# ADR-003: MCP Server for AI Integration

**Date:** 2025-12 (Session 8)
**Status:** Adopted

## Context

The Residency Scheduler needs to support AI agent interaction for:
- Autonomous schedule operations (via Claude Code, Codex agents)
- Natural language queries about schedules
- Automated compliance checking and reporting
- AI-assisted swap matching and conflict resolution

Direct database access by AI agents poses risks:
- Data integrity violations
- Missing audit trails
- Potential security issues
- Lack of business logic enforcement

## Decision

Build a **FastMCP server** with 34+ scheduling-specific tools:
- Run MCP server in a dedicated Docker container
- AI agents interact via MCP protocol (not direct DB access)
- All operations go through existing service layer
- Audit trails maintained for all AI actions

### Tool Categories

| Category | Tools | Examples |
|----------|-------|----------|
| **Scheduling** | 10+ | `generate_schedule`, `validate_schedule`, `get_coverage_gaps` |
| **People** | 5+ | `list_residents`, `get_person`, `update_availability` |
| **Swaps** | 5+ | `request_swap`, `auto_match_swap`, `execute_swap` |
| **Resilience** | 8+ | `get_burnout_risk`, `check_n1_contingency`, `get_resilience_score` |
| **ACGME** | 4+ | `validate_acgme`, `check_80_hour_rule`, `check_supervision` |
| **Analytics** | 4+ | `get_workload_balance`, `get_coverage_forecast` |

## Consequences

### Positive
- **Safe AI interaction**: No direct database manipulation
- **Audit trails**: All AI actions are logged with attribution
- **Composable tools**: Agents can orchestrate complex workflows
- **Business logic enforcement**: AI actions respect constraints
- **Consistent interface**: Same validation for human and AI actions

### Negative
- **Additional infrastructure**: MCP server must be deployed alongside app
- **Latency**: Extra network hop for AI operations
- **Development overhead**: Tools must be maintained alongside API
- **Versioning complexity**: MCP tools and API must stay in sync

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AI Agent      │     │   MCP Server    │     │   Backend API   │
│ (Claude/Codex)  │────▶│  (FastMCP)      │────▶│   (FastAPI)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │     MCP Protocol      │     HTTP REST         │
        │    (tool calls)       │   (internal calls)    │
        ▼                       ▼                       ▼
   Natural Language       Tool Execution          Business Logic
   Understanding          + Audit Trail           + Data Access
```

## Implementation

### MCP Server Configuration
```yaml
# docker-compose.yml
mcp-server:
  build: ./mcp-server
  environment:
    - BACKEND_URL=http://backend:8000
    - LOG_LEVEL=INFO
  depends_on:
    - backend
  ports:
    - "8080:8080"  # Dev mode HTTP transport
```

### Tool Registration
```python
# mcp-server/scheduler_mcp/tools/scheduling.py
from fastmcp import tool

@tool
async def generate_schedule(
    start_date: str,
    end_date: str,
    include_preferences: bool = True
) -> dict:
    """Generate a schedule for the specified date range.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        include_preferences: Whether to include resident preferences

    Returns:
        Generated schedule with assignments
    """
    async with get_api_client() as client:
        return await client.post("/api/schedule/generate", json={
            "start_date": start_date,
            "end_date": end_date,
            "include_preferences": include_preferences
        })
```

## References

- [FastMCP Documentation](https://github.com/anthropics/fastmcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- `mcp-server/` - MCP server implementation
- `docs/api/MCP_TOOLS_REFERENCE.md` - Complete tool reference
- `docs/architecture/MCP_ORCHESTRATION_PATTERNS.md` - Orchestration patterns

## See Also

**Related ADRs:**
- [ADR-001: FastAPI + SQLAlchemy](ADR-001-fastapi-sqlalchemy-async.md) - Backend API that MCP server calls
- [ADR-011: CI_LIAISON Container Management](ADR-011-ci-liaison-container-management.md) - Container orchestration for MCP server
- [ADR-007: Monorepo with Docker Compose](../../.claude/dontreadme/synthesis/DECISIONS.md#adr-007-monorepo-with-docker-compose) - MCP server in Docker

**Implementation Code:**
- `mcp-server/scheduler_mcp/server.py` - FastMCP server entry point
- `mcp-server/scheduler_mcp/tools/` - Tool implementations
- `mcp-server/scheduler_mcp/api_client.py` - Backend API integration
- `docker-compose.yml` - MCP server container configuration

**Architecture Documentation:**
- [MCP Orchestration Patterns](../MCP_ORCHESTRATION_PATTERNS.md) - Multi-tool workflows
- [Tool Composition Patterns](../TOOL_COMPOSITION_PATTERNS.md) - Composing MCP tools

**API Documentation:**
- [MCP Tools Reference](../../api/MCP_TOOLS_REFERENCE.md) - All 34+ MCP tools
- [MCP Tool Guide](../../api/MCP_TOOL_GUIDE.md) - Usage guide

**Skills:**
- `.claude/skills/MCP_ORCHESTRATION/` - AI agent orchestration skill
