# Multi-Objective Optimization Framework

> **Version:** 1.0
> **Last Updated:** 2025-12-27
> **Author:** Far Realm Session 8

## Executive Summary

The multi-objective optimization framework provides comprehensive support for decision-making when multiple competing goals cannot all be optimized simultaneously. It complements the existing NSGA-II implementation with MOEA/D and adds advanced constraint handling, preference articulation, and interactive decision support.

## The Multi-Objective Lens

### Why Multi-Objective Matters

Real-world scheduling problems have inherently conflicting goals:

| Objective | Conflict With | Trade-off |
|-----------|--------------|-----------|
| **Coverage** | Equity | Full coverage may require overloading some staff |
| **Preferences** | Compliance | Staff wishes may conflict with ACGME rules |
| **Efficiency** | Resilience | Lean staffing offers no buffer for emergencies |
| **Call Equity** | Convenience | Fair distribution may require inconvenient times |

**The Pareto Frontier**: Instead of finding a single "best" solution, we discover the set of solutions where improving one objective necessarily degrades another. This is the Pareto frontier (or Pareto front).

```
        Coverage
            ▲
            │     ●───●      ← Pareto Frontier
            │    ╱     ╲       (all trade-offs)
            │   ●       ●
            │  ╱         ╲
            │ ●           ●
            │╱             ╲
            └────────────────► Equity
                           (minimize)
```

Every point on the frontier represents a fundamentally different trade-off. Moving along the frontier means accepting costs in some objectives to gain in others.

### Decision Maker Role

The framework recognizes that **humans must make the final trade-off decisions**. Technology can:
- Compute the Pareto frontier efficiently
- Quantify trade-offs precisely
- Present options in understandable ways
- Support exploration and comparison

But only the decision maker can determine which trade-off is acceptable for their specific context.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   Multi-Objective Framework                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │   MOEA/D     │  │  Constraint  │  │  Preference           │ │
│  │  Algorithm   │  │  Handling    │  │  Articulation         │ │
│  │              │  │              │  │                       │ │
│  │ Decomposition│  │ Penalty      │  │ A Priori (Weights)    │ │
│  │ Subproblems  │  │ Repair       │  │ A Posteriori (Select) │ │
│  │ Neighborhoods│  │ Relaxation   │  │ Interactive           │ │
│  └──────────────┘  └──────────────┘  └───────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │  Quality     │  │  Diversity   │  │  Decision             │ │
│  │  Indicators  │  │  Preservation│  │  Support              │ │
│  │              │  │              │  │                       │ │
│  │ Hypervolume  │  │ Crowding     │  │ Trade-Off Analysis    │ │
│  │ IGD/GD       │  │ ε-Dominance  │  │ Navigation            │ │
│  │ Spread       │  │ Niching      │  │ Exploration           │ │
│  └──────────────┘  └──────────────┘  └───────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                Dynamic Reweighting                        │  │
│  │   Feedback → Context → Temporal → Weight Adjustment       │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               Holographic Export                          │  │
│  │   Pareto Visualization → Trade-Off Landscape → JSON       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. MOEA/D Algorithm (`moead.py`)

Multi-Objective Evolutionary Algorithm based on Decomposition. Complements NSGA-II with a different approach.

**Key Concepts:**
- **Weight Vectors**: Directions in objective space, each defining a subproblem
- **Decomposition**: Convert MOO to scalar optimization using scalarizing functions
- **Neighborhoods**: Subproblems share information with neighbors

**Decomposition Methods:**

| Method | Formula | Characteristics |
|--------|---------|-----------------|
| Weighted Sum | Σ(wᵢ × fᵢ) | Simple, cannot find non-convex regions |
| Tchebycheff | max(wᵢ × \|fᵢ - z*ᵢ\|) | Finds non-convex regions |
| PBI | d₁ + θ × d₂ | Balances convergence and diversity |

**Usage:**
```python
from app.multi_objective.moead import create_tchebycheff_moead

moead = create_tchebycheff_moead(
    objectives=scheduling_objectives,
    n_weight_vectors=100,
    max_generations=200
)

archive = moead.optimize(
    initial_solutions=seed_schedules,
    evaluate=evaluate_schedule,
    mutate=mutate_schedule,
    crossover=crossover_schedules
)
```

### 2. Constraint Handling (`constraints.py`)

