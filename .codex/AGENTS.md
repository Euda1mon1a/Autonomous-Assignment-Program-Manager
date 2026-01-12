# Codex Agent Instructions

> Codex reads this file before starting work. See also: `docs/development/AGENTS.md` for monitoring patterns.

---

## Project Context

**Residency Scheduler** - Military medical residency scheduling with ACGME compliance.

- **Backend**: FastAPI, SQLAlchemy 2.0, PostgreSQL, Celery/Redis
- **Frontend**: Next.js 14, React 18, TailwindCSS
- **MCP Server**: 34+ AI tools for scheduling, validation, resilience

---

## Open Tasks

### Task 1: MCP Server Tests Failing in CI

**Priority:** HIGH
**Status:** Open
**Created:** 2026-01-11

**Problem:**
- `mcp-server-tests` job fails on every CI run (including main branch)
- Failed tests: test_api_client.py, test_resilience_integration.py, test_server.py
- Likely root cause: Integration tests require running backend; CI doesn't start containers (confirm via CI logs)

**Files to examine:**
- `.github/workflows/ci-tests.yml` (CI workflow)
- `mcp-server/tests/test_api_client.py` (failing tests)
- `mcp-server/tests/conftest.py` (test fixtures)
- `mcp-server/tests/test_resilience_integration.py`

**Options to evaluate:**
1. Add pytest markers: `@pytest.mark.integration` and skip in CI
2. Add httpx response mocking for API client tests
3. Add backend service to CI workflow (docker-compose)

**Deliverable:**
- Recommend best approach
- Capture failing CI log signature to confirm root cause
- Implement the fix
- Ensure CI passes for MCP tests

---

### Task 2: Seaborn Warning Cleanup

**Priority:** HIGH
**Status:** Open
**Created:** 2026-01-11

**Problem:**
Every Python command in backend container logs:
```
seaborn not available - enhanced visualization disabled
```

**Context:**
- Some analytics code optionally imports seaborn for statistical charts
- Seaborn is NOT used for frontend heatmaps (those use Plotly.js)
- The warning is visual noise

**Files to examine:**
- `backend/` (search for seaborn imports and warning text)

**Task:**
1. Grep for "seaborn" in `backend/`
2. Determine if seaborn is actually used anywhere
3. If unused: Remove the import and warning entirely
4. If used: Silence the warning or add seaborn to requirements

**Preference:** Remove if unused (per HUMAN_TODO recommendation)

**Deliverable:**
- PR that eliminates the seaborn warning from logs
- No functional regression

---

### Task 3: MCP API Client 401 Token Refresh

**Priority:** HIGH
**Status:** Open
**Created:** 2026-01-11

**Problem:**
MCP API client caches JWT token indefinitely. If token expires or is invalidated,
client returns 401 for all calls until container restart.

**File:** `mcp-server/src/scheduler_mcp/api_client.py`

**Current behavior (~line 50):**
```python
async def _ensure_authenticated(self) -> dict[str, str]:
    if self._token is None:  # Doesn't detect expired tokens
        await self._login()
    return {"Authorization": f"Bearer {self._token}"}
```

**Proposed fix:**
```python
async def _request_with_retry(
    self,
    method: str,
    url: str,
    *,
    _token_refreshed: bool = False,
    **kwargs,
) -> httpx.Response:
    # ... existing retry logic ...

    # On 401, try refreshing token once before giving up
    if response.status_code == 401 and not _token_refreshed:
        logger.warning("Received 401 Unauthorized, attempting token refresh")
        self._token = None  # Clear stale token
        headers = dict(kwargs.get("headers", {}))
        headers.update(await self._ensure_authenticated())
        kwargs["headers"] = headers
        return await self._request_with_retry(
            method,
            url,
            _token_refreshed=True,
            **kwargs,
        )
```

**Tests to add:**
- Unit test: 401 triggers token refresh
- Unit test: Second 401 after refresh raises (prevents loop)
- Integration test: Token expiry recovery

**Deliverable:**
- Implement the fix per spec above
- Add tests
- Ensure existing MCP tests still pass

---

## Completed Tasks

(none yet)

---

## Conventions

See `docs/development/AGENTS.md` for:
- Code rot detection patterns
- Consistency drift checks
- Type safety enforcement
- Performance pattern detection
