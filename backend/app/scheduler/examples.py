"""
Usage examples for the Advanced Task Scheduler.

This file demonstrates how to use the advanced task scheduler features
including priority queues, dependencies, distributed locking, and retry logic.
"""

import asyncio

from app.scheduler.advanced_scheduler import (
    RetryConfig,
    RetryStrategy,
    TaskDefinition,
    TaskDependency,
    TaskPriority,
    get_advanced_scheduler,
)


# Example 1: Simple task with priority
def example_simple_task():
    """Example of scheduling a simple task with priority."""
    scheduler = get_advanced_scheduler()

    # Register a high-priority task
    task_def = TaskDefinition(
        task_id="urgent_cleanup",
        task_name="Urgent Cleanup Task",
        func_path="app.scheduler.jobs.cleanup_old_executions",
        priority=TaskPriority.HIGH,
        args=[30],  # retention_days
    )

    scheduler.register_task(task_def)

    # Schedule the task
    execution_id = scheduler.schedule_task("urgent_cleanup")

    print(f"Scheduled task with execution_id: {execution_id}")


# Example 2: Task with retry configuration
def example_task_with_retry():
    """Example of a task with exponential backoff retry."""
    scheduler = get_advanced_scheduler()

    # Configure retry with exponential backoff
    retry_config = RetryConfig(
        strategy=RetryStrategy.EXPONENTIAL,
        max_attempts=5,
        initial_delay=60,  # Start with 60 seconds
        max_delay=3600,  # Cap at 1 hour
        backoff_multiplier=2.0,
        jitter=True,
    )

    task_def = TaskDefinition(
        task_id="resilient_task",
        task_name="Resilient Task with Retry",
        func_path="app.tasks.periodic_tasks.some_flaky_task",
        priority=TaskPriority.NORMAL,
        retry_config=retry_config,
    )

    scheduler.register_task(task_def)
    execution_id = scheduler.schedule_task("resilient_task")

    print(f"Scheduled resilient task: {execution_id}")


# Example 3: Task dependencies (DAG)
def example_task_dependencies():
    """Example of tasks with dependencies (directed acyclic graph)."""
    scheduler = get_advanced_scheduler()

    # Task 1: Fetch data (no dependencies)
    task1 = TaskDefinition(
        task_id="fetch_data",
        task_name="Fetch Data Task",
        func_path="app.tasks.data.fetch_data",
        priority=TaskPriority.NORMAL,
    )
    scheduler.register_task(task1)

    # Task 2: Process data (depends on fetch_data)
    task2 = TaskDefinition(
        task_id="process_data",
        task_name="Process Data Task",
        func_path="app.tasks.data.process_data",
        priority=TaskPriority.NORMAL,
        dependencies=[
            TaskDependency(
                task_id="fetch_data",
                dependency_type="success",  # Only run if fetch succeeded
            )
        ],
    )
    scheduler.register_task(task2)

    # Task 3: Generate report (depends on process_data)
    task3 = TaskDefinition(
        task_id="generate_report",
        task_name="Generate Report Task",
        func_path="app.tasks.reports.generate",
        priority=TaskPriority.NORMAL,
        dependencies=[
            TaskDependency(
                task_id="process_data",
                dependency_type="success",
            )
        ],
    )
    scheduler.register_task(task3)

    # Schedule all tasks
    scheduler.schedule_task("fetch_data")
    scheduler.schedule_task("process_data")
    scheduler.schedule_task("generate_report")

    print("Scheduled task dependency chain: fetch -> process -> report")


# Example 4: Task with distributed lock
def example_distributed_lock():
    """Example of a task that requires exclusive execution."""
    scheduler = get_advanced_scheduler()

    task_def = TaskDefinition(
        task_id="exclusive_task",
        task_name="Exclusive Task (Requires Lock)",
        func_path="app.tasks.critical.exclusive_operation",
        priority=TaskPriority.HIGH,
        require_lock=True,
        lock_timeout=600,  # 10 minutes
    )

    scheduler.register_task(task_def)
    execution_id = scheduler.schedule_task("exclusive_task")

    print(f"Scheduled exclusive task with lock: {execution_id}")


