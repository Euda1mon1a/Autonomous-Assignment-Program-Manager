# TAMC Family Medicine Scheduling Policies

## Overview

The Residency Scheduler generates ACGME-compliant schedules for the TAMC Family Medicine residency program. This document covers the scheduling architecture, activity codes, constraints, and solver mechanics.

## Block Structure

- **Academic Year:** 13 rotation blocks (4 weeks each)
- **Half-Day Slots:** Each day divided into AM and PM sessions
- **Schedule Unit:** One person + one half-day slot + one activity code

Residents rotate through clinical services (IM, Peds, OB, Surgery, etc.) and return to FMC (Family Medicine Clinic) blocks where the CP-SAT solver assigns daily activities.

## Activity Codes

| Code | Name | Who | Description |
|------|------|-----|-------------|
| C | Clinic | Faculty/Resident | Seeing own patients, generates patient load |
| AT | Attending | Faculty | Supervising residents in clinic (precepting) |
| CV | Virtual Clinic | Faculty/Resident | Telemedicine, same as C but virtual |
| SM | Sports Medicine | Faculty/Resident | SM clinic, requires SM-credentialed faculty |
| VAS | Vasectomy | Faculty/Resident | Dedicated 1:1 faculty supervision, minor surgery |
| PROC | Procedure | Resident | Procedure clinic, requires credentialed faculty |
| ADM | Admin | Faculty | GME admin, DFM duties |
| FMIT | FM Inpatient Team | Faculty | Inpatient service (preloaded, not solver-assigned) |
| NF | Night Float | Resident | Overnight coverage rotation |
| FLX | Flex | Resident | Protected study/admin time |
| LV | Leave | Both | Vacation, sick, personal |
| PC | Post-Call | Faculty | Day off after inpatient call |
| PCAT | Post-Call Admin | Faculty | Admin time after overnight call |
| LEC | Lecture | Resident | Wednesday AM didactics |
| ADV | Advising | Resident | Last Wednesday PM advising sessions |
| OIC | Officer in Charge | Faculty | Administrative duty day |

## Two-Grid CP-SAT Architecture

The scheduling system uses two separate CP-SAT solvers that run in sequence:

### Grid 1: Main Solver (`solvers.py`)

Assigns faculty to activities (C, AT, SM, ADM) and residents to rotations. Faculty decisions here are **authoritative** — the activity solver cannot override them.

### Grid 2: Activity Solver (`activity_solver.py`)

Assigns specific half-day activities to residents. By default (`include_faculty_slots=False`), faculty appear as **frozen baselines** — the activity solver can see them but not move them.

Think of it as two whiteboards:
- **Whiteboard 1:** Both faculty and residents, filled in first
- **Whiteboard 2:** Only residents, with faculty photocopied as read-only reference

### Why Two Grids?

If both solvers could move faculty, they'd fight each other. The main solver makes faculty assignments; the activity solver respects them as fixed inputs.

## Faculty Alignment Constraints

### SM Alignment (Same-Grid)

SM faculty are on the activity solver's grid (when `include_faculty_slots=True`). The solver has full control: "if SM resident is here, SM faculty must be here too."

### VAS Override (Frozen-Grid with Holes)

VAS faculty are on the frozen grid. The activity solver creates targeted **override variables** — binary checkboxes that say "steal this faculty from their current activity and reassign to VAS."

Override candidates must meet ALL criteria:
- Faculty is VAS-credentialed (`_is_vas_faculty()`)
- Slot is VAS-eligible (Thu AM, Thu PM, Fri AM only)
- Faculty has a current activity to override

This works elegantly because VAS is narrow: only 3 half-day slots per week, ~24 override variables per block. The solver sees the full trade-off: pulling a faculty to VAS (cost 8) means one less AT preceptor.

### When Override vs Post-Solve

