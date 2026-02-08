"""Schedule display rules — learned from handjam ground truth.

These rules transform raw DB activity codes into the display codes that
appear in the handjam Excel workbook. Discovered via pattern extraction:

    handjam (ground truth) <-diff-> DB export -> transformation rules

The coordinator applies these rules implicitly when filling the schedule.
This module codifies them so the export can match.

Architecture:
    DB activity code + context (rotation, day, absence) -> display code

Rules are organized by category:
    1. Night float: OFF -> rotation code for NF-type rotations
    2. Weekend overrides: W -> rotation-specific code for certain rotations
    3. Rotation clinic: C -> rotation-specific clinic code
    4. Faculty weekends: GME/CV/DFM/SM -> W on weekends
    5. Code normalization: spelling/abbreviation fixes (IM->IMW, etc.)
    6. Absence mapping: LV -> specific absence type (DEP, USAFP, TDY)
    7. NF code -> rotation-specific NF display code
"""

from __future__ import annotations

from datetime import date
from typing import Any


# ── Rule 1: Night float OFF -> rotation-specific display code ─────────
# When a resident on a night-float rotation has "OFF" during the day,
# the handjam shows their rotation code instead of OFF.
# Keyed by rotation abbreviation fragment (matched against rot1/rot2).
# Order matters: longer/more specific keys checked first.
_NF_ROTATION_MAP: list[tuple[str, str]] = [
    # (rotation_fragment, display_code)  — checked in order
    ("LDNF", "L&D"),  # L&D Night Float
    ("PEDSNF", "PedsNF"),  # Peds Night Float
    ("PEDNF", "PedsNF"),  # Peds Night Float (alt)
    ("PNF", "PedsNF"),  # Peds Night Float (short)
    ("PEDSW", "PedsNF"),  # Peds Ward also does NF (secondary)
    ("NF/ENDO", "NF"),  # NF with Endo secondary
    ("NF", "NF"),  # Generic NF (MUST be last — substring of others)
]

# Neuro rotation with NF component
_NEURO_NF_TAGS = {"NEURO", "NEURO/NF"}


# ── Rule 2: Weekend overrides by rotation ─────────────────────────────
# Certain rotations show their rotation code on weekends instead of "W"
WEEKEND_ROTATION_OVERRIDES: dict[str, str] = {
    "FMIT": "FMIT",
    "IMW": "IMW",
    "KAP": "KAP",
}


# ── Rule 3: Rotation-specific clinic codes ────────────────────────────
# When DB shows generic "C" (fm_clinic), handjam shows the rotation-
# specific clinic code. Only applied when the mapping is >80% consistent
# in the ground truth data.
ROTATION_CLINIC_MAP: dict[str, str] = {
    "GYN": "GYN",  # 11/11 = 100%
    "SM": "SM",  # 13/21 = 62% (borderline, but dominant)
    # POCUS: C->US only 9/20 = 45% — too ambiguous, removed
    # PROC: C->PR only 7/17 = 41% — too ambiguous, removed
    # FMC: C maps to CC, C40, PR, ADM etc. — not deterministic
    # Surg Exp: C maps to Ophtho, URO, ENT etc. — day-specific
}


# ── Rule 4: Faculty weekend collapse ──────────────────────────────────
# Faculty educational/administrative codes collapse to "W" on weekends.
FACULTY_WEEKEND_COLLAPSE: set[str] = {
    "GME",
    "CV",
    "DFM",
    "SM",
    "LEC",
    "ADV",
    "AT",
    "DO",
}


# ── Rule 5: Code normalization ────────────────────────────────────────
# Simple 1:1 display code fixes where DB abbreviation differs from handjam.
CODE_NORMALIZATION: dict[str, str] = {
    "IM": "IMW",
    "LDNF": "L&D",
    "PedNF": "PedsNF",
}


# ── Rule 6: Absence type mapping (requires absence data) ─────────────
# The handjam shows specific absence codes instead of generic "LV"
ABSENCE_TYPE_MAP: dict[str, str] = {
    "deployment": "DEP",
    "tdy": "TDY",
    "usafp": "USAFP",
    # Regular leave stays as "LV"
}


# ── Rule 7: Generic NF code -> rotation-specific NF display code ──────
# The DB often assigns the generic "NF" activity code to all NF-type
# rotations. The handjam distinguishes: L&D NF shows "L&D", Peds NF
# shows "PedsNF", etc. This rule maps generic NF -> specific display.
# Uses the same rotation map as Rule 1.


