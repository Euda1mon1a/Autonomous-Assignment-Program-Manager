"""
Notification service for scheduling alerts.

Handles queue-based notification dispatch with support for:
- Schedule changes
- Absence alerts
- Compliance warnings
- Assignment reminders
"""
import asyncio
from datetime import date, datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID
from dataclasses import dataclass, field

from sqlalchemy.orm import Session
from celery import shared_task

from app.models.user import User
from app.models.person import Person
from app.notifications.email import EmailSender
from app.notifications.templates import NotificationTemplates


class NotificationType(str, Enum):
    """Notification type enumeration."""

    SCHEDULE_CHANGE = "schedule_change"
    ABSENCE_ALERT = "absence_alert"
    COMPLIANCE_WARNING = "compliance_warning"
    ASSIGNMENT_REMINDER = "assignment_reminder"


@dataclass
class NotificationPreferences:
    """
    User notification preferences.

    In production, these would be stored in the database.
    For now, we use sensible defaults.
    """

    user_id: UUID
    email_enabled: bool = True
    schedule_change_enabled: bool = True
    absence_alert_enabled: bool = True
    compliance_warning_enabled: bool = True
    assignment_reminder_enabled: bool = True
    reminder_days_before: int = 1  # Days before assignment to send reminder
    batch_notifications: bool = False  # Group multiple notifications
    digest_frequency: Optional[str] = None  # 'daily', 'weekly', or None for immediate

    def is_enabled(self, notification_type: NotificationType) -> bool:
        """Check if a specific notification type is enabled."""
        if not self.email_enabled:
            return False

        type_map = {
            NotificationType.SCHEDULE_CHANGE: self.schedule_change_enabled,
            NotificationType.ABSENCE_ALERT: self.absence_alert_enabled,
            NotificationType.COMPLIANCE_WARNING: self.compliance_warning_enabled,
            NotificationType.ASSIGNMENT_REMINDER: self.assignment_reminder_enabled,
        }

        return type_map.get(notification_type, True)


@dataclass
class Notification:
    """Represents a notification to be sent."""

    notification_type: NotificationType
    recipient_email: str
    recipient_name: str
    template_variables: Dict[str, Any]
    priority: int = 1  # 1 = high, 2 = medium, 3 = low
    send_at: Optional[datetime] = None  # Schedule for later, None = immediate
    metadata: Dict[str, Any] = field(default_factory=dict)


