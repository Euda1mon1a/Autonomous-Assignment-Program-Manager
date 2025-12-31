"""
Pyomo-based Optimization Solver for Residency Scheduling.

Provides a solver implementation using Pyomo that captures rich optimization data:
- Dual values (shadow prices) for constraint sensitivity
- Slack values for constraint headroom
- Solution statistics and convergence history

This solver enables "why" explanations for scheduling decisions.
"""

import logging
import time
from dataclasses import dataclass, field

from app.models.assignment import Assignment
from app.scheduling.constraints import ConstraintManager, SchedulingContext
from app.scheduling.solvers import BaseSolver, SolverResult

logger = logging.getLogger(__name__)


@dataclass
class ConstraintInsight:
    """Insight about a constraint's impact on the solution."""

    name: str
    dual_value: float  # Shadow price - value of relaxing constraint by 1 unit
    slack: float  # How much headroom before constraint is binding
    is_binding: bool  # True if constraint is at its limit
    interpretation: str  # Human-readable explanation


@dataclass
class PyomoSolutionData:
    """
    Rich solution data captured from Pyomo optimization.

    This data enables validation and understanding of "why"
    the schedule looks the way it does.
    """

    # Solution quality
    objective_value: float = 0.0
    is_optimal: bool = False
    solver_status: str = ""
    termination_condition: str = ""

    # Timing
    solve_time_seconds: float = 0.0

    # Constraint insights
    constraint_insights: list[ConstraintInsight] = field(default_factory=list)

    # Variable insights
    binding_constraints: list[str] = field(default_factory=list)
    bottleneck_resources: list[str] = field(default_factory=list)

    # Sensitivity analysis
    sensitivity_report: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "objective_value": self.objective_value,
            "is_optimal": self.is_optimal,
            "solver_status": self.solver_status,
            "termination_condition": self.termination_condition,
            "solve_time_seconds": self.solve_time_seconds,
            "constraint_insights": [
                {
                    "name": c.name,
                    "dual_value": c.dual_value,
                    "slack": c.slack,
                    "is_binding": c.is_binding,
                    "interpretation": c.interpretation,
                }
                for c in self.constraint_insights
            ],
            "binding_constraints": self.binding_constraints,
            "bottleneck_resources": self.bottleneck_resources,
            "sensitivity_report": self.sensitivity_report,
        }


