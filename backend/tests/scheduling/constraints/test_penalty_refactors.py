"""Tests for constraint penalty refactors (PR #1316).

Verifies that refactored constraints correctly:
1. Use faculty_template_assignments (not template_assignments)
2. Use context.faculty_idx (not context.resident_idx)
3. Handle missing Fri/Sat call vars gracefully (FMIT)
4. Create penalty BoolVars in objective_terms
"""

import logging
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import SchedulingContext
from app.scheduling.constraints.faculty_role import (
    FacultyRoleClinicConstraint,
    SMFacultyClinicConstraint,
)
from app.scheduling.constraints.fmit import FMITMandatoryCallConstraint
from app.scheduling.constraints.temporal import WednesdayAMInternOnlyConstraint


# ============================================================================
# Fake CP-SAT helpers
# ============================================================================


class FakeBoolVar:
    """Fake CP-SAT BoolVar that supports Not() and arithmetic."""

    def __init__(self, name=""):
        self._name = name
        self._negated = False

    def Not(self):
        neg = FakeBoolVar(f"not({self._name})")
        neg._negated = True
        return neg

    def __add__(self, other):
        return FakeIntVar(f"({self._name}+{other})")

    def __radd__(self, other):
        if other == 0:
            return self
        return FakeIntVar(f"({other}+{self._name})")

    def __sub__(self, other):
        return FakeIntVar(f"({self._name}-{other})")

    def __rsub__(self, other):
        return FakeIntVar(f"({other}-{self._name})")

    def __repr__(self):
        return f"FakeBoolVar({self._name})"


class FakeIntVar:
    """Fake CP-SAT IntVar that supports arithmetic."""

    def __init__(self, name=""):
        self._name = name

    def __add__(self, other):
        return FakeIntVar(f"({self._name}+{other})")

    def __radd__(self, other):
        if other == 0:
            return self
        return FakeIntVar(f"({other}+{self._name})")

    def __sub__(self, other):
        return FakeIntVar(f"({self._name}-{other})")

    def __ge__(self, other):
        return ("ge", self, other)

    def __le__(self, other):
        return ("le", self, other)

    def __repr__(self):
        return f"FakeIntVar({self._name})"


class FakeCpModel:
    """Minimal CP-SAT model mock that tracks calls."""

    def __init__(self):
        self.adds = []
        self.int_vars = []
        self.bool_vars = []
        self.implications = []

    def Add(self, expr):
        self.adds.append(expr)
        return MagicMock()

    def NewIntVar(self, lb, ub, name):
        var = FakeIntVar(name)
        self.int_vars.append((lb, ub, name))
        return var

    def NewBoolVar(self, name):
        var = FakeBoolVar(name)
        self.bool_vars.append(name)
        return var

    def AddImplication(self, src, target):
        self.implications.append((src, target))


# ============================================================================
# Mock builders
# ============================================================================


def _person(pid=None, name="Person", pgy_level=None, person_type="resident"):
    ns = SimpleNamespace(id=pid or uuid4(), name=name, type=person_type)
    if pgy_level is not None:
        ns.pgy_level = pgy_level
    return ns


def _faculty(
    pid=None,
    name="Faculty",
    faculty_role="core",
    weekly_clinic_limit=4,
    is_sports_medicine=False,
    max_clinic_halfdays_per_week=None,
    min_clinic_halfdays_per_week=None,
):
    ns = SimpleNamespace(
        id=pid or uuid4(),
        name=name,
        type="faculty",
        faculty_role=faculty_role,
        weekly_clinic_limit=weekly_clinic_limit,
        is_sports_medicine=is_sports_medicine,
    )
    if max_clinic_halfdays_per_week is not None:
        ns.max_clinic_halfdays_per_week = max_clinic_halfdays_per_week
    if min_clinic_halfdays_per_week is not None:
        ns.min_clinic_halfdays_per_week = min_clinic_halfdays_per_week
    return ns


def _block(bid=None, block_date=None, time_of_day="AM"):
    return SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2026, 3, 16),  # Monday
        time_of_day=time_of_day,
    )


def _template(tid=None, name="Clinic", rotation_type="outpatient"):
    return SimpleNamespace(
        id=tid or uuid4(),
        name=name,
        rotation_type=rotation_type,
    )


def _context(residents=None, faculty=None, blocks=None, templates=None, **kwargs):
    return SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
        **kwargs,
    )


