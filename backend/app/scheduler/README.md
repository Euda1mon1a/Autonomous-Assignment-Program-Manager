# Advanced Task Scheduler

Enterprise-grade task scheduling system for the Residency Scheduler backend with advanced features including priority queues, task dependencies, distributed locking, retry mechanisms, and health monitoring.

## Overview

The Advanced Task Scheduler extends the base APScheduler-based job scheduler with enterprise features:

- **Priority Queues**: Five priority levels (CRITICAL, HIGH, NORMAL, LOW, BACKGROUND)
- **Task Dependencies**: DAG-based dependency management with cycle detection
- **Distributed Locking**: Redis-backed distributed locks for exclusive task execution
- **Retry with Backoff**: Configurable retry strategies (exponential, linear, fixed)
- **Health Monitoring**: Real-time metrics, error tracking, and health status reporting
- **Cron Expression Parsing**: Standard cron syntax support
- **Task Execution History**: Complete audit trail of task executions

## Architecture

### Core Components

1. **AdvancedTaskScheduler**: Main scheduler orchestrating task execution
2. **PriorityTaskQueue**: Priority-based task queue management
3. **TaskDependencyGraph**: DAG-based dependency resolution
4. **DistributedTaskLock**: Redis-backed distributed locking
5. **TaskRetryManager**: Retry logic with multiple backoff strategies
6. **SchedulerHealthMonitor**: Metrics collection and health monitoring

## Usage

### Basic Task Scheduling

```python
from app.scheduler.advanced_scheduler import (
    AdvancedTaskScheduler,
    TaskDefinition,
    TaskPriority,
)

# Initialize scheduler
scheduler = AdvancedTaskScheduler()

# Define a task
task_def = TaskDefinition(
    task_id="my_task",
    task_name="My Task",
    func_path="app.tasks.my_module.my_function",
    priority=TaskPriority.HIGH,
)

# Register and schedule
scheduler.register_task(task_def)
execution_id = scheduler.schedule_task("my_task")
```

### Priority Queues

Tasks are executed in priority order:

```python
# CRITICAL tasks run first
critical_task = TaskDefinition(
    task_id="critical_task",
    task_name="Critical Task",
    func_path="app.tasks.critical.handle_emergency",
    priority=TaskPriority.CRITICAL,
)

# BACKGROUND tasks run last
background_task = TaskDefinition(
    task_id="background_task",
    task_name="Background Cleanup",
    func_path="app.tasks.maintenance.cleanup",
    priority=TaskPriority.BACKGROUND,
)
```

Priority levels (from highest to lowest):
- `CRITICAL`: Immediate execution, highest priority
- `HIGH`: Important tasks
- `NORMAL`: Standard tasks
- `LOW`: Non-urgent tasks
- `BACKGROUND`: Lowest priority, run when idle

### Task Dependencies

Create task workflows with dependencies:

```python
from app.scheduler.advanced_scheduler import TaskDependency

# Task 1: Fetch data
fetch_task = TaskDefinition(
    task_id="fetch_data",
    task_name="Fetch Data",
    func_path="app.tasks.data.fetch",
)

# Task 2: Process data (depends on fetch)
process_task = TaskDefinition(
    task_id="process_data",
    task_name="Process Data",
    func_path="app.tasks.data.process",
    dependencies=[
        TaskDependency(
            task_id="fetch_data",
            dependency_type="success",  # Only run if fetch succeeds
        )
    ],
)

# Task 3: Generate report (depends on process)
report_task = TaskDefinition(
    task_id="generate_report",
    task_name="Generate Report",
    func_path="app.tasks.reports.generate",
    dependencies=[
        TaskDependency(
            task_id="process_data",
            dependency_type="success",
        )
    ],
)
```

Dependency types:
- `completion`: Run after dependency completes (success or failure)
- `success`: Run only if dependency succeeds
- `failure`: Run only if dependency fails

### Distributed Locking

