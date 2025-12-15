"""Core notification service for schedule alerts and updates."""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.notifications.templates import (
    NotificationType,
    get_template,
    render_notification,
)
from app.notifications.channels import (
    NotificationChannel,
    NotificationPayload,
    DeliveryResult,
    get_channel,
)


class ScheduledNotification(BaseModel):
    """
    A notification scheduled for future delivery.

    Attributes:
        id: Unique identifier
        recipient_id: UUID of the recipient
        notification_type: Type of notification
        data: Data for template rendering
        send_at: When to send the notification
        status: Status (pending, sent, failed)
        created_at: When the notification was scheduled
    """
    id: UUID = Field(default_factory=uuid.uuid4)
    recipient_id: UUID
    notification_type: NotificationType
    data: Dict[str, Any]
    send_at: datetime
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationPreferences(BaseModel):
    """
    User notification preferences.

    Attributes:
        user_id: UUID of the user
        enabled_channels: List of enabled channels
        notification_types: Dict of notification type to enabled status
        quiet_hours_start: Start of quiet hours (no notifications)
        quiet_hours_end: End of quiet hours
    """
    user_id: UUID
    enabled_channels: List[str] = ["in_app", "email"]
    notification_types: Dict[str, bool] = Field(
        default_factory=lambda: {
            NotificationType.SCHEDULE_PUBLISHED.value: True,
            NotificationType.ASSIGNMENT_CHANGED.value: True,
            NotificationType.SHIFT_REMINDER_24H.value: True,
            NotificationType.SHIFT_REMINDER_1H.value: True,
            NotificationType.ACGME_WARNING.value: True,
            NotificationType.ABSENCE_APPROVED.value: True,
            NotificationType.ABSENCE_REJECTED.value: True,
        }
    )
    quiet_hours_start: Optional[int] = None  # Hour (0-23)
    quiet_hours_end: Optional[int] = None  # Hour (0-23)


