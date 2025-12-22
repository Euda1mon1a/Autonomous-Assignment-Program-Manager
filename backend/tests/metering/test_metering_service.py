"""Tests for metering service."""
import json
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.metering.service import (
    MeteringService,
    MeteredResource,
    AggregationPeriod,
    PricingConfig,
    UsageTier,
)


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis_mock = MagicMock()
    redis_mock.zadd = MagicMock()
    redis_mock.expire = MagicMock()
    redis_mock.incrby = MagicMock()
    redis_mock.get = MagicMock(return_value=None)
    redis_mock.setex = MagicMock()
    redis_mock.zrangebyscore = MagicMock(return_value=[])
    return redis_mock


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def metering_service(mock_db, mock_redis):
    """Create metering service with mocks."""
    return MeteringService(db=mock_db, redis_client=mock_redis)


class TestPricingConfig:
    """Test pricing configuration."""

    def test_calculate_cost_basic_tier(self):
        """Test cost calculation for basic tier."""
        cost = PricingConfig.calculate_cost(
            resource=MeteredResource.SCHEDULE_GENERATION,
            quantity=1,
            tier=UsageTier.BASIC,
        )

        # Should be base price (1.00) * quantity (1) * tier multiplier (1.0)
        assert cost == Decimal("1.00")

    def test_calculate_cost_professional_tier(self):
        """Test cost calculation with tier discount."""
        cost = PricingConfig.calculate_cost(
            resource=MeteredResource.SCHEDULE_GENERATION,
            quantity=1,
            tier=UsageTier.PROFESSIONAL,
        )

        # Should be base price (1.00) * tier multiplier (0.75)
        assert cost == Decimal("0.75")

    def test_calculate_cost_volume_discount(self):
        """Test cost calculation with volume discount."""
        cost = PricingConfig.calculate_cost(
            resource=MeteredResource.API_READ,
            quantity=2000,
            tier=UsageTier.BASIC,
        )

        # Base price: 0.001
        # Volume discount: 5% (for >1000 units)
        # Expected: 0.001 * 2000 * 0.95 = 1.90
        assert cost == Decimal("1.90")

    def test_calculate_cost_free_tier(self):
        """Test cost calculation for free tier."""
        cost = PricingConfig.calculate_cost(
            resource=MeteredResource.SCHEDULE_GENERATION,
            quantity=10,
            tier=UsageTier.FREE,
        )

        # Free tier should have 0 cost
        assert cost == Decimal("0.00")


