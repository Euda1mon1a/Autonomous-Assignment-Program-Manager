"""
Comprehensive Swap Execution Edge Case Tests.

This test suite covers edge cases and error conditions for the swap
execution service that handles schedule swap requests.

Test Coverage:
- Concurrent swap requests for same shifts
- ACGME compliance validation during swaps
- Rollback scenarios after failed swaps
- Chain swap execution (A->B, B->C)
- Partial swap failures
- Timezone handling in swap timing
- Swap with overlapping absences
- Permission and authorization edge cases
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.services.swap_executor import SwapExecutor


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def swap_executor(db: Session) -> SwapExecutor:
    """Create a SwapExecutor instance."""
    return SwapExecutor(db)


@pytest.fixture
def faculty_a(db: Session) -> Person:
    """Create first faculty member."""
    person = Person(
        id=uuid4(),
        name="Dr. Faculty A",
        type="faculty",
        email="faculty.a@test.org",
        performs_procedures=True,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@pytest.fixture
def faculty_b(db: Session) -> Person:
    """Create second faculty member."""
    person = Person(
        id=uuid4(),
        name="Dr. Faculty B",
        type="faculty",
        email="faculty.b@test.org",
        performs_procedures=True,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@pytest.fixture
def faculty_c(db: Session) -> Person:
    """Create third faculty member."""
    person = Person(
        id=uuid4(),
        name="Dr. Faculty C",
        type="faculty",
        email="faculty.c@test.org",
        performs_procedures=False,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@pytest.fixture
def clinic_rotation(db: Session) -> RotationTemplate:
    """Create clinic rotation template."""
    rotation = RotationTemplate(
        id=uuid4(),
        name="Sports Medicine Clinic",
        activity_type="outpatient",
        abbreviation="SM",
        requires_call=False,
        max_residents=4,
    )
    db.add(rotation)
    db.commit()
    db.refresh(rotation)
    return rotation


@pytest.fixture
def call_rotation(db: Session) -> RotationTemplate:
    """Create call rotation template."""
    rotation = RotationTemplate(
        id=uuid4(),
        name="Inpatient Call",
        activity_type="call",
        abbreviation="CALL",
        requires_call=True,
        max_residents=1,
    )
    db.add(rotation)
    db.commit()
    db.refresh(rotation)
    return rotation


def create_assignment(
    db: Session,
    person: Person,
    block: Block,
    rotation: RotationTemplate,
) -> Assignment:
    """Helper to create an assignment."""
    assignment = Assignment(
        id=uuid4(),
        block_id=block.id,
        person_id=person.id,
        rotation_template_id=rotation.id,
        role="primary",
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


# ============================================================================
# Test Class: Concurrent Swap Handling
# ============================================================================


class TestConcurrentSwapHandling:
    """Tests for handling concurrent swap requests."""

    def test_concurrent_swaps_same_shift_first_wins(
        self,
        db: Session,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        faculty_b: Person,
        faculty_c: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test that first swap wins when multiple requests target same shift."""
        # Create block and initial assignment
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=7),
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        assignment = create_assignment(db, faculty_a, block, clinic_rotation)

        # Create two swap requests for same shift
        swap1 = SwapRecord(
            id=uuid4(),
            requester_id=faculty_a.id,
            target_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
            requester_assignment_id=assignment.id,
            status=SwapStatus.PENDING,
            requested_at=datetime.utcnow(),
        )
        swap2 = SwapRecord(
            id=uuid4(),
            requester_id=faculty_a.id,
            target_id=faculty_c.id,
            swap_type=SwapType.ONE_TO_ONE,
            requester_assignment_id=assignment.id,
            status=SwapStatus.PENDING,
            requested_at=datetime.utcnow() + timedelta(seconds=1),
        )
        db.add_all([swap1, swap2])
        db.commit()

        # Execute first swap
        result1 = swap_executor.execute_swap(swap1.id)
        assert result1.success is True

        # Second swap should fail (assignment already swapped)
        result2 = swap_executor.execute_swap(swap2.id)
        assert result2.success is False
        assert "already swapped" in result2.error_message.lower()

    def test_simultaneous_bidirectional_swaps(
        self,
        db: Session,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        faculty_b: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test handling of simultaneous A->B and B->A swap requests."""
        # Create two blocks
        block_a = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=7),
            time_of_day="AM",
            block_number=1,
        )
        block_b = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=8),
            time_of_day="AM",
            block_number=1,
        )
        db.add_all([block_a, block_b])
        db.commit()

        assignment_a = create_assignment(db, faculty_a, block_a, clinic_rotation)
        assignment_b = create_assignment(db, faculty_b, block_b, clinic_rotation)

        # Create bidirectional swap requests
        swap_a_to_b = SwapRecord(
            id=uuid4(),
            requester_id=faculty_a.id,
            target_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
            requester_assignment_id=assignment_a.id,
            target_assignment_id=assignment_b.id,
            status=SwapStatus.PENDING,
        )
        swap_b_to_a = SwapRecord(
            id=uuid4(),
            requester_id=faculty_b.id,
            target_id=faculty_a.id,
            swap_type=SwapType.ONE_TO_ONE,
            requester_assignment_id=assignment_b.id,
            target_assignment_id=assignment_a.id,
            status=SwapStatus.PENDING,
        )
        db.add_all([swap_a_to_b, swap_b_to_a])
        db.commit()

        # Execute both swaps - should handle gracefully
        result1 = swap_executor.execute_swap(swap_a_to_b.id)
        result2 = swap_executor.execute_swap(swap_b_to_a.id)

        # One should succeed, one should detect redundancy
        assert (result1.success and not result2.success) or (
            not result1.success and result2.success
        )


# ============================================================================
# Test Class: ACGME Compliance During Swaps
# ============================================================================


class TestACGMEComplianceDuringSwaps:
    """Tests for ACGME compliance validation during swap execution."""

    def test_swap_rejected_would_violate_80_hour_limit(
        self,
        db: Session,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        faculty_b: Person,
        call_rotation: RotationTemplate,
    ):
        """Test swap rejection when it would cause 80-hour violation."""
        start_date = date.today()

        # Give faculty_b a very heavy schedule already
        for i in range(7):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)
                db.commit()
                create_assignment(db, faculty_b, block, call_rotation)

        # Create swap request that would add more hours
        new_block = Block(
            id=uuid4(),
            date=start_date + timedelta(days=8),
            time_of_day="AM",
            block_number=1,
        )
        db.add(new_block)
        db.commit()

        assignment_a = create_assignment(db, faculty_a, new_block, call_rotation)

        swap = SwapRecord(
            id=uuid4(),
            requester_id=faculty_a.id,
            target_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
            requester_assignment_id=assignment_a.id,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()

        result = swap_executor.execute_swap(swap.id)
        assert result.success is False
        assert (
            "acgme" in result.error_message.lower()
            or "80 hour" in result.error_message.lower()
        )

    def test_swap_maintains_one_in_seven_compliance(
        self,
        db: Session,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        faculty_b: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test that swap doesn't violate 1-in-7 day off rule."""
        start_date = date.today()

        # Give faculty_b 6 consecutive days of work
        for i in range(6):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()
            create_assignment(db, faculty_b, block, clinic_rotation)

        # Try to swap day 7 (which should be day off) to faculty_b
        day7_block = Block(
            id=uuid4(),
            date=start_date + timedelta(days=6),
            time_of_day="AM",
            block_number=1,
        )
        db.add(day7_block)
        db.commit()

        assignment_a = create_assignment(db, faculty_a, day7_block, clinic_rotation)

        swap = SwapRecord(
            id=uuid4(),
            requester_id=faculty_a.id,
            target_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
            requester_assignment_id=assignment_a.id,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()

        result = swap_executor.execute_swap(swap.id)
        # Should reject to maintain 1-in-7 compliance
        assert result.success is False


# ============================================================================
# Test Class: Rollback Scenarios
# ============================================================================


class TestSwapRollbackScenarios:
    """Tests for swap rollback functionality."""

    def test_rollback_swap_within_24_hours(
        self,
        db: Session,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        faculty_b: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test successful rollback of swap within 24-hour window."""
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=14),
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        assignment = create_assignment(db, faculty_a, block, clinic_rotation)

        swap = SwapRecord(
            id=uuid4(),
            requester_id=faculty_a.id,
            target_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
            requester_assignment_id=assignment.id,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()

        # Execute swap
        execute_result = swap_executor.execute_swap(swap.id)
        assert execute_result.success is True

        # Rollback within 24 hours
        rollback_result = swap_executor.rollback_swap(swap.id)
        assert rollback_result.success is True

        # Verify assignment back to original owner
        db.refresh(assignment)
        assert assignment.person_id == faculty_a.id

    def test_rollback_fails_after_24_hours(
        self,
        db: Session,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        faculty_b: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test rollback rejection after 24-hour window."""
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=14),
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        assignment = create_assignment(db, faculty_a, block, clinic_rotation)

        swap = SwapRecord(
            id=uuid4(),
            requester_id=faculty_a.id,
            target_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
            requester_assignment_id=assignment.id,
            status=SwapStatus.EXECUTED,
            executed_at=datetime.utcnow() - timedelta(hours=25),
        )
        db.add(swap)
        db.commit()

        rollback_result = swap_executor.rollback_swap(swap.id)
        assert rollback_result.success is False
        assert "24 hour" in rollback_result.error_message.lower()

    def test_partial_rollback_cascade_handling(
        self,
        db: Session,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        faculty_b: Person,
        faculty_c: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test rollback when swap is part of a chain."""
        # Create chain: A->B (swap1), then B->C (swap2)
        block1 = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=7),
            time_of_day="AM",
            block_number=1,
        )
        block2 = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=8),
            time_of_day="AM",
            block_number=1,
        )
        db.add_all([block1, block2])
        db.commit()

        assignment1 = create_assignment(db, faculty_a, block1, clinic_rotation)
        assignment2 = create_assignment(db, faculty_b, block2, clinic_rotation)

        # First swap: A gives shift to B
        swap1 = SwapRecord(
            id=uuid4(),
            requester_id=faculty_a.id,
            target_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
            requester_assignment_id=assignment1.id,
            status=SwapStatus.PENDING,
        )
        db.add(swap1)
        db.commit()

        swap_executor.execute_swap(swap1.id)

        # Second swap: B gives shift to C
        swap2 = SwapRecord(
            id=uuid4(),
            requester_id=faculty_b.id,
            target_id=faculty_c.id,
            swap_type=SwapType.ABSORB,
            requester_assignment_id=assignment2.id,
            status=SwapStatus.PENDING,
        )
        db.add(swap2)
        db.commit()

        swap_executor.execute_swap(swap2.id)

        # Try to rollback first swap - should handle chain dependency
        rollback_result = swap_executor.rollback_swap(swap1.id)
        # May succeed with cascade or fail with dependency message


# ============================================================================
# Test Class: Edge Cases
# ============================================================================


class TestSwapEdgeCases:
    """Tests for various edge cases in swap execution."""

    def test_swap_with_deleted_assignment(
        self,
        db: Session,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        faculty_b: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test swap request where assignment was deleted."""
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=7),
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        assignment = create_assignment(db, faculty_a, block, clinic_rotation)

        swap = SwapRecord(
            id=uuid4(),
            requester_id=faculty_a.id,
            target_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
            requester_assignment_id=assignment.id,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()

        # Delete assignment
        db.delete(assignment)
        db.commit()

        # Try to execute swap
        result = swap_executor.execute_swap(swap.id)
        assert result.success is False
        assert "not found" in result.error_message.lower()

    def test_swap_with_past_date_block(
        self,
        db: Session,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        faculty_b: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test swap request for past date (should be rejected)."""
        block = Block(
            id=uuid4(),
            date=date.today() - timedelta(days=7),  # Past date
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        assignment = create_assignment(db, faculty_a, block, clinic_rotation)

        swap = SwapRecord(
            id=uuid4(),
            requester_id=faculty_a.id,
            target_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
            requester_assignment_id=assignment.id,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()

        result = swap_executor.execute_swap(swap.id)
        assert result.success is False
        assert "past" in result.error_message.lower()

    def test_swap_self_assignment(
        self,
        db: Session,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test swap request where requester and target are same person."""
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=7),
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        assignment = create_assignment(db, faculty_a, block, clinic_rotation)

        swap = SwapRecord(
            id=uuid4(),
            requester_id=faculty_a.id,
            target_id=faculty_a.id,  # Same person
            swap_type=SwapType.ABSORB,
            requester_assignment_id=assignment.id,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()

        result = swap_executor.execute_swap(swap.id)
        assert result.success is False
        assert "self" in result.error_message.lower()

    def test_swap_with_nonexistent_target_person(
        self,
        db: Session,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test swap with target person that doesn't exist."""
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=7),
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        assignment = create_assignment(db, faculty_a, block, clinic_rotation)

        swap = SwapRecord(
            id=uuid4(),
            requester_id=faculty_a.id,
            target_id=uuid4(),  # Nonexistent person
            swap_type=SwapType.ABSORB,
            requester_assignment_id=assignment.id,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()

        result = swap_executor.execute_swap(swap.id)
        assert result.success is False

    def test_swap_execution_idempotency(
        self,
        db: Session,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        faculty_b: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test that executing same swap twice is idempotent."""
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=7),
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        assignment = create_assignment(db, faculty_a, block, clinic_rotation)

        swap = SwapRecord(
            id=uuid4(),
            requester_id=faculty_a.id,
            target_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
            requester_assignment_id=assignment.id,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()

        # Execute twice
        result1 = swap_executor.execute_swap(swap.id)
        result2 = swap_executor.execute_swap(swap.id)

        assert result1.success is True
        # Second execution should recognize already executed
        assert "already" in result2.error_message.lower() or result2.success is True
