# Resilience Framework: Sacrifice Hierarchy (Triage Medicine Load Shedding)

## Document Information
- **Status**: Complete reconnaissance findings
- **Search Party Operation**: G2_RECON
- **Target**: Sacrifice hierarchy (triage) system
- **Source Code**: `backend/app/resilience/sacrifice_hierarchy.py`
- **Integration Point**: `backend/app/resilience/service.py`
- **Last Updated**: 2025-12-30

---

## Executive Summary

The Sacrifice Hierarchy is a **pre-made triage system** that removes crisis decision burden during medical scheduling emergencies. Rather than making difficult prioritization decisions in-the-moment (when stress impairs judgment), the system codifies explicit priorities beforehand.

**Core Philosophy:**
> "Decisions made during crisis are worse than decisions made beforehand. Having an explicit hierarchy removes guilt, politics, and cognitive load from crisis decision-making."

**Key Innovation**: Activities are sacrificed based on pre-established priority order, not ad-hoc politicking. Services restored in reverse sacrifice order when capacity returns.

---

## Triage Level Definitions

### LoadSheddingLevel Enum (Severity Scale)

```python
class LoadSheddingLevel(IntEnum):
    """Load shedding severity levels (0-5 scale)."""

    NORMAL = 0          # No shedding - all activities running
    YELLOW = 1          # Suspend optional education only
    ORANGE = 2          # Also suspend admin and research
    RED = 3             # Also suspend core education
    BLACK = 4           # Essential services only (patient safety + ACGME minimum)
    CRITICAL = 5        # Patient safety only (absolute extreme)
```

### Activity Category Hierarchy (Protection Priority)

```python
class ActivityCategory(IntEnum):
    """Activity categories in order of protection priority.

    Lower number = higher priority = more protected = never sacrificed first.
    """

    PATIENT_SAFETY = 1         # ICU coverage, OR staffing, trauma response
    ACGME_REQUIREMENTS = 2      # Minimum case numbers, required rotations
    CONTINUITY_OF_CARE = 3      # Clinic follow-ups, chronic disease management
    EDUCATION_CORE = 4          # Didactics, simulation labs
    RESEARCH = 5                # Studies, publications, grants
    ADMINISTRATION = 6          # Meetings, committees, paperwork
    EDUCATION_OPTIONAL = 7      # Conferences, electives, enrichment
```

**Key Principle**: Categories are NEVER sacrificed out of order. If you're at RED level and need to cut activities, you've already cut everything in EDUCATION_OPTIONAL, ADMINISTRATION, RESEARCH, and EDUCATION_CORE—and now you're cutting CONTINUITY_OF_CARE.

---

## Triage Decision Framework

### Load Shedding Decision Tree

```
System Load Analysis
│
├─ NORMAL (< 70% utilization)
│  └─ Continue all activities (no shedding)
│
├─ YELLOW (70-80% utilization)
│  └─ Suspend: EDUCATION_OPTIONAL
│     Keep: Everything else
│
├─ ORANGE (80-90% utilization)
│  └─ Suspend: EDUCATION_OPTIONAL, ADMINISTRATION, RESEARCH
│     Keep: Patient safety, ACGME, Continuity, Core education
│
├─ RED (90-95% utilization)
│  └─ Suspend: Optional ed, Admin, Research, CORE EDUCATION
│     Keep: Patient safety, ACGME, Continuity only
│
├─ BLACK (95-100% utilization)
│  └─ Suspend: Everything except patient safety + ACGME minimum
│     Essential services only
│
└─ CRITICAL (100%+ utilization / system failure)
   └─ Patient safety only
      Emergency protocols, external support activation
```

### Priority Calculation Algorithm

```python
def calculate_required_level(
    current_capacity: float,      # Available faculty-hours
    required_capacity: float,      # Required faculty-hours for all activities
) -> LoadSheddingLevel:
    """Calculate minimum level needed to fit demand within capacity."""

    if current_capacity >= required_capacity:
        return LoadSheddingLevel.NORMAL

    # Iterate through levels, finding first one where demand fits capacity
    for level in [YELLOW, ORANGE, RED, BLACK, CRITICAL]:
        remaining_hours = sum(
            a.faculty_hours
            for a in activities
            if a.category not in sacrificed_categories_at_level(level)
        )

        if remaining_hours <= current_capacity:
            return level

    return LoadSheddingLevel.CRITICAL
```

