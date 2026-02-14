"""
Background Job Monitoring API Routes.

Provides endpoints for monitoring and managing Celery background tasks:
- Active task listings
- Job queue status
- Worker health checks
- Task success/failure rates
- Average execution times
- Retry statistics
- Job cancellation
- Priority management
- Scheduled task overview
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.jobs import (
    FailureRecord,
    JobsDashboardOverview,
    PerformanceMetrics,
    QueuePurgeRequest,
    QueuePurgeResponse,
    QueueStatus,
    ReservedTaskInfo,
    RetryStatistics,
    ScheduledTaskConfig,
    ScheduledTaskInfo,
    ScheduledTasksSummary,
    SlowTaskRecord,
    TaskHistoryRecord,
    TaskHistoryResponse,
    TaskInfo,
    TaskRevocationRequest,
    TaskRevocationResponse,
    TaskStatistics,
    ThroughputMetrics,
    WorkerHealth,
    WorkerStats,
    WorkerUtilization,
)
from app.services.job_monitor import (
    CeleryMonitorService,
    JobHistoryService,
    JobStatsService,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _pick_value(payload: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Return the first non-null value from a payload for the provided keys."""
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return default


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _normalize_task_statistics(
    stats: dict[str, Any], task_name: str | None, hours: int
) -> dict[str, Any]:
    average_runtime = float(
        _pick_value(
            stats, "averageRuntimeSeconds", "average_runtime_seconds", default=0.0
        )
    )
    success_rate = float(_pick_value(stats, "successRate", "success_rate", default=0.0))
    total_tasks = int(_pick_value(stats, "totalTasks", "total_tasks", default=0))
    return {
        "taskName": _pick_value(
            stats, "taskName", "task_name", default=task_name or "all"
        ),
        "timeRangeHours": int(
            _pick_value(stats, "timeRangeHours", "time_range_hours", default=hours)
        ),
        "totalTasks": total_tasks,
        "successfulTasks": int(
            _pick_value(stats, "successfulTasks", "successful_tasks", default=0)
        ),
        "failedTasks": int(
            _pick_value(stats, "failedTasks", "failed_tasks", default=0)
        ),
        "pendingTasks": int(
            _pick_value(stats, "pendingTasks", "pending_tasks", default=0)
        ),
        "retriedTasks": int(
            _pick_value(stats, "retriedTasks", "retried_tasks", default=0)
        ),
        "successRate": success_rate,
        "failureRate": float(
            _pick_value(
                stats,
                "failureRate",
                "failure_rate",
                default=(100.0 - success_rate if total_tasks > 0 else 0.0),
            )
        ),
        "averageRuntimeSeconds": average_runtime,
        "minRuntimeSeconds": float(
            _pick_value(
                stats,
                "minRuntimeSeconds",
                "min_runtime_seconds",
                default=average_runtime,
            )
        ),
        "maxRuntimeSeconds": float(
            _pick_value(
                stats,
                "maxRuntimeSeconds",
                "max_runtime_seconds",
                default=average_runtime,
            )
        ),
        "timestamp": _pick_value(stats, "timestamp", default=_now_iso()),
    }


def _normalize_retry_statistics(
    stats: dict[str, Any], task_name: str | None
) -> dict[str, Any]:
    retry_reasons = _pick_value(
        stats, "commonRetryReasons", "common_retry_reasons", default=[]
    )
    if isinstance(retry_reasons, str):
        retry_reasons = [retry_reasons]
    elif not isinstance(retry_reasons, list):
        retry_reasons = list(retry_reasons) if retry_reasons else []

    return {
        "taskName": _pick_value(
            stats, "taskName", "task_name", default=task_name or "all"
        ),
        "totalRetries": int(
            _pick_value(stats, "totalRetries", "total_retries", default=0)
        ),
        "tasksWithRetries": int(
            _pick_value(stats, "tasksWithRetries", "tasks_with_retries", default=0)
        ),
        "maxRetriesUsed": int(
            _pick_value(stats, "maxRetriesUsed", "max_retries_used", default=0)
        ),
        "averageRetriesPerTask": float(
            _pick_value(
                stats, "averageRetriesPerTask", "average_retries_per_task", default=0.0
            )
        ),
        "retrySuccessRate": float(
            _pick_value(stats, "retrySuccessRate", "retry_success_rate", default=0.0)
        ),
        "commonRetryReasons": retry_reasons,
        "timestamp": _pick_value(stats, "timestamp", default=_now_iso()),
    }


