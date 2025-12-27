# Bio-Inspired Optimization for Multi-Objective Schedule Optimization

> **Far Realm Session 7**: Evolutionary and swarm-based optimization providing population-based search to complement QUBO's quantum approach.

## Overview

The bio-inspired optimization framework provides evolutionary and swarm-based algorithms for multi-objective schedule optimization. These algorithms excel at:

1. **Multi-objective Optimization**: Simultaneously optimizing multiple competing objectives
2. **Diverse Solution Discovery**: Finding a range of Pareto-optimal trade-offs
3. **Global Search**: Escaping local optima through population-based exploration
4. **Hybrid Integration**: Combining with QUBO quantum-inspired solvers

## The Evolutionary Lens

Bio-inspired algorithms view scheduling as an evolutionary process:

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVOLUTIONARY PERSPECTIVE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Chromosomes = Complete Schedules                               │
│  ┌─────┬─────┬─────┬─────┬─────┐                               │
│  │ R1  │  2  │  0  │  1  │  3  │  (Template assignments)       │
│  │ R2  │  1  │  2  │  2  │  0  │                               │
│  │ R3  │  3  │  1  │  0  │  1  │                               │
│  └─────┴─────┴─────┴─────┴─────┘                               │
│                                                                 │
│  Fitness = Multi-Objective Evaluation                           │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Coverage: 0.85  │ Fairness: 0.72  │ ACGME: 0.95        │    │
│  │ Preferences: 0.68 │ Learning: 0.74 │ Continuity: 0.61  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Selection Pressure → Better Solutions Survive                  │
│  Crossover → Combine Good Partial Solutions                     │
│  Mutation → Explore New Possibilities                           │
│  Diversity Maintenance → Avoid Premature Convergence            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why Bio-Inspired for Scheduling?

| Characteristic | Benefit for Scheduling |
|---------------|------------------------|
| Population-based | Explore multiple solutions simultaneously |
| Multi-objective | Balance fairness vs coverage vs compliance |
| Adaptive | Respond to changing constraints |
| Robust | Handle noisy evaluations and incomplete data |
| Parallel | Exploit multi-core architectures |

## Algorithms Implemented

### 1. Genetic Algorithm (GA)

The workhorse of evolutionary optimization, using genetic operators to evolve solutions.

```python
from app.scheduling.bio_inspired import GeneticAlgorithmSolver, GAConfig

config = GAConfig(
    population_size=100,
    max_generations=200,
    crossover_rate=0.8,
    mutation_rate=0.1,
    elite_size=5,
    adaptive_mutation=True,
)

solver = GeneticAlgorithmSolver(config=config, seed=42)
result = solver.solve(context)
```

**Key Features:**
- Multiple selection methods (tournament, roulette, rank)
- Multiple crossover operators (uniform, single/two-point, row/block-based)
- Multiple mutation operators (flip, swap, insert, delete, scramble)
- Adaptive mutation rates responding to search progress
- Niching for diversity maintenance

### 2. NSGA-II (Non-dominated Sorting GA)

The gold standard for multi-objective optimization, discovering Pareto-optimal trade-offs.

```python
from app.scheduling.bio_inspired import NSGA2Solver, NSGA2Config

config = NSGA2Config(
    population_size=100,
    max_generations=200,
)

solver = NSGA2Solver(
    config=config,
    objectives=["coverage", "fairness", "acgme_compliance"],
)
result = solver.solve(context)

# Get all Pareto-optimal solutions
pareto_solutions = solver.get_pareto_solutions()
```

**Key Features:**
- Fast non-dominated sorting O(MN²)
- Crowding distance for diversity preservation
- Elitist replacement combining parents and offspring
- No scalarization required - finds full Pareto front

### 3. Particle Swarm Optimization (PSO)

Swarm intelligence for continuous optimization of scheduling parameters.

```python
from app.scheduling.bio_inspired import ParticleSwarmSolver, PSOConfig

config = PSOConfig(
    swarm_size=50,
    max_iterations=200,
    topology=SwarmTopology.RING,
    inertia_weight=0.7,
    cognitive_coeff=1.5,
    social_coeff=1.5,
)

solver = ParticleSwarmSolver(config=config)
result = solver.solve(context)

# Get optimized objective weights
weights = solver.get_optimized_weights()
```

**Key Features:**
- Multiple topology options (global, ring, random, von Neumann)
- Adaptive inertia weight
- Optimizes objective weights for scalarization
- Constraint handling via penalty functions

### 4. Ant Colony Optimization (ACO)

Path finding optimization for rotation sequences.

