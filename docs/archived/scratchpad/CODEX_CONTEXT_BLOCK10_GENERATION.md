# Block 10 Schedule Generation: Business Logic & Intent

> **Purpose:** Provide Codex IDE with deep context for identifying gaps in schedule generation code.
> **Last Updated:** 2026-01-21

---

## Executive Summary

Block 10 schedule generation transforms high-level rotation assignments ("Resident X on FMIT") into detailed half-day assignments ("Resident X works FMIT AM on March 15"). This is a **military medical residency** scheduler for TAMC Family Medicine with strict ACGME compliance requirements.

### Key Constraint: 56-Assignment Rule

Every person (resident or faculty) must have **exactly 56 half-day assignments per block** (28 days × 2 slots). This makes gap detection trivial:
- 56 assignments = complete schedule
- <56 assignments = gap detected (bug)

---

## Pipeline Overview (CORRECTED Order of Operations)

> **CRITICAL:** The dependency chain is: Call → PCAT/DO → AT Coverage → Resident Clinic → Faculty Admin
>
> PCAT (Post-Call Attending Time) counts toward AT (supervision) coverage.
> Residents MUST know PCAT availability BEFORE scheduling clinic slots.
> Faculty admin time fills AFTER knowing resident clinic demand.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: NON-CALL PRELOADS (Locked slots - NEVER overwritten by solver)    │
│  Source: SyncPreloadService (with skip_faculty_call=True)                    │
│  Priority: HIGHEST (source='preload')                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Absences (LV-AM, LV-PM) - vacation, sick, conference                     │
│  2. Inpatient rotations (FMIT, NF, PedW, KAP, IM, LDNF)                      │
│  3. FMIT Fri/Sat call - auto-assigned during FMIT week                       │
│  4. C-I (inpatient clinic): PGY-1 Wed AM, PGY-2 Tue PM, PGY-3 Mon PM        │
│  5. Resident call preloads                                                   │
│  6. aSM (Sports Med Wed AM for SM faculty)                                   │
│  7. Conferences (HAFP, USAFP, LEC) [stubbed]                                 │
│  8. Protected time (SIM, PI, MM) [stubbed]                                   │
│  ⚠️ Faculty call PCAT/DO SKIPPED - comes from NEW call in Phase 3            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: RESIDENT EXPANSION                                                 │
│  Source: BlockAssignmentExpansionService                                     │
│  Priority: MEDIUM (source='solver')                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Expands BlockAssignment → HalfDayAssignment                                 │
│  Input:  "Resident X on FMC for Block 10"                                   │
│  Output: 56 half-day records with appropriate activities                     │
│                                                                              │
│  Key Logic:                                                                  │
│  - Mid-block rotation transitions (day 11 = column 28 in Excel)              │
│  - Rotation-specific patterns (KAP, LDNF, IM, PedW, FMIT)                    │
│  - Wednesday PM = LEC for non-exempt rotations                               │
│  - Last Wednesday: AM = LEC, PM = ADV for ALL residents                      │
│  - Intern continuity: PGY-1 Wed AM = C (except exempt rotations)             │
│  - 1-in-7 day-off rule (ACGME) with PAUSE semantics for absences             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: CALL SOLVER (Sun-Thu) + PCAT/DO Generation                         │
│  Source: GreedySolver → _sync_call_pcat_do_to_half_day()                     │
│  Priority: PRELOAD (LOCKED after creation)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  ★ CRITICAL: Call MUST be solved BEFORE activity solver runs ★               │
│                                                                              │
│  Sun-Thu call uses equity algorithm (min-gap decay)                          │
│  FMIT Fri/Sat call comes from preloads (Phase 1)                             │
│                                                                              │
│  IMMEDIATELY after creating CallAssignment records:                          │
│  → Creates PCAT (AM) + DO (PM) for next day (source='preload', LOCKED)       │
│  → NOW we have baseline AT coverage for ratio calculations                   │
│                                                                              │
│  Key rules:                                                                  │
│  - FMIT faculty don't get PCAT/DO (continue coverage)                        │
│  - No back-to-back call (need gap days)                                      │
│  - Sunday tracked separately for equity                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: ACTIVITY SOLVER (Residents Only)                                   │
│  Source: CPSATActivitySolver                                                 │
│  Priority: MEDIUM (source='solver')                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ★ NOW knows PCAT availability from Phase 3 for AT coverage calculations ★   │
│                                                                              │
│  Assigns C/LEC/ADV activities to RESIDENT slots with source='solver/template'│
│                                                                              │
│  CRITICAL: Excludes faculty (Person.type != 'faculty')                       │
│  Faculty slots are managed by FacultyAssignmentExpansionService              │
│                                                                              │
│  Constraints:                                                                │
│  - One activity per slot per person                                          │
│  - Wednesday PM = LEC (weeks 1-3)                                            │
│  - Last Wednesday: AM = LEC, PM = ADV                                        │
│  - Objective: Maximize clinic (C) assignments                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 5: FACULTY EXPANSION                                                  │
│  Source: FacultyAssignmentExpansionService                                   │
│  Priority: LOW (source='template')                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  ★ NOW knows resident clinic demand from Phase 4 ★                           │
│  ★ PCAT/DO from Phase 3 preserved (source='preload' > 'template') ★          │
│                                                                              │
│  Ensures faculty have 56 half-day records with admin time placeholders       │
│                                                                              │
│  Activity Assignment Priority:                                               │
│  1. Deployed (DEP) - tdy, training, military_duty, deployment                │
│  2. Absent (LV-AM/LV-PM) - blocking absences                                 │
│  3. Weekend (W)                                                              │
│  4. Holiday (HOL) - from Block.is_holiday or NON_OPERATIONAL intent          │
│  5. Admin time (gme/dfm/sm_clinic) - based on faculty.admin_type             │
│                                                                              │
│  CRITICAL: SM admin_type maps to 'sm_clinic' activity (not 'sm')             │
│  CRITICAL: Exclude adjuncts (faculty_role='adjunct' OR NULL → included)      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why This Order Matters

