"""Tests for queue management API routes.

Tests the async task queue system including:
- Task submission (single, chain, group, dependencies)
- Task status and progress monitoring
- Task control (cancel, retry)
- Queue statistics and purging
- Worker management
- Scheduled and periodic tasks
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


class TestQueueRoutes:
    """Test suite for queue management API endpoints."""

    # ========================================================================
    # Authentication Tests
    # ========================================================================

    def test_submit_task_requires_auth(self, client: TestClient):
        """Test that task submission requires authentication."""
        response = client.post(
            "/api/v1/queue/tasks/submit",
            json={
                "task_name": "app.tasks.process",
                "args": [1, 2],
            },
        )
        assert response.status_code == 401

    def test_get_task_status_requires_auth(self, client: TestClient):
        """Test that task status requires authentication."""
        response = client.get(f"/api/v1/queue/tasks/{uuid4()}/status")
        assert response.status_code == 401

    def test_cancel_task_requires_auth(self, client: TestClient):
        """Test that task cancellation requires authentication."""
        response = client.post(
            "/api/v1/queue/tasks/cancel",
            json={"task_id": str(uuid4())},
        )
        assert response.status_code == 401

    def test_queue_stats_requires_auth(self, client: TestClient):
        """Test that queue stats requires authentication."""
        response = client.get("/api/v1/queue/queues/stats")
        assert response.status_code == 401

    def test_worker_health_requires_auth(self, client: TestClient):
        """Test that worker health requires authentication."""
        response = client.get("/api/v1/queue/workers/health")
        assert response.status_code == 401

    # ========================================================================
    # Task Submission Tests
    # ========================================================================

    @patch("app.api.routes.queue.QueueManager")
    def test_submit_task_success(
        self,
        mock_queue_manager: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful task submission."""
        task_id = str(uuid4())
        mock_manager = MagicMock()
        mock_manager.submit_task.return_value = task_id
        mock_queue_manager.return_value = mock_manager

        response = client.post(
            "/api/v1/queue/tasks/submit",
            headers=auth_headers,
            json={
                "task_name": "app.tasks.process_data",
                "args": [123],
                "kwargs": {"option": "value"},
                "priority": 7,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["taskId"] == task_id
        assert data["status"] == "submitted"

    @patch("app.api.routes.queue.QueueManager")
    def test_submit_task_with_countdown(
        self,
        mock_queue_manager: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test task submission with countdown."""
        task_id = str(uuid4())
        mock_manager = MagicMock()
        mock_manager.submit_task.return_value = task_id
        mock_queue_manager.return_value = mock_manager

        response = client.post(
            "/api/v1/queue/tasks/submit",
            headers=auth_headers,
            json={
                "task_name": "app.tasks.delayed_task",
                "args": [],
                "countdown": 60,
            },
        )
        assert response.status_code == 200

    @patch("app.api.routes.queue.QueueManager")
    def test_submit_task_chain_success(
        self,
        mock_queue_manager: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test submitting a task chain."""
        chain_id = str(uuid4())
        mock_manager = MagicMock()
        mock_manager.submit_task_chain.return_value = chain_id
        mock_queue_manager.return_value = mock_manager

        response = client.post(
            "/api/v1/queue/tasks/submit-chain",
            headers=auth_headers,
            json={
                "tasks": [
                    {"taskName": "app.tasks.step1", "args": [1], "kwargs": {}},
                    {"taskName": "app.tasks.step2", "args": [], "kwargs": {}},
                ],
                "priority": 5,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["taskName"] == "chain"
        assert "2 tasks" in data["message"]

    @patch("app.api.routes.queue.QueueManager")
    def test_submit_task_group_success(
        self,
        mock_queue_manager: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test submitting a task group (parallel)."""
        group_id = str(uuid4())
        mock_manager = MagicMock()
        mock_manager.submit_task_group.return_value = group_id
        mock_queue_manager.return_value = mock_manager

        response = client.post(
            "/api/v1/queue/tasks/submit-group",
            headers=auth_headers,
            json={
                "tasks": [
                    {"taskName": "app.tasks.parallel1", "args": [1]},
                    {"taskName": "app.tasks.parallel2", "args": [2]},
                ],
                "priority": 5,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["taskName"] == "group"

    @patch("app.api.routes.queue.QueueManager")
    def test_submit_task_with_dependencies(
        self,
        mock_queue_manager: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test submitting task with dependencies."""
        task_id = str(uuid4())
        mock_manager = MagicMock()
        mock_manager.submit_task_with_dependencies.return_value = task_id
        mock_queue_manager.return_value = mock_manager

        response = client.post(
            "/api/v1/queue/tasks/submit-with-dependencies",
            headers=auth_headers,
            json={
                "task_name": "app.tasks.aggregate_results",
                "dependencies": ["task-id-1", "task-id-2"],
                "priority": 7,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "2 dependencies" in data["message"]

    # ========================================================================
    # Task Status Tests
    # ========================================================================

    @patch("app.api.routes.queue.get_task_status")
    def test_get_task_status_success(
        self,
        mock_get_status: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting task status."""
        task_id = str(uuid4())
        mock_get_status.return_value = {
            "task_id": task_id,
            "state": "SUCCESS",
            "ready": True,
            "successful": True,
            "result": {"data": "processed"},
        }

        response = client.get(
            f"/api/v1/queue/tasks/{task_id}/status",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["taskId"] == task_id

    @patch("app.api.routes.queue.QueueManager")
    def test_get_task_progress_success(
        self,
        mock_queue_manager: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting task progress."""
        task_id = str(uuid4())
        mock_manager = MagicMock()
        mock_manager.get_task_progress.return_value = {
            "current": 50,
            "total": 100,
            "percentage": 50,
        }
        mock_queue_manager.return_value = mock_manager

        response = client.get(
            f"/api/v1/queue/tasks/{task_id}/progress",
            headers=auth_headers,
        )
        assert response.status_code == 200

    # ========================================================================
    # Task Control Tests
    # ========================================================================

    @patch("app.api.routes.queue.QueueManager")
    def test_cancel_task_success(
        self,
        mock_queue_manager: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test cancelling a task."""
        task_id = str(uuid4())
        mock_manager = MagicMock()
        mock_manager.cancel_task.return_value = True
        mock_queue_manager.return_value = mock_manager

        response = client.post(
            "/api/v1/queue/tasks/cancel",
            headers=auth_headers,
            json={"task_id": task_id, "terminate": False},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    @patch("app.queue.tasks.retry_task")
    def test_retry_task_success(
        self,
        mock_retry: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test retrying a failed task."""
        original_id = str(uuid4())
        new_id = str(uuid4())
        mock_retry.return_value = new_id

        response = client.post(
            "/api/v1/queue/tasks/retry",
            headers=auth_headers,
            json={"task_id": original_id, "countdown": 60},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["originalTaskId"] == original_id
        assert data["newTaskId"] == new_id

    # ========================================================================
    # Queue Statistics Tests
    # ========================================================================

    @patch("app.api.routes.queue.QueueManager")
    def test_get_queue_stats_success(
        self,
        mock_queue_manager: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting queue statistics."""
        mock_manager = MagicMock()
        mock_manager.get_queue_stats.return_value = {
            "queues": {
                "default": {"active": 5, "reserved": 10, "pending": 25},
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }
        mock_queue_manager.return_value = mock_manager

        response = client.get(
            "/api/v1/queue/queues/stats",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @patch("app.api.routes.queue.QueueManager")
    def test_purge_queue_requires_confirm(
        self,
        mock_queue_manager: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test queue purge requires confirmation."""
        response = client.post(
            "/api/v1/queue/queues/purge",
            headers=auth_headers,
            json={"queue_name": "test_queue", "confirm": False},
        )
        assert response.status_code == 400
        assert "confirmation" in response.json()["detail"].lower()

    @patch("app.api.routes.queue.QueueManager")
    def test_purge_queue_success(
        self,
        mock_queue_manager: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful queue purge."""
        mock_manager = MagicMock()
        mock_manager.purge_queue.return_value = 15
        mock_queue_manager.return_value = mock_manager

        response = client.post(
            "/api/v1/queue/queues/purge",
            headers=auth_headers,
            json={"queue_name": "test_queue", "confirm": True},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["tasksPurged"] == 15

    # ========================================================================
    # Worker Management Tests
    # ========================================================================

    @patch("app.api.routes.queue.WorkerManager")
    def test_get_worker_health_success(
        self,
        mock_worker_manager: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting worker health."""
        mock_manager = MagicMock()
        mock_manager.get_worker_health.return_value = {
            "healthy": True,
            "workers": {"celery@worker1": {"status": "online"}},
            "total_workers": 4,
            "online_workers": 4,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        mock_worker_manager.return_value = mock_manager

        response = client.get(
            "/api/v1/queue/workers/health",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @patch("app.api.routes.queue.WorkerManager")
    def test_get_worker_stats_success(
        self,
        mock_worker_manager: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting worker statistics."""
        mock_manager = MagicMock()
        mock_manager.get_worker_stats.return_value = {
            "workers": {"celery@worker1": {"active": 3}},
            "total_workers": 4,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        mock_worker_manager.return_value = mock_manager

        response = client.get(
            "/api/v1/queue/workers/stats",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @patch("app.api.routes.queue.WorkerManager")
    def test_worker_control_autoscale(
        self,
        mock_worker_manager: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test worker autoscale control."""
        mock_manager = MagicMock()
        mock_manager.autoscale_worker.return_value = True
        mock_worker_manager.return_value = mock_manager

        response = client.post(
            "/api/v1/queue/workers/control",
            headers=auth_headers,
            json={
                "worker_name": "celery@worker1",
                "action": "autoscale",
                "parameters": {"max": 10, "min": 2},
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "autoscale" in data["message"]

    @patch("app.api.routes.queue.WorkerManager")
    def test_worker_control_invalid_action(
        self,
        mock_worker_manager: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test worker control with invalid action."""
        response = client.post(
            "/api/v1/queue/workers/control",
            headers=auth_headers,
            json={
                "worker_name": "celery@worker1",
                "action": "invalid_action",
                "parameters": {},
            },
        )
        assert response.status_code == 400

    # ========================================================================
    # Scheduler Tests
    # ========================================================================

    @patch("app.api.routes.queue.TaskScheduler")
    def test_schedule_task_success(
        self,
        mock_scheduler: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test scheduling a task."""
        task_id = str(uuid4())
        mock_sched = MagicMock()
        mock_sched.schedule_task.return_value = task_id
        mock_scheduler.return_value = mock_sched

        response = client.post(
            "/api/v1/queue/schedule/task",
            headers=auth_headers,
            json={
                "task_name": "app.tasks.send_reminder",
                "countdown": 3600,
                "priority": 7,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["taskId"] == task_id

    @patch("app.api.routes.queue.TaskScheduler")
    def test_add_periodic_task_success(
        self,
        mock_scheduler: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test adding periodic task."""
        mock_sched = MagicMock()
        mock_scheduler.return_value = mock_sched

        response = client.post(
            "/api/v1/queue/schedule/periodic",
            headers=auth_headers,
            json={
                "name": "daily-cleanup",
                "task_name": "app.tasks.cleanup",
                "schedule_config": {"crontab": {"hour": 2, "minute": 0}},
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "daily-cleanup"

    @patch("app.api.routes.queue.TaskScheduler")
    def test_get_periodic_tasks_success(
        self,
        mock_scheduler: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting periodic tasks."""
        mock_sched = MagicMock()
        mock_sched.get_periodic_tasks.return_value = {
            "tasks": {
                "daily-cleanup": {"task": "app.tasks.cleanup", "schedule": "0 2 * * *"},
            },
            "total_tasks": 1,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        mock_scheduler.return_value = mock_sched

        response = client.get(
            "/api/v1/queue/schedule/periodic",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @patch("app.api.routes.queue.TaskScheduler")
    def test_control_periodic_task_disable(
        self,
        mock_scheduler: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test disabling periodic task."""
        mock_sched = MagicMock()
        mock_sched.disable_periodic_task.return_value = True
        mock_scheduler.return_value = mock_sched

        response = client.post(
            "/api/v1/queue/schedule/periodic/control",
            headers=auth_headers,
            json={"name": "daily-cleanup", "action": "disable"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "disabled" in data["message"]
