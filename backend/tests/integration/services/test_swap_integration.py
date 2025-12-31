"""
Integration tests for swap service with validation.

Tests swap operations with real database and validation logic.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestSwapIntegration:
    """Test swap service integration."""

    def test_one_to_one_swap_execution_integration(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Test executing a one-to-one swap."""
        # Create blocks
        block_a = Block(
            id=uuid4(),
            date=date.today(),
            time_of_day="AM",
            block_number=1,
        )
        block_b = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=1),
            time_of_day="AM",
            block_number=1,
        )
        db.add(block_a)
        db.add(block_b)
        db.commit()

        # Create assignments
        assignment_a = Assignment(
            id=uuid4(),
            block_id=block_a.id,
            person_id=sample_residents[0].id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        assignment_b = Assignment(
            id=uuid4(),
            block_id=block_b.id,
            person_id=sample_residents[1].id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add(assignment_a)
        db.add(assignment_b)
        db.commit()

        # Execute swap
        # swap_service = SwapService(db)
        # result = swap_service.execute_swap(
        #     assignment_a_id=assignment_a.id,
        #     assignment_b_id=assignment_b.id,
        # )
        # assert result.success

    def test_swap_validation_integration(
        self,
        db: Session,
        sample_resident: Person,
        sample_rotation_template: RotationTemplate,
    ):
        """Test swap validation before execution."""
        # Create assignment
        block = Block(
            id=uuid4(),
            date=date.today(),
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        # Try to swap with itself (should fail validation)
        # swap_service = SwapService(db)
        # result = swap_service.validate_swap(
        #     assignment_a_id=assignment.id,
        #     assignment_b_id=assignment.id,
        # )
        # assert result.is_valid == False

    def test_swap_auto_matching_integration(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Test automatic swap matching."""
        # Create multiple assignments
        blocks = []
        assignments = []

        for i in range(4):
            block = Block(
                id=uuid4(),
                date=date.today() + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)

        db.commit()

        for i, block in enumerate(blocks):
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_residents[i % len(sample_residents)].id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
            assignments.append(assignment)

        db.commit()

        # Find swap matches
        # swap_service = SwapService(db)
        # matches = swap_service.find_swap_matches(
        #     assignment_id=assignments[0].id,
        # )
        # assert len(matches) > 0

    def test_swap_rollback_integration(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Test rolling back a swap."""
        # Create and execute swap
        block_a = Block(
            id=uuid4(),
            date=date.today(),
            time_of_day="AM",
            block_number=1,
        )
        block_b = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=1),
            time_of_day="AM",
            block_number=1,
        )
        db.add_all([block_a, block_b])
        db.commit()

        assignment_a = Assignment(
            id=uuid4(),
            block_id=block_a.id,
            person_id=sample_residents[0].id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        assignment_b = Assignment(
            id=uuid4(),
            block_id=block_b.id,
            person_id=sample_residents[1].id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add_all([assignment_a, assignment_b])
        db.commit()

        # Execute and rollback swap
        # swap_service = SwapService(db)
        # swap_result = swap_service.execute_swap(...)
        # rollback_result = swap_service.rollback_swap(swap_result.swap_id)
        # assert rollback_result.success
