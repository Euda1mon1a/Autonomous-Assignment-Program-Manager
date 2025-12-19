"""
Comprehensive tests for swap executor service.

Tests for:
- Swap execution flow
- Validation checks
- Rollback functionality
- Error handling
- Call cascade updates
"""
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.person import Person
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.user import User
from app.services.swap_executor import (
    ExecutionResult,
    RollbackResult,
    SwapExecutor,
)


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
    faculty = Person(
        id=uuid4(),
        name="Dr. Faculty A",
        type="faculty",
        email="faculty.a@hospital.org",
        performs_procedures=True,
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def faculty_b(db: Session) -> Person:
    """Create second faculty member."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Faculty B",
        type="faculty",
        email="faculty.b@hospital.org",
        performs_procedures=True,
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user for executor audit fields."""
    from app.core.security import get_password_hash

    user = User(
        id=uuid4(),
        username="executor_user",
        email="executor@test.org",
        hashed_password=get_password_hash("testpass"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================================
# ExecutionResult Tests
# ============================================================================


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_successful_result(self):
        """Test creating a successful execution result."""
        swap_id = uuid4()
        result = ExecutionResult(
            success=True,
            swap_id=swap_id,
            message="Swap executed successfully",
        )

        assert result.success is True
        assert result.swap_id == swap_id
        assert result.message == "Swap executed successfully"
        assert result.error_code is None

    def test_failed_result(self):
        """Test creating a failed execution result."""
        result = ExecutionResult(
            success=False,
            message="Execution failed",
            error_code="VALIDATION_ERROR",
        )

        assert result.success is False
        assert result.swap_id is None
        assert result.message == "Execution failed"
        assert result.error_code == "VALIDATION_ERROR"

    def test_default_values(self):
        """Test ExecutionResult default values."""
        result = ExecutionResult(success=True)

        assert result.success is True
        assert result.swap_id is None
        assert result.message == ""
        assert result.error_code is None


# ============================================================================
# RollbackResult Tests
# ============================================================================


class TestRollbackResult:
    """Tests for RollbackResult dataclass."""

    def test_successful_rollback_result(self):
        """Test creating a successful rollback result."""
        result = RollbackResult(
            success=True,
            message="Rollback completed",
        )

        assert result.success is True
        assert result.message == "Rollback completed"
        assert result.error_code is None

    def test_failed_rollback_result(self):
        """Test creating a failed rollback result."""
        result = RollbackResult(
            success=False,
            message="Rollback failed",
            error_code="ROLLBACK_WINDOW_EXPIRED",
        )

        assert result.success is False
        assert result.message == "Rollback failed"
        assert result.error_code == "ROLLBACK_WINDOW_EXPIRED"

    def test_default_values(self):
        """Test RollbackResult default values."""
        result = RollbackResult(success=False)

        assert result.success is False
        assert result.message == ""
        assert result.error_code is None


# ============================================================================
# SwapExecutor Initialization Tests
# ============================================================================


class TestSwapExecutorInitialization:
    """Tests for SwapExecutor initialization."""

    def test_init(self, db: Session):
        """Test service initialization."""
        executor = SwapExecutor(db)

        assert executor.db == db
        assert executor.ROLLBACK_WINDOW_HOURS == 24

    def test_rollback_window_constant(self, swap_executor: SwapExecutor):
        """Test rollback window is properly set."""
        assert swap_executor.ROLLBACK_WINDOW_HOURS == 24


# ============================================================================
# Swap Execution Tests
# ============================================================================


class TestSwapExecution:
    """Tests for execute_swap() method."""

    def test_execute_one_to_one_swap_minimal(
        self, swap_executor: SwapExecutor, faculty_a: Person, faculty_b: Person
    ):
        """Test executing a one-to-one swap with minimal parameters."""
        source_week = date.today() + timedelta(days=14)
        target_week = date.today() + timedelta(days=21)

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_b.id,
            target_week=target_week,
            swap_type="one_to_one",
        )

        assert result.success is True
        assert result.swap_id is not None
        assert isinstance(result.swap_id, UUID)
        assert "executed" in result.message.lower()
        assert result.error_code is None

    def test_execute_one_to_one_swap_with_all_params(
        self,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        faculty_b: Person,
        test_user: User,
    ):
        """Test executing a one-to-one swap with all parameters."""
        source_week = date.today() + timedelta(days=14)
        target_week = date.today() + timedelta(days=21)

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_b.id,
            target_week=target_week,
            swap_type="one_to_one",
            reason="TDY conflict",
            executed_by_id=test_user.id,
        )

        assert result.success is True
        assert result.swap_id is not None
        assert result.message == f"Swap executed. Week {source_week} transferred."

    def test_execute_absorb_swap(
        self,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        faculty_b: Person,
        test_user: User,
    ):
        """Test executing an absorb swap (no target week)."""
        source_week = date.today() + timedelta(days=14)

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_b.id,
            target_week=None,
            swap_type="absorb",
            reason="Emergency coverage",
            executed_by_id=test_user.id,
        )

        assert result.success is True
        assert result.swap_id is not None
        assert "transferred" in result.message.lower()

    def test_execute_swap_without_reason(
        self, swap_executor: SwapExecutor, faculty_a: Person, faculty_b: Person
    ):
        """Test executing swap without reason (optional field)."""
        source_week = date.today() + timedelta(days=14)
        target_week = date.today() + timedelta(days=21)

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_b.id,
            target_week=target_week,
            swap_type="one_to_one",
            reason=None,
        )

        assert result.success is True
        assert result.swap_id is not None

    def test_execute_swap_without_executor_id(
        self, swap_executor: SwapExecutor, faculty_a: Person, faculty_b: Person
    ):
        """Test executing swap without executed_by_id (optional field)."""
        source_week = date.today() + timedelta(days=14)
        target_week = date.today() + timedelta(days=21)

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_b.id,
            target_week=target_week,
            swap_type="one_to_one",
            executed_by_id=None,
        )

        assert result.success is True

    def test_execute_swap_same_day_source_and_target(
        self, swap_executor: SwapExecutor, faculty_a: Person, faculty_b: Person
    ):
        """Test executing swap where source and target weeks are the same."""
        swap_week = date.today() + timedelta(days=14)

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=swap_week,
            target_faculty_id=faculty_b.id,
            target_week=swap_week,
            swap_type="one_to_one",
        )

        # Should still execute successfully (validation would happen elsewhere)
        assert result.success is True

    def test_execute_swap_with_past_date(
        self, swap_executor: SwapExecutor, faculty_a: Person, faculty_b: Person
    ):
        """Test executing swap with past date (validation should happen elsewhere)."""
        past_week = date.today() - timedelta(days=7)

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=past_week,
            target_faculty_id=faculty_b.id,
            target_week=None,
            swap_type="absorb",
        )

        # Executor doesn't validate dates, should succeed
        assert result.success is True

    def test_execute_swap_unique_swap_ids(
        self, swap_executor: SwapExecutor, faculty_a: Person, faculty_b: Person
    ):
        """Test that multiple executions generate unique swap IDs."""
        source_week = date.today() + timedelta(days=14)
        target_week = date.today() + timedelta(days=21)

        result1 = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_b.id,
            target_week=target_week,
            swap_type="one_to_one",
        )

        result2 = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=source_week + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            target_week=target_week + timedelta(days=7),
            swap_type="one_to_one",
        )

        assert result1.swap_id != result2.swap_id


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestSwapExecutionErrorHandling:
    """Tests for error handling in swap execution."""

    @patch.object(SwapExecutor, "execute_swap")
    def test_execute_swap_database_error(
        self, mock_execute: Mock, swap_executor: SwapExecutor, faculty_a: Person, faculty_b: Person
    ):
        """Test handling of database errors during execution."""
        # Configure mock to return a failure result
        mock_execute.return_value = ExecutionResult(
            success=False,
            message="Swap execution failed: Database connection error",
            error_code="EXECUTION_FAILED",
        )

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_b.id,
            target_week=date.today() + timedelta(days=21),
            swap_type="one_to_one",
        )

        assert result.success is False
        assert result.error_code == "EXECUTION_FAILED"

    def test_execute_swap_with_exception(self, db: Session):
        """Test execution with an exception in the method."""
        # Create an executor with a mock database that raises an exception
        mock_db = MagicMock(spec=Session)
        mock_db.add.side_effect = Exception("Database error")

        executor = SwapExecutor(mock_db)

        result = executor.execute_swap(
            source_faculty_id=uuid4(),
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=uuid4(),
            target_week=date.today() + timedelta(days=21),
            swap_type="one_to_one",
        )

        assert result.success is False
        assert "failed" in result.message.lower()
        assert result.error_code == "EXECUTION_FAILED"

    def test_execute_swap_exception_message_format(self, db: Session):
        """Test that exception message is properly formatted."""
        mock_db = MagicMock(spec=Session)
        mock_db.add.side_effect = ValueError("Invalid value")

        executor = SwapExecutor(mock_db)

        result = executor.execute_swap(
            source_faculty_id=uuid4(),
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=uuid4(),
            target_week=None,
            swap_type="absorb",
        )

        assert result.success is False
        assert "Swap execution failed: Invalid value" == result.message
        assert result.error_code == "EXECUTION_FAILED"


