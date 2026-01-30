"""
Sleep Debt Accumulation Model with Circadian Rhythm Integration.

Implements the Two-Process Model of sleep regulation (Borbély, 1982):
- Process S (Sleep Homeostasis): Sleep pressure that builds during wakefulness
- Process C (Circadian): 24-hour biological clock modulating alertness

Sleep debt accumulates when:
1. Total sleep < baseline requirement (typically 7-8 hours)
2. Sleep timing misaligned with circadian phase
3. Sleep fragmented or poor quality

Key Concepts:
- Sleep debt is cumulative and requires recovery sleep to repay
- Circadian nadir (2-6 AM) compounds fatigue effects
- Night shift workers accumulate debt faster due to circadian misalignment
- Recovery requires ~1.5 hours extra sleep per hour of debt (partial recovery)

Medical Residency Application:
- Tracks cumulative sleep debt over rotation cycles
- Identifies circadian phase for shift assignments
- Predicts performance degradation from sleep debt
- Informs scheduling decisions to prevent chronic debt accumulation

References:
- Borbély, A.A. (1982). A two process model of sleep regulation.
- Van Dongen, H.P. et al. (2003). The cumulative cost of additional wakefulness.
- Åkerstedt, T. & Folkard, S. (1997). The three-process model of alertness.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


class CircadianPhase(str, Enum):
    """
    Circadian rhythm phases affecting alertness and performance.

    Based on the 24-hour biological clock with distinct phases
    of alertness and vulnerability.
    """

    NADIR = "nadir"  # 2-6 AM: Lowest alertness, highest fatigue
    EARLY_MORNING = "early_morning"  # 6-9 AM: Increasing alertness
    MORNING_PEAK = "morning_peak"  # 9-12 PM: Peak alertness
    POST_LUNCH = "post_lunch"  # 12-3 PM: Post-prandial dip
    AFTERNOON = "afternoon"  # 3-6 PM: Secondary peak
    EVENING = "evening"  # 6-9 PM: Declining alertness
    NIGHT = "night"  # 9 PM-2 AM: Pre-sleep decline

    # Circadian alertness multipliers (1.0 = baseline)
    # Values < 1.0 indicate reduced alertness


CIRCADIAN_MULTIPLIERS = {
    CircadianPhase.NADIR: 0.6,  # Significant impairment
    CircadianPhase.EARLY_MORNING: 0.85,
    CircadianPhase.MORNING_PEAK: 1.0,
    CircadianPhase.POST_LUNCH: 0.9,
    CircadianPhase.AFTERNOON: 0.95,
    CircadianPhase.EVENING: 0.9,
    CircadianPhase.NIGHT: 0.75,
}


@dataclass
class SleepOpportunity:
    """
    Represents a sleep period for debt calculation.

    Captures both objective sleep metrics and quality factors
    that affect actual recovery.

    Attributes:
        start_time: When sleep period began
        end_time: When sleep period ended
        duration_hours: Total sleep duration
        quality_factor: Sleep quality (0.0-1.0, 1.0 = perfect)
        is_primary_sleep: Main sleep period vs. nap
        circadian_aligned: Whether sleep was at circadian-appropriate time
        interruptions: Number of interruptions during sleep
        environment_factor: Sleep environment quality (0.0-1.0)
    """

    start_time: datetime
    end_time: datetime
    duration_hours: float = field(init=False)
    quality_factor: float = 1.0
    is_primary_sleep: bool = True
    circadian_aligned: bool = True
    interruptions: int = 0
    environment_factor: float = 1.0

    def __post_init__(self) -> None:
        """Calculate duration from start and end times."""
        delta = self.end_time - self.start_time
        self.duration_hours = max(0, delta.total_seconds() / 3600)

    @property
    def effective_sleep_hours(self) -> float:
        """
        Calculate effective sleep accounting for quality factors.

        Returns sleep hours adjusted for:
        - Sleep quality
        - Circadian alignment
        - Sleep fragmentation
        - Environment quality
        """
        base = self.duration_hours

        # Quality adjustment
        base *= self.quality_factor

        # Circadian misalignment reduces recovery value by 20%
        if not self.circadian_aligned:
            base *= 0.8

            # Each interruption reduces value by 5%
        interruption_penalty = 1 - (self.interruptions * 0.05)
        base *= max(0.5, interruption_penalty)

        # Environment adjustment
        base *= self.environment_factor

        return base


@dataclass
class SleepDebtState:
    """
    Current sleep debt state for a resident.

    Tracks cumulative sleep debt and recovery trajectory.

    Attributes:
        resident_id: UUID of the resident
        current_debt_hours: Total accumulated sleep debt
        last_updated: When state was last calculated
        consecutive_deficit_days: Days with < 7 hours sleep
        recovery_sleep_needed: Hours of extra sleep to repay debt
        chronic_debt: Whether debt has been sustained > 5 days
        debt_severity: Severity classification
        impairment_equivalent_bac: Cognitive impairment BAC equivalent
    """

    resident_id: UUID
    current_debt_hours: float
    last_updated: datetime
    consecutive_deficit_days: int = 0
    recovery_sleep_needed: float = 0.0
    chronic_debt: bool = False
    debt_severity: str = "none"
    impairment_equivalent_bac: float = 0.0

    def to_dict(self) -> dict:
        """Convert state to dictionary for API response."""
        return {
            "resident_id": str(self.resident_id),
            "current_debt_hours": round(self.current_debt_hours, 1),
            "last_updated": self.last_updated.isoformat(),
            "consecutive_deficit_days": self.consecutive_deficit_days,
            "recovery_sleep_needed": round(self.recovery_sleep_needed, 1),
            "chronic_debt": self.chronic_debt,
            "debt_severity": self.debt_severity,
            "impairment_equivalent_bac": round(self.impairment_equivalent_bac, 3),
        }


class SleepDebtModel:
    """
    Sleep debt accumulation and recovery model.

    Implements sleep homeostasis (Process S) with circadian modulation
    for accurate fatigue prediction in medical residency scheduling.

    Key Features:
    - Cumulative debt tracking across days
    - Circadian-aware recovery calculation
    - Impairment equivalence (BAC mapping)
    - Recovery time estimation

    Constants:
        BASELINE_SLEEP_NEED: Default daily sleep requirement (hours)
        MAX_DEBT_HOURS: Maximum trackable debt before saturation
        DEBT_RECOVERY_RATIO: Extra sleep needed per hour of debt
        CHRONIC_THRESHOLD_DAYS: Days of deficit before chronic classification
    """

    BASELINE_SLEEP_NEED: float = 7.5  # Average adult requirement
    MAX_DEBT_HOURS: float = 40.0  # Beyond this, cumulative tracking less reliable
    DEBT_RECOVERY_RATIO: float = 1.5  # 1.5 hours extra per hour of debt
    CHRONIC_THRESHOLD_DAYS: int = 5

    def __init__(
        self,
        baseline_sleep_need: float = BASELINE_SLEEP_NEED,
        individual_variability: float = 0.0,
    ) -> None:
        """
        Initialize sleep debt model.

        Args:
            baseline_sleep_need: Individual's sleep requirement
            individual_variability: Adjustment for individual differences (-1 to +1)
        """
        self.baseline_sleep_need = baseline_sleep_need + individual_variability
        self._current_debt: dict[UUID, float] = {}  # In-memory cache
        self._deficit_days: dict[UUID, int] = {}

    def calculate_daily_debt(
        self,
        sleep_opportunities: list[SleepOpportunity],
    ) -> float:
        """
        Calculate sleep debt accumulated in a 24-hour period.

        Args:
            sleep_opportunities: List of sleep periods in the day

        Returns:
            Net sleep debt change (positive = debt increased)

        Example:
            >>> model = SleepDebtModel()
            >>> sleep = SleepOpportunity(
            ...     start_time=datetime(2024, 1, 1, 23, 0),
            ...     end_time=datetime(2024, 1, 2, 4, 30),  # Only 5.5 hours
            ...     quality_factor=0.9
            ... )
            >>> debt = model.calculate_daily_debt([sleep])
            >>> print(debt)  # ~2.5 hours (7.5 - 5.5 * 0.9)
        """
        total_effective_sleep = sum(
            s.effective_sleep_hours for s in sleep_opportunities
        )

        # Debt is the difference from baseline
        daily_debt = self.baseline_sleep_need - total_effective_sleep

        logger.debug(
            f"Daily debt calculation: "
            f"effective_sleep={total_effective_sleep:.1f}h, "
            f"baseline={self.baseline_sleep_need}h, "
            f"debt_change={daily_debt:+.1f}h"
        )

        return daily_debt

    def update_cumulative_debt(
        self,
        resident_id: UUID,
        daily_debt_change: float,
        natural_recovery: bool = True,
    ) -> SleepDebtState:
        """
        Update cumulative sleep debt for a resident.

        Debt accumulates day over day, with some natural recovery
        during adequate sleep periods.

        Args:
            resident_id: UUID of the resident
            daily_debt_change: Change in debt (positive = more debt)
            natural_recovery: Apply modest recovery during adequate sleep

        Returns:
            Updated SleepDebtState
        """
        current_debt = self._current_debt.get(resident_id, 0.0)
        deficit_days = self._deficit_days.get(resident_id, 0)

        # Update debt
        new_debt = current_debt + daily_debt_change

        # Track consecutive deficit days
        if daily_debt_change > 0:
            deficit_days += 1
        else:
            # If sleeping adequately, count toward recovery
            if natural_recovery and daily_debt_change < -0.5:
                # Reduce accumulated debt with recovery ratio
                recovery_applied = abs(daily_debt_change) / self.DEBT_RECOVERY_RATIO
                new_debt = max(0, current_debt - recovery_applied)
            deficit_days = 0

            # Clamp to valid range
        new_debt = max(0, min(new_debt, self.MAX_DEBT_HOURS))

        # Update caches
        self._current_debt[resident_id] = new_debt
        self._deficit_days[resident_id] = deficit_days

        # Classify severity
        severity = self._classify_debt_severity(new_debt)
        chronic = deficit_days >= self.CHRONIC_THRESHOLD_DAYS
        recovery_needed = new_debt * self.DEBT_RECOVERY_RATIO
        impairment_bac = self._calculate_impairment_equivalent(new_debt)

        state = SleepDebtState(
            resident_id=resident_id,
            current_debt_hours=new_debt,
            last_updated=datetime.utcnow(),
            consecutive_deficit_days=deficit_days,
            recovery_sleep_needed=recovery_needed,
            chronic_debt=chronic,
            debt_severity=severity,
            impairment_equivalent_bac=impairment_bac,
        )

        logger.info(
            f"Sleep debt updated for {resident_id}: "
            f"debt={new_debt:.1f}h, severity={severity}, "
            f"chronic={chronic}, BAC_equiv={impairment_bac:.3f}"
        )

        return state

    def get_circadian_phase(self, dt: datetime) -> CircadianPhase:
        """
        Determine circadian phase for a given datetime.

        Uses standard circadian rhythm assuming normal sleep schedule.
        For shift workers, phase may be shifted.

        Args:
            dt: Datetime to evaluate

        Returns:
            Current CircadianPhase
        """
        hour = dt.hour

        if 2 <= hour < 6:
            return CircadianPhase.NADIR
        elif 6 <= hour < 9:
            return CircadianPhase.EARLY_MORNING
        elif 9 <= hour < 12:
            return CircadianPhase.MORNING_PEAK
        elif 12 <= hour < 15:
            return CircadianPhase.POST_LUNCH
        elif 15 <= hour < 18:
            return CircadianPhase.AFTERNOON
        elif 18 <= hour < 21:
            return CircadianPhase.EVENING
        else:
            return CircadianPhase.NIGHT

    def get_circadian_multiplier(self, dt: datetime) -> float:
        """
        Get circadian alertness multiplier for a given time.

        Multiplier represents relative alertness compared to
        peak (morning). Values < 1.0 indicate reduced alertness.

        Args:
            dt: Datetime to evaluate

        Returns:
            Alertness multiplier (0.6 - 1.0)

        Example:
            >>> model = SleepDebtModel()
            >>> # At 4 AM (nadir)
            >>> mult = model.get_circadian_multiplier(
            ...     datetime(2024, 1, 1, 4, 0)
            ... )
            >>> print(mult)  # 0.6
        """
        phase = self.get_circadian_phase(dt)
        return CIRCADIAN_MULTIPLIERS[phase]

    def calculate_circadian_curve(
        self,
        start_time: datetime,
        duration_hours: int = 24,
    ) -> list[dict]:
        """
        Generate circadian alertness curve for visualization.

        Creates hourly data points showing circadian rhythm
        variation in alertness.

        Args:
            start_time: Start of the curve
            duration_hours: Hours to generate

        Returns:
            List of dicts with time and alertness data
        """
        curve = []
        current = start_time

        for i in range(duration_hours):
            phase = self.get_circadian_phase(current)
            multiplier = CIRCADIAN_MULTIPLIERS[phase]

            curve.append(
                {
                    "time": current.isoformat(),
                    "hour": current.hour,
                    "phase": phase.value,
                    "phase_name": phase.name,
                    "alertness_multiplier": multiplier,
                    "alertness_percent": int(multiplier * 100),
                }
            )

            current += timedelta(hours=1)

        return curve

    def predict_debt_trajectory(
        self,
        resident_id: UUID,
        planned_sleep_hours: list[float],
        start_debt: float | None = None,
    ) -> list[dict]:
        """
        Predict sleep debt trajectory over future days.

        Projects how debt will change given planned sleep hours.
        Useful for schedule optimization.

        Args:
            resident_id: UUID of resident
            planned_sleep_hours: List of planned sleep hours per day
            start_debt: Starting debt (None = use current)

        Returns:
            List of daily debt predictions

        Example:
            >>> model = SleepDebtModel()
            >>> trajectory = model.predict_debt_trajectory(
            ...     resident_id=UUID("..."),
            ...     planned_sleep_hours=[6.0, 5.5, 7.0, 9.0, 9.0, 8.0, 7.5],
            ...     start_debt=10.0
            ... )
            >>> # Shows debt increasing then recovering
        """
        if start_debt is None:
            current_debt = self._current_debt.get(resident_id, 0.0)
        else:
            current_debt = start_debt

        trajectory = []
        deficit_days = 0

        for day, sleep_hours in enumerate(planned_sleep_hours):
            # Calculate daily change
            daily_change = self.baseline_sleep_need - sleep_hours

            # Update cumulative debt
            if daily_change > 0:
                current_debt += daily_change
                deficit_days += 1
            else:
                # Recovery during adequate sleep
                recovery = abs(daily_change) / self.DEBT_RECOVERY_RATIO
                current_debt = max(0, current_debt - recovery)
                deficit_days = 0

            current_debt = min(current_debt, self.MAX_DEBT_HOURS)

            severity = self._classify_debt_severity(current_debt)
            impairment = self._calculate_impairment_equivalent(current_debt)

            trajectory.append(
                {
                    "day": day + 1,
                    "planned_sleep_hours": sleep_hours,
                    "debt_change": round(daily_change, 1),
                    "cumulative_debt": round(current_debt, 1),
                    "severity": severity,
                    "impairment_bac": round(impairment, 3),
                    "deficit_days": deficit_days,
                }
            )

        return trajectory

    def estimate_recovery_time(
        self,
        current_debt: float,
        recovery_sleep_per_night: float = 9.0,
    ) -> int:
        """
        Estimate nights needed to fully recover from sleep debt.

        Args:
            current_debt: Current sleep debt hours
            recovery_sleep_per_night: Planned sleep during recovery

        Returns:
            Estimated nights to full recovery

        Example:
            >>> model = SleepDebtModel()
            >>> nights = model.estimate_recovery_time(15.0, 9.0)
            >>> print(nights)  # ~15 nights
        """
        if current_debt <= 0:
            return 0

            # Extra sleep per night above baseline
        extra_per_night = recovery_sleep_per_night - self.baseline_sleep_need

        if extra_per_night <= 0:
            return -1  # Cannot recover without extra sleep

            # Recovery per night (accounting for efficiency)
        recovery_per_night = extra_per_night / self.DEBT_RECOVERY_RATIO

        nights = math.ceil(current_debt / recovery_per_night)

        logger.debug(
            f"Recovery estimate: debt={current_debt}h, "
            f"extra/night={extra_per_night}h, "
            f"recovery/night={recovery_per_night:.1f}h, "
            f"nights_needed={nights}"
        )

        return nights

    def _classify_debt_severity(self, debt_hours: float) -> str:
        """Classify sleep debt severity."""
        if debt_hours < 2:
            return "none"
        elif debt_hours < 5:
            return "mild"
        elif debt_hours < 10:
            return "moderate"
        elif debt_hours < 20:
            return "severe"
        else:
            return "critical"

    def _calculate_impairment_equivalent(self, debt_hours: float) -> float:
        """
        Calculate cognitive impairment as blood alcohol equivalent.

        Research shows sleep debt impairs cognition similarly to alcohol:
        - 17-19 hours awake ≈ 0.05% BAC
        - 24 hours awake ≈ 0.10% BAC

        We extend this to cumulative debt:
        - 5 hours debt ≈ 0.02% BAC
        - 10 hours debt ≈ 0.05% BAC
        - 20 hours debt ≈ 0.10% BAC

        Args:
            debt_hours: Current sleep debt

        Returns:
            Approximate BAC equivalence
        """
        # Linear approximation: 0.005 BAC per hour of debt
        bac = debt_hours * 0.005

        # Cap at 0.15 (severe impairment)
        return min(bac, 0.15)


def get_circadian_phases_info() -> list[dict]:
    """
    Get all circadian phases with descriptions for UI display.

    Returns:
        List of phase information dicts
    """
    return [
        {
            "phase": phase.value,
            "name": phase.name,
            "time_range": _get_phase_time_range(phase),
            "alertness_multiplier": CIRCADIAN_MULTIPLIERS[phase],
            "description": _get_phase_description(phase),
        }
        for phase in CircadianPhase
    ]


def _get_phase_time_range(phase: CircadianPhase) -> str:
    """Get time range string for a circadian phase."""
    ranges = {
        CircadianPhase.NADIR: "2:00 AM - 6:00 AM",
        CircadianPhase.EARLY_MORNING: "6:00 AM - 9:00 AM",
        CircadianPhase.MORNING_PEAK: "9:00 AM - 12:00 PM",
        CircadianPhase.POST_LUNCH: "12:00 PM - 3:00 PM",
        CircadianPhase.AFTERNOON: "3:00 PM - 6:00 PM",
        CircadianPhase.EVENING: "6:00 PM - 9:00 PM",
        CircadianPhase.NIGHT: "9:00 PM - 2:00 AM",
    }
    return ranges.get(phase, "Unknown")


def _get_phase_description(phase: CircadianPhase) -> str:
    """Get description for a circadian phase."""
    descriptions = {
        CircadianPhase.NADIR: (
            "Biological low point. Highest fatigue vulnerability. "
            "Avoid high-risk procedures if possible."
        ),
        CircadianPhase.EARLY_MORNING: (
            "Waking transition. Alertness increasing but not at peak. "
            "Good for routine tasks."
        ),
        CircadianPhase.MORNING_PEAK: (
            "Peak alertness and cognitive performance. "
            "Ideal for complex decisions and procedures."
        ),
        CircadianPhase.POST_LUNCH: (
            "Post-prandial dip. Modest reduction in alertness. "
            "Normal for most clinical work."
        ),
        CircadianPhase.AFTERNOON: (
            "Secondary alertness peak. Good for sustained attention tasks."
        ),
        CircadianPhase.EVENING: (
            "Declining alertness as body prepares for sleep. Adequate for routine work."
        ),
        CircadianPhase.NIGHT: (
            "Pre-sleep decline. Reduced cognitive performance. "
            "Night shift workers adapt over 3-5 days."
        ),
    }
    return descriptions.get(phase, "Unknown phase")
