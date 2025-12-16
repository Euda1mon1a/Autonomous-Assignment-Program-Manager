***REMOVED*** Resilience-Aware Scheduling Integration

***REMOVED******REMOVED*** Overview

This document describes the integration between the scheduling engine (`scheduling/`) and the resilience framework (`resilience/`). As of this implementation, the scheduling system can use resilience data to make more robust decisions, protecting the system from cascade failures.

***REMOVED******REMOVED*** Architecture

***REMOVED******REMOVED******REMOVED*** Before Integration (Passive Monitoring)

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

***REMOVED******REMOVED******REMOVED*** After Integration (Active Constraints)

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

***REMOVED******REMOVED*** New Components

***REMOVED******REMOVED******REMOVED*** 1. Extended SchedulingContext

`backend/app/scheduling/constraints.py`

The `SchedulingContext` dataclass now includes resilience data fields:

```python
@dataclass
class SchedulingContext:
    ***REMOVED*** Core scheduling data
    residents: list
    faculty: list
    blocks: list
    templates: list
    availability: dict[UUID, dict[UUID, dict]]

    ***REMOVED*** Resilience data (Tier 1 Integration)
    hub_scores: dict[UUID, float]           ***REMOVED*** Faculty hub vulnerability
    current_utilization: float              ***REMOVED*** System utilization (0-1)
    n1_vulnerable_faculty: set[UUID]        ***REMOVED*** Single points of failure
    preference_trails: dict[UUID, dict]     ***REMOVED*** Stigmergy data
    zone_assignments: dict[UUID, UUID]      ***REMOVED*** Blast radius zones
    target_utilization: float = 0.80        ***REMOVED*** 80% threshold
```

***REMOVED******REMOVED******REMOVED*** 2. HubProtectionConstraint

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

***REMOVED******REMOVED******REMOVED*** 3. UtilizationBufferConstraint

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
    penalty = (over_threshold ** 2) × weight × 100  ***REMOVED*** Quadratic
```

***REMOVED******REMOVED******REMOVED*** 4. ConstraintManager Factory Methods

Two factory methods available:

```python
***REMOVED*** Default: Resilience constraints disabled (backward compatible)
manager = ConstraintManager.create_default()

***REMOVED*** Resilience-aware: Constraints enabled
manager = ConstraintManager.create_resilience_aware(target_utilization=0.80)
```

***REMOVED******REMOVED*** Data Flow

***REMOVED******REMOVED******REMOVED*** Schedule Generation with Resilience

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

***REMOVED******REMOVED*** Usage Examples

***REMOVED******REMOVED******REMOVED*** Basic Usage (Resilience-Aware)

```python
from app.scheduling.engine import SchedulingEngine
from app.scheduling.constraints import ConstraintManager
from app.resilience.service import ResilienceConfig

***REMOVED*** Create engine with resilience-aware constraints
engine = SchedulingEngine(
    db=session,
    start_date=date(2024, 7, 1),
    end_date=date(2024, 7, 31),
    constraint_manager=ConstraintManager.create_resilience_aware(),
    resilience_config=ResilienceConfig(max_utilization=0.80),
)

***REMOVED*** Generate with resilience checks
result = engine.generate(
    algorithm="cp_sat",
    check_resilience=True,  ***REMOVED*** Default
)

***REMOVED*** Check resilience status
if result["resilience"]["utilization_rate"] > 0.80:
    print("Warning: Schedule exceeds 80% utilization buffer")
```

***REMOVED******REMOVED******REMOVED*** Providing Hub Scores Manually

If hub analysis hasn't been run, you can provide scores directly:

```python
context = SchedulingContext(
    residents=residents,
    faculty=faculty,
    blocks=blocks,
    templates=templates,
    availability=availability_matrix,
    ***REMOVED*** Manually set hub scores
    hub_scores={
        faculty_1.id: 0.7,  ***REMOVED*** Critical hub
        faculty_2.id: 0.5,  ***REMOVED*** Moderate hub
        faculty_3.id: 0.2,  ***REMOVED*** Not a hub
    },
    target_utilization=0.80,
)
```

***REMOVED******REMOVED******REMOVED*** Custom Constraint Weights

```python
from app.scheduling.constraints import (
    ConstraintManager,
    HubProtectionConstraint,
    UtilizationBufferConstraint,
)

