"""Shared code mappings for schedule import/export.

Canonical map of Excel display codes → DB activity codes.
Consolidated from Block 11/12 proven mappings (61+ entries).

Usage:
    from code_maps import CODE_MAP, reverse_code_map
"""

# Excel display code → DB activity code
CODE_MAP = {
    "SM": "sm_clinic",
    "aSM": "aSM",
    "LEC": "lec",
    "CLC": "CLC",
    "CC": "CC",
    "W": "W",
    "C": "fm_clinic",
    "C`": "fm_clinic",      # Typo variant
    "FLX": "FLX",
    "HC": "HLC",
    "PI": "PI",
    "GME": "gme",
    "FMIT": "FMIT",
    "retreat": "RETREAT",
    "RETREAT": "RETREAT",
    "NF": "NF",
    "OFF": "off",
    "PCAT": "pcat",
    "DO": "do",
    "DFM": "dfm",
    "CCC": "CCC",
    "SLV": "SLV",
    "CV": "CV",
    "DEP": "DEP",
    "PC": "recovery",
    "LV": "LV",
    "AT": "at",
    "at": "at",
    "NEURO": "NEURO",
    "PedSP": "PEDS-S",
    "Derm": "DERM",
    "NBN": "NBN",
    "PR": "PR",
    "TDY": "TDY",
    "ADM": "ADM",
    "OB": "OB",
    "L&D": "KAP-LD",        # Default; override per person if TAMC vs KAP
    "Orient": "ORIENT",
    "VasC": "VASC",
    "BOARDS": "ADM",
    "C-N": "C-N",
    "HR for Sup Training": "HR-SUP",
    "HR for Sup": "HR-SUP",
    "EPIC": "ORIENT",
    "STRAUB": "elective",
    "SIM": "SIM",
    "V2": "V2",
    "HV": "HV",
    "KAP": "KAP-LD",
    "procedure": "procedure",
    "ADV": "ADV",
    "VAS": "VAS",
    "Coding": "CODING",
    "C30": "C30",
    "LDNF": "LDNF",
    "HOL": "HOL",
    "PedW": "PEDSW",
    "TNG": "TNG",
    "P ER": "PEDS-ER",
    "ER": "ER",
    "US": "US",
    "C-I": "C-I",
    "C40": "C40",
    "Rad": "RAD",
    "Cast": "CAST",
    "TENT": "TENT",
    # Historical block codes (discovered during blocks 2-11 extraction)
    "RTRT": "RETREAT",       # Alternate retreat abbreviation
    "IMW": "IMW",
    "CP": "recovery",        # Alternate recovery code
    "PedsNF": "PedNF",      # DB uses PedNF
    "USAFP": "USAFP",
    "Peds": "PEDS",
    "Endo": "ENDO",
    "ALS": "ALS",
    "ALL": "ALL",
    "Palli": "PALLI",
    "Ophtho": "OPHTHO",
    "GYN": "GYN",
    "ENT": "ENT",
    "URO": "URO",
    "DERM": "DERM",
    "C60": "C60",
    "Sim": "SIM",
    "Ori": "ORIENT",
    "PER": "PER",
    "DOFM": "DOFM",
    "APD": "APD",
    # Codes from blocks 2-6 needing explicit mapping
    "ICU": "ICU",
    "NICU": "NICU",         # Exact match to DB
    "MM": "MM",             # Exact match to DB
    "ER": "ER",
    "PedC": "PEDC",
    "VA": "VA",
    "C40": "C40",
    "SEL": "elective",      # Selective → elective
    "HAFP": "HAFP",         # Exact match to DB
    "ILE": "ILE",
    "RSH": "RSH",
    "USU": "USU",
    "Card": "CARDS",
    "Cards": "CARDS",
    "LSCO": "LSCO",
    "GI": "GI",
    "PSY": "PSY",
    "ADHD": "ADHD",
    "MultiD": "MULTID",
    "FED": "FED",
    "MUC": "MUC",
    "PAL": "PALLI",         # Palliative alias
    "ANES": "ANES",
    "OPTH": "OPHTHO",       # Alternate spelling
    "ECO": "ECO",
    "NRP": "NRP",
    "PALS": "PALS",
    "LND": "KAP-LD",        # L&D variant spelling
    "STEP3": "STEP3",
    "Step 3": "STEP3",
    "ITE": "ITE",
    "FAC": "FAC",
    "BLS": "BLS",
    "PCAT DO": "pcat",      # PCAT variant
    "AMS": "AMS",
}

# Leave-type activity codes (for absence sync)
LEAVE_CODES = {"LV", "LV-AM", "LV-PM", "TDY", "DEP", "SLV"}

# Maps leave codes to absence_type
LEAVE_TYPE_MAP = {
    "LV": "vacation",
    "LV-AM": "vacation",
    "LV-PM": "vacation",
    "SLV": "vacation",
    "TDY": "tdy",
    "DEP": "deployment",
}


def reverse_code_map() -> dict[str, str]:
    """Build display_code → db_code reverse mapping.

    When multiple display codes map to the same DB code, all are included.
    Returns {db_code: display_code} for the most common/canonical form.
    """
    reverse = {}
    for display, db in CODE_MAP.items():
        # First mapping wins (canonical form)
        if db not in reverse:
            reverse[db] = display
    return reverse


def display_to_db(display_code: str) -> str:
    """Map a handjam display code to its DB activity code.

    Falls back to lowercase if not in CODE_MAP.
    """
    if display_code in CODE_MAP:
        return CODE_MAP[display_code]
    # Try case-insensitive match
    for key, val in CODE_MAP.items():
        if key.lower() == display_code.lower():
            return val
    return display_code.lower()