# Example 5: Cron-scheduled task
def example_cron_task():
    """Example of scheduling a task with a cron expression."""
    scheduler = get_advanced_scheduler()

    task_def = TaskDefinition(
        task_id="hourly_cleanup",
        task_name="Hourly Cleanup Task",
        func_path="app.scheduler.jobs.cleanup_old_executions",
        priority=TaskPriority.BACKGROUND,
        args=[90],  # retention_days
    )

    scheduler.register_task(task_def)

    # Schedule to run every hour at minute 15
    execution_ids = scheduler.schedule_cron_task(
        task_id="hourly_cleanup",
        cron_expression="15 * * * *",  # Every hour at :15
    )

    print(f"Scheduled cron task(s): {execution_ids}")


# Example 6: Multi-priority task queue
def example_multi_priority():
    """Example demonstrating priority-based task execution."""
    scheduler = get_advanced_scheduler()

    # Register tasks with different priorities
    priorities = [
        (TaskPriority.CRITICAL, "critical_alert"),
        (TaskPriority.HIGH, "high_priority_task"),
        (TaskPriority.NORMAL, "normal_task"),
        (TaskPriority.LOW, "low_priority_task"),
        (TaskPriority.BACKGROUND, "background_cleanup"),
    ]

    for priority, task_id in priorities:
        task_def = TaskDefinition(
            task_id=task_id,
            task_name=f"{priority.name} Task",
            func_path="app.scheduler.jobs.heartbeat_job",
            priority=priority,
        )
        scheduler.register_task(task_def)
        scheduler.schedule_task(task_id)

    print("Scheduled tasks with varying priorities (CRITICAL to BACKGROUND)")


# Example 7: Task with timeout
def example_task_timeout():
    """Example of a task with execution timeout."""
    scheduler = get_advanced_scheduler()

    task_def = TaskDefinition(
        task_id="timed_task",
        task_name="Task with Timeout",
        func_path="app.tasks.processing.long_running_task",
        priority=TaskPriority.NORMAL,
        timeout=300,  # 5 minutes
    )

    scheduler.register_task(task_def)
    execution_id = scheduler.schedule_task("timed_task")

    print(f"Scheduled task with 5-minute timeout: {execution_id}")


# Example 8: Monitoring and health checks
async def example_health_monitoring():
    """Example of monitoring scheduler health."""
    scheduler = get_advanced_scheduler()

    # Start scheduler
    await scheduler.start()

    # Wait a bit for tasks to execute
    await asyncio.sleep(5)

    # Get health status
    health = scheduler.get_health_status()

    print("Scheduler Health Status:")
    print(f"  Status: {health['status']}")
    print(f"  Success Rate: {health['success_rate']}%")
    print(f"  Running Tasks: {health['running_tasks']}")
    print(f"  Queued Tasks: {health['queue_stats']['total_queued']}")
    print(f"  Average Execution Time: {health['average_execution_time']}s")

    # Stop scheduler
    await scheduler.stop()


