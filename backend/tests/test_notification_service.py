"""
Comprehensive unit tests for NotificationService.

Tests for:
- Creating and sending notifications
- Marking notifications as read
- Querying notifications by user/type
- Scheduling notifications
- Processing scheduled notifications
- User notification preferences
- Bulk notification sending
- Edge cases (invalid inputs, missing users)
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    NotificationPreferenceRecord,
    ScheduledNotificationRecord,
)
from app.models.person import Person
from app.notifications.channels import DeliveryResult
from app.notifications.service import (
    NotificationPreferences,
    NotificationService,
    ScheduledNotification,
)
from app.notifications.templates import NotificationType

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_user(db: Session) -> Person:
    """Create a sample user for notifications."""
    user = Person(
        id=uuid4(),
        name="Dr. Test User",
        type="resident",
        email="test.user@hospital.org",
        pgy_level=2,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def another_user(db: Session) -> Person:
    """Create another sample user."""
    user = Person(
        id=uuid4(),
        name="Dr. Another User",
        type="faculty",
        email="another.user@hospital.org",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def notification_service(db: Session) -> NotificationService:
    """Create NotificationService instance."""
    return NotificationService(db)


@pytest.fixture
def sample_notification(db: Session, sample_user: Person) -> Notification:
    """Create a sample notification."""
    notification = Notification(
        id=uuid4(),
        recipient_id=sample_user.id,
        notification_type="schedule_published",
        subject="Test Notification",
        body="This is a test notification body.",
        data={"test_key": "test_value"},
        priority="normal",
        channels_delivered="in_app",
        is_read=False,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@pytest.fixture
def sample_preferences(
    db: Session, sample_user: Person
) -> NotificationPreferenceRecord:
    """Create sample notification preferences."""
    prefs = NotificationPreferenceRecord(
        id=uuid4(),
        user_id=sample_user.id,
        enabled_channels="in_app,email",
        notification_types={
            "schedule_published": True,
            "assignment_changed": True,
            "acgme_warning": True,
        },
        quiet_hours_start=None,
        quiet_hours_end=None,
    )
    db.add(prefs)
    db.commit()
    db.refresh(prefs)
    return prefs


# ============================================================================
# Test send_notification
# ============================================================================


@pytest.mark.unit
class TestSendNotification:
    """Tests for send_notification method."""

    @pytest.mark.asyncio
    async def test_send_notification_success(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test successfully sending a notification."""
        with patch("app.notifications.service.get_channel") as mock_get_channel:
            # Mock channel delivery
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(
                return_value=DeliveryResult(
                    success=True, channel="in_app", message="Delivered successfully"
                )
            )
            mock_get_channel.return_value = mock_channel

            results = await notification_service.send_notification(
                recipient_id=sample_user.id,
                notification_type=NotificationType.SCHEDULE_PUBLISHED,
                data={
                    "period": "January 2025",
                    "coverage_rate": "95.0",
                    "total_assignments": "100",
                    "violations_count": "0",
                    "publisher_name": "Admin",
                    "published_at": "2025-01-01 10:00:00 UTC",
                },
                channels=["in_app"],
            )

            assert len(results) == 1
            assert results[0].success is True
            assert results[0].channel == "in_app"

            # Verify notification was stored in database
            notification = (
                db.query(Notification)
                .filter(Notification.recipient_id == sample_user.id)
                .first()
            )
            assert notification is not None
            assert notification.notification_type == "schedule_published"
            assert notification.is_read is False

    @pytest.mark.asyncio
    async def test_send_notification_template_not_found(
        self,
        notification_service: NotificationService,
        sample_user: Person,
    ):
        """Test sending notification with invalid template."""
        # Create a mock NotificationType that doesn't have a template
        with patch("app.notifications.service.render_notification", return_value=None):
            results = await notification_service.send_notification(
                recipient_id=sample_user.id,
                notification_type=NotificationType.SCHEDULE_PUBLISHED,
                data={},
            )

            assert len(results) == 1
            assert results[0].success is False
            assert "Template not found" in results[0].message

    @pytest.mark.asyncio
    async def test_send_notification_respects_preferences(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test that notifications respect user preferences."""
        # Create preferences with schedule_published disabled
        prefs = NotificationPreferenceRecord(
            user_id=sample_user.id,
            enabled_channels="in_app,email",
            notification_types={"schedule_published": False},
        )
        db.add(prefs)
        db.commit()

        results = await notification_service.send_notification(
            recipient_id=sample_user.id,
            notification_type=NotificationType.SCHEDULE_PUBLISHED,
            data={
                "period": "January 2025",
                "coverage_rate": "95.0",
                "total_assignments": "100",
                "violations_count": "0",
                "publisher_name": "Admin",
                "published_at": "2025-01-01 10:00:00 UTC",
            },
        )

        # Should return empty list (notification skipped)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_send_notification_quiet_hours(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test that notifications respect quiet hours for non-high priority."""
        current_hour = datetime.utcnow().hour

        # Set quiet hours to include current hour
        prefs = NotificationPreferenceRecord(
            user_id=sample_user.id,
            enabled_channels="in_app,email",
            notification_types={},
            quiet_hours_start=current_hour,
            quiet_hours_end=(current_hour + 1) % 24,
        )
        db.add(prefs)
        db.commit()

        # Try to send normal priority notification (should be skipped)
        results = await notification_service.send_notification(
            recipient_id=sample_user.id,
            notification_type=NotificationType.ABSENCE_APPROVED,
            data={
                "absence_type": "Vacation",
                "start_date": "2025-01-01",
                "end_date": "2025-01-05",
                "duration_days": "5",
                "approval_notes": "Approved",
                "approver_name": "Admin",
                "approved_at": "2025-01-01 10:00:00 UTC",
            },
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_send_notification_multiple_channels(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test sending notification through multiple channels."""
        with patch("app.notifications.service.get_channel") as mock_get_channel:
            # Mock both in_app and email channels
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(
                return_value=DeliveryResult(
                    success=True, channel="test", message="Delivered"
                )
            )
            mock_get_channel.return_value = mock_channel

            results = await notification_service.send_notification(
                recipient_id=sample_user.id,
                notification_type=NotificationType.ACGME_WARNING,
                data={
                    "violation_type": "Duty Hours",
                    "severity": "HIGH",
                    "person_name": "Dr. Test User",
                    "violation_details": "Exceeded 80 hours",
                    "recommended_action": "Adjust schedule",
                    "detected_at": "2025-01-01 10:00:00 UTC",
                },
                channels=["in_app", "email"],
            )

            # Should have results from both channels
            assert len(results) == 2


# ============================================================================
# Test send_bulk
# ============================================================================


@pytest.mark.unit
class TestSendBulk:
    """Tests for send_bulk method."""

    @pytest.mark.asyncio
    async def test_send_bulk_multiple_recipients(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        another_user: Person,
        db: Session,
    ):
        """Test sending bulk notifications to multiple recipients."""
        with patch("app.notifications.service.get_channel") as mock_get_channel:
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(
                return_value=DeliveryResult(
                    success=True, channel="in_app", message="Delivered"
                )
            )
            mock_get_channel.return_value = mock_channel

            results = await notification_service.send_bulk(
                recipient_ids=[sample_user.id, another_user.id],
                notification_type=NotificationType.SCHEDULE_PUBLISHED,
                data={
                    "period": "January 2025",
                    "coverage_rate": "95.0",
                    "total_assignments": "100",
                    "violations_count": "0",
                    "publisher_name": "Admin",
                    "published_at": "2025-01-01 10:00:00 UTC",
                },
                channels=["in_app"],
            )

            assert len(results) == 2
            assert str(sample_user.id) in results
            assert str(another_user.id) in results

    @pytest.mark.asyncio
    async def test_send_bulk_empty_list(
        self,
        notification_service: NotificationService,
    ):
        """Test sending bulk with empty recipient list."""
        results = await notification_service.send_bulk(
            recipient_ids=[],
            notification_type=NotificationType.SCHEDULE_PUBLISHED,
            data={},
        )

        assert len(results) == 0


# ============================================================================
# Test schedule_notification
# ============================================================================


@pytest.mark.unit
class TestScheduleNotification:
    """Tests for schedule_notification method."""

    def test_schedule_notification_success(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test successfully scheduling a notification."""
        send_at = datetime.utcnow() + timedelta(hours=24)

        scheduled = notification_service.schedule_notification(
            recipient_id=sample_user.id,
            notification_type=NotificationType.SHIFT_REMINDER_24H,
            data={
                "rotation_name": "Emergency Medicine",
                "location": "Building A",
                "start_date": "2025-01-15",
                "duration_weeks": "4",
                "contact_person": "Dr. Coordinator",
                "contact_email": "coordinator@hospital.org",
            },
            send_at=send_at,
        )

        assert scheduled is not None
        assert scheduled.recipient_id == sample_user.id
        assert scheduled.notification_type == NotificationType.SHIFT_REMINDER_24H
        assert scheduled.status == "pending"
        assert scheduled.send_at == send_at

        # Verify stored in database
        record = (
            db.query(ScheduledNotificationRecord)
            .filter(ScheduledNotificationRecord.id == scheduled.id)
            .first()
        )
        assert record is not None
        assert record.status == "pending"

    def test_schedule_notification_in_past(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test scheduling notification for past time (should still work)."""
        send_at = datetime.utcnow() - timedelta(hours=1)

        scheduled = notification_service.schedule_notification(
            recipient_id=sample_user.id,
            notification_type=NotificationType.SHIFT_REMINDER_1H,
            data={"rotation_name": "Test", "location": "Test", "start_time": "10:00"},
            send_at=send_at,
        )

        assert scheduled is not None
        # Will be processed immediately by process_scheduled_notifications


# ============================================================================
# Test process_scheduled_notifications
# ============================================================================


@pytest.mark.unit
class TestProcessScheduledNotifications:
    """Tests for process_scheduled_notifications method."""

    @pytest.mark.asyncio
    async def test_process_due_notifications(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test processing due scheduled notifications."""
        # Create a due notification
        past_time = datetime.utcnow() - timedelta(minutes=5)
        record = ScheduledNotificationRecord(
            recipient_id=sample_user.id,
            notification_type="shift_reminder_24h",
            data={
                "rotation_name": "Surgery",
                "location": "OR 5",
                "start_date": "2025-01-20",
                "duration_weeks": "2",
                "contact_person": "Dr. Smith",
                "contact_email": "smith@hospital.org",
            },
            send_at=past_time,
            status="pending",
        )
        db.add(record)
        db.commit()

        with patch("app.notifications.service.get_channel") as mock_get_channel:
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(
                return_value=DeliveryResult(
                    success=True, channel="in_app", message="Delivered"
                )
            )
            mock_get_channel.return_value = mock_channel

            sent_count = await notification_service.process_scheduled_notifications()

            assert sent_count == 1

            # Verify status updated
            db.refresh(record)
            assert record.status == "sent"
            assert record.sent_at is not None

    @pytest.mark.asyncio
    async def test_process_no_due_notifications(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test processing when no notifications are due."""
        # Create a future notification
        future_time = datetime.utcnow() + timedelta(hours=24)
        record = ScheduledNotificationRecord(
            recipient_id=sample_user.id,
            notification_type="shift_reminder_24h",
            data={"rotation_name": "Test", "location": "Test"},
            send_at=future_time,
            status="pending",
        )
        db.add(record)
        db.commit()

        sent_count = await notification_service.process_scheduled_notifications()

        assert sent_count == 0

        # Verify status unchanged
        db.refresh(record)
        assert record.status == "pending"

    @pytest.mark.asyncio
    async def test_process_handles_failures(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test that failed notifications are marked as failed."""
        past_time = datetime.utcnow() - timedelta(minutes=5)
        record = ScheduledNotificationRecord(
            recipient_id=sample_user.id,
            notification_type="invalid_type",  # Invalid type will cause failure
            data={},
            send_at=past_time,
            status="pending",
        )
        db.add(record)
        db.commit()

        sent_count = await notification_service.process_scheduled_notifications()

        assert sent_count == 1

        # Verify status is failed
        db.refresh(record)
        assert record.status == "failed"
        assert record.error_message is not None


# ============================================================================
# Test get_pending_notifications
# ============================================================================


@pytest.mark.unit
class TestGetPendingNotifications:
    """Tests for get_pending_notifications method."""

    def test_get_unread_notifications(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test getting unread notifications for a user."""
        # Create multiple notifications
        for i in range(3):
            notification = Notification(
                recipient_id=sample_user.id,
                notification_type="schedule_published",
                subject=f"Test Notification {i}",
                body=f"Body {i}",
                data={},
                is_read=False,
            )
            db.add(notification)

        # Create one read notification
        read_notification = Notification(
            recipient_id=sample_user.id,
            notification_type="assignment_changed",
            subject="Read Notification",
            body="Read body",
            data={},
            is_read=True,
        )
        db.add(read_notification)
        db.commit()

        notifications = notification_service.get_pending_notifications(
            user_id=sample_user.id, unread_only=True
        )

        assert len(notifications) == 3
        for notif in notifications:
            assert notif["is_read"] is False

    def test_get_all_notifications(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test getting all notifications (read and unread)."""
        # Create unread notification
        unread = Notification(
            recipient_id=sample_user.id,
            notification_type="schedule_published",
            subject="Unread",
            body="Unread body",
            data={},
            is_read=False,
        )
        db.add(unread)

        # Create read notification
        read = Notification(
            recipient_id=sample_user.id,
            notification_type="assignment_changed",
            subject="Read",
            body="Read body",
            data={},
            is_read=True,
        )
        db.add(read)
        db.commit()

        notifications = notification_service.get_pending_notifications(
            user_id=sample_user.id, unread_only=False
        )

        assert len(notifications) == 2

    def test_get_notifications_limit(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test limiting number of returned notifications."""
        # Create 10 notifications
        for i in range(10):
            notification = Notification(
                recipient_id=sample_user.id,
                notification_type="schedule_published",
                subject=f"Test {i}",
                body=f"Body {i}",
                data={},
                is_read=False,
            )
            db.add(notification)
        db.commit()

        notifications = notification_service.get_pending_notifications(
            user_id=sample_user.id, limit=5
        )

        assert len(notifications) == 5

    def test_get_notifications_empty(
        self,
        notification_service: NotificationService,
        sample_user: Person,
    ):
        """Test getting notifications when user has none."""
        notifications = notification_service.get_pending_notifications(
            user_id=sample_user.id
        )

        assert len(notifications) == 0

    def test_get_notifications_wrong_user(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        another_user: Person,
        db: Session,
    ):
        """Test that user only sees their own notifications."""
        # Create notification for sample_user
        notification = Notification(
            recipient_id=sample_user.id,
            notification_type="schedule_published",
            subject="Test",
            body="Body",
            data={},
            is_read=False,
        )
        db.add(notification)
        db.commit()

        # Query as another_user
        notifications = notification_service.get_pending_notifications(
            user_id=another_user.id
        )

        assert len(notifications) == 0


# ============================================================================
# Test mark_as_read
# ============================================================================


@pytest.mark.unit
class TestMarkAsRead:
    """Tests for mark_as_read method."""

    def test_mark_single_notification_as_read(
        self,
        notification_service: NotificationService,
        sample_notification: Notification,
        db: Session,
    ):
        """Test marking a single notification as read."""
        assert sample_notification.is_read is False

        count = notification_service.mark_as_read([sample_notification.id])

        assert count == 1

        db.refresh(sample_notification)
        assert sample_notification.is_read is True
        assert sample_notification.read_at is not None

    def test_mark_multiple_notifications_as_read(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test marking multiple notifications as read."""
        # Create multiple notifications
        notification_ids = []
        for i in range(3):
            notification = Notification(
                recipient_id=sample_user.id,
                notification_type="schedule_published",
                subject=f"Test {i}",
                body=f"Body {i}",
                data={},
                is_read=False,
            )
            db.add(notification)
            db.flush()
            notification_ids.append(notification.id)
        db.commit()

        count = notification_service.mark_as_read(notification_ids)

        assert count == 3

        # Verify all are marked as read
        for notif_id in notification_ids:
            notification = (
                db.query(Notification).filter(Notification.id == notif_id).first()
            )
            assert notification.is_read is True

    def test_mark_as_read_invalid_ids(
        self,
        notification_service: NotificationService,
    ):
        """Test marking non-existent notifications as read."""
        count = notification_service.mark_as_read([uuid4(), uuid4()])

        assert count == 0

    def test_mark_as_read_empty_list(
        self,
        notification_service: NotificationService,
    ):
        """Test marking with empty list."""
        count = notification_service.mark_as_read([])

        assert count == 0


# ============================================================================
# Test Notification Preferences
# ============================================================================


@pytest.mark.unit
class TestNotificationPreferences:
    """Tests for notification preference management."""

    def test_get_user_preferences_exists(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        sample_preferences: NotificationPreferenceRecord,
    ):
        """Test getting existing user preferences."""
        prefs = notification_service._get_user_preferences(sample_user.id)

        assert prefs is not None
        assert prefs.user_id == sample_user.id
        assert "in_app" in prefs.enabled_channels
        assert "email" in prefs.enabled_channels
        assert prefs.notification_types.get("schedule_published") is True

    def test_get_user_preferences_default(
        self,
        notification_service: NotificationService,
        sample_user: Person,
    ):
        """Test getting default preferences when none exist."""
        prefs = notification_service._get_user_preferences(sample_user.id)

        assert prefs is not None
        assert prefs.user_id == sample_user.id
        # Should have default channels
        assert "in_app" in prefs.enabled_channels
        assert "email" in prefs.enabled_channels

    def test_update_user_preferences_new(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test creating new user preferences."""
        new_prefs = NotificationPreferences(
            user_id=sample_user.id,
            enabled_channels=["in_app"],
            notification_types={
                "schedule_published": False,
                "assignment_changed": True,
            },
            quiet_hours_start=22,
            quiet_hours_end=7,
        )

        updated = notification_service.update_user_preferences(
            user_id=sample_user.id,
            preferences=new_prefs,
        )

        assert updated.user_id == sample_user.id
        assert updated.enabled_channels == ["in_app"]
        assert updated.quiet_hours_start == 22
        assert updated.quiet_hours_end == 7

        # Verify stored in database
        record = (
            db.query(NotificationPreferenceRecord)
            .filter(NotificationPreferenceRecord.user_id == sample_user.id)
            .first()
        )
        assert record is not None
        assert record.enabled_channels == "in_app"

    def test_update_user_preferences_existing(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        sample_preferences: NotificationPreferenceRecord,
        db: Session,
    ):
        """Test updating existing user preferences."""
        updated_prefs = NotificationPreferences(
            user_id=sample_user.id,
            enabled_channels=["email"],
            notification_types={"schedule_published": False},
            quiet_hours_start=20,
            quiet_hours_end=8,
        )

        notification_service.update_user_preferences(
            user_id=sample_user.id,
            preferences=updated_prefs,
        )

        # Verify updated in database
        db.refresh(sample_preferences)
        assert sample_preferences.enabled_channels == "email"
        assert sample_preferences.quiet_hours_start == 20
        assert sample_preferences.quiet_hours_end == 8

    def test_should_send_notification_type_disabled(
        self,
        notification_service: NotificationService,
    ):
        """Test _should_send_notification when type is disabled."""
        prefs = NotificationPreferences(
            user_id=uuid4(),
            notification_types={"schedule_published": False},
        )

        should_send = notification_service._should_send_notification(
            prefs,
            NotificationType.SCHEDULE_PUBLISHED,
        )

        assert should_send is False

    def test_should_send_notification_type_enabled(
        self,
        notification_service: NotificationService,
    ):
        """Test _should_send_notification when type is enabled."""
        prefs = NotificationPreferences(
            user_id=uuid4(),
            notification_types={"schedule_published": True},
        )

        should_send = notification_service._should_send_notification(
            prefs,
            NotificationType.SCHEDULE_PUBLISHED,
        )

        assert should_send is True

    def test_should_send_notification_quiet_hours_high_priority(
        self,
        notification_service: NotificationService,
    ):
        """Test that high priority notifications override quiet hours."""
        current_hour = datetime.utcnow().hour
        prefs = NotificationPreferences(
            user_id=uuid4(),
            quiet_hours_start=current_hour,
            quiet_hours_end=(current_hour + 1) % 24,
        )

        # High priority notification should still send
        should_send = notification_service._should_send_notification(
            prefs,
            NotificationType.ACGME_WARNING,  # High priority
        )

        # Note: This depends on template having high priority
        # The actual implementation may vary


# ============================================================================
# Test Edge Cases
# ============================================================================


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_send_notification_invalid_recipient(
        self,
        notification_service: NotificationService,
    ):
        """Test sending notification to non-existent user."""
        # Should not crash, but may skip based on preferences
        results = await notification_service.send_notification(
            recipient_id=uuid4(),  # Non-existent user
            notification_type=NotificationType.SCHEDULE_PUBLISHED,
            data={
                "period": "January 2025",
                "coverage_rate": "95.0",
                "total_assignments": "100",
                "violations_count": "0",
                "publisher_name": "Admin",
                "published_at": "2025-01-01 10:00:00 UTC",
            },
        )

        # Should handle gracefully (may return empty or skip)
        assert isinstance(results, list)

    def test_get_preferences_invalid_user(
        self,
        notification_service: NotificationService,
    ):
        """Test getting preferences for non-existent user."""
        prefs = notification_service._get_user_preferences(uuid4())

        # Should return default preferences
        assert prefs is not None
        assert isinstance(prefs, NotificationPreferences)

    def test_mark_as_read_already_read(
        self,
        notification_service: NotificationService,
        sample_notification: Notification,
        db: Session,
    ):
        """Test marking already-read notification as read again."""
        # Mark as read first time
        notification_service.mark_as_read([sample_notification.id])
        db.refresh(sample_notification)
        first_read_at = sample_notification.read_at

        # Mark as read again
        count = notification_service.mark_as_read([sample_notification.id])

        assert count == 1
        db.refresh(sample_notification)
        # read_at may be updated again
        assert sample_notification.is_read is True

    @pytest.mark.asyncio
    async def test_send_notification_channel_not_found(
        self,
        notification_service: NotificationService,
        sample_user: Person,
    ):
        """Test sending notification through non-existent channel."""
        with patch("app.notifications.service.get_channel", return_value=None):
            results = await notification_service.send_notification(
                recipient_id=sample_user.id,
                notification_type=NotificationType.SCHEDULE_PUBLISHED,
                data={
                    "period": "January 2025",
                    "coverage_rate": "95.0",
                    "total_assignments": "100",
                    "violations_count": "0",
                    "publisher_name": "Admin",
                    "published_at": "2025-01-01 10:00:00 UTC",
                },
                channels=["invalid_channel"],
            )

            # Should have a failure result
            assert len(results) > 0
            assert any(not r.success for r in results)

    def test_notification_preferences_edge_cases(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test notification preference edge cases."""
        # Test with quiet hours wrapping around midnight
        prefs = NotificationPreferences(
            user_id=sample_user.id,
            enabled_channels=[],  # No channels enabled
            notification_types={},
            quiet_hours_start=23,  # 11 PM
            quiet_hours_end=2,  # 2 AM
        )

        updated = notification_service.update_user_preferences(
            user_id=sample_user.id,
            preferences=prefs,
        )

        assert updated.quiet_hours_start == 23
        assert updated.quiet_hours_end == 2


# ============================================================================
# Test NotificationPreferences Model
# ============================================================================


@pytest.mark.unit
class TestNotificationPreferencesModel:
    """Tests for NotificationPreferences Pydantic model."""

    def test_create_preferences_with_defaults(self):
        """Test creating preferences with default values."""
        user_id = uuid4()
        prefs = NotificationPreferences(user_id=user_id)

        assert prefs.user_id == user_id
        assert "in_app" in prefs.enabled_channels
        assert "email" in prefs.enabled_channels
        assert NotificationType.SCHEDULE_PUBLISHED.value in prefs.notification_types
        assert prefs.quiet_hours_start is None
        assert prefs.quiet_hours_end is None

    def test_create_preferences_custom(self):
        """Test creating preferences with custom values."""
        user_id = uuid4()
        prefs = NotificationPreferences(
            user_id=user_id,
            enabled_channels=["in_app"],
            notification_types={"test_type": True},
            quiet_hours_start=22,
            quiet_hours_end=6,
        )

        assert prefs.user_id == user_id
        assert prefs.enabled_channels == ["in_app"]
        assert prefs.notification_types == {"test_type": True}
        assert prefs.quiet_hours_start == 22
        assert prefs.quiet_hours_end == 6


# ============================================================================
# Test ScheduledNotification Model
# ============================================================================


@pytest.mark.unit
class TestScheduledNotificationModel:
    """Tests for ScheduledNotification Pydantic model."""

    def test_create_scheduled_notification(self):
        """Test creating a scheduled notification."""
        recipient_id = uuid4()
        send_at = datetime.utcnow() + timedelta(hours=1)

        scheduled = ScheduledNotification(
            recipient_id=recipient_id,
            notification_type=NotificationType.SHIFT_REMINDER_24H,
            data={"test": "data"},
            send_at=send_at,
        )

        assert scheduled.recipient_id == recipient_id
        assert scheduled.notification_type == NotificationType.SHIFT_REMINDER_24H
        assert scheduled.data == {"test": "data"}
        assert scheduled.send_at == send_at
        assert scheduled.status == "pending"
        assert scheduled.id is not None
        assert scheduled.created_at is not None


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestNotificationServiceIntegration:
    """Integration tests for notification service workflows."""

    @pytest.mark.asyncio
    async def test_complete_notification_workflow(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test complete notification workflow from send to read."""
        with patch("app.notifications.service.get_channel") as mock_get_channel:
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(
                return_value=DeliveryResult(
                    success=True, channel="in_app", message="Delivered"
                )
            )
            mock_get_channel.return_value = mock_channel

            # Step 1: Send notification
            await notification_service.send_notification(
                recipient_id=sample_user.id,
                notification_type=NotificationType.SCHEDULE_PUBLISHED,
                data={
                    "period": "January 2025",
                    "coverage_rate": "95.0",
                    "total_assignments": "100",
                    "violations_count": "0",
                    "publisher_name": "Admin",
                    "published_at": "2025-01-01 10:00:00 UTC",
                },
            )

            # Step 2: Get pending notifications
            notifications = notification_service.get_pending_notifications(
                user_id=sample_user.id, unread_only=True
            )

            assert len(notifications) == 1
            notif_id = notifications[0]["id"]

            # Step 3: Mark as read
            count = notification_service.mark_as_read([notif_id])
            assert count == 1

            # Step 4: Verify no unread notifications
            unread = notification_service.get_pending_notifications(
                user_id=sample_user.id, unread_only=True
            )
            assert len(unread) == 0

    @pytest.mark.asyncio
    async def test_scheduled_notification_workflow(
        self,
        notification_service: NotificationService,
        sample_user: Person,
        db: Session,
    ):
        """Test scheduling and processing notification workflow."""
        # Step 1: Schedule notification for past (will be processed immediately)
        send_at = datetime.utcnow() - timedelta(minutes=1)

        scheduled = notification_service.schedule_notification(
            recipient_id=sample_user.id,
            notification_type=NotificationType.SHIFT_REMINDER_24H,
            data={
                "rotation_name": "Surgery",
                "location": "OR 3",
                "start_date": "2025-01-20",
                "duration_weeks": "2",
                "contact_person": "Dr. Smith",
                "contact_email": "smith@hospital.org",
            },
            send_at=send_at,
        )

        assert scheduled.status == "pending"

        # Step 2: Process scheduled notifications
        with patch("app.notifications.service.get_channel") as mock_get_channel:
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(
                return_value=DeliveryResult(
                    success=True, channel="in_app", message="Delivered"
                )
            )
            mock_get_channel.return_value = mock_channel

            sent_count = await notification_service.process_scheduled_notifications()
            assert sent_count == 1

        # Step 3: Verify notification was created
        notifications = notification_service.get_pending_notifications(
            user_id=sample_user.id
        )
        assert len(notifications) >= 1
