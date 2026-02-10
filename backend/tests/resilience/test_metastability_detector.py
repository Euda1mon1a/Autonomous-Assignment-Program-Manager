"""Tests for metastability detector (pure logic, no DB)."""

import math
from datetime import datetime

import pytest

from app.resilience.metastability_detector import (
    EscapeStrategy,
    MetastabilityAnalysis,
    MetastabilityDetector,
    MetastableState,
    SolverState,
)


# -- EscapeStrategy enum -----------------------------------------------------


class TestEscapeStrategy:
    def test_values(self):
        assert EscapeStrategy.CONTINUE_SEARCH == "continue_search"
        assert EscapeStrategy.INCREASE_TEMPERATURE == "increase_temperature"
        assert EscapeStrategy.BASIN_HOPPING == "basin_hopping"
        assert EscapeStrategy.RESTART_NEW_SEED == "restart_new_seed"
        assert EscapeStrategy.ACCEPT_LOCAL_OPTIMUM == "accept_local_optimum"

    def test_member_count(self):
        assert len(EscapeStrategy) == 5

    def test_is_string_enum(self):
        assert isinstance(EscapeStrategy.CONTINUE_SEARCH, str)


# -- MetastableState dataclass ------------------------------------------------


class TestMetastableState:
    def test_creation(self):
        state = MetastableState(
            objective_value=85.0,
            constraint_violations=0,
            barrier_height=5.0,
            basin_size=10,
            escape_probability=0.2,
            plateau_duration=60,
            best_objective=80.0,
        )
        assert state.objective_value == 85.0
        assert state.constraint_violations == 0
        assert state.barrier_height == 5.0
        assert state.basin_size == 10
        assert state.escape_probability == 0.2
        assert state.plateau_duration == 60
        assert state.best_objective == 80.0

    def test_defaults(self):
        state = MetastableState(
            objective_value=100.0,
            constraint_violations=0,
            barrier_height=1.0,
            basin_size=1,
            escape_probability=0.5,
            plateau_duration=10,
            best_objective=100.0,
        )
        assert state.temperature == 1.0
        assert state.iteration == 0
        assert isinstance(state.timestamp, datetime)

    def test_custom_optional_fields(self):
        state = MetastableState(
            objective_value=50.0,
            constraint_violations=3,
            barrier_height=10.0,
            basin_size=5,
            escape_probability=0.01,
            plateau_duration=100,
            best_objective=40.0,
            temperature=5.0,
            iteration=500,
        )
        assert state.temperature == 5.0
        assert state.iteration == 500


# -- SolverState dataclass ----------------------------------------------------


class TestSolverState:
    def test_creation(self):
        state = SolverState(iteration=10, objective_value=95.0)
        assert state.iteration == 10
        assert state.objective_value == 95.0

    def test_defaults(self):
        state = SolverState(iteration=0, objective_value=100.0)
        assert state.constraint_violations == 0
        assert state.num_assignments == 0
        assert state.temperature == 1.0
        assert state.random_seed is None
        assert state.metadata == {}

    def test_custom_fields(self):
        state = SolverState(
            iteration=50,
            objective_value=80.0,
            constraint_violations=2,
            num_assignments=15,
            temperature=3.0,
            random_seed=42,
            metadata={"solver": "cpsat"},
        )
        assert state.constraint_violations == 2
        assert state.num_assignments == 15
        assert state.temperature == 3.0
        assert state.random_seed == 42
        assert state.metadata == {"solver": "cpsat"}


# -- MetastabilityAnalysis dataclass ------------------------------------------


class TestMetastabilityAnalysis:
    def test_creation(self):
        analysis = MetastabilityAnalysis(
            is_metastable=True,
            metastable_state=None,
            recommended_strategy=EscapeStrategy.BASIN_HOPPING,
            plateau_detected=True,
            barrier_height=8.0,
            escape_probability=0.05,
        )
        assert analysis.is_metastable is True
        assert analysis.recommended_strategy == EscapeStrategy.BASIN_HOPPING
        assert analysis.plateau_detected is True

    def test_defaults(self):
        analysis = MetastabilityAnalysis(
            is_metastable=False,
            metastable_state=None,
            recommended_strategy=EscapeStrategy.CONTINUE_SEARCH,
            plateau_detected=False,
            barrier_height=0.0,
            escape_probability=1.0,
        )
        assert isinstance(analysis.analysis_timestamp, datetime)
        assert analysis.trajectory_length == 0
        assert analysis.best_iteration == 0
        assert analysis.stagnation_duration == 0


