# Faculty HDA & Call — Complete Logic, Schema, and Excel Pipeline

Context: I'm building a military medical residency scheduling system. Faculty scheduling has cross-block FMIT logic, overnight call assignment, post-call cascading (PCAT/DO), role-based clinic caps, and equity tracking. The master schedule lives in Excel spreadsheets. Below is exactly what we're running — the actual schema, constraint logic, preload pipeline, and Excel rendering. No embellishment.

---

## Infrastructure

PostgreSQL 17.7 (Homebrew, Apple Silicon)
- Database: residency_scheduler
- ORM: SQLAlchemy 2.0.45 (async via asyncpg)
- Migrations: Alembic (117+ migrations)
- Validation: Pydantic 2.12.5
- API: FastAPI 0.128.0
- Excel: openpyxl
- Solver: OR-Tools CP-SAT + PuLP
- Background: Celery + Redis

---

## Core Tables (Live Schema)

### people (56 rows) — Residents & Faculty

```
id                           | uuid           | PK
name                         | varchar(255)   | NOT NULL, indexed
type                         | varchar(50)    | CHECK IN ('resident','faculty')
email                        | varchar(255)   | UNIQUE
pgy_level                    | integer        | CHECK 1-3 (residents only)
faculty_role                 | varchar(50)    | CHECK IN (pd,apd,oic,dept_chief,sports_med,core,adjunct)
specialties                  | varchar[]      | array
clinic_min/max               | integer        | per-week half-day caps
at_min/max                   | integer        | attending time caps
gme_min/max, dfm_min/max    | integer        | admin caps
sm_min/max                   | integer        | sports medicine caps
sunday_call_count            | integer        | default 0, equity tracking
weekday_call_count           | integer        | default 0
fmit_weeks_count             | integer        | default 0
```

### half_day_assignments (17,675 rows) — Daily AM/PM Schedule Grid

```
id                         | uuid        | PK
person_id                  | uuid        | FK → people(id) CASCADE
date                       | date        | NOT NULL
time_of_day                | varchar(2)  | CHECK IN ('AM','PM')
activity_id                | uuid        | FK → activities(id) RESTRICT
source                     | varchar(20) | CHECK IN (preload, manual, solver, template)
block_assignment_id        | uuid        | provenance link to block_assignments
is_override                | boolean     | NOT NULL
counts_toward_fmc_capacity | boolean

UNIQUE(person_id, date, time_of_day)
Source priority: preload > manual > solver > template (higher never overwritten by lower)
```

### call_assignments — Overnight & Weekend Call

```
id          | uuid        | PK
date        | date        | NOT NULL
person_id   | uuid        | FK → people(id) CASCADE
call_type   | varchar(50) | NOT NULL
is_weekend  | boolean     | default false
is_holiday  | boolean     | default false
created_at  | timestamp

UNIQUE(date, person_id, call_type)
DB CHECK (migration): call_type IN ('overnight', 'weekend', 'backup')
ORM CHECK (stale): call_type IN ('sunday', 'weekday', 'holiday', 'backup')
*** NOTE: ORM model CHECK is out of sync with migration. Code writes 'overnight'. DB allows it. ***
```

### inpatient_preloads (62 rows) — Locked Assignments Before Solver Runs

```
id                 | uuid        | PK
person_id          | uuid        | FK → people(id) CASCADE
rotation_type      | varchar(20) | CHECK IN (FMIT, NF, PedW, PedNF, KAP, IM, LDNF)
start_date         | date        | (Friday for FMIT)
end_date           | date        | (Thursday for FMIT)
fmit_week_number   | integer     | 1-4
includes_post_call | boolean     | if true, generate recovery day after end_date

UNIQUE(person_id, start_date, rotation_type)
```

### activities (116 rows) — Slot-Level Events

```
id                              | uuid        | PK
name                            | varchar(255)| UNIQUE
code                            | varchar(50) | UNIQUE — this fills half_day_assignments
display_abbreviation            | varchar(20) | grid cell text
activity_category               | varchar(20) | clinical|educational|administrative|time_off
is_protected                    | boolean     | solver cannot modify
provides_supervision            | boolean     | AT, PCAT, DO
counts_toward_physical_capacity | boolean     | max 6 per half-day
```

### Key Activity Codes Used for Faculty

