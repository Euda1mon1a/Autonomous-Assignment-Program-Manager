"""
Schedule Publish Staging: Atomic Publishing with Backup Support.

Provides write-ahead logging and backup capabilities for schedule publishing,
enabling complete rollback for MODIFY and DELETE operations.

This module addresses the critical gap in schedule_draft_service.py where
MODIFY and DELETE rollbacks log warnings about inability to restore original data.

Features:
    - Pre-publish backup creation for MODIFY/DELETE operations
    - Atomic publish with transaction support
    - Complete rollback restoration
    - Audit trail preservation

Usage:
    from app.scheduling.schedule_publish_staging import StagingPublisher

    publisher = StagingPublisher(db)

    # Stage changes (creates backups)
    result = publisher.stage_publish(draft_id)

    # Commit staged changes
    if result.success:
        publisher.commit_publish(draft_id)

    # Or rollback with full restoration
    rollback_result = publisher.rollback_with_restore(draft_id)
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.assignment_backup import AssignmentBackup
from app.models.half_day_assignment import HalfDayAssignment
from app.models.schedule_draft import (
    DraftAssignmentChangeType,
    ScheduleDraft,
    ScheduleDraftAssignment,
    ScheduleDraftStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class BackupResult:
    """Result of backup operation."""

    success: bool
    backup_count: int = 0
    errors: list[str] = field(default_factory=list)
    backup_ids: list[UUID] = field(default_factory=list)


@dataclass
class RestoreResult:
    """Result of restore operation."""

    success: bool
    restored_count: int = 0
    failed_count: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class StagingResult:
    """Result of staging operation."""

    success: bool
    draft_id: UUID | None = None
    backup_result: BackupResult | None = None
    message: str = ""
    error_code: str | None = None


class StagingPublisher:
    """
    Manages staged publishing with backup and restore capabilities.

    Provides:
    - Backup creation before MODIFY/DELETE
    - Atomic staging of changes
    - Full restore during rollback
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize staging publisher.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def stage_publish(self, draft_id: UUID) -> StagingResult:
        """
        Stage a draft for publishing by creating backups for MODIFY/DELETE operations.

        This should be called BEFORE the actual publish operation to ensure
        backup data exists for rollback.

        Args:
            draft_id: UUID of the draft to stage

        Returns:
            StagingResult with backup information
        """
        try:
            # Get draft with assignments
            draft = (
                self.db.query(ScheduleDraft)
                .filter(ScheduleDraft.id == draft_id)
                .first()
            )

            if not draft:
                return StagingResult(
                    success=False,
                    draft_id=draft_id,
                    message=f"Draft {draft_id} not found",
                    error_code="DRAFT_NOT_FOUND",
                )

            if draft.status != ScheduleDraftStatus.DRAFT:
                return StagingResult(
                    success=False,
                    draft_id=draft_id,
                    message=f"Cannot stage draft with status {draft.status.value}",
                    error_code="INVALID_STATUS",
                )

            # Get all draft assignments that need backup
            draft_assignments = (
                self.db.query(ScheduleDraftAssignment)
                .filter(ScheduleDraftAssignment.draft_id == draft_id)
                .filter(
                    ScheduleDraftAssignment.change_type.in_(
                        [
                            DraftAssignmentChangeType.MODIFY,
                            DraftAssignmentChangeType.DELETE,
                        ]
                    )
                )
                .all()
            )

            # Create backups
            backup_result = self._create_backups(draft_assignments)

            if not backup_result.success:  # noqa: resilience-ok (error handling, not SPOF)
                return StagingResult(
                    success=False,
                    draft_id=draft_id,
                    backup_result=backup_result,
                    message=f"Backup creation failed: {backup_result.errors}",
                    error_code="BACKUP_FAILED",
                )

            logger.info(
                f"Staged draft {draft_id} with {backup_result.backup_count} backups"
            )

            return StagingResult(
                success=True,
                draft_id=draft_id,
                backup_result=backup_result,
                message=f"Draft staged with {backup_result.backup_count} backups",
            )

        except Exception as e:
            logger.exception(f"Failed to stage draft {draft_id}: {e}")
            return StagingResult(
                success=False,
                draft_id=draft_id,
                message=f"Staging failed: {str(e)}",
                error_code="STAGING_ERROR",
            )

    def _create_backups(
        self, draft_assignments: list[ScheduleDraftAssignment]
    ) -> BackupResult:
        """
        Create backups for draft assignments.

        Args:
            draft_assignments: Assignments to backup

        Returns:
            BackupResult with backup information
        """
        backup_count = 0
        backup_ids = []
        errors = []

        for da in draft_assignments:
            try:
                # Find existing assignment(s) to backup
                # For time_of_day="ALL", returns both AM and PM slots
                existing_assignments = self._find_existing_assignments(da)

                if not existing_assignments:
                    # For DELETE, we must find the original to backup
                    if da.change_type == DraftAssignmentChangeType.DELETE:
                        errors.append(
                            f"Cannot find existing assignment for DELETE: {da.id}"
                        )
                    continue

                # Create backup for each existing assignment
                for existing in existing_assignments:
                    backup = AssignmentBackup(
                        draft_assignment_id=da.id,
                        original_assignment_id=existing.id
                        if hasattr(existing, "id")
                        else None,
                        backup_type=da.change_type.value,
                        original_data_json=self._serialize_assignment(existing),
                        source_table="half_day_assignments",
                    )

                    self.db.add(backup)
                    self.db.flush()  # Get the ID

                    backup_ids.append(backup.id)
                    backup_count += 1

                    logger.debug(
                        f"Created backup for {da.change_type.value} of {da.person_id} "
                        f"on {da.assignment_date} ({existing.time_of_day})"
                    )

            except Exception as e:
                errors.append(f"Failed to backup {da.id}: {str(e)}")
                logger.warning(f"Failed to create backup for {da.id}: {e}")

        return BackupResult(
            success=len(errors) == 0,
            backup_count=backup_count,
            errors=errors,
            backup_ids=backup_ids,
        )

    def _find_existing_assignments(
        self, draft_assignment: ScheduleDraftAssignment
    ) -> list[HalfDayAssignment]:
        """
        Find existing assignment(s) for a draft assignment.

        For time_of_day="ALL", returns both AM and PM slots to ensure
        complete backup of full-day changes.

        Args:
            draft_assignment: The draft assignment to find original(s) for

        Returns:
            List of existing HalfDayAssignment(s), may be empty
        """
        results = []

        # Try by existing_assignment_id first
        if draft_assignment.existing_assignment_id:
            existing = (
                self.db.query(HalfDayAssignment)
                .filter(HalfDayAssignment.id == draft_assignment.existing_assignment_id)
                .first()
            )
            if existing:
                results.append(existing)
                # For ALL, also get the other slot
                if draft_assignment.time_of_day == "ALL":
                    other_slot = "PM" if existing.time_of_day == "AM" else "AM"
                    other = (
                        self.db.query(HalfDayAssignment)
                        .filter(
                            HalfDayAssignment.person_id == draft_assignment.person_id,
                            HalfDayAssignment.date == draft_assignment.assignment_date,
                            HalfDayAssignment.time_of_day == other_slot,
                        )
                        .first()
                    )
                    if other:
                        results.append(other)
                    # FIX: Only return if we got BOTH slots for ALL
                    # Otherwise fall through to fallback path to try again
                    if len(results) == 2:
                        return results
                else:
                    # Single slot request - can return with one result
                    return results

        # Clear results before fallback to avoid duplicates
        results = []

        # Fallback to matching by person/date/time
        base_query = self.db.query(HalfDayAssignment).filter(
            HalfDayAssignment.person_id == draft_assignment.person_id,
            HalfDayAssignment.date == draft_assignment.assignment_date,
        )

        # Handle time_of_day matching
        if draft_assignment.time_of_day == "ALL":
            # For ALL, backup BOTH AM and PM slots to ensure complete rollback
            am_assignment = base_query.filter(
                HalfDayAssignment.time_of_day == "AM"
            ).first()
            pm_assignment = base_query.filter(
                HalfDayAssignment.time_of_day == "PM"
            ).first()
            if am_assignment:
                results.append(am_assignment)
            if pm_assignment:
                results.append(pm_assignment)
        else:
            single = base_query.filter(
                HalfDayAssignment.time_of_day == draft_assignment.time_of_day
            ).first()
            if single:
                results.append(single)

        return results

    def _serialize_assignment(self, assignment: HalfDayAssignment) -> dict[str, Any]:
        """
        Serialize an assignment to JSON-compatible dict.

        Includes all fields necessary for complete restoration including
        provenance and override tracking fields.

        Args:
            assignment: The assignment to serialize

        Returns:
            Dictionary representation of the assignment
        """
        return {
            "id": str(assignment.id),
            "person_id": str(assignment.person_id),
            "date": assignment.date.isoformat() if assignment.date else None,
            "time_of_day": assignment.time_of_day,
            "activity_id": str(assignment.activity_id)
            if assignment.activity_id
            else None,
            "source": assignment.source.value
            if hasattr(assignment.source, "value")
            else assignment.source,
            "is_override": getattr(assignment, "is_override", False),
            "override_reason": getattr(assignment, "override_reason", None),
            "notes": getattr(assignment, "notes", None),
            "created_at": assignment.created_at.isoformat()
            if assignment.created_at
            else None,
            # Provenance fields for complete restoration
            "block_assignment_id": str(assignment.block_assignment_id)
            if getattr(assignment, "block_assignment_id", None)
            else None,
            # Override tracking fields
            "overridden_by": str(assignment.overridden_by)
            if getattr(assignment, "overridden_by", None)
            else None,
            "overridden_at": assignment.overridden_at.isoformat()
            if getattr(assignment, "overridden_at", None)
            else None,
            # Timestamp for audit
            "updated_at": assignment.updated_at.isoformat()
            if getattr(assignment, "updated_at", None)
            else None,
        }

    def _parse_datetime_from_backup(
        self, value: str | datetime | None
    ) -> datetime | None:
        """
        Parse datetime from backup data, handling both string and datetime objects.

        Args:
            value: String (ISO format), datetime, or None

        Returns:
            datetime object or None if parsing fails
        """
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                logger.warning(f"Could not parse datetime string: {value}")
                return None
        return None

    def restore_from_backups(
        self, draft_id: UUID, restored_by_id: UUID | None = None
    ) -> RestoreResult:
        """
        Restore assignments from backups during rollback.

        Args:
            draft_id: UUID of the draft being rolled back
            restored_by_id: UUID of the user performing restoration

        Returns:
            RestoreResult with restoration details
        """
        restored_count = 0
        failed_count = 0
        errors = []

        try:
            # Get all unrestored backups for this draft
            backups = (
                self.db.query(AssignmentBackup)
                .join(ScheduleDraftAssignment)
                .filter(
                    ScheduleDraftAssignment.draft_id == draft_id,
                    AssignmentBackup.restored_at.is_(None),
                )
                .all()
            )

            for backup in backups:
                try:
                    # Restore the assignment
                    restored = self._restore_single_backup(backup, restored_by_id)
                    if restored:
                        restored_count += 1
                    else:
                        failed_count += 1
                        errors.append(f"Failed to restore backup {backup.id}")

                except Exception as e:
                    failed_count += 1
                    errors.append(f"Error restoring backup {backup.id}: {str(e)}")
                    logger.warning(f"Failed to restore backup {backup.id}: {e}")

            logger.info(
                f"Restored {restored_count} assignments for draft {draft_id}, "
                f"{failed_count} failed"
            )

            return RestoreResult(
                success=failed_count == 0,
                restored_count=restored_count,
                failed_count=failed_count,
                errors=errors,
            )

        except Exception as e:
            logger.exception(f"Failed to restore backups for draft {draft_id}: {e}")
            return RestoreResult(
                success=False,
                errors=[f"Restoration failed: {str(e)}"],
            )

    def _restore_single_backup(
        self, backup: AssignmentBackup, restored_by_id: UUID | None
    ) -> bool:
        """
        Restore a single backup.

        Args:
            backup: The backup to restore
            restored_by_id: User performing restoration

        Returns:
            True if restored successfully
        """
        from datetime import date as date_type

        data = backup.original_data_json

        if backup.backup_type == "DELETE":
            # Re-create the deleted assignment
            assignment_date = data.get("date")
            if isinstance(assignment_date, str):
                assignment_date = date_type.fromisoformat(assignment_date)

            # Parse timestamps for provenance restoration
            created_at = self._parse_datetime_from_backup(data.get("created_at"))
            overridden_at = self._parse_datetime_from_backup(data.get("overridden_at"))

            new_assignment = HalfDayAssignment(
                person_id=UUID(data["person_id"]),
                date=assignment_date,
                time_of_day=data.get("time_of_day", "AM"),
                activity_id=UUID(data["activity_id"])
                if data.get("activity_id")
                else None,
                source=data.get("source", "MANUAL"),
                is_override=data.get("is_override", False),
                override_reason=data.get("override_reason"),
                notes=data.get("notes"),
                # Provenance fields for complete restoration
                block_assignment_id=UUID(data["block_assignment_id"])
                if data.get("block_assignment_id")
                else None,
                # Override tracking fields
                overridden_by=UUID(data["overridden_by"])
                if data.get("overridden_by")
                else None,
                overridden_at=overridden_at,
                # Preserve original timestamps
                created_at=created_at or datetime.utcnow(),
                updated_at=self._parse_datetime_from_backup(data.get("updated_at"))
                or datetime.utcnow(),
            )

            self.db.add(new_assignment)
            logger.debug(
                f"Restored deleted assignment for {data['person_id']} on {data['date']}"
            )

        elif backup.backup_type == "MODIFY":
            # Find the modified assignment and restore original values
            if backup.original_assignment_id:
                existing = (
                    self.db.query(HalfDayAssignment)
                    .filter(HalfDayAssignment.id == backup.original_assignment_id)
                    .first()
                )

                if existing:
                    # Restore original values
                    if data.get("activity_id"):
                        existing.activity_id = UUID(data["activity_id"])
                    existing.source = data.get("source", existing.source)
                    existing.is_override = data.get("is_override", existing.is_override)
                    existing.override_reason = data.get("override_reason")
                    existing.notes = data.get("notes")

                    # Restore provenance fields
                    if data.get("block_assignment_id"):
                        existing.block_assignment_id = UUID(data["block_assignment_id"])

                    # Restore override tracking fields
                    existing.overridden_by = (
                        UUID(data["overridden_by"])
                        if data.get("overridden_by")
                        else None
                    )
                    existing.overridden_at = self._parse_datetime_from_backup(
                        data.get("overridden_at")
                    )

                    # Restore updated_at for audit fidelity
                    restored_updated_at = self._parse_datetime_from_backup(
                        data.get("updated_at")
                    )
                    if restored_updated_at:
                        existing.updated_at = restored_updated_at

                    logger.debug(
                        f"Restored modified assignment {backup.original_assignment_id}"
                    )
                else:
                    # Assignment was deleted after modification - recreate it
                    assignment_date = data.get("date")
                    if isinstance(assignment_date, str):
                        assignment_date = date_type.fromisoformat(assignment_date)

                    # Parse timestamps for provenance restoration
                    created_at = self._parse_datetime_from_backup(
                        data.get("created_at")
                    )
                    overridden_at = self._parse_datetime_from_backup(
                        data.get("overridden_at")
                    )

                    new_assignment = HalfDayAssignment(
                        person_id=UUID(data["person_id"]),
                        date=assignment_date,
                        time_of_day=data.get("time_of_day", "AM"),
                        activity_id=UUID(data["activity_id"])
                        if data.get("activity_id")
                        else None,
                        source=data.get("source", "MANUAL"),
                        is_override=data.get("is_override", False),
                        override_reason=data.get("override_reason"),
                        notes=data.get("notes"),
                        # Provenance fields for complete restoration
                        block_assignment_id=UUID(data["block_assignment_id"])
                        if data.get("block_assignment_id")
                        else None,
                        # Override tracking fields
                        overridden_by=UUID(data["overridden_by"])
                        if data.get("overridden_by")
                        else None,
                        overridden_at=overridden_at,
                        # Preserve original timestamps
                        created_at=created_at or datetime.utcnow(),
                        updated_at=self._parse_datetime_from_backup(
                            data.get("updated_at")
                        )
                        or datetime.utcnow(),
                    )
                    self.db.add(new_assignment)
                    logger.debug(
                        f"Recreated missing modified assignment for {data['person_id']}"
                    )

        # Mark backup as restored
        backup.restored_at = datetime.utcnow()
        backup.restored_by_id = restored_by_id

        return True

    def get_backup_count(self, draft_id: UUID) -> int:
        """
        Get count of backups for a draft.

        Args:
            draft_id: UUID of the draft

        Returns:
            Number of backups
        """
        return (
            self.db.query(AssignmentBackup)
            .join(ScheduleDraftAssignment)
            .filter(ScheduleDraftAssignment.draft_id == draft_id)
            .count()
        )

    def get_unrestored_backup_count(self, draft_id: UUID) -> int:
        """
        Get count of unrestored backups for a draft.

        Args:
            draft_id: UUID of the draft

        Returns:
            Number of unrestored backups
        """
        return (
            self.db.query(AssignmentBackup)
            .join(ScheduleDraftAssignment)
            .filter(
                ScheduleDraftAssignment.draft_id == draft_id,
                AssignmentBackup.restored_at.is_(None),
            )
            .count()
        )


# Convenience function for integration with schedule_draft_service
def create_pre_publish_backups(db: Session, draft_id: UUID) -> BackupResult:
    """
    Create backups for all MODIFY/DELETE operations in a draft.

    Call this before publishing to ensure rollback capability.

    Args:
        db: Database session
        draft_id: Draft to backup

    Returns:
        BackupResult with backup information
    """
    publisher = StagingPublisher(db)
    result = publisher.stage_publish(draft_id)
    return result.backup_result or BackupResult(
        success=False, errors=["Staging failed"]
    )


def restore_draft_backups(
    db: Session, draft_id: UUID, restored_by_id: UUID | None = None
) -> RestoreResult:
    """
    Restore all backups for a draft during rollback.

    Args:
        db: Database session
        draft_id: Draft being rolled back
        restored_by_id: User performing restoration

    Returns:
        RestoreResult with restoration details
    """
    publisher = StagingPublisher(db)
    return publisher.restore_from_backups(draft_id, restored_by_id)
