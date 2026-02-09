"""Tests for webhook schemas (Field bounds, field_validators, defaults, nested models)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookListResponse,
    WebhookDeliveryResponse,
    WebhookDeliveryListResponse,
    WebhookDeliveryRetryRequest,
    WebhookEventTrigger,
    WebhookEventTriggerResponse,
    WebhookDeadLetterResponse,
    WebhookDeadLetterListResponse,
    WebhookDeadLetterResolveRequest,
    WebhookStatistics,
    WebhookStatisticsResponse,
)


class TestWebhookCreate:
    def test_valid(self):
        r = WebhookCreate(
            url="https://example.com/webhook",
            name="My Webhook",
            event_types=["schedule.created"],
        )
        assert r.timeout_seconds == 30
        assert r.max_retries == 5
        assert r.secret is None
        assert r.custom_headers is None
        assert r.metadata is None

    # --- name min_length=1, max_length=255 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            WebhookCreate(
                url="https://example.com/webhook",
                name="",
                event_types=["ev"],
            )

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            WebhookCreate(
                url="https://example.com/webhook",
                name="x" * 256,
                event_types=["ev"],
            )

    # --- event_types min_length=1 ---

    def test_event_types_empty(self):
        with pytest.raises(ValidationError):
            WebhookCreate(
                url="https://example.com/webhook",
                name="Hook",
                event_types=[],
            )

    # --- event_types field_validator deduplicates ---

    def test_event_types_deduplicated(self):
        r = WebhookCreate(
            url="https://example.com/webhook",
            name="Hook",
            event_types=["a", "b", "a"],
        )
        assert sorted(r.event_types) == ["a", "b"]

    # --- secret min_length=32 ---

    def test_secret_too_short(self):
        with pytest.raises(ValidationError):
            WebhookCreate(
                url="https://example.com/webhook",
                name="Hook",
                event_types=["ev"],
                secret="short",
            )

    def test_secret_valid(self):
        r = WebhookCreate(
            url="https://example.com/webhook",
            name="Hook",
            event_types=["ev"],
            secret="a" * 32,
        )
        assert len(r.secret) == 32

    # --- timeout_seconds ge=1, le=300 ---

    def test_timeout_below_min(self):
        with pytest.raises(ValidationError):
            WebhookCreate(
                url="https://example.com/webhook",
                name="Hook",
                event_types=["ev"],
                timeout_seconds=0,
            )

    def test_timeout_above_max(self):
        with pytest.raises(ValidationError):
            WebhookCreate(
                url="https://example.com/webhook",
                name="Hook",
                event_types=["ev"],
                timeout_seconds=301,
            )

    # --- max_retries ge=0, le=10 ---

    def test_max_retries_below_min(self):
        with pytest.raises(ValidationError):
            WebhookCreate(
                url="https://example.com/webhook",
                name="Hook",
                event_types=["ev"],
                max_retries=-1,
            )

    def test_max_retries_above_max(self):
        with pytest.raises(ValidationError):
            WebhookCreate(
                url="https://example.com/webhook",
                name="Hook",
                event_types=["ev"],
                max_retries=11,
            )

    # --- url must be HttpUrl ---

    def test_invalid_url(self):
        with pytest.raises(ValidationError):
            WebhookCreate(
                url="not-a-url",
                name="Hook",
                event_types=["ev"],
            )


class TestWebhookUpdate:
    def test_all_none(self):
        r = WebhookUpdate()
        assert r.url is None
        assert r.name is None
        assert r.event_types is None
        assert r.timeout_seconds is None

    def test_partial(self):
        r = WebhookUpdate(name="Updated", timeout_seconds=60)
        assert r.name == "Updated"
        assert r.timeout_seconds == 60

    def test_event_types_deduplicated(self):
        r = WebhookUpdate(event_types=["x", "y", "x"])
        assert sorted(r.event_types) == ["x", "y"]

    def test_event_types_none_passes(self):
        r = WebhookUpdate(event_types=None)
        assert r.event_types is None

    def test_bounds_on_update(self):
        with pytest.raises(ValidationError):
            WebhookUpdate(timeout_seconds=0)


class TestWebhookResponse:
    def test_valid(self):
        r = WebhookResponse(
            id=uuid4(),
            url="https://example.com/webhook",
            name="Hook",
            description=None,
            event_types=["ev"],
            status="active",
            retry_enabled=True,
            max_retries=5,
            timeout_seconds=30,
            custom_headers={},
            metadata={},
            owner_id=None,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
            last_triggered_at=None,
        )
        assert r.status == "active"
        assert r.last_triggered_at is None


class TestWebhookListResponse:
    def test_valid(self):
        r = WebhookListResponse(webhooks=[], total=0, skip=0, limit=50)
        assert r.webhooks == []
        assert r.limit == 50


class TestWebhookDeliveryResponse:
    def test_valid(self):
        r = WebhookDeliveryResponse(
            id=uuid4(),
            webhook_id=uuid4(),
            event_type="schedule.created",
            event_id=None,
            payload={"key": "value"},
            status="delivered",
            attempt_count=1,
            max_attempts=5,
            next_retry_at=None,
            http_status_code=200,
            response_body=None,
            response_time_ms=150,
            error_message=None,
            created_at=datetime(2026, 1, 1),
            first_attempted_at=datetime(2026, 1, 1),
            last_attempted_at=datetime(2026, 1, 1),
            completed_at=datetime(2026, 1, 1),
        )
        assert r.status == "delivered"
        assert r.http_status_code == 200


class TestWebhookDeliveryListResponse:
    def test_valid(self):
        r = WebhookDeliveryListResponse(deliveries=[], total=0, skip=0, limit=50)
        assert r.deliveries == []


class TestWebhookDeliveryRetryRequest:
    def test_valid(self):
        did = uuid4()
        r = WebhookDeliveryRetryRequest(delivery_id=did)
        assert r.delivery_id == did


class TestWebhookEventTrigger:
    def test_defaults(self):
        r = WebhookEventTrigger(event_type="test.event", payload={"data": 1})
        assert r.event_id is None
        assert r.immediate is False

    def test_immediate(self):
        r = WebhookEventTrigger(event_type="test.event", payload={}, immediate=True)
        assert r.immediate is True


class TestWebhookEventTriggerResponse:
    def test_valid(self):
        r = WebhookEventTriggerResponse(
            event_type="test.event", webhooks_triggered=3, message="OK"
        )
        assert r.webhooks_triggered == 3


class TestWebhookDeadLetterResponse:
    def test_valid(self):
        r = WebhookDeadLetterResponse(
            id=uuid4(),
            delivery_id=uuid4(),
            webhook_id=uuid4(),
            event_type="ev",
            payload={"x": 1},
            total_attempts=5,
            last_error_message="timeout",
            last_http_status=None,
            resolved=False,
            resolved_at=None,
            resolved_by=None,
            resolution_notes=None,
            created_at=datetime(2026, 1, 1),
        )
        assert r.resolved is False
        assert r.last_error_message == "timeout"


class TestWebhookDeadLetterListResponse:
    def test_valid(self):
        r = WebhookDeadLetterListResponse(dead_letters=[], total=0, skip=0, limit=50)
        assert r.dead_letters == []


class TestWebhookDeadLetterResolveRequest:
    def test_defaults(self):
        r = WebhookDeadLetterResolveRequest()
        assert r.notes is None
        assert r.retry is False

    def test_with_notes(self):
        r = WebhookDeadLetterResolveRequest(notes="Fixed upstream", retry=True)
        assert r.retry is True


class TestWebhookStatistics:
    def test_valid(self):
        r = WebhookStatistics(
            webhook_id=uuid4(),
            total_deliveries=100,
            successful_deliveries=95,
            failed_deliveries=5,
            pending_deliveries=0,
            dead_letter_count=2,
            success_rate=0.95,
            average_response_time_ms=150.5,
        )
        assert r.success_rate == 0.95
        assert r.average_response_time_ms == 150.5


class TestWebhookStatisticsResponse:
    def test_valid(self):
        stats = WebhookStatistics(
            webhook_id=uuid4(),
            total_deliveries=10,
            successful_deliveries=10,
            failed_deliveries=0,
            pending_deliveries=0,
            dead_letter_count=0,
            success_rate=1.0,
            average_response_time_ms=None,
        )
        r = WebhookStatisticsResponse(statistics=stats)
        assert r.statistics.success_rate == 1.0
        assert r.statistics.average_response_time_ms is None
