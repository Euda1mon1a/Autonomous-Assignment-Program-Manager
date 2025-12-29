"""
Tools subpackage for specialized MCP tools.

This package contains specialized tool implementations that integrate
with the backend constraint service and other services.
"""

from .validate_schedule import (
    ConstraintConfig,
    ScheduleValidationRequest,
    ScheduleValidationResponse,
    validate_schedule,
)
from .game_theory_tools import (
    # Analysis Functions
    analyze_nash_stability,
    find_deviation_incentives,
    detect_coordination_failures,
    # Request Models
    NashStabilityRequest,
    DeviationIncentivesRequest,
    # Response Models
    NashStabilityResponse,
    PersonDeviationAnalysis,
    CoordinationFailuresResponse,
    # Supporting Models
    DeviationIncentive,
    CoordinationFailure,
    UtilityComponents,
    # Enums
    StabilityStatus,
    DeviationType,
    CoordinationFailureType,
    # Utility Functions
    calculate_person_utility,
)

__all__ = [
    "ConstraintConfig",
    "ScheduleValidationRequest",
    "ScheduleValidationResponse",
    "validate_schedule",
    # Game Theory Tools
    "analyze_nash_stability",
    "find_deviation_incentives",
    "detect_coordination_failures",
    "NashStabilityRequest",
    "DeviationIncentivesRequest",
    "NashStabilityResponse",
    "PersonDeviationAnalysis",
    "CoordinationFailuresResponse",
    "DeviationIncentive",
    "CoordinationFailure",
    "UtilityComponents",
    "StabilityStatus",
    "DeviationType",
    "CoordinationFailureType",
    "calculate_person_utility",
]
