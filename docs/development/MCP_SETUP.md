# MCP Server Setup for Claude Code IDE

> **Updated:** 2026-02-26

## Overview

This document describes the Model Context Protocol (MCP) server integration for the Residency Scheduler application with Claude Code IDE.

## Quick Start (Native macOS — Recommended)

```bash
# 1. Start the MCP server natively (no Docker needed)
cd mcp-server && uvicorn scheduler_mcp.server:app --port 8080

# 2. Register with Claude Code (one-time)
claude mcp add --transport http --scope local residency-scheduler http://127.0.0.1:8080/mcp

# 3. Verify connection
# Use /mcp in Claude Code to check status
```

> **Note:** Docker is still supported but native macOS is the primary development setup as of Feb 2026. All core services (PostgreSQL, Redis, MCP server) run natively on Apple Silicon.

## Quick Start (Docker — Alternative)

```bash
# 1. Start all services
docker compose up -d

# 2. Verify MCP server
docker compose exec -T mcp-server python -c \
  "from scheduler_mcp.server import mcp; print('MCP OK')"

# 3. Claude Code automatically connects via .mcp.json
```

## Configuration Files

### 1. `.mcp.json` (Project Root)

Defines the MCP server configuration with HTTP transport:

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

**Key Points:**
- MCP server runs as Docker container with HTTP transport
- Supports multi-agent workflows and spawned agents
- Port bound to localhost only for security

See **[MCP Transport Security Guide](./MCP_TRANSPORT_SECURITY.md)** for secure HTTP configuration.

### 2. `.claude/settings.json`

Updated to enable the MCP server:
- Added `"enableAllProjectMcpServers": true` to automatically approve all project MCP servers

## Helper Scripts

### `scripts/start-mcp.sh`

Starts the MCP server with all required dependencies:
1. Checks if FastAPI backend is running
2. Starts backend with Docker Compose if needed
3. Waits for backend health check
4. Sets required environment variables
5. Launches MCP server with HTTP transport

**Usage:**
```bash
./scripts/start-mcp.sh
```

### `scripts/test-mcp-integration.sh`

Integration test suite for MCP server:
1. Tests MCP module imports
2. Verifies no PII in MCP code
3. Tests domain context expansion
4. Tests constraint explanations

**Usage:**
```bash
./scripts/test-mcp-integration.sh
```

## How It Works

### Architecture

```
Claude Code IDE
    ↓ (HTTP)
MCP Server (scheduler_mcp.server)
    ↓ (HTTP)
FastAPI Backend (localhost:8000)
    ↓
PostgreSQL Database
```

### Claude Code Integration

When Claude Code starts in this project:
1. Reads `.mcp.json` to discover available MCP servers
2. Checks `.claude/settings.json` for approval
3. Since `enableAllProjectMcpServers: true`, automatically connects
4. Connects to MCP server via HTTP transport
5. MCP server tools become available in Claude Code context

### Available MCP Tools

The MCP server exposes tools for:
- **Schedule Management**: Query assignments, blocks, rotations
- **ACGME Compliance**: Check work hours, supervision ratios
- **Swap Management**: Process swap requests, find matches
- **Domain Context**: Expand abbreviations (PGY-1, FMIT, etc.)
- **Constraint Explanations**: Explain scheduling rules
- **Resilience Framework**: N-1/N-2 contingency, defense levels, utilization
- **Deployment Tools**: Security scans, smoke tests, production promotion

See `/home/user/Autonomous-Assignment-Program-Manager/mcp-server/src/scheduler_mcp/server.py` for full tool definitions.

### MCP Server Module Structure

```
mcp-server/src/scheduler_mcp/
├── __init__.py           # Package initialization
├── server.py             # Main MCP server with tool registration
├── api_client.py         # HTTP client for backend API calls
├── tools.py              # Core tool definitions (validation, conflicts)
├── tools/                # Specialized tool implementations
│   ├── __init__.py       # Tools subpackage exports
│   └── validate_schedule.py  # ConstraintService integration
├── resources.py          # MCP resources (schedule status, compliance)
├── domain_context.py     # Domain abbreviations and glossary
├── resilience_integration.py  # Resilience framework tools
├── deployment_tools.py   # CI/CD deployment tools
├── async_tools.py        # Background task management
└── error_handling.py     # Standardized error responses
```

#### Adding New Tools

To add a new tool with backend service integration:

1. **Create module in `tools/`**:
   ```python
   # mcp-server/src/scheduler_mcp/tools/my_tool.py
   from pydantic import BaseModel, Field, field_validator

   class MyToolRequest(BaseModel):
       param: str = Field(..., min_length=1)

       @field_validator("param")
       @classmethod
       def validate_param(cls, v: str) -> str:
           # Add input validation
           return v.strip()

   async def my_tool(request: MyToolRequest) -> dict:
       # Implement with backend service calls
       pass
   ```

2. **Export in `tools/__init__.py`**:
   ```python
   from .my_tool import MyToolRequest, my_tool
   ```

