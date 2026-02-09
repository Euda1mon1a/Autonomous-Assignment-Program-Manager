"""Tests for job monitoring schemas (Pydantic validation and alias coverage)."""

import pytest
from pydantic import ValidationError

from app.schemas.jobs import (
    TaskInfo,
    ScheduledTaskInfo,
    ReservedTaskInfo,
    WorkerInfo,
    WorkerStats,
    WorkerHealth,
    QueueStatus,
    QueueLengths,
    TaskStatistics,
    RetryStatistics,
    PerformanceMetrics,
    ThroughputMetrics,
    WorkerUtilization,
    TaskHistoryRecord,
    TaskHistoryResponse,
    TimelineBucket,
    TaskTimeline,
    FailureRecord,
    SlowTaskRecord,
    ScheduledTaskConfig,
    ScheduledTasksSummary,
    TaskRevocationRequest,
    TaskRevocationResponse,
    QueuePurgeRequest,
    QueuePurgeResponse,
    JobsDashboardOverview,
)


# ===========================================================================
# TaskInfo Tests
# ===========================================================================


class TestTaskInfo:
    def test_valid_minimal(self):
        r = TaskInfo(task_id="abc-123", task_name="generate_schedule")
        assert r.worker is None
        assert r.queue is None
        assert r.status is None
        assert r.args is None
        assert r.kwargs is None
        assert r.time_start is None
        assert r.acknowledged is None
        assert r.ready is None
        assert r.successful is None
        assert r.failed is None
        assert r.result is None
        assert r.error is None
        assert r.traceback is None

    def test_alias_construction(self):
        r = TaskInfo(
            taskId="abc-123",
            taskName="generate_schedule",
            timeStart=1234567890.0,
        )
        assert r.task_id == "abc-123"
        assert r.time_start == 1234567890.0

    def test_full(self):
        r = TaskInfo(
            task_id="abc-123",
            task_name="generate_schedule",
            worker="worker-1",
            queue="default",
            status="STARTED",
            args=[1, 2],
            kwargs={"block_id": "B10"},
            time_start=1234567890.0,
            acknowledged=True,
            ready=False,
            successful=False,
            failed=False,
            result=None,
            error=None,
            traceback=None,
        )
        assert r.acknowledged is True


# ===========================================================================
# ScheduledTaskInfo Tests
# ===========================================================================


class TestScheduledTaskInfo:
    def test_valid(self):
        r = ScheduledTaskInfo(task_name="daily_cleanup")
        assert r.task_id is None
        assert r.worker is None
        assert r.eta is None
        assert r.priority is None
        assert r.args is None
        assert r.kwargs is None

    def test_alias_construction(self):
        r = ScheduledTaskInfo(taskName="daily_cleanup", taskId="sched-1")
        assert r.task_name == "daily_cleanup"
        assert r.task_id == "sched-1"


# ===========================================================================
# ReservedTaskInfo Tests
# ===========================================================================


class TestReservedTaskInfo:
    def test_valid(self):
        r = ReservedTaskInfo(task_id="res-1", task_name="process_swap")
        assert r.worker is None
        assert r.queue is None
        assert r.priority is None

    def test_alias_construction(self):
        r = ReservedTaskInfo(taskId="res-1", taskName="process_swap")
        assert r.task_id == "res-1"


# ===========================================================================
# WorkerInfo Tests
# ===========================================================================


class TestWorkerInfo:
    def test_valid(self):
        r = WorkerInfo(name="worker-1", status="online")
        assert r.pool is None
        assert r.max_concurrency is None
        assert r.processes is None

    def test_alias_construction(self):
        r = WorkerInfo(name="worker-1", status="online", maxConcurrency=4)
        assert r.max_concurrency == 4


# ===========================================================================
# WorkerStats Tests
# ===========================================================================


