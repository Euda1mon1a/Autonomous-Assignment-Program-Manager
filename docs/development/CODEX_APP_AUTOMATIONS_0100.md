# Codex App Automations at 0100

> Last updated: 2026-02-12 (HST)
> Scope: Codex **App for macOS** automation registry (`~/.codex/automations`)

## Human Summary

You now have `15` registered Codex App automations in a staggered `01:00-02:00` local window (this doc). Additional automations exist in the Codex App and CLI — see `docs/architecture/PAI2_TRI_AGENT_SWARM.md` Section 9 (Overnight Playbooks) for the broader orchestration picture.
This keeps one nightly block while reducing launch contention.

## Where They Live

- Automation definitions: `~/.codex/automations/<id>/automation.toml`
- Per-automation run memory: `~/.codex/automations/<id>/memory.md`
- Schedule syntax: `rrule = "RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=0;BYDAY=SU,MO,TU,WE,TH,FR,SA"`

## Current 0100 Schedule

| ID | Name | Time | Purpose |
|---|---|---|---|
| `hook-pii-health-check` | Hook + PII Health Check | `01:00` | Verify pre-commit, PII scanner, and gitleaks remain healthy |
| `codex-worktree-triage` | Codex Worktree Triage | `01:02` | Surface actionable worktree signal and cherry-pick candidates |
| `daily-bug-scan` | Daily bug scan | `01:05` | Find likely regressions from recent commits with minimal safe fixes |
| `rag-ingest-readiness` | RAG Ingest Readiness | `01:08` | Keep RAG docs ingestion-ready with clear metadata and probes |
| `security-sweep` | Security Sweep | `01:12` | Audit secrets, auth, SQL injection risk, rate limiting, CORS/cookies |
| `test-gap-detection` | Test Gap Detection | `01:16` | Add focused tests for recently touched untested paths |
| `pre-release-check` | Pre-release Check | `01:20` | Validate release readiness and docs/config hygiene |
| `check-for-bandit-issues` | Check for bandit issues | `01:24` | Run Bandit workflow and remediate backend security warnings |
| `check-for-mypy-issues` | Check for mypy issues | `01:28` | Reduce backend type errors with minimal behavior change |
| `ci-lite` | CI lite | `01:40` | Run lightweight static and mocked quality checks |
| `inspiration` | Inspiration | `01:50` | Explore high-upside ideas outside routine review patterns |
| `codex-cherry-pick-hunter` | Codex Cherry-Pick Hunter | `01:54` | Detect unique/dirty worktree changes before any cleanup |
| `codex-storage-hygiene` | Codex Storage Hygiene | `01:56` | Audit Codex local storage and archive/session retention pressure |
| `codex-skill-audit` | Codex Skill Audit | `01:58` | Detect skill duplication and metadata drift across Codex/Claude roots |
| `codex-daily-health` | Codex Daily Health | `02:00` | Run unified MCP/hooks/cherry-pick/skill health summary |

## New Additions Made This Session

- `codex-worktree-triage`
- `hook-pii-health-check`
- `rag-ingest-readiness`
- `codex-storage-hygiene`
- `codex-cherry-pick-hunter`
- `codex-skill-audit`
- `codex-daily-health`

All are `ACTIVE` and included in the staggered nightly window.

## Fast Edit Patterns

To disable one automation:

```bash
sed -i '' 's/^status = \"ACTIVE\"/status = \"PAUSED\"/' ~/.codex/automations/<id>/automation.toml
```

To move an automation to 01:15:

```bash
sed -i '' 's/BYMINUTE=0/BYMINUTE=15/' ~/.codex/automations/<id>/automation.toml
```

To verify all schedules quickly:

```bash
for f in ~/.codex/automations/*/automation.toml; do
  echo "===== $f"
  rg -n "^id =|^name =|^status =|^rrule =" "$f"
done
```

## App vs Shared-Space Clarification

- App-only state: `~/.codex/automations/*` (this controls Codex App schedules).
- Shared repo state: docs/scripts under this repository (used by both Codex and Claude).
- Practical model: App automations generate findings; repo scripts/docs keep output understandable and reviewable by humans.

## Quick Status Command

```bash
.codex/scripts/codex_app_schedule_status.sh
```

To enforce minute fan-out limits in automation checks:

```bash
.codex/scripts/codex_app_schedule_status.sh --fail-on-collision --max-per-minute 5
```

## Quick Preflight Command

```bash
make automation-preflight
```
