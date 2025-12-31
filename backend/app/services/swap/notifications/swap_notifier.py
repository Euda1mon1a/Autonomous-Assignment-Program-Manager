"""
Swap notification orchestrator.

Coordinates all swap-related notifications across multiple channels.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.swap import SwapRecord, SwapStatus
from app.models.person import Person
from .email_templates import SwapEmailTemplates


logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    """Result of notification sending."""

    success: bool
    channels_sent: list[str]
    failed_channels: list[str]
    message: str


class SwapNotifier:
    """
    Orchestrates swap notifications.

    Sends notifications via multiple channels:
    - Email
    - In-app notifications
    - SMS (for urgent)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize swap notifier.

        Args:
            db: Async database session
        """
        self.db = db
        self.email_templates = SwapEmailTemplates()

    async def notify_swap_created(
        self,
        swap: SwapRecord,
    ) -> NotificationResult:
        """
        Send notifications when swap is created.

        Args:
            swap: Swap record

        Returns:
            NotificationResult
        """
        channels_sent = []
        failed_channels = []

        # Get faculty information
        source_faculty = await self._get_faculty(swap.source_faculty_id)
        target_faculty = await self._get_faculty(swap.target_faculty_id)

        if not source_faculty or not target_faculty:
            return NotificationResult(
                success=False,
                channels_sent=[],
                failed_channels=["email"],
                message="Faculty not found",
            )

        # Send email to target faculty
        email_sent = await self._send_email(
            recipient=target_faculty.email if hasattr(target_faculty, "email") else None,
            subject="New Swap Request",
            body=self.email_templates.swap_request_email(
                source_name=source_faculty.name,
                target_name=target_faculty.name,
                source_week=swap.source_week,
                target_week=swap.target_week,
                reason=swap.reason,
            ),
        )

        if email_sent:
            channels_sent.append("email")
        else:
            failed_channels.append("email")

        # Send in-app notification
        in_app_sent = await self._send_in_app_notification(
            user_id=swap.target_faculty_id,
            title="New Swap Request",
            message=f"{source_faculty.name} requested to swap week {swap.source_week}",
        )

        if in_app_sent:
            channels_sent.append("in_app")
        else:
            failed_channels.append("in_app")

        logger.info(
            f"Sent swap creation notifications for {swap.id}: "
            f"{channels_sent}"
        )

        return NotificationResult(
            success=len(channels_sent) > 0,
            channels_sent=channels_sent,
            failed_channels=failed_channels,
            message=f"Notifications sent via {', '.join(channels_sent)}",
        )

    async def notify_swap_executed(
        self,
        swap: SwapRecord,
    ) -> NotificationResult:
        """
        Send notifications when swap is executed.

        Args:
            swap: Swap record

        Returns:
            NotificationResult
        """
        channels_sent = []
        failed_channels = []

        source_faculty = await self._get_faculty(swap.source_faculty_id)
        target_faculty = await self._get_faculty(swap.target_faculty_id)

        if not source_faculty or not target_faculty:
            return NotificationResult(
                success=False,
                channels_sent=[],
                failed_channels=["email"],
                message="Faculty not found",
            )

        # Send email to both parties
        for faculty in [source_faculty, target_faculty]:
            email_sent = await self._send_email(
                recipient=faculty.email if hasattr(faculty, "email") else None,
                subject="Swap Executed",
                body=self.email_templates.swap_executed_email(
                    faculty_name=faculty.name,
                    source_week=swap.source_week,
                    target_week=swap.target_week,
                    executed_at=swap.executed_at,
                ),
            )

            if email_sent:
                channels_sent.append(f"email_{faculty.name}")

        return NotificationResult(
            success=True,
            channels_sent=channels_sent,
            failed_channels=failed_channels,
            message="Execution notifications sent",
        )

    async def notify_swap_rolled_back(
        self,
        swap: SwapRecord,
    ) -> NotificationResult:
        """
        Send notifications when swap is rolled back.

        Args:
            swap: Swap record

        Returns:
            NotificationResult
        """
        channels_sent = []

        source_faculty = await self._get_faculty(swap.source_faculty_id)
        target_faculty = await self._get_faculty(swap.target_faculty_id)

        if not source_faculty or not target_faculty:
            return NotificationResult(
                success=False,
                channels_sent=[],
                failed_channels=["email"],
                message="Faculty not found",
            )

        # Send urgent notifications
        for faculty in [source_faculty, target_faculty]:
            email_sent = await self._send_email(
                recipient=faculty.email if hasattr(faculty, "email") else None,
                subject="URGENT: Swap Rolled Back",
                body=self.email_templates.swap_rollback_email(
                    faculty_name=faculty.name,
                    source_week=swap.source_week,
                    reason=swap.rollback_reason,
                ),
            )

            if email_sent:
                channels_sent.append(f"email_{faculty.name}")

        return NotificationResult(
            success=True,
            channels_sent=channels_sent,
            failed_channels=[],
            message="Rollback notifications sent",
        )

    async def notify_swap_match_found(
        self,
        swap: SwapRecord,
        match_id: UUID,
        compatibility_score: float,
    ) -> NotificationResult:
        """
        Notify when a compatible match is found.

        Args:
            swap: Swap record
            match_id: ID of matching swap
            compatibility_score: Compatibility score (0-1)

        Returns:
            NotificationResult
        """
        channels_sent = []

        source_faculty = await self._get_faculty(swap.source_faculty_id)

        if not source_faculty:
            return NotificationResult(
                success=False,
                channels_sent=[],
                failed_channels=["email"],
                message="Faculty not found",
            )

        # Get matching swap
        match_result = await self.db.execute(
            select(SwapRecord).where(SwapRecord.id == match_id)
        )
        match_swap = match_result.scalar_one_or_none()

        if not match_swap:
            return NotificationResult(
                success=False,
                channels_sent=[],
                failed_channels=["email"],
                message="Match not found",
            )

        match_faculty = await self._get_faculty(match_swap.source_faculty_id)

        if not match_faculty:
            return NotificationResult(
                success=False,
                channels_sent=[],
                failed_channels=["email"],
                message="Match faculty not found",
            )

        # Send notification
        email_sent = await self._send_email(
            recipient=source_faculty.email if hasattr(source_faculty, "email") else None,
            subject="Compatible Swap Match Found",
            body=self.email_templates.swap_match_email(
                faculty_name=source_faculty.name,
                match_name=match_faculty.name,
                match_week=match_swap.source_week,
                compatibility_score=compatibility_score,
            ),
        )

        if email_sent:
            channels_sent.append("email")

        return NotificationResult(
            success=len(channels_sent) > 0,
            channels_sent=channels_sent,
            failed_channels=[],
            message="Match notification sent",
        )

    # ===== Private Helper Methods =====

    async def _get_faculty(self, faculty_id: UUID) -> Person | None:
        """Get faculty member by ID."""
        result = await self.db.execute(
            select(Person).where(Person.id == faculty_id)
        )
        return result.scalar_one_or_none()

    async def _send_email(
        self,
        recipient: str | None,
        subject: str,
        body: str,
    ) -> bool:
        """
        Send email notification.

        Args:
            recipient: Email address
            subject: Email subject
            body: Email body

        Returns:
            True if sent successfully
        """
        if not recipient:
            logger.warning("No recipient email provided")
            return False

        # In real implementation, would use email service
        logger.info(f"Sending email to {recipient}: {subject}")

        return True

    async def _send_in_app_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
    ) -> bool:
        """
        Send in-app notification.

        Args:
            user_id: User ID
            title: Notification title
            message: Notification message

        Returns:
            True if sent successfully
        """
        # In real implementation, would create notification record
        logger.info(f"In-app notification for {user_id}: {title}")

        return True
