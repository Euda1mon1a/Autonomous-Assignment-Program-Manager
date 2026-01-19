# MASTER PRIORITY LIST - Codebase Audit

> **Generated:** 2026-01-18
> **Last Updated:** 2026-01-18 (Thermodynamics free-energy + energy-landscape MCP tools wired)
> **Authority:** This is the single source of truth for codebase priorities.
> **Supersedes:** TODO_INVENTORY.md, PRIORITY_LIST.md, TECHNICAL_DEBT.md, ARCHITECTURAL_DISCONNECTS.md
> **Methodology:** Full codebase exploration via Claude Code agents

---

## CRITICAL (Fix Immediately)

### 1. ~~Orphan Security Routes~~ ✅ RESOLVED
6 routes now wired to API (commit `b92a9e02`):

| Route | Endpoint | Status |
|-------|----------|--------|
| `sso.py` | `/api/v1/sso` | ✅ Wired |
| `audience_tokens.py` | `/api/v1/audience-tokens` | ✅ Wired |
| `sessions.py` | `/api/v1/sessions` | ✅ Wired |
| `profiling.py` | `/api/v1/profiling` | ✅ Wired |
| `claude_chat.py` | `/api/v1/claude-chat` | ✅ Wired |
| `scheduler.py` | `/api/v1/scheduler-jobs` | ✅ Wired |

**Resolved:** 2026-01-18 in `feature/master-priority-implementation`

### 2. PII in Git History
- Resident names in deleted files (BLOCK_10_SUMMARY.md, AIRTABLE_EXPORT_SUMMARY.md) still in history
- Requires `git filter-repo` + force push to main
- All collaborators must re-clone after

**Ref:** `docs/TODO_INVENTORY.md` line 6

### 3. ~~Documentation Contradictions~~ ✅ RESOLVED
Contradictions fixed (commit `pending`):

| Doc | Fix Applied |
|-----|-------------|
| TECHNICAL_DEBT.md | Tracking table now shows DEBT-001/002/003 as Resolved |
| ARCHITECTURAL_DISCONNECTS.md | Removed stale STATUS UPDATE section, added authority note |
| PRIORITY_LIST.md | Added deprecation header pointing here |
| TODO_INVENTORY.md | Added deprecation header pointing here |

**Resolved:** 2026-01-18 in `feature/master-priority-implementation`

### 4. ~~Frontend API Path Mismatches~~ ✅ RESOLVED
3 hooks fixed (commit `b92a9e02`):

| Hook | Before | After | Status |
|------|--------|-------|--------|
| `useGameTheory` | `/v1/game-theory/*` | `/game-theory/*` | ✅ Fixed |
| `usePhaseTransitionRisk` | `/exotic-resilience/...` | `/resilience/exotic/...` | ✅ Fixed |
| `useRigidityScore` | `/exotic-resilience/...` | `/resilience/exotic/...` | ✅ Fixed |

**Resolved:** 2026-01-18 in `feature/master-priority-implementation`

### 5. ~~Schedule Rollback Data Loss~~ ✅ RESOLVED
Fixed in commits `66a14461` and `8bbb3cb9`:
- `_find_existing_assignments()` captures both AM+PM for "ALL" time_of_day
- Full provenance serialization (block_assignment_id, overridden_by/at, updated_at)
- All 3 restoration paths restore all fields including updated_at
- Duplicate prevention with `results = []` before fallback path
- Date string coercion in work_hour_validator.py

**Resolved:** 2026-01-18 in `feature/master-priority-implementation`

---

## HIGH (Address Soon)

### 6. Orphan Framework Code (12K+ LOC) - ANALYSIS COMPLETE
Production-quality infrastructure built for future scaling. Analyzed 2026-01-18:

| Module | LOC | Quality | Recommendation |
|--------|-----|---------|----------------|
| **CQRS** (`backend/app/cqrs/`) | 4,248 | Full impl, 1 test file | **ROADMAP** - Keep for multi-facility scaling |
| **Saga** (`backend/app/saga/`) | 2,142 | Full impl with compensation | **EVALUATE** - Useful for swap workflows |
| **EventBus** (`backend/app/eventbus/`) | 1,385 | Generic Redis pub/sub | **INVESTIGATE** - See note below |
| **Deployment** (`backend/app/deployment/`) | 2,773 | Blue-green + canary | **EVALUATE** - Zero-downtime deploys |
| **gRPC** (`backend/app/grpc/`) | 1,775 | Full server, JWT auth | **EVALUATE** - MCP/external integrations |

