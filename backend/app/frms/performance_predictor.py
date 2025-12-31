"""
Machine Learning Performance Degradation Predictor.

This module implements predictive models for resident performance degradation
based on fatigue indicators. Uses ensemble methods combining:

1. Bio-mathematical model features (Three-Process Model outputs)
2. Schedule pattern features (consecutive days, night shifts, call frequency)
3. Historical performance indicators (error reports, near-misses)
4. Circadian alignment metrics

The ML model predicts:
- Next-shift performance degradation probability
- Optimal break timing for performance recovery
- Risk of clinical errors under current schedule
- Recommended interventions

Model Architecture:
- Feature extraction from schedule and fatigue data
- Gradient boosting for degradation prediction
- Probabilistic outputs with confidence intervals

Validation:
- Designed for cross-validation against resident reported fatigue
- Integration with actual error reporting systems
- Calibration against PVT-style cognitive testing
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from enum import Enum
from typing import Any
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class ClinicalRiskLevel(str, Enum):
    """
    Clinical error risk levels based on fatigue.

    Mapped from aviation risk categories to medical context.
    """

    MINIMAL = "minimal"  # <5% error rate increase
    LOW = "low"  # 5-20% error rate increase
    MODERATE = "moderate"  # 20-50% error rate increase
    HIGH = "high"  # 50-100% error rate increase
    SEVERE = "severe"  # >100% error rate increase (2x+ baseline)


@dataclass
class PerformanceDegradation:
    """
    Predicted performance degradation analysis.

    Attributes:
        person_id: UUID of the resident
        prediction_time: When prediction was made
        degradation_probability: Probability of significant degradation (0-1)
        error_multiplier: Expected error rate multiplier (1.0 = baseline)
        clinical_risk: Categorical risk level
        contributing_factors: Factors contributing to degradation
        confidence_interval: 95% CI for degradation probability
        recommended_actions: List of recommended interventions
        optimal_break_time: Recommended time for recovery break
        hours_to_recovery: Hours needed to reach acceptable performance
    """

    person_id: UUID
    prediction_time: datetime
    degradation_probability: float
    error_multiplier: float
    clinical_risk: ClinicalRiskLevel
    contributing_factors: dict[str, float] = field(default_factory=dict)
    confidence_interval: tuple[float, float] = (0.0, 1.0)
    recommended_actions: list[str] = field(default_factory=list)
    optimal_break_time: datetime | None = None
    hours_to_recovery: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to dictionary for API response."""
        return {
            "person_id": str(self.person_id),
            "prediction_time": self.prediction_time.isoformat(),
            "degradation_probability": round(self.degradation_probability, 4),
            "error_multiplier": round(self.error_multiplier, 2),
            "clinical_risk": self.clinical_risk.value,
            "contributing_factors": {
                k: round(v, 4) for k, v in self.contributing_factors.items()
            },
            "confidence_interval": {
                "lower": round(self.confidence_interval[0], 4),
                "upper": round(self.confidence_interval[1], 4),
            },
            "recommended_actions": self.recommended_actions,
            "optimal_break_time": (
                self.optimal_break_time.isoformat() if self.optimal_break_time else None
            ),
            "hours_to_recovery": round(self.hours_to_recovery, 1),
        }


