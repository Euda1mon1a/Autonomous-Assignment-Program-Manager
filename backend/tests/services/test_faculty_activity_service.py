"""Tests for FacultyActivityService upsert behavior."""

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.activity import Activity, ActivityCategory
from app.models.person import Person
from app.services.faculty_activity_service import FacultyActivityService


@pytest.mark.asyncio
async def test_upsert_template_slot_creates_and_updates(
    db: Session,
    sample_faculty: Person,
) -> None:
    activity_a = Activity(
        id=uuid4(),
        name="Clinic A",
        code="clinic_a",
        display_abbreviation="C",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    activity_b = Activity(
        id=uuid4(),
        name="Clinic B",
        code="clinic_b",
        display_abbreviation="CB",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    db.add_all([activity_a, activity_b])
    db.commit()

    service = FacultyActivityService(db)

    created = await service.upsert_template_slot(
        person_id=sample_faculty.id,
        day_of_week=1,
        time_of_day="AM",
        week_number=None,
        activity_id=activity_a.id,
        is_locked=False,
        priority=50,
        notes="Initial",
    )

    updated = await service.upsert_template_slot(
        person_id=sample_faculty.id,
        day_of_week=1,
        time_of_day="AM",
        week_number=None,
        activity_id=activity_b.id,
        is_locked=True,
        priority=80,
        notes="Updated",
    )

    assert created.id == updated.id
    assert updated.activity_id == activity_b.id
    assert updated.is_locked is True
    assert updated.priority == 80
    assert updated.notes == "Updated"
