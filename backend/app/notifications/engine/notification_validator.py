"""Validation for notification payloads."""

from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.notifications.notification_types import NotificationType

logger = get_logger(__name__)


class ValidationError(Exception):
    """Notification validation error."""

    pass


class NotificationValidator:
    """
    Validates notification payloads before sending.

    Validation checks:
    - Required fields present
    - Data types correct
    - Required template variables present
    - Recipient valid
    - Channel valid
    """

    # Required data fields by notification type
    REQUIRED_FIELDS = {
        NotificationType.SCHEDULE_PUBLISHED: [
            "period",
            "coverage_rate",
            "total_assignments",
        ],
        NotificationType.ASSIGNMENT_CHANGED: [
            "rotation_name",
            "block_name",
            "start_date",
        ],
        NotificationType.ACGME_WARNING: [
            "violation_type",
            "severity",
            "violation_details",
        ],
    }

    VALID_CHANNELS = ["in_app", "email", "sms", "webhook"]

    def validate(
        self,
        recipient_id: UUID,
        notification_type: NotificationType,
        data: dict[str, Any],
        channels: list[str],
    ) -> None:
        """
        Validate notification.

        Args:
            recipient_id: Recipient UUID
            notification_type: Type of notification
            data: Notification data
            channels: Channels to use

        Raises:
            ValidationError: If validation fails
        """
        # Validate recipient
        if not recipient_id:
            raise ValidationError("Recipient ID required")

        # Validate channels
        for channel in channels:
            if channel not in self.VALID_CHANNELS:
                raise ValidationError(f"Invalid channel: {channel}")

        # Validate required fields
        required = self.REQUIRED_FIELDS.get(notification_type, [])
        missing = [field for field in required if field not in data]

        if missing:
            raise ValidationError(f"Missing required fields: {missing}")

        logger.debug("Notification validated successfully")
