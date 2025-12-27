"""
Modular Constraint System for Residency Scheduling.

This package provides a flexible, composable constraint system that can be used
with multiple solvers (OR-Tools CP-SAT, PuLP, custom algorithms).

Constraint Types:
- Hard Constraints: Must be satisfied (ACGME rules, availability, capacity)
- Soft Constraints: Should be optimized (preferences, equity, continuity)

Architecture:
- Constraint: Base class defining the interface
- HardConstraint: Constraints that must be satisfied
- SoftConstraint: Constraints with weights for optimization
- ConstraintManager: Composes and manages constraints for solvers

All classes are re-exported from this module to maintain backward compatibility
with existing code that imports directly from the constraints module.

Example:
    >>> from backend.app.scheduling.constraints import ConstraintManager
    >>> from backend.app.scheduling.constraints import AvailabilityConstraint
    >>>
    >>> manager = ConstraintManager.create_default()
    >>> manager.add(AvailabilityConstraint())
"""

# Base classes and types
# ACGME compliance constraints
from .acgme import (
    ACGMEConstraintValidator,
    AvailabilityConstraint,
    EightyHourRuleConstraint,
    OneInSevenRuleConstraint,
    SupervisionRatioConstraint,
)
from .base import (
    Constraint,
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SchedulingContext,
    SoftConstraint,
)

# Call coverage constraints
from .call_coverage import (
    AdjunctCallExclusionConstraint,
    CallAvailabilityConstraint,
    OvernightCallCoverageConstraint,
)

# Call equity and preference constraints
from .call_equity import (
    CallSpacingConstraint,
    DeptChiefWednesdayPreferenceConstraint,
    SundayCallEquityConstraint,
    TuesdayCallPreferenceConstraint,
    WeekdayCallEquityConstraint,
)

# Capacity and coverage constraints
from .capacity import (
    ClinicCapacityConstraint,
    CoverageConstraint,
    MaxPhysiciansInClinicConstraint,
    OnePersonPerBlockConstraint,
)

# Equity and continuity constraints
from .equity import ContinuityConstraint, EquityConstraint

# Faculty and preference constraints
from .faculty import PreferenceConstraint

# Faculty role-based constraints
from .faculty_role import (
    FacultyRoleClinicConstraint,
    SMFacultyClinicConstraint,
)

# Faculty primary duty constraints (Airtable-driven)
from .primary_duty import (
    FacultyClinicEquitySoftConstraint,
    FacultyDayAvailabilityConstraint,
    FacultyPrimaryDutyClinicConstraint,
    PrimaryDutyConfig,
    load_primary_duties_config,
)

# FMIT constraints
from .fmit import (
    FMITContinuityTurfConstraint,
    FMITMandatoryCallConstraint,
    FMITStaffingFloorConstraint,
    FMITWeekBlockingConstraint,
    PostFMITRecoveryConstraint,
    PostFMITSundayBlockingConstraint,
    get_fmit_week_dates,
    is_sun_thurs,
)

# Constraint manager
from .manager import ConstraintManager

# Night Float post-call constraints
from .night_float_post_call import NightFloatPostCallConstraint

# Post-call assignment constraints
from .post_call import PostCallAutoAssignmentConstraint

# Resilience-aware constraints
from .resilience import (
    HubProtectionConstraint,
    N1VulnerabilityConstraint,
    PreferenceTrailConstraint,
    UtilizationBufferConstraint,
    ZoneBoundaryConstraint,
)

# Resident inpatient constraints
from .inpatient import (
    FMITResidentClinicDayConstraint,
    ResidentInpatientHeadcountConstraint,
)

# Sports Medicine coordination constraints
from .sports_medicine import SMResidentFacultyAlignmentConstraint

# Temporal constraints
from .temporal import (
    InvertedWednesdayConstraint,
    WednesdayAMInternOnlyConstraint,
    WednesdayPMSingleFacultyConstraint,
)

# Define __all__ for explicit exports
__all__ = [
    # Base classes and types
    "Constraint",
    "ConstraintPriority",
    "ConstraintResult",
    "ConstraintType",
    "ConstraintViolation",
    "HardConstraint",
    "SchedulingContext",
    "SoftConstraint",
    # ACGME constraints
    "ACGMEConstraintValidator",
    "AvailabilityConstraint",
    "EightyHourRuleConstraint",
    "OneInSevenRuleConstraint",
    "SupervisionRatioConstraint",
    # Capacity constraints
    "ClinicCapacityConstraint",
    "CoverageConstraint",
    "MaxPhysiciansInClinicConstraint",
    "OnePersonPerBlockConstraint",
    # Temporal constraints
    "WednesdayAMInternOnlyConstraint",
    "WednesdayPMSingleFacultyConstraint",
    "InvertedWednesdayConstraint",
    # Faculty constraints
    "PreferenceConstraint",
    # Faculty role constraints
    "FacultyRoleClinicConstraint",
    "SMFacultyClinicConstraint",
    # Faculty primary duty constraints
    "FacultyPrimaryDutyClinicConstraint",
    "FacultyDayAvailabilityConstraint",
    "FacultyClinicEquitySoftConstraint",
    "PrimaryDutyConfig",
    "load_primary_duties_config",
    # FMIT constraints
    "FMITContinuityTurfConstraint",
    "FMITMandatoryCallConstraint",
    "FMITStaffingFloorConstraint",
    "FMITWeekBlockingConstraint",
    "PostFMITRecoveryConstraint",
    "PostFMITSundayBlockingConstraint",
    "get_fmit_week_dates",
    "is_sun_thurs",
    # Equity constraints
    "ContinuityConstraint",
    "EquityConstraint",
    # Sports Medicine coordination constraints
    "SMResidentFacultyAlignmentConstraint",
    # Post-call assignment constraints
    "PostCallAutoAssignmentConstraint",
    # Night Float post-call constraints
    "NightFloatPostCallConstraint",
    # Call coverage constraints
    "AdjunctCallExclusionConstraint",
    "CallAvailabilityConstraint",
    "OvernightCallCoverageConstraint",
    # Call equity and preference constraints
    "CallSpacingConstraint",
    "DeptChiefWednesdayPreferenceConstraint",
    "SundayCallEquityConstraint",
    "TuesdayCallPreferenceConstraint",
    "WeekdayCallEquityConstraint",
    # Resilience constraints
    "HubProtectionConstraint",
    "N1VulnerabilityConstraint",
    "PreferenceTrailConstraint",
    "UtilizationBufferConstraint",
    "ZoneBoundaryConstraint",
    # Resident inpatient constraints
    "FMITResidentClinicDayConstraint",
    "ResidentInpatientHeadcountConstraint",
    # Manager
    "ConstraintManager",
]
