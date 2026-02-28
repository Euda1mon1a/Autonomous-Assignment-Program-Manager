# Day-of-Week Convention Mismatch Bug

**Created:** 2026-02-27
**Severity:** P0 (runtime bugs in constraint + frontend, documentation across 9+ files)
**Status:** **FIXED** — all runtime bugs patched, all docstrings corrected, regression tests added

---

## Summary

Two different DOW conventions coexist in the codebase:

| Table | Convention | 0 | 5 | 6 |
|-------|-----------|---|---|---|
| `faculty_weekly_templates` | **Python weekday** | Monday | Saturday | Sunday |
| `weekly_patterns` | **PG EXTRACT(DOW)** | Sunday | Friday | Saturday |

Most code was written assuming PG DOW everywhere, but faculty templates were seeded with Python `weekday()`. This caused:
- **Runtime bug (latent):** `FacultyWeeklyTemplateConstraint` converted Python→PG DOW before template lookup → off-by-one day mismatch
- **Runtime bug (frontend):** `isWeekend()` flagged Monday as weekend, missed Saturday; `DAY_LABELS` mapped 0→Sunday for faculty data
- **Documentation bugs:** 9+ files had wrong DOW comments/docstrings

**The data was always correct. The code and documentation were wrong.**

---

## Convention Reference

| Convention | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|-----------|---|---|---|---|---|---|---|
| **Python `weekday()`** | Mon | Tue | Wed | Thu | Fri | Sat | Sun |
| **Python `isoweekday()`** | — | Mon | Tue | Wed | Thu | Fri | Sat (Sun=7) |
| **PG `EXTRACT(DOW ...)`** | Sun | Mon | Tue | Wed | Thu | Fri | Sat |
| **PG `EXTRACT(ISODOW ...)`** | — | Mon | Tue | Wed | Thu | Fri | Sat (Sun=7) |

---

## Evidence That Data Uses Python Weekday

1. **Faculty templates with DOW=4 contain Friday activities** (at, gme, sm_clinic, dfm, FMIT) — confirmed via DB query
2. **Faculty templates with DOW=5,6 contain "W" (weekend)** — Saturday and Sunday
3. **`call_equity.py:877`** compares `pref.day_of_week` directly with `date.weekday()` (Python convention)
4. **`activity_solver.py:1019`** does the same comparison
5. Template data was seeded using Python `weekday()` convention

---

## Root Cause

The `FacultyWeeklyTemplate` model was initially created with PG DOW in the docstring (migration `20260109_faculty_weekly.py` has `comment="0=Sunday, 6=Saturday"`). However, all code that seeds and consumes the data uses Python `weekday()`. The model documentation was never validated against actual usage.

The PG DOW convention in comments may have originated from:
- FMIT call patterns (Fri-Sat overnight) where someone confused the specific FMIT DOW numbering with general convention
- Faculty schedules being independent of block schedules, creating cross-pollination of conventions

---

## Fixes Applied (2026-02-27)

### Phase 1: Core models and engine (initial session)

| File | What Changed |
|------|-------------|
| `backend/app/models/faculty_weekly_template.py` | Docstring, column comment, `__repr__`, `day_name`, `is_weekend` — all now Python weekday |
| `backend/app/models/faculty_weekly_override.py` | Same fixes as template model |
| `backend/app/scheduling/engine.py:3334-3355` | Template lookup comments corrected |
| `backend/app/scheduling/engine.py:3373-3377` | `_resolve_template_activity()` uses `slot_date.weekday()` directly |

### Phase 2: Runtime bugs + all docstrings (P0 fix session)

