"""Batch operation validator."""
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.repositories.assignment import AssignmentRepository
from app.repositories.block import BlockRepository
from app.repositories.person import PersonRepository
from app.schemas.batch import (
    BatchAssignmentCreate,
    BatchAssignmentDelete,
    BatchAssignmentUpdate,
    BatchOperationResult,
    BatchValidationResult,
)
from app.scheduling.validator import ACGMEValidator


class BatchValidator:
    """Validator for batch operations."""

    def __init__(self, db: Session):
        self.db = db
        self.assignment_repo = AssignmentRepository(db)
        self.block_repo = BlockRepository(db)
        self.person_repo = PersonRepository(db)

    def validate_create_batch(
        self,
        assignments: list[BatchAssignmentCreate],
        validate_acgme: bool = True,
    ) -> BatchValidationResult:
        """
        Validate a batch of assignment creations.

        Args:
            assignments: List of assignments to create
            validate_acgme: Whether to validate ACGME compliance

        Returns:
            BatchValidationResult with validation status and errors
        """
        validation_errors = []
        operation_errors = []

        # Check batch size
        if len(assignments) > 1000:
            validation_errors.append("Batch size exceeds maximum of 1000 operations")
            return BatchValidationResult(
                valid=False,
                total_operations=len(assignments),
                validation_errors=validation_errors,
            )

        # Check for duplicates within batch
        seen_pairs = set()
        for idx, assignment in enumerate(assignments):
            pair = (str(assignment.block_id), str(assignment.person_id))
            if pair in seen_pairs:
                operation_errors.append(
                    BatchOperationResult(
                        index=idx,
                        success=False,
                        error=f"Duplicate block-person pair in batch: {pair}",
                    )
                )
            seen_pairs.add(pair)

        # Validate each assignment
        for idx, assignment in enumerate(assignments):
            result = self._validate_single_create(assignment, idx)
            if not result.success:
                operation_errors.append(result)

        # Validate ACGME compliance if requested
        acgme_warnings = []
        if validate_acgme and not operation_errors:
            acgme_warnings = self._validate_acgme_batch(assignments)

        is_valid = len(validation_errors) == 0 and len(operation_errors) == 0

        return BatchValidationResult(
            valid=is_valid,
            total_operations=len(assignments),
            validation_errors=validation_errors,
            operation_errors=operation_errors,
            acgme_warnings=acgme_warnings,
        )

    def validate_update_batch(
        self,
        assignments: list[BatchAssignmentUpdate],
        validate_acgme: bool = True,
    ) -> BatchValidationResult:
        """
        Validate a batch of assignment updates.

        Args:
            assignments: List of assignments to update
            validate_acgme: Whether to validate ACGME compliance

        Returns:
            BatchValidationResult with validation status and errors
        """
        validation_errors = []
        operation_errors = []

        # Check batch size
        if len(assignments) > 1000:
            validation_errors.append("Batch size exceeds maximum of 1000 operations")
            return BatchValidationResult(
                valid=False,
                total_operations=len(assignments),
                validation_errors=validation_errors,
            )

        # Check for duplicate assignment IDs in batch
        seen_ids = set()
        for idx, assignment in enumerate(assignments):
            if assignment.assignment_id in seen_ids:
                operation_errors.append(
                    BatchOperationResult(
                        index=idx,
                        success=False,
                        assignment_id=assignment.assignment_id,
                        error=f"Duplicate assignment ID in batch: {assignment.assignment_id}",
                    )
                )
            seen_ids.add(assignment.assignment_id)

        # Validate each assignment
        for idx, assignment in enumerate(assignments):
            result = self._validate_single_update(assignment, idx)
            if not result.success:
                operation_errors.append(result)

        # Validate ACGME compliance if requested (skip for now as updates are complex)
        acgme_warnings = []

        is_valid = len(validation_errors) == 0 and len(operation_errors) == 0

        return BatchValidationResult(
            valid=is_valid,
            total_operations=len(assignments),
            validation_errors=validation_errors,
            operation_errors=operation_errors,
            acgme_warnings=acgme_warnings,
        )

    def validate_delete_batch(
        self,
        assignments: list[BatchAssignmentDelete],
    ) -> BatchValidationResult:
        """
        Validate a batch of assignment deletions.

        Args:
            assignments: List of assignments to delete

        Returns:
            BatchValidationResult with validation status and errors
        """
        validation_errors = []
        operation_errors = []

        # Check batch size
        if len(assignments) > 1000:
            validation_errors.append("Batch size exceeds maximum of 1000 operations")
            return BatchValidationResult(
                valid=False,
                total_operations=len(assignments),
                validation_errors=validation_errors,
            )

        # Check for duplicate assignment IDs in batch
        seen_ids = set()
        for idx, assignment in enumerate(assignments):
            if assignment.assignment_id in seen_ids:
                operation_errors.append(
                    BatchOperationResult(
                        index=idx,
                        success=False,
                        assignment_id=assignment.assignment_id,
                        error=f"Duplicate assignment ID in batch: {assignment.assignment_id}",
                    )
                )
            seen_ids.add(assignment.assignment_id)

        # Validate each assignment exists
        for idx, assignment in enumerate(assignments):
            result = self._validate_single_delete(assignment, idx)
            if not result.success:
                operation_errors.append(result)

        is_valid = len(validation_errors) == 0 and len(operation_errors) == 0

        return BatchValidationResult(
            valid=is_valid,
            total_operations=len(assignments),
            validation_errors=validation_errors,
            operation_errors=operation_errors,
        )

    def _validate_single_create(
        self,
        assignment: BatchAssignmentCreate,
        index: int,
    ) -> BatchOperationResult:
        """Validate a single assignment creation."""
        # Check if block exists
        block = self.block_repo.get_by_id(assignment.block_id)
        if not block:
            return BatchOperationResult(
                index=index,
                success=False,
                error=f"Block not found: {assignment.block_id}",
            )

        # Check if person exists
        person = self.person_repo.get_by_id(assignment.person_id)
        if not person:
            return BatchOperationResult(
                index=index,
                success=False,
                error=f"Person not found: {assignment.person_id}",
            )

        # Check if assignment already exists
        existing = self.assignment_repo.get_by_block_and_person(
            assignment.block_id,
            assignment.person_id,
        )
        if existing:
            return BatchOperationResult(
                index=index,
                success=False,
                assignment_id=existing.id,
                error=f"Assignment already exists for person {assignment.person_id} on block {assignment.block_id}",
            )

        return BatchOperationResult(index=index, success=True)

    def _validate_single_update(
        self,
        assignment: BatchAssignmentUpdate,
        index: int,
    ) -> BatchOperationResult:
        """Validate a single assignment update."""
        # Check if assignment exists
        existing = self.assignment_repo.get_by_id(assignment.assignment_id)
        if not existing:
            return BatchOperationResult(
                index=index,
                success=False,
                assignment_id=assignment.assignment_id,
                error=f"Assignment not found: {assignment.assignment_id}",
            )

        # Check optimistic locking
        if existing.updated_at != assignment.updated_at:
            return BatchOperationResult(
                index=index,
                success=False,
                assignment_id=assignment.assignment_id,
                error=f"Assignment has been modified. Expected version: {assignment.updated_at}, "
                      f"Current version: {existing.updated_at}",
            )

        return BatchOperationResult(
            index=index,
            success=True,
            assignment_id=assignment.assignment_id,
        )

    def _validate_single_delete(
        self,
        assignment: BatchAssignmentDelete,
        index: int,
    ) -> BatchOperationResult:
        """Validate a single assignment deletion."""
        # Check if assignment exists
        existing = self.assignment_repo.get_by_id(assignment.assignment_id)
        if not existing:
            return BatchOperationResult(
                index=index,
                success=False,
                assignment_id=assignment.assignment_id,
                error=f"Assignment not found: {assignment.assignment_id}",
            )

        return BatchOperationResult(
            index=index,
            success=True,
            assignment_id=assignment.assignment_id,
        )

    def _validate_acgme_batch(
        self,
        assignments: list[BatchAssignmentCreate],
    ) -> list[str]:
        """
        Validate ACGME compliance for a batch of assignments.

        Returns list of warning messages.
        """
        warnings = []

        if not assignments:
            return warnings

        # Get date range from assignments
        block_ids = [a.block_id for a in assignments]
        blocks = [self.block_repo.get_by_id(bid) for bid in block_ids]
        blocks = [b for b in blocks if b is not None]

        if not blocks:
            return warnings

        dates = [b.date for b in blocks]
        min_date = min(dates)
        max_date = max(dates)

        # Expand window for rolling average validation
        start_date = min_date - timedelta(weeks=4)
        end_date = max_date + timedelta(weeks=4)

        # Run ACGME validation
        validator = ACGMEValidator(self.db)
        result = validator.validate_all(start_date, end_date)

        # Collect warnings
        if result.violations:
            warnings.append(
                f"ACGME validation found {len(result.violations)} violations "
                f"in date range {start_date} to {end_date}"
            )
            # Add first 5 violations as examples
            for violation in result.violations[:5]:
                warnings.append(f"  - {violation.severity}: {violation.message}")
            if len(result.violations) > 5:
                warnings.append(f"  ... and {len(result.violations) - 5} more violations")

        return warnings
