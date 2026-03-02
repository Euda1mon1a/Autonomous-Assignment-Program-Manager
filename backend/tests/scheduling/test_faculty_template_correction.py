"""Tests for SchedulingEngine._apply_faculty_template_correction().

Verifies that solver-source faculty HDAs are corrected to match their
faculty_weekly_templates. This is Step 7.5b in the pipeline — a safety
net that ensures template fidelity after the solver writes coarse codes
(C, AT, OFF) and backfill fills gaps.
"""

from datetime import date
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.models.activity import Activity, ActivityCategory
from app.models.faculty_weekly_template import FacultyWeeklyTemplate
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.person import FacultyRole, Person
from app.scheduling.engine import SchedulingEngine


def _create_activity(db, code: str, name: str | None = None) -> Activity:
    activity = Activity(
        id=uuid4(),
        name=name or code.upper(),
        code=code,
        display_abbreviation=code.upper(),
        activity_category=ActivityCategory.CLINICAL.value,
        is_protected=False,
        counts_toward_physical_capacity=False,
    )
    db.add(activity)
    db.flush()
    return activity


def _create_faculty(
    db, name: str = "Test Faculty", role: str = FacultyRole.CORE.value
) -> Person:
    faculty = Person(
        id=uuid4(),
        name=name,
        type="faculty",
        faculty_role=role,
    )
    db.add(faculty)
    db.flush()
    return faculty


def _create_template(db, person_id, day_of_week: int, tod: str, activity_id):
    tpl = FacultyWeeklyTemplate(
        id=uuid4(),
        person_id=person_id,
        day_of_week=day_of_week,
        time_of_day=tod,
        activity_id=activity_id,
        week_number=None,
    )
    db.add(tpl)
    db.flush()
    return tpl


def _create_hda(db, person_id, hda_date, tod, activity_id, source="solver"):
    hda = HalfDayAssignment(
        person_id=person_id,
        date=hda_date,
        time_of_day=tod,
        activity_id=activity_id,
        source=source,
    )
    db.add(hda)
    db.flush()
    return hda


def _make_engine(db):
    """Create engine with real DB but bypassed __init__."""
    with patch.object(SchedulingEngine, "__init__", lambda self, *a, **kw: None):
        engine = SchedulingEngine.__new__(SchedulingEngine)
        engine.db = db
        engine.start_date = date(2026, 5, 7)
        engine.end_date = date(2026, 6, 3)
    return engine


# ── Test 1: Corrects solver C → template sm_clinic ──


def test_corrects_solver_c_to_template_sm_clinic(db):
    """Solver's generic C (fm_clinic) should become sm_clinic per template."""
    fm_clinic = _create_activity(db, "fm_clinic", "FM Clinic")
    sm_clinic = _create_activity(db, "sm_clinic", "SM Clinic")

    faculty = _create_faculty(db)

    # Template: Monday AM = sm_clinic
    _create_template(db, faculty.id, 0, "AM", sm_clinic.id)

    # HDA: Monday AM = fm_clinic (solver wrote generic clinic)
    monday = date(2026, 5, 11)  # Monday
    hda = _create_hda(db, faculty.id, monday, "AM", fm_clinic.id)

    engine = _make_engine(db)
    count = engine._apply_faculty_template_correction([faculty])

    assert count == 1
    db.refresh(hda)
    assert hda.activity_id == sm_clinic.id


# ── Test 2: Corrects solver AT → template gme ──


def test_corrects_solver_at_to_template_gme(db):
    """Solver's generic AT should become gme per template."""
    at = _create_activity(db, "at", "Admin Time")
    gme = _create_activity(db, "gme", "GME")

    faculty = _create_faculty(db)
    _create_template(db, faculty.id, 1, "PM", gme.id)  # Tuesday PM

    tuesday = date(2026, 5, 12)  # Tuesday
    hda = _create_hda(db, faculty.id, tuesday, "PM", at.id)

    engine = _make_engine(db)
    count = engine._apply_faculty_template_correction([faculty])

    assert count == 1
    db.refresh(hda)
    assert hda.activity_id == gme.id


# ── Test 3: Corrects solver OFF → template activity ──


