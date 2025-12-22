#!/usr/bin/env python3
"""Seed rotation templates from Airtable data.

Run with: python scripts/seed_templates.py

To populate ROTATIONS dict: Export from Airtable and paste rotation data below.
"""
import sys
from pathlib import Path

import requests

BASE_URL = "http://localhost:8000"

# Your actual rotations from Airtable - POPULATE THIS
# Key fields: name, activity_type, abbreviation, leave_eligible
# Half-day patterns: outpatient=10/week (3 FM clinic), inpatient/FMIT=14/week
ROTATIONS = [
    # ========== INPATIENT (14 half-days/week, no call, leave NOT eligible) ==========
    {
        "name": "FMIT",
        "activity_type": "inpatient",
        "abbreviation": "FMIT",
        "leave_eligible": False,
        "max_residents": 1,
        "supervision_required": True,
    },
    {
        "name": "FMIT + Night Float Intern",
        "activity_type": "inpatient",
        "abbreviation": "FMIT+NF",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Night Float Intern + FMIT",
        "activity_type": "inpatient",
        "abbreviation": "NF+FMIT",
        "leave_eligible": False,
        "max_residents": 1,
    },
    # ========== NIGHT FLOAT (Special 2-week patterns) ==========
    {
        "name": "Night Float",
        "activity_type": "night_float",
        "abbreviation": "NF",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Neonatal Intensive Care Unit + Night Float",
        "activity_type": "night_float",
        "abbreviation": "NICU+NF",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Night Float + Neonatal Intensive Care Unit",
        "activity_type": "night_float",
        "abbreviation": "NF+NICU",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Dermatology + Night Float",
        "activity_type": "night_float",
        "abbreviation": "Derm+NF",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Night Float + Dermatology",
        "activity_type": "night_float",
        "abbreviation": "NF+Derm",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Psychiatry + Night Float",
        "activity_type": "night_float",
        "abbreviation": "Psych+NF",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Night Float + Psychiatry",
        "activity_type": "night_float",
        "abbreviation": "NF+Psych",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Cardiology + Night Float",
        "activity_type": "night_float",
        "abbreviation": "Cardio+NF",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Night Float + Cardiology",
        "activity_type": "night_float",
        "abbreviation": "NF+Cardio",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Surgical Experience + Night Float",
        "activity_type": "night_float",
        "abbreviation": "Surg+NF",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Night Float + Surgical Experience",
        "activity_type": "night_float",
        "abbreviation": "NF+Surg",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Night Float + Medical Selective",
        "activity_type": "night_float",
        "abbreviation": "NF+Med",
        "leave_eligible": False,
        "max_residents": 1,
    },
    # ========== OUTPATIENT (10 half-days/week, 3/10 = FM Clinic) ==========
    {
        "name": "Neurology Selective",
        "activity_type": "outpatient",
        "abbreviation": "Neuro",
        "leave_eligible": True,
        "requires_specialty": "Neurology",
    },
    {
        "name": "Infectious Disease Selective",
        "activity_type": "outpatient",
        "abbreviation": "ID",
        "leave_eligible": True,
        "requires_specialty": "Infectious Disease",
    },
    {
        "name": "Palliative Selective",
        "activity_type": "outpatient",
        "abbreviation": "Pall",
        "leave_eligible": True,
    },
    {
        "name": "Pediatrics Subspecialty",
        "activity_type": "outpatient",
        "abbreviation": "PedsSub",
        "leave_eligible": True,
    },
    {
        "name": "Selective Medicine",
        "activity_type": "outpatient",
        "abbreviation": "SelMed",
        "leave_eligible": True,
    },
    {
        "name": "Research Elective",
        "activity_type": "outpatient",
        "abbreviation": "Research",
        "leave_eligible": True,
    },
    # ========== CLINIC ==========
    {
        "name": "Family Medicine Clinic Resident",
        "activity_type": "clinic",
        "abbreviation": "FMC",
        "leave_eligible": True,
        "clinic_location": "Main Clinic",
        "max_residents": 6,
        "supervision_required": True,
        "max_supervision_ratio": 4,
    },
    {
        "name": "Procedures Rotation",
        "activity_type": "procedure",
        "abbreviation": "Proc",
        "leave_eligible": True,
        "requires_procedure_credential": True,
    },
    # ========== INTERN ROTATIONS ==========
    {
        "name": "Internal Medicine Intern",
        "activity_type": "inpatient",
        "abbreviation": "IM",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Emergency Medicine",
        "activity_type": "inpatient",
        "abbreviation": "EM",
        "leave_eligible": False,
        "max_residents": 2,
    },
    {
        "name": "Labor and Delivery Intern",
        "activity_type": "inpatient",
        "abbreviation": "L&D",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Pediatrics Ward Intern",
        "activity_type": "inpatient",
        "abbreviation": "PedsWard",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Newborn Nursery",
        "activity_type": "inpatient",
        "abbreviation": "NBN",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Labor and Delivery Night Float",
        "activity_type": "night_float",
        "abbreviation": "L&D-NF",
        "leave_eligible": False,
        "max_residents": 1,
    },
    {
        "name": "Pediatrics Night Float Intern",
        "activity_type": "night_float",
        "abbreviation": "Peds-NF",
        "leave_eligible": False,
        "max_residents": 1,
    },
    # ========== ORIENTATION / MISC ==========
    {
        "name": "Family Medicine Orientation",
        "activity_type": "orientation",
        "abbreviation": "FMO",
        "leave_eligible": False,
    },
    {
        "name": "Direct Commission Course + BOLC + Family Medicine Orientation",
        "activity_type": "orientation",
        "abbreviation": "DCC+BOLC",
        "leave_eligible": False,
    },
]


def login():
    """Login and get auth token."""
    resp = requests.post(
        f"{BASE_URL}/api/v1/auth/login/json",
        json={"username": "admin", "password": "AdminPassword123!"},
    )
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        sys.exit(1)
    return resp.json()["access_token"]


def create_template(data, headers):
    """Create a rotation template."""
    resp = requests.post(
        f"{BASE_URL}/api/v1/rotation-templates", json=data, headers=headers
    )
    if resp.status_code in [200, 201]:
        print(f"  ✓ Created {data['name']}")
        return True
    elif resp.status_code == 409 or "already exists" in resp.text.lower():
        print(f"  ⏭ Skipped {data['name']} (already exists)")
        return False
    else:
        print(f"  ✗ Failed {data['name']}: {resp.status_code} - {resp.text[:150]}")
        return False


def main():
    print("Logging in...")
    token = login()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\n=== Creating {len(ROTATIONS)} Rotation Templates ===\n")
    created = 0
    for rot in ROTATIONS:
        if create_template(rot, headers):
            created += 1

    print(f"\n=== Done! Created {created}/{len(ROTATIONS)} templates ===")


if __name__ == "__main__":
    main()