| File | What Changed |
|------|-------------|
| `backend/app/scheduling/constraints/faculty_weekly_template.py` | **RUNTIME FIX:** Deleted `_python_weekday_to_pattern()`, use `weekday()` directly at 3 call sites. Fixed `_get_effective_slot()` docstring. |
| `frontend/src/types/faculty-activity.ts` | **RUNTIME FIX:** `isWeekend()` now checks `>= 5` (Sat/Sun). `DAY_LABELS` + `DAY_LABELS_SHORT` now map 0→Monday. JSDoc corrected. |
| `backend/app/schemas/faculty_activity.py` | Docstring: `"0=Monday, 6=Sunday (Python weekday)"` (2 locations) |
| `backend/app/schemas/rotation_template_gui.py` | Clarified: `"PG DOW: 0=Sunday, 6=Saturday (weekly_patterns convention)"` (2 locations) |
| `backend/app/services/faculty_activity_service.py` | Docstring: `"0-6 (Monday-Sunday, Python weekday)"` (4 locations) |
| `backend/app/scheduling/constraints/protected_slot.py` | Clarified comments: weekly_patterns uses PG DOW |
| `backend/app/models/weekly_pattern.py` | Added `PG_DOW_SUNDAY`/`PG_DOW_SATURDAY` constants, clarified docstring and column comment |
| `backend/app/models/faculty_weekly_template.py` | Added `PYTHON_WEEKDAY_SATURDAY`/`PYTHON_WEEKDAY_SUNDAY` constants |
| `backend/scripts/backfill_external_rotation_saturday_off.py` | Comment: `"PG DOW convention: 0=Sunday, 6=Saturday"` |
| `backend/scripts/backfill_weekly_patterns_saturday_off.py` | Same |

### Regression Tests Added

| File | What It Tests |
|------|---------------|
| `backend/tests/scheduling/constraints/test_faculty_weekly_template_dow.py` | Template lookup matches correct day, `_python_weekday_to_pattern` removed |
| `backend/tests/models/test_dow_conventions.py` | Constants are distinct between the two conventions |
| `frontend/src/__tests__/types/faculty-activity-dow.test.ts` | `isWeekend()`, `DAY_LABELS`, `DAY_LABELS_SHORT` use Python weekday |

---

## NOT Changed (Intentionally)

| File | Reason |
|------|--------|
| `backend/alembic/versions/20260109_faculty_weekly.py` | Never edit existing migrations |
| `frontend/src/types/weekly-pattern.ts` | Correctly uses PG DOW for `weekly_patterns` data |
| `backend/app/models/weekly_pattern.py` (convention) | PG DOW is correct for this table |
| `backend/app/services/block_assignment_expansion_service.py` | Self-contained PG DOW usage, does not cross into faculty template context |

---

## Disambiguation Constants

To prevent future confusion, explicit constants are defined:

```python
# backend/app/models/faculty_weekly_template.py
PYTHON_WEEKDAY_SATURDAY = 5  # Python weekday convention
PYTHON_WEEKDAY_SUNDAY = 6

# backend/app/models/weekly_pattern.py (class attributes)
WeeklyPattern.PG_DOW_SUNDAY = 0  # PG EXTRACT(DOW) convention
WeeklyPattern.PG_DOW_SATURDAY = 6
```

---

## Testing Verification

### Automated tests

```bash
# Backend
cd backend && pytest tests/scheduling/constraints/test_faculty_weekly_template_dow.py tests/models/test_dow_conventions.py -v

# Frontend
cd frontend && npm test -- --testPathPattern faculty-activity-dow
```

### DB verification queries

```sql
-- Should show Friday activities (at, gme, sm_clinic, etc.) for DOW=4
SELECT p.name, fwt.day_of_week, fwt.time_of_day, a.code
FROM faculty_weekly_templates fwt
JOIN people p ON fwt.person_id = p.id
JOIN activities a ON fwt.activity_id = a.id
WHERE fwt.day_of_week = 4  -- Python weekday for Friday
  AND fwt.week_number IS NULL
ORDER BY p.name;

-- Should show W (weekend) for DOW=5 (Sat) and DOW=6 (Sun)
SELECT fwt.day_of_week, a.code, COUNT(*)
FROM faculty_weekly_templates fwt
JOIN activities a ON fwt.activity_id = a.id
WHERE fwt.week_number IS NULL
GROUP BY fwt.day_of_week, a.code
ORDER BY fwt.day_of_week, a.code;
```
