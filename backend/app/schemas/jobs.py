"""
Job monitoring schemas.

Pydantic models for background job monitoring, including:
- Active task listings
- Job statistics
- Worker health
- Task history
- Queue status
"""

from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Core Job Schemas
# ============================================================================


class TaskInfo(BaseModel):
    """Information about a Celery task."""
    task_id: str = Field(alias="taskId")
    task_name: str = Field(alias="taskName")
    worker: str | None = None
    queue: str | None = None
    status: str | None = None
    args: list[Any] | None = None
    kwargs: dict[str, Any] | None = None
    time_start: float | None = Field(None, alias="timeStart")
    acknowledged: bool | None = None
    ready: bool | None = None
    successful: bool | None = None
    failed: bool | None = None
    result: Any | None = None
    error: str | None = None
    traceback: str | None = None

    class Config:
        populate_by_name = True


class ScheduledTaskInfo(BaseModel):
    """Information about a scheduled task."""
    task_id: str | None = Field(None, alias="taskId")
    task_name: str = Field(alias="taskName")
    worker: str | None = None
    eta: str | None = None
    priority: int | None = None
    args: list[Any] | None = None
    kwargs: dict[str, Any] | None = None

    class Config:
        populate_by_name = True


class ReservedTaskInfo(BaseModel):
    """Information about a reserved (queued) task."""
    task_id: str = Field(alias="taskId")
    task_name: str = Field(alias="taskName")
    worker: str | None = None
    queue: str | None = None
    priority: int | None = None
    args: list[Any] | None = None
    kwargs: dict[str, Any] | None = None

    class Config:
        populate_by_name = True


# ============================================================================
# Worker Schemas
# ============================================================================


class WorkerInfo(BaseModel):
    """Information about a Celery worker."""
    name: str
    status: str
    pool: str | None = None
    max_concurrency: int | None = Field(None, alias="maxConcurrency")
    processes: list[Any] | None = None

    class Config:
        populate_by_name = True


class WorkerStats(BaseModel):
    """Statistics about Celery workers."""
    total_workers: int = Field(alias="totalWorkers")
    online_workers: int = Field(alias="onlineWorkers")
    workers: list[WorkerInfo]

    class Config:
        populate_by_name = True


class WorkerHealth(BaseModel):
    """Worker health status."""
    healthy: bool
    total_workers: int = Field(alias="totalWorkers")
    online_workers: int = Field(alias="onlineWorkers")
    offline_workers: int = Field(alias="offlineWorkers")
    workers: list[str]
    timestamp: str

    class Config:
        populate_by_name = True


# ============================================================================
# Queue Schemas
# ============================================================================


class QueueStatus(BaseModel):
    """Status of a task queue."""
    queue_name: str = Field(alias="queueName")
    active_tasks: int = Field(alias="activeTasks")
    reserved_tasks: int = Field(alias="reservedTasks")
    total_pending: int = Field(alias="totalPending")

    class Config:
        populate_by_name = True


class QueueLengths(BaseModel):
    """Queue lengths for all queues."""
    queues: dict[str, int]
    timestamp: str

    class Config:
        populate_by_name = True


# ============================================================================
# Statistics Schemas
# ============================================================================


class TaskStatistics(BaseModel):
    """Statistics for task executions."""
    task_name: str = Field(alias="taskName")
    time_range_hours: int = Field(alias="timeRangeHours")
    total_tasks: int = Field(alias="totalTasks")
    successful_tasks: int = Field(alias="successfulTasks")
    failed_tasks: int = Field(alias="failedTasks")
    pending_tasks: int = Field(alias="pendingTasks")
    retried_tasks: int = Field(alias="retriedTasks")
    success_rate: float = Field(alias="successRate")
    failure_rate: float = Field(alias="failureRate")
    average_runtime_seconds: float = Field(alias="averageRuntimeSeconds")
    min_runtime_seconds: float = Field(alias="minRuntimeSeconds")
    max_runtime_seconds: float = Field(alias="maxRuntimeSeconds")
    timestamp: str

    class Config:
        populate_by_name = True