class NotificationService:
    """
    Notification service for scheduling alerts.

    Handles queuing, batching, and delivery of email notifications.
    """

    def __init__(self, db: Session):
        """Initialize notification service."""
        self.db = db
        self.email_sender = EmailSender()
        self.templates = NotificationTemplates()
        self._queue: List[Notification] = []

    def get_user_preferences(self, user_id: UUID) -> NotificationPreferences:
        """
        Get notification preferences for a user.

        In production, this would query the database.
        For now, returns default preferences.
        """
        # TODO: Implement database storage for preferences
        return NotificationPreferences(user_id=user_id)

    async def send_schedule_change_notification(
        self,
        recipient_email: str,
        recipient_name: str,
        change_type: str,
        effective_date: date,
        block_name: Optional[str] = None,
        rotation_name: Optional[str] = None,
        details: Optional[str] = None,
        schedule_url: Optional[str] = None,
    ) -> bool:
        """
        Send schedule change notification.

        Args:
            recipient_email: Recipient's email address
            recipient_name: Recipient's name
            change_type: Type of change (e.g., "Assignment", "Rotation Swap", "Time Change")
            effective_date: When the change takes effect
            block_name: Name of affected block (optional)
            rotation_name: Name of affected rotation (optional)
            details: Additional details about the change (optional)
            schedule_url: URL to view updated schedule (optional)

        Returns:
            bool: True if notification sent successfully
        """
        template_vars = {
            "recipient_name": recipient_name,
            "change_type": change_type,
            "effective_date": effective_date,
            "block_name": block_name,
            "rotation_name": rotation_name,
            "details": details,
            "schedule_url": schedule_url,
        }

        notification = Notification(
            notification_type=NotificationType.SCHEDULE_CHANGE,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            template_variables=template_vars,
            priority=1,
        )

        return await self._send_notification(notification)

    async def send_absence_alert(
        self,
        recipient_email: str,
        recipient_name: str,
        absent_person_name: str,
        absence_reason: str,
        start_date: date,
        end_date: date,
        affected_count: int = 0,
        critical_services: Optional[List[str]] = None,
        coverage_url: Optional[str] = None,
    ) -> bool:
        """
        Send absence alert notification to coordinators/admins.

        Args:
            recipient_email: Coordinator's email
            recipient_name: Coordinator's name
            absent_person_name: Name of person who will be absent
            absence_reason: Reason for absence
            start_date: Absence start date
            end_date: Absence end date
            affected_count: Number of affected assignments
            critical_services: List of critical services affected
            coverage_url: URL to manage coverage

        Returns:
            bool: True if notification sent successfully
        """
        template_vars = {
            "recipient_name": recipient_name,
            "absent_person_name": absent_person_name,
            "absence_reason": absence_reason,
            "start_date": start_date,
            "end_date": end_date,
            "affected_count": affected_count,
            "critical_services": critical_services or [],
            "coverage_url": coverage_url,
        }

        notification = Notification(
            notification_type=NotificationType.ABSENCE_ALERT,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            template_variables=template_vars,
            priority=1,
        )

        return await self._send_notification(notification)

    async def send_compliance_warning(
        self,
        recipient_email: str,
        recipient_name: str,
        violation_type: str,
        severity: str,
        start_date: date,
        end_date: date,
        description: str,
        affected_person: Optional[str] = None,
        recommended_action: Optional[str] = None,
        review_url: Optional[str] = None,
    ) -> bool:
        """
        Send compliance warning notification.

        Args:
            recipient_email: Administrator's email
            recipient_name: Administrator's name
            violation_type: Type of compliance violation
            severity: Severity level (e.g., "High", "Medium", "Low")
            start_date: Start of affected period
            end_date: End of affected period
            description: Description of the violation
            affected_person: Name of affected person (optional)
            recommended_action: Suggested corrective action (optional)
            review_url: URL to review the issue (optional)

        Returns:
            bool: True if notification sent successfully
        """
        template_vars = {
            "recipient_name": recipient_name,
            "violation_type": violation_type,
            "severity": severity,
            "start_date": start_date,
            "end_date": end_date,
            "description": description,
            "affected_person": affected_person,
            "recommended_action": recommended_action,
            "review_url": review_url,
        }

        notification = Notification(
            notification_type=NotificationType.COMPLIANCE_WARNING,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            template_variables=template_vars,
            priority=1 if severity.lower() == "high" else 2,
        )

        return await self._send_notification(notification)

    async def send_assignment_reminder(
        self,
        recipient_email: str,
        recipient_name: str,
        assignment_date: date,
        rotation_name: str,
        location: Optional[str] = None,
        supervisor: Optional[str] = None,
        start_time: Optional[str] = None,
        instructions: Optional[str] = None,
        requirements: Optional[List[str]] = None,
        schedule_url: Optional[str] = None,
    ) -> bool:
        """
        Send assignment reminder notification.

        Args:
            recipient_email: Recipient's email
            recipient_name: Recipient's name
            assignment_date: Date of the assignment
            rotation_name: Name of the rotation
            location: Assignment location (optional)
            supervisor: Supervising faculty (optional)
            start_time: Assignment start time (optional)
            instructions: Special instructions (optional)
            requirements: List of requirements (optional)
            schedule_url: URL to view schedule (optional)

        Returns:
            bool: True if notification sent successfully
        """
        template_vars = {
            "recipient_name": recipient_name,
            "assignment_date": assignment_date,
            "rotation_name": rotation_name,
            "location": location,
            "supervisor": supervisor,
            "start_time": start_time,
            "instructions": instructions,
            "requirements": requirements or [],
            "schedule_url": schedule_url,
        }

        notification = Notification(
            notification_type=NotificationType.ASSIGNMENT_REMINDER,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            template_variables=template_vars,
            priority=2,
        )

        return await self._send_notification(notification)

    async def send_batch_notifications(
        self,
        notifications: List[Notification],
        max_concurrent: int = 5,
    ) -> Dict[str, bool]:
        """
        Send multiple notifications concurrently.

        Args:
            notifications: List of notifications to send
            max_concurrent: Maximum concurrent sends

        Returns:
            dict mapping recipient emails to success status
        """
        # Prepare email data for batch sending
        email_data = []

        for notification in notifications:
            subject, html_content = self.templates.render(
                notification.notification_type.value,
                notification.template_variables,
            )

            email_data.append({
                "to_email": notification.recipient_email,
                "to_name": notification.recipient_name,
                "subject": subject,
                "html_content": html_content,
            })

        # Send batch
        return await self.email_sender.send_batch(email_data, max_concurrent)

    def queue_notification(self, notification: Notification) -> None:
        """
        Add notification to queue for later processing.

        Args:
            notification: Notification to queue
        """
        self._queue.append(notification)

    async def process_queue(self) -> Dict[str, int]:
        """
        Process all queued notifications.

        Returns:
            dict with counts of sent, failed, and skipped notifications
        """
        if not self._queue:
            return {"sent": 0, "failed": 0, "skipped": 0}

        # Sort by priority (lower number = higher priority)
        self._queue.sort(key=lambda n: n.priority)

        results = await self.send_batch_notifications(self._queue)

        sent = sum(1 for success in results.values() if success)
        failed = len(results) - sent

        # Clear queue
        self._queue.clear()

        return {
            "sent": sent,
            "failed": failed,
            "skipped": 0,
        }

    async def _send_notification(self, notification: Notification) -> bool:
        """
        Send a single notification immediately.

        Args:
            notification: Notification to send

        Returns:
            bool: True if sent successfully
        """
        try:
            # Render template
            subject, html_content = self.templates.render(
                notification.notification_type.value,
                notification.template_variables,
            )

            # Send email
            success = await self.email_sender.send_email(
                to_email=notification.recipient_email,
                subject=subject,
                html_content=html_content,
                to_name=notification.recipient_name,
            )

            return success

        except Exception as e:
            print(f"Failed to send notification: {str(e)}")
            return False

    def notify_schedule_coordinators(
        self,
        notification_type: NotificationType,
        template_variables: Dict[str, Any],
    ) -> None:
        """
        Queue notifications for all schedule coordinators.

        Args:
            notification_type: Type of notification
            template_variables: Variables for template rendering
        """
        # Get all coordinators and admins
        coordinators = (
            self.db.query(User)
            .filter(User.role.in_(["admin", "coordinator"]))
            .filter(User.is_active == True)
            .all()
        )

        # Queue notification for each coordinator
        for coordinator in coordinators:
            notification = Notification(
                notification_type=notification_type,
                recipient_email=coordinator.email,
                recipient_name=coordinator.username,
                template_variables=template_variables,
                priority=1,
            )
            self.queue_notification(notification)


