"""
Tests for Advanced Task Scheduler.

Tests all advanced features including:
- Priority queue management
- Task dependency resolution
- Distributed locking
- Retry with backoff
- Health monitoring
- Cron expression parsing
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest
import redis

from app.scheduler.advanced_scheduler import (
    AdvancedTaskScheduler,
    DistributedTaskLock,
    PriorityTaskQueue,
    RetryConfig,
    RetryStrategy,
    SchedulerHealthMonitor,
    TaskDefinition,
    TaskDependency,
    TaskDependencyGraph,
    TaskExecution,
    TaskPriority,
    TaskRetryManager,
    TaskStatus,
)


class TestPriorityTaskQueue:
    """Test suite for priority task queue."""

    def test_enqueue_and_dequeue(self):
        """Test basic enqueue and dequeue operations."""
        queue = PriorityTaskQueue()

        # Create test tasks with different priorities
        task_low = TaskExecution(
            execution_id=uuid4(),
            task_id="task_low",
            task_name="Low Priority Task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.LOW,
            scheduled_time=datetime.utcnow(),
        )

        task_high = TaskExecution(
            execution_id=uuid4(),
            task_id="task_high",
            task_name="High Priority Task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            scheduled_time=datetime.utcnow(),
        )

        task_critical = TaskExecution(
            execution_id=uuid4(),
            task_id="task_critical",
            task_name="Critical Task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.CRITICAL,
            scheduled_time=datetime.utcnow(),
        )

        # Enqueue in non-priority order
        queue.enqueue(task_low)
        queue.enqueue(task_high)
        queue.enqueue(task_critical)

        # Dequeue should return in priority order
        assert queue.dequeue().task_id == "task_critical"
        assert queue.dequeue().task_id == "task_high"
        assert queue.dequeue().task_id == "task_low"
        assert queue.dequeue() is None

    def test_queue_size(self):
        """Test queue size tracking."""
        queue = PriorityTaskQueue()

        assert queue.size() == 0
        assert queue.is_empty()

        task = TaskExecution(
            execution_id=uuid4(),
            task_id="task1",
            task_name="Test Task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.NORMAL,
            scheduled_time=datetime.utcnow(),
        )

        queue.enqueue(task)

        assert queue.size() == 1
        assert not queue.is_empty()
        assert queue.size(TaskPriority.NORMAL) == 1
        assert queue.size(TaskPriority.HIGH) == 0

    def test_remove_task(self):
        """Test removing a specific task from queue."""
        queue = PriorityTaskQueue()

        task1 = TaskExecution(
            execution_id=uuid4(),
            task_id="task1",
            task_name="Task 1",
            status=TaskStatus.PENDING,
            priority=TaskPriority.NORMAL,
            scheduled_time=datetime.utcnow(),
        )

        task2 = TaskExecution(
            execution_id=uuid4(),
            task_id="task2",
            task_name="Task 2",
            status=TaskStatus.PENDING,
            priority=TaskPriority.NORMAL,
            scheduled_time=datetime.utcnow(),
        )

        queue.enqueue(task1)
        queue.enqueue(task2)

        assert queue.size() == 2
        assert queue.remove("task1")
        assert queue.size() == 1
        assert queue.dequeue().task_id == "task2"

    def test_peek(self):
        """Test peeking at next task without removing it."""
        queue = PriorityTaskQueue()

        task = TaskExecution(
            execution_id=uuid4(),
            task_id="task1",
            task_name="Test Task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.NORMAL,
            scheduled_time=datetime.utcnow(),
        )

        queue.enqueue(task)

        peeked = queue.peek()
        assert peeked is not None
        assert peeked.task_id == "task1"
        assert queue.size() == 1  # Still in queue


class TestTaskDependencyGraph:
    """Test suite for task dependency graph."""

    def test_add_task_without_dependencies(self):
        """Test adding a task with no dependencies."""
        graph = TaskDependencyGraph()

        graph.add_task("task1", [])

        assert "task1" in graph.graph
        assert len(graph.get_dependencies("task1")) == 0

    def test_add_task_with_dependencies(self):
        """Test adding tasks with dependencies."""
        graph = TaskDependencyGraph()

        # Add task1 with no dependencies
        graph.add_task("task1", [])

        # Add task2 that depends on task1
        dep = TaskDependency(task_id="task1", dependency_type="completion")
        graph.add_task("task2", [dep])

        assert "task2" in graph.graph
        assert "task1" in graph.get_dependencies("task2")
        assert "task2" in graph.get_dependents("task1")

    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        graph = TaskDependencyGraph()

        graph.add_task("task1", [])
        graph.add_task("task2", [TaskDependency(task_id="task1")])

        # Try to add task1 depending on task2 (creates cycle)
        with pytest.raises(ValueError, match="circular dependency"):
            graph.add_task("task3", [
                TaskDependency(task_id="task2"),
                TaskDependency(task_id="task3"),  # Self-cycle
            ])

    def test_topological_sort(self):
        """Test topological sorting of tasks."""
        graph = TaskDependencyGraph()

        # Create a simple DAG: task1 -> task2 -> task3
        graph.add_task("task1", [])
        graph.add_task("task2", [TaskDependency(task_id="task1")])
        graph.add_task("task3", [TaskDependency(task_id="task2")])

        sorted_tasks = graph.topological_sort()

        # task1 should come before task2, task2 before task3
        assert sorted_tasks.index("task1") < sorted_tasks.index("task2")
        assert sorted_tasks.index("task2") < sorted_tasks.index("task3")

    def test_remove_task(self):
        """Test removing a task from the graph."""
        graph = TaskDependencyGraph()

        graph.add_task("task1", [])
        graph.add_task("task2", [TaskDependency(task_id="task1")])

        graph.remove_task("task1")

        assert "task1" not in graph.graph
        assert "task1" not in graph.get_dependencies("task2")


class TestDistributedTaskLock:
    """Test suite for distributed task locking."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        mock = MagicMock(spec=redis.Redis)
        return mock

    def test_acquire_lock_success(self, mock_redis):
        """Test successful lock acquisition."""
        mock_redis.set.return_value = True

        lock = DistributedTaskLock(mock_redis)
        lock_id = lock.acquire("task1", timeout=300, max_wait=5)

        assert lock_id is not None
        mock_redis.set.assert_called_once()

    def test_acquire_lock_timeout(self, mock_redis):
        """Test lock acquisition timeout."""
        mock_redis.set.return_value = False

        lock = DistributedTaskLock(mock_redis)
        lock_id = lock.acquire("task1", timeout=300, max_wait=1)

        assert lock_id is None

    def test_release_lock_success(self, mock_redis):
        """Test successful lock release."""
        # Mock the Lua script
        mock_script = MagicMock()
        mock_script.return_value = 1
        mock_redis.register_script.return_value = mock_script

        lock = DistributedTaskLock(mock_redis)
        released = lock.release("task1", "lock123")

        assert released
        mock_script.assert_called_once()

    def test_is_locked(self, mock_redis):
        """Test checking if task is locked."""
        mock_redis.exists.return_value = 1

        lock = DistributedTaskLock(mock_redis)
        assert lock.is_locked("task1")

        mock_redis.exists.return_value = 0
        assert not lock.is_locked("task1")

    def test_get_lock_ttl(self, mock_redis):
        """Test getting lock TTL."""
        mock_redis.ttl.return_value = 120

        lock = DistributedTaskLock(mock_redis)
        ttl = lock.get_lock_ttl("task1")

        assert ttl == 120

        mock_redis.ttl.return_value = -1
        assert lock.get_lock_ttl("task1") is None


