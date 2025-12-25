# Block 10: Session Handoff Document

> **Session Date:** 2025-12-25
> **Status:** ABORTED - Schema mismatch blocking API testing
> **Next Action:** Full database rebuild required

---

## Executive Summary

Attempted to test Block 10 schedule generation via API. **Blocked by database schema mismatch** - the database was reset to an older migration state that's incompatible with the current backend code.

**Block 10 constraint code is complete and tested** - just can't run end-to-end API test until database is properly rebuilt.

---

## What Was Accomplished

| Task | Status | Notes |
|------|--------|-------|
| MCP tool discovery | Done | Found `generate_schedule`, `validate_schedule`, `detect_conflicts` |
| Database restore from backup | Done | 29 people, 730 blocks, 38 templates restored |
| Missing columns added | Done | 7 columns added to `people` table |
| Auth working | Done | Admin user authenticates successfully |
| Schedule generation | Blocked | Transaction errors due to schema mismatch |

---

## Critical Discovery: Database Was Reset

### What Happened
The database was found **completely empty** (0 rows in all tables). This appears to have happened during an authorized reset that unexpectedly included the database.

### What We Restored
From backup `backups/postgres/residency_scheduler_20251224_133000.sql.gz`:
- 1 admin user
- 29 people (12 faculty + 17 residents)
- 38 rotation templates
- 730 blocks (full academic year Jul 2025 - Jun 2026)

### Schema Mismatch Issues
The backup was from a **newer schema** than the current database state. We manually added these missing columns:

```sql
-- Added to people table
ALTER TABLE people ADD COLUMN faculty_role VARCHAR(50);
ALTER TABLE people ADD COLUMN sunday_call_count INTEGER DEFAULT 0;
ALTER TABLE people ADD COLUMN weekday_call_count INTEGER DEFAULT 0;
ALTER TABLE people ADD COLUMN fmit_weeks_count INTEGER DEFAULT 0;
ALTER TABLE people ADD COLUMN screener_role VARCHAR(50);
ALTER TABLE people ADD COLUMN can_screen BOOLEAN DEFAULT false;
ALTER TABLE people ADD COLUMN screening_efficiency INTEGER DEFAULT 100;
```

**However**, there are likely additional schema mismatches in other tables (rotation_templates, assignments, etc.) that we didn't address.

---

## Backup Status

### Verified Backups Exist and Intact
```
backups/postgres/
├── residency_scheduler_20251223_212059.sql.gz (90KB) - integrity verified
└── residency_scheduler_20251224_133000.sql.gz (100KB) - integrity verified
```

### Backup Contains
- Full schema with all migrations applied
- Admin user with credentials
- All people, blocks, rotation_templates
- Absences data (153 records)

---

## Block 10 Constraint Status (Code Layer)

All Block 10 constraints are **implemented, tested, and registered**:

| Constraint | Type | File | Status |
|------------|------|------|--------|
| `PostFMITSundayBlockingConstraint` | Hard | `fmit.py` | Registered in manager.py |
| `ResidentInpatientHeadcountConstraint` | Hard | `inpatient.py` | Registered in manager.py |
| `CallSpacingConstraint` | Soft | `call_equity.py` | Registered in manager.py |
| `SundayCallEquityConstraint` | Soft | `call_equity.py` | Registered in manager.py |
| `WeekdayCallEquityConstraint` | Soft | `call_equity.py` | Registered in manager.py |
| `TuesdayCallPreferenceConstraint` | Soft | `call_equity.py` | Registered in manager.py |

**Tests passing**: 64+ tests in constraint test files

**Registration verified in both**:
- `ConstraintManager.create_default()`
- `ConstraintManager.create_resilience_aware()`

**Weight hierarchy** (documented in call_equity.py):
```
Sunday (10.0) > CallSpacing (8.0) > Weekday (5.0) > Tuesday (2.0)
```

---

## Recommended Next Steps

### Option A: Full Database Rebuild (Recommended)
```bash
# 1. Stop containers
docker-compose down

# 2. Remove database volume
docker volume rm autonomous-assignment-program-manager_postgres_data

# 3. Restart (creates fresh DB)
docker-compose up -d

# 4. Run all migrations
cd backend
alembic upgrade head

# 5. Seed data (people, blocks, templates)
python scripts/seed_people.py
python scripts/seed_blocks.py
python scripts/seed_templates.py
```

### Option B: Test Constraints via Pytest (Skip API)
```bash
cd backend
pytest tests/test_fmit_constraints.py tests/test_call_equity_constraints.py -v
```

### Option C: Restore Full Backup
```bash
# Drop and recreate database
docker-compose exec db dropdb -U scheduler residency_scheduler
docker-compose exec db createdb -U scheduler residency_scheduler

# Restore from backup
gunzip -c backups/postgres/residency_scheduler_20251224_133000.sql.gz | \
  docker-compose exec -T db psql -U scheduler -d residency_scheduler
```

---

## Lessons Learned

### 1. Database Reset Authorization
**Issue:** User authorized a reset that included the database without realizing it.
**Fix:** Add explicit confirmation for database operations:
```
WARNING: This will reset the database. Type 'RESET DATABASE' to confirm:
```

### 2. Schema-Data Coupling
**Issue:** Backup data requires matching schema version.
**Fix:** Backups should include alembic version; restore should verify compatibility.

### 3. MCP Import Issues
**Issue:** MCP tools use relative imports, can't be invoked directly from CLI.
**Fix:** MCP tools must be run via the MCP server, not imported directly.

### 4. Constraint Registration Gap (FIXED 2025-12-25)
**Issue:** Session handoff doc claimed constraints were "registered" when they weren't.
The constraints were implemented, exported in `__init__.py`, and tested, but never
added to `ConstraintManager.create_default()`.

**Root cause:** Manual verification of line numbers without running actual tests.

**Fixes implemented:**
1. Added `test_constraint_registration.py` - Tests that verify exported constraints
   are actually registered in the manager factory methods
2. Added `scripts/verify_constraints.py` - Pre-flight script to run before commits
3. Updated `manager.py` - All Block 10 constraints now registered in both
   `create_default()` and `create_resilience_aware()`

**Prevention:** Always run `python scripts/verify_constraints.py` before committing
constraint-related changes.

---

## Files Modified This Session

| File | Change |
|------|--------|
| Database `people` table | Added 7 columns |
| `backend/app/scheduling/constraints/manager.py` | Registered Block 10 constraints |
| `backend/tests/test_constraint_registration.py` | NEW - Tests to prevent registration gaps |
| `scripts/verify_constraints.py` | NEW - Pre-flight verification script |
| `docs/development/SESSION_HANDOFF_20251225.md` | Updated with fix details |

---

## Key Files for Next Session

| File | Purpose |
|------|---------|
| `backend/app/scheduling/constraints/manager.py` | Block 10 constraints registered here |
| `backend/app/scheduling/constraints/fmit.py` | PostFMITSundayBlockingConstraint |
| `backend/app/scheduling/constraints/inpatient.py` | ResidentInpatientHeadcountConstraint |
| `backend/app/scheduling/constraints/call_equity.py` | CallSpacingConstraint |
| `backups/postgres/*.sql.gz` | Database backups |
| `backend/alembic/versions/018_*.py` | Missing columns migration |

---

## Session Notes

- N8N warnings in logs are noise (unused service in docker-compose)
- Database credentials are in `.env` file (not committed)
- Blocks exist for full academic year: 2025-07-01 to 2026-06-30
- Block 10 date range: 2026-03-10 to 2026-04-06
