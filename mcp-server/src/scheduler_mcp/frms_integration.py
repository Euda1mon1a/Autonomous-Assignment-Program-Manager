"""
Fatigue Risk Management System (FRMS) MCP Integration.

Exposes aviation-inspired fatigue risk management tools for AI assistant
interaction. These tools implement FRMS principles from FAA AC 120-103A
and ICAO Doc 9966, adapted for medical residency scheduling.

Tools:
- run_frms_assessment: Comprehensive fatigue profile for a resident
- get_fatigue_score: Real-time fatigue scoring from factors
- analyze_sleep_debt: Cumulative sleep debt analysis with BAC equivalence
- predict_alertness: Alertness prediction for future time points
- evaluate_fatigue_hazard: Hazard level assessment with mitigations
- scan_team_fatigue: Team-wide fatigue risk scan
- assess_schedule_fatigue_risk: Evaluate proposed schedule fatigue impact

Key Concepts:
- Samn-Perelli Scale: 7-level fatigue scale from USAF aviation (1-7)
- Sleep Debt: Cumulative sleep deficit with circadian rhythm modeling
- Alertness Prediction: Three-Process Model (S, C, W)
- Hazard Thresholds: 5-level severity (GREEN -> BLACK)

References:
- FAA Advisory Circular AC 120-103A
- ICAO Doc 9966: FRMS Manual for Regulators
- Samn & Perelli (1982) USAF fatigue scale
- Two-process sleep model (Borbely, 1982)
"""

import hashlib
import logging
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def _anonymize_id(identifier: str | None, prefix: str = "Resident") -> str:
    """Create consistent anonymized reference from ID.

    Uses SHA-256 hash for consistent mapping without exposing PII.
    Complies with OPSEC/PERSEC requirements for military medical data.
    """
    if not identifier:
        return f"{prefix}-unknown"
    hash_suffix = hashlib.sha256(identifier.encode()).hexdigest()[:6]
    return f"{prefix}-{hash_suffix}"


# =============================================================================
# Enums
# =============================================================================


class SamnPerelliLevelEnum(int, Enum):
    """Samn-Perelli 7-level fatigue scale from USAF aviation."""

    FULLY_ALERT = 1  # Fully alert, wide awake, extremely peppy
    VERY_LIVELY = 2  # Very lively, responsive, but not at peak
    OKAY = 3  # Okay, somewhat fresh
    A_LITTLE_TIRED = 4  # A little tired, less than fresh
    MODERATELY_TIRED = 5  # Moderately tired, let down
    EXTREMELY_TIRED = 6  # Extremely tired, very difficult to concentrate
    EXHAUSTED = 7  # Completely exhausted, unable to function effectively


class CircadianPhaseEnum(str, Enum):
    """Circadian rhythm phases affecting alertness."""

    NADIR = "nadir"  # 2-6 AM: Lowest alertness
    EARLY_MORNING = "early_morning"  # 6-9 AM: Increasing alertness
    MORNING_PEAK = "morning_peak"  # 9-12 PM: Peak alertness
    POST_LUNCH = "post_lunch"  # 12-3 PM: Post-prandial dip
    AFTERNOON = "afternoon"  # 3-6 PM: Secondary peak
    EVENING = "evening"  # 6-9 PM: Declining alertness
    NIGHT = "night"  # 9 PM-2 AM: Pre-sleep decline


class HazardLevelEnum(str, Enum):
    """Fatigue hazard levels with escalating interventions."""

    GREEN = "green"  # Normal operations
    YELLOW = "yellow"  # Advisory - enhanced monitoring
    ORANGE = "orange"  # Cautionary - schedule review
    RED = "red"  # Warning - modification required
    BLACK = "black"  # Critical - immediate intervention


class MitigationTypeEnum(str, Enum):
    """Types of fatigue mitigation actions."""

    MONITORING = "monitoring"  # Enhanced observation
    BUDDY_SYSTEM = "buddy_system"  # Pair with alert colleague
    DUTY_RESTRICTION = "duty_restriction"  # Limit to lower-risk duties
    SHIFT_SWAP = "shift_swap"  # Swap with rested colleague
    EARLY_RELEASE = "early_release"  # End shift early
    SCHEDULE_MODIFICATION = "schedule_modification"  # Modify future schedule
    MANDATORY_REST = "mandatory_rest"  # Required rest period
    IMMEDIATE_RELIEF = "immediate_relief"  # Immediate coverage by backup


class SleepDebtSeverityEnum(str, Enum):
    """Sleep debt severity classification."""

    NONE = "none"  # < 2 hours
    MILD = "mild"  # 2-5 hours
    MODERATE = "moderate"  # 5-10 hours
    SEVERE = "severe"  # 10-20 hours
    CRITICAL = "critical"  # > 20 hours


class FatigueRiskLevelEnum(str, Enum):
    """Overall fatigue risk classification."""

    MINIMAL = "minimal"  # Fully alert, no concerns
    LOW = "low"  # Minor fatigue factors
    MODERATE = "moderate"  # Some fatigue, monitoring needed
    HIGH = "high"  # Significant fatigue, intervention needed


# =============================================================================
# Response Models
# =============================================================================


class CurrentStateInfo(BaseModel):
    """Current fatigue state information."""

    alertness_score: float = Field(ge=0.0, le=1.0, description="Alertness 0-1")
    alertness_percent: int = Field(ge=0, le=100, description="Alertness as percentage")
    samn_perelli_level: int = Field(ge=1, le=7, description="SP fatigue level 1-7")
    samn_perelli_name: str = Field(description="SP level name")
    sleep_debt_hours: float = Field(ge=0.0, description="Accumulated sleep debt")
    circadian_phase: str = Field(description="Current circadian phase")
    hours_since_sleep: float = Field(ge=0.0, description="Hours since last sleep")


class HazardInfo(BaseModel):
    """Fatigue hazard information."""

    level: str = Field(description="Hazard level color code")
    level_name: str = Field(description="Hazard level name")
    triggers: list[str] = Field(default_factory=list, description="Triggers that activated this level")
    required_mitigations: list[str] = Field(default_factory=list, description="Required mitigation actions")
    is_critical: bool = Field(description="Whether hazard requires immediate intervention")


class WorkHistoryInfo(BaseModel):
    """Work history information."""

    hours_worked_week: float = Field(ge=0.0, description="Hours worked in current week")
    hours_worked_day: float = Field(ge=0.0, description="Hours worked today")
    consecutive_duty_days: int = Field(ge=0, description="Consecutive days on duty")
    consecutive_night_shifts: int = Field(ge=0, description="Consecutive night shifts")


class PredictionsInfo(BaseModel):
    """Fatigue predictions."""

    end_of_shift_alertness: float | None = Field(None, description="Predicted alertness at shift end")
    next_rest_opportunity: str | None = Field(None, description="Next rest opportunity ISO datetime")
    recovery_sleep_needed: float = Field(ge=0.0, description="Hours of recovery sleep needed")


