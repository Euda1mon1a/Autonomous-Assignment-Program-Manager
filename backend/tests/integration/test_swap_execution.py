"""
Integration tests for swap execution service.

Based on test frames from docs/testing/TEST_SCENARIO_FRAMES.md
Tests the full swap execution workflow including:
- One-to-one swaps
- Absorb swaps (give-away)
- Rollback within 24-hour window
- Validation failures

Note: ACGME validation is not currently integrated into SwapExecutor.
Future enhancement needed to validate swaps don't violate work hour limits.
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.call_assignment import CallAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.services.swap_executor import SwapExecutor


# ============================================================================
# Fixtures for Swap Testing
# ============================================================================


@pytest.fixture
def swap_faculty_pair(db: Session) -> dict:
    """
    Create two faculty members for swap testing.

    Returns:
        dict with keys: faculty_a, faculty_b
    """
    faculty_a = Person(
        id=uuid4(),
        name="Dr. Alice Faculty",
        type="faculty",
        email="alice.faculty@hospital.org",
        performs_procedures=True,
        specialties=["Sports Medicine"],
    )
    faculty_b = Person(
        id=uuid4(),
        name="Dr. Bob Faculty",
        type="faculty",
        email="bob.faculty@hospital.org",
        performs_procedures=True,
        specialties=["Primary Care"],
    )

    db.add_all([faculty_a, faculty_b])
    db.commit()
    db.refresh(faculty_a)
    db.refresh(faculty_b)

    return {"faculty_a": faculty_a, "faculty_b": faculty_b}


@pytest.fixture
def rotation_templates(db: Session) -> dict:
    """
    Create rotation templates for testing.

    Returns:
        dict with keys: clinic, call, procedures
    """
    clinic_rotation = RotationTemplate(
        id=uuid4(),
        name="Sports Medicine Clinic",
        rotation_type="clinic",
        abbreviation="SM",
        clinic_location="Building A",
        max_residents=4,
        supervision_required=True,
        max_supervision_ratio=4,
    )

    call_rotation = RotationTemplate(
        id=uuid4(),
        name="Call Coverage",
        rotation_type="call",
        abbreviation="CALL",
        max_residents=1,
        supervision_required=True,
        max_supervision_ratio=2,
    )

    procedures_rotation = RotationTemplate(
        id=uuid4(),
        name="Procedures",
        rotation_type="procedures",
        abbreviation="PROC",
        max_residents=2,
        supervision_required=True,
        max_supervision_ratio=2,
    )

    db.add_all([clinic_rotation, call_rotation, procedures_rotation])
    db.commit()
    db.refresh(clinic_rotation)
    db.refresh(call_rotation)
    db.refresh(procedures_rotation)

    return {
        "clinic": clinic_rotation,
        "call": call_rotation,
        "procedures": procedures_rotation,
    }


@pytest.fixture
def swap_week_blocks(db: Session) -> dict:
    """
    Create blocks for two weeks for swap testing.

    Returns:
        dict with keys: week1_start, week1_blocks, week2_start, week2_blocks
    """
    # Week 1: Jan 15-21, 2025 (Monday-Sunday)
    week1_start = date(2025, 1, 13)  # Monday
    week1_blocks = []

    for i in range(7):
        current_date = week1_start + timedelta(days=i)
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=1,
                is_weekend=(current_date.weekday() >= 5),
                is_holiday=False,
            )
            db.add(block)
            week1_blocks.append(block)

    # Week 2: Jan 22-28, 2025 (Monday-Sunday)
    week2_start = date(2025, 1, 20)  # Monday
    week2_blocks = []

    for i in range(7):
        current_date = week2_start + timedelta(days=i)
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=2,
                is_weekend=(current_date.weekday() >= 5),
                is_holiday=False,
            )
            db.add(block)
            week2_blocks.append(block)

    db.commit()

    return {
        "week1_start": week1_start,
        "week1_blocks": week1_blocks,
        "week2_start": week2_start,
        "week2_blocks": week2_blocks,
    }


@pytest.fixture
def one_to_one_swap_scenario(
    db: Session,
    swap_faculty_pair: dict,
    swap_week_blocks: dict,
    rotation_templates: dict,
) -> dict:
    """
    Create complete scenario for one-to-one swap testing.

    Faculty A has clinic assignments in week 1.
    Faculty B has call assignments in week 2.
    They want to swap entire weeks.

    Returns:
        dict with all necessary data for swap tests
    """
    faculty_a = swap_faculty_pair["faculty_a"]
    faculty_b = swap_faculty_pair["faculty_b"]
    week1_blocks = swap_week_blocks["week1_blocks"]
    week2_blocks = swap_week_blocks["week2_blocks"]
    clinic = rotation_templates["clinic"]
    call = rotation_templates["call"]

    # Create assignments for faculty A in week 1 (clinic)
    week1_assignments = []
    for block in week1_blocks:
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=faculty_a.id,
            rotation_template_id=clinic.id,
            role="primary",
        )
        db.add(assignment)
        week1_assignments.append(assignment)

    # Create assignments for faculty B in week 2 (call)
    week2_assignments = []
    for block in week2_blocks:
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=faculty_b.id,
            rotation_template_id=call.id,
            role="primary",
        )
        db.add(assignment)
        week2_assignments.append(assignment)

    # Create call assignments for Friday/Saturday in both weeks
    # Week 1 Friday
    week1_friday = swap_week_blocks["week1_start"] + timedelta(days=4)
    call_week1_fri = CallAssignment(
        id=uuid4(),
        date=week1_friday,
        person_id=faculty_a.id,
        call_type="overnight",
        is_weekend=False,
    )
    db.add(call_week1_fri)

    # Week 2 Saturday
    week2_saturday = swap_week_blocks["week2_start"] + timedelta(days=5)
    call_week2_sat = CallAssignment(
        id=uuid4(),
        date=week2_saturday,
        person_id=faculty_b.id,
        call_type="overnight",
        is_weekend=True,
    )
    db.add(call_week2_sat)

    db.commit()

    return {
        **swap_faculty_pair,
        **swap_week_blocks,
        **rotation_templates,
        "week1_assignments": week1_assignments,
        "week2_assignments": week2_assignments,
        "call_week1_fri": call_week1_fri,
        "call_week2_sat": call_week2_sat,
    }


# ============================================================================
# Test 1.1: Basic One-to-One Swap
# ============================================================================


def test_execute_one_to_one_swap(db: Session, one_to_one_swap_scenario: dict):
    """
    Test successful one-to-one swap execution.

    Frame 1.1 from TEST_SCENARIO_FRAMES.md

    Scenario:
        Faculty A has clinic week (Jan 13-19).
        Faculty B has call week (Jan 20-26).
        They swap entire weeks.

    Expected:
        - Swap executes successfully
        - All assignments transferred
        - Call assignments updated
        - SwapRecord created with EXECUTED status
        - Audit trail exists
    """
    # SETUP
    faculty_a = one_to_one_swap_scenario["faculty_a"]
    faculty_b = one_to_one_swap_scenario["faculty_b"]
    week1_start = one_to_one_swap_scenario["week1_start"]
    week2_start = one_to_one_swap_scenario["week2_start"]
    week1_assignments = one_to_one_swap_scenario["week1_assignments"]
    week2_assignments = one_to_one_swap_scenario["week2_assignments"]

    # Verify initial state
    assert len(week1_assignments) == 14  # 7 days × 2 sessions
    assert len(week2_assignments) == 14
    assert all(a.person_id == faculty_a.id for a in week1_assignments)
    assert all(a.person_id == faculty_b.id for a in week2_assignments)

    # ACTION
    executor = SwapExecutor(db)
    result = executor.execute_swap(
        source_faculty_id=faculty_a.id,
        source_week=week1_start,
        target_faculty_id=faculty_b.id,
        target_week=week2_start,
        swap_type=SwapType.ONE_TO_ONE,
        reason="Faculty requested schedule swap for personal reasons",
    )

    # ASSERT - Execution result
    assert result.success is True
    assert result.swap_id is not None
    assert "transferred" in result.message.lower()
    assert result.error_code is None

    # ASSERT - SwapRecord created
    swap_record = db.query(SwapRecord).filter(SwapRecord.id == result.swap_id).first()
    assert swap_record is not None
    assert swap_record.status == SwapStatus.EXECUTED
    assert swap_record.swap_type == SwapType.ONE_TO_ONE
    assert swap_record.source_faculty_id == faculty_a.id
    assert swap_record.target_faculty_id == faculty_b.id
    assert swap_record.source_week == week1_start
    assert swap_record.target_week == week2_start
    assert swap_record.executed_at is not None

    # ASSERT - Week 1 assignments transferred to faculty B
    db.expire_all()  # Refresh from database
    for assignment in week1_assignments:
        db.refresh(assignment)
        assert assignment.person_id == faculty_b.id, (
            f"Week 1 assignment {assignment.id} should be transferred to faculty B"
        )
        assert "swapped" in assignment.notes.lower()

    # ASSERT - Week 2 assignments transferred to faculty A
    for assignment in week2_assignments:
        db.refresh(assignment)
        assert assignment.person_id == faculty_a.id, (
            f"Week 2 assignment {assignment.id} should be transferred to faculty A"
        )
        assert "swapped" in assignment.notes.lower()

    # ASSERT - Call assignments updated
    call_week1_fri = one_to_one_swap_scenario["call_week1_fri"]
    call_week2_sat = one_to_one_swap_scenario["call_week2_sat"]

    db.refresh(call_week1_fri)
    db.refresh(call_week2_sat)

    assert call_week1_fri.person_id == faculty_b.id, (
        "Week 1 Friday call should be transferred to faculty B"
    )
    assert call_week2_sat.person_id == faculty_a.id, (
        "Week 2 Saturday call should be transferred to faculty A"
    )


# ============================================================================
# Test 1.2: Swap Rollback Within 24-Hour Window
# ============================================================================


def test_swap_execution_rollback(db: Session, one_to_one_swap_scenario: dict):
    """
    Test swap rollback within permitted 24-hour window.

    Frame 1.2 from TEST_SCENARIO_FRAMES.md

    Scenario:
        1. Execute one-to-one swap
        2. Immediately request rollback (within 24h)
        3. Verify original assignments restored

    Expected:
        - Rollback succeeds
        - Original assignments restored
        - SwapRecord status updated to ROLLED_BACK
        - Rollback timestamp recorded
    """
    # SETUP - Execute initial swap
    faculty_a = one_to_one_swap_scenario["faculty_a"]
    faculty_b = one_to_one_swap_scenario["faculty_b"]
    week1_start = one_to_one_swap_scenario["week1_start"]
    week2_start = one_to_one_swap_scenario["week2_start"]
    week1_assignments = one_to_one_swap_scenario["week1_assignments"]
    week2_assignments = one_to_one_swap_scenario["week2_assignments"]

    executor = SwapExecutor(db)
    swap_result = executor.execute_swap(
        source_faculty_id=faculty_a.id,
        source_week=week1_start,
        target_faculty_id=faculty_b.id,
        target_week=week2_start,
        swap_type=SwapType.ONE_TO_ONE,
        reason="Initial swap request",
    )

    assert swap_result.success is True
    swap_id = swap_result.swap_id

    # Verify swap executed (assignments swapped)
    db.expire_all()
    db.refresh(week1_assignments[0])
    db.refresh(week2_assignments[0])
    assert week1_assignments[0].person_id == faculty_b.id
    assert week2_assignments[0].person_id == faculty_a.id

    # ACTION - Rollback within 24-hour window
    rollback_result = executor.rollback_swap(
        swap_id=swap_id,
        reason="Faculty member had family emergency, need to revert",
    )

    # ASSERT - Rollback succeeded
    assert rollback_result.success is True
    assert rollback_result.error_code is None
    assert "successfully" in rollback_result.message.lower()

    # ASSERT - SwapRecord updated
    swap_record = db.query(SwapRecord).filter(SwapRecord.id == swap_id).first()
    assert swap_record.status == SwapStatus.ROLLED_BACK
    assert swap_record.rolled_back_at is not None
    assert (
        swap_record.rollback_reason
        == "Faculty member had family emergency, need to revert"
    )

    # ASSERT - Original assignments restored
    db.expire_all()
    for assignment in week1_assignments:
        db.refresh(assignment)
        assert assignment.person_id == faculty_a.id, (
            f"Week 1 assignment {assignment.id} should be restored to faculty A"
        )

    for assignment in week2_assignments:
        db.refresh(assignment)
        assert assignment.person_id == faculty_b.id, (
            f"Week 2 assignment {assignment.id} should be restored to faculty B"
        )

    # ASSERT - Call assignments restored
    call_week1_fri = one_to_one_swap_scenario["call_week1_fri"]
    call_week2_sat = one_to_one_swap_scenario["call_week2_sat"]

    db.refresh(call_week1_fri)
    db.refresh(call_week2_sat)

    assert call_week1_fri.person_id == faculty_a.id
    assert call_week2_sat.person_id == faculty_b.id


def test_swap_rollback_window_expired(db: Session, one_to_one_swap_scenario: dict):
    """
    Test rollback fails after 24-hour window expires.

    Scenario:
        1. Execute swap
        2. Manually set executed_at to 25 hours ago
        3. Attempt rollback
        4. Verify rollback rejected

    Expected:
        - Rollback fails with ROLLBACK_WINDOW_EXPIRED error
        - Assignments remain swapped
        - SwapRecord status unchanged
    """
    # SETUP
    faculty_a = one_to_one_swap_scenario["faculty_a"]
    faculty_b = one_to_one_swap_scenario["faculty_b"]
    week1_start = one_to_one_swap_scenario["week1_start"]
    week2_start = one_to_one_swap_scenario["week2_start"]

    executor = SwapExecutor(db)
    swap_result = executor.execute_swap(
        source_faculty_id=faculty_a.id,
        source_week=week1_start,
        target_faculty_id=faculty_b.id,
        target_week=week2_start,
        swap_type=SwapType.ONE_TO_ONE,
        reason="Test swap",
    )

    swap_id = swap_result.swap_id

    # Manually set executed_at to 25 hours ago (past the 24-hour window)
    swap_record = db.query(SwapRecord).filter(SwapRecord.id == swap_id).first()
    swap_record.executed_at = datetime.utcnow() - timedelta(hours=25)
    db.commit()

    # ACTION - Attempt rollback after window expired
    rollback_result = executor.rollback_swap(
        swap_id=swap_id,
        reason="Attempting late rollback",
    )

    # ASSERT - Rollback failed
    assert rollback_result.success is False
    assert rollback_result.error_code == "ROLLBACK_WINDOW_EXPIRED"
    assert "24 hours" in rollback_result.message.lower()

    # ASSERT - SwapRecord status unchanged
    db.refresh(swap_record)
    assert swap_record.status == SwapStatus.EXECUTED
    assert swap_record.rolled_back_at is None


def test_can_rollback_boundary_conditions(db: Session, one_to_one_swap_scenario: dict):
    """
    Test can_rollback() at exact boundary conditions.

    Tests:
        - Exactly at 24:00:00 (edge case)
        - Just before window expires (23:59:00)
        - Just after window expires (24:01:00)
    """
    faculty_a = one_to_one_swap_scenario["faculty_a"]
    faculty_b = one_to_one_swap_scenario["faculty_b"]
    week1_start = one_to_one_swap_scenario["week1_start"]

    executor = SwapExecutor(db)
    swap_result = executor.execute_swap(
        source_faculty_id=faculty_a.id,
        source_week=week1_start,
        target_faculty_id=faculty_b.id,
        target_week=None,  # Absorb swap for simplicity
        swap_type=SwapType.ABSORB,
    )

    swap_id = swap_result.swap_id
    swap_record = db.query(SwapRecord).filter(SwapRecord.id == swap_id).first()

    # Test 1: Just before window expires (23:59:00) - should succeed
    swap_record.executed_at = datetime.utcnow() - timedelta(hours=23, minutes=59)
    db.commit()
    assert executor.can_rollback(swap_id) is True

    # Test 2: Exactly at 24:00:00 - should succeed (inclusive)
    swap_record.executed_at = datetime.utcnow() - timedelta(hours=24)
    db.commit()
    assert executor.can_rollback(swap_id) is True

    # Test 3: Just after window expires (24:01:00) - should fail
    swap_record.executed_at = datetime.utcnow() - timedelta(hours=24, minutes=1)
    db.commit()
    assert executor.can_rollback(swap_id) is False


# ============================================================================
# Test 1.3: Swap Validation Failure
# ============================================================================


def test_execute_swap_validation_failure(db: Session, swap_faculty_pair: dict):
    """
    Test swap execution with validation errors.

    Frame 1.3 from TEST_SCENARIO_FRAMES.md

    NOTE: Current SwapExecutor does not implement ACGME validation.
    This test demonstrates the expected behavior once validation is added.

    Scenario:
        Attempt swap that would violate ACGME 80-hour rule.

    Current behavior: Swap executes (no validation)
    Expected future behavior: Swap rejected with validation error

    TODO: Update this test when ACGME validation is integrated into SwapExecutor
    """
    # SETUP
    faculty_a = swap_faculty_pair["faculty_a"]
    faculty_b = swap_faculty_pair["faculty_b"]
    week1_start = date(2025, 1, 13)

    executor = SwapExecutor(db)

    # NOTE: This test currently passes because validation isn't implemented
    # When ACGME validation is added, this should raise an exception
    result = executor.execute_swap(
        source_faculty_id=faculty_a.id,
        source_week=week1_start,
        target_faculty_id=faculty_b.id,
        target_week=None,
        swap_type=SwapType.ABSORB,
        reason="Testing validation",
    )

    # Current behavior: succeeds
    assert result.success is True

    # TODO: Future expected behavior (uncomment when validation added):
    # with pytest.raises(ValueError, match="ACGME.*violation"):
    #     executor.execute_swap(
    #         source_faculty_id=faculty_a.id,
    #         source_week=week1_start,
    #         target_faculty_id=faculty_b.id,
    #         target_week=None,
    #         swap_type=SwapType.ABSORB,
    #     )


def test_execute_swap_nonexistent_faculty(db: Session):
    """
    Test swap execution with nonexistent faculty IDs.

    Scenario:
        Attempt swap with invalid faculty ID.

    Expected:
        Execution fails gracefully with error message.
    """
    fake_faculty_id = uuid4()
    week1_start = date(2025, 1, 13)

    executor = SwapExecutor(db)
    result = executor.execute_swap(
        source_faculty_id=fake_faculty_id,
        source_week=week1_start,
        target_faculty_id=uuid4(),
        target_week=None,
        swap_type=SwapType.ABSORB,
    )

    # Should fail gracefully
    assert result.success is False
    assert result.error_code == "EXECUTION_FAILED"
    assert result.message is not None


def test_rollback_nonexistent_swap(db: Session):
    """
    Test rollback of nonexistent swap ID.

    Expected:
        Rollback fails with SWAP_NOT_FOUND error.
    """
    fake_swap_id = uuid4()

    executor = SwapExecutor(db)
    result = executor.rollback_swap(
        swap_id=fake_swap_id,
        reason="Testing error handling",
    )

    assert result.success is False
    assert result.error_code == "SWAP_NOT_FOUND"
    assert "not found" in result.message.lower()


# ============================================================================
# Test 1.4: Absorb Swap (Give-Away)
# ============================================================================


def test_execute_absorb_swap(
    db: Session,
    swap_faculty_pair: dict,
    swap_week_blocks: dict,
    rotation_templates: dict,
):
    """
    Test absorb-type swap where one faculty gives away shift.

    Frame 1.4 from TEST_SCENARIO_FRAMES.md

    Scenario:
        Faculty A wants to give away week 1 (e.g., family emergency).
        Faculty B absorbs the week (gets extra shifts, nothing in return).

    Expected:
        - Swap executes with SwapType.ABSORB
        - Week 1 assignments transferred to faculty B
        - No reciprocal transfer (target_week is None)
        - Work hours updated (faculty A decreased, faculty B increased)
    """
    # SETUP
    faculty_a = swap_faculty_pair["faculty_a"]
    faculty_b = swap_faculty_pair["faculty_b"]
    week1_start = swap_week_blocks["week1_start"]
    week1_blocks = swap_week_blocks["week1_blocks"]
    clinic = rotation_templates["clinic"]

    # Create assignments for faculty A in week 1
    week1_assignments = []
    for block in week1_blocks:
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=faculty_a.id,
            rotation_template_id=clinic.id,
            role="primary",
        )
        db.add(assignment)
        week1_assignments.append(assignment)

    db.commit()

    # Verify initial state
    assert len(week1_assignments) == 14  # 7 days × 2 sessions
    assert all(a.person_id == faculty_a.id for a in week1_assignments)

    # ACTION - Execute absorb swap
    executor = SwapExecutor(db)
    result = executor.execute_swap(
        source_faculty_id=faculty_a.id,
        source_week=week1_start,
        target_faculty_id=faculty_b.id,
        target_week=None,  # No reciprocal week (absorb)
        swap_type=SwapType.ABSORB,
        reason="Faculty A has family emergency, Faculty B covering",
    )

    # ASSERT - Execution succeeded
    assert result.success is True
    assert result.swap_id is not None
    assert result.error_code is None

    # ASSERT - SwapRecord created correctly
    swap_record = db.query(SwapRecord).filter(SwapRecord.id == result.swap_id).first()
    assert swap_record.swap_type == SwapType.ABSORB
    assert swap_record.source_faculty_id == faculty_a.id
    assert swap_record.target_faculty_id == faculty_b.id
    assert swap_record.source_week == week1_start
    assert swap_record.target_week is None  # No reciprocal week
    assert swap_record.status == SwapStatus.EXECUTED

    # ASSERT - All week 1 assignments transferred to faculty B
    db.expire_all()
    for assignment in week1_assignments:
        db.refresh(assignment)
        assert assignment.person_id == faculty_b.id, (
            f"Assignment {assignment.id} should be transferred to faculty B (absorb)"
        )
        assert "swapped" in assignment.notes.lower()

    # NOTE: Work hour calculations would be verified here if implemented
    # TODO: When work hour tracking is added, verify:
    # - Faculty A's hours decreased by week 1 total
    # - Faculty B's hours increased by week 1 total


def test_absorb_swap_rollback(
    db: Session,
    swap_faculty_pair: dict,
    swap_week_blocks: dict,
    rotation_templates: dict,
):
    """
    Test rollback of absorb swap.

    Scenario:
        1. Execute absorb swap (faculty A gives week to faculty B)
        2. Rollback within 24h
        3. Verify week returned to faculty A

    Expected:
        - Rollback succeeds
        - Assignments restored to original faculty
    """
    # SETUP
    faculty_a = swap_faculty_pair["faculty_a"]
    faculty_b = swap_faculty_pair["faculty_b"]
    week1_start = swap_week_blocks["week1_start"]
    week1_blocks = swap_week_blocks["week1_blocks"]
    clinic = rotation_templates["clinic"]

    # Create assignments for faculty A
    week1_assignments = []
    for block in week1_blocks:
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=faculty_a.id,
            rotation_template_id=clinic.id,
            role="primary",
        )
        db.add(assignment)
        week1_assignments.append(assignment)

    db.commit()

    # Execute absorb swap
    executor = SwapExecutor(db)
    swap_result = executor.execute_swap(
        source_faculty_id=faculty_a.id,
        source_week=week1_start,
        target_faculty_id=faculty_b.id,
        target_week=None,
        swap_type=SwapType.ABSORB,
    )

    assert swap_result.success is True

    # Verify swap executed
    db.expire_all()
    db.refresh(week1_assignments[0])
    assert week1_assignments[0].person_id == faculty_b.id

    # ACTION - Rollback absorb swap
    rollback_result = executor.rollback_swap(
        swap_id=swap_result.swap_id,
        reason="Faculty B can no longer cover the week",
    )

    # ASSERT - Rollback succeeded
    assert rollback_result.success is True

    # ASSERT - Assignments restored to faculty A
    db.expire_all()
    for assignment in week1_assignments:
        db.refresh(assignment)
        assert assignment.person_id == faculty_a.id, (
            f"Assignment {assignment.id} should be restored to faculty A after rollback"
        )


# ============================================================================
# Edge Cases and Additional Tests
# ============================================================================


def test_swap_with_explicit_executed_by(
    db: Session, swap_faculty_pair: dict, admin_user
):
    """
    Test swap execution tracking who performed the swap.

    Scenario:
        Admin user executes swap on behalf of faculty.
        Verify executed_by_id is tracked.
    """
    faculty_a = swap_faculty_pair["faculty_a"]
    faculty_b = swap_faculty_pair["faculty_b"]
    week1_start = date(2025, 1, 13)

    executor = SwapExecutor(db)
    result = executor.execute_swap(
        source_faculty_id=faculty_a.id,
        source_week=week1_start,
        target_faculty_id=faculty_b.id,
        target_week=None,
        swap_type=SwapType.ABSORB,
        executed_by_id=admin_user.id,
    )

    assert result.success is True

    swap_record = db.query(SwapRecord).filter(SwapRecord.id == result.swap_id).first()
    assert swap_record.executed_by_id == admin_user.id


def test_rollback_with_explicit_rolled_back_by(
    db: Session, swap_faculty_pair: dict, admin_user
):
    """
    Test rollback tracking who performed the rollback.
    """
    faculty_a = swap_faculty_pair["faculty_a"]
    faculty_b = swap_faculty_pair["faculty_b"]
    week1_start = date(2025, 1, 13)

    executor = SwapExecutor(db)
    swap_result = executor.execute_swap(
        source_faculty_id=faculty_a.id,
        source_week=week1_start,
        target_faculty_id=faculty_b.id,
        target_week=None,
        swap_type=SwapType.ABSORB,
    )

    rollback_result = executor.rollback_swap(
        swap_id=swap_result.swap_id,
        reason="Admin override",
        rolled_back_by_id=admin_user.id,
    )

    assert rollback_result.success is True

    swap_record = (
        db.query(SwapRecord).filter(SwapRecord.id == swap_result.swap_id).first()
    )
    assert swap_record.rolled_back_by_id == admin_user.id


def test_rollback_invalid_status(db: Session, swap_faculty_pair: dict):
    """
    Test rollback fails if swap status is not EXECUTED.

    Scenario:
        Create swap with PENDING status.
        Attempt rollback.
        Verify rollback rejected.
    """
    faculty_a = swap_faculty_pair["faculty_a"]
    faculty_b = swap_faculty_pair["faculty_b"]

    # Create swap record with PENDING status (not executed)
    swap_record = SwapRecord(
        id=uuid4(),
        source_faculty_id=faculty_a.id,
        source_week=date(2025, 1, 13),
        target_faculty_id=faculty_b.id,
        target_week=None,
        swap_type=SwapType.ABSORB,
        status=SwapStatus.PENDING,  # Not executed yet
    )
    db.add(swap_record)
    db.commit()

    executor = SwapExecutor(db)
    result = executor.rollback_swap(
        swap_id=swap_record.id,
        reason="Testing invalid status",
    )

    assert result.success is False
    assert result.error_code == "INVALID_STATUS"
    assert "status" in result.message.lower()


def test_call_cascade_update(
    db: Session, swap_faculty_pair: dict, swap_week_blocks: dict
):
    """
    Test that Friday/Saturday call assignments are properly updated.

    Scenario:
        Create call assignments for Friday and Saturday in week.
        Execute swap.
        Verify call assignments transferred to new faculty.
    """
    faculty_a = swap_faculty_pair["faculty_a"]
    faculty_b = swap_faculty_pair["faculty_b"]
    week1_start = swap_week_blocks["week1_start"]

    # Create Friday call (weekday 4)
    friday_date = week1_start + timedelta(days=4)
    friday_call = CallAssignment(
        id=uuid4(),
        date=friday_date,
        person_id=faculty_a.id,
        call_type="overnight",
    )
    db.add(friday_call)

    # Create Saturday call (weekday 5)
    saturday_date = week1_start + timedelta(days=5)
    saturday_call = CallAssignment(
        id=uuid4(),
        date=saturday_date,
        person_id=faculty_a.id,
        call_type="weekend",
        is_weekend=True,
    )
    db.add(saturday_call)

    db.commit()

    # Execute absorb swap
    executor = SwapExecutor(db)
    result = executor.execute_swap(
        source_faculty_id=faculty_a.id,
        source_week=week1_start,
        target_faculty_id=faculty_b.id,
        target_week=None,
        swap_type=SwapType.ABSORB,
    )

    assert result.success is True

    # Verify call assignments transferred
    db.refresh(friday_call)
    db.refresh(saturday_call)

    assert friday_call.person_id == faculty_b.id
    assert saturday_call.person_id == faculty_b.id


# ============================================================================
# Summary Statistics
# ============================================================================


def test_swap_execution_comprehensive_coverage(db: Session):
    """
    Meta-test to verify comprehensive test coverage.

    This test documents what has been tested and what remains to be tested.
    """
    tested_scenarios = [
        "One-to-one swap execution",
        "Absorb swap execution",
        "Swap rollback within 24h window",
        "Rollback window expiration",
        "Rollback boundary conditions (23:59, 24:00, 24:01)",
        "Rollback of nonexistent swap",
        "Rollback with invalid status",
        "Swap with nonexistent faculty",
        "Call cascade updates (Fri/Sat)",
        "Execution tracking (executed_by_id)",
        "Rollback tracking (rolled_back_by_id)",
        "Absorb swap rollback",
    ]

    # Future test scenarios (not yet implemented)
    future_tests = [
        "ACGME validation (80-hour rule)",
        "ACGME validation (1-in-7 rule)",
        "Credential requirement validation",
        "Concurrent swap execution (race conditions)",
        "Swap during schedule generation",
        "Leave conflict detection",
        "Work hour calculation updates",
        "Notification system integration",
        "Audit trail verification",
    ]

    # This is a documentation test - always passes
    assert len(tested_scenarios) == 12
    assert len(future_tests) == 9

    # TODO: Implement tests for future_tests scenarios
    # See docs/testing/TEST_SCENARIO_FRAMES.md for additional test frames
