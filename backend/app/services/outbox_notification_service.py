"""Notification service for outbox events.

This service handles sending email notifications for events from the transactional
outbox, including:
- Assignment changes (created, updated, deleted)
- Swap events (requested, approved, rejected, executed)
- Conflict events (detected, resolved, escalated)

Integration:
    Used by app.outbox.tasks to send notifications when events are processed.
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.user import User
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class OutboxNotificationService:
    """Service for sending notifications from outbox events."""

    def __init__(self, db: Session) -> None:
        """Initialize notification service.

        Args:
            db: Database session for looking up recipients
        """
        self.db = db
        self.email_service = EmailService()

    def _get_person_email(self, person_id: str | UUID) -> str | None:
        """Get email address for a person.

        Args:
            person_id: Person UUID as string or UUID object

        Returns:
            Email address or None if not found
        """
        try:
            if isinstance(person_id, str):
                person_id = UUID(person_id)
            person = self.db.query(Person).filter(Person.id == person_id).first()
            return person.email if person else None
        except (ValueError, TypeError):
            logger.warning(f"Invalid person_id: {person_id}")
            return None

    def _get_coordinator_emails(self) -> list[str]:
        """Get email addresses for coordinators.

        Returns:
            List of coordinator email addresses
        """
        coordinators = (
            self.db.query(User)
            .filter(User.role.in_(["admin", "coordinator"]))
            .filter(User.is_active == True)
            .all()
        )
        return [u.email for u in coordinators if u.email]

    # =========================================================================
    # Assignment Notifications
    # =========================================================================

    def notify_assignment_created(
        self,
        person_id: str,
        block_id: str,
        rotation_id: str | None,
        payload: dict[str, Any],
    ) -> bool:
        """Notify person of new assignment.

        Args:
            person_id: ID of person assigned
            block_id: ID of block
            rotation_id: ID of rotation (optional)
            payload: Full event payload

        Returns:
            True if notification sent successfully
        """
        email = self._get_person_email(person_id)
        if not email:
            logger.warning(f"No email for person {person_id}, skipping notification")
            return False

        rotation_name = payload.get("rotation_name", "Unknown Rotation")
        block_date = payload.get("block_date", "Unknown Date")

        subject = f"New Schedule Assignment: {rotation_name}"
        body_html = f"""
        <html>
        <body>
            <h2>New Schedule Assignment</h2>
            <p>You have been assigned to a new rotation:</p>
            <ul>
                <li><strong>Rotation:</strong> {rotation_name}</li>
                <li><strong>Date:</strong> {block_date}</li>
            </ul>
            <p>Please check the scheduling system for full details.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This is an automated message from the Residency Scheduling System.
            </p>
        </body>
        </html>
        """
        body_text = f"""
New Schedule Assignment

You have been assigned to a new rotation:
- Rotation: {rotation_name}
- Date: {block_date}

Please check the scheduling system for full details.
        """

        return self.email_service.send_email(email, subject, body_html, body_text)

    def notify_assignment_updated(
        self,
        person_id: str,
        assignment_id: str,
        old_rotation: str | None,
        new_rotation: str | None,
        payload: dict[str, Any],
    ) -> bool:
        """Notify person of assignment change.

        Args:
            person_id: ID of affected person
            assignment_id: ID of assignment
            old_rotation: Previous rotation ID
            new_rotation: New rotation ID
            payload: Full event payload

        Returns:
            True if notification sent successfully
        """
        email = self._get_person_email(person_id)
        if not email:
            return False

        old_name = payload.get("old_rotation_name", old_rotation or "Unknown")
        new_name = payload.get("new_rotation_name", new_rotation or "Unknown")
        block_date = payload.get("block_date", "Unknown Date")

        subject = "Schedule Assignment Updated"
        body_html = f"""
        <html>
        <body>
            <h2>Schedule Assignment Updated</h2>
            <p>One of your assignments has been updated:</p>
            <ul>
                <li><strong>Date:</strong> {block_date}</li>
                <li><strong>Previous Rotation:</strong> {old_name}</li>
                <li><strong>New Rotation:</strong> {new_name}</li>
            </ul>
            <p>Please check the scheduling system for full details.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This is an automated message from the Residency Scheduling System.
            </p>
        </body>
        </html>
        """
        body_text = f"""
Schedule Assignment Updated

One of your assignments has been updated:
- Date: {block_date}
- Previous Rotation: {old_name}
- New Rotation: {new_name}

