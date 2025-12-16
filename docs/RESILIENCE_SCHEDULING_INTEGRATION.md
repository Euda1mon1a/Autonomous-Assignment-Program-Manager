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
│  │                                                 │ │   │
│  │  Tier 1 Resilience (Critical):                 │ │   │
│  │   + HubProtectionConstraint  ◀─────────────────┤ │   │
│  │   + UtilizationBufferConstraint ◀──────────────┤ │   │
│  │                                                 │ │   │
│  │  Tier 2 Resilience (Strategic):                │ │   │
│  │   + ZoneBoundaryConstraint ◀───────────────────┤ │   │
│  │   + PreferenceTrailConstraint ◀────────────────┤ │   │
│  │   + N1VulnerabilityConstraint ◀────────────────┤ │   │
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
                    │ blast_radius       │
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
    hub_scores: dict[UUID, float]           ***REMOVED*** hub vulnerability
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

***REMOVED******REMOVED*** Tier 2 Constraints (Implemented)

***REMOVED******REMOVED******REMOVED*** 5. ZoneBoundaryConstraint

`backend/app/scheduling/constraints.py`

Respects blast radius zone boundaries in scheduling.

**Pattern (AWS Architecture):**
- Failures should be contained within defined boundaries ("cells")
- A problem in one zone cannot propagate to affect others
- Zone A failure → Zones B and C continue unaffected

**Implementation:**
- Penalizes assignments where faculty_zone != block_zone
- Critical zones (inpatient) have higher isolation requirements
- Auto-enabled when zone data is available

**Example Zones:**
```
Zone A: Inpatient (ICU, Wards, Procedures)
Zone B: Outpatient (Clinics, Consults)
Zone C: Education (Didactics, Simulation)
```

**Penalty:** `cross_zone_count × weight (12.0)`

***REMOVED******REMOVED******REMOVED*** 6. PreferenceTrailConstraint

`backend/app/scheduling/constraints.py`

Uses stigmergy preference trails for assignment optimization.

**Pattern (Swarm Intelligence):**
- Individual agents follow pheromone trails
- Strong trails indicate consistent preference/avoidance
- Collective optimization emerges from local signals

**Trail Thresholds:**
- `STRONG_TRAIL_THRESHOLD = 0.6`: Strong signal
- `WEAK_TRAIL_THRESHOLD = 0.3`: Ignore

**Implementation:**
```python
***REMOVED*** Slot type derived from block: "monday_am", "friday_pm", etc.
slot_type = f"{block.date.strftime('%A').lower()}_{block.time_of_day.lower()}"

***REMOVED*** Trail strength determines bonus/penalty
if trail_strength >= 0.6:  ***REMOVED*** Preference
    bonus = (trail_strength - 0.5) × 20
elif trail_strength <= 0.4:  ***REMOVED*** Avoidance
    penalty = (0.5 - trail_strength) × 20
```

***REMOVED******REMOVED******REMOVED*** 7. N1VulnerabilityConstraint

`backend/app/scheduling/constraints.py`

Prevents schedules that create single points of failure.

**Pattern (Power Grid N-1):**
- System must survive loss of any single component
- No service should depend on exactly one faculty member
- Redundancy improves resilience

**Implementation:**
- Penalizes blocks with only 1-2 available faculty
- Scarcity factor: 1 available = 2x penalty, 2 available = 1x penalty
- Reports sole providers (faculty who are only coverage for multiple blocks)

**Violation Example:**
```json
{
    "constraint_name": "N1Vulnerability",
    "severity": "HIGH",
    "message": "15 blocks have single-point-of-failure coverage (12%)",
    "details": {
        "n1_vulnerable_blocks": 15,
        "vulnerability_rate": 0.12,
        "sole_provider_counts": {"faculty_1_id": 8, "faculty_2_id": 7},
        "n1_pass": false
    }
}
```

***REMOVED******REMOVED*** Configuration Reference

***REMOVED******REMOVED******REMOVED*** ResilienceConfig

