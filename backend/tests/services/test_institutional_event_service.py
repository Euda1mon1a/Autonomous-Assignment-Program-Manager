"""Tests for InstitutionalEventService."""

from datetime import date
from uuid import uuid4

from app.models.activity import Activity, ActivityCategory
from app.services.institutional_event_service import InstitutionalEventService
from app.schemas.institutional_event import (
    InstitutionalEventCreate,
    InstitutionalEventUpdate,
)


def test_institutional_event_service_crud(db):
    activity = Activity(
        id=uuid4(),
        name="Holiday",
        code="HOL",
        display_abbreviation="HOL",
        activity_category=ActivityCategory.ADMINISTRATIVE.value,
    )
    db.add(activity)
    db.commit()

    service = InstitutionalEventService(db)
    event_in = InstitutionalEventCreate(
        name="Holiday Break",
        event_type="holiday",
        start_date=date.today(),
        end_date=date.today(),
        time_of_day=None,
        applies_to="all",
        applies_to_inpatient=False,
        activity_id=activity.id,
        notes="",
        is_active=True,
    )

    event = service.create_event(event_in)
    assert event.name == "Holiday Break"

    list_result = service.list_events(is_active=True)
    assert list_result["total"] == 1

    updated = service.update_event(
        event.id,
        InstitutionalEventUpdate(name="Updated Holiday"),
    )
    assert updated is not None
    assert updated.name == "Updated Holiday"

    deleted = service.delete_event(event.id)
    assert deleted is True

    active_after_delete = service.list_events(is_active=True)
    assert active_after_delete["total"] == 0
