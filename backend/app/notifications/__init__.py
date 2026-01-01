"""
Notification System for Schedule Alerts and Updates.

This package provides a comprehensive notification framework for the Residency
Scheduler application, supporting multiple delivery channels and notification types.

Architecture Overview
---------------------
The notification system is built on a queue-based architecture with the following
components:

1. **Channels** (channels.py): Delivery mechanisms for notifications
   - InAppChannel: Stores notifications in database for UI display
   - EmailChannel: Prepares email payloads for SMTP delivery via Celery
   - WebhookChannel: Sends JSON payloads to external systems (Slack, Teams, etc.)

2. **Templates** (notification_types.py, templates.py): Message templates
   - NotificationType enum: Defines available notification types
   - NotificationTemplate: Dataclass for rendering subject/body with variables
   - Template registry: Pre-configured templates for each notification type

3. **Service** (service.py): Core notification orchestration
   - NotificationService: Main class for sending, scheduling, and managing notifications
   - User preferences: Per-user channel and quiet hours configuration
   - Bulk sending: Efficient batch delivery to multiple recipients

4. **Tasks** (tasks.py): Celery background tasks for async delivery
   - send_email: SMTP delivery with retry logic and exponential backoff
   - send_webhook: HTTP POST delivery with retry logic
   - detect_leave_conflicts: Conflict detection after leave approval

Delivery Flow
-------------
1. Application code calls NotificationService.send_notification()
2. Service renders template with provided data
3. Service checks user preferences (enabled channels, quiet hours)
4. Service dispatches to each enabled channel
5. Channels queue async work via Celery tasks (email, webhook)
6. In-app notifications are stored directly in database

Supported Notification Types
----------------------------
- SCHEDULE_PUBLISHED: New schedule published (high priority)
- ASSIGNMENT_CHANGED: User's assignment modified (high priority)
- SHIFT_REMINDER_24H: 24-hour shift reminder (normal priority)
- SHIFT_REMINDER_1H: 1-hour shift reminder (high priority, in-app only)
- ACGME_WARNING: Compliance violation detected (high priority, all channels)
- ABSENCE_APPROVED: Leave request approved (normal priority)
- ABSENCE_REJECTED: Leave request rejected (normal priority)

Example Usage
-------------
::

    from app.db.session import get_db
    from app.notifications import (
        get_notification_service,
        NotificationType,
        notify_schedule_published,
        notify_acgme_warning,
    )

    # Get database session
    db = next(get_db())

    # Option 1: Use convenience functions
    await notify_schedule_published(
        db=db,
        recipient_ids=[user1_id, user2_id],
        period="January 2025",
        coverage_rate=95.5,
        total_assignments=120,
        violations_count=2,
        publisher_name="Dr. Smith",
    )

    # Option 2: Use service directly for more control
    service = get_notification_service(db)
    results = await service.send_notification(
        recipient_id=user_id,
        notification_type=NotificationType.ACGME_WARNING,
        data={
            "violation_type": "80-Hour Rule",
            "severity": "CRITICAL",
            "person_name": "Dr. Johnson",
            "violation_details": "Weekly hours exceeded 80-hour limit",
            "recommended_action": "Reduce scheduled shifts immediately",
        },
        channels=["in_app", "email", "webhook"],
    )

Configuration
-------------
Email delivery requires the following environment variables:
    - SMTP_HOST: SMTP server hostname
    - SMTP_PORT: SMTP server port (default: 587)
    - SMTP_USER: SMTP username
    - SMTP_PASSWORD: SMTP password
    - EMAIL_FROM: Default sender email address

Webhook delivery uses httpx with 30-second timeout and 3 retries with
exponential backoff.

Dependencies
------------
- Celery + Redis: Required for async email and webhook delivery
- SQLAlchemy: Database persistence for notifications and preferences
- Pydantic: Data validation for payloads and preferences
- httpx: HTTP client for webhook delivery
"""

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
from app.notifications.notification_types import (
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
