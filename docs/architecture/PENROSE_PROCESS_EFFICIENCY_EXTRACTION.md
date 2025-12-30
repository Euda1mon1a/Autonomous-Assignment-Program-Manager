# Penrose Process Efficiency Extraction

**Status:** Implemented
**Version:** 1.0.0
**Last Updated:** 2025-12-29

## Overview

The Penrose Process Efficiency Extraction applies black hole physics concepts to medical residency schedule optimization. Named after physicist Roger Penrose, this technique exploits rotation boundaries (duty cycle transitions) to extract efficiency improvements without adding new constraints.

## Physics Foundation

### The Penrose Process

In astrophysics, the Penrose process extracts rotational energy from spinning black holes:

1. A particle enters the **ergosphere** (region between event horizon and static limit)
2. The particle splits into two components
3. One component (with **negative energy** relative to infinity) falls into the black hole
4. The other component escapes with **more energy** than the original particle
5. The black hole's rotation slows down (energy conservation)

**Theoretical maximum extraction:** 29% of the black hole's rotational energy

### Scheduling Analogy

| Physics Concept | Scheduling Equivalent |
|-----------------|----------------------|
| **Rotating Black Hole** | Schedule with recurring duty cycles |
| **Ergosphere** | Rotation boundary periods (week ends, block transitions) |
| **Particle Split** | Assignment decomposition into phases |
| **Negative Energy State** | Swaps with local cost but global benefit |
| **Energy Extraction** | Conflict reduction and coverage improvement |
| **Rotation Spindown** | Diminishing returns on optimization |

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                 PenroseEfficiencyExtractor                  │
├─────────────────────────────────────────────────────────────┤
│ • identify_ergosphere_periods()                             │
│ • decompose_into_phases()                                   │
│ • find_negative_energy_swaps()                              │
│ • execute_penrose_cascade()                                 │
│ • compute_extraction_efficiency()                           │
└─────────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐
│ ErgospherePeriod│ │ PenroseSwap  │ │RotationEnergyTrkr│
├─────────────────┤ ├──────────────┤ ├──────────────────┤
│ • start_time    │ │ • assignment │ │ • initial_energy │
│ • end_time      │ │ • local_cost │ │ • extracted      │
│ • velocity      │ │ • global_ben │ │ • budget         │
│ • potential     │ │ • net_extr   │ │ • history        │
│ • boundary_type │ │ • executed   │ │ • is_exhausted   │
└─────────────────┘ └──────────────┘ └──────────────────┘
```

### Data Structures

#### ErgospherePeriod

Represents a rotation boundary with extraction potential.

```python
@dataclass
class ErgospherePeriod:
    start_time: datetime
    end_time: datetime
    rotation_velocity: float          # Swaps per day
    extraction_potential: float       # 0-1 scale (max 0.29)
    boundary_type: str                # "week_end", "block_transition", "rotation_handoff"
    affected_assignments: list[UUID]
```

**Boundary Types:**
- **week_end**: Friday PM to Monday AM transitions
- **block_transition**: Last day of academic block to first day of next
- **rotation_handoff**: Service change boundaries (future)

#### PhaseComponent

Decomposes assignments into rotation phases.

```python
@dataclass
class PhaseComponent:
    assignment_id: UUID
    phase_type: str                   # "pre_transition", "transition", "post_transition"
    energy_state: str                 # "positive", "negative", "zero"
    phase_start: datetime
    phase_end: datetime
    conflict_score: int
    flexibility_score: float          # 0-1, degrees of freedom
```

#### PenroseSwap

Represents a swap with local cost but global benefit.

```python
@dataclass
class PenroseSwap:
    swap_id: UUID
    assignment_a: UUID
    assignment_b: UUID
    local_cost: float                 # Local conflict increase
    global_benefit: float             # System-wide benefit
    ergosphere_period: ErgospherePeriod
    confidence: float = 0.8
    executed: bool = False

    @property
    def net_extraction(self) -> float:
        return global_benefit - abs(local_cost)
```

#### RotationEnergyTracker

Tracks extraction limits (prevents over-optimization).

```python
class RotationEnergyTracker:
    initial_rotation_energy: float
    extracted_energy: float = 0.0
    max_extraction_fraction: float = 0.29  # Penrose limit
    extraction_history: list[dict]

    @property
    def is_exhausted(self) -> bool:
        return extraction_fraction >= max_extraction_fraction
