# Foam Topology Scheduler - Design Document

> **Status:** Design Sketch | **Inspired by:** Penn Engineering Foam Bubble Research (2026)
> **Author:** AI-assisted design | **Related:** `spin_glass_model.py`, `hopfield_attractor_tools.py`

---

## Executive Summary

University of Pennsylvania engineers discovered that foam bubbles **continuously reorganize** in patterns that mathematically mirror how AI systems learn—challenging decades of assumptions that foams behave like static glass.

This document sketches a `FoamTopologyScheduler` that applies foam dynamics to medical residency scheduling, complementing existing Hopfield/spin-glass methods with a **perpetual soft reorganization** paradigm.

**Key Insight:** While Hopfield networks seek stable attractors, foam dynamics shows that wandering through configuration space can be optimal—exactly what we need for self-healing schedules.

---

## Physics Foundation

### Foam Structure Basics

| Foam Concept | Mathematical Model | Scheduling Analog |
|--------------|-------------------|-------------------|
| **Bubble** | Voronoi cell with curved faces | Assignment unit (person-block-template) |
| **Film** | Interface between two bubbles | Constraint boundary between assignments |
| **Plateau border** | Junction of three films at 120° | Multi-constraint intersection |
| **Vertex** | Junction of four Plateau borders | High-constraint-density decision point |

### T1 Topological Events (The Key Innovation)

A **T1 event** occurs when two bubbles that were neighbors become separated, while two previously non-adjacent bubbles become neighbors. This is the fundamental rearrangement mechanism in foam.

```
BEFORE T1:                    AFTER T1:
    A                             A
   / \                           /|\
  B   C         →               B | C
   \ /                           \|/
    D                             D

Bubbles B-C were neighbors     Bubbles A-D are now neighbors
Bubbles A-D were separated     Bubbles B-C are now separated
```

**Scheduling Translation:**
- A T1 event = a **shift swap** between two residents
- The "film length" threshold = constraint satisfaction margin
- T1 triggers when film shrinks to zero = swap becomes constraint-neutral

### Energy Model

Unlike Hopfield (fixed energy minima), foam energy continuously shifts:

```
E_foam = E_surface + E_pressure + E_viscous

E_surface = γ × Σ(film_areas)           # Surface tension (constraint penalties)
E_pressure = Σ(ΔP × bubble_volumes)     # Pressure difference (equity imbalance)
E_viscous = η × (dε/dt)²                # Viscous dissipation (change resistance)
```

**In Scheduling Terms:**
```python
E_schedule = E_constraint + E_equity + E_inertia

E_constraint = Σ(constraint_penalty × violation_degree)
E_equity = Σ(|workload_i - mean_workload|²)
E_inertia = resistance_to_change × num_recent_changes
```

### Coarsening Dynamics (Ostwald Ripening)

Foam naturally **coarsens** over time—small bubbles shrink and disappear while large bubbles grow. This is driven by gas diffusion across films.

**Scheduling Translation:**
- "Small bubbles" = fragmented assignments (single isolated shifts)
- "Large bubbles" = consolidated blocks (contiguous rotations)
- Coarsening = natural consolidation of scattered assignments into coherent blocks

---

## Core Data Structures

### `FoamCell` - The Bubble Analog

```python
@dataclass
class FoamCell:
    """
    A bubble in the foam = an assignment in the schedule.

    Attributes:
        cell_id: Unique identifier
        resident_id: Assigned resident
        block_id: Schedule block
        template_id: Assignment template (rotation type)

        # Topological properties
        neighbors: Set of adjacent FoamCell IDs (shared constraints)
        face_areas: Dict[neighbor_id, float] - "interface tension" with each neighbor
        volume: Effective "size" of assignment (hours, importance weight)
        pressure: Internal pressure (workload stress relative to capacity)

        # Dynamic properties
        centroid: Position in constraint space (for visualization)
        velocity: Rate of change (momentum from recent modifications)
        age: Time since last T1 event involving this cell
    """
    cell_id: str
    resident_id: UUID
    block_id: UUID
    template_id: UUID | None

    neighbors: set[str] = field(default_factory=set)
    face_areas: dict[str, float] = field(default_factory=dict)
    volume: float = 1.0
    pressure: float = 0.0

    centroid: np.ndarray = field(default_factory=lambda: np.zeros(3))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))
    age: float = 0.0
```

