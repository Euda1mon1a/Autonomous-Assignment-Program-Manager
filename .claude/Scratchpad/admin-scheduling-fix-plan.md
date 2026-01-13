# Admin Scheduling Hub - Session Progress

> **Last Updated:** 2026-01-13 | **Status:** Generate flow FIXED, API type drift prevention ADDED

---

## Summary

Made Admin Scheduling Hub functional: fixed validation endpoint, fixed type mismatches, added OpenAPI type generation to prevent future drift.

## Session 2 Completed Work (This Session)

### 1. Fixed Validate Config 422 Error

**Problem:** `useValidateConfiguration` sent raw `RunConfiguration`, backend expected `ScheduleRequest`

**File:** `frontend/src/hooks/useAdminScheduling.ts` (lines 118-128)
```typescript
// BEFORE: post('/schedule/validate-config', config)
// AFTER: Transforms blockRange → startDate/endDate like useGenerateScheduleRun does
```

### 2. Fixed ValidationResponse Type Mismatch

**Problem:** Frontend expected `isValid`/`warnings`, backend returns `valid`/`violations`

**Files changed:**
- `frontend/src/types/admin-scheduling.ts` - Updated `ValidationResponse` interface
- `frontend/src/app/admin/scheduling/page.tsx` - Updated all usages (lines 158, 659-694, 338, 1548)

### 3. Created OpenAPI Type Generation System (DRIFT PREVENTION)

**New files:**
- `frontend/scripts/generate-api-types.sh` - Generation + drift check script
- `frontend/src/types/api-generated.ts` - 60K lines of generated types (861 schemas)

**Updated:**
- `frontend/package.json` - Added `generate:types` and `generate:types:check` scripts
- `scripts/validate-api-contract.sh` - Pre-commit now checks for type drift

**Usage:**
```bash
cd frontend && npm run generate:types        # Regenerate from live backend
cd frontend && npm run generate:types:check  # Check for drift (pre-commit uses this)
```

## Session 1 Completed Work (Previous Session)

### Backend Queue Endpoints (ALL DONE)
- `GET /schedule/queue` → `RunQueueResponse`
- `POST /schedule/queue/batch` → `list[ExperimentRunResponse]`
- `DELETE /schedule/queue/{run_id}` → cancels experiment

### Frontend (ALL DONE)
- Lazy loading for 3D components (DoD GPU performance)
- Fixed activeRun reference

## Current Status

| Feature | Status |
|---------|--------|
| Queue endpoints | ✅ Working |
| Validate config | ✅ Fixed - green checkmark shown |
| Generate button | ⚠️ 500 error - DB needs re-seeding |
| Schedule 3D data | ⚠️ Shows test data (transformation mismatch) |
| API drift prevention | ✅ Pre-commit hook active |
| Database | ❌ Lost in 95GB cleanup - needs re-seed |

## Next Steps (if continuing)

1. **Re-seed database** - DB lost during 95GB cleanup, causes 500 on generate
   - Error: `block_assignments.block_number = (0, 2024)` - no data to query
   - Run: `cd backend && python -m app.db.seed` or similar
2. **Schedule 3D real data** - Fix VoxelScheduleView3D transformation for nested API response
3. **Phase 4 (deferred)** - Celery task integration for async schedule generation
4. **Fix key prop warning** - ConfigurationPanel ConstraintToggle needs unique key

## Key Files

| File | What |
|------|------|
| `frontend/src/hooks/useAdminScheduling.ts:118-128` | Fixed validate hook |
| `frontend/src/types/admin-scheduling.ts:266-281` | Fixed ValidationResponse type |
| `frontend/src/types/api-generated.ts` | 60K generated types (source of truth) |
| `frontend/scripts/generate-api-types.sh` | Type generation script |
| `scripts/validate-api-contract.sh` | Pre-commit drift detection |

## Drift Prevention Pattern (NEW)

**Root cause of today's bug:** Frontend TypeScript types were hand-written and drifted from backend Pydantic schemas.

**Solution implemented:**
1. FastAPI auto-generates OpenAPI spec at `/openapi.json`
2. `openapi-typescript` generates TS types from that spec
3. Pre-commit hook compares generated vs committed types
4. If drift detected → commit blocked, developer must regenerate

**This prevents:** Future `isValid` vs `valid` type mismatches
