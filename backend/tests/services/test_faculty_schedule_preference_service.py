"""Tests for FacultySchedulePreferenceService."""

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.faculty_schedule_preference import (
    FacultyPreferenceDirection,
    FacultyPreferenceType,
    FacultySchedulePreference,
)
from app.models.person import Person
from app.schemas.faculty_schedule_preference import (
    FacultySchedulePreferenceCreate,
    FacultySchedulePreferenceUpdate,
)
from app.services.faculty_schedule_preference_service import (
    FacultySchedulePreferenceService,
)


def _create_faculty(db):
    faculty = Person(
        id=uuid4(),
        name="Dr. Faculty Pref",
        type="faculty",
        email="faculty.pref@example.org",
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


def test_create_preference_rejects_duplicate_rank(db):
    faculty = _create_faculty(db)
    service = FacultySchedulePreferenceService(db)

    first = FacultySchedulePreference(
        id=uuid4(),
        person_id=faculty.id,
        preference_type=FacultyPreferenceType.CLINIC,
        direction=FacultyPreferenceDirection.PREFER,
        rank=1,
        day_of_week=2,
        time_of_day="AM",
        weight=6,
        is_active=True,
    )
    db.add(first)
    db.commit()

    with pytest.raises(HTTPException) as excinfo:
        service.create_preference(
            FacultySchedulePreferenceCreate(
                person_id=faculty.id,
                preference_type=FacultyPreferenceType.CLINIC,
                direction=FacultyPreferenceDirection.PREFER,
                rank=1,
                day_of_week=3,
                time_of_day="PM",
                weight=6,
                is_active=True,
            )
        )

    assert excinfo.value.status_code == 409


def test_create_preference_rejects_third_active(db):
    faculty = _create_faculty(db)
    service = FacultySchedulePreferenceService(db)

    for rank in (1, 2):
        db.add(
            FacultySchedulePreference(
                id=uuid4(),
                person_id=faculty.id,
                preference_type=FacultyPreferenceType.CLINIC,
                direction=FacultyPreferenceDirection.PREFER,
                rank=rank,
                day_of_week=rank,
                time_of_day="AM",
                weight=6,
                is_active=True,
            )
        )
    db.commit()

    with pytest.raises(HTTPException) as excinfo:
        service.create_preference(
            FacultySchedulePreferenceCreate(
                person_id=faculty.id,
                preference_type=FacultyPreferenceType.CALL,
                direction=FacultyPreferenceDirection.AVOID,
                rank=2,
                day_of_week=4,
                time_of_day=None,
                weight=6,
                is_active=True,
            )
        )

    # Rank collision is detected before active-count check
    assert excinfo.value.status_code == 409


def test_update_preference_rejects_rank_collision(db):
    faculty = _create_faculty(db)
    service = FacultySchedulePreferenceService(db)

    pref_one = FacultySchedulePreference(
        id=uuid4(),
        person_id=faculty.id,
        preference_type=FacultyPreferenceType.CLINIC,
        direction=FacultyPreferenceDirection.PREFER,
        rank=1,
        day_of_week=1,
        time_of_day="AM",
        weight=6,
        is_active=True,
    )
    pref_two = FacultySchedulePreference(
        id=uuid4(),
        person_id=faculty.id,
        preference_type=FacultyPreferenceType.CALL,
        direction=FacultyPreferenceDirection.AVOID,
        rank=2,
        day_of_week=2,
        time_of_day=None,
        weight=6,
        is_active=True,
    )
    db.add_all([pref_one, pref_two])
    db.commit()

    with pytest.raises(HTTPException) as excinfo:
        service.update_preference(
            pref_two.id,
            FacultySchedulePreferenceUpdate(rank=1),
        )

    assert excinfo.value.status_code == 409


def test_delete_preference_marks_inactive(db):
    faculty = _create_faculty(db)
    service = FacultySchedulePreferenceService(db)

    pref = FacultySchedulePreference(
        id=uuid4(),
        person_id=faculty.id,
        preference_type=FacultyPreferenceType.CLINIC,
        direction=FacultyPreferenceDirection.PREFER,
        rank=1,
        day_of_week=1,
        time_of_day="AM",
        weight=6,
        is_active=True,
    )
    db.add(pref)
    db.commit()

    assert service.delete_preference(pref.id) is True
    db.refresh(pref)
    assert pref.is_active is False
