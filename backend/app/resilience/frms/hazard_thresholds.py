"""
Fatigue Hazard Thresholds and Triggers for Schedule Modifications.

Implements a tiered hazard system based on aviation FRMS principles:
- Level 1 (GREEN): Normal operations, routine monitoring
- Level 2 (YELLOW): Advisory, enhanced monitoring required
- Level 3 (ORANGE): Cautionary, schedule review recommended
- Level 4 (RED): Warning, schedule modification required
- Level 5 (BLACK): Critical, immediate intervention required

Each hazard level maps to specific:
- Alertness score thresholds
- Sleep debt limits
- Duty hour restrictions
- Circadian considerations
- Mandatory mitigations

Medical Residency Application:
- Integrates with ACGME duty hour rules
- Triggers proactive schedule adjustments
- Generates alerts before fatigue reaches critical levels
- Provides audit trail for safety compliance

References:
- FAA AC 120-103A: FRMS Advisory Circular
- ICAO Doc 9966: FRMS Manual for Regulators
- ACGME Duty Hour Standards
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID

from app.core.logging import get_logger
from app.resilience.frms.samn_perelli import SamnPerelliLevel
from app.resilience.frms.alertness_engine import AlertnessPrediction

logger = get_logger(__name__)


class HazardLevel(str, Enum):
    """
    Fatigue hazard levels with escalating interventions.

    Based on aviation FRMS color-coded risk levels.
    """

    GREEN = "green"  # Normal operations
    YELLOW = "yellow"  # Advisory - enhanced monitoring
    ORANGE = "orange"  # Cautionary - schedule review
    RED = "red"  # Warning - modification required
    BLACK = "black"  # Critical - immediate intervention


class TriggerType(str, Enum):
    """Types of fatigue hazard triggers."""

    ALERTNESS_LOW = "alertness_low"
    SLEEP_DEBT_HIGH = "sleep_debt_high"
    HOURS_AWAKE_EXTENDED = "hours_awake_extended"
    CIRCADIAN_NADIR = "circadian_nadir"
    CONSECUTIVE_NIGHTS = "consecutive_nights"
    ACGME_APPROACHING = "acgme_approaching"
    ACGME_VIOLATION = "acgme_violation"
    SAMN_PERELLI_HIGH = "samn_perelli_high"
    WORKLOAD_SUSTAINED = "workload_sustained"
    RECOVERY_INSUFFICIENT = "recovery_insufficient"


class MitigationType(str, Enum):
    """Types of fatigue mitigation actions."""

    MONITORING = "monitoring"  # Enhanced observation
    BUDDY_SYSTEM = "buddy_system"  # Pair with alert colleague
    DUTY_RESTRICTION = "duty_restriction"  # Limit to lower-risk duties
    SHIFT_SWAP = "shift_swap"  # Swap with rested colleague
    EARLY_RELEASE = "early_release"  # End shift early
    SCHEDULE_MODIFICATION = "schedule_modification"  # Modify future schedule
    MANDATORY_REST = "mandatory_rest"  # Required rest period
    IMMEDIATE_RELIEF = "immediate_relief"  # Immediate coverage by backup


# Hazard level thresholds
THRESHOLDS = {
    HazardLevel.GREEN: {
        "alertness_min": 0.7,
        "sleep_debt_max": 5.0,
        "hours_awake_max": 14.0,
        "samn_perelli_max": SamnPerelliLevel.A_LITTLE_TIRED,
        "consecutive_nights_max": 2,
    },
    HazardLevel.YELLOW: {
        "alertness_min": 0.55,
        "sleep_debt_max": 10.0,
        "hours_awake_max": 18.0,
        "samn_perelli_max": SamnPerelliLevel.MODERATELY_TIRED,
        "consecutive_nights_max": 4,
    },
    HazardLevel.ORANGE: {
        "alertness_min": 0.45,
        "sleep_debt_max": 15.0,
        "hours_awake_max": 22.0,
        "samn_perelli_max": SamnPerelliLevel.EXTREMELY_TIRED,
        "consecutive_nights_max": 5,
    },
    HazardLevel.RED: {
        "alertness_min": 0.35,
        "sleep_debt_max": 20.0,
        "hours_awake_max": 26.0,
        "samn_perelli_max": SamnPerelliLevel.EXHAUSTED,
        "consecutive_nights_max": 6,
    },
    HazardLevel.BLACK: {
        "alertness_min": 0.0,  # Below RED triggers BLACK
        "sleep_debt_max": 40.0,
        "hours_awake_max": 48.0,
        "samn_perelli_max": SamnPerelliLevel.EXHAUSTED,
        "consecutive_nights_max": 7,
    },
}

# Required mitigations by hazard level
LEVEL_MITIGATIONS = {
    HazardLevel.GREEN: [],
    HazardLevel.YELLOW: [
        MitigationType.MONITORING,
    ],
    HazardLevel.ORANGE: [
        MitigationType.MONITORING,
        MitigationType.BUDDY_SYSTEM,
        MitigationType.DUTY_RESTRICTION,
    ],
    HazardLevel.RED: [
        MitigationType.DUTY_RESTRICTION,
        MitigationType.SHIFT_SWAP,
        MitigationType.SCHEDULE_MODIFICATION,
    ],
    HazardLevel.BLACK: [
        MitigationType.MANDATORY_REST,
        MitigationType.IMMEDIATE_RELIEF,
    ],
}


@dataclass
class FatigueHazard:
    """
    Represents a detected fatigue hazard.

    Captures the hazard level, triggers, and required mitigations.

    Attributes:
        resident_id: UUID of the affected resident
        hazard_level: Severity level of the hazard
        detected_at: When the hazard was identified
        triggers: List of factors that triggered the hazard
        alertness_score: Current alertness score
        sleep_debt: Current sleep debt
        hours_awake: Current hours awake
        samn_perelli: Current Samn-Perelli level
        required_mitigations: Actions that must be taken
        recommended_mitigations: Additional suggested actions
        acgme_risk: Whether ACGME violation is imminent
        escalation_time: When hazard will escalate if unaddressed
        notes: Additional context or observations
    """

    resident_id: UUID
    hazard_level: HazardLevel
    detected_at: datetime
    triggers: list[TriggerType] = field(default_factory=list)
    alertness_score: float | None = None
    sleep_debt: float | None = None
    hours_awake: float | None = None
    samn_perelli: SamnPerelliLevel | None = None
    required_mitigations: list[MitigationType] = field(default_factory=list)
    recommended_mitigations: list[MitigationType] = field(default_factory=list)
    acgme_risk: bool = False
    escalation_time: datetime | None = None
    notes: str | None = None

    def to_dict(self) -> dict:
        """Convert hazard to dictionary for API response."""
        return {
            "resident_id": str(self.resident_id),
            "hazard_level": self.hazard_level.value,
            "hazard_level_name": self.hazard_level.name,
            "detected_at": self.detected_at.isoformat(),
            "triggers": [t.value for t in self.triggers],
            "alertness_score": (
                round(self.alertness_score, 3) if self.alertness_score else None
            ),
            "sleep_debt": round(self.sleep_debt, 1) if self.sleep_debt else None,
            "hours_awake": round(self.hours_awake, 1) if self.hours_awake else None,
            "samn_perelli": self.samn_perelli.value if self.samn_perelli else None,
            "required_mitigations": [m.value for m in self.required_mitigations],
            "recommended_mitigations": [m.value for m in self.recommended_mitigations],
            "acgme_risk": self.acgme_risk,
            "escalation_time": (
                self.escalation_time.isoformat() if self.escalation_time else None
            ),
            "notes": self.notes,
        }

    @property
    def is_critical(self) -> bool:
        """Check if hazard requires immediate intervention."""
        return self.hazard_level in [HazardLevel.RED, HazardLevel.BLACK]

    @property
    def requires_schedule_change(self) -> bool:
        """Check if hazard requires schedule modification."""
        return self.hazard_level in [
            HazardLevel.ORANGE,
            HazardLevel.RED,
            HazardLevel.BLACK,
        ]


class HazardThresholdEngine:
    """
    Engine for evaluating fatigue hazards and triggering interventions.

    Continuously monitors fatigue metrics against thresholds and
    generates hazard assessments with required mitigations.

    Features:
    - Multi-factor hazard evaluation
    - Escalation prediction
    - ACGME compliance integration
    - Mitigation recommendations
    - Audit trail generation

    Usage:
        engine = HazardThresholdEngine()
        hazard = engine.evaluate_hazard(
            resident_id=UUID("..."),
            alertness=0.45,
            sleep_debt=12.0,
            hours_awake=20.0,
            samn_perelli=SamnPerelliLevel.EXTREMELY_TIRED
        )
        if hazard.is_critical:
            # Trigger immediate intervention
            ...
    """

    def __init__(
        self,
        acgme_weekly_limit: float = 80.0,
        acgme_daily_limit: float = 24.0,
    ):
        """
        Initialize hazard threshold engine.

        Args:
            acgme_weekly_limit: ACGME weekly hour limit
            acgme_daily_limit: ACGME daily shift limit
        """
        self.acgme_weekly_limit = acgme_weekly_limit
        self.acgme_daily_limit = acgme_daily_limit

    def evaluate_hazard(
        self,
        resident_id: UUID,
        alertness: float | None = None,
        sleep_debt: float | None = None,
        hours_awake: float | None = None,
        samn_perelli: SamnPerelliLevel | None = None,
        consecutive_nights: int = 0,
        hours_worked_week: float = 0.0,
        prediction: AlertnessPrediction | None = None,
    ) -> FatigueHazard:
        """
        Evaluate fatigue metrics and determine hazard level.

        Checks all metrics against thresholds and identifies
        the highest applicable hazard level.

        Args:
            resident_id: UUID of the resident
            alertness: Alertness score (0.0-1.0)
            sleep_debt: Accumulated sleep debt hours
            hours_awake: Hours since last sleep
            samn_perelli: Samn-Perelli fatigue level
            consecutive_nights: Number of consecutive night shifts
            hours_worked_week: Hours worked in current week
            prediction: AlertnessPrediction if available

        Returns:
            FatigueHazard with level and required mitigations
        """
        # Extract from prediction if provided
        if prediction:
            alertness = alertness or prediction.alertness_score
            sleep_debt = sleep_debt or prediction.sleep_debt
            hours_awake = hours_awake or prediction.hours_awake
            samn_perelli = samn_perelli or prediction.samn_perelli_estimate

        # Collect triggers and find highest hazard level
        triggers = []
        highest_level = HazardLevel.GREEN

        # Check each metric against thresholds
        if alertness is not None:
            level = self._check_alertness(alertness)
            if level.value > highest_level.value:
                highest_level = level
                triggers.append(TriggerType.ALERTNESS_LOW)

        if sleep_debt is not None:
            level = self._check_sleep_debt(sleep_debt)
            if level.value > highest_level.value:
                highest_level = level
                triggers.append(TriggerType.SLEEP_DEBT_HIGH)

        if hours_awake is not None:
            level = self._check_hours_awake(hours_awake)
            if level.value > highest_level.value:
                highest_level = level
                triggers.append(TriggerType.HOURS_AWAKE_EXTENDED)

        if samn_perelli is not None:
            level = self._check_samn_perelli(samn_perelli)
            if level.value > highest_level.value:
                highest_level = level
                triggers.append(TriggerType.SAMN_PERELLI_HIGH)

        if consecutive_nights > 0:
            level = self._check_consecutive_nights(consecutive_nights)
            if level.value > highest_level.value:
                highest_level = level
                triggers.append(TriggerType.CONSECUTIVE_NIGHTS)

        # Check ACGME compliance
        acgme_risk = False
        if hours_worked_week > 0:
            if hours_worked_week >= self.acgme_weekly_limit:
                triggers.append(TriggerType.ACGME_VIOLATION)
                highest_level = HazardLevel.RED
                acgme_risk = True
            elif hours_worked_week >= self.acgme_weekly_limit * 0.9:
                triggers.append(TriggerType.ACGME_APPROACHING)
                if highest_level.value < HazardLevel.ORANGE.value:
                    highest_level = HazardLevel.ORANGE
                acgme_risk = True

        # Get required mitigations for this level
        required_mits = LEVEL_MITIGATIONS.get(highest_level, [])

        # Calculate escalation time
        escalation_time = self._estimate_escalation_time(
            highest_level, hours_awake, sleep_debt
        )

        hazard = FatigueHazard(
            resident_id=resident_id,
            hazard_level=highest_level,
            detected_at=datetime.utcnow(),
            triggers=triggers,
            alertness_score=alertness,
            sleep_debt=sleep_debt,
            hours_awake=hours_awake,
            samn_perelli=samn_perelli,
            required_mitigations=list(required_mits),
            recommended_mitigations=self._get_recommended_mitigations(highest_level),
            acgme_risk=acgme_risk,
            escalation_time=escalation_time,
        )

        if highest_level != HazardLevel.GREEN:
            logger.warning(
                f"Fatigue hazard detected for {resident_id}: "
                f"level={highest_level.value}, "
                f"triggers={[t.value for t in triggers]}, "
                f"acgme_risk={acgme_risk}"
            )

        return hazard

    def evaluate_from_prediction(
        self,
        prediction: AlertnessPrediction,
        consecutive_nights: int = 0,
        hours_worked_week: float = 0.0,
    ) -> FatigueHazard:
        """
        Evaluate hazard from an AlertnessPrediction.

        Convenience method for integrating with alertness engine.

        Args:
            prediction: AlertnessPrediction to evaluate
            consecutive_nights: Number of consecutive night shifts
            hours_worked_week: Hours worked in current week

        Returns:
            FatigueHazard assessment
        """
        return self.evaluate_hazard(
            resident_id=prediction.resident_id,
            prediction=prediction,
            consecutive_nights=consecutive_nights,
            hours_worked_week=hours_worked_week,
        )

    def batch_evaluate(
        self,
        residents: list[dict],
    ) -> list[FatigueHazard]:
        """
        Evaluate hazards for multiple residents.

        Args:
            residents: List of dicts with resident fatigue data

        Returns:
            List of FatigueHazard assessments
        """
        hazards = []
        for data in residents:
            hazard = self.evaluate_hazard(
                resident_id=data.get("resident_id"),
                alertness=data.get("alertness"),
                sleep_debt=data.get("sleep_debt"),
                hours_awake=data.get("hours_awake"),
                samn_perelli=data.get("samn_perelli"),
                consecutive_nights=data.get("consecutive_nights", 0),
                hours_worked_week=data.get("hours_worked_week", 0),
            )
            hazards.append(hazard)
        return hazards

    def get_level_summary(self, hazards: list[FatigueHazard]) -> dict:
        """
        Summarize hazard levels across a group.

        Args:
            hazards: List of hazard assessments

        Returns:
            Dict with counts and percentages by level
        """
        counts = dict.fromkeys(HazardLevel, 0)
        for hazard in hazards:
            counts[hazard.hazard_level] += 1

        total = len(hazards) if hazards else 1

        return {
            "total_residents": len(hazards),
            "by_level": {
                level.value: {
                    "count": count,
                    "percentage": round(count / total * 100, 1),
                }
                for level, count in counts.items()
            },
            "critical_count": sum(1 for h in hazards if h.is_critical),
            "acgme_risk_count": sum(1 for h in hazards if h.acgme_risk),
        }

    def _check_alertness(self, alertness: float) -> HazardLevel:
        """Check alertness against thresholds."""
        for level in [
            HazardLevel.BLACK,
            HazardLevel.RED,
            HazardLevel.ORANGE,
            HazardLevel.YELLOW,
            HazardLevel.GREEN,
        ]:
            if alertness < THRESHOLDS[level]["alertness_min"]:
                # Below this level's minimum, so return the higher level
                if level == HazardLevel.GREEN:
                    return HazardLevel.YELLOW
                continue
            return level
        return HazardLevel.BLACK

    def _check_sleep_debt(self, sleep_debt: float) -> HazardLevel:
        """Check sleep debt against thresholds."""
        for level in [
            HazardLevel.GREEN,
            HazardLevel.YELLOW,
            HazardLevel.ORANGE,
            HazardLevel.RED,
            HazardLevel.BLACK,
        ]:
            if sleep_debt <= THRESHOLDS[level]["sleep_debt_max"]:
                return level
        return HazardLevel.BLACK

    def _check_hours_awake(self, hours_awake: float) -> HazardLevel:
        """Check hours awake against thresholds."""
        for level in [
            HazardLevel.GREEN,
            HazardLevel.YELLOW,
            HazardLevel.ORANGE,
            HazardLevel.RED,
            HazardLevel.BLACK,
        ]:
            if hours_awake <= THRESHOLDS[level]["hours_awake_max"]:
                return level
        return HazardLevel.BLACK

    def _check_samn_perelli(self, sp_level: SamnPerelliLevel) -> HazardLevel:
        """Check Samn-Perelli level against thresholds."""
        for level in [
            HazardLevel.GREEN,
            HazardLevel.YELLOW,
            HazardLevel.ORANGE,
            HazardLevel.RED,
            HazardLevel.BLACK,
        ]:
            if sp_level <= THRESHOLDS[level]["samn_perelli_max"]:
                return level
        return HazardLevel.BLACK

    def _check_consecutive_nights(self, nights: int) -> HazardLevel:
        """Check consecutive nights against thresholds."""
        for level in [
            HazardLevel.GREEN,
            HazardLevel.YELLOW,
            HazardLevel.ORANGE,
            HazardLevel.RED,
            HazardLevel.BLACK,
        ]:
            if nights <= THRESHOLDS[level]["consecutive_nights_max"]:
                return level
        return HazardLevel.BLACK

    def _estimate_escalation_time(
        self,
        current_level: HazardLevel,
        hours_awake: float | None,
        sleep_debt: float | None,
    ) -> datetime | None:
        """Estimate when hazard will escalate to next level."""
        if current_level == HazardLevel.BLACK:
            return None  # Already at highest

        now = datetime.utcnow()

        # Estimate based on hours awake progression
        if hours_awake is not None:
            current_threshold = THRESHOLDS[current_level]["hours_awake_max"]

            # Find next level's threshold
            levels = list(HazardLevel)
            current_idx = levels.index(current_level)
            if current_idx < len(levels) - 1:
                next_threshold = THRESHOLDS[levels[current_idx + 1]]["hours_awake_max"]
                hours_until_escalation = next_threshold - hours_awake
                if hours_until_escalation > 0:
                    return now + timedelta(hours=hours_until_escalation)

        return None

    def _get_recommended_mitigations(
        self,
        level: HazardLevel,
    ) -> list[MitigationType]:
        """Get recommended (optional) mitigations for a hazard level."""
        # Recommend mitigations from adjacent levels
        recommended = []

        if level == HazardLevel.YELLOW:
            recommended.append(MitigationType.BUDDY_SYSTEM)
        elif level == HazardLevel.ORANGE:
            recommended.append(MitigationType.SHIFT_SWAP)
            recommended.append(MitigationType.EARLY_RELEASE)
        elif level == HazardLevel.RED:
            recommended.append(MitigationType.IMMEDIATE_RELIEF)

        return recommended


def get_hazard_level_info() -> list[dict]:
    """
    Get all hazard levels with descriptions for UI display.

    Returns:
        List of hazard level information dicts
    """
    descriptions = {
        HazardLevel.GREEN: "Normal operations. Fatigue within acceptable limits.",
        HazardLevel.YELLOW: "Advisory. Enhanced monitoring recommended.",
        HazardLevel.ORANGE: "Cautionary. Schedule review and possible modification.",
        HazardLevel.RED: "Warning. Schedule modification required.",
        HazardLevel.BLACK: "Critical. Immediate intervention required.",
    }

    return [
        {
            "level": level.value,
            "name": level.name,
            "description": descriptions[level],
            "thresholds": THRESHOLDS[level],
            "required_mitigations": [m.value for m in LEVEL_MITIGATIONS[level]],
        }
        for level in HazardLevel
    ]


def get_mitigation_info() -> list[dict]:
    """
    Get all mitigation types with descriptions.

    Returns:
        List of mitigation type information dicts
    """
    descriptions = {
        MitigationType.MONITORING: "Enhanced observation of the resident's condition.",
        MitigationType.BUDDY_SYSTEM: "Pair with an alert colleague for mutual support.",
        MitigationType.DUTY_RESTRICTION: "Limit duties to lower-risk activities.",
        MitigationType.SHIFT_SWAP: "Swap shifts with a rested colleague.",
        MitigationType.EARLY_RELEASE: "End current shift early.",
        MitigationType.SCHEDULE_MODIFICATION: "Modify upcoming schedule to allow recovery.",
        MitigationType.MANDATORY_REST: "Required rest period before next duty.",
        MitigationType.IMMEDIATE_RELIEF: "Immediate coverage by backup personnel.",
    }

    return [
        {
            "type": mit.value,
            "name": mit.name,
            "description": descriptions[mit],
        }
        for mit in MitigationType
    ]
