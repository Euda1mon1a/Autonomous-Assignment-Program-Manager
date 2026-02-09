"""Tests for queue schemas (Field bounds, aliases, defaults, populate_by_name)."""

import pytest
from pydantic import ValidationError

from app.schemas.queue import (
    TaskSubmitRequest,
    TaskSubmitResponse,
    TaskChainRequest,
    TaskGroupRequest,
    TaskDependencyRequest,
    TaskStatusResponse,
    TaskProgressResponse,
    TaskCancelRequest,
    TaskCancelResponse,
    TaskRetryRequest,
    TaskRetryResponse,
    QueueStatsResponse,
    QueuePurgeRequest,
    QueuePurgeResponse,
    WorkerHealthResponse,
    WorkerStatsResponse,
    WorkerUtilizationResponse,
    WorkerTasksResponse,
    WorkerControlRequest,
    WorkerControlResponse,
    ScheduleTaskRequest,
    ScheduleTaskResponse,
    PeriodicTaskRequest,
    PeriodicTaskResponse,
    PeriodicTasksListResponse,
    ScheduledTasksListResponse,
    PeriodicTaskControlRequest,
    PeriodicTaskControlResponse,
    DeadLetterTask,
    DeadLetterQueueResponse,
)


# ── TaskSubmitRequest ──────────────────────────────────────────────────


class TestTaskSubmitRequest:
    def test_defaults(self):
        r = TaskSubmitRequest(taskName="my.task")
        assert r.task_name == "my.task"
        assert r.args == []
        assert r.kwargs == {}
        assert r.priority == 5
        assert r.countdown is None
        assert r.eta is None
        assert r.queue is None

    def test_by_field_name(self):
        r = TaskSubmitRequest(task_name="my.task")
        assert r.task_name == "my.task"

    # --- priority ge=0, le=9 ---

    def test_priority_below_min(self):
        with pytest.raises(ValidationError):
            TaskSubmitRequest(taskName="t", priority=-1)

    def test_priority_above_max(self):
        with pytest.raises(ValidationError):
            TaskSubmitRequest(taskName="t", priority=10)

    # --- countdown ge=0 ---

    def test_countdown_negative(self):
        with pytest.raises(ValidationError):
            TaskSubmitRequest(taskName="t", countdown=-1)


# ── TaskSubmitResponse ─────────────────────────────────────────────────


class TestTaskSubmitResponse:
    def test_by_alias(self):
        r = TaskSubmitResponse(taskId="abc", taskName="my.task", status="pending")
        assert r.task_id == "abc"
        assert r.task_name == "my.task"

    def test_by_field_name(self):
        r = TaskSubmitResponse(task_id="abc", task_name="my.task", status="pending")
        assert r.task_id == "abc"

    def test_optional_defaults(self):
        r = TaskSubmitResponse(taskId="abc", taskName="t", status="ok")
        assert r.message is None
        assert r.estimated_execution is None


# ── TaskChainRequest ───────────────────────────────────────────────────


class TestTaskChainRequest:
    def test_defaults(self):
        r = TaskChainRequest(tasks=[{"name": "t1"}])
        assert r.priority == 5

    def test_priority_bounds(self):
        with pytest.raises(ValidationError):
            TaskChainRequest(tasks=[], priority=-1)
        with pytest.raises(ValidationError):
            TaskChainRequest(tasks=[], priority=10)


# ── TaskGroupRequest ───────────────────────────────────────────────────


class TestTaskGroupRequest:
    def test_defaults(self):
        r = TaskGroupRequest(tasks=[{"name": "t1"}])
        assert r.priority == 5

    def test_priority_bounds(self):
        with pytest.raises(ValidationError):
            TaskGroupRequest(tasks=[], priority=10)


# ── TaskDependencyRequest ──────────────────────────────────────────────


class TestTaskDependencyRequest:
    def test_by_alias(self):
        r = TaskDependencyRequest(taskName="my.task", dependencies=["dep1"])
        assert r.task_name == "my.task"
        assert r.priority == 5
        assert r.args == []
        assert r.kwargs == {}

    def test_priority_bounds(self):
        with pytest.raises(ValidationError):
            TaskDependencyRequest(taskName="t", dependencies=[], priority=10)


# ── TaskStatusResponse ─────────────────────────────────────────────────


class TestTaskStatusResponse:
    def test_by_alias(self):
        r = TaskStatusResponse(taskId="abc", state="SUCCESS", ready=True)
        assert r.task_id == "abc"

    def test_optional_defaults(self):
        r = TaskStatusResponse(taskId="abc", state="PENDING", ready=False)
        assert r.successful is None
        assert r.failed is None
        assert r.progress is None
        assert r.result is None
        assert r.error is None
        assert r.traceback is None


# ── TaskProgressResponse ───────────────────────────────────────────────


class TestTaskProgressResponse:
    def test_by_alias(self):
        r = TaskProgressResponse(taskId="abc", current=5, total=10, percentage=50)
        assert r.task_id == "abc"
        assert r.message is None


# ── TaskCancelRequest ──────────────────────────────────────────────────


class TestTaskCancelRequest:
    def test_defaults(self):
        r = TaskCancelRequest(taskId="abc")
        assert r.task_id == "abc"
        assert r.terminate is False


# ── TaskCancelResponse ─────────────────────────────────────────────────


class TestTaskCancelResponse:
    def test_by_alias(self):
        r = TaskCancelResponse(taskId="abc", success=True, message="ok")
        assert r.task_id == "abc"


# ── TaskRetryRequest ───────────────────────────────────────────────────


