#!/usr/bin/env python3
"""
Seed inpatient rotations from Airtable block schedule data.

This script reads the block_schedule.json and faculty_inpatient_schedule.json
and creates inpatient assignments in the database.

Usage:
    python scripts/seed_inpatient_rotations.py --block 10
    python scripts/seed_inpatient_rotations.py --block 10 --dry-run
    python scripts/seed_inpatient_rotations.py --block 10 --clear-first
"""

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import requests

# Configuration
BASE_URL = os.getenv("SEED_BASE_URL", "http://localhost:8000")
DATA_DIR = Path(__file__).parent.parent / "docs" / "schedules"

# Inpatient rotation keywords
INPATIENT_KEYWORDS = [
    "FMIT",
    "Night Float",
    "Inpatient",
    "NICU",
    "Neonatal Intensive Care",
    "Labor and Delivery Night",
    "Pediatrics Night Float",
]


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


def load_json(filename: str) -> dict:
    """Load JSON file from data directory."""
    # Try both sanitized and de-sanitized versions
    for prefix in ["", "sanitized_"]:
        path = DATA_DIR / f"{prefix}{filename}"
        if path.exists():
            with open(path) as f:
                return json.load(f)

    # Also check docs/data for backward compatibility
    alt_dir = Path(__file__).parent.parent / "docs" / "data"
    for prefix in ["", "sanitized_"]:
        path = alt_dir / f"{prefix}{filename}"
        if path.exists():
            with open(path) as f:
                return json.load(f)

    raise FileNotFoundError(f"Cannot find {filename} in {DATA_DIR} or {alt_dir}")


def get_people_mapping(headers: dict) -> dict:
    """Get mapping of person names to database IDs."""
    resp = requests.get(f"{BASE_URL}/api/v1/people", headers=headers)
    if resp.status_code != 200:
        print(f"Failed to get people: {resp.text}")
        sys.exit(1)

    people = resp.json()
    if isinstance(people, dict) and "items" in people:
        people = people["items"]

    return {p["name"]: p["id"] for p in people}


def get_rotation_templates(headers: dict) -> dict:
    """Get mapping of rotation names to database IDs."""
    resp = requests.get(f"{BASE_URL}/api/v1/rotation-templates", headers=headers)
    if resp.status_code != 200:
        print(f"Failed to get rotation templates: {resp.text}")
        sys.exit(1)

    templates = resp.json()
    if isinstance(templates, dict) and "items" in templates:
        templates = templates["items"]

    return {t["name"]: t for t in templates}


def get_blocks_for_block_number(headers: dict, block_number: int) -> list:
    """Get all half-day blocks for a given academic block number."""
    resp = requests.get(
        f"{BASE_URL}/api/v1/blocks",
        params={"block_number": block_number, "limit": 100},
        headers=headers,
    )
    if resp.status_code != 200:
        print(f"Failed to get blocks: {resp.text}")
        sys.exit(1)

    blocks = resp.json()
    if isinstance(blocks, dict) and "items" in blocks:
        blocks = blocks["items"]

    return sorted(blocks, key=lambda b: (b["date"], b["time_of_day"]))


def is_inpatient_rotation(rotation_name: str) -> bool:
    """Check if a rotation name indicates inpatient duty."""
    return any(kw.lower() in rotation_name.lower() for kw in INPATIENT_KEYWORDS)


def get_inpatient_template(templates: dict, rotation_name: str) -> dict | None:
    """Find the appropriate inpatient template for a rotation."""
    rotation_lower = rotation_name.lower()

    # Try exact match first
    if rotation_name in templates:
        return templates[rotation_name]

    # Map rotation names to template names
    if "fmit" in rotation_lower or "family medicine inpatient" in rotation_lower:
        # FMIT assignments use FMIT AM/PM templates
        return templates.get("FMIT AM") or templates.get("FMIT PM")
    elif "night float" in rotation_lower or "night" in rotation_lower:
        return templates.get("Night Float AM") or templates.get("Night Float PM")
    elif "nicu" in rotation_lower or "neonatal" in rotation_lower:
        return templates.get("NICU")
    elif "labor and delivery" in rotation_lower:
        return templates.get("Night Float AM") or templates.get("Night Float PM")

    return None


def clear_block_assignments(headers: dict, block_number: int, dry_run: bool) -> int:
    """Clear existing assignments for a block."""
    # This needs to be done via direct DB or a delete endpoint
    # For now, we'll document this as a manual step
    print(f"  [NOTE] Clear assignments via: ")
    print(f"    docker compose exec db psql -U scheduler -d residency_scheduler \\")
    print(f"      -c \"DELETE FROM assignments WHERE block_id IN (")
    print(f"           SELECT id FROM blocks WHERE block_number = {block_number});\"")
    return 0


def create_assignment(
    headers: dict,
    person_id: str,
    block_id: str,
    template_id: str,
    role: str = "primary",
    dry_run: bool = False,
) -> bool:
    """Create a single assignment."""
    if dry_run:
        return True

    resp = requests.post(
        f"{BASE_URL}/api/v1/assignments",
        json={
            "person_id": person_id,
            "block_id": block_id,
            "rotation_template_id": template_id,
            "role": role,
        },
        headers=headers,
    )

    if resp.status_code in [200, 201]:
        return True
    elif resp.status_code == 409:
        # Duplicate - already exists
        return True
    else:
        print(f"    Failed to create assignment: {resp.status_code} - {resp.text[:100]}")
        return False


