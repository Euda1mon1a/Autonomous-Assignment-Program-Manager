# OpenAI Codex App Guide (macOS)

> **Last Updated:** 2026-02-02
> **Purpose:** Practical guide to the Codex macOS app, plus fast vs slow automation paths

---

## BLUF: AI Coding Tool Selection Matrix

### Codex

| Interface | Best Use Case | Why | Notes |
|---|---|---|---|
| **macOS App** | Parallel long-running tasks, review-focused workflows | Enables multiple agents in parallel across projects and includes built-in worktree support, skills, automations, and git functionality | Best for unattended or multi-threaded work |
| **GitHub (cloud review)** | PR review in GitHub | Comment `@codex review` or enable automatic reviews in Codex settings | If you already have PR review enabled, keep it on |
| **GitHub Action** | Event-driven CI tasks | `openai/codex-action@v1` runs Codex inside GitHub Actions workflows | Fast triggers on PR open or CI failure |
| **CLI non-interactive** | Scheduled or scripted jobs | `codex exec` is designed for CI, pre-merge checks, and scheduled runs | Good for cron or CI-only workflows |

### Claude (project-local tools)

| Interface | Best Use Case | Why | Notes |
|---|---|---|---|
| **Claude Code CLI** | Interactive dev, rapid edit-test loop | Strong tool use + fast feedback | Best when you are in the code |
| **Task Agents** | Parallel exploration | Context isolation for multi-file work | Good for search/explore/plan |
| **Web/API** | Research and planning | Longer-form analysis, artifacts | Use for docs/plans |

### Decision Guide (quick mapping)

| Scenario | Use | Why |
|---|---|---|
| “Fix this bug now” | Claude Code CLI | Fast interactive loop |
| “Review my PR” | Codex GitHub review | Native GitHub review flow |
| “Run 5 tasks in parallel overnight” | Codex App | Worktrees + review queue |
| “CI failed; diagnose fast” | Codex GitHub Action or `codex exec` | Immediate workflow trigger |
| “Daily maintenance checks” | Codex App Automations | Scheduled runs |

---

## Fast Automation Triggers (minutes, not nightly)

If you need **immediate** automation, use GitHub Actions. Codex supports two fast paths:

1) **Codex GitHub Action**
- Runs Codex directly inside workflows via `openai/codex-action@v1` and `codex exec`.
- Ideal for PR auto-review or CI-failure triage.

2) **CLI non-interactive (`codex exec`)**
- Designed for CI, pre-merge checks, and scheduled jobs.
- Useful if you already run CI workflows and want Codex to act on failures.

### Example: PR review via Codex Action

```yaml
name: Codex pull request review
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  codex:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v5
      - name: Run Codex
        uses: openai/codex-action@v1
        with:
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          prompt-file: .github/codex/prompts/review.md
          output-file: codex-output.md
          safety-strategy: drop-sudo
          sandbox: workspace-write
```

### Example: CI failure auto-fix with `codex exec`

```yaml
name: Codex auto-fix on CI failure
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]

jobs:
  fix:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Codex
        run: |
          codex exec --full-auto --sandbox workspace-write \
            "Read the repo, run the failing tests, make the minimal fix, and stop."
```

---

## Slow / Overnight Automations (Codex App)

Codex app automations are **best for deeper, longer runs**:
- Automations run **locally in the Codex app**, and the app must be running.
- Findings go to the **Triage inbox** for review.
- Each automation run in a Git repo uses a **dedicated background worktree**.
- You can combine automations with **skills** for repeatable workflows.
- Automations use your default sandbox settings; you can tighten or allowlist commands using rules.

This is the right place for nightly scans, test-gap detection, broader refactors, or documentation sweeps.

> **Tip:** Use the **Test** button to run any automation manually. The scheduled time is preserved - testing doesn't reset or skip the next scheduled run.

### Recommended Schedule (0100 Local)

Schedule all automations at **0100**. Codex runs them **in parallel with worktree isolation** - each gets its own copy of the repo. No conflicts, no waiting.

