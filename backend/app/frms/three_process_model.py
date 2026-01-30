"""
Three-Process Model of Alertness.

This module implements the bio-mathematical Three-Process Model for predicting
human alertness and effectiveness, combining:

1. Process S (Homeostatic): Sleep debt accumulation and recovery
2. Process C (Circadian): 24-hour biological rhythm
3. Process W (Sleep Inertia): Grogginess immediately after waking

Based on validated aviation models:
- Two-Process Model (Borbély 1982)
- SAFTE-FAST (Hursh et al., validated by FAA CAMI)
- ICAO/FAA/EASA regulatory thresholds

Key Features:
- Real-time effectiveness scoring (0-100%)
- Window of Circadian Low (WOCL) detection (2:00-6:00 AM)
- Shift-specific effectiveness predictions
- Cumulative sleep debt tracking
- Sleep quality adjustments

Regulatory Thresholds:
- 95-100%: Optimal performance
- 85-94%: Acceptable
- 77-84%: FAA caution threshold
- 70-76%: FRA high-risk threshold
- <70%: Unacceptable for safety-critical tasks

References:
- Hursh, S.R. et al. (2004). Fatigue models for applied research in warfighting.
- FAA CAMI (2009-2010). Field validation with 178 flight attendants.
- Borbély, A.A. (1982). A two process model of sleep regulation.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

import logging

logger = logging.getLogger(__name__)


class CircadianPhase(str, Enum):
    """
    Circadian rhythm phases affecting alertness.

    Based on physiological markers (cortisol, melatonin, body temperature).
    """

    WOCL = "wocl"  # Window of Circadian Low (2:00-6:00 AM) - minimum alertness
    MORNING_RISE = "morning_rise"  # 6:00-9:00 AM - cortisol rising
    MORNING_PEAK = "morning_peak"  # 9:00-12:00 PM - peak alertness
    POST_LUNCH_DIP = "post_lunch_dip"  # 12:00-3:00 PM - alertness decline
    AFTERNOON_RISE = "afternoon_rise"  # 3:00-6:00 PM - secondary peak
    EVENING = "evening"  # 6:00-10:00 PM - gradual decline
    PRE_SLEEP = "pre_sleep"  # 10:00 PM-2:00 AM - melatonin rising


class SleepInertiaState(str, Enum):
    """
    Sleep inertia severity states.

    Sleep inertia is grogginess immediately after waking that impairs
    performance for 5-30 minutes (or longer with severe sleep debt).
    """

    SEVERE = "severe"  # 0-5 minutes: 20-30% impairment
    MODERATE = "moderate"  # 5-15 minutes: 10-20% impairment
    MILD = "mild"  # 15-30 minutes: 5-10% impairment
    RESOLVED = "resolved"  # >30 minutes: no impairment


@dataclass
class EffectivenessScore:
    """
    Comprehensive effectiveness score with component breakdown.

    Attributes:
        overall: Combined effectiveness score (0-100%)
        homeostatic: Sleep debt component (Process S)
        circadian: Biological rhythm component (Process C)
        sleep_inertia: Post-wake grogginess penalty (Process W)
        timestamp: When score was calculated
        risk_level: Categorical risk assessment
        factors: Detailed factor breakdown
    """

    overall: float
    homeostatic: float
    circadian: float
    sleep_inertia: float
    timestamp: datetime
    risk_level: str
    factors: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to dictionary for API response."""
        return {
            "overall": round(self.overall, 2),
            "components": {
                "homeostatic": round(self.homeostatic, 2),
                "circadian": round(self.circadian, 2),
                "sleep_inertia": round(self.sleep_inertia, 2),
            },
            "timestamp": self.timestamp.isoformat(),
            "risk_level": self.risk_level,
            "factors": self.factors,
        }


