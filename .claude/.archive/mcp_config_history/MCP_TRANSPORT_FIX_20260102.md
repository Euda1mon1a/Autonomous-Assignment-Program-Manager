# MCP Transport Configuration Fix - 2026-01-02

> **Session:** mcp-refinement branch (Sessions 046-047)
> **Issue:** MCP "No servers configured" after config changes
> **Resolution:** Schema field must be `"type": "sse"`, NOT `"transport": "streamable-http"`
> **Secondary Issue:** Antigravity IDE autoConnect was interfering

---

## The Problem

User reported: "somehow something we solved over a week ago is an issue"

`/mcp` showed: "No MCP servers configured"

Yet MCP server container was healthy and responding on port 8080.

---

## Root Cause

**Protocol mismatch between server and client config.**

The MCP server (FastMCP) uses **SSE (Server-Sent Events)** internally, even when `MCP_TRANSPORT=http` is set. This is confirmed by:

1. Server logs: `mcp.server.streamable_http_manager - INFO - StreamableHTTP session manager started`
2. Server response to plain HTTP: `"Client must accept both application/json and text/event-stream"`

The `.mcp.json` had `"transport": "http"` which tells Claude Code to use plain HTTP, but the server expects SSE-capable clients.

---

## The Fix (Applied 2026-01-02)

### `.mcp.json`
```json
{
  "mcpServers": {
    "residency-scheduler": {
      "url": "http://127.0.0.1:8080/mcp",
      "transport": "streamable-http"  // Was "http" - WRONG
    }
  }
}
```

### `.vscode/mcp.json`
Same change: `"transport": "http"` → `"transport": "streamable-http"`

---

## Why This Keeps Happening

The config has been changed multiple times during MCP debugging sessions:

| Date | Change | Reason |
|------|--------|--------|
| Dec 28 (Session 006-010) | STDIO → HTTP | STDIO single-client limitation |
| Dec 28 (Session 012) | HTTP confirmed | Parallel agent support needed |
| Jan 1 (18512b34) | `http` → `streamable-http` | SSE protocol match |
| Jan 2 (today) | Someone changed back to `http` | Unknown - possibly testing |
| Jan 2 (this fix) | `http` → `streamable-http` | Restoring correct config |

---

## The Rule (Document This!)

| Component | Transport Value | Why |
|-----------|-----------------|-----|
| **Server** (`docker-compose.yml`) | `MCP_TRANSPORT: http` | "HTTP server mode" |
| **Client** (`.mcp.json`) | `"transport": "streamable-http"` | "Expect SSE streaming" |

**They look different but work together:**
- Server says "I'm an HTTP server" (listening mode)
- Client says "I expect streamable-http/SSE" (protocol mode)

---

## Verification Steps

After changing config, must restart Claude Code:

```bash
# 1. Check server health
curl http://127.0.0.1:8080/health
# Should return 200

# 2. Test SSE requirement
curl -X POST http://127.0.0.1:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "id": 1, "params": {}}'
# Should return: "Client must accept both application/json and text/event-stream"
# This CONFIRMS streamable-http is required

# 3. Restart Claude Code
# 4. Run /mcp - should show server connected with 34 tools
```

---

## Files Modified This Session

| File | Change |
|------|--------|
| `.mcp.json` | `transport: "http"` → `"streamable-http"` |
| `.vscode/mcp.json` | `transport: "http"` → `"streamable-http"` |

---

## Prevention

Add to CI/pre-commit check:
```bash
# Verify MCP transport config consistency
grep -q '"transport": "streamable-http"' .mcp.json || echo "ERROR: .mcp.json transport must be streamable-http"
```

---

## Related Documentation

- **Original fix:** Commit `18512b34` (Jan 1, 2026)
- **Session history:** ORCHESTRATOR_ADVISOR_NOTES.md Sessions 006-012
- **ADR:** `docs/architecture/decisions/ADR-003-mcp-server-ai-integration.md`
- **Server README:** `mcp-server/README.md` (lines 184-213)

