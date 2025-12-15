"""
Notification system for scheduling alerts.

This module provides email notification functionality for:
- Schedule changes
- Absence alerts
- Compliance warnings
- Assignment reminders

Usage:
    from app.notifications import NotificationService, NotificationType

    service = NotificationService(db)
    await service.send_schedule_change_notification(
        recipient_email="resident@example.com",
        recipient_name="Dr. Smith",
        change_type="Assignment",
        effective_date=date.today(),
        details="Your clinic rotation has been moved to next week."
    )
"""

from app.notifications.service import (
    NotificationService,
    NotificationType,
    NotificationPreferences,
    Notification,
    send_notification_task,
    send_batch_notifications_task,
)
from app.notifications.email import EmailSender, EmailSettings
from app.notifications.templates import NotificationTemplates

__all__ = [
    "NotificationService",
    "NotificationType",
    "NotificationPreferences",
    "Notification",
    "EmailSender",
    "EmailSettings",
    "NotificationTemplates",
    "send_notification_task",
    "send_batch_notifications_task",
]
