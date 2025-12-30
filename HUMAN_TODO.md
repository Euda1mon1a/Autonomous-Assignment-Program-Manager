# Human TODO

> Tasks that require human action (external accounts, manual configuration, etc.)

---

## Next Session Priority (2025-12-25)

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

**Test Coverage Gap Identified:**
- No explicit balance behavior tests exist
- Balance is verified implicitly through assignment distribution
- Recommendation: Add dedicated `test_template_balance_*` tests to each solver's test class

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

### Broken Documentation Links (Need Decision)

The following links in `README.md` point to non-existent files:

| Broken Link | Suggested Fix |
|-------------|---------------|
| `docs/api/endpoints/credentials.md` (line 81) | → `docs/api/authentication.md` |
| `docs/SETUP.md` (line 180) | → `docs/getting-started/installation.md` |
| `docs/API_REFERENCE.md` (line 376) | → `docs/api/index.md` |

**Decision needed:** Fix links to existing files, or create the missing files?

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

#### 1. Celery Worker Missing Queues
**Priority:** CRITICAL
**Location:** `docker-compose.yml` (celery-worker service)

```yaml
# CURRENT (broken):
command: celery -A app.core.celery_app worker -Q default,resilience,notifications

# SHOULD BE:
command: celery -A app.core.celery_app worker -Q default,resilience,notifications,metrics,exports,security
```

**Impact:** Metrics, exports, and security rotation tasks will queue indefinitely.

#### 2. Security TODOs in audience_tokens.py
**Priority:** CRITICAL
**Location:** `/backend/app/api/routes/audience_tokens.py`

| Line | Issue | Risk |
|------|-------|------|
| 120 | Role-based audience restrictions missing | Privilege escalation |
| 198 | Token ownership verification incomplete | Token theft |

**Action:** Implement role checks and ownership verification before MVP launch.

### 🟡 HIGH PRIORITY - Fix This Week

#### 3. Frontend Environment Variable Mismatch
**Location:** `/frontend/src/hooks/useClaudeChat.ts`
- Uses `REACT_APP_API_URL` (React CRA style)
- Should use `NEXT_PUBLIC_API_URL` (Next.js style)
- **Impact:** Claude chat will fail silently

#### 4. Missing Database Indexes
**Location:** Database schema
```sql
CREATE INDEX idx_block_date ON blocks(date);
CREATE INDEX idx_assignment_person_id ON assignments(person_id);
CREATE INDEX idx_assignment_block_id ON assignments(block_id);
```
**Impact:** Slow queries on schedule views and reports

#### 5. Admin Users Page API Not Wired
**Location:** `/frontend/src/app/admin/users/page.tsx`
- 4 TODO comments for CRUD API calls
- Currently uses mock data
- **Impact:** User management non-functional

#### 6. Resilience API Response Models
**Location:** `/backend/app/api/routes/resilience.py`
- Only 12/54 endpoints have `response_model` defined (22%)
- **Impact:** Poor OpenAPI documentation, inconsistent responses

### 🟢 MEDIUM PRIORITY - Post-Launch Sprint

#### 7. Frontend Accessibility Gaps
- Only 24/80 core components have ARIA attributes
- Missing `<thead>` in ScheduleGrid tables
- Missing `aria-label` on icon-only buttons

#### 8. Token Refresh Not Implemented
- Access tokens expire in 15 minutes
- Refresh token exists but not used in frontend
- Users silently logged out

#### 9. MCP Placeholder Tools (11 tools)
- Hopfield networks, immune system, game theory return synthetic data
- Shapley value returns uniform distribution

#### 10. Frontend WebSocket Client Missing
- Backend WebSocket fully implemented (8 event types)
- Frontend only has SSE, no native WebSocket client

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

**Overall MVP Status:** PRODUCTION-READY (with 2 critical fixes)

See also:
- `docs/planning/MVP_STATUS_REPORT.md` - Full 16-layer analysis
- `docs/planning/TECHNICAL_DEBT.md` - Tracked issues by priority

---

*Last updated: 2025-12-30 (Full-stack MVP review completed)*
