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

### 2. Faculty Activity Diversity — `PARTIALLY FIXED` (HIGH)
*   **Issue:** Solver activity model too coarse. 4 types (C, AT, PCAT, DO) → write-back maps C→fm_clinic, AT→at generically. Templates have ~15 specific activity types (CV, sm_clinic, SIM, dfm, etc.) that are ignored.
*   **Root cause:** `FacultyWeeklyTemplateConstraint` not registered in `manager.py`. Even if registered, constraint's `add_to_cpsat()` expects `faculty_activities[f_i, b_i, tod, a_i]` variable structure that doesn't exist — solver uses separate `fac_clinic[f_i, b_i]` / `fac_supervise[f_i, b_i]` dicts.
*   **Fix (two-part):**
    1. **Write-back (DONE)**: `_persist_faculty_half_day_from_solver()` now template-aware — loads `faculty_weekly_templates` using **Python weekday convention (0=Mon)**. Resolves solver C→template-specific clinic code (CV, sm_clinic, dfm), solver AT→template-specific admin code (gme, lec, SIM). 103 HDAs updated (56 Friday restorations + 47 within-category refinements).
    2. **Solver (DEFERRED)**: Cross-category mismatches (solver says C but template wants AT, or vice versa) ~100 violations. ~27 are FMIT rotation overrides (expected — FMIT assignment trumps weekly template). Requires FacultyWeeklyTemplateConstraint integration as soft preference.

### 3. Orphaned Activity UUID — `FIXED`
*   **Issue:** ~~8 rows~~ 5 `faculty_weekly_templates` rows referenced wrong FMIT UUID `9fd0dca9-...`.
*   **Fix:** Updated to correct FMIT UUID `bd9c66b3-ad3c-2d6d-1a3d-1fa7bc8960a9`.

### 4. Apply Adjunct Migration — `DEFERRED`
*   **Decision:** Adjuncts deferred until core scheduling locked in. Removed non-essential faculty from DB.

### 5. Zeroing Validation — `IN PROGRESS`
*   **Approach:** Export DB grid → compare against coordinator's Excel cell-by-cell → isolate DB (solver) vs export (XLSX) issues.
*   **Export:** `/tmp/Block12_Schedule_Grid_Zeroing.xlsx` (3 sheets: Raw Codes, Numeric Codes 1-9, Legend)
*   **Tool:** Claude for Excel compares numeric grid against coordinator workbook.
*   **See:** `docs/planning/SCHEDULE_GRID_ZEROING_PLAN.md` for full methodology.

---

### Important Context Discovered During Exploration

*   **Preloader over Solver:** The `constants.py` mappings and `rotation_codes.py` handlers now cover ALL Block 12 rotations. The preloader is deterministic; the solver is easily broken by vacation overlap. NF-combined, FMIT, PEDW, LDNF, NF all have working handlers.
*   **Engine vs Faculty Templates:** The solver's engine dynamically falls back to generating generic HDAs if a faculty member has no `faculty_weekly_templates`. The engine uses `person.faculty_role` heavily (e.g. `'adjunct'`). Adjunct exclusion is now implemented (Phase 2.1 DONE).
*   **Soft vs Hard Constraints:** In `rotation_activity_requirements`, `min_halfdays` acts as a HARD constraint. If a resident takes vacation, a high `min_halfdays` will result in `INFEASIBLE`. Keep `min_halfdays` at `0` and use `target_halfdays` with a high `priority`.
*   **32 of 48 constraints disabled:** All policy hard constraints are disabled in `ConstraintManager.create_default()` to prevent INFEASIBLE. See `BLOCK_12_ANNUAL_WORKBOOK_ROADMAP.md` section 11j for the P1-P5 re-enablement plan.
*   **Solver activity model architecture (`solvers.py:968-1073`):** Faculty half-day decisions use 4 binary variables per slot: `fac_clinic`, `fac_supervise`, `fac_pcat`, `fac_do`. At most one active per slot (mutual exclusion constraint). Clinic/supervise only on workdays; PCAT/DO linked bidirectionally to overnight call assignments. Write-back in `engine.py:3370` maps C→activity code via `_get_activity_id_by_code()`. The `variables` dict exposes both index-keyed (`fac_clinic[f_i, b_i]`) and UUID-keyed (`faculty_clinic[(uuid, date, tod)]`) views for constraint wiring.
*   **Faculty fill around residents:** Faculty clinic slots (`fac_clinic`) are constrained by supervision ratio (ACGME: 1 faculty per 2 PGY-1 or 4 PGY-2/3 in clinic) and weekly clinic limits (`min_clinic_halfdays_per_week`, `max_clinic_halfdays_per_week` from Person model). Faculty MUST be solver-generated, not preloaded.
