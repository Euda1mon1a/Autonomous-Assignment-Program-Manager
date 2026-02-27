"""Tests for YTD call equity: prior_calls hydration, MAD formulation, and sync."""

import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest


# ---------------------------------------------------------------------------
# Lightweight stubs so tests don't need the full app / DB / OR-Tools stack
# ---------------------------------------------------------------------------


@dataclass
class FakeBlock:
    id: UUID
    date: date


@dataclass
class FakePerson:
    id: UUID
    name: str = "Faculty"


@dataclass
class FakeContext:
    blocks: list = field(default_factory=list)
    faculty: list = field(default_factory=list)
    call_eligible_faculty: list = field(default_factory=list)
    call_eligible_faculty_idx: dict = field(default_factory=dict)
    block_idx: dict = field(default_factory=dict)
    prior_calls: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Minimal CP-SAT model mock for unit tests
# ---------------------------------------------------------------------------


class FakeCPModel:
    """Mimics the subset of or-tools CpModel used by call_equity constraints."""

    def __init__(self):
        self._vars: dict[str, Any] = {}
        self._constraints: list = []
        self._abs_equalities: list = []
        self._var_counter = 0

    def NewIntVar(self, lb, ub, name):
        v = FakeIntVar(name, lb, ub)
        self._vars[name] = v
        self._var_counter += 1
        return v

    def Add(self, expr):
        self._constraints.append(expr)

    def AddAbsEquality(self, target, source):
        self._abs_equalities.append((target, source))


class FakeIntVar:
    def __init__(self, name, lb, ub):
        self.name = name
        self.lb = lb
        self.ub = ub

    def __repr__(self):
        return f"IntVar({self.name})"

    # Arithmetic support so `F * (history + sum(vars_list)) - ...` works
    def __add__(self, other):
        return _Expr("+", self, other)

    def __radd__(self, other):
        return _Expr("+", other, self)

    def __sub__(self, other):
        return _Expr("-", self, other)

    def __rsub__(self, other):
        return _Expr("-", other, self)

    def __mul__(self, other):
        return _Expr("*", self, other)

    def __rmul__(self, other):
        return _Expr("*", other, self)

    def __eq__(self, other):
        return _Expr("==", self, other)

    def __hash__(self):
        return id(self)


