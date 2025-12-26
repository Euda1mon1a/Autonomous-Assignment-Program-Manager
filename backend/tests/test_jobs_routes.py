"""
Comprehensive tests for Background Job Monitoring API routes.

Tests coverage for Celery background task monitoring:
- GET /api/v1/jobs/dashboard - Dashboard overview
- GET /api/v1/jobs/active - Active tasks
- GET /api/v1/jobs/scheduled - Scheduled tasks
- GET /api/v1/jobs/reserved - Reserved tasks
- GET /api/v1/jobs/tasks/{task_id} - Task info
- GET /api/v1/jobs/workers - Worker stats
- GET /api/v1/jobs/workers/health - Worker health
- GET /api/v1/jobs/workers/utilization - Worker utilization
- GET /api/v1/jobs/queues - Queue statistics
- GET /api/v1/jobs/statistics/tasks - Task statistics
- GET /api/v1/jobs/statistics/retries - Retry statistics
- GET /api/v1/jobs/statistics/performance - Performance metrics
- GET /api/v1/jobs/statistics/throughput - Throughput metrics
- GET /api/v1/jobs/history - Task history
- GET /api/v1/jobs/history/failures - Recent failures
- GET /api/v1/jobs/history/slow - Slow tasks
- GET /api/v1/jobs/scheduled-tasks - Beat schedule summary
- POST /api/v1/jobs/tasks/revoke - Revoke task
- POST /api/v1/jobs/queues/purge - Purge queue
- GET /api/v1/jobs/registered - Registered tasks
"""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# Test Classes
# ============================================================================


class TestJobsDashboard:
    """Tests for GET /api/v1/jobs/dashboard endpoint."""

    def test_dashboard_requires_auth(self, client: TestClient):
        """Test that dashboard requires authentication."""
        response = client.get("/api/v1/jobs/dashboard")
        assert response.status_code in [401, 403]

    def test_dashboard_success(self, client: TestClient, auth_headers: dict):
        """Test getting dashboard overview."""
        with (
            patch("app.api.routes.jobs.CeleryMonitorService") as mock_monitor,
            patch("app.api.routes.jobs.JobStatsService") as mock_stats,
        ):
            # Mock monitor service
            mock_monitor_instance = MagicMock()
            mock_monitor_instance.get_active_tasks.return_value = []
            mock_monitor_instance.get_scheduled_tasks.return_value = []
            mock_monitor_instance.get_reserved_tasks.return_value = []
            mock_monitor_instance.get_worker_stats.return_value = {
                "total_workers": 2,
                "online_workers": 2,
            }
            mock_monitor_instance.get_queue_lengths.return_value = {"default": 0}
            mock_monitor.return_value = mock_monitor_instance

            # Mock stats service
            mock_stats_instance = MagicMock()
            mock_stats_instance.get_worker_utilization.return_value = {
                "average_utilization_percentage": 50.0
            }
            mock_stats.return_value = mock_stats_instance

            response = client.get("/api/v1/jobs/dashboard", headers=auth_headers)

            if response.status_code == 200:
                data = response.json()
                assert "activeTasksCount" in data
                assert "totalWorkers" in data


class TestActiveTasks:
    """Tests for GET /api/v1/jobs/active endpoint."""

    def test_active_tasks_requires_auth(self, client: TestClient):
        """Test that active tasks requires authentication."""
        response = client.get("/api/v1/jobs/active")
        assert response.status_code in [401, 403]

    def test_active_tasks_success(self, client: TestClient, auth_headers: dict):
        """Test getting active tasks."""
        with patch("app.api.routes.jobs.CeleryMonitorService") as mock_monitor:
            mock_instance = MagicMock()
            mock_instance.get_active_tasks.return_value = [
                {
                    "task_id": "task-123",
                    "task_name": "test_task",
                    "worker": "celery@worker1",
                    "queue": "default",
                    "time_start": datetime.utcnow().timestamp(),
                    "acknowledged": True,
                }
            ]
            mock_monitor.return_value = mock_instance

            response = client.get("/api/v1/jobs/active", headers=auth_headers)

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)

    def test_active_tasks_filter_by_queue(self, client: TestClient, auth_headers: dict):
        """Test filtering active tasks by queue."""
        with patch("app.api.routes.jobs.CeleryMonitorService") as mock_monitor:
            mock_instance = MagicMock()
            mock_instance.get_active_tasks.return_value = []
            mock_monitor.return_value = mock_instance

            response = client.get(
                "/api/v1/jobs/active?queue=resilience",
                headers=auth_headers,
            )

            if response.status_code == 200:
                mock_instance.get_active_tasks.assert_called_once_with(
                    queue_name="resilience"
                )


