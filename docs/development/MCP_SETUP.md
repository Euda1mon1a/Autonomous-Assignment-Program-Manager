# MCP Server Setup for Claude Code IDE

## Overview

This document describes the Model Context Protocol (MCP) server integration for the Residency Scheduler application with Claude Code IDE.

## Configuration Files

### 1. `.mcp.json` (Project Root)

Defines the MCP server configuration:
- **Server Name**: `residency-scheduler`
- **Command**: `python -m scheduler_mcp.server`
- **Working Directory**: `mcp-server/src`
- **Environment Variables**:
  - `API_BASE_URL`: http://localhost:8000 (FastAPI backend)
  - `PYTHONPATH`: mcp-server/src
  - `LOG_LEVEL`: INFO
- **Transport**: stdio (standard input/output)

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
5. Launches MCP server in stdio mode

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
    ↓ (stdio)
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
4. Launches MCP server as subprocess with stdio transport
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

### 1. FastAPI Backend Running

MCP server requires the FastAPI backend to be healthy:
```bash
docker-compose up -d backend
curl http://localhost:8000/health
```

### 2. Python Dependencies

MCP server dependencies must be installed:
```bash
cd mcp-server
pip install -r requirements.txt
```

### 3. Claude Code IDE

Must be using Claude Code CLI or IDE with MCP support.

## Testing the Setup

### 1. Basic Import Test
```bash
cd mcp-server/src
python -c "from scheduler_mcp.server import mcp; print('OK')"
```

### 2. Full Integration Test
```bash
./scripts/test-mcp-integration.sh
```

### 3. Manual MCP Server Start
```bash
# Terminal 1: Start backend
docker-compose up backend

# Terminal 2: Start MCP server
./scripts/start-mcp.sh
```

### 4. Claude Code Test

In Claude Code IDE:
```
Ask Claude: "Use the MCP tool to check ACGME compliance for PGY-1 residents this week"
```

Claude should have access to MCP tools and be able to query the backend.

## Troubleshooting

### MCP Server Won't Start

**Error**: `ModuleNotFoundError: No module named 'scheduler_mcp'`

**Fix**:
```bash
export PYTHONPATH=/home/user/Autonomous-Assignment-Program-Manager/mcp-server/src
cd mcp-server/src
python -m scheduler_mcp.server
```

### Backend Not Healthy

**Error**: `FastAPI backend failed to start`

**Fix**:
```bash
docker-compose logs backend
docker-compose restart backend
```

### Permission Denied on Scripts

**Error**: `Permission denied: ./scripts/start-mcp.sh`

**Fix**:
```bash
chmod +x scripts/start-mcp.sh scripts/test-mcp-integration.sh
```

### Claude Code Doesn't See MCP Server

**Check**:
1. `.mcp.json` exists in project root
2. `.claude/settings.json` has `"enableAllProjectMcpServers": true`
3. Restart Claude Code IDE
4. Check Claude Code logs for MCP server connection

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
- **Project Architecture**: `/home/user/Autonomous-Assignment-Program-Manager/docs/architecture/`
- **API Documentation**: `/home/user/Autonomous-Assignment-Program-Manager/docs/api/`
