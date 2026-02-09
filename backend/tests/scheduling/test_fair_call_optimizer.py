"""Tests for fair call optimizer CP-SAT solver (pure logic, no DB required)."""

from datetime import date

import pytest
from ortools.sat.python import cp_model

from app.scheduling.fair_call_optimizer import (
    CallScheduleInput,
    CallScheduleModel,
    CallScheduleResult,
    _status_to_string,
    _validate_input,
    optimize_call_schedule,
)


# ==================== Helpers ====================


def _make_input(
    num_days: int = 4,
    num_faculty: int = 2,
    target: int = 2,
) -> CallScheduleInput:
    """Build a simple balanced CallScheduleInput."""
    days = [date(2025, 1, i + 1) for i in range(num_days)]
    faculty = [f"FAC-{i:03d}" for i in range(1, num_faculty + 1)]
    target_calls = dict.fromkeys(faculty, target)
    eligibility = {day: set(faculty) for day in days}
    return CallScheduleInput(
        days=days,
        faculty=faculty,
        target_calls=target_calls,
        eligibility=eligibility,
    )


# ==================== Dataclass Tests ====================


class TestCallScheduleInput:
    """Test CallScheduleInput dataclass."""

    def test_basic_construction(self):
        inp = _make_input()
        assert len(inp.days) == 4
        assert len(inp.faculty) == 2
        assert inp.max_calls is None

    def test_with_max_calls(self):
        inp = _make_input()
        inp.max_calls = {"FAC-001": 3}
        assert inp.max_calls["FAC-001"] == 3


class TestCallScheduleResult:
    """Test CallScheduleResult dataclass."""

    def test_basic_construction(self):
        result = CallScheduleResult(
            schedule={date(2025, 1, 1): "FAC-001"},
            deviations={"FAC-001": 0},
            max_deviation=0,
            solve_time_seconds=0.5,
            status="optimal",
        )
        assert result.status == "optimal"
        assert result.objective_value == 0

    def test_default_objective_value(self):
        result = CallScheduleResult(
            schedule={},
            deviations={},
            max_deviation=0,
            solve_time_seconds=0.1,
            status="infeasible",
        )
        assert result.objective_value == 0


# ==================== Validation Tests ====================


class TestValidateInput:
    """Test _validate_input function."""

    def test_valid_input_passes(self):
        inp = _make_input()
        _validate_input(inp)  # Should not raise

    def test_no_days_raises(self):
        inp = _make_input()
        inp.days = []
        with pytest.raises(ValueError, match="No call days"):
            _validate_input(inp)

    def test_no_faculty_raises(self):
        inp = _make_input()
        inp.faculty = []
        with pytest.raises(ValueError, match="No faculty"):
            _validate_input(inp)

    def test_missing_target_calls_raises(self):
        inp = _make_input()
        inp.target_calls.pop("FAC-001")
        with pytest.raises(ValueError, match="missing target_calls"):
            _validate_input(inp)

    def test_missing_eligibility_day_raises(self):
        inp = _make_input()
        del inp.eligibility[inp.days[0]]
        with pytest.raises(ValueError, match="missing eligibility"):
            _validate_input(inp)

    def test_empty_eligibility_raises(self):
        inp = _make_input()
        inp.eligibility[inp.days[0]] = set()
        with pytest.raises(ValueError, match="no eligible faculty"):
            _validate_input(inp)

    def test_unknown_faculty_in_eligibility_raises(self):
        inp = _make_input()
        inp.eligibility[inp.days[0]].add("UNKNOWN-FAC")
        with pytest.raises(ValueError, match="unknown faculty"):
            _validate_input(inp)


# ==================== Status String Tests ====================


class TestStatusToString:
    """Test _status_to_string helper."""

    def test_optimal(self):
        assert _status_to_string(cp_model.OPTIMAL) == "optimal"

    def test_feasible(self):
        assert _status_to_string(cp_model.FEASIBLE) == "feasible"

    def test_infeasible(self):
        assert _status_to_string(cp_model.INFEASIBLE) == "infeasible"

    def test_unknown(self):
        assert _status_to_string(cp_model.UNKNOWN) == "unknown"


# ==================== Model Building Tests ====================


class TestCallScheduleModel:
    """Test CallScheduleModel construction."""

    def test_model_builds_without_error(self):
        inp = _make_input()
        model = CallScheduleModel(inp)
        assert model.model is not None
        assert model.max_deviation is not None

    def test_assignment_variables_created(self):
        inp = _make_input(num_days=2, num_faculty=3)
        model = CallScheduleModel(inp)
        assert len(model.is_assigned) == 2
        for day in inp.days:
            assert len(model.is_assigned[day]) == 3

    def test_calls_assigned_variables(self):
        inp = _make_input(num_faculty=3)
        model = CallScheduleModel(inp)
        assert len(model.calls_assigned) == 3

    def test_deviation_variables(self):
        inp = _make_input(num_faculty=2)
        model = CallScheduleModel(inp)
        assert len(model.deviation) == 2
        assert len(model.abs_deviation) == 2


# ==================== Solver Tests ====================


