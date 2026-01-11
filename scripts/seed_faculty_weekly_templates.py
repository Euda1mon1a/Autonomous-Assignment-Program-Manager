#!/usr/bin/env python3
"""Seed faculty weekly templates from primary duties data.

Reads sanitized_primary_duties.json and creates FacultyWeeklyTemplate records
for each faculty based on their primary duty requirements.

Run with: python scripts/seed_faculty_weekly_templates.py
"""
import json
import sys
from pathlib import Path
from uuid import UUID

import requests

BASE_URL = "http://localhost:8000"
DATA_DIR = Path("docs/schedules")
CONFIG_DIR = Path("config")

# Faculty role assignments - loaded from local config file (gitignored)
# See config/faculty_roles.local.json.example for format
FACULTY_ROLES_PATH = CONFIG_DIR / "faculty_roles.local.json"
if FACULTY_ROLES_PATH.exists():
    FACULTY_ROLES = json.loads(FACULTY_ROLES_PATH.read_text())
else:
    FACULTY_ROLES = {}
    print(f"Warning: {FACULTY_ROLES_PATH} not found. Using empty FACULTY_ROLES.")
    print("Copy config/faculty_roles.local.json.example to config/faculty_roles.local.json")
    print("and populate with your faculty role mappings.")

# Activity codes from database
ACTIVITIES = {
    "clinic": "fm_clinic",      # C
    "supervision": "at",         # AT (Attending Time)
    "gme": "gme",               # GME
    "sports_med": "sm_clinic",  # SM
    "dfm": "dfm",               # DFM
    "pcat": "pcat",             # PCAT
}

# Day mapping
DAYS = {
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6,
    "Sunday": 0,
}


def load_primary_duties():
    """Load primary duties from sanitized JSON."""
    path = DATA_DIR / "sanitized_primary_duties.json"
    with open(path) as f:
        data = json.load(f)
    return data.get("records", [])


def load_faculty():
    """Load faculty from sanitized JSON."""
    path = DATA_DIR / "sanitized_faculty.json"
    with open(path) as f:
        data = json.load(f)
    return data.get("records", [])


def get_db_faculty(headers):
    """Get faculty from database."""
    resp = requests.get(
        f"{BASE_URL}/api/v1/people",
        params={"type": "faculty", "limit": 100},
        headers=headers,
    )
    if resp.status_code != 200:
        print(f"Failed to get faculty: {resp.text}")
        return []
    return resp.json().get("items", [])


def get_db_activities(headers):
    """Get activities from database."""
    resp = requests.get(
        f"{BASE_URL}/api/v1/activities",
        headers=headers,
    )
    if resp.status_code != 200:
        print(f"Failed to get activities: {resp.text}")
        return {}
    activities = resp.json()
    # Map code to ID
    return {a["code"]: a["id"] for a in activities}


def login():
    """Login and get auth token."""
    # Try common passwords
    passwords = ["AdminPassword123!", "admin", "Admin123!"]
    for pwd in passwords:
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/login/json",
            json={"username": "admin", "password": pwd},
        )
        if resp.status_code == 200:
            return resp.json()["access_token"]
    print("Login failed - check admin password")
    return None


def get_faculty_role(faculty_name: str) -> str:
    """Determine faculty role from name."""
    for name_part, role in FACULTY_ROLES.items():
        if name_part.lower() in faculty_name.lower():
            return role
    return "core"


