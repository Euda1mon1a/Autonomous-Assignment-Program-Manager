***REMOVED*** Tool Discovery Workflow

Dynamic discovery and classification of available MCP tools.

***REMOVED******REMOVED*** Overview

The MCP server exposes tools via FastMCP framework. This workflow enables runtime discovery of:
- Available tools and their signatures
- Input/output schemas
- Tool capabilities and constraints
- Health status and availability

***REMOVED******REMOVED*** Discovery Process

***REMOVED******REMOVED******REMOVED*** Step 1: Scan MCP Endpoints

```python
from scheduler_mcp.server import mcp

***REMOVED*** Get all registered tools
all_tools = mcp.tools

***REMOVED*** Count by category
print(f"Total tools: {len(all_tools)}")
```

***REMOVED******REMOVED******REMOVED*** Step 2: Parse Tool Metadata

For each tool, extract:

```python
tool_metadata = {
    "name": tool.name,
    "description": tool.description,
    "input_schema": tool.input_schema,  ***REMOVED*** Pydantic model
    "output_schema": tool.return_annotation,
    "category": categorize_tool(tool.name),
    "async": inspect.iscoroutinefunction(tool.fn),
    "required_params": get_required_params(tool.input_schema),
    "optional_params": get_optional_params(tool.input_schema),
}
```

***REMOVED******REMOVED******REMOVED*** Step 3: Build Dynamic Registry

Maintain in-memory registry of discovered tools:

```python
TOOL_REGISTRY = {
    "validate_schedule_tool": {
        "category": "core_scheduling",
        "subcategory": "validation",
        "requires": ["DATABASE_URL"],
        "produces": "ScheduleValidationResult",
        "estimated_duration": "2-30 seconds",
        "rate_limit": None,
        "idempotent": True,
    },
    ***REMOVED*** ... 35 more tools
}
```

***REMOVED******REMOVED******REMOVED*** Step 4: Classify Capabilities

Group tools by capability:

| Capability | Tools | Use Cases |
|------------|-------|-----------|
| **Data Retrieval** | `schedule_status_resource`, `compliance_summary_resource` | Read-only queries |
| **Validation** | `validate_schedule_tool`, `validate_schedule_by_id_tool` | Pre-flight checks |
| **Analysis** | `detect_conflicts_tool`, `analyze_swap_candidates_tool` | Decision support |
| **Modification** | `generate_schedule` (via API) | Write operations |
| **Background** | `start_background_task_tool`, `get_task_status_tool` | Long-running ops |
| **Resilience** | All 13 resilience tools | System health monitoring |
| **Deployment** | All 7 deployment tools | CI/CD automation |
| **Benchmarking** | All 5 empirical tools | Performance analysis |

***REMOVED******REMOVED*** Automatic Capability Classification

***REMOVED******REMOVED******REMOVED*** Rule-Based Classification

```python
def categorize_tool(tool_name: str) -> str:
    """Automatically categorize tool by name pattern."""

    ***REMOVED*** Core scheduling
    if any(x in tool_name for x in ["validate", "generate", "conflict", "swap"]):
        return "core_scheduling"

    ***REMOVED*** Resilience framework
    if any(x in tool_name for x in ["utilization", "contingency", "defense",
                                     "fallback", "sacrifice", "homeostasis",
                                     "blast_radius", "le_chatelier", "hub",
                                     "cognitive", "behavioral", "stigmergy", "mtf"]):
        return "resilience_framework"

    ***REMOVED*** Background tasks
    if any(x in tool_name for x in ["background_task", "task_status", "cancel_task",
                                     "active_tasks"]):
        return "background_tasks"

    ***REMOVED*** Deployment
    if any(x in tool_name for x in ["deployment", "security_scan", "smoke_test",
                                     "promote", "rollback"]):
        return "deployment"

    ***REMOVED*** Empirical testing
    if any(x in tool_name for x in ["benchmark", "ablation", "module_usage"]):
        return "empirical_testing"

    ***REMOVED*** Resources
    if "resource" in tool_name:
        return "resources"

    return "uncategorized"
```

***REMOVED******REMOVED******REMOVED*** Dependency Analysis

