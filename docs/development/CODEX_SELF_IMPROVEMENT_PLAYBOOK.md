# Codex Self-Improvement Playbook

> Last updated: 2026-02-06
> Scope: Codex-owned files, automation hygiene, and integration quality

## Why This Exists

Codex and Claude often run in parallel in this repo. This playbook keeps Codex-specific assets from drifting and turns local findings into practical upgrades.

## Core Loop (10-20 min)

1. Run Codex worktree triage:
   - `python3 scripts/ops/codex_automation_report.py`
2. Run safety audit:
   - `scripts/ops/codex_safety_audit.sh --hooks-only --with-scans`
3. Verify MCP availability:
   - `CODEX_HOME=.codex codex mcp list`
4. Run skill audit:
   - `scripts/ops/codex_skill_audit.sh --save`
5. Run unified daily health:
   - `scripts/ops/codex_daily_health.sh --save`
6. Capture action items:
   - Append actionable items to `HUMAN_TODO.md` only if they are owner-clear and testable.

## Cherry-Pick Rubric

Treat a worktree change as `keep` only if all are true:

- It reduces real operator friction or improves safety.
- It avoids hidden state or brittle local assumptions.
- It is easy to validate in one command.
- It does not duplicate existing functionality.

Treat as `discard` when it is mostly cache/artifact churn.

## Codex-Owned Surfaces To Keep Healthy

- `.codex/config.toml.example`
- `.codex/setup.sh`
- `.codex/skills/`
- `scripts/ops/codex_automation_report.py`
- `scripts/ops/codex_automation_triage.py`
- `scripts/ops/codex_safety_audit.sh`
- `scripts/ops/codex_skill_audit.sh`
- `scripts/ops/codex_daily_health.sh`
- `scripts/ops/codex_safe_prune_plan.sh`
- `docs/development/CODEX53_OPUS46_RAG_WORKFLOW.md`
- `docs/rag-knowledge/codex53-vs-opus46-capabilities.md`

## Current Improvement Priorities

1. Reduce false-positive signal in worktree triage.
2. Keep hook/PII scan checks one command away from startup.
3. Keep MCP key loading stable when `.env` values are placeholders.
4. Keep skill namespace drift visible (duplicate names, missing frontmatter).
5. Maintain Codex/Claude parallel-edit guidance in AGENTS docs.

## Ideation Backlog

These are high-value next candidates:

1. Add JSON output mode to `scripts/ops/codex_safety_audit.sh` for dashboards.
2. Add optional `--diff-main` mode in worktree triage scripts for stronger cherry-pick ranking.
3. Add a single `scripts/ops/codex_self_check.sh` entrypoint that runs triage + safety + MCP health and writes one report.
4. Add CI lint/test for Codex ops scripts (`shellcheck` + `ruff` where applicable).
5. Add automated stale-doc detector for Codex docs using last update metadata.
6. Add a diff-aware mode to `codex_skill_audit.sh` (detect new/removed skills since last report).

## Done Criteria For Any Codex Improvement

- Change is small and composable.
- Validation command and output are documented in commit/PR notes.
- No local secret material is added to tracked files.
- At least one user-facing friction point is reduced.
