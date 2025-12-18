# MCP Async Task Tools Documentation

## Overview

The Scheduler MCP server provides tools for managing long-running background tasks using Celery. These tools allow MCP clients (like Claude) to:

1. **Start background tasks** - Trigger resilience analysis, metrics computation, etc.
2. **Poll task status** - Check progress and retrieve results
3. **Cancel tasks** - Revoke running or queued tasks
4. **List active tasks** - View all currently executing tasks

This enables non-blocking, asynchronous operations for compute-intensive tasks that would otherwise timeout in synchronous API calls.

---

## Prerequisites

### Backend Requirements

The async tools require the following backend services to be running:

1. **Redis** - Celery broker and result backend
2. **Celery Worker** - Processes background tasks
3. **Celery Beat** (optional) - For periodic scheduled tasks

### Start Backend Services

```bash
# Start Redis
docker-compose up -d redis

# Start Celery worker and beat
cd backend
../scripts/start-celery.sh both

# Or start individually
../scripts/start-celery.sh worker  # Worker only
../scripts/start-celery.sh beat    # Beat scheduler only
```

### Verify Services

```bash
# Check Redis connection
redis-cli ping
# Should return: PONG

# Verify Celery worker is running
cd backend
python verify_celery.py
```

---

## Available Tools

### 1. `start_background_task_tool`

Starts a new background task and returns a task ID for polling.

#### Parameters

- `task_type` (str, required): Type of task to start
- `params` (dict, optional): Task-specific parameters

#### Available Task Types

##### Resilience Tasks

| Task Type | Description | Parameters | Duration |
|-----------|-------------|------------|----------|
| `resilience_health_check` | Run system health check | None | 1-2 min |
| `resilience_contingency` | Run N-1/N-2 contingency analysis | `{"days_ahead": 90}` | 2-5 min |
| `resilience_fallback_precompute` | Precompute fallback schedules | `{"days_ahead": 90}` | 5-10 min |
| `resilience_utilization_forecast` | Forecast utilization | `{"days_ahead": 90}` | 1-3 min |
| `resilience_crisis_activation` | Activate crisis response mode | `{"severity": str, "reason": str, "approved_by": str}` | 30 sec |

##### Metrics Tasks

| Task Type | Description | Parameters | Duration |
|-----------|-------------|------------|----------|
| `metrics_computation` | Compute schedule metrics | `{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}` | 2-5 min |
| `metrics_snapshot` | Take metrics snapshot | `{"period_days": 90}` | 1-2 min |
| `metrics_cleanup` | Clean up old snapshots | `{"retention_days": 365}` | 1-2 min |
| `metrics_fairness_report` | Generate fairness trend report | `{"weeks_back": 12}` | 2-4 min |
| `metrics_version_diff` | Compare schedule versions | `{"run_id_1": "uuid", "run_id_2": "uuid"}` | 1-3 min |

#### Returns

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_type": "resilience_contingency",
  "status": "queued",
  "estimated_duration": "2-5 minutes",
  "queued_at": "2025-12-18T10:30:00Z",
  "message": "Task resilience_contingency queued successfully..."
}
```

#### Example Usage

```python
# Start a contingency analysis
result = await start_background_task_tool(
    task_type="resilience_contingency",
    params={"days_ahead": 90}
)

task_id = result["task_id"]
# Save task_id for polling
```

---

### 2. `get_task_status_tool`

Poll the status of a background task.

#### Parameters

- `task_id` (str, required): Task ID from `start_background_task_tool`

#### Returns

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "progress": 100,
  "result": {
    "timestamp": "2025-12-18T10:35:00Z",
    "n1_pass": true,
    "n2_pass": false,
    "n1_vulnerabilities_count": 0,
    "n2_fatal_pairs_count": 2
  },
  "error": null,
  "started_at": "2025-12-18T10:30:05Z",
  "completed_at": "2025-12-18T10:35:00Z"
}
```

#### Status Values

| Status | Description | Progress |
|--------|-------------|----------|
| `pending` | Waiting to be executed | 0% |
| `started` | Currently running | 50% |
| `success` | Completed successfully | 100% |
| `failure` | Task failed | 100% |
| `revoked` | Task was canceled | 100% |
| `retry` | Being retried after failure | 25% |

