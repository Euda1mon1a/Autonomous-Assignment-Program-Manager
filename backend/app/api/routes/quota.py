"""
API quota management endpoints.

Provides endpoints for:
- Viewing quota status
- Getting usage reports
- Setting custom quotas (admin)
- Resetting quotas (admin)
- Viewing alerts
"""

import logging
from datetime import datetime

import redis
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import get_settings
from app.core.security import get_admin_user, get_current_active_user
from app.models.user import User
from app.quota import QuotaManager
from app.quota.policies import (
    ADMIN_POLICY,
    FREE_POLICY,
    PREMIUM_POLICY,
    STANDARD_POLICY,
    QuotaPolicyType,
    create_custom_policy,
)
from app.schemas.quota import (
    AllPoliciesResponse,
    QuotaAlertsResponse,
    QuotaPolicyConfig,
    QuotaPolicyInfo,
    QuotaStatus,
    QuotaUsageReport,
    RecordUsageRequest,
    RecordUsageResponse,
    ResetQuotaRequest,
    ResetQuotaResponse,
    SetCustomQuotaRequest,
    SetCustomQuotaResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


def get_redis_client() -> redis.Redis:
    """
    Get Redis client for quota management.

    Returns:
        Redis client instance

    Raises:
        HTTPException: If Redis connection fails
    """
    try:
        redis_url = settings.redis_url_with_password
        client = redis.from_url(
            redis_url,
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        client.ping()
        return client
    except (redis.ConnectionError, redis.TimeoutError) as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Quota service temporarily unavailable",
        )


def get_quota_manager(
    redis_client: redis.Redis = Depends(get_redis_client),
) -> QuotaManager:
    """
    Get QuotaManager instance.

    Args:
        redis_client: Redis client dependency

    Returns:
        QuotaManager instance
    """
    return QuotaManager(redis_client)


@router.get("/status", response_model=QuotaStatus)
async def get_quota_status(
    current_user: User = Depends(get_current_active_user),
    quota_manager: QuotaManager = Depends(get_quota_manager),
) -> QuotaStatus:
    """
    Get current quota status for the authenticated user.

    Returns usage, limits, and remaining quota for all resource types.

    **Example Response:**
    ```json
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "policy_type": "premium",
      "reset_times": {
        "daily": "2025-12-21T00:00:00",
        "monthly": "2026-01-01T00:00:00"
      },
      "resources": {
        "api": {
          "limits": {"daily": 10000, "monthly": 250000},
          "usage": {"daily": 523, "monthly": 15234},
          "remaining": {"daily": 9477, "monthly": 234766},
          "percentage": {"daily": 5.23, "monthly": 6.09}
        },
        ...
      }
    }
    ```
    """
    try:
        summary = quota_manager.get_usage_summary(
            str(current_user.id), current_user.role
        )
        return QuotaStatus(**summary)
    except Exception as e:
        logger.error(f"Failed to get quota status for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quota status",
        )


@router.get("/alerts", response_model=QuotaAlertsResponse)
async def get_quota_alerts(
    current_user: User = Depends(get_current_active_user),
    quota_manager: QuotaManager = Depends(get_quota_manager),
) -> QuotaAlertsResponse:
    """
    Get quota usage alerts for the authenticated user.

    Returns alerts when usage exceeds warning thresholds.

    **Example Response:**
    ```json
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "alerts": [
        {
          "resource_type": "schedule",
          "timestamp": "2025-12-20T15:30:00",
          "alert_level": "warning",
          "daily_percentage": 85.2,
          "monthly_percentage": 78.3
        }
      ]
    }
    ```
    """
    try:
        alerts = quota_manager.get_alerts(str(current_user.id))
        return QuotaAlertsResponse(
            user_id=str(current_user.id),
            alerts=alerts,
        )
    except Exception as e:
        logger.error(f"Failed to get alerts for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts",
        )


@router.get("/report", response_model=QuotaUsageReport)
async def get_quota_report(
    period: str = "monthly",
    current_user: User = Depends(get_current_active_user),
    quota_manager: QuotaManager = Depends(get_quota_manager),
) -> QuotaUsageReport:
    """
    Get quota usage report for the authenticated user.

    Args:
        period: Report period ("daily" or "monthly")

    **Example Response:**
    ```json
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "policy_type": "premium",
      "period": "monthly",
      "resources": {...},
      "total_usage": 15234,
      "total_limit": 250000,
      "usage_percentage": 6.09,
      "generated_at": "2025-12-20T15:30:00"
    }
    ```
    """
    if period not in ["daily", "monthly"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period must be 'daily' or 'monthly'",
        )

    try:
        summary = quota_manager.get_usage_summary(
            str(current_user.id), current_user.role
        )

        # Calculate total usage and limit based on period
        total_usage = 0
        total_limit = 0
        for resource in summary["resources"].values():
            if period == "daily":
                total_usage += resource["usage"]["daily"]
                total_limit += resource["limits"]["daily"]
            else:
                total_usage += resource["usage"]["monthly"]
                total_limit += resource["limits"]["monthly"]

        usage_percentage = (total_usage / total_limit * 100) if total_limit > 0 else 0

        return QuotaUsageReport(
            user_id=str(current_user.id),
            policy_type=summary["policy_type"],
            period=period,
            resources=summary["resources"],
            total_usage=total_usage,
            total_limit=total_limit,
            usage_percentage=round(usage_percentage, 2),
            generated_at=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to generate report for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate usage report",
        )


@router.get("/policies", response_model=AllPoliciesResponse)
async def get_quota_policies(
    current_user: User = Depends(get_current_active_user),
) -> AllPoliciesResponse:
    """
    Get all available quota policies.

    Returns information about all quota policy tiers.

    **Example Response:**
    ```json
    {
      "policies": [
        {
          "policy_type": "free",
          "roles": ["clinical_staff", "rn", "lpn", "msa"],
          "config": {
            "daily_limit": 100,
            "monthly_limit": 2000,
            ...
          }
        },
        ...
      ]
    }
    ```
    """
    policies = [
        QuotaPolicyInfo(
            policy_type=QuotaPolicyType.FREE.value,
            roles=["clinical_staff", "rn", "lpn", "msa"],
            config=QuotaPolicyConfig(
                daily_limit=FREE_POLICY.daily_limit,
                monthly_limit=FREE_POLICY.monthly_limit,
                schedule_generation_daily=FREE_POLICY.schedule_generation_daily,
                schedule_generation_monthly=FREE_POLICY.schedule_generation_monthly,
                export_daily=FREE_POLICY.export_daily,
                export_monthly=FREE_POLICY.export_monthly,
                report_daily=FREE_POLICY.report_daily,
                report_monthly=FREE_POLICY.report_monthly,
                allow_overage=FREE_POLICY.allow_overage,
                overage_percentage=FREE_POLICY.overage_percentage,
            ),
        ),
        QuotaPolicyInfo(
            policy_type=QuotaPolicyType.STANDARD.value,
            roles=["faculty", "resident"],
            config=QuotaPolicyConfig(
                daily_limit=STANDARD_POLICY.daily_limit,
                monthly_limit=STANDARD_POLICY.monthly_limit,
                schedule_generation_daily=STANDARD_POLICY.schedule_generation_daily,
                schedule_generation_monthly=STANDARD_POLICY.schedule_generation_monthly,
                export_daily=STANDARD_POLICY.export_daily,
                export_monthly=STANDARD_POLICY.export_monthly,
                report_daily=STANDARD_POLICY.report_daily,
                report_monthly=STANDARD_POLICY.report_monthly,
                allow_overage=STANDARD_POLICY.allow_overage,
                overage_percentage=STANDARD_POLICY.overage_percentage,
            ),
        ),
        QuotaPolicyInfo(
            policy_type=QuotaPolicyType.PREMIUM.value,
            roles=["coordinator"],
            config=QuotaPolicyConfig(
                daily_limit=PREMIUM_POLICY.daily_limit,
                monthly_limit=PREMIUM_POLICY.monthly_limit,
                schedule_generation_daily=PREMIUM_POLICY.schedule_generation_daily,
                schedule_generation_monthly=PREMIUM_POLICY.schedule_generation_monthly,
                export_daily=PREMIUM_POLICY.export_daily,
                export_monthly=PREMIUM_POLICY.export_monthly,
                report_daily=PREMIUM_POLICY.report_daily,
                report_monthly=PREMIUM_POLICY.report_monthly,
                allow_overage=PREMIUM_POLICY.allow_overage,
                overage_percentage=PREMIUM_POLICY.overage_percentage,
            ),
        ),
        QuotaPolicyInfo(
            policy_type=QuotaPolicyType.ADMIN.value,
            roles=["admin"],
            config=QuotaPolicyConfig(
                daily_limit=ADMIN_POLICY.daily_limit,
                monthly_limit=ADMIN_POLICY.monthly_limit,
                schedule_generation_daily=ADMIN_POLICY.schedule_generation_daily,
                schedule_generation_monthly=ADMIN_POLICY.schedule_generation_monthly,
                export_daily=ADMIN_POLICY.export_daily,
                export_monthly=ADMIN_POLICY.export_monthly,
                report_daily=ADMIN_POLICY.report_daily,
                report_monthly=ADMIN_POLICY.report_monthly,
                allow_overage=ADMIN_POLICY.allow_overage,
                overage_percentage=ADMIN_POLICY.overage_percentage,
            ),
        ),
    ]

    return AllPoliciesResponse(policies=policies)


@router.post("/custom", response_model=SetCustomQuotaResponse)
async def set_custom_quota(
    request: SetCustomQuotaRequest,
    admin_user: User = Depends(get_admin_user),
    quota_manager: QuotaManager = Depends(get_quota_manager),
) -> SetCustomQuotaResponse:
    """
    Set custom quota for a user (admin only).

    Allows administrators to override default role-based quotas.

    **Requires:** Admin role

    **Example Request:**
    ```json
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "policy": {
        "daily_limit": 5000,
        "monthly_limit": 100000,
        "schedule_generation_daily": 100,
        ...
      },
      "ttl_seconds": 86400
    }
    ```
    """
    try:
        # Create custom policy from config
        custom_policy = create_custom_policy(
            daily_limit=request.policy.daily_limit,
            monthly_limit=request.policy.monthly_limit,
            schedule_generation_daily=request.policy.schedule_generation_daily,
            schedule_generation_monthly=request.policy.schedule_generation_monthly,
            export_daily=request.policy.export_daily,
            export_monthly=request.policy.export_monthly,
            report_daily=request.policy.report_daily,
            report_monthly=request.policy.report_monthly,
            allow_overage=request.policy.allow_overage,
            overage_percentage=request.policy.overage_percentage,
        )

        # Set custom policy
        success = quota_manager.set_custom_policy(
            request.user_id,
            custom_policy,
            request.ttl_seconds,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set custom quota",
            )

        # Calculate expiration time
        expires_at = None
        if request.ttl_seconds:
            from datetime import timedelta

            expires_at = (
                datetime.utcnow() + timedelta(seconds=request.ttl_seconds)
            ).isoformat()

        logger.info(
            f"Admin {admin_user.username} set custom quota for user {request.user_id}"
        )

        return SetCustomQuotaResponse(
            success=True,
            message="Custom quota set successfully",
            user_id=request.user_id,
            policy=request.policy,
            expires_at=expires_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set custom quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set custom quota",
        )


@router.delete("/custom/{user_id}")
async def remove_custom_quota(
    user_id: str,
    admin_user: User = Depends(get_admin_user),
    quota_manager: QuotaManager = Depends(get_quota_manager),
):
    """
    Remove custom quota for a user (admin only).

    Reverts user back to role-based quota policy.

    **Requires:** Admin role
    """
    try:
        success = quota_manager.remove_custom_policy(user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove custom quota",
            )

        logger.info(
            f"Admin {admin_user.username} removed custom quota for user {user_id}"
        )

        return {
            "success": True,
            "message": "Custom quota removed successfully",
            "user_id": user_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove custom quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove custom quota",
        )


@router.post("/reset", response_model=ResetQuotaResponse)
async def reset_quota(
    request: ResetQuotaRequest,
    admin_user: User = Depends(get_admin_user),
    quota_manager: QuotaManager = Depends(get_quota_manager),
) -> ResetQuotaResponse:
    """
    Reset quota for a user (admin only).

    Manually reset daily and/or monthly quotas.

    **Requires:** Admin role

    **Example Request:**
    ```json
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "resource_type": "api",
      "reset_daily": true,
      "reset_monthly": false
    }
    ```
    """
    try:
        success = quota_manager.reset_user_quota(
            request.user_id,
            request.resource_type,
            request.reset_daily,
            request.reset_monthly,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset quota",
            )

        logger.info(
            f"Admin {admin_user.username} reset quota for user {request.user_id} "
            f"(resource={request.resource_type}, daily={request.reset_daily}, "
            f"monthly={request.reset_monthly})"
        )

        return ResetQuotaResponse(
            success=True,
            message="Quota reset successfully",
            user_id=request.user_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset quota",
        )


@router.post("/record", response_model=RecordUsageResponse)
async def record_usage(
    request: RecordUsageRequest,
    admin_user: User = Depends(get_admin_user),
    quota_manager: QuotaManager = Depends(get_quota_manager),
) -> RecordUsageResponse:
    """
    Manually record usage for a user (admin only).

    Used for testing or manual adjustments.

    **Requires:** Admin role

    **Example Request:**
    ```json
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "resource_type": "api",
      "amount": 10
    }
    ```
    """
    try:
        # Get user role (assume admin for manual recording)
        daily_usage, monthly_usage = quota_manager.record_usage(
            request.user_id,
            "admin",  # Use admin role for manual recording
            request.resource_type,
            request.amount,
        )

        logger.info(
            f"Admin {admin_user.username} recorded {request.amount} "
            f"{request.resource_type} usage for user {request.user_id}"
        )

        return RecordUsageResponse(
            success=True,
            user_id=request.user_id,
            resource_type=request.resource_type,
            daily_usage=daily_usage,
            monthly_usage=monthly_usage,
        )
    except Exception as e:
        logger.error(f"Failed to record usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record usage",
        )
