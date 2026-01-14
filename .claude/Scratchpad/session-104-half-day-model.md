# Session 104: Half-Day Assignment Data Model

> **Date:** 2026-01-14
> **Status:** COMPLETE (Design Phase)
> **Decision:** Option B - Persist Half-Day Assignments
> **Context:** ~8% remaining

## Executive Summary

Transitioning from compute-on-read (BlockAssignment + WeeklyPattern → expand) to **persisted half-day assignments**. This enables:
- Inter-block logic with actual dates
- Preloaded assignments (FMIT, C-I, call) stored in DB
- Frontend showing actual assignments, not rotation templates
- Solver writes directly to half-day table

## Data Model Design

### New Table: `half_day_assignments`

```sql
CREATE TABLE half_day_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core assignment
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    date DATE NOT NULL,                    -- Actual date (inter-block natural)
    time_of_day VARCHAR(2) NOT NULL,       -- "AM" or "PM"
    activity_id UUID REFERENCES activities(id),

    -- Provenance
    source VARCHAR(20) NOT NULL,           -- See SourceType enum
    block_assignment_id UUID REFERENCES block_assignments(id),

    -- Override tracking
    is_override BOOLEAN DEFAULT FALSE,     -- True if manually changed from template
    override_reason TEXT,
    overridden_by UUID REFERENCES users(id),
    overridden_at TIMESTAMP,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    UNIQUE(person_id, date, time_of_day),
    CHECK(time_of_day IN ('AM', 'PM')),
    CHECK(source IN ('template', 'preload', 'solver', 'manual'))
);

-- Performance indexes
CREATE INDEX idx_hda_person_date ON half_day_assignments(person_id, date);
CREATE INDEX idx_hda_date_range ON half_day_assignments(date);
CREATE INDEX idx_hda_activity ON half_day_assignments(activity_id);
CREATE INDEX idx_hda_source ON half_day_assignments(source);
```

### Source Types

| Source | Meaning | Examples |
|--------|---------|----------|
| `template` | Expanded from WeeklyPattern | FMC → C on Monday AM |
| `preload` | Manually preloaded (belt & suspenders) | FMIT, C-I, NF, call, aSM |
| `solver` | Assigned by CP-SAT solver | Outpatient C, faculty AT |
| `manual` | Human override | Swap, leave adjustment |

### Priority Order (Conflict Resolution)

When multiple sources want the same slot:
```
1. preload (FMIT, call, absences) - NEVER overwritten
2. manual (explicit human override)
3. solver (computed assignments)
4. template (default pattern)
```

## Calendar Structure (Confirmed)

```
Academic Year: July 1 - June 30

Block 0:  July 1 → First Thursday - 1 (variable: 1-6 days)
          Purpose: Orientation, calendar fudge

Blocks 1-12: Thursday → Wednesday (28 days each, 56 half-days)

Block 13: Thursday → June 30 (variable: 28+ days)
          Purpose: Absorb end-of-year remainder
```

## Workflow Changes

### Before (Current)
```
1. BlockAssignment created (block-level)
2. WeeklyPattern defines template
3. Expansion service computes half-days at query time
4. Frontend shows rotation templates only
```

### After (New)
```
1. BlockAssignment created (block-level) - unchanged
2. Preloads written to half_day_assignments (FMIT, C-I, call, aSM, absences)
3. Template expansion writes baseline to half_day_assignments (source='template')
4. Solver overwrites solvable slots (source='solver')
5. Frontend queries half_day_assignments directly
6. Manual overrides update in place (source='manual', is_override=true)
```

### Preload Order (Canonical)

1. **Absences** (LV, HOL, DEP, TDY)
2. **FMIT** - both faculty and resident
3. **FMIT Fri/Sat call** - auto-assigned with FMIT
4. **C-I** (inpatient follow-up clinic):
   - PGY-1: Wednesday AM
   - PGY-2: Tuesday PM
   - PGY-3: Monday PM
5. **Night Float** - full pattern including post-call
6. **aSM** - Wednesday AM for SM faculty (Tagawa)
7. **Conferences** (HAFP, USAFP, LEC)
8. **Protected time** (SIM, PI, MM)

## Inter-Block Logic