#### Example Usage

```python
# Poll task status
status = await get_task_status_tool(task_id="550e8400-e29b-41d4-a716-446655440000")

if status["status"] == "success":
    result = status["result"]
    print(f"Task completed: {result}")
elif status["status"] == "failure":
    error = status["error"]
    print(f"Task failed: {error}")
else:
    progress = status["progress"]
    print(f"Task in progress: {progress}%")
```

---

### 3. `cancel_task_tool`

Cancel a running or queued background task.

#### Parameters

- `task_id` (str, required): Task ID to cancel

#### Returns

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "revoked",
  "message": "Task 550e8400-e29b-41d4-a716-446655440000 has been canceled...",
  "canceled_at": "2025-12-18T10:32:00Z"
}
```

#### Notes

- Canceling a completed task has no effect
- Running tasks may not stop immediately (depends on task implementation)
- Tasks are sent a termination signal and marked as revoked

#### Example Usage

```python
# Cancel a task
result = await cancel_task_tool(task_id="550e8400-e29b-41d4-a716-446655440000")
print(result["message"])
```

---

### 4. `list_active_tasks_tool`

List all currently active (queued or running) tasks.

#### Parameters

- `task_type` (str, optional): Filter by task type

#### Returns

```json
{
  "total_active": 2,
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "task_name": "app.resilience.tasks.run_contingency_analysis",
      "task_type": "resilience_contingency",
      "status": "running",
      "started_at": "2025-12-18T10:30:05Z"
    },
    {
      "task_id": "660e8400-e29b-41d4-a716-446655440001",
      "task_name": "app.tasks.schedule_metrics_tasks.compute_schedule_metrics",
      "task_type": "metrics_computation",
      "status": "running",
      "started_at": "2025-12-18T10:29:00Z"
    }
  ],
  "queried_at": "2025-12-18T10:35:00Z"
}
```

#### Example Usage

```python
# List all active tasks
all_tasks = await list_active_tasks_tool()
print(f"Total active: {all_tasks['total_active']}")

# Filter by task type
resilience_tasks = await list_active_tasks_tool(task_type="resilience_contingency")
for task in resilience_tasks["tasks"]:
    print(f"Task {task['task_id']}: {task['status']}")
```

---

## Usage Patterns

### Pattern 1: Fire and Forget

Start a task without waiting for results:

```python
# Start task
result = await start_background_task_tool(
    task_type="resilience_health_check"
)
print(f"Health check started: {result['task_id']}")
# Continue with other work...
```

### Pattern 2: Poll Until Complete

Start a task and wait for completion:

```python
# Start task
result = await start_background_task_tool(
    task_type="metrics_computation",
    params={"start_date": "2025-01-01", "end_date": "2025-03-31"}
)
task_id = result["task_id"]

# Poll until complete
import asyncio

while True:
    status = await get_task_status_tool(task_id=task_id)

    if status["status"] == "success":
        print(f"Task completed: {status['result']}")
        break
    elif status["status"] == "failure":
        print(f"Task failed: {status['error']}")
        break
    else:
        print(f"Progress: {status['progress']}%")
        await asyncio.sleep(5)  # Wait 5 seconds before polling again
```

### Pattern 3: Timeout and Cancel

Start a task with a timeout:

```python
import asyncio

# Start task
result = await start_background_task_tool(
    task_type="resilience_fallback_precompute",
    params={"days_ahead": 90}
)
task_id = result["task_id"]

# Poll with timeout
timeout = 300  # 5 minutes
elapsed = 0
poll_interval = 10

while elapsed < timeout:
    status = await get_task_status_tool(task_id=task_id)

    if status["status"] in ["success", "failure", "revoked"]:
        break

    await asyncio.sleep(poll_interval)
    elapsed += poll_interval

# Cancel if still running
if elapsed >= timeout:
    await cancel_task_tool(task_id=task_id)
    print("Task timed out and was canceled")
```

### Pattern 4: Monitor Active Tasks

Check what's currently running:

```python
# Get all active tasks
active = await list_active_tasks_tool()

