"""
Prometheus Metrics Package.

Centralized metrics collection for the Residency Scheduler application.

This package provides:
- Prometheus registry and metric definitions
- Custom metric collectors for system resources
- Request metrics middleware
- Metrics endpoint for Prometheus scraping

Metrics Categories:
- HTTP: Request latency, count, active connections
- Database: Query duration, connection pool stats
- Cache: Hit/miss ratios, operation latencies
- Background Tasks: Task duration, queue depth
- Application: Schedule generation, ACGME compliance
- System: CPU, memory, disk usage
- Errors: Error rates by type and endpoint

Usage:
    from app.core.metrics import metrics, get_metrics

    # Record custom metric
    metrics.schedule_generation_duration.labels(algorithm="cp_sat").observe(12.5)

    # Use context manager for timing
    with metrics.time_database_query("SELECT"):
        result = await db.execute(query)
"""

from app.core.metrics.prometheus import (
    MetricsRegistry,
    get_metrics,
    metrics,
)

__all__ = [
    "MetricsRegistry",
    "get_metrics",
    "metrics",
]
