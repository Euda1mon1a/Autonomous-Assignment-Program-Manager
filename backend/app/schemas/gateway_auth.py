"""Pydantic schemas for gateway authentication."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class APIKeyCreate(BaseModel):
    """Schema for creating a new API key."""
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable key name")
    scopes: Optional[str] = Field(None, description="Comma-separated list of allowed scopes")
    allowed_ips: Optional[str] = Field(None, description="Comma-separated list of allowed IP addresses/CIDR")
    rate_limit_per_minute: Optional[int] = Field(100, ge=1, le=10000)
    rate_limit_per_hour: Optional[int] = Field(5000, ge=1, le=100000)
    expires_at: Optional[datetime] = None

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, v: Optional[str]) -> Optional[str]:
        """Validate scopes format."""
        if v:
            scopes = [s.strip() for s in v.split(",")]
            if not all(scopes):
                raise ValueError("Scopes cannot contain empty values")
        return v

    @field_validator("allowed_ips")
    @classmethod
    def validate_ips(cls, v: Optional[str]) -> Optional[str]:
        """Validate IP addresses format."""
        if v:
            ips = [ip.strip() for ip in v.split(",")]
            if not all(ips):
                raise ValueError("IP list cannot contain empty values")
        return v


class APIKeyResponse(BaseModel):
    """Schema for API key response (includes the actual key only on creation)."""
    id: UUID
    name: str
    key_prefix: str
    scopes: Optional[str]
    allowed_ips: Optional[str]
    rate_limit_per_minute: Optional[int]
    rate_limit_per_hour: Optional[int]
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    last_used_ip: Optional[str]
    total_requests: int
    created_at: datetime

    # Only present on initial creation
    api_key: Optional[str] = Field(None, description="Full API key (only shown once on creation)")

    class Config:
        from_attributes = True


class APIKeyUpdate(BaseModel):
    """Schema for updating an existing API key."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    scopes: Optional[str] = None
    allowed_ips: Optional[str] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=10000)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000)
    is_active: Optional[bool] = None


class APIKeyRotateRequest(BaseModel):
    """Schema for rotating an API key."""
    name: Optional[str] = Field(None, description="Optional new name for rotated key")
    grace_period_hours: int = Field(
        24,
        ge=0,
        le=168,
        description="Hours to keep old key valid (0-168, default 24)"
    )


class APIKeyRevokeRequest(BaseModel):
    """Schema for revoking an API key."""
    reason: str = Field(..., min_length=1, max_length=500)


class OAuth2ClientCreate(BaseModel):
    """Schema for creating a new OAuth2 client."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scopes: str = Field("read", description="Comma-separated list of allowed scopes")
    grant_types: str = Field("client_credentials", description="Allowed OAuth2 grant types")
    is_confidential: bool = Field(True, description="Whether client can keep secret confidential")
    rate_limit_per_minute: Optional[int] = Field(100, ge=1, le=10000)
    rate_limit_per_hour: Optional[int] = Field(5000, ge=1, le=100000)
    access_token_lifetime_seconds: int = Field(3600, ge=300, le=86400)


class OAuth2ClientResponse(BaseModel):
    """Schema for OAuth2 client response."""
    id: UUID
    client_id: str
    name: str
    description: Optional[str]
    scopes: str
    grant_types: str
    is_active: bool
    is_confidential: bool
    rate_limit_per_minute: Optional[int]
    rate_limit_per_hour: Optional[int]
    access_token_lifetime_seconds: int
    last_used_at: Optional[datetime]
    total_tokens_issued: int
    created_at: datetime

    # Only present on initial creation
    client_secret: Optional[str] = Field(None, description="Client secret (only shown once on creation)")

    class Config:
        from_attributes = True


class OAuth2ClientUpdate(BaseModel):
    """Schema for updating an OAuth2 client."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scopes: Optional[str] = None
    is_active: Optional[bool] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=10000)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000)


class OAuth2TokenRequest(BaseModel):
    """Schema for OAuth2 token request (client_credentials flow)."""
    grant_type: str = Field(..., pattern="^client_credentials$")
    client_id: str = Field(..., min_length=1)
    client_secret: str = Field(..., min_length=1)
    scope: Optional[str] = Field(None, description="Requested scopes (space-separated)")