Advanced techniques for handling constraints during optimization.

**Penalty Methods:**

| Method | Behavior | Use When |
|--------|----------|----------|
| Static | Fixed penalty coefficients | Simple problems |
| Dynamic | Penalty grows with generation | Need exploration early |
| Adaptive | Adjusts based on feasibility ratio | Uncertain constraint difficulty |
| Constraint Dominance | Feasible always beats infeasible | Strict compliance required |

**Repair Operators:**
- **Greedy Repair**: Fix violations one at a time, smallest first
- **Random Repair**: Stochastic perturbations to escape local optima

**Constraint Relaxation:**
- Gradually relax constraints when no feasible solution exists
- Restore constraints as search progresses
- Useful for emergency scheduling scenarios

```python
from app.multi_objective.constraints import (
    create_scheduling_constraint_handler,
    ConstraintRelaxer
)

handler = create_scheduling_constraint_handler()
handler.set_generation_info(current_gen, max_gen)

# Process solution with constraint handling
processed = handler.process_solution(solution, violations, context)
```

### 3. Preference Articulation (`preferences.py`)

Methods for incorporating decision maker preferences.

**A Priori (Before Optimization):**
- **Weighted Sum**: Specify importance weights for objectives
- **Reference Point**: Specify target values (aspirations)
- **Lexicographic**: Specify priority ordering

**A Posteriori (After Optimization):**
- Present entire Pareto front
- Decision maker selects from options

**Interactive (During Optimization):**
- Iterative refinement of preferences
- Feedback guides search direction
- NIMBUS-style classification

```python
from app.multi_objective.preferences import (
    PreferenceArticulator,
    ReferencePoint,
    InteractivePreferenceElicitor
)

# A Priori
articulator = PreferenceArticulator(objectives)
articulator.set_weights({"coverage": 0.5, "equity": 0.3, "resilience": 0.2})

# Interactive
elicitor = InteractivePreferenceElicitor(objectives)
representatives = elicitor.start_elicitation(frontier)
# ... collect user feedback ...
new_reps = elicitor.process_feedback("rating", {"ratings": {...}}, frontier)
```

### 4. Quality Indicators (`indicators.py`)

Metrics for evaluating Pareto front quality.

| Indicator | Measures | Direction |
|-----------|----------|-----------|
| Hypervolume | Dominated space volume | Higher is better |
| Generational Distance (GD) | Convergence to reference | Lower is better |
| Inverted GD (IGD) | Convergence + Coverage | Lower is better |
| Spread | Distribution uniformity | Lower is better |
| Spacing | Gap uniformity | Lower is better |
| Epsilon | Domination relationship | Lower is better |
| Maximum Spread | Extent of front | Higher is better |

```python
from app.multi_objective.indicators import QualityEvaluator

evaluator = QualityEvaluator()
report = evaluator.evaluate(frontier, reference_front)

print(f"Hypervolume: {report.hypervolume}")
print(f"IGD: {report.inverted_generational_distance}")
```

### 5. Decision Support (`decision_support.py`)

Interactive tools for navigating trade-offs.

**Trade-Off Analyzer:**
- Quantify trade-offs between objectives
- Calculate marginal rate of substitution
- Identify favorable trade-offs

**Solution Explorer:**
- Navigate the Pareto front
- Filter by objective bounds
- Bookmark and compare solutions

**Decision Maker Interface:**
- Unified access to all tools
- Track decision history
- Generate recommendations

```python
from app.multi_objective.decision_support import DecisionMaker

dm = DecisionMaker(frontier, objectives)

# Get overview
overview = dm.get_overview()

# Compare solutions
comparison = dm.compare_solutions(sol_a, sol_b)

# Record preference
dm.record_preference(sol_a, sol_b, preferred=0)

# Get recommendation
recommended, explanation = dm.get_recommendation()
```

### 6. Diversity Preservation (`diversity.py`)

Mechanisms to maintain solution diversity.

**Crowding Distance (NSGA-II):**
- Density estimate in objective space
- Boundary solutions get infinite distance
- Used for selection among equal-rank solutions

**Epsilon-Dominance:**
- Grid-based diversity
- One solution per grid cell
- Guaranteed minimum spacing

**Niching (Fitness Sharing):**
- Solutions in same niche share fitness
- Encourages exploration of sparse regions

**Reference Points (NSGA-III):**
- Associate solutions with reference directions
- Ensures coverage of entire front

