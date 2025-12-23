"""
Constraint Services Module.

This package provides ACGME compliance constraints and faculty constraint
services with caching, authorization, and validation support.

The constraints enforce ACGME (Accreditation Council for Graduate Medical
Education) requirements for resident duty hours, supervision, and schedules.

Modules:
    acgme: ACGME compliance constraints (80-hour rule, 1-in-7, supervision)
    faculty: Faculty preference and constraint services with caching

Example:
    >>> from backend.app.services.constraints import (
    ...     ACGMEConstraintValidator,
    ...     EightyHourRuleConstraint,
    ...     FacultyConstraintService,
    ... )
"""

from app.services.constraints.faculty import (
    CachedFacultyPreferenceService,
    FacultyConstraintService,
)

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
    "CachedFacultyPreferenceService",
    "FacultyConstraintService",
]
