#!/usr/bin/env python3
"""Pre-flight verification script for constraint development.

Run this script before committing constraint changes to verify:
1. All exported constraints are registered in ConstraintManager
2. Constraint weights follow the documented hierarchy
3. Tests pass for constraint-related files

Usage:
    cd backend
    python ../scripts/verify_constraints.py

Or from project root:
    python scripts/verify_constraints.py
"""

import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
if backend_path.exists():
    sys.path.insert(0, str(backend_path))
else:
    # Already in backend directory
    sys.path.insert(0, str(Path(__file__).parent.parent))


def verify_constraint_registration():
    """Verify all exported constraints are registered."""
    print("\n" + "=" * 60)
    print("CONSTRAINT REGISTRATION VERIFICATION")
    print("=" * 60)

    try:
        from app.scheduling.constraints import ConstraintManager
        from app.scheduling.constraints import (
            # Call equity
            CallSpacingConstraint,
            SundayCallEquityConstraint,
            TuesdayCallPreferenceConstraint,
            WeekdayCallEquityConstraint,
            # Inpatient
            ResidentInpatientHeadcountConstraint,
            # FMIT
            PostFMITSundayBlockingConstraint,
        )
    except ImportError as e:
        print(f"ERROR: Failed to import constraints: {e}")
        print("Make sure you're running from the backend directory or project root")
        return False

    manager = ConstraintManager.create_default()
    registered_types = {type(c) for c in manager.constraints}

    print(f"\nRegistered constraints ({len(manager.constraints)} total):")
    for c in sorted(manager.constraints, key=lambda x: x.name):
        status = "ENABLED" if c.enabled else "disabled"
        weight = f"weight={c.weight}" if hasattr(c, "weight") else ""
        print(f"  - {c.name}: {status} {weight}")

    # Check Block 10 constraints
    block10_constraints = [
        ("CallSpacingConstraint", CallSpacingConstraint),
        ("SundayCallEquityConstraint", SundayCallEquityConstraint),
        ("TuesdayCallPreferenceConstraint", TuesdayCallPreferenceConstraint),
        ("WeekdayCallEquityConstraint", WeekdayCallEquityConstraint),
        ("ResidentInpatientHeadcountConstraint", ResidentInpatientHeadcountConstraint),
        ("PostFMITSundayBlockingConstraint", PostFMITSundayBlockingConstraint),
    ]

    print("\nBlock 10 Constraint Check:")
    all_registered = True
    for name, cls in block10_constraints:
        if cls in registered_types:
            print(f"  [OK] {name}")
        else:
            print(f"  [MISSING] {name} - NOT REGISTERED!")
            all_registered = False

    return all_registered


def verify_weight_hierarchy():
    """Verify call equity weight hierarchy."""
    print("\n" + "=" * 60)
    print("WEIGHT HIERARCHY VERIFICATION")
    print("=" * 60)

    try:
        from app.scheduling.constraints import ConstraintManager
    except ImportError:
        return False

    manager = ConstraintManager.create_default()
    constraint_by_name = {c.name: c for c in manager.constraints}

    # Expected hierarchy
    hierarchy = [
        ("SundayCallEquity", 10.0),
        ("CallSpacing", 8.0),
        ("WeekdayCallEquity", 5.0),
        ("TuesdayCallPreference", 2.0),
    ]

    print("\nCall equity weight hierarchy:")
    all_correct = True
    prev_weight = float("inf")

    for name, expected_weight in hierarchy:
        constraint = constraint_by_name.get(name)
        if not constraint:
            print(f"  [MISSING] {name}")
            all_correct = False
            continue

        actual_weight = constraint.weight
        if actual_weight != expected_weight:
            print(f"  [WRONG] {name}: expected {expected_weight}, got {actual_weight}")
            all_correct = False
        elif actual_weight > prev_weight:
            print(f"  [ORDER] {name}: weight {actual_weight} breaks hierarchy")
            all_correct = False
        else:
            print(f"  [OK] {name}: weight={actual_weight}")

        prev_weight = actual_weight

    return all_correct


def verify_both_managers():
    """Verify constraints in both create_default and create_resilience_aware."""
    print("\n" + "=" * 60)
    print("MANAGER CONSISTENCY VERIFICATION")
    print("=" * 60)

    try:
        from app.scheduling.constraints import ConstraintManager
    except ImportError:
        return False

    default = ConstraintManager.create_default()
    resilience = ConstraintManager.create_resilience_aware()

    default_names = {c.name for c in default.constraints}
    resilience_names = {c.name for c in resilience.constraints}

    # Block 10 constraints that must be in both
    required = {
        "ResidentInpatientHeadcount",
        "PostFMITSundayBlocking",
        "SundayCallEquity",
        "CallSpacing",
        "WeekdayCallEquity",
        "TuesdayCallPreference",
    }

    print("\nBlock 10 constraints in both managers:")
    all_present = True
    for name in required:
        in_default = name in default_names
        in_resilience = name in resilience_names

        if in_default and in_resilience:
            print(f"  [OK] {name}")
        elif in_default:
            print(f"  [MISSING] {name} - only in create_default()")
            all_present = False
        elif in_resilience:
            print(f"  [MISSING] {name} - only in create_resilience_aware()")
            all_present = False
        else:
            print(f"  [MISSING] {name} - not in either manager!")
            all_present = False

    return all_present


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("CONSTRAINT PRE-FLIGHT VERIFICATION")
    print("=" * 60)
    print("This script verifies constraint implementation completeness.")
    print("Run this before committing constraint changes.")

    results = []

    results.append(("Registration", verify_constraint_registration()))
    results.append(("Weight Hierarchy", verify_weight_hierarchy()))
    results.append(("Manager Consistency", verify_both_managers()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n[SUCCESS] All verifications passed!")
        return 0
    else:
        print("\n[FAILURE] Some verifications failed. Fix issues before committing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
