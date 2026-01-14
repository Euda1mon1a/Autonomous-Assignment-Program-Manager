# Half-Day Assignment Data Model

> **Version:** 1.0
> **Date:** 2026-01-14
> **Status:** Approved Design
> **Author:** Session 104 (Claude + Dr. Montgomery)

## Executive Summary

This document defines the architecture for persisting schedule assignments at the half-day granularity. The design replaces the previous compute-on-read approach (BlockAssignment + WeeklyPattern → expand at query time) with persisted half-day assignments that use actual dates for inter-block logic.

## Design Principles

### 1. Dates Over Block References

Assignments use actual dates, not block+1 references. This enables:
- Natural inter-block constraint handling
- FMIT spanning blocks without special logic
- Leap year and year boundary handled automatically by date arithmetic

### 2. Belt & Suspenders

Every constraint is enforced at multiple layers:
- **Source tables**: Store the authoritative "what"
- **Preload phase**: Writes to half_day_assignments
- **Solver constraints**: Validate during optimization
- **Post-solve validation**: Final fail-safe check

Neither layer can fail silently. If preload has a bug, constraints catch it. If constraints have a bug, preload ensures correct data exists.

### 3. Source Priority

When multiple sources want the same slot:

| Priority | Source | Description |
|----------|--------|-------------|
| 1 | `preload` | FMIT, call, absences - NEVER overwritten |
| 2 | `manual` | Explicit human override |
| 3 | `solver` | Computed by CP-SAT |
| 4 | `template` | Default from WeeklyPattern |

---

## Academic Year Calendar Structure

All blocks start Thursday, end Wednesday (except Block 0 and 13).

```
Academic Year: July 1 - June 30

Block 0:  July 1 → First Thursday - 1 day
          Variable length (1-6 days)
          Purpose: Orientation, onboarding, calendar fudge factor

Blocks 1-12: Thursday → Wednesday
          Fixed 28 days (56 half-day assignments per person)

Block 13: Thursday → June 30
          Variable length (28+ days)
          Purpose: Absorb end-of-year remainder
```

**Example AY25-26:**
- July 1, 2025 = Tuesday
- Block 0 = July 1-2 (2 days)
- Block 1 = July 3-30 (28 days)
- Block 13 absorbs remainder to reach June 30, 2026

---

## Data Model

### Core Table: half_day_assignments

This is the unified schedule table. All sources merge here.

```sql
CREATE TABLE half_day_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core assignment
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    time_of_day VARCHAR(2) NOT NULL CHECK (time_of_day IN ('AM', 'PM')),
    activity_id UUID REFERENCES activities(id),

    -- Provenance
    source VARCHAR(20) NOT NULL CHECK (source IN ('template', 'preload', 'solver', 'manual')),
    block_assignment_id UUID REFERENCES block_assignments(id),

    -- Override tracking
    is_override BOOLEAN DEFAULT FALSE,
    override_reason TEXT,
    overridden_by UUID REFERENCES users(id),
    overridden_at TIMESTAMP,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    UNIQUE(person_id, date, time_of_day)
);

-- Performance indexes
CREATE INDEX idx_hda_person_date ON half_day_assignments(person_id, date);
CREATE INDEX idx_hda_date_range ON half_day_assignments(date);
CREATE INDEX idx_hda_activity ON half_day_assignments(activity_id);
CREATE INDEX idx_hda_source ON half_day_assignments(source);
```

### Source Table: inpatient_preloads

For FMIT, Night Float, Peds Ward, and other inpatient rotations.

```sql
CREATE TABLE inpatient_preloads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
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

    UNIQUE(person_id, start_date, rotation_type),
    CHECK (rotation_type IN ('FMIT', 'NF', 'PedW', 'PedNF', 'KAP', 'IM', 'LDNF'))
);
```

### Source Table: resident_call_preloads

For L&D call and Night Float coverage (Chief-assigned).

