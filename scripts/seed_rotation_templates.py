#!/usr/bin/env python3
"""
Seed rotation templates with correct activity types.

This ensures the solver knows which rotations to skip (inpatient, off-site, etc.)
and which to optimize (outpatient, procedures).

Usage:
    python scripts/seed_rotation_templates.py
    python scripts/seed_rotation_templates.py --dry-run
"""

import argparse
import os
import sys

import requests

BASE_URL = os.getenv("SEED_BASE_URL", "http://localhost:8000")

# Rotation templates by activity type
# Each entry: (name, abbreviation, display_abbreviation)
# - abbreviation: DB format with AM/PM suffix (e.g., "C-AM", "FMIT-AM")
# - display_abbreviation: Short GUI code (e.g., "C", "FMIT")
TEMPLATES = {
    "inpatient": [
        # FMIT variants
        ("FMIT AM", "FMIT-AM", "FMIT"),
        ("FMIT PM", "FMIT-PM", "FMIT"),
        ("Family Medicine Inpatient Team Intern", "FMI", "FMI"),
        ("Family Medicine Inpatient Team Resident", "FMIT-R", "FMIT"),
        ("Family Medicine Inpatient Team Pre-Attending", "FMIT-PA", "FMIT"),
        # Night Float variants
        ("Night Float AM", "NF-AM", "NF"),
        ("Night Float PM", "NF-PM", "NF"),
        ("Night Float + Cardiology", "NF+C", "NF"),
        ("Night Float + Dermatology", "NF-DERM", "NF"),
        ("Night Float + Medical Selective", "NF-MED", "NF"),
        ("Night Float + Neonatal Intensive Care Unit", "NF-NICU", "NF"),
        ("Night Float Intern + FMIT", "NFI", "NFI"),
        ("Cardiology + Night Float", "C+NF", "NF"),
        ("Dermatology + Night Float", "D+NF", "NF"),
        ("Pediatrics Night Float Intern", "PNF", "PNF"),
        # ICU/NICU
        ("NICU", "NICU", "NICU"),
        ("Neonatal Intensive Care Unit + Night Float", "NICU-NF", "NICU"),
        ("Intensive Care Unit Intern", "ICU", "ICU"),
        # L&D
        ("Labor and Delivery Intern", "LD-I", "LD"),
        ("Labor and Delivery Night Float", "LDNF", "LD"),
        # Other inpatient
        ("Internal Medicine Intern", "IMW", "IMW"),
        ("Pediatrics Ward Intern", "PedW", "PedW"),
        ("Newborn Nursery", "NBN", "NBN"),
    ],
    "off": [
        # Off-site rotations (different hospitals)
        ("Hilo", "HILO", "HILO"),
        ("Kapiolani", "KAP", "KAP"),
        ("Okinawa", "OKI", "OKI"),
        ("OFF AM", "OFF-AM", "OFF"),
        ("OFF PM", "OFF-PM", "OFF"),
    ],
    "education": [
        # Orientation and education
        ("Family Medicine Orientation", "FMO", "FMO"),
        ("Graduate Medical Education AM", "GME-AM", "GME"),
        ("Graduate Medical Education PM", "GME-PM", "GME"),
        ("Lecture AM", "LEC-AM", "LEC"),
        ("Lecture PM", "LEC-PM", "LEC"),
        ("Simulation", "SIM", "SIM"),
    ],
    "outpatient": [
        # Clinic rotations (solver handles these)
        ("Clinic AM", "C-AM", "C"),
        ("Clinic PM", "C-PM", "C"),
        ("Continuity Clinic AM", "CC-AM", "CC"),
        ("Continuity Clinic PM", "CC-PM", "CC"),
        ("Clinic Virtual AM", "CV-AM", "CV"),
        ("Clinic Virtual PM", "CV-PM", "CV"),
        ("Clinic 30min AM", "C30-AM", "C30"),
        ("Clinic 30min PM", "C30-PM", "C30"),
        ("Sports Medicine AM", "SM-AM", "SM"),
        ("Sports Medicine PM", "SM-PM", "SM"),
        ("Academic Sports Medicine AM", "ASM-AM", "ASM"),
        ("Colposcopy AM", "COLP-AM", "COLP"),
        ("Colposcopy PM", "COLP-PM", "COLP"),
        ("Houseless Clinic AM", "HC-AM", "HC"),
        ("Houseless Clinic PM", "HC-PM", "HC"),
        ("Nursing Home Clinic AM", "CLC-AM", "CLC"),
        ("Nursing Home Clinic PM", "CLC-PM", "CLC"),
        ("PCAT AM", "PCAT-AM", "PCAT"),
        ("Pediatrics Clinic AM", "PedC-AM", "PedC"),
        ("Pediatrics Clinic PM", "PedC-PM", "PedC"),
        ("Resident Supervision AM", "RSU-AM", "RSU"),
        ("Resident Supervision PM", "RSU-PM", "RSU"),
        ("Advising PM", "ADV-PM", "ADV"),
        ("Direct Observation PM", "DO-PM", "DO"),
        ("Department of Family Medicine AM", "DFM-AM", "DFM"),
        ("Department of Family Medicine PM", "DFM-PM", "DFM"),
        ("Video Clinic PGY-1 AM", "V1-AM", "V1"),
        ("Video Clinic PGY-2 AM", "V2-AM", "V2"),
        ("Video Clinic PGY-3 AM", "V3-AM", "V3"),
        ("Home Visit AM", "HV-AM", "HV"),
        ("Home Visit PM", "HV-PM", "HV"),
        ("Walk-In Contraceptive Services AM", "WICS-AM", "WICS"),
        ("Walk-In Contraceptive Services PM", "WICS-PM", "WICS"),
    ],
    "procedures": [
        ("Procedure AM", "PR-AM", "PR"),
        ("Procedure PM", "PR-PM", "PR"),
        ("Botox AM", "BTX-AM", "BTX"),
        ("Botox PM", "BTX-PM", "BTX"),
        ("Vasectomy AM", "VAS-AM", "VAS"),
        ("Vasectomy PM", "VAS-PM", "VAS"),
        ("Vasectomy Counseling AM", "VasC-AM", "VasC"),
        ("Vasectomy Counseling PM", "VasC-PM", "VasC"),
    ],
    "absence": [
        ("Leave AM", "LV-AM", "LV"),
        ("Leave PM", "LV-PM", "LV"),
        ("Weekend AM", "W-AM", "W"),
        ("Weekend PM", "W-PM", "W"),
        ("Holiday AM", "HOL-AM", "HOL"),
        ("Holiday PM", "HOL-PM", "HOL"),
        ("Federal Holiday AM", "FED-AM", "FED"),
        ("Federal Holiday PM", "FED-PM", "FED"),
        ("TDY AM", "TDY-AM", "TDY"),
        ("TDY PM", "TDY-PM", "TDY"),
    ],
    "recovery": [
        ("Post-Call Recovery AM", "PC-AM", "PC"),
        ("Post-Call Recovery PM", "PC-PM", "PC"),
    ],
    "administrative": [
        ("Administrative AM", "ADM-AM", "ADM"),
        ("Administrative PM", "ADM-PM", "ADM"),
        ("Process Improvement AM", "PI-AM", "PI"),
        ("Process Improvement PM", "PI-PM", "PI"),
        ("Research AM", "RSH-AM", "RSH"),
        ("Research PM", "RSH-PM", "RSH"),
        ("Flex Time AM", "FLX-AM", "FLX"),
        ("Flex Time PM", "FLX-PM", "FLX"),
    ],
    "military": [
        ("Military Unique Curriculum AM", "MUC-AM", "MUC"),
        ("Military Unique Curriculum PM", "MUC-PM", "MUC"),
        ("Combat Casualty Care Course AM", "C4-AM", "C4"),
        ("Combat Casualty Care Course PM", "C4-PM", "C4"),
        ("Epic Training AM", "EPIC-AM", "EPIC"),
        ("Straub Health Visit PM", "STRAUB-PM", "STRAUB"),
    ],
}