```python
from app.multi_objective.diversity import DiversityMechanism, DiversityMetric

diversity = DiversityMechanism(
    objectives,
    primary_metric=DiversityMetric.CROWDING_DISTANCE
)

# Calculate diversity for population
diversity.calculate_diversity(population)

# Select with diversity consideration
selected = diversity.select(population, n=50)
```

### 7. Dynamic Reweighting (`reweighting.py`)

Adaptive objective weights based on context and feedback.

**Feedback-Based:**
- Learn from user ratings, comparisons, selections
- Infer implicit preferences

**Context-Aware:**
- Different weight profiles for contexts (normal, emergency, understaffed)
- Automatic context detection

**Temporal:**
- Schedule weight changes
- Phase-based optimization

```python
from app.multi_objective.reweighting import (
    DynamicReweighter,
    ContextType,
    FeedbackType
)

reweighter = DynamicReweighter(objectives)

# Set context
reweighter.set_context(ContextType.EMERGENCY)

# Process feedback
reweighter.process_feedback(
    FeedbackType.RATING,
    {"rating": 4, "objectives": solution.objective_values}
)

# Boost specific objective
reweighter.boost_objective("coverage", factor=1.5, duration=timedelta(hours=4))
```

### 8. Holographic Export (`export.py`)

JSON export for 3D visualization and decision support interfaces.

**Export Formats:**
- **Trade-Off Landscape**: Complete Pareto front with metadata
- **3D Visualization**: Point cloud ready for rendering
- **Decision Journey**: User exploration and selection history

```python
from app.multi_objective.export import (
    HolographicExporter,
    export_for_holographic_hub
)

# Quick export
exports = export_for_holographic_hub(frontier, objectives, decision_maker)

# Detailed export
exporter = HolographicExporter(objectives)
landscape_json = exporter.export_landscape(frontier, ExportFormat.FULL)
viz_json = exporter.export_visualization(frontier, "coverage", "equity", "resilience")
```

## Integration with Existing System

### Scheduling Engine

The multi-objective framework integrates with the existing scheduling engine:

```python
from app.scheduling.engine import SchedulingEngine
from app.multi_objective import MOEADAlgorithm, DecisionMaker

# Generate initial schedule with existing engine
engine = SchedulingEngine(constraints=ConstraintManager.create_default())
initial_schedule = engine.generate(context)

# Optimize with multi-objective
moead = create_tchebycheff_moead(SCHEDULING_OBJECTIVES)
archive = moead.optimize(
    initial_solutions=[initial_schedule],
    evaluate=engine.evaluate,
    mutate=engine.mutate,
    crossover=engine.crossover
)

# Decision support
dm = DecisionMaker(archive.get_frontier(), SCHEDULING_OBJECTIVES)
final_schedule, rationale = dm.get_recommendation()
```

### Existing Pareto Service

Complements `pareto_optimization_service.py`:

| Feature | Existing (NSGA-II) | New (MOEA/D) |
|---------|-------------------|--------------|
| Algorithm | Dominance-based | Decomposition-based |
| Scalability | Good for 2-3 objectives | Better for 4+ objectives |
| Distribution | May cluster | More uniform |
| Constraint Handling | Basic | Advanced (penalty, repair, relaxation) |
| Preferences | A posteriori | A priori, a posteriori, interactive |
| Decision Support | Ranking | Full navigation and analysis |

### Resilience Framework

Integrates with resilience objectives:

```python
RESILIENCE_OBJECTIVES = [
    ObjectiveConfig(
        name="hub_protection",
        display_name="Hub Protection",
        description="Protection of critical hub faculty",
        direction=ObjectiveDirection.MAXIMIZE,
        objective_type=ObjectiveType.HUB_PROTECTION,
        weight=0.7
    ),
    ObjectiveConfig(
        name="buffer_capacity",
        display_name="Buffer Capacity",
        description="Maintain 20% utilization buffer",
        direction=ObjectiveDirection.MAXIMIZE,
        objective_type=ObjectiveType.BUFFER_CAPACITY,
        weight=0.5
    ),
    # ...
]
```

## Usage Examples

### Example 1: Emergency Scheduling

