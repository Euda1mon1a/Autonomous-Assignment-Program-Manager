# OpenAI Codex App Guide (macOS)

> **Last Updated:** 2026-02-03
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
