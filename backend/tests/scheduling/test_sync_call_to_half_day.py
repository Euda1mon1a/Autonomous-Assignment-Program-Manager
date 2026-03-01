"""Tests for SchedulingEngine._sync_call_to_half_day().

Verifies that CALL HDAs are created on the call date PM slot when the
solver generates new call_assignments. This closes the two-table sync gap
where _sync_call_pcat_do_to_half_day() creates PCAT/DO for the day AFTER
a call but never creates the CALL HDA for the call date itself.
"""

from datetime import date
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.models.activity import Activity, ActivityCategory
from app.models.call_assignment import CallAssignment
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.person import FacultyRole, Person
from app.scheduling.engine import SchedulingEngine


def _create_call_activity(db) -> Activity:
    activity = Activity(
        id=uuid4(),
        name="Call",
        code="call",
        display_abbreviation="CALL",
        activity_category=ActivityCategory.CLINICAL.value,
        is_protected=False,
        counts_toward_physical_capacity=False,
    )
    db.add(activity)
    db.flush()
    return activity


def _create_faculty(db, name: str = "Test Faculty") -> Person:
    faculty = Person(
        id=uuid4(),
        name=name,
        type="faculty",
        faculty_role=FacultyRole.CORE.value,
    )
    db.add(faculty)
    db.flush()
    return faculty


def _make_engine(db):
    """Create engine with real DB but bypassed __init__."""
    with patch.object(SchedulingEngine, "__init__", lambda self, *a, **kw: None):
        engine = SchedulingEngine.__new__(SchedulingEngine)
        engine.db = db
        engine.start_date = date(2026, 5, 7)
        engine.end_date = date(2026, 6, 3)
    return engine


def test_creates_call_hda_for_new_assignment(db):
    """CALL HDA should be created on call date PM slot."""
    call_activity = _create_call_activity(db)
    faculty = _create_faculty(db)

    call_date = date(2026, 5, 12)  # Monday
    ca = CallAssignment(
        date=call_date,
        person_id=faculty.id,
        call_type="overnight",
        is_weekend=False,
    )
    db.add(ca)
    db.flush()

    engine = _make_engine(db)
    count = engine._sync_call_to_half_day([ca])

    assert count == 1

    hda = (
        db.query(HalfDayAssignment)
        .filter(
            HalfDayAssignment.person_id == faculty.id,
            HalfDayAssignment.date == call_date,
            HalfDayAssignment.time_of_day == "PM",
        )
        .first()
    )
    assert hda is not None
    assert hda.activity_id == call_activity.id
    assert hda.source == AssignmentSource.PRELOAD.value


def test_overwrites_solver_slot(db):
    """Solver-sourced PM slot should be overwritten with CALL."""
    call_activity = _create_call_activity(db)
    faculty = _create_faculty(db)

    # Create a solver-sourced HDA on the PM slot
    other_activity = Activity(
        id=uuid4(),
        name="FM Clinic",
        code="fm_clinic",
        display_abbreviation="C",
        activity_category=ActivityCategory.CLINICAL.value,
        is_protected=False,
        counts_toward_physical_capacity=True,
    )
    db.add(other_activity)
    db.flush()

    call_date = date(2026, 5, 13)  # Tuesday
    existing_hda = HalfDayAssignment(
        person_id=faculty.id,
        date=call_date,
        time_of_day="PM",
        activity_id=other_activity.id,
        source=AssignmentSource.SOLVER.value,
    )
    db.add(existing_hda)
    db.flush()

    ca = CallAssignment(
        date=call_date,
        person_id=faculty.id,
        call_type="overnight",
        is_weekend=False,
    )
    db.add(ca)
    db.flush()

    engine = _make_engine(db)
    count = engine._sync_call_to_half_day([ca])

    assert count == 1
    db.refresh(existing_hda)
    assert existing_hda.activity_id == call_activity.id
    assert existing_hda.source == AssignmentSource.PRELOAD.value


def test_skips_when_already_call(db):
    """Preloaded CALL HDA should not be re-counted."""
    call_activity = _create_call_activity(db)
    faculty = _create_faculty(db)

    call_date = date(2026, 5, 14)
    existing_hda = HalfDayAssignment(
        person_id=faculty.id,
        date=call_date,
        time_of_day="PM",
        activity_id=call_activity.id,  # already CALL
        source=AssignmentSource.PRELOAD.value,
    )
    db.add(existing_hda)
    db.flush()

    ca = CallAssignment(
        date=call_date,
        person_id=faculty.id,
        call_type="overnight",
        is_weekend=False,
    )
    db.add(ca)
    db.flush()

    engine = _make_engine(db)
    count = engine._sync_call_to_half_day([ca])

    # Already CALL — no change needed
    assert count == 0


