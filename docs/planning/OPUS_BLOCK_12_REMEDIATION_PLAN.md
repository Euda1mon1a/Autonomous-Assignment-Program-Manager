# Block 12 Remediation Plan (Solver & Preloader Data Starvation)

**Context:** ~~The Block 12 export is rendering correctly, but the data is incomplete.~~ **RESOLVED.** DB verification (Feb 27, PG17) confirms all 16 residents and all 14 faculty have 56 HDAs each. Data generation is complete. Remaining work is **quality** refinement (weekend work, activity diversity) via constraint re-enablement.

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
- 14 faculty × 56 HDAs
- Adjunct faculty not yet in DB (`20260227_add_adjunct` migration unapplied)

---

## Phase 4: Quality Refinement (NEW — Post-Generation)

**Status:** Data exists but has quality issues revealed by spatial analysis.

### 1. Faculty Weekend Work — `NOT DONE` (HIGH)
*   **Issue:** 12/14 faculty have 16 non-W weekend HDAs (100% of weekends). `WeekendWork` constraint is disabled.
*   **Fix:** Re-enable `WeekendWork` in P1 constraint batch (see roadmap section 11j).

### 2. Faculty Activity Diversity — `NEEDS REVIEW`
*   **Issue:** Some faculty may have generic all-GME/AT schedules vs. template-driven variety.
*   **Validation:** Use `schedule_grid` view to check `COUNT(DISTINCT activity_code)` per faculty.

### 3. Orphaned Activity UUID — `NOT DONE` (LOW)
*   **Issue:** 8 `faculty_weekly_templates` rows reference activity UUID `9fd0dca9-f260-478d-80b1-c9ea5d78b6d0` which does not exist in `activities` table.
*   **Fix:** Either insert the missing activity or update the template rows to reference the correct activity.

### 4. Apply Adjunct Migration — `NOT DONE` (MEDIUM)
*   **Issue:** `20260227_add_adjunct_role.py` exists but DB head is `9bcfa50205e4`. Adjunct faculty need to be classified.
*   **Fix:** Run `alembic upgrade head` after verifying migration chain.

---

### Important Context Discovered During Exploration

*   **Preloader over Solver:** The `constants.py` mappings and `rotation_codes.py` handlers now cover ALL Block 12 rotations. The preloader is deterministic; the solver is easily broken by vacation overlap. NF-combined, FMIT, PEDW, LDNF, NF all have working handlers.
*   **Engine vs Faculty Templates:** The solver's engine dynamically falls back to generating generic HDAs if a faculty member has no `faculty_weekly_templates`. The engine uses `person.faculty_role` heavily (e.g. `'adjunct'`). Adjunct exclusion is now implemented (Phase 2.1 DONE).
*   **Soft vs Hard Constraints:** In `rotation_activity_requirements`, `min_halfdays` acts as a HARD constraint. If a resident takes vacation, a high `min_halfdays` will result in `INFEASIBLE`. Keep `min_halfdays` at `0` and use `target_halfdays` with a high `priority`.
*   **32 of 48 constraints disabled:** All policy hard constraints are disabled in `ConstraintManager.create_default()` to prevent INFEASIBLE. See `BLOCK_12_ANNUAL_WORKBOOK_ROADMAP.md` section 11j for the P1-P5 re-enablement plan.
