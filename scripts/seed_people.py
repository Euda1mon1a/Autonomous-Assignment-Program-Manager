#!/usr/bin/env python3
<<<<<<< HEAD
"""Seed the database with test people."""
import json
import os
import requests
import sys

BASE_URL = os.getenv("SEED_BASE_URL", "http://localhost:8000")

# Read credentials from environment (allows override without editing code)
admin_username = os.getenv("SEED_ADMIN_USERNAME", "admin")
admin_password = os.getenv("SEED_ADMIN_PASSWORD", "admin123")

# Login to get token
login_resp = requests.post(
    f"{BASE_URL}/api/v1/auth/login/json",
    json={"username": admin_username, "password": admin_password}
)
if login_resp.status_code != 200:
    print(f"Login failed: {login_resp.text}")
    sys.exit(1)
    
token = login_resp.json()["access_token"]
print(f"Logged in successfully, token: {token[:20]}...")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def create_person(data):
=======
"""Seed the database with sample people.

Run with: python scripts/seed_people.py

NOTE: Uses synthetic identifiers per DATA_SECURITY_POLICY.md
Real personnel data should never be committed to the repository.
"""
import sys

import requests

BASE_URL = "http://localhost:8000"


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


def create_person(data, headers):
    """Create a person record."""
>>>>>>> origin/docs/session-14-summary
    resp = requests.post(f"{BASE_URL}/api/v1/people", json=data, headers=headers)
    if resp.status_code in [200, 201]:
        print(f"  ✓ Created {data['name']}")
        return True
<<<<<<< HEAD
=======
    elif resp.status_code == 409 or "already exists" in resp.text.lower():
        print(f"  ⏭ Skipped {data['name']} (already exists)")
        return False
>>>>>>> origin/docs/session-14-summary
    else:
        print(f"  ✗ Failed {data['name']}: {resp.status_code} - {resp.text[:150]}")
        return False


<<<<<<< HEAD
created_count = 0

# PGY-1 Residents (6)
print("\n=== Creating PGY-1 Residents ===")
pgy1_names = [
    "Alex Chen",
    "Jordan Lee",
    "Taylor Smith",
    "Morgan Davis",
    "Casey Brown",
    "Riley Wilson",
]
for name in pgy1_names:
    email = name.lower().replace(" ", ".") + "@residency.edu"
    if create_person(
        {"name": name, "type": "resident", "pgy_level": 1, "email": email}
    ):
        created_count += 1

# PGY-2 Residents (6)
print("\n=== Creating PGY-2 Residents ===")
pgy2_names = [
    "Jamie Garcia",
    "Sam Martinez",
    "Drew Anderson",
    "Quinn Thomas",
    "Reese Jackson",
    "Avery White",
]
for name in pgy2_names:
    email = name.lower().replace(" ", ".") + "@residency.edu"
    if create_person(
        {"name": name, "type": "resident", "pgy_level": 2, "email": email}
    ):
        created_count += 1

# PGY-3 Residents (6)
print("\n=== Creating PGY-3 Residents ===")
pgy3_names = [
    "Parker Harris",
    "Cameron Clark",
    "Blake Lewis",
    "Skyler Young",
    "Hayden King",
    "Emery Scott",
]
for name in pgy3_names:
    email = name.lower().replace(" ", ".") + "@residency.edu"
    if create_person(
        {"name": name, "type": "resident", "pgy_level": 3, "email": email}
    ):
        created_count += 1

# Faculty (10) - without "Dr." in email
print("\n=== Creating Faculty ===")
faculty_data = [
    {"name": "Dr. Sarah Johnson", "faculty_role": "pd", "email_name": "sarah.johnson"},
    {"name": "Dr. Michael Chen", "faculty_role": "apd", "email_name": "michael.chen"},
    {
        "name": "Dr. Emily Rodriguez",
        "faculty_role": "oic",
        "email_name": "emily.rodriguez",
    },
    {"name": "Dr. David Kim", "faculty_role": "dept_chief", "email_name": "david.kim"},
    {
        "name": "Dr. Lisa Patel",
        "faculty_role": "sports_med",
        "email_name": "lisa.patel",
    },
    {"name": "Dr. James Wilson", "faculty_role": "core", "email_name": "james.wilson"},
    {
        "name": "Dr. Amanda Thompson",
        "faculty_role": "core",
        "email_name": "amanda.thompson",
    },
    {
        "name": "Dr. Robert Garcia",
        "faculty_role": "core",
        "email_name": "robert.garcia",
    },
    {"name": "Dr. Michelle Lee", "faculty_role": "core", "email_name": "michelle.lee"},
    {
        "name": "Dr. Christopher Davis",
        "faculty_role": "core",
        "email_name": "chris.davis",
    },
]
for fac in faculty_data:
    if create_person(
        {
            "name": fac["name"],
            "type": "faculty",
            "faculty_role": fac["faculty_role"],
            "email": f"{fac['email_name']}@hospital.edu",
        }
    ):
        created_count += 1

