"""
Tests for async_tools module.

Tests the structure, imports, and basic functionality of the Celery
async task management tools.
"""

import pytest
from datetime import datetime

from scheduler_mcp.async_tools import (
    ActiveTaskInfo,
    ActiveTasksResult,
    BackgroundTaskRequest,
    BackgroundTaskResult,
    CancelTaskResult,
    TaskStatus,
    TaskStatusResult,
    TaskType,
    TASK_TYPE_MAP,
    TASK_DURATION_ESTIMATES,
    validate_task_params,
)


class TestTaskTypeEnum:
    """Test TaskType enumeration."""

    def test_all_task_types_exist(self):
        """Verify all expected task types are defined."""
        expected_types = [
            "resilience_health_check",
            "resilience_contingency",
            "resilience_fallback_precompute",
            "resilience_utilization_forecast",
            "resilience_crisis_activation",
            "metrics_computation",
            "metrics_snapshot",
            "metrics_cleanup",
            "metrics_fairness_report",
            "metrics_version_diff",
        ]

        for task_type in expected_types:
            assert task_type in [t.value for t in TaskType]

    def test_task_type_map_completeness(self):
        """Verify all task types have Celery task name mappings."""
        for task_type in TaskType:
            assert task_type in TASK_TYPE_MAP
            assert TASK_TYPE_MAP[task_type].startswith("app.")

    def test_duration_estimates_exist(self):
        """Verify all task types have duration estimates."""
        for task_type in TaskType:
            assert task_type in TASK_DURATION_ESTIMATES
            assert isinstance(TASK_DURATION_ESTIMATES[task_type], str)


class TestModels:
    """Test Pydantic models for requests and responses."""

    def test_background_task_request(self):
        """Test BackgroundTaskRequest model."""
        request = BackgroundTaskRequest(
            task_type=TaskType.RESILIENCE_HEALTH_CHECK,
            params={"days_ahead": 90},
        )
        assert request.task_type == TaskType.RESILIENCE_HEALTH_CHECK
        assert request.params == {"days_ahead": 90}

    def test_background_task_request_default_params(self):
        """Test BackgroundTaskRequest with default params."""
        request = BackgroundTaskRequest(
            task_type=TaskType.METRICS_SNAPSHOT,
        )
        assert request.params == {}

    def test_background_task_result(self):
        """Test BackgroundTaskResult model."""
        now = datetime.utcnow()
        result = BackgroundTaskResult(
            task_id="test-task-id",
            task_type=TaskType.RESILIENCE_CONTINGENCY,
            status="queued",
            estimated_duration="2-5 minutes",
            queued_at=now,
            message="Task queued successfully",
        )
        assert result.task_id == "test-task-id"
        assert result.status == "queued"
        assert result.estimated_duration == "2-5 minutes"

    def test_task_status_result(self):
        """Test TaskStatusResult model."""
        result = TaskStatusResult(
            task_id="test-task-id",
            status=TaskStatus.SUCCESS,
            progress=100,
            result={"completed": True},
            error=None,
        )
        assert result.task_id == "test-task-id"
        assert result.status == TaskStatus.SUCCESS
        assert result.progress == 100
        assert result.result == {"completed": True}

    def test_task_status_result_with_error(self):
        """Test TaskStatusResult with error."""
        result = TaskStatusResult(
            task_id="test-task-id",
            status=TaskStatus.FAILURE,
            progress=100,
            result=None,
            error="Task failed: Connection timeout",
        )
        assert result.status == TaskStatus.FAILURE
        assert result.error is not None

    def test_cancel_task_result(self):
        """Test CancelTaskResult model."""
        now = datetime.utcnow()
        result = CancelTaskResult(
            task_id="test-task-id",
            status="revoked",
            message="Task canceled",
            canceled_at=now,
        )
        assert result.task_id == "test-task-id"
        assert result.status == "revoked"

    def test_active_task_info(self):
        """Test ActiveTaskInfo model."""
        now = datetime.utcnow()
        info = ActiveTaskInfo(
            task_id="test-task-id",
            task_name="app.resilience.tasks.periodic_health_check",
            task_type="resilience_health_check",
            status="running",
            started_at=now,
        )
        assert info.task_id == "test-task-id"
        assert info.task_type == "resilience_health_check"

    def test_active_tasks_result(self):
        """Test ActiveTasksResult model."""
        now = datetime.utcnow()
        tasks = [
            ActiveTaskInfo(
                task_id="task-1",
                task_name="app.resilience.tasks.periodic_health_check",
                status="running",
            ),
            ActiveTaskInfo(
                task_id="task-2",
                task_name="app.tasks.schedule_metrics_tasks.compute_schedule_metrics",
                status="running",
            ),
        ]
        result = ActiveTasksResult(
            total_active=2,
            tasks=tasks,
            queried_at=now,
        )
        assert result.total_active == 2
        assert len(result.tasks) == 2


