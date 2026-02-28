# Block 12 Fresh Solve + Annual Workbook Export Roadmap

**Created:** 2026-02-27
**Academic Year:** 2025 (blocks run Jul 2025 – Jun 2026)
**Block 12 Dates:** May 7 – Jun 3, 2026
**Approach:** Fresh solve Block 12, then export full AY 2025 as 14-sheet workbook with baseline tracking

---

## Recent Changes Context (Feb 25-27, 2026)

These PRs landed in the last 48 hours and directly affect the solve/export pipeline. **Read these first if debugging.**

### PR #1207 — CP-SAT Solver Optimizations (Feb 27)

**File:** `backend/app/scheduling/solvers.py`

| Change | Detail |
|--------|--------|
| `num_workers: 0` (was 4) | Auto-detects all CPU cores instead of hardcoded 4 |
| Solution hinting (warm start) | Hints existing locked assignments to 1, greedy-fills remaining. Gives solver a feasible starting bound → faster pruning |
| `symmetry_level = 0` | Disables symmetry detection — residents are heterogeneous, few symmetries exist. Saves O(n^2) presolve |
| `linearization_level = 1` | Minimal linearization — constraints are already linear or use AddAbsEquality |
| `log_search_progress = True` | Solver logs visible during run |
| Faculty availability check in variable creation | Skips creating variables for unavailable faculty blocks — smaller model |
| O(1) reverse lookups | `block_by_idx` and `faculty_id_by_call_idx` dicts replace O(N*B) inner loops in PCAT/DO linking |

**Impact on Block 12:** Faster solve, same correctness. Warm start especially helpful since preloaded slots (absences, FMIT, NF) are hinted as locked.

### PR #1199 — MAD Call Equity + Prior Calls Hydration (Feb 26)

**File:** `backend/app/scheduling/engine.py`, `constraints/call_equity.py`

- `_build_context()` now hydrates `prior_calls` via GROUP BY with CASE expression
- MAD (Mean Absolute Deviation) replaces Min-Max for weekday/sunday equity pools
- `_sync_academic_year_call_counts()` — idempotent post-solve write-back

### PR #1202 — FMIT Weekend Split (Feb 26)

**File:** `backend/app/scheduling/engine.py`

- FMIT Saturday calls (`overnight + is_weekend=True`) → mapped to `sunday` equity pool
- Prevents FMIT-covering faculty from having inflated weekday call counts

### PR #1197 — SQL Injection Fix (Feb 26)

**File:** `backend/app/db/sql_identifiers.py`

- `validate_identifier()` and `validate_search_path()` for all dynamic SQL
- Not directly relevant to solve but important for any raw SQL queries

### PR #1198 — 27,598 Lines Dead Code Removed (Feb 26)

- Removed: CQRS, event sourcing, SAML, OAuth2 PKCE, sharding, partitioning, outbox, key management
- If engine imports fail with `ModuleNotFoundError`, check if the import was for deleted code

### PR #1206 — Next.js 15 Upgrade + Doc Sweep (Feb 27)

- Frontend upgrade — not relevant to backend solve
- 19 stale docs cleaned up

### Key Architecture References (Updated)

| Document | What It Covers |
|----------|----------------|
| `docs/architecture/ENGINE_ASSIGNMENT_FLOW.md` | Preserve-then-solve flow, 6 loader types, occupied_slots filtering, LangGraph pipeline, prior_calls hydration |
| `docs/architecture/CALL_CONSTRAINTS.md` | Call coverage (Sun-Thu), MAD equity formulation, FMIT weekend split, variable structure |
| `docs/architecture/FACULTY_FIX_ROADMAP.md` | Phase 1 complete (MAD, prior_calls, FMIT split). Phase 2-3 pending. |

---

## Pipeline Reference (Corrected)

### Engine Entry Point

```python
from app.scheduling.engine import SchedulingEngine
engine = SchedulingEngine(db)
result = engine.generate(block_number=12, academic_year=2025, algorithm="cp_sat")
```

**Method:** `SchedulingEngine.generate()` at `engine.py:146`
**Key params:** `block_number`, `academic_year`, `algorithm` ("cp_sat" | "greedy" | "pulp" | "hybrid"), `timeout_seconds` (default 60)

### Preload Entry Point

```python
from app.services.sync_preload_service import SyncPreloadService
svc = SyncPreloadService(db)
count = svc.load_all_preloads(block_number=12, academic_year=2025)
```

**Class:** `app.services.sync_preload_service.SyncPreloadService` (NOT in `preload/` subdirectory)
**Key params:** `block_number`, `academic_year`, `skip_faculty_call` (default False — set True if engine will generate new calls)

### Export Pipeline (No XML Needed)

```
DB → HalfDayJSONExporter → JSON dict → JSONToXlsxConverter → xlsx
```