class RetryStatistics(BaseModel):
    """Statistics for task retries."""
    task_name: str = Field(alias="taskName")
    total_retries: int = Field(alias="totalRetries")
    tasks_with_retries: int = Field(alias="tasksWithRetries")
    max_retries_used: int = Field(alias="maxRetriesUsed")
    average_retries_per_task: float = Field(alias="averageRetriesPerTask")
    retry_success_rate: float = Field(alias="retrySuccessRate")
    common_retry_reasons: list[str] = Field(alias="commonRetryReasons")
    timestamp: str

    class Config:
        populate_by_name = True


class PerformanceMetrics(BaseModel):
    """Performance metrics for tasks."""
    task_name: str = Field(alias="taskName")
    time_range_hours: int = Field(alias="timeRangeHours")
    total_executions: int = Field(alias="totalExecutions")
    average_runtime_seconds: float = Field(alias="averageRuntimeSeconds")
    median_runtime_seconds: float = Field(alias="medianRuntimeSeconds")
    p50_runtime_seconds: float = Field(alias="p50RuntimeSeconds")
    p75_runtime_seconds: float = Field(alias="p75RuntimeSeconds")
    p90_runtime_seconds: float = Field(alias="p90RuntimeSeconds")
    p95_runtime_seconds: float = Field(alias="p95RuntimeSeconds")
    p99_runtime_seconds: float = Field(alias="p99RuntimeSeconds")
    min_runtime_seconds: float = Field(alias="minRuntimeSeconds")
    max_runtime_seconds: float = Field(alias="maxRuntimeSeconds")
    std_dev_runtime_seconds: float = Field(alias="stdDevRuntimeSeconds")
    timestamp: str

    class Config:
        populate_by_name = True


class ThroughputMetrics(BaseModel):
    """Throughput metrics for task processing."""
    queue_name: str = Field(alias="queueName")
    time_range_hours: int = Field(alias="timeRangeHours")
    total_tasks_processed: int = Field(alias="totalTasksProcessed")
    tasks_per_minute: float = Field(alias="tasksPerMinute")
    tasks_per_hour: float = Field(alias="tasksPerHour")
    peak_throughput_per_hour: float = Field(alias="peakThroughputPerHour")
    average_queue_time_seconds: float = Field(alias="averageQueueTimeSeconds")
    average_processing_time_seconds: float = Field(alias="averageProcessingTimeSeconds")
    timestamp: str

    class Config:
        populate_by_name = True


class WorkerUtilization(BaseModel):
    """Worker utilization metrics."""
    total_workers: int = Field(alias="totalWorkers")
    active_workers: int = Field(alias="activeWorkers")
    idle_workers: int = Field(alias="idleWorkers")
    average_utilization_percentage: float = Field(alias="averageUtilizationPercentage")
    tasks_per_worker: float = Field(alias="tasksPerWorker")
    timestamp: str

    class Config:
        populate_by_name = True


# ============================================================================
# History Schemas
# ============================================================================


class TaskHistoryRecord(BaseModel):
    """Historical task execution record."""
    task_id: str = Field(alias="taskId")
    task_name: str = Field(alias="taskName")
    status: str
    started_at: str | None = Field(None, alias="startedAt")
    completed_at: str | None = Field(None, alias="completedAt")
    runtime_seconds: float | None = Field(None, alias="runtimeSeconds")
    worker: str | None = None
    queue: str | None = None
    retries: int | None = None
    args: list[Any] | None = None
    kwargs: dict[str, Any] | None = None
    result: Any | None = None
    error: str | None = None

    class Config:
        populate_by_name = True


class TaskHistoryResponse(BaseModel):
    """Response containing task history."""
    task_name: str | None = Field(None, alias="taskName")
    total_count: int = Field(alias="totalCount")
    limit: int
    offset: int
    tasks: list[TaskHistoryRecord]
    filters: dict[str, Any] | None = None
    timestamp: str

    class Config:
        populate_by_name = True