class TestValidation:
    """Test parameter validation logic."""

    def test_validate_resilience_contingency_params_valid(self):
        """Test valid params for resilience_contingency."""
        # Should not raise
        validate_task_params(
            TaskType.RESILIENCE_CONTINGENCY,
            {"days_ahead": 90}
        )

    def test_validate_resilience_contingency_params_invalid(self):
        """Test invalid params for resilience_contingency."""
        with pytest.raises(ValueError, match="days_ahead must be an integer"):
            validate_task_params(
                TaskType.RESILIENCE_CONTINGENCY,
                {"days_ahead": "ninety"}
            )

    def test_validate_crisis_activation_missing_severity(self):
        """Test crisis activation without required severity."""
        with pytest.raises(ValueError, match="severity parameter required"):
            validate_task_params(
                TaskType.RESILIENCE_CRISIS_ACTIVATION,
                {"reason": "Emergency"}
            )

    def test_validate_crisis_activation_missing_reason(self):
        """Test crisis activation without required reason."""
        with pytest.raises(ValueError, match="reason parameter required"):
            validate_task_params(
                TaskType.RESILIENCE_CRISIS_ACTIVATION,
                {"severity": "critical"}
            )

    def test_validate_version_diff_missing_params(self):
        """Test version diff without required run IDs."""
        with pytest.raises(ValueError, match="run_id_1 and run_id_2 required"):
            validate_task_params(
                TaskType.METRICS_VERSION_DIFF,
                {"run_id_1": "uuid1"}
            )

    def test_validate_metrics_snapshot_params_valid(self):
        """Test valid params for metrics_snapshot."""
        # Should not raise
        validate_task_params(
            TaskType.METRICS_SNAPSHOT,
            {"period_days": 90}
        )

    def test_validate_metrics_snapshot_params_invalid(self):
        """Test invalid params for metrics_snapshot."""
        with pytest.raises(ValueError, match="period_days must be an integer"):
            validate_task_params(
                TaskType.METRICS_SNAPSHOT,
                {"period_days": "ninety"}
            )

    def test_validate_empty_params(self):
        """Test validation with empty params (should pass for most tasks)."""
        # Should not raise for health check (no params required)
        validate_task_params(
            TaskType.RESILIENCE_HEALTH_CHECK,
            {}
        )


class TestTaskTypeMapping:
    """Test task type to Celery task name mapping."""

    def test_resilience_task_mapping(self):
        """Test resilience task type mappings."""
        assert TASK_TYPE_MAP[TaskType.RESILIENCE_HEALTH_CHECK] == \
            "app.resilience.tasks.periodic_health_check"
        assert TASK_TYPE_MAP[TaskType.RESILIENCE_CONTINGENCY] == \
            "app.resilience.tasks.run_contingency_analysis"
        assert TASK_TYPE_MAP[TaskType.RESILIENCE_FALLBACK_PRECOMPUTE] == \
            "app.resilience.tasks.precompute_fallback_schedules"
        assert TASK_TYPE_MAP[TaskType.RESILIENCE_UTILIZATION_FORECAST] == \
            "app.resilience.tasks.generate_utilization_forecast"
        assert TASK_TYPE_MAP[TaskType.RESILIENCE_CRISIS_ACTIVATION] == \
            "app.resilience.tasks.activate_crisis_response"

    def test_metrics_task_mapping(self):
        """Test metrics task type mappings."""
        assert TASK_TYPE_MAP[TaskType.METRICS_COMPUTATION] == \
            "app.tasks.schedule_metrics_tasks.compute_schedule_metrics"
        assert TASK_TYPE_MAP[TaskType.METRICS_SNAPSHOT] == \
            "app.tasks.schedule_metrics_tasks.snapshot_metrics"
        assert TASK_TYPE_MAP[TaskType.METRICS_CLEANUP] == \
            "app.tasks.schedule_metrics_tasks.cleanup_old_snapshots"
        assert TASK_TYPE_MAP[TaskType.METRICS_FAIRNESS_REPORT] == \
            "app.tasks.schedule_metrics_tasks.generate_fairness_trend_report"
        assert TASK_TYPE_MAP[TaskType.METRICS_VERSION_DIFF] == \
            "app.tasks.schedule_metrics_tasks.compute_version_diff"


# Note: Integration tests that actually call start_background_task, get_task_status,
# cancel_task, and list_active_tasks would require a running Celery instance with
# Redis. Those should be in a separate integration test suite.
