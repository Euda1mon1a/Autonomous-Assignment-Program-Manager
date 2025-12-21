***REMOVED*** Workflow Orchestration Engine

This package provides a comprehensive workflow execution engine for the Residency Scheduler application.

***REMOVED******REMOVED*** Features

- **Template-based Workflow Definitions**: Define reusable workflow templates with versioning
- **Sequential and Parallel Execution**: Execute steps one-by-one or concurrently
- **Conditional Branching**: Skip steps based on runtime conditions
- **Error Handling with Retry Logic**: Automatic retry with exponential backoff
- **State Persistence**: Resume workflows after failures or restarts
- **Timeout Handling**: Configure timeouts at workflow and step levels
- **Workflow Cancellation**: Cancel running workflows gracefully
- **Template Versioning**: Evolve workflows while maintaining backward compatibility

***REMOVED******REMOVED*** Architecture

***REMOVED******REMOVED******REMOVED*** Components

1. **Models** (`app/models/workflow.py`):
   - `WorkflowTemplate`: Versioned workflow definitions
   - `WorkflowInstance`: Runtime workflow executions
   - `WorkflowStepExecution`: Individual step execution records

2. **Engine** (`app/workflow/engine.py`):
   - `WorkflowEngine`: Core orchestration logic
   - Step execution with retry and timeout handling
   - Dependency resolution and execution planning

3. **Service** (`app/services/workflow_service.py`):
   - High-level workflow management API
   - Common workflow templates
   - Monitoring and statistics

4. **Schemas** (`app/schemas/workflow.py`):
   - Pydantic schemas for API validation
   - Request/response models

***REMOVED******REMOVED*** Usage

***REMOVED******REMOVED******REMOVED*** Creating a Workflow Template

```python
from app.workflow.engine import WorkflowEngine

engine = WorkflowEngine(db)

template = engine.create_template(
    name="schedule_generation",
    definition={
        "steps": [
            {
                "id": "validate",
                "name": "Validate Input",
                "handler": "app.services.handlers.validate_input",
                "execution_mode": "sequential",
                "depends_on": [],
                "retry_policy": {
                    "max_attempts": 3,
                    "backoff_multiplier": 2,
                    "max_backoff_seconds": 300
                },
                "timeout_seconds": 60,
            },
            {
                "id": "generate",
                "name": "Generate Schedule",
                "handler": "app.services.handlers.generate_schedule",
                "execution_mode": "sequential",
                "depends_on": ["validate"],
                "timeout_seconds": 600,
            },
        ],
        "error_handlers": {},
        "default_timeout_seconds": 3600,
    },
    description="Automated schedule generation workflow",
    tags=["schedule", "automated"],
)
```

***REMOVED******REMOVED******REMOVED*** Executing a Workflow

```python
***REMOVED*** Create workflow instance
instance = engine.create_instance(
    template_id=template.id,
    input_data={"start_date": "2024-01-01", "end_date": "2024-12-31"},
    priority=5,
)

***REMOVED*** Execute asynchronously
await engine.execute_workflow(
    instance_id=instance.id,
    async_execution=True,
)

***REMOVED*** Check status
instance = engine.get_instance(instance.id)
print(f"Status: {instance.status}")
```

***REMOVED******REMOVED******REMOVED*** Using the Service Layer

```python
from app.services.workflow_service import WorkflowService

service = WorkflowService(db)

***REMOVED*** Start a workflow by template name
instance = service.start_workflow(
    template_name="schedule_generation",
    input_data={"start_date": "2024-01-01"},
    priority=10,
    async_execution=True,
)

***REMOVED*** Monitor running workflows
running = service.get_running_workflows()
for workflow in running:
    print(f"{workflow.name}: {workflow.status}")

***REMOVED*** Get statistics
stats = service.get_statistics(template_name="schedule_generation")
print(f"Success rate: {stats['success_rate']:.1f}%")
```

***REMOVED******REMOVED*** Workflow Definition Schema

***REMOVED******REMOVED******REMOVED*** Step Definition

```python
{
    "id": "unique_step_id",           ***REMOVED*** Unique identifier
    "name": "Human Readable Name",    ***REMOVED*** Display name
    "handler": "module.path.function", ***REMOVED*** Python handler path
    "execution_mode": "sequential",   ***REMOVED*** "sequential" or "parallel"
    "depends_on": ["step1", "step2"], ***REMOVED*** Dependencies
    "condition": "expression",        ***REMOVED*** Optional conditional (Python expr)
    "retry_policy": {
        "max_attempts": 3,            ***REMOVED*** Maximum retry attempts
        "backoff_multiplier": 2.0,    ***REMOVED*** Exponential backoff multiplier
        "max_backoff_seconds": 300,   ***REMOVED*** Maximum backoff delay
        "retry_on_timeout": True      ***REMOVED*** Retry on timeout
    },
    "timeout_seconds": 60,            ***REMOVED*** Step timeout
    "input_mapping": {                ***REMOVED*** Input parameter mapping
        "param1": "static_value",
        "param2": "step_outputs.step1.result"
    }
}
```

***REMOVED******REMOVED******REMOVED*** Complete Workflow Definition

```python
{
    "steps": [                        ***REMOVED*** List of step definitions
        ***REMOVED*** ... step objects
    ],
    "error_handlers": {               ***REMOVED*** Error handling
        "step_id": "error_handler_step_id"
    },
    "default_timeout_seconds": 3600   ***REMOVED*** Default workflow timeout
}
```

***REMOVED******REMOVED*** Step Handlers

Step handlers are async functions that receive input data and return output data:

