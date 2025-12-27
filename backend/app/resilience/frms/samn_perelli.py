"""
Samn-Perelli Fatigue Scale Implementation.

The Samn-Perelli (SP) fatigue scale was developed at the USAF School of
Aerospace Medicine (Brooks AFB, TX) by Samn & Perelli (1982).

It is a 7-point Likert-type scale ranging from:
- 1 = Fully alert, wide awake, extremely peppy
- 7 = Completely exhausted, unable to function effectively

Aviation Safety Thresholds (per Samn & Perelli):
- Levels 1-4: Safe for flying duties
- Level 5: Moderate fatigue, performance impairment possible
- Level 6: Severe fatigue, duties permissible but not recommended
- Level 7: Complete exhaustion, duties not permitted

Medical Residency Adaptation:
- Mapped to clinical duty safety requirements
- Integrated with ACGME work hour monitoring
- Provides objective thresholds for schedule modifications

References:
- Samn, S.W. & Perelli, L.P. (1982). Estimating aircrew fatigue: A technique
  with implications for airlift operations. USAF SAM Report No. 82-21.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from typing import Optional
from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


class SamnPerelliLevel(IntEnum):
    """
    Samn-Perelli 7-level fatigue scale.

    Each level has operational implications for medical duty safety.
    """

    FULLY_ALERT = 1  # Fully alert, wide awake, extremely peppy
    VERY_LIVELY = 2  # Very lively, responsive, but not at peak
    OKAY = 3  # Okay, somewhat fresh
    A_LITTLE_TIRED = 4  # A little tired, less than fresh
    MODERATELY_TIRED = 5  # Moderately tired, let down
    EXTREMELY_TIRED = 6  # Extremely tired, very difficult to concentrate
    EXHAUSTED = 7  # Completely exhausted, unable to function effectively


# Level descriptions for UI display
LEVEL_DESCRIPTIONS = {
    SamnPerelliLevel.FULLY_ALERT: "Fully alert, wide awake, extremely peppy",
    SamnPerelliLevel.VERY_LIVELY: "Very lively, responsive, but not at peak",
    SamnPerelliLevel.OKAY: "Okay, somewhat fresh",
    SamnPerelliLevel.A_LITTLE_TIRED: "A little tired, less than fresh",
    SamnPerelliLevel.MODERATELY_TIRED: "Moderately tired, let down",
    SamnPerelliLevel.EXTREMELY_TIRED: (
        "Extremely tired, very difficult to concentrate"
    ),
    SamnPerelliLevel.EXHAUSTED: "Completely exhausted, unable to function effectively",
}

# Clinical duty safety thresholds
DUTY_THRESHOLDS = {
    "critical_care": SamnPerelliLevel.A_LITTLE_TIRED,  # Max level 4 for ICU/ER
    "procedures": SamnPerelliLevel.OKAY,  # Max level 3 for procedures
    "inpatient": SamnPerelliLevel.MODERATELY_TIRED,  # Max level 5 for wards
    "outpatient": SamnPerelliLevel.MODERATELY_TIRED,  # Max level 5 for clinic
    "education": SamnPerelliLevel.EXTREMELY_TIRED,  # Max level 6 for conferences
    "administrative": SamnPerelliLevel.EXTREMELY_TIRED,  # Max level 6 for admin
}


@dataclass
class SamnPerelliAssessment:
    """
    Complete Samn-Perelli fatigue assessment.

    Captures both subjective rating and objective context for
    comprehensive fatigue risk evaluation.

    Attributes:
        resident_id: UUID of the assessed resident
        level: Samn-Perelli fatigue level (1-7)
        description: Human-readable description of the level
        assessed_at: Timestamp of assessment
        is_self_reported: Whether this was self-reported vs. predicted
        context: Additional context (shift info, time of day, etc.)
        safe_for_duty: Whether resident is safe for clinical duty
        duty_restrictions: List of duties that should be avoided
        recommended_rest_hours: Suggested rest before next shift
        notes: Optional notes from the assessment
    """

    resident_id: UUID
    level: SamnPerelliLevel
    description: str
    assessed_at: datetime
    is_self_reported: bool = False
    context: Optional[dict] = None
    safe_for_duty: bool = True
    duty_restrictions: Optional[list[str]] = None
    recommended_rest_hours: Optional[float] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert assessment to dictionary for API response."""
        return {
            "resident_id": str(self.resident_id),
            "level": self.level.value,
            "level_name": self.level.name,
            "description": self.description,
            "assessed_at": self.assessed_at.isoformat(),
            "is_self_reported": self.is_self_reported,
            "context": self.context,
            "safe_for_duty": self.safe_for_duty,
            "duty_restrictions": self.duty_restrictions,
            "recommended_rest_hours": self.recommended_rest_hours,
            "notes": self.notes,
        }


