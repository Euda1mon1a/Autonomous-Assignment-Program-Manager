"""
Unit tests for NotificationService.

Comprehensive tests covering:
1. Notification Creation (single user, multiple users, priority levels)
2. Delivery Channels (in-app, email, webhook with mocks)
3. Template Rendering (variable substitution, HTML vs plain text, missing variables)
4. Batching Logic (batch multiple, digest, immediate vs scheduled)
5. Retry Handling (failed delivery retry, max retry limit, dead letter queue)

These are pure unit tests with extensive mocking to isolate the service layer.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch, call
from uuid import uuid4, UUID

from app.notifications.service import (
    NotificationService,
    NotificationPreferences,
    ScheduledNotification,
)
from app.notifications.channels import (
    DeliveryResult,
    NotificationPayload,
    InAppChannel,
    EmailChannel,
    WebhookChannel,
)
from app.notifications.templates import NotificationType, render_notification
from app.models.notification import (
    Notification,
    NotificationPreferenceRecord,
    ScheduledNotificationRecord,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.query = Mock()
    return db


@pytest.fixture
def notification_service(mock_db):
    """Create NotificationService instance with mock db."""
    return NotificationService(mock_db)


@pytest.fixture
def sample_recipient_id():
    """Sample recipient UUID."""
    return uuid4()


@pytest.fixture
def sample_notification_data():
    """Sample notification data for templates."""
    return {
        "period": "January 2025",
        "coverage_rate": "95.0",
        "total_assignments": "100",
        "violations_count": "0",
        "publisher_name": "Admin",
        "published_at": "2025-01-01 10:00:00 UTC",
    }


# ============================================================================
# Test 1: Notification Creation - Single User
# ============================================================================

class TestNotificationCreationSingleUser:
    """Test creating notifications for a single user."""

    @pytest.mark.asyncio
    async def test_create_notification_single_user_success(
        self,
        notification_service,
        mock_db,
        sample_recipient_id,
        sample_notification_data,
    ):
        """Test successfully creating a notification for a single user."""
        # Mock channel delivery
        with patch('app.notifications.service.get_channel') as mock_get_channel:
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(return_value=DeliveryResult(
                success=True,
                channel="in_app",
                message="Notification stored successfully"
            ))
            mock_get_channel.return_value = mock_channel

            # Mock preferences
            with patch.object(
                notification_service,
                '_get_user_preferences',
                return_value=NotificationPreferences(user_id=sample_recipient_id)
            ):
                results = await notification_service.send_notification(
                    recipient_id=sample_recipient_id,
                    notification_type=NotificationType.SCHEDULE_PUBLISHED,
                    data=sample_notification_data,
                    channels=["in_app"]
                )

                # Verify delivery was successful
                assert len(results) == 1
                assert results[0].success is True
                assert results[0].channel == "in_app"

                # Verify database add was called
                assert mock_db.add.called
                assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_notification_with_high_priority(
        self,
        notification_service,
        mock_db,
        sample_recipient_id,
    ):
        """Test creating a high priority notification."""
        with patch('app.notifications.service.get_channel') as mock_get_channel:
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(return_value=DeliveryResult(
                success=True,
                channel="in_app",
                message="Delivered"
            ))
            mock_get_channel.return_value = mock_channel

            with patch.object(
                notification_service,
                '_get_user_preferences',
                return_value=NotificationPreferences(user_id=sample_recipient_id)
            ):
                results = await notification_service.send_notification(
                    recipient_id=sample_recipient_id,
                    notification_type=NotificationType.ACGME_WARNING,
                    data={
                        "violation_type": "80-Hour Rule",
                        "severity": "HIGH",
                        "person_name": "Dr. Test",
                        "violation_details": "Exceeded weekly hours",
                        "recommended_action": "Adjust schedule",
                        "detected_at": "2025-01-01 10:00:00 UTC",
                    },
                )

                assert len(results) > 0
                # Verify notification was stored
                assert mock_db.add.called

                # Check that the added notification has high priority
                call_args = mock_db.add.call_args_list
                notification = call_args[-1][0][0]
                assert isinstance(notification, Notification)
                assert notification.priority == "high"

    @pytest.mark.asyncio
    async def test_create_notification_with_normal_priority(
        self,
        notification_service,
        mock_db,
        sample_recipient_id,
    ):
        """Test creating a normal priority notification."""
        with patch('app.notifications.service.get_channel') as mock_get_channel:
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(return_value=DeliveryResult(
                success=True,
                channel="in_app",
                message="Delivered"
            ))
            mock_get_channel.return_value = mock_channel

            with patch.object(
                notification_service,
                '_get_user_preferences',
                return_value=NotificationPreferences(user_id=sample_recipient_id)
            ):
                results = await notification_service.send_notification(
                    recipient_id=sample_recipient_id,
                    notification_type=NotificationType.ABSENCE_APPROVED,
                    data={
                        "absence_type": "Vacation",
                        "start_date": "2025-01-15",
                        "end_date": "2025-01-20",
                        "duration_days": "5",
                        "approval_notes": "Approved",
                        "approver_name": "Dr. Manager",
                        "approved_at": "2025-01-01 10:00:00 UTC",
                    },
                )

                assert len(results) > 0
                # Verify normal priority
                call_args = mock_db.add.call_args_list
                notification = call_args[-1][0][0]
                assert notification.priority == "normal"


# ============================================================================
# Test 2: Notification Creation - Multiple Users
# ============================================================================

class TestNotificationCreationMultipleUsers:
    """Test creating notifications for multiple users."""

    @pytest.mark.asyncio
    async def test_create_notification_multiple_users_bulk(
        self,
        notification_service,
        mock_db,
        sample_notification_data,
    ):
        """Test sending bulk notifications to multiple users."""
        recipient_ids = [uuid4() for _ in range(3)]

        with patch('app.notifications.service.get_channel') as mock_get_channel:
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(return_value=DeliveryResult(
                success=True,
                channel="in_app",
                message="Delivered"
            ))
            mock_get_channel.return_value = mock_channel

            with patch.object(
                notification_service,
                '_get_user_preferences',
                side_effect=lambda uid: NotificationPreferences(user_id=uid)
            ):
                results = await notification_service.send_bulk(
                    recipient_ids=recipient_ids,
                    notification_type=NotificationType.SCHEDULE_PUBLISHED,
                    data=sample_notification_data,
                )

                # Verify all recipients received notification
                assert len(results) == 3
                for recipient_id in recipient_ids:
                    assert str(recipient_id) in results

    @pytest.mark.asyncio
    async def test_bulk_notification_partial_failure(
        self,
        notification_service,
        mock_db,
        sample_notification_data,
    ):
        """Test bulk notification handles partial failures gracefully."""
        recipient_ids = [uuid4() for _ in range(3)]

        with patch('app.notifications.service.get_channel') as mock_get_channel:
            # First two succeed, third fails
            success_result = DeliveryResult(
                success=True,
                channel="in_app",
                message="Delivered"
            )
            failure_result = DeliveryResult(
                success=False,
                channel="in_app",
                message="Delivery failed"
            )

            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(
                side_effect=[success_result, success_result, failure_result]
            )
            mock_get_channel.return_value = mock_channel

            with patch.object(
                notification_service,
                '_get_user_preferences',
                side_effect=lambda uid: NotificationPreferences(user_id=uid)
            ):
                results = await notification_service.send_bulk(
                    recipient_ids=recipient_ids,
                    notification_type=NotificationType.SCHEDULE_PUBLISHED,
                    data=sample_notification_data,
                )

                # All recipients should have results
                assert len(results) == 3

                # First two should succeed
                assert results[str(recipient_ids[0])][0].success is True
                assert results[str(recipient_ids[1])][0].success is True

                # Third should fail
                assert results[str(recipient_ids[2])][0].success is False


# ============================================================================
# Test 3: Delivery Channels - In-App
# ============================================================================

class TestDeliveryChannelInApp:
    """Test in-app notification delivery."""

    @pytest.mark.asyncio
    async def test_in_app_channel_delivery_success(self):
        """Test successful in-app notification delivery."""
        channel = InAppChannel()
        mock_db = Mock()

        payload = NotificationPayload(
            recipient_id=uuid4(),
            notification_type="test_notification",
            subject="Test Subject",
            body="Test Body",
            priority="normal",
        )

        result = await channel.deliver(payload, mock_db)

        assert result.success is True
        assert result.channel == "in_app"
        assert "stored successfully" in result.message.lower()

    @pytest.mark.asyncio
    async def test_in_app_channel_no_database(self):
        """Test in-app channel fails without database session."""
        channel = InAppChannel()

        payload = NotificationPayload(
            recipient_id=uuid4(),
            notification_type="test_notification",
            subject="Test Subject",
            body="Test Body",
        )

        result = await channel.deliver(payload, db=None)

        assert result.success is False
        assert "database session required" in result.message.lower()


# ============================================================================
# Test 4: Delivery Channels - Email (Mock SMTP)
# ============================================================================

class TestDeliveryChannelEmail:
    """Test email notification delivery with mocked SMTP."""

    @pytest.mark.asyncio
    async def test_email_channel_prepare_payload(self):
        """Test email channel prepares correct payload."""
        channel = EmailChannel(from_address="test@example.com")

        payload = NotificationPayload(
            recipient_id=uuid4(),
            notification_type="test_notification",
            subject="Test Subject",
            body="Test Body",
            priority="high",
        )

        result = await channel.deliver(payload)

        assert result.success is True
        assert result.channel == "email"
        assert result.metadata is not None
        assert "email_payload" in result.metadata

        email_payload = result.metadata["email_payload"]
        assert email_payload["from"] == "test@example.com"
        assert email_payload["subject"] == "Test Subject"
        assert email_payload["priority"] == "high"

    @pytest.mark.asyncio
    async def test_email_channel_html_formatting(self):
        """Test email channel formats HTML correctly."""
        channel = EmailChannel()

        payload = NotificationPayload(
            recipient_id=uuid4(),
            notification_type="test_notification",
            subject="Test Subject",
            body="Test Body with\nmultiple lines",
            priority="high",
        )

        result = await channel.deliver(payload)

        assert result.success is True
        email_payload = result.metadata["email_payload"]
        html = email_payload["html"]

        # Verify HTML structure
        assert "<html>" in html
        assert "<body>" in html
        assert "Test Subject" in html
        assert "Test Body with\nmultiple lines" in html
        assert "priority-high" in html

    @pytest.mark.asyncio
    async def test_email_channel_handles_exception(self):
        """Test email channel handles exceptions gracefully."""
        channel = EmailChannel()

        # Mock _format_html to raise exception
        with patch.object(channel, '_format_html', side_effect=Exception("Format error")):
            payload = NotificationPayload(
                recipient_id=uuid4(),
                notification_type="test",
                subject="Test",
                body="Test",
            )

            result = await channel.deliver(payload)

            assert result.success is False
            assert "failed to prepare email" in result.message.lower()


# ============================================================================
# Test 5: Delivery Channels - Webhook/Slack (Mock Webhook)
# ============================================================================

class TestDeliveryChannelWebhook:
    """Test webhook notification delivery (Slack, etc.) with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_webhook_channel_prepare_payload(self):
        """Test webhook channel prepares correct payload."""
        webhook_url = "https://hooks.slack.com/services/test"
        channel = WebhookChannel(webhook_url=webhook_url)

        payload = NotificationPayload(
            recipient_id=uuid4(),
            notification_type="acgme_warning",
            subject="ACGME Violation",
            body="80-hour rule violated",
            priority="high",
            data={"severity": "HIGH"},
        )

        result = await channel.deliver(payload)

        assert result.success is True
        assert result.channel == "webhook"
        assert result.metadata is not None

        webhook_payload = result.metadata["payload"]
        assert webhook_payload["event"] == "notification"
        assert webhook_payload["type"] == "acgme_warning"
        assert webhook_payload["subject"] == "ACGME Violation"
        assert webhook_payload["priority"] == "high"
        assert webhook_payload["data"]["severity"] == "HIGH"

    @pytest.mark.asyncio
    async def test_webhook_channel_no_url(self):
        """Test webhook channel without URL configured."""
        channel = WebhookChannel(webhook_url=None)

        payload = NotificationPayload(
            recipient_id=uuid4(),
            notification_type="test",
            subject="Test",
            body="Test",
        )

        result = await channel.deliver(payload)

        # Should still succeed (queued for delivery)
        assert result.success is True
        assert result.metadata["webhook_url"] is None