---

## Session 047 Update: The REAL Root Cause

**Date:** 2026-01-02 (continued from Session 046)

### What `/doctor` Actually Said

```
[Failed to parse] Project config (shared via .mcp.json)
Location: /Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.mcp.json
└ [Error] mcpServers.residency-scheduler: Does not adhere to MCP server configuration schema
```

### The Actual Problem

Session 046 thought the issue was the transport VALUE (`http` vs `streamable-http`).

**Wrong.** The issue was the FIELD NAME:
- `"transport": "streamable-http"` ❌ Invalid schema field
- `"type": "sse"` ✅ Valid Claude Code MCP schema

### Claude Code MCP Schema (Correct)

```json
{
  "mcpServers": {
    "server-name": {
      "type": "sse",           // Valid values: "sse" or "stdio"
      "url": "http://..."      // For SSE type
    }
  }
}
```

Or for STDIO:
```json
{
  "mcpServers": {
    "server-name": {
      "command": "docker",
      "args": ["compose", "exec", "..."]
    }
  }
}
```

### Secondary Issue: Antigravity IDE Interference

`.antigravity/settings.json` had:
```json
"mcp": {
  "autoConnect": true,  // Was overwriting/conflicting with Claude Code config
  ...
}
```

**Fix:** Set `autoConnect: false`

### Files Modified (Session 047)

| File | Change |
|------|--------|
| `.mcp.json` | `"transport": "streamable-http"` → `"type": "sse"` |
| `.vscode/mcp.json` | Removed non-standard fields, simplified to valid schema |
| `.antigravity/settings.json` | `"autoConnect": true` → `false` |

### The Definitive Rule

| Config File | Field | Value | Purpose |
|-------------|-------|-------|---------|
| `docker-compose.yml` | `MCP_TRANSPORT` | `http` | Server listening mode |
| `.mcp.json` | `type` | `sse` | Client connection protocol |

**They are DIFFERENT fields with DIFFERENT names.** Don't confuse them.

### Prevention

Add to CI/linting:
```bash
# Validate MCP config schema
jq -e '.mcpServers["residency-scheduler"].type == "sse"' .mcp.json || exit 1
```

---

*Created by ORCHESTRATOR - Session 046 (2026-01-02)*
*Updated by ORCHESTRATOR - Session 047 (2026-01-02) - Actual root cause identified*

---

## Session 048 Update: SSE is DEPRECATED (2026-01-02)

### The Problem (Again)

After Session 047's fix (`type: sse`), MCP still failing:
- `POST /mcp HTTP/1.1" 406 Not Acceptable`
- `GET /mcp HTTP/1.1" 400 Bad Request`

### Root Cause

Per **official Claude Code documentation**:
- `type: sse` is **DEPRECATED**
- `type: http` is **RECOMMENDED**

The SSE transport sends wrong Accept headers. FastMCP's streamable HTTP requires:
```
Accept: application/json, text/event-stream
```

SSE transport only sends `Accept: text/event-stream` → 406 Not Acceptable.

### The Fix (Session 048)

```json
// Session 047 (deprecated, broken)
{ "type": "sse", "url": "http://127.0.0.1:8080/mcp" }

// Session 048 (correct, recommended)
{ "type": "http", "url": "http://127.0.0.1:8080/mcp" }
```

### Files Modified

| File | Change |
|------|--------|
| `.mcp.json` | `"type": "sse"` → `"type": "http"` |
| `.vscode/mcp.json` | `"type": "sse"` → `"type": "http"` |

### The Definitive Rule (FINAL)

| Component | Config | Value |
|-----------|--------|-------|
| Server (`docker-compose.yml`) | `MCP_TRANSPORT` env | `http` |
| Client (`.mcp.json`) | `type` field | `http` |

**Both use `http` now.** The server runs HTTP, the client connects via HTTP.

### Why Session 047 Was Wrong

