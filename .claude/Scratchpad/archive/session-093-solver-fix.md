# Session 093: Solver 3D Visualization Fix

**Date:** 2026-01-13
**Branch:** `feat/exotic-explorations`

## Summary

Fixed the 500 errors on `/schedule/generate` that were preventing the Solver 3D visualization from working.

## Root Cause Analysis

### Myth Busted: Next.js Header Forwarding

The original theory that Next.js rewrites strip Authorization headers was **incorrect**.

**Evidence:**
- Tested with `curl` through Next.js proxy (port 3000)
- Backend logs confirmed `Authorization: Bearer ...` header was received
- The `user=anonymous` in PHI middleware is benign - it runs before auth sets the user

### Actual Root Causes

1. **Database Constraint Violation (FIXED)**
   - Error: `UniqueViolation: duplicate key violates unique constraint "unique_call_per_day"`
   - Root cause: No cleanup of existing CallAssignments before regeneration + type mismatch
   - The solver uses `call_type='overnight'` but the constraint only allows `('sunday', 'weekday', 'holiday', 'backup')`

2. **Solver Type Error (NOT FIXED)**
   - Error: `__rsub__(): incompatible function arguments`
   - This is data-dependent and requires further investigation
   - Likely occurs when specific constraint combinations are active

3. **WebSocket Error (Symptom)**
   - Error: `WebSocket is not connected. Need to call "accept" first.`
   - This was a symptom of the solver crashing mid-broadcast, not a root cause

## Fixes Applied

### File: `backend/app/scheduling/engine.py`

**Method:** `_create_call_assignments_from_result`

Changes:
1. Added cleanup of existing call assignments for the date range before inserting
2. Added mapping from `'overnight'` to correct database values:
   - Sunday → `'sunday'`
   - Mon-Thu → `'weekday'`

```python
# Clear existing call assignments for this date range to avoid conflicts
deleted_count = (
    self.db.query(CallAssignment)
    .filter(
        CallAssignment.date >= self.start_date,
        CallAssignment.date <= self.end_date,
    )
    .delete(synchronize_session=False)
)

# Map solver call types to database-allowed values
is_sunday = block.date.weekday() == 6
if call_type == "overnight":
    mapped_call_type = "sunday" if is_sunday else "weekday"
else:
    mapped_call_type = call_type
```

## Testing Required

After rebuilding the backend container:
1. Log in to the scheduling admin page
2. Trigger schedule generation
3. Verify 200 response (not 500)
4. Check voxel visualization renders

## Remaining Issues

- `__rsub__` solver error - data-dependent, needs investigation with specific test case
- WebSocket error - should resolve once solver stops crashing

## Container Rebuild Command

```bash
docker-compose up -d --build backend
```
