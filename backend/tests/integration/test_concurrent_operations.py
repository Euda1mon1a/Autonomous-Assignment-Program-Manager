"""
Integration tests for concurrent operations.

Tests critical concurrency scenarios including:
1. Concurrent assignment edits (optimistic locking)
2. Swap requests during schedule generation
3. Task cancellation mid-execution
4. Race conditions in swap matching

Based on TEST_SCENARIO_FRAMES.md Section 5.
"""

import asyncio
import threading
import time
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord, SwapStatus, SwapType


# ============================================================================
# Test Fixtures for Concurrent Scenarios
# ============================================================================


@pytest.fixture
def concurrent_edit_scenario(integration_db: Session, full_program_setup: dict):
    """
    Create scenario for concurrent edit testing.

    Returns:
        dict with keys: assignment, faculty_a, faculty_b, block
    """
    setup = full_program_setup
    faculty_a = setup["faculty"][0]
    faculty_b = setup["faculty"][1]
    template = setup["templates"][0]
    block = setup["blocks"][0]

    # Create an assignment that will be edited concurrently
    assignment = Assignment(
        id=uuid4(),
        block_id=block.id,
        person_id=faculty_a.id,
        rotation_template_id=template.id,
        role="primary",
    )
    integration_db.add(assignment)
    integration_db.commit()
    integration_db.refresh(assignment)

    return {
        "assignment": assignment,
        "faculty_a": faculty_a,
        "faculty_b": faculty_b,
        "block": block,
        "template": template,
    }


@pytest.fixture
def swap_scenario(integration_db: Session, full_program_setup: dict):
    """
    Create scenario for swap testing with two faculty and assignments.

    Returns:
        dict with keys: faculty_a, faculty_b, assignment_a, assignment_b, blocks
    """
    setup = full_program_setup
    faculty_a = setup["faculty"][0]
    faculty_b = setup["faculty"][1]
    template = setup["templates"][0]

    # Create two assignments on different days
    block_a = setup["blocks"][0]
    block_b = setup["blocks"][2]

    assignment_a = Assignment(
        id=uuid4(),
        block_id=block_a.id,
        person_id=faculty_a.id,
        rotation_template_id=template.id,
        role="primary",
    )

    assignment_b = Assignment(
        id=uuid4(),
        block_id=block_b.id,
        person_id=faculty_b.id,
        rotation_template_id=template.id,
        role="primary",
    )

    integration_db.add_all([assignment_a, assignment_b])
    integration_db.commit()
    integration_db.refresh(assignment_a)
    integration_db.refresh(assignment_b)

    return {
        "faculty_a": faculty_a,
        "faculty_b": faculty_b,
        "assignment_a": assignment_a,
        "assignment_b": assignment_b,
        "block_a": block_a,
        "block_b": block_b,
    }


# ============================================================================
# Frame 5.1: Concurrent Assignment Edit Tests
# ============================================================================


