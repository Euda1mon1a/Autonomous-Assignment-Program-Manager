"""Priority handling for notifications."""

from typing import Any

from app.core.logging import get_logger
from app.notifications.notification_types import NotificationType

logger = get_logger(__name__)


class PriorityHandler:
    """
    Handles notification priority calculations and management.

    Priority Levels:
    - CRITICAL (90-100): Immediate delivery, no batching, bypass quiet hours
    - HIGH (70-89): Prioritized delivery, minimal delay
    - NORMAL (30-69): Standard delivery, can be batched
    - LOW (0-29): Delayed delivery, aggressive batching

    Priority is calculated based on:
    1. Notification type base priority
    2. Data-driven priority modifiers
    3. User role/status
    4. Time sensitivity
    """

    # Base priority scores for notification types
    BASE_PRIORITIES = {
        NotificationType.ACGME_WARNING: 95,  # CRITICAL
        NotificationType.SCHEDULE_PUBLISHED: 75,  # HIGH
        NotificationType.ASSIGNMENT_CHANGED: 70,  # HIGH
        NotificationType.SHIFT_REMINDER_1H: 60,  # NORMAL
        NotificationType.SHIFT_REMINDER_24H: 40,  # NORMAL
        NotificationType.ABSENCE_APPROVED: 50,  # NORMAL
        NotificationType.ABSENCE_REJECTED: 50,  # NORMAL
    }

    def __init__(self) -> None:
        """Initialize the priority handler."""
        pass

    def calculate_priority_score(
        self,
        notification_type: NotificationType,
        priority_level: str,
        data: dict[str, Any],
    ) -> int:
        """
        Calculate numerical priority score for a notification.

        Args:
            notification_type: Type of notification
            priority_level: Priority level string ('high', 'normal', 'low')
            data: Notification data for context-based priority

        Returns:
            Priority score (0-100)
        """
        # Start with base priority for the notification type
        base_score = self.BASE_PRIORITIES.get(notification_type, 50)

        # Apply priority level override
        if priority_level == "high":
            base_score = max(base_score, 70)
        elif priority_level == "low":
            base_score = min(base_score, 30)

            # Apply data-driven modifiers
        modifiers = self._calculate_modifiers(notification_type, data)
        final_score = base_score + modifiers

        # Clamp to valid range
        final_score = max(0, min(100, final_score))

        logger.debug(
            "Priority calculated: %s -> %d (base: %d, modifiers: %+d)",
            notification_type.value,
            final_score,
            base_score,
            modifiers,
        )

        return final_score

    def _calculate_modifiers(
        self, notification_type: NotificationType, data: dict[str, Any]
    ) -> int:
        """
        Calculate priority modifiers based on notification data.

        Args:
            notification_type: Type of notification
            data: Notification data

        Returns:
            Modifier value (-20 to +20)
        """
        modifiers = 0

        # ACGME warnings: Higher priority for CRITICAL severity
        if notification_type == NotificationType.ACGME_WARNING:
            severity = data.get("severity", "MEDIUM")
            if severity == "CRITICAL":
                modifiers += 5
            elif severity == "LOW":
                modifiers -= 5

                # Schedule published: Higher priority if violations present
        elif notification_type == NotificationType.SCHEDULE_PUBLISHED:
            violations = data.get("violations_count", 0)
            if violations > 0:
                modifiers += min(10, violations * 2)  # Cap at +10

                # Assignment changes: Higher priority for immediate changes
        elif notification_type == NotificationType.ASSIGNMENT_CHANGED:
            # Check if change is for upcoming shifts
            days_until = data.get("days_until_shift", 999)
            if days_until <= 1:
                modifiers += 15
            elif days_until <= 3:
                modifiers += 10
            elif days_until <= 7:
                modifiers += 5

                # Shift reminders: Increase priority closer to shift time
        elif notification_type == NotificationType.SHIFT_REMINDER_1H:
            modifiers += 20  # Very high priority for imminent shifts

        return max(-20, min(20, modifiers))

    def get_priority_category(self, score: int) -> str:
        """
        Get priority category from numerical score.

        Args:
            score: Priority score (0-100)

        Returns:
            Category string ('critical', 'high', 'normal', 'low')
        """
        if score >= 90:
            return "critical"
        elif score >= 70:
            return "high"
        elif score >= 30:
            return "normal"
        else:
            return "low"

    def should_bypass_quiet_hours(self, score: int) -> bool:
        """
        Determine if notification should bypass quiet hours.

        Args:
            score: Priority score

        Returns:
            True if should bypass quiet hours
        """
        return score >= 90  # CRITICAL notifications bypass quiet hours

    def should_batch(self, score: int) -> bool:
        """
        Determine if notification can be batched.

        Args:
            score: Priority score

        Returns:
            True if can be batched
        """
        return score < 70  # HIGH and CRITICAL are not batched

    def get_delivery_delay_seconds(self, score: int) -> int:
        """
        Get recommended delivery delay based on priority.

        Args:
            score: Priority score

        Returns:
            Delay in seconds (0 for immediate)
        """
        if score >= 90:
            return 0  # Immediate
        elif score >= 70:
            return 60  # 1 minute
        elif score >= 30:
            return 300  # 5 minutes
        else:
            return 900  # 15 minutes
