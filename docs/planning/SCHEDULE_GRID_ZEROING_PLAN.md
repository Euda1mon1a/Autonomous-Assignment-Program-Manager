# Schedule Grid Zeroing Plan

**Created:** 2026-02-27
**Purpose:** Row-by-row, column-by-column validation of Block 12 schedule data via `schedule_grid` SQL view.
**Philosophy:** "Zero the rifle" — align DB with Excel reality before any constraint tuning or solver refinement.

---

## Current State

### Infrastructure (DONE)
- `schedule_grid` SQL view created in PG17 (also Alembic migration at `20260227_schedule_grid_view.py`)
- View pivots `half_day_assignments` into `person × date` with AM/PM columns
- Block 12 dates: **2026-05-07 (Thu) → 2026-06-03 (Wed)** = 28 days = 56 half-day slots
- Pivoted Excel export: `/tmp/Block12_Schedule_Grid_Zeroing.xlsx` (3 sheets: Raw Codes, Numeric Codes, Legend)

### Block 12 Data (DONE)
- 16 residents × 56 HDAs each ✓
- 10 core faculty × 56 HDAs each ✓ (reduced from 14 → removed 4 non-core faculty)
- Adjuncts deferred until core functionality locked in

### Data Fixes Applied
1. **Orphaned activity UUID** — FIXED. 5 `faculty_weekly_templates` rows updated from `9fd0dca9-...` → correct FMIT UUID `bd9c66b3-...`
2. **Personnel cleanup** — Removed 4 non-core faculty (1 with 0 templates, 3 near all-GME)

### Known Quality Issues (Solver-Side)
1. **Faculty solver ignores templates** — `FacultyWeeklyTemplateConstraint` not registered in `manager.py`. Cross-category mismatches remain (~100 slots where solver chose C but template wants AT, or vice versa). Within-category specificity now handled by template-aware write-back.
2. ~~**Faculty work Sat/Sun**~~ — **FIXED.** Root cause: `activity_solver.py` overwrote weekend "OFF" codes with clinical activities when `include_faculty_slots=True`. Added faculty weekend exclusion filter. Weekend uses standard Sat+Sun (`weekday() >= 5`). Weekend violations: 60 → 0.
3. ~~**Solver activity model too coarse**~~ — **PARTIALLY FIXED.** Write-back at `engine.py` now template-aware: loads `faculty_weekly_templates`, resolves C→CV/sm_clinic/dfm, AT→gme/lec/SIM. 103 HDAs updated (56 Friday restorations + 47 template refinements). Cross-category mismatches (solver category vs template category) ~100 — requires FacultyWeeklyTemplateConstraint integration.
4. **Alembic stamp mismatch** — DB at `9bcfa50205e4`, not in migration files
5. ~~**DOW convention mismatch**~~ — **FIXED (P0).** All runtime bugs patched (constraint, frontend `isWeekend`/`DAY_LABELS`), all 9 docstrings corrected, disambiguation constants added, 67 regression tests. See `docs/architecture/DOW_CONVENTION_BUG.md`.

### Numeric Code Legend
| Code | Meaning | Activities |
|------|---------|-----------|
| 1 | Clinic | fm_clinic, CV, sm_clinic, C40, HLC, RAD |
| 2 | AT/Admin | at, gme, SIM, dfm |
| 3 | PCAT | pcat (post-call AM) |
| 4 | DO | do (post-call PM) |
| 5 | Leave | LV-AM, LV-PM |
| 6 | FMIT | FMIT inpatient teaching |
| 7 | Off/Weekend | W, off |
| 8 | Conference | lec, ADV, C, C-I |
| 9 | Rotation | NBN, NF, PedNF, PedW, DERM, CARDS, LDNF, PEM, TDY |

---

## Zeroing Process

### Step 1: Export Full Grid as CSV/Table

```sql
-- Full Block 12 grid
SELECT name, person_type, faculty_role, pgy_level,
    date, day_of_week, am_code, pm_code, am_source, pm_source
FROM schedule_grid
WHERE date >= '2026-05-07' AND date <= '2026-06-03'
ORDER BY person_type, name, date;
```

### Step 2: Resident Grid (16 people × 28 days)

Key columns from `block_assignments`:
- `resident_id` (column is `resident_id`, NOT `person_id`)
- `rotation_template_id` → rotation abbreviation
- `secondary_rotation_template_id` → NF-combined second half

For each resident, verify:
1. **Rotation code matches** — AM/PM codes align with assigned rotation
2. **Weekend pattern** — inpatient rotations have W on weekends, outpatient varies
3. **NF-combined split** — first 14 days = one rotation, day 15 = recovery, rest = other
4. **Source consistency** — preloaded slots match rotation handler expectations