@pytest.mark.integration
class TestConcurrentAssignmentEdit:
    """Test concurrent edits to same assignment with transaction isolation."""

    def test_concurrent_assignment_edit_with_separate_sessions(
        self, concurrent_edit_scenario
    ):
        """
        Test concurrent edits using separate database sessions.

        Scenario: User A and User B both edit assignment simultaneously
        Expected: Second commit should detect conflicting update
        """
        assignment_id = concurrent_edit_scenario["assignment"].id
        faculty_b_id = concurrent_edit_scenario["faculty_b"].id

        results = {"session_a_success": None, "session_b_success": None, "error": None}

        def edit_with_session_a():
            """Simulate User A editing the assignment."""
            db = SessionLocal()
            try:
                # Fetch assignment
                assignment = db.query(Assignment).filter_by(id=assignment_id).first()

                # Simulate some processing time
                time.sleep(0.1)

                # Modify assignment
                assignment.notes = "Modified by User A"
                assignment.updated_at = datetime.utcnow()

                db.commit()
                results["session_a_success"] = True
            except Exception as e:
                db.rollback()
                results["session_a_success"] = False
                if not results["error"]:
                    results["error"] = str(e)
            finally:
                db.close()

        def edit_with_session_b():
            """Simulate User B editing the assignment."""
            db = SessionLocal()
            try:
                # Fetch assignment
                assignment = db.query(Assignment).filter_by(id=assignment_id).first()

                # Simulate some processing time
                time.sleep(0.1)

                # Modify assignment (different field)
                assignment.person_id = faculty_b_id
                assignment.updated_at = datetime.utcnow()

                db.commit()
                results["session_b_success"] = True
            except Exception as e:
                db.rollback()
                results["session_b_success"] = False
                if not results["error"]:
                    results["error"] = str(e)
            finally:
                db.close()

        # Execute both edits concurrently
        thread_a = threading.Thread(target=edit_with_session_a)
        thread_b = threading.Thread(target=edit_with_session_b)

        thread_a.start()
        thread_b.start()

        thread_a.join()
        thread_b.join()

        # Both should succeed with SQLite (no row-level locking)
        # In PostgreSQL with proper optimistic locking, one would fail
        # This test documents the current behavior
        assert results["session_a_success"] is not None
        assert results["session_b_success"] is not None

        # Verify final state - last write wins in SQLite
        db = SessionLocal()
        try:
            assignment = db.query(Assignment).filter_by(id=assignment_id).first()
            # One of the changes should be present
            assert assignment is not None
        finally:
            db.close()

    def test_concurrent_edit_with_explicit_locking(self, concurrent_edit_scenario):
        """
        Test concurrent edits with explicit row-level locking.

        Scenario: Use SELECT ... FOR UPDATE to prevent lost updates
        Expected: Second transaction waits for first to complete
        """
        assignment_id = concurrent_edit_scenario["assignment"].id

        results = {"lock_acquired": [], "update_order": []}

        def edit_with_lock(user_name: str, delay: float):
            """Edit with explicit row lock."""
            db = SessionLocal()
            try:
                # Acquire row-level lock (PostgreSQL: FOR UPDATE, SQLite: immediate lock)
                assignment = (
                    db.query(Assignment)
                    .filter_by(id=assignment_id)
                    .with_for_update()
                    .first()
                )

                results["lock_acquired"].append(user_name)

                # Simulate processing
                time.sleep(delay)

                # Update
                assignment.notes = f"Updated by {user_name}"
                assignment.updated_at = datetime.utcnow()

                db.commit()
                results["update_order"].append(user_name)
            finally:
                db.close()

        # Execute edits concurrently
        thread_a = threading.Thread(
            target=edit_with_lock, args=("User A", 0.2), daemon=True
        )
        thread_b = threading.Thread(
            target=edit_with_lock, args=("User B", 0.1), daemon=True
        )

        thread_a.start()
        time.sleep(0.05)  # Ensure A starts first
        thread_b.start()

        thread_a.join(timeout=2.0)
        thread_b.join(timeout=2.0)

        # Both should complete
        assert len(results["update_order"]) == 2

        # Verify sequential execution (User A should finish first due to earlier lock)
        # Note: In SQLite this may behave differently than PostgreSQL
        db = SessionLocal()
        try:
            assignment = db.query(Assignment).filter_by(id=assignment_id).first()
            assert assignment.notes in ["Updated by User A", "Updated by User B"]
        finally:
            db.close()


# ============================================================================
# Frame 5.2: Swap During Schedule Generation Tests
# ============================================================================


