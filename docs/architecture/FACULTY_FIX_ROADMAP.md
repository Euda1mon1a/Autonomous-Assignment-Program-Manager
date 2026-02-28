# Faculty Scheduling Fix Roadmap

> **Status:** Phase 1 COMPLETED, Phases 2-3 planned
> **Created:** 2026-02-25
> **Updated:** 2026-02-26 — Phase 1 completed (PRs #1199, #1201, #1202)
> **Depends on:** Gemini WP-2/3/4/8/9 completion (Phases 2-3)
> **Prereqs:** `FACULTY_SCHEDULING_SPECIFICATION.md`, `annual-workbook-architecture.md`, `excel-stateful-roundtrip-roadmap.md`
>
> **Audit Confirmation (Feb 26, 2026):** Full-codebase Perplexity Computer audit (session #8, 39MB upload) independently confirmed Gap #1 as the highest-priority scheduling bug. Finding 4.2: `build_scheduling_context()` never populates `prior_calls` — the constraint code correctly reads via `getattr(context, "prior_calls", {})` but always receives an empty dict. YTD call equity is silently a no-op. See `docs/perplexity-uploads/started/full-codebase/RESULTS.md` for full findings. Implementation status for Gemini-authored code: see `docs/architecture/gemini-implementation-review.md`.
>
> **Phase 1 Completion (Feb 26, 2026):** All 5 steps implemented and merged via Mac Mini overnight sprint + Codex/Gemini fix passes. MAD replaces Min-Max. `prior_calls` hydrated from `call_assignments` via GROUP BY. FMIT weekend calls correctly split from weekday equity via `is_weekend` CASE expression. 9 unit tests passing.

---

## Background

A comprehensive audit of the faculty scheduling pipeline (DB models → preloads → constraints → solver → JSON → Excel) identified 6 gaps. An expert architectural review provided solutions for all 6. This roadmap documents the fix plan across 3 phases.

The existing pipeline correctly separates `_load_fmit_call` (Friday/Saturday mandatory) from `_load_faculty_call` (cascading post-call), which is the right decoupling for three conflicting paradigms: **ACGME supervision** (hard rules), **inpatient service weeks** (rolling 7-day cadences), and **human equity** (soft rules). The fixes below preserve this architecture.

### Gaps Identified

| # | Gap | Severity | Phase |
|---|-----|----------|-------|
| 1 | ~~Solver amnesia — call equity resets to 0 each block~~ | ~~High~~ | ~~1~~ DONE |
| 2 | ORM CHECK constraint stale vs DB migration | Low | 2 |
| 3 | `DeptChiefWednesdayPreference` implemented but not registered | Medium | 2 |
| 4 | FMIT/call constraints disabled by default, no `profile` mechanism | Medium | 2 |
| 5 | 12 faculty rows — roster may exceed template limit | Medium | 3 |
| 6 | Cross-block FMIT invisible on per-block Excel sheets | High | 3 |

---

## Phase 1: Longitudinal Call Equity (Fixes Gap #1) — COMPLETED

> **Completed:** 2026-02-26
> **PRs:** #1199 (MAD + prior_calls + sync), #1201 (max default=0 safety), #1202 (FMIT weekend split)
> **Tests:** 9/9 passing in `backend/tests/test_call_equity_ytd.py`

### Problem

Equity constraints (`SundayCallEquity` w=10, `WeekdayCallEquity` w=5, `HolidayCallEquity` w=7) start from 0 every block. `call_counts` in `solvers.py:2088` is a local dict that dies after each run. Faculty who took 4 Sunday calls in Block 9 are treated identically to someone who took 0 in Block 10.

### Solution

> **Gemini 3 Pro Analysis (Feb 26, 2026):** Gemini read engine.py (170KB) end-to-end and identified that `_build_context()` at **line 737-770** has EXISTING prior_calls hydration logic, but it's broken — uses `extract("dow")` and filters on `call_type == "overnight"`, silently dropping all Sunday/Weekend history. Additionally, `call_equity.py` uses a **Min-Max (Chebyshev norm)** formulation that is fundamentally incompatible with the additive MAD history model. Both must be replaced.

Shift objective from minimizing the **local max** (Chebyshev norm) to minimizing **Mean Absolute Deviation (MAD)** via `AddAbsEquality`, with additive gamma=1 history model.

### Step 1A: `prior_calls` Already Exists in SchedulingContext

**File:** `backend/app/scheduling/constraints/base.py` (line 262)

Already defined: `prior_calls: dict[UUID, dict[str, int]] = field(default_factory=dict)`. No change needed.

### Step 1B: Replace Broken Hydration in Engine

**File:** `backend/app/scheduling/engine.py` — replace lines 737-770 in `_build_context()`

The existing code uses `extract("dow")` and `call_type == "overnight"` filter, which silently drops all Sunday/Weekend history. Replace with the `GROUP BY` SQL pattern from annual-leap Section 3:

```python
# Query call_assignments for YTD totals (ay_start through block_start)
stmt = (
    select(CallAssignment.person_id, CallAssignment.call_type, func.count().label("ytd_count"))
    .where(and_(
        CallAssignment.date >= ay_start,
        CallAssignment.date < self.start_date,
        CallAssignment.call_type.in_(["weekend", "overnight", "holiday"])
    ))
    .group_by(CallAssignment.person_id, CallAssignment.call_type)
)
# Map: "weekend" → "sunday", "overnight" → "weekday", "holiday" → "holiday"
```

### Step 1C: Replace Min-Max with MAD in call_equity.py

**File:** `backend/app/scheduling/constraints/call_equity.py` — replace `SundayCallEquityConstraint.add_to_cpsat()` (line 120+) and `WeekdayCallEquityConstraint.add_to_cpsat()` (lines 309-322)

**Why restructuring is required:** The existing Min-Max formulation (`model.Add(history + sum(vars_list) <= max_sunday)`) stops caring about balancing anyone below the max threshold. If one faculty member has YTD total of 15, the solver ignores equity for everyone below 15.

**MAD formulation via `AddAbsEquality`:** Multiply by F (faculty count) to avoid fractional integers in CP-SAT:
```python
# For each faculty: dev = F * (history + current) - total_calls
# abs_dev = |dev|
# Minimize sum of abs_dev * weight
model.AddAbsEquality(abs_dev, dev)  # (target, source)
objective_vars.append((abs_dev, int(self.weight)))
```

### Step 1D: Post-Solve Write-Back to PersonAcademicYear

**File:** `backend/app/scheduling/engine.py` — new method `_sync_academic_year_call_counts()` + call after PCAT/DO integrity checks (line ~440)

**Idempotent design:** Do NOT increment `+1` — recalculate YTD totals from `call_assignments` source of truth each time. Safe against block re-generation, rollbacks, and manual DB edits.

### Step 1E: Tests — COMPLETED

All 9 tests passing in `backend/tests/test_call_equity_ytd.py`:

- **TestSundayCallEquityMAD (3 tests):** MAD creates abs_dev vars, deviation with prior history, empty prior_calls degrades to single-block equity
- **TestWeekdayCallEquityMAD (1 test):** Creates deviation variables for Mon-Thu
- **TestSyncAcademicYearCallCounts (2 tests):** Idempotent sync, handles no-call scenario
- **TestPriorCallsHydration (3 tests):** Call type mapping, accumulation by person, FMIT weekend split (overnight+is_weekend=True maps to sunday, not weekday)

---

## Phase 2: Code Gap Fixes (Fixes Gaps #2–4)

### 2A: ORM CHECK Constraint Mismatch (Gap #2)

**Problem:** ORM model at `call_assignment.py:52-55` declares `call_type IN ('sunday', 'weekday', 'holiday', 'backup')`. DB migration (`001_initial_schema.py:156`) has `IN ('overnight', 'weekend', 'backup')`. Code writes `'overnight'`. No runtime INSERT failure (PG uses migration CHECK), but ORM metadata is stale.

**File:** `backend/app/models/call_assignment.py`

```python
# Before (stale):
CheckConstraint("call_type IN ('sunday', 'weekday', 'holiday', 'backup')", name="check_call_type")

# After (matches migration):
CheckConstraint("call_type IN ('overnight', 'weekend', 'backup')", name="check_call_type")
```

No migration needed — metadata-only alignment.

### 2B: Register DeptChiefWednesdayPreferenceConstraint (Gap #3)

**Problem:** Fully implemented at `call_equity.py:1456-1575` (CP-SAT + PuLP) and already imported in `manager.py:64`, but NOT added in `create_default()`.

**File:** `backend/app/scheduling/constraints/manager.py`

Add to `create_default()` (disabled by default, enabled via profile):

```python
# After the TuesdayCallPreference/CallNightBeforeLeave block (~line 427):
manager.add(DeptChiefWednesdayPreferenceConstraint(weight=1.0))
manager.disable("DeptChiefWednesdayPreference")
```

### 2C: Add `profile` Parameter to `create_default()` (Gap #4)

**Problem:** FMIT constraints (`FMITWeekBlocking`, `FMITMandatoryCall`) and `OvernightCallGeneration` are added but disabled by default (lines 364–388). Callers must manually enable them. No caller currently passes parameters — all 8 call sites use `create_default()` with no args.

**File:** `backend/app/scheduling/constraints/manager.py`

```python
@classmethod
def create_default(cls, profile: str = "resident") -> "ConstraintManager":
    manager = cls()
    # ... existing constraint registration (unchanged) ...

    if profile == "faculty":
        manager.enable("FMITWeekBlocking")
        manager.enable("FMITMandatoryCall")
        manager.enable("OvernightCallGeneration")
        manager.enable("DeptChiefWednesdayPreference")

    return manager
```

**Also update** `ConstraintService.get_manager_for_config()` dispatch map at `constraint_service.py:569`:

```python
config_map = {
    "default": ConstraintManager.create_default,
    "faculty": lambda: ConstraintManager.create_default(profile="faculty"),
    "minimal": ConstraintManager.create_minimal,
    "strict": ConstraintManager.create_strict,
    "resilience": lambda: ConstraintManager.create_resilience_aware(tier=2),
}
```

**Backward compatibility:** Default `"resident"` profile preserves current behavior for all 8 callers:
`engine.py:117`, `solvers.py:135`, `anderson_localization.py:309`, `generator.py:133`, `constraint_service.py:163`, `constraint_service.py:576`

### 2D: DOW Convention Fix — COMPLETED (Feb 27, 2026)

**Problem:** `FacultyWeeklyTemplate.day_of_week` stores Python weekday (0=Mon, 6=Sun) but model docstrings, column comments, schemas, service docstrings, and constraint code all assumed PG DOW (0=Sun, 6=Sat). This caused runtime bugs (constraint off-by-one, frontend weekend misdetection) and wrong documentation across 9+ files.

**All fixes applied:**

| Category | Files Changed | Detail |
|----------|---------------|--------|
| Backend constraint (RUNTIME) | `constraints/faculty_weekly_template.py` | Deleted `_python_weekday_to_pattern()`, fixed 3 call sites |
| Frontend (RUNTIME) | `types/faculty-activity.ts` | `isWeekend()` fixed (was flagging Monday), `DAY_LABELS`/`DAY_LABELS_SHORT` remapped 0→Monday |
| Docstrings (9 files) | schemas, services, constraints, scripts | All corrected to state correct convention |
| Constants | `faculty_weekly_template.py`, `weekly_pattern.py` | `PYTHON_WEEKDAY_*` and `PG_DOW_*` disambiguation constants |
| Tests (29 new) | 3 new test files | `test_faculty_weekly_template_dow.py`, `test_dow_conventions.py`, `faculty-activity-dow.test.ts` |
| Existing tests (38 fixed) | `test_faculty_weekly_template_constraint.py` | Removed deleted-method tests, fixed validate test DOW values |

**Investigated:** `block_assignment_expansion_service.py:713` uses `isoweekday() % 7` (PG DOW). Confirmed self-contained — does NOT interact with faculty templates. Tracked as LOW #42.

**Reference:** `docs/architecture/DOW_CONVENTION_BUG.md` (marked FIXED with full file list and test commands).

### Phase 2 Tests

- `create_default(profile="faculty")` returns manager with FMIT + call constraints enabled
- `create_default()` (no args) keeps existing disabled state — zero behavioral change
- ORM CHECK values match migration CHECK values
- `FacultyWeeklyTemplate.__repr__()` shows correct day name for DOW=4 → "Fri" (not "Thu")
- `FacultyWeeklyTemplate.is_weekend` returns True for DOW=5,6 (Sat, Sun), False for DOW=0 (Mon)

---

## Phase 3: Annual Workbook — 15-Sheet Design with YTD_SUMMARY (Fixes Gaps #5–6)

### Problem

Per-block Excel sheets cannot display cross-block FMIT weeks or longitudinal equity. A Block 10 sheet showing 5 FMIT half-days from a week that started in Block 9 looks inequitable without the full picture. The template also caps at 12 faculty rows.

### Solution

15-sheet annual workbook: Sheet 0 = `YTD_SUMMARY`, Sheets 1–14 = Blocks 0–13. Expand template to 50 pre-formatted rows with unused rows hidden.

### Existing Foundation (Already Implemented)

| Component | Status | Location |
|-----------|--------|----------|
| `export_year_xlsx()` | Done | `canonical_schedule_export_service.py:88-159` |
| API route | Done | `export.py:268` — GET `/schedule/year/xlsx` |
| `_copy_worksheet()` | Done | `canonical_schedule_export_service.py:161-196` |
| Phantom columns (stub blocks) | Done | `canonical_schedule_export_service.py:198-217` |
| `__SYS_META__` + `__REF__` | Done | WP-1 metadata (committed `d70a1444`) |
| Parent/child batch import | Done | `import_staging.py:112-157`, `import_tasks.py` |
| Longitudinal validator | Done | `longitudinal_validator.py` (NF caps + clinic mins) |
| Architecture doc | Done | `annual-workbook-architecture.md` (354 lines) |
| Template file | **Missing** | `backend/data/BlockTemplate2_Official.xlsx` not on disk |

### 3A: Expand Template to 50 Pre-Formatted Faculty Rows (Gap #5)

**Problem:** Current template has 12 faculty rows (31–42). Roster may exceed 12 active faculty.

**Approach:** Expand master template to 50 faculty rows (31–80). During export, **hide** unused rows. Do NOT use `openpyxl.insert_rows()` — it corrupts merged cells and `SUMPRODUCT` formulas.

```python
active_count = len(data["faculty"])
last_populated = 30 + active_count
for row_idx in range(last_populated + 1, 81):
    ws.row_dimensions[row_idx].hidden = True
```

Summary formulas move to Row 81 (was 43). `%CVf` moves to Row 82 (was 44).

**Files to update:**
- `backend/data/BlockTemplate2_Official.xlsx` — expand or create with 50 faculty rows
- `backend/app/services/xml_to_xlsx_converter.py`:
  - Faculty row range: 31→80 (was 31→42)
  - Totals row: 81 (was 43)
  - `%CVf` row: 82 (was 44)
  - Summary column formula ranges: `BJ31:BJ80` etc.
  - `_fill_call_row()`: update CALL formula range

### 3B: Add YTD_SUMMARY Sheet (Gap #6)

> **Audit Warning (Finding 4.5):** The column numbers referenced below (cols 62–70) are positional offsets into BlockTemplate2_Official.xlsx. Any change to the block sheet layout (inserting/removing columns, reordering) silently breaks all SUMIF formulas. The audit recommends either computing column positions dynamically at runtime or using Excel named ranges instead of positional references.

New sheet injected as Sheet 0 of the annual workbook. Lists all faculty with live formulas aggregating data across 14 block sheets.

**Why SUMIF, not 3D references:** Coordinators may sort faculty alphabetically on individual block sheets. SUMIF matches by name (Column E) so the math survives sorting.

**Cross-block FMIT formula (the key insight):**

```excel
=(
  SUMIF('Block 0'!$E$31:$E$80, $A2, 'Block 0'!BQ$31:BQ$80) +
  SUMIF('Block 1'!$E$31:$E$80, $A2, 'Block 1'!BQ$31:BQ$80) +
  ... [through Block 13]
) / 14
```

**Why `/14`:** 1 FMIT week = exactly 14 half-days. Faculty C works Apr 4–10 spanning Blocks 10+11: Block 10 counts 10 half-days, Block 11 counts 4. Sum = 14, ÷ 14 = `1.0 FMIT Weeks`. Zero Python cross-block logic — Excel does it natively and reactively as coordinators edit grids.

**YTD_SUMMARY columns:**

| Col | Header | Formula Pattern |
|-----|--------|----------------|
| A | Faculty Name | Static (from roster) |
| B | YTD Clinic (C+SM) | SUMIF across 14 blocks, col 62 |
| C | YTD CC | SUMIF across 14 blocks, col 63 |
| D | YTD CV | SUMIF across 14 blocks, col 64 |
| E | YTD Total Clinic | =B+C+D |
| F | YTD AT (AT+PCAT+DO) | SUMIF across 14 blocks, col 66 |
| G | YTD Admin | SUMIF across 14 blocks, col 67 |
| H | YTD Leave | SUMIF across 14 blocks, col 68 |
| I | YTD FMIT Weeks | SUMIF col 69 / 14 |
| J | YTD Call Nights | SUMIF across 14 blocks, col 70 |

**File:** `backend/app/services/canonical_schedule_export_service.py` — add `_build_ytd_summary_sheet()`, call from `export_year_xlsx()`.

### 3C: Template Creation

`backend/data/` directory and `BlockTemplate2_Official.xlsx` do not exist on disk. Structure is defined in `docs/scheduling/BlockTemplate2_Structure.xml`.

Options:
1. Generate template programmatically from the XML structure file
2. Create manually in Excel with 50 faculty rows pre-formatted
3. Both: generate baseline, manually polish formatting

### Phase 3 Tests

- `_build_ytd_summary_sheet()` generates correct SUMIF formulas
- Row hiding works for 5, 12, 30, 50 active faculty
- Export 3-block year workbook, verify YTD FMIT formula resolves correctly
- Single-block export regression — unchanged behavior

---

## Dependency Graph

```
Phase 2A (ORM fix) ─────────── standalone
Phase 2B (register constraint) ─ standalone
Phase 2C (profile param) ─────── depends on 2B
Phase 2D (tests) ─────────────── depends on 2A-C

Phase 1A (prior_calls field) ── standalone
Phase 1B (hydrate YTD) ──────── depends on 1A
Phase 1C (CP-SAT injection) ─── depends on 1A, 1B
Phase 1D (tests) ─────────────── depends on 1A-C

Phase 3A (50 rows) ───────────── standalone (template)
Phase 3B (YTD_SUMMARY) ──────── depends on 3A (row numbers)
Phase 3C (template creation) ── parallel with 3A
Phase 3D (tests) ─────────────── depends on 3A-C
```

**Recommended order:** Phase 2 → Phase 1 → Phase 3

Phase 2 is pure fix work (small, low-risk). Phase 1 changes solver behavior (medium risk, needs careful testing). Phase 3 is additive feature work (template + new sheet).

---

## Critical Files

| File | Phase | Change |
|------|-------|--------|
| `backend/app/scheduling/constraints/base.py` | 1A | Add `prior_calls` field to SchedulingContext |
| `backend/app/scheduling/engine.py` | 1B | Hydrate YTD query + inject into context |
| `backend/app/scheduling/constraints/call_equity.py` | 1C | Modify CP-SAT objective expressions |
| `backend/app/models/call_assignment.py` | 2A | Fix CHECK constraint values |
| `backend/app/scheduling/constraints/manager.py` | 2B, 2C | Register constraint + add `profile` param |
| `backend/app/services/constraint_service.py` | 2C | Update dispatch map |
| `backend/app/services/xml_to_xlsx_converter.py` | 3A | Update row refs for 50-row layout |
| `backend/app/services/canonical_schedule_export_service.py` | 3B | Add `_build_ytd_summary_sheet()` |
| `backend/data/BlockTemplate2_Official.xlsx` | 3C | Create template |

---

## Verification

```bash
# Phase 2 — Code gap fixes
cd backend
.venv/bin/python -m pytest tests/scheduling/ -x -q -k "constraint_manager or call_assignment"
.venv/bin/python -c "from app.models.call_assignment import CallAssignment; print(CallAssignment.__table_args__)"

# Phase 1 — Longitudinal equity
.venv/bin/python -m pytest tests/scheduling/ -x -q -k "call_equity or prior_calls"

# Phase 3 — Annual workbook
.venv/bin/python -m pytest tests/services/test_canonical_schedule_export.py -x -q
.venv/bin/python -m pytest tests/services/ -x -q -k "ytd_summary or annual"

# Full regression
.venv/bin/python -m pytest tests/ -x -q --ignore=tests/scheduling/test_fair_call_optimizer.py
```

> **Note:** `test_fair_call_optimizer.py` has a pre-existing ortools `CpSolverStatus` attribute error — ignore until ortools version is updated.