class TimelineBucket(BaseModel):
    """Time bucket for timeline data."""
    timestamp: str
    total_tasks: int = Field(alias="totalTasks")
    successful_tasks: int = Field(alias="successfulTasks")
    failed_tasks: int = Field(alias="failedTasks")
    average_runtime_seconds: float = Field(alias="averageRuntimeSeconds")

    class Config:
        populate_by_name = True


class TaskTimeline(BaseModel):
    """Task execution timeline."""
    task_name: str = Field(alias="taskName")
    time_range_hours: int = Field(alias="timeRangeHours")
    granularity: str
    buckets: list[TimelineBucket]
    timestamp: str

    class Config:
        populate_by_name = True


class FailureRecord(BaseModel):
    """Task failure record."""
    task_id: str = Field(alias="taskId")
    task_name: str = Field(alias="taskName")
    failed_at: str = Field(alias="failedAt")
    error_type: str = Field(alias="errorType")
    error_message: str = Field(alias="errorMessage")
    traceback: str | None = None
    worker: str | None = None
    queue: str | None = None
    retries: int | None = None
    args: list[Any] | None = None
    kwargs: dict[str, Any] | None = None

    class Config:
        populate_by_name = True


class SlowTaskRecord(BaseModel):
    """Slow task record."""
    task_id: str = Field(alias="taskId")
    task_name: str = Field(alias="taskName")
    runtime_seconds: float = Field(alias="runtimeSeconds")
    started_at: str = Field(alias="startedAt")
    completed_at: str = Field(alias="completedAt")
    worker: str | None = None
    queue: str | None = None
    status: str

    class Config:
        populate_by_name = True


# ============================================================================
# Beat Schedule Schemas
# ============================================================================


class ScheduledTaskConfig(BaseModel):
    """Configuration for a scheduled (beat) task."""
    name: str
    task: str
    schedule: str
    options: dict[str, Any] | None = None

    class Config:
        populate_by_name = True


class ScheduledTasksSummary(BaseModel):
    """Summary of scheduled tasks."""
    total_scheduled_tasks: int = Field(alias="totalScheduledTasks")
    scheduled_tasks: list[ScheduledTaskConfig] = Field(alias="scheduledTasks")
    timestamp: str

    class Config:
        populate_by_name = True


# ============================================================================
# Control Schemas
# ============================================================================


class TaskRevocationRequest(BaseModel):
    """Request to revoke (cancel) a task."""
    task_id: str = Field(alias="taskId")
    terminate: bool = False

    class Config:
        populate_by_name = True


class TaskRevocationResponse(BaseModel):
    """Response to task revocation request."""
    task_id: str = Field(alias="taskId")
    success: bool
    message: str | None = None

    class Config:
        populate_by_name = True


class QueuePurgeRequest(BaseModel):
    """Request to purge a queue."""
    queue_name: str = Field(alias="queueName")
    confirm: bool = False

    class Config:
        populate_by_name = True


class QueuePurgeResponse(BaseModel):
    """Response to queue purge request."""
    queue_name: str = Field(alias="queueName")
    tasks_purged: int = Field(alias="tasksPurged")
    timestamp: str

    class Config:
        populate_by_name = True


# ============================================================================
# Dashboard Overview Schemas
# ============================================================================


class JobsDashboardOverview(BaseModel):
    """Overview data for jobs dashboard."""
    active_tasks_count: int = Field(alias="activeTasksCount")
    scheduled_tasks_count: int = Field(alias="scheduledTasksCount")
    reserved_tasks_count: int = Field(alias="reservedTasksCount")
    total_workers: int = Field(alias="totalWorkers")
    online_workers: int = Field(alias="onlineWorkers")
    queue_counts: dict[str, int] = Field(alias="queueCounts")
    worker_utilization_percentage: float = Field(alias="workerUtilizationPercentage")
    timestamp: str

    class Config:
        populate_by_name = True