def get_auth_token() -> str:
    """Get authentication token."""
    username = os.getenv("SEED_ADMIN_USERNAME", "admin")
    password = os.getenv("SEED_ADMIN_PASSWORD", "admin123")

    resp = requests.post(
        f"{BASE_URL}/api/v1/auth/login/json",
        json={"username": username, "password": password},
    )
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        sys.exit(1)

    return resp.json()["access_token"]


def main():
    parser = argparse.ArgumentParser(description="Seed rotation templates")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done"
    )
    args = parser.parse_args()

    if args.dry_run:
        print("[DRY RUN MODE]")

    print("Authenticating...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    total_added = 0
    total_exists = 0
    total_failed = 0

    for activity_type, templates in TEMPLATES.items():
        print(f"\n=== {activity_type.upper()} ===")

        for name, abbrev, display_abbrev in templates:
            if args.dry_run:
                print(
                    f"  Would add: {name} (abbrev={abbrev}, display={display_abbrev})"
                )
                continue

            data = {
                "name": name,
                "abbreviation": abbrev,
                "display_abbreviation": display_abbrev,
                "activity_type": activity_type,
            }

            resp = requests.post(
                f"{BASE_URL}/api/v1/rotation-templates",
                headers=headers,
                json=data,
            )

            if resp.status_code in [200, 201]:
                print(f"  + {name} ({abbrev} / {display_abbrev})")
                total_added += 1
            elif resp.status_code == 409 or "exists" in resp.text.lower():
                print(f"  . {name} (exists)")
                total_exists += 1
            else:
                print(f"  x {name}: {resp.status_code}")
                total_failed += 1

    print("\n=== Summary ===")
    print(f"  Added: {total_added}")
    print(f"  Existed: {total_exists}")
    print(f"  Failed: {total_failed}")


if __name__ == "__main__":
    main()
