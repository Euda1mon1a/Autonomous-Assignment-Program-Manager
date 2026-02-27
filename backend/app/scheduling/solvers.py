"""
Optimization Solvers for Residency Scheduling.

This module provides multiple solver implementations:
- PuLP Linear Programming: Fast, good for large problems
- OR-Tools CP-SAT: Optimal solutions with constraint propagation
- Hybrid Solver: Combines approaches for best results

Each solver uses the modular constraint system from constraints.py.

ARCHITECTURE NOTE:
These solvers are designed for OUTPATIENT HALF-DAY OPTIMIZATION only.
Block-assigned rotations (FMIT, NF, inpatient) are handled separately and
should NOT be passed to these solvers.

IMPORTANT: The engine._get_rotation_templates() must filter to rotation_type="outpatient"
before passing templates to solvers. If NF/PC/inpatient templates are included,
solvers will incorrectly assign residents to them.

KNOWN ISSUES (2025-12-24) - ALL FIXED:

1. GREEDY SOLVER - Template Selection Bug (lines ~1273-1279):
   Previously always selected the first template that passes constraints.
   STATUS: FIXED - Now selects template with fewest total assignments for
   even distribution across rotation types.

2. CP-SAT SOLVER - No Template Balance (lines ~794-816):
   Previously only penalized resident equity, not template concentration.
   STATUS: FIXED - Added template_balance_penalty to objective function.
   Penalizes max template count to encourage distribution.

3. PuLP SOLVER - No Template Balance (lines ~346-386):
   Previously only penalized resident equity, not template concentration.
   STATUS: FIXED - Added template_balance_penalty to objective function.
   Same pattern as CP-SAT: penalizes max template count.

4. TEMPLATE FILTERING - Engine Issue (engine.py:874-905):
   Previously returned ALL templates without filtering.
   STATUS: FIXED - _get_rotation_templates() now defaults to rotation_type="outpatient".
   Block-assigned rotations (NF, PC, FMIT, inpatient) excluded by default.
   NOTE: Previous fix incorrectly used "clinic" instead of "outpatient" - corrected 2025-12-26.

All four fixes applied 2025-12-24, filter corrected 2025-12-26. Solvers should now:
- Only receive outpatient templates (half-day elective/selective optimization)
- Distribute assignments evenly across available rotation types
- Balance both resident workload AND template variety
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any
from uuid import UUID

from app.models.assignment import Assignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.constraints import (
    ConstraintManager,
    SchedulingContext,
)

logger = logging.getLogger(__name__)


# Objective function weights
COVERAGE_WEIGHT = 1000  # Primary objective: maximize schedule coverage
EQUITY_PENALTY_WEIGHT = 10  # Secondary: balance workload across residents
TEMPLATE_BALANCE_WEIGHT = 5  # Tertiary: distribute assignments across rotation types

# Redis TTL for solver progress tracking
SOLVER_PROGRESS_TTL_SECONDS = 300  # 5 minutes


class SolverResult:
    """Result from a solver run."""

    def __init__(
        self,
        success: bool,
        assignments: list[
            tuple[UUID, UUID, UUID | None]
        ],  # (person_id, block_id, template_id)
        status: str,
        objective_value: float = 0.0,
        runtime_seconds: float = 0.0,
        solver_status: str = "",
        statistics: dict[Any, Any] | None = None,
        explanations: dict[Any, Any]
        | None = None,  # person_id, block_id -> DecisionExplanation
        random_seed: int | None = None,
        call_assignments: list[tuple[UUID, UUID, str]]
        | None = None,  # (person_id, block_id, call_type)
        faculty_half_day_assignments: list[tuple[UUID, UUID, str]]
        | None = None,  # (faculty_id, block_id, activity_type)
    ) -> None:
        self.success = success
        self.assignments = assignments
        self.status = status
        self.objective_value = objective_value
        self.runtime_seconds = runtime_seconds
        self.solver_status = solver_status
        self.statistics = statistics or {}
        self.explanations = (
            explanations or {}
        )  # (person_id, block_id) -> explanation dict
        self.random_seed = random_seed
        self.call_assignments = (
            call_assignments or []
        )  # (person_id, block_id, call_type)
        self.faculty_half_day_assignments = (
            faculty_half_day_assignments or []
        )  # (faculty_id, block_id, activity_type: C, AT, PCAT, DO, OFF)

    def __repr__(self) -> str:
        return f"SolverResult(success={self.success}, assignments={len(self.assignments)}, status={self.status})"


class BaseSolver(ABC):
    """
    Base class for scheduling solvers.

    All solvers use a ConstraintManager for composable constraints
    and a SchedulingContext for data access.
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.constraint_manager = (
            constraint_manager or ConstraintManager.create_default()
        )
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] | None = None,
    ) -> SolverResult:
        """
        Solve the scheduling problem.

        Args:
            context: SchedulingContext with all necessary data
            existing_assignments: Assignments to preserve (incremental scheduling)

        Returns:
            SolverResult with assignments and statistics
        """
        pass

    def _select_template(
        self,
        resident: Person,
        templates: list[RotationTemplate],
    ) -> RotationTemplate | None:
        """
        Select appropriate rotation template for a resident.

        Filters templates to find those suitable for the resident.
        Could be extended to consider PGY level, specialty, etc.

        Args:
            resident: Person object for the resident being assigned
            templates: List of available rotation templates to choose from

        Returns:
            RotationTemplate if a suitable template is found, None otherwise.
            Returns the first suitable template in the list.

        """
        return templates[0] if templates else None


