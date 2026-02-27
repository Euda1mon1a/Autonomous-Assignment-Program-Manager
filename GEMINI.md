# Gemini CLI Guardrails (Startup)

This `GEMINI.md` exists so Gemini CLI loads critical guardrails for this repo at startup.

Authoritative references:
- `CLAUDE.md` (project-wide engineering, security, and contract rules)
- `AGENTS.md` (condensed guardrails shared across all AI agents)
- `docs/development/AGENTS.md` (monitoring patterns, cross-system file discovery)

If there is any conflict, follow the strictest rule.

---

## HARD BOUNDARIES (NEVER CROSS)

### Validation and types
- NEVER remove or relax Pydantic constraints (`min_length`, `max_length`, `ge`, `le`, `regex`, `pattern`).
- NEVER weaken type annotations (for example `dict[str, int]` to `dict[str, Any]`).
- NEVER add `extra="allow"` / `ConfigDict(extra="allow")` to Pydantic models.
- NEVER change `Literal[...]` types to plain `str`.

### Error handling and security
- NEVER replace generic client-safe errors with `str(e)`.
- NEVER add try/except fallback behavior that can mask failures or create ghost state.
- NEVER reduce authentication or authorization checks.
- NEVER remove rate limiting.
- NEVER log or commit sensitive data (PII, schedules, credentials, deployment data).

### Code structure and scope
- NEVER change function signatures or return types without updating all callers.
- NEVER register a FastAPI router at multiple prefixes.
- NEVER change algorithm thresholds/constants unless explicitly requested.
- NEVER modify more than 30 files in one branch.

### Scheduling and compliance
- NEVER modify scheduling logic, ACGME compliance rules, or constraint definitions without explicit approval.
- NEVER modify models without creating a new Alembic migration.
- NEVER edit existing Alembic migrations.

---

## Code Change Safety Classification

| Change Type | Safety |
|---|---|
| Add `from e` to exception handlers | SAFE |
| Reorder imports | SAFE |
| Fix `datetime.utcnow()` to `datetime.now(UTC)` and both sides of comparisons | SAFE |
| Remove unused imports | CHECK |
| Add type annotations | CHECK |
| Remove Pydantic field constraints | FORBIDDEN |
| Add snake_case/camelCase normalization functions in backend | FORBIDDEN |
| Change Pydantic Field defaults without explicit instruction | FORBIDDEN |
| Add try/except fallback patterns | FORBIDDEN |
| Change error message text to `str(e)` | FORBIDDEN |
| Register routers at new prefixes without explicit instruction | FORBIDDEN |

---

## Known Anti-Patterns to Avoid

- Flexible Validation: removing strict constraints (for example dropping `min_length=32` on webhook secrets).
- Normalization Layer: adding backend `_normalize_*()` response converters for snake/camel case.
- Improved Error Messages: exposing internals with `str(e)` in API responses.
- Defensive Fallback: converting hard failures into silent alternate write paths.

---

## Project Context

**Residency Scheduler** — Military medical residency scheduling with ACGME compliance.

- **Backend**: FastAPI, SQLAlchemy 2.0, PostgreSQL, Celery/Redis
- **Frontend**: Next.js 14, React 18, TailwindCSS
- **MCP Server**: 97+ AI tools at `http://127.0.0.1:8081/mcp`

See `CLAUDE.md` for full project rules, API type contracts, and security requirements.

### Task Lists (Single Source of Truth)

- **Agent tasks:** `TODO.md` (root) — prioritized batches for autonomous work
- **Human tasks:** `HUMAN_TODO.md` (root) — requires human action (accounts, config, decisions)
- **Do NOT create separate task lists** — all agents share the same `TODO.md`

---

## Running Tests

The backend config validates secrets at import time (`backend/app/core/config.py`). Tests require either `DEBUG=true` (relaxes validation to warnings) or strong auto-generated secrets.

### Quick Test Run (SQLite in-memory, no PostgreSQL needed)

Set env vars then run pytest from `backend/`:

    export DEBUG=true
    cd backend && pytest -v --tb=short

The conftest will auto-select SQLite in-memory when no database URL is set.

### Full Test Run (against PostgreSQL)

Generate strong secrets first, then export them before running pytest:

    export DEBUG=true
    python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
    # Copy output and set as your DB password and Redis password env vars
    cd backend && pytest -v --tb=short

See `backend/.env.example` for all required env var names.

### Unit Tests Only (no DB, no Redis)

    export DEBUG=true
    cd backend && pytest tests/test_call_equity_ytd.py tests/constraints/ -v --noconftest

### Frontend Tests

```bash
cd frontend && npm test
```

### Why DEBUG=true Is Required

`conftest.py` imports `from app.main import app`, which initializes `Settings()`. The `validate_secrets()` validator in `config.py` raises `ValueError` for weak/default credentials when `DEBUG=false`. Setting `DEBUG=true` relaxes validators to warnings only.

**NEVER use `DEBUG=true` in production.** This is safe ONLY for local test runs.

### Test Markers

- `@pytest.mark.requires_db` — needs PostgreSQL
- `@pytest.mark.integration` — integration tests
- `@pytest.mark.acgme` — ACGME compliance tests
- `@pytest.mark.slow` — long-running tests

### Notes

- `--noconftest` skips `conftest.py` entirely (useful for pure unit tests without DB/app fixtures)
- SQLite in-memory automatically skips pgvector and JSONB columns (see `conftest.py` line 72-82)
- Coverage threshold is 70% (`pytest.ini` `fail_under` setting)
