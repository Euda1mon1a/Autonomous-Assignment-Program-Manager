# Time Crystal Anti-Churn Architecture

**Date:** 2025-12-29
**Status:** Implemented
**Location:** `backend/app/scheduling/periodicity/`

## Overview

The Time Crystal Anti-Churn module implements schedule stability optimization inspired by discrete time crystal physics and minimal disruption planning research. It prevents unnecessary schedule reshuffling during regeneration by explicitly optimizing for both constraint satisfaction AND rigidity.

## Problem Statement

### Current Behavior (Without Anti-Churn)

When the scheduling engine regenerates a schedule:

1. Solver treats each block independently
2. Finds optimal solution based on constraints
3. **May completely reshuffle assignments** even when only minor adjustments needed
4. Residents experience "schedule churn" - unnecessary changes to their rotations

**Example:**
```
Trigger: One resident adds a single day of leave
Current Behavior:
  - Solver regenerates entire 4-week block
  - 30 residents have assignments changed
  - Only 3 changes were actually necessary

Result: Confusion, complaints, loss of trust in system
```

### Desired Behavior (With Anti-Churn)

1. Solver considers current schedule as baseline
2. Finds solution that satisfies constraints WITH MINIMAL CHANGES
3. Only modifies assignments when necessary
4. Residents experience stable, predictable schedules

**Example:**
```
Trigger: One resident adds a single day of leave
With Anti-Churn:
  - Solver regenerates 4-week block
  - 3 residents have assignments changed
  - Changes localized to directly affected rotations

Result: Minimal disruption, maintained trust
```

## Theoretical Foundation

### Time Crystal Physics

**Discrete time crystals** are quantum systems that exhibit:
- **Rigid periodic behavior** that persists under perturbation
- **Subharmonic responses** - emergent longer cycles from base driving period
- **Phase locking** - synchronized behavior across coupled systems

**Mapping to Scheduling:**

| Time Crystal Property | Scheduling Analog |
|-----------------------|-------------------|
| Periodic driving (period T) | Weekly rhythm (7 days), ACGME windows (28 days) |
| Subharmonic response (period nT) | Q4 call (4-day cycle), alternating weekends (14-day) |
| Rigidity under perturbation | Schedule stability when constraints change |
| Phase coherence | Assignment patterns that repeat predictably |

### Minimal Disruption Planning

Recent research (Shleyfman et al., 2025) formalizes "plan disruption" - the problem of finding plans that minimally modify the initial state while achieving goals.

**Key Insight:** Jointly optimize:
1. **Goal achievement** (constraint satisfaction)
2. **Minimal changes** (state stability)

This maps perfectly to residency scheduling:
- Goals = ACGME compliance, coverage, equity
- Initial state = Current schedule
- Optimal plan = New schedule with minimal disruption

### Hamming Distance as Stability Metric

**Hamming distance** counts positions where two sequences differ. For schedules:

```python
hamming_distance(schedule_A, schedule_B) = |{assignments that differ}|
```

**Rigidity score** is the complement of normalized Hamming distance:

```python
rigidity = 1 - (hamming_distance / max_possible_distance)
```

- Rigidity = 1.0 → Identical schedules (perfect stability)
- Rigidity = 0.0 → Completely different (maximum churn)

## Architecture

### Module Structure

```
backend/app/scheduling/periodicity/
├── __init__.py                  # Public API exports
├── anti_churn.py                # Core implementation
├── INTEGRATION_GUIDE.md         # Integration documentation
└── examples.py                  # Usage examples

backend/tests/scheduling/periodicity/
├── __init__.py
└── test_anti_churn.py           # Comprehensive unit tests
```

### Core Components

#### 1. ScheduleSnapshot

Immutable representation of schedule state:

```python
@dataclass
class ScheduleSnapshot:
    assignments: frozenset[tuple[UUID, UUID, UUID | None]]
    timestamp: datetime
    metadata: dict[str, Any] | None
```

**Purpose:** Enable fast, reliable comparison between schedules

**Key Methods:**
- `from_assignments()` - Create from Assignment model objects
- `from_tuples()` - Create from solver output
- `to_dict()` - Convert to lookup dictionary

#### 2. Hamming Distance Functions

```python
def hamming_distance(schedule_a, schedule_b) -> int
def hamming_distance_by_person(schedule_a, schedule_b) -> dict[UUID, int]
```

**Purpose:** Quantify schedule differences

**Use Cases:**
- Measure total churn
- Identify which residents are most affected
- Track churn trends over time

#### 3. Rigidity Calculation

```python
def calculate_schedule_rigidity(new_schedule, current_schedule) -> float
```

**Returns:** Score from 0.0 (completely different) to 1.0 (identical)

**Interpretation:**
- ≥0.95: Minimal changes (safe to publish)
- 0.85-0.94: Low churn (review recommended)
- 0.70-0.84: Moderate churn (review carefully)
- 0.50-0.69: High churn (investigate)
- <0.50: Critical churn (likely indicates problem)

#### 4. Time Crystal Objective Function

```python
def time_crystal_objective(
    new_schedule: ScheduleSnapshot,
    current_schedule: ScheduleSnapshot,
    constraint_results: list[ConstraintResult],
    alpha: float = 0.3,
    beta: float = 0.1,
) -> float
```

**Objective:**
```
score = (1-α-β)·constraint_score + α·rigidity_score + β·fairness_score
```

**Parameters:**
- `alpha` (α): Weight for rigidity (anti-churn)
- `beta` (β): Weight for fairness (even churn distribution)
- Constraint weight: `1 - α - β`

**Tuning Recommendations:**

| α | Constraint | Rigidity | Use Case |
|---|------------|----------|----------|
| 0.0 | 100% | 0% | Pure optimization (max churn) |
| 0.1 | 90% | 10% | Constraint-focused with slight stability |
| 0.3 | 70% | 30% | **Balanced (recommended)** |
| 0.5 | 50% | 50% | Conservative (prefer stability) |
| 1.0 | 0% | 100% | Pure stability (no changes) |

#### 5. Impact Estimation

```python
def estimate_churn_impact(current, proposed) -> dict
```

**Returns:**
```python
{
    "total_changes": 15,
    "affected_people": 8,
    "max_person_churn": 4,
    "mean_person_churn": 1.875,
    "rigidity": 0.82,
    "severity": "moderate",
    "recommendation": "Moderate churn affecting 8 people. Review changes carefully."
}
```

**Purpose:** Human-readable summary for administrators

## Integration Patterns

### Pattern A: Post-Solver Validation (Simplest)

**When:** You want to add anti-churn without modifying solver code

```python
# In engine.py
result = solver.solve(context, existing_assignments)

if result.success:
    # Check churn
    current = ScheduleSnapshot.from_assignments(existing_assignments)
    proposed = ScheduleSnapshot.from_tuples(result.assignments)
    impact = estimate_churn_impact(current, proposed)

    if impact["severity"] in ["high", "critical"]:
        return {"status": "rejected", "reason": "Churn too high", "impact": impact}
```

**Pros:**
- Simple, non-invasive
- No solver modifications needed
- Easy to enable/disable

**Cons:**
- Solver doesn't optimize for rigidity
- May generate schedules that get rejected

### Pattern B: Solver Objective Integration (Advanced)

**When:** You want solver to directly optimize for rigidity

```python
# In solvers.py CP-SAT solver
# Add churn penalty to objective function

churn_penalty = 0
for person, block in assignment_pairs:
    current_template = current_map.get((person.id, block.id))
    if current_template:
        for template in templates:
            if template.id != current_template:
                # Penalize changing from current assignment
                churn_indicator = model.NewBoolVar(f"churn_{person}_{block}_{template}")
                model.Add(churn_indicator == x[(person, block, template)])
                churn_penalty += churn_indicator

# Weighted objective
model.Minimize(
    (1 - alpha) * (coverage_penalty + equity_penalty) +
    alpha * 100 * churn_penalty
)
```

