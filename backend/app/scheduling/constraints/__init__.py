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

***REMOVED*** Base classes and types
***REMOVED*** ACGME compliance constraints
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

***REMOVED*** Overnight call coverage constraints (hard)
from .call_coverage import (
    AdjunctCallExclusionConstraint,
    CallAvailabilityConstraint,
    OvernightCallCoverageConstraint,
    OVERNIGHT_CALL_DAYS,
)

***REMOVED*** Call equity and preference constraints (soft)
from .call_equity import (
    CallSpacingConstraint,
    DeptChiefWednesdayPreferenceConstraint,
    SundayCallEquityConstraint,
    TuesdayCallPreferenceConstraint,
    WeekdayCallEquityConstraint,
)

***REMOVED*** Capacity and coverage constraints
from .capacity import (
    ClinicCapacityConstraint,
    CoverageConstraint,
    MaxPhysiciansInClinicConstraint,
    OnePersonPerBlockConstraint,
)

***REMOVED*** Equity and continuity constraints
from .equity import ContinuityConstraint, EquityConstraint

***REMOVED*** Faculty and preference constraints
from .faculty import PreferenceConstraint

***REMOVED*** Faculty role-based constraints
from .faculty_role import (
    FacultyRoleClinicConstraint,
    SMFacultyClinicConstraint,
)

***REMOVED*** Faculty primary duty constraints (Airtable-driven)
from .primary_duty import (
    FacultyClinicEquitySoftConstraint,
    FacultyDayAvailabilityConstraint,
    FacultyPrimaryDutyClinicConstraint,
    PrimaryDutyConfig,
    load_primary_duties_config,
)

***REMOVED*** FMIT constraints
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

***REMOVED*** Constraint manager
from .manager import ConstraintManager

***REMOVED*** Night Float post-call constraints
from .night_float_post_call import NightFloatPostCallConstraint

***REMOVED*** Post-call assignment constraints
from .post_call import PostCallAutoAssignmentConstraint

***REMOVED*** Resilience-aware constraints
from .resilience import (
    HubProtectionConstraint,
    N1VulnerabilityConstraint,
    PreferenceTrailConstraint,
    UtilizationBufferConstraint,
    ZoneBoundaryConstraint,
)

***REMOVED*** Resident inpatient constraints
from .inpatient import (
    FMITResidentClinicDayConstraint,
    ResidentInpatientHeadcountConstraint,
)

***REMOVED*** Sports Medicine coordination constraints
from .sports_medicine import SMResidentFacultyAlignmentConstraint

***REMOVED*** Temporal constraints
from .temporal import (
    InvertedWednesdayConstraint,
    WednesdayAMInternOnlyConstraint,
    WednesdayPMSingleFacultyConstraint,
)

***REMOVED*** Define __all__ for explicit exports
__all__ = [
    ***REMOVED*** Base classes and types
    "Constraint",
    "ConstraintPriority",
    "ConstraintResult",
    "ConstraintType",
    "ConstraintViolation",
    "HardConstraint",
    "SchedulingContext",
    "SoftConstraint",
    ***REMOVED*** ACGME constraints
    "ACGMEConstraintValidator",
    "AvailabilityConstraint",
    "EightyHourRuleConstraint",
    "OneInSevenRuleConstraint",
    "SupervisionRatioConstraint",
    ***REMOVED*** Capacity constraints
    "ClinicCapacityConstraint",
    "CoverageConstraint",
    "MaxPhysiciansInClinicConstraint",
    "OnePersonPerBlockConstraint",
    ***REMOVED*** Temporal constraints
    "WednesdayAMInternOnlyConstraint",
    "WednesdayPMSingleFacultyConstraint",
    "InvertedWednesdayConstraint",
    ***REMOVED*** Faculty constraints
    "PreferenceConstraint",
    ***REMOVED*** Faculty role constraints
    "FacultyRoleClinicConstraint",
    "SMFacultyClinicConstraint",
    ***REMOVED*** Faculty primary duty constraints
    "FacultyPrimaryDutyClinicConstraint",
    "FacultyDayAvailabilityConstraint",
    "FacultyClinicEquitySoftConstraint",
    "PrimaryDutyConfig",
    "load_primary_duties_config",
    ***REMOVED*** FMIT constraints
    "FMITContinuityTurfConstraint",
    "FMITMandatoryCallConstraint",
    "FMITStaffingFloorConstraint",
    "FMITWeekBlockingConstraint",
    "PostFMITRecoveryConstraint",
    "PostFMITSundayBlockingConstraint",
    "get_fmit_week_dates",
    "is_sun_thurs",
    ***REMOVED*** Equity constraints
    "ContinuityConstraint",
    "EquityConstraint",
    ***REMOVED*** Sports Medicine coordination constraints
    "SMResidentFacultyAlignmentConstraint",
    ***REMOVED*** Post-call assignment constraints
    "PostCallAutoAssignmentConstraint",
    ***REMOVED*** Night Float post-call constraints
    "NightFloatPostCallConstraint",
    ***REMOVED*** Overnight call coverage constraints (hard)
    "AdjunctCallExclusionConstraint",
    "CallAvailabilityConstraint",
    "OvernightCallCoverageConstraint",
    "OVERNIGHT_CALL_DAYS",
    ***REMOVED*** Call equity and preference constraints (soft)
    "CallSpacingConstraint",
    "DeptChiefWednesdayPreferenceConstraint",
    "SundayCallEquityConstraint",
    "TuesdayCallPreferenceConstraint",
    "WeekdayCallEquityConstraint",
    ***REMOVED*** Resilience constraints
    "HubProtectionConstraint",
    "N1VulnerabilityConstraint",
    "PreferenceTrailConstraint",
    "UtilizationBufferConstraint",
    "ZoneBoundaryConstraint",
    ***REMOVED*** Resident inpatient constraints
    "FMITResidentClinicDayConstraint",
    "ResidentInpatientHeadcountConstraint",
    ***REMOVED*** Manager
    "ConstraintManager",
]