# Example 9: Complex workflow with multiple features
async def example_complex_workflow():
    """
    Example of a complex workflow combining multiple features.

    Demonstrates:
    - Task dependencies
    - Priority levels
    - Retry configuration
    - Distributed locking
    """
    scheduler = get_advanced_scheduler()

    # Step 1: Data validation (high priority, with lock)
    validate_task = TaskDefinition(
        task_id="validate_data",
        task_name="Validate Input Data",
        func_path="app.tasks.validation.validate",
        priority=TaskPriority.HIGH,
        require_lock=True,
        lock_timeout=300,
    )
    scheduler.register_task(validate_task)

    # Step 2: Data processing (depends on validation, with retry)
    process_task = TaskDefinition(
        task_id="process_validated_data",
        task_name="Process Validated Data",
        func_path="app.tasks.processing.process",
        priority=TaskPriority.NORMAL,
        dependencies=[
            TaskDependency(
                task_id="validate_data",
                dependency_type="success",
            )
        ],
        retry_config=RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            max_attempts=3,
            initial_delay=30,
        ),
    )
    scheduler.register_task(process_task)

    # Step 3: Generate report (depends on processing)
    report_task = TaskDefinition(
        task_id="generate_final_report",
        task_name="Generate Final Report",
        func_path="app.tasks.reports.generate_final",
        priority=TaskPriority.NORMAL,
        dependencies=[
            TaskDependency(
                task_id="process_validated_data",
                dependency_type="success",
            )
        ],
    )
    scheduler.register_task(report_task)

    # Step 4: Notify users (low priority, runs after report)
    notify_task = TaskDefinition(
        task_id="notify_users",
        task_name="Notify Users of Completion",
        func_path="app.tasks.notifications.send_completion",
        priority=TaskPriority.LOW,
        dependencies=[
            TaskDependency(
                task_id="generate_final_report",
                dependency_type="completion",  # Run even if report failed
            )
        ],
    )
    scheduler.register_task(notify_task)

    # Schedule the workflow
    await scheduler.start()

    scheduler.schedule_task("validate_data")
    scheduler.schedule_task("process_validated_data")
    scheduler.schedule_task("generate_final_report")
    scheduler.schedule_task("notify_users")

    print("Complex workflow scheduled:")
    print("  validate_data (HIGH, locked)")
    print("  -> process_validated_data (NORMAL, retry)")
    print("  -> generate_final_report (NORMAL)")
    print("  -> notify_users (LOW)")

    # Monitor execution
    await asyncio.sleep(10)

    health = scheduler.get_health_status()
    print(
        f"\nWorkflow Progress: {health['metrics']['tasks_completed']} tasks completed"
    )

    await scheduler.stop()


# Example 10: Scheduled task status tracking
def example_task_status_tracking():
    """Example of tracking task execution status."""
    scheduler = get_advanced_scheduler()

    task_def = TaskDefinition(
        task_id="tracked_task",
        task_name="Tracked Task",
        func_path="app.scheduler.jobs.heartbeat_job",
        priority=TaskPriority.NORMAL,
    )

    scheduler.register_task(task_def)
    execution_id = scheduler.schedule_task("tracked_task")

    # Check status
    status = scheduler.get_task_status(execution_id)

    print(f"Task Status for {execution_id}:")
    print(f"  Task Name: {status['task_name']}")
    print(f"  Status: {status['status']}")
    print(f"  Priority: {status['priority']}")
    print(f"  Scheduled Time: {status['scheduled_time']}")
    print(f"  Retry Count: {status['retry_count']}")


if __name__ == "__main__":
    """
    Run examples (for demonstration purposes).

    In production, tasks would be registered during application startup
    and scheduled via API endpoints or internal triggers.
    """
    print("=== Advanced Task Scheduler Examples ===\n")

    print("Example 1: Simple Task with Priority")
    example_simple_task()
    print()

    print("Example 2: Task with Retry")
    example_task_with_retry()
    print()

    print("Example 3: Task Dependencies")
    example_task_dependencies()
    print()

    print("Example 4: Distributed Lock")
    example_distributed_lock()
    print()

    print("Example 5: Cron Scheduling")
    example_cron_task()
    print()

    print("Example 6: Multi-Priority Queue")
    example_multi_priority()
    print()

    print("Example 7: Task Timeout")
    example_task_timeout()
    print()

    # Async examples
    print("Example 8: Health Monitoring")
    asyncio.run(example_health_monitoring())
    print()

    print("Example 9: Complex Workflow")
    asyncio.run(example_complex_workflow())
    print()

    print("Example 10: Task Status Tracking")
    example_task_status_tracking()
