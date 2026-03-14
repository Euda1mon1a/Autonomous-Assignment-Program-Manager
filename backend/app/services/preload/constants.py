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
    "NF-PEDS-PGY": "NF-PEDS-PG",
    "NF-AM": "NF",
    "NF-PM": "NF",
    "NF-LD": "LDNF",
    "L&D NIGHT FLOAT": "LDNF",
    "L AND D NIGHT FLOAT": "LDNF",
    "KAPI": "KAP",
    "KAPI-LD": "KAP",
    "KAPI_LD": "KAP",
    "KAPI-LD-PG": "KAP",
    "KAPIOLANI": "KAP",
    "KAPIOLANI L AND D": "KAP",
    "MILITARY": "MIL",
    "MILITARY DUTY": "MIL",
    "OKINAWA": "OKI",
    "JAPAN OFF-SITE": "JAPAN",
    "JAPAN OFF-SITE ROTATION": "JAPAN",
    "PEDS EM": "PEDS-EM",
    "PEDIATRIC EMERGENCY MEDICINE": "PEDS-EM",
}

# Half-block NF combined rotations: abbreviation → specialty activity code.
# NF-first: Night Float days 1-14, specialty days 16-28.
NF_COMBINED_ACTIVITY_MAP: dict[str, str] = {
    "NF-CARDIO": "CARDS",
    "NF-FMIT-PG": "FMIT",
    "NF-DERM-PG": "DERM",
    "NF-PEDS-PG": "PEDW",
    "NF-NICU-PG": "NICU",
    "NF-1ST-END": "ENDO",
    "NF-MED-SEL": "SEL-MED",
}

# All combined NF codes for set membership checks.
_ALL_NF_COMBINED = set(NF_COMBINED_ACTIVITY_MAP)

NIGHT_FLOAT_ROTATIONS: set[str] = {
    "NF",
    "PEDNF",
    "LDNF",
} | _ALL_NF_COMBINED

# Legacy fallback: prefer DB column rotation_templates.is_lec_exempt
LEC_EXEMPT_ROTATIONS: set[str] = {
    "NF",
    "PEDNF",
    "LDNF",
    "TDY",
    "HILO",
    "OKI",
    "JAPAN",
    "PEDS-EM",
    "MIL",
} | _ALL_NF_COMBINED

# Legacy fallback: prefer DB column rotation_templates.is_continuity_exempt
INTERN_CONTINUITY_EXEMPT_ROTATIONS: set[str] = {
    "NF",
    "PEDNF",
    "LDNF",
    "TDY",
    "HILO",
    "OKI",
    "KAP",
    "JAPAN",
    "PEDS-EM",
    "MIL",
} | _ALL_NF_COMBINED

# Legacy fallback: prefer DB column rotation_templates.is_offsite
OFFSITE_ROTATIONS: set[str] = {"TDY", "HILO", "OKI", "JAPAN", "PEDS-EM", "MIL"}
KAP_ROTATIONS: set[str] = {"KAP"}
CLINIC_PATTERN_CODES: set[str] = {"C", "C-I", "C-N", "FM_CLINIC"}

# Legacy fallback: prefer DB column rotation_templates.is_saturday_off
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
    "MIL",
    "NF",
} | _ALL_NF_COMBINED

# Rotation types that require translation to activity codes
ROTATION_TO_ACTIVITY: dict[str, str] = {
    "HILO": "TDY",
    "FMC": "fm_clinic",
    "JAPAN": "TDY",
    "PEDS-EM": "PEM",
}


# ---------------------------------------------------------------------------
# DB-backed classification helpers (fallback to Python constants)
# ---------------------------------------------------------------------------


