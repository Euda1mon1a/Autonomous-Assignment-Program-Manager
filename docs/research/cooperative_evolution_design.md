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

## 6. Endosymbiosis: Coalition Phase Transitions

### 6.1 Concept: From Partnership to Permanent Fusion

**Biological Analog:** ~2 billion years ago, a prokaryote engulfed an aerobic bacterium. Instead of digesting it, they formed a permanent symbiosis. That bacterium became the mitochondrion - no longer a separate organism, but an integral organelle. The host gained ATP production it could never evolve alone.

**Schedule Analog:** When certain cell coalitions prove so consistently successful that separating them would degrade fitness, they **fuse into atomic scheduling units**. The coalition stops being "cells that cooperate" and becomes "a single indivisible gene."

```
BEFORE (Coalition):           AFTER (Endosymbiont):
┌───────┐    ┌───────┐        ┌─────────────────┐
│ R2-NF │◄──►│ R3-AT │        │ [R2-NF ⊕ R3-AT] │
└───────┘    └───────┘        │   ATOMIC UNIT   │
  ▲              ▲            └─────────────────┘
  │              │                    │
  └──cooperation─┘                    └── Cannot be separated
     (breakable)                         (fused genome)
```

### 6.2 Detection Criteria: When to Trigger Absorption

A coalition becomes an endosymbiont candidate when it crosses multiple thresholds:

```python
class EndosymbiosisDetector:
    """
    Monitors coalitions for phase transition signals.
    """

    # Thresholds for endosymbiosis trigger
    CO_OCCURRENCE_THRESHOLD = 0.95  # Appear together 95%+ of time
    GENERATION_STABILITY = 20       # Stable for 20+ generations
    MUTUAL_DEPENDENCY = 0.8         # 80%+ fitness drop if separated
    MIN_COALITION_SIZE = 2          # At least 2 cells
    MAX_COALITION_SIZE = 5          # Don't absorb too many at once

    def detect_candidates(self, history: GenerationHistory) -> List[Coalition]:
        """
        Identify coalitions ready for endosymbiosis.
        """
        candidates = []

        for coalition in history.get_stable_coalitions():
            if self._meets_criteria(coalition, history):
                candidates.append(coalition)

        return candidates

    def _meets_criteria(self, coalition: Coalition, history: GenerationHistory) -> bool:
        """
        All criteria must be met for phase transition.
        """
        # Criterion 1: Co-occurrence frequency
        co_occurrence = history.calculate_co_occurrence(coalition)
        if co_occurrence < self.CO_OCCURRENCE_THRESHOLD:
            return False

        # Criterion 2: Generational stability
        stable_generations = history.count_stable_generations(coalition)
        if stable_generations < self.GENERATION_STABILITY:
            return False

        # Criterion 3: Mutual fitness dependency
        dependency = self._calculate_mutual_dependency(coalition)
        if dependency < self.MUTUAL_DEPENDENCY:
            return False

        # Criterion 4: Size bounds
        if not (self.MIN_COALITION_SIZE <= len(coalition) <= self.MAX_COALITION_SIZE):
            return False

        return True

    def _calculate_mutual_dependency(self, coalition: Coalition) -> float:
        """
        Measure how much each member depends on others.

        High dependency = removing any member crashes coalition fitness.
        """
        baseline_fitness = coalition.total_fitness()
        dependencies = []

        for member in coalition.members:
            # Fitness without this member
            reduced = coalition.fitness_without(member)
            # How much did fitness drop?
            drop = (baseline_fitness - reduced) / baseline_fitness
            dependencies.append(drop)

        # Return minimum dependency (weakest link)
        return min(dependencies)
```

**Detection Signals in Practice:**

| Signal | Threshold | Meaning |
|--------|-----------|---------|
| Co-occurrence | >95% | They always appear together |
| Stability | >20 generations | Not a lucky streak |
| Mutual dependency | >80% drop | Neither survives alone |
| Fitness boost | >40% combined | Together > sum of parts |

### 6.3 Implementation: Endosymbiont Templates

When absorption triggers, the coalition becomes a **template** - an atomic unit in the scheduling genome.

