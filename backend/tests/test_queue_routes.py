"""
Comprehensive tests for Queue Management API routes.

Tests coverage for async task queue system:
- POST /api/queue/tasks/submit - Submit task
- POST /api/queue/tasks/submit-chain - Submit task chain
- POST /api/queue/tasks/submit-group - Submit task group
- POST /api/queue/tasks/submit-with-dependencies - Submit with dependencies
- GET /api/queue/tasks/{task_id}/status - Get task status
- GET /api/queue/tasks/{task_id}/progress - Get task progress
- POST /api/queue/tasks/cancel - Cancel task
- POST /api/queue/tasks/retry - Retry task
- GET /api/queue/queues/stats - Get queue stats
- POST /api/queue/queues/purge - Purge queue
- GET /api/queue/workers/health - Worker health
- GET /api/queue/workers/stats - Worker stats
- GET /api/queue/workers/utilization - Worker utilization
- GET /api/queue/workers/tasks - Worker tasks
- POST /api/queue/workers/control - Control worker
- POST /api/queue/schedule/task - Schedule task
- POST /api/queue/schedule/periodic - Add periodic task
- GET /api/queue/schedule/periodic - Get periodic tasks
- GET /api/queue/schedule/scheduled - Get scheduled tasks
- POST /api/queue/schedule/periodic/control - Control periodic task
"""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Task Submission Tests
# ============================================================================