**Example: March 16 (Monday after Sunday call)**

```
Faculty A took call Sunday night
→ Monday AM = PCAT (can precept, counts as 1.0 AT coverage)
→ Monday PM = DO (day off)

Resident AT demand Monday AM:
- 2 PGY-1 in clinic = 1.0 AT needed
- 2 PGY-2 in clinic = 0.5 AT needed
- Total = 1.5 AT needed

AT coverage Monday AM:
- Faculty A: PCAT (1.0 AT) ← From call schedule
- Faculty B: C (1.0 AT)
- Total = 2.0 AT available ✓

If call changes AFTER residents scheduled → PCAT disappears →
Only 1.0 AT available but 1.5 needed → ACGME violation!
```

---

## File-by-File Business Logic

### 1. `backend/app/scheduling/engine.py` - Main Orchestrator

**Intent:** Central entry point that coordinates all phases of schedule generation.

**Key Method: `generate()`**
```python
def generate(
    block_number: int,
    academic_year: int,
    algorithm: str = "greedy",
    expand_block_assignments: bool = True,
    create_draft: bool = False,
    ...
) -> dict:
```

**Business Logic (CORRECTED Order - Session 125):**

1. **Create schedule run record** for audit trail
2. **Check pre-generation resilience** (utilization thresholds, N-1 coverage)
3. **Ensure blocks exist** for date range (creates Block records if missing)
4. **Load preserved assignments:**
   - FMIT faculty assignments
   - Resident inpatient assignments
   - Absence assignments
5. **Build availability matrix** from absences
6. **Get residents, faculty, templates**
7. **If `expand_block_assignments=True` and NOT draft mode:**
   - **Step 3.5:** Load NON-CALL preloads (`skip_faculty_call=True`) → FMIT, absences, C-I, NF, aSM
   - **Step 3.6:** Expand resident block assignments → HalfDayAssignment
   - **Step 5:** Run `GreedySolver` (call_assignments only) → Sun-Thu call
   - **Step 6.5:** Create CallAssignment records
   - **Step 6.6:** Generate PCAT/DO (`_sync_call_pcat_do_to_half_day()`) → LOCKED
   - **Step 6.7:** Run `CPSATActivitySolver.solve()` → C/LEC/ADV for residents (NOW knows PCAT)
   - **Step 6.8:** Run `FacultyAssignmentExpansionService` → faculty admin (NOW knows resident demand)
8. **Validate ACGME compliance** (80-hour rule, 1-in-7, supervision ratios)
9. **Check post-generation resilience**
10. **Return results** with assignments, validation, resilience info

**Critical Guard (Session 124 Fix):**
```python
if expand_block_assignments and block_number and academic_year and not create_draft:
    # Run full pipeline
elif create_draft:
    logger.info("Skipping preload sync in draft mode (would modify live data)")
```

**Why this matters:** Draft mode should NOT modify live `half_day_assignments` table - it only previews what would happen.

---

### 2. `backend/app/services/sync_preload_service.py` - Locked Assignments

**Intent:** Create preload assignments that the solver CANNOT overwrite.

**Key Method: `load_all_preloads()`**

**Business Logic (Order Matters!):**

```python
# Order from TAMC skill - do NOT change
total += self._load_absences(start_date, end_date)           # LV-AM, LV-PM
total += self._load_inpatient_preloads(start_date, end_date) # FMIT, NF, PedW...
total += self._load_fmit_call(start_date, end_date)          # Fri/Sat PM
total += self._load_inpatient_clinic(block_number, ...)      # C-I by PGY
total += self._load_resident_call(start_date, end_date)      # Resident call
total += self._load_faculty_call(start_date, end_date)       # CALL → PCAT/DO
total += self._load_sm_preloads(start_date, end_date)        # aSM Wed AM
```

**Why Preloads First:**
- FMIT, call, and absences are NON-NEGOTIABLE
- Solver operates only on unlocked slots
- Preloads have `source='preload'` which is LOCKED

**Special Rotation Patterns:**

| Rotation | Pattern | Notes |
|----------|---------|-------|
| KAP | Mon=KAP/OFF, Tue=OFF/OFF, Wed=C/LEC, Thu-Sun=KAP | Kapiolani L&D (off-site) |
| LDNF | Mon-Thu=OFF/LDNF, Fri=C/OFF, Sat-Sun=W | **Friday** clinic, NOT Wed! |
| FMIT | All=FMIT except C-I clinic slots | Works weekends |
| NF | AM=OFF, PM=NF | Night float |

**PCAT/DO Generation (Faculty Call):**
```python
# Next day after call: PCAT AM, DO PM
next_day = call.date + timedelta(days=1)
if not self._is_on_fmit(call.person_id, next_day):
    self._create_preload(person_id, next_day, "AM", pcat_id)
    self._create_preload(person_id, next_day, "PM", do_id)
```

**PCAT = Post-Call Attending Time** (can precept, counts as AT coverage)
**DO = Direct Observation** (auto-assigned PM after call)

---

### 3. `backend/app/services/block_assignment_expansion_service.py` - Resident Slots

**Intent:** Convert BlockAssignment records into HalfDayAssignment records with rotation-appropriate activities.

**Key Method: `expand_block_assignments()`**

**Business Logic:**

1. **Load BlockAssignments** for (block_number, academic_year) with rotation templates
2. **Pre-load blocks, absences** for efficient lookup
3. **For each BlockAssignment:**
   - Get active rotation (handles mid-block transition at day 11)
   - For each of 28 days:
     - Check availability (absence, weekend, holiday, 1-in-7)
     - Apply rotation-specific pattern (KAP, LDNF, IM, PedW, FMIT, NF)
     - Create AM and PM HalfDayAssignment records

**Mid-Block Transition:**
```python
MID_BLOCK_DAY = 11  # Day 11 = start of Week 3 = Excel column 28

def _get_active_rotation(block_assignment, day_index):
    if block_assignment.secondary_rotation_template_id and day_index >= MID_BLOCK_DAY:
        return block_assignment.secondary_rotation_template
    return block_assignment.rotation_template
```

**Example:** Resident with "Peds Ward → Peds NF" - uses PedW for days 0-10, PedNF for days 11-27.

**1-in-7 Rule (ACGME - CRITICAL):**

The 1-in-7 rule requires one day off every 7 consecutive work days.