With actual dates, inter-block is natural:

```python
# PCAT/DO from Wednesday call carries to Thursday (next block)
if call_date.weekday() == 2:  # Wednesday
    pcat_date = call_date + timedelta(days=1)  # Thursday
    # Just insert - block_id is irrelevant
    HalfDayAssignment(
        person_id=faculty_id,
        date=pcat_date,
        time_of_day="AM",
        activity_id=pcat_activity_id,
        source="preload"
    )
```

No block+1 references needed. Solver queries by date range.

## FMIT Spanning Blocks

Faculty FMIT is independent of block boundaries:

```
Block 10: Mar 12 - Apr 8
LaBounty FMIT: Apr 3 (Fri) - Apr 9 (Thu)
Post-FMIT PC: Apr 10 (Fri) - in Block 11

All stored as dates. Block 11 sees LaBounty's PC automatically.
```

## Row Count Estimate

```
Residents: 17 × 13 blocks × 56 half-days = 12,376 rows/year
Faculty:   14 × 13 blocks × 56 half-days = 10,192 rows/year
Block 0:   31 × ~4 half-days = ~124 rows/year
Block 13:  31 × ~60 half-days = ~1,860 rows/year
---------------------------------------------------------
Total:     ~24,500 rows/year (trivial for PostgreSQL)
```

## Migration Strategy

### Phase 1: Add Table
- Create `half_day_assignments` table
- Add indexes and constraints

### Phase 2: Dual-Write
- Expansion service writes to new table
- Frontend still reads from old path
- Verify data matches

### Phase 3: Switch Read Path
- Frontend reads from `half_day_assignments`
- Keep BlockAssignment for block-level metadata

### Phase 4: Solver Integration
- Solver writes directly to `half_day_assignments`
- Source = 'solver' for computed slots

## Open Questions

1. **Block 0/13 handling**: Do they have assignments or just administrative?
2. **Resident call**: Stored here or separate table? (Chief-assigned, L&D)
3. **Activity granularity**: C vs C30 vs C40 vs C-I - separate activities or flags?

## Related Files

- `backend/app/models/block_assignment.py` - Block-level (unchanged)
- `backend/app/models/activity.py` - Activity definitions
- `backend/app/services/faculty_assignment_expansion_service.py` - Will write to new table
- `.claude/skills/tamc-excel-scheduling/SKILL.md` - Workflow documentation

## Next Steps

1. [ ] Finalize table schema (review open questions)
2. [ ] Create Alembic migration
3. [ ] Update expansion service to write half-days
4. [ ] Add preload service for FMIT/C-I/call
5. [ ] Update frontend to query half_day_assignments
6. [ ] Integrate solver output

---

*This design enables the elegant solved approach the user envisioned, replacing the static Airtable/n8n template matching.*

---

## Resume Instructions

Session 104 complete (design phase). If continuing this work:

### Immediate Next Step
Create Alembic migration for `half_day_assignments` table.

### Key Context
1. **User confirmed Option B** (persist half-days with actual dates)
2. **Calendar structure confirmed**: Block 0/13 are fudge factors, Blocks 1-12 are 28 days each
3. **FMIT is date-based**, not block-based - spans blocks naturally
4. **C-I is PRELOADED** for FMIT residents (PGY-1 Wed AM, PGY-2 Tue PM, PGY-3 Mon PM)

### Files Modified This Session
- `.claude/Scratchpad/session-104-half-day-model.md` - This file (design doc)
- `.claude/skills/tamc-excel-scheduling/SKILL.md` - v1.4, added calendar structure and edge cases
- `HUMAN_TODO.md` - Added pending follow-ups (Peds NF, resident call)

### Open Questions - RESOLVED

1. **Block 0/13 assignments**: Normal assignments for both
   - Block 0: Follow logic from preceding year rotation
   - New intern (no preceding year): Just assign FLX
   - Block 13: Normal assignments

2. **Resident call**: Both
   - Store in separate preload table (like absences)
   - Copy to `half_day_assignments` during preload phase
   - Pattern: preload table → half_day_assignments