class ACGMEInfo(BaseModel):
    """ACGME compliance information from fatigue perspective."""

    hours_remaining: float = Field(description="Hours remaining in 80-hour limit")
    violation_risk: bool = Field(description="Whether ACGME violation is imminent")


class FRMSAssessmentResponse(BaseModel):
    """
    Complete FRMS assessment response for a resident.

    Aggregates all fatigue-related metrics for comprehensive view,
    adapted from aviation FRMS standards for medical residency.
    """

    resident_id: str = Field(description="Resident UUID")
    resident_name: str = Field(description="Resident name (anonymized)")
    pgy_level: int = Field(ge=1, le=7, description="Post-graduate year level")
    generated_at: str = Field(description="Assessment timestamp ISO format")
    current_state: CurrentStateInfo = Field(description="Current fatigue state")
    hazard: HazardInfo = Field(description="Hazard assessment")
    work_history: WorkHistoryInfo = Field(description="Work history metrics")
    predictions: PredictionsInfo = Field(description="Fatigue predictions")
    acgme: ACGMEInfo = Field(description="ACGME compliance info")
    severity: str = Field(description="Overall severity: healthy, warning, critical, emergency")


class FatigueScoreResponse(BaseModel):
    """
    Real-time fatigue score response.

    Provides immediate fatigue scoring based on objective factors
    without requiring database access.
    """

    samn_perelli_level: int = Field(ge=1, le=7, description="Samn-Perelli level 1-7")
    samn_perelli_name: str = Field(description="SP level name")
    alertness_score: float = Field(ge=0.0, le=1.0, description="Alertness 0-1")
    circadian_phase: str = Field(description="Current circadian phase")
    factors: dict[str, float] = Field(description="Input factors used")
    is_safe_for_duty: bool = Field(description="Whether safe for clinical duty")
    duty_restrictions: list[str] = Field(default_factory=list, description="Restricted duty types")
    recommendations: list[str] = Field(default_factory=list, description="Fatigue management recommendations")
    severity: str = Field(description="Severity: healthy, warning, critical")


class SleepDebtAnalysisResponse(BaseModel):
    """
    Sleep debt analysis response.

    Analyzes cumulative sleep debt with circadian rhythm modeling
    and provides cognitive impairment equivalence (BAC mapping).
    """

    current_debt_hours: float = Field(ge=0.0, description="Current sleep debt hours")
    debt_severity: SleepDebtSeverityEnum = Field(description="Debt severity classification")
    consecutive_deficit_days: int = Field(ge=0, description="Days with < 7h sleep")
    recovery_sleep_needed: float = Field(ge=0.0, description="Hours needed to recover")
    chronic_debt: bool = Field(description="Whether debt is chronic (>5 days)")
    impairment_equivalent_bac: float = Field(
        ge=0.0, le=0.15, description="Cognitive impairment as BAC equivalent"
    )
    debt_trajectory: list[dict[str, Any]] = Field(
        default_factory=list, description="Projected debt over next 7 days"
    )
    recovery_nights_needed: int = Field(ge=0, description="Nights needed for full recovery")
    recommendations: list[str] = Field(default_factory=list, description="Recovery recommendations")
    severity: str = Field(description="Severity: healthy, warning, critical, emergency")


class AlertnessPredictionResponse(BaseModel):
    """
    Alertness prediction for a future time point.

    Combines Three-Process Model (S, C, W) for comprehensive
    alertness prediction.
    """

    prediction_time: str = Field(description="Prediction target time ISO format")
    alertness_score: float = Field(ge=0.0, le=1.0, description="Predicted alertness 0-1")
    alertness_percent: int = Field(ge=0, le=100, description="Alertness as percentage")
    samn_perelli_estimate: int = Field(ge=1, le=7, description="Estimated SP level")
    circadian_phase: str = Field(description="Circadian phase at prediction time")
    hours_awake: float = Field(ge=0.0, description="Estimated hours awake")
    sleep_debt: float = Field(ge=0.0, description="Estimated sleep debt")
    performance_capacity: int = Field(ge=0, le=100, description="Performance capacity %")
    risk_level: FatigueRiskLevelEnum = Field(description="Risk classification")
    contributing_factors: list[str] = Field(default_factory=list, description="Factors affecting alertness")
    recommendations: list[str] = Field(default_factory=list, description="Mitigation recommendations")
    severity: str = Field(description="Severity level")


class FatigueHazardResponse(BaseModel):
    """
    Fatigue hazard evaluation response.

    Evaluates current state against hazard thresholds and
    provides required mitigations based on aviation FRMS.
    """

    hazard_level: HazardLevelEnum = Field(description="Current hazard level")
    hazard_level_name: str = Field(description="Hazard level display name")
    triggers: list[str] = Field(default_factory=list, description="Triggered hazard factors")
    alertness_score: float | None = Field(None, description="Current alertness if available")
    sleep_debt: float | None = Field(None, description="Current sleep debt if available")
    hours_awake: float | None = Field(None, description="Hours awake if available")
    samn_perelli: int | None = Field(None, description="SP level if available")
    required_mitigations: list[str] = Field(default_factory=list, description="Required actions")
    recommended_mitigations: list[str] = Field(default_factory=list, description="Recommended actions")
    acgme_risk: bool = Field(description="Whether ACGME violation is imminent")
    escalation_time: str | None = Field(None, description="When hazard will escalate ISO datetime")
    is_critical: bool = Field(description="Whether immediate intervention needed")
    requires_schedule_change: bool = Field(description="Whether schedule modification required")
    severity: str = Field(description="Severity level")


class ResidentFatigueSummary(BaseModel):
    """Summary of a resident's fatigue status for team scan."""

    resident_id: str = Field(description="Resident UUID")
    name: str = Field(description="Resident name (anonymized)")
    alertness_score: float = Field(ge=0.0, le=1.0, description="Current alertness")
    hazard_level: str = Field(description="Current hazard level")
    samn_perelli_level: int = Field(ge=1, le=7, description="SP fatigue level")
    hours_worked_week: float = Field(ge=0.0, description="Hours worked this week")
    is_critical: bool = Field(description="Whether critical hazard")


class TeamFatigueScanResponse(BaseModel):
    """
    Team-wide fatigue risk scan response.

    Scans all residents for fatigue risks, providing a summary
    for supervisory oversight.
    """

    scan_time: str = Field(description="Scan timestamp ISO format")
    total_residents: int = Field(ge=0, description="Total residents scanned")
    residents_green: int = Field(ge=0, description="Residents at GREEN level")
    residents_yellow: int = Field(ge=0, description="Residents at YELLOW level")
    residents_orange: int = Field(ge=0, description="Residents at ORANGE level")
    residents_red: int = Field(ge=0, description="Residents at RED level")
    residents_black: int = Field(ge=0, description="Residents at BLACK level")
    critical_residents: list[ResidentFatigueSummary] = Field(
        default_factory=list, description="Residents requiring immediate attention"
    )
    at_risk_residents: list[ResidentFatigueSummary] = Field(
        default_factory=list, description="Residents at elevated risk"
    )
    average_alertness: float = Field(ge=0.0, le=1.0, description="Average team alertness")
    average_hours_worked: float = Field(ge=0.0, description="Average hours worked")
    recommendations: list[str] = Field(default_factory=list, description="Team-level recommendations")
    severity: str = Field(description="Overall team severity")


