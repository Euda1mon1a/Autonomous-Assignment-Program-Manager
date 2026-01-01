# CCW 1000-Task Burn Plan

> **Session:** claude/analyze-improve-repo-streams-DUeMr
> **Created:** 2025-12-31
> **Target:** 1000 tasks across 10 streams
> **Constraint:** No overlap with PR #578

---

## Executive Summary

Based on G-2 SEARCH_PARTY reconnaissance findings, this plan targets 1000 concrete improvements across 10 parallel streams. Each stream contains 100 actionable tasks derived from gap analysis.

---

## Files CCW Cannot Touch

- `backend/app/core/config.py`
- `backend/app/core/security.py`
- `backend/app/db/session.py`
- Any `.env` files
- Existing migrations

---

## Stream Overview

| Stream | Category | Gap Count | Priority |
|--------|----------|-----------|----------|
| 1 | Backend API Response Models | 150 endpoints | HIGH |
| 2 | Frontend Accessibility | 224 issues | HIGH |
| 3 | Test Coverage Expansion | 19+ gaps | HIGH |
| 4 | TypeScript Strict Mode | 75 issues | MEDIUM |
| 5 | Python Docstrings & Type Hints | 597 missing | MEDIUM |
| 6 | Error Handling | 84+ gaps | HIGH |
| 7 | API Documentation & OpenAPI | 150+ schemas | MEDIUM |
| 8 | Frontend Component Optimization | 80+ components | MEDIUM |
| 9 | MCP Tool Implementation | 13 files | HIGH |
| 10 | Code Quality & Linting | 100+ fixes | MEDIUM |

---

## Stream 1: Backend API Response Models (100 Tasks)

**Gap:** 150 endpoints missing `response_model` parameter

### Priority Files (0% Coverage)
1. `docs.py` - 11 endpoints
2. `profiling.py` - 10 endpoints
3. `conflicts.py` - 9 endpoints
4. `health.py` - 9 endpoints
5. `role_filter_example.py` - 9 endpoints
6. `sso.py` - 8 endpoints
7. `calendar.py` - 7 endpoints
8. `sessions.py` - 7 endpoints
9. `metrics.py` - 5 endpoints
10. `visualization.py` - 5 endpoints

### Task Breakdown
- Tasks 1-20: Create Pydantic schemas for `docs.py` + `profiling.py`
- Tasks 21-40: Create schemas for `conflicts.py` + `health.py`
- Tasks 41-60: Create schemas for `role_filter_example.py` + `sso.py`
- Tasks 61-80: Create schemas for `calendar.py` + `sessions.py`
- Tasks 81-100: Create schemas for `metrics.py` + `visualization.py` + extras

---

## Stream 2: Frontend Accessibility (100 Tasks)

**Gap:** 224 accessibility issues across 86 files

### Categories
- Form inputs without aria-label: 124 issues
- Interactive divs without role: 50 issues
- Interactive divs without tabIndex: 50 issues

### Priority Files
1. `app/admin/users/page.tsx` - 13 issues
2. `components/schedule/WeekView.tsx` - 10 issues
3. `features/templates/components/TemplateShareModal.tsx` - 8 issues
4. `features/conflicts/ManualOverrideModal.tsx` - 8 issues
5. `features/templates/components/TemplateEditor.tsx` - 7 issues
6. `app/settings/page.tsx` - 6 issues
7. `features/templates/components/TemplateLibrary.tsx` - 6 issues
8. `features/import-export/BulkImportModal.tsx` - 6 issues
9. `app/admin/audit/page.tsx` - 5 issues
10. `components/ExcelExportButton.tsx` - 5 issues

### Task Breakdown
- Tasks 1-25: Add aria-labels to form inputs (top 30 files)
- Tasks 26-50: Add role="button" to interactive divs
- Tasks 51-75: Add tabIndex to interactive elements
- Tasks 76-100: Add aria-describedby and keyboard handlers

---

## Stream 3: Test Coverage Expansion (100 Tasks)

**Gap:** 19 untested files + many edge cases