### Activity Sacrifice Order (Within Category)

When multiple activities exist in a category that must be cut, they're removed in this order:

1. **Optional activities first** (conferences, electives)
2. **Meetings/committees** before direct service
3. **Smaller commitments before larger ones** (5-hour task before 20-hour task)
4. **Non-required before required** (optional rotation before mandatory)

```python
# Sorting logic from shed_load() method
sorted_activities = sorted(
    current_demand,
    key=lambda a: (
        a.category.value,        # Higher category = less protected
        not a.is_required,        # Non-required first
        a.faculty_hours,          # Smaller commitments first
    ),
    reverse=True,                 # So we pop from end (least protected first)
)
```

---

## Core Data Structures

### Activity Class

```python
@dataclass
class Activity:
    """An activity that can be scheduled."""

    id: UUID                        # Unique identifier
    name: str                       # Human-readable name (e.g., "Morning Clinic")
    category: ActivityCategory      # Priority tier
    faculty_hours: float            # Required faculty hours
    is_required: bool = False       # Can it be deferred?
    min_frequency: str | None       # e.g., "weekly", "monthly"
    can_be_deferred: bool = True    # Whether deferral is allowed
    deferral_limit_days: int = 30   # Max days it can be deferred
```

### LoadSheddingStatus Class (Current State)

```python
@dataclass
class LoadSheddingStatus:
    """Current load shedding status."""

    level: LoadSheddingLevel                # Current level (NORMAL, YELLOW, etc.)
    level_name: str                         # Human-readable name
    active_since: datetime | None           # When this level was activated
    activities_suspended: list[str]         # Names of suspended activities
    activities_protected: list[str]         # Names still running
    current_coverage: float                 # Faculty-hours allocated
    target_coverage: float                  # Faculty-hours needed
    decisions_log: list[SacrificeDecision]  # Audit trail (last 10)
```

### SacrificeDecision Class (Audit Trail)

```python
@dataclass
class SacrificeDecision:
    """Record of a sacrifice decision for compliance audit trail."""

    timestamp: datetime             # When decision was made
    level: LoadSheddingLevel        # What level was activated
    activities_suspended: list[str] # What was cut
    reason: str                     # Why this decision was made
    coverage_before: float          # Capacity before shedding
    coverage_after: float           # Capacity after shedding
    approved_by: str | None         # Who authorized this
    notes: str = ""                 # Additional context
```

---

## Method Reference

### Primary Methods

#### `shed_load()` - Main Load Shedding Function

```python
def shed_load(
    self,
    current_demand: list[Activity],
    available_capacity: float,
    reason: str = "",
    approved_by: str | None = None,
) -> tuple[list[Activity], list[Activity]]:
    """
    Remove activities until demand fits capacity.

    Args:
        current_demand: List of Activity objects needing coverage
        available_capacity: Available faculty-hours for the period
        reason: Reason for shedding (recorded for audit trail)
        approved_by: Person approving the decision

    Returns:
        tuple: (kept_activities, sacrificed_activities)

    Example:
        >>> hierarchy = SacrificeHierarchy()
        >>> kept, sacrificed = hierarchy.shed_load(
        ...     current_demand=activities,
        ...     available_capacity=100.0,
        ...     reason="PCS season understaffing",
        ...     approved_by="Dr. Chief"
        ... )
        >>> print(f"Suspended {len(sacrificed)} activities, freeing "
        ...       f"{sum(a.faculty_hours for a in sacrificed)} hours")
    """
```

**Algorithm**:
1. Sort activities by sacrifice priority
2. Build "kept" list from most protected up
3. Everything that doesn't fit goes to "sacrificed"
4. Log decision with reason and approval
5. Return both lists

#### `activate_level()` - Escalate Triage Level

```python
def activate_level(
    self,
    level: LoadSheddingLevel,
    reason: str = "",
    approved_by: str | None = None,
) -> None:
    """
    Activate a specific load shedding level.

    This suspends all activities in sacrificed categories.

    Example:
        >>> hierarchy.activate_level(
        ...     LoadSheddingLevel.ORANGE,
        ...     reason="Multiple faculty out with flu",
        ...     approved_by="Dr. Chief"
        ... )
    """
```

#### `deactivate_level()` - Reduce Triage Level (Recovery)

