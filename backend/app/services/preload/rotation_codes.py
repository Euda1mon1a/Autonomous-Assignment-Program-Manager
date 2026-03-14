"""Rotation code determination — pure functions for AM/PM activity code selection.

These functions determine what activity codes should be preloaded for a given
rotation type + date combination. They are used by both the sync and async
preload services.
"""

from __future__ import annotations

from datetime import date, timedelta

from .constants import (
    INTERN_CONTINUITY_EXEMPT_ROTATIONS,
    KAP_ROTATIONS,
    LEC_EXEMPT_ROTATIONS,
    NF_COMBINED_ACTIVITY_MAP,
    OFFSITE_ROTATIONS,
    ROTATION_TO_ACTIVITY,
    SATURDAY_OFF_ROTATIONS,
)
from .date_helpers import is_last_wednesday


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


def is_lec_exempt(rotation_code: str) -> bool:
    return rotation_code in LEC_EXEMPT_ROTATIONS


def is_intern_continuity_exempt(rotation_code: str) -> bool:
    return rotation_code in INTERN_CONTINUITY_EXEMPT_ROTATIONS


# ---------------------------------------------------------------------------
# Day-specific rotation code patterns
# ---------------------------------------------------------------------------


def get_kap_codes(current_date: date) -> tuple[str, str]:
    """Kapiolani L&D pattern."""
    dow = current_date.weekday()
    if dow == 0:  # Monday
        return ("KAP", "OFF")
    if dow == 1:  # Tuesday
        return ("OFF", "OFF")
    if dow == 2:  # Wednesday
        return ("C", "LEC")
    return ("KAP", "KAP")


def get_ldnf_codes(current_date: date) -> tuple[str, str]:
    """L&D Night Float pattern with Friday clinic."""
    dow = current_date.weekday()
    if dow == 4:  # Friday
        return ("C", "OFF")
    if dow >= 5:  # Weekend
        return ("W", "W")
    return ("OFF", "LDNF")


def get_nf_codes(rotation_code: str, current_date: date) -> tuple[str, str]:
    """Night Float pattern (NF/PedNF)."""
    dow = current_date.weekday()
    if rotation_code == "PEDNF":
        if dow == 5:  # Saturday off only
            return ("W", "W")
        return ("OFF", "PedNF")
    if dow >= 5:
        return ("W", "W")
    return ("OFF", "NF")


def get_hilo_codes(
    current_date: date, block_start: date, block_end: date
) -> tuple[str, str]:
    """Hilo/Okinawa TDY pattern with pre/post clinic days.

    Pattern:
      - Days 0-1 (block start): Clinic before departure
      - Monday and Tuesday before block end: Clinic on return
      - All other weekdays: TDY
    """
    day_index = (current_date - block_start).days
    if day_index in (0, 1):  # Thu/Fri before leaving
        return ("C", "C")
    # Return clinic = Monday and Tuesday before block ends
    # Find the last Monday on or before block_end
    last_monday = block_end - timedelta(days=(block_end.weekday() - 0) % 7)
    if last_monday > block_end:
        last_monday -= timedelta(days=7)
    last_tuesday = last_monday + timedelta(days=1)
    if current_date in (last_monday, last_tuesday):
        return ("C", "C")
    return ("TDY", "TDY")


# ---------------------------------------------------------------------------
# Main rotation code functions (used by different preload phases)
# ---------------------------------------------------------------------------


def get_rotation_codes(
    rotation_type: object,
    current_date: date,
    *,
    person: object = None,
    has_time_off_patterns: bool = False,
) -> tuple[str, str]:
    """Get AM/PM activity codes for inpatient rotations based on day of week.

    Used by ``_load_inpatient_preloads`` to determine what gets preloaded
    for each day of an inpatient rotation.

    Args:
        rotation_type: InpatientRotationType enum or string rotation code.
        current_date: The date being processed.
        person: Person model (for PGY-level Saturday rules).
        has_time_off_patterns: Whether GUI time-off patterns exist.
    """
    if rotation_type is None:
        return ("FMIT", "FMIT")

    dow = current_date.weekday()

    code_raw = rotation_type.value if hasattr(rotation_type, "value") else rotation_type
    code_str = str(code_raw) if code_raw is not None else ""
    code_upper = code_str.strip().upper()

    person_type = getattr(person, "type", None)
    pgy_level = (
        getattr(person, "pgy_level", None) if person_type == "resident" else None
    )

    # Resident-only Saturday/Sunday off rules (temporary P6-2 defaults).
    # GUI patterns override these defaults when has_time_off_patterns=True.
    if person_type == "resident" and not has_time_off_patterns:
        if code_upper == "FMIT":
            if dow == 5 and pgy_level in (1, 2):
                return ("W", "W")
            if dow == 6 and pgy_level == 3:
                return ("W", "W")
        if dow == 5 and code_upper in SATURDAY_OFF_ROTATIONS:
            return ("W", "W")

    if code_upper == "KAP":
        if dow == 0:
            return ("KAP", "OFF")
        elif dow == 1:
            return ("OFF", "OFF")
        elif dow == 2:
            return ("C", "LEC")
        else:
            return ("KAP", "KAP")

    if code_upper == "LDNF":
        if dow == 4:
            return ("C", "OFF")
        elif dow >= 5:
            if not has_time_off_patterns:
                return ("W", "W")
            return ("OFF", "LDNF")
        else:
            return ("OFF", "LDNF")

    if code_upper == "NF":
        if dow >= 5:
            if not has_time_off_patterns:
                return ("W", "W")
            return ("OFF", "NF")
        else:
            return ("OFF", "NF")

    if code_upper == "PEDNF":
        if dow == 5:
            if not has_time_off_patterns:
                return ("W", "W")
            return ("OFF", "PedNF")
        return ("OFF", "PedNF")

    mapped = ROTATION_TO_ACTIVITY.get(code_upper, code_str)
    mapped_str = str(mapped) if mapped is not None else ""
    return (mapped_str, mapped_str)