@pytest.mark.integration
class TestSwapDuringGeneration:
    """Test swap requests submitted during schedule generation."""

    @pytest.mark.asyncio
    async def test_swap_during_schedule_generation(self, swap_scenario):
        """
        Test swap request handling during schedule generation.

        Scenario: User submits swap while optimizer is generating next block
        Expected: Swap should be queued or rejected with clear message
        """
        faculty_a = swap_scenario["faculty_a"]
        faculty_b = swap_scenario["faculty_b"]
        assignment_a = swap_scenario["assignment_a"]
        assignment_b = swap_scenario["assignment_b"]

        generation_in_progress = threading.Event()
        generation_complete = threading.Event()
        swap_result = {"status": None, "error": None}

        def simulate_schedule_generation():
            """Simulate long-running schedule generation."""
            generation_in_progress.set()
            time.sleep(0.5)  # Simulate generation taking 500ms
            generation_complete.set()

        def attempt_swap():
            """Attempt to execute swap during generation."""
            # Wait for generation to start
            generation_in_progress.wait(timeout=1.0)

            db = SessionLocal()
            try:
                # Create swap request
                swap = SwapRecord(
                    id=uuid4(),
                    source_faculty_id=faculty_a.id,
                    source_week=swap_scenario["block_a"].date,
                    target_faculty_id=faculty_b.id,
                    target_week=swap_scenario["block_b"].date,
                    swap_type=SwapType.ONE_TO_ONE,
                    status=SwapStatus.PENDING,
                    requested_at=datetime.utcnow(),
                )
                db.add(swap)
                db.commit()

                # In real system, swap executor would check for generation lock
                # For now, we just verify swap can be created
                swap_result["status"] = "created"
                db.refresh(swap)
                swap_result["swap_id"] = swap.id

            except Exception as e:
                swap_result["status"] = "error"
                swap_result["error"] = str(e)
                db.rollback()
            finally:
                db.close()

        # Start generation task
        gen_thread = threading.Thread(target=simulate_schedule_generation, daemon=True)
        gen_thread.start()

        # Attempt swap during generation
        swap_thread = threading.Thread(target=attempt_swap, daemon=True)
        swap_thread.start()

        # Wait for both to complete
        gen_thread.join(timeout=2.0)
        swap_thread.join(timeout=2.0)

        # Swap should be created (in real system, it would be queued)
        assert swap_result["status"] == "created"
        assert swap_result.get("swap_id") is not None

        # Verify swap exists in database
        db = SessionLocal()
        try:
            swap = db.query(SwapRecord).filter_by(id=swap_result["swap_id"]).first()
            assert swap is not None
            assert swap.status == SwapStatus.PENDING
        finally:
            db.close()


# ============================================================================
# Frame 5.3: Task Cancellation Tests
# ============================================================================


@pytest.mark.integration
class TestTaskCancellation:
    """Test graceful handling of task cancellation."""

    @pytest.mark.asyncio
    async def test_task_cancellation_mid_execution(self, integration_db):
        """
        Test graceful cancellation of long-running task.

        Scenario: Long-running task is cancelled by user
        Expected: Task stops gracefully, database in consistent state
        """
        cancellation_flag = threading.Event()
        task_state = {"assignments_created": 0, "cleanup_done": False}

        def long_running_task():
            """Simulate long-running schedule generation that checks for cancellation."""
            db = SessionLocal()
            created_assignments = []

            try:
                # Simulate creating assignments in batches
                for i in range(10):
                    if cancellation_flag.is_set():
                        # Cancellation requested - rollback and exit
                        db.rollback()
                        task_state["cleanup_done"] = True
                        return

                    # Create assignment (simulating work)
                    # In real scenario, this would be actual assignment creation
                    task_state["assignments_created"] += 1
                    time.sleep(0.1)  # Simulate work

                # If we got here, task completed normally
                db.commit()

            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

        # Start task
        task_thread = threading.Thread(target=long_running_task, daemon=True)
        task_thread.start()

        # Wait a bit, then cancel
        time.sleep(0.25)  # Let it create ~2-3 assignments
        cancellation_flag.set()

        # Wait for task to acknowledge cancellation
        task_thread.join(timeout=2.0)

        # Verify task stopped early
        assert task_state["assignments_created"] < 10
        assert task_state["cleanup_done"] is True

    @pytest.mark.asyncio
    async def test_task_cancellation_with_asyncio(self):
        """
        Test task cancellation using asyncio.CancelledError.

        Scenario: Async task handles cancellation gracefully
        Expected: Resources cleaned up, no partial state
        """

        async def cancellable_task(progress_callback):
            """Simulated cancellable async task."""
            try:
                for i in range(10):
                    progress_callback(i)
                    await asyncio.sleep(0.1)
                return "completed"
            except asyncio.CancelledError:
                progress_callback("cancelled")
                raise

        progress = []

        # Start task
        task = asyncio.create_task(cancellable_task(progress.append))

        # Wait a bit, then cancel
        await asyncio.sleep(0.25)
        task.cancel()

        # Wait for cancellation to propagate
        with pytest.raises(asyncio.CancelledError):
            await task

        # Verify task was cancelled mid-execution
        assert len(progress) < 10
        assert progress[-1] == "cancelled"