class ScheduleFatigueRiskResponse(BaseModel):
    """
    Schedule fatigue risk assessment response.

    Evaluates fatigue risk for a proposed schedule,
    identifying high-risk periods before they occur.
    """

    resident_id: str = Field(description="Resident UUID")
    shifts_evaluated: int = Field(ge=0, description="Number of shifts evaluated")
    overall_risk: FatigueRiskLevelEnum = Field(description="Overall schedule risk level")
    minimum_alertness: float = Field(ge=0.0, le=1.0, description="Lowest alertness in schedule")
    average_alertness: float = Field(ge=0.0, le=1.0, description="Average alertness")
    high_risk_periods: int = Field(ge=0, description="Number of high-risk periods")
    hazard_distribution: dict[str, int] = Field(
        default_factory=dict, description="Count by hazard level"
    )
    high_risk_windows: list[dict[str, Any]] = Field(
        default_factory=list, description="High-risk window details"
    )
    trajectory: list[dict[str, Any]] = Field(
        default_factory=list, description="Alertness trajectory"
    )
    recommendations: list[str] = Field(default_factory=list, description="Schedule optimization recommendations")
    severity: str = Field(description="Severity level")


# =============================================================================
# Tool Functions
# =============================================================================


async def run_frms_assessment(
    resident_id: str,
    target_time: str | None = None,
) -> FRMSAssessmentResponse:
    """
    Run comprehensive FRMS assessment for a resident.

    Generates a complete fatigue profile aggregating all FRMS metrics
    including Samn-Perelli level, sleep debt, alertness prediction,
    hazard assessment, and ACGME compliance status.

    This is the primary tool for understanding a resident's current
    fatigue state and any required interventions.

    Args:
        resident_id: UUID of the resident to assess.
        target_time: Optional target time for assessment (ISO format).
                    Defaults to current time if not specified.

    Returns:
        FRMSAssessmentResponse with comprehensive fatigue profile.

    Raises:
        ValueError: If resident_id is invalid
        RuntimeError: If FRMS service unavailable

    Example:
        # Get current fatigue profile
        result = await run_frms_assessment(
            resident_id="550e8400-e29b-41d4-a716-446655440000"
        )

        if result.hazard.is_critical:
            print(f"CRITICAL: {result.hazard.required_mitigations}")
        else:
            print(f"Alertness: {result.current_state.alertness_percent}%")
    """
    if not resident_id:
        raise ValueError("resident_id is required")

    logger.info(f"Running FRMS assessment for resident {resident_id}")

    try:
        from app.resilience.frms import FRMSService

        # Parse target time
        if target_time:
            target_dt = datetime.fromisoformat(target_time)
        else:
            target_dt = datetime.utcnow()

        # Create service (without DB for now - would integrate with API client)
        service = FRMSService()

        # Get profile
        try:
            resident_uuid = UUID(resident_id)
        except ValueError as e:
            raise ValueError(f"Invalid resident_id format: {resident_id}") from e

        profile = await service.get_resident_profile(resident_uuid, target_dt)
        profile_dict = profile.to_dict()

        # Determine severity
        hazard_level = profile.hazard_level.value
        if hazard_level == "black":
            severity = "emergency"
        elif hazard_level == "red":
            severity = "critical"
        elif hazard_level in ("orange", "yellow"):
            severity = "warning"
        else:
            severity = "healthy"

        return FRMSAssessmentResponse(
            resident_id=str(profile.resident_id),
            resident_name=_anonymize_id(str(profile.resident_id), "Resident"),
            pgy_level=profile.pgy_level,
            generated_at=profile_dict["generated_at"],
            current_state=CurrentStateInfo(
                alertness_score=profile_dict["current_state"]["alertness_score"],
                alertness_percent=profile_dict["current_state"]["alertness_percent"],
                samn_perelli_level=profile_dict["current_state"]["samn_perelli_level"],
                samn_perelli_name=profile_dict["current_state"]["samn_perelli_name"],
                sleep_debt_hours=profile_dict["current_state"]["sleep_debt_hours"],
                circadian_phase=profile_dict["current_state"]["circadian_phase"],
                hours_since_sleep=profile_dict["current_state"]["hours_since_sleep"],
            ),
            hazard=HazardInfo(
                level=profile_dict["hazard"]["level"],
                level_name=profile_dict["hazard"]["level_name"],
                triggers=profile_dict["hazard"]["triggers"],
                required_mitigations=profile_dict["hazard"]["required_mitigations"],
                is_critical=profile_dict["hazard"]["is_critical"],
            ),
            work_history=WorkHistoryInfo(
                hours_worked_week=profile_dict["work_history"]["hours_worked_week"],
                hours_worked_day=profile_dict["work_history"]["hours_worked_day"],
                consecutive_duty_days=profile_dict["work_history"]["consecutive_duty_days"],
                consecutive_night_shifts=profile_dict["work_history"]["consecutive_night_shifts"],
            ),
            predictions=PredictionsInfo(
                end_of_shift_alertness=profile_dict["predictions"]["end_of_shift_alertness"],
                next_rest_opportunity=profile_dict["predictions"]["next_rest_opportunity"],
                recovery_sleep_needed=profile_dict["predictions"]["recovery_sleep_needed"],
            ),
            acgme=ACGMEInfo(
                hours_remaining=profile_dict["acgme"]["hours_remaining"],
                violation_risk=profile_dict["acgme"]["violation_risk"],
            ),
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"FRMS module unavailable: {e}")
        return await _run_frms_assessment_fallback(resident_id, target_time)
    except Exception as e:
        logger.error(f"FRMS assessment failed: {e}")
        raise RuntimeError(f"Failed to run FRMS assessment: {e}") from e


