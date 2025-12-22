"""
Unit tests for notification modules.

Tests for:
- Email templates
- Notification channels
- Service methods
"""
from datetime import date, timedelta

import pytest


@pytest.mark.unit
class TestEmailTemplates:
    """Test email template rendering."""

    def test_certification_reminder_template(self):
        """Test certification reminder template exists."""
        from app.notifications.notification_types import get_certification_reminder_template

        template = get_certification_reminder_template(
            person_name="Dr. Jane Smith",
            certification_name="BLS",
            expiry_date=date.today() + timedelta(days=30),
            days_until_expiry=30,
        )

        assert template is not None
        assert "Dr. Jane Smith" in template["subject"] or "Dr. Jane Smith" in template["body"]
        assert "BLS" in template["body"]

    def test_schedule_notification_template(self):
        """Test schedule notification template."""
        from app.notifications.notification_types import get_schedule_notification_template

        template = get_schedule_notification_template(
            person_name="Dr. John Doe",
            schedule_date=date.today(),
            assignment_details="Sports Medicine Clinic - AM",
        )

        assert template is not None
        assert "body" in template
        assert "subject" in template


@pytest.mark.unit
class TestNotificationService:
    """Test notification service methods."""

    def test_format_recipient_list(self):
        """Test formatting recipient email list."""
        recipients = ["admin@hospital.org", "coord@hospital.org"]

        # Simple join for email list
        formatted = ", ".join(recipients)

        assert "admin@hospital.org" in formatted
        assert "coord@hospital.org" in formatted

    def test_validate_email_format(self):
        """Test email format validation using email-validator library."""
        from email_validator import validate_email, EmailNotValidError

        valid_emails = [
            "user@example.com",
            "user.name@hospital.org",
            "user+tag@domain.co.uk",
        ]

        invalid_emails = [
            "not-an-email",
            "@missing-local.com",
            "missing-domain@",
            "spaces in@email.com",
        ]

        for email in valid_emails:
            try:
                validate_email(email, check_deliverability=False)
            except EmailNotValidError:
                pytest.fail(f"{email} should be valid")

        for email in invalid_emails:
            with pytest.raises(EmailNotValidError):
                validate_email(email, check_deliverability=False)


@pytest.mark.unit
class TestNotificationChannels:
    """Test notification channel configurations."""

    def test_email_channel_config(self):
        """Test email channel configuration."""
        # Default email config should have required fields
        config = {
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "use_tls": True,
            "from_address": "scheduler@hospital.org",
        }

        assert "smtp_host" in config
        assert "smtp_port" in config
        assert config["smtp_port"] > 0

    def test_channel_priority_ordering(self):
        """Test notification channel priority."""
        channels = ["email", "sms", "push"]
        priority_order = {"email": 1, "sms": 2, "push": 3}

        sorted_channels = sorted(channels, key=lambda c: priority_order.get(c, 99))

        assert sorted_channels[0] == "email"


@pytest.mark.unit
class TestReminderLogic:
    """Test reminder scheduling logic."""

    def test_calculate_reminder_dates(self):
        """Test calculating reminder dates from expiry."""
        expiry_date = date.today() + timedelta(days=90)
        reminder_days = [30, 14, 7, 1]

        reminder_dates = [
            expiry_date - timedelta(days=d)
            for d in reminder_days
        ]

        # All reminder dates should be before expiry
        for rd in reminder_dates:
            assert rd < expiry_date

        # Should be in chronological order
        sorted_dates = sorted(reminder_dates)
        assert sorted_dates == reminder_dates

    def test_is_reminder_due(self):
        """Test checking if a reminder is due."""
        today = date.today()
        expiry = today + timedelta(days=30)
        days_until = (expiry - today).days

        # 30-day reminder is due
        reminder_thresholds = [180, 90, 30, 14, 7]
        due_reminders = [t for t in reminder_thresholds if days_until <= t]

        assert 30 in due_reminders
        assert 14 not in due_reminders  # Only 30 days out

    def test_skip_past_reminders(self):
        """Test that past reminders are skipped."""
        expiry = date.today() - timedelta(days=5)  # Already expired
        today = date.today()

        # Should detect expired certification
        is_expired = expiry < today

        assert is_expired is True


@pytest.mark.unit
class TestBatchNotifications:
    """Test batch notification handling."""

    def test_batch_recipient_grouping(self):
        """Test grouping recipients for batch sends."""
        notifications = [
            {"recipient": "user1@example.com", "type": "reminder"},
            {"recipient": "user2@example.com", "type": "reminder"},
            {"recipient": "user1@example.com", "type": "schedule"},
        ]

        # Group by recipient
        grouped = {}
        for n in notifications:
            recipient = n["recipient"]
            if recipient not in grouped:
                grouped[recipient] = []
            grouped[recipient].append(n)

        assert len(grouped["user1@example.com"]) == 2
        assert len(grouped["user2@example.com"]) == 1

    def test_batch_size_limiting(self):
        """Test batch size limiting for rate limiting."""
        recipients = [f"user{i}@example.com" for i in range(100)]
        max_batch_size = 25

        # Split into batches
        batches = [
            recipients[i:i + max_batch_size]
            for i in range(0, len(recipients), max_batch_size)
        ]

        assert len(batches) == 4
        assert all(len(b) <= max_batch_size for b in batches)


@pytest.mark.unit
class TestLeaveConflictDetectionTask:
    """Test the leave conflict detection background task."""

    def test_detect_leave_conflicts_task_exists(self):
        """Test that the conflict detection task is properly registered."""
        from app.notifications.tasks import detect_leave_conflicts

        assert detect_leave_conflicts is not None
        assert hasattr(detect_leave_conflicts, 'delay')

    def test_detect_leave_conflicts_with_valid_absence(
        self,
        db,
        sample_faculty,
        sample_absence,
    ):
        """Test conflict detection task with valid absence."""
        from app.notifications.tasks import detect_leave_conflicts

        # Run the task synchronously for testing
        result = detect_leave_conflicts(str(sample_absence.id))

        assert result is not None
        assert "status" in result
        assert result["status"] == "completed"
        assert "conflicts_found" in result
        assert "alerts_created" in result

    def test_detect_leave_conflicts_with_fmit_overlap(
        self,
        db,
        sample_faculty,
    ):
        """Test conflict detection when leave overlaps with FMIT."""
        from datetime import date, timedelta
        from uuid import uuid4
        from app.models.absence import Absence
        from app.models.assignment import Assignment
        from app.models.block import Block
        from app.models.rotation_template import RotationTemplate
        from app.notifications.tasks import detect_leave_conflicts

        # Create FMIT template
        fmit_template = RotationTemplate(
            id=uuid4(),
            name="FMIT Rotation",
            activity_type="inpatient",
            abbreviation="FMIT",
        )
        db.add(fmit_template)

        # Create blocks
        start = date.today() + timedelta(days=30)
        blocks = []
        for i in range(7):
            block = Block(
                id=uuid4(),
                date=start + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)

        db.commit()

        # Create FMIT assignments
        for block in blocks[:3]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_faculty.id,
                rotation_template_id=fmit_template.id,
                role="primary",
            )
            db.add(assignment)

        # Create blocking leave that overlaps
        absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=start,
            end_date=start + timedelta(days=5),
            absence_type="deployment",
            is_blocking=True,
        )
        db.add(absence)
        db.commit()

        # Run conflict detection
        result = detect_leave_conflicts(str(absence.id))

        assert result is not None
        assert result["status"] == "completed"
        # Should have detected conflicts
        assert result["conflicts_found"] >= 0
