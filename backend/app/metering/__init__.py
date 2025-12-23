"""
Usage metering system for the Residency Scheduler.

This module provides comprehensive usage tracking and metering capabilities
for billing, analytics, and capacity planning. It complements the quota
system with detailed event tracking, aggregation, and forecasting.

Key Components:
    - MeteringService: Main service for recording and analyzing usage
    - MeteredResource: Resource type definitions
    - UsageEvent: Individual usage event tracking
    - UsageAggregator: Time-based usage aggregation
    - BillingIntegration: Hooks for billing systems
    - UsageForecaster: ML-based usage forecasting

Usage:
    from app.metering import MeteringService, MeteredResource

    # Initialize service
    metering = MeteringService(db, redis_client)

    # Record usage
    await metering.record_event(
        user_id="user-123",
        resource=MeteredResource.SCHEDULE_GENERATION,
        quantity=1,
        metadata={"complexity": "high"}
    )

    # Get usage report
    report = await metering.generate_usage_report(
        user_id="user-123",
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31)
    )
"""

from app.metering.service import (
    AggregationPeriod,
    BillingRecord,
    ForecastResult,
    MeteredResource,
    MeteringService,
    OverageAlert,
    UsageAggregation,
    UsageEvent,
    UsageReport,
)

__all__ = [
    "MeteringService",
    "MeteredResource",
    "UsageEvent",
    "UsageAggregation",
    "UsageReport",
    "BillingRecord",
    "ForecastResult",
    "OverageAlert",
    "AggregationPeriod",
]