Ensure only one instance of a task runs at a time:

```python
task_def = TaskDefinition(
    task_id="exclusive_task",
    task_name="Exclusive Task",
    func_path="app.tasks.critical.exclusive_operation",
    require_lock=True,
    lock_timeout=600,  # Lock expires after 10 minutes
)
```

The scheduler automatically:
- Acquires Redis lock before execution
- Releases lock after completion
- Handles lock timeout and failures

### Retry with Backoff

Configure automatic retry for failed tasks:

```python
from app.scheduler.advanced_scheduler import RetryConfig, RetryStrategy

retry_config = RetryConfig(
    strategy=RetryStrategy.EXPONENTIAL,
    max_attempts=5,
    initial_delay=60,  # Start with 60 seconds
    max_delay=3600,  # Cap at 1 hour
    backoff_multiplier=2.0,
    jitter=True,  # Add random jitter
)

task_def = TaskDefinition(
    task_id="resilient_task",
    task_name="Resilient Task",
    func_path="app.tasks.processing.flaky_operation",
    retry_config=retry_config,
)
```

Retry strategies:
- `EXPONENTIAL`: Delay doubles with each retry (recommended)
- `LINEAR`: Delay increases linearly
- `FIXED`: Constant delay between retries
- `NONE`: No retry

### Cron Scheduling

Schedule tasks using cron expressions:

```python
# Run every hour at minute 15
scheduler.schedule_cron_task(
    task_id="hourly_task",
    cron_expression="15 * * * *",
)

# Run daily at 2:30 AM
scheduler.schedule_cron_task(
    task_id="daily_task",
    cron_expression="30 2 * * *",
)

# Run every Monday at 9 AM
scheduler.schedule_cron_task(
    task_id="weekly_task",
    cron_expression="0 9 * * 1",
)
```

### Health Monitoring

Monitor scheduler health and performance:

```python
# Get health status
health = scheduler.get_health_status()

print(f"Status: {health['status']}")  # healthy or degraded
print(f"Success Rate: {health['success_rate']}%")
print(f"Running Tasks: {health['running_tasks']}")
print(f"Queued Tasks: {health['queue_stats']['total_queued']}")
print(f"Avg Execution Time: {health['average_execution_time']}s")

# Check recent errors
for error in health['recent_errors']:
    print(f"  {error['task_name']}: {error['error']}")
```

### Task Status Tracking

Track individual task execution:

```python
execution_id = scheduler.schedule_task("my_task")

# Check status
status = scheduler.get_task_status(execution_id)

print(f"Status: {status['status']}")
print(f"Started: {status['started_time']}")
print(f"Retry Count: {status['retry_count']}")
print(f"Error: {status['error']}")
```

Task statuses:
- `PENDING`: Queued, waiting to run
- `RUNNING`: Currently executing
- `COMPLETED`: Successfully finished
- `FAILED`: Failed (will not retry)
- `RETRYING`: Failed but will retry
- `CANCELLED`: Cancelled by user
- `SKIPPED`: Skipped due to dependencies

### Cancelling Tasks

Cancel queued or running tasks:

```python
execution_id = scheduler.schedule_task("my_task")

# Cancel before execution
if scheduler.cancel_task(execution_id):
    print("Task cancelled")
else:
    print("Task not found or already completed")
```

## Integration with Existing Scheduler

The Advanced Scheduler complements the existing APScheduler-based job scheduler:

- **APScheduler** (`app.scheduler.scheduler.py`): Used for periodic tasks, cron jobs, and simple scheduling
- **Advanced Scheduler** (`app.scheduler.advanced_scheduler.py`): Used for complex workflows, priority management, and enterprise features

Use cases:
- Simple periodic tasks → Use APScheduler
- Complex workflows with dependencies → Use Advanced Scheduler
- Tasks requiring distributed locking → Use Advanced Scheduler
- Tasks needing advanced retry logic → Use Advanced Scheduler

