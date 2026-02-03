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

Configure automations to run at **0100** so results are ready before you leave for work:

| Automation | Time | Purpose |
|------------|------|---------|
| **Daily Bug Scan** | 0100 | Scan commits for likely bugs, propose fixes |
| **Test Gap Detection** | 0115 | Find untested paths, add focused tests |
| **Security Sweep** | 0130 | Check for dependency vulnerabilities |
| **Pre-release Check** | 0145 | Verify changelog, migrations, feature flags |

Results land in the **Triage inbox** by ~0200-0300, ready for morning review.

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
