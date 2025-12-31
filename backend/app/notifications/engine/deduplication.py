"""Deduplication engine for notifications."""

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.notifications.notification_types import NotificationType

logger = get_logger(__name__)


class DeduplicationEngine:
    """
    Prevents duplicate notifications from being sent.

    Deduplication strategy:
    1. Generate fingerprint from (recipient, type, key data)
    2. Check if fingerprint was sent within time window
    3. Reject if duplicate, otherwise record and allow

    Time windows vary by notification type:
    - ACGME warnings: 4 hours (don't spam about same violation)
    - Schedule published: 24 hours (one per day max)
    - Assignment changed: 1 hour (but allow multiple distinct changes)
    - Shift reminders: No dedup (each reminder is unique)
    """

    # Default deduplication windows (in minutes) by notification type
    DEFAULT_WINDOWS = {
        NotificationType.ACGME_WARNING: 240,  # 4 hours
        NotificationType.SCHEDULE_PUBLISHED: 1440,  # 24 hours
        NotificationType.ASSIGNMENT_CHANGED: 60,  # 1 hour
        NotificationType.SHIFT_REMINDER_24H: 0,  # No dedup
        NotificationType.SHIFT_REMINDER_1H: 0,  # No dedup
        NotificationType.ABSENCE_APPROVED: 60,  # 1 hour
        NotificationType.ABSENCE_REJECTED: 60,  # 1 hour
    }

    # Fields to include in fingerprint by notification type
    FINGERPRINT_FIELDS = {
        NotificationType.ACGME_WARNING: ["violation_type", "person_name"],
        NotificationType.SCHEDULE_PUBLISHED: ["period"],
        NotificationType.ASSIGNMENT_CHANGED: ["block_name", "rotation_name"],
        NotificationType.SHIFT_REMINDER_24H: ["rotation_name", "start_date"],
        NotificationType.SHIFT_REMINDER_1H: ["rotation_name", "start_time"],
        NotificationType.ABSENCE_APPROVED: ["absence_type", "start_date"],
        NotificationType.ABSENCE_REJECTED: ["absence_type", "start_date"],
    }

    def __init__(self):
        """Initialize the deduplication engine."""
        # In-memory cache: fingerprint -> last_sent_timestamp
        self._cache: dict[str, datetime] = {}

        # Statistics
        self._stats = defaultdict(int)

    def is_duplicate(
        self,
        recipient_id: UUID,
        notification_type: NotificationType,
        data: dict[str, Any],
        window_minutes: int | None = None,
    ) -> bool:
        """
        Check if notification is a duplicate.

        Args:
            recipient_id: UUID of recipient
            notification_type: Type of notification
            data: Notification data
            window_minutes: Optional custom window (overrides default)

        Returns:
            True if duplicate, False if unique
        """
        # Get deduplication window
        window = window_minutes or self.DEFAULT_WINDOWS.get(notification_type, 60)

        # No deduplication if window is 0
        if window == 0:
            return False

        # Generate fingerprint
        fingerprint = self._generate_fingerprint(recipient_id, notification_type, data)

        # Check if fingerprint exists and is within window
        if fingerprint in self._cache:
            last_sent = self._cache[fingerprint]
            age_minutes = (datetime.utcnow() - last_sent).total_seconds() / 60

            if age_minutes < window:
                self._stats["duplicates_blocked"] += 1
                logger.debug(
                    "Duplicate notification blocked: %s (age: %.1f min)",
                    fingerprint,
                    age_minutes,
                )
                return True

        self._stats["unique_notifications"] += 1
        return False

    def record_sent(
        self,
        recipient_id: UUID,
        notification_type: NotificationType,
        data: dict[str, Any],
    ) -> None:
        """
        Record that a notification was sent.

        Args:
            recipient_id: UUID of recipient
            notification_type: Type of notification
            data: Notification data
        """
        fingerprint = self._generate_fingerprint(recipient_id, notification_type, data)
        self._cache[fingerprint] = datetime.utcnow()

        logger.debug("Notification fingerprint recorded: %s", fingerprint)

    def _generate_fingerprint(
        self,
        recipient_id: UUID,
        notification_type: NotificationType,
        data: dict[str, Any],
    ) -> str:
        """
        Generate a unique fingerprint for a notification.

        Args:
            recipient_id: UUID of recipient
            notification_type: Type of notification
            data: Notification data

        Returns:
            SHA256 fingerprint string
        """
        # Get fields to include in fingerprint
        fields = self.FINGERPRINT_FIELDS.get(notification_type, [])

        # Extract relevant data
        fingerprint_data = {
            "recipient_id": str(recipient_id),
            "notification_type": notification_type.value,
        }

        for field in fields:
            if field in data:
                fingerprint_data[field] = data[field]

        # Generate hash
        data_str = json.dumps(fingerprint_data, sort_keys=True)
        fingerprint = hashlib.sha256(data_str.encode()).hexdigest()

        return fingerprint

    def clear_expired(self) -> int:
        """
        Clear expired fingerprints from cache.

        Returns:
            Number of fingerprints cleared
        """
        now = datetime.utcnow()
        max_age = timedelta(days=7)  # Keep fingerprints for 7 days max

        expired = [
            fp
            for fp, timestamp in self._cache.items()
            if (now - timestamp) > max_age
        ]

        for fp in expired:
            del self._cache[fp]

        if expired:
            logger.info("Cleared %d expired fingerprints", len(expired))

        return len(expired)

    def get_cache_size(self) -> int:
        """
        Get the number of fingerprints in cache.

        Returns:
            Cache size
        """
        return len(self._cache)

    def get_statistics(self) -> dict[str, Any]:
        """
        Get deduplication statistics.

        Returns:
            Dictionary of statistics
        """
        total = self._stats["unique_notifications"] + self._stats["duplicates_blocked"]
        duplicate_rate = (
            self._stats["duplicates_blocked"] / total * 100 if total > 0 else 0
        )

        return {
            "cache_size": len(self._cache),
            "unique_notifications": self._stats["unique_notifications"],
            "duplicates_blocked": self._stats["duplicates_blocked"],
            "duplicate_rate_percent": round(duplicate_rate, 2),
        }

    def clear_cache(self) -> None:
        """Clear all fingerprints from cache."""
        self._cache.clear()
        logger.info("Deduplication cache cleared")

    def reset_statistics(self) -> None:
        """Reset statistics counters."""
        self._stats.clear()
        logger.info("Deduplication statistics reset")
