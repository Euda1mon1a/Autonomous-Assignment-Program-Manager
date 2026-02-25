# MASTER PRIORITY LIST - Codebase Audit

> **Generated:** 2026-01-18
> **Last Updated:** 2026-02-25 (MEDIUM #33 Office.js AI-Navigable Excel Add-in)
> **Authority:** This is the single source of truth for codebase priorities.
> **Supersedes:** TODO_INVENTORY.md, PRIORITY_LIST.md, TECHNICAL_DEBT.md, ARCHITECTURAL_DISCONNECTS.md
> **Methodology:** Full codebase exploration via Claude Code agents (10 parallel agents, Session 136)
>
> **Session 136 Audit Reports:**
> - [API Coverage Matrix](reports/API_COVERAGE_MATRIX_2026-01-23.md) - 84 routes, 752+ endpoints, 53% tested
> - [Security Posture](reports/SECURITY_POSTURE_2026-01-23.md) - 1 Critical, 4 High, 3 Medium
> - [DB-Schema Alignment](reports/DB_SCHEMA_ALIGNMENT_AUDIT_2026-01-23.md) - 87 models, 12 missing, 7 orphaned
> - [Skills Audit](reports/SKILLS_AUDIT_2026-01-23.md) - 92 skills, 7.6/10 average
> - [MCP Tools Audit](reports/MCP_TOOLS_AUDIT_2026-01-23.md) - 137 tools, 10 placeholders
> - [Skills-Tools Rationalization](reports/SKILLS_TOOLS_RATIONALIZATION_2026-01-23.md) - Consolidation plan

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
| 4 | MEDIUM | Standing orders dispersed across identity cards *(identity cards archived -- see `.claude/archive/identities/`)* |
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

### 1. PII in Git History
- Resident names in deleted files (BLOCK_10_SUMMARY.md, AIRTABLE_EXPORT_SUMMARY.md) still in history
- Requires `git filter-repo` + force push to main
- All collaborators must re-clone after

**Ref:** `docs/archived/superseded/TODO_INVENTORY.md` line 6 (archived)

### 2. MCP Production Security (PRODUCTION GATE)
**Status:** ✅ Checklist documented (PR #801) — run during deploy

**Requirement:** Production deployments MUST set `MCP_API_KEY` environment variable.

**Context:** `MCP_ALLOW_LOCAL_DEV=true` in `docker-compose.local.yml` bypasses all auth checks for dev convenience. This is intentional - Docker network detection is fragile and dev environments shouldn't require auth debugging.

**Production Checklist:** See `docs/security/MCP_PRODUCTION_SECURITY_CHECKLIST.md`

**Without `MCP_API_KEY`:** Server fails closed for non-local requests (returns 500).

**Ref:** PR #764, Session 136

---

## HIGH (Address Soon)

### 3. CP-SAT FMIT Fri/Sat Call Missing (NEW - Feb 2026)
**Status:** ✅ Fixed locally; pending verification in main + MCP parity

**Symptom (prior):** No Friday/Saturday call entries in `call_assignments`, so FMIT faculty call was not represented as call. PCAT/DO only existed for Sun–Thu calls.

**Root Cause (confirmed):**
- Solver call variables are **only created for Sun–Thu**.
- Preload sync **creates FMIT Fri/Sat `call_assignments`**, but the engine cleared
  the entire `call_assignments` range after the solver, **wiping FMIT Fri/Sat**.

**Local Fix Applied (2026-02-05):**
1. Preserve FMIT Fri/Sat `call_assignments` when clearing the call table
   (derive dates from `inpatient_preloads`).
2. Ensure FMIT call preload creation is **faculty-only** (parity with async preload service).

**Verification Required:**
1. Regenerate call assignments; confirm Fri/Sat call appears in `call_assignments`.
2. Confirm PCAT/DO remains correct (skip if still on FMIT).
3. Update MCP/API tooling to mirror direct Docker behavior.

### 3.1. CP-SAT Infeasible With 98% Preassigned (NEW - Feb 2026)
**Status:** Active - blocks regeneration
**Report:** [`docs/reports/cpsat-call-preload-and-schema-drift-20260205.md`](reports/cpsat-call-preload-and-schema-drift-20260205.md)

**Symptom:** CP-SAT returns **INFEASIBLE** for 2026-03-12 → 2026-04-08.

**Evidence (Docker logs):**
- 98% of slots pre-assigned; multiple residents at **40/40 workday blocks**.
- `ExistingAssignmentPreservation` hard-locks **664** assignments.
- Missing templates: **DO, NF, PC, PCAT, SM** (constraints disabled).
- NF headcount uses template name match; existing assignments show **4 NF‑named templates per block**, violating `NF_CONCURRENT_MAX = 1`.
- Diagnostic run with `ResidentInpatientHeadcount` disabled still **INFEASIBLE** → broader constraint conflict remains.

**Updated root cause (2026‑02‑05):**
- Minimal infeasible hard set (ddmin) = `OvernightCallCoverage` + `CallAvailability`.
- Stale **PCAT/DO preloads** lock next‑day slots (e.g., 2026‑03‑13), leaving **zero** eligible faculty for 2026‑03‑12 call.
- Fix implemented locally: clear stale faculty PCAT/DO preloads when `skip_faculty_call=True`
  (`SyncPreloadService._clear_faculty_call_preloads`).
- **Post‑fix status:** Full Docker regen (clear → preload → CP‑SAT → activity solver) returns **partial** (not infeasible), with **3 supervision ratio** violations remaining.  
   Run ID: `b0d947e2-9b78-4c55-9754-a6e7188362f8` (2026‑02‑05 20:02).  
   Call assignments: **28** (20 weekday + 8 weekend).
 - **Solver log note:** `No faculty_at or faculty_pcat variables, supervision constraint not applied` (likely reason for supervision gaps).

**Action (Documented):**
1. Validate that locked assignments don’t violate hard constraints (1-in-7, 80-hr, supervision).
2. Confirm preassignments are not stale solver output.
3. If needed, introduce **soft** preservation with high penalty or clear stale solver output before solve.

### 3.5. DB Schema Drift (NEW - Feb 2026)
**Status:** Alembic head sync **FAIL** per stack health audit (2026-02-19)

**Symptoms:**
- Missing tables in DB (models exist): `calendar_subscriptions`, `export_jobs`, `export_job_executions`, `oauth2_authorization_codes`, `pkce_clients`, `schema_change_events`, `schema_versions`, `state_machine_instances`, `state_machine_transitions`, `webhooks`, `webhook_deliveries`, `webhook_dead_letters`.
- Extra tables in DB: Continuum version tables (`*_version`, `transaction`) and legacy tables (`schedule_versions`, `schedule_diffs`, `metric_snapshots`, `chaos_experiments`, `faculty_activity_permissions`).
- **Feb 19 audit:** DB current revision = `20260205_add_credential_flag_type`, head = `20260218_drafts_ver_tbl`. Two new migrations merged since (composite query indexes + AI budget tables) which extend the chain further.

**Action:**
1. Run `alembic upgrade head` on live DB to sync all pending migrations.
2. Confirm which missing tables are **intentional/optional** vs required.
3. Add migrations for required tables.
4. **Do not prune** tables unless they cause active issues.

### 4. Block 10 Schedule Generation - PARTIAL (Activity Solver OK)
**Status:** CP-SAT ✅ | Activity Solver ✅ | Backend Export ⚠️ (partial) | Frontend Export ✅
**Block 12 Prep:** Started — see `docs/scheduling/BLOCK12_SCHEDULE_LOAD.md` and preflight script (PR #1160)

**Latest Run (2026-01-27):**
- CP-SAT solver generated **589** rotation assignments + **20** call nights
- Activity solver status: **OPTIMAL** (~0.13s), **455** activities assigned
- Outpatient slots to assign: **455**
- Physical capacity constraints applied to **40/40** time slots (soft 6 / hard 8)
- Activity min shortfall total: **1** (soft penalty)
- Post-call PCAT/DO gap persists (expected in dev)
- Weekly CV ratio (faculty+PGY‑3, FMC clinic only): **22.22% / 28.57% / 25.00% / 29.41%**
  - Solver slots alone hit ~30.77% each week; preloaded C lowers overall ratio.

**Root Cause Observed (resolved):**
- Capacity infeasibility (2026-04-01 AM) resolved by:
  - Preloading inpatient clinic from weekly patterns
  - **Proactive CV target** for faculty + PGY‑3 (not fallback)

**New (2026-01-29):**
- Credentialed procedures now linked via `activities.procedure_id` (VAS/VASC/SM).
- VAS/VASC allocator + activity solver use `procedure_credentials` with competency-based priority.

**New (2026-02-06):**
- Human-facing schedule verification: [`docs/guides/SCHEDULE_ALIGNMENT_QUESTIONNAIRE.md`](guides/SCHEDULE_ALIGNMENT_QUESTIONNAIRE.md)
- 15-min coordinator checklist for expected vs actual alignment

**References:**
- `docs/reports/block10-cpsat-run-20260127.md`
- `docs/scheduling/CP_SAT_CANONICAL_PIPELINE.md`
- `docs/guides/SCHEDULE_ALIGNMENT_QUESTIONNAIRE.md` (NEW - verification checklist)

**Immediate Action:**
1. Review **activity min shortfall** (1 total) and decide if acceptable.
2. Address **post-call PCAT/DO** gap (Step 4 in `cpsat-open-questions`).
3. Address **1-in-7/rest-period** warnings (time-off templates not in solver context).
4. Continue policy decisions in `docs/reports/cpsat-open-questions-20260127.md`.

### 5. ACGME Compliance Validation Gaps
Call duty and performance profiling have edge cases:

| Issue | Location | Status |
|-------|----------|--------|
| `call_assignments` excluded from 24+4/rest checks | `acgme_compliance_engine.py:231,273` | ⏸️ Deferred - Pending MEDCOM ruling |

**Action:** Merge call_assignments into shift validation (pending MEDCOM ruling on ACGME interpretation).

### 6. Faculty Scheduling Pipeline Gaps

**Doc:** [`docs/reports/FACULTY_ASSIGNMENT_PIPELINE_AUDIT_20260120.md`](reports/FACULTY_ASSIGNMENT_PIPELINE_AUDIT_20260120.md)

Status update:
- ✅ Canonical faculty schedule table = `half_day_assignments`
- ✅ Faculty half‑day activities now generated by **global CP‑SAT solver**
- ✅ Legacy faculty expansion service archived

Remaining faculty-specific gaps:
- Weekly min/max clinic parameters exist but are not enforced in constraints (beyond solver limits)
- 4 faculty have no weekly templates; overrides are effectively empty

**Action:**
1. Enforce or normalize weekly clinic min/max limits and fix template coverage gaps

### 9. Lock Window + Break-Glass Publish Gate (NEW - Feb 2026)
**Status:** Phase 1 complete; Phase 2 UI complete; Phase 3 in progress

**Why:** Protect near-term schedules from solver/import/resilience churn while still allowing urgent changes with explicit approval.

**Policy Summary:**
- Lock date stored in DB (GUI editable); dates on or before lock date are locked.
- System-initiated changes can be staged but **cannot be published** without break-glass approval.
- Manual edits allowed for Coordinator/Admin with audit (current decision).
- Swaps inside lock window require break-glass even if user-initiated.
- Break-glass requires reason + Coordinator/Admin approval + full re-validation.

**Docs:**
- `docs/specs/LOCK_WINDOW_BREAK_GLASS_SPEC.md`
- `docs/roadmaps/LOCK_WINDOW_BREAK_GLASS_ROADMAP.md`
- `docs/resilience/LOCK_WINDOW_BREAK_GLASS_POLICY.md`

**Immediate Action:**
1. Phase 3: Resilience workflows (stage + gated publish)
2. Phase 3: Imports (lock-window flag injection)
3. Optional: Break-glass notifications (Slack/email)

### Phase 6 — CP-SAT Hardening + Equity + Excel Staging (In Progress)
**Status:** In progress (PR #784 merged; PR #785 merged — Excel staging + draft flow)
**Doc:** [`docs/planning/CP_SAT_PIPELINE_REFINEMENT_PHASE6.md`](planning/CP_SAT_PIPELINE_REFINEMENT_PHASE6.md)

**Highlights:**
1. ACGME compliance truth alignment (remove stub, validator‑driven)
2. External rotation time‑off intake (FMIT/IMW/Peds patterns) — **Complete** (PR #784 + ICU/NICU/L&D backfill)
   - GUI time‑off patterns now applied to inpatient preloads (#784)
   - Saturday-off weekly patterns backfilled for ICU/NICU/L&D (`backend/scripts/backfill_weekly_patterns_saturday_off.py`)
   - Temporary default: Saturday off for external/inpatient rotations until refined
3. Excel staging + diff metrics (measure manual vs automated changes)
   - ✅ Block Template2 staging + diff preview + draft endpoints (PR #785)
   - ✅ Draft creation is atomic; `failed_ids` surfaced on failure
4. Institutional events table (USAFP/holidays/retreats)
5. Equity + preferences:
   - Faculty equity by role (GME/DFM/AT/C)
   - LEC/ADV + Sunday/weekday call equity across the board
   - Holiday equity for FMIT + call
   - Resident equity across all assignments (block/week/assignment)
   - 2 soft preferences per faculty (clinic + call)

**Solver Lockdown (GUI Readiness) — Priority Subset**
1. **CP-SAT only in production paths** (API + enums)
   - Reject non‑cp_sat in prod config
   - Hide non‑cp_sat options from `/enums/scheduling-algorithms`
2. **Faculty immutability guard**
   - Activity solver must require explicit override to touch faculty slots
   - Add test: faculty assignments unchanged after activity solver
3. **Resident eligibility regression**
   - Test that `requires_procedure_credential` does *not* block residents

**Secondary Hardening**
4. Locked slots are forced to zero (add regression test)
5. Call assignment integrity across all blocks (weekends included)

### 7. Pre-commit Hook Failures (Session 128) - MYPY PROGRESS
**Updated:** 2026-02-19 (stack health audit)

Pre-commit hooks blocking commits due to pre-existing issues:

| Hook | Issue | Scope | Progress |
|------|-------|-------|----------|
| **mypy** | 4,347 type errors | 742 files | 41.5% fixed (3,079 errors) |
| **bandit** | 0 high severity, config in pyproject.toml | Merged (Sessions 154-155) | ✅ Complete |
| **Modron March** | FairnessAuditResponse location | Type in wrong file | ✅ Fixed (PR #838) |

**mypy Progress (Sessions 137-139 + Feb 2026):**
| Session | Start | End | Fixed | % |
|---------|-------|-----|-------|---|
| 137 R1 | 7,426 | 6,880 | 546 | 7.3% |
| 137 R2 | 6,880 | 6,440 | 440 | 6.4% |
| 139 | 6,678 | 6,443 | 235 | 3.5% |
| Feb 2026 | 6,443 | 4,347 | 2,096 | 28.2% |
| **Total** | 7,426 | 4,347 | **3,079** | **41.5%** |

**Feb 19 audit note:** mypy baseline=4390, current=4347, delta=-43 (within tolerance). Cumulative reduction from 7,426 → 4,347 = 41.5% fixed.

**Ref:** [`docs/scratchpad/session-139-mypy-parallel-fixes.md`](scratchpad/session-139-mypy-parallel-fixes.md)

**Top Error Patterns (for bulk fix):**
| Pattern | Est. Count | Fix |
|---------|------------|-----|
| `no-untyped-def` | ~2,000 | Add `-> None` or `-> Type` |
| `var-annotated` | ~1,500 | Add `: Type` to variables |
| SQLAlchemy Column | ~1,000 | `cast(Type, model.attr)` |

**Recommended Next Approach:** Bulk sed/awk for common patterns instead of one-by-one fixes.

**Action:**
1. Bulk fix `-> None` patterns with sed
2. Bulk fix SQLAlchemy Column casts

**✅ Resolved sub-items:** bandit added to requirements.txt (PR #839), Modron March fixed (PR #838)

### 8. Orphan Framework Code (12K+ LOC) - ANALYSIS COMPLETE
Production-quality infrastructure built for future scaling. Analyzed 2026-01-18:

| Module | LOC | Quality | Recommendation |
|--------|-----|---------|----------------|
| **CQRS** (`backend/app/cqrs/`) | 4,248 | Full impl, 1 test file | **ROADMAP** - Keep for multi-facility scaling |
| **Saga** (`backend/app/saga/`) | 2,142 | Full impl with compensation | **EVALUATE** - Useful for swap workflows |
| **EventBus** (`backend/app/eventbus/`) | 1,385 | Generic Redis pub/sub | **INVESTIGATE** - External integrations |
| **Deployment** (`backend/app/deployment/`) | 2,773 | Blue-green + canary | **EVALUATE** - Zero-downtime deploys |
| **gRPC** (`backend/app/grpc/`) | 1,775 | Full server, JWT auth | **EVALUATE** - MCP/external integrations |

**Decision:** Keep all modules on roadmap. Integrate as features require.

### 14. Admin GUI Backend Gaps (NEW - Session 156)
**Added:** 2026-02-01
**Updated:** 2026-02-19 — Admin service status dashboard merged (PR #1174)
**Source:** Backend/DB GUI readiness assessment

Backend is **90% ready** (90 routes, 63 models, comprehensive CRUD). These gaps block full admin GUI:

| Gap | Impact | Effort | Status |
|-----|--------|--------|--------|
| **Swap approval workflow** | Swaps execute immediately; no approve/deny stage | 4-6h | ⏳ Pending |
| **Leave approval workflow** | Leave created; no approval/denial flow | 4-6h | ⏳ Pending |
| **Dashboard aggregate endpoints** | No summary widgets (counts, trends) | 2-4h | ✅ Done (PR #804) |
| **Cascading delete warnings** | No endpoint warns about dependent records | 2-3h | ✅ Done (PR #804) |
| **Field-level change tracking** | Activity log tracks actions, not field diffs | 4-6h | ⏳ Pending |

**What's Ready:**
- ✅ All CRUD operations (users, people, blocks, rotations, assignments, leave, swaps)
- ✅ Bulk operations with dry-run and validation
- ✅ Enumeration endpoints for dropdowns (PR #794)
- ✅ Pagination and filtering on list endpoints
- ✅ Audit trails and activity logging
- ✅ Real-time WebSocket support
- ✅ Rate limiting and DoS protection
- ✅ Dashboard aggregates (`/api/v1/admin/dashboard/summary`)
- ✅ Delete-impact warnings (`/api/v1/admin/delete-impact`)

**Missing Enums (hardcode in frontend for now):**
- User roles: `admin, coordinator, faculty, resident, clinical_staff, rn, lpn, msa`
- User status: `active, inactive, locked, pending`
- Absence reasons: free text (no enum)
- Leave types: free text (no enum)

**Action:**
1. Implement swap approval workflow (new `swap_status` state machine)
2. Implement leave approval workflow (new `leave_status` state machine)
3. Add field-level change tracking (audit diffs per update)

**Files to modify:**
- `backend/app/services/swap_service.py` (approval workflow)
- `backend/app/services/absence_service.py` (leave approval workflow)
- `backend/app/services/activity_log_service.py` (field-level diff capture)

### 15. K2.5 Swarm MCP Integration (NEW - Session Phase 8)
**Added:** 2026-01-30
**Design:** [`docs/planning/K2_SWARM_MCP_INTEGRATION.md`](planning/K2_SWARM_MCP_INTEGRATION.md)
**Analysis:** [`docs/research/AGENT_ARCHITECTURE_COMPARISON.md`](research/AGENT_ARCHITECTURE_COMPARISON.md)

Integrate Kimi K2.5 Agent Swarm as a managed execution asset for parallel bulk work.

| Tool | Purpose |
|------|---------|
| `k2_swarm_spawn_task` | Send task to 100-agent swarm |
| `k2_swarm_get_result` | Poll completion, get patches/files/analysis |
| `k2_swarm_apply_patches` | Selective apply with dry-run default |

**Architecture:** AAPM orchestrates → K2.5 executes in parallel → Results returned as drafts for review → Claude/human approves before commit.

**First Use Case:** Mypy bulk fix (4,250 errors across 742 files)
- Highly parallelizable (each file independent)
- Clear success metric (error count reduction)
- Low-risk patches (type annotations)

**Prerequisites:**
- [ ] Moonshot API account with swarm access (`platform.moonshot.ai`)
- [ ] `MOONSHOT_API_KEY` environment variable
- [ ] MCP tool implementation

**Files:**
- `mcp-server/src/scheduler_mcp/k2_swarm/` (new module)

**Effort:** 4-6 hours implementation + testing

### 16. MCP Clear-Existing Does Not Clear Half-Day Assignments (NEW - Feb 2026)
**Status:** Gap in MCP cleanup after successful local runs

**Symptom:** Schedule generation becomes **INFEASIBLE/partial** after repeated runs because stale `half_day_assignments` (sources `solver`/`template`) persist even when MCP `clear_existing` is used.

**Cause:** MCP client deletes `assignments` only; `half_day_assignments` cleanup runs only after a successful solve, so failed/partial runs leave stale solver/template rows.

**Action:**
1. Update MCP client to clear `half_day_assignments` (sources `solver`/`template`) for the target date range.
2. Document interim Docker/SQL cleanup procedure for admins.
3. Add integration test to ensure MCP `clear_existing` clears both tables.

### 17. Local-First Runtime Refactor (Mac mini) (NEW - Feb 2026)
**Status:** Proposed
**Roadmap:** [`docs/roadmaps/LOCAL_FIRST_REFACTOR_ROADMAP.md`](roadmaps/LOCAL_FIRST_REFACTOR_ROADMAP.md)

Mac mini is now the primary execution environment. Runtime defaults should be
local-first, with Docker/Render paths treated as optional compatibility only.

**Target Outcomes:**
1. One-command local stack boot is authoritative.
2. Scripts/tests/hooks stop assuming container-first runtime.
3. README/setup/ops docs prioritize local runbook first.

**Immediate Action:**
1. Execute Phases 0-2 from the roadmap (bootstrap, runtime defaults, script consolidation).
2. Run local smoke verification (auth, schedule validation, resilience, MCP).
3. Complete docs handoff and keep Docker as fallback only.

### 18. Stack Health RED — Alembic Head Sync (NEW - Feb 2026)
**Added:** 2026-02-19
**Source:** Stack health audit `2026-02-19_122157.md`

**Status:** FAIL — DB revision is `20260205_add_credential_flag_type`, head is `20260218_drafts_ver_tbl`. Multiple migrations pending.

**Current migration chain (post-merge):**
```
20260218_drafts_ver_tbl → 20260219_composite_query_idx → 20260219_ai_budget_tables
```

**Related audit findings:**
| Check | Status |
|-------|--------|
| Alembic Head Sync | FAIL |
| Migration State | WARN (pending migrations) |
| Docker Containers | WARN (not running) |
| API Health | WARN (unreachable) |
| Sacred Backups | WARN (none found) |

**Action:**
1. Run `alembic upgrade head` on live DB — verify all tables created.
2. Address Docker/API unavailability during audit (may be transient).
3. Create at least one sacred backup per backup policy.
4. Re-run stack audit to confirm GREEN or identify remaining blockers.

### 19. Budget Cron Manager Wiring (NEW - Feb 2026)
**Added:** 2026-02-19
**Source:** Mini branch triage Wave 2 cherry-pick (PR #1177)

**Status:** Code merged, not wired into production paths.

Budget-aware cron manager tracks Opus API usage costs with Redis real-time tracking + PostgreSQL persistence. Code is complete but:
- Budget routes **not registered** in `app/main.py`
- Celery beat schedule **not configured** for periodic budget tasks (rollup, alerting)
- Redis keys (`ai_budget:*`) exist but no periodic reader invokes them

**Files:**
- `backend/app/services/budget_cron_manager.py` — Core manager (merged + fixed: persisted config, rollup month)
- `backend/app/tasks/budget_tasks.py` — Celery tasks
- `backend/alembic/versions/20260219_add_ai_budget_tables.py` — Migration (merged + fixed: server_default)

**Action:**
1. Register budget router in `app/main.py` (if admin endpoints exist)
2. Add Celery beat schedule entries for daily/monthly rollup tasks
3. Verify Redis key structure matches manager expectations
4. Test end-to-end: log usage → daily rollup → monthly report → threshold alerts

### 20. "No CLI" Execution Phases (NEW - Feb 2026)
**Added:** 2026-02-19
**Source:** `docs/reports/REPO_STATE_PLAIN_ENGLISH_2026-02-19.md`

Three-phase plan to eliminate CLI dependency for all operations:

| Phase | Timeline | Target |
|-------|----------|--------|
| **1** | 2-4 weeks | Web-first for daily scheduling ops (imports, exports, swaps, compliance) |
| **2** | 6-10 weeks | Admin operations mostly in UI (health, migrations, backups, job controls) |
| **3** | 10-16 weeks | Never-CLI — terminal optional even for upgrades, recovery, and incidents |

**Phase 1 blockers:**
- Clear RED audit status (Item 18)
- Remove fallback-only behavior for core admin health
- Close key UX reliability gaps (error boundaries, loading state consistency)

**Phase 2 blockers:**
- Guided UI flows for migration status, backup management, recovery checks
- Guardrails and confirmation workflows for risky actions

**Phase 3 blockers:**
- One-click upgrade and rollback paths
- In-app incident runbooks and recovery tooling
- Production-hardening and security closure for critical findings

**Confidence:** Medium — RED health status adds uncertainty. Security and migration debt can introduce hidden work.

### 21. Working Branches With Committed Files — RESOLVED (Feb 2026)
**Added:** 2026-02-20
**Resolved:** 2026-02-21

| Branch | Disposition |
|--------|------------|
| `feature/empty-table-features` | ✅ Merged as PR #1182 |
| `feat/schedule-vision-research` | ✅ Superseded by PR #1187 (merged) |
| `docs/repo-state-report-feb19` | Stale — can be deleted |
| `feat/ml-training-deployment` | ✅ Merged as PR #1187 |
| `feat/phase7-block-level-constraints-gh` | ✅ Merged as PR #1188 |
| `docs/ml-integration-status-and-branch-triage` | Closed (PR #1186, superseded) |

All local branches deleted, remote refs pruned.

### 22. MCP Server Reliability — MOSTLY RESOLVED (Feb 2026)
**Added:** 2026-02-20
**Status:** ✅ Server-side fixed (PR #1184); ✅ Client-side config fix documented

**Server-Side (PR #1184 — merged):**
- ✅ `scripts/watchdog-mcp.sh` — Health check + double-fork auto-restart daemon
- ✅ `com.aapm.mcp-watchdog` launchd agent — 60s interval, RunAtLoad, auto-restart
- ✅ Port corrected: 8081 → 8080 in `_native-lib.sh` and `start-native.sh`
- ✅ `/mcp-recovery` skill created (45th skill) with 7 recovery procedures
- ✅ Health endpoint: `curl -sf http://127.0.0.1:8080/health`

**Client-Side (config fix — this session):**
- ✅ Root cause: Claude Code reads MCP config from `~/.claude.json` (per-project local scope) with highest priority, not `~/.claude/config.json`
- ✅ Fix: `claude mcp add --transport http --scope local residency-scheduler http://127.0.0.1:8080/mcp`
- ✅ Transport: Streamable HTTP (`--transport http`), NOT SSE or stdio. Server uses FastMCP 2.x `mcp.http_app(stateless_http=True)`
- ✅ Documented in: `MCP_SETUP.md`, `MCP_IDE_INTEGRATION.md`, `/mcp-recovery` skill (Recovery #7)

**Remaining:**
- Monitor for memory leaks over time (97+ tools, RAG vector store)
- Consider circuit breaker between MCP → backend for cascade failure prevention

**Files:**
- `scripts/watchdog-mcp.sh` — Watchdog daemon
- `~/Library/LaunchAgents/com.aapm.mcp-watchdog.plist` — launchd config
- `.claude/skills/mcp-recovery/SKILL.md` — Recovery skill (7 procedures)
- `docs/development/MCP_SETUP.md` — Setup + troubleshooting
- `docs/development/MCP_IDE_INTEGRATION.md` — IDE config

---

## MEDIUM (Plan for Sprint)

### 10. Service Layer Pagination
- `absence_controller.py:45` - Pagination applied at controller level
- **Need:** Push to service/repository for SQL LIMIT/OFFSET efficiency

### 11. Hooks and Scripts Consolidation
**Priority:** MEDIUM
**Roadmap:** [`docs/planning/HOOKS_AND_SCRIPTS_ROADMAP.md`](planning/HOOKS_AND_SCRIPTS_ROADMAP.md)
**Updated:** 2026-01-26 (Session 141)

**✅ Verified Aligned (2026-01-26):**
- All 15 pre-commit scripts exist and match config
- D&D hooks (Couatl Killer, Beholder Bane, Gorgon's Gaze) run in parallel
- CLAUDE.md documents all 5 D&D patterns + enforcement

| Gap | Current State | Impact |
|-----|---------------|--------|
| MyPy/Bandit advisory | `|| true` patterns | Bugs/security issues slip through |

**✅ Resolved sub-items:**
- Pre-push hook: Githyanki Gatekeeper merged (PR #837)
- Sequential phases: D&D hooks now parallel

**Human Decisions Required:**
- [ ] Approve full parallel pre-commit approach
- [ ] Decide GPG signing policy

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

### 20. Skills-Tools Rationalization (NEW - Session 136)
**Added:** 2026-01-23
**Source:** [Skills-Tools Rationalization](reports/SKILLS_TOOLS_RATIONALIZATION_2026-01-23.md)

| Category | Count | Action |
|----------|-------|--------|
| Skills → MCP Tools | 3 | `coverage-reporter`, `changelog-generator`, `check-camelcase` |
| Skills → Call MCP Tools | 4 | `SWAP_EXECUTION`, `COMPLIANCE_VALIDATION`, etc. |
| Skills → RAG | 5 | `hierarchy`, `parties`, `python-testing-patterns` |
| Redundancies | 4 | `startupO-legacy`, `deep-research`+`devcom` |

✅ `check-camelcase` skill created (PR #839)

**NOTE (2026-02-06):** Codex implemented faculty clinic floor constraints in activity solver (commit `000fa24d`, branch `codex/excel-export-functional-20260206`):
- Faculty clinic min/max caps now enforced with **hard floor (>=1)** + **soft penalty** for min shortfall
- Legacy fallback added: reads `clinic_min`/`clinic_max` from DB if weekly template missing
- **P1 Follow-up:** Raw SQL in `_get_legacy_clinic_caps_for_person` should be migrated to ORM for maintainability

### 25. Activity Solver Physical Capacity Overflow (NEW - Session 142)
**Added:** 2026-01-26
**Source:** Block 10 regen report (`docs/reports/block10-cpsat-run-20260126.md`)

Activity solver now skips physical-capacity constraints for most slots because
minimum clinic demand exceeds the hard cap of 6 (e.g., 15–16 required).

**Impact:**
- Activity solver succeeds, but capacity is unenforced for ~35/40 slots in Block 10.
- Policy decision needed: soft constraint vs FM-clinic-only vs per-activity caps.

**Fix:**
1. Decide capacity scope (FM clinic only vs all clinical activities).
2. Consider soft-penalty model if hard caps are routinely exceeded.
3. Align `counts_toward_physical_capacity` flags with policy.

**Effort:** 2-4 hours

### 26. Supervision Activity Metadata Validation (NEW - Session 142)
**Added:** 2026-01-26
**Source:** Block 10 regen report (`docs/reports/block10-cpsat-run-20260126.md`)

AT coverage now uses `Activity.requires_supervision` + `Activity.provides_supervision`
instead of narrow code lists. If these flags are incorrect or incomplete, AT
coverage constraints will under/over-count demand.

**Fix:**
1. Audit clinical activities for `requires_supervision=True`.
2. Ensure AT/PCAT/DO (and SM clinic if applicable) have `provides_supervision=True`.
3. Add a validation check for missing supervision flags on clinical activities.

**Effort:** 1-2 hours

### 27. MCP Placeholder Tools (NEW - Session 136)
**Added:** 2026-01-23
**Source:** [MCP Tools Audit](reports/MCP_TOOLS_AUDIT_2026-01-23.md)

10 MCP tools return mock data instead of real backend integration:

| Tool | Backend Service Needed |
|------|----------------------|
| `analyze_homeostasis_tool` | `HomeostasisService.check_homeostasis()` |
| `get_static_fallbacks_tool` | `ResilienceService.get_fallback_schedules()` |
| `execute_sacrifice_hierarchy_tool` | `ResilienceService.execute_sacrifice()` |
| `calculate_blast_radius_tool` | `BlastRadiusService.calculate()` |
| (6 more) | See PLACEHOLDER_IMPLEMENTATIONS.md |

~~**Action:** Add `[MOCK]` prefix to tool descriptions until backend services exist.~~ ✅ Done (PR #839) — 10 tools labeled `[MOCK]`

### 28. Exception Handling Audit (NEW - Blind Spot Assessment)
**Added:** 2026-01-27
**Source:** Blind spot assessment (`.claude/plans/deep-foraging-starfish.md`)
**Reference:** [SOFTWARE_CONCEPTS_MEDICAL_ANALOGIES.md](development/SOFTWARE_CONCEPTS_MEDICAL_ANALOGIES.md)

Found 20+ instances of exception swallowing pattern:
```python
except Exception as e:
    logger.error(f"Something failed: {e}")
    # continues execution  ← silent failure
```

**Affected files:**
- `solver_control.py` - 8 instances
- `free_energy_integration.py` - 3 instances
- `solvers.py` - several instances

**Risk:** Silent failures hide bugs until downstream effects appear. Errors logged but not surfaced.

**Medical analogy:** Like logging critical lab values to a file nobody checks - patient continues until they code.

**Fix options:**
1. **Fail loudly:** `raise` after logging (crash on error)
2. **Explicit recovery:** Document and handle specific exceptions with fallbacks

**Action:** Audit each `except Exception` and decide: fatal or explicit recovery?

**Effort:** 4-6 hours

### 29. Transaction Boundary Audit (NEW - Blind Spot Assessment)
**Added:** 2026-01-27
**Source:** Blind spot assessment (`.claude/plans/deep-foraging-starfish.md`)
**Reference:** [SOFTWARE_CONCEPTS_MEDICAL_ANALOGIES.md](development/SOFTWARE_CONCEPTS_MEDICAL_ANALOGIES.md)

`engine.py` has 13+ calls to `commit()`, `flush()`, `rollback()` scattered throughout, suggesting:
1. Transaction boundaries evolved organically
2. Partial commits possible (some data saved, some not)
3. Rollback may not undo everything expected

**Risk:** Partial schedule commits = data corruption worse than no schedule.

**Medical analogy:** Surgery where power fails mid-procedure - organ removed but nothing closed.

**Files:**
- `backend/app/scheduling/engine.py` - 13+ transaction calls
- `backend/app/scheduling/activity_solver.py` - 1 flush

**Fix:**
1. Map all commit/rollback calls in engine.py
2. Identify transaction boundaries
3. Ensure atomic operations (all-or-nothing)

**Effort:** 4-6 hours

### 30. Async/Sync Documentation Fix (NEW - Blind Spot Assessment)
**Added:** 2026-01-27
**Source:** Blind spot assessment (`.claude/plans/deep-foraging-starfish.md`)
**Reference:** [SOFTWARE_CONCEPTS_MEDICAL_ANALOGIES.md](development/SOFTWARE_CONCEPTS_MEDICAL_ANALOGIES.md)

`BEST_PRACTICES_AND_GOTCHAS.md` states "All database operations MUST be async" but:
- `activity_solver.py` uses sync `Session` (intentionally)
- `engine.py` uses sync `Session` (intentionally)

**This is correct behavior** - scheduler is CPU-bound (like surgery), not I/O-bound. But docs don't reflect this.

**Medical analogy:** API = ED attending (multitask). Scheduler = Surgeon (blocking is expected).

**Fix:** Update `docs/development/BEST_PRACTICES_AND_GOTCHAS.md` Section 4 to clarify:
- API layer: async required
- Scheduler: sync intentional (CPU-bound work)

**Effort:** 30 minutes

### 31. CP-SAT Pipeline Integration Tests (NEW - Blind Spot Assessment)
**Added:** 2026-01-27
**Source:** Blind spot assessment (`.claude/plans/deep-foraging-starfish.md`)
**Reference:** [SOFTWARE_CONCEPTS_MEDICAL_ANALOGIES.md](development/SOFTWARE_CONCEPTS_MEDICAL_ANALOGIES.md)

The MCP validation `await` bug wasn't caught by unit tests - found by operational testing.

**Status (2026-02-04):** Added minimal CP-SAT pipeline integration test at
`backend/tests/scheduling/test_cpsat_pipeline.py` (tiny dataset, call + PCAT/DO assertions).

### 32. Test Infrastructure Quirks Audit (NEW - Session 150)
**Added:** 2026-01-29
**Source:** P5.1 schedule override test failures

FastAPI TestClient has undocumented behavior differences between versioned and non-versioned routes:

| Issue | Symptom | Root Cause |
|-------|---------|------------|
| Query params stripped | `?start_date=...&end_date=...` not reaching handler | TestClient on `/api/*` paths |
| Tests pass locally, fail in CI | Inconsistent path handling | Path prefix routing quirks |

**Discovery:** Tests hitting `/api/admin/schedule-overrides?start_date=...` returned 400 (missing required params). Same tests hitting `/api/v1/admin/schedule-overrides?start_date=...` worked correctly.

**Fix Applied:** Changed all test paths to use `/api/v1/*` versioned routes.

**Action Required:**
1. Audit all route tests for `/api/*` vs `/api/v1/*` consistency
2. Document TestClient path quirk in `BEST_PRACTICES_AND_GOTCHAS.md`
3. Consider adding test helper that enforces versioned paths

**Files:**
- `backend/tests/routes/*.py` - All route test files
- `backend/tests/conftest.py` - Test client fixture

**Effort:** 2-3 hours

**Gap:**
- Unit tests: pass (functions exist, logic correct in isolation)
- Integration tests: sparse (components interacting)
- End-to-end: manual (Codex operational testing)

**Medical analogy:** Unit tests = in vitro (cells in dish). Integration tests = in vivo (whole organism). You can have all proteins working but still have disease.

**Fix:**
1. Add integration test that actually calls MCP validation against real backend
2. Add integration test that runs full CP-SAT pipeline on test data
3. Include in CI pipeline

**Effort:** 4-8 hours

### 33. Office.js AI-Navigable Excel Add-in (NEW - Feb 2026)
**Added:** 2026-02-25
**Roadmap:** [`docs/architecture/OFFICEJS_AI_ROADMAP.md`](architecture/OFFICEJS_AI_ROADMAP.md)
**Depends on:** Excel Stateful Round-Trip Phase 2 (UUID Anchoring)

Office.js add-in that reads the veryHidden metadata sheets (`__SYS_META__`, `__REF__`, `__ANCHORS__`) to enable AI-assisted schedule editing inside Excel on macOS.

| Component | Status |
|-----------|--------|
| `__SYS_META__` + `__REF__` sheets | LIVE (excel_metadata.py) |
| `__ANCHORS__` sheet (UUID + hash) | Code exists, not wired into export |
| Office.js add-in skeleton | NOT STARTED |
| LLM integration (pluggable backend) | NOT STARTED |
| GCC High deployment | NOT STARTED |

**Key Risk:** No offline mode — add-in requires internet. openpyxl + AppleScript pipelines remain primary for disconnected ops.

**Three Sandbox Rules:**
1. `writeScheduleCell()` wrapper auto-clears row hash (LLMs can't MD5)
2. Protected sheet guard refuses writes to `__ANCHORS__`/`__REF__`/`__SYS_META__`
3. Pluggable LLM backend — local/on-prem/GCC High only for CUI data

**Files (future):**
- `office-addin/` — New directory (Yeoman scaffold)
- `backend/app/services/excel_metadata.py` — Add `llm_rules_of_engagement` to ExportMetadata

**Effort:** Phase A (skeleton): 2-3 days. Phase B (LLM): 3-5 days. Phase C (validation): 2-3 days. Phase D (GCC High): 1-2 days.

**Action:** Complete Excel Phase 2 (wire `__ANCHORS__` into export) first. Then scaffold add-in.

---

## LOW (Backlog)

### 16. A/B Testing Infrastructure
- **Location:** `backend/app/experiments/`
- Infrastructure exists, route registered
- Minimal production usage - consider for Labs rollout

### 17. ML Workload Analysis — MOSTLY RESOLVED (Feb 2026)
- ~~`ml.py` returns "placeholder response"~~ ML scorer now wired into LangGraph pipeline (PR #1181)
- **Done:** `ScheduleScorer` ensemble (PreferencePredictor, ConflictPredictor, WorkloadOptimizer) runs as `ml_score` node (node 12) in 13-node LangGraph StateGraph
- **Done:** Schedule-vision pipeline merged (PR #1187) — CatBoost + distillation + multi-AY feature extraction with theme color resolution, 9 rounds of Codex review
- **Done:** Phase 7 block-level constraint calibration merged (PR #1188) — faculty GME/DFM/SM caps, per-activity locked counters, week-scoped requirement keying, 9 rounds of Codex review
- **Remaining:** Models need training data to be fitted; currently gracefully degrades (returns empty scores) when models are unfitted
- **Remaining:** `ml.py` placeholder API endpoint still returns mock data (separate from pipeline scorer)

**Schedule-Vision Pipeline (on main — PR #1187):**

| Script | Purpose |
|--------|---------|
| `scripts/schedule-vision/extract_universal.py` | Multi-AY Excel feature extractor (theme colors, era1/era2 layouts) |
| `scripts/schedule-vision/learn_catboost.py` | CatBoost evaluation (LOAYO + LOBO CV, feature importance, ablation) |
| `scripts/schedule-vision/distill.py` | Knowledge distillation (teacher with RGB → student without) |
| `scripts/schedule-vision/benchmark.py` | Head-to-head comparison vs 68.8% baseline |
| `scripts/ml/export_blocks_json.py` | DB export with source filtering (preload/manual only) |
| `scripts/ml/calibrate_constraints.py` | Constraint calibration from learned data (week-scoped) |
| `scripts/ml/validate_e2e.py` | E2E validation metrics for constraint calibration |

**Next:** Train models on historical data, benchmark against baseline.

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

### 29. Codex Worktree Cleanup (NEW - 2026-02-04)
**Location:** `~/.codex/worktrees/*/Autonomous-Assignment-Program-Manager`
**Status:** Safe to clean after Codex CLI finishes current work

10 worktrees examined. All uncommitted changes are **already merged** via PRs #816/#817:

| Worktree | Base | Changes | Status |
|----------|------|---------|--------|
| 155f | #814 | 6 | Merged in #817 (schedule drafts frontend) |
| 8667 | #817 | 0 | Clean |
| a692 | #817 | 0 | Clean |
| aa99 | #817 | 0 | Clean |
| b0e4 | #814 | 6 | Merged in #817 (resilience draft flags) |
| b55a | #817 | 0 | Clean |
| bad1 | old | 2 | Noise (stack health JSON, npm cache) |
| cb5a | #814 | 2 | Merged in #817 (settings tests) |
| dca9 | #814 | 5 | Merged in #817 (admin dashboard) |
| ddb5 | #814 | 5 | Merged in #817 (swap lock-window) |

**Action when ready:**
```bash
for dir in ~/.codex/worktrees/*/Autonomous-Assignment-Program-Manager; do
  cd "$dir" && git fetch origin main && git reset --hard origin/main && git clean -fd
done
```

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

## SUMMARY

| Priority | Open | Resolved |
|----------|------|----------|
| **CRITICAL** | 2 | 6 |
| **HIGH** | 11 | 10 |
| **MEDIUM** | 17 | 12 |
| **LOW** | 13 | 3 |
| **TOTAL** | **43** | **31** |

### Top 5 Actions for Next Session

1. **Purge PII from Git History** (CRITICAL #1) - `git filter-repo` + force push + re-clone
2. **MCP Production Security Checklist** (CRITICAL #2) - set `MCP_API_KEY`, lock ports
3. **Alembic Head Sync** (HIGH #18) - `alembic upgrade head` + re-run stack audit
4. **Resolve ACGME Compliance Gaps** (HIGH #5) - merge call_assignments into rest checks
5. **CP-SAT Infeasible With Preassigned** (HIGH #3.1) - clear stale preloads, verify regen

### Blind Spot Assessment Items (2026-01-27)

| # | Item | Effort | Priority |
|---|------|--------|----------|
| 28 | Exception Handling Audit | 4-6h | MEDIUM |
| 29 | Transaction Boundary Audit | 4-6h | MEDIUM |
| 30 | Async/Sync Doc Fix | 30m | MEDIUM |
| 31 | CP-SAT Integration Tests | 4-8h | MEDIUM |

**Reference:** [SOFTWARE_CONCEPTS_MEDICAL_ANALOGIES.md](development/SOFTWARE_CONCEPTS_MEDICAL_ANALOGIES.md)

### Session 2026-02-21 Updates

| Change | Item | Reason |
|--------|------|--------|
| ✅ Merged | PR #1187 | ML training pipeline + schedule-vision models (CatBoost, distillation, multi-AY extraction, theme colors, 9 Codex rounds) |
| ✅ Merged | PR #1188 | Phase 7 block-level constraint calibration + faculty GME/DFM/SM caps (per-activity counters, week-scoped keying, 9 Codex rounds) |
| ✅ Closed | PR #1186 | docs: ML integration status — superseded by #1187/#1188 merges |
| 🗑️ Deleted | 8 branches | Stale feature/review branches (feat/ml-training-deployment, feat/phase7-*, pr-1186/1187/1188, etc.) |
| 🗑️ Pruned | 2 remote refs | origin/feat/ml-training-deployment, origin/feat/phase7-block-level-constraints-gh |
| 📝 Updated | HIGH #21 | Working branches → RESOLVED (all merged, closed, or deleted) |
| 📝 Updated | LOW #17 | ML Workload Analysis → MOSTLY RESOLVED (schedule-vision + constraint calibration on main) |

**Codex review rounds (PRs #1187 + #1188 combined):**
- Rounds 2-9 across both PRs
- 27+ Codex bot findings triaged (real bugs, false positives, cross-PR, already fixed)
- Key fixes: fold padding class alignment, LabelEncoder fit, or-falsiness zero-caps, theme color XML, per-activity locked counters, admin_type cap selection, week-scoped requirement keying, export source filtering, class-order validation

### Session 2026-02-20 Updates

| Change | Item | Reason |
|--------|------|--------|
| ✅ Merged | PR #1181 | ML scorer node wired into LangGraph pipeline (13 nodes, 9 Codex review rounds) |
| ✅ Merged | PR #1184 | MCP watchdog with launchd auto-restart (server-side reliability fix) |
| ✅ Created | PR #1183 | Documentation updates for 13-node pipeline (5 files: CP_SAT_CANONICAL_PIPELINE, SCHEDULE_GENERATION_RUNBOOK, ENGINE_ASSIGNMENT_FLOW, ARCHITECTURE, ADR-2026-02-17) |
| ✅ Fixed | MCP client | Root cause: config in `~/.claude/config.json` not picked up; fix: `claude mcp add --transport http --scope local` writes to `~/.claude.json` project key |
| 📝 Updated | HIGH #22 | MCP reliability → MOSTLY RESOLVED (server watchdog + client config fix) |
| 📝 Updated | LOW #17 | ML Workload Analysis → PARTIALLY RESOLVED (scorer in pipeline, models need training) |
| 📝 Updated | 3 docs | MCP_SETUP.md, MCP_IDE_INTEGRATION.md, mcp-recovery skill — client config precedence + transport types |
| ➕ Added | HIGH #21 | Working branches with committed files needing review/rebase (3 branches, all stale on graph files) |
| 📋 Inventoried | 3 branches | `feature/empty-table-features` (4 commits), `feat/schedule-vision-research` (1 commit), `docs/repo-state-report-feb19` (1 commit) |

### Session 2026-02-19 Updates

| Change | Item | Reason |
|--------|------|--------|
| ✅ Merged | PRs #1161-#1170 | `datetime.utcnow()` → `datetime.now(UTC)` migration (10 PRs, all modules) |
| ✅ Merged | PR #1171 | Codex wheat-and-chaff triage branch |
| ✅ Merged | PRs #1172-#1178 | Mini branch triage Wave 2 cherry-picks (keyboard a11y, admin dashboard, loading states, composite indexes, budget cron, VaR/Shapley tests) |
| ✅ Merged | PR #1179 | Mini branch triage report — Wave 2 results |
| ✅ Fixed | PR #1173 | Codex P2: keyboard focus reset on grid dimension shrink |
| ✅ Fixed | PR #1174 | Codex P2: admin dashboard banner ignores degraded dependencies |
| ✅ Fixed | PR #1175 | Codex P2: duplicate `source_week` and `batch_id` indexes removed |
| ✅ Fixed | PR #1177 | Codex P1: persisted config not loaded, rollup reads wrong month, migration server_default |
| ✅ Fixed | PR #1178 | Codex P1 (false positive): stale review on force-pushed branch |
| 🗑️ Deleted | 21 branches | Stale local `claude/2026-02-*` branches |
| 🗑️ Pruned | 8 remote refs | Cherry-pick and docs remote refs |
| 🗑️ Removed | `mini` remote | Unreachable Mac Mini remote |
| ➕ Added | HIGH #18 | Stack Health RED — Alembic head sync FAIL |
| ➕ Added | HIGH #19 | Budget cron manager wiring (code merged, not wired) |
| ➕ Added | HIGH #20 | "No CLI" execution phases (3-phase timeline) |
| 📝 Updated | HIGH #3.5 | DB schema drift now confirmed FAIL per stack audit |
| 📝 Updated | HIGH #7 | mypy 7,426 → 4,347 (41.5% fixed) |
| 📝 Updated | HIGH #14 | Admin status dashboard merged (PR #1174) |
| 📝 Resolved | MEDIUM #24 | Preload service code duplication (PR #1154) |

### Session 2026-02-05 Updates

| Change | Item | Reason |
|--------|------|--------|
| ✅ Merged | PR #813 | `/codex-local-triage` skill |
| ✅ Merged | PR #814 | Security patches + compliance updates |
| ✅ Merged | PR #815 | Exotic visualization revival (6 viz features) |
| ✅ Merged | PR #816 | Faculty credential summaries + RBAC |
| ✅ Merged | PR #817 | Lock-window + break-glass publish gate (Phase 1) |
| ✅ Merged | PR #818 | CP-SAT authority for faculty activities |
| 🗑️ Deleted | 42 branches | Stale local + remote branches (search-party verified) |
| ➕ Added | HIGH #9 | Lock-window + break-glass spec/roadmap/policy |
| ➕ Added | LOW #29 | Codex worktree cleanup (safe to clean) |
| 🔧 In Progress | Codex P1 | #817: Manual drafts bypass break-glass (branch: feat/lock-window-ui) |
| 🔧 In Progress | Codex P2 | #816: Filter expired credentials in summaries (branch: feat/faculty-credential-summary) |

### Session 142 Updates (2026-01-26)

| Change | Item | Reason |
|--------|------|--------|
| ✅ Resolved | MEDIUM #22 | `activity_type` → `rotation_type` rename done (commit 7cd3f4eb) |
| ✅ Resolved | MEDIUM #23 | CP-SAT failure logging improvements |
| ➕ Added | MEDIUM #24 | Preload service code duplication (~300 LOC + magic numbers) |
| ➕ Added | MEDIUM #25 | Activity solver physical-capacity overflow (capacity skipped) |
| ➕ Added | MEDIUM #26 | Supervision activity metadata validation |
| 📝 Added | Review doc | `docs/reviews/CODEX_CPSAT_REVIEW_20260125.md` |
| ✅ Fixed | Block 10 | CP-SAT + activity solver succeed after block-assignment filtering |
| ⚠️ Found | Block 10 | Capacity constraints skipped for 35/40 slots (policy needed) |
| 📝 Added | gitignore | `.claude/dontreadme/sessions/*.md` for session scratchpads |
| 📝 Updated | ops scripts | `block_regen.py` + `block_export.py` now backfill env |

### Session 151 Updates (2026-01-31)

| Change | Item | Reason |
|--------|------|--------|
| ✅ Resolved | HIGH #9 | DoS guardrails merged (PR #793) |
| ✅ Committed | Enums API | `/api/v1/enums/*` for frontend dropdowns (PR #794) |

### Session 155 Updates (2026-02-01)

| Change | Item | Reason |
|--------|------|--------|
| ✅ Merged | PR #798 | Wellness route ordering + analytics fields + docs |
| ✅ Fixed | Wellness routes | `/surveys/history` route ordering, analytics KeyError guard |
| ✅ Updated | CHANGELOG | Session 154 entries for PRs #794-797 |
| ✅ Updated | RATE_LIMIT_AUDIT | Marked upload/schedule rate limits resolved |
| ✅ Updated | ENDPOINT_CATALOG | Added enum endpoints section |

### Session 156 Updates (2026-02-01)

| Change | Item | Reason |
|--------|------|--------|
| ✅ Merged | PR #800 | Kimi K2.5 swarm orchestrator + Codex P2 fixes |
| ✅ Merged | PR #801 | Kimi swarm mypy fixes (22 errors: 4209→4187) + Codex P1/P2 |
| ➕ Added | HIGH #14 | Admin GUI backend gaps (swap/leave approval workflows) |
| 📝 Assessed | Backend readiness | 90% ready for GUI (90 routes, 63 models) |

### Session 154 Updates (2026-01-31)

| Change | Item | Reason |
|--------|------|--------|
| ✅ Resolved | HIGH #11 | Schema drift detection + naming convention added |
| ✅ Resolved | HIGH #12 | API route test coverage (1,720 lines) |
| ✅ Completed | Enum Endpoints | PR #794 - Frontend dropdown endpoints |

### Session 152 Updates (2026-02-01)

| Change | Item | Reason |
|--------|------|--------|
| ✅ Resolved | HIGH #10 | Rate limits added to expensive endpoints |

### Session 150 Updates (2026-01-29)

| Change | Item | Reason |
|--------|------|--------|
| ✅ Committed | Phase 5.0 | Schedule override layer (commit `5826b410`) |
| ✅ Committed | Phase 5.1 | Cascade overrides + GAP + call coverage (commit `7cd4b045`) |
| ➕ Added | MEDIUM #32 | Test infrastructure quirks (TestClient `/api` vs `/api/v1`) |
| 📝 Updated | HIGH Phase 5 | Call + cascade + GAP override complete |

### Session 141 Updates (2026-01-26)

| Change | Item | Reason |
|--------|------|--------|
| ✅ Resolved | API/WS Convention Audit | PRs #758, #760, #765 - full enforcement |
| ✅ N/A | PII in Burnout APIs | Files don't exist (planned, not implemented) |
| 📝 Updated | Bandit hook | Branch ready, needs merge |
| ✅ Verified | Hooks Consolidation | All 15 scripts aligned, D&D parallel |

## COMPLETED / ARCHIVE

### 15. Missing Dependencies in requirements.txt (MEDIUM #15) — RESOLVED (PR #839)
**Added:** 2026-01-23 (Session 136)
**Resolved:** PR #839 — Added `bandit>=1.7.0` and `types-PyYAML>=6.0.0`
**Also consider (future):** Split into `requirements.txt` (core) + `requirements-dev.txt` (testing/linting)

### Mini Branch Triage (Waves 1+2) — COMPLETED (2026-02-19)
**Wave 1:** 19 branches → 5 merged, 8 discarded, 6 modified (PR #1119)
**Wave 2:** 21 branches → 7 cherry-pick PRs (#1172-#1178), 6 discarded
**Total:** 40 branches across 2 waves, 12 PRs created
**Report:** `docs/archived/reports/OPUS_MINI_BRANCH_TRIAGE_REPORT.md`

### datetime.utcnow() Migration — COMPLETED (2026-02-19)
**PRs:** #1161-#1170 (10 PRs covering all backend modules)
**Scope:** All `datetime.utcnow()` → `datetime.now(UTC)`, `utcfromtimestamp()` → `fromtimestamp(tz=UTC)`
**Modules:** core, services, scheduling, resilience, API routes, tasks, MCP server, tests

### 24. Preload Service Code Duplication (MEDIUM #24) — RESOLVED (2026-02-18)
**Added:** 2026-01-25
**Resolved:** PR #1154 — Extracted shared logic into `backend/app/services/preload/` package (6 modules, 565 LOC). Sync service reduced from 1,516 to 1,016 LOC. Zero test regressions.

### 9. DoS Vulnerabilities - Unbounded Queries (HIGH #9) — RESOLVED (2026-01-31)
**Added:** 2026-01-23
**Source:** [Security Posture Report](reports/SECURITY_POSTURE_2026-01-23.md)
**Resolved:** PR #793

| Endpoint | File:Line | Issue |
|----------|-----------|-------|
| `GET /analytics/export/research` | `analytics.py:769` | No max date range, full table scan |
| `GET /analytics/metrics/history` | `analytics.py:185` | No limit clause |
| `GET /schedule/runs` | `schedule.py:1369` | `.all()` loads entire table for count |

**Fixes:**
1. Enforced `MAX_RANGE = timedelta(days=365)` validation
2. Switched to `func.count()` for pagination totals

### 10. Missing Rate Limits on Expensive Endpoints (HIGH #10) — RESOLVED (2026-02-01)
**Added:** 2026-01-23
**Source:** [Security Posture Report](reports/SECURITY_POSTURE_2026-01-23.md)

| Endpoint | Impact |
|----------|--------|
| `POST /schedule/generate` | CPU exhaustion |
| `POST /import/analyze` | File processing exhaustion |
| `POST /exports/{job_id}/run` | Celery queue exhaustion |
| `POST /uploads` | Storage exhaustion |

**Fix:** Added `@limiter.limit("2/minute")` on all listed endpoints.

### 11. No DB-Schema Drift Detection (HIGH #11) — RESOLVED (2026-01-31)
**Added:** 2026-01-23
**Resolved:** PR #796

**Fixes Applied:**
- Added `naming_convention` to `backend/app/db/base.py` (deterministic constraint names)
- Fixed `provides_supervision` and `counts_toward_physical_capacity` persistence in ActivityService

### 12. API Test Coverage Gap (HIGH #12) — RESOLVED (2026-01-31)
**Added:** 2026-01-23
**Resolved:** PR #797

**Coverage Added (1,720 lines):**
- `test_fatigue_risk_routes.py` - 16 endpoints tested
- `test_resilience_routes_smoke.py` - Defense-level, circuit-breakers
- `test_call_assignments_routes_api.py` - CRUD, coverage, bulk, PCAT
- `test_webhooks_routes.py` - CRUD, deliveries, dead-letters
- `test_wellness_routes.py` - Surveys, gamification, admin
- `test_swap_routes_api.py` - Validate, execute, rollback

### Enum Dropdown Endpoints — COMPLETED (2026-01-31)
**Resolved:** PR #794

**New endpoints:** `/api/v1/enums/*`
- `scheduling-algorithms`
- `activity-categories`
- `rotation-types`
- `pgy-levels`
- `constraint-categories`
- `person-types`
- `freeze-scopes`

**Notes:** Enum values aligned to schema validation (e.g., PGY 1–3 only, resident/faculty only).

### 1. Excel Export Silent Failures (CRITICAL #1) — RESOLVED (2026-01-31)
**Added:** 2026-01-23  
**Source:** 10-agent parallel investigation

Block 10 Excel export had multiple silent failure modes causing incomplete/incorrect output:

| Issue | Severity | Location | Impact |
|-------|----------|----------|--------|
| **Row mapping silent skip** | CRITICAL | `xml_to_xlsx_converter.py:397` | Missing people in export - only warning log |
| **Faculty filtered out** | HIGH | `half_day_xml_exporter.py:139` | Faculty never appear in export |
| **Frontend auth bypass** | HIGH | `frontend/src/lib/export.ts:122` | Uses raw `fetch()`, JWT may not be sent |
| **Missing structure XML fallback** | HIGH | `xml_to_xlsx_converter.py:121-123` | Silent wrong row numbering |
| **Fragile name matching** | MEDIUM | `xml_to_xlsx_converter.py:382-394` | First-name matching causes false positives |

**Resolution (2026-01-31):**
- ✅ Canonical JSON export pipeline (`HalfDayJSONExporter` → `JSONToXlsxConverter`)
- ✅ Merged-cell safe writing (headers + schedule cells)
- ✅ Name mapping handles `Last, First` ↔ `First Last`
- ✅ Faculty included in canonical export
- ✅ Backend draft flow: Stage→Preview→Draft→Publish complete (PRs #785, #787, #788)
- ✅ Atomic draft creation with `failed_ids` tracking
- ✅ Bandit security config merged
- ✅ Frontend export auth uses authenticated API client (PR #792)

**Remaining (optional):**
- Add export failure toast in UI (`frontend/src/components/dashboard/QuickActions.tsx`)

**Files:**
- ~~`backend/app/services/xml_to_xlsx_converter.py`~~ ✅
- ~~`backend/app/services/half_day_xml_exporter.py`~~ ✅
- `frontend/src/lib/export.ts` ✅

### 13. Frontend Integration Gaps (HIGH #13) — RESOLVED (2026-01-31)
**Added:** 2026-01-31  
**Source:** Stack readiness assessment (backend 90% ready, frontend 30% → 80%)

| Component | Status | File | Effort |
|-----------|--------|------|--------|
| Excel export auth | ✅ Done | `frontend/src/lib/export.ts` | — |
| Half-day import API | ✅ Done | `frontend/src/api/half-day-import.ts` | — |
| Half-day import UI | ✅ Done | `frontend/src/app/import/half-day/page.tsx` | — |
| Type contracts | ✅ Ready | `frontend/src/types/api-generated.ts` | — |
| Draft API client | ✅ Ready | `frontend/src/api/schedule-drafts.ts` | — |

**Completed (PR #791 + #792):**
- Validation errors vs warnings distinction (errors block draft)
- Preview filters: diff_type, activity_code, has_errors, person_id
- `staged_id` on diff entries for row selection
- Wizard UI at `/import/half-day` with Upload → Preview → Draft flow
- TanStack Query hooks for stage/preview/draft mutations

### Phase 5 — Post-release Coverage Overrides ✅ COMMITTED (Session 150)
**Status:** P5.0 + P5.1 committed (`5826b410`, `7cd4b045`)  
**Doc:** [`docs/planning/CP_SAT_PIPELINE_REFINEMENT_PHASE5.md`](planning/CP_SAT_PIPELINE_REFINEMENT_PHASE5.md)

**Completed:**
1. ✅ Schedule override model (coverage, cancellation, gap types)
2. ✅ Admin-only routes (create, list, deactivate)
3. ✅ Overlay integration (`include_overrides` param)
4. ✅ Call override model + service
5. ✅ Cascade planner with sacrifice hierarchy:
   - GME/DFM → Solo clinic → Procedures → PROTECTED (FMIT/AT/PCAT/DO)
6. ✅ GAP override type for visible unfilled slots
7. ✅ Post-call PCAT/DO auto-GAP creation

**Remaining (optional):**
- [ ] Excel round-trip import creates overrides only (no hard deletes)
- [ ] Resilience-driven cascade scoring (blast radius + contingency)

### ~~22. Rename `activity_type` → `rotation_type`~~ ✅ RESOLVED (2026-01-25)
**Resolved by:** Commit `7cd3f4eb` - 180 files changed, migration `20260126_rename_rotation_type`

Complete rename across entire codebase including DB migration, models, schemas, API, frontend types, solver, and all documentation.

### ~~23. CP-SAT Failure Logging Improvements~~ ✅ RESOLVED (2026-01-26)
**Resolved by:** Commit `9a5c9b19`

Added solver failure diagnostics in `SchedulingEngine`:
- Logs enabled/disabled constraint lists
- Logs context summary (residents, templates, blocks, locked slots)
- Warns on missing key templates (PCAT/DO/SM/NF/PC)

### Archived Resolutions (2026-01-18 → 2026-01-20)

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

### ~~API/WS Convention Audit~~ ✅ RESOLVED (2026-01-26)
~~Full audit completed via PRs #758, #760, #765:~~
- ~~WS messages: Auto snake↔camel conversion (PR #760)~~
- ~~REST query params: 90+ violations fixed (PR #758)~~
- ~~Frontend hooks: 17 hooks fixed~~
- ~~Enforcement: Gorgon's Gaze, Couatl Killer, Modron March hooks~~

### ~~PII in Burnout APIs~~ ✅ N/A (2026-01-26)
~~Security report referenced `contagion_model.py`, `resilience_integration.py` with PII-exposing classes. Investigation found these files/classes don't exist - report was based on planned (not implemented) code.~~

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

---

*This document consolidates findings from TODO_INVENTORY.md, PRIORITY_LIST.md, TECHNICAL_DEBT.md, ARCHITECTURAL_DISCONNECTS.md, and Session 136 audit reports. Keep this as the authoritative source.*