## Configuration

The scheduler uses Redis for distributed locking. Configure via environment variables:

```bash
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password
```

Scheduler settings:

```python
scheduler = AdvancedTaskScheduler(
    redis_client=custom_redis_client,  # Optional
    max_concurrent_tasks=10,  # Maximum parallel tasks
)
```

## Performance Considerations

- **Queue Size**: Monitor queue size to prevent backlog
- **Concurrent Tasks**: Adjust `max_concurrent_tasks` based on resources
- **Lock Timeout**: Set appropriate timeout to prevent deadlocks
- **Retry Limits**: Cap `max_attempts` to prevent infinite retries
- **History Size**: Task history is automatically trimmed to 1000 entries

## Examples

See `app.scheduler.examples.py` for comprehensive usage examples including:

1. Simple task with priority
2. Task with retry configuration
3. Task dependencies (DAG)
4. Distributed locking
5. Cron scheduling
6. Multi-priority queue
7. Task timeout
8. Health monitoring
9. Complex workflow
10. Task status tracking

## Testing

Run tests:

```bash
cd backend
pytest tests/scheduler/test_advanced_scheduler.py -v
```

Test coverage:
- Priority queue operations
- Dependency graph validation
- Lock acquisition/release
- Retry logic and backoff calculation
- Health monitoring and metrics
- Task execution flow

## API Reference

### Classes

- **AdvancedTaskScheduler**: Main scheduler class
- **TaskDefinition**: Task configuration
- **TaskExecution**: Task execution state
- **TaskDependency**: Task dependency specification
- **RetryConfig**: Retry configuration
- **TaskPriority**: Priority enumeration
- **TaskStatus**: Status enumeration
- **RetryStrategy**: Retry strategy enumeration

### Key Methods

- `register_task(task_def)`: Register task definition
- `unregister_task(task_id)`: Unregister task
- `schedule_task(task_id, **kwargs)`: Schedule immediate execution
- `schedule_cron_task(task_id, cron_expression)`: Schedule cron task
- `cancel_task(execution_id)`: Cancel task
- `get_task_status(execution_id)`: Get execution status
- `get_health_status()`: Get scheduler health
- `start()`: Start scheduler (async)
- `stop(wait=True)`: Stop scheduler (async)

## Best Practices

1. **Use Appropriate Priorities**: Reserve CRITICAL for true emergencies
2. **Set Realistic Timeouts**: Prevent tasks from running indefinitely
3. **Monitor Health**: Regularly check scheduler health status
4. **Limit Dependencies**: Avoid overly complex dependency chains
5. **Test Retry Logic**: Verify retry behavior under failure scenarios
6. **Use Locks Sparingly**: Only for truly exclusive operations
7. **Clean Up**: Unregister tasks that are no longer needed

## Troubleshooting

### Tasks Not Executing

1. Check scheduler is started: `await scheduler.start()`
2. Verify task is registered: `task_id in scheduler.task_definitions`
3. Check queue size: `scheduler.task_queue.size()`
4. Review health status: `scheduler.get_health_status()`

### Lock Acquisition Failures

1. Verify Redis connection: `redis-cli ping`
2. Check lock timeout settings
3. Review lock TTL: `lock_manager.get_lock_ttl(task_id)`
4. Force release if stuck: `lock_manager.force_release(task_id)` (use with caution)

### Dependency Errors

1. Verify no circular dependencies
2. Check dependency task IDs match registered tasks
3. Ensure dependencies complete before dependents
4. Review dependency graph: `scheduler.dependency_graph.topological_sort()`

## Future Enhancements

Potential improvements:

- Persistent task queue (survive restarts)
- Multi-node coordination
- Task chaining with data passing
- WebSocket-based real-time status updates
- Grafana dashboard integration
- Advanced scheduling patterns (rate limiting, bulkhead)

## License

This component is part of the Residency Scheduler project.
