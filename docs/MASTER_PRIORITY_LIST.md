# MASTER PRIORITY LIST - Codebase Audit

> **Generated:** 2026-01-18
> **Last Updated:** 2026-01-19 (Added: Block 10 GUI Fixes - PR #758)
> **Authority:** This is the single source of truth for codebase priorities.
> **Supersedes:** TODO_INVENTORY.md, PRIORITY_LIST.md, TECHNICAL_DEBT.md, ARCHITECTURAL_DISCONNECTS.md
> **Methodology:** Full codebase exploration via Claude Code agents

---

## PENDING REVIEW

### PAI² Governance Revision Proposal
**File:** [`docs/proposals/PAI2_GOVERNANCE_REVISION_PROPOSAL.md`](proposals/PAI2_GOVERNANCE_REVISION_PROPOSAL.md)
**Date:** 2026-01-18
**Source:** PLAN_PARTY (10 probes) analysis of HUMAN_REPORT

Addresses 7 gaps in PAI² governance framework:

| Gap | Severity | Summary |
|-----|----------|---------|
| 1 | HIGH | No standardized handoff kit ORCH→Deputies |
| 2 | MEDIUM | Exceptions (USASOC/user/subagent) not surfaced |
| 3 | LOW | ORCHESTRATOR not in agents.yaml |
| 4 | MEDIUM | Standing orders dispersed across identity cards |
| 5 | LOW | MCP audit logs not visible in-repo |
| 6 | MEDIUM | /force-multiplier lacks RAG health check |
| 7 | HIGH | No formal offline SOP |

**Decision Required:** Gap 3 has 5/5 probe split - Option A (add to yaml), B (identity only), or C (spawnable:false flag)?

**Action:** Review proposal, make Gap 3 decision, approve phases.

### ADK Integration Analysis
**File:** [`docs/research/ADK_INTEGRATION_ANALYSIS.md`](research/ADK_INTEGRATION_ANALYSIS.md)
**Date:** 2026-01-19
**Source:** PLAN_PARTY (10 probes) analysis of Google ADK TypeScript exploration

Comprehensive disposition matrix for Google ADK integration:

| Tier | Count | Summary |
|------|-------|---------|
| 1 - Immediate | 5 | Tool trajectory scoring, response match scoring, test case framework, Zod patterns, evaluation YAML |
| 2 - Review | 8 | Gemini router, multi-agent orchestration, semantic equivalence, safety eval, TypeScript layer |
| 3 - Skip | 8 | Full Gemini runtime, TypeScript migration, Vertex Enterprise, tool registry duplication |

**Key Finding:** ADK evaluation patterns are additive; ADK tools are redundant (MCP already covers).

**New Skills Recommended:**
- `agent-evaluation` (P1) - Tool trajectory + response match scoring
- `trajectory-analyzer` (P2) - Tool call sequence validation
- `response-matcher` (P3) - Semantic equivalence checking

**Total Effort:** 7-10 days for Tier 1 implementation

**Action:** Review analysis, approve Phase 1 (evaluation framework).

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
| Hopfield Network | ✓ | ✓ | `features/hopfield-energy/` | API ✅ |
| Free Energy | ✓ | ✗ | `features/free-energy/` | API ✅ |
| Energy Landscape | ✓ | ✗ | `features/energy-landscape/` | API ✅ |
| Circadian Phase | ✓ | ✗ | `features/synapse-monitor/` | API ✅ |
| Penrose Efficiency | ✗ | ✗ | Not implemented | - |
| Anderson Localization | ✗ | ✗ | Not implemented | - |
| Persistent Homology | ✗ | ✗ | Not implemented | - |
| Keystone Species | ✗ | ✗ | Not implemented | - |
| Quantum Zeno | ✗ | ✗ | Not implemented | - |
| Stigmergy | ✓ | ✗ | `app/admin/visualizations/stigmergy-flow/` | API ✅ (PR #750) |
| Bottleneck Flow | ✓ | ✗ | `features/bottleneck-flow/` | Mock ✅ (PR #753) |
| Bridge Sync | ✓ | ✗ | `features/bridge-sync/` | Mock ✅ (PR #753) |
| Static Stability | ✓ | ✗ | `features/sovereign-portal/` | API ✅ |
| Le Chatelier | ✗ | ✓ | MCP tool analysis | API |

### 9. ~~GUI Components Using Mock Data~~ ✅ MOSTLY RESOLVED (PR #750)

**Command Center Dashboards - WIRED:**
| Component | Location | Status |
|-----------|----------|--------|
| ResilienceOverseerDashboard | `components/scheduling/` | ✅ Wired to `/resilience/health` |
| SovereignPortal | `features/sovereign-portal/` | ✅ Wired via `hooks.ts` |
| ResilienceLabsPage | `app/admin/labs/resilience/` | ✅ Wired to vulnerability API |

**Labs Visualizations - WIRED:**
| Component | Location | Status |
|-----------|----------|--------|
| Synapse Monitor | `features/synapse-monitor/` | ✅ Wired via `useSynapseData.ts` |
| Fragility Triage | `features/fragility-triage/` | ✅ Wired via `useFragilityData.ts` |
| N-1/N-2 Resilience | `features/n1n2-resilience/` | ✅ Wired via `useN1N2Data.ts` |
| Holographic Hub | `features/holographic-hub/` | ✅ Wired via `hooks.ts` |
| Free Energy | `features/free-energy/` | ✅ New visualizer (PR #750) |
| Energy Landscape | `features/energy-landscape/` | ✅ New visualizer (PR #750) |
| Hopfield Network | `features/hopfield-energy/` | ✅ Fully wired (PR #753) |
| Bottleneck Flow | `features/bottleneck-flow/` | ✅ New visualizer (PR #753) |
| Bridge Sync | `features/bridge-sync/` | ✅ Height fixed (PR #753) |

**Resolved:** 2026-01-18 (PR #750 visualizers, PR #753 Hopfield + Bottleneck + Bridge)

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

### 14. Hooks and Scripts Consolidation
**Priority:** MEDIUM
**Added:** 2026-01-19 (PLAN_PARTY analysis - 10 probes, 8.5/10 convergence)
**Roadmap:** [`docs/planning/HOOKS_AND_SCRIPTS_ROADMAP.md`](planning/HOOKS_AND_SCRIPTS_ROADMAP.md)

Repository automation consolidation addressing performance, reliability, and maintainability gaps:

| Gap | Current State | Impact |
|-----|---------------|--------|
| No pre-push hook | Missing | Dangerous ops reach remote |
| 24 sequential phases | 15-30s commits | Developer friction |
| MyPy/Bandit advisory | `|| true` patterns | Bugs/security issues slip through |
| 3 backup scripts | Overlapping, deprecated | Confusion |
| Claude Code hooks incomplete | No RAG injection | AI workflow suboptimal |

**Phase Overview:**

| Phase | Focus | Owner | Status |
|-------|-------|-------|--------|
| 1 | Quick Wins (parallelize, consolidate, externalize) | COORD_OPS | TODO |
| 2 | Hook Hardening (pre-push, strict MyPy/Bandit) | COORD_TOOLING | TODO |
| 3 | AI Workflow Enhancement (RAG injection, metrics) | COORD_TOOLING | TODO |
| 4 | Compliance Hardening (GPG evaluation, Gitleaks history) | COORD_OPS | TODO |

**Human Decisions Required:**
- [ ] Approve parallel pre-commit approach (Phase 1)
- [ ] Decide GPG signing policy (Phase 4)

**Key Files:** `.pre-commit-config.yaml`, `scripts/pii-scan.sh`, `.claude/hooks/*.sh`

### 15. ~~Block 10 GUI Navigation~~ ✅ RESOLVED (PR #758)
**Priority:** MEDIUM
**Added:** 2026-01-19 (Chrome Extension exploration)
**Branch:** `feat/block10-gui-human-corrections`

Fixed critical issues preventing Block 10 navigation for human review and corrections:

| Issue | Root Cause | Fix |
|-------|------------|-----|
| People API 500 | `performs_procedures` NULL validation | Field validator: NULL → False |
| Block navigation stuck on Block 0 | Cross-year block merging | Group by `academicYear-blockNumber` composite key |
| Couatl Killer violations | camelCase query params | Fixed to snake_case (`start_date`, `end_date`, `block_number`) |

**Root Cause Analysis:**
Block navigation was stuck because blocks from different academic years (AY 2024, AY 2025) had the same `block_number` and were merged by `useBlockRanges`. This created 2-year spans like "Block 0: Jul 1, 2024 - Jul 1, 2026" instead of proper 4-week blocks.

**Files Changed:**
| File | Change |
|------|--------|
| `backend/app/schemas/person.py` | Add `@field_validator("performs_procedures", mode="before")` |
| `frontend/src/hooks/useBlocks.ts` | Add `academicYear` calculation, composite key grouping, snake_case params |
| `frontend/src/api/resilience.ts` | Fix snake_case query params |

**Verification:**
- ✅ Navigate to Block 10 (Mar 13 - Apr 9, 2025)
- ✅ Proper 4-week date ranges
- ✅ People loading (no 500 errors)
- ✅ Schedule assignments visible

**Ref:** PR #758, `.claude/plans/quirky-percolating-feather.md`

### 16. ~~Documentation Consolidation~~ ✅ RESOLVED
Root-level docs reduced from 68 → 28 files.

| Before | After | Change |
|--------|-------|--------|
| 68 root docs | 28 root docs | -40 files consolidated |
| Scattered guides | Consolidated in `docs/development/` | Easier navigation |

**Remaining:** openapi.yaml (Dec 31) timestamp stale, but content accurate.
**Resolved:** 2026-01-18 in `feature/master-priority-implementation`

### 16. ~~CLI and Security Cleanup~~ ✅ RESOLVED
Codex review issues fixed:

| Issue | Location | Status |
|-------|----------|--------|
| Startup log references wrong CLI command | `main.py:145` | ✅ Fixed - Now shows `app.cli user create` |
| Queue whitelist too permissive | `queue.py:65` | ✅ Fixed - Removed `app.services.*` prefix |

**Resolved:** 2026-01-18 in `feature/master-priority-implementation` (commit `8bbb3cb9`)
**Ref:** `docs/reviews/2026-01-17-current-changes-review.md`

### 17. ~~VaR Backend Endpoints~~ ✅ RESOLVED
Endpoints created and wired to MCP tools:
- `POST /api/v1/analytics/coverage-var` - Coverage Value-at-Risk
- `POST /api/v1/analytics/workload-var` - Workload Value-at-Risk
- `POST /api/v1/analytics/conditional-var` - Conditional VaR (CVaR/Expected Shortfall)

**Files added:**
- `backend/app/schemas/var_analytics.py` - Request/response schemas
- `backend/app/services/var_service.py` - VaR calculation service
- `backend/tests/services/test_var_service.py` - Unit tests

**Resolved:** 2026-01-18 in PR #744

### 18. ~~Seed Script Credentials~~ ✅ RESOLVED
Issue identified in code review was based on commit `66a14461` which had hard-coded `AdminPassword123!`.
PR #743 fixed this - now uses `os.environ.get("ADMIN_PASSWORD", "admin123")` matching the app's default.

**Resolved:** 2026-01-18 in PR #743
**Ref:** `docs/reviews/2026-01-18-commit-66a1446-review.md`

---

## LOW (Backlog)

### 19. A/B Testing Infrastructure
- **Location:** `backend/app/experiments/`
- Infrastructure exists, route registered
- Minimal production usage - consider for Labs rollout

### 20. ML Workload Analysis
- `ml.py` returns "placeholder response"
- Low priority unless ML features requested

### 21. Time Crystal DB Loading
- `time_crystal_tools.py:281, 417`
- Acceptable fallback to empty schedules
- Fix if `schedule_id` parameter becomes primary use case

### 22. Spreadsheet Editor for Tier 1 Users (PR #740)
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

### 23. Experimental Analytics Platform (PR #752)
**Priority:** LOW (Future Enhancement)
**Added:** 2026-01-19 (from Claude web session)
**Roadmap:** [`docs/roadmaps/EXPERIMENTAL_ANALYTICS_ROADMAP.md`](roadmaps/EXPERIMENTAL_ANALYTICS_ROADMAP.md)

Comprehensive statistical analytics platform extending `/admin/scheduling` with research capabilities:

| Phase | Focus | Key Components |
|-------|-------|----------------|
| 1 | Data Collection Foundation | Outcome tables, Maslach burnout surveys, Excel import |
| 2 | Statistical Infrastructure | Hypothesis testing, Bayesian (PyMC), Survival analysis (lifelines) |
| 3 | Visualization Components | Kaplan-Meier curves, forest plots, predicted vs actual |
| 4 | Dashboard Tabs | Outcomes, Survival Analysis, A/B Testing, Predictions |
| 5 | Factorial Design | Multi-factor schedule optimization experiments |

**Current State:**
| Component | Status |
|-----------|--------|
| A/B Testing Backend | ✅ Ready (`backend/app/experiments/ab_testing.py`) |
| Scheduling Lab UI | ✅ Ready (1,792 lines) |
| scipy/statsmodels | ⚠️ Underutilized (~30% used) |
| Outcome Data Collection | ❌ Missing |
| Bayesian Framework (PyMC) | ❌ Missing |
| Survival Analysis (lifelines) | ❌ Missing |

**New Dependencies Required:** `pymc`, `arviz`, `lifelines`, `pingouin`

**Research Applications:**
- A/B testing scheduling algorithms with statistical rigor
- Survival analysis for time-to-burnout prediction
- Factorial design for multi-factor optimization
- Predicted vs actual tracking for model accuracy

**Ref:** PR #752, `docs/roadmaps/EXPERIMENTAL_ANALYTICS_ROADMAP.md`

### 24. Claude Code CLI Guide & Vercel Agent Skills (PR #754)
**Priority:** LOW (Reference/Enhancement)
**Added:** 2026-01-19 (from Claude web session)
**Guide:** [`docs/guides/CLAUDE_CODE_CLI_GUIDE.md`](guides/CLAUDE_CODE_CLI_GUIDE.md)

Comprehensive guide covering Claude Code CLI usage and Vercel Agent Skills integration:

| Topic | Content |
|-------|---------|
| Core CLI | Commands, keyboard shortcuts, configuration hierarchy |
| Slash Commands | Custom command creation, built-in commands |
| Hooks System | PreToolUse, PostToolUse, lifecycle automation |
| MCP Integration | Context window management, tool discovery |
| Modes | Interactive, Plan, Background operation |

**Vercel Agent Skills (140+ rules):**
| Skill | Rules | Purpose |
|-------|-------|---------|
| `react-best-practices` | 40+ | React/Next.js performance optimization |
| `web-design-guidelines` | 100+ | Accessibility and UX compliance |

**Installation Commands:**
```bash
npx add-skill vercel-labs/agent-skills --skill react-best-practices -g -a claude-code -y
npx add-skill vercel-labs/agent-skills --skill web-design-guidelines -g -a claude-code -y
```

**Ref:** PR #754, `docs/guides/CLAUDE_CODE_CLI_GUIDE.md`

### 25. String Theory Scheduling (PR #737)
**Priority:** LOW (Research/Exploration)
**Added:** 2026-01-18 (from Claude web session)
**Design:** [`docs/exotic/STRING_THEORY_SCHEDULING.md`](exotic/STRING_THEORY_SCHEDULING.md)

Exploratory design document applying string theory mathematics to scheduling:

| Concept | Scheduling Application |
|---------|----------------------|
| Minimal Surface Optimization | 3D surface minimization vs 1D path optimization |
| Duality Transforms | Multiple equivalent schedule representations |
| Conformal Invariance | Scale-independent pattern validation |
| Worldsheet Dynamics | Resident trajectories as string worldlines |
| Rodriguez-Castillo Algorithm | String theory-inspired meta-heuristic |

**Key Insight:** January 2026 breakthrough showed string theory's minimal surface equations describe biological network optimization - applicable to resource allocation.

**Novel vs Existing:** Higher-order surfaces (vs pairwise relationships), multi-way junctions (vs binary), natural 25% slack margin.

**Ref:** PR #737, `docs/exotic/STRING_THEORY_SCHEDULING.md`

### 26. Optional Modules Assessment
**Priority:** LOW (Reference)
**Added:** 2026-01-18
**Document:** [`docs/planning/OPTIONAL_MODULES_ASSESSMENT.md`](planning/OPTIONAL_MODULES_ASSESSMENT.md)

Comprehensive inventory of optional modules with gap analysis:

**Key Findings:**
- 18+ optional modules already implemented
- 4 modules identified as missing with high potential value
- FHIR integration deprioritized (2+ year horizon)

**Current Modules by Tier:**
| Tier | Category | Count |
|------|----------|-------|
| 1 | AI & Intelligence | 4 (MCP, pgvector/RAG, Ollama, ML Scoring) |
| 2 | Observability | 5 (OpenTelemetry, Prometheus, Grafana, Loki, Exporters) |
| 3 | Integration | 5 (iCal, PDF, Webhooks, Email, Excel) |
| 4 | Development | 3 (K6, Slack Bot, Shadow Traffic) |
| 5 | Infrastructure | 3 (Nginx, S3, Virus Scanning) |

**Missing Modules (Recommended):**
1. Feature Flag System (HIGH priority - noted as now ✅ in item #7)
2. Audit Log Dashboard
3. Schedule Diff Viewer
4. Notification Preferences UI

**Ref:** `docs/planning/OPTIONAL_MODULES_ASSESSMENT.md`

### 27. GUI Considerations (PR #739)
**Priority:** LOW (Reference)
**Added:** 2026-01-18 (from Claude web session)
**Document:** [`docs/development/GUI_CONSIDERATIONS.md`](development/GUI_CONSIDERATIONS.md)

Comprehensive guide for frontend GUI development covering icon libraries, 3D integration, and component patterns:

| Topic | Content |
|-------|---------|
| Icon Libraries | Heroicons (current), Lucide, Material Symbols evaluation |
| 3D Integration | Three.js via react-three-fiber, performance considerations |
| Animation | Framer Motion patterns, reduced-motion accessibility |
| Charts | Recharts (current), Victory, Nivo comparison |
| Component Patterns | Consistent spacing, color tokens, responsive breakpoints |

**Current Stack:**
| Category | Library | Status |
|----------|---------|--------|
| Icons | `@heroicons/react` | ✅ Installed |
| 3D | `@react-three/fiber` | ✅ Installed |
| Charts | `recharts` | ✅ Installed |
| Animation | `framer-motion` | ✅ Installed |

**Identified Gaps:**
- No icon library standardization guide
- Missing 3D performance optimization patterns
- Chart accessibility improvements needed

**Ref:** PR #739, `docs/development/GUI_CONSIDERATIONS.md`

### 28. Cooperative Evolution Research (PR #718)
**Priority:** LOW (Research/Exploration)
**Added:** 2026-01-15 (from Claude web session)
**Document:** [`docs/research/cooperative_evolution_design.md`](research/cooperative_evolution_design.md)

Theoretical foundation for cooperative cell selection in genetic algorithm scheduling:

| Concept | Application |
|---------|-------------|
| Cooperative Fitness Scoring | Base fitness + uplift + coalition patterns |
| NetworkX Coalition Detection | Simplified Shapley value allocation |
| Darwinian Selection Pressure | Evolutionary advantage for cooperators |
| Integration Hooks | Plugs into `backend/app/scheduling/bio_inspired/` GA |

**Expected Emergent Behaviors:**
- Clustering of cooperative agents
- Natural dominance hierarchies
- Self-organizing schedule patterns

**Prerequisites:** `networkx` (already installed), existing GA framework
**Ref:** PR #718, `docs/research/cooperative_evolution_design.md`

### 29. Foam Topology Scheduler (PR #730)
**Priority:** LOW (Research/Exploration)
**Added:** 2026-01-17 (from Claude web session)
**Document:** [`docs/exotic/FOAM_TOPOLOGY_SCHEDULER.md`](exotic/FOAM_TOPOLOGY_SCHEDULER.md)

Design inspired by Penn Engineering research showing foam bubbles continuously reorganize in patterns mirroring AI learning:

| Concept | Scheduling Application |
|---------|----------------------|
| T1 Topological Events | Natural shift swaps (bubble neighbor changes) |
| Foam Coarsening | Assignment consolidation (small bubbles merge) |
| Continuous "Wandering" | Self-healing schedule reorganization |
| Perpetual Soft Reorganization | Complements Hopfield/spin-glass methods |

**Key Insight:** Foam dynamics provide a perpetual soft reorganization paradigm vs rigid constraint solving.

**Design Components:**
- Data structures for foam topology
- Algorithm logic for T1 events
- MCP tool specifications
- Integration with existing resilience framework

**Ref:** PR #730, `docs/exotic/FOAM_TOPOLOGY_SCHEDULER.md`

### 30. ORCHESTRATOR Spec Handoff Pattern (commit 73c74b3c)
**Priority:** LOW (Reference/PAI Enhancement)
**Added:** 2026-01-18 (from Claude web session)
**Document:** [`docs/ORCHESTRATOR_SPEC_HANDOFF.md`](ORCHESTRATOR_SPEC_HANDOFF.md)

Explains seamless subagent launch via prepared AgentSpec handoff:

| Concept | Description |
|---------|-------------|
| Preparation | `spawn_agent_tool` prepares AgentSpec (identity + RAG + mission) |
| Handoff | ORCHESTRATOR reads spec file, runs `Task()` as-is |
| Review | Subagent writes to checkpoint path, ORCHESTRATOR synthesizes |

**Workflow:**
1. **Prepare** (any environment) → Call `spawn_agent_tool`, save spec to scratchpad
2. **Handoff** (ORCHESTRATOR runtime) → Read spec, execute via `Task()`
3. **Review** → Subagent output at checkpoint path

**Constraints:**
- Spawn chain validation: Use Deputy (ARCHITECT/SYNTHESIZER) as parent, not ORCHESTRATOR
- Model selection: From `agents.yaml`, no ad-hoc overrides
- Execution boundary: This environment prepares, ORCHESTRATOR executes

**Suggested Improvements:**
- Add ORCHESTRATOR to `agents.yaml` (aligns with Gap 3 in PAI² proposal)
- Create spec queue directory: `.claude/Scratchpad/specs/`
- Document USASOC/user override exceptions

**Ref:** commit 73c74b3c, `docs/ORCHESTRATOR_SPEC_HANDOFF.md`

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
| **MEDIUM** | 2 open, 7 resolved | ~~activity logging~~✅, ~~emails~~✅, pagination, hooks/scripts, ~~Block 10 GUI~~✅, ~~docs~~✅, ~~CLI/security cleanup~~✅, ~~VaR endpoints~~✅, ~~seed script~~✅ |
| **LOW** | 12 | A/B testing, ML, time crystal, spreadsheet editor, experimental analytics, CLI guide, string theory, optional modules, GUI guide, cooperative evolution, foam topology, ORCH spec handoff |
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