Please check the scheduling system for full details.
        """

        return self.email_service.send_email(email, subject, body_html, body_text)

    def notify_assignment_deleted(
        self,
        person_id: str,
        assignment_id: str,
        payload: dict[str, Any],
    ) -> bool:
        """Notify person of assignment removal.

        Args:
            person_id: ID of affected person
            assignment_id: ID of assignment removed
            payload: Full event payload

        Returns:
            True if notification sent successfully
        """
        email = self._get_person_email(person_id)
        if not email:
            return False

        rotation_name = payload.get("rotation_name", "Unknown")
        block_date = payload.get("block_date", "Unknown Date")

        subject = "Schedule Assignment Removed"
        body_html = f"""
        <html>
        <body>
            <h2>Schedule Assignment Removed</h2>
            <p>An assignment has been removed from your schedule:</p>
            <ul>
                <li><strong>Rotation:</strong> {rotation_name}</li>
                <li><strong>Date:</strong> {block_date}</li>
            </ul>
            <p>Please check the scheduling system for your updated schedule.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This is an automated message from the Residency Scheduling System.
            </p>
        </body>
        </html>
        """
        body_text = f"""
Schedule Assignment Removed

An assignment has been removed from your schedule:
- Rotation: {rotation_name}
- Date: {block_date}

Please check the scheduling system for your updated schedule.
        """

        return self.email_service.send_email(email, subject, body_html, body_text)

    # =========================================================================
    # Swap Notifications
    # =========================================================================

    def notify_swap_requested(
        self,
        target_id: str,
        requester_id: str,
        swap_id: str,
        payload: dict[str, Any],
    ) -> bool:
        """Notify target person of new swap request.

        Args:
            target_id: ID of person receiving request
            requester_id: ID of person requesting swap
            swap_id: ID of swap request
            payload: Full event payload

        Returns:
            True if notification sent successfully
        """
        email = self._get_person_email(target_id)
        if not email:
            return False

        requester_name = payload.get("requester_name", "A colleague")
        swap_type = payload.get("swap_type", "schedule")

        subject = f"New Swap Request from {requester_name}"
        body_html = f"""
        <html>
        <body>
            <h2>New Swap Request</h2>
            <p>{requester_name} has requested a {swap_type} swap with you.</p>
            <p>Please log in to the scheduling system to review and respond to this request.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This is an automated message from the Residency Scheduling System.
            </p>
        </body>
        </html>
        """
        body_text = f"""
New Swap Request

{requester_name} has requested a {swap_type} swap with you.

Please log in to the scheduling system to review and respond to this request.
        """

        return self.email_service.send_email(email, subject, body_html, body_text)

    def notify_swap_approved(
        self,
        requester_id: str,
        swap_id: str,
        payload: dict[str, Any],
    ) -> bool:
        """Notify requester that their swap was approved.

        Args:
            requester_id: ID of person who requested swap
            swap_id: ID of swap request
            payload: Full event payload

        Returns:
            True if notification sent successfully
        """
        email = self._get_person_email(requester_id)
        if not email:
            return False

        approver_name = payload.get("approver_name", "The coordinator")

        subject = "Swap Request Approved"
        body_html = f"""
        <html>
        <body>
            <h2>Swap Request Approved</h2>
            <p>Good news! Your swap request has been approved by {approver_name}.</p>
            <p>The swap will be processed shortly. Please check your schedule for updates.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This is an automated message from the Residency Scheduling System.
            </p>
        </body>
        </html>
        """
        body_text = f"""
Swap Request Approved

Good news! Your swap request has been approved by {approver_name}.

The swap will be processed shortly. Please check your schedule for updates.
        """

        return self.email_service.send_email(email, subject, body_html, body_text)

    def notify_swap_rejected(
        self,
        requester_id: str,
        swap_id: str,
        reason: str | None,
        payload: dict[str, Any],
    ) -> bool:
        """Notify requester that their swap was rejected.

        Args:
            requester_id: ID of person who requested swap
            swap_id: ID of swap request
            reason: Rejection reason
            payload: Full event payload

        Returns:
            True if notification sent successfully
        """
        email = self._get_person_email(requester_id)
        if not email:
            return False

        reason_text = reason or "No reason provided"

        subject = "Swap Request Rejected"
        body_html = f"""
        <html>
        <body>
            <h2>Swap Request Rejected</h2>
            <p>Unfortunately, your swap request has been rejected.</p>
            <p><strong>Reason:</strong> {reason_text}</p>
            <p>If you have questions, please contact the scheduling coordinator.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This is an automated message from the Residency Scheduling System.
            </p>
        </body>
        </html>
        """
        body_text = f"""
Swap Request Rejected

Unfortunately, your swap request has been rejected.

Reason: {reason_text}

