"""
MCP Tools for Celery Async Task Management.

Provides tools for starting, monitoring, and managing background tasks
using the Celery distributed task queue.

Supports:
- Starting resilience analysis tasks
- Starting schedule metrics computation tasks
- Polling task status
- Canceling tasks
- Listing active tasks
"""

import logging
import os
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Task Type Enumerations


class TaskType(str, Enum):
    """Available background task types."""

    # Resilience tasks
    RESILIENCE_HEALTH_CHECK = "resilience_health_check"
    RESILIENCE_CONTINGENCY = "resilience_contingency"
    RESILIENCE_FALLBACK_PRECOMPUTE = "resilience_fallback_precompute"
    RESILIENCE_UTILIZATION_FORECAST = "resilience_utilization_forecast"
    RESILIENCE_CRISIS_ACTIVATION = "resilience_crisis_activation"

    # Schedule metrics tasks
    METRICS_COMPUTATION = "metrics_computation"
    METRICS_SNAPSHOT = "metrics_snapshot"
    METRICS_CLEANUP = "metrics_cleanup"
    METRICS_FAIRNESS_REPORT = "metrics_fairness_report"
    METRICS_VERSION_DIFF = "metrics_version_diff"


class TaskStatus(str, Enum):
    """Celery task statuses."""

    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    REVOKED = "revoked"
    RETRY = "retry"


# Request/Response Models


class BackgroundTaskRequest(BaseModel):
    """Request to start a background task."""

    task_type: TaskType
    params: dict[str, Any] = Field(default_factory=dict)


class BackgroundTaskResult(BaseModel):
    """Result of starting a background task."""

    task_id: str
    task_type: TaskType
    status: str
    estimated_duration: str
    queued_at: datetime
    message: str


class TaskStatusResult(BaseModel):
    """Result of checking task status."""

    task_id: str
    status: TaskStatus
    progress: int = Field(ge=0, le=100, default=0)
    result: Any | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class CancelTaskResult(BaseModel):
    """Result of canceling a task."""

    task_id: str
    status: str
    message: str
    canceled_at: datetime


class ActiveTaskInfo(BaseModel):
    """Information about an active task."""

    task_id: str
    task_name: str
    task_type: str | None = None
    status: str
    started_at: datetime | None = None


class ActiveTasksResult(BaseModel):
    """Result of listing active tasks."""

    total_active: int
    tasks: list[ActiveTaskInfo]
    queried_at: datetime


# Task Type to Celery Task Name Mapping

TASK_TYPE_MAP = {
    # Resilience tasks
    TaskType.RESILIENCE_HEALTH_CHECK: "app.resilience.tasks.periodic_health_check",
    TaskType.RESILIENCE_CONTINGENCY: "app.resilience.tasks.run_contingency_analysis",
    TaskType.RESILIENCE_FALLBACK_PRECOMPUTE: "app.resilience.tasks.precompute_fallback_schedules",
    TaskType.RESILIENCE_UTILIZATION_FORECAST: "app.resilience.tasks.generate_utilization_forecast",
    TaskType.RESILIENCE_CRISIS_ACTIVATION: "app.resilience.tasks.activate_crisis_response",

    # Schedule metrics tasks
    TaskType.METRICS_COMPUTATION: "app.tasks.schedule_metrics_tasks.compute_schedule_metrics",
    TaskType.METRICS_SNAPSHOT: "app.tasks.schedule_metrics_tasks.snapshot_metrics",
    TaskType.METRICS_CLEANUP: "app.tasks.schedule_metrics_tasks.cleanup_old_snapshots",
    TaskType.METRICS_FAIRNESS_REPORT: "app.tasks.schedule_metrics_tasks.generate_fairness_trend_report",
    TaskType.METRICS_VERSION_DIFF: "app.tasks.schedule_metrics_tasks.compute_version_diff",
}

