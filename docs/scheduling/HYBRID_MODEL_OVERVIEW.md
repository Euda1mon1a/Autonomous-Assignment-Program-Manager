# Hybrid Scheduling Model Overview

**Status:** Draft for PD Review
**Last Updated:** 2026-01-11
**Author:** Scheduling System

---

## Executive Summary

The scheduling system uses a **hybrid model** that combines:
1. **Protected patterns** - Fixed activities that cannot be moved (e.g., Wednesday lecture time)
2. **Activity requirements** - Quantity targets that the solver satisfies (e.g., "3 clinic half-days")
3. **Solver optimization** - Fills remaining slots with the rotation's default activity type

This approach ensures academic time is sacred while allowing flexibility for clinic and specialty activities.

---

## The Three Layers

### Layer 1: Protected Patterns (Fixed WHERE)

These define **exactly when** specific activities occur. The scheduling solver cannot move them.

| Activity | Day | Time | Weeks | Who |
|----------|-----|------|-------|-----|
| **Lecture (LEC)** | Wednesday | PM | 1, 2, 3 | All daytime rotations |
| **Lecture (LEC)** | Wednesday | AM | 4 | All daytime rotations |
| **Advising (ADV)** | Wednesday | PM | 4 | All daytime rotations |
| **FM Clinic** | Wednesday | AM | 1, 2, 3 | PGY-1 interns |
| **FM Clinic** | Tuesday | PM | 1-4 | FMIT-PGY2 |
| **FM Clinic Inpatient** | Monday | PM | 1-4 | FMIT-PGY3 |

**Key Point:** Protected patterns ensure academic time (Wednesday lecture and advising) is preserved across all rotations.

### Layer 2: Activity Requirements (Fixed HOW MANY)

These define **how many half-days** of an activity are required. The solver decides where to place them.

| Rotation Type | Clinic Requirement | Notes |
|---------------|-------------------|-------|
| PGY-1 interns | 3 half-days (protected) | Fixed on Wed AM |
| FMIT-PGY2 | 4 half-days (protected) | Fixed on Tue PM |
| FMIT-PGY3 | 4 half-days (protected) | Fixed on Mon PM |
| **PGY-2/3 specialty** | **3 half-days (flexible)** | **Solver places** |

### Layer 3: Solver (Fills Remaining Slots)

For slots not covered by protected patterns, the solver fills them with the rotation's **default activity type**:

| Rotation | Default Activity |
|----------|-----------------|
| FMIT | inpatient |
| FMC | outpatient |
| Neurology, Dermatology, etc. | specialty |
| IM, Peds Ward, etc. | inpatient |

---

## Standard Wednesday Pattern

For **daytime rotations** (not Night Float), the standard Wednesday pattern is:

```
Week 1: PM = Lecture
Week 2: PM = Lecture
Week 3: PM = Lecture
Week 4: AM = Lecture, PM = Advising
```

**Why Week 4 is Different:**
- Week 4 has advising in the PM slot (faculty 1-on-1 time)
- Lecture moves to the AM slot for Week 4 only

---

## Exceptions to Standard Pattern

### Night Float Rotations (No Wednesday Activities)

These rotations work nights and do not attend daytime lecture/advising:

- NF (all variants: NF-AM, NF-PM, NF-LD, NF-PEDS-PGY1, etc.)
- NBN (Newborn Nursery night)
- NICU (Night)
- ICU

### Special Activity Rotations (Win Over Wednesday)

These rotations have activities that **take priority** over standard Wednesday lecture/advising:

| Rotation | Reason |
|----------|--------|
| PCAT-AM | Preceptorship with faculty - takes priority |
| DO-PM | Direct observation - takes priority |

### Faculty Rotations (Different Pattern)

Faculty rotations (FMIT-FAC-AM, FMIT-FAC-PM) have different patterns based on their teaching responsibilities.

### Off/Leave Types (No Academic Requirements)

- HILO-PGY3, KAPI, OFF-AM, OFF-PM, etc.
- LV-AM, LV-PM (Leave)
- W-AM, W-PM (Weekend)

---

## Clinic Distribution by PGY Level

### PGY-1 (Interns)

