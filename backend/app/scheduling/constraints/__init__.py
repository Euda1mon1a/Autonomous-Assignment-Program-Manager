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

# ACGME compliance constraints
from .acgme import (
    AvailabilityConstraint,
    EightyHourRuleConstraint,
    OneInSevenRuleConstraint,
    SupervisionRatioConstraint,
)

# Capacity and coverage constraints
from .capacity import (
    ClinicCapacityConstraint,
    CoverageConstraint,
    MaxPhysiciansInClinicConstraint,
    OnePersonPerBlockConstraint,
)

# Temporal constraints
from .temporal import WednesdayAMInternOnlyConstraint

***REMOVED*** and preference constraints
from .faculty import PreferenceConstraint

***REMOVED*** role-based constraints
from .faculty_role import (
    FacultyRoleClinicConstraint,
    SMFacultyClinicConstraint,
)

# FMIT constraints
from .fmit import (
    FMITMandatoryCallConstraint,
    FMITWeekBlockingConstraint,
    PostFMITRecoveryConstraint,
    get_fmit_week_dates,
    is_sun_thurs,
)

# Equity and continuity constraints
from .equity import ContinuityConstraint, EquityConstraint

# Sports Medicine coordination constraints
from .sports_medicine import SMResidentFacultyAlignmentConstraint

# Post-call assignment constraints
from .post_call import PostCallAutoAssignmentConstraint

# Call equity and preference constraints
from .call_equity import (
    DeptChiefWednesdayPreferenceConstraint,
    SundayCallEquityConstraint,
    TuesdayCallPreferenceConstraint,
    WeekdayCallEquityConstraint,
)

# Resilience-aware constraints
from .resilience import (
    HubProtectionConstraint,
    N1VulnerabilityConstraint,
    PreferenceTrailConstraint,
    UtilizationBufferConstraint,
    ZoneBoundaryConstraint,
)

# Constraint manager
from .manager import ConstraintManager

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
    ***REMOVED*** constraints
    "PreferenceConstraint",
    ***REMOVED*** role constraints
    "FacultyRoleClinicConstraint",
    "SMFacultyClinicConstraint",
    # FMIT constraints
    "FMITMandatoryCallConstraint",
    "FMITWeekBlockingConstraint",
    "PostFMITRecoveryConstraint",
    "get_fmit_week_dates",
    "is_sun_thurs",
    # Equity constraints
    "ContinuityConstraint",
    "EquityConstraint",
    # Sports Medicine coordination constraints
    "SMResidentFacultyAlignmentConstraint",
    # Post-call assignment constraints
    "PostCallAutoAssignmentConstraint",
    # Call equity and preference constraints
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
    # Manager
    "ConstraintManager",
]