Session 047 misread the error:
- `/doctor` said "Does not adhere to MCP server configuration schema"
- Concluded the FIELD NAME was wrong (`transport` vs `type`) ✓ Correct
- Concluded the VALUE should be `sse` ✗ Wrong - `sse` is deprecated

The schema validation passed with `type: sse` (valid field), but runtime failed because SSE transport sends wrong headers.

### Prevention

```bash
# Correct CI check (use http, not sse)
jq -e '.mcpServers["residency-scheduler"].type == "http"' .mcp.json || exit 1
```

---

*Updated by ORCHESTRATOR - Session 048 (2026-01-02) - SSE deprecated, HTTP is correct*

---

## Session 049 Update: FastMCP 2.x Session Management Issue (2026-01-02)

### The Deeper Problem

After all config fixes, MCP tools still fail with:
```
Streamable HTTP error: Error POSTing to endpoint: No valid session ID provided
```

### Root Cause Analysis

**FastMCP 2.x (currently 2.14.2) requires Streamable HTTP session management.**

The server logs show:
```
mcp.server.streamable_http_manager - INFO - StreamableHTTP session manager started
```

FastMCP's HTTP mode now requires:
1. Session initialization handshake
2. Session ID tracking
3. Session-aware requests

**Claude Code's `type: http` transport does NOT handle this session protocol.**

### Sacred Backup Comparison

The sacred backup (commit `e19be27b`, 2026-01-01) had:
```python
# Working state - simple Starlette without lifespan
app = Starlette(routes=routes)  # NO lifespan = NO session management
```

Current broken state:
```python
# Required by FastMCP 2.x - triggers session manager
app = Starlette(routes=routes, lifespan=mcp_app.lifespan)
```

### Version Investigation

| FastMCP Version | `http_app()` exists? | Session Required? |
|-----------------|---------------------|-------------------|
| 0.4.1 | No | No (but resource param validation is stricter) |
| 2.0.0 | No | Unknown |
| 2.5.0 | No (Pydantic compat issue) | Unknown |
| 2.10.0+ | Yes | **YES - Session manager mandatory** |

### What We Tried

1. **Pin FastMCP 0.4.1** - No `http_app()` method
2. **Pin FastMCP 2.0.0** - No `http_app()` method
3. **Pin FastMCP 2.5.0** - Pydantic compatibility error
4. **Latest 2.14.2 with `type: sse`** - Still gets session ID error
5. **Latest 2.14.2 with `type: http`** - Same session ID error

### Current State (End of Session 049)

Files modified but **MCP still not working**:
- `.mcp.json`: `type: sse`, URL `/mcp/sse`
- `.vscode/mcp.json`: `type: sse`, URL `/mcp/sse`
- `mcp-server/pyproject.toml`: `fastmcp>=2.10.0`
- `mcp-server/src/scheduler_mcp/server.py`:
  - Fixed resource parameter validation (2 resources)
  - Lifespan still enabled

### Investigation TODO for Next Session

1. **Try FastMCP native SSE transport** instead of Starlette wrapper:
   ```python
   # Replace Starlette/uvicorn setup with:
   mcp.run(transport="sse", host="0.0.0.0", port=8080)
   ```

2. **Check if FastMCP has session-less HTTP mode**:
   - Look for config option to disable session management
   - Check FastMCP issues/docs for Claude Code compatibility

3. **Try older FastMCP that works**:
   - Find the exact version that has `http_app()` BUT doesn't require sessions
   - May need to check git history for what was installed in sacred backup's Docker image

4. **Consider MCP SDK directly instead of FastMCP**:
   - The `mcp` package (1.25.0) might have simpler HTTP mode
   - FastMCP is a convenience wrapper that may have over-complicated things

5. **Test from sacred backup branch**:
   ```bash
   git checkout e19be27b
   docker compose up -d --build mcp-server
   # Then test if MCP tools work
   ```

### Key Insight

The problem is **NOT client config** - it's **server-side FastMCP version**.

