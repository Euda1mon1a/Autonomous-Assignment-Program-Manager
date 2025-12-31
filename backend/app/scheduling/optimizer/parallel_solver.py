"""Parallel solver for schedule generation.

Runs multiple solver instances in parallel to explore different solution spaces.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class SolverResult:
    """Result from a solver instance."""

    solver_id: int
    success: bool
    solution: dict | None
    objective_value: float
    duration_seconds: float
    iterations: int
    error: str | None = None


class ParallelSolver:
    """Run multiple solver instances in parallel."""

    def __init__(
        self,
        num_solvers: int = 4,
        timeout_seconds: int = 300,
        early_stop_threshold: float | None = None,
    ):
        """Initialize parallel solver.

        Args:
            num_solvers: Number of parallel solver instances
            timeout_seconds: Timeout for each solver
            early_stop_threshold: Stop when this objective value reached
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
        """Run solvers in parallel and return best solution.

        Args:
            problem_data: Problem definition
            solver_func: Async solver function (problem, solver_id) -> solution
            strategy_variants: Optional list of strategy parameters for each solver

        Returns:
            Best solver result
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
        """Run a single solver instance.

        Args:
            solver_id: Solver instance ID
            problem_data: Problem definition
            solver_func: Solver function

        Returns:
            SolverResult
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
        """Run solvers with different diversification strategies.

        Args:
            problem_data: Problem definition
            solver_func: Solver function

        Returns:
            Best solver result
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
        """Get heuristic strategy for solver.

        Args:
            solver_id: Solver ID

        Returns:
            Heuristic name
        """
        heuristics = ["greedy", "random", "balanced", "minimize_conflicts"]
        return heuristics[solver_id % len(heuristics)]

    def _get_search_strategy_for_solver(self, solver_id: int) -> str:
        """Get search strategy for solver.

        Args:
            solver_id: Solver ID

        Returns:
            Search strategy name
        """
        strategies = ["depth_first", "breadth_first", "best_first", "random"]
        return strategies[solver_id % len(strategies)]


class AdaptiveParallelSolver(ParallelSolver):
    """Parallel solver that adapts based on progress."""

    async def solve_adaptive(
        self,
        problem_data: dict,
        solver_func: Callable,
        checkpoint_interval: int = 30,
    ) -> SolverResult:
        """Solve with adaptive strategy based on progress.

        Args:
            problem_data: Problem definition
            solver_func: Solver function
            checkpoint_interval: Seconds between progress checks

        Returns:
            Best solver result
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
