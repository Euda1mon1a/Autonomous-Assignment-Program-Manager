"""
ACGME Constraint Services.

This package provides ACGME compliance constraints as a service layer,
enabling constraint-based scheduling validation and optimization.

The constraints enforce ACGME (Accreditation Council for Graduate Medical
Education) requirements for resident duty hours, supervision, and schedules.

Modules:
    acgme: ACGME compliance constraints (80-hour rule, 1-in-7, supervision)

Example:
    >>> from backend.app.services.constraints import (
    ...     ACGMEConstraintValidator,
    ...     EightyHourRuleConstraint,
    ...     OneInSevenRuleConstraint,
    ...     SupervisionRatioConstraint,
    ... )
"""

from .acgme import (
    ACGMEConstraintValidator,
    AvailabilityConstraint,
    EightyHourRuleConstraint,
    OneInSevenRuleConstraint,
    SupervisionRatioConstraint,
)

__all__ = [
    "ACGMEConstraintValidator",
    "AvailabilityConstraint",
    "EightyHourRuleConstraint",
    "OneInSevenRuleConstraint",
    "SupervisionRatioConstraint",
]
