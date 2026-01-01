"""Pydantic schemas for experiments/A/B testing API endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.experiments.ab_testing import (
    ExperimentConfig,
    ExperimentStatus,
    ExperimentTargeting,
    MetricType,
    Variant,
)

# =============================================================================
# Request Schemas
# =============================================================================


class ExperimentCreateRequest(BaseModel):
    """Request schema for creating a new experiment."""

    key: str = Field(
        ..., description="Unique experiment identifier", min_length=1, max_length=100
    )
    name: str = Field(
        ..., description="Human-readable experiment name", min_length=1, max_length=255
    )
    description: str = Field(default="", description="Experiment description")
    hypothesis: str = Field(default="", description="Hypothesis being tested")
    variants: list[Variant] = Field(
        ..., min_length=2, description="Experiment variants (minimum 2)"
    )
    targeting: ExperimentTargeting = Field(
        default_factory=ExperimentTargeting, description="Targeting rules"
    )
    config: ExperimentConfig = Field(
        default_factory=ExperimentConfig, description="Experiment configuration"
    )
    start_date: datetime | None = Field(
        default=None, description="Scheduled start date"
    )
    end_date: datetime | None = Field(default=None, description="Scheduled end date")


class ExperimentUpdateRequest(BaseModel):
    """Request schema for updating an experiment."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Human-readable experiment name",
    )
    description: str | None = Field(
        default=None, max_length=2000, description="Experiment description"
    )
    hypothesis: str | None = Field(
        default=None, max_length=1000, description="Hypothesis being tested"
    )
    targeting: ExperimentTargeting | None = Field(
        default=None, description="Targeting rules"
    )
    config: ExperimentConfig | None = Field(
        default=None, description="Experiment configuration"
    )
    end_date: datetime | None = Field(default=None, description="Scheduled end date")


class UserAssignmentRequest(BaseModel):
    """Request schema for assigning a user to an experiment variant."""

    user_id: str = Field(
        ..., min_length=1, max_length=100, description="User identifier"
    )
    user_attributes: dict[str, Any] = Field(
        default_factory=dict, description="User attributes for targeting evaluation"
    )
    force_variant: str | None = Field(
        default=None,
        max_length=100,
        description="Force assignment to specific variant (override)",
    )


class MetricTrackRequest(BaseModel):
    """Request schema for tracking a metric."""

    user_id: str = Field(..., description="User identifier")
    variant_key: str = Field(..., description="Variant identifier")
    metric_name: str = Field(
        ..., description="Metric name", min_length=1, max_length=100
    )
    value: float = Field(..., description="Metric value")
    metric_type: MetricType = Field(
        default=MetricType.NUMERIC, description="Type of metric"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ConcludeExperimentRequest(BaseModel):
    """Request schema for concluding an experiment."""

    winning_variant: str = Field(
        ..., min_length=1, max_length=100, description="The winning variant key"
    )
    notes: str = Field(default="", max_length=2000, description="Conclusion notes")


# =============================================================================
# Response Schemas
# =============================================================================


class VariantResponse(BaseModel):
    """Response schema for a variant."""

    key: str
    name: str
    description: str
    allocation: int
    is_control: bool
    config: dict[str, Any]


class ExperimentResponse(BaseModel):
    """Response schema for an experiment."""

    key: str
    name: str
    description: str
    hypothesis: str
    variants: list[VariantResponse]
    targeting: ExperimentTargeting
    config: ExperimentConfig
    status: ExperimentStatus
    start_date: datetime | None
    end_date: datetime | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class ExperimentListResponse(BaseModel):
    """Response schema for list of experiments."""

    experiments: list[ExperimentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class VariantAssignmentResponse(BaseModel):
    """Response schema for user assignment to variant."""

    experiment_key: str
    user_id: str
    variant_key: str
    assigned_at: datetime
    is_override: bool


class MetricDataResponse(BaseModel):
    """Response schema for tracked metric."""

    experiment_key: str
    user_id: str
    variant_key: str
    metric_name: str
    metric_type: MetricType
    value: float
    timestamp: datetime


class VariantMetricsResponse(BaseModel):
    """Response schema for variant metrics summary."""

    variant_key: str
    user_count: int
    metrics: dict[str, dict[str, float]]


class ExperimentResultsResponse(BaseModel):
    """Response schema for experiment results."""

    experiment_key: str
    status: ExperimentStatus
    start_date: datetime | None
    end_date: datetime | None
    duration_days: float
    total_users: int
    variant_metrics: list[VariantMetricsResponse]
    is_significant: bool
    confidence_level: float
    p_value: float | None
    winning_variant: str | None
    recommendation: str
    statistical_power: float | None


class ExperimentLifecycleResponse(BaseModel):
    """Response schema for lifecycle event."""

    experiment_key: str
    event_type: str
    previous_status: ExperimentStatus | None
    new_status: ExperimentStatus
    triggered_by: str
    timestamp: datetime
    notes: str
    metadata: dict[str, Any]


class ExperimentLifecycleListResponse(BaseModel):
    """Response schema for list of lifecycle events."""

    events: list[ExperimentLifecycleResponse]
    total: int


class ExperimentStatsResponse(BaseModel):
    """Response schema for experiment statistics."""

    total_experiments: int
    running_experiments: int
    completed_experiments: int
    draft_experiments: int
    paused_experiments: int
    cancelled_experiments: int
    total_users_assigned: int
    total_metrics_tracked: int