def get_lec_exempt_codes(db_session=None) -> set[str]:
    """Get LEC-exempt rotation codes from DB, with Python fallback.

    Queries rotation_templates.is_lec_exempt when a DB session is provided.
    Falls back to the hardcoded LEC_EXEMPT_ROTATIONS set otherwise.
    """
    if db_session is not None:
        from app.models.rotation_template import RotationTemplate

        rows = (
            db_session.query(RotationTemplate.abbreviation)
            .filter(
                RotationTemplate.is_lec_exempt == True,  # noqa: E712
                RotationTemplate.is_archived == False,  # noqa: E712
            )
            .all()
        )
        if rows:
            return {r.abbreviation for r in rows if r.abbreviation}
    return LEC_EXEMPT_ROTATIONS  # fallback


def get_continuity_exempt_codes(db_session=None) -> set[str]:
    """Get intern-continuity-exempt rotation codes from DB, with Python fallback.

    Queries rotation_templates.is_continuity_exempt when a DB session is provided.
    Falls back to the hardcoded INTERN_CONTINUITY_EXEMPT_ROTATIONS set otherwise.
    """
    if db_session is not None:
        from app.models.rotation_template import RotationTemplate

        rows = (
            db_session.query(RotationTemplate.abbreviation)
            .filter(
                RotationTemplate.is_continuity_exempt == True,  # noqa: E712
                RotationTemplate.is_archived == False,  # noqa: E712
            )
            .all()
        )
        if rows:
            return {r.abbreviation for r in rows if r.abbreviation}
    return INTERN_CONTINUITY_EXEMPT_ROTATIONS  # fallback


def get_offsite_codes(db_session=None) -> set[str]:
    """Get offsite rotation codes from DB, with Python fallback.

    Queries rotation_templates.is_offsite when a DB session is provided.
    Falls back to the hardcoded OFFSITE_ROTATIONS set otherwise.
    """
    if db_session is not None:
        from app.models.rotation_template import RotationTemplate

        rows = (
            db_session.query(RotationTemplate.abbreviation)
            .filter(
                RotationTemplate.is_offsite == True,  # noqa: E712
                RotationTemplate.is_archived == False,  # noqa: E712
            )
            .all()
        )
        if rows:
            return {r.abbreviation for r in rows if r.abbreviation}
    return OFFSITE_ROTATIONS  # fallback


def get_saturday_off_codes(db_session=None) -> set[str]:
    """Get Saturday-off rotation codes from DB, with Python fallback.

    Queries rotation_templates.is_saturday_off when a DB session is provided.
    Falls back to the hardcoded SATURDAY_OFF_ROTATIONS set otherwise.
    """
    if db_session is not None:
        from app.models.rotation_template import RotationTemplate

        rows = (
            db_session.query(RotationTemplate.abbreviation)
            .filter(
                RotationTemplate.is_saturday_off == True,  # noqa: E712
                RotationTemplate.is_archived == False,  # noqa: E712
            )
            .all()
        )
        if rows:
            return {r.abbreviation for r in rows if r.abbreviation}
    return SATURDAY_OFF_ROTATIONS  # fallback


def canonical_rotation_code(raw_code: str | None) -> str:
    """Normalize a rotation code for matching."""
    code = (raw_code or "").strip().upper()
    if not code:
        return ""
    # Preserve combined NF codes — they are canonical already.
    if code in NF_COMBINED_ACTIVITY_MAP:
        return code
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
    if (
        code.startswith("FMIT-PGY")
        or code.startswith("FMIT-R")
        or code.startswith("FMIT-FAC")
    ):
        return "FMIT"
    if code.startswith("PEDS-WARD"):
        return "PEDW"
    if code.startswith("NF-PEDS"):
        # Check if alias maps to a combined code (e.g., NF-PEDS-PGY → NF-PEDS-PG)
        aliased = ROTATION_ALIASES.get(code)
        if aliased and aliased in NF_COMBINED_ACTIVITY_MAP:
            return aliased
        return "PEDNF"
    if code.startswith("IM-PGY"):
        return "IM"
    return ROTATION_ALIASES.get(code, code)
