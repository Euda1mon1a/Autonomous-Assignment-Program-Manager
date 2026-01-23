# Rotation Template Half-Day Comparison

**Generated:** 2026-01-22
**Purpose:** Compare database rotation templates vs Excel Templates sheet before Codex populates values
**Backup:** `backups/20260122_102856_Pre-Codex half-day rotation template values/`

---

## Executive Summary

| Metric | Database | Excel |
|--------|----------|-------|
| **Total Templates** | 87 | 90 |
| **Templates with Half-Day Patterns** | 79 (partial) | 88 (complete) |
| **Max Patterns per Template** | 9 | 56 |
| **Expected Patterns per Template** | 56 (7 days × 2 × 4 weeks) | 56 |

### Key Findings

1. **Database templates have INCOMPLETE patterns** - Most have only 5-9 patterns instead of the expected 56
2. **Naming mismatch** - Excel uses descriptive names with dates; DB uses standardized abbreviations
3. **Structure difference** - Excel is a 4-week grid; DB uses `weekly_patterns` table with (week_number, day_of_week, time_of_day)
4. **Both use similar activities** - C (Clinic), LEC (Lecture), NF (Night Float), etc.

---

## Database Schema Understanding

### Table: `weekly_patterns`

| Column | Type | Description |
|--------|------|-------------|
| `rotation_template_id` | UUID | FK to rotation_templates |
| `week_number` | int | 1-4 for block weeks |
| `day_of_week` | int | 0=Mon, 1=Tue, ..., 6=Sun |
| `time_of_day` | varchar(2) | 'AM' or 'PM' |
| `activity_type` | varchar(50) | Type category |
| `activity_id` | UUID | FK to activities table |

**Expected entries per template:** 7 days × 2 half-days × 4 weeks = **56 patterns**

### Table: `rotation_halfday_requirements`

Alternative summary table with aggregate counts:
- `fm_clinic_halfdays` - Total FM clinic half-days
- `specialty_halfdays` - Total specialty half-days
- `academics_halfdays` - Total academic half-days

**Current state:** All 87 templates have 0 entries in this table

---

## Database Templates (87)

### By Category

| Category | Count | Templates |
|----------|-------|-----------|
| **rotation** | 62 | FMIT-PGY1/2/3, FMC, NF variants, EM, ICU, etc. |
| **time_off** | 9 | HILO-PGY3, JAPAN, KAPI, OKI, MILITARY, OFF-AM/PM, PC |
| **educational** | 6 | GME-AM/PM, LEC-AM/PM, FMO, FAC-DEV |
| **absence** | 4 | LV-AM/PM, W-AM/PM |

### Pattern Coverage (Current State)

```
Templates with patterns: 79 of 87
Templates with 0 patterns: 8 (NF, PSYCH, PEDS-EM, Japan, Military, PCAT-AM, etc.)

Pattern distribution:
  - 8-9 patterns: 12 templates (FMIT, FMC, IM, Procedures, etc.)
  - 5 patterns: 67 templates (most others)
  - 0 patterns: 8 templates
```

---

## Excel Templates Sheet (90)

### By PGY Level

| Section | Count | Examples |
|---------|-------|----------|
| **PGY 3 Rotations** | 11 | Geriatrics, FMIT PGY-3, Med Select, NICU/NF, Psych, Derm |
| **PGY 2 Rotations** | 13 | Cardiology, ER R2, FMIT 2A, GYN, L&D Pit-Boss, Sports Med |
| **PGY 1 Rotations** | 66 | ER, FMC, FMIT 1, ICU, L&D, Medicine Ward, NBN, Peds, etc. |

### Pattern Completeness

```
Templates with 56/56 half-days: 83 (fully specified)
Templates with 54-55/56: 5 (nearly complete)
Templates with 17/56: 1 (Endocrine 2-week partial)
Templates with 0-1/56: 3 (placeholders/empty)
```

---

## Name Mapping: Excel → Database

### Direct Matches

| Excel Name | DB Abbreviation | Status |
|------------|-----------------|--------|
| FMIT PGY-3 | FMIT-PGY3 | Match |
| FMIT 1 | FMIT-PGY1 | Match |
| Night Float * | NF | Match |
| Emergency Room | EM | Match |
| Medicine Ward | IM | Match |
| Newborn Nursery | NBN | Match |
| FM Orientation | FMO | Match |

