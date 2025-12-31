"""Pydantic schemas for Fatigue Risk Management System API.

Defines request/response schemas for:
- Fatigue assessments
- Alertness predictions
- Hazard alerts
- Interventions
- Dashboard data
"""

from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Samn-Perelli Assessment Schemas
# =============================================================================


class SamnPerelliAssessmentRequest(BaseModel):
    """Request to submit a Samn-Perelli fatigue assessment."""

    level: int = Field(..., ge=1, le=7, description="Samn-Perelli level (1-7)")
    notes: str | None = Field(None, max_length=1000)


class SamnPerelliAssessmentResponse(BaseModel):
    """Response with Samn-Perelli assessment details."""

    resident_id: str
    level: int
    level_name: str
    description: str
    assessed_at: datetime
    is_self_reported: bool
    safe_for_duty: bool
    duty_restrictions: list[str] | None = None
    recommended_rest_hours: float | None = None
    notes: str | None = None


# =============================================================================
# Fatigue Score Schemas
# =============================================================================


class FatigueScoreRequest(BaseModel):
    """Request for real-time fatigue score calculation."""

    hours_awake: float = Field(..., ge=0, description="Hours since last sleep")
    hours_worked_24h: float = Field(..., ge=0, description="Hours worked in last 24h")
    consecutive_night_shifts: int = Field(0, ge=0)
    time_of_day_hour: int = Field(12, ge=0, le=23)
    prior_sleep_hours: float = Field(7.0, ge=0)


class FatigueScoreResponse(BaseModel):
    """Response with calculated fatigue score."""

    samn_perelli_level: int
    samn_perelli_name: str
    alertness_score: float
    circadian_phase: str
    factors: dict


# =============================================================================
# Alertness Prediction Schemas
# =============================================================================


class AlertnessPredictionResponse(BaseModel):
    """Response with alertness prediction."""

    resident_id: str
    prediction_time: datetime
    alertness_score: float
    alertness_percent: int
    samn_perelli: dict
    circadian_phase: str
    hours_awake: float
    sleep_debt: float
    performance_capacity: int
    risk_level: str
    contributing_factors: list[str]
    recommendations: list[str]


class ShiftPatternInput(BaseModel):
    """Input for a shift in schedule assessment."""

    type: str = Field(..., description="Shift type (day, night, call_24, etc.)")
    start: str = Field(..., description="ISO datetime string")
    end: str = Field(..., description="ISO datetime string")
    prior_sleep: float = Field(7.0, ge=0)


class ScheduleFatigueAssessmentRequest(BaseModel):
    """Request to assess fatigue risk for proposed schedule."""

    proposed_shifts: list[ShiftPatternInput]


class ScheduleFatigueAssessmentResponse(BaseModel):
    """Response with schedule fatigue risk assessment."""

    resident_id: str
    shifts_evaluated: int
    overall_risk: str
    metrics: dict
    hazard_distribution: dict
    high_risk_windows: list[dict]
    trajectory: list[dict]
    recommendations: list[str]


# =============================================================================
# Hazard Alert Schemas
# =============================================================================


class HazardAlertResponse(BaseModel):
    """Response with fatigue hazard alert details."""

    resident_id: str
    hazard_level: str
    hazard_level_name: str
    detected_at: datetime
    triggers: list[str]
    alertness_score: float | None = None
    sleep_debt: float | None = None
    hours_awake: float | None = None
    samn_perelli: int | None = None
    required_mitigations: list[str]
    recommended_mitigations: list[str]
    acgme_risk: bool
    escalation_time: datetime | None = None
    notes: str | None = None


class HazardScanResponse(BaseModel):
    """Response with hazard scan results for multiple residents."""

    scanned_at: datetime
    total_residents: int
    hazards_found: int
    by_level: dict
    critical_count: int
    acgme_risk_count: int
    residents: list[dict]


# =============================================================================
# Fatigue Profile Schemas
# =============================================================================