### `FoamFilm` - The Constraint Interface

```python
@dataclass
class FoamFilm:
    """
    Interface between two bubbles = shared constraint boundary.

    When film area → 0, a T1 event (swap) becomes favorable.

    Attributes:
        film_id: Unique identifier
        cell_a: First adjacent cell
        cell_b: Second adjacent cell

        area: Film area (constraint satisfaction margin)
        tension: Surface tension (constraint weight)
        curvature: Mean curvature (pressure difference indicator)

        t1_threshold: Area below which T1 event triggers
        t1_eligible: Whether this film can undergo T1
    """
    film_id: str
    cell_a: str
    cell_b: str

    area: float = 1.0
    tension: float = 1.0
    curvature: float = 0.0

    t1_threshold: float = 0.1
    t1_eligible: bool = True
```

### `T1Event` - The Swap Operation

```python
@dataclass
class T1Event:
    """
    A topological rearrangement = schedule swap.

    When executed, changes the neighbor relationships:
    - cells_separating: Were neighbors, now separated
    - cells_connecting: Were separated, now neighbors

    Attributes:
        event_id: Unique identifier
        timestamp: When event occurred

        film_collapsed: The film that triggered the T1
        cells_separating: Tuple of cells that lose adjacency
        cells_connecting: Tuple of cells that gain adjacency

        energy_before: Total energy before T1
        energy_after: Total energy after T1
        energy_delta: Change in energy (negative = favorable)

        constraint_impacts: Dict of constraint violations changed
        reversible: Whether this T1 can be undone
    """
    event_id: str
    timestamp: datetime

    film_collapsed: str
    cells_separating: tuple[str, str]
    cells_connecting: tuple[str, str]

    energy_before: float = 0.0
    energy_after: float = 0.0
    energy_delta: float = 0.0

    constraint_impacts: dict[str, float] = field(default_factory=dict)
    reversible: bool = True
```

---

## Algorithm Logic

### 1. Foam Initialization

Convert existing schedule to foam topology:

```python
def initialize_foam(assignments: list[Assignment], constraints: list[Constraint]) -> FoamStructure:
    """
    Convert schedule assignments to foam cells.

    1. Create FoamCell for each assignment
    2. Build adjacency graph based on shared constraints
    3. Compute initial film areas (constraint satisfaction margins)
    4. Calculate pressures (workload imbalances)
    5. Assign positions in constraint space for visualization
    """
    foam = FoamStructure()

    # Create cells
    for assignment in assignments:
        cell = FoamCell(
            cell_id=f"cell_{assignment.id}",
            resident_id=assignment.person_id,
            block_id=assignment.block_id,
            template_id=assignment.template_id,
        )
        foam.add_cell(cell)

    # Build neighbor relationships
    for constraint in constraints:
        affected_cells = constraint.get_affected_assignments(assignments)
        for cell_a, cell_b in itertools.combinations(affected_cells, 2):
            # Cells sharing a constraint are neighbors
            foam.add_neighbor(cell_a, cell_b)

            # Film area = how much "slack" in the constraint
            margin = constraint.compute_margin(cell_a, cell_b)
            foam.set_film_area(cell_a, cell_b, margin)

    # Compute pressures
    for resident in get_all_residents():
        workload = sum(c.volume for c in foam.cells_for_resident(resident))
        pressure = (workload - target_workload) / target_workload
        for cell in foam.cells_for_resident(resident):
            cell.pressure = pressure

    return foam
```

### 2. T1 Event Detection

Find eligible T1 events (swaps that would reduce energy):

```python
def detect_t1_candidates(foam: FoamStructure) -> list[T1Event]:
    """
    Identify films approaching zero area (T1-eligible).

    A T1 is favorable when:
    1. Film area < threshold (constraint nearly saturated)
    2. Energy after T1 < energy before
    3. No hard constraint violations post-T1
    """
    candidates = []

    for film in foam.films:
        if film.area > film.t1_threshold:
            continue
        if not film.t1_eligible:
            continue

        # Simulate T1 outcome
        cell_a, cell_b = foam.cells[film.cell_a], foam.cells[film.cell_b]

        # Find cells that would become new neighbors
        new_neighbors = find_post_t1_neighbors(foam, film)

        # Compute energy change
        energy_before = foam.compute_local_energy(cell_a, cell_b)
        energy_after = simulate_t1_energy(foam, film, new_neighbors)

        if energy_after < energy_before:
            event = T1Event(
                event_id=f"t1_{film.film_id}_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                film_collapsed=film.film_id,
                cells_separating=(cell_a.cell_id, cell_b.cell_id),
                cells_connecting=new_neighbors,
                energy_before=energy_before,
                energy_after=energy_after,
                energy_delta=energy_after - energy_before,
            )
            candidates.append(event)

    return sorted(candidates, key=lambda e: e.energy_delta)
```

