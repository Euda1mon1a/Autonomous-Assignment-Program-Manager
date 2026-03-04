---
name: codex-app-automation-triage
description: Consolidate and triage Codex macOS app automation output. Use when you need a morning report across Codex worktrees and want to separate actionable code changes from noise.
metadata:
  short-description: Codex App automation consolidation
---

# Codex App Automation Triage

Use this skill to consolidate Codex macOS app automation output and sort wheat from chaff.

## Quick start

From the repo root:

```bash
python .codex/scripts/codex_automation_report.py
```

This generates a Markdown report under `docs/reports/automation/` and prints the path.

## What this does

- Scans `~/.codex/worktrees/*/*` for git worktrees created by the Codex macOS app.
- Filters to the current repo by matching `origin` URL.
- Summarizes each worktree: branch, last commit, number of changes.
- Classifies changes into **signal** vs **noise** using simple path heuristics.

## Interpreting the report

**Signal (actionable)** typically includes:

- `backend/` application code
- `frontend/src/` components or hooks (non-generated)
- `tests/` or `backend/tests/`

**Noise** typically includes:

- generated types (e.g., `frontend/src/types/api-generated*.ts`)
- `node_modules/`, `dist/`, `coverage/`, `.next/`
- `.claude/` or `.codex/` artifacts

## Follow-up workflow (recommended)

For each worktree with signal:

1. Inspect changes:
   ```bash
   git -C <worktree> status -sb
   git -C <worktree> diff
   ```
2. Decide:
   - **Keep**: cherry-pick or copy changes into your current branch
   - **Discard**: ignore or delete the worktree
3. Record in your daily notes if needed.

## Options

Include clean worktrees:

```bash
python .codex/scripts/codex_automation_report.py --include-clean
```

Custom worktree root:

```bash
python .codex/scripts/codex_automation_report.py --root /custom/path
```

## Output

The report is a single Markdown file suitable for quick morning review and sharing.
