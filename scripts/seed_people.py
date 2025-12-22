#!/usr/bin/env python3
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
    resp = requests.post(f"{BASE_URL}/api/v1/people", json=data, headers=headers)
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