### 3. Continuous Dynamics (The "Wandering")

The key innovation from Penn research—foam doesn't settle, it wanders:

```python
def evolve_foam(foam: FoamStructure, dt: float) -> list[T1Event]:
    """
    Evolve foam dynamics for one time step.

    Unlike Hopfield (gradient descent to fixed point), foam exhibits
    continuous reconfiguration. The system "wanders" through configuration
    space, occasionally executing T1 events.

    Returns:
        List of T1 events that occurred during this step
    """
    executed_events = []

    # 1. Update pressures based on current workloads
    update_pressures(foam)

    # 2. Gas diffusion: volume transfer between neighbors (workload balancing)
    for film in foam.films:
        delta_p = foam.cells[film.cell_a].pressure - foam.cells[film.cell_b].pressure
        # Gas flows from high to low pressure
        volume_transfer = film.area * delta_p * dt * DIFFUSION_CONSTANT
        transfer_volume(foam, film.cell_a, film.cell_b, volume_transfer)

    # 3. Film area dynamics: areas change based on pressure differences
    for film in foam.films:
        # Laplace pressure drives film curvature
        curvature = compute_film_curvature(foam, film)
        # Area changes to minimize surface energy
        d_area = -film.tension * curvature * dt
        film.area = max(0.0, film.area + d_area)

    # 4. Check for T1 events (films reaching zero area)
    for candidate in detect_t1_candidates(foam):
        if validate_t1_safety(foam, candidate):
            execute_t1(foam, candidate)
            executed_events.append(candidate)

            # Update ages of affected cells
            for cell_id in [candidate.cells_separating[0], candidate.cells_separating[1],
                           candidate.cells_connecting[0], candidate.cells_connecting[1]]:
                foam.cells[cell_id].age = 0.0

    # 5. Age all cells
    for cell in foam.cells.values():
        cell.age += dt

    # 6. Coarsening: remove very small cells (fragmented assignments)
    coarsen_foam(foam, min_volume=MIN_CELL_VOLUME)

    return executed_events
```

### 4. Coarsening (Block Consolidation)

```python
def coarsen_foam(foam: FoamStructure, min_volume: float = 0.1):
    """
    Remove small cells and redistribute their volume (Ostwald ripening).

    In scheduling: consolidate fragmented single-shift assignments
    into coherent blocks.
    """
    small_cells = [c for c in foam.cells.values() if c.volume < min_volume]

    for cell in small_cells:
        if not cell.neighbors:
            # Isolated cell - just remove
            foam.remove_cell(cell.cell_id)
            continue

        # Find largest neighbor to absorb this cell
        largest_neighbor = max(
            cell.neighbors,
            key=lambda n: foam.cells[n].volume
        )

        # Transfer assignment to larger neighbor's resident
        absorbing_cell = foam.cells[largest_neighbor]

        # Record the consolidation event
        log_consolidation(cell, absorbing_cell)

        # Remove small cell
        foam.remove_cell(cell.cell_id)
```

---

## Integration Points

### Backend: `FoamTopologyScheduler` Class