def seed_resident_inpatient(
    block_number: int,
    headers: dict,
    people: dict,
    templates: dict,
    blocks: list,
    dry_run: bool,
) -> int:
    """Seed resident inpatient assignments from block_schedule.json."""
    print(f"\n=== Seeding Resident Inpatient Rotations (Block {block_number}) ===")

    try:
        data = load_json("block_schedule.json")
    except FileNotFoundError:
        print("  [SKIP] block_schedule.json not found")
        return 0

    created = 0

    for rec in data["records"]:
        fields = rec["fields"]
        rec_block = fields.get("blockNumber", [""])[0]

        # Filter to target block
        if str(rec_block) != str(block_number):
            continue

        rotation_name = fields.get("rotationName", [""])[0]
        resident_name = fields.get("Resident", [""])[0]

        # Only process inpatient rotations
        if not is_inpatient_rotation(rotation_name):
            continue

        # Find person in database
        person_id = people.get(resident_name)
        if not person_id:
            print(f"  [WARN] Person not found: {resident_name}")
            continue

        # Find appropriate template
        template = get_inpatient_template(templates, rotation_name)
        if not template:
            print(f"  [WARN] No template for rotation: {rotation_name}")
            continue

        print(f"  {resident_name}: {rotation_name}")

        # Create assignment for each half-day block
        for block in blocks:
            # Use AM or PM template based on time of day
            tod = block["time_of_day"]
            template_name = template["name"]

            # Swap AM/PM if needed
            if "AM" in template_name and tod == "PM":
                alt_name = template_name.replace("AM", "PM")
                if alt_name in templates:
                    template = templates[alt_name]
            elif "PM" in template_name and tod == "AM":
                alt_name = template_name.replace("PM", "AM")
                if alt_name in templates:
                    template = templates[alt_name]

            success = create_assignment(
                headers,
                person_id,
                block["id"],
                template["id"],
                role="primary",
                dry_run=dry_run,
            )
            if success:
                created += 1

    return created


def seed_faculty_fmit(
    block_number: int,
    headers: dict,
    people: dict,
    templates: dict,
    dry_run: bool,
) -> int:
    """Seed faculty FMIT assignments from faculty_inpatient_schedule.json."""
    print(f"\n=== Seeding Faculty FMIT (Block {block_number}) ===")

    try:
        data = load_json("faculty_inpatient_schedule.json")
    except FileNotFoundError:
        print("  [SKIP] faculty_inpatient_schedule.json not found")
        return 0

    created = 0

    for rec in data["records"]:
        fields = rec["fields"]
        rec_block = fields.get("blockNumber")

        if rec_block != block_number:
            continue

        week = fields.get("weekOfBlock")
        start_date = fields.get("Inpatient Week Start")
        end_date = fields.get("Inpatient Week End")
        title = fields.get("blockWeekInpatientAttending", "")

        # Extract faculty name (last part after " - ")
        faculty_name = title.split(" - ")[-1] if title else None
        if not faculty_name:
            continue

        person_id = people.get(faculty_name)
        if not person_id:
            print(f"  [WARN] Faculty not found: {faculty_name}")
            continue

        print(f"  Week {week}: {faculty_name} ({start_date} to {end_date})")

        # Get FMIT templates
        fmit_am = templates.get("FMIT AM")
        fmit_pm = templates.get("FMIT PM")

        if not fmit_am or not fmit_pm:
            print("  [WARN] FMIT AM/PM templates not found")
            continue

        # Get blocks for this week
        resp = requests.get(
            f"{BASE_URL}/api/v1/blocks",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "limit": 100,
            },
            headers=headers,
        )

        if resp.status_code != 200:
            print(f"  [WARN] Failed to get blocks for week: {resp.text}")
            continue

        week_blocks = resp.json()
        if isinstance(week_blocks, dict) and "items" in week_blocks:
            week_blocks = week_blocks["items"]

        for block in week_blocks:
            tod = block["time_of_day"]
            template = fmit_am if tod == "AM" else fmit_pm

            success = create_assignment(
                headers,
                person_id,
                block["id"],
                template["id"],
                role="primary",
                dry_run=dry_run,
            )
            if success:
                created += 1

    return created


def main():
    parser = argparse.ArgumentParser(description="Seed inpatient rotations")
    parser.add_argument("--block", type=int, required=True, help="Block number (1-13)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument(
        "--clear-first", action="store_true", help="Clear existing assignments first"
    )
    args = parser.parse_args()

    if args.dry_run:
        print("[DRY RUN MODE - No changes will be made]")

    # Authenticate
    print("\nAuthenticating...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("  ✓ Authenticated")

    # Load mappings
    print("\nLoading database mappings...")
    people = get_people_mapping(headers)
    print(f"  ✓ {len(people)} people")

    templates = get_rotation_templates(headers)
    print(f"  ✓ {len(templates)} rotation templates")

    blocks = get_blocks_for_block_number(headers, args.block)
    print(f"  ✓ {len(blocks)} half-day blocks for Block {args.block}")

    # Clear if requested
    if args.clear_first:
        print(f"\nClearing existing Block {args.block} assignments...")
        clear_block_assignments(headers, args.block, args.dry_run)

    # Seed resident inpatient
    resident_count = seed_resident_inpatient(
        args.block, headers, people, templates, blocks, args.dry_run
    )

    # Seed faculty FMIT
    faculty_count = seed_faculty_fmit(
        args.block, headers, people, templates, args.dry_run
    )

    # Summary
    print(f"\n=== Summary ===")
    print(f"  Resident inpatient assignments: {resident_count}")
    print(f"  Faculty FMIT assignments: {faculty_count}")
    print(f"  Total: {resident_count + faculty_count}")

    if args.dry_run:
        print("\n[DRY RUN - No changes were made]")
    else:
        print("\n✓ Inpatient rotations seeded successfully")
        print("\nNext step: Re-run outpatient solver to fill remaining slots")
        print(f"  curl -X POST http://localhost:8000/api/v1/schedule/generate ...")


if __name__ == "__main__":
    main()