```python
def deactivate_level(
    self,
    to_level: LoadSheddingLevel = LoadSheddingLevel.NORMAL
) -> None:
    """
    Reduce load shedding level and restore services.

    Services restored in reverse sacrifice order
    (most important first).
    """
```

#### `get_recovery_plan()` - Recovery Roadmap

```python
def get_recovery_plan(self) -> list[dict]:
    """
    Get plan for recovering from current load shedding level.

    Returns activities in priority order for restoration.

    Returns:
        list[dict]: Each item contains:
            - activity: Activity name
            - category: Activity category name
            - hours_required: Faculty hours to restore
            - can_defer_further: Whether it can be delayed more
            - max_deferral_days: Maximum postponement days
    """
```

#### `calculate_required_level()` - Automatic Level Selection

```python
def calculate_required_level(
    self,
    current_capacity: float,
    required_capacity: float,
) -> LoadSheddingLevel:
    """
    Calculate the minimum level needed to fit demand within capacity.

    Returns the least severe triage level that would allow
    all remaining activities to fit in available capacity.
    """
```

#### `get_status()` - Current State Snapshot

```python
def get_status(self) -> LoadSheddingStatus:
    """Get current load shedding status."""
```

#### `get_category_summary()` - Category Breakdown

```python
def get_category_summary(self) -> dict[str, dict]:
    """Get summary of activities by category."""
```

---

## Ethical Considerations

### Design Philosophy: Removing Guilt and Politics

**Problem**: When a crisis hits and you need to cut activities, that's when leadership is most stressed and decisions are worst. Emotions run high. Politics enter. Guilt clouds judgment.

**Solution**: Make these decisions ahead of time, in calm reflection, with broad input. Then when crisis hits, execute the pre-made plan. This:

1. **Removes politics** - "We decided this in advance, not picking favorites now"
2. **Reduces guilt** - "We did what we planned, not making exceptions"
3. **Improves decisions** - Made with clear head, not under stress
4. **Ensures fairness** - Everyone knows the rules beforehand
5. **Speeds response** - No committee meetings during crisis

### Key Ethical Constraints

**NEVER sacrifice**:
- Patient safety (life-or-death care)
- ACGME accreditation requirements (program survival)

**CAN sacrifice** (in order):
1. Optional professional development
2. Administrative work
3. Research
4. Required education
5. Routine patient follow-ups (if emergency care maintained)

**NEVER sacrifice the decision-making process itself**:
- All sacrifices must be logged
- Reason recorded
- Authority captured
- Audit trail maintained
- Recovery plan documented

---

## Integration with Resilience Service

### Connection to Defense in Depth

The Sacrifice Hierarchy is the **load shedding component** of Defense in Depth:

```python
# From resilience/service.py

if severity == "minor":
    self.defense.activate_action(DefenseLevel.CONTROL, "early_warning")
    self.sacrifice.activate_level(LoadSheddingLevel.YELLOW, reason)
    # Result: Suspend optional education

elif severity == "moderate":
    self.defense.activate_action(DefenseLevel.SAFETY_SYSTEMS, "auto_reassignment")
    self.sacrifice.activate_level(LoadSheddingLevel.ORANGE, reason)
    # Result: Suspend admin, research, optional education

elif severity == "severe":
    self.defense.activate_action(DefenseLevel.CONTAINMENT, "service_reduction")
    self.sacrifice.activate_level(LoadSheddingLevel.RED, reason)
    # Result: Suspend all non-clinical education

elif severity == "critical":
    self.defense.activate_action(DefenseLevel.EMERGENCY, "crisis_communication")
    self.sacrifice.activate_level(LoadSheddingLevel.BLACK, reason)
    # Result: Essential services only
```

### Usage in Crisis Response

```python
# From resilience/service.py - activate_crisis_response()

def activate_crisis_response(
    self,
    severity: str = "moderate",  # "minor", "moderate", "severe", "critical"
    reason: str = "",
) -> dict:
    """Activate crisis response mode with automatic load shedding."""

    # Self-determines which triage level based on severity
    # Sacrifices activities accordingly
    # Logs all decisions
    # Returns recovery plan
```

---

## Difficult Decisions Philosophy

### The Nature of Triage

Triage in emergency medicine is fundamentally about choosing who gets help first when help is limited. The sacrifice hierarchy is medical scheduling's version of triage.

