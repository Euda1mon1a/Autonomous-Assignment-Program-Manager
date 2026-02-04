"""Tests for ScheduleOverrideService validation behavior."""

from datetime import date
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.activity import Activity, ActivityCategory
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person
from app.schemas.schedule_override import ScheduleOverrideCreate
from app.services.schedule_override_service import ScheduleOverrideService


@pytest.mark.asyncio
async def test_schedule_override_blocks_protected_cancellation(async_db_session, db):
    resident = Person(
        id=uuid4(),
        name="Dr. Resident",
        type="resident",
        email="resident@example.org",
        pgy_level=1,
    )
    activity = Activity(
        id=uuid4(),
        name="FMIT",
        code="FMIT",
        display_abbreviation="FMIT",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    db.add_all([resident, activity])
    db.commit()

    assignment = HalfDayAssignment(
        id=uuid4(),
        person_id=resident.id,
        date=date.today(),
        time_of_day="AM",
        activity_id=activity.id,
        source="solver",
    )
    db.add(assignment)
    db.commit()

    service = ScheduleOverrideService(async_db_session)

    with pytest.raises(HTTPException) as exc:
        await service.create_override(
            ScheduleOverrideCreate(
                half_day_assignment_id=assignment.id,
                override_type="cancellation",
                replacement_person_id=None,
                reason="testing",
                notes=None,
                supersedes_override_id=None,
            ),
            created_by_id=None,
        )

    assert exc.value.status_code == 400
    assert "cannot cancel" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_schedule_override_requires_different_replacement(async_db_session, db):
    resident = Person(
        id=uuid4(),
        name="Dr. Resident",
        type="resident",
        email="resident2@example.org",
        pgy_level=2,
    )
    activity = Activity(
        id=uuid4(),
        name="Clinic",
        code="CLN",
        display_abbreviation="C",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    db.add_all([resident, activity])
    db.commit()

    assignment = HalfDayAssignment(
        id=uuid4(),
        person_id=resident.id,
        date=date.today(),
        time_of_day="PM",
        activity_id=activity.id,
        source="solver",
    )
    db.add(assignment)
    db.commit()

    service = ScheduleOverrideService(async_db_session)

    with pytest.raises(HTTPException) as exc:
        await service.create_override(
            ScheduleOverrideCreate(
                half_day_assignment_id=assignment.id,
                override_type="coverage",
                replacement_person_id=resident.id,
                reason="testing",
                notes=None,
                supersedes_override_id=None,
            ),
            created_by_id=None,
        )

    assert exc.value.status_code == 400
    assert "replacement person must differ" in exc.value.detail.lower()
