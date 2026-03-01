#!/usr/bin/env python3
"""Regenerate Block 12 schedule with the Wednesday PM LEC fix applied.

This script:
1. Creates a DB session
2. Instantiates the SchedulingEngine for Block 12 dates
3. Calls engine.generate() with block_number=12, academic_year=2025
4. Reports results

Usage:
    cd backend && SKIP_SETTINGS_VALIDATION=1 .venv/bin/python \
        ../scripts/scheduling/regenerate_block12.py
"""

import os
import sys
import time

# Setup
backend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
sys.path.insert(0, os.path.abspath(backend_dir))
os.environ["SKIP_SETTINGS_VALIDATION"] = "1"

from app.db.session import SessionLocal
from app.scheduling.engine import SchedulingEngine
from app.utils.academic_blocks import get_block_dates


def main():
    block_number = 12
    academic_year = 2025

    block_dates = get_block_dates(block_number, academic_year)
    print(f"Block {block_number} AY {academic_year}: {block_dates.start_date} to {block_dates.end_date}")

    db = SessionLocal()
    try:
        engine = SchedulingEngine(
            db=db,
            start_date=block_dates.start_date,
            end_date=block_dates.end_date,
        )

        print("Starting generation...")
        start = time.time()
        result = engine.generate(
            block_number=block_number,
            academic_year=academic_year,
            algorithm="cp_sat",
            timeout_seconds=120.0,
            check_resilience=False,
            validate_pcat_do=True,
        )
        elapsed = time.time() - start

        print(f"\n{'=' * 60}")
        print(f"RESULT: {result.get('status', 'unknown')}")
        print(f"Time: {elapsed:.1f}s")
        print(f"Assignments: {result.get('total_assigned', 0)}")
        print(f"Message: {result.get('message', 'none')}")

        if result.get("status") == "success":
            db.commit()
            print("Changes committed.")
        else:
            db.rollback()
            print("Rolled back (generation failed).")
            if result.get("pre_solver_validation"):
                psv = result["pre_solver_validation"]
                print(f"  Issues: {psv.get('issues', [])}")
                print(f"  Recommendations: {psv.get('recommendations', [])}")
            if result.get("pcat_do_issues"):
                print(f"  PCAT/DO issues: {result['pcat_do_issues']}")

        print(f"{'=' * 60}")
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
