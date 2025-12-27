"""
Fatigue Risk Management System (FRMS) Service.

The main service integrating all FRMS components for medical residency
scheduling. Provides a unified API for fatigue risk assessment,
prediction, and schedule optimization.

Service Responsibilities:
1. Real-time fatigue scoring for residents
2. Predictive alertness modeling for scheduling
3. Hazard detection and intervention triggering
4. ACGME compliance validation through fatigue lens
5. Dashboard data generation
6. Temporal constraint export for holographic hub

Integration Points:
- Scheduling Engine: Provides fatigue constraints for optimization
- Resilience Framework: Integrates with existing health monitoring
- ACGME Validator: Adds fatigue-based compliance checking
- API Routes: Exposes FRMS data to frontend

References:
- FAA AC 120-103A: FRMS for Aviation Safety
- ICAO Doc 9966: FRMS Manual for Regulators
- ACGME Common Program Requirements (Duty Hours)
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.logging import get_logger
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.resilience.frms.samn_perelli import (
    SamnPerelliLevel,
    SamnPerelliAssessment,
    assess_fatigue_level,
    estimate_level_from_factors,
    DUTY_THRESHOLDS,
)
from app.resilience.frms.sleep_debt import (
    SleepDebtModel,
    SleepDebtState,
    SleepOpportunity,
    CircadianPhase,
)
from app.resilience.frms.alertness_engine import (
    AlertnessPredictor,
    AlertnessPrediction,
    ShiftPattern,
    ShiftType,
)
from app.resilience.frms.hazard_thresholds import (
    HazardLevel,
    FatigueHazard,
    HazardThresholdEngine,
    TriggerType,
)

logger = get_logger(__name__)


@dataclass
class FatigueProfile:
    """
    Complete fatigue profile for a resident.

    Aggregates all fatigue-related data for comprehensive view.
    """

    resident_id: UUID
    resident_name: str
    pgy_level: int
    generated_at: datetime

    # Current state
    current_alertness: float
    samn_perelli_level: SamnPerelliLevel
    sleep_debt_hours: float
    circadian_phase: CircadianPhase
    hours_since_sleep: float

    # Hazard assessment
    hazard_level: HazardLevel
    hazard_triggers: list[str]
    required_mitigations: list[str]

    # Work history
    hours_worked_week: float
    hours_worked_day: float
    consecutive_duty_days: int
    consecutive_night_shifts: int

    # Predictions
    predicted_end_of_shift_alertness: Optional[float] = None
    next_rest_opportunity: Optional[datetime] = None
    recovery_sleep_needed: float = 0.0

    # ACGME compliance
    acgme_hours_remaining: float = 80.0
    acgme_violation_risk: bool = False

    def to_dict(self) -> dict:
        """Convert profile to dictionary for API response."""
        return {
            "resident_id": str(self.resident_id),
            "resident_name": self.resident_name,
            "pgy_level": self.pgy_level,
            "generated_at": self.generated_at.isoformat(),
            "current_state": {
                "alertness_score": round(self.current_alertness, 3),
                "alertness_percent": int(self.current_alertness * 100),
                "samn_perelli_level": self.samn_perelli_level.value,
                "samn_perelli_name": self.samn_perelli_level.name,
                "sleep_debt_hours": round(self.sleep_debt_hours, 1),
                "circadian_phase": self.circadian_phase.value,
                "hours_since_sleep": round(self.hours_since_sleep, 1),
            },
            "hazard": {
                "level": self.hazard_level.value,
                "level_name": self.hazard_level.name,
                "triggers": self.hazard_triggers,
                "required_mitigations": self.required_mitigations,
                "is_critical": self.hazard_level in [HazardLevel.RED, HazardLevel.BLACK],
            },
            "work_history": {
                "hours_worked_week": round(self.hours_worked_week, 1),
                "hours_worked_day": round(self.hours_worked_day, 1),
                "consecutive_duty_days": self.consecutive_duty_days,
                "consecutive_night_shifts": self.consecutive_night_shifts,
            },
            "predictions": {
                "end_of_shift_alertness": (
                    round(self.predicted_end_of_shift_alertness, 3)
                    if self.predicted_end_of_shift_alertness
                    else None
                ),
                "next_rest_opportunity": (
                    self.next_rest_opportunity.isoformat()
                    if self.next_rest_opportunity
                    else None
                ),
                "recovery_sleep_needed": round(self.recovery_sleep_needed, 1),
            },
            "acgme": {
                "hours_remaining": round(self.acgme_hours_remaining, 1),
                "violation_risk": self.acgme_violation_risk,
            },
        }


class FRMSService:
    """
    Fatigue Risk Management System Service.

    Provides comprehensive fatigue risk management capabilities
    for medical residency scheduling, adapted from aviation FRMS.

    Key Features:
    - Real-time fatigue scoring
    - Predictive alertness modeling
    - Hazard detection and mitigation
    - ACGME compliance integration
    - Temporal constraint generation

    Usage:
        service = FRMSService(db)
        profile = await service.get_resident_profile(resident_id)
        hazards = await service.scan_all_residents()
    """

    # ACGME duty hour limits
    ACGME_WEEKLY_LIMIT = 80.0
    ACGME_DAILY_LIMIT = 24.0
    ACGME_MIN_REST_BETWEEN_SHIFTS = 8.0

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        sleep_model: Optional[SleepDebtModel] = None,
        alertness_predictor: Optional[AlertnessPredictor] = None,
        hazard_engine: Optional[HazardThresholdEngine] = None,
    ):
        """
        Initialize FRMS service.

        Args:
            db: Database session for data access
            sleep_model: SleepDebtModel instance
            alertness_predictor: AlertnessPredictor instance
            hazard_engine: HazardThresholdEngine instance
        """
        self.db = db
        self.sleep_model = sleep_model or SleepDebtModel()
        self.alertness_predictor = alertness_predictor or AlertnessPredictor(
            self.sleep_model
        )
        self.hazard_engine = hazard_engine or HazardThresholdEngine()

    async def get_resident_profile(
        self,
        resident_id: UUID,
        target_time: Optional[datetime] = None,
    ) -> FatigueProfile:
        """
        Get complete fatigue profile for a resident.

        Aggregates all fatigue metrics into a comprehensive profile
        suitable for dashboard display and decision support.

        Args:
            resident_id: UUID of the resident
            target_time: Time to evaluate (default: now)

        Returns:
            FatigueProfile with complete fatigue assessment
        """
        target_time = target_time or datetime.utcnow()

        # Get resident info
        resident = await self._get_resident(resident_id)
        if not resident:
            raise ValueError(f"Resident not found: {resident_id}")

        # Get work history
        work_data = await self._get_work_history(resident_id, target_time)

        # Calculate fatigue metrics
        hours_awake = self._estimate_hours_awake(work_data, target_time)
        sleep_debt = self._estimate_sleep_debt(work_data)

        # Get alertness prediction
        shift_patterns = self._build_shift_patterns(work_data)
        prediction = self.alertness_predictor.predict_alertness(
            resident_id=resident_id,
            target_time=target_time,
            recent_shifts=shift_patterns,
            sleep_history=[],
            current_sleep_debt=sleep_debt,
        )

        # Evaluate hazard
        hazard = self.hazard_engine.evaluate_from_prediction(
            prediction=prediction,
            consecutive_nights=work_data.get("consecutive_nights", 0),
            hours_worked_week=work_data.get("hours_week", 0),
        )

        # Calculate ACGME status
        acgme_remaining = self.ACGME_WEEKLY_LIMIT - work_data.get("hours_week", 0)
        acgme_risk = acgme_remaining < 10 or hazard.acgme_risk

        profile = FatigueProfile(
            resident_id=resident_id,
            resident_name=resident.name if resident else "Unknown",
            pgy_level=resident.pgy_level if resident else 0,
            generated_at=datetime.utcnow(),
            current_alertness=prediction.alertness_score,
            samn_perelli_level=prediction.samn_perelli_estimate,
            sleep_debt_hours=sleep_debt,
            circadian_phase=prediction.circadian_phase,
            hours_since_sleep=hours_awake,
            hazard_level=hazard.hazard_level,
            hazard_triggers=[t.value for t in hazard.triggers],
            required_mitigations=[m.value for m in hazard.required_mitigations],
            hours_worked_week=work_data.get("hours_week", 0),
            hours_worked_day=work_data.get("hours_today", 0),
            consecutive_duty_days=work_data.get("consecutive_days", 0),
            consecutive_night_shifts=work_data.get("consecutive_nights", 0),
            recovery_sleep_needed=sleep_debt * self.sleep_model.DEBT_RECOVERY_RATIO,
            acgme_hours_remaining=max(0, acgme_remaining),
            acgme_violation_risk=acgme_risk,
        )

        logger.info(
            f"Generated fatigue profile for {resident_id}: "
            f"alertness={prediction.alertness_score:.2f}, "
            f"hazard={hazard.hazard_level.value}"
        )

        return profile

    async def scan_all_residents(
        self,
        target_time: Optional[datetime] = None,
        hazard_threshold: HazardLevel = HazardLevel.YELLOW,
    ) -> list[FatigueProfile]:
        """
        Scan all residents for fatigue risks.

        Returns profiles for all residents, optionally filtered
        to those above a hazard threshold.

        Args:
            target_time: Time to evaluate
            hazard_threshold: Minimum hazard level to include

        Returns:
            List of FatigueProfile for matching residents
        """
        target_time = target_time or datetime.utcnow()

        residents = await self._get_all_residents()
        profiles = []

        for resident in residents:
            try:
                profile = await self.get_resident_profile(
                    resident.id, target_time
                )
                if profile.hazard_level.value >= hazard_threshold.value:
                    profiles.append(profile)
            except Exception as e:
                logger.error(f"Error scanning resident {resident.id}: {e}")

        # Sort by hazard level (highest first)
        profiles.sort(
            key=lambda p: (p.hazard_level.value, -p.current_alertness),
            reverse=True,
        )

        return profiles

    async def assess_schedule_fatigue_risk(
        self,
        resident_id: UUID,
        proposed_shifts: list[dict],
    ) -> dict:
        """
        Assess fatigue risk for a proposed schedule.

        Evaluates how a proposed schedule would affect fatigue
        and identifies high-risk periods.

        Args:
            resident_id: UUID of the resident
            proposed_shifts: List of shift dicts with start/end times

        Returns:
            Dict with risk assessment and recommendations
        """
        # Convert to ShiftPatterns
        shifts = []
        for s in proposed_shifts:
            shift_type = ShiftType(s.get("type", "day"))
            shifts.append(
                ShiftPattern(
                    shift_type=shift_type,
                    start_time=datetime.fromisoformat(s["start"]),
                    end_time=datetime.fromisoformat(s["end"]),
                    prior_sleep_hours=s.get("prior_sleep", 7.0),
                )
            )

        # Get trajectory
        trajectory = self.alertness_predictor.predict_shift_trajectory(
            resident_id=resident_id,
            upcoming_shifts=shifts,
            current_sleep_debt=0.0,
        )

        # Identify high-risk windows
        high_risk = self.alertness_predictor.identify_high_risk_windows(trajectory)

        # Calculate overall metrics
        min_alertness = min(p.alertness_score for p in trajectory) if trajectory else 1.0
        avg_alertness = (
            sum(p.alertness_score for p in trajectory) / len(trajectory)
            if trajectory
            else 1.0
        )

        # Count hazard levels
        hazard_counts = {}
        for pred in trajectory:
            hazard = self.hazard_engine.evaluate_from_prediction(pred)
            level = hazard.hazard_level.value
            hazard_counts[level] = hazard_counts.get(level, 0) + 1

        return {
            "resident_id": str(resident_id),
            "shifts_evaluated": len(shifts),
            "overall_risk": (
                "high" if min_alertness < 0.4 else
                "moderate" if min_alertness < 0.6 else
                "low"
            ),
            "metrics": {
                "minimum_alertness": round(min_alertness, 3),
                "average_alertness": round(avg_alertness, 3),
                "high_risk_periods": len(high_risk),
            },
            "hazard_distribution": hazard_counts,
            "high_risk_windows": high_risk,
            "trajectory": [p.to_dict() for p in trajectory],
            "recommendations": self._generate_schedule_recommendations(
                trajectory, high_risk
            ),
        }

    async def get_team_heatmap(
        self,
        target_date: date,
        include_predictions: bool = True,
    ) -> dict:
        """
        Generate team fatigue heatmap for a day.

        Creates a grid of fatigue levels by resident and hour
        for visualization.

        Args:
            target_date: Date to generate heatmap for
            include_predictions: Include future hour predictions

        Returns:
            Dict with heatmap data
        """
        residents = await self._get_all_residents()
        heatmap = {
            "date": target_date.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "residents": [],
            "hours": list(range(24)),
        }

        for resident in residents:
            resident_data = {
                "resident_id": str(resident.id),
                "name": resident.name,
                "pgy_level": resident.pgy_level,
                "hourly_alertness": [],
            }

            for hour in range(24):
                target_time = datetime.combine(target_date, datetime.min.time())
                target_time = target_time.replace(hour=hour)

                try:
                    profile = await self.get_resident_profile(
                        resident.id, target_time
                    )
                    resident_data["hourly_alertness"].append({
                        "hour": hour,
                        "alertness": round(profile.current_alertness, 2),
                        "hazard_level": profile.hazard_level.value,
                    })
                except Exception:
                    resident_data["hourly_alertness"].append({
                        "hour": hour,
                        "alertness": None,
                        "hazard_level": "unknown",
                    })

            heatmap["residents"].append(resident_data)

        return heatmap

    def calculate_fatigue_score(
        self,
        hours_awake: float,
        hours_worked_24h: float,
        consecutive_night_shifts: int = 0,
        time_of_day_hour: int = 12,
        prior_sleep_hours: float = 7.0,
    ) -> dict:
        """
        Calculate real-time fatigue score from factors.

        Simple synchronous calculation for immediate scoring
        without database access.

        Args:
            hours_awake: Hours since last sleep
            hours_worked_24h: Work hours in last 24h
            consecutive_night_shifts: Number of consecutive nights
            time_of_day_hour: Current hour (0-23)
            prior_sleep_hours: Hours of prior sleep

        Returns:
            Dict with fatigue score and metrics
        """
        sp_level = estimate_level_from_factors(
            hours_awake=hours_awake,
            hours_worked_24h=hours_worked_24h,
            consecutive_night_shifts=consecutive_night_shifts,
            time_of_day_hour=time_of_day_hour,
            prior_sleep_hours=prior_sleep_hours,
        )

        # Estimate alertness from SP level
        alertness = 1.0 - (sp_level.value - 1) / 6.0

        # Get circadian phase
        dummy_time = datetime.now().replace(hour=time_of_day_hour)
        circadian_phase = self.sleep_model.get_circadian_phase(dummy_time)

        return {
            "samn_perelli_level": sp_level.value,
            "samn_perelli_name": sp_level.name,
            "alertness_score": round(alertness, 3),
            "circadian_phase": circadian_phase.value,
            "factors": {
                "hours_awake": hours_awake,
                "hours_worked_24h": hours_worked_24h,
                "consecutive_night_shifts": consecutive_night_shifts,
                "time_of_day_hour": time_of_day_hour,
                "prior_sleep_hours": prior_sleep_hours,
            },
        }

    def export_temporal_constraints(self) -> dict:
        """
        Export temporal constraint data for holographic hub.

        Generates JSON data describing the chronobiology constraints
        used in scheduling optimization.

        Returns:
            Dict with temporal constraint specifications
        """
        return {
            "version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "framework": "Aviation FRMS adapted for Medical Residency",
            "references": [
                "FAA AC 120-103A",
                "ICAO Doc 9966",
                "ACGME Duty Hours",
            ],
            "circadian_rhythm": {
                "description": "24-hour biological clock affecting alertness",
                "phases": [
                    {
                        "phase": phase.value,
                        "time_range": self._get_phase_time_range(phase),
                        "alertness_multiplier": mult,
                        "scheduling_impact": self._get_phase_scheduling_impact(phase),
                    }
                    for phase, mult in self.sleep_model.__class__.__bases__[0].__dict__.get(
                        "CIRCADIAN_MULTIPLIERS", {}
                    ).items()
                ] if False else self._build_circadian_phases(),
            },
            "sleep_homeostasis": {
                "description": "Sleep pressure accumulation and recovery",
                "baseline_sleep_need": self.sleep_model.baseline_sleep_need,
                "max_trackable_debt": self.sleep_model.MAX_DEBT_HOURS,
                "recovery_ratio": self.sleep_model.DEBT_RECOVERY_RATIO,
                "debt_severity_thresholds": {
                    "mild": 2.0,
                    "moderate": 5.0,
                    "severe": 10.0,
                    "critical": 20.0,
                },
            },
            "samn_perelli_scale": {
                "description": "7-level subjective fatigue scale (USAF 1982)",
                "levels": [
                    {"level": i, "description": self._get_sp_description(i)}
                    for i in range(1, 8)
                ],
                "duty_thresholds": {
                    duty: level.value
                    for duty, level in DUTY_THRESHOLDS.items()
                },
            },
            "hazard_thresholds": {
                "description": "Fatigue hazard levels triggering interventions",
                "levels": [
                    {
                        "level": level.value,
                        "alertness_min": thresholds["alertness_min"],
                        "sleep_debt_max": thresholds["sleep_debt_max"],
                        "hours_awake_max": thresholds["hours_awake_max"],
                    }
                    for level, thresholds in {
                        HazardLevel.GREEN: {"alertness_min": 0.7, "sleep_debt_max": 5, "hours_awake_max": 14},
                        HazardLevel.YELLOW: {"alertness_min": 0.55, "sleep_debt_max": 10, "hours_awake_max": 18},
                        HazardLevel.ORANGE: {"alertness_min": 0.45, "sleep_debt_max": 15, "hours_awake_max": 22},
                        HazardLevel.RED: {"alertness_min": 0.35, "sleep_debt_max": 20, "hours_awake_max": 26},
                        HazardLevel.BLACK: {"alertness_min": 0.0, "sleep_debt_max": 40, "hours_awake_max": 48},
                    }.items()
                ],
            },
            "acgme_integration": {
                "description": "FRMS validates ACGME compliance through fatigue lens",
                "weekly_limit": self.ACGME_WEEKLY_LIMIT,
                "daily_limit": self.ACGME_DAILY_LIMIT,
                "min_rest_between": self.ACGME_MIN_REST_BETWEEN_SHIFTS,
            },
            "scheduling_constraints": {
                "hard_constraints": [
                    {
                        "name": "circadian_nadir_avoidance",
                        "description": "Avoid scheduling high-risk procedures during circadian nadir (2-6 AM)",
                        "applies_to": ["procedures", "critical_care"],
                    },
                    {
                        "name": "max_consecutive_nights",
                        "description": "Maximum consecutive night shifts before mandatory recovery",
                        "limit": 4,
                    },
                    {
                        "name": "post_call_restriction",
                        "description": "No new duties after 24-hour call until rest period",
                        "min_rest_hours": 8,
                    },
                ],
                "soft_constraints": [
                    {
                        "name": "circadian_alignment",
                        "description": "Prefer shifts aligned with circadian rhythm",
                        "weight": 0.3,
                    },
                    {
                        "name": "sleep_debt_prevention",
                        "description": "Avoid schedules that accumulate sleep debt",
                        "weight": 0.4,
                    },
                    {
                        "name": "recovery_opportunity",
                        "description": "Ensure adequate recovery time between duty periods",
                        "weight": 0.3,
                    },
                ],
            },
        }

    # Helper methods

    async def _get_resident(self, resident_id: UUID) -> Optional[Person]:
        """Get resident by ID."""
        if not self.db:
            return None
        result = await self.db.execute(
            select(Person).where(Person.id == resident_id)
        )
        return result.scalar_one_or_none()

    async def _get_all_residents(self) -> list[Person]:
        """Get all residents."""
        if not self.db:
            return []
        result = await self.db.execute(
            select(Person).where(Person.type == "resident")
        )
        return list(result.scalars().all())

    async def _get_work_history(
        self,
        resident_id: UUID,
        target_time: datetime,
    ) -> dict:
        """Get work history for a resident."""
        if not self.db:
            return {
                "hours_week": 0,
                "hours_today": 0,
                "consecutive_days": 0,
                "consecutive_nights": 0,
            }

        # Get assignments in last 7 days
        week_ago = target_time - timedelta(days=7)
        today = target_time.date()

        result = await self.db.execute(
            select(Assignment)
            .join(Block)
            .where(
                and_(
                    Assignment.person_id == resident_id,
                    Block.date >= week_ago.date(),
                    Block.date <= today,
                )
            )
        )
        assignments = list(result.scalars().all())

        # Calculate metrics
        hours_week = len(assignments) * 6  # 6 hours per half-day block
        hours_today = sum(
            1 for a in assignments
            if hasattr(a, 'block') and a.block and a.block.date == today
        ) * 6

        # Simplified consecutive days/nights calculation
        return {
            "hours_week": hours_week,
            "hours_today": hours_today,
            "consecutive_days": min(len(set(a.block.date for a in assignments if hasattr(a, 'block') and a.block)), 7),
            "consecutive_nights": 0,  # Would need more complex logic
        }

    def _estimate_hours_awake(self, work_data: dict, target_time: datetime) -> float:
        """Estimate hours since last sleep."""
        # Simplified: assume woke at 6 AM if working today
        if work_data.get("hours_today", 0) > 0:
            wake_time = target_time.replace(hour=6, minute=0)
            if target_time > wake_time:
                return (target_time - wake_time).total_seconds() / 3600
        return 8.0  # Default assumption

    def _estimate_sleep_debt(self, work_data: dict) -> float:
        """Estimate sleep debt from work history."""
        # Simplified: assume 1 hour debt per 12 hours worked above 40/week
        excess_hours = max(0, work_data.get("hours_week", 0) - 40)
        return excess_hours / 12

    def _build_shift_patterns(self, work_data: dict) -> list[ShiftPattern]:
        """Build shift patterns from work data."""
        # Simplified implementation
        return []

    def _generate_schedule_recommendations(
        self,
        trajectory: list[AlertnessPrediction],
        high_risk: list[dict],
    ) -> list[str]:
        """Generate recommendations for schedule optimization."""
        recommendations = []

        if high_risk:
            recommendations.append(
                f"Schedule contains {len(high_risk)} high-risk periods - consider modifications"
            )

        if any(p.alertness_score < 0.4 for p in trajectory):
            recommendations.append(
                "Critical alertness levels predicted - avoid scheduling high-risk duties"
            )

        if len(trajectory) > 3:
            avg = sum(p.alertness_score for p in trajectory) / len(trajectory)
            if avg < 0.6:
                recommendations.append(
                    "Overall schedule fatigue burden is high - consider adding rest days"
                )

        if not recommendations:
            recommendations.append("Schedule fatigue risk within acceptable limits")

        return recommendations

    def _build_circadian_phases(self) -> list[dict]:
        """Build circadian phase data for export."""
        from app.resilience.frms.sleep_debt import CIRCADIAN_MULTIPLIERS

        return [
            {
                "phase": phase.value,
                "time_range": self._get_phase_time_range(phase),
                "alertness_multiplier": mult,
                "scheduling_impact": self._get_phase_scheduling_impact(phase),
            }
            for phase, mult in CIRCADIAN_MULTIPLIERS.items()
        ]

    def _get_phase_time_range(self, phase: CircadianPhase) -> str:
        """Get time range for circadian phase."""
        ranges = {
            CircadianPhase.NADIR: "02:00-06:00",
            CircadianPhase.EARLY_MORNING: "06:00-09:00",
            CircadianPhase.MORNING_PEAK: "09:00-12:00",
            CircadianPhase.POST_LUNCH: "12:00-15:00",
            CircadianPhase.AFTERNOON: "15:00-18:00",
            CircadianPhase.EVENING: "18:00-21:00",
            CircadianPhase.NIGHT: "21:00-02:00",
        }
        return ranges.get(phase, "Unknown")

    def _get_phase_scheduling_impact(self, phase: CircadianPhase) -> str:
        """Get scheduling impact description for phase."""
        impacts = {
            CircadianPhase.NADIR: "Avoid high-risk procedures; heightened supervision required",
            CircadianPhase.EARLY_MORNING: "Good for routine tasks; alertness building",
            CircadianPhase.MORNING_PEAK: "Optimal for complex procedures and decisions",
            CircadianPhase.POST_LUNCH: "Schedule lighter duties; natural dip period",
            CircadianPhase.AFTERNOON: "Good for sustained attention tasks",
            CircadianPhase.EVENING: "Routine duties; prepare for handoff",
            CircadianPhase.NIGHT: "Enhanced monitoring; limit duration for day-workers",
        }
        return impacts.get(phase, "Monitor alertness")

    def _get_sp_description(self, level: int) -> str:
        """Get Samn-Perelli level description."""
        descriptions = {
            1: "Fully alert, wide awake, extremely peppy",
            2: "Very lively, responsive, but not at peak",
            3: "Okay, somewhat fresh",
            4: "A little tired, less than fresh",
            5: "Moderately tired, let down",
            6: "Extremely tired, very difficult to concentrate",
            7: "Completely exhausted, unable to function effectively",
        }
        return descriptions.get(level, "Unknown")
