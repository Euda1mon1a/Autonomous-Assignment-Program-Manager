"""Binary search: isolate which hard constraint causes INFEASIBLE.

Enables each hard constraint one at a time (all others disabled)
and runs the solver. When it fails, you've found the culprit.

Usage:
    cd backend && python ../scripts/debug/isolate_infeasible_constraint.py

Origin: Gemini CLI debugging session (Feb 27, 2026).
Found 1in7Rule as blocker for Block 12 preloaded data.
"""

import os
import sys

os.environ["DEBUG"] = "true"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

from datetime import date

from app.db.session import SessionLocal
from app.scheduling.engine import SchedulingEngine

# --- Configure these for your block ---
BLOCK_NUMBER = 12
ACADEMIC_YEAR = 2025
START_DATE = date(2026, 5, 7)
END_DATE = date(2026, 6, 3)
# ---------------------------------------

HARD_CONSTRAINTS = [
    "1in7Rule",
    "80HourRule",
    "AdjunctCallExclusion",
    "Availability",
    "CallAvailability",
    "ClinicCapacity",
    "FacultyDayAvailability",
    "FacultyPrimaryDutyClinic",
    "FacultyRoleClinic",
    "NightFloatPostCall",
    "OvernightCallCoverage",
    "PostFMITRecovery",
    "ResidentInpatientHeadcount",
    "SupervisionRatio",
    "WeekendWork",
]

db = SessionLocal()
print(f"Testing {len(HARD_CONSTRAINTS)} hard constraints one at a time...\n")

for current_hard in HARD_CONSTRAINTS:
    engine = SchedulingEngine(db, start_date=START_DATE, end_date=END_DATE)

    # Disable all EXCEPT the current one being tested
    for c in HARD_CONSTRAINTS:
        if c != current_hard:
            engine.constraint_manager.disable(c)

    res = engine.generate(
        block_number=BLOCK_NUMBER, academic_year=ACADEMIC_YEAR, algorithm="cp_sat"
    )
    status = res.get("status")
    if status == "failed":
        print(f"\n!!! INFEASIBLE CAUSE: {current_hard} !!!")
        break
    else:
        print(f"  OK: {current_hard}")

db.close()
