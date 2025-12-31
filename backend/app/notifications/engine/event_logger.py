"""Event logging for notification audit trails."""

import json
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class NotificationEventType(str, Enum):
    """Types of notification events."""

    CREATED = "created"
    QUEUED = "queued"
    DEQUEUED = "dequeued"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRIED = "retried"
    DEDUPLICATED = "deduplicated"
    RATE_LIMITED = "rate_limited"
    BATCHED = "batched"
    READ = "read"
    DELETED = "deleted"


class NotificationEvent(BaseModel):
    """
    Represents a notification lifecycle event.

    Attributes:
        id: Unique event ID
        notification_id: ID of notification
        event_type: Type of event
        channel: Channel involved (if applicable)
        recipient_id: Recipient UUID
        metadata: Additional event data
        timestamp: When event occurred
    """

    id: UUID = Field(default_factory=uuid4)
    notification_id: UUID
    event_type: NotificationEventType
    channel: str | None = None
    recipient_id: UUID
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NotificationEventLogger:
    """
    Logs notification lifecycle events for audit trails.

    Features:
    - Complete audit trail of all notification events
    - Queryable event log
    - Statistics and analytics
    - Compliance reporting
    """

    def __init__(self, max_events: int = 10000):
        """
        Initialize event logger.

        Args:
            max_events: Maximum events to keep in memory
        """
        self._events: list[NotificationEvent] = []
        self._max_events = max_events

    def log_event(
        self,
        notification_id: UUID,
        event_type: NotificationEventType,
        recipient_id: UUID,
        channel: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        """
        Log a notification event.

        Args:
            notification_id: ID of notification
            event_type: Type of event
            recipient_id: Recipient UUID
            channel: Channel involved
            metadata: Additional event data

        Returns:
            Event ID
        """
        event = NotificationEvent(
            notification_id=notification_id,
            event_type=event_type,
            recipient_id=recipient_id,
            channel=channel,
            metadata=metadata or {},
        )

        self._events.append(event)

        # Trim if exceeds max
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events :]

        logger.debug(
            "Logged event: %s for notification %s (channel: %s)",
            event_type.value,
            notification_id,
            channel or "N/A",
        )

        return event.id

    def get_events(
        self,
        notification_id: UUID | None = None,
        recipient_id: UUID | None = None,
        event_type: NotificationEventType | None = None,
        limit: int = 100,
    ) -> list[NotificationEvent]:
        """
        Get events matching criteria.

        Args:
            notification_id: Filter by notification
            recipient_id: Filter by recipient
            event_type: Filter by event type
            limit: Maximum events to return

        Returns:
            List of events
        """
        events = self._events

        if notification_id:
            events = [e for e in events if e.notification_id == notification_id]

        if recipient_id:
            events = [e for e in events if e.recipient_id == recipient_id]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        # Return most recent first
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)

        return events[:limit]

    def get_timeline(self, notification_id: UUID) -> list[dict[str, Any]]:
        """
        Get complete timeline for a notification.

        Args:
            notification_id: ID of notification

        Returns:
            List of timeline events
        """
        events = self.get_events(notification_id=notification_id)

        return [
            {
                "event_type": e.event_type.value,
                "channel": e.channel,
                "timestamp": e.timestamp.isoformat(),
                "metadata": e.metadata,
            }
            for e in events
        ]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get event statistics.

        Returns:
            Dictionary of statistics
        """
        by_type = {}
        by_channel = {}

        for event in self._events:
            # Count by type
            if event.event_type.value not in by_type:
                by_type[event.event_type.value] = 0
            by_type[event.event_type.value] += 1

            # Count by channel
            if event.channel:
                if event.channel not in by_channel:
                    by_channel[event.channel] = 0
                by_channel[event.channel] += 1

        return {
            "total_events": len(self._events),
            "by_type": by_type,
            "by_channel": by_channel,
        }

    def export_events(self, filepath: str) -> None:
        """
        Export events to JSON file.

        Args:
            filepath: Path to export file
        """
        events_data = [
            {
                "id": str(e.id),
                "notification_id": str(e.notification_id),
                "event_type": e.event_type.value,
                "channel": e.channel,
                "recipient_id": str(e.recipient_id),
                "metadata": e.metadata,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in self._events
        ]

        with open(filepath, "w") as f:
            json.dump(events_data, f, indent=2)

        logger.info("Exported %d events to %s", len(self._events), filepath)

    def clear_old_events(self, days: int = 30) -> int:
        """
        Clear events older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of events cleared
        """
        cutoff = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)

        old_count = len(self._events)
        self._events = [
            e for e in self._events if e.timestamp.timestamp() >= cutoff
        ]
        new_count = len(self._events)

        cleared = old_count - new_count
        if cleared > 0:
            logger.info("Cleared %d events older than %d days", cleared, days)

        return cleared
