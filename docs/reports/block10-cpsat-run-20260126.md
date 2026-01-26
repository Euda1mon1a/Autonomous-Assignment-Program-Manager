# Block 10 CP-SAT Regen + Export Report (2026-01-26)

## Summary
- **CP-SAT generation failed** for Block 10 (AY2026) with solver status **INFEASIBLE**.
- Only preloads remained after the run (no solver-generated half-day or call assignments).
- **XLSX export succeeded** but contained **preloads only**.
- **CSV export would be empty** because the `assignments` table had 0 rows in the block date range.

Block window: **2027-03-11 → 2027-04-07** (Block 10, AY2026).

## Environment + Preconditions
- Python: `python3.11`
- Database: `residency-scheduler-db` (Docker)
- Required migration: `20260126_rename_rotation_type`
- Required env: `DATABASE_URL` and `CORS_ORIGINS` (JSON string)

## Commands Run

### 1) Audit-only summary (pre-existing state)
```
DB_PASSWORD=$(docker inspect -f "{{range .Config.Env}}{{println .}}{{end}}" residency-scheduler-db | sed -n "s/^POSTGRES_PASSWORD=//p" | head -n1)
export DATABASE_URL="postgresql://scheduler:${DB_PASSWORD}@localhost:5432/residency_scheduler"
export CORS_ORIGINS='["*"]'
python3.11 scripts/ops/block_regen.py --block 10 --academic-year 2026 --audit-only
```

### 2) Migration applied
```
DB_PASSWORD=$(docker inspect -f "{{range .Config.Env}}{{println .}}{{end}}" residency-scheduler-db | sed -n "s/^POSTGRES_PASSWORD=//p" | head -n1)
export DATABASE_URL="postgresql://scheduler:${DB_PASSWORD}@localhost:5432/residency_scheduler"
cd backend
python3.11 -m alembic upgrade head
```

### 3) Full regen attempt
```
DB_PASSWORD=$(docker inspect -f "{{range .Config.Env}}{{println .}}{{end}}" residency-scheduler-db | sed -n "s/^POSTGRES_PASSWORD=//p" | head -n1)
export DATABASE_URL="postgresql://scheduler:${DB_PASSWORD}@localhost:5432/residency_scheduler"
export CORS_ORIGINS='["*"]'
python3.11 scripts/ops/block_regen.py --block 10 --academic-year 2026 --timeout 300
```

### 4) Canonical XLSX export
```
DB_PASSWORD=$(docker inspect -f "{{range .Config.Env}}{{println .}}{{end}}" residency-scheduler-db | sed -n "s/^POSTGRES_PASSWORD=//p" | head -n1)
export DATABASE_URL="postgresql://scheduler:${DB_PASSWORD}@localhost:5432/residency_scheduler"
export CORS_ORIGINS='["*"]'
python3.11 scripts/ops/block_export.py --block 10 --academic-year 2026 --output /tmp/block10_export.xlsx
```

### 5) Canonical JSON metrics
```
DB_PASSWORD=$(docker inspect -f "{{range .Config.Env}}{{println .}}{{end}}" residency-scheduler-db | sed -n "s/^POSTGRES_PASSWORD=//p" | head -n1)
export DATABASE_URL="postgresql://scheduler:${DB_PASSWORD}@localhost:5432/residency_scheduler"
export CORS_ORIGINS='["*"]'
PYTHONPATH=backend python3.11 - <<"PY"
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

### Audit-only (before regen)
```
SUMMARY COUNTS:
  call_assignments: 16
  half_day_assignments: 1512
  hda_activity_at: 96
  hda_activity_do: 15
  hda_activity_pcat: 15
  hda_source_preload: 468
  hda_source_solver: 1044
  pcat_do_next_day: 4
```

### Regen attempt (after migration)
```
... Loaded 202 preload assignments
... Running CP-SAT solver for outpatient assignments + call
No faculty_at or faculty_pcat variables, supervision constraint not applied
NF or PC templates not found - Night Float post-call constraint inactive
PCAT or DO templates not found - post-call constraint inactive
CP-SAT solver status: INFEASIBLE
STATUS: failed
MESSAGE: CP-SAT solver failed: INFEASIBLE
TOTAL_ASSIGNED: 0
SUMMARY COUNTS:
  call_assignments: 0
  half_day_assignments: 202
  hda_source_preload: 202
  pcat_do_next_day: 0
```

### Canonical JSON metrics
```
JSON residents: 17
JSON faculty: 0
JSON call nights: 0
JSON filled slots: 202
JSON empty slots: 750
```

### XLSX export
```
Saved xlsx to /tmp/block10_export.xlsx
```

## Findings
- **CP-SAT infeasible** for the block (no solver assignments created).
- **Only preloads** remain; solver did not fill outpatient half-days or calls.
- **No `assignments` rows** for the block range, so CSV export is empty.
- **Canonical export succeeds** but renders only preloads.
- Missing templates in DB:
  - **PCAT/DO rotation templates: 0**
  - **SM templates (abbrev SM): 0**

## Plan (Next Steps)
1) **Restore missing rotation templates** (PCAT, DO, SM) in DB.
2) **Ensure faculty inpatient assignments exist** (solver uses assignments for faculty context).
3) **Re-run CP-SAT** with `--clear` and verify solver status != INFEASIBLE.
4) **Verify call/PCAT/DO sync** produces next-day preload slots.
5) **Re-export canonical JSON + XLSX** and verify row mappings.

## Priority List (Block 10 Recovery)
- **P0:** Restore missing templates (PCAT/DO/SM) and re-run CP-SAT.
- **P1:** Ensure faculty assignment context exists for the block (needed for call + supervision).
- **P2:** Validate AT coverage math against actual resident clinic demand.
- **P3:** Re-run export and validate row mappings + call rows in XLSX.

## Console Additions (Recommended)
These diagnostics should be printed or run as standard post-run checks:
- Block assignments count by rotation_type (outpatient/inpatient/etc).
- Presence of required templates: PCAT/DO/SM.
- Presence of AT/PCAT/DO activities.
- Assignments row count for the block date range.
- JSON metrics: filled vs empty slots.

Suggested quick checks:
```
# Templates present?
PYTHONPATH=backend python3.11 - <<"PY"
from app.db.session import SessionLocal
from app.models.rotation_template import RotationTemplate
from sqlalchemy import func

session = SessionLocal()
try:
    rows = session.query(RotationTemplate.rotation_type, func.count()).group_by(RotationTemplate.rotation_type).all()
finally:
    session.close()

print(rows)
PY
```