class TestTaskRetryRequest:
    def test_defaults(self):
        r = TaskRetryRequest(taskId="abc")
        assert r.task_id == "abc"
        assert r.countdown is None
        assert r.eta is None

    def test_countdown_negative(self):
        with pytest.raises(ValidationError):
            TaskRetryRequest(taskId="abc", countdown=-1)


# ── TaskRetryResponse ──────────────────────────────────────────────────


class TestTaskRetryResponse:
    def test_by_alias(self):
        r = TaskRetryResponse(originalTaskId="a", newTaskId="b", message="ok")
        assert r.original_task_id == "a"
        assert r.new_task_id == "b"


# ── QueuePurgeRequest ──────────────────────────────────────────────────


class TestQueuePurgeRequest:
    def test_defaults(self):
        r = QueuePurgeRequest(queueName="default")
        assert r.queue_name == "default"
        assert r.confirm is False


# ── QueuePurgeResponse ─────────────────────────────────────────────────


class TestQueuePurgeResponse:
    def test_by_alias(self):
        r = QueuePurgeResponse(queueName="default", tasksPurged=5, timestamp="now")
        assert r.queue_name == "default"
        assert r.tasks_purged == 5


# ── WorkerHealthResponse ───────────────────────────────────────────────


class TestWorkerHealthResponse:
    def test_by_alias(self):
        r = WorkerHealthResponse(
            healthy=True,
            workers={},
            totalWorkers=4,
            onlineWorkers=3,
            timestamp="now",
        )
        assert r.total_workers == 4
        assert r.online_workers == 3


# ── WorkerUtilizationResponse ──────────────────────────────────────────


class TestWorkerUtilizationResponse:
    def test_by_alias(self):
        r = WorkerUtilizationResponse(
            totalWorkers=4,
            activeWorkers=2,
            idleWorkers=2,
            utilizationPercentage=50.0,
            timestamp="now",
        )
        assert r.total_workers == 4
        assert r.active_workers == 2
        assert r.idle_workers == 2
        assert r.utilization_percentage == 50.0


# ── WorkerControlRequest ──────────────────────────────────────────────


class TestWorkerControlRequest:
    def test_defaults(self):
        r = WorkerControlRequest(workerName="worker-1", action="shutdown")
        assert r.worker_name == "worker-1"
        assert r.parameters == {}


# ── ScheduleTaskRequest ────────────────────────────────────────────────


class TestScheduleTaskRequest:
    def test_defaults(self):
        r = ScheduleTaskRequest(taskName="my.task")
        assert r.task_name == "my.task"
        assert r.priority == 5
        assert r.args == []
        assert r.kwargs == {}
        assert r.eta is None
        assert r.countdown is None

    def test_priority_bounds(self):
        with pytest.raises(ValidationError):
            ScheduleTaskRequest(taskName="t", priority=10)

    def test_countdown_negative(self):
        with pytest.raises(ValidationError):
            ScheduleTaskRequest(taskName="t", countdown=-1)


# ── ScheduleTaskResponse ───────────────────────────────────────────────


class TestScheduleTaskResponse:
    def test_by_alias(self):
        r = ScheduleTaskResponse(
            taskId="abc", taskName="my.task", scheduledFor="2026-01-15", message="ok"
        )
        assert r.task_id == "abc"
        assert r.task_name == "my.task"
        assert r.scheduled_for == "2026-01-15"


# ── PeriodicTaskRequest ────────────────────────────────────────────────


class TestPeriodicTaskRequest:
    def test_defaults(self):
        r = PeriodicTaskRequest(
            name="daily-check",
            taskName="app.tasks.check",
            scheduleConfig={"every": "1h"},
        )
        assert r.task_name == "app.tasks.check"
        assert r.schedule_config == {"every": "1h"}
        assert r.args == []
        assert r.kwargs == {}
        assert r.options == {}


# ── PeriodicTaskResponse ───────────────────────────────────────────────


class TestPeriodicTaskResponse:
    def test_by_alias(self):
        r = PeriodicTaskResponse(
            name="daily-check", taskName="t", schedule="1h", message="ok"
        )
        assert r.task_name == "t"


# ── PeriodicTasksListResponse ──────────────────────────────────────────


class TestPeriodicTasksListResponse:
    def test_by_alias(self):
        r = PeriodicTasksListResponse(tasks={}, totalTasks=5, timestamp="now")
        assert r.total_tasks == 5


# ── ScheduledTasksListResponse ─────────────────────────────────────────


class TestScheduledTasksListResponse:
    def test_by_alias(self):
        r = ScheduledTasksListResponse(tasks={}, totalTasks=3, timestamp="now")
        assert r.total_tasks == 3


# ── DeadLetterTask ─────────────────────────────────────────────────────


class TestDeadLetterTask:
    def test_by_alias(self):
        r = DeadLetterTask(
            taskId="abc",
            taskName="my.task",
            args=[],
            kwargs={},
            error="Timeout",
            errorType="TimeoutError",
            traceback="...",
            failedAt="2026-01-15T12:00:00",
        )
        assert r.task_id == "abc"
        assert r.task_name == "my.task"
        assert r.error_type == "TimeoutError"
        assert r.failed_at == "2026-01-15T12:00:00"


# ── DeadLetterQueueResponse ───────────────────────────────────────────


class TestDeadLetterQueueResponse:
    def test_by_alias(self):
        r = DeadLetterQueueResponse(tasks=[], totalTasks=0, timestamp="now")
        assert r.total_tasks == 0
