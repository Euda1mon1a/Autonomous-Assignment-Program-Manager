# Round 9: Project Status, Fixes, and Parallel Work Proposals

**Date**: December 15, 2024
**Current Progress**: ~75% complete
**After Round 9**: Target ~95% complete

---

## Project Status Summary

### What's Working Well

| Component | Status | Notes |
|-----------|--------|-------|
| **Backend API** | ✅ Complete | 40+ endpoints, FastAPI, full CRUD operations |
| **Database Layer** | ✅ Complete | PostgreSQL 15, SQLAlchemy 2.0, 8 core models |
| **Authentication** | ✅ Complete | JWT-based, bcrypt hashing, role-based access |
| **Scheduling Engine** | ✅ Complete | Greedy + CP-SAT solver (newly added) |
| **ACGME Validator** | ✅ Complete | 80-hour rule, 1-in-7 rule, supervision ratios |
| **React Query Hooks** | ✅ Complete | All CRUD hooks implemented with caching |
| **Frontend Pages** | ✅ 90% | Dashboard, Login, People, Templates, Absences, Compliance, Settings, Help |
| **Schedule View** | ⚠️ 70% | Grid view implemented, editing partially done |
| **Documentation** | ✅ Complete | 15+ markdown docs covering all aspects |

### What Needs Work

| Component | Status | Priority |
|-----------|--------|----------|
| **API Endpoint Bug** | 🔴 Critical | Double `/api` prefix in some hooks |
| **Frontend Tests** | 🔴 Critical | 77 files, 0 tests implemented |
| **Schedule Editing** | 🟡 High | QuickAssignMenu, EditAssignmentModal need polish |
| **Calendar Views** | 🟡 High | Day/Week/Month views incomplete |
| **E2E Tests** | 🟡 High | Playwright configured but no tests |
| **Console.log cleanup** | 🟢 Medium | 8 instances to replace with logger |
| **Security: Auth Tokens** | 🟢 Medium | localStorage → HttpOnly cookies |

---

## Recommended Fixes

### 🔴 CRITICAL: API Endpoint Double Prefix Bug

**Location**: `frontend/src/lib/hooks.ts`

**Problem**: The API client base URL ends with `/api`, but some hooks prepend `/api/` again.

```typescript
// api.ts line 10:
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

// hooks.ts - INCORRECT (double /api prefix):
get<ListResponse<Assignment>>(`/api/assignments?...`)  // Line 111
get<ListResponse<Person>>(`/api/people${queryString}`)  // Line 171
get<ListResponse<Absence>>(`/api/absences${params}`)    // Line 295
get<ListResponse<RotationTemplate>>('/api/rotation-templates') // Line 378

// hooks.ts - CORRECT (no prefix, uses baseURL):
get<Person>(`/people/${id}`)  // Line 187
get<RotationTemplate>(`/rotation-templates/${id}`)  // Line 393
```

**Fix**: Remove `/api` prefix from all hook endpoints that already include it:

| File | Line | Current | Should Be |
|------|------|---------|-----------|
| hooks.ts | 111 | `/api/assignments?...` | `/assignments?...` |
| hooks.ts | 171 | `/api/people...` | `/people...` |
| hooks.ts | 295 | `/api/absences...` | `/absences...` |
| hooks.ts | 378 | `/api/rotation-templates` | `/rotation-templates` |

---

### 🔴 CRITICAL: Missing Frontend Tests

**Current State**: Jest and React Testing Library configured, but `frontend/src/__tests__/` is empty.

**Required Tests** (minimum for core functionality):
1. `hooks.test.ts` - Test React Query hooks with MSW
2. `api.test.ts` - Test API client error handling
3. `components/AddPersonModal.test.tsx` - Form validation
4. `components/AddAbsenceModal.test.tsx` - Date validation
5. `components/ScheduleGrid.test.tsx` - Rendering with mock data
6. `pages/login.test.tsx` - Auth flow testing
7. `pages/schedule.test.tsx` - Schedule page interactions

---

### 🟡 HIGH: Console.log Cleanup

Replace with proper logging or remove:

| File | Line | Type | Action |
|------|------|------|--------|
| ErrorBoundary.tsx | 31-32 | `console.error` | Keep (error boundary should log) |
| export.ts | 152 | `console.error` | Replace with toast notification |
| ExcelExportButton.tsx | 44, 124 | `console.error` | Replace with toast notification |
| absences/page.tsx | 114 | `console.error` | Replace with toast notification |
| QuickAssignMenu.tsx | 306 | `console.error` | Replace with toast notification |
| QuickActions.tsx | 31 | `console.error` | Replace with toast notification |

