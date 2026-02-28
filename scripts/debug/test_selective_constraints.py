"""Run solver with a custom set of constraints disabled.

Edit DISABLE_LIST to test different combinations.

Usage:
    cd backend && python ../scripts/debug/test_selective_constraints.py

Origin: Gemini CLI debugging session (Feb 27, 2026).
"""

import os
import sys

os.environ["DEBUG"] = "true"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

from datetime import date

from app.db.session import SessionLocal
from app.scheduling.engine import SchedulingEngine

# --- Configure these ---
BLOCK_NUMBER = 12
ACADEMIC_YEAR = 2025
START_DATE = date(2026, 5, 7)
END_DATE = date(2026, 6, 3)

DISABLE_LIST = [
    "FacultySupervision",
    "SupervisionRatio",
    "ClinicCapacity",
    "FacultyPrimaryDutyClinic",
]
# -----------------------

db = SessionLocal()
engine = SchedulingEngine(db, start_date=START_DATE, end_date=END_DATE)

for name in DISABLE_LIST:
    engine.constraint_manager.disable(name)

disabled = [c.name for c in engine.constraint_manager.constraints if not c.enabled]
enabled = [c.name for c in engine.constraint_manager.constraints if c.enabled]
print(f"Disabled ({len(disabled)}): {disabled}")
print(f"Enabled  ({len(enabled)}): {enabled}\n")

res = engine.generate(
    block_number=BLOCK_NUMBER, academic_year=ACADEMIC_YEAR, algorithm="cp_sat"
)
print(f"\nSolver result: {res.get('status')}")
db.close()
