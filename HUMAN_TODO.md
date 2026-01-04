# Human TODO

> Tasks that require human action (external accounts, manual configuration, etc.)

---

## Priority: Import/Export Staging DB (2026-01-01)

**Status:** ✅ COMPLETE (verified 2026-01-04)
**Context:** Full round-trip import workflow implemented and deployed.

### Implementation Summary

All 6 required components are FULLY IMPLEMENTED:

| Component | Location | Status |
|-----------|----------|--------|
| **Model** | `backend/app/models/import_staging.py` | ✅ Complete |
| **Schema** | `backend/app/schemas/import_staging.py` | ✅ Complete |
| **Service** | `backend/app/services/import_staging_service.py` | ✅ Complete |
| **Routes** | `backend/app/api/routes/import_staging.py` | ✅ Complete (6 endpoints) |
| **Migration** | `backend/alembic/versions/20260101_import_staging_tables.py` | ✅ Complete |
| **Frontend** | Wired to routes | ✅ Complete |

### Endpoints Implemented
- [x] POST `/import/stage` - Parse Excel and stage (no commit)
- [x] GET `/import/batches` - List staged batches
- [x] GET `/import/batches/{id}/preview` - Show staged vs existing
- [x] POST `/import/batches/{id}/apply` - Commit staged to live
- [x] POST `/import/batches/{id}/rollback` - Undo applied batch
- [x] DELETE `/import/batches/{id}` - Remove batch

### Conflict Resolution Modes
| Mode | Behavior | Status |
|------|----------|--------|
| Replace | Delete block assignments, insert staged | ✅ Implemented |
| Merge | Keep existing, add new, skip conflicts | ✅ Implemented |
| Upsert | Update if person+date+slot exists, else insert | ✅ Implemented |

**Verification:** Database migration runs on startup, all 6 endpoints tested and functional, round-trip workflow: Export → Edit → Re-import now fully operational.

---

## Post-Rebuild Fixes (2026-01-02)

**Context:** After Session 052 infrastructure rebuild, several items need attention.

### 1. Re-enable Alembic Migrations in docker-entrypoint.sh
**Priority:** High
**Status:** DONE (verified 2026-01-03)

~~Migrations were commented out during rebuild to prevent issues.~~

**Verified:** `alembic upgrade head` is ACTIVE at line 22 of `backend/docker-entrypoint.sh`.
The migration runs on every container startup as intended.

```bash
# From backend/docker-entrypoint.sh:22
alembic upgrade head
```

**No action required** - this was a phantom task.

### 2. Fix Misleading "/mcp not authenticated" Display
**Priority:** Low
**Status:** TODO

The `/mcp` command shows "not authenticated" even when tools work fine. This is because:
- Claude Code checks `api_key_configured` in MCP health response
- `MCP_API_KEY` is optional (for external clients), not required for tool operation
- Backend JWT auth (`API_USERNAME`/`API_PASSWORD`) is what actually matters

**Options:**
1. Set a dummy `MCP_API_KEY` env var to make display show "authenticated"
2. Update MCP health endpoint to report auth based on backend JWT capability
3. Document that "not authenticated" is cosmetic when tools work

**Impact:** Confusing for operators, but tools function correctly.

---

## Completed (2025-12-25)

### 1. Block 10 Schedule Generation - COMPLETE ✅
**Priority:** High
**Context:** Block 10 fully working as of 2025-12-25

- [x] Run schedule generation with Docker backend (87 assignments, 112.5% coverage)
- [x] Verify assignments distributed across clinic templates
- [x] All 25 constraints active and working
- [x] 0 violations

**Verified:** See `docs/development/SESSION_HANDOFF_20251225.md` for details

### 2. Complete MCP Wiring - DONE
**Priority:** Medium
**Context:** PR #402 wired 3/5 tools, 2 remaining - **FIXED 2025-12-24**

| Tool | Issue | Fix Applied |
|------|-------|-------------|
| `analyze_swap_candidates` | Backend required file upload | Created `/schedule/swaps/candidates` JSON endpoint |
| `run_contingency_analysis` | Different response structure | Added response mapping in `resilience_integration.py` |

**Files Changed:**
- `backend/app/api/routes/schedule.py` - Added JSON-based swap candidates endpoint
- `backend/app/schemas/schedule.py` - Added new request/response schemas
- `mcp-server/src/scheduler_mcp/tools.py` - Wired to backend, kept mock as fallback
- `mcp-server/src/scheduler_mcp/api_client.py` - Updated to call new endpoint
- `mcp-server/src/scheduler_mcp/resilience_integration.py` - Added backend response mapping

### 3. PuLP Solver Template Balance - DONE
**Priority:** Low
**Context:** Only fixed greedy + CP-SAT, PuLP may have same issue - **FIXED 2025-12-24**

- [x] Check if PuLP solver has template concentration bug ✅
- [x] Apply same fix pattern if needed (select template with fewest assignments) ✅

**Fix Applied:** Added template balance penalty to PuLP solver objective function, matching CP-SAT pattern

### 4. Optional: Add `solver_managed` Flag
**Priority:** Low (nice-to-have)
**Context:** Cleaner than filtering by `activity_type`

- [ ] Add `solver_managed: bool` to RotationTemplate model
- [ ] Create Alembic migration
- [ ] Update `_get_rotation_templates()` to use flag

---

## Feature Requests - Pending Investigation

### ACGME Rest Hours - PGY-Level Differentiation
**Priority:** Medium
**Added:** 2025-12-30
**Status:** Awaiting PF discussion

**Issue:** MEDCOM analysis identified that ACGME rest hours should be PGY-level dependent:

