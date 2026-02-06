# Codex Cherry-Pick Hunter

> Last updated: 2026-02-05 (HST)
> Scope: Prevent losing useful worktree commits before cleanup

## Why This Exists

Useful changes can live in detached worktrees and be lost during cleanup.
This tool finds:

- Patch-unique commits vs `origin/main`
- Dirty worktree state (uncommitted files)

## Run It

```bash
# Human-readable report in terminal
scripts/ops/codex_cherry_pick_hunter.sh

# Save report to docs/reports/automation/
scripts/ops/codex_cherry_pick_hunter.sh --save
```

## Safety Gate Mode

```bash
scripts/ops/codex_cherry_pick_hunter.sh --risk-check
echo $?
```

Exit codes:

- `0`: no risk findings
- `3`: risk detected (unique commits and/or dirty worktree)

## Integration With Prune

`scripts/ops/codex_storage_hygiene.sh --prune-stale --apply` now uses this as a hard gate:

- If risk is detected, prune is blocked and a report is generated.
- To bypass intentionally, pass `--allow-risky-prune`.

## Current Finding Snapshot

Most worktrees are safe, but `bad1` currently has:

- 5 unique commits vs `origin/main`
- dirty files present

Do not prune worktrees until those commits are reviewed/cherry-picked.
