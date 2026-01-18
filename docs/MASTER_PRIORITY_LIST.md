# MASTER PRIORITY LIST - Codebase Audit

> **Generated:** 2026-01-18
> **Supersedes:** Scattered tracking in TODO_INVENTORY.md, PRIORITY_LIST.md, TECHNICAL_DEBT.md
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

### 3. Documentation Contradictions
| Doc A | Doc B | Contradiction |
|-------|-------|---------------|
| PRIORITY_LIST.md | TECHNICAL_DEBT.md | DEBT-001/002/003 marked "RESOLVED" vs "Open" |
| ROADMAP.md | TODO_INVENTORY.md | Items marked done that aren't |
| ARCHITECTURAL_DISCONNECTS.md | itself | Claims issues resolved then documents them as critical |

**Action:** Reconcile documents or consolidate into this file.

### 4. ~~Frontend API Path Mismatches~~ ✅ RESOLVED
3 hooks fixed (commit `b92a9e02`):

| Hook | Before | After | Status |
|------|--------|-------|--------|
| `useGameTheory` | `/v1/game-theory/*` | `/game-theory/*` | ✅ Fixed |
| `usePhaseTransitionRisk` | `/exotic-resilience/...` | `/resilience/exotic/...` | ✅ Fixed |
| `useRigidityScore` | `/exotic-resilience/...` | `/resilience/exotic/...` | ✅ Fixed |

**Resolved:** 2026-01-18 in `feature/master-priority-implementation`

### 5. Schedule Rollback Data Loss
Rollback/backup infrastructure has gaps that can cause data loss:

| Issue | Location | Impact |
|-------|----------|--------|
| `time_of_day="ALL"` only captures AM | `schedule_publish_staging.py:277` | PM assignment lost |
| Missing fields in serialization | `schedule_publish_staging.py:298,403` | Provenance/overrides lost |
| Rest-period assumes `date` objects | `work_hour_validator.py:341` | TypeError on strings |

**Action:** Fix serialization to capture all slots and fields; add date coercion.
**Ref:** `docs/reviews/2026-01-17-current-changes-review.md`

---

## HIGH (Address Soon)

### 6. Orphan Framework Code (12K+ LOC)
Built but never integrated into production code paths:

| Module | LOC | Status |
|--------|-----|--------|
| CQRS (`backend/app/cqrs/`) | 4,248 | Full infrastructure, zero usage |
| Saga (`backend/app/saga/`) | 2,142 | Orchestration pattern, unused |
| EventBus (`backend/app/eventbus/`) | 1,385 | Pub/sub, dormant |
| Deployment (`backend/app/deployment/`) | 2,773 | Canary/blue-green, never instantiated |
| gRPC (`backend/app/grpc/`) | 1,775 | Full server, no clients |

**Decision needed:** Integrate into scheduler engine OR remove to reduce maintenance burden.

### 7. Feature Flags Underutilized
- **Location:** `backend/app/features/` - 45KB of production-ready code
- **Actual usage:** 1 flag (`swap_marketplace_enabled` in `portal.py`)
- **Should flag:** Labs hub, 3D visualizations, experimental scheduling algorithms

### 8. MCP Tool Placeholders (16 tools)

**NOT IMPLEMENTED (return zeros):**
| Tool | Domain |
|------|--------|
| `optimize_free_energy_tool` | Thermodynamics |
| `analyze_energy_landscape_tool` | Thermodynamics |

**MOCK DATA (realistic placeholders):**
| Tool | Domain |
|------|--------|
| `calculate_shapley_workload_tool` | Fairness |
| `calculate_hopfield_energy_tool` | Hopfield |
| `find_nearby_attractors_tool` | Hopfield |
| `measure_basin_depth_tool` | Hopfield |
| `detect_spurious_attractors_tool` | Hopfield |
| `get_unified_critical_index_tool` | Resilience |
| `calculate_recovery_distance_tool` | Resilience |
| `assess_creep_fatigue_tool` | Resilience |
| `analyze_transcription_triggers_tool` | Resilience |

**API FALLBACK (mock when backend unavailable):**
| Tool | Domain |
|------|--------|
| `assess_immune_response_tool` | Immune System |
| `check_memory_cells_tool` | Immune System |
| `analyze_antibody_response_tool` | Immune System |
| `calculate_coverage_var_tool` | VaR Risk |
| `calculate_workload_var_tool` | VaR Risk |

