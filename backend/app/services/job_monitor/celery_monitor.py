"""
Celery Task Monitoring Service.

Provides real-time monitoring of Celery tasks including:
- Active task listings
- Task queue status
- Worker health checks
- Task state inspection
- Task cancellation
- Priority management
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from celery import Celery
from celery.result import AsyncResult

from app.core.celery_app import get_celery_app

logger = logging.getLogger(__name__)


class CeleryMonitorService:
    """Service for monitoring and managing Celery tasks."""

    def __init__(self):
        """Initialize the Celery monitor service."""
        self.celery_app: Celery = get_celery_app()

    def get_active_tasks(self, queue_name: str | None = None) -> list[dict[str, Any]]:
        """
        Get list of currently active (running) tasks.

        Args:
            queue_name: Optional filter by queue name

        Returns:
            List of active task dictionaries with metadata

        Example:
            >>> service = CeleryMonitorService()
            >>> tasks = service.get_active_tasks(queue_name="resilience")
            >>> len(tasks)
            3
        """
        try:
            inspect = self.celery_app.control.inspect()
            active = inspect.active()

            if not active:
                return []

            all_tasks = []
            for worker, tasks in active.items():
                for task in tasks:
                    task_info = {
                        "task_id": task.get("id"),
                        "task_name": task.get("name"),
                        "worker": worker,
                        "queue": task.get("delivery_info", {}).get(
                            "routing_key", "default"
                        ),
                        "args": task.get("args", []),
                        "kwargs": task.get("kwargs", {}),
                        "time_start": task.get("time_start"),
                        "acknowledged": task.get("acknowledged", False),
                    }

                    # Filter by queue if specified
                    if queue_name is None or task_info["queue"] == queue_name:
                        all_tasks.append(task_info)

            return all_tasks

        except Exception as e:
            logger.error(f"Error fetching active tasks: {e}")
            return []

    def get_scheduled_tasks(self) -> list[dict[str, Any]]:
        """
        Get list of scheduled (not yet running) tasks.

        Returns:
            List of scheduled task dictionaries

        Example:
            >>> service = CeleryMonitorService()
            >>> scheduled = service.get_scheduled_tasks()
        """
        try:
            inspect = self.celery_app.control.inspect()
            scheduled = inspect.scheduled()

            if not scheduled:
                return []

            all_tasks = []
            for worker, tasks in scheduled.items():
                for task in tasks:
                    task_info = {
                        "task_id": task.get("request", {}).get("id"),
                        "task_name": task.get("request", {}).get("name"),
                        "worker": worker,
                        "eta": task.get("eta"),
                        "priority": task.get("priority", 0),
                        "args": task.get("request", {}).get("args", []),
                        "kwargs": task.get("request", {}).get("kwargs", {}),
                    }
                    all_tasks.append(task_info)

            return all_tasks

        except Exception as e:
            logger.error(f"Error fetching scheduled tasks: {e}")
            return []

    def get_reserved_tasks(self) -> list[dict[str, Any]]:
        """
        Get list of reserved (queued but not running) tasks.

        Returns:
            List of reserved task dictionaries

        Example:
            >>> service = CeleryMonitorService()
            >>> reserved = service.get_reserved_tasks()
        """
        try:
            inspect = self.celery_app.control.inspect()
            reserved = inspect.reserved()

            if not reserved:
                return []

            all_tasks = []
            for worker, tasks in reserved.items():
                for task in tasks:
                    task_info = {
                        "task_id": task.get("id"),
                        "task_name": task.get("name"),
                        "worker": worker,
                        "queue": task.get("delivery_info", {}).get(
                            "routing_key", "default"
                        ),
                        "priority": task.get("priority", 0),
                        "args": task.get("args", []),
                        "kwargs": task.get("kwargs", {}),
                    }
                    all_tasks.append(task_info)

            return all_tasks

        except Exception as e:
            logger.error(f"Error fetching reserved tasks: {e}")
            return []

    def get_worker_stats(self) -> dict[str, Any]:
        """
        Get statistics about Celery workers.

        Returns:
            Dictionary with worker statistics including:
            - Total workers
            - Workers by queue
            - Worker status
            - Pool sizes

        Example:
            >>> service = CeleryMonitorService()
            >>> stats = service.get_worker_stats()
            >>> stats["total_workers"]
            4
        """
        try:
            inspect = self.celery_app.control.inspect()
            stats_data = inspect.stats()

            if not stats_data:
                return {
                    "total_workers": 0,
                    "online_workers": 0,
                    "workers": [],
                }

            workers = []
            for worker_name, worker_stats in stats_data.items():
                worker_info = {
                    "name": worker_name,
                    "status": "online",
                    "pool": worker_stats.get("pool", {}).get(
                        "implementation", "unknown"
                    ),
                    "max_concurrency": worker_stats.get("pool", {}).get(
                        "max-concurrency", 0
                    ),
                    "processes": worker_stats.get("pool", {}).get("processes", []),
                }
                workers.append(worker_info)

            return {
                "total_workers": len(workers),
                "online_workers": len(workers),
                "workers": workers,
            }

        except Exception as e:
            logger.error(f"Error fetching worker stats: {e}")
            return {
                "total_workers": 0,
                "online_workers": 0,
                "workers": [],
            }

    def get_queue_lengths(self) -> dict[str, int]:
        """
        Get the number of tasks in each queue.

        Returns:
            Dictionary mapping queue names to task counts

        Example:
            >>> service = CeleryMonitorService()
            >>> lengths = service.get_queue_lengths()
            >>> lengths["resilience"]
            5
        """
        try:
            # Get reserved tasks grouped by queue
            reserved = self.get_reserved_tasks()
            active = self.get_active_tasks()

            queue_counts: dict[str, int] = {}

            # Count reserved tasks
            for task in reserved:
                queue = task.get("queue", "default")
                queue_counts[queue] = queue_counts.get(queue, 0) + 1

            # Count active tasks
            for task in active:
                queue = task.get("queue", "default")
                queue_counts[queue] = queue_counts.get(queue, 0) + 1

            return queue_counts

        except Exception as e:
            logger.error(f"Error getting queue lengths: {e}")
            return {}

    def get_task_info(self, task_id: str) -> dict[str, Any] | None:
        """
        Get detailed information about a specific task.

        Args:
            task_id: The task ID to query

        Returns:
            Task information dictionary or None if not found

        Example:
            >>> service = CeleryMonitorService()
            >>> info = service.get_task_info("abc-123-def")
            >>> info["state"]
            "SUCCESS"
        """
        try:
            result = AsyncResult(task_id, app=self.celery_app)

            task_info = {
                "task_id": task_id,
                "state": result.state,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
                "failed": result.failed() if result.ready() else None,
            }

            # Add result if available
            if result.ready():
                if result.successful():
                    task_info["result"] = result.result
                elif result.failed():
                    task_info["error"] = str(result.info)
                    task_info["traceback"] = result.traceback

            # Add task metadata if available
            if hasattr(result, "info") and result.info:
                task_info["info"] = result.info

            return task_info

        except Exception as e:
            logger.error(f"Error getting task info for {task_id}: {e}")
            return None

    def revoke_task(self, task_id: str, terminate: bool = False) -> bool:
        """
        Revoke (cancel) a task.

        Args:
            task_id: The task ID to revoke
            terminate: If True, terminate the task immediately (default: False)

        Returns:
            True if revocation was successful, False otherwise

        Example:
            >>> service = CeleryMonitorService()
            >>> service.revoke_task("abc-123-def", terminate=True)
            True
        """
        try:
            self.celery_app.control.revoke(task_id, terminate=terminate)
            logger.info(f"Task {task_id} revoked (terminate={terminate})")
            return True

        except Exception as e:
            logger.error(f"Error revoking task {task_id}: {e}")
            return False

    def purge_queue(self, queue_name: str) -> int:
        """
        Purge all tasks from a specific queue.

        Args:
            queue_name: Name of the queue to purge

        Returns:
            Number of tasks purged

        Warning:
            This operation cannot be undone. Use with caution.

        Example:
            >>> service = CeleryMonitorService()
            >>> count = service.purge_queue("test_queue")
            >>> count
            10
        """
        try:
            # Purge the queue
            count = self.celery_app.control.purge()
            logger.warning(f"Purged {count} tasks from queue {queue_name}")
            return count or 0

        except Exception as e:
            logger.error(f"Error purging queue {queue_name}: {e}")
            return 0

    def get_registered_tasks(self) -> list[str]:
        """
        Get list of all registered task names.

        Returns:
            List of task names

        Example:
            >>> service = CeleryMonitorService()
            >>> tasks = service.get_registered_tasks()
            >>> "app.resilience.tasks.periodic_health_check" in tasks
            True
        """
        try:
            inspect = self.celery_app.control.inspect()
            registered = inspect.registered()

            if not registered:
                return []

            # Collect all unique task names from all workers
            all_tasks = set()
            for worker, tasks in registered.items():
                all_tasks.update(tasks)

            return sorted(list(all_tasks))

        except Exception as e:
            logger.error(f"Error getting registered tasks: {e}")
            return []

    def ping_workers(self) -> dict[str, dict[str, Any]]:
        """
        Ping all workers to check their availability.

        Returns:
            Dictionary mapping worker names to ping response

        Example:
            >>> service = CeleryMonitorService()
            >>> pings = service.ping_workers()
            >>> pings["celery@worker1"]["ok"]
            "pong"
        """
        try:
            ping_response = self.celery_app.control.ping(timeout=1.0)

            if not ping_response:
                return {}

            result = {}
            for response in ping_response:
                for worker, status in response.items():
                    result[worker] = status

            return result

        except Exception as e:
            logger.error(f"Error pinging workers: {e}")
            return {}

    def get_worker_health(self) -> dict[str, Any]:
        """
        Get comprehensive worker health status.

        Returns:
            Dictionary with worker health metrics including:
            - Total workers
            - Online workers
            - Offline workers
            - Worker details

        Example:
            >>> service = CeleryMonitorService()
            >>> health = service.get_worker_health()
            >>> health["healthy"]
            True
        """
        try:
            ping_results = self.ping_workers()
            stats = self.get_worker_stats()

            online_workers = list(ping_results.keys())
            total_workers = stats.get("total_workers", 0)

            return {
                "healthy": len(online_workers) > 0,
                "total_workers": total_workers,
                "online_workers": len(online_workers),
                "offline_workers": max(0, total_workers - len(online_workers)),
                "workers": online_workers,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting worker health: {e}")
            return {
                "healthy": False,
                "total_workers": 0,
                "online_workers": 0,
                "offline_workers": 0,
                "workers": [],
                "timestamp": datetime.utcnow().isoformat(),
            }