---

### 🟡 HIGH: Schedule View Components Completion

**Already Implemented**:
- `ScheduleGrid.tsx` - Basic grid rendering
- `ScheduleCell.tsx` - Cell rendering with colors
- `BlockNavigation.tsx` - Date navigation
- `PersonFilter.tsx` - Person dropdown

**Need Completion**:
1. `EditAssignmentModal.tsx` - Click-to-edit with warnings
2. `QuickAssignMenu.tsx` - Right-click context menu (partially done)
3. `DayView.tsx` / `WeekView.tsx` / `MonthView.tsx` - Alternative views
4. `ViewToggle.tsx` - View switcher component

---

### 🟢 MEDIUM: Security Improvements

**Auth Token Storage**:
- Current: `localStorage.getItem('auth_token')`
- Recommended: HttpOnly cookies with CSRF protection
- Impact: Prevents XSS-based token theft

**Rate Limiting**:
- Not currently implemented in FastAPI
- Add via `slowapi` or custom middleware

---

## 5 Parallel Opus Terminal Proposals

Each terminal should work on a distinct, non-overlapping area to prevent merge conflicts.

---

### Terminal 1: Opus-APIFixes

**Priority**: CRITICAL
**Estimated Completion**: 30 minutes

**Mission**: Fix the API endpoint prefix bug and standardize all hook endpoints.

**Exclusive Files**:
- `frontend/src/lib/hooks.ts`
- `frontend/src/lib/api.ts` (if needed)

**Tasks**:
1. Audit all `get()`, `post()`, `put()`, `del()` calls in hooks.ts
2. Remove duplicate `/api` prefixes from all endpoints
3. Ensure consistency: all paths should NOT start with `/api` since baseURL includes it
4. Test each endpoint path is correct
5. Add JSDoc comments documenting the endpoint paths

**Prompt**:
```
You are Opus-APIFixes. Your mission is to fix the critical API endpoint bug in frontend/src/lib/hooks.ts.

CONTEXT: The API client in api.ts sets baseURL to 'http://localhost:8000/api'. This means all endpoints should NOT include '/api' prefix. However, some hooks incorrectly use '/api/...' causing double prefixing.

TASK:
1. Read frontend/src/lib/hooks.ts carefully
2. Find all instances where endpoints start with '/api/'
3. Remove the '/api' prefix from those endpoints (change '/api/people' to '/people')
4. Ensure all endpoints follow the same pattern (no /api prefix)
5. Run TypeScript check to ensure no compilation errors
6. Commit with message: "fix: Remove duplicate /api prefix from hook endpoints"
7. Push to your branch

DO NOT modify any other files. Only fix frontend/src/lib/hooks.ts.
```

---

### Terminal 2: Opus-FrontendTests

**Priority**: CRITICAL
**Estimated Completion**: 2 hours

**Mission**: Create foundational frontend test suite with MSW for API mocking.

**Exclusive Files**:
- `frontend/src/__tests__/*.test.ts(x)`
- `frontend/src/mocks/handlers.ts`
- `frontend/src/mocks/server.ts`
- `frontend/jest.setup.js` (if modifications needed)

**Tasks**:
1. Set up MSW (Mock Service Worker) handlers for all API endpoints
2. Create test utilities for rendering with React Query
3. Write tests for:
   - `hooks.test.ts` - usePeople, useSchedule, useAbsences
   - `api.test.ts` - Error handling, token attachment
   - `AddPersonModal.test.tsx` - Form validation
4. Ensure all tests pass

**Prompt**:
```
You are Opus-FrontendTests. Your mission is to create the foundational frontend test suite.

CONTEXT: The frontend has 77 TypeScript files but zero tests. Jest and React Testing Library are configured. We need MSW for API mocking.

YOUR EXCLUSIVE FILES (only modify these):
- frontend/src/__tests__/*.test.ts(x) (CREATE)
- frontend/src/mocks/handlers.ts (CREATE)
- frontend/src/mocks/server.ts (CREATE)
- frontend/jest.setup.js (MODIFY if needed)

TASKS:
1. Install MSW if not present: npm install -D msw
2. Create mocks/handlers.ts with handlers for: /people, /absences, /assignments, /rotation-templates, /schedule/generate, /schedule/validate
3. Create mocks/server.ts to set up the test server
4. Update jest.setup.js to start/stop MSW server
5. Create __tests__/hooks.test.ts testing usePeople, useAbsences hooks
6. Create __tests__/api.test.ts testing error transformation
7. Create __tests__/components/AddPersonModal.test.tsx testing form validation
8. Run tests to verify they pass

Commit: "test: Add frontend test infrastructure with MSW and initial tests"
Push to your branch.
```

