# Schedule Generation Prerequisites

> **Purpose:** Document the required data loading order and scripts for production schedule generation
> **Created:** 2026-01-01 (Session 046)
> **Status:** Active

---

## Overview

Schedule generation requires data to be loaded in a specific order. The solver fills remaining slots after absences and FMIT (Family Medicine Inpatient Team) rotation assignments are established.

**Critical Order:**
```
1. Use Existing People (already in database)
       ↓
2. Load ABSENCES (leave, vacation, TDY, conferences)
       ↓
3. Pre-assign FMIT Rotation (Family Medicine Inpatient Team)
       ↓
4. Run Solver (fills remaining slots)
```

---

## Current Database State

### People (28 total)
Query: `SELECT name, type, pgy_level FROM people ORDER BY type, pgy_level, name;`

| Type | Count | PGY Levels |
|------|-------|------------|
| Residents | 18 | 6 × PGY1, 6 × PGY2, 6 × PGY3 |
| Faculty | 10 | N/A |

**Note:** Names are sanitized for GitHub (e.g., "PGY1 Resident 01"). Real names stay local only - see [Common Issues](#sanitized-names-intentional) for details.

### Rotation Templates (70 total)
- Inpatient rotations: Seeded
- Outpatient rotations: 26 templates seeded (Session 046)

---

## Data Loading Steps

### Step 1: Verify People Exist

```bash
# Check people count
docker compose -f docker-compose.local.yml exec -T db \
  psql -U scheduler -d residency_scheduler \
  -c "SELECT type, COUNT(*) FROM people GROUP BY type;"
```

Expected: 18 residents, 10 faculty

### Step 2: Load Absences

**Script:** `scripts/import_excel.py`
- Imports absences from Excel files
- Supports leave types: Annual, Sick, TDY, Conference, etc.

**Usage:**
```bash
docker compose -f docker-compose.local.yml exec backend \
  python scripts/import_excel.py --file absences.xlsx --type absences
```

**Direct SQL (for individual absences):**
```sql
INSERT INTO absences (id, person_id, start_date, end_date, absence_type, notes, created_at)
VALUES (
  gen_random_uuid(),
  'person-uuid-here',
  '2026-03-15',
  '2026-03-17',
  'TDY',
  'Conference attendance',
  NOW()
);
```

### Step 3: Pre-assign FMIT Rotation

FMIT (Family Medicine Inpatient Team) is a high-priority rotation that must be assigned BEFORE the solver runs.

**Script:** `scripts/seed_inpatient_rotations.py`
- Pre-assigns FMIT rotation slots
- Creates assignments for Family Medicine Inpatient Team

**Usage:**
```bash
docker compose -f docker-compose.local.yml exec backend \
  python scripts/seed_inpatient_rotations.py --block 10
```

### Step 4: Run Solver

**Script:** `scripts/scheduling/generate_schedule.py`

```bash
# Dry run first (recommended)
docker compose -f docker-compose.local.yml exec backend \
  python scripts/scheduling/generate_schedule.py --block 10 --dry-run --verbose

# Actual generation
docker compose -f docker-compose.local.yml exec backend \
  python scripts/scheduling/generate_schedule.py --block 10 --verbose
```

---

## Block Reference (AY 2025-2026)

| Block | Start Date | End Date | Days |
|-------|------------|----------|------|
| **10** | Thu, Mar 12, 2026 | Wed, Apr 8, 2026 | 28 |
| **11** | Thu, Apr 9, 2026 | Wed, May 6, 2026 | 28 |
| **12** | Thu, May 7, 2026 | Wed, Jun 3, 2026 | 28 |
| **13** | Thu, Jun 4, 2026 | Tue, Jun 30, 2026 | 27 |

See `docs/architecture/ACADEMIC_YEAR_BLOCKS.md` for full block schedule.

---

## Common Issues

### Sanitized Names (Intentional)
The database shows "PGY1 Resident 01", "Faculty 01" instead of real names:
- **This is intentional** - names are sanitized for GitHub (PHI protection)
- Real names stay in local database only, never committed to repository
- For local development with real names, update `people` table directly:
  ```sql
  UPDATE people SET name = 'Dr. Actual Name' WHERE id = 'uuid';
  ```
- **NEVER commit real names to the repository** (OPSEC/PERSEC requirement)

### Missing Absences
If absences are not reflected in schedule:
- Absences MUST be loaded BEFORE running solver
- Solver does not retroactively check for absences

### FMIT Not Assigned
If FMIT rotation slots are empty:
- FMIT MUST be pre-assigned BEFORE running solver
- Run `seed_inpatient_rotations.py` before schedule generation

### 28-Day Bug (Diagnosed)
Schedule view defaults to wrong date range:
- **Root cause:** Uses Monday start instead of Thursday (academic block boundary)
- **Missing:** Block number display (should show "Block 7 (Dec 18 - Jan 14)")
- **Fix documented:** `.claude/Scratchpad/BUG_28_DAY_SCHEDULE_VIEW.md`

---

## Data Files Reference

Sanitized Airtable exports (for reference/import):
- `docs/schedules/sanitized_residents.json`
- `docs/schedules/sanitized_faculty.json`
- `docs/schedules/sanitized_resident_absences.json`
- `docs/schedules/sanitized_faculty_absences.json`
- `docs/schedules/sanitized_block_schedule.json`
- `docs/schedules/sanitized_faculty_inpatient_schedule.json`

---

## Related Documentation

- [Schedule Generation Runbook](SCHEDULE_GENERATION_RUNBOOK.md)
- [Academic Year Blocks](../architecture/ACADEMIC_YEAR_BLOCKS.md)
- [Block 10 Roadmap](../planning/BLOCK_10_ROADMAP.md)

---

*This document was created based on Session 046 findings and user feedback.*
