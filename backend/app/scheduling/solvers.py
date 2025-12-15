"""
Optimization Solvers for Residency Scheduling.

This module provides multiple solver implementations:
- PuLP Linear Programming: Fast, good for large problems
- OR-Tools CP-SAT: Optimal solutions with constraint propagation
- Hybrid Solver: Combines approaches for best results

Each solver uses the modular constraint system from constraints.py.
"""
from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Optional, Any
from uuid import UUID
from collections import defaultdict
import time
import logging

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.block import Block
from app.models.assignment import Assignment
from app.models.rotation_template import RotationTemplate
from app.scheduling.constraints import (
    ConstraintManager,
    SchedulingContext,
    ConstraintResult,
)

logger = logging.getLogger(__name__)


class SolverResult:
    """Result from a solver run."""

    def __init__(
        self,
        success: bool,
        assignments: list[tuple[UUID, UUID, Optional[UUID]]],  # (person_id, block_id, template_id)
        status: str,
        objective_value: float = 0.0,
        runtime_seconds: float = 0.0,
        solver_status: str = "",
        statistics: dict = None,
    ):
        self.success = success
        self.assignments = assignments
        self.status = status
        self.objective_value = objective_value
        self.runtime_seconds = runtime_seconds
        self.solver_status = solver_status
        self.statistics = statistics or {}

    def __repr__(self):
        return f"SolverResult(success={self.success}, assignments={len(self.assignments)}, status={self.status})"