manager = ConstraintManager.create_default()

***REMOVED*** Replace with custom-weighted constraints
manager.remove("HubProtection")
manager.add(HubProtectionConstraint(weight=25.0))  ***REMOVED*** Higher penalty

manager.remove("UtilizationBuffer")
manager.add(UtilizationBufferConstraint(
    weight=30.0,
    target_utilization=0.75,  ***REMOVED*** More conservative
))
```

***REMOVED******REMOVED*** Validation Output

When resilience constraints are active, validation includes additional details:

```python
result = constraint_manager.validate_all(assignments, context)

***REMOVED*** Example violation from HubProtectionConstraint:
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

***REMOVED*** Example violation from UtilizationBufferConstraint:
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

***REMOVED******REMOVED*** Future Tier 2 Integration

The following features are prepared for but not yet fully integrated:

***REMOVED******REMOVED******REMOVED*** Zone-Aware Scheduling (Blast Radius)

```python
***REMOVED*** Future: SchedulingContext will include zone data
context.zone_assignments = {
    faculty_1.id: zone_inpatient.id,
    faculty_2.id: zone_outpatient.id,
}
context.block_zones = {
    block_1.id: zone_inpatient.id,
    block_2.id: zone_outpatient.id,
}

***REMOVED*** Future: ZoneBoundaryConstraint
***REMOVED*** Penalizes cross-zone assignments to contain failures
```

***REMOVED******REMOVED******REMOVED*** Preference Trail Integration (Stigmergy)

```python
***REMOVED*** Future: Use preference trails in assignment scoring
context.preference_trails = {
    faculty_1.id: {
        "monday_am": 0.8,  ***REMOVED*** Strong preference
        "friday_pm": 0.2,  ***REMOVED*** Avoidance
    }
}

***REMOVED*** Future: PreferenceTrailConstraint
***REMOVED*** Rewards assignments matching positive trails
```

***REMOVED******REMOVED******REMOVED*** N-1 Vulnerability as Constraint

```python
***REMOVED*** Future: Penalize schedules that create single points of failure
context.n1_vulnerable_faculty = {faculty_1.id, faculty_2.id}

***REMOVED*** Future: N1VulnerabilityConstraint
***REMOVED*** Prevents any single faculty from being sole coverage for a service
```

***REMOVED******REMOVED*** Configuration Reference

***REMOVED******REMOVED******REMOVED*** ResilienceConfig

```python
@dataclass
class ResilienceConfig:
    ***REMOVED*** Tier 1: Utilization thresholds
    max_utilization: float = 0.80
    warning_threshold: float = 0.70

    ***REMOVED*** Tier 3: Hub Analysis settings
    hub_threshold: float = 0.4           ***REMOVED*** Score to be considered a hub
    critical_hub_threshold: float = 0.6  ***REMOVED*** Score for critical hub status
```

***REMOVED******REMOVED******REMOVED*** Constraint Weights (Defaults)

| Constraint | Weight | Priority | Effect |
|------------|--------|----------|--------|
| CoverageConstraint | 1000.0 | HIGH | Maximize block coverage |
| UtilizationBufferConstraint | 20.0 | HIGH | Maintain 20% buffer |
| HubProtectionConstraint | 15.0 | MEDIUM | Protect critical faculty |
| EquityConstraint | 10.0 | MEDIUM | Balance workload |
| ContinuityConstraint | 5.0 | LOW | Minimize rotation changes |

***REMOVED******REMOVED*** Testing

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

    ***REMOVED*** Hub should have fewer or equal assignments
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

    ***REMOVED*** Should be at or below 80%
    assert utilization <= 0.85  ***REMOVED*** Small tolerance for soft constraint
```

***REMOVED******REMOVED*** Related Documentation

- [RESILIENCE_FRAMEWORK.md](./RESILIENCE_FRAMEWORK.md) - Full resilience concept documentation
- [SCHEDULING_OPTIMIZATION.md](./SCHEDULING_OPTIMIZATION.md) - Solver algorithms
- [TODO_RESILIENCE.md](./TODO_RESILIENCE.md) - Implementation status