`JSONToXlsxConverter` inherits from `XMLToXlsxConverter` but **structure XML is optional**. When `structure_xml_path=None` (our case — XML doesn't exist), the converter calls `_build_dynamic_mappings()` which allocates rows from JSON data. The template XLSX (`BlockTemplate2_Official.xlsx`) still provides formatting/styling.

**No XML file is needed. The JSON-to-XLSX path is the canonical pipeline.**

### Block Data Coverage (AY 2025)

| Block | HDAs | Status |
|:-----:|-----:|--------|
| 0–8 | 0 | Empty — never solved |
| 9 | 600 | Solved |
| 10 | 1,080 | Solved |
| 11 | 0 | Empty |
| **12** | **0** | **Target of this roadmap** |
| 13 | 0 | Empty |

The annual workbook will have 12 blank sheets. YTD_SUMMARY formulas will only reflect Blocks 9, 10, and 12. This is expected — the coordinator cherry-picks Block 12.

---

## Pre-Flight Checklist

Before starting any step, verify:

```bash
# Database is running
pg_isready -h localhost -p 5432

# Backend venv is active
cd /Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend
source .venv/bin/activate

# MCP server is healthy (optional but recommended)
# curl http://127.0.0.1:8080/mcp/health
```

---

## Step 0: Backup

**MANDATORY. Do this before anything else.**

```python
mcp__residency-scheduler__create_backup_tool(reason="Pre-Block 12 fresh solve + annual workbook export")
```

Or manually:

```bash
pg_dump -h localhost -U scheduler residency_scheduler > ~/backups/pre-block12-solve-$(date +%Y%m%dT%H%M%S).sql
```

**Verify backup exists before proceeding.**

---

## Step 1: Verify Block 12 Starting State

**Purpose:** Confirm what exists and what doesn't before touching anything.

```bash
cd backend && DEBUG=true .venv/bin/python3 -c "
from app.db.session import SessionLocal
from sqlalchemy import text
db = SessionLocal()

print('=== BLOCK 12 PRE-SOLVE STATE ===')

# HDAs (expect 0)
hda = db.execute(text(\"SELECT COUNT(*) FROM half_day_assignments WHERE date >= '2026-05-07' AND date <= '2026-06-03'\")).scalar()
print(f'HDAs: {hda}')

# Block assignments (expect 16 — these are INPUTS, do NOT delete)
ba = db.execute(text(\"SELECT COUNT(*) FROM block_assignments WHERE block_number=12 AND academic_year=2025\")).scalar()
print(f'Block assignments: {ba}')

# Call assignments (expect 23)
ca = db.execute(text(\"SELECT COUNT(*) FROM call_assignments WHERE date >= '2026-05-07' AND date <= '2026-06-03'\")).scalar()
print(f'Call assignments: {ca}')

# Absences (expect 8 — these are SOURCE OF TRUTH, do NOT delete)
ab = db.execute(text(\"SELECT COUNT(*) FROM absences WHERE start_date <= '2026-06-03' AND end_date >= '2026-05-07'\")).scalar()
print(f'Absences: {ab}')

db.close()
"
```

### Expected State

| Table | Expected Count | Action |
|-------|---------------|--------|
| `half_day_assignments` | 0 | Ready for solve — nothing to clear |
| `block_assignments` | 16 | **PRESERVE** — solver input (rotation assignments) |
| `call_assignments` | 23 | Keep or re-solve (see Step 2 decision) |
| `absences` | 8 | **NEVER TOUCH** — coordinator-approved leave |
| `academic_blocks` | 1 (Block 12) | **NEVER TOUCH** — block definition |

### If HDAs are NOT zero

Something wrote to them since the audit. Clear only Block 12 HDAs:

```sql
DELETE FROM half_day_assignments
WHERE date >= '2026-05-07' AND date <= '2026-06-03';
```

---

## Step 2: Decision — Call Assignments

**23 call assignments already exist for Block 12.**

| Option | Pros | Cons |
|--------|------|------|
| **Keep existing calls** | Less disruption, already scheduled | May not match new solver output |
| **Clear and re-solve calls** | Consistent with fresh solve, MAD equity applies | Loses any manual call tweaks |

**If keeping calls:** Skip call clearing. The solver should respect existing call assignments as constraints.

**If re-solving calls:**

```sql
DELETE FROM call_assignments
WHERE date >= '2026-05-07' AND date <= '2026-06-03';
```

---

## Step 3: Load Preloads

**Purpose:** Populate HDAs for absences, FMIT, NF combined splits, and call preloads (PCAT/DO) before the solver runs. These become `source='preload'` and are LOCKED — the solver cannot overwrite them.

```python
# In a Python session with backend context:
from app.db.session import SessionLocal
from app.services.preload.sync_preload_service import SyncPreloadService

db = SessionLocal()
svc = SyncPreloadService(db)
result = svc.load_all_preloads(block_number=12, academic_year=2025)
db.commit()
print(result)
db.close()
```

### What preloads create

| Source | What | Expected HDAs |
|--------|------|---------------|
| Absences (8 records) | LV-AM, LV-PM for each leave day in block | ~80 (varies by overlap days) |
| FMIT preloads | FMIT activity for FMIT-assigned residents | ~96 (3 residents: full + wk 1-2 + NF+FMIT) |
| NF combined half-block | First/second half splits (NF-CARDIO, NF-FMIT-PG, etc.) | ~192 (6 NF combined residents × 2 slots × 16 days each) |
| Call preloads (PCAT/DO) | Post-call attending time, direct observation | ~10-20 |
| Day off / weekend | OFF, W codes | ~180 |

### Verify after preloads

```bash
DEBUG=true .venv/bin/python3 -c "
from app.db.session import SessionLocal
from sqlalchemy import text
db = SessionLocal()
count = db.execute(text(\"SELECT COUNT(*) FROM half_day_assignments WHERE date >= '2026-05-07' AND date <= '2026-06-03'\")).scalar()
by_source = db.execute(text(\"SELECT source, COUNT(*) FROM half_day_assignments WHERE date >= '2026-05-07' AND date <= '2026-06-03' GROUP BY source\")).all()
print(f'Total HDAs after preload: {count}')
for src, cnt in by_source:
    print(f'  {src}: {cnt}')
db.close()
"
```

**Expect:** 400–600 preload HDAs. If significantly less, check rotation code mappings in `backend/app/services/preload/constants.py`.

### If preloads fail or produce wrong data

```sql
-- Roll back preloads only (source='preload'), preserving any manual entries
DELETE FROM half_day_assignments
WHERE date >= '2026-05-07' AND date <= '2026-06-03'
  AND source = 'preload';
```

Then debug `rotation_codes.py` handlers. Key files:
- `backend/app/services/preload/constants.py` — NF_COMBINED_ACTIVITY_MAP, REVERSE_NF_COMBINED_MAP, ROTATION_ALIASES
- `backend/app/services/preload/rotation_codes.py` — resolve_activity_for_date()
- `backend/app/services/preload/sync_preload_service.py` — load_all_preloads()

---

## Step 4: Run Fresh Solve

**Purpose:** Fill remaining HDA slots with solver-generated assignments (`source='solver'`).

The engine reads:
- Block assignments (16 rotation records) → what each resident is supposed to do
- Preloaded HDAs → locked slots the solver must respect
- Rotation templates + weekly patterns → how to expand rotations into daily slots
- Absences → already projected as preloads, solver sees them as occupied

```python
from app.db.session import SessionLocal
from app.scheduling.engine import SchedulingEngine  # verify actual class name

db = SessionLocal()
engine = SchedulingEngine(db)
result = engine.generate_schedule(block_number=12, academic_year=2025)
db.commit()
print(result)
db.close()
```

> **Note:** If the engine class/method name differs, check:
> ```bash
> grep -n "class.*Engine\|def generate" backend/app/scheduling/engine.py | head -20
> ```

### Verify after solve

```bash
DEBUG=true .venv/bin/python3 -c "
from app.db.session import SessionLocal
from sqlalchemy import text
db = SessionLocal()

total = db.execute(text(\"SELECT COUNT(*) FROM half_day_assignments WHERE date >= '2026-05-07' AND date <= '2026-06-03'\")).scalar()
by_source = db.execute(text(\"SELECT source, COUNT(*) FROM half_day_assignments WHERE date >= '2026-05-07' AND date <= '2026-06-03' GROUP BY source ORDER BY source\")).all()
by_person = db.execute(text(\"\"\"
    SELECT p.name, COUNT(*) FROM half_day_assignments h
    JOIN people p ON h.person_id = p.id
    WHERE h.date >= '2026-05-07' AND h.date <= '2026-06-03'
    GROUP BY p.name ORDER BY p.name
\"\"\")).all()
null_activity = db.execute(text(\"SELECT COUNT(*) FROM half_day_assignments WHERE date >= '2026-05-07' AND date <= '2026-06-03' AND activity_id IS NULL\")).scalar()

print(f'Total HDAs: {total}')
print(f'Null activity_id: {null_activity}')
print()
for src, cnt in by_source:
    print(f'  {src}: {cnt}')
print()
print('Per-resident HDA counts (expect ~56 each for 28-day block):')
for name, cnt in by_person:
    flag = ' *** LOW' if cnt < 40 else ''
    print(f'  {name}: {cnt}{flag}')
db.close()
"
```

### Expected outcomes

| Metric | Expected |
|--------|----------|
| Total HDAs | ~900–1,200 (16 residents × 56 slots + faculty) |
| Null activity_id | **0** — any nulls = rotation mapping bug |
| Per-resident count | ~54–56 each |
| Source distribution | ~60% preload, ~40% solver |

### If solve fails

1. Check `logs/app.log` for solver errors
2. Common issues:
   - Infeasible constraint → check if absences conflict with mandatory coverage
   - Timeout → solver time limit may need increase
   - Import error → check `engine.py` imports after PR #1198 dead code removal
3. Roll back solver HDAs only: `DELETE FROM half_day_assignments WHERE date >= '2026-05-07' AND date <= '2026-06-03' AND source = 'solver';`
4. Fix issue and re-run Step 4

---

## Step 5: Validate Schedule

**Purpose:** Verify ACGME compliance and coverage before exporting.

```python
mcp__residency-scheduler__validate_schedule_tool  # MCP tool
```

Or manually check key constraints:

```bash
DEBUG=true .venv/bin/python3 -c "
from app.db.session import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# Check 80-hour rule (rough: 56 slots × 6h = 336h max, 80h/wk × 4wk = 320h limit)
print('=== 80-HOUR RULE CHECK (approximate) ===')
heavy = db.execute(text(\"\"\"
    SELECT p.name, COUNT(*) as slots FROM half_day_assignments h
    JOIN people p ON h.person_id = p.id
    JOIN activities a ON h.activity_id = a.id
    WHERE h.date >= '2026-05-07' AND h.date <= '2026-06-03'
      AND a.category = 'clinical'
    GROUP BY p.name
    HAVING COUNT(*) > 53
    ORDER BY slots DESC
\"\"\")).all()
if heavy:
    for name, cnt in heavy:
        print(f'  WARNING: {name} has {cnt} clinical half-days')
else:
    print('  All residents within limits')

# Check 1-in-7 (every 7-day window must have 1 day off)
print()
print('=== FMIT COVERAGE CHECK ===')
fmit = db.execute(text(\"\"\"
    SELECT h.date, h.time_of_day, p.name FROM half_day_assignments h
    JOIN people p ON h.person_id = p.id
    JOIN activities a ON h.activity_id = a.id
    WHERE h.date >= '2026-05-07' AND h.date <= '2026-06-03'
      AND a.code = 'FMIT'
    ORDER BY h.date, h.time_of_day
\"\"\")).all()
print(f'  FMIT half-day slots: {len(fmit)}')

# Check NF coverage
print()
print('=== NIGHT FLOAT COVERAGE CHECK ===')
nf = db.execute(text(\"\"\"
    SELECT h.date, p.name FROM half_day_assignments h
    JOIN people p ON h.person_id = p.id
    JOIN activities a ON h.activity_id = a.id
    WHERE h.date >= '2026-05-07' AND h.date <= '2026-06-03'
      AND a.code = 'NF'
    ORDER BY h.date
\"\"\")).all()
print(f'  NF slots: {len(nf)}')

db.close()
"
```

### Cross-reference with Block 12 Analysis

Compare solver output against `docs/analysis/BLOCK_12_ANALYSIS.md`:
- 16 residents should match the rotation matrix (Section 2)
- 8 absences should produce leave HDAs (Section 4)
- FMIT coverage: 3 residents (full, wk 1-2, NF+FMIT) (Section 6)
- Night Float: 4 residents (3 full, 1 wk 3-4) (Section 6)
- L&D NF: 1 resident solo (Section 6)
- Peds NF: 2 residents (full, wk 3+) (Section 6)

---

## Step 6: Add `__BASELINE__` Sheet to Export Pipeline

**Purpose:** Fingerprint every cell the system generated so we can detect hand-jams on reimport.

### File: `backend/app/services/excel_metadata.py`

Add `write_baseline_sheet()`:

```python
def write_baseline_sheet(
    wb: Workbook,
    sheet_name: str,
    cell_data: list[dict],  # [{cell_ref, value, row_hash, source}, ...]
) -> None:
    """Write __BASELINE__{N}__ sheet with cell fingerprints for hand-jam detection."""
    baseline_sheet_name = f"__BASELINE_{sheet_name}__"
    if baseline_sheet_name in wb.sheetnames:
        del wb[baseline_sheet_name]
    ws = wb.create_sheet(baseline_sheet_name)
    ws.sheet_state = "veryHidden"

    # Headers
    ws.cell(row=1, column=1, value="cell_ref")
    ws.cell(row=1, column=2, value="value")
    ws.cell(row=1, column=3, value="row_hash")
    ws.cell(row=1, column=4, value="source")

    for i, entry in enumerate(cell_data, start=2):
        ws.cell(row=i, column=1, value=entry["cell_ref"])
        ws.cell(row=i, column=2, value=entry["value"])
        ws.cell(row=i, column=3, value=entry["row_hash"])
        ws.cell(row=i, column=4, value=entry["source"])
```

### File: `backend/app/services/canonical_schedule_export_service.py`

In `export_year_xlsx()`, after copying each block sheet, collect cell data from HDAs and call `write_baseline_sheet()`. The HDA source field (`preload`, `solver`, `manual`) maps directly to the baseline source column.

### Key design decisions

- One `__BASELINE__` sheet per block (e.g., `__BASELINE_Block 12__`) — avoids one giant sheet
- Cell refs use Excel notation (e.g., "F9" = first data cell)
- Row hashes use existing `compute_row_hash()` from `excel_metadata.py`
- `source` comes from `HalfDayAssignment.source` field

---

## Step 7: Add `__OVERRIDES__` Detection to Import Pipeline

**Purpose:** On reimport, compare each cell against its baseline. Differences = hand-jams.

### File: `backend/app/services/excel_metadata.py`

Add `read_baseline()` and `write_overrides_sheet()`:

```python
def read_baseline(wb: Workbook, sheet_name: str) -> dict[str, dict]:
    """Read baseline data for a block sheet. Returns {cell_ref: {value, row_hash, source}}."""
    baseline_sheet_name = f"__BASELINE_{sheet_name}__"
    if baseline_sheet_name not in wb.sheetnames:
        return {}
    ws = wb[baseline_sheet_name]
    result = {}
    row = 2
    while True:
        cell_ref = ws.cell(row=row, column=1).value
        if not cell_ref:
            break
        result[str(cell_ref)] = {
            "value": ws.cell(row=row, column=2).value,
            "row_hash": ws.cell(row=row, column=3).value,
            "source": ws.cell(row=row, column=4).value,
        }
        row += 1
    return result


def write_overrides_sheet(
    wb: Workbook,
    sheet_name: str,
    overrides: list[dict],  # [{cell_ref, original, new_value, person_name, date, time_of_day}, ...]
) -> None:
    """Write __OVERRIDES__{N}__ sheet tracking hand-jammed cells."""
    override_sheet_name = f"__OVERRIDES_{sheet_name}__"
    if override_sheet_name in wb.sheetnames:
        del wb[override_sheet_name]
    ws = wb.create_sheet(override_sheet_name)
    ws.sheet_state = "veryHidden"

    headers = ["cell_ref", "original_value", "new_value", "person_name", "date", "time_of_day"]
    for col, h in enumerate(headers, start=1):
        ws.cell(row=1, column=col, value=h)

    for i, entry in enumerate(overrides, start=2):
        for col, key in enumerate(headers, start=1):
            ws.cell(row=i, column=col, value=entry.get(key))
```

### File: `backend/app/services/half_day_import_service.py`

In `stage_block_sheet()`, after parsing the reimported sheet:

1. Read `__BASELINE_{sheet_name}__` from the workbook
2. For each parsed cell, compare value against baseline
3. Cells that differ → record as override
4. Persist overrides to HDAs with `source='manual'`

### File: `backend/app/tasks/import_tasks.py`

In `process_yearly_workbook()`, after staging each sheet, collect overrides and write `__OVERRIDES__` sheets back into the workbook for audit trail.

---

## Step 8: Export Annual Workbook

**Purpose:** Generate the 14-sheet master workbook for AY 2025.

```python
from app.db.session import SessionLocal
from app.services.canonical_schedule_export_service import CanonicalScheduleExportService

db = SessionLocal()
svc = CanonicalScheduleExportService(db)
xlsx_bytes = svc.export_year_xlsx(
    academic_year=2025,
    include_faculty=True,
    include_overrides=True,
    output_path="/tmp/AY2025_Master_Schedule.xlsx",
)
print(f"Exported {len(xlsx_bytes)} bytes")
db.close()
```

Or via API:

```bash
curl -o AY2025_Master_Schedule.xlsx \
  "http://localhost:8000/api/v1/export/schedule/year/xlsx?academic_year=2025"
```

### Verify the output

Open in Excel and check:

| Check | How |
|-------|-----|
| 14 block sheets exist | Sheet tabs: Block 0 through Block 13 |
| YTD_SUMMARY is first sheet | Should be auto-selected on open |
| Block 12 has data | All 16 residents have rotation codes in all 56 slots |
| Faculty supervision visible | Rows 31+ have faculty names and activity codes |
| `__SYS_META__` exists | VBA: `Sheets("__SYS_META__").Visible = xlSheetVisible` |
| `__BASELINE_Block 12__` exists | VBA: same unhide technique |
| `__REF__` has code lists | Unhide and verify rotation/activity codes |
| Phantom columns grayed | Block 0 and Block 13 should have gray locked columns for non-existent days |
| Absences show as LV | PGY-2 resident (May 29–Jun 3), PGY-2 resident (May 14–18, Jun 2–3), etc. |
| Deployed faculty shows as deployed | Full block deployment activity |

---

## Step 9: Hand-Jam Round-Trip Test

**Purpose:** Verify the baseline/override detection works.

1. Open `AY2025_Master_Schedule.xlsx`
2. Go to Block 12 sheet
3. Change 3 cells (e.g., swap two rotation codes, change one leave to a clinic day)
4. Save as `AY2025_Master_Schedule_EDITED.xlsx`
5. Reimport:

```bash
curl -X POST "http://localhost:8000/api/v1/import/staging/yearly" \
  -F "file=@AY2025_Master_Schedule_EDITED.xlsx" \
  -F "academic_year=2025"
```

6. Verify `__OVERRIDES_Block 12__` sheet captures exactly 3 changes
7. Verify staged assignments show the 3 diffs with correct old/new values

---

## Step 10: Run Tests

```bash
cd backend && DEBUG=true .venv/bin/python3 -m pytest tests/services/test_canonical_schedule_export.py -v
cd backend && DEBUG=true .venv/bin/python3 -m pytest tests/services/test_half_day_import.py -v
cd backend && DEBUG=true .venv/bin/python3 -m pytest tests/services/test_excel_metadata.py -v
```

If test files don't exist yet for baseline/overrides, write them as part of Steps 6–7.

---

## Recovery Procedures

### If solve produces bad data

```sql
-- Delete only solver-generated HDAs for Block 12
DELETE FROM half_day_assignments
WHERE date >= '2026-05-07' AND date <= '2026-06-03'
  AND source = 'solver';
```

Then return to Step 4.

### If preloads are wrong

```sql
-- Delete only preloaded HDAs for Block 12
DELETE FROM half_day_assignments
WHERE date >= '2026-05-07' AND date <= '2026-06-03'
  AND source = 'preload';
```

Then return to Step 3.

### If everything is wrong

```sql
-- Nuclear option: clear ALL Block 12 HDAs
DELETE FROM half_day_assignments
WHERE date >= '2026-05-07' AND date <= '2026-06-03';
```

Then return to Step 3. Block assignments, absences, and call assignments are untouched.

### If database is corrupted

Restore from the backup created in Step 0:

```bash
psql -h localhost -U scheduler residency_scheduler < ~/backups/pre-block12-solve-TIMESTAMP.sql
```

Or use MCP:

```python
mcp__residency-scheduler__restore_backup_tool(backup_id="...")
```

---

## 13 Absences Reference — Block 12 (Do Not Delete)

**Reconciled 2026-02-27** from coordinator's master leave spreadsheet.

### Faculty (8 entries)

| # | Person | Type | Full Range | In-Block Days | Notes |
|---|--------|------|------------|---------------|-------|
| 1 | Faculty-APD | vacation | May 7 – May 18 | 12 days (wk 1-2) | 2-week leave, not on FMIT |
| 2 | Faculty-OIC | vacation | May 21 – May 25 | 5 days | **Corrected** from May 18-21. FMIT starts May 22. |
| 3 | Faculty-Deployed | deployment | Feb 21 – Jun 30 | **28 days (full block)** | Spans entire AY |
| 4 | Faculty-SM | vacation | May 26 – May 29 | 4 days | |
| 5 | Faculty-Core-A | tdy | May 14 | 1 day | BLS certification. Available for call, HDAs blocked. |
| 6 | Faculty-Core-A | tdy | May 21 | 1 day | PALS certification. Available for call, HDAs blocked. |
| 7 | Faculty-Core-A | tdy | May 28 | 1 day | BLS certification. Available for call, HDAs blocked. |
| 8 | Faculty-Core-B | vacation | May 26 – May 29 | 4 days | |

### Residents (5 entries)

| # | Person | Type | Full Range | In-Block Days | Boundary? |
|---|--------|------|------------|---------------|-----------|
| 9 | Resident-PGY2-A | vacation | May 29 – Jun 4 | 6 days (May 29–Jun 3) | Spans into Block 13 |
| 10 | Resident-PGY3-A | vacation | May 27 – Jun 2 | 7 days | No |
| 11 | Resident-PGY2-B | vacation | May 14 – May 18 | 5 days | No |
| 12 | Resident-PGY2-B | vacation | Jun 2 – Jun 7 | 2 days (Jun 2–3) | Spans into Block 13 |
| 13 | Resident-PGY1-A | vacation | May 24 – May 30 | 7 days | No |

### Block 12 Faculty Availability by Week

| Week | Dates | Faculty on Leave/TDY | Available (of 10) |
|------|-------|----------------------|:-:|
| 1 | May 7–11 | Faculty-APD (LV), Faculty-Deployed (DEP) | **8** |
| 2 | May 12–18 | Faculty-APD (LV), Faculty-Core-A (BLS 14th), Faculty-Deployed (DEP) | **7–8** |
| 3 | May 19–25 | Faculty-OIC (LV 21-25), Faculty-Core-A (PALS 21st), Faculty-Deployed (DEP) | **7–8** |
| 4 | May 26–Jun 3 | Faculty-SM (LV), Faculty-Core-B (LV), Faculty-Core-A (BLS 28th), Faculty-Deployed (DEP) | **6–7** |

---

## 16 Block Assignments Reference (Solver Input — Preserve)

| Resident | PGY | Rotation | Secondary | NF Combined? |
|----------|-----|----------|-----------|:------------:|
| R-PGY2-A | 2 | FMC | — | No |
| R-PGY3-B | 3 | FMIT-PGY3 | — | No |
| R-PGY3-C | 3 | PEDS-EM | — | No |
| R-PGY1-D | 1 | NF-FMIT-PG | — | Yes |
| R-PGY3-E | 3 | HILO-PGY3 | — | No (off-site) |
| R-PGY1-F | 1 | MSK-SEL | — | No |
| R-PGY2-G | 2 | NF-CARDIO | — | Yes |
| R-PGY2-H | 2 | NF-LD | — | Yes |
| R-PGY3-I | 3 | JAPAN | — | No (off-site) |
| R-PGY2-J | 2 | ELEC | — | No |
| R-PGY1-K | 1 | NBN | — | No |
| R-PGY1-L | 1 | FMIT-PGY2 | NF | Yes |
| R-PGY1-M | 1 | PEDS-WARD- | NF-PEDS-PG | Yes |
| R-PGY2-N | 2 | D+N | — | Yes (alias for DERM-NF) |
| R-PGY2-O | 2 | ELEC | — | No |
| R-PGY1-P | 1 | NF-PEDS-PG | — | Yes |

---

## Absence Reconciliation Log (2026-02-27)

**Source:** Coordinator's master leave spreadsheet (pasted dump of all PGY-1, PGY-2, PGY-3 leave plus faculty corrections).

### Changes Made (11 total, all committed)

| # | Action | Person | Details |
|---|--------|--------|---------|
| 1 | **UPDATE** | Faculty-OIC | Block 12 leave dates corrected: May 18-21 → **May 21-25** |
| 2 | INSERT | Faculty-Core-B | vacation May 26-29 (Block 12) |
| 3 | INSERT | Faculty-APD | vacation May 7-18 (Block 12, 2 weeks) |
| 4 | INSERT | Faculty-Core-A | tdy May 14 (BLS certification) |
| 5 | INSERT | Faculty-Core-A | tdy May 21 (PALS certification) |
| 6 | INSERT | Faculty-Core-A | tdy May 28 (BLS certification) |
| 7 | INSERT | R-PGY3-B | vacation Apr 9 (Block 11, single day) |
| 8 | INSERT | R-PGY3-B | vacation Apr 18 (Block 11, single day) |
| 9 | INSERT | Resident-Q | vacation Jul 24-Aug 6 (Block 1-2) |
| 10 | INSERT | Resident-Q | vacation Nov 29-Dec 5 (Block 6) |
| 11 | INSERT | Resident-R | vacation Aug 1-5 (Block 2) |

### All Residents Verified Complete

Every resident leave entry from the coordinator's spreadsheet was diffed against the `absences` table. All PGY-1/2/3 leaves matched except the 5 inserts above (R-PGY3-B B11, Resident-Q B1+B6, Resident-R B2).

### Decisions Made

| Question | Answer |
|----------|--------|
| Faculty-APD leave window | May 7-18 (Block 12 wk 1-2). Not on FMIT — faculty don't have rotations. |
| R-PGY3-I "Last week AY 26-27 Block 2" | Out of scope — next academic year. Skipped. |
| Faculty-Core-A BLS/PALS absence_type | `tdy` — `training` not in CHECK constraint. `is_away_from_program=false` (still available for call). |

### CHECK Constraint for `absence_type`

Valid values: `vacation`, `deployment`, `tdy`, `medical`, `family_emergency`, `conference`, `bereavement`, `emergency_leave`, `sick`, `convalescent`, `maternity_paternity`.

If `training` is needed as a distinct type in the future, requires Alembic migration to ALTER the CHECK constraint.

---

## What We Are NOT Doing

- Not building Celery batch pipeline (manual single-export workflow)
- Not adding Data Validation dropdowns (Phase 3 of stateful round-trip roadmap)
- Not adding conditional formatting
- Not implementing cross-block leave continuity (longitudinal validator 4c)
- Not implementing 1-in-7 boundary checking (longitudinal validator 4d)
- Not preserving old Block 12 stale data (was already 0 HDAs)
- Not modifying block assignments or absences (except the 11 reconciliation changes above)

---

## Files to Modify

| File | Change | Step |
|------|--------|------|
| `backend/app/services/excel_metadata.py` | Add `write_baseline_sheet()`, `read_baseline()`, `write_overrides_sheet()` | 6, 7 |
| `backend/app/services/canonical_schedule_export_service.py` | Call `write_baseline_sheet()` in `export_year_xlsx()` loop | 6 |
| `backend/app/services/half_day_import_service.py` | Add baseline diff in `stage_block_sheet()` | 7 |
| `backend/app/tasks/import_tasks.py` | Write `__OVERRIDES__` sheets after staging | 7 |

## Files to Read (Context)

| File | Why |
|------|-----|
| `backend/app/services/preload/rotation_codes.py` | Activity code resolution for NF combined |
| `backend/app/services/preload/constants.py` | NF_COMBINED_ACTIVITY_MAP, ROTATION_ALIASES |
| `backend/app/models/half_day_assignment.py` | HDA model, source field enum |
| `backend/app/services/half_day_json_exporter.py` | What the export queries from HDAs |
| `docs/analysis/BLOCK_12_ANALYSIS.md` | Roster, rotation matrix, coverage expectations |
| `docs/architecture/excel-stateful-roundtrip-roadmap.md` | Phase 1–4 architecture context |

---

## Step 11: Post-Solve Refinements (Feb 27, 2026)

After the initial Block 12 solve + export (commit `e937e7fa`), a visual review of the workbook identified several issues. This section documents the fixes applied.

### 11a: Faculty Classification + Alembic Migration

**Migration:** `20260227_add_adjunct_role.py` (revision `20260227_add_adjunct`)

| Change | Detail |
|--------|--------|
| CHECK constraint updated | Added `'adjunct'` to `ck_people_check_faculty_role` |
| 3 faculty → adjunct | 3 non-physician faculty (Clinical Psych ×2, Clinical Pharmacist — new INSERT) |
| 4 faculty → core (backfill) | 4 core faculty with NULL role (were NULL) |
| 1 faculty → NULL | Left as NULL, filtered at export time |

### 11b: Faculty Filtering at Export

**File:** `canonical_schedule_export_service.py` → `_export_json_data()`

- 13 placeholder faculty (`Dr. Faculty-A` through `Dr. Faculty-M`) removed at export
- 1 NULL-role faculty removed at export
- Adjunct faculty (3 non-physician) **kept** for manual input
- Result: 17 faculty in workbook (14 core + 3 adjunct)

### 11c: Faculty Grouping (Core First, Adjunct Below)

**Files:** `half_day_xml_exporter.py`, `half_day_json_exporter.py`, `xml_to_xlsx_converter.py`

- Added `faculty_role` to `_fetch_people()` output
- Two-tier sort in `_build_dynamic_mappings()`: core alphabetical first, adjunct alphabetical below

### 11d: Zero Black Cells (Gap Fill)

**File:** `half_day_json_exporter.py` → `_build_person()`

- Empty AM/PM cells for non-adjunct people filled:
  - Saturday/Sunday → `"W"` (weekend)
  - Weekday → `"OFF"` (ACGME-conservative)
- Adjunct faculty left blank for coordinator manual input

### 11e: Rotation Preload Gap Fixes

**9 residents had partial HDAs due to missing rotation handlers.**

**File:** `constants.py`
- New aliases: `NF-PEDS-PG→PEDNF`, `NF-PEDS-PGY→PEDNF`, `NF-LD→LDNF`
- Prefix matching in `canonical_rotation_code()`: `FMIT-PGY*→FMIT`, `PEDS-WARD-*→PEDW`, `NF-PEDS-*→PEDNF`

**File:** `rotation_codes.py` → `get_rotation_preload_codes()`
- **Wednesday fix:** NF combined rotations now return `("OFF","LEC")` instead of `(None,None)` — closes 6-slot gap for 3 NF-combined residents
- **FMIT handler:** weekdays `("FMIT","FMIT")`, weekends `("W","W")` — fixes FMIT residents (17→56, partial)
- **NBN handler:** weekdays `("NBN","NBN")`, weekends `("W","W")` — fixes NBN resident (24→56)
- **PEDW handler:** weekdays `("PEDW","PEDW")`, Saturday `("W","W")` — fixes PEDW resident partial

### 11f: AI Assistant Prompts

- `docs/prompts/CLAUDE_FOR_EXCEL_PROMPT.md` — Opus 4.6 Excel add-in prompt
- `docs/prompts/GEMINI_SCHEDULE_ANALYSIS_PROMPT.md` — Gemini 3.1 Pro extended thinking prompt

### 11g: Post-Audit Fixes (Plan: nested-gliding-feather)

6 issues identified by Claude for Excel audit of Block 12 sheet:

| Fix | Severity | Description | Status |
|-----|----------|-------------|--------|
| 1 | HIGH | Black-on-black LEC cells — moved LEC/ADV/DFM to white font group in `TAMC_Color_Scheme_Reference.xml` | **Done** |
| 2 | HIGH | Tally formula off-by-one — BO29/BP29/BQ29 referenced wrong columns in `xml_to_xlsx_converter.py:580-582` | **Done** |
| 3 | MED | Row 4 placeholder faculty names — added `Faculty-*` filter in `_export_json_data()` | **Done** |
| 4 | MED | Rows 25-30 visible — added row dimension copy to `_copy_worksheet()` | **Done** |
| 5 | LOW | aSM not in REF — already present, false alarm | N/A |
| 6 | LOW | NF Wednesday LEC — not a bug (NF residents exempt from Wed PM lectures) | N/A |

### 11h: Hidden Sheet Analysis + Perplexity Council Review (Feb 27)

**Claude for Excel** analyzed all VeryHidden sheets (`__BASELINE__`, `__SYS_META__`, `__REF__`):

| Finding | Severity | Status |
|---------|----------|--------|
| Zero baseline drift (all 1,680 cells match) | Good | Confirmed |
| `__REF__` case-sensitivity bug — 15 uppercase codes missing, lowercase equivalents present | Bug | **Added as MEDIUM #35 to Master Priority List** |
| Missing baselines for 10 of 14 blocks | Expected | Only blocks 9, 10, 12, 13 were ever solved |
| Block 13 baseline truncated (54 rows, 1 faculty) | Investigate | May be expected if Block 13 has minimal data |
| Rotation name mismatch (FMIT vs FMIT-PGY1 in REF) | Design gap | Not broken, just unmapped abbreviations |

**Perplexity Council** (GPT-5.2 + Claude Opus 4.6 + Gemini 3.1 Pro) validated architecture:

| Recommendation | Actionability | Disposition |
|---------------|--------------|-------------|
| Never duplicate export in Node.js | Already doing this | No action |
| Named ranges in fat template | Good long-term, LOW priority | Added as future consideration |
| Deterministic generation (stable sort keys) | Useful for baseline fingerprinting | **LOW #32 in Master Priority List** |
| Template version validation (SHA256 sentinel) | Cheap insurance (~10 lines) | **LOW #31 in Master Priority List** |
| Export contract formalization (Pydantic schema) | Future-proofing | **LOW #33 in Master Priority List** |
| Hand-jam reconciliation loop | Most ambitious, deferred | **LOW #34 in Master Priority List** |

**Key council consensus:** Architecture is correct and exceeds recommendations. Sequential openpyxl generation → Office.js auditing is the right pattern. Python exporter is single source of truth — never build a parallel Node.js/ExcelJS path.

### 11i: Data Starvation Remediation (Feb 27)

**Root cause analysis:** Export pipeline renders DB faithfully. The gaps are upstream — the preloader was run BEFORE rotation handlers were added, and several DB constraints are broken/missing.

**Detailed plan:** [`OPUS_BLOCK_12_REMEDIATION_PLAN.md`](OPUS_BLOCK_12_REMEDIATION_PLAN.md) (Gemini-sourced, with corrections below)

**Resident coverage analysis (16 residents, 56 HDAs each expected):**

| Status | Count | Residents |
|--------|------:|-----------|
| Full (56/56) | 7 | R-PGY2-J, R-PGY2-A, R-PGY1-F, R-PGY2-O (solver), R-PGY3-C, R-PGY3-E, R-PGY3-I (preload) |
| Near-full (50/56) | 3 | R-PGY2-G (NF-CARDIO), R-PGY2-N (D+N), R-PGY1-D (NF-FMIT-PG) — 6 transition slots missing |
| Severely incomplete | 6 | R-PGY2-H (5), R-PGY1-P (13), R-PGY1-M (14), R-PGY3-B (17), R-PGY1-K (24), R-PGY1-L (40) |

**Key insight:** All rotation handlers already exist in `rotation_codes.py` (FMIT:266, NBN:273, PEDW:280, LDNF:260, NF:263, NF-combined:202). The `canonical_rotation_code()` normalizer covers all Block 12 codes. The primary fix is simply **re-running the preloader** — no new code needed for resident gaps.

**DB corrections needed:**

| Issue | Target | Fix |
|-------|--------|-----|
| NBN min>max constraint | `rotation_activity_requirements` | Set `min_halfdays=20, target_halfdays=24` |
| FMIT-PGY3 zero requirements | `rotation_activity_requirements` | Insert with `min_halfdays=0, target_halfdays=36` |
| 4 faculty missing templates | `faculty_weekly_templates` | Clone baseline pattern (14 rows per faculty) |
| aSM missing from activities | `activities` table | Insert if absent |

**Logic fix applied:**

| Fix | File | Change |
|-----|------|--------|
| Adjunct exclusion from solver | `engine.py:_persist_faculty_half_day_from_solver()` | Filter adjunct person_ids before writing HDAs |

**Corrections to OPUS plan:**

| OPUS Claim | Reality |
|------------|---------|
| NF-combined needs rotation_activity_requirements | Wrong — preloader handles these, not solver |
| NF_COMBINED_ACTIVITY_MAP missing entries | Wrong — all mappings exist in constants.py |
| PEDS-WARD needs new handling | Wrong — PEDW handler exists at rotation_codes.py:280 |

### 11j: Solver Constraint Triage + Excel Cross-Validation (Feb 27, PM)

**Problem:** After DB corrections and preloader re-run, the CP-SAT solver returned INFEASIBLE. Root cause: 15 hard constraints using `model.Add()` in CP-SAT — when preloaded data inherently violates them (e.g., faculty FMIT 7-day stretches vs 1-in-7 rule), the solver crashes and returns an empty payload, wiping all faculty schedules.

**Chain of failures (Gemini CLI session):**
1. Solver hit INFEASIBLE on `OneInSevenRuleConstraint` — 116 preloaded violations from faculty FMIT 7-day stretches
2. Gemini tried: zeroing all `min_halfdays`, disabling supervision, binary search across 15 hard constraints
3. Found `1in7Rule` as the blocker, disabled it, solver succeeded
4. Then Gemini added day_of_week migrations + `prefer_full_days` column that scrambled data
5. Multiple re-exports overwrote the good version

**Resolution (commit `9ecaccdc`):**
- Reverted Gemini's day_of_week migrations (quarantined as patch in `docs/archived/patches/`)
- Kept two valid changes: `FacultySupervision` Hard->Soft, adjunct query fix
- Disabled ALL policy hard constraints in `ConstraintManager.create_default()`
- Only 3 physically-impossible constraints remain enabled: `Availability`, `AdjunctCallExclusion`, `CallAvailability`
- Solver now returns OPTIMAL in <1s

**Constraint classification (new architecture):**

| Category | Constraints | Status |
|----------|-------------|--------|
| **Physical (enabled)** | Availability, AdjunctCallExclusion, CallAvailability | Hard — cannot be violated |
| **ACGME (disabled)** | 80HourRule, 1in7Rule, SupervisionRatio, FacultySupervision | Need refactor to indicator+penalty pattern |
| **Operational (disabled)** | ClinicCapacity, MaxPhysiciansInClinic, WeekendWork, NightFloatPostCall, FacultyClinicCap, ResidentInpatientHeadcount, PostFMITRecovery, PostFMITSundayBlocking | Need refactor to indicator+penalty pattern |
| **Faculty (disabled)** | FacultyPrimaryDutyClinic, FacultyDayAvailability, FacultyRoleClinic | Need refactor to indicator+penalty pattern |
| **Call (disabled)** | OvernightCallCoverage | Need refactor to indicator+penalty pattern |
| **Soft (always active)** | Coverage, Equity, Continuity, FacultyClinicEquity, call equity suite, resilience suite | Already use penalty/objective pattern |

**Excel cross-validation findings (Claude add-in for Excel, Turn 1):**

| Issue | Observed in Excel | DB Root Cause |
|-------|-------------------|---------------|
| All 13 faculty work every weekend | Zero W/OFF on Sat/Sun for any faculty | `WeekendWork` constraint disabled — solver fills all slots |
| Staff Call shows 1 name/night | Excel column shows first faculty only | DB has 46 call_assignments with multi-faculty per night (up to 4 on 5/17) |
| Resident Call row empty | All cells blank | 0 resident call_assignments in DB for Block 12 |
| 3 Staff Call date gaps | 5/7, 5/11, 5/25 uncovered | No call_assignments for those dates |
| 1 faculty in DB but not in Excel | 12 call assignments in DB | May be filtered as adjunct or not in export person list |
| SM faculty: zero C/CV | Only AT (39) + SM (8) | May be correct for SM-only faculty role |
| 1 resident: heavy LV front-load | LV first 3 weeks, then mixed | Correct — matches absence records |

**Priority fixes for next solver run:**

| Priority | Fix | Impact |
|----------|-----|--------|
| **P1** | Re-enable `WeekendWork` constraint only | Gives faculty weekends off |
| **P2** | Re-enable `ClinicCapacity` | Prevents over-scheduling clinic rooms |
| **P3** | Re-enable `FacultyDayAvailability` | Respects faculty availability preferences |
| **P4** | Investigate multi-call-per-night in export | Export currently drops all but first name |
| **P5** | Add resident call generation or manual entry | Resident Call row is empty |

**Constraint refactoring roadmap (future PR):**

To convert hard constraints to true soft constraints in CP-SAT:
1. Replace `model.Add(expr)` with indicator variable pattern:
   ```python
   indicator = model.NewBoolVar(f"satisfied_{constraint_name}_{i}")
   model.Add(expr).OnlyEnforceIf(indicator)
   penalty_vars.append((weight, indicator.Not()))
   ```
2. Add penalty sum to objective: `model.Minimize(sum(w * v for w, v in penalty_vars))`
3. Weight hierarchy: ACGME (1000) > Operational (500) > Faculty preference (100)
4. Test each constraint individually before batch-enabling

This is a significant refactor (~15 constraint files, ~30 `model.Add()` sites) and should be its own focused PR after the Block 12 export is validated.

### 11k: Future Work — Faculty Full-Day Preference (Deferred)

**Feature:** `prefer_full_days` boolean on `Person` model — when true, solver groups AM+PM clinic slots on the same day instead of scattering them across the week.

**Why deferred:** Attempted by Gemini CLI (commits `68f69d92`, `d4b9cc1a`, both reverted) before basics were locked in. Migration had broken `down_revision` pointing to a deleted migration (`be2e66649140`). The feature is valid but depends on:
1. Constraint refactoring (section 11j) — hard→soft conversion must be complete first
2. `FacultyPrimaryDutyClinicConstraint` re-enabled and working
3. WeekendWork + ClinicCapacity constraints validated (P1/P2 fixes)

**Implementation sketch (from Gemini spec, saved to `/tmp/gemini_full_day_preference.patch`):**
- Add `prefer_full_days` Boolean column to `people` table (default=true)
- In `FacultyPrimaryDutyClinicConstraint.add_to_cpsat()`: create indicator variable `is_full_day` per day, add soft bonus when AM+PM match
- Weight: ~100 (faculty preference tier)

**Prerequisite:** Lock in P1-P5 fixes from section 11j first.

**Execution order:** DB fixes (B1-B4) → purge Block 12 HDAs → preloader → solver → export
