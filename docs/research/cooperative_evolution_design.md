# Cooperative Evolution for Schedule Optimization

> **Status:** Research Draft
> **Date:** 2026-01-15
> **Purpose:** Theoretical foundation for cooperative cell selection in residency scheduling

---

## Executive Summary

Traditional genetic algorithms treat each schedule cell as an independent unit competing for survival. This document proposes a **cooperative evolution** model where cells are scored not just by individual fitness, but by their contribution to neighboring cells and overall schedule patterns. The key insight: **cells that enable others outcompete selfish cells over generations**.

---

## 1. Core Game Theory Mechanics

### 1.1 The Cooperative Fitness Function

Standard fitness considers only local validity. Cooperative fitness adds two dimensions:

```
TOTAL_FITNESS = BASE_SCORE + NEIGHBOR_UPLIFT + PATTERN_COMPLETION
```

| Component | What It Measures | Example |
|-----------|------------------|---------|
| Base Score | Individual cell validity | "This cell assigns R2 to Night Float" |
| Neighbor Uplift | How much this cell improves adjacent cells | "R2 here means R3 next door has backup" |
| Pattern Completion | Whether this cell completes a recognized pattern | "This completes 5-day AT coverage chain" |

### 1.2 Neighbor Uplift Calculation

```python
def calculate_neighbor_uplift(cell, grid):
    """
    Score contribution to neighboring cells.

    A cell "uplifts" neighbors when:
    - It provides coverage they lack (temporal adjacency)
    - It provides supervision they need (role complementarity)
    - It provides backup if they fail (resilience)
    """
    uplift = 0

    for neighbor in grid.get_adjacent(cell):
        # Temporal: Does this cell extend neighbor's coverage?
        if cell.covers_gap_before(neighbor) or cell.covers_gap_after(neighbor):
            uplift += COVERAGE_CHAIN_BONUS  # e.g., +50

        # Role: Does this cell complement neighbor's role?
        if cell.provides_supervision_for(neighbor):
            uplift += SUPERVISION_PAIR_BONUS  # e.g., +30

        # Resilience: Does this cell protect neighbor post-call?
            if cell.provides_recovery_for(neighbor):
            uplift += RECOVERY_PARTNER_BONUS  # e.g., +20

    return uplift
```

### 1.3 Pattern Completion Rewards

Recognized patterns that yield completion bonuses:

| Pattern | Description | Bonus |
|---------|-------------|-------|
| **Coverage Chain** | 5+ consecutive half-days with same rotation | +100 |
| **Teaching Pair** | Senior (R3/Faculty) + Junior (R1/R2) same session | +50 |
| **Post-Call Shield** | Light assignment following call shift | +40 |
| **Balanced Week** | Resident has variety without fragmentation | +30 |
| **Supervision Ratio** | Maintains required attending:resident ratio | +60 |

```python
def pattern_completion_score(cell, grid):
    """
    Check if placing this cell completes any recognized patterns.
    Returns sum of all pattern bonuses.
    """
    score = 0

    # Check each pattern type
    if completes_coverage_chain(cell, grid):
        score += COVERAGE_CHAIN_PATTERN

    if completes_teaching_pair(cell, grid):
        score += TEACHING_PAIR_PATTERN

    if creates_post_call_shield(cell, grid):
        score += POST_CALL_SHIELD_PATTERN

    # ... additional patterns

    return score
```

---

## 2. Coalition Detection

### 2.1 Graph Representation with NetworkX

The schedule grid maps naturally to a graph where:
- **Nodes** = Cells (row, column, assignment)
- **Edges** = Cooperative relationships between cells
- **Edge Weights** = Strength of cooperation

```python
import networkx as nx

def build_cooperation_graph(grid):
    """
    Build a graph where edges represent cooperative relationships.
    """
    G = nx.Graph()

    for cell in grid.all_cells():
        G.add_node(cell.id, **cell.attributes())

    # Add edges for cooperative relationships
    for cell_a, cell_b in grid.all_pairs():
        coop_score = measure_cooperation(cell_a, cell_b)
        if coop_score > COOPERATION_THRESHOLD:
            G.add_edge(cell_a.id, cell_b.id, weight=coop_score)

    return G
```