class BaseSolver(ABC):
    """
    Base class for scheduling solvers.

    All solvers use a ConstraintManager for composable constraints
    and a SchedulingContext for data access.
    """

    def __init__(
        self,
        constraint_manager: Optional[ConstraintManager] = None,
        timeout_seconds: float = 60.0,
    ):
        self.constraint_manager = constraint_manager or ConstraintManager.create_default()
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] = None,
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
    ) -> Optional[RotationTemplate]:
        """Select appropriate rotation template for a resident."""
        suitable = []
        for template in templates:
            # Skip templates requiring procedure credentials
            if template.requires_procedure_credential:
                continue
            suitable.append(template)

        return suitable[0] if suitable else None


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
        constraint_manager: Optional[ConstraintManager] = None,
        timeout_seconds: float = 60.0,
        solver_backend: str = "PULP_CBC_CMD",
    ):
        super().__init__(constraint_manager, timeout_seconds)
        self.solver_backend = solver_backend

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] = None,
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

        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    # Skip templates requiring procedure credentials if resident doesn't have them
                    if template.requires_procedure_credential:
                        continue

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

        variables = {
            "assignments": x_2d,  # For legacy constraints
            "template_assignments": x,  # For rotation-specific constraints
        }

        # ==================================================
        # CONSTRAINT: At most one rotation per person per block
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
                        pulp.lpSum(rotation_vars) <= 1,
                        f"one_rotation_{r_i}_{b_i}"
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
                        if assignment.rotation_template_id and assignment.rotation_template_id in template_idx:
                            t_i = template_idx[assignment.rotation_template_id]
                            if (r_i, b_i, t_i) in x:
                                prob += x[r_i, b_i, t_i] == 1, f"preserve_{r_i}_{b_i}_{t_i}"

        # ==================================================
        # OBJECTIVE FUNCTION
        # Maximize: coverage * weight - equity_penalty
        # ==================================================
        coverage = pulp.lpSum(x.values())

        # Equity penalty: minimize max assignments
        max_assigns = variables.get("equity_penalty")
        if max_assigns:
            prob += 1000 * coverage - 10 * max_assigns, "objective"
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
        # EXTRACT SOLUTION
        # ==================================================
        assignments = []
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    t_i = template_idx[template.id]
                    if (r_i, b_i, t_i) in x and pulp.value(x[r_i, b_i, t_i]) == 1:
                        assignments.append((
                            resident.id,
                            block.id,
                            template.id,
                        ))

        logger.info(f"PuLP found {len(assignments)} assignments in {runtime:.2f}s")

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
                "total_templates": len(context.templates),
                "coverage_rate": len(assignments) / len(workday_blocks) if workday_blocks else 0,
            },
        )


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
        constraint_manager: Optional[ConstraintManager] = None,
        timeout_seconds: float = 60.0,
        num_workers: int = 4,
    ):
        super().__init__(constraint_manager, timeout_seconds)
        self.num_workers = num_workers

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] = None,
    ) -> SolverResult:
        """Solve using OR-Tools CP-SAT."""
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

        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    # Skip templates requiring procedure credentials if resident doesn't have them
                    if template.requires_procedure_credential:
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
                    model.Add(sum(rotation_vars) == 0).OnlyEnforceIf(x_2d[r_i, b_i].Not())

        variables = {
            "assignments": x_2d,  # For legacy constraints
            "template_assignments": x,  # For rotation-specific constraints
        }

        # ==================================================
        # CONSTRAINT: At most one rotation per person per block
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
                    model.Add(sum(rotation_vars) <= 1)

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
                        if assignment.rotation_template_id and assignment.rotation_template_id in template_idx:
                            t_i = template_idx[assignment.rotation_template_id]
                            if (r_i, b_i, t_i) in x:
                                model.Add(x[r_i, b_i, t_i] == 1)

        # ==================================================
        # OBJECTIVE FUNCTION
        # Maximize: coverage * 1000 - equity_penalty
        # ==================================================
        coverage = sum(x.values())

        equity_penalty = variables.get("equity_penalty")
        if equity_penalty is not None:
            model.Maximize(coverage * 1000 - equity_penalty * 10)
        else:
            model.Maximize(coverage)

        # ==================================================
        # SOLVE
        # ==================================================
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.timeout_seconds
        solver.parameters.num_search_workers = self.num_workers

        status = solver.Solve(model)
        runtime = time.time() - start_time

        # Check solution status
        status_name = solver.StatusName(status)
        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            logger.warning(f"CP-SAT solver status: {status_name}")
            return SolverResult(
                success=False,
                assignments=[],
                status="infeasible",
                solver_status=status_name,
                runtime_seconds=runtime,
            )

        # ==================================================
        # EXTRACT SOLUTION
        # ==================================================
        assignments = []
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            for block in workday_blocks:
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    t_i = template_idx[template.id]
                    if (r_i, b_i, t_i) in x and solver.Value(x[r_i, b_i, t_i]) == 1:
                        assignments.append((
                            resident.id,
                            block.id,
                            template.id,
                        ))

        logger.info(f"CP-SAT found {len(assignments)} assignments in {runtime:.2f}s (status: {status_name})")

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
                "total_templates": len(context.templates),
                "coverage_rate": len(assignments) / len(workday_blocks) if workday_blocks else 0,
                "branches": solver.NumBranches(),
                "conflicts": solver.NumConflicts(),
            },
        )


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
        constraint_manager: Optional[ConstraintManager] = None,
        timeout_seconds: float = 120.0,
        pulp_timeout: float = 30.0,
        cpsat_timeout: float = 60.0,
    ):
        super().__init__(constraint_manager, timeout_seconds)
        self.pulp_timeout = pulp_timeout
        self.cpsat_timeout = cpsat_timeout

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] = None,
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
    """

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] = None,
    ) -> SolverResult:
        """Solve using greedy algorithm."""
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

        # Track existing assignments
        assigned_blocks = set()
        assignment_counts = {r.id: 0 for r in context.residents}
        template_block_counts = defaultdict(lambda: defaultdict(int))  # template_id -> block_id -> count

        if existing_assignments:
            for a in existing_assignments:
                assigned_blocks.add(a.block_id)
                if a.person_id in assignment_counts:
                    assignment_counts[a.person_id] += 1
                if a.rotation_template_id:
                    template_block_counts[a.rotation_template_id][a.block_id] += 1

        # Calculate difficulty (eligible resident count) for each block
        def count_eligible(block):
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

        # Assign residents
        assignments = []
        for block in sorted_blocks:
            # Find eligible residents
            eligible = [
                r for r in context.residents
                if self._is_available(r.id, block.id, context)
            ]

            if not eligible:
                continue  # No one available

            # Select resident with fewest assignments (equity)
            selected = min(eligible, key=lambda r: assignment_counts[r.id])

            # Select best available template
            template = None
            for t in context.templates:
                # Skip if requires procedure credential
                if t.requires_procedure_credential:
                    continue

                # Check capacity constraint
                if t.max_residents and template_block_counts[t.id][block.id] >= t.max_residents:
                    continue

                # Found a valid template
                template = t
                break

            if not template:
                # No valid template available, skip this block
                logger.debug(f"No valid rotation template for resident {selected.name} in block {block.id}")
                continue

            assignments.append((
                selected.id,
                block.id,
                template.id,
            ))
            assignment_counts[selected.id] += 1
            template_block_counts[template.id][block.id] += 1

        runtime = time.time() - start_time

        logger.info(f"Greedy found {len(assignments)} assignments in {runtime:.2f}s")

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
                "coverage_rate": len(assignments) / len(sorted_blocks) if sorted_blocks else 0,
            },
        )

    def _is_available(self, person_id: UUID, block_id: UUID, context: SchedulingContext) -> bool:
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
    """Factory for creating solvers by name."""

    _solvers = {
        "greedy": GreedySolver,
        "pulp": PuLPSolver,
        "cp_sat": CPSATSolver,
        "hybrid": HybridSolver,
    }

    @classmethod
    def create(
        cls,
        name: str,
        constraint_manager: Optional[ConstraintManager] = None,
        **kwargs,
    ) -> BaseSolver:
        """
        Create a solver by name.

        Args:
            name: Solver name ('greedy', 'pulp', 'cp_sat', 'hybrid')
            constraint_manager: Optional constraint manager
            **kwargs: Additional solver-specific arguments

        Returns:
            BaseSolver instance
        """
        if name not in cls._solvers:
            raise ValueError(f"Unknown solver: {name}. Available: {list(cls._solvers.keys())}")

        solver_class = cls._solvers[name]
        return solver_class(constraint_manager=constraint_manager, **kwargs)

    @classmethod
    def available_solvers(cls) -> list[str]:
        """Get list of available solver names."""
        return list(cls._solvers.keys())

    @classmethod
    def register(cls, name: str, solver_class: type):
        """Register a custom solver."""
        cls._solvers[name] = solver_class
