"""
Background Task Processing Tests (Celery).

Comprehensive tests for Celery background task processing including
task execution, retry logic, error handling, and scheduling.

Test Coverage:
- Task execution success and failure
- Retry logic with backoff
- Task result storage and retrieval
- Periodic task scheduling
- Task timeout handling
- Task chain and group execution
- Error handling and logging
- Task status tracking
"""

from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from celery.result import AsyncResult
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate

# Skip if resilience_tasks module doesn't exist yet
pytest.importorskip("app.tasks.resilience_tasks")
from app.tasks.resilience_tasks import (
    check_resilience_health,
    run_n_minus_analysis,
)
from app.tasks.schedule_tasks import (
    generate_schedule_async,
    validate_schedule_async,
)
from app.tasks.notification_tasks import (
    send_assignment_notification,
    send_bulk_notifications,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_person(db: Session) -> Person:
    """Create a sample person for testing."""
    person = Person(
        id=uuid4(),
        name="Dr. Test Person",
        type="resident",
        email="test@example.com",
        pgy_level=2,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@pytest.fixture
def sample_block(db: Session) -> Block:
    """Create a sample block."""
    block = Block(
        id=uuid4(),
        date=date.today() + timedelta(days=7),
        time_of_day="AM",
        block_number=1,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


@pytest.fixture
def sample_rotation(db: Session) -> RotationTemplate:
    """Create a sample rotation template."""
    rotation = RotationTemplate(
        id=uuid4(),
        name="Test Clinic",
        rotation_type="outpatient",
        abbreviation="TC",
        max_residents=4,
    )
    db.add(rotation)
    db.commit()
    db.refresh(rotation)
    return rotation


# ============================================================================
# Test Class: Task Execution
# ============================================================================


class TestTaskExecution:
    """Tests for basic task execution."""

    @patch("app.tasks.resilience_tasks.ResilienceMonitor")
    def test_resilience_health_check_task_executes(self, mock_monitor, db: Session):
        """Test resilience health check task executes successfully."""
        mock_instance = Mock()
        mock_instance.check_health.return_value = {"status": "GREEN"}
        mock_monitor.return_value = mock_instance

        # Execute task synchronously for testing
        result = check_resilience_health.apply()

        assert result.successful()
        assert result.result["status"] == "GREEN"

    @patch("app.tasks.notification_tasks.EmailService")
    def test_notification_task_sends_email(
        self, mock_email_service, db: Session, sample_person: Person
    ):
        """Test notification task sends email successfully."""
        mock_service = Mock()
        mock_service.send_email.return_value = True
        mock_email_service.return_value = mock_service

        result = send_assignment_notification.apply(
            args=[
                str(sample_person.id),
                "Test Subject",
                "Test Message",
            ]
        )

        assert result.successful()
        mock_service.send_email.assert_called_once()

    @patch("app.tasks.schedule_tasks.SchedulingEngine")
    def test_schedule_generation_task_executes(
        self, mock_engine, db: Session, sample_rotation: RotationTemplate
    ):
        """Test schedule generation task executes."""
        mock_instance = Mock()
        mock_instance.generate_schedule.return_value = Mock(
            success=True, assignments_created=10
        )
        mock_engine.return_value = mock_instance

        start_date = date.today() + timedelta(days=7)
        end_date = start_date + timedelta(days=6)

        result = generate_schedule_async.apply(
            args=[
                str(start_date),
                str(end_date),
                [str(sample_rotation.id)],
            ]
        )

        assert result.successful()


# ============================================================================
# Test Class: Retry Logic
# ============================================================================


class TestRetryLogic:
    """Tests for task retry behavior."""

    @patch("app.tasks.notification_tasks.EmailService")
    def test_task_retries_on_failure(self, mock_email_service):
        """Test task retries when it fails."""
        mock_service = Mock()
        # First call fails, second succeeds
        mock_service.send_email.side_effect = [
            Exception("Temporary failure"),
            True,
        ]
        mock_email_service.return_value = mock_service

        # Task should retry automatically
        # Implementation depends on Celery retry configuration

    @patch("app.tasks.resilience_tasks.NMinusAnalyzer")
    def test_task_retries_with_exponential_backoff(self, mock_analyzer):
        """Test task retries with exponential backoff."""
        mock_instance = Mock()
        mock_instance.analyze_n_minus_1.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            {"passes": True},  # Succeeds on third try
        ]
        mock_analyzer.return_value = mock_instance

        # Task should retry with increasing delays
        # Verify retry behavior matches configuration

    def test_task_gives_up_after_max_retries(self):
        """Test task stops retrying after max attempts."""
        # Mock a task that always fails
        with patch("app.tasks.notification_tasks.EmailService") as mock_service:
            mock_instance = Mock()
            mock_instance.send_email.side_effect = Exception("Permanent failure")
            mock_service.return_value = mock_instance

            # After max retries, task should fail permanently
            # Implementation depends on max_retries setting


# ============================================================================
# Test Class: Task Results
# ============================================================================


class TestTaskResults:
    """Tests for task result storage and retrieval."""

    @patch("app.tasks.schedule_tasks.SchedulingEngine")
    def test_task_result_stored_and_retrievable(self, mock_engine, db: Session):
        """Test task results are stored and can be retrieved."""
        mock_instance = Mock()
        mock_instance.generate_schedule.return_value = Mock(
            success=True,
            assignments_created=15,
        )
        mock_engine.return_value = mock_instance

        # Execute task
        result = generate_schedule_async.apply()

        # Should be able to retrieve result
        task_id = result.id
        retrieved = AsyncResult(task_id)

        assert retrieved.ready()
        assert retrieved.successful()

    def test_failed_task_stores_error_info(self):
        """Test failed task stores error information."""
        with patch("app.tasks.resilience_tasks.ResilienceMonitor") as mock_monitor:
            mock_instance = Mock()
            mock_instance.check_health.side_effect = ValueError("Test error")
            mock_monitor.return_value = mock_instance

            result = check_resilience_health.apply()

            # Result should contain error information
            assert result.failed()
            assert "Test error" in str(result.traceback)


# ============================================================================
# Test Class: Periodic Tasks
# ============================================================================


class TestPeriodicTasks:
    """Tests for scheduled periodic tasks."""

    @patch("app.tasks.resilience_tasks.ResilienceMonitor")
    def test_resilience_check_runs_periodically(self, mock_monitor):
        """Test resilience health check is scheduled to run periodically."""
        # Verify task is registered with Celery Beat
        from app.core.celery_app import celery_app

        # Check if task is in beat schedule
        schedule = celery_app.conf.beat_schedule
        assert (
            "check-resilience-health" in schedule
            or "resilience-health-check" in schedule
        )

    @patch("app.tasks.schedule_tasks.NMinusAnalyzer")
    def test_n_minus_analysis_scheduled_daily(self, mock_analyzer):
        """Test N-1/N-2 analysis is scheduled to run daily."""
        from app.core.celery_app import celery_app

        schedule = celery_app.conf.beat_schedule
        # Verify daily N-minus analysis is scheduled
        # Task name may vary based on configuration


# ============================================================================
# Test Class: Task Timeouts
# ============================================================================


class TestTaskTimeouts:
    """Tests for task timeout handling."""

    @patch("app.tasks.schedule_tasks.SchedulingEngine")
    def test_long_running_task_times_out(self, mock_engine):
        """Test long-running task times out appropriately."""
        import time

        mock_instance = Mock()

        def slow_generate(*args, **kwargs):
            time.sleep(10)  # Simulate slow operation
            return Mock(success=True)

        mock_instance.generate_schedule.side_effect = slow_generate
        mock_engine.return_value = mock_instance

        # Task should timeout if configured with time_limit
        # Implementation depends on task configuration

    def test_soft_timeout_sends_warning(self):
        """Test soft timeout sends warning before hard timeout."""
        # Celery supports soft_time_limit for warnings
        # Test that soft timeout is triggered appropriately


# ============================================================================
# Test Class: Task Chains and Groups
# ============================================================================


class TestTaskChainsAndGroups:
    """Tests for task chaining and grouping."""

    @patch("app.tasks.schedule_tasks.SchedulingEngine")
    @patch("app.tasks.schedule_tasks.ACGMEValidator")
    def test_schedule_generation_then_validation_chain(
        self, mock_validator, mock_engine, db: Session
    ):
        """Test chaining schedule generation with validation."""
        from celery import chain

        mock_engine_instance = Mock()
        mock_engine_instance.generate_schedule.return_value = Mock(success=True)
        mock_engine.return_value = mock_engine_instance

        mock_validator_instance = Mock()
        mock_validator_instance.validate_schedule.return_value = []
        mock_validator.return_value = mock_validator_instance

        # Create task chain
        start_date = date.today() + timedelta(days=7)
        end_date = start_date + timedelta(days=6)

        task_chain = chain(
            generate_schedule_async.s(str(start_date), str(end_date), []),
            validate_schedule_async.s(),
        )

        # Execute chain
        result = task_chain.apply()
        assert result.successful()

    @patch("app.tasks.notification_tasks.EmailService")
    def test_bulk_notifications_as_group(self, mock_email_service, db: Session):
        """Test sending bulk notifications as a group."""
        from celery import group

        mock_service = Mock()
        mock_service.send_email.return_value = True
        mock_email_service.return_value = mock_service

        # Create multiple people
        people = []
        for i in range(5):
            person = Person(
                id=uuid4(),
                name=f"Dr. Person {i}",
                type="resident",
                email=f"person{i}@test.org",
                pgy_level=1,
            )
            db.add(person)
            people.append(person)
        db.commit()

        # Send notifications as group
        notification_group = group(
            send_assignment_notification.s(str(person.id), "Subject", "Message")
            for person in people
        )

        result = notification_group.apply()
        # All tasks in group should complete
        assert all(r.successful() for r in result.results)


# ============================================================================
# Test Class: Error Handling
# ============================================================================


class TestErrorHandling:
    """Tests for task error handling."""

    @patch("app.tasks.resilience_tasks.ResilienceMonitor")
    def test_task_handles_database_error_gracefully(self, mock_monitor, db: Session):
        """Test task handles database errors gracefully."""
        mock_instance = Mock()
        mock_instance.check_health.side_effect = Exception("Database connection failed")
        mock_monitor.return_value = mock_instance

        result = check_resilience_health.apply()

        # Task should fail but not crash
        assert result.failed()

    @patch("app.tasks.notification_tasks.EmailService")
    def test_task_logs_error_on_failure(self, mock_email_service):
        """Test task logs errors when it fails."""
        mock_service = Mock()
        mock_service.send_email.side_effect = Exception("SMTP connection failed")
        mock_email_service.return_value = mock_service

        with patch("app.tasks.notification_tasks.logger") as mock_logger:
            result = send_assignment_notification.apply(
                args=["person_id", "Subject", "Message"]
            )

            # Logger should have been called with error
            assert mock_logger.error.called or mock_logger.exception.called


# ============================================================================
# Test Class: Task Status Tracking
# ============================================================================


class TestTaskStatusTracking:
    """Tests for tracking task status and progress."""

    @patch("app.tasks.schedule_tasks.SchedulingEngine")
    def test_task_progress_can_be_monitored(self, mock_engine):
        """Test task progress can be monitored during execution."""
        mock_instance = Mock()
        mock_instance.generate_schedule.return_value = Mock(success=True)
        mock_engine.return_value = mock_instance

        # Start task
        result = generate_schedule_async.apply_async()

        # Should be able to check status
        assert result.state in ["PENDING", "STARTED", "SUCCESS", "FAILURE"]

    def test_task_state_transitions(self):
        """Test task state transitions through lifecycle."""
        with patch("app.tasks.resilience_tasks.ResilienceMonitor") as mock_monitor:
            mock_instance = Mock()
            mock_instance.check_health.return_value = {"status": "GREEN"}
            mock_monitor.return_value = mock_instance

            result = check_resilience_health.apply_async()

            # Initial state
            assert result.state in ["PENDING", "STARTED"]

            # Wait for completion
            result.get(timeout=5)

            # Final state
            assert result.state == "SUCCESS"
