"""Rate limiting for notifications."""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.notifications.notification_types import NotificationType

logger = get_logger(__name__)


class RateLimitBucket:
    """
    Token bucket for rate limiting.

    Attributes:
        capacity: Maximum tokens in bucket
        tokens: Current token count
        refill_rate: Tokens added per minute
        last_refill: Last refill timestamp
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize rate limit bucket.

        Args:
            capacity: Maximum tokens
            refill_rate: Tokens per minute
        """
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate
        self.last_refill = datetime.utcnow()

    def refill(self) -> None:
        """Refill tokens based on time elapsed."""
        now = datetime.utcnow()
        elapsed = (now - self.last_refill).total_seconds() / 60  # minutes

        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def consume(self, count: int = 1) -> bool:
        """
        Try to consume tokens.

        Args:
            count: Number of tokens to consume

        Returns:
            True if tokens consumed, False if insufficient
        """
        self.refill()

        if self.tokens >= count:
            self.tokens -= count
            return True

        return False


class NotificationRateLimiter:
    """
    Rate limiter for notifications to prevent spam.

    Rate Limiting Strategy:
    1. Per-user global limit (e.g., 100 notifications/hour)
    2. Per-user per-type limit (e.g., 10 ACGME warnings/hour)
    3. Per-channel limit (e.g., 50 emails/hour per user)

    Uses token bucket algorithm:
    - Each user/type/channel has a bucket
    - Buckets refill over time
    - Notifications consume tokens
    - Reject if insufficient tokens
    """

    # Global rate limits (per user)
    GLOBAL_LIMIT_PER_HOUR = 100

    # Per-type rate limits (per user per hour)
    TYPE_LIMITS_PER_HOUR = {
        NotificationType.ACGME_WARNING: 10,
        NotificationType.SCHEDULE_PUBLISHED: 5,
        NotificationType.ASSIGNMENT_CHANGED: 20,
        NotificationType.SHIFT_REMINDER_24H: 10,
        NotificationType.SHIFT_REMINDER_1H: 10,
        NotificationType.ABSENCE_APPROVED: 10,
        NotificationType.ABSENCE_REJECTED: 10,
    }

    # Per-channel rate limits (per user per hour)
    CHANNEL_LIMITS_PER_HOUR = {
        "in_app": 100,
        "email": 50,
        "sms": 20,
        "webhook": 50,
    }

    def __init__(self):
        """Initialize the rate limiter."""
        # User-level buckets: user_id -> RateLimitBucket
        self._user_buckets: dict[UUID, RateLimitBucket] = {}

        # Type-level buckets: (user_id, type) -> RateLimitBucket
        self._type_buckets: dict[tuple[UUID, str], RateLimitBucket] = {}

        # Channel-level buckets: (user_id, channel) -> RateLimitBucket
        self._channel_buckets: dict[tuple[UUID, str], RateLimitBucket] = {}

        # Statistics
        self._stats = defaultdict(int)

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def check_rate_limit(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        channel: str = "in_app",
    ) -> bool:
        """
        Check if notification is within rate limits.

        Args:
            user_id: UUID of user
            notification_type: Type of notification
            channel: Channel to check

        Returns:
            True if within limits, False if rate limited
        """
        async with self._lock:
            # Check global user limit
            if not self._check_user_limit(user_id):
                self._stats["global_limits_hit"] += 1
                logger.warning("Global rate limit hit for user %s", user_id)
                return False

            # Check per-type limit
            if not self._check_type_limit(user_id, notification_type):
                self._stats["type_limits_hit"] += 1
                logger.warning(
                    "Type rate limit hit for user %s, type %s",
                    user_id,
                    notification_type.value,
                )
                return False

            # Check per-channel limit
            if not self._check_channel_limit(user_id, channel):
                self._stats["channel_limits_hit"] += 1
                logger.warning(
                    "Channel rate limit hit for user %s, channel %s",
                    user_id,
                    channel,
                )
                return False

            self._stats["notifications_allowed"] += 1
            return True

    def _check_user_limit(self, user_id: UUID) -> bool:
        """Check global user rate limit."""
        if user_id not in self._user_buckets:
            # Create new bucket: 100 notifications/hour = 100 capacity, 100/60 refill rate
            self._user_buckets[user_id] = RateLimitBucket(
                capacity=self.GLOBAL_LIMIT_PER_HOUR,
                refill_rate=self.GLOBAL_LIMIT_PER_HOUR / 60,
            )

        bucket = self._user_buckets[user_id]
        return bucket.consume(1)

    def _check_type_limit(
        self, user_id: UUID, notification_type: NotificationType
    ) -> bool:
        """Check per-type rate limit."""
        key = (user_id, notification_type.value)

        if key not in self._type_buckets:
            limit = self.TYPE_LIMITS_PER_HOUR.get(notification_type, 20)
            self._type_buckets[key] = RateLimitBucket(
                capacity=limit,
                refill_rate=limit / 60,
            )

        bucket = self._type_buckets[key]
        return bucket.consume(1)

    def _check_channel_limit(self, user_id: UUID, channel: str) -> bool:
        """Check per-channel rate limit."""
        key = (user_id, channel)

        if key not in self._channel_buckets:
            limit = self.CHANNEL_LIMITS_PER_HOUR.get(channel, 50)
            self._channel_buckets[key] = RateLimitBucket(
                capacity=limit,
                refill_rate=limit / 60,
            )

        bucket = self._channel_buckets[key]
        return bucket.consume(1)

    async def reset_user_limits(self, user_id: UUID) -> None:
        """
        Reset all rate limits for a user.

        Args:
            user_id: UUID of user
        """
        async with self._lock:
            if user_id in self._user_buckets:
                del self._user_buckets[user_id]

            # Remove type buckets
            type_keys = [k for k in self._type_buckets.keys() if k[0] == user_id]
            for key in type_keys:
                del self._type_buckets[key]

            # Remove channel buckets
            channel_keys = [k for k in self._channel_buckets.keys() if k[0] == user_id]
            for key in channel_keys:
                del self._channel_buckets[key]

            logger.info("Reset all rate limits for user %s", user_id)

    async def get_remaining_quota(
        self, user_id: UUID, notification_type: NotificationType | None = None
    ) -> dict[str, float]:
        """
        Get remaining quota for a user.

        Args:
            user_id: UUID of user
            notification_type: Optional type to check

        Returns:
            Dictionary with remaining tokens
        """
        async with self._lock:
            quota = {}

            # Global quota
            if user_id in self._user_buckets:
                bucket = self._user_buckets[user_id]
                bucket.refill()
                quota["global"] = bucket.tokens
            else:
                quota["global"] = self.GLOBAL_LIMIT_PER_HOUR

            # Type-specific quota
            if notification_type:
                key = (user_id, notification_type.value)
                if key in self._type_buckets:
                    bucket = self._type_buckets[key]
                    bucket.refill()
                    quota[f"type_{notification_type.value}"] = bucket.tokens
                else:
                    quota[f"type_{notification_type.value}"] = self.TYPE_LIMITS_PER_HOUR.get(
                        notification_type, 20
                    )

            return quota

    async def get_statistics(self) -> dict[str, Any]:
        """
        Get rate limiter statistics.

        Returns:
            Dictionary of statistics
        """
        async with self._lock:
            total_requests = (
                self._stats["notifications_allowed"]
                + self._stats["global_limits_hit"]
                + self._stats["type_limits_hit"]
                + self._stats["channel_limits_hit"]
            )

            rate_limited = (
                self._stats["global_limits_hit"]
                + self._stats["type_limits_hit"]
                + self._stats["channel_limits_hit"]
            )

            return {
                "active_user_buckets": len(self._user_buckets),
                "active_type_buckets": len(self._type_buckets),
                "active_channel_buckets": len(self._channel_buckets),
                "notifications_allowed": self._stats["notifications_allowed"],
                "global_limits_hit": self._stats["global_limits_hit"],
                "type_limits_hit": self._stats["type_limits_hit"],
                "channel_limits_hit": self._stats["channel_limits_hit"],
                "total_requests": total_requests,
                "rate_limited_percent": (
                    round(rate_limited / total_requests * 100, 2)
                    if total_requests > 0
                    else 0
                ),
            }

    async def cleanup_expired(self) -> int:
        """
        Clean up buckets that haven't been used recently.

        Returns:
            Number of buckets cleaned up
        """
        async with self._lock:
            now = datetime.utcnow()
            max_age = timedelta(hours=24)

            cleaned = 0

            # Clean user buckets
            expired_users = [
                user_id
                for user_id, bucket in self._user_buckets.items()
                if (now - bucket.last_refill) > max_age
            ]
            for user_id in expired_users:
                del self._user_buckets[user_id]
                cleaned += 1

            # Clean type buckets
            expired_types = [
                key
                for key, bucket in self._type_buckets.items()
                if (now - bucket.last_refill) > max_age
            ]
            for key in expired_types:
                del self._type_buckets[key]
                cleaned += 1

            # Clean channel buckets
            expired_channels = [
                key
                for key, bucket in self._channel_buckets.items()
                if (now - bucket.last_refill) > max_age
            ]
            for key in expired_channels:
                del self._channel_buckets[key]
                cleaned += 1

            if cleaned > 0:
                logger.info("Cleaned up %d expired rate limit buckets", cleaned)

            return cleaned
