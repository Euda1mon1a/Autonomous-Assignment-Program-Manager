# Session 124: Codex IDE Fixes for Half-Day Mode

> **Date:** 2026-01-21
> **Branch:** `feature/activity-assignment-session-119`
> **PR:** #760
> **Latest Commit:** `c614d3cf`

---

## Mission

Address Codex IDE findings for faculty expansion service, engine, and debugger.

## Codex Findings Addressed

### Round 1 Fixes (commit `0f0177aa`)

| Priority | Finding | Fix |
|----------|---------|-----|
| HIGH | Adjunct filter drops NULL faculty_role | Added `OR faculty_role IS NULL` condition |
| HIGH | Faculty expansion runs in draft mode | Added `and not create_draft` guard |
| MEDIUM | SM admin_type → missing activity | Map SM → `sm_clinic` activity code |
| MEDIUM | Deployment detection incomplete | Include tdy/training/military_duty |
| MEDIUM | Debugger hardcodes localhost | Use `NEXT_PUBLIC_API_URL` env var |
| MEDIUM | Debugger block selector not year-aware | Use `selectedBlockKey` with academicYear |

### Round 2 Fixes (commit `cf8ddf37`)

| Priority | Finding | Fix |
|----------|---------|-----|
| HIGH | Holiday handling uses missing Holiday model | Derive from `Block.is_holiday` and `operational_intent` |
| HIGH | Activity solver overwrites faculty placeholders | Filter `Person.type != 'faculty'` in `_load_unlocked_slots` |
| MEDIUM | Debugger `selectedBlock` undefined | Fix reference to `selectedBlockKey` |

### Round 3 Fixes (commit `c614d3cf`)

| Priority | Finding | Fix |
|----------|---------|-----|
| MEDIUM | Call assignments empty in half-day mode | Run greedy solver for Sun-Thu call equity |

### Round 4 Fixes (Session 125)

| Priority | Finding | Fix |
|----------|---------|-----|
| HIGH | Draft mode mutates live CallAssignment | Added `if not create_draft` guard at engine.py:500 |
| HIGH | Call preload/solver divergence (PCAT/DO stale) | Added `_sync_call_pcat_do_to_half_day()` after step 6.5 |
| MEDIUM | Holiday detection per-date (not per-slot) | Changed to `(date, time_of_day)` tuples in faculty_expansion |

**Key Insight:** Preloads run BEFORE solver generates new call assignments. This caused PCAT/DO in half_day_assignments to be based on OLD CallAssignment records while the solver created NEW ones. Fixed by adding a sync step after call generation.

## Key Design Decisions

### Two CP-SAT Solvers
- **`CPSATSolver`** (solvers.py) - Legacy rotation-level solver
- **`CPSATActivitySolver`** (activity_solver.py) - Half-day activity solver

### Half-Day Mode Pipeline
```
1. BlockAssignmentExpansionService → HalfDayAssignment (residents)
2. SyncPreloadService → Lock FMIT/call/absences (PCAT/DO from OLD call)
3. FacultyAssignmentExpansionService → HalfDayAssignment (faculty admin time)
4. CPSATActivitySolver → Assign C/LEC/ADV to unlocked resident slots
5. GreedySolver (call only) → Sun-Thu call equity → CallAssignment records
6. _sync_call_pcat_do_to_half_day → Update PCAT/DO to match NEW call
```

### Call Assignment Sources
| Call Type | Source |
|-----------|--------|
| FMIT Fri/Sat | Preloads (`_load_fmit_call`) |
| Sun-Thu | Greedy solver (equity algorithm) |

### Faculty vs Resident Slots
- **Residents:** Activity solver assigns C, LEC, ADV
- **Faculty:** FacultyExpansion assigns GME/DFM/sm_clinic (solver excluded)

## Files Modified

### Backend
- `backend/app/services/faculty_assignment_expansion_service.py`
  - NULL faculty_role handling
  - SM → sm_clinic mapping
  - Holiday from Block table
  - Deployment type expansion

- `backend/app/scheduling/engine.py`
  - Draft mode guards
  - Greedy solver for call in half-day mode

- `backend/app/scheduling/activity_solver.py`
  - Exclude faculty from solver scope

### Frontend
- `frontend/src/app/admin/debugger/page.tsx`
  - Year-aware block selector
  - Configurable API base URL

## Verification Commands

```bash
# Run Block 10 generation
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Content-Type: application/json" \
  -d '{"block_number": 10, "academic_year": 2025, "expand_block_assignments": true}'

# Check faculty assignments
docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler -c \
  "SELECT p.name, a.code, COUNT(*)
   FROM half_day_assignments hda
   JOIN people p ON hda.person_id = p.id
   JOIN activities a ON hda.activity_id = a.id
   WHERE p.type = 'faculty'
   GROUP BY p.name, a.code
   ORDER BY p.name, a.code;"

# Check call assignments generated
docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler -c \
  "SELECT p.name, ca.date, ca.call_type
   FROM call_assignments ca
   JOIN people p ON ca.faculty_id = p.id
   ORDER BY ca.date;"
```

## Open Items

- [ ] Run Block 10 generation to verify all fixes
- [ ] Audit generated schedule against ROSETTA expectations
- [ ] MCP 401 issue (Codex client not sending auth header)

---

*Session 124 - Codex IDE fixes for half-day mode*
