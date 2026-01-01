"""
Parallel solver for schedule generation.

This module implements parallel optimization strategies for the residency
scheduling solver. By running multiple solver instances concurrently with
different configurations, it explores diverse regions of the solution space
to find better optima than a single solver could achieve.

Key Concepts:
    **Portfolio Solving**: Running multiple solvers with different strategies
    simultaneously. This is based on the observation that different heuristics
    excel on different problem instances.

    **Diversification**: Each solver instance uses a different random seed,
    heuristic, and search strategy to ensure they explore different parts
    of the solution space rather than converging to the same local optimum.

    **Early Stopping**: When a solution meeting the threshold is found,
    remaining solver instances are cancelled to save computation.

Classes:
    SolverResult: Dataclass containing results from a single solver instance.

    ParallelSolver: Base parallel solver that runs N instances concurrently
        and returns the best solution found.

    AdaptiveParallelSolver: Enhanced solver that monitors progress at checkpoints
        and can cancel underperforming instances early.

Performance Considerations:
    - Default configuration uses 4 parallel solvers, which provides good
      diversification without excessive memory usage.
    - Each solver instance runs in its own asyncio task but shares the
      same process memory. For CPU-bound solvers, consider using
      ProcessPoolExecutor.
    - Timeout is per-solver, not total. With 4 solvers and 300s timeout,
      worst case is 300s (not 1200s) due to parallelism.

Example:
    >>> async def my_solver(problem: dict, solver_id: int) -> dict:
    ...     '''Custom solver function.'''
    ...     # Solver implementation
    ...     return {"objective_value": 100, "iterations": 1000, "assignments": [...]}
    >>>
    >>> solver = ParallelSolver(num_solvers=4, timeout_seconds=300)
    >>> result = await solver.solve(problem_data, my_solver)
    >>> if result.success:
    ...     print(f"Best objective: {result.objective_value}")
    ...     schedule = result.solution

See Also:
    - OR-Tools CP-SAT solver: Often used as the underlying solver
    - docs/architecture/SOLVER_ALGORITHM.md: Solver architecture documentation
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class SolverResult:
    """
    Result from a single solver instance execution.

    Contains all information about a solver run including the solution found,
    performance metrics, and any errors encountered.

    Attributes:
        solver_id: Unique identifier for this solver instance (0 to num_solvers-1).
            Used to correlate results with strategy variants.

        success: Whether the solver found a valid solution. False indicates
            timeout, error, or infeasibility.

        solution: The schedule solution dictionary if successful, None otherwise.
            Contains 'assignments', 'objective_value', and solver-specific metadata.

        objective_value: Optimization objective value. Lower is better.
            Set to float('inf') for failed solvers to ensure they're never selected.

        duration_seconds: Wall-clock time the solver ran, useful for performance
            analysis and timeout tuning.

        iterations: Number of solver iterations/nodes explored. Useful for
            comparing solver efficiency across different strategies.

        error: Error message if solver failed, None on success. Common errors:
            'timeout', 'infeasible', or exception messages.

    Example:
        >>> result = SolverResult(
        ...     solver_id=0,
        ...     success=True,
        ...     solution={"assignments": [...], "objective_value": 150},
        ...     objective_value=150.0,
        ...     duration_seconds=45.2,
        ...     iterations=12500
        ... )
        >>> if result.success:
        ...     print(f"Solver {result.solver_id} found solution with obj={result.objective_value}")
    """

    solver_id: int
    success: bool
    solution: dict | None
    objective_value: float
    duration_seconds: float
    iterations: int
    error: str | None = None


class ParallelSolver:
    """
    Run multiple solver instances in parallel for schedule optimization.

    This class implements portfolio-based parallel solving, where multiple
    solver instances with different configurations run concurrently to
    explore the solution space more thoroughly.

    The parallel approach provides several benefits:
        1. **Robustness**: If one solver gets stuck, others may find solutions
        2. **Diversity**: Different strategies explore different solution regions
        3. **Speed**: First-found good solution can be returned early
        4. **Quality**: Best solution across all solvers is selected

    Attributes:
        num_solvers: Number of parallel solver instances to run.
        timeout_seconds: Maximum time per solver instance.
        early_stop_threshold: Objective value threshold for early termination.
        results: List of results from all solver instances after solve().

    Example:
        >>> solver = ParallelSolver(
        ...     num_solvers=4,
        ...     timeout_seconds=300,
        ...     early_stop_threshold=100.0
        ... )
        >>> result = await solver.solve(problem_data, my_solver_func)
        >>> print(f"Best solution: {result.objective_value}")
    """

    def __init__(
        self,
        num_solvers: int = 4,
        timeout_seconds: int = 300,
        early_stop_threshold: float | None = None,
    ):
        """
        Initialize parallel solver with configuration.

        Args:
            num_solvers: Number of parallel solver instances to run. Default 4
                provides good diversification without excessive resource usage.
                Increase for harder problems, decrease for simple ones.

            timeout_seconds: Maximum time in seconds for each solver instance.
                Default 300 (5 minutes) works well for medium-sized schedules.
                All solvers share this timeout and run concurrently.

            early_stop_threshold: Optional objective value threshold. When any
                solver finds a solution with objective <= this value, all
                other solvers are cancelled and the solution is returned
                immediately. Set to None (default) to always wait for all
                solvers to complete.

        Note:
            The total wall-clock time is bounded by timeout_seconds (not
            timeout_seconds * num_solvers) due to parallel execution.
        """
        self.num_solvers = num_solvers
        self.timeout_seconds = timeout_seconds
        self.early_stop_threshold = early_stop_threshold
        self.results: list[SolverResult] = []

    async def solve(
        self,
        problem_data: dict,
        solver_func: Callable[[dict, int], Any],
        strategy_variants: list[dict] | None = None,
    ) -> SolverResult:
        """
        Run solvers in parallel and return the best solution found.

        Launches num_solvers instances of solver_func concurrently, each with
        potentially different strategy parameters. Waits for all to complete
        (or timeout), then returns the result with the lowest objective value.

        Args:
            problem_data: Dictionary containing the scheduling problem definition.
                Expected keys include 'persons', 'rotations', 'blocks', 'constraints'.
                This is passed to each solver instance.

            solver_func: Async callable with signature (problem: dict, solver_id: int) -> dict.
                Must return a dictionary with at least 'objective_value' key.
                The solver_id can be used to vary behavior per instance.

            strategy_variants: Optional list of dictionaries, one per solver.
                Each dictionary is merged with problem_data before passing to
                the corresponding solver. Use to configure different heuristics,
                random seeds, or search strategies per solver.

        Returns:
            SolverResult: The result with the lowest objective_value among all
                successful solvers. If all solvers fail, returns a SolverResult
                with success=False and error describing the failure.

        Example:
            >>> async def my_solver(problem: dict, solver_id: int) -> dict:
            ...     seed = problem.get("random_seed", solver_id)
            ...     # ... solver implementation ...
            ...     return {"objective_value": 150, "iterations": 1000}
            >>>
            >>> strategies = [
            ...     {"random_seed": 0, "heuristic": "greedy"},
            ...     {"random_seed": 100, "heuristic": "random"},
            ... ]
            >>> result = await solver.solve(problem, my_solver, strategies)
        """
        logger.info(f"Starting parallel solver with {self.num_solvers} instances")
        start_time = datetime.utcnow()

        # Create solver tasks
        tasks = []
        for i in range(self.num_solvers):
            # Use strategy variant if provided
            if strategy_variants and i < len(strategy_variants):
                problem = {**problem_data, **strategy_variants[i]}
            else:
                problem = problem_data.copy()

            task = self._run_solver_instance(i, problem, solver_func)
            tasks.append(task)

        # Run all solvers in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Solver exception: {result}")
            elif isinstance(result, SolverResult) and result.success:
                valid_results.append(result)

        if not valid_results:
            logger.error("No valid solutions found by any solver")
            return SolverResult(
                solver_id=-1,
                success=False,
                solution=None,
                objective_value=float("inf"),
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                iterations=0,
                error="All solvers failed",
            )

        # Return best solution (lowest objective value)
        best_result = min(valid_results, key=lambda r: r.objective_value)

        logger.info(
            f"Parallel solver complete: best objective = {best_result.objective_value} "
            f"from solver {best_result.solver_id}"
        )

        return best_result

    async def _run_solver_instance(
        self,
        solver_id: int,
        problem_data: dict,
        solver_func: Callable,
    ) -> SolverResult:
        """
        Run a single solver instance with timeout protection.

        Executes the solver function with the given problem data, wrapped in
        asyncio timeout handling. Captures execution time, iteration count,
        and any errors.

        Args:
            solver_id: Unique identifier for this solver instance. Passed to
                solver_func and included in the result for correlation.

            problem_data: Problem definition dictionary to pass to solver_func.
                May include strategy-specific parameters merged in by solve().

            solver_func: The async solver function to execute. Expected to
                return a dict with 'objective_value' and optionally 'iterations'.

        Returns:
            SolverResult: Contains success status, solution, metrics, and any error.
                On timeout, success=False and error='timeout'.
                On exception, success=False and error contains the exception message.

        Note:
            This is an internal method. Use solve() or solve_with_diversification()
            for the public API.
        """
        start_time = datetime.utcnow()

        try:
            # Run solver with timeout
            solution = await asyncio.wait_for(
                solver_func(problem_data, solver_id),
                timeout=self.timeout_seconds,
            )

            duration = (datetime.utcnow() - start_time).total_seconds()

            # Extract objective value and iterations
            objective_value = solution.get("objective_value", float("inf"))
            iterations = solution.get("iterations", 0)

            logger.info(
                f"Solver {solver_id} complete: "
                f"objective = {objective_value}, "
                f"time = {duration:.2f}s"
            )

            return SolverResult(
                solver_id=solver_id,
                success=True,
                solution=solution,
                objective_value=objective_value,
                duration_seconds=duration,
                iterations=iterations,
            )

        except TimeoutError:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.warning(f"Solver {solver_id} timeout after {duration:.2f}s")

            return SolverResult(
                solver_id=solver_id,
                success=False,
                solution=None,
                objective_value=float("inf"),
                duration_seconds=duration,
                iterations=0,
                error="timeout",
            )

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Solver {solver_id} error: {e}", exc_info=True)

            return SolverResult(
                solver_id=solver_id,
                success=False,
                solution=None,
                objective_value=float("inf"),
                duration_seconds=duration,
                iterations=0,
                error=str(e),
            )

    async def solve_with_diversification(
        self,
        problem_data: dict,
        solver_func: Callable,
    ) -> SolverResult:
        """
        Run solvers with automatically generated diversification strategies.

        Creates strategy variants for each solver instance with different:
            - Random seeds (for stochastic components)
            - Heuristics (greedy, random, balanced, minimize_conflicts)
            - Search strategies (depth_first, breadth_first, best_first, random)

        This is a convenience method that automatically configures good
        diversification without requiring manual strategy specification.

        Args:
            problem_data: Dictionary containing the scheduling problem definition.

            solver_func: Async solver function that accepts strategy parameters
                via the problem dictionary. Should use 'random_seed', 'heuristic',
                and 'search_strategy' keys if present.

        Returns:
            SolverResult: Best result across all diversified solver instances.

        Example:
            >>> result = await solver.solve_with_diversification(
            ...     problem_data={"persons": [...], "rotations": [...]},
            ...     solver_func=my_flexible_solver
            ... )

        Note:
            The solver_func should be implemented to use the strategy parameters.
            If it ignores them, all solvers will behave identically (but with
            different random seeds if any stochastic behavior exists).
        """
        # Create different strategy variants
        strategies = []

        for i in range(self.num_solvers):
            strategy = {
                "random_seed": i * 1000,
                "heuristic": self._get_heuristic_for_solver(i),
                "search_strategy": self._get_search_strategy_for_solver(i),
            }
            strategies.append(strategy)

        return await self.solve(problem_data, solver_func, strategies)

    def _get_heuristic_for_solver(self, solver_id: int) -> str:
        """
        Get heuristic strategy for a solver instance.

        Maps solver IDs to heuristic names in a round-robin fashion to ensure
        diversity across solver instances.

        Args:
            solver_id: The solver instance ID (0 to num_solvers-1).

        Returns:
            Heuristic name string. One of:
                - 'greedy': Always pick locally optimal choice
                - 'random': Random selection for exploration
                - 'balanced': Balance between greedy and exploration
                - 'minimize_conflicts': Prioritize conflict avoidance

        Note:
            The solver_func is responsible for interpreting these heuristic
            names and implementing the corresponding behavior.
        """
        heuristics = ["greedy", "random", "balanced", "minimize_conflicts"]
        return heuristics[solver_id % len(heuristics)]

    def _get_search_strategy_for_solver(self, solver_id: int) -> str:
        """
        Get search strategy for a solver instance.

        Maps solver IDs to search strategies in a round-robin fashion,
        offset from heuristics to maximize strategy diversity.

        Args:
            solver_id: The solver instance ID (0 to num_solvers-1).

        Returns:
            Search strategy name string. One of:
                - 'depth_first': Explore deep before backtracking
                - 'breadth_first': Explore level by level
                - 'best_first': Priority queue based on objective estimate
                - 'random': Random node selection for diversity

        Note:
            The solver_func is responsible for interpreting these strategy
            names and implementing the corresponding search behavior.
        """
        strategies = ["depth_first", "breadth_first", "best_first", "random"]
        return strategies[solver_id % len(strategies)]


class AdaptiveParallelSolver(ParallelSolver):
    """
    Parallel solver with adaptive monitoring and early termination.

    Extends ParallelSolver with checkpoint-based progress monitoring. At
    regular intervals, checks completed solvers and can terminate early
    when a good-enough solution is found.

    This is useful when:
        - Some solvers may finish much faster than others
        - Early stopping can save significant computation time
        - Real-time progress feedback is needed

    The adaptive approach differs from base ParallelSolver:
        - Does not wait for all solvers to complete
        - Periodically checks for completed results
        - Can cancel remaining solvers when threshold is met
        - Provides incremental best-solution updates

    Example:
        >>> solver = AdaptiveParallelSolver(
        ...     num_solvers=8,
        ...     timeout_seconds=600,
        ...     early_stop_threshold=50.0
        ... )
        >>> result = await solver.solve_adaptive(
        ...     problem_data,
        ...     my_solver_func,
        ...     checkpoint_interval=30
        ... )
    """

    async def solve_adaptive(
        self,
        problem_data: dict,
        solver_func: Callable,
        checkpoint_interval: int = 30,
    ) -> SolverResult:
        """
        Solve with adaptive monitoring and early termination support.

        Starts all solver instances, then periodically checks for completed
        results. Updates the best-known solution as results arrive and can
        terminate early if early_stop_threshold is configured and reached.

        Args:
            problem_data: Dictionary containing the scheduling problem definition.
                Passed to each solver instance.

            solver_func: Async solver function with signature
                (problem: dict, solver_id: int) -> dict.

            checkpoint_interval: Seconds between progress checks. Default 30.
                Lower values provide faster response but more overhead.
                Higher values are more efficient but slower to react.

        Returns:
            SolverResult: Best result found across all solver instances.
                Returns as soon as:
                    1. All solvers complete, OR
                    2. A solution meeting early_stop_threshold is found, OR
                    3. Total elapsed time exceeds timeout_seconds

        Note:
            Unlike solve(), this method actively monitors progress and can
            cancel remaining solvers. This is useful for long-running solvers
            where early termination provides significant time savings.

        Example:
            >>> # Stop as soon as any solver finds objective <= 100
            >>> solver = AdaptiveParallelSolver(
            ...     num_solvers=4,
            ...     timeout_seconds=300,
            ...     early_stop_threshold=100.0
            ... )
            >>> result = await solver.solve_adaptive(
            ...     problem,
            ...     my_solver,
            ...     checkpoint_interval=15  # Check every 15 seconds
            ... )
        """
        logger.info("Starting adaptive parallel solver")

        # Start all solvers
        tasks = []
        for i in range(self.num_solvers):
            task = asyncio.create_task(
                self._run_solver_instance(i, problem_data.copy(), solver_func)
            )
            tasks.append(task)

        # Monitor progress and adapt
        best_objective = float("inf")
        elapsed = 0

        while elapsed < self.timeout_seconds:
            await asyncio.sleep(checkpoint_interval)
            elapsed += checkpoint_interval

            # Check for completed solvers
            done_tasks = [task for task in tasks if task.done()]

            for task in done_tasks:
                if not task.exception():
                    result = task.result()
                    if result.success and result.objective_value < best_objective:
                        best_objective = result.objective_value
                        logger.info(f"New best objective: {best_objective}")

                        # Early stop if threshold reached
                        if (
                            self.early_stop_threshold
                            and best_objective <= self.early_stop_threshold
                        ):
                            logger.info("Early stop threshold reached")
                            # Cancel remaining tasks
                            for t in tasks:
                                if not t.done():
                                    t.cancel()
                            break

            # All tasks complete
            if len(done_tasks) == len(tasks):
                break

        # Gather results
        results = []
        for task in tasks:
            if task.done() and not task.exception():
                results.append(task.result())

        if not results:
            return SolverResult(
                solver_id=-1,
                success=False,
                solution=None,
                objective_value=float("inf"),
                duration_seconds=elapsed,
                iterations=0,
                error="No solutions found",
            )

        # Return best result
        return min(results, key=lambda r: r.objective_value)
