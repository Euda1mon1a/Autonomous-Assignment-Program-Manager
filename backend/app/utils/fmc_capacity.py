"""Helpers for FMC physical capacity calculations."""

from __future__ import annotations

from typing import Iterable

from app.models.activity import Activity
from app.models.half_day_assignment import HalfDayAssignment
from app.models.rotation_template import RotationTemplate


def _normalize_code(code: str | None) -> str:
    return (code or "").strip().upper()


# Templates that represent FMC continuity clinic.
FMC_TEMPLATE_ABBREVS = {"C", "C-AM", "C-PM", "CONT", "CONTINUITY"}

# Clinic activity codes that *may* represent FMC continuity depending on template.
FMC_CLINIC_CODES = {"C", "C-N", "C-I", "FM_CLINIC"}

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

CV_CODES = {"CV"}

SM_CAPACITY_CODES = {"SM", "SM_CLINIC", "ASM"}

PROC_VAS_CODES = {"PR", "PROC", "PROCEDURE", "VAS"}


def activity_is_sm_capacity(activity: Activity | None) -> bool:
    if not activity:
        return False
    code = _normalize_code(activity.code)
    display = _normalize_code(activity.display_abbreviation)
    return code in SM_CAPACITY_CODES or display in SM_CAPACITY_CODES


def activity_is_proc_or_vas(activity: Activity | None) -> bool:
    if not activity:
        return False
    code = _normalize_code(activity.code)
    display = _normalize_code(activity.display_abbreviation)
    return code in PROC_VAS_CODES or display in PROC_VAS_CODES


def template_is_fmc_clinic(template: RotationTemplate | None) -> bool:
    if not template:
        return False
    abbrev = (template.display_abbreviation or template.abbreviation or "").strip()
    return abbrev.upper() in FMC_TEMPLATE_ABBREVS


def activity_counts_toward_fmc_capacity_for_template(
    activity: Activity | None, template: RotationTemplate | None
) -> bool:
    if not activity:
        return False
    units = getattr(activity, "capacity_units", None)
    if units is not None and units <= 0:
        return False
    code = _normalize_code(activity.code)
    display = _normalize_code(activity.display_abbreviation)
    if code in CV_CODES or display in CV_CODES:
        return False
    if activity_is_sm_capacity(activity):
        return True
    if activity_is_proc_or_vas(activity):
        return True
    if code in {"V1", "V2", "V3"} or display in {"V1", "V2", "V3"}:
        return True
    if code in FMC_CLINIC_CODES or display in FMC_CLINIC_CODES:
        return template_is_fmc_clinic(template)
    return False


def activity_counts_toward_fmc_capacity(activity: Activity | None) -> bool:
    if not activity:
        return False
    units = getattr(activity, "capacity_units", None)
    if units is not None and units <= 0:
        return False
    code = _normalize_code(activity.code)
    display = _normalize_code(activity.display_abbreviation)
    if code in CV_CODES or display in CV_CODES:
        return False
    return code in FMC_CAPACITY_CODES


def activity_capacity_units(activity: Activity | None) -> int:
    """Return capacity units for an activity (defaults to 1)."""
    if not activity:
        return 0
    units = getattr(activity, "capacity_units", None)
    if units is None:
        return 1
    try:
        return max(0, int(units))
    except (TypeError, ValueError):
        return 1


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
            non_sm += activity_capacity_units(activity)
    return non_sm + (1 if sm_present else 0)