### Missing Tests
#### Frontend Components (8)
1. `fmit-timeline/TimelineControls.tsx`
2. `fmit-timeline/TimelineRow.tsx`
3. `fmit-timeline/FMITTimeline.tsx`
4. `conflicts/BatchResolution.tsx`
5. `conflicts/ManualOverrideModal.tsx`
6. `call-roster/CallRoster.tsx`
7. `call-roster/CallCalendarDay.tsx`
8. `holographic-hub/LayerControlPanel.tsx`

#### Backend Routes (11)
1. `admin_users.py`
2. `audience_tokens.py`
3. `block_scheduler.py`
4. `call_assignments.py`
5. `claude_chat.py`
6. `exotic_resilience.py`
7. `fatigue_risk.py`
8. `oauth2.py`
9. `qubo_templates.py`
10. `role_filter_example.py`
11. `ws.py`

### Task Breakdown
- Tasks 1-25: Write tests for 8 untested frontend components
- Tasks 26-60: Write tests for 11 untested backend routes
- Tasks 61-100: Add edge case tests for existing test files

---

## Stream 4: TypeScript Strict Mode (100 Tasks)

**Gap:** 75 type issues across frontend

### Categories
- `:any` type annotations: 17 occurrences
- `as any` casts: 18 occurrences
- Non-null assertions (!): 40 occurrences
- Missing return types: 180+ functions

### Priority Files
1. `utils/debounce.ts` - 8 issues
2. `hooks/useWebSocket.test.ts` - 7 issues
3. `components/schedule/__tests__/PersonFilter.test.tsx` - 7 issues
4. `features/voxel-schedule/__tests__/VoxelScheduleView.test.tsx` - 6 issues
5. `features/daily-manifest/LocationCard.tsx` - 4 issues

### Task Breakdown
- Tasks 1-25: Replace `:any` with proper types
- Tasks 26-50: Replace `as any` with proper type assertions
- Tasks 51-75: Replace non-null assertions with null checks
- Tasks 76-100: Add explicit return types to functions

---

## Stream 5: Python Docstrings & Type Hints (100 Tasks)

**Gap:** 597 missing docstrings across 105 files

### Priority Files (Services)
1. `conflict_alert_service.py` - 30 missing
2. `conflict_auto_resolver.py` - 25 missing
3. `swap_auto_matcher.py` - 16 missing
4. `faculty_preference_service.py` - 16 missing
5. `resilience/contingency.py` - 16 missing
6. `audit_service.py` - 15 missing
7. `xlsx_import.py` - 14 missing
8. `llm_router.py` - 13 missing
9. `conflict_auto_detector.py` - 12 missing
10. `constraints/acgme.py` - 12 missing

### Task Breakdown
- Tasks 1-30: Add docstrings to conflict services
- Tasks 31-50: Add docstrings to swap and faculty services
- Tasks 51-70: Add docstrings to audit and import services
- Tasks 71-90: Add docstrings to search and LLM services
- Tasks 91-100: Add docstrings to controllers

---

## Stream 6: Error Handling Improvements (100 Tasks)

**Gap:** 84+ bare except, 34+ information leakage

### Categories
- Bare `except Exception:`: 84 instances
- HTTPException with `str(e)` leakage: 34 instances
- Silent exception swallowing: 20+ instances
- Missing logging: 30+ instances

### Priority Files
1. `api/routes/search.py` - 16 issues
2. `api/routes/queue.py` - 8+ issues
3. `api/routes/fatigue_risk.py` - 6 issues
4. `api/routes/role_views.py` - 4 issues
5. `api/routes/features.py` - 4 issues
6. `resilience/hub_analysis.py` - 4 issues
7. `api/routes/conflicts.py` - 8 issues
8. `auth/oauth2_pkce.py` - 3 issues
9. `cache/cache_manager.py` - 15 issues
10. `rollback/manager.py` - 3 issues

### Task Breakdown
- Tasks 1-35: Fix HTTPException information leakage
- Tasks 36-60: Replace bare except with specific exceptions
- Tasks 61-80: Add logging to silent exception handlers
- Tasks 81-100: Add proper error recovery patterns