**Real-world emergency room triage**:
```
GREEN   - Walking wounded, non-urgent
YELLOW  - Delayed injuries, can wait
RED     - Life-threatening, immediate care
BLACK   - Deceased or expectant
```

**Scheduling triage**:
```
NORMAL    - All activities running
YELLOW    - Cut optional enrichment
ORANGE    - Cut admin and research too
RED       - Cut core education too
BLACK     - Patient safety + accreditation only
CRITICAL  - Patient safety only
```

### Uncomfortable Truths

1. **Some activities WILL be cut** - There's no avoiding this in crisis
2. **Cutting education hurts residents** - But letting patient safety fail hurts worse
3. **Decisions require authority** - Pre-approval removes blame-shifting
4. **Logistics are political** - Transparency prevents worse politics later

### Transparency as Ethical Requirement

Each sacrifice decision includes:
- **Who** authorized it (accountability)
- **When** it happened (timeline)
- **Why** it was necessary (justification)
- **What** will be restored and when (recovery plan)

This creates an audit trail defensible to:
- Residents ("Here's why your education was affected")
- Accreditors ("Here's how we managed compliance during crisis")
- Patients ("Here's how we prioritized safety")

---

## Activation Procedures

### Manual Activation (Administrator)

```python
hierarchy = SacrificeHierarchy()

# Register activities
for activity in all_activities:
    hierarchy.register_activity(activity)

# Activate a level (e.g., during flu outbreak)
hierarchy.activate_level(
    LoadSheddingLevel.ORANGE,
    reason="Multiple faculty out with influenza",
    approved_by="Dr. Julie Chen, Chief"
)

# Check status
status = hierarchy.get_status()
print(f"Currently at level: {status.level_name}")
print(f"Suspended activities: {status.activities_suspended}")
print(f"Coverage reduced from {status.target_coverage}h to {status.current_coverage}h")
```

### Automatic Activation (Resilience Service)

```python
# From resilience/service.py
resilience_service = ResilienceService(db)

# Service automatically determines level based on capacity/demand
kept, sacrificed = resilience_service.sacrifice.shed_load(
    current_demand=all_activities,
    available_capacity=current_faculty_hours,
    reason="PCS season understaffing: 3 faculty departing",
    approved_by="Dr. Program Director"
)

# Get recovery roadmap
recovery = resilience_service.sacrifice.get_recovery_plan()
```

### Recovery Procedure

```python
# After capacity returns (new faculty arrives)
hierarchy.deactivate_level(LoadSheddingLevel.NORMAL)

# Services restored in reverse order:
# 1. Optional education (highest priority, restored first)
# 2. Administration
# 3. Research
# 4. Core education
# 5. Everything else
```

---

## Undocumented Patterns and Edge Cases

### Hidden Complexity: Deferred vs. Sacrificed

The code distinguishes between activities that are **deferred** (can come back) vs. **sacrificed** (gone for this period):

```python
# Each Activity has:
can_be_deferred: bool = True        # Can this be rescheduled?
deferral_limit_days: int = 30       # How long can we defer?
```

Conference attendance might be deferrable (move to next month). Emergency OR coverage is not deferrable.

### Inter-Category Dependencies

**Not explicitly modeled**: Activities in lower categories sometimes depend on activities in higher categories. Example:
- "Resident didactic lecture" (EDUCATION_CORE) depends on
- "Faculty prep time" (ADMINISTRATION)

If you cut administration, some education might become impossible anyway.

### Temporal Aspects