```sql
-- Resident rotation assignments for Block 12
SELECT p.name, p.pgy_level, rt.abbreviation as rotation,
    rt2.abbreviation as secondary_rotation
FROM block_assignments ba
JOIN people p ON ba.resident_id = p.id
LEFT JOIN rotation_templates rt ON ba.rotation_template_id = rt.id
LEFT JOIN rotation_templates rt2 ON ba.secondary_rotation_template_id = rt2.id
WHERE ba.block_number = 12 AND ba.academic_year = 2025
ORDER BY p.pgy_level, p.name;
```

### Step 3: Faculty Grid (10 people × 28 days)

For each faculty member, verify:
1. **Template alignment** — solver-generated codes match `faculty_weekly_templates`
2. **Weekend handling** — should have W on Fri/Sat (per TAMC convention: Fri=day off, Sat=day off)
3. **Leave overlay** — LV-AM/LV-PM should align with `absences` table
4. **PCAT/DO post-call** — one day per faculty per call = PCAT AM, DO PM
5. **FMIT assignments** — preloaded from rotation, not solver-generated

```sql
-- Faculty template vs actual comparison
SELECT
    p.name,
    sg.date,
    sg.am_code as actual_am,
    sg.pm_code as actual_pm,
    sg.am_source,
    sg.pm_source,
    -- Template expectation for this day_of_week
    MAX(CASE WHEN fwt.time_of_day = 'AM' THEN a.code END) as template_am,
    MAX(CASE WHEN fwt.time_of_day = 'PM' THEN a.code END) as template_pm
FROM schedule_grid sg
JOIN people p ON sg.person_id = p.id
LEFT JOIN faculty_weekly_templates fwt
    ON fwt.person_id = p.id
    AND fwt.day_of_week = sg.day_of_week
    AND fwt.week_number IS NULL
LEFT JOIN activities a ON fwt.activity_id = a.id
WHERE sg.date >= '2026-05-07' AND sg.date <= '2026-06-03'
    AND sg.person_type = 'faculty'
GROUP BY p.name, sg.date, sg.am_code, sg.pm_code, sg.am_source, sg.pm_source
ORDER BY p.name, sg.date;
```

### Step 4: Delta Report

For each person, identify:
- **Mismatches**: actual ≠ template (for faculty) or actual ≠ rotation expectation (for residents)
- **Missing W**: non-W codes on Fri/Sat for faculty
- **Unexpected sources**: solver where preload expected, or vice versa
- **Coverage gaps**: NULL am_code or pm_code

### Step 5: Isolate DB vs Export Issues

**Key insight:** If the grid CSV/XLSX matches the coordinator's Excel, the export pipeline is correct and all issues are solver/preloader (DB-side). If they differ, isolate whether it's a DB issue or an export rendering issue.

| Where Mismatch Found | Root Cause Layer | Fix |
|----------------------|-----------------|-----|
| DB grid ≠ Excel AND DB grid is wrong | Solver/preloader | Fix preloader handler or solver constraint, re-run |
| DB grid ≠ Excel AND DB grid is right | Export pipeline | Fix `xml_to_xlsx_converter.py` or `canonical_schedule_export_service.py` |
| DB grid = Excel (both wrong) | Upstream data | Fix `block_assignments`, `faculty_weekly_templates`, or `absences` |
| DB grid = Excel (both right) | DONE | Move to next person |

### Step 6: Fix Enumeration

Each delta maps to a fix category:
| Delta Type | Fix |
|-----------|-----|
| Faculty actual ≠ template | Solver activity model too coarse → template-aware write-back |
| Faculty work Fri/Sat | Add weekend blocking at `fac_clinic`/`fac_supervise` level in solver |
| Resident code ≠ rotation | Preloader handler bug → fix handler → re-preload |
| Missing HDA | Preloader gap → add handler → re-preload |
| Wrong source | Engine routing issue → fix source assignment |
| Leave mismatch | Absence table gap → sync absences |

### Step 7: Iterate

After fixing each variable:
1. Re-run preloader (if preload issue)
2. Re-run solver (if constraint issue)
3. Re-query `schedule_grid`
4. Verify delta is gone
5. Next variable

---

## TAMC Calendar Convention

Per TAMC Family Medicine scheduling convention:
- **Block starts Thursday** (not Monday)
- **Week = Thu–Wed** (7 days)
- **Weekend = Sat + Sun** (standard civilian weekend)
- **Faculty FMIT call runs Fri–Thu** (24-hour overnight pattern, not aligned to blocks)

Weekend check: `weekday() >= 5` (Python: 5=Sat, 6=Sun) is correct.

## DOW Convention Mismatch — RESOLVED

**Status: FIXED (P0, Feb 27 2026).** All runtime bugs and documentation corrected.

