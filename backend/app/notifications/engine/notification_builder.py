"""Builder pattern for constructing notifications."""

from typing import Any
from uuid import UUID

from app.notifications.channels import NotificationPayload
from app.notifications.notification_types import NotificationType, render_notification


class NotificationBuilder:
    """
    Builder for creating notification payloads.

    Provides a fluent interface for constructing notifications
    with validation and defaults.
    """

    def __init__(self):
        """Initialize builder."""
        self._recipient_id: UUID | None = None
        self._notification_type: NotificationType | None = None
        self._data: dict[str, Any] = {}
        self._priority: str = "normal"
        self._channels: list[str] = ["in_app"]

    def recipient(self, recipient_id: UUID) -> "NotificationBuilder":
        """Set recipient ID."""
        self._recipient_id = recipient_id
        return self

    def notification_type(self, ntype: NotificationType) -> "NotificationBuilder":
        """Set notification type."""
        self._notification_type = ntype
        return self

    def data(self, **kwargs) -> "NotificationBuilder":
        """Set notification data."""
        self._data.update(kwargs)
        return self

    def priority(self, priority: str) -> "NotificationBuilder":
        """Set priority level."""
        self._priority = priority
        return self

    def channels(self, *channels: str) -> "NotificationBuilder":
        """Set delivery channels."""
        self._channels = list(channels)
        return self

    def build(self) -> NotificationPayload:
        """
        Build the notification payload.

        Returns:
            NotificationPayload

        Raises:
            ValueError: If required fields missing
        """
        if not self._recipient_id:
            raise ValueError("Recipient ID required")

        if not self._notification_type:
            raise ValueError("Notification type required")

        # Render template
        rendered = render_notification(self._notification_type, self._data)
        if not rendered:
            raise ValueError(f"Template not found: {self._notification_type}")

        return NotificationPayload(
            recipient_id=self._recipient_id,
            notification_type=self._notification_type.value,
            subject=rendered["subject"],
            body=rendered["body"],
            data=self._data,
            priority=self._priority,
        )
