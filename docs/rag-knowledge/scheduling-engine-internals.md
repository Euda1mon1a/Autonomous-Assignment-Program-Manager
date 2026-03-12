# Scheduling Engine Internals

> **doc_type:** scheduling_policy
> **Last verified:** 2026-03-09 against codebase
> **Purpose:** Arcane scheduling patterns that are non-obvious and must be understood before modifying engine code

---

## 1. NF Combined Half-Block Rotations

NF (Night Float) combined rotations split a 28-day block into two 14-day phases with a recovery day between them. **Preloaded slots bypass the solver entirely.**

### Block Calendar

- Blocks always start **Thursday** and end **Wednesday** (28 days, enforced by `academic_blocks.py`)
- `mid_block_date = block_start + timedelta(days=14)` = day 15 = always Thursday

### Phase Structure

| Days | Calendar | Activity |
|------|----------|----------|
| 1–14 | Thu–Wed | Phase 1 rotation |
| 15 | Thu | Recovery (AM + PM = "recovery") |
| 16–28 | Fri–Wed | Phase 2 rotation |

### Transition Mechanics

- Resident A's last NF shift is **Wednesday** (day 14)
- Resident A is **post-call (PC)** on Thursday (day 15 = recovery day)
- Resident B starts the next block on Thursday and is also PC on that first Thursday

### Two Rotation Directions

**NF-first** (`NF_COMBINED_ACTIVITY_MAP` in `constants.py`):
- Phase 1: OFF/NF (sleep AM, work PM)
- Phase 2: Specialty full day (e.g., CARDIO, DERM)
- Codes: `NF-CARDIO`, `NF-FMIT-PG`, `NF-DERM-PG`

**Specialty-first / Mirror** (`REVERSE_NF_COMBINED_MAP`):
- Phase 1: Specialty full day
- Phase 2: OFF/NF
- Codes: `CARDS-NF`, `DERM-NF`

### Aliases (Prevent `+` Split Bug)

`ROTATION_ALIASES` in `constants.py`:
- `D+N` → `DERM-NF`
- `C+N` → `CARDS-NF`

Without aliases, `_resolve_rotation_code_for_date` would split on `+` and misinterpret the code.

### Two Mid-Block Calculations (NOT Conflicting)

| File | Calculation | Day | Purpose |
|------|-------------|-----|---------|
| `rotation_codes.py:218` | `start + timedelta(days=14)` | Day 15 (Thu) | Phase split within rotation (NF ↔ specialty) |
| `sync_preload_service.py:443` | `start + timedelta(days=11)` | Day 12 (Mon) | Secondary template switching (administrative) |

These serve different purposes and are intentionally different values.

### Key Files

- `backend/app/services/preload/constants.py:114-130` — activity maps
- `backend/app/services/preload/rotation_codes.py:216-262` — phase logic
- `backend/app/utils/academic_blocks.py` — block calendar (THURSDAY=3)

---

## 2. DOW (Day of Week) Convention

### Primary Convention: Python Weekday

`faculty_weekly_templates.day_of_week` uses **Python weekday** (0=Mon, 6=Sun).

Evidence: DOW=4 rows contain Friday activities, DOW=5/6 contain "W" (weekend).

The engine template lookup (`engine.py:4199`) uses `date.weekday()` — correct.

### Known Fragility: block_assignment_expansion_service.py

`block_assignment_expansion_service.py:713` uses `isoweekday() % 7` which produces **PG DOW** (0=Sun, 6=Sat).

This is **intentionally correct** because `_get_weekly_patterns()` (lines 1168-1170) builds its pattern dict with PG DOW keys:
```python
days_to_include = range(0, 7)  # 0=Sun, 1=Mon, ..., 6=Sat (PG DOW)
```

**Why it's fragile:**
- Only file in the codebase using PG DOW convention
- No comment explaining the intent
- 4 other `isoweekday()` calls in the same file use it differently
- Refactoring to `weekday()` would silently break lookups