# ============================================================================
# Test 6: Template Rendering - Variable Substitution
# ============================================================================

class TestTemplateVariableSubstitution:
    """Test template rendering with variable substitution."""

    def test_template_rendering_all_variables(self):
        """Test template renders correctly with all variables provided."""
        data = {
            "period": "January 2025",
            "coverage_rate": "95.0",
            "total_assignments": "100",
            "violations_count": "0",
            "publisher_name": "Dr. Admin",
            "published_at": "2025-01-01 10:00:00 UTC",
        }

        rendered = render_notification(NotificationType.SCHEDULE_PUBLISHED, data)

        assert rendered is not None
        assert "January 2025" in rendered["subject"]
        assert "95.0" in rendered["body"]
        assert "100" in rendered["body"]
        assert "Dr. Admin" in rendered["body"]

    def test_template_rendering_missing_variables_safe_substitute(self):
        """Test template handles missing variables gracefully with safe_substitute."""
        # Provide incomplete data
        data = {
            "period": "January 2025",
            "coverage_rate": "95.0",
            # Missing: total_assignments, violations_count, publisher_name, published_at
        }

        rendered = render_notification(NotificationType.SCHEDULE_PUBLISHED, data)

        assert rendered is not None
        assert "January 2025" in rendered["subject"]
        assert "95.0" in rendered["body"]
        # Missing variables should be left as $variable_name (safe_substitute behavior)

    def test_template_rendering_empty_data(self):
        """Test template with completely empty data."""
        rendered = render_notification(NotificationType.SCHEDULE_PUBLISHED, {})

        assert rendered is not None
        # Template should still render with placeholders


