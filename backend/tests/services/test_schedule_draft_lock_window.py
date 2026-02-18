from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from app.models.person import Person
from app.models.schedule_draft import (
    DraftAssignmentChangeType,
    DraftSourceType,
    ScheduleDraft,
    ScheduleDraftAssignment,
    ScheduleDraftStatus,
)
from app.models.settings import ApplicationSettings
from app.models.user import User
from app.services.schedule_draft_service import ScheduleDraftService


@pytest.mark.asyncio
async def test_publish_blocked_by_lock_window(db):
    lock_date = date.today() + timedelta(days=7)
    settings = ApplicationSettings(schedule_lock_date=lock_date)
    db.add(settings)

    user = User(
        id=uuid4(),
        username="admin_user",
        email="admin@example.com",
        hashed_password="hashed",
        role="admin",
    )
    person = Person(
        id=uuid4(),
        name="Test Resident",
        type="resident",
        email="resident@example.com",
        pgy_level=1,
    )
    db.add_all([user, person])
    db.commit()

    draft = ScheduleDraft(
        id=uuid4(),
        created_at=datetime.utcnow(),
        created_by_id=user.id,
        target_start_date=date.today(),
        target_end_date=date.today(),
        status=ScheduleDraftStatus.DRAFT,
        source_type=DraftSourceType.SOLVER,
        change_summary={"added": 0, "modified": 0, "deleted": 0},
        flags_total=0,
        flags_acknowledged=0,
    )
    db.add(draft)
    db.commit()

    draft_assignment = ScheduleDraftAssignment(
        id=uuid4(),
        draft_id=draft.id,
        person_id=person.id,
        assignment_date=date.today(),
        time_of_day="AM",
        activity_code=None,
        rotation_id=None,
        change_type=DraftAssignmentChangeType.ADD,
        existing_assignment_id=None,
    )
    db.add(draft_assignment)
    db.commit()

    service = ScheduleDraftService(db)
    result = await service.publish_draft(
        draft_id=draft.id,
        published_by_id=user.id,
        override_comment=None,
        validate_acgme=True,
    )

    assert result.success is False
    assert result.error_code == "LOCK_WINDOW_BLOCKED"


@pytest.mark.asyncio
async def test_manual_draft_bypasses_lock_window_breakglass(db):
    """Manual drafts should bypass break-glass gate per policy.

    Coordinators are trusted for manual edits - the break-glass gate
    is intended for automated systems (SOLVER, IMPORT), not human judgment.
    """
    lock_date = date.today() + timedelta(days=7)
    settings = ApplicationSettings(schedule_lock_date=lock_date)
    db.add(settings)

    user = User(
        id=uuid4(),
        username="coordinator",
        email="coord@example.com",
        hashed_password="hashed",
        role="coordinator",
    )
    person = Person(
        id=uuid4(),
        name="Test Resident",
        type="resident",
        email="resident@example.com",
        pgy_level=1,
    )
    db.add_all([user, person])
    db.commit()

    # Key difference: source_type=DraftSourceType.MANUAL
    draft = ScheduleDraft(
        id=uuid4(),
        created_at=datetime.utcnow(),
        created_by_id=user.id,
        target_start_date=date.today(),
        target_end_date=date.today(),
        status=ScheduleDraftStatus.DRAFT,
        source_type=DraftSourceType.MANUAL,
        change_summary={"added": 0, "modified": 0, "deleted": 0},
        flags_total=0,
        flags_acknowledged=0,
    )
    db.add(draft)
    db.commit()

    draft_assignment = ScheduleDraftAssignment(
        id=uuid4(),
        draft_id=draft.id,
        person_id=person.id,
        assignment_date=date.today(),
        time_of_day="AM",
        activity_code=None,
        rotation_id=None,
        change_type=DraftAssignmentChangeType.ADD,
        existing_assignment_id=None,
    )
    db.add(draft_assignment)
    db.commit()

    service = ScheduleDraftService(db)
    result = await service.publish_draft(
        draft_id=draft.id,
        published_by_id=user.id,
        override_comment=None,
        validate_acgme=True,
    )

    # MANUAL drafts should NOT return LOCK_WINDOW_BLOCKED
    assert result.error_code != "LOCK_WINDOW_BLOCKED"


# ============================================================================
# Break-Glass Approval Tests
# ============================================================================


