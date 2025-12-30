***REMOVED*** Spin Glass Constraint Model

***REMOVED******REMOVED*** Overview

The **Spin Glass Constraint Model** treats residency scheduling as a frustrated magnetic system from statistical physics. This approach provides powerful tools for understanding constraint conflicts, generating diverse solutions, and analyzing the structure of the scheduling problem space.

***REMOVED******REMOVED*** Physics Background

***REMOVED******REMOVED******REMOVED*** What is a Spin Glass?

In physics, a **spin glass** is a disordered magnetic system where competing interactions between spins prevent the system from settling into a single global optimum. Instead, the system has many "frustrated" configurations with similar energies.

**Key Properties:**
- **Frustration**: Conflicting interactions that cannot all be satisfied
- **Replica Symmetry Breaking (RSB)**: Multiple degenerate ground states
- **Energy Landscape**: Complex terrain with multiple local minima
- **Glass Transition**: Point where system "freezes" into rigid configuration

***REMOVED******REMOVED******REMOVED*** Scheduling Analogy

| Physics Concept | Scheduling Equivalent |
|----------------|----------------------|
| Spin | Assignment (person, block, rotation) |
| Magnetic interaction | Constraint between assignments |
| Energy | Total constraint violations |
| Frustration | Conflicting constraints |
| Replica | Alternative near-optimal schedule |
| Glass transition | Loss of scheduling flexibility |

***REMOVED******REMOVED*** Implementation

***REMOVED******REMOVED******REMOVED*** Core Components

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. `SpinGlassScheduler`

Main class for spin glass-based scheduling analysis.

```python
from app.scheduling import SpinGlassScheduler

scheduler = SpinGlassScheduler(
    context=scheduling_context,
    constraints=constraint_list,
    temperature=1.0,  ***REMOVED*** Controls diversity
    random_seed=42,   ***REMOVED*** For reproducibility
)
```

**Key Methods:**

- `compute_frustration_index()` → `float`
  - Measures degree of constraint conflict (0.0-1.0)
  - High frustration indicates incompatible requirements

- `generate_replica_schedules(n_replicas=10)` → `list[ReplicaSchedule]`
  - Creates ensemble of near-optimal solutions
  - Each replica is a different valid schedule

- `compute_parisi_overlap(schedule_a, schedule_b)` → `float`
  - Measures similarity between two schedules (0.0-1.0)
  - Used to detect replica symmetry breaking

- `find_glass_transition_threshold()` → `float`
  - Identifies critical point where flexibility vanishes
  - Helps predict constraint capacity limits

- `analyze_energy_landscape(replicas)` → `LandscapeAnalysis`
  - Maps solution space structure
  - Identifies basins, barriers, and frustration clusters

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Data Classes

**`FrustrationCluster`**
```python
@dataclass
class FrustrationCluster:
    constraints: list[str]           ***REMOVED*** Conflicting constraints
    frustration_index: float         ***REMOVED*** Conflict intensity (0-1)
    affected_persons: set[UUID]      ***REMOVED*** Impacted people
    affected_blocks: set[UUID]       ***REMOVED*** Impacted blocks
    conflict_type: str               ***REMOVED*** Category of conflict
    resolution_suggestions: list[str] ***REMOVED*** How to reduce frustration
```

**`ReplicaSchedule`**
```python
@dataclass
class ReplicaSchedule:
    schedule_id: str                           ***REMOVED*** Unique identifier
    assignments: list[tuple[UUID, UUID, UUID]] ***REMOVED*** (person, block, template)
    energy: float                              ***REMOVED*** Total violations
    magnetization: float                       ***REMOVED*** Soft constraint alignment
    replica_index: int                         ***REMOVED*** Index in ensemble
    constraint_violations: dict[str, float]    ***REMOVED*** Breakdown by type
```

**`LandscapeAnalysis`**
```python
@dataclass
class LandscapeAnalysis:
    global_minimum_energy: float               ***REMOVED*** Best energy found
    local_minima: list[float]                  ***REMOVED*** Energy of each basin
    energy_barrier_heights: list[float]        ***REMOVED*** Gaps between basins
    basin_sizes: dict[int, int]                ***REMOVED*** Replicas per basin
    frustration_clusters: list[FrustrationCluster]
    glass_transition_temp: float               ***REMOVED*** Freezing temperature
```

