"""
Tests for Metastability Detection and Escape System.

Tests the metastability detector that identifies when optimization solvers
are trapped in local optima and recommends escape strategies.
"""

from datetime import datetime, timedelta

import numpy as np
import pytest

from app.resilience.metastability_detector import (
    EscapeStrategy,
    MetastabilityAnalysis,
    MetastabilityDetector,
    MetastableState,
    SolverState,
)
from app.resilience.metastability_integration import (
    MetastabilitySolutionCallback,
    MetastabilitySolverWrapper,
    apply_escape_strategy,
    check_metastability_during_solve,
)


class TestEscapeStrategy:
    """Test EscapeStrategy enum."""

    def test_all_strategies_defined(self):
        """Test that all expected escape strategies exist."""
        expected_strategies = {
            "continue_search",
            "increase_temperature",
            "basin_hopping",
            "restart_new_seed",
            "accept_local_optimum",
        }

        actual_strategies = {strategy.value for strategy in EscapeStrategy}
        assert actual_strategies == expected_strategies

    def test_strategy_values(self):
        """Test specific enum values."""
        assert EscapeStrategy.CONTINUE_SEARCH == "continue_search"
        assert EscapeStrategy.INCREASE_TEMPERATURE == "increase_temperature"
        assert EscapeStrategy.BASIN_HOPPING == "basin_hopping"
        assert EscapeStrategy.RESTART_NEW_SEED == "restart_new_seed"
        assert EscapeStrategy.ACCEPT_LOCAL_OPTIMUM == "accept_local_optimum"


class TestSolverState:
    """Test SolverState dataclass."""

    def test_solver_state_minimal(self):
        """Test creating solver state with minimal fields."""
        state = SolverState(
            iteration=10,
            objective_value=42.5,
        )

        assert state.iteration == 10
        assert state.objective_value == 42.5
        assert state.constraint_violations == 0
        assert state.num_assignments == 0
        assert state.temperature == 1.0
        assert state.random_seed is None
        assert state.metadata == {}

    def test_solver_state_full(self):
        """Test creating solver state with all fields."""
        metadata = {"solver": "CP-SAT", "wall_time": 1.5}

        state = SolverState(
            iteration=100,
            objective_value=25.3,
            constraint_violations=2,
            num_assignments=50,
            temperature=2.5,
            random_seed=42,
            metadata=metadata,
        )

        assert state.iteration == 100
        assert state.objective_value == 25.3
        assert state.constraint_violations == 2
        assert state.num_assignments == 50
        assert state.temperature == 2.5
        assert state.random_seed == 42
        assert state.metadata == metadata


class TestMetastableState:
    """Test MetastableState dataclass."""

    def test_metastable_state_creation(self):
        """Test creating metastable state."""
        state = MetastableState(
            objective_value=100.0,
            constraint_violations=0,
            barrier_height=10.5,
            basin_size=25,
            escape_probability=0.15,
            plateau_duration=75,
            best_objective=95.0,
            temperature=1.5,
            iteration=200,
        )

        assert state.objective_value == 100.0
        assert state.constraint_violations == 0
        assert state.barrier_height == 10.5
        assert state.basin_size == 25
        assert state.escape_probability == 0.15
        assert state.plateau_duration == 75
        assert state.best_objective == 95.0
        assert state.temperature == 1.5
        assert state.iteration == 200
        assert isinstance(state.timestamp, datetime)


