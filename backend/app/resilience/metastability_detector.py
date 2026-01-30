"""
Metastability Detection for Schedule Optimization.

Detects when solvers are trapped in local optima (metastable states)
and recommends escape strategies.

Physics basis: Metastable states are long-lived non-equilibrium configurations
separated from true equilibrium by energy barriers. In materials science and
chemistry, systems can get "stuck" in these states even though lower-energy
configurations exist.

Application to Scheduling:
- "Energy" = Objective function value (lower is better)
- "Metastable state" = Local optimum the solver cannot escape
- "Energy barrier" = Difficulty of transitioning to better solutions
- "Temperature" = Search randomness/exploration parameter
- "Escape probability" = Likelihood of finding better solution

Key Concepts:
1. **Plateau Detection**: Objective value stagnates despite continued search
2. **Barrier Height Estimation**: How hard it is to escape current state
3. **Basin Size**: How many similar solutions cluster around current state
4. **Escape Probability**: Boltzmann factor exp(-ΔE/kT) from statistical mechanics
5. **Escape Strategies**: Restart, increase temperature, basin hopping, etc.

Example:
    detector = MetastabilityDetector(plateau_threshold=0.01, plateau_window=100)

    # During solver run:
    trajectory = [100, 95, 90, 87, 85, 85.1, 84.9, 85, 85.2, ...]

    if detector.detect_plateau(trajectory):
        strategy = detector.recommend_escape_strategy(metastable_state)
        # Apply strategy: restart with new seed, increase temperature, etc.
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

import numpy as np

logger = logging.getLogger(__name__)


class EscapeStrategy(str, Enum):
    """
    Recommended strategies for escaping metastable states.

    Ordered by increasing computational cost and disruption.
    """

    CONTINUE_SEARCH = "continue_search"  # Not metastable, keep going
    INCREASE_TEMPERATURE = "increase_temperature"  # More randomness
    BASIN_HOPPING = "basin_hopping"  # Jump to random state, local search
    RESTART_NEW_SEED = "restart_new_seed"  # Complete restart with new seed
    ACCEPT_LOCAL_OPTIMUM = "accept_local_optimum"  # Barrier too high, accept current


@dataclass
class MetastableState:
    """
    Represents a detected metastable state in optimization trajectory.

    Attributes:
        objective_value: Current objective function value
        constraint_violations: Number of constraint violations (0 = feasible)
        barrier_height: Estimated energy barrier to escape (relative units)
        basin_size: Number of similar solutions in neighborhood
        escape_probability: Probability of escaping via thermal fluctuation (0-1)
        plateau_duration: Number of iterations stuck at this value
        best_objective: Best objective seen in entire run
        temperature: Current search temperature parameter
        iteration: Current iteration number
        timestamp: When this state was detected
    """

    objective_value: float
    constraint_violations: int
    barrier_height: float
    basin_size: int
    escape_probability: float
    plateau_duration: int
    best_objective: float
    temperature: float = 1.0
    iteration: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SolverState:
    """
    Snapshot of solver state at a given iteration.

    Used to track solver trajectory over time.

    Attributes:
        iteration: Iteration number
        objective_value: Current objective value
        constraint_violations: Number of violated constraints
        num_assignments: Number of assignments in current solution
        temperature: Search temperature (if applicable)
        random_seed: Random seed for this iteration (if applicable)
        metadata: Additional solver-specific data
    """

    iteration: int
    objective_value: float
    constraint_violations: int = 0
    num_assignments: int = 0
    temperature: float = 1.0
    random_seed: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetastabilityAnalysis:
    """
    Complete analysis of solver trajectory for metastability.

    Attributes:
        is_metastable: Whether solver is trapped in metastable state
        metastable_state: Detected metastable state (if any)
        recommended_strategy: Suggested escape strategy
        plateau_detected: Whether objective plateau was detected
        barrier_height: Estimated escape barrier height
        escape_probability: Probability of natural escape
        analysis_timestamp: When analysis was performed
        trajectory_length: Number of iterations analyzed
        best_iteration: Iteration where best solution was found
        stagnation_duration: How long solver has been stuck
    """

    is_metastable: bool
    metastable_state: MetastableState | None
    recommended_strategy: EscapeStrategy
    plateau_detected: bool
    barrier_height: float
    escape_probability: float
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    trajectory_length: int = 0
    best_iteration: int = 0
    stagnation_duration: int = 0


class MetastabilityDetector:
    """
    Detects and analyzes metastable states in optimization trajectories.

    Uses signal processing and statistical mechanics principles to identify
    when a solver is trapped in local optima and recommend escape strategies.

    Features:
    - Plateau detection via moving statistics
    - Energy barrier estimation via perturbation sampling
    - Escape probability via Boltzmann distribution
    - Strategy recommendation based on barrier height and basin size

    Example:
        detector = MetastabilityDetector(plateau_threshold=0.01, plateau_window=100)

        # Track solver progress
        trajectory = []
        for iteration, state in enumerate(solver.iterate()):
            solver_state = SolverState(
                iteration=iteration,
                objective_value=state.objective,
                constraint_violations=state.violations
            )
            trajectory.append(solver_state)

            # Check for metastability every 50 iterations
            if iteration % 50 == 0:
                analysis = detector.analyze_solver_trajectory(trajectory)
                if analysis.is_metastable:
                    logger.warning(f"Metastability detected: {analysis.recommended_strategy}")
                    # Apply escape strategy
    """

    def __init__(
        self,
        plateau_threshold: float = 0.01,
        plateau_window: int = 100,
        min_stagnation: int = 50,
        temperature: float = 1.0,
    ) -> None:
        """
        Initialize metastability detector.

        Args:
            plateau_threshold: Max relative change to consider plateaued (e.g., 0.01 = 1%)
            plateau_window: Number of recent iterations to check for plateau
            min_stagnation: Minimum iterations of stagnation before declaring metastable
            temperature: Search temperature for escape probability calculation
        """
        self.plateau_threshold = plateau_threshold
        self.plateau_window = plateau_window
        self.min_stagnation = min_stagnation
        self.temperature = temperature

        logger.info(
            f"MetastabilityDetector initialized: threshold={plateau_threshold:.3f}, "
            f"window={plateau_window}, min_stagnation={min_stagnation}"
        )

    def detect_plateau(
        self,
        solver_trajectory: list[float],
        window: int | None = None,
    ) -> bool:
        """
        Detect if objective function has plateaued (stagnated).

        Uses coefficient of variation (CV = std/mean) over recent window.
        If CV < threshold, objective is considered plateaued.

        Args:
            solver_trajectory: List of objective values over time
            window: Window size (defaults to self.plateau_window)

        Returns:
            True if plateau detected, False otherwise

        Example:
            trajectory = [100, 95, 90, 87, 85, 85.1, 84.9, 85, 85.2, 85.1]
            is_stuck = detector.detect_plateau(trajectory, window=5)
            # True - last 5 values vary < 1% around 85
        """
        if window is None:
            window = self.plateau_window

        if len(solver_trajectory) < window:
            # Not enough data
            return False

            # Get recent window
        recent = solver_trajectory[-window:]

        # Check if all values are identical (perfect plateau)
        if len(set(recent)) == 1:
            logger.debug("Perfect plateau detected (all values identical)")
            return True

            # Calculate coefficient of variation
        mean_val = np.mean(recent)
        std_val = np.std(recent)

        # Avoid division by zero
        if abs(mean_val) < 1e-10:
            cv = 0.0
        else:
            cv = std_val / abs(mean_val)

        is_plateaued = cv < self.plateau_threshold

        logger.debug(
            f"Plateau check: CV={cv:.6f}, threshold={self.plateau_threshold:.6f}, "
            f"plateaued={is_plateaued}"
        )

        return is_plateaued

    def estimate_barrier_height(
        self,
        current_state: SolverState,
        perturbation_samples: int = 50,
    ) -> float:
        """
        Estimate energy barrier height via perturbation analysis.

        Simulates random perturbations around current state and measures
        how much the objective worsens. High barrier = perturbations hurt objective.

        Args:
            current_state: Current solver state
            perturbation_samples: Number of random perturbations to try

        Returns:
            Estimated barrier height (relative units)

        Notes:
            In a real implementation integrated with the solver, this would:
            1. Generate nearby solutions (swap assignments, etc.)
            2. Evaluate their objective values
            3. Measure average degradation

            For now, we estimate based on constraint violations and objective value.
            Higher violations = lower barrier (easier to escape to feasible region)
        """
        # Heuristic estimation based on state properties
        # In reality, this would sample neighbor solutions

        # If infeasible, barrier is lower (many directions to explore)
        if current_state.constraint_violations > 0:
            barrier = 1.0 + (current_state.constraint_violations * 0.1)
        else:
            # Feasible solution - assume moderate barrier
            # In practice, would sample nearby solutions
            barrier = 5.0

            # Normalize by objective scale
        if current_state.objective_value > 1e-10:
            barrier = barrier * (1.0 + math.log10(abs(current_state.objective_value)))

        logger.debug(
            f"Estimated barrier height: {barrier:.2f} "
            f"(violations={current_state.constraint_violations})"
        )

        return barrier

    def compute_escape_probability(
        self,
        barrier_height: float,
        temperature: float | None = None,
    ) -> float:
        """
        Compute escape probability using Boltzmann distribution.

        Based on statistical mechanics: P(escape) = exp(-ΔE / kT)
        where ΔE = barrier height, k = Boltzmann constant, T = temperature

        Args:
            barrier_height: Energy barrier to escape
            temperature: Search temperature (higher = more exploration)

        Returns:
            Escape probability (0-1)

        Example:
            # High barrier, low temperature = low escape probability
            prob = detector.compute_escape_probability(barrier=10.0, temperature=1.0)
            # prob ≈ 0.000045 (very unlikely to escape)

            # High barrier, high temperature = higher escape probability
            prob = detector.compute_escape_probability(barrier=10.0, temperature=5.0)
            # prob ≈ 0.135 (more likely to escape)
        """
        if temperature is None:
            temperature = self.temperature

            # Avoid division by zero
        if temperature < 1e-10:
            return 0.0

            # Boltzmann factor: exp(-E/kT)
            # Using k=1 for simplicity (dimensionless units)
        try:
            probability = math.exp(-barrier_height / temperature)
        except OverflowError:
            # Barrier too high
            probability = 0.0

            # Clamp to [0, 1]
        probability = max(0.0, min(1.0, probability))

        logger.debug(
            f"Escape probability: {probability:.6f} "
            f"(barrier={barrier_height:.2f}, temp={temperature:.2f})"
        )

        return probability

    def recommend_escape_strategy(
        self,
        metastable_state: MetastableState,
    ) -> EscapeStrategy:
        """
        Recommend escape strategy based on metastable state characteristics.

        Decision logic:
        - Low barrier + high escape probability → Continue search
        - Medium barrier → Increase temperature
        - High barrier + small basin → Basin hopping
        - Very high barrier → Restart with new seed
        - Extreme barrier + feasible → Accept local optimum

        Args:
            metastable_state: Detected metastable state

        Returns:
            Recommended escape strategy
        """
        barrier = metastable_state.barrier_height
        escape_prob = metastable_state.escape_probability
        violations = metastable_state.constraint_violations
        basin_size = metastable_state.basin_size

        # If infeasible, never accept - must keep searching
        if violations > 0:
            if barrier < 5.0:
                strategy = EscapeStrategy.INCREASE_TEMPERATURE
            elif barrier < 10.0:
                strategy = EscapeStrategy.BASIN_HOPPING
            else:
                strategy = EscapeStrategy.RESTART_NEW_SEED
        else:
            # Feasible solution
            if escape_prob > 0.2:
                # High escape probability - continue current search
                strategy = EscapeStrategy.CONTINUE_SEARCH
            elif barrier < 5.0:
                # Low-medium barrier - increase randomness
                strategy = EscapeStrategy.INCREASE_TEMPERATURE
            elif barrier < 15.0:
                # Medium-high barrier - try basin hopping
                strategy = EscapeStrategy.BASIN_HOPPING
            elif barrier < 25.0:
                # High barrier - restart needed
                strategy = EscapeStrategy.RESTART_NEW_SEED
            else:
                # Extreme barrier - may be global optimum
                strategy = EscapeStrategy.ACCEPT_LOCAL_OPTIMUM

        logger.info(
            f"Recommended strategy: {strategy.value} "
            f"(barrier={barrier:.2f}, escape_prob={escape_prob:.4f}, "
            f"violations={violations})"
        )

        return strategy

    def analyze_solver_trajectory(
        self,
        trajectory: list[SolverState],
    ) -> MetastabilityAnalysis:
        """
        Perform complete metastability analysis on solver trajectory.

        Analyzes the full trajectory to detect metastable states, estimate
        barriers, and recommend escape strategies.

        Args:
            trajectory: List of SolverState snapshots over time

        Returns:
            Complete metastability analysis

        Example:
            trajectory = [
                SolverState(iteration=0, objective_value=100, ...),
                SolverState(iteration=1, objective_value=95, ...),
                ...
            ]
            analysis = detector.analyze_solver_trajectory(trajectory)

            if analysis.is_metastable:
                print(f"Trapped! Strategy: {analysis.recommended_strategy}")
        """
        if len(trajectory) < self.plateau_window:
            # Not enough data for analysis
            return MetastabilityAnalysis(
                is_metastable=False,
                metastable_state=None,
                recommended_strategy=EscapeStrategy.CONTINUE_SEARCH,
                plateau_detected=False,
                barrier_height=0.0,
                escape_probability=1.0,
                trajectory_length=len(trajectory),
                best_iteration=0,
                stagnation_duration=0,
            )

            # Extract objective values
        objectives = [state.objective_value for state in trajectory]

        # Find best solution
        best_idx = np.argmin(objectives)
        best_objective = objectives[best_idx]

        # Check for plateau
        plateau_detected = self.detect_plateau(objectives)

        # Calculate stagnation duration (iterations since best)
        stagnation = len(trajectory) - best_idx - 1

        # Get current state
        current_state = trajectory[-1]

        # Estimate barrier height
        barrier_height = self.estimate_barrier_height(current_state)

        # Compute escape probability
        escape_probability = self.compute_escape_probability(
            barrier_height, current_state.temperature
        )

        # Estimate basin size (number of solutions with similar objective)
        # Count how many recent solutions are within 1% of current
        current_obj = current_state.objective_value
        tolerance = abs(current_obj) * 0.01
        recent_window = min(50, len(trajectory))
        recent_states = trajectory[-recent_window:]
        basin_size = sum(
            1
            for state in recent_states
            if abs(state.objective_value - current_obj) <= tolerance
        )

        # Determine if metastable
        is_metastable = (
            plateau_detected
            and stagnation >= self.min_stagnation
            and current_state.constraint_violations == 0  # Only feasible states
        )

        # Create metastable state
        metastable_state = None
        if is_metastable or plateau_detected:
            metastable_state = MetastableState(
                objective_value=current_state.objective_value,
                constraint_violations=current_state.constraint_violations,
                barrier_height=barrier_height,
                basin_size=basin_size,
                escape_probability=escape_probability,
                plateau_duration=stagnation,
                best_objective=best_objective,
                temperature=current_state.temperature,
                iteration=current_state.iteration,
            )

            # Recommend strategy
        if metastable_state:
            strategy = self.recommend_escape_strategy(metastable_state)
        else:
            strategy = EscapeStrategy.CONTINUE_SEARCH

        analysis = MetastabilityAnalysis(
            is_metastable=is_metastable,
            metastable_state=metastable_state,
            recommended_strategy=strategy,
            plateau_detected=plateau_detected,
            barrier_height=barrier_height,
            escape_probability=escape_probability,
            trajectory_length=len(trajectory),
            best_iteration=best_idx,
            stagnation_duration=stagnation,
        )

        if is_metastable:
            logger.warning(
                f"Metastability detected after {len(trajectory)} iterations: "
                f"stagnation={stagnation}, barrier={barrier_height:.2f}, "
                f"strategy={strategy.value}"
            )
        else:
            logger.debug(
                f"No metastability detected: plateau={plateau_detected}, "
                f"stagnation={stagnation}/{self.min_stagnation}"
            )

        return analysis

    def estimate_basin_size(
        self,
        trajectory: list[SolverState],
        current_state: SolverState,
        tolerance_percent: float = 1.0,
        window: int = 50,
    ) -> int:
        """
        Estimate the size of the current basin of attraction.

        Counts how many recent solutions cluster around the current objective value.
        Large basin = many similar solutions (hard to escape)
        Small basin = few similar solutions (easier to escape)

        Args:
            trajectory: Full solver trajectory
            current_state: Current state
            tolerance_percent: Percentage tolerance for "similar" (default 1%)
            window: How many recent iterations to check

        Returns:
            Estimated basin size (number of similar solutions)
        """
        if not trajectory:
            return 0

        current_obj = current_state.objective_value
        tolerance = abs(current_obj) * (tolerance_percent / 100.0)

        recent_window = min(window, len(trajectory))
        recent_states = trajectory[-recent_window:]

        basin_size = sum(
            1
            for state in recent_states
            if abs(state.objective_value - current_obj) <= tolerance
        )

        logger.debug(
            f"Basin size: {basin_size}/{recent_window} solutions within "
            f"{tolerance_percent}% of current objective"
        )

        return basin_size
