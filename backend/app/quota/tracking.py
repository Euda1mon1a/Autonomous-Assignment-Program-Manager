"""
Usage tracking for API quotas.

This module provides Redis-based tracking of API usage for quota enforcement.
Tracks usage on daily and monthly basis with automatic reset.
"""

import logging
from datetime import datetime, timedelta

import redis

from app.quota.policies import QuotaPolicy

logger = logging.getLogger(__name__)


class QuotaTracker:
    """
    Redis-based quota usage tracker.

    Tracks API usage across different time periods and resource types.
    Uses Redis for fast, distributed tracking with automatic expiration.
    """

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize quota tracker.

        Args:
            redis_client: Redis client for usage storage
        """
        self.redis = redis_client

    def _get_daily_key(self, user_id: str, resource_type: str = "api") -> str:
        """
        Get Redis key for daily quota tracking.

        Args:
            user_id: User ID
            resource_type: Type of resource (api, schedule, export, report)

        Returns:
            str: Redis key for daily quota
        """
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return f"quota:daily:{resource_type}:{user_id}:{date_str}"

    def _get_monthly_key(self, user_id: str, resource_type: str = "api") -> str:
        """
        Get Redis key for monthly quota tracking.

        Args:
            user_id: User ID
            resource_type: Type of resource (api, schedule, export, report)

        Returns:
            str: Redis key for monthly quota
        """
        month_str = datetime.utcnow().strftime("%Y-%m")
        return f"quota:monthly:{resource_type}:{user_id}:{month_str}"

    def _get_ttl_daily(self) -> int:
        """
        Get TTL in seconds for daily quota keys.

        Returns:
            int: Seconds until end of day + 1 hour buffer
        """
        now = datetime.utcnow()
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
        ttl_seconds = int((end_of_day - now).total_seconds()) + 3600  # +1 hour buffer
        return ttl_seconds

    def _get_ttl_monthly(self) -> int:
        """
        Get TTL in seconds for monthly quota keys.

        Returns:
            int: Seconds until end of month + 1 day buffer
        """
        now = datetime.utcnow()
        # Get last day of current month
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)

        end_of_month = next_month - timedelta(seconds=1)
        ttl_seconds = int((end_of_month - now).total_seconds()) + 86400  # +1 day buffer
        return ttl_seconds

    def increment_usage(
        self,
        user_id: str,
        resource_type: str = "api",
        amount: int = 1,
    ) -> tuple[int, int]:
        """
        Increment usage counters for a user.

        Args:
            user_id: User ID
            resource_type: Type of resource being used
            amount: Amount to increment by (default: 1)

        Returns:
            tuple[int, int]: (daily_usage, monthly_usage) after increment
        """
        daily_key = self._get_daily_key(user_id, resource_type)
        monthly_key = self._get_monthly_key(user_id, resource_type)

        # Use pipeline for atomic operations
        pipe = self.redis.pipeline()

        # Increment counters
        pipe.incrby(daily_key, amount)
        pipe.incrby(monthly_key, amount)

        # Set TTL if keys are new
        pipe.expire(daily_key, self._get_ttl_daily())
        pipe.expire(monthly_key, self._get_ttl_monthly())

        results = pipe.execute()

        daily_usage = results[0]
        monthly_usage = results[1]

        logger.debug(
            f"Incremented {resource_type} quota for user {user_id}: "
            f"daily={daily_usage}, monthly={monthly_usage}"
        )

        return daily_usage, monthly_usage

    def get_usage(
        self,
        user_id: str,
        resource_type: str = "api",
    ) -> tuple[int, int]:
        """
        Get current usage for a user.

        Args:
            user_id: User ID
            resource_type: Type of resource

        Returns:
            tuple[int, int]: (daily_usage, monthly_usage)
        """
        daily_key = self._get_daily_key(user_id, resource_type)
        monthly_key = self._get_monthly_key(user_id, resource_type)

        pipe = self.redis.pipeline()
        pipe.get(daily_key)
        pipe.get(monthly_key)
        results = pipe.execute()

        daily_usage = int(results[0] or 0)
        monthly_usage = int(results[1] or 0)

        return daily_usage, monthly_usage

    def get_remaining(
        self,
        user_id: str,
        policy: QuotaPolicy,
        resource_type: str = "api",
    ) -> tuple[int, int]:
        """
        Get remaining quota for a user.

        Args:
            user_id: User ID
            policy: Quota policy
            resource_type: Type of resource

        Returns:
            tuple[int, int]: (daily_remaining, monthly_remaining)
        """
        daily_usage, monthly_usage = self.get_usage(user_id, resource_type)

        # Get limits based on resource type
        if resource_type == "schedule":
            daily_limit = policy.schedule_generation_daily
            monthly_limit = policy.schedule_generation_monthly
        elif resource_type == "export":
            daily_limit = policy.export_daily
            monthly_limit = policy.export_monthly
        elif resource_type == "report":
            daily_limit = policy.report_daily
            monthly_limit = policy.report_monthly
        else:  # "api" or default
            daily_limit = policy.daily_limit
            monthly_limit = policy.monthly_limit

        # Calculate remaining with overage
        if policy.allow_overage:
            daily_limit_with_overage = int(
                daily_limit * (1 + policy.overage_percentage)
            )
            monthly_limit_with_overage = int(
                monthly_limit * (1 + policy.overage_percentage)
            )
        else:
            daily_limit_with_overage = daily_limit
            monthly_limit_with_overage = monthly_limit

        daily_remaining = max(0, daily_limit_with_overage - daily_usage)
        monthly_remaining = max(0, monthly_limit_with_overage - monthly_usage)

        return daily_remaining, monthly_remaining

    def check_quota(
        self,
        user_id: str,
        policy: QuotaPolicy,
        resource_type: str = "api",
        amount: int = 1,
    ) -> tuple[bool, str | None]:
        """
        Check if user has sufficient quota.

        Args:
            user_id: User ID
            policy: Quota policy
            resource_type: Type of resource
            amount: Amount needed

        Returns:
            tuple[bool, Optional[str]]: (is_allowed, reason_if_denied)
        """
        daily_usage, monthly_usage = self.get_usage(user_id, resource_type)

        # Get limits based on resource type
        if resource_type == "schedule":
            daily_limit = policy.schedule_generation_daily
            monthly_limit = policy.schedule_generation_monthly
        elif resource_type == "export":
            daily_limit = policy.export_daily
            monthly_limit = policy.export_monthly
        elif resource_type == "report":
            daily_limit = policy.report_daily
            monthly_limit = policy.report_monthly
        else:  # "api" or default
            daily_limit = policy.daily_limit
            monthly_limit = policy.monthly_limit

        # Apply overage if allowed
        if policy.allow_overage:
            daily_limit = int(daily_limit * (1 + policy.overage_percentage))
            monthly_limit = int(monthly_limit * (1 + policy.overage_percentage))

        # Check daily quota
        if daily_usage + amount > daily_limit:
            return (
                False,
                f"Daily {resource_type} quota exceeded ({daily_limit} per day)",
            )

        # Check monthly quota
        if monthly_usage + amount > monthly_limit:
            return (
                False,
                f"Monthly {resource_type} quota exceeded ({monthly_limit} per month)",
            )

        return True, None

    def get_reset_times(self) -> tuple[datetime, datetime]:
        """
        Get reset times for daily and monthly quotas.

        Returns:
            tuple[datetime, datetime]: (daily_reset, monthly_reset)
        """
        now = datetime.utcnow()

        # Daily reset: midnight UTC
        daily_reset = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Monthly reset: first day of next month at midnight UTC
        if now.month == 12:
            monthly_reset = now.replace(
                year=now.year + 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        else:
            monthly_reset = now.replace(
                month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0
            )

        return daily_reset, monthly_reset

    def reset_quota(
        self,
        user_id: str,
        resource_type: str = "api",
        reset_daily: bool = True,
        reset_monthly: bool = False,
    ) -> bool:
        """
        Manually reset quota for a user (admin operation).

        Args:
            user_id: User ID
            resource_type: Type of resource
            reset_daily: Reset daily quota
            reset_monthly: Reset monthly quota

        Returns:
            bool: True if reset successful
        """
        try:
            if reset_daily:
                daily_key = self._get_daily_key(user_id, resource_type)
                self.redis.delete(daily_key)
                logger.info(f"Reset daily {resource_type} quota for user {user_id}")

            if reset_monthly:
                monthly_key = self._get_monthly_key(user_id, resource_type)
                self.redis.delete(monthly_key)
                logger.info(f"Reset monthly {resource_type} quota for user {user_id}")

            return True
        except Exception as e:
            logger.error(f"Failed to reset quota for user {user_id}: {e}")
            return False

    def get_usage_percentage(
        self,
        user_id: str,
        policy: QuotaPolicy,
        resource_type: str = "api",
    ) -> tuple[float, float]:
        """
        Get usage as percentage of quota.

        Args:
            user_id: User ID
            policy: Quota policy
            resource_type: Type of resource

        Returns:
            tuple[float, float]: (daily_percentage, monthly_percentage)
        """
        daily_usage, monthly_usage = self.get_usage(user_id, resource_type)

        # Get limits
        if resource_type == "schedule":
            daily_limit = policy.schedule_generation_daily
            monthly_limit = policy.schedule_generation_monthly
        elif resource_type == "export":
            daily_limit = policy.export_daily
            monthly_limit = policy.export_monthly
        elif resource_type == "report":
            daily_limit = policy.report_daily
            monthly_limit = policy.report_monthly
        else:
            daily_limit = policy.daily_limit
            monthly_limit = policy.monthly_limit

        daily_percentage = (daily_usage / daily_limit * 100) if daily_limit > 0 else 0
        monthly_percentage = (
            (monthly_usage / monthly_limit * 100) if monthly_limit > 0 else 0
        )

        return daily_percentage, monthly_percentage

    def should_alert(
        self,
        user_id: str,
        policy: QuotaPolicy,
        resource_type: str = "api",
    ) -> tuple[bool, str | None]:
        """
        Check if usage alerts should be triggered.

        Args:
            user_id: User ID
            policy: Quota policy
            resource_type: Type of resource

        Returns:
            tuple[bool, Optional[str]]: (should_alert, alert_level)
                alert_level: "warning" or "critical" or None
        """
        daily_pct, monthly_pct = self.get_usage_percentage(
            user_id, policy, resource_type
        )

        # Use the higher percentage
        max_pct = max(daily_pct, monthly_pct) / 100.0

        if max_pct >= policy.critical_threshold:
            return True, "critical"
        elif max_pct >= policy.warning_threshold:
            return True, "warning"

        return False, None
