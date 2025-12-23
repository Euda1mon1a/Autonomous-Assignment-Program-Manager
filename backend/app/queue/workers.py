"""
Worker Management.

Manages Celery workers including:
- Worker health monitoring
- Worker statistics and metrics
- Worker pool management
- Task distribution and load balancing
"""

import logging
from datetime import datetime
from typing import Any

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


class WorkerManager:
    """
    Manages Celery workers and provides monitoring capabilities.

    Provides interface for:
    - Worker health checks
    - Worker statistics
    - Task distribution
    - Worker pool information
    """

    def __init__(self):
        """Initialize worker manager."""
        self.app = celery_app
        self.inspect = self.app.control.inspect()

    def get_active_workers(self) -> list[str]:
        """
        Get list of active worker names.

        Returns:
            list[str]: Active worker names
        """
        stats = self.inspect.stats()
        if not stats:
            return []
        return list(stats.keys())

    def get_worker_stats(self, worker_name: str | None = None) -> dict[str, Any]:
        """
        Get worker statistics.

        Args:
            worker_name: Specific worker name (None for all workers)

        Returns:
            dict: Worker statistics
        """
        stats = self.inspect.stats()
        if not stats:
            return {"workers": {}, "total_workers": 0}

        if worker_name:
            return {
                "worker": worker_name,
                "stats": stats.get(worker_name, {}),
                "timestamp": datetime.utcnow().isoformat(),
            }

        return {
            "workers": stats,
            "total_workers": len(stats),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_worker_health(self) -> dict[str, Any]:
        """
        Check worker health status.

        Returns:
            dict: Health status for all workers
        """
        # Ping workers
        ping_result = self.inspect.ping()

        if not ping_result:
            return {
                "healthy": False,
                "workers": {},
                "total_workers": 0,
                "online_workers": 0,
                "timestamp": datetime.utcnow().isoformat(),
            }

        workers = {}
        for worker, response in ping_result.items():
            workers[worker] = {
                "online": response.get("ok") == "pong",
                "response_time": response.get("timestamp"),
            }

        online_count = sum(1 for w in workers.values() if w["online"])

        return {
            "healthy": online_count > 0,
            "workers": workers,
            "total_workers": len(workers),
            "online_workers": online_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_worker_tasks(self, worker_name: str | None = None) -> dict[str, Any]:
        """
        Get tasks being processed by workers.

        Args:
            worker_name: Specific worker name (None for all workers)

        Returns:
            dict: Worker tasks information
        """
        active = self.inspect.active()
        reserved = self.inspect.reserved()
        scheduled = self.inspect.scheduled()

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "workers": {},
        }

        if not active and not reserved and not scheduled:
            return result

        workers = set()
        if active:
            workers.update(active.keys())
        if reserved:
            workers.update(reserved.keys())
        if scheduled:
            workers.update(scheduled.keys())

        for worker in workers:
            if worker_name and worker != worker_name:
                continue

            result["workers"][worker] = {
                "active": active.get(worker, []) if active else [],
                "reserved": reserved.get(worker, []) if reserved else [],
                "scheduled": scheduled.get(worker, []) if scheduled else [],
                "total_active": len(active.get(worker, [])) if active else 0,
                "total_reserved": len(reserved.get(worker, [])) if reserved else 0,
                "total_scheduled": len(scheduled.get(worker, [])) if scheduled else 0,
            }

        return result

    def get_worker_pool_info(self, worker_name: str | None = None) -> dict[str, Any]:
        """
        Get worker pool information.

        Args:
            worker_name: Specific worker name (None for all workers)

        Returns:
            dict: Worker pool information
        """
        stats = self.inspect.stats()
        if not stats:
            return {"workers": {}}

        result = {"workers": {}}

        for worker, worker_stats in stats.items():
            if worker_name and worker != worker_name:
                continue

            pool_info = worker_stats.get("pool", {})
            result["workers"][worker] = {
                "pool_type": pool_info.get("implementation"),
                "max_concurrency": pool_info.get("max-concurrency"),
                "processes": pool_info.get("processes"),
                "timeouts": pool_info.get("timeouts"),
            }

        return result

    def get_registered_tasks(self, worker_name: str | None = None) -> dict[str, Any]:
        """
        Get tasks registered with workers.

        Args:
            worker_name: Specific worker name (None for all workers)

        Returns:
            dict: Registered tasks
        """
        registered = self.inspect.registered()
        if not registered:
            return {"workers": {}}

        result = {"workers": {}}

        for worker, tasks in registered.items():
            if worker_name and worker != worker_name:
                continue

            result["workers"][worker] = {
                "tasks": sorted(tasks),
                "task_count": len(tasks),
            }

        return result

    def get_worker_utilization(self) -> dict[str, Any]:
        """
        Calculate worker utilization metrics.

        Returns:
            dict: Worker utilization data
        """
        stats = self.inspect.stats()
        active = self.inspect.active()

        if not stats:
            return {
                "total_workers": 0,
                "active_workers": 0,
                "idle_workers": 0,
                "utilization_percentage": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
            }

        total_workers = len(stats)
        active_workers = 0

        if active:
            active_workers = sum(1 for tasks in active.values() if tasks)

        idle_workers = total_workers - active_workers
        utilization = (
            (active_workers / total_workers * 100) if total_workers > 0 else 0.0
        )

        return {
            "total_workers": total_workers,
            "active_workers": active_workers,
            "idle_workers": idle_workers,
            "utilization_percentage": round(utilization, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_worker_queues(self, worker_name: str | None = None) -> dict[str, Any]:
        """
        Get queues being consumed by workers.

        Args:
            worker_name: Specific worker name (None for all workers)

        Returns:
            dict: Worker queue assignments
        """
        active_queues = self.inspect.active_queues()
        if not active_queues:
            return {"workers": {}}

        result = {"workers": {}}

        for worker, queues in active_queues.items():
            if worker_name and worker != worker_name:
                continue

            result["workers"][worker] = {
                "queues": [
                    {
                        "name": q.get("name"),
                        "exchange": q.get("exchange", {}).get("name"),
                        "routing_key": q.get("routing_key"),
                    }
                    for q in queues
                ],
                "queue_count": len(queues),
            }

        return result

    def shutdown_worker(self, worker_name: str, immediate: bool = False) -> bool:
        """
        Shutdown a specific worker.

        Args:
            worker_name: Worker name to shutdown
            immediate: If True, shutdown immediately without waiting for tasks

        Returns:
            bool: True if shutdown command sent
        """
        destination = [worker_name]

        if immediate:
            self.app.control.shutdown(destination=destination)
        else:
            # Graceful shutdown: stop accepting new tasks, finish current ones
            self.app.control.cancel_consumer("default", destination=destination)

        logger.warning(
            f"Shutdown command sent to worker {worker_name} (immediate={immediate})"
        )
        return True

    def autoscale_worker(
        self,
        worker_name: str,
        max_concurrency: int,
        min_concurrency: int,
    ) -> bool:
        """
        Configure worker autoscaling.

        Args:
            worker_name: Worker name
            max_concurrency: Maximum number of concurrent tasks
            min_concurrency: Minimum number of concurrent tasks

        Returns:
            bool: True if autoscale command sent
        """
        destination = [worker_name]
        self.app.control.autoscale(
            max=max_concurrency,
            min=min_concurrency,
            destination=destination,
        )

        logger.info(
            f"Autoscale configured for worker {worker_name}: "
            f"min={min_concurrency}, max={max_concurrency}"
        )
        return True

    def pool_grow(self, worker_name: str, n: int = 1) -> bool:
        """
        Grow worker pool by n processes.

        Args:
            worker_name: Worker name
            n: Number of processes to add

        Returns:
            bool: True if command sent
        """
        destination = [worker_name]
        self.app.control.pool_grow(n=n, destination=destination)

        logger.info(f"Growing worker {worker_name} pool by {n} processes")
        return True

    def pool_shrink(self, worker_name: str, n: int = 1) -> bool:
        """
        Shrink worker pool by n processes.

        Args:
            worker_name: Worker name
            n: Number of processes to remove

        Returns:
            bool: True if command sent
        """
        destination = [worker_name]
        self.app.control.pool_shrink(n=n, destination=destination)

        logger.info(f"Shrinking worker {worker_name} pool by {n} processes")
        return True

    def get_worker_report(self) -> dict[str, Any]:
        """
        Get comprehensive worker report.

        Returns:
            dict: Complete worker status report
        """
        return {
            "health": self.get_worker_health(),
            "stats": self.get_worker_stats(),
            "utilization": self.get_worker_utilization(),
            "tasks": self.get_worker_tasks(),
            "pool_info": self.get_worker_pool_info(),
            "queues": self.get_worker_queues(),
            "timestamp": datetime.utcnow().isoformat(),
        }