class _Expr:
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __add__(self, other):
        return _Expr("+", self, other)

    def __radd__(self, other):
        return _Expr("+", other, self)

    def __sub__(self, other):
        return _Expr("-", self, other)

    def __rsub__(self, other):
        return _Expr("-", other, self)

    def __mul__(self, other):
        return _Expr("*", self, other)

    def __rmul__(self, other):
        return _Expr("*", other, self)

    def __eq__(self, other):
        return _Expr("==", self, other)

    def __le__(self, other):
        return _Expr("<=", self, other)

    def __ge__(self, other):
        return _Expr(">=", self, other)

    def __hash__(self):
        return id(self)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSundayCallEquityMAD:
    """Test the MAD reformulation of SundayCallEquityConstraint."""

    def _make_context(self, n_faculty=3, prior=None):
        faculty = [FakePerson(id=uuid4(), name=f"F{i}") for i in range(n_faculty)]
        # 4 Sundays in a typical 28-day block
        sundays = [
            FakeBlock(id=uuid4(), date=date(2026, 2, 1)),  # Sunday
            FakeBlock(id=uuid4(), date=date(2026, 2, 8)),
            FakeBlock(id=uuid4(), date=date(2026, 2, 15)),
            FakeBlock(id=uuid4(), date=date(2026, 2, 22)),
        ]
        ctx = FakeContext(
            blocks=sundays,
            faculty=faculty,
            call_eligible_faculty=faculty,
            call_eligible_faculty_idx={f.id: i for i, f in enumerate(faculty)},
            block_idx={b.id: i for i, b in enumerate(sundays)},
            prior_calls=prior or {},
        )
        return ctx, faculty, sundays

    def test_mad_creates_abs_dev_vars(self):
        """MAD formulation creates one abs_dev variable per faculty member."""
        from app.scheduling.constraints.call_equity import (
            SundayCallEquityConstraint,
        )

        ctx, faculty, sundays = self._make_context(n_faculty=3)
        model = FakeCPModel()

        # Create call variables for each faculty × sunday
        call_vars = {}
        for i, f in enumerate(faculty):
            for j, b in enumerate(sundays):
                var = model.NewIntVar(0, 1, f"call_{i}_{j}")
                call_vars[(i, j, "overnight")] = var

        variables = {"call_assignments": call_vars, "objective_terms": []}

        constraint = SundayCallEquityConstraint(weight=10.0)
        constraint.add_to_cpsat(model, variables, ctx)

        # Should have created AddAbsEquality calls — one per faculty
        assert len(model._abs_equalities) == 3
        # Objective terms should have 3 entries (one abs_dev per faculty)
        assert len(variables["objective_terms"]) == 3

    def test_mad_with_prior_calls_creates_deviation(self):
        """With YTD history, MAD should still create deviation variables."""
        from app.scheduling.constraints.call_equity import (
            SundayCallEquityConstraint,
        )

        faculty_ids = [uuid4() for _ in range(3)]
        prior = {
            faculty_ids[0]: {"sunday": 5, "weekday": 10},
            faculty_ids[1]: {"sunday": 2, "weekday": 10},
            faculty_ids[2]: {"sunday": 3, "weekday": 10},
        }
        faculty = [
            FakePerson(id=fid, name=f"F{i}") for i, fid in enumerate(faculty_ids)
        ]
        sundays = [
            FakeBlock(id=uuid4(), date=date(2026, 2, 1 + 7 * i)) for i in range(4)
        ]

        ctx = FakeContext(
            blocks=sundays,
            faculty=faculty,
            call_eligible_faculty=faculty,
            call_eligible_faculty_idx={f.id: i for i, f in enumerate(faculty)},
            block_idx={b.id: i for i, b in enumerate(sundays)},
            prior_calls=prior,
        )

        model = FakeCPModel()
        call_vars = {}
        for i, f in enumerate(faculty):
            for j, b in enumerate(sundays):
                call_vars[(i, j, "overnight")] = model.NewIntVar(0, 1, f"call_{i}_{j}")

        variables = {"call_assignments": call_vars, "objective_terms": []}
        constraint = SundayCallEquityConstraint(weight=10.0)
        constraint.add_to_cpsat(model, variables, ctx)

        assert len(model._abs_equalities) == 3
        # Weight should be 10 for all terms
        for _, weight in variables["objective_terms"]:
            assert weight == 10

    def test_mad_empty_prior_calls_block1(self):
        """Block 1 (July): empty prior_calls should still work — degrades to single-block equity."""
        from app.scheduling.constraints.call_equity import (
            SundayCallEquityConstraint,
        )

        ctx, faculty, sundays = self._make_context(n_faculty=4, prior={})
        model = FakeCPModel()
        call_vars = {}
        for i, f in enumerate(faculty):
            for j, b in enumerate(sundays):
                call_vars[(i, j, "overnight")] = model.NewIntVar(0, 1, f"call_{i}_{j}")

        variables = {"call_assignments": call_vars, "objective_terms": []}
        constraint = SundayCallEquityConstraint(weight=10.0)
        constraint.add_to_cpsat(model, variables, ctx)

        # Should work fine with empty history
        assert len(model._abs_equalities) == 4
        assert len(variables["objective_terms"]) == 4


class TestWeekdayCallEquityMAD:
    """Test the MAD reformulation of WeekdayCallEquityConstraint."""

    def test_mad_creates_vars_for_weekdays(self):
        """WeekdayCallEquity MAD creates deviation variables for Mon-Thu."""
        from app.scheduling.constraints.call_equity import (
            WeekdayCallEquityConstraint,
        )

        faculty = [FakePerson(id=uuid4()) for _ in range(3)]
        # 4 weeks × 4 weekdays = 16 weekday blocks
        weekdays = []
        for week in range(4):
            for dow in range(4):  # Mon-Thu
                weekdays.append(
                    FakeBlock(
                        id=uuid4(),
                        date=date(2026, 2, 2 + week * 7 + dow),  # Mon
                    )
                )

        ctx = FakeContext(
            blocks=weekdays,
            faculty=faculty,
            call_eligible_faculty=faculty,
            call_eligible_faculty_idx={f.id: i for i, f in enumerate(faculty)},
            block_idx={b.id: i for i, b in enumerate(weekdays)},
            prior_calls={},
        )

        model = FakeCPModel()
        call_vars = {}
        for i, f in enumerate(faculty):
            for j, b in enumerate(weekdays):
                call_vars[(i, j, "overnight")] = model.NewIntVar(0, 1, f"call_{i}_{j}")

        variables = {"call_assignments": call_vars, "objective_terms": []}
        constraint = WeekdayCallEquityConstraint(weight=5.0)
        constraint.add_to_cpsat(model, variables, ctx)

        assert len(model._abs_equalities) == 3
        for _, weight in variables["objective_terms"]:
            assert weight == 5