def test_overrides_preloaded_non_call_activity(db):
    """CALL overrides preloaded LEC/W/OFF because call is authoritative."""
    call_activity = _create_call_activity(db)
    faculty = _create_faculty(db)

    # Preloaded LEC on this PM slot (e.g., Wednesday PM LEC)
    lec_activity = Activity(
        id=uuid4(),
        name="LEC",
        code="LEC",
        display_abbreviation="LEC",
        activity_category=ActivityCategory.EDUCATIONAL.value,
        is_protected=True,
        counts_toward_physical_capacity=False,
    )
    db.add(lec_activity)
    db.flush()

    call_date = date(2026, 5, 13)  # Wednesday
    existing_hda = HalfDayAssignment(
        person_id=faculty.id,
        date=call_date,
        time_of_day="PM",
        activity_id=lec_activity.id,
        source=AssignmentSource.PRELOAD.value,
    )
    db.add(existing_hda)
    db.flush()

    ca = CallAssignment(
        date=call_date,
        person_id=faculty.id,
        call_type="overnight",
        is_weekend=False,
    )
    db.add(ca)
    db.flush()

    engine = _make_engine(db)
    count = engine._sync_call_to_half_day([ca])

    assert count == 1
    db.refresh(existing_hda)
    assert existing_hda.activity_id == call_activity.id
    assert existing_hda.source == AssignmentSource.PRELOAD.value


def test_empty_list_returns_zero(db):
    """Empty call_assignments list should return 0 without error."""
    _create_call_activity(db)
    engine = _make_engine(db)
    count = engine._sync_call_to_half_day([])
    assert count == 0


def test_multiple_calls_creates_multiple_hdas(db):
    """Multiple call assignments should create one CALL HDA each."""
    _create_call_activity(db)
    f1 = _create_faculty(db, "Faculty A")
    f2 = _create_faculty(db, "Faculty B")

    ca1 = CallAssignment(
        date=date(2026, 5, 12),
        person_id=f1.id,
        call_type="overnight",
        is_weekend=False,
    )
    ca2 = CallAssignment(
        date=date(2026, 5, 18),
        person_id=f2.id,
        call_type="weekend",
        is_weekend=True,
    )
    db.add_all([ca1, ca2])
    db.flush()

    engine = _make_engine(db)
    count = engine._sync_call_to_half_day([ca1, ca2])

    assert count == 2

    hdas = (
        db.query(HalfDayAssignment).filter(HalfDayAssignment.time_of_day == "PM").all()
    )
    assert len(hdas) == 2


def test_removes_stale_call_hdas(db):
    """Old CALL HDAs without matching call_assignment should be deleted.

    Scenario: faculty A had a call last regen, but this regen assigns
    the call to faculty B instead. Faculty A's stale CALL HDA must be removed.
    """
    call_activity = _create_call_activity(db)
    faculty_a = _create_faculty(db, "Faculty A (stale)")
    faculty_b = _create_faculty(db, "Faculty B (current)")

    call_date = date(2026, 5, 14)  # Wednesday, within block range

    # Simulate stale CALL HDA from previous regeneration for faculty A
    stale_hda = HalfDayAssignment(
        person_id=faculty_a.id,
        date=call_date,
        time_of_day="PM",
        activity_id=call_activity.id,
        source=AssignmentSource.PRELOAD.value,
    )
    db.add(stale_hda)
    db.flush()

    # Current regeneration assigns the call to faculty B only
    ca = CallAssignment(
        date=call_date,
        person_id=faculty_b.id,
        call_type="overnight",
        is_weekend=False,
    )
    db.add(ca)
    db.flush()

    engine = _make_engine(db)
    count = engine._sync_call_to_half_day([ca])

    # Faculty B gets a new CALL HDA
    assert count == 1

    # Faculty A's stale CALL HDA should be gone
    remaining = (
        db.query(HalfDayAssignment)
        .filter(
            HalfDayAssignment.time_of_day == "PM",
            HalfDayAssignment.activity_id == call_activity.id,
        )
        .all()
    )
    assert len(remaining) == 1
    assert remaining[0].person_id == faculty_b.id


