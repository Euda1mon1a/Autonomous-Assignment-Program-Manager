"""Advanced notification filtering."""

from datetime import datetime, time
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.notifications.notification_types import NotificationType

logger = get_logger(__name__)


class NotificationFilter:
    """
    Filters notifications based on complex rules.

    Filter types:
    - Time-based: No notifications during specific hours
    - Frequency: Limit notifications per timeframe
    - Content: Filter based on data content
    - User status: Filter based on user attributes
    """

    def __init__(self):
        """Initialize filter."""
        # User-specific filters
        self._user_filters: dict[UUID, dict[str, Any]] = {}

    def should_filter(
        self,
        recipient_id: UUID,
        notification_type: NotificationType,
        data: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """
        Check if notification should be filtered.

        Args:
            recipient_id: Recipient UUID
            notification_type: Type of notification
            data: Notification data

        Returns:
            Tuple of (should_filter, reason)
        """
        # Time-based filter
        if self._is_in_do_not_disturb(recipient_id):
            # Allow critical notifications
            if notification_type == NotificationType.ACGME_WARNING:
                return False, None
            return True, "Do not disturb hours"

        # Content-based filter
        if self._is_content_filtered(recipient_id, data):
            return True, "Content filter"

        return False, None

    def _is_in_do_not_disturb(self, recipient_id: UUID) -> bool:
        """Check if current time is in do-not-disturb hours."""
        if recipient_id not in self._user_filters:
            return False

        filters = self._user_filters[recipient_id]
        dnd_start = filters.get("dnd_start")
        dnd_end = filters.get("dnd_end")

        if not dnd_start or not dnd_end:
            return False

        current_time = datetime.utcnow().time()
        return dnd_start <= current_time < dnd_end

    def _is_content_filtered(self, recipient_id: UUID, data: dict[str, Any]) -> bool:
        """Check if content matches filter rules."""
        if recipient_id not in self._user_filters:
            return False

        filters = self._user_filters[recipient_id]
        content_filters = filters.get("content_filters", [])

        for content_filter in content_filters:
            field = content_filter["field"]
            value = content_filter["value"]

            if field in data and data[field] == value:
                return True

        return False

    def add_user_filter(
        self,
        recipient_id: UUID,
        dnd_start: time | None = None,
        dnd_end: time | None = None,
        content_filters: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add filters for a user."""
        self._user_filters[recipient_id] = {
            "dnd_start": dnd_start,
            "dnd_end": dnd_end,
            "content_filters": content_filters or [],
        }

        logger.info("Added filters for user %s", recipient_id)

    def remove_user_filter(self, recipient_id: UUID) -> None:
        """Remove filters for a user."""
        if recipient_id in self._user_filters:
            del self._user_filters[recipient_id]
            logger.info("Removed filters for user %s", recipient_id)