def _create_locked_draft(db, source_type=DraftSourceType.SOLVER):
    """Helper to create a draft with an assignment inside the lock window."""
    lock_date = date.today() + timedelta(days=7)
    settings = db.query(ApplicationSettings).first()
    if not settings:
        settings = ApplicationSettings(schedule_lock_date=lock_date)
        db.add(settings)
    else:
        settings.schedule_lock_date = lock_date

    user = User(
        id=uuid4(),
        username=f"user_{uuid4().hex[:8]}",
        email=f"{uuid4().hex[:8]}@example.com",
        hashed_password="hashed",
        role="coordinator",
    )
    person = Person(
        id=uuid4(),
        name="Test Resident",
        type="resident",
        email=f"{uuid4().hex[:8]}@example.com",
        pgy_level=1,
    )
    db.add_all([user, person])
    db.commit()

    draft = ScheduleDraft(
        id=uuid4(),
        created_at=datetime.utcnow(),
        created_by_id=user.id,
        target_start_date=date.today(),
        target_end_date=date.today(),
        status=ScheduleDraftStatus.DRAFT,
        source_type=source_type,
        change_summary={"added": 0, "modified": 0, "deleted": 0},
        flags_total=0,
        flags_acknowledged=0,
    )
    db.add(draft)
    db.commit()

    assignment = ScheduleDraftAssignment(
        id=uuid4(),
        draft_id=draft.id,
        person_id=person.id,
        assignment_date=date.today(),
        time_of_day="AM",
        activity_code=None,
        rotation_id=None,
        change_type=DraftAssignmentChangeType.ADD,
        existing_assignment_id=None,
    )
    db.add(assignment)
    db.commit()

    return draft, user, lock_date


@pytest.mark.asyncio
async def test_approve_break_glass_success(db):
    """Break-glass approval should succeed for a draft touching the lock window."""
    draft, user, lock_date = _create_locked_draft(db)
    service = ScheduleDraftService(db)

    result = await service.approve_break_glass(
        draft_id=draft.id,
        approved_by_id=user.id,
        reason="Emergency schedule change required for coverage gap",
    )

    assert result.success is True
    assert result.approved_at is not None
    assert result.approved_by_id == user.id
    assert (
        result.approval_reason == "Emergency schedule change required for coverage gap"
    )
    assert result.lock_date_at_approval == lock_date


@pytest.mark.asyncio
async def test_approve_break_glass_draft_not_found(db):
    """Break-glass approval should fail for non-existent draft."""
    service = ScheduleDraftService(db)

    result = await service.approve_break_glass(
        draft_id=uuid4(),
        approved_by_id=uuid4(),
        reason="This draft does not exist",
    )

    assert result.success is False
    assert result.error_code == "DRAFT_NOT_FOUND"


@pytest.mark.asyncio
async def test_approve_break_glass_no_lock_window_violation(db):
    """Break-glass approval should fail if draft doesn't touch lock window."""
    # Create draft with assignments AFTER the lock window
    lock_date = date.today() - timedelta(days=30)  # Lock date in the past
    settings = ApplicationSettings(schedule_lock_date=lock_date)
    db.add(settings)

    user = User(
        id=uuid4(),
        username=f"user_{uuid4().hex[:8]}",
        email=f"{uuid4().hex[:8]}@example.com",
        hashed_password="hashed",
        role="coordinator",
    )
    person = Person(
        id=uuid4(),
        name="Test Resident",
        type="resident",
        email=f"{uuid4().hex[:8]}@example.com",
        pgy_level=1,
    )
    db.add_all([user, person])
    db.commit()

    draft = ScheduleDraft(
        id=uuid4(),
        created_at=datetime.utcnow(),
        created_by_id=user.id,
        target_start_date=date.today() + timedelta(days=60),
        target_end_date=date.today() + timedelta(days=90),
        status=ScheduleDraftStatus.DRAFT,
        source_type=DraftSourceType.SOLVER,
        change_summary={"added": 0, "modified": 0, "deleted": 0},
        flags_total=0,
        flags_acknowledged=0,
    )
    db.add(draft)
    db.commit()

    # Assignment date is well after lock date
    assignment = ScheduleDraftAssignment(
        id=uuid4(),
        draft_id=draft.id,
        person_id=person.id,
        assignment_date=date.today() + timedelta(days=60),
        time_of_day="AM",
        activity_code=None,
        rotation_id=None,
        change_type=DraftAssignmentChangeType.ADD,
        existing_assignment_id=None,
    )
    db.add(assignment)
    db.commit()

    service = ScheduleDraftService(db)
    result = await service.approve_break_glass(
        draft_id=draft.id,
        approved_by_id=user.id,
        reason="This should not be needed",
    )

    assert result.success is False
    assert result.error_code == "NO_LOCK_WINDOW_VIOLATION"


