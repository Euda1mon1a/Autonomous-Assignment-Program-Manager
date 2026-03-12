# Constraint Catalog Summary

> **doc_type:** scheduling_policy
> **Source:** Condensed from `docs/architecture/CONSTRAINT_CATALOG.md` (v2.0)
> **Last Updated:** 2026-03-09
> **Purpose:** Quick reference for all 47 scheduling constraints

---

## Overview

- **47 Constraint Classes** in 18 modules
- **27 Hard Constraints** — must be satisfied; violations make schedule infeasible
- **20 Soft Constraints** — optimization objectives; violations add penalty
- **4 Disabled** (engine-conditional): ResidentWeeklyClinic, ZoneBoundary, PreferenceTrail, N1Vulnerability
- **3 Passive** (enabled but no-op): WednesdayPMSingleFaculty, SMResidentFacultyAlignment, HalfDayRequirement

### Architecture

```
Constraint (Abstract)
├── HardConstraint
│   ├── ACGME Constraints (4)
│   ├── Capacity Constraints (4)
│   ├── Call Constraints (3)
│   ├── FMIT Constraints (5)
│   ├── Temporal Constraints (3)
│   ├── Availability Constraints (2)
│   └── Other (2)
├── SoftConstraint
│   ├── Equity Constraints (5)
│   ├── Resilience Constraints (4)
│   ├── Preference Constraints (3)
│   ├── Coverage Constraints (2)
│   ├── Call Equity Constraints (4)
│   └── Faculty Constraints (2)
```

---

## Quick Reference

| Name | Type | Category | Priority | Weight | File |
|------|------|----------|----------|--------|------|
| **Availability** | Hard | ACGME | CRITICAL | - | acgme.py |
| **EightyHourRule** | Hard | ACGME | CRITICAL | - | acgme.py |
| **OneInSevenRule** | Hard | ACGME | CRITICAL | - | acgme.py |
| **SupervisionRatio** | Hard | ACGME | CRITICAL | - | acgme.py |
| **OnePersonPerBlock** | Hard | Capacity | HIGH | - | capacity.py |
| **ClinicCapacity** | Hard | Capacity | HIGH | - | capacity.py |
| **MaxPhysiciansInClinic** | Hard | Capacity | HIGH | - | capacity.py |
| **CoverageConstraint** | Soft | Coverage | HIGH | 1.0 | capacity.py |
| **PostCallAutoAssignment** | Hard | Call | CRITICAL | - | post_call.py |
| **NightFloatPostCall** | Hard | Call | HIGH | - | night_float_post_call.py |
| **OvernightCallCoverage** | Hard | Call | HIGH | - | call_coverage.py |
| **OvernightCallGeneration** | Hard | Call | HIGH | - | overnight_call.py |
| **CallAvailability** | Hard | Call | HIGH | - | call_coverage.py |
| **AdjunctCallExclusion** | Hard | Call | CRITICAL | - | call_coverage.py |
| **FacultyDayAvailability** | Hard | Faculty | HIGH | - | primary_duty.py |
| **FacultyPrimaryDutyClinic** | Hard | Faculty | HIGH | - | primary_duty.py |
| **FacultyRoleClinic** | Hard | Faculty | HIGH | - | faculty_role.py |
| **SMFacultyClinic** | Hard | Faculty | HIGH | - | faculty_role.py |
| **EquityConstraint** | Soft | Equity | MEDIUM | 2.0 | equity.py |
| **ContinuityConstraint** | Soft | Equity | MEDIUM | 1.5 | equity.py |
| **PreferenceConstraint** | Soft | Preference | MEDIUM | 1.0 | faculty.py |
| **HubProtection** | Soft | Resilience | MEDIUM | 1.5 | resilience.py |
| **UtilizationBuffer** | Soft | Resilience | HIGH | 2.0 | resilience.py |
| **N1Vulnerability** | Soft | Resilience | HIGH | 2.5 | resilience.py |
| **PreferenceTrail** | Soft | Resilience | LOW | 0.5 | resilience.py |
| **ZoneBoundary** | Soft | Resilience | MEDIUM | 1.0 | resilience.py |
| **FMIT Constraints** | Hard | FMIT | HIGH | - | fmit.py |
| **Call Equity Constraints** | Soft | Call Equity | MEDIUM | 1.0-2.0 | call_equity.py |
| **Temporal Constraints** | Hard | Temporal | HIGH | - | temporal.py |
| **Inpatient Constraints** | Hard | Inpatient | HIGH | - | inpatient.py |
| **Sports Medicine Constraints** | Hard | Sports Med | HIGH | - | sports_medicine.py |

All constraint files are in `backend/app/scheduling/constraints/`.

---

## Hard Constraints (27)

### ACGME Compliance (acgme.py) — NEVER DISABLE

| Constraint | What It Prevents |
|-----------|-----------------|
| **Availability** | Assignments during vacation, TDY, medical leave, requested absence |
| **EightyHourRule** | >80 hours/week over 4-week rolling average (28-day window, 320 hours max) |
| **OneInSevenRule** | Working 7 consecutive days without a 24-hour break |
| **SupervisionRatio** | Inadequate faculty-to-resident supervision ratio by PGY level |

### Capacity (capacity.py)

