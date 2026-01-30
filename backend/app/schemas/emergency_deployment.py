"""Emergency deployment response schemas."""

from datetime import date, datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class EmergencyStrategy(str, Enum):
    """Strategy used to handle emergency deployment."""

    INCREMENTAL = "incremental"
    CASCADE = "cascade"
    FALLBACK = "fallback"


class FragilityAssessment(BaseModel):
    """Fragility assessment result before repair attempt."""

    fragility_score: float = Field(ge=0.0, le=1.0, description="0=resilient, 1=brittle")
    rd_mean: float = Field(ge=0.0, description="Average recovery distance")
    rd_max: int = Field(ge=0, description="Maximum recovery distance")
    affected_slots: int = Field(
        ge=0, description="Number of slots affected by deployment"
    )
    recommended_strategy: EmergencyStrategy
    assessment_time_ms: float = Field(
        ge=0, description="Assessment time in milliseconds"
    )


class RepairOutcome(BaseModel):
    """Outcome of a repair attempt."""

    success: bool
    strategy_used: EmergencyStrategy
    slots_repaired: int = 0
    slots_remaining: int = 0
    cascade_steps: int = 0
    fallback_activated: str | None = None
    execution_time_ms: float = Field(ge=0, description="Execution time in milliseconds")
    details: list[str] = Field(default_factory=list)


class HealthVerification(BaseModel):
    """Health verification after repair."""

    coverage_rate: float = Field(
        ge=0.0, le=1.0, description="Post-repair coverage rate"
    )
    is_healthy: bool = Field(description="Coverage >= 95%")
    escalated: bool = Field(False, description="Whether crisis mode was activated")
    escalation_severity: str | None = Field(
        None, description="Crisis severity if escalated"
    )


class EmergencyDeploymentRequest(BaseModel):
    """Request emergency deployment response for a person."""

    person_id: UUID = Field(..., description="Deployed person ID")
    start_date: date = Field(..., description="Deployment start date (inclusive)")
    end_date: date = Field(..., description="Deployment end date (inclusive)")
    reason: str = Field(
        "deployment", description="Reason (deployment, emergency_leave, etc.)"
    )
    notes: str | None = Field(None, description="Optional notes for audit")
    dry_run: bool = Field(
        True, description="If true, assess and plan only; don't apply"
    )
    force_strategy: EmergencyStrategy | None = Field(
        None, description="Force a specific strategy (overrides auto-selection)"
    )


class EmergencyDeploymentResponse(BaseModel):
    """Response from emergency deployment handler."""

    request_id: UUID = Field(description="Unique ID for this emergency response")
    person_id: UUID
    start_date: date
    end_date: date
    dry_run: bool

    # Assessment phase
    assessment: FragilityAssessment

    # Repair phase (populated if not dry_run)
    repair_outcome: RepairOutcome | None = None

    # Verification phase (populated if repair attempted)
    health_check: HealthVerification | None = None

    # Summary
    overall_success: bool = Field(
        description="True if schedule is healthy after response"
    )
    total_time_ms: float = Field(ge=0, description="Total response time")
    recommendations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    # Audit
    timestamp: datetime = Field(default_factory=datetime.now)