```python
@dataclass
class Endosymbiont:
    """
    A fused scheduling unit that propagates as one gene.

    Born from coalitions that proved inseparable.
    """
    id: str
    members: FrozenSet[CellTemplate]  # Immutable member set
    pattern: SchedulePattern          # The spatial arrangement
    fitness_baseline: float           # Expected combined fitness
    generation_born: int              # When fusion occurred
    lineage: str                      # Ancestry tracking

    # Emergent capabilities (see 6.5)
    unlocked_patterns: List[str]      # Patterns only this combo enables
    coverage_guarantee: float         # Coverage this unit guarantees
    supervision_guarantee: bool       # Does this unit self-supervise?

    def __hash__(self):
        """Endosymbionts are immutable and hashable."""
        return hash(self.id)

    def instantiate(self, grid: ScheduleGrid, anchor: Position) -> List[Cell]:
        """
        Place this endosymbiont into a grid at the anchor position.

        All members are placed atomically - all or nothing.
        """
        cells = []
        for template in self.members:
            offset = self.pattern.get_offset(template)
            position = anchor + offset
            cell = template.instantiate(position)
            cells.append(cell)
        return cells

    def is_compatible(self, grid: ScheduleGrid, anchor: Position) -> bool:
        """
        Check if this endosymbiont can be placed at anchor.

        Unlike individual cells, endosymbionts check ALL member
        positions before committing.
        """
        for template in self.members:
            offset = self.pattern.get_offset(template)
            position = anchor + offset
            if not grid.position_available(position):
                return False
            if not template.constraints_satisfied(position, grid):
                return False
        return True
```

**The Absorption/Merger Logic:**

```python
class EndosymbiosisEngine:
    """
    Executes coalition-to-endosymbiont phase transitions.
    """

    def __init__(self, genome: ScheduleGenome):
        self.genome = genome
        self.detector = EndosymbiosisDetector()
        self.endosymbiont_registry = {}

    def process_generation(self, generation: int, history: GenerationHistory):
        """
        Check for and execute any endosymbiosis events this generation.
        """
        # Step 1: Detect candidates
        candidates = self.detector.detect_candidates(history)

        for coalition in candidates:
            # Step 2: Verify no overlap with existing endosymbionts
            if self._overlaps_existing(coalition):
                continue

            # Step 3: Execute absorption
            endosymbiont = self._absorb(coalition, generation)

            # Step 4: Register in genome
            self._register(endosymbiont)

            # Step 5: Remove individual genes, add fused gene
            self._update_genome(coalition, endosymbiont)

            # Step 6: Log the phase transition
            self._log_endosymbiosis_event(coalition, endosymbiont, generation)

    def _absorb(self, coalition: Coalition, generation: int) -> Endosymbiont:
        """
        Execute the absorption: coalition → endosymbiont.

        This is the phase transition moment.
        """
        # Extract the pattern (spatial arrangement)
        pattern = self._extract_pattern(coalition)

        # Calculate emergent properties
        unlocked = self._discover_unlocked_patterns(coalition)
        coverage = self._calculate_coverage_guarantee(coalition)
        supervision = self._check_supervision_guarantee(coalition)

        # Create the endosymbiont
        endosymbiont = Endosymbiont(
            id=f"endo_{generation}_{hash(coalition)}",
            members=frozenset(c.to_template() for c in coalition.members),
            pattern=pattern,
            fitness_baseline=coalition.total_fitness(),
            generation_born=generation,
            lineage=self._trace_lineage(coalition),
            unlocked_patterns=unlocked,
            coverage_guarantee=coverage,
            supervision_guarantee=supervision,
        )

        return endosymbiont

    def _update_genome(self, coalition: Coalition, endosymbiont: Endosymbiont):
        """
        Replace individual genes with fused endosymbiont gene.

        Before: [gene_A, gene_B, gene_C, ...]
        After:  [endo_ABC, ...]  (genes A, B, C removed)
        """
        # Remove individual member genes
        for member in coalition.members:
            self.genome.remove_gene(member.gene_id)

        # Add endosymbiont as single gene
        self.genome.add_gene(endosymbiont)

    def _extract_pattern(self, coalition: Coalition) -> SchedulePattern:
        """
        Capture the spatial relationship between coalition members.

        This pattern is preserved forever in the endosymbiont.
        """
        anchor = coalition.get_anchor()  # Reference point
        offsets = {}

        for member in coalition.members:
            offset = member.position - anchor.position
            offsets[member.template()] = offset

        return SchedulePattern(anchor_type=anchor.type, offsets=offsets)
```

### 6.4 Emergent Lock-in: Indivisible Propagation

Once endosymbiosis occurs, the fused unit **cannot be separated** by normal evolutionary operations.