@pytest.mark.asyncio
async def test_publish_succeeds_after_break_glass_approval(db):
    """Publish should succeed for a lock-window draft after break-glass approval."""
    draft, user, _ = _create_locked_draft(db)
    service = ScheduleDraftService(db)

    # First approve break-glass
    approval_result = await service.approve_break_glass(
        draft_id=draft.id,
        approved_by_id=user.id,
        reason="Emergency coverage gap requires schedule change",
    )
    assert approval_result.success is True

    # Now publish should succeed (not blocked by lock window)
    publish_result = await service.publish_draft(
        draft_id=draft.id,
        published_by_id=user.id,
        override_comment=None,
        validate_acgme=True,
    )

    assert publish_result.error_code != "LOCK_WINDOW_BLOCKED"


@pytest.mark.asyncio
async def test_publish_fails_without_approval_when_locked(db):
    """Publish should fail when lock window is touched and no approval exists."""
    draft, user, _ = _create_locked_draft(db)
    service = ScheduleDraftService(db)

    # Publish without break-glass approval
    result = await service.publish_draft(
        draft_id=draft.id,
        published_by_id=user.id,
        override_comment=None,
        validate_acgme=True,
    )

    assert result.success is False
    assert result.error_code == "LOCK_WINDOW_BLOCKED"
    assert "approve-break-glass" in result.message


@pytest.mark.asyncio
async def test_approval_resets_when_lock_date_changes(db):
    """Break-glass approval should reset if the lock date changes."""
    draft, user, original_lock_date = _create_locked_draft(db)
    service = ScheduleDraftService(db)

    # Approve break-glass
    approval_result = await service.approve_break_glass(
        draft_id=draft.id,
        approved_by_id=user.id,
        reason="Initial approval for coverage change",
    )
    assert approval_result.success is True

    # Verify approval is set
    db.refresh(draft)
    assert draft.approved_at is not None

    # Change the lock date
    settings = db.query(ApplicationSettings).first()
    settings.schedule_lock_date = original_lock_date + timedelta(days=14)
    db.commit()

    # Refresh the lock window flag — this should detect the change
    service._refresh_lock_window_flag(draft.id, commit=True)

    # Re-read draft
    db.refresh(draft)
    assert draft.approved_at is None, "Approval should reset when lock date changes"


@pytest.mark.asyncio
async def test_approve_break_glass_creates_activity_log(db):
    """Break-glass approval should create an activity log entry."""
    from app.models.activity_log import ActivityLog

    draft, user, _ = _create_locked_draft(db)
    service = ScheduleDraftService(db)

    # Count existing activity log entries
    before_count = db.query(ActivityLog).count()

    await service.approve_break_glass(
        draft_id=draft.id,
        approved_by_id=user.id,
        reason="Coverage gap requires emergency change",
    )

    after_count = db.query(ActivityLog).count()
    assert after_count == before_count + 1

    entry = (
        db.query(ActivityLog)
        .filter(ActivityLog.action_type == "BREAK_GLASS_APPROVED")
        .first()
    )
    assert entry is not None
    assert entry.user_id == user.id
    assert entry.target_id == str(draft.id)


@pytest.mark.asyncio
async def test_approve_break_glass_auto_acknowledges_lock_flag(db):
    """Break-glass approval should auto-acknowledge the LOCK_WINDOW_VIOLATION flag."""
    from app.models.schedule_draft import DraftFlagType, ScheduleDraftFlag

    draft, user, _ = _create_locked_draft(db)
    service = ScheduleDraftService(db)

    # Refresh lock window flag to create the LOCK_WINDOW_VIOLATION flag
    service._refresh_lock_window_flag(draft.id, commit=True)

    # Verify flag exists and is unacknowledged
    flag = (
        db.query(ScheduleDraftFlag)
        .filter(
            ScheduleDraftFlag.draft_id == draft.id,
            ScheduleDraftFlag.flag_type == DraftFlagType.LOCK_WINDOW_VIOLATION,
        )
        .first()
    )
    assert flag is not None
    assert flag.acknowledged_at is None

    # Approve break-glass
    result = await service.approve_break_glass(
        draft_id=draft.id,
        approved_by_id=user.id,
        reason="Emergency coverage gap requires schedule change",
    )
    assert result.success is True

    # Verify flag is now acknowledged
    db.refresh(flag)
    assert flag.acknowledged_at is not None
    assert flag.acknowledged_by_id == user.id
    assert "Break-glass approved" in flag.resolution_note
