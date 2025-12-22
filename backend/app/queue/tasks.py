"""
Task definitions and utilities for the async queue system.

Provides base classes, enums, and utilities for creating and managing
tasks with advanced features like priority, dependencies, and progress tracking.
"""

import logging
import time
import uuid
from datetime import datetime, timedelta
from enum import IntEnum
from typing import Any, Callable, Optional

from celery import Task, group, chain
from celery.exceptions import Retry
from celery.result import AsyncResult

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


class TaskPriority(IntEnum):
    """
    Task priority levels.

    Higher numbers = higher priority.
    These map to Celery's priority system (0-9, where 9 is highest).
    """

    LOW = 3
    NORMAL = 5
    HIGH = 7
    CRITICAL = 9


class TaskStatus(str):
    """Task status constants."""

    PENDING = "pending"
    RECEIVED = "received"
    STARTED = "started"
    PROGRESS = "progress"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"
    REJECTED = "rejected"


class BaseQueueTask(Task):
    """
    Base task class with enhanced features.

    Provides:
    - Automatic retry with exponential backoff
    - Progress tracking
    - Dead letter queue for failed tasks
    - Task timing and metrics
    - Error handling and logging
    """

    # Default retry policy
    autoretry_for = (Exception,)
    max_retries = 3
    retry_backoff = True  # Exponential backoff
    retry_backoff_max = 600  # Max 10 minutes
    retry_jitter = True  # Add randomness to avoid thundering herd

    # Task timing
    track_started = True
    acks_late = True  # Acknowledge after task completes (ensures no loss on worker crash)
    reject_on_worker_lost = True

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the task with timing and error handling.

        Args:
            *args: Positional arguments for the task
            **kwargs: Keyword arguments for the task

        Returns:
            Any: Task result
        """
        start_time = time.time()
        try:
            logger.info(f"Starting task {self.name} (ID: {self.request.id})")
            result = super().__call__(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(
                f"Task {self.name} completed successfully in {duration:.2f}s "
                f"(ID: {self.request.id})"
            )
            return result
        except Exception as exc:
            duration = time.time() - start_time
            logger.error(
                f"Task {self.name} failed after {duration:.2f}s "
                f"(ID: {self.request.id}): {exc}",
                exc_info=True,
            )
            raise

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """
        Handler called when task is retried.

        Args:
            exc: Exception that caused the retry
            task_id: Unique task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
            einfo: Exception info
        """
        logger.warning(
            f"Task {self.name} is being retried (ID: {task_id}, "
            f"retry {self.request.retries}/{self.max_retries}): {exc}"
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_failure(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any
    ) -> None:
        """
        Handler called when task fails after all retries.

        Sends failed task to dead letter queue for investigation.

        Args:
            exc: Exception that caused the failure
            task_id: Unique task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
            einfo: Exception info
        """
        logger.error(
            f"Task {self.name} failed permanently (ID: {task_id}): {exc}",
            exc_info=True,
        )

        # Send to dead letter queue
        try:
            from app.queue.manager import QueueManager

            queue_manager = QueueManager()
            queue_manager.send_to_dead_letter_queue(
                task_id=task_id,
                task_name=self.name,
                args=args,
                kwargs=kwargs,
                error=str(exc),
                error_type=type(exc).__name__,
                traceback=str(einfo),
            )
        except Exception as dlq_exc:
            logger.error(f"Failed to send task to dead letter queue: {dlq_exc}")

        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        """
        Handler called when task succeeds.

        Args:
            retval: Task return value
            task_id: Unique task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
        """
        logger.info(f"Task {self.name} succeeded (ID: {task_id})")
        super().on_success(retval, task_id, args, kwargs)

    def update_progress(
        self, current: int, total: int, message: str | None = None
    ) -> None:
        """
        Update task progress.

        Args:
            current: Current progress value
            total: Total progress value
            message: Optional progress message
        """
        progress = {
            "current": current,
            "total": total,
            "percentage": int((current / total) * 100) if total > 0 else 0,
        }
        if message:
            progress["message"] = message

        self.update_state(state=TaskStatus.PROGRESS, meta=progress)


# ============================================================================
# Task Creation Utilities
# ============================================================================


def create_task_chain(*tasks: tuple) -> chain:
    """
    Create a chain of tasks that execute sequentially.

    Each task's result is passed as input to the next task.

    Args:
        *tasks: Tasks to chain together (task, args, kwargs)

    Returns:
        chain: Celery chain object

    Example:
        >>> create_task_chain(
        ...     (task1, (arg1,), {}),
        ...     (task2, (), {"kwarg": "value"}),
        ... )
    """
    signatures = []
    for task_info in tasks:
        if isinstance(task_info, tuple) and len(task_info) == 3:
            task, args, kwargs = task_info
            signatures.append(task.s(*args, **kwargs))
        else:
            signatures.append(task_info)

    return chain(*signatures)


def create_task_group(*tasks: tuple) -> group:
    """
    Create a group of tasks that execute in parallel.

    Args:
        *tasks: Tasks to group together (task, args, kwargs)

    Returns:
        group: Celery group object

    Example:
        >>> create_task_group(
        ...     (task1, (arg1,), {}),
        ...     (task2, (arg2,), {}),
        ... )
    """
    signatures = []
    for task_info in tasks:
        if isinstance(task_info, tuple) and len(task_info) == 3:
            task, args, kwargs = task_info
            signatures.append(task.s(*args, **kwargs))
        else:
            signatures.append(task_info)

    return group(*signatures)


def get_task_result(task_id: str) -> AsyncResult:
    """
    Get task result object.

    Args:
        task_id: Task ID

    Returns:
        AsyncResult: Celery async result
    """
    return AsyncResult(task_id, app=celery_app)


def get_task_status(task_id: str) -> dict[str, Any]:
    """
    Get detailed task status.

    Args:
        task_id: Task ID

    Returns:
        dict: Task status information
    """
    result = get_task_result(task_id)

    status = {
        "task_id": task_id,
        "state": result.state,
        "ready": result.ready(),
        "successful": result.successful(),
        "failed": result.failed(),
    }

    if result.state == TaskStatus.PROGRESS:
        status["progress"] = result.info
    elif result.ready():
        if result.successful():
            status["result"] = result.result
        else:
            status["error"] = str(result.info)

    return status


def cancel_task(task_id: str, terminate: bool = False) -> bool:
    """
    Cancel a task.

    Args:
        task_id: Task ID to cancel
        terminate: If True, terminate the task if it's running

    Returns:
        bool: True if task was revoked
    """
    celery_app.control.revoke(task_id, terminate=terminate)
    logger.info(f"Task {task_id} cancelled (terminate={terminate})")
    return True


def retry_task(
    task_id: str,
    countdown: int | None = None,
    eta: datetime | None = None,
) -> str:
    """
    Retry a failed task.

    Args:
        task_id: Task ID to retry
        countdown: Delay in seconds before retry
        eta: Absolute time when to execute

    Returns:
        str: New task ID

    Raises:
        ValueError: If task not found or not in failed state
    """
    result = get_task_result(task_id)

    if not result.failed():
        raise ValueError(f"Task {task_id} is not in failed state")

    # Get original task info
    task_name = result.name
    task_args = result.args or ()
    task_kwargs = result.kwargs or {}

    # Create new task
    task = celery_app.tasks[task_name]
    new_result = task.apply_async(
        args=task_args,
        kwargs=task_kwargs,
        countdown=countdown,
        eta=eta,
    )

    logger.info(f"Retrying task {task_id} as new task {new_result.id}")
    return new_result.id


# ============================================================================
# Example Tasks
# ============================================================================


@celery_app.task(base=BaseQueueTask, bind=True)
def example_long_running_task(self, duration: int = 10) -> dict[str, Any]:
    """
    Example task demonstrating progress tracking.

    Args:
        duration: Task duration in seconds

    Returns:
        dict: Task completion info
    """
    for i in range(duration):
        time.sleep(1)
        self.update_progress(
            current=i + 1,
            total=duration,
            message=f"Processing step {i + 1} of {duration}",
        )

    return {
        "status": "completed",
        "duration": duration,
        "completed_at": datetime.utcnow().isoformat(),
    }


@celery_app.task(base=BaseQueueTask, bind=True)
def example_dependency_task(self, dependency_result: Any) -> dict[str, Any]:
    """
    Example task that depends on another task's result.

    Args:
        dependency_result: Result from previous task

    Returns:
        dict: Task result with dependency info
    """
    return {
        "status": "completed",
        "dependency_result": dependency_result,
        "processed_at": datetime.utcnow().isoformat(),
    }
