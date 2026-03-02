"""Tests for overnight call generation constraint (pure logic, no DB required)."""

from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.overnight_call import (
    OvernightCallGenerationConstraint,
    is_overnight_call_night,
)


# ==================== Helpers ====================


def _person(pid=None, name="Faculty", **kwargs):
    ns = SimpleNamespace(id=pid or uuid4(), name=name)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _block(bid=None, block_date=None, time_of_day="AM", **kwargs):
    ns = SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 3),
        time_of_day=time_of_day,
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _template(tid=None, name="Template", **kwargs):
    ns = SimpleNamespace(id=tid or uuid4(), name=name)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _call_assignment(person_id, block_id, call_date=None, **kwargs):
    ns = SimpleNamespace(
        person_id=person_id,
        block_id=block_id,
        call_type="overnight",
        date=call_date or date(2025, 3, 3),
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _context(faculty=None, blocks=None, templates=None, **kwargs):
    ctx = SchedulingContext(
        residents=[],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )
    for k, v in kwargs.items():
        setattr(ctx, k, v)
    return ctx


# ==================== is_overnight_call_night Tests ====================


class TestIsOvernightCallNight:
    def test_sunday_true(self):
        assert is_overnight_call_night(date(2025, 3, 9)) is True

    def test_monday_true(self):
        assert is_overnight_call_night(date(2025, 3, 3)) is True

    def test_tuesday_true(self):
        assert is_overnight_call_night(date(2025, 3, 4)) is True

    def test_wednesday_true(self):
        assert is_overnight_call_night(date(2025, 3, 5)) is True

    def test_thursday_true(self):
        assert is_overnight_call_night(date(2025, 3, 6)) is True

    def test_friday_false(self):
        assert is_overnight_call_night(date(2025, 3, 7)) is False

    def test_saturday_false(self):
        assert is_overnight_call_night(date(2025, 3, 8)) is False


# ==================== OvernightCallGenerationConstraint Init ====================


class TestOvernightCallInit:
    def test_name(self):
        c = OvernightCallGenerationConstraint()
        assert c.name == "OvernightCallGeneration"

    def test_type(self):
        c = OvernightCallGenerationConstraint()
        assert c.constraint_type == ConstraintType.CALL

    def test_priority(self):
        c = OvernightCallGenerationConstraint()
        assert c.priority == ConstraintPriority.HIGH


# ==================== _get_eligible_faculty Tests ====================


class TestGetEligibleFaculty:
    def test_core_faculty_eligible(self):
        """Faculty must be in call_eligible_faculty_idx to be eligible."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. Core", faculty_role="core")
        b = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[fac], blocks=[b])
        ctx.call_eligible_faculty_idx[fac.id] = 0
        eligible = c._get_eligible_faculty(ctx, date(2025, 3, 3), {})
        assert len(eligible) == 1
        assert eligible[0][0] is fac

    def test_adjunct_excluded_by_faculty_role(self):
        """ADJUNCT faculty excluded via faculty_role attribute."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. Adj", faculty_role="adjunct")
        b = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[fac], blocks=[b])
        eligible = c._get_eligible_faculty(ctx, date(2025, 3, 3), {})
        assert len(eligible) == 0

    def test_fmit_blocked_during_fmit_week(self):
        """Faculty on FMIT blocked from call during FMIT week."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. FMIT")
        b = _block(block_date=date(2025, 3, 10))  # Monday
        ctx = _context(faculty=[fac], blocks=[b])
        # FMIT week Fri 3/7 - Thu 3/13
        fmit_weeks = {fac.id: [(date(2025, 3, 7), date(2025, 3, 13))]}
        eligible = c._get_eligible_faculty(ctx, date(2025, 3, 10), fmit_weeks)
        assert len(eligible) == 0

    def test_fmit_not_blocked_outside_week(self):
        """Faculty not blocked outside their FMIT week."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. FMIT")
        b = _block(block_date=date(2025, 3, 17))
        ctx = _context(faculty=[fac], blocks=[b])
        ctx.call_eligible_faculty_idx[fac.id] = 0
        fmit_weeks = {fac.id: [(date(2025, 3, 7), date(2025, 3, 13))]}
        eligible = c._get_eligible_faculty(ctx, date(2025, 3, 17), fmit_weeks)
        assert len(eligible) == 1

    def test_post_fmit_sunday_blocked(self):
        """Sunday after FMIT week blocked."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. FMIT")
        sun = _block(block_date=date(2025, 3, 16))  # Sunday after FMIT 3/7-3/13
        ctx = _context(faculty=[fac], blocks=[sun])
        fmit_weeks = {fac.id: [(date(2025, 3, 7), date(2025, 3, 13))]}
        # blocked_sunday = 3/13 + 3 = 3/16
        eligible = c._get_eligible_faculty(ctx, date(2025, 3, 16), fmit_weeks)
        assert len(eligible) == 0

    def test_unavailable_faculty_excluded(self):
        """Faculty with unavailable block excluded."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. Away")
        b = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[fac], blocks=[b])
        ctx.availability = {fac.id: {b.id: {"available": False}}}
        eligible = c._get_eligible_faculty(ctx, date(2025, 3, 3), {})
        assert len(eligible) == 0

    def test_available_faculty_included(self):
        """Faculty with available block included."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. Here")
        b = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[fac], blocks=[b])
        ctx.call_eligible_faculty_idx[fac.id] = 0
        ctx.availability = {fac.id: {b.id: {"available": True}}}
        eligible = c._get_eligible_faculty(ctx, date(2025, 3, 3), {})
        assert len(eligible) == 1


# ==================== _identify_fmit_weeks Tests ====================


class TestIdentifyFmitWeeks:
    def test_no_existing_assignments(self):
        c = OvernightCallGenerationConstraint()
        ctx = _context()
        result = c._identify_fmit_weeks(ctx)
        assert result == {}

    def test_fmit_assignment_identified(self):
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. A")
        fmit = _template(name="FMIT", rotation_type="inpatient")
        b = _block(block_date=date(2025, 3, 10))
        a = SimpleNamespace(
            person_id=fac.id, block_id=b.id, rotation_template_id=fmit.id
        )
        ctx = _context(faculty=[fac], blocks=[b], templates=[fmit])
        ctx.existing_assignments = [a]
        result = c._identify_fmit_weeks(ctx)
        assert fac.id in result
        assert (date(2025, 3, 7), date(2025, 3, 13)) in result[fac.id]

    def test_non_fmit_ignored(self):
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. A")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b = _block(block_date=date(2025, 3, 10))
        a = SimpleNamespace(
            person_id=fac.id, block_id=b.id, rotation_template_id=clinic.id
        )
        ctx = _context(faculty=[fac], blocks=[b], templates=[clinic])
        ctx.existing_assignments = [a]
        result = c._identify_fmit_weeks(ctx)
        assert result == {}


# ==================== validate Tests ====================


class TestOvernightCallValidate:
    def test_no_assignments_no_blocks_satisfied(self):
        c = OvernightCallGenerationConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_uncovered_night_critical_violation(self):
        """Night with no call assignment -> CRITICAL violation."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. A")
        mon = _block(block_date=date(2025, 3, 3))  # Monday (call night)
        ctx = _context(faculty=[fac], blocks=[mon])
        result = c.validate([], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "CRITICAL"
        assert "No overnight call" in result.violations[0].message

    def test_covered_night_satisfied(self):
        """Night with exactly one call assignment -> satisfied."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. A")
        mon = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[fac], blocks=[mon])
        a = _call_assignment(fac.id, mon.id, call_date=date(2025, 3, 3))
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_double_coverage_high_violation(self):
        """Two calls on same night -> HIGH violation."""
        c = OvernightCallGenerationConstraint()
        fac1 = _person(name="Dr. A")
        fac2 = _person(name="Dr. B")
        mon = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[fac1, fac2], blocks=[mon])
        assignments = [
            _call_assignment(fac1.id, mon.id, call_date=date(2025, 3, 3)),
            _call_assignment(fac2.id, mon.id, call_date=date(2025, 3, 3)),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert any(v.severity == "HIGH" for v in result.violations)

    def test_adjunct_assigned_critical_violation(self):
        """ADJUNCT faculty assigned call -> CRITICAL violation."""
        c = OvernightCallGenerationConstraint()
        adj = _person(name="Dr. Adj", faculty_role="adjunct")
        mon = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[adj], blocks=[mon])
        a = _call_assignment(adj.id, mon.id, call_date=date(2025, 3, 3))
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert any("ADJUNCT" in v.message for v in result.violations)

    def test_friday_saturday_not_checked(self):
        """Friday and Saturday blocks -> no call nights to check."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. A")
        fri = _block(block_date=date(2025, 3, 7))  # Friday
        sat = _block(block_date=date(2025, 3, 8))  # Saturday
        ctx = _context(faculty=[fac], blocks=[fri, sat])
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_non_overnight_call_ignored(self):
        """Non-overnight call type -> not counted."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. A")
        mon = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[fac], blocks=[mon])
        a = SimpleNamespace(
            person_id=fac.id,
            block_id=mon.id,
            call_type="backup",
            date=date(2025, 3, 3),
        )
        result = c.validate([a], ctx)
        # Monday still uncovered by overnight call
        assert result.satisfied is False

    def test_multiple_nights_all_covered(self):
        """Multiple call nights all covered -> satisfied."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. A")
        # Mon-Thu (4 call nights)
        blocks = [
            _block(block_date=date(2025, 3, 3) + timedelta(days=i)) for i in range(4)
        ]
        ctx = _context(faculty=[fac], blocks=blocks)
        assignments = [_call_assignment(fac.id, b.id, call_date=b.date) for b in blocks]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True
