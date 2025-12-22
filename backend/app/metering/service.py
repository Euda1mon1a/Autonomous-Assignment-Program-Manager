"""
Metering service for usage tracking, billing, and forecasting.

This service provides comprehensive usage metering capabilities including:
- Event recording with detailed metadata
- Time-based usage aggregation (hourly, daily, weekly, monthly, yearly)
- Quota enforcement and overage tracking
- Billing integration and invoice generation
- ML-based usage forecasting
- Usage analytics and reporting
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

import redis
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================


class MeteredResource(str, Enum):
    """Types of metered resources in the system."""

    # API Operations
    API_READ = "api_read"
    API_WRITE = "api_write"
    API_DELETE = "api_delete"

    # Schedule Operations
    SCHEDULE_GENERATION = "schedule_generation"
    SCHEDULE_VALIDATION = "schedule_validation"
    SCHEDULE_OPTIMIZATION = "schedule_optimization"

    # Export Operations
    EXPORT_PDF = "export_pdf"
    EXPORT_EXCEL = "export_excel"
    EXPORT_CSV = "export_csv"
    EXPORT_ICAL = "export_ical"

    # Report Generation
    REPORT_COMPLIANCE = "report_compliance"
    REPORT_ANALYTICS = "report_analytics"
    REPORT_UTILIZATION = "report_utilization"
    REPORT_CUSTOM = "report_custom"

    # Data Operations
    DATA_IMPORT = "data_import"
    DATA_BULK_UPDATE = "data_bulk_update"

    # ML/AI Operations
    ML_SWAP_MATCHING = "ml_swap_matching"
    ML_CONFLICT_DETECTION = "ml_conflict_detection"
    ML_FORECASTING = "ml_forecasting"

    # Notification Operations
    NOTIFICATION_EMAIL = "notification_email"
    NOTIFICATION_SMS = "notification_sms"
    NOTIFICATION_PUSH = "notification_push"

    # Storage Operations
    STORAGE_UPLOAD = "storage_upload"
    STORAGE_DOWNLOAD = "storage_download"


class AggregationPeriod(str, Enum):
    """Time period for usage aggregation."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class UsageTier(str, Enum):
    """Usage tiers for tiered pricing."""

    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class UsageEvent:
    """Represents a single usage event."""

    user_id: str
    resource: MeteredResource
    quantity: int
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    cost: Optional[Decimal] = None
    billed: bool = False
    event_id: Optional[str] = None


@dataclass
class UsageAggregation:
    """Aggregated usage data for a time period."""

    user_id: str
    resource: MeteredResource
    period: AggregationPeriod
    period_start: datetime
    period_end: datetime
    total_quantity: int
    total_cost: Decimal
    event_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UsageReport:
    """Comprehensive usage report."""

    user_id: str
    start_date: datetime
    end_date: datetime
    total_cost: Decimal
    by_resource: dict[str, UsageAggregation]
    by_period: dict[str, UsageAggregation]
    overages: list["OverageAlert"]
    forecasted_usage: Optional["ForecastResult"] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BillingRecord:
    """Billing record for invoice generation."""

    user_id: str
    billing_period_start: datetime
    billing_period_end: datetime
    line_items: list[dict[str, Any]]
    subtotal: Decimal
    taxes: Decimal
    total: Decimal
    currency: str = "USD"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OverageAlert:
    """Alert for quota overage."""

    user_id: str
    resource: MeteredResource
    quota_limit: int
    actual_usage: int
    overage_amount: int
    overage_percentage: float
    period: AggregationPeriod
    timestamp: datetime
    severity: str  # "warning", "critical", "emergency"


@dataclass
class ForecastResult:
    """Usage forecast result."""

    user_id: str
    resource: MeteredResource
    forecast_period: AggregationPeriod
    forecast_start: datetime
    forecast_end: datetime
    predicted_usage: int
    confidence_interval_lower: int
    confidence_interval_upper: int
    confidence_level: float
    model_accuracy: float
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Pricing Configuration
# =============================================================================