```python
# backend/app/scheduling/foam_topology.py

class FoamTopologyScheduler:
    """
    Foam-inspired scheduler using continuous topological dynamics.

    Key difference from SpinGlassScheduler:
    - Spin glass seeks fixed attractors (replica equilibria)
    - Foam topology allows continuous "wandering" with periodic T1 swaps

    Best for:
    - Self-healing schedules that adapt to perturbations
    - Finding natural swap opportunities (T1 events)
    - Consolidating fragmented assignments (coarsening)
    """

    def __init__(
        self,
        context: SchedulingContext,
        constraints: list[Constraint],
        diffusion_rate: float = 0.1,      # How fast workload balances
        t1_threshold: float = 0.1,        # Film area to trigger T1
        coarsening_threshold: float = 0.1, # Min cell volume
        random_seed: int | None = None,
    ):
        self.context = context
        self.constraints = constraints
        self.diffusion_rate = diffusion_rate
        self.t1_threshold = t1_threshold
        self.coarsening_threshold = coarsening_threshold
        self.rng = np.random.default_rng(random_seed)
        self.foam: FoamStructure | None = None
        self.t1_history: list[T1Event] = []

    def from_schedule(self, assignments: list[Assignment]) -> None:
        """Initialize foam from existing schedule."""
        self.foam = initialize_foam(assignments, self.constraints)

    def evolve(self, steps: int = 100, dt: float = 0.01) -> EvolutionResult:
        """
        Evolve foam dynamics and collect T1 events.

        Returns:
            EvolutionResult with recommended swaps and consolidations
        """
        for _ in range(steps):
            events = evolve_foam(self.foam, dt)
            self.t1_history.extend(events)

        return EvolutionResult(
            recommended_swaps=self.t1_history[-10:],  # Recent T1s
            consolidation_opportunities=self.find_coarsening_targets(),
            energy_trajectory=self.compute_energy_history(),
            stability_score=self.compute_stability(),
        )

    def find_optimal_swaps(self, n: int = 5) -> list[SwapRecommendation]:
        """
        Find top N swap opportunities based on T1 dynamics.

        Unlike greedy swaps, these are topologically "natural" exchanges
        where the constraint boundaries have thinned to allow passage.
        """
        candidates = detect_t1_candidates(self.foam)

        return [
            SwapRecommendation(
                resident_a=self.foam.cells[c.cells_separating[0]].resident_id,
                resident_b=self.foam.cells[c.cells_separating[1]].resident_id,
                block_a=self.foam.cells[c.cells_separating[0]].block_id,
                block_b=self.foam.cells[c.cells_separating[1]].block_id,
                energy_improvement=-c.energy_delta,
                constraint_margin=c.film_collapsed.area,
                natural_score=1.0 - c.film_collapsed.area,  # Lower film = more natural
            )
            for c in candidates[:n]
        ]
```

### MCP Tools

```python
# mcp-server/src/scheduler_mcp/foam_topology_tools.py

async def analyze_foam_structure(
    schedule_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> FoamStructureResponse:
    """
    Convert schedule to foam topology and analyze structure.

    Returns:
        - Cell count, film count, average neighbors
        - Pressure distribution (workload imbalance)
        - Films near T1 threshold (swap-ready boundaries)
        - Coarsening candidates (fragmented assignments)
    """

async def detect_natural_swaps(
    schedule_id: str | None = None,
    max_swaps: int = 10,
) -> NaturalSwapsResponse:
    """
    Find "natural" swap opportunities using T1 dynamics.

    Unlike greedy swap matching, T1-based swaps occur at points
    where constraint boundaries have naturally thinned, making
    the exchange nearly constraint-neutral.

    Returns:
        - Ranked list of T1-eligible swaps
        - Energy improvement for each
        - Constraint margins
        - "Naturalness" score (how organic the swap is)
    """

async def simulate_foam_evolution(
    schedule_id: str | None = None,
    steps: int = 100,
    return_trajectory: bool = True,
) -> FoamEvolutionResponse:
    """
    Simulate foam dynamics and observe emergent behavior.

    The Penn research shows foam wanders through configurations
    rather than settling. This simulation reveals:

    - Which swaps would naturally occur
    - Where consolidation would happen
    - How energy fluctuates over time
    - Stability characteristics

    Returns:
        - T1 events that would occur
        - Energy trajectory
        - Final foam state
        - Recommendations
    """

async def compute_foam_metrics(
    schedule_id: str | None = None,
) -> FoamMetricsResponse:
    """
    Compute foam physics metrics for schedule.

    Metrics:
        - Mean pressure: Average workload stress
        - Pressure variance: Equity measure
        - Mean film area: Average constraint slack
        - T1 rate: How many swaps per unit time
        - Coarsening rate: Consolidation tendency
        - Diffusion constant: How fast system equilibrates
    """
```

---