```python
async def my_step_handler(input_data: dict) -> dict:
    """
    Custom step handler.

    Args:
        input_data: Input parameters from workflow

    Returns:
        Output data to be passed to dependent steps

    Raises:
        Exception: On failure (will trigger retry if configured)
    """
    ***REMOVED*** Process input
    result = await do_work(input_data)

    ***REMOVED*** Return output
    return {
        "success": True,
        "result": result,
        "message": "Step completed"
    }
```

***REMOVED******REMOVED*** Conditional Steps

Use Python expressions to conditionally execute steps:

```python
{
    "id": "conditional_step",
    "name": "Execute Only on Success",
    "handler": "app.handlers.conditional_handler",
    "condition": "step_outputs['previous_step']['success'] == True",
    "depends_on": ["previous_step"],
}
```

Available context in conditions:
- `step_outputs`: Dictionary of outputs from completed steps
- `input_data`: Original workflow input data
- `context`: Shared workflow context

***REMOVED******REMOVED*** Parallel Execution

Steps with the same dependencies execute in parallel:

```python
"steps": [
    {
        "id": "step1",
        "name": "Initial Step",
        "depends_on": [],
    },
    {
        "id": "step2a",
        "name": "Parallel A",
        "depends_on": ["step1"],  ***REMOVED*** Same dependency
    },
    {
        "id": "step2b",
        "name": "Parallel B",
        "depends_on": ["step1"],  ***REMOVED*** Same dependency - runs parallel with 2a
    },
]
```

***REMOVED******REMOVED*** Error Handling

***REMOVED******REMOVED******REMOVED*** Retry Logic

Steps automatically retry on failure with exponential backoff:

```python
"retry_policy": {
    "max_attempts": 3,
    "backoff_multiplier": 2.0,
    "max_backoff_seconds": 300
}
```

Retry schedule:
- Attempt 1: Immediate
- Attempt 2: Wait 2^1 = 2 seconds
- Attempt 3: Wait 2^2 = 4 seconds

***REMOVED******REMOVED******REMOVED*** Error Handlers

Configure error handler steps for specific failures:

```python
"error_handlers": {
    "critical_step": "send_error_notification"
}
```

***REMOVED******REMOVED*** Monitoring and Statistics

***REMOVED******REMOVED******REMOVED*** Query Instances

```python
***REMOVED*** Get failed workflows
failed, total = engine.query_instances(
    status="failed",
    created_after=datetime.now() - timedelta(hours=24),
)

***REMOVED*** Get high priority workflows
priority, total = engine.query_instances(
    priority_min=8,
)
```

***REMOVED******REMOVED******REMOVED*** Statistics

```python
stats = engine.get_statistics(template_id=template.id)

***REMOVED*** Returns:
{
    "total_instances": 100,
    "running_instances": 5,
    "completed_instances": 80,
    "failed_instances": 15,
    "cancelled_instances": 0,
    "success_rate": 84.2,
    "avg_duration_seconds": 45.3
}
```

***REMOVED******REMOVED*** Database Schema

***REMOVED******REMOVED******REMOVED*** WorkflowTemplate
- `id`: UUID primary key
- `name`: Template name
- `version`: Version number
- `definition`: JSON workflow definition
- `is_active`: Active flag
- `created_at`, `updated_at`: Timestamps

***REMOVED******REMOVED******REMOVED*** WorkflowInstance
- `id`: UUID primary key
- `template_id`: Foreign key to template
- `status`: Current status (pending/running/completed/failed/cancelled)
- `input_data`: JSON input parameters
- `output_data`: JSON output results
- `execution_state`: JSON execution state
- `started_at`, `completed_at`, `timeout_at`: Timestamps
- `priority`: Execution priority (0-100)

***REMOVED******REMOVED******REMOVED*** WorkflowStepExecution
- `id`: UUID primary key
- `workflow_instance_id`: Foreign key to instance
- `step_id`: Step identifier from template
- `status`: Step status
- `attempt_number`, `max_attempts`: Retry tracking
- `input_data`, `output_data`: JSON data
- `error_message`, `error_traceback`: Error details
- `started_at`, `completed_at`, `duration_seconds`: Timing

***REMOVED******REMOVED*** Best Practices

1. **Keep Steps Idempotent**: Steps should be safe to retry
2. **Use Timeouts**: Always configure appropriate timeouts
3. **Handle Errors Gracefully**: Return structured error information
4. **Log Progress**: Use structured logging in step handlers
5. **Version Templates**: Create new versions instead of modifying existing templates
6. **Monitor Execution**: Track statistics and failed workflows
7. **Test Handlers**: Unit test step handlers independently
8. **Document Workflows**: Add descriptions and tags to templates

***REMOVED******REMOVED*** Testing

See `tests/test_workflow_engine.py` for comprehensive test examples:

```bash
***REMOVED*** Run workflow engine tests
pytest backend/tests/test_workflow_engine.py -v

***REMOVED*** Run specific test
pytest backend/tests/test_workflow_engine.py::test_execute_simple_workflow -v
```

***REMOVED******REMOVED*** Example Workflows

***REMOVED******REMOVED******REMOVED*** Schedule Generation Workflow

See `WorkflowService.create_schedule_generation_workflow()` for a complete example of a multi-step workflow with:
- Input validation
- Schedule generation
- ACGME compliance checking
- Parallel conflict detection and resilience calculation
- Completion notification

***REMOVED******REMOVED*** Future Enhancements

Potential future features:
- Sub-workflows (nested workflow execution)
- Human-in-the-loop steps (approval/review)
- Dynamic step injection
- Workflow scheduling (cron-like execution)
- Workflow templates from YAML/JSON files
- Visual workflow designer
- Real-time execution monitoring dashboard
