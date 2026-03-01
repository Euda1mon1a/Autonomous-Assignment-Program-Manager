# Block 12 Remediation Plan (Solver & Preloader Data Starvation)

**Context:** ~~The Block 12 export is rendering correctly, but the data is incomplete.~~ **RESOLVED.** DB verification (Feb 27, PG17) confirms all 16 residents and 10 core faculty have 56 HDAs each. Data generation is complete. Remaining work is **quality** refinement via zeroing (DB↔Excel alignment) and solver constraint integration.

**Goal:** ~~Fix the upstream data requirements so the solver can successfully generate a complete 56-slot schedule for every active resident and core faculty member, while explicitly excluding adjuncts.~~ **ACHIEVED.** Focus shifts to quality: re-enable disabled constraints iteratively.

**Source:** Gemini CLI exploration (Feb 27, 2026). Corrections noted inline.

**Verified Status (Feb 27, 2026):** See `BLOCK_12_ANNUAL_WORKBOOK_ROADMAP.md` → "Remediation Status" section for authoritative status.

---

## Phase 1: Database Corrections (The Data Layer) — `COMPLETE`

### 1. Fix the NBN Broken Constraint — `NON-ISSUE`
*   **Target:** PGY-1 resident on NBN rotation
*   **Issue:** NBN was reported to have `min=31 > max=28`. **DB query confirms this does not exist.** All 7 NBN rows have `min=0, max=40`.
*   **Action:** None needed.

### 2. Hydrate Rotation Requirements — `UNNECESSARY`
*   **Targets:** FMIT-PGY3, NF-combined rotations, PEDS.
*   **Correction:** NF-combined residents are preloader-handled, not solver-handled. All mappings already exist in `constants.py` and `canonical_rotation_code()`.

### 3. Hydrate Core Faculty Templates — `NON-ISSUE`
*   **Targets:** ~~4 core faculty without weekly templates.~~
*   **DB-verified:** 13 of 14 faculty have 14 templates each. Only Kate Bohringer has 0 — she is not a Block 12 participant (removed from scope). Derrick Thiel does not exist in the `people` table (removed from scope).

---

## Phase 2: Logic Refinements (Preloader & Engine) — `COMPLETE`

### 1. Explicitly Exclude Adjuncts from Solver — `DONE`
*   **Status:** Implemented at 3 filter points: `engine.py:949-951` (call eligibility), `engine.py:3306-3354` (HDA write-back skip), `activity_solver.py:1099,3442-3476` (template handling).

### 2. Update `constants.py` NF-Combined Mappings — `UNNECESSARY`
*   **Correction:** All mappings already exist.

### 3. Refine Preloader Primary Codes — `UNNECESSARY`
*   **Correction:** All handlers exist.

---

## Phase 3: Execution & Regeneration — `COMPLETE`

**Status:** Pipeline ran successfully. DB contains complete Block 12 data:
- 16 residents × 56 HDAs (13 fully preloaded, 3 with solver fills)
- 10 core faculty × 56 HDAs (reduced from 14: removed 4 non-core faculty with 0 templates or near-all-GME)
- Adjuncts deferred until core functionality locked in

---

## Phase 4: Quality Refinement (NEW — Post-Generation)

**Status:** Data exists but has quality issues revealed by spatial analysis.

### 1. Faculty Weekend Work — `FIXED` (HIGH)
*   **Issue:** Faculty working Sat/Sun. Root cause: `CPSATActivitySolver` in `activity_solver.py` overwrote weekend "OFF" codes with clinical activities when `include_faculty_slots=True`. No weekend exclusion filter existed for faculty slots.
*   **Fix:** Added faculty weekend exclusion filter in `activity_solver.py` (~line 394) that skips faculty slots on Sat+Sun (`weekday() >= 5`). Standard civilian weekend convention (Sat+Sun). Engine `is_weekend` flag unchanged.
*   **DOW Convention Clarification:** `FacultyWeeklyTemplate.day_of_week` uses **Python weekday (0=Mon, 6=Sun)** despite model docstring claiming PG DOW (0=Sun). All consuming code (`call_equity.py:877`, `activity_solver.py:1019`) uses Python convention. Docstring is incorrect — data is correct.
*   **Result:** Weekend violations reduced from 60 → 0

