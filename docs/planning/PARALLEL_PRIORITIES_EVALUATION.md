# Parallel Priorities Evaluation

> **Generated:** 2025-12-18
> **Updated:** 2025-12-18
> **Purpose:** Identify 10 independent workstreams for parallel terminal execution
> **Status:** COMPLETED - All workstreams executed successfully
> **Next Session:** See `SESSION_8_PARALLEL_PRIORITIES.md` for current priorities

---

## Executive Summary

This document identifies **10 independent work areas** that can be executed in parallel without file conflicts or logical dependencies. Each workstream operates on isolated files/directories and can be completed autonomously.

---

## Workstream Overview

| # | Workstream | Priority | Type | Primary Files | Status |
|---|------------|----------|------|---------------|--------|
| 1 | Swap Executor Implementation | High | Backend | `swap_executor.py` | ✅ COMPLETED |
| 2 | Stability Metrics TODOs | Medium | Backend | `stability_metrics.py` | ✅ COMPLETED |
| 3 | Leave Routes FMIT Integration | Medium | Backend | `leave.py` | ✅ COMPLETED |
| 4 | Portal Routes Enhancement | Low | Backend | `portal.py` | ✅ COMPLETED |
| 5 | FMIT Week Verification | High | Backend | `swap_request_service.py:668` | ✅ COMPLETED |
| 6 | Frontend Hooks Reorganization | Medium | Frontend | `hooks.ts` → `hooks/` | ✅ COMPLETED |
| 7 | Frontend Feature Tests | Medium | Frontend | New test files | ⏳ Deferred to Session 8 |
| 8 | Constraints Module Refactoring | High | Backend | `constraints.py` | ⏳ Deferred to Session 8 |
| 9 | Documentation Consolidation | Low | Docs | `docs/`, `wiki/` | ⏳ Deferred to Session 8 |
| 10 | Playwright E2E Test Expansion | Low | Frontend | `e2e/` | ⏳ Deferred to Session 8 |

---

## Detailed Workstream Specifications

### Workstream 1: Swap Executor Implementation
**Priority:** High | **Type:** Backend Feature

**Location:** `backend/app/services/swap_executor.py`

**TODOs to Resolve:**
- Line 60: `# TODO: Persist SwapRecord when model is wired`
- Line 61: `# TODO: Update schedule assignments`
- Line 62: `# TODO: Update call cascade`
- Line 84: `# TODO: Implement when SwapRecord model is wired`

**Tasks:**
1. Create SwapRecord model if not exists (check `backend/app/models/`)
2. Implement `persist_swap_record()` method
3. Implement `update_schedule_assignments()` method
4. Implement `update_call_cascade()` method
5. Add database migration if needed
6. Add unit tests in `backend/tests/services/test_swap_executor.py`

**Non-Interference:** Isolated to swap executor service - no overlap with other workstreams

**Reference:** See `docs/IMPLEMENTATION_TRACKER.md` for implementation guidance

---

### Workstream 2: Stability Metrics TODOs
**Priority:** Medium | **Type:** Backend Feature

**Location:** `backend/app/analytics/stability_metrics.py`

**TODOs to Resolve:**
- Line 222: `# TODO: Implement version history lookup using SQLAlchemy-Continuum`
- Line 520: `# TODO: Integrate with app.scheduling.validator.ACGMEValidator`
- Line 544: `# TODO: Implement by querying schedule version history`

**Tasks:**
1. Implement SQLAlchemy-Continuum version history lookup
2. Integrate ACGME validator for compliance checking
3. Query schedule version history for analytics
4. Add unit tests in `backend/tests/analytics/test_stability_metrics.py`

**Non-Interference:** Isolated analytics module - no file overlap with other workstreams

---

### Workstream 3: Leave Routes FMIT Integration
**Priority:** Medium | **Type:** Backend Feature

**Location:** `backend/app/api/routes/leave.py`

**TODOs to Resolve:**
- Line 180: `# TODO: Check for FMIT conflicts when schedule data is available`
- Line 236: `# TODO: Trigger conflict detection in background`

**Tasks:**
1. Implement FMIT conflict checking function
2. Add Celery task for background conflict detection
3. Wire up the task trigger after leave approval
4. Add tests in `backend/tests/routes/test_leave_routes.py`