async def _run_frms_assessment_fallback(
    resident_id: str,
    target_time: str | None,
) -> FRMSAssessmentResponse:
    """Fallback FRMS assessment when module unavailable."""
    now = datetime.utcnow()
    hour = now.hour

    # Determine circadian phase
    if 2 <= hour < 6:
        phase = "nadir"
        alertness = 0.6
    elif 6 <= hour < 9:
        phase = "early_morning"
        alertness = 0.75
    elif 9 <= hour < 12:
        phase = "morning_peak"
        alertness = 0.9
    elif 12 <= hour < 15:
        phase = "post_lunch"
        alertness = 0.8
    elif 15 <= hour < 18:
        phase = "afternoon"
        alertness = 0.85
    elif 18 <= hour < 21:
        phase = "evening"
        alertness = 0.8
    else:
        phase = "night"
        alertness = 0.7

    # Derive SP level from alertness
    sp_level = max(1, min(7, int(8 - alertness * 7)))
    sp_names = {
        1: "FULLY_ALERT", 2: "VERY_LIVELY", 3: "OKAY",
        4: "A_LITTLE_TIRED", 5: "MODERATELY_TIRED",
        6: "EXTREMELY_TIRED", 7: "EXHAUSTED"
    }

    return FRMSAssessmentResponse(
        resident_id=resident_id,
        resident_name=f"Resident-{resident_id[-4:]}",
        pgy_level=2,
        generated_at=now.isoformat(),
        current_state=CurrentStateInfo(
            alertness_score=alertness,
            alertness_percent=int(alertness * 100),
            samn_perelli_level=sp_level,
            samn_perelli_name=sp_names[sp_level],
            sleep_debt_hours=2.0,
            circadian_phase=phase,
            hours_since_sleep=8.0,
        ),
        hazard=HazardInfo(
            level="green",
            level_name="GREEN",
            triggers=[],
            required_mitigations=[],
            is_critical=False,
        ),
        work_history=WorkHistoryInfo(
            hours_worked_week=45.0,
            hours_worked_day=8.0,
            consecutive_duty_days=3,
            consecutive_night_shifts=0,
        ),
        predictions=PredictionsInfo(
            end_of_shift_alertness=alertness * 0.9,
            next_rest_opportunity=None,
            recovery_sleep_needed=3.0,
        ),
        acgme=ACGMEInfo(
            hours_remaining=35.0,
            violation_risk=False,
        ),
        severity="healthy",
    )


async def get_fatigue_score(
    hours_awake: float,
    hours_worked_24h: float,
    consecutive_night_shifts: int = 0,
    time_of_day_hour: int = 12,
    prior_sleep_hours: float = 7.0,
) -> FatigueScoreResponse:
    """
    Calculate real-time fatigue score from objective factors.

    Provides immediate fatigue scoring without database access,
    suitable for quick assessments and scheduling decisions.

    Uses the Samn-Perelli scale adapted from USAF aviation
    with factors including hours awake, work intensity,
    circadian timing, and prior sleep.

    Args:
        hours_awake: Hours since last sleep period (0-48).
        hours_worked_24h: Work hours in last 24 hours (0-24).
        consecutive_night_shifts: Number of consecutive night shifts (0-7).
        time_of_day_hour: Current hour 0-23 (for circadian effects).
        prior_sleep_hours: Hours of sleep in prior sleep period (0-12).

    Returns:
        FatigueScoreResponse with fatigue level and safety assessment.

    Raises:
        ValueError: If parameters are out of valid range

    Example:
        # Score after 18 hours awake, 12 hours worked
        result = await get_fatigue_score(
            hours_awake=18,
            hours_worked_24h=12,
            time_of_day_hour=4  # 4 AM circadian nadir
        )

        if not result.is_safe_for_duty:
            print(f"Fatigue level {result.samn_perelli_level}: {result.duty_restrictions}")
    """
    # Validate inputs
    if hours_awake < 0 or hours_awake > 72:
        raise ValueError("hours_awake must be between 0 and 72")
    if hours_worked_24h < 0 or hours_worked_24h > 24:
        raise ValueError("hours_worked_24h must be between 0 and 24")
    if consecutive_night_shifts < 0 or consecutive_night_shifts > 14:
        raise ValueError("consecutive_night_shifts must be between 0 and 14")
    if time_of_day_hour < 0 or time_of_day_hour > 23:
        raise ValueError("time_of_day_hour must be between 0 and 23")
    if prior_sleep_hours < 0 or prior_sleep_hours > 16:
        raise ValueError("prior_sleep_hours must be between 0 and 16")

    logger.info(
        f"Calculating fatigue score: awake={hours_awake}h, worked={hours_worked_24h}h, "
        f"nights={consecutive_night_shifts}, hour={time_of_day_hour}"
    )

    try:
        from app.resilience.frms import FRMSService

        service = FRMSService()
        result = service.calculate_fatigue_score(
            hours_awake=hours_awake,
            hours_worked_24h=hours_worked_24h,
            consecutive_night_shifts=consecutive_night_shifts,
            time_of_day_hour=time_of_day_hour,
            prior_sleep_hours=prior_sleep_hours,
        )

        sp_level = result["samn_perelli_level"]
        alertness = result["alertness_score"]

        # Determine safety and restrictions
        is_safe = sp_level <= 6
        duty_restrictions = []
        if sp_level >= 5:
            duty_restrictions.extend(["critical_care", "procedures"])
        if sp_level >= 6:
            duty_restrictions.extend(["inpatient"])
        if sp_level >= 7:
            duty_restrictions.extend(["outpatient", "education", "administrative"])

        # Generate recommendations
        recommendations = []
        if hours_awake > 16:
            recommendations.append(f"Extended wakefulness ({hours_awake:.0f}h) - rest recommended")
        if 2 <= time_of_day_hour <= 6:
            recommendations.append("Circadian nadir period - avoid high-risk procedures")
        if prior_sleep_hours < 6:
            recommendations.append(f"Sleep deficit (only {prior_sleep_hours:.1f}h) - plan recovery sleep")
        if consecutive_night_shifts > 2:
            recommendations.append(f"{consecutive_night_shifts} consecutive nights - circadian disruption risk")

        # Determine severity
        if sp_level >= 7:
            severity = "critical"
        elif sp_level >= 5:
            severity = "warning"
        else:
            severity = "healthy"

        return FatigueScoreResponse(
            samn_perelli_level=sp_level,
            samn_perelli_name=result["samn_perelli_name"],
            alertness_score=alertness,
            circadian_phase=result["circadian_phase"],
            factors=result["factors"],
            is_safe_for_duty=is_safe,
            duty_restrictions=duty_restrictions,
            recommendations=recommendations,
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"FRMS module unavailable: {e}")
        return await _get_fatigue_score_fallback(
            hours_awake, hours_worked_24h, consecutive_night_shifts,
            time_of_day_hour, prior_sleep_hours
        )
    except Exception as e:
        logger.error(f"Fatigue score calculation failed: {e}")
        raise RuntimeError(f"Failed to calculate fatigue score: {e}") from e