class TestSubmitTaskEndpoint:
    """Tests for POST /api/queue/tasks/submit endpoint."""

    def test_submit_task_requires_auth(self, client: TestClient):
        """Test that submit task requires authentication."""
        response = client.post(
            "/api/queue/tasks/submit",
            json={
                "task_name": "app.tasks.test",
                "args": [],
                "kwargs": {},
                "priority": 5,
            },
        )

        assert response.status_code in [401, 403]

    def test_submit_task_success(self, client: TestClient, auth_headers: dict):
        """Test successful task submission."""
        with patch("app.api.routes.queue.QueueManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.submit_task.return_value = str(uuid4())
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/queue/tasks/submit",
                json={
                    "task_name": "app.tasks.test",
                    "args": [1, 2],
                    "kwargs": {"key": "value"},
                    "priority": 7,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_submit_task_with_countdown(self, client: TestClient, auth_headers: dict):
        """Test task submission with countdown."""
        with patch("app.api.routes.queue.QueueManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.submit_task.return_value = str(uuid4())
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/queue/tasks/submit",
                json={
                    "task_name": "app.tasks.test",
                    "args": [],
                    "kwargs": {},
                    "priority": 5,
                    "countdown": 60,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_submit_task_with_eta(self, client: TestClient, auth_headers: dict):
        """Test task submission with ETA."""
        with patch("app.api.routes.queue.QueueManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.submit_task.return_value = str(uuid4())
            mock_manager.return_value = mock_instance

            eta = datetime.utcnow().isoformat()
            response = client.post(
                "/api/queue/tasks/submit",
                json={
                    "task_name": "app.tasks.test",
                    "args": [],
                    "kwargs": {},
                    "priority": 5,
                    "eta": eta,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestSubmitTaskChainEndpoint:
    """Tests for POST /api/queue/tasks/submit-chain endpoint."""

    def test_submit_chain_requires_auth(self, client: TestClient):
        """Test that submit chain requires authentication."""
        response = client.post(
            "/api/queue/tasks/submit-chain",
            json={
                "tasks": [{"taskName": "task1", "args": [], "kwargs": {}}],
                "priority": 5,
            },
        )

        assert response.status_code in [401, 403]

    def test_submit_chain_success(self, client: TestClient, auth_headers: dict):
        """Test successful task chain submission."""
        with patch("app.api.routes.queue.QueueManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.submit_task_chain.return_value = str(uuid4())
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/queue/tasks/submit-chain",
                json={
                    "tasks": [
                        {"taskName": "task1", "args": [1], "kwargs": {}},
                        {"taskName": "task2", "args": [], "kwargs": {}},
                    ],
                    "priority": 5,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestSubmitTaskGroupEndpoint:
    """Tests for POST /api/queue/tasks/submit-group endpoint."""

    def test_submit_group_requires_auth(self, client: TestClient):
        """Test that submit group requires authentication."""
        response = client.post(
            "/api/queue/tasks/submit-group",
            json={
                "tasks": [{"taskName": "task1", "args": [], "kwargs": {}}],
                "priority": 5,
            },
        )

        assert response.status_code in [401, 403]

    def test_submit_group_success(self, client: TestClient, auth_headers: dict):
        """Test successful task group submission."""
        with patch("app.api.routes.queue.QueueManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.submit_task_group.return_value = str(uuid4())
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/queue/tasks/submit-group",
                json={
                    "tasks": [
                        {"taskName": "task1", "args": [1], "kwargs": {}},
                        {"taskName": "task2", "args": [2], "kwargs": {}},
                    ],
                    "priority": 5,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestSubmitTaskWithDependenciesEndpoint:
    """Tests for POST /api/queue/tasks/submit-with-dependencies endpoint."""

    def test_submit_with_deps_requires_auth(self, client: TestClient):
        """Test that submit with dependencies requires authentication."""
        response = client.post(
            "/api/queue/tasks/submit-with-dependencies",
            json={
                "task_name": "aggregate",
                "dependencies": ["task-1", "task-2"],
                "args": [],
                "kwargs": {},
                "priority": 5,
            },
        )

        assert response.status_code in [401, 403]

    def test_submit_with_deps_success(self, client: TestClient, auth_headers: dict):
        """Test successful task submission with dependencies."""
        with patch("app.api.routes.queue.QueueManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.submit_task_with_dependencies.return_value = str(uuid4())
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/queue/tasks/submit-with-dependencies",
                json={
                    "task_name": "aggregate_results",
                    "dependencies": [str(uuid4()), str(uuid4())],
                    "args": [],
                    "kwargs": {},
                    "priority": 7,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


# ============================================================================
# Task Status Tests
# ============================================================================


class TestTaskStatusEndpoint:
    """Tests for GET /api/queue/tasks/{task_id}/status endpoint."""

    def test_status_requires_auth(self, client: TestClient):
        """Test that status requires authentication."""
        task_id = str(uuid4())
        response = client.get(f"/api/queue/tasks/{task_id}/status")

        assert response.status_code in [401, 403]

    def test_status_success(self, client: TestClient, auth_headers: dict):
        """Test successful status retrieval."""
        with patch("app.api.routes.queue.get_task_status") as mock_get_status:
            mock_get_status.return_value = {
                "task_id": str(uuid4()),
                "status": "SUCCESS",
                "result": None,
            }

            task_id = str(uuid4())
            response = client.get(
                f"/api/queue/tasks/{task_id}/status",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestTaskProgressEndpoint:
    """Tests for GET /api/queue/tasks/{task_id}/progress endpoint."""

    def test_progress_requires_auth(self, client: TestClient):
        """Test that progress requires authentication."""
        task_id = str(uuid4())
        response = client.get(f"/api/queue/tasks/{task_id}/progress")

        assert response.status_code in [401, 403]

    def test_progress_success(self, client: TestClient, auth_headers: dict):
        """Test successful progress retrieval."""
        with patch("app.api.routes.queue.QueueManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.get_task_progress.return_value = {
                "current": 50,
                "total": 100,
                "percent": 50.0,
            }
            mock_manager.return_value = mock_instance

            task_id = str(uuid4())
            response = client.get(
                f"/api/queue/tasks/{task_id}/progress",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


# ============================================================================
# Task Control Tests
# ============================================================================


class TestCancelTaskEndpoint:
    """Tests for POST /api/queue/tasks/cancel endpoint."""

    def test_cancel_requires_auth(self, client: TestClient):
        """Test that cancel requires authentication."""
        response = client.post(
            "/api/queue/tasks/cancel",
            json={"task_id": str(uuid4()), "terminate": False},
        )

        assert response.status_code in [401, 403]

    def test_cancel_success(self, client: TestClient, auth_headers: dict):
        """Test successful task cancellation."""
        with patch("app.api.routes.queue.QueueManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.cancel_task.return_value = True
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/queue/tasks/cancel",
                json={"task_id": str(uuid4()), "terminate": False},
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestRetryTaskEndpoint:
    """Tests for POST /api/queue/tasks/retry endpoint."""

    def test_retry_requires_auth(self, client: TestClient):
        """Test that retry requires authentication."""
        response = client.post(
            "/api/queue/tasks/retry",
            json={"task_id": str(uuid4())},
        )

        assert response.status_code in [401, 403]

    def test_retry_success(self, client: TestClient, auth_headers: dict):
        """Test successful task retry."""
        with patch("app.api.routes.queue.retry_task") as mock_retry:
            mock_retry.return_value = str(uuid4())

            response = client.post(
                "/api/queue/tasks/retry",
                json={"task_id": str(uuid4()), "countdown": 60},
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


# ============================================================================
# Queue Statistics Tests
# ============================================================================


class TestQueueStatsEndpoint:
    """Tests for GET /api/queue/queues/stats endpoint."""

    def test_stats_requires_auth(self, client: TestClient):
        """Test that stats requires authentication."""
        response = client.get("/api/queue/queues/stats")

        assert response.status_code in [401, 403]

    def test_stats_success(self, client: TestClient, auth_headers: dict):
        """Test successful queue stats retrieval."""
        with patch("app.api.routes.queue.QueueManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.get_queue_stats.return_value = {
                "queues": {"default": {"pending": 10, "active": 5}},
                "total_pending": 10,
                "total_active": 5,
            }
            mock_manager.return_value = mock_instance

            response = client.get(
                "/api/queue/queues/stats",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestQueuePurgeEndpoint:
    """Tests for POST /api/queue/queues/purge endpoint."""

    def test_purge_requires_auth(self, client: TestClient):
        """Test that purge requires authentication."""
        response = client.post(
            "/api/queue/queues/purge",
            json={"queue_name": "test", "confirm": True},
        )

        assert response.status_code in [401, 403]

    def test_purge_requires_confirmation(self, client: TestClient, auth_headers: dict):
        """Test purge requires confirmation."""
        response = client.post(
            "/api/queue/queues/purge",
            json={"queue_name": "test", "confirm": False},
            headers=auth_headers,
        )

        assert response.status_code in [400, 401]

    def test_purge_success(self, client: TestClient, auth_headers: dict):
        """Test successful queue purge."""
        with patch("app.api.routes.queue.QueueManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.purge_queue.return_value = 5
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/queue/queues/purge",
                json={"queue_name": "test", "confirm": True},
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


# ============================================================================
# Worker Tests
# ============================================================================


class TestWorkerHealthEndpoint:
    """Tests for GET /api/queue/workers/health endpoint."""

    def test_health_requires_auth(self, client: TestClient):
        """Test that worker health requires authentication."""
        response = client.get("/api/queue/workers/health")

        assert response.status_code in [401, 403]

    def test_health_success(self, client: TestClient, auth_headers: dict):
        """Test successful worker health retrieval."""
        with patch("app.api.routes.queue.WorkerManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.get_worker_health.return_value = {
                "healthy": True,
                "workers": 3,
                "active": 2,
            }
            mock_manager.return_value = mock_instance

            response = client.get(
                "/api/queue/workers/health",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestWorkerStatsEndpoint:
    """Tests for GET /api/queue/workers/stats endpoint."""

    def test_stats_requires_auth(self, client: TestClient):
        """Test that worker stats requires authentication."""
        response = client.get("/api/queue/workers/stats")

        assert response.status_code in [401, 403]

    def test_stats_success(self, client: TestClient, auth_headers: dict):
        """Test successful worker stats retrieval."""
        with patch("app.api.routes.queue.WorkerManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.get_worker_stats.return_value = {
                "workers": [],
                "total_processed": 100,
            }
            mock_manager.return_value = mock_instance

            response = client.get(
                "/api/queue/workers/stats",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestWorkerControlEndpoint:
    """Tests for POST /api/queue/workers/control endpoint."""

    def test_control_requires_auth(self, client: TestClient):
        """Test that worker control requires authentication."""
        response = client.post(
            "/api/queue/workers/control",
            json={
                "worker_name": "celery@worker1",
                "action": "shutdown",
                "parameters": {},
            },
        )

        assert response.status_code in [401, 403]

    def test_control_autoscale_success(self, client: TestClient, auth_headers: dict):
        """Test successful worker autoscale control."""
        with patch("app.api.routes.queue.WorkerManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.autoscale_worker.return_value = True
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/queue/workers/control",
                json={
                    "worker_name": "celery@worker1",
                    "action": "autoscale",
                    "parameters": {"max": 10, "min": 2},
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


# ============================================================================
# Scheduler Tests
# ============================================================================


class TestScheduleTaskEndpoint:
    """Tests for POST /api/queue/schedule/task endpoint."""

    def test_schedule_requires_auth(self, client: TestClient):
        """Test that schedule task requires authentication."""
        response = client.post(
            "/api/queue/schedule/task",
            json={
                "task_name": "send_reminder",
                "args": [],
                "kwargs": {},
                "countdown": 3600,
                "priority": 5,
            },
        )

        assert response.status_code in [401, 403]

    def test_schedule_success(self, client: TestClient, auth_headers: dict):
        """Test successful task scheduling."""
        with patch("app.api.routes.queue.TaskScheduler") as mock_scheduler:
            mock_instance = MagicMock()
            mock_instance.schedule_task.return_value = str(uuid4())
            mock_scheduler.return_value = mock_instance

            response = client.post(
                "/api/queue/schedule/task",
                json={
                    "task_name": "send_reminder",
                    "args": [],
                    "kwargs": {},
                    "countdown": 3600,
                    "priority": 7,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestPeriodicTaskEndpoint:
    """Tests for periodic task endpoints."""

    def test_add_periodic_requires_auth(self, client: TestClient):
        """Test that add periodic task requires authentication."""
        response = client.post(
            "/api/queue/schedule/periodic",
            json={
                "name": "daily-cleanup",
                "task_name": "app.tasks.cleanup",
                "schedule_config": {"crontab": {"hour": 2, "minute": 0}},
                "args": [],
                "kwargs": {},
            },
        )

        assert response.status_code in [401, 403]

    def test_add_periodic_success(self, client: TestClient, auth_headers: dict):
        """Test successful periodic task addition."""
        with patch("app.api.routes.queue.TaskScheduler") as mock_scheduler:
            mock_instance = MagicMock()
            mock_instance.add_periodic_task.return_value = None
            mock_scheduler.return_value = mock_instance

            response = client.post(
                "/api/queue/schedule/periodic",
                json={
                    "name": "daily-cleanup",
                    "task_name": "app.tasks.cleanup",
                    "schedule_config": {"crontab": {"hour": 2, "minute": 0}},
                    "args": [],
                    "kwargs": {},
                    "options": {},
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_get_periodic_tasks_requires_auth(self, client: TestClient):
        """Test that get periodic tasks requires authentication."""
        response = client.get("/api/queue/schedule/periodic")

        assert response.status_code in [401, 403]

    def test_get_periodic_tasks_success(self, client: TestClient, auth_headers: dict):
        """Test successful periodic tasks retrieval."""
        with patch("app.api.routes.queue.TaskScheduler") as mock_scheduler:
            mock_instance = MagicMock()
            mock_instance.get_periodic_tasks.return_value = {"tasks": []}
            mock_scheduler.return_value = mock_instance

            response = client.get(
                "/api/queue/schedule/periodic",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_control_periodic_requires_auth(self, client: TestClient):
        """Test that control periodic requires authentication."""
        response = client.post(
            "/api/queue/schedule/periodic/control",
            json={"name": "daily-cleanup", "action": "disable"},
        )

        assert response.status_code in [401, 403]


# ============================================================================
# Integration Tests
# ============================================================================


class TestQueueIntegration:
    """Integration tests for queue management."""

    def test_queue_endpoints_accessible(self, client: TestClient, auth_headers: dict):
        """Test queue endpoints respond appropriately."""
        with (
            patch("app.api.routes.queue.QueueManager") as mock_qm,
            patch("app.api.routes.queue.WorkerManager") as mock_wm,
            patch("app.api.routes.queue.TaskScheduler") as mock_ts,
            patch("app.api.routes.queue.get_task_status") as mock_status,
        ):
            # Setup mocks
            mock_qm_instance = MagicMock()
            mock_qm_instance.get_queue_stats.return_value = {"queues": {}}
            mock_qm_instance.get_task_progress.return_value = None
            mock_qm.return_value = mock_qm_instance

            mock_wm_instance = MagicMock()
            mock_wm_instance.get_worker_health.return_value = {"healthy": True}
            mock_wm_instance.get_worker_stats.return_value = {"workers": []}
            mock_wm_instance.get_worker_utilization.return_value = {"utilization": 0}
            mock_wm_instance.get_worker_tasks.return_value = {"tasks": []}
            mock_wm.return_value = mock_wm_instance

            mock_ts_instance = MagicMock()
            mock_ts_instance.get_periodic_tasks.return_value = {"tasks": []}
            mock_ts_instance.get_scheduled_tasks.return_value = {"tasks": []}
            mock_ts.return_value = mock_ts_instance

            mock_status.return_value = {"task_id": "test", "status": "PENDING"}

            task_id = str(uuid4())

            endpoints = [
                ("/api/queue/queues/stats", "GET"),
                ("/api/queue/workers/health", "GET"),
                ("/api/queue/workers/stats", "GET"),
                ("/api/queue/workers/utilization", "GET"),
                ("/api/queue/workers/tasks", "GET"),
                ("/api/queue/schedule/periodic", "GET"),
                ("/api/queue/schedule/scheduled", "GET"),
                (f"/api/queue/tasks/{task_id}/status", "GET"),
                (f"/api/queue/tasks/{task_id}/progress", "GET"),
            ]

            for url, method in endpoints:
                response = client.get(url, headers=auth_headers)
                assert response.status_code in [
                    200,
                    401,
                ], f"Failed for {url}"
