"""Email bounce handling."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class BounceType(str, Enum):
    """Types of email bounces."""

    HARD = "hard"  # Permanent failure (invalid address)
    SOFT = "soft"  # Temporary failure (mailbox full)
    COMPLAINT = "complaint"  # Spam complaint
    BLOCK = "block"  # Blocked by recipient


class BounceEvent(BaseModel):
    """Email bounce event."""

    id: UUID = Field(default_factory=uuid4)
    message_id: str
    recipient: str
    bounce_type: BounceType
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_data: dict[str, Any] | None = None


class BounceHandler:
    """
    Handles email bounces and complaints.

    Features:
    - Track bounce events
    - Maintain suppression list
    - Automatic retry logic for soft bounces
    - Compliance with email best practices
    """

    # Thresholds for suppression
    HARD_BOUNCE_THRESHOLD = 1  # Suppress after 1 hard bounce
    SOFT_BOUNCE_THRESHOLD = 3  # Suppress after 3 soft bounces
    COMPLAINT_THRESHOLD = 1  # Suppress after 1 complaint

    def __init__(self) -> None:
        """Initialize bounce handler."""
        self._events: list[BounceEvent] = []
        self._suppression_list: set[str] = set()

    def record_bounce(
        self,
        message_id: str,
        recipient: str,
        bounce_type: BounceType,
        reason: str,
        raw_data: dict[str, Any] | None = None,
    ) -> UUID:
        """
        Record a bounce event.

        Args:
            message_id: Email message ID
            recipient: Recipient email
            bounce_type: Type of bounce
            reason: Bounce reason
            raw_data: Raw bounce data

        Returns:
            Event ID
        """
        event = BounceEvent(
            message_id=message_id,
            recipient=recipient,
            bounce_type=bounce_type,
            reason=reason,
            raw_data=raw_data,
        )

        self._events.append(event)

        # Check if should suppress
        if self._should_suppress(recipient):
            self._suppression_list.add(recipient)
            logger.warning("Added to suppression list: %s", recipient)

        logger.info(
            "Bounce recorded: %s (%s) - %s",
            recipient,
            bounce_type.value,
            reason,
        )

        return event.id

    def is_suppressed(self, recipient: str) -> bool:
        """
        Check if recipient is suppressed.

        Args:
            recipient: Recipient email

        Returns:
            True if suppressed
        """
        return recipient in self._suppression_list

    def remove_from_suppression(self, recipient: str) -> bool:
        """
        Remove recipient from suppression list.

        Args:
            recipient: Recipient email

        Returns:
            True if removed
        """
        if recipient in self._suppression_list:
            self._suppression_list.remove(recipient)
            logger.info("Removed from suppression list: %s", recipient)
            return True

        return False

    def get_bounce_count(
        self, recipient: str, bounce_type: BounceType | None = None
    ) -> int:
        """
        Get bounce count for recipient.

        Args:
            recipient: Recipient email
            bounce_type: Optional bounce type filter

        Returns:
            Bounce count
        """
        events = [e for e in self._events if e.recipient == recipient]

        if bounce_type:
            events = [e for e in events if e.bounce_type == bounce_type]

        return len(events)

    def _should_suppress(self, recipient: str) -> bool:
        """Determine if recipient should be suppressed."""
        hard_bounces = self.get_bounce_count(recipient, BounceType.HARD)
        soft_bounces = self.get_bounce_count(recipient, BounceType.SOFT)
        complaints = self.get_bounce_count(recipient, BounceType.COMPLAINT)

        return (
            hard_bounces >= self.HARD_BOUNCE_THRESHOLD
            or soft_bounces >= self.SOFT_BOUNCE_THRESHOLD
            or complaints >= self.COMPLAINT_THRESHOLD
        )

    def get_statistics(self) -> dict[str, Any]:
        """Get bounce statistics."""
        return {
            "total_bounces": len(self._events),
            "suppressed_recipients": len(self._suppression_list),
            "hard_bounces": self.get_bounce_count(None, BounceType.HARD),
            "soft_bounces": self.get_bounce_count(None, BounceType.SOFT),
            "complaints": self.get_bounce_count(None, BounceType.COMPLAINT),
        }

    def get_bounce_count(
        self, recipient: str | None, bounce_type: BounceType | None
    ) -> int:
        """Get bounce count with optional filters."""
        events = self._events

        if recipient:
            events = [e for e in events if e.recipient == recipient]

        if bounce_type:
            events = [e for e in events if e.bounce_type == bounce_type]

        return len(events)
