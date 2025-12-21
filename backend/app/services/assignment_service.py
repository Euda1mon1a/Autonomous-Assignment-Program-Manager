"""Assignment service for business logic."""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.settings import OverrideReasonCode
from app.repositories.assignment import AssignmentRepository
from app.repositories.block import BlockRepository
from app.repositories.person import PersonRepository
from app.scheduling.validator import ACGMEValidator
from app.services.freeze_horizon_service import (
    FreezeHorizonService,
    FreezeHorizonViolation,
    FreezeOverrideRequest,
)


class AssignmentService:
    """Service for assignment business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.assignment_repo = AssignmentRepository(db)
        self.block_repo = BlockRepository(db)
        self.person_repo = PersonRepository(db)
        self.freeze_service = FreezeHorizonService(db)

    def get_assignment(self, assignment_id: UUID) -> Assignment | None:
        """
        Get a single assignment by ID with eager loading.

        N+1 Optimization: Uses selectinload to eagerly fetch related Person, Block,
        and RotationTemplate entities in a single query batch, preventing N+1 queries
        when accessing assignment.person, assignment.block, or assignment.rotation_template.
        """
        return self.assignment_repo.get_by_id_with_relations(assignment_id)

    def list_assignments(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        person_id: UUID | None = None,
        role: str | None = None,
        activity_type: str | None = None,
    ) -> dict:
        """
        List assignments with optional filters.

        N+1 Optimization: The repository's list_with_filters method uses joinedload
        to eagerly fetch Person, Block, and RotationTemplate relationships, preventing
        N+1 queries when iterating over results.
        """
        assignments = self.assignment_repo.list_with_filters(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
            role=role,
            activity_type=activity_type,
        )
        return {"items": assignments, "total": len(assignments)}

    def create_assignment(
        self,
        block_id: UUID,
        person_id: UUID,
        role: str,
        created_by: str,
        override_reason: str | None = None,
        rotation_template_id: UUID | None = None,
        activity_type: str | None = None,
        notes: str | None = None,
        # Freeze horizon override parameters
        freeze_override_reason_code: OverrideReasonCode | None = None,
        freeze_override_reason_text: str | None = None,
        initiating_module: str = "manual",
    ) -> dict:
        """
        Create a new assignment with ACGME validation and freeze horizon check.

        Returns dict with:
        - assignment: The created assignment
        - acgme_warnings: List of ACGME compliance warnings
        - is_compliant: Whether the assignment is ACGME compliant
        - freeze_status: Freeze horizon check result
        - error: Error message if creation failed
        """
        # Get block to check freeze horizon
        block = self.block_repo.get_by_id(block_id)
        if not block:
            return {
                "assignment": None,
                "error": "Block not found",
                "freeze_status": None,
            }

        # Check freeze horizon
        freeze_override = None
        if freeze_override_reason_code and freeze_override_reason_text:
            freeze_override = FreezeOverrideRequest(
                reason_code=freeze_override_reason_code,
                reason_text=freeze_override_reason_text,
                initiated_by=created_by,
                initiating_module=initiating_module,
            )

        try:
            freeze_result = self.freeze_service.enforce_freeze_or_override(
                block_date=block.date,
                override_request=freeze_override,
                block_id=block_id,
            )
        except FreezeHorizonViolation as e:
            return {
                "assignment": None,
                "error": e.check_result.message,
                "freeze_status": e.check_result.to_dict(),
            }

        # Check for duplicate
        existing = self.assignment_repo.get_by_block_and_person(block_id, person_id)
        if existing:
            return {
                "assignment": None,
                "error": "Person already assigned to this block",
                "freeze_status": freeze_result.to_dict(),
            }

        # Build assignment data
        assignment_data = {
            "block_id": block_id,
            "person_id": person_id,
            "role": role,
            "created_by": created_by,
        }
        if rotation_template_id:
            assignment_data["rotation_template_id"] = rotation_template_id
        if activity_type:
            assignment_data["activity_type"] = activity_type
        if notes:
            assignment_data["notes"] = notes

        # Create assignment
        assignment = self.assignment_repo.create(assignment_data)

        # Update audit record with assignment ID if freeze was overridden
        if freeze_result.is_frozen and freeze_override:
            self.freeze_service.create_audit_record(
                assignment_id=assignment.id,
                block_id=block_id,
                block_date=block.date,
                freeze_result=freeze_result,
                override_request=freeze_override,
            )

        # Validate ACGME compliance
        validation = self._validate_acgme(assignment, override_reason)

        # Add override note if provided
        if override_reason and validation["warnings"]:
            existing_notes = assignment.notes or ""
            override_note = f"\nACGME Override: {override_reason}"
            assignment.notes = (existing_notes + override_note).strip()

        self.assignment_repo.commit()
        self.assignment_repo.refresh(assignment)

        return {
            "assignment": assignment,
            "acgme_warnings": validation["warnings"],
            "is_compliant": validation["is_compliant"],
            "freeze_status": freeze_result.to_dict(),
            "error": None,
        }

    def update_assignment(
        self,
        assignment_id: UUID,
        update_data: dict,
        expected_updated_at,
        override_reason: str | None = None,
        # Freeze horizon override parameters
        freeze_override_reason_code: OverrideReasonCode | None = None,
        freeze_override_reason_text: str | None = None,
        updated_by: str = "unknown",
        initiating_module: str = "manual",
    ) -> dict:
        """
        Update an assignment with optimistic locking and freeze horizon check.

        Returns dict with:
        - assignment: The updated assignment
        - acgme_warnings: List of ACGME compliance warnings
        - is_compliant: Whether the assignment is ACGME compliant
        - freeze_status: Freeze horizon check result
        - error: Error message if update failed
        """
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            return {"assignment": None, "error": "Assignment not found", "freeze_status": None}

        # Get block for freeze horizon check
        block = self.block_repo.get_by_id(assignment.block_id)
        if not block:
            return {"assignment": None, "error": "Block not found", "freeze_status": None}

        # Check freeze horizon
        freeze_override = None
        if freeze_override_reason_code and freeze_override_reason_text:
            freeze_override = FreezeOverrideRequest(
                reason_code=freeze_override_reason_code,
                reason_text=freeze_override_reason_text,
                initiated_by=updated_by,
                initiating_module=initiating_module,
            )

        try:
            freeze_result = self.freeze_service.enforce_freeze_or_override(
                block_date=block.date,
                override_request=freeze_override,
                assignment_id=assignment_id,
                block_id=assignment.block_id,
            )
        except FreezeHorizonViolation as e:
            return {
                "assignment": None,
                "error": e.check_result.message,
                "freeze_status": e.check_result.to_dict(),
            }

        # Optimistic locking check
        if assignment.updated_at != expected_updated_at:
            return {
                "assignment": None,
                "error": f"Assignment has been modified by another user. "
                f"Current version: {assignment.updated_at}, Your version: {expected_updated_at}",
                "freeze_status": freeze_result.to_dict(),
            }

        # Update assignment
        assignment = self.assignment_repo.update(assignment, update_data)

        # Validate ACGME compliance
        validation = self._validate_acgme(assignment, override_reason)

        # Add override note if provided
        if override_reason and validation["warnings"]:
            existing_notes = assignment.notes or ""
            override_note = f"\nACGME Override: {override_reason}"
            assignment.notes = (existing_notes + override_note).strip()

        self.assignment_repo.commit()
        self.assignment_repo.refresh(assignment)

        return {
            "assignment": assignment,
            "acgme_warnings": validation["warnings"],
            "is_compliant": validation["is_compliant"],
            "freeze_status": freeze_result.to_dict(),
            "error": None,
        }

    def delete_assignment(
        self,
        assignment_id: UUID,
        # Freeze horizon override parameters
        freeze_override_reason_code: OverrideReasonCode | None = None,
        freeze_override_reason_text: str | None = None,
        deleted_by: str = "unknown",
        initiating_module: str = "manual",
    ) -> dict:
        """Delete an assignment with freeze horizon check."""
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            return {"success": False, "error": "Assignment not found", "freeze_status": None}

        # Get block for freeze horizon check
        block = self.block_repo.get_by_id(assignment.block_id)
        if not block:
            return {"success": False, "error": "Block not found", "freeze_status": None}

        # Check freeze horizon
        freeze_override = None
        if freeze_override_reason_code and freeze_override_reason_text:
            freeze_override = FreezeOverrideRequest(
                reason_code=freeze_override_reason_code,
                reason_text=freeze_override_reason_text,
                initiated_by=deleted_by,
                initiating_module=initiating_module,
            )

        try:
            freeze_result = self.freeze_service.enforce_freeze_or_override(
                block_date=block.date,
                override_request=freeze_override,
                assignment_id=assignment_id,
                block_id=assignment.block_id,
            )
        except FreezeHorizonViolation as e:
            return {
                "success": False,
                "error": e.check_result.message,
                "freeze_status": e.check_result.to_dict(),
            }

        self.assignment_repo.delete(assignment)
        self.assignment_repo.commit()
        return {"success": True, "error": None, "freeze_status": freeze_result.to_dict()}

    def delete_assignments_bulk(
        self,
        start_date: date,
        end_date: date,
        # Freeze horizon override parameters
        freeze_override_reason_code: OverrideReasonCode | None = None,
        freeze_override_reason_text: str | None = None,
        deleted_by: str = "unknown",
        initiating_module: str = "planning",
    ) -> dict:
        """
        Delete all assignments in a date range with freeze horizon check.

        For bulk operations, we check if ANY assignments fall within the freeze horizon.
        If so, ALL deletions require override (or we reject the entire operation).
        """
        block_ids = self.block_repo.get_ids_in_date_range(start_date, end_date)

        # Check freeze horizon for the entire date range
        settings = self.freeze_service.get_settings()
        today = date.today()
        freeze_end = today + timedelta(days=settings.freeze_horizon_days)

        # Any overlap with freeze horizon?
        has_frozen_assignments = start_date <= freeze_end

        if has_frozen_assignments and settings.freeze_scope != "none":
            # Need override for bulk delete that touches freeze horizon
            freeze_override = None
            if freeze_override_reason_code and freeze_override_reason_text:
                freeze_override = FreezeOverrideRequest(
                    reason_code=freeze_override_reason_code,
                    reason_text=freeze_override_reason_text,
                    initiated_by=deleted_by,
                    initiating_module=initiating_module,
                )

            # Use earliest affected date for freeze check
            check_date = max(start_date, today)
            try:
                freeze_result = self.freeze_service.enforce_freeze_or_override(
                    block_date=check_date,
                    override_request=freeze_override,
                )
            except FreezeHorizonViolation as e:
                return {
                    "deleted": 0,
                    "error": f"Bulk delete blocked: {e.check_result.message}",
                    "freeze_status": e.check_result.to_dict(),
                }

        deleted_count = self.assignment_repo.delete_by_block_ids(block_ids)
        self.assignment_repo.commit()
        return {"deleted": deleted_count, "error": None, "freeze_status": None}

    def _validate_acgme(
        self,
        assignment: Assignment,
        override_reason: str | None = None,
    ) -> dict:
        """
        Validate ACGME compliance for a single assignment.

        Returns dict with:
        - violations: List of Violation objects
        - warnings: List of warning messages
        - is_compliant: boolean
        """
        block = self.block_repo.get_by_id(assignment.block_id)
        if not block:
            return {"violations": [], "warnings": [], "is_compliant": True}

        # Validate a window around the assignment date (+/- 4 weeks)
        start_date = block.date - timedelta(weeks=4)
        end_date = block.date + timedelta(weeks=4)

        validator = ACGMEValidator(self.db)
        result = validator.validate_all(start_date, end_date)

        # Filter violations related to this person
        person = self.person_repo.get_by_id(assignment.person_id)
        relevant_violations = []
        if person and person.type == "resident":
            relevant_violations = [
                v for v in result.violations if v.person_id == assignment.person_id
            ]

        # Build warnings list
        warnings = []
        for violation in relevant_violations:
            warnings.append(f"{violation.severity}: {violation.message}")

        if relevant_violations and override_reason:
            warnings.append(f"Override acknowledged: {override_reason}")

        return {
            "violations": relevant_violations,
            "warnings": warnings,
            "is_compliant": len(relevant_violations) == 0,
        }
