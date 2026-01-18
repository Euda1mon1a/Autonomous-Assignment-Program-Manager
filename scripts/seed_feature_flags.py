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
    {
        "key": "labs_hub_enabled",
        "name": "Research Labs Hub",
        "description": (
            "Gates access to the experimental Research Labs Hub (/admin/labs). "
            "Contains wellness analytics, optimization algorithms, fairness metrics, "
            "and advanced resilience tools. Enabled by default for admin and coordinator roles."
        ),
        "flag_type": "boolean",
        "enabled": True,
        "target_roles": ["admin", "coordinator"],
        "environments": None,
        "rollout_percentage": None,
        "target_user_ids": None,
        "variants": None,
        "dependencies": None,
        "custom_attributes": None,
    },
    {
        "key": "exotic_resilience_enabled",
        "name": "Exotic Resilience Features",
        "description": (
            "Gates access to exotic resilience endpoints including thermodynamics (entropy, "
            "phase transitions), immune system (AIS anomaly detection), time crystal "
            "(anti-churn, periodicity), and advanced physics-based analytics. "
            "Disabled by default due to experimental nature and computational cost."
        ),
        "flag_type": "boolean",
        "enabled": False,
        "target_roles": ["admin"],
        "environments": None,
        "rollout_percentage": None,
        "target_user_ids": None,
        "variants": None,
        "dependencies": None,
        "custom_attributes": None,
    },
    {
        "key": "voxel_visualization_enabled",
        "name": "3D Voxel Grid Visualization",
        "description": (
            "Gates access to the 3D voxel grid visualization for schedule coverage. "
            "Performance-intensive feature that renders schedule data as 3D WebGL elements. "
            "Disabled by default due to high client-side resource requirements."
        ),
        "flag_type": "boolean",
        "enabled": False,
        "target_roles": ["admin"],
        "environments": None,
        "rollout_percentage": None,
        "target_user_ids": None,
        "variants": None,
        "dependencies": None,
        "custom_attributes": None,
    },
    {
        "key": "command_center_enabled",
        "name": "Command Center Dashboard",
        "description": (
            "Gates access to the Command Center overseer dashboard. "
            "Provides real-time operational overview, incident management, "
            "and cross-system monitoring. Disabled by default for admin-only access."
        ),
        "flag_type": "boolean",
        "enabled": False,
        "target_roles": ["admin"],
        "environments": None,
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
    print("\n--- Feature Flag Semantics ---")
    print("IMPORTANT: None vs empty list ([]) have different meanings:")
    print("  target_roles: None  = all roles allowed (if flag enabled)")
    print("  target_roles: []    = NO roles allowed")
    print("  target_user_ids: None = no user-specific targeting")
    print("  target_user_ids: []   = NO users allowed (blocks everyone)")
    print("  environments: None    = all environments")
    print("  environments: []      = NO environments (flag never applies)")
    print("\nEnvironment is read from TELEMETRY_ENVIRONMENT setting.")


if __name__ == "__main__":
    main()