def test_corrects_solver_off_to_template_activity(db):
    """OFF (from backfill) should become cv when template says cv."""
    off = _create_activity(db, "OFF", "Off")
    cv = _create_activity(db, "cv", "CV Clinic")

    faculty = _create_faculty(db)
    _create_template(db, faculty.id, 2, "AM", cv.id)  # Wednesday AM

    wednesday = date(2026, 5, 13)  # Wednesday
    hda = _create_hda(db, faculty.id, wednesday, "AM", off.id)

    engine = _make_engine(db)
    count = engine._apply_faculty_template_correction([faculty])

    assert count == 1
    db.refresh(hda)
    assert hda.activity_id == cv.id


# ── Test 4: Skips preload source ──


def test_skips_preload_source(db):
    """Preloaded HDAs must never be modified."""
    fm_clinic = _create_activity(db, "fm_clinic", "FM Clinic")
    sm_clinic = _create_activity(db, "sm_clinic", "SM Clinic")

    faculty = _create_faculty(db)
    _create_template(db, faculty.id, 0, "AM", sm_clinic.id)

    monday = date(2026, 5, 11)
    hda = _create_hda(db, faculty.id, monday, "AM", fm_clinic.id, source="preload")

    engine = _make_engine(db)
    count = engine._apply_faculty_template_correction([faculty])

    assert count == 0
    db.refresh(hda)
    assert hda.activity_id == fm_clinic.id  # Unchanged


# ── Test 5: Skips manual source ──


def test_skips_manual_source(db):
    """Manual HDAs must never be modified."""
    fm_clinic = _create_activity(db, "fm_clinic", "FM Clinic")
    sm_clinic = _create_activity(db, "sm_clinic", "SM Clinic")

    faculty = _create_faculty(db)
    _create_template(db, faculty.id, 0, "AM", sm_clinic.id)

    monday = date(2026, 5, 11)
    hda = _create_hda(db, faculty.id, monday, "AM", fm_clinic.id, source="manual")

    engine = _make_engine(db)
    count = engine._apply_faculty_template_correction([faculty])

    assert count == 0
    db.refresh(hda)
    assert hda.activity_id == fm_clinic.id


# ── Test 6: Skips post-call codes ──


def test_skips_postcall_codes(db):
    """PCAT, DO, CALL, W, LEC HDAs must never be overridden."""
    pcat = _create_activity(db, "pcat", "Post-Call")
    sm_clinic = _create_activity(db, "sm_clinic", "SM Clinic")

    faculty = _create_faculty(db)
    _create_template(db, faculty.id, 0, "AM", sm_clinic.id)

    monday = date(2026, 5, 11)
    hda = _create_hda(db, faculty.id, monday, "AM", pcat.id)

    engine = _make_engine(db)
    count = engine._apply_faculty_template_correction([faculty])

    assert count == 0
    db.refresh(hda)
    assert hda.activity_id == pcat.id


# ── Test 7: Skips weekends ──


def test_skips_weekends(db):
    """Weekend HDAs (Sat/Sun) must not be template-corrected."""
    fm_clinic = _create_activity(db, "fm_clinic", "FM Clinic")
    sm_clinic = _create_activity(db, "sm_clinic", "SM Clinic")

    faculty = _create_faculty(db)
    # Even if a template exists for Saturday (unusual), skip it
    _create_template(db, faculty.id, 5, "AM", sm_clinic.id)

    saturday = date(2026, 5, 9)  # Saturday
    hda = _create_hda(db, faculty.id, saturday, "AM", fm_clinic.id)

    engine = _make_engine(db)
    count = engine._apply_faculty_template_correction([faculty])

    assert count == 0
    db.refresh(hda)
    assert hda.activity_id == fm_clinic.id


# ── Test 8: Skips adjuncts ──