def assess_fatigue_level(
    level: int,
    resident_id: UUID,
    is_self_reported: bool = False,
    context: Optional[dict] = None,
    notes: Optional[str] = None,
) -> SamnPerelliAssessment:
    """
    Create a Samn-Perelli fatigue assessment from a level rating.

    Validates the level and derives safety implications based on
    aviation-adapted thresholds for medical duty.

    Args:
        level: Fatigue level (1-7)
        resident_id: UUID of the resident
        is_self_reported: Whether this is a self-assessment
        context: Optional context dict (shift_type, hours_worked, etc.)
        notes: Optional free-text notes

    Returns:
        SamnPerelliAssessment with derived safety recommendations

    Raises:
        ValueError: If level is not in valid range (1-7)

    Example:
        >>> assessment = assess_fatigue_level(
        ...     level=5,
        ...     resident_id=UUID("..."),
        ...     is_self_reported=True,
        ...     context={"shift_type": "night", "hours_worked": 20}
        ... )
        >>> print(assessment.safe_for_duty)  # True but with restrictions
        >>> print(assessment.duty_restrictions)  # ["critical_care", "procedures"]
    """
    # Validate level
    if level < 1 or level > 7:
        raise ValueError(f"Samn-Perelli level must be 1-7, got {level}")

    sp_level = SamnPerelliLevel(level)
    description = LEVEL_DESCRIPTIONS[sp_level]

    # Determine safety implications
    safe_for_duty = sp_level <= SamnPerelliLevel.EXTREMELY_TIRED
    duty_restrictions = []

    # Check against duty-specific thresholds
    for duty_type, max_level in DUTY_THRESHOLDS.items():
        if sp_level > max_level:
            duty_restrictions.append(duty_type)

    # Calculate recommended rest based on level
    rest_hours = _calculate_recommended_rest(sp_level)

    assessment = SamnPerelliAssessment(
        resident_id=resident_id,
        level=sp_level,
        description=description,
        assessed_at=datetime.utcnow(),
        is_self_reported=is_self_reported,
        context=context,
        safe_for_duty=safe_for_duty,
        duty_restrictions=duty_restrictions if duty_restrictions else None,
        recommended_rest_hours=rest_hours,
        notes=notes,
    )

    logger.info(
        f"Fatigue assessment for {resident_id}: "
        f"SP-{level} ({sp_level.name}), safe={safe_for_duty}, "
        f"restrictions={duty_restrictions}"
    )

    return assessment


def is_safe_for_duty(
    level: SamnPerelliLevel,
    duty_type: str = "inpatient",
) -> tuple[bool, str]:
    """
    Check if a fatigue level is safe for a specific duty type.

    Uses aviation-adapted thresholds for medical residency duties.

    Args:
        level: Samn-Perelli fatigue level
        duty_type: Type of clinical duty (critical_care, procedures, etc.)

    Returns:
        Tuple of (is_safe, reason)

    Example:
        >>> safe, reason = is_safe_for_duty(SamnPerelliLevel.MODERATELY_TIRED, "procedures")
        >>> print(safe)  # False
        >>> print(reason)  # "Level 5 exceeds threshold of 3 for procedures"
    """
    threshold = DUTY_THRESHOLDS.get(duty_type, SamnPerelliLevel.MODERATELY_TIRED)

    if level <= threshold:
        return True, f"Level {level.value} within threshold of {threshold.value} for {duty_type}"
    else:
        return False, f"Level {level.value} exceeds threshold of {threshold.value} for {duty_type}"