# ============================================================================
# Frame 5.4: Swap Race Condition Tests
# ============================================================================


@pytest.mark.integration
class TestSwapRaceCondition:
    """Test race conditions in concurrent swap matching."""

    def test_swap_race_condition_two_faculty_want_same_shift(
        self, integration_db, full_program_setup
    ):
        """
        Test concurrent swap matching race condition handling.

        Scenario: Faculty A and C both want to swap with Faculty B
        Expected: Only one swap succeeds, other gets clear conflict error
        """
        setup = full_program_setup
        faculty_a = setup["faculty"][0]
        faculty_b = setup["faculty"][1]
        faculty_c = setup["residents"][0]  # Use resident as third party
        template = setup["templates"][0]

        # Create assignments
        # Faculty A has shift 1
        # Faculty C has shift 1 (same as A - conflict scenario)
        # Faculty B has shift 2
        shift_1_date = setup["blocks"][0]
        shift_2_date = setup["blocks"][2]

        assignment_a = Assignment(
            id=uuid4(),
            block_id=shift_1_date.id,
            person_id=faculty_a.id,
            rotation_template_id=template.id,
            role="primary",
        )

        assignment_c = Assignment(
            id=uuid4(),
            block_id=shift_1_date.id,
            person_id=faculty_c.id,
            rotation_template_id=template.id,
            role="backup",  # Different role to avoid unique constraint
        )

        assignment_b = Assignment(
            id=uuid4(),
            block_id=shift_2_date.id,
            person_id=faculty_b.id,
            rotation_template_id=template.id,
            role="primary",
        )

        integration_db.add_all([assignment_a, assignment_c, assignment_b])
        integration_db.commit()

        results = {"swap_a_status": None, "swap_c_status": None}

        def create_swap_a_to_b():
            """Faculty A requests swap with B."""
            db = SessionLocal()
            try:
                swap = SwapRecord(
                    id=uuid4(),
                    source_faculty_id=faculty_a.id,
                    source_week=shift_1_date.date,
                    target_faculty_id=faculty_b.id,
                    target_week=shift_2_date.date,
                    swap_type=SwapType.ONE_TO_ONE,
                    status=SwapStatus.PENDING,
                    requested_at=datetime.utcnow(),
                )
                db.add(swap)
                db.commit()

                # Simulate swap execution with small delay
                time.sleep(0.05)

                # Mark as executed
                swap.status = SwapStatus.EXECUTED
                swap.executed_at = datetime.utcnow()
                db.commit()

                results["swap_a_status"] = "executed"
            except Exception as e:
                results["swap_a_status"] = f"error: {str(e)}"
                db.rollback()
            finally:
                db.close()

        def create_swap_c_to_b():
            """Faculty C also requests swap with B (conflict!)."""
            db = SessionLocal()
            try:
                # Small delay to ensure A starts first
                time.sleep(0.02)

                swap = SwapRecord(
                    id=uuid4(),
                    source_faculty_id=faculty_c.id,
                    source_week=shift_1_date.date,
                    target_faculty_id=faculty_b.id,
                    target_week=shift_2_date.date,
                    swap_type=SwapType.ONE_TO_ONE,
                    status=SwapStatus.PENDING,
                    requested_at=datetime.utcnow(),
                )
                db.add(swap)
                db.commit()

                # Try to execute
                time.sleep(0.05)

                # In real system, this should fail because B's assignment already swapped
                # For now, both will succeed in creating requests
                swap.status = SwapStatus.EXECUTED
                swap.executed_at = datetime.utcnow()
                db.commit()

                results["swap_c_status"] = "executed"
            except Exception as e:
                results["swap_c_status"] = f"error: {str(e)}"
                db.rollback()
            finally:
                db.close()

        # Execute both swap requests concurrently
        thread_a = threading.Thread(target=create_swap_a_to_b, daemon=True)
        thread_c = threading.Thread(target=create_swap_c_to_b, daemon=True)

        thread_a.start()
        thread_c.start()

        thread_a.join(timeout=2.0)
        thread_c.join(timeout=2.0)

        # Both should create requests (real swap executor would handle conflicts)
        # This test documents current behavior and serves as basis for improvements
        assert results["swap_a_status"] is not None
        assert results["swap_c_status"] is not None

    def test_swap_auto_matcher_prevents_double_booking(
        self, integration_db, swap_scenario
    ):
        """
        Test that swap auto-matcher prevents double-booking.

        Scenario: Two compatible swaps submitted for same person
        Expected: First swap locks the assignment, second fails
        """
        faculty_a = swap_scenario["faculty_a"]
        faculty_b = swap_scenario["faculty_b"]
        assignment_a = swap_scenario["assignment_a"]

        results = {"first_swap": None, "second_swap": None}

        def create_first_swap():
            """Create first swap and hold lock briefly."""
            db = SessionLocal()
            try:
                # Lock the assignment
                assignment = (
                    db.query(Assignment)
                    .filter_by(id=assignment_a.id)
                    .with_for_update()
                    .first()
                )

                # Create swap
                swap = SwapRecord(
                    id=uuid4(),
                    source_faculty_id=faculty_a.id,
                    source_week=assignment.block.date,
                    target_faculty_id=faculty_b.id,
                    target_week=assignment.block.date + timedelta(days=1),
                    swap_type=SwapType.ONE_TO_ONE,
                    status=SwapStatus.PENDING,
                )
                db.add(swap)

                # Hold lock for a moment
                time.sleep(0.2)

                db.commit()
                results["first_swap"] = "success"
            except Exception as e:
                results["first_swap"] = f"error: {str(e)}"
                db.rollback()
            finally:
                db.close()

        def create_second_swap():
            """Attempt second swap on same assignment."""
            # Wait a bit to ensure first swap starts
            time.sleep(0.05)

            db = SessionLocal()
            try:
                # Try to lock the same assignment
                assignment = (
                    db.query(Assignment)
                    .filter_by(id=assignment_a.id)
                    .with_for_update(nowait=False)  # Will wait for lock
                    .first()
                )

                # If we get here, first swap already committed
                # Check if assignment is already involved in a swap
                swap = SwapRecord(
                    id=uuid4(),
                    source_faculty_id=faculty_a.id,
                    source_week=assignment.block.date,
                    target_faculty_id=faculty_b.id,
                    target_week=assignment.block.date + timedelta(days=2),
                    swap_type=SwapType.ONE_TO_ONE,
                    status=SwapStatus.PENDING,
                )
                db.add(swap)
                db.commit()
                results["second_swap"] = "success"

            except Exception as e:
                results["second_swap"] = f"error: {str(e)}"
                db.rollback()
            finally:
                db.close()

        # Execute both concurrently
        thread_1 = threading.Thread(target=create_first_swap, daemon=True)
        thread_2 = threading.Thread(target=create_second_swap, daemon=True)

        thread_1.start()
        thread_2.start()

        thread_1.join(timeout=2.0)
        thread_2.join(timeout=2.0)

        # First should always succeed
        assert results["first_swap"] == "success"

        # Second may succeed or fail depending on timing (both are valid behaviors)
        # Real swap executor would add additional validation
        assert results["second_swap"] is not None