def _normalize_performance_metrics(
    metrics: dict[str, Any], task_name: str | None, hours: int
) -> dict[str, Any]:
    p50_runtime = float(
        _pick_value(metrics, "p50RuntimeSeconds", "p50_runtime_seconds", default=0.0)
    )
    p95_runtime = float(
        _pick_value(
            metrics, "p95RuntimeSeconds", "p95_runtime_seconds", default=p50_runtime
        )
    )

    return {
        "taskName": _pick_value(
            metrics, "taskName", "task_name", default=task_name or "all"
        ),
        "timeRangeHours": int(
            _pick_value(metrics, "timeRangeHours", "time_range_hours", default=hours)
        ),
        "totalExecutions": int(
            _pick_value(metrics, "totalExecutions", "total_executions", default=0)
        ),
        "averageRuntimeSeconds": float(
            _pick_value(
                metrics,
                "averageRuntimeSeconds",
                "average_runtime_seconds",
                default=p50_runtime,
            )
        ),
        "medianRuntimeSeconds": float(
            _pick_value(
                metrics,
                "medianRuntimeSeconds",
                "median_runtime_seconds",
                default=p50_runtime,
            )
        ),
        "p50RuntimeSeconds": p50_runtime,
        "p75RuntimeSeconds": float(
            _pick_value(
                metrics, "p75RuntimeSeconds", "p75_runtime_seconds", default=p50_runtime
            )
        ),
        "p90RuntimeSeconds": float(
            _pick_value(
                metrics, "p90RuntimeSeconds", "p90_runtime_seconds", default=p95_runtime
            )
        ),
        "p95RuntimeSeconds": p95_runtime,
        "p99RuntimeSeconds": float(
            _pick_value(
                metrics, "p99RuntimeSeconds", "p99_runtime_seconds", default=p95_runtime
            )
        ),
        "minRuntimeSeconds": float(
            _pick_value(
                metrics, "minRuntimeSeconds", "min_runtime_seconds", default=p50_runtime
            )
        ),
        "maxRuntimeSeconds": float(
            _pick_value(
                metrics, "maxRuntimeSeconds", "max_runtime_seconds", default=p95_runtime
            )
        ),
        "stdDevRuntimeSeconds": float(
            _pick_value(
                metrics, "stdDevRuntimeSeconds", "std_dev_runtime_seconds", default=0.0
            )
        ),
        "timestamp": _pick_value(metrics, "timestamp", default=_now_iso()),
    }


def _normalize_throughput_metrics(
    metrics: dict[str, Any], queue: str | None, hours: int
) -> dict[str, Any]:
    tasks_per_hour = float(
        _pick_value(metrics, "tasksPerHour", "tasks_per_hour", default=0.0)
    )
    average_queue_time = float(
        _pick_value(
            metrics,
            "averageQueueTimeSeconds",
            "average_queue_time_seconds",
            default=0.0,
        )
    )

    return {
        "queueName": _pick_value(
            metrics, "queueName", "queue_name", default=queue or "all"
        ),
        "timeRangeHours": int(
            _pick_value(metrics, "timeRangeHours", "time_range_hours", default=hours)
        ),
        "totalTasksProcessed": int(
            _pick_value(
                metrics, "totalTasksProcessed", "total_tasks_processed", default=0
            )
        ),
        "tasksPerMinute": float(
            _pick_value(
                metrics,
                "tasksPerMinute",
                "tasks_per_minute",
                default=tasks_per_hour / 60.0,
            )
        ),
        "tasksPerHour": tasks_per_hour,
        "peakThroughputPerHour": float(
            _pick_value(
                metrics,
                "peakThroughputPerHour",
                "peak_throughput_per_hour",
                default=tasks_per_hour,
            )
        ),
        "averageQueueTimeSeconds": average_queue_time,
        "averageProcessingTimeSeconds": float(
            _pick_value(
                metrics,
                "averageProcessingTimeSeconds",
                "average_processing_time_seconds",
                default=average_queue_time,
            )
        ),
        "timestamp": _pick_value(metrics, "timestamp", default=_now_iso()),
    }