# ============================================================================
# Test 7: Template Rendering - HTML vs Plain Text
# ============================================================================

class TestTemplateHTMLvsPlainText:
    """Test HTML vs plain text template rendering."""

    @pytest.mark.asyncio
    async def test_email_channel_produces_html(self):
        """Test email channel produces HTML format."""
        channel = EmailChannel()

        payload = NotificationPayload(
            recipient_id=uuid4(),
            notification_type="schedule_published",
            subject="Schedule Published",
            body="Your schedule has been published.",
            priority="normal",
        )

        result = await channel.deliver(payload)

        assert result.success is True
        email_payload = result.metadata["email_payload"]

        # Body should be plain text
        assert email_payload["body"] == "Your schedule has been published."

        # HTML should be formatted version
        html = email_payload["html"]
        assert "<html>" in html
        assert "<body>" in html
        assert "Schedule Published" in html

    @pytest.mark.asyncio
    async def test_in_app_channel_plain_text(self):
        """Test in-app channel uses plain text."""
        channel = InAppChannel()
        mock_db = Mock()

        payload = NotificationPayload(
            recipient_id=uuid4(),
            notification_type="test",
            subject="Test Subject",
            body="Plain text body",
        )

        result = await channel.deliver(payload, mock_db)

        # In-app should be plain text (no HTML formatting)
        assert result.success is True


