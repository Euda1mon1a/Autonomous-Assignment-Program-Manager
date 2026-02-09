"""Tests for parallel solver (pure async logic, no DB required)."""

import asyncio

import pytest

from app.scheduling.optimizer.parallel_solver import (
    AdaptiveParallelSolver,
    ParallelSolver,
    SolverResult,
)


# ==================== Helpers ====================


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


async def _good_solver(problem: dict, solver_id: int) -> dict:
    """Solver that returns a valid solution."""
    return {
        "objective_value": 100 - solver_id * 10,
        "iterations": 1000 + solver_id * 100,
        "assignments": [{"person_id": "p1", "block_id": "b1"}],
    }


async def _failing_solver(problem: dict, solver_id: int) -> dict:
    """Solver that raises an exception."""
    raise RuntimeError(f"Solver {solver_id} crashed")


async def _slow_solver(problem: dict, solver_id: int) -> dict:
    """Solver that takes too long."""
    await asyncio.sleep(10)
    return {"objective_value": 50, "iterations": 5000}


async def _mixed_solver(problem: dict, solver_id: int) -> dict:
    """Solver 0 succeeds, solver 1 fails."""
    if solver_id == 1:
        raise RuntimeError("Solver 1 crashed")
    return {"objective_value": 200 - solver_id * 50, "iterations": 1000}


async def _strategy_echo_solver(problem: dict, solver_id: int) -> dict:
    """Solver that echoes strategy params back in solution."""
    return {
        "objective_value": solver_id,
        "iterations": 1,
        "heuristic": problem.get("heuristic"),
        "random_seed": problem.get("random_seed"),
        "search_strategy": problem.get("search_strategy"),
    }


# ==================== SolverResult Tests ====================


class TestSolverResult:
    """Test SolverResult dataclass."""

    def test_construction(self):
        r = SolverResult(
            solver_id=0,
            success=True,
            solution={"assignments": []},
            objective_value=42.5,
            duration_seconds=1.2,
            iterations=500,
        )
        assert r.solver_id == 0
        assert r.success is True
        assert r.objective_value == 42.5
        assert r.iterations == 500
        assert r.error is None

    def test_failed_result(self):
        r = SolverResult(
            solver_id=1,
            success=False,
            solution=None,
            objective_value=float("inf"),
            duration_seconds=0.1,
            iterations=0,
            error="timeout",
        )
        assert r.success is False
        assert r.error == "timeout"
        assert r.solution is None

    def test_default_error_none(self):
        r = SolverResult(
            solver_id=0,
            success=True,
            solution={},
            objective_value=0,
            duration_seconds=0,
            iterations=0,
        )
        assert r.error is None


# ==================== ParallelSolver Init Tests ====================


class TestParallelSolverInit:
    """Test ParallelSolver constructor."""

    def test_defaults(self):
        s = ParallelSolver()
        assert s.num_solvers == 4
        assert s.timeout_seconds == 300
        assert s.early_stop_threshold is None
        assert s.results == []

    def test_custom_params(self):
        s = ParallelSolver(num_solvers=8, timeout_seconds=60, early_stop_threshold=10.0)
        assert s.num_solvers == 8
        assert s.timeout_seconds == 60
        assert s.early_stop_threshold == 10.0


# ==================== ParallelSolver.solve Tests ====================


class TestParallelSolverSolve:
    """Test ParallelSolver.solve method."""

    def test_returns_best_result(self):
        """Best solver (lowest objective) selected."""
        s = ParallelSolver(num_solvers=3, timeout_seconds=5)
        result = _run(s.solve({"test": True}, _good_solver))
        assert result.success is True
        # solver 0: 100, solver 1: 90, solver 2: 80 -> best is 80
        assert result.objective_value == 80
        assert result.solver_id == 2

    def test_all_solvers_fail(self):
        """All failures -> SolverResult with success=False."""
        s = ParallelSolver(num_solvers=2, timeout_seconds=5)
        result = _run(s.solve({}, _failing_solver))
        assert result.success is False
        assert result.solver_id == -1
        assert result.error == "All solvers failed"
        assert result.objective_value == float("inf")

    def test_timeout_returns_failure(self):
        """Solver exceeding timeout returns failure."""
        s = ParallelSolver(num_solvers=1, timeout_seconds=1)
        result = _run(s.solve({}, _slow_solver))
        # Solver times out -> no valid results -> all failed
        assert result.success is False

    def test_mixed_success_and_failure(self):
        """Some solvers succeed, some fail -> best of successful returned."""
        s = ParallelSolver(num_solvers=3, timeout_seconds=5)
        result = _run(s.solve({}, _mixed_solver))
        assert result.success is True
        # solver 0: 200, solver 1: fails, solver 2: 100
        assert result.objective_value == 100

    def test_strategy_variants_applied(self):
        """Strategy variants merged into problem data."""
        s = ParallelSolver(num_solvers=2, timeout_seconds=5)
        strategies = [
            {"custom_key": "value_0"},
            {"custom_key": "value_1"},
        ]

        async def echo_solver(problem, solver_id):
            return {
                "objective_value": solver_id,
                "iterations": 1,
                "custom_key": problem.get("custom_key"),
            }

        result = _run(s.solve({}, echo_solver, strategies))
        # Best is solver_id=0 (objective 0)
        assert result.solution["custom_key"] == "value_0"

    def test_more_solvers_than_strategies(self):
        """Extra solvers get plain problem_data copy."""
        s = ParallelSolver(num_solvers=3, timeout_seconds=5)
        strategies = [{"extra": "yes"}]
        result = _run(s.solve({"base": True}, _good_solver, strategies))
        assert result.success is True

    def test_single_solver(self):
        s = ParallelSolver(num_solvers=1, timeout_seconds=5)
        result = _run(s.solve({}, _good_solver))
        assert result.success is True
        assert result.solver_id == 0
        assert result.objective_value == 100

    def test_duration_positive(self):
        s = ParallelSolver(num_solvers=1, timeout_seconds=5)
        result = _run(s.solve({}, _good_solver))
        assert result.duration_seconds >= 0


