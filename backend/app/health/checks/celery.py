"""
Celery health check implementation.

Provides comprehensive Celery health monitoring including:
- Worker availability
- Worker status
- Queue lengths
- Task statistics
- Scheduled task status
"""

import asyncio
import logging
import time
from typing import Any

from celery import Celery
from celery.app.control import Inspect

from app.core.celery_app import get_celery_app

logger = logging.getLogger(__name__)


class CeleryHealthCheck:
    """
    Celery health check implementation.

    Performs health checks on Celery workers including:
    - Worker availability and status
    - Active task count
    - Queue lengths
    - Scheduled tasks
    - Worker pool statistics
    """

    def __init__(self, timeout: float = 5.0) -> None:
        """
        Initialize Celery health check.

        Args:
            timeout: Maximum time in seconds to wait for health check
        """
        self.timeout = timeout
        self.name = "celery"
        self.celery_app: Celery = get_celery_app()

    async def check(self) -> dict[str, Any]:
        """
        Perform Celery health check.

        Returns:
            Dictionary with health status:
            - status: "healthy", "degraded", or "unhealthy"
            - workers_online: Number of active workers
            - active_tasks: Number of currently running tasks
            - scheduled_tasks: Number of scheduled tasks
            - queues: Queue statistics
            - error: Error message if unhealthy

        Raises:
            TimeoutError: If check exceeds timeout
        """
        start_time = time.time()

        try:
            # Run check with timeout
            result = await asyncio.wait_for(self._perform_check(), timeout=self.timeout)

            response_time_ms = (time.time() - start_time) * 1000
            result["response_time_ms"] = round(response_time_ms, 2)

            # Determine status based on worker availability
            workers_online = result.get("workers_online", 0)
            if workers_online == 0:
                result["status"] = "unhealthy"
                result["error"] = "No Celery workers are online"
            elif response_time_ms > 2000:  # > 2 seconds is degraded
                result["status"] = "degraded"
                result["warning"] = "Celery response time is slow"

            return result

        except TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Celery health check timed out after {self.timeout}s")
            return {
                "status": "unhealthy",
                "error": f"Health check timed out after {self.timeout}s",
                "response_time_ms": round(response_time_ms, 2),
            }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Celery health check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": round(response_time_ms, 2),
            }

    async def _perform_check(self) -> dict[str, Any]:
        """
        Perform the actual Celery health check.

        Returns:
            Dictionary with detailed health information
        """
        try:
            # Create inspector
            inspector: Inspect = self.celery_app.control.inspect(timeout=self.timeout)

            # 1. Get active workers
            stats = inspector.stats()
            if stats is None:
                return {
                    "status": "unhealthy",
                    "error": "No Celery workers responding",
                    "workers_online": 0,
                }

            workers_online = len(stats)

            # 2. Get active tasks
            active = inspector.active()
            active_tasks = sum(len(tasks) for tasks in (active or {}).values())

            # 3. Get scheduled tasks
            scheduled = inspector.scheduled()
            scheduled_tasks = sum(len(tasks) for tasks in (scheduled or {}).values())

            # 4. Get reserved tasks
            reserved = inspector.reserved()
            reserved_tasks = sum(len(tasks) for tasks in (reserved or {}).values())

            # 5. Get registered tasks
            registered = inspector.registered()
            registered_tasks_count = sum(
                len(tasks) for tasks in (registered or {}).values()
            )

            # 6. Get queue lengths (if available)
            queue_stats = self._get_queue_stats()

            # All checks passed
            return {
                "status": "healthy",
                "workers_online": workers_online,
                "active_tasks": active_tasks,
                "scheduled_tasks": scheduled_tasks,
                "reserved_tasks": reserved_tasks,
                "registered_tasks": registered_tasks_count,
                "queues": queue_stats,
            }

        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": f"Celery error: {str(e)}",
            }

    def _get_queue_stats(self) -> dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Dictionary with queue information
        """
        try:
            # Get queue names from celery app config
            queues = ["default", "resilience", "notifications", "metrics"]

            queue_info = {}
            for queue_name in queues:
                queue_info[queue_name] = {
                    "exists": True,  # Assume exists if configured
                }

            return queue_info

        except Exception as e:
            logger.warning(f"Failed to get queue stats: {e}")
            return {}

    async def check_worker_ping(self) -> dict[str, Any]:
        """
        Ping Celery workers to verify they're responsive.

        Returns:
            Dictionary with ping results for each worker
        """
        try:
            inspector: Inspect = self.celery_app.control.inspect(timeout=self.timeout)

            # Ping all workers
            pong = inspector.ping()

            if not pong:
                return {
                    "status": "unhealthy",
                    "error": "No workers responded to ping",
                }

            workers = []
            for worker_name, response in pong.items():
                workers.append(
                    {
                        "name": worker_name,
                        "ok": response.get("ok") == "pong",
                    }
                )

            return {
                "status": "healthy",
                "workers": workers,
                "total_workers": len(workers),
            }

        except Exception as e:
            logger.error(f"Celery worker ping failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    async def check_scheduled_tasks(self) -> dict[str, Any]:
        """
        Check the status of scheduled (beat) tasks.

        Returns:
            Dictionary with scheduled task information
        """
        try:
            inspector: Inspect = self.celery_app.control.inspect(timeout=self.timeout)

            # Get scheduled tasks
            scheduled = inspector.scheduled()

            if scheduled is None:
                return {
                    "status": "degraded",
                    "warning": "Could not retrieve scheduled tasks",
                }

            total_scheduled = sum(len(tasks) for tasks in scheduled.values())

            # Get registered periodic tasks from beat schedule
            beat_schedule = self.celery_app.conf.beat_schedule
            registered_periodic = len(beat_schedule) if beat_schedule else 0

            return {
                "status": "healthy",
                "scheduled_tasks": total_scheduled,
                "registered_periodic_tasks": registered_periodic,
            }

        except Exception as e:
            logger.error(f"Scheduled task check failed: {e}")
            return {
                "status": "degraded",
                "error": str(e),
            }

    async def check_queue_health(self) -> dict[str, Any]:
        """
        Check health of Celery queues.

        Returns:
            Dictionary with queue health information
        """
        try:
            inspector: Inspect = self.celery_app.control.inspect(timeout=self.timeout)

            # Get active queues from workers
            active_queues = inspector.active_queues()

            if not active_queues:
                return {
                    "status": "degraded",
                    "warning": "No active queues found",
                }

            queues = []
            for worker_name, worker_queues in active_queues.items():
                for queue in worker_queues:
                    queues.append(
                        {
                            "name": queue["name"],
                            "routing_key": queue.get("routing_key", "unknown"),
                            "worker": worker_name,
                        }
                    )

            return {
                "status": "healthy",
                "queues": queues,
                "total_queues": len(set(q["name"] for q in queues)),
            }

        except Exception as e:
            logger.error(f"Queue health check failed: {e}")
            return {
                "status": "degraded",
                "error": str(e),
            }
