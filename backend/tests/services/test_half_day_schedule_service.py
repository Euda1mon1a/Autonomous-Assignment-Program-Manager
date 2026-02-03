"""Tests for HalfDayScheduleService supervision coverage."""

from datetime import date
from uuid import uuid4

import pytest

from app.models.activity import Activity, ActivityCategory
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person
from app.services.half_day_schedule_service import HalfDayScheduleService


@pytest.mark.asyncio
async def test_get_at_coverage_counts_supervision(async_db_session, db):
    resident = Person(
        id=uuid4(),
        name="Dr. Resident",
        type="resident",
        email="resident@example.org",
        pgy_level=1,
    )
    faculty = Person(
        id=uuid4(),
        name="Dr. Faculty",
        type="faculty",
        email="faculty@example.org",
    )
    db.add_all([resident, faculty])

    clinic_activity = Activity(
        id=uuid4(),
        name="Clinic",
        code="C",
        display_abbreviation="C",
        activity_category=ActivityCategory.CLINICAL.value,
        counts_toward_physical_capacity=True,
        provides_supervision=False,
    )
    supervision_activity = Activity(
        id=uuid4(),
        name="Attending Time",
        code="AT",
        display_abbreviation="AT",
        activity_category=ActivityCategory.CLINICAL.value,
        provides_supervision=True,
    )
    db.add_all([clinic_activity, supervision_activity])
    db.commit()

    slot_date = date.today()
    resident_assignment = HalfDayAssignment(
        id=uuid4(),
        person_id=resident.id,
        date=slot_date,
        time_of_day="AM",
        activity_id=clinic_activity.id,
        counts_toward_fmc_capacity=True,
        source="solver",
    )
    faculty_assignment = HalfDayAssignment(
        id=uuid4(),
        person_id=faculty.id,
        date=slot_date,
        time_of_day="AM",
        activity_id=supervision_activity.id,
        counts_toward_fmc_capacity=False,
        source="solver",
    )
    db.add_all([resident_assignment, faculty_assignment])
    db.commit()

    service = HalfDayScheduleService(async_db_session)
    result = await service.get_at_coverage(slot_date, "AM")

    assert result["at_demand"] == 0.5
    assert result["at_demand_rounded"] == 1
    assert result["at_coverage"] == 1.0
    assert result["is_sufficient"] is True
