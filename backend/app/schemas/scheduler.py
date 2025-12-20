"""Pydantic schemas for job scheduler."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CronTriggerSchema(BaseModel):
    """
    Schema for cron trigger configuration.

    Attributes:
        year: 4-digit year
        month: Month (1-12)
        day: Day of month (1-31)
        week: ISO week (1-53)
        day_of_week: Number or name of weekday
        hour: Hour (0-23)
        minute: Minute (0-59)
        second: Second (0-59)
        start_date: Earliest possible date/time
        end_date: Latest possible date/time
        timezone: Time zone
    """

    year: str | int | None = None
    month: str | int | None = None
    day: str | int | None = None
    week: str | int | None = None
    day_of_week: str | int | None = None
    hour: str | int | None = None
    minute: str | int | None = None
    second: str | int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    timezone: str = "UTC"


class IntervalTriggerSchema(BaseModel):
    """
    Schema for interval trigger configuration.

    Attributes:
        weeks: Number of weeks to wait
        days: Number of days to wait
        hours: Number of hours to wait
        minutes: Number of minutes to wait
        seconds: Number of seconds to wait
        start_date: Starting point for interval
        end_date: Latest possible date/time
        timezone: Time zone
    """

    weeks: int = 0
    days: int = 0
    hours: int = 0
    minutes: int = 0
    seconds: int = 0
    start_date: datetime | None = None
    end_date: datetime | None = None
    timezone: str = "UTC"

    @field_validator("weeks", "days", "hours", "minutes", "seconds")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Validate that interval values are non-negative."""
        if v < 0:
            raise ValueError("Interval values must be non-negative")
        return v


class DateTriggerSchema(BaseModel):
    """
    Schema for date trigger configuration.

    Attributes:
        run_date: The date/time to run the job
        timezone: Time zone
    """

    run_date: datetime
    timezone: str = "UTC"


class JobCreateSchema(BaseModel):
    """
    Schema for creating a scheduled job.

    Attributes:
        name: Unique job name
        job_func: Fully qualified function path
        trigger_type: Type of trigger (cron, interval, date)
        trigger_config: Trigger configuration
        args: Positional arguments for job function
        kwargs: Keyword arguments for job function
        max_instances: Maximum concurrent instances
        misfire_grace_time: Seconds after scheduled time to still run
        coalesce: Whether to run once or multiple times for missed runs
        description: Job description
    """

    name: str = Field(..., min_length=1, max_length=255)
    job_func: str = Field(..., min_length=1, max_length=500)
    trigger_type: str = Field(..., pattern="^(cron|interval|date)$")
    trigger_config: dict[str, Any]
    args: list[Any] = Field(default_factory=list)
    kwargs: dict[str, Any] = Field(default_factory=dict)
    max_instances: int = Field(default=1, ge=1, le=10)
    misfire_grace_time: int | None = Field(default=None, ge=0)
    coalesce: bool = True
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("trigger_config")
    @classmethod
    def validate_trigger_config(cls, v: dict, info) -> dict:
        """Validate trigger configuration based on trigger type."""
        if not v:
            raise ValueError("trigger_config cannot be empty")

        trigger_type = info.data.get("trigger_type")

        if trigger_type == "cron":
            # Validate cron trigger config
            try:
                CronTriggerSchema(**v)
            except Exception as e:
                raise ValueError(f"Invalid cron trigger config: {e}")
        elif trigger_type == "interval":
            # Validate interval trigger config
            try:
                IntervalTriggerSchema(**v)
            except Exception as e:
                raise ValueError(f"Invalid interval trigger config: {e}")
        elif trigger_type == "date":
            # Validate date trigger config
            try:
                DateTriggerSchema(**v)
            except Exception as e:
                raise ValueError(f"Invalid date trigger config: {e}")

        return v


