"""Feature flag schemas for request/response validation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FeatureFlagBase(BaseModel):
    """Base schema for feature flags."""

    key: str = Field(
        ..., min_length=1, max_length=100, description="Unique feature flag key"
    )
    name: str = Field(
        ..., min_length=1, max_length=255, description="Human-readable name"
    )
    description: str | None = Field(
        None, description="Detailed description of the feature"
    )
    flag_type: str = Field(
        default="boolean", description="Flag type: boolean, percentage, or variant"
    )
    enabled: bool = Field(default=False, description="Whether the flag is enabled")
    rollout_percentage: float | None = Field(
        None, ge=0.0, le=1.0, description="Percentage rollout (0.0-1.0)"
    )
    environments: list[str] | None = Field(
        None, description="Target environments (null = all)"
    )
    target_user_ids: list[str] | None = Field(
        None, description="Target user IDs (null = all)"
    )
    target_roles: list[str] | None = Field(
        None, description="Target roles (null = all)"
    )
    variants: dict[str, float] | None = Field(
        None, description="A/B test variants with weights"
    )
    dependencies: list[str] | None = Field(
        None, description="Required feature flag keys"
    )
    custom_attributes: dict[str, Any] | None = Field(
        None, description="Custom targeting attributes"
    )

    @field_validator("flag_type")
    @classmethod
    def validate_flag_type(cls, v: str) -> str:
        """Validate flag type is one of allowed values."""
        allowed_types = {"boolean", "percentage", "variant"}
        if v not in allowed_types:
            raise ValueError(f"flag_type must be one of: {', '.join(allowed_types)}")
        return v

    @field_validator("variants")
    @classmethod
    def validate_variants(cls, v: dict[str, float] | None) -> dict[str, float] | None:
        """Validate variant weights sum to 1.0."""
        if v is not None:
            total = sum(v.values())
            if not (0.99 <= total <= 1.01):  # Allow small floating point errors
                raise ValueError(f"Variant weights must sum to 1.0, got {total}")
            for variant_name, weight in v.items():
                if not (0.0 <= weight <= 1.0):
                    raise ValueError(
                        f"Variant weight must be between 0.0 and 1.0, got {weight} for {variant_name}"
                    )
        return v

    @field_validator("environments")
    @classmethod
    def validate_environments(cls, v: list[str] | None) -> list[str] | None:
        """Validate environment names."""
        if v is not None:
            allowed_envs = {"development", "staging", "production", "test"}
            for env in v:
                if env not in allowed_envs:
                    raise ValueError(
                        f"Invalid environment: {env}. Allowed: {', '.join(allowed_envs)}"
                    )
        return v

    @field_validator("target_roles")
    @classmethod
    def validate_roles(cls, v: list[str] | None) -> list[str] | None:
        """Validate role names."""
        if v is not None:
            allowed_roles = {
                "admin",
                "coordinator",
                "faculty",
                "clinical_staff",
                "rn",
                "lpn",
                "msa",
                "resident",
            }
            for role in v:
                if role not in allowed_roles:
                    raise ValueError(
                        f"Invalid role: {role}. Allowed: {', '.join(allowed_roles)}"
                    )
        return v


class FeatureFlagCreate(FeatureFlagBase):
    """Schema for creating a feature flag."""

    pass


class FeatureFlagUpdate(BaseModel):
    """Schema for updating a feature flag (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    flag_type: str | None = None
    enabled: bool | None = None
    rollout_percentage: float | None = Field(None, ge=0.0, le=1.0)
    environments: list[str] | None = None
    target_user_ids: list[str] | None = None
    target_roles: list[str] | None = None
    variants: dict[str, float] | None = None
    dependencies: list[str] | None = None
    custom_attributes: dict[str, Any] | None = None

    @field_validator("flag_type")
    @classmethod
    def validate_flag_type(cls, v: str | None) -> str | None:
        """Validate flag type is one of allowed values."""
        if v is not None:
            allowed_types = {"boolean", "percentage", "variant"}
            if v not in allowed_types:
                raise ValueError(
                    f"flag_type must be one of: {', '.join(allowed_types)}"
                )
        return v

    @field_validator("variants")
    @classmethod
    def validate_variants(cls, v: dict[str, float] | None) -> dict[str, float] | None:
        """Validate variant weights sum to 1.0."""
        if v is not None:
            total = sum(v.values())
            if not (0.99 <= total <= 1.01):
                raise ValueError(f"Variant weights must sum to 1.0, got {total}")
        return v

    @field_validator("environments")
    @classmethod
    def validate_environments(cls, v: list[str] | None) -> list[str] | None:
        """Validate environment names."""
        if v is not None:
            allowed_envs = {"development", "staging", "production", "test"}
            for env in v:
                if env not in allowed_envs:
                    raise ValueError(
                        f"Invalid environment: {env}. Allowed: {', '.join(allowed_envs)}"
                    )
        return v


class FeatureFlagResponse(FeatureFlagBase):
    """Schema for feature flag responses."""

    id: UUID
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeatureFlagEvaluationRequest(BaseModel):
    """Schema for evaluating a feature flag."""

    flag_key: str = Field(..., description="Feature flag key to evaluate")
    user_id: str | None = Field(None, description="User ID for targeting")
    user_role: str | None = Field(None, description="User role for targeting")
    environment: str | None = Field(
        None, description="Environment (dev, staging, production)"
    )
    context: dict[str, Any] | None = Field(
        None, description="Additional context for evaluation"
    )


class FeatureFlagEvaluationResponse(BaseModel):
    """Schema for feature flag evaluation result."""

    enabled: bool = Field(
        ..., description="Whether the feature is enabled for this context"
    )
    variant: str | None = Field(None, description="A/B test variant (if applicable)")
    flag_type: str = Field(..., description="Type of flag")
    reason: str | None = Field(None, description="Reason for the evaluation result")


class FeatureFlagBulkEvaluationRequest(BaseModel):
    """Schema for evaluating multiple feature flags at once."""

    flag_keys: list[str] = Field(
        ..., description="List of feature flag keys to evaluate"
    )
    user_id: str | None = Field(None, description="User ID for targeting")
    user_role: str | None = Field(None, description="User role for targeting")
    environment: str | None = Field(None, description="Environment")
    context: dict[str, Any] | None = Field(None, description="Additional context")


class FeatureFlagBulkEvaluationResponse(BaseModel):
    """Schema for bulk feature flag evaluation results."""

    flags: dict[str, FeatureFlagEvaluationResponse] = Field(
        ..., description="Map of flag key to evaluation result"
    )


class FeatureFlagAuditResponse(BaseModel):
    """Schema for feature flag audit log entries."""

    id: UUID
    flag_id: UUID
    user_id: UUID | None
    username: str | None
    action: str
    changes: dict[str, Any] | None
    reason: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class FeatureFlagStatsResponse(BaseModel):
    """Schema for feature flag statistics."""

    total_flags: int
    enabled_flags: int
    disabled_flags: int
    percentage_rollout_flags: int
    variant_flags: int
    flags_by_environment: dict[str, int]
    recent_evaluations: int
    unique_users: int


class FeatureFlagListResponse(BaseModel):
    """Schema for paginated feature flag list."""

    flags: list[FeatureFlagResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
