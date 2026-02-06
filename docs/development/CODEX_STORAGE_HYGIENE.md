# Codex Storage Hygiene

> Last updated: 2026-02-05 (HST)
> Scope: Codex App local state under `~/.codex`

## Why This Matters

Codex App keeps local worktrees, sessions, and logs. In this repo, storage pressure is mostly local artifacts, not source code.

## Current Snapshot

- `~/.codex`: about `2.9G`
- `~/.codex/worktrees`: about `2.4G`
- Largest worktree: `bad1` about `2.1G`
- Dominant reclaim target: cache directories (`frontend/node_modules`, `frontend/.next`, `frontend/.npm-cache`, backend caches)

## One-Command Audit

```bash
scripts/ops/codex_storage_hygiene.sh --audit
```

## Safe Cleanup (Dry-Run First)

```bash
# Show what would be removed
scripts/ops/codex_storage_hygiene.sh --clean-caches

# Execute cache cleanup
scripts/ops/codex_storage_hygiene.sh --clean-caches --apply
```

## Archive / Session Retention

```bash
# List old session files
scripts/ops/codex_storage_hygiene.sh --list-old-sessions --session-days 30

# Prune old session files
scripts/ops/codex_storage_hygiene.sh --prune-old-sessions --session-days 30 --apply
```

## Stale Worktree Retention

```bash
# List clean stale worktrees older than 14 days
scripts/ops/codex_storage_hygiene.sh --list-stale --days 14

# Prune clean stale worktrees older than 14 days
scripts/ops/codex_storage_hygiene.sh --prune-stale --days 14 --apply
```

## Safe Prune Plan (Exclude bad1 by Default)

```bash
# Generate a human-readable safe prune plan (no deletes)
scripts/ops/codex_safe_prune_plan.sh --save

# Optional execution of only prune-ready worktrees
scripts/ops/codex_safe_prune_plan.sh --apply --exclude-ids bad1
```

## Cherry-Pick Protection (Critical)

Before stale-worktree prune, run:

```bash
scripts/ops/codex_cherry_pick_hunter.sh --save
```

`--prune-stale` is now fail-closed:

- It runs cherry-pick hunter safety check by default.
- If risk is detected, prune is blocked and a report path is printed.
- Override only if intentional: `--allow-risky-prune`

## Guardrails

- Script defaults to read-only audit/dry-run.
- Deletions require `--apply`.
- Stale-worktree prune only touches clean worktrees (no uncommitted changes).
- Stale-worktree prune is blocked when cherry-pick hunter reports risk (unless explicitly overridden).

## App Automation

- Added Codex App automation: `codex-storage-hygiene` at `01:56` daily.
- It runs audit-only and reports suggested follow-up commands.