**`ReplicaSymmetryAnalysis`**
```python
@dataclass
class ReplicaSymmetryAnalysis:
    parisi_overlap_matrix: np.ndarray      ***REMOVED*** n×n similarity matrix
    rsb_order_parameter: float             ***REMOVED*** Symmetry breaking degree (0-1)
    diversity_score: float                 ***REMOVED*** Solution variety (0-1)
    ultrametric_distance: dict             ***REMOVED*** Hierarchical structure
    mean_overlap: float                    ***REMOVED*** Average similarity
    overlap_distribution: dict[str, int]   ***REMOVED*** Histogram of overlaps
```

***REMOVED******REMOVED******REMOVED*** 3. Visualization Tools

Located in `spin_glass_visualizer.py`:

```python
from app.scheduling import (
    plot_energy_landscape,
    plot_parisi_overlap_matrix,
    plot_overlap_distribution,
    plot_frustration_network,
    plot_solution_basins,
    export_landscape_summary,
)

***REMOVED*** Generate visualizations
plot_energy_landscape(replicas, landscape, "energy.png")
plot_parisi_overlap_matrix(rsb_analysis, "overlap.png")
export_landscape_summary(replicas, landscape, rsb, "summary.json")
```

**Available Plots:**
- Energy landscape scatter plot
- Parisi overlap heatmap
- Overlap distribution histogram
- Constraint frustration network
- Solution basin 2D projection

***REMOVED******REMOVED*** Usage Guide

***REMOVED******REMOVED******REMOVED*** Basic Workflow

```python
from app.scheduling import (
    SpinGlassScheduler,
    SchedulingContext,
    ConstraintManager,
)

***REMOVED*** 1. Set up scheduler
constraint_manager = ConstraintManager.create_default()
constraints = constraint_manager.get_enabled_constraints()

scheduler = SpinGlassScheduler(
    context=scheduling_context,
    constraints=constraints,
    temperature=1.0,
    random_seed=42,
)

***REMOVED*** 2. Analyze frustration
frustration = scheduler.compute_frustration_index()
print(f"Frustration: {frustration:.3f}")

***REMOVED*** 3. Generate replicas
replicas = scheduler.generate_replica_schedules(n_replicas=20)

***REMOVED*** 4. Analyze landscape
landscape = scheduler.analyze_energy_landscape(replicas)
rsb = scheduler.compute_replica_symmetry_analysis(replicas)

***REMOVED*** 5. Interpret results
if frustration > 0.7:
    print("⚠ Highly frustrated - constraints conflict significantly")

if rsb.diversity_score > 0.7:
    print("✓ High diversity - many viable solutions")
else:
    print("⚠ Low diversity - schedule may be brittle")
```

***REMOVED******REMOVED******REMOVED*** Use Cases

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. **Constraint Conflict Detection**

Identify which constraints are preventing optimal solutions:

```python
frustration = scheduler.compute_frustration_index()
landscape = scheduler.analyze_energy_landscape(replicas)

for cluster in landscape.frustration_clusters:
    print(f"Conflict: {cluster.conflict_type}")
    print(f"  Constraints: {cluster.constraints}")
    print(f"  Suggestions: {cluster.resolution_suggestions}")
```

**Example Output:**
```
Conflict: equity_vs_preference
  Constraints: ['WorkloadEquity', 'FacultyPreference']
  Suggestions: ['Reduce weight of WorkloadEquity', 'Relax preference requirements']
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. **Contingency Planning**

Generate multiple valid schedules for backup:

```python
replicas = scheduler.generate_replica_schedules(n_replicas=10)

***REMOVED*** Sort by different criteria
by_energy = sorted(replicas, key=lambda r: r.energy)
by_preferences = sorted(replicas, key=lambda r: -r.magnetization)

print("Primary schedule (min violations):", by_energy[0].schedule_id)
print("Backup schedule (max preferences):", by_preferences[0].schedule_id)

***REMOVED*** Check diversity
overlap = scheduler.compute_parisi_overlap(by_energy[0], by_preferences[0])
if overlap < 0.5:
    print("Backups are sufficiently diverse")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. **Flexibility Analysis**

Determine if system can handle additional constraints:

```python
critical_density = scheduler.find_glass_transition_threshold()

current_density = len(constraints) / len(blocks)

if current_density > critical_density * 0.9:
    print("⚠ Approaching glass transition - adding constraints risky")
else:
    print("✓ System has flexibility for additional constraints")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. **Trade-off Exploration**

Understand trade-offs between competing objectives:

```python
replicas = scheduler.generate_replica_schedules(n_replicas=50)

***REMOVED*** Pareto front analysis
pareto_front = []
for replica in replicas:
    violations = replica.constraint_violations
    equity_cost = violations.get('equity', 0)
    preference_cost = violations.get('preference', 0)

    ***REMOVED*** Check if Pareto-optimal
    is_dominated = any(
        r.constraint_violations.get('equity', 0) < equity_cost and
        r.constraint_violations.get('preference', 0) < preference_cost
        for r in replicas
    )

    if not is_dominated:
        pareto_front.append(replica)