```sql
CREATE TABLE resident_call_preloads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    call_date DATE NOT NULL,
    call_type VARCHAR(20) NOT NULL,  -- 'ld_24hr', 'nf_coverage', 'weekend'

    -- Provenance
    assigned_by VARCHAR(20),  -- 'chief', 'scheduler'

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(person_id, call_date),
    CHECK (call_type IN ('ld_24hr', 'nf_coverage', 'weekend'))
);
```

---

## Preload Flow

### Phase 1: Load Source Tables

```
absences              → LV-AM, LV-PM
inpatient_preloads    → FMIT, NF, PedW, KAP, IM, C-I
resident_call_preloads → CALL, PC
faculty_call          → CALL, PCAT, DO
```

### Phase 2: Write to half_day_assignments

- All assignments written with `source='preload'`
- Validate no overlaps before writing
- Protected slots cannot be overwritten by solver

### Phase 3: Solver Runs

- Respects preloaded slots (skips them)
- Fills remaining slots with `source='solver'`
- Constraints validate inpatient rules as fail safe

### Phase 4: Post-Solve Validation

- FMIT residents have C-I on correct day?
- NF has post-call Thursday?
- No double-booking?
- ACGME work hours OK?

---

## Inter-Block Logic

With actual dates, inter-block constraints are natural:

```python
# PCAT/DO from Wednesday call carries to Thursday (next block)
if call_date.weekday() == 2:  # Wednesday
    pcat_date = call_date + timedelta(days=1)  # Thursday
    HalfDayAssignment(
        person_id=faculty_id,
        date=pcat_date,
        time_of_day="AM",
        activity_id=pcat_activity_id,
        source="preload"
    )
```

### Examples

| Scenario | Handling |
|----------|----------|
| PCAT/DO from Wednesday call | Thursday = next block; insert by date |
| Faculty FMIT spanning blocks | FMIT is date-based, not block-based |
| Night Float post-call | NF ends Wednesday, post-call Thursday = next block |
| Post-FMIT PC | PC Friday may be in next block |

**FMIT Example (Block 10-11 boundary):**
```
LaBounty FMIT: Apr 3 (Fri) - Apr 9 (Thu)  ← Spans Block 10/11
Post-FMIT PC: Apr 10 (Fri)                ← In Block 11
```

---

## Storage Estimates

```
Residents: 17 × 13 blocks × 56 half-days = 12,376 rows/year
Faculty:   14 × 13 blocks × 56 half-days = 10,192 rows/year
Block 0:   31 × ~4 half-days = ~124 rows/year
Block 13:  31 × ~60 half-days = ~1,860 rows/year
─────────────────────────────────────────────────────────
Total:     ~24,500 rows/year (trivial for PostgreSQL)
```

---

## FMIT Inpatient Clinic (C-I)

Residents on FMIT have protected continuity clinic:

| PGY Level | C-I Day | Notes |
|-----------|---------|-------|
| PGY-1 | Wednesday AM | Hard constraint - intern continuity |
| PGY-2 | Tuesday PM | FMIT resident clinic |
| PGY-3 | Monday PM | FMIT resident clinic |

C-I is PRELOADED, not solved. These slots are locked before solver runs.

---

## Activity Granularity

Clinic activities are separate for appointment duration:

| Activity | Duration | Use Case |
|----------|----------|----------|
| C | Standard | Experienced residents/faculty |
| C30 | 30 min | Standard appointments |
| C40 | 40 min | New learners (more time per patient) |
| C60 | 60 min | New interns (maximum time) |
| C-I | Varies | FMIT inpatient follow-up clinic |

---

## Migration Strategy

### Phase 1: Add Tables
- Create `half_day_assignments` table
- Create `inpatient_preloads` table
- Create `resident_call_preloads` table
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

---

## Related Documents

- `.claude/skills/tamc-excel-scheduling/SKILL.md` - Scheduling workflow and rules
- `.claude/Scratchpad/session-104-half-day-model.md` - Design session notes
- `backend/app/models/block_assignment.py` - Block-level assignments
- `backend/app/models/activity.py` - Activity definitions

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-14 | Initial design approved |