```python
@dataclass
class ResilienceConfig:
    ***REMOVED*** Tier 1: Utilization thresholds
    max_utilization: float = 0.80
    warning_threshold: float = 0.70

    ***REMOVED*** Hub Analysis settings
    hub_threshold: float = 0.4           ***REMOVED*** Score to be considered a hub
    critical_hub_threshold: float = 0.6  ***REMOVED*** Score for critical hub status
```

***REMOVED******REMOVED******REMOVED*** Constraint Weights (Defaults)

| Constraint | Weight | Priority | Tier | Effect |
|------------|--------|----------|------|--------|
| CoverageConstraint | 1000.0 | HIGH | - | Maximize block coverage |
| N1VulnerabilityConstraint | 25.0 | HIGH | 2 | Prevent single points of failure |
| UtilizationBufferConstraint | 20.0 | HIGH | 1 | Maintain 20% buffer |
| HubProtectionConstraint | 15.0 | MEDIUM | 1 | Protect critical faculty |
| ZoneBoundaryConstraint | 12.0 | MEDIUM | 2 | Contain failures to zones |
| EquityConstraint | 10.0 | MEDIUM | - | Balance workload |
| PreferenceTrailConstraint | 8.0 | LOW | 2 | Follow learned preferences |
| ContinuityConstraint | 5.0 | LOW | - | Minimize rotation changes |

***REMOVED******REMOVED******REMOVED*** Factory Methods

```python
***REMOVED*** Backward compatible (all resilience constraints disabled)
ConstraintManager.create_default()

***REMOVED*** Tier 1 only (hub protection, utilization buffer)
ConstraintManager.create_resilience_aware(tier=1)

***REMOVED*** Full resilience (Tier 1 + Tier 2)
ConstraintManager.create_resilience_aware(tier=2)  ***REMOVED*** default

***REMOVED*** Custom utilization target
ConstraintManager.create_resilience_aware(target_utilization=0.75)
```

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

---

***REMOVED******REMOVED*** Tier 2 Reflection: What Works, What Doesn't Translate

***REMOVED******REMOVED******REMOVED*** Successfully Integrated into Constraints

| Resilience Concept | Constraint | Integration Quality |
|-------------------|------------|---------------------|
| Hub Vulnerability (Network Theory) | HubProtectionConstraint | ✅ Excellent - direct translation |
| 80% Utilization (Queuing Theory) | UtilizationBufferConstraint | ✅ Excellent - direct translation |
| Blast Radius Isolation (AWS) | ZoneBoundaryConstraint | ✅ Good - requires zone setup |
| Stigmergy Trails (Swarm Intelligence) | PreferenceTrailConstraint | ✅ Good - requires trail history |
| N-1 Contingency (Power Grid) | N1VulnerabilityConstraint | ✅ Good - works without pre-analysis |

***REMOVED******REMOVED******REMOVED*** Resilience Features That Don't Translate to Constraints

Some resilience concepts from the framework don't fit the constraint-based optimization model:

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Homeostasis/Feedback Loops (Biology)

**Why it doesn't translate:**
- Operates across multiple scheduling runs, not within a single solve
- Involves tracking deviation from setpoints over time
- Requires adjusting weights/targets between runs, not during optimization

**Better integration approach:**
```python
***REMOVED*** Meta-scheduler that adjusts constraint weights between runs
class HomeostasisAdjuster:
    def adjust_for_next_run(self, health_history):
        ***REMOVED*** If coverage consistently low, increase CoverageConstraint weight
        ***REMOVED*** If burnout indicators high, increase UtilizationBuffer threshold
        ***REMOVED*** This adjusts inputs TO the solver, not the solver itself
        pass
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Le Chatelier's Principle (Chemistry)

**Why it doesn't translate:**
- Models stress response and compensation debt over time
- Predicts equilibrium shifts, doesn't constrain solutions
- Better suited for advisory/prediction than optimization

**Better integration approach:**
```python
***REMOVED*** Post-solve advisory: "This schedule requires X compensation,
***REMOVED*** which will create Y burnout debt by month-end"
class EquilibriumAdvisor:
    def assess_schedule(self, assignments):
        stress = calculate_applied_stress(assignments)
        compensation = stress * 0.5  ***REMOVED*** Partial compensation
        debt = compensation * 1.5  ***REMOVED*** Cost of compensation
        return SustainabilityReport(stress, compensation, debt)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Cognitive Load Management (Psychology)

