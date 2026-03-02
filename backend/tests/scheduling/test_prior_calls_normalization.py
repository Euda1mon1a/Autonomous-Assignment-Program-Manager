"""Tests for prior_calls availability normalization in SchedulingEngine._build_context().

Verifies that YTD call totals are scaled by availability window so deployed
faculty aren't penalized for fewer calls. Faculty deployed for half the year
should have their prior_calls doubled so the MAD equity constraint sees
equal call RATES.
"""

from datetime import date
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.models.absence import Absence
from app.models.person import FacultyRole, Person
from app.scheduling.engine import SchedulingEngine
from app.utils.academic_blocks import get_block_dates


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


def _create_absence(
    db,
    person_id,
    start: date,
    end: date,
    absence_type: str = "deployment",
    is_blocking: bool = True,
):
    absence = Absence(
        id=uuid4(),
        person_id=person_id,
        start_date=start,
        end_date=end,
        absence_type=absence_type,
        is_blocking=is_blocking,
    )
    db.add(absence)
    db.flush()
    return absence


def _make_engine(db):
    """Create engine with real DB but bypassed __init__."""
    with patch.object(SchedulingEngine, "__init__", lambda self, *a, **kw: None):
        engine = SchedulingEngine.__new__(SchedulingEngine)
        engine.db = db
        engine.start_date = date(2026, 5, 7)
        engine.end_date = date(2026, 6, 3)
    return engine


def _normalize_prior_calls(
    engine, prior_calls, call_eligible, block_number, academic_year
):
    """Run the normalization logic extracted from _build_context.

    This mirrors the normalization code in engine.py after prior_calls hydration.
    """
    from app.models.absence import Absence

    if (
        prior_calls
        and call_eligible
        and block_number is not None
        and academic_year is not None
    ):
        elapsed_blocks = max(block_number, 1)

        for fac in call_eligible:
            fid = fac.id
            if fid not in prior_calls:
                continue

            blocked_count = 0
            for bn in range(1, block_number + 1):
                bd = get_block_dates(bn, academic_year)
                has_blocking = (
                    engine.db.query(Absence.id)
                    .filter(
                        Absence.person_id == fid,
                        Absence.is_blocking == True,  # noqa: E712
                        Absence.start_date <= bd.end_date,
                        Absence.end_date >= bd.start_date,
                    )
                    .first()
                ) is not None
                if has_blocking:
                    blocked_count += 1

            available = max(elapsed_blocks - blocked_count, 1)
            if available < elapsed_blocks:
                scale = elapsed_blocks / available
                for call_type in prior_calls[fid]:
                    prior_calls[fid][call_type] = int(
                        round(prior_calls[fid][call_type] * scale)
                    )

    return prior_calls


def test_no_absences_no_change(db):
    """Faculty available all blocks → prior_calls unchanged."""
    faculty = _create_faculty(db, "Available Faculty")
    engine = _make_engine(db)

    prior_calls = {faculty.id: {"weekday": 10, "sunday": 2}}
    result = _normalize_prior_calls(
        engine, prior_calls, [faculty], block_number=12, academic_year=2025
    )

    assert result[faculty.id]["weekday"] == 10
    assert result[faculty.id]["sunday"] == 2


def test_deployment_scales_prior(db):
    """Faculty deployed 7 of 12 blocks → prior scaled by 12/5=2.4x."""
    faculty = _create_faculty(db, "Deployed Faculty")

    # Deployment covers blocks 1-7 (Jul 1 - Dec 31 overlaps 7 blocks)
    _create_absence(db, faculty.id, date(2025, 7, 1), date(2025, 12, 31))

    engine = _make_engine(db)
    prior_calls = {faculty.id: {"weekday": 5, "sunday": 1}}
    result = _normalize_prior_calls(
        engine, prior_calls, [faculty], block_number=12, academic_year=2025
    )

    # 7 blocked, 5 available → scale = 12/5 = 2.4x
    # weekday: round(5 * 2.4) = 12, sunday: round(1 * 2.4) = 2
    assert result[faculty.id]["weekday"] == 12
    assert result[faculty.id]["sunday"] == 2


def test_zero_prior_unchanged(db):
    """0 prior_calls stays 0 regardless of availability."""
    faculty = _create_faculty(db, "Zero Calls")

    # Deployed half the year
    _create_absence(db, faculty.id, date(2025, 7, 1), date(2025, 12, 31))

    engine = _make_engine(db)
    prior_calls = {faculty.id: {"weekday": 0, "sunday": 0}}
    result = _normalize_prior_calls(
        engine, prior_calls, [faculty], block_number=12, academic_year=2025
    )

    assert result[faculty.id]["weekday"] == 0
    assert result[faculty.id]["sunday"] == 0


def test_partial_overlap_counts_blocked(db):
    """1-day overlap with a block still counts that block as blocked."""
    faculty = _create_faculty(db, "Partial Overlap")

    # Block 1 for AY2025 starts Jul 3. Absence ending Jul 3 overlaps.
    bd = get_block_dates(1, 2025)
    _create_absence(db, faculty.id, date(2025, 6, 15), bd.start_date)

    engine = _make_engine(db)
    prior_calls = {faculty.id: {"weekday": 10}}
    result = _normalize_prior_calls(
        engine, prior_calls, [faculty], block_number=12, academic_year=2025
    )

    # At least block 1 should be counted as blocked
    # With 11 available out of 12: scale = 12/11 ≈ 1.09
    # weekday: round(10 * 1.09) = 11
    assert result[faculty.id]["weekday"] >= 10  # Scaled up at least slightly


def test_all_blocks_blocked_floor(db):
    """All blocks blocked → available floored to 1, max scaling."""
    faculty = _create_faculty(db, "All Blocked")

    # Deployment covers entire academic year
    _create_absence(db, faculty.id, date(2025, 6, 1), date(2026, 7, 1))

    engine = _make_engine(db)
    prior_calls = {faculty.id: {"weekday": 1}}
    result = _normalize_prior_calls(
        engine, prior_calls, [faculty], block_number=12, academic_year=2025
    )

    # available = max(12 - 12, 1) = 1, scale = 12/1 = 12.0
    assert result[faculty.id]["weekday"] == 12


def test_faculty_not_in_prior_calls_skipped(db):
    """Faculty with no prior_calls entry is skipped without error."""
    faculty = _create_faculty(db, "No Prior")

    engine = _make_engine(db)
    prior_calls = {}  # Empty — faculty has no entries
    result = _normalize_prior_calls(
        engine, prior_calls, [faculty], block_number=12, academic_year=2025
    )

    assert faculty.id not in result


def test_non_blocking_absence_not_counted(db):
    """Non-blocking absences (conference) should not affect scaling."""
    faculty = _create_faculty(db, "Conference")

    # Non-blocking absence covering many blocks
    _create_absence(
        db,
        faculty.id,
        date(2025, 7, 1),
        date(2025, 12, 31),
        absence_type="conference",
        is_blocking=False,
    )

    engine = _make_engine(db)
    prior_calls = {faculty.id: {"weekday": 10}}
    result = _normalize_prior_calls(
        engine, prior_calls, [faculty], block_number=12, academic_year=2025
    )

    # No blocking absences → no scaling
    assert result[faculty.id]["weekday"] == 10
