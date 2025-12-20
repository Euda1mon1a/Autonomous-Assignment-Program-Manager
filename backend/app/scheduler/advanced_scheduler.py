"""
Advanced Task Scheduler with enterprise features.

Extends the base JobScheduler with:
- Task priority queues
- Task dependencies (DAG-based)
- Distributed task locking
- Task retry with exponential backoff
- Advanced health monitoring
- Task execution metrics

This scheduler builds on top of APScheduler and integrates with the existing
job scheduler infrastructure while adding advanced enterprise features.
"""

import asyncio
import hashlib
import logging
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional
from uuid import UUID, uuid4

import redis
from croniter import croniter

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.scheduler.jobs import get_job_function
from app.scheduler.persistence import JobPersistence

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels for queue management."""

    CRITICAL = 0  # Highest priority - run immediately
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4  # Lowest priority - run when idle


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class RetryStrategy(Enum):
    """Retry strategy for failed tasks."""

    NONE = "none"  # No retry
    FIXED = "fixed"  # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"  # Linear backoff


@dataclass
class RetryConfig:
    """Configuration for task retry behavior."""

    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    max_attempts: int = 3
    initial_delay: int = 60  # seconds
    max_delay: int = 3600  # seconds
    backoff_multiplier: float = 2.0
    jitter: bool = True  # Add random jitter to prevent thundering herd


@dataclass
class TaskDependency:
    """Represents a dependency between tasks."""

    task_id: str
    dependency_type: str = "completion"  # completion, success, failure
    timeout: Optional[int] = None  # seconds to wait for dependency


@dataclass
class TaskExecution:
    """Represents a single task execution."""

    execution_id: UUID
    task_id: str
    task_name: str
    status: TaskStatus
    priority: TaskPriority
    scheduled_time: datetime
    started_time: Optional[datetime] = None
    completed_time: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    traceback_str: Optional[str] = None
    retry_count: int = 0
    lock_id: Optional[str] = None
    dependencies: list[TaskDependency] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDefinition:
    """Defines a task that can be scheduled."""

    task_id: str
    task_name: str
    func_path: str
    priority: TaskPriority = TaskPriority.NORMAL
    args: list[Any] = field(default_factory=list)
    kwargs: dict[str, Any] = field(default_factory=dict)
    retry_config: Optional[RetryConfig] = None
    dependencies: list[TaskDependency] = field(default_factory=list)
    require_lock: bool = False
    lock_timeout: int = 300  # seconds
    timeout: Optional[int] = None  # task execution timeout
    tags: list[str] = field(default_factory=list)


class DistributedTaskLock:
    """
    Distributed locking mechanism for tasks using Redis.

    Ensures only one instance of a task runs at a time across multiple workers.
    Uses Redis SET with NX (not exists) and EX (expiry) for atomic lock acquisition.
    """

    # Lua script for atomic lock release
    RELEASE_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize distributed lock.

        Args:
            redis_client: Optional Redis client. If not provided, creates from settings.
        """
        if redis_client is None:
            settings = get_settings()
            redis_url = settings.redis_url_with_password
            self.redis = redis.from_url(redis_url)
        else:
            self.redis = redis_client

        self._release_script = self.redis.register_script(self.RELEASE_SCRIPT)

    def acquire(
        self,
        task_id: str,
        timeout: int = 300,
        retry_delay: float = 0.5,
        max_wait: int = 30,
    ) -> Optional[str]:
        """
        Acquire a distributed lock for a task.

        Args:
            task_id: Unique task identifier
            timeout: Lock expiry timeout in seconds
            retry_delay: Delay between retry attempts
            max_wait: Maximum time to wait for lock acquisition

        Returns:
            Lock ID if acquired, None if timeout
        """
        lock_key = f"lock:task:{task_id}"
        lock_id = str(uuid4())

        start_time = time.time()
        while time.time() - start_time < max_wait:
            # Try to acquire lock atomically
            acquired = self.redis.set(
                lock_key,
                lock_id,
                nx=True,  # SET if Not eXists
                ex=timeout,  # EXpiry in seconds
            )

            if acquired:
                logger.debug(f"Acquired lock for task {task_id}")
                return lock_id

            # Lock held by another process, wait and retry
            time.sleep(retry_delay)

        logger.warning(f"Failed to acquire lock for task {task_id} within {max_wait}s")
        return None

    def release(self, task_id: str, lock_id: str) -> bool:
        """
        Release a distributed lock.

        Args:
            task_id: Task identifier
            lock_id: Lock ID returned by acquire()

        Returns:
            True if released, False if lock wasn't owned
        """
        lock_key = f"lock:task:{task_id}"

        try:
            # Use Lua script to atomically check ownership and delete
            result = self._release_script(keys=[lock_key], args=[lock_id])
            released = bool(result)

            if released:
                logger.debug(f"Released lock for task {task_id}")

            return released

        except redis.RedisError:
            return False

    def is_locked(self, task_id: str) -> bool:
        """
        Check if a task is currently locked.

        Args:
            task_id: Task identifier

        Returns:
            True if locked, False otherwise
        """
        lock_key = f"lock:task:{task_id}"
        try:
            return self.redis.exists(lock_key) > 0
        except redis.RedisError:
            return False

    def get_lock_ttl(self, task_id: str) -> Optional[int]:
        """
        Get remaining TTL for a task lock.

        Args:
            task_id: Task identifier

        Returns:
            Remaining seconds, or None if not locked
        """
        lock_key = f"lock:task:{task_id}"
        try:
            ttl = self.redis.ttl(lock_key)
            return ttl if ttl > 0 else None
        except redis.RedisError:
            return None