# -- MetastabilityDetector init -----------------------------------------------


class TestMetastabilityDetectorInit:
    def test_defaults(self):
        d = MetastabilityDetector()
        assert d.plateau_threshold == 0.01
        assert d.plateau_window == 100
        assert d.min_stagnation == 50
        assert d.temperature == 1.0

    def test_custom(self):
        d = MetastabilityDetector(
            plateau_threshold=0.05,
            plateau_window=50,
            min_stagnation=20,
            temperature=2.0,
        )
        assert d.plateau_threshold == 0.05
        assert d.plateau_window == 50
        assert d.min_stagnation == 20
        assert d.temperature == 2.0


# -- detect_plateau -----------------------------------------------------------


class TestDetectPlateau:
    def test_not_enough_data(self):
        d = MetastabilityDetector(plateau_window=10)
        assert d.detect_plateau([1.0, 2.0, 3.0]) == False  # noqa: E712 (numpy bool)

    def test_perfect_plateau(self):
        d = MetastabilityDetector(plateau_window=5)
        trajectory = [85.0] * 10
        assert d.detect_plateau(trajectory) == True  # noqa: E712 (numpy bool)

    def test_highly_varying_no_plateau(self):
        d = MetastabilityDetector(plateau_window=5, plateau_threshold=0.01)
        trajectory = [100.0, 50.0, 100.0, 50.0, 100.0, 50.0, 100.0]
        assert d.detect_plateau(trajectory) == False  # noqa: E712 (numpy bool)

    def test_small_variation_is_plateau(self):
        d = MetastabilityDetector(plateau_window=5, plateau_threshold=0.02)
        # CV = std/|mean|; values near 85 with tiny variation
        trajectory = [85.0, 85.1, 84.9, 85.05, 84.95]
        assert d.detect_plateau(trajectory) == True  # noqa: E712 (numpy bool)

    def test_custom_window(self):
        d = MetastabilityDetector(plateau_window=100)
        # Use custom window=3 override, only last 3 matter
        trajectory = [100.0, 50.0, 85.0, 85.0, 85.0]
        assert d.detect_plateau(trajectory, window=3) == True  # noqa: E712 (numpy bool)

    def test_mean_near_zero(self):
        """When mean is near zero, CV set to 0.0 → plateau detected."""
        d = MetastabilityDetector(plateau_window=5, plateau_threshold=0.01)
        trajectory = [0.0, 0.0, 0.0, 0.0, 0.0]
        assert d.detect_plateau(trajectory) == True  # noqa: E712 (numpy bool)

    def test_descending_no_plateau(self):
        d = MetastabilityDetector(plateau_window=5, plateau_threshold=0.001)
        trajectory = [100.0, 90.0, 80.0, 70.0, 60.0]
        assert d.detect_plateau(trajectory) == False  # noqa: E712 (numpy bool)

    def test_only_uses_last_window(self):
        d = MetastabilityDetector(plateau_window=3, plateau_threshold=0.01)
        # First part varies wildly, last 3 are plateau
        trajectory = [1000.0, 1.0, 500.0, 85.0, 85.0, 85.0]
        assert d.detect_plateau(trajectory) == True  # noqa: E712 (numpy bool)


# -- estimate_barrier_height --------------------------------------------------