**Why it doesn't translate:**
- Affects UI/workflow, not the optimization algorithm
- Operates on human decision-making, not solver decisions
- Miller's Law limits apply to coordinators, not software

**Better integration approach:**
```python
***REMOVED*** Limit manual decisions presented to coordinators
***REMOVED*** Batch schedule changes for approval
***REMOVED*** Provide smart defaults with one-click accept
***REMOVED*** This wraps the scheduler, doesn't change its behavior
```

***REMOVED******REMOVED******REMOVED*** Key Insight: Constraint vs. Advisory vs. Meta-Control

| Type | When Applied | Example |
|------|--------------|---------|
| **Constraint** | During single solve | HubProtectionConstraint |
| **Advisory** | After solve (validation) | Le Chatelier equilibrium analysis |
| **Meta-Control** | Between solves | Homeostasis weight adjustment |

---

***REMOVED******REMOVED*** Tier 3 Preparation: What's Next

***REMOVED******REMOVED******REMOVED*** Tier 3 Constraint Candidates

Based on analysis, these could be implemented as constraints:

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. AllostasisConstraint (Cumulative Stress)

**Concept:** Track faculty cumulative stress ("allostatic load") and penalize
assignments that push individuals into burnout risk.

```python
class AllostasisConstraint(SoftConstraint):
    """
    Prevents assigning overloaded faculty.

    Allostasis (biology): Cumulative wear and tear from chronic stress.
    Unlike acute stress, allostatic load accumulates and doesn't reset.

    Implementation:
    - Track rolling stress score per faculty
    - Penalize assignments to high-allostasis individuals
    - Encourage recovery time for stressed faculty
    """

    def validate(self, assignments, context):
        for faculty_id, allostatic_load in context.allostatic_loads.items():
            if allostatic_load > self.BURNOUT_THRESHOLD:
                ***REMOVED*** Penalize any assignments to this faculty
                pass
```

**Data needed in SchedulingContext:**
- `allostatic_loads: dict[UUID, float]` - Cumulative stress per faculty
- `recovery_requirements: dict[UUID, int]` - Days off needed

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. EquilibriumShiftConstraint (Le Chatelier Integration)

**Concept:** Penalize schedules that create unsustainable compensation demands.

```python
class EquilibriumShiftConstraint(SoftConstraint):
    """
    Penalizes schedules requiring excessive compensation.

    Le Chatelier: Systems under stress partially compensate,
    but compensation has costs (overtime, burnout debt).

    Implementation:
    - Calculate compensation required for schedule
    - Penalize if compensation_debt exceeds sustainable threshold
    """

    def validate(self, assignments, context):
        compensation_debt = calculate_compensation_debt(assignments, context)
        if compensation_debt > context.sustainable_compensation_limit:
            ***REMOVED*** High penalty for unsustainable schedules
            pass
```

**Data needed in SchedulingContext:**
- `baseline_capacity: float` - Normal capacity before stress
- `sustainable_compensation_limit: float` - Max acceptable debt

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. DecisionComplexityConstraint (Cognitive Load Proxy)

**Concept:** Penalize schedules that are hard for humans to understand/manage.

```python
class DecisionComplexityConstraint(SoftConstraint):
    """
    Penalizes overly complex schedules.

    Cognitive psychology: Complexity increases coordinator burden.
    Simple, predictable schedules reduce decision fatigue.

    Implementation:
    - Penalize excessive pattern changes
    - Reward consistent assignments
    - Penalize exceptions and special cases
    """

    def validate(self, assignments, context):
        complexity_score = calculate_schedule_complexity(assignments)
        ***REMOVED*** Changes per week, exceptions, pattern breaks, etc.
        if complexity_score > self.SIMPLICITY_TARGET:
            ***REMOVED*** Penalty proportional to excess complexity
            pass
```

**Data needed in SchedulingContext:**
- `pattern_expectations: dict` - Expected regular patterns
- `exception_count_limit: int` - Max tolerable exceptions

***REMOVED******REMOVED******REMOVED*** Meta-Control Systems (Between Solves)

