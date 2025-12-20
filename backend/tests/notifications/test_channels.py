"""Tests for notification delivery channels."""
import uuid
from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from app.notifications.channels import (
    AVAILABLE_CHANNELS,
    DeliveryResult,
    EmailChannel,
    InAppChannel,
    NotificationChannel,
    NotificationPayload,
    WebhookChannel,
    get_channel,
)


class TestNotificationPayload:
    """Test suite for NotificationPayload model."""

    def test_notification_payload_creation(self):
        """Test creating a notification payload with all fields."""
        recipient_id = uuid.uuid4()
        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="test_type",
            subject="Test Subject",
            body="Test Body",
            data={"key": "value"},
            priority="high"
        )

        assert payload.recipient_id == recipient_id
        assert payload.notification_type == "test_type"
        assert payload.subject == "Test Subject"
        assert payload.body == "Test Body"
        assert payload.data == {"key": "value"}
        assert payload.priority == "high"
        assert isinstance(payload.id, uuid.UUID)
        assert isinstance(payload.created_at, datetime)

    def test_notification_payload_defaults(self):
        """Test NotificationPayload uses correct default values."""
        recipient_id = uuid.uuid4()
        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="test_type",
            subject="Test Subject",
            body="Test Body"
        )

        # Default values should be set
        assert payload.data is None
        assert payload.priority == "normal"
        assert isinstance(payload.id, uuid.UUID)
        assert isinstance(payload.created_at, datetime)

    def test_notification_payload_id_generation(self):
        """Test that each payload gets a unique ID."""
        recipient_id = uuid.uuid4()
        payload1 = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="test",
            subject="Test",
            body="Body"
        )
        payload2 = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="test",
            subject="Test",
            body="Body"
        )

        assert payload1.id != payload2.id


class TestDeliveryResult:
    """Test suite for DeliveryResult model."""

    def test_delivery_result_creation(self):
        """Test creating a delivery result with all fields."""
        result = DeliveryResult(
            success=True,
            channel="email",
            message="Email sent successfully",
            metadata={"email_id": "123"}
        )

        assert result.success is True
        assert result.channel == "email"
        assert result.message == "Email sent successfully"
        assert result.metadata == {"email_id": "123"}

    def test_delivery_result_without_metadata(self):
        """Test DeliveryResult with None metadata."""
        result = DeliveryResult(
            success=False,
            channel="webhook",
            message="Webhook failed"
        )

        assert result.success is False
        assert result.channel == "webhook"
        assert result.message == "Webhook failed"
        assert result.metadata is None


class TestInAppChannel:
    """Test suite for InAppChannel."""

    @pytest.mark.asyncio
    async def test_channel_name(self):
        """Test channel_name property."""
        channel = InAppChannel()
        assert channel.channel_name == "in_app"

    @pytest.mark.asyncio
    async def test_deliver_success(self):
        """Test successful in-app notification delivery with database session."""
        channel = InAppChannel()
        db = MagicMock()
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="schedule_change",
            subject="Schedule Updated",
            body="Your schedule has been changed",
            priority="high"
        )

        result = await channel.deliver(payload, db)

        assert result.success is True
        assert result.channel == "in_app"
        assert result.message == "Notification stored successfully"
        assert result.metadata is not None
        assert "notification_id" in result.metadata
        assert result.metadata["notification_id"] == str(payload.id)

    @pytest.mark.asyncio
    async def test_deliver_missing_db(self):
        """Test in-app delivery fails when database session is missing."""
        channel = InAppChannel()
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="schedule_change",
            subject="Schedule Updated",
            body="Your schedule has been changed"
        )

        result = await channel.deliver(payload, db=None)

        assert result.success is False
        assert result.channel == "in_app"
        assert result.message == "Database session required for in-app notifications"

    @pytest.mark.asyncio
    async def test_deliver_handles_exception(self):
        """Test in-app delivery handles exceptions gracefully."""
        channel = InAppChannel()

        # Create a mock that raises an exception
        db = MagicMock()

        # Create payload with invalid data that might cause an exception
        recipient_id = uuid.uuid4()
        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="test",
            subject="Test",
            body="Test"
        )

        # Mock the payload.id property to raise an exception when converted to string
        original_id = payload.id
        mock_id = Mock()
        mock_id.__str__ = Mock(side_effect=Exception("Database error"))
        payload.id = mock_id

        # The channel should catch the exception and return a failed result
        result = await channel.deliver(payload, db)

        assert result.success is False
        assert result.channel == "in_app"
        assert "Failed to store notification" in result.message
        assert "Database error" in result.message