if active["total_active"] > 0:
    print(f"Found {active['total_active']} active tasks:")
    for task in active["tasks"]:
        print(f"  - {task['task_type']}: {task['status']}")
else:
    print("No active tasks")
```

---

## Error Handling

All async tools raise exceptions for error conditions:

### Common Exceptions

| Exception | Cause | Resolution |
|-----------|-------|------------|
| `ValueError` | Invalid task_type or params | Check task type spelling and param types |
| `ConnectionError` | Celery/Redis connection failed | Verify Redis is running and accessible |
| `ImportError` | Backend dependencies not available | Check PYTHONPATH includes backend directory |

### Example Error Handling

```python
try:
    result = await start_background_task_tool(
        task_type="invalid_task",
        params={}
    )
except ValueError as e:
    print(f"Invalid task type: {e}")
except ConnectionError as e:
    print(f"Celery connection failed: {e}")
except ImportError as e:
    print(f"Backend not available: {e}")
```

---

## Task-Specific Examples

### Example: Run Contingency Analysis

```python
# Start contingency analysis for next 90 days
result = await start_background_task_tool(
    task_type="resilience_contingency",
    params={"days_ahead": 90}
)

task_id = result["task_id"]
print(f"Contingency analysis started: {task_id}")

# Poll for result
import asyncio
while True:
    status = await get_task_status_tool(task_id=task_id)

    if status["status"] == "success":
        result = status["result"]
        print(f"N-1 Pass: {result['n1_pass']}")
        print(f"N-2 Pass: {result['n2_pass']}")
        print(f"N-1 Vulnerabilities: {result['n1_vulnerabilities_count']}")
        print(f"N-2 Fatal Pairs: {result['n2_fatal_pairs_count']}")
        break

    await asyncio.sleep(5)
```

### Example: Compute Schedule Metrics

```python
# Compute metrics for Q1 2025
result = await start_background_task_tool(
    task_type="metrics_computation",
    params={
        "start_date": "2025-01-01",
        "end_date": "2025-03-31"
    }
)

task_id = result["task_id"]

# Wait for completion
import asyncio
while True:
    status = await get_task_status_tool(task_id=task_id)

    if status["status"] == "success":
        metrics = status["result"]["schedule_analysis"]["metrics"]
        print(f"Fairness: {metrics['fairness']['value']}")
        print(f"Coverage: {metrics['coverage']['value']}")
        print(f"Compliance: {metrics['compliance']['value']}")
        break

    await asyncio.sleep(5)
```

### Example: Activate Crisis Response

```python
# Activate crisis response (requires approval)
result = await start_background_task_tool(
    task_type="resilience_crisis_activation",
    params={
        "severity": "critical",
        "reason": "Mass absence due to weather emergency",
        "approved_by": "admin-user-id"
    }
)

task_id = result["task_id"]

# This task completes quickly (30 seconds)
import asyncio
await asyncio.sleep(5)

status = await get_task_status_tool(task_id=task_id)
if status["status"] == "success":
    print("Crisis response activated")
    print(f"Actions taken: {status['result']['actions_taken']}")
```

---

## Troubleshooting

### Task Stays in "pending" Status

**Cause**: Celery worker is not running or not connected to Redis.

**Solution**:
```bash
# Check if Celery worker is running
ps aux | grep celery

# Start Celery worker
cd backend
../scripts/start-celery.sh worker
```

### ConnectionError When Starting Tasks

**Cause**: Redis is not running or not accessible.

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
docker-compose up -d redis
```

### ImportError When Starting Tasks

**Cause**: Backend dependencies not in PYTHONPATH.

**Solution**:
```bash
# Set PYTHONPATH to include backend directory
export PYTHONPATH=/path/to/backend:$PYTHONPATH

# Or run from backend directory
cd backend
python -m app.core.celery_app
```

### Task Fails Immediately

**Cause**: Invalid parameters or task execution error.

**Solution**:
```python
# Check task status for error details
status = await get_task_status_tool(task_id=task_id)
print(f"Error: {status['error']}")

# Check Celery worker logs
# backend/logs/celery.log
```

---

## Performance Considerations