```

## Algorithm

### Phase 1: Ergosphere Identification

```python
async def identify_ergosphere_periods(
    start_date: date,
    end_date: date
) -> list[ErgospherePeriod]:
    """
    Scan schedule for rotation boundaries.

    Returns high-potential periods sorted by extraction_potential.
    """
```

**Detection Rules:**

1. **Week-End Ergospheres**
   - Period: Friday PM to Monday AM
   - Rotation velocity: Historical swap rate × 2.0 (weekend factor)
   - Extraction potential: min(0.29, velocity × 0.1)

2. **Block Transition Ergospheres**
   - Period: Last block half-day to first of next block
   - Rotation velocity: Historical swap rate × 1.0
   - Extraction potential: min(0.29, velocity × 0.15) *(higher than weekends)*

3. **High-Potential Threshold**
   - Ergospheres with `extraction_potential > 0.15` (15%)

### Phase 2: Phase Decomposition

```python
async def decompose_into_phases(
    assignment: Assignment
) -> list[PhaseComponent]:
    """
    Split assignment into pre/during/post transition phases.

    Identifies negative-energy states (phases where conflicts decrease).
    """
```

**Energy State Classification:**

- **Positive Energy**: Phase increases conflicts
- **Negative Energy**: Phase reduces conflicts (target for swaps)
- **Zero Energy**: No net conflict change

### Phase 3: Negative-Energy Swap Discovery

```python
async def find_negative_energy_swaps(
    schedule_id: UUID,
    period: ErgospherePeriod
) -> list[PenroseSwap]:
    """
    Find swaps that are locally costly but globally beneficial.

    Returns swaps sorted by net_extraction (highest first).
    """
```

**Swap Evaluation:**

1. **Local Cost Calculation**
   - Rotation template mismatch: +2.0
   - Role mismatch: +1.5
   - Preference mismatch: +1.0

2. **Global Benefit Calculation**
   - Improved workload balance: +3.0
   - Reduced consecutive shifts: +2.0
   - Better specialty coverage: +1.5

3. **Beneficial Swap Filter**
   - Only include swaps where `global_benefit > abs(local_cost)`

### Phase 4: Penrose Cascade Execution

```python
async def execute_penrose_cascade(
    schedule_id: UUID,
    max_iterations: int = 5
) -> dict[str, Any]:
    """
    Execute cascade of Penrose swaps until convergence or budget exhaustion.

    Returns optimization metrics.
    """
```

**Cascade Algorithm:**

```
Initialize RotationEnergyTracker(initial_energy=100.0)

FOR iteration = 1 to max_iterations:
    IF tracker.is_exhausted:
        BREAK

    ergospheres = identify_ergosphere_periods(date_range)

    swaps = []
    FOR ergosphere IN high_potential_ergospheres:
        swaps.extend(find_negative_energy_swaps(schedule, ergosphere))

    IF no beneficial swaps found:
        BREAK

    FOR swap IN swaps sorted by net_extraction DESC:
        IF swap.net_extraction <= tracker.extraction_budget:
            execute_swap(swap)
            tracker.record_extraction(swap)

RETURN optimization_results
```

**Termination Conditions:**

1. Max iterations reached
2. Extraction budget exhausted (29% limit)
3. No more beneficial swaps found

## Visualization

### PenroseVisualizer

Provides four visualization types:

#### 1. Ergosphere Timeline

Shows when and where extraction opportunities exist.

```python
visualizer.plot_ergosphere_timeline(ergospheres)
```

**Features:**
- Timeline of ergosphere periods
- Color intensity = extraction potential
- Grouped by boundary type

#### 2. Extraction Efficiency Plot

Tracks cumulative energy extraction vs. Penrose limit.

```python
visualizer.plot_extraction_efficiency(swaps)
```

**Features:**
- Cumulative extraction curve
- Individual swap contributions (bar chart)
- Penrose limit line (29% threshold)

#### 3. Swap Network Graph

Visualizes swap relationships and clusters.

```python
visualizer.plot_swap_network(swaps)
```

**Features:**
- Nodes = assignments
- Edges = swaps (thickness = benefit)
- Color = executed vs. proposed

#### 4. Phase Decomposition

Shows energy states across assignment phases.

```python
visualizer.plot_phase_decomposition(phases)
```

**Features:**
- Phase progression (pre → transition → post)
- Color-coded energy states
- Conflict scores overlay

## Usage Examples

### Basic Optimization

```python
from app.scheduling import PenroseEfficiencyExtractor
from datetime import date, timedelta

