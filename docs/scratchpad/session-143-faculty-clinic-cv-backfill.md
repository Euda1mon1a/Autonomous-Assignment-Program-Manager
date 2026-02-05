# Session 143: Faculty Clinic Wiring + CV Backfill

**Date:** 2026-02-05
**Branch:** `feat/faculty-clinic-cv`
**PR:** #822 (separate from PR #821 supervision fix)
**Status:** PR created, backup + postmortem pending

---

## What Was Done

### 1. Faculty Clinic Variable Re-Keying (CRITICAL FIX)
- **Bug:** `fac_clinic` used `(int, int)` index keys but `FacultyClinicCapConstraint` expected `(UUID, date, slot)` keys
- **Effect:** Faculty C assignments were silently **zero** — constraint appeared active but added 0 solver constraints
- **Fix:** Added `faculty_clinic_by_slot` re-keying in `solvers.py:1017-1028`, wired as `"faculty_clinic"` in variables dict
- **Result:** Faculty C went from **0 to 44** (28 C + 16 CV)

### 2. Soft MIN Clinic Penalty
- **Problem:** Hard MIN constraint caused INFEASIBLE when supervision demand competed
- **Fix:** `CLINIC_MIN_PENALTY = 200` via `shortfall` IntVar in objective function (`solvers.py:1133-1160`)
- **Replaced:** Inline role-based clinic caps → DB-sourced `min_clinic_halfdays_per_week` / `max_clinic_halfdays_per_week`

### 3. CV Backfill (Step 7.6)
- **Location:** `engine.py:_backfill_virtual_clinic()`
- **Logic:** Converts ~30% of clinic (C) to virtual clinic (CV)
- **Priority:** Faculty(100) >> PGY-3(3) > PGY-2(2), no PGY-1
- **Result:** 68/223 clinic slots converted (30% virtual clinic)

### 4. Supporting Changes
- FMIT constraint refactoring
- Inpatient constraint coverage accuracy
- Preload/assignment service enhancements
- Resilience hook false positive fix (burnout grep excluded constraint/ dir)

---

## DB Verification (Block 10, run f668f7f6)

### Faculty Clinic Counts
| Faculty | C | CV | Total | Min | Max | Weekly Avg |
|---------|---|----|-------|-----|-----|------------|
| McRae | 6 | 4 | 10 | 2 | 4 | ~2.5 |
| LaBounty | 6 | 3 | 9 | 2 | 4 | ~2.25 |
| Chu | 5 | 3 | 8 | 2 | 4 | ~2.0 |
| Kinkennon | 5 | 3 | 8 | 2 | 4 | ~2.0 |
| Dahl | 2 | 1 | 3 | 1 | 2 | ~0.75 |
| McGuire | 2 | 1 | 3 | 1 | 1 | 1/wk exact |
| Montgomery | 2 | 1 | 3 | 1 | 2 | ~0.75 |
| Tagawa | 0 | 0 | 0 | 0 | 0 | correct |
| Bevis | 0 | 0 | 0 | 0 | 0 | correct |
| Colgan | 0 | 0 | 0 | 2 | 4 | on leave |

### CV Distribution
- Faculty: 16 CV / 44 total = 36%
- Resident: 56 CV / 214 total = 26%
- Overall: 72 CV / 258 total = 28% (target 30%)
- PGY-1: 0 CV (correct), PGY-2: 40 CV, PGY-3: 16 CV

### Supervision
- All 31 clinic slots have AT faculty (2-6 per slot)
- McGuire: exactly 1 clinic/week across 3 weeks (respects max=1)

### Totals
- Residents: 816 half-day assignments / 17 people
- Faculty: 480 half-day assignments / 10 people

---

## Commits on Branch
1. `fa6058ae` - feat: faculty clinic wiring + soft MIN + CV backfill
2. `1238a033` - feat: constraint + service improvements from Block 10 iteration
(Plus 5 inherited commits from `feat/credential-penalty-ramp`)

---

## Pending Items
- [x] Immaculate backup: `/tmp/immaculate_block10_cv_20260205.dump` (2.7MB, SHA256: 651419b8...)
- [ ] Full postmortem doc (blocked by PII hook — names need anonymization)
- [ ] Schema drift report commit (same PII concern)
- [x] Stash recovery: all 28 lost files recovered from `dea47a14` before GC
- [ ] Commit recovered docs/config/frontend files (next session)

## Stash Recovery Log
- Stash `dea47a14` (WIP on feat/credential-penalty-ramp) was dropped during branch restructuring
- Recovered via `git show dea47a14:<path>` for all 28 files
- Core backend files were committed in PR #822
- Remaining 28 files (docs, config, frontend, .claude) recovered to working tree
- **Must commit before git gc** or they will be permanently lost

---

## Key Lessons
- **ORM attribute names != DB column names:** `clinic_min`/`clinic_max` in DB, but `min_clinic_halfdays_per_week`/`max_clinic_halfdays_per_week` in Person model. `getattr()` must use model-mapped names.
- **Hard MIN constraints cause infeasibility:** When supervision demand competes with clinic MIN, solver goes INFEASIBLE. Always use soft penalties for MIN constraints.
- **Stash recovery via fsck:** Dropped stash can be recovered from `git fsck --unreachable` → `git show <sha>:<path>`.
- **Resilience hook false positive:** Burnout grep matched "workload.*exceed" in ACGME constraint validator messages. Fixed by excluding `constraints/` dir.
