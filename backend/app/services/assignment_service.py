"""Assignment service for business logic."""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.repositories.assignment import AssignmentRepository
from app.repositories.block import BlockRepository
from app.repositories.person import PersonRepository
from app.scheduling.validator import ACGMEValidator


class AssignmentService:
    """Service for assignment business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.assignment_repo = AssignmentRepository(db)
        self.block_repo = BlockRepository(db)
        self.person_repo = PersonRepository(db)

    def get_assignment(self, assignment_id: UUID) -> Assignment | None:
        """Get a single assignment by ID."""
        return self.assignment_repo.get_by_id(assignment_id)

    def list_assignments(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        person_id: UUID | None = None,
        role: str | None = None,
        activity_type: str | None = None,
    ) -> dict:
        """List assignments with optional filters."""
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
    ) -> dict:
        """
        Create a new assignment with ACGME validation.

        Returns dict with:
        - assignment: The created assignment
        - acgme_warnings: List of ACGME compliance warnings
        - is_compliant: Whether the assignment is ACGME compliant
        - error: Error message if creation failed
        """
        # Check for duplicate
        existing = self.assignment_repo.get_by_block_and_person(block_id, person_id)
        if existing:
            return {
                "assignment": None,
                "error": "Person already assigned to this block",
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
            "error": None,
        }

    def update_assignment(
        self,
        assignment_id: UUID,
        update_data: dict,
        expected_updated_at,
        override_reason: str | None = None,
    ) -> dict:
        """
        Update an assignment with optimistic locking.

        Returns dict with:
        - assignment: The updated assignment
        - acgme_warnings: List of ACGME compliance warnings
        - is_compliant: Whether the assignment is ACGME compliant
        - error: Error message if update failed
        """
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            return {"assignment": None, "error": "Assignment not found"}

        # Optimistic locking check
        if assignment.updated_at != expected_updated_at:
            return {
                "assignment": None,
                "error": f"Assignment has been modified by another user. "
                f"Current version: {assignment.updated_at}, Your version: {expected_updated_at}",
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
            "error": None,
        }

    def delete_assignment(self, assignment_id: UUID) -> dict:
        """Delete an assignment."""
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            return {"success": False, "error": "Assignment not found"}

        self.assignment_repo.delete(assignment)
        self.assignment_repo.commit()
        return {"success": True, "error": None}

    def delete_assignments_bulk(self, start_date: date, end_date: date) -> dict:
        """Delete all assignments in a date range."""
        block_ids = self.block_repo.get_ids_in_date_range(start_date, end_date)
        deleted_count = self.assignment_repo.delete_by_block_ids(block_ids)
        self.assignment_repo.commit()
        return {"deleted": deleted_count}

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