| Constraint | What It Prevents |
|-----------|-----------------|
| **OnePersonPerBlock** | Double-booking a person in the same half-day slot |
| **ClinicCapacity** | Exceeding clinic's maximum learner capacity |
| **MaxPhysiciansInClinic** | Too many physicians assigned to same clinic session |

### Call (post_call.py, night_float_post_call.py, call_coverage.py, overnight_call.py)

| Constraint | What It Prevents |
|-----------|-----------------|
| **PostCallAutoAssignment** | Working clinical duties after overnight call (auto-assigns PC/OFF) |
| **NightFloatPostCall** | Missing post-call recovery after NF shift ends |
| **OvernightCallCoverage** | Uncovered overnight call slots (Sun-Thu) |
| **OvernightCallGeneration** | Creates call BoolVars for eligible faculty; blocks ineligible nights |
| **CallAvailability** | Call assignments to unavailable faculty |
| **AdjunctCallExclusion** | Call assignments to adjunct faculty (NEVER take call) |

### Faculty (primary_duty.py, faculty_role.py)

| Constraint | What It Prevents |
|-----------|-----------------|
| **FacultyDayAvailability** | Faculty assigned on days they're not available (template-driven) |
| **FacultyPrimaryDutyClinic** | Faculty not in their primary duty clinic when scheduled |
| **FacultyRoleClinic** | Faculty assigned to clinics outside their role scope |
| **SMFacultyClinic** | Sports Medicine faculty in wrong clinic sessions |

### FMIT (fmit.py) — 5 constraints

Enforce FMIT (Family Medicine Inpatient Team) pairing rules, coverage requirements, and scheduling patterns. Date-scoped pair filtering (see `scheduling-engine-internals.md` for details).

### Temporal (temporal.py) — 3 constraints

Enforce rotation spacing, WednesdayAM intern-only sessions, and temporal sequencing rules.

### Inpatient (inpatient.py)

Enforce inpatient service spacing and coverage requirements.

### Sports Medicine (sports_medicine.py)

Enforce SM-specific clinic assignments and learner caps.

---

## Soft Constraints (20)

### Equity (equity.py)

| Constraint | Weight | What It Optimizes |
|-----------|--------|------------------|
| **EquityConstraint** | 2.0 | Even distribution of desirable/undesirable assignments |
| **ContinuityConstraint** | 1.5 | Patient continuity (same resident sees same patients) |

### Call Equity (call_equity.py) — 4 constraints

Uses MAD (Mean Absolute Deviation) via CP-SAT `AddAbsEquality`. Minimizes call count variance across faculty. FMIT Saturday calls map to Sunday equity bucket. See `scheduling-engine-internals.md` for details.

### Resilience (resilience.py) — 4 constraints (2 disabled)

| Constraint | Weight | Status | What It Optimizes |
|-----------|--------|--------|------------------|
| **HubProtection** | 1.5 | Enabled | Protects critical scheduling hubs from overload |
| **UtilizationBuffer** | 2.0 | Enabled | Keeps utilization below 80% threshold |
| **N1Vulnerability** | 2.5 | **Disabled** | N-1 redundancy (single point of failure detection) |
| **PreferenceTrail** | 0.5 | **Disabled** | Historical preference satisfaction |
| **ZoneBoundary** | 1.0 | **Disabled** | Zone-based scheduling boundaries |

### Preference (faculty.py) — 3 constraints

| Constraint | Weight | What It Optimizes |
|-----------|--------|------------------|
| **PreferenceConstraint** | 1.0 | Faculty day/time preferences from templates |

### Coverage (capacity.py)

| Constraint | Weight | What It Optimizes |
|-----------|--------|------------------|
| **CoverageConstraint** | 1.0 | Minimum staffing levels met across all clinics |

---

## Constraint Ordering and Priorities

Constraints are applied in priority order: **CRITICAL → HIGH → MEDIUM → LOW**

### CRITICAL Tier (NEVER disable)

- Availability, EightyHourRule, OneInSevenRule, SupervisionRatio
- PostCallAutoAssignment, AdjunctCallExclusion

### Relaxation Rules

If the solver finds no feasible solution, constraints are relaxed in tiers:

1. **Tier 1:** Low-priority soft constraints (PreferenceTrail, ZoneBoundary)
2. **Tier 2:** Medium-priority soft constraints (Equity, Continuity, Preference)
3. **Tier 3:** High-priority soft constraints (Coverage, UtilizationBuffer)
4. **Tier 4:** Hard constraint relaxation — **LAST RESORT ONLY**, requires coordinator approval

CRITICAL-tier hard constraints are NEVER relaxed.

---

## Key Behaviors

- **Constraint Manager** (`ConstraintManager`) orchestrates application order
- **SchedulingContext** provides shared state (people, blocks, activities, absences)
- All constraints implement `add_to_cpsat(model, variables, context)` interface
- Soft constraints return `(variable, weight)` tuples for the objective function
- Hard constraints add constraints directly to the CP-SAT model
- See `backend/app/scheduling/constraints/` for all implementations

---

## Related Documents

- `docs/architecture/CONSTRAINT_CATALOG.md` — Full 1590-line reference
- `docs/architecture/DISABLED_CONSTRAINTS_AUDIT.md` — Why 4 are disabled
- `docs/rag-knowledge/scheduling-engine-internals.md` — Engine internals (MAD equity, FMIT filtering, etc.)
