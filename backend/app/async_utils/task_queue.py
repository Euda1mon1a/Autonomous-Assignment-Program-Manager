"""Background task queue optimization.

Provides optimized task queue management for Celery and async tasks.
"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class TaskPriority(int, Enum):
    """Task priority levels."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Task:
    """Task definition."""

    id: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority
    created_at: datetime
    retries: int = 0
    max_retries: int = 3


class TaskQueue:
    """Optimized async task queue with priority and retry handling."""

    def __init__(
        self,
        max_concurrent: int = 10,
        max_queue_size: int = 1000,
    ):
        """Initialize task queue.

        Args:
            max_concurrent: Maximum concurrent tasks
            max_queue_size: Maximum queue size
        """
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.queues: dict[TaskPriority, asyncio.PriorityQueue] = {
            priority: asyncio.PriorityQueue(maxsize=max_queue_size)
            for priority in TaskPriority
        }
        self.active_tasks: set[asyncio.Task] = set()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.stats = {
            "completed": 0,
            "failed": 0,
            "retried": 0,
            "total_time": 0.0,
        }
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None

    async def enqueue(
        self,
        func: Callable,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        task_id: Optional[str] = None,
        max_retries: int = 3,
        **kwargs,
    ) -> str:
        """Enqueue a task.

        Args:
            func: Async function to execute
            *args: Function arguments
            priority: Task priority
            task_id: Optional task ID
            max_retries: Maximum retry attempts
            **kwargs: Function keyword arguments

        Returns:
            Task ID
        """
        task_id = task_id or f"task_{datetime.utcnow().timestamp()}"

        task = Task(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            created_at=datetime.utcnow(),
            max_retries=max_retries,
        )

        # Add to appropriate priority queue
        queue = self.queues[priority]

        # Priority queue uses negative priority for proper ordering
        await queue.put((-priority.value, task))

        logger.debug(f"Enqueued task {task_id} with priority {priority.name}")
        return task_id

    async def start(self):
        """Start the task queue worker."""
        if self._running:
            logger.warning("Task queue already running")
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info(f"Task queue started (max_concurrent={self.max_concurrent})")

    async def stop(self):
        """Stop the task queue worker."""
        self._running = False

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        # Wait for active tasks to complete
        if self.active_tasks:
            logger.info(f"Waiting for {len(self.active_tasks)} active tasks to complete")
            await asyncio.gather(*self.active_tasks, return_exceptions=True)

        logger.info("Task queue stopped")

    async def _worker(self):
        """Worker loop to process tasks."""
        while self._running:
            try:
                # Try to get tasks from queues in priority order
                task = await self._get_next_task()

                if task:
                    # Execute task with concurrency limit
                    task_coroutine = self._execute_task(task)
                    task_obj = asyncio.create_task(task_coroutine)
                    self.active_tasks.add(task_obj)
                    task_obj.add_done_callback(self.active_tasks.discard)
                else:
                    # No tasks available, wait a bit
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                await asyncio.sleep(0.1)

    async def _get_next_task(self) -> Optional[Task]:
        """Get next task from queues (priority order).

        Returns:
            Next task or None if all queues empty
        """
        # Check queues in priority order
        for priority in sorted(TaskPriority, key=lambda p: p.value, reverse=True):
            queue = self.queues[priority]

            if not queue.empty():
                try:
                    _, task = queue.get_nowait()
                    return task
                except asyncio.QueueEmpty:
                    continue

        return None

    async def _execute_task(self, task: Task):
        """Execute a task with retry logic.

        Args:
            task: Task to execute
        """
        async with self.semaphore:
            start_time = datetime.utcnow()

            try:
                # Execute task
                result = await task.func(*task.args, **task.kwargs)

                # Track success
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                self.stats["completed"] += 1
                self.stats["total_time"] += execution_time

                logger.debug(
                    f"Task {task.id} completed in {execution_time:.2f}s"
                )

                return result

            except Exception as e:
                logger.error(f"Task {task.id} failed: {e}", exc_info=True)

                # Retry logic
                if task.retries < task.max_retries:
                    task.retries += 1
                    self.stats["retried"] += 1

                    # Re-enqueue with exponential backoff
                    await asyncio.sleep(2 ** task.retries)
                    queue = self.queues[task.priority]
                    await queue.put((-task.priority.value, task))

                    logger.info(
                        f"Task {task.id} retry {task.retries}/{task.max_retries}"
                    )
                else:
                    self.stats["failed"] += 1
                    logger.error(f"Task {task.id} failed permanently after {task.retries} retries")

    async def get_queue_sizes(self) -> dict[str, int]:
        """Get current queue sizes by priority.

        Returns:
            Dictionary of priority -> queue size
        """
        return {
            priority.name: queue.qsize()
            for priority, queue in self.queues.items()
        }

    async def get_stats(self) -> dict:
        """Get task queue statistics.

        Returns:
            Statistics dictionary
        """
        total_tasks = self.stats["completed"] + self.stats["failed"]
        avg_time = (
            self.stats["total_time"] / self.stats["completed"]
            if self.stats["completed"] > 0
            else 0.0
        )

        return {
            **self.stats,
            "active_tasks": len(self.active_tasks),
            "queue_sizes": await self.get_queue_sizes(),
            "total_tasks": total_tasks,
            "average_execution_time": round(avg_time, 3),
            "success_rate": (
                self.stats["completed"] / total_tasks * 100
                if total_tasks > 0
                else 0.0
            ),
        }


# Global task queue instance
_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """Get global task queue instance.

    Returns:
        TaskQueue singleton
    """
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue
