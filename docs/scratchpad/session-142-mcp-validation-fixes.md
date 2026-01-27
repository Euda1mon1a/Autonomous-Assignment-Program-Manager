# Session 142: MCP Validation & Docker Fixes

**Date:** 2026-01-26
**Branch:** `cpsat-pipeline-next`
**Focus:** Fix MCP tool validation failures and Docker container startup issues

---

## Issues Addressed

### 1. Docker Backend Restart Loop
**Symptom:** Backend container kept restarting with `uvicorn: No such option: -c`

**Root Cause:** `docker-compose.local.yml` command used `sh -c "..."` but `docker-entrypoint.sh` already handles migrations and uvicorn. The entrypoint appends `"$@"` to uvicorn, so `sh -c ...` became invalid args.

**Fix:** Changed command from full shell script to just `["--reload"]`

```yaml
# Before (broken):
command: >
  sh -c "alembic upgrade head && uvicorn ... --reload"

# After (works):
command: ["--reload"]
```

### 2. Redis Double-Password Bug
**Symptom:** `invalid username-password pair` on Redis connection

**Root Cause:** `REDIS_URL` already contained password, and `config.py:redis_url_with_password` added it again, creating malformed URL:
```
redis://:password@:password@redis:6379/0
```

**Fix:** Removed password from `REDIS_URL` in docker-compose.local.yml (3 occurrences)

### 3. Block Quality Report Date/Year Bug
**Symptom:** Report header showed wrong dates (2025-03-13 → 2026-04-08, AY 2024)

**Root Cause:**
- `get_block_dates()` queried by block_number without academic year filter
- Hardcoded `academic_year=2025` defaults everywhere
- Didn't use existing `academic_blocks.py` utility

**Fix:**
- Updated `block_quality_report_service.py` to use canonical `get_block_dates_util()`
- Made `academic_year` required parameter (no defaults)
- MCP tools and CLI now auto-derive from current date if not specified

### 4. Conflicts Endpoint 404
**Symptom:** MCP `detect_conflicts_tool` returned 404

**Root Cause:** Path mismatch:
- MCP client called: `/api/v1/conflicts/analyze`
- Actual backend: `/api/v1/conflicts/analysis/analyze`

**Fix:** Updated MCP client to use correct path

### 5. validate_schedule_by_id Tool Broken
**Symptom:** Tool called `client.post()` which doesn't exist

**Root Cause:** `SchedulerAPIClient` has domain-specific methods, no generic `post()`

**Fix:**
- Added `validate_schedule_by_id()` method to `api_client.py`
- Updated tool to use new method

### 6. Swap Candidates 500 Error
**Symptom:** Backend 500 on `/schedule/swaps/candidates`

**Root Cause:** Mixed sync/async DB operations:
- Endpoint was `async def` but used `Depends(get_db)` (sync session)
- Used `db.query()` (SQLAlchemy 1.x API) instead of `await db.execute(select())`

**Fix:**
- Changed to `Depends(get_async_db)` with `AsyncSession`
- Converted all `db.query()` to `await db.execute(select())`
- Added `await` to all `db.execute()` calls

---

## Files Modified

| File | Change |
|------|--------|
| `docker-compose.local.yml` | Fixed backend command, Redis URLs |
| `backend/app/services/block_quality_report_service.py` | Use utility, require academic_year |
| `mcp-server/src/scheduler_mcp/server.py` | Auto-derive academic_year |
| `scripts/generate_block_quality_report.py` | Auto-detect academic_year |
| `mcp-server/src/scheduler_mcp/api_client.py` | Fixed conflicts path, added validate_by_id |
| `mcp-server/src/scheduler_mcp/tools/validate_schedule.py` | Use new method |
| `backend/app/api/routes/schedule.py` | Async session + query fixes |

---

## Validation Status (Post-Fix)

| Tool | Before | After |
|------|--------|-------|
| validate_schedule_tool | OK | OK |
| detect_conflicts_tool | 404 | Fixed |
| validate_schedule_by_id_tool | Broken | Fixed |
| swap_candidates | 500 | Fixed |
| block_quality_report | Wrong dates | Fixed |

---

## Key Learnings

1. **Docker entrypoint + compose command interaction:** Don't duplicate what entrypoint does
2. **Config property composition:** Watch for double-application of transformations
3. **Async endpoint pattern:** `async def` + `get_db` + `db.query()` = subtle bugs
4. **Path registration:** Prefix + decorator = full path (watch for duplication)

---

*Session 142 - MCP/Docker Infrastructure Fixes*
