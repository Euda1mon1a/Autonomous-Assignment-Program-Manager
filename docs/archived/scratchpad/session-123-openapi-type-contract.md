# Session 123: OpenAPI Type Contract Enforcement

> **Date:** 2026-01-20
> **Branch:** `feature/activity-assignment-session-119`
> **Latest Commit:** Pending (P3 endpoint wiring)

---

## Mission

Implement "belt and suspenders" enforcement to prevent schema drift. Schema changes must be intentional.

## What We Found (Search-Party Intel)

120-probe search-party discovered:
- **47+ total disconnects**
- **4 Critical 404s** (resilience endpoints)
- **35+ query param violations** (camelCase sent, snake_case expected)
- **5 enum drift values** (AbsenceType mismatch)
- **Faculty pipeline gap** (writes to `assignments` instead of `half_day_assignments`)

## Completed Work

### P0: OpenAPI Type Contract Enforcement ✅

**File:** `frontend/scripts/generate-api-types.sh`
- Generates types from backend OpenAPI spec
- **Smart camelCase conversion**: Only converts `components.schemas.*` properties
- **Preserves snake_case** for query/path params (Couatl Killer protection)
- `--check` mode for drift detection

**CLAUDE.md Standing Order Added:**
- Generated types ARE the source of truth
- Pre-commit hook, CI check, startup check

**Regenerated Types:**
- `frontend/src/types/api-generated.ts`
- 68,766 lines, 979 schemas, 3,657 properties converted to camelCase
- Query params preserved as snake_case

### P1: Query Param Violations Fixed ✅

**90+ violations fixed across 17 files:**

| File | Params Fixed |
|------|--------------|
| `useAbsences.ts` | person_id, start_date, end_date, absence_type, academic_year |
| `useSwaps.ts` | swap_type, source_faculty_id, target_faculty_id, start_date, end_date |
| `useCallAssignments.ts` | start_date, end_date, person_id, call_type |
| `useFacultyActivities.ts` | week_number, day_of_week, time_of_day, start_date, end_date |
| `useAdminUsers.ts` | page_size, user_id, date_from, date_to |
| `useProcedures.ts` | is_active, complexity_level, include_expired |
| `useAdminScheduling.ts` | start_date, end_date |
| `usePeople.ts` | pgy_level |
| `useAdminTemplates.ts` | activity_type |
| `features/audit/hooks.ts` | start_date, end_date, user_ids |
| `features/fmit-timeline/hooks.ts` | start_date, end_date, faculty_ids, rotation_ids, workload_status, view_mode |
| `features/heatmap/hooks.ts` | start_date, end_date, person_ids, rotation_ids, include_fmit, group_by |
| `features/conflicts/hooks.ts` | person_ids, start_date, end_date |
| `features/daily-manifest/hooks.ts` | time_of_day |
| `features/holographic-hub/hooks.ts` | start_date, end_date |
| `lib/export.ts` | start_date, end_date, block_number |

### P2: AbsenceType Enum Drift Fixed ✅

**Values changed (camelCase → snake_case):**
- `familyEmergency` → `family_emergency`
- `emergencyLeave` → `emergency_leave`
- `maternityPaternity` → `maternity_paternity`

**Values added:**
- `training`
- `military_duty`

**Files updated:**
- `src/types/api.ts` (enum definition)
- `src/components/AddAbsenceModal.tsx`
- `src/app/absences/page.tsx`
- `src/features/import-export/types.ts`
- `src/features/import-export/validation.ts`

### P3: Resilience Endpoint Wiring ✅

**Decision:** Add backend endpoints to wire frontend calls to existing calculators.

**New Backend Schemas Added (`backend/app/schemas/resilience.py`):**
- `DefenseLevelRequest` / `DefenseLevelResponse`
- `UtilizationThresholdRequest` / `UtilizationThresholdResponse`
- `BurnoutRtRequest` / `BurnoutRtResponse`
- `CircuitBreakerState`, `CircuitBreakerInfo`
- `AllBreakersStatusResponse`
- `BreakerHealthMetrics`, `BreakerHealthResponse`, `BreakerSeverity`

**New Backend Endpoints Added (`backend/app/api/routes/resilience.py`):**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/resilience/defense-level` | POST | Calculate defense level from coverage rate |
| `/resilience/utilization-threshold` | POST | Check utilization against 80% threshold |
| `/resilience/burnout/rt` | POST | Calculate burnout reproduction number |
| `/resilience/circuit-breakers` | GET | Get all circuit breaker statuses |
| `/resilience/circuit-breakers/health` | GET | Get aggregated breaker health metrics |

**Frontend Types Regenerated:**
- `frontend/src/types/api-generated.ts` now includes new schemas
- 992 schemas, 69,289 lines

---

## Status Summary

| Phase | Scope | Status |
|-------|-------|--------|
| P0 | OpenAPI enforcement | ✅ Complete |
| P1 | Fix 90+ query param violations | ✅ Complete |
| P2 | Fix enum drift (AbsenceType) | ✅ Complete |
| P3 | Wire resilience endpoints | ✅ Complete |
| P4 | Refactor faculty pipeline to half_day_assignments | Pending (backend) |

---

## What's Left

### P4: Faculty Pipeline (Backend Refactor)

Current: `FacultyAssignmentExpansionService` → `assignments` table
Should: `FacultyAssignmentExpansionService` → `half_day_assignments` table

This is a backend refactor - separate scope from frontend wiring.

---

## Pre-existing Type Errors (Not from our changes)

These TS errors existed before session 123 and are unrelated to P1/P2/P3:
- `src/app/admin/resilience-hub/page.tsx` - FairnessAuditResponse prop mismatches
- `src/components/TemplatePatternModal.tsx` - WeeklyGridEditorProps mismatch
- `src/features/bridge-sync/components/BridgeEdge3D.tsx` - Three.js ref types

---

## Verification Commands

```bash
# Check for query param violations (should return nothing)
grep -rE "params\.(set|append)\(['\"][a-z]+[A-Z]" frontend/src --include="*.ts"

# Check for camelCase enum values (should return nothing)
grep -rE "'familyEmergency'|'emergencyLeave'|'maternityPaternity'" frontend/src

# Regenerate types if backend schema changes
cd frontend && npm run generate:types

# Check for drift
cd frontend && npm run generate:types:check

# Test new endpoints (requires backend running)
curl -X POST http://localhost:8000/resilience/defense-level \
  -H "Content-Type: application/json" \
  -d '{"coverage_rate": 0.85}'

curl http://localhost:8000/resilience/circuit-breakers
curl http://localhost:8000/resilience/circuit-breakers/health
```

---

*Session 123 - P0/P1/P2/P3 complete.*