# Celery tasks for asynchronous notification processing
@shared_task(name="notifications.send_notification")
def send_notification_task(
    notification_type: str,
    recipient_email: str,
    recipient_name: str,
    template_variables: dict,
) -> bool:
    """
    Celery task for sending notifications asynchronously.

    Args:
        notification_type: Type of notification
        recipient_email: Recipient's email
        recipient_name: Recipient's name
        template_variables: Template variables

    Returns:
        bool: True if sent successfully
    """
    email_sender = EmailSender()
    templates = NotificationTemplates()

    try:
        # Render template
        subject, html_content = templates.render(
            notification_type,
            template_variables,
        )

        # Send email synchronously (Celery worker handles async)
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(
            email_sender.send_email(
                to_email=recipient_email,
                subject=subject,
                html_content=html_content,
                to_name=recipient_name,
            )
        )

        return success

    except Exception as e:
        print(f"Task failed to send notification: {str(e)}")
        return False


@shared_task(name="notifications.send_batch")
def send_batch_notifications_task(notifications_data: list) -> dict:
    """
    Celery task for sending batch notifications.

    Args:
        notifications_data: List of notification dictionaries

    Returns:
        dict with send results
    """
    email_sender = EmailSender()
    templates = NotificationTemplates()

    email_data = []

    for notif_data in notifications_data:
        subject, html_content = templates.render(
            notif_data["notification_type"],
            notif_data["template_variables"],
        )

        email_data.append({
            "to_email": notif_data["recipient_email"],
            "to_name": notif_data["recipient_name"],
            "subject": subject,
            "html_content": html_content,
        })

    # Send batch synchronously (Celery worker handles async)
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(
        email_sender.send_batch(email_data)
    )

    return results
