# MASTER PRIORITY LIST - Codebase Audit

> **Generated:** 2026-01-18
> **Last Updated:** 2026-01-23 (Session 136: Full re-examination, Excel export investigation)
> **Authority:** This is the single source of truth for codebase priorities.
> **Supersedes:** TODO_INVENTORY.md, PRIORITY_LIST.md, TECHNICAL_DEBT.md, ARCHITECTURAL_DISCONNECTS.md
> **Methodology:** Full codebase exploration via Claude Code agents (10 parallel agents, Session 136)

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

### Skills → MCP Tool Wrapping Decision
**File:** [`docs/architecture/SKILLS_RAG_MCP_ARCHITECTURE.md`](architecture/SKILLS_RAG_MCP_ARCHITECTURE.md)
**Date:** 2026-01-22
**Source:** Session 136 architecture analysis

We have three overlapping knowledge mechanisms (Skills, RAG, MCP Tools) with redundancy:

| Mechanism | Context Cost | Reliability | Use Case |
|-----------|--------------|-------------|----------|
| **Skills** | HIGH (5-50K tokens) | 100% complete | Complex workflows, teaching |
| **RAG** | LOW (500-2K tokens) | May miss things | Fact lookups |
| **MCP Tools** | MINIMAL | Deterministic | Validation, execution |

**Tier 1 Candidates (Wrap Soon):**
| Skill | Size | MCP Tool Candidate | Rationale |
|-------|------|-------------------|-----------|
| `/acgme-compliance` | 15KB | `validate_acgme_rules` | Deterministic rule checking |
| `/schedule-validator` | 8KB | `validate_schedule_comprehensive` | Structured validation |
| `/constraint-preflight` | 12KB | `verify_constraint_registration` | Checklist automatable |
| `/swap-analyzer` | 6KB | `analyze_swap_safety` | Compatibility computable |

**Tier 3 (Keep as Skill):**
- `/tamc-excel-scheduling` (43KB) - Complex workflows, many examples
- `/SCHEDULING` (10KB) - Multi-phase orchestration
- `/schedule-optimization` (25KB) - Solver debugging needs full context

**Decision Required:**
1. Approve Tier 1 wrapping candidates
2. Estimate implementation effort
3. Decide layered approach (MCP first → RAG fallback → Skill for complex)

**Benefit:** Reduce context usage by ~50KB/session while maintaining reliability.

---

## CRITICAL (Fix Immediately)

### 1. Excel Export Silent Failures (NEW - Session 136)
**Added:** 2026-01-23
**Source:** 10-agent parallel investigation

Block 10 Excel export has multiple silent failure modes causing incomplete/incorrect output:

| Issue | Severity | Location | Impact |
|-------|----------|----------|--------|
| **Row mapping silent skip** | CRITICAL | `xml_to_xlsx_converter.py:397` | Missing people in export - only warning log |
| **Faculty filtered out** | HIGH | `half_day_xml_exporter.py:139` | Faculty never appear in export |
| **Frontend auth bypass** | HIGH | `frontend/src/lib/export.ts:122` | Uses raw `fetch()`, JWT may not be sent |
| **Missing structure XML fallback** | HIGH | `xml_to_xlsx_converter.py:121-123` | Silent wrong row numbering |
| **Fragile name matching** | MEDIUM | `xml_to_xlsx_converter.py:382-394` | First-name matching causes false positives |

**Why Plan B (Claude for macOS manual):** These silent failures produce incomplete Excel files without user feedback.

**Required Fixes:**
1. Replace silent skip with exception in `xml_to_xlsx_converter.py:397`
2. Add `include_faculty=True` parameter to `HalfDayXMLExporter`
3. Fix frontend auth - use axios instead of raw fetch in `export.ts`
4. Validate row mappings during converter initialization
5. Add user feedback (toast) on export failures

**Files:**
- `backend/app/services/xml_to_xlsx_converter.py`
- `backend/app/services/half_day_xml_exporter.py`
- `frontend/src/lib/export.ts`
- `frontend/src/components/dashboard/QuickActions.tsx`

### 2. PII in Git History
- Resident names in deleted files (BLOCK_10_SUMMARY.md, AIRTABLE_EXPORT_SUMMARY.md) still in history
- Requires `git filter-repo` + force push to main
- All collaborators must re-clone after

