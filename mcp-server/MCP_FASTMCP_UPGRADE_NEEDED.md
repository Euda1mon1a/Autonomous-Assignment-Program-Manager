# MCP Server - FastMCP API Upgrade Needed

> **Created:** 2025-12-27
> **Status:** All known issues FIXED

## Summary

The MCP server has been updated for compatibility with FastMCP version (>=0.2.0). All known API changes have been addressed.

## Issues Fixed in This Branch

### 1. Namespace Collision (FIXED)
- **Problem**: `tools.py` module shadowed by `tools/` package
- **Fix**: Renamed `tools.py` → `scheduling_tools.py`
- **File**: `server.py` line 96 import updated

### 2. FastMCP Init API (FIXED)
- **Problem**: `description` parameter no longer exists
- **Fix**: Changed to `instructions` parameter
- **File**: `server.py` line 151-158

### 3. Resource URI Templates (FIXED)
- **Problem**: Static resource URIs like `schedule://status` no longer allowed
- **Error**: `ValueError: URI template must contain at least one parameter`
- **Fix**: Changed to templated URIs with `date_range` parameter:
  - `schedule://status` → `schedule://status/{date_range}`
  - `schedule://compliance` → `schedule://compliance/{date_range}`
- **Files**: `server.py` lines 164 and 189
- **New parameter**: `date_range: str = "current"` added to both resource functions

## Potential Future Issues

### 4. Unknown Additional Issues
There may be more API changes discovered during testing. The FastMCP library appears to have undergone significant API changes between versions.

## Recommended Next Steps

1. Build and test the MCP server container
2. Verify all 36 tools are registered correctly
3. Test resource endpoints with the new `date_range` parameter

## Files Modified

| File | Change |
|------|--------|
| `src/scheduler_mcp/tools.py` | Renamed to `scheduling_tools.py` |
| `src/scheduler_mcp/server.py` | Updated imports (line 96), init (line 151), and resource decorators (lines 164, 189) |

## Testing

Once fixes are complete:
```bash
docker compose build mcp-server
docker compose up -d mcp-server
docker compose exec -T mcp-server python -c \
  "from scheduler_mcp.server import mcp; print(f'Tools: {len(mcp._tools)}')"
```

Expected output: `Tools: 36`
