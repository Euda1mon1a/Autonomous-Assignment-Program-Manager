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
**Status:** To implement

**Issues:**
- [ ] Top header row (dates) disappears when scrolling vertically through residents
- [ ] First column (resident name/PGY) disappears when scrolling horizontally

**Implementation:**
```css
/* Sticky header row */
th { position: sticky; top: 0; background-color: ...; z-index: 1; }

/* Sticky first column */
td:first-child, th:first-child { position: sticky; left: 0; z-index: 2; }
```

**Additional UX suggestions:**
- Add subtle row/column hover highlight for scanning dense schedules
- Ensure scroll container is on grid (not whole page)

---

### 2. Heatmap Page - Add Block Navigation
**Priority:** High
**Page:** `/heatmap`
**Status:** To implement

**Current state:** Only manual date pickers (From/To)

**Requested:** Match Schedule page block navigation pattern:
```
[◀ Previous Block] [Next Block ▶] [Today] [This Block] Block: [Mar 12 - Apr 8, 2026]
```

**Proposed layout:**
```
Current:  From: [date] To: [date] Group by: [dropdown] ☑ Include FMIT [Filters]

Proposed: [◀ Prev] [Next ▶] [Today] [This Block] Block: [Date Range]
          From: [date] To: [date] Group by: [dropdown] ☑ Include FMIT [Filters]
```

**Benefits:**
- Consistency with Schedule page UX
- One-click block selection vs manual date entry
- Quick navigation through 730 blocks

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
**Status:** UX improvement needed

**Current behavior:** Shows "Error Loading Manifest - Not Found" when no schedule data exists

**Issues:**
- [ ] Poor error message - doesn't explain the actual problem
- [ ] No empty state guidance for users
- [ ] Date picker allows selecting dates with no schedule data

**Recommended fixes:**
- [ ] Better error message: "No schedule assignments for this date"
- [ ] Empty state with CTA: "No schedule data available. Generate a schedule or import data to get started"
- [ ] Disable/gray out dates with no schedule data
- [ ] Show data availability indicator (e.g., "Schedule available: Mar 16 - Apr 12, 2026")

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

### Backend Fix: Faculty Assignments Missing rotation_template_id

**Priority:** Medium
**Found:** Session 14 (2025-12-22)
**Location:** Schedule generation engine or seeder

**Issue:** Faculty-Inpatient Year View shows all zeros because faculty assignments are created without `rotation_template_id`.

Database verification:
```
 total_assignments | with_template | without_template |   type
-------------------+---------------+------------------+----------
                40 |             0 |               40 | faculty
                40 |            40 |                0 | resident
```

**Root Cause:** The schedule generator creates faculty assignments without linking rotation templates. The frontend correctly filters by `activity_type === 'inpatient'`, but faculty assignments have `activity_type = NULL` because no template is assigned.

**Files to investigate:**
- `backend/app/scheduling/engine.py` - Faculty assignment creation logic
- Seed scripts that generate test data

**Frontend code (working correctly):**
```typescript
// FacultyInpatientWeeksView.tsx:92-94
if (
  (am && am.activityType?.toLowerCase() === 'inpatient') ||
  (pm && pm.activityType?.toLowerCase() === 'inpatient')
) {
  count++
```

---

### Solver Template Distribution Bugs - FIXED

**Priority:** High
**Found:** Session review (2025-12-24)
**Fixed:** 2025-12-24
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

*Last updated: 2025-12-28*