class OAuth2TokenResponse(BaseModel):
    """Schema for OAuth2 token response."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: Optional[str] = None


class IPWhitelistCreate(BaseModel):
    """Schema for creating an IP whitelist entry."""
    ip_address: str = Field(..., min_length=7, max_length=45, description="IP address or CIDR range")
    description: Optional[str] = Field(None, max_length=500)
    applies_to: str = Field("all", description="What this whitelist applies to")
    expires_at: Optional[datetime] = None

    @field_validator("applies_to")
    @classmethod
    def validate_applies_to(cls, v: str) -> str:
        """Validate applies_to field."""
        valid_values = {"all", "api_keys", "oauth2", "gateway"}
        if v not in valid_values:
            raise ValueError(f"applies_to must be one of: {', '.join(valid_values)}")
        return v


class IPWhitelistResponse(BaseModel):
    """Schema for IP whitelist response."""
    id: UUID
    ip_address: str
    description: Optional[str]
    applies_to: str
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class IPBlacklistCreate(BaseModel):
    """Schema for creating an IP blacklist entry."""
    ip_address: str = Field(..., min_length=7, max_length=45, description="IP address or CIDR range to block")
    reason: str = Field(..., min_length=1, max_length=500)
    detection_method: Optional[str] = Field("manual", max_length=100)
    expires_at: Optional[datetime] = Field(None, description="Auto-unblock time (null = permanent)")

    @field_validator("detection_method")
    @classmethod
    def validate_detection_method(cls, v: Optional[str]) -> Optional[str]:
        """Validate detection_method field."""
        valid_values = {"manual", "rate_limit", "brute_force", "suspicious_activity", "automated"}
        if v and v not in valid_values:
            raise ValueError(f"detection_method must be one of: {', '.join(valid_values)}")
        return v


class IPBlacklistResponse(BaseModel):
    """Schema for IP blacklist response."""
    id: UUID
    ip_address: str
    reason: str
    detection_method: Optional[str]
    incident_count: int
    is_active: bool
    expires_at: Optional[datetime]
    last_hit_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class RequestSignatureVerifyRequest(BaseModel):
    """Schema for request signature verification."""
    signature: str = Field(..., description="HMAC signature from request header")
    timestamp: str = Field(..., description="Request timestamp")
    method: str = Field(..., pattern="^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)$")
    path: str = Field(..., min_length=1, max_length=2000)
    body: Optional[str] = Field(None, description="Request body for POST/PUT/PATCH")


class GatewayAuthValidationRequest(BaseModel):
    """Schema for validating gateway authentication."""
    api_key: Optional[str] = Field(None, description="API key for validation")
    jwt_token: Optional[str] = Field(None, description="JWT token for validation")
    client_id: Optional[str] = Field(None, description="OAuth2 client ID")
    client_secret: Optional[str] = Field(None, description="OAuth2 client secret")
    ip_address: str = Field(..., description="Client IP address")
    request_signature: Optional[RequestSignatureVerifyRequest] = None


class GatewayAuthValidationResponse(BaseModel):
    """Schema for gateway authentication validation response."""
    is_valid: bool
    auth_type: Optional[str] = Field(None, description="Type of authentication used: 'api_key', 'jwt', 'oauth2'")
    user_id: Optional[UUID] = None
    scopes: list[str] = Field(default_factory=list)
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset_at: Optional[datetime] = None
    error_message: Optional[str] = None


class APIKeyListResponse(BaseModel):
    """Schema for listing API keys."""
    total: int
    items: list[APIKeyResponse]


class OAuth2ClientListResponse(BaseModel):
    """Schema for listing OAuth2 clients."""
    total: int
    items: list[OAuth2ClientResponse]


class IPWhitelistListResponse(BaseModel):
    """Schema for listing IP whitelist entries."""
    total: int
    items: list[IPWhitelistResponse]


class IPBlacklistListResponse(BaseModel):
    """Schema for listing IP blacklist entries."""
    total: int
    items: list[IPBlacklistResponse]