### Requires Mapping

| Excel Name | Likely DB Match | Notes |
|------------|-----------------|-------|
| Geriatrics 7/20 | GERI | Date suffix = last updated |
| FMC 4/21 | FMC | Date suffix |
| Night Float * / Cards 7/26 | NF-CARDIO | Combined rotation |
| NICU/NF 7/26 | NIC | Combined rotation |
| Peds ER 7/20 | PEDS-EM | Name variation |
| ICU (Hilo) | HILO-PGY3 | Off-site variant |
| Derm (2 weeks) | DERM or D+N | Partial block |
| Cardiology 08/22 | CARDIO or C+N | Version date |
| CM/PM & RSH 4/21 | ? | No clear match |
| L&D Pit-Boss Nights | NF-LD | Night L&D variant |

### Missing from Database

| Excel Template | Notes |
|----------------|-------|
| SM Rotator | Placeholder in Excel (0/56) |
| Elective Opportunity Examples | Placeholder |
| Psych 2 week | Placeholder (0/56) |
| ARCHIVED ROTATIONS section | Historical |
| Multiple version-dated templates | GYN*3/21, GYN*11/19, etc. |

### Missing from Excel

| DB Template | Notes |
|-------------|-------|
| PCAT-AM | Procedure clinic |
| Direct Observation PM (DO-PM) | Teaching activity |
| Several half-day variants | Already in Excel as full slots |

---

## What Codex Should Populate

### Primary Task: `weekly_patterns` Table

For each rotation template, Codex should create 56 entries:
- 4 weeks × 7 days × 2 half-days = 56 rows per template

**Fields to populate:**
```sql
INSERT INTO weekly_patterns (
  id,                    -- UUID
  rotation_template_id,  -- FK to rotation_templates
  week_number,           -- 1, 2, 3, or 4
  day_of_week,          -- 0=Mon through 6=Sun
  time_of_day,          -- 'AM' or 'PM'
  activity_type,        -- from Excel cell value
  activity_id,          -- FK to activities (lookup by code)
  is_protected,         -- false unless locked
  created_at,           -- now()
  updated_at            -- now()
)
```

### Secondary Task: `rotation_halfday_requirements` Table

Aggregate summary for scheduler optimization:
```sql
INSERT INTO rotation_halfday_requirements (
  id,
  rotation_template_id,
  fm_clinic_halfdays,        -- COUNT where activity = 'C' or 'FMC'
  specialty_halfdays,        -- COUNT where activity = rotation-specific
  specialty_name,            -- e.g., 'Cardiology', 'Surgery'
  academics_halfdays,        -- COUNT where activity = 'LEC' or 'GME'
  elective_halfdays,         -- COUNT where activity = 'ELEC'
  min_consecutive_specialty, -- derived from pattern
  prefer_combined_clinic_days -- true if AM+PM clinic on same day
)
```

---

## Activity Code Mapping (Excel → DB)

| Excel Value | DB `activity_type` | DB `activities.code` |
|-------------|-------------------|----------------------|
| C | fm_clinic | fm_clinic |
| FMC | fm_clinic | fm_clinic |
| LEC | lecture | lec |
| ADV | advising | advising |
| GME | education | gme |
| NF | night_float | night_float |
| FMIT | inpatient | fmit_ward |
| PROC | procedures | procedures |
| OFF | time_off | off |
| LV | leave | leave |
| W | weekend | weekend |
| PC | post_call | post_call |
| AT | teaching | at_supervise |
| PEDS | pediatrics | peds_clinic |
| Cards/CARDIO | specialty | cardiology |
| DERM | specialty | dermatology |
| SURG | specialty | surgery |
| EM/ER | emergency | em |
| ICU | icu | icu |
| L&D | labor_delivery | labor_delivery |
| NBN | newborn | nbn |
| NICU | nicu | nicu |
| PSYCH | psychiatry | psychiatry |
| MSK | specialty | msk |
| NEURO | specialty | neurology |
| GYN | specialty | gyn |
| GERI | specialty | geriatrics |

