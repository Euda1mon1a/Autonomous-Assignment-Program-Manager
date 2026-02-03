# OpenAI Codex App Guide (macOS)

> **Last Updated:** 2026-02-03
> **Purpose:** Practical guide to the Codex macOS app, plus fast automation triggers

---

## BLUF: AI Coding Tool Selection Matrix

### Codex

| Interface | Best Use Case | Why | Notes |
|---|---|---|---|
| **macOS App** | Parallel long-running tasks, review-focused workflows | Built‑in worktrees, skills, automations, and Git tools | Best for unattended or multi‑threaded work |
| **GitHub Action** | PR review + CI failure triage | `openai/codex-action@v1` runs `codex exec` inside workflows | Fast, event‑driven triggers |
| **CLI / IDE** | Local interactive dev | Pair in terminal/IDE for iterative edits and testing | Best for hands‑on changes |
| **Automations (App)** | Recurring maintenance | Scheduled background runs with an inbox/triage queue | Use for repeatable checks |

### Claude (project-local tools)

| Interface | Best Use Case | Why | Notes |
|---|---|---|---|
| **Claude Code CLI** | Interactive dev, rapid edit‑test loop | Strong tool use + quick feedback | Best when you’re in the code |
| **Task Agents** | Parallel exploration | Context isolation for multi‑file work | Good for “search/explore/plan” |
| **Web/API** | Research and planning | Longer‑form analysis, artifacts | Use for docs/plans |

### Decision Guide (quick mapping)

| Scenario | Use | Why |
|---|---|---|
| “Fix this bug now” | Claude Code CLI | Fast interactive loop |
| “Review my PR” | Codex GitHub Action / PR review | Automated review in GitHub |
| “Run 5 tasks in parallel overnight” | Codex App | Worktrees + review queue |
| “CI failed; diagnose fast” | Codex GitHub Action | Immediate workflow_run trigger |
| “Interactive refactor with feedback” | Claude Code CLI | Tight iteration |
| “Daily maintenance checks” | Codex App Automations | Scheduled runs |

---

## Fast Automation Triggers (minutes, not nightly)

Use GitHub Actions + Codex Action for immediate triggers. These run as soon as a PR opens, or when CI fails.

### 1) Auto‑review on PR open/sync

```yaml
name: Codex Auto Review
on:
  pull_request:
    types: [opened, synchronize, ready_for_review]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: openai/codex-action@v1
        with:
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          prompt: "Review this PR for bugs and security issues. Provide P1/P2/P3 findings."
          sandbox: workspace-write
          safety-strategy: drop-sudo
```

### 2) Auto‑fix on CI failure

```yaml
name: Codex CI Auto-Fix
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]

jobs:
  fix:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - uses: openai/codex-action@v1
        with:
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          prompt: "Diagnose the CI failure, propose a fix, and open a PR."
          sandbox: workspace-write
          safety-strategy: drop-sudo
```

### Security notes for Actions
- Prefer **drop‑sudo** (or unprivileged user) to limit risk.
- Restrict who can trigger the workflow.
- Keep `sandbox` as tight as possible.
- Avoid running Codex before steps that need elevated access.

---

## Codex App Basics

### Availability & Plans
- The **Codex app is available on macOS (Apple Silicon)**.
- Windows/Linux are **notify‑only** for now.
- Codex is included with **Plus, Pro, Business, Enterprise, and Edu** plans.
- **Free and Go** plans include Codex for a limited time.

### Sign‑in
- Sign in with your **ChatGPT account**.
- You can also sign in with an **OpenAI API key**, but some features (like cloud threads) may be unavailable.

### Core App Capabilities
- **Worktrees** for parallel tasks
- **Skills** and **Automations**
- **Git tools** (diffs, stage, commit, push)
- **Built‑in terminal** per thread
- **Web search** (cached by default)
- **Cloud tasks** run in isolated sandboxes with your repo and environment; you can review, merge, or pull results locally.

### Automations (App)
- Automations run **locally**, and the app must be running.
- Results land in an **inbox/triage queue** for review.
- Each run uses a **background worktree** for Git repos.

### Security & Sandboxing
- Codex is **secure by default** and uses system‑level sandboxing.
- By default, agents can edit files only in the active folder/branch and use **cached web search**.
- Elevated actions (e.g., broader network access) require permission.
- You can configure **rules** to auto‑approve specific commands.

---

## Getting Started Checklist

1. Install the Codex app for macOS
2. Sign in with your ChatGPT account
3. Add a project folder
4. Start a thread with a scoped task
5. Review diffs in‑app before pulling or merging

---

## Official References

- [Introducing the Codex app (OpenAI)](https://openai.com/index/introducing-the-codex-app/)
- [Codex app (Developer docs)](https://developers.openai.com/codex/app/)
- [Codex app features (Developer docs)](https://developers.openai.com/codex/app/features/)
- [Automations (Developer docs)](https://developers.openai.com/codex/app/automations)
- [Codex GitHub Action (Developer docs)](https://developers.openai.com/codex/github-action)
- [Using Codex with your ChatGPT plan (Help Center)](https://help.openai.com/en/articles/11369540-icodex-in-chatgpt)