## CLI Integration (Claude Code)

### New Skill: `/foam-analysis`

```yaml
# .claude/skills/foam-analysis.md
---
name: foam-analysis
description: Analyze schedule using foam topology dynamics
trigger: /foam-analysis
---

# Foam Topology Analysis

Analyzes the current schedule using foam bubble dynamics inspired by
the Penn Engineering research showing foam continuously reorganizes
in patterns that mirror AI learning.

## Usage

```
/foam-analysis [schedule_id] [--swaps] [--evolve] [--metrics]
```

## Options

- `--swaps`: Find natural T1 swap opportunities
- `--evolve N`: Simulate N evolution steps
- `--metrics`: Compute foam physics metrics
- `--viz`: Generate visualization data

## Example Output

```
Foam Topology Analysis
═══════════════════════════════════════════════════════════

Structure:
  Cells (assignments): 156
  Films (constraint interfaces): 423
  Avg neighbors per cell: 5.4

Pressure Distribution (workload):
  Mean: 0.02 (nearly balanced)
  Std: 0.15
  Max overload: Dr. Smith (+23%)
  Max underload: Dr. Jones (-18%)

T1-Eligible Films (swap opportunities):
  1. Smith↔Jones (Block 7) - film: 0.08, energy: -2.3
  2. Chen↔Park (Block 12) - film: 0.12, energy: -1.7
  3. Wilson↔Lee (Block 3) - film: 0.14, energy: -0.9

Coarsening Candidates (fragmented):
  - Dr. Brown: 3 isolated half-days → consolidate
  - Dr. Davis: 2 scattered shifts → consolidate

Recommendation: Execute swap #1 (Smith↔Jones) - natural T1
```
```

### Integration with Existing Skills

The foam analysis complements existing exotic methods:

| Skill | Physics | Use Case |
|-------|---------|----------|
| `/spin-glass` | Replica theory | Find diverse near-optimal schedules |
| `/hopfield-energy` | Attractor dynamics | Assess schedule stability |
| `/foam-analysis` | Continuous topology | Find natural swaps, consolidate |
| `/quantum-optimize` | QUBO/annealing | Call schedule optimization |

---

## Frontend Visualization

### Foam Topology Visualizer (`foam-topology.html`)

Extend the existing Hopfield visualization with foam-specific features:

```javascript
// Key visualization elements:

// 1. Bubbles as 3D spheres (Voronoi cells)
function renderFoamCells(foam) {
    foam.cells.forEach(cell => {
        const geometry = new THREE.SphereGeometry(cell.volume * 0.5, 32, 32);
        const material = new THREE.MeshPhongMaterial({
            color: pressureToColor(cell.pressure),
            transparent: true,
            opacity: 0.7,
        });
        const sphere = new THREE.Mesh(geometry, material);
        sphere.position.copy(cell.centroid);
        scene.add(sphere);
    });
}

// 2. Films as connecting surfaces
function renderFilms(foam) {
    foam.films.forEach(film => {
        // Film color: green (healthy margin) → red (near T1)
        const color = filmAreaToColor(film.area, film.t1_threshold);

        // Draw curved surface between cells
        const surface = createFilmSurface(
            foam.cells[film.cell_a].centroid,
            foam.cells[film.cell_b].centroid,
            film.curvature
        );
        surface.material.color = color;
        scene.add(surface);
    });
}

// 3. T1 event animation
function animateT1(event) {
    // Dramatic animation of topology change:
    // - Collapsing film shrinks to point
    // - Cells rotate around each other
    // - New film expands between new neighbors

    const timeline = gsap.timeline();

    // Phase 1: Film collapse
    timeline.to(film.mesh.scale, { x: 0, y: 0, duration: 0.5 });

    // Phase 2: Cell swap animation
    timeline.to(cellA.mesh.position, { ...cellB.originalPosition, duration: 0.5 });
    timeline.to(cellB.mesh.position, { ...cellA.originalPosition, duration: 0.5 }, "<");

    // Phase 3: New film expansion
    timeline.fromTo(newFilm.mesh.scale, { x: 0, y: 0 }, { x: 1, y: 1, duration: 0.5 });
}

// 4. Controls
const controls = {
    diffusionRate: 0.1,    // How fast pressure equalizes
    t1Threshold: 0.1,      // When swaps trigger
    showFilms: true,       // Toggle film visibility
    showPressure: true,    // Color by workload
    autoEvolve: false,     // Continuous evolution
    speed: 1.0,            // Evolution speed
};
```

