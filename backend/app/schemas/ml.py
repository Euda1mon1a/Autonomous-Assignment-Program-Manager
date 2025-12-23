"""Pydantic schemas for ML API endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# Request Schemas
# =============================================================================


class TrainModelsRequest(BaseModel):
    """Request to train ML models."""

    model_types: list[str] | None = Field(
        default=None,
        description="Models to train: 'preference', 'conflict', 'workload'. None = all.",
    )
    lookback_days: int | None = Field(
        default=None,
        ge=30,
        le=730,
        description="Days of historical data to use. Defaults to ML_TRAINING_LOOKBACK_DAYS.",
    )
    force_retrain: bool = Field(
        default=False,
        description="Force retraining even if models exist.",
    )


class ScoreScheduleRequest(BaseModel):
    """Request to score a schedule."""

    schedule_id: str | None = Field(
        default=None,
        description="ID of existing schedule to score.",
    )
    schedule_data: dict[str, Any] | None = Field(
        default=None,
        description="Schedule data to score (if not using schedule_id).",
    )
    include_suggestions: bool = Field(
        default=True,
        description="Include improvement suggestions in response.",
    )


class PredictConflictRequest(BaseModel):
    """Request to predict conflict probability for an assignment."""

    person_id: str = Field(..., description="Person ID")
    block_id: str = Field(..., description="Block ID")
    rotation_id: str | None = Field(default=None, description="Rotation template ID")
    existing_assignments: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Existing assignments for context.",
    )


class PredictPreferenceRequest(BaseModel):
    """Request to predict preference score for an assignment."""

    person_id: str = Field(..., description="Person ID")
    rotation_id: str = Field(..., description="Rotation template ID")
    block_id: str = Field(..., description="Block ID")


class WorkloadAnalysisRequest(BaseModel):
    """Request for workload analysis."""

    person_ids: list[str] | None = Field(
        default=None,
        description="Person IDs to analyze. None = all.",
    )
    start_date: str | None = Field(
        default=None,
        description="Start date (ISO format).",
    )
    end_date: str | None = Field(
        default=None,
        description="End date (ISO format).",
    )


# =============================================================================
# Response Schemas
# =============================================================================


class ModelStatusResponse(BaseModel):
    """Response for individual model status."""

    name: str
    available: bool
    last_trained: datetime | None
    age_days: int | None
    metrics: dict[str, float] | None = None


class ModelHealthResponse(BaseModel):
    """Response for ML model health check."""

    ml_enabled: bool
    models_available: str
    models: list[ModelStatusResponse]
    recommendations: list[str]


class TrainingResultResponse(BaseModel):
    """Response for model training result."""

    model_name: str
    status: str
    samples: int | None = None
    metrics: dict[str, float] | None = None
    error: str | None = None
    path: str | None = None


class TrainModelsResponse(BaseModel):
    """Response for train models request."""

    timestamp: datetime
    lookback_days: int
    models_trained: int
    results: dict[str, TrainingResultResponse]
    task_id: str | None = None


class ScoreComponentResponse(BaseModel):
    """Response for individual score component."""

    name: str
    score: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    details: dict[str, Any] = Field(default_factory=dict)


class SuggestionResponse(BaseModel):
    """Response for improvement suggestion."""

    type: str
    priority: str = Field(description="high, medium, low")
    description: str
    impact: float = Field(ge=0.0, le=1.0, description="Expected improvement")
    affected_items: list[str] = Field(default_factory=list)


class ScheduleScoreResponse(BaseModel):
    """Response for schedule scoring."""

    overall_score: float = Field(ge=0.0, le=1.0)
    grade: str = Field(description="Letter grade A+ to F")
    components: list[ScoreComponentResponse]
    suggestions: list[SuggestionResponse] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConflictPredictionResponse(BaseModel):
    """Response for conflict prediction."""

    conflict_probability: float = Field(ge=0.0, le=1.0)
    risk_level: str = Field(description="CRITICAL, HIGH, MEDIUM, LOW, MINIMAL")
    risk_factors: list[str]
    recommendation: str


class PreferencePredictionResponse(BaseModel):
    """Response for preference prediction."""

    preference_score: float = Field(ge=0.0, le=1.0)
    interpretation: str
    contributing_factors: list[dict[str, Any]]


class PersonWorkloadResponse(BaseModel):
    """Response for individual person workload."""

    person_id: str
    person_name: str
    current_utilization: float
    optimal_utilization: float
    is_overloaded: bool
    workload_cluster: int | None = None


class WorkloadAnalysisResponse(BaseModel):
    """Response for workload analysis."""

    total_people: int
    overloaded_count: int
    underutilized_count: int
    fairness_score: float = Field(ge=0.0, le=1.0)
    gini_coefficient: float = Field(ge=0.0, le=1.0)
    people: list[PersonWorkloadResponse]
    rebalancing_suggestions: list[SuggestionResponse]