def get_rotation_preload_codes(
    rotation_code: str,
    current_date: date,
    block_start: date,
    block_end: date,
    pgy_level: int,
    is_outpatient: bool,
    has_time_off_patterns: bool = False,
    template=None,
) -> tuple[str | None, str | None]:
    """Return AM/PM activity codes for rotation-protected preloads.

    Used by ``_load_rotation_protected_preloads`` to determine what gets
    preloaded for each date of a block assignment.

    When ``template`` is provided, reads classification flags from the DB
    (is_offsite, is_lec_exempt, is_saturday_off, preload_activity_code)
    instead of hardcoded Python constants.
    """
    if not rotation_code:
        return (None, None)

    # DB-driven classification (preferred) vs Python fallback
    _is_lec_exempt = (
        template.is_lec_exempt
        if template and hasattr(template, "is_lec_exempt")
        else is_lec_exempt(rotation_code)
    )
    _is_saturday_off = (
        template.is_saturday_off
        if template and hasattr(template, "is_saturday_off")
        else rotation_code in SATURDAY_OFF_ROTATIONS
    )
    _is_continuity_exempt = (
        template.is_continuity_exempt
        if template and hasattr(template, "is_continuity_exempt")
        else is_intern_continuity_exempt(rotation_code)
    )
    _preload_code = (
        template.preload_activity_code
        if template and hasattr(template, "preload_activity_code")
        else None
    )

    # Last Wednesday: LEC/ADV for all (unless lec-exempt)
    if is_last_wednesday(current_date, block_end) and not _is_lec_exempt:
        return ("LEC", "ADV")

    # Saturday off
    if current_date.weekday() == 5 and _is_saturday_off and not has_time_off_patterns:
        return ("W", "W")

    # NF-combined rotations (complex day-of-week logic, stays hardcoded for now)
    if rotation_code in NF_COMBINED_ACTIVITY_MAP:
        dow = current_date.weekday()
        mid_block_date = block_start + timedelta(days=14)

        if dow == 2:  # Wednesday
            return ("OFF", "LEC")

        if current_date == mid_block_date:
            return ("recovery", "recovery")

        if dow == 6:  # Sunday
            return ("W", "W")

        if current_date < mid_block_date:
            return ("OFF", "NF")
        else:
            specialty = NF_COMBINED_ACTIVITY_MAP[rotation_code]
            return (specialty, specialty)

    # DB-driven simple preload: fill all slots with preload_activity_code
    if _preload_code:
        dow = current_date.weekday()
        if dow == 6:  # Sunday always off
            return ("W", "W")
        if dow == 5 and _is_saturday_off:
            return ("W", "W")
        return (_preload_code, _preload_code)

    # Fallback: complex patterns not yet in DB (KAP day-of-week, HILO pre/post)
    if rotation_code in KAP_ROTATIONS:
        return get_kap_codes(current_date)

    if rotation_code == "LDNF":
        return get_ldnf_codes(current_date)

    if rotation_code in ("NF", "PEDNF"):
        return get_nf_codes(rotation_code, current_date)

    # Wednesday protected patterns (intern continuity only for outpatient)
    if current_date.weekday() == 2:  # Wednesday
        am_code = None
        if is_outpatient and pgy_level == 1 and not _is_continuity_exempt:
            am_code = "C"

        pm_code = None
        if not _is_lec_exempt:
            pm_code = "LEC"

        return (am_code, pm_code)

    return (None, None)
