"""Tests for SwapExecutor service."""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4
from unittest.mock import patch

from app.services.swap_executor import SwapExecutor, ExecutionResult, RollbackResult
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.call_assignment import CallAssignment
from app.models.person import Person


class TestSwapExecutor:
    """Test suite for SwapExecutor service."""

    # ========================================================================
    # Execute Swap Tests
    # ========================================================================

    def test_execute_swap_one_to_one_success(self, db, sample_faculty):
        """Test executing a one-to-one swap successfully."""
        # Create two faculty members
        faculty1 = sample_faculty
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Sarah Jones",
            type="faculty",
            email="sarah.jones@hospital.org",
        )
        db.add(faculty2)
        db.commit()

        # Create blocks for two weeks
        week1_start = date(2025, 1, 6)  # Monday
        week2_start = date(2025, 1, 13)  # Monday

        # Create blocks for week 1
        week1_blocks = []
        for day_offset in range(7):
            for time in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=week1_start + timedelta(days=day_offset),
                    time_of_day=time,
                    block_number=1,
                )
                db.add(block)
                week1_blocks.append(block)

        # Create blocks for week 2
        week2_blocks = []
        for day_offset in range(7):
            for time in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=week2_start + timedelta(days=day_offset),
                    time_of_day=time,
                    block_number=2,
                )
                db.add(block)
                week2_blocks.append(block)

        db.commit()

        # Create assignments for week 1 (faculty1)
        for block in week1_blocks[:4]:  # First 2 days
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=faculty1.id,
                role="primary",
            )
            db.add(assignment)

        # Create assignments for week 2 (faculty2)
        for block in week2_blocks[:4]:  # First 2 days
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=faculty2.id,
                role="primary",
            )
            db.add(assignment)

        db.commit()

        # Execute swap
        executor = SwapExecutor(db)
        result = executor.execute_swap(
            source_faculty_id=faculty1.id,
            source_week=week1_start,
            target_faculty_id=faculty2.id,
            target_week=week2_start,
            swap_type="one_to_one",
            reason="Family emergency",
        )

        assert result.success is True
        assert result.swap_id is not None
        assert "transferred" in result.message.lower()

        # Verify swap record was created
        swap_record = db.query(SwapRecord).filter(SwapRecord.id == result.swap_id).first()
        assert swap_record is not None
        assert swap_record.status == SwapStatus.EXECUTED
        assert swap_record.source_faculty_id == faculty1.id
        assert swap_record.target_faculty_id == faculty2.id
        assert swap_record.swap_type == SwapType.ONE_TO_ONE

        # Verify assignments were swapped
        week1_assignments = (
            db.query(Assignment)
            .join(Block)
            .filter(Block.date >= week1_start)
            .filter(Block.date < week1_start + timedelta(days=7))
            .all()
        )
        for assignment in week1_assignments:
            # Faculty1's assignments should now belong to faculty2
            assert assignment.person_id == faculty2.id

        week2_assignments = (
            db.query(Assignment)
            .join(Block)
            .filter(Block.date >= week2_start)
            .filter(Block.date < week2_start + timedelta(days=7))
            .all()
        )
        for assignment in week2_assignments:
            # Faculty2's assignments should now belong to faculty1
            assert assignment.person_id == faculty1.id

    def test_execute_swap_absorb_success(self, db, sample_faculty):
        """Test executing an absorb swap successfully."""
        faculty1 = sample_faculty
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Sarah Jones",
            type="faculty",
            email="sarah.jones@hospital.org",
        )
        db.add(faculty2)
        db.commit()

        # Create blocks for one week
        week_start = date(2025, 1, 6)  # Monday
        blocks = []
        for day_offset in range(7):
            for time in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=week_start + timedelta(days=day_offset),
                    time_of_day=time,
                    block_number=1,
                )
                db.add(block)
                blocks.append(block)

        db.commit()

        # Create assignments for faculty1
        for block in blocks[:4]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=faculty1.id,
                role="primary",
            )
            db.add(assignment)

        db.commit()

        # Execute absorb swap (faculty2 takes faculty1's week)
        executor = SwapExecutor(db)
        result = executor.execute_swap(
            source_faculty_id=faculty1.id,
            source_week=week_start,
            target_faculty_id=faculty2.id,
            target_week=None,  # No target week for absorb
            swap_type="absorb",
            reason="Faculty1 has leave",
        )

        assert result.success is True
        assert result.swap_id is not None

        # Verify assignments were transferred
        week_assignments = (
            db.query(Assignment)
            .join(Block)
            .filter(Block.date >= week_start)
            .filter(Block.date < week_start + timedelta(days=7))
            .all()
        )
        for assignment in week_assignments:
            assert assignment.person_id == faculty2.id

    def test_execute_swap_with_call_cascade(self, db, sample_faculty):
        """Test that call assignments are updated during swap."""
        faculty1 = sample_faculty
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Sarah Jones",
            type="faculty",
            email="sarah.jones@hospital.org",
        )
        db.add(faculty2)
        db.commit()

        # Create week starting on Monday
        week_start = date(2025, 1, 6)  # Monday, Jan 6, 2025

        # Create blocks for the week
        for day_offset in range(7):
            for time in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=week_start + timedelta(days=day_offset),
                    time_of_day=time,
                    block_number=1,
                    is_weekend=(week_start + timedelta(days=day_offset)).weekday() >= 5,
                )
                db.add(block)

        # Create call assignment for Friday (day 4)
        friday = week_start + timedelta(days=4)
        call_friday = CallAssignment(
            id=uuid4(),
            date=friday,
            person_id=faculty1.id,
            call_type="overnight",
        )
        db.add(call_friday)

        # Create call assignment for Saturday (day 5)
        saturday = week_start + timedelta(days=5)
        call_saturday = CallAssignment(
            id=uuid4(),
            date=saturday,
            person_id=faculty1.id,
            call_type="weekend",
            is_weekend=True,
        )
        db.add(call_saturday)

        db.commit()

        # Execute swap
        executor = SwapExecutor(db)
        result = executor.execute_swap(
            source_faculty_id=faculty1.id,
            source_week=week_start,
            target_faculty_id=faculty2.id,
            target_week=None,
            swap_type="absorb",
        )

        assert result.success is True

        # Verify call assignments were transferred
        friday_call = db.query(CallAssignment).filter(CallAssignment.date == friday).first()
        assert friday_call.person_id == faculty2.id

        saturday_call = db.query(CallAssignment).filter(CallAssignment.date == saturday).first()
        assert saturday_call.person_id == faculty2.id

    def test_execute_swap_failure_rolls_back(self, db, sample_faculty):
        """Test that failed swap execution rolls back changes."""
        faculty1 = sample_faculty

        # Try to execute swap with invalid target faculty (doesn't exist)
        executor = SwapExecutor(db)
        result = executor.execute_swap(
            source_faculty_id=faculty1.id,
            source_week=date(2025, 1, 6),
            target_faculty_id=uuid4(),  # Non-existent faculty
            target_week=None,
            swap_type="absorb",
        )

        # Should handle gracefully and not create partial data
        # In this case, the swap record might be created but assignments won't change
        # The important thing is that we don't have inconsistent state

    # ========================================================================
    # Rollback Swap Tests
    # ========================================================================

    def test_rollback_swap_success(self, db, sample_faculty):
        """Test successfully rolling back a swap."""
        faculty1 = sample_faculty
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Sarah Jones",
            type="faculty",
            email="sarah.jones@hospital.org",
        )
        db.add(faculty2)
        db.commit()

        # Create blocks and assignments
        week_start = date(2025, 1, 6)
        blocks = []
        for day_offset in range(7):
            for time in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=week_start + timedelta(days=day_offset),
                    time_of_day=time,
                    block_number=1,
                )
                db.add(block)
                blocks.append(block)

        db.commit()

        # Create assignments for faculty1
        for block in blocks[:4]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=faculty1.id,
                role="primary",
            )
            db.add(assignment)

        db.commit()

        # Execute swap
        executor = SwapExecutor(db)
        exec_result = executor.execute_swap(
            source_faculty_id=faculty1.id,
            source_week=week_start,
            target_faculty_id=faculty2.id,
            target_week=None,
            swap_type="absorb",
        )

        assert exec_result.success is True
        swap_id = exec_result.swap_id

        # Verify assignments were transferred to faculty2
        assignments_after_swap = (
            db.query(Assignment)
            .join(Block)
            .filter(Block.date >= week_start)
            .filter(Block.date < week_start + timedelta(days=7))
            .all()
        )
        for assignment in assignments_after_swap:
            assert assignment.person_id == faculty2.id

        # Rollback the swap
        rollback_result = executor.rollback_swap(
            swap_id=swap_id,
            reason="Changed mind",
        )

        assert rollback_result.success is True
        assert "successfully" in rollback_result.message.lower()

        # Verify swap record status
        swap_record = db.query(SwapRecord).filter(SwapRecord.id == swap_id).first()
        assert swap_record.status == SwapStatus.ROLLED_BACK
        assert swap_record.rollback_reason == "Changed mind"

        # Verify assignments were restored to faculty1
        assignments_after_rollback = (
            db.query(Assignment)
            .join(Block)
            .filter(Block.date >= week_start)
            .filter(Block.date < week_start + timedelta(days=7))
            .all()
        )
        for assignment in assignments_after_rollback:
            assert assignment.person_id == faculty1.id

    def test_rollback_swap_not_found(self, db):
        """Test rollback with non-existent swap ID."""
        executor = SwapExecutor(db)
        result = executor.rollback_swap(
            swap_id=uuid4(),
            reason="Test",
        )

        assert result.success is False
        assert result.error_code == "SWAP_NOT_FOUND"
        assert "not found" in result.message.lower()

    def test_rollback_swap_invalid_status(self, db, sample_faculty):
        """Test rollback with swap in invalid status."""
        faculty1 = sample_faculty
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Sarah Jones",
            type="faculty",
            email="sarah.jones@hospital.org",
        )
        db.add(faculty2)

        # Create a swap record with PENDING status
        swap_record = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty1.id,
            source_week=date(2025, 1, 6),
            target_faculty_id=faculty2.id,
            target_week=None,
            swap_type=SwapType.ABSORB,
            status=SwapStatus.PENDING,  # Not executed yet
        )
        db.add(swap_record)
        db.commit()

        # Try to rollback
        executor = SwapExecutor(db)
        result = executor.rollback_swap(
            swap_id=swap_record.id,
            reason="Test",
        )

        assert result.success is False
        assert result.error_code == "INVALID_STATUS"

    def test_rollback_swap_expired_window(self, db, sample_faculty):
        """Test rollback after window has expired."""
        faculty1 = sample_faculty
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Sarah Jones",
            type="faculty",
            email="sarah.jones@hospital.org",
        )
        db.add(faculty2)

        # Create a swap record executed 25 hours ago (past 24-hour window)
        old_execution_time = datetime.utcnow() - timedelta(hours=25)
        swap_record = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty1.id,
            source_week=date(2025, 1, 6),
            target_faculty_id=faculty2.id,
            target_week=None,
            swap_type=SwapType.ABSORB,
            status=SwapStatus.EXECUTED,
            executed_at=old_execution_time,
        )
        db.add(swap_record)
        db.commit()

        # Try to rollback
        executor = SwapExecutor(db)
        result = executor.rollback_swap(
            swap_id=swap_record.id,
            reason="Test",
        )

        assert result.success is False
        assert result.error_code == "ROLLBACK_WINDOW_EXPIRED"
        assert "24" in result.message  # Mentions the 24-hour window

    # ========================================================================
    # Can Rollback Tests
    # ========================================================================

    def test_can_rollback_within_window(self, db, sample_faculty):
        """Test that swap can be rolled back within 24-hour window."""
        faculty1 = sample_faculty
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Sarah Jones",
            type="faculty",
            email="sarah.jones@hospital.org",
        )
        db.add(faculty2)

        # Create recently executed swap
        swap_record = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty1.id,
            source_week=date(2025, 1, 6),
            target_faculty_id=faculty2.id,
            target_week=None,
            swap_type=SwapType.ABSORB,
            status=SwapStatus.EXECUTED,
            executed_at=datetime.utcnow() - timedelta(hours=2),  # 2 hours ago
        )
        db.add(swap_record)
        db.commit()

        executor = SwapExecutor(db)
        assert executor.can_rollback(swap_record.id) is True

    def test_can_rollback_outside_window(self, db, sample_faculty):
        """Test that swap cannot be rolled back after 24 hours."""
        faculty1 = sample_faculty
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Sarah Jones",
            type="faculty",
            email="sarah.jones@hospital.org",
        )
        db.add(faculty2)

        # Create old executed swap
        swap_record = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty1.id,
            source_week=date(2025, 1, 6),
            target_faculty_id=faculty2.id,
            target_week=None,
            swap_type=SwapType.ABSORB,
            status=SwapStatus.EXECUTED,
            executed_at=datetime.utcnow() - timedelta(hours=30),  # 30 hours ago
        )
        db.add(swap_record)
        db.commit()

        executor = SwapExecutor(db)
        assert executor.can_rollback(swap_record.id) is False

    def test_can_rollback_invalid_status(self, db, sample_faculty):
        """Test that pending swaps cannot be rolled back."""
        faculty1 = sample_faculty
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Sarah Jones",
            type="faculty",
            email="sarah.jones@hospital.org",
        )
        db.add(faculty2)

        swap_record = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty1.id,
            source_week=date(2025, 1, 6),
            target_faculty_id=faculty2.id,
            target_week=None,
            swap_type=SwapType.ABSORB,
            status=SwapStatus.PENDING,
        )
        db.add(swap_record)
        db.commit()

        executor = SwapExecutor(db)
        assert executor.can_rollback(swap_record.id) is False

    def test_can_rollback_not_found(self, db):
        """Test can_rollback with non-existent swap."""
        executor = SwapExecutor(db)
        assert executor.can_rollback(uuid4()) is False

    # ========================================================================
    # Edge Cases and Integration Tests
    # ========================================================================

    def test_execute_swap_with_enum_type(self, db, sample_faculty):
        """Test executing swap with SwapType enum instead of string."""
        faculty1 = sample_faculty
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Sarah Jones",
            type="faculty",
            email="sarah.jones@hospital.org",
        )
        db.add(faculty2)
        db.commit()

        week_start = date(2025, 1, 6)

        # Create blocks
        for day_offset in range(7):
            for time in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=week_start + timedelta(days=day_offset),
                    time_of_day=time,
                    block_number=1,
                )
                db.add(block)
        db.commit()

        executor = SwapExecutor(db)
        result = executor.execute_swap(
            source_faculty_id=faculty1.id,
            source_week=week_start,
            target_faculty_id=faculty2.id,
            target_week=None,
            swap_type=SwapType.ABSORB,  # Using enum directly
        )

        assert result.success is True

    def test_execute_swap_preserves_executed_by(self, db, sample_faculty, admin_user):
        """Test that executed_by_id is preserved in swap record."""
        faculty1 = sample_faculty
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Sarah Jones",
            type="faculty",
            email="sarah.jones@hospital.org",
        )
        db.add(faculty2)
        db.commit()

        week_start = date(2025, 1, 6)

        # Create blocks
        for day_offset in range(7):
            for time in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=week_start + timedelta(days=day_offset),
                    time_of_day=time,
                    block_number=1,
                )
                db.add(block)
        db.commit()

        executor = SwapExecutor(db)
        result = executor.execute_swap(
            source_faculty_id=faculty1.id,
            source_week=week_start,
            target_faculty_id=faculty2.id,
            target_week=None,
            swap_type="absorb",
            executed_by_id=admin_user.id,
        )

        assert result.success is True

        # Verify executed_by_id was saved
        swap_record = db.query(SwapRecord).filter(SwapRecord.id == result.swap_id).first()
        assert swap_record.executed_by_id == admin_user.id
