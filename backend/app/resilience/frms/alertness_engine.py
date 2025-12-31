"""
Alertness Prediction Engine for Medical Residency Scheduling.

Predicts future alertness levels based on:
- Prior shift patterns and cumulative workload
- Sleep opportunity windows
- Circadian timing of shifts
- Individual fatigue history

This engine integrates the Three-Process Model (Åkerstedt & Folkard, 1997):
- Process S: Sleep homeostasis (sleep debt accumulation)
- Process C: Circadian rhythm (24-hour biological clock)
- Process W: Sleep inertia (grogginess after waking)

The engine provides:
1. Point-in-time alertness predictions
2. Shift-by-shift fatigue trajectory
3. Risk identification for high-fatigue periods
4. Schedule optimization recommendations

Medical Residency Context:
- Shift patterns (day, night, call) heavily influence fatigue
- Call schedules create extended wakefulness
- Post-call recovery is critical for safety
- Rotation transitions create adjustment periods

References:
- Åkerstedt, T. & Folkard, S. (1997). The three-process model of alertness.
- Hursh, S.R. et al. (2004). Fatigue models for applied research.
- Van Dongen, H.P. (2004). Comparison of mathematical model predictions.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID

from app.core.logging import get_logger
from app.resilience.frms.samn_perelli import (
    SamnPerelliLevel,
    estimate_level_from_factors,
)
from app.resilience.frms.sleep_debt import (
    CircadianPhase,
    SleepDebtModel,
    SleepOpportunity,
    CIRCADIAN_MULTIPLIERS,
)

logger = get_logger(__name__)


class ShiftType(str, Enum):
    """Types of clinical shifts affecting fatigue patterns."""

    DAY = "day"  # Standard daytime (7 AM - 5 PM)
    EVENING = "evening"  # Evening shift (3 PM - 11 PM)
    NIGHT = "night"  # Night shift (7 PM - 7 AM)
    CALL_24 = "call_24"  # 24-hour in-house call
    CALL_28 = "call_28"  # 28-hour extended call
    POST_CALL = "post_call"  # Day after call (typically off by 12 PM)
    OFF = "off"  # Day off
    HALF_DAY = "half_day"  # Half-day clinic or education


# Shift characteristics for fatigue modeling
SHIFT_CHARACTERISTICS = {
    ShiftType.DAY: {
        "typical_start_hour": 7,
        "typical_end_hour": 17,
        "duration_hours": 10,
        "circadian_aligned": True,
        "fatigue_factor": 1.0,
    },
    ShiftType.EVENING: {
        "typical_start_hour": 15,
        "typical_end_hour": 23,
        "duration_hours": 8,
        "circadian_aligned": False,
        "fatigue_factor": 1.2,
    },
    ShiftType.NIGHT: {
        "typical_start_hour": 19,
        "typical_end_hour": 7,
        "duration_hours": 12,
        "circadian_aligned": False,
        "fatigue_factor": 1.8,
    },
    ShiftType.CALL_24: {
        "typical_start_hour": 7,
        "typical_end_hour": 7,
        "duration_hours": 24,
        "circadian_aligned": False,
        "fatigue_factor": 2.5,
    },
    ShiftType.CALL_28: {
        "typical_start_hour": 7,
        "typical_end_hour": 11,
        "duration_hours": 28,
        "circadian_aligned": False,
        "fatigue_factor": 3.0,
    },
    ShiftType.POST_CALL: {
        "typical_start_hour": 7,
        "typical_end_hour": 12,
        "duration_hours": 5,
        "circadian_aligned": True,
        "fatigue_factor": 1.5,  # Still fatigued from call
    },
    ShiftType.OFF: {
        "typical_start_hour": 0,
        "typical_end_hour": 0,
        "duration_hours": 0,
        "circadian_aligned": True,
        "fatigue_factor": 0.0,
    },
    ShiftType.HALF_DAY: {
        "typical_start_hour": 8,
        "typical_end_hour": 12,
        "duration_hours": 4,
        "circadian_aligned": True,
        "fatigue_factor": 0.5,
    },
}


@dataclass
class ShiftPattern:
    """
    Represents a work shift for alertness prediction.

    Attributes:
        shift_type: Type of clinical shift
        start_time: Shift start datetime
        end_time: Shift end datetime
        duration_hours: Actual shift duration
        is_overnight: Whether shift crosses midnight
        prior_sleep_hours: Hours of sleep before this shift
        prior_sleep_quality: Sleep quality factor (0.0-1.0)
    """

    shift_type: ShiftType
    start_time: datetime
    end_time: datetime
    duration_hours: float = field(init=False)
    is_overnight: bool = field(init=False)
    prior_sleep_hours: float = 7.0
    prior_sleep_quality: float = 0.9

    def __post_init__(self):
        """Calculate derived fields."""
        delta = self.end_time - self.start_time
        self.duration_hours = delta.total_seconds() / 3600
        self.is_overnight = self.end_time.date() > self.start_time.date()

    @property
    def fatigue_factor(self) -> float:
        """Get fatigue factor for this shift type."""
        return SHIFT_CHARACTERISTICS.get(self.shift_type, {}).get("fatigue_factor", 1.0)

    @property
    def is_circadian_aligned(self) -> bool:
        """Check if shift is aligned with normal circadian rhythm."""
        return SHIFT_CHARACTERISTICS.get(self.shift_type, {}).get(
            "circadian_aligned", True
        )


@dataclass
class AlertnessPrediction:
    """
    Predicted alertness for a specific time point.

    Combines sleep homeostasis, circadian rhythm, and recent
    work history to predict performance capability.

    Attributes:
        resident_id: UUID of the resident
        prediction_time: Time point being predicted
        alertness_score: Predicted alertness (0.0-1.0, 1.0 = fully alert)
        samn_perelli_estimate: Estimated Samn-Perelli level
        circadian_phase: Current circadian phase
        hours_awake: Estimated hours since last sleep
        sleep_debt: Cumulative sleep debt
        performance_capacity: Estimated performance capacity percentage
        risk_level: Risk classification
        contributing_factors: Factors affecting alertness
        recommendations: Suggested mitigations
    """

    resident_id: UUID
    prediction_time: datetime
    alertness_score: float
    samn_perelli_estimate: SamnPerelliLevel
    circadian_phase: CircadianPhase
    hours_awake: float
    sleep_debt: float
    performance_capacity: float
    risk_level: str
    contributing_factors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert prediction to dictionary for API response."""
        return {
            "resident_id": str(self.resident_id),
            "prediction_time": self.prediction_time.isoformat(),
            "alertness_score": round(self.alertness_score, 3),
            "alertness_percent": int(self.alertness_score * 100),
            "samn_perelli": {
                "level": self.samn_perelli_estimate.value,
                "name": self.samn_perelli_estimate.name,
            },
            "circadian_phase": self.circadian_phase.value,
            "hours_awake": round(self.hours_awake, 1),
            "sleep_debt": round(self.sleep_debt, 1),
            "performance_capacity": int(self.performance_capacity),
            "risk_level": self.risk_level,
            "contributing_factors": self.contributing_factors,
            "recommendations": self.recommendations,
        }