class TestEstimateBarrierHeight:
    def test_infeasible_state(self):
        d = MetastabilityDetector()
        state = SolverState(
            iteration=100, objective_value=50.0, constraint_violations=5
        )
        barrier = d.estimate_barrier_height(state)
        # barrier = (1.0 + 5*0.1) * (1.0 + log10(50)) = 1.5 * (1 + 1.699) = ~4.05
        assert barrier > 0
        assert barrier < 10

    def test_feasible_state(self):
        d = MetastabilityDetector()
        state = SolverState(
            iteration=100, objective_value=50.0, constraint_violations=0
        )
        barrier = d.estimate_barrier_height(state)
        # barrier = 5.0 * (1.0 + log10(50)) = 5.0 * 2.699 = ~13.49
        assert barrier > 10

    def test_small_objective_no_scale(self):
        d = MetastabilityDetector()
        state = SolverState(iteration=100, objective_value=0.0, constraint_violations=0)
        barrier = d.estimate_barrier_height(state)
        # objective_value=0.0 → condition (>1e-10) is False → no scaling
        assert barrier == 5.0

    def test_more_violations_lower_barrier(self):
        d = MetastabilityDetector()
        state_few = SolverState(
            iteration=100, objective_value=100.0, constraint_violations=1
        )
        state_many = SolverState(
            iteration=100, objective_value=100.0, constraint_violations=10
        )
        # More violations → lower base barrier (1 + violations * 0.1)
        # state_few: (1 + 0.1) * (1 + log10(100)) = 1.1 * 3 = 3.3
        # state_many: (1 + 1.0) * (1 + log10(100)) = 2.0 * 3 = 6.0
        barrier_few = d.estimate_barrier_height(state_few)
        barrier_many = d.estimate_barrier_height(state_many)
        # Both are lower than feasible (5.0 base) with same objective
        # but state_many has higher base from more violations
        assert barrier_few < barrier_many

    def test_positive_result(self):
        d = MetastabilityDetector()
        state = SolverState(iteration=0, objective_value=1.0, constraint_violations=0)
        barrier = d.estimate_barrier_height(state)
        assert barrier > 0


# -- compute_escape_probability -----------------------------------------------


class TestComputeEscapeProbability:
    def test_zero_barrier(self):
        d = MetastabilityDetector(temperature=1.0)
        prob = d.compute_escape_probability(0.0)
        assert prob == pytest.approx(1.0)

    def test_high_barrier_low_temp(self):
        d = MetastabilityDetector(temperature=1.0)
        prob = d.compute_escape_probability(10.0)
        assert prob < 0.01

    def test_high_barrier_high_temp(self):
        d = MetastabilityDetector(temperature=10.0)
        prob = d.compute_escape_probability(10.0)
        # exp(-10/10) = exp(-1) ≈ 0.368
        assert prob == pytest.approx(math.exp(-1.0), rel=1e-3)

    def test_zero_temperature(self):
        d = MetastabilityDetector(temperature=0.0)
        prob = d.compute_escape_probability(5.0)
        assert prob == 0.0

    def test_custom_temperature_param(self):
        d = MetastabilityDetector(temperature=1.0)
        # Override with explicit parameter
        prob = d.compute_escape_probability(5.0, temperature=5.0)
        assert prob == pytest.approx(math.exp(-1.0), rel=1e-3)

    def test_clamped_to_unit_interval(self):
        d = MetastabilityDetector(temperature=100.0)
        # Very low barrier, very high temp → exp ≈ 1
        prob = d.compute_escape_probability(0.001, temperature=1000.0)
        assert 0.0 <= prob <= 1.0

    def test_very_high_barrier_returns_zero(self):
        d = MetastabilityDetector(temperature=0.001)
        prob = d.compute_escape_probability(1000.0)
        assert prob == 0.0

    def test_negative_temperature_treated_as_zero(self):
        d = MetastabilityDetector()
        prob = d.compute_escape_probability(5.0, temperature=-1.0)
        assert prob == 0.0


# -- recommend_escape_strategy ------------------------------------------------