def _calculate_recommended_rest(level: SamnPerelliLevel) -> float:
    """
    Calculate recommended rest hours based on fatigue level.

    Based on sleep science:
    - Light fatigue: 8 hours normal sleep
    - Moderate fatigue: 8-10 hours with buffer
    - Severe fatigue: 10-12 hours recovery sleep
    - Exhaustion: 12+ hours extended recovery

    Args:
        level: Samn-Perelli fatigue level

    Returns:
        Recommended rest hours before next duty
    """
    rest_hours = {
        SamnPerelliLevel.FULLY_ALERT: 8.0,
        SamnPerelliLevel.VERY_LIVELY: 8.0,
        SamnPerelliLevel.OKAY: 8.0,
        SamnPerelliLevel.A_LITTLE_TIRED: 9.0,
        SamnPerelliLevel.MODERATELY_TIRED: 10.0,
        SamnPerelliLevel.EXTREMELY_TIRED: 11.0,
        SamnPerelliLevel.EXHAUSTED: 12.0,
    }
    return rest_hours.get(level, 10.0)


def estimate_level_from_factors(
    hours_awake: float,
    hours_worked_24h: float,
    consecutive_night_shifts: int = 0,
    time_of_day_hour: int = 12,
    prior_sleep_hours: float = 7.0,
) -> SamnPerelliLevel:
    """
    Estimate Samn-Perelli level from objective factors.

    Uses a weighted model based on fatigue science to predict
    subjective fatigue level from measurable factors.

    Args:
        hours_awake: Hours since last sleep period
        hours_worked_24h: Work hours in last 24 hours
        consecutive_night_shifts: Number of consecutive night shifts
        time_of_day_hour: Current hour (0-23) for circadian effects
        prior_sleep_hours: Hours of sleep in prior sleep period

    Returns:
        Estimated Samn-Perelli level (1-7)

    Example:
        >>> level = estimate_level_from_factors(
        ...     hours_awake=18,
        ...     hours_worked_24h=12,
        ...     consecutive_night_shifts=2,
        ...     time_of_day_hour=4,  # Early morning
        ...     prior_sleep_hours=5.0
        ... )
        >>> print(level)  # Likely EXTREMELY_TIRED or EXHAUSTED
    """
    # Base score starts at 1 (fully alert)
    score = 1.0

    # Hours awake impact (major factor)
    # Awake > 16 hours significantly impairs performance
    if hours_awake > 24:
        score += 3.0
    elif hours_awake > 20:
        score += 2.5
    elif hours_awake > 16:
        score += 1.5
    elif hours_awake > 12:
        score += 0.5

    # Work hours impact
    if hours_worked_24h > 16:
        score += 2.0
    elif hours_worked_24h > 12:
        score += 1.0
    elif hours_worked_24h > 8:
        score += 0.5

    # Consecutive night shifts (circadian disruption)
    score += min(consecutive_night_shifts * 0.5, 1.5)

    # Time of day (circadian low point: 2-6 AM)
    if 2 <= time_of_day_hour <= 6:
        score += 1.5
    elif 14 <= time_of_day_hour <= 16:
        # Post-lunch dip
        score += 0.3

    # Prior sleep deficit
    sleep_deficit = max(0, 7.0 - prior_sleep_hours)
    score += sleep_deficit * 0.3

    # Clamp to valid range
    level = max(1, min(7, round(score)))

    logger.debug(
        f"Estimated SP level from factors: "
        f"awake={hours_awake}h, worked={hours_worked_24h}h, "
        f"nights={consecutive_night_shifts}, hour={time_of_day_hour}, "
        f"sleep={prior_sleep_hours}h -> SP-{level}"
    )

    return SamnPerelliLevel(level)


def get_all_levels() -> list[dict]:
    """
    Get all Samn-Perelli levels with descriptions for UI display.

    Returns:
        List of dicts with level info for dropdown/selection UI
    """
    return [
        {
            "level": level.value,
            "name": level.name,
            "description": LEVEL_DESCRIPTIONS[level],
        }
        for level in SamnPerelliLevel
    ]
