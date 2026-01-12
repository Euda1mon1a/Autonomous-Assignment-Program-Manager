# Codex Agent Instructions

> Codex reads this file before starting work. See also: `docs/development/AGENTS.md` for monitoring patterns.

---

## 🎯 ACTIVE TASK: MCP Server Tests Failing in CI

**Branch:** Create `codex/fix-mcp-ci-tests` from `main`

**Mission:** Make `mcp-server-tests` CI job pass without breaking local integration tests.

**Steps:**
1. Check recent CI run logs: `gh run list --workflow=ci-tests.yml --limit=3`
2. Find the specific failure: `gh run view <run-id> --log-failed`
3. Confirm root cause is "backend not running" (look for connection refused, 401, timeout)
4. Implement fix using **Option 2** (httpx mocking) - cleanest, no CI infrastructure changes
5. Run tests locally: `cd mcp-server && pytest tests/ -v`
6. Push and verify CI passes

**Mocking pattern for api_client tests:**
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient") as mock:
        client = AsyncMock()
        mock.return_value.__aenter__.return_value = client
        yield client

@pytest.mark.asyncio
async def test_health_check_success(mock_httpx_client):
    mock_httpx_client.request.return_value = MockResponse(200, {"status": "healthy"})
    # ... test logic
```

**Commit message format:** `fix(mcp): mock API client tests for CI compatibility`

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

### Task 2: MCP API Client 401 Token Refresh - TESTS ONLY

**Priority:** MEDIUM
**Status:** Open
**Created:** 2026-01-11
**Updated:** 2026-01-11

**Context:**
The 401 token refresh logic was already implemented in PR #608 (`e6c4440e`).
The implementation is complete at lines 113-121 of `api_client.py`.

**Remaining work:** Add unit tests for the 401 refresh behavior.

**File:** `mcp-server/tests/test_api_client.py`

**Tests to add:**
- Unit test: 401 triggers token refresh (mock httpx to return 401 then 200)
- Unit test: Second 401 after refresh raises (prevents infinite loop)
- Unit test: Non-401 errors don't trigger token refresh

**Example test pattern:**
```python
@pytest.mark.asyncio
async def test_401_triggers_token_refresh(mock_client):
    """401 response should trigger token refresh and retry."""
    # First call returns 401, second returns 200
    mock_client.request.side_effect = [
        MockResponse(401, {}),
        MockResponse(200, {"data": "success"}),
    ]

    async with SchedulerAPIClient(config) as client:
        client._token = "expired_token"
        result = await client.health_check()

    assert result is True
    assert mock_client.request.call_count == 2
```

**Deliverable:**
- Add tests to `test_api_client.py`
- Ensure CI passes

---

## Completed Tasks

### ~~Task 2~~ → Seaborn Warning Cleanup ✓

**Completed:** 2026-01-11
**Commit:** `9200055e`

Removed unused seaborn import attempt from `spin_glass_visualizer.py`.
Warning no longer appears in container logs.

### ~~Task 3~~ → MCP API Client 401 Token Refresh (Implementation) ✓

**Completed:** PR #608 (`e6c4440e`)

The 401 token refresh is implemented in `api_client.py` lines 113-121.
Tests still needed (see Task 2 above).

---

## Conventions

See `docs/development/AGENTS.md` for:
- Code rot detection patterns
- Consistency drift checks
- Type safety enforcement
- Performance pattern detection