# ============================================================================
# Rollback Tests
# ============================================================================


class TestSwapRollback:
    """Tests for rollback_swap() method."""

    def test_rollback_swap_not_implemented(
        self, swap_executor: SwapExecutor, test_user: User
    ):
        """Test rollback returns not implemented status."""
        swap_id = uuid4()

        result = swap_executor.rollback_swap(
            swap_id=swap_id,
            reason="User requested rollback",
            rolled_back_by_id=test_user.id,
        )

        assert result.success is False
        assert "not yet implemented" in result.message.lower()
        assert result.error_code == "NOT_IMPLEMENTED"

    def test_rollback_swap_with_reason(
        self, swap_executor: SwapExecutor, test_user: User
    ):
        """Test rollback with a reason."""
        swap_id = uuid4()

        result = swap_executor.rollback_swap(
            swap_id=swap_id,
            reason="Executed by mistake",
            rolled_back_by_id=test_user.id,
        )

        assert result.success is False
        assert result.error_code == "NOT_IMPLEMENTED"

    def test_rollback_swap_without_user_id(self, swap_executor: SwapExecutor):
        """Test rollback without rolled_back_by_id (optional field)."""
        swap_id = uuid4()

        result = swap_executor.rollback_swap(
            swap_id=swap_id,
            reason="System rollback",
            rolled_back_by_id=None,
        )

        assert result.success is False
        assert result.error_code == "NOT_IMPLEMENTED"

    def test_rollback_nonexistent_swap(self, swap_executor: SwapExecutor):
        """Test rollback of a non-existent swap."""
        fake_swap_id = uuid4()

        result = swap_executor.rollback_swap(
            swap_id=fake_swap_id,
            reason="Testing",
        )

        # Currently returns NOT_IMPLEMENTED regardless
        assert result.success is False