| Rotation | Clinic Day | Clinic Time | Half-Days |
|----------|------------|-------------|-----------|
| FMC | Wednesday | AM | 3 (weeks 1-3) |
| IM-PGY1 | Wednesday | AM | 3 (weeks 1-3) |
| PEDS-WARD-PGY1 | Wednesday | AM | 3 (weeks 1-3) |
| KAPI-LD-PGY1 | Wednesday | AM | 3 (weeks 1-3) |
| PROC-AM | Wednesday | AM | 3 (weeks 1-3) |
| TAMC-LD | Wednesday | AM | 3 (weeks 1-3) |
| MSK-SEL | Wednesday | AM | 3 (weeks 1-3) |
| FMIT-PGY1 | Wednesday | AM | 3 (weeks 1-3) |

**Pattern:** Intern clinic is always Wednesday morning before lecture.

### PGY-2 (FMIT)

| Rotation | Clinic Day | Clinic Time | Half-Days |
|----------|------------|-------------|-----------|
| FMIT-PGY2 | Tuesday | PM | 4 (all weeks) |

**Pattern:** FMIT-R residents have Tuesday afternoon clinic.

### PGY-3 (FMIT)

| Rotation | Clinic Day | Clinic Time | Half-Days |
|----------|------------|-------------|-----------|
| FMIT-PGY3 | Monday | PM | 4 (all weeks) |

**Pattern:** FMIT-PA residents have Monday afternoon clinic (inpatient follow-ups).

### PGY-2/3 (Specialty Rotations)

| Rotation Type | Clinic Half-Days | Placement |
|---------------|------------------|-----------|
| DERM, ELEC, GYN, NEURO, etc. | 3 | **Flexible - solver decides** |

**Pattern:** Residents on specialty rotations get 3 half-days of clinic. The solver places them in available slots around protected academic time.

---

## Current System Metrics

| Metric | Count |
|--------|-------|
| Total protected patterns | 433 |
| Total activity requirements | 166 |
| Templates with LEC patterns | 79 |
| Templates with ADV patterns | 48 |
| Templates with FM clinic patterns | 12 |

---

## How Absences Are Handled

### Two Systems for Absences

The system tracks absences in two ways:

| System | Purpose | Example |
|--------|---------|---------|
| **Absences Table** | Actual leave requests (annual, sick, TDY) | "Dr. Smith on leave Jan 15-17" |
| **Absence Rotation Templates** | Display placeholders for blocked time | LV-AM, LV-PM, W-AM, W-PM |

### Absences Table

When a resident requests leave, it's recorded in the `absences` table:

| Field | Purpose |
|-------|---------|
| `person_id` | Who is absent |
| `start_date`, `end_date` | When |
| `absence_type` | Type (annual, sick, TDY, etc.) |
| `is_blocking` | Should this block assignments? |
| `deployment_orders` | Military deployment? |

**Key field: `is_blocking`** - If true, no assignments will be generated for this person during this period.

### Absence Rotation Templates

These are "placeholder" rotation templates used to show blocked time in the UI:

| Template | Purpose |
|----------|---------|
| LV-AM | Leave (morning) |
| LV-PM | Leave (afternoon) |
| W-AM | Weekend (morning) |
| W-PM | Weekend (afternoon) |

These have `activity_type = 'absence'` and are NOT scheduled by the solver - they're used for display purposes.

### How Absences Affect Schedule Generation

During block assignment expansion:

1. **Check if person is absent** for each day
2. **If absent (blocking)** → Skip generating assignments for that day
3. **If weekend** → Skip (unless rotation includes weekends)
4. **If 1-in-7 forced day off** → Skip and reset counter

**Important:** Absence days are NOT filled with any activity - they're simply skipped.

### How Absences Appear on the Schedule

**Question:** When someone is on leave, what shows in their schedule slot?

| Scenario | What's Generated | What Displays |
|----------|-----------------|---------------|
| Regular work day | Assignment with rotation activity | "FMIT", "LEC", etc. |
| Weekend (no work) | Assignment with W activity | "W-AM/W-PM" |
| Leave/TDY (blocking) | Assignment with LV activity | "LV-AM/LV-PM" |
| 1-in-7 day off | Assignment with OFF activity | "OFF" |

### The 56-Assignment Rule (Quick Validation)

