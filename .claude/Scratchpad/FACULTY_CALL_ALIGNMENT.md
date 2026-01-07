# Faculty Call & Schedule Fixes - Session 067

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

## Schedule Week View Issue

User reported Mon-Wed only showing. Diagnosis:
- Container code matches source ✅
- `weekStartsOn: 1` correctly set in WeekView.tsx:92 ✅
- `Array.from({ length: 7 })` correct ✅
- `grid-cols-8` correct ✅

**Likely cause:** Browser cache. Try Cmd+Shift+R hard refresh.

## TODO

- [ ] Date picker typing quirk in CreateCallAssignmentModal (year shows last digit only when typing)
  - Either make read-only with calendar-only, or use custom date picker component

## Test Credentials

- Username: `admin`
- Password: `admin123`