class TaskDependencyGraph:
    """
    Manages task dependencies using a Directed Acyclic Graph (DAG).

    Validates dependency relationships and determines task execution order.
    Detects circular dependencies and provides topological sorting.
    """

    def __init__(self):
        """Initialize empty dependency graph."""
        self.graph: dict[str, set[str]] = defaultdict(set)
        self.reverse_graph: dict[str, set[str]] = defaultdict(set)
        self.task_metadata: dict[str, dict[str, Any]] = {}

    def add_task(self, task_id: str, dependencies: list[TaskDependency]) -> None:
        """
        Add a task and its dependencies to the graph.

        Args:
            task_id: Task identifier
            dependencies: List of task dependencies

        Raises:
            ValueError: If adding the task would create a cycle
        """
        # Add task to graph
        if task_id not in self.graph:
            self.graph[task_id] = set()

        # Add dependencies
        for dep in dependencies:
            self.graph[task_id].add(dep.task_id)
            self.reverse_graph[dep.task_id].add(task_id)

            # Store dependency metadata
            if task_id not in self.task_metadata:
                self.task_metadata[task_id] = {}
            self.task_metadata[task_id][dep.task_id] = {
                "type": dep.dependency_type,
                "timeout": dep.timeout,
            }

        # Validate no cycles
        if self.has_cycle():
            # Rollback changes
            for dep in dependencies:
                self.graph[task_id].discard(dep.task_id)
                self.reverse_graph[dep.task_id].discard(task_id)
            raise ValueError(f"Adding task {task_id} would create a circular dependency")

    def remove_task(self, task_id: str) -> None:
        """
        Remove a task from the graph.

        Args:
            task_id: Task identifier
        """
        # Remove from graph
        if task_id in self.graph:
            # Remove reverse edges
            for dep_id in self.graph[task_id]:
                self.reverse_graph[dep_id].discard(task_id)
            del self.graph[task_id]

        # Remove reverse graph entry
        if task_id in self.reverse_graph:
            # Remove forward edges
            for dependent_id in self.reverse_graph[task_id]:
                self.graph[dependent_id].discard(task_id)
            del self.reverse_graph[task_id]

        # Remove metadata
        self.task_metadata.pop(task_id, None)

    def has_cycle(self) -> bool:
        """
        Check if the graph contains a cycle.

        Returns:
            True if cycle detected, False otherwise
        """
        visited = set()
        rec_stack = set()

        def visit(node: str) -> bool:
            if node in rec_stack:
                return True  # Cycle detected
            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.graph.get(node, set()):
                if visit(neighbor):
                    return True

            rec_stack.remove(node)
            return False

        for node in self.graph:
            if visit(node):
                return True

        return False

    def get_dependencies(self, task_id: str) -> set[str]:
        """
        Get direct dependencies for a task.

        Args:
            task_id: Task identifier

        Returns:
            Set of dependency task IDs
        """
        return self.graph.get(task_id, set()).copy()

    def get_dependents(self, task_id: str) -> set[str]:
        """
        Get tasks that depend on this task.

        Args:
            task_id: Task identifier

        Returns:
            Set of dependent task IDs
        """
        return self.reverse_graph.get(task_id, set()).copy()

    def topological_sort(self) -> list[str]:
        """
        Get topological ordering of tasks.

        Returns:
            List of task IDs in execution order

        Raises:
            ValueError: If graph contains a cycle
        """
        if self.has_cycle():
            raise ValueError("Cannot perform topological sort on graph with cycles")

        visited = set()
        result = []

        def visit(node: str) -> None:
            if node in visited:
                return

            visited.add(node)

            for neighbor in self.graph.get(node, set()):
                visit(neighbor)

            result.append(node)

        for node in self.graph:
            visit(node)

        return result[::-1]  # Reverse for correct order


