"""Rules learned from handjam ground truth vs DB diff.

6,396 labeled cells, 943 diffs → these transformation rules.

Usage:
    from learned_rules import transform
    display_code = transform(db_display, rotation1, rotation2, section, person_context)
"""

# ──────────────────────────────────────────────────────────────
# RULE 1: Universal code remappings (apply to everyone)
# ──────────────────────────────────────────────────────────────
UNIVERSAL_REMAP = {
    "ADV": "GME",       # 10/10 occurrences: ADV always displays as GME
    "LDNF": "L&D",      # 12/12: LDNF always displays as L&D
    "PedNF": "PedsNF",  # 17/17: PedNF always displays as PedsNF
}

# ──────────────────────────────────────────────────────────────
# RULE 2: Rotation-based OFF/W overrides (RESIDENTS only)
#
# Pattern: When a resident is on a 24/7 rotation, their "OFF"
# half-days show the rotation code, and their "W" (weekend)
# half-days show the rotation-specific weekend code.
# ──────────────────────────────────────────────────────────────
# rotation1 → {db_display: handjam_display}
ROTATION_OVERRIDES = {
    # Night float rotations: OFF → rotation code
    "NF": {
        "OFF": "NF",
        "W": "NF",       # NF works weekends too
    },
    "NEURO": {
        "OFF": "NF",      # 9x NF vs 3x NEURO — default to NF (safer)
        "W": "NF",        # weekends show NF
    },
    "Peds NF": {
        "OFF": "PedsNF",
        "W": "PedsNF",
        "PedW": "PedsNF",  # PedW code displays as PedsNF for NF side
    },
    "Peds Ward": {
        "OFF": "PedsNF",  # Ward residents' OFF days are NF coverage
        "W": "PedW",      # weekends show PedW
        "PedNF": "PedsNF",  # normalize PedNF→PedsNF
    },
    # L&D night float
    "L and D night float": {
        "OFF": "L&D",
        "LDNF": "L&D",
        "W": "L&D",
        "LEC": "L&D",     # 4/4: LEC→L&D on L&D NF
        "ADV": "L&D",     # 1/1: ADV→L&D
    },
    # Inpatient rotations: W → rotation code
    "FMIT 2": {
        "W": "FMIT",
        "LEC": "FMIT",    # 8/8: LEC→FMIT on FMIT rotations
        "ADV": "FMIT",    # 2/2: ADV→FMIT on FMIT rotations
        "C": "FMIT",      # 4/4: C→FMIT (Petrie)
    },
    "Kapiolani L and D": {
        "W": "KAP",
        "C": "KAP",       # 1/1: Travis C→KAP
        "LEC": "KAP",     # 1/1: Travis LEC→KAP
    },
    "IM": {
        "IM": "IMW",     # IM always displays as IMW (47/48)
        "W": "IMW",      # weekends too (8x)
    },
    "Hilo": {
        "W": "TDY",      # Hilo = TDY site, weekends are TDY
    },
}

# ──────────────────────────────────────────────────────────────
# RULE 3: Rotation-based clinic code overrides
#
# Pattern: When the DB says "C" (fm_clinic), the handjam shows
# the specific clinic type based on rotation.
# ──────────────────────────────────────────────────────────────
CLINIC_ROTATION_MAP = {
    "SM": "SM",              # Sports Med: C→SM (13/13)
    "Gyn Clinic": "GYN",    # GYN clinic: C→GYN (11/11)
    "PROC": "PR",            # Procedures: C→PR (7/7)
    "POCUS": "US",           # Ultrasound: C→US (9/9)
    # "Surg Exp" is wild — maps to subspecialty rotations (Ophtho, URO, ENT)
    # These can't be predicted from rotation alone; they're per-day assignments
}

# ──────────────────────────────────────────────────────────────
# RULE 4: Absence type overrides
# ──────────────────────────────────────────────────────────────
# When DB shows "LV" and person has a specific absence type:
ABSENCE_OVERRIDES = {
    "deployment": "DEP",    # 56/56: Colgan deployment → DEP
    "usafp": "USAFP",      # 18/18: USAFP conference → USAFP
    # Regular leave stays "LV"
}

