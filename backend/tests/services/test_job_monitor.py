"""Tests for CeleryMonitorService."""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from app.services.job_monitor.celery_monitor import CeleryMonitorService


class TestCeleryMonitorService:
    """Test suite for CeleryMonitorService."""

    # ========================================================================
    # Active Tasks Tests
    # ========================================================================

    @patch("app.services.job_monitor.celery_monitor.get_celery_app")
    def test_get_active_tasks_success(self, mock_get_app):
        """Test getting active tasks successfully."""
        mock_app = Mock()
        mock_inspect = Mock()
        mock_app.control.inspect.return_value = mock_inspect
        mock_inspect.active.return_value = {
            "worker1": [
                {
                    "id": "task-123",
                    "name": "app.tasks.process_schedule",
                    "args": [],
                    "kwargs": {},
                    "time_start": 1234567890,
                    "acknowledged": True,
                    "delivery_info": {"routing_key": "resilience"},
                }
            ]
        }
        mock_get_app.return_value = mock_app

        service = CeleryMonitorService()
        tasks = service.get_active_tasks()

        assert len(tasks) == 1
        assert tasks[0]["task_id"] == "task-123"
        assert tasks[0]["task_name"] == "app.tasks.process_schedule"
        assert tasks[0]["worker"] == "worker1"
        assert tasks[0]["queue"] == "resilience"

    @patch("app.services.job_monitor.celery_monitor.get_celery_app")
    def test_get_active_tasks_empty(self, mock_get_app):
        """Test getting active tasks when none exist."""
        mock_app = Mock()
        mock_inspect = Mock()
        mock_app.control.inspect.return_value = mock_inspect
        mock_inspect.active.return_value = None
        mock_get_app.return_value = mock_app

        service = CeleryMonitorService()
        tasks = service.get_active_tasks()

        assert tasks == []

    @patch("app.services.job_monitor.celery_monitor.get_celery_app")
    def test_get_active_tasks_with_queue_filter(self, mock_get_app):
        """Test filtering active tasks by queue."""
        mock_app = Mock()
        mock_inspect = Mock()
        mock_app.control.inspect.return_value = mock_inspect
        mock_inspect.active.return_value = {
            "worker1": [
                {
                    "id": "task-1",
                    "name": "task1",
                    "delivery_info": {"routing_key": "queue1"},
                },
                {
                    "id": "task-2",
                    "name": "task2",
                    "delivery_info": {"routing_key": "queue2"},
                },
            ]
        }
        mock_get_app.return_value = mock_app

        service = CeleryMonitorService()
        tasks = service.get_active_tasks(queue_name="queue1")

        assert len(tasks) == 1
        assert tasks[0]["task_id"] == "task-1"

    # ========================================================================
    # Scheduled Tasks Tests
    # ========================================================================

    @patch("app.services.job_monitor.celery_monitor.get_celery_app")
    def test_get_scheduled_tasks_success(self, mock_get_app):
        """Test getting scheduled tasks."""
        mock_app = Mock()
        mock_inspect = Mock()
        mock_app.control.inspect.return_value = mock_inspect
        mock_inspect.scheduled.return_value = {
            "worker1": [
                {
                    "request": {
                        "id": "task-456",
                        "name": "app.tasks.scheduled_task",
                        "args": [],
                        "kwargs": {},
                    },
                    "eta": "2025-01-01T12:00:00",
                    "priority": 5,
                }
            ]
        }
        mock_get_app.return_value = mock_app

        service = CeleryMonitorService()
        tasks = service.get_scheduled_tasks()

        assert len(tasks) == 1
        assert tasks[0]["task_id"] == "task-456"
        assert tasks[0]["eta"] == "2025-01-01T12:00:00"
        assert tasks[0]["priority"] == 5

    # ========================================================================
    # Worker Stats Tests
    # ========================================================================

    @patch("app.services.job_monitor.celery_monitor.get_celery_app")
    def test_get_worker_stats_success(self, mock_get_app):
        """Test getting worker statistics."""
        mock_app = Mock()
        mock_inspect = Mock()
        mock_app.control.inspect.return_value = mock_inspect
        mock_inspect.stats.return_value = {
            "worker1": {
                "pool": {
                    "implementation": "prefork",
                    "max-concurrency": 4,
                    "processes": [1, 2, 3, 4],
                }
            }
        }
        mock_get_app.return_value = mock_app

        service = CeleryMonitorService()
        stats = service.get_worker_stats()

        assert stats["total_workers"] == 1
        assert stats["online_workers"] == 1
        assert len(stats["workers"]) == 1
        assert stats["workers"][0]["name"] == "worker1"
        assert stats["workers"][0]["max_concurrency"] == 4

    @patch("app.services.job_monitor.celery_monitor.get_celery_app")
    def test_get_worker_stats_no_workers(self, mock_get_app):
        """Test getting worker stats when no workers are online."""
        mock_app = Mock()
        mock_inspect = Mock()
        mock_app.control.inspect.return_value = mock_inspect
        mock_inspect.stats.return_value = None
        mock_get_app.return_value = mock_app

        service = CeleryMonitorService()
        stats = service.get_worker_stats()

        assert stats["total_workers"] == 0
        assert stats["online_workers"] == 0
        assert stats["workers"] == []

    # ========================================================================
    # Task Info Tests
    # ========================================================================

    @patch("app.services.job_monitor.celery_monitor.get_celery_app")
    @patch("app.services.job_monitor.celery_monitor.AsyncResult")
    def test_get_task_info_success(self, mock_async_result, mock_get_app):
        """Test getting task information for a successful task."""
        mock_result = Mock()
        mock_result.state = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {"status": "completed"}
        mock_async_result.return_value = mock_result
        mock_get_app.return_value = Mock()

        service = CeleryMonitorService()
        info = service.get_task_info("task-789")

        assert info is not None
        assert info["task_id"] == "task-789"
        assert info["state"] == "SUCCESS"
        assert info["ready"] is True
        assert info["successful"] is True
        assert info["result"] == {"status": "completed"}

    @patch("app.services.job_monitor.celery_monitor.get_celery_app")
    @patch("app.services.job_monitor.celery_monitor.AsyncResult")
    def test_get_task_info_pending(self, mock_async_result, mock_get_app):
        """Test getting task information for a pending task."""
        mock_result = Mock()
        mock_result.state = "PENDING"
        mock_result.ready.return_value = False
        mock_async_result.return_value = mock_result
        mock_get_app.return_value = Mock()

        service = CeleryMonitorService()
        info = service.get_task_info("task-pending")

        assert info["state"] == "PENDING"
        assert info["ready"] is False

    # ========================================================================
    # Task Control Tests
    # ========================================================================

    @patch("app.services.job_monitor.celery_monitor.get_celery_app")
    def test_revoke_task_success(self, mock_get_app):
        """Test revoking a task successfully."""
        mock_app = Mock()
        mock_control = Mock()
        mock_app.control = mock_control
        mock_get_app.return_value = mock_app

        service = CeleryMonitorService()
        result = service.revoke_task("task-123", terminate=True)

        assert result is True
        mock_control.revoke.assert_called_once_with("task-123", terminate=True)

    @patch("app.services.job_monitor.celery_monitor.get_celery_app")
    def test_purge_queue_success(self, mock_get_app):
        """Test purging a queue."""
        mock_app = Mock()
        mock_control = Mock()
        mock_control.purge.return_value = 5
        mock_app.control = mock_control
        mock_get_app.return_value = mock_app

        service = CeleryMonitorService()
        count = service.purge_queue("test_queue")

        assert count == 5

    # ========================================================================
    # Worker Health Tests
    # ========================================================================

    @patch("app.services.job_monitor.celery_monitor.get_celery_app")
    def test_ping_workers_success(self, mock_get_app):
        """Test pinging workers."""
        mock_app = Mock()
        mock_control = Mock()
        mock_control.ping.return_value = [{"worker1": {"ok": "pong"}}]
        mock_app.control = mock_control
        mock_get_app.return_value = mock_app

        service = CeleryMonitorService()
        pings = service.ping_workers()

        assert "worker1" in pings
        assert pings["worker1"]["ok"] == "pong"

    @patch("app.services.job_monitor.celery_monitor.get_celery_app")
    def test_get_worker_health_healthy(self, mock_get_app):
        """Test getting worker health when workers are healthy."""
        mock_app = Mock()
        mock_control = Mock()
        mock_inspect = Mock()
        mock_control.ping.return_value = [{"worker1": {"ok": "pong"}}]
        mock_inspect.stats.return_value = {"worker1": {}}
        mock_app.control.inspect.return_value = mock_inspect
        mock_app.control = mock_control
        mock_get_app.return_value = mock_app

        service = CeleryMonitorService()
        health = service.get_worker_health()

        assert health["healthy"] is True
        assert health["online_workers"] == 1
        assert "worker1" in health["workers"]

    @patch("app.services.job_monitor.celery_monitor.get_celery_app")
    def test_get_registered_tasks(self, mock_get_app):
        """Test getting registered task names."""
        mock_app = Mock()
        mock_inspect = Mock()
        mock_inspect.registered.return_value = {
            "worker1": ["task1", "task2"],
            "worker2": ["task2", "task3"],
        }
        mock_app.control.inspect.return_value = mock_inspect
        mock_get_app.return_value = mock_app

        service = CeleryMonitorService()
        tasks = service.get_registered_tasks()

        assert len(tasks) == 3
        assert "task1" in tasks
        assert "task2" in tasks
        assert "task3" in tasks
