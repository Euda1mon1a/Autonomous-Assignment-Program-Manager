"""Tests for SchedulingEngine._get_call_eligible_faculty() absence filtering.

Verifies that faculty with blocking absences covering the ENTIRE block
date range are excluded from call eligibility. Partial absences within
the block are handled per-night by OvernightCallGenerationConstraint.
"""

from datetime import date
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.models.absence import Absence
from app.models.person import FacultyRole, Person
from app.scheduling.engine import SchedulingEngine


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


def test_excludes_faculty_with_blocking_absence(db):
    """Faculty deployed during block should be excluded from call eligibility."""
    deployed = _create_faculty(db, "Deployed Faculty")
    available = _create_faculty(db, "Available Faculty")

    # Deployment covers entire block
    _create_absence(db, deployed.id, date(2026, 2, 21), date(2026, 6, 30))

    engine = _make_engine(db)
    eligible = engine._get_call_eligible_faculty([deployed, available])

    assert len(eligible) == 1
    assert eligible[0].id == available.id


def test_partial_overlap_still_eligible(db):
    """Faculty with partial blocking absence stays eligible at block level.

    Per-night exclusion is handled by OvernightCallGenerationConstraint.
    """
    faculty = _create_faculty(db, "Partial Overlap")

    # Absence covers first 2 weeks of block — NOT the entire block
    _create_absence(db, faculty.id, date(2026, 5, 1), date(2026, 5, 20))

    engine = _make_engine(db)
    eligible = engine._get_call_eligible_faculty([faculty])

    # Partial absence → still eligible (per-night blocking handles exclusion)
    assert len(eligible) == 1
    assert eligible[0].id == faculty.id


def test_includes_faculty_without_absence(db):
    """Faculty with no absences should be eligible."""
    faculty = _create_faculty(db, "No Absence")

    engine = _make_engine(db)
    eligible = engine._get_call_eligible_faculty([faculty])

    assert len(eligible) == 1
    assert eligible[0].id == faculty.id


def test_includes_non_blocking_absence(db):
    """Faculty with non-blocking absence (vacation day) should still be eligible."""
    faculty = _create_faculty(db, "On Vacation")

    _create_absence(
        db,
        faculty.id,
        date(2026, 5, 15),
        date(2026, 5, 15),
        absence_type="conference",
        is_blocking=False,
    )

    engine = _make_engine(db)
    eligible = engine._get_call_eligible_faculty([faculty])

    assert len(eligible) == 1


def test_excludes_adjuncts_still(db):
    """Adjunct filtering should still work alongside absence filtering."""
    # Can't create adjuncts in SQLite due to CHECK constraint,
    # so test with in-memory Person
    adjunct = Person(
        id=uuid4(),
        name="Adjunct",
        type="faculty",
        faculty_role=FacultyRole.ADJUNCT.value,
    )

    engine = _make_engine(db)
    eligible = engine._get_call_eligible_faculty([adjunct])

    assert len(eligible) == 0


def test_absence_outside_block_does_not_exclude(db):
    """Absence completely outside block date range should not exclude faculty."""
    faculty = _create_faculty(db, "Past Absence")

    # Absence ends before block starts
    _create_absence(db, faculty.id, date(2026, 3, 1), date(2026, 4, 30))

    engine = _make_engine(db)
    eligible = engine._get_call_eligible_faculty([faculty])

    assert len(eligible) == 1


def test_multiple_faculty_mixed(db):
    """Mix of available, deployed, and partially-absent faculty.

    Only fully-deployed faculty (absence covers entire block) are excluded.
    Partially-absent faculty remain eligible for per-night blocking.
    """
    available1 = _create_faculty(db, "Available 1")
    available2 = _create_faculty(db, "Available 2")
    deployed = _create_faculty(db, "Deployed")
    on_leave = _create_faculty(db, "On Leave")

    # Deployed covers entire block (Apr 1 - Jul 1 ⊇ May 7 - Jun 3)
    _create_absence(db, deployed.id, date(2026, 4, 1), date(2026, 7, 1), "deployment")
    # On-leave covers only part of block (May 10-25 ⊄ May 7 - Jun 3)
    _create_absence(
        db,
        on_leave.id,
        date(2026, 5, 10),
        date(2026, 5, 25),
        "maternity_paternity",
    )

    engine = _make_engine(db)
    eligible = engine._get_call_eligible_faculty(
        [available1, available2, deployed, on_leave]
    )

    # 3 eligible: 2 available + on_leave (partial). Deployed excluded.
    assert len(eligible) == 3
    eligible_ids = {f.id for f in eligible}
    assert available1.id in eligible_ids
    assert available2.id in eligible_ids
    assert on_leave.id in eligible_ids
    assert deployed.id not in eligible_ids


def test_empty_faculty_list(db):
    """Empty faculty list should return empty."""
    engine = _make_engine(db)
    eligible = engine._get_call_eligible_faculty([])

    assert eligible == []
