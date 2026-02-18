"""Preload constants — rotation aliases, classification sets, and mapping rules.

These constants are shared between the sync and async preload services.
"""

from __future__ import annotations

# Rotation normalization: maps variant spellings → canonical code
ROTATION_ALIASES: dict[str, str] = {
    "PNF": "PEDNF",
    "PEDS NF": "PEDNF",
    "PEDS NIGHT FLOAT": "PEDNF",
    "PEDIATRICS NIGHT FLOAT": "PEDNF",
    "L&D NIGHT FLOAT": "LDNF",
    "L AND D NIGHT FLOAT": "LDNF",
    "KAPI": "KAP",
    "KAPI-LD": "KAP",
    "KAPI_LD": "KAP",
    "KAPIOLANI": "KAP",
    "KAPIOLANI L AND D": "KAP",
    "OKINAWA": "OKI",
}

NIGHT_FLOAT_ROTATIONS: set[str] = {"NF", "PEDNF", "LDNF"}
LEC_EXEMPT_ROTATIONS: set[str] = {"NF", "PEDNF", "LDNF", "TDY", "HILO", "OKI"}
INTERN_CONTINUITY_EXEMPT_ROTATIONS: set[str] = {
    "NF",
    "PEDNF",
    "LDNF",
    "TDY",
    "HILO",
    "OKI",
    "KAP",
}
OFFSITE_ROTATIONS: set[str] = {"TDY", "HILO", "OKI"}
KAP_ROTATIONS: set[str] = {"KAP"}
CLINIC_PATTERN_CODES: set[str] = {"C", "C-I", "C-N", "FM_CLINIC"}

# Temporary Saturday-off rules for external/inpatient rotations (P6-2).
SATURDAY_OFF_ROTATIONS: set[str] = {
    "IM",
    "IMW",
    "PEDW",
    "PEDNF",
    "ICU",
    "CCU",
    "NICU",
    "NIC",
    "NBN",
    "LAD",
    "LND",
    "LD",
    "L&D",
    "KAP",
    "HILO",
    "OKI",
    "TDY",
}

# Rotation types that require translation to activity codes
ROTATION_TO_ACTIVITY: dict[str, str] = {
    "HILO": "TDY",
    "FMC": "fm_clinic",
}


def canonical_rotation_code(raw_code: str | None) -> str:
    """Normalize a rotation code for matching."""
    code = (raw_code or "").strip().upper()
    if not code:
        return ""
    if code.startswith("HILO"):
        return "HILO"
    if code.startswith("OKI"):
        return "OKI"
    if code.startswith("KAPI"):
        return "KAP"
    return ROTATION_ALIASES.get(code, code)
