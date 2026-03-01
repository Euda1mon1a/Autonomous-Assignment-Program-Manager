#!/usr/bin/env python3
"""Constraint stress test — enable disabled constraints one at a time.

For each disabled policy-hard constraint:
1. Enable ONLY that constraint (all others stay disabled)
2. Run the solver (no commit — rollback after)
3. Report OPTIMAL / INFEASIBLE / error
4. Move to next constraint

Usage:
    cd backend && SKIP_SETTINGS_VALIDATION=1 .venv/bin/python \
        ../scripts/scheduling/constraint_stress_test.py
"""

import os
import sys
import time

backend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
sys.path.insert(0, os.path.abspath(backend_dir))
os.environ["SKIP_SETTINGS_VALIDATION"] = "1"

from app.db.session import SessionLocal
from app.scheduling.engine import SchedulingEngine
from app.utils.academic_blocks import get_block_dates

# The 18 disabled policy-hard constraints, ordered safest → riskiest
CONSTRAINTS_TO_TEST = [
    "ClinicCapacity",
    "FacultyClinicCap",
    "NightFloatPostCall",
    "PostFMITRecovery",
    "PostFMITSundayBlocking",
    "FacultyDayAvailability",
    "FacultyPrimaryDutyClinic",
    "FacultyRoleClinic",
    "MaxPhysiciansInClinic",
    "WednesdayAMInternOnly",
    "InvertedWednesday",
    "ResidentInpatientHeadcount",
    "OvernightCallCoverage",
    "SupervisionRatio",
    "FacultySupervision",
    "80HourRule",
    "1in7Rule",
    # WednesdayPMSingleFaculty needs variable refactor — skip
]


def test_constraint(constraint_name: str, block_number: int, academic_year: int):
    """Enable one constraint, run solver, report result, rollback."""
    block_dates = get_block_dates(block_number, academic_year)
    db = SessionLocal()

    try:
        engine = SchedulingEngine(
            db=db,
            start_date=block_dates.start_date,
            end_date=block_dates.end_date,
        )

        # Enable just this one constraint
        engine.constraint_manager.enable(constraint_name)

        # Verify it's actually enabled
        enabled_names = [c.name for c in engine.constraint_manager.get_enabled()]
        if constraint_name not in enabled_names:
            return "SKIP", "Not found in constraint list", 0.0

        start = time.time()
        result = engine.generate(
            block_number=block_number,
            academic_year=academic_year,
            algorithm="cp_sat",
            timeout_seconds=30.0,
            check_resilience=False,
            validate_pcat_do=False,
        )
        elapsed = time.time() - start

        status = result.get("status", "unknown")
        msg = result.get("message", "")
        assignments = result.get("total_assigned", 0)

        if status == "success":
            return "OPTIMAL", f"{assignments} assignments", elapsed
        else:
            # Check for INFEASIBLE details
            psv = result.get("pre_solver_validation", {})
            issues = psv.get("issues", [])
            return "INFEASIBLE", f"{msg}; issues={issues[:3]}", elapsed

    except Exception as e:
        return "ERROR", str(e)[:200], 0.0
    finally:
        db.rollback()
        db.close()


def main():
    block_number = 12
    academic_year = 2025
    block_dates = get_block_dates(block_number, academic_year)

    print("=" * 70)
    print(f"CONSTRAINT STRESS TEST — Block {block_number} AY {academic_year}")
    print(f"Date range: {block_dates.start_date} to {block_dates.end_date}")
    print(f"Testing {len(CONSTRAINTS_TO_TEST)} disabled constraints one at a time")
    print("=" * 70)
    print()

    results = []
    for i, name in enumerate(CONSTRAINTS_TO_TEST, 1):
        print(f"[{i}/{len(CONSTRAINTS_TO_TEST)}] Testing: {name} ...", end=" ", flush=True)
        status, detail, elapsed = test_constraint(name, block_number, academic_year)

        marker = {"OPTIMAL": "✓", "INFEASIBLE": "✗", "ERROR": "!", "SKIP": "—"}
        print(f"{marker.get(status, '?')} {status} ({elapsed:.1f}s) — {detail}")
        results.append((name, status, detail, elapsed))

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    optimal = [r for r in results if r[1] == "OPTIMAL"]
    infeasible = [r for r in results if r[1] == "INFEASIBLE"]
    errors = [r for r in results if r[1] == "ERROR"]

    print(f"\n  OPTIMAL:    {len(optimal)}/{len(results)}")
    for name, _, detail, t in optimal:
        print(f"    ✓ {name} ({t:.1f}s) — {detail}")

    if infeasible:
        print(f"\n  INFEASIBLE: {len(infeasible)}/{len(results)}")
        for name, _, detail, t in infeasible:
            print(f"    ✗ {name} ({t:.1f}s) — {detail}")

    if errors:
        print(f"\n  ERROR:      {len(errors)}/{len(results)}")
        for name, _, detail, t in errors:
            print(f"    ! {name} — {detail}")

    # Safe to enable list
    if optimal:
        print(f"\n  SAFE TO ENABLE (individually tested):")
        for name, _, _, _ in optimal:
            print(f"    - {name}")

    print()


if __name__ == "__main__":
    main()