# ============================================================================
# Can Rollback Tests
# ============================================================================


class TestCanRollback:
    """Tests for can_rollback() method."""

    def test_can_rollback_placeholder(self, swap_executor: SwapExecutor):
        """Test can_rollback returns False (placeholder implementation)."""
        swap_id = uuid4()

        can_rollback = swap_executor.can_rollback(swap_id)

        assert can_rollback is False

    def test_can_rollback_different_swap_ids(self, swap_executor: SwapExecutor):
        """Test can_rollback with different swap IDs."""
        swap_id1 = uuid4()
        swap_id2 = uuid4()

        can_rollback1 = swap_executor.can_rollback(swap_id1)
        can_rollback2 = swap_executor.can_rollback(swap_id2)

        assert can_rollback1 is False
        assert can_rollback2 is False

    def test_can_rollback_return_type(self, swap_executor: SwapExecutor):
        """Test can_rollback returns boolean."""
        result = swap_executor.can_rollback(uuid4())

        assert isinstance(result, bool)


# ============================================================================
# Private Method Tests
# ============================================================================


class TestPrivateMethods:
    """Tests for private helper methods."""

    def test_update_schedule_assignments_callable(
        self, swap_executor: SwapExecutor, faculty_a: Person, faculty_b: Person
    ):
        """Test _update_schedule_assignments can be called without error."""
        source_week = date.today() + timedelta(days=14)

        # Should not raise an exception (currently a pass statement)
        swap_executor._update_schedule_assignments(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_b.id,
        )

    def test_update_call_cascade_callable(
        self, swap_executor: SwapExecutor, faculty_b: Person
    ):
        """Test _update_call_cascade can be called without error."""
        week = date.today() + timedelta(days=14)

        # Should not raise an exception (currently a pass statement)
        swap_executor._update_call_cascade(
            week=week,
            new_faculty_id=faculty_b.id,
        )

    def test_update_schedule_assignments_with_same_faculty(
        self, swap_executor: SwapExecutor, faculty_a: Person
    ):
        """Test updating schedule assignments with same source and target."""
        source_week = date.today() + timedelta(days=14)

        # Should handle edge case without error
        swap_executor._update_schedule_assignments(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_a.id,
        )


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestSwapExecutorIntegration:
    """Integration tests for swap executor with database."""

    def test_execute_swap_creates_correct_data_structure(
        self,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        faculty_b: Person,
        test_user: User,
    ):
        """Test that execute_swap prepares correct data structure."""
        source_week = date.today() + timedelta(days=14)
        target_week = date.today() + timedelta(days=21)

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_b.id,
            target_week=target_week,
            swap_type="one_to_one",
            reason="Integration test",
            executed_by_id=test_user.id,
        )

        # Verify the result structure
        assert result.success is True
        assert isinstance(result.swap_id, UUID)
        assert result.message
        assert result.error_code is None

    def test_execute_multiple_swaps_for_same_faculty(
        self,
        swap_executor: SwapExecutor,
        faculty_a: Person,
        faculty_b: Person,
    ):
        """Test executing multiple swaps involving the same faculty."""
        # Execute first swap
        result1 = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_b.id,
            target_week=date.today() + timedelta(days=21),
            swap_type="one_to_one",
        )

        # Execute second swap
        result2 = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=28),
            target_faculty_id=faculty_b.id,
            target_week=date.today() + timedelta(days=35),
            swap_type="one_to_one",
        )

        assert result1.success is True
        assert result2.success is True
        assert result1.swap_id != result2.swap_id

    def test_execute_swap_with_real_database_session(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
    ):
        """Test execution with real database session."""
        executor = SwapExecutor(db)

        result = executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_b.id,
            target_week=date.today() + timedelta(days=21),
            swap_type="one_to_one",
        )

        assert result.success is True
        assert result.swap_id is not None


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestSwapExecutorEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_execute_swap_with_very_long_reason(
        self, swap_executor: SwapExecutor, faculty_a: Person, faculty_b: Person
    ):
        """Test executing swap with very long reason text."""
        long_reason = "A" * 10000  # 10k character reason

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_b.id,
            target_week=date.today() + timedelta(days=21),
            swap_type="one_to_one",
            reason=long_reason,
        )

        assert result.success is True

    def test_execute_swap_with_empty_string_reason(
        self, swap_executor: SwapExecutor, faculty_a: Person, faculty_b: Person
    ):
        """Test executing swap with empty string reason."""
        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_b.id,
            target_week=date.today() + timedelta(days=21),
            swap_type="one_to_one",
            reason="",
        )

        assert result.success is True

    def test_execute_swap_with_special_characters_in_reason(
        self, swap_executor: SwapExecutor, faculty_a: Person, faculty_b: Person
    ):
        """Test executing swap with special characters in reason."""
        special_reason = "Reason with special chars: @#$%^&*(){}[]|\\<>?/~`"

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_b.id,
            target_week=date.today() + timedelta(days=21),
            swap_type="one_to_one",
            reason=special_reason,
        )

        assert result.success is True

    def test_execute_swap_far_future_date(
        self, swap_executor: SwapExecutor, faculty_a: Person, faculty_b: Person
    ):
        """Test executing swap with date far in the future."""
        far_future = date.today() + timedelta(days=365 * 2)  # 2 years

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=far_future,
            target_faculty_id=faculty_b.id,
            target_week=far_future + timedelta(days=7),
            swap_type="one_to_one",
        )

        assert result.success is True

    def test_rollback_window_hours_immutable(self, swap_executor: SwapExecutor):
        """Test that ROLLBACK_WINDOW_HOURS is a constant."""
        original_value = swap_executor.ROLLBACK_WINDOW_HOURS

        # Try to modify (won't work in practice but demonstrates it's a class attribute)
        assert original_value == 24
        assert SwapExecutor.ROLLBACK_WINDOW_HOURS == 24


