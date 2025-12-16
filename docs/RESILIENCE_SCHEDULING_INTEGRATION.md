# Resilience-Aware Scheduling Integration

## Overview

This document describes the integration between the scheduling engine (`scheduling/`) and the resilience framework (`resilience/`). As of this implementation, the scheduling system can use resilience data to make more robust decisions, protecting the system from cascade failures.

## Architecture

### Before Integration (Passive Monitoring)

```
┌─────────────────────┐       ┌────────────────────┐
│  SchedulingEngine   │       │ ResilienceService  │
│                     │       │                    │
│  generate()         │──────▶│ check_health()     │
│  - solve schedule   │       │ - post-hoc report  │
│  - return result    │◀──────│ - warnings only    │
└─────────────────────┘       └────────────────────┘
        │
        │ Resilience data NOT used in solving
        ▼
    Schedule (may be fragile)
```

### After Integration (Active Constraints)

```
┌─────────────────────────────────────────────────────────┐
│                    SchedulingEngine                      │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              SchedulingContext                      │ │
│  │                                                     │ │
│  │  residents, faculty, blocks, templates              │ │
│  │  availability_matrix                                │ │
│  │                                                     │ │
│  │  + hub_scores: {faculty_id: score}      ◀────────┐ │ │
│  │  + current_utilization: 0.75            ◀────────┤ │ │
│  │  + n1_vulnerable_faculty: {ids}         ◀────────┤ │ │
│  │  + preference_trails: {faculty: prefs}  ◀────────┤ │ │
│  │  + zone_assignments: {faculty: zone}    ◀────────┤ │ │
│  └───────────────────────────────────────────────────┼─┘ │
│                                                      │   │
│  ┌─────────────────────────────────────────────────┐ │   │
│  │           ConstraintManager                     │ │   │
│  │                                                 │ │   │
│  │  Hard Constraints:                              │ │   │
│  │   - AvailabilityConstraint                      │ │   │
│  │   - EightyHourRuleConstraint                    │ │   │
│  │   - OneInSevenRuleConstraint                    │ │   │
│  │   - SupervisionRatioConstraint                  │ │   │
│  │                                                 │ │   │
│  │  Soft Constraints:                              │ │   │
│  │   - CoverageConstraint                          │ │   │
│  │   - EquityConstraint                            │ │   │
│  │   + HubProtectionConstraint  ◀─────────────────┤ │   │
│  │   + UtilizationBufferConstraint ◀──────────────┤ │   │
│  └─────────────────────────────────────────────────┘ │   │
│                                                      │   │
└───────────────────────────────────────────────────────┼───┘
                                                       │
                              ┌────────────────────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ ResilienceService  │
                    │                    │
                    │ hub_analyzer       │
                    │ contingency        │
                    │ stigmergy          │
                    │ utilization        │
                    └────────────────────┘
```

## New Components

### 1. Extended SchedulingContext

`backend/app/scheduling/constraints.py`

The `SchedulingContext` dataclass now includes resilience data fields:

```python
@dataclass
class SchedulingContext:
    # Core scheduling data
    residents: list
    faculty: list
    blocks: list
    templates: list
    availability: dict[UUID, dict[UUID, dict]]

    # Resilience data (Tier 1 Integration)
    hub_scores: dict[UUID, float]           # Faculty hub vulnerability
    current_utilization: float              # System utilization (0-1)
    n1_vulnerable_faculty: set[UUID]        # Single points of failure
    preference_trails: dict[UUID, dict]     # Stigmergy data
    zone_assignments: dict[UUID, UUID]      # Blast radius zones
    target_utilization: float = 0.80        # 80% threshold
```

### 2. HubProtectionConstraint

`backend/app/scheduling/constraints.py`

Soft constraint that protects critical "hub" faculty from over-assignment.

**Rationale (Network Theory):**
- Scale-free networks are robust to random failure but vulnerable to targeted hub removal
- In scheduling, "hubs" are faculty who cover unique services or are hard to replace
- Over-assigning hubs increases systemic risk

**Thresholds:**
- `HIGH_HUB_THRESHOLD = 0.4`: Above this = significant hub
- `CRITICAL_HUB_THRESHOLD = 0.6`: Above this = critical hub (2x penalty)

**Penalty Calculation:**
```
penalty = assignment_count × hub_score × multiplier × weight

Where:
  multiplier = 2.0 if hub_score ≥ 0.6 else 1.0
  weight = 15.0 (configurable)
```

### 3. UtilizationBufferConstraint

`backend/app/scheduling/constraints.py`

