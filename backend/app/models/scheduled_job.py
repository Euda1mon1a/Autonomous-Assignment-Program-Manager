"""Scheduled job model for job scheduler."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.db.types import GUID, JSONType


class ScheduledJob(Base):
    """
    Scheduled job model for storing job configurations.

    Attributes:
        id: Unique job identifier
        name: Job name (must be unique)
        job_func: Fully qualified function name to execute
        trigger_type: Type of trigger (cron, interval, date)
        trigger_config: JSON configuration for the trigger
        args: Positional arguments for the job function
        kwargs: Keyword arguments for the job function
        next_run_time: Next scheduled run time
        last_run_time: Last execution time
        run_count: Number of times the job has been executed
        max_instances: Maximum concurrent instances of this job
        misfire_grace_time: Seconds after scheduled time to still run the job
        coalesce: Whether to run once or multiple times for missed runs
        enabled: Whether the job is enabled
        description: Human-readable description
        created_at: When the job was created
        updated_at: When the job was last updated
        created_by: User who created the job
    """

    __tablename__ = "scheduled_jobs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    job_func = Column(String(500), nullable=False)
    trigger_type = Column(String(50), nullable=False)  # cron, interval, date
    trigger_config = Column(JSONType, nullable=False, default=dict)
    args = Column(JSONType, nullable=True, default=list)
    kwargs = Column(JSONType, nullable=True, default=dict)
    next_run_time = Column(DateTime, nullable=True, index=True)
    last_run_time = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
    max_instances = Column(Integer, default=1)
    misfire_grace_time = Column(Integer, nullable=True)  # seconds
    coalesce = Column(Boolean, default=True)
    enabled = Column(Boolean, default=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<ScheduledJob(name='{self.name}', trigger_type='{self.trigger_type}', enabled={self.enabled})>"


class JobExecution(Base):
    """
    Job execution history model.

    Tracks each execution of scheduled jobs for auditing and debugging.

    Attributes:
        id: Unique execution identifier
        job_id: Reference to the scheduled job
        job_name: Name of the job (denormalized for history)
        started_at: When the job started executing
        finished_at: When the job finished executing
        status: Execution status (success, failure, missed)
        result: Job execution result (JSON)
        error: Error message if failed
        traceback: Full traceback if failed
        runtime_seconds: How long the job took to execute
        scheduled_run_time: When the job was originally scheduled
    """

    __tablename__ = "job_executions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), nullable=False, index=True)
    job_name = Column(String(255), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, index=True)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, index=True)  # success, failure, missed
    result = Column(JSONType, nullable=True)
    error = Column(Text, nullable=True)
    traceback = Column(Text, nullable=True)
    runtime_seconds = Column(Integer, nullable=True)
    scheduled_run_time = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<JobExecution(job_name='{self.job_name}', status='{self.status}', started_at='{self.started_at}')>"
