# Constraint Interaction Matrix

Comprehensive reference for understanding constraint relationships, priorities, conflicts, and recommended configurations in the Residency Scheduler constraint system.

> **Last Updated:** 2025-12-30
> **Purpose:** Technical reference for constraint interactions and configuration
> **Related:** [SOLVER_ALGORITHM.md](SOLVER_ALGORITHM.md), [FACULTY_SCHEDULING_SPECIFICATION.md](FACULTY_SCHEDULING_SPECIFICATION.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Constraint Catalog](#constraint-catalog)
3. [Priority Hierarchy](#priority-hierarchy)
4. [Constraint Interactions](#constraint-interactions)
5. [Conflict Resolution](#conflict-resolution)
6. [Configuration Patterns](#configuration-patterns)
7. [Dependency Graph](#dependency-graph)
8. [Weight Tuning Guide](#weight-tuning-guide)
9. [Common Issues](#common-issues)
10. [Constraint Debugging](#constraint-debugging)

---

## Overview

The Residency Scheduler uses a **modular, composable constraint system** with 35+ constraints organized into hard constraints (must be satisfied) and soft constraints (optimization objectives).

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Hard Constraint** | Must be satisfied for valid schedule (ACGME rules, availability, capacity) |
| **Soft Constraint** | Optimization objective with weight (equity, preferences, resilience) |
| **Priority** | Determines application order: CRITICAL(100) > HIGH(75) > MEDIUM(50) > LOW(25) |
| **Weight** | Soft constraint penalty multiplier (higher = more important) |
| **Context** | SchedulingContext bundle with all data needed for constraint evaluation |

### Architecture

```
ConstraintManager
    ├── Hard Constraints (17 in default config)
    │   ├── ACGME Compliance (4)
    │   ├── Availability & Capacity (7)
    │   ├── Temporal Rules (3)
    │   └── Faculty/FMIT Rules (3+)
    └── Soft Constraints (14 in default config)
        ├── Coverage & Equity (4)
        ├── Call Equity (4)
        ├── Faculty Preferences (1)
        └── Resilience (5 - Tier 1&2)
```

---

## Constraint Catalog

### ACGME Compliance Constraints (Hard)

| Constraint | Priority | Type | Description |
|------------|----------|------|-------------|
| `AvailabilityConstraint` | CRITICAL | AVAILABILITY | Enforces absence tracking - no assignments during blocking absences |
| `EightyHourRuleConstraint` | CRITICAL | DUTY_HOURS | Max 80 hours/week, rolling 4-week average (53 blocks per 28 days) |
| `OneInSevenRuleConstraint` | CRITICAL | CONSECUTIVE_DAYS | At least 1 day off per 7 days (max 6 consecutive duty days) |
| `SupervisionRatioConstraint` | CRITICAL | SUPERVISION | PGY-1: 1:2 faculty ratio, PGY-2/3: 1:4 faculty ratio |

**Key Characteristics:**
- All have CRITICAL priority (100)
- Violations make schedule invalid/non-compliant
- Cannot be disabled
- Applied first in solver

**Interactions:**
- `AvailabilityConstraint` can conflict with `CoverageConstraint` (soft) if too many absences
- `EightyHourRuleConstraint` limits `EquityConstraint` effectiveness (some residents may have target blocks that violate 80hr)
- `SupervisionRatioConstraint` is typically enforced post-hoc (not in solver)

---

### Capacity & Coverage Constraints

| Constraint | Type | Priority | Weight | Description |
|------------|------|----------|--------|-------------|
| `OnePersonPerBlockConstraint` | Hard | CRITICAL | N/A | At most 1 primary resident per block |
| `ClinicCapacityConstraint` | Hard | HIGH | N/A | Respects rotation template max_residents limits |
| `MaxPhysiciansInClinicConstraint` | Hard | HIGH | N/A | Physical space limit (default: 6 physicians per clinic session) |
| `CoverageConstraint` | Soft | HIGH | 1000.0 | Maximize number of covered blocks (primary objective) |

**Key Characteristics:**
- `CoverageConstraint` has highest weight (1000.0) - dominates objective function
- Physical constraints (capacity, space) are non-negotiable

**Interactions:**
- `CoverageConstraint` competes with all soft constraints
- `ClinicCapacityConstraint` can limit `EquityConstraint` (if templates are saturated)
- `MaxPhysiciansInClinicConstraint` affects faculty supervision assignments

---

### Temporal Constraints (Hard)

| Constraint | Priority | Type | Description |
|------------|----------|------|-------------|
| `WednesdayAMInternOnlyConstraint` | HIGH | ROTATION | Wednesday AM clinic reserved for PGY-1 continuity |
| `WednesdayPMSingleFacultyConstraint` | HIGH | CAPACITY | Wednesday PM limited to 1 faculty for academic half-day |
| `InvertedWednesdayConstraint` | HIGH | ROTATION | Prevents Wednesday morning assignments for certain roles |

**Interactions:**
- All three affect Wednesday scheduling (overlapping scope)
- Can conflict with `SupervisionRatioConstraint` if only 1 PGY-1 is available on Wednesday AM
- `WednesdayPMSingleFacultyConstraint` limits faculty availability for other blocks

---

### Faculty Primary Duty Constraints (Airtable-Driven)

| Constraint | Type | Priority | Weight | Description |
|------------|------|----------|--------|-------------|
| `FacultyPrimaryDutyClinicConstraint` | Hard | HIGH | N/A | Enforces per-faculty clinic min/max from primary_duties.json |
| `FacultyDayAvailabilityConstraint` | Hard | HIGH | N/A | Enforces per-faculty day-of-week availability |
| `FacultyClinicEquitySoftConstraint` | Soft | MEDIUM | 15.0 | Balances clinic workload across faculty |

**Key Characteristics:**
- Driven by `backend/app/scheduling/primary_duties.json`
- Per-faculty targets (heterogeneous, not homogeneous)
- `FacultyDayAvailabilityConstraint` blocks specific days (e.g., no clinic on admin days)

**Interactions:**
- `FacultyPrimaryDutyClinicConstraint` sets hard limits that `FacultyClinicEquitySoftConstraint` optimizes within
- Can conflict with `CoverageConstraint` if faculty targets are too restrictive
- `FacultyDayAvailabilityConstraint` reduces available faculty pool for certain days

---

### Faculty Role Constraints (Hard)

| Constraint | Priority | Description |
|------------|----------|-------------|
| `FacultyRoleClinicConstraint` | HIGH | Enforces role-based clinic rules (e.g., PD/APD admin days) |
| `SMFacultyClinicConstraint` | HIGH | Sports Medicine faculty excluded from regular clinic |

**Interactions:**
- `SMFacultyClinicConstraint` removes SM faculty from clinic pool → affects coverage
- Works with `FacultyDayAvailabilityConstraint` for comprehensive role-based blocking

---

### FMIT (Family Medicine Inpatient Teaching) Constraints

| Constraint | Type | Priority | Default | Description |
|------------|------|----------|---------|-------------|
| `FMITWeekBlockingConstraint` | Hard | CRITICAL | Disabled | Blocks clinic & Sun-Thurs call during FMIT week (Fri-Thu) |
| `FMITMandatoryCallConstraint` | Hard | CRITICAL | Disabled | FMIT attending must cover Fri/Sat night call |
| `PostFMITRecoveryConstraint` | Hard | CRITICAL | **Enabled** | Friday after FMIT is completely blocked (recovery day) |
| `PostFMITSundayBlockingConstraint` | Hard | CRITICAL | **Enabled** | Sunday following FMIT blocked |
| `FMITResidentClinicDayConstraint` | Hard | HIGH | Disabled | Prevents resident clinic during FMIT week |
| `FMITContinuityTurfConstraint` | Hard | CRITICAL | Not in default | OB turf rules based on load shedding level |
| `FMITStaffingFloorConstraint` | Hard | CRITICAL | Not in default | Minimum faculty requirements for FMIT |

**Key Characteristics:**
- FMIT weeks run Friday to Thursday (independent of calendar weeks)
- Most FMIT constraints disabled by default (opt-in via configuration)
- `PostFMITRecoveryConstraint` always enabled (burnout prevention)

**Interactions:**
- `FMITWeekBlockingConstraint` removes faculty from clinic pool for entire week
- Conflicts with `FacultyPrimaryDutyClinicConstraint` if faculty has high clinic minimums
- `PostFMITRecoveryConstraint` reduces Friday coverage
- Works with `CallEquityConstraint` (FMIT faculty must take Fri/Sat call)

---

### Call Coverage Constraints (Hard)

| Constraint | Priority | Default | Description |
|------------|----------|---------|-------------|
| `OvernightCallCoverageConstraint` | CRITICAL | Not in default | Ensures overnight call coverage for specified days |
| `CallAvailabilityConstraint` | CRITICAL | Not in default | Respects faculty availability for call |
| `AdjunctCallExclusionConstraint` | HIGH | Not in default | Excludes adjunct faculty from solver-generated call |

**Interactions:**
- Works with `FMITMandatoryCallConstraint` (FMIT gets Fri/Sat)
- `AdjunctCallExclusionConstraint` removes faculty from call pool → increases load on others

---

### Overnight Call Generation & Post-Call (Hard, Opt-In)

| Constraint | Priority | Default | Description |
|------------|----------|---------|-------------|
| `OvernightCallGenerationConstraint` | CRITICAL | Disabled | Unified overnight call generation for eligible nights |
| `PostCallAutoAssignmentConstraint` | CRITICAL | Disabled | Auto-assigns post-call blocks after overnight call |
| `NightFloatPostCallConstraint` | CRITICAL | **Enabled** | Prevents assignments immediately after Night Float |

**Key Characteristics:**
- `OvernightCallGenerationConstraint` disabled by default (opt-in per program)
- `PostCallAutoAssignmentConstraint` ensures post-call recovery time
- `NightFloatPostCallConstraint` always enabled (ACGME rest requirement)

**Interactions:**
- `OvernightCallGenerationConstraint` creates assignments → `PostCallAutoAssignmentConstraint` blocks next day
- `NightFloatPostCallConstraint` can reduce coverage for blocks immediately after Night Float
- Competes with `CoverageConstraint` (post-call blocks unavailable)

---

### Call Equity Constraints (Soft)

| Constraint | Weight | Priority | Description |
|------------|--------|----------|-------------|
| `SundayCallEquityConstraint` | 10.0 | MEDIUM | Fair distribution of Sunday overnight call (worst day) |
| `CallSpacingConstraint` | 8.0 | MEDIUM | Minimum days between call shifts (prevent burnout) |
| `WeekdayCallEquityConstraint` | 5.0 | MEDIUM | Fair distribution of Mon-Thurs call |
| `TuesdayCallPreferenceConstraint` | 2.0 | LOW | PD/APD avoid Tuesday (academics) |
| `DeptChiefWednesdayPreferenceConstraint` | 2.0 | LOW | Dept Chief prefers Wednesday call |

**Weight Hierarchy:**
```
Sunday Equity (10.0) > CallSpacing (8.0) > Weekday Equity (5.0) > Day Preferences (2.0)
```

**Rationale:**
- Sunday is worst day (disrupts weekend, busy Monday) → highest weight
- Spacing prevents burnout → second priority
- Weekday balance → third priority
- Individual preferences → lowest weight

**Interactions:**
- All compete for call assignments
- `CallSpacingConstraint` can conflict with `SundayCallEquityConstraint` (may force uneven Sunday distribution)
- Work together to create fair, sustainable call schedule

---

### Equity & Continuity Constraints (Soft)

| Constraint | Weight | Priority | Description |
|------------|--------|----------|-------------|
| `EquityConstraint` | 10.0 | MEDIUM | Balance workload across residents (supports heterogeneous targets) |
| `ContinuityConstraint` | 5.0 | LOW | Encourage rotation continuity (minimize template changes) |

**Key Characteristics:**
- `EquityConstraint` now supports per-resident `target_clinical_blocks` (heterogeneous)
- Falls back to minimizing max assignments if no targets set
- `ContinuityConstraint` is post-processing validation only (not enforced in solver)

**Interactions:**
- `EquityConstraint` competes with `CoverageConstraint` (coverage may require uneven distribution)
- `ContinuityConstraint` conflicts with dynamic scheduling needs
- Can conflict with `EightyHourRuleConstraint` if targets are too high

---

### Resilience Constraints (Soft)

#### Tier 1: Core Resilience (Enabled by Default)

| Constraint | Weight | Priority | Description |
|------------|--------|----------|-------------|
| `HubProtectionConstraint` | 15.0 | MEDIUM | Protects critical hub faculty from over-assignment |
| `UtilizationBufferConstraint` | 20.0 | HIGH | Maintains 20% capacity buffer (80% utilization threshold) |

#### Tier 2: Strategic Resilience (Disabled by Default)

| Constraint | Weight | Priority | Description |
|------------|--------|----------|-------------|
| `ZoneBoundaryConstraint` | 12.0 | MEDIUM | Respects blast radius zone boundaries |
| `PreferenceTrailConstraint` | 8.0 | LOW | Uses stigmergy preference trails for optimization |
| `N1VulnerabilityConstraint` | 25.0 | HIGH | Prevents single points of failure |

**Key Characteristics:**
- Tier 1 enabled in `create_default()`, Tier 2 disabled
- Use `create_resilience_aware(tier=2)` to enable all resilience constraints
- Requires resilience data populated in SchedulingContext (hub_scores, zone_assignments, etc.)

**Resilience Weight Hierarchy:**
```
N1Vulnerability (25.0) > UtilizationBuffer (20.0) > HubProtection (15.0) >
ZoneBoundary (12.0) > PreferenceTrail (8.0)
```

**Interactions:**
- `HubProtectionConstraint` reduces assignments to critical faculty → may increase assignments to others
- `UtilizationBufferConstraint` limits total assignments → conflicts with `CoverageConstraint`
- `ZoneBoundaryConstraint` prefers in-zone assignments → can conflict with `EquityConstraint`
- `N1VulnerabilityConstraint` encourages redundancy → may increase faculty workload

**Data Dependencies:**
- `HubProtectionConstraint`: Requires `context.hub_scores` from ResilienceService
- `UtilizationBufferConstraint`: Uses `context.target_utilization` (default 0.80)
- `ZoneBoundaryConstraint`: Requires `context.zone_assignments` and `context.block_zones`
- `PreferenceTrailConstraint`: Requires `context.preference_trails` from stigmergy analysis
- `N1VulnerabilityConstraint`: Uses `context.n1_vulnerable_faculty` set

---

### Sports Medicine Constraints (Hard, Opt-In)

| Constraint | Priority | Default | Description |
|------------|----------|---------|-------------|
| `SMResidentFacultyAlignmentConstraint` | HIGH | Disabled | SM residents must align with SM faculty clinic days |
| `SMFacultyClinicConstraint` | HIGH | Disabled | SM faculty excluded from regular clinic |

**Interactions:**
- Enable only if Sports Medicine program exists
- `SMFacultyClinicConstraint` removes faculty from clinic pool
- Works with `FacultyRoleClinicConstraint` for comprehensive role filtering

---

### Faculty Preference Constraints (Soft)

| Constraint | Weight | Priority | Default | Description |
|------------|--------|----------|---------|-------------|
| `PreferenceConstraint` | 5.0 | LOW | Not in default | General faculty preference optimization |

**Note:** Not included in default ConstraintManager - use with caution to avoid bias.

---

## Priority Hierarchy

### Hard Constraint Evaluation Order

Constraints are applied in priority order (highest first):

```
CRITICAL (100):
├── ACGME Compliance (4 constraints)
│   ├── AvailabilityConstraint
│   ├── EightyHourRuleConstraint
│   ├── OneInSevenRuleConstraint
│   └── SupervisionRatioConstraint
├── Capacity
│   └── OnePersonPerBlockConstraint
└── FMIT (when enabled)
    ├── FMITWeekBlockingConstraint
    ├── FMITMandatoryCallConstraint
    ├── PostFMITRecoveryConstraint
    └── PostFMITSundayBlockingConstraint

HIGH (75):
├── Capacity
│   ├── ClinicCapacityConstraint
│   └── MaxPhysiciansInClinicConstraint
├── Temporal
│   ├── WednesdayAMInternOnlyConstraint
│   ├── WednesdayPMSingleFacultyConstraint
│   └── InvertedWednesdayConstraint
├── Faculty Primary Duty
│   ├── FacultyPrimaryDutyClinicConstraint
│   └── FacultyDayAvailabilityConstraint
├── Faculty Role
│   ├── FacultyRoleClinicConstraint
│   └── SMFacultyClinicConstraint
└── Post-Call
    └── NightFloatPostCallConstraint
```

### Soft Constraint Weight Order

Objective function: `maximize(coverage) - Σ(weight × penalty)`

```
Coverage (1000.0)           # Dominant objective
  ├─ N1Vulnerability (25.0)   # Resilience Tier 2
  ├─ UtilizationBuffer (20.0) # Resilience Tier 1
  ├─ HubProtection (15.0)     # Resilience Tier 1
  ├─ FacultyClinicEquity (15.0)
  ├─ ZoneBoundary (12.0)      # Resilience Tier 2
  ├─ SundayCallEquity (10.0)
  ├─ Equity (10.0)
  ├─ CallSpacing (8.0)
  ├─ PreferenceTrail (8.0)    # Resilience Tier 2
  ├─ WeekdayCallEquity (5.0)
  ├─ Continuity (5.0)
  └─ TuesdayCallPreference (2.0)
```

**Weight Categories:**
- **1000+**: Primary objective (coverage)
- **20-30**: Critical soft constraints (resilience, N-1)
- **10-20**: Important soft constraints (equity, hub protection)
- **5-10**: Standard soft constraints (balance, spacing)
- **2-5**: Low-priority soft constraints (preferences, continuity)

---

## Constraint Interactions

### Synergistic Interactions (Constraints That Work Together)

| Constraint Pair | Interaction | Benefit |
|----------------|-------------|---------|
| `AvailabilityConstraint` + `FacultyDayAvailabilityConstraint` | Both block assignments | Comprehensive availability enforcement |
| `FMITWeekBlockingConstraint` + `PostFMITRecoveryConstraint` | Sequential blocking | Prevents FMIT burnout |
| `CallSpacingConstraint` + `SundayCallEquityConstraint` | Spacing + fairness | Sustainable call schedule |
| `HubProtectionConstraint` + `N1VulnerabilityConstraint` | Hub protection + redundancy | Resilient faculty pool |
| `UtilizationBufferConstraint` + `EquityConstraint` | Buffer + balance | Sustainable workload |
| `FacultyPrimaryDutyClinicConstraint` + `FacultyClinicEquitySoftConstraint` | Hard limits + soft optimization | Fair clinic distribution within constraints |

### Competitive Interactions (Constraints That Compete)

| Constraint Pair | Competition | Resolution |
|----------------|-------------|------------|
| `CoverageConstraint` vs. All Soft Constraints | Coverage vs. optimization | Coverage weight (1000.0) dominates |
| `EquityConstraint` vs. `ContinuityConstraint` | Balance vs. stability | Equity weight (10.0) > Continuity (5.0) |
| `HubProtectionConstraint` vs. `EquityConstraint` | Protect hubs vs. balance all | Hub protection targets specific faculty |
| `UtilizationBufferConstraint` vs. `CoverageConstraint` | Buffer vs. max coverage | Balance via buffer weight (20.0) |
| `ZoneBoundaryConstraint` vs. `EquityConstraint` | Zone isolation vs. balance | Depends on resilience tier enabled |
| `CallSpacingConstraint` vs. `SundayCallEquityConstraint` | Spacing vs. fairness | Sunday weight (10.0) > Spacing (8.0) but both apply |

### Conflicting Interactions (Potential Issues)

| Constraint Pair | Conflict Type | Impact | Mitigation |
|----------------|---------------|--------|------------|
| `EightyHourRuleConstraint` vs. `EquityConstraint` | Hard limit vs. soft target | Equity may be impossible to achieve | Set realistic target_clinical_blocks |
| `WednesdayAMInternOnlyConstraint` vs. `SupervisionRatioConstraint` | Limited residents vs. supervision need | May need >1 faculty on Wednesday | Ensure enough PGY-1 residents |
| `FacultyPrimaryDutyClinicConstraint` vs. `CoverageConstraint` | Faculty limits vs. coverage need | Clinic may be under-covered | Adjust faculty targets or hire more faculty |
| `FMITWeekBlockingConstraint` vs. `ClinicCapacityConstraint` | Block faculty vs. need coverage | Clinic capacity reduced during FMIT weeks | Stagger FMIT weeks across faculty |
| `PostCallAutoAssignmentConstraint` vs. `CoverageConstraint` | Block post-call vs. coverage need | Reduced coverage next day | Plan call nights carefully |
| `N1VulnerabilityConstraint` vs. `CoverageConstraint` | Redundancy vs. max coverage | May leave some blocks uncovered | Use Tier 2 only when needed |

---

## Conflict Resolution

### Conflict Resolution Strategy

The constraint system uses a hierarchical conflict resolution approach:

```
1. Hard Constraints (Priority-Based)
   ├─ CRITICAL (100) applied first → infeasible if violated
   ├─ HIGH (75) applied second → infeasible if violated
   └─ Conflicts between same priority → deterministic order in ConstraintManager

2. Soft Constraints (Weight-Based)
   ├─ All soft constraints contribute to objective function
   ├─ Solver finds Pareto-optimal solution balancing all weights
   └─ Higher weight = more influence on final solution

3. Hard vs. Soft Conflicts
   ├─ Hard constraints always win
   ├─ Soft constraints optimize within hard constraint boundaries
   └─ If hard constraints are infeasible → solver fails (no solution)
```

### Handling Infeasible Schedules

When hard constraints cannot be satisfied:

```python
# Solver returns None if infeasible
result = solver.solve(context, constraints)

if result is None:
    # Common causes:
    # 1. Too many absences (AvailabilityConstraint)
    # 2. Insufficient faculty (SupervisionRatioConstraint)
    # 3. Over-constrained faculty targets (FacultyPrimaryDutyClinicConstraint)
    # 4. Conflicting FMIT/clinic requirements

    # Mitigation strategies:
    # - Reduce faculty clinic minimums
    # - Disable optional hard constraints (FMIT, Sports Medicine)
    # - Extend date range
    # - Hire more faculty
```

### Debugging Constraint Conflicts

Use `ConstraintManager.validate_all()` to identify violations:

```python
from backend.app.scheduling.constraints import ConstraintManager

manager = ConstraintManager.create_default()
result = manager.validate_all(assignments, context)

if not result.satisfied:
    for violation in result.violations:
        print(f"{violation.constraint_name}: {violation.message}")
        print(f"  Severity: {violation.severity}")
        print(f"  Details: {violation.details}")
```

**Common Violation Patterns:**

| Violation | Likely Cause | Fix |
|-----------|--------------|-----|
| `80HourRule: X hours/week (limit: 80)` | Too many assignments | Reduce target_clinical_blocks or add residents |
| `SupervisionRatio: needs X faculty but has Y` | Insufficient faculty | Assign more faculty or reduce resident count |
| `ClinicCapacity: X assigned (max: Y)` | Template over-saturated | Increase max_residents or add templates |
| `WednesdayAMInternOnly: PGY-2 assigned` | Wrong resident type | Check resident PGY levels |
| `HubProtection: Hub faculty over-assigned` | Hub concentration | Distribute assignments more evenly |

---

## Configuration Patterns

### 1. Default Configuration (Balanced)

```python
manager = ConstraintManager.create_default()
```

**Profile:**
- All ACGME compliance (4 hard)
- Core capacity/temporal (10 hard)
- Standard equity/coverage (8 soft)
- Tier 1 resilience (2 soft, enabled)
- FMIT/SM disabled (opt-in)
- Tier 2 resilience disabled

**Best For:** Most residency programs, production use

---

### 2. Resilience-Aware Configuration (Robust)

```python
manager = ConstraintManager.create_resilience_aware(
    target_utilization=0.80,
    tier=2  # Enable all resilience constraints
)
```

**Profile:**
- All default constraints
- Tier 1 + Tier 2 resilience (5 soft total)
- Hub protection, utilization buffer, zone boundaries, preference trails, N-1 vulnerability

**Best For:** Programs with resilience data (hub scores, zones), high turnover, high complexity

**Weight Impact:**
```
N1Vulnerability (25.0) + UtilizationBuffer (20.0) + HubProtection (15.0) +
ZoneBoundary (12.0) + PreferenceTrail (8.0) = 80.0 total resilience weight
```

---

### 3. Minimal Configuration (Fast)

```python
manager = ConstraintManager.create_minimal()
```

**Profile:**
- Availability (1 hard)
- One person per block (1 hard)
- Coverage (1 soft)

**Best For:** Quick prototyping, small schedules (<100 blocks), testing

**Performance:** <1 second for most schedules

---

### 4. Strict Configuration (Aggressive Optimization)

```python
manager = ConstraintManager.create_strict()
```

**Profile:**
- All default constraints
- Soft constraint weights doubled (all 2× penalties)

**Best For:** High-quality solutions, research, long-term planning

**Note:** May increase solve time significantly (2-10×)

---

### 5. FMIT-Enabled Configuration (Inpatient Focus)

```python
manager = ConstraintManager.create_default()
manager.enable("FMITWeekBlocking")
manager.enable("FMITMandatoryCall")
manager.enable("FMITResidentClinicDay")
```

**Profile:**
- Default + FMIT constraints
- `PostFMITRecoveryConstraint` already enabled by default

**Best For:** Programs with active FMIT service

**Impact:** Significant reduction in faculty clinic availability during FMIT weeks

---

### 6. Call-Focused Configuration (Equity Priority)

```python
manager = ConstraintManager.create_default()

# Increase call equity weights
for c in manager._soft_constraints:
    if c.constraint_type == ConstraintType.EQUITY and "Call" in c.name:
        c.weight *= 2  # Double call equity importance
```

**Profile:**
- Default + enhanced call equity weights
- `SundayCallEquity (20.0)`, `CallSpacing (16.0)`, `WeekdayCallEquity (10.0)`

**Best For:** Programs with frequent call complaints, high call frequency

---

### 7. Custom Configuration Template

```python
manager = ConstraintManager()

# Add only what you need
manager.add(AvailabilityConstraint())
manager.add(OnePersonPerBlockConstraint())
manager.add(EightyHourRuleConstraint())
manager.add(CoverageConstraint(weight=1000.0))
manager.add(EquityConstraint(weight=15.0))  # Increase equity importance
manager.add(HubProtectionConstraint(weight=20.0))  # Increase hub protection

# Conditionally enable
if has_fmit_service:
    manager.add(FMITWeekBlockingConstraint())

if has_resilience_data:
    manager.add(UtilizationBufferConstraint(target_utilization=0.75))  # More conservative
```

---

## Dependency Graph

### Hard Constraint Dependencies

```
AvailabilityConstraint (CRITICAL)
    ├─ Required by: All constraints (provides availability data)
    └─ Depends on: Absence records in database

SupervisionRatioConstraint (CRITICAL)
    ├─ Triggered by: Resident assignments
    └─ Requires: Faculty pool, PGY levels

OnePersonPerBlockConstraint (CRITICAL)
    ├─ Prevents: Double-booking
    └─ Required by: Coverage calculations

ClinicCapacityConstraint (HIGH)
    ├─ Depends on: RotationTemplate.max_residents
    └─ Affects: Coverage, Equity

WednesdayAMInternOnlyConstraint (HIGH)
    ├─ Filters: Resident eligibility
    └─ May conflict with: SupervisionRatioConstraint (if few PGY-1)

FacultyPrimaryDutyClinicConstraint (HIGH)
    ├─ Depends on: primary_duties.json
    └─ Affects: Faculty availability, coverage

FMITWeekBlockingConstraint (CRITICAL, opt-in)
    ├─ Blocks: Clinic + Sun-Thurs call
    ├─ Requires: FMIT assignments identified
    └─ Triggers: PostFMITRecoveryConstraint

PostFMITRecoveryConstraint (CRITICAL)
    ├─ Triggered by: FMIT assignments
    └─ Blocks: Friday after FMIT week
```

### Soft Constraint Dependencies

```
CoverageConstraint (1000.0)
    ├─ Primary objective
    └─ Competes with: All other soft constraints

EquityConstraint (10.0)
    ├─ Depends on: target_clinical_blocks (if set)
    └─ Competes with: Coverage, Continuity

HubProtectionConstraint (15.0)
    ├─ Depends on: context.hub_scores from ResilienceService
    └─ Competes with: Equity, Coverage

UtilizationBufferConstraint (20.0)
    ├─ Depends on: context.target_utilization
    └─ Limits: Total assignments

N1VulnerabilityConstraint (25.0)
    ├─ Depends on: context.n1_vulnerable_faculty
    └─ Encourages: Redundancy (may reduce coverage)

CallEquity Constraints (2.0-10.0)
    ├─ Depend on: Call assignments (OvernightCallGenerationConstraint)
    └─ Compete with: Each other (spacing vs. fairness)
```

### Data Flow Dependencies

```
Database
    ├─ Persons (residents, faculty)
    ├─ Blocks (date, time_of_day)
    ├─ RotationTemplates (max_residents, rotation_type)
    └─ Absences (blocking, start_date, end_date)

SchedulingContext
    ├─ Built from database queries
    ├─ availability matrix (from Absences)
    ├─ Resilience data (optional, from ResilienceService)
    │   ├─ hub_scores
    │   ├─ n1_vulnerable_faculty
    │   ├─ zone_assignments
    │   └─ preference_trails
    └─ Lookup indices (resident_idx, faculty_idx, block_idx)

ConstraintManager
    ├─ Reads: SchedulingContext
    ├─ Applies: Constraints to solver model
    └─ Outputs: Validated assignments
```

---

## Weight Tuning Guide

### Weight Scaling Principles

1. **Coverage Dominance:** `CoverageConstraint (1000.0)` should be 50-100× higher than other soft constraints
2. **Tier Separation:** Critical soft constraints (20-30) should be 2-3× higher than standard (5-10)
3. **Within-Tier Balance:** Constraints in same tier should differ by 20-50% (not orders of magnitude)

### Tuning Scenarios

#### Scenario 1: Improve Workload Balance

**Problem:** Large workload variance across residents

**Solution:**
```python
manager = ConstraintManager.create_default()

# Increase equity weight
for c in manager._soft_constraints:
    if c.name == "Equity":
        c.weight = 20.0  # Double from 10.0
```

**Impact:** More balanced distribution, may sacrifice some coverage

---

#### Scenario 2: Protect Critical Faculty

**Problem:** Hub faculty (PD, specialty leads) are over-assigned

**Solution:**
```python
manager = ConstraintManager.create_resilience_aware(tier=1)

# Increase hub protection weight
for c in manager._soft_constraints:
    if c.name == "HubProtection":
        c.weight = 30.0  # Double from 15.0
```

**Impact:** Hub faculty get fewer assignments, others compensate

---

#### Scenario 3: Improve Call Distribution

**Problem:** Unfair call distribution, complaints about Sunday call

**Solution:**
```python
manager = ConstraintManager.create_default()

# Increase call equity weights
for c in manager._soft_constraints:
    if "Call" in c.name and "Equity" in c.name:
        c.weight *= 1.5
```

**Impact:**
- `SundayCallEquity: 10.0 → 15.0`
- `WeekdayCallEquity: 5.0 → 7.5`

---

#### Scenario 4: Reduce System Utilization (More Buffer)

**Problem:** System running too hot (>85% utilization), frequent scheduling emergencies

**Solution:**
```python
manager = ConstraintManager.create_resilience_aware(
    target_utilization=0.75  # Reduce from 0.80 to 0.75
)

# Increase buffer weight
for c in manager._soft_constraints:
    if c.name == "UtilizationBuffer":
        c.weight = 40.0  # Double from 20.0
```

**Impact:** Schedule targets 75% utilization (25% buffer), may reduce coverage slightly

---

#### Scenario 5: Balance Coverage vs. Equity Tradeoff

**Problem:** Coverage is good but some residents work 2× others

**Solution:**
```python
manager = ConstraintManager.create_default()

# Option A: Reduce coverage dominance (aggressive)
for c in manager._soft_constraints:
    if c.name == "Coverage":
        c.weight = 500.0  # Reduce from 1000.0
    if c.name == "Equity":
        c.weight = 25.0  # Increase from 10.0

# Option B: Keep coverage dominant, but boost equity (conservative)
for c in manager._soft_constraints:
    if c.name == "Equity":
        c.weight = 50.0  # 5× increase (still <5% of coverage weight)
```

**Impact:**
- Option A: Significant equity improvement, may reduce coverage by 5-10%
- Option B: Moderate equity improvement, minimal coverage impact

---

### Weight Tuning Best Practices

1. **One Change at a Time:** Adjust one weight, test, measure impact
2. **Relative Scaling:** Consider ratios, not absolute values (Equity/Coverage = 10/1000 = 1%)
3. **Validation:** Always run validation after tuning to check for violations
4. **Document Changes:** Track weight changes and reasons in version control
5. **A/B Testing:** Generate schedules with old/new weights, compare metrics
6. **Stakeholder Feedback:** Survey faculty/residents on quality before/after tuning

---

## Common Issues

### Issue 1: Solver Times Out / No Solution Found

**Symptoms:**
- Solver runs for >5 minutes and fails
- Returns `None` (infeasible)

**Common Causes:**
1. **Too many absences** → `AvailabilityConstraint` blocks too many assignments
2. **Over-constrained faculty** → `FacultyPrimaryDutyClinicConstraint` targets too restrictive
3. **FMIT + high clinic mins** → `FMITWeekBlockingConstraint` conflicts with clinic requirements
4. **Insufficient faculty** → `SupervisionRatioConstraint` cannot be satisfied

**Diagnosis:**
```python
# Run pre-flight validation
from backend.app.scheduling.preflight import validate_constraints

issues = validate_constraints(context, manager)
for issue in issues:
    print(f"{issue.severity}: {issue.message}")
```

**Solutions:**
- Reduce faculty clinic minimums in `primary_duties.json`
- Disable optional constraints (`FMIT`, `SM`)
- Extend date range to give solver more flexibility
- Add more faculty to pool

---

### Issue 2: Poor Workload Balance (High Equity Penalty)

**Symptoms:**
- Some residents have 2× assignments of others
- `EquityConstraint` violations in validation

**Common Causes:**
1. **Coverage weight too high** → `CoverageConstraint (1000.0)` dominates `EquityConstraint (10.0)`
2. **Heterogeneous targets** → Some residents have higher `target_clinical_blocks`
3. **Availability imbalance** → Some residents have many absences

**Diagnosis:**
```python
# Check equity penalty
result = manager.validate_all(assignments, context)
for v in result.violations:
    if v.constraint_name == "Equity":
        print(f"Min: {v.details['min']}, Max: {v.details['max']}, Spread: {v.details['spread']}")
```

**Solutions:**
- Increase `EquityConstraint` weight: `10.0 → 20.0 or 50.0`
- Set realistic `target_clinical_blocks` for all residents
- Reduce `CoverageConstraint` weight: `1000.0 → 500.0` (aggressive)
- Check for absence patterns (some residents consistently unavailable)

---

### Issue 3: Wednesday AM Has No Residents

**Symptoms:**
- `WednesdayAMInternOnlyConstraint` blocks all residents
- `SupervisionRatioConstraint` violations on Wednesday

**Common Causes:**
1. **No PGY-1 residents available** → All PGY-1 have absences on Wednesdays
2. **Insufficient PGY-1 count** → Only 1 PGY-1 but need 2+ for clinic

**Diagnosis:**
```python
# Check PGY-1 availability
pgy1_residents = [r for r in context.residents if r.pgy_level == 1]
wednesday_blocks = [b for b in context.blocks if b.date.weekday() == 2 and b.time_of_day == "AM"]

for block in wednesday_blocks:
    available_pgy1 = [r for r in pgy1_residents
                      if context.availability.get(r.id, {}).get(block.id, {}).get('available', True)]
    print(f"{block.date}: {len(available_pgy1)} PGY-1 available")
```

**Solutions:**
- Ensure at least 2 PGY-1 residents per Wednesday
- Disable `WednesdayAMInternOnlyConstraint` temporarily if needed
- Adjust PGY-1 absence schedules to avoid Wednesday conflicts

---

### Issue 4: FMIT Weeks Cause Coverage Gaps

**Symptoms:**
- Clinic under-staffed during FMIT weeks
- `ClinicCapacityConstraint` violations

**Common Causes:**
1. **Multiple faculty on FMIT same week** → `FMITWeekBlockingConstraint` removes too many
2. **FMIT + high clinic minimums** → Faculty can't meet clinic targets with FMIT weeks

**Diagnosis:**
```python
# Check FMIT week overlap
fmit_assignments = [a for a in existing_assignments if "FMIT" in a.rotation_template.name]
fmit_weeks = {}
for a in fmit_assignments:
    week = get_fmit_week_dates(a.block.date)
    fmit_weeks.setdefault(week, []).append(a.person_id)

for week, faculty_ids in fmit_weeks.items():
    if len(faculty_ids) > 1:
        print(f"Week {week}: {len(faculty_ids)} faculty on FMIT (too many!)")
```

**Solutions:**
- Stagger FMIT weeks across faculty (max 1 per week)
- Reduce faculty clinic minimums during FMIT-heavy periods
- Disable `FMITWeekBlockingConstraint` and handle manually
- Increase clinic `max_residents` temporarily during FMIT weeks

---

### Issue 5: Resilience Constraints Have No Effect

**Symptoms:**
- Hub faculty still over-assigned despite `HubProtectionConstraint`
- Utilization >90% despite `UtilizationBufferConstraint`

**Common Causes:**
1. **No resilience data** → `context.hub_scores` is empty
2. **Weights too low** → Resilience weights drowned out by `CoverageConstraint`
3. **Tier 2 disabled** → Only Tier 1 enabled but need more aggressive constraints

**Diagnosis:**
```python
# Check resilience data
print(f"Hub scores: {len(context.hub_scores)} faculty")
print(f"N-1 vulnerable: {len(context.n1_vulnerable_faculty)} faculty")
print(f"Zone assignments: {len(context.zone_assignments)} faculty")
print(f"Current utilization: {context.current_utilization:.0%}")

# Check constraint weights
for c in manager.get_soft_constraints():
    if c.constraint_type in [ConstraintType.HUB_PROTECTION, ConstraintType.UTILIZATION_BUFFER]:
        print(f"{c.name}: weight={c.weight}, enabled={c.enabled}")
```

**Solutions:**
- Populate resilience data via `ResilienceService`
- Increase resilience weights: `HubProtection: 15→30`, `UtilizationBuffer: 20→40`
- Enable Tier 2: `manager = ConstraintManager.create_resilience_aware(tier=2)`
- Reduce `target_utilization`: `0.80 → 0.75`

---

### Issue 6: Call Distribution Unfair (Some Faculty Get All Sundays)

**Symptoms:**
- `SundayCallEquityConstraint` violations
- Faculty complaints about Sunday call concentration

**Common Causes:**
1. **Weight too low** → `SundayCallEquity (10.0)` not competitive with other objectives
2. **Conflicts with `CallSpacingConstraint`** → Spacing forces uneven distribution
3. **Limited faculty pool** → Adjuncts excluded, only 3-4 faculty available

**Diagnosis:**
```python
# Check Sunday call distribution
sunday_calls = defaultdict(int)
for a in assignments:
    if a.block.date.weekday() == 6 and a.call_type == "overnight":
        sunday_calls[a.person_id] += 1

for faculty_id, count in sunday_calls.items():
    print(f"{faculty_id}: {count} Sundays")

mean = sum(sunday_calls.values()) / len(sunday_calls)
variance = sum((c - mean)**2 for c in sunday_calls.values()) / len(sunday_calls)
print(f"Mean: {mean:.1f}, Variance: {variance:.1f}")
```

**Solutions:**
- Increase `SundayCallEquityConstraint` weight: `10.0 → 20.0`
- Reduce `CallSpacingConstraint` weight: `8.0 → 4.0` (allow tighter spacing for fairness)
- Expand faculty call pool (include adjuncts if appropriate)
- Manually review and adjust call assignments

---

## Constraint Debugging

### Debugging Workflow

```
1. Identify Violation
   ├─ Run validation: manager.validate_all(assignments, context)
   ├─ Check violation.constraint_name and violation.severity
   └─ Review violation.details for specifics

2. Isolate Cause
   ├─ Check constraint dependencies (see Dependency Graph)
   ├─ Test with minimal config: ConstraintManager.create_minimal()
   ├─ Add constraints one at a time until violation appears
   └─ Check data: context.residents, context.blocks, context.availability

3. Test Solutions
   ├─ Disable conflicting constraints
   ├─ Adjust weights
   ├─ Modify input data (absences, targets, templates)
   └─ Re-run solver and validation

4. Verify Fix
   ├─ Run full validation
   ├─ Check all metrics (coverage rate, equity, utilization)
   └─ A/B compare with previous schedule
```

### Debugging Tools

#### Tool 1: Constraint Isolation

```python
# Test each constraint individually
manager = ConstraintManager()
manager.add(AvailabilityConstraint())
manager.add(OnePersonPerBlockConstraint())

# Add suspect constraint
manager.add(FMITWeekBlockingConstraint())

# Test
result = manager.validate_all(assignments, context)
print(f"Satisfied: {result.satisfied}")
print(f"Violations: {len(result.violations)}")
```

#### Tool 2: Constraint Dependency Checker

```python
def check_dependencies(constraint_name, context):
    """Check if constraint has required data."""
    if constraint_name == "HubProtection":
        return len(context.hub_scores) > 0
    elif constraint_name == "UtilizationBuffer":
        return context.target_utilization > 0
    elif constraint_name == "ZoneBoundary":
        return len(context.zone_assignments) > 0 and len(context.block_zones) > 0
    # ... add more checks
    return True

# Check all constraints
for c in manager.get_enabled():
    has_data = check_dependencies(c.name, context)
    print(f"{c.name}: {'✓' if has_data else '✗ (missing data)'}")
```

#### Tool 3: Weight Impact Analyzer

```python
def analyze_weight_impact(manager):
    """Show relative weight distribution."""
    soft = manager.get_soft_constraints()
    total_weight = sum(c.weight for c in soft)

    for c in sorted(soft, key=lambda x: -x.weight):
        pct = (c.weight / total_weight) * 100
        print(f"{c.name:30s} {c.weight:6.1f} ({pct:5.1f}%)")

    print(f"{'='*50}")
    print(f"{'Total':30s} {total_weight:6.1f}")
```

#### Tool 4: Constraint Conflict Detector

```python
def detect_conflicts(manager, assignments, context):
    """Find constraints that are fighting each other."""
    results = {}

    for constraint in manager.get_enabled():
        result = constraint.validate(assignments, context)
        results[constraint.name] = {
            'satisfied': result.satisfied,
            'penalty': result.penalty,
            'violations': len(result.violations)
        }

    # Identify high-penalty constraints
    high_penalty = [(name, r['penalty']) for name, r in results.items()
                    if r['penalty'] > 100]

    print("High-Penalty Constraints (likely conflicts):")
    for name, penalty in sorted(high_penalty, key=lambda x: -x[1]):
        print(f"  {name}: {penalty:.1f}")
```

---

## Summary Statistics

### Constraint Inventory

| Category | Hard | Soft | Total |
|----------|------|------|-------|
| ACGME Compliance | 4 | 0 | 4 |
| Capacity/Coverage | 3 | 1 | 4 |
| Temporal | 3 | 0 | 3 |
| Faculty Primary Duty | 2 | 1 | 3 |
| Faculty Role | 2 | 0 | 2 |
| FMIT | 6 | 0 | 6 |
| Call Coverage | 3 | 0 | 3 |
| Call Equity | 0 | 4 | 4 |
| Overnight Call/Post-Call | 3 | 0 | 3 |
| Equity/Continuity | 0 | 2 | 2 |
| Resilience | 0 | 5 | 5 |
| Sports Medicine | 2 | 0 | 2 |
| Preferences | 0 | 1 | 1 |
| **TOTAL** | **28** | **14** | **42** |

### Default Configuration Breakdown

| Config | Hard | Soft | Disabled |
|--------|------|------|----------|
| `create_default()` | 17 | 11 | 14 |
| `create_resilience_aware(tier=1)` | 17 | 13 | 12 |
| `create_resilience_aware(tier=2)` | 17 | 14 | 11 |
| `create_minimal()` | 2 | 1 | 39 |
| `create_strict()` | 17 | 11 (2× weights) | 14 |

### Weight Distribution (Default Config)

```
Coverage:              1000.0 (69.2%)
UtilizationBuffer:       20.0 ( 1.4%)
HubProtection:           15.0 ( 1.0%)
FacultyClinicEquity:     15.0 ( 1.0%)
SundayCallEquity:        10.0 ( 0.7%)
Equity:                  10.0 ( 0.7%)
CallSpacing:              8.0 ( 0.6%)
WeekdayCallEquity:        5.0 ( 0.3%)
Continuity:               5.0 ( 0.3%)
TuesdayCallPreference:    2.0 ( 0.1%)
───────────────────────────────────
Total:                 1090.0
```

---

## References

- [SOLVER_ALGORITHM.md](SOLVER_ALGORITHM.md) - Solver implementation details
- [FACULTY_SCHEDULING_SPECIFICATION.md](FACULTY_SCHEDULING_SPECIFICATION.md) - Faculty constraint specifications
- [cross-disciplinary-resilience.md](cross-disciplinary-resilience.md) - Resilience framework concepts
- [CALL_CONSTRAINTS.md](CALL_CONSTRAINTS.md) - Call scheduling constraints
- [FMIT_CONSTRAINTS.md](FMIT_CONSTRAINTS.md) - FMIT scheduling rules

---

*Last Updated: 2025-12-30 - Comprehensive constraint interaction matrix covering all 42 constraints in the system*