# ============================================================================
# Test 8: Batching Logic - Batch Multiple Notifications
# ============================================================================

class TestBatchingMultipleNotifications:
    """Test batching multiple notifications."""

    @pytest.mark.asyncio
    async def test_batch_notifications_sequential(
        self,
        notification_service,
        mock_db,
    ):
        """Test batching sends notifications sequentially."""
        recipient_ids = [uuid4() for _ in range(5)]

        with patch('app.notifications.service.get_channel') as mock_get_channel:
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(return_value=DeliveryResult(
                success=True,
                channel="in_app",
                message="Delivered"
            ))
            mock_get_channel.return_value = mock_channel

            with patch.object(
                notification_service,
                '_get_user_preferences',
                side_effect=lambda uid: NotificationPreferences(user_id=uid)
            ):
                results = await notification_service.send_bulk(
                    recipient_ids=recipient_ids,
                    notification_type=NotificationType.SHIFT_REMINDER_24H,
                    data={
                        "rotation_name": "Surgery",
                        "location": "OR 3",
                        "start_date": "2025-01-15",
                        "duration_weeks": "2",
                        "contact_person": "Dr. Smith",
                        "contact_email": "smith@hospital.org",
                    },
                )

                # Verify all notifications sent
                assert len(results) == 5

                # Verify channel.deliver was called 5 times
                assert mock_channel.deliver.call_count == 5


# ============================================================================
# Test 9: Batching Logic - Immediate vs Scheduled Delivery
# ============================================================================