async with get_db() as db:
    extractor = PenroseEfficiencyExtractor(db)

    # Identify opportunities
    start = date.today()
    end = start + timedelta(days=28)  # One block
    ergospheres = await extractor.identify_ergosphere_periods(start, end)

    print(f"Found {len(ergospheres)} ergospheres")
    high_potential = [e for e in ergospheres if e.is_high_potential]
    print(f"{len(high_potential)} are high-potential (>15%)")

    # Execute cascade optimization
    schedule_id = UUID("...")
    result = await extractor.execute_penrose_cascade(schedule_id)

    print(f"Executed {result['swaps_executed']} swaps")
    print(f"Efficiency extracted: {result['efficiency_extracted']:.2%}")
    print(f"Improvement: {result['improvement']:.1f}%")
```

### Targeted Ergosphere Optimization

```python
# Find negative-energy swaps in specific period
friday_pm_ergosphere = ergospheres[0]  # Assume sorted by potential

swaps = await extractor.find_negative_energy_swaps(
    schedule_id,
    friday_pm_ergosphere
)

print(f"Found {len(swaps)} beneficial swaps")
for swap in swaps[:5]:  # Top 5
    print(f"  Net extraction: {swap.net_extraction:.2f}")
    print(f"  Ratio: {swap.extraction_ratio:.2f}x")
```

### Phase Analysis

```python
# Decompose specific assignment
assignment = await db.get(Assignment, assignment_id)
phases = await extractor.decompose_into_phases(assignment)

for phase in phases:
    print(f"{phase.phase_type}: {phase.energy_state} energy")
    print(f"  Conflicts: {phase.conflict_score}")
    print(f"  Flexibility: {phase.flexibility_score:.2f}")
```

### Visualization Workflow

```python
from app.scheduling import PenroseVisualizer

visualizer = PenroseVisualizer()

# Generate all visualizations
fig1 = visualizer.plot_ergosphere_timeline(ergospheres)
fig1.savefig("ergosphere_timeline.png")

fig2 = visualizer.plot_extraction_efficiency(swaps)
fig2.savefig("extraction_efficiency.png")

fig3 = visualizer.plot_swap_network(swaps)
fig3.savefig("swap_network.png")

# Generate report
report = visualizer.generate_summary_report(ergospheres, swaps, efficiency)
print(report["summary"])
print("\nRecommendations:")
for rec in report["recommendations"]:
    print(f"  {rec}")
```

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Identify ergospheres | O(B) | B = number of blocks |
| Decompose assignment | O(1) | Fixed 3 phases per assignment |
| Find swaps | O(A²) | A = assignments in period |
| Execute cascade | O(I × E × A²) | I = iterations, E = ergospheres |

### Space Complexity

- **Ergosphere storage**: O(B) where B = blocks in date range
- **Swap storage**: O(A²) where A = assignments per ergosphere
- **Energy tracker history**: O(S) where S = swaps executed

### Optimization Limits

- **Maximum extraction**: 29% of initial rotation energy (Penrose limit)
- **Diminishing returns**: Efficiency gain decreases with each iteration
- **Practical limit**: ~5 cascade iterations before marginal returns

## Integration Points

### Scheduling Engine

```python
from app.scheduling import SchedulingEngine, PenroseEfficiencyExtractor

async def generate_optimized_schedule(schedule_config):
    # Standard schedule generation
    schedule = await SchedulingEngine.generate(schedule_config)

    # Post-processing: Penrose optimization
    extractor = PenroseEfficiencyExtractor(db)
    result = await extractor.execute_penrose_cascade(
        schedule.id,
        max_iterations=3
    )

    schedule.metadata["penrose_efficiency"] = result["efficiency_extracted"]
    schedule.metadata["swaps_executed"] = result["swaps_executed"]

    return schedule
```

### MCP Tools

```python
# MCP tool for AI agent access
@mcp.tool()
async def optimize_schedule_penrose(
    schedule_id: str,
    max_iterations: int = 5
) -> dict:
    """Extract efficiency using Penrose process."""
    extractor = PenroseEfficiencyExtractor(db)
    return await extractor.execute_penrose_cascade(
        UUID(schedule_id),
        max_iterations=max_iterations
    )