### 2.2 Identifying Natural Partnerships

NetworkX provides algorithms to detect coalition structures:

```python
def detect_coalitions(G):
    """
    Find natural groupings of cooperating cells.
    """
    # Option 1: Community detection (Louvain)
    communities = nx.community.louvain_communities(G)

    # Option 2: Clique detection (fully connected subgroups)
    cliques = list(nx.find_cliques(G))

    # Option 3: K-core decomposition (highly connected regions)
    k_cores = nx.k_core(G, k=3)  # Cells with 3+ cooperative neighbors

    return {
        'communities': communities,
        'cliques': cliques,
        'dense_regions': k_cores
    }
```

### 2.3 Simplified Shapley Scoring

Full Shapley value computation is O(2^n) - intractable for large grids. We use approximations:

```python
def approximate_shapley(cell, coalition, samples=100):
    """
    Monte Carlo approximation of Shapley value.

    Shapley value = average marginal contribution across
    all possible orderings of coalition members.
    """
    marginal_contributions = []

    for _ in range(samples):
        # Random ordering of coalition members
        ordering = random.shuffle(coalition.members)

        # Find where this cell appears in ordering
        cell_position = ordering.index(cell)

        # Coalition before this cell joined
        predecessor_coalition = ordering[:cell_position]

        # Marginal contribution = value with cell - value without
        value_with = coalition_score(predecessor_coalition + [cell])
        value_without = coalition_score(predecessor_coalition)

        marginal_contributions.append(value_with - value_without)

    return mean(marginal_contributions)
```

**Practical Shortcut: Neighbor-Based Approximation**

For real-time fitness evaluation, use local neighborhood only:

```python
def local_shapley(cell, grid, radius=2):
    """
    Approximate Shapley using only nearby cells.
    Much faster: O(radius^2) instead of O(2^n).
    """
    neighborhood = grid.get_cells_within(cell, radius)

    # Score grid with and without this cell
    with_cell = neighborhood_score(neighborhood)
    without_cell = neighborhood_score(neighborhood - {cell})

    return with_cell - without_cell
```

---

## 3. Selection Pressure

### 3.1 The Darwinian Twist

Standard GA selection: **cells with highest individual fitness survive**.

Cooperative selection: **cells that improve coalition fitness survive**.

```python
def cooperative_selection(population, grid, tournament_size=3):
    """
    Selection that rewards cooperation over selfishness.

    Key insight: A cell with mediocre individual score but high
    neighbor uplift beats a high-scoring loner.
    """
    selected = []

    for _ in range(len(population) // 2):
        # Tournament selection
        candidates = random.sample(population, tournament_size)

        # Score includes cooperative contribution
        scored = [
            (cell, cooperative_fitness(cell, grid))
            for cell in candidates
        ]

        # Winner has highest cooperative fitness
        winner = max(scored, key=lambda x: x[1])[0]
        selected.append(winner)

    return selected
```

### 3.2 Coalition-Level Selection

Instead of selecting individual cells, select **pairs or groups**:

```python
def pair_selection(population, grid):
    """
    Select cell pairs that work well together.

    This preserves cooperative relationships through generations.
    """
    # Build cooperation graph
    G = build_cooperation_graph(grid)

    # Find strongly cooperative pairs
    pairs = [
        (u, v, data['weight'])
        for u, v, data in G.edges(data=True)
        if data['weight'] > HIGH_COOPERATION_THRESHOLD
    ]

    # Sort by combined fitness + cooperation bonus
    pairs.sort(key=lambda p: combined_pair_score(p, grid), reverse=True)

    # Select top pairs - both members survive together
    selected_pairs = pairs[:len(pairs) // 2]

    return flatten(selected_pairs)
```

### 3.3 Why Cooperators Win

**Generation 1:** Random mix of selfish and cooperative cells.

**Generation N:** Cooperative cells cluster. Their coalition scores compound:
- Cell A helps Cell B (+30 uplift)
- Cell B helps Cell C (+30 uplift)
- Cell C helps Cell A (+30 uplift)
- Each cell gets +60 total uplift from cooperation

**Selfish cells** only get base scores. Over generations, cooperative clusters dominate through pure selection pressure - no explicit "cooperation rule" needed.