# No screeners for now - API only supports resident/faculty types

print(f"\n=== Done! Created {created_count} people ===")
=======
def main():
    print("Logging in...")
    token = login()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    created_count = 0

    # ==================== PGY-1 RESIDENTS (6) ====================
    print("\n=== Creating PGY-1 Residents ===")
    pgy1 = [
        {"name": "PGY1-01", "pgy": 1},
        {"name": "PGY1-02", "pgy": 1},
        {"name": "PGY1-03", "pgy": 1},
        {"name": "PGY1-04", "pgy": 1},
        {"name": "PGY1-05", "pgy": 1},
        {"name": "PGY1-06", "pgy": 1},
    ]
    for r in pgy1:
        email = r["name"].lower().replace("-", "") + "@example.mil"
        if create_person(
            {"name": r["name"], "type": "resident", "pgy_level": 1, "email": email},
            headers,
        ):
            created_count += 1

    # ==================== PGY-2 RESIDENTS (6) ====================
    print("\n=== Creating PGY-2 Residents ===")
    pgy2 = [
        {"name": "PGY2-01", "pgy": 2},
        {"name": "PGY2-02", "pgy": 2},
        {"name": "PGY2-03", "pgy": 2},
        {"name": "PGY2-04", "pgy": 2},
        {"name": "PGY2-05", "pgy": 2},
        {"name": "PGY2-06", "pgy": 2},
    ]
    for r in pgy2:
        email = r["name"].lower().replace("-", "") + "@example.mil"
        if create_person(
            {"name": r["name"], "type": "resident", "pgy_level": 2, "email": email},
            headers,
        ):
            created_count += 1

    # ==================== PGY-3 RESIDENTS (5) ====================
    print("\n=== Creating PGY-3 Residents ===")
    pgy3 = [
        {"name": "PGY3-01", "pgy": 3},
        {"name": "PGY3-02", "pgy": 3},
        {"name": "PGY3-03", "pgy": 3},
        {"name": "PGY3-04", "pgy": 3},
        {"name": "PGY3-05", "pgy": 3},
    ]
    for r in pgy3:
        email = r["name"].lower().replace("-", "") + "@example.mil"
        if create_person(
            {"name": r["name"], "type": "resident", "pgy_level": 3, "email": email},
            headers,
        ):
            created_count += 1

    # ==================== FACULTY (12) ====================
    print("\n=== Creating Faculty ===")
    faculty = [
        {"name": "FAC-PD", "role": "pd"},
        {"name": "FAC-APD", "role": "apd"},
        {"name": "FAC-OIC", "role": "oic"},
        {"name": "FAC-CORE-01", "role": "core"},
        {"name": "FAC-CORE-02", "role": "core"},
        {"name": "FAC-CORE-03", "role": "core"},
        {"name": "FAC-CORE-04", "role": "core"},  # Example: excluded from assignments
        {"name": "FAC-CORE-05", "role": "core"},
        {"name": "FAC-CORE-06", "role": "core"},
        {"name": "FAC-SPORTS", "role": "sports_med"},
        {"name": "FAC-CORE-07", "role": "core"},
        {"name": "FAC-CHIEF", "role": "dept_chief"},
    ]
    for f in faculty:
        email = f["name"].lower().replace("-", ".") + "@example.mil"
        if create_person(
            {
                "name": f["name"],
                "type": "faculty",
                "faculty_role": f["role"],
                "email": email,
            },
            headers,
        ):
            created_count += 1

    print(f"\n=== Done! Created {created_count} people ===")


if __name__ == "__main__":
    main()
>>>>>>> origin/docs/session-14-summary
