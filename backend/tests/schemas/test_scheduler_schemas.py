"""Tests for job scheduler schemas (Field bounds, field_validators, defaults, patterns)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.scheduler import (
    CronTriggerSchema,
    IntervalTriggerSchema,
    DateTriggerSchema,
    JobCreateSchema,
    JobUpdateSchema,
    JobResponseSchema,
    JobExecutionSchema,
    JobStatisticsSchema,
    JobListResponseSchema,
    JobExecutionListSchema,
    SyncResultSchema,
    JobActionResponseSchema,
)


# ── CronTriggerSchema ───────────────────────────────────────────────────


class TestCronTriggerSchema:
    def test_defaults(self):
        r = CronTriggerSchema()
        assert r.year is None
        assert r.month is None
        assert r.day is None
        assert r.week is None
        assert r.day_of_week is None
        assert r.hour is None
        assert r.minute is None
        assert r.second is None
        assert r.start_date is None
        assert r.end_date is None
        assert r.timezone == "UTC"

    def test_with_values(self):
        r = CronTriggerSchema(hour=8, minute=0, day_of_week="mon")
        assert r.hour == 8
        assert r.day_of_week == "mon"


# ── IntervalTriggerSchema ───────────────────────────────────────────────


class TestIntervalTriggerSchema:
    def test_defaults(self):
        r = IntervalTriggerSchema()
        assert r.weeks == 0
        assert r.days == 0
        assert r.hours == 0
        assert r.minutes == 0
        assert r.seconds == 0
        assert r.timezone == "UTC"

    # --- validator: non-negative ---

    def test_negative_weeks(self):
        with pytest.raises(ValidationError, match="non-negative"):
            IntervalTriggerSchema(weeks=-1)

    def test_negative_days(self):
        with pytest.raises(ValidationError, match="non-negative"):
            IntervalTriggerSchema(days=-1)

    def test_negative_hours(self):
        with pytest.raises(ValidationError, match="non-negative"):
            IntervalTriggerSchema(hours=-1)

    def test_negative_minutes(self):
        with pytest.raises(ValidationError, match="non-negative"):
            IntervalTriggerSchema(minutes=-1)

    def test_negative_seconds(self):
        with pytest.raises(ValidationError, match="non-negative"):
            IntervalTriggerSchema(seconds=-1)


# ── DateTriggerSchema ───────────────────────────────────────────────────


class TestDateTriggerSchema:
    def test_defaults(self):
        r = DateTriggerSchema(run_date=datetime(2026, 6, 15))
        assert r.timezone == "UTC"


# ── JobCreateSchema ─────────────────────────────────────────────────────


class TestJobCreateSchema:
    def test_defaults(self):
        r = JobCreateSchema(
            name="test-job",
            job_func="app.tasks.run",
            trigger_type="cron",
            trigger_config={"hour": 8},
        )
        assert r.args == []
        assert r.kwargs == {}
        assert r.max_instances == 1
        assert r.misfire_grace_time is None
        assert r.coalesce is True
        assert r.description is None

    # --- name min_length=1, max_length=255 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            JobCreateSchema(
                name="",
                job_func="app.tasks.run",
                trigger_type="cron",
                trigger_config={"hour": 8},
            )

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            JobCreateSchema(
                name="x" * 256,
                job_func="app.tasks.run",
                trigger_type="cron",
                trigger_config={"hour": 8},
            )

    # --- trigger_type pattern: cron|interval|date ---

    def test_trigger_type_invalid(self):
        with pytest.raises(ValidationError):
            JobCreateSchema(
                name="test",
                job_func="app.tasks.run",
                trigger_type="weekly",
                trigger_config={"hour": 8},
            )

    def test_trigger_type_cron(self):
        r = JobCreateSchema(
            name="test",
            job_func="app.tasks.run",
            trigger_type="cron",
            trigger_config={"hour": 8},
        )
        assert r.trigger_type == "cron"

    def test_trigger_type_interval(self):
        r = JobCreateSchema(
            name="test",
            job_func="app.tasks.run",
            trigger_type="interval",
            trigger_config={"hours": 1},
        )
        assert r.trigger_type == "interval"

    def test_trigger_type_date(self):
        r = JobCreateSchema(
            name="test",
            job_func="app.tasks.run",
            trigger_type="date",
            trigger_config={"run_date": "2026-06-15T08:00:00"},
        )
        assert r.trigger_type == "date"

    # --- max_instances ge=1, le=10 ---

    def test_max_instances_below_min(self):
        with pytest.raises(ValidationError):
            JobCreateSchema(
                name="test",
                job_func="app.tasks.run",
                trigger_type="cron",
                trigger_config={"hour": 8},
                max_instances=0,
            )

    def test_max_instances_above_max(self):
        with pytest.raises(ValidationError):
            JobCreateSchema(
                name="test",
                job_func="app.tasks.run",
                trigger_type="cron",
                trigger_config={"hour": 8},
                max_instances=11,
            )

    # --- misfire_grace_time ge=0 ---

    def test_misfire_grace_time_negative(self):
        with pytest.raises(ValidationError):
            JobCreateSchema(
                name="test",
                job_func="app.tasks.run",
                trigger_type="cron",
                trigger_config={"hour": 8},
                misfire_grace_time=-1,
            )

    # --- description max_length=1000 ---

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            JobCreateSchema(
                name="test",
                job_func="app.tasks.run",
                trigger_type="cron",
                trigger_config={"hour": 8},
                description="x" * 1001,
            )

    # --- trigger_config validator (empty) ---

    def test_trigger_config_empty(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            JobCreateSchema(
                name="test",
                job_func="app.tasks.run",
                trigger_type="cron",
                trigger_config={},
            )

    # --- trigger_config validator (invalid interval config) ---

    def test_trigger_config_invalid_interval(self):
        with pytest.raises(ValidationError, match="Invalid interval"):
            JobCreateSchema(
                name="test",
                job_func="app.tasks.run",
                trigger_type="interval",
                trigger_config={"hours": -5},
            )


# ── JobUpdateSchema ─────────────────────────────────────────────────────


class TestJobUpdateSchema:
    def test_all_none(self):
        r = JobUpdateSchema()
        assert r.trigger_config is None
        assert r.args is None
        assert r.kwargs is None
        assert r.max_instances is None
        assert r.misfire_grace_time is None
        assert r.coalesce is None
        assert r.enabled is None
        assert r.description is None

    def test_max_instances_bounds(self):
        with pytest.raises(ValidationError):
            JobUpdateSchema(max_instances=0)

    def test_misfire_grace_time_bounds(self):
        with pytest.raises(ValidationError):
            JobUpdateSchema(misfire_grace_time=-1)


# ── JobResponseSchema ───────────────────────────────────────────────────


class TestJobResponseSchema:
    def test_valid(self):
        r = JobResponseSchema(
            id=uuid4(),
            name="test-job",
            job_func="app.tasks.run",
            trigger_type="cron",
            trigger_config={"hour": 8},
            args=[],
            kwargs={},
            next_run_time=None,
            last_run_time=None,
            run_count=0,
            max_instances=1,
            misfire_grace_time=None,
            coalesce=True,
            enabled=True,
            description=None,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
            created_by=None,
        )
        assert r.run_count == 0
        assert r.enabled is True


# ── JobExecutionSchema ──────────────────────────────────────────────────


class TestJobExecutionSchema:
    def test_valid(self):
        r = JobExecutionSchema(
            id=uuid4(),
            job_id=uuid4(),
            job_name="test-job",
            started_at=datetime(2026, 1, 1),
            finished_at=None,
            status="running",
            result=None,
            error=None,
            runtime_seconds=None,
            scheduled_run_time=datetime(2026, 1, 1),
        )
        assert r.status == "running"
        assert r.finished_at is None


# ── JobStatisticsSchema ─────────────────────────────────────────────────


class TestJobStatisticsSchema:
    def test_valid(self):
        r = JobStatisticsSchema(
            job_id="job-1",
            job_name="test-job",
            total_runs=100,
            success_count=95,
            failure_count=3,
            missed_count=2,
            average_runtime_seconds=5.5,
            last_run_time=None,
            next_run_time=None,
        )
        assert r.total_runs == 100


# ── List/Sync/Action schemas ────────────────────────────────────────────


class TestJobListResponseSchema:
    def test_valid(self):
        r = JobListResponseSchema(total=0, jobs=[])
        assert r.jobs == []


class TestJobExecutionListSchema:
    def test_valid(self):
        r = JobExecutionListSchema(total=0, limit=50, offset=0, executions=[])
        assert r.executions == []


class TestSyncResultSchema:
    def test_defaults(self):
        r = SyncResultSchema(added=1, removed=0, updated=2)
        assert r.timestamp is not None

    def test_custom_timestamp(self):
        ts = datetime(2026, 1, 1)
        r = SyncResultSchema(added=0, removed=0, updated=0, timestamp=ts)
        assert r.timestamp == ts


class TestJobActionResponseSchema:
    def test_defaults(self):
        r = JobActionResponseSchema(success=True, message="Done")
        assert r.job_id is None

    def test_with_job_id(self):
        uid = uuid4()
        r = JobActionResponseSchema(success=True, message="Done", job_id=uid)
        assert r.job_id == uid