class TestTaskRetryManager:
    """Test suite for task retry management."""

    def test_should_retry_none_strategy(self):
        """Test that NONE strategy prevents retries."""
        manager = TaskRetryManager()
        config = RetryConfig(strategy=RetryStrategy.NONE, max_attempts=3)

        execution = TaskExecution(
            execution_id=uuid4(),
            task_id="task1",
            task_name="Test Task",
            status=TaskStatus.FAILED,
            priority=TaskPriority.NORMAL,
            scheduled_time=datetime.utcnow(),
            retry_count=0,
        )

        assert not manager.should_retry(execution, config)

    def test_should_retry_max_attempts(self):
        """Test that retries stop after max attempts."""
        manager = TaskRetryManager()
        config = RetryConfig(strategy=RetryStrategy.EXPONENTIAL, max_attempts=3)

        execution = TaskExecution(
            execution_id=uuid4(),
            task_id="task1",
            task_name="Test Task",
            status=TaskStatus.FAILED,
            priority=TaskPriority.NORMAL,
            scheduled_time=datetime.utcnow(),
            retry_count=3,
        )

        assert not manager.should_retry(execution, config)

        execution.retry_count = 2
        assert manager.should_retry(execution, config)

    def test_calculate_delay_fixed(self):
        """Test fixed delay calculation."""
        manager = TaskRetryManager()
        config = RetryConfig(
            strategy=RetryStrategy.FIXED,
            initial_delay=60,
            jitter=False,
        )

        execution = TaskExecution(
            execution_id=uuid4(),
            task_id="task1",
            task_name="Test Task",
            status=TaskStatus.FAILED,
            priority=TaskPriority.NORMAL,
            scheduled_time=datetime.utcnow(),
            retry_count=0,
        )

        delay = manager.calculate_delay(execution, config)
        assert delay == 60

        execution.retry_count = 5
        delay = manager.calculate_delay(execution, config)
        assert delay == 60  # Fixed delay

    def test_calculate_delay_exponential(self):
        """Test exponential backoff calculation."""
        manager = TaskRetryManager()
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            initial_delay=10,
            backoff_multiplier=2.0,
            max_delay=1000,
            jitter=False,
        )

        execution = TaskExecution(
            execution_id=uuid4(),
            task_id="task1",
            task_name="Test Task",
            status=TaskStatus.FAILED,
            priority=TaskPriority.NORMAL,
            scheduled_time=datetime.utcnow(),
            retry_count=0,
        )

        # First retry: 10 * 2^0 = 10
        delay = manager.calculate_delay(execution, config)
        assert delay == 10

        # Second retry: 10 * 2^1 = 20
        execution.retry_count = 1
        delay = manager.calculate_delay(execution, config)
        assert delay == 20

        # Third retry: 10 * 2^2 = 40
        execution.retry_count = 2
        delay = manager.calculate_delay(execution, config)
        assert delay == 40

    def test_calculate_delay_linear(self):
        """Test linear backoff calculation."""
        manager = TaskRetryManager()
        config = RetryConfig(
            strategy=RetryStrategy.LINEAR,
            initial_delay=30,
            jitter=False,
        )

        execution = TaskExecution(
            execution_id=uuid4(),
            task_id="task1",
            task_name="Test Task",
            status=TaskStatus.FAILED,
            priority=TaskPriority.NORMAL,
            scheduled_time=datetime.utcnow(),
            retry_count=0,
        )

        # First retry: 30 * 1 = 30
        delay = manager.calculate_delay(execution, config)
        assert delay == 30

        # Second retry: 30 * 2 = 60
        execution.retry_count = 1
        delay = manager.calculate_delay(execution, config)
        assert delay == 60

    def test_record_retry(self):
        """Test recording retry attempts."""
        manager = TaskRetryManager()

        manager.record_retry("task1")
        assert manager.get_retry_count("task1") == 1

        manager.record_retry("task1")
        assert manager.get_retry_count("task1") == 2

        manager.clear_history("task1")
        assert manager.get_retry_count("task1") == 0


