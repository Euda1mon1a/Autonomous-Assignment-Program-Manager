"""Notification service for FMIT swap events."""
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from uuid import UUID

from sqlalchemy.orm import Session


class SwapNotificationType(str, Enum):
    """Types of swap notifications."""
    SWAP_REQUEST_RECEIVED = "swap_request_received"
    SWAP_REQUEST_ACCEPTED = "swap_request_accepted"
    SWAP_REQUEST_REJECTED = "swap_request_rejected"
    SWAP_EXECUTED = "swap_executed"
    SWAP_ROLLED_BACK = "swap_rolled_back"
    SWAP_REMINDER = "swap_reminder"
    MARKETPLACE_MATCH = "marketplace_match"


@dataclass
class SwapNotification:
    """A swap notification to be sent."""
    recipient_id: UUID
    recipient_email: str
    notification_type: SwapNotificationType
    subject: str
    body: str
    swap_id: UUID | None = None
    week: date | None = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class SwapNotificationService:
    """
    Service for sending notifications related to FMIT swaps.

    Integrates with the email service to send notifications
    and respects faculty notification preferences.
    """

    def __init__(self, db: Session):
        self.db = db
        self._pending_notifications: list[SwapNotification] = []

    def notify_swap_request_received(
        self,
        recipient_faculty_id: UUID,
        requester_name: str,
        week_offered: date,
        swap_id: UUID,
        reason: str | None = None,
    ) -> SwapNotification | None:
        """
        Notify a faculty member that they received a swap request.

        Args:
            recipient_faculty_id: Faculty receiving the request
            requester_name: Name of the requesting faculty
            week_offered: The FMIT week being offered
            swap_id: The swap request ID
            reason: Optional reason for the request
        """
        if not self._should_notify(recipient_faculty_id, "swap_requests"):
            return None

        recipient = self._get_faculty_info(recipient_faculty_id)
        if not recipient:
            return None

        subject = f"FMIT Swap Request from {requester_name}"
        body = self._build_swap_request_body(
            requester_name=requester_name,
            week=week_offered,
            reason=reason,
        )

        notification = SwapNotification(
            recipient_id=recipient_faculty_id,
            recipient_email=recipient["email"],
            notification_type=SwapNotificationType.SWAP_REQUEST_RECEIVED,
            subject=subject,
            body=body,
            swap_id=swap_id,
            week=week_offered,
        )

        self._pending_notifications.append(notification)
        return notification

    def notify_swap_accepted(
        self,
        recipient_faculty_id: UUID,
        accepter_name: str,
        week: date,
        swap_id: UUID,
    ) -> SwapNotification | None:
        """Notify that a swap request was accepted."""
        if not self._should_notify(recipient_faculty_id, "swap_requests"):
            return None

        recipient = self._get_faculty_info(recipient_faculty_id)
        if not recipient:
            return None

        subject = f"Swap Request Accepted by {accepter_name}"
        body = f"""Good news! {accepter_name} has accepted your swap request for the week of {week.isoformat()}.

The swap will be processed shortly. You will receive another notification when it is complete.

If you have any questions, please contact the scheduling coordinator.
"""

        notification = SwapNotification(
            recipient_id=recipient_faculty_id,
            recipient_email=recipient["email"],
            notification_type=SwapNotificationType.SWAP_REQUEST_ACCEPTED,
            subject=subject,
            body=body,
            swap_id=swap_id,
            week=week,
        )

        self._pending_notifications.append(notification)
        return notification

    def notify_swap_rejected(
        self,
        recipient_faculty_id: UUID,
        rejecter_name: str,
        week: date,
        swap_id: UUID,
        reason: str | None = None,
    ) -> SwapNotification | None:
        """Notify that a swap request was rejected."""
        if not self._should_notify(recipient_faculty_id, "swap_requests"):
            return None

        recipient = self._get_faculty_info(recipient_faculty_id)
        if not recipient:
            return None

        subject = f"Swap Request Declined by {rejecter_name}"
        body = f"""{rejecter_name} has declined your swap request for the week of {week.isoformat()}.

{f"Reason: {reason}" if reason else ""}

You can try requesting a swap with another faculty member or posting in the swap marketplace.
"""

        notification = SwapNotification(
            recipient_id=recipient_faculty_id,
            recipient_email=recipient["email"],
            notification_type=SwapNotificationType.SWAP_REQUEST_REJECTED,
            subject=subject,
            body=body,
            swap_id=swap_id,
            week=week,
        )

        self._pending_notifications.append(notification)
        return notification

    def notify_swap_executed(
        self,
        faculty_ids: list[UUID],
        week: date,
        swap_id: UUID,
        details: str,
    ) -> list[SwapNotification]:
        """Notify all parties that a swap was executed."""
        notifications = []

        for faculty_id in faculty_ids:
            if not self._should_notify(faculty_id, "schedule_changes"):
                continue

            recipient = self._get_faculty_info(faculty_id)
            if not recipient:
                continue

            subject = f"FMIT Schedule Updated - Week of {week.isoformat()}"
            body = f"""Your FMIT schedule has been updated.

{details}

Please review your updated schedule in the portal.
"""

            notification = SwapNotification(
                recipient_id=faculty_id,
                recipient_email=recipient["email"],
                notification_type=SwapNotificationType.SWAP_EXECUTED,
                subject=subject,
                body=body,
                swap_id=swap_id,
                week=week,
            )

            notifications.append(notification)
            self._pending_notifications.append(notification)

        return notifications

    def notify_swap_rolled_back(
        self,
        faculty_ids: list[UUID],
        week: date,
        swap_id: UUID,
        reason: str,
    ) -> list[SwapNotification]:
        """Notify all parties that a swap was rolled back."""
        notifications = []

        for faculty_id in faculty_ids:
            recipient = self._get_faculty_info(faculty_id)
            if not recipient:
                continue

            subject = f"FMIT Swap Rolled Back - Week of {week.isoformat()}"
            body = f"""A recent swap affecting the week of {week.isoformat()} has been rolled back.

Reason: {reason}

Your schedule has been reverted to its previous state. Please review your schedule in the portal.
"""

            notification = SwapNotification(
                recipient_id=faculty_id,
                recipient_email=recipient["email"],
                notification_type=SwapNotificationType.SWAP_ROLLED_BACK,
                subject=subject,
                body=body,
                swap_id=swap_id,
                week=week,
            )

            notifications.append(notification)
            self._pending_notifications.append(notification)

        return notifications

    def notify_marketplace_match(
        self,
        recipient_faculty_id: UUID,
        poster_name: str,
        week_available: date,
        request_id: UUID,
    ) -> SwapNotification | None:
        """Notify about a potential marketplace match."""
        if not self._should_notify(recipient_faculty_id, "swap_requests"):
            return None

        recipient = self._get_faculty_info(recipient_faculty_id)
        if not recipient:
            return None

        subject = f"FMIT Week Available - {week_available.isoformat()}"
        body = f"""{poster_name} has posted the week of {week_available.isoformat()} in the swap marketplace.

Based on your preferences, this week may be a good match for you.

View the marketplace in the portal to respond.
"""

        notification = SwapNotification(
            recipient_id=recipient_faculty_id,
            recipient_email=recipient["email"],
            notification_type=SwapNotificationType.MARKETPLACE_MATCH,
            subject=subject,
            body=body,
            swap_id=request_id,
            week=week_available,
        )

        self._pending_notifications.append(notification)
        return notification

    def send_pending_notifications(self) -> int:
        """
        Send all pending notifications.

        Returns:
            Number of notifications sent
        """
        # TODO: Integrate with actual email service
        # For now, just clear the queue and return count
        count = len(self._pending_notifications)

        for notification in self._pending_notifications:
            self._send_notification(notification)

        self._pending_notifications.clear()
        return count

    def get_pending_count(self) -> int:
        """Get count of pending notifications."""
        return len(self._pending_notifications)

    def _should_notify(self, faculty_id: UUID, preference_key: str) -> bool:
        """Check if faculty wants this type of notification."""
        from app.models.faculty_preference import FacultyPreference

        prefs = self.db.query(FacultyPreference).filter(
            FacultyPreference.faculty_id == faculty_id
        ).first()

        if not prefs:
            return True  # Default to notify

        pref_map = {
            "swap_requests": prefs.notify_swap_requests,
            "schedule_changes": prefs.notify_schedule_changes,
            "conflict_alerts": prefs.notify_conflict_alerts,
        }

        return pref_map.get(preference_key, True)

    def _get_faculty_info(self, faculty_id: UUID) -> dict | None:
        """Get faculty name and email."""
        from app.models.person import Person

        faculty = self.db.query(Person).filter(
            Person.id == faculty_id
        ).first()

        if not faculty:
            return None

        return {
            "id": faculty.id,
            "name": faculty.name,
            "email": faculty.email or f"{faculty.name.lower().replace(' ', '.')}@example.com",
        }

    def _build_swap_request_body(
        self,
        requester_name: str,
        week: date,
        reason: str | None = None,
    ) -> str:
        """Build the body for a swap request notification."""
        return f"""{requester_name} would like to swap their FMIT week.

Week offered: {week.isoformat()}
{f"Reason: {reason}" if reason else ""}

Please log in to the faculty portal to accept or decline this request.
"""

    def _send_notification(self, notification: SwapNotification) -> bool:
        """Actually send a notification (placeholder for email integration)."""
        # TODO: Integrate with email_service.py
        # For now, just log
        print(f"[NOTIFICATION] To: {notification.recipient_email}")
        print(f"  Subject: {notification.subject}")
        return True