---

### Terminal 3: Opus-ScheduleViews

**Priority**: HIGH
**Estimated Completion**: 1.5 hours

**Mission**: Complete the alternative calendar view components (Day, Week, Month).

**Exclusive Files**:
- `frontend/src/components/schedule/DayView.tsx` (CREATE)
- `frontend/src/components/schedule/WeekView.tsx` (CREATE)
- `frontend/src/components/schedule/MonthView.tsx` (CREATE)
- `frontend/src/components/schedule/ViewToggle.tsx` (CREATE if not exists)

**Tasks**:
1. Create ViewToggle component for switching views
2. Implement DayView with AM/PM sessions for all people
3. Implement WeekView with 7-day condensed grid
4. Implement MonthView calendar overview
5. Export all from schedule/index.ts

**Prompt**:
```
You are Opus-ScheduleViews. Your mission is to implement alternative calendar view components.

CONTEXT: The ScheduleGrid provides the main "Block" view (4-week grid). Users also need Day, Week, and Month views for different use cases. Round 8 prompts specify the requirements.

YOUR EXCLUSIVE FILES (only modify these):
- frontend/src/components/schedule/DayView.tsx (CREATE)
- frontend/src/components/schedule/WeekView.tsx (CREATE)
- frontend/src/components/schedule/MonthView.tsx (CREATE)
- frontend/src/components/schedule/ViewToggle.tsx (CREATE)

Read these files for context (DO NOT MODIFY):
- frontend/src/components/schedule/ScheduleGrid.tsx (understand existing patterns)
- frontend/src/lib/hooks.ts (understand data hooks)
- ROUND_8_SCHEDULE_VIEW_PROMPTS.md (requirements spec)

TASKS:
1. Create ViewToggle with buttons: Day | Week | Month | Block
2. Create DayView showing single day with all people in rows, AM/PM columns
3. Create WeekView showing 7 days with condensed cells
4. Create MonthView showing calendar grid with assignment counts per day
5. Use same color coding as ScheduleGrid (rotationColors)
6. Export all from frontend/src/components/schedule/index.ts

Commit: "feat: Add Day, Week, and Month calendar view components"
Push to your branch.
```

---

### Terminal 4: Opus-EditAssignment

**Priority**: HIGH
**Estimated Completion**: 1.5 hours

**Mission**: Complete the assignment editing modal with warnings system.

**Exclusive Files**:
- `frontend/src/components/schedule/EditAssignmentModal.tsx` (CREATE/COMPLETE)
- `frontend/src/components/schedule/AssignmentWarnings.tsx` (CREATE/COMPLETE)
- `frontend/src/components/ConfirmDialog.tsx` (MODIFY if needed for warnings)

**Tasks**:
1. Complete EditAssignmentModal with full functionality
2. Implement AssignmentWarnings with WARN-NOT-BLOCK philosophy
3. Add confirmation checkbox for critical warnings
4. Wire up useUpdateAssignment and useDeleteAssignment hooks
5. Handle optimistic updates with rollback on error

**Prompt**:
```
You are Opus-EditAssignment. Your mission is to complete the assignment editing functionality.

CONTEXT: Admins need to edit assignments directly on the schedule. The system should WARN but NOT BLOCK - special circumstances come up and humans need final authority. Round 8 prompts specify requirements.

YOUR EXCLUSIVE FILES (only modify these):
- frontend/src/components/schedule/EditAssignmentModal.tsx (CREATE/COMPLETE)
- frontend/src/components/schedule/AssignmentWarnings.tsx (CREATE/COMPLETE)
- frontend/src/components/ConfirmDialog.tsx (MODIFY if needed)

Read these files for context:
- frontend/src/lib/hooks.ts (useUpdateAssignment, useDeleteAssignment, useAbsences)
- frontend/src/components/schedule/ScheduleCell.tsx (understand click handler)
- ROUND_8_SCHEDULE_VIEW_PROMPTS.md (Section 2: Opus-ScheduleEdit)

TASKS:
1. EditAssignmentModal:
   - Header showing person name, date, session
   - Rotation template dropdown
   - Notes field for override reason
   - Delete button (if editing existing)
   - Save button that calls useUpdateAssignment or useCreateAssignment
2. AssignmentWarnings:
   - Check if person is absent on date
   - Display warnings with severity (info, warning, critical)
   - Require acknowledgment checkbox for critical warnings
3. Wire up to ScheduleCell onClick (via callback prop)

Commit: "feat: Complete assignment editing modal with warnings system"
Push to your branch.
```

