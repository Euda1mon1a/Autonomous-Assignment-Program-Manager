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
TEMPLATES = {
    "inpatient": [
        # FMIT variants
        ("FMIT AM", "FMIT-AM"),
        ("FMIT PM", "FMIT-PM"),
        ("Family Medicine Inpatient Team Intern", "FMI"),
        ("Family Medicine Inpatient Team Resident", "FMIT-R"),
        ("Family Medicine Inpatient Team Pre-Attending", "FMIT-PA"),
        # Night Float variants
        ("Night Float AM", "NF-AM"),
        ("Night Float PM", "NF-PM"),
        ("Night Float + Cardiology", "NF+C"),
        ("Night Float + Dermatology", "NF-DERM"),
        ("Night Float + Medical Selective", "NF-MED"),
        ("Night Float + Neonatal Intensive Care Unit", "NF-NICU"),
        ("Night Float Intern + FMIT", "NFI"),
        ("Cardiology + Night Float", "C+NF"),
        ("Dermatology + Night Float", "D+NF"),
        ("Pediatrics Night Float Intern", "PNF"),
        # ICU/NICU
        ("NICU", "NICU"),
        ("Neonatal Intensive Care Unit + Night Float", "NICU-NF"),
        ("Intensive Care Unit Intern", "ICU"),
        # L&D
        ("Labor and Delivery Intern", "LD-I"),
        ("Labor and Delivery Night Float", "LDNF"),
        # Other inpatient
        ("Internal Medicine Intern", "IM-INT"),
        ("Pediatrics Ward Intern", "PEDS-W"),
        ("Newborn Nursery", "NBN"),
    ],
    "off": [
        # Off-site rotations (different hospitals)
        ("Hilo", "HILO"),
        ("Kapiolani", "KAPI"),
        ("Okinawa", "OKI"),
        ("OFF AM", "OFF-AM"),
        ("OFF PM", "OFF-PM"),
    ],
    "education": [
        # Orientation and education
        ("Family Medicine Orientation", "FMO"),
        ("Graduate Medical Education AM", "GME-AM"),
        ("Graduate Medical Education PM", "GME-PM"),
        ("Lecture AM", "LEC-AM"),
        ("Lecture PM", "LEC-PM"),
    ],
    "outpatient": [
        # Clinic rotations (solver handles these)
        ("Clinic AM", "CLI-AM"),
        ("Clinic PM", "CLI-PM"),
        ("Sports Medicine AM", "SPM-AM"),
        ("Sports Medicine PM", "SPM-PM"),
        ("Academic Sports Medicine AM", "ASM-AM"),
        ("Colposcopy AM", "COL-AM"),
        ("Colposcopy PM", "COL-PM"),
        ("Houseless Clinic AM", "HLC-AM"),
        ("Houseless Clinic PM", "HLC-PM"),
        ("PCAT AM", "PCAT-AM"),
        ("Resident Supervision AM", "RSU-AM"),
        ("Resident Supervision PM", "RSU-PM"),
        ("Advising PM", "ADV-PM"),
        ("Direct Observation PM", "DOB-PM"),
        ("Department of Family Medicine AM", "DFM-AM"),
        ("Department of Family Medicine PM", "DFM-PM"),
    ],
    "procedures": [
        ("Procedure AM", "PRO-AM"),
        ("Procedure PM", "PRO-PM"),
        ("Botox AM", "BOT-AM"),
        ("Botox PM", "BOT-PM"),
        ("Vasectomy AM", "VAS-AM"),
        ("Vasectomy PM", "VAS-PM"),
    ],
    "absence": [
        ("Leave AM", "LEA-AM"),
        ("Leave PM", "LEA-PM"),
        ("Weekend AM", "WKD-AM"),
        ("Weekend PM", "WKD-PM"),
    ],
    "recovery": [
        ("Post-Call Recovery", "PCR"),
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
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
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
        
        for name, abbrev in templates:
            if args.dry_run:
                print(f"  Would add: {name} ({abbrev})")
                continue

            data = {
                "name": name,
                "abbreviation": abbrev,
                "activity_type": activity_type,
            }

            resp = requests.post(
                f"{BASE_URL}/api/v1/rotation-templates",
                headers=headers,
                json=data,
            )

            if resp.status_code in [200, 201]:
                print(f"  ✓ {name}")
                total_added += 1
            elif resp.status_code == 409 or "exists" in resp.text.lower():
                print(f"  · {name} (exists)")
                total_exists += 1
            else:
                print(f"  ✗ {name}: {resp.status_code}")
                total_failed += 1

    print(f"\n=== Summary ===")
    print(f"  Added: {total_added}")
    print(f"  Existed: {total_exists}")
    print(f"  Failed: {total_failed}")


if __name__ == "__main__":
    main()