class TestMetastabilityDetector:
    """Test MetastabilityDetector class."""

    def test_initialization_default(self):
        """Test initialization with default parameters."""
        detector = MetastabilityDetector()

        assert detector.plateau_threshold == 0.01
        assert detector.plateau_window == 100
        assert detector.min_stagnation == 50
        assert detector.temperature == 1.0

    def test_initialization_custom(self):
        """Test initialization with custom parameters."""
        detector = MetastabilityDetector(
            plateau_threshold=0.02,
            plateau_window=50,
            min_stagnation=25,
            temperature=2.0,
        )

        assert detector.plateau_threshold == 0.02
        assert detector.plateau_window == 50
        assert detector.min_stagnation == 25
        assert detector.temperature == 2.0

    def test_detect_plateau_clear_plateau(self):
        """Test plateau detection with obvious plateau."""
        detector = MetastabilityDetector(plateau_threshold=0.01, plateau_window=10)

        # Improving trajectory followed by plateau
        trajectory = [100, 95, 90, 85, 80, 80, 80, 80, 80, 80, 80, 80]

        is_plateau = detector.detect_plateau(trajectory, window=5)
        assert is_plateau  # Last 5 values are constant

    def test_detect_plateau_improving(self):
        """Test no plateau when still improving."""
        detector = MetastabilityDetector(plateau_threshold=0.01, plateau_window=10)

        # Continuously improving
        trajectory = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55]

        is_plateau = detector.detect_plateau(trajectory, window=5)
        assert not is_plateau  # Still improving significantly

    def test_detect_plateau_noisy_plateau(self):
        """Test plateau detection with noise around stable value."""
        detector = MetastabilityDetector(plateau_threshold=0.01, plateau_window=10)

        # Small fluctuations around 85 (< 1% variation)
        trajectory = [100, 95, 90, 85, 85.1, 84.9, 85.2, 84.8, 85.0, 85.1]

        is_plateau = detector.detect_plateau(trajectory, window=5)
        assert is_plateau  # Variation < 1%

    def test_detect_plateau_insufficient_data(self):
        """Test plateau detection with insufficient data."""
        detector = MetastabilityDetector(plateau_window=100)

        trajectory = [100, 95, 90]  # Only 3 points

        is_plateau = detector.detect_plateau(trajectory)
        assert not is_plateau  # Not enough data

    def test_estimate_barrier_height_infeasible(self):
        """Test barrier estimation for infeasible solutions."""
        detector = MetastabilityDetector()

        state = SolverState(
            iteration=10,
            objective_value=100.0,
            constraint_violations=5,  # Infeasible
        )

        barrier = detector.estimate_barrier_height(state)

        # Infeasible solutions should have lower barrier
        assert barrier > 0
        assert barrier < 10  # Should be relatively low

    def test_estimate_barrier_height_feasible(self):
        """Test barrier estimation for feasible solutions."""
        detector = MetastabilityDetector()

        state = SolverState(
            iteration=10,
            objective_value=100.0,
            constraint_violations=0,  # Feasible
        )

        barrier = detector.estimate_barrier_height(state)

        # Feasible solutions should have moderate barrier
        assert barrier > 0

    def test_compute_escape_probability_low_barrier(self):
        """Test escape probability with low barrier."""
        detector = MetastabilityDetector(temperature=1.0)

        # Low barrier = high escape probability
        prob = detector.compute_escape_probability(barrier_height=1.0, temperature=1.0)

        assert 0.0 <= prob <= 1.0
        assert prob > 0.3  # exp(-1) ≈ 0.368

    def test_compute_escape_probability_high_barrier(self):
        """Test escape probability with high barrier."""
        detector = MetastabilityDetector(temperature=1.0)

        # High barrier = low escape probability
        prob = detector.compute_escape_probability(barrier_height=20.0, temperature=1.0)

        assert 0.0 <= prob <= 1.0
        assert prob < 0.001  # exp(-20) is very small

    def test_compute_escape_probability_high_temperature(self):
        """Test that higher temperature increases escape probability."""
        detector = MetastabilityDetector()

        barrier = 10.0

        prob_low_temp = detector.compute_escape_probability(barrier, temperature=1.0)
        prob_high_temp = detector.compute_escape_probability(barrier, temperature=5.0)

        assert prob_high_temp > prob_low_temp

    def test_recommend_strategy_continue_search(self):
        """Test strategy recommendation: continue search."""
        detector = MetastabilityDetector()

        # High escape probability, low barrier
        state = MetastableState(
            objective_value=100.0,
            constraint_violations=0,
            barrier_height=2.0,
            basin_size=10,
            escape_probability=0.5,  # High
            plateau_duration=50,
            best_objective=95.0,
        )

        strategy = detector.recommend_escape_strategy(state)
        assert strategy == EscapeStrategy.CONTINUE_SEARCH

    def test_recommend_strategy_increase_temperature(self):
        """Test strategy recommendation: increase temperature."""
        detector = MetastabilityDetector()

        # Medium barrier, feasible
        state = MetastableState(
            objective_value=100.0,
            constraint_violations=0,
            barrier_height=4.0,
            basin_size=20,
            escape_probability=0.1,
            plateau_duration=75,
            best_objective=95.0,
        )

        strategy = detector.recommend_escape_strategy(state)
        assert strategy == EscapeStrategy.INCREASE_TEMPERATURE

    def test_recommend_strategy_basin_hopping(self):
        """Test strategy recommendation: basin hopping."""
        detector = MetastabilityDetector()

        # Medium-high barrier
        state = MetastableState(
            objective_value=100.0,
            constraint_violations=0,
            barrier_height=12.0,
            basin_size=15,
            escape_probability=0.05,
            plateau_duration=100,
            best_objective=95.0,
        )

        strategy = detector.recommend_escape_strategy(state)
        assert strategy == EscapeStrategy.BASIN_HOPPING

    def test_recommend_strategy_restart(self):
        """Test strategy recommendation: restart with new seed."""
        detector = MetastabilityDetector()

        # High barrier
        state = MetastableState(
            objective_value=100.0,
            constraint_violations=0,
            barrier_height=20.0,
            basin_size=30,
            escape_probability=0.01,
            plateau_duration=150,
            best_objective=95.0,
        )

        strategy = detector.recommend_escape_strategy(state)
        assert strategy == EscapeStrategy.RESTART_NEW_SEED

    def test_recommend_strategy_accept_optimum(self):
        """Test strategy recommendation: accept local optimum."""
        detector = MetastabilityDetector()

        # Very high barrier, feasible
        state = MetastableState(
            objective_value=100.0,
            constraint_violations=0,
            barrier_height=30.0,
            basin_size=50,
            escape_probability=0.0001,
            plateau_duration=200,
            best_objective=98.0,
        )

        strategy = detector.recommend_escape_strategy(state)
        assert strategy == EscapeStrategy.ACCEPT_LOCAL_OPTIMUM

    def test_recommend_strategy_infeasible_never_accept(self):
        """Test that infeasible solutions are never accepted."""
        detector = MetastabilityDetector()

        # Very high barrier but infeasible
        state = MetastableState(
            objective_value=100.0,
            constraint_violations=3,  # Infeasible
            barrier_height=30.0,
            basin_size=50,
            escape_probability=0.0001,
            plateau_duration=200,
            best_objective=95.0,
        )

        strategy = detector.recommend_escape_strategy(state)
        # Should restart, not accept
        assert strategy in [
            EscapeStrategy.RESTART_NEW_SEED,
            EscapeStrategy.BASIN_HOPPING,
            EscapeStrategy.INCREASE_TEMPERATURE,
        ]

    def test_analyze_trajectory_insufficient_data(self):
        """Test trajectory analysis with insufficient data."""
        detector = MetastabilityDetector(plateau_window=100)

        trajectory = [
            SolverState(iteration=i, objective_value=100 - i) for i in range(10)
        ]

        analysis = detector.analyze_solver_trajectory(trajectory)

        assert not analysis.is_metastable
        assert analysis.metastable_state is None
        assert analysis.recommended_strategy == EscapeStrategy.CONTINUE_SEARCH
        assert analysis.trajectory_length == 10

    def test_analyze_trajectory_improving(self):
        """Test trajectory analysis with improving trajectory."""
        detector = MetastabilityDetector(
            plateau_window=50, plateau_threshold=0.05, min_stagnation=20
        )

        # Continuously improving trajectory
        trajectory = [
            SolverState(iteration=i, objective_value=100 - i * 0.5)
            for i in range(100)
        ]

        analysis = detector.analyze_solver_trajectory(trajectory)

        assert not analysis.is_metastable
        assert not analysis.plateau_detected  # Still improving
        assert analysis.trajectory_length == 100
        assert analysis.best_iteration == 99  # Best at end

    def test_analyze_trajectory_metastable(self):
        """Test trajectory analysis detecting metastability."""
        detector = MetastabilityDetector(
            plateau_window=20, plateau_threshold=0.01, min_stagnation=30
        )

        # Improve then plateau
        improving = [100 - i for i in range(50)]
        plateau = [50.0] * 60  # Constant for 60 iterations
        trajectory = [
            SolverState(iteration=i, objective_value=val, constraint_violations=0)
            for i, val in enumerate(improving + plateau)
        ]

        analysis = detector.analyze_solver_trajectory(trajectory)

        assert analysis.plateau_detected
        assert analysis.is_metastable  # Feasible + plateau + stagnation
        assert analysis.metastable_state is not None
        assert analysis.best_iteration == 49  # Best at end of improvement
        assert analysis.stagnation_duration >= 30

    def test_analyze_trajectory_infeasible_plateau_not_metastable(self):
        """Test that infeasible plateaus are not considered metastable."""
        detector = MetastabilityDetector(
            plateau_window=20, plateau_threshold=0.01, min_stagnation=30
        )

        # Plateau but infeasible
        trajectory = [
            SolverState(
                iteration=i, objective_value=50.0, constraint_violations=5  # Infeasible
            )
            for i in range(100)
        ]

        analysis = detector.analyze_solver_trajectory(trajectory)

        # Plateau detected, but not metastable due to infeasibility
        assert analysis.plateau_detected
        assert not analysis.is_metastable  # Must be feasible for metastability

    def test_estimate_basin_size(self):
        """Test basin size estimation."""
        detector = MetastabilityDetector()

        # Create trajectory with clustering around 100
        trajectory = []
        for i in range(100):
            if i < 50:
                # Early diversity
                obj = 150 - i
            else:
                # Cluster around 100 (within 1%)
                obj = 100 + (i % 2) * 0.5 - 0.25
            trajectory.append(SolverState(iteration=i, objective_value=obj))

        current_state = SolverState(iteration=100, objective_value=100.0)

        basin_size = detector.estimate_basin_size(
            trajectory, current_state, tolerance_percent=1.0, window=50
        )

        # Should find most recent 50 iterations clustered around 100
        assert basin_size > 40  # Most of the window

    def test_estimate_basin_size_small_basin(self):
        """Test basin size estimation with small basin."""
        detector = MetastabilityDetector()

        # Diverse trajectory, no clustering
        trajectory = [
            SolverState(iteration=i, objective_value=100 - i * 0.5) for i in range(100)
        ]

        current_state = SolverState(iteration=100, objective_value=50.0)

        basin_size = detector.estimate_basin_size(
            trajectory, current_state, tolerance_percent=1.0, window=50
        )

        # No clustering - small basin
        assert basin_size < 5