**EventBus Investigation Required:**
- Two event systems exist intentionally:
  - `app/events/` = Domain event sourcing (ScheduleCreated, SwapExecuted) - **USED** by `stroboscopic_manager.py`
  - `app/eventbus/` = Generic distributed messaging (Redis pub/sub, wildcards) - **UNUSED** but likely for external integrations
- **Probable use case:** n8n workflow automation, external system webhooks, multi-facility sync
- **Do not delete** - architecture intent is external integration, not internal domain events

**Near-Term Integration Candidates:**
1. **Saga** → Swap execution workflows (multi-step with automatic rollback)
2. **Deployment** → CI/CD pipeline (zero-downtime releases)
3. **gRPC** → MCP server performance (binary protocol vs REST)

**Decision:** Keep all modules on roadmap. Integrate as features require.

### 7. ~~Feature Flags~~ ✅ RESOLVED
- **Location:** `backend/app/features/` - 45KB of production-ready code
- **Before:** 1 flag (`swap_marketplace_enabled`)
- **After:** 5 flags with backend gating on 17 exotic resilience endpoints

| Flag Key | Default | Target Roles | Purpose |
|----------|---------|--------------|---------|
| `swap_marketplace_enabled` | true | admin, coordinator, faculty | Original flag |
| `labs_hub_enabled` | true | admin, coordinator | Gates `/admin/labs` hierarchy |
| `exotic_resilience_enabled` | false | admin | Gates 17 `/resilience/exotic/*` endpoints |
| `voxel_visualization_enabled` | false | admin | Gates 3D voxel viz (perf-intensive) |
| `command_center_enabled` | false | admin | Gates overseer dashboard |

**~~HIGH: Endpoints Missing `current_user` Injection~~** ✅ FIXED
All 17 feature-flagged endpoints now have `current_user: User = Depends(get_current_active_user)`.
Issue identified in code review was based on commit `66a14461`, but PR #743 fixed this before merge.

**Resolved:** 2026-01-18 in PR #743
**Future work:** Frontend `useFeatureFlag` hook, percentage rollouts, individual lab category flags

### 8. ~~MCP Tool Placeholders (16 tools)~~ ✅ RESOLVED

**Progress:** 16/16 tools now wired to backend (2026-01-18)

**FULLY WORKING (real backend with real data):**
| Tool | Domain | Backend Endpoint |
|------|--------|------------------|
| `assess_immune_response_tool` | Immune System | `/resilience/exotic/immune/assess` |
| `check_memory_cells_tool` | Immune System | `/resilience/exotic/immune/memory-cells` |
| `analyze_antibody_response_tool` | Immune System | `/resilience/exotic/immune/antibody-analysis` |
| `get_unified_critical_index_tool` | Composite | `/resilience/exotic/composite/unified-critical-index` |
| `calculate_recovery_distance_tool` | Composite | `/resilience/exotic/composite/recovery-distance` |
| `assess_creep_fatigue_tool` | Composite | `/resilience/exotic/composite/creep-fatigue` |
| `analyze_transcription_triggers_tool` | Composite | `/resilience/exotic/composite/transcription-factors` |
| `calculate_shapley_workload_tool` | Fairness | `/mcp-proxy/calculate-shapley-workload` |
| `calculate_hopfield_energy_tool` | Hopfield | `/resilience/exotic/hopfield/energy` |
| `find_nearby_attractors_tool` | Hopfield | `/resilience/exotic/hopfield/attractors` |
| `measure_basin_depth_tool` | Hopfield | `/resilience/exotic/hopfield/basin-depth` |
| `detect_spurious_attractors_tool` | Hopfield | `/resilience/exotic/hopfield/spurious` |
| `optimize_free_energy_tool` | Thermodynamics | `/resilience/exotic/thermodynamics/free-energy` |
| `analyze_energy_landscape_tool` | Thermodynamics | `/resilience/exotic/thermodynamics/energy-landscape` |