class PriorityTaskQueue:
    """
    Priority-based task queue with support for multiple priority levels.

    Tasks are executed in priority order (CRITICAL > HIGH > NORMAL > LOW > BACKGROUND).
    Within the same priority level, tasks are executed FIFO.
    """

    def __init__(self):
        """Initialize priority queue."""
        self.queues: dict[TaskPriority, list[TaskExecution]] = {
            priority: [] for priority in TaskPriority
        }
        self.task_index: dict[str, TaskExecution] = {}

    def enqueue(self, task_execution: TaskExecution) -> None:
        """
        Add a task to the queue.

        Args:
            task_execution: Task execution to queue
        """
        priority = task_execution.priority
        self.queues[priority].append(task_execution)
        self.task_index[task_execution.task_id] = task_execution

        logger.debug(
            f"Enqueued task {task_execution.task_name} "
            f"with priority {priority.name}"
        )

    def dequeue(self) -> Optional[TaskExecution]:
        """
        Remove and return the highest priority task.

        Returns:
            TaskExecution or None if queue is empty
        """
        # Check queues in priority order
        for priority in TaskPriority:
            if self.queues[priority]:
                task = self.queues[priority].pop(0)
                self.task_index.pop(task.task_id, None)
                return task

        return None

    def peek(self) -> Optional[TaskExecution]:
        """
        Return the highest priority task without removing it.

        Returns:
            TaskExecution or None if queue is empty
        """
        for priority in TaskPriority:
            if self.queues[priority]:
                return self.queues[priority][0]

        return None

    def remove(self, task_id: str) -> bool:
        """
        Remove a specific task from the queue.

        Args:
            task_id: Task identifier

        Returns:
            True if removed, False if not found
        """
        if task_id not in self.task_index:
            return False

        task = self.task_index[task_id]
        priority = task.priority

        try:
            self.queues[priority].remove(task)
            del self.task_index[task_id]
            return True
        except ValueError:
            return False

    def size(self, priority: Optional[TaskPriority] = None) -> int:
        """
        Get queue size.

        Args:
            priority: Optional priority level to check

        Returns:
            Number of tasks in queue(s)
        """
        if priority:
            return len(self.queues[priority])

        return sum(len(q) for q in self.queues.values())

    def is_empty(self) -> bool:
        """
        Check if queue is empty.

        Returns:
            True if empty, False otherwise
        """
        return self.size() == 0

    def get_tasks_by_priority(self, priority: TaskPriority) -> list[TaskExecution]:
        """
        Get all tasks at a specific priority level.

        Args:
            priority: Priority level

        Returns:
            List of task executions
        """
        return self.queues[priority].copy()


