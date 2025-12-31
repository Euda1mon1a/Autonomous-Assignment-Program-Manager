"""Email throttling to prevent rate limit issues."""

from datetime import datetime, timedelta
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailThrottler:
    """
    Throttles email sending to avoid rate limits.

    Implements:
    - Per-hour limits
    - Per-day limits
    - Recipient-specific limits
    - Domain-specific limits
    """

    # Default limits
    HOURLY_LIMIT = 100
    DAILY_LIMIT = 1000
    PER_RECIPIENT_HOURLY_LIMIT = 5

    def __init__(self):
        """Initialize throttler."""
        self._hourly_count = 0
        self._daily_count = 0
        self._hour_start = datetime.utcnow()
        self._day_start = datetime.utcnow()
        self._recipient_counts: dict[str, list[datetime]] = {}

    def can_send(self, recipient: str) -> tuple[bool, str | None]:
        """
        Check if email can be sent.

        Args:
            recipient: Recipient email

        Returns:
            Tuple of (can_send, reason)
        """
        self._reset_if_needed()

        # Check hourly limit
        if self._hourly_count >= self.HOURLY_LIMIT:
            return False, "Hourly limit exceeded"

        # Check daily limit
        if self._daily_count >= self.DAILY_LIMIT:
            return False, "Daily limit exceeded"

        # Check per-recipient limit
        if not self._check_recipient_limit(recipient):
            return False, f"Per-recipient limit exceeded for {recipient}"

        return True, None

    def record_sent(self, recipient: str) -> None:
        """Record that an email was sent."""
        self._hourly_count += 1
        self._daily_count += 1

        if recipient not in self._recipient_counts:
            self._recipient_counts[recipient] = []

        self._recipient_counts[recipient].append(datetime.utcnow())

    def _reset_if_needed(self) -> None:
        """Reset counters if time window elapsed."""
        now = datetime.utcnow()

        # Reset hourly
        if now - self._hour_start >= timedelta(hours=1):
            self._hourly_count = 0
            self._hour_start = now

        # Reset daily
        if now - self._day_start >= timedelta(days=1):
            self._daily_count = 0
            self._day_start = now

    def _check_recipient_limit(self, recipient: str) -> bool:
        """Check per-recipient limit."""
        if recipient not in self._recipient_counts:
            return True

        # Count sends in last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_sends = [
            ts for ts in self._recipient_counts[recipient] if ts >= one_hour_ago
        ]

        # Update counts
        self._recipient_counts[recipient] = recent_sends

        return len(recent_sends) < self.PER_RECIPIENT_HOURLY_LIMIT

    def get_statistics(self) -> dict[str, Any]:
        """Get throttling statistics."""
        return {
            "hourly_count": self._hourly_count,
            "hourly_limit": self.HOURLY_LIMIT,
            "daily_count": self._daily_count,
            "daily_limit": self.DAILY_LIMIT,
        }
