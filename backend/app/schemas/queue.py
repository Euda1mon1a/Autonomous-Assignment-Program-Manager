"""
Queue system schemas.

Pydantic models for queue management API requests and responses.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Task Submission Schemas
# ============================================================================


class TaskSubmitRequest(BaseModel):
    """Request to submit a task to the queue."""

    task_name: str = Field(..., alias="taskName", description="Name of the task to execute")
    args: list[Any] = Field(default_factory=list, description="Positional arguments")
    kwargs: dict[str, Any] = Field(default_factory=dict, description="Keyword arguments")
    priority: int = Field(default=5, ge=0, le=9, description="Task priority (0-9, 9=highest)")
    countdown: int | None = Field(None, ge=0, description="Delay in seconds before execution")
    eta: str | None = Field(None, description="ISO timestamp when to execute")
    queue: str | None = Field(None, description="Queue name (overrides priority-based routing)")

    class Config:
        populate_by_name = True


class TaskSubmitResponse(BaseModel):
    """Response after submitting a task."""

    task_id: str = Field(..., alias="taskId")
    task_name: str = Field(..., alias="taskName")
    status: str
    message: str | None = None
    estimated_execution: str | None = Field(None, alias="estimatedExecution")

    class Config:
        populate_by_name = True


# ============================================================================
# Task Chain/Group Schemas
# ============================================================================


class TaskChainRequest(BaseModel):
    """Request to submit a chain of tasks."""

    tasks: list[dict[str, Any]] = Field(..., description="List of tasks to chain")
    priority: int = Field(default=5, ge=0, le=9)

    class Config:
        populate_by_name = True


class TaskGroupRequest(BaseModel):
    """Request to submit a group of parallel tasks."""

    tasks: list[dict[str, Any]] = Field(..., description="List of tasks to group")
    priority: int = Field(default=5, ge=0, le=9)

    class Config:
        populate_by_name = True


class TaskDependencyRequest(BaseModel):
    """Request to submit a task with dependencies."""

    task_name: str = Field(..., alias="taskName")
    args: list[Any] = Field(default_factory=list)
    kwargs: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(..., description="List of task IDs that must complete first")
    priority: int = Field(default=5, ge=0, le=9)

    class Config:
        populate_by_name = True


# ============================================================================
# Task Status Schemas
# ============================================================================


class TaskStatusResponse(BaseModel):
    """Task status information."""

    task_id: str = Field(..., alias="taskId")
    state: str
    ready: bool
    successful: bool | None = None
    failed: bool | None = None
    progress: dict[str, Any] | None = None
    result: Any | None = None
    error: str | None = None
    traceback: str | None = None

    class Config:
        populate_by_name = True


class TaskProgressResponse(BaseModel):
    """Task progress information."""

    task_id: str = Field(..., alias="taskId")
    current: int
    total: int
    percentage: int
    message: str | None = None

    class Config:
        populate_by_name = True


# ============================================================================
# Task Control Schemas
# ============================================================================


class TaskCancelRequest(BaseModel):
    """Request to cancel a task."""

    task_id: str = Field(..., alias="taskId")
    terminate: bool = Field(default=False, description="Terminate if running")

    class Config:
        populate_by_name = True


class TaskCancelResponse(BaseModel):
    """Response after cancelling a task."""

    task_id: str = Field(..., alias="taskId")
    success: bool
    message: str

    class Config:
        populate_by_name = True


class TaskRetryRequest(BaseModel):
    """Request to retry a failed task."""

    task_id: str = Field(..., alias="taskId")
    countdown: int | None = Field(None, ge=0)
    eta: str | None = None

    class Config:
        populate_by_name = True


class TaskRetryResponse(BaseModel):
    """Response after retrying a task."""

    original_task_id: str = Field(..., alias="originalTaskId")
    new_task_id: str = Field(..., alias="newTaskId")
    message: str

    class Config:
        populate_by_name = True


# ============================================================================
# Queue Statistics Schemas
# ============================================================================


class QueueStatsResponse(BaseModel):
    """Queue statistics."""

    queues: dict[str, dict[str, int]]
    timestamp: str

    class Config:
        populate_by_name = True


class QueuePurgeRequest(BaseModel):
    """Request to purge a queue."""

    queue_name: str = Field(..., alias="queueName")
    confirm: bool = Field(default=False, description="Must be true to confirm purge")

    class Config:
        populate_by_name = True


class QueuePurgeResponse(BaseModel):
    """Response after purging a queue."""

    queue_name: str = Field(..., alias="queueName")
    tasks_purged: int = Field(..., alias="tasksPurged")
    timestamp: str

    class Config:
        populate_by_name = True


# ============================================================================
# Worker Schemas
# ============================================================================


class WorkerHealthResponse(BaseModel):
    """Worker health status."""

    healthy: bool
    workers: dict[str, Any]
    total_workers: int = Field(..., alias="totalWorkers")
    online_workers: int = Field(..., alias="onlineWorkers")
    timestamp: str

    class Config:
        populate_by_name = True


class WorkerStatsResponse(BaseModel):
    """Worker statistics."""

    workers: dict[str, Any]
    total_workers: int = Field(..., alias="totalWorkers")
    timestamp: str

    class Config:
        populate_by_name = True


class WorkerUtilizationResponse(BaseModel):
    """Worker utilization metrics."""

    total_workers: int = Field(..., alias="totalWorkers")
    active_workers: int = Field(..., alias="activeWorkers")
    idle_workers: int = Field(..., alias="idleWorkers")
    utilization_percentage: float = Field(..., alias="utilizationPercentage")
    timestamp: str

    class Config:
        populate_by_name = True


class WorkerTasksResponse(BaseModel):
    """Worker tasks information."""

    workers: dict[str, Any]
    timestamp: str

    class Config:
        populate_by_name = True


class WorkerControlRequest(BaseModel):
    """Request to control a worker."""

    worker_name: str = Field(..., alias="workerName")
    action: str = Field(..., description="Action: shutdown, autoscale, grow, shrink")
    parameters: dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class WorkerControlResponse(BaseModel):
    """Response after worker control action."""

    worker_name: str = Field(..., alias="workerName")
    action: str
    success: bool
    message: str

    class Config:
        populate_by_name = True


# ============================================================================
# Scheduler Schemas
# ============================================================================


class ScheduleTaskRequest(BaseModel):
    """Request to schedule a task for future execution."""

    task_name: str = Field(..., alias="taskName")
    args: list[Any] = Field(default_factory=list)
    kwargs: dict[str, Any] = Field(default_factory=dict)
    eta: str | None = Field(None, description="ISO timestamp when to execute")
    countdown: int | None = Field(None, ge=0, description="Delay in seconds")
    priority: int = Field(default=5, ge=0, le=9)

    class Config:
        populate_by_name = True


class ScheduleTaskResponse(BaseModel):
    """Response after scheduling a task."""

    task_id: str = Field(..., alias="taskId")
    task_name: str = Field(..., alias="taskName")
    scheduled_for: str = Field(..., alias="scheduledFor")
    message: str

    class Config:
        populate_by_name = True


class PeriodicTaskRequest(BaseModel):
    """Request to add a periodic task."""

    name: str = Field(..., description="Unique name for this periodic task")
    task_name: str = Field(..., alias="taskName")
    schedule_config: dict[str, Any] = Field(..., alias="scheduleConfig")
    args: list[Any] = Field(default_factory=list)
    kwargs: dict[str, Any] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class PeriodicTaskResponse(BaseModel):
    """Response after adding a periodic task."""

    name: str
    task_name: str = Field(..., alias="taskName")
    schedule: str
    message: str

    class Config:
        populate_by_name = True


class PeriodicTasksListResponse(BaseModel):
    """List of periodic tasks."""

    tasks: dict[str, Any]
    total_tasks: int = Field(..., alias="totalTasks")
    timestamp: str

    class Config:
        populate_by_name = True


class ScheduledTasksListResponse(BaseModel):
    """List of scheduled tasks."""

    tasks: dict[str, list[dict[str, Any]]]
    total_tasks: int = Field(..., alias="totalTasks")
    timestamp: str

    class Config:
        populate_by_name = True


class PeriodicTaskControlRequest(BaseModel):
    """Request to control a periodic task."""

    name: str
    action: str = Field(..., description="Action: enable, disable, remove")

    class Config:
        populate_by_name = True


class PeriodicTaskControlResponse(BaseModel):
    """Response after periodic task control action."""

    name: str
    action: str
    success: bool
    message: str

    class Config:
        populate_by_name = True


# ============================================================================
# Dead Letter Queue Schemas
# ============================================================================


class DeadLetterTask(BaseModel):
    """Task in dead letter queue."""

    task_id: str = Field(..., alias="taskId")
    task_name: str = Field(..., alias="taskName")
    args: list[Any]
    kwargs: dict[str, Any]
    error: str
    error_type: str = Field(..., alias="errorType")
    traceback: str
    failed_at: str = Field(..., alias="failedAt")

    class Config:
        populate_by_name = True


class DeadLetterQueueResponse(BaseModel):
    """Dead letter queue contents."""

    tasks: list[DeadLetterTask]
    total_tasks: int = Field(..., alias="totalTasks")
    timestamp: str

    class Config:
        populate_by_name = True