| Code | Name | Category | When Assigned |
|------|------|----------|---------------|
| C | Clinic | clinical | Regular outpatient clinic half-day |
| SM | Sports Medicine Clinic | clinical | SM faculty + SM rotation residents |
| AT | Attending/Precepting | clinical | Supervision of resident clinic |
| PCAT | Post-Call Attending | clinical | AM after overnight call |
| DO | Direct Observation | clinical | PM after overnight call |
| FMIT | FMIT Inpatient | clinical | All slots during FMIT week (Fri-Thu) |
| CALL | Overnight Call | clinical | PM slot on call night |
| CC | Continuity Clinic | clinical | Resident continuity clinic |
| CV | Cardiovascular | clinical | Specialty clinic |
| GME | Graduate Medical Education | administrative | Admin time |
| DFM | Department of FM | administrative | Departmental duties |
| DOFM | Director of FM | administrative | Director duties |
| LV | Leave | time_off | Vacation/absence |
| OFF | Off | time_off | Day off |
| W | Weekend Off | time_off | Weekend not working |
| PC | Post-Call | time_off | Recovery day after FMIT |

---

## Domain Rules: FMIT Week Structure

FMIT weeks are **independent of 4-week academic blocks**:

```
FMIT Week: Friday (start) → Thursday (end)
Block boundary is irrelevant — FMIT can span blocks.

Week 1 (FMIT Week):
  Fri: FMIT (AM/PM) + Fri night call (MANDATORY — FMIT attending)
  Sat: FMIT (AM/PM) + Sat night call (MANDATORY — FMIT attending)
  Sun: FMIT (AM/PM) — NOT available for Sun-Thu call
  Mon: FMIT (AM/PM) — NOT available for call
  Tue: FMIT (AM/PM) — NOT available for call
  Wed: FMIT (AM/PM) — NOT available for call
  Thu: FMIT (AM/PM) — NOT available for call

Week 2 (Post-FMIT):
  Fri: BLOCKED entirely (recovery day "PC") — no scheduling
  Sat+: Normal availability resumes
```

### Cross-Block Example (Block 10 = Mar 12 – Apr 8)
- Faculty A: FMIT started Fri Mar 7 (Block 9), ends Thu Mar 13 (Block 10)
  - Block 10 sheet shows: 2 FMIT days (Mar 12-13) then PC on Mar 14
- Faculty B: FMIT starts Fri Mar 14, ends Thu Mar 20 (within Block 10)
  - Block 10 sheet shows: full 7 FMIT days
- Faculty C: FMIT starts Fri Apr 4, ends Thu Apr 10 (spans into Block 11)
  - Block 10 sheet shows: 5 FMIT days (Apr 4-8), recovery Fri Apr 9 appears on Block 11

### Faculty Roles & Clinic Caps

| Role | Clinic Half-Days/Week (max) | SM Clinic/Week | FMIT Eligible | Notes |
|------|---------------------------|----------------|---------------|-------|
| PD | 0 | - | Yes (~6/yr) | Leadership/admin focus |
| APD | 2 | - | Yes (~6/yr) | Flexible within block (≤8/block total) |
| OIC | 2 | - | Yes (~6/yr) | Avoid Mon/Fri clinic (soft) |
| DEPT_CHIEF | 1 | - | Yes (~6/yr) | Administrative |
| SPORTS_MED | 0 regular | 4 | Yes (~6/yr) | SM clinic only, blocked from regular C |
| CORE | 4 (max 16/block) | - | Yes (~6/yr) | Standard attending |
| ADJUNCT | 0 | - | Manual only | Not auto-scheduled for anything |

### Call Rules

| Nights | Coverage | Source |
|--------|----------|--------|
| Friday + Saturday | FMIT attending (mandatory) | Preload creates CallAssignment |
| Sunday–Thursday | Non-FMIT, non-absent, non-ADJUNCT faculty | Solver generates exactly 1 per night |

**Post-call cascade (Sun–Thu call only):**
- Next day AM: PCAT (Post-Call Attending)
- Next day PM: DO (Direct Observation)
- Exception: If next day falls within an FMIT preload → skip PCAT/DO

