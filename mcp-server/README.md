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

The MCP server exposes **97+ tools** organized into functional categories.

### Core Scheduling Tools

- **validate_schedule** - Validate a schedule against ACGME work hour rules
- **run_contingency_analysis** - Analyze impact of faculty absences or emergencies
- **detect_conflicts** - Identify scheduling conflicts and auto-resolution options
- **analyze_swap_candidates** - Find optimal swap matches for schedule changes

### Resilience Framework Tools (77 tools)

See [RESILIENCE_MCP_INTEGRATION.md](./RESILIENCE_MCP_INTEGRATION.md) for full documentation.

**Tier 1-2 Core Resilience**:
- `check_utilization_threshold` - 80% queuing theory threshold
- `get_defense_level` - Defense-in-depth status (5 levels)
- `run_contingency_analysis_resilience` - N-1/N-2 power grid analysis
- `analyze_homeostasis` - Feedback loop monitoring
- `calculate_blast_radius` - Zone-based failure containment

**Cross-Disciplinary Analytics (Tier 3)**:
- `run_spc_analysis` - Western Electric Rules for workload drift
- `calculate_process_capability` - Six Sigma Cp/Cpk indices
- `calculate_burnout_rt` - SIR epidemiology reproduction number
- `optimize_erlang_coverage` - Telecommunications queuing optimization
- `detect_burnout_precursors` - Seismic STA/LTA early warning
- `calculate_fire_danger_index` - Multi-temporal burnout (CFFDRS)
- `assess_creep_fatigue` - Materials science Larson-Miller analysis

### Exotic Research Tools (20 tools) - NEW

See [docs/EXOTIC_RESEARCH_TOOLS.md](./docs/EXOTIC_RESEARCH_TOOLS.md) for full documentation.

**Kalman Filter (Control Theory)**:
- `analyze_workload_trend` - Filter noisy workload, extract trends
- `detect_workload_anomalies` - Identify outliers via residual analysis

**Fourier/FFT (Signal Processing)**:
- `detect_schedule_cycles` - FFT periodicity detection (7d, 28d cycles)
- `analyze_harmonic_resonance` - ACGME window alignment scoring
- `calculate_spectral_entropy` - Schedule complexity measurement

**Game Theory (Economics)**:
- `analyze_nash_stability` - Detect stable schedule equilibria
- `find_deviation_incentives` - Predict swap requests before they happen
- `detect_coordination_failures` - Find blocked Pareto improvements

**Value-at-Risk (Financial Engineering)**:
- `calculate_coverage_var` - Probabilistic coverage bounds
- `calculate_workload_var` - Workload distribution risk
- `simulate_disruption_scenarios` - Monte Carlo stress testing
- `calculate_conditional_var` - Tail risk (Expected Shortfall)

**Lotka-Volterra (Ecology)**:
- `analyze_supply_demand_cycles` - Fit predator-prey model
- `predict_capacity_crunch` - Forecast coverage crises
- `find_equilibrium_point` - Calculate stable staffing targets
- `simulate_intervention` - Test what-if capacity changes

**Hopfield Attractor (Neuroscience)**:
- `calculate_hopfield_energy` - Schedule state energy
- `find_nearby_attractors` - Identify stable patterns
- `measure_basin_depth` - Robustness to perturbations
- `detect_spurious_attractors` - Find scheduling anti-patterns

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

### Docker Container (Recommended)

The MCP server runs as a Docker container following Docker MCP Toolkit patterns:

```bash
# Start all services including MCP server
docker-compose up -d

# Development mode (hot reload, HTTP transport on port 8080)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View MCP server logs
docker-compose logs -f mcp-server

# Test MCP server health
docker-compose exec mcp-server python -c \
  "from scheduler_mcp.server import mcp; print(f'Tools: {len(mcp.tools)}')"
```

