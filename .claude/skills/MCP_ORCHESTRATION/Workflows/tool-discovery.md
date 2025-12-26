# Tool Discovery Workflow

Dynamic discovery and classification of available MCP tools.

## Overview

The MCP server exposes tools via FastMCP framework. This workflow enables runtime discovery of:
- Available tools and their signatures
- Input/output schemas
- Tool capabilities and constraints
- Health status and availability

## Discovery Process

### Step 1: Scan MCP Endpoints

```python
from scheduler_mcp.server import mcp

# Get all registered tools
all_tools = mcp.tools

# Count by category
print(f"Total tools: {len(all_tools)}")
```

### Step 2: Parse Tool Metadata

For each tool, extract:

```python
tool_metadata = {
    "name": tool.name,
    "description": tool.description,
    "input_schema": tool.input_schema,  # Pydantic model
    "output_schema": tool.return_annotation,
    "category": categorize_tool(tool.name),
    "async": inspect.iscoroutinefunction(tool.fn),
    "required_params": get_required_params(tool.input_schema),
    "optional_params": get_optional_params(tool.input_schema),
}
```

### Step 3: Build Dynamic Registry

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
    # ... 35 more tools
}
```

### Step 4: Classify Capabilities

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

## Automatic Capability Classification

### Rule-Based Classification

```python
def categorize_tool(tool_name: str) -> str:
    """Automatically categorize tool by name pattern."""

    # Core scheduling
    if any(x in tool_name for x in ["validate", "generate", "conflict", "swap"]):
        return "core_scheduling"

    # Resilience framework
    if any(x in tool_name for x in ["utilization", "contingency", "defense",
                                     "fallback", "sacrifice", "homeostasis",
                                     "blast_radius", "le_chatelier", "hub",
                                     "cognitive", "behavioral", "stigmergy", "mtf"]):
        return "resilience_framework"

    # Background tasks
    if any(x in tool_name for x in ["background_task", "task_status", "cancel_task",
                                     "active_tasks"]):
        return "background_tasks"

    # Deployment
    if any(x in tool_name for x in ["deployment", "security_scan", "smoke_test",
                                     "promote", "rollback"]):
        return "deployment"

    # Empirical testing
    if any(x in tool_name for x in ["benchmark", "ablation", "module_usage"]):
        return "empirical_testing"

    # Resources
    if "resource" in tool_name:
        return "resources"

    return "uncategorized"
```

### Dependency Analysis

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

    # Check if tool requires database
    if tool_name in ["validate_schedule_tool", "detect_conflicts_tool",
                     "analyze_swap_candidates_tool"]:
        dependencies["requires_db"] = True
        dependencies["requires_api"] = True

    # Check if tool requires Celery
    if "background_task" in tool_name or "task_status" in tool_name:
        dependencies["requires_celery"] = True
        dependencies["requires_redis"] = True

    # Identify chainable tools
    if tool_name == "validate_deployment_tool":
        dependencies["can_chain_to"] = [
            "run_security_scan_tool",
            "run_smoke_tests_tool",
            "promote_to_production_tool",
        ]

    return dependencies
```

## Health Checks

### MCP Server Health

```bash
# Check if MCP server is running
docker-compose ps mcp-server

# Check tool count
docker-compose exec mcp-server python -c \
  "from scheduler_mcp.server import mcp; print(f'Registered tools: {len(mcp.tools)}')"
```

Expected output: `Registered tools: 36`

### Backend API Health

```bash
# Test API connectivity from MCP container
docker-compose exec mcp-server curl -s http://backend:8000/health

# Expected response:
# {"status": "healthy", "version": "1.0.0"}
```

### Celery Worker Health

```bash
# Check active workers
docker-compose exec mcp-server python -c \
  "from app.core.celery_app import get_celery_app; \
   app = get_celery_app(); \
   inspect = app.control.inspect(); \
   print(f'Active workers: {inspect.active()}')"
```

## Discovery Examples

### Example 1: Find All Validation Tools

```python
validation_tools = [
    tool for tool in TOOL_REGISTRY.items()
    if "validation" in tool[1].get("subcategory", "")
]

# Returns:
# - validate_schedule_tool
# - validate_schedule_by_id_tool
# - validate_deployment_tool
```

### Example 2: Find Tools That Can Start Background Tasks

```python
async_capable_tools = [
    tool for tool in TOOL_REGISTRY.items()
    if tool[1].get("estimated_duration", "").endswith("minutes")
]

# These tools should use start_background_task_tool:
# - run_contingency_analysis_resilience_tool (2-5 minutes)
# - generate_schedule (variable, potentially >2 minutes)
# - benchmark_solvers_tool (variable)
# - benchmark_constraints_tool (variable)
# - benchmark_resilience_tool (variable)
```

### Example 3: Find Idempotent Tools (Safe to Retry)

```python
idempotent_tools = [
    tool for tool in TOOL_REGISTRY.items()
    if tool[1].get("idempotent", False)
]

# Safe to retry without side effects:
# - All validation tools
# - All analysis tools
# - All read-only resource tools
# - All benchmarking tools
```

### Example 4: Find Tools with Rate Limits

```python
rate_limited_tools = [
    tool for tool in TOOL_REGISTRY.items()
    if tool[1].get("rate_limit") is not None
]

# Currently none, but future consideration:
# - GitHub API calls in deployment tools
# - External API integrations
```

## Tool Signature Extraction

### Extract Input Schema

```python
def get_input_schema(tool_name: str) -> dict:
    """Extract Pydantic schema for tool inputs."""

    tool = mcp.get_tool(tool_name)
    if not tool:
        raise ValueError(f"Tool {tool_name} not found")

    # Get Pydantic model
    input_model = tool.input_schema

    # Extract fields
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

### Extract Output Schema

```python
def get_output_schema(tool_name: str) -> dict:
    """Extract return type annotation."""

    tool = mcp.get_tool(tool_name)
    return_annotation = tool.return_annotation

    # Parse Pydantic model
    if hasattr(return_annotation, "model_fields"):
        return {
            field_name: field_info.annotation
            for field_name, field_info in return_annotation.model_fields.items()
        }

    return {"type": str(return_annotation)}
```

## Dynamic Routing

### Route by Capability

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

### Route by Input Type

```python
def find_tools_accepting_input(input_type: str) -> list[str]:
    """Find tools that accept a specific input type."""

    # Example: Find tools that accept date ranges
    if input_type == "date_range":
        return [
            "validate_schedule_tool",
            "detect_conflicts_tool",
            "run_contingency_analysis_tool",
        ]

    # Example: Find tools that accept schedule_id
    if input_type == "schedule_id":
        return [
            "validate_schedule_by_id_tool",
        ]

    # Example: Find tools that accept task_id
    if input_type == "task_id":
        return [
            "get_task_status_tool",
            "cancel_task_tool",
        ]
```

## Registry Maintenance

### Update on Server Restart

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

### Version Tracking

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

## Best Practices

1. **Cache registry** - Don't re-scan on every request
2. **Lazy load schemas** - Only extract when needed
3. **Health check first** - Verify server is running before discovery
4. **Handle missing tools gracefully** - Provide fallbacks
5. **Log discovery errors** - Aid debugging
6. **Version check** - Ensure MCP server version compatibility

## Related Workflows

- `error-handling.md` - What to do when tools fail
- `tool-composition.md` - How to chain discovered tools
- `../Reference/mcp-tool-index.md` - Static tool catalog
