# Codex Task Tracker

> Tasks suitable for GitHub Codex async investigation via IDE
> **Last Updated:** 2026-01-11
> **Integration:** `/check-codex` skill, `codex-feedback-monitor.yml` workflow

---

## Open Tasks

### [HIGH] MCP Server Tests Failing in CI

- **Status:** Open
- **Created:** 2026-01-11
- **Source:** HUMAN_TODO.md
- **Files:**
  - `.github/workflows/ci-tests.yml`
  - `mcp-server/tests/test_api_client.py`
  - `mcp-server/tests/test_resilience_integration.py`
  - `mcp-server/tests/conftest.py`

**Codex Prompt:**
```
Investigate why MCP server tests fail in CI but pass locally.

**Problem:**
- `mcp-server-tests` job fails on every CI run (including main branch)
- Failed tests: test_api_client.py, test_resilience_integration.py, test_server.py
- Root cause: Integration tests require running backend, CI doesn't start containers

**Files to examine:**
- .github/workflows/ci-tests.yml (CI workflow)
- mcp-server/tests/test_api_client.py (failing tests)
- mcp-server/tests/conftest.py (test fixtures)
- mcp-server/tests/test_resilience_integration.py

**Options to evaluate:**
1. Add pytest markers: `@pytest.mark.integration` and skip in CI
2. Add httpx response mocking for API client tests
3. Add backend service to CI workflow (docker-compose)

**Deliverable:**
- Recommend best approach
- Implement the fix
- Ensure CI passes for MCP tests
```

---

### [HIGH] Seaborn Warning Cleanup

- **Status:** Open
- **Created:** 2026-01-11
- **Source:** HUMAN_TODO.md
- **Files:** `backend/` (grep for seaborn)

**Codex Prompt:**
```
Remove unnecessary seaborn import that clutters backend logs.

**Problem:**
Every Python command in backend container logs:
"seaborn not available - enhanced visualization disabled"

**Context:**
- Some analytics code optionally imports seaborn for statistical charts
- Seaborn is NOT used for frontend heatmaps (those use Plotly.js)
- The warning is visual noise

**Task:**
1. Grep for "seaborn" in backend/
2. Determine if seaborn is actually used anywhere
3. If unused: Remove the import and warning entirely
4. If used: Silence the warning or add seaborn to requirements

**Preference:** Remove if unused (per HUMAN_TODO recommendation)

**Deliverable:**
- PR that eliminates the seaborn warning from logs
- No functional regression
```

---

### [HIGH] MCP API Client 401 Token Refresh

- **Status:** Open
- **Created:** 2026-01-11
- **Source:** HUMAN_TODO.md
- **Files:** `mcp-server/src/scheduler_mcp/api_client.py`

**Codex Prompt:**
```
Implement automatic token refresh on 401 Unauthorized in MCP API client.

**Problem:**
MCP API client caches JWT token indefinitely. If token expires or is invalidated,
client returns 401 for all calls until container restart.

**File:** mcp-server/src/scheduler_mcp/api_client.py

**Current behavior (line ~50):**
```python
async def _ensure_authenticated(self) -> dict[str, str]:
    if self._token is None:  # Doesn't detect expired tokens
        await self._login()
    return {"Authorization": f"Bearer {self._token}"}
```

**Proposed fix:**
```python
async def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
    # ... existing retry logic ...

    # On 401, try refreshing token once before giving up
    if response.status_code == 401 and not kwargs.get("_token_refreshed"):
        logger.warning("Received 401 Unauthorized, attempting token refresh")
        self._token = None  # Clear stale token
        kwargs["headers"] = await self._ensure_authenticated()
        kwargs["_token_refreshed"] = True  # Prevent infinite loop
        return await self._request_with_retry(method, url, **kwargs)
```

**Tests to add:**
- Unit test: 401 triggers token refresh
- Unit test: Second 401 after refresh raises (prevents loop)
- Integration test: Token expiry recovery

**Deliverable:**
- Implement the fix per spec above
- Add tests
- Ensure existing MCP tests still pass
```

---

## Completed Tasks

(none yet)

---

## Usage

1. Copy the **Codex Prompt** block for a task
2. Paste into Codex IDE (VS Code / GitHub)
3. When Codex submits PR, update status here
4. Move to Completed when merged

## Related Files

- `CODEX_REVIEW_FINDINGS.md` - Historical findings from Codex reviews
- `.github/workflows/codex-feedback-monitor.yml` - Auto-labels PRs with Codex feedback
- `.claude/skills/check-codex/SKILL.md` - Skill to fetch Codex comments