### Polling Frequency

- **Recommended**: Poll every 5-10 seconds
- **Too frequent**: Polling every second adds unnecessary load
- **Too infrequent**: Polling every 60 seconds delays result retrieval

### Task Concurrency

- Celery workers process tasks in parallel (default: 4 concurrent tasks)
- Adjust with `worker_concurrency` in `backend/app/core/celery_app.py`
- Monitor with `list_active_tasks_tool`

### Result Expiration

- Task results expire after 1 hour (configured in celery_app.py)
- Poll and save results before expiration
- Expired results return status "pending" (indistinguishable from queued)

---

## Testing

### Unit Tests

Run unit tests for async tools:

```bash
cd mcp-server
pytest tests/test_async_tools.py -v
```

### Integration Tests

Integration tests require a running Celery instance:

```bash
# Start services
docker-compose up -d redis
cd backend && ../scripts/start-celery.sh worker &

# Run integration tests
cd mcp-server
pytest tests/test_async_tools_integration.py -v
```

---

## Security Considerations

### Authentication

- MCP server tools do not enforce authentication (MCP protocol handles this)
- Backend Celery tasks may require database access (uses service account)
- Sensitive task parameters (e.g., `approved_by`) should be validated

### Authorization

- Crisis activation requires admin privileges
- MCP clients should verify user permissions before starting privileged tasks
- Task results may contain sensitive data (use appropriate access controls)

### Rate Limiting

- Consider implementing rate limits on task creation
- Use `list_active_tasks_tool` to check current load
- Prevent abuse by limiting concurrent tasks per user

---

## Advanced Usage

### Custom Task Parameters

Some tasks accept flexible parameters:

```python
# Metrics computation with custom date range
result = await start_background_task_tool(
    task_type="metrics_computation",
    params={
        "start_date": "2025-01-01",
        "end_date": "2025-12-31"  # Full year
    }
)

# Fairness report for last 6 months
result = await start_background_task_tool(
    task_type="metrics_fairness_report",
    params={
        "weeks_back": 26  # ~6 months
    }
)
```

### Chaining Tasks

Start multiple tasks in sequence:

```python
# 1. Compute metrics
metrics_result = await start_background_task_tool(
    task_type="metrics_computation"
)
metrics_task_id = metrics_result["task_id"]

# 2. Wait for completion
while True:
    status = await get_task_status_tool(task_id=metrics_task_id)
    if status["status"] == "success":
        break
    await asyncio.sleep(5)

# 3. Take snapshot
snapshot_result = await start_background_task_tool(
    task_type="metrics_snapshot"
)
```

---

## FAQ

### Q: Can I start the same task multiple times?

**A**: Yes, each invocation creates a new task with a unique task_id. Be mindful of resource usage.

### Q: What happens if Celery worker crashes during task execution?

**A**: The task will remain in "started" status indefinitely. Celery does not automatically retry crashed tasks unless configured. Monitor with `list_active_tasks_tool` and restart worker.

### Q: Can I prioritize tasks?

**A**: Celery supports task priority, but it's not currently exposed through these MCP tools. Tasks are processed FIFO within each queue.

### Q: How do I see task execution logs?

**A**: Check Celery worker logs:
```bash
# Docker logs
docker-compose logs -f backend

# Local logs
tail -f backend/logs/celery.log
```

### Q: What's the maximum task execution time?

**A**: Tasks have a 10-minute hard limit (configured in celery_app.py). Tasks exceeding this are terminated.

---

## Related Documentation

- **[MCP Server README](./README.md)** - General MCP server documentation
- **[Backend Celery Configuration](../backend/app/core/celery_app.py)** - Celery task configuration
- **[Resilience Tasks](../backend/app/resilience/tasks.py)** - Resilience analysis tasks
- **[Schedule Metrics Tasks](../backend/app/tasks/schedule_metrics_tasks.py)** - Metrics computation tasks
- **[CLAUDE.md](../CLAUDE.md)** - Project guidelines including Celery usage

---

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review [Backend Celery Configuration](../backend/app/core/celery_app.py)
3. Check Celery worker logs for task execution errors
4. File an issue in the project repository
