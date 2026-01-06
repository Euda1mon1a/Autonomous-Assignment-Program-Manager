"""
QUBO Template Optimization API Routes.

Provides endpoints for quantum-inspired rotation template selection:
- On-demand QUBO optimization
- Pareto front exploration
- Energy landscape visualization
- Benchmark comparisons
- Quantum advantage documentation
"""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.user import User
from app.scheduling.constraints import SchedulingContext
from app.scheduling.quantum.qubo_solver import get_quantum_library_status
from app.scheduling.quantum.qubo_template_selector import (
    EnergyLandscapeExplorer,
    HybridTemplatePipeline,
    ParetoFrontExplorer,
    QUBOTemplateFormulation,
    QUBOTemplateSolver,
    TemplateBenchmark,
    TemplateDesirability,
    TemplateSelectionConfig,
    get_template_selector_status,
)
from app.schemas.qubo_templates import (
    AssignmentSchema,
    BenchmarkComparisonSchema,
    BenchmarkResultSchema,
    EnergyLandscapePointSchema,
    EnergyLandscapeSchema,
    ParetoSolutionSchema,
    QuantumAdvantageDocResponse,
    QuantumAdvantageScenario,
    QUBOStatisticsSchema,
    QUBOStatusResponse,
    QUBOTemplateOptimizeRequest,
    QUBOTemplateOptimizeResponse,
    TemplateDesirabilityLevel,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Helper Functions
# ============================================================================


def build_scheduling_context(
    db: Session,
    start_date: date,
    end_date: date,
    person_ids: list | None = None,
    template_ids: list | None = None,
) -> SchedulingContext:
    """
    Build a scheduling context from database entities.

    Args:
        db: Database session
        start_date: Schedule start date
        end_date: Schedule end date
        person_ids: Optional filter for specific persons
        template_ids: Optional filter for specific templates

    Returns:
        SchedulingContext populated with relevant data
    """
    # Query blocks
    blocks_query = db.query(Block).filter(
        Block.date >= start_date,
        Block.date <= end_date,
    )
    blocks = blocks_query.all()

    # Query residents
    residents_query = db.query(Person).filter(Person.role == "RESIDENT")
    if person_ids:
        residents_query = residents_query.filter(Person.id.in_(person_ids))
    residents = residents_query.all()

    # Query faculty
    faculty_query = db.query(Person).filter(Person.role == "FACULTY")
    faculty = faculty_query.all()

    # Query templates
    templates_query = db.query(RotationTemplate)
    if template_ids:
        templates_query = templates_query.filter(RotationTemplate.id.in_(template_ids))
    templates = templates_query.all()

    # Build context
    context = SchedulingContext(
        blocks=blocks,
        residents=residents,
        faculty=faculty,
        templates=templates,
        availability={},
        existing_assignments=[],
    )

    return context


def convert_desirability_mappings(
    mappings: list | None,
) -> dict[str, TemplateDesirability]:
    """Convert schema desirability mappings to internal format."""
    if not mappings:
        return {}

    result = {}
    for mapping in mappings:
        if mapping.desirability == TemplateDesirabilityLevel.HIGHLY_DESIRABLE:
            result[mapping.template_name] = TemplateDesirability.HIGHLY_DESIRABLE
        elif mapping.desirability == TemplateDesirabilityLevel.UNDESIRABLE:
            result[mapping.template_name] = TemplateDesirability.UNDESIRABLE
        else:
            result[mapping.template_name] = TemplateDesirability.NEUTRAL

    return result


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/optimize", response_model=QUBOTemplateOptimizeResponse)
async def optimize_template_selection(
    request: QUBOTemplateOptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Optimize rotation template selection using QUBO.

    This endpoint uses Quadratic Unconstrained Binary Optimization (QUBO)
    to find optimal template assignments that balance:
    - Coverage: Assign templates to all available slots
    - Fairness: Distribute desirable/undesirable rotations equally
    - Preferences: Satisfy resident preferences when possible
    - Learning goals: Provide rotation variety for education

    The optimization uses a hybrid classical-quantum pipeline:
    1. QUBO formulation with adaptive temperature annealing
    2. Classical gradient descent refinement
    3. Constraint repair for feasibility

    Optionally includes:
    - Pareto front exploration for multi-objective trade-offs
    - Energy landscape visualization data
    - Benchmark comparisons against classical approaches

    Requires authentication and schedule management permissions.
    """
    # Check permissions
    if not current_user.can_manage_schedules:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to optimize schedules",
        )

    try:
        # Build scheduling context from database
        context = build_scheduling_context(
            db=db,
            start_date=request.start_date,
            end_date=request.end_date,
            person_ids=request.person_ids,
            template_ids=request.template_ids,
        )

        if not context.residents:
            raise HTTPException(
                status_code=400,
                detail="No residents found for the specified criteria",
            )

        if not context.templates:
            raise HTTPException(
                status_code=400,
                detail="No templates found for the specified criteria",
            )

        if not context.blocks:
            raise HTTPException(
                status_code=400,
                detail="No blocks found in the date range",
            )

        logger.info(
            f"QUBO optimization: {len(context.residents)} residents, "
            f"{len(context.blocks)} blocks, {len(context.templates)} templates"
        )

        # Build configuration
        config = TemplateSelectionConfig(
            coverage_weight=request.objective_weights.coverage,
            fairness_weight=request.objective_weights.fairness,
            preference_weight=request.objective_weights.preference,
            learning_goal_weight=request.objective_weights.learning,
            num_reads=request.annealing_config.num_reads,
            num_sweeps=request.annealing_config.num_sweeps,
            beta_start=request.annealing_config.beta_start,
            beta_end=request.annealing_config.beta_end,
            use_adaptive_temperature=request.annealing_config.use_adaptive_temperature,
            pareto_population=request.pareto_config.population_size,
            pareto_generations=request.pareto_config.generations,
            seed=request.seed,
        )

        # Convert desirability mappings
        desirability_map = convert_desirability_mappings(request.desirability_mappings)

        # Run optimization
        solver = QUBOTemplateSolver(config=config)
        result = solver.solve_with_full_result(context)

        # Build response
        assignments = [
            AssignmentSchema(
                person_id=a[0],
                block_id=a[1],
                template_id=a[2],
            )
            for a in result.assignments
        ]

        # Pareto frontier
        pareto_frontier = [
            ParetoSolutionSchema(
                solution_id=sol.solution_id,
                objectives=sol.objectives,
                rank=sol.rank,
                crowding_distance=sol.crowding_distance,
                num_assignments=len(sol.assignments),
            )
            for sol in result.pareto_frontier
        ]

        # Energy landscape
        energy_landscape = None
        if request.include_energy_landscape and result.energy_landscape:
            points = [
                EnergyLandscapePointSchema(
                    energy=p.energy,
                    is_local_minimum=p.is_local_minimum,
                    tunneling_probability=p.tunneling_probability,
                    basin_size=p.basin_size,
                    objectives=p.objectives,
                )
                for p in result.energy_landscape[:100]
            ]
            minima = [p for p in points if p.is_local_minimum]

            energy_landscape = EnergyLandscapeSchema(
                num_samples=len(result.energy_landscape),
                num_local_minima=len(minima),
                global_minimum_energy=min(p.energy for p in result.energy_landscape)
                if result.energy_landscape
                else 0,
                energy_range={
                    "min": min(p.energy for p in result.energy_landscape)
                    if result.energy_landscape
                    else 0,
                    "max": max(p.energy for p in result.energy_landscape)
                    if result.energy_landscape
                    else 0,
                },
                points=points,
                minima=minima[:20],
            )

        # Benchmarks
        benchmarks = None
        if request.include_benchmarks:
            benchmark = TemplateBenchmark(context)
            bench_results = benchmark.run_benchmark()

            benchmarks = BenchmarkComparisonSchema(
                qubo=BenchmarkResultSchema(
                    approach="qubo",
                    success=bench_results["qubo"]["success"],
                    num_assignments=bench_results["qubo"]["num_assignments"],
                    runtime_seconds=bench_results["qubo"]["runtime_seconds"],
                    objective_value=bench_results["qubo"].get("objective_value"),
                ),
                greedy=BenchmarkResultSchema(
                    approach="greedy",
                    success=bench_results["greedy"]["success"],
                    num_assignments=bench_results["greedy"]["num_assignments"],
                    runtime_seconds=bench_results["greedy"]["runtime_seconds"],
                    objective_value=None,
                ),
                random=BenchmarkResultSchema(
                    approach="random",
                    success=bench_results["random"]["success"],
                    num_assignments=bench_results["random"]["num_assignments"],
                    runtime_seconds=bench_results["random"]["runtime_seconds"],
                    objective_value=None,
                ),
                qubo_vs_greedy_improvement=bench_results["comparison"][
                    "qubo_vs_greedy_improvement"
                ],
                qubo_vs_random_improvement=bench_results["comparison"][
                    "qubo_vs_random_improvement"
                ],
            )

        # Statistics
        stats = result.statistics
        statistics = QUBOStatisticsSchema(
            num_variables=stats.get("num_variables", 0),
            num_qubo_terms=stats.get("num_qubo_terms", 0),
            qubo_energy=stats.get("qubo_energy", 0),
            refined_energy=stats.get("refined_energy", 0),
            final_energy=stats.get("final_energy", 0),
            improvement=stats.get("improvement", 0),
            num_assignments=stats.get("num_assignments", len(assignments)),
            objectives=stats.get("objectives", {}),
            pareto_frontier_size=stats.get("pareto_frontier_size", 0),
            num_local_minima=stats.get("num_local_minima", 0),
        )

        # Quantum advantage estimate
        quantum_advantage = None
        if benchmarks:
            greedy_time = benchmarks.greedy.runtime_seconds
            qubo_improvement = benchmarks.qubo_vs_greedy_improvement
            if greedy_time > 0 and qubo_improvement > 0:
                # Simple heuristic: advantage = quality_improvement / time_overhead
                time_ratio = benchmarks.qubo.runtime_seconds / greedy_time
                quantum_advantage = (1 + qubo_improvement / 100) / max(time_ratio, 0.1)

        return QUBOTemplateOptimizeResponse(
            success=result.success,
            message=f"Optimized {len(assignments)} assignments with QUBO template selection",
            assignments=assignments,
            statistics=statistics,
            pareto_frontier=pareto_frontier,
            recommended_solution_id=result.recommended_solution_id,
            energy_landscape=energy_landscape,
            benchmarks=benchmarks,
            runtime_seconds=result.runtime_seconds,
            quantum_advantage_estimate=quantum_advantage,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("QUBO optimization failed")
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {str(e)}",
        )


@router.get("/status", response_model=QUBOStatusResponse)
async def get_qubo_status(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get status of QUBO template selector.

    Returns information about:
    - Whether QUBO solver is available
    - Available features (Pareto, adaptive temperature, etc.)
    - Recommended problem sizes
    - Quantum library availability

    Useful for clients to determine capability before optimization.
    """
    selector_status = get_template_selector_status()
    library_status = get_quantum_library_status()

    return QUBOStatusResponse(
        available=selector_status["qubo_template_selector_available"],
        features=selector_status["features"],
        recommended_problem_size=selector_status["recommended_problem_size"],
        quantum_libraries=library_status,
    )


@router.get("/quantum-advantage", response_model=QuantumAdvantageDocResponse)
async def get_quantum_advantage_documentation(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get documentation on quantum advantage scenarios.

    Returns detailed information about:
    - When QUBO outperforms classical approaches
    - Problem characteristics that enable advantage
    - Current limitations and recommendations

    This endpoint documents the theoretical and practical aspects
    of quantum advantage in residency scheduling optimization.
    """
    return QuantumAdvantageDocResponse(
        overview="""
QUBO (Quadratic Unconstrained Binary Optimization) formulation enables quantum-inspired
and quantum-native optimization of residency scheduling. The template selection problem
maps naturally to QUBO because:

1. Binary decisions: Each (resident, period, template) combination is a yes/no decision
2. Quadratic interactions: Fairness and conflict constraints create pairwise interactions
3. Optimization landscape: Multiple local minima benefit from quantum tunneling

The 780-variable sweet spot (approximately 15 residents × 26 periods × 2 templates)
represents the regime where:
- Classical solvers struggle with exponential search space
- Quantum annealers can embed the full problem
- Simulated quantum annealing shows measurable speedup
        """.strip(),
        scenarios=[
            QuantumAdvantageScenario(
                scenario_name="Large-Scale Fairness Optimization",
                description="""
When optimizing for equitable distribution of desirable and undesirable rotations
across many residents, the problem develops a frustrated energy landscape with
many local minima. Quantum tunneling can escape these minima more efficiently
than classical simulated annealing.
                """.strip(),
                problem_characteristics=[
                    "15+ residents with competing preferences",
                    "Multiple desirability categories (3+ levels)",
                    "Tight capacity constraints on popular rotations",
                    "Historical fairness debt requiring rebalancing",
                ],
                expected_speedup="2-5x over greedy, 1.5-3x over classical SA",
                conditions=[
                    "Problem size 500-2000 variables",
                    "High constraint density (>50% of variables interact)",
                    "Multiple competing objectives",
                ],
            ),
            QuantumAdvantageScenario(
                scenario_name="Multi-Objective Pareto Exploration",
                description="""
Finding the full Pareto frontier for 3+ objectives requires exploring many
trade-off solutions. Quantum-inspired approaches can sample the frontier
more uniformly due to natural exploration of the energy landscape.
                """.strip(),
                problem_characteristics=[
                    "3+ conflicting objectives",
                    "Need for diverse solution set",
                    "Decision-maker prefers options over single solution",
                    "Trade-offs are non-obvious without exploration",
                ],
                expected_speedup="5-20x for Pareto frontier quality (hypervolume)",
                conditions=[
                    "Sufficient time budget (>60 seconds)",
                    "Clear objective definitions",
                    "Willingness to explore trade-offs",
                ],
            ),
            QuantumAdvantageScenario(
                scenario_name="Highly Constrained Scheduling",
                description="""
When many hard constraints create narrow feasibility corridors in the solution
space, quantum tunneling can find feasible solutions where classical methods
get stuck in infeasible regions.
                """.strip(),
                problem_characteristics=[
                    "High constraint satisfaction ratio (>80% of constraints active)",
                    "Many overlapping capacity limits",
                    "Complex availability patterns (military TDY, medical leave)",
                    "ACGME rules creating interdependencies",
                ],
                expected_speedup="10-100x for finding any feasible solution",
                conditions=[
                    "Classical solvers frequently report 'infeasible'",
                    "Solution space is fragmented",
                    "Constraints are non-trivially satisfiable",
                ],
            ),
            QuantumAdvantageScenario(
                scenario_name="Incremental Re-optimization",
                description="""
When a small change (new absence, swap request) requires re-optimizing a
previously optimal schedule, warm-starting from the previous solution
combined with quantum tunneling finds better adjustments faster.
                """.strip(),
                problem_characteristics=[
                    "Existing near-optimal schedule",
                    "Single or few changes to constraints",
                    "Need to minimize disruption",
                    "Time pressure for quick response",
                ],
                expected_speedup="3-10x for maintaining solution quality",
                conditions=[
                    "Previous solution available for warm start",
                    "Change affects <10% of variables",
                    "Quality threshold defined",
                ],
            ),
        ],
        current_limitations=[
            "Simulated quantum annealing provides polynomial, not exponential, speedup",
            "Actual quantum hardware (D-Wave) limited to ~5000 variables after embedding",
            "Quantum coherence times limit annealing duration on real hardware",
            "Classical pre/post-processing still required for constraint handling",
            "Problem formulation overhead can dominate for small instances",
            "Stochastic nature means results vary between runs",
        ],
        recommendations=[
            "Use QUBO for problems with 500-5000 binary variables",
            "Enable adaptive temperature for problems with many local minima",
            "Use Pareto exploration when trade-offs between objectives matter",
            "Benchmark against greedy for your specific problem structure",
            "Consider hybrid approach: QUBO for exploration, classical for refinement",
            "Set realistic expectations: 2-10x speedup, not exponential",
            "Monitor energy landscape to understand problem difficulty",
        ],
    )


@router.post("/explore-landscape")
async def explore_energy_landscape(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    sample_count: int = Query(
        default=200, ge=50, le=1000, description="Number of samples"
    ),
    seed: int | None = Query(default=None, description="Random seed"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Explore the QUBO energy landscape for visualization.

    This endpoint samples the energy landscape to identify:
    - Local minima and their basin sizes
    - Tunneling probabilities between minima
    - Energy distribution and ruggedness

    Useful for understanding problem difficulty and tuning optimization parameters.
    """
    if not current_user.can_manage_schedules:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions",
        )

    try:
        context = build_scheduling_context(db, start_date, end_date)

        if not context.residents or not context.templates or not context.blocks:
            raise HTTPException(
                status_code=400,
                detail="Insufficient data for landscape exploration",
            )

        formulation = QUBOTemplateFormulation(context)
        formulation.build()

        explorer = EnergyLandscapeExplorer(
            formulation,
            sample_count=sample_count,
            seed=seed,
        )
        points = explorer.explore()

        return explorer.export_for_visualization()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Landscape exploration failed")
        raise HTTPException(
            status_code=500,
            detail=f"Exploration failed: {str(e)}",
        )


@router.post("/explore-pareto")
async def explore_pareto_frontier(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    objectives: list[str] = Query(
        default=["coverage", "fairness", "preference"],
        description="Objectives to optimize",
    ),
    population_size: int = Query(default=50, ge=10, le=200),
    generations: int = Query(default=50, ge=10, le=200),
    seed: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Explore the Pareto frontier for multi-objective optimization.

    Returns the set of non-dominated solutions that represent optimal
    trade-offs between the specified objectives.

    Useful for decision-making when multiple objectives conflict.
    """
    if not current_user.can_manage_schedules:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions",
        )

    try:
        context = build_scheduling_context(db, start_date, end_date)

        if not context.residents or not context.templates or not context.blocks:
            raise HTTPException(
                status_code=400,
                detail="Insufficient data for Pareto exploration",
            )

        formulation = QUBOTemplateFormulation(context)
        formulation.build()

        explorer = ParetoFrontExplorer(
            formulation,
            objectives=objectives,
            population_size=population_size,
            generations=generations,
            seed=seed,
        )
        frontier = explorer.explore()

        return explorer.export_for_visualization()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Pareto exploration failed")
        raise HTTPException(
            status_code=500,
            detail=f"Exploration failed: {str(e)}",
        )


@router.post("/benchmark")
async def run_benchmark(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Run benchmark comparison of QUBO vs classical approaches.

    Compares:
    - QUBO template selector
    - Greedy assignment
    - Random assignment

    Returns timing and quality metrics for each approach.
    """
    if not current_user.can_manage_schedules:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions",
        )

    try:
        context = build_scheduling_context(db, start_date, end_date)

        if not context.residents or not context.templates or not context.blocks:
            raise HTTPException(
                status_code=400,
                detail="Insufficient data for benchmark",
            )

        benchmark = TemplateBenchmark(context)
        results = benchmark.run_benchmark()

        return {
            "results": results,
            "context": {
                "num_residents": len(context.residents),
                "num_blocks": len(context.blocks),
                "num_templates": len(context.templates),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Benchmark failed")
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark failed: {str(e)}",
        )