class TestMetastabilitySolutionCallback:
    """Test OR-Tools solution callback for metastability tracking."""

    def test_callback_initialization(self):
        """Test callback initializes correctly."""
        callback = MetastabilitySolutionCallback()

        assert callback.trajectory == []
        assert callback.iteration == 0
        assert isinstance(callback.start_time, float)


class TestMetastabilitySolverWrapper:
    """Test solver wrapper with metastability detection."""

    def test_wrapper_initialization(self):
        """Test wrapper initialization."""
        wrapper = MetastabilitySolverWrapper(
            check_interval=50,
            auto_apply_strategy=True,
            plateau_threshold=0.02,
        )

        assert wrapper.check_interval == 50
        assert wrapper.auto_apply_strategy is True
        assert wrapper.detector.plateau_threshold == 0.02

    def test_analyze_trajectory(self):
        """Test trajectory analysis through wrapper."""
        wrapper = MetastabilitySolverWrapper()

        trajectory = [
            SolverState(iteration=i, objective_value=100 - i) for i in range(100)
        ]

        analysis = wrapper.analyze_trajectory(trajectory)

        assert isinstance(analysis, MetastabilityAnalysis)
        assert analysis.trajectory_length == 100


class TestIntegrationFunctions:
    """Test integration utility functions."""

    def test_check_metastability_not_at_interval(self):
        """Test metastability check skips when not at interval."""
        detector = MetastabilityDetector()
        trajectory = [
            SolverState(iteration=i, objective_value=100 - i) for i in range(10)
        ]

        should_intervene, analysis = check_metastability_during_solve(
            trajectory, detector, check_interval=50
        )

        assert not should_intervene  # Not at interval
        assert analysis is None

    def test_check_metastability_at_interval_not_metastable(self):
        """Test metastability check at interval, not metastable."""
        detector = MetastabilityDetector(plateau_window=20, min_stagnation=10)

        # Improving trajectory
        trajectory = [
            SolverState(iteration=i, objective_value=100 - i) for i in range(50)
        ]

        should_intervene, analysis = check_metastability_during_solve(
            trajectory, detector, check_interval=50
        )

        assert not should_intervene  # Not metastable
        assert analysis is not None
        assert not analysis.is_metastable

    def test_check_metastability_at_interval_metastable(self):
        """Test metastability check at interval, metastable detected."""
        detector = MetastabilityDetector(
            plateau_window=20, plateau_threshold=0.01, min_stagnation=30
        )

        # Plateau trajectory
        improving = [100 - i for i in range(20)]
        plateau = [80.0] * 80
        trajectory = [
            SolverState(iteration=i, objective_value=val, constraint_violations=0)
            for i, val in enumerate(improving + plateau)
        ]

        should_intervene, analysis = check_metastability_during_solve(
            trajectory, detector, check_interval=100
        )

        assert should_intervene  # Metastable
        assert analysis is not None
        assert analysis.is_metastable


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_plateau_detection_empty_trajectory(self):
        """Test plateau detection with empty trajectory."""
        detector = MetastabilityDetector()

        is_plateau = detector.detect_plateau([])
        assert not is_plateau

    def test_plateau_detection_single_value(self):
        """Test plateau detection with single repeated value."""
        detector = MetastabilityDetector(plateau_window=10)

        trajectory = [42.0] * 20

        is_plateau = detector.detect_plateau(trajectory)
        assert is_plateau  # All identical

    def test_escape_probability_zero_temperature(self):
        """Test escape probability with zero temperature."""
        detector = MetastabilityDetector()

        prob = detector.compute_escape_probability(barrier_height=5.0, temperature=0.0)
        assert prob == 0.0  # Zero temperature = no escape

    def test_escape_probability_extreme_barrier(self):
        """Test escape probability with extreme barrier height."""
        detector = MetastabilityDetector()

        # Very high barrier should give near-zero probability
        prob = detector.compute_escape_probability(
            barrier_height=1000.0, temperature=1.0
        )
        assert 0.0 <= prob <= 1.0
        assert prob < 1e-10

    def test_analyze_empty_trajectory(self):
        """Test analysis of empty trajectory."""
        detector = MetastabilityDetector()

        analysis = detector.analyze_solver_trajectory([])

        assert not analysis.is_metastable
        assert analysis.trajectory_length == 0
        assert analysis.recommended_strategy == EscapeStrategy.CONTINUE_SEARCH