class TestOptimizeCallSchedule:
    """Test optimize_call_schedule end-to-end."""

    def test_balanced_2x4_optimal(self):
        """2 faculty, 4 days, target 2 each -> perfectly balanced."""
        inp = _make_input(num_days=4, num_faculty=2, target=2)
        result = optimize_call_schedule(inp, time_limit_seconds=10.0)
        assert result.status in ("optimal", "feasible")
        assert len(result.schedule) == 4
        assert result.max_deviation == 0

    def test_all_days_covered(self):
        """Every day gets exactly one faculty member assigned."""
        inp = _make_input(num_days=6, num_faculty=3, target=2)
        result = optimize_call_schedule(inp, time_limit_seconds=10.0)
        assert result.status in ("optimal", "feasible")
        assert len(result.schedule) == 6
        for day in inp.days:
            assert day in result.schedule
            assert result.schedule[day] in inp.faculty

    def test_eligibility_respected(self):
        """Faculty only assigned to days they're eligible."""
        days = [date(2025, 1, 1), date(2025, 1, 2)]
        faculty = ["A", "B"]
        eligibility = {
            days[0]: {"A"},  # Only A eligible day 1
            days[1]: {"B"},  # Only B eligible day 2
        }
        inp = CallScheduleInput(
            days=days,
            faculty=faculty,
            target_calls={"A": 1, "B": 1},
            eligibility=eligibility,
        )
        result = optimize_call_schedule(inp, time_limit_seconds=10.0)
        assert result.status in ("optimal", "feasible")
        assert result.schedule[days[0]] == "A"
        assert result.schedule[days[1]] == "B"

    def test_deviations_reported(self):
        inp = _make_input(num_days=4, num_faculty=2, target=2)
        result = optimize_call_schedule(inp, time_limit_seconds=10.0)
        assert len(result.deviations) == 2
        for fac in inp.faculty:
            assert fac in result.deviations

    def test_solve_time_positive(self):
        inp = _make_input()
        result = optimize_call_schedule(inp, time_limit_seconds=10.0)
        assert result.solve_time_seconds > 0

    def test_max_calls_respected(self):
        """Hard cap on max calls prevents over-assignment."""
        days = [date(2025, 1, i + 1) for i in range(4)]
        faculty = ["A", "B"]
        inp = CallScheduleInput(
            days=days,
            faculty=faculty,
            target_calls={"A": 3, "B": 1},
            eligibility={d: {"A", "B"} for d in days},
            max_calls={"A": 2},  # Cap A at 2
        )
        result = optimize_call_schedule(inp, time_limit_seconds=10.0)
        assert result.status in ("optimal", "feasible")
        # Count A's assignments
        a_count = sum(1 for fac in result.schedule.values() if fac == "A")
        assert a_count <= 2

    def test_3_faculty_5_days_fairness(self):
        """3 faculty, 5 days: expect max_deviation <= 1."""
        days = [date(2025, 1, i + 1) for i in range(5)]
        faculty = ["A", "B", "C"]
        inp = CallScheduleInput(
            days=days,
            faculty=faculty,
            target_calls={"A": 2, "B": 2, "C": 1},
            eligibility={d: set(faculty) for d in days},
        )
        result = optimize_call_schedule(inp, time_limit_seconds=10.0)
        assert result.status in ("optimal", "feasible")
        assert result.max_deviation <= 1

    def test_single_faculty_single_day(self):
        """Trivial case: 1 faculty, 1 day."""
        inp = CallScheduleInput(
            days=[date(2025, 1, 1)],
            faculty=["A"],
            target_calls={"A": 1},
            eligibility={date(2025, 1, 1): {"A"}},
        )
        result = optimize_call_schedule(inp, time_limit_seconds=5.0)
        assert result.status in ("optimal", "feasible")
        assert result.schedule[date(2025, 1, 1)] == "A"
        assert result.max_deviation == 0


# ==================== Phase Tests ====================


class TestPhases:
    """Test individual solver phases."""

    def test_phase1_returns_valid_status(self):
        inp = _make_input()
        model = CallScheduleModel(inp)
        status = model.minimize_max_deviation(10.0)
        assert status in (
            cp_model.OPTIMAL,
            cp_model.FEASIBLE,
            cp_model.INFEASIBLE,
            cp_model.UNKNOWN,
        )

    def test_phase2_after_phase1(self):
        inp = _make_input()
        model = CallScheduleModel(inp)
        status1 = model.minimize_max_deviation(10.0)
        assert status1 in (cp_model.OPTIMAL, cp_model.FEASIBLE)

        # Extract max_dev from phase 1
        solver1 = cp_model.CpSolver()
        solver1.parameters.max_time_in_seconds = 10.0
        solver1.Solve(model.model)
        max_dev = solver1.Value(model.max_deviation)

        status2, solver2 = model.minimize_sum_deviations(max_dev, 10.0)
        assert status2 in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    def test_extract_solution(self):
        inp = _make_input(num_days=2, num_faculty=2, target=1)
        model = CallScheduleModel(inp)
        model.minimize_max_deviation(10.0)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0
        solver.Solve(model.model)

        schedule = model.extract_solution(solver)
        assert len(schedule) == 2
        for day in inp.days:
            assert day in schedule
            assert schedule[day] in inp.faculty

    def test_extract_deviations(self):
        inp = _make_input(num_days=4, num_faculty=2, target=2)
        model = CallScheduleModel(inp)
        model.minimize_max_deviation(10.0)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0
        solver.Solve(model.model)

        deviations = model.extract_deviations(solver)
        assert len(deviations) == 2
        for fac in inp.faculty:
            assert fac in deviations