print(f"Found {len(pareto_front)} Pareto-optimal schedules")
```

***REMOVED******REMOVED*** Interpretation Guide

***REMOVED******REMOVED******REMOVED*** Frustration Index

| Range | Interpretation | Action |
|-------|---------------|--------|
| 0.0 - 0.3 | Low frustration - constraints compatible | Safe to proceed |
| 0.3 - 0.6 | Moderate frustration - some conflicts | Monitor closely |
| 0.6 - 0.8 | High frustration - significant conflicts | Consider constraint relaxation |
| 0.8 - 1.0 | Extreme frustration - constraints incompatible | Major revision needed |

***REMOVED******REMOVED******REMOVED*** Diversity Score

| Range | Interpretation | Robustness |
|-------|---------------|------------|
| 0.7 - 1.0 | High diversity - many solutions | Excellent - robust to changes |
| 0.4 - 0.7 | Moderate diversity - some variety | Good - reasonable flexibility |
| 0.2 - 0.4 | Low diversity - few solutions | Poor - brittle schedule |
| 0.0 - 0.2 | Minimal diversity - nearly unique solution | Critical - very fragile |

***REMOVED******REMOVED******REMOVED*** Combined Analysis

| Frustration | Diversity | Situation | Recommendation |
|------------|-----------|-----------|----------------|
| Low | High | **Ideal** | Multiple good solutions available |
| Low | Low | **Optimal but Brittle** | Single dominant solution, monitor changes |
| High | High | **Conflicted** | Many solutions but all flawed, relax constraints |
| High | Low | **Critical** | Few solutions and all problematic, major revision |

***REMOVED******REMOVED*** Integration with Existing Solvers

The spin glass model complements existing solvers:

```python
***REMOVED*** Step 1: Use CP-SAT to find initial solution
from app.scheduling.solvers import SolverFactory

solver = SolverFactory.create_solver("cp_sat", constraint_manager)
base_result = solver.solve(context)

***REMOVED*** Step 2: Use spin glass to generate alternatives
scheduler = SpinGlassScheduler(context, constraints, temperature=1.0)
replicas = scheduler.generate_replica_schedules(
    n_replicas=10,
    base_solver_result=base_result,
)

***REMOVED*** Step 3: Analyze diversity
rsb = scheduler.compute_replica_symmetry_analysis(replicas)

if rsb.diversity_score < 0.3:
    logger.warning("Low diversity detected - schedule may be rigid")

***REMOVED*** Step 4: Select best replica based on secondary criteria
best_replica = max(replicas, key=lambda r: r.magnetization)
return best_replica.assignments
```

***REMOVED******REMOVED*** Performance Considerations

***REMOVED******REMOVED******REMOVED*** Computational Complexity

- **Frustration Index**: O(C²) where C = number of constraints
- **Replica Generation**: O(N × B × R × T) where:
  - N = replicas
  - B = blocks
  - R = residents
  - T = annealing steps (default 100)
- **Overlap Computation**: O(N² × A) where A = assignments per schedule
- **Landscape Analysis**: O(N² + N × C)

***REMOVED******REMOVED******REMOVED*** Scaling Guidelines

| Problem Size | Recommended Replicas | Expected Runtime |
|-------------|---------------------|------------------|
| Small (<100 blocks) | 20-50 | < 1 minute |
| Medium (100-500 blocks) | 10-20 | 1-5 minutes |
| Large (>500 blocks) | 5-10 | 5-15 minutes |

***REMOVED******REMOVED******REMOVED*** Optimization Tips

1. **Temperature Tuning**: Start with T=1.0, increase for more diversity
2. **Replica Count**: Use fewer replicas for initial analysis, more for production
3. **Caching**: Interaction matrix is cached - reuse scheduler instance
4. **Parallel Generation**: Replicas are independent - can be generated in parallel

***REMOVED******REMOVED*** Testing

Comprehensive test suite in `tests/scheduling/test_spin_glass.py`:

```bash
***REMOVED*** Run all tests
pytest tests/scheduling/test_spin_glass.py -v

***REMOVED*** Run specific test class
pytest tests/scheduling/test_spin_glass.py::TestFrustrationIndex -v