# ============================================================================
# Fix 1: FacultyRoleClinicConstraint uses faculty vars + faculty_idx
# ============================================================================


class TestFacultyRoleClinicUsesFacultyVars:
    """FacultyRoleClinicConstraint must read faculty_template_assignments."""

    def test_cpsat_adds_penalty_terms_with_faculty_vars(self):
        """Verify penalty terms are added when faculty_template_assignments has data."""
        model = FakeCpModel()
        fac = _faculty(faculty_role="core", weekly_clinic_limit=2)
        tmpl = _template()
        # Monday block
        blk = _block(block_date=date(2026, 3, 16))

        ctx = _context(faculty=[fac], blocks=[blk], templates=[tmpl])

        # faculty_idx maps faculty.id -> 0
        f_i = ctx.faculty_idx[fac.id]
        b_i = ctx.block_idx[blk.id]
        t_i = ctx.template_idx[tmpl.id]

        # Create BoolVars in the faculty matrix
        var = FakeBoolVar(f"fta_{f_i}_{b_i}_{t_i}")
        variables = {
            "faculty_template_assignments": {(f_i, b_i, t_i): var},
        }

        constraint = FacultyRoleClinicConstraint()
        constraint.add_to_cpsat(model, variables, ctx)

        # Should have added penalty terms
        obj_terms = variables.get("objective_terms", [])
        assert len(obj_terms) > 0, "Expected penalty terms in objective_terms"

    def test_cpsat_ignores_resident_template_assignments(self):
        """Verify template_assignments (resident matrix) is NOT read."""
        model = FakeCpModel()
        fac = _faculty(faculty_role="core", weekly_clinic_limit=2)
        tmpl = _template()
        blk = _block(block_date=date(2026, 3, 16))

        ctx = _context(faculty=[fac], blocks=[blk], templates=[tmpl])

        f_i = ctx.faculty_idx[fac.id]
        b_i = ctx.block_idx[blk.id]
        t_i = ctx.template_idx[tmpl.id]

        var = FakeBoolVar(f"ta_{f_i}_{b_i}_{t_i}")
        variables = {
            "template_assignments": {(f_i, b_i, t_i): var},
            # No faculty_template_assignments
        }

        constraint = FacultyRoleClinicConstraint()
        constraint.add_to_cpsat(model, variables, ctx)

        # Should NOT have added any terms (no faculty vars)
        obj_terms = variables.get("objective_terms", [])
        assert len(obj_terms) == 0, (
            "Should not create penalty terms from resident template_assignments"
        )

    def test_cpsat_uses_faculty_idx_not_resident_idx(self):
        """Verify faculty_idx lookup is used, not resident_idx."""
        model = FakeCpModel()
        res = _person(pgy_level=1)
        fac = _faculty(faculty_role="core", weekly_clinic_limit=2)
        tmpl = _template()
        blk = _block(block_date=date(2026, 3, 16))

        ctx = _context(residents=[res], faculty=[fac], blocks=[blk], templates=[tmpl])

        # faculty_idx and resident_idx should map different IDs
        assert fac.id in ctx.faculty_idx
        assert fac.id not in ctx.resident_idx

        f_i = ctx.faculty_idx[fac.id]
        b_i = ctx.block_idx[blk.id]
        t_i = ctx.template_idx[tmpl.id]

        var = FakeBoolVar(f"fta_{f_i}_{b_i}_{t_i}")
        variables = {
            "faculty_template_assignments": {(f_i, b_i, t_i): var},
        }

        constraint = FacultyRoleClinicConstraint()
        constraint.add_to_cpsat(model, variables, ctx)

        obj_terms = variables.get("objective_terms", [])
        assert len(obj_terms) > 0


class TestSMFacultyClinicUsesFacultyVars:
    """SMFacultyClinicConstraint must read faculty_template_assignments."""

    def test_cpsat_adds_penalty_for_sm_in_regular_clinic(self):
        """SM faculty in regular clinic should produce penalty terms."""
        model = FakeCpModel()
        fac = _faculty(
            faculty_role="sports_med",
            is_sports_medicine=True,
            weekly_clinic_limit=0,
        )
        tmpl = _template(name="Regular Clinic", rotation_type="outpatient")
        blk = _block(block_date=date(2026, 3, 16))

        ctx = _context(faculty=[fac], blocks=[blk], templates=[tmpl])

        f_i = ctx.faculty_idx[fac.id]
        b_i = ctx.block_idx[blk.id]
        t_i = ctx.template_idx[tmpl.id]

        var = FakeBoolVar(f"fta_{f_i}_{b_i}_{t_i}")
        variables = {
            "faculty_template_assignments": {(f_i, b_i, t_i): var},
        }

        constraint = SMFacultyClinicConstraint()
        constraint.add_to_cpsat(model, variables, ctx)

        obj_terms = variables.get("objective_terms", [])
        assert len(obj_terms) > 0, "SM faculty in regular clinic should be penalized"
        # Verify implications were added (SM penalty uses AddImplication)
        assert len(model.implications) > 0


