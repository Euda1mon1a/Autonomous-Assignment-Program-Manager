# Block Regeneration Runbook (CP-SAT)

This runbook regenerates a single academic block using the canonical CP-SAT pipeline.
It assumes you have a valid local DB and have already taken a backup.

## Prerequisites

- Python 3.11+ environment for the backend.
- Ops scripts load `.env` and backfill `DATABASE_URL` if missing/empty.
- Local backup created (required before destructive clears).

**Note:** If your shell has a stale `CORS_ORIGINS` value (e.g., from `source .env`),
set it to a valid JSON string before running scripts:
`export CORS_ORIGINS='[\"*\"]'`.

## Pre-flight Checks (Recommended)

Use these before a regen to avoid silent failures:

```
# Ensure DB schema is current (rotation_type rename)
cd backend
python3.11 -m alembic upgrade head

# Confirm required rotation templates exist (PCAT/DO/SM)
PYTHONPATH=backend python3.11 - <<'PY'
from app.db.session import SessionLocal
from app.models.rotation_template import RotationTemplate

session = SessionLocal()
try:
    pcat_do = session.query(RotationTemplate).filter(
        RotationTemplate.abbreviation.in_(["PCAT", "DO"])
    ).count()
    sm = session.query(RotationTemplate).filter(
        RotationTemplate.abbreviation == "SM"
    ).count()
finally:
    session.close()

print(f"PCAT/DO templates: {pcat_do}")
print(f"SM templates: {sm}")
PY
```

## Script

Use:

```
python scripts/ops/block_regen.py --block 10 --academic-year 2026 --clear
```

Common flags:

- `--clear` clears `half_day_assignments` and `call_assignments` for the block,
  and removes next-day `pcat`/`do` slots.
- `--timeout 300` sets CP-SAT timeout (seconds).
- `--draft` creates a draft instead of writing live data.
- `--audit-only` prints counts without generating.
- `--skip-pcat-do-validate` skips the post-call integrity check.

## Notes

- The script prints a PII-free summary of counts by source and activity.
- The canonical pipeline uses CP-SAT for call + outpatient activity filling;
  inpatient coverage should be preloaded upstream.

## Post-run Quick Checks (Console Additions)

These help confirm CP-SAT produced real schedule output:

```
PYTHONPATH=backend python3.11 - <<'PY'
from app.db.session import SessionLocal
from app.models.half_day_assignment import HalfDayAssignment
from app.models.call_assignment import CallAssignment
from app.utils.academic_blocks import get_block_dates

block_number = 10
academic_year = 2026
block_dates = get_block_dates(block_number, academic_year)

session = SessionLocal()
try:
    hda = session.query(HalfDayAssignment).filter(
        HalfDayAssignment.date >= block_dates.start_date,
        HalfDayAssignment.date <= block_dates.end_date,
    ).count()
    calls = session.query(CallAssignment).filter(
        CallAssignment.date >= block_dates.start_date,
        CallAssignment.date <= block_dates.end_date,
    ).count()
finally:
    session.close()

print(f"Half-day assignments: {hda}")
print(f"Call assignments: {calls}")
PY
```

If CP-SAT returns **INFEASIBLE**, capture:
- Preload count vs solver count (should not be preload-only).
- Presence of PCAT/DO/SM rotation templates.
- Presence of AT/PCAT/DO activities.
