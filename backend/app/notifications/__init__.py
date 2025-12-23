"""Notification system for schedule alerts and updates."""

from sqlalchemy.orm import Session

from app.notifications.channels import (
    AVAILABLE_CHANNELS,
    DeliveryResult,
    EmailChannel,
    InAppChannel,
    NotificationChannel,
    NotificationPayload,
    WebhookChannel,
    get_channel,
)
from app.notifications.service import (
    NotificationPreferences,
    NotificationService,
    ScheduledNotification,
    notify_acgme_warning,
    notify_schedule_published,
)
from app.notifications.templates import (
    NOTIFICATION_TEMPLATES,
    NotificationTemplate,
    NotificationType,
    get_template,
    render_notification,
)

__all__ = [
    # Service
    "NotificationService",
    "NotificationPreferences",
    "ScheduledNotification",
    "get_notification_service",
    "notify_schedule_published",
    "notify_acgme_warning",
    # Templates
    "NotificationType",
    "NotificationTemplate",
    "get_template",
    "render_notification",
    "NOTIFICATION_TEMPLATES",
    # Channels
    "NotificationChannel",
    "NotificationPayload",
    "DeliveryResult",
    "InAppChannel",
    "EmailChannel",
    "WebhookChannel",
    "get_channel",
    "AVAILABLE_CHANNELS",
]


def get_notification_service(db: Session) -> NotificationService:
    """
    Factory function to create a NotificationService instance.

    Args:
        db: Database session for the service to use

    Returns:
        Configured NotificationService instance

    Example:
        ```python
        from app.db.session import get_db
        from app.notifications import get_notification_service

        db = next(get_db())
        notification_service = get_notification_service(db)

        # Send a notification
        await notification_service.send_notification(
            recipient_id=user_id,
            notification_type=NotificationType.SCHEDULE_PUBLISHED,
            data={
                "period": "January 2025",
                "coverage_rate": "95.5",
                "total_assignments": 120,
                "violations_count": 2,
                "publisher_name": "Dr. Smith",
                "published_at": "2025-01-15 10:30:00 UTC"
            }
        )
        ```
    """
    return NotificationService(db)
