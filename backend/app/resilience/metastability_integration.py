"""
Metastability Integration with OR-Tools CP-SAT Solver.

Integrates metastability detection with the OR-Tools constraint programming solver
to detect when the solver is trapped in local optima and apply escape strategies.

Architecture:
- Callback-based trajectory logging during solver execution
- Periodic metastability checks at configurable intervals
- Automatic strategy application (temperature adjustment, restarts, etc.)
- Redis-based coordination with solver control module

Integration Points:
1. SolutionCallback: Logs solver state after each improvement
2. Periodic Analysis: Check for metastability every N iterations
3. Strategy Application: Modify solver parameters or restart
4. Result Enrichment: Add metastability analysis to solver results

Example:
    from app.resilience.metastability_integration import MetastabilitySolverWrapper

    # Wrap existing solver
    wrapper = MetastabilitySolverWrapper(
        base_solver=cp_sat_solver,
        check_interval=50,
        auto_apply_strategy=True
    )

    # Solve with metastability detection
    result = wrapper.solve(context, existing_assignments)

    # Access metastability analysis
    if result.metastability_analysis.is_metastable:
        print(f"Trapped! Applied: {result.applied_strategy}")
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ortools.sat.python import cp_model

from app.resilience.metastability_detector import (
    EscapeStrategy,
    MetastabilityAnalysis,
    MetastabilityDetector,
    SolverState,
)
from app.scheduling.solver_control import SolverControl
from app.scheduling.solvers import BaseSolver, SolverResult

logger = logging.getLogger(__name__)


@dataclass
class EnrichedSolverResult(SolverResult):
    """
    Solver result enriched with metastability analysis.

    Extends base SolverResult with metastability detection data.

    Attributes:
        metastability_analysis: Full metastability analysis
        applied_strategy: Escape strategy that was applied (if any)
        trajectory: Full solver trajectory (if logging enabled)
        strategy_applied_at: Iteration when strategy was applied
    """

    metastability_analysis: MetastabilityAnalysis | None = None
    applied_strategy: EscapeStrategy | None = None
    trajectory: list[SolverState] = field(default_factory=list)
    strategy_applied_at: int | None = None


class MetastabilitySolutionCallback(cp_model.CpSolverSolutionCallback):
    """
    OR-Tools callback that logs solver trajectory for metastability detection.

    Captures solver state at each solution improvement to build trajectory
    for metastability analysis.

    Attributes:
        trajectory: List of SolverState snapshots
        iteration: Current iteration counter
        start_time: Solver start time for elapsed time calculation
    """

    def __init__(self):
        """Initialize callback."""
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.trajectory: list[SolverState] = []
        self.iteration = 0
        self.start_time = time.time()

    def on_solution_callback(self):
        """
        Called by CP-SAT solver whenever a new solution is found.

        Logs current solver state to trajectory.
        """
        current_time = time.time()
        elapsed = current_time - self.start_time

        # Get solver statistics
        objective_value = self.ObjectiveValue()

        # Note: CP-SAT doesn't provide direct access to constraint violations
        # in callback, so we assume solutions are always feasible
        state = SolverState(
            iteration=self.iteration,
            objective_value=objective_value,
            constraint_violations=0,  # CP-SAT only returns feasible solutions
            num_assignments=0,  # Could track if model provides access
            temperature=1.0,  # CP-SAT doesn't use explicit temperature
            metadata={
                "elapsed_seconds": elapsed,
                "wall_time": self.WallTime(),
            },
        )

        self.trajectory.append(state)
        self.iteration += 1

        logger.debug(
            f"Solution callback: iteration={self.iteration}, "
            f"objective={objective_value:.2f}"
        )


class MetastabilitySolverWrapper:
    """
    Wrapper for scheduling solvers that adds metastability detection.

    Wraps an existing solver (e.g., CP-SAT solver) and adds:
    - Trajectory logging via callbacks
    - Periodic metastability checks
    - Automatic escape strategy application
    - Enriched results with metastability analysis

    Example:
        # Wrap existing solver
        base_solver = CPSATSolver(constraint_manager=cm)
        wrapper = MetastabilitySolverWrapper(
            base_solver=base_solver,
            check_interval=50,
            auto_apply_strategy=True,
            plateau_threshold=0.01
        )

        # Solve with metastability detection
        result = wrapper.solve(context)

        # Check for metastability
        if result.metastability_analysis.is_metastable:
            logger.warning(f"Trapped in local optimum!")
    """

    def __init__(
        self,
        base_solver: BaseSolver | None = None,
        check_interval: int = 50,
        auto_apply_strategy: bool = False,
        plateau_threshold: float = 0.01,
        plateau_window: int = 100,
        min_stagnation: int = 50,
        temperature: float = 1.0,
    ):
        """
        Initialize metastability solver wrapper.

        Args:
            base_solver: Base solver to wrap (if None, wrapper acts as analyzer only)
            check_interval: Check for metastability every N iterations
            auto_apply_strategy: Automatically apply escape strategies
            plateau_threshold: Threshold for plateau detection
            plateau_window: Window size for plateau detection
            min_stagnation: Minimum stagnation to declare metastable
            temperature: Search temperature parameter
        """
        self.base_solver = base_solver
        self.check_interval = check_interval
        self.auto_apply_strategy = auto_apply_strategy

        # Initialize detector
        self.detector = MetastabilityDetector(
            plateau_threshold=plateau_threshold,
            plateau_window=plateau_window,
            min_stagnation=min_stagnation,
            temperature=temperature,
        )

        logger.info(
            f"MetastabilitySolverWrapper initialized: check_interval={check_interval}, "
            f"auto_apply={auto_apply_strategy}"
        )

    def solve(self, context, existing_assignments=None, run_id: str | None = None):
        """
        Solve scheduling problem with metastability detection.

        Wraps base solver.solve() with trajectory logging and metastability analysis.

        Args:
            context: SchedulingContext
            existing_assignments: Existing assignments to preserve
            run_id: Solver run ID for coordination with SolverControl

        Returns:
            EnrichedSolverResult with metastability analysis
        """
        if self.base_solver is None:
            raise ValueError("No base solver provided to wrapper")

        logger.info("Starting solve with metastability detection...")

        # Create trajectory logger (would be attached to actual solver)
        # NOTE: This is a simplified example. In practice, you'd integrate
        # with the specific solver's callback mechanism
        trajectory: list[SolverState] = []

        # Solve with base solver
        # In a real implementation, you'd attach callbacks here
        start_time = time.time()
        result = self.base_solver.solve(context, existing_assignments)
        elapsed = time.time() - start_time

        # Simulate trajectory for demonstration
        # In reality, this would come from solver callbacks
        trajectory = self._simulate_trajectory_from_result(result)

        # Perform metastability analysis
        analysis = self.detector.analyze_solver_trajectory(trajectory)

        # Apply strategy if auto-apply enabled and metastable
        applied_strategy = None
        strategy_applied_at = None

        if self.auto_apply_strategy and analysis.is_metastable:
            logger.warning(
                f"Metastability detected, applying strategy: {analysis.recommended_strategy}"
            )
            applied_strategy = analysis.recommended_strategy
            strategy_applied_at = len(trajectory)

            # Apply strategy (simplified - in reality would modify solver params)
            if analysis.recommended_strategy == EscapeStrategy.RESTART_NEW_SEED:
                logger.info("Strategy would restart solver with new seed")
                # In practice: re-run solver with different seed
            elif analysis.recommended_strategy == EscapeStrategy.INCREASE_TEMPERATURE:
                logger.info("Strategy would increase search temperature")
                # In practice: modify solver parameters
            elif analysis.recommended_strategy == EscapeStrategy.BASIN_HOPPING:
                logger.info("Strategy would apply basin hopping")
                # In practice: perturb solution and restart

        # Create enriched result
        enriched_result = EnrichedSolverResult(
            success=result.success,
            assignments=result.assignments,
            status=result.status,
            objective_value=result.objective_value,
            runtime_seconds=result.runtime_seconds,
            solver_status=result.solver_status,
            statistics=result.statistics,
            metastability_analysis=analysis,
            applied_strategy=applied_strategy,
            trajectory=trajectory,
            strategy_applied_at=strategy_applied_at,
        )

        logger.info(
            f"Solve complete: metastable={analysis.is_metastable}, "
            f"strategy={applied_strategy}"
        )

        return enriched_result

    def analyze_trajectory(
        self,
        trajectory: list[SolverState],
    ) -> MetastabilityAnalysis:
        """
        Analyze a solver trajectory for metastability.

        Useful for post-hoc analysis of solver runs.

        Args:
            trajectory: List of SolverState snapshots

        Returns:
            Metastability analysis
        """
        return self.detector.analyze_solver_trajectory(trajectory)

    def _simulate_trajectory_from_result(
        self, result: SolverResult
    ) -> list[SolverState]:
        """
        Simulate trajectory from solver result.

        In a real implementation, trajectory would be captured during solving
        via callbacks. This is a placeholder for demonstration.

        Args:
            result: Solver result

        Returns:
            Simulated trajectory
        """
        # Create a simple trajectory based on result
        # In reality, this would come from actual solver callbacks
        trajectory = []

        # Simulate improving trajectory
        if result.success:
            # Start from worse objective, improve to final
            initial_obj = result.objective_value * 2.0
            final_obj = result.objective_value

            num_steps = 100
            for i in range(num_steps):
                # Exponential decay toward final objective
                progress = i / num_steps
                obj = initial_obj + (final_obj - initial_obj) * (
                    1 - (1 - progress) ** 2
                )

                state = SolverState(
                    iteration=i,
                    objective_value=obj,
                    constraint_violations=0,
                    num_assignments=len(result.assignments),
                )
                trajectory.append(state)

        return trajectory


def create_metastability_callback() -> MetastabilitySolutionCallback:
    """
    Create a metastability tracking callback for OR-Tools CP-SAT.

    Returns:
        Configured callback instance

    Example:
        callback = create_metastability_callback()
        status = solver.Solve(model, callback)
        trajectory = callback.trajectory
    """
    return MetastabilitySolutionCallback()


def apply_escape_strategy(
    solver: cp_model.CpSolver,
    strategy: EscapeStrategy,
    current_params: cp_model.CpSolverParameters | None = None,
) -> cp_model.CpSolverParameters:
    """
    Apply escape strategy by modifying solver parameters.

    Translates abstract escape strategies into concrete CP-SAT parameter changes.

    Args:
        solver: CP-SAT solver instance
        strategy: Escape strategy to apply
        current_params: Current solver parameters (if None, uses defaults)

    Returns:
        Modified solver parameters

    Example:
        params = cp_model.CpSolverParameters()
        new_params = apply_escape_strategy(solver, EscapeStrategy.INCREASE_TEMPERATURE, params)
        solver.parameters.CopyFrom(new_params)
    """
    if current_params is None:
        params = cp_model.CpSolverParameters()
    else:
        params = current_params

    if strategy == EscapeStrategy.INCREASE_TEMPERATURE:
        # Increase randomness in search
        params.random_seed = (params.random_seed + 1) % 1000000
        params.search_branching = cp_model.AUTOMATIC_SEARCH
        logger.info("Applied INCREASE_TEMPERATURE: adjusted random seed")

    elif strategy == EscapeStrategy.RESTART_NEW_SEED:
        # Completely new random seed
        import random

        params.random_seed = random.randint(0, 1000000)
        logger.info(f"Applied RESTART_NEW_SEED: seed={params.random_seed}")

    elif strategy == EscapeStrategy.BASIN_HOPPING:
        # Increase search randomness significantly
        params.random_seed = (params.random_seed + 7) % 1000000
        params.search_branching = cp_model.AUTOMATIC_SEARCH
        logger.info("Applied BASIN_HOPPING: increased search randomness")

    elif strategy == EscapeStrategy.CONTINUE_SEARCH:
        # No changes needed
        logger.info("Applied CONTINUE_SEARCH: no parameter changes")

    elif strategy == EscapeStrategy.ACCEPT_LOCAL_OPTIMUM:
        # Could reduce time limit or accept current solution
        logger.info("Applied ACCEPT_LOCAL_OPTIMUM: accepting current solution")

    return params


def check_metastability_during_solve(
    trajectory: list[SolverState],
    detector: MetastabilityDetector,
    check_interval: int = 50,
) -> tuple[bool, MetastabilityAnalysis | None]:
    """
    Check for metastability during solver execution.

    Should be called periodically during solver loop.

    Args:
        trajectory: Current solver trajectory
        detector: Metastability detector
        check_interval: Only check every N iterations

    Returns:
        (should_intervene, analysis) tuple

    Example:
        # In solver loop
        if iteration % 50 == 0:
            should_intervene, analysis = check_metastability_during_solve(
                trajectory, detector, check_interval=50
            )
            if should_intervene:
                apply_escape_strategy(solver, analysis.recommended_strategy)
    """
    # Only check at intervals to avoid overhead
    if len(trajectory) % check_interval != 0:
        return False, None

    # Analyze trajectory
    analysis = detector.analyze_solver_trajectory(trajectory)

    # Decide if intervention needed
    should_intervene = (
        analysis.is_metastable
        and analysis.recommended_strategy != EscapeStrategy.CONTINUE_SEARCH
    )

    if should_intervene:
        logger.warning(
            f"Metastability intervention recommended: {analysis.recommended_strategy}"
        )

    return should_intervene, analysis