**Ref:** `docs/archived/superseded/TODO_INVENTORY.md` line 6 (archived)

### 3. MCP Production Security (PRODUCTION GATE)
**Status:** Dev bypass implemented - production MUST configure auth

**Requirement:** Production deployments MUST set `MCP_API_KEY` environment variable.

**Context:** `MCP_ALLOW_LOCAL_DEV=true` in `docker-compose.dev.yml` bypasses all auth checks for dev convenience. This is intentional - Docker network detection is fragile and dev environments shouldn't require auth debugging.

**Production Checklist:**
- [ ] `MCP_API_KEY` set in production .env (32+ chars, use `python -c 'import secrets; print(secrets.token_urlsafe(32))'`)
- [ ] `MCP_ALLOW_LOCAL_DEV` NOT set (or explicitly `false`)
- [ ] Ports 8080/8081 not exposed to public internet
- [ ] If using reverse proxy, ensure API key header forwarded

**Without `MCP_API_KEY`:** Server fails closed for non-local requests (returns 500).

**Ref:** PR #764, Session 136

---

## HIGH (Address Soon)

### 4. Block 10 Schedule Generation - WORKING but Export Blocked
**Status:** Generation ✅ | Export ⚠️ BLOCKED (see #1)

**What's Working:**
- Block 10 generation: 1,512 half-day assignments (17 residents × 56 slots + 10 faculty × 56 slots)
- 0 NULL activity_id - all assignments have valid activities
- HalfDayXMLExporter reads from `half_day_assignments` table correctly
- XML checkpoint exists for validation

**What's Blocked:**
- xlsx export has silent failures (see CRITICAL #1)
- Faculty excluded from export
- Frontend export may fail due to auth bypass

**Workaround (Plan B):** Manual export via Claude for macOS using XML → Excel transformation

### 5. ACGME Compliance Validation Gaps
Call duty and performance profiling have edge cases:

| Issue | Location | Status |
|-------|----------|--------|
| `call_assignments` excluded from 24+4/rest checks | `acgme_compliance_engine.py:231,273` | ⏸️ Deferred - Pending MEDCOM ruling |

**Action:** Merge call_assignments into shift validation (pending MEDCOM ruling on ACGME interpretation).

### 6. Faculty Scheduling Pipeline Gaps

**Doc:** [`docs/reports/FACULTY_ASSIGNMENT_PIPELINE_AUDIT_20260120.md`](reports/FACULTY_ASSIGNMENT_PIPELINE_AUDIT_20260120.md)

Remaining faculty-specific gaps:
- 2 adjunct faculty have zero Block 10 legacy assignments
- Weekly min/max clinic parameters exist but are not enforced in constraints
- 4 faculty have no weekly templates; overrides are effectively empty

**Action:**
1. Decide canonical schedule table for faculty (prefer half_day_assignments)
2. Wire faculty expansion into half-day pipeline before CP-SAT activity solver
3. Enforce or normalize weekly clinic min/max limits and fix template coverage gaps

### 7. API/WS Convention Audit Required (Session 128)

WebSocket debugging revealed convention violations. Systematic audit needed:

| Audit | Scope | Status |
|-------|-------|--------|
| Full WS audit | All WebSocket messages for case consistency | TODO |
| REST endpoint audit | Query params, request/response bodies | TODO |
| Hook/useX audit | Frontend hooks for snake_case violations | TODO |
| WS smoke test | `GET /api/v1/ws/health` + wscat connect | TODO |

### 8. Pre-commit Hook Failures (Session 128)

Pre-commit hooks blocking commits due to pre-existing issues:

| Hook | Issue | Scope |
|------|-------|-------|
| **mypy** | 100+ type errors | periodic_tasks.py, tensegrity_solver.py, etc. |
| **bandit** | `command not found` | Tool not installed |
| **Modron March** | FairnessAuditResponse location | Type in wrong file |

**Action:**
1. Fix mypy errors systematically (group by file/pattern)
2. Install bandit: `pip install bandit`
3. Update Modron March to check correct type locations

### 9. Orphan Framework Code (12K+ LOC) - ANALYSIS COMPLETE
Production-quality infrastructure built for future scaling. Analyzed 2026-01-18:

| Module | LOC | Quality | Recommendation |
|--------|-----|---------|----------------|
| **CQRS** (`backend/app/cqrs/`) | 4,248 | Full impl, 1 test file | **ROADMAP** - Keep for multi-facility scaling |
| **Saga** (`backend/app/saga/`) | 2,142 | Full impl with compensation | **EVALUATE** - Useful for swap workflows |
| **EventBus** (`backend/app/eventbus/`) | 1,385 | Generic Redis pub/sub | **INVESTIGATE** - External integrations |
| **Deployment** (`backend/app/deployment/`) | 2,773 | Blue-green + canary | **EVALUATE** - Zero-downtime deploys |
| **gRPC** (`backend/app/grpc/`) | 1,775 | Full server, JWT auth | **EVALUATE** - MCP/external integrations |

**Decision:** Keep all modules on roadmap. Integrate as features require.

---

## MEDIUM (Plan for Sprint)

### 10. Service Layer Pagination
- `absence_controller.py:45` - Pagination applied at controller level
- **Need:** Push to service/repository for SQL LIMIT/OFFSET efficiency

### 11. Hooks and Scripts Consolidation
**Priority:** MEDIUM
**Roadmap:** [`docs/planning/HOOKS_AND_SCRIPTS_ROADMAP.md`](planning/HOOKS_AND_SCRIPTS_ROADMAP.md)

| Gap | Current State | Impact |
|-----|---------------|--------|
| No pre-push hook | Missing | Dangerous ops reach remote |
| 24 sequential phases | 15-30s commits | Developer friction |
| MyPy/Bandit advisory | `|| true` patterns | Bugs/security issues slip through |

**Human Decisions Required:**
- [ ] Approve parallel pre-commit approach (Phase 1)
- [ ] Decide GPG signing policy (Phase 4)

### 12. Admin Debugger - Database Inspector Enhancement
**Priority:** MEDIUM
**Branch:** `feature/activity-assignment-session-119`

Database Inspector now supports multiple data types but Activities view has upstream API issue.

| View | Status | Notes |
|------|--------|-------|
| Schedule | ✅ Working | 702 assignments for Block 10 |
| Absences | ✅ Working | 100 absences with type filtering |
| People | ✅ Working | 33 people with search, type filter |
| Rotations | ✅ Working | 87 templates in grid layout |
| Activities | ⚠️ API Issue | Code validator too strict for 'LV-PM' |

### 13. Templates Hub - Unified Template Management
**Status:** UI COMPLETE - DB population pending (Session 131-132)
**Branch:** `feature/rotation-faculty-templates`

| Component | Status |
|-----------|--------|
| Main page structure | ✅ Complete |
| RotationsPanel | ✅ Complete |
| MySchedulePanel | ✅ Complete |
| FacultyPanel | ✅ Complete |
| MatrixPanel | ✅ Complete |
| BulkOperationsPanel | Pending |

### 14. Block 10-13 Rotation Template Population
**Priority:** HIGH (Next DB work)
**Status:** SCHEMA PREP COMPLETE - Awaiting schedule generation
**Backup:** `backups/20260122_102856_Pre-Codex half-day rotation template values/`

**✅ SCHEMA PREP COMPLETE (2026-01-22):**
1. ✅ DB backup created
2. ✅ Cleared `half_day_assignments`: 1,524 → 0 rows
3. ✅ Added 32 new activity codes: 51 → 83 total
4. ✅ Verified Block 10 rotations (17 residents)
5. ✅ Verified faculty weekly templates (10 faculty)

**Next:** Run schedule generation (preload + solver)

### 15. Missing Dependencies in requirements.txt
**Priority:** LOW (Quick Fix)
**Added:** 2026-01-23 (Session 136)

Pre-commit hooks fail due to missing dependencies:

| Package | Issue | Fix |
|---------|-------|-----|
| `bandit` | Pre-commit `command not found` | Add `bandit>=1.7.0` |
| `types-PyYAML` | mypy missing stubs error | Add `types-PyYAML>=6.0.0` |

**Also consider:**
- Split into `requirements.txt` (core) + `requirements-dev.txt` (testing/linting)
- Heavy ML deps (`sentence-transformers`, `transformers`) could be optional

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

### 19. Spreadsheet Editor for Tier 1 Users (PR #740)
Excel-like grid editor for schedule verification.

| Feature | Status |
|---------|--------|
| Grid display | Specified |
| Click-to-edit | Specified |
| SheetJS export | Library installed (`xlsx@0.20.2`) |
| ACGME validation | Specified |
| Keyboard nav | ~3-4 days implementation |

### 20. Experimental Analytics Platform (PR #752)
**Roadmap:** [`docs/roadmaps/EXPERIMENTAL_ANALYTICS_ROADMAP.md`](roadmaps/EXPERIMENTAL_ANALYTICS_ROADMAP.md)

| Phase | Focus |
|-------|-------|
| 1 | Data Collection Foundation |
| 2 | Statistical Infrastructure (PyMC, lifelines) |
| 3 | Visualization Components |
| 4 | Dashboard Tabs |
| 5 | Factorial Design |

### 21. Claude Code CLI Guide & Vercel Agent Skills (PR #754)
**Guide:** [`docs/guides/CLAUDE_CODE_CLI_GUIDE.md`](guides/CLAUDE_CODE_CLI_GUIDE.md)
- 140+ Vercel Agent Skills rules documented
- React/Next.js performance patterns

### 22. String Theory Scheduling (PR #737)
**Design:** [`docs/exotic/STRING_THEORY_SCHEDULING.md`](exotic/STRING_THEORY_SCHEDULING.md)
- Minimal surface optimization for scheduling
- Research/exploration priority

### 23. Optional Modules Assessment
**Document:** [`docs/planning/OPTIONAL_MODULES_ASSESSMENT.md`](planning/OPTIONAL_MODULES_ASSESSMENT.md)
- 18+ optional modules already implemented
- 4 modules identified as missing

### 24. GUI Considerations (PR #739)
**Document:** [`docs/development/GUI_CONSIDERATIONS.md`](development/GUI_CONSIDERATIONS.md)
- Icon libraries, 3D integration, animation patterns

### 25. Cooperative Evolution Research (PR #718)
**Document:** [`docs/research/cooperative_evolution_design.md`](research/cooperative_evolution_design.md)
- Genetic algorithm scheduling with cooperative fitness

### 26. Foam Topology Scheduler (PR #730)
**Document:** [`docs/exotic/FOAM_TOPOLOGY_SCHEDULER.md`](exotic/FOAM_TOPOLOGY_SCHEDULER.md)
- Foam dynamics for perpetual soft reorganization

### 27. Jupyter IDE Integration for Empirical Evaluation
**Status:** Not started

Set up Jupyter notebook integration via Claude Code IDE tools for empirical data analysis.

| Use Case | Benefit |
|----------|---------|
| Scheduling vs Resilience A/B testing | Side-by-side metrics |
| ACGME violation pattern analysis | Coverage heatmaps |
| Constraint debugging | Interactive traces |
| Algorithm parameter tuning | Iterate without rerunning solver |

### 28. ORCHESTRATOR Spec Handoff Pattern
**Document:** [`docs/ORCHESTRATOR_SPEC_HANDOFF.md`](ORCHESTRATOR_SPEC_HANDOFF.md)
- Seamless subagent launch via prepared AgentSpec

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
| Feature Flags | ✅ Real | Infrastructure complete |
| Fairness Suite | ✅ Production | Lorenz, Shapley, Trends fully wired |
| Block 10 Generation | ✅ Working | 1,512 assignments, 0 NULL activities |
| HalfDayXMLExporter | ✅ Working | Reads from half_day_assignments |

---

## ~~COMPLETED~~ (Archived)

### ~~Orphan Security Routes~~ ✅ RESOLVED (2026-01-18)
~~6 routes now wired to API (commit `b92a9e02`):~~
- ~~`sso.py` → `/api/v1/sso`~~
- ~~`audience_tokens.py` → `/api/v1/audience-tokens`~~
- ~~`sessions.py` → `/api/v1/sessions`~~
- ~~`profiling.py` → `/api/v1/profiling`~~
- ~~`claude_chat.py` → `/api/v1/claude-chat`~~
- ~~`scheduler.py` → `/api/v1/scheduler-jobs`~~

### ~~Documentation Contradictions~~ ✅ RESOLVED (2026-01-18)
~~Contradictions fixed - TECHNICAL_DEBT.md, ARCHITECTURAL_DISCONNECTS.md, PRIORITY_LIST.md, TODO_INVENTORY.md all updated.~~

### ~~Frontend API Path Mismatches~~ ✅ RESOLVED (2026-01-18)
~~3 hooks fixed (commit `b92a9e02`):~~
- ~~`useGameTheory` → `/game-theory/*`~~
- ~~`usePhaseTransitionRisk` → `/resilience/exotic/...`~~
- ~~`useRigidityScore` → `/resilience/exotic/...`~~

### ~~Schedule Rollback Data Loss~~ ✅ RESOLVED (2026-01-18)
~~Fixed in commits `66a14461` and `8bbb3cb9`:~~
- ~~`_find_existing_assignments()` captures both AM+PM~~
- ~~Full provenance serialization~~
- ~~All 3 restoration paths restore all fields~~

### ~~Feature Flags~~ ✅ RESOLVED (2026-01-18)
~~5 flags with backend gating on 17 exotic resilience endpoints. All endpoints have `current_user` injection.~~

### ~~MCP Tool Placeholders (16 tools)~~ ✅ RESOLVED (2026-01-18)
~~16/16 tools now wired to backend. All MCP resilience tools working with real backend.~~

### ~~GUI Components Using Mock Data~~ ✅ RESOLVED (PR #750, #753)
~~Command Center Dashboards and Labs Visualizations all wired to real APIs.~~

### ~~Half-Day Pipeline & Weekend Fixes~~ ✅ RESOLVED (Sessions 125-126)
~~Major fixes: PCAT/DO creation, cross-block handling, mid-block transitions, weekend patterns.~~

### ~~Wiring Standardization Gaps~~ ✅ RESOLVED (Session 129-130)
~~DefenseLevel mapping, enum values documented, Docker proxy routing, Suspense boundaries all fixed.~~

### ~~Admin Activity Logging~~ ✅ RESOLVED (2026-01-18)
~~Fully implemented with migration, logging function, and API endpoint.~~

### ~~Invitation Emails~~ ✅ RESOLVED (2026-01-18)
~~Working via `render_email_template()` + `send_email.delay()`.~~

### ~~Block 10 GUI Navigation~~ ✅ RESOLVED (PR #758)
~~Fixed: People API 500, cross-year block merging, Couatl Killer violations.~~

### ~~Documentation Consolidation~~ ✅ RESOLVED (2026-01-18)
~~Root-level docs reduced from 68 → 28 files.~~

### ~~CLI and Security Cleanup~~ ✅ RESOLVED (2026-01-18)
~~Startup log fixed, queue whitelist tightened.~~

### ~~VaR Backend Endpoints~~ ✅ RESOLVED (2026-01-18)
~~3 endpoints created: coverage-var, workload-var, conditional-var.~~

### ~~Seed Script Credentials~~ ✅ RESOLVED (2026-01-18)
~~Now uses `os.environ.get()` instead of hardcoded password.~~

### ~~Docker Bind Mounts~~ ✅ RESOLVED (2026-01-18)
~~Switched from named volumes to `./data/postgres/`, `./data/redis/` for visibility.~~

### ~~Academic Year Fix~~ ✅ RESOLVED (2026-01-18)
~~`block_quality_report_service.py` derives academic year from block start date.~~

### ~~psutil Dependency~~ ✅ RESOLVED (2026-01-18)
~~Added `psutil>=5.9.0` to requirements.txt.~~

### ~~GUI + Wiring Review (PR #756)~~ ✅ RESOLVED (2026-01-20)
~~Verified GUI fixes, identified and fixed remaining wiring gaps.~~

---

## SUMMARY

| Priority | Open | Resolved |
|----------|------|----------|
| **CRITICAL** | 3 | 4 |
| **HIGH** | 6 | 5 |
| **MEDIUM** | 6 | 9 |
| **LOW** | 13 | 3 |
| **TOTAL** | **28** | **21** |

### Top 5 Actions for Next Session

1. **Fix Excel Export Silent Failures** (CRITICAL #1) - Blocking production use
2. **Fix Frontend Export Auth** - `export.ts` using raw fetch instead of axios
3. **Add Faculty to XML Export** - Currently filtered out
4. **Run Block 10-13 Schedule Generation** - Schema prep done, ready for solver
5. **Complete API/WS Convention Audit** - Prevent future wiring issues

---

*This document consolidates findings from TODO_INVENTORY.md, PRIORITY_LIST.md, TECHNICAL_DEBT.md, and ARCHITECTURAL_DISCONNECTS.md. Keep this as the authoritative source.*