```
SELFISH CELL:    base=80, uplift=0,  total=80
COOPERATIVE CELL: base=70, uplift=60, total=130
                                      ^^^^^^^^
                                      Cooperation wins
```

---

## 4. Integration Points

### 4.1 Existing bio_inspired/ Architecture

Current modules in `backend/app/scheduling/bio_inspired/`:

| Module | Purpose | Integration Point |
|--------|---------|-------------------|
| `genetic_algorithm.py` | Standard GA | Replace `fitness()` with `cooperative_fitness()` |
| `nsga2.py` | Multi-objective | Add cooperation as objective |
| `particle_swarm.py` | PSO optimizer | Swarm = coalition, not individuals |
| `ant_colony.py` | ACO pathfinding | Pheromone = cooperation signal |
| `base.py` | Base optimizer class | Extend with coalition tracking |

### 4.2 Proposed Module Structure

```
backend/app/scheduling/
├── bio_inspired/           # Existing
│   ├── genetic_algorithm.py
│   ├── nsga2.py
│   └── ...
│
└── cooperative_evolution/  # New
    ├── __init__.py
    ├── fitness.py          # cooperative_fitness(), neighbor_uplift()
    ├── coalitions.py       # NetworkX graph building, community detection
    ├── shapley.py          # Approximate Shapley values
    ├── selection.py        # pair_selection(), coalition_selection()
    └── integration.py      # Hooks into existing GA
```

### 4.3 Integration Code

```python
# integration.py - Hook cooperative fitness into existing GA

from ..bio_inspired.genetic_algorithm import GeneticScheduleOptimizer
from .fitness import cooperative_fitness
from .coalitions import build_cooperation_graph
from .selection import pair_selection

class CooperativeGeneticOptimizer(GeneticScheduleOptimizer):
    """
    Extends standard GA with cooperative selection.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cooperation_graph = None

    def fitness(self, individual, grid):
        """Override: use cooperative fitness instead of individual."""
        return cooperative_fitness(individual, grid)

    def select(self, population, grid):
        """Override: use pair selection instead of individual."""
        # Rebuild cooperation graph each generation
        self.cooperation_graph = build_cooperation_graph(grid)
        return pair_selection(population, grid)

    def evolve_generation(self, population, grid):
        """
        One generation of cooperative evolution.
        """
        # Update cooperation graph
        self.cooperation_graph = build_cooperation_graph(grid)

        # Log coalition statistics
        coalitions = detect_coalitions(self.cooperation_graph)
        self.log_coalition_stats(coalitions)

        # Standard GA operations with cooperative fitness
        return super().evolve_generation(population, grid)
```

### 4.4 Configuration Interface

```python
# Example configuration
COOPERATIVE_EVOLUTION_CONFIG = {
    # Fitness weights
    'base_weight': 1.0,
    'uplift_weight': 0.5,
    'pattern_weight': 0.3,

    # Coalition detection
    'cooperation_threshold': 0.3,
    'shapley_samples': 50,
    'neighborhood_radius': 2,

    # Selection
    'pair_selection_ratio': 0.7,  # 70% pair, 30% individual
    'tournament_size': 3,

    # Pattern bonuses
    'coverage_chain_bonus': 100,
    'teaching_pair_bonus': 50,
    'recovery_partner_bonus': 40,
}
```

---

## 5. Emergent Behavior

### 5.1 Expected Progression

