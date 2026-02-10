"""Tests for faculty clinic and supervision constraints (pure logic, no DB required)."""

import math
from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.faculty_clinic import (
    DEFAULT_CLINIC_CAPS,
    FacultyClinicCapConstraint,
    FacultySupervisionConstraint,
)


# ==================== Helpers ====================


def _person(pid=None, name="Faculty", **kwargs):
    """Build a mock person with optional attributes."""
    ns = SimpleNamespace(id=pid or uuid4(), name=name)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _block(bid=None, block_date=None, time_of_day="AM"):
    """Build a mock block."""
    return SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 3),
        time_of_day=time_of_day,
    )


def _context(
    residents=None,
    blocks=None,
    faculty=None,
    templates=None,
    start_date=None,
    end_date=None,
):
    """Build a SchedulingContext with optional date range."""
    ctx = SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )
    if start_date is not None:
        ctx.start_date = start_date
    if end_date is not None:
        ctx.end_date = end_date
    return ctx


def _clinic_assignment(person_id, assign_date, activity_code="C", **kwargs):
    """Build a mock clinic assignment with date and activity_code."""
    ns = SimpleNamespace(
        person_id=person_id,
        date=assign_date,
        activity_code=activity_code,
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _supervision_assignment(
    person_id,
    assign_date,
    time_of_day="AM",
    person_type="resident",
    activity_code="fm_clinic",
    pgy_level=None,
):
    """Build a mock assignment for supervision constraint."""
    return SimpleNamespace(
        person_id=person_id,
        date=assign_date,
        time_of_day=time_of_day,
        person_type=person_type,
        activity_code=activity_code,
        pgy_level=pgy_level,
    )


# ==================== Constants Tests ====================


class TestFacultyClinicConstants:
    """Test module-level constants."""

    def test_default_caps(self):
        assert DEFAULT_CLINIC_CAPS == (0, 4)


# ==================== FacultyClinicCapConstraint Init ====================


class TestClinicCapInit:
    """Test FacultyClinicCapConstraint initialization."""

    def test_name(self):
        c = FacultyClinicCapConstraint()
        assert c.name == "FacultyClinicCap"

    def test_type(self):
        c = FacultyClinicCapConstraint()
        assert c.constraint_type == ConstraintType.CAPACITY

    def test_priority(self):
        c = FacultyClinicCapConstraint()
        assert c.priority == ConstraintPriority.HIGH

    def test_default_weight(self):
        c = FacultyClinicCapConstraint()
        assert c.weight == 50.0

    def test_custom_weight(self):
        c = FacultyClinicCapConstraint(weight=100.0)
        assert c.weight == 100.0


# ==================== _get_caps Tests ====================


class TestGetCaps:
    """Test _get_caps helper."""

    def test_db_fields_take_precedence(self):
        """Person-specific DB columns used when both set."""
        c = FacultyClinicCapConstraint()
        f = _person(
            name="Dr. Test",
            min_clinic_halfdays_per_week=1,
            max_clinic_halfdays_per_week=3,
        )
        assert c._get_caps(f) == (1, 3)

    def test_fallback_to_default(self):
        """Falls back to DEFAULT_CLINIC_CAPS when no DB values."""
        c = FacultyClinicCapConstraint()
        f = _person(name="Dr. Test")
        assert c._get_caps(f) == DEFAULT_CLINIC_CAPS

    def test_no_db_fields_uses_default(self):
        """Faculty without DB fields uses DEFAULT_CLINIC_CAPS."""
        c = FacultyClinicCapConstraint()
        f = _person(name="Dr. Unknown")
        assert c._get_caps(f) == DEFAULT_CLINIC_CAPS

    def test_db_min_none_max_set_falls_back(self):
        """If only one DB field is set (not both), falls back to default."""
        c = FacultyClinicCapConstraint()
        f = _person(
            name="Dr. Test",
            min_clinic_halfdays_per_week=None,
            max_clinic_halfdays_per_week=3,
        )
        assert c._get_caps(f) == DEFAULT_CLINIC_CAPS

    def test_empty_name(self):
        c = FacultyClinicCapConstraint()
        f = _person(name="")
        assert c._get_caps(f) == DEFAULT_CLINIC_CAPS


# ==================== _get_week_dates Tests ====================


class TestGetWeekDates:
    """Test _get_week_dates helper (7-day windows)."""

    def test_single_week(self):
        c = FacultyClinicCapConstraint()
        result = c._get_week_dates(date(2025, 3, 3), date(2025, 3, 9))
        assert len(result) == 1
        assert result[0] == (date(2025, 3, 3), date(2025, 3, 9))

    def test_two_weeks(self):
        c = FacultyClinicCapConstraint()
        result = c._get_week_dates(date(2025, 3, 3), date(2025, 3, 16))
        assert len(result) == 2
        assert result[0] == (date(2025, 3, 3), date(2025, 3, 9))
        assert result[1] == (date(2025, 3, 10), date(2025, 3, 16))

    def test_partial_week(self):
        """End date mid-week truncates last window."""
        c = FacultyClinicCapConstraint()
        result = c._get_week_dates(date(2025, 3, 3), date(2025, 3, 12))
        assert len(result) == 2
        assert result[1][1] == date(2025, 3, 12)  # Truncated to end_date

    def test_single_day(self):
        c = FacultyClinicCapConstraint()
        result = c._get_week_dates(date(2025, 3, 3), date(2025, 3, 3))
        assert len(result) == 1
        assert result[0] == (date(2025, 3, 3), date(2025, 3, 3))

    def test_four_weeks(self):
        c = FacultyClinicCapConstraint()
        result = c._get_week_dates(date(2025, 3, 3), date(2025, 3, 30))
        assert len(result) == 4


# ==================== FacultyClinicCapConstraint validate Tests ====================


class TestClinicCapValidate:
    """Test FacultyClinicCapConstraint.validate method."""

    def test_no_date_range_satisfied(self):
        """No start/end date -> satisfied immediately."""
        c = FacultyClinicCapConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_no_assignments_satisfied(self):
        c = FacultyClinicCapConstraint()
        ctx = _context(start_date=date(2025, 3, 3), end_date=date(2025, 3, 9))
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_within_max_satisfied(self):
        """Faculty within max cap -> satisfied."""
        c = FacultyClinicCapConstraint()
        fac = _person(
            name="Dr. A", min_clinic_halfdays_per_week=0, max_clinic_halfdays_per_week=2
        )
        ctx = _context(
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 9),
        )
        assignments = [
            _clinic_assignment(fac.id, date(2025, 3, 3), "C"),
            _clinic_assignment(fac.id, date(2025, 3, 4), "C"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_exceeds_max_violation(self):
        """Faculty exceeds max cap -> HIGH violation."""
        c = FacultyClinicCapConstraint()
        fac = _person(
            name="Dr. B", min_clinic_halfdays_per_week=0, max_clinic_halfdays_per_week=1
        )
        ctx = _context(
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 9),
        )
        assignments = [
            _clinic_assignment(fac.id, date(2025, 3, 3), "C"),
            _clinic_assignment(fac.id, date(2025, 3, 4), "C"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "HIGH"
        assert "Dr. B" in result.violations[0].message

    def test_zero_max_allows_zero_satisfied(self):
        """Faculty with max 0 and no clinic assignments -> satisfied."""
        c = FacultyClinicCapConstraint()
        fac = _person(
            name="Dr. C", min_clinic_halfdays_per_week=0, max_clinic_halfdays_per_week=0
        )
        ctx = _context(
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 9),
        )
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_fm_clinic_code_counted(self):
        """Activity code 'fm_clinic' is also counted."""
        c = FacultyClinicCapConstraint()
        fac = _person(
            name="Dr. B", min_clinic_halfdays_per_week=0, max_clinic_halfdays_per_week=1
        )
        ctx = _context(
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 9),
        )
        assignments = [
            _clinic_assignment(fac.id, date(2025, 3, 3), "fm_clinic"),
            _clinic_assignment(fac.id, date(2025, 3, 4), "fm_clinic"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False

    def test_non_clinic_code_ignored(self):
        """Activity codes not in {'fm_clinic', 'C'} are ignored."""
        c = FacultyClinicCapConstraint()
        fac = _person(
            name="Dr. B", min_clinic_halfdays_per_week=0, max_clinic_halfdays_per_week=1
        )
        ctx = _context(
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 9),
        )
        assignments = [
            _clinic_assignment(fac.id, date(2025, 3, 3), "at"),
            _clinic_assignment(fac.id, date(2025, 3, 4), "pcat"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_min_violation_medium_severity(self):
        """Below minimum -> MEDIUM severity (still satisfied)."""
        c = FacultyClinicCapConstraint()
        fac = _person(
            name="Custom",
            min_clinic_halfdays_per_week=3,
            max_clinic_halfdays_per_week=4,
        )
        ctx = _context(
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 9),
        )
        assignments = [
            _clinic_assignment(fac.id, date(2025, 3, 3), "C"),
        ]
        result = c.validate(assignments, ctx)
        # satisfied is True because MEDIUM violations don't count
        assert result.satisfied is True
        assert len(result.violations) == 1
        assert result.violations[0].severity == "MEDIUM"

    def test_penalty_calculated_for_max_violation(self):
        """Penalty = weight * (count - max) for MAX violation."""
        c = FacultyClinicCapConstraint(weight=50.0)
        fac = _person(
            name="Dr. B", min_clinic_halfdays_per_week=0, max_clinic_halfdays_per_week=1
        )
        ctx = _context(
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 9),
        )
        assignments = [
            _clinic_assignment(fac.id, date(2025, 3, 3), "C"),
            _clinic_assignment(fac.id, date(2025, 3, 4), "C"),
            _clinic_assignment(fac.id, date(2025, 3, 5), "C"),
        ]
        result = c.validate(assignments, ctx)
        # 3 clinics, max 1 -> excess 2 -> penalty 50 * 2 = 100
        assert result.penalty == 100.0

    def test_penalty_calculated_for_min_violation(self):
        """Penalty = weight * 0.5 * (min - count) for MIN violation."""
        c = FacultyClinicCapConstraint(weight=50.0)
        fac = _person(
            name="Custom",
            min_clinic_halfdays_per_week=2,
            max_clinic_halfdays_per_week=4,
        )
        ctx = _context(
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 9),
        )
        assignments = [
            _clinic_assignment(fac.id, date(2025, 3, 3), "C"),
        ]
        result = c.validate(assignments, ctx)
        # 1 clinic, min 2 -> deficit 1 -> penalty 50 * 0.5 * 1 = 25
        assert result.penalty == 25.0

    def test_unknown_faculty_skipped(self):
        """Assignment for person not in faculty list is skipped."""
        c = FacultyClinicCapConstraint()
        unknown_id = uuid4()
        fac = _person(
            name="Dr. B", min_clinic_halfdays_per_week=0, max_clinic_halfdays_per_week=1
        )
        ctx = _context(
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 9),
        )
        assignments = [
            _clinic_assignment(unknown_id, date(2025, 3, 3), "C"),
            _clinic_assignment(unknown_id, date(2025, 3, 4), "C"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_multiple_weeks(self):
        """Violations checked per week independently."""
        c = FacultyClinicCapConstraint()
        fac = _person(
            name="Dr. B", min_clinic_halfdays_per_week=0, max_clinic_halfdays_per_week=1
        )
        ctx = _context(
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 16),
        )
        # Week 1: 1 clinic (ok), Week 2: 2 clinics (violation)
        assignments = [
            _clinic_assignment(fac.id, date(2025, 3, 3), "C"),
            _clinic_assignment(fac.id, date(2025, 3, 10), "C"),
            _clinic_assignment(fac.id, date(2025, 3, 11), "C"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1


# ==================== FacultySupervisionConstraint Init ====================


class TestSupervisionInit:
    """Test FacultySupervisionConstraint initialization."""

    def test_name(self):
        c = FacultySupervisionConstraint()
        assert c.name == "FacultySupervision"

    def test_type(self):
        c = FacultySupervisionConstraint()
        assert c.constraint_type == ConstraintType.SUPERVISION

    def test_priority(self):
        c = FacultySupervisionConstraint()
        assert c.priority == ConstraintPriority.CRITICAL

    def test_at_demand_constants(self):
        assert FacultySupervisionConstraint.AT_DEMAND == {1: 0.5, 2: 0.25, 3: 0.25}

    def test_at_coverage_codes(self):
        assert {"at", "pcat"} == FacultySupervisionConstraint.AT_COVERAGE_CODES


# ==================== FacultySupervisionConstraint validate Tests ====================


class TestSupervisionValidate:
    """Test FacultySupervisionConstraint.validate method."""

    def test_no_date_range_satisfied(self):
        c = FacultySupervisionConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_no_assignments_satisfied(self):
        c = FacultySupervisionConstraint()
        ctx = _context(start_date=date(2025, 3, 3), end_date=date(2025, 3, 9))
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_one_pgy1_one_faculty_satisfied(self):
        """1 PGY-1 resident needs 0.5 AT -> ceil(0.5) = 1 faculty needed."""
        c = FacultySupervisionConstraint()
        res = _person(name="Intern", pgy_level=1)
        fac = _person(name="Dr. A")
        ctx = _context(
            residents=[res],
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 3),
        )
        assignments = [
            _supervision_assignment(
                res.id, date(2025, 3, 3), "AM", "resident", "fm_clinic", 1
            ),
            _supervision_assignment(fac.id, date(2025, 3, 3), "AM", "faculty", "at"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_two_pgy1_one_faculty_satisfied(self):
        """2 PGY-1 residents need 1.0 AT -> ceil(1.0) = 1 faculty."""
        c = FacultySupervisionConstraint()
        res1 = _person(name="Intern A", pgy_level=1)
        res2 = _person(name="Intern B", pgy_level=1)
        fac = _person(name="Dr. A")
        ctx = _context(
            residents=[res1, res2],
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 3),
        )
        assignments = [
            _supervision_assignment(
                res1.id, date(2025, 3, 3), "AM", "resident", "fm_clinic", 1
            ),
            _supervision_assignment(
                res2.id, date(2025, 3, 3), "AM", "resident", "fm_clinic", 1
            ),
            _supervision_assignment(fac.id, date(2025, 3, 3), "AM", "faculty", "at"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_three_pgy1_one_faculty_violation(self):
        """3 PGY-1 residents need 1.5 AT -> ceil(1.5) = 2 faculty needed."""
        c = FacultySupervisionConstraint()
        res1 = _person(name="Int A", pgy_level=1)
        res2 = _person(name="Int B", pgy_level=1)
        res3 = _person(name="Int C", pgy_level=1)
        fac = _person(name="Dr. A")
        ctx = _context(
            residents=[res1, res2, res3],
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 3),
        )
        assignments = [
            _supervision_assignment(
                res1.id, date(2025, 3, 3), "AM", "resident", "fm_clinic", 1
            ),
            _supervision_assignment(
                res2.id, date(2025, 3, 3), "AM", "resident", "fm_clinic", 1
            ),
            _supervision_assignment(
                res3.id, date(2025, 3, 3), "AM", "resident", "fm_clinic", 1
            ),
            _supervision_assignment(fac.id, date(2025, 3, 3), "AM", "faculty", "at"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "CRITICAL"
        assert "deficit" in result.violations[0].message

    def test_four_pgy2_one_faculty_satisfied(self):
        """4 PGY-2 residents need 1.0 AT -> ceil(1.0) = 1 faculty."""
        c = FacultySupervisionConstraint()
        residents = [_person(name=f"R{i}", pgy_level=2) for i in range(4)]
        fac = _person(name="Dr. A")
        ctx = _context(
            residents=residents,
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 3),
        )
        assignments = [
            _supervision_assignment(
                r.id, date(2025, 3, 3), "AM", "resident", "fm_clinic", 2
            )
            for r in residents
        ] + [
            _supervision_assignment(fac.id, date(2025, 3, 3), "AM", "faculty", "at"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_five_pgy2_one_faculty_violation(self):
        """5 PGY-2 residents need 1.25 AT -> ceil(1.25) = 2 faculty needed."""
        c = FacultySupervisionConstraint()
        residents = [_person(name=f"R{i}", pgy_level=2) for i in range(5)]
        fac = _person(name="Dr. A")
        ctx = _context(
            residents=residents,
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 3),
        )
        assignments = [
            _supervision_assignment(
                r.id, date(2025, 3, 3), "AM", "resident", "fm_clinic", 2
            )
            for r in residents
        ] + [
            _supervision_assignment(fac.id, date(2025, 3, 3), "AM", "faculty", "at"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False

    def test_pcat_counts_as_coverage(self):
        """PCAT activity code counts as AT coverage."""
        c = FacultySupervisionConstraint()
        res = _person(name="Intern", pgy_level=1)
        fac = _person(name="Dr. A")
        ctx = _context(
            residents=[res],
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 3),
        )
        assignments = [
            _supervision_assignment(
                res.id, date(2025, 3, 3), "AM", "resident", "fm_clinic", 1
            ),
            _supervision_assignment(fac.id, date(2025, 3, 3), "AM", "faculty", "pcat"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_clinic_code_variants_counted(self):
        """Resident clinic codes C, C-N, CV all count."""
        c = FacultySupervisionConstraint()
        res1 = _person(name="R1", pgy_level=2)
        res2 = _person(name="R2", pgy_level=2)
        res3 = _person(name="R3", pgy_level=2)
        ctx = _context(
            residents=[res1, res2, res3],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 3),
        )
        assignments = [
            _supervision_assignment(
                res1.id, date(2025, 3, 3), "AM", "resident", "C", 2
            ),
            _supervision_assignment(
                res2.id, date(2025, 3, 3), "AM", "resident", "C-N", 2
            ),
            _supervision_assignment(
                res3.id, date(2025, 3, 3), "AM", "resident", "CV", 2
            ),
        ]
        result = c.validate(assignments, ctx)
        # 3 PGY-2 = 0.75 demand, ceil(0.75)=1 faculty needed, 0 provided
        assert result.satisfied is False
        assert result.violations[0].details["required"] == 1

    def test_violation_details_correct(self):
        """Violation details include all expected fields."""
        c = FacultySupervisionConstraint()
        res = _person(name="Intern", pgy_level=1)
        ctx = _context(
            residents=[res],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 3),
        )
        assignments = [
            _supervision_assignment(
                res.id, date(2025, 3, 3), "AM", "resident", "fm_clinic", 1
            ),
        ]
        result = c.validate(assignments, ctx)
        v = result.violations[0]
        assert v.details["date"] == "2025-03-03"
        assert v.details["slot"] == "AM"
        assert v.details["required"] == 1
        assert v.details["actual"] == 0
        assert v.details["deficit"] == 1
        assert v.details["residents"] == 1

    def test_separate_slots_checked_independently(self):
        """AM and PM slots checked independently."""
        c = FacultySupervisionConstraint()
        res = _person(name="Intern", pgy_level=1)
        fac = _person(name="Dr. A")
        ctx = _context(
            residents=[res],
            faculty=[fac],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 3),
        )
        assignments = [
            # AM: resident + faculty -> ok
            _supervision_assignment(
                res.id, date(2025, 3, 3), "AM", "resident", "fm_clinic", 1
            ),
            _supervision_assignment(fac.id, date(2025, 3, 3), "AM", "faculty", "at"),
            # PM: resident but no faculty -> violation
            _supervision_assignment(
                res.id, date(2025, 3, 3), "PM", "resident", "fm_clinic", 1
            ),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].details["slot"] == "PM"

    def test_non_clinic_resident_not_counted(self):
        """Resident with non-clinic activity code not counted for demand."""
        c = FacultySupervisionConstraint()
        res = _person(name="Intern", pgy_level=1)
        ctx = _context(
            residents=[res],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 3),
        )
        assignments = [
            _supervision_assignment(
                res.id, date(2025, 3, 3), "AM", "resident", "FMIT", 1
            ),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_default_pgy_level_2(self):
        """Resident without pgy_level defaults to PGY-2 (0.25 demand)."""
        c = FacultySupervisionConstraint()
        res = _person(name="Resident")
        ctx = _context(
            residents=[res],
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 3),
        )
        assignments = [
            _supervision_assignment(
                res.id, date(2025, 3, 3), "AM", "resident", "fm_clinic", None
            ),
        ]
        result = c.validate(assignments, ctx)
        # PGY-2 default: 0.25 demand -> ceil(0.25) = 1 faculty needed
        assert result.satisfied is False
        assert result.violations[0].details["required"] == 1