### React Component Integration

```tsx
// frontend/src/components/scheduling/FoamTopologyViewer.tsx

interface FoamTopologyViewerProps {
    scheduleId: string;
    onSwapSelect?: (swap: T1Event) => void;
}

export function FoamTopologyViewer({ scheduleId, onSwapSelect }: FoamTopologyViewerProps) {
    const { data: foamData } = useQuery({
        queryKey: ['foam-topology', scheduleId],
        queryFn: () => api.get(`/api/v1/schedules/${scheduleId}/foam-topology`),
    });

    const [selectedSwap, setSelectedSwap] = useState<T1Event | null>(null);

    return (
        <div className="grid grid-cols-3 gap-4">
            {/* 3D Visualization */}
            <div className="col-span-2 h-[600px] bg-gray-900 rounded-xl">
                <FoamCanvas foam={foamData?.foam} selectedSwap={selectedSwap} />
            </div>

            {/* Control Panel */}
            <div className="space-y-4">
                {/* Pressure Distribution */}
                <Card>
                    <CardHeader>
                        <CardTitle>Workload Pressure</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <PressureHistogram pressures={foamData?.pressures} />
                    </CardContent>
                </Card>

                {/* Natural Swaps */}
                <Card>
                    <CardHeader>
                        <CardTitle>Natural Swap Opportunities</CardTitle>
                        <CardDescription>T1-eligible topology changes</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <SwapList
                            swaps={foamData?.t1Candidates}
                            onSelect={setSelectedSwap}
                            onExecute={onSwapSelect}
                        />
                    </CardContent>
                </Card>

                {/* Coarsening */}
                <Card>
                    <CardHeader>
                        <CardTitle>Consolidation Opportunities</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <CoarseningList candidates={foamData?.coarseningCandidates} />
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
```

---

## Implementation Roadmap

### Phase 1: Core Data Structures
- [ ] `FoamCell`, `FoamFilm`, `T1Event` dataclasses
- [ ] `FoamStructure` container with topology operations
- [ ] Schedule-to-foam conversion

### Phase 2: Dynamics Engine
- [ ] Pressure calculation from workloads
- [ ] Film area dynamics
- [ ] T1 event detection and execution
- [ ] Coarsening algorithm

### Phase 3: Integration
- [ ] `FoamTopologyScheduler` class
- [ ] MCP tools for foam analysis
- [ ] `/foam-analysis` CLI skill

### Phase 4: Visualization
- [ ] `foam-topology.html` standalone visualizer
- [ ] `FoamTopologyViewer` React component
- [ ] T1 animation

### Phase 5: Production Hardening
- [ ] Unit tests for topology operations
- [ ] Integration tests with real schedules
- [ ] Performance optimization
- [ ] Documentation

---

## Scientific References

1. **Penn Engineering Foam Research (2026)**: Bubbles reorganize in patterns mirroring AI learning
2. **Weaire, D., & Hutzler, S. (1999)**: *The Physics of Foams* - foundational foam mechanics
3. **Durand, M., & Stone, H. A. (2006)**: T1 process and foam rheology
4. **Katgert, G., et al. (2008)**: Jamming and geometry of two-dimensional foams

---

## Summary

The `FoamTopologyScheduler` offers a unique complement to existing physics-inspired methods:

| Method | Paradigm | Strength |
|--------|----------|----------|
| **Hopfield** | Seek stable attractors | Stability assessment |
| **Spin Glass** | Explore replica diversity | Robust schedule ensembles |
| **Foam Topology** | Continuous reconfiguration | Natural swaps, self-healing |

The key insight from Penn's research—that foam "wanders" rather than "settles"—maps perfectly to self-healing schedules that continuously adapt through T1-style swaps.

---

*No existing Python library for foam topology dynamics exists. Implementation from scratch using NumPy for numerics.*

**Sources:**
- [OpenFOAM](https://www.openfoam.com/) - CFD framework (not applicable to discrete topology)
- [PythonFOAM](https://arxiv.org/abs/2103.09389) - OpenFOAM data analysis (not foam physics)