```python
from app.scheduling.bio_inspired import AntColonySolver, ACOConfig

config = ACOConfig(
    colony_size=50,
    max_iterations=200,
    alpha=1.0,  # Pheromone importance
    beta=2.0,   # Heuristic importance
    evaporation_rate=0.1,
)

solver = AntColonySolver(config=config)
result = solver.solve(context)

# Analyze pheromone patterns
analysis = solver.get_pheromone_analysis()
```

**Key Features:**
- Pheromone-guided probabilistic construction
- Heuristic integration for constraint awareness
- Elite ant reinforcement
- Local search enhancement

### 5. Hybrid GA-QUBO

Evolutionary problem decomposition with quantum-inspired solving.

```python
from app.scheduling.bio_inspired import HybridGAQUBOSolver, HybridConfig

config = HybridConfig(
    population_size=50,
    n_subproblems=10,
    n_islands=4,
    enable_migration=True,
)

solver = HybridGAQUBOSolver(config=config)
result = solver.solve(context)
```

**Key Features:**
- GA evolves problem decompositions
- QUBO solves sub-problems with simulated annealing
- Island model with migration
- Combines evolutionary exploration with quantum-inspired optimization

## Multi-Objective Optimization

### The Six Objectives

```python
class FitnessVector:
    coverage: float        # Block assignment coverage (0-1)
    fairness: float        # Workload equity (0-1, higher=fairer)
    preferences: float     # Preference satisfaction (0-1)
    learning_goals: float  # Educational alignment (0-1)
    acgme_compliance: float # Regulatory compliance (0-1)
    continuity: float      # Rotation continuity (0-1)
```

### Pareto Dominance

A solution **dominates** another if it's at least as good in all objectives and strictly better in at least one.

```
Solution A: [0.9, 0.6, 0.7, 0.5, 0.95, 0.4]
Solution B: [0.8, 0.5, 0.6, 0.4, 0.90, 0.3]

A dominates B (better or equal in all, strictly better in all)
```

### Pareto Front

The Pareto front contains all non-dominated solutions - the set of optimal trade-offs.

```
       Fairness
          ↑
      1.0 │    ○
          │   ○ ○
      0.8 │  ○   ○      Pareto Front
          │ ○     ○
      0.6 │○       ○
          │         ○
      0.4 │          ○
          │
          └────────────→ Coverage
            0.4  0.6  0.8  1.0
```

## Visualization & Export

### Fitness Landscape Visualization

```python
from app.scheduling.bio_inspired import FitnessLandscapeVisualizer

visualizer = FitnessLandscapeVisualizer(resolution=50)
landscape_data = visualizer.generate_landscape(population_history)

# Returns:
# - 3D surface data for visualization
# - Peak locations (local optima)
# - Ruggedness metrics
```

### Evolution Tracking

```python
from app.scheduling.bio_inspired import EvolutionTracker

tracker = EvolutionTracker(sample_rate=5)

for generation in range(max_generations):
    # ... evolution step ...
    tracker.record_generation(generation, population, pareto_front)

animation_data = tracker.get_animation_data()
```

### JSON Export for Holographic Hub

```python
from app.scheduling.bio_inspired import (
    ParetoExporter,
    EvolutionExporter,
    HolographicExporter,
)

# Export Pareto front
pareto_exporter = ParetoExporter(algorithm_name="nsga2")
pareto_exporter.export_to_file(pareto_front, "pareto_front.json")

# Export evolution history
evolution_exporter = EvolutionExporter(algorithm_name="nsga2")
evolution_exporter.export_to_file(evolution_history, "evolution.json")

# Complete holographic hub export
holographic = HolographicExporter()
holographic.export_to_file(
    "holographic_data.json",
    evolution_history=evolution_history,
    pareto_front=pareto_front,
    population_snapshots=snapshots,
)
```

## Advanced Features

### Adaptive Mutation Rates

Mutation rates automatically adjust based on search progress:

```
Stagnation detected → Increase mutation rate (more exploration)
Good progress → Decrease mutation rate (more exploitation)
Low diversity → Increase mutation rate (prevent convergence)
```

### Island Model Migration

Parallel populations evolve independently with periodic migration:

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Island 1│────→│ Island 2│────→│ Island 3│────→│ Island 4│
│  BY_RES │     │ BY_WEEK │     │ ADAPTIVE│     │ ADAPTIVE│
└────↑────┘     └─────────┘     └─────────┘     └────│────┘
     │                                               │
     └───────────────────────────────────────────────┘
         Migration every 10 generations (ring topology)