class TestMeteringService:
    """Test metering service."""

    @pytest.mark.asyncio
    async def test_record_event(self, metering_service, mock_redis):
        """Test recording a usage event."""
        event = await metering_service.record_event(
            user_id="user-123",
            resource=MeteredResource.SCHEDULE_GENERATION,
            quantity=1,
            metadata={"complexity": "high"},
        )

        assert event.user_id == "user-123"
        assert event.resource == MeteredResource.SCHEDULE_GENERATION
        assert event.quantity == 1
        assert event.cost == Decimal("1.00")
        assert event.metadata == {"complexity": "high"}

        # Verify Redis calls were made
        assert mock_redis.zadd.called
        assert mock_redis.incrby.called

    @pytest.mark.asyncio
    async def test_check_quota_within_limit(self, metering_service, mock_redis):
        """Test quota check when within limit."""
        # Mock current usage as 50
        mock_redis.get.return_value = b"50"

        is_allowed, reason = await metering_service.check_quota(
            user_id="user-123",
            resource=MeteredResource.SCHEDULE_GENERATION,
            quantity=10,
            quota_limit=100,
        )

        assert is_allowed is True
        assert reason is None

    @pytest.mark.asyncio
    async def test_check_quota_exceeds_limit(self, metering_service, mock_redis):
        """Test quota check when exceeding limit."""
        # Mock current usage as 95
        mock_redis.get.return_value = b"95"

        is_allowed, reason = await metering_service.check_quota(
            user_id="user-123",
            resource=MeteredResource.SCHEDULE_GENERATION,
            quantity=10,
            quota_limit=100,
        )

        assert is_allowed is False
        assert "Quota exceeded" in reason

    @pytest.mark.asyncio
    async def test_track_overage_creates_alert(self, metering_service, mock_redis):
        """Test overage tracking creates alert."""
        alert = await metering_service.track_overage(
            user_id="user-123",
            resource=MeteredResource.SCHEDULE_GENERATION,
            quota_limit=100,
            actual_usage=150,
        )

        assert alert is not None
        assert alert.overage_amount == 50
        assert alert.overage_percentage == 50.0
        assert alert.severity == "critical"
        assert mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_track_overage_no_alert_when_under_limit(
        self, metering_service, mock_redis
    ):
        """Test no alert when under quota."""
        alert = await metering_service.track_overage(
            user_id="user-123",
            resource=MeteredResource.SCHEDULE_GENERATION,
            quota_limit=100,
            actual_usage=80,
        )

        assert alert is None

    @pytest.mark.asyncio
    async def test_forecast_usage(self, metering_service, mock_redis):
        """Test usage forecasting."""
        # Mock historical usage data
        historical_events = []
        for i in range(30):
            event_data = {
                "quantity": 10 + i,  # Increasing usage
                "cost": "1.00",
                "metadata": {},
                "timestamp": (datetime.utcnow() - timedelta(days=30 - i)).isoformat(),
            }
            historical_events.append(json.dumps(event_data).encode())

        mock_redis.zrangebyscore.return_value = historical_events

        forecast = await metering_service.forecast_usage(
            user_id="user-123",
            resource=MeteredResource.SCHEDULE_GENERATION,
            forecast_periods=7,
        )

        assert forecast.user_id == "user-123"
        assert forecast.resource == MeteredResource.SCHEDULE_GENERATION
        assert forecast.predicted_usage > 0
        assert forecast.confidence_interval_lower < forecast.predicted_usage
        assert forecast.confidence_interval_upper > forecast.predicted_usage
        assert 0.0 <= forecast.model_accuracy <= 1.0

    @pytest.mark.asyncio
    async def test_generate_billing_record(self, metering_service, mock_redis):
        """Test billing record generation."""
        # Mock usage events
        events = []
        for i in range(10):
            event = {
                "quantity": 5,
                "cost": "1.00",
                "metadata": {},
                "timestamp": datetime.utcnow().isoformat(),
            }
            events.append(json.dumps(event).encode())

        mock_redis.zrangebyscore.return_value = events

        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()

        billing_record = await metering_service.generate_billing_record(
            user_id="user-123",
            billing_period_start=start_date,
            billing_period_end=end_date,
        )

        assert billing_record.user_id == "user-123"
        assert billing_record.subtotal >= Decimal("0")
        assert billing_record.taxes >= Decimal("0")
        assert billing_record.total == billing_record.subtotal + billing_record.taxes

    @pytest.mark.asyncio
    async def test_export_billing_data_stripe_format(
        self, metering_service, mock_redis
    ):
        """Test billing data export in Stripe format."""
        # Mock usage events
        events = [
            json.dumps(
                {
                    "quantity": 10,
                    "cost": "10.00",
                    "metadata": {},
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ).encode()
        ]
        mock_redis.zrangebyscore.return_value = events

        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()

        export_data = await metering_service.export_billing_data(
            user_id="user-123",
            start_date=start_date,
            end_date=end_date,
            format="stripe",
        )

        assert "customer" in export_data
        assert export_data["customer"] == "user-123"
        assert "amount" in export_data
        assert "currency" in export_data
        assert export_data["currency"] == "usd"

    @pytest.mark.asyncio
    async def test_get_usage_trends(self, metering_service, mock_redis):
        """Test usage trends analysis."""
        # Mock increasing usage over time
        events = []
        for i in range(7):
            event = {
                "quantity": i + 1,
                "cost": "1.00",
                "metadata": {},
                "timestamp": (datetime.utcnow() - timedelta(days=7 - i)).isoformat(),
            }
            events.append(json.dumps(event).encode())

        mock_redis.zrangebyscore.return_value = events

        trends = await metering_service.get_usage_trends(
            user_id="user-123",
            resource=MeteredResource.SCHEDULE_GENERATION,
            days=7,
        )

        assert trends["user_id"] == "user-123"
        assert "statistics" in trends
        assert "trend" in trends
        assert trends["trend"]["direction"] in ["increasing", "decreasing", "stable"]
        assert len(trends["daily_usage"]) > 0


class TestAggregation:
    """Test usage aggregation."""

    @pytest.mark.asyncio
    async def test_aggregate_usage_single_resource(
        self, metering_service, mock_redis
    ):
        """Test aggregating usage for a single resource."""
        # Mock events
        events = []
        for i in range(5):
            event = {
                "quantity": 2,
                "cost": "2.00",
                "metadata": {},
                "timestamp": datetime.utcnow().isoformat(),
            }
            events.append(json.dumps(event).encode())

        mock_redis.zrangebyscore.return_value = events

        aggregations = await metering_service.aggregate_usage(
            user_id="user-123",
            resource=MeteredResource.SCHEDULE_GENERATION,
            period=AggregationPeriod.DAILY,
        )

        assert len(aggregations) > 0
        agg = aggregations[0]
        assert agg.user_id == "user-123"
        assert agg.total_quantity == 10  # 5 events * 2 quantity each
        assert agg.total_cost == Decimal("10.00")  # 5 events * 2.00 each

    @pytest.mark.asyncio
    async def test_aggregate_usage_no_events(self, metering_service, mock_redis):
        """Test aggregation when no events exist."""
        mock_redis.zrangebyscore.return_value = []

        aggregations = await metering_service.aggregate_usage(
            user_id="user-123",
            resource=MeteredResource.SCHEDULE_GENERATION,
            period=AggregationPeriod.DAILY,
        )

        # Should return empty list or handle gracefully
        assert isinstance(aggregations, list)


class TestOverageAlerts:
    """Test overage alert functionality."""

    @pytest.mark.asyncio
    async def test_get_overage_alerts(self, metering_service, mock_redis):
        """Test retrieving overage alerts."""
        # Mock alert data
        alert_data = json.dumps(
            {
                "quota_limit": 100,
                "actual_usage": 150,
                "overage_amount": 50,
                "overage_percentage": 50.0,
                "severity": "critical",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        mock_redis.get.return_value = alert_data.encode()

        alerts = await metering_service.get_overage_alerts(
            user_id="user-123",
            resource=MeteredResource.SCHEDULE_GENERATION,
        )

        assert len(alerts) > 0
        alert = alerts[0]
        assert alert.overage_amount == 50
        assert alert.severity == "critical"