**PAUSE Semantics for Absences:**
```python
# Absence: Counter HOLDS (doesn't reset)
# Scheduled off: Counter RESETS to 0
if not is_absent and not skip_holiday:
    consecutive_days = 0  # RESET
# Absence: counter HOLDS (no reset) - correct ACGME interpretation
```

**Why PAUSE (not RESET on absence):**
- Leave is SEPARATE from ACGME-required rest days
- Schedule must be compliant INDEPENDENT of leave status
- Prevents gaming: can't work 6→leave→work 6→leave→work 6...

**Last Wednesday Rule:**
```python
def _is_last_wednesday_of_block(current_date, end_date):
    if not self._is_wednesday(current_date):
        return False
    next_wed = current_date + timedelta(days=7)
    return next_wed > end_date  # No more Wednesdays in block
```

**Last Wednesday assignments:**
- AM = LEC (for ALL residents, including exempt rotations)
- PM = ADV (advising, for ALL residents)

**Common Error:** Scheduling morning clinic on last Wednesday. WRONG.

---

### 4. `backend/app/services/faculty_assignment_expansion_service.py` - Faculty Admin Time

**Intent:** Ensure faculty have 56 half-day assignments with appropriate admin time placeholders.

**Key Method: `fill_faculty_assignments()`**

**Business Logic:**

1. **Load active faculty** (excluding adjuncts if `exclude_adjuncts=True`)
2. **Pre-load activities, absences, existing assignments, holidays**
3. **For each faculty, for each of 56 slots:**
   - If existing assignment → SKIP (respect source priority)
   - If deployed → DEP activity
   - If absent → LV-AM/LV-PM
   - If weekend → W
   - If holiday → HOL
   - Else → admin time (gme/dfm/sm_clinic based on admin_type)

**Session 124 Fixes:**

**NULL faculty_role Fix:**
```python
# SQLAlchemy's != returns False for NULL comparisons
# Must explicitly include NULL rows
stmt = stmt.where(
    or_(Person.faculty_role != "adjunct", Person.faculty_role.is_(None))
)
```

**Why:** Most faculty have `faculty_role=NULL` (not adjuncts). The previous code `!= 'adjunct'` excluded them because `NULL != 'adjunct'` returns False in SQL.

**SM admin_type Mapping:**
```python
if admin_type and admin_type.upper() == "SM":
    activity_code = "sm_clinic"  # NOT 'sm'!
else:
    activity_code = admin_type.lower() if admin_type else "gme"
```

**Why:** Activity table has `sm_clinic` code, not `sm`. SM faculty have `admin_type='SM'`.

**Holiday from Block Table:**
```python
def _preload_holidays(self, start_date, end_date):
    stmt = select(Block.date).where(
        Block.date >= start_date,
        Block.date <= end_date,
        # Match holidays OR non-operational days
        (Block.is_holiday == True) |
        (Block.operational_intent == OperationalIntent.NON_OPERATIONAL),
    ).distinct()
```

**Why:** No separate Holiday model. Holidays are marked on Block records.

**Deployment Types:**
```python
deployed_absence_types = {"deployment", "tdy", "training", "military_duty"}
```

**Why:** All of these should use DEP activity, not LV (leave).

---

### 5. `backend/app/scheduling/activity_solver.py` - Resident Activities

**Intent:** Assign C (clinic), LEC (lecture), ADV (advising) activities to resident half-day slots.

**Key Method: `solve()`**

**Business Logic:**

1. **Load unlocked slots** where `source IN ('solver', 'template')` AND `Person.type != 'faculty'`
2. **Load activities** (fm_clinic, lec, advising)
3. **Create CP-SAT model** with decision variables
4. **Add constraints:**
   - One activity per slot per person
   - Wednesday PM (weeks 1-3) = LEC
   - Last Wednesday: AM = LEC, PM = ADV
5. **Objective:** Maximize clinic assignments
6. **Solve and update** HalfDayAssignment records

