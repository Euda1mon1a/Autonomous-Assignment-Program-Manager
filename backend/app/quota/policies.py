"""
Quota policy definitions and role-based limits.

This module defines quota policies for different user roles and resource types.
Quotas are enforced on a daily and monthly basis to prevent abuse and ensure
fair resource allocation.
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QuotaPolicyType(str, Enum):
    """Types of quota policies."""

    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"
    ADMIN = "admin"
    CUSTOM = "custom"


@dataclass
class QuotaPolicy:
    """
    Quota policy configuration.

    Defines limits for API usage on daily and monthly basis.
    """

    policy_type: QuotaPolicyType
    daily_limit: int
    monthly_limit: int

    # Resource-specific limits
    schedule_generation_daily: int
    schedule_generation_monthly: int

    # Export limits
    export_daily: int
    export_monthly: int

    # Report generation limits
    report_daily: int
    report_monthly: int

    # Overage handling
    allow_overage: bool = False
    overage_percentage: float = 0.0  # % of quota allowed as overage

    # Alert thresholds (% of quota used)
    warning_threshold: float = 0.80  # 80%
    critical_threshold: float = 0.95  # 95%


# Policy definitions for different user roles
FREE_POLICY = QuotaPolicy(
    policy_type=QuotaPolicyType.FREE,
    daily_limit=100,
    monthly_limit=2000,
    schedule_generation_daily=5,
    schedule_generation_monthly=50,
    export_daily=10,
    export_monthly=100,
    report_daily=5,
    report_monthly=50,
    allow_overage=False,
    overage_percentage=0.0,
    warning_threshold=0.80,
    critical_threshold=0.95,
)

STANDARD_POLICY = QuotaPolicy(
    policy_type=QuotaPolicyType.STANDARD,
    daily_limit=1000,
    monthly_limit=25000,
    schedule_generation_daily=50,
    schedule_generation_monthly=1000,
    export_daily=100,
    export_monthly=2000,
    report_daily=50,
    report_monthly=1000,
    allow_overage=True,
    overage_percentage=0.10,  # 10% overage allowed
    warning_threshold=0.80,
    critical_threshold=0.95,
)

PREMIUM_POLICY = QuotaPolicy(
    policy_type=QuotaPolicyType.PREMIUM,
    daily_limit=10000,
    monthly_limit=250000,
    schedule_generation_daily=500,
    schedule_generation_monthly=10000,
    export_daily=1000,
    export_monthly=20000,
    report_daily=500,
    report_monthly=10000,
    allow_overage=True,
    overage_percentage=0.20,  # 20% overage allowed
    warning_threshold=0.75,
    critical_threshold=0.90,
)

ADMIN_POLICY = QuotaPolicy(
    policy_type=QuotaPolicyType.ADMIN,
    daily_limit=100000,
    monthly_limit=2500000,
    schedule_generation_daily=5000,
    schedule_generation_monthly=100000,
    export_daily=10000,
    export_monthly=200000,
    report_daily=5000,
    report_monthly=100000,
    allow_overage=True,
    overage_percentage=0.50,  # 50% overage allowed
    warning_threshold=0.90,
    critical_threshold=0.95,
)

# Role to policy mapping
ROLE_POLICY_MAPPING = {
    "admin": ADMIN_POLICY,
    "coordinator": PREMIUM_POLICY,
    "faculty": STANDARD_POLICY,
    "resident": STANDARD_POLICY,
    "clinical_staff": FREE_POLICY,
    "rn": FREE_POLICY,
    "lpn": FREE_POLICY,
    "msa": FREE_POLICY,
}


def get_policy_for_role(role: str) -> QuotaPolicy:
    """
    Get quota policy for a user role.

    Args:
        role: User role (admin, coordinator, faculty, etc.)

    Returns:
        QuotaPolicy: Quota policy for the role

    Raises:
        ValueError: If role is not recognized
    """
    if role not in ROLE_POLICY_MAPPING:
        logger.warning(f"Unknown role '{role}', using FREE policy")
        return FREE_POLICY

    return ROLE_POLICY_MAPPING[role]


def create_custom_policy(
    daily_limit: int,
    monthly_limit: int,
    schedule_generation_daily: int | None = None,
    schedule_generation_monthly: int | None = None,
    export_daily: int | None = None,
    export_monthly: int | None = None,
    report_daily: int | None = None,
    report_monthly: int | None = None,
    allow_overage: bool = False,
    overage_percentage: float = 0.0,
) -> QuotaPolicy:
    """
    Create a custom quota policy.

    Args:
        daily_limit: Daily API call limit
        monthly_limit: Monthly API call limit
        schedule_generation_daily: Daily schedule generation limit
        schedule_generation_monthly: Monthly schedule generation limit
        export_daily: Daily export limit
        export_monthly: Monthly export limit
        report_daily: Daily report generation limit
        report_monthly: Monthly report generation limit
        allow_overage: Whether to allow overage
        overage_percentage: Percentage of overage allowed (0.0-1.0)

    Returns:
        QuotaPolicy: Custom quota policy
    """
    return QuotaPolicy(
        policy_type=QuotaPolicyType.CUSTOM,
        daily_limit=daily_limit,
        monthly_limit=monthly_limit,
        schedule_generation_daily=schedule_generation_daily or daily_limit // 10,
        schedule_generation_monthly=schedule_generation_monthly or monthly_limit // 10,
        export_daily=export_daily or daily_limit // 5,
        export_monthly=export_monthly or monthly_limit // 5,
        report_daily=report_daily or daily_limit // 10,
        report_monthly=report_monthly or monthly_limit // 10,
        allow_overage=allow_overage,
        overage_percentage=overage_percentage,
        warning_threshold=0.80,
        critical_threshold=0.95,
    )


def validate_policy_limits(policy: QuotaPolicy) -> bool:
    """
    Validate that policy limits are consistent.

    Args:
        policy: Quota policy to validate

    Returns:
        bool: True if valid, False otherwise
    """
    # Daily limits should be less than monthly
    if policy.daily_limit * 30 > policy.monthly_limit:
        logger.warning(
            f"Policy {policy.policy_type}: daily_limit * 30 ({policy.daily_limit * 30}) "
            f"exceeds monthly_limit ({policy.monthly_limit})"
        )
        return False

    # Resource-specific daily limits should be <= general daily limit
    if policy.schedule_generation_daily > policy.daily_limit:
        logger.warning(
            f"Policy {policy.policy_type}: schedule_generation_daily "
            f"exceeds daily_limit"
        )
        return False

    if policy.export_daily > policy.daily_limit:
        logger.warning(f"Policy {policy.policy_type}: export_daily exceeds daily_limit")
        return False

    if policy.report_daily > policy.daily_limit:
        logger.warning(f"Policy {policy.policy_type}: report_daily exceeds daily_limit")
        return False

    # Overage percentage should be between 0 and 1
    if not 0.0 <= policy.overage_percentage <= 1.0:
        logger.warning(
            f"Policy {policy.policy_type}: overage_percentage must be between 0 and 1"
        )
        return False

    return True
