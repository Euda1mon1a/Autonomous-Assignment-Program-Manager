"""Activity locking helpers for source priority decisions.

Centralizes the rule: preloaded/protected activities must be locked
(source=preload), while all other activities can be solver/template.
"""

from __future__ import annotations

from typing import Iterable

from app.models.activity import Activity

# Activity codes/abbreviations that must be locked (never overwritten).
# Derived from tamc-scheduling.skill "Preload Codes (Never Overwrite)".
_LOCKED_CODES = {
    "FMIT",
    "LV",
    "LV-AM",
    "LV-PM",
    "W",
    "W-AM",
    "W-PM",
    "PC",
    "PCAT",
    "DO",
    "LEC",
    "LEC-PM",
    "ADV",
    "SIM",
    "HAFP",
    "USAFP",
    "BLS",
    "DEP",
    "PI",
    "MM",
    "HOL",
    "TDY",
    "CCC",
    "ORIENT",
    "OFF",
    "OFF-AM",
    "OFF-PM",
}


def _normalize_code(code: str | None) -> str:
    """Normalize activity codes/abbreviations for comparisons."""
    return (code or "").strip().upper()


def is_activity_preloaded(activity: Activity | None) -> bool:
    """Return True if this activity should be locked as preload.

    Rules (first principles):
    - time_off activities are locked
    - protected activities are locked
    - known preload codes are locked
    """
    if activity is None:
        return False

    if activity.activity_category == "time_off":
        return True

    if activity.is_protected:
        return True

    code = _normalize_code(activity.code)
    abbrev = _normalize_code(activity.display_abbreviation)
    return code in _LOCKED_CODES or abbrev in _LOCKED_CODES


# Activity codes that should block solver rotation assignment.
# These represent absences, off-site/inpatient rotations, or post-call protection.
_BLOCKING_CODES = {
    "FMIT",
    "NF",
    "PEDNF",
    "LDNF",
    "KAP",
    "KAPI-LD",
    "KAPI_LD",
    "IM",
    "PEDW",
    "PNF",
    "TDY",
    "DEP",
    "LV",
    "OFF",
    "W",
    "HOL",
    "PC",
    "PCAT",
    "DO",
}


def _base_code(code: str | None) -> str:
    """Normalize and strip AM/PM suffixes."""
    normalized = _normalize_code(code)
    if normalized.endswith("-AM") or normalized.endswith("-PM"):
        return normalized[:-3]
    return normalized


def is_activity_blocking_for_solver(activity: Activity | None) -> bool:
    """
    Return True if this activity should block solver rotation assignment.

    Blocking means the solver should not assign a rotation template to that slot.
    """
    if activity is None:
        return False

    if activity.activity_category == "time_off":
        return True

    code = _base_code(activity.code)
    abbrev = _base_code(activity.display_abbreviation)
    return code in _BLOCKING_CODES or abbrev in _BLOCKING_CODES


def is_code_preloaded(code: str | None) -> bool:
    """Return True if a raw code/abbrev is in the locked preload list."""
    return _normalize_code(code) in _LOCKED_CODES


def preload_codes() -> Iterable[str]:
    """Expose locked codes for diagnostics/tests."""
    return sorted(_LOCKED_CODES)
