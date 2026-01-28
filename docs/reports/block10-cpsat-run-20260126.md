# Block 10 CP-SAT Regen + Export Report (2026-01-26)

## Summary
- **CP-SAT generation succeeded** for Block 10 (AY2026) with 617 solver assignments + 20 call nights.
- **Activity solver failed** under the **soft 6 / hard 8** physical capacity model because minimum clinic demand is 15-16 in most slots (35/40), even after restricting capacity to C-variants/PROC/SM/VAS and excluding CV.
- **Supervision demand uses activity flags** (`requires_supervision` / `provides_supervision`) instead of narrow code lists.
- **XLSX / JSON exports not re-run** after the hard-capacity change (activity solver failure leaves activities unassigned).

Block window: **2027-03-11 → 2027-04-07** (Block 10, AY2026).

## Changes Applied (latest run)
- **Engine now filters residents by BlockAssignment** when block/year provided.
- **Block 0 handling** fixed by checking `block_number is not None` instead of truthy checks.
- **Post-call template lookup** now accepts PCAT/DO prefixes (PCAT-AM / DO-PM).
- **Activity solver** computes supervision demand/coverage from activity flags.
- **Physical capacity model** updated to **soft 6 / hard 8** and now fails fast if minimum clinic demand exceeds hard limit.
- **Capacity codes now explicit:** C + variants (excludes CV), V1-3, PROC/PR/PROCEDURE, SM (faculty only), VAS.
- **Supervision required additions:** PROC/VAS now always require AT coverage.
- **Ops scripts** load `.env` before imports and backfill `DATABASE_URL` when empty.
- **New audit script:** `scripts/ops/supervision_activity_audit.py`

## Environment + Preconditions
- Python: `python3.11`
- Database: `residency-scheduler-db` (Docker)
- Required migration: `20260126_rename_rotation_type`
- Ops scripts now auto-load `.env` before backend imports and backfill `DATABASE_URL` when empty.

## Commands Run (Latest Successful Run)

### 1) Regen (clear + CP-SAT)
```
python3.11 scripts/ops/block_regen.py --block 10 --academic-year 2026 --clear
```

### 2) Canonical XLSX export (not re-run after capacity change)
```
python3.11 scripts/ops/block_export.py --block 10 --academic-year 2026 --output /tmp/block10_export.xlsx
```

### 3) Canonical JSON metrics (not re-run after capacity change)
```
PYTHONPATH=backend python3.11 - <<'PY'
from app.db.session import SessionLocal
from app.services.half_day_json_exporter import HalfDayJSONExporter
from app.utils.academic_blocks import get_block_dates

block_number = 10
academic_year = 2026
block_dates = get_block_dates(block_number, academic_year)

session = SessionLocal()
try:
    exporter = HalfDayJSONExporter(session)
    data = exporter.export(
        block_dates.start_date,
        block_dates.end_date,
        include_faculty=True,
        include_call=True,
    )
finally:
    session.close()

residents = data.get("residents", [])
faculty = data.get("faculty", [])
call_nights = data.get("call", {}).get("nights", [])

filled_slots = 0
empty_slots = 0
for person in residents + faculty:
    for day in person.get("days", []):
        for key in ("am", "pm"):
            if day.get(key):
                filled_slots += 1
            else:
                empty_slots += 1

print(f"JSON residents: {len(residents)}")
print(f"JSON faculty: {len(faculty)}")
print(f"JSON call nights: {len(call_nights)}")
print(f"JSON filled slots: {filled_slots}")
print(f"JSON empty slots: {empty_slots}")
PY
```

## Console Results (Key Lines)

### Regen + Activity Solver
```
... Loaded 202 preload assignments
... CP-SAT solver generated 617 rotation assignments and 20 call assignments
... Synced 40 PCAT/DO slots to match new call assignments
... Supervision activity sets: required=48, providers=4 (fallback_required=False, fallback_providers=False)
... Physical capacity infeasible: 35 of 40 slots have minimum clinic demand above hard 8
... Activity solver failed: Physical capacity infeasible (min clinic demand exceeds hard 8)
STATUS: partial
MESSAGE: Generated 617 assignments using cp_sat
SUMMARY COUNTS:
  call_assignments: 20
  half_day_assignments: 1112
  hda_activity_do: 19
  hda_activity_pcat: 19
  hda_source_preload: 240
  hda_source_solver: 872
  pcat_do_next_day: 2
```

### JSON Metrics
Not re-run for this pass (activity solver failure leaves activities unassigned).

### XLSX Export
Not re-run for this pass (would export partial schedule).

## Findings
- **CP-SAT + call** succeeds for Block 10 (solver + call assignments created).
- **Activity solver fails** because minimum clinic demand is **15-16** per slot for most weekdays, which exceeds the **hard 8** capacity.
- Even with **capacity limited to C/PROC/SM/VAS (CV excluded)**, the **allowed activity sets per outpatient template are still all capacity-coded**, so every outpatient slot contributes to the minimum.
- **SM capacity is faculty-only** to avoid double counting resident + faculty in the same room.
- **Supervision constraint** at block solver still logs: `No faculty_at or faculty_pcat variables, supervision constraint not applied` (activity solver now enforces AT coverage).
- **Night Float post-call constraint** still logs: `NF or PC templates not found` (inactive).

## Plan (Next Steps)
1) **Make physical capacity feasible**
   - Decide if PROC/VAS should count for **residents**, or only for **faculty** (similar to SM).
   - Add at least one **non-capacity** activity option to outpatient rotations (e.g., admin/reading) if clinic demand must be reduced.
   - Update activity requirements so outpatient templates have at least one non-capacity alternative.
2) **Validate supervision metadata**
   - Use `scripts/ops/supervision_activity_audit.py` and fix missing `requires_supervision` flags.
3) **Confirm NF/PC templates**
   - Ensure night-float + post-call templates exist where required.

## Priority List (Block 10 Stabilization)
- **P0:** Physical capacity infeasible (min clinic demand 15-16 > hard 8).
- **P1:** Supervision coverage depends on activity flags; validate clinical activity metadata.
- **P2:** NF/PC templates absent (post-call constraint inactive).

## Console Additions (Recommended)
Add these standard post-run checks:
- Count residents included by BlockAssignment for the block.
- Report how many capacity constraints are infeasible (min clinic demand > hard cap).
- Surface missing AT/PCAT/NF/PC templates explicitly.
- JSON metrics: filled vs empty slots.

Suggested quick checks:
```
PYTHONPATH=backend python3.11 - <<'PY'
from app.db.session import SessionLocal
from app.models.block_assignment import BlockAssignment
from sqlalchemy import func

session = SessionLocal()
try:
    rows = session.query(BlockAssignment.block_number, func.count()) \
        .filter(BlockAssignment.academic_year == 2026) \
        .group_by(BlockAssignment.block_number).all()
finally:
    session.close()

print(rows)
PY
```
