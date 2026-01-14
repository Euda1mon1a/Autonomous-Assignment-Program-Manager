# Session 103: DB Alignment + Skill Refinement

> **Date:** 2026-01-14
> **Status:** COMPLETE ✓
> **Context:** 11%

## Phase 1-5: DB Alignment (COMPLETE)

All phases from original mission complete:
- Skill updated to v1.3
- DB constraints added (11 columns + sm_min/sm_max)
- Code refactored to read from DB
- Adjuncts identified by faculty_role, not name lookup

## Phase 6: SM Constraints (COMPLETE)

- Added `sm_min`/`sm_max` columns (Tagawa: 2-4)
- Added Wednesday AM → aSM preload for SM faculty
- aSM = Academic Sports Medicine (non-clinical: ultrasound training, didactics)
- SM pairing rule documented: resident SM requires Tagawa SM

## Phase 7: Skill Refinement (COMPLETE)

### Order of Operations (Canonical)
1. Preload non-negotiables (FMIT, absences, holidays, FMIT Fri/Sat call)
2. Assign Sun-Thu call (min-gap decay, auto-generates PCAT baseline)
3. Solve outpatient (residents) - solver applies rotation patterns
4. Calculate supervision demand (resident C creates demand)
5. Assign faculty AT (to meet supervision demand)
6. Assign faculty C (personal clinic, counts toward physical capacity)
7. Fill admin time (GME/DFM/SM)

### Critical Distinctions Documented

**C vs AT:**
| Activity | Definition | Physical Capacity | AT Coverage |
|----------|------------|-------------------|-------------|
| Resident C | Resident seeing patients | Counts (max 6) | Creates demand |
| Faculty C | Faculty seeing OWN patients | Counts (max 6) | None |
| Faculty AT | Faculty supervising residents | Does NOT count | Provides |
| PCAT | Post Call Attending Time | Does NOT count | Provides (= AT) |
| DO | Direct Observation | - | Auto-assigned after call |

**PROC/VAS:** +1.0 AT demand (dedicated 1:1 supervision)

**SM:** Closed loop - does NOT use AT resources, Tagawa's SM does NOT provide AT

### Code Corrections
- PCAT = Post Call **Attending** Time (not Admin)
- DO = Direct Observation (not Day Off)

## Files Modified This Session

**Migrations:**
- `20260114_faculty_constraints.py` - 11 constraint columns
- `20260114_sm_constraints.py` - sm_min/sm_max

**Models:**
- `backend/app/models/person.py` - 13 new columns total

**Services:**
- `backend/app/services/faculty_assignment_expansion_service.py` - reads constraints from DB, aSM preload

**Skills:**
- `.claude/skills/tamc-excel-scheduling/SKILL.md` - v1.3, order of operations, C vs AT
- `.claude/skills/tamc-excel-scheduling/references/faculty-roster.md` - SM constraints, aSM definition

**Tests:**
- `backend/tests/services/test_faculty_assignment_expansion_service.py` - mock new columns

## Resume Instructions

Session complete. If continuing this work:
1. Solver integration for order of operations
2. Call assignment with min-gap decay
3. Physical capacity constraint (max 6) enforcement