```

### Dashboard Integration

```python
# Add to resilience dashboard
from app.scheduling import PenroseVisualizer

async def get_penrose_metrics(schedule_id: UUID):
    extractor = PenroseEfficiencyExtractor(db)

    # Get current state
    ergospheres = await extractor.identify_ergosphere_periods(
        date.today(),
        date.today() + timedelta(days=28)
    )

    # Calculate potential
    total_potential = sum(e.extraction_potential for e in ergospheres)

    return {
        "ergosphere_count": len(ergospheres),
        "high_potential_count": sum(1 for e in ergospheres if e.is_high_potential),
        "total_extraction_potential": total_potential,
        "avg_potential_per_ergosphere": total_potential / len(ergospheres) if ergospheres else 0,
    }
```

## Testing

### Test Coverage

- **ErgospherePeriod**: 6 tests (validation, properties, thresholds)
- **PhaseComponent**: 3 tests (validation, energy states)
- **PenroseSwap**: 7 tests (calculation, ratios, beneficial detection)
- **RotationEnergyTracker**: 5 tests (tracking, exhaustion, rejection)
- **PenroseEfficiencyExtractor**: 6 async tests (identification, decomposition, swaps, cascade)
- **PenroseVisualizer**: 4 tests (plotting, reports)

**Total:** 31 tests, ~700 lines of test code

### Running Tests

```bash
cd backend
pytest tests/scheduling/test_penrose_efficiency.py -v
```

### Test Fixtures

```python
@pytest.fixture
def sample_ergosphere():
    return ErgospherePeriod(
        start_time=datetime(2024, 1, 5, 12, 0),
        end_time=datetime(2024, 1, 8, 8, 0),
        rotation_velocity=2.0,
        extraction_potential=0.15,
        boundary_type="week_end",
    )

@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    return db
```

## Future Enhancements

### Planned Features

1. **Rotation Handoff Detection** (v1.1)
   - Identify service change boundaries
   - Higher extraction potential at major transitions

2. **Machine Learning Integration** (v1.2)
   - Predict extraction potential from historical data
   - Learn optimal swap patterns per ergosphere type

3. **Multi-Schedule Coordination** (v1.3)
   - Coordinate Penrose swaps across multiple residency programs
   - Global optimization across specialties

4. **Real-Time Monitoring** (v1.4)
   - Stream ergosphere detection as schedules evolve
   - Alert when high-potential periods emerge

### Research Directions

- **Quantum-Inspired Scheduling**: Explore quantum tunneling analogs for constraint satisfaction
- **Hawking Radiation Model**: Use schedule "evaporation" (gradual degradation) as optimization signal
- **Kerr Metric Scheduling**: Incorporate rotation parameter (duty cycle intensity) into optimization

## References

### Physics Literature

- Penrose, R. (1969). "Gravitational collapse: The role of general relativity." *Nuovo Cimento Rivista Serie*, 1, 252-276.
- Wald, R.M. (1974). "Energy limits in the Penrose process." *Physical Review D*, 10(6), 1680-1685.

### Scheduling Theory

- Brucker, P. (2007). *Scheduling Algorithms*. Springer.
- Pinedo, M. (2016). *Scheduling: Theory, Algorithms, and Systems*. Springer.

### Cross-Disciplinary Applications

- Similar concept to "negative mass" propulsion in Alcubierre drive
- Analogous to arbitrage in financial markets (local loss, global gain)

## Glossary

| Term | Definition |
|------|------------|
| **Ergosphere** | Rotation boundary period with extraction potential |
| **Negative Energy State** | Assignment phase that reduces conflicts when swapped |
| **Rotation Velocity** | Rate of schedule changes (swaps per day) |
| **Extraction Potential** | Estimated efficiency gain (0-1 scale, max 0.29) |
| **Penrose Limit** | Maximum extractable energy (29% of rotation energy) |
| **Penrose Swap** | Swap with local cost but global benefit |
| **Phase Component** | Pre/during/post transition decomposition of assignment |
| **Energy Tracker** | Monitor for extraction budget and limits |

---

**Implementation Files:**

- `backend/app/scheduling/penrose_efficiency.py` (849 lines)
- `backend/app/scheduling/penrose_visualization.py` (674 lines)
- `backend/tests/scheduling/test_penrose_efficiency.py` (686 lines)

**Total Implementation:** ~2,200 lines of production code + tests
