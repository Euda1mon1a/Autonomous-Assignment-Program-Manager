***REMOVED*** Block Schedule Architecture

> **Last Verified:** 2025-12-25
> **Purpose:** Comprehensive documentation of the block schedule hierarchy and full-stack implementation

---

***REMOVED******REMOVED*** 1. Time Hierarchy Overview

The scheduler uses a hierarchical time structure that maps the Academic Year down to half-day assignment slots:

```
ACADEMIC YEAR (365-366 days)
│   July 1 ────────────────────────────────────────────► June 30
│
├── 13 ACADEMIC BLOCKS (28 days each, 4 weeks)
│   │   Block 1: Jul 1-28
│   │   Block 2: Jul 29 - Aug 25
│   │   ...
│   │   Block 13: Jun 3-30 (extended to complete AY)
│   │
│   ├── 2 BLOCK-HALVES per block (14 days each)
│   │   │   Used for NF (Night Float) and NICU rotations
│   │   │   block_half = 1 (days 1-14) or 2 (days 15-28)
│   │   │
│   │   └── 28 CALENDAR DAYS per block
│   │       │
│   │       └── 2 HALF-DAY SLOTS per day (AM/PM)
│   │           │   AM: 8:00 AM - 12:00 PM
│   │           │   PM: 1:00 PM - 5:00 PM
│   │           │
│   │           └── ASSIGNMENT (Person + Block + Rotation)
```

***REMOVED******REMOVED******REMOVED*** Counts Per Academic Year

| Level | Count | Formula |
|-------|-------|---------|
| Academic Year | 1 | Fixed: July 1 - June 30 |
| Academic Blocks | 13 | 52 weeks ÷ 4 weeks/block |
| Block-Halves | 26 | 13 blocks × 2 halves |
| Calendar Days | 365 | Standard year |
| **Half-Day Slots** | **730** | 365 days × 2 (AM/PM) |

---

***REMOVED******REMOVED*** 2. Calendar Systems

***REMOVED******REMOVED******REMOVED*** Gregorian Calendar (Display Only)

The system intentionally ignores Gregorian month boundaries for scheduling. Gregorian dates are only used for:
- ICS calendar exports (`calscale="GREGORIAN"`)
- User-facing date displays
- External calendar integration

***REMOVED******REMOVED******REMOVED*** Academic Block Calendar (Scheduling)

All scheduling logic uses 28-day academic blocks:

```
GREGORIAN:
│ Jan │ Feb │ Mar │ Apr │ May │ Jun │ Jul │ Aug │ Sep │ Oct │ Nov │ Dec │

ACADEMIC BLOCKS:
│ B1  │ B2  │ B3  │ B4  │ B5  │ B6  │ B7  │ B8  │ B9  │ B10 │ B11 │ B12 │B13│
└─Jul 1                                                          Jun 30─┘
```

**Every block from 2-12 crosses at least one Gregorian month boundary.** This is by design.

***REMOVED******REMOVED******REMOVED*** FMIT Calendar (Exception)

FMIT (Faculty Managing Inpatient Teaching) operates on **Friday-Thursday weeks**:
- Independent of both Gregorian months and academic blocks
- Uses `get_fmit_week_dates()` in `backend/app/scheduling/constraints/fmit.py`

---

***REMOVED******REMOVED*** 3. Block-to-Date Conversion

***REMOVED******REMOVED******REMOVED*** Formula

```python
***REMOVED*** Academic year always starts July 1
academic_year_start = date(year, 7, 1)  ***REMOVED*** If month >= 7, else year-1

***REMOVED*** Block boundaries
block_start = academic_year_start + timedelta(days=(block_number - 1) * 28)
block_end = block_start + timedelta(days=27)  ***REMOVED*** 28 days inclusive

***REMOVED*** Block 13 extended to June 30 to complete academic year
if block_number == 13:
    block_end = date(year + 1, 6, 30)
```

