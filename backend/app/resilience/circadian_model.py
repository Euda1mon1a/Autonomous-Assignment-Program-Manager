"""
Circadian Phase Response Curve Model for Resident Wellbeing.

Models each resident as a circadian oscillator with:
- Phase φ(t): Current position in 24-hour cycle (0-24 hours)
- Amplitude A(t): Strength of circadian rhythm (0-1, degraded = burnout risk)
- Period τ ≈ 24.2 hours: Natural circadian period (free-running)

Integrates with schedule optimization to minimize circadian disruption by:
1. Predicting phase shifts from shift timing (Phase Response Curves)
2. Tracking amplitude degradation from irregular schedules
3. Computing circadian quality scores for schedule evaluation
4. Optimizing shift timing to maintain circadian alignment

Biology Basis: Phase Response Curves (PRCs)
--------------------------------------------
PRCs quantify how shift schedules shift circadian timing:

- **Morning Light (6-10 AM)**: Advances circadian phase (earlier wake time)
- **Evening Light (8 PM-12 AM)**: Delays circadian phase (later wake time)
- **Dead Zone (12-4 PM)**: Minimal phase shift effect
- **Night Exposure (12-6 AM)**: Maximal phase shift potential

Key Principle: Misalignment between internal circadian phase and external
schedule demands creates "social jetlag" similar to time zone travel.

Medical Residency Application:
- Night shifts force light exposure during circadian night → phase delays
- Rotating shifts prevent circadian adaptation → chronic misalignment
- Irregular schedules degrade amplitude → reduced alertness variance
- Forward rotation (days→evenings→nights) easier than backward

References:
- Czeisler, C.A. & Gooley, J.J. (2007). Sleep and circadian rhythms in humans.
- Khalsa, S.B. et al. (2003). A phase response curve to single bright light pulses.
- Wright, K.P. et al. (2013). Entrainment of the human circadian clock.
- Roenneberg, T. et al. (2012). Social jetlag and obesity.
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================


class CircadianShiftType(str, Enum):
    """
    Shift types with different circadian impacts.

    Each shift type has characteristic light exposure patterns
    that influence circadian phase shifts.
    """

    DAY = "day"  # 7 AM - 3 PM: Morning light exposure (phase advance)
    EVENING = "evening"  # 3 PM - 11 PM: Evening light exposure (phase delay)
    NIGHT = "night"  # 11 PM - 7 AM: Night light exposure (strong phase delay)
    LONG_DAY = "long_day"  # 7 AM - 7 PM: Extended day exposure
    SPLIT = "split"  # Interrupted: High circadian disruption


class CircadianQualityLevel(str, Enum):
    """Circadian alignment quality categories."""

    EXCELLENT = "excellent"  # 0.85-1.0: Strong, well-aligned rhythm
    GOOD = "good"  # 0.70-0.84: Adequate alignment
    FAIR = "fair"  # 0.55-0.69: Some misalignment
    POOR = "poor"  # 0.40-0.54: Significant misalignment
    CRITICAL = "critical"  # 0.0-0.39: Severe disruption


# Circadian period constants
NATURAL_PERIOD_HOURS = 24.2  # Free-running period without zeitgebers
ENTRAINED_PERIOD_HOURS = 24.0  # Period when entrained to light/dark cycle
MIN_AMPLITUDE = 0.0  # Complete circadian rhythm collapse
MAX_AMPLITUDE = 1.0  # Perfect circadian rhythm strength

# Phase Response Curve parameters (in hours of phase shift per hour of stimulus)
PRC_ADVANCE_MAX = 1.5  # Maximum advance from morning light (hours)
PRC_DELAY_MAX = -2.5  # Maximum delay from evening/night light (hours)
PRC_DEAD_ZONE_START = 12  # Hour when PRC effect minimal (noon)
PRC_DEAD_ZONE_END = 16  # Hour when PRC effect resumes (4 PM)

# Amplitude decay/recovery rates
AMPLITUDE_DECAY_RATE = 0.05  # Per irregular shift (5% amplitude loss)
AMPLITUDE_RECOVERY_RATE = 0.02  # Per regular shift (2% amplitude gain)
AMPLITUDE_RECOVERY_DAYS = 14  # Days of regular schedule for full recovery


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class CircadianOscillator:
    """
    Models an individual's circadian rhythm as a biological oscillator.

    The circadian system is an endogenous ~24-hour oscillator that
    regulates sleep/wake timing, hormone release, and alertness.

    Attributes:
        resident_id: UUID of the resident
        phase: Current circadian phase (0-24 hours, 0 = midnight)
        amplitude: Rhythm strength (0-1, 1 = perfect oscillation)
        period: Natural circadian period in hours (~24.2h)
        last_updated: When oscillator state was last calculated
        chronotype_offset: Individual chronotype offset (negative = morning type)
        entrainment_strength: How strongly entrained to light/dark (0-1)
    """

    resident_id: UUID
    phase: float = 0.0  # Hours (0-24)
    amplitude: float = 1.0  # 0-1
    period: float = NATURAL_PERIOD_HOURS
    last_updated: datetime = field(default_factory=datetime.now)
    chronotype_offset: float = 0.0  # Hours (-2 to +2)
    entrainment_strength: float = 1.0  # 0-1

    def __post_init__(self):
        """Validate oscillator parameters."""
        self.phase = self.phase % 24.0  # Keep phase in [0, 24)
        self.amplitude = max(MIN_AMPLITUDE, min(MAX_AMPLITUDE, self.amplitude))
        if not 22.0 <= self.period <= 26.0:
            logger.warning(f"Unusual circadian period: {self.period}h (typical 24-25h)")

    def compute_phase_shift(
        self,
        shift_start: datetime,
        shift_duration: float,
        shift_type: CircadianShiftType,
    ) -> float:
        """
        Calculate circadian phase shift from a work shift.

        Uses Phase Response Curve (PRC) to determine how shift timing
        affects circadian phase. Morning shifts advance phase, evening/night
        shifts delay phase.

        Args:
            shift_start: When shift begins
            shift_duration: Shift length in hours
            shift_type: Type of shift (day, evening, night)

        Returns:
            Phase shift in hours (positive = advance, negative = delay)

        Example:
            >>> osc = CircadianOscillator(resident_id=UUID("..."))
            >>> shift = datetime(2024, 1, 1, 23, 0)  # 11 PM start
            >>> shift_delta = osc.compute_phase_shift(
            ...     shift, 12.0, CircadianShiftType.NIGHT
            ... )
            >>> print(shift_delta)  # Negative (phase delay)
        """
        shift_hour = shift_start.hour
        midpoint_hour = (shift_hour + shift_duration / 2) % 24

        # Get PRC value at shift midpoint
        prc_value = self._get_prc_value(midpoint_hour)

        # Scale by shift duration and amplitude
        phase_shift = prc_value * shift_duration * self.amplitude

        # Shift type modifiers
        if shift_type == CircadianShiftType.NIGHT:
            phase_shift *= 1.5  # Night shifts have stronger effect
        elif shift_type == CircadianShiftType.SPLIT:
            phase_shift *= 0.5  # Split shifts have weaker but irregular effect

        logger.debug(
            f"Phase shift calculation: shift_hour={shift_hour}, "
            f"midpoint={midpoint_hour:.1f}, prc={prc_value:.2f}, "
            f"duration={shift_duration}h, shift={phase_shift:+.2f}h"
        )

        return phase_shift

    def update_phase(self, time_elapsed: timedelta, phase_shift: float = 0.0):
        """
        Update circadian phase accounting for natural drift and imposed shifts.

        The circadian oscillator has a natural period (~24.2h) that causes
        it to drift relative to the 24-hour day without zeitgeber entrainment.

        Args:
            time_elapsed: Time since last update
            phase_shift: External phase shift from light exposure (hours)
        """
        hours_elapsed = time_elapsed.total_seconds() / 3600

        # Natural progression at intrinsic period
        natural_advance = hours_elapsed * (24.0 / self.period)

        # Apply external phase shift (from PRC)
        total_shift = natural_advance + phase_shift

        # Update phase
        self.phase = (self.phase + total_shift) % 24.0
        self.last_updated = datetime.now()

        logger.debug(
            f"Phase updated: elapsed={hours_elapsed:.1f}h, "
            f"natural={natural_advance:.2f}h, external={phase_shift:+.2f}h, "
            f"new_phase={self.phase:.2f}h"
        )

    def update_amplitude(self, schedule_regularity: float):
        """
        Update circadian amplitude based on schedule regularity.

        Regular schedules strengthen circadian rhythms (increase amplitude).
        Irregular schedules weaken rhythms (decrease amplitude).

        Args:
            schedule_regularity: Measure of schedule consistency (0-1)
                1.0 = perfectly regular
                0.5 = moderately irregular
                0.0 = highly irregular

        Example:
            >>> osc = CircadianOscillator(resident_id=UUID("..."), amplitude=0.8)
            >>> osc.update_amplitude(0.3)  # Irregular schedule
            >>> print(osc.amplitude)  # Decreased (e.g., 0.76)
        """
        if schedule_regularity >= 0.8:
            # Regular schedule: amplitude recovery
            delta = AMPLITUDE_RECOVERY_RATE * (schedule_regularity - 0.8) / 0.2
            self.amplitude = min(MAX_AMPLITUDE, self.amplitude + delta)
        else:
            # Irregular schedule: amplitude decay
            delta = AMPLITUDE_DECAY_RATE * (0.8 - schedule_regularity) / 0.8
            self.amplitude = max(MIN_AMPLITUDE, self.amplitude - delta)

        logger.debug(
            f"Amplitude updated: regularity={schedule_regularity:.2f}, "
            f"new_amplitude={self.amplitude:.3f}"
        )

    def get_current_alertness(self, current_time: datetime) -> float:
        """
        Calculate current alertness based on circadian phase.

        Alertness follows a sinusoidal pattern with peak ~4 hours after
        circadian wake time and trough during circadian night (phase + 22h).

        Args:
            current_time: Time to evaluate alertness

        Returns:
            Alertness score (0-1), modulated by amplitude

        Example:
            >>> osc = CircadianOscillator(resident_id=UUID("..."), phase=6.0)
            >>> alertness = osc.get_current_alertness(
            ...     datetime(2024, 1, 1, 10, 0)  # 10 AM (4h after wake at 6 AM)
            ... )
            >>> print(alertness)  # High (e.g., 0.85)
        """
        # Current clock time
        current_hour = current_time.hour + current_time.minute / 60

        # Phase represents wake time (e.g., phase=6.0 means wake at 6 AM)
        # Peak alertness occurs ~4 hours after wake
        # Trough occurs ~22 hours after wake (2 hours before next wake)
        peak_time = (self.phase + 4.0) % 24.0

        # Calculate hour offset from peak
        hour_offset = current_hour - peak_time

        # Normalize to [-12, 12] range
        while hour_offset > 12:
            hour_offset -= 24
        while hour_offset < -12:
            hour_offset += 24

        # Cosine curve: peak at 0, trough at ±12
        # cos(0) = 1 (peak), cos(π) = -1 (trough)
        base_alertness = 0.5 + 0.5 * math.cos(2 * math.pi * hour_offset / 24.0)

        # Apply amplitude modulation
        # Low amplitude = flattened curve (less variation)
        # High amplitude = full variation
        modulated_alertness = 0.5 + self.amplitude * (base_alertness - 0.5)

        return max(0.0, min(1.0, modulated_alertness))

    def _get_prc_value(self, hour: float) -> float:
        """
        Get Phase Response Curve value for a given hour.

        PRC describes how light exposure at different times shifts
        circadian phase:
        - Morning (6-10 AM): Phase advance (positive)
        - Dead zone (12-4 PM): Minimal effect (~0)
        - Evening/Night (8 PM-2 AM): Phase delay (negative)

        Args:
            hour: Hour of day (0-24)

        Returns:
            PRC value (hours of phase shift per hour of stimulus)
        """
        # Normalize to [0, 24)
        hour = hour % 24.0

        # Dead zone: minimal PRC effect
        if PRC_DEAD_ZONE_START <= hour < PRC_DEAD_ZONE_END:
            return 0.0

        # Morning advance (6-10 AM): positive PRC
        if 6 <= hour < 10:
            # Sinusoidal rise to peak
            t = (hour - 6) / 4  # Normalize to [0, 1]
            return PRC_ADVANCE_MAX * math.sin(math.pi * t)

        # Evening/night delay (8 PM - 2 AM): negative PRC
        if hour >= 20 or hour < 2:
            # Peak delay at midnight
            if hour >= 20:
                t = (hour - 20) / 4  # 8 PM to midnight
            else:
                t = (hour + 4) / 4  # Midnight to 2 AM (continues curve)
            return PRC_DELAY_MAX * math.sin(math.pi * t)

        # Transition zones: linear interpolation
        if 2 <= hour < 6:
            # Delay → advance transition
            t = (hour - 2) / 4
            return PRC_DELAY_MAX * (1 - t)  # Decay to zero
        elif 10 <= hour < 12:
            # Advance → dead zone transition
            t = (hour - 10) / 2
            return PRC_ADVANCE_MAX * (1 - t)
        elif 16 <= hour < 20:
            # Dead zone → delay transition
            t = (hour - 16) / 4
            return PRC_DELAY_MAX * t  # Rise from zero

        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert oscillator to dictionary for API response."""
        return {
            "resident_id": str(self.resident_id),
            "phase": round(self.phase, 2),
            "amplitude": round(self.amplitude, 3),
            "period": round(self.period, 2),
            "last_updated": self.last_updated.isoformat(),
            "chronotype_offset": round(self.chronotype_offset, 2),
            "entrainment_strength": round(self.entrainment_strength, 3),
        }


