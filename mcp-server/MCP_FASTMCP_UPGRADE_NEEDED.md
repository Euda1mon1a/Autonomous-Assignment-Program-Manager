# MCP Server - FastMCP API Upgrade Needed

> **Created:** 2025-12-27
> **Status:** Blocked - requires FastMCP API migration

## Summary

The MCP server is incompatible with the current FastMCP version (>=0.2.0). Multiple API changes need to be addressed before the server will start.

## Issues Fixed in This Branch

### 1. Namespace Collision (FIXED)
- **Problem**: `tools.py` module shadowed by `tools/` package
- **Fix**: Renamed `tools.py` → `scheduling_tools.py`
- **File**: `server.py` line 96 import updated

### 2. FastMCP Init API (FIXED)
- **Problem**: `description` parameter no longer exists
- **Fix**: Changed to `instructions` parameter
- **File**: `server.py` line 151-158

## Remaining Issues

### 3. Resource URI Templates (NOT FIXED)
```
ValueError: URI template must contain at least one parameter
```
- **Location**: `server.py` line 164
- **Cause**: Static resource URIs like `schedule://status` no longer allowed
- **Impact**: Both `@mcp.resource("schedule://status")` and `@mcp.resource("schedule://compliance")` fail

**Potential Fixes**:
1. Add dummy parameters: `schedule://status/{dummy}`
2. Use a different decorator for static resources
3. Pin to older FastMCP version that supports static URIs

### 4. Unknown Additional Issues
There may be more API changes after fixing issue #3. The FastMCP library appears to have undergone significant API changes.

## Recommended Next Steps

### Option A: Pin FastMCP Version
Find the last version that worked and pin it:
```toml
# pyproject.toml
"fastmcp==0.1.x",  # Find exact working version
```

### Option B: Full API Migration
1. Review FastMCP 0.2.0+ changelog
2. Update all resource decorators
3. Update any other changed APIs
4. Add comprehensive tests

## Files Modified

| File | Change |
|------|--------|
| `src/scheduler_mcp/tools.py` | Renamed to `scheduling_tools.py` |
| `src/scheduler_mcp/server.py` | Updated imports (line 96) and init (line 151) |

## Testing

Once fixes are complete:
```bash
docker compose build mcp-server
docker compose up -d mcp-server
docker compose exec -T mcp-server python -c \
  "from scheduler_mcp.server import mcp; print(f'Tools: {len(mcp._tools)}')"
```

Expected output: `Tools: 36`