**Session 124 Fix - Exclude Faculty:**
```python
def _load_unlocked_slots(self, start_date, end_date):
    from app.models.person import Person
    stmt = (
        select(HalfDayAssignment)
        .join(Person, HalfDayAssignment.person_id == Person.id)
        .where(
            HalfDayAssignment.date >= start_date,
            HalfDayAssignment.date <= end_date,
            HalfDayAssignment.source.in_([
                AssignmentSource.SOLVER.value,
                AssignmentSource.TEMPLATE.value,
            ]),
            Person.type != "faculty",  # CRITICAL: Exclude faculty
        )
    )
```

**Why:** Faculty slots are managed by `FacultyAssignmentExpansionService`. If activity solver touches them, it overwrites admin time (gme/dfm) with clinic (C).

---

### 6. `backend/app/scheduling/solvers.py` - Call and Outpatient

**Intent:** Provide optimization solvers for call distribution and outpatient scheduling.

**Key Classes:**
- `GreedySolver` - Fast heuristic for initial assignments
- `CPSATSolver` - Optimal solutions with constraint propagation (legacy rotation-level)
- `PuLPSolver` - Linear programming for large problems

**Call Assignment Output:**
```python
SolverResult.call_assignments: list[tuple[UUID, UUID, str]]
# (person_id, block_id, call_type)
```

**Session 124 Fix - Call in Half-Day Mode:**
```python
# In engine.py
else:
    # Half-day mode: Run greedy solver ONLY for call assignments (Sun-Thu)
    logger.info(
        "Running greedy solver for Sun-Thu call assignments only "
        "(rotation assignments handled by expansion service)"
    )
    solver_result = self._run_solver("greedy", context, timeout_seconds)
    # Clear rotation assignments but preserve call_assignments
    solver_result.assignments = []
```

**Why:** In half-day mode:
- Rotation assignments come from expansion services (handled by Phases 2-4)
- Only Sun-Thu call needs solver (FMIT Fri/Sat comes from preloads)
- Greedy solver outputs BOTH rotation assignments AND call_assignments
- We clear rotation assignments but keep call_assignments

---

## Source Priority System

```
┌──────────────────────────────────────────────────────────────────┐
│  Source        │ Priority │ Locked │ Can Overwrite              │
├──────────────────────────────────────────────────────────────────┤
│  preload       │ 1 (HIGH) │ YES    │ Nothing                    │
│  manual        │ 2        │ YES    │ Nothing                    │
│  solver        │ 3        │ NO     │ template                   │
│  template      │ 4 (LOW)  │ NO     │ (overwritten by all above) │
└──────────────────────────────────────────────────────────────────┘
```

**Enforcement:**
```python
class HalfDayAssignment:
    @property
    def is_locked(self) -> bool:
        return self.source in (
            AssignmentSource.PRELOAD.value,
            AssignmentSource.MANUAL.value,
        )
```

---

## Known Gaps and Potential Issues

### Addressed in Session 124

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Adjunct filter drops NULL faculty_role | SQL NULL comparison | `OR faculty_role IS NULL` |
| Faculty expansion in draft mode | No guard | `and not create_draft` |
| SM admin_type → missing activity | Wrong activity code | Map SM → `sm_clinic` |
| Deployment detection incomplete | Missing types | Include tdy/training/military_duty |
| Holiday handling missing model | Assumed Holiday table | Derive from Block.is_holiday |
| Activity solver overwrites faculty | No person type filter | `Person.type != 'faculty'` |
| Call assignments empty | Assumed all from preload | Run greedy for Sun-Thu |

### Addressed in Session 125 (Codex Round 4 + Order Fix)

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Draft mode mutates live CallAssignment | No guard on `_create_call_assignments_from_result` | Added `if not create_draft` guard |
| Call preload/solver sequence divergence | Preloads run before solver; PCAT/DO based on OLD call | Added `_sync_call_pcat_do_to_half_day()` after step 6.5 |
| Holiday detection per-date not per-slot | Query used `Block.date` only | Changed to `(date, time_of_day)` tuples |
| **CRITICAL: Wrong order of operations** | Activity solver ran before PCAT/DO created; faculty expansion ran before knowing resident demand | **Restructured entire pipeline** (see below) |

**Detailed Fixes:**

1. **Draft Mode CallAssignment Guard (engine.py:489)**
   ```python
   if not create_draft:
       call_assignments = self._create_call_assignments_from_result(...)
       if call_assignments and expand_block_assignments:
           self._sync_call_pcat_do_to_half_day(call_assignments)
   ```