class TestRecommendEscapeStrategy:
    def _make_state(self, barrier, escape_prob, violations=0, basin_size=5):
        return MetastableState(
            objective_value=85.0,
            constraint_violations=violations,
            barrier_height=barrier,
            basin_size=basin_size,
            escape_probability=escape_prob,
            plateau_duration=100,
            best_objective=80.0,
        )

    def test_infeasible_low_barrier(self):
        d = MetastabilityDetector()
        state = self._make_state(barrier=3.0, escape_prob=0.1, violations=2)
        assert d.recommend_escape_strategy(state) == EscapeStrategy.INCREASE_TEMPERATURE

    def test_infeasible_medium_barrier(self):
        d = MetastabilityDetector()
        state = self._make_state(barrier=7.0, escape_prob=0.05, violations=2)
        assert d.recommend_escape_strategy(state) == EscapeStrategy.BASIN_HOPPING

    def test_infeasible_high_barrier(self):
        d = MetastabilityDetector()
        state = self._make_state(barrier=15.0, escape_prob=0.001, violations=1)
        assert d.recommend_escape_strategy(state) == EscapeStrategy.RESTART_NEW_SEED

    def test_feasible_high_escape_prob(self):
        d = MetastabilityDetector()
        state = self._make_state(barrier=2.0, escape_prob=0.3, violations=0)
        assert d.recommend_escape_strategy(state) == EscapeStrategy.CONTINUE_SEARCH

    def test_feasible_low_barrier(self):
        d = MetastabilityDetector()
        state = self._make_state(barrier=3.0, escape_prob=0.1, violations=0)
        assert d.recommend_escape_strategy(state) == EscapeStrategy.INCREASE_TEMPERATURE

    def test_feasible_medium_barrier(self):
        d = MetastabilityDetector()
        state = self._make_state(barrier=10.0, escape_prob=0.01, violations=0)
        assert d.recommend_escape_strategy(state) == EscapeStrategy.BASIN_HOPPING

    def test_feasible_high_barrier(self):
        d = MetastabilityDetector()
        state = self._make_state(barrier=20.0, escape_prob=0.001, violations=0)
        assert d.recommend_escape_strategy(state) == EscapeStrategy.RESTART_NEW_SEED

    def test_feasible_extreme_barrier(self):
        d = MetastabilityDetector()
        state = self._make_state(barrier=30.0, escape_prob=0.0, violations=0)
        assert d.recommend_escape_strategy(state) == EscapeStrategy.ACCEPT_LOCAL_OPTIMUM


# -- analyze_solver_trajectory ------------------------------------------------


class TestAnalyzeSolverTrajectory:
    def test_insufficient_data(self):
        d = MetastabilityDetector(plateau_window=10)
        trajectory = [
            SolverState(iteration=i, objective_value=float(100 - i)) for i in range(5)
        ]
        analysis = d.analyze_solver_trajectory(trajectory)
        assert analysis.is_metastable == False  # noqa: E712 (numpy bool)
        assert analysis.recommended_strategy == EscapeStrategy.CONTINUE_SEARCH
        assert analysis.trajectory_length == 5

    def test_improving_trajectory_not_metastable(self):
        d = MetastabilityDetector(
            plateau_window=5, plateau_threshold=0.01, min_stagnation=3
        )
        trajectory = [
            SolverState(iteration=i, objective_value=float(100 - i * 2))
            for i in range(10)
        ]
        analysis = d.analyze_solver_trajectory(trajectory)
        assert analysis.is_metastable == False  # noqa: E712 (numpy bool)

    def test_plateau_detected_with_stagnation(self):
        d = MetastabilityDetector(
            plateau_window=5, plateau_threshold=0.02, min_stagnation=3
        )
        # First improving, then plateau at 80
        trajectory = []
        for i in range(5):
            trajectory.append(
                SolverState(iteration=i, objective_value=float(100 - i * 4))
            )
        # Best is at index 4 → objective 84
        for i in range(5, 15):
            trajectory.append(SolverState(iteration=i, objective_value=84.0))
        analysis = d.analyze_solver_trajectory(trajectory)
        assert analysis.plateau_detected == True  # noqa: E712 (numpy bool)
        assert analysis.stagnation_duration >= 3

    def test_metastable_requires_feasible(self):
        """is_metastable requires constraint_violations == 0."""
        d = MetastabilityDetector(
            plateau_window=5, plateau_threshold=0.02, min_stagnation=3
        )
        trajectory = []
        for i in range(5):
            trajectory.append(
                SolverState(iteration=i, objective_value=float(100 - i * 4))
            )
        for i in range(5, 15):
            trajectory.append(
                SolverState(iteration=i, objective_value=84.0, constraint_violations=1)
            )
        analysis = d.analyze_solver_trajectory(trajectory)
        # Plateau detected but not metastable (infeasible)
        assert analysis.plateau_detected == True  # noqa: E712 (numpy bool)
        assert analysis.is_metastable == False  # noqa: E712 (numpy bool)

    def test_metastable_feasible_plateau_with_stagnation(self):
        d = MetastabilityDetector(
            plateau_window=5, plateau_threshold=0.02, min_stagnation=3
        )
        # Best at iteration 2 (obj=92), then long plateau at 92
        trajectory = [
            SolverState(iteration=0, objective_value=100.0),
            SolverState(iteration=1, objective_value=96.0),
            SolverState(iteration=2, objective_value=92.0),
        ]
        for i in range(3, 15):
            trajectory.append(SolverState(iteration=i, objective_value=92.0))
        analysis = d.analyze_solver_trajectory(trajectory)
        assert analysis.plateau_detected == True  # noqa: E712 (numpy bool)
        assert analysis.is_metastable == True  # noqa: E712 (numpy bool)
        assert analysis.metastable_state is not None
        assert analysis.recommended_strategy != EscapeStrategy.CONTINUE_SEARCH

    def test_best_iteration_tracked(self):
        d = MetastabilityDetector(plateau_window=5, min_stagnation=3)
        trajectory = [
            SolverState(iteration=0, objective_value=100.0),
            SolverState(iteration=1, objective_value=80.0),  # best
            SolverState(iteration=2, objective_value=90.0),
            SolverState(iteration=3, objective_value=95.0),
            SolverState(iteration=4, objective_value=95.0),
        ]
        analysis = d.analyze_solver_trajectory(trajectory)
        assert analysis.best_iteration == 1

    def test_barrier_and_escape_computed(self):
        d = MetastabilityDetector(
            plateau_window=5, plateau_threshold=0.02, min_stagnation=3
        )
        trajectory = [SolverState(iteration=i, objective_value=85.0) for i in range(10)]
        analysis = d.analyze_solver_trajectory(trajectory)
        assert analysis.barrier_height > 0
        assert 0.0 <= analysis.escape_probability <= 1.0