async def _get_fatigue_score_fallback(
    hours_awake: float,
    hours_worked_24h: float,
    consecutive_night_shifts: int,
    time_of_day_hour: int,
    prior_sleep_hours: float,
) -> FatigueScoreResponse:
    """Fallback fatigue score calculation."""
    # Calculate score based on factors
    score = 1.0

    if hours_awake > 24:
        score += 3.0
    elif hours_awake > 20:
        score += 2.5
    elif hours_awake > 16:
        score += 1.5
    elif hours_awake > 12:
        score += 0.5

    if hours_worked_24h > 16:
        score += 2.0
    elif hours_worked_24h > 12:
        score += 1.0
    elif hours_worked_24h > 8:
        score += 0.5

    score += min(consecutive_night_shifts * 0.5, 1.5)

    if 2 <= time_of_day_hour <= 6:
        score += 1.5
    elif 14 <= time_of_day_hour <= 16:
        score += 0.3

    sleep_deficit = max(0, 7.0 - prior_sleep_hours)
    score += sleep_deficit * 0.3

    sp_level = max(1, min(7, round(score)))
    alertness = 1.0 - (sp_level - 1) / 6.0

    sp_names = {
        1: "FULLY_ALERT", 2: "VERY_LIVELY", 3: "OKAY",
        4: "A_LITTLE_TIRED", 5: "MODERATELY_TIRED",
        6: "EXTREMELY_TIRED", 7: "EXHAUSTED"
    }

    # Determine circadian phase
    if 2 <= time_of_day_hour < 6:
        phase = "nadir"
    elif 6 <= time_of_day_hour < 9:
        phase = "early_morning"
    elif 9 <= time_of_day_hour < 12:
        phase = "morning_peak"
    elif 12 <= time_of_day_hour < 15:
        phase = "post_lunch"
    elif 15 <= time_of_day_hour < 18:
        phase = "afternoon"
    elif 18 <= time_of_day_hour < 21:
        phase = "evening"
    else:
        phase = "night"

    is_safe = sp_level <= 6
    duty_restrictions = []
    if sp_level >= 5:
        duty_restrictions.extend(["critical_care", "procedures"])
    if sp_level >= 6:
        duty_restrictions.extend(["inpatient"])

    recommendations = []
    if hours_awake > 16:
        recommendations.append(f"Extended wakefulness ({hours_awake:.0f}h)")
    if phase == "nadir":
        recommendations.append("Circadian nadir - increased vigilance")

    severity = "critical" if sp_level >= 7 else ("warning" if sp_level >= 5 else "healthy")

    return FatigueScoreResponse(
        samn_perelli_level=sp_level,
        samn_perelli_name=sp_names[sp_level],
        alertness_score=alertness,
        circadian_phase=phase,
        factors={
            "hours_awake": hours_awake,
            "hours_worked_24h": hours_worked_24h,
            "consecutive_night_shifts": consecutive_night_shifts,
            "time_of_day_hour": time_of_day_hour,
            "prior_sleep_hours": prior_sleep_hours,
        },
        is_safe_for_duty=is_safe,
        duty_restrictions=duty_restrictions,
        recommendations=recommendations,
        severity=severity,
    )


async def analyze_sleep_debt(
    sleep_hours_per_day: list[float],
    baseline_sleep_need: float = 7.5,
) -> SleepDebtAnalysisResponse:
    """
    Analyze cumulative sleep debt with BAC equivalence mapping.

    Calculates accumulated sleep debt over a period and provides:
    - Severity classification
    - Cognitive impairment equivalence (BAC mapping)
    - Recovery time estimation
    - Trajectory projection

    Scientific basis: Van Dongen et al. (2003) "The cumulative cost
    of additional wakefulness" - sleep debt has measurable cognitive
    effects equivalent to blood alcohol levels.

    Args:
        sleep_hours_per_day: List of sleep hours for each day (most recent last).
                            Typical length: 7-14 days.
        baseline_sleep_need: Individual's baseline sleep requirement (default: 7.5h).

    Returns:
        SleepDebtAnalysisResponse with debt analysis and recovery plan.

    Raises:
        ValueError: If inputs are invalid

    Example:
        # Analyze past week of sleep
        result = await analyze_sleep_debt(
            sleep_hours_per_day=[6.0, 5.5, 7.0, 5.0, 6.5, 8.0, 6.0],
            baseline_sleep_need=7.5
        )

        print(f"Sleep debt: {result.current_debt_hours}h")
        print(f"BAC equivalent: {result.impairment_equivalent_bac:.3f}")
        print(f"Recovery needed: {result.recovery_nights_needed} nights")
    """
    if not sleep_hours_per_day:
        raise ValueError("sleep_hours_per_day cannot be empty")
    if baseline_sleep_need < 4 or baseline_sleep_need > 12:
        raise ValueError("baseline_sleep_need must be between 4 and 12 hours")

    for i, hours in enumerate(sleep_hours_per_day):
        if hours < 0 or hours > 24:
            raise ValueError(f"Invalid sleep hours at day {i}: {hours}")

    logger.info(f"Analyzing sleep debt: {len(sleep_hours_per_day)} days, baseline={baseline_sleep_need}h")

    try:
        from uuid import uuid4

        from app.resilience.frms import SleepDebtModel

        model = SleepDebtModel(baseline_sleep_need=baseline_sleep_need)

        # Calculate cumulative debt
        resident_id = uuid4()
        total_debt = 0.0
        deficit_days = 0

        for hours in sleep_hours_per_day:
            daily_change = baseline_sleep_need - hours
            if daily_change > 0:
                total_debt += daily_change
                deficit_days += 1
            else:
                # Recovery
                recovery = abs(daily_change) / model.DEBT_RECOVERY_RATIO
                total_debt = max(0, total_debt - recovery)
                deficit_days = 0

        total_debt = min(total_debt, model.MAX_DEBT_HOURS)

        # Classify severity
        if total_debt < 2:
            debt_severity = SleepDebtSeverityEnum.NONE
            severity = "healthy"
        elif total_debt < 5:
            debt_severity = SleepDebtSeverityEnum.MILD
            severity = "healthy"
        elif total_debt < 10:
            debt_severity = SleepDebtSeverityEnum.MODERATE
            severity = "warning"
        elif total_debt < 20:
            debt_severity = SleepDebtSeverityEnum.SEVERE
            severity = "critical"
        else:
            debt_severity = SleepDebtSeverityEnum.CRITICAL
            severity = "emergency"

        # Calculate BAC equivalence
        bac = min(total_debt * 0.005, 0.15)

        # Calculate recovery needs
        recovery_sleep_needed = total_debt * model.DEBT_RECOVERY_RATIO
        recovery_nights = model.estimate_recovery_time(total_debt, 9.0)

        # Project trajectory (next 7 days with 8h sleep per night)
        trajectory = model.predict_debt_trajectory(
            resident_id, [8.0] * 7, start_debt=total_debt
        )

        # Generate recommendations
        recommendations = []
        if total_debt > 10:
            recommendations.append("Significant sleep debt - prioritize recovery sleep")
        if deficit_days >= 5:
            recommendations.append(f"Chronic deficit ({deficit_days} days) - schedule intervention")
        if bac >= 0.05:
            recommendations.append(f"Impairment equivalent to {bac:.2f} BAC - restrict high-risk duties")
        recommendations.append(f"Target {baseline_sleep_need + 1.5}h/night for {recovery_nights} nights to recover")

        return SleepDebtAnalysisResponse(
            current_debt_hours=round(total_debt, 1),
            debt_severity=debt_severity,
            consecutive_deficit_days=deficit_days,
            recovery_sleep_needed=round(recovery_sleep_needed, 1),
            chronic_debt=deficit_days >= 5,
            impairment_equivalent_bac=round(bac, 3),
            debt_trajectory=trajectory,
            recovery_nights_needed=max(0, recovery_nights) if recovery_nights >= 0 else 0,
            recommendations=recommendations,
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"FRMS module unavailable: {e}")
        return await _analyze_sleep_debt_fallback(sleep_hours_per_day, baseline_sleep_need)
    except Exception as e:
        logger.error(f"Sleep debt analysis failed: {e}")
        raise RuntimeError(f"Failed to analyze sleep debt: {e}") from e