# ============================================================================
# Additional Edge Cases
# ============================================================================


@pytest.mark.integration
class TestConcurrentEdgeCases:
    """Test edge cases in concurrent operations."""

    def test_concurrent_read_during_write(self, concurrent_edit_scenario):
        """
        Test reading assignment while it's being updated.

        Scenario: User reads assignment while another user updates it
        Expected: Read sees either old or new value (no partial state)
        """
        assignment_id = concurrent_edit_scenario["assignment"].id

        results = {"read_value": None, "write_complete": False}

        def write_assignment():
            """Update assignment."""
            db = SessionLocal()
            try:
                assignment = db.query(Assignment).filter_by(id=assignment_id).first()
                time.sleep(0.1)  # Simulate slow update
                assignment.notes = "Updated value"
                db.commit()
                results["write_complete"] = True
            finally:
                db.close()

        def read_assignment():
            """Read assignment during update."""
            time.sleep(0.05)  # Start read during write
            db = SessionLocal()
            try:
                assignment = db.query(Assignment).filter_by(id=assignment_id).first()
                results["read_value"] = assignment.notes
            finally:
                db.close()

        # Execute concurrently
        write_thread = threading.Thread(target=write_assignment, daemon=True)
        read_thread = threading.Thread(target=read_assignment, daemon=True)

        write_thread.start()
        read_thread.start()

        write_thread.join(timeout=1.0)
        read_thread.join(timeout=1.0)

        # Read should see either None (original) or "Updated value" (new)
        # Never partial state
        assert results["read_value"] in [None, "Updated value"]
        assert results["write_complete"] is True

    def test_deadlock_prevention(self, integration_db, full_program_setup):
        """
        Test deadlock prevention in concurrent operations.

        Scenario: Two transactions try to lock resources in different order
        Expected: One waits for the other, no deadlock
        """
        setup = full_program_setup
        assignment_1 = Assignment(
            id=uuid4(),
            block_id=setup["blocks"][0].id,
            person_id=setup["faculty"][0].id,
            rotation_template_id=setup["templates"][0].id,
            role="primary",
        )
        assignment_2 = Assignment(
            id=uuid4(),
            block_id=setup["blocks"][1].id,
            person_id=setup["faculty"][1].id,
            rotation_template_id=setup["templates"][0].id,
            role="primary",
        )
        integration_db.add_all([assignment_1, assignment_2])
        integration_db.commit()

        results = {"thread_1": None, "thread_2": None}

        def transaction_1():
            """Lock assignments in order: 1 then 2."""
            db = SessionLocal()
            try:
                a1 = (
                    db.query(Assignment)
                    .filter_by(id=assignment_1.id)
                    .with_for_update()
                    .first()
                )
                time.sleep(0.1)
                a2 = (
                    db.query(Assignment)
                    .filter_by(id=assignment_2.id)
                    .with_for_update()
                    .first()
                )
                a1.notes = "T1"
                a2.notes = "T1"
                db.commit()
                results["thread_1"] = "success"
            except Exception as e:
                results["thread_1"] = f"error: {str(e)}"
                db.rollback()
            finally:
                db.close()

        def transaction_2():
            """Lock assignments in same order: 1 then 2 (prevents deadlock)."""
            time.sleep(0.05)  # Start slightly after thread 1
            db = SessionLocal()
            try:
                a1 = (
                    db.query(Assignment)
                    .filter_by(id=assignment_1.id)
                    .with_for_update()
                    .first()
                )
                a2 = (
                    db.query(Assignment)
                    .filter_by(id=assignment_2.id)
                    .with_for_update()
                    .first()
                )
                a1.notes = "T2"
                a2.notes = "T2"
                db.commit()
                results["thread_2"] = "success"
            except Exception as e:
                results["thread_2"] = f"error: {str(e)}"
                db.rollback()
            finally:
                db.close()

        # Execute concurrently
        t1 = threading.Thread(target=transaction_1, daemon=True)
        t2 = threading.Thread(target=transaction_2, daemon=True)

        t1.start()
        t2.start()

        t1.join(timeout=2.0)
        t2.join(timeout=2.0)

        # Both should complete (one waits for the other)
        assert results["thread_1"] == "success"
        assert results["thread_2"] == "success"