class PricingConfig:
    """Pricing configuration for metered resources."""

    # Base prices per unit (in cents)
    RESOURCE_PRICES = {
        MeteredResource.API_READ: Decimal("0.001"),
        MeteredResource.API_WRITE: Decimal("0.005"),
        MeteredResource.API_DELETE: Decimal("0.005"),
        MeteredResource.SCHEDULE_GENERATION: Decimal("1.00"),
        MeteredResource.SCHEDULE_VALIDATION: Decimal("0.10"),
        MeteredResource.SCHEDULE_OPTIMIZATION: Decimal("2.00"),
        MeteredResource.EXPORT_PDF: Decimal("0.25"),
        MeteredResource.EXPORT_EXCEL: Decimal("0.25"),
        MeteredResource.EXPORT_CSV: Decimal("0.10"),
        MeteredResource.EXPORT_ICAL: Decimal("0.10"),
        MeteredResource.REPORT_COMPLIANCE: Decimal("0.50"),
        MeteredResource.REPORT_ANALYTICS: Decimal("0.75"),
        MeteredResource.REPORT_UTILIZATION: Decimal("0.50"),
        MeteredResource.REPORT_CUSTOM: Decimal("1.00"),
        MeteredResource.DATA_IMPORT: Decimal("0.50"),
        MeteredResource.DATA_BULK_UPDATE: Decimal("0.75"),
        MeteredResource.ML_SWAP_MATCHING: Decimal("0.50"),
        MeteredResource.ML_CONFLICT_DETECTION: Decimal("0.50"),
        MeteredResource.ML_FORECASTING: Decimal("1.00"),
        MeteredResource.NOTIFICATION_EMAIL: Decimal("0.02"),
        MeteredResource.NOTIFICATION_SMS: Decimal("0.10"),
        MeteredResource.NOTIFICATION_PUSH: Decimal("0.01"),
        MeteredResource.STORAGE_UPLOAD: Decimal("0.05"),  # per MB
        MeteredResource.STORAGE_DOWNLOAD: Decimal("0.02"),  # per MB
    }

    # Tiered pricing multipliers
    TIER_MULTIPLIERS = {
        UsageTier.FREE: Decimal("0"),  # Free tier
        UsageTier.BASIC: Decimal("1.0"),  # Full price
        UsageTier.PROFESSIONAL: Decimal("0.75"),  # 25% discount
        UsageTier.ENTERPRISE: Decimal("0.50"),  # 50% discount
    }

    # Volume discounts (quantity threshold -> discount percentage)
    VOLUME_DISCOUNTS = {
        1000: Decimal("0.05"),  # 5% discount above 1k units
        10000: Decimal("0.10"),  # 10% discount above 10k units
        100000: Decimal("0.15"),  # 15% discount above 100k units
        1000000: Decimal("0.20"),  # 20% discount above 1M units
    }

    @classmethod
    def calculate_cost(
        cls,
        resource: MeteredResource,
        quantity: int,
        tier: UsageTier = UsageTier.BASIC,
    ) -> Decimal:
        """
        Calculate cost for a resource usage.

        Args:
            resource: Type of resource
            quantity: Quantity used
            tier: User tier for pricing

        Returns:
            Decimal: Total cost in cents
        """
        base_price = cls.RESOURCE_PRICES.get(resource, Decimal("0"))
        tier_multiplier = cls.TIER_MULTIPLIERS.get(tier, Decimal("1.0"))

        # Apply volume discount
        volume_discount = Decimal("0")
        for threshold, discount in sorted(cls.VOLUME_DISCOUNTS.items(), reverse=True):
            if quantity >= threshold:
                volume_discount = discount
                break

        # Calculate final cost
        cost_per_unit = base_price * tier_multiplier * (1 - volume_discount)
        total_cost = cost_per_unit * quantity

        return total_cost.quantize(Decimal("0.01"))


# =============================================================================
# Metering Service
# =============================================================================


