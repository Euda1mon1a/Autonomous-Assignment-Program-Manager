***REMOVED*** MCP Server Setup for Claude Code IDE

> **Updated:** 2025-12-29

***REMOVED******REMOVED*** Overview

This document describes the Model Context Protocol (MCP) server integration for the Residency Scheduler application with Claude Code IDE.

***REMOVED******REMOVED*** Quick Start (Docker - Recommended)

```bash
***REMOVED*** 1. Start all services
docker compose up -d

***REMOVED*** 2. Verify MCP server
docker compose exec -T mcp-server python -c \
  "from scheduler_mcp.server import mcp; print('MCP OK')"

***REMOVED*** 3. Claude Code automatically connects via .mcp.json
```

***REMOVED******REMOVED*** Configuration Files

***REMOVED******REMOVED******REMOVED*** 1. `.mcp.json` (Project Root)

Defines the MCP server configuration with Docker-first approach:

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "command": "docker",
      "args": ["compose", "exec", "-T", "mcp-server", "python", "-m", "scheduler_mcp.server"],
      "env": { "LOG_LEVEL": "INFO" },
      "transport": "stdio"
    },
    "residency-scheduler-local": {
      "command": "python",
      "args": ["-m", "scheduler_mcp.server"],
      "cwd": "mcp-server/src",
      "disabled": true
    }
  }
}
```

**Key Points:**
- Primary server uses Docker (no local Python deps needed)
- Local fallback available but disabled by default
- Transport: stdio (standard input/output)

***REMOVED******REMOVED******REMOVED*** Transport Selection

| Transport | Use Case | Concurrency |
|-----------|----------|-------------|
| **STDIO** | Single agent, simple setup | Single client only |
| **HTTP** | Multi-agent workflows, spawned agents | Many clients |

**Important:** STDIO transport supports only one client at a time. If you spawn agents that need MCP access, they will see "Not connected" errors due to pipe contention.

For multi-agent workflows, switch to HTTP transport:

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "url": "http://127.0.0.1:8080/mcp",
      "transport": "http"
    }
  }
}
```

See **[MCP Transport Security Guide](./MCP_TRANSPORT_SECURITY.md)** for secure HTTP configuration.

***REMOVED******REMOVED******REMOVED*** 2. `.claude/settings.json`

Updated to enable the MCP server:
- Added `"enableAllProjectMcpServers": true` to automatically approve all project MCP servers

***REMOVED******REMOVED*** Helper Scripts

***REMOVED******REMOVED******REMOVED*** `scripts/start-mcp.sh`

Starts the MCP server with all required dependencies:
1. Checks if FastAPI backend is running
2. Starts backend with Docker Compose if needed
3. Waits for backend health check
4. Sets required environment variables
5. Launches MCP server in stdio mode

**Usage:**
```bash
./scripts/start-mcp.sh
```

***REMOVED******REMOVED******REMOVED*** `scripts/test-mcp-integration.sh`

Integration test suite for MCP server:
1. Tests MCP module imports
2. Verifies no PII in MCP code
3. Tests domain context expansion
4. Tests constraint explanations

**Usage:**
```bash
./scripts/test-mcp-integration.sh
```

***REMOVED******REMOVED*** How It Works

***REMOVED******REMOVED******REMOVED*** Architecture

```
Claude Code IDE
    ↓ (stdio)
MCP Server (scheduler_mcp.server)
    ↓ (HTTP)
FastAPI Backend (localhost:8000)
    ↓
PostgreSQL Database
```

***REMOVED******REMOVED******REMOVED*** Claude Code Integration

When Claude Code starts in this project:
1. Reads `.mcp.json` to discover available MCP servers
2. Checks `.claude/settings.json` for approval
3. Since `enableAllProjectMcpServers: true`, automatically connects
4. Launches MCP server as subprocess with stdio transport
5. MCP server tools become available in Claude Code context

***REMOVED******REMOVED******REMOVED*** Available MCP Tools

The MCP server exposes tools for:
- **Schedule Management**: Query assignments, blocks, rotations
- **ACGME Compliance**: Check work hours, supervision ratios
- **Swap Management**: Process swap requests, find matches
- **Domain Context**: Expand abbreviations (PGY-1, FMIT, etc.)
- **Constraint Explanations**: Explain scheduling rules
- **Resilience Framework**: N-1/N-2 contingency, defense levels, utilization
- **Deployment Tools**: Security scans, smoke tests, production promotion

See `/home/user/Autonomous-Assignment-Program-Manager/mcp-server/src/scheduler_mcp/server.py` for full tool definitions.

***REMOVED******REMOVED******REMOVED*** MCP Server Module Structure