See `docs/architecture/DOW_CONVENTION_BUG.md` for full details including:
- Runtime fixes: backend constraint (`_python_weekday_to_pattern` deleted), frontend `isWeekend()`/`DAY_LABELS`
- Documentation fixes: 9 files corrected
- Disambiguation constants: `PYTHON_WEEKDAY_*` and `PG_DOW_*`
- Regression tests: 67 tests (29 new + 38 existing fixed)

**Remaining LOW #42:** `block_assignment_expansion_service.py:713` uses `isoweekday() % 7` (PG DOW). Confirmed self-contained, does not interact with faculty templates.

---

## Key SQL Queries

### psql connection
```bash
PSQL=/opt/homebrew/Cellar/postgresql@17/17.7_1/bin/psql
$PSQL -h localhost -p 5432 -U scheduler -d residency_scheduler
```

### Quick health check
```sql
SELECT person_type, COUNT(DISTINCT person_id) as people, COUNT(*) as total_rows
FROM schedule_grid
WHERE date >= '2026-05-07' AND date <= '2026-06-03'
GROUP BY person_type;
```

### Per-person summary
```sql
SELECT name, person_type, faculty_role,
    COUNT(DISTINCT am_code) as am_codes,
    COUNT(DISTINCT pm_code) as pm_codes,
    COUNT(*) FILTER (WHERE am_source = 'preload') as preload_days,
    COUNT(*) FILTER (WHERE am_source = 'solver') as solver_days
FROM schedule_grid
WHERE date >= '2026-05-07' AND date <= '2026-06-03'
GROUP BY name, person_type, faculty_role
ORDER BY person_type, name;
```

---

## Faculty Solver Architecture (Key Finding)

The CP-SAT solver uses a **coarse 4-type faculty activity model**:

| Solver Variable | Activity Type | When Created |
|----------------|--------------|-------------|
| `fac_clinic[f_i, b_i]` | Clinic (C) | Workdays only |
| `fac_supervise[f_i, b_i]` | Attending/Supervision (AT) | Workdays only |
| `fac_pcat[f_i, b_i]` | Post-Call Attending (PCAT) | All days, linked to call |
| `fac_do[f_i, b_i]` | Day Off post-call (DO) | All days, linked to call |
| *(none set)* | OFF | Default |

**The write-back** (`engine.py:3370`) maps these to activity codes: C→fm_clinic, AT→at. It does NOT consult faculty weekly templates for specific activity selection (CV vs fm_clinic vs sm_clinic).

**Templates have ~15 activity types** (CV, fm_clinic, sm_clinic, at, gme, SIM, dfm, lec, etc.) which map to the 4 solver types. The solver decides *clinic vs supervise*, not *which specific clinic*.

**Implication for zeroing:** Faculty solver slots will always show generic codes (fm_clinic, at, gme). To match Excel exactly, the write-back needs to be template-aware: look up the faculty's weekly template for that day/slot and use the template's specific activity code instead of the generic one.

---

## Zeroing Exports

| File | Format | Content |
|------|--------|---------|
| `/tmp/block12_pivoted_grid.csv` | CSV | 26 rows × 59 cols, raw activity codes |
| `/tmp/Block12_Schedule_Grid_Zeroing.xlsx` | XLSX | 3 sheets: Raw Codes, Numeric Codes (1-9), Legend |

Open in Excel → compare against coordinator's Block 12 workbook → Claude for Excel identifies cell-by-cell deltas.

---

## Files

| File | Purpose |
|------|---------|
| `backend/alembic/versions/20260227_schedule_grid_view.py` | Alembic migration for view |
| `backend/app/scheduling/solvers.py:968-1073` | Faculty activity variables + constraint wiring |
| `backend/app/scheduling/engine.py:3281-3415` | Faculty HDA write-back from solver |
| `backend/app/scheduling/constraints/faculty_weekly_template.py` | Template constraint (not registered) |
| `backend/app/scheduling/constraints/manager.py:324-480` | Constraint registration |
| `docs/planning/SCHEDULE_GRID_ZEROING_PLAN.md` | This file |
| `docs/planning/BLOCK_12_ANNUAL_WORKBOOK_ROADMAP.md` | Parent roadmap (section 11l) |
| `docs/planning/OPUS_BLOCK_12_REMEDIATION_PLAN.md` | Phase 4 quality refinement |

---

## Dependencies

- PG17 running on localhost:5432
- psql at `/opt/homebrew/Cellar/postgresql@17/17.7_1/bin/psql`
- Backend venv at `/Users/aaronmontgomery/.pyenv/versions/aapm`
- Settings validation blocks app import — use psql directly or set `SKIP_SETTINGS_VALIDATION=1`
- `schedule_grid` view already created in live DB