**Not a runtime bug**, but a documentation/fragility issue. Future cleanup should add a `_to_pg_dow()` helper.

### Summary

| Context | Convention | Formula |
|---------|-----------|---------|
| `faculty_weekly_templates` | Python weekday | `date.weekday()` (0=Mon) |
| `engine.py` template lookup | Python weekday | `slot_date.weekday()` |
| `block_assignment_expansion_service.py` | PG DOW | `date.isoweekday() % 7` (0=Sun) |

---

## 3. Call Equity (MAD via CP-SAT)

### Mean Absolute Deviation Formulation

Call equity uses **MAD (Mean Absolute Deviation)** instead of Min-Max, implemented via CP-SAT's `AddAbsEquality`.

From `call_equity.py:167-171`:
```
dev = F * (history + current) - total_history - sum(all_vars)
abs_dev = model.AddAbsEquality(target, dev)
```

**F-multiplication** keeps values in integer domain (CP-SAT requires integers).

### FMIT Saturday → Sunday Equity

FMIT overnight calls on Friday/Saturday are reclassified as **"weekend" equity** (Sunday bucket), not "overnight" (weekday).

From `engine.py:1892-1901`:
```python
effective_type = case(
    (and_(call_type == "overnight", is_weekend == True), "weekend"),
    else_=call_type,
)
```

### Post-Solve Write-Back

Write-back is **idempotent recalculation** from `call_assignments` source of truth. Never increments (+1). Safe against block re-generation and rollbacks.

### Key Files

- `backend/app/scheduling/constraints/call_equity.py:125-171`
- `backend/app/scheduling/engine.py:1883-1914`

---

## 4. FMIT Pair Filtering (Date-Scoped)

### Date-Scoped, Not Person-Scoped

FMIT call pair filtering checks each `(person_id, call_date)` against absence intervals for that person. A short absence only removes FMIT pairs on dates it actually covers — not all pairs for that faculty.

From `engine.py:1617-1625`:
```python
fmit_call_pairs = {
    (pid, d) for pid, d in fmit_call_pairs
    if not any(abs_start <= d <= abs_end
               for abs_start, abs_end in person_absences.get(pid, []))
}
```

### Two-Level Eligibility

| Level | Scope | Mechanism |
|-------|-------|-----------|
| **Call eligibility** | Full block | Solver creates BoolVars for all call-eligible faculty on all Sun-Thu nights |
| **Per-night exclusion** | Individual night | `OvernightCallGenerationConstraint` blocks ineligible slots (FMIT/absence) |

### Key Files

- `backend/app/scheduling/engine.py:1593-1632`
- `backend/app/scheduling/constraints/overnight_call.py:215-266`

---

## 5. Faculty Gap Backfill

### The Problem

The solver can leave all 4 binary activity variables = 0 for a faculty half-day slot when constraint interactions prevent any valid assignment. These gaps appear as NULL activity codes.

### The Solution

`_backfill_faculty_gaps()` (`engine.py:3530-3542`) fills empty slots:
- **Weekday gaps** → OFF (day off)
- **Weekend gaps** → W (weekend)

Uses `is_weekend` flag on the block to choose.

### Key File

- `backend/app/scheduling/engine.py:3483-3560`

---

## 6. Stale CALL Preload Detection

### Why CALL HDAs Shouldn't Exist

Faculty CALL assignments are tracked in the `call_assignments` table, not `half_day_assignments` (HDAs). Faculty work normal AM/PM activities and go on call overnight. Call info appears in row 4 of the export.

### Cleanup Logic

`engine.py:1848-1870` removes ALL faculty CALL HDAs in the current block range (`start_date` to `end_date`). Stale CALL HDAs may remain from older code paths or previous generations where call dates moved.

**Important nuance:** This method only *removes* stale CALL HDAs. It does NOT directly write PCAT/DO replacements. PCAT/DO come from the preload sync step (`sync_preload_service.py`) as a separate operation.

### Key File

- `backend/app/scheduling/engine.py:1815-1878`