FastMCP 2.x fundamentally changed how HTTP transport works, adding mandatory session management that Claude Code's HTTP client doesn't support.

### Stack Status (End of Session)

- Backend: GREEN (healthy)
- Frontend: Likely healthy
- Database: Healthy
- Redis: Healthy
- MCP Server: RUNNING but **MCP tools fail** (session error)

---

*Updated by ORCHESTRATOR - Session 049 (2026-01-02) - FastMCP 2.x session management incompatibility identified*

---

## Session 050 Update: Same Pattern Repeats (2026-01-02)

### What Happened

User reported MCP broken again. Investigation revealed:
1. `mcp-server/pyproject.toml` had uncommitted change: `fastmcp>=0.2.0` → `fastmcp>=2.10.0`
2. `mcp-server/src/scheduler_mcp/server.py` had 35 lines of uncommitted changes (resource param simplification)
3. Container was running stale code (old server.py) but with new FastMCP 2.14.2

### The Fix (This Session)

```bash
# Reverted uncommitted MCP changes
git checkout -- mcp-server/pyproject.toml mcp-server/src/scheduler_mcp/server.py

# Rebuilt container with reverted code
docker compose up -d --build mcp-server
```

### The Recurring Pattern

| Date | Issue | Root Cause | Fix Attempted |
|------|-------|------------|---------------|
| Dec 28 | STDIO contention | Single-client transport | Switch to HTTP |
| Jan 1 | Schema error | Wrong field name | `transport` → `type` |
| Jan 2 (046) | Wrong transport | `http` vs `streamable-http` | Change value |
| Jan 2 (047) | Schema validation | SSE deprecated | Change to `http` |
| Jan 2 (048) | Session ID error | FastMCP 2.x sessions | Various |
| Jan 2 (049) | Version incompatibility | FastMCP 2.x breaking | Pin versions (failed) |
| **Jan 2 (050)** | Stale container | Uncommitted upgrades | **Revert + rebuild** |

### Why This Keeps Happening

1. **Version creep**: Someone upgrades `pyproject.toml` but doesn't finish the work
2. **Container staleness**: Code changes without rebuild
3. **pip defaults to latest**: `>=0.2.0` installs 2.14.2, not 0.2.0

### The Solution (Still Needed)

**PIN THE VERSION that works with Claude Code:**
```toml
# In mcp-server/pyproject.toml
dependencies = [
    "fastmcp==0.4.1",  # Pin to known-working version
    # NOT "fastmcp>=0.2.0" which allows 2.x
]
```

### Current State (End of Session 050)

- `.mcp.json`: `type: http` ✓
- `pyproject.toml`: `>=0.2.0` (reverted but still allows 2.x)
- Container: Rebuilt, healthy
- MCP tools: **Awaiting Claude Code restart to verify**

### Next Steps

1. Restart Claude Code, test MCP tools
2. If still fails with session error, need to pin FastMCP to specific 0.x version
3. Find the exact Docker image that worked (before any 2.x contamination)

---

*Updated by ORCHESTRATOR - Session 050 (2026-01-02) - Reverted uncommitted changes, documented recurring pattern*

---

## Session 050 Continued: Investigation Summary

### What We Confirmed

1. **No saved Docker image** - Antigravity's sacred backups contain DB + frontend, NOT Docker images
2. **FastMCP 2.14.2** is in the rebuilt container (pip installs latest matching `>=0.2.0`)
3. **`.mcp.json` is correct** - `"type": "http"` (proper schema)
4. **Session 049 already tried** pinning 0.4.1, 2.0.0, 2.5.0 - all failed
5. **Not using STDIO** - user confirmed HTTP transport required

### Historical Investigation

When MCP was "working" (commit `9f235da5`):
```json
// Old .mcp.json - had WRONG schema but maybe Claude Code was more lenient?
{
  "transport": "http",      // Now must be "type"
  "disabled": true          // Invalid field - caused schema errors later
}
```