@dataclass
class CircadianImpact:
    """
    Impact assessment of a schedule on circadian rhythms.

    Quantifies how a schedule affects circadian alignment and
    provides actionable metrics for schedule optimization.

    Attributes:
        resident_id: UUID of resident
        phase_drift: Total circadian phase drift (hours)
        amplitude_change: Change in circadian amplitude (-1 to +1)
        quality_score: Overall circadian quality (0-1)
        misalignment_hours: Hours per week of circadian misalignment
        recovery_days_needed: Days to recover circadian alignment
        quality_level: Categorical quality assessment
        shift_impacts: Per-shift circadian impact details
    """

    resident_id: UUID
    phase_drift: float  # Hours
    amplitude_change: float  # -1 to +1
    quality_score: float  # 0-1
    misalignment_hours: float  # Hours per week
    recovery_days_needed: int
    quality_level: CircadianQualityLevel
    shift_impacts: list[dict] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "resident_id": str(self.resident_id),
            "phase_drift": round(self.phase_drift, 2),
            "amplitude_change": round(self.amplitude_change, 3),
            "quality_score": round(self.quality_score, 3),
            "misalignment_hours": round(self.misalignment_hours, 1),
            "recovery_days_needed": self.recovery_days_needed,
            "quality_level": self.quality_level.value,
            "shift_impacts": self.shift_impacts,
            "analyzed_at": self.analyzed_at.isoformat(),
        }


