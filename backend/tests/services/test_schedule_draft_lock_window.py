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
        break_glass_reason=None,
        validate_acgme=True,
    )

    assert result.success is False
    assert result.error_code == "LOCK_WINDOW_BLOCKED"