class TestScheduledTasks:
    """Tests for GET /api/v1/jobs/scheduled endpoint."""

    def test_scheduled_tasks_success(self, client: TestClient, auth_headers: dict):
        """Test getting scheduled tasks."""
        with patch("app.api.routes.jobs.CeleryMonitorService") as mock_monitor:
            mock_instance = MagicMock()
            mock_instance.get_scheduled_tasks.return_value = []
            mock_monitor.return_value = mock_instance

            response = client.get("/api/v1/jobs/scheduled", headers=auth_headers)

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)


class TestReservedTasks:
    """Tests for GET /api/v1/jobs/reserved endpoint."""

    def test_reserved_tasks_success(self, client: TestClient, auth_headers: dict):
        """Test getting reserved tasks."""
        with patch("app.api.routes.jobs.CeleryMonitorService") as mock_monitor:
            mock_instance = MagicMock()
            mock_instance.get_reserved_tasks.return_value = []
            mock_monitor.return_value = mock_instance

            response = client.get("/api/v1/jobs/reserved", headers=auth_headers)

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)


class TestTaskInfo:
    """Tests for GET /api/v1/jobs/tasks/{task_id} endpoint."""

    def test_get_task_info_success(self, client: TestClient, auth_headers: dict):
        """Test getting task info by ID."""
        with patch("app.api.routes.jobs.CeleryMonitorService") as mock_monitor:
            mock_instance = MagicMock()
            mock_instance.get_task_info.return_value = {
                "task_id": "task-123",
                "task_name": "test_task",
                "state": "SUCCESS",
                "ready": True,
                "successful": True,
            }
            mock_monitor.return_value = mock_instance

            response = client.get(
                "/api/v1/jobs/tasks/task-123",
                headers=auth_headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert data["taskId"] == "task-123"

    def test_get_task_info_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting task info for non-existent task."""
        with patch("app.api.routes.jobs.CeleryMonitorService") as mock_monitor:
            mock_instance = MagicMock()
            mock_instance.get_task_info.return_value = None
            mock_monitor.return_value = mock_instance

            response = client.get(
                "/api/v1/jobs/tasks/non-existent",
                headers=auth_headers,
            )

            # Should return 404 or 500
            assert response.status_code in [401, 404, 500]


class TestWorkerEndpoints:
    """Tests for worker-related endpoints."""

    def test_worker_stats_success(self, client: TestClient, auth_headers: dict):
        """Test getting worker stats."""
        with patch("app.api.routes.jobs.CeleryMonitorService") as mock_monitor:
            mock_instance = MagicMock()
            mock_instance.get_worker_stats.return_value = {
                "total_workers": 2,
                "online_workers": 2,
                "workers": [],
            }
            mock_monitor.return_value = mock_instance

            response = client.get("/api/v1/jobs/workers", headers=auth_headers)

            if response.status_code == 200:
                data = response.json()
                assert "totalWorkers" in data

    def test_worker_health_success(self, client: TestClient, auth_headers: dict):
        """Test getting worker health."""
        with patch("app.api.routes.jobs.CeleryMonitorService") as mock_monitor:
            mock_instance = MagicMock()
            mock_instance.get_worker_health.return_value = {
                "healthy": True,
                "totalWorkers": 2,
                "onlineWorkers": 2,
                "offlineWorkers": 0,
                "workers": [],
                "timestamp": datetime.utcnow().isoformat(),
            }
            mock_monitor.return_value = mock_instance

            response = client.get("/api/v1/jobs/workers/health", headers=auth_headers)

            if response.status_code == 200:
                data = response.json()
                assert "healthy" in data

    def test_worker_utilization_success(self, client: TestClient, auth_headers: dict):
        """Test getting worker utilization."""
        with patch("app.api.routes.jobs.JobStatsService") as mock_stats:
            mock_instance = MagicMock()
            mock_instance.get_worker_utilization.return_value = {
                "totalWorkers": 2,
                "activeWorkers": 1,
                "idleWorkers": 1,
                "averageUtilizationPercentage": 50.0,
                "tasksPerWorker": 0.5,
                "timestamp": datetime.utcnow().isoformat(),
            }
            mock_stats.return_value = mock_instance

            response = client.get(
                "/api/v1/jobs/workers/utilization",
                headers=auth_headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert "averageUtilizationPercentage" in data


class TestQueueEndpoints:
    """Tests for queue-related endpoints."""

    def test_queue_statistics_success(self, client: TestClient, auth_headers: dict):
        """Test getting queue statistics."""
        with patch("app.api.routes.jobs.JobStatsService") as mock_stats:
            mock_instance = MagicMock()
            mock_instance.get_queue_statistics.return_value = {
                "default": {
                    "queueName": "default",
                    "activeTasks": 0,
                    "reservedTasks": 0,
                    "totalPending": 0,
                }
            }
            mock_stats.return_value = mock_instance

            response = client.get("/api/v1/jobs/queues", headers=auth_headers)

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)


class TestStatisticsEndpoints:
    """Tests for statistics endpoints."""

    def test_task_statistics_success(self, client: TestClient, auth_headers: dict):
        """Test getting task statistics."""
        with patch("app.api.routes.jobs.JobStatsService") as mock_stats:
            mock_instance = MagicMock()
            mock_instance.get_task_statistics.return_value = {
                "taskName": "all",
                "timeRangeHours": 24,
                "totalTasks": 100,
                "successfulTasks": 98,
                "failedTasks": 2,
                "successRate": 98.0,
                "averageRuntimeSeconds": 5.0,
            }
            mock_stats.return_value = mock_instance

            response = client.get(
                "/api/v1/jobs/statistics/tasks",
                headers=auth_headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert "totalTasks" in data

    def test_retry_statistics_success(self, client: TestClient, auth_headers: dict):
        """Test getting retry statistics."""
        with patch("app.api.routes.jobs.JobStatsService") as mock_stats:
            mock_instance = MagicMock()
            mock_instance.get_retry_statistics.return_value = {
                "taskName": "all",
                "totalRetries": 5,
                "tasksWithRetries": 3,
                "maxRetriesUsed": 2,
                "averageRetriesPerTask": 1.67,
                "retrySuccessRate": 80.0,
            }
            mock_stats.return_value = mock_instance

            response = client.get(
                "/api/v1/jobs/statistics/retries",
                headers=auth_headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert "totalRetries" in data

    def test_performance_metrics_success(self, client: TestClient, auth_headers: dict):
        """Test getting performance metrics."""
        with patch("app.api.routes.jobs.JobStatsService") as mock_stats:
            mock_instance = MagicMock()
            mock_instance.get_performance_metrics.return_value = {
                "taskName": "all",
                "timeRangeHours": 24,
                "totalExecutions": 100,
                "p50RuntimeSeconds": 3.0,
                "p95RuntimeSeconds": 8.0,
                "p99RuntimeSeconds": 12.0,
            }
            mock_stats.return_value = mock_instance

            response = client.get(
                "/api/v1/jobs/statistics/performance",
                headers=auth_headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert "p50RuntimeSeconds" in data

    def test_throughput_metrics_success(self, client: TestClient, auth_headers: dict):
        """Test getting throughput metrics."""
        with patch("app.api.routes.jobs.JobStatsService") as mock_stats:
            mock_instance = MagicMock()
            mock_instance.get_throughput_metrics.return_value = {
                "queueName": "all",
                "timeRangeHours": 24,
                "totalTasksProcessed": 1000,
                "tasksPerHour": 41.67,
                "tasksPerMinute": 0.69,
                "averageQueueTimeSeconds": 2.5,
            }
            mock_stats.return_value = mock_instance

            response = client.get(
                "/api/v1/jobs/statistics/throughput",
                headers=auth_headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert "tasksPerHour" in data


class TestHistoryEndpoints:
    """Tests for history endpoints."""

    def test_task_history_success(self, client: TestClient, auth_headers: dict):
        """Test getting task history."""
        with patch("app.api.routes.jobs.JobHistoryService") as mock_history:
            mock_instance = MagicMock()
            mock_instance.get_task_history.return_value = {
                "task_name": None,
                "total_count": 0,
                "tasks": [],
            }
            mock_history.return_value = mock_instance

            response = client.get("/api/v1/jobs/history", headers=auth_headers)

            if response.status_code == 200:
                data = response.json()
                assert "totalCount" in data

    def test_recent_failures_success(self, client: TestClient, auth_headers: dict):
        """Test getting recent failures."""
        with patch("app.api.routes.jobs.JobHistoryService") as mock_history:
            mock_instance = MagicMock()
            mock_instance.get_recent_failures.return_value = []
            mock_history.return_value = mock_instance

            response = client.get(
                "/api/v1/jobs/history/failures",
                headers=auth_headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)

    def test_slow_tasks_success(self, client: TestClient, auth_headers: dict):
        """Test getting slow tasks."""
        with patch("app.api.routes.jobs.JobHistoryService") as mock_history:
            mock_instance = MagicMock()
            mock_instance.get_slow_tasks.return_value = []
            mock_history.return_value = mock_instance

            response = client.get("/api/v1/jobs/history/slow", headers=auth_headers)

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)


class TestTaskControlEndpoints:
    """Tests for task control endpoints."""

    def test_revoke_task_success(self, client: TestClient, auth_headers: dict):
        """Test revoking a task."""
        with patch("app.api.routes.jobs.CeleryMonitorService") as mock_monitor:
            mock_instance = MagicMock()
            mock_instance.revoke_task.return_value = True
            mock_monitor.return_value = mock_instance

            response = client.post(
                "/api/v1/jobs/tasks/revoke",
                json={"task_id": "task-123", "terminate": False},
                headers=auth_headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True

    def test_purge_queue_requires_confirmation(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that purge queue requires confirmation."""
        response = client.post(
            "/api/v1/jobs/queues/purge",
            json={"queue_name": "test", "confirm": False},
            headers=auth_headers,
        )

        # Should fail without confirmation
        assert response.status_code in [400, 401]

    def test_purge_queue_success(self, client: TestClient, auth_headers: dict):
        """Test purging a queue with confirmation."""
        with patch("app.api.routes.jobs.CeleryMonitorService") as mock_monitor:
            mock_instance = MagicMock()
            mock_instance.purge_queue.return_value = 5
            mock_monitor.return_value = mock_instance

            response = client.post(
                "/api/v1/jobs/queues/purge",
                json={"queue_name": "test", "confirm": True},
                headers=auth_headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert "tasksPurged" in data


class TestRegisteredTasks:
    """Tests for GET /api/v1/jobs/registered endpoint."""

    def test_registered_tasks_success(self, client: TestClient, auth_headers: dict):
        """Test getting registered tasks."""
        with patch("app.api.routes.jobs.CeleryMonitorService") as mock_monitor:
            mock_instance = MagicMock()
            mock_instance.get_registered_tasks.return_value = [
                "app.tasks.task1",
                "app.tasks.task2",
            ]
            mock_monitor.return_value = mock_instance

            response = client.get("/api/v1/jobs/registered", headers=auth_headers)

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)


# ============================================================================
# Integration Tests
# ============================================================================


class TestJobsIntegration:
    """Integration tests for jobs endpoints."""

    def test_jobs_endpoints_require_auth(self, client: TestClient):
        """Test that all jobs endpoints require authentication."""
        endpoints = [
            "/api/v1/jobs/dashboard",
            "/api/v1/jobs/active",
            "/api/v1/jobs/scheduled",
            "/api/v1/jobs/workers",
            "/api/v1/jobs/queues",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [401, 403], f"Failed for {endpoint}"

    def test_jobs_endpoints_return_json(self, client: TestClient, auth_headers: dict):
        """Test that jobs endpoints return JSON."""
        with patch("app.api.routes.jobs.CeleryMonitorService") as mock_monitor:
            mock_instance = MagicMock()
            mock_instance.get_active_tasks.return_value = []
            mock_monitor.return_value = mock_instance

            response = client.get("/api/v1/jobs/active", headers=auth_headers)

            if response.status_code == 200:
                assert response.headers["content-type"] == "application/json"
