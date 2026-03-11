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
    "NF-PEDS-PG": "PEDNF",
    "NF-PEDS-PGY": "PEDNF",
    "NF-LD": "LDNF",
    "L&D NIGHT FLOAT": "LDNF",
    "L AND D NIGHT FLOAT": "LDNF",
    "KAPI": "KAP",
    "KAPI-LD": "KAP",
    "KAPI_LD": "KAP",
    "KAPIOLANI": "KAP",
    "KAPIOLANI L AND D": "KAP",
    "OKINAWA": "OKI",
    "JAPAN OFF-SITE": "JAPAN",
    "JAPAN OFF-SITE ROTATION": "JAPAN",
    "PEDS EM": "PEDS-EM",
    "PEDIATRIC EMERGENCY MEDICINE": "PEDS-EM",
    "D+N": "DERM-NF",
    "C+N": "CARDS-NF",
}

NIGHT_FLOAT_ROTATIONS: set[str] = {
    "NF",
    "PEDNF",
    "LDNF",
    "NF-CARDIO",
    "NF-FMIT-PG",
    "NF-DERM-PG",
    "CARDS-NF",
    "DERM-NF",
    "FMIT-NF-PG",
}
LEC_EXEMPT_ROTATIONS: set[str] = {
    "NF",
    "PEDNF",
    "LDNF",
    "NF-CARDIO",
    "NF-FMIT-PG",
    "NF-DERM-PG",
    "CARDS-NF",
    "DERM-NF",
    "FMIT-NF-PG",
    "TDY",
    "HILO",
    "OKI",
    "JAPAN",
    "PEDS-EM",
}
INTERN_CONTINUITY_EXEMPT_ROTATIONS: set[str] = {
    "NF",
    "PEDNF",
    "LDNF",
    "NF-CARDIO",
    "NF-FMIT-PG",
    "NF-DERM-PG",
    "CARDS-NF",
    "DERM-NF",
    "FMIT-NF-PG",
    "TDY",
    "HILO",
    "OKI",
    "KAP",
    "JAPAN",
    "PEDS-EM",
}
OFFSITE_ROTATIONS: set[str] = {"TDY", "HILO", "OKI", "JAPAN", "PEDS-EM"}
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
    "JAPAN",
    "PEDS-EM",
    "NF-CARDIO",
    "NF-FMIT-PG",
    "NF-DERM-PG",
    "CARDS-NF",
    "DERM-NF",
    "FMIT-NF-PG",
}

# Rotation types that require translation to activity codes
ROTATION_TO_ACTIVITY: dict[str, str] = {
    "HILO": "TDY",
    "FMC": "fm_clinic",
    "JAPAN": "TDY",
    "PEDS-EM": "PEM",
}

# Half-block NF combined rotations: abbreviation → specialty activity code.
# NF-first: Night Float days 1-14, specialty days 16-28.
NF_COMBINED_ACTIVITY_MAP: dict[str, str] = {
    "NF-CARDIO": "CARDS",
    "NF-FMIT-PG": "FMIT",
    "NF-DERM-PG": "DERM",
}

# Mirror (specialty-first) combined rotations: specialty days 1-14, NF days 16-28.
# These pair with NF-first templates to ensure continuous NF coverage.
# Codes use "-NF" suffix (not "+N") because canonical_rotation_code rewrites
# D+N → DERM-NF and C+N → CARDS-NF to prevent the "+" split in
# _resolve_rotation_code_for_date.
REVERSE_NF_COMBINED_MAP: dict[str, str] = {
    "CARDS-NF": "CARDS",
    "DERM-NF": "DERM",
    "FMIT-NF-PG": "FMIT",
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
    if code.startswith("JAPAN"):
        return "JAPAN"
    if code.startswith("PEDS-EM") or code.startswith("PEDS EM"):
        return "PEDS-EM"
    if code.startswith("FMIT-PGY") or code.startswith("FMIT-R"):
        return "FMIT"
    if code.startswith("PEDS-WARD"):
        return "PEDW"
    if code.startswith("NF-PEDS"):
        return "PEDNF"
    return ROTATION_ALIASES.get(code, code)
