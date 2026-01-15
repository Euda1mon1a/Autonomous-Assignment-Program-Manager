"""
Schedule XML Exporter.

Generates XML schedule from resident data using rotation patterns.
This is the validation checkpoint in the central dogma pipeline:

    DB (BlockAssignments) → ScheduleXMLExporter → XML → compare to ROSETTA
                                                      ↓ if match
                                               XMLToXlsxConverter → xlsx

The XML format matches ROSETTA ground truth for validation.
"""

from datetime import date, timedelta
from typing import Any
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

from app.core.logging import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ROTATION PATTERNS - TAMC Scheduling Skill constants
# These patterns define how each rotation maps to AM/PM codes.
# ═══════════════════════════════════════════════════════════════════════════════

# Pattern: (default_am, default_pm)
# Special handling for specific days overrides these defaults.
# Keys are LOWERCASE for case-insensitive matching via _normalize_rotation()
ROTATION_PATTERNS: dict[str, tuple[str, str]] = {
    # Family Medicine Clinic
    "FMC": ("C", "C"),
    "FM Clinic": ("C", "C"),
    # FM Inpatient Team - works weekends, has continuity clinic
    "FMIT": ("FMIT", "FMIT"),
    "FMIT 2": ("FMIT", "FMIT"),
    # Neurology elective
    "NEURO": ("NEURO", "C"),
    # Night Float - OFF mornings, NF evenings
    "NF": ("OFF", "NF"),
    # Peds Night Float - OFF mornings, PedNF evenings
    "PedNF": ("OFF", "PedNF"),
    "Peds NF": ("OFF", "PedNF"),
    # Peds Ward - inpatient, works weekends
    "PedW": ("PedW", "PedW"),
    "Peds Ward": ("PedW", "PedW"),
    # Internal Medicine - inpatient, works weekends
    "IM": ("IM", "IM"),
    "IMW": ("IM", "IM"),
    "Internal Medicine": ("IM", "IM"),
    # Procedures
    "PROC": ("PR", "C"),
    "PR": ("PR", "C"),
    # Sports Medicine
    "SM": ("SM", "C"),
    # Ultrasound/POCUS
    "POCUS": ("US", "C"),
    # L&D Night Float - FRIDAY clinic (not Wednesday!)
    "LDNF": ("OFF", "LDNF"),
    "L&D Night Float": ("OFF", "LDNF"),
    "L and D night float": ("OFF", "LDNF"),
    # Kapiolani L&D - off-site rotation
    "KAP": ("KAP", "KAP"),
    "KAPI-LD": ("KAP", "KAP"),
    "Kapiolani L and D": ("KAP", "KAP"),
    # Surgery Experience
    "Surg Exp": ("SURG", "C"),
    "SURG": ("SURG", "C"),
    # Gynecology Clinic
    "Gyn Clinic": ("GYN", "C"),
    "GYN": ("GYN", "C"),
    # Off-site/TDY
    "Hilo": ("TDY", "TDY"),
    "TDY": ("TDY", "TDY"),
    # Endocrinology elective
    "ENDO": ("ENDO", "C"),
    "Endocrinology": ("ENDO", "C"),
}

# Rotations that include weekend work (don't mark W on Sat/Sun)
INPATIENT_ROTATIONS = frozenset(
    [
        "FMIT",
        "FMIT 2",
        "IM",
        "IMW",
        "Internal Medicine",
        "PedW",
        "Peds Ward",
        "KAP",
        "KAP-LD",
        "KAPI-LD",
        "Kapiolani L and D",
        # TDY/Hilo - off-island, works weekends (TDY all day)
        "TDY",
        "Hilo",
    ]
)

# Rotations exempt from Wednesday PM LEC
LEC_EXEMPT_ROTATIONS = frozenset(
    [
        "NF",
        "PedNF",
        "Peds NF",
        "LDNF",
        "L&D Night Float",
        "L and D night float",
        "TDY",
        "Hilo",
    ]
)