class TestSchedulerHealthMonitor:
    """Test suite for scheduler health monitoring."""

    def test_record_execution_success(self):
        """Test recording successful execution."""
        monitor = SchedulerHealthMonitor()

        execution = TaskExecution(
            execution_id=uuid4(),
            task_id="task1",
            task_name="Test Task",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.NORMAL,
            scheduled_time=datetime.utcnow(),
        )

        monitor.record_execution(execution, execution_time=2.5)

        assert monitor.metrics["tasks_executed"] == 1
        assert monitor.metrics["tasks_succeeded"] == 1
        assert monitor.metrics["total_execution_time"] == 2.5

    def test_record_execution_failure(self):
        """Test recording failed execution."""
        monitor = SchedulerHealthMonitor()

        execution = TaskExecution(
            execution_id=uuid4(),
            task_id="task1",
            task_name="Test Task",
            status=TaskStatus.FAILED,
            priority=TaskPriority.NORMAL,
            scheduled_time=datetime.utcnow(),
            error="Test error",
        )

        monitor.record_execution(execution, execution_time=1.0)

        assert monitor.metrics["tasks_executed"] == 1
        assert monitor.metrics["tasks_failed"] == 1
        assert len(monitor.error_log) == 1

    def test_record_lock_acquisition(self):
        """Test recording lock acquisitions."""
        monitor = SchedulerHealthMonitor()

        monitor.record_lock_acquisition(True)
        monitor.record_lock_acquisition(True)
        monitor.record_lock_acquisition(False)

        assert monitor.metrics["lock_acquisitions"] == 2
        assert monitor.metrics["lock_failures"] == 1

    def test_get_health_status(self):
        """Test getting health status."""
        monitor = SchedulerHealthMonitor()

        # Record some executions
        for i in range(10):
            execution = TaskExecution(
                execution_id=uuid4(),
                task_id=f"task{i}",
                task_name=f"Task {i}",
                status=TaskStatus.COMPLETED if i < 9 else TaskStatus.FAILED,
                priority=TaskPriority.NORMAL,
                scheduled_time=datetime.utcnow(),
            )
            monitor.record_execution(execution, execution_time=1.0)

        health = monitor.get_health_status()

        assert health["status"] in ["healthy", "degraded"]
        assert health["metrics"]["tasks_executed"] == 10
        assert health["metrics"]["tasks_succeeded"] == 9
        assert health["metrics"]["tasks_failed"] == 1
        assert health["success_rate"] == 90.0

    def test_reset_metrics(self):
        """Test resetting metrics."""
        monitor = SchedulerHealthMonitor()

        execution = TaskExecution(
            execution_id=uuid4(),
            task_id="task1",
            task_name="Test Task",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.NORMAL,
            scheduled_time=datetime.utcnow(),
        )

        monitor.record_execution(execution, execution_time=1.0)
        assert monitor.metrics["tasks_executed"] == 1

        monitor.reset_metrics()
        assert monitor.metrics["tasks_executed"] == 0
        assert len(monitor.error_log) == 0