class TaskRetryManager:
    """
    Manages task retry logic with configurable strategies.

    Supports exponential backoff, linear backoff, and fixed delay strategies
    with optional jitter to prevent thundering herd problems.
    """

    def __init__(self):
        """Initialize retry manager."""
        self.retry_history: dict[str, list[datetime]] = defaultdict(list)

    def should_retry(
        self,
        task_execution: TaskExecution,
        config: RetryConfig,
    ) -> bool:
        """
        Determine if a failed task should be retried.

        Args:
            task_execution: Failed task execution
            config: Retry configuration

        Returns:
            True if should retry, False otherwise
        """
        if config.strategy == RetryStrategy.NONE:
            return False

        return task_execution.retry_count < config.max_attempts

    def calculate_delay(
        self,
        task_execution: TaskExecution,
        config: RetryConfig,
    ) -> int:
        """
        Calculate delay before next retry attempt.

        Args:
            task_execution: Task execution
            config: Retry configuration

        Returns:
            Delay in seconds
        """
        attempt = task_execution.retry_count

        if config.strategy == RetryStrategy.FIXED:
            delay = config.initial_delay

        elif config.strategy == RetryStrategy.LINEAR:
            delay = config.initial_delay * (attempt + 1)

        elif config.strategy == RetryStrategy.EXPONENTIAL:
            delay = config.initial_delay * (config.backoff_multiplier ** attempt)

        else:
            delay = config.initial_delay

        # Apply max delay cap
        delay = min(delay, config.max_delay)

        # Add jitter if enabled (±20% random variation)
        if config.jitter:
            import random
            jitter_factor = random.uniform(0.8, 1.2)
            delay = int(delay * jitter_factor)

        return delay

    def record_retry(self, task_id: str) -> None:
        """
        Record a retry attempt.

        Args:
            task_id: Task identifier
        """
        self.retry_history[task_id].append(datetime.utcnow())

    def get_retry_count(self, task_id: str) -> int:
        """
        Get number of retries for a task.

        Args:
            task_id: Task identifier

        Returns:
            Number of retry attempts
        """
        return len(self.retry_history.get(task_id, []))

    def clear_history(self, task_id: str) -> None:
        """
        Clear retry history for a task.

        Args:
            task_id: Task identifier
        """
        self.retry_history.pop(task_id, None)