**MISSING BACKEND ENDPOINTS (MCP has API calls, backend 404s):**
| Tool | Domain | Expected Endpoint |
|------|--------|-------------------|
| `calculate_coverage_var_tool` | VaR Risk | `/api/v1/analytics/coverage-var` |
| `calculate_workload_var_tool` | VaR Risk | `/api/v1/analytics/workload-var` |

**Note:** Core ACGME validation tools are REAL implementations. All 16 MCP resilience tools now wired to real backend.

**Frontend Visualizer/Dashboard Status:**

| Module | Viz | Dash | Frontend Location | Data |
|--------|-----|------|-------------------|------|
| Unified Critical Index | ✓ | ✓ | `features/resilience/ResilienceHub.tsx` | API |
| Recovery Distance | ✗ | ✗ | Not implemented | - |
| Creep Fatigue | ✗ | ✗ | Not implemented | - |
| Transcription Factors | ✗ | ✗ | Not implemented | - |
| Hopfield Network | ✓ | ✗ | `features/hopfield-energy/` | Mock |
| Free Energy | ✗ | ✗ | Not implemented | API ✅ |
| Energy Landscape | ✗ | ✗ | Not implemented | API ✅ |
| Circadian Phase | ✓ | ✗ | `features/synapse-monitor/` | Mock |
| Penrose Efficiency | ✗ | ✗ | Not implemented | - |
| Anderson Localization | ✗ | ✗ | Not implemented | - |
| Persistent Homology | ✗ | ✗ | Not implemented | - |
| Keystone Species | ✗ | ✗ | Not implemented | - |
| Quantum Zeno | ✗ | ✗ | Not implemented | - |
| Stigmergy | ✓ | ✗ | `app/admin/visualizations/stigmergy-flow/` | Mock |
| Static Stability | ✓ | ✗ | `features/sovereign-portal/` | API |
| Le Chatelier | ✗ | ✓ | MCP tool analysis | API |

### 9. GUI Components Using Mock Data (10 components)

**Command Center Dashboards (HIGH - misleading operators):**
| Component | Location | Issue |
|-----------|----------|-------|
| ResilienceOverseerDashboard | `components/scheduling/` | `generateMockData()` simulates live metrics |
| SovereignPortal | `features/sovereign-portal/` | `generateMockDashboardState()` fakes all 4 panels |
| ResilienceLabsPage | `app/admin/labs/resilience/` | "Mock AI analysis" with hardcoded responses |

**Labs Visualizations (MEDIUM - beta/demo status):**
| Component | Location | Issue |
|-----------|----------|-------|
| Synapse Monitor | `features/synapse-monitor/` | Uses `MOCK_PERSONNEL` |
| Fragility Triage | `features/fragility-triage/` | `generateMockDays()` creates random fragility |
| N-1/N-2 Resilience | Labs page | `MOCK_FACULTY` with simulated cascades |
| Holographic Hub | `features/holographic-hub/` | `generateMockHolographicData()` |

**Decision needed:** Wire to real MCP tools OR add "DEMO" badges to UI.

### 10. ACGME Compliance Validation Gaps
Call duty and performance profiling have edge cases:

| Issue | Location | Status |
|-------|----------|--------|
| `call_assignments` excluded from 24+4/rest checks | `acgme_compliance_engine.py:231,273` | ⏸️ Deferred - Pending MEDCOM ruling |
| Performance profiler uses hardcoded defaults | `constraint_validator.py:567` | ✅ Fixed - Uses actual context.residents/blocks |
| MCP SSE/HTTP localhost inconsistency | `server.py:5348,5536` | ✅ Fixed - Aligned localhost detection |

**Action:** Merge call_assignments into shift validation (pending MEDCOM ruling on ACGME interpretation).
**Ref:** `docs/reviews/2026-01-17-current-changes-review.md`

---

## MEDIUM (Plan for Sprint)

### 11. ~~Admin Activity Logging~~ ✅ RESOLVED
Activity logging is fully implemented:
- Migration `20260117_xxx` creates `activity_log` table
- `admin_users.py:_log_activity()` writes to database
- `/admin/users/{id}/activity` endpoint returns activity history