```
┌─────────────────────────────────────────────────────────────────┐
│ Generation 1: Random Soup                                       │
│ ┌───┬───┬───┬───┬───┐                                          │
│ │ S │ C │ S │ S │ C │   S = Selfish (high base, no uplift)     │
│ ├───┼───┼───┼───┼───┤   C = Cooperative (helps neighbors)      │
│ │ S │ S │ C │ S │ S │                                          │
│ ├───┼───┼───┼───┼───┤   Distribution: ~50% S, ~50% C            │
│ │ C │ S │ S │ C │ S │   Average fitness: ~80                    │
│ └───┴───┴───┴───┴───┘                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Generation 10: Clustering Emerges                               │
│ ┌───┬───┬───┬───┬───┐                                          │
│ │ C │ C │ S │ C │ C │   Cooperators cluster together            │
│ ├───┼───┼───┼───┼───┤   Cluster members get uplift bonuses     │
│ │ C │ C │ S │ C │ C │                                          │
│ ├───┼───┼───┼───┼───┤   Distribution: ~30% S, ~70% C            │
│ │ S │ S │ S │ C │ C │   Average fitness: ~95                    │
│ └───┴───┴───┴───┴───┘                                          │
│       ▲           ▲                                             │
│       │           └── Cooperative cluster (high fitness)        │
│       └── Selfish island (outcompeted)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Generation 50: Cooperative Dominance                            │
│ ┌───┬───┬───┬───┬───┐                                          │
│ │ C │ C │ C │ C │ C │   Cooperators dominate                    │
│ ├───┼───┼───┼───┼───┤   Selfish cells eliminated or converted  │
│ │ C │ C │ C │ C │ C │                                          │
│ ├───┼───┼───┼───┼───┤   Distribution: ~95% C, ~5% S             │
│ │ C │ C │ C │ C │ C │   Average fitness: ~120                   │
│ └───┴───┴───┴───┴───┘                                          │
│                                                                 │
│ The grid now exhibits emergent patterns:                        │
│ - Coverage chains across rows                                   │
│ - Teaching pairs in columns                                     │
│ - Recovery shields after call blocks                            │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Observable Metrics

Track these metrics across generations to observe emergence:

| Metric | Early Generations | Late Generations |
|--------|-------------------|------------------|
| **Average Coalition Size** | 1-2 cells | 5+ cells |
| **Graph Density** | Sparse (0.1-0.2) | Dense (0.5-0.7) |
| **Pattern Completion Rate** | 10-20% | 80-90% |
| **Variance in Fitness** | High (cells very different) | Low (all cooperative) |
| **Selfish Cell Ratio** | ~50% | <5% |

### 5.3 Emergent Patterns

What we expect to see "evolve" without explicit rules:

**Coverage Chains:**
```
Without cooperation rules:     With cooperation pressure:
┌───┬───┬───┬───┬───┐         ┌───┬───┬───┬───┬───┐
│ A │ B │ - │ C │ - │   →     │ A │ A │ A │ A │ A │
│gap│gap│   │gap│   │         │continuous coverage│
└───┴───┴───┴───┴───┘         └───┴───┴───┴───┴───┘
```

**Teaching Pairs:**
```
Without:                       With:
┌─────┬─────┐                  ┌─────┬─────┐
│ R1  │ R1  │                  │ R1  │ R3  │  ← Senior supervises
├─────┼─────┤                  ├─────┼─────┤
│ R2  │ R2  │                  │ R2  │ Fac │  ← Faculty teaches
└─────┴─────┴                  └─────┴─────┘
No supervision                 Teaching pairs emerge
```

**Recovery Shields:**
```
Without:                       With:
Call → Heavy → Heavy           Call → Light → Normal
       (burnout)                     (recovery)
```

### 5.4 Connection to Axelrod's Findings

This model mirrors Axelrod's Iterated Prisoner's Dilemma results:

| Axelrod Finding | Schedule Analog |
|-----------------|-----------------|
| Cooperation beats defection long-term | Cooperative cells outcompete selfish |
| Clustering protects cooperators | Coalition formation in grid |
| TIT-FOR-TAT wins | Cells that reciprocate uplift survive |
| Nice strategies dominate | Cells that help neighbors first win |

The schedule grid becomes an **evolutionary petri dish** where cooperation emerges from pure selection pressure.

---

## 6. Next Steps

1. **Prototype `cooperative_fitness()`** - Implement and validate scoring
2. **Build NetworkX integration** - Graph-based coalition detection
3. **Benchmark against standard GA** - Compare convergence speed and solution quality
4. **Tune cooperation weights** - Find optimal balance of base vs uplift
5. **Visualize emergence** - Animate coalition formation over generations

---

## References

- Axelrod, R. (1984). *The Evolution of Cooperation*
- Shapley, L.S. (1953). "A Value for n-Person Games"
- NetworkX Documentation: Community Detection
- DEAP Documentation: Coevolutionary Algorithms

---

*This document describes the theoretical foundation for cooperative cell selection. Production implementation pending.*