**Call Equity:**
- Sunday call: separate pool, weight 10.0 (worst day)
- Weekday (Mon–Thu): combined pool, weight 5.0
- Holiday: separate pool, weight 7.0
- Call spacing: penalize back-to-back weeks, weight 8.0
- **Per-block only** — no longitudinal history fed to solver

---

## Preload Loading Pipeline (Exact Order of Operations)

`SyncPreloadService.load_all_preloads(block_number, academic_year)`:

```
1. _load_absences(start, end)         → LV-AM, LV-PM for blocking absences
2. _load_institutional_events(start, end) → holidays, retreats
3. _load_rotation_protected_preloads(block, ay) → weekly pattern templates
4. _load_inpatient_preloads(start, end)   → FMIT/NF/etc half-day assignments
5. _load_fmit_call(start, end)            → CallAssignment for Fri/Sat
6. _load_inpatient_clinic(block, ay)      → C-I by PGY (Wed AM/Tue PM/Mon PM)
7. _load_resident_call(start, end)        → CALL at PM
8. _load_faculty_call(start, end)         → CALL PM + PCAT/DO next day
9. _load_sm_preloads(start, end)          → aSM Wed AM for SM faculty
10. _load_compound_rotation_weekends()    → W on weekends for NF compound
```

### _load_fmit_call() Logic

```
Query: InpatientPreload WHERE rotation_type='FMIT'
       AND start_date <= block_end AND end_date >= block_start
       AND person.type = 'faculty'

For each FMIT preload:
    current = max(preload.start_date, block_start)
    end = min(preload.end_date, block_end)

    For each day current..end:
        if current.weekday() in (4, 5):  # Friday=4, Saturday=5
            if no existing CallAssignment(person_id, date, 'overnight'):
                CREATE CallAssignment(
                    person_id, date=current,
                    call_type='overnight',
                    is_weekend=(weekday >= 5)
                )
```

### _load_faculty_call() Logic

```
Query: ALL CallAssignment WHERE date in [block_start, block_end]

For each call:
    1. Create preload: HDA(person_id, call.date, PM, activity=CALL, source=preload)

    2. next_day = call.date + 1
       if NOT _is_on_fmit(person_id, next_day):
           Create preload: HDA(person_id, next_day, AM, activity=PCAT, source=preload)
           Create preload: HDA(person_id, next_day, PM, activity=DO, source=preload)
```

### _is_on_fmit() Logic

```
SELECT InpatientPreload
WHERE person_id = ? AND rotation_type = 'FMIT'
  AND start_date <= date AND end_date >= date
RETURNS: True if any record exists
```

### _create_preload() — Dedup + Priority

```
Check existing HDA at (person_id, date, time_of_day):
  - If source is template/solver → overwrite with preload (preload wins)
  - If source is preload and new is time_off → overwrite (time_off wins)
  - If source is preload and same activity → skip (idempotent)
  - If no existing → create new HDA(source='preload')

IntegrityError on flush → swallow (race condition, another process created it)
```

---

## Constraint System (CP-SAT Solver)

### Constraint Registration (ConstraintManager.create_default())

| Constraint | Type | Weight | Registered | Enabled |
|-----------|------|--------|-----------|---------|
| FMITWeekBlockingConstraint | Hard | — | Yes | **DISABLED** |
| FMITMandatoryCallConstraint | Hard | — | Yes | **DISABLED** |
| PostFMITRecoveryConstraint | Hard | — | Yes | Enabled |
| PostFMITSundayBlockingConstraint | Soft | — | Yes | Enabled |
| FMITContinuityTurfConstraint | Hard | — | **NOT REGISTERED** | Crisis only |
| FMITStaffingFloorConstraint | Hard | — | **NOT REGISTERED** | Crisis only |
| OvernightCallGenerationConstraint | Hard | — | Yes | **DISABLED** |
| PostCallAutoAssignmentConstraint | Soft | 35.0 | Yes | Enabled |
| SundayCallEquityConstraint | Soft | 10.0 | Yes | Enabled |
| WeekdayCallEquityConstraint | Soft | 5.0 | Yes | Enabled |
| HolidayCallEquityConstraint | Soft | 7.0 | Yes | Enabled |
| CallSpacingConstraint | Soft | 8.0 | Yes | Enabled |
| FacultyCallPreferenceConstraint | Soft | 1.0 | Yes | Enabled |
| TuesdayCallPreferenceConstraint | Soft | 2.0 | Yes | Enabled |
| DeptChiefWednesdayPreferenceConstraint | Soft | 1.0 | **NOT REGISTERED** | Missing |
| FacultyRoleClinicConstraint | Hard | — | Yes | Enabled |
| FacultyClinicCapConstraint | Soft | 50.0 | Yes | Enabled |
| SMFacultyClinicConstraint | Hard | — | Yes | **DISABLED** |
| FacultySupervisionConstraint | Hard | — | Yes | Enabled |

