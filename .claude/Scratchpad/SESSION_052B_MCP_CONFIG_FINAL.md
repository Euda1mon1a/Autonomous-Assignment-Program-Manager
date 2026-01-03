# Session 052B: MCP Configuration - AUTHORITATIVE

> **Date:** 2026-01-02/03 (Hawaii/UTC)
> **Branch:** `fix/system-hardening-2026-01-02-b`
> **PR:** #612
> **Status:** MCP configs fixed, container rebuilt, awaiting Claude Code restart

---

## AUTHORITATIVE MCP CONFIGURATION

**This supersedes ALL prior Session 046/047/048/052 MCP config documentation.**

### Correct Schema

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "url": "http://127.0.0.1:8080/mcp",
      "type": "http"
    }
  }
}
```

### Key Facts

| Field | Correct Value | Wrong Values (DO NOT USE) |
|-------|---------------|---------------------------|
| Field name | `type` | `transport` |
| Field value | `"http"` | `"sse"`, `"streamable-http"` |
| URL path | `/mcp` | `/mcp/sse` |

### Config Locations (All Must Match)

| Location | Status | Content |
|----------|--------|---------|
| `.mcp.json` | UPDATED | `"type": "http"` |
| `.vscode/mcp.json` | UPDATED | `"type": "http"` |
| `~/.claude/config.json` | UPDATED | `"type": "http"` |

### Server Requirements

| Component | Requirement |
|-----------|-------------|
| FastMCP version | `==2.14.2` (pinned) |
| Server mode | `stateless_http=True` |
| Transport env | `MCP_TRANSPORT: http` |

---

## Changes Made This Session

1. **Cherry-picked** commit `bc1b46da` from `fix/system-hardening-2026-01-02` branch
   - Added `stateless_http=True` to `mcp-server/src/scheduler_mcp/server.py`
   - Added `MCP_TRANSPORT_FIX_20260102.md` scratchpad (quarantined - had wrong info)

2. **Fixed all config files** to use `type: http` (not `transport: http`)
   - `.mcp.json`
   - `.vscode/mcp.json`
   - `~/.claude/config.json`

3. **Rebuilt MCP container** with new server.py containing `stateless_http=True`

4. **Quarantined outdated files** to `.claude/Scratchpad/quarantine/`:
   - `MCP_TRANSPORT_FIX_20260102.md` - Had wrong `streamable-http` and `type: sse` info
   - `SESSION_052_INFRASTRUCTURE_REBUILD.md` - Had wrong `transport: http` examples
   - `SESSION_052_MCP_INFRASTRUCTURE_REBUILD.md` - Had wrong config examples

---

## Validation

Run `scripts/validate-mcp-config.sh` to verify config is correct:

```bash
$ bash scripts/validate-mcp-config.sh
==========================================
MCP Configuration Validator
==========================================

--- Checking .mcp.json ---
OK: type = 'http' (correct for FastMCP 2.x stateless mode)
OK: url = 'http://127.0.0.1:8080/mcp' (correct /mcp endpoint)

--- Checking mcp-server/pyproject.toml ---
OK: FastMCP pinned to 2.14.2 (known working version)

--- Checking mcp-server/src/scheduler_mcp/server.py ---
OK: stateless_http=True is set (disables session requirement)
OK: lifespan is properly configured

--- Checking docker-compose.yml ---
OK: MCP_TRANSPORT: http (correct)
OK: API_USERNAME and API_PASSWORD references found

--- Checking .env.example ---
OK: API_USERNAME and API_PASSWORD documented in .env.example

==========================================
Validation Summary
==========================================
PASSED: All checks OK
```

---

## Next Steps

1. **Restart Claude Code** to reload MCP config
2. Run `/mcp` to verify connection
3. Address Codex P1 (re-enable alembic migrations)

---

## Historical Context

Sessions 046-048 had various misdiagnoses:
- Session 046: Thought `transport: streamable-http` was needed (WRONG)
- Session 047: Thought `type: sse` was needed (WRONG - deprecated)
- Session 048: Identified `type: http` but didn't implement `stateless_http=True`

The correct combination is:
- **Client config:** `"type": "http"`
- **Server config:** `stateless_http=True`

---

*Session 052B - ORCHESTRATOR Mode*