**Non-Interference:** Isolated to leave routes - no overlap with other route files

---

### Workstream 4: Portal Routes Enhancement
**Priority:** Low | **Type:** Backend Feature

**Location:** `backend/app/api/routes/portal.py`

**TODOs to Resolve:**
- Line 102: `has_conflict=False, # TODO: Could check conflict_alerts table`
- Line 306: `# TODO: Create notifications for candidates`

**Tasks:**
1. Add conflict_alerts table query for available weeks
2. Implement swap candidate notification creation
3. Add tests in `backend/tests/routes/test_portal_routes.py`

**Non-Interference:** Isolated to portal routes - no overlap with other workstreams

---

### Workstream 5: FMIT Week Verification
**Priority:** High | **Type:** Backend Feature

**Location:** `backend/app/services/swap_request_service.py`

**TODOs to Resolve:**
- Line 668: `# TODO: Implement proper FMIT week verification`

**Tasks:**
1. Implement `verify_fmit_week()` method
2. Query FMIT schedule data for validation
3. Integrate with swap eligibility checks
4. Add tests in `backend/tests/services/test_swap_request_service.py`

**Non-Interference:** Different service file from Workstream 1 (swap_executor vs swap_request_service)

---

### Workstream 6: Frontend Hooks Reorganization
**Priority:** Medium | **Type:** Frontend Refactoring

**Location:** `frontend/src/lib/hooks.ts` → `frontend/src/hooks/`

**Tasks:**
1. Create `frontend/src/hooks/` directory structure:
   ```
   hooks/
   ├── index.ts
   ├── useAuth.ts
   ├── useSchedule.ts
   ├── useSwaps.ts
   ├── usePeople.ts
   ├── useAbsences.ts
   ├── useCertifications.ts
   ├── useNotifications.ts
   ├── useAnalytics.ts
   └── useResilience.ts
   ```
2. Extract hooks by domain from `hooks.ts`
3. Update imports across components (find/replace)
4. Ensure React Query cache keys are preserved
5. Run existing tests to verify no regression

**Non-Interference:** Frontend-only, no backend changes

---

### Workstream 7: Frontend Feature Tests
**Priority:** Medium | **Type:** Frontend Testing

**Location:** `frontend/__tests__/features/` (new files)

**Untested Features:**
1. Procedure credentialing UI
2. Advanced filters in schedule view
3. Absence conflict detection UI
4. Resilience hub visualization
5. Export customization dialogs
6. Notification preferences UI
7. FMIT week detection UI
8. Swap marketplace auto-matching UI

**Tasks:**
1. Create test files for each untested feature
2. Use Jest + React Testing Library
3. Target 80% coverage for each feature
4. Add to CI/CD pipeline

**Non-Interference:** Creates new test files only - no production code changes

---

### Workstream 8: Constraints Module Refactoring
**Priority:** High | **Type:** Backend Refactoring

**Location:** `backend/app/scheduling/constraints.py` (~600+ lines)

**Tasks:**
1. Analyze current constraint definitions
2. Extract constraint groups into separate files:
   ```
   scheduling/constraints/
   ├── __init__.py
   ├── acgme_constraints.py
   ├── faculty_constraints.py
   ├── time_constraints.py
   ├── capacity_constraints.py
   └── custom_constraints.py
   ```
3. Create constraint registry/factory pattern
4. Update imports in `engine.py` and `solvers.py`
5. Maintain 100% test coverage during refactor

**Non-Interference:** Scheduling module is isolated from API routes and services

---

### Workstream 9: Documentation Consolidation
**Priority:** Low | **Type:** Documentation

**Locations:** `docs/`, `wiki/`

**Tasks:**
1. Audit all documentation files in `docs/` and `wiki/`
2. Create unified structure:
   ```
   docs/
   ├── README.md
   ├── getting-started/
   ├── architecture/
   ├── guides/
   ├── api/
   └── development/
   ```
3. Migrate wiki content to appropriate docs sections
4. Remove duplicate/outdated documentation
5. Add cross-references between related docs
6. Update main README.md with doc navigation

