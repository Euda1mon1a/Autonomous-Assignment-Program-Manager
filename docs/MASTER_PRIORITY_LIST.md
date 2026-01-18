# MASTER PRIORITY LIST - Codebase Audit

> **Generated:** 2026-01-18
> **Supersedes:** Scattered tracking in TODO_INVENTORY.md, PRIORITY_LIST.md, TECHNICAL_DEBT.md
> **Methodology:** Full codebase exploration via Claude Code agents

---

## CRITICAL (Fix Immediately)

### 1. Orphan Security Routes (NOT WIRED)
6 fully-implemented routes disconnected from main API:

| Route | LOC | Impact |
|-------|-----|--------|
| `sso.py` | 551 | **SSO authentication unavailable** |
| `audience_tokens.py` | 531 | **Auth token generation missing** |
| `sessions.py` | 287 | **User session management missing** |
| `profiling.py` | 662 | Performance analysis unavailable |
| `claude_chat.py` | 885 | Claude integration disconnected |
| `scheduler.py` | 550 | Background job scheduler unwired |

**Location:** `backend/app/api/routes/`
**Action:** Wire to `main.py` or document as intentionally deferred.

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

### 4. Frontend API Path Mismatches
3 hooks call endpoints at wrong paths (all return 404):

| Hook | Frontend Path | Backend Path |
|------|---------------|--------------|
| `useGameTheory` | `/v1/game-theory/*` | `/game-theory/*` |
| `usePhaseTransitionRisk` | `/exotic-resilience/...` | `/resilience/exotic/...` |
| `useRigidityScore` | `/exotic-resilience/...` | `/resilience/exotic/...` |

**Location:** `frontend/src/hooks/`
**Action:** Fix path prefixes in hooks OR update backend route registration.

---

## HIGH (Address Soon)

### 5. Orphan Framework Code (12K+ LOC)
Built but never integrated into production code paths:

| Module | LOC | Status |
|--------|-----|--------|
| CQRS (`backend/app/cqrs/`) | 4,248 | Full infrastructure, zero usage |
| Saga (`backend/app/saga/`) | 2,142 | Orchestration pattern, unused |
| EventBus (`backend/app/eventbus/`) | 1,385 | Pub/sub, dormant |
| Deployment (`backend/app/deployment/`) | 2,773 | Canary/blue-green, never instantiated |
| gRPC (`backend/app/grpc/`) | 1,775 | Full server, no clients |

**Decision needed:** Integrate into scheduler engine OR remove to reduce maintenance burden.

### 6. Feature Flags Underutilized
- **Location:** `backend/app/features/` - 45KB of production-ready code
- **Actual usage:** 1 flag (`swap_marketplace_enabled` in `portal.py`)
- **Should flag:** Labs hub, 3D visualizations, experimental scheduling algorithms

### 7. MCP Tool Placeholders (16 tools)

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

### 8. GUI Components Using Mock Data (10 components)

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

---

## MEDIUM (Plan for Sprint)

### 9. Admin Activity Logging
- `admin_users.py:77` - `_log_activity()` is no-op placeholder
- `admin_users.py:596` - Returns empty response pending table creation
- **Need:** Alembic migration for `activity_log` table

### 10. Invitation Emails
- `admin_users.py:236, 552` - Emails not actually sent
- **Need:** Wire EmailService to notification tasks

### 11. Service Layer Pagination
- `absence_controller.py:45` - Pagination applied at controller level
- **Need:** Push to service/repository for SQL LIMIT/OFFSET efficiency

### 12. Documentation Consolidation
- **68 root-level .md files** (PRIORITY_LIST.md recommended 5-8)
- Stale timestamps: openapi.yaml (Dec 31), ENDPOINT_CATALOG.md (Jan 4)
- Many docs reference files that no longer exist

---

## LOW (Backlog)

### 13. A/B Testing Infrastructure
- **Location:** `backend/app/experiments/`
- Infrastructure exists, route registered
- Minimal production usage - consider for Labs rollout

### 14. ML Workload Analysis
- `ml.py` returns "placeholder response"
- Low priority unless ML features requested

### 15. Time Crystal DB Loading
- `time_crystal_tools.py:281, 417`
- Acceptable fallback to empty schedules
- Fix if `schedule_id` parameter becomes primary use case

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
| **CRITICAL** | 4 | 6 orphan routes, PII in history, doc contradictions, 3 API path mismatches |
| **HIGH** | 4 | 12K LOC orphan frameworks, feature flags, 16 MCP stubs, 10 mock GUI components |
| **MEDIUM** | 4 | Activity logging, emails, pagination, doc consolidation |
| **LOW** | 3 | A/B testing, ML, time crystal |

### Biggest Wins (Impact vs Effort)

1. **Wire 6 orphan routes** → Unlock SSO, sessions, profiling (LOW effort, HIGH impact)
2. **Fix 3 API path mismatches** → Unlock game theory, exotic resilience features (LOW effort, HIGH impact)
3. **Decide on CQRS/Saga/EventBus** → 12K LOC to integrate or remove (MEDIUM effort)
4. **Fix doc contradictions** → Restore trust in documentation (LOW effort)
5. **Expand feature flag usage** → Labs, 3D viz behind flags (LOW effort)
6. **Wire mock dashboards** → Real data for ResilienceOverseer, SovereignPortal (MEDIUM effort)

---

*This document consolidates findings from TODO_INVENTORY.md, PRIORITY_LIST.md, TECHNICAL_DEBT.md, and ARCHITECTURAL_DISCONNECTS.md. Keep this as the authoritative source.*
