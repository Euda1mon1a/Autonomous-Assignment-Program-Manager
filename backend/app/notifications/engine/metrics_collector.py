"""Metrics collection for notification system."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class NotificationMetrics:
    """
    Collects and aggregates notification metrics.

    Metrics tracked:
    - Total notifications sent
    - Success/failure rates
    - Delivery latency
    - Channel performance
    - Type distribution
    - Priority distribution
    """

    def __init__(self):
        """Initialize metrics collector."""
        # Counters
        self._sent_count = 0
        self._failed_count = 0
        self._queued_count = 0
        self._deduplicated_count = 0
        self._rate_limited_count = 0

        # By notification type
        self._by_type = defaultdict(int)

        # By channel
        self._by_channel = defaultdict(lambda: {"sent": 0, "failed": 0})

        # By priority
        self._by_priority = defaultdict(int)

        # Latency tracking (in seconds)
        self._latencies: list[float] = []
        self._max_latencies = 1000  # Keep last 1000

        # Start time
        self._start_time = datetime.utcnow()

    def record_sent(
        self,
        notification_type: str,
        channel: str,
        priority: str,
        latency_seconds: float | None = None,
    ) -> None:
        """
        Record a sent notification.

        Args:
            notification_type: Type of notification
            channel: Channel used
            priority: Priority level
            latency_seconds: Time from creation to delivery
        """
        self._sent_count += 1
        self._by_type[notification_type] += 1
        self._by_channel[channel]["sent"] += 1
        self._by_priority[priority] += 1

        if latency_seconds is not None:
            self._latencies.append(latency_seconds)
            if len(self._latencies) > self._max_latencies:
                self._latencies = self._latencies[-self._max_latencies :]

    def record_failed(self, notification_type: str, channel: str) -> None:
        """
        Record a failed notification.

        Args:
            notification_type: Type of notification
            channel: Channel that failed
        """
        self._failed_count += 1
        self._by_channel[channel]["failed"] += 1

    def record_queued(self) -> None:
        """Record a queued notification."""
        self._queued_count += 1

    def record_deduplicated(self) -> None:
        """Record a deduplicated notification."""
        self._deduplicated_count += 1

    def record_rate_limited(self) -> None:
        """Record a rate-limited notification."""
        self._rate_limited_count += 1

    def get_summary(self) -> dict[str, Any]:
        """
        Get metrics summary.

        Returns:
            Dictionary of metrics
        """
        total = self._sent_count + self._failed_count
        success_rate = (self._sent_count / total * 100) if total > 0 else 0

        # Calculate latency statistics
        latency_stats = {}
        if self._latencies:
            latency_stats = {
                "min": min(self._latencies),
                "max": max(self._latencies),
                "avg": sum(self._latencies) / len(self._latencies),
                "p50": self._percentile(self._latencies, 50),
                "p95": self._percentile(self._latencies, 95),
                "p99": self._percentile(self._latencies, 99),
            }

        # Calculate uptime
        uptime_seconds = (datetime.utcnow() - self._start_time).total_seconds()

        return {
            "sent": self._sent_count,
            "failed": self._failed_count,
            "queued": self._queued_count,
            "deduplicated": self._deduplicated_count,
            "rate_limited": self._rate_limited_count,
            "success_rate_percent": round(success_rate, 2),
            "by_type": dict(self._by_type),
            "by_channel": dict(self._by_channel),
            "by_priority": dict(self._by_priority),
            "latency": latency_stats,
            "uptime_seconds": uptime_seconds,
        }

    def _percentile(self, values: list[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def reset(self) -> None:
        """Reset all metrics."""
        self._sent_count = 0
        self._failed_count = 0
        self._queued_count = 0
        self._deduplicated_count = 0
        self._rate_limited_count = 0
        self._by_type.clear()
        self._by_channel.clear()
        self._by_priority.clear()
        self._latencies.clear()
        self._start_time = datetime.utcnow()

        logger.info("Metrics reset")