### Constraint Logic (Pseudocode)

**get_fmit_week_dates(any_date) → (friday, thursday)**
```
weekday = any_date.weekday()
if weekday >= 4:  # Fri/Sat/Sun
    days_since_friday = weekday - 4
else:             # Mon-Thu
    days_since_friday = weekday + 3
friday = any_date - days_since_friday
thursday = friday + 6
return (friday, thursday)
```

**FMITWeekBlockingConstraint (Hard)**
```
For each faculty with FMIT assignment:
    Derive FMIT week (Fri-Thu) from preload dates
    For each half-day block in FMIT week:
        model.Add(clinic_var == 0)       # Block all clinic templates
        model.Add(call_var == 0)         # Block Sun-Thu call
        # Fri/Sat NOT blocked (mandatory call handled separately)
```

**FMITMandatoryCallConstraint (Hard)**
```
For each FMIT faculty:
    For Friday and Saturday of FMIT week:
        model.Add(call_var == 1)  # Force call assignment
```

**PostFMITRecoveryConstraint (Hard)**
```
For each FMIT preload:
    recovery_friday = thursday_end + 1 day
    For ALL templates and call types on recovery_friday:
        model.Add(var == 0)  # Block everything
```

**OvernightCallGenerationConstraint (Hard)**
```
For each Sun-Thu night in block:
    eligible = [f for f in faculty if:
        - not ADJUNCT
        - not on FMIT that week
        - not post-FMIT Sunday blocked
        - not absent]

    For each eligible faculty:
        var = model.NewBoolVar(f"call_{f_i}_{date}")
        call_assignments[(f_i, b_i, "overnight")] = var

    model.Add(sum(night_vars) == 1)  # Exactly one faculty per night
```

**PostCallAutoAssignmentConstraint (Soft, weight=35.0)**
```
For each overnight call on Sun-Thu:
    next_day = call_date + 1

    # AM: penalize missing PCAT
    shortfall = model.NewIntVar(0, 1, ...)
    model.Add(sum(pcat_vars) + shortfall >= call_var)
    objective += shortfall * 35

    # PM: penalize missing DO (same pattern)

    Skip if next_day block is locked/unavailable
    Skip if next_day falls in FMIT (exempt)
```

**SundayCallEquityConstraint (Soft, weight=10.0)**
```
sunday_blocks = [b for b in blocks if weekday == 6]

For each eligible faculty:
    sunday_count = sum(call_vars for Sundays)

max_sunday = model.NewIntVar(0, num_sundays, "max_sunday")
For each faculty:
    model.Add(sunday_count <= max_sunday)

objective += max_sunday * 10  # Minimize the maximum
```

**WeekdayCallEquityConstraint (Soft, weight=5.0)**
```
Same as Sunday but for Mon-Thu (weekday in 0,1,2,3)
objective += max_weekday * 5
```

**CallSpacingConstraint (Soft, weight=8.0)**
```
Group blocks by ISO week
For each pair of consecutive weeks, for each faculty:
    has_week1 = AddMaxEquality(bool_var, week1_call_vars)
    has_week2 = AddMaxEquality(bool_var, week2_call_vars)
    back_to_back = AddMultiplicationEquality(var, [has_week1, has_week2])
    objective += back_to_back * 8
```

**FacultyRoleClinicConstraint (Hard)**
```
clinic_templates = [t for t in templates if rotation_type == 'outpatient']

For each faculty:
    (min_limit, max_limit) = role-based OR person-specific override
    Group blocks by week (Mon-Sun)

    For each week:
        clinic_vars = [var for clinic template assignments this week]
        model.Add(sum(clinic_vars) <= max_limit)
```

