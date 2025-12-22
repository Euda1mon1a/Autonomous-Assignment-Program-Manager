#!/usr/bin/env python3
"""
Airtable Sync Script - Fetches data from Airtable and imports into local database.

Fetches:
- Residents (people)
- Faculty (people)
- Rotation Templates (clinic templates)

Data is saved to docs/data/ (gitignored) then imported to database.
No PII is stored in this script - all data comes from Airtable API.

Usage:
    # Fetch from Airtable and save to JSON
    python scripts/airtable_sync.py fetch

    # Import from JSON to database
    python scripts/airtable_sync.py import

    # Both in one step
    python scripts/airtable_sync.py sync

Environment Variables:
    AIRTABLE_API_KEY - Airtable Personal Access Token
    AIRTABLE_BASE_ID - Airtable Base ID (default: appDgFtrU7njCKDW5)
    SEED_BASE_URL - API base URL (default: http://localhost:8000)
    SEED_ADMIN_USERNAME - Admin username (default: admin)
    SEED_ADMIN_PASSWORD - Admin password (default: admin123)
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Airtable config
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "appDgFtrU7njCKDW5")

# Table IDs from Airtable
TABLES = {
    "residents": "tblbsetAVqoDqcjgo",
    "faculty": "tblmgzodmqTsJ5inf",
    "clinic_templates": "tblHTCeipFRtL242K",
    "rotation_templates": "tblLUzjfad4B1GQ1a",
    "primary_duties": "tbltYT3HMWxGCcCfo",
    "block_schedule": "tbl3TfpZSGYGxlCIG",
    "blocks": "tblWHxncXVwlxXV4i",
    "resident_assignments": "tbl17gcDUtXc14Rjv",
    "faculty_assignments": "tbloGnXnu0mC6y83L",
}

# Output directory (gitignored)
DATA_DIR = Path(__file__).parent.parent / "docs" / "data"


def fetch_airtable_table(table_id: str, table_name: str) -> list[dict]:
    """Fetch all records from an Airtable table."""
    import urllib.request
    import urllib.error

    if not AIRTABLE_API_KEY:
        print("ERROR: AIRTABLE_API_KEY environment variable not set")
        sys.exit(1)

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table_id}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

    all_records = []
    offset = None

    while True:
        req_url = url
        if offset:
            req_url += f"?offset={offset}"

        request = urllib.request.Request(req_url, headers=headers)

        try:
            with urllib.request.urlopen(request) as response:
                data = json.loads(response.read().decode())
                all_records.extend(data.get("records", []))
                offset = data.get("offset")
                if not offset:
                    break
        except urllib.error.HTTPError as e:
            print(f"ERROR fetching {table_name}: {e.code} {e.reason}")
            sys.exit(1)

    print(f"  Fetched {len(all_records)} records from {table_name}")
    return all_records


def fetch_all():
    """Fetch all tables from Airtable and save to JSON files."""
    print("Fetching data from Airtable...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()

    for name, table_id in TABLES.items():
        records = fetch_airtable_table(table_id, name)

        output = {
            "fetched_at": timestamp,
            "table_name": name,
            "table_id": table_id,
            "record_count": len(records),
            "records": records,
        }

        output_path = DATA_DIR / f"airtable_{name}.json"
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2, default=str)

        print(f"  Saved to {output_path}")

    print(f"\nFetch complete! Data saved to {DATA_DIR}/")


def load_json(name: str) -> list[dict]:
    """Load records from a saved JSON file."""
    path = DATA_DIR / f"airtable_{name}.json"
    if not path.exists():
        print(f"ERROR: {path} not found. Run 'fetch' first.")
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    return data.get("records", [])


def get_api_token() -> str:
    """Get API token for local database."""
    import urllib.request
    import urllib.error

    base_url = os.getenv("SEED_BASE_URL", "http://localhost:8000")
    username = os.getenv("SEED_ADMIN_USERNAME", "admin")
    password = os.getenv("SEED_ADMIN_PASSWORD", "admin123")

    login_data = json.dumps({"username": username, "password": password}).encode()
    request = urllib.request.Request(
        f"{base_url}/api/v1/auth/login/json",
        data=login_data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode())
            return data["access_token"]
    except urllib.error.HTTPError as e:
        print(f"ERROR logging in: {e.code} {e.reason}")
        sys.exit(1)


def api_post(token: str, endpoint: str, data: dict) -> tuple[int, dict]:
    """POST to the local API."""
    import urllib.request
    import urllib.error

    base_url = os.getenv("SEED_BASE_URL", "http://localhost:8000")
    url = f"{base_url}/api/v1/{endpoint}"

    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return e.code, {"error": body}


def import_people(token: str):
    """Import residents and faculty from saved JSON."""
    print("\nImporting people...")

    # Import residents
    residents = load_json("residents")
    created = 0
    skipped = 0

    for record in residents:
        fields = record.get("fields", {})
        first_name = fields.get("First Name", "")
        last_name = fields.get("Resident", "")  # Last name is in "Resident" field

        if not first_name or not last_name:
            skipped += 1
            continue

        name = f"{first_name} {last_name}"
        pgy_list = fields.get("postGraduateYear", [])
        pgy = int(pgy_list[0]) if pgy_list else 1
        email = fields.get("Email Address", "")
        airtable_id = record.get("id", "")

        person_data = {
            "name": name,
            "type": "resident",
            "pgy_level": pgy,
            "email": email,
            "external_id": airtable_id,  # Store Airtable ID for linking
        }

        status, resp = api_post(token, "people", person_data)
        if status in (200, 201):
            print(f"  + Resident: {name} (PGY-{pgy})")
            created += 1
        else:
            # Check if duplicate
            if "already exists" in str(resp).lower() or status == 409:
                skipped += 1
            else:
                print(f"  ! Failed: {name} - {resp}")
                skipped += 1

    print(f"  Residents: {created} created, {skipped} skipped")

    # Import faculty
    faculty = load_json("faculty")
    created = 0
    skipped = 0

    for record in faculty:
        fields = record.get("fields", {})
        first_name = fields.get("First Name", "")
        last_name = fields.get("Last Name", "")

        if not first_name or not last_name:
            skipped += 1
            continue

        name = f"{first_name} {last_name}"
        faculty_type = fields.get("Faculty Type", "")
        email = fields.get("Email Address", "")
        airtable_id = record.get("id", "")
        performs_proc = bool(fields.get("Performs Procedure"))

        # Map faculty type to role (adjunct not in enum, use core)
        role = "core"
        # Valid roles: pd, apd, oic, dept_chief, sports_med, core

        # Generate placeholder email if missing (use example.com per RFC 2606)
        if not email:
            safe_name = name.lower().replace(" ", ".").replace("'", "")
            email = f"{safe_name}@example.com"

        person_data = {
            "name": name,
            "type": "faculty",
            "faculty_role": role,
            "email": email,
            "external_id": airtable_id,
            "performs_procedures": performs_proc,
        }

        status, resp = api_post(token, "people", person_data)
        if status in (200, 201):
            print(f"  + Faculty: {name} ({role})")
            created += 1
        else:
            if "already exists" in str(resp).lower() or status == 409:
                skipped += 1
            else:
                print(f"  ! Failed: {name} - {resp}")
                skipped += 1

    print(f"  Faculty: {created} created, {skipped} skipped")


def import_rotation_templates(token: str):
    """Import rotation templates from saved JSON."""
    print("\nImporting rotation templates...")

    templates = load_json("clinic_templates")
    created = 0
    skipped = 0

    for record in templates:
        fields = record.get("fields", {})
        name = fields.get("name", "")

        if not name:
            skipped += 1
            continue

        airtable_id = record.get("id", "")
        activity_key = fields.get("activityKey", name)

        # Generate abbreviation from name
        # e.g., "Inpatient Attending AM" -> "INA-AM"
        # e.g., "Clinic PM" -> "CLI-PM"
        words = name.replace("-", " ").split()
        time_suffix = ""
        if words and words[-1] in ("AM", "PM"):
            time_suffix = f"-{words[-1]}"
            words = words[:-1]

        if len(words) >= 2:
            abbrev = (words[0][:2] + words[1][:1]).upper() + time_suffix
        elif words:
            abbrev = words[0][:3].upper() + time_suffix
        else:
            abbrev = "UNK"

        # Determine activity type from name
        activity_type = "outpatient"  # default
        name_lower = name.lower()
        if "inpatient" in name_lower:
            activity_type = "inpatient"
        elif "lecture" in name_lower or "education" in name_lower:
            activity_type = "education"
        elif "call" in name_lower:
            activity_type = "call"
        elif "off" in name_lower:
            activity_type = "off"
        elif "procedure" in name_lower or "botox" in name_lower or "vasectomy" in name_lower:
            activity_type = "procedures"
        elif "sports" in name_lower:
            activity_type = "outpatient"

        # Determine days of week
        days = []
        if fields.get("monday"):
            days.append("monday")
        if fields.get("Tuesday"):
            days.append("tuesday")
        if fields.get("Wednesday"):
            days.append("wednesday")
        if fields.get("Thursday"):
            days.append("thursday")
        if fields.get("friday"):
            days.append("friday")
        if fields.get("Saturday"):
            days.append("saturday")
        if fields.get("Sunday"):
            days.append("sunday")

        template_data = {
            "name": name,
            "abbreviation": abbrev,
            "activity_type": activity_type,
            "external_id": airtable_id,
            # "days_of_week": days,  # If schema supports it
        }

        status, resp = api_post(token, "rotation-templates", template_data)
        if status in (200, 201):
            print(f"  + Template: {name} ({abbrev})")
            created += 1
        else:
            if "already exists" in str(resp).lower() or status == 409:
                skipped += 1
            else:
                print(f"  ! Failed: {name} - {resp}")
                skipped += 1

    print(f"  Templates: {created} created, {skipped} skipped")


def import_all():
    """Import all data from JSON files to database."""
    print("Importing data to local database...")

    token = get_api_token()
    print(f"  Authenticated successfully")

    import_people(token)
    import_rotation_templates(token)

    print("\nImport complete!")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "fetch":
        fetch_all()
    elif command == "import":
        import_all()
    elif command == "sync":
        fetch_all()
        import_all()
    else:
        print(f"Unknown command: {command}")
        print("Commands: fetch, import, sync")
        sys.exit(1)


if __name__ == "__main__":
    main()
