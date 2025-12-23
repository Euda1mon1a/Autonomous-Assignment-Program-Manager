"""
Tests for background job scheduler.

Tests the scheduler functionality including:
- Job creation and management
- Trigger types (cron, interval, date)
- Job persistence
- Job execution tracking
- API endpoints
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.scheduler.jobs import JobChain, get_job_function, scheduled_job
from app.scheduler.persistence import JobPersistence
from app.scheduler.triggers import (
    CronTriggerConfig,
    DateTriggerConfig,
    IntervalTriggerConfig,
    create_trigger,
)

# ============================================================================
# Trigger Tests
# ============================================================================


class TestTriggers:
    """Test trigger configurations."""

    def test_cron_trigger_config(self):
        """Test cron trigger configuration."""
        config = CronTriggerConfig(hour=3, minute=0, timezone="UTC")

        trigger = config.to_apscheduler_trigger()
        assert trigger is not None

    def test_interval_trigger_config(self):
        """Test interval trigger configuration."""
        config = IntervalTriggerConfig(hours=2, minutes=30, timezone="UTC")

        trigger = config.to_apscheduler_trigger()
        assert trigger is not None

    def test_interval_trigger_validation(self):
        """Test interval trigger validates non-negative values."""
        with pytest.raises(ValueError):
            IntervalTriggerConfig(hours=-1)

    def test_date_trigger_config(self):
        """Test date trigger configuration."""
        run_date = datetime.utcnow() + timedelta(hours=1)
        config = DateTriggerConfig(run_date=run_date, timezone="UTC")

        trigger = config.to_apscheduler_trigger()
        assert trigger is not None

    def test_create_trigger_cron(self):
        """Test creating cron trigger from dict."""
        trigger = create_trigger("cron", {"hour": 3, "minute": 0})
        assert trigger is not None

    def test_create_trigger_interval(self):
        """Test creating interval trigger from dict."""
        trigger = create_trigger("interval", {"hours": 2})
        assert trigger is not None

    def test_create_trigger_date(self):
        """Test creating date trigger from dict."""
        run_date = datetime.utcnow() + timedelta(hours=1)
        trigger = create_trigger("date", {"run_date": run_date})
        assert trigger is not None

    def test_create_trigger_invalid_type(self):
        """Test creating trigger with invalid type."""
        with pytest.raises(ValueError, match="Invalid trigger type"):
            create_trigger("invalid", {})


# ============================================================================
# Job Decorator Tests
# ============================================================================


class TestJobDecorator:
    """Test job decorator functionality."""

    def test_scheduled_job_decorator(self):
        """Test scheduled job decorator adds metadata."""

        @scheduled_job(name="test_job", description="Test job", max_instances=2)
        def test_func():
            return "test"

        assert hasattr(test_func, "_scheduled_job")
        assert test_func._scheduled_job is True
        assert test_func._job_name == "test_job"
        assert test_func._job_description == "Test job"
        assert test_func._max_instances == 2

    def test_scheduled_job_default_name(self):
        """Test scheduled job decorator uses function name by default."""

        @scheduled_job()
        def my_custom_job():
            return "test"

        assert my_custom_job._job_name == "my_custom_job"

    def test_get_job_function(self):
        """Test getting job function by path."""
        func = get_job_function("app.scheduler.jobs.heartbeat_job")
        assert callable(func)


# ============================================================================
# Job Chain Tests
# ============================================================================


class TestJobChain:
    """Test job chaining functionality."""

    def test_job_chain_creation(self):
        """Test creating a job chain."""
        chain = JobChain()
        assert chain.jobs == []

    def test_job_chain_add_job(self):
        """Test adding jobs to chain."""

        def job1():
            return 1

        def job2(x):
            return x + 1

        chain = JobChain()
        chain.add_job("job1", job1)
        chain.add_job("job2", job2)

        assert len(chain.jobs) == 2
        assert chain.jobs[0]["name"] == "job1"
        assert chain.jobs[1]["name"] == "job2"

    def test_job_chain_execution(self):
        """Test executing a job chain."""

        def add_one(x=0):
            return x + 1

        def multiply_by_two(x):
            return x * 2

        chain = JobChain()
        chain.add_job("add", add_one, kwargs={"x": 5})
        chain.add_job("multiply", multiply_by_two)

        result = chain.execute()
        assert result == 12  # (5 + 1) * 2

    def test_job_chain_failure(self):
        """Test job chain stops on failure."""

        def failing_job():
            raise ValueError("Job failed")

        chain = JobChain()
        chain.add_job("failing", failing_job)

        with pytest.raises(ValueError, match="Job failed"):
            chain.execute()


# ============================================================================
# Persistence Tests
# ============================================================================


class TestJobPersistence:
    """Test job persistence layer."""

    def test_create_job(self, db: Session):
        """Test creating a scheduled job in database."""
        persistence = JobPersistence(db)

        job = persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3, "minute": 0},
            description="Test job",
        )

        assert job.id is not None
        assert job.name == "test_job"
        assert job.trigger_type == "cron"
        assert job.enabled is True

    def test_create_duplicate_job_fails(self, db: Session):
        """Test creating duplicate job raises error."""
        persistence = JobPersistence(db)

        persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
        )

        with pytest.raises(ValueError, match="already exists"):
            persistence.create_job(
                name="test_job",
                job_func="app.scheduler.jobs.heartbeat_job",
                trigger_type="cron",
                trigger_config={"hour": 3},
            )

    def test_get_job_by_id(self, db: Session):
        """Test getting job by ID."""
        persistence = JobPersistence(db)

        job = persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
        )

        retrieved = persistence.get_job_by_id(job.id)
        assert retrieved is not None
        assert retrieved.id == job.id
        assert retrieved.name == job.name

    def test_get_job_by_name(self, db: Session):
        """Test getting job by name."""
        persistence = JobPersistence(db)

        job = persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
        )

        retrieved = persistence.get_job_by_name("test_job")
        assert retrieved is not None
        assert retrieved.id == job.id

    def test_get_all_jobs(self, db: Session):
        """Test getting all jobs."""
        persistence = JobPersistence(db)

        persistence.create_job(
            name="job1",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
        )

        persistence.create_job(
            name="job2",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="interval",
            trigger_config={"hours": 2},
        )

        jobs = persistence.get_all_jobs(enabled_only=False)
        assert len(jobs) == 2

    def test_get_enabled_jobs_only(self, db: Session):
        """Test getting only enabled jobs."""
        persistence = JobPersistence(db)

        persistence.create_job(
            name="enabled_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
            enabled=True,
        )

        persistence.create_job(
            name="disabled_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 4},
            enabled=False,
        )

        jobs = persistence.get_all_jobs(enabled_only=True)
        assert len(jobs) == 1
        assert jobs[0].name == "enabled_job"

    def test_update_job(self, db: Session):
        """Test updating a job."""
        persistence = JobPersistence(db)

        job = persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
            description="Original description",
        )

        updated = persistence.update_job(
            job.id,
            description="Updated description",
            enabled=False,
        )

        assert updated is not None
        assert updated.description == "Updated description"
        assert updated.enabled is False

    def test_delete_job(self, db: Session):
        """Test deleting a job."""
        persistence = JobPersistence(db)

        job = persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
        )

        success = persistence.delete_job(job.id)
        assert success is True

        retrieved = persistence.get_job_by_id(job.id)
        assert retrieved is None

    def test_record_execution(self, db: Session):
        """Test recording job execution."""
        persistence = JobPersistence(db)

        job = persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
        )

        execution = persistence.record_execution_start(
            job_id=job.id,
            job_name=job.name,
            scheduled_run_time=datetime.utcnow(),
        )

        assert execution.id is not None
        assert execution.status == "running"

    def test_record_execution_success(self, db: Session):
        """Test recording successful execution."""
        persistence = JobPersistence(db)

        job = persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
        )

        execution = persistence.record_execution_start(
            job_id=job.id,
            job_name=job.name,
            scheduled_run_time=datetime.utcnow(),
        )

        persistence.record_execution_success(execution.id, result={"status": "ok"})

        db.refresh(execution)
        assert execution.status == "success"
        assert execution.result == {"status": "ok"}
        assert execution.finished_at is not None

    def test_record_execution_failure(self, db: Session):
        """Test recording failed execution."""
        persistence = JobPersistence(db)

        job = persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
        )

        execution = persistence.record_execution_start(
            job_id=job.id,
            job_name=job.name,
            scheduled_run_time=datetime.utcnow(),
        )

        persistence.record_execution_failure(
            execution.id, error="Test error", traceback="Test traceback"
        )

        db.refresh(execution)
        assert execution.status == "failure"
        assert execution.error == "Test error"
        assert execution.traceback == "Test traceback"

    def test_get_job_statistics(self, db: Session):
        """Test getting job statistics."""
        persistence = JobPersistence(db)

        job = persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
        )

        # Create some executions
        for i in range(3):
            execution = persistence.record_execution_start(
                job_id=job.id,
                job_name=job.name,
                scheduled_run_time=datetime.utcnow(),
            )
            persistence.record_execution_success(execution.id)

        # Create one failure
        execution = persistence.record_execution_start(
            job_id=job.id,
            job_name=job.name,
            scheduled_run_time=datetime.utcnow(),
        )
        persistence.record_execution_failure(execution.id, error="Test error")

        stats = persistence.get_job_statistics(job.id)

        assert stats["success_count"] == 3
        assert stats["failure_count"] == 1


# ============================================================================
# API Endpoint Tests
# ============================================================================


class TestSchedulerAPI:
    """Test scheduler API endpoints."""

    def test_create_job_unauthorized(self, client: TestClient):
        """Test creating job without authentication fails."""
        response = client.post(
            "/api/v1/scheduler/jobs",
            json={
                "name": "test_job",
                "job_func": "app.scheduler.jobs.heartbeat_job",
                "trigger_type": "cron",
                "trigger_config": {"hour": 3},
            },
        )
        assert response.status_code == 401

    def test_create_job_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test creating job with valid data."""
        response = client.post(
            "/api/v1/scheduler/jobs",
            headers=auth_headers,
            json={
                "name": "test_job",
                "job_func": "app.scheduler.jobs.heartbeat_job",
                "trigger_type": "cron",
                "trigger_config": {"hour": 3, "minute": 0},
                "description": "Test job",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test_job"
        assert data["trigger_type"] == "cron"
        assert data["enabled"] is True

    def test_create_job_invalid_trigger(self, client: TestClient, auth_headers: dict):
        """Test creating job with invalid trigger config."""
        response = client.post(
            "/api/v1/scheduler/jobs",
            headers=auth_headers,
            json={
                "name": "test_job",
                "job_func": "app.scheduler.jobs.heartbeat_job",
                "trigger_type": "invalid",
                "trigger_config": {"hour": 3},
            },
        )

        assert response.status_code == 422

    def test_list_jobs(self, client: TestClient, auth_headers: dict, db: Session):
        """Test listing all jobs."""
        # Create a job first
        persistence = JobPersistence(db)
        persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
        )

        response = client.get("/api/v1/scheduler/jobs", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_get_job(self, client: TestClient, auth_headers: dict, db: Session):
        """Test getting a specific job."""
        persistence = JobPersistence(db)
        job = persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
        )

        response = client.get(f"/api/v1/scheduler/jobs/{job.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_job"

    def test_get_nonexistent_job(self, client: TestClient, auth_headers: dict):
        """Test getting a nonexistent job returns 404."""
        response = client.get(f"/api/v1/scheduler/jobs/{uuid4()}", headers=auth_headers)

        assert response.status_code == 404

    def test_update_job(self, client: TestClient, auth_headers: dict, db: Session):
        """Test updating a job."""
        persistence = JobPersistence(db)
        job = persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
            description="Original",
        )

        response = client.patch(
            f"/api/v1/scheduler/jobs/{job.id}",
            headers=auth_headers,
            json={"description": "Updated"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated"

    def test_delete_job(self, client: TestClient, auth_headers: dict, db: Session):
        """Test deleting a job."""
        persistence = JobPersistence(db)
        job = persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
        )

        response = client.delete(
            f"/api/v1/scheduler/jobs/{job.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_job_statistics(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test getting job statistics."""
        persistence = JobPersistence(db)
        job = persistence.create_job(
            name="test_job",
            job_func="app.scheduler.jobs.heartbeat_job",
            trigger_type="cron",
            trigger_config={"hour": 3},
        )

        response = client.get(
            f"/api/v1/scheduler/jobs/{job.id}/statistics", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_name" in data
        assert data["job_name"] == "test_job"