| Automation | Days | Purpose |
|------------|------|---------|
| **Daily Bug Scan** | Mo-Fr | Scan commits for bugs, propose fixes |
| **Test Gap Detection** | Mo-Fr | Find untested paths, add focused tests |
| **Security Sweep** | Daily | Check for vulnerabilities, secrets |
| **Pre-release Check** | Mo-Fr | Verify changelog, migrations, flags |
| **Dead Code Detection** | Mo-Fr | Remove unused imports, functions |
| **Type Coverage** | Mo-Fr | Add type hints, fix mypy/tsc errors |
| **API Contract Sync** | Mo-Fr | Ensure frontend types match backend |
| **ACGME Compliance** | Su | Audit scheduling rules for violations |
| **Flaky Test Hunter** | We, Sa | Find and fix intermittent test failures |
| **Dependency Health** | Su | Check for vulnerable/outdated packages |
| **Doc Freshness** | Fr | Fix stale docstrings and broken links |
| **TODO Triage** | Mo | Collect TODOs, fix trivial ones |

Results land in **Triage inbox** by ~0200-0300, ready for morning review.

### Automation Prompts (Copy-Paste Ready)

<details>
<summary><b>Daily Bug Scan</b></summary>

```
Scan commits from the last 24 hours for likely bugs. Focus on:
- Missing await on async functions
- Unclosed resources (db sessions, file handles)
- Off-by-one errors in date/block logic
- Null/undefined access without guards

For each bug found, create a minimal fix. If no bugs, report "No issues found."
```
</details>

<details>
<summary><b>Test Gap Detection</b></summary>

```
Identify untested code paths added in the last 7 days. Check:
- backend/app/api/routes/ for endpoints without test coverage
- backend/app/services/ for service methods without unit tests
- frontend/src/hooks/ for hooks without test files

For each gap, write a focused test. Prioritize ACGME compliance and scheduling logic.
```
</details>

<details>
<summary><b>Security Sweep</b></summary>

```
Run a security audit on the codebase:
- Check for hardcoded secrets or credentials
- Review auth routes for bypass vulnerabilities
- Scan for SQL injection in raw queries
- Check rate limiting on sensitive endpoints
- Verify CORS and cookie settings

Report findings with severity (P1/P2/P3). Propose fixes for P1/P2.
```
</details>

<details>
<summary><b>Pre-release Check</b></summary>

```
Verify release readiness:
- CHANGELOG.md updated for recent commits
- No pending Alembic migrations without documentation
- Feature flags documented in docs/
- No TODO or FIXME in committed code from last 48 hours
- OpenAPI types match frontend (run generate:types:check)

Report blockers. If clean, report "Ready for release."
```
</details>

<details>
<summary><b>Dead Code Detection</b></summary>

```
Find dead code in the codebase:
- Unused imports in Python and TypeScript files
- Functions/methods never called
- Unreachable code paths
- Commented-out code blocks older than 30 days

Remove dead code and create a commit. Skip files in tests/ and __pycache__.
```
</details>

<details>
<summary><b>Type Coverage Expansion</b></summary>

```
Improve type coverage:
- Add type hints to untyped Python functions in backend/app/
- Fix mypy errors that are currently ignored
- Add missing TypeScript types in frontend/src/
- Replace 'any' types with proper interfaces

Focus on public APIs and service layer. Create minimal, focused commits.
```
</details>

<details>
<summary><b>API Contract Sync</b></summary>

```
Verify frontend/backend API contract:
- Run: cd frontend && npm run generate:types
- Compare generated types with committed api-generated.ts
- If drift detected, commit the updated types
- Check for camelCase/snake_case mismatches in new code

Report any endpoints with mismatched request/response shapes.
```
</details>

<details>
<summary><b>ACGME Compliance Audit</b></summary>

```
Audit scheduling code for ACGME compliance:
- 80-hour weekly limit enforced in constraints
- 1-in-7 day off rule implemented
- 24+4 hour shift limits in validator
- Supervision ratios in assignment logic

Check backend/app/scheduling/ and backend/app/validators/. Flag any logic that could allow violations.
```
</details>