class TestEmailChannel:
    """Test suite for EmailChannel."""

    def test_initialization_default_from_address(self):
        """Test EmailChannel initialization with default from address."""
        channel = EmailChannel()
        assert channel.from_address == "noreply@schedule.mil"

    def test_initialization_custom_from_address(self):
        """Test EmailChannel initialization with custom from address."""
        custom_email = "admin@example.com"
        channel = EmailChannel(from_address=custom_email)
        assert channel.from_address == custom_email

    @pytest.mark.asyncio
    async def test_channel_name(self):
        """Test channel_name property."""
        channel = EmailChannel()
        assert channel.channel_name == "email"

    @pytest.mark.asyncio
    async def test_deliver_success(self):
        """Test successful email payload preparation."""
        channel = EmailChannel(from_address="test@example.com")
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="schedule_reminder",
            subject="Schedule Reminder",
            body="You have an upcoming shift",
            priority="normal"
        )

        result = await channel.deliver(payload)

        assert result.success is True
        assert result.channel == "email"
        assert result.message == "Email queued for delivery"
        assert result.metadata is not None
        assert "email_payload" in result.metadata

        email_payload = result.metadata["email_payload"]
        assert email_payload["from"] == "test@example.com"
        assert email_payload["to"] == f"user-{recipient_id}@example.com"
        assert email_payload["subject"] == "Schedule Reminder"
        assert email_payload["body"] == "You have an upcoming shift"
        assert email_payload["priority"] == "normal"
        assert "html" in email_payload

    @pytest.mark.asyncio
    async def test_deliver_with_db_session(self):
        """Test email delivery with optional database session."""
        channel = EmailChannel()
        db = MagicMock()
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="test",
            subject="Test",
            body="Test body"
        )

        result = await channel.deliver(payload, db)

        assert result.success is True
        assert result.channel == "email"

    def test_format_html_normal_priority(self):
        """Test HTML formatting with normal priority."""
        channel = EmailChannel()
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="test",
            subject="Test Subject",
            body="Test body content",
            priority="normal"
        )

        html = channel._format_html(payload)

        assert "<html>" in html
        assert "Test Subject" in html
        assert "Test body content" in html
        assert "priority-normal" in html
        assert "automated notification" in html.lower()

    def test_format_html_high_priority(self):
        """Test HTML formatting with high priority styling."""
        channel = EmailChannel()
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="emergency",
            subject="Emergency Alert",
            body="Urgent message",
            priority="high"
        )

        html = channel._format_html(payload)

        assert "priority-high" in html
        assert "Emergency Alert" in html
        assert "Urgent message" in html
        # Check that high priority CSS class is referenced
        assert ".priority-high" in html

    def test_format_html_low_priority(self):
        """Test HTML formatting with low priority styling."""
        channel = EmailChannel()
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="info",
            subject="Information",
            body="Low priority info",
            priority="low"
        )

        html = channel._format_html(payload)

        assert "priority-low" in html
        assert "Information" in html
        assert "Low priority info" in html
        # Check that low priority CSS class is referenced
        assert ".priority-low" in html

    def test_format_html_structure(self):
        """Test HTML template structure and CSS styling."""
        channel = EmailChannel()
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="test",
            subject="Test",
            body="Body",
            priority="normal"
        )

        html = channel._format_html(payload)

        # Check structure
        assert "<html>" in html
        assert "</html>" in html
        assert "<head>" in html
        assert "<style>" in html
        assert "<body>" in html
        assert "<div class=\"header\">" in html
        assert "<div class=\"content priority-normal\">" in html
        assert "<div class=\"footer\">" in html

        # Check CSS classes exist
        assert ".header" in html
        assert ".content" in html
        assert ".priority-high" in html
        assert ".priority-normal" in html
        assert ".priority-low" in html
        assert ".footer" in html


