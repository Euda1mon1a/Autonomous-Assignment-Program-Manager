"""Email tracking (opens and clicks)."""

import hashlib
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailTrackingEvent(BaseModel):
    """Email tracking event."""

    id: UUID = Field(default_factory=uuid4)
    message_id: str
    recipient: str
    event_type: str  # 'open' or 'click'
    user_agent: str | None = None
    ip_address: str | None = None
    link_url: str | None = None  # For click events
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EmailTracker:
    """
    Tracks email opens and clicks.

    Features:
    - Transparent 1x1 pixel for open tracking
    - Link rewriting for click tracking
    - Privacy-preserving (no PII in URLs)
    """

    def __init__(self, tracking_domain: str = "scheduler.local") -> None:
        """
        Initialize email tracker.

        Args:
            tracking_domain: Domain for tracking URLs
        """
        self.tracking_domain = tracking_domain
        self._events: list[EmailTrackingEvent] = []

    def generate_tracking_pixel(self, message_id: str, recipient: str) -> str:
        """
        Generate tracking pixel HTML.

        Args:
            message_id: Email message ID
            recipient: Recipient email

        Returns:
            HTML img tag with tracking pixel
        """
        # Create tracking token
        token = self._generate_token(message_id, recipient)

        pixel_url = f"https://{self.tracking_domain}/track/open/{token}.gif"

        html = f'<img src="{pixel_url}" width="1" height="1" alt="" />'

        logger.debug("Generated tracking pixel for %s", message_id)

        return html

    def rewrite_link(self, message_id: str, recipient: str, original_url: str) -> str:
        """
        Rewrite link for click tracking.

        Args:
            message_id: Email message ID
            recipient: Recipient email
            original_url: Original link URL

        Returns:
            Tracking-enabled URL
        """
        token = self._generate_token(message_id, recipient)

        # Encode original URL
        url_hash = hashlib.sha256(original_url.encode()).hexdigest()[:16]

        tracking_url = f"https://{self.tracking_domain}/track/click/{token}/{url_hash}"

        logger.debug("Rewrote link for tracking: %s", original_url)

        return tracking_url

    def record_open(
        self,
        message_id: str,
        recipient: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> UUID:
        """
        Record email open event.

        Args:
            message_id: Email message ID
            recipient: Recipient email
            user_agent: User agent string
            ip_address: IP address

        Returns:
            Event ID
        """
        event = EmailTrackingEvent(
            message_id=message_id,
            recipient=recipient,
            event_type="open",
            user_agent=user_agent,
            ip_address=ip_address,
        )

        self._events.append(event)

        logger.info("Email opened: %s (%s)", message_id, recipient)

        return event.id

    def record_click(
        self,
        message_id: str,
        recipient: str,
        link_url: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> UUID:
        """
        Record link click event.

        Args:
            message_id: Email message ID
            recipient: Recipient email
            link_url: Clicked link URL
            user_agent: User agent string
            ip_address: IP address

        Returns:
            Event ID
        """
        event = EmailTrackingEvent(
            message_id=message_id,
            recipient=recipient,
            event_type="click",
            link_url=link_url,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        self._events.append(event)

        logger.info("Email link clicked: %s (%s)", message_id, link_url)

        return event.id

    def get_statistics(self, message_id: str | None = None) -> dict[str, Any]:
        """
        Get tracking statistics.

        Args:
            message_id: Optional message ID to filter by

        Returns:
            Statistics dictionary
        """
        events = self._events

        if message_id:
            events = [e for e in events if e.message_id == message_id]

        opens = sum(1 for e in events if e.event_type == "open")
        clicks = sum(1 for e in events if e.event_type == "click")
        unique_recipients = len(set(e.recipient for e in events))

        return {
            "total_events": len(events),
            "opens": opens,
            "clicks": clicks,
            "unique_recipients": unique_recipients,
        }

    def _generate_token(self, message_id: str, recipient: str) -> str:
        """
        Generate tracking token.

        Args:
            message_id: Message ID
            recipient: Recipient email

        Returns:
            Tracking token
        """
        data = f"{message_id}:{recipient}"
        token = hashlib.sha256(data.encode()).hexdigest()[:32]
        return token