**Every resident should have exactly 56 assignments per block:**

```
28 days × 2 slots (AM + PM) = 56 half-day assignments
```

This is a fast human check:
- **56 assignments** → Schedule is complete
- **< 56 assignments** → Something is missing (gap in coverage)

**Why this matters:** By generating assignments for ALL slots (including weekends, leave, and days off), we can quickly validate schedule completeness with a simple count.

| Day Type | Activity Code | Counts Toward 56? |
|----------|---------------|-------------------|
| Work day | FMIT, LEC, etc. | Yes |
| Weekend | W | Yes |
| Leave | LV | Yes |
| Day off | OFF | Yes |

**Current behavior:** The expansion service **skips** generating assignments for absent/weekend days.

**Proposed change:** Generate assignments for ALL 56 slots, using W, LV, or OFF activities for non-work days. This enables the simple count validation.

**Visual Example:**
```
Dr. Smith on FMIT, with leave Jan 15-16:

                Mon 13   Tue 14   Wed 15   Thu 16   Fri 17
              +--------+--------+--------+--------+--------+
  AM          |  FMIT  |  FMIT  |   LV   |   LV   |  FMIT  |
              +--------+--------+--------+--------+--------+
  PM          |  FMIT  |  FMIT  |   LV   |   LV   |  FMIT  |
              +--------+--------+--------+--------+--------+
                                    ^        ^
                                    |________|
                                    Absence shown as "LV" (orthogonal to rotation)
```

**Key point:** The absence (LV) is **orthogonal** to the rotation - the resident is still "on FMIT" for the block, but those specific days show as leave. The underlying block assignment (FMIT) doesn't change.

---

## Preloaded vs Solved Slots

### Preloaded Slots (Protected Patterns)

These are **fixed in advance** via `weekly_patterns` with `is_protected = true`:

| What | When Placed | Can Solver Move? |
|------|-------------|------------------|
| Wednesday LEC | Before solver runs | No |
| Wednesday ADV | Before solver runs | No |
| Intern clinic (Wed AM) | Before solver runs | No |
| FMIT clinic (specific days) | Before solver runs | No |

**Preloaded slots appear in the schedule exactly as defined in the pattern.**

### Solved Slots (Activity Requirements)

These are **placed by the solver** based on `rotation_activity_requirements`:

| What | When Placed | Where? |
|------|-------------|--------|
| Specialty rotation clinic | During solver run | Solver decides |
| Additional activities | During solver run | Available slots |

**Solved slots are placed in available slots after protected patterns and absences are accounted for.**

### Visual Example: DERM Rotation (Week 1)

```
                Mon     Tue     Wed       Thu     Fri
              +-------+-------+---------+-------+-------+
  AM          |  ???  |  ???  |   ???   |  ???  |  ???  |
              +-------+-------+---------+-------+-------+
  PM          |  ???  |  ???  |   LEC   |  ???  |  ???  |
              +-------+-------+---------+-------+-------+
                                  ^
                                  |
                            PRELOADED (protected pattern)

After solver runs:

                Mon     Tue     Wed       Thu     Fri
              +-------+-------+---------+-------+-------+
  AM          | SPEC  | SPEC  |  CLIN   | SPEC  | SPEC  |
              +-------+-------+---------+-------+-------+
  PM          | SPEC  | CLIN  |   LEC   | SPEC  | CLIN  |
              +-------+-------+---------+-------+-------+
                        ^                          ^
                        |                          |
                  SOLVED (3 clinic half-days placed by solver)
```

### Key Difference

| Aspect | Preloaded (Protected) | Solved (Flexible) |
|--------|----------------------|-------------------|
| Defined by | `weekly_patterns` table | `rotation_activity_requirements` |
| When placed | Before solver | During solver |
| Location | Fixed (specific day/time/week) | Flexible (solver decides) |
| Can be moved | No | Yes (within constraints) |
| Examples | LEC, ADV, intern clinic | Specialty clinic (3 half-days) |

---

## ACGME 1-in-7 Rule and Absences

### The Rule

Residents must have **1 day off per 7 days**, averaged over 4 weeks.