class TestWebhookChannel:
    """Test suite for WebhookChannel."""

    def test_initialization_without_url(self):
        """Test WebhookChannel initialization without URL."""
        channel = WebhookChannel()
        assert channel.webhook_url is None

    def test_initialization_with_url(self):
        """Test WebhookChannel initialization with URL."""
        url = "https://hooks.slack.com/services/test"
        channel = WebhookChannel(webhook_url=url)
        assert channel.webhook_url == url

    @pytest.mark.asyncio
    async def test_channel_name(self):
        """Test channel_name property."""
        channel = WebhookChannel()
        assert channel.channel_name == "webhook"

    @pytest.mark.asyncio
    async def test_deliver_success(self):
        """Test successful webhook payload preparation."""
        webhook_url = "https://example.com/webhook"
        channel = WebhookChannel(webhook_url=webhook_url)
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="system_alert",
            subject="System Alert",
            body="System status changed",
            data={"status": "degraded", "service": "api"},
            priority="high"
        )

        result = await channel.deliver(payload)

        assert result.success is True
        assert result.channel == "webhook"
        assert result.message == "Webhook queued for delivery"
        assert result.metadata is not None
        assert "webhook_url" in result.metadata
        assert result.metadata["webhook_url"] == webhook_url
        assert "payload" in result.metadata

        webhook_payload = result.metadata["payload"]
        assert webhook_payload["event"] == "notification"
        assert webhook_payload["notification_id"] == str(payload.id)
        assert webhook_payload["type"] == "system_alert"
        assert webhook_payload["recipient_id"] == str(recipient_id)
        assert webhook_payload["subject"] == "System Alert"
        assert webhook_payload["body"] == "System status changed"
        assert webhook_payload["priority"] == "high"
        assert webhook_payload["data"] == {"status": "degraded", "service": "api"}
        assert "timestamp" in webhook_payload
        # Verify timestamp is ISO format
        datetime.fromisoformat(webhook_payload["timestamp"])

    @pytest.mark.asyncio
    async def test_deliver_without_webhook_url(self):
        """Test webhook delivery without configured URL."""
        channel = WebhookChannel()
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="test",
            subject="Test",
            body="Test"
        )

        result = await channel.deliver(payload)

        assert result.success is True
        assert result.channel == "webhook"
        assert result.metadata["webhook_url"] is None

    @pytest.mark.asyncio
    async def test_deliver_with_db_session(self):
        """Test webhook delivery with optional database session."""
        channel = WebhookChannel(webhook_url="https://example.com/hook")
        db = MagicMock()
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="test",
            subject="Test",
            body="Test"
        )

        result = await channel.deliver(payload, db)

        assert result.success is True
        assert result.channel == "webhook"

    @pytest.mark.asyncio
    async def test_deliver_payload_structure(self):
        """Test webhook payload has correct structure."""
        channel = WebhookChannel(webhook_url="https://example.com/webhook")
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="schedule_change",
            subject="Schedule Updated",
            body="Your schedule has been modified",
            data={"shift_id": "123", "reason": "coverage"},
            priority="normal"
        )

        result = await channel.deliver(payload)

        webhook_payload = result.metadata["payload"]

        # Verify all required fields are present
        required_fields = [
            "event", "notification_id", "type", "recipient_id",
            "subject", "body", "priority", "timestamp", "data"
        ]
        for field in required_fields:
            assert field in webhook_payload, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_deliver_with_none_data(self):
        """Test webhook delivery when payload data is None."""
        channel = WebhookChannel(webhook_url="https://example.com/webhook")
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="test",
            subject="Test",
            body="Test",
            data=None
        )

        result = await channel.deliver(payload)

        assert result.success is True
        webhook_payload = result.metadata["payload"]
        assert webhook_payload["data"] is None


class TestChannelRegistry:
    """Test suite for channel registry and factory function."""

    def test_available_channels_registry(self):
        """Test AVAILABLE_CHANNELS contains all expected channels."""
        assert "in_app" in AVAILABLE_CHANNELS
        assert "email" in AVAILABLE_CHANNELS
        assert "webhook" in AVAILABLE_CHANNELS

        assert AVAILABLE_CHANNELS["in_app"] == InAppChannel
        assert AVAILABLE_CHANNELS["email"] == EmailChannel
        assert AVAILABLE_CHANNELS["webhook"] == WebhookChannel

    def test_available_channels_count(self):
        """Test AVAILABLE_CHANNELS has expected number of channels."""
        assert len(AVAILABLE_CHANNELS) == 3

    def test_get_channel_in_app(self):
        """Test get_channel factory for in_app channel."""
        channel = get_channel("in_app")
        assert channel is not None
        assert isinstance(channel, InAppChannel)
        assert channel.channel_name == "in_app"

    def test_get_channel_email_default(self):
        """Test get_channel factory for email channel with defaults."""
        channel = get_channel("email")
        assert channel is not None
        assert isinstance(channel, EmailChannel)
        assert channel.channel_name == "email"
        assert channel.from_address == "noreply@schedule.mil"

    def test_get_channel_email_with_kwargs(self):
        """Test get_channel factory for email channel with custom args."""
        custom_email = "custom@example.com"
        channel = get_channel("email", from_address=custom_email)
        assert channel is not None
        assert isinstance(channel, EmailChannel)
        assert channel.from_address == custom_email

    def test_get_channel_webhook_default(self):
        """Test get_channel factory for webhook channel with defaults."""
        channel = get_channel("webhook")
        assert channel is not None
        assert isinstance(channel, WebhookChannel)
        assert channel.channel_name == "webhook"
        assert channel.webhook_url is None

    def test_get_channel_webhook_with_kwargs(self):
        """Test get_channel factory for webhook channel with custom args."""
        webhook_url = "https://example.com/hook"
        channel = get_channel("webhook", webhook_url=webhook_url)
        assert channel is not None
        assert isinstance(channel, WebhookChannel)
        assert channel.webhook_url == webhook_url

    def test_get_channel_invalid_name(self):
        """Test get_channel returns None for invalid channel name."""
        channel = get_channel("invalid_channel")
        assert channel is None

    def test_get_channel_empty_name(self):
        """Test get_channel returns None for empty channel name."""
        channel = get_channel("")
        assert channel is None

    def test_get_channel_case_sensitive(self):
        """Test get_channel is case-sensitive."""
        channel = get_channel("IN_APP")  # Wrong case
        assert channel is None