**FacultyClinicCapConstraint (Soft, weight=50.0)**
```
For each faculty, each week (Mon-Fri only, skip weekends):
    clinic_vars = sum of faculty_clinic[(faculty_id, date, AM/PM)]
    model.Add(sum <= max_c)  # Hard upper bound
    # MIN is soft (validation only, no solver constraint)
```

**FacultySupervisionConstraint (Hard, ACGME)**
```
AT demand by PGY: {1: 0.5, 2: 0.25, 3: 0.25} faculty per resident
Scaled by 4 for integer arithmetic.

For each weekday, each slot (AM/PM):
    demand = sum(resident_clinic[r_i] * pgy_demand * 4)
    coverage = sum(faculty_at[f_i] + faculty_pcat[f_i]) * 4
    model.Add(coverage >= demand)
```

---

## Excel Export Pipeline

### Data Flow

```
CanonicalScheduleExportService.export_block_xlsx(include_faculty=True, include_call=True)
  → HalfDayJSONExporter.export(block_start, block_end)
    → Queries HalfDayAssignment + CallAssignment from DB
    → Returns JSON dict:
        {
          "block_start": "2026-03-12",
          "block_end": "2026-04-08",
          "source": "half_day_assignments",
          "residents": [person_dict, ...],
          "faculty": [person_dict, ...],         ← Separated by Person.type
          "call": {"nights": [{"date": "...", "staff": "LASTNAME"}, ...]}
        }
  → JSONToXlsxConverter.convert_from_json(data)
    → Writes to Excel template
  → _stamp_metadata() adds __SYS_META__ and __REF__ hidden sheets
```

### Person Dict Structure (same for faculty and residents)

```python
{
    "name": "Smith, John",          # From Person.name
    "pgy": None,                    # None for faculty, 1-3 for residents
    "rotation1": "",                # From BlockAssignment (often empty for faculty)
    "rotation2": "",                # Secondary rotation
    "days": [                       # One entry per day in block (28 days)
        {"date": "2026-03-12", "weekday": "Thu", "am": "C", "pm": "AT"},
        {"date": "2026-03-13", "weekday": "Fri", "am": "FMIT", "pm": "FMIT"},
        ...
    ]
}
```

### Call Assignment Export

`_fetch_call_assignments()` queries ALL CallAssignment in date range (both FMIT Fri/Sat and solver Sun-Thu). Returns `[{"date": date_obj, "staff": "LASTNAME"}]`. Last name extracted by: `name.split(",")[0]` for "Last, First" format, or `name.split()[-1]` otherwise.

### Block Template 2 Excel Layout

```
Row 4:  Staff Call — faculty last name per night (AM column only)
Row 5:  Resident Call
Rows 9-28:  Residents (20 slots)
Row 29: Resident totals
Row 30: Faculty summary headers
Rows 31-42: Faculty (12 slots)
Row 43: Faculty totals
Row 44: %CVf metric

Columns:
  A (1): Rotation1
  B (2): Rotation2
  C (3): Template code — "C19" for faculty, "R1"/"R2"/"R3" for residents
  D (4): Role — "FAC" for faculty, "PGY 1/2/3" for residents
  E (5): Name — "Last, First" format
  F-BI (6-61): Schedule grid — 28 days × 2 cols (AM=even, PM=odd)
  BJ-BR (62-70): Summary columns
```

### Faculty Summary Formulas (Columns 62-70, Rows 31-42)

```
BJ (62): =SUMPRODUCT(COUNTIF(F{r}:BI{r}, {"C","SM"}))          — Clinic count
BK (63): =COUNTIF(F{r}:BI{r}, "CC")                             — Continuity Clinic
BL (64): =COUNTIF(F{r}:BI{r}, "CV")                             — Cardiovascular
BM (65): =BJ{r}+BK{r}+BL{r}                                    — Total patient care
BN (66): =SUMPRODUCT(COUNTIF(F{r}:BI{r}, {"AT","PCAT","DO"}))   — Teaching/supervision
BO (67): =SUMPRODUCT(COUNTIF(F{r}:BI{r}, {"GME","DFM","DOFM"})) — Administrative
BP (68): =COUNTIF(F{r}:BI{r}, "LV")                             — Leave days
BQ (69): =COUNTIF(F{r}:BI{r}, "FMIT")                           — FMIT half-days
BR (70): =COUNTIF(F4:BI4, "{LASTNAME}")                         — Call count from row 4
```

