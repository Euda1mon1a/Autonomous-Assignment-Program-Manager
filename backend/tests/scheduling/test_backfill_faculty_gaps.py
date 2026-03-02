"""Tests for SchedulingEngine._backfill_faculty_gaps() + ARCH-005.

Verifies that:
- Empty faculty slots are backfilled with OFF (weekday) or W (weekend)
- Adjunct faculty are excluded from backfill
- Existing HDAs are never overwritten
- ARCH-005 runtime assertion fires when >50% of a faculty member's
  slots are gaps (indicating over-constraining)
"""

from datetime import date
from unittest.mock import MagicMock, call, patch
from uuid import uuid4

import pytest

from app.models.activity import Activity, ActivityCategory
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


def _make_blocks(db, dates_and_tods: list[tuple[date, str, bool]]):
    """Create Block rows in DB and return them.

    Each tuple: (date, time_of_day, is_weekend)
    """
    from app.models.block import Block

    blocks = []
    for d, tod, weekend in dates_and_tods:
        b = Block(
            id=uuid4(),
            date=d,
            time_of_day=tod,
            block_number=12,
            is_weekend=weekend,
        )
        db.add(b)
        blocks.append(b)
    db.flush()
    return blocks


# ── Test 1: Weekday gaps get OFF, weekend gaps get W ──


def test_backfill_assigns_off_weekday_w_weekend(db):
    """Empty weekday slots -> OFF, empty weekend slots -> W."""
    off = _create_activity(db, "off", "Day Off")
    w = _create_activity(db, "W", "Weekend")
    faculty = _create_faculty(db, "Dr. Alpha")

    blocks = _make_blocks(
        db,
        [
            (date(2026, 5, 11), "AM", False),  # Monday
            (date(2026, 5, 11), "PM", False),  # Monday
            (date(2026, 5, 17), "AM", True),  # Saturday
        ],
    )

    engine = _make_engine(db)
    engine._backfill_faculty_gaps([faculty], blocks)

    hdas = (
        db.query(HalfDayAssignment)
        .filter(HalfDayAssignment.person_id == faculty.id)
        .order_by(HalfDayAssignment.date, HalfDayAssignment.time_of_day)
        .all()
    )
    assert len(hdas) == 3
    assert hdas[0].activity_id == off.id  # Monday AM -> OFF
    assert hdas[1].activity_id == off.id  # Monday PM -> OFF
    assert hdas[2].activity_id == w.id  # Saturday AM -> W
    for hda in hdas:
        assert hda.source == AssignmentSource.SOLVER.value


# ── Test 2: Existing HDAs are never overwritten ──


def test_backfill_skips_existing_hdas(db):
    """Slots with existing HDAs should not be touched."""
    off = _create_activity(db, "off", "Day Off")
    _create_activity(db, "W", "Weekend")
    clinic = _create_activity(db, "fm_clinic", "FM Clinic")
    faculty = _create_faculty(db, "Dr. Beta")

    blocks = _make_blocks(
        db,
        [
            (date(2026, 5, 11), "AM", False),
            (date(2026, 5, 11), "PM", False),
        ],
    )

    # Pre-existing HDA for Monday AM
    _create_hda(db, faculty.id, date(2026, 5, 11), "AM", clinic.id)

    engine = _make_engine(db)
    engine._backfill_faculty_gaps([faculty], blocks)

    hdas = (
        db.query(HalfDayAssignment)
        .filter(HalfDayAssignment.person_id == faculty.id)
        .order_by(HalfDayAssignment.time_of_day)
        .all()
    )
    assert len(hdas) == 2
    # AM was pre-existing -> still fm_clinic
    am_hda = [h for h in hdas if h.time_of_day == "AM"][0]
    assert am_hda.activity_id == clinic.id
    # PM was empty -> backfilled with OFF
    pm_hda = [h for h in hdas if h.time_of_day == "PM"][0]
    assert pm_hda.activity_id == off.id


# ── Test 3: Adjunct faculty excluded ──


def test_backfill_excludes_adjunct_faculty(db):
    """Adjunct faculty should never be backfilled (hand-jammed).

    Note: SQLite CHECK constraint on people.faculty_role doesn't include
    'adjunct', so we use a mock Person to test the filter logic.
    """
    _create_activity(db, "off", "Day Off")
    _create_activity(db, "W", "Weekend")

    # Create a mock adjunct since SQLite CHECK doesn't allow 'adjunct'
    adjunct = MagicMock(spec=Person)
    adjunct.id = uuid4()
    adjunct.name = "Dr. Adjunct"
    adjunct.faculty_role = FacultyRole.ADJUNCT.value

    blocks = _make_blocks(
        db,
        [
            (date(2026, 5, 11), "AM", False),
        ],
    )

    engine = _make_engine(db)
    engine._backfill_faculty_gaps([adjunct], blocks)

    hdas = db.query(HalfDayAssignment).all()
    assert len(hdas) == 0