# ============================================================================
# Fix 2: FMITMandatoryCall handles no Fri/Sat call vars gracefully
# ============================================================================


class TestFMITMandatoryCallNoFriSatVars:
    """FMITMandatoryCallConstraint handles absent Fri/Sat call vars."""

    def _make_fmit_context(self):
        """Create context with FMIT assignment (Fri-Thu week)."""
        fac = _faculty(name="FMIT Faculty")
        # FMIT template
        fmit_tmpl = SimpleNamespace(
            id=uuid4(),
            name="FMIT",
            rotation_type="inpatient",
            abbreviation="FMIT",
            display_abbreviation="FMIT",
        )
        # Friday start of FMIT week
        friday = date(2026, 3, 13)  # A Friday
        blocks = []
        for i in range(7):  # Fri through Thu
            d = friday + timedelta(days=i)
            blocks.append(_block(block_date=d))

        # Build context with existing FMIT assignment
        fmit_assignment = SimpleNamespace(
            person_id=fac.id,
            block_id=blocks[0].id,  # Friday block
            rotation_template_id=fmit_tmpl.id,
            rotation_template=fmit_tmpl,
        )
        # Also need the block attribute for cross-block resolution
        fmit_assignment.block = blocks[0]

        ctx = _context(
            faculty=[fac],
            blocks=blocks,
            templates=[fmit_tmpl],
            call_eligible_faculty=[fac],
            existing_assignments=[fmit_assignment],
        )
        return ctx, fac

    def test_cpsat_no_crash_with_sun_thu_only_call_vars(self):
        """Should not crash when call_assignments has only Sun-Thu vars."""
        model = FakeCpModel()
        ctx, fac = self._make_fmit_context()
        call_i = ctx.call_eligible_faculty_idx[fac.id]

        # Create call vars for Sun-Thu only (no Fri/Sat)
        call_vars = {}
        for block in ctx.blocks:
            dow = block.date.weekday()
            # Only Sun(6), Mon(0), Tue(1), Wed(2), Thu(3)
            if dow in (6, 0, 1, 2, 3):
                b_i = ctx.block_idx[block.id]
                call_vars[(call_i, b_i, "overnight")] = FakeBoolVar(
                    f"call_{call_i}_{b_i}"
                )

        variables = {"call_assignments": call_vars}

        constraint = FMITMandatoryCallConstraint()
        constraint.add_to_cpsat(model, variables, ctx)

        # Should have added 0 penalty terms (no Fri/Sat call vars exist)
        obj_terms = variables.get("objective_terms", [])
        assert len(obj_terms) == 0

    def test_cpsat_logs_preloaded_message(self, caplog):
        """Should log a message when no Fri/Sat call vars found."""
        model = FakeCpModel()
        ctx, fac = self._make_fmit_context()
        call_i = ctx.call_eligible_faculty_idx[fac.id]

        # Call vars for Sun-Thu only
        call_vars = {}
        for block in ctx.blocks:
            dow = block.date.weekday()
            if dow in (6, 0, 1, 2, 3):
                b_i = ctx.block_idx[block.id]
                call_vars[(call_i, b_i, "overnight")] = FakeBoolVar(
                    f"call_{call_i}_{b_i}"
                )

        variables = {"call_assignments": call_vars}

        constraint = FMITMandatoryCallConstraint()
        with caplog.at_level(logging.INFO):
            constraint.add_to_cpsat(model, variables, ctx)

        assert any("preloaded" in msg.lower() for msg in caplog.messages)

    def test_cpsat_adds_terms_when_fri_sat_vars_present(self):
        """If Fri/Sat call vars exist, penalty terms should be created."""
        model = FakeCpModel()
        ctx, fac = self._make_fmit_context()
        call_i = ctx.call_eligible_faculty_idx[fac.id]

        # Create call vars for ALL days (including Fri/Sat)
        call_vars = {}
        for block in ctx.blocks:
            b_i = ctx.block_idx[block.id]
            call_vars[(call_i, b_i, "overnight")] = FakeBoolVar(f"call_{call_i}_{b_i}")

        variables = {"call_assignments": call_vars}

        constraint = FMITMandatoryCallConstraint()
        constraint.add_to_cpsat(model, variables, ctx)

        # Should have terms for Fri + Sat = 2 penalty terms
        obj_terms = variables.get("objective_terms", [])
        assert len(obj_terms) == 2


