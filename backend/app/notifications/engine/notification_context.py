"""Notification context manager."""

from contextvars import ContextVar
from typing import Any
from uuid import UUID

# Context variables for notification tracking
current_notification_id: ContextVar[UUID | None] = ContextVar(
    "current_notification_id", default=None
)
current_recipient_id: ContextVar[UUID | None] = ContextVar(
    "current_recipient_id", default=None
)
notification_metadata: ContextVar[dict[str, Any]] = ContextVar(
    "notification_metadata", default_factory=dict
)


class NotificationContext:
    """
    Context manager for notification processing.

    Provides context variables for tracking notification state
    throughout the processing pipeline.
    """

    def __init__(
        self,
        notification_id: UUID,
        recipient_id: UUID,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize notification context.

        Args:
            notification_id: Notification UUID
            recipient_id: Recipient UUID
            metadata: Optional metadata
        """
        self.notification_id = notification_id
        self.recipient_id = recipient_id
        self.metadata = metadata or {}

        self._notification_token = None
        self._recipient_token = None
        self._metadata_token = None

    def __enter__(self):
        """Enter context."""
        self._notification_token = current_notification_id.set(self.notification_id)
        self._recipient_token = current_recipient_id.set(self.recipient_id)
        self._metadata_token = notification_metadata.set(self.metadata)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        if self._notification_token:
            current_notification_id.reset(self._notification_token)
        if self._recipient_token:
            current_recipient_id.reset(self._recipient_token)
        if self._metadata_token:
            notification_metadata.reset(self._metadata_token)


def get_current_notification_id() -> UUID | None:
    """Get current notification ID from context."""
    return current_notification_id.get()


def get_current_recipient_id() -> UUID | None:
    """Get current recipient ID from context."""
    return current_recipient_id.get()


def get_notification_metadata() -> dict[str, Any]:
    """Get notification metadata from context."""
    return notification_metadata.get()
