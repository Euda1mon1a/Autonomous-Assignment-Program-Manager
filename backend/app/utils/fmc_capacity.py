"""Helpers for FMC physical capacity calculations."""

from __future__ import annotations

from typing import Iterable

from app.models.activity import Activity
from app.models.half_day_assignment import HalfDayAssignment


def _normalize_code(code: str | None) -> str:
    return (code or "").strip().upper()


# Activities that consume FMC physical capacity (room/screener constraint).
# CV (virtual clinic) explicitly excluded.
FMC_CAPACITY_CODES = {
    "C",
    "C-N",
    "C-I",
    "FM_CLINIC",
    "V1",
    "V2",
    "V3",
    "PROC",
    "PR",
    "PROCEDURE",
    "VAS",
    "SM",
    "SM_CLINIC",
    "ASM",
}

SM_CAPACITY_CODES = {"SM", "SM_CLINIC", "ASM"}

PROC_VAS_CODES = {"PR", "PROC", "PROCEDURE", "VAS"}


def activity_is_sm_capacity(activity: Activity | None) -> bool:
    if not activity:
        return False
    code = _normalize_code(activity.code)
    return code in SM_CAPACITY_CODES


def activity_is_proc_or_vas(activity: Activity | None) -> bool:
    if not activity:
        return False
    code = _normalize_code(activity.code)
    return code in PROC_VAS_CODES


def activity_counts_toward_fmc_capacity(activity: Activity | None) -> bool:
    if not activity:
        return False
    code = _normalize_code(activity.code)
    return code in FMC_CAPACITY_CODES


def assignment_counts_toward_fmc_capacity(assignment: HalfDayAssignment) -> bool:
    """Return True if the assignment should count toward FMC capacity."""
    if assignment.counts_toward_fmc_capacity is not None:
        return bool(assignment.counts_toward_fmc_capacity)
    return activity_counts_toward_fmc_capacity(assignment.activity)


def slot_fmc_capacity(assignments: Iterable[HalfDayAssignment]) -> int:
    """Count FMC capacity units for a slot, with SM counted once per slot."""
    non_sm = 0
    sm_present = False
    for assignment in assignments:
        activity = assignment.activity
        if activity_is_sm_capacity(activity):
            if assignment_counts_toward_fmc_capacity(assignment):
                sm_present = True
            continue
        if assignment_counts_toward_fmc_capacity(assignment):
            non_sm += 1
    return non_sm + (1 if sm_present else 0)