class PuLPSolver(BaseSolver):
    """
    Linear Programming solver using PuLP.

    Advantages:
    - Fast for large problems
    - Supports multiple LP backends (CBC, GLPK, Gurobi, CPLEX)
    - Good for feasibility problems

    Limitations:
    - Some constraints require linearization
    - May not find optimal solution for highly constrained problems
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 60.0,
        solver_backend: str = "PULP_CBC_CMD",
    ) -> None:
        super().__init__(constraint_manager, timeout_seconds)
        self.solver_backend = solver_backend

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] | None = None,
    ) -> SolverResult:
        """Solve using PuLP linear programming."""
        try:
            import pulp
        except ImportError:
            logger.error("PuLP not installed. Run: pip install pulp>=2.7.0")
            return SolverResult(
                success=False,
                assignments=[],
                status="error",
                solver_status="PuLP not installed",
            )

        start_time = time.time()

        # Filter to workday blocks
        workday_blocks = [b for b in context.blocks if not b.is_weekend]

        if not workday_blocks or not context.residents or not context.templates:
            return SolverResult(
                success=False,
                assignments=[],
                status="empty",
                solver_status="No blocks, residents, or rotation templates",
            )

        # Create the LP problem
        prob = pulp.LpProblem("ResidencySchedule", pulp.LpMaximize)

        # ==================================================
        # DECISION VARIABLES
        # x[r_i, b_i, t_i] = 1 if resident r assigned to rotation t during block b
        # ==================================================
        x = {}
        template_idx = {t.id: i for i, t in enumerate(context.templates)}

        locked_blocks = getattr(context, "locked_blocks", set())
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            for block in workday_blocks:
                if (resident.id, block.id) in locked_blocks:
                    continue
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    t_i = template_idx[template.id]
                    x[r_i, b_i, t_i] = pulp.LpVariable(
                        f"x_{r_i}_{b_i}_{t_i}",
                        cat=pulp.LpBinary,
                    )

        # Store both 2D (for legacy constraints) and 3D variables
        # 2D view: x_2d[r_i, b_i] = sum over all rotations
        x_2d = {}
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                rotation_vars = [
                    x[r_i, b_i, t_i]
                    for t_i in range(len(context.templates))
                    if (r_i, b_i, t_i) in x
                ]
                if rotation_vars:
                    x_2d[r_i, b_i] = pulp.lpSum(rotation_vars)

        # ==================================================
        # FACULTY DECISION VARIABLES
        # f[f_i, b_i, t_i] = 1 if faculty f assigned to rotation t during block b
        # ==================================================
        f = {}
        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            for block in workday_blocks:
                if (faculty.id, block.id) in locked_blocks:
                    continue
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    t_i = template_idx[template.id]
                    f[f_i, b_i, t_i] = pulp.LpVariable(
                        f"f_{f_i}_{b_i}_{t_i}",
                        cat=pulp.LpBinary,
                    )

        # 2D view for faculty
        f_2d = {}
        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                rotation_vars = [
                    f[f_i, b_i, t_i]
                    for t_i in range(len(context.templates))
                    if (f_i, b_i, t_i) in f
                ]
                if rotation_vars:
                    f_2d[f_i, b_i] = pulp.lpSum(rotation_vars)

        # ==================================================
        # OVERNIGHT CALL DECISION VARIABLES
        # call[f_i, b_i, "overnight"] = 1 if faculty f on call for block b's date
        # Sun-Thurs nights + Fri/Sat when FMIT attending is mandatory
        # ==================================================
        call = {}
        call_eligible = getattr(context, "call_eligible_faculty", [])
        call_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {fac.id: i for i, fac in enumerate(call_eligible)},
        )

        if call_eligible:
            call_dates_processed = set()
            for block in workday_blocks:
                # Only Sun-Thurs nights (Sun=6, Mon=0, Tue=1, Wed=2, Thu=3)
                if block.date.weekday() not in (0, 1, 2, 3, 6):
                    continue
                # Only one variable per date (not per block/session)
                if block.date in call_dates_processed:
                    continue
                call_dates_processed.add(block.date)

                b_i = context.block_idx[block.id]
                for fac in call_eligible:
                    f_i = call_idx.get(fac.id)
                    if f_i is not None:
                        call[f_i, b_i, "overnight"] = pulp.LpVariable(
                            f"call_{f_i}_{b_i}",
                            cat=pulp.LpBinary,
                        )

        variables = {
            "assignments": x_2d,  # For legacy constraints (residents)
            "template_assignments": x,  # For rotation-specific constraints (residents)
            "faculty_assignments": f_2d,  # Faculty 2D view
            "faculty_template_assignments": f,  # Faculty 3D view
            "call_assignments": call,  # Overnight call assignments
        }

        # ==================================================
        # CONSTRAINT: At most one rotation per resident per block
        # ==================================================
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                rotation_vars = [
                    x[r_i, b_i, t_i]
                    for t_i in range(len(context.templates))
                    if (r_i, b_i, t_i) in x
                ]
                if rotation_vars:
                    prob += (
                        pulp.lpSum(rotation_vars) == 1,
                        f"one_rotation_res_{r_i}_{b_i}",
                    )

        # ==================================================
        # CONSTRAINT: At most one rotation per faculty per block
        # ==================================================
        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                rotation_vars = [
                    f[f_i, b_i, t_i]
                    for t_i in range(len(context.templates))
                    if (f_i, b_i, t_i) in f
                ]
                if rotation_vars:
                    prob += (
                        pulp.lpSum(rotation_vars) <= 1,
                        f"one_rotation_fac_{f_i}_{b_i}",
                    )

        # ==================================================
        # APPLY CONSTRAINTS FROM MANAGER
        # ==================================================
        self.constraint_manager.apply_to_pulp(prob, variables, context)

        # ==================================================
        # PRESERVE EXISTING ASSIGNMENTS
        # ==================================================
        if existing_assignments:
            for assignment in existing_assignments:
                if assignment.person_id in context.resident_idx:
                    r_i = context.resident_idx[assignment.person_id]
                    if assignment.block_id in context.block_idx:
                        b_i = context.block_idx[assignment.block_id]
                        if (
                            assignment.rotation_template_id
                            and assignment.rotation_template_id in template_idx
                        ):
                            t_i = template_idx[assignment.rotation_template_id]
                            if (r_i, b_i, t_i) in x:
                                prob += (
                                    x[r_i, b_i, t_i] == 1,
                                    f"preserve_{r_i}_{b_i}_{t_i}",
                                )

        # ==================================================
        # OBJECTIVE FUNCTION
        # Maximize: coverage * 1000 - equity_penalty - template_balance_penalty
        #
        # Template balance ensures assignments are distributed across rotation
        # types, not concentrated in a single rotation (e.g., all Night Float).
        # ==================================================
        coverage = pulp.lpSum(x.values())

        # Calculate template assignment counts for balance penalty
        template_counts = {}
        for t_i, template in enumerate(context.templates):
            template_vars = [
                x[r_i, b_i, t_i]
                for r_i in range(len(context.residents))
                for b_i in range(len(workday_blocks))
                if (r_i, b_i, t_i) in x
            ]
            if template_vars:
                template_counts[t_i] = pulp.lpSum(template_vars)

        # Template balance penalty: penalize max template count to encourage distribution
        # This prevents all assignments going to one rotation type
        template_balance_penalty = None
        if len(template_counts) > 1:
            max_template_count = pulp.LpVariable(
                "max_template_count",
                lowBound=0,
                cat=pulp.LpInteger,
            )
            for t_i, count_expr in template_counts.items():
                prob += (
                    max_template_count >= count_expr,
                    f"max_template_ge_{t_i}",
                )
            template_balance_penalty = max_template_count

        # Build objective with all penalties
        equity_penalty = variables.get("equity_penalty")
        objective_terms = variables.get("objective_terms", [])

        if (
            equity_penalty is not None
            or template_balance_penalty is not None
            or objective_terms
        ):
            objective_expr = COVERAGE_WEIGHT * coverage
            if equity_penalty is not None:
                objective_expr -= EQUITY_PENALTY_WEIGHT * equity_penalty
            if template_balance_penalty is not None:
                objective_expr -= TEMPLATE_BALANCE_WEIGHT * template_balance_penalty
            if objective_terms:
                objective_expr -= pulp.lpSum(
                    term_var * int(weight) for term_var, weight in objective_terms
                )
            prob += objective_expr, "objective"
        else:
            prob += coverage, "objective"

        # ==================================================
        # SOLVE
        # ==================================================
        try:
            solver = pulp.PULP_CBC_CMD(
                msg=0,
                timeLimit=self.timeout_seconds,
            )
            prob.solve(solver)
        except Exception as e:
            logger.error(f"PuLP solver error: {e}")
            return SolverResult(
                success=False,
                assignments=[],
                status="error",
                solver_status=str(e),
            )

        runtime = time.time() - start_time

        # Check solution status
        status = pulp.LpStatus[prob.status]
        if status not in ["Optimal", "Feasible"]:
            logger.warning(f"PuLP solver status: {status}")
            return SolverResult(
                success=False,
                assignments=[],
                status="infeasible",
                solver_status=status,
                runtime_seconds=runtime,
            )

        # ==================================================
        # EXTRACT SOLUTION - Residents
        # ==================================================
        assignments = []
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    t_i = template_idx[template.id]
                    if (r_i, b_i, t_i) in x and pulp.value(x[r_i, b_i, t_i]) == 1:
                        assignments.append(
                            (
                                resident.id,
                                block.id,
                                template.id,
                            )
                        )

        # ==================================================
        # EXTRACT SOLUTION - Faculty
        # ==================================================
        faculty_assignment_count = 0
        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    t_i = template_idx[template.id]
                    if (f_i, b_i, t_i) in f and pulp.value(f[f_i, b_i, t_i]) == 1:
                        assignments.append(
                            (
                                faculty.id,
                                block.id,
                                template.id,
                            )
                        )
                        faculty_assignment_count += 1

        # ==================================================
        # EXTRACT SOLUTION - Overnight Call Assignments
        # ==================================================
        call_assignments_result = []
        if call_eligible and call:
            block_id_by_idx = {context.block_idx[b.id]: b.id for b in context.blocks}
            for (f_i, b_i, call_type), var in call.items():
                if pulp.value(var) == 1:
                    # Find the faculty and block for this variable
                    faculty_id = None
                    block_id = block_id_by_idx.get(b_i)
                    for fac in call_eligible:
                        if call_idx.get(fac.id) == f_i:
                            faculty_id = fac.id
                            break
                    if faculty_id and block_id:
                        call_assignments_result.append(
                            (faculty_id, block_id, call_type)
                        )

            logger.info(
                f"PuLP found {len(call_assignments_result)} overnight call assignments"
            )

        logger.info(
            f"PuLP found {len(assignments)} assignments "
            f"({len(assignments) - faculty_assignment_count} residents, "
            f"{faculty_assignment_count} faculty) in {runtime:.2f}s"
        )

        return SolverResult(
            success=True,
            assignments=assignments,
            status="optimal" if status == "Optimal" else "feasible",
            objective_value=pulp.value(prob.objective) if prob.objective else 0,
            runtime_seconds=runtime,
            solver_status=status,
            statistics={
                "total_blocks": len(workday_blocks),
                "total_residents": len(context.residents),
                "total_faculty": len(context.faculty),
                "total_templates": len(context.templates),
                "resident_assignments": len(assignments) - faculty_assignment_count,
                "faculty_assignments": faculty_assignment_count,
                "call_assignments": len(call_assignments_result),
                "coverage_rate": (
                    len(assignments) / len(workday_blocks) if workday_blocks else 0
                ),
            },
            call_assignments=call_assignments_result,
        )


class SolverProgressCallback:
    """
    Progress callback for CP-SAT solver that stores updates in Redis.

    This callback is invoked by OR-Tools whenever a new solution is found,
    allowing us to track progress and provide real-time feedback to users.
    Optionally broadcasts to WebSocket for real-time visualization.
    """

    def __init__(
        self,
        task_id: str,
        redis_client,
        broadcast_callback: Any | None = None,
    ) -> None:
        """
        Initialize the progress callback.

        Args:
            task_id: Unique identifier for the solver task
            redis_client: Redis client for storing progress data
            broadcast_callback: Optional async callback for WebSocket broadcast
        """
        self.broadcast_callback = broadcast_callback

        try:
            from ortools.sat.python import cp_model

            outer = self

            # Create a dynamic class that inherits from CpSolverSolutionCallback
            class _ProgressCallback(cp_model.CpSolverSolutionCallback):
                def __init__(self, task_id: str, redis_client) -> None:
                    super().__init__()
                    self.task_id = task_id
                    self.redis = redis_client
                    self.solution_count = 0
                    self.start_time = time.time()

                def on_solution_callback(self) -> None:
                    """Called by OR-Tools when a new solution is found."""
                    self.solution_count += 1
                    elapsed = time.time() - self.start_time

                    # Get current objective value and best bound
                    current_obj = self.ObjectiveValue()
                    best_bound = self.BestObjectiveBound()

                    # Calculate optimality gap (0-100%)
                    # Gap = |best_bound - current_obj| / |best_bound| * 100
                    gap = 0.0
                    if best_bound != 0:
                        gap = abs(best_bound - current_obj) / abs(best_bound) * 100

                    # Estimate progress (inverse of gap, capped at 99% until optimal)
                    # Progress = 100 - gap, but cap at 99% for non-optimal solutions
                    progress_pct = min(100 - gap, 99.0)

                    progress_data = {
                        "solutions_found": self.solution_count,
                        "current_objective": current_obj,
                        "best_bound": best_bound,
                        "optimality_gap_pct": round(gap, 2),
                        "progress_pct": round(progress_pct, 2),
                        "elapsed_seconds": round(elapsed, 2),
                        "status": "solving",
                        "timestamp": time.time(),
                    }

                    try:
                        # Store in Redis with 5 minute expiry
                        self.redis.setex(
                            f"solver_progress:{self.task_id}",
                            SOLVER_PROGRESS_TTL_SECONDS,
                            json.dumps(progress_data),
                        )
                        logger.debug(
                            f"Progress update for task {self.task_id}: "
                            f"{self.solution_count} solutions, "
                            f"{progress_pct:.1f}% progress, "
                            f"gap={gap:.2f}%"
                        )
                    except Exception as e:
                        logger.error(f"Failed to store progress in Redis: {e}")

                    # Broadcast to WebSocket if callback provided
                    if outer.broadcast_callback:
                        try:
                            # Use camelCase for frontend compatibility
                            ws_data = {
                                "eventType": "solver_solution",
                                "taskId": self.task_id,
                                "solutionNum": self.solution_count,
                                "solutionType": "progress",
                                "objectiveValue": current_obj,
                                "optimalityGapPct": round(gap, 2),
                                "progressPct": round(progress_pct, 2),
                                "elapsedSeconds": round(elapsed, 2),
                                "isOptimal": gap < 0.01,
                            }
                            outer._trigger_broadcast(ws_data)
                        except Exception as e:
                            logger.error(f"Failed to broadcast solver event: {e}")

            # Store the callback instance
            self._callback = _ProgressCallback(task_id, redis_client)

        except ImportError:
            logger.warning("OR-Tools not available, progress callback disabled")
            self._callback = None

    def _trigger_broadcast(self, data: dict) -> None:
        """Trigger async broadcast from sync context."""
        import asyncio
        import inspect

        if not self.broadcast_callback:
            return

        result = self.broadcast_callback(data)
        if inspect.iscoroutine(result):
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(result)
            except RuntimeError:
                # No running event loop - skip broadcast
                logger.debug("No event loop available for solver broadcast")

    def get_callback(self) -> Any | None:
        """Get the underlying OR-Tools callback object."""
        return self._callback


class CPSATSolver(BaseSolver):
    """
    Constraint Programming solver using Google OR-Tools CP-SAT.

    Advantages:
    - Guarantees optimal solutions (within timeout)
    - Powerful constraint propagation
    - Handles complex logical constraints naturally

    Features:
    - Parallel solving (configurable workers)
    - Handles non-linear constraints
    - Built-in support for scheduling-specific constraints
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 60.0,
        num_workers: int = 0,  # 0 = auto-detect all cores
        task_id: str | None = None,
        redis_client=None,
    ) -> None:
        super().__init__(constraint_manager, timeout_seconds)
        self.num_workers = num_workers
        self.task_id = task_id
        self.redis_client = redis_client

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] | None = None,
    ) -> SolverResult:
        """
        Solve scheduling problem using Google OR-Tools CP-SAT solver.

        CP-SAT (Constraint Programming - Boolean Satisfiability) is a powerful
        constraint programming solver that combines SAT solving with constraint
        propagation to find optimal solutions.

        Algorithm Overview:
            1. Create decision variables: x[r,b,t] for each (resident, block, template)
            2. Add base constraint: at most one rotation per resident per block
            3. Apply all enabled constraints from ConstraintManager
            4. Define objective function: maximize coverage, minimize penalties
            5. Invoke CP-SAT solver with parallel search workers
            6. Extract and return solution

        Advantages of CP-SAT:
            - **Optimality**: Guarantees optimal solution (or best within timeout)
            - **Constraint Propagation**: Prunes search space intelligently
            - **Parallel Solving**: Uses multiple workers for faster solving
            - **Complex Constraints**: Handles logical constraints naturally

        Performance:
            - Small problems (<100 blocks, <10 residents): <1 second
            - Medium problems (<500 blocks, <50 residents): 1-30 seconds
            - Large problems: May timeout, falls back to best feasible solution

        Args:
            context: SchedulingContext with residents, blocks, templates, constraints
            existing_assignments: Optional assignments to preserve (incremental scheduling)

        Returns:
            SolverResult with:
                - success: True if optimal or feasible solution found
                - assignments: List of (person_id, block_id, template_id) tuples
                - status: "optimal", "feasible", or "infeasible"
                - objective_value: Final objective function value
                - runtime_seconds: Solver runtime
                - statistics: Solver statistics (branches, conflicts, etc.)

        Example:
            >>> solver = CPSATSolver(timeout_seconds=60.0, num_workers=4)
            >>> result = solver.solve(context)
            >>> if result.success:
            ...     print(f"Found {len(result.assignments)} assignments")
            ...     print(f"Objective: {result.objective_value}")

        Note:
            Requires OR-Tools package: pip install ortools>=9.8
        """
        try:
            from ortools.sat.python import cp_model
        except ImportError:
            logger.error("OR-Tools not installed. Run: pip install ortools>=9.8")
            return SolverResult(
                success=False,
                assignments=[],
                status="error",
                solver_status="OR-Tools not installed",
            )

        start_time = time.time()

        # Normalise optional param to avoid NoneType iteration / len() errors
        if existing_assignments is None:
            existing_assignments = []

        # Filter to workday blocks
        workday_blocks = [b for b in context.blocks if not b.is_weekend]

        if not workday_blocks or not context.residents or not context.templates:
            return SolverResult(
                success=False,
                assignments=[],
                status="empty",
                solver_status="No blocks, residents, or rotation templates",
            )

        # Create the CP model
        model = cp_model.CpModel()

        # ==================================================
        # DECISION VARIABLES
        # x[r_i, b_i, t_i] = 1 if resident r assigned to rotation t during block b
        # ==================================================
        x = {}
        template_idx = {t.id: i for i, t in enumerate(context.templates)}

        locked_blocks = getattr(context, "locked_blocks", set())
        availability = getattr(context, "availability", {}) or {}
        resident_template_map = getattr(context, "resident_template_map", {}) or {}
        active_template_ids = {t.id for t in context.templates}
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            raw_assigned = resident_template_map.get(resident.id, set())
            # Only restrict to assigned templates that are actually active;
            # if none match (e.g. archived template), allow all templates
            # so the resident still gets solver variables.
            assigned_template_ids = raw_assigned & active_template_ids
            for block in workday_blocks:
                if (resident.id, block.id) in locked_blocks:
                    continue
                # Also skip blocks where resident is unavailable (leave, TDY, etc.)
                # Prevents conflict between Availability constraint and OneAssignmentPerBlock
                block_avail = availability.get(resident.id, {}).get(block.id)
                if block_avail and not block_avail.get("available", True):
                    continue
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    # If resident has BlockAssignment(s), only create vars for those rotations
                    if (
                        assigned_template_ids
                        and template.id not in assigned_template_ids
                    ):
                        continue
                    t_i = template_idx[template.id]
                    x[r_i, b_i, t_i] = model.NewBoolVar(f"x_{r_i}_{b_i}_{t_i}")

        # Store both 2D (for legacy constraints) and 3D variables
        # 2D view: x_2d[r_i, b_i] = OR of all rotations
        x_2d = {}
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                rotation_vars = [
                    x[r_i, b_i, t_i]
                    for t_i in range(len(context.templates))
                    if (r_i, b_i, t_i) in x
                ]
                if rotation_vars:
                    # Create a 2D indicator: 1 if assigned to any rotation in this block
                    x_2d[r_i, b_i] = model.NewBoolVar(f"x_2d_{r_i}_{b_i}")
                    # x_2d = 1 iff at least one rotation is selected
                    model.Add(sum(rotation_vars) >= 1).OnlyEnforceIf(x_2d[r_i, b_i])
                    model.Add(sum(rotation_vars) == 0).OnlyEnforceIf(
                        x_2d[r_i, b_i].Not()
                    )

        # ==================================================
        # FACULTY DECISION VARIABLES
        # f[f_i, b_i, t_i] = 1 if faculty f assigned to rotation t during block b
        # ==================================================
        f = {}
        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            for block in workday_blocks:
                if (faculty.id, block.id) in locked_blocks:
                    continue
                # Skip blocks where faculty is unavailable (mirrors resident filtering)
                block_avail = availability.get(faculty.id, {}).get(block.id)
                if block_avail and not block_avail.get("available", True):
                    continue
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    t_i = template_idx[template.id]
                    f[f_i, b_i, t_i] = model.NewBoolVar(f"f_{f_i}_{b_i}_{t_i}")

        # 2D view for faculty
        f_2d = {}
        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                rotation_vars = [
                    f[f_i, b_i, t_i]
                    for t_i in range(len(context.templates))
                    if (f_i, b_i, t_i) in f
                ]
                if rotation_vars:
                    f_2d[f_i, b_i] = model.NewBoolVar(f"f_2d_{f_i}_{b_i}")
                    model.Add(sum(rotation_vars) >= 1).OnlyEnforceIf(f_2d[f_i, b_i])
                    model.Add(sum(rotation_vars) == 0).OnlyEnforceIf(
                        f_2d[f_i, b_i].Not()
                    )

        # ==================================================
        # OVERNIGHT CALL DECISION VARIABLES
        # call[f_i, b_i, "overnight"] = 1 if faculty f on call for block b's date
        # Only Sun-Thurs nights (weekday 0,1,2,3,6)
        # ==================================================
        call = {}
        call_eligible = getattr(context, "call_eligible_faculty", [])
        call_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {fac.id: i for i, fac in enumerate(call_eligible)},
        )

        if call_eligible:
            # Track dates already processed (one call per date, not per block)
            call_dates_processed = set()
            call_blocks = [
                block
                for block in context.blocks
                if block.date.weekday() in (0, 1, 2, 3, 6)  # Mon-Thu, Sun
            ]
            for block in call_blocks:
                if block.date in call_dates_processed:
                    continue
                call_dates_processed.add(block.date)

                b_i = context.block_idx[block.id]
                for faculty in call_eligible:
                    f_i = call_idx.get(faculty.id)
                    if f_i is not None:
                        call[f_i, b_i, "overnight"] = model.NewBoolVar(
                            f"call_{f_i}_{b_i}"
                        )
            logger.info(
                f"Created {len(call)} call variables for {len(call_eligible)} "
                f"eligible faculty across {len(call_dates_processed)} nights"
            )

        # ==================================================
        # FACULTY ACTIVITY DECISION VARIABLES (Half-Day Level)
        # These determine what each faculty does in each half-day slot:
        # - clinic: Faculty primary clinic session
        # - supervise: Faculty supervising residents
        # - pcat: Post-call attending (morning after overnight call)
        # - do: Day off (afternoon after overnight call)
        # If none selected, slot defaults to OFF
        # ==================================================
        fac_clinic = {}  # fac_clinic[f_i, b_i] = 1 if faculty f does clinic in block b
        fac_supervise = {}  # fac_supervise[f_i, b_i] = 1 if faculty f supervises
        fac_pcat = {}  # fac_pcat[f_i, b_i] = 1 if faculty f has PCAT
        fac_do = {}  # fac_do[f_i, b_i] = 1 if faculty f has DO

        # Track which blocks are AM vs PM for PCAT/DO assignment
        am_blocks = {b.id: b for b in context.blocks if b.time_of_day == "AM"}
        pm_blocks = {b.id: b for b in context.blocks if b.time_of_day == "PM"}

        # Create variables for all faculty across all blocks (including weekends for PCAT/DO)
        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            for block in context.blocks:  # All blocks, not just workdays
                b_i = context.block_idx[block.id]

                # Clinic only on workdays (not weekends/holidays)
                if not block.is_weekend and not getattr(block, "is_holiday", False):
                    fac_clinic[f_i, b_i] = model.NewBoolVar(f"fac_clinic_{f_i}_{b_i}")
                    fac_supervise[f_i, b_i] = model.NewBoolVar(
                        f"fac_supervise_{f_i}_{b_i}"
                    )

                # PCAT/DO can happen any day (after overnight call)
                fac_pcat[f_i, b_i] = model.NewBoolVar(f"fac_pcat_{f_i}_{b_i}")
                fac_do[f_i, b_i] = model.NewBoolVar(f"fac_do_{f_i}_{b_i}")

        logger.info(
            f"Created faculty activity variables: "
            f"{len(fac_clinic)} clinic, {len(fac_supervise)} supervise, "
            f"{len(fac_pcat)} pcat, {len(fac_do)} do"
        )

        # ==================================================
        # RESIDENT CLINIC INDICATORS (for supervision constraints)
        # ==================================================
        resident_clinic = {}
        clinic_template_ids = set()
        for template in context.templates:
            if getattr(template, "rotation_type", "") == "outpatient":
                clinic_template_ids.add(template.id)

        if clinic_template_ids:
            clinic_template_indices = [
                template_idx[tid] for tid in clinic_template_ids if tid in template_idx
            ]
            for resident in context.residents:
                r_i = context.resident_idx[resident.id]
                for block in workday_blocks:
                    b_i = context.block_idx[block.id]
                    clinic_vars = [
                        x[r_i, b_i, t_i]
                        for t_i in clinic_template_indices
                        if (r_i, b_i, t_i) in x
                    ]
                    if clinic_vars:
                        resident_clinic[
                            (resident.id, block.date, block.time_of_day)
                        ] = (
                            clinic_vars[0]
                            if len(clinic_vars) == 1
                            else sum(clinic_vars)
                        )

        # Re-key faculty activity vars from (int, int) to (UUID, date, slot)
        # so constraints can look them up by faculty ID + date + AM/PM
        faculty_at_by_slot: dict[tuple, Any] = {}
        faculty_pcat_by_slot: dict[tuple, Any] = {}
        faculty_clinic_by_slot: dict[tuple, Any] = {}
        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                slot_key = (faculty.id, block.date, block.time_of_day)
                if (f_i, b_i) in fac_supervise:
                    faculty_at_by_slot[slot_key] = fac_supervise[f_i, b_i]
                if (f_i, b_i) in fac_pcat:
                    faculty_pcat_by_slot[slot_key] = fac_pcat[f_i, b_i]
                if (f_i, b_i) in fac_clinic:
                    faculty_clinic_by_slot[slot_key] = fac_clinic[f_i, b_i]

        variables = {
            "assignments": x_2d,  # For legacy constraints (residents)
            "template_assignments": x,  # For rotation-specific constraints (residents)
            "faculty_assignments": f_2d,  # Faculty 2D view
            "faculty_template_assignments": f,  # Faculty 3D view
            "call_assignments": call,  # Overnight call assignments
            # Faculty activity variables (index-keyed, for objective function)
            "fac_clinic": fac_clinic,
            "fac_supervise": fac_supervise,
            "fac_pcat": fac_pcat,
            "fac_do": fac_do,
            # Constraint wiring (UUID-date-slot keyed)
            "faculty_at": faculty_at_by_slot,
            "faculty_pcat": faculty_pcat_by_slot,
            "faculty_clinic": faculty_clinic_by_slot,
            "resident_clinic": resident_clinic,
        }

        # ==================================================
        # CONSTRAINT: At most one rotation per resident per block
        # ==================================================
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                rotation_vars = [
                    x[r_i, b_i, t_i]
                    for t_i in range(len(context.templates))
                    if (r_i, b_i, t_i) in x
                ]
                if rotation_vars:
                    model.Add(sum(rotation_vars) == 1)

        # ==================================================
        # CONSTRAINT: At most one rotation per faculty per block
        # ==================================================
        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                rotation_vars = [
                    f[f_i, b_i, t_i]
                    for t_i in range(len(context.templates))
                    if (f_i, b_i, t_i) in f
                ]
                if rotation_vars:
                    model.Add(sum(rotation_vars) <= 1)

        # ==================================================
        # FACULTY ACTIVITY CONSTRAINTS
        # ==================================================

        # Hard-block faculty activity on locked/unavailable slots
        availability = getattr(context, "availability", {}) or {}
        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            for block in context.blocks:
                b_i = context.block_idx[block.id]
                is_locked = (faculty.id, block.id) in locked_blocks
                block_avail = availability.get(faculty.id, {}).get(block.id)
                is_unavailable = bool(block_avail) and not block_avail.get(
                    "available", True
                )
                if not (is_locked or is_unavailable):
                    continue
                if (f_i, b_i) in fac_clinic:
                    model.Add(fac_clinic[f_i, b_i] == 0)
                if (f_i, b_i) in fac_supervise:
                    model.Add(fac_supervise[f_i, b_i] == 0)
                if (f_i, b_i) in fac_pcat:
                    model.Add(fac_pcat[f_i, b_i] == 0)
                if (f_i, b_i) in fac_do:
                    model.Add(fac_do[f_i, b_i] == 0)

        # Constraint: At most one activity per faculty per slot
        # (clinic, supervise, pcat, do) are mutually exclusive
        # If none selected, slot is implicitly OFF
        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            for block in context.blocks:
                b_i = context.block_idx[block.id]
                activity_vars = []
                if (f_i, b_i) in fac_clinic:
                    activity_vars.append(fac_clinic[f_i, b_i])
                if (f_i, b_i) in fac_supervise:
                    activity_vars.append(fac_supervise[f_i, b_i])
                if (f_i, b_i) in fac_pcat:
                    activity_vars.append(fac_pcat[f_i, b_i])
                if (f_i, b_i) in fac_do:
                    activity_vars.append(fac_do[f_i, b_i])
                if activity_vars:
                    model.Add(sum(activity_vars) <= 1)

        # Constraint: Faculty clinic limits from DB (clinic_min/clinic_max per week)
        from collections import defaultdict
        from datetime import timedelta

        blocks_by_week: dict[tuple, list] = defaultdict(list)
        for block in workday_blocks:
            week_start = block.date - timedelta(days=block.date.weekday())
            blocks_by_week[week_start].append(block)

        # Soft penalty weight for clinic minimum shortfall
        CLINIC_MIN_PENALTY = 200  # Strong incentive to meet minimum clinic

        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            weekly_min = getattr(faculty, "min_clinic_halfdays_per_week", 0) or 0
            weekly_max = getattr(faculty, "max_clinic_halfdays_per_week", 4) or 4

            for week_start, week_blocks in blocks_by_week.items():
                clinic_vars = [
                    fac_clinic[f_i, context.block_idx[b.id]]
                    for b in week_blocks
                    if (f_i, context.block_idx[b.id]) in fac_clinic
                ]
                if clinic_vars:
                    model.Add(sum(clinic_vars) <= weekly_max)
                    # MIN is soft to avoid infeasibility with supervision demand
                    if weekly_min > 0:
                        shortfall = model.NewIntVar(
                            0,
                            weekly_min,
                            f"clinic_shortfall_{f_i}_{week_start}",
                        )
                        model.Add(shortfall >= weekly_min - sum(clinic_vars))
                        objective_terms = variables.setdefault("objective_terms", [])
                        objective_terms.append((shortfall, CLINIC_MIN_PENALTY))

        # Constraint: PCAT/DO linked to overnight call
        # If call[f, date] = 1, then pcat[f, date+1, AM] = 1 and do[f, date+1, PM] = 1
        allowed_pcat: set[tuple[int, int]] = set()
        allowed_do: set[tuple[int, int]] = set()
        if call_eligible and call:
            # Build date->block mapping
            date_am_block = {}
            date_pm_block = {}
            for block in context.blocks:
                if block.time_of_day == "AM":
                    date_am_block[block.date] = block
                else:
                    date_pm_block[block.date] = block

            # Pre-build reverse lookups for O(1) access (avoids O(N*B) inner loops)
            block_by_idx = {context.block_idx[b.id]: b for b in context.blocks}
            faculty_id_by_call_idx = {
                call_idx[fac.id]: fac.id for fac in call_eligible if fac.id in call_idx
            }

            for (f_i_call, b_i_call, call_type), call_var in call.items():
                call_block = block_by_idx.get(b_i_call)
                if not call_block:
                    continue

                next_day = call_block.date + timedelta(days=1)

                faculty_id = faculty_id_by_call_idx.get(f_i_call)
                if not faculty_id or faculty_id not in context.faculty_idx:
                    continue

                f_i = context.faculty_idx[faculty_id]

                # Link PCAT to next day AM (bidirectional)
                if next_day in date_am_block:
                    next_am = date_am_block[next_day]
                    next_am_b_i = context.block_idx[next_am.id]
                    if (f_i, next_am_b_i) in fac_pcat:
                        allowed_pcat.add((f_i, next_am_b_i))
                        # call <=> pcat (bidirectional: PCAT iff call)
                        model.Add(fac_pcat[f_i, next_am_b_i] == call_var)

                # Link DO to next day PM (bidirectional)
                if next_day in date_pm_block:
                    next_pm = date_pm_block[next_day]
                    next_pm_b_i = context.block_idx[next_pm.id]
                    if (f_i, next_pm_b_i) in fac_do:
                        allowed_do.add((f_i, next_pm_b_i))
                        # call <=> do (bidirectional: DO iff call)
                        model.Add(fac_do[f_i, next_pm_b_i] == call_var)

        # If no call mapping exists for a slot, PCAT/DO must be 0
        for (f_i, b_i), var in fac_pcat.items():
            if (f_i, b_i) not in allowed_pcat:
                model.Add(var == 0)
        for (f_i, b_i), var in fac_do.items():
            if (f_i, b_i) not in allowed_do:
                model.Add(var == 0)

        # Constraint: Supervision ratio (ACGME)
        # For each slot with residents in clinic, need enough faculty supervisors
        # PGY-1: 1 faculty per 2 residents (ratio 0.5)
        # PGY-2/3: 1 faculty per 4 residents (ratio 0.25)
        # Find clinic template(s)
        clinic_template_ids = set()
        for template in context.templates:
            name_lower = template.name.lower()
            if (
                "clinic" in name_lower
                or "fm" in name_lower
                or "outpatient" in name_lower
            ):
                clinic_template_ids.add(template.id)

        if clinic_template_ids:
            clinic_template_indices = [
                template_idx[tid] for tid in clinic_template_ids if tid in template_idx
            ]

            for block in workday_blocks:
                b_i = context.block_idx[block.id]

                # Count PGY-1 residents in clinic
                pgy1_in_clinic = []
                pgy23_in_clinic = []
                for resident in context.residents:
                    r_i = context.resident_idx[resident.id]
                    pgy = getattr(resident, "pgy_level", 2)
                    for t_i in clinic_template_indices:
                        if (r_i, b_i, t_i) in x:
                            if pgy == 1:
                                pgy1_in_clinic.append(x[r_i, b_i, t_i])
                            else:
                                pgy23_in_clinic.append(x[r_i, b_i, t_i])

                if not pgy1_in_clinic and not pgy23_in_clinic:
                    continue

                # Calculate supervision load (multiply by 4 to avoid fractions)
                # PGY-1: 2 per faculty (load = 2), PGY-2/3: 4 per faculty (load = 1)
                # supervision_load = pgy1 * 2 + pgy23 * 1
                # supervision_needed * 4 >= supervision_load
                pgy1_sum = sum(pgy1_in_clinic) if pgy1_in_clinic else 0
                pgy23_sum = sum(pgy23_in_clinic) if pgy23_in_clinic else 0
                supervision_load = pgy1_sum * 2 + pgy23_sum

                # Faculty supervising in this block
                faculty_supervising = [
                    fac_supervise[context.faculty_idx[fac.id], b_i]
                    for fac in context.faculty
                    if (context.faculty_idx[fac.id], b_i) in fac_supervise
                ]

                if faculty_supervising:
                    # supervision_needed >= ceil(supervision_load / 4)
                    # Linearized: 4 * sum(supervisors) >= supervision_load
                    model.Add(4 * sum(faculty_supervising) >= supervision_load)

        logger.info(
            "Added faculty activity constraints (clinic limits, PCAT/DO, supervision)"
        )

        # ==================================================
        # APPLY CONSTRAINTS FROM MANAGER
        # ==================================================
        self.constraint_manager.apply_to_cpsat(model, variables, context)

        # ==================================================
        # PRESERVE EXISTING ASSIGNMENTS
        # ==================================================
        if existing_assignments:
            for assignment in existing_assignments:
                if assignment.person_id in context.resident_idx:
                    r_i = context.resident_idx[assignment.person_id]
                    if assignment.block_id in context.block_idx:
                        b_i = context.block_idx[assignment.block_id]
                        if (
                            assignment.rotation_template_id
                            and assignment.rotation_template_id in template_idx
                        ):
                            t_i = template_idx[assignment.rotation_template_id]
                            if (r_i, b_i, t_i) in x:
                                model.Add(x[r_i, b_i, t_i] == 1)

        # ==================================================
        # OBJECTIVE FUNCTION
        # Maximize: coverage * 1000 - equity_penalty - template_balance_penalty
        #
        # Template balance ensures assignments are distributed across rotation
        # types, not concentrated in a single rotation (e.g., all Night Float).
        # ==================================================
        coverage = sum(x.values())

        # Calculate template assignment counts for balance penalty
        template_counts = {}
        for t_i, template in enumerate(context.templates):
            template_vars = [
                x[r_i, b_i, t_i]
                for r_i in range(len(context.residents))
                for b_i in range(len(workday_blocks))
                if (r_i, b_i, t_i) in x
            ]
            if template_vars:
                template_counts[t_i] = sum(template_vars)

        # Template balance penalty: penalize max template count to encourage distribution
        # This prevents all assignments going to one rotation type
        template_balance_penalty = None
        if len(template_counts) > 1:
            max_template_count = model.NewIntVar(
                0, len(context.residents) * len(workday_blocks), "max_template_count"
            )
            for t_i, count_expr in template_counts.items():
                model.Add(max_template_count >= count_expr)
            template_balance_penalty = max_template_count

        # Build objective with all penalties
        equity_penalty = variables.get("equity_penalty")
        objective_terms = variables.get("objective_terms", [])

        objective_expr = coverage * COVERAGE_WEIGHT
        if equity_penalty is not None:
            objective_expr -= equity_penalty * EQUITY_PENALTY_WEIGHT
        if template_balance_penalty is not None:
            objective_expr -= template_balance_penalty * TEMPLATE_BALANCE_WEIGHT
        if objective_terms:
            for term_var, weight in objective_terms:
                objective_expr -= term_var * int(weight)

        model.Maximize(objective_expr)

        # ==================================================
        # SOLUTION HINTING (warm start)
        # Provide a greedy initial solution so the solver starts with a
        # feasible bound and prunes the search space faster.
        # ==================================================
        hinted_resident_blocks: set[tuple[int, int]] = set()
        hint_count = 0

        # Priority 1: hint existing (locked) assignments
        for assignment in existing_assignments:
            if assignment.person_id in context.resident_idx:
                r_i = context.resident_idx[assignment.person_id]
                if assignment.block_id in context.block_idx:
                    b_i = context.block_idx[assignment.block_id]
                    if (
                        assignment.rotation_template_id
                        and assignment.rotation_template_id in template_idx
                    ):
                        t_i = template_idx[assignment.rotation_template_id]
                        if (r_i, b_i, t_i) in x:
                            model.AddHint(x[r_i, b_i, t_i], 1)
                            hinted_resident_blocks.add((r_i, b_i))
                            hint_count += 1

        # Priority 2: greedy fill — for each unhinted (resident, block),
        # hint the first available template to 1, rest to 0
        for (r_i, b_i, t_i), var in x.items():
            if (r_i, b_i) not in hinted_resident_blocks:
                model.AddHint(var, 1)
                hinted_resident_blocks.add((r_i, b_i))
                hint_count += 1
            else:
                model.AddHint(var, 0)

        logger.info(f"Solution hints: {hint_count} vars hinted to 1")

        # ==================================================
        # PRE-SOLVE DEBUGGING
        # ==================================================
        proto = model.Proto()
        logger.info("=" * 60)
        logger.info("PRE-SOLVE STATE")
        logger.info("=" * 60)
        logger.info(
            f"Model: {len(proto.variables)} vars, {len(proto.constraints)} constraints"
        )
        logger.info(
            f"Residents: {len(context.residents)}, Faculty: {len(context.faculty)}"
        )
        logger.info(
            f"Templates: {len(context.templates)}, Workday blocks: {len(workday_blocks)}"
        )
        logger.info(f"Resident decision vars (x): {len(x)}")
        logger.info(f"Faculty decision vars (f): {len(f)}")
        logger.info(f"Existing assignments to preserve: {len(existing_assignments)}")

        # Count locked assignments by person
        locked_by_person = {}
        for a in existing_assignments:
            name = "unknown"
            if a.person_id in context.resident_idx:
                name = f"R:{context.residents[context.resident_idx[a.person_id]].name}"
            elif a.person_id in context.faculty_idx:
                name = f"F:{context.faculty[context.faculty_idx[a.person_id]].name}"
            locked_by_person[name] = locked_by_person.get(name, 0) + 1
        for name, count in sorted(locked_by_person.items(), key=lambda x: -x[1])[:10]:
            logger.info(f"  Locked: {name} = {count}")

        # Log hard constraints from constraint manager
        hard_constraints = []
        soft_constraints = []
        for c in self.constraint_manager.constraints:
            is_hard = (
                hasattr(c, "is_hard")
                and c.is_hard
                or c.__class__.__name__.endswith("HardConstraint")
            )
            from app.scheduling.constraints.base import HardConstraint

            if isinstance(c, HardConstraint):
                hard_constraints.append(c.name)
            else:
                soft_constraints.append(c.name)
        logger.info(f"Hard constraints from manager: {hard_constraints}")
        logger.info(f"Soft constraints from manager: {soft_constraints}")

        # Log built-in hard constraints in this solver
        logger.info("Built-in hard constraints in solver:")
        logger.info(
            "  - OneAssignmentPerBlock: each (resident, block) has exactly 1 template"
        )
        logger.info(
            "  - FacultyAtMostOnePerBlock: each (faculty, block) has at most 1 template"
        )
        logger.info("  - FacultySupervision: 4*supervisors >= supervision_load")
        logger.info("  - OneCallPerNight: exactly 1 faculty per night")
        logger.info("  - FacultyClinicCap: faculty clinic <= weekly max")
        logger.info(
            "  - PCAT/DO linkage: call[f,n]=1 => pcat[f,n+1,AM]=1, do[f,n+1,PM]=1"
        )
        logger.info(
            "  - ExistingAssignmentPreservation: locked assignments forced to 1"
        )
        logger.info(f"  - Locked existing assignments: {len(existing_assignments)}")
        logger.info("=" * 60)

        # ==================================================
        # SOLVE
        # ==================================================
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.timeout_seconds
        solver.parameters.num_search_workers = self.num_workers
        # Disable symmetry detection — residents/faculty have heterogeneous
        # PGY levels, templates, and availability so few symmetries exist.
        # Saves O(n^2) presolve overhead.
        solver.parameters.symmetry_level = 0
        # Minimal linearization — constraints are already linear or use
        # AddAbsEquality; deeper levels add overhead for no benefit.
        solver.parameters.linearization_level = 1
        solver.parameters.log_search_progress = True

        # Create progress callback if Redis client is available
        callback = None
        if self.task_id and self.redis_client:
            try:
                # Import broadcast function for real-time visualization
                from app.websocket.manager import broadcast_solver_event

                callback_wrapper = SolverProgressCallback(
                    self.task_id,
                    self.redis_client,
                    broadcast_callback=broadcast_solver_event,
                )
                callback = callback_wrapper.get_callback()
                logger.info(f"Progress tracking enabled for task {self.task_id}")
            except Exception as e:
                logger.warning(f"Failed to create progress callback: {e}")

        # Solve with or without callback
        if callback:
            status = solver.Solve(model, callback)
        else:
            status = solver.Solve(model)

        runtime = time.time() - start_time

        # Store final status in Redis if callback was used
        if self.task_id and self.redis_client:
            try:
                status_name = solver.StatusName(status)
                final_data = {
                    "solutions_found": callback.solution_count if callback else 0,
                    "current_objective": (
                        solver.ObjectiveValue()
                        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
                        else 0
                    ),
                    "best_bound": (
                        solver.BestObjectiveBound()
                        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
                        else 0
                    ),
                    "optimality_gap_pct": 0.0 if status == cp_model.OPTIMAL else None,
                    "progress_pct": 100.0 if status == cp_model.OPTIMAL else 99.0,
                    "elapsed_seconds": round(runtime, 2),
                    "status": (
                        "completed"
                        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
                        else "failed"
                    ),
                    "solver_status": status_name,
                    "timestamp": time.time(),
                }
                self.redis_client.setex(
                    f"solver_progress:{self.task_id}",
                    SOLVER_PROGRESS_TTL_SECONDS,
                    json.dumps(final_data),
                )
            except Exception as e:
                logger.error(f"Failed to store final status in Redis: {e}")

        # Check solution status
        status_name = solver.StatusName(status)
        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            logger.warning(f"CP-SAT solver status: {status_name}")

            # Enhanced debugging for INFEASIBLE
            logger.error("=" * 60)
            logger.error("INFEASIBLE SOLVER DEBUGGING")
            logger.error("=" * 60)

            # Log model statistics
            proto = model.Proto()
            logger.error(
                f"Model stats: {len(proto.variables)} vars, {len(proto.constraints)} constraints"
            )

            # Log resident/faculty counts
            logger.error(f"Residents: {len(context.residents)}")
            logger.error(f"Faculty: {len(context.faculty)}")
            logger.error(f"Templates: {len(context.templates)}")
            logger.error(f"Workday blocks: {len(workday_blocks)}")

            # Log locked assignment counts
            locked_resident_count = sum(
                1 for a in existing_assignments if a.person_id in context.resident_idx
            )
            locked_faculty_count = sum(
                1 for a in existing_assignments if a.person_id in context.faculty_idx
            )
            logger.error(f"Locked resident assignments: {locked_resident_count}")
            logger.error(f"Locked faculty assignments: {locked_faculty_count}")

            # Log template usage
            template_usage = {}
            for a in existing_assignments:
                if a.rotation_template_id:
                    template_usage[a.rotation_template_id] = (
                        template_usage.get(a.rotation_template_id, 0) + 1
                    )
            logger.error(
                f"Template usage in locked assignments: {len(template_usage)} unique templates"
            )
            for tid, count in sorted(template_usage.items(), key=lambda x: -x[1])[:10]:
                tname = next(
                    (t.name for t in context.templates if t.id == tid), str(tid)
                )
                logger.error(f"  {tname}: {count}")

            # Log x variable counts by type
            resident_vars = sum(1 for k in x if k[0] < len(context.residents))
            logger.error(f"Resident decision vars (x): {resident_vars}")
            logger.error(f"Faculty decision vars (f): {len(f)}")

            # Check for over-constrained blocks
            block_constraint_counts = {}
            for r_i, b_i, t_i in x:
                block_constraint_counts[b_i] = block_constraint_counts.get(b_i, 0) + 1
            if block_constraint_counts:
                max_block = max(block_constraint_counts.values())
                min_block = min(block_constraint_counts.values())
                logger.error(f"Vars per block: min={min_block}, max={max_block}")

            # Log supervision constraint info
            logger.error(f"Clinic template IDs found: {len(clinic_template_ids)}")
            logger.error(f"Faculty supervise vars: {len(fac_supervise)}")

            logger.error("=" * 60)

            return SolverResult(
                success=False,
                assignments=[],
                status="infeasible",
                solver_status=status_name,
                runtime_seconds=runtime,
            )

        # ==================================================
        # EXTRACT SOLUTION - Residents
        # ==================================================
        assignments = []
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    t_i = template_idx[template.id]
                    if (r_i, b_i, t_i) in x and solver.Value(x[r_i, b_i, t_i]) == 1:
                        assignments.append(
                            (
                                resident.id,
                                block.id,
                                template.id,
                            )
                        )

        # ==================================================
        # EXTRACT SOLUTION - Faculty
        # ==================================================
        faculty_assignment_count = 0
        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    t_i = template_idx[template.id]
                    if (f_i, b_i, t_i) in f and solver.Value(f[f_i, b_i, t_i]) == 1:
                        assignments.append(
                            (
                                faculty.id,
                                block.id,
                                template.id,
                            )
                        )
                        faculty_assignment_count += 1

        # ==================================================
        # EXTRACT SOLUTION - Overnight Call Assignments
        # ==================================================
        call_assignments_result = []
        if call_eligible and call:
            block_id_by_idx = {context.block_idx[b.id]: b.id for b in context.blocks}
            for (f_i, b_i, call_type), var in call.items():
                if solver.Value(var) == 1:
                    # Find the faculty and block for this variable
                    faculty_id = None
                    block_id = block_id_by_idx.get(b_i)
                    for fac in call_eligible:
                        if call_idx.get(fac.id) == f_i:
                            faculty_id = fac.id
                            break
                    if faculty_id and block_id:
                        call_assignments_result.append(
                            (faculty_id, block_id, call_type)
                        )

            logger.info(
                f"CP-SAT found {len(call_assignments_result)} overnight call assignments"
            )

        # ==================================================
        # EXTRACT SOLUTION - Faculty Half-Day Assignments
        # For each faculty, for each block, determine activity:
        # clinic, supervise, pcat, do, or off (default)
        # ==================================================
        faculty_half_day_result = []
        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            for block in context.blocks:  # All blocks (56 per 4-week period)
                b_i = context.block_idx[block.id]

                # Determine activity for this slot
                activity = "OFF"  # Default

                if (f_i, b_i) in fac_clinic and solver.Value(fac_clinic[f_i, b_i]) == 1:
                    activity = "C"  # Clinic
                elif (f_i, b_i) in fac_supervise and solver.Value(
                    fac_supervise[f_i, b_i]
                ) == 1:
                    activity = "AT"  # Attending/Supervision
                elif (f_i, b_i) in fac_pcat and solver.Value(fac_pcat[f_i, b_i]) == 1:
                    activity = "PCAT"  # Post-Call Attending Time
                elif (f_i, b_i) in fac_do and solver.Value(fac_do[f_i, b_i]) == 1:
                    activity = "DO"  # Day Off (post-call)

                faculty_half_day_result.append((faculty.id, block.id, activity))

        # Count by activity type for logging
        activity_counts = {}
        for _, _, act in faculty_half_day_result:
            activity_counts[act] = activity_counts.get(act, 0) + 1

        logger.info(
            f"CP-SAT generated {len(faculty_half_day_result)} faculty half-day assignments "
            f"({len(context.faculty)} faculty × {len(context.blocks)} blocks): "
            f"C={activity_counts.get('C', 0)}, AT={activity_counts.get('AT', 0)}, "
            f"PCAT={activity_counts.get('PCAT', 0)}, DO={activity_counts.get('DO', 0)}, "
            f"OFF={activity_counts.get('OFF', 0)}"
        )

        logger.info(
            f"CP-SAT found {len(assignments)} assignments "
            f"({len(assignments) - faculty_assignment_count} residents, "
            f"{faculty_assignment_count} faculty) in {runtime:.2f}s (status: {status_name})"
        )

        return SolverResult(
            success=True,
            assignments=assignments,
            status="optimal" if status == cp_model.OPTIMAL else "feasible",
            objective_value=solver.ObjectiveValue(),
            runtime_seconds=runtime,
            solver_status=status_name,
            statistics={
                "total_blocks": len(workday_blocks),
                "total_residents": len(context.residents),
                "total_faculty": len(context.faculty),
                "total_templates": len(context.templates),
                "resident_assignments": len(assignments) - faculty_assignment_count,
                "faculty_assignments": faculty_assignment_count,
                "call_assignments": len(call_assignments_result),
                "faculty_half_day_assignments": len(faculty_half_day_result),
                "faculty_activity_breakdown": activity_counts,
                "coverage_rate": (
                    len(assignments) / len(workday_blocks) if workday_blocks else 0
                ),
                "branches": solver.NumBranches(),
                "conflicts": solver.NumConflicts(),
            },
            call_assignments=call_assignments_result,
            faculty_half_day_assignments=faculty_half_day_result,
        )

    @staticmethod
    def get_progress(task_id: str, redis_client) -> dict | None:
        """
        Query the current progress of a solver task from Redis.

        Args:
            task_id: Unique identifier for the solver task
            redis_client: Redis client for retrieving progress data

        Returns:
            Dictionary with progress information, or None if not found

        Example response:
            {
                "solutions_found": 5,
                "current_objective": 1234,
                "best_bound": 1250,
                "optimality_gap_pct": 1.28,
                "progress_pct": 98.72,
                "elapsed_seconds": 15.3,
                "status": "solving",  # or "completed" / "failed"
                "solver_status": "OPTIMAL",  # OR-Tools status name
                "timestamp": 1234567890.123
            }
        """
        if not redis_client:
            return None

        try:
            key = f"solver_progress:{task_id}"
            data = redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve progress from Redis: {e}")
            return None


