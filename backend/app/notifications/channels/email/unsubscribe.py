"""Unsubscribe management."""

import hashlib
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class UnsubscribeRecord(BaseModel):
    """Unsubscribe record."""

    email: str
    notification_types: list[str] = Field(default_factory=list)  # Empty = all types
    unsubscribed_at: datetime = Field(default_factory=datetime.utcnow)
    reason: str | None = None


class UnsubscribeManager:
    """
    Manages email unsubscribes.

    Features:
    - One-click unsubscribe
    - Selective unsubscribe by type
    - Unsubscribe link generation
    - Compliance with CAN-SPAM
    """

    def __init__(self, unsubscribe_domain: str = "scheduler.local") -> None:
        """
        Initialize unsubscribe manager.

        Args:
            unsubscribe_domain: Domain for unsubscribe links
        """
        self.unsubscribe_domain = unsubscribe_domain
        self._unsubscribes: dict[str, UnsubscribeRecord] = {}

    def generate_unsubscribe_link(
        self, recipient: str, notification_type: str | None = None
    ) -> str:
        """
        Generate unsubscribe link.

        Args:
            recipient: Recipient email
            notification_type: Optional specific type to unsubscribe from

        Returns:
            Unsubscribe URL
        """
        token = self._generate_token(recipient)

        if notification_type:
            url = f"https://{self.unsubscribe_domain}/unsubscribe/{token}?type={notification_type}"
        else:
            url = f"https://{self.unsubscribe_domain}/unsubscribe/{token}"

        return url

    def unsubscribe(
        self,
        email: str,
        notification_types: list[str] | None = None,
        reason: str | None = None,
    ) -> None:
        """
        Unsubscribe a recipient.

        Args:
            email: Recipient email
            notification_types: Specific types to unsubscribe (None = all)
            reason: Optional unsubscribe reason
        """
        if email in self._unsubscribes:
            record = self._unsubscribes[email]

            if notification_types:
                # Add to existing types
                for ntype in notification_types:
                    if ntype not in record.notification_types:
                        record.notification_types.append(ntype)
            else:
                # Unsubscribe from all
                record.notification_types = []

            if reason:
                record.reason = reason

            logger.info("Updated unsubscribe: %s", email)

        else:
            # Create new record
            record = UnsubscribeRecord(
                email=email,
                notification_types=notification_types or [],
                reason=reason,
            )
            self._unsubscribes[email] = record

            logger.info("New unsubscribe: %s", email)

    def is_unsubscribed(self, email: str, notification_type: str | None = None) -> bool:
        """
        Check if recipient is unsubscribed.

        Args:
            email: Recipient email
            notification_type: Optional specific type to check

        Returns:
            True if unsubscribed
        """
        if email not in self._unsubscribes:
            return False

        record = self._unsubscribes[email]

        # Empty list means unsubscribed from all
        if not record.notification_types:
            return True

            # Check specific type
        if notification_type:
            return notification_type in record.notification_types

        return False

    def resubscribe(
        self, email: str, notification_types: list[str] | None = None
    ) -> bool:
        """
        Resubscribe a recipient.

        Args:
            email: Recipient email
            notification_types: Specific types to resubscribe (None = all)

        Returns:
            True if resubscribed
        """
        if email not in self._unsubscribes:
            return False

        if notification_types:
            # Remove specific types
            record = self._unsubscribes[email]
            record.notification_types = [
                t for t in record.notification_types if t not in notification_types
            ]
        else:
            # Remove completely
            del self._unsubscribes[email]

        logger.info("Resubscribed: %s", email)
        return True

    def get_statistics(self) -> dict[str, Any]:
        """Get unsubscribe statistics."""
        total = len(self._unsubscribes)
        all_types = sum(
            1 for r in self._unsubscribes.values() if not r.notification_types
        )
        partial = total - all_types

        return {
            "total_unsubscribes": total,
            "unsubscribed_from_all": all_types,
            "partial_unsubscribes": partial,
        }

    def _generate_token(self, email: str) -> str:
        """Generate unsubscribe token."""
        token = hashlib.sha256(email.encode()).hexdigest()[:32]
        return token