3. **Import in `server.py`**:
   ```python
   from .tools.my_tool import MyToolRequest, my_tool
   ```

4. **Register with `@mcp.tool()`** decorator in `server.py`

## Prerequisites

### Option A: Docker (Recommended)

Just have Docker and Docker Compose installed:
```bash
docker compose up -d
```

All dependencies (Python, fastmcp, httpx, etc.) are included in the container.

### Option B: Local Python (For MCP Development Only)

If you need to modify the MCP server code:
```bash
cd mcp-server
pip install -e .
```

Then enable the local config in `.mcp.json` by swapping `disabled` flags.

### 3. Claude Code IDE

Must be using Claude Code CLI or IDE with MCP support.

## Testing the Setup

### 1. Docker Test (Recommended)
```bash
# Start services
docker compose up -d

# Test MCP server
docker compose exec -T mcp-server python -c \
  "from scheduler_mcp.server import mcp; print(f'Tools: {len(mcp._tools)}')"

# Test backend connectivity
docker compose exec -T mcp-server curl -s http://backend:8000/health
```

### 2. Full Integration Test
```bash
./scripts/test-mcp-integration.sh
```

### 3. Claude Code Test

With Docker running, Claude Code automatically connects. Test with:
```
Ask Claude: "Use the MCP tool to check ACGME compliance for PGY-1 residents this week"
```

Claude should have access to 36 MCP tools and be able to query the backend.

## Troubleshooting

### Docker Container Not Running

**Error**: MCP tools not available

**Fix**:
```bash
# Check status
docker compose ps

# Start if needed
docker compose up -d

# Check logs
docker compose logs mcp-server
```

### MCP Server Won't Start (Local Python)

**Error**: `ModuleNotFoundError: No module named 'fastmcp'`

**Cause**: Running local Python without dependencies installed

**Fix**: Use Docker (recommended) or install deps:
```bash
cd mcp-server && pip install -e .
```

### Backend Not Healthy

**Error**: `FastAPI backend failed to start`

**Fix**:
```bash
docker compose logs backend
docker compose restart backend
```

### Claude Code Doesn't See MCP Server

**Check**:
1. MCP server healthy: `curl -sf http://127.0.0.1:8080/health`
2. Verify config is in the right location (see below)
3. Run `/mcp` in Claude Code to reconnect
4. If `/mcp` fails, fully quit and relaunch Claude Code from a new terminal

**Critical: Client Config Location**

Claude Code reads MCP config from multiple locations with this precedence:

| Priority | Location | Written by |
|----------|----------|------------|
| 1 | `~/.claude.json` → `projects["/path/to/repo"].mcpServers` | `claude mcp add --scope local` |
| 2 | `.mcp.json` (repo root) | Manual edit |
| 3 | `~/.claude/config.json` → `mcpServers` | Manual edit |

**The canonical way to register the MCP server:**

```bash
claude mcp add --transport http --scope local residency-scheduler http://127.0.0.1:8080/mcp
```

Manual edits to `~/.claude/config.json` or `.mcp.json` may not be picked up reliably. The CLI command writes to `~/.claude.json` under the project key, which has the highest priority.

**Transport types:**
- `--transport http` — Streamable HTTP (required, server only exposes this)
- `--transport sse` — SSE (deprecated, server does NOT expose this endpoint)
- `--transport stdio` — DO NOT USE (limits parallel tool calls to one at a time)

## Security Notes

### No PII in MCP Layer

The MCP server is designed to **never expose PII**:
- Person names removed from all responses
- Only role-based IDs (PGY-1, PGY-2, FAC-01, etc.)
- Compliant with OPSEC/PERSEC requirements

### API Authentication

MCP server connects to localhost FastAPI backend:
- No authentication required for local development
- Production: Should use API keys or mTLS
- All traffic stays on localhost (not exposed)

### Environment Variables

Sensitive config should use environment variables:
- `API_BASE_URL` - Backend endpoint
- `API_KEY` - If needed for production
- Never commit `.env` files with secrets

## Next Steps

1. **Add MCP Tools**: Extend `scheduler_mcp/server.py` with new tools
2. **Enhance Domain Context**: Add more abbreviation expansions
3. **Add Caching**: Cache frequently used queries
4. **Add Metrics**: Track MCP tool usage
5. **Production Deploy**: Secure MCP server for production

## References

- **MCP Specification**: https://modelcontextprotocol.io/
- **Claude Code Docs**: https://docs.anthropic.com/claude-code
- **Project Architecture**: `docs/architecture/`
- **API Documentation**: `docs/api/`

## Related Documentation

- **[MCP Transport Security Guide](./MCP_TRANSPORT_SECURITY.md)** - Secure HTTP configuration for multi-agent access
- **[Admin MCP Guide](../admin-manual/mcp-admin-guide.md)** - End-user guide for administrators
- **[MCP Architecture Decision](./MCP_ARCHITECTURE_DECISION.md)** - Design rationale
