# Session 060 - Immaculate Rebuild & GUI Audit

**Date:** 2026-01-06
**Duration:** ~1 hour
**Outcome:** Test environment rebuilt, 16 GUI bugs documented

---

## The Story

Started with a request to remove "priorities" from RAG (it's for institutional knowledge, not todos). Pivoted to a full immaculate rebuild when it became clear the test environment needed fresh seed data including call assignments and import history for GUI testing.

### What Worked
- Enhanced seed script now generates 365 days of ALL data types:
  - 15,175 assignments
  - 231 call assignments (overnight, weekend, backup rotation)
  - 7 import batches (applied, staged, rejected statuses)
  - 45 residents, 10 faculty, 14 rotation templates
- Created `rebuild-immaculate-testdata.sh` to automate future rebuilds
- Backup system worked flawlessly

### What We Found
Ran GUI audit with human tester + Gemini Flash. Found 16 issues across the frontend:

**The Big Three (P0):**
1. Conflicts page returns 404 but dashboard shows 42 violations - endpoint mismatch
2. Swap Marketplace tells admin "no permission" - RBAC bug
3. Block dates are wrong - the infamous "Block 0 fudge factor" has regressed AGAIN

**Data Display Issues:**
- Month view only shows 2 days of data
- Week view only shows Monday/Tuesday
- Call roster completely empty despite 231 seeded records
- Import batch table missing from UI entirely

### Technical Notes

**Enum Hell:** PostgreSQL enums are lowercase (`applied`, `staged`) but SQLAlchemy's Enum type converts to uppercase names (`APPLIED`, `STAGED`). Fixed with raw SQL using `CAST(:value AS enumtype)` syntax.

**The Fudge Factor:** Block 0 date calculation keeps breaking. This is at least the third time it's regressed. Need to add a test that catches this before it ships.

---

## For Future Sessions

### If Fixing GUI Bugs
Start with the Conflicts API - it's probably just a wrong route path. Check:
- `backend/app/api/routes/` for conflicts endpoint
- `frontend/src/` for the API call URL

### If Block Dates Wrong Again
The calculation lives somewhere in:
- Seed script block generation
- Backend scheduling logic
- Frontend display formatting

Look for anything that handles "Block 0" or academic year start date (July 1).

### Test Environment
Backup `immaculate_testdata_20260106` has everything. Restore with:
```bash
./scripts/stack-backup.sh restore immaculate_testdata_20260106
```

---

## Artifacts

| File | Purpose |
|------|---------|
| `GUI_BUG_REPORT_20260106.md` | Full prioritized bug list |
| `SESSION_060_HANDOFF.md` | Technical handoff notes |
| `seed_antigravity.py` | Enhanced with call + import |
| `rebuild-immaculate-testdata.sh` | Rebuild automation |

---

*"The best time to find bugs is before users do. The second best time is during a systematic audit."*
