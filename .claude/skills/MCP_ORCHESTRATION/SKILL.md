---
name: MCP_ORCHESTRATION
description: Tool discovery, routing, chaining, error handling, and composition for the 34+ MCP scheduling tools. Use when orchestrating complex multi-tool workflows, handling MCP errors, or discovering available capabilities.
---

# MCP Orchestration Skill

Expert orchestration of Model Context Protocol (MCP) tools for medical residency scheduling. Handles tool discovery, intelligent routing, error recovery, and complex multi-tool composition.

## When This Skill Activates

- Multi-step workflows requiring 2+ MCP tools
- Error recovery from failed MCP calls
- Tool capability discovery needed
- Complex scheduling operations requiring orchestration
- Debugging MCP integration issues
- Performance optimization of tool chains

## Overview

The MCP server exposes 34+ specialized tools across 6 categories:

| Category | Tools | Purpose |
|----------|-------|---------|
| **Core Scheduling** | 5 | Validation, generation, conflict detection, swaps |
| **Resilience Framework** | 13 | Utilization, contingency, defense levels, homeostasis |
| **Background Tasks** | 4 | Celery task management (start, status, cancel, list) |
| **Deployment** | 7 | Validation, security, smoke tests, rollback |
| **Empirical Testing** | 5 | Benchmarking solvers, constraints, modules |
| **Resources** | 2 | Schedule status, compliance summary |

**Total: 36 tools** available for orchestration.

## Key Orchestration Phases

### Phase 1: Discovery
1. Identify available tools matching task requirements
2. Check tool availability and health
3. Verify prerequisites (DB connection, API availability)
4. Map inputs/outputs between dependent tools

### Phase 2: Planning
1. Create execution DAG (directed acyclic graph)
2. Identify parallel vs sequential dependencies
3. Plan error handling checkpoints
4. Estimate execution time and resource usage

### Phase 3: Execution
1. Execute tools in dependency order
2. Handle transient errors with retry logic
3. Propagate results through tool chain
4. Monitor progress and resource utilization

### Phase 4: Recovery
1. Detect permanent vs transient failures
2. Execute fallback strategies
3. Rollback partial state changes if needed
4. Log errors for human escalation

## Orchestration Patterns

### Pattern 1: Sequential Chain
```
Tool A → Tool B → Tool C
```
Each tool depends on previous tool's output.

**Example:** Schedule Generation Pipeline
```
validate_deployment → generate_schedule → validate_schedule → run_smoke_tests
```

### Pattern 2: Parallel Fan-Out
```
       → Tool B
Tool A → Tool C
       → Tool D
```
Multiple tools execute concurrently on same input.

**Example:** Comprehensive Schedule Analysis
```
                → validate_schedule
schedule_status → detect_conflicts
                → check_utilization_threshold
```

### Pattern 3: Map-Reduce
```
Tool A → [Tool B, Tool B, Tool B] → Tool C
```
Parallel execution followed by aggregation.

**Example:** Multi-Person Swap Analysis
```
For each faculty:
    analyze_swap_candidates → aggregate_results → rank_by_score
```

### Pattern 4: Conditional Routing
```
Tool A → Decision → Tool B (if condition)
               → Tool C (else)
```

**Example:** Deployment Workflow
```
validate_deployment → (if valid) → promote_to_production
                   → (else)      → rollback_deployment
```

## Key Files

| File | Purpose |
|------|---------|
| `Workflows/tool-discovery.md` | MCP endpoint scanning and capability mapping |
| `Workflows/error-handling.md` | Retry logic, fallback strategies, escalation |
| `Workflows/tool-composition.md` | DAG patterns, parallel execution, result synthesis |
| `Reference/mcp-tool-index.md` | Complete tool catalog with I/O schemas |
| `Reference/tool-error-patterns.md` | Known failure modes and workarounds |
| `Reference/composition-examples.md` | Real-world multi-tool chains |

## Output

This skill produces:

1. **Execution Plans**: DAG of tool dependencies with timing estimates
2. **Error Reports**: Categorized failures with recovery recommendations
3. **Performance Metrics**: Latency, throughput, resource usage
4. **Capability Maps**: Which tools can satisfy which requirements

## Error Handling Strategy

