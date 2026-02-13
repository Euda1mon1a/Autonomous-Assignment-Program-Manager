"""Generate a block schedule from scratch using the scheduling pipeline.

Runs the full pipeline: preload sync → activity solver → faculty expansion.
Use after block_assignments and rotation_templates are populated.

Usage:
  1. Copy to /tmp/generate_blockNN.py
  2. Fill in BLOCK_CONFIG
  3. Run: backend/.venv/bin/python /tmp/generate_blockNN.py

Prerequisite:
  - Database backup
  - block_assignments table populated (solver or manual entry)
  - rotation_templates configured for the block

Reference implementation: scripts/data/block11_import/ (local only, gitignored)
"""

import os
import sys

# ── Bootstrap ────────────────────────────────────────────────────────────────
# Adjust path to your backend directory
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
os.chdir(BACKEND_DIR)
sys.path.insert(0, ".")

from dotenv import dotenv_values

for env_file in ["../.env", ".env"]:
    if os.path.exists(env_file):
        for key, value in dotenv_values(env_file).items():
            if value is not None:
                os.environ[key] = value

from datetime import date

from app.db.session import SessionLocal
from app.services.faculty_assignment_expansion_service import (
    FacultyAssignmentExpansionService,
)
from app.services.sync_preload_service import SyncPreloadService

# ── Configuration ────────────────────────────────────────────────────────────

BLOCK_CONFIG = {
    "block_number": 0,  # e.g., 12
    "academic_year": 2025,  # AY start year
    "start_date": date(2026, 1, 1),  # First day of block
    "end_date": date(2026, 1, 28),  # Last day of block
}

# Set True to run each stage
RUN_PRELOAD_SYNC = True
RUN_ACTIVITY_SOLVER = True
RUN_FACULTY_EXPANSION = True


# ── Pipeline ─────────────────────────────────────────────────────────────────


def main():
    block_num = BLOCK_CONFIG["block_number"]
    ay = BLOCK_CONFIG["academic_year"]

    if block_num == 0:
        print("ERROR: Set block_number in BLOCK_CONFIG before running.")
        return

    db = SessionLocal()

    try:
        # Stage 1: Preload sync (FMIT, call, absences → HDAs)
        if RUN_PRELOAD_SYNC:
            print(f"[1/3] Running preload sync for Block {block_num} AY {ay}...")
            preload_svc = SyncPreloadService(db)
            preload_count = preload_svc.sync_block(block_num, ay)
            db.commit()
            print(f"  Synced {preload_count} preload HDAs")
        else:
            print("[1/3] Skipping preload sync")

        # Stage 2: Activity solver (generate outpatient schedule)
        if RUN_ACTIVITY_SOLVER:
            print(f"[2/3] Running activity solver for Block {block_num} AY {ay}...")
            from app.scheduling.engine import SchedulingEngine

            engine = SchedulingEngine(db)
            result = engine.generate_schedule(
                block_number=block_num,
                academic_year=ay,
                create_draft=True,
            )
            db.commit()
            print(f"  Solver result: {result}")
        else:
            print("[2/3] Skipping activity solver")

        # Stage 3: Faculty expansion (fill remaining faculty slots)
        if RUN_FACULTY_EXPANSION:
            print(f"[3/3] Running faculty expansion for Block {block_num} AY {ay}...")
            faculty_svc = FacultyAssignmentExpansionService(db)
            created = faculty_svc.fill_faculty_assignments(block_num, ay)
            db.commit()
            print(f"  Created {created} faculty HDAs")
        else:
            print("[3/3] Skipping faculty expansion")

        print("Done.")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
