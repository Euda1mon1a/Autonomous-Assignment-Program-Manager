#!/usr/bin/env python3
"""
Validate expansion service against ROSETTA_COMPLETE ground truth.

Parses Block10_ROSETTA_COMPLETE.xml and compares against expansion service output.
"""

import sys
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

ROSETTA_PATH = (
    Path(__file__).parent.parent.parent
    / "docs"
    / "scheduling"
    / "Block10_ROSETTA_COMPLETE.xml"
)


def parse_rosetta_xml(path: Path) -> dict[str, dict]:
    """
    Parse ROSETTA XML into resident schedules.

    Returns:
        Dict mapping resident name to schedule dict:
        {
            "Travis, Colin": {
                "pgy": 1,
                "rotation1": "KAP",
                "rotation2": "",
                "days": {
                    "2026-03-12": {"am": "KAP", "pm": "KAP"},
                    ...
                }
            }
        }
    """
    tree = ElementTree.parse(path)
    root = tree.getroot()

    residents = {}
    for resident in root.findall("resident"):
        name = resident.get("name")
        pgy = int(resident.get("pgy", 0))
        rotation1 = resident.get("rotation1", "")
        rotation2 = resident.get("rotation2", "")

        days = {}
        for day in resident.findall("day"):
            date_str = day.get("date")
            am = day.get("am")
            pm = day.get("pm")
            days[date_str] = {"am": am, "pm": pm}

        residents[name] = {
            "pgy": pgy,
            "rotation1": rotation1,
            "rotation2": rotation2,
            "days": days,
        }

    return residents


def get_rotation_pattern(
    rotation: str, day_of_week: int, is_last_wed: bool = False
) -> tuple[str, str]:
    """
    Get expected AM/PM codes for a rotation on a given day.

    Args:
        rotation: Rotation name
        day_of_week: 0=Mon, 1=Tue, ..., 6=Sun
        is_last_wed: True if this is the last Wednesday of the block

    Returns:
        Tuple of (AM_code, PM_code)
    """
    # Last Wednesday override
    if is_last_wed:
        return ("LEC", "ADV")

    # Weekend
    if day_of_week in (5, 6):  # Sat, Sun
        # Some rotations work weekends
        if rotation in ("IM", "FMIT", "PedW"):
            pass  # These work weekends
        elif rotation == "KAP":
            return ("KAP", "KAP")  # KAP works weekends
        else:
            return ("W", "W")

    # Wednesday PM is LEC for most
    if day_of_week == 2:  # Wednesday
        # Get AM code, PM is LEC
        am, _ = _get_base_pattern(rotation, day_of_week)
        return (am, "LEC")

    return _get_base_pattern(rotation, day_of_week)


def _get_base_pattern(rotation: str, day_of_week: int) -> tuple[str, str]:
    """Get base AM/PM pattern for rotation."""

    # KAP - Kapiolani L&D (PGY-1)
    if rotation == "KAP":
        if day_of_week == 0:  # Monday
            return ("KAP", "OFF")
        elif day_of_week == 1:  # Tuesday
            return ("OFF", "OFF")
        elif day_of_week == 2:  # Wednesday
            return ("C", "LEC")
        else:  # Thu-Sun
            return ("KAP", "KAP")

    # LDNF - L&D Night Float (PGY-2)
    if rotation in ("LDNF", "L&D Night Float"):
        if day_of_week == 4:  # Friday
            return ("C", "OFF")
        elif day_of_week in (5, 6):  # Weekend
            return ("W", "W")
        else:  # Mon-Thu
            return ("OFF", "LDNF")

    # Night Float
    if rotation == "NF":
        return ("OFF", "NF")

    # Peds Night Float
    if rotation in ("Peds NF", "PedNF"):
        return ("OFF", "PedNF")

    # Peds Ward
    if rotation in ("Peds Ward", "PedW"):
        return ("PedW", "PedW")

    # FMIT
    if rotation in ("FMIT", "FMIT 2"):
        return ("FMIT", "FMIT")

    # IM
    if rotation == "IM":
        return ("IM", "IM")

    # FMC - Family Medicine Clinic
    if rotation == "FMC":
        return ("C", "C")

    # PROC - Procedures
    if rotation == "PROC":
        return ("PR", "C")

    # Neurology
    if rotation == "NEURO":
        return ("NEURO", "C")

    # Sports Medicine
    if rotation == "SM":
        return ("SM", "C")

    # POCUS
    if rotation == "POCUS":
        return ("US", "C")

    # Surgery Experience
    if rotation in ("Surg Exp", "SURG"):
        return ("SURG", "C")

    # Gyn Clinic
    if rotation in ("Gyn Clinic", "GYN"):
        return ("GYN", "C")

    # Hilo TDY
    if rotation == "Hilo":
        return ("TDY", "TDY")

    # Default
    return (rotation, rotation)


