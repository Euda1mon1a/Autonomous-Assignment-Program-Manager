# Codex Agent Instructions

> Codex reads this file before starting work. See also: `docs/development/AGENTS.md` for monitoring patterns.

---

## 🎯 ACTIVE TASK: None

Last completed: MCP server CI test mocking (see Completed Tasks).

---

## Project Context

**Residency Scheduler** - Military medical residency scheduling with ACGME compliance.

- **Backend**: FastAPI, SQLAlchemy 2.0, PostgreSQL, Celery/Redis
- **Frontend**: Next.js 14, React 18, TailwindCSS
- **MCP Server**: 34+ AI tools for scheduling, validation, resilience

---

## Open Tasks

(none)

## Completed Tasks

### MCP Server Tests Failing in CI ✓

**Completed:** 2026-01-11
**Commit:** `c2e8ace8`

Mocked API client tests to avoid backend calls and added 401 refresh unit coverage.

### MCP API Client 401 Token Refresh (Tests) ✓

**Completed:** 2026-01-11
**Commit:** `c2e8ace8`

Added unit tests for token refresh, second-401 guard, and non-401 behavior.

### Seaborn Warning Cleanup ✓

**Completed:** 2026-01-11
**Commit:** `9200055e`

Removed unused seaborn import attempt from `spin_glass_visualizer.py`.
Warning no longer appears in container logs.

### MCP API Client 401 Token Refresh (Implementation) ✓

**Completed:** PR #608 (`e6c4440e`)

The 401 token refresh is implemented in `api_client.py` lines 113-121.
Tests added in `c2e8ace8`.

---

## Conventions

See `docs/development/AGENTS.md` for:
- Code rot detection patterns
- Consistency drift checks
- Type safety enforcement
- Performance pattern detection