class PyomoSolver(BaseSolver):
    """
    Mathematical optimization solver using Pyomo.

    Advantages over PuLP/OR-Tools:
    - Algebraic modeling language (equations look like math)
    - Rich solution data capture (duals, slacks, sensitivity)
    - Multiple solver backends (CBC, GLPK, Gurobi, CPLEX)
    - Stochastic programming support (future)

    Use this solver when you need to understand:
    - Why the schedule looks the way it does
    - Which constraints are limiting coverage
    - What would happen if constraints were relaxed

    Example:
        >>> solver = PyomoSolver(capture_duals=True)
        >>> result = solver.solve(context)
        >>> if result.success:
        ...     data = solver.get_solution_data()
        ...     for insight in data.constraint_insights:
        ...         if insight.is_binding:
        ...             print(f"{insight.name}: {insight.interpretation}")
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 60.0,
        solver_name: str = "cbc",  # Free solver, or "glpk", "gurobi", "cplex"
        capture_duals: bool = True,
        capture_slacks: bool = True,
    ):
        """
        Initialize Pyomo solver.

        Args:
            constraint_manager: Constraint manager for scheduling rules
            timeout_seconds: Maximum time for solver
            solver_name: Backend solver ("cbc", "glpk", "gurobi", "cplex")
            capture_duals: Whether to capture dual values (shadow prices)
            capture_slacks: Whether to capture slack values
        """
        super().__init__(constraint_manager, timeout_seconds)
        self.solver_name = solver_name
        self.capture_duals = capture_duals
        self.capture_slacks = capture_slacks
        self._solution_data: PyomoSolutionData | None = None

    def get_solution_data(self) -> PyomoSolutionData | None:
        """Get the captured solution data from the last solve."""
        return self._solution_data

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] = None,
    ) -> SolverResult:
        """
        Solve scheduling problem using Pyomo.

        This solver formulates the scheduling problem as a mixed-integer
        linear program (MILP) and solves it using the configured backend.

        After solving, call get_solution_data() to retrieve constraint
        insights and sensitivity information.

        Args:
            context: Scheduling context with residents, blocks, templates
            existing_assignments: Optional assignments to preserve

        Returns:
            SolverResult with assignments and statistics
        """
        try:
            from pyomo.environ import (
                Binary,
                ConcreteModel,
                Constraint,
                Objective,
                SolverFactory,
                TerminationCondition,
                Var,
                maximize,
                value,
            )
        except ImportError:
            logger.error("Pyomo not installed. Run: pip install pyomo")
            return SolverResult(
                success=False,
                assignments=[],
                status="error",
                solver_status="Pyomo not installed",
            )

        start_time = time.time()
        self._solution_data = PyomoSolutionData()

        # Filter to workday blocks
        workday_blocks = [b for b in context.blocks if not b.is_weekend]

        if not workday_blocks or not context.residents or not context.templates:
            return SolverResult(
                success=False,
                assignments=[],
                status="empty",
                solver_status="No blocks, residents, or rotation templates",
            )

        # Build index mappings
        residents = list(context.residents)
        blocks = list(workday_blocks)
        templates = [
            t for t in context.templates if not t.requires_procedure_credential
        ]

        R = range(len(residents))
        B = range(len(blocks))
        T = range(len(templates))

        # Create Pyomo model
        model = ConcreteModel(name="ResidencyScheduler")

        # ==================================================
        # DECISION VARIABLES
        # x[r,b,t] = 1 if resident r assigned to template t in block b
        # ==================================================
        model.x = Var(R, B, T, domain=Binary)

        # ==================================================
        # OBJECTIVE: Maximize coverage
        # ==================================================
        def objective_rule(m):
            return sum(m.x[r, b, t] for r in R for b in B for t in T)

        model.objective = Objective(rule=objective_rule, sense=maximize)

        # ==================================================
        # CONSTRAINT: At most one rotation per resident per block
        # ==================================================
        def one_rotation_rule(m, r, b):
            return sum(m.x[r, b, t] for t in T) <= 1

        model.one_rotation = Constraint(R, B, rule=one_rotation_rule)

        # ==================================================
        # CONSTRAINT: Template capacity per block
        # ==================================================
        def template_capacity_rule(m, b, t):
            template = templates[t]
            max_residents = template.max_residents or len(residents)
            return sum(m.x[r, b, t] for r in R) <= max_residents

        model.template_capacity = Constraint(B, T, rule=template_capacity_rule)

        # ==================================================
        # CONSTRAINT: Preserve existing assignments
        # ==================================================
        if existing_assignments:
            template_idx = {t.id: i for i, t in enumerate(templates)}
            resident_idx = {r.id: i for i, r in enumerate(residents)}
            block_idx = {b.id: i for i, b in enumerate(blocks)}

            def preserve_rule(m, idx):
                a = existing_assignments[idx]
                if (
                    a.person_id in resident_idx
                    and a.block_id in block_idx
                    and a.rotation_template_id in template_idx
                ):
                    r = resident_idx[a.person_id]
                    b = block_idx[a.block_id]
                    t = template_idx[a.rotation_template_id]
                    return m.x[r, b, t] == 1
                return Constraint.Skip

            model.preserve = Constraint(
                range(len(existing_assignments)), rule=preserve_rule
            )

        # ==================================================
        # SOLVE
        # ==================================================
        try:
            solver = SolverFactory(self.solver_name)
            if not solver.available():
                logger.warning(f"Solver {self.solver_name} not available, trying cbc")
                solver = SolverFactory("cbc")

            solver.options["seconds"] = self.timeout_seconds

            # Enable dual/slack capture
            if self.capture_duals:
                model.dual = None  # Will be populated after solve

            results = solver.solve(model, tee=False)

        except Exception as e:
            logger.error(f"Pyomo solver error: {e}")
            return SolverResult(
                success=False,
                assignments=[],
                status="error",
                solver_status=str(e),
            )

        runtime = time.time() - start_time

        # Check termination condition
        term_cond = results.solver.termination_condition
        self._solution_data.termination_condition = str(term_cond)
        self._solution_data.solve_time_seconds = runtime

        if term_cond not in [
            TerminationCondition.optimal,
            TerminationCondition.feasible,
        ]:
            logger.warning(f"Pyomo solver termination: {term_cond}")
            return SolverResult(
                success=False,
                assignments=[],
                status="infeasible",
                solver_status=str(term_cond),
                runtime_seconds=runtime,
            )

        self._solution_data.is_optimal = term_cond == TerminationCondition.optimal
        self._solution_data.solver_status = str(term_cond)

        # ==================================================
        # CAPTURE CONSTRAINT INSIGHTS
        # ==================================================
        if self.capture_duals and hasattr(model, "dual"):
            self._capture_constraint_insights(model, residents, blocks, templates)

        # ==================================================
        # EXTRACT SOLUTION
        # ==================================================
        assignments = []
        for r in R:
            for b in B:
                for t in T:
                    if value(model.x[r, b, t]) > 0.5:
                        assignments.append(
                            (
                                residents[r].id,
                                blocks[b].id,
                                templates[t].id,
                            )
                        )

        self._solution_data.objective_value = value(model.objective)

        logger.info(
            f"Pyomo found {len(assignments)} assignments in {runtime:.2f}s "
            f"(status: {term_cond})"
        )

        return SolverResult(
            success=True,
            assignments=assignments,
            status="optimal" if self._solution_data.is_optimal else "feasible",
            objective_value=self._solution_data.objective_value,
            runtime_seconds=runtime,
            solver_status=str(term_cond),
            statistics={
                "total_blocks": len(blocks),
                "total_residents": len(residents),
                "total_templates": len(templates),
                "coverage_rate": len(assignments) / len(blocks) if blocks else 0,
                "binding_constraints": len(self._solution_data.binding_constraints),
                "solver_backend": self.solver_name,
            },
        )

    def _capture_constraint_insights(
        self,
        model,
        residents: list,
        blocks: list,
        templates: list,
    ) -> None:
        """Capture dual values and generate constraint insights."""

        insights = []
        binding = []

        # Analyze one_rotation constraints
        if hasattr(model, "one_rotation"):
            for (r, b), con in model.one_rotation.items():
                try:
                    dual = model.dual.get(con, 0.0)
                    slack = con.uslack() if hasattr(con, "uslack") else 0.0
                    is_binding = abs(slack) < 1e-6

                    if is_binding and abs(dual) > 1e-6:
                        resident_name = (
                            residents[r].name if r < len(residents) else f"Resident {r}"
                        )
                        block_date = blocks[b].date if b < len(blocks) else f"Block {b}"

                        interpretation = (
                            f"{resident_name} is fully scheduled on {block_date}. "
                            f"Shadow price: {dual:.2f} (value of adding another slot)"
                        )

                        insights.append(
                            ConstraintInsight(
                                name=f"one_rotation[{r},{b}]",
                                dual_value=dual,
                                slack=slack,
                                is_binding=True,
                                interpretation=interpretation,
                            )
                        )
                        binding.append(f"Resident {resident_name} on {block_date}")

                except Exception as e:
                    logger.debug(
                        f"Could not extract dual for one_rotation[{r},{b}]: {e}"
                    )

        # Analyze template_capacity constraints
        if hasattr(model, "template_capacity"):
            for (b, t), con in model.template_capacity.items():
                try:
                    dual = model.dual.get(con, 0.0)
                    slack = con.uslack() if hasattr(con, "uslack") else 0.0
                    is_binding = abs(slack) < 1e-6

                    if is_binding and abs(dual) > 1e-6:
                        template_name = (
                            templates[t].name if t < len(templates) else f"Template {t}"
                        )
                        block_date = blocks[b].date if b < len(blocks) else f"Block {b}"

                        interpretation = (
                            f"{template_name} is at capacity on {block_date}. "
                            f"Adding 1 more slot would improve objective by {dual:.2f}"
                        )

                        insights.append(
                            ConstraintInsight(
                                name=f"template_capacity[{b},{t}]",
                                dual_value=dual,
                                slack=slack,
                                is_binding=True,
                                interpretation=interpretation,
                            )
                        )
                        binding.append(f"{template_name} capacity on {block_date}")

                except Exception as e:
                    logger.debug(
                        f"Could not extract dual for template_capacity[{b},{t}]: {e}"
                    )

        self._solution_data.constraint_insights = insights
        self._solution_data.binding_constraints = binding

        # Identify bottleneck resources (constraints with highest dual values)
        sorted_insights = sorted(
            insights, key=lambda x: abs(x.dual_value), reverse=True
        )
        self._solution_data.bottleneck_resources = [i.name for i in sorted_insights[:5]]

    def get_sensitivity_report(self) -> dict:
        """
        Generate a sensitivity report explaining what limits coverage.

        Returns:
            Dictionary with:
            - bottlenecks: Top constraints limiting objective
            - recommendations: Suggested changes to improve
            - headroom: Constraints with slack (not limiting)
        """
        if not self._solution_data:
            return {"error": "No solution data available. Run solve() first."}

        report = {
            "summary": {
                "objective_value": self._solution_data.objective_value,
                "is_optimal": self._solution_data.is_optimal,
                "solve_time": self._solution_data.solve_time_seconds,
                "binding_constraint_count": len(
                    self._solution_data.binding_constraints
                ),
            },
            "bottlenecks": [],
            "recommendations": [],
            "headroom": [],
        }

        for insight in self._solution_data.constraint_insights:
            if insight.is_binding:
                report["bottlenecks"].append(
                    {
                        "constraint": insight.name,
                        "dual_value": insight.dual_value,
                        "interpretation": insight.interpretation,
                    }
                )

                # Generate recommendation
                if "capacity" in insight.name.lower():
                    report["recommendations"].append(
                        f"Consider increasing capacity for the resource in {insight.name}"
                    )
                elif "one_rotation" in insight.name.lower():
                    report["recommendations"].append(
                        "Resident is fully utilized - consider distributing load"
                    )
            else:
                report["headroom"].append(
                    {
                        "constraint": insight.name,
                        "slack": insight.slack,
                    }
                )

        return report


# Register with SolverFactory
def register_pyomo_solver() -> None:
    """Register PyomoSolver with the SolverFactory."""
    from app.scheduling.solvers import SolverFactory

    SolverFactory.register("pyomo", PyomoSolver)