```python
def analyze_dependencies(tool_name: str) -> dict:
    """Identify what this tool depends on."""

    dependencies = {
        "requires_db": False,
        "requires_api": False,
        "requires_celery": False,
        "requires_redis": False,
        "input_from_tools": [],
        "can_chain_to": [],
    }

    ***REMOVED*** Check if tool requires database
    if tool_name in ["validate_schedule_tool", "detect_conflicts_tool",
                     "analyze_swap_candidates_tool"]:
        dependencies["requires_db"] = True
        dependencies["requires_api"] = True

    ***REMOVED*** Check if tool requires Celery
    if "background_task" in tool_name or "task_status" in tool_name:
        dependencies["requires_celery"] = True
        dependencies["requires_redis"] = True

    ***REMOVED*** Identify chainable tools
    if tool_name == "validate_deployment_tool":
        dependencies["can_chain_to"] = [
            "run_security_scan_tool",
            "run_smoke_tests_tool",
            "promote_to_production_tool",
        ]

    return dependencies
```

***REMOVED******REMOVED*** Health Checks

***REMOVED******REMOVED******REMOVED*** MCP Server Health

```bash
***REMOVED*** Check if MCP server is running
docker-compose ps mcp-server

***REMOVED*** Check tool count
docker-compose exec mcp-server python -c \
  "from scheduler_mcp.server import mcp; print(f'Registered tools: {len(mcp.tools)}')"
```

Expected output: `Registered tools: 36`

***REMOVED******REMOVED******REMOVED*** Backend API Health

```bash
***REMOVED*** Test API connectivity from MCP container
docker-compose exec mcp-server curl -s http://backend:8000/health

***REMOVED*** Expected response:
***REMOVED*** {"status": "healthy", "version": "1.0.0"}
```

***REMOVED******REMOVED******REMOVED*** Celery Worker Health

```bash
***REMOVED*** Check active workers
docker-compose exec mcp-server python -c \
  "from app.core.celery_app import get_celery_app; \
   app = get_celery_app(); \
   inspect = app.control.inspect(); \
   print(f'Active workers: {inspect.active()}')"
```

***REMOVED******REMOVED*** Discovery Examples

***REMOVED******REMOVED******REMOVED*** Example 1: Find All Validation Tools

```python
validation_tools = [
    tool for tool in TOOL_REGISTRY.items()
    if "validation" in tool[1].get("subcategory", "")
]

***REMOVED*** Returns:
***REMOVED*** - validate_schedule_tool
***REMOVED*** - validate_schedule_by_id_tool
***REMOVED*** - validate_deployment_tool
```

***REMOVED******REMOVED******REMOVED*** Example 2: Find Tools That Can Start Background Tasks

```python
async_capable_tools = [
    tool for tool in TOOL_REGISTRY.items()
    if tool[1].get("estimated_duration", "").endswith("minutes")
]

***REMOVED*** These tools should use start_background_task_tool:
***REMOVED*** - run_contingency_analysis_resilience_tool (2-5 minutes)
***REMOVED*** - generate_schedule (variable, potentially >2 minutes)
***REMOVED*** - benchmark_solvers_tool (variable)
***REMOVED*** - benchmark_constraints_tool (variable)
***REMOVED*** - benchmark_resilience_tool (variable)
```

***REMOVED******REMOVED******REMOVED*** Example 3: Find Idempotent Tools (Safe to Retry)

```python
idempotent_tools = [
    tool for tool in TOOL_REGISTRY.items()
    if tool[1].get("idempotent", False)
]

***REMOVED*** Safe to retry without side effects:
***REMOVED*** - All validation tools
***REMOVED*** - All analysis tools
***REMOVED*** - All read-only resource tools
***REMOVED*** - All benchmarking tools
```

***REMOVED******REMOVED******REMOVED*** Example 4: Find Tools with Rate Limits

```python
rate_limited_tools = [
    tool for tool in TOOL_REGISTRY.items()
    if tool[1].get("rate_limit") is not None
]

***REMOVED*** Currently none, but future consideration:
***REMOVED*** - GitHub API calls in deployment tools
***REMOVED*** - External API integrations
```

***REMOVED******REMOVED*** Tool Signature Extraction

***REMOVED******REMOVED******REMOVED*** Extract Input Schema

```python
def get_input_schema(tool_name: str) -> dict:
    """Extract Pydantic schema for tool inputs."""

    tool = mcp.get_tool(tool_name)
    if not tool:
        raise ValueError(f"Tool {tool_name} not found")

    ***REMOVED*** Get Pydantic model
    input_model = tool.input_schema

    ***REMOVED*** Extract fields
    return {
        field_name: {
            "type": field_info.annotation,
            "required": field_info.is_required(),
            "default": field_info.default,
            "description": field_info.description,
        }
        for field_name, field_info in input_model.model_fields.items()
    }
```

