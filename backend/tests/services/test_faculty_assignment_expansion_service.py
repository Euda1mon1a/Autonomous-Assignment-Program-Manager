"""Tests for FacultyAssignmentExpansionService."""

from datetime import date
from uuid import uuid4

from app.models.activity import Activity
from app.models.half_day_assignment import HalfDayAssignment, AssignmentSource
from app.models.person import Person
from app.services.faculty_assignment_expansion_service import (
    FacultyAssignmentExpansionService,
)


def _create_activity(db, code: str) -> Activity:
    activity = Activity(
        name=f"{code} activity",
        code=code,
        display_abbreviation=code.upper(),
        activity_category="administrative",
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def test_fill_slot_prioritizes_deployment_over_leave(db) -> None:
    person = Person(
        id=uuid4(),
        name="Dr. Deploy",
        type="faculty",
        admin_type="GME",
    )
    db.add(person)
    db.commit()

    dep = _create_activity(db, "DEP")
    lv_am = _create_activity(db, "LV-AM")
    weekend = _create_activity(db, "W")
    holiday = _create_activity(db, "HOL")
    gme = _create_activity(db, "gme")

    FacultyAssignmentExpansionService._activity_cache = {}
    service = FacultyAssignmentExpansionService(db)
    service._activity_cache = {
        "DEP": dep,
        "LV-AM": lv_am,
        "W": weekend,
        "HOL": holiday,
        "gme": gme,
    }

    created = service._fill_slot(
        person=person,
        slot_date=date(2026, 2, 10),
        time_of_day="AM",
        is_weekend=False,
        is_absent=True,
        is_deployed=True,
        is_holiday=False,
        admin_type="GME",
    )

    assert created is True
    db.commit()

    assignment = (
        db.query(HalfDayAssignment)
        .filter_by(person_id=person.id, date=date(2026, 2, 10), time_of_day="AM")
        .one()
    )
    assert assignment.activity_id == dep.id
    assert assignment.source == AssignmentSource.TEMPLATE.value


def test_fill_slot_maps_sm_admin_type_to_sm_clinic(db) -> None:
    person = Person(
        id=uuid4(),
        name="Dr. Sports",
        type="faculty",
        admin_type="SM",
    )
    db.add(person)
    db.commit()

    sm_activity = _create_activity(db, "sm_clinic")

    FacultyAssignmentExpansionService._activity_cache = {}
    service = FacultyAssignmentExpansionService(db)
    service._activity_cache = {"sm_clinic": sm_activity}

    created = service._fill_slot(
        person=person,
        slot_date=date(2026, 2, 11),
        time_of_day="PM",
        is_weekend=False,
        is_absent=False,
        is_deployed=False,
        is_holiday=False,
        admin_type="SM",
    )

    assert created is True
    db.commit()

    assignment = (
        db.query(HalfDayAssignment)
        .filter_by(person_id=person.id, date=date(2026, 2, 11), time_of_day="PM")
        .one()
    )
    assert assignment.activity_id == sm_activity.id
