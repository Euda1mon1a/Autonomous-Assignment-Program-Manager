"""
Queue Management API Routes.

Provides endpoints for managing the async task queue system:
- Task submission with priority and dependencies
- Task status monitoring and progress tracking
- Task cancellation and retry
- Worker management and monitoring
- Task scheduling (delayed and recurring)
- Queue statistics and health checks
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_active_user
from app.models.user import User
from app.queue.manager import QueueManager
from app.queue.scheduler import TaskScheduler
from app.queue.tasks import TaskPriority, get_task_status
from app.queue.workers import WorkerManager
from app.schemas.queue import (
    PeriodicTaskControlRequest,
    PeriodicTaskControlResponse,
    PeriodicTaskRequest,
    PeriodicTaskResponse,
    PeriodicTasksListResponse,
    QueuePurgeRequest,
    QueuePurgeResponse,
    QueueStatsResponse,
    ScheduledTasksListResponse,
    ScheduleTaskRequest,
    ScheduleTaskResponse,
    TaskCancelRequest,
    TaskCancelResponse,
    TaskChainRequest,
    TaskDependencyRequest,
    TaskGroupRequest,
    TaskProgressResponse,
    TaskRetryRequest,
    TaskRetryResponse,
    TaskStatusResponse,
    TaskSubmitRequest,
    TaskSubmitResponse,
    WorkerControlRequest,
    WorkerControlResponse,
    WorkerHealthResponse,
    WorkerStatsResponse,
    WorkerTasksResponse,
    WorkerUtilizationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Task Submission Endpoints
# ============================================================================


@router.post("/tasks/submit", response_model=TaskSubmitResponse)
async def submit_task(
    request: TaskSubmitRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit a task to the queue.

    Supports:
    - Priority-based routing
    - Delayed execution
    - Custom queue assignment

    Requires authentication.

    Example:
        >>> POST /api/v1/queue/tasks/submit
        >>> {
        ...     "taskName": "app.tasks.process_data",
        ...     "args": [123],
        ...     "priority": 7,
        ...     "countdown": 60
        ... }
    """
    try:
        manager = QueueManager()

        # Parse ETA if provided
        eta = None
        if request.eta:
            eta = datetime.fromisoformat(request.eta)

        task_id = manager.submit_task(
            task_name=request.task_name,
            args=tuple(request.args),
            kwargs=request.kwargs,
            priority=TaskPriority(request.priority),
            countdown=request.countdown,
            eta=eta,
            queue=request.queue,
        )

        # Calculate estimated execution time
        if eta:
            estimated_execution = eta.isoformat()
        elif request.countdown:
            estimated_execution = datetime.utcnow().timestamp() + request.countdown
            estimated_execution = datetime.fromtimestamp(
                estimated_execution
            ).isoformat()
        else:
            estimated_execution = "immediate"

        return TaskSubmitResponse(
            task_id=task_id,
            task_name=request.task_name,
            status="submitted",
            message="Task submitted successfully",
            estimated_execution=estimated_execution,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail="Error submitting task")