# ==================== _run_solver_instance Tests ====================


class TestRunSolverInstance:
    """Test _run_solver_instance method."""

    def test_successful_run(self):
        s = ParallelSolver(timeout_seconds=5)
        result = _run(s._run_solver_instance(0, {}, _good_solver))
        assert result.success is True
        assert result.solver_id == 0
        assert result.objective_value == 100
        assert result.iterations == 1000

    def test_timeout_run(self):
        s = ParallelSolver(timeout_seconds=1)
        result = _run(s._run_solver_instance(0, {}, _slow_solver))
        assert result.success is False
        assert result.error == "timeout"
        assert result.objective_value == float("inf")

    def test_exception_run(self):
        s = ParallelSolver(timeout_seconds=5)
        result = _run(s._run_solver_instance(0, {}, _failing_solver))
        assert result.success is False
        assert "crashed" in result.error
        assert result.objective_value == float("inf")

    def test_missing_objective_defaults_inf(self):
        async def no_objective(problem, solver_id):
            return {"iterations": 10}

        s = ParallelSolver(timeout_seconds=5)
        result = _run(s._run_solver_instance(0, {}, no_objective))
        assert result.success is True
        assert result.objective_value == float("inf")

    def test_missing_iterations_defaults_zero(self):
        async def no_iterations(problem, solver_id):
            return {"objective_value": 50}

        s = ParallelSolver(timeout_seconds=5)
        result = _run(s._run_solver_instance(0, {}, no_iterations))
        assert result.iterations == 0


# ==================== Heuristic / Strategy Tests ====================


class TestHeuristicAndStrategy:
    """Test _get_heuristic_for_solver and _get_search_strategy_for_solver."""

    def test_heuristic_round_robin(self):
        s = ParallelSolver()
        assert s._get_heuristic_for_solver(0) == "greedy"
        assert s._get_heuristic_for_solver(1) == "random"
        assert s._get_heuristic_for_solver(2) == "balanced"
        assert s._get_heuristic_for_solver(3) == "minimize_conflicts"
        assert s._get_heuristic_for_solver(4) == "greedy"  # Wraps around

    def test_search_strategy_round_robin(self):
        s = ParallelSolver()
        assert s._get_search_strategy_for_solver(0) == "depth_first"
        assert s._get_search_strategy_for_solver(1) == "breadth_first"
        assert s._get_search_strategy_for_solver(2) == "best_first"
        assert s._get_search_strategy_for_solver(3) == "random"
        assert s._get_search_strategy_for_solver(4) == "depth_first"


# ==================== solve_with_diversification Tests ====================


class TestSolveWithDiversification:
    """Test solve_with_diversification method."""

    def test_generates_strategies(self):
        """Each solver gets different heuristic/strategy."""
        s = ParallelSolver(num_solvers=4, timeout_seconds=5)
        result = _run(s.solve_with_diversification({}, _strategy_echo_solver))
        assert result.success is True
        # Best is solver_id=0 (objective 0)
        assert result.solution["heuristic"] == "greedy"
        assert result.solution["random_seed"] == 0
        assert result.solution["search_strategy"] == "depth_first"

    def test_uses_different_seeds(self):
        """Each solver gets seed = solver_id * 1000."""
        s = ParallelSolver(num_solvers=2, timeout_seconds=5)

        collected = []

        async def collecting_solver(problem, solver_id):
            collected.append(problem.get("random_seed"))
            return {"objective_value": solver_id, "iterations": 1}

        _run(s.solve_with_diversification({}, collecting_solver))
        assert 0 in collected
        assert 1000 in collected


# ==================== AdaptiveParallelSolver Tests ====================


class TestAdaptiveParallelSolver:
    """Test AdaptiveParallelSolver subclass."""

    def test_inherits_from_parallel_solver(self):
        s = AdaptiveParallelSolver()
        assert isinstance(s, ParallelSolver)
        assert s.num_solvers == 4

    def test_solve_adaptive_returns_best(self):
        """Basic adaptive solve returns best result."""
        s = AdaptiveParallelSolver(num_solvers=2, timeout_seconds=5)
        result = _run(s.solve_adaptive({}, _good_solver, checkpoint_interval=1))
        assert result.success is True
        # solver 0: 100, solver 1: 90
        assert result.objective_value == 90

    def test_solve_adaptive_all_fail(self):
        """When all solvers fail, returns a failed result."""
        s = AdaptiveParallelSolver(num_solvers=2, timeout_seconds=5)
        result = _run(s.solve_adaptive({}, _failing_solver, checkpoint_interval=1))
        assert result.success is False
        assert result.objective_value == float("inf")

    def test_solve_adaptive_early_stop(self):
        """When threshold is met, returns early."""
        s = AdaptiveParallelSolver(
            num_solvers=2, timeout_seconds=10, early_stop_threshold=95
        )

        async def fast_solver(problem, solver_id):
            return {"objective_value": 90, "iterations": 100}

        result = _run(s.solve_adaptive({}, fast_solver, checkpoint_interval=1))
        assert result.success is True
        assert result.objective_value <= 95

    def test_can_use_base_solve(self):
        """AdaptiveParallelSolver can also use base class solve()."""
        s = AdaptiveParallelSolver(num_solvers=2, timeout_seconds=5)
        result = _run(s.solve({}, _good_solver))
        assert result.success is True
