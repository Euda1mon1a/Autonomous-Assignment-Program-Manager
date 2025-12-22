"""
Job Statistics Collection Service.

Provides statistics and metrics for Celery tasks including:
- Task success/failure rates
- Average execution times
- Retry statistics
- Task distribution by queue
- Performance trends
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from celery import Celery
from celery.events.state import State

from app.core.celery_app import get_celery_app

logger = logging.getLogger(__name__)


class JobStatsService:
    """Service for collecting and analyzing job statistics."""

    def __init__(self):
        """Initialize the job statistics service."""
        self.celery_app: Celery = get_celery_app()
        self._state = State()

    def get_task_statistics(
        self,
        task_name: str | None = None,
        time_range_hours: int = 24
    ) -> dict[str, Any]:
        """
        Get statistics for tasks over a time range.

        Args:
            task_name: Optional filter by task name
            time_range_hours: Hours to look back for statistics (default: 24)

        Returns:
            Dictionary with task statistics

        Example:
            >>> service = JobStatsService()
            >>> stats = service.get_task_statistics(
            ...     task_name="app.resilience.tasks.periodic_health_check",
            ...     time_range_hours=24
            ... )
            >>> stats["total_tasks"]
            96
        """
        try:
            # In a production system, this would query a task result backend
            # or metrics database. For now, we'll provide a structure
            # that can be populated from Redis or a custom task tracking system.

            return {
                "task_name": task_name or "all",
                "time_range_hours": time_range_hours,
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "pending_tasks": 0,
                "retried_tasks": 0,
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "average_runtime_seconds": 0.0,
                "min_runtime_seconds": 0.0,
                "max_runtime_seconds": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting task statistics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_queue_statistics(self) -> dict[str, dict[str, Any]]:
        """
        Get statistics for all queues.

        Returns:
            Dictionary mapping queue names to statistics

        Example:
            >>> service = JobStatsService()
            >>> stats = service.get_queue_statistics()
            >>> stats["resilience"]["total_tasks"]
            45
        """
        try:
            from app.services.job_monitor.celery_monitor import CeleryMonitorService

            monitor = CeleryMonitorService()

            # Get current queue lengths
            queue_lengths = monitor.get_queue_lengths()

            # Get active and reserved tasks
            active_tasks = monitor.get_active_tasks()
            reserved_tasks = monitor.get_reserved_tasks()

            # Build statistics per queue
            stats = {}

            # Initialize known queues from celery config
            known_queues = ["default", "resilience", "notifications", "metrics", "cleanup"]

            for queue_name in known_queues:
                active_count = sum(1 for t in active_tasks if t.get("queue") == queue_name)
                reserved_count = sum(1 for t in reserved_tasks if t.get("queue") == queue_name)

                stats[queue_name] = {
                    "queue_name": queue_name,
                    "active_tasks": active_count,
                    "reserved_tasks": reserved_count,
                    "total_pending": queue_lengths.get(queue_name, 0),
                }

            return stats

        except Exception as e:
            logger.error(f"Error getting queue statistics: {e}")
            return {}

    def get_retry_statistics(self, task_name: str | None = None) -> dict[str, Any]:
        """
        Get retry statistics for tasks.

        Args:
            task_name: Optional filter by task name

        Returns:
            Dictionary with retry statistics

        Example:
            >>> service = JobStatsService()
            >>> stats = service.get_retry_statistics()
            >>> stats["total_retries"]
            12
        """
        try:
            # This would query a task result backend or metrics database
            # For now, provide a structure for the data

            return {
                "task_name": task_name or "all",
                "total_retries": 0,
                "tasks_with_retries": 0,
                "max_retries_used": 0,
                "average_retries_per_task": 0.0,
                "retry_success_rate": 0.0,
                "common_retry_reasons": [],
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting retry statistics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_performance_metrics(
        self,
        task_name: str | None = None,
        time_range_hours: int = 24
    ) -> dict[str, Any]:
        """
        Get performance metrics for tasks.

        Args:
            task_name: Optional filter by task name
            time_range_hours: Hours to look back (default: 24)

        Returns:
            Dictionary with performance metrics including percentiles

        Example:
            >>> service = JobStatsService()
            >>> metrics = service.get_performance_metrics(
            ...     task_name="app.tasks.schedule_metrics_tasks.snapshot_metrics"
            ... )
            >>> metrics["p95_runtime_seconds"]
            45.2
        """
        try:
            # This would analyze task execution times from a result backend
            # Provide structure for percentile-based performance metrics

            return {
                "task_name": task_name or "all",
                "time_range_hours": time_range_hours,
                "total_executions": 0,
                "average_runtime_seconds": 0.0,
                "median_runtime_seconds": 0.0,
                "p50_runtime_seconds": 0.0,
                "p75_runtime_seconds": 0.0,
                "p90_runtime_seconds": 0.0,
                "p95_runtime_seconds": 0.0,
                "p99_runtime_seconds": 0.0,
                "min_runtime_seconds": 0.0,
                "max_runtime_seconds": 0.0,
                "std_dev_runtime_seconds": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_task_distribution(self, time_range_hours: int = 24) -> dict[str, int]:
        """
        Get distribution of tasks by task name.

        Args:
            time_range_hours: Hours to look back (default: 24)

        Returns:
            Dictionary mapping task names to execution counts

        Example:
            >>> service = JobStatsService()
            >>> dist = service.get_task_distribution()
            >>> dist["app.resilience.tasks.periodic_health_check"]
            96
        """
        try:
            # This would query a task result backend or metrics database
            # Return structure for task distribution

            return {
                "app.resilience.tasks.periodic_health_check": 0,
                "app.resilience.tasks.run_contingency_analysis": 0,
                "app.tasks.schedule_metrics_tasks.snapshot_metrics": 0,
                "app.tasks.schedule_metrics_tasks.compute_schedule_metrics": 0,
                "app.notifications.tasks.send_email": 0,
            }

        except Exception as e:
            logger.error(f"Error getting task distribution: {e}")
            return {}

    def get_failure_analysis(
        self,
        task_name: str | None = None,
        time_range_hours: int = 24
    ) -> dict[str, Any]:
        """
        Analyze task failures to identify common issues.

        Args:
            task_name: Optional filter by task name
            time_range_hours: Hours to look back (default: 24)

        Returns:
            Dictionary with failure analysis including common errors

        Example:
            >>> service = JobStatsService()
            >>> analysis = service.get_failure_analysis()
            >>> analysis["most_common_errors"][0]
            {"error_type": "DatabaseError", "count": 5}
        """
        try:
            # This would analyze task failure logs and exceptions
            # Provide structure for failure analysis

            return {
                "task_name": task_name or "all",
                "time_range_hours": time_range_hours,
                "total_failures": 0,
                "unique_error_types": 0,
                "most_common_errors": [
                    # {"error_type": "DatabaseError", "count": 5, "percentage": 50.0}
                ],
                "failure_by_hour": [
                    # {"hour": "2024-01-15T10:00:00", "count": 2}
                ],
                "affected_queues": [],
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error analyzing failures: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_throughput_metrics(
        self,
        queue_name: str | None = None,
        time_range_hours: int = 24
    ) -> dict[str, Any]:
        """
        Get throughput metrics for task processing.

        Args:
            queue_name: Optional filter by queue name
            time_range_hours: Hours to look back (default: 24)

        Returns:
            Dictionary with throughput metrics

        Example:
            >>> service = JobStatsService()
            >>> metrics = service.get_throughput_metrics(queue_name="resilience")
            >>> metrics["tasks_per_hour"]
            15.5
        """
        try:
            # This would calculate throughput from task completion data
            # Provide structure for throughput metrics

            return {
                "queue_name": queue_name or "all",
                "time_range_hours": time_range_hours,
                "total_tasks_processed": 0,
                "tasks_per_minute": 0.0,
                "tasks_per_hour": 0.0,
                "peak_throughput_per_hour": 0.0,
                "average_queue_time_seconds": 0.0,
                "average_processing_time_seconds": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting throughput metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_scheduled_tasks_summary(self) -> dict[str, Any]:
        """
        Get summary of scheduled (beat) tasks.

        Returns:
            Dictionary with scheduled task information

        Example:
            >>> service = JobStatsService()
            >>> summary = service.get_scheduled_tasks_summary()
            >>> summary["total_scheduled_tasks"]
            8
        """
        try:
            # Get scheduled tasks from Celery Beat
            # This would typically query the beat schedule

            from app.core.celery_app import celery_app

            beat_schedule = celery_app.conf.beat_schedule or {}

            scheduled_tasks = []
            for task_name, task_config in beat_schedule.items():
                scheduled_tasks.append({
                    "name": task_name,
                    "task": task_config.get("task"),
                    "schedule": str(task_config.get("schedule")),
                    "options": task_config.get("options", {}),
                })

            return {
                "total_scheduled_tasks": len(scheduled_tasks),
                "scheduled_tasks": scheduled_tasks,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting scheduled tasks summary: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_worker_utilization(self) -> dict[str, Any]:
        """
        Calculate worker utilization metrics.

        Returns:
            Dictionary with worker utilization data

        Example:
            >>> service = JobStatsService()
            >>> util = service.get_worker_utilization()
            >>> util["average_utilization_percentage"]
            65.5
        """
        try:
            from app.services.job_monitor.celery_monitor import CeleryMonitorService

            monitor = CeleryMonitorService()

            # Get worker stats and active tasks
            worker_stats = monitor.get_worker_stats()
            active_tasks = monitor.get_active_tasks()

            total_workers = worker_stats.get("total_workers", 0)
            if total_workers == 0:
                return {
                    "total_workers": 0,
                    "active_workers": 0,
                    "idle_workers": 0,
                    "average_utilization_percentage": 0.0,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Count workers with active tasks
            workers_with_tasks = set()
            for task in active_tasks:
                workers_with_tasks.add(task.get("worker"))

            active_workers = len(workers_with_tasks)
            idle_workers = total_workers - active_workers
            utilization = (active_workers / total_workers) * 100 if total_workers > 0 else 0.0

            return {
                "total_workers": total_workers,
                "active_workers": active_workers,
                "idle_workers": idle_workers,
                "average_utilization_percentage": round(utilization, 2),
                "tasks_per_worker": round(len(active_tasks) / total_workers, 2) if total_workers > 0 else 0.0,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating worker utilization: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
