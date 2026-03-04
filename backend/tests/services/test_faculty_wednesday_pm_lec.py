"""Tests for faculty Wednesday PM LEC preload injection.

Wednesday PM is protected didactic time at TAMC — residents have LEC
(from rotation_codes.py), and faculty should attend LEC rather than
being scheduled into clinic by the solver.
"""

from datetime import date, timedelta
from uuid import uuid4

from app.models.activity import Activity, ActivityCategory
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.inpatient_preload import InpatientPreload, InpatientRotationType
from app.models.person import FacultyRole, Person
from app.services.sync_preload_service import SyncPreloadService


def _create_activity(db, code: str, display: str, category: str) -> Activity:
    activity = Activity(
        id=uuid4(),
        name=code,
        code=code,
        display_abbreviation=display,
        activity_category=category,
        is_protected=category == ActivityCategory.EDUCATIONAL.value,
        counts_toward_physical_capacity=False,
    )
    db.add(activity)
    return activity


def _get_assignment(
    db, person_id, date_val, time_of_day: str
) -> HalfDayAssignment | None:
    return (
        db.query(HalfDayAssignment)
        .filter(
            HalfDayAssignment.person_id == person_id,
            HalfDayAssignment.date == date_val,
            HalfDayAssignment.time_of_day == time_of_day,
        )
        .first()
    )


def _find_regular_wednesday(start_date: date, end_date: date) -> date | None:
    """Find a Wednesday that is NOT the final Wednesday (>= 7 days before end_date)."""
    current = start_date
    while current <= end_date:
        if current.weekday() == 2 and (end_date - current).days >= 7:
            return current
        current += timedelta(days=1)
    return None


def _find_final_wednesday(start_date: date, end_date: date) -> date | None:
    """Find the final Wednesday (within 7 days of end_date)."""
    current = start_date
    while current <= end_date:
        if current.weekday() == 2 and (end_date - current).days < 7:
            return current
        current += timedelta(days=1)
    return None


def test_faculty_wednesday_pm_lec(db):
    """Core faculty should get LEC preloaded on regular Wednesday PMs."""
    _create_activity(db, "LEC", "LEC", ActivityCategory.EDUCATIONAL.value)

    faculty = Person(
        id=uuid4(),
        name="Test Faculty",
        type="faculty",
        faculty_role=FacultyRole.CORE.value,
    )
    db.add(faculty)
    db.commit()

    # Use a date range that includes a regular Wednesday
    # Feb 2026: Wed Feb 4 (day=4, regular), Wed Feb 11 (day=11, regular)
    start_date = date(2026, 2, 2)
    end_date = date(2026, 2, 15)

    service = SyncPreloadService(db)
    count = service._load_faculty_wednesday_pm_lec(start_date, end_date)

    assert count > 0, "Should create at least one LEC preload"

    # Check the first regular Wednesday
    wed = _find_regular_wednesday(start_date, end_date)
    assert wed is not None

    assignment = _get_assignment(db, faculty.id, wed, "PM")
    assert assignment is not None, f"No PM assignment for faculty on {wed}"
    assert assignment.activity.code == "LEC"
    assert assignment.source == AssignmentSource.PRELOAD.value


def test_faculty_final_wednesday_not_overridden(db):
    """Faculty should NOT get LEC on the final Wednesday (inverted schedule)."""
    _create_activity(db, "LEC", "LEC", ActivityCategory.EDUCATIONAL.value)

    faculty = Person(
        id=uuid4(),
        name="Test Faculty Final Wed",
        type="faculty",
        faculty_role=FacultyRole.CORE.value,
    )
    db.add(faculty)
    db.commit()

    # Use a date range where the only Wednesday is the final one
    # Jan 2026: Wed Jan 28 — within 7 days of end_date Jan 31
    start_date = date(2026, 1, 26)
    end_date = date(2026, 1, 31)

    service = SyncPreloadService(db)
    count = service._load_faculty_wednesday_pm_lec(start_date, end_date)

    final_wed = _find_final_wednesday(start_date, end_date)
    assert final_wed is not None
    assert final_wed == date(2026, 1, 28)

    assignment = _get_assignment(db, faculty.id, final_wed, "PM")
    assert assignment is None, f"Final Wednesday {final_wed} should NOT get LEC preload"
    assert count == 0


