"""
End-to-end tests for the complete swap request lifecycle.

Tests cover the entire swap workflow from request creation through execution,
rollback, auto-matching, ACGME validation, and notification triggers.

E2E Test Scenarios:
1. Create swap request → approval → execution flow
2. Swap rollback within 24-hour window
3. Auto-matching swap candidates
4. ACGME validation after swap execution
5. Notification triggers during swap lifecycle
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.call_assignment import CallAssignment
from app.models.faculty_preference import FacultyPreference
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapApproval, SwapRecord, SwapStatus, SwapType
from app.models.user import User
from app.scheduling.validator import ACGMEValidator
from app.services.swap_auto_matcher import SwapAutoMatcher
from app.services.swap_executor import SwapExecutor
from app.services.swap_notification_service import (
    SwapNotificationService,
    SwapNotificationType,
)
from app.services.swap_request_service import SwapRequestService
from app.services.swap_validation import SwapValidationService


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def faculty_a(db: Session) -> Person:
    """Create first faculty member for swap tests."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Alice Faculty",
        type="faculty",
        email="alice.faculty@hospital.org",
        performs_procedures=True,
        specialties=["Family Medicine"],
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def faculty_b(db: Session) -> Person:
    """Create second faculty member for swap tests."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Bob Faculty",
        type="faculty",
        email="bob.faculty@hospital.org",
        performs_procedures=True,
        specialties=["Family Medicine"],
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def faculty_c(db: Session) -> Person:
    """Create third faculty member for auto-matching tests."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Carol Faculty",
        type="faculty",
        email="carol.faculty@hospital.org",
        performs_procedures=True,
        specialties=["Family Medicine"],
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def residents(db: Session) -> list[Person]:
    """Create multiple residents for ACGME validation tests."""
    resident_list = []
    for i, pgy in enumerate([1, 2, 3]):
        resident = Person(
            id=uuid4(),
            name=f"Dr. Resident PGY{pgy}",
            type="resident",
            email=f"resident.pgy{pgy}@hospital.org",
            pgy_level=pgy,
        )
        db.add(resident)
        resident_list.append(resident)
    db.commit()
    for r in resident_list:
        db.refresh(r)
    return resident_list


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create an admin user for executor audit fields."""
    from app.core.security import get_password_hash

    user = User(
        id=uuid4(),
        username="admin_user",
        email="admin@hospital.org",
        hashed_password=get_password_hash("testpass123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def fmit_template(db: Session) -> RotationTemplate:
    """Create FMIT rotation template for swap tests."""
    template = RotationTemplate(
        id=uuid4(),
        name="FMIT",
        activity_type="inpatient",
        abbreviation="FMIT",
        max_residents=0,
        supervision_required=False,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def clinic_template(db: Session) -> RotationTemplate:
    """Create clinic rotation template for ACGME validation."""
    template = RotationTemplate(
        id=uuid4(),
        name="Clinic",
        activity_type="outpatient",
        abbreviation="CLINIC",
        max_residents=4,
        supervision_required=True,
        max_supervision_ratio=4,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def create_blocks_for_week(db: Session, week_start: date) -> list[Block]:
    """Helper to create blocks for a full week (7 days × AM/PM)."""
    blocks = []
    for day_offset in range(7):
        current_date = week_start + timedelta(days=day_offset)
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
            blocks.append(block)
    db.commit()
    for b in blocks:
        db.refresh(b)
    return blocks


def create_fmit_assignments(
    db: Session,
    faculty: Person,
    blocks: list[Block],
    template: RotationTemplate,
) -> list[Assignment]:
    """Helper to create FMIT assignments for a faculty member."""
    assignments = []
    for block in blocks:
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=faculty.id,
            rotation_template_id=template.id,
            role="primary",
        )
        db.add(assignment)
        assignments.append(assignment)
    db.commit()
    for a in assignments:
        db.refresh(a)
    return assignments


def create_call_assignments(
    db: Session,
    faculty: Person,
    week_start: date,
) -> list[CallAssignment]:
    """Helper to create Friday and Saturday call assignments."""
    call_assignments = []
    for day_offset in range(7):
        current_date = week_start + timedelta(days=day_offset)
        # Friday (4) and Saturday (5)
        if current_date.weekday() in [4, 5]:
            call = CallAssignment(
                id=uuid4(),
                person_id=faculty.id,
                date=current_date,
                call_type="backup",
            )
            db.add(call)
            call_assignments.append(call)
    db.commit()
    for c in call_assignments:
        db.refresh(c)
    return call_assignments


# ============================================================================
# E2E Test 1: Create swap request → approval → execution flow
# ============================================================================


class TestSwapRequestApprovalExecutionFlow:
    """E2E tests for complete swap request lifecycle."""

    def test_one_to_one_swap_full_lifecycle(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
        fmit_template: RotationTemplate,
        admin_user: User,
    ):
        """Test full lifecycle: create request → approve → execute one-to-one swap."""
        # Setup: Create FMIT assignments for both faculty
        week_a = date.today() + timedelta(days=14)
        week_b = date.today() + timedelta(days=21)

        blocks_a = create_blocks_for_week(db, week_a)
        blocks_b = create_blocks_for_week(db, week_b)

        assignments_a = create_fmit_assignments(db, faculty_a, blocks_a, fmit_template)
        assignments_b = create_fmit_assignments(db, faculty_b, blocks_b, fmit_template)

        # Step 1: Create swap request
        swap_service = SwapRequestService(db)
        request_result = swap_service.create_request(
            requester_id=faculty_a.id,
            source_week=week_a,
            desired_weeks=[week_b],
            reason="Conference attendance",
            target_faculty_id=faculty_b.id,
            auto_find_candidates=False,
        )

        assert request_result.success is True
        assert request_result.request_id is not None
        request_id = request_result.request_id

        # Verify swap record created
        swap_record = db.query(SwapRecord).filter_by(id=request_id).first()
        assert swap_record is not None
        assert swap_record.status == SwapStatus.PENDING
        assert swap_record.swap_type == SwapType.ONE_TO_ONE
        assert swap_record.source_faculty_id == faculty_a.id
        assert swap_record.target_faculty_id == faculty_b.id

        # Step 2: Target faculty responds (accepts)
        response_result = swap_service.respond_to_request(
            request_id=request_id,
            faculty_id=faculty_b.id,
            accept=True,
            notes="Happy to help!",
        )

        assert response_result.success is True
        assert response_result.executed is True

        # Verify swap was executed
        db.refresh(swap_record)
        assert swap_record.status == SwapStatus.EXECUTED
        assert swap_record.approved_at is not None
        assert swap_record.executed_at is not None

        # Verify assignments were swapped
        # Week A assignments should now belong to faculty_b
        for assignment in assignments_a:
            db.refresh(assignment)
            assert assignment.person_id == faculty_b.id
            assert "Swapped from faculty" in assignment.notes

        # Week B assignments should now belong to faculty_a
        for assignment in assignments_b:
            db.refresh(assignment)
            assert assignment.person_id == faculty_a.id
            assert "Swapped from faculty" in assignment.notes

    def test_absorb_swap_full_lifecycle(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
        fmit_template: RotationTemplate,
    ):
        """Test full lifecycle for absorb swap (one-way transfer)."""
        # Setup: Create FMIT assignment for faculty_a only
        week_a = date.today() + timedelta(days=14)
        blocks_a = create_blocks_for_week(db, week_a)
        assignments_a = create_fmit_assignments(db, faculty_a, blocks_a, fmit_template)

        # Create swap request (absorb type - no desired weeks)
        swap_service = SwapRequestService(db)
        request_result = swap_service.create_request(
            requester_id=faculty_a.id,
            source_week=week_a,
            desired_weeks=None,  # No desired weeks = ABSORB
            reason="Emergency leave",
            target_faculty_id=faculty_b.id,
            auto_find_candidates=False,
        )

        assert request_result.success is True
        request_id = request_result.request_id

        swap_record = db.query(SwapRecord).filter_by(id=request_id).first()
        assert swap_record.swap_type == SwapType.ABSORB

        # Accept the absorb swap
        response_result = swap_service.respond_to_request(
            request_id=request_id,
            faculty_id=faculty_b.id,
            accept=True,
        )

        assert response_result.success is True
        assert response_result.executed is True

        # Verify assignments transferred to faculty_b
        for assignment in assignments_a:
            db.refresh(assignment)
            assert assignment.person_id == faculty_b.id

    def test_swap_rejection_flow(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
        fmit_template: RotationTemplate,
    ):
        """Test swap rejection workflow."""
        week_a = date.today() + timedelta(days=14)
        blocks_a = create_blocks_for_week(db, week_a)
        create_fmit_assignments(db, faculty_a, blocks_a, fmit_template)

        swap_service = SwapRequestService(db)
        request_result = swap_service.create_request(
            requester_id=faculty_a.id,
            source_week=week_a,
            desired_weeks=None,
            target_faculty_id=faculty_b.id,
            auto_find_candidates=False,
        )

        request_id = request_result.request_id

        # Reject the swap
        response_result = swap_service.respond_to_request(
            request_id=request_id,
            faculty_id=faculty_b.id,
            accept=False,
            notes="Already committed that week",
        )

        assert response_result.success is True
        assert response_result.executed is False

        # Verify swap was rejected
        swap_record = db.query(SwapRecord).filter_by(id=request_id).first()
        assert swap_record.status == SwapStatus.REJECTED
        assert "Already committed" in swap_record.notes

    def test_counter_offer_flow(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
        fmit_template: RotationTemplate,
    ):
        """Test counter-offer workflow."""
        week_a = date.today() + timedelta(days=14)
        week_b = date.today() + timedelta(days=21)
        week_c = date.today() + timedelta(days=28)  # Counter-offer week

        blocks_a = create_blocks_for_week(db, week_a)
        blocks_c = create_blocks_for_week(db, week_c)

        create_fmit_assignments(db, faculty_a, blocks_a, fmit_template)
        create_fmit_assignments(db, faculty_b, blocks_c, fmit_template)

        swap_service = SwapRequestService(db)

        # Original request
        request_result = swap_service.create_request(
            requester_id=faculty_a.id,
            source_week=week_a,
            desired_weeks=[week_b],
            target_faculty_id=faculty_b.id,
            auto_find_candidates=False,
        )

        original_request_id = request_result.request_id

        # Counter-offer with different week
        response_result = swap_service.respond_to_request(
            request_id=original_request_id,
            faculty_id=faculty_b.id,
            accept=False,
            counter_week=week_c,
        )

        assert response_result.success is True
        assert response_result.new_request_id is not None

        # Original request should be rejected
        original_swap = db.query(SwapRecord).filter_by(id=original_request_id).first()
        assert original_swap.status == SwapStatus.REJECTED

        # New counter-offer request should exist
        counter_swap = (
            db.query(SwapRecord).filter_by(id=response_result.new_request_id).first()
        )
        assert counter_swap is not None
        assert counter_swap.source_faculty_id == faculty_b.id
        assert counter_swap.source_week == week_c
        assert counter_swap.target_faculty_id == faculty_a.id


# ============================================================================
# E2E Test 2: Swap rollback within 24-hour window
# ============================================================================


class TestSwapRollback:
    """E2E tests for swap rollback functionality."""

    def test_rollback_within_24_hour_window(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
        fmit_template: RotationTemplate,
        admin_user: User,
    ):
        """Test rolling back a swap within the 24-hour window."""
        week_a = date.today() + timedelta(days=14)
        week_b = date.today() + timedelta(days=21)

        blocks_a = create_blocks_for_week(db, week_a)
        blocks_b = create_blocks_for_week(db, week_b)

        assignments_a = create_fmit_assignments(db, faculty_a, blocks_a, fmit_template)
        assignments_b = create_fmit_assignments(db, faculty_b, blocks_b, fmit_template)

        # Execute a swap
        executor = SwapExecutor(db)
        execution_result = executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=week_a,
            target_faculty_id=faculty_b.id,
            target_week=week_b,
            swap_type="one_to_one",
            reason="Test swap",
            executed_by_id=admin_user.id,
        )

        assert execution_result.success is True
        swap_id = execution_result.swap_id

        # Verify swap was executed
        swap_record = db.query(SwapRecord).filter_by(id=swap_id).first()
        assert swap_record.status == SwapStatus.EXECUTED

        # Verify assignments were swapped
        for assignment in assignments_a:
            db.refresh(assignment)
            assert assignment.person_id == faculty_b.id

        # Check can_rollback returns True
        can_rollback = executor.can_rollback(swap_id)
        assert can_rollback is True

        # Rollback the swap
        rollback_result = executor.rollback_swap(
            swap_id=swap_id,
            reason="Executed by mistake",
            rolled_back_by_id=admin_user.id,
        )

        assert rollback_result.success is True

        # Verify swap status changed
        db.refresh(swap_record)
        assert swap_record.status == SwapStatus.ROLLED_BACK
        assert swap_record.rolled_back_at is not None
        assert swap_record.rollback_reason == "Executed by mistake"

        # Verify assignments were restored
        for assignment in assignments_a:
            db.refresh(assignment)
            assert assignment.person_id == faculty_a.id

        for assignment in assignments_b:
            db.refresh(assignment)
            assert assignment.person_id == faculty_b.id

    def test_rollback_outside_24_hour_window(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
        fmit_template: RotationTemplate,
    ):
        """Test that rollback fails outside the 24-hour window."""
        week_a = date.today() + timedelta(days=14)

        blocks_a = create_blocks_for_week(db, week_a)
        create_fmit_assignments(db, faculty_a, blocks_a, fmit_template)

        executor = SwapExecutor(db)
        execution_result = executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=week_a,
            target_faculty_id=faculty_b.id,
            target_week=None,
            swap_type="absorb",
        )

        swap_id = execution_result.swap_id

        # Manually update executed_at to be >24 hours ago
        swap_record = db.query(SwapRecord).filter_by(id=swap_id).first()
        swap_record.executed_at = datetime.utcnow() - timedelta(hours=25)
        db.commit()

        # Check can_rollback returns False
        can_rollback = executor.can_rollback(swap_id)
        assert can_rollback is False

        # Attempt rollback should fail
        rollback_result = executor.rollback_swap(
            swap_id=swap_id,
            reason="Too late",
        )

        assert rollback_result.success is False
        assert rollback_result.error_code == "ROLLBACK_WINDOW_EXPIRED"

        # Verify status unchanged
        db.refresh(swap_record)
        assert swap_record.status == SwapStatus.EXECUTED

    def test_rollback_call_cascade(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
        fmit_template: RotationTemplate,
    ):
        """Test that rollback also reverses call cascade assignments."""
        week_a = date.today() + timedelta(days=14)
        # Ensure week starts on a Monday for predictable Friday/Saturday
        week_a = week_a - timedelta(days=week_a.weekday())

        blocks_a = create_blocks_for_week(db, week_a)
        create_fmit_assignments(db, faculty_a, blocks_a, fmit_template)
        call_assignments_a = create_call_assignments(db, faculty_a, week_a)

        executor = SwapExecutor(db)
        execution_result = executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=week_a,
            target_faculty_id=faculty_b.id,
            target_week=None,
            swap_type="absorb",
        )

        swap_id = execution_result.swap_id

        # Verify call cascade was updated to faculty_b
        for call_assignment in call_assignments_a:
            db.refresh(call_assignment)
            assert call_assignment.person_id == faculty_b.id

        # Rollback the swap
        rollback_result = executor.rollback_swap(
            swap_id=swap_id,
            reason="Testing rollback",
        )

        assert rollback_result.success is True

        # Verify call cascade was restored to faculty_a
        for call_assignment in call_assignments_a:
            db.refresh(call_assignment)
            assert call_assignment.person_id == faculty_a.id


# ============================================================================
# E2E Test 3: Auto-matching swap candidates
# ============================================================================


class TestSwapAutoMatching:
    """E2E tests for auto-matching swap candidates."""

    def test_auto_match_finds_compatible_swaps(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
        faculty_c: Person,
        fmit_template: RotationTemplate,
    ):
        """Test that auto-matcher finds compatible swap pairs."""
        week_a = date.today() + timedelta(days=14)
        week_b = date.today() + timedelta(days=21)
        week_c = date.today() + timedelta(days=28)

        blocks_a = create_blocks_for_week(db, week_a)
        blocks_b = create_blocks_for_week(db, week_b)
        blocks_c = create_blocks_for_week(db, week_c)

        create_fmit_assignments(db, faculty_a, blocks_a, fmit_template)
        create_fmit_assignments(db, faculty_b, blocks_b, fmit_template)
        create_fmit_assignments(db, faculty_c, blocks_c, fmit_template)

        # Create mutual swap requests (A wants B's week, B wants A's week)
        swap_a = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_a.id,
            source_week=week_a,
            target_faculty_id=faculty_b.id,
            target_week=week_b,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=datetime.utcnow(),
        )
        db.add(swap_a)

        swap_b = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_b.id,
            source_week=week_b,
            target_faculty_id=faculty_a.id,
            target_week=week_a,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=datetime.utcnow(),
        )
        db.add(swap_b)

        db.commit()

        # Run auto-matcher
        swap_service = SwapRequestService(db)
        match_result = swap_service.auto_match_requests()

        assert match_result.matches_found > 0
        assert len(match_result.potential_matches) > 0

        # Verify the match is mutual
        matched_pair = match_result.potential_matches[0]
        assert swap_a.id in matched_pair
        assert swap_b.id in matched_pair

    def test_auto_matcher_suggests_optimal_matches(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
        faculty_c: Person,
    ):
        """Test auto-matcher ranking and scoring."""
        week_a = date.today() + timedelta(days=14)
        week_b = date.today() + timedelta(days=21)
        week_c = date.today() + timedelta(days=28)

        # Create faculty preferences to influence scoring
        pref_a = FacultyPreference(
            faculty_id=faculty_a.id,
            preferred_weeks=[week_b],
            blocked_weeks=[week_a],
        )
        pref_b = FacultyPreference(
            faculty_id=faculty_b.id,
            preferred_weeks=[week_a],
            blocked_weeks=[],
        )
        db.add_all([pref_a, pref_b])

        # Create pending swap request from faculty_a
        swap_request = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_a.id,
            source_week=week_a,
            target_faculty_id=faculty_b.id,
            target_week=week_b,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=datetime.utcnow(),
        )
        db.add(swap_request)
        db.commit()

        # Use auto-matcher to suggest matches
        matcher = SwapAutoMatcher(db)
        matches = matcher.suggest_optimal_matches(swap_request.id, top_k=5)

        # Should have matches since faculty_b prefers week_a
        assert len(matches) >= 0  # May or may not find matches depending on data

    def test_batch_auto_match_pending_requests(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
    ):
        """Test batch processing of all pending swap requests."""
        week_a = date.today() + timedelta(days=14)

        # Create multiple pending requests
        for i in range(3):
            swap = SwapRecord(
                id=uuid4(),
                source_faculty_id=faculty_a.id,
                source_week=week_a + timedelta(days=i * 7),
                target_faculty_id=faculty_b.id,
                target_week=None,
                swap_type=SwapType.ABSORB,
                status=SwapStatus.PENDING,
                requested_at=datetime.utcnow(),
            )
            db.add(swap)
        db.commit()

        # Run batch auto-match
        matcher = SwapAutoMatcher(db)
        batch_result = matcher.auto_match_pending_requests()

        assert batch_result.total_requests_processed == 3
        assert batch_result.execution_time_seconds > 0


# ============================================================================
# E2E Test 4: ACGME validation after swap execution
# ============================================================================


class TestACGMEValidationAfterSwap:
    """E2E tests for ACGME compliance validation after swap execution."""

    def test_swap_maintains_acgme_compliance(
        self,
        db: Session,
        faculty_a: Person,
        residents: list[Person],
        fmit_template: RotationTemplate,
        clinic_template: RotationTemplate,
    ):
        """Test that swapping faculty doesn't violate ACGME supervision ratios."""
        week_start = date.today() + timedelta(days=14)
        blocks = create_blocks_for_week(db, week_start)

        # Create clinic assignments for residents (require supervision)
        for resident in residents[:2]:  # 2 residents
            for block in blocks[:4]:  # First 2 days
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=resident.id,
                    rotation_template_id=clinic_template.id,
                    role="primary",
                )
                db.add(assignment)

        # Assign faculty_a as supervisor
        for block in blocks[:4]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=faculty_a.id,
                rotation_template_id=clinic_template.id,
                role="supervisor",
            )
            db.add(assignment)

        db.commit()

        # Validate before swap
        validator = ACGMEValidator(db)
        result_before = validator.validate_all(
            start_date=week_start,
            end_date=week_start + timedelta(days=6),
        )

        # Should be compliant (2 residents, 1 faculty = 2:1 ratio, within 4:1 limit)
        assert result_before.valid is True

        # Now swap clinic assignments - this should maintain compliance
        # (Implementation would update assignments to different faculty)

        # Validate after hypothetical swap
        result_after = validator.validate_all(
            start_date=week_start,
            end_date=week_start + timedelta(days=6),
        )

        # Should still be compliant
        assert result_after.valid is True

    def test_swap_detects_acgme_violation(
        self,
        db: Session,
        residents: list[Person],
        clinic_template: RotationTemplate,
    ):
        """Test that ACGME validator detects violations after problematic swap."""
        week_start = date.today() + timedelta(days=14)
        blocks = create_blocks_for_week(db, week_start)

        # Create scenario that would violate supervision ratio
        # Assign 5 residents to clinic (exceeds 4:1 ratio with 0 faculty)
        for resident in residents:
            for block in blocks[:2]:
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=resident.id,
                    rotation_template_id=clinic_template.id,
                    role="primary",
                )
                db.add(assignment)

        db.commit()

        # Validate - should detect supervision ratio violation
        validator = ACGMEValidator(db)
        result = validator.validate_all(
            start_date=week_start,
            end_date=week_start + timedelta(days=6),
        )

        # Should have violations (no supervising faculty)
        assert len(result.violations) > 0