# -- estimate_basin_size ------------------------------------------------------


class TestEstimateBasinSize:
    def test_empty_trajectory(self):
        d = MetastabilityDetector()
        state = SolverState(iteration=0, objective_value=85.0)
        assert d.estimate_basin_size([], state) == 0

    def test_all_same_value(self):
        d = MetastabilityDetector()
        trajectory = [SolverState(iteration=i, objective_value=85.0) for i in range(10)]
        state = SolverState(iteration=10, objective_value=85.0)
        assert d.estimate_basin_size(trajectory, state) == 10

    def test_none_within_tolerance(self):
        d = MetastabilityDetector()
        trajectory = [
            SolverState(iteration=i, objective_value=float(i * 100)) for i in range(10)
        ]
        state = SolverState(iteration=10, objective_value=5000.0)
        # tolerance = 5000 * 0.01 = 50, none are within 50 of 5000
        size = d.estimate_basin_size(trajectory, state, tolerance_percent=1.0)
        assert size == 0

    def test_custom_tolerance(self):
        d = MetastabilityDetector()
        trajectory = [
            SolverState(iteration=0, objective_value=100.0),
            SolverState(iteration=1, objective_value=105.0),
            SolverState(iteration=2, objective_value=110.0),
            SolverState(iteration=3, objective_value=200.0),
        ]
        state = SolverState(iteration=4, objective_value=100.0)
        # tolerance_percent=10 → tolerance = 100 * 10/100 = 10
        size = d.estimate_basin_size(trajectory, state, tolerance_percent=10.0)
        assert size == 3  # 100.0, 105.0, and 110.0 (|110-100|=10 ≤ 10)

    def test_window_limits_search(self):
        d = MetastabilityDetector()
        # 20 states all at 85.0, but window=5
        trajectory = [SolverState(iteration=i, objective_value=85.0) for i in range(20)]
        state = SolverState(iteration=20, objective_value=85.0)
        size = d.estimate_basin_size(trajectory, state, window=5)
        assert size == 5

    def test_zero_objective(self):
        d = MetastabilityDetector()
        trajectory = [SolverState(iteration=i, objective_value=0.0) for i in range(5)]
        state = SolverState(iteration=5, objective_value=0.0)
        # tolerance = 0 * 0.01 = 0, all are exactly 0
        size = d.estimate_basin_size(trajectory, state)
        assert size == 5