class TestAdvancedTaskScheduler:
    """Test suite for advanced task scheduler."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        mock = MagicMock(spec=redis.Redis)
        mock.set.return_value = True
        return mock

    @pytest.fixture
    def scheduler(self, mock_redis):
        """Create scheduler instance with mock Redis."""
        return AdvancedTaskScheduler(redis_client=mock_redis, max_concurrent_tasks=5)

    def test_register_task(self, scheduler):
        """Test registering a task definition."""
        task_def = TaskDefinition(
            task_id="task1",
            task_name="Test Task",
            func_path="app.scheduler.jobs.heartbeat_job",
            priority=TaskPriority.NORMAL,
        )

        scheduler.register_task(task_def)

        assert "task1" in scheduler.task_definitions
        assert scheduler.task_definitions["task1"] == task_def

    def test_register_duplicate_task(self, scheduler):
        """Test registering duplicate task raises error."""
        task_def = TaskDefinition(
            task_id="task1",
            task_name="Test Task",
            func_path="app.scheduler.jobs.heartbeat_job",
        )

        scheduler.register_task(task_def)

        with pytest.raises(ValueError, match="already registered"):
            scheduler.register_task(task_def)

    def test_unregister_task(self, scheduler):
        """Test unregistering a task."""
        task_def = TaskDefinition(
            task_id="task1",
            task_name="Test Task",
            func_path="app.scheduler.jobs.heartbeat_job",
        )

        scheduler.register_task(task_def)
        assert scheduler.unregister_task("task1")
        assert "task1" not in scheduler.task_definitions

    def test_schedule_task(self, scheduler):
        """Test scheduling a task for execution."""
        task_def = TaskDefinition(
            task_id="task1",
            task_name="Test Task",
            func_path="app.scheduler.jobs.heartbeat_job",
            priority=TaskPriority.HIGH,
        )

        scheduler.register_task(task_def)

        execution_id = scheduler.schedule_task("task1")

        assert execution_id is not None
        assert scheduler.task_queue.size() == 1

        # Verify priority
        queued_task = scheduler.task_queue.peek()
        assert queued_task.priority == TaskPriority.HIGH

    def test_schedule_task_not_registered(self, scheduler):
        """Test scheduling unregistered task raises error."""
        with pytest.raises(ValueError, match="not registered"):
            scheduler.schedule_task("nonexistent")

    def test_cancel_queued_task(self, scheduler):
        """Test cancelling a queued task."""
        task_def = TaskDefinition(
            task_id="task1",
            task_name="Test Task",
            func_path="app.scheduler.jobs.heartbeat_job",
        )

        scheduler.register_task(task_def)
        execution_id = scheduler.schedule_task("task1")

        assert scheduler.cancel_task(execution_id)
        assert scheduler.task_queue.is_empty()

    def test_get_health_status(self, scheduler):
        """Test getting scheduler health status."""
        health = scheduler.get_health_status()

        assert "status" in health
        assert "queue_stats" in health
        assert "running_tasks" in health
        assert health["running_tasks"] == 0
        assert health["max_concurrent_tasks"] == 5

    @pytest.mark.asyncio
    async def test_schedule_cron_task(self, scheduler):
        """Test scheduling task with cron expression."""
        task_def = TaskDefinition(
            task_id="task1",
            task_name="Test Task",
            func_path="app.scheduler.jobs.heartbeat_job",
        )

        scheduler.register_task(task_def)

        # Schedule to run every hour
        execution_ids = scheduler.schedule_cron_task(
            "task1",
            cron_expression="0 */1 * * *",
        )

        assert len(execution_ids) > 0
        assert scheduler.task_queue.size() > 0

    def test_schedule_cron_task_invalid_expression(self, scheduler):
        """Test scheduling with invalid cron expression."""
        task_def = TaskDefinition(
            task_id="task1",
            task_name="Test Task",
            func_path="app.scheduler.jobs.heartbeat_job",
        )

        scheduler.register_task(task_def)

        with pytest.raises(ValueError, match="Invalid cron expression"):
            scheduler.schedule_cron_task("task1", cron_expression="invalid cron")

    def test_get_task_status_queued(self, scheduler):
        """Test getting status of queued task."""
        task_def = TaskDefinition(
            task_id="task1",
            task_name="Test Task",
            func_path="app.scheduler.jobs.heartbeat_job",
        )

        scheduler.register_task(task_def)
        execution_id = scheduler.schedule_task("task1")

        status = scheduler.get_task_status(execution_id)

        assert status is not None
        assert status["execution_id"] == str(execution_id)
        assert status["task_id"] == "task1"
        assert status["status"] == TaskStatus.PENDING.value

    def test_get_task_status_not_found(self, scheduler):
        """Test getting status of nonexistent task."""
        status = scheduler.get_task_status(uuid4())
        assert status is None


@pytest.mark.asyncio
class TestAdvancedTaskSchedulerAsync:
    """Async tests for task scheduler execution."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        mock = MagicMock(spec=redis.Redis)
        mock.set.return_value = True
        mock_script = MagicMock()
        mock_script.return_value = 1
        mock.register_script.return_value = mock_script
        return mock

    @pytest.fixture
    def scheduler(self, mock_redis):
        """Create scheduler instance."""
        return AdvancedTaskScheduler(redis_client=mock_redis, max_concurrent_tasks=5)

    async def test_task_execution_flow(self, scheduler):
        """Test complete task execution flow."""

        # Define a simple test task
        def test_task():
            return {"result": "success"}

        # Mock the get_job_function to return our test task
        with patch("app.scheduler.advanced_scheduler.get_job_function") as mock_get_func:
            mock_get_func.return_value = test_task

            task_def = TaskDefinition(
                task_id="task1",
                task_name="Test Task",
                func_path="test.task",
                priority=TaskPriority.NORMAL,
            )

            scheduler.register_task(task_def)
            execution_id = scheduler.schedule_task("task1")

            # Start scheduler
            await scheduler.start()

            # Wait for task to complete
            await asyncio.sleep(2)

            # Stop scheduler
            await scheduler.stop()

            # Verify execution
            status = scheduler.get_task_status(execution_id)
            assert status is not None

    async def test_task_with_retry_on_failure(self, scheduler):
        """Test task retry on failure."""
        call_count = 0

        def failing_task():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Simulated failure")
            return {"result": "success after retries"}

        with patch("app.scheduler.advanced_scheduler.get_job_function") as mock_get_func:
            mock_get_func.return_value = failing_task

            task_def = TaskDefinition(
                task_id="task1",
                task_name="Failing Task",
                func_path="test.failing_task",
                priority=TaskPriority.NORMAL,
                retry_config=RetryConfig(
                    strategy=RetryStrategy.FIXED,
                    max_attempts=3,
                    initial_delay=1,  # Short delay for testing
                ),
            )

            scheduler.register_task(task_def)
            execution_id = scheduler.schedule_task("task1")

            await scheduler.start()
            await asyncio.sleep(5)
            await scheduler.stop()

            # Verify task was retried
            assert call_count >= 2
