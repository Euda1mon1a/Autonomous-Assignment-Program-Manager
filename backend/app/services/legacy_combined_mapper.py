def get_canonical_combined_rotation(primary: str, secondary: str) -> str | None:
    """Map legacy split columns to canonical concurrent rotation abbreviations."""
    if not primary or not secondary:
        return None

    p = primary.strip().upper()
    s = secondary.strip().upper()

    # Normalize inputs
    if "DERM" in p and "NF" in s:
        return "DERM/NF"
    if "NF" in p and "DERM" in s:
        return "DERM/NF"

    if "ENDO" in p and "NF" in s:
        return "ENDO/NF"
    if "NF" in p and "ENDO" in s:
        return "ENDO/NF"

    if "CARDIO" in p and "NF" in s:
        return "CARDIO/NF"
    if "NF" in p and "CARDIO" in s:
        return "CARDIO/NF"

    if "MED" in p and "NF" in s:
        return "MED/NF"
    if "NF" in p and "MED" in s:
        return "MED/NF"

    if "NICU" in p and "NF" in s:
        return "NICU/NF"
    if "NF" in p and "NICU" in s:
        return "NICU/NF"

    if "NEURO" in p and "NF" in s:
        return "NEURO/NF"
    if "NF" in p and "NEURO" in s:
        return "NEURO/NF"

    if ("PEDS WARD" in p or "PEDSW" in p or p == "PEDS-W") and "NF" in s:
        return "PEDSW/NF"
    if "NF" in p and ("PEDS WARD" in s or "PEDSW" in s or s == "PEDS-W"):
        return "PEDSW/NF"

    if ("L&D" in p or "L AND D" in p) and "NF" in s:
        return "L&D/NF"
    if "NF" in p and ("L&D" in s or "L AND D" in s):
        return "L&D/NF"

    return None
