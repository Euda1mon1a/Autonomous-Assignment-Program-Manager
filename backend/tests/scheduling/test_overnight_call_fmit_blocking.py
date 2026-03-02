"""Tests for OvernightCallGenerationConstraint FMIT/absence blocking.

Verifies that the constraint correctly blocks ineligible faculty's call
variables (FMIT week, post-FMIT Sunday) by forcing existing solver
variables to 0, rather than creating new variables.
"""

from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

from app.scheduling.constraints.base import SchedulingContext
from app.scheduling.constraints.overnight_call import (
    OvernightCallGenerationConstraint,
)


# ==================== Helpers ====================


def _person(pid=None, name="Faculty", **kwargs):
    ns = SimpleNamespace(id=pid or uuid4(), name=name)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _block(bid=None, block_date=None, time_of_day="AM", is_weekend=False, **kwargs):
    ns = SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2026, 5, 11),
        time_of_day=time_of_day,
        is_weekend=is_weekend,
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _context(faculty=None, call_eligible=None, blocks=None, **kwargs):
    ctx = SchedulingContext(
        residents=[],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=[],
        call_eligible_faculty=call_eligible or [],
    )
    for k, v in kwargs.items():
        setattr(ctx, k, v)
    return ctx


class FakeCpModel:
    """Minimal CP-SAT model stub for testing constraint addition."""

    def __init__(self):
        self.constraints = []

    def Add(self, expr):
        self.constraints.append(expr)
        return SimpleNamespace()

    def NewBoolVar(self, name):
        return SimpleNamespace(name=name, _value=None)


# ==================== _get_eligible_faculty index fix ====================


class TestEligibleFacultyUsesCorrectIndex:
    def test_uses_call_eligible_faculty_idx(self):
        """Faculty found via call_eligible_faculty_idx, not resident_idx."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. Core", faculty_role="core")
        b = _block(block_date=date(2026, 5, 11))  # Monday
        ctx = _context(faculty=[fac], call_eligible=[fac], blocks=[b])

        eligible = c._get_eligible_faculty(ctx, date(2026, 5, 11), {})
        assert len(eligible) == 1
        assert eligible[0][0] is fac
        assert eligible[0][1] == 0  # f_i from call_eligible_faculty_idx

    def test_faculty_not_in_call_eligible_excluded(self):
        """Faculty in context.faculty but NOT in call_eligible is excluded."""
        c = OvernightCallGenerationConstraint()
        fac1 = _person(name="Dr. Eligible", faculty_role="core")
        fac2 = _person(name="Dr. NotEligible", faculty_role="core")
        b = _block(block_date=date(2026, 5, 11))
        # fac2 is in faculty but not in call_eligible
        ctx = _context(faculty=[fac1, fac2], call_eligible=[fac1], blocks=[b])

        eligible = c._get_eligible_faculty(ctx, date(2026, 5, 11), {})
        assert len(eligible) == 1
        assert eligible[0][0] is fac1


# ==================== FMIT blocking ====================


class TestFmitBlocked:
    def test_fmit_week_faculty_excluded(self):
        """Faculty on FMIT during target date should be excluded."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. FMIT", faculty_role="core")
        b = _block(block_date=date(2026, 5, 12))  # Tuesday
        ctx = _context(call_eligible=[fac], blocks=[b])

        # FMIT week Fri 5/8 - Thu 5/14
        fmit_weeks = {fac.id: [(date(2026, 5, 8), date(2026, 5, 14))]}
        eligible = c._get_eligible_faculty(ctx, date(2026, 5, 12), fmit_weeks)
        assert len(eligible) == 0

    def test_post_fmit_sunday_blocked(self):
        """Sunday after FMIT week should be blocked."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. FMIT", faculty_role="core")
        # Post-FMIT Sunday: thursday_end(5/14) + 3 = 5/17 (Sunday)
        sun = _block(block_date=date(2026, 5, 17))
        ctx = _context(call_eligible=[fac], blocks=[sun])

        fmit_weeks = {fac.id: [(date(2026, 5, 8), date(2026, 5, 14))]}
        eligible = c._get_eligible_faculty(ctx, date(2026, 5, 17), fmit_weeks)
        assert len(eligible) == 0

    def test_non_fmit_faculty_not_blocked(self):
        """Faculty NOT on FMIT should pass through."""
        c = OvernightCallGenerationConstraint()
        fac_fmit = _person(name="Dr. FMIT", faculty_role="core")
        fac_avail = _person(name="Dr. Available", faculty_role="core")
        b = _block(block_date=date(2026, 5, 12))
        ctx = _context(call_eligible=[fac_fmit, fac_avail], blocks=[b])

        fmit_weeks = {fac_fmit.id: [(date(2026, 5, 8), date(2026, 5, 14))]}
        eligible = c._get_eligible_faculty(ctx, date(2026, 5, 12), fmit_weeks)
        assert len(eligible) == 1
        assert eligible[0][0] is fac_avail


# ==================== add_to_cpsat blocking ====================


class TestAddToCpsatBlocksIneligible:
    def test_blocks_ineligible_call_vars(self):
        """Constraint should add var == 0 for FMIT-blocked faculty."""
        c = OvernightCallGenerationConstraint()
        fac_avail = _person(name="Dr. Available", faculty_role="core")
        fac_fmit = _person(name="Dr. FMIT", faculty_role="core")

        # Monday block
        mon = _block(block_date=date(2026, 5, 11))
        ctx = _context(
            call_eligible=[fac_avail, fac_fmit],
            blocks=[mon],
            templates=[],
        )

        b_i = ctx.block_idx[mon.id]
        # f_i: fac_avail=0, fac_fmit=1
        var_avail = SimpleNamespace(name="call_0")
        var_fmit = SimpleNamespace(name="call_1")

        variables = {
            "call_assignments": {
                (0, b_i, "overnight"): var_avail,
                (1, b_i, "overnight"): var_fmit,
            }
        }

        # FMIT blocks fac_fmit on this date
        fmit_template = SimpleNamespace(
            id=uuid4(), name="FMIT", rotation_type="inpatient"
        )
        fmit_assignment = SimpleNamespace(
            person_id=fac_fmit.id,
            block_id=mon.id,
            rotation_template_id=fmit_template.id,
        )
        ctx.templates = [fmit_template]
        ctx.existing_assignments = [fmit_assignment]

        model = FakeCpModel()
        c.add_to_cpsat(model, variables, ctx)

        # Should have added at least one blocking constraint
        assert len(model.constraints) >= 1

    def test_no_call_vars_returns_early(self):
        """Empty call_assignments should cause early return with no constraints."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. A", faculty_role="core")
        mon = _block(block_date=date(2026, 5, 11))
        ctx = _context(call_eligible=[fac], blocks=[mon])

        model = FakeCpModel()
        variables = {"call_assignments": {}}
        c.add_to_cpsat(model, variables, ctx)

        assert len(model.constraints) == 0

    def test_no_blocking_when_all_eligible(self):
        """No FMIT weeks → no blocking constraints added."""
        c = OvernightCallGenerationConstraint()
        fac = _person(name="Dr. A", faculty_role="core")
        mon = _block(block_date=date(2026, 5, 11))
        ctx = _context(call_eligible=[fac], blocks=[mon])

        b_i = ctx.block_idx[mon.id]
        var = SimpleNamespace(name="call_0")
        variables = {"call_assignments": {(0, b_i, "overnight"): var}}

        model = FakeCpModel()
        c.add_to_cpsat(model, variables, ctx)

        # No FMIT weeks, no absences → no blocking
        assert len(model.constraints) == 0