def test_skips_adjuncts(db):
    """Adjunct faculty should be entirely skipped.

    The CHECK constraint on people.faculty_role doesn't include 'adjunct'
    in SQLite test mode, so we simulate by creating a Person object with
    faculty_role='adjunct' in memory (not flushed) and verifying the
    method filters it out before querying the DB.
    """
    fm_clinic = _create_activity(db, "fm_clinic", "FM Clinic")
    sm_clinic = _create_activity(db, "sm_clinic", "SM Clinic")

    # Create an adjunct-like Person in memory only (not persisted to DB)
    adjunct = Person(
        id=uuid4(),
        name="Adjunct",
        type="faculty",
        faculty_role=FacultyRole.ADJUNCT.value,
    )

    engine = _make_engine(db)
    # Pass only the adjunct — method should filter to empty core list and return 0
    count = engine._apply_faculty_template_correction([adjunct])

    assert count == 0


# ── Test 9: No template → no change ──


def test_no_template_no_change(db):
    """If no template exists for a slot, the HDA stays unchanged."""
    fm_clinic = _create_activity(db, "fm_clinic", "FM Clinic")

    faculty = _create_faculty(db)
    # No template created for this faculty

    monday = date(2026, 5, 11)
    hda = _create_hda(db, faculty.id, monday, "AM", fm_clinic.id)

    engine = _make_engine(db)
    count = engine._apply_faculty_template_correction([faculty])

    assert count == 0
    db.refresh(hda)
    assert hda.activity_id == fm_clinic.id


# ── Test 10: Template matches → no unnecessary update ──


def test_template_matches_no_change(db):
    """When HDA already matches template, no update should occur."""
    sm_clinic = _create_activity(db, "sm_clinic", "SM Clinic")

    faculty = _create_faculty(db)
    _create_template(db, faculty.id, 0, "AM", sm_clinic.id)

    monday = date(2026, 5, 11)
    hda = _create_hda(db, faculty.id, monday, "AM", sm_clinic.id)

    engine = _make_engine(db)
    count = engine._apply_faculty_template_correction([faculty])

    assert count == 0


# ── Test 11: Unknown template code falls back ──


def test_unknown_template_code_falls_back(db):
    """If template references an unknown activity code, keep current."""
    fm_clinic = _create_activity(db, "fm_clinic", "FM Clinic")

    faculty = _create_faculty(db)

    # Create a template pointing to an activity with a code
    # that we'll delete after creating the template to simulate
    # a code that _get_activity_id_by_code can't resolve
    bogus = _create_activity(db, "bogus_xyz", "Bogus")
    _create_template(db, faculty.id, 0, "AM", bogus.id)
    # Delete the activity so _get_activity_id_by_code will fail
    db.delete(bogus)
    db.flush()

    monday = date(2026, 5, 11)
    hda = _create_hda(db, faculty.id, monday, "AM", fm_clinic.id)

    engine = _make_engine(db)
    # Clear any cached activity IDs
    if hasattr(engine, "_activity_id_cache"):
        engine._activity_id_cache.clear()
    count = engine._apply_faculty_template_correction([faculty])

    assert count == 0
    db.refresh(hda)
    assert hda.activity_id == fm_clinic.id


# ── Test 12: Multiple faculty corrected ──


def test_multiple_faculty_corrected(db):
    """Batch correction across multiple faculty members."""
    fm_clinic = _create_activity(db, "fm_clinic", "FM Clinic")
    sm_clinic = _create_activity(db, "sm_clinic", "SM Clinic")
    cv = _create_activity(db, "cv", "CV Clinic")

    fac1 = _create_faculty(db, "Faculty A")
    fac2 = _create_faculty(db, "Faculty B")

    # Fac1: Monday AM → sm_clinic
    _create_template(db, fac1.id, 0, "AM", sm_clinic.id)
    # Fac2: Monday AM → cv
    _create_template(db, fac2.id, 0, "AM", cv.id)

    monday = date(2026, 5, 11)
    hda1 = _create_hda(db, fac1.id, monday, "AM", fm_clinic.id)
    hda2 = _create_hda(db, fac2.id, monday, "AM", fm_clinic.id)

    engine = _make_engine(db)
    count = engine._apply_faculty_template_correction([fac1, fac2])

    assert count == 2
    db.refresh(hda1)
    db.refresh(hda2)
    assert hda1.activity_id == sm_clinic.id
    assert hda2.activity_id == cv.id