---

## Validation Checklist for Codex

Before committing changes:

- [ ] Total weekly_patterns entries = 87 templates × 56 slots = 4,872
- [ ] Each template has exactly 56 patterns (or justified exception)
- [ ] All activity_id values are valid FKs to activities table
- [ ] No duplicate (template_id, week_number, day_of_week, time_of_day) combinations
- [ ] rotation_halfday_requirements has 87 entries (one per template)
- [ ] Aggregate counts match weekly_patterns detail

---

## CP-SAT Translation Strategy

### The Core Problem

The Excel templates show **solved schedules** - the final answer. But CP-SAT needs:
1. **Constraints** - What rules must be satisfied
2. **Variables** - What the solver decides
3. **Objectives** - What to optimize

**NOT everything in Excel should be a fixed pattern.** We need to decompose each template into:

| Category | Storage | CP-SAT Role |
|----------|---------|-------------|
| **Fixed Slots** | `weekly_patterns` (is_protected=true) | Constants, not variables |
| **Required Counts** | `rotation_halfday_requirements` | Hard constraints |
| **Soft Preferences** | `rotation_halfday_requirements` flags | Soft constraints (cost) |
| **Fill Slots** | Solver output | Decision variables |

---

## Template Decomposition: What to Extract

### 1. FIXED SLOTS (Hard-coded, non-negotiable)

These are slots that are ALWAYS the same for a rotation type. Store in `weekly_patterns` with `is_protected=true`.

**Common Fixed Patterns:**

| Pattern | Applies To | Rationale |
|---------|-----------|-----------|
| Wed PM = Lecture | Most PGY-1 rotations | Mandatory didactics |
| Wed AM = Clinic | FMC, FMIT interns | Protected clinic continuity |
| Sat/Sun = OFF or specialty | All rotations | Weekend coverage rules |
| Night Float = NF all week | NF rotations | By definition |
| Post-call AM = PC | Day after NF | ACGME requirement |

**Extraction Rule:** If a slot has the SAME value across >90% of Excel variants for that rotation type, mark it FIXED.

### 2. REQUIRED COUNTS (Hard Constraints for Solver)

Store in `rotation_halfday_requirements`. These become CP-SAT constraints like:
```python
model.Add(sum(clinic_vars) == template.fm_clinic_halfdays)
model.Add(sum(specialty_vars) == template.specialty_halfdays)
```

**Extract from Excel:**

| Field | How to Calculate | Example |
|-------|------------------|---------|
| `fm_clinic_halfdays` | COUNT(C, FMC, C-AM, C-PM) | FMC: 8-10 |
| `specialty_halfdays` | COUNT(rotation-specific activity) | Cardio: 40 |
| `academics_halfdays` | COUNT(LEC, GME, ADV) | Most: 4-8 |
| `elective_halfdays` | COUNT(ELEC, flexible) | Usually 0 |

### 3. SOFT PREFERENCES (Optimization Objectives)

Store as flags in `rotation_halfday_requirements`:

| Flag | Meaning | CP-SAT Translation |
|------|---------|-------------------|
| `prefer_combined_clinic_days` | AM+PM clinic same day | Minimize clinic day count |
| `min_consecutive_specialty` | Group specialty blocks | Minimize specialty transitions |

**Extraction Rule:** Analyze Excel patterns for clustering behavior.

### 4. DERIVED CONSTRAINTS (Implicit Rules)

These aren't stored - they're built into the solver logic:

| Rule | Constraint |
|------|------------|
| **Post-call recovery** | If slot[day-1, PM] = NF, then slot[day, AM] = PC |
| **No double-booking** | Each half-day has exactly one activity |
| **Weekend continuity** | If Sat AM = X, often Sat PM = X |
| **ACGME hours** | Max 80 hrs/week, 1 day off per 7 |

---

## Recommended Template Classifications

### Class A: Fully Fixed (Solver Input, Not Variables)

These rotations are 100% predetermined. Solver reads them as **constants** that consume resources (supervision, space, clinic slots).