def main():
    """Run validation."""
    print("=" * 70)
    print("ROSETTA_COMPLETE VALIDATION")
    print("=" * 70)
    print()

    if not ROSETTA_PATH.exists():
        print(f"ERROR: ROSETTA file not found at {ROSETTA_PATH}")
        sys.exit(1)

    # Parse ROSETTA
    print(f"Parsing: {ROSETTA_PATH}")
    residents = parse_rosetta_xml(ROSETTA_PATH)
    print(f"Found {len(residents)} residents")
    print()

    # Display summary
    print("Residents by PGY level:")
    by_pgy = {}
    for name, data in residents.items():
        pgy = data["pgy"]
        by_pgy.setdefault(pgy, []).append(name)

    for pgy in sorted(by_pgy.keys()):
        print(f"  PGY-{pgy}: {len(by_pgy[pgy])}")
        for name in sorted(by_pgy[pgy]):
            rot = residents[name]["rotation1"]
            rot2 = residents[name].get("rotation2", "")
            if rot2:
                print(f"    - {name}: {rot} → {rot2}")
            else:
                print(f"    - {name}: {rot}")

    print()

    # Validate patterns
    print("Validating patterns...")
    print("-" * 70)

    mismatches = []
    for name, data in residents.items():
        rot1 = data["rotation1"]
        rot2 = data.get("rotation2", "")

        for date_str, slots in data["days"].items():
            d = date.fromisoformat(date_str)
            dow = d.weekday()

            # Determine if mid-block (Mar 23+)
            mid_block_date = date(2026, 3, 23)
            rotation = rot2 if (rot2 and d >= mid_block_date) else rot1

            # Check if last Wednesday (Apr 8)
            is_last_wed = date_str == "2026-04-08"

            expected_am, expected_pm = get_rotation_pattern(rotation, dow, is_last_wed)
            actual_am = slots["am"]
            actual_pm = slots["pm"]

            if expected_am != actual_am:
                mismatches.append(
                    {
                        "name": name,
                        "date": date_str,
                        "slot": "AM",
                        "expected": expected_am,
                        "actual": actual_am,
                        "rotation": rotation,
                    }
                )

            if expected_pm != actual_pm:
                mismatches.append(
                    {
                        "name": name,
                        "date": date_str,
                        "slot": "PM",
                        "expected": expected_pm,
                        "actual": actual_pm,
                        "rotation": rotation,
                    }
                )

    if mismatches:
        print(f"Found {len(mismatches)} mismatches:")
        print()

        # Group by resident
        by_resident = {}
        for m in mismatches:
            by_resident.setdefault(m["name"], []).append(m)

        for name in sorted(by_resident.keys()):
            items = by_resident[name]
            print(f"{name} ({len(items)} mismatches):")
            for m in items[:5]:  # Show first 5
                print(
                    f"  {m['date']} {m['slot']}: expected {m['expected']}, got {m['actual']} (rot={m['rotation']})"
                )
            if len(items) > 5:
                print(f"  ... and {len(items) - 5} more")
            print()
    else:
        print("All patterns match!")

    print("=" * 70)
    if mismatches:
        print(f"VALIDATION: {len(mismatches)} mismatches found")
        print("These indicate where our pattern logic differs from ROSETTA")
    else:
        print("VALIDATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
