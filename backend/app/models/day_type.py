"""
Day Type Enums for MEDCOM Day-Type System.

Defines standardized day types and operational intent levels for
military medical residency scheduling.

Reference: MEDCOM/DHA training holiday and minimal manning guidance.
"""

from enum import Enum


class DayType(str, Enum):
    """
    Day type classification for scheduling blocks.

    Based on MEDCOM/DHA reference for training holidays, minimal manning,
    and EO closure days.
    """

    NORMAL = "NORMAL"
    """Standard operating day with baseline capacity."""

    FEDERAL_HOLIDAY = "FEDERAL_HOLIDAY"
    """OPM-listed federal holiday (observed date per OPM rules)."""

    TRAINING_HOLIDAY = "TRAINING_HOLIDAY"
    """
    Unit/installation-designated training holiday (DONSA).
    Discretionary and mission-dependent. Not guaranteed - chain of command
    can restrict if mission requirements prevent participation.
    """

    MINIMAL_MANNING = "MINIMAL_MANNING"
    """
    Command-directed reduced manning day.
    Organization remains open but plans for reduced staffing.
    """

    EO_CLOSURE = "EO_CLOSURE"
    """
    Presidential Executive Order excused-from-duty day.
    Agency heads can require work for national security, defense,
    or other public needs.
    """

    INAUGURATION_DAY = "INAUGURATION_DAY"
    """
    Legal holiday for DC-area federal employees on January 20 every fourth year.
    Not applicable for Hawaii MTF scheduling but included for portability.
    """


class OperationalIntent(str, Enum):
    """
    Operational capacity intent for scheduling blocks.

    Defines the expected operational state and default capacity multiplier.
    """

    NORMAL = "NORMAL"
    """
    Baseline operations. Full capacity (1.0 multiplier).
    Standard scheduling rules apply.
    """

    REDUCED_CAPACITY = "REDUCED_CAPACITY"
    """
    Clinic open but reduced throughput. Default 0.25 multiplier.
    Typical triggers: MINIMAL_MANNING, some FEDERAL_HOLIDAY dates.
    Block routine appointments, prioritize urgent/inpatient/ED.
    """

    NON_OPERATIONAL = "NON_OPERATIONAL"
    """
    No routine clinic. Skeleton crew only. Default 0.0 multiplier.
    Typical triggers: TRAINING_HOLIDAY (DONSA), some EO_CLOSURE days.
    Essential personnel override may still apply.
    """


# Default mapping from DayType to OperationalIntent
DAY_TYPE_DEFAULT_INTENT: dict[DayType, OperationalIntent] = {
    DayType.NORMAL: OperationalIntent.NORMAL,
    DayType.FEDERAL_HOLIDAY: OperationalIntent.REDUCED_CAPACITY,
    DayType.TRAINING_HOLIDAY: OperationalIntent.NON_OPERATIONAL,
    DayType.MINIMAL_MANNING: OperationalIntent.REDUCED_CAPACITY,
    DayType.EO_CLOSURE: OperationalIntent.NON_OPERATIONAL,
    DayType.INAUGURATION_DAY: OperationalIntent.NORMAL,  # Not applicable for Hawaii
}

# Default capacity multipliers by OperationalIntent
OPERATIONAL_INTENT_CAPACITY: dict[OperationalIntent, float] = {
    OperationalIntent.NORMAL: 1.0,
    OperationalIntent.REDUCED_CAPACITY: 0.25,
    OperationalIntent.NON_OPERATIONAL: 0.0,
}


def get_default_operational_intent(day_type: DayType) -> OperationalIntent:
    """Get the default operational intent for a day type."""
    return DAY_TYPE_DEFAULT_INTENT.get(day_type, OperationalIntent.NORMAL)


def get_capacity_multiplier(intent: OperationalIntent) -> float:
    """Get the default capacity multiplier for an operational intent."""
    return OPERATIONAL_INTENT_CAPACITY.get(intent, 1.0)