```python
class CooperativeGeneticOptimizer:
    """
    GA that respects endosymbiont atomicity.
    """

    def crossover(self, parent_a: Genome, parent_b: Genome) -> Genome:
        """
        Crossover that preserves endosymbionts.

        Endosymbionts cross over as atomic units.
        Individual genes cross normally.
        """
        child = Genome()

        # Handle endosymbionts first (atomic transfer)
        for endo in parent_a.endosymbionts:
            if random.random() < 0.5:
                child.add_endosymbiont(endo)

        for endo in parent_b.endosymbionts:
            if endo not in child.endosymbionts and random.random() < 0.5:
                child.add_endosymbiont(endo)

        # Handle individual genes (normal crossover)
        individual_genes = self._standard_crossover(
            parent_a.individual_genes,
            parent_b.individual_genes
        )
        child.add_genes(individual_genes)

        return child

    def mutate(self, genome: Genome, mutation_rate: float) -> Genome:
        """
        Mutation that respects endosymbiont boundaries.

        Endosymbionts mutate as units (position shift) not internally.
        """
        mutated = genome.copy()

        # Endosymbionts: can shift position, cannot break apart
        for endo in mutated.endosymbionts:
            if random.random() < mutation_rate:
                # Shift entire endosymbiont, don't mutate members
                self._shift_endosymbiont(endo, mutated)

        # Individual genes: normal mutation
        for gene in mutated.individual_genes:
            if random.random() < mutation_rate:
                self._mutate_gene(gene)

        return mutated

    def _shift_endosymbiont(self, endo: Endosymbiont, genome: Genome):
        """
        Move an endosymbiont to a new valid position.

        All members move together, preserving their pattern.
        """
        current_anchor = genome.get_anchor_position(endo)
        valid_positions = genome.grid.find_valid_positions(endo)

        if valid_positions:
            new_anchor = random.choice(valid_positions)
            genome.relocate_endosymbiont(endo, new_anchor)
```

**Lock-in Visualization:**

```
Generation 50: Endosymbiosis occurs
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   Coalition [R2-NF, R3-AT, Fac-Sup] triggers absorption        │
│                                                                 │
│   ┌───────┐   ┌───────┐   ┌───────┐                            │
│   │ R2-NF │ + │ R3-AT │ + │Fac-Sup│                            │
│   └───────┘   └───────┘   └───────┘                            │
│       │           │           │                                 │
│       └───────────┼───────────┘                                 │
│                   ▼                                             │
│   ┌─────────────────────────────────┐                          │
│   │   ENDOSYMBIONT: "TeachingTrio"  │                          │
│   │   ┌───────┬───────┬───────┐     │                          │
│   │   │ R2-NF │ R3-AT │Fac-Sup│     │  ← Atomic, indivisible   │
│   │   └───────┴───────┴───────┘     │                          │
│   │   Coverage: 100% | Supervision: ✓│                          │
│   └─────────────────────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Generation 51+: TeachingTrio propagates as single gene
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   Crossover: TeachingTrio transfers whole or not at all       │
│   Mutation:  TeachingTrio shifts position, never breaks        │
│   Selection: TeachingTrio competes as unit                     │
│                                                                 │
│   ┌─────────────────────────────────┐                          │
│   │      TeachingTrio              │──► Child A inherits       │
│   └─────────────────────────────────┘                          │
│                                                                 │
│   ┌─────────────────────────────────┐                          │
│   │      TeachingTrio (shifted)    │──► Child B inherits       │
│   └─────────────────────────────────┘     (different position)  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.5 Fitness Implications: Emergent Capabilities

Endosymbionts gain capabilities that **neither component had alone**. This is the evolutionary payoff for fusion.

```python
def discover_unlocked_patterns(endosymbiont: Endosymbiont) -> List[EmergentCapability]:
    """
    Identify capabilities that only exist in the fused state.

    These are the 'mitochondrial ATP' of scheduling.
    """
    capabilities = []

    # Capability 1: Coverage Guarantee
    # Individual cells might cover their slot. Endosymbionts can
    # guarantee continuous multi-slot coverage.
    if endosymbiont.provides_continuous_coverage():
        capabilities.append(EmergentCapability(
            name="CoverageChainLock",
            description="Guarantees unbroken coverage across member slots",
            fitness_bonus=50,
            constraint_satisfaction=["no_coverage_gap"]
        ))

    # Capability 2: Self-Supervision
    # A senior-junior endosymbiont satisfies its own supervision
    # requirement - no external dependency.
    if endosymbiont.is_self_supervising():
        capabilities.append(EmergentCapability(
            name="SelfSupervision",
            description="Contains both supervisor and supervisee",
            fitness_bonus=40,
            constraint_satisfaction=["supervision_ratio"]
        ))

    # Capability 3: Training Synergy
    # Teaching pairs that fused unlock training bonuses.
    if endosymbiont.has_teaching_relationship():
        capabilities.append(EmergentCapability(
            name="TrainingSynergy",
            description="Locked-in teaching relationship",
            fitness_bonus=30,
            constraint_satisfaction=["procedure_exposure"]
        ))

    # Capability 4: Resilience Guarantee
    # Fused units that include backup coverage are inherently resilient.
    if endosymbiont.has_backup_coverage():
        capabilities.append(EmergentCapability(
            name="InherentResilience",
            description="Built-in backup for member absence",
            fitness_bonus=60,
            constraint_satisfaction=["n_minus_1_coverage"]
        ))

    return capabilities