def _normalize_slow_task_record(task: dict[str, Any]) -> dict[str, Any]:
    started_at = _pick_value(task, "startedAt", "started_at", default=_now_iso())
    return {
        "taskId": str(_pick_value(task, "taskId", "task_id", default="unknown")),
        "taskName": _pick_value(task, "taskName", "task_name", default="unknown"),
        "runtimeSeconds": float(
            _pick_value(task, "runtimeSeconds", "runtime_seconds", default=0.0)
        ),
        "startedAt": started_at,
        "completedAt": _pick_value(
            task, "completedAt", "completed_at", default=started_at
        ),
        "worker": _pick_value(task, "worker"),
        "queue": _pick_value(task, "queue"),
        "status": _pick_value(task, "status", default="UNKNOWN"),
    }


# ============================================================================
# Dashboard Overview
# ============================================================================


@router.get("/dashboard", response_model=JobsDashboardOverview)
async def get_jobs_dashboard_overview(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get overview data for the jobs monitoring dashboard.

    Returns summary statistics including:
    - Active, scheduled, and reserved task counts
    - Worker status
    - Queue lengths
    - Worker utilization

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/dashboard
        {
            "activeTasksCount": 5,
            "scheduledTasksCount": 2,
            "reservedTasksCount": 10,
            "totalWorkers": 4,
            "onlineWorkers": 4,
            "queueCounts": {"default": 3, "resilience": 5, "metrics": 2},
            "workerUtilizationPercentage": 62.5,
            "timestamp": "2024-01-15T10:00:00Z"
        }
    """
    try:
        monitor = CeleryMonitorService()
        stats_service = JobStatsService()

        # Get active tasks
        active_tasks = monitor.get_active_tasks()
        scheduled_tasks = monitor.get_scheduled_tasks()
        reserved_tasks = monitor.get_reserved_tasks()

        # Get worker stats
        worker_stats = monitor.get_worker_stats()

        # Get queue counts
        queue_counts = monitor.get_queue_lengths()

        # Get worker utilization
        utilization = stats_service.get_worker_utilization()

        return JobsDashboardOverview(
            activeTasksCount=len(active_tasks),
            scheduledTasksCount=len(scheduled_tasks),
            reservedTasksCount=len(reserved_tasks),
            totalWorkers=worker_stats.get("total_workers", 0),
            onlineWorkers=worker_stats.get("online_workers", 0),
            queueCounts=queue_counts,
            workerUtilizationPercentage=utilization.get(
                "average_utilization_percentage", 0.0
            ),
            timestamp=datetime.utcnow().isoformat(),
        )

    except (ValueError, KeyError, AttributeError) as e:
        logger.error(f"Error getting jobs dashboard overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Error fetching dashboard overview"
        ) from e


# ============================================================================
# Active Tasks
# ============================================================================


@router.get("/active", response_model=list[TaskInfo])
async def get_active_tasks(
    queue: str | None = Query(None, description="Filter by queue name"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get list of currently active (running) tasks.

    Optionally filter by queue name.

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/active?queue=resilience
        [
            {
                "taskId": "abc-123-def",
                "taskName": "app.resilience.tasks.periodic_health_check",
                "worker": "celery@worker1",
                "queue": "resilience",
                "timeStart": 1705315200.0,
                "acknowledged": true
            }
        ]
    """
    try:
        monitor = CeleryMonitorService()
        tasks = monitor.get_active_tasks(queue_name=queue)

        return [
            TaskInfo(
                taskId=task["task_id"],
                taskName=task["task_name"],
                worker=task.get("worker"),
                queue=task.get("queue"),
                args=task.get("args"),
                kwargs=task.get("kwargs"),
                timeStart=task.get("time_start"),
                acknowledged=task.get("acknowledged"),
            )
            for task in tasks
        ]

    except Exception as e:
        logger.error(f"Error getting active tasks: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching active tasks"
        ) from e


@router.get("/scheduled", response_model=list[ScheduledTaskInfo])
async def get_scheduled_tasks(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get list of scheduled (not yet running) tasks.

    These are tasks scheduled to run at a future time (ETA).

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/scheduled
        [
            {
                "taskId": "xyz-789-abc",
                "taskName": "app.tasks.cleanup_tasks.cleanup_idempotency_requests",
                "worker": "celery@worker2",
                "eta": "2024-01-15T11:00:00Z",
                "priority": 5
            }
        ]
    """
    try:
        monitor = CeleryMonitorService()
        tasks = monitor.get_scheduled_tasks()

        return [
            ScheduledTaskInfo(
                taskId=task.get("task_id"),
                taskName=task["task_name"],
                worker=task.get("worker"),
                eta=task.get("eta"),
                priority=task.get("priority"),
                args=task.get("args"),
                kwargs=task.get("kwargs"),
            )
            for task in tasks
        ]

    except Exception as e:
        logger.error(f"Error getting scheduled tasks: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching scheduled tasks"
        ) from e


@router.get("/reserved", response_model=list[ReservedTaskInfo])
async def get_reserved_tasks(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get list of reserved (queued but not running) tasks.

    These are tasks in the queue waiting to be executed by a worker.

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/reserved
        [
            {
                "taskId": "def-456-ghi",
                "taskName": "app.notifications.tasks.send_email",
                "worker": "celery@worker1",
                "queue": "notifications",
                "priority": 3
            }
        ]
    """
    try:
        monitor = CeleryMonitorService()
        tasks = monitor.get_reserved_tasks()

        return [
            ReservedTaskInfo(
                taskId=task["task_id"],
                taskName=task["task_name"],
                worker=task.get("worker"),
                queue=task.get("queue"),
                priority=task.get("priority"),
                args=task.get("args"),
                kwargs=task.get("kwargs"),
            )
            for task in tasks
        ]

    except Exception as e:
        logger.error(f"Error getting reserved tasks: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching reserved tasks"
        ) from e


# ============================================================================
# Task Details
# ============================================================================


@router.get("/tasks/{task_id}", response_model=TaskInfo)
async def get_task_info(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get detailed information about a specific task.

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/tasks/abc-123-def
        {
            "taskId": "abc-123-def",
            "taskName": "app.resilience.tasks.periodic_health_check",
            "status": "SUCCESS",
            "ready": true,
            "successful": true,
            "result": {"status": "healthy"}
        }
    """
    try:
        monitor = CeleryMonitorService()
        task_info = monitor.get_task_info(task_id)

        if not task_info:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        return TaskInfo(
            taskId=task_info["task_id"],
            taskName=task_info.get("task_name"),
            status=task_info.get("state"),
            ready=task_info.get("ready"),
            successful=task_info.get("successful"),
            failed=task_info.get("failed"),
            result=task_info.get("result"),
            error=task_info.get("error"),
            traceback=task_info.get("traceback"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task info for {task_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching task information"
        ) from e


# ============================================================================
# Workers
# ============================================================================


@router.get("/workers", response_model=WorkerStats)
async def get_worker_stats(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get statistics about Celery workers.

    Returns information about all workers including:
    - Total worker count
    - Online worker count
    - Worker details (name, pool, concurrency)

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/workers
        {
            "totalWorkers": 4,
            "onlineWorkers": 4,
            "workers": [
                {
                    "name": "celery@worker1",
                    "status": "online",
                    "pool": "prefork",
                    "maxConcurrency": 4
                }
            ]
        }
    """
    try:
        monitor = CeleryMonitorService()
        stats = monitor.get_worker_stats()

        workers = [
            {
                "name": w["name"],
                "status": w["status"],
                "pool": w.get("pool"),
                "maxConcurrency": w.get("max_concurrency"),
                "processes": w.get("processes"),
            }
            for w in stats.get("workers", [])
        ]

        return WorkerStats(
            totalWorkers=stats.get("total_workers", 0),
            onlineWorkers=stats.get("online_workers", 0),
            workers=workers,
        )

    except Exception as e:
        logger.error(f"Error getting worker stats: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching worker statistics"
        ) from e


@router.get("/workers/health", response_model=WorkerHealth)
async def get_worker_health(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get comprehensive worker health status.

    Includes ping results and availability information.

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/workers/health
        {
            "healthy": true,
            "totalWorkers": 4,
            "onlineWorkers": 4,
            "offlineWorkers": 0,
            "workers": ["celery@worker1", "celery@worker2"],
            "timestamp": "2024-01-15T10:00:00Z"
        }
    """
    try:
        monitor = CeleryMonitorService()
        health = monitor.get_worker_health()

        return WorkerHealth(**health)

    except Exception as e:
        logger.error(f"Error getting worker health: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching worker health"
        ) from e


@router.get("/workers/utilization", response_model=WorkerUtilization)
async def get_worker_utilization(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get worker utilization metrics.

    Shows what percentage of workers are actively processing tasks.

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/workers/utilization
        {
            "totalWorkers": 4,
            "activeWorkers": 3,
            "idleWorkers": 1,
            "averageUtilizationPercentage": 75.0,
            "tasksPerWorker": 1.25,
            "timestamp": "2024-01-15T10:00:00Z"
        }
    """
    try:
        stats_service = JobStatsService()
        utilization = stats_service.get_worker_utilization()

        return WorkerUtilization(**utilization)

    except Exception as e:
        logger.error(f"Error getting worker utilization: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching worker utilization"
        ) from e


# ============================================================================
# Queues
# ============================================================================


@router.get("/queues", response_model=dict[str, QueueStatus])
async def get_queue_statistics(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get statistics for all queues.

    Shows active, reserved, and total pending tasks per queue.

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/queues
        {
            "resilience": {
                "queueName": "resilience",
                "activeTasks": 2,
                "reservedTasks": 5,
                "totalPending": 7
            },
            "metrics": {
                "queueName": "metrics",
                "activeTasks": 1,
                "reservedTasks": 3,
                "totalPending": 4
            }
        }
    """
    try:
        stats_service = JobStatsService()
        stats = stats_service.get_queue_statistics()

        return {
            queue_name: QueueStatus(**queue_stats)
            for queue_name, queue_stats in stats.items()
        }

    except Exception as e:
        logger.error(f"Error getting queue statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching queue statistics"
        ) from e


# ============================================================================
# Statistics
# ============================================================================


@router.get("/statistics/tasks", response_model=TaskStatistics)
async def get_task_statistics(
    task_name: str | None = Query(None, description="Filter by task name"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get statistics for tasks over a time range.

    Includes success/failure rates, execution counts, and runtime metrics.

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/statistics/tasks?task_name=app.resilience.tasks.periodic_health_check&hours=24
        {
            "taskName": "app.resilience.tasks.periodic_health_check",
            "timeRangeHours": 24,
            "totalTasks": 96,
            "successfulTasks": 95,
            "failedTasks": 1,
            "successRate": 98.96,
            "averageRuntimeSeconds": 5.2
        }
    """
    try:
        stats_service = JobStatsService()
        stats = stats_service.get_task_statistics(
            task_name=task_name, time_range_hours=hours
        )
        normalized_stats = _normalize_task_statistics(
            stats, task_name=task_name, hours=hours
        )
        return TaskStatistics(**normalized_stats)

    except Exception as e:
        logger.error(f"Error getting task statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching task statistics"
        ) from e


@router.get("/statistics/retries", response_model=RetryStatistics)
async def get_retry_statistics(
    task_name: str | None = Query(None, description="Filter by task name"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get retry statistics for tasks.

    Shows how often tasks are retrying and their success after retry.

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/statistics/retries
        {
            "taskName": "all",
            "totalRetries": 15,
            "tasksWithRetries": 8,
            "maxRetriesUsed": 3,
            "averageRetriesPerTask": 1.88,
            "retrySuccessRate": 87.5
        }
    """
    try:
        stats_service = JobStatsService()
        stats = stats_service.get_retry_statistics(task_name=task_name)
        normalized_stats = _normalize_retry_statistics(stats, task_name=task_name)
        return RetryStatistics(**normalized_stats)

    except Exception as e:
        logger.error(f"Error getting retry statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching retry statistics"
        ) from e


@router.get("/statistics/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    task_name: str | None = Query(None, description="Filter by task name"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get performance metrics for tasks.

    Includes percentile-based runtime analysis (p50, p75, p90, p95, p99).

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/statistics/performance?task_name=app.tasks.schedule_metrics_tasks.snapshot_metrics
        {
            "taskName": "app.tasks.schedule_metrics_tasks.snapshot_metrics",
            "timeRangeHours": 24,
            "totalExecutions": 24,
            "p50RuntimeSeconds": 3.2,
            "p95RuntimeSeconds": 5.8,
            "p99RuntimeSeconds": 7.1
        }
    """
    try:
        stats_service = JobStatsService()
        metrics = stats_service.get_performance_metrics(
            task_name=task_name, time_range_hours=hours
        )
        normalized_metrics = _normalize_performance_metrics(
            metrics, task_name=task_name, hours=hours
        )
        return PerformanceMetrics(**normalized_metrics)

    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching performance metrics"
        ) from e


@router.get("/statistics/throughput", response_model=ThroughputMetrics)
async def get_throughput_metrics(
    queue: str | None = Query(None, description="Filter by queue name"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get throughput metrics for task processing.

    Shows tasks per minute/hour and queue/processing times.

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/statistics/throughput?queue=resilience
        {
            "queueName": "resilience",
            "timeRangeHours": 24,
            "totalTasksProcessed": 96,
            "tasksPerHour": 4.0,
            "tasksPerMinute": 0.067,
            "averageQueueTimeSeconds": 2.5
        }
    """
    try:
        stats_service = JobStatsService()
        metrics = stats_service.get_throughput_metrics(
            queue_name=queue, time_range_hours=hours
        )
        normalized_metrics = _normalize_throughput_metrics(
            metrics, queue=queue, hours=hours
        )
        return ThroughputMetrics(**normalized_metrics)

    except Exception as e:
        logger.error(f"Error getting throughput metrics: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching throughput metrics"
        ) from e


# ============================================================================
# History
# ============================================================================


@router.get("/history", response_model=TaskHistoryResponse)
async def get_task_history(
    task_name: str | None = Query(None, description="Filter by task name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Records to skip"),
    status: str | None = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get historical task execution records.

    Supports pagination and filtering by task name and status.

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/history?limit=50&status=SUCCESS
        {
            "taskName": null,
            "totalCount": 1250,
            "limit": 50,
            "offset": 0,
            "tasks": [...]
        }
    """
    try:
        history_service = JobHistoryService()
        history = history_service.get_task_history(
            task_name=task_name, limit=limit, offset=offset, status_filter=status
        )

        tasks = [TaskHistoryRecord(**task) for task in history.get("tasks", [])]

        return TaskHistoryResponse(
            taskName=history.get("task_name"),
            totalCount=history.get("total_count", 0),
            limit=limit,
            offset=offset,
            tasks=tasks,
            filters=history.get("filters"),
            timestamp=history.get("timestamp", datetime.utcnow().isoformat()),
        )

    except Exception as e:
        logger.error(f"Error getting task history: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching task history"
        ) from e


@router.get("/history/failures", response_model=list[FailureRecord])
async def get_recent_failures(
    limit: int = Query(50, ge=1, le=500, description="Maximum failures to return"),
    task_name: str | None = Query(None, description="Filter by task name"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get recent task failures for debugging.

    Useful for identifying and troubleshooting problematic tasks.

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/history/failures?limit=10
        [
            {
                "taskId": "failed-123",
                "taskName": "app.resilience.tasks.run_contingency_analysis",
                "failedAt": "2024-01-15T09:45:00Z",
                "errorType": "DatabaseError",
                "errorMessage": "Connection timeout"
            }
        ]
    """
    try:
        history_service = JobHistoryService()
        failures = history_service.get_recent_failures(limit=limit, task_name=task_name)

        return [FailureRecord(**failure) for failure in failures]

    except Exception as e:
        logger.error(f"Error getting recent failures: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching recent failures"
        ) from e


@router.get("/history/slow", response_model=list[SlowTaskRecord])
async def get_slow_tasks(
    threshold: float = Query(60.0, ge=0.1, description="Runtime threshold in seconds"),
    limit: int = Query(50, ge=1, le=500, description="Maximum slow tasks to return"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get tasks that exceeded a runtime threshold.

    Identifies performance bottlenecks and slow-running tasks.

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/history/slow?threshold=30.0&limit=10
        [
            {
                "taskId": "slow-123",
                "taskName": "app.resilience.tasks.precompute_fallback_schedules",
                "runtimeSeconds": 125.5,
                "startedAt": "2024-01-15T08:00:00Z",
                "completedAt": "2024-01-15T08:02:05Z"
            }
        ]
    """
    try:
        history_service = JobHistoryService()
        slow_tasks = history_service.get_slow_tasks(
            threshold_seconds=threshold, limit=limit, hours=hours
        )
        return [
            SlowTaskRecord(**_normalize_slow_task_record(task)) for task in slow_tasks
        ]

    except Exception as e:
        logger.error(f"Error getting slow tasks: {e}")
        raise HTTPException(status_code=500, detail="Error fetching slow tasks") from e


# ============================================================================
# Beat Schedule
# ============================================================================


@router.get("/scheduled-tasks", response_model=ScheduledTasksSummary)
async def get_scheduled_tasks_summary(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get summary of scheduled (beat) tasks.

    Shows all periodic tasks configured in Celery Beat.

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/scheduled-tasks
        {
            "totalScheduledTasks": 8,
            "scheduledTasks": [
                {
                    "name": "resilience-health-check",
                    "task": "app.resilience.tasks.periodic_health_check",
                    "schedule": "crontab(minute='*/15')",
                    "options": {"queue": "resilience"}
                }
            ]
        }
    """
    try:
        stats_service = JobStatsService()
        summary = stats_service.get_scheduled_tasks_summary()

        tasks = [
            ScheduledTaskConfig(**task) for task in summary.get("scheduled_tasks", [])
        ]

        return ScheduledTasksSummary(
            totalScheduledTasks=summary.get("total_scheduled_tasks", 0),
            scheduledTasks=tasks,
            timestamp=summary.get("timestamp", datetime.utcnow().isoformat()),
        )

    except Exception as e:
        logger.error(f"Error getting scheduled tasks summary: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching scheduled tasks"
        ) from e


# ============================================================================
# Task Control
# ============================================================================


@router.post("/tasks/revoke", response_model=TaskRevocationResponse)
async def revoke_task(
    request: TaskRevocationRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Revoke (cancel) a task.

    Can optionally terminate the task immediately if it's already running.

    Requires authentication.

    Warning:
        Terminating running tasks can leave them in an inconsistent state.
        Use with caution.

    Example:
        >>> POST /api/v1/jobs/tasks/revoke
        >>> {"taskId": "abc-123-def", "terminate": false}
        {
            "taskId": "abc-123-def",
            "success": true,
            "message": "Task revoked successfully"
        }
    """
    try:
        monitor = CeleryMonitorService()
        success = monitor.revoke_task(
            task_id=request.task_id, terminate=request.terminate
        )

        if success:
            message = f"Task {request.task_id} revoked"
            if request.terminate:
                message += " and terminated"
        else:
            message = f"Failed to revoke task {request.task_id}"

        return TaskRevocationResponse(
            taskId=request.task_id,
            success=success,
            message=message,
        )

    except Exception as e:
        logger.error(f"Error revoking task {request.task_id}: {e}")
        raise HTTPException(status_code=500, detail="Error revoking task") from e


@router.post("/queues/purge", response_model=QueuePurgeResponse)
async def purge_queue(
    request: QueuePurgeRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Purge all tasks from a specific queue.

    Warning:
        This operation cannot be undone. Use with extreme caution.
        Requires explicit confirmation flag.

    Requires authentication.

    Example:
        >>> POST /api/v1/jobs/queues/purge
        >>> {"queueName": "test_queue", "confirm": true}
        {
            "queueName": "test_queue",
            "tasksPurged": 25,
            "timestamp": "2024-01-15T10:00:00Z"
        }
    """
    try:
        if not request.confirm:
            raise HTTPException(
                status_code=400, detail="Queue purge requires explicit confirmation"
            )

        monitor = CeleryMonitorService()
        count = monitor.purge_queue(request.queue_name)

        return QueuePurgeResponse(
            queueName=request.queue_name,
            tasksPurged=count,
            timestamp=datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purging queue {request.queue_name}: {e}")
        raise HTTPException(status_code=500, detail="Error purging queue") from e


# ============================================================================
# Registered Tasks
# ============================================================================


@router.get("/registered", response_model=list[str])
async def get_registered_tasks(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get list of all registered task names.

    Shows all tasks that workers can execute.

    Requires authentication.

    Example:
        >>> GET /api/v1/jobs/registered
        [
            "app.resilience.tasks.periodic_health_check",
            "app.resilience.tasks.run_contingency_analysis",
            "app.tasks.schedule_metrics_tasks.snapshot_metrics",
            "app.notifications.tasks.send_email"
        ]
    """
    try:
        monitor = CeleryMonitorService()
        tasks = monitor.get_registered_tasks()

        return tasks

    except Exception as e:
        logger.error(f"Error getting registered tasks: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching registered tasks"
        ) from e