class MeteringService:
    """
    Main service for usage metering and billing.

    Provides comprehensive metering capabilities including event recording,
    aggregation, billing integration, and usage forecasting.
    """

    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        """
        Initialize metering service.

        Args:
            db: Database session for persistent storage
            redis_client: Redis client for real-time tracking
        """
        self.db = db
        self.redis = redis_client

    # =========================================================================
    # Event Recording
    # =========================================================================

    async def record_event(
        self,
        user_id: str,
        resource: MeteredResource,
        quantity: int = 1,
        metadata: Optional[dict[str, Any]] = None,
        tier: UsageTier = UsageTier.BASIC,
    ) -> UsageEvent:
        """
        Record a usage event.

        Args:
            user_id: User ID
            resource: Type of resource being used
            quantity: Quantity used (default: 1)
            metadata: Optional metadata about the event
            tier: User tier for pricing

        Returns:
            UsageEvent: Recorded event with cost calculation
        """
        timestamp = datetime.utcnow()
        metadata = metadata or {}

        # Calculate cost
        cost = PricingConfig.calculate_cost(resource, quantity, tier)

        # Create event
        event = UsageEvent(
            user_id=user_id,
            resource=resource,
            quantity=quantity,
            timestamp=timestamp,
            metadata=metadata,
            cost=cost,
            billed=False,
            event_id=f"{user_id}:{resource.value}:{timestamp.isoformat()}",
        )

        # Store in Redis for real-time tracking
        await self._store_event_redis(event)

        # Store in database for persistent tracking (would need a model)
        # await self._store_event_db(event)

        logger.info(
            f"Recorded usage event: user={user_id}, resource={resource.value}, "
            f"quantity={quantity}, cost={cost}"
        )

        return event

    async def _store_event_redis(self, event: UsageEvent) -> None:
        """
        Store event in Redis for real-time tracking.

        Args:
            event: Usage event to store
        """
        # Store in sorted set by timestamp
        key = f"metering:events:{event.user_id}:{event.resource.value}"
        score = event.timestamp.timestamp()
        value = json.dumps(
            {
                "quantity": event.quantity,
                "cost": str(event.cost),
                "metadata": event.metadata,
                "timestamp": event.timestamp.isoformat(),
            }
        )

        self.redis.zadd(key, {value: score})

        # Set expiration (keep events for 90 days in Redis)
        self.redis.expire(key, 90 * 24 * 3600)

        # Update real-time counters
        await self._update_realtime_counters(event)

    async def _update_realtime_counters(self, event: UsageEvent) -> None:
        """
        Update real-time usage counters.

        Args:
            event: Usage event
        """
        now = datetime.utcnow()

        # Hourly counter
        hour_key = f"metering:hourly:{event.user_id}:{event.resource.value}:{now.strftime('%Y-%m-%d-%H')}"
        self.redis.incrby(hour_key, event.quantity)
        self.redis.expire(hour_key, 7 * 24 * 3600)  # 7 days

        # Daily counter
        day_key = f"metering:daily:{event.user_id}:{event.resource.value}:{now.strftime('%Y-%m-%d')}"
        self.redis.incrby(day_key, event.quantity)
        self.redis.expire(day_key, 90 * 24 * 3600)  # 90 days

        # Monthly counter
        month_key = f"metering:monthly:{event.user_id}:{event.resource.value}:{now.strftime('%Y-%m')}"
        self.redis.incrby(month_key, event.quantity)
        self.redis.expire(month_key, 365 * 24 * 3600)  # 1 year

    # =========================================================================
    # Usage Aggregation
    # =========================================================================

    async def aggregate_usage(
        self,
        user_id: str,
        resource: Optional[MeteredResource] = None,
        period: AggregationPeriod = AggregationPeriod.DAILY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[UsageAggregation]:
        """
        Aggregate usage data for a time period.

        Args:
            user_id: User ID
            resource: Optional resource filter (None = all resources)
            period: Aggregation period
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)

        Returns:
            list[UsageAggregation]: Aggregated usage data
        """
        # Default date range
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        aggregations = []

        # Determine resources to aggregate
        resources = [resource] if resource else list(MeteredResource)

        for res in resources:
            agg = await self._aggregate_resource_usage(
                user_id=user_id,
                resource=res,
                period=period,
                start_date=start_date,
                end_date=end_date,
            )
            if agg:
                aggregations.append(agg)

        return aggregations

    async def _aggregate_resource_usage(
        self,
        user_id: str,
        resource: MeteredResource,
        period: AggregationPeriod,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[UsageAggregation]:
        """
        Aggregate usage for a specific resource.

        Args:
            user_id: User ID
            resource: Resource type
            period: Aggregation period
            start_date: Start date
            end_date: End date

        Returns:
            Optional[UsageAggregation]: Aggregated data or None if no usage
        """
        # Get events from Redis
        key = f"metering:events:{user_id}:{resource.value}"

        # Query by timestamp range
        start_score = start_date.timestamp()
        end_score = end_date.timestamp()

        events = self.redis.zrangebyscore(key, start_score, end_score)

        if not events:
            return None

        # Aggregate data
        total_quantity = 0
        total_cost = Decimal("0")
        event_count = len(events)

        for event_data in events:
            event = json.loads(event_data)
            total_quantity += event["quantity"]
            total_cost += Decimal(event["cost"])

        return UsageAggregation(
            user_id=user_id,
            resource=resource,
            period=period,
            period_start=start_date,
            period_end=end_date,
            total_quantity=total_quantity,
            total_cost=total_cost,
            event_count=event_count,
        )

    # =========================================================================
    # Quota Enforcement
    # =========================================================================

    async def check_quota(
        self,
        user_id: str,
        resource: MeteredResource,
        quantity: int,
        quota_limit: int,
        period: AggregationPeriod = AggregationPeriod.DAILY,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if usage would exceed quota.

        Args:
            user_id: User ID
            resource: Resource type
            quantity: Quantity to check
            quota_limit: Quota limit
            period: Period for quota check

        Returns:
            tuple[bool, Optional[str]]: (is_allowed, reason_if_denied)
        """
        # Get current usage for period
        current_usage = await self._get_current_period_usage(
            user_id=user_id, resource=resource, period=period
        )

        # Check if would exceed quota
        if current_usage + quantity > quota_limit:
            overage = (current_usage + quantity) - quota_limit
            return (
                False,
                f"Quota exceeded: {current_usage}/{quota_limit} used, "
                f"would exceed by {overage}",
            )

        return True, None

    async def _get_current_period_usage(
        self,
        user_id: str,
        resource: MeteredResource,
        period: AggregationPeriod,
    ) -> int:
        """
        Get current usage for the current period.

        Args:
            user_id: User ID
            resource: Resource type
            period: Period type

        Returns:
            int: Current usage
        """
        now = datetime.utcnow()

        # Determine key based on period
        if period == AggregationPeriod.HOURLY:
            key = f"metering:hourly:{user_id}:{resource.value}:{now.strftime('%Y-%m-%d-%H')}"
        elif period == AggregationPeriod.DAILY:
            key = f"metering:daily:{user_id}:{resource.value}:{now.strftime('%Y-%m-%d')}"
        elif period == AggregationPeriod.MONTHLY:
            key = f"metering:monthly:{user_id}:{resource.value}:{now.strftime('%Y-%m')}"
        else:
            # For weekly/yearly, calculate from events
            return await self._calculate_period_usage(user_id, resource, period)

        # Get counter from Redis
        usage = self.redis.get(key)
        return int(usage) if usage else 0

    async def _calculate_period_usage(
        self,
        user_id: str,
        resource: MeteredResource,
        period: AggregationPeriod,
    ) -> int:
        """
        Calculate usage for non-standard periods (weekly, yearly).

        Args:
            user_id: User ID
            resource: Resource type
            period: Period type

        Returns:
            int: Calculated usage
        """
        now = datetime.utcnow()

        # Determine date range
        if period == AggregationPeriod.WEEKLY:
            start_date = now - timedelta(days=7)
        elif period == AggregationPeriod.YEARLY:
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)

        # Aggregate from events
        agg = await self._aggregate_resource_usage(
            user_id=user_id,
            resource=resource,
            period=period,
            start_date=start_date,
            end_date=now,
        )

        return agg.total_quantity if agg else 0

    # =========================================================================
    # Overage Tracking
    # =========================================================================

    async def track_overage(
        self,
        user_id: str,
        resource: MeteredResource,
        quota_limit: int,
        actual_usage: int,
        period: AggregationPeriod = AggregationPeriod.DAILY,
    ) -> Optional[OverageAlert]:
        """
        Track and alert on quota overage.

        Args:
            user_id: User ID
            resource: Resource type
            quota_limit: Quota limit
            actual_usage: Actual usage
            period: Period type

        Returns:
            Optional[OverageAlert]: Alert if overage detected
        """
        if actual_usage <= quota_limit:
            return None

        overage_amount = actual_usage - quota_limit
        overage_percentage = (overage_amount / quota_limit) * 100

        # Determine severity
        if overage_percentage >= 100:
            severity = "emergency"
        elif overage_percentage >= 50:
            severity = "critical"
        else:
            severity = "warning"

        alert = OverageAlert(
            user_id=user_id,
            resource=resource,
            quota_limit=quota_limit,
            actual_usage=actual_usage,
            overage_amount=overage_amount,
            overage_percentage=overage_percentage,
            period=period,
            timestamp=datetime.utcnow(),
            severity=severity,
        )

        # Store alert in Redis
        await self._store_overage_alert(alert)

        logger.warning(
            f"Overage alert: user={user_id}, resource={resource.value}, "
            f"overage={overage_amount} ({overage_percentage:.1f}%), "
            f"severity={severity}"
        )

        return alert

    async def _store_overage_alert(self, alert: OverageAlert) -> None:
        """
        Store overage alert in Redis.

        Args:
            alert: Overage alert to store
        """
        key = f"metering:overage:{alert.user_id}:{alert.resource.value}"
        value = json.dumps(
            {
                "quota_limit": alert.quota_limit,
                "actual_usage": alert.actual_usage,
                "overage_amount": alert.overage_amount,
                "overage_percentage": alert.overage_percentage,
                "severity": alert.severity,
                "timestamp": alert.timestamp.isoformat(),
            }
        )

        self.redis.setex(key, 7 * 24 * 3600, value)  # 7 days expiration

    async def get_overage_alerts(
        self,
        user_id: str,
        resource: Optional[MeteredResource] = None,
    ) -> list[OverageAlert]:
        """
        Get overage alerts for a user.

        Args:
            user_id: User ID
            resource: Optional resource filter

        Returns:
            list[OverageAlert]: List of overage alerts
        """
        alerts = []

        resources = [resource] if resource else list(MeteredResource)

        for res in resources:
            key = f"metering:overage:{user_id}:{res.value}"
            alert_data = self.redis.get(key)

            if alert_data:
                data = json.loads(alert_data)
                alert = OverageAlert(
                    user_id=user_id,
                    resource=res,
                    quota_limit=data["quota_limit"],
                    actual_usage=data["actual_usage"],
                    overage_amount=data["overage_amount"],
                    overage_percentage=data["overage_percentage"],
                    period=AggregationPeriod.DAILY,  # Default
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    severity=data["severity"],
                )
                alerts.append(alert)

        return alerts

    # =========================================================================
    # Usage Reports
    # =========================================================================

    async def generate_usage_report(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_forecast: bool = False,
    ) -> UsageReport:
        """
        Generate comprehensive usage report.

        Args:
            user_id: User ID
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            include_forecast: Include usage forecast

        Returns:
            UsageReport: Comprehensive usage report
        """
        # Default date range
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Aggregate by resource
        by_resource = {}
        total_cost = Decimal("0")

        for resource in MeteredResource:
            agg = await self._aggregate_resource_usage(
                user_id=user_id,
                resource=resource,
                period=AggregationPeriod.DAILY,
                start_date=start_date,
                end_date=end_date,
            )

            if agg:
                by_resource[resource.value] = agg
                total_cost += agg.total_cost

        # Get overage alerts
        overages = await self.get_overage_alerts(user_id)

        # Generate forecast if requested
        forecasted_usage = None
        if include_forecast:
            # Forecast for the most used resource
            if by_resource:
                top_resource_value = max(
                    by_resource.items(), key=lambda x: x[1].total_quantity
                )[0]
                top_resource = MeteredResource(top_resource_value)
                forecasted_usage = await self.forecast_usage(
                    user_id=user_id,
                    resource=top_resource,
                    forecast_periods=7,  # 7 days ahead
                )

        # Aggregate by period (daily breakdown)
        by_period = await self._aggregate_by_daily_periods(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        return UsageReport(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            total_cost=total_cost,
            by_resource=by_resource,
            by_period=by_period,
            overages=overages,
            forecasted_usage=forecasted_usage,
        )

    async def _aggregate_by_daily_periods(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, UsageAggregation]:
        """
        Aggregate usage by daily periods.

        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date

        Returns:
            dict[str, UsageAggregation]: Usage by day
        """
        by_period = {}

        current = start_date
        while current <= end_date:
            day_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1) - timedelta(seconds=1)

            # Aggregate all resources for this day
            day_quantity = 0
            day_cost = Decimal("0")
            day_events = 0

            for resource in MeteredResource:
                agg = await self._aggregate_resource_usage(
                    user_id=user_id,
                    resource=resource,
                    period=AggregationPeriod.DAILY,
                    start_date=day_start,
                    end_date=day_end,
                )

                if agg:
                    day_quantity += agg.total_quantity
                    day_cost += agg.total_cost
                    day_events += agg.event_count

            if day_events > 0:
                by_period[day_start.strftime("%Y-%m-%d")] = UsageAggregation(
                    user_id=user_id,
                    resource=MeteredResource.API_READ,  # Placeholder
                    period=AggregationPeriod.DAILY,
                    period_start=day_start,
                    period_end=day_end,
                    total_quantity=day_quantity,
                    total_cost=day_cost,
                    event_count=day_events,
                )

            current += timedelta(days=1)

        return by_period

    # =========================================================================
    # Billing Integration
    # =========================================================================

    async def generate_billing_record(
        self,
        user_id: str,
        billing_period_start: datetime,
        billing_period_end: datetime,
        tax_rate: Decimal = Decimal("0.08"),  # 8% default
    ) -> BillingRecord:
        """
        Generate billing record for invoice.

        Args:
            user_id: User ID
            billing_period_start: Billing period start
            billing_period_end: Billing period end
            tax_rate: Tax rate (default: 8%)

        Returns:
            BillingRecord: Billing record with line items
        """
        line_items = []
        subtotal = Decimal("0")

        # Generate line items for each resource
        for resource in MeteredResource:
            agg = await self._aggregate_resource_usage(
                user_id=user_id,
                resource=resource,
                period=AggregationPeriod.MONTHLY,
                start_date=billing_period_start,
                end_date=billing_period_end,
            )

            if agg and agg.total_quantity > 0:
                line_items.append(
                    {
                        "resource": resource.value,
                        "description": f"{resource.value.replace('_', ' ').title()}",
                        "quantity": agg.total_quantity,
                        "unit_price": str(
                            agg.total_cost / agg.total_quantity
                        ),  # Average unit price
                        "total": str(agg.total_cost),
                    }
                )
                subtotal += agg.total_cost

        # Calculate taxes
        taxes = (subtotal * tax_rate).quantize(Decimal("0.01"))
        total = subtotal + taxes

        return BillingRecord(
            user_id=user_id,
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
            line_items=line_items,
            subtotal=subtotal,
            taxes=taxes,
            total=total,
        )

    async def export_billing_data(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        format: str = "json",
    ) -> dict[str, Any]:
        """
        Export billing data for external billing systems.

        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date
            format: Export format (json, csv, stripe, etc.)

        Returns:
            dict[str, Any]: Formatted billing data
        """
        billing_record = await self.generate_billing_record(
            user_id=user_id,
            billing_period_start=start_date,
            billing_period_end=end_date,
        )

        if format == "stripe":
            # Format for Stripe billing API
            return {
                "customer": user_id,
                "currency": billing_record.currency.lower(),
                "amount": int(
                    billing_record.total * 100
                ),  # Stripe uses cents
                "description": f"Usage from {start_date.date()} to {end_date.date()}",
                "metadata": {
                    "billing_period_start": billing_period_start.isoformat(),
                    "billing_period_end": billing_period_end.isoformat(),
                    "line_items_count": len(billing_record.line_items),
                },
                "line_items": billing_record.line_items,
            }
        else:
            # Default JSON format
            return {
                "user_id": billing_record.user_id,
                "billing_period": {
                    "start": billing_record.billing_period_start.isoformat(),
                    "end": billing_record.billing_period_end.isoformat(),
                },
                "line_items": billing_record.line_items,
                "subtotal": str(billing_record.subtotal),
                "taxes": str(billing_record.taxes),
                "total": str(billing_record.total),
                "currency": billing_record.currency,
            }

    # =========================================================================
    # Usage Forecasting
    # =========================================================================

    async def forecast_usage(
        self,
        user_id: str,
        resource: MeteredResource,
        forecast_periods: int = 7,
        confidence_level: float = 0.95,
    ) -> ForecastResult:
        """
        Forecast future usage using simple moving average (can be enhanced with ML).

        Args:
            user_id: User ID
            resource: Resource to forecast
            forecast_periods: Number of periods to forecast (days)
            confidence_level: Confidence level (default: 95%)

        Returns:
            ForecastResult: Forecast with confidence intervals
        """
        # Get historical data (last 30 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        historical_usage = []
        current = start_date

        while current <= end_date:
            day_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1) - timedelta(seconds=1)

            agg = await self._aggregate_resource_usage(
                user_id=user_id,
                resource=resource,
                period=AggregationPeriod.DAILY,
                start_date=day_start,
                end_date=day_end,
            )

            usage = agg.total_quantity if agg else 0
            historical_usage.append(usage)

            current += timedelta(days=1)

        # Calculate simple moving average
        if not historical_usage:
            predicted_usage = 0
            std_dev = 0
        else:
            predicted_usage = int(sum(historical_usage) / len(historical_usage))

            # Calculate standard deviation
            variance = sum(
                (x - predicted_usage) ** 2 for x in historical_usage
            ) / len(historical_usage)
            std_dev = int(variance**0.5)

        # Calculate confidence interval (using normal distribution approximation)
        # For 95% confidence, z-score is approximately 1.96
        z_score = 1.96 if confidence_level == 0.95 else 2.576  # 99% confidence

        margin_of_error = int(z_score * std_dev)
        confidence_interval_lower = max(0, predicted_usage - margin_of_error)
        confidence_interval_upper = predicted_usage + margin_of_error

        # Estimate model accuracy (R-squared approximation)
        if historical_usage:
            mean_usage = sum(historical_usage) / len(historical_usage)
            ss_tot = sum((x - mean_usage) ** 2 for x in historical_usage)
            ss_res = sum((x - predicted_usage) ** 2 for x in historical_usage)
            model_accuracy = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        else:
            model_accuracy = 0.0

        forecast_start = end_date + timedelta(days=1)
        forecast_end = forecast_start + timedelta(days=forecast_periods - 1)

        return ForecastResult(
            user_id=user_id,
            resource=resource,
            forecast_period=AggregationPeriod.DAILY,
            forecast_start=forecast_start,
            forecast_end=forecast_end,
            predicted_usage=predicted_usage * forecast_periods,
            confidence_interval_lower=confidence_interval_lower * forecast_periods,
            confidence_interval_upper=confidence_interval_upper * forecast_periods,
            confidence_level=confidence_level,
            model_accuracy=max(0.0, min(1.0, model_accuracy)),
            metadata={
                "historical_days": len(historical_usage),
                "average_daily_usage": predicted_usage,
                "std_dev": std_dev,
            },
        )

    async def get_usage_trends(
        self,
        user_id: str,
        resource: MeteredResource,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get usage trends and analytics.

        Args:
            user_id: User ID
            resource: Resource type
            days: Number of days to analyze

        Returns:
            dict[str, Any]: Trend analysis
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get daily usage
        daily_usage = []
        current = start_date

        while current <= end_date:
            day_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1) - timedelta(seconds=1)

            agg = await self._aggregate_resource_usage(
                user_id=user_id,
                resource=resource,
                period=AggregationPeriod.DAILY,
                start_date=day_start,
                end_date=day_end,
            )

            usage = agg.total_quantity if agg else 0
            daily_usage.append({"date": day_start.date().isoformat(), "usage": usage})

            current += timedelta(days=1)

        # Calculate statistics
        usage_values = [d["usage"] for d in daily_usage]

        if usage_values:
            avg_usage = sum(usage_values) / len(usage_values)
            max_usage = max(usage_values)
            min_usage = min(usage_values)

            # Calculate trend (simple linear regression slope)
            n = len(usage_values)
            sum_x = sum(range(n))
            sum_y = sum(usage_values)
            sum_xy = sum(i * y for i, y in enumerate(usage_values))
            sum_x2 = sum(i**2 for i in range(n))

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
            trend = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
        else:
            avg_usage = 0
            max_usage = 0
            min_usage = 0
            slope = 0
            trend = "no_data"

        return {
            "user_id": user_id,
            "resource": resource.value,
            "period_days": days,
            "daily_usage": daily_usage,
            "statistics": {
                "average": avg_usage,
                "maximum": max_usage,
                "minimum": min_usage,
                "total": sum(usage_values),
            },
            "trend": {
                "direction": trend,
                "slope": slope,
            },
        }