class SchedulerHealthMonitor:
    """
    Monitors scheduler health and performance metrics.

    Tracks task execution statistics, queue sizes, error rates,
    and provides health status reporting.
    """

    def __init__(self):
        """Initialize health monitor."""
        self.start_time = datetime.utcnow()
        self.metrics = {
            "tasks_executed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "tasks_retried": 0,
            "tasks_cancelled": 0,
            "total_execution_time": 0.0,
            "lock_acquisitions": 0,
            "lock_failures": 0,
        }
        self.error_log: list[dict[str, Any]] = []
        self.max_error_log_size = 100

    def record_execution(
        self,
        task_execution: TaskExecution,
        execution_time: float,
    ) -> None:
        """
        Record task execution metrics.

        Args:
            task_execution: Completed task execution
            execution_time: Execution time in seconds
        """
        self.metrics["tasks_executed"] += 1
        self.metrics["total_execution_time"] += execution_time

        if task_execution.status == TaskStatus.COMPLETED:
            self.metrics["tasks_succeeded"] += 1
        elif task_execution.status == TaskStatus.FAILED:
            self.metrics["tasks_failed"] += 1
            self._log_error(task_execution)
        elif task_execution.status == TaskStatus.RETRYING:
            self.metrics["tasks_retried"] += 1
        elif task_execution.status == TaskStatus.CANCELLED:
            self.metrics["tasks_cancelled"] += 1

    def record_lock_acquisition(self, success: bool) -> None:
        """
        Record lock acquisition attempt.

        Args:
            success: Whether lock was acquired
        """
        if success:
            self.metrics["lock_acquisitions"] += 1
        else:
            self.metrics["lock_failures"] += 1

    def _log_error(self, task_execution: TaskExecution) -> None:
        """
        Log task execution error.

        Args:
            task_execution: Failed task execution
        """
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task_execution.task_id,
            "task_name": task_execution.task_name,
            "error": task_execution.error,
            "retry_count": task_execution.retry_count,
        }

        self.error_log.append(error_entry)

        # Trim log if too large
        if len(self.error_log) > self.max_error_log_size:
            self.error_log = self.error_log[-self.max_error_log_size:]

    def get_health_status(self) -> dict[str, Any]:
        """
        Get current health status.

        Returns:
            Dictionary with health metrics
        """
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        total_tasks = self.metrics["tasks_executed"]
        success_rate = (
            self.metrics["tasks_succeeded"] / total_tasks * 100
            if total_tasks > 0 else 0
        )

        avg_execution_time = (
            self.metrics["total_execution_time"] / total_tasks
            if total_tasks > 0 else 0
        )

        lock_success_rate = (
            self.metrics["lock_acquisitions"] /
            (self.metrics["lock_acquisitions"] + self.metrics["lock_failures"]) * 100
            if self.metrics["lock_acquisitions"] + self.metrics["lock_failures"] > 0
            else 0
        )

        return {
            "status": "healthy" if success_rate >= 90 else "degraded",
            "uptime_seconds": uptime,
            "metrics": self.metrics.copy(),
            "success_rate": round(success_rate, 2),
            "average_execution_time": round(avg_execution_time, 2),
            "lock_success_rate": round(lock_success_rate, 2),
            "recent_errors": self.error_log[-10:],  # Last 10 errors
        }

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.start_time = datetime.utcnow()
        self.metrics = {k: 0 if isinstance(v, int) else 0.0 for k, v in self.metrics.items()}
        self.error_log = []