Soft constraint that maintains capacity buffer per queuing theory.

**Rationale (Queuing Theory):**
- Wait times increase exponentially as utilization approaches 100%
- At 80% utilization, system can absorb unexpected absences
- At 90%+, small disturbances cause cascade failures

**Formula:**
```
Wait Time ∝ ρ / (1 - ρ)

At 80%: multiplier = 4x (manageable)
At 90%: multiplier = 9x (dangerous)
At 95%: multiplier = 19x (cascade)
```

**Penalty Calculation:**
```python
if utilization > target:
    over_threshold = utilization - target
    penalty = (over_threshold ** 2) × weight × 100  # Quadratic
```

### 4. ConstraintManager Factory Methods

Two factory methods available:

```python
# Default: Resilience constraints disabled (backward compatible)
manager = ConstraintManager.create_default()

# Resilience-aware: Constraints enabled
manager = ConstraintManager.create_resilience_aware(target_utilization=0.80)
```

## Data Flow

### Schedule Generation with Resilience

```
1. SchedulingEngine.generate(check_resilience=True)
   │
   ├─▶ 2. _check_pre_generation_resilience()
   │       │
   │       └─▶ ResilienceService.check_health()
   │           Store result in self._pre_health_report
   │
   ├─▶ 3. _build_context(include_resilience=True)
   │       │
   │       └─▶ _populate_resilience_data()
   │           ├─▶ _get_hub_scores()      → context.hub_scores
   │           ├─▶ _get_n1_vulnerable()   → context.n1_vulnerable_faculty
   │           └─▶ _get_preference_trails() → context.preference_trails
   │           │
   │           └─▶ Enable HubProtection & UtilizationBuffer constraints
   │
   ├─▶ 4. _run_solver(algorithm, context)
   │       │
   │       └─▶ ConstraintManager.apply_to_cpsat/pulp(model, vars, context)
   │           │
   │           ├─▶ HubProtectionConstraint.add_to_cpsat()
   │           │   Adds penalty for hub over-assignment
   │           │
   │           └─▶ UtilizationBufferConstraint.add_to_cpsat()
   │               Adds penalty above 80% utilization
   │
   ├─▶ 5. Solve & create assignments
   │
   └─▶ 6. Return result with resilience info:
           {
             "resilience": {
               "pre_generation_status": "healthy",
               "post_generation_status": "warning",
               "utilization_rate": 0.78,
               "n1_compliant": true,
               "n2_compliant": false,
               "warnings": [...],
               "resilience_constraints_active": true,
               "hub_faculty_count": 3
             }
           }
```

## Usage Examples

### Basic Usage (Resilience-Aware)

```python
from app.scheduling.engine import SchedulingEngine
from app.scheduling.constraints import ConstraintManager
from app.resilience.service import ResilienceConfig

# Create engine with resilience-aware constraints
engine = SchedulingEngine(
    db=session,
    start_date=date(2024, 7, 1),
    end_date=date(2024, 7, 31),
    constraint_manager=ConstraintManager.create_resilience_aware(),
    resilience_config=ResilienceConfig(max_utilization=0.80),
)

# Generate with resilience checks
result = engine.generate(
    algorithm="cp_sat",
    check_resilience=True,  # Default
)

# Check resilience status
if result["resilience"]["utilization_rate"] > 0.80:
    print("Warning: Schedule exceeds 80% utilization buffer")
```

### Providing Hub Scores Manually

If hub analysis hasn't been run, you can provide scores directly:

```python
context = SchedulingContext(
    residents=residents,
    faculty=faculty,
    blocks=blocks,
    templates=templates,
    availability=availability_matrix,
    # Manually set hub scores
    hub_scores={
        faculty_1.id: 0.7,  # Critical hub
        faculty_2.id: 0.5,  # Moderate hub
        faculty_3.id: 0.2,  # Not a hub
    },
    target_utilization=0.80,
)
```

### Custom Constraint Weights

```python
from app.scheduling.constraints import (
    ConstraintManager,
    HubProtectionConstraint,
    UtilizationBufferConstraint,
)

manager = ConstraintManager.create_default()

# Replace with custom-weighted constraints
manager.remove("HubProtection")
manager.add(HubProtectionConstraint(weight=25.0))  # Higher penalty

manager.remove("UtilizationBuffer")
manager.add(UtilizationBufferConstraint(
    weight=30.0,
    target_utilization=0.75,  # More conservative
))
```

## Validation Output

When resilience constraints are active, validation includes additional details:

