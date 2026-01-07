# Session 067 - Schedule UX Redesign

**Branch:** `session/067-antigravity-faculty-call` | **Date:** 2026-01-07

## Status: COMMITTED ✅

Commit `15a62aa4` pushed to remote.

## All Fixes Applied

### Backend Fixes

| File | Fix |
|------|-----|
| `backend/app/schemas/block.py` | `block_number` limit 13→14 (DB has block 14 for June) |
| `backend/app/schemas/absence.py` | `deployment_orders: bool` → `bool \| None` |
| `backend/app/auth/permissions/decorators.py` | **MAJOR** - Rewrote `require_role` from decorator to FastAPI dependency (was causing "func query param required" 422 error) |
| `backend/app/services/call_assignment_service.py` | Added `selectinload(CallAssignment.person)` after create to fix async greenlet error |
| `backend/app/controllers/*.py` | Added `model_validate()` to 9 controllers (13 methods) for ORM→Pydantic conversion |

### Frontend Fixes

| File | Fix |
|------|-----|
| `frontend/src/features/call-roster/hooks.ts` | **REWROTE** - Use `/call-assignments` endpoint instead of `/assignments?activity_type=on_call` |
| `frontend/src/types/call-assignment.ts` | `call_date`→`date` for response types (backend uses alias) |
| `frontend/src/app/admin/faculty-call/page.tsx` | Fixed transform function + wired up create modal |
| `frontend/src/components/admin/CreateCallAssignmentModal.tsx` | **NEW** - Modal with date picker, faculty dropdown, call type selector |

## Key Debugging Patterns

### "func query param required" (422)
**Cause:** `require_role` was a decorator being used as `Depends(require_role([...]))` - FastAPI tried to inject `func` parameter
**Fix:** Rewrote `require_role` to return a dependency function, not a decorator

### "MissingGreenlet" async error
**Cause:** SQLAlchemy lazy loading `person` relationship outside async context
**Fix:** Re-query with `selectinload()` after create/update

### "Objects are not valid as React child"
**Cause:** Pydantic validation error object being rendered
**Fix:** Check controller has `model_validate()`, schema constraints match DB

## Working URLs

- `/call-roster` ✅ - Faculty call calendar
- `/admin/faculty-call` ✅ - Faculty call management with create
- `/schedule` (week view) - Diagnosed, code correct, may need browser hard refresh

## Schedule Week View Issue - FIXED ✅

User reported Mon-Wed only showing.

**Root Cause:** API pagination - default `page_size=100` only returned first 100 of 272 assignments for the week. Days with assignments outside the first 100 showed empty.

**Fix:** Changed `frontend/src/app/schedule/page.tsx` to use `page_size=500` (backend max) for both blocks and assignments queries.

```typescript
// Before: /assignments?start_date=...&end_date=... (default 100)
// After:  /assignments?start_date=...&end_date=...&page_size=500
```

## Annual View Freeze Fix

**Problem:** Res./Fac. buttons in ViewToggle switch to annual views that render 21,900+ cells (30 residents × 365 days × 2 AM/PM), causing browser freeze.

**Fix:** Added performance safeguard to both views:
- `ResidentAcademicYearView.tsx` - Shows warning if >5000 cells
- `FacultyInpatientWeeksView.tsx` - Shows warning if >5000 cells

User can click "Render Anyway" or "Switch to Block View".

---

## CURRENT WORK: Schedule View UX Redesign

**Plan:** `/Users/aaronmontgomery/.claude/plans/merry-hatching-torvalds.md`

### Overview

Reorganize schedule views into Block Views and Calendar Views:

```
┌─────────────────────────────────────────────────────────┐
│ [Block Views]                │  [Calendar Views]        │
│ ┌────┬────────┬──────┐       │  ┌─────┬──────┬───────┐  │
│ │ AY │ Block  │ Week │       │  │ Day │ Week │ Month │  │
│ └────┴────────┴──────┘       │  └─────┴──────┴───────┘  │
└─────────────────────────────────────────────────────────┘
```

### New Components Needed

1. **BlockAnnualView.tsx** (NEW)
   - 14 columns: Block 0-13
   - Rows: Residents only, grouped by PGY
   - Cells: Rotation abbreviation + color
   - Block 0: Warning banner for orientation period
   - Click block → navigate to Block view

2. **PersonFilter.tsx** - Enhance for multi-select
   - Current: Single-select (exists but not wired up)
   - Needed: Multi-select to compare schedules (e.g., SM resident + SM faculty)

3. **ViewToggle.tsx** - Reorganize
   - Remove Res./Fac. from visible (keep as URL param hidden)
   - Add block-annual view type
   - Group: Block Views | Calendar Views

### Key User Decisions

- Block AY: **Residents only** (faculty don't have block rotations)
- Block Week: Default to **current week** within selected block
- Res/Fac views: **Keep as hidden** (URL param access only)
- Block 0: **Must be visible** with warning banner

### API for Block Assignments

Endpoint: `/block-scheduler/assignments` (block_scheduler.py)
- Uses `BlockAssignmentResponse` schema
- Fields: block_number, academic_year, resident_id, rotation_template_id

### Progress

- [x] Explored current views and data models
- [x] Plan approved
- [ ] Create BlockAnnualView.tsx
- [ ] Modify ViewToggle.tsx
- [ ] Update schedule/page.tsx
- [ ] Enhance PersonFilter for multi-select
- [ ] Add Block 0 warning

---

## TODO (backlog)

- [ ] Date picker typing quirk in CreateCallAssignmentModal

## Test Credentials

- Username: `admin`
- Password: `admin123`