| PGY Level | ACGME Requirement | Current Code |
|-----------|------------------|--------------|
| PGY-1 | 10 hours ("should have" - recommended) | 8 hours |
| PGY-2+ | 8 hours ("must have" - required) | 8 hours ✓ |

**Current implementation:** Single constant `ACGME_MIN_REST_BETWEEN_SHIFTS = 8.0` in `backend/app/resilience/frms/frms_service.py:181`

**Questions for PF:**
- [ ] Should PGY-1 residents be held to the stricter 10-hour recommendation?
- [ ] Is 8 hours acceptable as floor for all levels (technically compliant)?
- [ ] Are there program-specific policies that override ACGME minimums?

**If approved for implementation:**
```python
ACGME_MIN_REST_PGY1 = 10.0      # ACGME "should have"
ACGME_MIN_REST_PGY2_PLUS = 8.0  # ACGME "must have"
```

**Files to update:**
- `backend/app/resilience/frms/frms_service.py` (constraint definition)
- `docs/rag-knowledge/acgme-rules.md` (documentation)
- `backend/app/prompts/scheduling_assistant.py` (AI guidance)

---

### Resident Call Types
**Priority:** Medium
**Added:** 2025-12-26
**Status:** Awaiting resident input

Two new resident call types need to be captured in the scheduling system:

| Call Type | Full Name | Status | Notes |
|-----------|-----------|--------|-------|
| **Resident NF Call** | Night Float Call (?) | Needs definition | Investigate with residents |
| **Resident LND Call** | Labor and Delivery Call (?) | Needs definition | Investigate with residents |

**Questions to clarify with residents:**
- [ ] What are the exact duties/responsibilities for each call type?
- [ ] What are the shift times (start/end)?
- [ ] Which PGY levels are eligible for each?
- [ ] Are there supervision requirements?
- [ ] How do these interact with ACGME work hour limits?
- [ ] Are there specific days/rotations when these apply?
- [ ] How do these relate to existing NF (Night Float) assignments?

**Implementation considerations (once defined):**
- Add to `RotationTemplate` or as separate assignment types
- Create scheduling constraints
- Update ACGME compliance checks if needed
- Add to solver if applicable

---

## Process Improvements (2026-01-01)

### CCW Burn Quality Protocol - ✅ COMPLETE
**Priority:** High → IMPLEMENTED
**Added:** 2026-01-01 (Session 047)
**Implemented:** 2026-01-04 (Session TOOLSMITH enhancement)
**Status:** Protocol fully documented and operational

**Protocol Location:** `.claude/protocols/CCW_BURN_PROTOCOL.md` (217 lines)

**Completed Action Items:**
- [x] Created formal CCW_BURN_PROTOCOL.md with pre-merge gates
- [x] Analyzed common error patterns from past burns
- [x] Added automated detection for known CCW error signatures
- [x] Established "quarantine" branch naming convention (`ccw/burn-*`)
- [x] Required stack audit GREEN before merging CCW burns
- [x] Added rollback procedures (3 options: revert, reset, cherry-pick)

**Protocol Sections:**
1. Executive Summary - CCW validation gap context
2. The Core Problem - Feedback loop visualization
3. Burn Execution Protocol - Phase 1 & 2 with gates
4. Common CCW Failure Patterns - Error catalog with detection
5. CCW Task Constraints - Constraints to include in prompts
6. Pre-Merge Quality Gates - Decontamination checklist
7. Rollback Procedure - 3 recovery strategies
8. Quick Reference - All stages summarized

**See Also:**
- `.claude/Scratchpad/CCW_BURN_POSTMORTEM.md` - Historical postmortem
- `.claude/scripts/ccw-validation-gate.sh` - Validation script
- `/stack-audit` skill - Required pre-merge check

---

## UI/UX Improvements (2025-12-26)

> Findings from Comet Assistant GUI exploration session

### 1. Schedule Grid - Frozen Headers/Columns
**Priority:** High
**Page:** `/schedule` (Block View)
**Status:** ✅ COMPLETE (Session 012, 2025-12-28)

**Issues:**
- [x] Top header row (dates) disappears when scrolling vertically through residents
- [x] First column (resident name/PGY) disappears when scrolling horizontally

**Implementation:**
```css
/* Sticky header row */
th { position: sticky; top: 0; background-color: ...; z-index: 1; }

/* Sticky first column */
td:first-child, th:first-child { position: sticky; left: 0; z-index: 2; }
```

**Files Modified:**
- `frontend/src/components/schedule/ScheduleHeader.tsx` - Added sticky positioning
- `frontend/src/components/schedule/ScheduleGrid.tsx` - Applied z-index hierarchy
- `frontend/src/app/globals.css` - Enhanced scroll container styling

**Additional UX suggestions:**
- Add subtle row/column hover highlight for scanning dense schedules
- Ensure scroll container is on grid (not whole page)

---

### 2. Heatmap Page - Add Block Navigation
**Priority:** High
**Page:** `/heatmap`
**Status:** ✅ COMPLETE (Session 012, 2025-12-28)

**Current state:** Only manual date pickers (From/To)

**Requested:** Match Schedule page block navigation pattern:
```
[◀ Previous Block] [Next Block ▶] [Today] [This Block] Block: [Mar 12 - Apr 8, 2026]
```

**Implemented layout:**
```
[◀ Prev] [Next ▶] [Today] [This Block] Block: [Date Range]
From: [date] To: [date] Group by: [dropdown] ☑ Include FMIT [Filters]
```

**Benefits:**
- Consistency with Schedule page UX
- One-click block selection vs manual date entry
- Quick navigation through 730 blocks