| Approach | When to Use | Example |
|----------|-------------|---------|
| **In-solver override** | Activity competes for shared resources | VAS, PROC — pulling faculty affects AT coverage |
| **Post-solve conversion** | 1:1 relabel with no side effects | C to CV — same room, same supervision |

**Rule:** If reassigning faculty changes what other people can do, it MUST be in the solver.

## Credential Penalty System

The solver applies a soft penalty when faculty are assigned to procedures they are not credentialed for.

**Environment Variable:** `FACULTY_CREDENTIAL_MISMATCH_PENALTY`
- **Default:** 15
- **Range:** 0 (disabled) to 40 (very strict)
- **Tuning:** Higher values make the solver try harder to match credentialed faculty

This is a **soft constraint** — it won't make the model infeasible. If no credentialed faculty is available, the solver assigns whoever is available but pays the penalty.

## Faculty Clinic Caps

Faculty have per-week MIN and MAX clinic (C) limits. These are hard constraints in the main solver.

- C (Clinic) counts toward caps
- AT (Attending/supervision) does NOT count — unlimited

## Physical Capacity

**Max 6 clinical workers per half-day.** This counts anyone generating patient load: C, CV, PROC, VAS. AT supervision does NOT count.

## AT Coverage (ACGME Supervision)

Faculty in C, PCAT, or CV provide AT supervision coverage. The solver ensures enough faculty are in these activities to meet resident supervision demand.

AT demand by resident type:
- PGY-1: 0.5 AT per resident
- PGY-2/3: 0.25 AT per resident
- PROC: 1.0 AT (dedicated faculty)
- VAS: 1.0 AT (dedicated faculty, via override)

## Penalty Hierarchy

The solver minimizes total penalty. Higher weight = avoid at all costs.

| Penalty | Weight | Meaning |
|---------|--------|---------|
| AT_COVERAGE_SHORTFALL | 50 | Not enough faculty supervising residents |
| CLINIC_OVERAGE | 40 | Faculty exceeding clinic cap |
| VAS/SM_ALIGNMENT_SHORTFALL | 30 | Resident doing VAS/SM without matching faculty |
| CLINIC_MIN_SHORTFALL | 25 | Faculty not meeting minimum clinic |
| OIC_CLINICAL_AVOID | 18 | OIC on dispreferred clinical day |
| CREDENTIAL_MISMATCH | 15 | Faculty doing uncredentialed procedure |
| ADMIN/AT_EQUITY | 12 | Uneven admin or supervision distribution |
| PHYSICAL_CAPACITY_SOFT | 10 | More than 6 clinical workers in half-day |
| VAS_OVERRIDE | 8 | Cost of pulling faculty from AT/clinic to VAS |

The solver will pull a faculty to VAS (cost 8) rather than leave a VAS shortfall (cost 30), but won't pull unnecessarily.

## Preloaded Activities

These activities are locked before the solver runs and cannot be changed:

FMIT, LV, PC, LEC, SIM, HAFP, USAFP, BLS, DEP, PI, MM, HOL, TDY, W (weekend)

## Schedule Generation Pipeline

1. **Preload phase** — Lock FMIT, leave, conferences, holidays
2. **Main CP-SAT solve** — Faculty activities (C, AT, SM, ADM), resident rotations
3. **Activity solve** — Resident half-day activities, VAS overrides
4. **Validation** — ACGME compliance check, coverage verification

## Coverage Gap Prevention

- **N-1 analysis:** Can the schedule survive loss of any single resident?
- **N-2 analysis:** Can critical services survive loss of two residents?
- **Real-time gap detection:** Identifies blocks below minimum coverage
- **Contingency planning:** Pre-computed fallback assignments

## Schedule Publication

- **4-6 weeks ahead:** Core rotation schedules published
- **2-3 weeks ahead:** Call schedules and weekend coverage finalized
- **1 week ahead:** Final adjustments
- **Post-publication changes:** Require formal swap request and approval