<details>
<summary><b>Flaky Test Hunter</b></summary>

```
Identify potentially flaky tests:
- Tests using time.sleep() or fixed delays
- Tests with race conditions (shared state, no isolation)
- Tests depending on execution order
- Async tests missing proper await

Run suspicious tests 3x each. If any fail intermittently, fix the flakiness or mark with @pytest.mark.flaky.
```
</details>

<details>
<summary><b>Dependency Health Check</b></summary>

```
Check dependency health:
- Run: pip-audit -r backend/requirements.txt
- Run: npm audit --json in frontend/
- Check for major version updates available
- Flag deprecated packages

Create a report of vulnerabilities by severity. Propose safe upgrades for minor/patch versions only.
```
</details>

<details>
<summary><b>Documentation Freshness</b></summary>

```
Audit documentation currency:
- Find docstrings that don't match function signatures
- Check README.md mentions features that exist
- Verify API docs in docs/api/ match actual endpoints
- Find broken internal links in markdown files

Fix stale docs. Don't add new docs, just fix existing.
```
</details>

<details>
<summary><b>TODO Triage</b></summary>

```
Collect and prioritize TODOs:
- Find all TODO, FIXME, HACK, XXX comments
- Group by file/module
- Estimate complexity (trivial/medium/complex)
- For trivial ones (<5 lines to fix), just fix them

Output a summary of remaining TODOs sorted by priority. Create commits for trivial fixes.
```
</details>

### Repo-Specific Automations (High Yield)

These automations target issues specific to this medical residency scheduling codebase. They catch bugs documented in CLAUDE.md and discovered in CCW sessions.

**Top 3 (Highest ROI):**
1. Missing Await Detector - catches 2-5 bugs/month
2. N-1 Faculty Vulnerability Scanner - prevents operational crises
3. Enum Value Sync Validator - catches frontend/backend drift

<details>
<summary><b>1. Missing Await Detector</b> ⭐ TOP 3</summary>

```
Scan backend/app/ for async functions with missing await on database operations.

For each file in api/routes/, services/, controllers/:
1. Find async def functions
2. Look for calls to AsyncSession methods: execute, commit, refresh, flush, delete, merge
3. Check if preceded by 'await' on same line or previous line
4. Flag violations with file:line and suggested fix

Pattern to detect:
  result = db.execute(select(Model))  # WRONG - missing await
  result = await db.execute(select(Model))  # CORRECT

Skip: tests/, conftest.py, sync background tasks (Celery)

For each violation found:
- Report file path and line number
- Show the offending line
- Suggest the fix (add 'await')
- Create a commit if fix is unambiguous
```
</details>

<details>
<summary><b>2. N-1 Faculty Vulnerability Scanner</b> ⭐ TOP 3</summary>

```
Analyze faculty coverage for single points of failure using MCP resilience tools.

Steps:
1. Run contingency analysis on current schedule
2. For each faculty member, calculate:
   - Coverage gaps if they're absent (uncovered blocks)
   - ACGME violations on replacement residents
   - Cascade failures (secondary overloads > 2)
3. Compute vulnerability score (0.0 - 1.0)
4. Check cross-training status for high-vulnerability faculty

Alert thresholds:
- vulnerability_score > 0.8: CRITICAL - no backup available
- vulnerability_score > 0.6: WARNING - partial coverage only
- cascade_failures > 2: ESCALATE - systemic risk

Report format:
| Faculty | Vuln Score | Gaps | Cascades | Cross-Trained Backup |
|---------|------------|------|----------|---------------------|

Suggest remediation:
- Cross-training recommendations
- Staffing level adjustments
- Temporary coverage for planned absences
```
</details>

<details>
<summary><b>3. Enum Value Sync Validator</b> ⭐ TOP 3</summary>

