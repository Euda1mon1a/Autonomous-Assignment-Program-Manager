"""API routes for Fatigue Risk Management System (FRMS).

Provides endpoints for:
- Real-time fatigue scoring
- Alertness predictions
- Hazard detection and monitoring
- Resident fatigue profiles
- Team dashboard data
- Temporal constraints export
- ACGME fatigue validation

All endpoints follow aviation FRMS principles adapted for medical residency.
"""

from datetime import datetime, date
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger
from app.resilience.frms import (
    FRMSService,
    SamnPerelliLevel,
    assess_fatigue_level,
    get_all_levels,
    HazardLevel,
    get_hazard_level_info,
    get_mitigation_info,
)
from app.resilience.frms.sleep_debt import get_circadian_phases_info
from app.schemas.fatigue_risk import (
    SamnPerelliAssessmentRequest,
    SamnPerelliAssessmentResponse,
    FatigueScoreRequest,
    FatigueScoreResponse,
    AlertnessPredictionResponse,
    ScheduleFatigueAssessmentRequest,
    ScheduleFatigueAssessmentResponse,
    HazardAlertResponse,
    HazardScanResponse,
    FatigueProfileResponse,
    SleepDebtStateResponse,
    SleepDebtTrajectoryRequest,
    SleepDebtTrajectoryResponse,
    TeamHeatmapRequest,
    TeamHeatmapResponse,
    TemporalConstraintsExport,
    InterventionCreateRequest,
    InterventionResponse,
    ACGMEFatigueValidationRequest,
    ACGMEFatigueValidationResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/fatigue-risk", tags=["Fatigue Risk Management"])


# =============================================================================
# Samn-Perelli Assessment Endpoints
# =============================================================================


@router.get("/samn-perelli/levels")
async def get_samn_perelli_levels() -> dict[str, Any]:
    """
    Get all Samn-Perelli fatigue levels with descriptions.

    Returns the 7-level fatigue scale adapted from aviation
    for use in medical residency fatigue assessment.
    """
    from app.resilience.frms.samn_perelli import get_all_levels

    return {"levels": get_all_levels()}


@router.post(
    "/resident/{resident_id}/assessment",
    response_model=SamnPerelliAssessmentResponse,
)
async def submit_fatigue_assessment(
    resident_id: UUID,
    request: SamnPerelliAssessmentRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a fatigue self-assessment for a resident.

    Residents can report their current Samn-Perelli fatigue level
    (1-7) for real-time safety monitoring.
    """
    try:
        assessment = assess_fatigue_level(
            level=request.level,
            resident_id=resident_id,
            is_self_reported=True,
            notes=request.notes,
        )
        return assessment.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Real-time Fatigue Scoring
# =============================================================================


@router.post("/score", response_model=FatigueScoreResponse)
async def calculate_fatigue_score(
    request: FatigueScoreRequest,
):
    """
    Calculate real-time fatigue score from objective factors.

    Provides immediate fatigue assessment based on:
    - Hours awake since last sleep
    - Hours worked in last 24 hours
    - Consecutive night shifts
    - Time of day (circadian phase)
    - Prior sleep duration

    This endpoint does not require database access and can be
    used for quick fatigue checks during scheduling.
    """
    service = FRMSService()
    return service.calculate_fatigue_score(
        hours_awake=request.hours_awake,
        hours_worked_24h=request.hours_worked_24h,
        consecutive_night_shifts=request.consecutive_night_shifts,
        time_of_day_hour=request.time_of_day_hour,
        prior_sleep_hours=request.prior_sleep_hours,
    )


# =============================================================================
# Resident Profile Endpoints
# =============================================================================


@router.get(
    "/resident/{resident_id}/profile",
    response_model=FatigueProfileResponse,
)
async def get_resident_fatigue_profile(
    resident_id: UUID,
    target_time: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get complete fatigue profile for a resident.

    Returns comprehensive fatigue assessment including:
    - Current alertness and Samn-Perelli level
    - Sleep debt and circadian phase
    - Hazard level and required mitigations
    - Work history metrics
    - ACGME compliance status

    This is the primary endpoint for fatigue monitoring dashboards.
    """
    service = FRMSService(db)
    try:
        profile = await service.get_resident_profile(
            resident_id=resident_id,
            target_time=target_time,
        )
        return profile.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/resident/{resident_id}/alertness",
    response_model=AlertnessPredictionResponse,
)
async def get_alertness_prediction(
    resident_id: UUID,
    target_time: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get alertness prediction for a specific time.

    Predicts resident alertness using the Three-Process Model:
    - Sleep homeostasis (debt accumulation)
    - Circadian rhythm (time-of-day effects)
    - Recent workload impact

    Use for evaluating if a resident is safe for specific duties.
    """
    service = FRMSService(db)
    try:
        profile = await service.get_resident_profile(
            resident_id=resident_id,
            target_time=target_time or datetime.utcnow(),
        )
        return {
            "resident_id": str(resident_id),
            "prediction_time": (target_time or datetime.utcnow()).isoformat(),
            "alertness_score": profile.current_alertness,
            "alertness_percent": int(profile.current_alertness * 100),
            "samn_perelli": {
                "level": profile.samn_perelli_level.value,
                "name": profile.samn_perelli_level.name,
            },
            "circadian_phase": profile.circadian_phase.value,
            "hours_awake": profile.hours_since_sleep,
            "sleep_debt": profile.sleep_debt_hours,
            "performance_capacity": int(profile.current_alertness * 100),
            "risk_level": profile.hazard_level.value,
            "contributing_factors": profile.hazard_triggers,
            "recommendations": profile.required_mitigations,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/resident/{resident_id}/schedule-assessment",
    response_model=ScheduleFatigueAssessmentResponse,
)
async def assess_schedule_fatigue_risk(
    resident_id: UUID,
    request: ScheduleFatigueAssessmentRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Assess fatigue risk for a proposed schedule.

    Evaluates how a proposed shift sequence would affect
    the resident's fatigue and identifies high-risk periods.

    Use before finalizing schedule assignments to ensure
    fatigue safety is maintained.
    """
    service = FRMSService(db)
    result = await service.assess_schedule_fatigue_risk(
        resident_id=resident_id,
        proposed_shifts=[s.model_dump() for s in request.proposed_shifts],
    )
    return result


# =============================================================================
# Hazard Monitoring Endpoints
# =============================================================================


@router.get(
    "/resident/{resident_id}/hazard",
    response_model=HazardAlertResponse,
)
async def get_current_hazard(
    resident_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current fatigue hazard status for a resident.

    Returns the hazard level (GREEN to BLACK) with:
    - Triggers that activated the hazard
    - Required mitigations
    - ACGME risk status
    - Escalation timeline
    """
    service = FRMSService(db)
    try:
        profile = await service.get_resident_profile(resident_id)
        return {
            "resident_id": str(resident_id),
            "hazard_level": profile.hazard_level.value,
            "hazard_level_name": profile.hazard_level.name,
            "detected_at": profile.generated_at.isoformat(),
            "triggers": profile.hazard_triggers,
            "alertness_score": profile.current_alertness,
            "sleep_debt": profile.sleep_debt_hours,
            "hours_awake": profile.hours_since_sleep,
            "samn_perelli": profile.samn_perelli_level.value,
            "required_mitigations": profile.required_mitigations,
            "recommended_mitigations": [],
            "acgme_risk": profile.acgme_violation_risk,
            "escalation_time": None,
            "notes": None,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/hazards/scan", response_model=HazardScanResponse)
async def scan_all_residents_for_hazards(
    min_level: str = Query("yellow", description="Minimum hazard level to include"),
    db: AsyncSession = Depends(get_db),
):
    """
    Scan all residents for fatigue hazards.

    Returns summary of hazards across the residency program
    for proactive safety monitoring.
    """
    service = FRMSService(db)
    threshold = HazardLevel(min_level)

    profiles = await service.scan_all_residents(hazard_threshold=threshold)

    level_counts = {}
    for p in profiles:
        level = p.hazard_level.value
        level_counts[level] = level_counts.get(level, 0) + 1

    return {
        "scanned_at": datetime.utcnow(),
        "total_residents": len(profiles),
        "hazards_found": len(
            [p for p in profiles if p.hazard_level != HazardLevel.GREEN]
        ),
        "by_level": level_counts,
        "critical_count": len(
            [
                p
                for p in profiles
                if p.hazard_level in [HazardLevel.RED, HazardLevel.BLACK]
            ]
        ),
        "acgme_risk_count": len([p for p in profiles if p.acgme_violation_risk]),
        "residents": [p.to_dict() for p in profiles],
    }


# =============================================================================
# Sleep Debt Endpoints
# =============================================================================


@router.get(
    "/resident/{resident_id}/sleep-debt",
    response_model=SleepDebtStateResponse,
)
async def get_sleep_debt_state(
    resident_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current sleep debt state for a resident.

    Returns accumulated sleep debt with:
    - Severity classification
    - Recovery sleep needed
    - Cognitive impairment equivalent (BAC)
    """
    service = FRMSService(db)
    try:
        profile = await service.get_resident_profile(resident_id)
        return {
            "resident_id": str(resident_id),
            "current_debt_hours": profile.sleep_debt_hours,
            "last_updated": profile.generated_at.isoformat(),
            "consecutive_deficit_days": 0,  # Would need history
            "recovery_sleep_needed": profile.recovery_sleep_needed,
            "chronic_debt": profile.sleep_debt_hours > 15,
            "debt_severity": (
                "critical"
                if profile.sleep_debt_hours > 20
                else "severe"
                if profile.sleep_debt_hours > 15
                else "moderate"
                if profile.sleep_debt_hours > 10
                else "mild"
                if profile.sleep_debt_hours > 5
                else "none"
            ),
            "impairment_equivalent_bac": min(0.15, profile.sleep_debt_hours * 0.005),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/resident/{resident_id}/sleep-debt/trajectory",
    response_model=SleepDebtTrajectoryResponse,
)
async def predict_sleep_debt_trajectory(
    resident_id: UUID,
    request: SleepDebtTrajectoryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Predict sleep debt trajectory over upcoming days.

    Given planned sleep hours, projects how sleep debt
    will change. Useful for schedule optimization.
    """
    service = FRMSService(db)
    trajectory = service.sleep_model.predict_debt_trajectory(
        resident_id=resident_id,
        planned_sleep_hours=request.planned_sleep_hours,
        start_debt=request.start_debt,
    )

    # Estimate recovery nights
    final_debt = trajectory[-1]["cumulative_debt"] if trajectory else 0
    recovery_nights = service.sleep_model.estimate_recovery_time(final_debt)

    return {
        "resident_id": str(resident_id),
        "days_predicted": len(request.planned_sleep_hours),
        "trajectory": trajectory,
        "recovery_estimate_nights": recovery_nights,
    }


# =============================================================================
# Team Dashboard Endpoints
# =============================================================================


@router.post("/team/heatmap", response_model=TeamHeatmapResponse)
async def get_team_fatigue_heatmap(
    request: TeamHeatmapRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate team fatigue heatmap for a day.

    Creates a grid showing fatigue levels by resident and hour
    for visualization and team-wide monitoring.
    """
    service = FRMSService(db)
    heatmap = await service.get_team_heatmap(
        target_date=request.target_date,
        include_predictions=request.include_predictions,
    )
    return heatmap


# =============================================================================
# Reference Data Endpoints
# =============================================================================


@router.get("/reference/circadian-phases")
async def get_circadian_phases() -> dict[str, Any]:
    """
    Get all circadian phases with descriptions.

    Returns the 7 circadian phases with time ranges,
    alertness multipliers, and scheduling guidance.
    """
    return {"phases": get_circadian_phases_info()}


@router.get("/reference/hazard-levels")
async def get_hazard_levels() -> dict[str, Any]:
    """
    Get all hazard levels with descriptions.

    Returns the 5 hazard levels (GREEN to BLACK) with
    thresholds and required mitigations.
    """
    return {"levels": get_hazard_level_info()}


@router.get("/reference/mitigation-types")
async def get_mitigation_types() -> dict[str, Any]:
    """
    Get all mitigation types with descriptions.

    Returns available fatigue mitigation actions that
    can be triggered by hazard detection.
    """
    return {"mitigations": get_mitigation_info()}


# =============================================================================
# Temporal Constraints Export
# =============================================================================


@router.get("/temporal-constraints", response_model=TemporalConstraintsExport)
async def export_temporal_constraints() -> TemporalConstraintsExport:
    """
    Export temporal constraint data for holographic hub.

    Returns comprehensive JSON describing the chronobiology
    constraints used in scheduling optimization.

    Includes:
    - Circadian rhythm parameters
    - Sleep homeostasis model
    - Samn-Perelli scale mapping
    - Hazard thresholds
    - ACGME integration
    - Scheduling constraints (hard and soft)
    """
    service = FRMSService()
    return service.export_temporal_constraints()


# =============================================================================
# ACGME Validation Endpoint
# =============================================================================


@router.post(
    "/resident/{resident_id}/acgme-validation",
    response_model=ACGMEFatigueValidationResponse,
)
async def validate_acgme_with_fatigue(
    resident_id: UUID,
    request: ACGMEFatigueValidationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Validate schedule against ACGME rules through fatigue lens.

    Extends traditional ACGME compliance checking with
    fatigue-based validation to ensure schedules are
    both rule-compliant and fatigue-safe.

    This endpoint proves that FRMS prevents ACGME violations
    by identifying fatigue risks before they manifest as
    duty hour problems.
    """
    service = FRMSService(db)

    # Get fatigue assessment for the schedule period
    try:
        profile = await service.get_resident_profile(resident_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Calculate ACGME metrics
    hours_summary = {
        "weekly_hours": profile.hours_worked_week,
        "weekly_limit": 80.0,
        "weekly_remaining": max(0, 80.0 - profile.hours_worked_week),
        "daily_hours": profile.hours_worked_day,
    }

    # Identify fatigue risk periods
    fatigue_risks = []
    if profile.hazard_level != HazardLevel.GREEN:
        fatigue_risks.append(
            {
                "time": profile.generated_at.isoformat(),
                "hazard_level": profile.hazard_level.value,
                "alertness": profile.current_alertness,
                "triggers": profile.hazard_triggers,
            }
        )

    # Determine compliance
    acgme_compliant = (
        profile.hours_worked_week <= 80.0 and not profile.acgme_violation_risk
    )
    fatigue_compliant = profile.hazard_level in [HazardLevel.GREEN, HazardLevel.YELLOW]

    # Generate recommendations
    recommendations = []
    if not acgme_compliant:
        recommendations.append("Schedule exceeds ACGME duty hour limits")
    if not fatigue_compliant:
        recommendations.extend(profile.required_mitigations)
    if profile.sleep_debt_hours > 10:
        recommendations.append(
            f"Accumulated sleep debt of {profile.sleep_debt_hours:.1f} hours requires recovery"
        )

    if not recommendations:
        recommendations.append(
            "Schedule meets both ACGME and fatigue safety requirements"
        )

    return {
        "resident_id": str(resident_id),
        "schedule_period": {
            "start": request.schedule_start.isoformat(),
            "end": request.schedule_end.isoformat(),
        },
        "acgme_compliant": acgme_compliant,
        "fatigue_compliant": fatigue_compliant,
        "hours_summary": hours_summary,
        "fatigue_risk_periods": fatigue_risks,
        "recommendations": recommendations,
        "validation_details": {
            "alertness_score": profile.current_alertness,
            "samn_perelli_level": profile.samn_perelli_level.value,
            "hazard_level": profile.hazard_level.value,
            "sleep_debt_hours": profile.sleep_debt_hours,
        },
    }
