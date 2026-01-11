# Session 2026-01-11: MEDCOM Day-Type System

## Summary

Expanding holiday support to full MEDCOM day-type system (PR #690 → PR #691).

---

## Completed

### PRs Merged
- **PR #688** - Resident 56-slot expansion ✓
- **PR #689** - Faculty 56-slot expansion ✓
- **PR #690** - Basic holiday support (HOL-AM/HOL-PM) ✓

---

## Current Work: MEDCOM Day-Type System

### Branch: `feature/holiday-support` (continuing)

### Codex P2 Fix
- Fixed holidays need OPM observed dates
- July 4, 2026 (Saturday) → observe Friday July 3
- Missing: Juneteenth (June 19)

### New Requirements
| Day Type | Meaning | Default Intent |
|----------|---------|---------------|
| FEDERAL_HOLIDAY | OPM holiday | REDUCED_CAPACITY |
| TRAINING_HOLIDAY | DONSA | NON_OPERATIONAL |
| MINIMAL_MANNING | Reduced staffing | REDUCED_CAPACITY |
| EO_CLOSURE | Presidential order | NON_OPERATIONAL |

### Operational Intent
- NON_OPERATIONAL: 0.0 capacity
- REDUCED_CAPACITY: 0.25 capacity
- NORMAL: 1.0 capacity

### Implementation Status
1. 🔲 Phase 1: Fix holidays.py (observed dates + Juneteenth) - IN PROGRESS
2. 🔲 Phase 2: Create DayType/OperationalIntent enums
3. 🔲 Phase 3: Database migration
4. 🔲 Phase 4: Update Block model
5. 🔲 Phase 5: Update expansion services

---

## Key Design Decisions

### Holiday Behavior (USER CONFIRMED)
- **Inpatient (FMIT, NF):** Get REGULAR assignments on holidays (they provide coverage)
- **All other rotations:** Get HOL-AM/HOL-PM placeholder assignments
- **1-in-7 rule:** Holidays PAUSE counter (like absences), don't reset

### Implementation
- Use `rotation.includes_weekend_work` as proxy - rotations that work weekends also work holidays
- 10 federal holidays (OPM standard): 4 fixed + 6 floating

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/app/utils/holidays.py` | Holiday calendar utility |
| `backend/app/services/block_assignment_expansion_service.py` | Resident 56-slot expansion |
| `backend/app/services/faculty_assignment_expansion_service.py` | Faculty 56-slot expansion |
| `scripts/generate_blocks.py` | Block generation with holidays |

---

## Next Steps

1. Lint and test resident expansion service
2. Update faculty expansion service
3. Create backfill script
4. Commit all changes
5. Create PR #690