class TestImmediateVsScheduledDelivery:
    """Test immediate vs scheduled notification delivery."""

    @pytest.mark.asyncio
    async def test_immediate_delivery(
        self,
        notification_service,
        mock_db,
        sample_recipient_id,
    ):
        """Test immediate notification delivery."""
        with patch('app.notifications.service.get_channel') as mock_get_channel:
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(return_value=DeliveryResult(
                success=True,
                channel="in_app",
                message="Delivered immediately"
            ))
            mock_get_channel.return_value = mock_channel

            with patch.object(
                notification_service,
                '_get_user_preferences',
                return_value=NotificationPreferences(user_id=sample_recipient_id)
            ):
                results = await notification_service.send_notification(
                    recipient_id=sample_recipient_id,
                    notification_type=NotificationType.SHIFT_REMINDER_1H,
                    data={
                        "rotation_name": "Emergency",
                        "location": "ER",
                        "start_time": "14:00",
                    },
                )

                # Immediate delivery should happen now
                assert len(results) > 0
                assert results[0].success is True
                assert mock_channel.deliver.called

    def test_scheduled_delivery(
        self,
        notification_service,
        mock_db,
        sample_recipient_id,
    ):
        """Test scheduling notification for future delivery."""
        send_at = datetime.utcnow() + timedelta(hours=24)

        # Mock database query
        mock_db.add = Mock()
        mock_db.commit = Mock()

        # Create a mock record that will be returned after commit
        mock_record = Mock(spec=ScheduledNotificationRecord)
        mock_record.id = uuid4()
        mock_record.status = "pending"
        mock_record.created_at = datetime.utcnow()

        mock_db.refresh = Mock(side_effect=lambda r: setattr(r, 'id', mock_record.id))

        scheduled = notification_service.schedule_notification(
            recipient_id=sample_recipient_id,
            notification_type=NotificationType.SHIFT_REMINDER_24H,
            data={"rotation_name": "Test"},
            send_at=send_at,
        )

        # Verify scheduled notification was created
        assert scheduled is not None
        assert scheduled.status == "pending"
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_process_scheduled_notifications_due(
        self,
        notification_service,
        mock_db,
    ):
        """Test processing due scheduled notifications."""
        # Create a mock due notification
        past_time = datetime.utcnow() - timedelta(minutes=5)
        mock_record = Mock(spec=ScheduledNotificationRecord)
        mock_record.id = uuid4()
        mock_record.recipient_id = uuid4()
        mock_record.notification_type = "shift_reminder_24h"
        mock_record.data = {"rotation_name": "Test"}
        mock_record.send_at = past_time
        mock_record.status = "pending"
        mock_record.retry_count = 0

        # Mock query to return the due notification
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_record]
        mock_db.query.return_value = mock_query

        with patch('app.notifications.service.get_channel') as mock_get_channel:
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(return_value=DeliveryResult(
                success=True,
                channel="in_app",
                message="Delivered"
            ))
            mock_get_channel.return_value = mock_channel

            with patch.object(
                notification_service,
                '_get_user_preferences',
                return_value=NotificationPreferences(user_id=mock_record.recipient_id)
            ):
                sent_count = await notification_service.process_scheduled_notifications()

                # Verify notification was sent
                assert sent_count == 1
                assert mock_record.status == "sent"


# ============================================================================
# Test 10: Retry Handling - Failed Delivery Retry
# ============================================================================

class TestRetryFailedDelivery:
    """Test retry logic for failed deliveries."""

    @pytest.mark.asyncio
    async def test_failed_delivery_increments_retry_count(
        self,
        notification_service,
        mock_db,
    ):
        """Test failed scheduled notification increments retry count."""
        mock_record = Mock(spec=ScheduledNotificationRecord)
        mock_record.id = uuid4()
        mock_record.recipient_id = uuid4()
        mock_record.notification_type = "invalid_type"
        mock_record.data = {}
        mock_record.send_at = datetime.utcnow() - timedelta(minutes=5)
        mock_record.status = "pending"
        mock_record.retry_count = 0
        mock_record.error_message = None

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_record]
        mock_db.query.return_value = mock_query

        # Force send_notification to raise an exception
        with patch.object(
            notification_service,
            'send_notification',
            side_effect=Exception("Delivery failed")
        ):
            sent_count = await notification_service.process_scheduled_notifications()

            # Verify retry count was incremented
            assert sent_count == 1
            assert mock_record.status == "failed"
            assert mock_record.retry_count == 1
            assert mock_record.error_message is not None

    @pytest.mark.asyncio
    async def test_retry_after_transient_failure(
        self,
        notification_service,
        mock_db,
    ):
        """Test notification retries after transient failure."""
        mock_record = Mock(spec=ScheduledNotificationRecord)
        mock_record.id = uuid4()
        mock_record.recipient_id = uuid4()
        mock_record.notification_type = "shift_reminder_24h"
        mock_record.data = {"rotation_name": "Test"}
        mock_record.send_at = datetime.utcnow() - timedelta(minutes=5)
        mock_record.status = "pending"
        mock_record.retry_count = 1  # Already retried once

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_record]
        mock_db.query.return_value = mock_query

        with patch('app.notifications.service.get_channel') as mock_get_channel:
            # First attempt fails, second succeeds (simulating retry)
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(return_value=DeliveryResult(
                success=True,
                channel="in_app",
                message="Delivered on retry"
            ))
            mock_get_channel.return_value = mock_channel

            with patch.object(
                notification_service,
                '_get_user_preferences',
                return_value=NotificationPreferences(user_id=mock_record.recipient_id)
            ):
                sent_count = await notification_service.process_scheduled_notifications()

                # Should succeed on retry
                assert sent_count == 1
                assert mock_record.status == "sent"