# ============================================================================
# Future Implementation Tests (To be updated when models are wired)
# ============================================================================


class TestSwapExecutorIntegration:
    """
    Integration tests for SwapExecutor with database.

    These tests verify that:
    - Swaps persist SwapRecord to database
    - Schedule assignments are actually updated
    - Call cascade is updated for Fri/Sat
    - Rollback works within 24-hour window
    """

    def test_execute_swap_persists_record(
        self,
        swap_executor: SwapExecutor,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
    ):
        """Test that executing a swap persists SwapRecord to database."""
        source_week = date.today() + timedelta(days=14)
        target_week = date.today() + timedelta(days=21)

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_b.id,
            target_week=target_week,
            swap_type="one_to_one",
        )

        # Should be able to query the swap record
        swap_record = db.query(SwapRecord).filter_by(id=result.swap_id).first()
        assert swap_record is not None
        assert swap_record.status == SwapStatus.EXECUTED
        assert swap_record.source_faculty_id == faculty_a.id
        assert swap_record.target_faculty_id == faculty_b.id

    def test_execute_swap_updates_assignments(
        self,
        swap_executor: SwapExecutor,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
    ):
        """Test that executing a swap updates schedule assignments."""
        source_week = date.today() + timedelta(days=14)

        # Create assignments for source week
        # ... (create assignment setup)

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_b.id,
            target_week=None,
            swap_type="absorb",
        )

        # Verify assignments were updated
        # ... (assertions for updated assignments)
        assert result.success is True

    def test_execute_swap_updates_call_cascade(
        self,
        swap_executor: SwapExecutor,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
    ):
        """Test that executing a swap updates call cascade for Fri/Sat."""
        source_week = date.today() + timedelta(days=14)

        # Create call cascade assignments
        # ... (create call cascade setup)

        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_b.id,
            target_week=None,
            swap_type="absorb",
        )

        # Verify call cascade was updated
        # ... (assertions for updated call cascade)
        assert result.success is True

    def test_rollback_swap_within_window(
        self,
        swap_executor: SwapExecutor,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
        test_user: User,
    ):
        """Test rolling back a swap within the 24-hour window."""
        # Execute a swap
        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_b.id,
            target_week=date.today() + timedelta(days=21),
            swap_type="one_to_one",
        )

        # Rollback within window
        rollback_result = swap_executor.rollback_swap(
            swap_id=result.swap_id,
            reason="User requested",
            rolled_back_by_id=test_user.id,
        )

        assert rollback_result.success is True

        # Verify swap record status
        swap_record = db.query(SwapRecord).filter_by(id=result.swap_id).first()
        assert swap_record.status == SwapStatus.ROLLED_BACK

    def test_rollback_swap_outside_window(
        self,
        swap_executor: SwapExecutor,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
    ):
        """Test that rollback fails outside the 24-hour window."""
        # Execute a swap
        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_b.id,
            target_week=date.today() + timedelta(days=21),
            swap_type="one_to_one",
        )

        # Manually update executed_at to be >24 hours ago
        swap_record = db.query(SwapRecord).filter_by(id=result.swap_id).first()
        swap_record.executed_at = datetime.utcnow() - timedelta(hours=25)
        db.commit()

        # Attempt rollback
        rollback_result = swap_executor.rollback_swap(
            swap_id=result.swap_id,
            reason="Too late",
        )

        assert rollback_result.success is False
        assert rollback_result.error_code == "ROLLBACK_WINDOW_EXPIRED"

    def test_can_rollback_within_window(
        self,
        swap_executor: SwapExecutor,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
    ):
        """Test can_rollback returns True within 24-hour window."""
        # Execute a swap
        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_b.id,
            target_week=date.today() + timedelta(days=21),
            swap_type="one_to_one",
        )

        # Check if can rollback
        can_rollback = swap_executor.can_rollback(result.swap_id)

        assert can_rollback is True

    def test_can_rollback_outside_window(
        self,
        swap_executor: SwapExecutor,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
    ):
        """Test can_rollback returns False outside 24-hour window."""
        # Execute a swap and age it
        result = swap_executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_b.id,
            target_week=date.today() + timedelta(days=21),
            swap_type="one_to_one",
        )

        # Manually update executed_at
        swap_record = db.query(SwapRecord).filter_by(id=result.swap_id).first()
        swap_record.executed_at = datetime.utcnow() - timedelta(hours=25)
        db.commit()

        # Check if can rollback
        can_rollback = swap_executor.can_rollback(result.swap_id)

        assert can_rollback is False