@router.post("/tasks/submit-chain", response_model=TaskSubmitResponse)
async def submit_task_chain(
    request: TaskChainRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit a chain of tasks that execute sequentially.

    Each task's result is passed as input to the next task.

    Requires authentication.

    Example:
        >>> POST /api/v1/queue/tasks/submit-chain
        >>> {
        ...     "tasks": [
        ...         {"taskName": "task1", "args": [1], "kwargs": {}},
        ...         {"taskName": "task2", "args": [], "kwargs": {}},
        ...     ],
        ...     "priority": 5
        ... }
    """
    try:
        manager = QueueManager()

        # Parse tasks
        tasks = [
            (t["taskName"], tuple(t.get("args", [])), t.get("kwargs", {}))
            for t in request.tasks
        ]

        task_id = manager.submit_task_chain(
            tasks=tasks,
            priority=TaskPriority(request.priority),
        )

        return TaskSubmitResponse(
            task_id=task_id,
            task_name="chain",
            status="submitted",
            message=f"Task chain with {len(tasks)} tasks submitted successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting task chain: {e}")
        raise HTTPException(status_code=500, detail="Error submitting task chain")


@router.post("/tasks/submit-group", response_model=TaskSubmitResponse)
async def submit_task_group(
    request: TaskGroupRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit a group of tasks that execute in parallel.

    Requires authentication.

    Example:
        >>> POST /api/v1/queue/tasks/submit-group
        >>> {
        ...     "tasks": [
        ...         {"taskName": "task1", "args": [1], "kwargs": {}},
        ...         {"taskName": "task2", "args": [2], "kwargs": {}},
        ...     ],
        ...     "priority": 5
        ... }
    """
    try:
        manager = QueueManager()

        # Parse tasks
        tasks = [
            (t["taskName"], tuple(t.get("args", [])), t.get("kwargs", {}))
            for t in request.tasks
        ]

        task_id = manager.submit_task_group(
            tasks=tasks,
            priority=TaskPriority(request.priority),
        )

        return TaskSubmitResponse(
            task_id=task_id,
            task_name="group",
            status="submitted",
            message=f"Task group with {len(tasks)} tasks submitted successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting task group: {e}")
        raise HTTPException(status_code=500, detail="Error submitting task group")


@router.post("/tasks/submit-with-dependencies", response_model=TaskSubmitResponse)
async def submit_task_with_dependencies(
    request: TaskDependencyRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit a task that depends on other tasks.

    The task will only execute after all dependencies complete successfully.

    Requires authentication.

    Example:
        >>> POST /api/v1/queue/tasks/submit-with-dependencies
        >>> {
        ...     "taskName": "aggregate_results",
        ...     "dependencies": ["task-id-1", "task-id-2"],
        ...     "priority": 7
        ... }
    """
    try:
        manager = QueueManager()

        task_id = manager.submit_task_with_dependencies(
            task_name=request.task_name,
            args=tuple(request.args),
            kwargs=request.kwargs,
            dependencies=request.dependencies,
            priority=TaskPriority(request.priority),
        )

        return TaskSubmitResponse(
            task_id=task_id,
            task_name=request.task_name,
            status="submitted",
            message=f"Task submitted with {len(request.dependencies)} dependencies",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting task with dependencies: {e}")
        raise HTTPException(
            status_code=500, detail="Error submitting task with dependencies"
        )


# ============================================================================
# Task Status Endpoints
# ============================================================================


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status_endpoint(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get task status and metadata.

    Requires authentication.

    Example:
        >>> GET /api/v1/queue/tasks/{task_id}/status
    """
    try:
        status = get_task_status(task_id)
        return TaskStatusResponse(**status)

    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail="Error fetching task status")


@router.get("/tasks/{task_id}/progress", response_model=None)
async def get_task_progress(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
) -> TaskProgressResponse | None:
    """
    Get task progress information.

    Returns None if task doesn't support progress tracking.

    Requires authentication.

    Example:
        >>> GET /api/v1/queue/tasks/{task_id}/progress
    """
    try:
        manager = QueueManager()
        progress = manager.get_task_progress(task_id)

        if not progress:
            return None

        return TaskProgressResponse(task_id=task_id, **progress)

    except Exception as e:
        logger.error(f"Error getting task progress: {e}")
        raise HTTPException(status_code=500, detail="Error fetching task progress")


# ============================================================================
# Task Control Endpoints
# ============================================================================


@router.post("/tasks/cancel", response_model=TaskCancelResponse)
async def cancel_task(
    request: TaskCancelRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Cancel a task.

    Can optionally terminate the task if it's already running.

    Requires authentication.

    Example:
        >>> POST /api/v1/queue/tasks/cancel
        >>> {"taskId": "abc-123", "terminate": false}
    """
    try:
        manager = QueueManager()
        success = manager.cancel_task(request.task_id, request.terminate)

        message = f"Task {request.task_id} cancelled"
        if request.terminate:
            message += " and terminated"

        return TaskCancelResponse(
            task_id=request.task_id,
            success=success,
            message=message,
        )

    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        raise HTTPException(status_code=500, detail="Error cancelling task")


@router.post("/tasks/retry", response_model=TaskRetryResponse)
async def retry_task(
    request: TaskRetryRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Retry a failed task.

    Creates a new task with the same parameters.

    Requires authentication.

    Example:
        >>> POST /api/v1/queue/tasks/retry
        >>> {"taskId": "failed-task-id", "countdown": 60}
    """
    try:
        from app.queue.tasks import retry_task as retry_task_func

        # Parse ETA if provided
        eta = None
        if request.eta:
            eta = datetime.fromisoformat(request.eta)

        new_task_id = retry_task_func(
            task_id=request.task_id,
            countdown=request.countdown,
            eta=eta,
        )

        return TaskRetryResponse(
            original_task_id=request.task_id,
            new_task_id=new_task_id,
            message=f"Task retried as new task {new_task_id}",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrying task: {e}")
        raise HTTPException(status_code=500, detail="Error retrying task")


# ============================================================================
# Queue Statistics Endpoints
# ============================================================================


@router.get("/queues/stats", response_model=QueueStatsResponse)
async def get_queue_stats(
    queue: str | None = Query(None, description="Queue name (None for all)"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get queue statistics.

    Requires authentication.

    Example:
        >>> GET /api/v1/queue/queues/stats?queue=default
    """
    try:
        manager = QueueManager()
        stats = manager.get_queue_stats(queue_name=queue)
        return QueueStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        raise HTTPException(status_code=500, detail="Error fetching queue statistics")


@router.post("/queues/purge", response_model=QueuePurgeResponse)
async def purge_queue(
    request: QueuePurgeRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Purge all tasks from a queue.

    Warning: This operation cannot be undone. Requires confirmation.

    Requires authentication.

    Example:
        >>> POST /api/v1/queue/queues/purge
        >>> {"queueName": "test_queue", "confirm": true}
    """
    try:
        if not request.confirm:
            raise HTTPException(
                status_code=400,
                detail="Queue purge requires explicit confirmation (confirm=true)",
            )

        manager = QueueManager()
        count = manager.purge_queue(request.queue_name)

        return QueuePurgeResponse(
            queue_name=request.queue_name,
            tasks_purged=count,
            timestamp=datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purging queue: {e}")
        raise HTTPException(status_code=500, detail="Error purging queue")


# ============================================================================
# Worker Endpoints
# ============================================================================


@router.get("/workers/health", response_model=WorkerHealthResponse)
async def get_worker_health(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get worker health status.

    Requires authentication.

    Example:
        >>> GET /api/v1/queue/workers/health
    """
    try:
        manager = WorkerManager()
        health = manager.get_worker_health()
        return WorkerHealthResponse(**health)

    except Exception as e:
        logger.error(f"Error getting worker health: {e}")
        raise HTTPException(status_code=500, detail="Error fetching worker health")


@router.get("/workers/stats", response_model=WorkerStatsResponse)
async def get_worker_stats(
    worker: str | None = Query(None, description="Worker name (None for all)"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get worker statistics.

    Requires authentication.

    Example:
        >>> GET /api/v1/queue/workers/stats
    """
    try:
        manager = WorkerManager()
        stats = manager.get_worker_stats(worker_name=worker)
        return WorkerStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting worker stats: {e}")
        raise HTTPException(status_code=500, detail="Error fetching worker statistics")


@router.get("/workers/utilization", response_model=WorkerUtilizationResponse)
async def get_worker_utilization(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get worker utilization metrics.

    Requires authentication.

    Example:
        >>> GET /api/v1/queue/workers/utilization
    """
    try:
        manager = WorkerManager()
        utilization = manager.get_worker_utilization()
        return WorkerUtilizationResponse(**utilization)

    except Exception as e:
        logger.error(f"Error getting worker utilization: {e}")
        raise HTTPException(status_code=500, detail="Error fetching worker utilization")


@router.get("/workers/tasks", response_model=WorkerTasksResponse)
async def get_worker_tasks(
    worker: str | None = Query(None, description="Worker name (None for all)"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get tasks being processed by workers.

    Requires authentication.

    Example:
        >>> GET /api/v1/queue/workers/tasks
    """
    try:
        manager = WorkerManager()
        tasks = manager.get_worker_tasks(worker_name=worker)
        return WorkerTasksResponse(**tasks)

    except Exception as e:
        logger.error(f"Error getting worker tasks: {e}")
        raise HTTPException(status_code=500, detail="Error fetching worker tasks")


@router.post("/workers/control", response_model=WorkerControlResponse)
async def control_worker(
    request: WorkerControlRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Control worker operations.

    Supported actions:
    - shutdown: Shutdown worker
    - autoscale: Configure autoscaling
    - grow: Grow worker pool
    - shrink: Shrink worker pool

    Requires authentication.

    Example:
        >>> POST /api/v1/queue/workers/control
        >>> {
        ...     "workerName": "celery@worker1",
        ...     "action": "autoscale",
        ...     "parameters": {"max": 10, "min": 2}
        ... }
    """
    try:
        manager = WorkerManager()
        success = False
        message = ""

        if request.action == "shutdown":
            immediate = request.parameters.get("immediate", False)
            success = manager.shutdown_worker(request.worker_name, immediate)
            message = f"Worker {request.worker_name} shutdown initiated"

        elif request.action == "autoscale":
            max_concurrency = request.parameters.get("max", 10)
            min_concurrency = request.parameters.get("min", 2)
            success = manager.autoscale_worker(
                request.worker_name, max_concurrency, min_concurrency
            )
            message = f"Worker {request.worker_name} autoscale configured"

        elif request.action == "grow":
            n = request.parameters.get("n", 1)
            success = manager.pool_grow(request.worker_name, n)
            message = f"Worker {request.worker_name} pool grown by {n}"

        elif request.action == "shrink":
            n = request.parameters.get("n", 1)
            success = manager.pool_shrink(request.worker_name, n)
            message = f"Worker {request.worker_name} pool shrunk by {n}"

        else:
            raise HTTPException(
                status_code=400, detail=f"Invalid action: {request.action}"
            )

        return WorkerControlResponse(
            worker_name=request.worker_name,
            action=request.action,
            success=success,
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error controlling worker: {e}")
        raise HTTPException(status_code=500, detail="Error controlling worker")


# ============================================================================
# Scheduler Endpoints
# ============================================================================


@router.post("/schedule/task", response_model=ScheduleTaskResponse)
async def schedule_task(
    request: ScheduleTaskRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Schedule a task for future execution.

    Requires authentication.

    Example:
        >>> POST /api/v1/queue/schedule/task
        >>> {
        ...     "taskName": "send_reminder",
        ...     "countdown": 3600,
        ...     "priority": 7
        ... }
    """
    try:
        scheduler = TaskScheduler()

        # Parse ETA if provided
        eta = None
        if request.eta:
            eta = datetime.fromisoformat(request.eta)

        task_id = scheduler.schedule_task(
            task_name=request.task_name,
            args=tuple(request.args),
            kwargs=request.kwargs,
            eta=eta,
            countdown=request.countdown,
            priority=TaskPriority(request.priority),
        )

        # Calculate scheduled time
        if eta:
            scheduled_for = eta.isoformat()
        elif request.countdown:
            scheduled_for = datetime.utcnow().timestamp() + request.countdown
            scheduled_for = datetime.fromtimestamp(scheduled_for).isoformat()
        else:
            scheduled_for = "immediate"

        return ScheduleTaskResponse(
            task_id=task_id,
            task_name=request.task_name,
            scheduled_for=scheduled_for,
            message="Task scheduled successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error scheduling task: {e}")
        raise HTTPException(status_code=500, detail="Error scheduling task")


@router.post("/schedule/periodic", response_model=PeriodicTaskResponse)
async def add_periodic_task(
    request: PeriodicTaskRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Add a periodic (recurring) task.

    Requires Celery Beat to be running.

    Requires authentication.

    Example:
        >>> POST /api/v1/queue/schedule/periodic
        >>> {
        ...     "name": "daily-cleanup",
        ...     "taskName": "app.tasks.cleanup",
        ...     "scheduleConfig": {
        ...         "crontab": {"hour": 2, "minute": 0}
        ...     }
        ... }
    """
    try:
        scheduler = TaskScheduler()

        scheduler.add_periodic_task(
            name=request.name,
            task_name=request.task_name,
            schedule_config=request.schedule_config,
            args=tuple(request.args),
            kwargs=request.kwargs,
            options=request.options,
        )

        return PeriodicTaskResponse(
            name=request.name,
            task_name=request.task_name,
            schedule=str(request.schedule_config),
            message="Periodic task added successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding periodic task: {e}")
        raise HTTPException(status_code=500, detail="Error adding periodic task")


@router.get("/schedule/periodic", response_model=PeriodicTasksListResponse)
async def get_periodic_tasks(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all periodic tasks.

    Requires authentication.

    Example:
        >>> GET /api/v1/queue/schedule/periodic
    """
    try:
        scheduler = TaskScheduler()
        tasks = scheduler.get_periodic_tasks()
        return PeriodicTasksListResponse(**tasks)

    except Exception as e:
        logger.error(f"Error getting periodic tasks: {e}")
        raise HTTPException(status_code=500, detail="Error fetching periodic tasks")


@router.get("/schedule/scheduled", response_model=ScheduledTasksListResponse)
async def get_scheduled_tasks(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get tasks scheduled for future execution.

    Requires authentication.

    Example:
        >>> GET /api/v1/queue/schedule/scheduled
    """
    try:
        scheduler = TaskScheduler()
        tasks = scheduler.get_scheduled_tasks()
        return ScheduledTasksListResponse(**tasks)

    except Exception as e:
        logger.error(f"Error getting scheduled tasks: {e}")
        raise HTTPException(status_code=500, detail="Error fetching scheduled tasks")


@router.post("/schedule/periodic/control", response_model=PeriodicTaskControlResponse)
async def control_periodic_task(
    request: PeriodicTaskControlRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Control a periodic task (enable, disable, remove).

    Requires authentication.

    Example:
        >>> POST /api/v1/queue/schedule/periodic/control
        >>> {"name": "daily-cleanup", "action": "disable"}
    """
    try:
        scheduler = TaskScheduler()
        success = False
        message = ""

        if request.action == "enable":
            success = scheduler.enable_periodic_task(request.name)
            message = f"Periodic task '{request.name}' enabled"

        elif request.action == "disable":
            success = scheduler.disable_periodic_task(request.name)
            message = f"Periodic task '{request.name}' disabled"

        elif request.action == "remove":
            success = scheduler.remove_periodic_task(request.name)
            message = f"Periodic task '{request.name}' removed"

        else:
            raise HTTPException(
                status_code=400, detail=f"Invalid action: {request.action}"
            )

        return PeriodicTaskControlResponse(
            name=request.name,
            action=request.action,
            success=success,
            message=message,
        )

    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error controlling periodic task: {e}")
        raise HTTPException(status_code=500, detail="Error controlling periodic task")