These would wrap the scheduler, not be constraints:

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. HomeostasisController

```python
class HomeostasisController:
    """
    Adjusts constraint weights between scheduling runs based on
    historical deviation from setpoints.

    Runs BEFORE generate(), modifies constraint_manager weights.
    """

    def adjust_weights(self, constraint_manager, health_history):
        ***REMOVED*** If coverage consistently below target, increase weight
        coverage_trend = analyze_trend(health_history, 'coverage')
        if coverage_trend < -0.05:  ***REMOVED*** 5% below setpoint trending down
            coverage_constraint = constraint_manager.get("Coverage")
            coverage_constraint.weight *= 1.1  ***REMOVED*** 10% increase

        ***REMOVED*** If utilization consistently high, lower threshold
        util_trend = analyze_trend(health_history, 'utilization')
        if util_trend > 0.85:  ***REMOVED*** Trending above buffer
            util_constraint = constraint_manager.get("UtilizationBuffer")
            util_constraint.target_utilization -= 0.05  ***REMOVED*** Tighten buffer
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. CognitiveLoadBatcher

```python
class CognitiveLoadBatcher:
    """
    Batches schedule changes to reduce coordinator cognitive load.

    Runs AFTER generate(), before presenting to user.
    """

    MAX_DECISIONS_PER_BATCH = 7  ***REMOVED*** Miller's Law

    def batch_for_review(self, changes):
        ***REMOVED*** Group similar changes
        ***REMOVED*** Prioritize by impact
        ***REMOVED*** Provide smart defaults
        ***REMOVED*** Return digestible batches
        pass
```

***REMOVED******REMOVED******REMOVED*** Data Pipeline for Tier 3

To enable Tier 3 constraints, the following data needs to flow from ResilienceService to SchedulingContext:

```
ResilienceService
├── homeostasis.py
│   └── get_allostatic_loads(faculty) → dict[UUID, float]
│   └── get_recovery_requirements(faculty) → dict[UUID, int]
│
├── le_chatelier.py
│   └── get_baseline_capacity() → float
│   └── get_compensation_debt() → float
│
├── cognitive_load.py
│   └── get_decision_budget() → int (remaining decisions)
│   └── get_complexity_limit() → float
│
└── → SchedulingContext (extended)
        + allostatic_loads
        + recovery_requirements
        + baseline_capacity
        + compensation_debt
        + decision_complexity_limit
```

***REMOVED******REMOVED******REMOVED*** Implementation Priority for Tier 3

| Feature | Impact | Complexity | Priority |
|---------|--------|------------|----------|
| AllostasisConstraint | High (prevents burnout) | Medium | 1 |
| HomeostasisController | High (adaptive scheduling) | Medium | 2 |
| EquilibriumShiftConstraint | Medium (sustainability) | Low | 3 |
| CognitiveLoadBatcher | Medium (UX improvement) | Medium | 4 |
| DecisionComplexityConstraint | Low (nice-to-have) | Low | 5 |

---

***REMOVED******REMOVED*** Current Implementation Status

***REMOVED******REMOVED******REMOVED*** Completed (Tier 1 + Tier 2)

| Feature | Status | Location |
|---------|--------|----------|
| SchedulingContext resilience fields | ✅ Complete | `constraints.py` |
| HubProtectionConstraint | ✅ Complete | `constraints.py` |
| UtilizationBufferConstraint | ✅ Complete | `constraints.py` |
| ZoneBoundaryConstraint | ✅ Complete | `constraints.py` |
| PreferenceTrailConstraint | ✅ Complete | `constraints.py` |
| N1VulnerabilityConstraint | ✅ Complete | `constraints.py` |
| Data population in engine | ✅ Complete | `engine.py` |
| Auto-enable constraints | ✅ Complete | `engine.py` |
| Factory methods | ✅ Complete | `constraints.py` |

***REMOVED******REMOVED******REMOVED*** Ready for Tier 3

- [ ] AllostasisConstraint
- [ ] EquilibriumShiftConstraint
- [ ] DecisionComplexityConstraint
- [ ] HomeostasisController (meta-control)
- [ ] CognitiveLoadBatcher (post-processing)