def transform_code(
    db_code: str,
    *,
    rotation: str = "",
    rotation2: str = "",
    is_weekend: bool = False,
    is_faculty: bool = False,
    absence_type: str | None = None,
    day_date: date | None = None,
) -> str:
    """Transform a DB activity code into handjam display code.

    Args:
        db_code: Raw activity code from DB (already display_abbreviation)
        rotation: Primary rotation name/abbreviation
        rotation2: Secondary rotation name/abbreviation
        is_weekend: Whether this is a Saturday or Sunday
        is_faculty: Whether this person is faculty
        absence_type: If person has an absence, the type (deployment, tdy, etc.)
        day_date: The date for this cell

    Returns:
        Transformed display code matching handjam conventions.
    """
    if not db_code:
        return db_code

    code = db_code.strip()
    rot = rotation.strip().upper() if rotation else ""
    rot2 = rotation2.strip().upper() if rotation2 else ""

    # Rule 6: Absence override (highest priority)
    if absence_type and code == "LV":
        mapped = ABSENCE_TYPE_MAP.get(absence_type.lower())
        if mapped:
            return mapped

    # Rule 5: Code normalization (simple spelling fixes)
    if code in CODE_NORMALIZATION:
        code = CODE_NORMALIZATION[code]

    # Rule 7: Generic NF code -> rotation-specific NF display code
    # Only when the person is NOT on a generic NF rotation
    if code == "NF":
        specific = _rotation_specific_nf(rot, rot2)
        if specific and specific != "NF":
            return specific

    # Rule 1: Night float OFF -> rotation code
    if code == "OFF":
        nf_code = _rotation_specific_nf(rot, rot2)
        if nf_code:
            return nf_code

    # Rule 2: Weekend overrides
    if is_weekend and code == "W":
        # Check NF-type rotations first
        nf_code = _rotation_specific_nf(rot, rot2)
        if nf_code:
            return nf_code

        # Check rotation-specific weekend overrides
        for rot_key, display in WEEKEND_ROTATION_OVERRIDES.items():
            if rot_key in rot:
                return display

    # Rule 4: Faculty weekend collapse
    if is_faculty and is_weekend and code in FACULTY_WEEKEND_COLLAPSE:
        return "W"

    # Rule 3: Rotation-specific clinic code
    if code == "C":
        for rot_key, clinic_code in ROTATION_CLINIC_MAP.items():
            if rot_key.upper() in rot or rot_key.upper() in rot2:
                return clinic_code

    return code


def _rotation_specific_nf(rot: str, rot2: str) -> str | None:
    """Map rotation to its NF display code, if applicable.

    Returns None if the rotation is not a night-float type.
    """
    combined = f"{rot} {rot2}".upper()

    # Check explicit NF rotation mappings (order matters)
    for nf_key, nf_display in _NF_ROTATION_MAP:
        if nf_key in combined:
            return nf_display

    # Neuro with NF component
    for tag in _NEURO_NF_TAGS:
        if tag in combined:
            return "NF"

    return None


def estimate_impact(mismatches: list[dict]) -> dict[str, int]:
    """Estimate how many mismatches each rule would fix.

    Args:
        mismatches: List of mismatch dicts from diff_truth_vs_db.py

    Returns:
        Dict of rule_name → count_fixed
    """
    fixes: dict[str, int] = {
        "night_float_off": 0,
        "weekend_override": 0,
        "rotation_clinic": 0,
        "faculty_weekend": 0,
        "code_normalization": 0,
        "absence_mapping": 0,
        "unfixed": 0,
    }

    for m in mismatches:
        db_code = m.get("db_code", "")
        truth_code = m.get("truth_code", "")
        rot = (m.get("rotation") or "").upper()

        if db_code in CODE_NORMALIZATION and CODE_NORMALIZATION[db_code] == truth_code:
            fixes["code_normalization"] += 1
        elif db_code == "OFF" and truth_code in NIGHT_FLOAT_ROTATIONS.values():
            fixes["night_float_off"] += 1
        elif db_code == "W" and truth_code in (
            "FMIT",
            "NF",
            "PedsNF",
            "PedW",
            "IMW",
            "KAP",
            "L&D",
        ):
            fixes["weekend_override"] += 1
        elif db_code == "C" and truth_code in ROTATION_CLINIC_MAP.values():
            fixes["rotation_clinic"] += 1
        elif db_code in FACULTY_WEEKEND_COLLAPSE and truth_code == "W":
            fixes["faculty_weekend"] += 1
        elif db_code == "LV" and truth_code in ABSENCE_TYPE_MAP.values():
            fixes["absence_mapping"] += 1
        else:
            fixes["unfixed"] += 1

    return fixes