# Estimated duration for each task type (for user information)
TASK_DURATION_ESTIMATES = {
    TaskType.RESILIENCE_HEALTH_CHECK: "1-2 minutes",
    TaskType.RESILIENCE_CONTINGENCY: "2-5 minutes",
    TaskType.RESILIENCE_FALLBACK_PRECOMPUTE: "5-10 minutes",
    TaskType.RESILIENCE_UTILIZATION_FORECAST: "1-3 minutes",
    TaskType.RESILIENCE_CRISIS_ACTIVATION: "30 seconds",
    TaskType.METRICS_COMPUTATION: "2-5 minutes",
    TaskType.METRICS_SNAPSHOT: "1-2 minutes",
    TaskType.METRICS_CLEANUP: "1-2 minutes",
    TaskType.METRICS_FAIRNESS_REPORT: "2-4 minutes",
    TaskType.METRICS_VERSION_DIFF: "1-3 minutes",
}


# Helper Functions


_celery_app = None


def get_celery_app():
    """
    Get or create a Celery application instance.

    Creates a standalone Celery client that connects to Redis using
    environment variables. This allows the MCP server to submit tasks
    and query status without needing the backend codebase.

    Returns:
        Celery application instance

    Raises:
        ImportError: If Celery is not installed
        ConnectionError: If Redis connection fails
    """
    global _celery_app

    if _celery_app is not None:
        return _celery_app

    try:
        from celery import Celery

        broker_url = os.getenv(
            "CELERY_BROKER_URL", "redis://localhost:6379/0"
        )
        result_backend = os.getenv(
            "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
        )

        _celery_app = Celery(
            "scheduler_mcp",
            broker=broker_url,
            backend=result_backend,
        )

        # Configure for remote task submission (no task autodiscovery needed)
        _celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            enable_utc=True,
            # Don't try to autodiscover tasks - we send by name
            imports=[],
        )

        logger.info(f"Created MCP Celery client connected to {broker_url}")
        return _celery_app

    except ImportError as e:
        logger.error(f"Celery not installed: {e}")
        raise ImportError("Celery package not installed.") from e


def validate_task_params(task_type: TaskType, params: dict[str, Any]) -> None:
    """
    Validate parameters for a specific task type.

    Args:
        task_type: Type of task to validate
        params: Parameters to validate

    Raises:
        ValueError: If parameters are invalid for the task type
    """
    # Resilience tasks validation
    if task_type == TaskType.RESILIENCE_CONTINGENCY:
        if "days_ahead" in params and not isinstance(params["days_ahead"], int):
            raise ValueError("days_ahead must be an integer")

    elif task_type == TaskType.RESILIENCE_FALLBACK_PRECOMPUTE:
        if "days_ahead" in params and not isinstance(params["days_ahead"], int):
            raise ValueError("days_ahead must be an integer")

    elif task_type == TaskType.RESILIENCE_UTILIZATION_FORECAST:
        if "days_ahead" in params and not isinstance(params["days_ahead"], int):
            raise ValueError("days_ahead must be an integer")

    elif task_type == TaskType.RESILIENCE_CRISIS_ACTIVATION:
        if "severity" not in params:
            raise ValueError("severity parameter required for crisis activation")
        if "reason" not in params:
            raise ValueError("reason parameter required for crisis activation")

    # Metrics tasks validation
    elif task_type == TaskType.METRICS_VERSION_DIFF:
        if "run_id_1" not in params or "run_id_2" not in params:
            raise ValueError("run_id_1 and run_id_2 required for version diff")

    elif task_type == TaskType.METRICS_SNAPSHOT:
        if "period_days" in params and not isinstance(params["period_days"], int):
            raise ValueError("period_days must be an integer")

    elif task_type == TaskType.METRICS_CLEANUP:
        if "retention_days" in params and not isinstance(params["retention_days"], int):
            raise ValueError("retention_days must be an integer")

    elif task_type == TaskType.METRICS_FAIRNESS_REPORT:
        if "weeks_back" in params and not isinstance(params["weeks_back"], int):
            raise ValueError("weeks_back must be an integer")


# Tool Functions