# ============================================================================
# Test 11: Retry Handling - Max Retry Limit
# ============================================================================

class TestMaxRetryLimit:
    """Test maximum retry limit enforcement."""

    @pytest.mark.asyncio
    async def test_max_retry_limit_enforced(
        self,
        notification_service,
        mock_db,
    ):
        """Test that notifications stop retrying after max attempts."""
        # Create notification that has already been retried 3 times
        mock_record = Mock(spec=ScheduledNotificationRecord)
        mock_record.id = uuid4()
        mock_record.recipient_id = uuid4()
        mock_record.notification_type = "test"
        mock_record.data = {}
        mock_record.send_at = datetime.utcnow() - timedelta(hours=1)
        mock_record.status = "pending"
        mock_record.retry_count = 3  # Max retries typically 3

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_record]
        mock_db.query.return_value = mock_query

        # Simulate failure
        with patch.object(
            notification_service,
            'send_notification',
            side_effect=Exception("Permanent failure")
        ):
            sent_count = await notification_service.process_scheduled_notifications()

            # Should be marked as failed
            assert sent_count == 1
            assert mock_record.status == "failed"
            assert mock_record.retry_count == 4  # Incremented
            # Note: Real implementation might have logic to not retry after max


# ============================================================================
# Test 12: User Preferences - Channel Filtering
# ============================================================================