```python
# Switch to emergency context
reweighter = DynamicReweighter(objectives)
reweighter.set_context(ContextType.EMERGENCY)

# Use constraint relaxation
handler = create_emergency_constraint_handler()

# Optimize with relaxed constraints
moead = MOEADAlgorithm(objectives, config)
archive = moead.optimize(...)

# Get coverage-prioritized solution
dm = DecisionMaker(archive.get_frontier(), objectives)
dm.preference_elicitor.record_selection(
    archive.get_solutions_by_objective("coverage", top_k=1)[0]
)
```

### Example 2: Interactive Preference Elicitation

```python
# Start interactive session
elicitor = InteractivePreferenceElicitor(objectives)
representatives = elicitor.start_elicitation(frontier)

# Present to user, collect feedback
user_ratings = get_user_ratings(representatives)

# Refine based on feedback
new_representatives = elicitor.process_feedback(
    "rating",
    {"ratings": user_ratings},
    frontier
)

# Repeat until satisfied
while not elicitor.state.is_complete:
    feedback = get_user_feedback(new_representatives)
    new_representatives = elicitor.process_feedback(
        feedback["type"],
        feedback["data"],
        frontier
    )
```

### Example 3: Quality Monitoring

```python
# Track optimization quality over generations
evaluator = QualityEvaluator()

for generation in range(max_generations):
    # Evolve population
    population = evolve(population)

    # Evaluate quality
    frontier = get_frontier(population)
    report = evaluator.evaluate(frontier, reference_front)

    # Log metrics
    log_metric("hypervolume", report.hypervolume, generation)
    log_metric("igd", report.inverted_generational_distance, generation)

    # Adjust based on quality
    if report.spread > 0.5:  # Poor distribution
        diversity.primary_metric = DiversityMetric.REFERENCE_POINT
```

## Best Practices

### 1. Objective Design

- **Normalization**: Always provide reference and nadir points
- **Independence**: Avoid highly correlated objectives
- **Measurability**: Objectives should be precisely calculable
- **Relevance**: Only include objectives that matter for decisions

### 2. Algorithm Selection

| Scenario | Recommended |
|----------|-------------|
| 2-3 objectives | NSGA-II or MOEA/D |
| 4+ objectives | MOEA/D with reference points |
| Many constraints | MOEA/D with adaptive penalty |
| Interactive | MOEA/D with preference articulation |

### 3. Constraint Handling

- Start with **static penalty** for simple problems
- Use **adaptive penalty** when constraint difficulty is unknown
- Enable **relaxation** for potentially infeasible problems
- Use **repair** when feasibility is critical

### 4. Decision Support

- Always start at the **knee** solution (balanced trade-off)
- Use **trade-off analysis** to understand costs
- **Bookmark** solutions for comparison
- **Record preferences** to improve recommendations

## Performance Considerations

| Component | Complexity | Notes |
|-----------|------------|-------|
| Dominance check | O(m × n²) | m=objectives, n=solutions |
| Crowding distance | O(m × n log n) | Per objective sort |
| Hypervolume (2D) | O(n log n) | Sweep algorithm |
| Hypervolume (>3D) | O(n^(m/2) log n) | Expensive, use sampling |
| MOEA/D generation | O(N × T × n) | N=subproblems, T=neighbors |

### Recommendations

- Limit population size to 100-200 for 2-3 objectives
- Use epsilon-dominance archiving for large fronts
- Sample hypervolume for >3 objectives
- Parallelize subproblem evolution in MOEA/D

## Testing

Run the comprehensive test suite:

```bash
cd backend
pytest tests/unit/test_multi_objective.py -v

# With coverage
pytest tests/unit/test_multi_objective.py --cov=app/multi_objective
```

## Future Enhancements

1. **Many-Objective Support**: NSGA-III reference point association
2. **Machine Learning Integration**: Learn preferences from historical data
3. **Robust Optimization**: Handle uncertainty in objectives
4. **Parallel MOEA/D**: Distribute subproblems across workers
5. **Visualization Dashboard**: Real-time Pareto front exploration

## References

1. Zhang, Q., & Li, H. (2007). MOEA/D: A multiobjective evolutionary algorithm based on decomposition.
2. Deb, K., et al. (2002). A fast and elitist multiobjective genetic algorithm: NSGA-II.
3. Miettinen, K. (1999). Nonlinear Multiobjective Optimization.
4. Zitzler, E., & Thiele, L. (1999). Multiobjective evolutionary algorithms: A comparative case study.