**Non-Interference:** Documentation only - no code changes

---

### Workstream 10: Playwright E2E Test Expansion
**Priority:** Low | **Type:** Frontend Testing

**Location:** `frontend/e2e/` (new test files)

**Test Scenarios to Add:**
1. Complete swap workflow (request → approval → execution)
2. Bulk import/export operations
3. Resilience framework interactions
4. Analytics dashboard interactions
5. Cross-browser testing (Chromium, Firefox, WebKit)
6. Mobile viewport testing

**Tasks:**
1. Create Page Object Model (POM) structure
2. Write E2E tests for each scenario
3. Add visual regression snapshots
4. Configure cross-browser matrix in CI

**Non-Interference:** E2E tests run against app, don't modify production code

---

## Dependency Matrix

| Workstream | Dependencies | Blocks |
|------------|--------------|--------|
| 1. Swap Executor | None | None |
| 2. Stability Metrics | None | None |
| 3. Leave Routes FMIT | None | None |
| 4. Portal Routes | None | None |
| 5. FMIT Verification | None | None |
| 6. Hooks Reorg | None | None |
| 7. Feature Tests | None | None |
| 8. Constraints Refactor | None | None |
| 9. Docs Consolidation | None | None |
| 10. E2E Tests | None | None |

**Conclusion:** All 10 workstreams are fully independent with zero file overlap.

---

## File Isolation Verification

| Workstream | Primary Files | Overlaps With |
|------------|---------------|---------------|
| 1 | `backend/app/services/swap_executor.py` | None |
| 2 | `backend/app/analytics/stability_metrics.py` | None |
| 3 | `backend/app/api/routes/leave.py` | None |
| 4 | `backend/app/api/routes/portal.py` | None |
| 5 | `backend/app/services/swap_request_service.py` | None |
| 6 | `frontend/src/lib/hooks.ts`, `frontend/src/hooks/` | None |
| 7 | `frontend/__tests__/features/*` (new) | None |
| 8 | `backend/app/scheduling/constraints.py` | None |
| 9 | `docs/`, `wiki/` | None |
| 10 | `frontend/e2e/*` (new) | None |

---

## Execution Order Recommendations

**Phase 1 - High Priority (Terminals 1-3):**
- Workstream 1: Swap Executor Implementation
- Workstream 5: FMIT Week Verification
- Workstream 8: Constraints Module Refactoring

**Phase 2 - Medium Priority (Terminals 4-7):**
- Workstream 2: Stability Metrics TODOs
- Workstream 3: Leave Routes FMIT Integration
- Workstream 6: Frontend Hooks Reorganization
- Workstream 7: Frontend Feature Tests

**Phase 3 - Low Priority (Terminals 8-10):**
- Workstream 4: Portal Routes Enhancement
- Workstream 9: Documentation Consolidation
- Workstream 10: Playwright E2E Test Expansion

---

## Terminal Assignment

```
Terminal 1:  Workstream 1 - Swap Executor Implementation
Terminal 2:  Workstream 2 - Stability Metrics TODOs
Terminal 3:  Workstream 3 - Leave Routes FMIT Integration
Terminal 4:  Workstream 4 - Portal Routes Enhancement
Terminal 5:  Workstream 5 - FMIT Week Verification
Terminal 6:  Workstream 6 - Frontend Hooks Reorganization
Terminal 7:  Workstream 7 - Frontend Feature Tests
Terminal 8:  Workstream 8 - Constraints Module Refactoring
Terminal 9:  Workstream 9 - Documentation Consolidation
Terminal 10: Workstream 10 - Playwright E2E Test Expansion
```

---

## Success Criteria

Each workstream should:
1. Resolve all identified TODOs in scope
2. Include appropriate unit/integration tests
3. Pass existing CI checks (lint, type-check, tests)
4. Update relevant documentation
5. Create atomic, reviewable commits

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Git conflicts | Each workstream on separate branch, merge sequentially |
| Test flakiness | Run tests in isolation before merging |
| Import cycles | Carefully manage cross-module imports |
| CI bottleneck | Stagger PR creation to avoid queue congestion |

---

*Generated for parallel execution planning*
*Last updated: 2025-12-18*
