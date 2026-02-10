# Full Realization Execution Plan

**Date:** 2026-02-10  
**Status:** Active  
**Scope:** Autonomous work that does not require live DB migrations, Docker-only services, or external credentials.

## Baseline (Verified)

Current repo state already includes several items that were previously listed as Phase 1 work:

- Refresh-token endpoint rate limiting is implemented:
  - `backend/app/api/routes/auth.py`
  - `backend/app/core/config.py`
- `frontend/package-lock.json` is committed and tracked.
- Wellness medal rendering does not use `dangerouslySetInnerHTML`:
  - `frontend/src/app/wellness/page.tsx`
- Remaining `key={index}` findings from the 4-file list are already resolved.
- Frontend lint and type-check are currently clean.

## Codex Automation Program (Integrated)

Codex App nightly automation is now part of execution, not separate from it.

### Current automation fleet

- Total active automations: `38`
- Registry path: `~/.codex/automations`

### Nightly schedule model

- `00:59`: `gh-codex-comment-sweep` (runs first; open PRs + recently closed PRs)
- `01:00`: parallel worktree wave (quality, debt, tests, security, drift, docs)
- `02:00+`: sequential synthesis and health jobs
  - `codex-daily-health` (02:00)
  - `codex-safe-prune-plan` (02:04)
  - `codex-weekly-deep-health` (02:10, Sunday)
  - `surprise` (02:15)
  - `circuit-breaker-health-monitor` (02:25)
  - `burnout-precursor-scanner` (02:30)
- `05:00`: `codex-morning-brief`

### Operational intent

- Use worktree-isolated parallelism for independent checks/fixes.
- Keep only dependent summary/health tasks sequenced.
- Feed morning human decisions from Codex outputs before merge/publish work.

## Environment Parity Gate (RAG)

Current host split:

- Mini: PostgreSQL 17 + pgvector, RAG functional.
- Laptop: PostgreSQL 15 without pgvector, backend may run but RAG/vector paths are degraded.

Implication:

- Any task requiring vector extension (`CREATE EXTENSION vector`, RAG ingestion, similarity retrieval) is blocked on laptop until parity is restored.

Required decision:

1. Upgrade laptop local PostgreSQL to 17+ and install Homebrew pgvector (recommended).
2. Keep laptop on PG15 and use Docker pgvector DB for RAG-dependent work.
3. Build/install pgvector against PG15 locally (allowed but higher maintenance risk).

Upgrade runbook:

- `docs/deployment/LAPTOP_PG17_PGVECTOR_UPGRADE.md`

Execution policy:

- Treat laptop RAG issues as environment-parity blockers, not application-code regressions.
- Validate host capabilities before opening RAG bug-fix PRs.

## Revised Phase Plan

## Phase 0 - Re-baseline and de-duplicate (0.5-1h)

- Remove stale tasks from prior plan that are already complete.
- Recompute live metrics before each phase (warnings, skips, debt open count).
- Keep all claims tied to command output or file evidence.

## Phase 1 - Build quality gate enforcement (1-2h)

- Ensure frontend remains warning-free and type-safe.
- Enforce Next build gates (no lint/type bypasses).
- Fix build blockers that surface once gates are on.

## Phase 2 - Non-DB technical debt sweep (2-6h)

- DEBT-012 (frontend API URL consistency): confirm all frontend API callers use shared config.
- DEBT-019 (logout behavior): choose and implement deterministic client behavior on logout failure.
- DEBT-008 (targeted a11y): high-impact ARIA and semantic fixes for forms/tables/alerts.
- DEBT-022 (index-key sweep): audit and close remaining cases with stable keys.

## Phase 3 - Test quality and skip strategy (4-8h)

- Triage DEBT-015 calibration failures by domain.
- Triage DEBT-016 skipped tests with explicit marker policy.
- Register any new pytest markers before use (`--strict-markers` is enabled).
- Reduce “obsolete skip” count without forcing DB-only tests into pure-logic lanes.

## Phase 4 - Documentation synchronization (1-3h)

- Update `docs/planning/TECHNICAL_DEBT.md` from verified current state.
- Update `HUMAN_TODO.md` for true human-only blockers.
- Update `CHANGELOG.md` with completed work.
- Keep docs aligned with actual paths (`docs/planning/ROADMAP.md`, not root `ROADMAP.md`).

## Phase 5 - Frontend coverage expansion (4-8h)

- Add focused tests for high-value untested components/hooks.
- Prioritize scheduling-critical UI and auth/error paths over vanity coverage.
- Track coverage gain and runtime cost together.

## Out of Scope (Human / DB / infra dependent)

- Live DB schema reconciliation and migration execution validation.
- Laptop-native PG major upgrade and pgvector installation (tracked operational task).
- CP-SAT infeasibility reproduction requiring production-like data.
- SMTP/Slack credentialed integrations.
- Force-push history rewrites and cross-collaborator coordination tasks.

## Implementation Tracker (This Session)

- [x] Codex automation fleet expanded and scheduled for nightly execution.
- [x] `gh-codex-comment-sweep` added and moved to run first (`00:59`).
- [x] Frontend build bypass removal started:
  - Removed `eslint.ignoreDuringBuilds` and `typescript.ignoreBuildErrors` from `frontend/next.config.js`.
- [x] Native script parity hardening for PostgreSQL versions:
  - Updated native scripts to detect/start/stop PostgreSQL 17/18/16/15.
  - Added pgvector extension visibility warning in `scripts/start-native.sh`.
- [x] Validation run:
  - `cd frontend && npm run lint` (clean)
  - `cd frontend && npm run type-check` (clean)
  - `cd frontend && npm run build` (success)

## Notes

- Next.js emitted non-fatal lockfile patch warnings during build. Build completed successfully.
- Continue prioritizing small, verified, mergeable slices over long autonomous monolith changes.
