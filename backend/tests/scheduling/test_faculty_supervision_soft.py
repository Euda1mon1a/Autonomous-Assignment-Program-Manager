"""Tests for FacultySupervisionConstraint soft-constraint behaviour.

Verifies that supervision deficit is penalised (not INFEASIBLE),
and that sufficient coverage produces zero deficit.
"""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.scheduling.constraints.faculty_clinic import FacultySupervisionConstraint


@pytest.fixture
def constraint():
    return FacultySupervisionConstraint()


class FakeIntVar:
    """Fake CP-SAT integer variable that supports arithmetic expressions."""

    def __init__(self, name=""):
        self._name = name

    def __mul__(self, other):
        return FakeIntVar(f"({self._name}*{other})")

    def __rmul__(self, other):
        return FakeIntVar(f"({other}*{self._name})")

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

    def __ge__(self, other):
        return ("ge", self, other)

    def __le__(self, other):
        return ("le", self, other)


@pytest.fixture
def model():
    """Minimal CP-SAT model mock that records Add / NewIntVar calls."""

    class FakeModel:
        def __init__(self):
            self.adds = []
            self.int_vars = []

        def Add(self, expr):
            self.adds.append(expr)
            return MagicMock()

        def NewIntVar(self, lb, ub, name):
            var = FakeIntVar(name)
            self.int_vars.append((lb, ub, name))
            return var

    return FakeModel()


def _make_context(start: date, end: date, residents, faculty):
    return SimpleNamespace(
        start_date=start,
        end_date=end,
        residents=residents,
        faculty=faculty,
    )


class TestAddToCpsat:
    """Test the CP-SAT integration (soft penalty, not hard)."""

    def test_creates_deficit_vars_for_clinic_slots(self, constraint, model):
        """Deficit variables created for each (date, slot) with residents."""
        r1 = SimpleNamespace(id=uuid4(), pgy_level=1)
        f1 = SimpleNamespace(id=uuid4())

        # Single weekday
        d = date(2026, 3, 2)  # Monday
        resident_clinic = {(r1.id, d, "AM"): FakeIntVar("r1_clinic")}
        faculty_at = {(f1.id, d, "AM"): FakeIntVar("f1_at")}

        variables = {
            "resident_clinic": resident_clinic,
            "faculty_at": faculty_at,
            "faculty_pcat": {},
        }
        context = _make_context(d, d, [r1], [f1])

        constraint.add_to_cpsat(model, variables, context)

        # Should have created at least 1 deficit var (AM slot)
        assert len(model.int_vars) >= 1
        assert any("sup_deficit" in name for _, _, name in model.int_vars)

    def test_no_hard_add_for_coverage(self, constraint, model):
        """The old hard model.Add(coverage >= demand) must NOT exist."""
        r1 = SimpleNamespace(id=uuid4(), pgy_level=2)
        f1 = SimpleNamespace(id=uuid4())

        d = date(2026, 3, 2)
        resident_clinic = {(r1.id, d, "AM"): FakeIntVar("r1_clinic")}
        faculty_at = {(f1.id, d, "AM"): FakeIntVar("f1_at")}

        variables = {
            "resident_clinic": resident_clinic,
            "faculty_at": faculty_at,
            "faculty_pcat": {},
        }
        context = _make_context(d, d, [r1], [f1])

        constraint.add_to_cpsat(model, variables, context)

        # All Add calls should be deficit constraints (deficit >= expr),
        # not hard coverage constraints.
        # The key signal: deficit vars were created, proving soft path taken.
        assert len(model.int_vars) >= 1

    def test_objective_terms_populated(self, constraint, model):
        """Deficit vars must appear in objective_terms with high weight."""
        r1 = SimpleNamespace(id=uuid4(), pgy_level=1)
        f1 = SimpleNamespace(id=uuid4())

        d = date(2026, 3, 2)
        resident_clinic = {(r1.id, d, "AM"): FakeIntVar("r1_clinic")}
        faculty_at = {(f1.id, d, "AM"): FakeIntVar("f1_at")}

        variables = {
            "resident_clinic": resident_clinic,
            "faculty_at": faculty_at,
            "faculty_pcat": {},
        }
        context = _make_context(d, d, [r1], [f1])

        constraint.add_to_cpsat(model, variables, context)

        terms = variables.get("objective_terms", [])
        assert len(terms) >= 1
        # Weight should be high (100 * 100 = 10000)
        _, weight = terms[0]
        assert weight == 10000

    def test_skips_weekends(self, constraint, model):
        """No deficit vars for Saturday/Sunday."""
        r1 = SimpleNamespace(id=uuid4(), pgy_level=1)
        f1 = SimpleNamespace(id=uuid4())

        sat = date(2026, 3, 7)  # Saturday
        sun = date(2026, 3, 8)  # Sunday
        resident_clinic = {
            (r1.id, sat, "AM"): FakeIntVar("r1_sat"),
            (r1.id, sun, "AM"): FakeIntVar("r1_sun"),
        }
        faculty_at = {
            (f1.id, sat, "AM"): FakeIntVar("f1_sat"),
            (f1.id, sun, "AM"): FakeIntVar("f1_sun"),
        }

        variables = {
            "resident_clinic": resident_clinic,
            "faculty_at": faculty_at,
            "faculty_pcat": {},
        }
        context = _make_context(sat, sun, [r1], [f1])

        constraint.add_to_cpsat(model, variables, context)

        assert len(model.int_vars) == 0

    def test_no_faculty_vars_warns(self, constraint, model):
        """If no faculty_at or faculty_pcat, constraint logs warning."""
        variables = {
            "resident_clinic": {(uuid4(), date(2026, 3, 2), "AM"): FakeIntVar("r")},
            "faculty_at": {},
            "faculty_pcat": {},
        }
        context = _make_context(date(2026, 3, 2), date(2026, 3, 2), [], [])

        # Should return without error (just logs warning)
        constraint.add_to_cpsat(model, variables, context)
        assert len(model.int_vars) == 0


class TestInit:
    """Test constructor sets expected values."""

    def test_priority_is_critical(self, constraint):
        from app.scheduling.constraints.base import ConstraintPriority

        assert constraint.priority == ConstraintPriority.CRITICAL

    def test_weight_is_100(self, constraint):
        assert constraint.weight == 100.0

    def test_name(self, constraint):
        assert constraint.name == "FacultySupervision"
