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

# Base classes, enums, and infrastructure
from app.scheduling.constraints.base import (
    # Enums
    ConstraintPriority,
    ConstraintType,
    # Dataclasses
    ConstraintViolation,
    ConstraintResult,
    SchedulingContext,
    # Base classes
    Constraint,
    HardConstraint,
    SoftConstraint,
    # Manager
    ConstraintManager,
)

# ACGME compliance constraints
from app.scheduling.constraints.acgme_constraints import (
    EightyHourRuleConstraint,
    OneInSevenRuleConstraint,
    SupervisionRatioConstraint,
)

# Time-based constraints
from app.scheduling.constraints.time_constraints import (
    AvailabilityConstraint,
    WednesdayAMInternOnlyConstraint,
)

# Capacity constraints
from app.scheduling.constraints.capacity_constraints import (
    OnePersonPerBlockConstraint,
    ClinicCapacityConstraint,
    MaxPhysiciansInClinicConstraint,
    CoverageConstraint,
)

# Custom/business constraints
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

# Define what gets exported with "from constraints import *"
__all__ = [
    # Base
    "ConstraintPriority",
    "ConstraintType",
    "ConstraintViolation",
    "ConstraintResult",
    "SchedulingContext",
    "Constraint",
    "HardConstraint",
    "SoftConstraint",
    "ConstraintManager",
    # ACGME
    "EightyHourRuleConstraint",
    "OneInSevenRuleConstraint",
    "SupervisionRatioConstraint",
    # Time
    "AvailabilityConstraint",
    "WednesdayAMInternOnlyConstraint",
    # Capacity
    "OnePersonPerBlockConstraint",
    "ClinicCapacityConstraint",
    "MaxPhysiciansInClinicConstraint",
    "CoverageConstraint",
    # Custom
    "EquityConstraint",
    "ContinuityConstraint",
    "PreferenceConstraint",
    "HubProtectionConstraint",
    "UtilizationBufferConstraint",
    "ZoneBoundaryConstraint",
    "PreferenceTrailConstraint",
    "N1VulnerabilityConstraint",
]