---

## Stream 7: API Documentation & OpenAPI (100 Tasks)

**Gap:** Missing response schemas, incomplete docs

### Focus Areas
- Create Pydantic response models for undocumented endpoints
- Add OpenAPI descriptions and examples
- Document request/response schemas
- Add API versioning documentation

### Task Breakdown
- Tasks 1-25: Create response schemas for health/metrics endpoints
- Tasks 26-50: Create response schemas for conflict/calendar endpoints
- Tasks 51-75: Add OpenAPI descriptions to existing endpoints
- Tasks 76-100: Add request/response examples

---

## Stream 8: Frontend Component Optimization (100 Tasks)

**Gap:** Performance and code quality improvements

### Focus Areas
- Add React.memo to pure components
- Add useMemo/useCallback where appropriate
- Optimize re-renders in list components
- Add loading states and error boundaries

### Priority Components
1. Schedule grid components
2. Template editor components
3. Resilience dashboard components
4. Conflict resolution components
5. Admin pages

### Task Breakdown
- Tasks 1-25: Add memoization to schedule components
- Tasks 26-50: Optimize template editor performance
- Tasks 51-75: Add loading/error states to features
- Tasks 76-100: Optimize admin page performance

---

## Stream 9: MCP Tool Implementation (100 Tasks)

**Gap:** 13 files with placeholder/mock data

### Placeholder Files
1. `var_risk_tools.py` - 3 placeholder functions
2. `immune_system_tools.py` - 3 placeholder functions
3. `thermodynamics_tools.py` - 4 placeholder functions
4. `scheduling_tools.py` - 2 placeholder functions
5. `hopfield_attractor_tools.py` - 4 placeholder functions
6. `composite_resilience_tools.py` - 4 placeholder functions
7. `time_crystal_tools.py` - 4 placeholder functions
8. `validate_schedule.py` - 1 placeholder function
9. `game_theory_tools.py` - 1 placeholder function
10. `deployment_tools.py` - 1 placeholder
11. `resilience_integration.py` - placeholder network
12. `server.py` - 1 TODO (Shapley)

### Task Breakdown
- Tasks 1-20: Implement var_risk backend API connections
- Tasks 21-40: Implement immune_system backend API connections
- Tasks 41-60: Implement thermodynamics backend API connections
- Tasks 61-80: Implement scheduling/hopfield backend API connections
- Tasks 81-100: Implement remaining tool backend connections

---

## Stream 10: Code Quality & Linting (100 Tasks)

**Gap:** Configuration differences and style issues

### Focus Areas
- Align line length (88 vs 100) across projects
- Fix remaining Ruff violations
- Fix ESLint warnings
- Standardize import ordering

### Task Breakdown
- Tasks 1-25: Fix Ruff E-series (style) violations
- Tasks 26-50: Fix Ruff F-series (logic) violations
- Tasks 51-75: Fix ESLint TypeScript warnings
- Tasks 76-100: Standardize code formatting

---

## Execution Strategy

### Parallel Execution
All 10 streams can execute in parallel since they target different file categories.

### Commit Strategy
- Commit every 10-20 tasks per stream
- Use descriptive commit messages: `fix(stream-N): description`
- Push incrementally to avoid large PRs

### Verification
- Run tests after each stream batch
- Verify no regressions with `pytest` and `npm test`
- Check linting passes before commit

---

## Progress Tracking

| Stream | Tasks | Completed | Status |
|--------|-------|-----------|--------|
| 1 | 100 | 0 | PENDING |
| 2 | 100 | 0 | PENDING |
| 3 | 100 | 0 | PENDING |
| 4 | 100 | 0 | PENDING |
| 5 | 100 | 0 | PENDING |
| 6 | 100 | 0 | PENDING |
| 7 | 100 | 0 | PENDING |
| 8 | 100 | 0 | PENDING |
| 9 | 100 | 0 | PENDING |
| 10 | 100 | 0 | PENDING |
| **TOTAL** | **1000** | **0** | **0%** |

---

*Plan generated from G-2 SEARCH_PARTY reconnaissance data*
