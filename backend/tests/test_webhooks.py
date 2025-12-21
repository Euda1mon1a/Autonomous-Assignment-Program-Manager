"""Tests for webhook delivery service."""
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.webhooks.delivery import WebhookDeliveryManager
from app.webhooks.models import (
    Webhook,
    WebhookDeadLetter,
    WebhookDelivery,
    WebhookDeliveryStatus,
    WebhookEventType,
    WebhookStatus,
)
from app.webhooks.service import WebhookService
from app.webhooks.signatures import WebhookSignatureGenerator


# Async test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def async_db():
    """Create an async test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ============================================================================
# Signature Generation Tests
# ============================================================================


class TestWebhookSignatureGenerator:
    """Test webhook signature generation and verification."""

    def test_generate_signature(self):
        """Test signature generation."""
        generator = WebhookSignatureGenerator()
        payload = {"event": "test.event", "data": {"id": "123"}}
        secret = "test-secret-key-12345678901234567890"

        signature, timestamp = generator.generate_signature(payload, secret)

        assert signature.startswith("sha256=")
        assert len(signature) > 10
        assert isinstance(timestamp, int)
        assert timestamp > 0

    def test_verify_signature_valid(self):
        """Test valid signature verification."""
        generator = WebhookSignatureGenerator()
        payload = {"event": "test.event", "data": {"id": "123"}}
        secret = "test-secret-key-12345678901234567890"

        signature, timestamp = generator.generate_signature(payload, secret)

        # Verify with correct signature and timestamp
        assert generator.verify_signature(payload, signature, timestamp, secret)

    def test_verify_signature_invalid(self):
        """Test invalid signature rejection."""
        generator = WebhookSignatureGenerator()
        payload = {"event": "test.event", "data": {"id": "123"}}
        secret = "test-secret-key-12345678901234567890"

        signature, timestamp = generator.generate_signature(payload, secret)

        # Verify with wrong secret
        assert not generator.verify_signature(
            payload, signature, timestamp, "wrong-secret"
        )

    def test_verify_signature_expired(self):
        """Test expired signature rejection."""
        generator = WebhookSignatureGenerator(timestamp_tolerance_seconds=1)
        payload = {"event": "test.event"}
        secret = "test-secret-key-12345678901234567890"

        # Generate signature with old timestamp
        old_timestamp = int(datetime.utcnow().timestamp()) - 10
        signature, _ = generator.generate_signature(payload, secret, old_timestamp)

        # Verify should fail due to timestamp
        with pytest.raises(ValueError, match="Timestamp outside tolerance window"):
            generator.verify_signature(payload, signature, old_timestamp, secret)

    def test_generate_headers(self):
        """Test webhook header generation."""
        generator = WebhookSignatureGenerator()
        payload = {"data": "test"}
        secret = "test-secret-key-12345678901234567890"
        event_type = "test.event"
        delivery_id = "delivery-123"

        headers = generator.generate_headers(payload, secret, event_type, delivery_id)

        assert "X-Webhook-Signature" in headers
        assert "X-Webhook-Timestamp" in headers
        assert "X-Webhook-Event" in headers
        assert "X-Webhook-Delivery" in headers
        assert headers["X-Webhook-Event"] == event_type
        assert headers["X-Webhook-Delivery"] == delivery_id
        assert headers["X-Webhook-Signature"].startswith("sha256=")


# ============================================================================
# Webhook Service Tests
# ============================================================================


class TestWebhookService:
    """Test webhook service business logic."""

    @pytest.mark.asyncio
    async def test_create_webhook(self, async_db):
        """Test webhook creation."""
        service = WebhookService()

        webhook = await service.create_webhook(
            db=async_db,
            url="https://example.com/webhook",
            name="Test Webhook",
            event_types=[WebhookEventType.SCHEDULE_CREATED.value],
            description="Test webhook endpoint"
        )

        assert webhook.id is not None
        assert webhook.url == "https://example.com/webhook"
        assert webhook.name == "Test Webhook"
        assert webhook.status == WebhookStatus.ACTIVE.value
        assert len(webhook.secret) > 0
        assert WebhookEventType.SCHEDULE_CREATED.value in webhook.event_types

    @pytest.mark.asyncio
    async def test_create_webhook_invalid_event_type(self, async_db):
        """Test webhook creation with invalid event type."""
        service = WebhookService()

        with pytest.raises(ValueError, match="Invalid event types"):
            await service.create_webhook(
                db=async_db,
                url="https://example.com/webhook",
                name="Test Webhook",
                event_types=["invalid.event.type"]
            )

    @pytest.mark.asyncio
    async def test_get_webhook(self, async_db):
        """Test retrieving a webhook."""
        service = WebhookService()

        # Create webhook
        created = await service.create_webhook(
            db=async_db,
            url="https://example.com/webhook",
            name="Test Webhook",
            event_types=[WebhookEventType.SCHEDULE_CREATED.value]
        )

        # Get webhook
        retrieved = await service.get_webhook(async_db, created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.url == created.url

    @pytest.mark.asyncio
    async def test_update_webhook(self, async_db):
        """Test updating a webhook."""
        service = WebhookService()

        # Create webhook
        webhook = await service.create_webhook(
            db=async_db,
            url="https://example.com/webhook",
            name="Test Webhook",
            event_types=[WebhookEventType.SCHEDULE_CREATED.value]
        )

        # Update webhook
        updated = await service.update_webhook(
            async_db,
            webhook.id,
            name="Updated Webhook",
            url="https://example.com/updated"
        )

        assert updated.name == "Updated Webhook"
        assert updated.url == "https://example.com/updated"

    @pytest.mark.asyncio
    async def test_delete_webhook(self, async_db):
        """Test deleting a webhook."""
        service = WebhookService()

        # Create webhook
        webhook = await service.create_webhook(
            db=async_db,
            url="https://example.com/webhook",
            name="Test Webhook",
            event_types=[WebhookEventType.SCHEDULE_CREATED.value]
        )

        # Delete webhook
        result = await service.delete_webhook(async_db, webhook.id)
        assert result is True

        # Verify deletion
        retrieved = await service.get_webhook(async_db, webhook.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_pause_resume_webhook(self, async_db):
        """Test pausing and resuming a webhook."""
        service = WebhookService()

        # Create webhook
        webhook = await service.create_webhook(
            db=async_db,
            url="https://example.com/webhook",
            name="Test Webhook",
            event_types=[WebhookEventType.SCHEDULE_CREATED.value]
        )

        # Pause webhook
        paused = await service.pause_webhook(async_db, webhook.id)
        assert paused.status == WebhookStatus.PAUSED.value

        # Resume webhook
        resumed = await service.resume_webhook(async_db, webhook.id)
        assert resumed.status == WebhookStatus.ACTIVE.value

    @pytest.mark.asyncio
    async def test_trigger_event(self, async_db):
        """Test triggering a webhook event."""
        service = WebhookService()

        # Create webhook
        await service.create_webhook(
            db=async_db,
            url="https://example.com/webhook",
            name="Test Webhook",
            event_types=[WebhookEventType.SCHEDULE_CREATED.value]
        )

        # Trigger event
        count = await service.trigger_event(
            db=async_db,
            event_type=WebhookEventType.SCHEDULE_CREATED.value,
            payload={"schedule_id": "123"}
        )

        assert count == 1

        # Verify delivery was created
        deliveries = await service.list_deliveries(async_db, limit=10)
        assert len(deliveries) == 1
        assert deliveries[0].event_type == WebhookEventType.SCHEDULE_CREATED.value

    @pytest.mark.asyncio
    async def test_trigger_event_no_subscribers(self, async_db):
        """Test triggering event with no subscribers."""
        service = WebhookService()

        # Trigger event without any webhooks
        count = await service.trigger_event(
            db=async_db,
            event_type=WebhookEventType.SCHEDULE_CREATED.value,
            payload={"schedule_id": "123"}
        )

        assert count == 0


# ============================================================================
# Webhook Delivery Tests
# ============================================================================


class TestWebhookDeliveryManager:
    """Test webhook delivery manager."""

    @pytest.mark.asyncio
    async def test_calculate_retry_delay(self):
        """Test exponential backoff calculation."""
        manager = WebhookDeliveryManager(base_retry_delay_seconds=60)

        assert manager._calculate_retry_delay(1) == 60
        assert manager._calculate_retry_delay(2) == 120
        assert manager._calculate_retry_delay(3) == 240
        assert manager._calculate_retry_delay(4) == 480
        assert manager._calculate_retry_delay(5) == 960

    @pytest.mark.asyncio
    async def test_calculate_retry_delay_with_cap(self):
        """Test retry delay respects maximum."""
        manager = WebhookDeliveryManager(
            base_retry_delay_seconds=60,
            max_retry_delay_seconds=300
        )

        assert manager._calculate_retry_delay(10) == 300  # Capped

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_successful_delivery(self, mock_post, async_db):
        """Test successful webhook delivery."""
        # Create webhook and delivery
        webhook = Webhook(
            id=uuid4(),
            url="https://example.com/webhook",
            name="Test Webhook",
            event_types=[WebhookEventType.SCHEDULE_CREATED.value],
            secret="test-secret-key-12345678901234567890",
            status=WebhookStatus.ACTIVE.value,
            timeout_seconds=30,
            max_retries=5
        )
        async_db.add(webhook)
        await async_db.commit()
        await async_db.refresh(webhook)

        delivery = WebhookDelivery(
            id=uuid4(),
            webhook_id=webhook.id,
            event_type=WebhookEventType.SCHEDULE_CREATED.value,
            payload={"schedule_id": "123"},
            status=WebhookDeliveryStatus.PENDING.value,
            max_attempts=5
        )
        async_db.add(delivery)
        await async_db.commit()
        await async_db.refresh(delivery)

        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        # Deliver webhook
        manager = WebhookDeliveryManager()
        success = await manager.deliver(async_db, str(delivery.id))

        assert success is True
        await async_db.refresh(delivery)
        assert delivery.status == WebhookDeliveryStatus.SUCCESS.value
        assert delivery.http_status_code == 200

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_failed_delivery_with_retry(self, mock_post, async_db):
        """Test failed delivery creates retry."""
        # Create webhook and delivery
        webhook = Webhook(
            id=uuid4(),
            url="https://example.com/webhook",
            name="Test Webhook",
            event_types=[WebhookEventType.SCHEDULE_CREATED.value],
            secret="test-secret-key-12345678901234567890",
            status=WebhookStatus.ACTIVE.value,
            timeout_seconds=30,
            max_retries=5
        )
        async_db.add(webhook)
        await async_db.commit()
        await async_db.refresh(webhook)

        delivery = WebhookDelivery(
            id=uuid4(),
            webhook_id=webhook.id,
            event_type=WebhookEventType.SCHEDULE_CREATED.value,
            payload={"schedule_id": "123"},
            status=WebhookDeliveryStatus.PENDING.value,
            max_attempts=5
        )
        async_db.add(delivery)
        await async_db.commit()
        await async_db.refresh(delivery)

        # Mock failed HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        # Deliver webhook
        manager = WebhookDeliveryManager()
        success = await manager.deliver(async_db, str(delivery.id))

        assert success is False
        await async_db.refresh(delivery)
        assert delivery.status == WebhookDeliveryStatus.FAILED.value
        assert delivery.http_status_code == 500
        assert delivery.next_retry_at is not None

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_max_retries_creates_dead_letter(self, mock_post, async_db):
        """Test max retries exceeded creates dead letter."""
        # Create webhook and delivery
        webhook = Webhook(
            id=uuid4(),
            url="https://example.com/webhook",
            name="Test Webhook",
            event_types=[WebhookEventType.SCHEDULE_CREATED.value],
            secret="test-secret-key-12345678901234567890",
            status=WebhookStatus.ACTIVE.value,
            timeout_seconds=30,
            max_retries=2
        )
        async_db.add(webhook)
        await async_db.commit()
        await async_db.refresh(webhook)

        delivery = WebhookDelivery(
            id=uuid4(),
            webhook_id=webhook.id,
            event_type=WebhookEventType.SCHEDULE_CREATED.value,
            payload={"schedule_id": "123"},
            status=WebhookDeliveryStatus.PENDING.value,
            max_attempts=2,
            attempt_count=2  # Already at max attempts
        )
        async_db.add(delivery)
        await async_db.commit()
        await async_db.refresh(delivery)

        # Mock failed HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        # Deliver webhook
        manager = WebhookDeliveryManager()
        success = await manager.deliver(async_db, str(delivery.id))

        assert success is False
        await async_db.refresh(delivery)
        assert delivery.status == WebhookDeliveryStatus.DEAD_LETTER.value

        # Verify dead letter was created
        service = WebhookService()
        dead_letters = await service.list_dead_letters(async_db, limit=10)
        assert len(dead_letters) == 1
        assert dead_letters[0].delivery_id == delivery.id


# ============================================================================
# Integration Tests
# ============================================================================


class TestWebhookIntegration:
    """Integration tests for complete webhook flow."""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_complete_webhook_flow(self, mock_post, async_db):
        """Test complete webhook creation, trigger, and delivery flow."""
        service = WebhookService()

        # 1. Create webhook
        webhook = await service.create_webhook(
            db=async_db,
            url="https://example.com/webhook",
            name="Test Webhook",
            event_types=[WebhookEventType.SCHEDULE_CREATED.value],
            description="Integration test webhook"
        )

        assert webhook.id is not None

        # 2. Trigger event
        count = await service.trigger_event(
            db=async_db,
            event_type=WebhookEventType.SCHEDULE_CREATED.value,
            payload={"schedule_id": "123", "created_by": "test-user"}
        )

        assert count == 1

        # 3. Mock successful delivery
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        # 4. Get delivery and process it
        deliveries = await service.list_deliveries(async_db, webhook_id=webhook.id)
        assert len(deliveries) == 1

        delivery = deliveries[0]
        success = await service.delivery_manager.deliver(async_db, str(delivery.id))

        assert success is True

        # 5. Verify delivery status
        updated_delivery = await service.get_delivery_status(async_db, delivery.id)
        assert updated_delivery.status == WebhookDeliveryStatus.SUCCESS.value
        assert updated_delivery.http_status_code == 200
