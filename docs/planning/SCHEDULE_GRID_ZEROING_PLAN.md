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

### Block 12 Data (DONE)
- 16 real residents × 56 HDAs each ✓
- 14 faculty × 56 HDAs each ✓
- Adjunct faculty not yet in DB (migration unapplied)

### Known Quality Issues
1. **All faculty work weekends** — WeekendWork constraint disabled
2. **Several faculty near all-GME** — FacultyWeeklyTemplateConstraint not registered
3. **Orphaned activity UUID** — 8 template rows → `9fd0dca9-...` (should be FMIT, wrong UUID)
4. **Alembic stamp mismatch** — DB at `9bcfa50205e4`, not in migration files

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

### Step 3: Faculty Grid (14 people × 28 days)

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

### Step 5: Fix Enumeration

Each delta maps to a fix category:
| Delta Type | Fix |
|-----------|-----|
| Faculty actual ≠ template | Register FacultyWeeklyTemplateConstraint + re-solve |
| Faculty weekend ≠ W | Re-enable WeekendWork + re-solve |
| Resident code ≠ rotation | Preloader handler bug → fix handler → re-preload |
| Missing HDA | Preloader gap → add handler → re-preload |
| Wrong source | Engine routing issue → fix source assignment |
| Leave mismatch | Absence table gap → sync absences |

### Step 6: Iterate

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
- **Weekend = Fri + Sat** (military schedule, not civilian Sat+Sun)
- **Sunday is a regular workday** for clinical rotations

This is critical for interpreting the grid. A faculty member working on Sunday is NORMAL. Working on Friday/Saturday is the issue.

**Correction needed:** The `WeekendWork` constraint and `schedule_grid` queries need to check `day_of_week IN (5, 6)` (Fri/Sat), NOT `(0, 6)` (Sun/Sat).

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

## Files

| File | Purpose |
|------|---------|
| `backend/alembic/versions/20260227_schedule_grid_view.py` | Alembic migration for view |
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