# ============================================================================
# Fix 3 (bonus): WednesdayAMInternOnly creates penalties for non-PGY1
# ============================================================================


class TestWednesdayAMInternOnlyCreatesPenalties:
    """WednesdayAMInternOnlyConstraint creates penalties for non-interns."""

    def test_cpsat_penalizes_pgy2_on_wednesday_am(self):
        """PGY-2 on Wednesday AM clinic should generate penalty BoolVar."""
        model = FakeCpModel()
        r2 = _person(pgy_level=2)
        tmpl = _template(name="Clinic", rotation_type="outpatient")
        # Wednesday AM block
        wed = date(2026, 3, 18)  # Wednesday
        blk = _block(block_date=wed, time_of_day="AM")

        ctx = _context(residents=[r2], blocks=[blk], templates=[tmpl])

        r_i = ctx.resident_idx[r2.id]
        b_i = ctx.block_idx[blk.id]
        t_i = ctx.template_idx[tmpl.id]

        var = FakeBoolVar(f"ta_{r_i}_{b_i}_{t_i}")
        variables = {
            "template_assignments": {(r_i, b_i, t_i): var},
        }

        constraint = WednesdayAMInternOnlyConstraint()
        constraint.add_to_cpsat(model, variables, ctx)

        obj_terms = variables.get("objective_terms", [])
        assert len(obj_terms) == 1, "PGY-2 on Wed AM should produce 1 penalty term"
        # Verify BoolVar was created
        assert len(model.bool_vars) == 1
        assert "wed_am_nonintern" in model.bool_vars[0]

    def test_cpsat_no_penalty_for_pgy1_on_wednesday_am(self):
        """PGY-1 on Wednesday AM should NOT generate penalty."""
        model = FakeCpModel()
        r1 = _person(pgy_level=1)
        tmpl = _template(name="Clinic", rotation_type="outpatient")
        wed = date(2026, 3, 18)
        blk = _block(block_date=wed, time_of_day="AM")

        ctx = _context(residents=[r1], blocks=[blk], templates=[tmpl])

        r_i = ctx.resident_idx[r1.id]
        b_i = ctx.block_idx[blk.id]
        t_i = ctx.template_idx[tmpl.id]

        var = FakeBoolVar(f"ta_{r_i}_{b_i}_{t_i}")
        variables = {
            "template_assignments": {(r_i, b_i, t_i): var},
        }

        constraint = WednesdayAMInternOnlyConstraint()
        constraint.add_to_cpsat(model, variables, ctx)

        obj_terms = variables.get("objective_terms", [])
        assert len(obj_terms) == 0, "PGY-1 on Wed AM should not be penalized"

    def test_cpsat_penalizes_multiple_non_interns(self):
        """Multiple non-PGY1 residents should each get a penalty."""
        model = FakeCpModel()
        r2 = _person(pgy_level=2, name="PGY2")
        r3 = _person(pgy_level=3, name="PGY3")
        r1 = _person(pgy_level=1, name="PGY1")  # Should be skipped
        tmpl = _template(name="Clinic", rotation_type="outpatient")
        wed = date(2026, 3, 18)
        blk = _block(block_date=wed, time_of_day="AM")

        ctx = _context(residents=[r2, r3, r1], blocks=[blk], templates=[tmpl])

        # Build template_assignments for all three residents
        template_vars = {}
        for r in [r2, r3, r1]:
            r_i = ctx.resident_idx[r.id]
            b_i = ctx.block_idx[blk.id]
            t_i = ctx.template_idx[tmpl.id]
            template_vars[(r_i, b_i, t_i)] = FakeBoolVar(f"ta_{r_i}_{b_i}_{t_i}")

        variables = {"template_assignments": template_vars}

        constraint = WednesdayAMInternOnlyConstraint()
        constraint.add_to_cpsat(model, variables, ctx)

        obj_terms = variables.get("objective_terms", [])
        # PGY-2 and PGY-3 penalized, PGY-1 skipped
        assert len(obj_terms) == 2