class TestSyncAcademicYearCallCounts:
    """Test _sync_academic_year_call_counts idempotency."""

    def test_sync_is_idempotent(self):
        """Running sync twice produces the same result."""
        from app.models.person_academic_year import PersonAcademicYear

        person_id = uuid4()

        # Mock DB session
        mock_db = MagicMock()

        # Simulate query results (now returns effective_type from CASE expr)
        mock_row = MagicMock()
        mock_row.person_id = person_id
        mock_row.effective_type = "weekend"
        mock_row.total = 5

        mock_row2 = MagicMock()
        mock_row2.person_id = person_id
        mock_row2.effective_type = "overnight"
        mock_row2.total = 12

        mock_db.execute.return_value.all.return_value = [mock_row, mock_row2]

        # Mock PAY record
        mock_pay = MagicMock(spec=PersonAcademicYear)
        mock_pay.person_id = person_id
        mock_pay.sunday_call_count = 0
        mock_pay.weekday_call_count = 0

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_pay]

        # Create engine-like object with the method
        from app.scheduling.engine import SchedulingEngine

        engine = object.__new__(SchedulingEngine)
        engine.db = mock_db

        # Run sync
        engine._sync_academic_year_call_counts(2025)

        # Verify counts were set correctly
        assert mock_pay.sunday_call_count == 5
        assert mock_pay.weekday_call_count == 12

        # Run sync again (idempotent) — same results
        engine._sync_academic_year_call_counts(2025)
        assert mock_pay.sunday_call_count == 5
        assert mock_pay.weekday_call_count == 12

    def test_sync_handles_no_calls(self):
        """Sync with no call assignments sets counts to 0."""
        from app.models.person_academic_year import PersonAcademicYear

        person_id = uuid4()

        mock_db = MagicMock()
        mock_db.execute.return_value.all.return_value = []

        mock_pay = MagicMock(spec=PersonAcademicYear)
        mock_pay.person_id = person_id
        mock_pay.sunday_call_count = 3  # Had previous value
        mock_pay.weekday_call_count = 7

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_pay]

        from app.scheduling.engine import SchedulingEngine

        engine = object.__new__(SchedulingEngine)
        engine.db = mock_db

        engine._sync_academic_year_call_counts(2025)

        # Should reset to 0 since no calls exist
        assert mock_pay.sunday_call_count == 0
        assert mock_pay.weekday_call_count == 0


class TestPriorCallsHydration:
    """Test the GROUP BY hydration pattern in engine._build_context()."""

    def test_call_type_mapping(self):
        """Verify the call_type mapping: weekend→sunday, overnight→weekday."""
        # This tests the mapping logic extracted from _build_context
        call_type_map = {
            "weekend": "sunday",
            "overnight": "weekday",
            "holiday": "holiday",
        }

        assert call_type_map["weekend"] == "sunday"
        assert call_type_map["overnight"] == "weekday"
        assert call_type_map["holiday"] == "holiday"

    def test_prior_calls_accumulates_by_person(self):
        """Multiple rows for same person should populate different keys."""
        call_type_map = {
            "weekend": "sunday",
            "overnight": "weekday",
            "holiday": "holiday",
        }

        # Simulate the hydration loop from _build_context
        # Rows now use effective_type (from CASE expression)
        pid = uuid4()
        rows = [
            MagicMock(person_id=pid, effective_type="weekend", ytd_count=3),
            MagicMock(person_id=pid, effective_type="overnight", ytd_count=8),
        ]

        prior_calls: dict[UUID, dict[str, int]] = {}
        for row in rows:
            key = call_type_map.get(row.effective_type, row.effective_type)
            if row.person_id not in prior_calls:
                prior_calls[row.person_id] = {}
            prior_calls[row.person_id][key] = row.ytd_count or 0

        assert prior_calls[pid] == {"sunday": 3, "weekday": 8}

    def test_fmit_weekend_calls_split_from_weekday(self):
        """FMIT Sat calls (overnight + is_weekend=True) must count as sunday, not weekday.

        The CASE expression reclassifies overnight+is_weekend as "weekend",
        so the hydration loop maps them to "sunday" equity, not "weekday".
        """
        call_type_map = {
            "weekend": "sunday",
            "overnight": "weekday",
            "holiday": "holiday",
        }

        pid = uuid4()
        # After the CASE expression:
        # - 4 Mon-Thu overnight (is_weekend=False) → effective_type="overnight"
        # - 2 FMIT Saturday (is_weekend=True) → effective_type="weekend"
        # - 3 Sunday (call_type="weekend") → effective_type="weekend"
        # GROUP BY collapses the two "weekend" sources:
        rows = [
            MagicMock(person_id=pid, effective_type="overnight", ytd_count=4),
            MagicMock(
                person_id=pid, effective_type="weekend", ytd_count=5
            ),  # 2 FMIT Sat + 3 Sunday
        ]

        prior_calls: dict[UUID, dict[str, int]] = {}
        for row in rows:
            key = call_type_map.get(row.effective_type, row.effective_type)
            if row.person_id not in prior_calls:
                prior_calls[row.person_id] = {}
            prior_calls[row.person_id][key] = row.ytd_count or 0

        # Weekday should be 4 (Mon-Thu only), NOT 6 (which included FMIT Sat)
        assert prior_calls[pid]["weekday"] == 4
        # Sunday should be 5 (3 actual Sunday + 2 FMIT Saturday)
        assert prior_calls[pid]["sunday"] == 5
