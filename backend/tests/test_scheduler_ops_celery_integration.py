"""Integration tests for scheduler ops Celery integration.

These tests verify that the scheduler_ops routes can properly
query Celery task data from the backend.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.api.routes.scheduler_ops import (
    _calculate_task_metrics,
    _get_recent_tasks,
)
from app.schemas.scheduler_ops import TaskStatus


class TestCeleryTaskMetricsIntegration:
    """Test suite for Celery task metrics integration."""

    @patch("app.api.routes.scheduler_ops.celery_app")
    def test_calculate_task_metrics_with_active_tasks(
        self, mock_celery_app, db_session
    ):
        """Test calculating metrics when there are active tasks."""
        # Mock inspect API
        mock_inspect = MagicMock()
        mock_celery_app.control.inspect.return_value = mock_inspect

        # Mock active tasks
        mock_inspect.active.return_value = {
            "worker1": [
                {"id": "task-1", "name": "app.resilience.tasks.periodic_health_check"},
                {
                    "id": "task-2",
                    "name": "app.resilience.tasks.run_contingency_analysis",
                },
            ],
            "worker2": [
                {"id": "task-3", "name": "app.notifications.tasks.send_alert"},
            ],
        }

        # Mock scheduled tasks
        mock_inspect.scheduled.return_value = {
            "worker1": [
                {
                    "id": "task-4",
                    "name": "app.resilience.tasks.precompute_fallback_schedules",
                },
            ],
        }

        # Mock reserved tasks
        mock_inspect.reserved.return_value = {}

        # Mock stats
        mock_inspect.stats.return_value = {
            "worker1": {"total": {"completed": 50}},
            "worker2": {"total": {"completed": 30}},
        }

        # Mock registered tasks
        mock_inspect.registered.return_value = {}

        # Calculate metrics
        metrics = _calculate_task_metrics(db_session)

        # Verify counts
        assert metrics.active_tasks == 3  # 2 + 1
        assert metrics.pending_tasks == 1  # scheduled
        assert metrics.total_tasks >= 4  # At least active + pending

    @patch("app.api.routes.scheduler_ops.celery_app")
    @patch("app.api.routes.scheduler_ops.Redis")
    def test_calculate_task_metrics_with_redis_results(
        self, mock_redis_class, mock_celery_app, db_session
    ):
        """Test calculating metrics from Redis result backend."""
        # Mock inspect API
        mock_inspect = MagicMock()
        mock_celery_app.control.inspect.return_value = mock_inspect

        mock_inspect.active.return_value = {}
        mock_inspect.scheduled.return_value = {}
        mock_inspect.reserved.return_value = {}
        mock_inspect.stats.return_value = {}
        mock_inspect.registered.return_value = {}

        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis_class.from_url.return_value = mock_redis

        # Mock task result keys
        mock_redis.keys.return_value = [
            b"celery-task-meta-task-1",
            b"celery-task-meta-task-2",
            b"celery-task-meta-task-3",
        ]

        # Mock task results
        def mock_get(key):
            results = {
                b"celery-task-meta-task-1": json.dumps(
                    {"status": "SUCCESS", "task_name": "test_task"}
                ),
                b"celery-task-meta-task-2": json.dumps(
                    {"status": "SUCCESS", "task_name": "test_task2"}
                ),
                b"celery-task-meta-task-3": json.dumps(
                    {"status": "FAILURE", "task_name": "test_task3"}
                ),
            }
            return results.get(key)

        mock_redis.get.side_effect = mock_get

        # Calculate metrics
        metrics = _calculate_task_metrics(db_session)

        # Verify counts
        assert metrics.completed_tasks == 2
        assert metrics.failed_tasks == 1
        assert metrics.success_rate == 2 / 3  # 2 success out of 3 total

    @patch("app.api.routes.scheduler_ops.celery_app")
    def test_calculate_task_metrics_no_workers(self, mock_celery_app, db_session):
        """Test calculating metrics when no workers are connected."""
        mock_inspect = MagicMock()
        mock_celery_app.control.inspect.return_value = mock_inspect

        # No workers connected
        mock_inspect.active.return_value = None
        mock_inspect.scheduled.return_value = None
        mock_inspect.reserved.return_value = None
        mock_inspect.stats.return_value = None
        mock_inspect.registered.return_value = None

        # Should return safe defaults
        metrics = _calculate_task_metrics(db_session)

        assert metrics.total_tasks == 0
        assert metrics.active_tasks == 0
        assert metrics.success_rate == 1.0

    @patch("app.api.routes.scheduler_ops.celery_app")
    def test_calculate_task_metrics_exception_handling(
        self, mock_celery_app, db_session
    ):
        """Test that exceptions are handled gracefully."""
        mock_inspect = MagicMock()
        mock_celery_app.control.inspect.return_value = mock_inspect

        # Simulate an exception
        mock_inspect.active.side_effect = Exception("Connection error")

        # Should return safe defaults without raising
        metrics = _calculate_task_metrics(db_session)

        assert metrics.total_tasks == 0
        assert metrics.success_rate == 1.0


class TestCeleryRecentTasksIntegration:
    """Test suite for Celery recent tasks integration."""

    @patch("app.api.routes.scheduler_ops.celery_app")
    @patch("app.api.routes.scheduler_ops.Redis")
    def test_get_recent_tasks_from_redis(
        self, mock_redis_class, mock_celery_app, db_session
    ):
        """Test fetching recent tasks from Redis backend."""
        # Mock inspect API (no active tasks)
        mock_inspect = MagicMock()
        mock_celery_app.control.inspect.return_value = mock_inspect
        mock_inspect.active.return_value = {}

        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis_class.from_url.return_value = mock_redis

        # Mock task keys
        mock_redis.keys.return_value = [
            b"celery-task-meta-task-1",
            b"celery-task-meta-task-2",
        ]

        # Mock task results
        completed_time = datetime.utcnow().isoformat()

        def mock_get(key):
            results = {
                b"celery-task-meta-task-1": json.dumps(
                    {
                        "status": "SUCCESS",
                        "task_name": "app.resilience.tasks.periodic_health_check",
                        "date_done": completed_time,
                    }
                ),
                b"celery-task-meta-task-2": json.dumps(
                    {
                        "status": "FAILURE",
                        "task_name": "app.resilience.tasks.run_contingency_analysis",
                        "date_done": completed_time,
                        "result": {"exc_message": "Database connection failed"},
                    }
                ),
            }
            return results.get(key)

        mock_redis.get.side_effect = mock_get

        # Get recent tasks
        tasks = _get_recent_tasks(db_session, limit=10)

        # Verify results
        assert len(tasks) == 2

        # Check completed task
        completed_task = next(t for t in tasks if t.status == TaskStatus.COMPLETED)
        assert "Periodic Health Check" in completed_task.name
        assert completed_task.error_message is None

        # Check failed task
        failed_task = next(t for t in tasks if t.status == TaskStatus.FAILED)
        assert "Run Contingency Analysis" in failed_task.name
        assert "Database connection failed" in failed_task.error_message

    @patch("app.api.routes.scheduler_ops.celery_app")
    @patch("app.api.routes.scheduler_ops.Redis")
    def test_get_recent_tasks_with_active_tasks(
        self, mock_redis_class, mock_celery_app, db_session
    ):
        """Test fetching recent tasks includes active tasks."""
        # Mock inspect API
        mock_inspect = MagicMock()
        mock_celery_app.control.inspect.return_value = mock_inspect

        # Mock active tasks
        current_time = datetime.utcnow().timestamp()
        mock_inspect.active.return_value = {
            "worker1": [
                {
                    "id": "active-task-1",
                    "name": "app.notifications.tasks.send_alert",
                    "time_start": current_time,
                    "args": ["alert-data"],
                    "kwargs": {},
                },
            ],
        }

        # Mock Redis (no stored results)
        mock_redis = MagicMock()
        mock_redis_class.from_url.return_value = mock_redis
        mock_redis.keys.return_value = []

        # Get recent tasks
        tasks = _get_recent_tasks(db_session, limit=10)

        # Verify active task is included
        assert len(tasks) == 1
        assert tasks[0].status == TaskStatus.IN_PROGRESS
        assert tasks[0].task_id == "active-task-1"
        assert "Send Alert" in tasks[0].name

    @patch("app.api.routes.scheduler_ops.celery_app")
    @patch("app.api.routes.scheduler_ops.Redis")
    def test_get_recent_tasks_limit(
        self, mock_redis_class, mock_celery_app, db_session
    ):
        """Test that recent tasks respects limit."""
        mock_inspect = MagicMock()
        mock_celery_app.control.inspect.return_value = mock_inspect
        mock_inspect.active.return_value = {}

        # Mock Redis with many tasks
        mock_redis = MagicMock()
        mock_redis_class.from_url.return_value = mock_redis

        # Create 20 task keys
        task_keys = [f"celery-task-meta-task-{i}".encode() for i in range(20)]
        mock_redis.keys.return_value = task_keys

        # Mock get to return valid task data
        def mock_get(key):
            return json.dumps(
                {
                    "status": "SUCCESS",
                    "task_name": "test_task",
                    "date_done": datetime.utcnow().isoformat(),
                }
            )

        mock_redis.get.side_effect = mock_get

        # Get recent tasks with limit of 5
        tasks = _get_recent_tasks(db_session, limit=5)

        # Should return only 5 tasks
        assert len(tasks) == 5

    @patch("app.api.routes.scheduler_ops.celery_app")
    def test_get_recent_tasks_exception_handling(self, mock_celery_app, db_session):
        """Test that exceptions are handled gracefully."""
        mock_inspect = MagicMock()
        mock_celery_app.control.inspect.return_value = mock_inspect

        # Simulate an exception
        mock_inspect.active.side_effect = Exception("Connection error")

        # Should return empty list without raising
        tasks = _get_recent_tasks(db_session, limit=10)

        assert tasks == []