async def start_background_task(
    task_type: TaskType,
    params: dict[str, Any] | None = None,
) -> BackgroundTaskResult:
    """
    Start a background task using Celery.

    This tool allows you to trigger long-running background tasks such as
    resilience analysis, schedule metrics computation, or contingency planning.

    The task will run asynchronously, and you can poll its status using the
    get_task_status tool.

    Args:
        task_type: Type of task to start (e.g., resilience_contingency, metrics_computation)
        params: Optional parameters for the task (task-specific)

    Available task types and their parameters:

    Resilience Tasks:
    - resilience_health_check: No params required
    - resilience_contingency: { "days_ahead": int (default: 90) }
    - resilience_fallback_precompute: { "days_ahead": int (default: 90) }
    - resilience_utilization_forecast: { "days_ahead": int (default: 90) }
    - resilience_crisis_activation: { "severity": str, "reason": str, "approved_by": str }

    Metrics Tasks:
    - metrics_computation: { "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }
    - metrics_snapshot: { "period_days": int (default: 90) }
    - metrics_cleanup: { "retention_days": int (default: 365) }
    - metrics_fairness_report: { "weeks_back": int (default: 12) }
    - metrics_version_diff: { "run_id_1": str, "run_id_2": str }

    Returns:
        BackgroundTaskResult with task_id for status polling

    Raises:
        ValueError: If task_type is invalid or params are invalid
        ConnectionError: If Celery/Redis connection fails
        ImportError: If backend dependencies are not available
    """
    if params is None:
        params = {}

    logger.info(f"Starting background task: {task_type} with params: {params}")

    try:
        # Validate parameters
        validate_task_params(task_type, params)

        # Get Celery app
        celery_app = get_celery_app()

        # Get task name
        task_name = TASK_TYPE_MAP.get(task_type)
        if not task_name:
            raise ValueError(f"Unknown task type: {task_type}")

        # Send task to Celery
        if params:
            async_result = celery_app.send_task(task_name, kwargs=params)
        else:
            async_result = celery_app.send_task(task_name)

        task_id = async_result.id

        logger.info(f"Task started: {task_id} ({task_type})")

        return BackgroundTaskResult(
            task_id=task_id,
            task_type=task_type,
            status="queued",
            estimated_duration=TASK_DURATION_ESTIMATES.get(task_type, "2-5 minutes"),
            queued_at=datetime.utcnow(),
            message=f"Task {task_type} queued successfully. Use get_task_status to monitor progress.",
        )

    except ImportError as e:
        logger.error(f"Failed to start task - import error: {e}")
        raise ImportError(
            "Celery backend not available. Ensure backend is running and PYTHONPATH is configured."
        ) from e

    except Exception as e:
        logger.error(f"Failed to start task {task_type}: {e}")
        raise ConnectionError(
            f"Failed to queue task. Check Celery/Redis connection: {e}"
        ) from e


async def get_task_status(task_id: str) -> TaskStatusResult:
    """
    Get the status of a background task.

    This tool polls the Celery result backend to check the status of a
    previously started task. Use this to monitor progress and retrieve results.

    Args:
        task_id: The task ID returned from start_background_task

    Returns:
        TaskStatusResult with current status, progress, and result/error

    Task statuses:
    - pending: Task is waiting to be executed
    - started: Task is currently running
    - success: Task completed successfully (result available)
    - failure: Task failed (error available)
    - revoked: Task was canceled
    - retry: Task is being retried after a failure

    Raises:
        ValueError: If task_id is invalid
        ConnectionError: If Celery/Redis connection fails
    """
    if not task_id:
        raise ValueError("task_id is required")

    logger.info(f"Checking status for task: {task_id}")

    try:
        # Get Celery app
        celery_app = get_celery_app()

        # Get AsyncResult
        from celery.result import AsyncResult
        async_result = AsyncResult(task_id, app=celery_app)

        # Get status
        status = async_result.state
        result = None
        error = None
        progress = 0

        # Handle different states
        if status == "PENDING":
            progress = 0
            message_status = TaskStatus.PENDING
        elif status == "STARTED":
            progress = 50
            message_status = TaskStatus.STARTED
        elif status == "SUCCESS":
            progress = 100
            result = async_result.result
            message_status = TaskStatus.SUCCESS
        elif status == "FAILURE":
            progress = 100
            error = str(async_result.info)
            message_status = TaskStatus.FAILURE
        elif status == "REVOKED":
            progress = 100
            message_status = TaskStatus.REVOKED
        elif status == "RETRY":
            progress = 25
            message_status = TaskStatus.RETRY
        else:
            # Unknown status
            progress = 0
            message_status = TaskStatus.PENDING

        # Get timestamps if available
        started_at = None
        completed_at = None

        # Check if result has datetime info
        if hasattr(async_result, "date_done") and async_result.date_done:
            completed_at = async_result.date_done

        logger.info(f"Task {task_id} status: {status}")

        return TaskStatusResult(
            task_id=task_id,
            status=message_status,
            progress=progress,
            result=result,
            error=error,
            started_at=started_at,
            completed_at=completed_at,
        )

    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        raise ConnectionError(
            f"Failed to retrieve task status. Check Celery/Redis connection: {e}"
        ) from e


