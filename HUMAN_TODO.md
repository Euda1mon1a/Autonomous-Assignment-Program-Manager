# Human TODO

> Tasks that require human action (external accounts, manual configuration, etc.)
> **Open items: ~26 | Archived: 31** (cleaned 2026-02-10)

---

## Native Excel Formatting Check — Visual QA Script 4 (2026-02-25)

**Priority:** Low
**Status:** Blocked (needs non-empty export data)

**Context:** Chrome MCP Visual QA Script 4 (`docs/prompts/CHROME_MCP_VISUAL_QA.md`) verifies conditional formatting renders correctly when an exported `.xlsx` is opened in macOS Excel/Numbers. Browser agents cannot launch native desktop apps or screenshot them.

**Steps (human):**
1. Ensure Export tab has data (Phase C of `docs/prompts/E2E_UNBLOCK_AND_EXPORT_WIRING.md`)
2. Export a block schedule as `.xlsx` from `/hub/import-export`
3. Open the downloaded file in Microsoft Excel or Numbers
4. Verify: colored cells, header rows, conditional formatting, data validation dropdowns
5. Screenshot and save as `mac_excel_formatting_check.png` in project root

**Unblocked when:** Export tab is wired to real data (Phase C complete).

---

## Consider GitHub Pro ($4/mo) (2026-02-06)

**Priority:** Low
**Status:** Deferred until closer to production

**Context:** Repo is now private. Branch protection and rulesets require GitHub Pro on private repos. Currently relying on discipline + pre-commit hooks (33 hooks across 25 phases) since you're the sole write-access user.

**Pro gets you:**
- Branch protection / rulesets on private repos
- Required reviewers, CODEOWNERS enforcement
- 3,000 Actions minutes (vs 2,000 free)
- Full repository traffic insights
- Email support from GitHub

**Note:** If self-hosting (GitLab, Gitea, etc.), this becomes moot — those platforms include branch protection at all tiers.

**Revisit when:** Adding collaborators with write access, or finalizing hosting decision.

## Codex Self-Improvement Ops (2026-02-06)

**Priority:** High
**Status:** Active

Codex-side safety and triage scaffolding is in place. These are the remaining human decisions.