class FatigueProfileResponse(BaseModel):
    """Complete fatigue profile for a resident."""

    resident_id: str
    resident_name: str
    pgy_level: int
    generated_at: datetime
    current_state: dict
    hazard: dict
    work_history: dict
    predictions: dict
    acgme: dict


# =============================================================================
# Sleep Debt Schemas
# =============================================================================


class SleepDebtStateResponse(BaseModel):
    """Response with current sleep debt state."""

    resident_id: str
    current_debt_hours: float
    last_updated: datetime
    consecutive_deficit_days: int
    recovery_sleep_needed: float
    chronic_debt: bool
    debt_severity: str
    impairment_equivalent_bac: float


class SleepDebtTrajectoryRequest(BaseModel):
    """Request to predict sleep debt trajectory."""

    planned_sleep_hours: list[float] = Field(
        ...,
        min_length=1,
        max_length=30,
        description="Planned sleep hours for each upcoming day",
    )
    start_debt: float | None = Field(None, ge=0)


class SleepDebtTrajectoryResponse(BaseModel):
    """Response with predicted sleep debt trajectory."""

    resident_id: str
    days_predicted: int
    trajectory: list[dict]
    recovery_estimate_nights: int


# =============================================================================
# Dashboard Schemas
# =============================================================================


class TeamHeatmapRequest(BaseModel):
    """Request for team fatigue heatmap."""

    target_date: date
    include_predictions: bool = True


class TeamHeatmapResponse(BaseModel):
    """Response with team fatigue heatmap."""

    date: str
    generated_at: datetime
    residents: list[dict]
    hours: list[int]


class CircadianPhaseInfo(BaseModel):
    """Information about a circadian phase."""

    phase: str
    name: str
    time_range: str
    alertness_multiplier: float
    description: str


class HazardLevelInfo(BaseModel):
    """Information about a hazard level."""

    level: str
    name: str
    description: str
    thresholds: dict
    required_mitigations: list[str]


class MitigationTypeInfo(BaseModel):
    """Information about a mitigation type."""

    type: str
    name: str
    description: str


# =============================================================================
# Temporal Constraints Export Schema
# =============================================================================


class TemporalConstraintsExport(BaseModel):
    """Export of temporal constraints for holographic hub."""

    version: str
    generated_at: datetime
    framework: str
    references: list[str]
    circadian_rhythm: dict
    sleep_homeostasis: dict
    samn_perelli_scale: dict
    hazard_thresholds: dict
    acgme_integration: dict
    scheduling_constraints: dict


# =============================================================================
# Intervention Schemas
# =============================================================================


class InterventionCreateRequest(BaseModel):
    """Request to record a fatigue intervention."""

    alert_id: UUID | None = None
    intervention_type: str
    description: str | None = None
    authorized_by: str | None = None
    authorization_method: str = "manual"


class InterventionUpdateRequest(BaseModel):
    """Request to update intervention outcome."""

    outcome: str
    outcome_notes: str | None = None
    post_alertness: float | None = None


class InterventionResponse(BaseModel):
    """Response with intervention details."""

    id: str
    person_id: str
    alert_id: str | None = None
    intervention_type: str
    description: str | None = None
    authorized_by: str | None = None
    authorization_method: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    outcome: str | None = None
    outcome_notes: str | None = None
    pre_alertness: float | None = None
    post_alertness: float | None = None
    alertness_improvement: float | None = None


# =============================================================================
# ACGME Validation Schemas
# =============================================================================


class ACGMEFatigueValidationRequest(BaseModel):
    """Request to validate schedule against ACGME via FRMS."""

    resident_id: UUID
    schedule_start: date
    schedule_end: date


class ACGMEFatigueValidationResponse(BaseModel):
    """Response with ACGME fatigue validation results."""

    resident_id: str
    schedule_period: dict
    acgme_compliant: bool
    fatigue_compliant: bool
    hours_summary: dict
    fatigue_risk_periods: list[dict]
    recommendations: list[str]
    validation_details: dict
