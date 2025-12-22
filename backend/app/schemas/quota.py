"""
Quota management schemas.

Pydantic schemas for quota API request/response validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class QuotaLimits(BaseModel):
    """Quota limits for a resource."""
    daily: int = Field(..., description="Daily limit")
    monthly: int = Field(..., description="Monthly limit")


class QuotaUsage(BaseModel):
    """Current quota usage."""
    daily: int = Field(..., description="Daily usage")
    monthly: int = Field(..., description="Monthly usage")


class QuotaRemaining(BaseModel):
    """Remaining quota."""
    daily: int = Field(..., description="Daily remaining")
    monthly: int = Field(..., description="Monthly remaining")


class QuotaPercentage(BaseModel):
    """Quota usage percentage."""
    daily: float = Field(..., description="Daily usage percentage")
    monthly: float = Field(..., description="Monthly usage percentage")


class ResourceQuotaStatus(BaseModel):
    """Quota status for a specific resource type."""
    limits: QuotaLimits = Field(..., description="Quota limits")
    usage: QuotaUsage = Field(..., description="Current usage")
    remaining: QuotaRemaining = Field(..., description="Remaining quota")
    percentage: QuotaPercentage = Field(..., description="Usage percentage")


class QuotaResetTimes(BaseModel):
    """Quota reset timestamps."""
    daily: str = Field(..., description="Daily reset time (ISO format)")
    monthly: str = Field(..., description="Monthly reset time (ISO format)")


class QuotaStatus(BaseModel):
    """
    Complete quota status for a user.

    Returned by GET /api/quota/status endpoint.
    """
    user_id: str = Field(..., description="User ID")
    policy_type: str = Field(..., description="Quota policy type")
    reset_times: QuotaResetTimes = Field(..., description="Reset times")
    resources: dict[str, ResourceQuotaStatus] = Field(
        ...,
        description="Quota status by resource type (api, schedule, export, report)",
    )


class QuotaPolicyConfig(BaseModel):
    """Quota policy configuration."""
    daily_limit: int = Field(..., gt=0, description="Daily API call limit")
    monthly_limit: int = Field(..., gt=0, description="Monthly API call limit")
    schedule_generation_daily: int = Field(
        ..., gt=0, description="Daily schedule generation limit"
    )
    schedule_generation_monthly: int = Field(
        ..., gt=0, description="Monthly schedule generation limit"
    )
    export_daily: int = Field(..., gt=0, description="Daily export limit")
    export_monthly: int = Field(..., gt=0, description="Monthly export limit")
    report_daily: int = Field(..., gt=0, description="Daily report generation limit")
    report_monthly: int = Field(..., gt=0, description="Monthly report generation limit")
    allow_overage: bool = Field(default=False, description="Allow quota overage")
    overage_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overage percentage allowed (0.0-1.0)",
    )


class SetCustomQuotaRequest(BaseModel):
    """
    Request to set custom quota for a user.

    Admin-only endpoint: POST /api/quota/custom
    """
    user_id: str = Field(..., description="User ID to apply custom quota")
    policy: QuotaPolicyConfig = Field(..., description="Custom quota policy")
    ttl_seconds: Optional[int] = Field(
        default=None,
        gt=0,
        description="Time-to-live in seconds (None = permanent)",
    )


class SetCustomQuotaResponse(BaseModel):
    """Response after setting custom quota."""
    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Result message")
    user_id: str = Field(..., description="User ID affected")
    policy: QuotaPolicyConfig = Field(..., description="Applied policy")
    expires_at: Optional[str] = Field(None, description="Expiration time (ISO format)")


class ResetQuotaRequest(BaseModel):
    """
    Request to reset quota for a user.

    Admin-only endpoint: POST /api/quota/reset
    """
    user_id: str = Field(..., description="User ID")
    resource_type: Optional[str] = Field(
        default=None,
        description="Resource type to reset (None = all)",
    )
    reset_daily: bool = Field(default=True, description="Reset daily quota")
    reset_monthly: bool = Field(default=False, description="Reset monthly quota")


class ResetQuotaResponse(BaseModel):
    """Response after resetting quota."""
    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Result message")
    user_id: str = Field(..., description="User ID affected")


class QuotaAlert(BaseModel):
    """Quota usage alert."""
    resource_type: str = Field(..., description="Resource type")
    timestamp: str = Field(..., description="Alert timestamp (ISO format)")
    alert_level: str = Field(..., description="Alert level (warning/critical)")
    daily_percentage: float = Field(..., description="Daily usage percentage")
    monthly_percentage: float = Field(..., description="Monthly usage percentage")


class QuotaAlertsResponse(BaseModel):
    """Response listing quota alerts."""
    user_id: str = Field(..., description="User ID")
    alerts: list[QuotaAlert] = Field(..., description="Active alerts")


class QuotaPolicyInfo(BaseModel):
    """Information about a quota policy."""
    policy_type: str = Field(..., description="Policy type")
    roles: list[str] = Field(..., description="Roles using this policy")
    config: QuotaPolicyConfig = Field(..., description="Policy configuration")


class AllPoliciesResponse(BaseModel):
    """Response listing all quota policies."""
    policies: list[QuotaPolicyInfo] = Field(..., description="Available quota policies")


class QuotaUsageReport(BaseModel):
    """Quota usage report for a time period."""
    user_id: str = Field(..., description="User ID")
    policy_type: str = Field(..., description="Current policy type")
    period: str = Field(..., description="Report period (daily/monthly)")
    resources: dict[str, ResourceQuotaStatus] = Field(
        ..., description="Usage by resource type"
    )
    total_usage: int = Field(..., description="Total API calls")
    total_limit: int = Field(..., description="Total limit")
    usage_percentage: float = Field(..., description="Overall usage percentage")
    generated_at: str = Field(..., description="Report generation time (ISO format)")


class QuotaExceededDetail(BaseModel):
    """
    Detailed error response for quota exceeded (429).

    Automatically returned when quota is exceeded.
    """
    error: str = Field(default="Quota exceeded", description="Error type")
    message: str = Field(..., description="Human-readable error message")
    resource_type: str = Field(..., description="Resource type that exceeded quota")
    daily_limit: int = Field(..., description="Daily limit")
    monthly_limit: int = Field(..., description="Monthly limit")
    reset_times: QuotaResetTimes = Field(..., description="Quota reset times")


class RecordUsageRequest(BaseModel):
    """Request to manually record usage (internal/testing)."""
    user_id: str = Field(..., description="User ID")
    resource_type: str = Field(default="api", description="Resource type")
    amount: int = Field(default=1, gt=0, description="Amount to record")


class RecordUsageResponse(BaseModel):
    """Response after recording usage."""
    success: bool = Field(..., description="Whether operation succeeded")
    user_id: str = Field(..., description="User ID")
    resource_type: str = Field(..., description="Resource type")
    daily_usage: int = Field(..., description="Daily usage after recording")
    monthly_usage: int = Field(..., description="Monthly usage after recording")