class HybridSolver(BaseSolver):
    """
    Hybrid solver that combines PuLP and CP-SAT.

    Strategy:
    1. Use PuLP for initial feasible solution (fast)
    2. Use CP-SAT to optimize and verify (accurate)
    3. Fallback between solvers on failure

    Best for:
    - Large, complex scheduling problems
    - When both speed and quality matter
    - When one solver might struggle alone
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 120.0,
        pulp_timeout: float = 30.0,
        cpsat_timeout: float = 60.0,
    ) -> None:
        super().__init__(constraint_manager, timeout_seconds)
        self.pulp_timeout = pulp_timeout
        self.cpsat_timeout = cpsat_timeout

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] | None = None,
    ) -> SolverResult:
        """Solve using hybrid approach."""
        start_time = time.time()

        # Try CP-SAT first (usually gives better results)
        cpsat_solver = CPSATSolver(
            self.constraint_manager,
            timeout_seconds=self.cpsat_timeout,
        )
        result = cpsat_solver.solve(context, existing_assignments)

        if result.success:
            logger.info("Hybrid: CP-SAT succeeded")
            return result

        # Fallback to PuLP
        logger.info("Hybrid: CP-SAT failed, trying PuLP")
        pulp_solver = PuLPSolver(
            self.constraint_manager,
            timeout_seconds=self.pulp_timeout,
        )
        result = pulp_solver.solve(context, existing_assignments)

        if result.success:
            logger.info("Hybrid: PuLP succeeded")
            return result

        # Both failed
        runtime = time.time() - start_time
        logger.warning("Hybrid: Both solvers failed")
        return SolverResult(
            success=False,
            assignments=[],
            status="infeasible",
            solver_status="Both CP-SAT and PuLP failed",
            runtime_seconds=runtime,
        )


class GreedySolver(BaseSolver):
    """
    Fast greedy solver for quick assignments.

    Strategy:
    - Sort blocks by difficulty (fewest eligible residents first)
    - Assign most available resident with fewest current assignments

    Best for:
    - Quick initial solutions
    - Simple scheduling scenarios
    - When speed is more important than optimality

    Features:
    - Generates decision explanations for each assignment
    - Tracks alternatives considered and rejection reasons
    - Computes confidence scores based on decision margin
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 60.0,
        generate_explanations: bool = True,
    ) -> None:
        super().__init__(constraint_manager, timeout_seconds)
        self.generate_explanations = generate_explanations

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] | None = None,
    ) -> SolverResult:
        """
        Solve scheduling problem using greedy heuristic algorithm with explainability.

        The greedy algorithm prioritizes difficult-to-assign blocks first and
        selects residents based on workload equity. While not guaranteed to find
        the optimal solution, it is fast and generates human-readable explanations
        for each decision.

        Algorithm:
            1. Calculate difficulty score for each block (# of eligible residents)
            2. Sort blocks by difficulty (fewest eligible residents first)
            3. For each block in sorted order:
               a. Find eligible residents (check availability)
               b. Score each candidate (prefer residents with fewer assignments)
               c. Select highest-scoring resident
               d. Generate decision explanation (if enabled)
               e. Assign resident to block with best available template
               f. Update assignment counts

        Decision Scoring:
            - Base score: max_assignments - current_assignments
            - This prioritizes residents with the fewest current assignments
            - Promotes workload equity naturally

        Explainability:
            If generate_explanations=True, creates DecisionExplanation for each
            assignment containing:
            - Why this resident was selected
            - What alternatives were considered
            - Constraint evaluations
            - Confidence score

        Advantages:
            - **Speed**: Very fast, typically <1 second for 1000+ blocks
            - **Transparency**: Full explanation of each decision
            - **Predictability**: Deterministic, same inputs = same outputs
            - **No dependencies**: Works without OR-Tools or PuLP

        Limitations:
            - **Not optimal**: May miss better solutions
            - **Greedy myopia**: Doesn't consider future consequences
            - **Local optima**: Can get stuck in suboptimal patterns

        Performance:
            - Small problems (<100 blocks): <0.1 seconds
            - Medium problems (<1000 blocks): 0.1-1 seconds
            - Large problems (<10000 blocks): 1-10 seconds

        Args:
            context: SchedulingContext with residents, blocks, templates
            existing_assignments: Optional assignments to preserve

        Returns:
            SolverResult with:
                - success: True (always succeeds with partial solution)
                - assignments: List of (person_id, block_id, template_id) tuples
                - status: "feasible"
                - explanations: Dict of (person_id, block_id) -> explanation
                - statistics: High/medium/low confidence assignment counts

        Example:
            >>> solver = GreedySolver(generate_explanations=True)
            >>> result = solver.solve(context)
            >>> for (pid, bid), explanation in result.explanations.items():
            ...     print(f"{explanation.person_name}: {explanation.trade_off_summary}")

        Best For:
            - Quick initial solutions
            - Simple scheduling scenarios
            - When transparency is more important than optimality
            - Prototyping and debugging
        """
        from app.scheduling.explainability import ExplainabilityService

        start_time = time.time()

        # Filter to workday blocks
        workday_blocks = [b for b in context.blocks if not b.is_weekend]

        if not workday_blocks or not context.residents or not context.templates:
            return SolverResult(
                success=False,
                assignments=[],
                status="empty",
                solver_status="No blocks, residents, or rotation templates",
            )

        # Initialize explainability service
        explainability = None
        if self.generate_explanations:
            explainability = ExplainabilityService(
                context=context,
                constraint_manager=self.constraint_manager,
                algorithm="greedy",
            )

        # Track existing assignments
        assigned_blocks = set()
        assignment_counts = {r.id: 0 for r in context.residents}
        template_block_counts = defaultdict(
            lambda: defaultdict(int)
        )  # template_id -> block_id -> count

        if existing_assignments:
            for a in existing_assignments:
                assigned_blocks.add(a.block_id)
                if a.person_id in assignment_counts:
                    assignment_counts[a.person_id] += 1
                if a.rotation_template_id:
                    template_block_counts[a.rotation_template_id][a.block_id] += 1

        # Calculate difficulty (eligible resident count) for each block
        def count_eligible(block) -> int:
            count = 0
            for r in context.residents:
                if self._is_available(r.id, block.id, context):
                    count += 1
            return count

        # Sort blocks by difficulty (hardest first)
        sorted_blocks = sorted(
            [b for b in workday_blocks if b.id not in assigned_blocks],
            key=count_eligible,
        )

        # Assign residents with explanations
        assignments = []
        explanations = {}

        for block in sorted_blocks:
            # Find eligible residents
            eligible = [
                r
                for r in context.residents
                if self._is_available(r.id, block.id, context)
            ]

            if not eligible:
                continue  # No one available

            # Score each candidate (lower is better for greedy equity)
            # Score = current assignments (we want to minimize this)
            candidate_scores = {}
            for r in eligible:
                # Invert so higher score = better candidate
                # Max assignments across all residents - this resident's count
                max_assigns = (
                    max(assignment_counts.values()) if assignment_counts else 0
                )
                candidate_scores[r.id] = (max_assigns - assignment_counts[r.id]) * 100

            # Select resident with fewest assignments (highest inverted score)
            selected = max(eligible, key=lambda r: candidate_scores[r.id])

            # Select best available template with rotation distribution
            # Instead of picking first valid template, distribute across templates
            template = None
            valid_templates = []
            for t in context.templates:
                # Check capacity constraint
                if (
                    t.max_residents
                    and template_block_counts[t.id][block.id] >= t.max_residents
                ):
                    continue

                # This template is valid - add to candidates
                valid_templates.append(t)

            if valid_templates:
                # Select template with fewest total assignments for even distribution
                # This prevents all assignments going to the first template
                template = min(
                    valid_templates,
                    key=lambda t: sum(template_block_counts[t.id].values()),
                )

            if not template:
                # No valid template available, skip this block
                logger.debug(
                    f"No valid rotation template for resident {selected.name} in block {block.id}"
                )
                continue

            # Generate explanation for this decision
            if explainability:
                explanation = explainability.explain_assignment(
                    selected_person=selected,
                    block=block,
                    template=template,
                    all_candidates=eligible,
                    candidate_scores=candidate_scores,
                    assignment_counts=assignment_counts.copy(),
                    score_breakdown={
                        "equity_score": candidate_scores[selected.id],
                        "coverage": COVERAGE_WEIGHT,  # Base coverage value
                    },
                )
                explanations[(selected.id, block.id)] = explanation.model_dump()

            assignments.append(
                (
                    selected.id,
                    block.id,
                    template.id,
                )
            )
            assignment_counts[selected.id] += 1
            template_block_counts[template.id][block.id] += 1

        # ==================================================
        # GREEDY FACULTY CALL ASSIGNMENT
        # Assign overnight call to faculty (Sun-Thu nights)
        # ==================================================
        call_assignments_result = []
        call_eligible = getattr(context, "call_eligible_faculty", [])

        if call_eligible:
            # Track call assignments per faculty for equity
            call_counts = {fac.id: 0 for fac in call_eligible}

            # Get unique call dates (Sun-Thu nights)
            call_dates_processed = set()
            call_blocks = [
                block
                for block in context.blocks
                if block.date.weekday() in (0, 1, 2, 3, 6)  # Mon-Thu, Sun
            ]

            for block in call_blocks:
                if block.date in call_dates_processed:
                    continue
                call_dates_processed.add(block.date)

                # Find available call-eligible faculty
                available_faculty = [
                    fac
                    for fac in call_eligible
                    if self._is_available(fac.id, block.id, context)
                ]

                if not available_faculty:
                    continue

                # Select faculty with fewest call assignments (greedy equity)
                selected_faculty = min(
                    available_faculty, key=lambda f: call_counts[f.id]
                )

                call_assignments_result.append(
                    (selected_faculty.id, block.id, "overnight")
                )
                call_counts[selected_faculty.id] += 1

            logger.info(
                f"Greedy assigned {len(call_assignments_result)} overnight call "
                f"assignments to {len(call_eligible)} eligible faculty"
            )

        runtime = time.time() - start_time

        logger.info(f"Greedy found {len(assignments)} assignments in {runtime:.2f}s")

        # Calculate confidence distribution
        high_conf = sum(
            1 for e in explanations.values() if e.get("confidence") == "high"
        )
        med_conf = sum(
            1 for e in explanations.values() if e.get("confidence") == "medium"
        )
        low_conf = sum(1 for e in explanations.values() if e.get("confidence") == "low")

        return SolverResult(
            success=True,
            assignments=assignments,
            status="feasible",
            objective_value=len(assignments),
            runtime_seconds=runtime,
            solver_status="Greedy complete",
            statistics={
                "total_blocks": len(workday_blocks),
                "total_residents": len(context.residents),
                "total_templates": len(context.templates),
                "coverage_rate": (
                    len(assignments) / len(sorted_blocks) if sorted_blocks else 0
                ),
                "high_confidence_assignments": high_conf,
                "medium_confidence_assignments": med_conf,
                "low_confidence_assignments": low_conf,
                "call_assignments": len(call_assignments_result),
            },
            explanations=explanations,
            call_assignments=call_assignments_result,
        )

    def _is_available(
        self, person_id: UUID, block_id: UUID, context: SchedulingContext
    ) -> bool:
        """Check if person is available for block."""
        if person_id not in context.availability:
            return True
        if block_id not in context.availability[person_id]:
            return True
        return context.availability[person_id][block_id].get("available", True)