class TestWorkerStats:
    def test_valid(self):
        r = WorkerStats(
            total_workers=3,
            online_workers=2,
            workers=[WorkerInfo(name="w1", status="online")],
        )
        assert len(r.workers) == 1

    def test_alias_construction(self):
        r = WorkerStats(totalWorkers=3, onlineWorkers=2, workers=[])
        assert r.total_workers == 3


# ===========================================================================
# WorkerHealth Tests
# ===========================================================================


class TestWorkerHealth:
    def test_valid(self):
        r = WorkerHealth(
            healthy=True,
            total_workers=3,
            online_workers=3,
            offline_workers=0,
            workers=["w1", "w2", "w3"],
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.healthy is True

    def test_alias_construction(self):
        r = WorkerHealth(
            healthy=False,
            totalWorkers=2,
            onlineWorkers=1,
            offlineWorkers=1,
            workers=["w1"],
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.offline_workers == 1


# ===========================================================================
# QueueStatus Tests
# ===========================================================================


class TestQueueStatus:
    def test_valid(self):
        r = QueueStatus(
            queue_name="default",
            active_tasks=5,
            reserved_tasks=3,
            total_pending=8,
        )
        assert r.queue_name == "default"

    def test_alias_construction(self):
        r = QueueStatus(
            queueName="default", activeTasks=0, reservedTasks=0, totalPending=0
        )
        assert r.active_tasks == 0


# ===========================================================================
# QueueLengths Tests
# ===========================================================================


class TestQueueLengths:
    def test_valid(self):
        r = QueueLengths(
            queues={"default": 5, "priority": 2},
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.queues["default"] == 5


# ===========================================================================
# TaskStatistics Tests
# ===========================================================================


class TestTaskStatistics:
    def test_valid(self):
        r = TaskStatistics(
            task_name="generate_schedule",
            time_range_hours=24,
            total_tasks=100,
            successful_tasks=95,
            failed_tasks=5,
            pending_tasks=0,
            retried_tasks=3,
            success_rate=0.95,
            failure_rate=0.05,
            average_runtime_seconds=120.5,
            min_runtime_seconds=30.0,
            max_runtime_seconds=300.0,
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.success_rate == 0.95

    def test_alias_construction(self):
        r = TaskStatistics(
            taskName="test",
            timeRangeHours=1,
            totalTasks=0,
            successfulTasks=0,
            failedTasks=0,
            pendingTasks=0,
            retriedTasks=0,
            successRate=0.0,
            failureRate=0.0,
            averageRuntimeSeconds=0.0,
            minRuntimeSeconds=0.0,
            maxRuntimeSeconds=0.0,
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.task_name == "test"


# ===========================================================================
# RetryStatistics Tests
# ===========================================================================


class TestRetryStatistics:
    def test_valid(self):
        r = RetryStatistics(
            task_name="process_swap",
            total_retries=10,
            tasks_with_retries=5,
            max_retries_used=3,
            average_retries_per_task=2.0,
            retry_success_rate=0.8,
            common_retry_reasons=["timeout", "db_lock"],
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.retry_success_rate == 0.8


# ===========================================================================
# PerformanceMetrics Tests
# ===========================================================================


class TestPerformanceMetrics:
    def test_valid(self):
        r = PerformanceMetrics(
            task_name="generate_schedule",
            time_range_hours=24,
            total_executions=50,
            average_runtime_seconds=120.0,
            median_runtime_seconds=110.0,
            p50_runtime_seconds=110.0,
            p75_runtime_seconds=150.0,
            p90_runtime_seconds=200.0,
            p95_runtime_seconds=250.0,
            p99_runtime_seconds=290.0,
            min_runtime_seconds=30.0,
            max_runtime_seconds=300.0,
            std_dev_runtime_seconds=50.0,
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.p99_runtime_seconds == 290.0

    def test_alias_construction(self):
        r = PerformanceMetrics(
            taskName="test",
            timeRangeHours=1,
            totalExecutions=0,
            averageRuntimeSeconds=0.0,
            medianRuntimeSeconds=0.0,
            p50RuntimeSeconds=0.0,
            p75RuntimeSeconds=0.0,
            p90RuntimeSeconds=0.0,
            p95RuntimeSeconds=0.0,
            p99RuntimeSeconds=0.0,
            minRuntimeSeconds=0.0,
            maxRuntimeSeconds=0.0,
            stdDevRuntimeSeconds=0.0,
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.task_name == "test"


# ===========================================================================
# ThroughputMetrics Tests
# ===========================================================================


class TestThroughputMetrics:
    def test_valid(self):
        r = ThroughputMetrics(
            queue_name="default",
            time_range_hours=24,
            total_tasks_processed=500,
            tasks_per_minute=0.35,
            tasks_per_hour=20.8,
            peak_throughput_per_hour=45.0,
            average_queue_time_seconds=2.5,
            average_processing_time_seconds=120.0,
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.tasks_per_hour == 20.8


# ===========================================================================
# WorkerUtilization Tests
# ===========================================================================


class TestWorkerUtilization:
    def test_valid(self):
        r = WorkerUtilization(
            total_workers=4,
            active_workers=3,
            idle_workers=1,
            average_utilization_percentage=75.0,
            tasks_per_worker=12.5,
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.average_utilization_percentage == 75.0


# ===========================================================================
# TaskHistoryRecord Tests
# ===========================================================================


class TestTaskHistoryRecord:
    def test_valid_minimal(self):
        r = TaskHistoryRecord(
            task_id="hist-1",
            task_name="generate_schedule",
            status="SUCCESS",
        )
        assert r.started_at is None
        assert r.completed_at is None
        assert r.runtime_seconds is None
        assert r.worker is None
        assert r.retries is None

    def test_full(self):
        r = TaskHistoryRecord(
            task_id="hist-1",
            task_name="generate_schedule",
            status="SUCCESS",
            started_at="2026-03-01T10:00:00Z",
            completed_at="2026-03-01T10:02:00Z",
            runtime_seconds=120.0,
            worker="worker-1",
            queue="default",
            retries=0,
            args=[],
            kwargs={},
            result={"status": "ok"},
            error=None,
        )
        assert r.runtime_seconds == 120.0


# ===========================================================================
# TaskHistoryResponse Tests
# ===========================================================================


class TestTaskHistoryResponse:
    def test_valid(self):
        r = TaskHistoryResponse(
            total_count=0,
            limit=50,
            offset=0,
            tasks=[],
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.task_name is None
        assert r.filters is None


# ===========================================================================
# TimelineBucket Tests
# ===========================================================================


class TestTimelineBucket:
    def test_valid(self):
        r = TimelineBucket(
            timestamp="2026-03-01T10:00:00Z",
            total_tasks=20,
            successful_tasks=18,
            failed_tasks=2,
            average_runtime_seconds=95.0,
        )
        assert r.total_tasks == 20


# ===========================================================================
# TaskTimeline Tests
# ===========================================================================


class TestTaskTimeline:
    def test_valid(self):
        r = TaskTimeline(
            task_name="generate_schedule",
            time_range_hours=24,
            granularity="hour",
            buckets=[],
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.granularity == "hour"


# ===========================================================================
# FailureRecord Tests
# ===========================================================================


class TestFailureRecord:
    def test_valid_minimal(self):
        r = FailureRecord(
            task_id="fail-1",
            task_name="process_swap",
            failed_at="2026-03-01T10:00:00Z",
            error_type="TimeoutError",
            error_message="Task timed out after 300s",
        )
        assert r.traceback is None
        assert r.worker is None
        assert r.retries is None

    def test_full(self):
        r = FailureRecord(
            task_id="fail-1",
            task_name="process_swap",
            failed_at="2026-03-01T10:00:00Z",
            error_type="TimeoutError",
            error_message="Task timed out",
            traceback="Traceback...",
            worker="worker-1",
            queue="default",
            retries=3,
            args=[],
            kwargs={},
        )
        assert r.retries == 3


# ===========================================================================
# SlowTaskRecord Tests
# ===========================================================================


class TestSlowTaskRecord:
    def test_valid(self):
        r = SlowTaskRecord(
            task_id="slow-1",
            task_name="generate_schedule",
            runtime_seconds=450.0,
            started_at="2026-03-01T10:00:00Z",
            completed_at="2026-03-01T10:07:30Z",
            status="SUCCESS",
        )
        assert r.worker is None
        assert r.queue is None


# ===========================================================================
# ScheduledTaskConfig Tests
# ===========================================================================


class TestScheduledTaskConfig:
    def test_valid(self):
        r = ScheduledTaskConfig(
            name="daily_cleanup",
            task="app.tasks.cleanup",
            schedule="0 0 * * *",
        )
        assert r.options is None

    def test_with_options(self):
        r = ScheduledTaskConfig(
            name="daily_cleanup",
            task="app.tasks.cleanup",
            schedule="0 0 * * *",
            options={"queue": "maintenance"},
        )
        assert r.options["queue"] == "maintenance"


# ===========================================================================
# ScheduledTasksSummary Tests
# ===========================================================================


class TestScheduledTasksSummary:
    def test_valid(self):
        r = ScheduledTasksSummary(
            total_scheduled_tasks=5,
            scheduled_tasks=[],
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.total_scheduled_tasks == 5


# ===========================================================================
# TaskRevocationRequest Tests
# ===========================================================================


class TestTaskRevocationRequest:
    def test_defaults(self):
        r = TaskRevocationRequest(task_id="abc-123")
        assert r.terminate is False

    def test_with_terminate(self):
        r = TaskRevocationRequest(task_id="abc-123", terminate=True)
        assert r.terminate is True

    def test_alias_construction(self):
        r = TaskRevocationRequest(taskId="abc-123")
        assert r.task_id == "abc-123"


# ===========================================================================
# TaskRevocationResponse Tests
# ===========================================================================


class TestTaskRevocationResponse:
    def test_valid(self):
        r = TaskRevocationResponse(task_id="abc-123", success=True)
        assert r.message is None

    def test_with_message(self):
        r = TaskRevocationResponse(
            task_id="abc-123", success=False, message="Task already completed"
        )
        assert r.message == "Task already completed"


# ===========================================================================
# QueuePurgeRequest Tests
# ===========================================================================


class TestQueuePurgeRequest:
    def test_defaults(self):
        r = QueuePurgeRequest(queue_name="default")
        assert r.confirm is False

    def test_alias_construction(self):
        r = QueuePurgeRequest(queueName="default", confirm=True)
        assert r.queue_name == "default"
        assert r.confirm is True


# ===========================================================================
# QueuePurgeResponse Tests
# ===========================================================================


class TestQueuePurgeResponse:
    def test_valid(self):
        r = QueuePurgeResponse(
            queue_name="default",
            tasks_purged=10,
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.tasks_purged == 10


# ===========================================================================
# JobsDashboardOverview Tests
# ===========================================================================


class TestJobsDashboardOverview:
    def test_valid(self):
        r = JobsDashboardOverview(
            active_tasks_count=5,
            scheduled_tasks_count=10,
            reserved_tasks_count=3,
            total_workers=4,
            online_workers=3,
            queue_counts={"default": 5, "priority": 2},
            worker_utilization_percentage=75.0,
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.worker_utilization_percentage == 75.0

    def test_alias_construction(self):
        r = JobsDashboardOverview(
            activeTasksCount=0,
            scheduledTasksCount=0,
            reservedTasksCount=0,
            totalWorkers=0,
            onlineWorkers=0,
            queueCounts={},
            workerUtilizationPercentage=0.0,
            timestamp="2026-03-01T00:00:00Z",
        )
        assert r.active_tasks_count == 0