**Not explicitly modeled**: Some activities have **deadline constraints**:
- Required certification exams (must happen by specific date)
- Compliance trainings (annual deadline)
- Accreditation site visits (scheduled, can't be deferred)

Cutting education might delay these, creating cascading problems.

### Category Conflicts

Some activities span multiple categories:
- "Grand rounds" = EDUCATION_CORE + CONTINUITY_OF_CARE
- "QI project" = RESEARCH + ADMINISTRATION
- "Simulation lab" = EDUCATION_CORE + PATIENT_SAFETY

Which category determines its protection level? **Current answer**: The primary_category field (if present), otherwise the explicit category.

---

## Implementation Status and Testing

### Code Location
- **Main implementation**: `/backend/app/resilience/sacrifice_hierarchy.py` (493 lines)
- **Integration**: `/backend/app/resilience/service.py` (lines 103-106, 273, 402, 444, etc.)
- **API routes**: `/backend/app/api/routes/resilience.py`
- **Schemas**: `/backend/app/schemas/resilience.py`

### Test Coverage
- Unit tests: `backend/tests/test_resilience.py` (covers SacrificeHierarchy)
- Integration tests: `backend/tests/test_resilience_routes_full.py`
- Load tests: `backend/tests/resilience/test_resilience_load.py`

### Current Limitations

1. **No temporal modeling** - Activities are snapshot, not timeline
2. **No dependency tracking** - Inter-activity dependencies not modeled
3. **No cost-benefit analysis** - Just priority order, not trade-off analysis
4. **Static categories** - Categories hardcoded, not configurable per program
5. **No override mechanism** - Can't temporarily elevate category during crisis

---

## Cross-Disciplinary Foundation

### Source Domain: Emergency Medicine Triage

The Sacrifice Hierarchy directly applies **emergency medicine triage principles**:

| Concept | Emergency Room | Scheduling |
|---------|---|---|
| **Triage** | Rapid assessment of patient acuity | Rapid assessment of system stress |
| **Categories** | GREEN/YELLOW/RED/BLACK | NORMAL/YELLOW/ORANGE/RED/BLACK |
| **Sorting** | By urgency/severity | By category value |
| **Decision** | Pre-trained algorithms, not ad-hoc | Pre-made hierarchy, not political |
| **Authority** | Triage nurse decision | Program director decision |
| **Documentation** | Audit trail for legal protection | Audit trail for accreditation |
| **Ethics** | "Greatest good for greatest number" | "Patient safety first, then accreditation" |

### Philosophical Foundation: Utilitarianism Under Constraint

The sacrifice hierarchy embodies **utilitarian triage ethics**:

1. **Maximize total welfare** under constraint
2. **Transparent criteria** rather than hidden politics
3. **Pre-commitment** to rules avoids in-the-moment bias
4. **Protection of essentials** (life safety, program viability)
5. **Documented reasoning** for accountability

---

## Frequently Asked Questions

### Q: What if cutting optional education causes residents to fail boards?
**A**: That's a legitimate concern. The hierarchy assumes core education continues at RED level. If cutting core education becomes necessary, that's when you're at RED level—explicitly indicating a severe crisis.

### Q: Can we add exceptions to the hierarchy?
**A**: The current implementation doesn't support exceptions. Adding exceptions would reintroduce the political favoritism the hierarchy was designed to eliminate.

### Q: How long can we run at RED/BLACK level?
**A**: This depends on program factors. Core education gaps accumulate. Training debt is tracked but not formally modeled in current code.

### Q: What if resident wellbeing requires protecting research time?
**A**: The hierarchy prioritizes patient safety and accreditation. Resident wellbeing (research time, admin relief) comes after those two. This reflects medical ethics hierarchy.

### Q: Can we use this to justify cutting resident safety training?
**A**: No. Safety training (ACGME requirement) is protected until BLACK level. Patient care training is protected until CRITICAL. Only in true CRITICAL crisis would this be considered.

---

## Recommendations for Enhancement

### Tier 1: Immediate (High Priority)

1. **Add temporal constraints** - Track activity deadlines and non-deferrability windows
2. **Model dependencies** - When activity X depends on activity Y, prevent cutting Y before X
3. **Add cost-benefit configuration** - Allow programs to override category order (with approval logging)

### Tier 2: Strategic (Medium Priority)

4. **Integrate with scheduling solver** - Automatically generate optimal shed_load() calls during schedule generation failures
5. **Track cumulative impact** - Monitor how long categories have been suspended for training debt analysis
6. **Predictive activation** - Forecast need for load shedding based on upcoming absences

### Tier 3: Advanced (Lower Priority)

7. **Machine learning calibration** - Learn optimal sacrifice order from program-specific outcomes
8. **Game theory analysis** - Model incentive effects of different hierarchies on resident behavior
9. **Fairness auditing** - Detect if sacrifice decisions systematically disadvantage certain groups

---

## Conclusion

The Sacrifice Hierarchy is a **decision catalyst** that removes crisis decision-making from the moment of crisis. By pre-establishing priorities, documenting authority, and maintaining audit trails, it enables transparent, defensible load shedding that protects both patient safety and program accreditation while explicitly managing the difficult tradeoffs that crises require.

**The core insight**: *The best time to make hard decisions is before you need to make them.*

