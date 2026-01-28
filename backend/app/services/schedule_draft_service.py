"""
Schedule draft service for staging workflow.

Provides the service layer for the schedule draft feature:
- create_draft(): Create a new draft for a block/date range
- add_assignment_to_draft(): Add/modify/delete assignment in draft
- get_draft_preview(): Compare draft vs live assignments
- publish_draft(): Commit draft to live assignments table
- rollback_draft(): Undo published draft within 24h window
- acknowledge_flag(): Acknowledge a flag on a draft

Transaction Safety:
    Uses transactional context managers to ensure atomicity.
    Rollback window of 24 hours for published drafts.

Usage:
    from app.services.schedule_draft_service import ScheduleDraftService

    service = ScheduleDraftService(db)
    draft = await service.create_draft(
        source_type=DraftSourceType.SOLVER,
        start_date=date(2026, 3, 12),
        end_date=date(2026, 4, 8),
        block_number=10,
        created_by_id=user_id,
    )
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ActivityNotFoundError
from app.db.transaction import transactional_with_retry
from app.models.activity import Activity
from app.models.assignment import Assignment
from app.models.block_assignment import BlockAssignment
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.rotation_template import RotationTemplate
from app.models.schedule_draft import (
    DraftAssignmentChangeType,
    DraftFlagSeverity,
    DraftFlagType,
    DraftSourceType,
    ScheduleDraft,
    ScheduleDraftAssignment,
    ScheduleDraftFlag,
    ScheduleDraftStatus,
)
from app.models.person import Person
from app.models.schedule_run import ScheduleRun
from app.scheduling.validator import ACGMEValidator
from app.utils.academic_blocks import get_block_half, get_block_number_for_date
from app.utils.fmc_capacity import activity_counts_toward_fmc_capacity_for_template

logger = logging.getLogger(__name__)

# Rollback window in hours
ROLLBACK_WINDOW_HOURS = 24


@dataclass
class CreateDraftResult:
    """Result of creating a draft."""

    success: bool
    draft_id: UUID | None = None
    message: str = ""
    error_code: str | None = None


@dataclass
class DraftPreviewResult:
    """Result of previewing a draft."""

    draft_id: UUID
    add_count: int = 0
    modify_count: int = 0
    delete_count: int = 0
    flags_total: int = 0
    flags_acknowledged: int = 0
    assignments: list[dict] | None = None
    flags: list[dict] | None = None
    acgme_violations: list[str] | None = None


@dataclass
class PublishResult:
    """Result of publishing a draft."""

    success: bool
    draft_id: UUID
    status: ScheduleDraftStatus
    published_count: int = 0
    error_count: int = 0
    errors: list[dict] | None = None
    acgme_warnings: list[str] | None = None
    rollback_available: bool = True
    rollback_expires_at: datetime | None = None
    message: str = ""
    error_code: str | None = None


@dataclass
class RollbackResult:
    """Result of rolling back a draft."""

    success: bool
    draft_id: UUID
    status: ScheduleDraftStatus
    rolled_back_count: int = 0
    failed_count: int = 0
    errors: list[str] | None = None
    message: str = ""
    error_code: str | None = None


class ScheduleDraftService:
    """
    Service for managing schedule draft workflow.

    Handles the complete lifecycle of schedule drafts:
    1. Create draft from solver/manual/swap
    2. Add/modify/delete assignments in draft
    3. Auto-detect conflicts and create flags
    4. Preview draft vs live
    5. Publish draft to live assignments
    6. Rollback published drafts within window

    Thread Safety:
        Uses row-level locking where needed to prevent concurrent
        modifications. Safe for use in multi-threaded environments.
    """

    def __init__(self, db: Session):
        """
        Initialize the ScheduleDraftService with a database session.

        Args:
            db: SQLAlchemy Session for database operations.
        """
        self.db = db

    async def create_draft(
        self,
        source_type: DraftSourceType,
        start_date: date,
        end_date: date,
        block_number: int | None = None,
        created_by_id: UUID | None = None,
        schedule_run_id: UUID | None = None,
        notes: str | None = None,
    ) -> CreateDraftResult:
        """
        Create a new draft for a date range.

        If a draft already exists for the same block/date range with status DRAFT,
        returns that draft instead of creating a new one.

        Args:
            source_type: Source of the draft (solver, manual, swap, import).
            start_date: Start date of the draft scope.
            end_date: End date of the draft scope.
            block_number: Optional block number.
            created_by_id: UUID of the user creating the draft.
            schedule_run_id: Optional link to schedule_runs table.
            notes: Optional notes about the draft.

        Returns:
            CreateDraftResult with draft_id and status.
        """
        try:
            # Check for existing active draft for this block/date range
            existing_draft = (
                self.db.query(ScheduleDraft)
                .filter(
                    ScheduleDraft.status == ScheduleDraftStatus.DRAFT,
                    ScheduleDraft.target_start_date == start_date,
                    ScheduleDraft.target_end_date == end_date,
                )
                .first()
            )

            if existing_draft:
                logger.info(
                    f"Found existing draft {existing_draft.id} for "
                    f"{start_date} - {end_date}"
                )
                return CreateDraftResult(
                    success=True,
                    draft_id=existing_draft.id,
                    message="Using existing draft for this date range",
                )

            # Create new draft
            draft = ScheduleDraft(
                id=uuid4(),
                created_at=datetime.utcnow(),
                created_by_id=created_by_id,
                target_block=block_number,
                target_start_date=start_date,
                target_end_date=end_date,
                status=ScheduleDraftStatus.DRAFT,
                source_type=source_type,
                source_schedule_run_id=schedule_run_id,
                notes=notes,
                change_summary={"added": 0, "modified": 0, "deleted": 0},
                flags_total=0,
                flags_acknowledged=0,
            )

            self.db.add(draft)
            self.db.commit()

            logger.info(
                f"Created draft {draft.id} for {start_date} - {end_date} "
                f"(block {block_number}, source={source_type.value})"
            )

            return CreateDraftResult(
                success=True,
                draft_id=draft.id,
                message=f"Created draft for Block {block_number or 'N/A'}",
            )

        except Exception as e:
            logger.exception(f"Failed to create draft: {e}")
            self.db.rollback()
            return CreateDraftResult(
                success=False,
                message=f"Failed to create draft: {str(e)}",
                error_code="CREATE_FAILED",
            )

    async def add_assignment_to_draft(
        self,
        draft_id: UUID,
        person_id: UUID,
        assignment_date: date,
        time_of_day: str | None,
        activity_code: str | None = None,
        rotation_id: UUID | None = None,
        change_type: DraftAssignmentChangeType = DraftAssignmentChangeType.ADD,
        existing_assignment_id: UUID | None = None,
    ) -> UUID | None:
        """
        Add an assignment to a draft.

        Args:
            draft_id: UUID of the draft.
            person_id: UUID of the person.
            assignment_date: Date of the assignment.
            time_of_day: AM/PM or None for full day.
            activity_code: Activity code.
            rotation_id: Optional rotation template ID.
            change_type: Type of change (add, modify, delete).
            existing_assignment_id: For modify/delete, the ID of existing assignment.

        Returns:
            UUID of the created draft assignment, or None on error.
        """
        try:
            # Normalize time_of_day: None -> "ALL" (full-day sentinel)
            normalized_time = time_of_day or "ALL"

            # Check if assignment already exists in draft
            existing = (
                self.db.query(ScheduleDraftAssignment)
                .filter(
                    ScheduleDraftAssignment.draft_id == draft_id,
                    ScheduleDraftAssignment.person_id == person_id,
                    ScheduleDraftAssignment.assignment_date == assignment_date,
                    ScheduleDraftAssignment.time_of_day == normalized_time,
                )
                .first()
            )

            if existing:
                # Update existing draft assignment
                existing.activity_code = activity_code
                existing.rotation_id = rotation_id
                existing.change_type = change_type
                existing.existing_assignment_id = existing_assignment_id
                self.db.commit()
                return existing.id

            # Create new draft assignment
            draft_assignment = ScheduleDraftAssignment(
                id=uuid4(),
                draft_id=draft_id,
                person_id=person_id,
                assignment_date=assignment_date,
                time_of_day=normalized_time,  # Use normalized value
                activity_code=activity_code,
                rotation_id=rotation_id,
                change_type=change_type,
                existing_assignment_id=existing_assignment_id,
            )

            self.db.add(draft_assignment)

            # Update change summary in draft
            draft = (
                self.db.query(ScheduleDraft)
                .filter(ScheduleDraft.id == draft_id)
                .first()
            )
            if draft and draft.change_summary:
                summary = draft.change_summary.copy()
                if change_type == DraftAssignmentChangeType.ADD:
                    summary["added"] = summary.get("added", 0) + 1
                elif change_type == DraftAssignmentChangeType.MODIFY:
                    summary["modified"] = summary.get("modified", 0) + 1
                elif change_type == DraftAssignmentChangeType.DELETE:
                    summary["deleted"] = summary.get("deleted", 0) + 1
                draft.change_summary = summary

            self.db.commit()
            return draft_assignment.id

        except Exception as e:
            logger.exception(f"Failed to add assignment to draft {draft_id}: {e}")
            self.db.rollback()
            return None

    async def add_flag_to_draft(
        self,
        draft_id: UUID,
        flag_type: DraftFlagType,
        severity: DraftFlagSeverity,
        message: str,
        assignment_id: UUID | None = None,
        person_id: UUID | None = None,
        affected_date: date | None = None,
    ) -> UUID | None:
        """
        Add a flag to a draft.

        Args:
            draft_id: UUID of the draft.
            flag_type: Type of flag.
            severity: Severity level.
            message: Flag message.
            assignment_id: Optional related assignment.
            person_id: Optional related person.
            affected_date: Optional affected date.

        Returns:
            UUID of the created flag, or None on error.
        """
        try:
            flag = ScheduleDraftFlag(
                id=uuid4(),
                draft_id=draft_id,
                flag_type=flag_type,
                severity=severity,
                message=message,
                assignment_id=assignment_id,
                person_id=person_id,
                affected_date=affected_date,
                created_at=datetime.utcnow(),
            )

            self.db.add(flag)

            # Update flags_total in draft
            draft = (
                self.db.query(ScheduleDraft)
                .filter(ScheduleDraft.id == draft_id)
                .first()
            )
            if draft:
                draft.flags_total = (draft.flags_total or 0) + 1

            self.db.commit()
            return flag.id

        except Exception as e:
            logger.exception(f"Failed to add flag to draft {draft_id}: {e}")
            self.db.rollback()
            return None

    async def acknowledge_flag(
        self,
        flag_id: UUID,
        acknowledged_by_id: UUID,
        resolution_note: str | None = None,
    ) -> bool:
        """
        Acknowledge a flag.

        Args:
            flag_id: UUID of the flag.
            acknowledged_by_id: UUID of the user acknowledging.
            resolution_note: Optional note about resolution.

        Returns:
            True if successful, False otherwise.
        """
        try:
            flag = (
                self.db.query(ScheduleDraftFlag)
                .filter(ScheduleDraftFlag.id == flag_id)
                .first()
            )

            if not flag:
                return False

            if flag.acknowledged_at is not None:
                # Already acknowledged
                return True

            flag.acknowledged_at = datetime.utcnow()
            flag.acknowledged_by_id = acknowledged_by_id
            flag.resolution_note = resolution_note

            # Update flags_acknowledged in draft
            draft = (
                self.db.query(ScheduleDraft)
                .filter(ScheduleDraft.id == flag.draft_id)
                .first()
            )
            if draft:
                draft.flags_acknowledged = (draft.flags_acknowledged or 0) + 1

            self.db.commit()
            return True

        except Exception as e:
            logger.exception(f"Failed to acknowledge flag {flag_id}: {e}")
            self.db.rollback()
            return False

    async def get_draft_preview(self, draft_id: UUID) -> DraftPreviewResult | None:
        """
        Get a preview of the draft showing changes vs live.

        Args:
            draft_id: UUID of the draft.

        Returns:
            DraftPreviewResult with counts and details, or None if not found.
        """
        draft = (
            self.db.query(ScheduleDraft)
            .options(
                selectinload(ScheduleDraft.assignments).selectinload(
                    ScheduleDraftAssignment.person
                ),
                selectinload(ScheduleDraft.flags),
            )
            .filter(ScheduleDraft.id == draft_id)
            .first()
        )

        if not draft:
            return None

        # Count changes by type
        add_count = sum(
            1
            for a in draft.assignments
            if a.change_type == DraftAssignmentChangeType.ADD
        )
        modify_count = sum(
            1
            for a in draft.assignments
            if a.change_type == DraftAssignmentChangeType.MODIFY
        )
        delete_count = sum(
            1
            for a in draft.assignments
            if a.change_type == DraftAssignmentChangeType.DELETE
        )

        # Build assignment list
        assignments = [
            {
                "id": str(a.id),
                "person_id": str(a.person_id),
                "person_name": a.person.name if a.person else None,
                "date": a.assignment_date.isoformat(),
                "time_of_day": a.time_of_day,
                "activity_code": a.activity_code,
                "change_type": a.change_type.value,
            }
            for a in draft.assignments
        ]

        # Build flags list with timestamps
        flags = [
            {
                "id": str(f.id),
                "type": f.flag_type.value,
                "severity": f.severity.value,
                "message": f.message,
                "acknowledged": f.acknowledged_at is not None,
                "acknowledged_at": (
                    f.acknowledged_at.isoformat() if f.acknowledged_at else None
                ),
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "date": f.affected_date.isoformat() if f.affected_date else None,
            }
            for f in draft.flags
        ]

        return DraftPreviewResult(
            draft_id=draft_id,
            add_count=add_count,
            modify_count=modify_count,
            delete_count=delete_count,
            flags_total=draft.flags_total or 0,
            flags_acknowledged=draft.flags_acknowledged or 0,
            assignments=assignments,
            flags=flags,
        )

    async def publish_draft(
        self,
        draft_id: UUID,
        published_by_id: UUID,
        override_comment: str | None = None,
        validate_acgme: bool = True,
    ) -> PublishResult:
        """
        Publish a draft to live assignments.

        Args:
            draft_id: UUID of the draft to publish.
            published_by_id: UUID of the user publishing.
            override_comment: Required for Tier 1 if unacknowledged flags exist.
            validate_acgme: If True, validate ACGME compliance after publish.

        Returns:
            PublishResult with counts and status.
        """
        try:
            with transactional_with_retry(self.db, max_retries=3, timeout_seconds=60.0):
                # Get draft with lock
                draft = (
                    self.db.query(ScheduleDraft)
                    .filter(ScheduleDraft.id == draft_id)
                    .with_for_update()
                    .first()
                )

                if not draft:
                    return PublishResult(
                        success=False,
                        draft_id=draft_id,
                        status=ScheduleDraftStatus.DRAFT,
                        message="Draft not found",
                        error_code="DRAFT_NOT_FOUND",
                    )

                if draft.status != ScheduleDraftStatus.DRAFT:
                    return PublishResult(
                        success=False,
                        draft_id=draft_id,
                        status=draft.status,
                        message=f"Cannot publish draft with status: {draft.status.value}",
                        error_code="INVALID_STATUS",
                    )

                # Check flags (Tier 1 must acknowledge or provide override comment)
                if draft.has_unacknowledged_flags and not override_comment:
                    return PublishResult(
                        success=False,
                        draft_id=draft_id,
                        status=draft.status,
                        message="Unacknowledged flags exist. Provide override_comment or acknowledge flags.",
                        error_code="FLAGS_UNACKNOWLEDGED",
                    )

                # Get all draft assignments
                draft_assignments = (
                    self.db.query(ScheduleDraftAssignment)
                    .filter(ScheduleDraftAssignment.draft_id == draft_id)
                    .all()
                )

                published_count = 0
                error_count = 0
                errors = []
                acgme_warnings = []

                for da in draft_assignments:
                    try:
                        created_ids = await self._apply_draft_assignment(da)
                        if created_ids:
                            # Store first created ID for reference (may have AM/PM pair)
                            da.created_assignment_id = created_ids[0]
                            published_count += len(created_ids)
                    except Exception as e:
                        logger.warning(
                            f"Failed to publish draft assignment {da.id}: {e}"
                        )
                        error_count += 1
                        errors.append(
                            {
                                "draft_assignment_id": str(da.id),
                                "person_id": str(da.person_id),
                                "date": da.assignment_date.isoformat(),
                                "error": str(e),
                            }
                        )

                # Update draft status based on success
                now = datetime.utcnow()

                if error_count > 0 and published_count == 0:
                    # Complete failure - stay in DRAFT
                    draft.notes = f"Publish failed: {error_count} errors"
                    logger.error(
                        f"Publish failed for draft {draft_id}: {error_count} errors, "
                        "0 published"
                    )
                    return PublishResult(
                        success=False,
                        draft_id=draft_id,
                        status=ScheduleDraftStatus.DRAFT,
                        published_count=0,
                        error_count=error_count,
                        errors=errors,
                        message=f"Publish failed: {error_count} errors",
                        error_code="PUBLISH_FAILED",
                    )

                # Partial or complete success - mark as PUBLISHED
                draft.status = ScheduleDraftStatus.PUBLISHED
                draft.published_at = now
                draft.published_by_id = published_by_id
                draft.rollback_available = True
                draft.rollback_expires_at = now + timedelta(hours=ROLLBACK_WINDOW_HOURS)

                if error_count > 0:
                    # Partial success - note the errors
                    draft.notes = (
                        f"Published with {error_count} errors "
                        f"({published_count} succeeded)"
                    )

                if override_comment:
                    draft.override_comment = override_comment
                    draft.override_by_id = published_by_id

                # ACGME validation after publish
                if validate_acgme and published_count > 0:
                    try:
                        validator = ACGMEValidator(self.db)
                        result = validator.validate_all(
                            draft.target_start_date, draft.target_end_date
                        )
                        acgme_warnings = [
                            f"{v.severity}: {v.message}" for v in result.violations
                        ]
                    except Exception as e:
                        logger.warning(f"ACGME validation after publish failed: {e}")

                logger.info(
                    f"Published draft {draft_id}: {published_count} published, "
                    f"{error_count} errors"
                )

                return PublishResult(
                    success=error_count == 0,
                    draft_id=draft_id,
                    status=draft.status,
                    published_count=published_count,
                    error_count=error_count,
                    errors=errors if errors else None,
                    acgme_warnings=acgme_warnings if acgme_warnings else None,
                    rollback_available=True,
                    rollback_expires_at=draft.rollback_expires_at,
                    message=f"Published {published_count} assignments"
                    + (f" ({error_count} failed)" if error_count > 0 else ""),
                )

        except Exception as e:
            logger.exception(f"Failed to publish draft {draft_id}: {e}")
            return PublishResult(
                success=False,
                draft_id=draft_id,
                status=ScheduleDraftStatus.DRAFT,
                message=f"Publish failed: {str(e)}",
                error_code="PUBLISH_FAILED",
            )

    async def _apply_draft_assignment(self, da: ScheduleDraftAssignment) -> list[UUID]:
        """
        Apply a single draft assignment to half_day_assignments table.

        Args:
            da: The draft assignment to apply.

        Returns:
            List of created/updated HalfDayAssignment UUIDs (may be 1 or 2 for ALL).

        Notes:
            - Published drafts get source=MANUAL (human-approved)
            - If time_of_day is 'ALL', creates both AM and PM assignments
        """
        created_ids = []

        # Resolve activity_code to activity_id (required for add/modify)
        activity_id = None
        if da.change_type != DraftAssignmentChangeType.DELETE:
            if da.activity_code:
                normalized = da.activity_code.strip()
                activity = (
                    self.db.query(Activity)
                    .filter(func.lower(Activity.code) == normalized.lower())
                    .first()
                )
                if not activity:
                    activity = (
                        self.db.query(Activity)
                        .filter(
                            func.lower(Activity.display_abbreviation)
                            == normalized.lower()
                        )
                        .first()
                    )
                if not activity:
                    activity = (
                        self.db.query(Activity)
                        .filter(func.lower(Activity.name) == normalized.lower())
                        .first()
                    )
                if not activity:
                    raise ActivityNotFoundError(
                        normalized, context="schedule_draft_service"
                    )
                activity_id = activity.id
            else:
                raise ActivityNotFoundError(
                    "<missing activity_code>",
                    context="schedule_draft_service",
                )

        # Determine time slots to process
        # Draft uses 'ALL' for full-day, HalfDayAssignment needs separate AM/PM
        time_slots = ["AM", "PM"] if da.time_of_day == "ALL" else [da.time_of_day]

        for time_slot in time_slots:
            if da.change_type == DraftAssignmentChangeType.DELETE:
                # Delete existing half-day assignment
                self.db.query(HalfDayAssignment).filter(
                    HalfDayAssignment.person_id == da.person_id,
                    HalfDayAssignment.date == da.assignment_date,
                    HalfDayAssignment.time_of_day == time_slot,
                ).delete()
                # Return None for deletes (no new ID created)

            elif da.change_type == DraftAssignmentChangeType.MODIFY:
                capacity_flag = self._resolve_fmc_capacity_flag(
                    da.person_id, da.assignment_date, activity_id
                )
                # Update existing half-day assignment
                existing = (
                    self.db.query(HalfDayAssignment)
                    .filter(
                        HalfDayAssignment.person_id == da.person_id,
                        HalfDayAssignment.date == da.assignment_date,
                        HalfDayAssignment.time_of_day == time_slot,
                    )
                    .first()
                )
                if existing:
                    existing.activity_id = activity_id
                    existing.counts_toward_fmc_capacity = capacity_flag
                    existing.source = AssignmentSource.MANUAL.value
                    existing.updated_at = datetime.utcnow()
                    created_ids.append(existing.id)
                else:
                    # No existing record - create new (shouldn't happen but handle gracefully)
                    half_day = self._create_half_day_assignment(
                        da, time_slot, activity_id, capacity_flag
                    )
                    self.db.add(half_day)
                    created_ids.append(half_day.id)

            else:  # ADD
                capacity_flag = self._resolve_fmc_capacity_flag(
                    da.person_id, da.assignment_date, activity_id
                )
                # Check if slot already exists (upsert logic)
                existing = (
                    self.db.query(HalfDayAssignment)
                    .filter(
                        HalfDayAssignment.person_id == da.person_id,
                        HalfDayAssignment.date == da.assignment_date,
                        HalfDayAssignment.time_of_day == time_slot,
                    )
                    .first()
                )
                if existing:
                    # Update existing (manual edits can override locked slots)
                    prior_source = existing.source
                    existing.activity_id = activity_id
                    existing.counts_toward_fmc_capacity = capacity_flag
                    existing.source = AssignmentSource.MANUAL.value
                    if prior_source != AssignmentSource.MANUAL.value:
                        existing.is_override = True
                    existing.updated_at = datetime.utcnow()
                    created_ids.append(existing.id)
                else:
                    # Create new half-day assignment
                    half_day = self._create_half_day_assignment(
                        da, time_slot, activity_id, capacity_flag
                    )
                    self.db.add(half_day)
                    created_ids.append(half_day.id)

        return created_ids

    def _resolve_rotation_template_for_date(
        self, person_id: UUID, assignment_date: date
    ) -> RotationTemplate | None:
        block_number, academic_year = get_block_number_for_date(assignment_date)
        block_assignment = (
            self.db.query(BlockAssignment)
            .options(
                selectinload(BlockAssignment.rotation_template),
                selectinload(BlockAssignment.secondary_rotation_template),
            )
            .filter(
                BlockAssignment.resident_id == person_id,
                BlockAssignment.block_number == block_number,
                BlockAssignment.academic_year == academic_year,
            )
            .first()
        )
        if not block_assignment:
            return None
        if (
            block_assignment.secondary_rotation_template_id
            and get_block_half(assignment_date) == 2
        ):
            return block_assignment.secondary_rotation_template
        return block_assignment.rotation_template

    def _resolve_fmc_capacity_flag(
        self,
        person_id: UUID,
        assignment_date: date,
        activity_id: UUID | None,
    ) -> bool | None:
        if not activity_id:
            return None
        activity = self.db.get(Activity, activity_id)
        if not activity:
            return None
        template = self._resolve_rotation_template_for_date(person_id, assignment_date)
        return activity_counts_toward_fmc_capacity_for_template(activity, template)

    def _create_half_day_assignment(
        self,
        da: ScheduleDraftAssignment,
        time_slot: str,
        activity_id: UUID | None,
        counts_toward_fmc_capacity: bool | None,
    ) -> HalfDayAssignment:
        """Create a new HalfDayAssignment from draft assignment data."""
        return HalfDayAssignment(
            id=uuid4(),
            person_id=da.person_id,
            date=da.assignment_date,
            time_of_day=time_slot,
            activity_id=activity_id,
            counts_toward_fmc_capacity=counts_toward_fmc_capacity,
            source=AssignmentSource.MANUAL.value,  # Published drafts = manual
            is_override=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    async def rollback_draft(
        self,
        draft_id: UUID,
        rolled_back_by_id: UUID,
    ) -> RollbackResult:
        """
        Rollback a published draft.

        Args:
            draft_id: UUID of the draft to rollback.
            rolled_back_by_id: UUID of the user performing rollback.

        Returns:
            RollbackResult with status and counts.
        """
        try:
            with transactional_with_retry(self.db, max_retries=3, timeout_seconds=60.0):
                # Get draft with lock
                draft = (
                    self.db.query(ScheduleDraft)
                    .filter(ScheduleDraft.id == draft_id)
                    .with_for_update()
                    .first()
                )

                if not draft:
                    return RollbackResult(
                        success=False,
                        draft_id=draft_id,
                        status=ScheduleDraftStatus.DRAFT,
                        message="Draft not found",
                        error_code="DRAFT_NOT_FOUND",
                    )

                if draft.status != ScheduleDraftStatus.PUBLISHED:
                    return RollbackResult(
                        success=False,
                        draft_id=draft_id,
                        status=draft.status,
                        message=f"Cannot rollback draft with status: {draft.status.value}",
                        error_code="INVALID_STATUS",
                    )

                # Check rollback window
                if not draft.rollback_available:
                    return RollbackResult(
                        success=False,
                        draft_id=draft_id,
                        status=draft.status,
                        message="Rollback not available for this draft",
                        error_code="ROLLBACK_NOT_AVAILABLE",
                    )

                if (
                    draft.rollback_expires_at
                    and datetime.utcnow() > draft.rollback_expires_at
                ):
                    draft.rollback_available = False
                    self.db.commit()
                    return RollbackResult(
                        success=False,
                        draft_id=draft_id,
                        status=draft.status,
                        message="Rollback window has expired",
                        error_code="ROLLBACK_EXPIRED",
                    )

                # Get all draft assignments that were published
                draft_assignments = (
                    self.db.query(ScheduleDraftAssignment)
                    .filter(
                        ScheduleDraftAssignment.draft_id == draft_id,
                        ScheduleDraftAssignment.created_assignment_id.isnot(None),
                    )
                    .all()
                )

                rolled_back_count = 0
                failed_count = 0
                errors = []

                for da in draft_assignments:
                    try:
                        # Determine time slots (ALL means both AM and PM)
                        time_slots = (
                            ["AM", "PM"]
                            if da.time_of_day == "ALL"
                            else [da.time_of_day]
                        )

                        if da.change_type == DraftAssignmentChangeType.ADD:
                            # Delete the created HalfDayAssignment(s)
                            # Delete by person_id, date, time_of_day since we may have
                            # created multiple records for ALL and only stored one ID
                            for slot in time_slots:
                                deleted = (
                                    self.db.query(HalfDayAssignment)
                                    .filter(
                                        HalfDayAssignment.person_id == da.person_id,
                                        HalfDayAssignment.date == da.assignment_date,
                                        HalfDayAssignment.time_of_day == slot,
                                        HalfDayAssignment.source
                                        == AssignmentSource.MANUAL.value,
                                    )
                                    .delete()
                                )
                                if deleted:
                                    rolled_back_count += 1
                            da.created_assignment_id = None

                        elif da.change_type == DraftAssignmentChangeType.DELETE:
                            # Cannot restore deleted assignments without backup
                            # Best-effort: Log failure but continue with audit trail
                            logger.warning(
                                f"Cannot restore deleted assignment {da.existing_assignment_id} "
                                f"(best-effort rollback - original data not preserved)"
                            )
                            failed_count += 1
                            errors.append(
                                f"Cannot restore deleted assignment for {da.person_id} "
                                f"on {da.assignment_date} - original data not backed up"
                            )

                        elif da.change_type == DraftAssignmentChangeType.MODIFY:
                            # Cannot restore modified assignments without backup
                            # Best-effort: Log failure but continue with audit trail
                            logger.warning(
                                f"Cannot restore modified assignment {da.existing_assignment_id} "
                                f"(best-effort rollback - original data not preserved)"
                            )
                            failed_count += 1
                            errors.append(
                                f"Cannot restore modified assignment for {da.person_id} "
                                f"on {da.assignment_date} - original data not backed up"
                            )

                    except Exception as e:
                        logger.warning(
                            f"Failed to rollback draft assignment {da.id}: {e}"
                        )
                        failed_count += 1
                        errors.append(str(e))

                # Update draft status based on success
                if rolled_back_count == 0 and failed_count > 0:
                    # Complete failure - stay in PUBLISHED
                    draft.notes = (
                        f"Rollback failed: {failed_count} errors, "
                        "no changes were reversed"
                    )
                    logger.error(
                        f"Rollback failed for draft {draft_id}: "
                        f"{failed_count} errors, 0 rolled back"
                    )
                    return RollbackResult(
                        success=False,
                        draft_id=draft_id,
                        status=ScheduleDraftStatus.PUBLISHED,
                        rolled_back_count=0,
                        failed_count=failed_count,
                        errors=errors,
                        message="Rollback failed: no changes were reversed",
                        error_code="ROLLBACK_FAILED",
                    )

                # Partial or complete success - mark as ROLLED_BACK
                draft.status = ScheduleDraftStatus.ROLLED_BACK
                draft.rolled_back_at = datetime.utcnow()
                draft.rolled_back_by_id = rolled_back_by_id
                draft.rollback_available = False

                if failed_count > 0:
                    # Partial success - audit trail in notes
                    draft.notes = (
                        f"Rollback incomplete: {rolled_back_count} reversed, "
                        f"{failed_count} could not be restored (best-effort rollback)"
                    )

                logger.info(
                    f"Rolled back draft {draft_id}: {rolled_back_count} rolled back, "
                    f"{failed_count} failed"
                )

                return RollbackResult(
                    success=failed_count == 0,
                    draft_id=draft_id,
                    status=draft.status,
                    rolled_back_count=rolled_back_count,
                    failed_count=failed_count,
                    errors=errors if errors else None,
                    message=f"Rolled back {rolled_back_count} assignments"
                    + (
                        f" ({failed_count} could not be restored)"
                        if failed_count > 0
                        else ""
                    ),
                )

        except Exception as e:
            logger.exception(f"Failed to rollback draft {draft_id}: {e}")
            return RollbackResult(
                success=False,
                draft_id=draft_id,
                status=ScheduleDraftStatus.PUBLISHED,
                message=f"Rollback failed: {str(e)}",
                error_code="ROLLBACK_FAILED",
            )

    async def discard_draft(self, draft_id: UUID) -> bool:
        """
        Discard a draft without publishing.

        Args:
            draft_id: UUID of the draft to discard.

        Returns:
            True if successful, False otherwise.
        """
        try:
            draft = (
                self.db.query(ScheduleDraft)
                .filter(ScheduleDraft.id == draft_id)
                .first()
            )

            if not draft:
                return False

            if draft.status != ScheduleDraftStatus.DRAFT:
                logger.warning(
                    f"Cannot discard draft {draft_id} with status {draft.status}"
                )
                return False

            draft.status = ScheduleDraftStatus.DISCARDED
            self.db.commit()

            logger.info(f"Discarded draft {draft_id}")
            return True

        except Exception as e:
            logger.exception(f"Failed to discard draft {draft_id}: {e}")
            self.db.rollback()
            return False

    async def get_active_draft_for_block(
        self,
        block_number: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> ScheduleDraft | None:
        """
        Get the active draft for a block or date range.

        Args:
            block_number: Block number to search for.
            start_date: Start date to search for.
            end_date: End date to search for.

        Returns:
            Active ScheduleDraft or None.
        """
        query = self.db.query(ScheduleDraft).filter(
            ScheduleDraft.status == ScheduleDraftStatus.DRAFT
        )

        if block_number is not None:
            query = query.filter(ScheduleDraft.target_block == block_number)

        if start_date and end_date:
            query = query.filter(
                ScheduleDraft.target_start_date == start_date,
                ScheduleDraft.target_end_date == end_date,
            )

        return query.first()

    async def list_drafts(
        self,
        status: ScheduleDraftStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ScheduleDraft]:
        """
        List drafts with optional status filter.

        Args:
            status: Filter by status (optional).
            limit: Maximum number of results.
            offset: Offset for pagination.

        Returns:
            List of ScheduleDraft objects.
        """
        query = self.db.query(ScheduleDraft).order_by(ScheduleDraft.created_at.desc())

        if status:
            query = query.filter(ScheduleDraft.status == status)

        return query.offset(offset).limit(limit).all()

    async def add_solver_assignments_to_draft(
        self,
        draft_id: UUID,
        assignments: list[Assignment],
        existing_ids: set[UUID] | None = None,
    ) -> int:
        """
        Bulk-add solver-generated assignments to a draft.

        This method takes Assignment objects from the scheduling engine and
        stages them in the draft. It determines change_type based on whether
        an existing assignment exists at the same slot.

        Args:
            draft_id: UUID of the draft.
            assignments: List of Assignment objects from solver.
            existing_ids: Set of existing assignment IDs to preserve.

        Returns:
            Number of assignments added to draft.
        """
        added_count = 0
        existing_ids = existing_ids or set()

        for assignment in assignments:
            # Skip preserved assignments (FMIT, absences, etc.)
            if assignment.id and assignment.id in existing_ids:
                continue

            # Determine change type - new assignment = ADD
            change_type = DraftAssignmentChangeType.ADD

            # Check if there's an existing live assignment at this slot
            # Assignment doesn't have date/time_of_day directly - access via block relationship
            from app.models.block import Block

            existing_assignment = (
                self.db.query(Assignment)
                .join(Block, Assignment.block_id == Block.id)
                .filter(
                    Assignment.person_id == assignment.person_id,
                    Block.date == assignment.block.date,
                    Block.time_of_day == assignment.block.time_of_day,
                )
                .first()
            )

            if existing_assignment:
                # Existing assignment - this is a MODIFY
                change_type = DraftAssignmentChangeType.MODIFY
                existing_assignment_id = existing_assignment.id
            else:
                existing_assignment_id = None

            # Create draft assignment
            # Access date/time_of_day via block relationship
            draft_assignment = ScheduleDraftAssignment(
                id=uuid4(),
                draft_id=draft_id,
                person_id=assignment.person_id,
                assignment_date=assignment.block.date,
                time_of_day=assignment.block.time_of_day
                or "ALL",  # Normalize None to ALL
                activity_code=getattr(assignment, "activity_code", None),
                rotation_id=assignment.rotation_template_id,
                change_type=change_type,
                existing_assignment_id=existing_assignment_id,
            )

            self.db.add(draft_assignment)
            added_count += 1

        # Update change summary in draft
        draft = (
            self.db.query(ScheduleDraft).filter(ScheduleDraft.id == draft_id).first()
        )
        if draft:
            add_count = sum(
                1
                for a in self.db.query(ScheduleDraftAssignment).filter(
                    ScheduleDraftAssignment.draft_id == draft_id,
                    ScheduleDraftAssignment.change_type
                    == DraftAssignmentChangeType.ADD,
                )
            )
            modify_count = sum(
                1
                for a in self.db.query(ScheduleDraftAssignment).filter(
                    ScheduleDraftAssignment.draft_id == draft_id,
                    ScheduleDraftAssignment.change_type
                    == DraftAssignmentChangeType.MODIFY,
                )
            )
            draft.change_summary = {
                "added": add_count,
                "modified": modify_count,
                "deleted": draft.change_summary.get("deleted", 0)
                if draft.change_summary
                else 0,
            }

        self.db.commit()
        logger.info(f"Added {added_count} solver assignments to draft {draft_id}")
        return added_count

    async def add_validation_flags_to_draft(
        self,
        draft_id: UUID,
        validation_result,
    ) -> int:
        """
        Add ACGME validation violations as flags to a draft.

        Args:
            draft_id: UUID of the draft.
            validation_result: ValidationResult from ACGMEValidator.

        Returns:
            Number of flags added.
        """
        flags_added = 0

        for violation in validation_result.violations:
            # Map violation type to flag type
            if "ACGME" in str(violation.type).upper() or "80" in str(violation.message):
                flag_type = DraftFlagType.ACGME_VIOLATION
            elif "coverage" in str(violation.type).lower():
                flag_type = DraftFlagType.COVERAGE_GAP
            elif "conflict" in str(violation.type).lower():
                flag_type = DraftFlagType.CONFLICT
            else:
                flag_type = DraftFlagType.MANUAL_REVIEW

            # Map severity
            severity_str = str(violation.severity).upper()
            if severity_str in ("CRITICAL", "HIGH"):
                severity = DraftFlagSeverity.ERROR
            elif severity_str == "MEDIUM":
                severity = DraftFlagSeverity.WARNING
            else:
                severity = DraftFlagSeverity.INFO

            # Create flag
            flag = ScheduleDraftFlag(
                id=uuid4(),
                draft_id=draft_id,
                flag_type=flag_type,
                severity=severity,
                message=violation.message,
                person_id=violation.person_id,
                affected_date=violation.details.get("date")
                if violation.details
                else None,
                created_at=datetime.utcnow(),
            )

            self.db.add(flag)
            flags_added += 1

        # Update flags_total in draft
        if flags_added > 0:
            draft = (
                self.db.query(ScheduleDraft)
                .filter(ScheduleDraft.id == draft_id)
                .first()
            )
            if draft:
                draft.flags_total = (draft.flags_total or 0) + flags_added

            self.db.commit()
            logger.info(f"Added {flags_added} validation flags to draft {draft_id}")

        return flags_added

    # =========================================================================
    # Sync versions for use from non-async contexts (e.g., scheduling engine)
    # =========================================================================

    def create_draft_sync(
        self,
        source_type: DraftSourceType,
        start_date: date,
        end_date: date,
        block_number: int | None = None,
        created_by_id: UUID | None = None,
        schedule_run_id: UUID | None = None,
        notes: str | None = None,
    ) -> CreateDraftResult:
        """
        Sync version of create_draft for use from non-async contexts.

        See create_draft() for full documentation.
        """
        try:
            # Check for existing active draft for this block/date range
            existing_draft = (
                self.db.query(ScheduleDraft)
                .filter(
                    ScheduleDraft.status == ScheduleDraftStatus.DRAFT,
                    ScheduleDraft.target_start_date == start_date,
                    ScheduleDraft.target_end_date == end_date,
                )
                .first()
            )

            if existing_draft:
                logger.info(
                    f"Found existing draft {existing_draft.id} for "
                    f"{start_date} - {end_date}"
                )
                return CreateDraftResult(
                    success=True,
                    draft_id=existing_draft.id,
                    message="Using existing draft for this date range",
                )

            # Create new draft
            draft = ScheduleDraft(
                id=uuid4(),
                created_at=datetime.utcnow(),
                created_by_id=created_by_id,
                target_block=block_number,
                target_start_date=start_date,
                target_end_date=end_date,
                status=ScheduleDraftStatus.DRAFT,
                source_type=source_type,
                source_schedule_run_id=schedule_run_id,
                notes=notes,
                change_summary={"added": 0, "modified": 0, "deleted": 0},
                flags_total=0,
                flags_acknowledged=0,
            )

            self.db.add(draft)
            self.db.commit()

            logger.info(
                f"Created draft {draft.id} for {start_date} - {end_date} "
                f"(block {block_number}, source={source_type.value})"
            )

            return CreateDraftResult(
                success=True,
                draft_id=draft.id,
                message=f"Created draft for Block {block_number or 'N/A'}",
            )

        except Exception as e:
            logger.exception(f"Failed to create draft: {e}")
            self.db.rollback()
            return CreateDraftResult(
                success=False,
                message=f"Failed to create draft: {str(e)}",
                error_code="CREATE_FAILED",
            )

    def add_solver_assignments_to_draft_sync(
        self,
        draft_id: UUID,
        assignments: list[Assignment],
        existing_ids: set[UUID] | None = None,
    ) -> int:
        """
        Sync version of add_solver_assignments_to_draft for use from non-async contexts.

        See add_solver_assignments_to_draft() for full documentation.
        """
        added_count = 0
        existing_ids = existing_ids or set()

        for assignment in assignments:
            # Skip preserved assignments (FMIT, absences, etc.)
            if assignment.id and assignment.id in existing_ids:
                continue

            # Determine change type - new assignment = ADD
            change_type = DraftAssignmentChangeType.ADD

            # Check if there's an existing live assignment at this slot
            # Assignment doesn't have date/time_of_day directly - access via block relationship
            from app.models.block import Block

            existing_assignment = (
                self.db.query(Assignment)
                .join(Block, Assignment.block_id == Block.id)
                .filter(
                    Assignment.person_id == assignment.person_id,
                    Block.date == assignment.block.date,
                    Block.time_of_day == assignment.block.time_of_day,
                )
                .first()
            )

            if existing_assignment:
                # Existing assignment - this is a MODIFY
                change_type = DraftAssignmentChangeType.MODIFY
                existing_assignment_id = existing_assignment.id
            else:
                existing_assignment_id = None

            # Create draft assignment
            # Access date/time_of_day via block relationship
            draft_assignment = ScheduleDraftAssignment(
                id=uuid4(),
                draft_id=draft_id,
                person_id=assignment.person_id,
                assignment_date=assignment.block.date,
                time_of_day=assignment.block.time_of_day or "ALL",
                activity_code=getattr(assignment, "activity_code", None),
                rotation_id=assignment.rotation_template_id,
                change_type=change_type,
                existing_assignment_id=existing_assignment_id,
            )

            self.db.add(draft_assignment)
            added_count += 1

        # Update change summary in draft
        draft = (
            self.db.query(ScheduleDraft).filter(ScheduleDraft.id == draft_id).first()
        )
        if draft:
            add_count = sum(
                1
                for a in self.db.query(ScheduleDraftAssignment).filter(
                    ScheduleDraftAssignment.draft_id == draft_id,
                    ScheduleDraftAssignment.change_type
                    == DraftAssignmentChangeType.ADD,
                )
            )
            modify_count = sum(
                1
                for a in self.db.query(ScheduleDraftAssignment).filter(
                    ScheduleDraftAssignment.draft_id == draft_id,
                    ScheduleDraftAssignment.change_type
                    == DraftAssignmentChangeType.MODIFY,
                )
            )
            draft.change_summary = {
                "added": add_count,
                "modified": modify_count,
                "deleted": draft.change_summary.get("deleted", 0)
                if draft.change_summary
                else 0,
            }

        self.db.commit()
        logger.info(f"Added {added_count} solver assignments to draft {draft_id}")
        return added_count

    def add_validation_flags_to_draft_sync(
        self,
        draft_id: UUID,
        validation_result,
    ) -> int:
        """
        Sync version of add_validation_flags_to_draft for use from non-async contexts.

        See add_validation_flags_to_draft() for full documentation.
        """
        flags_added = 0

        for violation in validation_result.violations:
            # Map violation type to flag type
            if "ACGME" in str(violation.type).upper() or "80" in str(violation.message):
                flag_type = DraftFlagType.ACGME_VIOLATION
            elif "coverage" in str(violation.type).lower():
                flag_type = DraftFlagType.COVERAGE_GAP
            elif "conflict" in str(violation.type).lower():
                flag_type = DraftFlagType.CONFLICT
            else:
                flag_type = DraftFlagType.MANUAL_REVIEW

            # Map severity
            severity_str = str(violation.severity).upper()
            if severity_str in ("CRITICAL", "HIGH"):
                severity = DraftFlagSeverity.ERROR
            elif severity_str == "MEDIUM":
                severity = DraftFlagSeverity.WARNING
            else:
                severity = DraftFlagSeverity.INFO

            # Create flag
            flag = ScheduleDraftFlag(
                id=uuid4(),
                draft_id=draft_id,
                flag_type=flag_type,
                severity=severity,
                message=violation.message,
                person_id=violation.person_id,
                affected_date=violation.details.get("date")
                if violation.details
                else None,
                created_at=datetime.utcnow(),
            )

            self.db.add(flag)
            flags_added += 1

        # Update flags_total in draft
        if flags_added > 0:
            draft = (
                self.db.query(ScheduleDraft)
                .filter(ScheduleDraft.id == draft_id)
                .first()
            )
            if draft:
                draft.flags_total = (draft.flags_total or 0) + flags_added

            self.db.commit()
            logger.info(f"Added {flags_added} validation flags to draft {draft_id}")

        return flags_added