```
mcp-server/src/scheduler_mcp/
├── __init__.py           ***REMOVED*** Package initialization
├── server.py             ***REMOVED*** Main MCP server with tool registration
├── api_client.py         ***REMOVED*** HTTP client for backend API calls
├── tools.py              ***REMOVED*** Core tool definitions (validation, conflicts)
├── tools/                ***REMOVED*** Specialized tool implementations
│   ├── __init__.py       ***REMOVED*** Tools subpackage exports
│   └── validate_schedule.py  ***REMOVED*** ConstraintService integration
├── resources.py          ***REMOVED*** MCP resources (schedule status, compliance)
├── domain_context.py     ***REMOVED*** Domain abbreviations and glossary
├── resilience_integration.py  ***REMOVED*** Resilience framework tools
├── deployment_tools.py   ***REMOVED*** CI/CD deployment tools
├── async_tools.py        ***REMOVED*** Background task management
└── error_handling.py     ***REMOVED*** Standardized error responses
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Adding New Tools

To add a new tool with backend service integration:

1. **Create module in `tools/`**:
   ```python
   ***REMOVED*** mcp-server/src/scheduler_mcp/tools/my_tool.py
   from pydantic import BaseModel, Field, field_validator

   class MyToolRequest(BaseModel):
       param: str = Field(..., min_length=1)

       @field_validator("param")
       @classmethod
       def validate_param(cls, v: str) -> str:
           ***REMOVED*** Add input validation
           return v.strip()

   async def my_tool(request: MyToolRequest) -> dict:
       ***REMOVED*** Implement with backend service calls
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

***REMOVED******REMOVED*** Prerequisites

***REMOVED******REMOVED******REMOVED*** Option A: Docker (Recommended)

Just have Docker and Docker Compose installed:
```bash
docker compose up -d
```

All dependencies (Python, fastmcp, httpx, etc.) are included in the container.

***REMOVED******REMOVED******REMOVED*** Option B: Local Python (For MCP Development Only)

If you need to modify the MCP server code:
```bash
cd mcp-server
pip install -e .
```

Then enable the local config in `.mcp.json` by swapping `disabled` flags.

***REMOVED******REMOVED******REMOVED*** 3. Claude Code IDE

Must be using Claude Code CLI or IDE with MCP support.

***REMOVED******REMOVED*** Testing the Setup

***REMOVED******REMOVED******REMOVED*** 1. Docker Test (Recommended)
```bash
***REMOVED*** Start services
docker compose up -d

***REMOVED*** Test MCP server
docker compose exec -T mcp-server python -c \
  "from scheduler_mcp.server import mcp; print(f'Tools: {len(mcp._tools)}')"

***REMOVED*** Test backend connectivity
docker compose exec -T mcp-server curl -s http://backend:8000/health
```

***REMOVED******REMOVED******REMOVED*** 2. Full Integration Test
```bash
./scripts/test-mcp-integration.sh
```

***REMOVED******REMOVED******REMOVED*** 3. Claude Code Test

With Docker running, Claude Code automatically connects. Test with:
```
Ask Claude: "Use the MCP tool to check ACGME compliance for PGY-1 residents this week"
```

Claude should have access to 36 MCP tools and be able to query the backend.

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Docker Container Not Running

**Error**: MCP tools not available

**Fix**:
```bash
***REMOVED*** Check status
docker compose ps

***REMOVED*** Start if needed
docker compose up -d

***REMOVED*** Check logs
docker compose logs mcp-server
```

***REMOVED******REMOVED******REMOVED*** MCP Server Won't Start (Local Python)

**Error**: `ModuleNotFoundError: No module named 'fastmcp'`

**Cause**: Running local Python without dependencies installed

**Fix**: Use Docker (recommended) or install deps:
```bash
cd mcp-server && pip install -e .
```

***REMOVED******REMOVED******REMOVED*** Backend Not Healthy

**Error**: `FastAPI backend failed to start`

**Fix**:
```bash
docker compose logs backend
docker compose restart backend
```

***REMOVED******REMOVED******REMOVED*** Claude Code Doesn't See MCP Server

**Check**:
1. Docker is running: `docker compose ps`
2. `.mcp.json` exists in project root
3. MCP server healthy: `docker compose exec -T mcp-server python -c "from scheduler_mcp.server import mcp; print('OK')"`
4. Restart Claude Code if needed

***REMOVED******REMOVED*** Security Notes

***REMOVED******REMOVED******REMOVED*** No PII in MCP Layer

The MCP server is designed to **never expose PII**:
- Person names removed from all responses
- Only role-based IDs (PGY-1, PGY-2, FAC-01, etc.)
- Compliant with OPSEC/PERSEC requirements

***REMOVED******REMOVED******REMOVED*** API Authentication

MCP server connects to localhost FastAPI backend:
- No authentication required for local development
- Production: Should use API keys or mTLS
- All traffic stays on localhost (not exposed)

***REMOVED******REMOVED******REMOVED*** Environment Variables

Sensitive config should use environment variables:
- `API_BASE_URL` - Backend endpoint
- `API_KEY` - If needed for production
- Never commit `.env` files with secrets

***REMOVED******REMOVED*** Next Steps

1. **Add MCP Tools**: Extend `scheduler_mcp/server.py` with new tools
2. **Enhance Domain Context**: Add more abbreviation expansions
3. **Add Caching**: Cache frequently used queries
4. **Add Metrics**: Track MCP tool usage
5. **Production Deploy**: Secure MCP server for production

***REMOVED******REMOVED*** References

- **MCP Specification**: https://modelcontextprotocol.io/
- **Claude Code Docs**: https://docs.anthropic.com/claude-code
- **Project Architecture**: `docs/architecture/`
- **API Documentation**: `docs/api/`

***REMOVED******REMOVED*** Related Documentation

- **[MCP Transport Security Guide](./MCP_TRANSPORT_SECURITY.md)** - Secure HTTP configuration for multi-agent access
- **[Admin MCP Guide](../admin-manual/mcp-admin-guide.md)** - End-user guide for administrators
- **[MCP Architecture Decision](./MCP_ARCHITECTURE_DECISION.md)** - Design rationale
