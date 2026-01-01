"""Tests for BatchProcessor service."""

import pytest
from datetime import date
from unittest.mock import Mock, patch
from uuid import uuid4

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.schemas.batch import (
    BatchAssignmentCreate,
    BatchAssignmentUpdate,
    BatchAssignmentDelete,
)
from app.services.batch.batch_processor import BatchProcessor


class TestBatchProcessor:
    """Test suite for BatchProcessor."""

    # ========================================================================
    # Batch Create Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_process_create_batch_success(
        self, db, sample_resident, sample_block, sample_rotation_template
    ):
        """Test successful batch creation of assignments."""
        processor = BatchProcessor(db)

        # Create batch data
        batch_data = [
            BatchAssignmentCreate(
                block_id=sample_block.id,
                person_id=sample_resident.id,
                role="primary",
                rotation_template_id=sample_rotation_template.id,
            )
        ]

        results = await processor.process_create_batch(
            assignments=batch_data,
            created_by="test_user",
            rollback_on_error=True,
        )

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].assignment_id is not None
        assert results[0].error is None

    @pytest.mark.asyncio
    async def test_process_create_batch_multiple_assignments(
        self, db, sample_residents, sample_blocks, sample_rotation_template
    ):
        """Test creating multiple assignments in a batch."""
        processor = BatchProcessor(db)

        batch_data = [
            BatchAssignmentCreate(
                block_id=sample_blocks[i].id,
                person_id=sample_residents[i].id,
                role="primary",
                rotation_template_id=sample_rotation_template.id,
            )
            for i in range(3)
        ]

        results = await processor.process_create_batch(
            assignments=batch_data,
            created_by="test_user",
            rollback_on_error=True,
        )

        assert len(results) == 3
        assert all(r.success for r in results)
        assert all(r.assignment_id is not None for r in results)

    @pytest.mark.asyncio
    async def test_process_create_batch_with_error_rollback(
        self, db, sample_resident, sample_block
    ):
        """Test batch creation rolls back on error when rollback_on_error=True."""
        processor = BatchProcessor(db)

        # Create valid and invalid batch data
        batch_data = [
            BatchAssignmentCreate(
                block_id=sample_block.id,
                person_id=sample_resident.id,
                role="primary",
            ),
            BatchAssignmentCreate(
                block_id=uuid4(),  # Invalid block ID
                person_id=sample_resident.id,
                role="primary",
            ),
        ]

        results = await processor.process_create_batch(
            assignments=batch_data,
            created_by="test_user",
            rollback_on_error=True,
        )

        # First should succeed, second should fail
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
        assert "error" in results[1].error.lower() or results[1].error != ""

    @pytest.mark.asyncio
    async def test_process_create_batch_without_rollback(
        self, db, sample_resident, sample_blocks
    ):
        """Test batch creation continues on error when rollback_on_error=False."""
        processor = BatchProcessor(db)

        batch_data = [
            BatchAssignmentCreate(
                block_id=sample_blocks[0].id,
                person_id=sample_resident.id,
                role="primary",
            ),
            BatchAssignmentCreate(
                block_id=uuid4(),  # Invalid
                person_id=sample_resident.id,
                role="primary",
            ),
            BatchAssignmentCreate(
                block_id=sample_blocks[1].id,
                person_id=sample_resident.id,
                role="backup",
            ),
        ]

        results = await processor.process_create_batch(
            assignments=batch_data,
            created_by="test_user",
            rollback_on_error=False,
        )

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True

    # ========================================================================
    # Batch Update Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_process_update_batch_success(self, db, sample_assignment):
        """Test successful batch update of assignments."""
        processor = BatchProcessor(db)

        batch_data = [
            BatchAssignmentUpdate(
                assignment_id=sample_assignment.id,
                updated_at=sample_assignment.updated_at,
                role="backup",
                notes="Updated via batch",
            )
        ]

        results = await processor.process_update_batch(
            assignments=batch_data,
            rollback_on_error=True,
        )

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].assignment_id == sample_assignment.id

        # Verify update
        db.refresh(sample_assignment)
        assert sample_assignment.role == "backup"
        assert "Updated via batch" in sample_assignment.notes

    @pytest.mark.asyncio
    async def test_process_update_batch_not_found(self, db):
        """Test batch update with non-existent assignment."""
        processor = BatchProcessor(db)

        batch_data = [
            BatchAssignmentUpdate(
                assignment_id=uuid4(),
                updated_at=None,
                role="backup",
            )
        ]

        results = await processor.process_update_batch(
            assignments=batch_data,
            rollback_on_error=True,
        )

        assert len(results) == 1
        assert results[0].success is False
        assert "not found" in results[0].error.lower()

    @pytest.mark.asyncio
    async def test_process_update_batch_optimistic_locking(
        self, db, sample_assignment
    ):
        """Test optimistic locking in batch update."""
        processor = BatchProcessor(db)

        old_updated_at = sample_assignment.updated_at

        # Simulate another update
        sample_assignment.notes = "Modified by someone else"
        db.commit()
        db.refresh(sample_assignment)

        # Try to update with old timestamp
        batch_data = [
            BatchAssignmentUpdate(
                assignment_id=sample_assignment.id,
                updated_at=old_updated_at,
                role="backup",
            )
        ]

        results = await processor.process_update_batch(
            assignments=batch_data,
            rollback_on_error=True,
        )

        assert len(results) == 1
        assert results[0].success is False
        assert "modified" in results[0].error.lower()

    # ========================================================================
    # Batch Delete Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_process_delete_batch_hard_delete(self, db, sample_assignment):
        """Test hard delete in batch deletion."""
        processor = BatchProcessor(db)

        assignment_id = sample_assignment.id

        batch_data = [
            BatchAssignmentDelete(
                assignment_id=assignment_id,
                soft_delete=False,
            )
        ]

        results = await processor.process_delete_batch(
            assignments=batch_data,
            rollback_on_error=True,
        )

        assert len(results) == 1
        assert results[0].success is True

        # Verify deletion
        deleted = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        assert deleted is None

    @pytest.mark.asyncio
    async def test_process_delete_batch_soft_delete(self, db, sample_assignment):
        """Test soft delete in batch deletion."""
        processor = BatchProcessor(db)

        assignment_id = sample_assignment.id

        batch_data = [
            BatchAssignmentDelete(
                assignment_id=assignment_id,
                soft_delete=True,
            )
        ]

        results = await processor.process_delete_batch(
            assignments=batch_data,
            rollback_on_error=True,
        )

        assert len(results) == 1
        assert results[0].success is True

        # Verify soft deletion
        db.refresh(sample_assignment)
        assert sample_assignment is not None
        assert "[SOFT DELETED]" in sample_assignment.notes

    @pytest.mark.asyncio
    async def test_process_delete_batch_not_found(self, db):
        """Test batch delete with non-existent assignment."""
        processor = BatchProcessor(db)

        batch_data = [
            BatchAssignmentDelete(
                assignment_id=uuid4(),
                soft_delete=False,
            )
        ]

        results = await processor.process_delete_batch(
            assignments=batch_data,
            rollback_on_error=True,
        )

        assert len(results) == 1
        assert results[0].success is False
        assert "not found" in results[0].error.lower()

    @pytest.mark.asyncio
    async def test_process_delete_batch_multiple(
        self, db, sample_residents, sample_blocks
    ):
        """Test deleting multiple assignments in batch."""
        processor = BatchProcessor(db)

        # Create multiple assignments
        assignments = []
        for i in range(3):
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_blocks[i].id,
                person_id=sample_residents[i].id,
                role="primary",
            )
            db.add(assignment)
            assignments.append(assignment)
        db.commit()

        batch_data = [
            BatchAssignmentDelete(
                assignment_id=a.id,
                soft_delete=False,
            )
            for a in assignments
        ]

        results = await processor.process_delete_batch(
            assignments=batch_data,
            rollback_on_error=True,
        )

        assert len(results) == 3
        assert all(r.success for r in results)

        # Verify all deleted
        remaining = db.query(Assignment).filter(
            Assignment.id.in_([a.id for a in assignments])
        ).count()
        assert remaining == 0