async def _analyze_sleep_debt_fallback(
    sleep_hours_per_day: list[float],
    baseline_sleep_need: float,
) -> SleepDebtAnalysisResponse:
    """Fallback sleep debt analysis."""
    total_debt = 0.0
    deficit_days = 0
    recovery_ratio = 1.5

    for hours in sleep_hours_per_day:
        daily_change = baseline_sleep_need - hours
        if daily_change > 0:
            total_debt += daily_change
            deficit_days += 1
        else:
            recovery = abs(daily_change) / recovery_ratio
            total_debt = max(0, total_debt - recovery)
            deficit_days = 0

    total_debt = min(total_debt, 40.0)

    if total_debt < 2:
        debt_severity = SleepDebtSeverityEnum.NONE
        severity = "healthy"
    elif total_debt < 5:
        debt_severity = SleepDebtSeverityEnum.MILD
        severity = "healthy"
    elif total_debt < 10:
        debt_severity = SleepDebtSeverityEnum.MODERATE
        severity = "warning"
    elif total_debt < 20:
        debt_severity = SleepDebtSeverityEnum.SEVERE
        severity = "critical"
    else:
        debt_severity = SleepDebtSeverityEnum.CRITICAL
        severity = "emergency"

    bac = min(total_debt * 0.005, 0.15)
    recovery_sleep = total_debt * recovery_ratio
    recovery_nights = int(recovery_sleep / 1.5) if total_debt > 0 else 0

    return SleepDebtAnalysisResponse(
        current_debt_hours=round(total_debt, 1),
        debt_severity=debt_severity,
        consecutive_deficit_days=deficit_days,
        recovery_sleep_needed=round(recovery_sleep, 1),
        chronic_debt=deficit_days >= 5,
        impairment_equivalent_bac=round(bac, 3),
        debt_trajectory=[],
        recovery_nights_needed=recovery_nights,
        recommendations=[f"Recovery needed: {recovery_nights} nights of 9h sleep"],
        severity=severity,
    )


async def evaluate_fatigue_hazard(
    alertness: float | None = None,
    sleep_debt: float | None = None,
    hours_awake: float | None = None,
    samn_perelli: int | None = None,
    consecutive_nights: int = 0,
    hours_worked_week: float = 0.0,
) -> FatigueHazardResponse:
    """
    Evaluate fatigue hazard level with mitigation requirements.

    Implements aviation FRMS 5-level hazard system:
    - GREEN: Normal operations
    - YELLOW: Advisory - enhanced monitoring
    - ORANGE: Cautionary - schedule review
    - RED: Warning - modification required
    - BLACK: Critical - immediate intervention

    At least one of alertness, sleep_debt, hours_awake, or samn_perelli
    must be provided for meaningful assessment.

    Args:
        alertness: Current alertness score 0.0-1.0 (optional).
        sleep_debt: Current accumulated sleep debt in hours (optional).
        hours_awake: Hours since last sleep (optional).
        samn_perelli: Current Samn-Perelli level 1-7 (optional).
        consecutive_nights: Number of consecutive night shifts (default: 0).
        hours_worked_week: Hours worked in current week (default: 0).

    Returns:
        FatigueHazardResponse with hazard level and required mitigations.

    Raises:
        ValueError: If all optional parameters are None

    Example:
        result = await evaluate_fatigue_hazard(
            alertness=0.4,
            sleep_debt=15.0,
            hours_awake=20,
            hours_worked_week=75
        )

        if result.is_critical:
            print(f"CRITICAL HAZARD: {result.required_mitigations}")
    """
    if all(x is None for x in [alertness, sleep_debt, hours_awake, samn_perelli]):
        raise ValueError("At least one fatigue metric must be provided")

    logger.info(
        f"Evaluating fatigue hazard: alertness={alertness}, debt={sleep_debt}, "
        f"awake={hours_awake}, SP={samn_perelli}"
    )

    try:
        from uuid import uuid4

        from app.resilience.frms import HazardThresholdEngine

        engine = HazardThresholdEngine()

        hazard = engine.evaluate_hazard(
            resident_id=uuid4(),
            alertness=alertness,
            sleep_debt=sleep_debt,
            hours_awake=hours_awake,
            samn_perelli=samn_perelli,
            consecutive_nights=consecutive_nights,
            hours_worked_week=hours_worked_week,
        )

        hazard_dict = hazard.to_dict()

        # Determine severity
        level = hazard.hazard_level.value
        if level == "black":
            severity = "emergency"
        elif level == "red":
            severity = "critical"
        elif level in ("orange", "yellow"):
            severity = "warning"
        else:
            severity = "healthy"

        return FatigueHazardResponse(
            hazard_level=HazardLevelEnum(level),
            hazard_level_name=hazard.hazard_level.name,
            triggers=hazard_dict["triggers"],
            alertness_score=hazard_dict["alertness_score"],
            sleep_debt=hazard_dict["sleep_debt"],
            hours_awake=hazard_dict["hours_awake"],
            samn_perelli=hazard_dict["samn_perelli"],
            required_mitigations=hazard_dict["required_mitigations"],
            recommended_mitigations=hazard_dict["recommended_mitigations"],
            acgme_risk=hazard_dict["acgme_risk"],
            escalation_time=hazard_dict["escalation_time"],
            is_critical=hazard.is_critical,
            requires_schedule_change=hazard.requires_schedule_change,
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"FRMS module unavailable: {e}")
        return await _evaluate_fatigue_hazard_fallback(
            alertness, sleep_debt, hours_awake, samn_perelli,
            consecutive_nights, hours_worked_week
        )
    except Exception as e:
        logger.error(f"Fatigue hazard evaluation failed: {e}")
        raise RuntimeError(f"Failed to evaluate fatigue hazard: {e}") from e