### Call Row Rendering (_fill_call_row)

```
For each day in block:
    col = 6 + (day_offset * 2)     # AM column only
    cell(row=4, column=col) = call_lookup.get(date, "")   # Faculty last name
```

### Call Count Formula (BR column)

The CALL column uses `=COUNTIF(F4:BI4, "LASTNAME")` where LASTNAME is extracted from the faculty member's name in column E using `_call_last_name_token()`:
- "Last, First" → "LAST"
- "First Last" → "LAST"
- Stars removed, uppercased

---

## Known Issues Found

### 1. CallAssignment ORM CHECK Mismatch
- **DB migration** allows: `('overnight', 'weekend', 'backup')`
- **ORM model** declares: `('sunday', 'weekday', 'holiday', 'backup')`
- **Code writes:** `'overnight'` (30+ references)
- **Impact:** No runtime bug (PG uses migration CHECK), but ORM is stale

### 2. Call Equity is Per-Block Only
- `SchedulingContext` has NO `prior_call_counts` field
- All equity constraints count from 0 each block
- Faculty A with 4 Sunday calls in Block 9 gets no relief in Block 10
- `people.sunday_call_count` / `weekday_call_count` columns exist but are NOT fed to the solver

### 3. Three Constraints Missing from Registration
- `DeptChiefWednesdayPreferenceConstraint` — simply missing from `create_default()`
- `FMITContinuityTurfConstraint` — not registered (crisis mode only, acceptable)
- `FMITStaffingFloorConstraint` — not registered (crisis mode only, acceptable)

### 4. Key Constraints Disabled by Default
- `FMITWeekBlockingConstraint`, `FMITMandatoryCallConstraint`, `OvernightCallGenerationConstraint` — registered but disabled. Must be explicitly enabled when scheduling faculty.

### 5. Faculty Row Limit
- Template has 12 faculty rows (31-42). No overflow handling if roster > 12 active faculty.

### 6. Cross-Block Boundaries
- FMIT spanning blocks: Preload service handles correctly (date-range overlap query)
- Post-FMIT recovery Friday: May fall in next block (handled by preload, shown on next block's sheet)
- Thursday call → Friday PCAT/DO: Preload creates in next block correctly, but Excel shows on next block's sheet only

---

## Roadmap (Approved)

All 6 known issues have been analyzed and a 3-phase fix roadmap exists at `docs/architecture/FACULTY_FIX_ROADMAP.md`. Summary:

### Phase 1: Longitudinal Call Equity (Gap #2 — solver amnesia)
- Add `prior_calls: dict[UUID, dict[str, int]]` to `SchedulingContext`
- Hydrate YTD from `call_assignments` table dynamically (not stale `people.*_count` columns)
- Inject history constants into CP-SAT: `model.Add(history + sum(current_block_vars) <= max_global)`
- Shifts objective from local-max to global-YTD-max

### Phase 2: Code Gap Fixes (Gaps #1, #3, #4)
- **2A:** Align ORM CHECK to match migration: `('overnight', 'weekend', 'backup')`
- **2B:** Register `DeptChiefWednesdayPreferenceConstraint` in `create_default()` (disabled by default)
- **2C:** Add `profile` parameter to `create_default(profile="faculty")` — auto-enables FMIT + call constraints

### Phase 3: Annual Workbook — 15-Sheet YTD_SUMMARY (Gaps #5, #6)
- Expand template to 50 pre-formatted faculty rows (31–80), hide unused (no `insert_rows`)
- Add `YTD_SUMMARY` sheet with SUMIF formulas across 14 block sheets
- Cross-block FMIT resolved natively: `= SUM(all_block_FMIT_half_days) / 14` = exact FMIT weeks
- SUMIF (not 3D refs) survives coordinator sorting

**Execution order:** Phase 2 → 1 → 3 (low-risk fixes, then solver changes, then additive features)

---

That's the actual system — 56 people, 17K+ half-day assignments, 62 inpatient preloads, OR-Tools CP-SAT solving one block at a time, 18 faculty-specific constraints (3 disabled, 3 unregistered), Excel rendering to a fixed 12-faculty-row template. Roadmap addresses all gaps. No embellishment.