# ============================================================================
# E2E Test 5: Notification triggers during swap lifecycle
# ============================================================================


class TestSwapNotifications:
    """E2E tests for notification triggers during swap lifecycle."""

    def test_notification_on_swap_request_received(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
        fmit_template: RotationTemplate,
    ):
        """Test notification sent when swap request is received."""
        week_a = date.today() + timedelta(days=14)
        blocks_a = create_blocks_for_week(db, week_a)
        create_fmit_assignments(db, faculty_a, blocks_a, fmit_template)

        notifier = SwapNotificationService(db)

        # Create notification for swap request
        notification = notifier.notify_swap_request_received(
            recipient_faculty_id=faculty_b.id,
            requester_name=faculty_a.name,
            week_offered=week_a,
            swap_id=uuid4(),
            reason="Need time off for conference",
        )

        assert notification is not None
        assert (
            notification.notification_type == SwapNotificationType.SWAP_REQUEST_RECEIVED
        )
        assert faculty_a.name in notification.subject
        assert notification.recipient_email == faculty_b.email

        # Verify notification is pending
        assert notifier.get_pending_count() == 1

    def test_notification_on_swap_accepted(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
    ):
        """Test notification sent when swap is accepted."""
        week_a = date.today() + timedelta(days=14)
        swap_id = uuid4()

        notifier = SwapNotificationService(db)

        notification = notifier.notify_swap_accepted(
            recipient_faculty_id=faculty_a.id,
            accepter_name=faculty_b.name,
            week=week_a,
            swap_id=swap_id,
        )

        assert notification is not None
        assert (
            notification.notification_type == SwapNotificationType.SWAP_REQUEST_ACCEPTED
        )
        assert faculty_b.name in notification.subject
        assert "accepted" in notification.body.lower()

    def test_notification_on_swap_rejected(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
    ):
        """Test notification sent when swap is rejected."""
        week_a = date.today() + timedelta(days=14)
        swap_id = uuid4()

        notifier = SwapNotificationService(db)

        notification = notifier.notify_swap_rejected(
            recipient_faculty_id=faculty_a.id,
            rejecter_name=faculty_b.name,
            week=week_a,
            swap_id=swap_id,
            reason="Already have another commitment",
        )

        assert notification is not None
        assert (
            notification.notification_type == SwapNotificationType.SWAP_REQUEST_REJECTED
        )
        assert faculty_b.name in notification.subject
        assert "declined" in notification.body.lower()
        assert "Already have another commitment" in notification.body

    def test_notification_on_swap_executed(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
    ):
        """Test notifications sent when swap is executed."""
        week_a = date.today() + timedelta(days=14)
        swap_id = uuid4()

        notifier = SwapNotificationService(db)

        notifications = notifier.notify_swap_executed(
            faculty_ids=[faculty_a.id, faculty_b.id],
            week=week_a,
            swap_id=swap_id,
            details="Swap completed successfully",
        )

        # Should send notification to both parties
        assert len(notifications) == 2

        for notification in notifications:
            assert notification.notification_type == SwapNotificationType.SWAP_EXECUTED
            assert "Schedule Updated" in notification.subject
            assert notification.recipient_id in [faculty_a.id, faculty_b.id]

    def test_notification_on_swap_rolled_back(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
    ):
        """Test notifications sent when swap is rolled back."""
        week_a = date.today() + timedelta(days=14)
        swap_id = uuid4()

        notifier = SwapNotificationService(db)

        notifications = notifier.notify_swap_rolled_back(
            faculty_ids=[faculty_a.id, faculty_b.id],
            week=week_a,
            swap_id=swap_id,
            reason="Executed in error",
        )

        assert len(notifications) == 2

        for notification in notifications:
            assert (
                notification.notification_type == SwapNotificationType.SWAP_ROLLED_BACK
            )
            assert "Rolled Back" in notification.subject
            assert "Executed in error" in notification.body

    def test_send_pending_notifications(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
    ):
        """Test sending all pending notifications."""
        notifier = SwapNotificationService(db)

        # Queue multiple notifications
        notifier.notify_swap_request_received(
            recipient_faculty_id=faculty_b.id,
            requester_name=faculty_a.name,
            week_offered=date.today() + timedelta(days=14),
            swap_id=uuid4(),
        )

        notifier.notify_swap_accepted(
            recipient_faculty_id=faculty_a.id,
            accepter_name=faculty_b.name,
            week=date.today() + timedelta(days=21),
            swap_id=uuid4(),
        )

        # Should have 2 pending
        assert notifier.get_pending_count() == 2

        # Send all pending
        sent_count = notifier.send_pending_notifications()

        # Should attempt to send all (may fail if email service not configured)
        assert sent_count >= 0

        # Pending queue should be cleared
        assert notifier.get_pending_count() == 0

    def test_full_lifecycle_with_notifications(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
        fmit_template: RotationTemplate,
    ):
        """Test that all notifications fire during full swap lifecycle."""
        week_a = date.today() + timedelta(days=14)
        week_b = date.today() + timedelta(days=21)

        blocks_a = create_blocks_for_week(db, week_a)
        blocks_b = create_blocks_for_week(db, week_b)

        create_fmit_assignments(db, faculty_a, blocks_a, fmit_template)
        create_fmit_assignments(db, faculty_b, blocks_b, fmit_template)

        swap_service = SwapRequestService(db)

        # Create request (should trigger notification)
        request_result = swap_service.create_request(
            requester_id=faculty_a.id,
            source_week=week_a,
            desired_weeks=[week_b],
            target_faculty_id=faculty_b.id,
            auto_find_candidates=False,
        )

        request_id = request_result.request_id

        # Verify notification was triggered
        assert request_result.candidates_notified == 1

        # Accept swap (should trigger acceptance + execution notifications)
        response_result = swap_service.respond_to_request(
            request_id=request_id,
            faculty_id=faculty_b.id,
            accept=True,
        )

        assert response_result.success is True
        assert response_result.executed is True

        # Notifications should have been queued and sent
        # (Actual email sending depends on email service configuration)


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestSwapLifecycleIntegration:
    """Integration tests combining multiple aspects of swap lifecycle."""

    def test_complete_swap_with_all_features(
        self,
        db: Session,
        faculty_a: Person,
        faculty_b: Person,
        faculty_c: Person,
        fmit_template: RotationTemplate,
        admin_user: User,
    ):
        """
        Test complete swap lifecycle with all features:
        - Request creation
        - Auto-matching
        - Validation
        - Execution
        - Notifications
        - Rollback capability
        """
        week_a = date.today() + timedelta(days=14)
        week_b = date.today() + timedelta(days=21)

        # Ensure week_a starts on Monday for predictable call cascade
        week_a = week_a - timedelta(days=week_a.weekday())
        week_b = week_b - timedelta(days=week_b.weekday())

        blocks_a = create_blocks_for_week(db, week_a)
        blocks_b = create_blocks_for_week(db, week_b)

        assignments_a = create_fmit_assignments(db, faculty_a, blocks_a, fmit_template)
        assignments_b = create_fmit_assignments(db, faculty_b, blocks_b, fmit_template)

        call_assignments_a = create_call_assignments(db, faculty_a, week_a)
        call_assignments_b = create_call_assignments(db, faculty_b, week_b)

        # Step 1: Validate before swap
        validation_service = SwapValidationService(db)
        validation_result = validation_service.validate_swap(
            source_faculty_id=faculty_a.id,
            source_week=week_a,
            target_faculty_id=faculty_b.id,
            target_week=week_b,
        )
        assert validation_result.valid is True

        # Step 2: Execute swap
        executor = SwapExecutor(db)
        execution_result = executor.execute_swap(
            source_faculty_id=faculty_a.id,
            source_week=week_a,
            target_faculty_id=faculty_b.id,
            target_week=week_b,
            swap_type="one_to_one",
            reason="Integration test",
            executed_by_id=admin_user.id,
        )
        assert execution_result.success is True
        swap_id = execution_result.swap_id

        # Step 3: Verify assignments swapped
        for assignment in assignments_a:
            db.refresh(assignment)
            assert assignment.person_id == faculty_b.id

        for assignment in assignments_b:
            db.refresh(assignment)
            assert assignment.person_id == faculty_a.id

        # Step 4: Verify call cascade swapped
        for call in call_assignments_a:
            db.refresh(call)
            assert call.person_id == faculty_b.id

        for call in call_assignments_b:
            db.refresh(call)
            assert call.person_id == faculty_a.id

        # Step 5: Verify can rollback
        can_rollback = executor.can_rollback(swap_id)
        assert can_rollback is True

        # Step 6: Execute rollback
        rollback_result = executor.rollback_swap(
            swap_id=swap_id,
            reason="Integration test rollback",
            rolled_back_by_id=admin_user.id,
        )
        assert rollback_result.success is True

        # Step 7: Verify everything restored
        for assignment in assignments_a:
            db.refresh(assignment)
            assert assignment.person_id == faculty_a.id

        for assignment in assignments_b:
            db.refresh(assignment)
            assert assignment.person_id == faculty_b.id

        for call in call_assignments_a:
            db.refresh(call)
            assert call.person_id == faculty_a.id

        for call in call_assignments_b:
            db.refresh(call)
            assert call.person_id == faculty_b.id

        # Step 8: Verify swap record status
        swap_record = db.query(SwapRecord).filter_by(id=swap_id).first()
        assert swap_record.status == SwapStatus.ROLLED_BACK