```
Detect frontend/backend enum drift that causes silent API failures.

Extract enums from:
- Backend: backend/app/models/*.py (SQLAlchemy enums)
- Backend: backend/app/schemas/*.py (Pydantic enums)
- Frontend: frontend/src/types/api.ts and api-generated.ts

For each enum type:
1. Compare value strings exactly (must be snake_case)
2. Flag any frontend enum with camelCase values (Gorgon's Gaze violation)
3. Detect new backend values not present in frontend
4. Report missing enum exports in frontend barrel files

Critical enums to check:
- PersonType, RotationType, SwapType, AbsenceType, ConflictType
- SwapStatus, LeaveStatus, ConflictStatus
- UserRole, FacultyRole

Test round-trip:
- Send enum value from frontend
- Verify backend validation accepts it
- Verify response contains same value

Report format:
| Enum | Backend Values | Frontend Values | Status |
|------|----------------|-----------------|--------|
```
</details>

<details>
<summary><b>4. ACGME Rolling Window Edge Case Tester</b></summary>

```
Generate and run edge case tests for ACGME 80-hour rolling window validator.

Test scenarios:
1. Exactly 80 hours in 28-day window (boundary)
2. 80.5 hours - should trigger violation
3. Feb 28/29 boundary in leap year
4. Dec 31 → Jan 1 year boundary
5. Block boundary (4-week block ends, new starts)
6. Resident with vacation mid-window (hours reset?)
7. Back-to-back 24-hour calls spanning window edge

For each scenario:
1. Create test schedule data
2. Run against backend/app/validators/acgme_validators.py
3. Verify expected pass/fail result
4. Report any edge cases that pass when they should fail

Target files:
- backend/app/validators/acgme_validators.py
- backend/app/scheduling/acgme_compliance_engine.py
- backend/tests/validators/test_acgme_edge_cases.py (create if missing)

If edge case bug found, create minimal fix with test.
```
</details>

<details>
<summary><b>5. Constraint Registration Drift Detector</b></summary>

```
Verify all scheduling constraints are properly registered with the solver.

Scan backend/app/scheduling/constraints/:
1. Find all classes inheriting from BaseConstraint or SchedulingConstraint
2. Check registration in constraint_registry.py (or equivalent)
3. For each constraint, verify:
   - Has Priority enum (CRITICAL, HIGH, MEDIUM, LOW)
   - Has weight value defined
   - Has test file in tests/scheduling/constraints/
   - Is documented in constraint docs

Report format:
| Constraint Class | Registered | Priority | Weight | Has Tests |
|------------------|------------|----------|--------|-----------|

Flag:
- Unregistered constraints (implemented but not used)
- Missing test coverage
- Constraints without priority (default behavior unclear)
- Duplicate registrations

If unregistered constraint found, add registration entry.
```
</details>

<details>
<summary><b>6. Migration Chain Integrity Checker</b></summary>

```
Verify Alembic migration chain integrity and naming conventions.

Scan backend/alembic/versions/:
1. Build dependency graph: down_revision → revision
2. Detect orphaned migrations (no parent, not initial)
3. Detect merge conflicts (multiple heads)
4. Verify naming convention: YYYYMMDD_description
5. Check revision ID length ≤ 64 characters
6. Verify each migration has both upgrade() and downgrade()

Run validation:
- alembic history --verbose
- alembic check (if available)

Report format:
| Migration | Revision | Down Revision | Length | Has Downgrade |
|-----------|----------|---------------|--------|---------------|

Flag:
- Broken chain links
- UUID-format revisions (old auto-generated, should convert)
- Names approaching 64-char limit (warn at 55+)
- Missing downgrade() function

If chain break found, identify the gap and suggest fix.
```
</details>

<details>
<summary><b>7. Async/Sync Type Mismatch Hunter</b></summary>

```
Find sync database operations in async routes causing event loop blocking.

Scan backend/app/api/routes/:
For each async def function:
1. Check parameter type hints for 'Session' (should be AsyncSession)
2. Find db.query() calls (sync ORM, should use select())
3. Find sync commits: db.commit() without await
4. Flag imports: 'from sqlalchemy.orm import Session' in async modules

Patterns to flag:
- async def endpoint(db: Session)  # Should be AsyncSession
- db.query(Model).filter(...)  # Should be await db.execute(select(...))
- db.add(item); db.commit()  # Should be await db.commit()

Exclude:
- Background task handlers (Celery uses sync by design)
- Files in backend/app/tasks/ (async optional)
- Test files using sync fixtures

Report format:
| File | Line | Pattern | Suggested Fix |
|------|------|---------|---------------|

Create fixes for clear violations.
```
</details>