# ── Test 4: Empty faculty list is a no-op ──


def test_backfill_empty_faculty_noop(db):
    """No faculty -> no work, no crash."""
    _create_activity(db, "off", "Day Off")
    _create_activity(db, "W", "Weekend")

    blocks = _make_blocks(
        db,
        [
            (date(2026, 5, 11), "AM", False),
        ],
    )

    engine = _make_engine(db)
    engine._backfill_faculty_gaps([], blocks)

    count = db.query(HalfDayAssignment).count()
    assert count == 0


# ── Test 5: ARCH-005 fires when >50% gaps ──


def test_arch005_logs_error_when_over_50pct_gaps(db):
    """ARCH-005: >50% backfilled slots triggers error log."""
    _create_activity(db, "off", "Day Off")
    _create_activity(db, "W", "Weekend")
    clinic = _create_activity(db, "fm_clinic", "FM Clinic")
    faculty = _create_faculty(db, "Dr. Gamma")

    # 4 blocks: pre-fill only 1, leave 3 empty -> 75% gaps
    blocks = _make_blocks(
        db,
        [
            (date(2026, 5, 11), "AM", False),
            (date(2026, 5, 11), "PM", False),
            (date(2026, 5, 12), "AM", False),
            (date(2026, 5, 12), "PM", False),
        ],
    )
    _create_hda(db, faculty.id, date(2026, 5, 11), "AM", clinic.id)

    engine = _make_engine(db)
    with patch("app.scheduling.engine.logger") as mock_logger:
        engine._backfill_faculty_gaps([faculty], blocks)

    # Find the ARCH-005 error call
    error_calls = [c for c in mock_logger.error.call_args_list if "ARCH-005" in str(c)]
    assert len(error_calls) == 1
    args = error_calls[0][0]
    assert "Dr. Gamma" in str(args)
    assert "3/4" in str(args) or (args[2] == 3 and args[3] == 4)


# ── Test 6: ARCH-005 does NOT fire when <=50% gaps ──


def test_arch005_silent_when_under_50pct_gaps(db):
    """ARCH-005 should not fire when gap percentage is <= 50%."""
    _create_activity(db, "off", "Day Off")
    _create_activity(db, "W", "Weekend")
    clinic = _create_activity(db, "fm_clinic", "FM Clinic")
    faculty = _create_faculty(db, "Dr. Delta")

    # 4 blocks: pre-fill 2, leave 2 empty -> exactly 50%
    blocks = _make_blocks(
        db,
        [
            (date(2026, 5, 11), "AM", False),
            (date(2026, 5, 11), "PM", False),
            (date(2026, 5, 12), "AM", False),
            (date(2026, 5, 12), "PM", False),
        ],
    )
    _create_hda(db, faculty.id, date(2026, 5, 11), "AM", clinic.id)
    _create_hda(db, faculty.id, date(2026, 5, 11), "PM", clinic.id)

    engine = _make_engine(db)
    with patch("app.scheduling.engine.logger") as mock_logger:
        engine._backfill_faculty_gaps([faculty], blocks)

    error_calls = [c for c in mock_logger.error.call_args_list if "ARCH-005" in str(c)]
    assert len(error_calls) == 0


# ── Test 7: ARCH-005 reports per-faculty, not aggregate ──


def test_arch005_per_faculty_reporting(db):
    """Only the over-constrained faculty should be flagged, not all."""
    _create_activity(db, "off", "Day Off")
    _create_activity(db, "W", "Weekend")
    clinic = _create_activity(db, "fm_clinic", "FM Clinic")

    healthy = _create_faculty(db, "Dr. Healthy")
    sick = _create_faculty(db, "Dr. Sick")

    blocks = _make_blocks(
        db,
        [
            (date(2026, 5, 11), "AM", False),
            (date(2026, 5, 11), "PM", False),
            (date(2026, 5, 12), "AM", False),
            (date(2026, 5, 12), "PM", False),
        ],
    )

    # Healthy: 3/4 pre-filled -> only 25% gaps -> no ARCH-005
    _create_hda(db, healthy.id, date(2026, 5, 11), "AM", clinic.id)
    _create_hda(db, healthy.id, date(2026, 5, 11), "PM", clinic.id)
    _create_hda(db, healthy.id, date(2026, 5, 12), "AM", clinic.id)

    # Sick: 0/4 pre-filled -> 100% gaps -> ARCH-005
    engine = _make_engine(db)
    with patch("app.scheduling.engine.logger") as mock_logger:
        engine._backfill_faculty_gaps([healthy, sick], blocks)

    error_calls = [c for c in mock_logger.error.call_args_list if "ARCH-005" in str(c)]
    assert len(error_calls) == 1
    assert "Dr. Sick" in str(error_calls[0])
    assert "Dr. Healthy" not in str(error_calls[0])
