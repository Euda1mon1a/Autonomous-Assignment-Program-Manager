"""
Constraints Module - Re-exports for Backward Compatibility.

This module provides a clean API for importing constraint classes while maintaining
backward compatibility with existing code that imports from the old monolithic
constraints.py file.

Usage:
    from app.scheduling.constraints import (
        ConstraintManager,
        SchedulingContext,
        EightyHourRuleConstraint,
        AvailabilityConstraint,
    )

The constraints are now organized into domain-specific modules:
- base: Core classes, enums, ConstraintManager, SchedulingContext
- acgme_constraints: ACGME compliance (duty hours, supervision)
- time_constraints: Availability and time-based rules
- capacity_constraints: Capacity limits and coverage
- custom_constraints: Equity, continuity, preferences, resilience
- faculty_constraints: Faculty-specific constraints (placeholder)
"""

***REMOVED*** Base classes, enums, and infrastructure
from app.scheduling.constraints.base import (
    ***REMOVED*** Enums
    ConstraintPriority,
    ConstraintType,
    ***REMOVED*** Dataclasses
    ConstraintViolation,
    ConstraintResult,
    SchedulingContext,
    ***REMOVED*** Base classes
    Constraint,
    HardConstraint,
    SoftConstraint,
    ***REMOVED*** Manager
    ConstraintManager,
)

***REMOVED*** ACGME compliance constraints
from app.scheduling.constraints.acgme_constraints import (
    EightyHourRuleConstraint,
    OneInSevenRuleConstraint,
    SupervisionRatioConstraint,
)

***REMOVED*** Time-based constraints
from app.scheduling.constraints.time_constraints import (
    AvailabilityConstraint,
    WednesdayAMInternOnlyConstraint,
)

***REMOVED*** Capacity constraints
from app.scheduling.constraints.capacity_constraints import (
    OnePersonPerBlockConstraint,
    ClinicCapacityConstraint,
    MaxPhysiciansInClinicConstraint,
    CoverageConstraint,
)

***REMOVED*** Custom/business constraints
from app.scheduling.constraints.custom_constraints import (
    EquityConstraint,
    ContinuityConstraint,
    PreferenceConstraint,
    HubProtectionConstraint,
    UtilizationBufferConstraint,
    ZoneBoundaryConstraint,
    PreferenceTrailConstraint,
    N1VulnerabilityConstraint,
)

***REMOVED*** Define what gets exported with "from constraints import *"
__all__ = [
    ***REMOVED*** Base
    "ConstraintPriority",
    "ConstraintType",
    "ConstraintViolation",
    "ConstraintResult",
    "SchedulingContext",
    "Constraint",
    "HardConstraint",
    "SoftConstraint",
    "ConstraintManager",
    ***REMOVED*** ACGME
    "EightyHourRuleConstraint",
    "OneInSevenRuleConstraint",
    "SupervisionRatioConstraint",
    ***REMOVED*** Time
    "AvailabilityConstraint",
    "WednesdayAMInternOnlyConstraint",
    ***REMOVED*** Capacity
    "OnePersonPerBlockConstraint",
    "ClinicCapacityConstraint",
    "MaxPhysiciansInClinicConstraint",
    "CoverageConstraint",
    ***REMOVED*** Custom
    "EquityConstraint",
    "ContinuityConstraint",
    "PreferenceConstraint",
    "HubProtectionConstraint",
    "UtilizationBufferConstraint",
    "ZoneBoundaryConstraint",
    "PreferenceTrailConstraint",
    "N1VulnerabilityConstraint",
]