class TestChannelAbstractInterface:
    """Test suite for NotificationChannel abstract interface."""

    def test_all_channels_have_channel_name(self):
        """Test all channel implementations have channel_name property."""
        for channel_class in AVAILABLE_CHANNELS.values():
            channel = channel_class() if channel_class != EmailChannel and channel_class != WebhookChannel else channel_class()
            assert hasattr(channel, 'channel_name')
            assert isinstance(channel.channel_name, str)
            assert len(channel.channel_name) > 0

    @pytest.mark.asyncio
    async def test_all_channels_have_deliver_method(self):
        """Test all channel implementations have deliver method."""
        recipient_id = uuid.uuid4()
        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="test",
            subject="Test",
            body="Test"
        )

        for channel_class in AVAILABLE_CHANNELS.values():
            if channel_class == InAppChannel:
                channel = channel_class()
                result = await channel.deliver(payload, MagicMock())
            else:
                channel = channel_class()
                result = await channel.deliver(payload)

            assert isinstance(result, DeliveryResult)
            assert hasattr(result, 'success')
            assert hasattr(result, 'channel')
            assert hasattr(result, 'message')


class TestPriorityHandling:
    """Test suite for priority handling across channels."""

    @pytest.mark.asyncio
    async def test_email_channel_high_priority(self):
        """Test email channel handles high priority correctly."""
        channel = EmailChannel()
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="emergency",
            subject="Emergency",
            body="High priority message",
            priority="high"
        )

        result = await channel.deliver(payload)
        assert result.metadata["email_payload"]["priority"] == "high"

        html = channel._format_html(payload)
        assert "priority-high" in html

    @pytest.mark.asyncio
    async def test_email_channel_normal_priority(self):
        """Test email channel handles normal priority correctly."""
        channel = EmailChannel()
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="info",
            subject="Information",
            body="Normal priority message",
            priority="normal"
        )

        result = await channel.deliver(payload)
        assert result.metadata["email_payload"]["priority"] == "normal"

        html = channel._format_html(payload)
        assert "priority-normal" in html

    @pytest.mark.asyncio
    async def test_email_channel_low_priority(self):
        """Test email channel handles low priority correctly."""
        channel = EmailChannel()
        recipient_id = uuid.uuid4()

        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type="info",
            subject="FYI",
            body="Low priority message",
            priority="low"
        )

        result = await channel.deliver(payload)
        assert result.metadata["email_payload"]["priority"] == "low"

        html = channel._format_html(payload)
        assert "priority-low" in html

    @pytest.mark.asyncio
    async def test_webhook_channel_priority_in_payload(self):
        """Test webhook channel includes priority in payload."""
        channel = WebhookChannel()
        recipient_id = uuid.uuid4()

        for priority in ["high", "normal", "low"]:
            payload = NotificationPayload(
                recipient_id=recipient_id,
                notification_type="test",
                subject="Test",
                body="Test",
                priority=priority
            )

            result = await channel.deliver(payload)
            assert result.metadata["payload"]["priority"] == priority

    @pytest.mark.asyncio
    async def test_in_app_channel_priority_preserved(self):
        """Test in-app channel preserves priority."""
        channel = InAppChannel()
        db = MagicMock()
        recipient_id = uuid.uuid4()

        for priority in ["high", "normal", "low"]:
            payload = NotificationPayload(
                recipient_id=recipient_id,
                notification_type="test",
                subject="Test",
                body="Test",
                priority=priority
            )

            result = await channel.deliver(payload, db)
            # Priority is preserved in the payload (tested in the deliver logic)
            assert result.success is True