class NotificationService:
    """
    Core notification service for managing schedule alerts and updates.

    This service provides a queue-based architecture for sending notifications
    through multiple channels (in-app, email, webhook) with support for
    immediate, bulk, and scheduled delivery.
    """

    def __init__(self, db: Session):
        """
        Initialize notification service.

        Args:
            db: Database session for persistence
        """
        self.db = db
        self._scheduled_queue: List[ScheduledNotification] = []

    async def send_notification(
        self,
        recipient_id: UUID,
        notification_type: NotificationType,
        data: Dict[str, Any],
        channels: Optional[List[str]] = None
    ) -> List[DeliveryResult]:
        """
        Send a single notification immediately.

        Args:
            recipient_id: UUID of the notification recipient
            notification_type: Type of notification to send
            data: Data dictionary for template rendering
            channels: Optional list of specific channels to use

        Returns:
            List of DeliveryResult objects for each channel
        """
        # Render the notification template
        rendered = render_notification(notification_type, data)
        if not rendered:
            return [DeliveryResult(
                success=False,
                channel="template",
                message=f"Template not found for type: {notification_type}"
            )]

        # Determine which channels to use
        target_channels = channels or rendered.get("channels", ["in_app"])

        # Check user preferences (TODO: load from database)
        # preferences = self._get_user_preferences(recipient_id)
        # if not self._should_send_notification(preferences, notification_type):
        #     return []

        # Create notification payload
        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type=notification_type.value,
            subject=rendered["subject"],
            body=rendered["body"],
            data=data,
            priority=rendered.get("priority", "normal"),
        )

        # Deliver through each channel
        results = []
        for channel_name in target_channels:
            channel = get_channel(channel_name)
            if channel:
                result = await channel.deliver(payload, self.db)
                results.append(result)
            else:
                results.append(DeliveryResult(
                    success=False,
                    channel=channel_name,
                    message=f"Channel not found: {channel_name}"
                ))

        return results

    async def send_bulk(
        self,
        recipient_ids: List[UUID],
        notification_type: NotificationType,
        data: Dict[str, Any],
        channels: Optional[List[str]] = None
    ) -> Dict[str, List[DeliveryResult]]:
        """
        Send the same notification to multiple recipients.

        Args:
            recipient_ids: List of recipient UUIDs
            notification_type: Type of notification to send
            data: Data dictionary for template rendering
            channels: Optional list of specific channels to use

        Returns:
            Dictionary mapping recipient_id to list of DeliveryResults
        """
        results = {}
        for recipient_id in recipient_ids:
            delivery_results = await self.send_notification(
                recipient_id=recipient_id,
                notification_type=notification_type,
                data=data,
                channels=channels
            )
            results[str(recipient_id)] = delivery_results

        return results

    def schedule_notification(
        self,
        recipient_id: UUID,
        notification_type: NotificationType,
        data: Dict[str, Any],
        send_at: datetime
    ) -> ScheduledNotification:
        """
        Schedule a notification for future delivery.

        Args:
            recipient_id: UUID of the notification recipient
            notification_type: Type of notification to send
            data: Data dictionary for template rendering
            send_at: When to send the notification

        Returns:
            ScheduledNotification object
        """
        scheduled = ScheduledNotification(
            recipient_id=recipient_id,
            notification_type=notification_type,
            data=data,
            send_at=send_at,
        )

        # TODO: Persist to database for production use
        # For now, add to in-memory queue
        self._scheduled_queue.append(scheduled)

        return scheduled

    async def process_scheduled_notifications(self) -> int:
        """
        Process and send all due scheduled notifications.

        This method should be called periodically (e.g., via Celery beat task)
        to check for and send scheduled notifications.

        Returns:
            Number of notifications sent
        """
        now = datetime.utcnow()
        sent_count = 0

        # TODO: Load from database instead of in-memory queue
        due_notifications = [
            n for n in self._scheduled_queue
            if n.send_at <= now and n.status == "pending"
        ]

        for notification in due_notifications:
            try:
                results = await self.send_notification(
                    recipient_id=notification.recipient_id,
                    notification_type=notification.notification_type,
                    data=notification.data
                )

                # Update status based on results
                all_success = all(r.success for r in results)
                notification.status = "sent" if all_success else "failed"
                sent_count += 1

            except Exception as e:
                notification.status = "failed"
                # TODO: Log error
                print(f"Failed to send scheduled notification {notification.id}: {e}")

        return sent_count

    def get_pending_notifications(
        self,
        user_id: UUID,
        limit: int = 50,
        unread_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch pending/unread notifications for a user.

        Args:
            user_id: UUID of the user
            limit: Maximum number of notifications to return
            unread_only: If True, only return unread notifications

        Returns:
            List of notification dictionaries
        """
        # TODO: Query database when notification model exists
        # For now, return empty list
        # notifications = (
        #     self.db.query(Notification)
        #     .filter(Notification.recipient_id == user_id)
        # )
        #
        # if unread_only:
        #     notifications = notifications.filter(Notification.is_read == False)
        #
        # notifications = notifications.order_by(
        #     Notification.created_at.desc()
        # ).limit(limit).all()

        return []

    def mark_as_read(self, notification_ids: List[UUID]) -> int:
        """
        Mark notifications as read.

        Args:
            notification_ids: List of notification UUIDs to mark as read

        Returns:
            Number of notifications marked as read
        """
        # TODO: Update database when notification model exists
        # count = (
        #     self.db.query(Notification)
        #     .filter(Notification.id.in_(notification_ids))
        #     .update({"is_read": True, "read_at": datetime.utcnow()})
        # )
        # self.db.commit()
        # return count

        return len(notification_ids)

    def _get_user_preferences(self, user_id: UUID) -> NotificationPreferences:
        """
        Load user notification preferences from database.

        Args:
            user_id: UUID of the user

        Returns:
            NotificationPreferences object
        """
        # TODO: Load from database when preference model exists
        # For now, return default preferences
        return NotificationPreferences(user_id=user_id)

    def _should_send_notification(
        self,
        preferences: NotificationPreferences,
        notification_type: NotificationType
    ) -> bool:
        """
        Check if notification should be sent based on user preferences.

        Args:
            preferences: User's notification preferences
            notification_type: Type of notification

        Returns:
            True if notification should be sent, False otherwise
        """
        # Check if notification type is enabled
        if not preferences.notification_types.get(notification_type.value, True):
            return False

        # Check quiet hours
        if preferences.quiet_hours_start and preferences.quiet_hours_end:
            current_hour = datetime.utcnow().hour
            if preferences.quiet_hours_start <= current_hour < preferences.quiet_hours_end:
                # Don't send during quiet hours unless it's high priority
                return False

        return True


# Convenience functions for common notification scenarios

async def notify_schedule_published(
    db: Session,
    recipient_ids: List[UUID],
    period: str,
    coverage_rate: float,
    total_assignments: int,
    violations_count: int,
    publisher_name: str
) -> Dict[str, List[DeliveryResult]]:
    """
    Send schedule published notifications to multiple recipients.

    Args:
        db: Database session
        recipient_ids: List of recipient UUIDs
        period: Schedule period (e.g., "January 2025")
        coverage_rate: Coverage percentage
        total_assignments: Total number of assignments
        violations_count: Number of ACGME violations
        publisher_name: Name of the person who published the schedule

    Returns:
        Dictionary of recipient_id to delivery results
    """
    service = NotificationService(db)
    data = {
        "period": period,
        "coverage_rate": f"{coverage_rate:.1f}",
        "total_assignments": total_assignments,
        "violations_count": violations_count,
        "publisher_name": publisher_name,
        "published_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    return await service.send_bulk(
        recipient_ids=recipient_ids,
        notification_type=NotificationType.SCHEDULE_PUBLISHED,
        data=data
    )


async def notify_acgme_warning(
    db: Session,
    recipient_id: UUID,
    violation_type: str,
    severity: str,
    person_name: str,
    violation_details: str,
    recommended_action: str
) -> List[DeliveryResult]:
    """
    Send ACGME compliance warning notification.

    Args:
        db: Database session
        recipient_id: UUID of the recipient (usually coordinator/admin)
        violation_type: Type of ACGME violation
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
        person_name: Name of affected person
        violation_details: Detailed description
        recommended_action: Recommended action to resolve

    Returns:
        List of delivery results
    """
    service = NotificationService(db)
    data = {
        "violation_type": violation_type,
        "severity": severity,
        "person_name": person_name,
        "violation_details": violation_details,
        "recommended_action": recommended_action,
        "detected_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    return await service.send_notification(
        recipient_id=recipient_id,
        notification_type=NotificationType.ACGME_WARNING,
        data=data
    )