**Container Security Features:**
- Resource limits: 1 CPU, 2GB RAM
- Privilege dropping: `no-new-privileges:true`
- Network isolation: Internal `app-network` only
- No host filesystem access (production)

### Standalone Mode (Development)

```bash
cd mcp-server
pip install -e .
python -m scheduler_mcp.server
```

### Claude Code Integration

The project includes pre-configured `.mcp.json` for Claude Code CLI.

**Default: Docker exec (stdio transport)**
```json
{
  "mcpServers": {
    "residency-scheduler": {
      "command": "docker",
      "args": ["compose", "exec", "-T", "mcp-server",
               "python", "-m", "scheduler_mcp.server"],
      "transport": "stdio"
    }
  }
}
```

**Alternative: Local Python (disabled by default)**
```json
{
  "mcpServers": {
    "residency-scheduler-local": {
      "command": "python",
      "args": ["-m", "scheduler_mcp.server"],
      "cwd": "mcp-server/src",
      "disabled": true
    }
  }
}
```

**Claude Code Resources:**
- `.claude/SESSION_STARTUP_TODOS.md` - Startup checklist
- `.claude/MCP_USAGE_TODOS.md` - MCP tool usage patterns

### Remote Deployment (Render, Railway, Fly.io)

Deploy the MCP server to a cloud platform for remote AI agent access:

#### Render Deployment

1. **Blueprint Deployment** (Recommended)

   The `render.yaml` in the project root includes the MCP server configuration.
   Connect your repo to Render and the MCP service will be created automatically.

2. **Manual Configuration**

   | Setting | Value |
   |---------|-------|
   | **Type** | Web Service |
   | **Dockerfile** | `./mcp-server/Dockerfile` |
   | **Port** | 8080 |
   | **Health Check** | `/health` |

3. **Environment Variables**

   Set these in the Render dashboard:

   ```bash
   # MCP Transport (required)
   MCP_TRANSPORT=http
   MCP_HOST=0.0.0.0
   MCP_PORT=8080

   # Authentication (required for production)
   # Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'
   MCP_API_KEY=<your-generated-secret>

   # Backend API connection
   API_BASE_URL=https://residency-scheduler-backend.onrender.com
   API_USERNAME=<your-api-user>
   API_PASSWORD=<your-api-password>
   ```

4. **Connect Claude Code to Remote MCP**

   Add to `~/.config/claude-code/settings.json`:

   ```json
   {
     "mcpServers": {
       "residency-scheduler-remote": {
         "type": "http",
         "url": "https://residency-scheduler-mcp.onrender.com/mcp",
         "headers": {
           "Authorization": "Bearer <your-mcp-api-key>"
         }
       }
     }
   }
   ```

5. **Verify Connection**

   ```bash
   # Health check (no auth required)
   curl https://residency-scheduler-mcp.onrender.com/health

   # MCP endpoint (requires auth)
   curl -H "Authorization: Bearer <your-key>" \
        https://residency-scheduler-mcp.onrender.com/mcp
   ```

#### Security Notes

- **Always set MCP_API_KEY** in production to prevent unauthorized access
- Health endpoint (`/health`) is unauthenticated for load balancer compatibility
- All MCP tool calls require valid API key
- Use HTTPS endpoints only

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

The MCP server follows Docker MCP Toolkit security patterns:

**Container-Level Security:**
- Resource limits prevent runaway processes (1 CPU, 2GB RAM)
- `no-new-privileges:true` prevents privilege escalation
- Network isolation restricts access to internal services only
- No host filesystem mounts in production
- Non-root user (`mcp:mcp`) inside container

**Application-Level Security:**
- Connects to FastAPI backend (not direct database) for PII protection
- Database credentials never exposed to MCP server
- All sensitive data sanitized through API layer
- Audit all tool invocations for compliance tracking

**Credential Management:**
- Secrets injected via environment variables at runtime
- No secrets stored in Docker image
- Redis password required for Celery integration

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