- [ ] Optional: review `docs/reports/automation/codex_bad1_final_salvage_20260205-2247.md` and cherry-pick from `codex/salvage/bad1-final-20260205-2247` if you want to keep any residual ideas.
- [ ] Keep nightly Codex hook scan automation enabled (`hook-pii-health-check` at `01:00`) unless replaced with an equivalent gate.
- [ ] Confirm canonical keychain service names for local API keys (`OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, optional `MCP_API_KEY`) for long-term setup stability.
- [ ] Decide whether to keep duplicated skills in both `.codex/skills` and `.claude/skills` or consolidate to one canonical root.

---

## LaTeX/MFR Generation Research (2026-01-28)

**Priority:** Low (deferred)
**Status:** DEFERRED - Research archived
**ADR:** `docs/decisions/ADR-2026-01-28-latex-generation.md`

**Summary:** PR #772 evaluated LaTeX libraries for military MFR generation.
- Recommendation: Jinja2 + pylatexenc when needed
- Current state: ReportLab sufficient for existing PDF needs
- Retrieve research: `git show origin/claude/research-latex-generation-THEPp:docs/research/latex-generation-research.md`

**Revisit when:** AR 25-50 MFR auto-generation becomes a priority

---

## Excel-to-CP-SAT Alignment (2026-01-28)

**Priority:** High (improves schedule quality)
**Status:** Analysis complete, implementation pending
**Analysis:** `docs/analysis/excel-vs-cpsat-block10-comparison.md`

**Findings:** Excel hand-tuned schedule differs significantly from CP-SAT output:
- CP-SAT assigns more clinic days to outpatient residents (+11 to +25 half-days)
- Excel captures institutional events (USAFP, OB retreat, DOCTORS' DAY) not in CP-SAT
- Faculty AT distribution differs (Excel more spread, CP-SAT concentrated with equity)

**Recommended Actions:**
- [ ] Create Excel import script as preload baseline
- [ ] Add weekly pattern constraints from Templates sheet
- [ ] Create `institutional_events` table for recurring events
- [ ] Map Excel short codes (C, CV, AT) to canonical activity codes

---

## Post-Rebuild Fixes (2026-01-02)

### Fix Misleading "/mcp not authenticated" Display
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

## Cleanup / Developer Experience (2026-01-09)

### Heatmap Feature - Needs Schedule Data
**Priority:** Medium (post-first-deployment)
**Status:** Working but empty

**Context:** Heatmap page at `/heatmap` works correctly but shows "No data available" because there's no schedule data in the database.

**To verify after first schedule generation:**
1. Navigate to `/heatmap`
2. Select date range that has assignments
3. Confirm Plotly.js heatmap renders with data

**No code changes needed** - just needs schedule data.

---

## Completed (2025-12-25) - Remaining Open Items

### Optional: Add `solver_managed` Flag
**Priority:** Low (nice-to-have)
**Context:** Cleaner than filtering by `activity_type`

- [ ] Add `solver_managed: bool` to RotationTemplate model
- [ ] Create Alembic migration
- [ ] Update `_get_rotation_templates()` to use flag

---

## Feature Requests - Pending Investigation

### Intern Scheduler Generator for Anticipated Leave
**Priority:** Medium
**Added:** 2026-01-05
**Status:** TODO - Feature Request

**Request:** Pre-generate schedules that accommodate anticipated (but not yet submitted) leave requests for incoming interns.

**Context:** Intern leave requests are not received until just before the Academic Year starts. The scheduler needs to generate tentative schedules with placeholder leave slots that can be filled in once actual requests arrive.

**Use Cases:**
- [ ] Generate AY schedule with "anticipated leave" placeholders
- [ ] Configure expected leave distribution (e.g., 4 weeks per intern)
- [ ] Auto-balance leave across blocks to avoid coverage gaps
- [ ] Allow manual override once actual requests arrive
- [ ] Track which leave slots are "anticipated" vs "confirmed"

**Implementation Considerations:**
- Add `leave_status: anticipated | confirmed | denied` to Absence model
- Generate schedule with anticipated absences distributed evenly
- Provide UI to convert anticipated -> confirmed when requests arrive
- Alerting for interns who haven't submitted requests by deadline

---

### ACGME Rest Hours - PGY-Level Differentiation
**Priority:** Medium
**Added:** 2025-12-30
**Status:** Awaiting PF discussion

**Issue:** MEDCOM analysis identified that ACGME rest hours should be PGY-level dependent:

| PGY Level | ACGME Requirement | Current Code |
|-----------|------------------|--------------|
| PGY-1 | 10 hours ("should have" - recommended) | 8 hours |
| PGY-2+ | 8 hours ("must have" - required) | 8 hours |

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

## Other Pending Tasks

### Resilience API Response Models - 85% COMPLETE
**Location:** `/backend/app/api/routes/resilience.py`
- 46/54 endpoints now have `response_model` defined (85% coverage, up from 22%)
- Remaining 8 endpoints return complex nested structures pending schema refactoring
- **Impact:** Significantly improved OpenAPI documentation, response consistency

### Frontend Accessibility Gaps - AUDIT UPDATE (2026-01-04)
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

### MCP Placeholder Tools (11 tools)
- Hopfield networks, immune system, game theory return synthetic data
- Shapley value returns uniform distribution

### Penrose Efficiency - Placeholder Logic
**Priority:** MEDIUM
**Location:** `/backend/app/resilience/exotic/penrose_efficiency.py`
**Found:** G2_RECON audit (2025-12-30)

- 10+ TODO comments with placeholder implementations
- Astrophysics-inspired efficiency extraction concept
- Currently returns synthetic data
- **Impact:** Exotic resilience feature non-functional

**Note:** Part of Tier 5 "Exotic Frontier Concepts" - advanced research features

### Activity Logging - Schedule Endpoint Enhancement
- [ ] Add activity logging to schedule modification endpoints (enhancement)
- **Note:** Admin audit trail fully operational. Schedule endpoint logging is an enhancement, not a blocker.

---

## Process Improvements

### Big Ideas (Deferred)

1. **Linting Enforcement**: Ruff is configured in `pyproject.toml` but not run in CI. Consider adding `ruff check --fix` to pre-commit or CI.

2. **Session Naming Convention**: Sessions 7-9 are in `docs/archived/sessions/` while 10+ are in `docs/sessions/`. Consider consolidating.

3. **Remaining Backend TODOs (from TODO_TRACKER.md)**:
   - Portal Dashboard Data (`portal.py:863`) - Faculty dashboard returns stub data
   - MCP Sampling Call (`agent_server.py:263`) - Placeholder LLM response
   - Server Cleanup Logic (`server.py:1121`) - DB connection cleanup on shutdown

---

## Session 045 Findings (2026-01-01)

### Human Action Required: Docker Desktop Restart

**Priority:** HIGH
**Blocker:** Frontend container rebuild needed but Docker Desktop frozen

**Action:**
1. Restart Docker Desktop (Cmd+Q -> Relaunch)
2. Run: `docker-compose up -d --build frontend`
3. Verify: `scripts/health-check.sh --docker`

**Context:** ARCHITECT confirmed PR #594 contains functional TypeScript changes requiring rebuild:
- New `frontend/src/types/state.ts` (362 lines)
- New `frontend/src/contexts/index.ts` (28 lines)
- 19 test file renames (.ts -> .tsx)

### CI Pipeline Pre-Existing Debt

**Priority:** P1 (not blocking Session 045, existed before)

| Issue | Fix |
|-------|-----|
| package-lock.json sync | `cd frontend && npm install && git add package-lock.json` |
| 11 remaining .ts->.tsx | Rename test files with JSX syntax |

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

## PAI Doctrine Enhancements (2026-01-06)

> Military doctrine patterns to formalize in PAI governance. Review and protocolize.

**Added:** 2026-01-06 (Session: PAI Structure Review)
**Status:** Awaiting review

### Already Implemented
- [x] Auftragstaktik (Commander's Intent) - in CLAUDE.md
- [x] AAR (After Action Review) - session-end skill
- [x] Chain of Command - identity cards
- [x] Left/Right Boundaries - CLAUDE.md
- [x] METT-TC equivalent (Resources Available) - CLAUDE.md

### Proposed Additions

#### 1. OPORD Template for Task() Prompts
**Priority:** HIGH
**Value:** Forces completeness when delegating

5-paragraph order format:
1. **Situation** - Terrain (codebase state), enemy (known issues), friendly (other agents working)
2. **Mission** - Who, what, when, where, why
3. **Execution** - Commander's intent, concept of ops, tasks to subordinates
4. **Sustainment** - Resources available, constraints
5. **Command & Signal** - Reporting requirements, escalation triggers

**Implementation:** Add OPORD template to CLAUDE.md Agent Spawning section or create `.claude/templates/OPORD.md`

#### 2. PACE Plan for Critical Operations
**Priority:** MEDIUM
**Value:** Explicit fallback chains

| Level | Meaning | Example |
|-------|---------|---------|
| **P**rimary | First choice | Use MCP tool directly |
| **A**lternate | If primary fails | Call backend API |
| **C**ontingency | If alternate fails | Parse files directly |
| **E**mergency | Last resort | Escalate to human |

**Implementation:** Add PACE thinking to identity cards or create `.claude/Governance/PACE_PATTERNS.md`

#### 3. CRM (Composite Risk Management) for Novel Approaches
**Priority:** MEDIUM
**Value:** Formalized risk assessment before risky ops

5-step process:
1. Identify hazards
2. Assess hazards (probability x severity)
3. Develop controls
4. Implement controls
5. Supervise and evaluate

**Implementation:** Add CRM checklist to skills that touch production data or security

#### 4. WARNO/FRAGO for Session Lifecycle
**Priority:** LOW
**Value:** Structured communication for pivots

- **WARNO (Warning Order):** Prep agents for upcoming complex work
- **FRAGO (Fragmentary Order):** Mid-session pivots without full re-briefing

**Implementation:** Document patterns in `.claude/Governance/` or integrate into orchestrator protocols

#### 5. IPB (Intelligence Prep of Battlefield) for Codebase Recon
**Priority:** LOW
**Value:** Systematic reconnaissance before operations

Already partially covered by:
- G2_RECON agent
- search-party skill
- Explore subagent

**Implementation:** Formalize IPB checklist for complex tasks

### Decision Needed
- [ ] Review which patterns provide value vs. overhead
- [ ] Decide implementation location (CLAUDE.md vs separate docs)
- [ ] Prioritize based on observed failure modes

---

## Half-Day Assignment Model - Pending Follow-ups (2026-01-14)

**Added:** Session 104 (design phase)
**Status:** Design complete, implementation pending
**Docs:** `docs/architecture/HALF_DAY_ASSIGNMENT_MODEL.md`

### 1. Peds Night Float (PedNF) Schedule Pattern
**Priority:** HIGH - Need verification
**Status:** TODO - Verify with Chief Residents

**Question:** What is the exact Peds Night Float schedule pattern?
- Start day/time?
- End day/time?
- Post-call rules (same as regular NF)?
- Does it span blocks?

**Current assumption (from Session 104):**
- Similar to regular Night Float but on Pediatrics
- Needs explicit confirmation before implementing in solver

### 2. Resident Call System Details
**Priority:** HIGH - Needed for preload table design
**Status:** TODO - Document from Chief Residents

**Known patterns:**
- L&D 24-hour call: Friday
- Night Float coverage: Various
- Weekend call: TBD

**Questions:**
- [ ] How are call assignments distributed (equity tracking)?
- [ ] What's the exact post-call pattern for residents?
- [ ] Who assigns call? (Chief Residents confirmed)
- [ ] Is there a call swap process?

### 3. Create Alembic Migration for half_day_assignments
**Priority:** HIGH - Next implementation step
**Status:** Pending - Blocked on design approval

**Tables to create:**
- `half_day_assignments` - Core schedule table
- `inpatient_preloads` - FMIT, NF, PedW, etc.
- `resident_call_preloads` - L&D, NF coverage, weekend

See `docs/architecture/HALF_DAY_ASSIGNMENT_MODEL.md` for full schema.

---

## UI Enhancement: Color Selection for Templates (2026-01-14)

### Add Color Picker to Activity/Assignment and Rotation Templates
**Priority:** Medium
**Added:** 2026-01-14
**Status:** TODO

**Request:** Add color selection UI to activity/assignment and rotation template editors.

**Color Semantics:**
| Color | Meaning |
|-------|---------|
| Red | Leave **ineligible** - Cannot take leave during this rotation |
| Yellow | Leave **eligible** - Can take leave during this rotation |

**Implementation Notes:**
- Color scheme reference: `docs/scheduling/TAMC_Color_Scheme_Reference.xml`
- Existing rotation column colors in XML:
  - `inpatient_critical` (red): IM, Peds Ward, KAP, LDNF, Surg Exp, ICU
  - `elective_outpatient` (yellow): FMC, NEURO, SM, POCUS, PROC, Gyn Clinic
  - `fmit` (cyan): FMIT1, FMIT2
  - `night_float` (black): NF, Peds NF
  - `orientation` (purple): FMO, DCC/BOLC/FMO

**Files to modify:**
- `frontend/src/app/admin/templates/page.tsx` - Add color picker to template editor
- `backend/app/models/rotation_template.py` - Add `color_hex` column (optional)
- Or use `leave_eligible: bool` flag and derive color from that

---

## Terminology Fixes (2026-01-13)

### CP-SAT: Rename `total_blocks_assigned` -> `total_assignments`
**Priority:** Low
**Added:** 2026-01-13
**Status:** TODO

**Problem:** `schedule_runs.total_blocks_assigned` is misleading - it counts assignments, not blocks.

**Recommended Approach:** Option B - Alias in Pydantic schemas (no migration)
```python
# In backend/app/schemas/schedule.py
total_assignments: int = Field(alias="total_blocks_assigned")
```

**Why Option B:**
- No Alembic migration needed
- DB column unchanged (backwards compatible)
- Frontend sees correct name via camelCase conversion
- 24 files reference this field - alias avoids mass rename

**Files affected (for future full rename):**
- `backend/app/models/schedule_run.py` - Column definition
- `backend/app/schemas/schedule.py` - Response schema
- `backend/app/scheduling/engine.py` - Assignment
- `mcp-server/src/scheduler_mcp/scheduling_tools.py` - MCP tool
- Tests and docs (20+ files)

---

## Hooks and Scripts Consolidation (2026-01-19)

**Priority:** MEDIUM
**Added:** 2026-01-19 (PLAN_PARTY analysis - 10 probes, 8.5/10 convergence)
**Status:** Roadmap complete, implementation pending
**Roadmap:** `docs/planning/HOOKS_AND_SCRIPTS_ROADMAP.md`

### Summary

Comprehensive hooks and scripts consolidation addressing:
- Pre-push hook addition (missing safety layer)
- Parallel pre-commit execution (15-30s -> <10s target)
- Backup script consolidation (3 scripts -> 1)
- Claude Code hooks enhancement (RAG injection, metrics alerting)
- PII scanner config externalization
- Graduate advisory hooks (MyPy, Bandit) to blocking

### Current State

| Category | Count | Status |
|----------|-------|--------|
| Git hooks (active) | 3 | pre-commit, commit-msg, post-merge |
| Pre-commit phases | 24 | Comprehensive but sequential (slow) |
| Claude Code hooks | 6 scripts | Partial coverage |
| Shell scripts | 45 | Needs consolidation |
| CI workflows | 17 | Well-integrated |

### Phase Overview

| Phase | Focus | Effort | Owner | Status |
|-------|-------|--------|-------|--------|
| 1 | Quick Wins (parallelize, consolidate, externalize) | 2-3 sessions | COORD_OPS | TODO |
| 2 | Hook Hardening (pre-push, strict MyPy/Bandit) | 2-3 sessions | COORD_TOOLING | TODO |
| 3 | AI Workflow Enhancement (RAG injection, metrics) | 3-4 sessions | COORD_TOOLING | TODO |
| 4 | Compliance Hardening (GPG evaluation, Gitleaks history) | 2-3 sessions | COORD_OPS | TODO |

### Human Actions Required

- [ ] Review and approve roadmap before implementation begins
- [ ] Decide on GPG signing enforcement policy (Phase 4)
- [ ] Confirm parallel pre-commit approach is safe (Phase 1)
- [ ] Review personnel name externalization approach (Phase 1)

### Key Files

| Category | Files |
|----------|-------|
| Pre-commit config | `.pre-commit-config.yaml` |
| PII scanner | `scripts/pii-scan.sh` |
| Backup scripts | `scripts/backup_full_stack.sh`, `scripts/full-stack-backup.sh`, `scripts/stack-backup.sh` |
| Claude Code hooks | `.claude/hooks/*.sh` |
| CI workflows | `.github/workflows/security.yml`, `.github/workflows/quality-gates.yml` |

### Gap Summary (from PLAN_PARTY Analysis)

| Gap | Priority | Risk | Status |
|-----|----------|------|--------|
| No pre-push hook | P1 | Dangerous ops reach remote | TODO |
| 24 sequential phases | P2 | 15-30s commit times | TODO |
| MyPy advisory (`|| true`) | P3 | Type bugs slip through | RESOLVED (2026-02-04) |
| Bandit advisory (`|| true`) | P3 | Security issues slip | RESOLVED (2026-02-04) |
| 3 overlapping backup scripts | P4 | Developer confusion | TODO |
| Claude Code hooks incomplete | P4 | No RAG injection | TODO |

**2026-02-04 Updates:**
- **MyPy:** Removed from pre-commit (full scan needed for accuracy, was never blocking)
  - Use `./scripts/mypy-check.sh` for manual type checking
  - CI-lite runs mypy as soft gate (informational)
- **Bandit:** Changed to scan staged files only (was scanning entire repo)
  - Use `./scripts/bandit-full.sh` for comprehensive security scans
  - Prevents pre-existing warnings from blocking unrelated commits

### Related Documents

- `docs/planning/HOOKS_AND_SCRIPTS_ROADMAP.md` - Full implementation roadmap
- `.claude/hooks/README.md` - Hooks ecosystem documentation
- `.pre-commit-config.yaml` - Pre-commit configuration (24 phases)

---

*Last updated: 2026-02-10 (archived 31 completed items)*

---

## Completed / Archived

> Items below have been completed and archived. Kept for historical reference.

- **CP-SAT Phase 2** -- Completed 2026-01-28. All P0-P4 items resolved; validator fixed to exclude time-off from duty hours; Block 10 validation clean.
- **Import/Export Staging DB** -- Completed 2026-01-04. Full round-trip import workflow with 6 endpoints, 3 conflict resolution modes, migration deployed.
- **Re-enable Alembic Migrations** -- Verified 2026-01-03. `alembic upgrade head` was already active in `docker-entrypoint.sh`; phantom task.
- **Seaborn Warning in Backend Logs** -- Completed 2026-01-11. Removed unused seaborn import from `spin_glass_visualizer.py` (commit `9200055e`).
- **Block 10 Schedule Generation** -- Completed 2025-12-25. 87 assignments, 112.5% coverage, 25 constraints active, 0 violations.
- **Complete MCP Wiring** -- Completed 2025-12-24. `analyze_swap_candidates` and `run_contingency_analysis` wired to backend with JSON endpoints.
- **PuLP Solver Template Balance** -- Completed 2025-12-24. Added template balance penalty to PuLP solver objective function.
- **Admin GUI Bulk Rotation Template Editing** -- Completed 2026-01-04. PRs #633, #638, #642 merged; template table, bulk actions, pattern and preference editors.
- **Admin GUI Absence Loader** -- Completed 2026-01-05. PR #649 merged; CSV/Excel upload with preview, conflict detection, apply/rollback workflow.
- **Faculty FMIT and Call Equity** -- Completed 2026-01-11. IntegratedWorkloadConstraint with 5 workload categories, min-max fairness, Jain's index (commit `1bac63ca`).
- **Admin GUI Wiring** -- Completed 2026-02-04. All admin dashboard pages fully wired: dashboard metrics, credentials, block-import staging, schedule-drafts.
- **Frontend Hub Consolidation (Phase 1)** -- Completed 2026-01-12. PRs #694-700 merged; RiskBar, Swap Hub, PersonSelector, Couatl Killer, Proxy Coverage, 3D Command Center.
- **CCW Burn Quality Protocol** -- Completed 2026-01-04. Protocol documented at `.claude/protocols/CCW_BURN_PROTOCOL.md` (217 lines) with pre-merge gates and rollback procedures.
- **Schedule Grid Frozen Headers** -- Completed 2025-12-28. Sticky header row and first column with z-index hierarchy for dense schedule scanning.
- **Heatmap Block Navigation** -- Completed 2025-12-28. Added Previous/Next/Today/This Block buttons matching Schedule page UX pattern.
- **Heatmap Backend Bug (group_by Validation)** -- Fixed via PR #512. Added daily/weekly heatmap generators, 28 new tests.
- **Daily Manifest Empty State UX** -- Completed 2025-12-28. Context-aware error messaging, info box with suggestions, quick action buttons.
- **NF Half-Block Documentation Consistency** -- Verified 2025-12-24. All 3 locations consistent; "block-half", Day 15 transition, PC rules, mirrored pairing all match.
- **Broken Documentation Links** -- Fixed 2026-01-04. All README.md links corrected to existing documentation files.
- **Full-Stack MVP Review Critical Items** -- All resolved by 2026-02-09. 11 items (Celery queues, security TODOs, env vars, DB indexes, admin users, CD pipeline, MCP prod config, procedure hooks, resilience components, TypeScript errors, token refresh) verified complete; overall MVP score PRODUCTION-READY.
- **Documentation Improvements** -- Completed 2025-12-31. 100 documentation tasks including Quick Reference Guide, API rewrites, troubleshooting expansion.
- **MCP API Client 401 Token Refresh** -- Completed 2026-01-02. PR #608 (commit `e6c4440e`); retry on 401 with fresh auth, loop prevention via flag.
- **MCP Server Tests Failing in CI** -- Resolved 2026-02-04. CI-lite workflow (`.github/workflows/ci-lite.yml`) created for repo-only validation with mocked API client.
- **Faculty Assignments Missing rotation_template_id** -- Fixed 2025-12-23. Added `_get_primary_template_for_block()` to engine; all 430 faculty assignments now have template IDs.
- **Solver Template Distribution Bugs** -- Fixed 2025-12-24, verified 2025-12-29. Three bugs (greedy, CP-SAT, template filter) fixed; all 4 solvers operational with balance tests.
- **Documentation Cleanup (Celery Checklist)** -- Completed 2025-12-21. Moved from archived to `docs/deployment/CELERY_PRODUCTION_CHECKLIST.md`.
- **Admin Email Invitations** -- Verified 2026-01-03. Was a phantom task; full email infrastructure already implemented (Celery task, SMTP service, route wiring).
- **Activity Logging Infrastructure** -- Verified 2026-01-04. Full ActivityLog model with 26 action types, 8 admin call sites, activity-log endpoint deployed.
- **Frontend WebSocket Client** -- Resolved. `useWebSocket.ts` implemented with reconnection, JWT auth, typed events.
- **Frontend Resilience Components** -- Verified 2026-01-04. All 4 components (BurnoutDashboard, ResilienceMetrics, N1Analysis, UtilizationChart) fully wired with 43 tests.
- **Frontend TypeScript Errors** -- Fixed 2025-12-30, hardened 2026-02-09 (PR #1099). All type errors resolved; strict build checks re-enabled.