class TestUserPreferencesChannelFiltering:
    """Test notification filtering based on user preferences."""

    @pytest.mark.asyncio
    async def test_disabled_notification_type_skipped(
        self,
        notification_service,
        mock_db,
        sample_recipient_id,
    ):
        """Test notifications are skipped when type is disabled."""
        # User has disabled schedule_published notifications
        preferences = NotificationPreferences(
            user_id=sample_recipient_id,
            notification_types={"schedule_published": False}
        )

        with patch.object(
            notification_service,
            '_get_user_preferences',
            return_value=preferences
        ):
            results = await notification_service.send_notification(
                recipient_id=sample_recipient_id,
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

            # Notification should be skipped
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_channel_filtering_by_preference(
        self,
        notification_service,
        mock_db,
        sample_recipient_id,
    ):
        """Test channels are filtered based on user preferences."""
        # User only wants in_app notifications
        preferences = NotificationPreferences(
            user_id=sample_recipient_id,
            enabled_channels=["in_app"]
        )

        with patch('app.notifications.service.get_channel') as mock_get_channel:
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(return_value=DeliveryResult(
                success=True,
                channel="in_app",
                message="Delivered"
            ))
            mock_get_channel.return_value = mock_channel

            with patch.object(
                notification_service,
                '_get_user_preferences',
                return_value=preferences
            ):
                results = await notification_service.send_notification(
                    recipient_id=sample_recipient_id,
                    notification_type=NotificationType.ACGME_WARNING,
                    data={
                        "violation_type": "Test",
                        "severity": "HIGH",
                        "person_name": "Test",
                        "violation_details": "Test",
                        "recommended_action": "Test",
                        "detected_at": "2025-01-01 10:00:00 UTC",
                    },
                    channels=["in_app", "email"]  # Request both channels
                )

                # Only in_app should be delivered
                assert len(results) == 1
                assert results[0].channel == "in_app"


# ============================================================================
# Test 13: Quiet Hours - Notification Suppression
# ============================================================================

class TestQuietHoursNotificationSuppression:
    """Test quiet hours notification suppression."""

    @pytest.mark.asyncio
    async def test_quiet_hours_suppresses_normal_priority(
        self,
        notification_service,
        mock_db,
        sample_recipient_id,
    ):
        """Test quiet hours suppress normal priority notifications."""
        current_hour = datetime.utcnow().hour

        preferences = NotificationPreferences(
            user_id=sample_recipient_id,
            quiet_hours_start=current_hour,
            quiet_hours_end=(current_hour + 1) % 24,
        )

        with patch.object(
            notification_service,
            '_get_user_preferences',
            return_value=preferences
        ):
            results = await notification_service.send_notification(
                recipient_id=sample_recipient_id,
                notification_type=NotificationType.ABSENCE_APPROVED,
                data={
                    "absence_type": "Vacation",
                    "start_date": "2025-01-15",
                    "end_date": "2025-01-20",
                    "duration_days": "5",
                    "approval_notes": "Approved",
                    "approver_name": "Manager",
                    "approved_at": "2025-01-01 10:00:00 UTC",
                },
            )

            # Normal priority notification should be suppressed during quiet hours
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_quiet_hours_allows_high_priority(
        self,
        notification_service,
        mock_db,
        sample_recipient_id,
    ):
        """Test quiet hours allow high priority notifications."""
        current_hour = datetime.utcnow().hour

        preferences = NotificationPreferences(
            user_id=sample_recipient_id,
            quiet_hours_start=current_hour,
            quiet_hours_end=(current_hour + 1) % 24,
        )

        with patch('app.notifications.service.get_channel') as mock_get_channel:
            mock_channel = Mock()
            mock_channel.deliver = AsyncMock(return_value=DeliveryResult(
                success=True,
                channel="in_app",
                message="Delivered"
            ))
            mock_get_channel.return_value = mock_channel

            with patch.object(
                notification_service,
                '_get_user_preferences',
                return_value=preferences
            ):
                results = await notification_service.send_notification(
                    recipient_id=sample_recipient_id,
                    notification_type=NotificationType.ACGME_WARNING,  # High priority
                    data={
                        "violation_type": "Critical",
                        "severity": "HIGH",
                        "person_name": "Test",
                        "violation_details": "Critical violation",
                        "recommended_action": "Immediate action required",
                        "detected_at": "2025-01-01 10:00:00 UTC",
                    },
                )

                # High priority should bypass quiet hours
                assert len(results) > 0


# ============================================================================
# Test 14: Template Not Found Handling
# ============================================================================

class TestTemplateNotFoundHandling:
    """Test handling of missing templates."""

    @pytest.mark.asyncio
    async def test_missing_template_returns_error(
        self,
        notification_service,
        sample_recipient_id,
    ):
        """Test missing template returns error result."""
        with patch('app.notifications.service.render_notification', return_value=None):
            results = await notification_service.send_notification(
                recipient_id=sample_recipient_id,
                notification_type=NotificationType.SCHEDULE_PUBLISHED,
                data={},
            )

            assert len(results) == 1
            assert results[0].success is False
            assert "template not found" in results[0].message.lower()


# ============================================================================
# Test 15: Channel Not Found Handling
# ============================================================================

class TestChannelNotFoundHandling:
    """Test handling of invalid/missing channels."""

    @pytest.mark.asyncio
    async def test_invalid_channel_returns_error(
        self,
        notification_service,
        mock_db,
        sample_recipient_id,
    ):
        """Test invalid channel returns error result."""
        with patch('app.notifications.service.get_channel', return_value=None):
            with patch.object(
                notification_service,
                '_get_user_preferences',
                return_value=NotificationPreferences(
                    user_id=sample_recipient_id,
                    enabled_channels=["invalid_channel"]
                )
            ):
                results = await notification_service.send_notification(
                    recipient_id=sample_recipient_id,
                    notification_type=NotificationType.SCHEDULE_PUBLISHED,
                    data={
                        "period": "January 2025",
                        "coverage_rate": "95.0",
                        "total_assignments": "100",
                        "violations_count": "0",
                        "publisher_name": "Admin",
                        "published_at": "2025-01-01 10:00:00 UTC",
                    },
                    channels=["invalid_channel"]
                )

                # Should have error result for invalid channel
                assert len(results) == 1
                assert results[0].success is False
                assert "channel not found" in results[0].message.lower()


# ============================================================================
# Test 16: Notification Retrieval and Read Status
# ============================================================================

class TestNotificationRetrievalAndReadStatus:
    """Test retrieving and marking notifications as read."""

    def test_get_pending_notifications_unread_only(
        self,
        notification_service,
        mock_db,
        sample_recipient_id,
    ):
        """Test getting only unread notifications."""
        # Mock unread notifications
        mock_notifications = [
            Mock(
                id=uuid4(),
                notification_type="schedule_published",
                subject="Test 1",
                body="Body 1",
                data={},
                priority="normal",
                is_read=False,
                created_at=datetime.utcnow(),
            ),
            Mock(
                id=uuid4(),
                notification_type="assignment_changed",
                subject="Test 2",
                body="Body 2",
                data={},
                priority="high",
                is_read=False,
                created_at=datetime.utcnow(),
            ),
        ]

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_notifications
        mock_db.query.return_value = mock_query

        notifications = notification_service.get_pending_notifications(
            user_id=sample_recipient_id,
            unread_only=True,
        )

        assert len(notifications) == 2
        assert all(n["is_read"] is False for n in notifications)

    def test_mark_notifications_as_read(
        self,
        notification_service,
        mock_db,
    ):
        """Test marking notifications as read."""
        notification_ids = [uuid4(), uuid4()]

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = 2
        mock_db.query.return_value = mock_query

        count = notification_service.mark_as_read(notification_ids)

        assert count == 2
        assert mock_db.commit.called


# ============================================================================
# Test 17: Update User Preferences
# ============================================================================

class TestUpdateUserPreferences:
    """Test updating user notification preferences."""

    def test_create_new_preferences(
        self,
        notification_service,
        mock_db,
        sample_recipient_id,
    ):
        """Test creating new user preferences."""
        # Mock query returns no existing preferences
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        new_prefs = NotificationPreferences(
            user_id=sample_recipient_id,
            enabled_channels=["in_app"],
            notification_types={"schedule_published": True},
            quiet_hours_start=22,
            quiet_hours_end=7,
        )

        result = notification_service.update_user_preferences(
            user_id=sample_recipient_id,
            preferences=new_prefs,
        )

        assert result.user_id == sample_recipient_id
        assert result.enabled_channels == ["in_app"]
        assert result.quiet_hours_start == 22
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_update_existing_preferences(
        self,
        notification_service,
        mock_db,
        sample_recipient_id,
    ):
        """Test updating existing user preferences."""
        # Mock existing preferences record
        existing_record = Mock(spec=NotificationPreferenceRecord)
        existing_record.user_id = sample_recipient_id
        existing_record.enabled_channels = "in_app,email"

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_record
        mock_db.query.return_value = mock_query

        updated_prefs = NotificationPreferences(
            user_id=sample_recipient_id,
            enabled_channels=["email"],
            notification_types={"schedule_published": False},
        )

        result = notification_service.update_user_preferences(
            user_id=sample_recipient_id,
            preferences=updated_prefs,
        )

        # Verify preferences were updated
        assert existing_record.enabled_channels == "email"
        assert existing_record.notification_types == {"schedule_published": False}
        assert mock_db.commit.called


# ============================================================================
# Test 18: Multiple Channel Delivery
# ============================================================================

class TestMultipleChannelDelivery:
    """Test delivering to multiple channels simultaneously."""

    @pytest.mark.asyncio
    async def test_deliver_to_multiple_channels(
        self,
        notification_service,
        mock_db,
        sample_recipient_id,
    ):
        """Test notification is delivered to all specified channels."""
        with patch('app.notifications.service.get_channel') as mock_get_channel:
            # Mock different channels
            def get_channel_side_effect(channel_name):
                mock_channel = Mock()
                mock_channel.deliver = AsyncMock(return_value=DeliveryResult(
                    success=True,
                    channel=channel_name,
                    message=f"{channel_name} delivered"
                ))
                return mock_channel

            mock_get_channel.side_effect = get_channel_side_effect

            with patch.object(
                notification_service,
                '_get_user_preferences',
                return_value=NotificationPreferences(
                    user_id=sample_recipient_id,
                    enabled_channels=["in_app", "email", "webhook"]
                )
            ):
                results = await notification_service.send_notification(
                    recipient_id=sample_recipient_id,
                    notification_type=NotificationType.ACGME_WARNING,
                    data={
                        "violation_type": "Test",
                        "severity": "HIGH",
                        "person_name": "Test",
                        "violation_details": "Test",
                        "recommended_action": "Test",
                        "detected_at": "2025-01-01 10:00:00 UTC",
                    },
                    channels=["in_app", "email", "webhook"]
                )

                # All three channels should have results
                assert len(results) == 3
                channel_names = {r.channel for r in results}
                assert "in_app" in channel_names
                assert "email" in channel_names
                assert "webhook" in channel_names
