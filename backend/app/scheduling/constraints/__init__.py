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

***REMOVED*** ACGME compliance constraints
from .acgme import (
    AvailabilityConstraint,
    EightyHourRuleConstraint,
    OneInSevenRuleConstraint,
    SupervisionRatioConstraint,
)

***REMOVED*** Capacity and coverage constraints
from .capacity import (
    ClinicCapacityConstraint,
    CoverageConstraint,
    MaxPhysiciansInClinicConstraint,
    OnePersonPerBlockConstraint,
)

***REMOVED*** Temporal constraints
from .temporal import WednesdayAMInternOnlyConstraint

***REMOVED*** and preference constraints
from .faculty import PreferenceConstraint

***REMOVED*** Equity and continuity constraints
from .equity import ContinuityConstraint, EquityConstraint

***REMOVED*** Resilience-aware constraints
from .resilience import (
    HubProtectionConstraint,
    N1VulnerabilityConstraint,
    PreferenceTrailConstraint,
    UtilizationBufferConstraint,
    ZoneBoundaryConstraint,
)

***REMOVED*** Constraint manager
from .manager import ConstraintManager

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
    ***REMOVED*** constraints
    "PreferenceConstraint",
    ***REMOVED*** Equity constraints
    "ContinuityConstraint",
    "EquityConstraint",
    ***REMOVED*** Resilience constraints
    "HubProtectionConstraint",
    "N1VulnerabilityConstraint",
    "PreferenceTrailConstraint",
    "UtilizationBufferConstraint",
    "ZoneBoundaryConstraint",
    ***REMOVED*** Manager
    "ConstraintManager",
]
