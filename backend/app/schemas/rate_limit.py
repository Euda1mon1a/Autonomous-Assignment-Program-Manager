"""
Rate limit response schemas.

Pydantic schemas for rate limit status and configuration endpoints.
"""
from pydantic import BaseModel, Field


class RateLimitStatus(BaseModel):
    """
    Current rate limit status for a user/client.

    Returned by GET /api/rate-limit/status endpoint.
    """
    tier: str = Field(..., description="Rate limit tier (free, standard, premium, admin)")
    limits: "RateLimitLimits" = Field(..., description="Rate limit thresholds")
    remaining: "RateLimitRemaining" = Field(..., description="Remaining requests")
    reset: "RateLimitReset" = Field(..., description="Reset timestamps")
    burst: "BurstStatus" = Field(..., description="Token bucket burst status")


class RateLimitLimits(BaseModel):
    """Rate limit thresholds."""
    per_minute: int = Field(..., description="Maximum requests per minute")
    per_hour: int = Field(..., description="Maximum requests per hour")
    burst_size: int = Field(..., description="Maximum burst requests")


class RateLimitRemaining(BaseModel):
    """Remaining request counts."""
    per_minute: int = Field(..., description="Remaining requests this minute")
    per_hour: int = Field(..., description="Remaining requests this hour")
    burst: int = Field(..., description="Remaining burst tokens")


class RateLimitReset(BaseModel):
    """Reset timestamps (Unix epoch seconds)."""
    minute: int = Field(..., description="Unix timestamp when minute window resets")
    hour: int = Field(..., description="Unix timestamp when hour window resets")


class BurstStatus(BaseModel):
    """Token bucket burst status."""
    tokens: float = Field(..., description="Current tokens in bucket")
    capacity: int = Field(..., description="Bucket capacity (max tokens)")
    refill_rate: float = Field(..., description="Tokens added per second")


class RateLimitConfig(BaseModel):
    """
    Rate limit configuration.

    Used for setting custom limits or viewing tier configurations.
    """
    requests_per_minute: int = Field(..., gt=0, description="Requests per minute limit")
    requests_per_hour: int = Field(..., gt=0, description="Requests per hour limit")
    burst_size: int = Field(..., gt=0, description="Token bucket capacity")
    burst_refill_rate: float = Field(..., gt=0, description="Tokens per second refill rate")


class CustomLimitRequest(BaseModel):
    """
    Request to set custom rate limit for a user.

    Admin-only endpoint: POST /api/rate-limit/custom
    """
    user_id: str = Field(..., description="User ID to apply custom limit")
    config: RateLimitConfig = Field(..., description="Custom rate limit configuration")
    ttl_seconds: int = Field(
        default=86400,
        gt=0,
        description="Time-to-live for custom limit in seconds (default: 24 hours)",
    )


class CustomLimitResponse(BaseModel):
    """Response after setting custom rate limit."""
    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Result message")
    user_id: str = Field(..., description="User ID affected")
    config: RateLimitConfig = Field(..., description="Applied configuration")
    expires_at: int = Field(..., description="Unix timestamp when custom limit expires")


class TierInfo(BaseModel):
    """
    Information about a rate limit tier.

    Returned by GET /api/rate-limit/tiers endpoint.
    """
    tier: str = Field(..., description="Tier name")
    config: RateLimitConfig = Field(..., description="Tier configuration")
    roles: list[str] = Field(..., description="User roles that get this tier")


class AllTiersResponse(BaseModel):
    """Response listing all available tiers."""
    tiers: list[TierInfo] = Field(..., description="All rate limit tiers")


class EndpointLimitInfo(BaseModel):
    """
    Information about endpoint-specific rate limits.

    Some endpoints (e.g., schedule generation) have tighter limits
    than the general tier limits.
    """
    endpoint: str = Field(..., description="Endpoint path or pattern")
    limits: RateLimitConfig | None = Field(
        None,
        description="Custom limits for this endpoint (None means tier defaults apply)",
    )


class EndpointLimitsResponse(BaseModel):
    """Response listing endpoint-specific limits."""
    endpoints: list[EndpointLimitInfo] = Field(
        ...,
        description="Endpoints with custom rate limits",
    )


class RateLimitHeaders(BaseModel):
    """
    Rate limit headers returned in API responses.

    These headers are automatically added to all API responses
    by the RateLimitMiddleware.
    """
    x_ratelimit_tier: str = Field(
        ...,
        alias="X-RateLimit-Tier",
        description="Current rate limit tier",
    )
    x_ratelimit_limit_minute: int = Field(
        ...,
        alias="X-RateLimit-Limit-Minute",
        description="Maximum requests per minute",
    )
    x_ratelimit_limit_hour: int = Field(
        ...,
        alias="X-RateLimit-Limit-Hour",
        description="Maximum requests per hour",
    )
    x_ratelimit_remaining_minute: int = Field(
        ...,
        alias="X-RateLimit-Remaining-Minute",
        description="Remaining requests this minute",
    )
    x_ratelimit_remaining_hour: int = Field(
        ...,
        alias="X-RateLimit-Remaining-Hour",
        description="Remaining requests this hour",
    )
    x_ratelimit_reset_minute: int = Field(
        ...,
        alias="X-RateLimit-Reset-Minute",
        description="Unix timestamp when minute window resets",
    )
    x_ratelimit_reset_hour: int = Field(
        ...,
        alias="X-RateLimit-Reset-Hour",
        description="Unix timestamp when hour window resets",
    )
    x_ratelimit_burst_remaining: int = Field(
        ...,
        alias="X-RateLimit-Burst-Remaining",
        description="Remaining burst tokens",
    )

    class Config:
        populate_by_name = True


class RateLimitErrorDetail(BaseModel):
    """
    Detailed error response for rate limit exceeded (429).

    Automatically returned when rate limit is exceeded.
    """
    error: str = Field(default="Rate limit exceeded", description="Error type")
    message: str = Field(..., description="Human-readable error message")
    tier: str = Field(..., description="Current rate limit tier")
    limits: dict = Field(..., description="Rate limit thresholds")
    remaining: dict = Field(..., description="Remaining requests")
    reset: dict = Field(..., description="Reset timestamps")