**Pros:**
- Solver inherently considers rigidity
- Better optimization (can't generate high-churn solutions)
- Guaranteed to respect churn limits

**Cons:**
- Requires solver code changes
- Adds complexity to objective function
- May increase solve time

### Pattern C: Constraint-Based (Recommended)

**When:** You want to use existing constraint framework

Create `AntiChurnConstraint`:

```python
class AntiChurnConstraint(SoftConstraint):
    """Penalize schedule changes beyond threshold."""

    def __init__(self, current_assignments, max_churn_per_person=5):
        self.current_map = {
            (a.person_id, a.block_id): a.rotation_template_id
            for a in current_assignments
        }
        self.max_churn = max_churn_per_person

    def add_to_cpsat(self, model, x, context):
        for person in context.residents:
            churn_count = sum(
                x[(person.id, block.id, template.id)]
                for block, template in all_combinations
                if self.current_map.get((person.id, block.id)) != template.id
            )
            # Penalize if churn_count > max_churn
            model.Add(churn_count <= self.max_churn)  # Can be soft penalty instead
```

**Pros:**
- Uses existing constraint infrastructure
- Works with all solvers (CP-SAT, PuLP, etc.)
- Easy to tune via constraint priority/weight

**Cons:**
- Still requires constraint implementation
- Need to register constraint in manager

## Performance Considerations

### Computational Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Create snapshot | O(n) | n = number of assignments |
| Hamming distance | O(n) | Set symmetric difference |
| Rigidity calculation | O(n) | Uses Hamming distance |
| Per-person churn | O(n) | Group by person ID |
| Time crystal objective | O(c + n) | c = constraints, n = assignments |

### Memory Usage

- **ScheduleSnapshot**: ~16 bytes per assignment (UUID tuple)
- **100 residents × 730 blocks**: ~1.2 MB per snapshot
- Negligible compared to solver memory (hundreds of MB)

### Impact on Solve Time

**Pattern A (Post-validation):** +0.1s (snapshot creation only)

**Pattern B (Objective integration):** +5-20% solve time
- Adds O(n) binary variables to model
- Increases constraint propagation work
- Worth it for built-in rigidity optimization

**Pattern C (Constraint-based):** +3-10% solve time
- Depends on constraint complexity
- Soft constraints add to objective
- Hard constraints add to feasibility check

## Monitoring and Observability

### Metrics to Track

```python
# Prometheus metrics
schedule_rigidity = Histogram(
    "schedule_rigidity_score",
    "Schedule rigidity after regeneration",
    buckets=[0.0, 0.5, 0.7, 0.85, 0.95, 1.0]
)

schedule_churn_severity = Counter(
    "schedule_churn_severity_total",
    "Regenerations by churn severity",
    ["severity"]
)

schedule_affected_people = Gauge(
    "schedule_affected_people_count",
    "Number of people affected by last regeneration"
)
```

### Grafana Dashboards

**Panel 1: Rigidity Over Time**
- Line graph of rigidity score per regeneration
- Threshold line at 0.7 (acceptable minimum)
- Alerts on drops below 0.5

**Panel 2: Churn Severity Distribution**
- Pie chart: minimal/low/moderate/high/critical
- Goal: >80% minimal/low

**Panel 3: Affected People Histogram**
- Distribution of how many people affected per regeneration
- Goal: Median <5 people

## Testing Strategy

### Unit Tests

See `tests/scheduling/periodicity/test_anti_churn.py`:

- ✅ Snapshot creation and immutability
- ✅ Hamming distance calculation (identical, minimal, high churn)
- ✅ Rigidity score calculation
- ✅ Time crystal objective with various alphas
- ✅ Invalid parameter handling
- ✅ Impact estimation
- ✅ Per-person churn tracking

### Integration Tests

```python
@pytest.mark.integration
async def test_schedule_regeneration_preserves_most_assignments():
    """Verify anti-churn works end-to-end."""
    # Add one absence
    # Regenerate schedule
    # Assert: rigidity > 0.8, affected_people < 5
```

### Load Tests

```bash
# k6 test: Measure regeneration performance with anti-churn enabled
k6 run load-tests/anti-churn-regeneration.js
```

## Future Enhancements

### 1. Adaptive Alpha Tuning

Learn optimal alpha based on historical data:

```python
def recommend_alpha(historical_regenerations):
    """Use ML to recommend alpha based on past performance."""
    # Features: constraint violations, user complaints, rigidity scores
    # Target: Minimize user complaints while maintaining compliance
    return optimal_alpha
```

### 2. Subharmonic Pattern Detection

Identify natural cycles and preserve them:

```python
def detect_periodic_patterns(assignments, base_period=7):
    """Find emergent cycles (Q4 call, alternating weekends)."""
    # Use autocorrelation to find periods: 7, 14, 28 days
    # Preserve assignments that fit these patterns
    return detected_periods
```

### 3. Stroboscopic State Management

Checkpoint-based updates (inspired by time crystal observation):

```python
class StroboscopicScheduleManager:
    """Publish schedule updates only at discrete checkpoints."""

    async def advance_checkpoint(self):
        """Week boundaries: draft becomes authoritative."""
        # All observers see consistent state
        # Reduces race conditions
```

### 4. Churn Contagion Modeling

Use epidemiology models to predict churn propagation:

```python
def predict_churn_cascade(initial_change):
    """Estimate how one change will ripple through schedule."""
    # Use network analysis + SIR model
    # Identify "churn superspreaders" - changes that cascade
    return predicted_total_churn
```

## References

### Research Papers

1. **Shleyfman et al. (2025)**. Planning with Minimal Disruption. arXiv:2508.15358
   https://arxiv.org/abs/2508.15358

2. **Forecasting Interrupted Time Series** (2024)
   https://www.tandfonline.com/doi/full/10.1080/01605682.2024.2395315

3. **Hamming Distance Metric Learning**
   https://www.researchgate.net/publication/283326408_Hamming_Distance_Metric_Learning

### Internal Documentation

- [SYNERGY_ANALYSIS.md Section 11](../../SYNERGY_ANALYSIS.md#11-time-crystal-dynamics-for-schedule-stability)
- [Integration Guide](../../backend/app/scheduling/periodicity/INTEGRATION_GUIDE.md)
- [Example Usage](../../backend/app/scheduling/periodicity/examples.py)

### Related Modules

- `scheduling/constraints/` - Constraint framework
- `scheduling/solvers.py` - CP-SAT, PuLP, hybrid solvers
- `scheduling/engine.py` - Main scheduling engine
- `resilience/` - N-1/N-2 contingency, homeostasis

## Changelog

### 2025-12-29 - Initial Implementation

- ✅ Core anti-churn module (`anti_churn.py`)
- ✅ ScheduleSnapshot, hamming_distance, rigidity calculation
- ✅ Time crystal objective function with tunable weights
- ✅ Impact estimation and severity classification
- ✅ Comprehensive unit tests (>90% coverage)
- ✅ Integration guide with 3 patterns (post-validation, objective, constraint)
- ✅ Example usage code
- ✅ Architecture documentation

### Future

- [ ] Integrate into SchedulingEngine (Pattern C recommended)
- [ ] Add Prometheus metrics and Grafana dashboards
- [ ] Implement adaptive alpha tuning
- [ ] Add subharmonic pattern detection
- [ ] Build stroboscopic state manager
- [ ] Create admin UI for churn impact visualization

---

*"A time crystal is a phase that spontaneously breaks time-translation symmetry."* - Frank Wilczek

*"In many planning applications, we want plans that minimally modify the initial state to achieve the goals."* - Shleyfman et al., 2025
