"""
Task Queue Manager.

Manages task queues with advanced features:
- Priority-based task routing
- Task dependencies and workflows
- Dead letter queue for failed tasks
- Task metadata and tracking
- Queue statistics and monitoring
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

from celery import chain, chord, group
from celery.result import AsyncResult

from app.core.celery_app import celery_app
from app.queue.tasks import TaskPriority, TaskStatus, get_task_result

logger = logging.getLogger(__name__)


class QueueManager:
    """
    Manages task queues and advanced task operations.

    Provides high-level interface for:
    - Submitting tasks with priority
    - Managing task dependencies
    - Tracking task progress
    - Handling failed tasks
    """

    # Queue names by priority
    QUEUE_PRIORITY_MAP = {
        TaskPriority.LOW: "low_priority",
        TaskPriority.NORMAL: "default",
        TaskPriority.HIGH: "high_priority",
        TaskPriority.CRITICAL: "critical",
    }

    # Dead letter queue
    DEAD_LETTER_QUEUE = "dead_letter"

    def __init__(self) -> None:
        """Initialize queue manager."""
        self.app = celery_app

    def submit_task(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        countdown: int | None = None,
        eta: datetime | None = None,
        expires: datetime | None = None,
        queue: str | None = None,
        link: str | None = None,
        link_error: str | None = None,
    ) -> str:
        """
        Submit a task to the queue.

        Args:
            task_name: Name of the task to execute
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            priority: Task priority level
            countdown: Delay in seconds before execution
            eta: Absolute time when to execute
            expires: Task expiration time
            queue: Queue name (overrides priority-based routing)
            link: Task to call on success
            link_error: Task to call on failure

        Returns:
            str: Task ID

        Example:
            >>> manager = QueueManager()
            >>> task_id = manager.submit_task(
            ...     "app.tasks.process_data",
            ...     args=(data_id,),
            ...     priority=TaskPriority.HIGH,
            ...     countdown=60,
            ... )
        """
        kwargs = kwargs or {}

        # Determine queue based on priority if not specified
        if queue is None:
            queue = self.QUEUE_PRIORITY_MAP.get(priority, "default")

            # Get task from registry
        task = self.app.tasks.get(task_name)
        if not task:
            raise ValueError(f"Task {task_name} not found in registry")

            # Submit task
        result = task.apply_async(
            args=args,
            kwargs=kwargs,
            priority=int(priority),
            countdown=countdown,
            eta=eta,
            expires=expires,
            queue=queue,
            link=link,
            link_error=link_error,
        )

        logger.info(
            f"Task {task_name} submitted with ID {result.id} "
            f"(priority={priority.name}, queue={queue})"
        )

        return result.id

    def submit_task_with_dependencies(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict | None = None,
        dependencies: list[str] | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """
        Submit a task that depends on other tasks.

        The task will only execute after all dependencies complete successfully.

        Args:
            task_name: Name of the task to execute
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            dependencies: List of task IDs that must complete first
            priority: Task priority level

        Returns:
            str: Task ID

        Example:
            >>> task_id = manager.submit_task_with_dependencies(
            ...     "app.tasks.aggregate_results",
            ...     dependencies=[task1_id, task2_id, task3_id],
            ... )
        """
        kwargs = kwargs or {}
        dependencies = dependencies or []

        if not dependencies:
            # No dependencies, submit normally
            return self.submit_task(task_name, args, kwargs, priority)

            # Wait for all dependencies to complete
            # Use chord: (group of dependencies) | callback task
        task = self.app.tasks.get(task_name)
        if not task:
            raise ValueError(f"Task {task_name} not found in registry")

            # Create dependency group (empty tasks that just return AsyncResult)
        dep_results = [AsyncResult(dep_id, app=self.app) for dep_id in dependencies]

        # Create a chord: wait for all dependencies, then execute task
        callback = task.s(*args, **kwargs)
        workflow = chord(dep_results)(callback)

        logger.info(
            f"Task {task_name} submitted with {len(dependencies)} dependencies "
            f"(ID: {workflow.id})"
        )

        return workflow.id

    def submit_task_chain(
        self,
        tasks: list[tuple[str, tuple, dict]],
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """
        Submit a chain of tasks that execute sequentially.

        Each task's result is passed as input to the next task.

        Args:
            tasks: List of (task_name, args, kwargs) tuples
            priority: Task priority level

        Returns:
            str: Chain ID

        Example:
            >>> chain_id = manager.submit_task_chain([
            ...     ("task1", (arg1,), {}),
            ...     ("task2", (), {"kwarg": "value"}),
            ...     ("task3", (), {}),
            ... ])
        """
        signatures = []
        for task_name, args, kwargs in tasks:
            task = self.app.tasks.get(task_name)
            if not task:
                raise ValueError(f"Task {task_name} not found in registry")
            signatures.append(task.s(*args, **kwargs))

            # Create chain
        workflow = chain(*signatures)
        result = workflow.apply_async(priority=int(priority))

        logger.info(f"Task chain submitted with {len(tasks)} tasks (ID: {result.id})")

        return result.id

    def submit_task_group(
        self,
        tasks: list[tuple[str, tuple, dict]],
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """
        Submit a group of tasks that execute in parallel.

        Args:
            tasks: List of (task_name, args, kwargs) tuples
            priority: Task priority level

        Returns:
            str: Group ID

        Example:
            >>> group_id = manager.submit_task_group([
            ...     ("task1", (arg1,), {}),
            ...     ("task2", (arg2,), {}),
            ...     ("task3", (arg3,), {}),
            ... ])
        """
        signatures = []
        for task_name, args, kwargs in tasks:
            task = self.app.tasks.get(task_name)
            if not task:
                raise ValueError(f"Task {task_name} not found in registry")
            signatures.append(task.s(*args, **kwargs))

            # Create group
        workflow = group(*signatures)
        result = workflow.apply_async(priority=int(priority))

        logger.info(f"Task group submitted with {len(tasks)} tasks (ID: {result.id})")

        return result.id

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        """
        Get task status and metadata.

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
            "successful": result.successful() if result.ready() else None,
            "failed": result.failed() if result.ready() else None,
        }

        # Add task info if available
        if hasattr(result, "info") and result.info:
            if isinstance(result.info, dict):
                status.update(result.info)
            elif result.state == TaskStatus.PROGRESS:
                status["progress"] = result.info

                # Add result or error
        if result.ready():
            if result.successful():
                status["result"] = result.result
            else:
                status["error"] = str(result.info)
                if hasattr(result.info, "traceback"):
                    status["traceback"] = result.info.traceback

        return status

    def cancel_task(self, task_id: str, terminate: bool = False) -> bool:
        """
        Cancel a task.

        Args:
            task_id: Task ID to cancel
            terminate: If True, terminate the task if running

        Returns:
            bool: True if task was cancelled
        """
        self.app.control.revoke(task_id, terminate=terminate)
        logger.info(f"Task {task_id} cancelled (terminate={terminate})")
        return True

    def get_task_progress(self, task_id: str) -> dict[str, Any] | None:
        """
        Get task progress information.

        Args:
            task_id: Task ID

        Returns:
            dict | None: Progress information or None if not available
        """
        result = get_task_result(task_id)

        if result.state == TaskStatus.PROGRESS:
            return result.info

        return None

    def send_to_dead_letter_queue(
        self,
        task_id: str,
        task_name: str,
        args: tuple,
        kwargs: dict,
        error: str,
        error_type: str,
        traceback: str,
    ) -> None:
        """
        Send failed task to dead letter queue.

        Args:
            task_id: Failed task ID
            task_name: Task name
            args: Task arguments
            kwargs: Task keyword arguments
            error: Error message
            error_type: Error type/class
            traceback: Error traceback
        """
        dead_letter_record = {
            "task_id": task_id,
            "task_name": task_name,
            "args": args,
            "kwargs": kwargs,
            "error": error,
            "error_type": error_type,
            "traceback": traceback,
            "failed_at": datetime.utcnow().isoformat(),
        }

        logger.error(
            f"Task {task_name} (ID: {task_id}) sent to dead letter queue: {error}"
        )

        # Store in persistent dead letter queue
        self.store_in_dead_letter_queue(
            job_id=task_id,
            job_data={
                "task_name": task_name,
                "args": args,
                "kwargs": kwargs,
                "error_type": error_type,
                "traceback": traceback,
            },
            error=error,
            retry_count=0,  # Tasks reaching DLQ have exhausted retries
        )

    def store_in_dead_letter_queue(
        self, job_id: str, job_data: dict, error: str, retry_count: int
    ) -> bool:
        """
        Store failed job in persistent dead letter queue.

        Args:
            job_id: Unique job identifier
            job_data: Original job payload
            error: Error message
            retry_count: Number of retries attempted

        Returns:
            True if stored successfully
        """
        try:
            dlq_entry = {
                "job_id": job_id,
                "job_data": job_data,
                "error": str(error),
                "retry_count": retry_count,
                "failed_at": datetime.utcnow().isoformat(),
                "status": "failed",
            }

            # Try Redis first (using synchronous client)
            try:
                import redis

                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                client = redis.from_url(redis_url)

                client.lpush("dlq:failed_jobs", json.dumps(dlq_entry, default=str))
                client.close()

                logger.info(f"Stored job {job_id} in DLQ (Redis)")
                return True
            except Exception as redis_error:
                logger.warning(f"Redis DLQ failed, using file fallback: {redis_error}")

                # Fallback to file storage
            dlq_dir = os.getenv("DLQ_DIR", "/tmp/dlq")
            os.makedirs(dlq_dir, exist_ok=True)

            filepath = os.path.join(dlq_dir, f"{job_id}.json")
            with open(filepath, "w") as f:
                json.dump(dlq_entry, f, indent=2, default=str)

            logger.info(f"Stored job {job_id} in DLQ (file)")
            return True
        except Exception as e:
            logger.error(f"Failed to store job in DLQ: {e}")
            return False

    def get_queue_stats(self, queue_name: str | None = None) -> dict[str, Any]:
        """
        Get queue statistics.

        Args:
            queue_name: Queue name (None for all queues)

        Returns:
            dict: Queue statistics
        """
        inspect = self.app.control.inspect()

        # Get active tasks
        active = inspect.active()
        scheduled = inspect.scheduled()
        reserved = inspect.reserved()

        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "queues": {},
        }

        # Aggregate by queue
        for worker, tasks in (active or {}).items():
            for task in tasks:
                q = task.get("delivery_info", {}).get("routing_key", "default")
                if queue_name is None or q == queue_name:
                    if q not in stats["queues"]:
                        stats["queues"][q] = {
                            "active": 0,
                            "scheduled": 0,
                            "reserved": 0,
                        }
                    stats["queues"][q]["active"] += 1

        for worker, tasks in (scheduled or {}).items():
            for task in tasks:
                q = task.get("delivery_info", {}).get("routing_key", "default")
                if queue_name is None or q == queue_name:
                    if q not in stats["queues"]:
                        stats["queues"][q] = {
                            "active": 0,
                            "scheduled": 0,
                            "reserved": 0,
                        }
                    stats["queues"][q]["scheduled"] += 1

        for worker, tasks in (reserved or {}).items():
            for task in tasks:
                q = task.get("delivery_info", {}).get("routing_key", "default")
                if queue_name is None or q == queue_name:
                    if q not in stats["queues"]:
                        stats["queues"][q] = {
                            "active": 0,
                            "scheduled": 0,
                            "reserved": 0,
                        }
                    stats["queues"][q]["reserved"] += 1

        return stats

    def purge_queue(self, queue_name: str) -> int:
        """
        Purge all tasks from a queue.

        Warning: This operation cannot be undone.

        Args:
            queue_name: Queue to purge

        Returns:
            int: Number of tasks purged
        """
        count = self.app.control.purge()
        logger.warning(f"Purged queue {queue_name}: {count} tasks removed")
        return count