**Resolved:** 2026-01-18 - Implementation exists, was incorrectly marked as stub

### 12. ~~Invitation Emails~~ ✅ RESOLVED (Alternative Implementation)
Invitation emails work via different code path:
- Create user: Uses `render_email_template("admin_welcome")` + `send_email.delay()`
- Resend invite: Uses `render_email_template()` + `send_email.delay()`
- **Note:** `email_service.py:send_invitation_email()` is dead code (never called) - cleanup candidate

**Resolved:** 2026-01-18 - Feature works, original function is unused dead code

### 13. Service Layer Pagination
- `absence_controller.py:45` - Pagination applied at controller level
- **Need:** Push to service/repository for SQL LIMIT/OFFSET efficiency

### 14. ~~Documentation Consolidation~~ ✅ RESOLVED
Root-level docs reduced from 68 → 28 files.

| Before | After | Change |
|--------|-------|--------|
| 68 root docs | 28 root docs | -40 files consolidated |
| Scattered guides | Consolidated in `docs/development/` | Easier navigation |

**Remaining:** openapi.yaml (Dec 31) timestamp stale, but content accurate.
**Resolved:** 2026-01-18 in `feature/master-priority-implementation`

### 15. ~~CLI and Security Cleanup~~ ✅ RESOLVED
Codex review issues fixed:

| Issue | Location | Status |
|-------|----------|--------|
| Startup log references wrong CLI command | `main.py:145` | ✅ Fixed - Now shows `app.cli user create` |
| Queue whitelist too permissive | `queue.py:65` | ✅ Fixed - Removed `app.services.*` prefix |

**Resolved:** 2026-01-18 in `feature/master-priority-implementation` (commit `8bbb3cb9`)
**Ref:** `docs/reviews/2026-01-17-current-changes-review.md`

### 16. ~~VaR Backend Endpoints~~ ✅ RESOLVED
Endpoints created and wired to MCP tools:
- `POST /api/v1/analytics/coverage-var` - Coverage Value-at-Risk
- `POST /api/v1/analytics/workload-var` - Workload Value-at-Risk
- `POST /api/v1/analytics/conditional-var` - Conditional VaR (CVaR/Expected Shortfall)

**Files added:**
- `backend/app/schemas/var_analytics.py` - Request/response schemas
- `backend/app/services/var_service.py` - VaR calculation service
- `backend/tests/services/test_var_service.py` - Unit tests

**Resolved:** 2026-01-18 in PR #744

### 17. ~~Seed Script Credentials~~ ✅ RESOLVED
Issue identified in code review was based on commit `66a14461` which had hard-coded `AdminPassword123!`.
PR #743 fixed this - now uses `os.environ.get("ADMIN_PASSWORD", "admin123")` matching the app's default.

**Resolved:** 2026-01-18 in PR #743
**Ref:** `docs/reviews/2026-01-18-commit-66a1446-review.md`

---

## LOW (Backlog)

### 18. A/B Testing Infrastructure
- **Location:** `backend/app/experiments/`
- Infrastructure exists, route registered
- Minimal production usage - consider for Labs rollout

### 19. ML Workload Analysis
- `ml.py` returns "placeholder response"
- Low priority unless ML features requested

### 20. Time Crystal DB Loading
- `time_crystal_tools.py:281, 417`
- Acceptable fallback to empty schedules
- Fix if `schedule_id` parameter becomes primary use case

### 21. Spreadsheet Editor for Tier 1 Users (PR #740)
Excel-like grid editor for schedule verification - eases transition for "normie" users comfortable with Excel.

| Feature | Status | Spec |
|---------|--------|------|
| Grid display (residents × dates) | Specified | `docs/design/SPREADSHEET_EDITOR_SPEC.md` |
| Click-to-edit with rotation dropdowns | Specified | Custom build (no license cost) |
| SheetJS export to `.xlsx` | Library installed | `xlsx@0.20.2` already in deps |
| ACGME hours validation per row | Specified | Reuses existing validators |
| Keyboard nav (arrows, Tab, Enter) | Specified | ~3-4 days implementation |

**Target:** Program coordinators, schedulers, admins who prefer Excel workflow.
**Benefit:** Eliminates export→edit→reimport friction; keeps data in-app.
**Ref:** PR #740, `docs/design/SPREADSHEET_EDITOR_SPEC.md`