def test_pcat_do_overwrites_stale_call_preload(db):
    """Stale CALL preload on next-day PM should be overwritten by DO.

    Scenario: Previous generation had a call on May 11 (CALL HDA on May 11 PM
    with source='preload'). New generation has a call on May 10 instead.
    The sync should overwrite the stale May 11 PM CALL with DO, not skip it.

    This was the root cause of the Block 12 regeneration PCAT/DO integrity
    failure: stale CALL preloads blocked DO creation, then got cleaned up by
    _sync_call_to_half_day, leaving nothing for the validation fallback.
    """
    call_activity = _create_call_activity(db)
    faculty = _create_faculty(db)

    # Create PCAT and DO activities
    pcat_activity = Activity(
        id=uuid4(),
        name="PCAT",
        code="pcat",
        display_abbreviation="PCAT",
        activity_category=ActivityCategory.CLINICAL.value,
        is_protected=True,
        counts_toward_physical_capacity=False,
    )
    do_activity = Activity(
        id=uuid4(),
        name="DO",
        code="do",
        display_abbreviation="DO",
        activity_category=ActivityCategory.CLINICAL.value,
        is_protected=True,
        counts_toward_physical_capacity=False,
    )
    db.add_all([pcat_activity, do_activity])
    db.flush()

    # Stale CALL preload from previous generation on May 11 PM
    stale_call_hda = HalfDayAssignment(
        person_id=faculty.id,
        date=date(2026, 5, 11),  # Monday
        time_of_day="PM",
        activity_id=call_activity.id,
        source=AssignmentSource.PRELOAD.value,
    )
    db.add(stale_call_hda)
    db.flush()

    # New generation: call on May 10 (Sunday) → needs DO on May 11 PM
    ca = CallAssignment(
        date=date(2026, 5, 10),
        person_id=faculty.id,
        call_type="overnight",
        is_weekend=True,
    )
    db.add(ca)
    db.flush()

    engine = _make_engine(db)
    count = engine._sync_call_pcat_do_to_half_day([ca])

    # Should create PCAT on May 11 AM + overwrite stale CALL with DO on May 11 PM
    assert count == 2

    # Verify May 11 PM is now DO, not CALL
    pm_hda = (
        db.query(HalfDayAssignment)
        .filter(
            HalfDayAssignment.person_id == faculty.id,
            HalfDayAssignment.date == date(2026, 5, 11),
            HalfDayAssignment.time_of_day == "PM",
        )
        .first()
    )
    assert pm_hda is not None
    assert pm_hda.activity_id == do_activity.id
    assert pm_hda.source == AssignmentSource.PRELOAD.value

    # Verify May 11 AM is PCAT
    am_hda = (
        db.query(HalfDayAssignment)
        .filter(
            HalfDayAssignment.person_id == faculty.id,
            HalfDayAssignment.date == date(2026, 5, 11),
            HalfDayAssignment.time_of_day == "AM",
        )
        .first()
    )
    assert am_hda is not None
    assert am_hda.activity_id == pcat_activity.id


def test_stale_cleanup_preserves_resident_call_hdas(db):
    """Stale CALL cleanup must NOT delete resident CALL preloads.

    Resident CALL HDAs come from resident_call_preloads (separate source)
    and have no matching CallAssignment rows. They must survive cleanup.
    """
    call_activity = _create_call_activity(db)

    # Create a resident (not faculty)
    resident = Person(
        id=uuid4(),
        name="Test Resident",
        type="resident",
    )
    db.add(resident)

    # Create a faculty member who has the current call
    faculty = _create_faculty(db, "Faculty with call")

    call_date = date(2026, 5, 14)  # Within block range

    # Resident CALL HDA (from resident_call_preloads, no CallAssignment)
    resident_call_hda = HalfDayAssignment(
        person_id=resident.id,
        date=call_date,
        time_of_day="PM",
        activity_id=call_activity.id,
        source=AssignmentSource.PRELOAD.value,
    )
    db.add(resident_call_hda)
    db.flush()

    # Only faculty has a CallAssignment — resident does not
    ca = CallAssignment(
        date=call_date,
        person_id=faculty.id,
        call_type="overnight",
        is_weekend=False,
    )
    db.add(ca)
    db.flush()

    engine = _make_engine(db)
    count = engine._sync_call_to_half_day([ca])

    # Faculty gets CALL HDA
    assert count == 1

    # Resident's CALL HDA must still exist (not deleted by stale cleanup)
    all_call_hdas = (
        db.query(HalfDayAssignment)
        .filter(
            HalfDayAssignment.activity_id == call_activity.id,
            HalfDayAssignment.time_of_day == "PM",
        )
        .all()
    )
    assert len(all_call_hdas) == 2  # resident + faculty
    person_ids = {h.person_id for h in all_call_hdas}
    assert resident.id in person_ids
    assert faculty.id in person_ids