***REMOVED******REMOVED******REMOVED*** Example: AY 2025-2026

| Block | Start | End | Gregorian Months |
|-------|-------|-----|------------------|
| 1 | Jul 1, 2025 | Jul 28, 2025 | July |
| 2 | Jul 29, 2025 | Aug 25, 2025 | July + August |
| 3 | Aug 26, 2025 | Sep 22, 2025 | August + September |
| 7 | Dec 9, 2025 | Jan 5, 2026 | December + January |
| 10 | Mar 10, 2026 | Apr 6, 2026 | March + April |
| 13 | Jun 3, 2026 | Jun 30, 2026 | June |

---

***REMOVED******REMOVED*** 4. Database Schema

***REMOVED******REMOVED******REMOVED*** Block Table

```sql
CREATE TABLE blocks (
    id UUID PRIMARY KEY,
    date DATE NOT NULL,
    time_of_day VARCHAR(2) NOT NULL,  -- 'AM' or 'PM'
    block_number INTEGER NOT NULL,     -- 1-13
    is_weekend BOOLEAN DEFAULT FALSE,
    is_holiday BOOLEAN DEFAULT FALSE,
    holiday_name VARCHAR(255),

    CONSTRAINT unique_block_per_half_day UNIQUE (date, time_of_day),
    CONSTRAINT check_time_of_day CHECK (time_of_day IN ('AM', 'PM'))
);
```

***REMOVED******REMOVED******REMOVED*** Assignment Table

```sql
CREATE TABLE assignments (
    id UUID PRIMARY KEY,
    block_id UUID REFERENCES blocks(id) ON DELETE CASCADE,
    person_id UUID REFERENCES people(id) ON DELETE CASCADE,
    rotation_template_id UUID REFERENCES rotation_templates(id),
    role VARCHAR(50) NOT NULL,  -- 'primary', 'supervising', 'backup'

    -- Explainability
    explain_json JSONB,
    confidence FLOAT,
    score FLOAT,

    CONSTRAINT unique_person_per_block UNIQUE (block_id, person_id),
    CONSTRAINT check_role CHECK (role IN ('primary', 'supervising', 'backup'))
);
```

***REMOVED******REMOVED******REMOVED*** Rotation Template Activity Types

| activity_type | Solver Handling | Examples |
|---------------|-----------------|----------|
| `outpatient` | **Optimized by solver** | Clinic, Sports Med, ID Selective |
| `inpatient` | **Pre-assigned, preserved** | FMIT, Night Float, NICU |
| `absence` | **Pre-loaded as unavailable** | Leave, Weekend, TDY |
| `clinic` | Has facility constraints | Physical clinic locations |

---

***REMOVED******REMOVED*** 5. Solver Architecture

***REMOVED******REMOVED******REMOVED*** Decision Variables

The solver uses 3D boolean variables:

```
x[r_i, b_i, t_i] ∈ {0, 1}

where:
  r_i = resident index (0 to N-1)
  b_i = block index (0 to B-1)    ← Each block = one AM or PM slot
  t_i = template index (0 to T-1) ← Outpatient templates only

x[r_i, b_i, t_i] = 1  iff  resident r assigned to template t in block b
```

***REMOVED******REMOVED******REMOVED*** What Solver Handles vs. Preserves

| Category | Handling |
|----------|----------|
| Outpatient templates | Optimized by solver |
| FMIT assignments | Pre-loaded, preserved |
| Night Float / NICU | Pre-assigned, preserved |
| Absences | Loaded as unavailable |
| Post-Call | Created automatically after NF |

***REMOVED******REMOVED******REMOVED*** Available Algorithms

- `greedy`: Fast heuristic with explainability
- `cp_sat`: OR-Tools constraint programming (primary)
- `pulp`: Linear programming backup
- `hybrid`: Combined approach

---

***REMOVED******REMOVED*** 6. API Endpoints

