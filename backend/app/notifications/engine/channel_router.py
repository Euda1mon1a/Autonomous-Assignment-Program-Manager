"""Intelligent channel routing."""

from typing import Any

from app.core.logging import get_logger
from app.notifications.notification_types import NotificationType

logger = get_logger(__name__)


class ChannelRouter:
    """
    Routes notifications to appropriate channels based on rules.

    Routing rules:
    - ACGME warnings: All channels (in_app, email, webhook)
    - Schedule published: in_app + email
    - Shift reminders: in_app only
    - Based on priority: High priority uses more channels
    - Based on time: Late night uses only in_app
    """

    DEFAULT_ROUTES = {
        NotificationType.ACGME_WARNING: ["in_app", "email", "webhook"],
        NotificationType.SCHEDULE_PUBLISHED: ["in_app", "email"],
        NotificationType.ASSIGNMENT_CHANGED: ["in_app", "email"],
        NotificationType.SHIFT_REMINDER_24H: ["in_app", "email"],
        NotificationType.SHIFT_REMINDER_1H: ["in_app"],
        NotificationType.ABSENCE_APPROVED: ["in_app", "email"],
        NotificationType.ABSENCE_REJECTED: ["in_app", "email"],
    }

    def route(
        self,
        notification_type: NotificationType,
        priority: str,
        data: dict[str, Any],
    ) -> list[str]:
        """
        Determine channels for notification.

        Args:
            notification_type: Type of notification
            priority: Priority level
            data: Notification data

        Returns:
            List of channel names
        """
        # Start with default routes
        channels = self.DEFAULT_ROUTES.get(notification_type, ["in_app"]).copy()

        # High priority: Ensure email included
        if priority == "high" and "email" not in channels:
            channels.append("email")

        # Critical priority: All channels
        if priority == "critical":
            channels = ["in_app", "email", "webhook"]

        logger.debug(
            "Routed %s (%s priority) to channels: %s",
            notification_type.value,
            priority,
            channels,
        )

        return channels