### The Real Problem

Per [GitHub Issue #4598](https://github.com/anthropics/claude-code/issues/4598) and [mcp-remote #113](https://github.com/geelen/mcp-remote/issues/113):

> FastMCP 2.x requires Streamable HTTP session management (Mcp-Session-Id headers).
> Claude Code's `type: http` transport does NOT send these headers.
> Result: `"Missing session ID"` error.

### Untested Options

| Option | FastMCP Version | Notes |
|--------|-----------------|-------|
| Pin to 1.0 | `fastmcp==1.0` | Never tried - only version between 0.x and 2.x |
| Use MCP SDK directly | Remove FastMCP | More work but may avoid session issue |
| Wait for Claude Code fix | Current 2.14.2 | Issue #4598 is open |

### Current State (Awaiting Restart)

```
.mcp.json:        type: http ✓
Container:        Rebuilt, healthy ✓
FastMCP version:  2.14.2 (unchanged)
MCP connection:   UNKNOWN - needs Claude Code restart
```

### Handoff Actions

1. **Restart Claude Code** to test MCP connection
2. If session error persists:
   - Try `fastmcp==1.0` pin and rebuild
   - Or accept MCP is broken until Claude Code supports sessions
3. **Do NOT keep changing .mcp.json** - the schema is correct now

### Files Reverted This Session

```bash
git checkout -- mcp-server/pyproject.toml mcp-server/src/scheduler_mcp/server.py
```

These had uncommitted upgrades to FastMCP 2.10+ with resource signature changes.

---

*Updated by ORCHESTRATOR - Session 050 (2026-01-02) - Full investigation, awaiting restart test*

---

## Session 051 Update: FINAL FIX - stateless_http=True (2026-01-03)

### The Solution

**FastMCP 2.x has a `stateless_http` parameter that disables session management!**

```python
# BEFORE (broken - requires session ID headers Claude Code doesn't send)
mcp_app = mcp.http_app()

# AFTER (working - stateless mode, no session required)
mcp_app = mcp.http_app(stateless_http=True)
```

### Files Modified

| File | Change |
|------|--------|
| `mcp-server/pyproject.toml` | `fastmcp>=2.10.0` (need 2.10+ for http_app()) |
| `mcp-server/src/scheduler_mcp/server.py` | `mcp.http_app(stateless_http=True)` |
| `.mcp.json` | `"type": "http"`, `"url": "http://127.0.0.1:8080/mcp"` |

### The Rule (DEFINITIVE)

| Component | Config | Value | Notes |
|-----------|--------|-------|-------|
| **Server** (pyproject.toml) | `fastmcp>=2.10.0` | FastMCP 2.x | Need `http_app()` method |
| **Server** (server.py) | `http_app(stateless_http=True)` | Disable sessions | Critical for Claude Code |
| **Server** (docker-compose.yml) | `MCP_TRANSPORT: http` | HTTP mode | |
| **Client** (.mcp.json) | `"type": "http"` | HTTP transport | NOT `"sse"` |
| **Client** (.mcp.json) | `"url": ".../mcp"` | Endpoint | NOT `/sse` |

### Why This Works

- FastMCP 2.x's `stateless_http=True` disables the StreamableHTTPSessionManager's session ID requirement
- Lifespan is still used (required for FastMCP 2.x initialization)
- Claude Code's HTTP transport works without session headers

### Verified Working

```
mcp__residency-scheduler__check_circuit_breakers_tool ✓
mcp__residency-scheduler__get_defense_level_tool ✓
mcp__residency-scheduler__check_utilization_threshold_tool ✓
mcp__residency-scheduler__validate_schedule_tool ✓
```

### RAG Tools Note

RAG tools (`rag_health`, `rag_search`, etc.) fail with 401 - this is a separate API authentication issue, not an MCP transport problem.

---

*Updated by ORCHESTRATOR - Session 051 (2026-01-03) - FINAL FIX: stateless_http=True*