# =============================================================================
# Circadian Schedule Analyzer
# =============================================================================


class CircadianScheduleAnalyzer:
    """
    Analyzes schedule impact on circadian rhythms.

    Uses circadian oscillator models to evaluate how shift schedules
    affect resident circadian alignment, providing:
    - Phase drift prediction
    - Amplitude degradation tracking
    - Circadian quality scoring
    - Optimization recommendations
    """

    def __init__(self):
        """Initialize circadian schedule analyzer."""
        # Cache of oscillator states per resident
        self._oscillators: dict[UUID, CircadianOscillator] = {}
        logger.info("Initialized CircadianScheduleAnalyzer")

    def get_or_create_oscillator(
        self,
        resident_id: UUID,
        initial_phase: float = 6.0,  # Default: wake at 6 AM
        initial_amplitude: float = 1.0,
    ) -> CircadianOscillator:
        """
        Get existing oscillator or create new one for resident.

        Args:
            resident_id: UUID of resident
            initial_phase: Initial circadian phase (default 6 AM wake)
            initial_amplitude: Initial rhythm strength

        Returns:
            CircadianOscillator instance
        """
        if resident_id not in self._oscillators:
            self._oscillators[resident_id] = CircadianOscillator(
                resident_id=resident_id,
                phase=initial_phase,
                amplitude=initial_amplitude,
            )
            logger.debug(f"Created new oscillator for resident {resident_id}")

        return self._oscillators[resident_id]

    def analyze_schedule_impact(
        self,
        resident_id: UUID,
        schedule: list[dict],  # List of shifts with start time, duration, type
    ) -> CircadianImpact:
        """
        Analyze circadian impact of a schedule.

        Simulates circadian oscillator through schedule to predict
        phase drift, amplitude changes, and overall quality.

        Args:
            resident_id: UUID of resident
            schedule: List of shift dicts with:
                - start_time: datetime
                - duration: float (hours)
                - type: CircadianShiftType

        Returns:
            CircadianImpact assessment

        Example:
            >>> analyzer = CircadianScheduleAnalyzer()
            >>> schedule = [
            ...     {"start_time": datetime(...), "duration": 12, "type": CircadianShiftType.DAY},
            ...     {"start_time": datetime(...), "duration": 12, "type": CircadianShiftType.NIGHT},
            ... ]
            >>> impact = analyzer.analyze_schedule_impact(resident_id, schedule)
            >>> print(impact.quality_score)
        """
        osc = self.get_or_create_oscillator(resident_id)

        # Save initial state
        initial_phase = osc.phase
        initial_amplitude = osc.amplitude

        # Simulate schedule
        shift_impacts = []
        total_misalignment = 0.0
        schedule_regularity_scores = []

        for i, shift in enumerate(schedule):
            start_time = shift["start_time"]
            duration = shift["duration"]
            shift_type = CircadianShiftType(shift["type"])

            # Calculate phase shift from this shift
            phase_shift = osc.compute_phase_shift(start_time, duration, shift_type)

            # Update oscillator phase
            if i > 0:
                prev_shift = schedule[i - 1]
                time_elapsed = start_time - prev_shift["start_time"]
            else:
                time_elapsed = timedelta(hours=0)

            osc.update_phase(time_elapsed, phase_shift)

            # Calculate misalignment for this shift
            optimal_phase = 10.0  # Optimal wake time: 10 AM circadian phase
            misalignment = abs((osc.phase - optimal_phase + 12) % 24 - 12)
            total_misalignment += misalignment

            # Track shift regularity (for amplitude calculation)
            if i > 0:
                prev_type = CircadianShiftType(schedule[i - 1]["type"])
                regularity = 1.0 if shift_type == prev_type else 0.3
                schedule_regularity_scores.append(regularity)

            shift_impacts.append(
                {
                    "shift_index": i,
                    "start_time": start_time.isoformat(),
                    "type": shift_type.value,
                    "phase_shift": round(phase_shift, 2),
                    "phase_after": round(osc.phase, 2),
                    "misalignment": round(misalignment, 2),
                }
            )

        # Calculate overall schedule regularity
        if schedule_regularity_scores:
            avg_regularity = sum(schedule_regularity_scores) / len(
                schedule_regularity_scores
            )
        else:
            avg_regularity = 1.0  # Single shift = perfectly regular

        # Update amplitude based on regularity
        osc.update_amplitude(avg_regularity)

        # Calculate impact metrics
        phase_drift = (
            osc.phase - initial_phase + 12
        ) % 24 - 12  # Normalized to [-12, 12]
        amplitude_change = osc.amplitude - initial_amplitude
        avg_misalignment = total_misalignment / len(schedule) if schedule else 0

        # Calculate quality score (0-1)
        quality_score = self._compute_quality_score(
            phase_drift, amplitude_change, avg_misalignment
        )

        # Determine quality level
        quality_level = self._classify_quality(quality_score)

        # Estimate recovery time
        recovery_days = self._estimate_recovery_days(abs(phase_drift), amplitude_change)

        impact = CircadianImpact(
            resident_id=resident_id,
            phase_drift=phase_drift,
            amplitude_change=amplitude_change,
            quality_score=quality_score,
            misalignment_hours=avg_misalignment,
            recovery_days_needed=recovery_days,
            quality_level=quality_level,
            shift_impacts=shift_impacts,
        )

        logger.info(
            f"Circadian impact analysis complete: "
            f"resident={resident_id}, quality={quality_score:.2f}, "
            f"phase_drift={phase_drift:+.2f}h, quality_level={quality_level}"
        )

        return impact

    def compute_circadian_quality_score(self, schedule: list[dict]) -> float:
        """
        Compute overall circadian quality score for a schedule.

        Higher scores indicate better circadian alignment.
        Used as optimization objective in schedule generation.

        Args:
            schedule: List of shifts (all residents combined)

        Returns:
            Quality score (0-1), 1.0 = optimal circadian alignment

        Example:
            >>> analyzer = CircadianScheduleAnalyzer()
            >>> score = analyzer.compute_circadian_quality_score(schedule)
            >>> print(score)  # 0.82
        """
        if not schedule:
            return 1.0

        # Group shifts by resident
        shifts_by_resident: dict[UUID, list] = {}
        for shift in schedule:
            resident_id = shift.get("resident_id")
            if resident_id:
                if resident_id not in shifts_by_resident:
                    shifts_by_resident[resident_id] = []
                shifts_by_resident[resident_id].append(shift)

        # Analyze each resident's schedule
        quality_scores = []
        for resident_id, resident_shifts in shifts_by_resident.items():
            impact = self.analyze_schedule_impact(resident_id, resident_shifts)
            quality_scores.append(impact.quality_score)

        # Average across all residents
        avg_quality = (
            sum(quality_scores) / len(quality_scores) if quality_scores else 1.0
        )

        logger.debug(
            f"Schedule circadian quality: {avg_quality:.3f} "
            f"(n={len(quality_scores)} residents)"
        )

        return avg_quality

    def predict_burnout_risk_from_circadian(self, amplitude: float) -> float:
        """
        Predict burnout risk from circadian amplitude degradation.

        Low circadian amplitude indicates chronic schedule disruption,
        which correlates with burnout risk.

        Args:
            amplitude: Current circadian amplitude (0-1)

        Returns:
            Burnout risk score (0-1), 1.0 = high risk

        Example:
            >>> analyzer = CircadianScheduleAnalyzer()
            >>> risk = analyzer.predict_burnout_risk_from_circadian(0.4)
            >>> print(risk)  # 0.6 (elevated risk)
        """
        # Inverse relationship: lower amplitude = higher risk
        # Sigmoid curve for smooth transition
        risk = 1.0 - amplitude

        # Apply sigmoid for more realistic risk curve
        # Risk accelerates below amplitude 0.5
        if amplitude < 0.5:
            risk = 1.0 / (1.0 + math.exp(-10 * (0.5 - amplitude)))
        else:
            risk = 0.5 * (1.0 - amplitude)

        return max(0.0, min(1.0, risk))

    def _compute_quality_score(
        self,
        phase_drift: float,
        amplitude_change: float,
        avg_misalignment: float,
    ) -> float:
        """
        Compute circadian quality score from components.

        Weights:
        - Phase drift: 40% (large drifts are problematic)
        - Amplitude change: 30% (degradation is concerning)
        - Misalignment: 30% (chronic misalignment impairs performance)

        Args:
            phase_drift: Total phase drift (hours)
            amplitude_change: Change in amplitude (-1 to +1)
            avg_misalignment: Average misalignment (hours)

        Returns:
            Quality score (0-1)
        """
        # Phase drift penalty (0-1, 0 = large drift)
        phase_score = max(0, 1.0 - abs(phase_drift) / 6.0)  # 6h drift = score 0

        # Amplitude penalty (0-1, 0 = large degradation)
        amp_score = 1.0 if amplitude_change >= 0 else max(0, 1.0 + amplitude_change)

        # Misalignment penalty (0-1, 0 = large misalignment)
        misalign_score = max(0, 1.0 - avg_misalignment / 6.0)  # 6h misalign = score 0

        # Weighted combination
        quality = 0.4 * phase_score + 0.3 * amp_score + 0.3 * misalign_score

        return max(0.0, min(1.0, quality))

    def _classify_quality(self, quality_score: float) -> CircadianQualityLevel:
        """Classify quality score into categorical level."""
        if quality_score >= 0.85:
            return CircadianQualityLevel.EXCELLENT
        elif quality_score >= 0.70:
            return CircadianQualityLevel.GOOD
        elif quality_score >= 0.55:
            return CircadianQualityLevel.FAIR
        elif quality_score >= 0.40:
            return CircadianQualityLevel.POOR
        else:
            return CircadianQualityLevel.CRITICAL

    def _estimate_recovery_days(
        self, abs_phase_drift: float, amplitude_change: float
    ) -> int:
        """
        Estimate days needed to recover circadian alignment.

        Recovery time depends on:
        - Phase drift magnitude (1 day per hour of drift)
        - Amplitude degradation (14 days for full amplitude recovery)

        Args:
            abs_phase_drift: Absolute phase drift (hours)
            amplitude_change: Change in amplitude

        Returns:
            Estimated recovery days
        """
        # Phase recovery: ~1 day per hour of drift
        phase_recovery_days = abs_phase_drift

        # Amplitude recovery: up to 14 days for full recovery
        if amplitude_change < 0:
            amp_recovery_days = abs(amplitude_change) * AMPLITUDE_RECOVERY_DAYS
        else:
            amp_recovery_days = 0

        # Take maximum (recovery processes can overlap partially)
        total_recovery = max(phase_recovery_days, amp_recovery_days)

        return int(math.ceil(total_recovery))

    def reset_oscillator(self, resident_id: UUID):
        """
        Reset oscillator to default state.

        Useful for testing or after extended time off.

        Args:
            resident_id: UUID of resident
        """
        if resident_id in self._oscillators:
            del self._oscillators[resident_id]
            logger.info(f"Reset oscillator for resident {resident_id}")

    def get_oscillator_summary(self) -> dict[str, Any]:
        """Get summary of all tracked oscillators."""
        return {
            "total_residents": len(self._oscillators),
            "oscillators": [osc.to_dict() for osc in self._oscillators.values()],
        }