---

## ALREADY WORKING (No Action Required)

| Module | Status | Evidence |
|--------|--------|----------|
| GraphQL | ✅ Active | Registered in main.py:437-440 |
| WebSocket | ✅ Active | Used by 6+ routes for real-time updates |
| Streaming | ✅ Active | Integrated with WebSocket |
| ACGME Validation | ✅ Real | Full compliance checking |
| RAG Search | ✅ Real | Vector embeddings working |
| Circuit Breakers | ✅ Real | State tracking functional |
| Feature Flags | ✅ Real | Infrastructure complete (underutilized) |
| Fairness Suite | ✅ Production | Lorenz, Shapley, Trends fully wired |

---

## INFRASTRUCTURE QUICK WINS ✅ (2026-01-18)

Low-effort, high-impact fixes completed this session:

### Docker Bind Mounts (Data Persistence)
Switched local development from named volumes to bind mounts.

| Before | After | Benefit |
|--------|-------|---------|
| Named volumes in `/var/lib/docker/volumes/` | `./data/postgres/`, `./data/redis/` | Data visible on host |
| Lost on `docker system prune` | Survives Docker resets | No more "where did my data go?" |
| Hidden, hard to backup | `cp -r data/postgres backups/` | Easy backup/restore |

**Files:** `docker-compose.local.yml`, `.gitignore`, `scripts/migrate-volumes-to-bind.sh`
**Docs:** `BEST_PRACTICES_AND_GOTCHAS.md`, `LOCAL_DEVELOPMENT_RECOVERY.md`

### Academic Year Fix
`block_quality_report_service.py` now derives academic year from block start date (July-June cycle) instead of hardcoding 2025.

### psutil Dependency
Added `psutil>=5.9.0` to `requirements.txt` for system profiling capabilities.

---

## SUMMARY

| Priority | Issues | Scope |
|----------|--------|-------|
| **CRITICAL** | 1 open, 4 resolved | ~~orphan routes~~✅, PII, ~~doc contradictions~~✅, ~~API mismatches~~✅, ~~rollback data loss~~✅ |
| **HIGH** | 2 open, 3 resolved | frameworks, ~~feature flags~~✅, ~~MCP stubs~~✅ (16/16 wired), mock GUI, ACGME compliance |
| **MEDIUM** | 1 open, 6 resolved | ~~activity logging~~✅, ~~emails~~✅, pagination, ~~docs~~✅, ~~CLI/security cleanup~~✅, ~~VaR endpoints~~✅, ~~seed script~~✅ |
| **LOW** | 4 | A/B testing, ML, time crystal, spreadsheet editor (tier 1 UX) |
| **INFRA** | 3 resolved | ~~bind mounts~~✅, ~~academic year fix~~✅, ~~psutil dep~~✅ |

### Biggest Wins (Impact vs Effort)

1. ~~**Wire 6 orphan routes**~~ ✅ DONE → SSO, sessions, profiling now available
2. ~~**Fix 3 API path mismatches**~~ ✅ DONE → Game theory, exotic resilience now working
3. ~~**Fix rollback serialization**~~ ✅ DONE → Schedule backup/restore now captures all fields
4. **Integrate orphan frameworks** → Saga for swaps, Deployment for CI/CD, gRPC for MCP (ON ROADMAP)
5. ~~**Fix doc contradictions**~~ ✅ DONE → Trust in documentation restored
6. ~~**Fix feature flag issues**~~ ✅ DONE → All 17 endpoints have current_user injection, seed script uses env vars
7. ~~**Wire Hopfield MCP tools**~~ ✅ DONE (PR #747) → 4 endpoints with real backend calculations
8. **Wire remaining MCP tools** → 2 thermodynamics tools remain (free energy, energy landscape)
9. **Wire mock dashboards** → Real data for ResilienceOverseer, SovereignPortal (MEDIUM effort)

---

*This document consolidates findings from TODO_INVENTORY.md, PRIORITY_LIST.md, TECHNICAL_DEBT.md, and ARCHITECTURAL_DISCONNECTS.md. Keep this as the authoritative source.*
