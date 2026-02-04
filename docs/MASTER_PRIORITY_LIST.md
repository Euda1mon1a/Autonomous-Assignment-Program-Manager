# MASTER PRIORITY LIST - Codebase Audit

> **Generated:** 2026-01-18
> **Last Updated:** 2026-02-03 (Admin GUI gaps partially closed; Codex App automation triage skill documented)
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

### 1. PII in Git History
- Resident names in deleted files (BLOCK_10_SUMMARY.md, AIRTABLE_EXPORT_SUMMARY.md) still in history
- Requires `git filter-repo` + force push to main
- All collaborators must re-clone after

**Ref:** `docs/archived/superseded/TODO_INVENTORY.md` line 6 (archived)

### 2. MCP Production Security (PRODUCTION GATE)
**Status:** ✅ Checklist documented (PR #801) — run during deploy

**Requirement:** Production deployments MUST set `MCP_API_KEY` environment variable.

**Context:** `MCP_ALLOW_LOCAL_DEV=true` in `docker-compose.dev.yml` bypasses all auth checks for dev convenience. This is intentional - Docker network detection is fragile and dev environments shouldn't require auth debugging.

**Production Checklist:** See `docs/security/MCP_PRODUCTION_SECURITY_CHECKLIST.md`

**Without `MCP_API_KEY`:** Server fails closed for non-local requests (returns 500).

**Ref:** PR #764, Session 136

---

## HIGH (Address Soon)

### 4. Block 10 Schedule Generation - PARTIAL (Activity Solver OK)
**Status:** CP-SAT ✅ | Activity Solver ✅ | Backend Export ⚠️ (partial) | Frontend Export ✅

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

**References:**
- `docs/reports/block10-cpsat-run-20260127.md`
- `docs/scheduling/CP_SAT_CANONICAL_PIPELINE.md`

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

### Phase 6 — CP-SAT Hardening + Equity + Excel Staging (In Progress)
**Status:** In progress (PR #784 merged; PR #785 merged — Excel staging + draft flow)
**Doc:** [`docs/planning/CP_SAT_PIPELINE_REFINEMENT_PHASE6.md`](planning/CP_SAT_PIPELINE_REFINEMENT_PHASE6.md)

**Highlights:**
1. ACGME compliance truth alignment (remove stub, validator‑driven)
2. External rotation time‑off intake (FMIT/IMW/Peds patterns) — **In progress** (PR #784)
   - GUI time‑off patterns now applied to inpatient preloads (#784)
   - Temporary default: Saturday off for external/inpatient rotations until refined
   - Remaining: confirm ICU/NICU/L&D authoritative day‑off rules
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

### 7. Pre-commit Hook Failures (Session 128) - MYPY PROGRESS
**Updated:** 2026-01-24 (Session 139)

Pre-commit hooks blocking commits due to pre-existing issues:

| Hook | Issue | Scope | Progress |
|------|-------|-------|----------|
| **mypy** | 6,443 type errors | 742 files | 13.2% fixed (983 errors) |
| **bandit** | 0 high severity, config in pyproject.toml | Merged (Sessions 154-155) | ✅ Complete |
| **Modron March** | FairnessAuditResponse location | Type in wrong file | TODO |

**mypy Progress (Sessions 137-139):**
| Session | Start | End | Fixed | % |
|---------|-------|-----|-------|---|
| 137 R1 | 7,426 | 6,880 | 546 | 7.3% |
| 137 R2 | 6,880 | 6,440 | 440 | 6.4% |
| 139 | 6,678 | 6,443 | 235 | 3.5% |
| **Total** | 7,426 | 6,443 | **983** | **13.2%** |

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
3. Install bandit: `pip install bandit`
4. Update Modron March to check correct type locations

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

### ~~11. No DB-Schema Drift Detection~~ — RESOLVED
See [COMPLETED section](#11-no-db-schema-drift-detection-high-11--resolved-2026-01-31)

### ~~12. API Test Coverage Gap~~ — RESOLVED
See [COMPLETED section](#12-api-test-coverage-gap-high-12--resolved-2026-01-31)

### 14. Admin GUI Backend Gaps (NEW - Session 156)
**Added:** 2026-02-01
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
| No pre-push hook | Missing | Dangerous ops reach remote |
| ~~24 sequential phases~~ | D&D hooks parallel, others sequential | ~~15-30s~~ Improved |
| MyPy/Bandit advisory | `|| true` patterns | Bugs/security issues slip through |

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

### 20. Skills-Tools Rationalization (NEW - Session 136)
**Added:** 2026-01-23
**Source:** [Skills-Tools Rationalization](reports/SKILLS_TOOLS_RATIONALIZATION_2026-01-23.md)

| Category | Count | Action |
|----------|-------|--------|
| Skills → MCP Tools | 3 | `coverage-reporter`, `changelog-generator`, `check-camelcase` |
| Skills → Call MCP Tools | 4 | `SWAP_EXECUTION`, `COMPLIANCE_VALIDATION`, etc. |
| Skills → RAG | 5 | `hierarchy`, `parties`, `python-testing-patterns` |
| Redundancies | 4 | `startupO-legacy`, `deep-research`+`devcom` |

**Missing Skill:** `check-camelcase` referenced in CLAUDE.md but skill doesn't exist.

### 24. Preload Service Code Duplication (NEW - Session 142)
**Added:** 2026-01-25
**Source:** Codex CP-SAT Review (`docs/reviews/CODEX_CPSAT_REVIEW_20260125.md`)

`preload_service.py` (async) and `sync_preload_service.py` (sync) have ~300 LOC of identical rotation pattern logic:

| Duplicated Code | LOC | Purpose |
|-----------------|-----|---------|
| `_ROTATION_ALIASES` | 15 | Alias normalization |
| `_NIGHT_FLOAT_ROTATIONS`, etc. | 10 | Exempt rotation sets |
| `_get_hilo_codes()` | 8 | Hilo TDY pattern |
| `_get_kap_codes()` | 10 | Kapiolani pattern |
| `_get_nf_codes()` | 8 | Night float pattern |
| `_resolve_rotation_code_for_date()` | 40 | Mid-block transitions |
| `_get_rotation_preload_codes()` | 50 | Pattern dispatcher |

**Also includes magic numbers:**
```python
if day_index in (0, 1):   # Thu/Fri before Hilo TDY
if day_index == 19:       # Return Tuesday
```

**Fix:**
1. Extract to `backend/app/services/rotation_pattern_utils.py`
2. Replace magic numbers with named constants
3. Both services import shared logic

**Effort:** 2-3 hours

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

**Action:** Add `[MOCK]` prefix to tool descriptions until backend services exist.

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

## SUMMARY

| Priority | Open | Resolved |
|----------|------|----------|
| **CRITICAL** | 2 | 6 |
| **HIGH** | 7 | 9 |
| **MEDIUM** | 16 | 11 |
| **LOW** | 13 | 3 |
| **TOTAL** | **38** | **29** |

### Top 5 Actions for Next Session

1. **Purge PII from Git History** (CRITICAL #1) - `git filter-repo` + force push + re-clone
2. **MCP Production Security Checklist** (CRITICAL #2) - set `MCP_API_KEY`, lock ports
3. ~~**Add DB-Schema Drift Tests** (HIGH #11)~~ ✅ Resolved (PR #796)
4. ~~**Add Resilience Route Tests** (HIGH #12)~~ ✅ Resolved (PR #797)
5. **Resolve ACGME Compliance Gaps** (HIGH #5) - merge call_assignments into rest checks

### Blind Spot Assessment Items (2026-01-27)

| # | Item | Effort | Priority |
|---|------|--------|----------|
| 28 | Exception Handling Audit | 4-6h | MEDIUM |
| 29 | Transaction Boundary Audit | 4-6h | MEDIUM |
| 30 | Async/Sync Doc Fix | 30m | MEDIUM |
| 31 | CP-SAT Integration Tests | 4-8h | MEDIUM |

**Reference:** [SOFTWARE_CONCEPTS_MEDICAL_ANALOGIES.md](development/SOFTWARE_CONCEPTS_MEDICAL_ANALOGIES.md)

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