@dataclass
class AlertnessState:
    """
    Complete alertness state for a person at a point in time.

    Tracks all three processes and provides effectiveness predictions.

    Attributes:
        person_id: UUID of the person
        timestamp: Current time
        sleep_reservoir: Current sleep reservoir level (0-100)
        hours_awake: Hours since last sleep
        last_sleep_end: When last sleep period ended
        last_sleep_duration: Duration of last sleep (hours)
        cumulative_debt: Accumulated sleep debt over multiple days
        circadian_phase: Current phase of circadian rhythm
        effectiveness: Current effectiveness score
        time_series: Historical effectiveness values
    """

    person_id: UUID
    timestamp: datetime
    sleep_reservoir: float = 100.0
    hours_awake: float = 0.0
    last_sleep_end: datetime | None = None
    last_sleep_duration: float = 8.0
    cumulative_debt: float = 0.0
    circadian_phase: CircadianPhase = CircadianPhase.MORNING_PEAK
    effectiveness: EffectivenessScore | None = None
    time_series: list[tuple[datetime, float]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dictionary for API response."""
        return {
            "person_id": str(self.person_id),
            "timestamp": self.timestamp.isoformat(),
            "sleep_reservoir": round(self.sleep_reservoir, 2),
            "hours_awake": round(self.hours_awake, 2),
            "last_sleep_end": self.last_sleep_end.isoformat()
            if self.last_sleep_end
            else None,
            "last_sleep_duration": round(self.last_sleep_duration, 2),
            "cumulative_debt": round(self.cumulative_debt, 2),
            "circadian_phase": self.circadian_phase.value,
            "effectiveness": self.effectiveness.to_dict()
            if self.effectiveness
            else None,
            "time_series": [
                {"time": t.isoformat(), "effectiveness": round(e, 2)}
                for t, e in self.time_series[-48:]  # Last 48 data points
            ],
        }


class ThreeProcessModel:
    """
    Bio-mathematical Three-Process Model for alertness prediction.

    Combines three physiological processes:
    1. Process S (Homeostatic): Sleep pressure builds during waking, dissipates during sleep
    2. Process C (Circadian): 24-hour rhythm with minimum at 4:00 AM
    3. Process W (Sleep Inertia): Performance impairment immediately after waking

    Constants calibrated against:
    - SAFTE-FAST model parameters
    - PVT (Psychomotor Vigilance Task) validation data
    - FAA CAMI field studies

    Usage:
        model = ThreeProcessModel()
        state = model.create_state(resident_id)
        state = model.update_wakefulness(state, hours=4.0)
        state = model.update_sleep(state, hours=7.5)
        score = model.calculate_effectiveness(state)
    """

    # =========================================================================
    # Model Constants (from SAFTE-FAST literature)
    # =========================================================================

    # Process S: Homeostatic constants
    TAU_WAKE = 18.2  # Time constant for sleep pressure rise (hours)
    TAU_SLEEP = 4.2  # Time constant for sleep pressure decay (hours)
    S_MIN = 0.0  # Minimum sleep reservoir level
    S_MAX = 100.0  # Maximum sleep reservoir level
    DEPLETION_RATE = 5.5  # Points lost per TAU_WAKE during waking
    RECOVERY_RATE = 20.0  # Points gained per TAU_SLEEP during sleep

    # Process C: Circadian constants
    CIRCADIAN_PERIOD = 24.0  # Period in hours
    CIRCADIAN_AMPLITUDE = 0.25  # Amplitude as fraction of mean (25% swing)
    CIRCADIAN_PHASE_SHIFT = 4.0  # Hours after midnight for minimum (4:00 AM)
    WOCL_START = 2.0  # Window of Circadian Low start (2:00 AM)
    WOCL_END = 6.0  # Window of Circadian Low end (6:00 AM)

    # Process W: Sleep inertia constants
    INERTIA_DURATION = 30.0  # Minutes for inertia to resolve
    INERTIA_MAX_PENALTY = 25.0  # Maximum penalty percentage
    INERTIA_DEBT_MULTIPLIER = 1.5  # Extra inertia with sleep debt

    # Effectiveness thresholds
    THRESHOLD_OPTIMAL = 95.0  # Fully rested optimal performance
    THRESHOLD_ACCEPTABLE = 85.0  # Acceptable performance
    THRESHOLD_FAA_CAUTION = 77.0  # FAA caution threshold
    THRESHOLD_FRA_HIGH_RISK = 70.0  # Federal Rail Administration threshold
    THRESHOLD_UNACCEPTABLE = 60.0  # Unacceptable for safety-critical tasks

    # Component weights for combined score
    WEIGHT_HOMEOSTATIC = 0.55  # 55% weight on sleep debt
    WEIGHT_CIRCADIAN = 0.35  # 35% weight on circadian rhythm
    WEIGHT_INERTIA = 0.10  # 10% weight on sleep inertia (when applicable)

    def __init__(self, calibration: dict[str, float] | None = None) -> None:
        """
        Initialize Three-Process Model with optional calibration.

        Args:
            calibration: Optional dict to override default constants
        """
        if calibration:
            for key, value in calibration.items():
                if hasattr(self, key.upper()):
                    setattr(self, key.upper(), value)
                    logger.info(f"Calibrated {key.upper()} = {value}")

                    # =========================================================================
                    # State Management
                    # =========================================================================

    def create_state(
        self,
        person_id: UUID,
        initial_reservoir: float = 100.0,
        timestamp: datetime | None = None,
    ) -> AlertnessState:
        """
        Create initial alertness state for a person.

        Args:
            person_id: UUID of the person
            initial_reservoir: Starting sleep reservoir (default: fully rested)
            timestamp: Current time (default: now)

        Returns:
            AlertnessState initialized for the person
        """
        timestamp = timestamp or datetime.now()
        phase = self._get_circadian_phase(timestamp.hour + timestamp.minute / 60.0)

        state = AlertnessState(
            person_id=person_id,
            timestamp=timestamp,
            sleep_reservoir=initial_reservoir,
            hours_awake=0.0,
            circadian_phase=phase,
        )

        # Calculate initial effectiveness
        state.effectiveness = self.calculate_effectiveness(state)

        logger.debug(
            f"Created state for {person_id}: "
            f"reservoir={initial_reservoir:.1f}, phase={phase.value}"
        )

        return state

    def update_wakefulness(
        self,
        state: AlertnessState,
        hours: float,
    ) -> AlertnessState:
        """
        Update state for time spent awake.

        Process S increases during wakefulness following an exponential
        saturation curve: S(t) = S_0 - (S_max - S_0) * (1 - exp(-t/τ))

        Args:
            state: Current alertness state
            hours: Hours of wakefulness to add

        Returns:
            Updated AlertnessState
        """
        if hours <= 0:
            return state

            # Update timestamp
        new_timestamp = state.timestamp + timedelta(hours=hours)

        # Process S: Sleep reservoir depletion during waking
        # Exponential decay toward minimum
        depletion = self.DEPLETION_RATE * (hours / self.TAU_WAKE)
        new_reservoir = max(self.S_MIN, state.sleep_reservoir - depletion)

        # Track cumulative debt if below optimal
        debt_threshold = 85.0
        if new_reservoir < debt_threshold:
            debt_increase = (debt_threshold - new_reservoir) * (hours / 24.0)
            new_debt = state.cumulative_debt + debt_increase
        else:
            new_debt = max(0, state.cumulative_debt - hours * 0.5)  # Slow recovery

            # Update circadian phase
        time_of_day = new_timestamp.hour + new_timestamp.minute / 60.0
        new_phase = self._get_circadian_phase(time_of_day)

        # Create updated state
        new_state = AlertnessState(
            person_id=state.person_id,
            timestamp=new_timestamp,
            sleep_reservoir=new_reservoir,
            hours_awake=state.hours_awake + hours,
            last_sleep_end=state.last_sleep_end,
            last_sleep_duration=state.last_sleep_duration,
            cumulative_debt=new_debt,
            circadian_phase=new_phase,
            time_series=state.time_series.copy(),
        )

        # Calculate new effectiveness
        new_state.effectiveness = self.calculate_effectiveness(new_state)

        # Add to time series
        new_state.time_series.append((new_timestamp, new_state.effectiveness.overall))

        logger.debug(
            f"Wakefulness update: +{hours:.1f}h, "
            f"reservoir {state.sleep_reservoir:.1f} -> {new_reservoir:.1f}, "
            f"effectiveness={new_state.effectiveness.overall:.1f}%"
        )

        return new_state

    def update_sleep(
        self,
        state: AlertnessState,
        hours: float,
        quality: float = 1.0,
    ) -> AlertnessState:
        """
        Update state for sleep period.

        Process S decreases during sleep following exponential decay:
        S(t) = S_max * exp(-t/τ)

        Args:
            state: Current alertness state
            hours: Hours of sleep
            quality: Sleep quality multiplier (0.5-1.0, default: 1.0)

        Returns:
            Updated AlertnessState with sleep inertia effects
        """
        if hours <= 0:
            return state

        quality = max(0.5, min(1.0, quality))  # Clamp to valid range

        # Calculate effective sleep (adjusted for quality)
        effective_hours = hours * quality

        # Update timestamp to end of sleep
        new_timestamp = state.timestamp + timedelta(hours=hours)

        # Process S: Sleep reservoir recovery during sleep
        recovery = self.RECOVERY_RATE * (effective_hours / self.TAU_SLEEP)
        new_reservoir = min(self.S_MAX, state.sleep_reservoir + recovery)

        # Reduce cumulative debt (sleep pays off debt)
        debt_recovery = (
            effective_hours * 2.0
        )  # Each hour of sleep reduces 2 hours of debt
        new_debt = max(0, state.cumulative_debt - debt_recovery)

        # Update circadian phase
        time_of_day = new_timestamp.hour + new_timestamp.minute / 60.0
        new_phase = self._get_circadian_phase(time_of_day)

        # Create updated state
        new_state = AlertnessState(
            person_id=state.person_id,
            timestamp=new_timestamp,
            sleep_reservoir=new_reservoir,
            hours_awake=0.0,  # Reset on wake
            last_sleep_end=new_timestamp,
            last_sleep_duration=hours,
            cumulative_debt=new_debt,
            circadian_phase=new_phase,
            time_series=state.time_series.copy(),
        )

        # Calculate new effectiveness (will include sleep inertia)
        new_state.effectiveness = self.calculate_effectiveness(new_state)

        # Add to time series
        new_state.time_series.append((new_timestamp, new_state.effectiveness.overall))

        logger.debug(
            f"Sleep update: {hours:.1f}h (quality={quality:.2f}), "
            f"reservoir {state.sleep_reservoir:.1f} -> {new_reservoir:.1f}, "
            f"effectiveness={new_state.effectiveness.overall:.1f}%"
        )

        return new_state

        # =========================================================================
        # Effectiveness Calculation
        # =========================================================================

    def calculate_effectiveness(
        self,
        state: AlertnessState,
        time_of_day: float | None = None,
    ) -> EffectivenessScore:
        """
        Calculate combined effectiveness score from all three processes.

        Formula: E = w_s * S + w_c * C - I
        where:
        - S = homeostatic component (sleep reservoir)
        - C = circadian component (time-of-day effect)
        - I = sleep inertia penalty (if just woke up)
        - w_s, w_c = component weights

        Args:
            state: Current alertness state
            time_of_day: Override time of day (default: from state timestamp)

        Returns:
            EffectivenessScore with component breakdown
        """
        if time_of_day is None:
            time_of_day = state.timestamp.hour + state.timestamp.minute / 60.0

            # Process S: Homeostatic component (normalized 0-100)
        homeostatic = state.sleep_reservoir

        # Apply cumulative debt penalty
        if state.cumulative_debt > 0:
            debt_penalty = min(20, state.cumulative_debt * 0.5)
            homeostatic = max(0, homeostatic - debt_penalty)

            # Process C: Circadian component (normalized 0-100)
        circadian = self._circadian_component(time_of_day)

        # Process W: Sleep inertia penalty
        inertia_penalty = self._sleep_inertia_penalty(state)

        # Combined effectiveness (weighted sum minus inertia)
        combined = (
            self.WEIGHT_HOMEOSTATIC * homeostatic
            + self.WEIGHT_CIRCADIAN * circadian
            - inertia_penalty
        )

        # Normalize to 0-100 range
        overall = max(0.0, min(100.0, combined))

        # Determine risk level
        risk_level = self._determine_risk_level(overall)

        # Build factors breakdown
        factors = {
            "hours_awake": state.hours_awake,
            "cumulative_debt_hours": state.cumulative_debt,
            "in_wocl": self.is_in_wocl(time_of_day),
            "circadian_phase": state.circadian_phase.value,
            "minutes_since_wake": (
                (state.timestamp - state.last_sleep_end).total_seconds() / 60.0
                if state.last_sleep_end
                else None
            ),
            "last_sleep_hours": state.last_sleep_duration,
        }

        return EffectivenessScore(
            overall=overall,
            homeostatic=homeostatic,
            circadian=circadian,
            sleep_inertia=inertia_penalty,
            timestamp=state.timestamp,
            risk_level=risk_level,
            factors=factors,
        )

    def _circadian_component(self, time_of_day: float) -> float:
        """
        Calculate circadian alertness component (0-100 scale).

        Uses sinusoidal model with minimum at CIRCADIAN_PHASE_SHIFT (4:00 AM).
        Amplitude modulates around mean of 75.

        Args:
            time_of_day: Hour of day (0.0-23.99)

        Returns:
            Circadian alertness value (0-100)
        """
        # Sinusoidal: minimum at 4:00 AM, maximum at 4:00 PM
        # C(t) = mean + amplitude * sin(2π(t - phase) / period)
        mean = 75.0
        amplitude = mean * self.CIRCADIAN_AMPLITUDE

        phase_radians = (
            2
            * math.pi
            * (time_of_day - self.CIRCADIAN_PHASE_SHIFT)
            / self.CIRCADIAN_PERIOD
        )

        # Shift by -π/2 so minimum is at phase_shift
        circadian = mean + amplitude * math.sin(phase_radians - math.pi / 2)

        return circadian

    def _sleep_inertia_penalty(self, state: AlertnessState) -> float:
        """
        Calculate sleep inertia penalty (Process W).

        Sleep inertia causes performance impairment for 5-30 minutes
        after waking. Severity increases with sleep debt.

        Args:
            state: Current alertness state

        Returns:
            Penalty to subtract from effectiveness (0-25+)
        """
        if state.last_sleep_end is None:
            return 0.0

        minutes_since_wake = (
            state.timestamp - state.last_sleep_end
        ).total_seconds() / 60.0

        if minutes_since_wake >= self.INERTIA_DURATION:
            return 0.0

            # Linear decay of inertia over INERTIA_DURATION minutes
        inertia_fraction = 1.0 - (minutes_since_wake / self.INERTIA_DURATION)

        # Base penalty scaled by inertia fraction
        base_penalty = self.INERTIA_MAX_PENALTY * inertia_fraction

        # Additional penalty if sleep deprived (makes inertia worse)
        if state.cumulative_debt > 0:
            debt_multiplier = 1.0 + min(0.5, state.cumulative_debt * 0.05)
            base_penalty *= debt_multiplier

        return base_penalty

    def _get_circadian_phase(self, time_of_day: float) -> CircadianPhase:
        """
        Determine circadian phase for a given time of day.

        Args:
            time_of_day: Hour of day (0.0-23.99)

        Returns:
            CircadianPhase enum value
        """
        if 2.0 <= time_of_day < 6.0:
            return CircadianPhase.WOCL
        elif 6.0 <= time_of_day < 9.0:
            return CircadianPhase.MORNING_RISE
        elif 9.0 <= time_of_day < 12.0:
            return CircadianPhase.MORNING_PEAK
        elif 12.0 <= time_of_day < 15.0:
            return CircadianPhase.POST_LUNCH_DIP
        elif 15.0 <= time_of_day < 18.0:
            return CircadianPhase.AFTERNOON_RISE
        elif 18.0 <= time_of_day < 22.0:
            return CircadianPhase.EVENING
        else:
            return CircadianPhase.PRE_SLEEP

    def _determine_risk_level(self, effectiveness: float) -> str:
        """
        Determine risk level category from effectiveness score.

        Args:
            effectiveness: Overall effectiveness score (0-100)

        Returns:
            Risk level string
        """
        if effectiveness >= self.THRESHOLD_OPTIMAL:
            return "optimal"
        elif effectiveness >= self.THRESHOLD_ACCEPTABLE:
            return "acceptable"
        elif effectiveness >= self.THRESHOLD_FAA_CAUTION:
            return "caution"
        elif effectiveness >= self.THRESHOLD_FRA_HIGH_RISK:
            return "high_risk"
        elif effectiveness >= self.THRESHOLD_UNACCEPTABLE:
            return "unacceptable"
        else:
            return "critical"

            # =========================================================================
            # WOCL and Time-of-Day Analysis
            # =========================================================================

    def is_in_wocl(self, time_of_day: float) -> bool:
        """
        Check if time falls within Window of Circadian Low.

        WOCL (2:00-6:00 AM) is when circadian alertness is at minimum.
        Error rates are 2-3x higher during WOCL.

        Args:
            time_of_day: Hour of day (0.0-23.99)

        Returns:
            True if in WOCL
        """
        return self.WOCL_START <= time_of_day < self.WOCL_END

    def get_wocl_risk_multiplier(self, time_of_day: float) -> float:
        """
        Get risk multiplier for WOCL exposure.

        Returns higher values during WOCL to weight fatigue constraints.

        Args:
            time_of_day: Hour of day (0.0-23.99)

        Returns:
            Risk multiplier (1.0 = normal, up to 2.5 at WOCL minimum)
        """
        if not self.is_in_wocl(time_of_day):
            return 1.0

            # Peak risk at 4:00 AM (center of WOCL)
        wocl_center = 4.0
        distance_from_center = abs(time_of_day - wocl_center)
        max_distance = (self.WOCL_END - self.WOCL_START) / 2.0

        # Parabolic: maximum at center, 1.0 at edges
        normalized_distance = distance_from_center / max_distance
        multiplier = 2.5 - 1.5 * (normalized_distance**2)

        return multiplier

    def calculate_max_shift_duration(
        self,
        start_hour: float,
        base_duration: float = 12.0,
    ) -> float:
        """
        Calculate maximum recommended shift duration based on start time.

        Based on EASA "unfavorable start time" logic - shifts starting
        during WOCL or late evening should be shorter.

        Args:
            start_hour: Hour of day when shift starts (0.0-23.99)
            base_duration: Maximum duration for favorable times (default: 12)

        Returns:
            Maximum recommended shift duration in hours
        """
        # Favorable: 6 AM - 6 PM
        if 6.0 <= start_hour < 18.0:
            return base_duration

            # Moderately unfavorable: 6 PM - 10 PM
        elif 18.0 <= start_hour < 22.0:
            return base_duration - 2.0

            # Highly unfavorable: 10 PM - 6 AM (includes WOCL)
        else:
            return base_duration - 4.0

            # =========================================================================
            # Shift Prediction
            # =========================================================================

    def predict_shift_effectiveness(
        self,
        state: AlertnessState,
        shift_start: datetime,
        shift_duration_hours: float,
        sample_interval_minutes: float = 30.0,
    ) -> list[tuple[datetime, EffectivenessScore]]:
        """
        Predict effectiveness throughout an entire shift.

        Simulates the Three-Process Model forward in time to predict
        how effectiveness will change during a shift.

        Args:
            state: Current alertness state (before shift)
            shift_start: When shift begins
            shift_duration_hours: Length of shift in hours
            sample_interval_minutes: How often to sample (default: 30 min)

        Returns:
            List of (timestamp, EffectivenessScore) predictions
        """
        predictions = []
        current_state = state

        # Advance to shift start if needed
        if shift_start > state.timestamp:
            pre_shift_hours = (shift_start - state.timestamp).total_seconds() / 3600.0
            current_state = self.update_wakefulness(current_state, pre_shift_hours)

            # Sample throughout shift
        current_time = shift_start
        end_time = shift_start + timedelta(hours=shift_duration_hours)
        interval_hours = sample_interval_minutes / 60.0

        while current_time <= end_time:
            # Calculate effectiveness at this point
            time_of_day = current_time.hour + current_time.minute / 60.0
            score = self.calculate_effectiveness(current_state, time_of_day)
            predictions.append((current_time, score))

            # Advance time
            current_time += timedelta(minutes=sample_interval_minutes)
            current_state = self.update_wakefulness(current_state, interval_hours)

        return predictions

    def get_shift_summary(
        self,
        predictions: list[tuple[datetime, EffectivenessScore]],
    ) -> dict:
        """
        Summarize shift effectiveness predictions.

        Args:
            predictions: List of (timestamp, EffectivenessScore) from predict_shift_effectiveness

        Returns:
            Summary dict with min, max, mean, time in each risk level
        """
        if not predictions:
            return {}

        scores = [p[1].overall for p in predictions]
        risk_levels = [p[1].risk_level for p in predictions]

        # Time in each risk level
        risk_time: dict[str, int] = {}
        for level in risk_levels:
            risk_time[level] = risk_time.get(level, 0) + 1

            # Calculate time in WOCL
        wocl_samples = sum(
            1 for t, _ in predictions if self.is_in_wocl(t.hour + t.minute / 60.0)
        )

        return {
            "effectiveness": {
                "minimum": min(scores),
                "maximum": max(scores),
                "mean": sum(scores) / len(scores),
                "start": predictions[0][1].overall,
                "end": predictions[-1][1].overall,
            },
            "risk_distribution": {
                level: count / len(predictions) * 100
                for level, count in risk_time.items()
            },
            "wocl_exposure": {
                "samples_in_wocl": wocl_samples,
                "percentage": wocl_samples / len(predictions) * 100,
            },
            "recommendations": self._generate_recommendations(scores, wocl_samples > 0),
        }

    def _generate_recommendations(
        self,
        scores: list[float],
        has_wocl_exposure: bool,
    ) -> list[str]:
        """Generate recommendations based on shift predictions."""
        recommendations = []

        min_score = min(scores)
        mean_score = sum(scores) / len(scores)

        if min_score < self.THRESHOLD_FRA_HIGH_RISK:
            recommendations.append(
                "ALERT: Effectiveness drops below 70% - high risk for errors"
            )
            recommendations.append(
                "Consider: Reduce shift duration or ensure faculty supervision"
            )

        elif min_score < self.THRESHOLD_FAA_CAUTION:
            recommendations.append(
                "CAUTION: Effectiveness drops below 77% during shift"
            )
            recommendations.append(
                "Consider: Schedule breaks during low-effectiveness periods"
            )

        if has_wocl_exposure:
            recommendations.append("WOCL: Shift includes 2:00-6:00 AM exposure")
            recommendations.append("Avoid: High-risk procedures during WOCL window")

        if mean_score >= self.THRESHOLD_ACCEPTABLE:
            recommendations.append("Overall shift effectiveness is acceptable")

        return recommendations
