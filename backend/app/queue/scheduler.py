"""
Task Scheduler.

Manages scheduled and recurring tasks:
- Delayed task execution
- Recurring task schedules
- Cron-based scheduling
- Schedule management and monitoring
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from celery.schedules import crontab, schedule

from app.core.celery_app import celery_app
from app.queue.tasks import TaskPriority

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Manages task scheduling including delayed and recurring tasks.

    Provides interface for:
    - Scheduling tasks for future execution
    - Managing recurring task schedules
    - Cron-based task scheduling
    - Schedule inspection and modification
    """

    def __init__(self):
        """Initialize task scheduler."""
        self.app = celery_app

    def schedule_task(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict | None = None,
        eta: datetime | None = None,
        countdown: int | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """
        Schedule a task for delayed execution.

        Args:
            task_name: Name of the task to execute
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            eta: Absolute time when to execute
            countdown: Delay in seconds before execution
            priority: Task priority level

        Returns:
            str: Task ID

        Example:
            >>> scheduler = TaskScheduler()
            >>> # Execute in 5 minutes
            >>> task_id = scheduler.schedule_task(
            ...     "app.tasks.send_notification",
            ...     args=(user_id,),
            ...     countdown=300,
            ... )
            >>> # Execute at specific time
            >>> eta = datetime(2024, 1, 15, 10, 0)
            >>> task_id = scheduler.schedule_task(
            ...     "app.tasks.generate_report",
            ...     eta=eta,
            ... )
        """
        kwargs = kwargs or {}

        if eta is None and countdown is None:
            raise ValueError("Must specify either eta or countdown")

        if eta and countdown:
            raise ValueError("Cannot specify both eta and countdown")

        # Get task from registry
        task = self.app.tasks.get(task_name)
        if not task:
            raise ValueError(f"Task {task_name} not found in registry")

        # Schedule task
        result = task.apply_async(
            args=args,
            kwargs=kwargs,
            eta=eta,
            countdown=countdown,
            priority=int(priority),
        )

        execution_time = eta or (datetime.utcnow() + timedelta(seconds=countdown))
        logger.info(
            f"Task {task_name} scheduled for {execution_time.isoformat()} "
            f"(ID: {result.id})"
        )

        return result.id

    def add_periodic_task(
        self,
        name: str,
        task_name: str,
        schedule_config: dict[str, Any],
        args: tuple = (),
        kwargs: dict | None = None,
        options: dict | None = None,
    ) -> bool:
        """
        Add a periodic task to the schedule.

        Note: This requires Celery Beat to be running.

        Args:
            name: Unique name for this periodic task
            task_name: Name of the task to execute
            schedule_config: Schedule configuration (crontab or interval)
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            options: Additional task options (queue, priority, etc.)

        Returns:
            bool: True if task added successfully

        Example:
            >>> # Run every day at 9 AM
            >>> scheduler.add_periodic_task(
            ...     name="daily-report",
            ...     task_name="app.tasks.generate_daily_report",
            ...     schedule_config={
            ...         "crontab": {"hour": 9, "minute": 0}
            ...     },
            ... )
            >>> # Run every 5 minutes
            >>> scheduler.add_periodic_task(
            ...     name="cleanup-temp-files",
            ...     task_name="app.tasks.cleanup_temp",
            ...     schedule_config={
            ...         "interval": {"every": 300}  # seconds
            ...     },
            ... )
        """
        kwargs = kwargs or {}
        options = options or {}

        # Parse schedule configuration
        task_schedule = self._parse_schedule_config(schedule_config)

        # Add to beat schedule
        self.app.conf.beat_schedule[name] = {
            "task": task_name,
            "schedule": task_schedule,
            "args": args,
            "kwargs": kwargs,
            "options": options,
        }

        logger.info(f"Periodic task '{name}' added to schedule (task={task_name})")
        return True

    def remove_periodic_task(self, name: str) -> bool:
        """
        Remove a periodic task from the schedule.

        Args:
            name: Name of the periodic task to remove

        Returns:
            bool: True if task removed

        Raises:
            KeyError: If task name not found
        """
        if name not in self.app.conf.beat_schedule:
            raise KeyError(f"Periodic task '{name}' not found in schedule")

        del self.app.conf.beat_schedule[name]
        logger.info(f"Periodic task '{name}' removed from schedule")
        return True

    def get_periodic_tasks(self) -> dict[str, Any]:
        """
        Get all periodic tasks.

        Returns:
            dict: All periodic tasks configuration
        """
        return {
            "tasks": {
                name: {
                    "task": config["task"],
                    "schedule": str(config["schedule"]),
                    "args": config.get("args", ()),
                    "kwargs": config.get("kwargs", {}),
                    "options": config.get("options", {}),
                }
                for name, config in self.app.conf.beat_schedule.items()
            },
            "total_tasks": len(self.app.conf.beat_schedule),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_scheduled_tasks(self) -> dict[str, Any]:
        """
        Get tasks scheduled for future execution.

        Returns:
            dict: Scheduled tasks information
        """
        inspect = self.app.control.inspect()
        scheduled = inspect.scheduled()

        if not scheduled:
            return {
                "tasks": {},
                "total_tasks": 0,
                "timestamp": datetime.utcnow().isoformat(),
            }

        result = {"tasks": {}, "total_tasks": 0}

        for worker, tasks in scheduled.items():
            result["tasks"][worker] = [
                {
                    "task_id": task.get("id"),
                    "task_name": task.get("name"),
                    "eta": task.get("eta"),
                    "priority": task.get("priority"),
                    "args": task.get("args"),
                    "kwargs": task.get("kwargs"),
                }
                for task in tasks
            ]
            result["total_tasks"] += len(tasks)

        result["timestamp"] = datetime.utcnow().isoformat()
        return result

    def cancel_scheduled_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.

        Args:
            task_id: Task ID to cancel

        Returns:
            bool: True if task cancelled
        """
        self.app.control.revoke(task_id, terminate=False)
        logger.info(f"Scheduled task {task_id} cancelled")
        return True

    def reschedule_task(
        self,
        task_id: str,
        eta: datetime | None = None,
        countdown: int | None = None,
    ) -> str:
        """
        Reschedule a task to a new time.

        Note: This cancels the old task and creates a new one.

        Args:
            task_id: Task ID to reschedule
            eta: New absolute time when to execute
            countdown: New delay in seconds before execution

        Returns:
            str: New task ID

        Raises:
            ValueError: If task not found or not scheduled
        """
        from celery.result import AsyncResult

        result = AsyncResult(task_id, app=self.app)

        # Cancel old task
        self.cancel_scheduled_task(task_id)

        # Get task details
        task_name = result.name
        if not task_name:
            raise ValueError(f"Task {task_id} not found or has no name")

        # Create new scheduled task
        # Note: We lose the original args/kwargs here
        # In production, you'd want to store these in a database
        task = self.app.tasks.get(task_name)
        if not task:
            raise ValueError(f"Task {task_name} not found in registry")

        new_result = task.apply_async(eta=eta, countdown=countdown)

        logger.info(
            f"Task {task_id} rescheduled as new task {new_result.id} "
            f"(eta={eta}, countdown={countdown})"
        )

        return new_result.id

    def _parse_schedule_config(self, config: dict[str, Any]) -> schedule | crontab:
        """
        Parse schedule configuration into Celery schedule object.

        Args:
            config: Schedule configuration dict

        Returns:
            schedule | crontab: Celery schedule object

        Raises:
            ValueError: If configuration is invalid
        """
        if "crontab" in config:
            # Cron-based schedule
            cron_config = config["crontab"]
            return crontab(**cron_config)

        elif "interval" in config:
            # Interval-based schedule
            interval_config = config["interval"]
            seconds = interval_config.get("every")
            if not seconds:
                raise ValueError("Interval schedule requires 'every' (seconds)")
            return schedule(run_every=timedelta(seconds=seconds))

        else:
            raise ValueError(
                "Schedule configuration must contain either 'crontab' or 'interval'"
            )

    def get_next_run_time(self, task_name: str) -> datetime | None:
        """
        Get the next scheduled run time for a periodic task.

        Args:
            task_name: Name of the periodic task

        Returns:
            datetime | None: Next run time or None if not found
        """
        if task_name not in self.app.conf.beat_schedule:
            return None

        task_config = self.app.conf.beat_schedule[task_name]
        task_schedule = task_config["schedule"]

        # Calculate next run time
        now = datetime.utcnow()
        if isinstance(task_schedule, crontab):
            # For crontab, we need to check when it will next run
            # This is approximate - actual calculation is complex
            return now  # Placeholder
        elif isinstance(task_schedule, schedule):
            # For interval schedule
            return now + task_schedule.run_every

        return None

    def enable_periodic_task(self, name: str) -> bool:
        """
        Enable a periodic task.

        Args:
            name: Name of the periodic task

        Returns:
            bool: True if enabled

        Raises:
            KeyError: If task not found
        """
        if name not in self.app.conf.beat_schedule:
            raise KeyError(f"Periodic task '{name}' not found")

        # Remove 'enabled': False if present
        if "enabled" in self.app.conf.beat_schedule[name]:
            self.app.conf.beat_schedule[name]["enabled"] = True

        logger.info(f"Periodic task '{name}' enabled")
        return True

    def disable_periodic_task(self, name: str) -> bool:
        """
        Disable a periodic task.

        Args:
            name: Name of the periodic task

        Returns:
            bool: True if disabled

        Raises:
            KeyError: If task not found
        """
        if name not in self.app.conf.beat_schedule:
            raise KeyError(f"Periodic task '{name}' not found")

        self.app.conf.beat_schedule[name]["enabled"] = False
        logger.info(f"Periodic task '{name}' disabled")
        return True
