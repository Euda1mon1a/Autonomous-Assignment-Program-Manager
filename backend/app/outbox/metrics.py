"""Outbox Metrics Collection and Health Monitoring.

This module provides observability for the transactional outbox pattern through
two complementary classes:

1. **OutboxMetricsCollector**: Gathers point-in-time metrics about outbox state
   (message counts, latencies, throughput). Used by Celery task for periodic
   metric collection.

2. **OutboxMonitor**: Higher-level health analysis that detects anomalies and
   determines if alerts should be triggered.

Key Metrics
-----------
**Message Counts**:
- ``pending_count``: Messages waiting to be published (should be low)
- ``processing_count``: Messages currently being processed (usually 0-1)
- ``published_count``: Successfully published (moves to archive after 24h)
- ``failed_count``: Failed messages (includes retryable and dead letters)

**Latency Metrics**:
- ``avg_pending_age_seconds``: Average time messages wait in pending state
- ``max_pending_age_seconds``: Oldest pending message age (critical metric)

**Retry Metrics**:
- ``retryable_failed_count``: Failed messages that can still be retried
- ``dead_letter_count``: Messages that exceeded max retries (need investigation)
- ``avg_retry_count``: Average retries for failed messages

**Throughput Metrics**:
- ``published_last_hour``: Messages published in last hour
- ``published_last_24h``: Messages published in last 24 hours

Alert Thresholds
----------------
Default thresholds for health checks:

==========================  ===========  ==================
Metric                      Threshold    Severity
==========================  ===========  ==================
max_pending_age_seconds     > 300s       Warning
max_pending_age_seconds     > 600s       Error
dead_letter_count           > 0          Error
stuck_processing_count      > 0          Warning
pending_count               > 1000       Warning
published_last_hour         = 0*         Error
==========================  ===========  ==================

*Only alerts if there are pending messages (indicates relay is failing)

Integration Options
-------------------
These metrics can be exported to various monitoring systems:

**Prometheus** (recommended)::

    from prometheus_client import Gauge

    outbox_pending = Gauge('outbox_pending_count', 'Pending messages')
    outbox_latency = Gauge('outbox_max_pending_age_seconds', 'Max pending age')

    @celery_app.task
    def export_metrics():
        metrics = OutboxMetricsCollector(db).collect_metrics()
        outbox_pending.set(metrics['pending_count'])
        outbox_latency.set(metrics['max_pending_age_seconds'])

**Application Logs** (current implementation)::

    @celery_app.task
    def collect_outbox_metrics():
        metrics = OutboxMetricsCollector(db).collect_metrics()
        logger.info(f"Outbox metrics: {metrics}")

**External Alerting** (PagerDuty, Slack)::

    monitor = OutboxMonitor(db)
    if monitor.should_alert():
        send_alert(monitor.get_alert_message())
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.outbox.models import OutboxArchive, OutboxMessage, OutboxStatus

logger = logging.getLogger(__name__)


class OutboxMetricsCollector:
    """Collects point-in-time metrics about the outbox for monitoring.

    This class provides low-level metric collection methods that query the
    database for current outbox state. It's designed to be called periodically
    by a Celery task (e.g., every 5 minutes) to populate monitoring dashboards.

    Metric Categories
    -----------------
    **Message Counts**: How many messages are in each state
    **Latency Metrics**: How long messages wait before publishing
    **Retry Metrics**: Failure and retry statistics
    **Throughput Metrics**: Publishing rate over time
    **Archive Metrics**: Size of archived messages

    Performance Considerations
    --------------------------
    Most queries are simple COUNT/AVG aggregations with index support.
    The collect_metrics() method issues ~12 queries, which should complete
    in under 100ms with proper indexes.

    For high-volume systems, consider:
    - Caching metrics for 1-5 minutes
    - Using database-side views/materialized views
    - Sampling instead of full counts

    Thread Safety
    -------------
    Not thread-safe. Each thread should create its own instance with
    its own database session.

    Example:
        ::

            with session_scope() as db:
                collector = OutboxMetricsCollector(db)
                metrics = collector.collect_metrics()

                # Export to monitoring
                for name, value in metrics.items():
                    statsd.gauge(f'outbox.{name}', value)
    """

    def __init__(self, db: Session):
        """
        Initialize metrics collector.

        Args:
            db: Database session
        """
        self.db = db

    def collect_metrics(self) -> dict[str, Any]:
        """
        Collect all outbox metrics.

        Returns:
            dict: Dictionary of metric name -> value
        """
        return {
            # Message counts
            "pending_count": self.count_by_status(OutboxStatus.PENDING),
            "processing_count": self.count_by_status(OutboxStatus.PROCESSING),
            "published_count": self.count_by_status(OutboxStatus.PUBLISHED),
            "failed_count": self.count_by_status(OutboxStatus.FAILED),
            # Latency metrics
            "avg_pending_age_seconds": self.get_avg_pending_age(),
            "max_pending_age_seconds": self.get_max_pending_age(),
            "oldest_pending_message_id": self.get_oldest_pending_message_id(),
            # Retry metrics
            "retryable_failed_count": self.count_retryable_failed(),
            "dead_letter_count": self.count_dead_letters(),
            "avg_retry_count": self.get_avg_retry_count(),
            # Processing metrics
            "stuck_processing_count": self.count_stuck_processing(),
            # Throughput (last hour)
            "published_last_hour": self.count_published_last_period(hours=1),
            "published_last_24h": self.count_published_last_period(hours=24),
            # Archive metrics
            "archive_count": self.count_archived_messages(),
        }

    def count_by_status(self, status: OutboxStatus) -> int:
        """
        Count messages by status.

        Args:
            status: Message status to count

        Returns:
            int: Number of messages with given status
        """
        result = self.db.execute(
            select(func.count(OutboxMessage.id)).where(
                OutboxMessage.status == status.value
            )
        )
        return result.scalar_one() or 0

    def get_avg_pending_age(self) -> float:
        """
        Get average age of pending messages in seconds.

        This is a key latency metric - high values indicate messages
        are not being processed quickly enough.

        Returns:
            float: Average age in seconds (0 if no pending messages)
        """
        now = datetime.utcnow()

        result = self.db.execute(
            select(
                func.avg(func.extract("epoch", now - OutboxMessage.created_at))
            ).where(OutboxMessage.status == OutboxStatus.PENDING.value)
        )

        avg_age = result.scalar_one()
        return float(avg_age) if avg_age is not None else 0.0

    def get_max_pending_age(self) -> float:
        """
        Get age of oldest pending message in seconds.

        Returns:
            float: Max age in seconds (0 if no pending messages)
        """
        now = datetime.utcnow()

        result = self.db.execute(
            select(
                func.max(func.extract("epoch", now - OutboxMessage.created_at))
            ).where(OutboxMessage.status == OutboxStatus.PENDING.value)
        )

        max_age = result.scalar_one()
        return float(max_age) if max_age is not None else 0.0

    def get_oldest_pending_message_id(self) -> str | None:
        """
        Get ID of oldest pending message (for debugging).

        Returns:
            Optional[str]: Message ID or None
        """
        result = self.db.execute(
            select(OutboxMessage.id)
            .where(OutboxMessage.status == OutboxStatus.PENDING.value)
            .order_by(OutboxMessage.created_at.asc())
            .limit(1)
        )

        message_id = result.scalar_one_or_none()
        return str(message_id) if message_id else None

    def count_retryable_failed(self) -> int:
        """
        Count failed messages that can still be retried.

        Returns:
            int: Number of retryable failed messages
        """
        result = self.db.execute(
            select(func.count(OutboxMessage.id)).where(
                and_(
                    OutboxMessage.status == OutboxStatus.FAILED.value,
                    OutboxMessage.retry_count < OutboxMessage.max_retries,
                )
            )
        )
        return result.scalar_one() or 0

    def count_dead_letters(self) -> int:
        """
        Count messages that exceeded max retries (dead letter queue).

        These messages require manual intervention or investigation.

        Returns:
            int: Number of dead letter messages
        """
        result = self.db.execute(
            select(func.count(OutboxMessage.id)).where(
                and_(
                    OutboxMessage.status == OutboxStatus.FAILED.value,
                    OutboxMessage.retry_count >= OutboxMessage.max_retries,
                )
            )
        )
        return result.scalar_one() or 0

    def get_avg_retry_count(self) -> float:
        """
        Get average retry count across all failed messages.

        Returns:
            float: Average retry count
        """
        result = self.db.execute(
            select(func.avg(OutboxMessage.retry_count)).where(
                OutboxMessage.status == OutboxStatus.FAILED.value
            )
        )

        avg_retries = result.scalar_one()
        return float(avg_retries) if avg_retries is not None else 0.0

    def count_stuck_processing(
        self,
        timeout_minutes: int = 5,
    ) -> int:
        """
        Count messages stuck in PROCESSING state.

        These messages started processing but never completed,
        indicating a potential relay failure.

        Args:
            timeout_minutes: Minutes before considering a message stuck

        Returns:
            int: Number of stuck messages
        """
        cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)

        result = self.db.execute(
            select(func.count(OutboxMessage.id)).where(
                and_(
                    OutboxMessage.status == OutboxStatus.PROCESSING.value,
                    OutboxMessage.processing_started_at < cutoff,
                )
            )
        )
        return result.scalar_one() or 0

    def count_published_last_period(self, hours: int = 1) -> int:
        """
        Count messages published in the last N hours (throughput metric).

        Args:
            hours: Number of hours to look back

        Returns:
            int: Number of messages published in period
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        result = self.db.execute(
            select(func.count(OutboxMessage.id)).where(
                and_(
                    OutboxMessage.status == OutboxStatus.PUBLISHED.value,
                    OutboxMessage.published_at >= cutoff,
                )
            )
        )
        return result.scalar_one() or 0

    def count_archived_messages(self) -> int:
        """
        Count total archived messages.

        Returns:
            int: Number of archived messages
        """
        result = self.db.execute(select(func.count(OutboxArchive.id)))
        return result.scalar_one() or 0

    def get_messages_by_event_type(
        self,
        hours: int = 24,
    ) -> dict[str, int]:
        """
        Get message counts by event type for the last N hours.

        Useful for understanding event distribution and patterns.

        Args:
            hours: Number of hours to look back

        Returns:
            dict: Event type -> count mapping
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        result = self.db.execute(
            select(
                OutboxMessage.event_type,
                func.count(OutboxMessage.id).label("count"),
            )
            .where(OutboxMessage.created_at >= cutoff)
            .group_by(OutboxMessage.event_type)
        )

        return {row.event_type: row.count for row in result}

    def get_messages_by_aggregate_type(
        self,
        hours: int = 24,
    ) -> dict[str, int]:
        """
        Get message counts by aggregate type for the last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            dict: Aggregate type -> count mapping
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        result = self.db.execute(
            select(
                OutboxMessage.aggregate_type,
                func.count(OutboxMessage.id).label("count"),
            )
            .where(OutboxMessage.created_at >= cutoff)
            .group_by(OutboxMessage.aggregate_type)
        )

        return {row.aggregate_type: row.count for row in result}

    def get_processing_latency_stats(self) -> dict[str, float]:
        """
        Get processing latency statistics for published messages.

        Measures time from message creation to publication.

        Returns:
            dict: Latency statistics (avg, min, max in seconds)
        """
        result = self.db.execute(
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        OutboxMessage.published_at - OutboxMessage.created_at,
                    )
                ).label("avg_latency"),
                func.min(
                    func.extract(
                        "epoch",
                        OutboxMessage.published_at - OutboxMessage.created_at,
                    )
                ).label("min_latency"),
                func.max(
                    func.extract(
                        "epoch",
                        OutboxMessage.published_at - OutboxMessage.created_at,
                    )
                ).label("max_latency"),
            ).where(
                and_(
                    OutboxMessage.status == OutboxStatus.PUBLISHED.value,
                    OutboxMessage.published_at.is_not(None),
                )
            )
        )

        row = result.one_or_none()

        if row and row.avg_latency is not None:
            return {
                "avg_latency_seconds": float(row.avg_latency),
                "min_latency_seconds": float(row.min_latency),
                "max_latency_seconds": float(row.max_latency),
            }

        return {
            "avg_latency_seconds": 0.0,
            "min_latency_seconds": 0.0,
            "max_latency_seconds": 0.0,
        }

    def check_health(self) -> dict[str, Any]:
        """
        Perform health check on the outbox.

        Returns health status and any issues detected.

        Returns:
            dict: Health check results with status and issues
        """
        issues = []

        # Check for stuck processing messages
        stuck_count = self.count_stuck_processing(timeout_minutes=5)
        if stuck_count > 0:
            issues.append(f"{stuck_count} messages stuck in processing state")

        # Check for high dead letter count
        dead_letter_count = self.count_dead_letters()
        if dead_letter_count > 10:
            issues.append(f"{dead_letter_count} messages in dead letter queue")

        # Check for old pending messages
        max_age = self.get_max_pending_age()
        if max_age > 300:  # 5 minutes
            issues.append(
                f"Oldest pending message is {max_age:.0f}s old (threshold: 300s)"
            )

        # Check for high pending count
        pending_count = self.count_by_status(OutboxStatus.PENDING)
        if pending_count > 1000:
            issues.append(f"{pending_count} pending messages (threshold: 1000)")

        # Determine overall status
        if not issues:
            status = "healthy"
        elif len(issues) == 1:
            status = "warning"
        else:
            status = "unhealthy"

        return {
            "status": status,
            "issues": issues,
            "metrics": {
                "pending_count": pending_count,
                "stuck_processing_count": stuck_count,
                "dead_letter_count": dead_letter_count,
                "max_pending_age_seconds": max_age,
            },
        }


class OutboxMonitor:
    """Higher-level monitoring and alerting for the outbox.

    This class builds on OutboxMetricsCollector to provide actionable
    health analysis. It detects anomalies, determines alert severity,
    and generates human-readable alert messages.

    Use Cases
    ---------
    1. **Scheduled Health Checks**: Run periodically to detect issues
    2. **On-Demand Status**: Check health before critical operations
    3. **Alerting Integration**: Feed into PagerDuty, Slack, etc.

    Anomaly Detection
    -----------------
    The monitor detects these anomaly types:

    - ``high_latency``: Messages waiting too long to be published
    - ``dead_letters``: Messages that exhausted retry attempts
    - ``stuck_processing``: Messages that never completed processing
    - ``low_throughput``: No publishing despite pending messages

    Alert Severity
    --------------
    - ``warning``: Single issue detected, investigate when convenient
    - ``error``: Critical issue requiring immediate attention

    Example:
        ::

            # In a health check endpoint
            @app.get("/health/outbox")
            def outbox_health(db: Session = Depends(get_db)):
                monitor = OutboxMonitor(db)
                anomalies = monitor.detect_anomalies()

                if monitor.should_alert():
                    # Trigger external alert
                    send_pagerduty_alert(monitor.get_alert_message())

                return {
                    "healthy": len(anomalies) == 0,
                    "anomalies": anomalies,
                }

            # In a Celery task
            @celery_app.task
            def check_outbox_health():
                with session_scope() as db:
                    monitor = OutboxMonitor(db)
                    if monitor.should_alert():
                        slack_notify(monitor.get_alert_message())
    """

    def __init__(self, db: Session):
        """Initialize outbox monitor.

        Args:
            db: Database session for metric queries
        """
        self.db = db
        self.collector = OutboxMetricsCollector(db)

    def detect_anomalies(self) -> list[dict[str, Any]]:
        """
        Detect anomalies in outbox behavior.

        Returns:
            list: List of detected anomalies with details
        """
        anomalies = []

        metrics = self.collector.collect_metrics()

        # Anomaly: High pending message age
        if metrics["max_pending_age_seconds"] > 600:  # 10 minutes
            anomalies.append(
                {
                    "type": "high_latency",
                    "severity": "warning",
                    "message": (
                        f"High pending message age: "
                        f"{metrics['max_pending_age_seconds']:.0f}s"
                    ),
                    "value": metrics["max_pending_age_seconds"],
                }
            )

        # Anomaly: Growing dead letter queue
        if metrics["dead_letter_count"] > 0:
            anomalies.append(
                {
                    "type": "dead_letters",
                    "severity": "error",
                    "message": f"Dead letter queue has {metrics['dead_letter_count']} messages",
                    "value": metrics["dead_letter_count"],
                }
            )

        # Anomaly: Stuck processing messages
        if metrics["stuck_processing_count"] > 0:
            anomalies.append(
                {
                    "type": "stuck_processing",
                    "severity": "warning",
                    "message": f"{metrics['stuck_processing_count']} messages stuck processing",
                    "value": metrics["stuck_processing_count"],
                }
            )

        # Anomaly: Low throughput
        if metrics["published_last_hour"] == 0 and metrics["pending_count"] > 0:
            anomalies.append(
                {
                    "type": "low_throughput",
                    "severity": "error",
                    "message": "No messages published in last hour despite pending messages",
                    "pending_count": metrics["pending_count"],
                }
            )

        return anomalies

    def should_alert(self) -> bool:
        """
        Determine if an alert should be triggered.

        Returns:
            bool: True if alert should be sent
        """
        anomalies = self.detect_anomalies()

        # Alert if any error-level anomalies
        return any(a["severity"] == "error" for a in anomalies)

    def get_alert_message(self) -> str:
        """
        Get formatted alert message for monitoring systems.

        Returns:
            str: Alert message
        """
        anomalies = self.detect_anomalies()

        if not anomalies:
            return "Outbox is healthy"

        lines = ["Outbox anomalies detected:"]
        for anomaly in anomalies:
            lines.append(f"- [{anomaly['severity'].upper()}] {anomaly['message']}")

        return "\n".join(lines)