***REMOVED*** Run with coverage
pytest tests/scheduling/test_spin_glass.py --cov=app.scheduling.spin_glass_model
```

**Test Coverage:**
- ✓ Scheduler initialization and reproducibility
- ✓ Frustration index computation
- ✓ Replica generation and diversity
- ✓ Parisi overlap calculation
- ✓ Glass transition detection
- ✓ Energy landscape analysis
- ✓ RSB analysis
- ✓ Integration workflows

***REMOVED******REMOVED*** References

***REMOVED******REMOVED******REMOVED*** Physics Literature

1. **Mézard, M., Parisi, G., & Virasoro, M. A.** (1987). *Spin glass theory and beyond*. World Scientific.
   - Comprehensive treatment of spin glass theory and RSB

2. **Sherrington, D., & Kirkpatrick, S.** (1975). "Solvable model of a spin-glass". *Physical Review Letters*, 35(26), 1792.
   - Original spin glass model (SK model)

3. **Parisi, G.** (1979). "Infinite number of order parameters for spin-glasses". *Physical Review Letters*, 43(23), 1754.
   - Introduction of replica symmetry breaking

***REMOVED******REMOVED******REMOVED*** Computational Applications

4. **Kirkpatrick, S., Gelatt, C. D., & Vecchi, M. P.** (1983). "Optimization by simulated annealing". *Science*, 220(4598), 671-680.
   - Simulated annealing algorithm

5. **Monasson, R., et al.** (1999). "Determining computational complexity from characteristic 'phase transitions'". *Nature*, 400(6740), 133-137.
   - Phase transitions in constraint satisfaction

***REMOVED******REMOVED*** File Structure

```
backend/app/scheduling/
├── spin_glass_model.py          ***REMOVED*** Core implementation (34 KB)
│   ├── SpinGlassScheduler       ***REMOVED*** Main scheduler class
│   ├── FrustrationCluster       ***REMOVED*** Constraint conflict data
│   ├── ReplicaSchedule          ***REMOVED*** Single replica data
│   ├── LandscapeAnalysis        ***REMOVED*** Energy landscape results
│   └── ReplicaSymmetryAnalysis  ***REMOVED*** RSB characterization
│
├── spin_glass_visualizer.py     ***REMOVED*** Visualization tools (16 KB)
│   ├── plot_energy_landscape()
│   ├── plot_parisi_overlap_matrix()
│   ├── plot_overlap_distribution()
│   ├── plot_frustration_network()
│   ├── plot_solution_basins()
│   └── export_landscape_summary()
│
├── spin_glass_example.py        ***REMOVED*** Usage examples (11 KB)
│   ├── demonstrate_spin_glass_scheduling()
│   ├── find_glass_transition_example()
│   └── compare_replicas_example()
│
└── SPIN_GLASS_README.md         ***REMOVED*** This file

backend/tests/scheduling/
└── test_spin_glass.py           ***REMOVED*** Test suite (25 KB)
    ├── TestSpinGlassSchedulerInit
    ├── TestFrustrationIndex
    ├── TestReplicaGeneration
    ├── TestParisiOverlap
    ├── TestGlassTransition
    ├── TestEnergyLandscape
    ├── TestRSBAnalysis
    └── TestSpinGlassIntegration
```

***REMOVED******REMOVED*** Future Enhancements

***REMOVED******REMOVED******REMOVED*** Planned Features

1. **Parallel Replica Generation**
   - Use multiprocessing for faster replica ensemble creation
   - Estimate: 5-10× speedup for large problems

2. **Adaptive Temperature Scheduling**
   - Automatically tune temperature based on constraint density
   - Use parallel tempering for better sampling

3. **Constraint Clustering**
   - Automatically group related constraints
   - Identify independent subsystems for decomposition

4. **Real-time Frustration Monitoring**
   - Track frustration during interactive schedule building
   - Alert user when adding constraint increases frustration

5. **Machine Learning Integration**
   - Learn constraint interaction patterns from historical data
   - Predict glass transition point without expensive sampling

***REMOVED******REMOVED******REMOVED*** Research Directions

- **Cavity Method**: Advanced RSB analysis using cavity equations
- **Message Passing**: Distributed constraint satisfaction via belief propagation
- **Quantum Annealing**: Integration with D-Wave quantum hardware
- **Hierarchical RSB**: Multi-level replica structure (Parisi full RSB)

***REMOVED******REMOVED*** License

This implementation is part of the Autonomous Assignment Program Manager
residency scheduling system. See main project LICENSE file.

***REMOVED******REMOVED*** Contact

For questions, issues, or contributions related to the Spin Glass model:
- Open an issue on the project repository
- Tag with `physics-inspired` and `scheduling` labels
- See CONTRIBUTING.md for development guidelines

---

**Version**: 1.0.0
**Last Updated**: 2025-12-29
**Authors**: Developed for medical residency scheduling optimization
