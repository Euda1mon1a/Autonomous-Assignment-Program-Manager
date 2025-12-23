"""Tests for background job monitoring API routes.

Tests the Celery background task monitoring including:
- Dashboard overview
- Active/scheduled/reserved tasks
- Task details and history
- Worker statistics and health
- Queue statistics
- Task revocation and queue purging
"""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


class TestJobsRoutes:
    """Test suite for jobs monitoring API endpoints."""

    # ========================================================================
    # Authentication Tests
    # ========================================================================

    def test_dashboard_requires_auth(self, client: TestClient):
        """Test that dashboard requires authentication."""
        response = client.get("/api/jobs/dashboard")
        assert response.status_code == 401

    def test_active_tasks_requires_auth(self, client: TestClient):
        """Test that active tasks requires authentication."""
        response = client.get("/api/jobs/active")
        assert response.status_code == 401

    def test_workers_requires_auth(self, client: TestClient):
        """Test that workers endpoint requires authentication."""
        response = client.get("/api/jobs/workers")
        assert response.status_code == 401

    def test_queues_requires_auth(self, client: TestClient):
        """Test that queues endpoint requires authentication."""
        response = client.get("/api/jobs/queues")
        assert response.status_code == 401

    def test_task_statistics_requires_auth(self, client: TestClient):
        """Test that task statistics requires authentication."""
        response = client.get("/api/jobs/statistics/tasks")
        assert response.status_code == 401

    def test_revoke_task_requires_auth(self, client: TestClient):
        """Test that task revocation requires authentication."""
        response = client.post(
            "/api/jobs/tasks/revoke",
            json={"task_id": str(uuid4())},
        )
        assert response.status_code == 401

    # ========================================================================
    # Dashboard Tests
    # ========================================================================

    @patch("app.api.routes.jobs.JobStatsService")
    @patch("app.api.routes.jobs.CeleryMonitorService")
    def test_dashboard_overview_success(
        self,
        mock_monitor_service: MagicMock,
        mock_stats_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting dashboard overview."""
        mock_monitor = MagicMock()
        mock_monitor.get_active_tasks.return_value = [{"task_id": "1"}]
        mock_monitor.get_scheduled_tasks.return_value = []
        mock_monitor.get_reserved_tasks.return_value = [{"task_id": "2"}, {"task_id": "3"}]
        mock_monitor.get_worker_stats.return_value = {
            "total_workers": 4,
            "online_workers": 4,
        }
        mock_monitor.get_queue_lengths.return_value = {"default": 5, "resilience": 3}
        mock_monitor_service.return_value = mock_monitor

        mock_stats = MagicMock()
        mock_stats.get_worker_utilization.return_value = {
            "average_utilization_percentage": 62.5,
        }
        mock_stats_service.return_value = mock_stats

        response = client.get("/api/jobs/dashboard", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["activeTasksCount"] == 1
        assert data["reservedTasksCount"] == 2
        assert data["totalWorkers"] == 4

    # ========================================================================
    # Active Tasks Tests
    # ========================================================================

    @patch("app.api.routes.jobs.CeleryMonitorService")
    def test_get_active_tasks_success(
        self,
        mock_monitor_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting active tasks."""
        mock_monitor = MagicMock()
        mock_monitor.get_active_tasks.return_value = [
            {
                "task_id": "abc-123",
                "task_name": "app.tasks.process",
                "worker": "celery@worker1",
                "queue": "default",
                "time_start": 1705315200.0,
                "acknowledged": True,
            }
        ]
        mock_monitor_service.return_value = mock_monitor

        response = client.get("/api/jobs/active", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["taskId"] == "abc-123"

    @patch("app.api.routes.jobs.CeleryMonitorService")
    def test_get_active_tasks_with_queue_filter(
        self,
        mock_monitor_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting active tasks filtered by queue."""
        mock_monitor = MagicMock()
        mock_monitor.get_active_tasks.return_value = []
        mock_monitor_service.return_value = mock_monitor

        response = client.get(
            "/api/jobs/active?queue=resilience",
            headers=auth_headers,
        )
        assert response.status_code == 200
        mock_monitor.get_active_tasks.assert_called_with(queue_name="resilience")

    @patch("app.api.routes.jobs.CeleryMonitorService")
    def test_get_scheduled_tasks_success(
        self,
        mock_monitor_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting scheduled tasks."""
        mock_monitor = MagicMock()
        mock_monitor.get_scheduled_tasks.return_value = [
            {
                "task_id": "xyz-789",
                "task_name": "app.tasks.cleanup",
                "worker": "celery@worker2",
                "eta": "2024-01-15T11:00:00Z",
                "priority": 5,
            }
        ]
        mock_monitor_service.return_value = mock_monitor

        response = client.get("/api/jobs/scheduled", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1

    @patch("app.api.routes.jobs.CeleryMonitorService")
    def test_get_reserved_tasks_success(
        self,
        mock_monitor_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting reserved tasks."""
        mock_monitor = MagicMock()
        mock_monitor.get_reserved_tasks.return_value = [
            {
                "task_id": "def-456",
                "task_name": "app.notifications.send_email",
                "worker": "celery@worker1",
                "queue": "notifications",
                "priority": 3,
            }
        ]
        mock_monitor_service.return_value = mock_monitor

        response = client.get("/api/jobs/reserved", headers=auth_headers)
        assert response.status_code == 200

    # ========================================================================
    # Task Details Tests
    # ========================================================================

    @patch("app.api.routes.jobs.CeleryMonitorService")
    def test_get_task_info_success(
        self,
        mock_monitor_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting task info."""
        task_id = "abc-123-def"
        mock_monitor = MagicMock()
        mock_monitor.get_task_info.return_value = {
            "task_id": task_id,
            "task_name": "app.tasks.process",
            "state": "SUCCESS",
            "ready": True,
            "successful": True,
            "result": {"status": "done"},
        }
        mock_monitor_service.return_value = mock_monitor

        response = client.get(
            f"/api/jobs/tasks/{task_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["taskId"] == task_id
        assert data["status"] == "SUCCESS"

    @patch("app.api.routes.jobs.CeleryMonitorService")
    def test_get_task_info_not_found(
        self,
        mock_monitor_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting non-existent task info."""
        mock_monitor = MagicMock()
        mock_monitor.get_task_info.return_value = None
        mock_monitor_service.return_value = mock_monitor

        response = client.get(
            f"/api/jobs/tasks/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    # ========================================================================
    # Worker Tests
    # ========================================================================

    @patch("app.api.routes.jobs.CeleryMonitorService")
    def test_get_worker_stats_success(
        self,
        mock_monitor_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting worker statistics."""
        mock_monitor = MagicMock()
        mock_monitor.get_worker_stats.return_value = {
            "total_workers": 4,
            "online_workers": 4,
            "workers": [
                {
                    "name": "celery@worker1",
                    "status": "online",
                    "pool": "prefork",
                    "max_concurrency": 4,
                }
            ],
        }
        mock_monitor_service.return_value = mock_monitor

        response = client.get("/api/jobs/workers", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["totalWorkers"] == 4

    @patch("app.api.routes.jobs.CeleryMonitorService")
    def test_get_worker_health_success(
        self,
        mock_monitor_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting worker health."""
        mock_monitor = MagicMock()
        mock_monitor.get_worker_health.return_value = {
            "healthy": True,
            "totalWorkers": 4,
            "onlineWorkers": 4,
            "offlineWorkers": 0,
            "workers": ["celery@worker1"],
            "timestamp": datetime.utcnow().isoformat(),
        }
        mock_monitor_service.return_value = mock_monitor

        response = client.get("/api/jobs/workers/health", headers=auth_headers)
        assert response.status_code == 200

    @patch("app.api.routes.jobs.JobStatsService")
    def test_get_worker_utilization_success(
        self,
        mock_stats_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting worker utilization."""
        mock_stats = MagicMock()
        mock_stats.get_worker_utilization.return_value = {
            "totalWorkers": 4,
            "activeWorkers": 3,
            "idleWorkers": 1,
            "averageUtilizationPercentage": 75.0,
            "tasksPerWorker": 1.25,
            "timestamp": datetime.utcnow().isoformat(),
        }
        mock_stats_service.return_value = mock_stats

        response = client.get("/api/jobs/workers/utilization", headers=auth_headers)
        assert response.status_code == 200

    # ========================================================================
    # Queue Statistics Tests
    # ========================================================================

    @patch("app.api.routes.jobs.JobStatsService")
    def test_get_queue_statistics_success(
        self,
        mock_stats_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting queue statistics."""
        mock_stats = MagicMock()
        mock_stats.get_queue_statistics.return_value = {
            "resilience": {
                "queueName": "resilience",
                "activeTasks": 2,
                "reservedTasks": 5,
                "totalPending": 7,
            },
            "metrics": {
                "queueName": "metrics",
                "activeTasks": 1,
                "reservedTasks": 3,
                "totalPending": 4,
            },
        }
        mock_stats_service.return_value = mock_stats

        response = client.get("/api/jobs/queues", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "resilience" in data

    # ========================================================================
    # Statistics Tests
    # ========================================================================

    @patch("app.api.routes.jobs.JobStatsService")
    def test_get_task_statistics_success(
        self,
        mock_stats_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting task statistics."""
        mock_stats = MagicMock()
        mock_stats.get_task_statistics.return_value = {
            "taskName": "all",
            "timeRangeHours": 24,
            "totalTasks": 96,
            "successfulTasks": 95,
            "failedTasks": 1,
            "successRate": 98.96,
            "averageRuntimeSeconds": 5.2,
        }
        mock_stats_service.return_value = mock_stats

        response = client.get(
            "/api/jobs/statistics/tasks?hours=24",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @patch("app.api.routes.jobs.JobStatsService")
    def test_get_retry_statistics_success(
        self,
        mock_stats_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting retry statistics."""
        mock_stats = MagicMock()
        mock_stats.get_retry_statistics.return_value = {
            "taskName": "all",
            "totalRetries": 15,
            "tasksWithRetries": 8,
            "maxRetriesUsed": 3,
            "averageRetriesPerTask": 1.88,
            "retrySuccessRate": 87.5,
        }
        mock_stats_service.return_value = mock_stats

        response = client.get("/api/jobs/statistics/retries", headers=auth_headers)
        assert response.status_code == 200

    @patch("app.api.routes.jobs.JobStatsService")
    def test_get_performance_metrics_success(
        self,
        mock_stats_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting performance metrics."""
        mock_stats = MagicMock()
        mock_stats.get_performance_metrics.return_value = {
            "taskName": "all",
            "timeRangeHours": 24,
            "totalExecutions": 24,
            "p50RuntimeSeconds": 3.2,
            "p95RuntimeSeconds": 5.8,
            "p99RuntimeSeconds": 7.1,
        }
        mock_stats_service.return_value = mock_stats

        response = client.get("/api/jobs/statistics/performance", headers=auth_headers)
        assert response.status_code == 200

    @patch("app.api.routes.jobs.JobStatsService")
    def test_get_throughput_metrics_success(
        self,
        mock_stats_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting throughput metrics."""
        mock_stats = MagicMock()
        mock_stats.get_throughput_metrics.return_value = {
            "queueName": "all",
            "timeRangeHours": 24,
            "totalTasksProcessed": 96,
            "tasksPerHour": 4.0,
            "tasksPerMinute": 0.067,
            "averageQueueTimeSeconds": 2.5,
        }
        mock_stats_service.return_value = mock_stats

        response = client.get("/api/jobs/statistics/throughput", headers=auth_headers)
        assert response.status_code == 200

    # ========================================================================
    # History Tests
    # ========================================================================

    @patch("app.api.routes.jobs.JobHistoryService")
    def test_get_task_history_success(
        self,
        mock_history_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting task history."""
        mock_history = MagicMock()
        mock_history.get_task_history.return_value = {
            "task_name": None,
            "total_count": 100,
            "tasks": [],
            "filters": {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        mock_history_service.return_value = mock_history

        response = client.get("/api/jobs/history?limit=50", headers=auth_headers)
        assert response.status_code == 200

    @patch("app.api.routes.jobs.JobHistoryService")
    def test_get_recent_failures_success(
        self,
        mock_history_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting recent failures."""
        mock_history = MagicMock()
        mock_history.get_recent_failures.return_value = [
            {
                "taskId": "failed-123",
                "taskName": "app.tasks.process",
                "failedAt": datetime.utcnow().isoformat(),
                "errorType": "ValueError",
                "errorMessage": "Invalid input",
            }
        ]
        mock_history_service.return_value = mock_history

        response = client.get("/api/jobs/history/failures?limit=10", headers=auth_headers)
        assert response.status_code == 200

    @patch("app.api.routes.jobs.JobHistoryService")
    def test_get_slow_tasks_success(
        self,
        mock_history_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting slow tasks."""
        mock_history = MagicMock()
        mock_history.get_slow_tasks.return_value = [
            {
                "taskId": "slow-123",
                "taskName": "app.tasks.heavy_process",
                "runtimeSeconds": 125.5,
                "startedAt": datetime.utcnow().isoformat(),
            }
        ]
        mock_history_service.return_value = mock_history

        response = client.get(
            "/api/jobs/history/slow?threshold=30.0",
            headers=auth_headers,
        )
        assert response.status_code == 200

    # ========================================================================
    # Task Control Tests
    # ========================================================================

    @patch("app.api.routes.jobs.CeleryMonitorService")
    def test_revoke_task_success(
        self,
        mock_monitor_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test revoking a task."""
        task_id = str(uuid4())
        mock_monitor = MagicMock()
        mock_monitor.revoke_task.return_value = True
        mock_monitor_service.return_value = mock_monitor

        response = client.post(
            "/api/jobs/tasks/revoke",
            headers=auth_headers,
            json={"task_id": task_id, "terminate": False},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    @patch("app.api.routes.jobs.CeleryMonitorService")
    def test_purge_queue_requires_confirm(
        self,
        mock_monitor_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test queue purge requires confirmation."""
        response = client.post(
            "/api/jobs/queues/purge",
            headers=auth_headers,
            json={"queue_name": "test", "confirm": False},
        )
        assert response.status_code == 400

    @patch("app.api.routes.jobs.CeleryMonitorService")
    def test_purge_queue_success(
        self,
        mock_monitor_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful queue purge."""
        mock_monitor = MagicMock()
        mock_monitor.purge_queue.return_value = 25
        mock_monitor_service.return_value = mock_monitor

        response = client.post(
            "/api/jobs/queues/purge",
            headers=auth_headers,
            json={"queue_name": "test_queue", "confirm": True},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["tasksPurged"] == 25

    # ========================================================================
    # Registered Tasks Tests
    # ========================================================================

    @patch("app.api.routes.jobs.CeleryMonitorService")
    def test_get_registered_tasks_success(
        self,
        mock_monitor_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting registered tasks."""
        mock_monitor = MagicMock()
        mock_monitor.get_registered_tasks.return_value = [
            "app.resilience.tasks.periodic_health_check",
            "app.tasks.schedule_metrics",
        ]
        mock_monitor_service.return_value = mock_monitor

        response = client.get("/api/jobs/registered", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2

    # ========================================================================
    # Scheduled Tasks Summary Tests
    # ========================================================================

    @patch("app.api.routes.jobs.JobStatsService")
    def test_get_scheduled_tasks_summary_success(
        self,
        mock_stats_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting scheduled tasks summary."""
        mock_stats = MagicMock()
        mock_stats.get_scheduled_tasks_summary.return_value = {
            "total_scheduled_tasks": 8,
            "scheduled_tasks": [
                {
                    "name": "resilience-health-check",
                    "task": "app.resilience.tasks.periodic_health_check",
                    "schedule": "crontab(minute='*/15')",
                    "options": {"queue": "resilience"},
                }
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }
        mock_stats_service.return_value = mock_stats

        response = client.get("/api/jobs/scheduled-tasks", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["totalScheduledTasks"] == 8