3. **Activity granularity**: Separate activities
   - C = standard clinic
   - C30 = 30-minute appointments
   - C40 = 40-minute appointments
   - C60 = 60-minute appointments
   - Purpose: New learners need more time per patient
   - **Document for later** - not blocking current work

4. **Inpatient rotations**: Option B - Separate preload table
   - Same pattern as absences (belt & suspenders)
   - Preload table → half_day_assignments
   - Constraints in solver as fail safe

## Preload Table Design

### Pattern: Source Table → half_day_assignments

All preloads follow the same pattern:
1. Source table stores the "what" (date ranges, assignments)
2. Preload phase writes to `half_day_assignments` (source='preload')
3. Solver respects preloaded slots (cannot overwrite)
4. Constraints validate as fail safe

### Source Tables

```sql
-- Already exists
absences (person_id, start_date, end_date, absence_type, ...)
    ↓ preload phase
half_day_assignments (source='preload', activity=LV)

-- NEW: Inpatient rotation preloads
inpatient_preloads (
    id UUID PRIMARY KEY,
    person_id UUID NOT NULL REFERENCES people(id),
    rotation_type VARCHAR(20) NOT NULL,  -- FMIT, NF, PedW, PedNF, KAP, IM, LDNF
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    -- For faculty FMIT (week-based)
    fmit_week_number INT,  -- 1-4 within block (NULL for residents)

    -- For NF/LDNF (shift timing)
    includes_post_call BOOLEAN DEFAULT TRUE,

    -- Provenance
    assigned_by VARCHAR(20),  -- 'chief', 'scheduler', 'coordinator', 'manual'

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    UNIQUE(person_id, start_date, rotation_type)
);
    ↓ preload phase
half_day_assignments (source='preload', activity=FMIT/NF/etc.)

-- NEW: Resident call preloads (L&D, NF coverage)
resident_call_preloads (
    id UUID PRIMARY KEY,
    person_id UUID NOT NULL REFERENCES people(id),
    call_date DATE NOT NULL,
    call_type VARCHAR(20) NOT NULL,  -- 'ld_24hr', 'nf_coverage', 'weekend'

    -- Provenance
    assigned_by VARCHAR(20),  -- 'chief', 'scheduler'

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(person_id, call_date)
);
    ↓ preload phase
half_day_assignments (source='preload', activity=CALL/PC)
```

### Preload Flow (Belt & Suspenders)

```
Phase 1: Load Source Tables
├── absences → LV-AM, LV-PM
├── inpatient_preloads → FMIT, NF, PedW, KAP, IM, C-I
├── resident_call_preloads → CALL, PC
└── faculty_call (existing?) → CALL, PCAT, DO

Phase 2: Write to half_day_assignments
├── All with source='preload'
├── is_protected=TRUE (solver cannot modify)
└── Validate no overlaps

Phase 3: Solver runs
├── Respects preloaded slots
├── Fills remaining slots (source='solver')
└── Constraints validate inpatient rules as FAIL SAFE

Phase 4: Constraint Validation (Belt & Suspenders)
├── FMIT residents have C-I on correct day? (PGY-1 Wed AM, etc.)
├── NF has post-call Thursday?
├── No double-booking?
└── ACGME work hours OK?
```

### Why Belt & Suspenders?

| Layer | Purpose | Catches |
|-------|---------|---------|
| **Preload table** | Source of truth for inpatient | Missing assignments |
| **Preload phase** | Writes to half_day_assignments | Ensures slots exist |
| **Solver constraints** | Validates during solve | Logic errors in preload |
| **Post-solve validation** | Final check | Edge cases, bugs |

If preload has a bug, constraints catch it.
If constraints have a bug, preload ensures correct data exists.
Neither can fail silently.

### Edge Cases Resolved
| Edge Case | Resolution |
|-----------|------------|
| Call before FMIT | Min 3-day buffer, prefer no call week before |
| PCAT/DO inter-block | Use actual dates, carries naturally |
| FMIT spanning blocks | Date-based, not block-tied |
| Multiple SM residents | Max 2, Tagawa supervises both, must match half-day |
| Tagawa post-call + SM | Medium constraint (avoid, not fail) |
| PGY-1 on FMIT | Still gets Wednesday AM continuity (C-I) |
| CLC on holiday | Skip, does not reschedule |