***REMOVED******REMOVED******REMOVED*** Block Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/blocks` | List blocks with date/block filters |
| GET | `/api/v1/blocks/{id}` | Get single block |
| POST | `/api/v1/blocks/generate` | Generate blocks for date range |

***REMOVED******REMOVED******REMOVED*** Schedule Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/schedule/generate` | Generate schedule (supports idempotency) |
| GET | `/api/v1/schedule/validate` | Validate ACGME compliance |

***REMOVED******REMOVED******REMOVED*** Response Schema

```json
{
  "id": "uuid",
  "date": "2025-07-01",
  "time_of_day": "AM",
  "block_number": 1,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

---

***REMOVED******REMOVED*** 7. Frontend Integration

***REMOVED******REMOVED******REMOVED*** TypeScript Types

```typescript
interface Block {
  id: UUID;
  date: DateString;
  time_of_day: 'AM' | 'PM';
  block_number: number;
  is_weekend: boolean;
  is_holiday: boolean;
  holiday_name: string | null;
}
```

***REMOVED******REMOVED******REMOVED*** Data Fetching

ScheduleGrid executes 4 parallel queries:
1. `GET /blocks?start_date=...&end_date=...`
2. `GET /assignments?start_date=...&end_date=...`
3. `GET /people`
4. `GET /rotation-templates`

***REMOVED******REMOVED******REMOVED*** Block Navigation

BlockNavigation maintains 28-day academic block ranges using `addDays(28)` / `subDays(28)`.

---

***REMOVED******REMOVED*** 8. ACGME Compliance

***REMOVED******REMOVED******REMOVED*** Validated Rules

| Rule | Description | Implementation |
|------|-------------|----------------|
| 80-Hour Rule | Max 80 hrs/week, rolling 4-week average | `_check_80_hour_rule()` |
| 1-in-7 Rule | One 24-hr off period every 7 days | `_check_1_in_7_rule()` |
| Supervision Ratios | 1:2 for PGY-1, 1:4 for PGY-2/3 | `_check_supervision_ratios()` |

---

***REMOVED******REMOVED*** 9. Key Files Reference

| Layer | File | Purpose |
|-------|------|---------|
| Model | `backend/app/models/block.py` | Block model (730/year) |
| Model | `backend/app/models/assignment.py` | Assignment model |
| Model | `backend/app/models/rotation_template.py` | Rotation definitions |
| Solver | `backend/app/scheduling/engine.py` | Orchestration |
| Solver | `backend/app/scheduling/solvers.py` | CP-SAT, Greedy, PuLP |
| Constraints | `backend/app/scheduling/constraints/` | 15 constraint modules |
| API | `backend/app/api/routes/blocks.py` | Block endpoints |
| API | `backend/app/api/routes/schedule.py` | Schedule generation |
| Frontend | `frontend/src/types/api.ts` | TypeScript types |
| Frontend | `frontend/src/hooks/useSchedule.ts` | Data fetching hooks |
| Frontend | `frontend/src/components/schedule/ScheduleGrid.tsx` | Schedule display |

---

***REMOVED******REMOVED*** 10. Constants

```python
***REMOVED*** From AcademicBlockService
BLOCK_DURATION_WEEKS = 4
BLOCK_DURATION_DAYS = 28
HOURS_PER_HALF_DAY = 6
MAX_WEEKLY_HOURS_ACGME = 80
EXPECTED_BLOCKS_PER_YEAR = 13

***REMOVED*** Implicit in structure
DAYS_PER_YEAR = 365
HALF_DAY_BLOCKS_PER_YEAR = 730  ***REMOVED*** 365 × 2
```

---

***REMOVED******REMOVED*** Summary

The Residency Scheduler correctly implements the block schedule architecture:

- **730 half-day blocks** (AM/PM) are the solver's atomic unit
- **13 academic blocks** (28 days) define rotation periods
- **Gregorian months are ignored** for scheduling logic
- **Solver only handles outpatient** templates; inpatient/absence preserved
- **Full-stack type alignment** between backend and frontend confirmed