### 2. Faculty Activity Diversity — `FIXED + VERIFIED` (HIGH)
*   **Issue:** Solver activity model too coarse. 4 types (C, AT, PCAT, DO) → write-back maps C→fm_clinic, AT→at generically. Templates have ~15 specific activity types (CV, sm_clinic, SIM, dfm, etc.) that are ignored.
*   **Root cause (original):** `FacultyWeeklyTemplateConstraint` not registered in `manager.py`. Even if registered, constraint's `add_to_cpsat()` expects `faculty_activities[f_i, b_i, tod, a_i]` variable structure that doesn't exist — solver uses separate `fac_clinic[f_i, b_i]` / `fac_supervise[f_i, b_i]` dicts.
*   **Root cause (dual-write bug, Mar 1):** Step 6.1 (`_persist_faculty_half_day_from_solver`) correctly resolves templates, but Step 6.7 (`CPSATActivitySolver.solve()`) with `ACTIVITY_SOLVER_INCLUDE_FACULTY=true` (default) re-processes faculty slots, **overwriting** template-resolved codes with coarse C/AT.
*   **Fix (three-part):**
    1. **Write-back (DONE)**: `_persist_faculty_half_day_from_solver()` now template-aware — loads `faculty_weekly_templates` using **Python weekday convention (0=Mon)**. Resolves solver C→template-specific clinic code (CV, sm_clinic, dfm), solver AT→template-specific admin code (gme, lec, SIM).
    2. **Activity solver exclusion (DONE, Mar 1)**: Changed `ACTIVITY_SOLVER_INCLUDE_FACULTY` default from `"true"` to `"false"` in `engine.py:665-667`. Faculty HDAs from Step 6.1 are no longer overwritten by Step 6.7.
    3. **Template correction sweep (DONE, Mar 1)**: New `_apply_faculty_template_correction()` as Step 7.5b — safety-net sweep corrects any remaining solver-source HDAs to match templates. 77 HDAs corrected on Block 12 regen.
*   **Tests:** 12 unit tests in `tests/scheduling/test_faculty_template_correction.py` — all passing.
*   **Result:** Template mismatches 186 → 0 true mismatches. Remaining 25 are expected (21 FMIT rotation overrides + 4 CV↔fm_clinic virtual clinic conversions).

### 3. Orphaned Activity UUID — `FIXED`
*   **Issue:** ~~8 rows~~ 5 `faculty_weekly_templates` rows referenced wrong FMIT UUID `9fd0dca9-...`.
*   **Fix:** Updated to correct FMIT UUID `bd9c66b3-ad3c-2d6d-1a3d-1fa7bc8960a9`.

### 4. Apply Adjunct Migration — `DEFERRED`
*   **Decision:** Adjuncts deferred until core scheduling locked in. Removed non-essential faculty from DB.

### 5. Wednesday PM LEC Conflict — `FIXED + VERIFIED` (HIGH)
*   **Issue:** Solver schedules faculty into clinic (C/CV/SM) on Wednesday PMs when residents have LEC (protected didactic time). Discovered via Claude for Excel visual verification.
*   **Scope (pre-fix):** Wk1: 5 faculty in clinic, Wk2: 4, Wk3: 2, Wk4: 3. One faculty member in clinic all 4 Wednesday PMs.
*   **Root cause:** No active constraint prevents faculty clinic on Wednesday PM. Three Wednesday constraints exist in `constraints/temporal.py` but ALL disabled. `FacultyWeeklyTemplateConstraint` NOT registered.
*   **Fix:** Preloader-level injection — `_load_faculty_wednesday_pm_lec()` added to `sync_preload_service.py`. Injects LEC for all core faculty on regular Wednesday PMs (day < 22). Skips 4th Wednesdays (inverted schedule) and FMIT faculty. Solver respects `source='preload'` slots (skipped_locked=299 during regeneration).
*   **Tests:** 5 unit tests in `tests/services/test_faculty_wednesday_pm_lec.py` — all passing.
*   **Regeneration (Feb 28):** Block 12 regenerated successfully (8.9s, 306 assignments, OPTIMAL). Wednesday PM clinic violations: 0. Regular Weds: all faculty have LEC. 4th Wed: solver assigns clinic to available faculty (inverted schedule preserved).
*   **Known trade-off:** Post-call DO on Wednesday PM is replaced by LEC. One faculty member's May 12 call → May 13 AM=PCAT (correct) PM=LEC (instead of DO). This is acceptable — faculty attend PCAT AM then LEC PM on Wednesdays.
*   **Verification:** DB 9/10 (Check 9 WARN: 1 call chain where LEC overrides DO on Wed PM — expected), XLSX 8/8 (0 true mismatches).

### 6. CALL Code Tracking Gaps — `FIXED + VERIFIED` (LOW)
*   **Root cause:** `_sync_call_pcat_do_to_half_day()` creates PCAT/DO for day AFTER call but NOT the CALL HDA on the call date itself. The preloader's `_load_faculty_call()` would create CALL HDAs but is skipped during regeneration (`skip_faculty_call=True`).
*   **Fix:** Added `_sync_call_to_half_day()` method in `engine.py` (~75 lines). Creates CALL HDA on call date PM for ALL `call_assignments` in the block date range (new solver-generated + preserved FMIT). CALL overrides all existing sources (preload, solver, template) because solver call_assignments are authoritative.
*   **Pipeline wiring:** Step 6.6a, after `_sync_call_pcat_do_to_half_day()`. Queries ALL `call_assignments` in date range (not just new) to include preserved FMIT Fri/Sat calls.
*   **Tests:** 6 unit tests in `tests/scheduling/test_sync_call_to_half_day.py` — all passing. Covers: new creation, solver overwrite, preload override, skip when already CALL, empty list, multiple calls.
*   **Regeneration (Feb 28):** 15 CALL HDAs synced. Block 12: 9/10 faculty with calls now have CALL HDAs (one faculty excluded — all calls in other blocks). DB 10/10, XLSX 8/8.
*   **Remaining:** 10 "orphaned" CALL HDAs from `resident_call_preloads` (Chief Resident manual entries) without matching `call_assignments`. This is the inherent two-source pattern, not a bug — `resident_call_preloads` is a separate data source from solver `call_assignments`.
*   **Edge cases:** (a) Consecutive-night calls: second call's CALL HDA correctly replaces first's DO. (b) Wed PM: CALL overrides LEC when solver assigns call on Wednesday. (c) One faculty Jun 3 call: cross-block boundary (Jun 4 = Block 13), no PCAT/DO expected.