***REMOVED******REMOVED******REMOVED*** Extract Output Schema

```python
def get_output_schema(tool_name: str) -> dict:
    """Extract return type annotation."""

    tool = mcp.get_tool(tool_name)
    return_annotation = tool.return_annotation

    ***REMOVED*** Parse Pydantic model
    if hasattr(return_annotation, "model_fields"):
        return {
            field_name: field_info.annotation
            for field_name, field_info in return_annotation.model_fields.items()
        }

    return {"type": str(return_annotation)}
```

***REMOVED******REMOVED*** Dynamic Routing

***REMOVED******REMOVED******REMOVED*** Route by Capability

```python
def find_tool_for_capability(capability: str) -> list[str]:
    """Find tools that provide a specific capability."""

    capability_map = {
        "schedule_validation": ["validate_schedule_tool", "validate_schedule_by_id_tool"],
        "conflict_detection": ["detect_conflicts_tool"],
        "swap_matching": ["analyze_swap_candidates_tool"],
        "contingency_planning": ["run_contingency_analysis_tool",
                                 "run_contingency_analysis_resilience_tool"],
        "utilization_monitoring": ["check_utilization_threshold_tool"],
        "deployment_validation": ["validate_deployment_tool"],
        "security_scanning": ["run_security_scan_tool"],
        "performance_testing": ["run_smoke_tests_tool"],
        "solver_comparison": ["benchmark_solvers_tool"],
        "constraint_analysis": ["benchmark_constraints_tool"],
        "code_reduction": ["ablation_study_tool", "module_usage_analysis_tool"],
    }

    return capability_map.get(capability, [])
```

***REMOVED******REMOVED******REMOVED*** Route by Input Type

```python
def find_tools_accepting_input(input_type: str) -> list[str]:
    """Find tools that accept a specific input type."""

    ***REMOVED*** Example: Find tools that accept date ranges
    if input_type == "date_range":
        return [
            "validate_schedule_tool",
            "detect_conflicts_tool",
            "run_contingency_analysis_tool",
        ]

    ***REMOVED*** Example: Find tools that accept schedule_id
    if input_type == "schedule_id":
        return [
            "validate_schedule_by_id_tool",
        ]

    ***REMOVED*** Example: Find tools that accept task_id
    if input_type == "task_id":
        return [
            "get_task_status_tool",
            "cancel_task_tool",
        ]
```

***REMOVED******REMOVED*** Registry Maintenance

***REMOVED******REMOVED******REMOVED*** Update on Server Restart

```python
async def refresh_tool_registry():
    """Refresh tool registry from MCP server."""

    global TOOL_REGISTRY

    from scheduler_mcp.server import mcp

    TOOL_REGISTRY.clear()

    for tool in mcp.tools:
        metadata = extract_tool_metadata(tool)
        dependencies = analyze_dependencies(tool.name)

        TOOL_REGISTRY[tool.name] = {
            **metadata,
            **dependencies,
        }

    logger.info(f"Registry refreshed: {len(TOOL_REGISTRY)} tools")
```

***REMOVED******REMOVED******REMOVED*** Version Tracking

```python
TOOL_REGISTRY_VERSION = {
    "last_updated": "2025-12-26T00:00:00Z",
    "mcp_server_version": "0.1.0",
    "total_tools": 36,
    "categories": {
        "core_scheduling": 5,
        "resilience_framework": 13,
        "background_tasks": 4,
        "deployment": 7,
        "empirical_testing": 5,
        "resources": 2,
    },
}
```

***REMOVED******REMOVED*** Best Practices

1. **Cache registry** - Don't re-scan on every request
2. **Lazy load schemas** - Only extract when needed
3. **Health check first** - Verify server is running before discovery
4. **Handle missing tools gracefully** - Provide fallbacks
5. **Log discovery errors** - Aid debugging
6. **Version check** - Ensure MCP server version compatibility

***REMOVED******REMOVED*** Related Workflows

- `error-handling.md` - What to do when tools fail
- `tool-composition.md` - How to chain discovered tools
- `../Reference/mcp-tool-index.md` - Static tool catalog