```python
result = constraint_manager.validate_all(assignments, context)

# Example violation from HubProtectionConstraint:
{
    "constraint_name": "HubProtection",
    "constraint_type": "hub_protection",
    "severity": "HIGH",
    "message": "Hub faculty Dr. Smith (score=0.72) has 15 assignments (avg=10.2)",
    "person_id": "uuid...",
    "details": {
        "hub_score": 0.72,
        "assignment_count": 15,
        "average_assignments": 10.2,
        "is_critical_hub": true
    }
}

# Example violation from UtilizationBufferConstraint:
{
    "constraint_name": "UtilizationBuffer",
    "constraint_type": "utilization_buffer",
    "severity": "HIGH",
    "message": "Utilization 92% exceeds target 80% (buffer exhausted)",
    "details": {
        "utilization_rate": 0.92,
        "target_utilization": 0.80,
        "buffer_remaining": 0.0,
        "total_assignments": 184,
        "max_capacity": 200,
        "danger_zone": true
    }
}
```

## Future Tier 2 Integration

The following features are prepared for but not yet fully integrated:

### Zone-Aware Scheduling (Blast Radius)

```python
# Future: SchedulingContext will include zone data
context.zone_assignments = {
    faculty_1.id: zone_inpatient.id,
    faculty_2.id: zone_outpatient.id,
}
context.block_zones = {
    block_1.id: zone_inpatient.id,
    block_2.id: zone_outpatient.id,
}

# Future: ZoneBoundaryConstraint
# Penalizes cross-zone assignments to contain failures
```

### Preference Trail Integration (Stigmergy)

```python
# Future: Use preference trails in assignment scoring
context.preference_trails = {
    faculty_1.id: {
        "monday_am": 0.8,  # Strong preference
        "friday_pm": 0.2,  # Avoidance
    }
}

# Future: PreferenceTrailConstraint
# Rewards assignments matching positive trails
```

### N-1 Vulnerability as Constraint

```python
# Future: Penalize schedules that create single points of failure
context.n1_vulnerable_faculty = {faculty_1.id, faculty_2.id}

# Future: N1VulnerabilityConstraint
# Prevents any single faculty from being sole coverage for a service
```

## Configuration Reference

### ResilienceConfig

```python
@dataclass
class ResilienceConfig:
    # Tier 1: Utilization thresholds
    max_utilization: float = 0.80
    warning_threshold: float = 0.70

    # Tier 3: Hub Analysis settings
    hub_threshold: float = 0.4           # Score to be considered a hub
    critical_hub_threshold: float = 0.6  # Score for critical hub status
```

### Constraint Weights (Defaults)

| Constraint | Weight | Priority | Effect |
|------------|--------|----------|--------|
| CoverageConstraint | 1000.0 | HIGH | Maximize block coverage |
| UtilizationBufferConstraint | 20.0 | HIGH | Maintain 20% buffer |
| HubProtectionConstraint | 15.0 | MEDIUM | Protect critical faculty |
| EquityConstraint | 10.0 | MEDIUM | Balance workload |
| ContinuityConstraint | 5.0 | LOW | Minimize rotation changes |

## Testing

```python
def test_hub_protection_reduces_hub_assignments():
    """Hub faculty should get fewer assignments when constraint is active."""
    context = SchedulingContext(
        faculty=[hub_faculty, normal_faculty],
        hub_scores={hub_faculty.id: 0.7},
        ...
    )

    manager = ConstraintManager.create_resilience_aware()
    result = solver.solve(context)

    hub_count = count_assignments(result, hub_faculty.id)
    normal_count = count_assignments(result, normal_faculty.id)

    # Hub should have fewer or equal assignments
    assert hub_count <= normal_count


def test_utilization_buffer_respected():
    """Schedule should not exceed 80% utilization when constraint is active."""
    context = SchedulingContext(
        faculty=faculty_list,
        target_utilization=0.80,
        ...
    )

    manager = ConstraintManager.create_resilience_aware()
    result = solver.solve(context)

    utilization = calculate_utilization(result, faculty_list)

    # Should be at or below 80%
    assert utilization <= 0.85  # Small tolerance for soft constraint
```

## Related Documentation

- [RESILIENCE_FRAMEWORK.md](./RESILIENCE_FRAMEWORK.md) - Full resilience concept documentation
- [SCHEDULING_OPTIMIZATION.md](./SCHEDULING_OPTIMIZATION.md) - Solver algorithms
- [TODO_RESILIENCE.md](./TODO_RESILIENCE.md) - Implementation status
