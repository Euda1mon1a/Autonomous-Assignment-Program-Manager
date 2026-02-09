"""Tests for Pareto optimization schemas (Pydantic validation, model_validator, Field bounds)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.pareto import (
    ObjectiveDirection,
    ObjectiveName,
    ParetoObjective,
    ParetoSolution,
    ParetoConstraint,
    ParetoResult,
    ParetoOptimizeRequest,
    ParetoOptimizeResponse,
    SolutionRankRequest,
    RankedSolution,
    SolutionRankResponse,
)


# ===========================================================================
# Enum Tests
# ===========================================================================


class TestObjectiveDirection:
    def test_values(self):
        assert ObjectiveDirection.MINIMIZE.value == "minimize"
        assert ObjectiveDirection.MAXIMIZE.value == "maximize"

    def test_count(self):
        assert len(ObjectiveDirection) == 2

    def test_is_str(self):
        assert isinstance(ObjectiveDirection.MINIMIZE, str)


class TestObjectiveName:
    def test_values(self):
        assert ObjectiveName.FAIRNESS.value == "fairness"
        assert ObjectiveName.COVERAGE.value == "coverage"
        assert ObjectiveName.PREFERENCE_SATISFACTION.value == "preference_satisfaction"
        assert ObjectiveName.WORKLOAD_BALANCE.value == "workload_balance"
        assert ObjectiveName.CONSECUTIVE_DAYS.value == "consecutive_days"
        assert ObjectiveName.SPECIALTY_DISTRIBUTION.value == "specialty_distribution"

    def test_count(self):
        assert len(ObjectiveName) == 6


# ===========================================================================
# ParetoObjective Tests
# ===========================================================================


class TestParetoObjective:
    def test_defaults(self):
        r = ParetoObjective(name=ObjectiveName.FAIRNESS)
        assert r.weight == 1.0
        assert r.direction == ObjectiveDirection.MAXIMIZE
        assert r.target_value is None

    # --- weight ge=0.0, le=1.0 ---

    def test_weight_boundaries(self):
        r = ParetoObjective(name=ObjectiveName.COVERAGE, weight=0.0)
        assert r.weight == 0.0

        r = ParetoObjective(name=ObjectiveName.COVERAGE, weight=1.0)
        assert r.weight == 1.0

    def test_weight_negative(self):
        with pytest.raises(ValidationError):
            ParetoObjective(name=ObjectiveName.FAIRNESS, weight=-0.1)

    def test_weight_above_one(self):
        with pytest.raises(ValidationError):
            ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.1)

    def test_with_target_value(self):
        r = ParetoObjective(
            name=ObjectiveName.WORKLOAD_BALANCE,
            weight=0.8,
            direction=ObjectiveDirection.MINIMIZE,
            target_value=0.95,
        )
        assert r.target_value == 0.95


# ===========================================================================
# ParetoSolution Tests
# ===========================================================================


class TestParetoSolution:
    def test_valid(self):
        r = ParetoSolution(
            solution_id=1,
            objective_values={"fairness": 0.9, "coverage": 0.95},
            decision_variables={"person1": "block1"},
        )
        assert r.is_feasible is True
        assert r.constraint_violations == []
        assert r.rank is None
        assert r.crowding_distance is None

    def test_infeasible(self):
        r = ParetoSolution(
            solution_id=2,
            objective_values={"fairness": 0.5},
            decision_variables={},
            is_feasible=False,
            constraint_violations=["80-hour violation"],
        )
        assert r.is_feasible is False
        assert len(r.constraint_violations) == 1


# ===========================================================================
# ParetoConstraint Tests
# ===========================================================================


class TestParetoConstraint:
    def test_valid(self):
        r = ParetoConstraint(constraint_type="max_consecutive_days")
        assert r.parameters == {}
        assert r.is_hard is True

    def test_with_params(self):
        r = ParetoConstraint(
            constraint_type="min_rest_hours",
            parameters={"hours": 8},
            is_hard=False,
        )
        assert r.parameters == {"hours": 8}
        assert r.is_hard is False


# ===========================================================================
# ParetoResult Tests
# ===========================================================================


class TestParetoResult:
    def test_valid(self):
        r = ParetoResult(
            solutions=[],
            frontier_indices=[],
            total_solutions=0,
            execution_time_seconds=30.0,
        )
        assert r.hypervolume is None
        assert r.convergence_metric is None
        assert r.algorithm == "NSGA-II"
        assert r.termination_reason is None


# ===========================================================================
# ParetoOptimizeRequest Tests
# ===========================================================================


class TestParetoOptimizeRequest:
    def _make_objectives(self, n=2):
        names = list(ObjectiveName)[:n]
        return [ParetoObjective(name=name) for name in names]

    def test_valid_minimal(self):
        r = ParetoOptimizeRequest(objectives=self._make_objectives(2))
        assert r.constraints == []
        assert r.population_size == 100
        assert r.n_generations == 100
        assert r.timeout_seconds == 300.0
        assert r.seed is None
        assert r.person_ids is None
        assert r.block_ids is None

    # --- objectives min_length=2 ---

    def test_objectives_one(self):
        with pytest.raises(ValidationError):
            ParetoOptimizeRequest(objectives=self._make_objectives(1))

    def test_objectives_multiple(self):
        r = ParetoOptimizeRequest(objectives=self._make_objectives(4))
        assert len(r.objectives) == 4

    # --- population_size ge=10, le=1000 ---

    def test_population_size_boundaries(self):
        r = ParetoOptimizeRequest(
            objectives=self._make_objectives(), population_size=10
        )
        assert r.population_size == 10

        r = ParetoOptimizeRequest(
            objectives=self._make_objectives(), population_size=1000
        )
        assert r.population_size == 1000

    def test_population_size_below_min(self):
        with pytest.raises(ValidationError):
            ParetoOptimizeRequest(objectives=self._make_objectives(), population_size=9)

    def test_population_size_above_max(self):
        with pytest.raises(ValidationError):
            ParetoOptimizeRequest(
                objectives=self._make_objectives(), population_size=1001
            )

    # --- n_generations ge=10, le=1000 ---

    def test_n_generations_boundaries(self):
        r = ParetoOptimizeRequest(objectives=self._make_objectives(), n_generations=10)
        assert r.n_generations == 10

        r = ParetoOptimizeRequest(
            objectives=self._make_objectives(), n_generations=1000
        )
        assert r.n_generations == 1000

    def test_n_generations_below_min(self):
        with pytest.raises(ValidationError):
            ParetoOptimizeRequest(objectives=self._make_objectives(), n_generations=9)

    def test_n_generations_above_max(self):
        with pytest.raises(ValidationError):
            ParetoOptimizeRequest(
                objectives=self._make_objectives(), n_generations=1001
            )

    # --- timeout_seconds ge=10.0, le=3600.0 ---

    def test_timeout_boundaries(self):
        r = ParetoOptimizeRequest(
            objectives=self._make_objectives(), timeout_seconds=10.0
        )
        assert r.timeout_seconds == 10.0

        r = ParetoOptimizeRequest(
            objectives=self._make_objectives(), timeout_seconds=3600.0
        )
        assert r.timeout_seconds == 3600.0

    def test_timeout_below_min(self):
        with pytest.raises(ValidationError):
            ParetoOptimizeRequest(
                objectives=self._make_objectives(), timeout_seconds=9.9
            )

    def test_timeout_above_max(self):
        with pytest.raises(ValidationError):
            ParetoOptimizeRequest(
                objectives=self._make_objectives(), timeout_seconds=3600.1
            )

    # --- model_validator: weights sum ---

    def test_weights_sum_valid(self):
        objs = [
            ParetoObjective(name=ObjectiveName.FAIRNESS, weight=0.5),
            ParetoObjective(name=ObjectiveName.COVERAGE, weight=0.5),
        ]
        r = ParetoOptimizeRequest(objectives=objs)
        assert len(r.objectives) == 2

    def test_with_ids(self):
        r = ParetoOptimizeRequest(
            objectives=self._make_objectives(),
            person_ids=[uuid4(), uuid4()],
            block_ids=[uuid4()],
        )
        assert len(r.person_ids) == 2
        assert len(r.block_ids) == 1


# ===========================================================================
# ParetoOptimizeResponse Tests
# ===========================================================================


class TestParetoOptimizeResponse:
    def test_valid(self):
        r = ParetoOptimizeResponse(
            success=True,
            message="Optimization complete",
        )
        assert r.result is None
        assert r.error is None
        assert r.recommended_solution_id is None


# ===========================================================================
# SolutionRankRequest Tests
# ===========================================================================


class TestSolutionRankRequest:
    def test_valid(self):
        r = SolutionRankRequest(
            solution_ids=[1, 2, 3],
            weights={"fairness": 0.6, "coverage": 0.4},
        )
        assert r.normalization == "minmax"

    # --- solution_ids min_length=1 ---

    def test_empty_solution_ids(self):
        with pytest.raises(ValidationError):
            SolutionRankRequest(solution_ids=[], weights={"fairness": 1.0})

    # --- model_validator: weights positive ---

    def test_negative_weight(self):
        with pytest.raises(ValidationError):
            SolutionRankRequest(
                solution_ids=[1],
                weights={"fairness": -0.5},
            )

    def test_zero_weight_allowed(self):
        r = SolutionRankRequest(
            solution_ids=[1],
            weights={"fairness": 0.0},
        )
        assert r.weights["fairness"] == 0.0


# ===========================================================================
# RankedSolution Tests
# ===========================================================================


class TestRankedSolution:
    def test_valid(self):
        r = RankedSolution(
            solution_id=1,
            rank=1,
            score=0.95,
            objective_values={"fairness": 0.9},
            weighted_score_breakdown={"fairness": 0.54},
        )
        assert r.rank == 1


# ===========================================================================
# SolutionRankResponse Tests
# ===========================================================================


class TestSolutionRankResponse:
    def test_valid(self):
        r = SolutionRankResponse(
            success=True,
            normalization_used="minmax",
        )
        assert r.ranked_solutions == []
        assert r.message == ""
