#!/usr/bin/env python3
"""Seed the database with test people."""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

# Login to get token
login_resp = requests.post(
    f"{BASE_URL}/api/v1/auth/login/json",
    json={"username": "admin", "password": "AdminPassword123!"}
)
if login_resp.status_code != 200:
    print(f"Login failed: {login_resp.text}")
    sys.exit(1)
    
token = login_resp.json()["access_token"]
print(f"Logged in successfully, token: {token[:20]}...")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def create_person(data):
    resp = requests.post(f"{BASE_URL}/api/v1/people", json=data, headers=headers)
    if resp.status_code in [200, 201]:
        print(f"  ✓ Created {data['name']}")
        return True
    else:
        print(f"  ✗ Failed {data['name']}: {resp.status_code} - {resp.text[:150]}")
        return False


created_count = 0

***REMOVED*** (6)
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

***REMOVED*** (6)
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

***REMOVED*** (6)
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

***REMOVED*** (10) - without "Dr." in email
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
