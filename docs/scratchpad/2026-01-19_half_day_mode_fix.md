# Session Summary: Half-Day Mode Schedule Generation Fix

**Date:** 2026-01-19
**Status:** COMPLETE

---

## Task

Fix `expand_block_assignments=True` mode in the scheduling engine to generate half-day assignments for Block 10.

## Problem Diagnosed

When calling `/api/v1/schedule/generate` with `expand_block_assignments=True`:
1. Expansion service creates 952 `Assignment` objects + 420 `HalfDayAssignment` records
2. Engine tried to persist Assignment objects to old table → unique constraint violations
3. Multiple code paths were adding to `self.assignments` which all get flushed to old table

## Root Cause

The engine had 4 sources adding Assignment objects:
1. Expansion service (now uses HalfDayAssignment)
2. `_create_assignments_from_result` (solver results)
3. `_assign_faculty` (faculty supervision)
4. Call assignments (separate table - OK)

In half-day mode, #2 and #3 are redundant because expansion already handles resident assignments.

## Changes Made

**File:** `backend/app/scheduling/engine.py`

| Line | Change |
|------|--------|
| 265 | Added `persist_half_day=True` to expansion call |
| 383-398 | Skip adding expanded assignments to `self.assignments` |
| 400-410 | Skip `_create_assignments_from_result` in half-day mode |
| 418-426 | Skip `_assign_faculty` in half-day mode |
| 1091-1099 | Fixed call_type mapping (`weekday`→`overnight`, `sunday`→`weekend`) |

## Results

**Database State After Generation:**

| Table | Source | Count |
|-------|--------|-------|
| half_day_assignments | preload (faculty) | 166 |
| half_day_assignments | preload (resident) | 540 |
| half_day_assignments | solver (resident) | **420 NEW** |
| call_assignments | overnight/weekend | **20 NEW** |

## Key Files

- `backend/app/scheduling/engine.py` - Main changes
- `backend/app/services/block_assignment_expansion_service.py` - Dual-write logic (existing)
- Plan file: `.claude/plans/quirky-percolating-feather.md`

## Backup

Pre-change backup: `backups/pre_solver_20260119_193531.sql`

## API Call

```bash
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "start_date": "2025-03-13",
    "end_date": "2025-04-09",
    "algorithm": "greedy",
    "expand_block_assignments": true,
    "block_number": 10,
    "academic_year": 2025,
    "timeout_seconds": 120
  }'
```

Note: Block 10 AY 2025 = March 2026 calendar dates (2026-03-12 to 2026-04-08)

## Next Steps

- Faculty half-day assignments need separate generation via `FacultyAssignmentExpansionService`
- Consider adding faculty expansion to the engine flow
- Validate against ROSETTA ground truth
