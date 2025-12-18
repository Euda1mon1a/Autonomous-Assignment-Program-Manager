# Residency Scheduler MCP Server

This is a Model Context Protocol (MCP) server for the Autonomous Assignment Program Manager - a medical residency scheduling application that handles ACGME-compliant schedule generation, conflict resolution, and workforce optimization.

## Purpose

The MCP server exposes key scheduling and analytics capabilities as structured tools and resources, enabling AI assistants to:

- Query schedule status and compliance metrics
- Validate proposed schedules against ACGME regulations
- Run contingency analyses for workforce planning
- Access conflict detection and resolution insights
- Monitor system health and resilience

## Architecture

This server is built using the [FastMCP](https://github.com/jlowin/fastmcp) framework, which provides:

- Simple decorator-based tool and resource definitions
- Automatic type validation and documentation
- Built-in error handling and logging
- SSE (Server-Sent Events) based transport

## Available Resources

Resources provide read-only access to scheduling data:

- **schedule_status** - Current schedule state, assignments, and coverage metrics
- **compliance_summary** - ACGME compliance status, violations, and warnings

## Available Tools

### Synchronous Tools

Tools enable active operations and analyses:

- **validate_schedule** - Validate a schedule against ACGME work hour rules
- **run_contingency_analysis** - Analyze impact of faculty absences or emergencies
- **detect_conflicts** - Identify scheduling conflicts and auto-resolution options
- **analyze_swap_candidates** - Find optimal swap matches for schedule changes

### Async Task Management Tools

Background task tools for long-running operations using Celery:

- **start_background_task** - Start a background task (resilience analysis, metrics computation, etc.)
- **get_task_status** - Poll task status and retrieve results
- **cancel_task** - Cancel a running or queued task
- **list_active_tasks** - List all currently active tasks

**Supported Task Types:**
- Resilience tasks: health check, contingency analysis, fallback precomputation, utilization forecast
- Metrics tasks: schedule metrics computation, snapshots, cleanup, fairness reports

See [ASYNC_TOOLS.md](./ASYNC_TOOLS.md) for comprehensive documentation and examples.

## Installation

```bash
cd mcp-server
pip install -e .
```

## Configuration

The MCP server connects to the same database as the main application. Set these environment variables:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/residency_scheduler
API_BASE_URL=http://localhost:8000  # Optional: for API integration
```

### For Async Task Management

To use async task tools, you also need:

1. **Redis** - Celery message broker
   ```bash
   docker-compose up -d redis
   ```

2. **Celery Worker** - Background task processor
   ```bash
   cd backend
   ../scripts/start-celery.sh worker
   ```

3. **PYTHONPATH** - Include backend directory
   ```bash
   export PYTHONPATH=/path/to/backend:$PYTHONPATH
   ```

## Running the Server

### Standalone Mode
```bash
python -m scheduler_mcp.server
```

### As MCP Server (for Claude Desktop, etc.)
Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "command": "python",
      "args": ["-m", "scheduler_mcp.server"],
      "cwd": "/path/to/mcp-server"
    }
  }
}
```

## Development

### Project Structure
```
mcp-server/
├── README.md                          # This file
├── ASYNC_TOOLS.md                     # Async task tools documentation
├── pyproject.toml                     # Python project configuration
├── examples/
│   └── async_task_example.py          # Example usage of async tools
├── tests/
│   └── test_async_tools.py            # Unit tests for async tools
└── src/
    └── scheduler_mcp/
        ├── __init__.py                # Package initialization
        ├── server.py                  # Main MCP server entry point
        ├── resources.py               # Resource definitions
        ├── tools.py                   # Tool definitions
        └── async_tools.py             # Async task management tools
```

### Adding New Tools

1. Define the tool function in `tools.py`
2. Add appropriate type hints and docstrings
3. Register with `@mcp.tool()` decorator
4. Import and register in `server.py`

### Adding New Resources

1. Define the resource function in `resources.py`
2. Return appropriate data structures
3. Register with `@mcp.resource()` decorator
4. Import and register in `server.py`

## Integration with Main Application

This MCP server is designed to complement the main FastAPI application by:

- Providing a conversational interface to scheduling operations
- Enabling batch operations and what-if analyses
- Supporting AI-assisted schedule optimization
- Facilitating natural language queries about compliance and conflicts

## Security Considerations

- The MCP server should run in a trusted environment
- Database credentials should be securely managed
- Consider implementing authentication for production deployments
- Audit all tool invocations for compliance tracking

## Future Enhancements

Planned additions include:

- Real-time schedule monitoring via prompts
- Integration with external calendar systems
- Advanced analytics and prediction tools
- Multi-site coordination capabilities
- Natural language schedule query interface

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [ACGME Work Hour Requirements](https://www.acgme.org/what-we-do/accreditation/common-program-requirements/)