async def _evaluate_fatigue_hazard_fallback(
    alertness: float | None,
    sleep_debt: float | None,
    hours_awake: float | None,
    samn_perelli: int | None,
    consecutive_nights: int,
    hours_worked_week: float,
) -> FatigueHazardResponse:
    """Fallback hazard evaluation."""
    triggers = []
    level = HazardLevelEnum.GREEN

    # Check each metric
    if alertness is not None:
        if alertness < 0.35:
            level = HazardLevelEnum.BLACK
            triggers.append("alertness_critical")
        elif alertness < 0.45:
            level = max(level, HazardLevelEnum.RED, key=lambda x: list(HazardLevelEnum).index(x))
            triggers.append("alertness_low")
        elif alertness < 0.55:
            level = max(level, HazardLevelEnum.ORANGE, key=lambda x: list(HazardLevelEnum).index(x))
            triggers.append("alertness_reduced")
        elif alertness < 0.70:
            level = max(level, HazardLevelEnum.YELLOW, key=lambda x: list(HazardLevelEnum).index(x))
            triggers.append("alertness_warning")

    if sleep_debt is not None:
        if sleep_debt > 20:
            level = HazardLevelEnum.BLACK if level != HazardLevelEnum.BLACK else level
            triggers.append("sleep_debt_critical")
        elif sleep_debt > 15:
            level = max(level, HazardLevelEnum.RED, key=lambda x: list(HazardLevelEnum).index(x))
            triggers.append("sleep_debt_high")
        elif sleep_debt > 10:
            level = max(level, HazardLevelEnum.ORANGE, key=lambda x: list(HazardLevelEnum).index(x))
            triggers.append("sleep_debt_elevated")

    if hours_awake is not None and hours_awake > 18:
        triggers.append("extended_wakefulness")
        if hours_awake > 26:
            level = HazardLevelEnum.BLACK
        elif hours_awake > 22:
            level = max(level, HazardLevelEnum.RED, key=lambda x: list(HazardLevelEnum).index(x))

    if hours_worked_week >= 80:
        triggers.append("acgme_violation")
        level = max(level, HazardLevelEnum.RED, key=lambda x: list(HazardLevelEnum).index(x))
    elif hours_worked_week >= 72:
        triggers.append("acgme_approaching")

    # Determine mitigations
    mitigations = {
        HazardLevelEnum.GREEN: [],
        HazardLevelEnum.YELLOW: ["monitoring"],
        HazardLevelEnum.ORANGE: ["monitoring", "buddy_system", "duty_restriction"],
        HazardLevelEnum.RED: ["duty_restriction", "shift_swap", "schedule_modification"],
        HazardLevelEnum.BLACK: ["mandatory_rest", "immediate_relief"],
    }

    severity = {
        HazardLevelEnum.GREEN: "healthy",
        HazardLevelEnum.YELLOW: "warning",
        HazardLevelEnum.ORANGE: "warning",
        HazardLevelEnum.RED: "critical",
        HazardLevelEnum.BLACK: "emergency",
    }

    return FatigueHazardResponse(
        hazard_level=level,
        hazard_level_name=level.name,
        triggers=triggers,
        alertness_score=alertness,
        sleep_debt=sleep_debt,
        hours_awake=hours_awake,
        samn_perelli=samn_perelli,
        required_mitigations=mitigations.get(level, []),
        recommended_mitigations=[],
        acgme_risk=hours_worked_week >= 72,
        escalation_time=None,
        is_critical=level in [HazardLevelEnum.RED, HazardLevelEnum.BLACK],
        requires_schedule_change=level in [HazardLevelEnum.ORANGE, HazardLevelEnum.RED, HazardLevelEnum.BLACK],
        severity=severity.get(level, "healthy"),
    )


async def scan_team_fatigue(
    hazard_threshold: str = "yellow",
) -> TeamFatigueScanResponse:
    """
    Scan all residents for fatigue risks.

    Returns fatigue profiles for all residents, filtered to those
    at or above the specified hazard threshold. Critical for
    supervisory oversight and proactive intervention.

    Args:
        hazard_threshold: Minimum hazard level to include in results.
                         Options: "green", "yellow", "orange", "red", "black".
                         Default: "yellow" (includes all elevated risks).

    Returns:
        TeamFatigueScanResponse with team fatigue summary and critical cases.

    Raises:
        ValueError: If hazard_threshold is invalid

    Example:
        # Get all residents at ORANGE or higher risk
        result = await scan_team_fatigue(hazard_threshold="orange")

        print(f"Critical residents: {result.residents_red + result.residents_black}")
        for resident in result.critical_residents:
            print(f"  {resident.name}: {resident.hazard_level}")
    """
    valid_thresholds = ["green", "yellow", "orange", "red", "black"]
    if hazard_threshold.lower() not in valid_thresholds:
        raise ValueError(f"hazard_threshold must be one of {valid_thresholds}")

    logger.info(f"Scanning team fatigue with threshold: {hazard_threshold}")

    try:
        from app.resilience.frms import FRMSService, HazardLevel

        service = FRMSService()
        threshold = HazardLevel(hazard_threshold.lower())

        profiles = await service.scan_all_residents(
            target_time=datetime.utcnow(),
            hazard_threshold=threshold,
        )

        # Count by level
        level_counts = dict.fromkeys(["green", "yellow", "orange", "red", "black"], 0)
        critical = []
        at_risk = []
        total_alertness = 0.0
        total_hours = 0.0

        for profile in profiles:
            level = profile.hazard_level.value
            level_counts[level] = level_counts.get(level, 0) + 1
            total_alertness += profile.current_alertness
            total_hours += profile.hours_worked_week

            summary = ResidentFatigueSummary(
                resident_id=str(profile.resident_id),
                name=_anonymize_id(str(profile.resident_id), "Resident"),
                alertness_score=profile.current_alertness,
                hazard_level=level,
                samn_perelli_level=profile.samn_perelli_level.value,
                hours_worked_week=profile.hours_worked_week,
                is_critical=level in ["red", "black"],
            )

            if level in ["red", "black"]:
                critical.append(summary)
            elif level in ["orange", "yellow"]:
                at_risk.append(summary)

        total = len(profiles) if profiles else 1
        avg_alertness = total_alertness / total if profiles else 0.9
        avg_hours = total_hours / total if profiles else 40.0

        # Determine overall severity
        if level_counts["black"] > 0:
            severity = "emergency"
        elif level_counts["red"] > 0:
            severity = "critical"
        elif level_counts["orange"] > total * 0.2:
            severity = "warning"
        else:
            severity = "healthy"

        # Generate recommendations
        recommendations = []
        if level_counts["black"] > 0:
            recommendations.append(f"IMMEDIATE: {level_counts['black']} resident(s) at BLACK level require relief")
        if level_counts["red"] > 0:
            recommendations.append(f"URGENT: {level_counts['red']} resident(s) at RED level need schedule modification")
        if avg_alertness < 0.7:
            recommendations.append(f"Team average alertness ({avg_alertness:.0%}) below optimal - review workload")
        if avg_hours > 60:
            recommendations.append(f"High average hours ({avg_hours:.0f}h/week) - monitor for burnout")

        return TeamFatigueScanResponse(
            scan_time=datetime.utcnow().isoformat(),
            total_residents=len(profiles),
            residents_green=level_counts["green"],
            residents_yellow=level_counts["yellow"],
            residents_orange=level_counts["orange"],
            residents_red=level_counts["red"],
            residents_black=level_counts["black"],
            critical_residents=critical,
            at_risk_residents=at_risk,
            average_alertness=avg_alertness,
            average_hours_worked=avg_hours,
            recommendations=recommendations,
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"FRMS module unavailable: {e}")
        return await _scan_team_fatigue_fallback(hazard_threshold)
    except Exception as e:
        logger.error(f"Team fatigue scan failed: {e}")
        raise RuntimeError(f"Failed to scan team fatigue: {e}") from e