---

### Terminal 5: Opus-E2ETests

**Priority**: HIGH
**Estimated Completion**: 2 hours

**Mission**: Create Playwright E2E tests for critical user journeys.

**Exclusive Files**:
- `frontend/e2e/*.spec.ts` (CREATE)
- `frontend/playwright.config.ts` (MODIFY if needed)

**Tasks**:
1. Configure Playwright for the project
2. Create E2E tests for:
   - Login flow
   - View schedule page
   - Add a person
   - Add an absence
   - Generate schedule
3. Add CI-friendly test script

**Prompt**:
```
You are Opus-E2ETests. Your mission is to create Playwright E2E tests for critical user flows.

CONTEXT: Playwright is configured but no E2E tests exist. We need tests for the main user journeys to prevent regressions.

YOUR EXCLUSIVE FILES (only modify these):
- frontend/e2e/*.spec.ts (CREATE)
- frontend/playwright.config.ts (MODIFY if needed)
- frontend/package.json (add test scripts if needed)

TASKS:
1. Review playwright.config.ts and ensure it's configured correctly
2. Create e2e/auth.spec.ts:
   - Test login with valid credentials
   - Test login with invalid credentials
   - Test logout
3. Create e2e/schedule.spec.ts:
   - Test viewing schedule page
   - Test navigating between blocks
4. Create e2e/people.spec.ts:
   - Test viewing people list
   - Test adding a new person
   - Test editing a person
5. Create e2e/absences.spec.ts:
   - Test adding an absence
   - Test viewing absence calendar
6. Add npm script: "test:e2e": "playwright test"

Commit: "test: Add Playwright E2E tests for critical user journeys"
Push to your branch.
```

---

## Coordination Summary

### File Ownership Matrix

| Terminal | Exclusive Files |
|----------|----------------|
| Opus-APIFixes | `hooks.ts`, `api.ts` |
| Opus-FrontendTests | `__tests__/*`, `mocks/*`, `jest.setup.js` |
| Opus-ScheduleViews | `DayView.tsx`, `WeekView.tsx`, `MonthView.tsx`, `ViewToggle.tsx` |
| Opus-EditAssignment | `EditAssignmentModal.tsx`, `AssignmentWarnings.tsx`, `ConfirmDialog.tsx` |
| Opus-E2ETests | `e2e/*`, `playwright.config.ts` |

### Merge Order

1. **Opus-APIFixes** first (critical bug fix, small change)
2. **Opus-FrontendTests** second (creates test infrastructure)
3. **Opus-ScheduleViews** and **Opus-EditAssignment** in parallel (no overlap)
4. **Opus-E2ETests** last (may depend on UI changes)

### After Round 9 Completion

**Expected State**: ~95% complete

| Component | Before | After |
|-----------|--------|-------|
| API Bug | 🔴 Broken | ✅ Fixed |
| Frontend Tests | 0% | 60% |
| Schedule Views | 70% | 100% |
| E2E Tests | 0% | 40% |

### Remaining for Round 10 (~5%)

1. Mobile-specific optimizations
2. Performance tuning for large schedules (100+ residents)
3. Print-friendly schedule export
4. Advanced analytics dashboard
5. Bulk import/export features

---

## Quick Start Commands

### Launch All 5 Terminals

```bash
# Terminal 1 - APIFixes
claude --branch claude/opus-api-fixes-$(date +%s)

# Terminal 2 - FrontendTests
claude --branch claude/opus-frontend-tests-$(date +%s)

# Terminal 3 - ScheduleViews
claude --branch claude/opus-schedule-views-$(date +%s)

# Terminal 4 - EditAssignment
claude --branch claude/opus-edit-assignment-$(date +%s)

# Terminal 5 - E2ETests
claude --branch claude/opus-e2e-tests-$(date +%s)
```

---

*Generated by Claude Opus 4.5 - December 15, 2024*
