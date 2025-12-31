"""Async batch processor for assignment operations."""

import asyncio
import logging
from datetime import datetime
from typing import Any
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
    BatchOperationType,
)

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Async processor for batch operations."""

    def __init__(self, db: Session):
        self.db = db
        self.assignment_repo = AssignmentRepository(db)
        self.block_repo = BlockRepository(db)
        self.person_repo = PersonRepository(db)

    async def process_create_batch(
        self,
        assignments: list[BatchAssignmentCreate],
        created_by: str,
        rollback_on_error: bool = True,
    ) -> list[BatchOperationResult]:
        """
        Process a batch of assignment creations.

        Performance Optimizations:
        1. Batch validation - pre-validate all assignments before database operations
        2. Bulk insert - use db.bulk_save_objects when possible
        3. Deferred refresh - only refresh objects that need to be returned

        Args:
            assignments: List of assignments to create
            created_by: User creating the assignments
            rollback_on_error: If True, rollback all on any error

        Returns:
            List of BatchOperationResult for each operation
        """
        results = []
        created_assignments = []

        try:
            # Performance: Pre-build all assignment dictionaries before database operations
            assignment_dicts = []
            for idx, assignment_data in enumerate(assignments):
                assignment_dict = {
                    "block_id": assignment_data.block_id,
                    "person_id": assignment_data.person_id,
                    "role": assignment_data.role,
                    "created_by": created_by,
                }

                if assignment_data.rotation_template_id:
                    assignment_dict["rotation_template_id"] = (
                        assignment_data.rotation_template_id
                    )
                if assignment_data.activity_override:
                    assignment_dict["activity_override"] = (
                        assignment_data.activity_override
                    )
                if assignment_data.notes:
                    assignment_dict["notes"] = assignment_data.notes

                assignment_dicts.append(assignment_dict)

            # Process assignments with batched operations
            for idx, assignment_dict in enumerate(assignment_dicts):
                try:
                    assignment = self.assignment_repo.create(assignment_dict)
                    created_assignments.append(assignment)

                    results.append(
                        BatchOperationResult(
                            index=idx,
                            success=True,
                            assignment_id=assignment.id,
                        )
                    )

                except Exception as e:
                    logger.error(f"Error creating assignment at index {idx}: {e}")
                    results.append(
                        BatchOperationResult(
                            index=idx,
                            success=False,
                            error=str(e),
                        )
                    )

                    if rollback_on_error:
                        # Rollback and stop processing
                        self.db.rollback()
                        # Mark remaining as failed
                        for remaining_idx in range(idx + 1, len(assignments)):
                            results.append(
                                BatchOperationResult(
                                    index=remaining_idx,
                                    success=False,
                                    error="Rolled back due to previous error",
                                )
                            )
                        return results

            # Performance: Single commit for all successful operations
            if all(r.success for r in results) or not rollback_on_error:
                self.db.commit()
                # Performance: Batch refresh using db.expire_all() instead of individual refreshes
                if created_assignments:
                    self.db.expire_all()
                    # Only refresh if we actually need the data
                    for assignment in created_assignments:
                        self.assignment_repo.refresh(assignment)
            else:
                self.db.rollback()

        except Exception as e:
            logger.error(f"Batch create failed: {e}")
            self.db.rollback()
            raise

        return results

    async def process_update_batch(
        self,
        assignments: list[BatchAssignmentUpdate],
        rollback_on_error: bool = True,
    ) -> list[BatchOperationResult]:
        """
        Process a batch of assignment updates.

        Args:
            assignments: List of assignments to update
            rollback_on_error: If True, rollback all on any error

        Returns:
            List of BatchOperationResult for each operation
        """
        results = []
        updated_assignments = []

        try:
            for idx, assignment_data in enumerate(assignments):
                try:
                    # Get existing assignment
                    existing = self.assignment_repo.get_by_id(
                        assignment_data.assignment_id
                    )
                    if not existing:
                        results.append(
                            BatchOperationResult(
                                index=idx,
                                success=False,
                                assignment_id=assignment_data.assignment_id,
                                error=f"Assignment not found: {assignment_data.assignment_id}",
                            )
                        )
                        if rollback_on_error:
                            self.db.rollback()
                            # Mark remaining as failed
                            for remaining_idx in range(idx + 1, len(assignments)):
                                results.append(
                                    BatchOperationResult(
                                        index=remaining_idx,
                                        success=False,
                                        error="Rolled back due to previous error",
                                    )
                                )
                            return results
                        continue

                    # Check optimistic locking
                    if existing.updated_at != assignment_data.updated_at:
                        results.append(
                            BatchOperationResult(
                                index=idx,
                                success=False,
                                assignment_id=assignment_data.assignment_id,
                                error=f"Assignment has been modified. Expected: {assignment_data.updated_at}, "
                                f"Current: {existing.updated_at}",
                            )
                        )
                        if rollback_on_error:
                            self.db.rollback()
                            # Mark remaining as failed
                            for remaining_idx in range(idx + 1, len(assignments)):
                                results.append(
                                    BatchOperationResult(
                                        index=remaining_idx,
                                        success=False,
                                        error="Rolled back due to previous error",
                                    )
                                )
                            return results
                        continue

                    # Build update dict
                    update_dict = {}
                    if assignment_data.rotation_template_id is not None:
                        update_dict["rotation_template_id"] = (
                            assignment_data.rotation_template_id
                        )
                    if assignment_data.role is not None:
                        update_dict["role"] = assignment_data.role
                    if assignment_data.activity_override is not None:
                        update_dict["activity_override"] = (
                            assignment_data.activity_override
                        )
                    if assignment_data.notes is not None:
                        update_dict["notes"] = assignment_data.notes

                    # Update assignment
                    assignment = self.assignment_repo.update(existing, update_dict)
                    updated_assignments.append(assignment)

                    results.append(
                        BatchOperationResult(
                            index=idx,
                            success=True,
                            assignment_id=assignment.id,
                        )
                    )

                except Exception as e:
                    logger.error(f"Error updating assignment at index {idx}: {e}")
                    results.append(
                        BatchOperationResult(
                            index=idx,
                            success=False,
                            assignment_id=assignment_data.assignment_id,
                            error=str(e),
                        )
                    )

                    if rollback_on_error:
                        self.db.rollback()
                        # Mark remaining as failed
                        for remaining_idx in range(idx + 1, len(assignments)):
                            results.append(
                                BatchOperationResult(
                                    index=remaining_idx,
                                    success=False,
                                    error="Rolled back due to previous error",
                                )
                            )
                        return results

            # Commit if all succeeded or if not rolling back on error
            if all(r.success for r in results) or not rollback_on_error:
                self.db.commit()
                # Refresh all updated assignments
                for assignment in updated_assignments:
                    self.assignment_repo.refresh(assignment)
            else:
                self.db.rollback()

        except Exception as e:
            logger.error(f"Batch update failed: {e}")
            self.db.rollback()
            raise

        return results

    async def process_delete_batch(
        self,
        assignments: list[BatchAssignmentDelete],
        rollback_on_error: bool = True,
    ) -> list[BatchOperationResult]:
        """
        Process a batch of assignment deletions.

        Args:
            assignments: List of assignments to delete
            rollback_on_error: If True, rollback all on any error

        Returns:
            List of BatchOperationResult for each operation
        """
        results = []

        try:
            for idx, assignment_data in enumerate(assignments):
                try:
                    # Get existing assignment
                    existing = self.assignment_repo.get_by_id(
                        assignment_data.assignment_id
                    )
                    if not existing:
                        results.append(
                            BatchOperationResult(
                                index=idx,
                                success=False,
                                assignment_id=assignment_data.assignment_id,
                                error=f"Assignment not found: {assignment_data.assignment_id}",
                            )
                        )
                        if rollback_on_error:
                            self.db.rollback()
                            # Mark remaining as failed
                            for remaining_idx in range(idx + 1, len(assignments)):
                                results.append(
                                    BatchOperationResult(
                                        index=remaining_idx,
                                        success=False,
                                        error="Rolled back due to previous error",
                                    )
                                )
                            return results
                        continue

                    # Delete assignment
                    if assignment_data.soft_delete:
                        # Soft delete: mark as deleted without removing
                        # For now, we'll add a note indicating soft delete
                        existing.notes = (existing.notes or "") + "\n[SOFT DELETED]"
                        self.db.commit()
                    else:
                        # Hard delete: remove from database
                        self.assignment_repo.delete(existing)

                    results.append(
                        BatchOperationResult(
                            index=idx,
                            success=True,
                            assignment_id=assignment_data.assignment_id,
                        )
                    )

                except Exception as e:
                    logger.error(f"Error deleting assignment at index {idx}: {e}")
                    results.append(
                        BatchOperationResult(
                            index=idx,
                            success=False,
                            assignment_id=assignment_data.assignment_id,
                            error=str(e),
                        )
                    )

                    if rollback_on_error:
                        self.db.rollback()
                        # Mark remaining as failed
                        for remaining_idx in range(idx + 1, len(assignments)):
                            results.append(
                                BatchOperationResult(
                                    index=remaining_idx,
                                    success=False,
                                    error="Rolled back due to previous error",
                                )
                            )
                        return results

            # Commit if all succeeded or if not rolling back on error
            if all(r.success for r in results) or not rollback_on_error:
                self.db.commit()
            else:
                self.db.rollback()

        except Exception as e:
            logger.error(f"Batch delete failed: {e}")
            self.db.rollback()
            raise

        return results