class AlertnessPredictor:
    """
    Predicts alertness based on shift patterns and sleep history.

    Implements a modified Three-Process Model for medical residency:
    - Process S: Sleep homeostasis (debt accumulation/recovery)
    - Process C: Circadian rhythm (time-of-day effects)
    - Process W: Sleep inertia (post-wake grogginess)

    Additional factors considered:
    - Workload intensity and duration
    - Shift transition effects
    - Cumulative fatigue from consecutive shifts
    - Individual variability

    Usage:
        predictor = AlertnessPredictor()
        prediction = predictor.predict_alertness(
            resident_id=UUID("..."),
            target_time=datetime.now() + timedelta(hours=8),
            recent_shifts=[...],
            sleep_history=[...]
        )
    """

    # Alertness thresholds
    HIGH_ALERT_THRESHOLD = 0.8  # Above this = good performance
    MODERATE_ALERT_THRESHOLD = 0.6  # Below this = concerning
    LOW_ALERT_THRESHOLD = 0.4  # Below this = high risk

    # Sleep inertia parameters
    SLEEP_INERTIA_DURATION_MINUTES = 30  # Duration of post-wake grogginess
    SLEEP_INERTIA_IMPACT = 0.15  # Reduction in alertness

    def __init__(self, sleep_model: SleepDebtModel | None = None):
        """
        Initialize alertness predictor.

        Args:
            sleep_model: SleepDebtModel instance (created if not provided)
        """
        self.sleep_model = sleep_model or SleepDebtModel()

    def predict_alertness(
        self,
        resident_id: UUID,
        target_time: datetime,
        recent_shifts: list[ShiftPattern],
        sleep_history: list[SleepOpportunity],
        current_sleep_debt: float = 0.0,
    ) -> AlertnessPrediction:
        """
        Predict alertness for a specific time point.

        Combines multiple fatigue factors to estimate alertness
        and derive safety recommendations.

        Args:
            resident_id: UUID of the resident
            target_time: Time to predict alertness for
            recent_shifts: Shifts in the last 7-14 days
            sleep_history: Sleep periods in the last 7 days
            current_sleep_debt: Known current sleep debt

        Returns:
            AlertnessPrediction with score and recommendations

        Example:
            >>> predictor = AlertnessPredictor()
            >>> shifts = [
            ...     ShiftPattern(ShiftType.NIGHT, start, end, prior_sleep_hours=6),
            ...     ShiftPattern(ShiftType.NIGHT, next_start, next_end, prior_sleep_hours=5),
            ... ]
            >>> prediction = predictor.predict_alertness(
            ...     UUID("..."),
            ...     datetime.now() + timedelta(hours=4),
            ...     shifts,
            ...     []
            ... )
            >>> print(prediction.risk_level)  # "high" or "moderate"
        """
        # Calculate component scores
        hours_awake = self._estimate_hours_awake(target_time, sleep_history)
        circadian_score = self._calculate_circadian_score(target_time)
        sleep_inertia = self._calculate_sleep_inertia(target_time, sleep_history)
        workload_impact = self._calculate_workload_impact(recent_shifts, target_time)

        # Estimate sleep debt if not provided
        if current_sleep_debt <= 0 and sleep_history:
            current_sleep_debt = self._estimate_sleep_debt(sleep_history)

        debt_impact = self._calculate_debt_impact(current_sleep_debt)

        # Combine into overall alertness score
        # Base alertness starts at 1.0 and is reduced by various factors
        base_alertness = 1.0

        # Apply circadian modulation
        alertness = base_alertness * circadian_score

        # Apply hours awake penalty (exponential decay after 16 hours)
        awake_penalty = self._hours_awake_penalty(hours_awake)
        alertness *= 1.0 - awake_penalty

        # Apply sleep debt penalty
        alertness *= 1.0 - debt_impact

        # Apply workload impact
        alertness *= 1.0 - workload_impact

        # Apply sleep inertia if recently woke
        alertness *= 1.0 - sleep_inertia

        # Clamp to valid range
        alertness = max(0.1, min(1.0, alertness))

        # Derive other metrics
        sp_level = self._alertness_to_samn_perelli(alertness, hours_awake)
        circadian_phase = self.sleep_model.get_circadian_phase(target_time)
        performance_capacity = alertness * 100
        risk_level = self._classify_risk(alertness, hours_awake, current_sleep_debt)
        factors = self._identify_contributing_factors(
            hours_awake, circadian_score, current_sleep_debt, workload_impact
        )
        recommendations = self._generate_recommendations(
            risk_level, hours_awake, current_sleep_debt, target_time
        )

        prediction = AlertnessPrediction(
            resident_id=resident_id,
            prediction_time=target_time,
            alertness_score=alertness,
            samn_perelli_estimate=sp_level,
            circadian_phase=circadian_phase,
            hours_awake=hours_awake,
            sleep_debt=current_sleep_debt,
            performance_capacity=performance_capacity,
            risk_level=risk_level,
            contributing_factors=factors,
            recommendations=recommendations,
        )

        logger.info(
            f"Alertness prediction for {resident_id} at {target_time}: "
            f"score={alertness:.2f}, SP-{sp_level.value}, "
            f"risk={risk_level}, awake={hours_awake:.1f}h"
        )

        return prediction

    def predict_shift_trajectory(
        self,
        resident_id: UUID,
        upcoming_shifts: list[ShiftPattern],
        current_sleep_debt: float = 0.0,
        sleep_per_off_day: float = 8.5,
    ) -> list[AlertnessPrediction]:
        """
        Predict alertness trajectory across multiple shifts.

        Useful for evaluating proposed schedules and identifying
        high-risk periods before they occur.

        Args:
            resident_id: UUID of the resident
            upcoming_shifts: Planned shift sequence
            current_sleep_debt: Starting sleep debt
            sleep_per_off_day: Expected sleep on days off

        Returns:
            List of predictions for each shift's key points

        Example:
            >>> predictor = AlertnessPredictor()
            >>> shifts = [
            ...     ShiftPattern(ShiftType.DAY, ...),
            ...     ShiftPattern(ShiftType.NIGHT, ...),
            ...     ShiftPattern(ShiftType.NIGHT, ...),
            ...     ShiftPattern(ShiftType.POST_CALL, ...),
            ...     ShiftPattern(ShiftType.OFF, ...),
            ... ]
            >>> trajectory = predictor.predict_shift_trajectory(
            ...     UUID("..."),
            ...     shifts,
            ...     current_sleep_debt=5.0
            ... )
            >>> for pred in trajectory:
            ...     print(f"{pred.prediction_time}: {pred.alertness_score:.2f}")
        """
        predictions = []
        running_debt = current_sleep_debt
        sleep_history = []

        for i, shift in enumerate(upcoming_shifts):
            # Create sleep opportunity before this shift
            if shift.prior_sleep_hours > 0:
                sleep_end = shift.start_time
                sleep_start = sleep_end - timedelta(hours=shift.prior_sleep_hours)
                sleep_opp = SleepOpportunity(
                    start_time=sleep_start,
                    end_time=sleep_end,
                    quality_factor=shift.prior_sleep_quality,
                    circadian_aligned=shift.is_circadian_aligned,
                )
                sleep_history.append(sleep_opp)

            # Predict at shift midpoint (when fatigue often peaks)
            if shift.shift_type != ShiftType.OFF:
                midpoint = shift.start_time + timedelta(hours=shift.duration_hours / 2)
                prediction = self.predict_alertness(
                    resident_id=resident_id,
                    target_time=midpoint,
                    recent_shifts=upcoming_shifts[: i + 1],
                    sleep_history=sleep_history,
                    current_sleep_debt=running_debt,
                )
                predictions.append(prediction)

            # Update running debt
            if shift.shift_type == ShiftType.OFF:
                # Recovery on off day
                extra_sleep = sleep_per_off_day - self.sleep_model.baseline_sleep_need
                recovery = extra_sleep / self.sleep_model.DEBT_RECOVERY_RATIO
                running_debt = max(0, running_debt - recovery)
            else:
                # Accumulate debt from inadequate sleep
                debt_change = (
                    self.sleep_model.baseline_sleep_need - shift.prior_sleep_hours
                )
                if debt_change > 0:
                    running_debt += debt_change

        return predictions

    def identify_high_risk_windows(
        self,
        trajectory: list[AlertnessPrediction],
        threshold: float = 0.5,
    ) -> list[dict]:
        """
        Identify periods of high fatigue risk in a trajectory.

        Args:
            trajectory: List of alertness predictions
            threshold: Alertness threshold for high risk

        Returns:
            List of high-risk windows with details
        """
        high_risk = []

        for pred in trajectory:
            if pred.alertness_score < threshold:
                high_risk.append(
                    {
                        "time": pred.prediction_time.isoformat(),
                        "alertness": round(pred.alertness_score, 3),
                        "samn_perelli": pred.samn_perelli_estimate.value,
                        "risk_level": pred.risk_level,
                        "factors": pred.contributing_factors,
                        "recommendations": pred.recommendations,
                    }
                )

        return high_risk

    def _estimate_hours_awake(
        self,
        target_time: datetime,
        sleep_history: list[SleepOpportunity],
    ) -> float:
        """Estimate hours since last sleep period."""
        if not sleep_history:
            # Default assumption: 8 hours if no history
            return 8.0

        # Find most recent sleep end time
        most_recent = max(sleep_history, key=lambda s: s.end_time)
        delta = target_time - most_recent.end_time

        # If sleep end is in the future, assume just woke up
        if delta.total_seconds() < 0:
            return 0.0

        return delta.total_seconds() / 3600

    def _calculate_circadian_score(self, target_time: datetime) -> float:
        """Get circadian alertness multiplier."""
        return self.sleep_model.get_circadian_multiplier(target_time)

    def _calculate_sleep_inertia(
        self,
        target_time: datetime,
        sleep_history: list[SleepOpportunity],
    ) -> float:
        """Calculate sleep inertia penalty if recently woke."""
        if not sleep_history:
            return 0.0

        most_recent = max(sleep_history, key=lambda s: s.end_time)
        minutes_since_wake = (target_time - most_recent.end_time).total_seconds() / 60

        if (
            minutes_since_wake < 0
            or minutes_since_wake > self.SLEEP_INERTIA_DURATION_MINUTES
        ):
            return 0.0

        # Linear decay of inertia
        inertia_fraction = 1.0 - (
            minutes_since_wake / self.SLEEP_INERTIA_DURATION_MINUTES
        )
        return self.SLEEP_INERTIA_IMPACT * inertia_fraction

    def _calculate_workload_impact(
        self,
        recent_shifts: list[ShiftPattern],
        target_time: datetime,
    ) -> float:
        """Calculate fatigue impact from recent workload."""
        if not recent_shifts:
            return 0.0

        # Look at shifts in last 7 days
        lookback = target_time - timedelta(days=7)
        recent = [s for s in recent_shifts if s.start_time >= lookback]

        if not recent:
            return 0.0

        # Sum fatigue factors weighted by recency
        total_impact = 0.0
        for shift in recent:
            days_ago = (target_time - shift.start_time).days
            recency_weight = max(0.1, 1.0 - (days_ago * 0.1))
            total_impact += shift.fatigue_factor * recency_weight * 0.05

        # Cap at 0.4 (40% reduction)
        return min(0.4, total_impact)

    def _estimate_sleep_debt(self, sleep_history: list[SleepOpportunity]) -> float:
        """Estimate sleep debt from sleep history."""
        if not sleep_history:
            return 0.0

        total_effective = sum(s.effective_sleep_hours for s in sleep_history)
        days = len(sleep_history)
        avg_sleep = total_effective / days if days > 0 else 0

        daily_deficit = self.sleep_model.baseline_sleep_need - avg_sleep
        return max(0, daily_deficit * days)

    def _calculate_debt_impact(self, sleep_debt: float) -> float:
        """Calculate alertness reduction from sleep debt."""
        # Linear relationship with saturation
        # 10 hours debt ≈ 20% reduction
        return min(0.5, sleep_debt * 0.02)

    def _hours_awake_penalty(self, hours_awake: float) -> float:
        """Calculate penalty for extended wakefulness."""
        if hours_awake <= 12:
            return 0.0
        elif hours_awake <= 16:
            return (hours_awake - 12) * 0.025
        elif hours_awake <= 20:
            return 0.1 + (hours_awake - 16) * 0.05
        elif hours_awake <= 24:
            return 0.3 + (hours_awake - 20) * 0.075
        else:
            return min(0.7, 0.6 + (hours_awake - 24) * 0.05)

    def _alertness_to_samn_perelli(
        self,
        alertness: float,
        hours_awake: float,
    ) -> SamnPerelliLevel:
        """Convert alertness score to Samn-Perelli level."""
        # Use estimate function from samn_perelli module
        # Map alertness to hours worked approximation
        hours_worked = min(hours_awake, 16)

        return estimate_level_from_factors(
            hours_awake=hours_awake,
            hours_worked_24h=hours_worked,
            consecutive_night_shifts=0,
            time_of_day_hour=12,  # Neutral
            prior_sleep_hours=7.0 * alertness,  # Inverse relationship
        )

    def _classify_risk(
        self,
        alertness: float,
        hours_awake: float,
        sleep_debt: float,
    ) -> str:
        """Classify overall fatigue risk level."""
        # High risk if any critical threshold exceeded
        if alertness < self.LOW_ALERT_THRESHOLD:
            return "high"
        if hours_awake > 20:
            return "high"
        if sleep_debt > 15:
            return "high"

        # Moderate risk
        if alertness < self.MODERATE_ALERT_THRESHOLD:
            return "moderate"
        if hours_awake > 16:
            return "moderate"
        if sleep_debt > 8:
            return "moderate"

        # Low risk
        if alertness < self.HIGH_ALERT_THRESHOLD:
            return "low"

        return "minimal"

    def _identify_contributing_factors(
        self,
        hours_awake: float,
        circadian_score: float,
        sleep_debt: float,
        workload_impact: float,
    ) -> list[str]:
        """Identify primary factors affecting alertness."""
        factors = []

        if hours_awake > 16:
            factors.append(f"Extended wakefulness ({hours_awake:.1f} hours)")
        if circadian_score < 0.8:
            factors.append("Circadian low point")
        if sleep_debt > 5:
            factors.append(f"Accumulated sleep debt ({sleep_debt:.1f} hours)")
        if workload_impact > 0.2:
            factors.append("High recent workload")

        return factors if factors else ["No significant fatigue factors"]

    def _generate_recommendations(
        self,
        risk_level: str,
        hours_awake: float,
        sleep_debt: float,
        target_time: datetime,
    ) -> list[str]:
        """Generate fatigue mitigation recommendations."""
        recommendations = []

        if risk_level == "high":
            recommendations.append("Consider deferring non-essential duties")
            recommendations.append("Avoid high-risk procedures if possible")
            if hours_awake > 20:
                recommendations.append("Strongly recommend sleep before continuing")

        if risk_level in ["high", "moderate"]:
            recommendations.append("Strategic caffeine use may help temporarily")
            recommendations.append("Take micro-breaks (10-15 min) when possible")
            if sleep_debt > 10:
                recommendations.append("Plan recovery sleep within 24 hours")

        # Circadian-specific advice
        phase = self.sleep_model.get_circadian_phase(target_time)
        if phase == CircadianPhase.NADIR:
            recommendations.append(
                "High vigilance needed during circadian low (2-6 AM)"
            )

        if not recommendations:
            recommendations.append("Current alertness adequate for clinical duties")

        return recommendations