# ==================================================
# SOLVER FACTORY
# ==================================================


class SolverFactory:
    """
    Factory for creating solver instances by name.

    Provides a centralized registry of available solvers and a simple
    interface for creating solver instances with appropriate configurations.

    Available Solvers:
        - **greedy**: Fast heuristic solver with explainability
        - **pulp**: Linear programming solver (requires PuLP package)
        - **cp_sat**: Constraint programming solver (requires OR-Tools package)
        - **hybrid**: Combines CP-SAT and PuLP for best results
        - **quantum**: Hybrid quantum-inspired solver (auto-selects best approach)
        - **qubo**: PyQUBO-based QUBO solver (requires pyqubo package)
        - **quantum_sa**: Quantum-inspired simulated annealing (pure Python fallback)

    Solver Selection Guide:
        - Small problems (<100 blocks): Use "greedy" for speed
        - Medium problems (<500 blocks): Use "cp_sat" for quality
        - Large problems (>500 blocks): Use "hybrid" for reliability
        - Need explanations: Use "greedy" with generate_explanations=True
        - Production schedules: Use "cp_sat" or "hybrid" for optimality
        - Experimental/research: Use "quantum" or "quantum_sa"

    Example:
        >>> # Create a CP-SAT solver with custom timeout
        >>> solver = SolverFactory.create(
        ...     "cp_sat",
        ...     timeout_seconds=120.0,
        ...     num_workers=8
        ... )
        >>> result = solver.solve(context)

        >>> # Create a greedy solver with explanations
        >>> solver = SolverFactory.create(
        ...     "greedy",
        ...     generate_explanations=True
        ... )
    """

    _solvers = {
        "greedy": GreedySolver,
        "pulp": PuLPSolver,
        "cp_sat": CPSATSolver,
        "hybrid": HybridSolver,
        "pyomo": None,  # Lazy-loaded to avoid import if not used
        "quantum": None,  # Lazy-loaded quantum-inspired solver
        "qubo": None,  # Lazy-loaded PyQUBO-based solver
        "quantum_sa": None,  # Lazy-loaded simulated quantum annealing
    }

    @classmethod
    def _get_pyomo_solver(cls) -> type:
        """Lazy-load PyomoSolver to avoid import errors if not installed."""
        if cls._solvers["pyomo"] is None:
            try:
                from app.scheduling.pyomo_solver import PyomoSolver

                cls._solvers["pyomo"] = PyomoSolver
            except ImportError:
                raise ValueError(
                    "PyomoSolver requires pyomo package: pip install pyomo"
                )
        return cls._solvers["pyomo"]

    @classmethod
    def _get_quantum_solver(cls, solver_type: str) -> type:
        """
        Lazy-load quantum solvers to avoid import errors if not installed.

        Args:
            solver_type: One of 'quantum', 'qubo', or 'quantum_sa'

        Returns:
            The requested solver class

        Note:
            These solvers have optional dependencies:
            - quantum/quantum_sa: Works with pure Python fallback (no dependencies)
            - qubo: Requires PyQUBO (pip install pyqubo)

        Environment Configuration:
            - USE_QUANTUM_SOLVER: Enable quantum solver (default: false)
            - DWAVE_API_TOKEN: D-Wave API token
            - QUANTUM_SOLVER_BACKEND: "classical" or "quantum" (default: classical)

        The solver gracefully falls back to classical simulated annealing if:
            - D-Wave libraries not installed
            - API token missing or invalid
            - D-Wave service unreachable
        """
        if cls._solvers[solver_type] is None:
            try:
                from app.scheduling.quantum import (
                    QuantumInspiredSolver,
                    QUBOSolver,
                    SimulatedQuantumAnnealingSolver,
                )

                cls._solvers["quantum"] = QuantumInspiredSolver
                cls._solvers["qubo"] = QUBOSolver
                cls._solvers["quantum_sa"] = SimulatedQuantumAnnealingSolver
            except ImportError as e:
                raise ValueError(
                    f"Quantum solver '{solver_type}' requires quantum module. "
                    f"Error: {e}"
                )
        return cls._solvers[solver_type]

    @classmethod
    def create(
        cls,
        name: str,
        constraint_manager: ConstraintManager | None = None,
        **kwargs,
    ) -> BaseSolver:
        """
        Create a solver instance by name.

        Args:
            name: Solver name ('greedy', 'pulp', 'cp_sat', 'hybrid')
            constraint_manager: Optional ConstraintManager instance.
                              If None, creates default manager with ACGME constraints.
            **kwargs: Solver-specific keyword arguments:
                     - timeout_seconds (float): Maximum solve time (default: 60.0)
                     - num_workers (int): Parallel workers for CP-SAT (default: 4)
                     - generate_explanations (bool): For greedy solver (default: True)
                     - solver_backend (str): For PuLP solver (default: "PULP_CBC_CMD")
                     - pulp_timeout (float): For hybrid solver PuLP phase
                     - cpsat_timeout (float): For hybrid solver CP-SAT phase

        Returns:
            BaseSolver: Instance of the requested solver

        Raises:
            ValueError: If solver name is not recognized

        Example:
            >>> # Create CP-SAT solver with long timeout
            >>> solver = SolverFactory.create(
            ...     "cp_sat",
            ...     timeout_seconds=300.0,
            ...     num_workers=16
            ... )

            >>> # Create custom constraint manager
            >>> manager = ConstraintManager()
            >>> manager.add(AvailabilityConstraint())
            >>> manager.add(CoverageConstraint(weight=1000.0))
            >>> solver = SolverFactory.create("greedy", constraint_manager=manager)
        """
        if name not in cls._solvers:
            raise ValueError(
                f"Unknown solver: {name}. Available: {list(cls._solvers.keys())}"
            )

        # Handle lazy-loaded solvers
        if name == "pyomo":
            solver_class = cls._get_pyomo_solver()
        elif name in ("quantum", "qubo", "quantum_sa"):
            solver_class = cls._get_quantum_solver(name)
        else:
            solver_class = cls._solvers[name]

        return solver_class(constraint_manager=constraint_manager, **kwargs)

    @classmethod
    def available_solvers(cls) -> list[str]:
        """Get list of available solver names."""
        return list(cls._solvers.keys())

    @classmethod
    def register(cls, name: str, solver_class: type) -> None:
        """Register a custom solver."""
        cls._solvers[name] = solver_class