**Note:** Core ACGME validation tools are REAL implementations.

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

| Issue | Location | Impact |
|-------|----------|--------|
| `call_assignments` excluded from 24+4/rest checks | `acgme_compliance_engine.py:231,273` | Extended call duty not validated |
| Performance profiler uses hardcoded defaults | `constraint_validator.py:567` | Understates real workload complexity |
| MCP SSE/HTTP localhost inconsistency | `server.py:5348,5536` | Startup failures with `0.0.0.0` |

**Action:** Merge call_assignments into shift validation; fix localhost detection.
**Ref:** `docs/reviews/2026-01-17-current-changes-review.md`

---

## MEDIUM (Plan for Sprint)

### 11. Admin Activity Logging
- `admin_users.py:77` - `_log_activity()` is no-op placeholder
- `admin_users.py:596` - Returns empty response pending table creation
- **Need:** Alembic migration for `activity_log` table

### 12. Invitation Emails
- `admin_users.py:236, 552` - Emails not actually sent
- **Need:** Wire EmailService to notification tasks

### 13. Service Layer Pagination
- `absence_controller.py:45` - Pagination applied at controller level
- **Need:** Push to service/repository for SQL LIMIT/OFFSET efficiency

### 14. Documentation Consolidation
- **68 root-level .md files** (PRIORITY_LIST.md recommended 5-8)
- Stale timestamps: openapi.yaml (Dec 31), ENDPOINT_CATALOG.md (Jan 4)
- Many docs reference files that no longer exist

### 15. CLI and Security Cleanup
Minor issues found in Codex review:

| Issue | Location | Impact |
|-------|----------|--------|
| Startup log references wrong CLI command | `main.py:145` | Operator confusion |
| Queue whitelist too permissive | `queue.py:65` | Any `app.services.*` allowed |

**Action:** Fix CLI reference; tighten queue task allowlist.
**Ref:** `docs/reviews/2026-01-17-current-changes-review.md`

---

## LOW (Backlog)

### 16. A/B Testing Infrastructure
- **Location:** `backend/app/experiments/`
- Infrastructure exists, route registered
- Minimal production usage - consider for Labs rollout

### 17. ML Workload Analysis
- `ml.py` returns "placeholder response"
- Low priority unless ML features requested

### 18. Time Crystal DB Loading
- `time_crystal_tools.py:281, 417`
- Acceptable fallback to empty schedules
- Fix if `schedule_id` parameter becomes primary use case

### 19. Spreadsheet Editor for Tier 1 Users (PR #740)
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

## SUMMARY

| Priority | Issues | Scope |
|----------|--------|-------|
| **CRITICAL** | 3 open, 2 resolved | ~~orphan routes~~✅, PII, doc contradictions, ~~API mismatches~~✅, rollback data loss |
| **HIGH** | 5 | frameworks, feature flags, MCP stubs, mock GUI, ACGME compliance gaps |
| **MEDIUM** | 5 | Activity logging, emails, pagination, docs, CLI/security cleanup |
| **LOW** | 4 | A/B testing, ML, time crystal, spreadsheet editor (tier 1 UX) |

### Biggest Wins (Impact vs Effort)

1. ~~**Wire 6 orphan routes**~~ ✅ DONE → SSO, sessions, profiling now available
2. ~~**Fix 3 API path mismatches**~~ ✅ DONE → Game theory, exotic resilience now working
3. **Fix rollback serialization** → Prevent schedule data loss on restore (MEDIUM effort, CRITICAL impact)
4. **Decide on CQRS/Saga/EventBus** → 12K LOC to integrate or remove (MEDIUM effort)
5. **Fix doc contradictions** → Restore trust in documentation (LOW effort)
6. **Expand feature flag usage** → Labs, 3D viz behind flags (LOW effort)
7. **Wire mock dashboards** → Real data for ResilienceOverseer, SovereignPortal (MEDIUM effort)

---

*This document consolidates findings from TODO_INVENTORY.md, PRIORITY_LIST.md, TECHNICAL_DEBT.md, and ARCHITECTURAL_DISCONNECTS.md. Keep this as the authoritative source.*