**File Modified:**
- `frontend/src/components/heatmap/HeatmapControls.tsx` - Added Previous/Next/Today/This Block buttons

---

### 3. Heatmap Backend Bug - group_by Validation - FIXED
**Priority:** Medium
**Page:** `/heatmap`
**Status:** FIXED (PR #512)

**Issue:** Backend rejects "Daily" and "Weekly" `group_by` values, only accepts "person" or "rotation"

**Resolution (PR #512):**
- Added `_generate_daily_heatmap()` and `_generate_weekly_heatmap()` helper methods
- Extended group_by validation to accept 'daily' and 'weekly' values (case-insensitive)
- Updated GET /heatmap, POST /heatmap/unified, GET /heatmap/image endpoints
- Added 28 new tests (22 route-level, 6 service-level)

---

### 4. Daily Manifest - Empty State UX
**Priority:** Medium
**Page:** `/daily-manifest`
**Status:** COMPLETE (Session 012, 2025-12-28)

**Issues fixed:**
- [x] Improved error messaging with context-aware messages (network error vs service unavailable)
- [x] Empty state now shows date-specific message with helpful guidance
- [x] Added info box with actionable suggestions ("What you can do" list)
- [x] Quick action buttons: "Go to Today" and "View All Day"
- [x] Search empty state: Shows search term and "Clear Search" button
- [ ] Date picker data availability indicator (deferred - requires backend endpoint)

**Files Modified:**
- `frontend/src/features/daily-manifest/DailyManifest.tsx`

**Changes:**
1. Error state now distinguishes between 404, network errors, and other errors with appropriate messaging
2. Empty state (no locations) shows:
   - CalendarX icon with date-specific heading
   - Context-aware message (morning/afternoon/all day)
   - Blue info box with helpful suggestions
   - Quick action buttons to navigate to today or view all day
3. Search empty state shows the search query and provides a "Clear Search" button

---

## Slack Integration Setup

- [ ] **Test Slack Webhook Connection**
  - Workspace: (obtain invite link from team lead - do not commit to repo)
  - Create an Incoming Webhook in the workspace
  - Test with a simple curl command
  - Add `SLACK_WEBHOOK_URL` to `monitoring/.env`

- [ ] **Set Up Slack App for ChatOps** (optional, for slash commands)
  - Create Slack App at https://api.slack.com/apps
  - Add slash command `/scheduler`
  - Add Bot Token Scopes: `chat:write`, `commands`, `users:read`
  - Install app to workspace
  - Copy Bot User OAuth Token for n8n

- [ ] **Create Slack Channels for Alerts**
  - `#alerts-critical`
  - `#alerts-warning`
  - `#alerts-database`
  - `#alerts-infrastructure`
  - `#residency-scheduler`
  - `#compliance-alerts`

---

## Documentation Cleanup

- [x] **Move CELERY_PRODUCTION_CHECKLIST.md out of archived** ✅ Completed 2025-12-21
  - Moved to: `docs/deployment/CELERY_PRODUCTION_CHECKLIST.md`
  - Reason: Contains pending production tasks (email implementation, SMTP config, monitoring)
  - Per archived/README.md, active checklists should not be archived

---

## Other Pending Tasks

### Backend Fix: Faculty Assignments Missing rotation_template_id - FIXED

**Priority:** Medium
**Found:** Session 14 (2025-12-22)
**Fixed:** Session 14 (2025-12-23) - Commit e88a63b
**Status:** RESOLVED

**Original Issue:** Faculty-Inpatient Year View showed all zeros because faculty assignments were created without `rotation_template_id`.

**Fix Applied:**
- Added `_get_primary_template_for_block()` method to determine rotation template from resident assignments
- Faculty supervisors now receive the same `rotation_template_id` as the residents they supervise
- Tests added: `test_faculty_receives_rotation_template_id()` and `test_faculty_template_matches_resident_template()`

**Current Database State (verified 2025-12-28):**
```
   type   | total_assignments | with_template | without_template
----------+-------------------+---------------+------------------
 faculty  |               430 |           430 |                0
 resident |              3592 |          3592 |                0
```

**Files Modified:**
- `backend/app/scheduling/engine.py` - Added `_get_primary_template_for_block()` and updated `_assign_faculty()`
- `backend/tests/test_scheduling_engine.py` - Added faculty template tests

---

### Solver Template Distribution Bugs - FIXED & VERIFIED

**Priority:** High
**Found:** Session review (2025-12-24)
**Fixed:** 2025-12-24
**Verified:** Session 015 (2025-12-29) - All 4 solvers operational
**Location:** `backend/app/scheduling/solvers.py`, `backend/app/scheduling/engine.py`

**Issue:** Both greedy and CP-SAT solvers were assigning all residents to the same rotation.

**Three bugs fixed:**

1. [x] **Greedy Solver:** Now selects template with fewest total assignments for even distribution
2. [x] **CP-SAT Solver:** Added `template_balance_penalty` to objective function
3. [x] **Template Filtering:** `_get_rotation_templates()` now defaults to `activity_type="outpatient"`
   - **NOTE (2025-12-26):** Previous fix incorrectly used `"clinic"` instead of `"outpatient"`.
     PR #442 was not merged due to this issue being caught during evaluation.
     The solver is for outpatient half-day optimization, so the filter must match `"outpatient"`
     activity_type (electives/selectives), not `"clinic"` (FM Clinic only).

**Architecture Note:**
- Block-assigned rotations (FMIT, NF, inpatient) are pre-assigned and shouldn't go to solver
- Solvers are for outpatient half-day optimization only
- Templates now filtered to `activity_type == "outpatient"` by default
- `"clinic"` is a separate activity_type for FM Clinic with its own capacity/supervision constraints

**Session 015 Verification Results (2025-12-29):**

| Solver | Tests | Status | Balance Verified |
|--------|-------|--------|------------------|
| **Greedy** | 7/7 pass | Operational | 7,7,6 distribution |
| **CP-SAT** | 4/4 pass | Operational | 9,9 distribution |
| **PuLP** | 5/5 pass | Operational | 9,9 distribution |
| **Hybrid** | 5/5 pass | Operational | Fallback chain working |

**Test Coverage Gap - FIXED (2026-01-04):**
- ~~No explicit balance behavior tests exist~~ RESOLVED
- ~~Balance is verified implicitly through assignment distribution~~ RESOLVED
- ~~Recommendation: Add dedicated `test_template_balance_*` tests~~ RESOLVED

**Implementation:** Added `TestTemplateBalance` class with 5 dedicated tests:
- `test_template_balance_greedy` - Verifies GreedySolver distributes across templates
- `test_template_balance_cpsat` - Verifies CPSATSolver distributes across templates
- `test_template_balance_pulp` - Verifies PuLPSolver distributes across templates
- `test_template_balance_hybrid` - Verifies HybridSolver distributes across templates
- `test_template_balance_no_concentration` - Ensures no template exceeds 60% of assignments

**Location:** `backend/tests/test_solvers.py` (lines 517-733)

---

### NF Half-Block Documentation Consistency - VERIFIED

**Priority:** Medium
**Found:** Session review (2025-12-24)
**Verified:** 2025-12-24

**Issue:** Night Float (NF) half-block mirrored pairing pattern is documented in multiple places.

**Audit completed - Documentation is CONSISTENT across all locations:**

| Location | Status | Notes |
|----------|--------|-------|
| `docs/development/CODEX_SYSTEM_OVERVIEW.md` | Consistent | Most comprehensive, has PC rules |
| `backend/app/scheduling/constraints/night_float_post_call.py` | Consistent | Implementation matches docs |
| `.claude/skills/schedule-optimization/SKILL.md` | Consistent | Cross-references other files |

**Verified consistent terminology:**
- [x] "block-half" used everywhere (not "half-block")
- [x] Day 15 as transition point between half 1 and half 2
- [x] PC = full day (AM + PM blocked)
- [x] NF in half 1 → Day 15 = PC; NF in half 2 → Day 1 next block = PC
- [x] Mirrored pairing pattern documented identically

---

## Cleanup Session Report (2025-12-21 Overnight)

### Completed Autonomously

- [x] Moved `CELERY_PRODUCTION_CHECKLIST.md` from archived to `docs/deployment/`
- [x] Renamed session 11 docs to avoid confusion:
  - `SESSION_011_PARALLEL_HIGH_YIELD_TODOS.md` → `SESSION_11A_MCP_AND_OPTIMIZATION.md`
  - `SESSION_11_PARALLEL_HIGH_YIELD_TODOS.md` → `SESSION_11B_TEST_COVERAGE.md`
- [x] Updated all cross-references in docs/sessions/README.md, docs/README.md, CHANGELOG.md
- [x] Verified .gitignore is properly configured (no committed secrets/artifacts)

### Broken Documentation Links - FIXED
**Status:** RESOLVED (verified 2026-01-04)

~~The following links in `README.md` point to non-existent files:~~

| Original Broken Link | Fixed To | Status |
|---------------------|----------|--------|
| ~~`docs/api/endpoints/credentials.md`~~ | `docs/api/authentication.md` (line 113) | FIXED |
| ~~`docs/SETUP.md`~~ | `docs/getting-started/installation.md` (line 298) | FIXED |
| ~~`docs/API_REFERENCE.md`~~ | `docs/api/index.md` (line 426, 530) | FIXED |

**Verification:** All README.md links now point to existing documentation files. The fixes were applied in a previous session but this TODO was not updated.

### Big Ideas (Deferred for Morning Review)

1. **Linting Enforcement**: Ruff is configured in `pyproject.toml` but not run in CI. Consider adding `ruff check --fix` to pre-commit or CI.

2. **Session Naming Convention**: Sessions 7-9 are in `docs/archived/sessions/` while 10+ are in `docs/sessions/`. Consider consolidating.

3. **Remaining Backend TODOs (from TODO_TRACKER.md)**:
   - Portal Dashboard Data (`portal.py:863`) - Faculty dashboard returns stub data
   - MCP Sampling Call (`agent_server.py:263`) - Placeholder LLM response
   - Server Cleanup Logic (`server.py:1121`) - DB connection cleanup on shutdown

### Skipped (Too Invasive for Rest Mode)

- Automated unused import cleanup (would require code changes)
- Large refactoring or architectural changes

---

---

## Full-Stack MVP Review Findings (2025-12-30)

> Comprehensive 16-layer inspection conducted. See `docs/planning/MVP_STATUS_REPORT.md` for full details.

### 🔴 CRITICAL - Fix Before Launch

#### 1. Celery Worker Missing Queues - ✅ RESOLVED
**Priority:** CRITICAL → RESOLVED
**Location:** `docker-compose.yml` (celery-worker service)
**Verified:** 2025-12-30 (Session 023)

The celery worker command already includes all 6 queues:
```yaml
command: celery -A app.core.celery_app worker --loglevel=info -Q default,resilience,notifications,metrics,exports,security
```

#### 2. Security TODOs in audience_tokens.py - ✅ RESOLVED
**Priority:** CRITICAL → RESOLVED
**Location:** `/backend/app/api/routes/audience_tokens.py`
**Verified:** 2025-12-30 (Session 023)

Both security controls are fully implemented:
- **Role-based restrictions:** `ROLE_LEVELS` (L59-68), `AUDIENCE_REQUIREMENTS` (L72-86), `check_audience_permission()` (L102-139)
- **Token ownership:** Multi-method verification (decode L349-384, blacklist L386-388), admin bypass (L391-424)

### 🟡 HIGH PRIORITY - Fix This Week

#### 3. Frontend Environment Variable Mismatch - ✅ RESOLVED
**Priority:** HIGH → RESOLVED
**Location:** `/frontend/src/hooks/useClaudeChat.ts`
**Verified:** 2025-12-30 (G2_RECON audit)

- ✅ Now uses `NEXT_PUBLIC_API_URL` correctly (Next.js style)
- ✅ All frontend hooks standardized to Next.js environment variable convention

#### 4. Missing Database Indexes - ✅ RESOLVED
**Priority:** HIGH → RESOLVED
**Location:** Database migrations
**Verified:** 2025-12-30 (G2_RECON audit)

- ✅ Added in migration `12b3fa4f11ec` (2025-12-21): `idx_block_date`, `idx_assignment_person_id`, `idx_assignment_block_id`
- ✅ Additional indexes added in migration `20251230_add_critical_indexes`: composite indexes for performance optimization

#### 5. Admin Users Page API - ✅ RESOLVED
**Priority:** HIGH → RESOLVED
**Location:** `/frontend/src/app/admin/users/page.tsx`, `/frontend/src/hooks/useAdminUsers.ts`
**Verified:** 2026-01-04 (Session G2_RECON verification)

**Status: FULLY WIRED AND OPERATIONAL**

All 8 API hooks fully wired to 8 backend endpoints:
- ✅ `useUsers()` - GET /admin/users with filters/pagination
- ✅ `useUser()` - GET /admin/users/{id} single user
- ✅ `useCreateUser()` - POST /admin/users
- ✅ `useUpdateUser()` - PATCH /admin/users/{id}
- ✅ `useDeleteUser()` - DELETE /admin/users/{id}
- ✅ `useToggleUserLock()` - POST /admin/users/{id}/lock
- ✅ `useResendInvite()` - POST /admin/users/{id}/resend-invite
- ✅ `useBulkUserAction()` - POST /admin/users/bulk

**Features Operational:** User CRUD, account locking, invitation management, bulk operations, activity audit log
**Previous concern:** Task was added when hooks were stubs; implementation completed but TODO not removed

#### 6. Resilience API Response Models - 85% COMPLETE
**Location:** `/backend/app/api/routes/resilience.py`
- 46/54 endpoints now have `response_model` defined (85% coverage, up from 22%)
- Remaining 8 endpoints return complex nested structures pending schema refactoring
- **Impact:** Significantly improved OpenAPI documentation, response consistency

#### 7. CD Pipeline - Deployment Logic Placeholder-Only
**Priority:** HIGH → RESOLVED
**Location:** `.github/workflows/cd.yml`
**Found:** G2_RECON audit (2025-12-30)
**Status:** ✅ FIXED (Session 025, 2025-12-30)

- ~~`deploy` job exists but contains only placeholder comments~~
- ~~No actual deployment logic (no kubectl, no helm, no container registry push)~~
- ~~CI passes but no automated deployment to staging/production~~
- ~~**Impact:** Manual deployment required, no CD automation~~

**Resolution (Session 025):**
- Implemented full deployment pipeline with container registry push
- Added staging and production deployment stages
- Integrated with existing CI workflow

#### 8. MCP Server Production Config - ✅ FIXED
**Priority:** HIGH → RESOLVED
**Location:** `docker-compose.prod.yml`
**Found:** G2_RECON audit (2025-12-30)
**Fixed:** 2026-01-04 (Session ARCHITECT verification)

**Status: FULLY CONFIGURED AND VALIDATED**

MCP server was present in prod config but had critical errors preventing functionality:

**Issues Fixed:**
- ✅ Transport mode: `streamable-http` → `http` (invalid transport corrected)
- ✅ Port binding: Added `127.0.0.1:8080:8080` (was missing, tools inaccessible)
- ✅ Security config: Removed duplicate `security_opt` (caused validation error)
- ✅ Celery worker: Fixed `container_name` + `replicas` conflict

**Configuration Verified:**
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml config --quiet
# Returns: SUCCESS (no errors)
```

**29+ MCP tools now available in production** with proper security (localhost-only binding, no-new-privileges)

#### 9. Frontend Procedure Hooks - All Stubs
**Priority:** HIGH → RESOLVED
**Location:** `/frontend/src/hooks/useProcedures.ts`
**Found:** G2_RECON audit (2025-12-30)
**Status:** ✅ FIXED (Session 025, 2025-12-30)

~~All 12 hooks return mock/stub implementations:~~
- ~~`useProcedures()` - Returns empty array~~
- ~~`useProcedure()` - Returns null~~
- ~~`useCreateProcedure()` - Logs to console only~~
- ~~`useUpdateProcedure()` - Logs to console only~~
- ~~`useDeleteProcedure()` - Logs to console only~~
- ~~Plus 7 more stubs~~

**Resolution (Session 025):**
- All 12 hooks wired to backend `/api/credentials/*` endpoints
- Uses TanStack Query patterns consistent with other hooks
- Includes error handling and loading states

#### 10. Frontend Resilience Components - ✅ RESOLVED
**Priority:** HIGH → RESOLVED
**Location:** `/frontend/src/features/resilience/components/`
**Found:** G2_RECON audit (2025-12-30)
**Verified:** 2026-01-04 (Session META_UPDATER verification)

**Status: FULLY WIRED AND TESTED**

All 4 components are fully functional and wired to backend:
- ✅ `BurnoutDashboard.tsx` - Connected to `/api/resilience/burnout` endpoints
- ✅ `ResilienceMetrics.tsx` - Connected to `/api/resilience/metrics` endpoints
- ✅ `N1Analysis.tsx` - Connected to `/api/resilience/contingency` endpoints
- ✅ `UtilizationChart.tsx` - Connected to `/api/resilience/utilization` endpoints

**Test Coverage:** 43 comprehensive tests verify all functionality
- BurnoutDashboard: 12 tests (render, API calls, error handling, state management)
- ResilienceMetrics: 11 tests (data loading, rendering, edge cases)
- N1Analysis: 10 tests (contingency logic, visualization)
- UtilizationChart: 10 tests (chart rendering, threshold indicators)

**Impact:** Resilience monitoring dashboard fully operational
**Previous concern:** G2_RECON found skeleton-only claim in MVP report; verification shows complete implementation was already in place

#### 11. Frontend TypeScript Errors - Pre-existing Build Issues
**Priority:** HIGH → RESOLVED
**Location:** Various frontend components
**Found:** Session 025 reconnaissance (2025-12-30)
**Status:** ✅ FIXED (Session 025, 2025-12-30)

Pre-existing TypeScript errors discovered during Session 025 audit:

| File | Error | Resolution |
|------|-------|------------|
| Various hooks | `zod` module not found | ✅ Added `zod` to dependencies |
| `EmptyState` component | Missing export | ✅ Added named export |
| `SearchInput` component | Props type mismatch | ✅ Fixed prop interface |

**Resolution (Session 025):**
- All TypeScript errors resolved
- `npm run type-check` now passes cleanly
- Build succeeds without type errors

---

### 🟢 MEDIUM PRIORITY - Post-Launch Sprint

#### 13. Frontend Accessibility Gaps - AUDIT UPDATE (2026-01-04)
**Status:** Partially addressed, some items were phantom tasks

| Issue | Status | Notes |
|-------|--------|-------|
| ~~Missing `<thead>` in ScheduleGrid~~ | RESOLVED | `ScheduleHeader.tsx` line 35 uses proper `<thead>` |
| ~~Missing `aria-label` on icon-only buttons~~ | RESOLVED | `IconButton` component enforces `aria-label` as required prop (line 105) |
| ARIA attributes coverage | IN PROGRESS | Navigation.tsx, Button.tsx, ScheduleGrid.tsx have proper ARIA |

**Components with proper ARIA verified:**
- `Navigation.tsx`: Skip-to-content link, nav role, aria-current, aria-labels on icons
- `Button.tsx`: aria-busy, aria-disabled
- `IconButton.tsx`: Enforces aria-label as required prop
- `ScheduleHeader.tsx`: Proper `<thead>`, scope attributes on `<th>`
- `ScheduleGrid.tsx`: role="grid", aria-label, role="row", role="rowheader"
- `LoadingSpinner`: role="status", aria-live, aria-busy

**Remaining work:** Audit remaining 70+ components for ARIA compliance (medium priority)

#### 14. Token Refresh Not Implemented - ✅ RESOLVED
**Priority:** MEDIUM → RESOLVED
**Location:** `/frontend/src/lib/auth.ts`
**Verified:** 2025-12-30 (G2_RECON audit)

- ✅ Full implementation in `frontend/src/lib/auth.ts`
- ✅ Proactive refresh: Background job checks token expiry every 5 minutes
- ✅ Reactive refresh: Intercepts 401 responses and refreshes before retrying
- ✅ Users no longer silently logged out

#### 15. MCP Placeholder Tools (11 tools)
- Hopfield networks, immune system, game theory return synthetic data
- Shapley value returns uniform distribution

#### 16. Frontend WebSocket Client Missing
- Backend WebSocket fully implemented (8 event types)
- Frontend only has SSE, no native WebSocket client

#### 17. Admin Email Invitations - IMPLEMENTED
**Priority:** MEDIUM
**Status:** DONE (verified 2026-01-03) - was a phantom task

~~User creation endpoint contains TODO: "Send invitation email"~~

**Actually Implemented:**
- `admin_users.py:239-265`: Sends email via `send_email.delay()` Celery task when `send_invite=True`
- `admin_users.py:588-610`: Resend invite also uses `send_email.delay()`
- Celery task: `backend/app/notifications/tasks.py:119-192` - fully implemented with retry logic
- Email template: `backend/app/notifications/channels/email/email_templates.py` - `admin_welcome` template exists
- EmailService: `backend/app/services/email_service.py` - full SMTP implementation

**Email Infrastructure Status:**
| Component | Status | Location |
|-----------|--------|----------|
| Celery task | Implemented | `notifications/tasks.py:send_email` |
| Email template | Implemented | `email_templates.py:admin_welcome` |
| SMTP service | Implemented | `email_service.py:EmailService` |
| Route wiring | Implemented | `admin_users.py:260,605` |

**Note:** Actual email delivery depends on SMTP configuration (`SMTP_HOST`, `SMTP_USER`, etc.).
Infrastructure is wired; SMTP credentials are environment-specific.

#### 18. Activity Logging - ✅ COMPLETE
**Priority:** MEDIUM
**Status:** DONE (verified 2026-01-04) - infrastructure exists and deployed

**Fully Implemented:**
- ✅ Model: `backend/app/models/activity_log.py` - Full ActivityLog model with 26 action types
- ✅ Migration: `backend/alembic/versions/20260103_add_activity_log_table.py` - Creates table with indexes
- ✅ Enum: `ActivityActionType` covers user, auth, schedule, swap, and settings actions
- ✅ Table deployed: Database migration runs on startup, table exists in production

**Wiring Status:** FULLY WIRED (verified 2026-01-04)
- [x] `_log_activity()` in `admin_users.py` - 8 call sites fully implemented:
  - Line 265: USER_CREATED on user creation
  - Line 399: USER_UPDATED on user updates
  - Line 449: USER_DELETED on user deletion
  - Line 512: USER_LOCKED/UNLOCKED on toggle
  - Line 547: Lock/unlock with reason
  - Line 618: INVITE_RESENT on resend
  - Line 834: Bulk operations
- [x] `GET /admin/users/activity-log` endpoint implemented (line 661)
- [ ] Add activity logging to schedule modification endpoints (enhancement)

**Note:** Admin audit trail fully operational. Schedule endpoint logging is an enhancement, not a blocker.

#### 19. Penrose Efficiency - Placeholder Logic
**Priority:** MEDIUM
**Location:** `/backend/app/resilience/exotic/penrose_efficiency.py`
**Found:** G2_RECON audit (2025-12-30)

- 10+ TODO comments with placeholder implementations
- Astrophysics-inspired efficiency extraction concept
- Currently returns synthetic data
- **Impact:** Exotic resilience feature non-functional

**Note:** Part of Tier 5 "Exotic Frontier Concepts" - advanced research features

---

### Full-Stack Review Summary

| Layer | Status | Score |
|-------|--------|-------|
| Frontend Architecture | ✅ Excellent | 92/100 |
| Backend Middleware | ✅ Excellent | 94/100 |
| Authentication | ✅ Excellent | 96/100 |
| Database/ORM | ✅ Good | 85/100 |
| Docker/Deploy | ⚠️ Good | 78/100 |
| CI/CD | ✅ Good | 82/100 |
| Error Handling | ✅ Excellent | 92/100 |

**Overall MVP Status:** PRODUCTION-READY ✅ (critical items verified resolved)

See also:
- `docs/planning/MVP_STATUS_REPORT.md` - Full 16-layer analysis
- `docs/planning/TECHNICAL_DEBT.md` - Tracked issues by priority

---

*Last updated: 2025-12-30 (Session 025 - CD pipeline, procedure hooks, TypeScript errors fixed)*


---

## Security & Compliance

### PHI Exposure in API Responses
**Priority:** HIGH
**Found:** PHI Exposure Audit (2025-12-30)
**Location:** `docs/security/PHI_EXPOSURE_AUDIT.md`
**Status:** Awaiting remediation

**Issue:** Protected Health Information (PHI) is exposed in API responses without masking or field-level access control.

**Exposed PHI Elements:**
- Person names and email addresses (clear PHI)
- Absence types (medical, deployment, TDY locations)
- Schedule patterns and duty assignments
- Free-text notes fields (potential PHI in unstructured data)

**Risk Assessment:**
| Category | Risk Level |
|----------|-----------|
| API Responses | HIGH |
| Export Endpoints | HIGH |
| Error Messages | LOW |
| Logging | MEDIUM |

**Required Actions:**
- [ ] Add "X-Contains-PHI" warning headers to affected endpoints
- [ ] Implement PHI access audit logging
- [ ] Sanitize logging to remove email addresses and names
- [ ] Add field-level access control to PersonResponse schema
- [ ] Encrypt bulk export downloads
- [ ] Create BREACH_RESPONSE_PLAN.md
- [ ] Create PHI_HANDLING_GUIDE.md for developers
- [ ] Add automated tests for PHI exposure
- [ ] Review frontend PHI handling
- [ ] Conduct penetration test focused on PHI exfiltration

**Affected Endpoints:**
- `GET /api/people` - All people with names/emails
- `GET /api/people/residents` - Resident names/emails
- `GET /api/people/faculty` - Faculty names/emails
- `GET /api/people/{person_id}` - Individual person details
- `GET /api/absences` - Absences with deployment/TDY data
- `GET /api/assignments` - Schedule patterns

**Note:** System has strong authentication and RBAC controls. Issue is with data exposure within authorized sessions, not unauthorized access.

**See:** `docs/security/PHI_EXPOSURE_AUDIT.md` for full analysis and remediation recommendations.

---

## Documentation Improvements (Completed 2025-12-31)

The following documentation improvements were completed in Stream 9:

- ✅ Created comprehensive Quick Reference Guide (docs/QUICK_REFERENCE.md)
- ✅ Created Getting Started guide for users, developers, and admins
- ✅ Completely rewrote people.md API documentation (71 → 708 lines)
- ✅ Completely rewrote absences.md API documentation (54 → 737 lines)
- ✅ Enhanced BLOCK_10_SUMMARY.md with statistics and compliance status
- ✅ Massively expanded troubleshooting in SCHEDULE_GENERATION_RUNBOOK.md
- ✅ Added advanced CLI usage tips and troubleshooting to cli-reference.md
- ✅ Resolved TODO in GAME_THEORY_SERVICE_SPEC.md with implementation details
- ✅ Added helper methods (_load_faculty_preferences, _load_stigmergy_utilities)
- ✅ Added examples and best practices to analytics.md, schedule.md, swaps.md
- ✅ Filled TBD placeholders in Block 10 schedule dates
- ✅ Added quick links and navigation improvements to README.md

**Total: 100 documentation tasks completed**

---

## Session 045 Findings (2026-01-01)

### Human Action Required: Docker Desktop Restart

**Priority:** HIGH
**Blocker:** Frontend container rebuild needed but Docker Desktop frozen

**Action:**
1. Restart Docker Desktop (Cmd+Q → Relaunch)
2. Run: `docker-compose up -d --build frontend`
3. Verify: `scripts/health-check.sh --docker`

**Context:** ARCHITECT confirmed PR #594 contains functional TypeScript changes requiring rebuild:
- New `frontend/src/types/state.ts` (362 lines)
- New `frontend/src/contexts/index.ts` (28 lines)
- 19 test file renames (.ts → .tsx)

### CI Pipeline Pre-Existing Debt

**Priority:** P1 (not blocking Session 045, existed before)

| Issue | Fix |
|-------|-----|
| package-lock.json sync | `cd frontend && npm install && git add package-lock.json` |
| 11 remaining .ts→.tsx | Rename test files with JSX syntax |

### Backlog Items

**Priority:** P2

| Issue | Owner | Notes |
|-------|-------|-------|
| Fix health-check.sh Redis auth | CI_LIAISON | Script fails on Redis NOAUTH |
| Populate RAG with Session 045 | G4_CONTEXT_MANAGER | Add governance patterns |
| Prune `session-044-local-commit` branch | RELEASE_MANAGER | Likely redundant |

### PR Status

- **PR #595**: Script ownership governance docs (ready to merge)
- **PR #594**: Already merged (CCW burn documentation)

---

## PAI Agent Structure Decisions (2026-01-01)

### G4 Context Management: Keep Separate or Consolidate?

**Priority:** Low (decide when RAG usage patterns emerge)
**Added:** 2026-01-01 (Session: mcp-refinement)
**Status:** Awaiting decision

**Current State:**
- **G4_CONTEXT_MANAGER**: Semantic memory curator (RAG gatekeeper, decides what to remember)
- **G4_LIBRARIAN**: File reference manager (tracks paths in agent specs)

**RAG is now integrated into MCP** with 4 tools:
- `rag_search` - Semantic search (185 chunks indexed)
- `rag_context` - Build LLM context
- `rag_health` - System status
- `rag_ingest` - Add documents

**Key Insight:** RAG provides the *mechanism*, G4 provides the *judgment*. Without intentional curation, RAG could become contaminated with:
- Failed approaches later abandoned
- Debugging tangents
- Work-in-progress that got reverted

**Options:**
| Option | G4_CONTEXT_MANAGER | G4_LIBRARIAN | Notes |
|--------|-------------------|--------------|-------|
| A. Keep both | Curator for RAG | File path tracker | Current state |
| B. Merge into one G4 | Combined semantic + structural | N/A | Simpler hierarchy |
| C. Demote LIBRARIAN | Curator for RAG | Becomes periodic skill | File paths rarely change |

**Decision Criteria:**
- How often do spawned agents need file paths vs RAG queries?
- Is file path management actually a recurring issue?
- Does RAG reduce need for explicit file references?

**Note:** File paths have been working; RAG is new. Wait for usage patterns to emerge before restructuring.

### Subagent MCP Context Gap

**Priority:** Medium
**Added:** 2026-01-01 (Session: mcp-refinement)
**Status:** TODO

**Problem:** Spawned subagents have **no MCP context**. They don't know:
- What MCP tools are available
- How to call them
- RAG endpoint URLs

**Observation:** G4_CONTEXT_MANAGER updated markdown files but didn't use MCP `rag_ingest` because it didn't have tool access in its spawned context.

**Options:**
| Option | Approach | Trade-off |
|--------|----------|-----------|
| A. Add MCP routes to agent prompts | Include API URLs in spawn prompt | More prompt tokens |
| B. Include MCP tool list in agent specs | Update `.claude/Agents/*.md` | Manual maintenance |
| C. Create MCP context skill | `/mcp-context` skill agents can invoke | Extra step |
| D. Environment variable injection | Pass MCP URLs via task metadata | Cleanest but needs tooling |

**Recommended:** Option A or B - include RAG API routes (http://localhost:8000/api/rag/*) in relevant agent specs.

---

## MCP API Client Improvements (2026-01-02)

### Token Refresh on 401 Unauthorized
**Priority:** Medium
**Added:** 2026-01-02 (Session: subagent-rag exploration)
**Status:** Roadmap

**Problem:** MCP API client singleton caches JWT token indefinitely. If:
- Token expires (backend JWT lifetime)
- Token is invalidated (password change, logout)
- Container started before backend was ready

...the client returns 401 for all subsequent calls until container restart.

**Current Behavior:**
```python
# api_client.py - only checks if token is None
async def _ensure_authenticated(self) -> dict[str, str]:
    if self._token is None:  # <-- Doesn't detect expired/invalid tokens
        await self._login()
    return {"Authorization": f"Bearer {self._token}"}
```

**Proposed Fix:**
```python
async def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
    # ... existing retry logic ...

    # On 401, try refreshing token once before giving up
    if response.status_code == 401 and not kwargs.get("_token_refreshed"):
        logger.warning("Received 401 Unauthorized, attempting token refresh")
        self._token = None  # Clear stale token
        kwargs["headers"] = await self._ensure_authenticated()
        kwargs["_token_refreshed"] = True  # Prevent infinite loop
        return await self._request_with_retry(method, url, **kwargs)
```

**Files to modify:**
- `mcp-server/src/scheduler_mcp/api_client.py`

**Testing:**
- [ ] Unit test: 401 triggers token refresh
- [ ] Unit test: Second 401 after refresh raises (prevents loop)
- [ ] Integration test: Token expiry recovery

**Workaround (current):** Restart MCP container to clear stale client:
```bash
docker compose restart mcp-server
```