<details>
<summary><b>8. Pre-Solver Infeasibility Detector</b></summary>

```
Detect constraint combinations that make schedules unsolvable BEFORE solver runs.

For upcoming block configuration, validate:
1. Total required coverage hours ≤ available resident hours
   - Sum all rotation coverage requirements
   - Sum all resident available hours (minus absences, leave)
   - Flag if deficit > 5%

2. Supervision ratios achievable with faculty count
   - PGY-1: 1:2 faculty ratio
   - PGY-2/3: 1:4 faculty ratio
   - Check each rotation's faculty availability

3. No resident has conflicting hard constraints
   - Vacation overlapping required rotation
   - Call assignment during blocking absence
   - Two rotations assigned same block

4. Call frequency requirements satisfiable
   - Every-3rd-night rule with resident pool size
   - Weekend call distribution feasibility

Report format:
| Constraint Conflict | Severity | Affected Residents | Resolution |
|--------------------|----------|-------------------|------------|

If infeasibility detected, suggest:
- Which constraint to relax
- Additional resources needed
- Alternative scheduling approach
```
</details>

<details>
<summary><b>9. Circuit Breaker Health Monitor</b></summary>

```
Monitor service health via circuit breaker status using MCP tools.

Steps:
1. Check all circuit breakers for current state
2. For breakers in HALF_OPEN or OPEN:
   - Record time since last state change
   - Attempt test probe if safe
   - Flag if stuck (> 1 hour in HALF_OPEN)

3. Check aggregate health metrics:
   - Failure rate per service
   - Request latency trends
   - Error rate spikes

Alert thresholds:
- OPEN breaker: CRITICAL - service unavailable
- HALF_OPEN > 1 hour: WARNING - recovery stalled
- failure_rate > 50%: WARNING - service degraded
- failure_rate > 80%: CRITICAL - service failing

Critical services (escalate immediately):
- Database connection
- Redis cache
- MCP server
- Auth service

Report format:
| Service | State | Duration | Failure Rate | Action |
|---------|-------|----------|--------------|--------|

If degraded, suggest:
- Service restart command
- Fallback activation
- Manual override steps
```
</details>

<details>
<summary><b>10. Burnout Precursor Scanner</b></summary>

```
Identify residents approaching burnout threshold using MCP wellness tools.

Steps:
1. Scan all residents for burnout precursors
2. Check team fatigue levels
3. For each resident with precursor_score > 0.7:
   - Current week's total hours
   - Consecutive days worked
   - Night shifts in last 14 days
   - Weekend calls in last month

4. Simulate burnout spread to identify super-spreaders
   - Network analysis of coverage dependencies
   - Contagion risk assessment

Alert thresholds:
- precursor_score > 0.9: CRITICAL - immediate intervention
- precursor_score > 0.7: WARNING - schedule adjustment needed
- team_fatigue > 0.6: WARNING - systemic issue

Report format:
| Resident | Score | Hours/Week | Consec Days | Night Shifts | Risk |
|----------|-------|------------|-------------|--------------|------|

Suggest schedule adjustments:
- Swap candidates (who can absorb load safely)
- Coverage redistribution options
- Mandatory rest recommendations
- Flag for program director review
```
</details>

---

## Availability & Plans

- The Codex app is available for **macOS**.
- Codex is included with **Plus, Pro, Business, Edu, and Enterprise** plans.
- **Free and Go** plans include Codex for a limited time.

---

## Official References

- Introducing the Codex app (OpenAI)
- Codex app automations
- Codex GitHub Action
- Codex in GitHub (`@codex review` + automatic reviews)
- Codex non-interactive (`codex exec`)
- Codex with ChatGPT plans