| Template | Pattern | Solver Role |
|----------|---------|-------------|
| **FMIT-PGY1/2/3** | Ward + PGY-specific clinic day | Counts against ward capacity, requires faculty supervision |
| Night Float (NF) | All slots = NF or PC | Counts against night coverage |
| Leave (LV-AM/PM) | All slots = LV | Reduces available workforce |
| Weekend (W-AM/PM) | All slots = W | Weekend off |
| OFF-AM/PM | All slots = OFF | Time off |
| Post-Call (PC) | All slots = PC | ACGME recovery requirement |
| Off-site (JAPAN, OKI, HILO, KAPI) | All slots = off-site | Not available locally |

**Storage:** Full 56-slot pattern in `weekly_patterns`, all `is_protected=true`.

**CP-SAT Treatment:**
```python
# Class A templates are CONSTANTS, not variables
# They create constraints for other assignments:
for slot in class_a_template.slots:
    occupied_slots.add(slot)  # Can't double-book
    if slot.activity == FMIT:
        ward_census[slot.time] += 1  # Supervision constraint
    if slot.activity == CLINIC:
        clinic_demand[slot.time] += 1  # Room constraint
```

### Class B: Partially Fixed (Some Solver Freedom)

These have fixed institutional slots plus flexible distribution:

| Template | Fixed Slots | Solver Decides |
|----------|-------------|----------------|
| FMC | Weekends=W, Wed PM=academics | Clinic day distribution |
| IM-PGY1 | Wed PM=LEC | Ward vs clinic balance |
| Specialty rotations | Wed PM often fixed | Specialty block clustering |

**Storage:**
- Fixed slots in `weekly_patterns` (is_protected=true)
- Counts in `rotation_halfday_requirements`
- Solver fills remaining slots

### Class C: Count-Only (Full Solver Freedom)

Solver has complete freedom on slot placement, only respects total counts:

| Template | Constraints |
|----------|-------------|
| Elective | X clinic + Y elective + Z academic |
| Medical Selective | X specialty + Y clinic |

**Storage:** Only `rotation_halfday_requirements` (no protected weekly_patterns).

---

## Specific Template Recommendations

### FMIT Rotations (PGY-1, PGY-2, PGY-3)

**100% FIXED - NOT SOLVER VARIABLES**

FMIT rotations are completely predetermined. CP-SAT does NOT optimize these - it only recognizes them as **occupied slots** that count against:
- **Supervision constraints** (faculty attending must be assigned)
- **Physical space constraints** (ward beds, clinic rooms)

#### FMIT PGY-1 (Intern)
```
ALL 56 SLOTS FIXED (from Excel "FMIT 1"):
  Week 1: Wed AM = C, Wed PM = LEC, all others = FMIT
  Week 2: Wed AM = C, Wed PM = LEC, all others = FMIT
  Week 3: Wed AM = C, Wed PM = PI, all others = FMIT
  Week 4: Wed AM = LEC, Wed PM = GME, all others = FMIT

TOTALS:
  - FMIT (ward): 48 half-days
  - Clinic (C): 3 half-days (Wed AM weeks 1-3)
  - Academics: 5 half-days (LEC×3 + PI + GME)
```

#### FMIT PGY-2 (FMIT 2A)
```
ALL 56 SLOTS FIXED (from Excel "FMIT 2A*12/15"):
  All weeks: Tue PM = C, all others = FMIT

TOTALS:
  - FMIT (ward): 52 half-days
  - Clinic (C): 4 half-days (Tue PM all weeks)
```

#### FMIT PGY-3 (Senior)
```
ALL 56 SLOTS FIXED (from Excel "FMIT PGY-3"):
  All weeks: Mon PM = C-I, all others = FMIT

TOTALS:
  - FMIT (ward): 52 half-days
  - Clinic (C-I): 4 half-days (Mon PM all weeks)
```

#### PGY-Specific Clinic Days (Institutionally Mandated)

| PGY | Clinic Day | Clinic Time | Rationale |
|-----|------------|-------------|-----------|
| PGY-1 | Wednesday | AM | Staggered from PGY-2/3 for ward coverage |
| PGY-2 | Tuesday | PM | Staggered from PGY-1/3 for ward coverage |
| PGY-3 | Monday | PM | Supervises intern clinic (C-I) |