async def cancel_task(task_id: str) -> CancelTaskResult:
    """
    Cancel a running or queued background task.

    This tool revokes a Celery task, preventing it from executing if queued
    or terminating it if currently running.

    Args:
        task_id: The task ID to cancel

    Returns:
        CancelTaskResult with cancellation confirmation

    Note:
        Canceling a task that has already completed has no effect.
        Tasks that are currently executing may not stop immediately.

    Raises:
        ValueError: If task_id is invalid
        ConnectionError: If Celery/Redis connection fails
    """
    if not task_id:
        raise ValueError("task_id is required")

    logger.info(f"Canceling task: {task_id}")

    try:
        # Get Celery app
        celery_app = get_celery_app()

        # Revoke the task
        celery_app.control.revoke(task_id, terminate=True)

        logger.info(f"Task {task_id} revoked")

        return CancelTaskResult(
            task_id=task_id,
            status="revoked",
            message=f"Task {task_id} has been canceled. It will not execute if queued, or will be terminated if running.",
            canceled_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        raise ConnectionError(
            f"Failed to cancel task. Check Celery/Redis connection: {e}"
        ) from e


async def list_active_tasks(
    task_type: TaskType | None = None,
) -> ActiveTasksResult:
    """
    List all currently active (queued or running) tasks.

    This tool queries Celery to find tasks that are currently executing
    or waiting in the queue. Optionally filter by task type.

    Args:
        task_type: Optional filter by task type (e.g., resilience_contingency)

    Returns:
        ActiveTasksResult with list of active tasks

    Note:
        This requires Celery workers to be running and connected to the broker.
        The result may not include tasks that completed very recently.

    Raises:
        ConnectionError: If Celery/Redis connection fails
    """
    logger.info(f"Listing active tasks (filter: {task_type})")

    try:
        # Get Celery app
        celery_app = get_celery_app()

        # Get active tasks from all workers
        inspect = celery_app.control.inspect()
        active_tasks_dict = inspect.active()

        if not active_tasks_dict:
            logger.info("No active tasks found (or no workers connected)")
            return ActiveTasksResult(
                total_active=0,
                tasks=[],
                queried_at=datetime.utcnow(),
            )

        # Flatten tasks from all workers
        all_tasks = []
        for worker_name, tasks_list in active_tasks_dict.items():
            for task_info in tasks_list:
                task_name = task_info.get("name", "unknown")
                task_id = task_info.get("id", "unknown")

                # Try to map task name to task type
                mapped_type = None
                for ttype, tname in TASK_TYPE_MAP.items():
                    if tname == task_name:
                        mapped_type = ttype.value
                        break

                # Filter by task type if specified
                if task_type and mapped_type != task_type.value:
                    continue

                # Get start time if available
                started_at = None
                if "time_start" in task_info:
                    try:
                        started_at = datetime.fromtimestamp(task_info["time_start"])
                    except (ValueError, TypeError):
                        pass

                all_tasks.append(
                    ActiveTaskInfo(
                        task_id=task_id,
                        task_name=task_name,
                        task_type=mapped_type,
                        status="running",
                        started_at=started_at,
                    )
                )

        logger.info(f"Found {len(all_tasks)} active tasks")

        return ActiveTasksResult(
            total_active=len(all_tasks),
            tasks=all_tasks,
            queried_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Failed to list active tasks: {e}")
        raise ConnectionError(
            f"Failed to query active tasks. Check Celery/Redis connection and ensure workers are running: {e}"
        ) from e