# Rotations where PGY-1 interns get Wednesday AM clinic (intern continuity)
INTERN_CONTINUITY_EXEMPT = frozenset(
    [
        "NF",
        "PedNF",
        "Peds NF",
        "LDNF",
        "L&D Night Float",
        "L and D night float",
        "TDY",
        "Hilo",
        "KAP",
        "KAP-LD",
        "KAPI-LD",
        "Kapiolani L and D",
    ]
)

# Lowercase versions for case-insensitive matching
_INPATIENT_ROTATIONS_LOWER = frozenset(r.lower() for r in INPATIENT_ROTATIONS)
_LEC_EXEMPT_ROTATIONS_LOWER = frozenset(r.lower() for r in LEC_EXEMPT_ROTATIONS)
_INTERN_CONTINUITY_EXEMPT_LOWER = frozenset(r.lower() for r in INTERN_CONTINUITY_EXEMPT)

# Build lowercase pattern lookup
_ROTATION_PATTERNS_LOWER: dict[str, tuple[str, str]] = {
    k.lower(): v for k, v in ROTATION_PATTERNS.items()
}


def _normalize_rotation(rotation: str) -> str:
    """Normalize rotation code for case-insensitive matching."""
    return rotation.lower() if rotation else ""


def _get_pattern(rotation: str) -> tuple[str, str]:
    """Get rotation pattern with case-insensitive lookup."""
    normalized = _normalize_rotation(rotation)
    return _ROTATION_PATTERNS_LOWER.get(normalized, ("C", "C"))


def _is_inpatient(rotation: str) -> bool:
    """Check if rotation is inpatient (case-insensitive)."""
    return _normalize_rotation(rotation) in _INPATIENT_ROTATIONS_LOWER


def _is_lec_exempt(rotation: str) -> bool:
    """Check if rotation is LEC-exempt (case-insensitive)."""
    return _normalize_rotation(rotation) in _LEC_EXEMPT_ROTATIONS_LOWER


def _is_intern_continuity_exempt(rotation: str) -> bool:
    """Check if rotation is intern continuity exempt (case-insensitive)."""
    return _normalize_rotation(rotation) in _INTERN_CONTINUITY_EXEMPT_LOWER