@dataclass
class EmergentCapability:
    """
    A capability that only exists in fused endosymbiont state.
    """
    name: str
    description: str
    fitness_bonus: float
    constraint_satisfaction: List[str]  # Constraints auto-satisfied

    def apply_to_fitness(self, base_fitness: float) -> float:
        """Endosymbionts get capability bonuses on top of member fitness."""
        return base_fitness + self.fitness_bonus
```

**Emergent Capability Examples:**

| Endosymbiont Type | Members | Emergent Capability | Why It's Emergent |
|-------------------|---------|---------------------|-------------------|
| **TeachingTrio** | R2 + R3 + Faculty | Self-Supervision + Training | No external supervisor needed; teaching happens automatically |
| **CoverageChain** | 5 consecutive AM slots | Coverage Guarantee | Gap impossible; chain is atomic |
| **CallRecovery** | Call + Post-Call Light | Burnout Prevention | Recovery is built-in, not optional |
| **CrossCover** | Clinic + Hospital backup | N-1 Resilience | Backup is structural, not assigned |

**Fitness Comparison:**

```
Individual Cells (Pre-Endosymbiosis):
┌─────────────────────────────────────────────────────────────────┐
│ R2-NF:    base=70, uplift=20, patterns=10     → total = 100    │
│ R3-AT:    base=75, uplift=25, patterns=15     → total = 115    │
│ Fac-Sup:  base=80, uplift=15, patterns=10     → total = 105    │
│                                                                 │
│ Combined (as coalition): 100 + 115 + 105      = 320            │
└─────────────────────────────────────────────────────────────────┘

TeachingTrio Endosymbiont (Post-Endosymbiosis):
┌─────────────────────────────────────────────────────────────────┐
│ Base (inherited):                              = 320           │
│ + SelfSupervision capability:                  +  40           │
│ + TrainingSynergy capability:                  +  30           │
│ + CoverageChainLock capability:                +  50           │
│ ─────────────────────────────────────────────────────          │
│ Endosymbiont fitness:                          = 440           │
│                                                                 │
│ Emergent bonus: 440 - 320 = +120 (37.5% boost)                 │
│                                                                 │
│ This bonus exists ONLY in fused state.                         │
│ Breaking the endosymbiont loses all 120 points.                │
└─────────────────────────────────────────────────────────────────┘
```

### 6.6 Evolutionary Dynamics: Endosymbiont Ecology

Over many generations, an ecosystem of endosymbionts emerges:

```
Generation 1-50: Coalition Phase
├── Individual cells compete
├── Coalitions form through cooperative selection
└── No endosymbionts yet

Generation 50-100: First Absorptions
├── Strongest coalitions cross thresholds
├── First endosymbionts appear (2-3 cell units)
└── Endosymbionts outcompete equivalent coalitions (+37% fitness)

Generation 100-200: Endosymbiont Competition
├── Multiple endosymbionts compete for grid space
├── Larger endosymbionts absorb smaller ones (meta-endosymbiosis)
└── Genome shifts from cells → endosymbionts as primary units

Generation 200+: Stabilization
├── Dominant endosymbiont species established
├── New coalitions rare (most niches filled)
├── Evolution operates on endosymbiont-level variation
└── Schedule genome is mostly "organelles, not cells"
```

**The Endgame:**

```
Early Genome:                    Late Genome:
┌─────────────────────────┐     ┌─────────────────────────┐
│ [c][c][c][c][c][c][c]   │     │ [ENDO-A ][ENDO-B ]      │
│ [c][c][c][c][c][c][c]   │     │ [ENDO-C    ][c][c]      │
│ [c][c][c][c][c][c][c]   │  →  │ [ENDO-D][ENDO-E  ]      │
│ [c][c][c][c][c][c][c]   │     │ [ENDO-F      ][c]       │
│ [c][c][c][c][c][c][c]   │     │ [ENDO-G ][ENDO-H ]      │
│                         │     │                         │
│ 35 individual cells     │     │ 8 endosymbionts + 4 cells│
│ High entropy            │     │ Low entropy, high order │
└─────────────────────────┘     └─────────────────────────┘
```

---

## 7. Next Steps

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
