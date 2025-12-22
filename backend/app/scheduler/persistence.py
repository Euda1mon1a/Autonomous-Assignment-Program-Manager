"""
Job persistence layer for the scheduler.

Handles saving and loading scheduled jobs from the database,
as well as tracking job execution history.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.scheduled_job import JobExecution, ScheduledJob

logger = logging.getLogger(__name__)


class JobPersistence:
    """
    Handles persistence of scheduled jobs and execution history.

    Provides methods to:
    - Load jobs from database
    - Save/update job configurations
    - Track job execution history
    - Query job statistics
    """

    def __init__(self, db: Session):
        """
        Initialize persistence layer.

        Args:
            db: Database session
        """
        self.db = db

    def get_all_jobs(self, enabled_only: bool = True) -> list[ScheduledJob]:
        """
        Get all scheduled jobs from database.

        Args:
            enabled_only: If True, only return enabled jobs

        Returns:
            List of scheduled jobs
        """
        query = self.db.query(ScheduledJob)

        if enabled_only:
            query = query.filter(ScheduledJob.enabled == True)

        return query.all()

    def get_job_by_id(self, job_id: UUID | str) -> ScheduledJob | None:
        """
        Get a job by its ID.

        Args:
            job_id: Job ID

        Returns:
            ScheduledJob or None if not found
        """
        return self.db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()

    def get_job_by_name(self, name: str) -> ScheduledJob | None:
        """
        Get a job by its name.

        Args:
            name: Job name

        Returns:
            ScheduledJob or None if not found
        """
        return self.db.query(ScheduledJob).filter(ScheduledJob.name == name).first()

    def create_job(
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
        enabled: bool = True,
        description: str | None = None,
        created_by: str | None = None,
    ) -> ScheduledJob:
        """
        Create a new scheduled job.

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
            enabled: Whether the job is enabled
            description: Job description
            created_by: User who created the job

        Returns:
            Created ScheduledJob

        Raises:
            ValueError: If a job with the same name already exists
        """
        # Check if job already exists
        existing = self.get_job_by_name(name)
        if existing:
            raise ValueError(f"Job with name '{name}' already exists")

        job = ScheduledJob(
            name=name,
            job_func=job_func,
            trigger_type=trigger_type,
            trigger_config=trigger_config,
            args=args or [],
            kwargs=kwargs or {},
            max_instances=max_instances,
            misfire_grace_time=misfire_grace_time,
            coalesce=coalesce,
            enabled=enabled,
            description=description,
            created_by=created_by,
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        logger.info(f"Created scheduled job '{name}'")

        return job

    def update_job(
        self,
        job_id: UUID | str,
        **kwargs,
    ) -> ScheduledJob | None:
        """
        Update a scheduled job.

        Args:
            job_id: Job ID
            **kwargs: Fields to update

        Returns:
            Updated ScheduledJob or None if not found
        """
        job = self.get_job_by_id(job_id)
        if not job:
            return None

        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)

        job.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(job)

        logger.info(f"Updated scheduled job '{job.name}'")

        return job

    def delete_job(self, job_id: UUID | str) -> bool:
        """
        Delete a scheduled job.

        Args:
            job_id: Job ID

        Returns:
            True if deleted, False if not found
        """
        job = self.get_job_by_id(job_id)
        if not job:
            return False

        job_name = job.name
        self.db.delete(job)
        self.db.commit()

        logger.info(f"Deleted scheduled job '{job_name}'")

        return True

    def update_job_next_run_time(
        self,
        job_id: UUID | str,
        next_run_time: datetime | None,
    ) -> None:
        """
        Update job's next run time.

        Args:
            job_id: Job ID
            next_run_time: Next scheduled run time
        """
        job = self.get_job_by_id(job_id)
        if job:
            job.next_run_time = next_run_time
            self.db.commit()

    def increment_run_count(self, job_id: UUID | str) -> None:
        """
        Increment job's run count.

        Args:
            job_id: Job ID
        """
        job = self.get_job_by_id(job_id)
        if job:
            job.run_count += 1
            job.last_run_time = datetime.utcnow()
            self.db.commit()

    def record_execution_start(
        self,
        job_id: UUID | str,
        job_name: str,
        scheduled_run_time: datetime,
    ) -> JobExecution:
        """
        Record the start of a job execution.

        Args:
            job_id: Job ID
            job_name: Job name
            scheduled_run_time: When the job was scheduled to run

        Returns:
            JobExecution record
        """
        execution = JobExecution(
            job_id=job_id,
            job_name=job_name,
            started_at=datetime.utcnow(),
            scheduled_run_time=scheduled_run_time,
            status="running",
        )

        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        return execution

    def record_execution_success(
        self,
        execution_id: UUID | str,
        result: Any = None,
    ) -> None:
        """
        Record successful job execution.

        Args:
            execution_id: Execution ID
            result: Job execution result
        """
        execution = self.db.query(JobExecution).filter(
            JobExecution.id == execution_id
        ).first()

        if execution:
            execution.finished_at = datetime.utcnow()
            execution.status = "success"
            execution.result = result

            if execution.started_at:
                delta = execution.finished_at - execution.started_at
                execution.runtime_seconds = int(delta.total_seconds())

            self.db.commit()

    def record_execution_failure(
        self,
        execution_id: UUID | str,
        error: str,
        traceback: str | None = None,
    ) -> None:
        """
        Record failed job execution.

        Args:
            execution_id: Execution ID
            error: Error message
            traceback: Full traceback
        """
        execution = self.db.query(JobExecution).filter(
            JobExecution.id == execution_id
        ).first()

        if execution:
            execution.finished_at = datetime.utcnow()
            execution.status = "failure"
            execution.error = error
            execution.traceback = traceback

            if execution.started_at:
                delta = execution.finished_at - execution.started_at
                execution.runtime_seconds = int(delta.total_seconds())

            self.db.commit()

    def record_missed_execution(
        self,
        job_id: UUID | str,
        job_name: str,
        scheduled_run_time: datetime,
    ) -> None:
        """
        Record a missed job execution.

        Args:
            job_id: Job ID
            job_name: Job name
            scheduled_run_time: When the job was scheduled to run
        """
        execution = JobExecution(
            job_id=job_id,
            job_name=job_name,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            scheduled_run_time=scheduled_run_time,
            status="missed",
            runtime_seconds=0,
        )

        self.db.add(execution)
        self.db.commit()

    def get_job_executions(
        self,
        job_id: UUID | str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[JobExecution]:
        """
        Get job execution history.

        Args:
            job_id: Optional job ID to filter by
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of job executions
        """
        query = self.db.query(JobExecution)

        if job_id:
            query = query.filter(JobExecution.job_id == job_id)

        query = query.order_by(JobExecution.started_at.desc())
        query = query.limit(limit).offset(offset)

        return query.all()

    def get_job_statistics(self, job_id: UUID | str) -> dict[str, Any]:
        """
        Get statistics for a job.

        Args:
            job_id: Job ID

        Returns:
            Dictionary with job statistics
        """
        job = self.get_job_by_id(job_id)
        if not job:
            return {}

        # Count executions by status
        executions = self.db.query(
            JobExecution.status,
            func.count(JobExecution.id).label("count")
        ).filter(
            JobExecution.job_id == job_id
        ).group_by(
            JobExecution.status
        ).all()

        status_counts = {status: count for status, count in executions}

        # Get average runtime
        avg_runtime = self.db.query(
            func.avg(JobExecution.runtime_seconds)
        ).filter(
            JobExecution.job_id == job_id,
            JobExecution.status == "success"
        ).scalar() or 0

        return {
            "job_id": str(job.id),
            "job_name": job.name,
            "total_runs": job.run_count,
            "success_count": status_counts.get("success", 0),
            "failure_count": status_counts.get("failure", 0),
            "missed_count": status_counts.get("missed", 0),
            "average_runtime_seconds": float(avg_runtime),
            "last_run_time": job.last_run_time.isoformat() if job.last_run_time else None,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        }