@dataclass
class ScheduleFeatures:
    """
    Extracted features from schedule for ML prediction.

    Features are normalized and designed for gradient boosting input.
    """

    # Time-based features
    consecutive_duty_days: int = 0
    hours_since_rest: float = 0.0
    hours_worked_7d: float = 0.0
    hours_worked_14d: float = 0.0
    hours_worked_28d: float = 0.0

    # Night shift features
    night_shifts_7d: int = 0
    night_shifts_14d: int = 0
    is_currently_night_shift: bool = False
    hours_in_wocl_7d: float = 0.0

    # Call and intensity features
    call_shifts_7d: int = 0
    weekend_days_worked: int = 0
    high_intensity_rotations: int = 0

    # Recovery features
    days_since_full_day_off: int = 0
    average_sleep_hours: float = 7.0
    recovery_quality_score: float = 1.0

    # Circadian features
    shift_start_hour: float = 7.0
    circadian_alignment_score: float = 1.0
    rotation_transitions_14d: int = 0

    # Historical features (if available)
    prior_fatigue_reports: int = 0
    prior_near_misses: int = 0

    def to_vector(self) -> list[float]:
        """Convert to feature vector for ML model."""
        return [
            float(self.consecutive_duty_days),
            self.hours_since_rest,
            self.hours_worked_7d,
            self.hours_worked_14d,
            self.hours_worked_28d,
            float(self.night_shifts_7d),
            float(self.night_shifts_14d),
            float(self.is_currently_night_shift),
            self.hours_in_wocl_7d,
            float(self.call_shifts_7d),
            float(self.weekend_days_worked),
            float(self.high_intensity_rotations),
            float(self.days_since_full_day_off),
            self.average_sleep_hours,
            self.recovery_quality_score,
            self.shift_start_hour,
            self.circadian_alignment_score,
            float(self.rotation_transitions_14d),
            float(self.prior_fatigue_reports),
            float(self.prior_near_misses),
        ]