class ScheduleXMLExporter:
    """
    Export schedule data to XML format matching ROSETTA ground truth.

    The XML format:
    ```xml
    <schedule block_start="2026-03-12" block_end="2026-04-08">
      <resident name="Name, First" pgy="1" rotation1="FMC" rotation2="">
        <day date="2026-03-12" weekday="Thu" am="C" pm="C"/>
        ...
      </resident>
      ...
    </schedule>
    ```
    """

    def __init__(self, block_start: date, block_end: date):
        self.block_start = block_start
        self.block_end = block_end

    def export(self, residents: list[dict[str, Any]]) -> str:
        """
        Export residents to XML string.

        Args:
            residents: List of dicts with keys:
                - name: "Last, First" format
                - pgy: PGY level (1, 2, or 3)
                - rotation1: Primary rotation code
                - rotation2: Secondary rotation code (for mid-block transition)

        Returns:
            XML string matching ROSETTA format
        """
        root = Element("schedule")
        root.set("block_start", self.block_start.isoformat())
        root.set("block_end", self.block_end.isoformat())

        for resident in sorted(residents, key=lambda r: r.get("name", "")):
            self._add_resident(root, resident)

        xml_str = tostring(root, encoding="unicode")
        return minidom.parseString(xml_str).toprettyxml(indent="  ")

    def _add_resident(self, parent: Element, resident: dict[str, Any]) -> None:
        """Add a resident element with all days."""
        res_elem = SubElement(parent, "resident")
        res_elem.set("name", resident.get("name", ""))
        res_elem.set("pgy", str(resident.get("pgy", 1)))
        res_elem.set("rotation1", resident.get("rotation1", ""))
        res_elem.set("rotation2", resident.get("rotation2") or "")

        # Calculate mid-block date (day 11 = start of Week 3)
        # TAMC weeks: Week 1 (Thu-Sun, days 0-3), Week 2 (Mon-Sun, days 4-10),
        #             Week 3 (Mon-Sun, days 11-17), Week 4 (Mon-Sun, days 18-24)
        # Mid-block transition happens at column 28 = day 11 = start of Week 3
        mid_block = self.block_start + timedelta(days=11)

        current = self.block_start
        while current <= self.block_end:
            # Determine active rotation (mid-block transition)
            rotation2 = resident.get("rotation2")
            if rotation2 and current >= mid_block:
                active_rotation = rotation2
            else:
                active_rotation = resident.get("rotation1", "")

            pgy = resident.get("pgy", 1)

            am_code, pm_code = self._get_day_codes(current, active_rotation, pgy)

            day_elem = SubElement(res_elem, "day")
            day_elem.set("date", current.isoformat())
            day_elem.set("weekday", current.strftime("%a"))
            day_elem.set("am", am_code)
            day_elem.set("pm", pm_code)

            current += timedelta(days=1)

    def _get_day_codes(
        self,
        current_date: date,
        rotation: str,
        pgy: int,
    ) -> tuple[str, str]:
        """
        Get AM and PM codes for a specific date and rotation.

        Applies priority rules:
        1. Last Wednesday → LEC/ADV
        2. Rotation-specific patterns (KAP, LDNF)
        3. Wednesday PM → LEC (non-exempt rotations)
        4. Intern continuity → Wed AM = C for PGY-1
        5. Weekend → W (non-inpatient rotations)
        6. Default rotation pattern
        """
        dow = current_date.isoweekday()  # 1=Mon..7=Sun
        is_weekend = dow in (6, 7)
        is_wednesday = dow == 3
        is_last_wed = self._is_last_wednesday(current_date)

        # Normalize rotation for case-insensitive matching
        rot_lower = _normalize_rotation(rotation)

        # Rule 1: Last Wednesday - ALL residents get LEC/ADV
        if is_last_wed:
            return ("LEC", "ADV")

        # Rule 2: Rotation-specific patterns
        # KAP (Kapiolani L&D) - special off-site pattern
        if rot_lower in ("kap", "kap-ld", "kapi-ld", "kapiolani l and d"):
            return self._get_kapiolani_codes(current_date)

        # LDNF (L&D Night Float) - Friday AM clinic!
        if rot_lower in ("ldnf", "l&d night float", "l and d night float"):
            return self._get_ldnf_codes(current_date)

        # Rule 3: Weekend handling
        if is_weekend:
            if _is_inpatient(rotation):
                # Inpatient rotations work weekends
                return self._get_inpatient_weekend_codes(rotation, pgy)
            else:
                return ("W", "W")

        # Rule 4: Wednesday handling
        if is_wednesday:
            am_code = self._get_wednesday_am(rotation, pgy)
            pm_code = self._get_wednesday_pm(rotation)
            return (am_code, pm_code)

        # Rule 5: Inpatient continuity clinic (non-Wednesday)
        if rot_lower in ("im", "imw", "internal medicine"):
            return self._get_im_codes(current_date, pgy)
        if rot_lower in ("pedw", "peds ward"):
            return self._get_pedw_codes(current_date, pgy)
        if rot_lower in ("fmit", "fmit 2"):
            return self._get_fmit_codes(current_date, pgy)

        # Rule 6: Default rotation pattern (case-insensitive)
        return _get_pattern(rotation)

    def _is_last_wednesday(self, current_date: date) -> bool:
        """Check if this is the last Wednesday of the block."""
        if current_date.isoweekday() != 3:  # Not Wednesday
            return False
        next_wed = current_date + timedelta(days=7)
        return next_wed > self.block_end

    def _get_kapiolani_codes(self, current_date: date) -> tuple[str, str]:
        """
        Kapiolani L&D rotation pattern:
        - Mon: KAP/OFF (travel back)
        - Tue: OFF/OFF (recovery)
        - Wed: C/LEC (continuity clinic)
        - Thu-Sun: KAP/KAP
        """
        dow = current_date.isoweekday()

        if dow == 1:  # Monday
            return ("KAP", "OFF")
        elif dow == 2:  # Tuesday
            return ("OFF", "OFF")
        elif dow == 3:  # Wednesday
            return ("C", "LEC")
        else:  # Thu-Sun
            return ("KAP", "KAP")

    def _get_ldnf_codes(self, current_date: date) -> tuple[str, str]:
        """
        L&D Night Float rotation pattern - FRIDAY AM clinic!
        - Mon-Thu: OFF/LDNF
        - Fri: C/OFF (Friday morning clinic!)
        - Sat-Sun: W/W
        """
        dow = current_date.isoweekday()

        if dow == 5:  # Friday
            return ("C", "OFF")
        elif dow in (6, 7):  # Weekend
            return ("W", "W")
        else:  # Mon-Thu
            return ("OFF", "LDNF")

    def _get_im_codes(self, current_date: date, pgy: int) -> tuple[str, str]:
        """
        Internal Medicine pattern:
        - Continuity clinic: PGY-1 Wed AM, PGY-2 Tue PM, PGY-3 Mon PM
        - All other times: IM/IM
        """
        dow = current_date.isoweekday()

        # Continuity clinic (handled elsewhere for Wednesday)
        if pgy == 2 and dow == 2:  # PGY-2 Tue PM
            return ("IM", "C")
        if pgy == 3 and dow == 1:  # PGY-3 Mon PM
            return ("IM", "C")

        return ("IM", "IM")

    def _get_pedw_codes(self, current_date: date, pgy: int) -> tuple[str, str]:
        """
        Peds Ward pattern:
        - Continuity clinic: PGY-1 Wed AM, PGY-2 Tue PM, PGY-3 Mon PM
        - All other times: PedW/PedW
        """
        dow = current_date.isoweekday()

        if pgy == 2 and dow == 2:  # PGY-2 Tue PM
            return ("PedW", "C")
        if pgy == 3 and dow == 1:  # PGY-3 Mon PM
            return ("PedW", "C")

        return ("PedW", "PedW")

    def _get_fmit_codes(self, current_date: date, pgy: int) -> tuple[str, str]:
        """
        FMIT pattern:
        - Continuity clinic: PGY-1 Wed AM, PGY-2 Tue PM, PGY-3 Mon PM
        - All other times: FMIT/FMIT
        """
        dow = current_date.isoweekday()

        if pgy == 2 and dow == 2:  # PGY-2 Tue PM
            return ("FMIT", "C")
        if pgy == 3 and dow == 1:  # PGY-3 Mon PM
            return ("FMIT", "C")

        return ("FMIT", "FMIT")

    def _get_inpatient_weekend_codes(self, rotation: str, pgy: int) -> tuple[str, str]:
        """Get weekend codes for inpatient rotations (they work weekends)."""
        rot_lower = _normalize_rotation(rotation)
        if rot_lower in ("im", "imw", "internal medicine"):
            return ("IM", "IM")
        elif rot_lower in ("pedw", "peds ward"):
            return ("PedW", "PedW")
        elif rot_lower in ("fmit", "fmit 2"):
            return ("FMIT", "FMIT")
        elif rot_lower in ("kap", "kap-ld", "kapi-ld", "kapiolani l and d"):
            return ("KAP", "KAP")
        elif rot_lower in ("tdy", "hilo"):
            return ("TDY", "TDY")
        return ("W", "W")

    def _get_wednesday_am(self, rotation: str, pgy: int) -> str:
        """
        Get Wednesday AM code.

        PGY-1 interns get Clinic (C) for intern continuity,
        EXCEPT for exempt rotations.

        Special cases:
        - SM rotation → aSM (Academic Sports Med) on Wed AM
        """
        if pgy == 1 and not _is_intern_continuity_exempt(rotation):
            return "C"

        # SM rotation gets aSM (Academic Sports Medicine) on Wed AM
        rot_lower = _normalize_rotation(rotation)
        if rot_lower in ("sm", "sports medicine", "sports medicine am"):
            return "aSM"

        # Non-interns or exempt rotations use rotation's default AM
        return _get_pattern(rotation)[0]

    def _get_wednesday_pm(self, rotation: str) -> str:
        """
        Get Wednesday PM code.

        Most rotations have LEC (lecture) on Wednesday PM,
        EXCEPT for exempt rotations (night float, off-site).
        """
        if _is_lec_exempt(rotation):
            return _get_pattern(rotation)[1]
        return "LEC"
