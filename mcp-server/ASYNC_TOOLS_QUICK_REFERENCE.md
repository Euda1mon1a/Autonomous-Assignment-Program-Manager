***REMOVED*** Async Task Tools - Quick Reference

***REMOVED******REMOVED*** Prerequisites

```bash
***REMOVED*** 1. Start Redis
docker-compose up -d redis

***REMOVED*** 2. Start Celery worker
cd backend && ../scripts/start-celery.sh worker

***REMOVED*** 3. Set PYTHONPATH
export PYTHONPATH=/path/to/backend:$PYTHONPATH
```

***REMOVED******REMOVED*** Available Task Types

***REMOVED******REMOVED******REMOVED*** Resilience Tasks

| Task Type | Parameters | Duration |
|-----------|------------|----------|
| `resilience_health_check` | None | 1-2 min |
| `resilience_contingency` | `{"days_ahead": 90}` | 2-5 min |
| `resilience_fallback_precompute` | `{"days_ahead": 90}` | 5-10 min |
| `resilience_utilization_forecast` | `{"days_ahead": 90}` | 1-3 min |
| `resilience_crisis_activation` | `{"severity": str, "reason": str}` | 30 sec |

***REMOVED******REMOVED******REMOVED*** Metrics Tasks

| Task Type | Parameters | Duration |
|-----------|------------|----------|
| `metrics_computation` | `{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}` | 2-5 min |
| `metrics_snapshot` | `{"period_days": 90}` | 1-2 min |
| `metrics_cleanup` | `{"retention_days": 365}` | 1-2 min |
| `metrics_fairness_report` | `{"weeks_back": 12}` | 2-4 min |
| `metrics_version_diff` | `{"run_id_1": "uuid", "run_id_2": "uuid"}` | 1-3 min |

***REMOVED******REMOVED*** Common Patterns

***REMOVED******REMOVED******REMOVED*** Start Task

```python
result = await start_background_task_tool(
    task_type="resilience_contingency",
    params={"days_ahead": 90}
)
task_id = result["task_id"]
```

***REMOVED******REMOVED******REMOVED*** Poll Status

```python
import asyncio

while True:
    status = await get_task_status_tool(task_id=task_id)

    if status["status"] == "success":
        print(f"Result: {status['result']}")
        break
    elif status["status"] == "failure":
        print(f"Error: {status['error']}")
        break

    await asyncio.sleep(5)  ***REMOVED*** Poll every 5 seconds
```

***REMOVED******REMOVED******REMOVED*** Cancel Task

```python
result = await cancel_task_tool(task_id=task_id)
print(result["message"])
```

***REMOVED******REMOVED******REMOVED*** List Active Tasks

```python
result = await list_active_tasks_tool()
print(f"Active tasks: {result['total_active']}")

for task in result["tasks"]:
    print(f"  - {task['task_id']}: {task['status']}")
```

***REMOVED******REMOVED*** Task Status Values

| Status | Description | Progress |
|--------|-------------|----------|
| `pending` | Waiting to execute | 0% |
| `started` | Currently running | 50% |
| `success` | Completed successfully | 100% |
| `failure` | Task failed | 100% |
| `revoked` | Task canceled | 100% |
| `retry` | Being retried | 25% |

***REMOVED******REMOVED*** Error Handling

```python
try:
    result = await start_background_task_tool(
        task_type="metrics_computation",
        params={"start_date": "2025-01-01", "end_date": "2025-03-31"}
    )
except ValueError as e:
    print(f"Invalid parameters: {e}")
except ConnectionError as e:
    print(f"Celery/Redis not available: {e}")
except ImportError as e:
    print(f"Backend dependencies missing: {e}")
```

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Task stays "pending"
**Cause:** Celery worker not running
**Fix:** `cd backend && ../scripts/start-celery.sh worker`

***REMOVED******REMOVED******REMOVED*** ConnectionError
**Cause:** Redis not running
**Fix:** `docker-compose up -d redis`

***REMOVED******REMOVED******REMOVED*** ImportError
**Cause:** PYTHONPATH not set
**Fix:** `export PYTHONPATH=/path/to/backend:$PYTHONPATH`

***REMOVED******REMOVED*** Examples

See `/mcp-server/examples/async_task_example.py` for complete working examples.

***REMOVED******REMOVED*** Full Documentation

See [ASYNC_TOOLS.md](./ASYNC_TOOLS.md) for comprehensive documentation.
