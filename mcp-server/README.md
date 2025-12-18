***REMOVED*** Residency Scheduler MCP Server

This is a Model Context Protocol (MCP) server for the Autonomous Assignment Program Manager - a medical residency scheduling application that handles ACGME-compliant schedule generation, conflict resolution, and workforce optimization.

***REMOVED******REMOVED*** Purpose

The MCP server exposes key scheduling and analytics capabilities as structured tools and resources, enabling AI assistants to:

- Query schedule status and compliance metrics
- Validate proposed schedules against ACGME regulations
- Run contingency analyses for workforce planning
- Access conflict detection and resolution insights
- Monitor system health and resilience

***REMOVED******REMOVED*** Architecture

This server is built using the [FastMCP](https://github.com/jlowin/fastmcp) framework, which provides:

- Simple decorator-based tool and resource definitions
- Automatic type validation and documentation
- Built-in error handling and logging
- SSE (Server-Sent Events) based transport

***REMOVED******REMOVED*** Available Resources

Resources provide read-only access to scheduling data:

- **schedule_status** - Current schedule state, assignments, and coverage metrics
- **compliance_summary** - ACGME compliance status, violations, and warnings

***REMOVED******REMOVED*** Available Tools

Tools enable active operations and analyses:

- **validate_schedule** - Validate a schedule against ACGME work hour rules
- **run_contingency_analysis** - Analyze impact of faculty absences or emergencies
- **detect_conflicts** - Identify scheduling conflicts and auto-resolution options
- **analyze_swap_candidates** - Find optimal swap matches for schedule changes

***REMOVED******REMOVED*** Installation

```bash
cd mcp-server
pip install -e .
```

***REMOVED******REMOVED*** Configuration

The MCP server connects to the same database as the main application. Set these environment variables:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/residency_scheduler
API_BASE_URL=http://localhost:8000  ***REMOVED*** Optional: for API integration
```

***REMOVED******REMOVED*** Running the Server

***REMOVED******REMOVED******REMOVED*** Standalone Mode
```bash
python -m scheduler_mcp.server
```

***REMOVED******REMOVED******REMOVED*** As MCP Server (for Claude Desktop, etc.)
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

***REMOVED******REMOVED*** Development

***REMOVED******REMOVED******REMOVED*** Project Structure
```
mcp-server/
├── README.md                          ***REMOVED*** This file
├── pyproject.toml                     ***REMOVED*** Python project configuration
└── src/
    └── scheduler_mcp/
        ├── __init__.py                ***REMOVED*** Package initialization
        ├── server.py                  ***REMOVED*** Main MCP server entry point
        ├── resources.py               ***REMOVED*** Resource definitions
        └── tools.py                   ***REMOVED*** Tool definitions
```

***REMOVED******REMOVED******REMOVED*** Adding New Tools

1. Define the tool function in `tools.py`
2. Add appropriate type hints and docstrings
3. Register with `@mcp.tool()` decorator
4. Import and register in `server.py`

***REMOVED******REMOVED******REMOVED*** Adding New Resources

1. Define the resource function in `resources.py`
2. Return appropriate data structures
3. Register with `@mcp.resource()` decorator
4. Import and register in `server.py`

***REMOVED******REMOVED*** Integration with Main Application

This MCP server is designed to complement the main FastAPI application by:

- Providing a conversational interface to scheduling operations
- Enabling batch operations and what-if analyses
- Supporting AI-assisted schedule optimization
- Facilitating natural language queries about compliance and conflicts

***REMOVED******REMOVED*** Security Considerations

- The MCP server should run in a trusted environment
- Database credentials should be securely managed
- Consider implementing authentication for production deployments
- Audit all tool invocations for compliance tracking

***REMOVED******REMOVED*** Future Enhancements

Planned additions include:

- Real-time schedule monitoring via prompts
- Integration with external calendar systems
- Advanced analytics and prediction tools
- Multi-site coordination capabilities
- Natural language schedule query interface

***REMOVED******REMOVED*** References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [ACGME Work Hour Requirements](https://www.acgme.org/what-we-do/accreditation/common-program-requirements/)