#### CP-SAT Role for FMIT

```python
# FMIT is NOT a decision variable - it's a CONSTANT
# Solver reads FMIT assignments and enforces downstream constraints:

for resident in fmit_residents:
    for slot in resident.fmit_slots:
        # These slots are OCCUPIED - not available for other assignments
        model.Add(slot_assignment[resident][slot] == FMIT_ACTIVITY_ID)

        # Count against ward capacity
        ward_census[slot] += 1

        # Require faculty supervision
        model.Add(sum(faculty_on_ward[slot]) >= required_supervision_ratio)
```

**Key Point:** Store full 56-slot pattern in `weekly_patterns` with `is_protected=true`. Solver treats as input data, not optimization target.

### FMC (Family Medicine Clinic)

**Multiple versions exist in Excel with varying clinic distributions.**

```
FIXED SLOTS (consistent across all FMC versions):
  - Sat/Sun ALL weeks: W (weekend off) = 16 half-days
  - Wed PM Week 1: LEC
  - Wed PM Week 2: LEC
  - Wed PM Week 3: PI (procedure instruction)
  - Wed PM Week 4: GME

VARIABLE SLOTS (differ by version/block):
  - Weekday clinic slots: 18-20 half-days of C/C40/C60
  - Procedure slots: PR, VAS, HV, CLC
  - Admin/flex: ADM, FLX, Coding, Orient

COUNTS (from Excel "FMC 4/21"):
  - fm_clinic_halfdays: 18 (C)
  - procedure_halfdays: 7 (PR, VAS, etc.)
  - academics_halfdays: 5 (LEC×3 + PI + GME)
  - weekend_off: 16 (W)
  - admin_flex: 10 (ADM, CLC, etc.)

ACTIVITY CODE VARIATIONS:
  - C = standard clinic
  - C40 = 40-minute appointments (earlier blocks)
  - C60 = 60-minute appointments
  - C40/OMT = clinic with osteopathic manipulation
```

**Key Insight:** FMC has more flexibility than FMIT. The solver could optimize clinic clustering while preserving:
1. Weekend off (fixed)
2. Wednesday PM academics (fixed)
3. Total clinic count (constraint)

### Night Float Variants (NF, NF-CARDIO, NF-FMIT, etc.)

```
FIXED SLOTS (100% predetermined):
  Week 1-2: NF all nights, PC all next mornings
  Week 3-4: Specialty component (Cardio/FMIT/etc.)

REQUIRED COUNTS:
  - night_float_halfdays: 28 (2 weeks)
  - specialty_halfdays: 28 (2 weeks)
  - post_call_halfdays: 14 (after each NF)

NO SOLVER NEEDED - fully determined
```

### Specialty Rotations (Cardiology, Derm, Psych, Surgery, etc.)

```
FIXED SLOTS:
  - Wed PM: Often lecture/conference
  - Weekend: Usually OFF or specialty continuation

REQUIRED COUNTS:
  - specialty_halfdays: 40-50 (dominant activity)
  - fm_clinic_halfdays: 0-4 (continuity clinic if any)
  - academics_halfdays: 2-4

SOFT PREFERENCES:
  - min_consecutive_specialty: 5 (full week blocks preferred)
```

---

## Data Population Strategy

### Phase 1: Class A Templates (Fully Fixed)

Directly copy Excel → `weekly_patterns` for:
- NF, LV, W, OFF, PC, JAPAN, OKI, HILO, KAPI, MILITARY

All 56 slots, `is_protected=true`.

### Phase 2: Class B Templates (Fixed + Counts)

For FMIT, FMC, IM, Peds, etc.:

1. **Identify fixed slots** by analyzing Excel patterns
2. **Calculate counts** from Excel totals
3. **Store fixed slots** in `weekly_patterns` (is_protected=true)
4. **Store counts** in `rotation_halfday_requirements`
5. **Leave remaining slots** for solver to fill

### Phase 3: Class C Templates (Counts Only)

For electives and highly flexible rotations:
- Store only `rotation_halfday_requirements`
- No `weekly_patterns` entries (or all is_protected=false)

---

## CP-SAT Constraint Translation

### From `rotation_halfday_requirements`:

```python
# Hard constraints
model.Add(sum(clinic_vars) == req.fm_clinic_halfdays)
model.Add(sum(specialty_vars) == req.specialty_halfdays)
model.Add(sum(academic_vars) == req.academics_halfdays)

# Soft constraints (minimize violations)
if req.prefer_combined_clinic_days:
    # Penalize clinic half-days that don't have matching AM/PM
    for day in range(7):
        for week in range(4):
            # Cost if clinic_AM xor clinic_PM
            ...

if req.min_consecutive_specialty:
    # Penalize specialty blocks shorter than min
    ...
```

### From `weekly_patterns` (is_protected=true):

```python
# Fixed assignments (not variables)
for pattern in protected_patterns:
    slot_idx = (pattern.week_number, pattern.day_of_week, pattern.time_of_day)
    # This slot is NOT a variable - it's a constant
    assignment[slot_idx] = pattern.activity_id
```

---

## Validation After Population

### Count Verification

For each template:
```sql
SELECT
    rt.name,
    rhr.fm_clinic_halfdays as expected_clinic,
    COUNT(wp.id) FILTER (WHERE wp.activity_type = 'fm_clinic') as actual_clinic,
    rhr.specialty_halfdays as expected_specialty,
    COUNT(wp.id) FILTER (WHERE wp.activity_type = 'specialty') as actual_specialty
FROM rotation_templates rt
LEFT JOIN rotation_halfday_requirements rhr ON rhr.rotation_template_id = rt.id
LEFT JOIN weekly_patterns wp ON wp.rotation_template_id = rt.id
GROUP BY rt.id, rt.name, rhr.fm_clinic_halfdays, rhr.specialty_halfdays;
```

### Consistency Check

- Fully fixed templates (Class A): Should have 56 patterns, all is_protected=true
- Hybrid templates (Class B): Should have some protected + counts matching
- Flexible templates (Class C): Should have counts only, few/no protected patterns

---

## Appendix: Full Database Template List

```
absence (4):
  LV-AM, LV-PM, W-AM, W-PM

educational (6):
  FAC-DEV, FMO, GME-AM, GME-PM, LEC-AM, LEC-PM

rotation (62):
  ACS-AM, ADV-PM, BTX-AM, BTX-PM, CARDIO, C+N, C-AM, C-PM,
  COLP-AM, COLP-PM, DFM-AM, DFM-PM, DERM, D+N, DO-PM, ELEC,
  EM, ENDO, FMC, FMIT-FAC-AM, FMIT-FAC-PM, FMIT-PGY1, FMIT-PGY2,
  FMIT-PGY3, GERI, GYN, HC-AM, HC-PM, ICU, IM-PGY1, IM, LAD,
  SEL-MED, MSK-SEL, NIC, NEURO, NEURO-1ST-NF-2ND, NBN, NICU, NF,
  NF-AM, NF-CARDIO, NF-DERM-PGY2, NF-FMIT-PGY1, NF-LD, NF-MED-SEL,
  NF-NICU-PGY1, NF-PEDS-PGY1, NF-PM, NF-1ST-ENDO-2ND, PCAT-AM,
  PEDS-EM, PEDS-CLIN, PEDS-SUB, PEDS-WARD-PGY1, POCUS, PROC-AM,
  PR-PM, PROC, PSYCH, AT-AM, AT-PM, SM-AM, SM-PM, SURG, TAMC-LD,
  VAS-AM, VAS-PM

time_off (9):
  HILO-PGY3, JAPAN, KAPI, KAPI-LD-PGY1, MILITARY, OFF-AM, OFF-PM, OKI, PC
```

---

## Appendix: Excel Templates Sheet Structure

```
Row 1: Day headers (Th, Fr, Sa, Su, M, Tu, W, Th, Fr, Sa, Su, M, Tu, W, ...)
Row 2: AM/PM headers
Row 3+: Template name | 56 half-day values | # clinics count

4-week block structure:
  Week 1: Days 1-7 (columns B-O)
  Week 2: Days 8-14 (columns P-AC)
  Week 3: Days 15-21 (columns AD-AQ)
  Week 4: Days 22-28 (columns AR-BE)
```
