#!/usr/bin/env python3
"""Seed default feature flags.

Run with: python scripts/seed_feature_flags.py

This script creates the default feature flags for the application.
Flags can later be modified via the admin API at /api/v1/features/.
"""

import sys

import requests

BASE_URL = "http://localhost:8000"

# Default feature flags
FEATURE_FLAGS = [
    {
        "key": "swap_marketplace_enabled",
        "name": "Enable Swap Marketplace",
        "description": (
            "Controls access to the swap marketplace. "
            "When enabled for a role, users with that role can browse the marketplace "
            "and post swaps for anyone to claim. "
            "Disabled by default for residents to prevent gamification of swaps "
            "(e.g., exploiting post-call PCAT/DO rules to avoid clinic duties)."
        ),
        "flag_type": "boolean",
        "enabled": True,
        # Only allow these roles to access marketplace (excludes 'resident')
        "target_roles": ["admin", "coordinator", "faculty"],
        "environments": None,  # All environments
        "rollout_percentage": None,
        "target_user_ids": None,
        "variants": None,
        "dependencies": None,
        "custom_attributes": None,
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


def create_flag(data: dict, headers: dict) -> bool:
    """Create a feature flag."""
    resp = requests.post(
        f"{BASE_URL}/api/v1/features/",
        json=data,
        headers=headers,
    )
    if resp.status_code in [200, 201]:
        print(f"  Created {data['key']}")
        return True
    elif resp.status_code == 400 and "already exists" in resp.text.lower():
        print(f"  Skipped {data['key']} (already exists)")
        return False
    else:
        print(f"  Failed {data['key']}: {resp.status_code} - {resp.text[:150]}")
        return False


def main():
    print("Logging in...")
    token = login()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\n=== Creating {len(FEATURE_FLAGS)} Feature Flags ===\n")
    created = 0
    for flag in FEATURE_FLAGS:
        if create_flag(flag, headers):
            created += 1

    print(f"\n=== Done! Created {created}/{len(FEATURE_FLAGS)} flags ===")

    # Print usage instructions
    print("\n--- Swap Marketplace Configuration ---")
    print("The swap marketplace is now disabled for residents by default.")
    print("\nTo enable for a specific resident:")
    print("  1. Add their user ID to 'target_user_ids' in the flag")
    print("  2. Or add 'resident' to 'target_roles' to enable for all residents")
    print("\nAPI endpoints:")
    print("  GET  /api/v1/features/swap_marketplace_enabled")
    print("  PUT  /api/v1/features/swap_marketplace_enabled")
    print("  POST /api/v1/features/swap_marketplace_enabled/enable")
    print("  POST /api/v1/features/swap_marketplace_enabled/disable")


if __name__ == "__main__":
    main()