class AdvancedTaskScheduler:
    """
    Advanced task scheduler with enterprise features.

    Features:
    - Priority-based task queues
    - Task dependency management (DAG)
    - Distributed locking for task exclusivity
    - Retry with exponential backoff
    - Health monitoring and metrics
    - Cron expression parsing
    - One-time and recurring task scheduling
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        max_concurrent_tasks: int = 10,
    ):
        """
        Initialize advanced scheduler.

        Args:
            redis_client: Optional Redis client for distributed locking
            max_concurrent_tasks: Maximum number of tasks to run concurrently
        """
        self.task_queue = PriorityTaskQueue()
        self.dependency_graph = TaskDependencyGraph()
        self.lock_manager = DistributedTaskLock(redis_client)
        self.retry_manager = TaskRetryManager()
        self.health_monitor = SchedulerHealthMonitor()

        self.max_concurrent_tasks = max_concurrent_tasks
        self.running_tasks: dict[str, TaskExecution] = {}
        self.task_definitions: dict[str, TaskDefinition] = {}
        self.task_history: list[TaskExecution] = []

        self._running = False
        self._executor_task: Optional[asyncio.Task] = None

    def register_task(self, task_def: TaskDefinition) -> None:
        """
        Register a task definition.

        Args:
            task_def: Task definition

        Raises:
            ValueError: If task ID already registered or dependencies create cycle
        """
        if task_def.task_id in self.task_definitions:
            raise ValueError(f"Task {task_def.task_id} already registered")

        # Add to dependency graph
        self.dependency_graph.add_task(task_def.task_id, task_def.dependencies)

        # Store definition
        self.task_definitions[task_def.task_id] = task_def

        logger.info(f"Registered task: {task_def.task_name} ({task_def.task_id})")

    def unregister_task(self, task_id: str) -> bool:
        """
        Unregister a task definition.

        Args:
            task_id: Task identifier

        Returns:
            True if unregistered, False if not found
        """
        if task_id not in self.task_definitions:
            return False

        # Remove from dependency graph
        self.dependency_graph.remove_task(task_id)

        # Remove definition
        del self.task_definitions[task_id]

        logger.info(f"Unregistered task: {task_id}")
        return True

    def schedule_task(
        self,
        task_id: str,
        scheduled_time: Optional[datetime] = None,
        **kwargs,
    ) -> UUID:
        """
        Schedule a task for execution.

        Args:
            task_id: Task identifier
            scheduled_time: When to run the task (default: now)
            **kwargs: Override task kwargs

        Returns:
            Execution ID

        Raises:
            ValueError: If task not registered or dependencies not met
        """
        if task_id not in self.task_definitions:
            raise ValueError(f"Task {task_id} not registered")

        task_def = self.task_definitions[task_id]

        # Create execution
        execution = TaskExecution(
            execution_id=uuid4(),
            task_id=task_id,
            task_name=task_def.task_name,
            status=TaskStatus.PENDING,
            priority=task_def.priority,
            scheduled_time=scheduled_time or datetime.utcnow(),
            dependencies=task_def.dependencies.copy(),
        )

        # Add to queue
        self.task_queue.enqueue(execution)

        logger.info(
            f"Scheduled task {task_def.task_name} "
            f"(execution_id={execution.execution_id})"
        )

        return execution.execution_id

    def schedule_cron_task(
        self,
        task_id: str,
        cron_expression: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[UUID]:
        """
        Schedule task using cron expression.

        Args:
            task_id: Task identifier
            cron_expression: Cron expression (e.g., "0 */6 * * *")
            start_time: Start of scheduling window
            end_time: End of scheduling window

        Returns:
            List of scheduled execution IDs

        Raises:
            ValueError: If cron expression is invalid
        """
        if task_id not in self.task_definitions:
            raise ValueError(f"Task {task_id} not registered")

        try:
            cron = croniter(cron_expression, start_time or datetime.utcnow())
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {e}")

        # Schedule next occurrence
        next_run = cron.get_next(datetime)

        if end_time and next_run > end_time:
            return []

        execution_id = self.schedule_task(task_id, scheduled_time=next_run)

        logger.info(
            f"Scheduled cron task {task_id} "
            f"(cron={cron_expression}, next_run={next_run})"
        )

        return [execution_id]

    def cancel_task(self, execution_id: UUID) -> bool:
        """
        Cancel a pending or running task.

        Args:
            execution_id: Execution identifier

        Returns:
            True if cancelled, False if not found or already completed
        """
        # Check if in queue
        task_id_to_remove = None
        for task_id, execution in self.task_queue.task_index.items():
            if execution.execution_id == execution_id:
                task_id_to_remove = task_id
                break

        if task_id_to_remove:
            self.task_queue.remove(task_id_to_remove)
            logger.info(f"Cancelled queued task {execution_id}")
            return True

        # Check if running
        for task_id, execution in self.running_tasks.items():
            if execution.execution_id == execution_id:
                execution.status = TaskStatus.CANCELLED
                logger.warning(f"Marked running task {execution_id} for cancellation")
                return True

        return False

    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._executor_task = asyncio.create_task(self._executor_loop())

        logger.info("Advanced task scheduler started")

    async def stop(self, wait: bool = True) -> None:
        """
        Stop the scheduler.

        Args:
            wait: Wait for running tasks to complete
        """
        if not self._running:
            return

        self._running = False

        if self._executor_task and wait:
            await self._executor_task

        logger.info("Advanced task scheduler stopped")

    async def _executor_loop(self) -> None:
        """
        Main executor loop.

        Continuously processes tasks from the queue.
        """
        while self._running:
            try:
                # Check if we can run more tasks
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.1)
                    continue

                # Get next task
                task_execution = self.task_queue.dequeue()

                if not task_execution:
                    await asyncio.sleep(0.1)
                    continue

                # Check if scheduled time has arrived
                if task_execution.scheduled_time > datetime.utcnow():
                    # Re-queue for later
                    self.task_queue.enqueue(task_execution)
                    await asyncio.sleep(1)
                    continue

                # Check dependencies
                if not self._check_dependencies(task_execution):
                    # Re-queue and wait for dependencies
                    self.task_queue.enqueue(task_execution)
                    await asyncio.sleep(1)
                    continue

                # Execute task
                asyncio.create_task(self._execute_task(task_execution))

            except Exception as e:
                logger.error(f"Error in executor loop: {e}", exc_info=True)
                await asyncio.sleep(1)

    def _check_dependencies(self, task_execution: TaskExecution) -> bool:
        """
        Check if task dependencies are satisfied.

        Args:
            task_execution: Task execution to check

        Returns:
            True if dependencies satisfied, False otherwise
        """
        if not task_execution.dependencies:
            return True

        # Check each dependency
        for dep in task_execution.dependencies:
            # Find dependency in history
            dep_execution = None
            for execution in self.task_history:
                if execution.task_id == dep.task_id:
                    dep_execution = execution
                    break

            if not dep_execution:
                return False  # Dependency not executed yet

            # Check dependency type
            if dep.dependency_type == "completion":
                if dep_execution.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    return False
            elif dep.dependency_type == "success":
                if dep_execution.status != TaskStatus.COMPLETED:
                    return False
            elif dep.dependency_type == "failure":
                if dep_execution.status != TaskStatus.FAILED:
                    return False

        return True

    async def _execute_task(self, task_execution: TaskExecution) -> None:
        """
        Execute a single task.

        Args:
            task_execution: Task to execute
        """
        task_def = self.task_definitions[task_execution.task_id]
        start_time = time.time()
        lock_id = None

        try:
            # Update status
            task_execution.status = TaskStatus.RUNNING
            task_execution.started_time = datetime.utcnow()
            self.running_tasks[task_execution.task_id] = task_execution

            # Acquire lock if required
            if task_def.require_lock:
                lock_id = self.lock_manager.acquire(
                    task_execution.task_id,
                    timeout=task_def.lock_timeout,
                )

                if not lock_id:
                    raise Exception(f"Failed to acquire lock for task {task_execution.task_id}")

                task_execution.lock_id = lock_id
                self.health_monitor.record_lock_acquisition(True)

            # Get function to execute
            func = get_job_function(task_def.func_path)

            # Execute with timeout if configured
            if task_def.timeout:
                result = await asyncio.wait_for(
                    asyncio.to_thread(func, *task_def.args, **task_def.kwargs),
                    timeout=task_def.timeout,
                )
            else:
                result = await asyncio.to_thread(func, *task_def.args, **task_def.kwargs)

            # Record success
            task_execution.status = TaskStatus.COMPLETED
            task_execution.result = result
            task_execution.completed_time = datetime.utcnow()

            logger.info(f"Task {task_execution.task_name} completed successfully")

        except Exception as e:
            # Record failure
            task_execution.status = TaskStatus.FAILED
            task_execution.error = str(e)
            task_execution.traceback_str = traceback.format_exc()
            task_execution.completed_time = datetime.utcnow()

            logger.error(
                f"Task {task_execution.task_name} failed: {e}",
                exc_info=True,
            )

            # Check if should retry
            if task_def.retry_config and self.retry_manager.should_retry(
                task_execution, task_def.retry_config
            ):
                delay = self.retry_manager.calculate_delay(
                    task_execution, task_def.retry_config
                )

                task_execution.status = TaskStatus.RETRYING
                task_execution.retry_count += 1

                # Schedule retry
                retry_time = datetime.utcnow() + timedelta(seconds=delay)
                retry_execution = TaskExecution(
                    execution_id=uuid4(),
                    task_id=task_execution.task_id,
                    task_name=task_execution.task_name,
                    status=TaskStatus.PENDING,
                    priority=task_execution.priority,
                    scheduled_time=retry_time,
                    dependencies=task_execution.dependencies,
                    retry_count=task_execution.retry_count,
                )

                self.task_queue.enqueue(retry_execution)
                self.retry_manager.record_retry(task_execution.task_id)

                logger.info(
                    f"Scheduled retry #{task_execution.retry_count} "
                    f"for task {task_execution.task_name} in {delay}s"
                )

        finally:
            # Release lock
            if lock_id:
                self.lock_manager.release(task_execution.task_id, lock_id)

            # Record metrics
            execution_time = time.time() - start_time
            task_execution.metrics["execution_time"] = execution_time
            self.health_monitor.record_execution(task_execution, execution_time)

            # Move to history
            self.running_tasks.pop(task_execution.task_id, None)
            self.task_history.append(task_execution)

            # Trim history if too large
            if len(self.task_history) > 1000:
                self.task_history = self.task_history[-1000:]

    def get_health_status(self) -> dict[str, Any]:
        """
        Get scheduler health status.

        Returns:
            Health status dictionary
        """
        health = self.health_monitor.get_health_status()

        # Add queue statistics
        health["queue_stats"] = {
            "total_queued": self.task_queue.size(),
            "by_priority": {
                priority.name: self.task_queue.size(priority)
                for priority in TaskPriority
            },
        }

        # Add running task count
        health["running_tasks"] = len(self.running_tasks)
        health["max_concurrent_tasks"] = self.max_concurrent_tasks

        return health

    def get_task_status(self, execution_id: UUID) -> Optional[dict[str, Any]]:
        """
        Get status of a specific task execution.

        Args:
            execution_id: Execution identifier

        Returns:
            Task status dictionary or None if not found
        """
        # Check running tasks
        for execution in self.running_tasks.values():
            if execution.execution_id == execution_id:
                return self._execution_to_dict(execution)

        # Check history
        for execution in self.task_history:
            if execution.execution_id == execution_id:
                return self._execution_to_dict(execution)

        # Check queue
        for execution in self.task_queue.task_index.values():
            if execution.execution_id == execution_id:
                return self._execution_to_dict(execution)

        return None

    def _execution_to_dict(self, execution: TaskExecution) -> dict[str, Any]:
        """
        Convert task execution to dictionary.

        Args:
            execution: Task execution

        Returns:
            Dictionary representation
        """
        return {
            "execution_id": str(execution.execution_id),
            "task_id": execution.task_id,
            "task_name": execution.task_name,
            "status": execution.status.value,
            "priority": execution.priority.name,
            "scheduled_time": execution.scheduled_time.isoformat(),
            "started_time": execution.started_time.isoformat() if execution.started_time else None,
            "completed_time": execution.completed_time.isoformat() if execution.completed_time else None,
            "retry_count": execution.retry_count,
            "error": execution.error,
            "metrics": execution.metrics,
        }


# Global scheduler instance
_advanced_scheduler: Optional[AdvancedTaskScheduler] = None


def get_advanced_scheduler() -> AdvancedTaskScheduler:
    """
    Get the global advanced scheduler instance.

    Returns:
        AdvancedTaskScheduler instance
    """
    global _advanced_scheduler

    if _advanced_scheduler is None:
        _advanced_scheduler = AdvancedTaskScheduler()

    return _advanced_scheduler
