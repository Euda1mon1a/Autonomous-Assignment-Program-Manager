"""Email activity logging."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailEventType(str, Enum):
    """Email event types."""

    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"
    UNSUBSCRIBED = "unsubscribed"
    COMPLAINED = "complained"


class EmailLogEntry(BaseModel):
    """Email log entry."""

    id: UUID = Field(default_factory=uuid4)
    message_id: str
    recipient: str
    event_type: EmailEventType
    subject: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmailLogger:
    """
    Logs all email activity for audit and debugging.

    Features:
    - Complete email lifecycle tracking
    - Searchable logs
    - Export to CSV/JSON
    - Analytics and reporting
    """

    def __init__(self, max_entries: int = 10000):
        """
        Initialize email logger.

        Args:
            max_entries: Maximum log entries to keep
        """
        self._logs: list[EmailLogEntry] = []
        self._max_entries = max_entries

    def log(
        self,
        message_id: str,
        recipient: str,
        event_type: EmailEventType,
        subject: str,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        """
        Log an email event.

        Args:
            message_id: Email message ID
            recipient: Recipient email
            event_type: Type of event
            subject: Email subject
            metadata: Additional metadata

        Returns:
            Log entry ID
        """
        entry = EmailLogEntry(
            message_id=message_id,
            recipient=recipient,
            event_type=event_type,
            subject=subject,
            metadata=metadata or {},
        )

        self._logs.append(entry)

        # Trim if exceeds max
        if len(self._logs) > self._max_entries:
            self._logs = self._logs[-self._max_entries:]

        logger.debug(
            "Logged email event: %s - %s (%s)",
            event_type.value,
            message_id,
            recipient,
        )

        return entry.id

    def get_logs(
        self,
        message_id: str | None = None,
        recipient: str | None = None,
        event_type: EmailEventType | None = None,
        limit: int = 100,
    ) -> list[EmailLogEntry]:
        """
        Get logs matching criteria.

        Args:
            message_id: Filter by message ID
            recipient: Filter by recipient
            event_type: Filter by event type
            limit: Maximum entries to return

        Returns:
            List of log entries
        """
        logs = self._logs

        if message_id:
            logs = [entry for entry in logs if entry.message_id == message_id]

        if recipient:
            logs = [entry for entry in logs if entry.recipient == recipient]

        if event_type:
            logs = [entry for entry in logs if entry.event_type == event_type]

        # Sort by timestamp (most recent first)
        logs = sorted(logs, key=lambda e: e.timestamp, reverse=True)

        return logs[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """Get email statistics."""
        by_event = {}
        for entry in self._logs:
            event = entry.event_type.value
            by_event[event] = by_event.get(event, 0) + 1

        return {
            "total_events": len(self._logs),
            "by_event_type": by_event,
        }