See `Workflows/error-handling.md` for complete strategy. Key principles:

1. **Retry Transient Errors**: Network timeouts, rate limits, DB locks
2. **Fail Fast on Permanent Errors**: Invalid inputs, missing resources
3. **Graceful Degradation**: Use cached data or reduced functionality
4. **Human Escalation**: Alert on unrecoverable errors

## Integration with MCP Server

The MCP server runs in Docker container `mcp-server` and exposes tools via:

- **STDIO Transport**: For Claude Desktop integration
- **HTTP Transport** (dev mode): Port 8080 for debugging

### Health Check
```bash
docker-compose logs -f mcp-server
docker-compose exec mcp-server python -c \
  "from scheduler_mcp.server import mcp; print(f'Tools: {len(mcp.tools)}')"
```

### API Connectivity Test
```bash
docker-compose exec mcp-server curl -s http://backend:8000/health
```

## Common Workflows

### 1. Schedule Safety Check
**Goal:** Comprehensive validation before deployment
```
Parallel:
  - validate_schedule(date_range)
  - detect_conflicts(date_range)
  - check_utilization_threshold()
  - run_contingency_analysis_resilience(N-1, N-2)

Aggregate results → Generate safety report
```

### 2. Emergency Coverage Response
**Goal:** Handle faculty absence with minimal disruption
```
1. run_contingency_analysis(scenario="faculty_absence", person_ids=[...])
2. For each resolution_option:
     analyze_swap_candidates(requester_id, assignment_id)
3. execute_sacrifice_hierarchy(target_level="yellow", simulate=True)
4. get_static_fallbacks() → Identify pre-computed schedules
```

### 3. Deployment Pipeline
**Goal:** Safe production deployment
```
1. validate_deployment(env="staging", git_ref="main")
2. run_security_scan(git_ref="main")
3. If all passed:
     run_smoke_tests(env="staging", suite="full")
4. If smoke tests passed:
     promote_to_production(staging_version, approval_token)
5. Monitor: get_deployment_status(deployment_id)
```

### 4. Performance Optimization
**Goal:** Identify and remove low-value code
```
Parallel:
  - benchmark_solvers(scenario_count=20)
  - benchmark_constraints(test_schedules="historical")
  - benchmark_resilience(modules=all)
  - module_usage_analysis(entry_points=["main", "api", "scheduling"])

Aggregate → Generate cut list → ablation_study(module_path)
```

## Best Practices

1. **Always check tool prerequisites** before execution
2. **Use background tasks** for long-running operations (>30s)
3. **Poll task status** instead of blocking on Celery tasks
4. **Implement timeouts** for all MCP calls (default: 30s)
5. **Log all tool inputs/outputs** for debugging
6. **Cache tool results** when appropriate (compliance summary, static fallbacks)
7. **Parallelize independent tools** to reduce latency
8. **Handle partial failures gracefully** in fan-out patterns

## Troubleshooting

### MCP Server Not Responding
```bash
# Check container status
docker-compose ps mcp-server

# View logs
docker-compose logs -f mcp-server

# Restart server
docker-compose restart mcp-server
```

### Backend API Unreachable from MCP
```bash
# Test connectivity from MCP container
docker-compose exec mcp-server curl -s http://backend:8000/health

# Check network
docker network inspect autonomous-assignment-program-manager_default
```

### Tool Returns Unexpected Result
1. Check tool signature in `Reference/mcp-tool-index.md`
2. Verify input schema matches expected format
3. Check backend API logs: `docker-compose logs backend`
4. Review error patterns in `Reference/tool-error-patterns.md`

## Related Skills

- **constraint-preflight**: Verify constraints before schedule generation
- **safe-schedule-generation**: Database backup before write operations
- **production-incident-responder**: Crisis response using MCP tools
- **systematic-debugger**: Root cause analysis of tool failures

## Version

- **Created:** 2025-12-26
- **MCP Server Version:** 0.1.0
- **Total Tools:** 36
- **Backend API:** FastAPI 0.109.0

---

*For detailed tool signatures and schemas, see `Reference/mcp-tool-index.md`*
*For error handling procedures, see `Workflows/error-handling.md`*
*For composition patterns, see `Reference/composition-examples.md`*