2. **PCAT/DO Sync After Call Generation (engine.py:497)**
   - `_sync_call_pcat_do_to_half_day()` runs AFTER solver creates CallAssignment records
   - Creates PCAT (AM) and DO (PM) in half_day_assignments for next day
   - Skips if person is on FMIT (they don't get PCAT/DO)
   - Uses `source='preload'` to LOCK slots

3. **Per-Slot Holiday Detection (faculty_assignment_expansion_service.py)**
   - Changed `_holiday_dates: set[date]` → `_holiday_slots: set[tuple[date, str]]`
   - Query now includes `Block.time_of_day`
   - Each slot checked independently: `(current_date, "AM") in self._holiday_slots`

4. **CRITICAL: Restructured Order of Operations (engine.py)**

   **Old (WRONG) Order:**
   ```
   1. Expand resident block assignments
   2. Load preloads (PCAT/DO from OLD call - STALE!)
   3. Fill faculty half-days (before knowing resident demand)
   4. Activity solver (doesn't know PCAT coverage)
   5. Call solver → NEW CallAssignment
   6. Sync PCAT/DO (TOO LATE - residents already scheduled)
   ```

   **New (CORRECT) Order:**
   ```
   1. Load NON-CALL preloads (skip_faculty_call=True)
   2. Expand resident block assignments
   3. Call solver → NEW CallAssignment
   4. Create PCAT/DO immediately (LOCKED as preload)
   5. Activity solver (NOW knows PCAT for AT coverage)
   6. Fill faculty half-days (NOW knows resident demand)
   ```

5. **SyncPreloadService.load_all_preloads() - New Parameter**
   ```python
   def load_all_preloads(
       self,
       block_number: int,
       academic_year: int,
       skip_faculty_call: bool = False,  # NEW - skip stale PCAT/DO
   ) -> int:
   ```

   When `skip_faculty_call=True`, skips loading PCAT/DO from existing CallAssignment records.
   Engine creates fresh PCAT/DO from NEW call in Step 6.6.

### Potential Remaining Gaps

1. **Partial-day absences** - Current code treats all absences as full-day
2. **Conference preloads** - Stubbed out in sync service
3. **Protected time preloads** - Stubbed out (SIM, PI, MM)
4. **FMIT post-call Friday** - PC (day off) enforcement
5. **Call back-to-back prevention** - No constraint in greedy solver
6. **Sunday call equity tracking** - Separate count not implemented
7. **No tests for half-day call generation path** - Regressions not caught by CI

---

## Testing and Verification

### Block 10 Generation Command
```bash
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Content-Type: application/json" \
  -d '{"block_number": 10, "academic_year": 2025, "expand_block_assignments": true}'
```

### Faculty Assignment Check
```sql
SELECT p.name, a.code, COUNT(*)
FROM half_day_assignments hda
JOIN people p ON hda.person_id = p.id
JOIN activities a ON hda.activity_id = a.id
WHERE p.type = 'faculty'
GROUP BY p.name, a.code
ORDER BY p.name, a.code;
```

### Call Assignment Check
```sql
SELECT p.name, ca.date, ca.call_type
FROM call_assignments ca
JOIN people p ON ca.faculty_id = p.id
WHERE ca.date >= '2026-03-12' AND ca.date <= '2026-04-08'
ORDER BY ca.date;
```

### 56-Assignment Rule Validation
```sql
SELECT person_id, COUNT(*) as slot_count
FROM half_day_assignments
WHERE date >= '2026-03-12' AND date <= '2026-04-08'
GROUP BY person_id
HAVING COUNT(*) != 56;
-- Should return 0 rows for complete schedules
```

---

## References

- `docs/scratchpad/session-124-codex-fixes.md` - This session's fixes
- `.claude/skills/tamc-excel-scheduling/skill.md` - TAMC scheduling rules
- `docs/architecture/HALF_DAY_ASSIGNMENT_MODEL.md` - Data model
- `CLAUDE.md` - Project guidelines

---

*Created for Codex IDE context - Session 124*
