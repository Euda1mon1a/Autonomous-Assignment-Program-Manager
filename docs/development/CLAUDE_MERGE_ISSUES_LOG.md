# Merge Issues Log

This document records merge-related events that may indicate history reconciliation or non-standard merges. Use it to cross-reference when investigating orphaned-branch issues.

## High-risk / history-reconciliation merges

- `5ee6cfb` — Merge docs/session-14-summary (PII-cleaned history)
- `7b41a79` — Merge remote-tracking branch `origin/main` into `docs/session-14-summary`
- `ff44d2b` — Merge remote-tracking branch `origin/main` into `docs/session-14-summary`
- `ad5783e` — Merge remote-tracking branch `origin/main` into `docs/session-14-summary`

## Recommended fixes for high-risk merges

- `5ee6cfb` (unrelated-history merge): Freeze `main` and run a full diff audit against the pre-PII base commit; re-apply any lost code via normal PRs and document the reconciliation steps.
- `7b41a79` / `ff44d2b` / `ad5783e` (remote-tracking merges into docs branch): Avoid merging `origin/main` into the docs branch; instead rebase the docs branch onto `origin/main` to keep a linear history and prevent duplicate merge commits.

## Local "merge main" (non‑PR) commits

- `55d5e15` — Merge remote main - keep updated triage report
- `90c3864` — Merge branch `main` into `claude/parallel-task-execution-buejF`
- `47f7fce` — Merge branch `main` into `claude/parallel-task-execution-buejF`
- `8367a4d` — Merge branch `main` into `claude/parallel-task-organization-MTcj4`
- `678704f` — Merge branch `main` into `claude/parallel-task-organization-MTcj4`

## Notes

- Standard PR merges (`Merge pull request #...`) are excluded; those are normal.
- This list was generated from `git log --merges --oneline -n 50`.