```

### Niching for Diversity

Fitness sharing within niches encourages diverse solutions:

```python
# Solutions too similar share fitness penalty
if similarity(ind1, ind2) > (1 - niche_radius):
    ind1.fitness /= niche_count + 1
```

## Integration with QUBO

The hybrid pipeline uses evolutionary search to find optimal problem decompositions:

```
┌──────────────────────────────────────────────────────────────┐
│                    HYBRID GA-QUBO PIPELINE                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. GA Population of Decompositions                          │
│     ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│     │ By Res   │  │ By Week  │  │ Adaptive │                │
│     └────┬─────┘  └────┬─────┘  └────┬─────┘                │
│          │             │             │                       │
│  2. QUBO Solves Sub-Problems                                 │
│          ↓             ↓             ↓                       │
│     ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│     │  QUBO    │  │  QUBO    │  │  QUBO    │                │
│     │ Annealer │  │ Annealer │  │ Annealer │                │
│     └────┬─────┘  └────┬─────┘  └────┬─────┘                │
│          │             │             │                       │
│  3. Merge and Evaluate                                       │
│          └─────────────┼─────────────┘                       │
│                        ↓                                     │
│              ┌─────────────────┐                             │
│              │ Complete        │                             │
│              │ Schedule        │                             │
│              │ (Fitness Eval)  │                             │
│              └────────┬────────┘                             │
│                       ↓                                      │
│  4. Evolution Continues                                      │
│     - Selection based on fitness                             │
│     - Crossover of decomposition strategies                  │
│     - Mutation of partition boundaries                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Performance Considerations

### Computational Complexity

| Algorithm | Time per Generation | Space |
|-----------|---------------------|-------|
| GA | O(N × Fitness Eval) | O(N × Chromosome Size) |
| NSGA-II | O(MN²) (M=objectives, N=pop) | O(N × Chromosome Size) |
| PSO | O(N × Fitness Eval) | O(N × Dimension) |
| ACO | O(N × Graph Size) | O(Graph Size²) |
| Hybrid | O(N × QUBO Solves) | O(N × Decomposition) |

### Parallelization

All algorithms support parallel evaluation:

```python
# Island model inherently parallel
for island in islands:  # Can be parallelized
    evolve_island(island)

# Fitness evaluation can be parallelized
with ProcessPoolExecutor() as executor:
    fitnesses = executor.map(evaluate, population)
```

## Algorithm Selection Guide

| Scenario | Recommended Algorithm |
|----------|----------------------|
| Single-objective, fast | GA |
| Multi-objective trade-offs | NSGA-II |
| Parameter tuning | PSO |
| Rotation sequence optimization | ACO |
| Large problems with decomposition | Hybrid GA-QUBO |

## Module Structure

```
backend/app/scheduling/bio_inspired/
├── __init__.py           # Module exports
├── base.py               # Chromosome, FitnessVector, Individual, BioInspiredSolver
├── genetic_algorithm.py  # GA with operators and adaptive mutation
├── nsga2.py              # NSGA-II with crowding distance
├── particle_swarm.py     # PSO with topologies
├── ant_colony.py         # ACO with pheromone matrix
├── hybrid_quantum.py     # GA-QUBO hybrid pipeline
├── visualization.py      # Fitness landscape, evolution tracker
└── export.py             # JSON export for holographic hub
```

## Usage Example

```python
from app.scheduling.bio_inspired import (
    NSGA2Solver,
    NSGA2Config,
    ParetoExporter,
    EvolutionExporter,
)

# Configure solver
config = NSGA2Config(
    population_size=100,
    max_generations=200,
)

# Create solver with specific objectives
solver = NSGA2Solver(
    config=config,
    objectives=["coverage", "fairness", "acgme_compliance"],
    seed=42,
)

# Solve
result = solver.solve(context)

# Access Pareto front
for solution in solver.get_pareto_solutions():
    print(f"Solution {solution['id']}: {solution['fitness']}")

# Export for visualization
ParetoExporter().export_to_file(
    solver.pareto_front,
    "output/pareto_front.json",
)

EvolutionExporter().export_to_file(
    solver.evolution_history,
    "output/evolution.json",
    best_individual=solver.best_individual,
)
```

## Related Documentation

- [QUBO Quantum Solver](./quantum/qubo_solver.py) - Quantum-inspired optimization
- [Solver Algorithm Guide](./SOLVER_ALGORITHM.md) - Complete solver documentation
- [Constraint System](./constraints.py) - Constraint definitions
- [Mathematical Unification](./MATHEMATICAL_UNIFICATION.md) - Cross-domain synthesis
