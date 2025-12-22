"""
Background job scheduler implementation.

Provides a flexible job scheduler using APScheduler with database persistence.
Supports cron, interval, and one-time job scheduling.
"""

import logging
import traceback
from datetime import datetime
from typing import Any
from uuid import UUID

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_MISSED,
)

from app.db.session import SessionLocal
from app.scheduler.jobs import get_job_function
from app.scheduler.persistence import JobPersistence
from app.scheduler.triggers import create_trigger

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler_instance: "JobScheduler | None" = None


class JobScheduler:
    """
    Background job scheduler with database persistence.

    Features:
    - Cron-based scheduling
    - Interval-based scheduling
    - One-time jobs
    - Job persistence
    - Missed job handling
    - Job chaining support
    """

    def __init__(self):
        """Initialize the job scheduler."""
        self.scheduler = BackgroundScheduler(
            timezone="UTC",
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 300,  # 5 minutes
            }
        )

        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )
        self.scheduler.add_listener(
            self._job_missed_listener,
            EVENT_JOB_MISSED
        )

        self._started = False

    def start(self) -> None:
        """
        Start the scheduler.

        Loads all enabled jobs from the database and starts the scheduler.
        """
        if self._started:
            logger.warning("Scheduler already started")
            return

        logger.info("Starting job scheduler...")

        # Load jobs from database
        self.load_jobs_from_database()

        # Start the scheduler
        self.scheduler.start()
        self._started = True

        logger.info("Job scheduler started successfully")

    def shutdown(self, wait: bool = True) -> None:
        """
        Shut down the scheduler.

        Args:
            wait: Whether to wait for running jobs to complete
        """
        if not self._started:
            return

        logger.info("Shutting down job scheduler...")
        self.scheduler.shutdown(wait=wait)
        self._started = False
        logger.info("Job scheduler shut down")

    def load_jobs_from_database(self) -> int:
        """
        Load all enabled jobs from the database.

        Returns:
            Number of jobs loaded
        """
        db = SessionLocal()
        try:
            persistence = JobPersistence(db)
            jobs = persistence.get_all_jobs(enabled_only=True)

            loaded_count = 0
            for job in jobs:
                try:
                    self._add_job_to_scheduler(job)
                    loaded_count += 1
                except Exception as e:
                    logger.error(f"Failed to load job '{job.name}': {e}", exc_info=True)

            logger.info(f"Loaded {loaded_count} jobs from database")
            return loaded_count

        finally:
            db.close()

    def sync_with_database(self) -> dict[str, int]:
        """
        Sync scheduler state with database.

        Adds new jobs, removes deleted jobs, and updates modified jobs.

        Returns:
            Dictionary with counts of added, removed, and updated jobs
        """
        db = SessionLocal()
        try:
            persistence = JobPersistence(db)
            db_jobs = persistence.get_all_jobs(enabled_only=True)

            # Get current jobs in scheduler
            scheduler_jobs = {job.id: job for job in self.scheduler.get_jobs()}

            # Convert database jobs to dict
            db_job_names = {job.name: job for job in db_jobs}

            added = 0
            removed = 0
            updated = 0

            # Add new jobs
            for job in db_jobs:
                if job.name not in scheduler_jobs:
                    try:
                        self._add_job_to_scheduler(job)
                        added += 1
                    except Exception as e:
                        logger.error(f"Failed to add job '{job.name}': {e}")

            # Remove deleted jobs
            for job_id, job in scheduler_jobs.items():
                if job_id not in db_job_names:
                    try:
                        self.scheduler.remove_job(job_id)
                        removed += 1
                    except Exception as e:
                        logger.error(f"Failed to remove job '{job_id}': {e}")

            logger.info(f"Scheduler sync: {added} added, {removed} removed, {updated} updated")

            return {
                "added": added,
                "removed": removed,
                "updated": updated,
            }

        finally:
            db.close()

    def add_job(
        self,
        name: str,
        job_func: str,
        trigger_type: str,
        trigger_config: dict[str, Any],
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
        max_instances: int = 1,
        misfire_grace_time: int | None = None,
        coalesce: bool = True,
        description: str | None = None,
        created_by: str | None = None,
    ) -> UUID:
        """
        Add a new job to the scheduler.

        Args:
            name: Unique job name
            job_func: Fully qualified function path
            trigger_type: Type of trigger (cron, interval, date)
            trigger_config: Trigger configuration dictionary
            args: Positional arguments for the job function
            kwargs: Keyword arguments for the job function
            max_instances: Maximum concurrent instances
            misfire_grace_time: Seconds after scheduled time to still run
            coalesce: Whether to run once or multiple times for missed runs
            description: Job description
            created_by: User who created the job

        Returns:
            Job ID

        Raises:
            ValueError: If job name already exists
        """
        db = SessionLocal()
        try:
            persistence = JobPersistence(db)

            # Create job in database
            job = persistence.create_job(
                name=name,
                job_func=job_func,
                trigger_type=trigger_type,
                trigger_config=trigger_config,
                args=args,
                kwargs=kwargs,
                max_instances=max_instances,
                misfire_grace_time=misfire_grace_time,
                coalesce=coalesce,
                enabled=True,
                description=description,
                created_by=created_by,
            )

            # Add to scheduler
            self._add_job_to_scheduler(job)

            logger.info(f"Added job '{name}' to scheduler")

            return job.id

        finally:
            db.close()

    def remove_job(self, job_id: UUID | str) -> bool:
        """
        Remove a job from the scheduler.

        Args:
            job_id: Job ID

        Returns:
            True if removed, False if not found
        """
        db = SessionLocal()
        try:
            persistence = JobPersistence(db)

            # Remove from scheduler
            try:
                self.scheduler.remove_job(str(job_id))
            except Exception as e:
                logger.warning(f"Job not in scheduler: {e}")

            # Delete from database
            return persistence.delete_job(job_id)

        finally:
            db.close()

    def pause_job(self, job_id: UUID | str) -> bool:
        """
        Pause a job.

        Args:
            job_id: Job ID

        Returns:
            True if paused, False if not found
        """
        try:
            self.scheduler.pause_job(str(job_id))

            # Update database
            db = SessionLocal()
            try:
                persistence = JobPersistence(db)
                persistence.update_job(job_id, enabled=False)
            finally:
                db.close()

            return True

        except Exception as e:
            logger.error(f"Failed to pause job: {e}")
            return False

    def resume_job(self, job_id: UUID | str) -> bool:
        """
        Resume a paused job.

        Args:
            job_id: Job ID

        Returns:
            True if resumed, False if not found
        """
        try:
            self.scheduler.resume_job(str(job_id))

            # Update database
            db = SessionLocal()
            try:
                persistence = JobPersistence(db)
                persistence.update_job(job_id, enabled=True)
            finally:
                db.close()

            return True

        except Exception as e:
            logger.error(f"Failed to resume job: {e}")
            return False

    def get_job_info(self, job_id: UUID | str) -> dict[str, Any] | None:
        """
        Get information about a scheduled job.

        Args:
            job_id: Job ID

        Returns:
            Job information dictionary or None if not found
        """
        job = self.scheduler.get_job(str(job_id))
        if not job:
            return None

        return {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        }

    def list_jobs(self) -> list[dict[str, Any]]:
        """
        List all jobs in the scheduler.

        Returns:
            List of job information dictionaries
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        return jobs

    def _add_job_to_scheduler(self, job: Any) -> None:
        """
        Add a database job to the APScheduler.

        Args:
            job: ScheduledJob model instance
        """
        # Get the function to execute
        func = get_job_function(job.job_func)

        # Create trigger
        trigger = create_trigger(job.trigger_type, job.trigger_config)

        # Wrap function to track execution
        wrapped_func = self._create_wrapped_function(
            job.id,
            job.name,
            func
        )

        # Add to scheduler
        self.scheduler.add_job(
            wrapped_func,
            trigger=trigger,
            id=str(job.id),
            name=job.name,
            args=job.args or [],
            kwargs=job.kwargs or {},
            max_instances=job.max_instances,
            misfire_grace_time=job.misfire_grace_time,
            coalesce=job.coalesce,
        )

    def _create_wrapped_function(
        self,
        job_id: UUID,
        job_name: str,
        func: Any,
    ) -> Any:
        """
        Create a wrapped function that tracks execution.

        Args:
            job_id: Job ID
            job_name: Job name
            func: Original function

        Returns:
            Wrapped function
        """
        def wrapper(*args, **kwargs):
            db = SessionLocal()
            execution_id = None

            try:
                persistence = JobPersistence(db)

                # Record execution start
                execution = persistence.record_execution_start(
                    job_id=job_id,
                    job_name=job_name,
                    scheduled_run_time=datetime.utcnow(),
                )
                execution_id = execution.id

                # Execute function
                result = func(*args, **kwargs)

                # Record success
                persistence.record_execution_success(execution_id, result)

                # Increment run count
                persistence.increment_run_count(job_id)

                return result

            except Exception as e:
                # Record failure
                if execution_id:
                    persistence.record_execution_failure(
                        execution_id,
                        str(e),
                        traceback.format_exc()
                    )

                logger.error(f"Job '{job_name}' failed: {e}", exc_info=True)
                raise

            finally:
                db.close()

        return wrapper

    def _job_executed_listener(self, event) -> None:
        """Handle job executed event."""
        logger.debug(f"Job {event.job_id} executed successfully")

    def _job_error_listener(self, event) -> None:
        """Handle job error event."""
        logger.error(f"Job {event.job_id} raised an exception: {event.exception}")

    def _job_missed_listener(self, event) -> None:
        """Handle job missed event."""
        logger.warning(f"Job {event.job_id} missed scheduled run time")

        db = SessionLocal()
        try:
            persistence = JobPersistence(db)
            job = persistence.get_job_by_id(UUID(event.job_id))

            if job:
                persistence.record_missed_execution(
                    job_id=job.id,
                    job_name=job.name,
                    scheduled_run_time=event.scheduled_run_time,
                )

        finally:
            db.close()


def get_scheduler() -> JobScheduler:
    """
    Get the global scheduler instance.

    Creates the scheduler if it doesn't exist yet.

    Returns:
        JobScheduler instance
    """
    global _scheduler_instance

    if _scheduler_instance is None:
        _scheduler_instance = JobScheduler()

    return _scheduler_instance


def start_scheduler() -> None:
    """Start the global scheduler instance."""
    scheduler = get_scheduler()
    if not scheduler._started:
        scheduler.start()


def shutdown_scheduler(wait: bool = True) -> None:
    """
    Shut down the global scheduler instance.

    Args:
        wait: Whether to wait for running jobs to complete
    """
    global _scheduler_instance

    if _scheduler_instance:
        _scheduler_instance.shutdown(wait=wait)
        _scheduler_instance = None
