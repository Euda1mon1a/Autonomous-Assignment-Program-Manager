# Claude Web Session Prompt: Tier 1 Independent Work

> **Created:** 2025-12-24
> **Purpose:** Starting prompt for next Claude (Web) session
> **Copy everything below the line to start a new session**

---

## Session Context

You are Claude (Web) working on the Residency Scheduler project. Claude Code (IDE) is working separately on Block 10 schedule generation with real data. You have **no PII access** and work only with source code, documentation, and sanitized data.

**Read these files first:**
1. `CLAUDE.md` - Project guidelines
2. `docs/planning/BLOCK_10_ROADMAP.md` - Current checkpoint status
3. `docs/planning/SESSION_CAPABILITIES.md` - Your available tools
4. `docs/development/PARALLEL_CLAUDE_BEST_PRACTICES.md` - Coordination patterns

**Branch:** Create your own branch from `origin/main` for any changes:
```
git fetch origin main
git checkout -b claude/web-tier1-work-<session-id> origin/main
```

---

## Your Priority Tasks (Tier 1 - No Dependencies)

Complete these tasks in order. All are independent of Block 10 data work.

### Task 1: Document Solver Algorithm (Priority: HIGH)

**Goal:** Create comprehensive documentation for the scheduling solver.

**Output:** `docs/architecture/SOLVER_ALGORITHM.md`

**Steps:**
1. Read the solver implementation:
   - `backend/app/scheduling/engine.py`
   - `backend/app/scheduling/solver.py` (if exists)
   - `backend/app/scheduling/constraints/` directory

2. Document:
   - Solver types available (Greedy, CP-SAT, PuLP)
   - Constraint hierarchy (hard vs soft)
   - Optimization objectives
   - Algorithm flow with diagram
   - Configuration options
   - Performance characteristics

3. Use `Glob` and `Grep` to find all constraint implementations:
   ```
   Glob: pattern="backend/app/scheduling/**/*.py"
   Grep: pattern="class.*Constraint" path="backend/app/scheduling"
   ```

**Commit message:** `docs: add comprehensive solver algorithm documentation`

---

### Task 2: Review MCP Placeholder Implementations (Priority: HIGH)

**Goal:** Analyze the 10 placeholder MCP tools and document what's needed to make them real.

**Output:** `docs/planning/MCP_PLACEHOLDER_IMPLEMENTATION_PLAN.md`

**Steps:**
1. Read the placeholder implementations:
   - `mcp-server/src/scheduler_mcp/resilience_integration.py` (lines 796-1213)

2. For each placeholder tool, document:
   - Current mock behavior
   - Required backend service/endpoint
   - Data dependencies
   - Estimated implementation effort
   - Priority ranking

3. Placeholder tools to analyze:
   - `analyze_homeostasis`
   - `get_static_fallbacks`
   - `execute_sacrifice_hierarchy`
   - `calculate_blast_radius`
   - `analyze_le_chatelier`
   - `analyze_hub_centrality`
   - `assess_cognitive_load`
   - `get_behavioral_patterns`
   - `analyze_stigmergy`
   - `check_mtf_compliance`

4. Cross-reference with backend services:
   ```
   Grep: pattern="def.*homeostasis|def.*fallback|def.*sacrifice" path="backend/app"
   ```

**Commit message:** `docs: create MCP placeholder implementation plan`

---

### Task 3: Audit Security Patterns (Priority: MEDIUM)

**Goal:** Review authentication, authorization, and data protection patterns.

**Output:** `docs/security/SECURITY_PATTERN_AUDIT.md`

**Steps:**
1. Invoke the security-audit skill:
   ```
   Skill: security-audit
   ```

2. Review these files:
   - `backend/app/core/security.py`
   - `backend/app/api/deps.py` (authentication dependencies)
   - `backend/app/core/rate_limit.py`
   - `backend/app/core/file_security.py`

3. Document:
   - Authentication flow (JWT handling)
   - Authorization patterns (RBAC implementation)
   - Rate limiting configuration
   - Input validation patterns
   - Error message sanitization
   - Any potential vulnerabilities

4. Check for common issues:
   ```
   Grep: pattern="password|secret|token|api_key" path="backend/app" -i
   ```

**Commit message:** `docs: add security pattern audit report`

---

### Task 4: Update CLAUDE.md with Session Learnings (Priority: MEDIUM)

**Goal:** Add new patterns discovered in this planning session.

**Output:** Updated `CLAUDE.md`

**Steps:**
1. Read current `CLAUDE.md`

2. Add new section: "## Parallel Work with Claude (Web)"
   - Reference `docs/development/PARALLEL_CLAUDE_BEST_PRACTICES.md`
   - Summarize PII boundaries
   - List safe vs unsafe operations

3. Add to "## Getting Help" section:
   - Reference new planning docs
   - Reference session capabilities doc

4. Verify no breaking changes to existing sections

**Commit message:** `docs: update CLAUDE.md with parallel work patterns`

---

### Task 5: Review Error Handling Patterns (Priority: LOW)

**Goal:** Improve error message clarity without leaking sensitive data.

**Files to review:**
- `backend/app/core/exceptions.py`
- `backend/app/api/routes/*.py` (exception handling in routes)

**Output:** Either:
- Direct code improvements (if simple)
- `docs/development/ERROR_HANDLING_IMPROVEMENTS.md` (if complex)

**Steps:**
1. Search for exception patterns:
   ```
   Grep: pattern="HTTPException|raise.*Error" path="backend/app/api"
   ```

2. Check for sensitive data leakage:
   ```
   Grep: pattern="detail=.*f\"|detail=.*{" path="backend/app"
   ```

3. Document or fix issues found

**Commit message:** `fix: improve error message clarity` or `docs: document error handling improvements`

---

## Completion Checklist

Before ending session:
- [ ] All tasks committed to your feature branch
- [ ] Branch pushed to remote
- [ ] PR created for each logical change
- [ ] Update `docs/planning/BLOCK_10_ROADMAP.md` with completed tasks
- [ ] No PII in any committed files

## Notes for Next Session

If you don't complete all tasks, document progress in:
`docs/sessions/SESSION_WEB_TIER1_PROGRESS.md`

Include:
- Tasks completed
- Tasks in progress
- Blockers encountered
- Recommendations for next session