ACGME source (Common Program Requirements, Residency 2026):
- 6.21.b: "Residents must be scheduled for a minimum of one day in seven free of clinical work and required education (when averaged over four weeks). At-home call cannot be assigned on these free days."
- Background/Intent: "It is desirable that days off be distributed throughout the month..."
- PDF: https://www.acgme.org/globalassets/pfassets/programrequirements/2026-prs/cprresidency_2026.pdf

### How Absences Affect the Counter

**Critical distinction:**

| Situation | Counter Behavior | Rationale |
|-----------|------------------|-----------|
| **Scheduled day off** (weekend, forced) | RESETS to 0 | This is the required rest day |
| **Absence** (leave, TDY, sick) | HOLDS (no change) | Leave ≠ scheduled day off |

### Why Absences Don't Reset the Counter

1. **Leave is separate from ACGME rest** - Annual leave is a benefit, not a compliance mechanism
2. **Schedule must be compliant independent of leave** - Can't rely on leave for rest days
3. **Prevents gaming** - Can't work 6 days → take leave → work 6 days → take leave...
4. **Ensures distribution** - Rest days are spread throughout the block

**Example:**
```
Days 1-5: Work (counter = 5)
Day 6: Annual Leave (counter HOLDS at 5)
Day 7: Return to work (counter = 6, approaching limit!)
Day 8: Forced day off (counter RESETS to 0)
```

If leave reset the counter, Day 7 would be counter = 1 and no forced day off would occur.

---

## How the Solver Works

1. **Lock protected patterns first** - Wednesday LEC/ADV, fixed clinic times
2. **Check available slots** - Total slots minus protected minus weekends minus absences
3. **Satisfy requirements** - Place flexible activities (specialty clinic) in available slots
4. **Fill remaining** - Use rotation's default activity type (inpatient, outpatient, specialty)

**Example for DERM rotation:**
- Protected: LEC (4 half-days), ADV (1 half-day)
- Requirement: fm_clinic (3 half-days, flexible)
- Remaining: specialty activities

The solver places 3 clinic half-days somewhere in the available Mon-Fri slots (not Wednesday PM which is lecture).

---

## Questions for PD Review

1. **56-Assignment Rule** - Should we generate assignments for ALL 56 slots (including W, LV, OFF) to enable simple count validation?

2. **Clinic distribution** - Is 3 half-days correct for all specialty rotations, or should some have more/less?

3. **PCAT/DO exceptions** - Are there other rotations that should win over Wednesday activities?

4. **Night Float patterns** - Should NF rotations have any academic time requirements?

5. **Faculty patterns** - What patterns should FMIT-FAC-AM and FMIT-FAC-PM have?

6. **New rotation setup** - When adding a new rotation template, what's the default pattern?

---

## Technical Notes (For Reference)

### Database Tables

| Table | Purpose |
|-------|---------|
| `rotation_templates` | Defines rotations (FMC, FMIT-PGY1, etc.) |
| `weekly_patterns` | Protected activity slots (LEC on Wed PM) |
| `rotation_activity_requirements` | Quantity requirements (3 clinic half-days) |
| `activities` | Activity definitions (lec, advising, fm_clinic) |

### Activity Codes

| Code | Description |
|------|-------------|
| `lec` | Lecture (academic) |
| `advising` | Faculty advising (academic) |
| `fm_clinic` | FM clinic (clinical) |
| `fm_clinic_i` | FM clinic inpatient follow-ups |

### Constraint System

Two constraints enforce the hybrid model:
- `ProtectedSlotConstraint` - Prevents solver from overwriting locked patterns
- `ActivityRequirementConstraint` - Validates activity counts are met

---

## Resilience UI Addendum (Keystone Summary)

Planned: report-only keystone summary surfaced in the resilience dashboard. This is informational only and does not gate solver runs.

Implementation outline:
- Compute keystones during the health check, using rotation templates as "services" (service_id = rotation_template_id).
- Derive service coverage from current assignments (providers per rotation in the period).
- Return a small summary (total, critical, top 5) in the health response.
- Optionally persist to `metrics_snapshot` for historical viewing.
- UI renders a compact panel with risk levels (no automation or policy actions).

Notes:
- NetworkX improves fidelity but the analysis degrades gracefully without it.
- No changes to solver behavior; this remains observational.

---

*This document is for PD review. Do not ingest into RAG until finalized.*