class JobUpdateSchema(BaseModel):
    """
    Schema for updating a scheduled job.

    Attributes:
        trigger_config: Updated trigger configuration
        args: Updated positional arguments
        kwargs: Updated keyword arguments
        max_instances: Updated max concurrent instances
        misfire_grace_time: Updated misfire grace time
        coalesce: Updated coalesce setting
        enabled: Whether the job is enabled
        description: Updated description
    """

    trigger_config: dict[str, Any] | None = None
    args: list[Any] | None = None
    kwargs: dict[str, Any] | None = None
    max_instances: int | None = Field(default=None, ge=1, le=10)
    misfire_grace_time: int | None = Field(default=None, ge=0)
    coalesce: bool | None = None
    enabled: bool | None = None
    description: str | None = Field(default=None, max_length=1000)


class JobResponseSchema(BaseModel):
    """
    Schema for scheduled job response.

    Attributes:
        id: Job ID
        name: Job name
        job_func: Function path
        trigger_type: Type of trigger
        trigger_config: Trigger configuration
        args: Positional arguments
        kwargs: Keyword arguments
        next_run_time: Next scheduled run time
        last_run_time: Last execution time
        run_count: Number of executions
        max_instances: Maximum concurrent instances
        misfire_grace_time: Misfire grace time
        coalesce: Coalesce setting
        enabled: Whether job is enabled
        description: Job description
        created_at: Creation timestamp
        updated_at: Update timestamp
        created_by: User who created the job
    """

    id: UUID
    name: str
    job_func: str
    trigger_type: str
    trigger_config: dict[str, Any]
    args: list[Any]
    kwargs: dict[str, Any]
    next_run_time: datetime | None
    last_run_time: datetime | None
    run_count: int
    max_instances: int
    misfire_grace_time: int | None
    coalesce: bool
    enabled: bool
    description: str | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None

    class Config:
        """Pydantic config."""

        from_attributes = True


class JobExecutionSchema(BaseModel):
    """
    Schema for job execution record.

    Attributes:
        id: Execution ID
        job_id: Job ID
        job_name: Job name
        started_at: Start time
        finished_at: Finish time
        status: Execution status
        result: Execution result
        error: Error message
        runtime_seconds: Runtime in seconds
        scheduled_run_time: Scheduled run time
    """

    id: UUID
    job_id: UUID
    job_name: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    result: Any | None
    error: str | None
    runtime_seconds: int | None
    scheduled_run_time: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class JobStatisticsSchema(BaseModel):
    """
    Schema for job statistics.

    Attributes:
        job_id: Job ID
        job_name: Job name
        total_runs: Total number of runs
        success_count: Number of successful runs
        failure_count: Number of failed runs
        missed_count: Number of missed runs
        average_runtime_seconds: Average runtime
        last_run_time: Last run time
        next_run_time: Next run time
    """

    job_id: str
    job_name: str
    total_runs: int
    success_count: int
    failure_count: int
    missed_count: int
    average_runtime_seconds: float
    last_run_time: str | None
    next_run_time: str | None


class JobListResponseSchema(BaseModel):
    """
    Schema for job list response.

    Attributes:
        total: Total number of jobs
        jobs: List of jobs
    """

    total: int
    jobs: list[JobResponseSchema]


class JobExecutionListSchema(BaseModel):
    """
    Schema for job execution list response.

    Attributes:
        total: Total number of executions
        limit: Query limit
        offset: Query offset
        executions: List of executions
    """

    total: int
    limit: int
    offset: int
    executions: list[JobExecutionSchema]


class SyncResultSchema(BaseModel):
    """
    Schema for scheduler sync result.

    Attributes:
        added: Number of jobs added
        removed: Number of jobs removed
        updated: Number of jobs updated
        timestamp: Sync timestamp
    """

    added: int
    removed: int
    updated: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class JobActionResponseSchema(BaseModel):
    """
    Schema for job action response.

    Attributes:
        success: Whether action was successful
        message: Response message
        job_id: Job ID
    """

    success: bool
    message: str
    job_id: UUID | None = None
