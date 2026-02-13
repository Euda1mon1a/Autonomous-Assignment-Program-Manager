"""Tests for FacultyAssignmentExpansionService."""

import pytest
from datetime import date
from uuid import uuid4

from app.models.absence import Absence
from app.models.activity import Activity
from app.models.half_day_assignment import HalfDayAssignment, AssignmentSource
from app.models.person import Person
from app.services.faculty_assignment_expansion_service import (
    FacultyAssignmentExpansionService,
)
from app.utils.academic_blocks import get_block_dates


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


@pytest.mark.xfail(
    reason="check_faculty_role constraint missing 'adjunct' — needs migration to add it",
    raises=Exception,
)
def test_get_adjunct_faculty_without_assignments_counts(db) -> None:
    block_dates = get_block_dates(1, 2025)
    test_date = block_dates.start_date

    adjunct_a = Person(
        id=uuid4(),
        name="Adjunct A",
        type="faculty",
        faculty_role="adjunct",
        min_clinic_halfdays_per_week=1,
        max_clinic_halfdays_per_week=2,
    )
    adjunct_b = Person(
        id=uuid4(),
        name="Adjunct B",
        type="faculty",
        faculty_role="adjunct",
        min_clinic_halfdays_per_week=0,
        max_clinic_halfdays_per_week=3,
    )
    db.add_all([adjunct_a, adjunct_b])
    db.commit()

    activity = _create_activity(db, "gme")

    assignment = HalfDayAssignment(
        person_id=adjunct_a.id,
        date=test_date,
        time_of_day="AM",
        activity_id=activity.id,
        source=AssignmentSource.PRELOAD.value,
    )
    db.add(assignment)
    db.commit()

    service = FacultyAssignmentExpansionService(db)
    gaps = service.get_adjunct_faculty_without_assignments(1, 2025)

    assert len(gaps) == 2
    counts = {gap.person_id: gap.existing_assignment_count for gap in gaps}
    assert counts[adjunct_a.id] == 1
    assert counts[adjunct_b.id] == 0