class PerformancePredictor:
    """
    ML-based performance degradation predictor.

    Uses an ensemble of features from bio-mathematical models and
    schedule patterns to predict performance degradation risk.

    The model is designed as a gradient boosting classifier but
    implemented here as a rule-based system that can be replaced
    with actual ML once training data is available.

    Usage:
        predictor = PerformancePredictor()
        features = predictor.extract_features(schedule_data, fatigue_state)
        prediction = predictor.predict(features, person_id)
    """

    # Feature importance weights (learned from literature/domain expertise)
    FEATURE_WEIGHTS = {
        "hours_since_rest": 0.15,
        "consecutive_duty_days": 0.12,
        "night_shifts_7d": 0.11,
        "hours_in_wocl_7d": 0.10,
        "hours_worked_7d": 0.09,
        "days_since_full_day_off": 0.08,
        "average_sleep_hours": 0.07,
        "circadian_alignment_score": 0.07,
        "call_shifts_7d": 0.06,
        "rotation_transitions_14d": 0.05,
        "is_currently_night_shift": 0.04,
        "weekend_days_worked": 0.03,
        "high_intensity_rotations": 0.03,
    }

    # Thresholds for risk classification
    DEGRADATION_THRESHOLDS = {
        "severe": 0.80,  # >80% probability = severe
        "high": 0.60,  # >60% = high
        "moderate": 0.40,  # >40% = moderate
        "low": 0.20,  # >20% = low
        "minimal": 0.0,  # <20% = minimal
    }

    # Error multiplier mapping
    ERROR_MULTIPLIER_MAP = {
        ClinicalRiskLevel.MINIMAL: 1.0,
        ClinicalRiskLevel.LOW: 1.2,
        ClinicalRiskLevel.MODERATE: 1.5,
        ClinicalRiskLevel.HIGH: 2.0,
        ClinicalRiskLevel.SEVERE: 3.0,
    }

    def __init__(self, model_version: str = "rule_based_v1"):
        """
        Initialize performance predictor.

        Args:
            model_version: Version identifier for the prediction model
        """
        self.model_version = model_version
        logger.info(f"Initialized PerformancePredictor (version: {model_version})")

    def extract_features(
        self,
        assignments: list[dict],
        current_time: datetime,
        fatigue_effectiveness: float | None = None,
        sleep_data: dict | None = None,
    ) -> ScheduleFeatures:
        """
        Extract ML features from schedule and fatigue data.

        Args:
            assignments: List of assignment dicts with block dates and types
            current_time: Current datetime for feature calculation
            fatigue_effectiveness: Current effectiveness from Three-Process Model
            sleep_data: Optional sleep tracking data

        Returns:
            ScheduleFeatures ready for prediction
        """
        features = ScheduleFeatures()

        if not assignments:
            return features

        # Sort assignments by date
        sorted_assignments = sorted(
            assignments,
            key=lambda a: a.get("date", date.min)
            if isinstance(a.get("date"), date)
            else date.fromisoformat(str(a.get("date", "2000-01-01"))),
        )

        current_date = current_time.date()

        # Calculate time-based features
        features.consecutive_duty_days = self._count_consecutive_days(
            sorted_assignments, current_date
        )

        features.hours_worked_7d = self._count_hours_in_window(
            sorted_assignments, current_date, 7
        )
        features.hours_worked_14d = self._count_hours_in_window(
            sorted_assignments, current_date, 14
        )
        features.hours_worked_28d = self._count_hours_in_window(
            sorted_assignments, current_date, 28
        )

        # Night shift features
        features.night_shifts_7d = self._count_night_shifts(
            sorted_assignments, current_date, 7
        )
        features.night_shifts_14d = self._count_night_shifts(
            sorted_assignments, current_date, 14
        )

        # Check if current shift is night shift
        current_hour = current_time.hour
        features.is_currently_night_shift = current_hour >= 18 or current_hour < 6
        features.shift_start_hour = current_hour

        # WOCL exposure
        features.hours_in_wocl_7d = self._estimate_wocl_hours(
            sorted_assignments, current_date, 7
        )

        # Call and weekend features
        features.call_shifts_7d = self._count_call_shifts(
            sorted_assignments, current_date, 7
        )
        features.weekend_days_worked = self._count_weekend_days(
            sorted_assignments, current_date, 14
        )

        # Recovery features
        features.days_since_full_day_off = self._days_since_off(
            sorted_assignments, current_date
        )

        # Rotation transitions
        features.rotation_transitions_14d = self._count_transitions(
            sorted_assignments, current_date, 14
        )

        # Sleep and circadian features
        if sleep_data:
            features.average_sleep_hours = sleep_data.get("average_hours", 7.0)
            features.recovery_quality_score = sleep_data.get("quality_score", 1.0)

        if fatigue_effectiveness is not None:
            # Map effectiveness to circadian alignment
            features.circadian_alignment_score = fatigue_effectiveness / 100.0

        return features

    def predict(
        self,
        features: ScheduleFeatures,
        person_id: UUID,
        prediction_time: datetime | None = None,
    ) -> PerformanceDegradation:
        """
        Predict performance degradation probability.

        Uses weighted feature combination (rule-based ML approximation)
        to estimate degradation risk. Can be replaced with actual
        trained model when data is available.

        Args:
            features: Extracted schedule features
            person_id: UUID of the person
            prediction_time: When prediction is for (default: now)

        Returns:
            PerformanceDegradation with risk assessment
        """
        prediction_time = prediction_time or datetime.now()

        # Calculate weighted risk score
        risk_score = self._calculate_risk_score(features)

        # Apply sigmoid to get probability
        degradation_prob = self._sigmoid(risk_score)

        # Determine clinical risk level
        clinical_risk = self._determine_risk_level(degradation_prob)

        # Get error multiplier
        error_multiplier = self.ERROR_MULTIPLIER_MAP[clinical_risk]

        # Calculate contributing factors
        contributing_factors = self._calculate_factor_contributions(features)

        # Calculate confidence interval (simple estimate based on data completeness)
        ci_width = 0.15  # Base confidence interval width
        confidence_interval = (
            max(0.0, degradation_prob - ci_width),
            min(1.0, degradation_prob + ci_width),
        )

        # Generate recommendations
        recommended_actions = self._generate_recommendations(
            features, degradation_prob, clinical_risk
        )

        # Calculate recovery time
        hours_to_recovery = self._estimate_recovery_time(features, degradation_prob)

        # Optimal break time
        optimal_break_time = self._calculate_optimal_break(
            prediction_time, features, degradation_prob
        )

        prediction = PerformanceDegradation(
            person_id=person_id,
            prediction_time=prediction_time,
            degradation_probability=degradation_prob,
            error_multiplier=error_multiplier,
            clinical_risk=clinical_risk,
            contributing_factors=contributing_factors,
            confidence_interval=confidence_interval,
            recommended_actions=recommended_actions,
            optimal_break_time=optimal_break_time,
            hours_to_recovery=hours_to_recovery,
        )

        logger.info(
            f"Performance prediction for {person_id}: "
            f"degradation={degradation_prob:.2%}, risk={clinical_risk.value}"
        )

        return prediction

    def _calculate_risk_score(self, features: ScheduleFeatures) -> float:
        """
        Calculate raw risk score from features.

        Uses domain-knowledge weights to combine features into
        a single risk score. Score is unbounded and will be
        transformed via sigmoid.
        """
        score = 0.0

        # Hours since rest (exponential penalty after 16 hours)
        if features.hours_since_rest > 16:
            excess = features.hours_since_rest - 16
            score += 0.15 * (1 + math.log(1 + excess))
        else:
            score += 0.15 * (features.hours_since_rest / 24)

        # Consecutive duty days (strong penalty after 6 days)
        if features.consecutive_duty_days > 6:
            score += 0.12 * (1 + (features.consecutive_duty_days - 6) * 0.3)
        else:
            score += 0.12 * (features.consecutive_duty_days / 7)

        # Night shifts (cumulative fatigue)
        score += 0.11 * min(1.0, features.night_shifts_7d / 3.0)

        # WOCL exposure
        score += 0.10 * min(1.0, features.hours_in_wocl_7d / 20.0)

        # Weekly hours (ACGME limit is 80)
        score += 0.09 * min(1.0, features.hours_worked_7d / 80.0)

        # Days since off (penalty increases after 7 days)
        if features.days_since_full_day_off > 7:
            score += 0.08 * (1 + (features.days_since_full_day_off - 7) * 0.2)
        else:
            score += 0.08 * (features.days_since_full_day_off / 7)

        # Sleep deficit (inverse relationship)
        sleep_deficit = max(0, 8 - features.average_sleep_hours)
        score += 0.07 * (sleep_deficit / 4)

        # Circadian misalignment (inverse of alignment score)
        score += 0.07 * (1 - features.circadian_alignment_score)

        # Call shifts
        score += 0.06 * min(1.0, features.call_shifts_7d / 2.0)

        # Rotation transitions
        score += 0.05 * min(1.0, features.rotation_transitions_14d / 4.0)

        # Current night shift bonus
        if features.is_currently_night_shift:
            score += 0.04

        # Weekend burden
        score += 0.03 * min(1.0, features.weekend_days_worked / 4.0)

        return score

    def _sigmoid(self, x: float, k: float = 4.0, x0: float = 0.5) -> float:
        """
        Apply sigmoid transformation to get probability.

        Args:
            x: Raw score
            k: Steepness parameter
            x0: Midpoint (50% probability point)

        Returns:
            Probability between 0 and 1
        """
        return 1.0 / (1.0 + math.exp(-k * (x - x0)))

    def _determine_risk_level(self, probability: float) -> ClinicalRiskLevel:
        """Determine clinical risk level from probability."""
        if probability >= self.DEGRADATION_THRESHOLDS["severe"]:
            return ClinicalRiskLevel.SEVERE
        elif probability >= self.DEGRADATION_THRESHOLDS["high"]:
            return ClinicalRiskLevel.HIGH
        elif probability >= self.DEGRADATION_THRESHOLDS["moderate"]:
            return ClinicalRiskLevel.MODERATE
        elif probability >= self.DEGRADATION_THRESHOLDS["low"]:
            return ClinicalRiskLevel.LOW
        else:
            return ClinicalRiskLevel.MINIMAL

    def _calculate_factor_contributions(
        self, features: ScheduleFeatures
    ) -> dict[str, float]:
        """Calculate relative contribution of each factor to risk."""
        contributions = {}

        # Normalize each factor's contribution
        total = 0.0
        raw_contributions = {
            "sleep_debt": max(0, 8 - features.average_sleep_hours) / 4 * 0.15,
            "consecutive_days": features.consecutive_duty_days / 7 * 0.12,
            "night_shifts": features.night_shifts_7d / 5 * 0.11,
            "wocl_exposure": features.hours_in_wocl_7d / 20 * 0.10,
            "weekly_hours": features.hours_worked_7d / 80 * 0.09,
            "days_without_rest": features.days_since_full_day_off / 7 * 0.08,
            "circadian_misalignment": (1 - features.circadian_alignment_score) * 0.07,
        }

        total = sum(raw_contributions.values()) or 1.0

        for factor, value in raw_contributions.items():
            contributions[factor] = value / total

        return contributions

    def _generate_recommendations(
        self,
        features: ScheduleFeatures,
        probability: float,
        risk_level: ClinicalRiskLevel,
    ) -> list[str]:
        """Generate actionable recommendations based on risk factors."""
        recommendations = []

        if risk_level in (ClinicalRiskLevel.SEVERE, ClinicalRiskLevel.HIGH):
            recommendations.append(
                "URGENT: Consider immediate rest period or reduced duties"
            )

        if features.consecutive_duty_days >= 6:
            recommendations.append(
                f"Schedule day off within 24 hours "
                f"({features.consecutive_duty_days} consecutive duty days)"
            )

        if features.night_shifts_7d >= 3:
            recommendations.append("Limit additional night shifts this week")

        if features.hours_in_wocl_7d > 10:
            recommendations.append(
                "Reduce WOCL (2-6 AM) exposure - high circadian risk"
            )

        if features.average_sleep_hours < 6:
            recommendations.append(
                "Sleep deficit detected - ensure adequate recovery sleep"
            )

        if features.days_since_full_day_off > 6:
            recommendations.append(
                f"ACGME 1-in-7 rule at risk - schedule full day off "
                f"({features.days_since_full_day_off} days since last)"
            )

        if features.circadian_alignment_score < 0.7:
            recommendations.append(
                "Circadian misalignment detected - consider schedule adjustment"
            )

        if not recommendations:
            recommendations.append("Performance risk within acceptable limits")

        return recommendations

    def _estimate_recovery_time(
        self, features: ScheduleFeatures, probability: float
    ) -> float:
        """Estimate hours of rest needed to recover to acceptable performance."""
        base_recovery = 8.0  # Minimum full night's sleep

        # Additional recovery for each risk factor
        extra_recovery = 0.0

        if features.consecutive_duty_days > 5:
            extra_recovery += (features.consecutive_duty_days - 5) * 2

        if features.night_shifts_7d > 2:
            extra_recovery += (features.night_shifts_7d - 2) * 4

        sleep_deficit = max(0, 8 - features.average_sleep_hours) * 2
        extra_recovery += sleep_deficit

        # Scale by probability
        total_recovery = base_recovery + extra_recovery * probability

        return min(48.0, total_recovery)  # Cap at 48 hours

    def _calculate_optimal_break(
        self,
        current_time: datetime,
        features: ScheduleFeatures,
        probability: float,
    ) -> datetime | None:
        """Calculate optimal time for a recovery break."""
        if probability < 0.3:
            return None  # No break urgently needed

        # Suggest break during next circadian peak
        current_hour = current_time.hour

        # Morning peak: 9-11 AM, Afternoon peak: 3-5 PM
        if current_hour < 9:
            # Before morning peak - can push to 9 AM
            optimal_hour = 9
        elif current_hour < 15:
            # Between peaks - suggest afternoon break
            optimal_hour = 15
        else:
            # After afternoon peak - suggest next morning
            optimal_hour = 9
            current_time += timedelta(days=1)

        optimal_break = current_time.replace(
            hour=optimal_hour, minute=0, second=0, microsecond=0
        )

        return optimal_break

    # =========================================================================
    # Feature Extraction Helpers
    # =========================================================================

    def _count_consecutive_days(
        self, assignments: list[dict], current_date: date
    ) -> int:
        """Count consecutive duty days leading up to current date."""
        dates_worked = set()
        for a in assignments:
            a_date = a.get("date")
            if isinstance(a_date, str):
                a_date = date.fromisoformat(a_date)
            if a_date:
                dates_worked.add(a_date)

        consecutive = 0
        check_date = current_date
        while check_date in dates_worked:
            consecutive += 1
            check_date -= timedelta(days=1)

        return consecutive

    def _count_hours_in_window(
        self, assignments: list[dict], current_date: date, days: int
    ) -> float:
        """Count hours worked in the past N days."""
        window_start = current_date - timedelta(days=days)
        hours = 0.0

        for a in assignments:
            a_date = a.get("date")
            if isinstance(a_date, str):
                a_date = date.fromisoformat(a_date)
            if a_date and window_start <= a_date <= current_date:
                # Assume 6 hours per half-day block
                hours += a.get("hours", 6.0)

        return hours

    def _count_night_shifts(
        self, assignments: list[dict], current_date: date, days: int
    ) -> int:
        """Count night shifts in the past N days."""
        window_start = current_date - timedelta(days=days)
        count = 0

        for a in assignments:
            a_date = a.get("date")
            if isinstance(a_date, str):
                a_date = date.fromisoformat(a_date)
            if a_date and window_start <= a_date <= current_date:
                if a.get("time_of_day") == "PM" or a.get("is_night_shift"):
                    count += 1

        return count

    def _estimate_wocl_hours(
        self, assignments: list[dict], current_date: date, days: int
    ) -> float:
        """Estimate hours spent in WOCL (2-6 AM) window."""
        # Approximate: night shifts include ~4 hours of WOCL
        night_shifts = self._count_night_shifts(assignments, current_date, days)
        return night_shifts * 4.0

    def _count_call_shifts(
        self, assignments: list[dict], current_date: date, days: int
    ) -> int:
        """Count call shifts in the past N days."""
        window_start = current_date - timedelta(days=days)
        count = 0

        for a in assignments:
            a_date = a.get("date")
            if isinstance(a_date, str):
                a_date = date.fromisoformat(a_date)
            if a_date and window_start <= a_date <= current_date:
                if a.get("is_call") or "call" in a.get("rotation_type", "").lower():
                    count += 1

        return count

    def _count_weekend_days(
        self, assignments: list[dict], current_date: date, days: int
    ) -> int:
        """Count weekend days worked in the past N days."""
        window_start = current_date - timedelta(days=days)
        weekend_dates = set()

        for a in assignments:
            a_date = a.get("date")
            if isinstance(a_date, str):
                a_date = date.fromisoformat(a_date)
            if a_date and window_start <= a_date <= current_date:
                if a_date.weekday() >= 5:  # Saturday=5, Sunday=6
                    weekend_dates.add(a_date)

        return len(weekend_dates)

    def _days_since_off(self, assignments: list[dict], current_date: date) -> int:
        """Calculate days since last full day off."""
        dates_worked = set()
        for a in assignments:
            a_date = a.get("date")
            if isinstance(a_date, str):
                a_date = date.fromisoformat(a_date)
            if a_date:
                dates_worked.add(a_date)

        days_since = 0
        check_date = current_date
        max_lookback = 14

        while days_since < max_lookback:
            if check_date not in dates_worked:
                break
            days_since += 1
            check_date -= timedelta(days=1)

        return days_since

    def _count_transitions(
        self, assignments: list[dict], current_date: date, days: int
    ) -> int:
        """Count rotation type transitions in the past N days."""
        window_start = current_date - timedelta(days=days)
        relevant = []

        for a in assignments:
            a_date = a.get("date")
            if isinstance(a_date, str):
                a_date = date.fromisoformat(a_date)
            if a_date and window_start <= a_date <= current_date:
                relevant.append((a_date, a.get("rotation_type", "unknown")))

        # Sort by date
        relevant.sort(key=lambda x: x[0])

        # Count transitions
        transitions = 0
        prev_rotation = None
        for _, rotation in relevant:
            if prev_rotation and rotation != prev_rotation:
                transitions += 1
            prev_rotation = rotation

        return transitions