def generate_weekly_pattern(duty_fields: dict, role: str) -> list:
    """Generate weekly pattern based on primary duty requirements.

    Returns list of (day_of_week, time_of_day, activity_code) tuples.
    """
    pattern = []

    # Get available days
    available_days = []
    for day, day_num in DAYS.items():
        if day_num == 0 or day_num == 6:  # Skip weekends by default
            continue
        key = f"available{day}"
        if duty_fields.get(key, True):  # Default to available if not specified
            available_days.append(day_num)

    # Get requirements
    clinic_min = duty_fields.get("Clinic Minimum Half-Days Per Week", 0)
    clinic_max = duty_fields.get("Clinic Maximum Half-Days Per Week", 0)
    gme_min = duty_fields.get("Minimum Graduate Medical Education Half-Day Per Week", 0)
    gme_max = duty_fields.get("Maximum Graduate Medical Education Half-Days Per Week", 0)
    supervision_min = duty_fields.get("Resident Supervision Minimum Half-Days Per Week", 0)
    sm_min = duty_fields.get("Sports Medicine Minimum Half-Days Per Week copy", 0)
    sm_max = duty_fields.get("Sports Medicine Maximum Half-Days Per Week", 0)

    # Determine activity based on role
    if role == "adjunct":
        # Skip adjunct - manual only
        return []

    if role == "pd":
        # Program Director: mostly GME/Admin
        for day in available_days:
            pattern.append((day, "AM", "gme"))
            pattern.append((day, "PM", "gme"))
        return pattern

    if role == "sports_med":
        # Sports Med: SM Clinic + Supervision
        for day in available_days:
            pattern.append((day, "AM", "sports_med"))
            pattern.append((day, "PM", "supervision"))
        return pattern

    # Core faculty and leadership: Mix of clinic, supervision, GME
    slots_per_day = 2  # AM and PM
    total_slots = len(available_days) * slots_per_day

    # Allocate slots
    clinic_slots = min(clinic_max, total_slots // 3) if clinic_max else 3
    gme_slots = max(gme_min, 1) if gme_max else 1
    supervision_slots = total_slots - clinic_slots - gme_slots

    slot_index = 0
    for day in available_days:
        for time in ["AM", "PM"]:
            if slot_index < clinic_slots:
                activity = "clinic"
            elif slot_index < clinic_slots + gme_slots:
                activity = "gme"
            else:
                activity = "supervision"
            pattern.append((day, time, activity))
            slot_index += 1

    return pattern


def create_template_slot(person_id: str, day: int, time: str, activity_id: str, headers: dict):
    """Create a single template slot via API."""
    resp = requests.post(
        f"{BASE_URL}/api/v1/faculty/{person_id}/weekly-template/slots",
        json={
            "day_of_week": day,
            "time_of_day": time,
            "activity_id": activity_id,
            "is_locked": False,
            "priority": 50,
        },
        headers=headers,
    )
    return resp.status_code in [200, 201]


def main():
    print("=== Faculty Weekly Templates Seeder ===\n")

    # Login
    token = login()
    if not token:
        print("Cannot proceed without authentication")
        sys.exit(1)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Get database data
    db_faculty = get_db_faculty(headers)
    db_activities = get_db_activities(headers)

    if not db_faculty:
        print("No faculty found in database")
        sys.exit(1)

    print(f"Found {len(db_faculty)} faculty in database")
    print(f"Found {len(db_activities)} activities")

    # Load Airtable data
    primary_duties = load_primary_duties()
    airtable_faculty = load_faculty()

    print(f"Loaded {len(primary_duties)} primary duties from Airtable")
    print(f"Loaded {len(airtable_faculty)} faculty from Airtable")

    # Build faculty -> duty mapping from Airtable
    faculty_duty_map = {}
    for duty in primary_duties:
        fields = duty.get("fields", {})
        faculty_ids = fields.get("Faculty ID (from Faculty)", [])
        for fid in faculty_ids:
            faculty_duty_map[fid] = fields

    # Process each database faculty
    created = 0
    skipped = 0

    for faculty in db_faculty:
        name = faculty.get("name", "Unknown")
        person_id = faculty.get("id")
        role = get_faculty_role(name)

        print(f"\n{name} ({role}):")

        if role == "adjunct":
            print("  Skipped (adjunct - manual only)")
            skipped += 1
            continue

        # Find matching primary duty (best effort)
        duty_fields = {}
        for duty in primary_duties:
            fields = duty.get("fields", {})
            duty_name = fields.get("primaryDuty", "").lower()
            if role in duty_name or "bravo" in duty_name:  # Generic match
                duty_fields = fields
                break

        # Generate pattern
        pattern = generate_weekly_pattern(duty_fields, role)

        if not pattern:
            print("  No pattern generated")
            skipped += 1
            continue

        # Create slots
        slots_created = 0
        for day, time, activity_code in pattern:
            activity_id = db_activities.get(ACTIVITIES.get(activity_code, activity_code))
            if not activity_id:
                print(f"  Warning: Activity '{activity_code}' not found")
                continue

            if create_template_slot(person_id, day, time, activity_id, headers):
                slots_created += 1

        print(f"  Created {slots_created} slots")
        created += slots_created

    print(f"\n=== Done! Created {created} template slots, skipped {skipped} faculty ===")


if __name__ == "__main__":
    main()