### 7. Call Distribution — `DEFERRED` (MEDIUM)
*   **Issue:** Distribution is reasonable but not MAD-optimized. Equity shows 1-7 overnight calls across 10 faculty.
*   **Context:** MAD equity (PR #1199) is implemented. Re-generating with the MAD constraint active will improve distribution.
*   **Action:** Regenerate Block 12, verify MAD equity produces better balance.

### 8. Zeroing Validation — `DONE (DB + XLSX + Visual)` — Updated Feb 28 Post-41-Constraint-Regen
*   **DB verification (10-check):** `scripts/scheduling/verify_block12.py` — **10/10 passed**. Check 7 WARN (186 template mismatches, C2 deferral). 24 calls, 23 chains verified (8 with FMIT/leave/weekend override).
*   **Export verification (8-check):** `scripts/scheduling/verify_block12_export.py` — **8/8 passed**. 1456 cells compared, **0 true mismatches**.
*   **Regeneration:** Block 12 regenerated with all 41 constraints enabled. OPTIMAL in 6.0s, 306 assignments. Two pipeline bugs fixed:
    1. **Stale CALL preload blocking PCAT/DO**: When a call date moved between generations, old CALL preloads on the next-day PM blocked DO creation, then got cleaned up by stale CALL cleanup, leaving a validation gap. Fix: `_sync_call_pcat_do_to_half_day` now overwrites CALL-activity preloads with DO.
    2. **Faculty HDA gaps**: Solver left some faculty slots unassigned (all 4 binary variables = 0). Fix: `_backfill_faculty_gaps` fills empty faculty slots with OFF (weekday) or W (weekend).
*   **Cross-block guard (Codex P1, PR #1216):** Stale CALL overwrite scoped to `next_day <= self.end_date` — prevents mutating legitimate CALL preloads belonging to adjacent block's generation.
*   **XLSX versions:** `/tmp/Block12_Export_v4.0_41_Constraints.xlsx` (post-PR #1216, current). User verified: "much closer to reality."
*   **See:** `docs/planning/SCHEDULE_GRID_ZEROING_PLAN.md` for full methodology.

---

### Important Context Discovered During Exploration

*   **Preloader over Solver:** The `constants.py` mappings and `rotation_codes.py` handlers now cover ALL Block 12 rotations. The preloader is deterministic; the solver is easily broken by vacation overlap. NF-combined, FMIT, PEDW, LDNF, NF all have working handlers.
*   **Engine vs Faculty Templates:** The solver's engine dynamically falls back to generating generic HDAs if a faculty member has no `faculty_weekly_templates`. The engine uses `person.faculty_role` heavily (e.g. `'adjunct'`). Adjunct exclusion is now implemented (Phase 2.1 DONE).
*   **Soft vs Hard Constraints:** In `rotation_activity_requirements`, `min_halfdays` acts as a HARD constraint. If a resident takes vacation, a high `min_halfdays` will result in `INFEASIBLE`. Keep `min_halfdays` at `0` and use `target_halfdays` with a high `priority`.
*   **41 of 50 constraints enabled (PR #1215):** 17 of 18 policy-hard constraints re-enabled after stress test (all OPTIMAL). FacultySupervision converted to soft with deficit penalty. Only WednesdayPMSingleFaculty remains disabled (needs solver variable refactor). 9 disabled total (1 policy-hard + 8 optional/tier-2).
*   **Solver activity model architecture (`solvers.py:968-1073`):** Faculty half-day decisions use 4 binary variables per slot: `fac_clinic`, `fac_supervise`, `fac_pcat`, `fac_do`. At most one active per slot (mutual exclusion constraint). Clinic/supervise only on workdays; PCAT/DO linked bidirectionally to overnight call assignments. Write-back in `engine.py:3370` maps C→activity code via `_get_activity_id_by_code()`. The `variables` dict exposes both index-keyed (`fac_clinic[f_i, b_i]`) and UUID-keyed (`faculty_clinic[(uuid, date, tod)]`) views for constraint wiring.
*   **Faculty fill around residents:** Faculty clinic slots (`fac_clinic`) are constrained by supervision ratio (ACGME: 1 faculty per 2 PGY-1 or 4 PGY-2/3 in clinic) and weekly clinic limits (`min_clinic_halfdays_per_week`, `max_clinic_halfdays_per_week` from Person model). Faculty MUST be solver-generated, not preloaded.
