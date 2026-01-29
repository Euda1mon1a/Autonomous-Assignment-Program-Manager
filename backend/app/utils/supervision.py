"""Helpers for FMC supervision ratio logic (AT/PCAT coverage)."""

from __future__ import annotations

from app.models.activity import Activity
from app.models.half_day_assignment import HalfDayAssignment
from app.utils.fmc_capacity import (
    activity_counts_toward_fmc_capacity,
    assignment_counts_toward_fmc_capacity,
)


def _normalize_code(code: str | None) -> str:
    return (code or "").strip().upper()


def activity_is_virtual_clinic(activity: Activity | None) -> bool:
    if not activity:
        return False
    code = _normalize_code(activity.code)
    display = _normalize_code(activity.display_abbreviation)
    return code == "CV" or display == "CV"


def activity_provides_supervision(activity: Activity | None) -> bool:
    """Return True if activity provides supervision (AT/PCAT only)."""
    if not activity:
        return False
    return activity.is_supervision


def activity_requires_fmc_supervision(activity: Activity | None) -> bool:
    """Return True if activity requires FMC supervision coverage."""
    if not activity:
        return False
    if activity_provides_supervision(activity):
        return False
    if activity_is_virtual_clinic(activity):
        return True
    return activity_counts_toward_fmc_capacity(activity)


def assignment_requires_fmc_supervision(
    assignment: HalfDayAssignment | None,
) -> bool:
    """Return True if assignment requires FMC supervision coverage."""
    if not assignment or not assignment.activity:
        return False
    if activity_provides_supervision(assignment.activity):
        return False
    if activity_is_virtual_clinic(assignment.activity):
        return True
    return assignment_counts_toward_fmc_capacity(assignment)
