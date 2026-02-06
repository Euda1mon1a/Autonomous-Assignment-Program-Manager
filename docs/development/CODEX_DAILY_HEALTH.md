# Codex Daily Health

> Last updated: 2026-02-05 (HST)
> Scope: One-command Codex operational health check

## Purpose

`scripts/ops/codex_daily_health.sh` is a unified check that runs:

- MCP visibility (`codex mcp list`)
- local MCP server health (`http://127.0.0.1:8081/health`)
- hook + scanner health (`pre-commit`, `pii-scan`, `gitleaks`)
- cherry-pick risk (`codex_cherry_pick_hunter`)
- skill drift (`codex_skill_audit`)
- automation schedule snapshot

## Commands

```bash
# Full run with scanner checks
scripts/ops/codex_daily_health.sh --save

# Faster run without scanners
scripts/ops/codex_daily_health.sh --save --skip-scans
```

## Exit Behavior

- `0`: PASS
- `1`: ATTENTION REQUIRED (for example: cherry-pick risk detected, hook fail, MCP issue)

## Current Automation

- Codex App automation id: `codex-daily-health`
- Schedule: `02:00` daily
