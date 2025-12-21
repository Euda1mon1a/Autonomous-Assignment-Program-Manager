"""
Quota manager - main service for quota management.

This module provides the main QuotaManager service that orchestrates
quota enforcement, tracking, alerts, and reporting.
"""
import logging
from datetime import datetime
from typing import Optional

import redis

from app.quota.policies import QuotaPolicy, get_policy_for_role, create_custom_policy
from app.quota.tracking import QuotaTracker

logger = logging.getLogger(__name__)


class QuotaExceededError(Exception):
    """Raised when quota is exceeded."""
    def __init__(self, message: str, daily_limit: int, monthly_limit: int):
        self.message = message
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        super().__init__(self.message)


class QuotaManager:
    """
    Main quota management service.

    Provides high-level quota management operations including:
    - Quota enforcement
    - Usage tracking
    - Custom quota assignment
    - Alert generation
    - Usage reports
    """

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize quota manager.

        Args:
            redis_client: Redis client for quota storage
        """
        self.redis = redis_client
        self.tracker = QuotaTracker(redis_client)

    def _get_custom_policy_key(self, user_id: str) -> str:
        """Get Redis key for custom policy storage."""
        return f"quota:custom_policy:{user_id}"

    def get_policy(self, user_id: str, user_role: str) -> QuotaPolicy:
        """
        Get quota policy for a user.

        Checks for custom policy first, falls back to role-based policy.

        Args:
            user_id: User ID
            user_role: User role

        Returns:
            QuotaPolicy: Applicable quota policy
        """
        # Check for custom policy
        custom_policy_key = self._get_custom_policy_key(user_id)
        custom_data = self.redis.hgetall(custom_policy_key)

        if custom_data:
            # Decode and create custom policy
            try:
                return create_custom_policy(
                    daily_limit=int(custom_data.get(b"daily_limit", 0)),
                    monthly_limit=int(custom_data.get(b"monthly_limit", 0)),
                    schedule_generation_daily=int(
                        custom_data.get(b"schedule_generation_daily", 0)
                    ),
                    schedule_generation_monthly=int(
                        custom_data.get(b"schedule_generation_monthly", 0)
                    ),
                    export_daily=int(custom_data.get(b"export_daily", 0)),
                    export_monthly=int(custom_data.get(b"export_monthly", 0)),
                    report_daily=int(custom_data.get(b"report_daily", 0)),
                    report_monthly=int(custom_data.get(b"report_monthly", 0)),
                    allow_overage=custom_data.get(b"allow_overage", b"0") == b"1",
                    overage_percentage=float(
                        custom_data.get(b"overage_percentage", b"0.0")
                    ),
                )
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to parse custom policy for user {user_id}: {e}")
                # Fall through to role-based policy

        # Return role-based policy
        return get_policy_for_role(user_role)

    def set_custom_policy(
        self,
        user_id: str,
        policy: QuotaPolicy,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Set custom quota policy for a user (admin operation).

        Args:
            user_id: User ID
            policy: Custom quota policy
            ttl_seconds: Optional expiration time in seconds

        Returns:
            bool: True if successful
        """
        try:
            custom_policy_key = self._get_custom_policy_key(user_id)

            # Store policy as hash
            policy_data = {
                "daily_limit": policy.daily_limit,
                "monthly_limit": policy.monthly_limit,
                "schedule_generation_daily": policy.schedule_generation_daily,
                "schedule_generation_monthly": policy.schedule_generation_monthly,
                "export_daily": policy.export_daily,
                "export_monthly": policy.export_monthly,
                "report_daily": policy.report_daily,
                "report_monthly": policy.report_monthly,
                "allow_overage": 1 if policy.allow_overage else 0,
                "overage_percentage": policy.overage_percentage,
            }

            self.redis.hset(custom_policy_key, mapping=policy_data)

            if ttl_seconds:
                self.redis.expire(custom_policy_key, ttl_seconds)

            logger.info(f"Set custom quota policy for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to set custom policy for user {user_id}: {e}")
            return False

    def remove_custom_policy(self, user_id: str) -> bool:
        """
        Remove custom quota policy for a user.

        Args:
            user_id: User ID

        Returns:
            bool: True if successful
        """
        try:
            custom_policy_key = self._get_custom_policy_key(user_id)
            self.redis.delete(custom_policy_key)
            logger.info(f"Removed custom quota policy for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove custom policy for user {user_id}: {e}")
            return False

    def enforce_quota(
        self,
        user_id: str,
        user_role: str,
        resource_type: str = "api",
        amount: int = 1,
    ) -> None:
        """
        Enforce quota limits before allowing an operation.

        Args:
            user_id: User ID
            user_role: User role
            resource_type: Type of resource being accessed
            amount: Amount of resource being requested

        Raises:
            QuotaExceededError: If quota is exceeded
        """
        policy = self.get_policy(user_id, user_role)
        is_allowed, reason = self.tracker.check_quota(
            user_id, policy, resource_type, amount
        )

        if not is_allowed:
            # Get limits for error message
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

            raise QuotaExceededError(reason or "Quota exceeded", daily_limit, monthly_limit)

    def record_usage(
        self,
        user_id: str,
        user_role: str,
        resource_type: str = "api",
        amount: int = 1,
    ) -> tuple[int, int]:
        """
        Record usage and return current totals.

        Args:
            user_id: User ID
            user_role: User role
            resource_type: Type of resource
            amount: Amount to record

        Returns:
            tuple[int, int]: (daily_usage, monthly_usage) after recording
        """
        daily_usage, monthly_usage = self.tracker.increment_usage(
            user_id, resource_type, amount
        )

        # Check if we should send alerts
        policy = self.get_policy(user_id, user_role)
        should_alert, alert_level = self.tracker.should_alert(
            user_id, policy, resource_type
        )

        if should_alert:
            self._trigger_alert(user_id, resource_type, alert_level, policy)

        return daily_usage, monthly_usage

    def _trigger_alert(
        self,
        user_id: str,
        resource_type: str,
        alert_level: str,
        policy: QuotaPolicy,
    ) -> None:
        """
        Trigger usage alert.

        Args:
            user_id: User ID
            resource_type: Type of resource
            alert_level: Alert level ("warning" or "critical")
            policy: Quota policy
        """
        daily_pct, monthly_pct = self.tracker.get_usage_percentage(
            user_id, policy, resource_type
        )

        logger.warning(
            f"Quota alert for user {user_id}: {alert_level} level "
            f"({resource_type}, daily={daily_pct:.1f}%, monthly={monthly_pct:.1f}%)"
        )

        # Store alert in Redis for retrieval
        alert_key = f"quota:alert:{user_id}:{resource_type}"
        alert_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_level": alert_level,
            "resource_type": resource_type,
            "daily_percentage": daily_pct,
            "monthly_percentage": monthly_pct,
        }
        self.redis.hset(alert_key, mapping=alert_data)
        self.redis.expire(alert_key, 86400)  # 24 hour expiry

    def get_usage_summary(
        self,
        user_id: str,
        user_role: str,
    ) -> dict:
        """
        Get comprehensive usage summary for a user.

        Args:
            user_id: User ID
            user_role: User role

        Returns:
            dict: Usage summary with all resource types
        """
        policy = self.get_policy(user_id, user_role)
        daily_reset, monthly_reset = self.tracker.get_reset_times()

        summary = {
            "user_id": user_id,
            "policy_type": policy.policy_type.value,
            "reset_times": {
                "daily": daily_reset.isoformat(),
                "monthly": monthly_reset.isoformat(),
            },
            "resources": {},
        }

        # Get usage for each resource type
        for resource_type in ["api", "schedule", "export", "report"]:
            daily_usage, monthly_usage = self.tracker.get_usage(user_id, resource_type)
            daily_remaining, monthly_remaining = self.tracker.get_remaining(
                user_id, policy, resource_type
            )
            daily_pct, monthly_pct = self.tracker.get_usage_percentage(
                user_id, policy, resource_type
            )

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

            summary["resources"][resource_type] = {
                "limits": {
                    "daily": daily_limit,
                    "monthly": monthly_limit,
                },
                "usage": {
                    "daily": daily_usage,
                    "monthly": monthly_usage,
                },
                "remaining": {
                    "daily": daily_remaining,
                    "monthly": monthly_remaining,
                },
                "percentage": {
                    "daily": round(daily_pct, 2),
                    "monthly": round(monthly_pct, 2),
                },
            }

        return summary

    def reset_user_quota(
        self,
        user_id: str,
        resource_type: Optional[str] = None,
        reset_daily: bool = True,
        reset_monthly: bool = False,
    ) -> bool:
        """
        Reset quota for a user (admin operation).

        Args:
            user_id: User ID
            resource_type: Specific resource type to reset (None = all)
            reset_daily: Reset daily quota
            reset_monthly: Reset monthly quota

        Returns:
            bool: True if successful
        """
        if resource_type:
            resource_types = [resource_type]
        else:
            resource_types = ["api", "schedule", "export", "report"]

        success = True
        for res_type in resource_types:
            result = self.tracker.reset_quota(
                user_id, res_type, reset_daily, reset_monthly
            )
            success = success and result

        return success

    def get_alerts(self, user_id: str) -> list[dict]:
        """
        Get recent alerts for a user.

        Args:
            user_id: User ID

        Returns:
            list[dict]: List of recent alerts
        """
        alerts = []
        for resource_type in ["api", "schedule", "export", "report"]:
            alert_key = f"quota:alert:{user_id}:{resource_type}"
            alert_data = self.redis.hgetall(alert_key)

            if alert_data:
                alerts.append({
                    "resource_type": resource_type,
                    "timestamp": alert_data.get(b"timestamp", b"").decode(),
                    "alert_level": alert_data.get(b"alert_level", b"").decode(),
                    "daily_percentage": float(
                        alert_data.get(b"daily_percentage", b"0")
                    ),
                    "monthly_percentage": float(
                        alert_data.get(b"monthly_percentage", b"0")
                    ),
                })

        return alerts