def test_final_wednesday_early_in_month(db):
    """Final Wednesday with day < 22 must still be skipped (Block 12 scenario).

    Block 12: May 7 – Jun 3, 2026. Jun 3 is a Wednesday with day=3,
    but it IS the final Wednesday (within 7 days of end_date).
    The old day >= 22 heuristic failed here.
    """
    _create_activity(db, "LEC", "LEC", ActivityCategory.EDUCATIONAL.value)

    faculty = Person(
        id=uuid4(),
        name="Test Faculty Block12",
        type="faculty",
        faculty_role=FacultyRole.CORE.value,
    )
    db.add(faculty)
    db.commit()

    # Block 12: May 7 – Jun 3, 2026
    start_date = date(2026, 5, 7)
    end_date = date(2026, 6, 3)

    service = SyncPreloadService(db)
    count = service._load_faculty_wednesday_pm_lec(start_date, end_date)

    # Jun 3 (day=3) is the final Wednesday — should be skipped
    final_wed = _find_final_wednesday(start_date, end_date)
    assert final_wed == date(2026, 6, 3)
    assignment = _get_assignment(db, faculty.id, final_wed, "PM")
    assert assignment is None, "Jun 3 final Wednesday should NOT get LEC preload"

    # Earlier Wednesdays (May 7, 14, 21, 28) should all get LEC
    regular_wed = _find_regular_wednesday(start_date, end_date)
    assert regular_wed is not None
    assignment = _get_assignment(db, faculty.id, regular_wed, "PM")
    assert assignment is not None, f"Regular Wednesday {regular_wed} should get LEC"
    assert assignment.activity.code == "LEC"


def test_no_faculty_means_no_preloads(db):
    """No faculty in DB → zero LEC preloads (no crash)."""
    _create_activity(db, "LEC", "LEC", ActivityCategory.EDUCATIONAL.value)
    db.commit()

    start_date = date(2026, 2, 2)
    end_date = date(2026, 2, 15)

    service = SyncPreloadService(db)
    count = service._load_faculty_wednesday_pm_lec(start_date, end_date)

    assert count == 0, "No faculty should mean zero preloads"


def test_fmit_faculty_excluded(db):
    """Faculty on FMIT rotation should keep their FMIT schedule, not LEC."""
    _create_activity(db, "LEC", "LEC", ActivityCategory.EDUCATIONAL.value)

    faculty = Person(
        id=uuid4(),
        name="FMIT Faculty",
        type="faculty",
        faculty_role=FacultyRole.CORE.value,
    )
    db.add(faculty)
    db.commit()

    start_date = date(2026, 2, 2)
    end_date = date(2026, 2, 15)

    # Create an FMIT preload covering the entire range
    fmit_preload = InpatientPreload(
        id=uuid4(),
        person_id=faculty.id,
        rotation_type=InpatientRotationType.FMIT,
        start_date=start_date,
        end_date=end_date,
    )
    db.add(fmit_preload)
    db.commit()

    service = SyncPreloadService(db)
    count = service._load_faculty_wednesday_pm_lec(start_date, end_date)

    assert count == 0, "FMIT faculty should not receive LEC preloads"

    wed = _find_regular_wednesday(start_date, end_date)
    assignment = _get_assignment(db, faculty.id, wed, "PM")
    assert assignment is None, "FMIT faculty should have no LEC on Wednesday PM"


def test_wednesday_am_not_affected(db):
    """Wednesday AM should NOT be touched by the LEC preloader."""
    _create_activity(db, "LEC", "LEC", ActivityCategory.EDUCATIONAL.value)

    faculty = Person(
        id=uuid4(),
        name="Faculty AM Check",
        type="faculty",
        faculty_role=FacultyRole.CORE.value,
    )
    db.add(faculty)
    db.commit()

    start_date = date(2026, 2, 2)
    end_date = date(2026, 2, 15)

    service = SyncPreloadService(db)
    service._load_faculty_wednesday_pm_lec(start_date, end_date)

    wed = _find_regular_wednesday(start_date, end_date)
    am_assignment = _get_assignment(db, faculty.id, wed, "AM")
    assert am_assignment is None, "Wednesday AM should not be affected by LEC preload"