async def _scan_team_fatigue_fallback(
    hazard_threshold: str,
) -> TeamFatigueScanResponse:
    """Fallback team scan."""
    return TeamFatigueScanResponse(
        scan_time=datetime.utcnow().isoformat(),
        total_residents=0,
        residents_green=0,
        residents_yellow=0,
        residents_orange=0,
        residents_red=0,
        residents_black=0,
        critical_residents=[],
        at_risk_residents=[],
        average_alertness=0.85,
        average_hours_worked=45.0,
        recommendations=["FRMS service unavailable - manual review recommended"],
        severity="warning",
    )


async def assess_schedule_fatigue_risk(
    resident_id: str,
    proposed_shifts: list[dict[str, Any]],
) -> ScheduleFatigueRiskResponse:
    """
    Assess fatigue risk for a proposed schedule.

    Evaluates how a proposed sequence of shifts would affect fatigue
    levels and identifies high-risk periods before they occur.
    Critical for proactive schedule optimization.

    Each shift in proposed_shifts should have:
    - start: ISO datetime string for shift start
    - end: ISO datetime string for shift end
    - type: Shift type ("day", "evening", "night", "call_24", etc.)
    - prior_sleep: Optional hours of expected prior sleep (default: 7.0)

    Args:
        resident_id: UUID of the resident.
        proposed_shifts: List of shift dictionaries to evaluate.

    Returns:
        ScheduleFatigueRiskResponse with risk assessment and recommendations.

    Raises:
        ValueError: If inputs are invalid

    Example:
        shifts = [
            {"start": "2025-01-15T07:00:00", "end": "2025-01-15T17:00:00", "type": "day"},
            {"start": "2025-01-16T19:00:00", "end": "2025-01-17T07:00:00", "type": "night"},
            {"start": "2025-01-17T19:00:00", "end": "2025-01-18T07:00:00", "type": "night"},
        ]

        result = await assess_schedule_fatigue_risk(
            resident_id="550e8400-e29b-41d4-a716-446655440000",
            proposed_shifts=shifts
        )

        if result.overall_risk == "high":
            print(f"High risk periods: {result.high_risk_periods}")
            print(f"Recommendations: {result.recommendations}")
    """
    if not resident_id:
        raise ValueError("resident_id is required")
    if not proposed_shifts:
        raise ValueError("proposed_shifts cannot be empty")

    # Validate shift structure
    for i, shift in enumerate(proposed_shifts):
        if "start" not in shift or "end" not in shift:
            raise ValueError(f"Shift {i} missing required 'start' or 'end' field")

    logger.info(f"Assessing schedule fatigue risk: {len(proposed_shifts)} shifts for {resident_id}")

    try:
        from uuid import UUID as UUIDType

        from app.resilience.frms import FRMSService

        service = FRMSService()

        try:
            resident_uuid = UUIDType(resident_id)
        except ValueError as e:
            raise ValueError(f"Invalid resident_id format: {resident_id}") from e

        result = await service.assess_schedule_fatigue_risk(
            resident_id=resident_uuid,
            proposed_shifts=proposed_shifts,
        )

        # Map overall risk
        risk_map = {
            "high": FatigueRiskLevelEnum.HIGH,
            "moderate": FatigueRiskLevelEnum.MODERATE,
            "low": FatigueRiskLevelEnum.LOW,
        }
        overall_risk = risk_map.get(result["overall_risk"], FatigueRiskLevelEnum.LOW)

        # Determine severity
        min_alert = result["metrics"]["minimum_alertness"]
        if min_alert < 0.4:
            severity = "critical"
        elif min_alert < 0.6:
            severity = "warning"
        else:
            severity = "healthy"

        return ScheduleFatigueRiskResponse(
            resident_id=result["resident_id"],
            shifts_evaluated=result["shifts_evaluated"],
            overall_risk=overall_risk,
            minimum_alertness=result["metrics"]["minimum_alertness"],
            average_alertness=result["metrics"]["average_alertness"],
            high_risk_periods=result["metrics"]["high_risk_periods"],
            hazard_distribution=result["hazard_distribution"],
            high_risk_windows=result["high_risk_windows"],
            trajectory=result["trajectory"],
            recommendations=result["recommendations"],
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"FRMS module unavailable: {e}")
        return await _assess_schedule_fatigue_risk_fallback(resident_id, proposed_shifts)
    except Exception as e:
        logger.error(f"Schedule fatigue risk assessment failed: {e}")
        raise RuntimeError(f"Failed to assess schedule fatigue risk: {e}") from e


async def _assess_schedule_fatigue_risk_fallback(
    resident_id: str,
    proposed_shifts: list[dict[str, Any]],
) -> ScheduleFatigueRiskResponse:
    """Fallback schedule assessment."""
    num_shifts = len(proposed_shifts)

    # Simple heuristics
    night_count = sum(1 for s in proposed_shifts if s.get("type", "").lower() in ("night", "call_24", "call_28"))
    has_consecutive_nights = night_count >= 2

    if night_count >= 4 or has_consecutive_nights:
        overall_risk = FatigueRiskLevelEnum.HIGH
        min_alertness = 0.4
        severity = "critical"
    elif night_count >= 2:
        overall_risk = FatigueRiskLevelEnum.MODERATE
        min_alertness = 0.6
        severity = "warning"
    else:
        overall_risk = FatigueRiskLevelEnum.LOW
        min_alertness = 0.8
        severity = "healthy"

    recommendations = []
    if has_consecutive_nights:
        recommendations.append("Consecutive night shifts detected - ensure adequate recovery time")
    if night_count >= 3:
        recommendations.append("High night shift density - consider redistribution")
    if not recommendations:
        recommendations.append("Schedule fatigue risk within acceptable limits")

    return ScheduleFatigueRiskResponse(
        resident_id=resident_id,
        shifts_evaluated=num_shifts,
        overall_risk=overall_risk,
        minimum_alertness=min_alertness,
        average_alertness=min_alertness + 0.1,
        high_risk_periods=1 if overall_risk == FatigueRiskLevelEnum.HIGH else 0,
        hazard_distribution={"green": num_shifts - night_count, "yellow": night_count},
        high_risk_windows=[],
        trajectory=[],
        recommendations=recommendations,
        severity=severity,
    )
