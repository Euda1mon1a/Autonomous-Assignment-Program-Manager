# Local-First Runtime Refactor Roadmap (Mac mini)

> **Created:** 2026-02-08  
> **Status:** Proposed  
> **Owner:** Platform / Backend  
> **Goal:** Make macOS local runtime the default operational path and keep Docker/Render as optional fallback only.

---

## Objectives

1. Local stack boots reliably with one command.
2. Backend, frontend, Celery, Redis, Postgres, and MCP run without container assumptions.
3. CI, tests, and scripts stop hard-coding Docker/Render-first behavior.
4. Docs reflect local-first operation for onboarding and day-to-day use.

---

## Scope

### In Scope
- Local bootstrap and runtime scripts.
- Environment defaults for local execution.
- Makefile local targets.
- Health, backup, and ops scripts for local stack.
- Documentation updates for local-first workflow.

### Out of Scope
- Full removal of Docker assets.
- Cloud hosting redesign.
- Feature/domain logic changes unrelated to runtime topology.

---

## Phase Plan

## Phase 0 - Baseline and Guardrails (0.5 day)
- Capture current startup/runtime behavior and known breakpoints.
- Define acceptance checks for auth, schedule validation, resilience endpoints, MCP health.
- Freeze high-risk migrations while runtime path changes are in progress.

## Phase 1 - Local Runtime Default (1 day)
- Standardize local service ports and env defaults.
- Ensure `scripts/start-local.sh` and `Makefile` local targets are canonical.
- Ensure backend health checks and MCP endpoint references are consistent.

## Phase 2 - Script and Ops Consolidation (1 day)
- Consolidate setup/start/stop/status under `scripts/` with local-first naming.
- Ensure backup/restore and health check scripts operate cleanly against local services.
- Remove Render-specific assumptions from developer scripts and local docs.

## Phase 3 - Test and Hook Alignment (1 day)
- Update tests/fixtures relying on container-only DB assumptions.
- Ensure pre-commit/quality hooks pass under local-first flow.
- Add a targeted smoke script for post-change local verification.

## Phase 4 - Documentation and Handoff (0.5-1 day)
- Update README quickstart and operations runbook.
- Document fallback Docker workflow as optional.
- Add troubleshooting matrix for local services (DB auth, Redis, Celery, MCP).

## Phase 5 - Optional De-Dockerization Sweep (optional, 1-2 days)
- Archive or reduce unused Docker/Render helpers.
- Keep minimal compatibility path for parity testing.

---

## Acceptance Criteria

1. `make local-start` (or equivalent) boots the full stack successfully.
2. Auth flow works and role-scoped routes remain accessible.
3. Schedule validation and resilience endpoints return valid responses.
4. MCP server can call core tools without Docker dependency.
5. Pre-commit and targeted tests pass in local-first mode.
6. README and master docs point to local-first workflow first.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Hidden Docker-only assumptions in scripts/tests | Medium | Add explicit local smoke checks per phase |
| Environment drift across developers | Medium | Publish canonical `.env.example` defaults and setup script |
| Breaking existing Docker users | Low | Keep Docker path as documented fallback |
| Hook/test instability during migration | Medium | Land changes in small, testable batches |

---

## Deliverables

- Updated local-first scripts and Makefile targets.
- Updated docs (README + ops + setup).
- Local smoke checklist and test notes.
- Priority tracking entry in `docs/MASTER_PRIORITY_LIST.md`.