# ──────────────────────────────────────────────────────────────
# RULE 5: NF rotation secondary mapping (rot2)
#
# When rotation2 exists, it can override OFF displays
# ──────────────────────────────────────────────────────────────
# If rot2 == "MS: Endo" and rot1 == "NF":
#   OFF → Endo on MS:Endo days (8x Hernandez)
#   OFF → NF on other days (10x Hernandez)
# This requires knowing the schedule for which subspecialty day it is


def transform(
    db_display: str,
    rotation1: str | None = None,
    rotation2: str | None = None,
    section: str = "resident",
    absence_type: str | None = None,
) -> str:
    """Transform DB display code to handjam display code.

    Args:
        db_display: The activities.display_abbreviation from DB
        rotation1: Primary rotation name from block_assignments
        rotation2: Secondary rotation name (if split rotation)
        section: "resident" or "faculty"
        absence_type: If person has an active absence

    Returns:
        The display code the handjam would show.
    """
    # Rule 4: Absence overrides (highest priority)
    if db_display == "LV" and absence_type:
        for abs_type, code in ABSENCE_OVERRIDES.items():
            if abs_type in absence_type.lower():
                return code

    # Rules 2 & 3: Rotation-based (residents only) — BEFORE universal
    # because rotation-specific overrides beat universal remaps
    # (e.g., FMIT 2 ADV→FMIT beats universal ADV→GME)
    if section == "resident" and rotation1:
        # Rule 2: Rotation overrides (OFF/W/LEC/ADV/etc.)
        rot_rules = ROTATION_OVERRIDES.get(rotation1, {})
        if db_display in rot_rules:
            return rot_rules[db_display]

        # Rule 3: Clinic code overrides
        if db_display == "C" and rotation1 in CLINIC_ROTATION_MAP:
            return CLINIC_ROTATION_MAP[rotation1]

    # Rule 1: Universal remappings (fallback)
    if db_display in UNIVERSAL_REMAP:
        return UNIVERSAL_REMAP[db_display]

    return db_display


# ──────────────────────────────────────────────────────────────
# Validation: test against ground truth diff
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json
    from pathlib import Path

    diff = json.loads(Path("/tmp/block10_diff.json").read_text())

    fixed = 0
    still_wrong = []
    made_worse = []

    for d in diff["differs_detail"]:
        section = "faculty" if d.get("rotation1") is None else "resident"
        # Better heuristic: faculty rows are 31+
        if "row" in d and d["row"] >= 31:
            section = "faculty"

        result = transform(
            db_display=d["db_display"],
            rotation1=d["rotation1"],
            rotation2=d["rotation2"],
            section=section,
        )
        if result == d["handjam"]:
            fixed += 1
        elif result != d["db_display"]:
            made_worse.append({
                "person": d["person"],
                "date": d["date"],
                "half": d["half"],
                "db": d["db_display"],
                "handjam": d["handjam"],
                "our_result": result,
            })
        else:
            still_wrong.append({
                "person": d["person"],
                "db": d["db_display"],
                "handjam": d["handjam"],
                "rot1": d["rotation1"],
            })

    total = len(diff["differs_detail"])
    print(f"=== RULE VALIDATION (943 diffs) ===")
    print(f"  Fixed by rules:  {fixed:4d} ({100*fixed/total:.1f}%)")
    print(f"  Still wrong:     {len(still_wrong):4d} ({100*len(still_wrong)/total:.1f}%)")
    print(f"  Made worse:      {len(made_worse):4d} ({100*len(made_worse)/total:.1f}%)")

    if made_worse:
        print(f"\n=== MADE WORSE (rules produced wrong answer) ===")
        from collections import Counter
        worse_patterns = Counter(
            (m["db"], m["handjam"], m["our_result"]) for m in made_worse
        )
        for (db, hj, ours), cnt in worse_patterns.most_common(20):
            print(f"  {db:8s} -> wanted {hj:8s}, got {ours:8s} ({cnt}x)")

    if still_wrong:
        print(f"\n=== STILL WRONG (top 20 patterns) ===")
        from collections import Counter
        wrong_patterns = Counter(
            (m["db"], m["handjam"], m.get("rot1", "?")) for m in still_wrong
        )
        for (db, hj, rot), cnt in wrong_patterns.most_common(20):
            print(f"  {db:8s} -> {hj:8s} (rot={rot}) ({cnt}x)")