If you have questions, please contact the scheduling coordinator.
        """

        return self.email_service.send_email(email, subject, body_html, body_text)

    def notify_swap_executed(
        self,
        requester_id: str,
        target_id: str | None,
        swap_id: str,
        payload: dict[str, Any],
    ) -> bool:
        """Notify both parties that swap has been executed.

        Args:
            requester_id: ID of person who requested swap
            target_id: ID of swap target (if applicable)
            swap_id: ID of swap
            payload: Full event payload

        Returns:
            True if at least one notification sent
        """
        success = False
        swap_type = payload.get("swap_type", "schedule")

        # Notify requester
        email = self._get_person_email(requester_id)
        if email:
            subject = "Swap Completed Successfully"
            body_html = f"""
            <html>
            <body>
                <h2>Swap Completed</h2>
                <p>Your {swap_type} swap has been successfully executed.</p>
                <p>Please check your updated schedule in the scheduling system.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This is an automated message from the Residency Scheduling System.
                </p>
            </body>
            </html>
            """
            if self.email_service.send_email(email, subject, body_html):
                success = True

        # Notify target if exists
        if target_id:
            email = self._get_person_email(target_id)
            if email:
                subject = "Swap Completed Successfully"
                body_html = f"""
                <html>
                <body>
                    <h2>Swap Completed</h2>
                    <p>A {swap_type} swap affecting your schedule has been completed.</p>
                    <p>Please check your updated schedule in the scheduling system.</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        This is an automated message from the Residency Scheduling System.
                    </p>
                </body>
                </html>
                """
                if self.email_service.send_email(email, subject, body_html):
                    success = True

        return success

    # =========================================================================
    # Conflict Notifications
    # =========================================================================

    def notify_conflict_detected(
        self,
        conflict_id: str | None,
        conflict_type: str,
        severity: str,
        affected_persons: list[str],
        payload: dict[str, Any],
    ) -> bool:
        """Notify affected persons and coordinators of a conflict.

        Args:
            conflict_id: ID of conflict
            conflict_type: Type of conflict
            severity: Conflict severity (low, medium, high)
            affected_persons: List of affected person IDs
            payload: Full event payload

        Returns:
            True if at least one notification sent
        """
        success = False

        # For high severity, notify coordinators
        if severity == "high":
            for email in self._get_coordinator_emails():
                subject = f"[HIGH SEVERITY] Schedule Conflict Detected: {conflict_type}"
                body_html = f"""
                <html>
                <body>
                    <h2 style="color: #dc3545;">High Severity Conflict Detected</h2>
                    <p><strong>Type:</strong> {conflict_type}</p>
                    <p><strong>Affected Persons:</strong> {len(affected_persons)}</p>
                    <p>Please log in to the scheduling system to review and resolve this conflict.</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        This is an automated message from the Residency Scheduling System.
                    </p>
                </body>
                </html>
                """
                if self.email_service.send_email(email, subject, body_html):
                    success = True

        # Notify affected persons
        for person_id in affected_persons:
            email = self._get_person_email(person_id)
            if email:
                subject = f"Schedule Conflict: {conflict_type}"
                body_html = f"""
                <html>
                <body>
                    <h2>Schedule Conflict Detected</h2>
                    <p>A scheduling conflict has been detected that affects you:</p>
                    <p><strong>Type:</strong> {conflict_type}</p>
                    <p>The scheduling team has been notified and will work to resolve this.</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        This is an automated message from the Residency Scheduling System.
                    </p>
                </body>
                </html>
                """
                if self.email_service.send_email(email, subject, body_html):
                    success = True

        return success

    def notify_conflict_resolved(
        self,
        conflict_id: str | None,
        resolution: str,
        affected_persons: list[str],
        payload: dict[str, Any],
    ) -> bool:
        """Notify affected persons that conflict has been resolved.

        Args:
            conflict_id: ID of conflict
            resolution: How conflict was resolved
            affected_persons: List of affected person IDs
            payload: Full event payload

        Returns:
            True if at least one notification sent
        """
        success = False

        for person_id in affected_persons:
            email = self._get_person_email(person_id)
            if email:
                subject = "Schedule Conflict Resolved"
                body_html = f"""
                <html>
                <body>
                    <h2>Schedule Conflict Resolved</h2>
                    <p>A scheduling conflict affecting you has been resolved.</p>
                    <p><strong>Resolution:</strong> {resolution}</p>
                    <p>Please check your schedule for any updates.</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        This is an automated message from the Residency Scheduling System.
                    </p>
                </body>
                </html>
                """
                if self.email_service.send_email(email, subject, body_html):
                    success = True

        return success

    def notify_conflict_escalated(
        self,
        conflict_id: str | None,
        conflict_type: str,
        escalation_level: int,
        payload: dict[str, Any],
    ) -> bool:
        """Notify coordinators of escalated conflict.

        Args:
            conflict_id: ID of conflict
            conflict_type: Type of conflict
            escalation_level: Level of escalation
            payload: Full event payload

        Returns:
            True if at least one notification sent
        """
        success = False

        for email in self._get_coordinator_emails():
            subject = (
                f"[ESCALATED] Schedule Conflict Requires Attention: {conflict_type}"
            )
            body_html = f"""
            <html>
            <body>
                <h2 style="color: #fd7e14;">Conflict Escalated - Level {escalation_level}</h2>
                <p><strong>Type:</strong> {conflict_type}</p>
                <p>This conflict has been escalated and requires immediate attention.</p>
                <p>Please log in to the scheduling system to review.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This is an automated message from the Residency Scheduling System.
                </p>
            </body>
            </html>
            """
            if self.email_service.send_email(email, subject, body_html):
                success = True

        return success
