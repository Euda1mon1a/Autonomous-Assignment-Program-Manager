# MCP Server Documentation

This directory contains documentation for the Residency Scheduler MCP (Model Context Protocol) server.

## Reference Documentation

### Tools
- [MCP Tools Reference](./MCP_TOOLS_REFERENCE.md) - Complete reference for MCP tools:
  - `validate_schedule` - ACGME compliance validation
  - `analyze_contingency` - N-1/N-2 contingency analysis
  - `detect_conflicts` - Conflict detection with auto-resolution
  - `find_swap_matches` - Intelligent swap matching

### Resources
- [MCP Resources Reference](./MCP_RESOURCES_REFERENCE.md) - Read-only data resources:
  - `schedule://status` - Schedule status and coverage metrics
  - `compliance://summary` - ACGME compliance summary

## Implementation Summaries

See the parent directory for implementation summaries:
- [Implementation Summary](../IMPLEMENTATION_SUMMARY.md) - Async task tools
- [Agent Implementation Summary](../AGENT_IMPLEMENTATION_SUMMARY.md) - Agent server
- [Deployment Tools Summary](../DEPLOYMENT_TOOLS_SUMMARY.md) - Deployment helpers
- [Error Handling Summary](../ERROR_HANDLING_SUMMARY.md) - Error handling patterns

## Quick Start

### Installation

```bash
cd mcp-server
pip install -e .
```

### Configuration

Set environment variables:
```bash
export DATABASE_URL="postgresql://user:pass@localhost/residency"
export REDIS_URL="redis://localhost:6379/0"
```

### Running the Server

```bash
python -m scheduler_mcp.server
```

### Claude Desktop Integration

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "residency-scheduler": {
      "command": "python",
      "args": ["-m", "scheduler_mcp.server"],
      "cwd": "/path/to/mcp-server",
      "env": {
        "DATABASE_URL": "postgresql://..."
      }
    }
  }
}
```

## Architecture

```
mcp-server/
├── src/scheduler_mcp/
│   ├── server.py        # FastMCP server entrypoint
│   ├── tools.py         # Tool implementations
│   ├── resources.py     # Resource implementations
│   ├── async_tools.py   # Celery async task tools
│   └── agent_server.py  # Agent-specific server
└── docs/
    ├── README.md              # This file
    ├── MCP_TOOLS_REFERENCE.md # Tools documentation
    └── MCP_RESOURCES_REFERENCE.md # Resources documentation
```
