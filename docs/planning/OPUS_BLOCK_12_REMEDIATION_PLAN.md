# Block 12 Remediation Plan (Solver & Preloader Data Starvation)

**Context:** The Block 12 export is rendering correctly, but the data is incomplete. The CP-SAT solver and preloader are failing to generate complete schedules for 12 of the 16 residents and 4 core faculty due to missing database constraints and preloader logic gaps.

**Goal:** Fix the upstream data requirements so the solver can successfully generate a complete 56-slot schedule for every active resident and core faculty member, while explicitly excluding adjuncts.

**Source:** Gemini CLI exploration (Feb 27, 2026). Corrections noted inline.

**Verified Status (Feb 27, 2026):** See `BLOCK_12_ANNUAL_WORKBOOK_ROADMAP.md` → "Remediation Status" section for authoritative status.

---

## Phase 1: Database Corrections (The Data Layer)

The solver is mathematically skipping residents because their `rotation_templates` have zero or broken `rotation_activity_requirements`.

### 1. Fix the NBN Broken Constraint — `NOT DONE`
*   **Target:** PGY-1 resident on NBN rotation
*   **Issue:** NBN has a broken constraint where `min=31` is greater than `max=28` (or similar paradoxes). The solver ignores the rotation or fails as INFEASIBLE.
*   **Action:** Create a SQL update (or Alembic migration) to update the `rotation_activity_requirements` table for the NBN template.
    *   *Fix:* Set `min_halfdays` to a valid number (e.g., `20`) that is less than or equal to `max_halfdays`.
*   **Correction:** NBN is inpatient (preloader-handled), so this is a data quality fix, not the root cause of coverage gaps.

### 2. Hydrate Rotation Requirements — `UNNECESSARY`
*   **Targets:** FMIT-PGY3, NF-combined rotations, PEDS.
*   **Issue:** These templates have 0, 1, or 2 requirements in the database.
*   **Action:** Insert rows into `rotation_activity_requirements`.
    *   *Crucial Warning:* When inserting new constraints, **keep `min_halfdays` very conservative (e.g. 0 or 10) and rely on `target_halfdays` and `priority` (e.g., 80) to guide the solver.** Setting a hard `min_halfdays=20` will instantly break the solver (INFEASIBLE) if a resident has a week of vacation.
*   **Correction:** NF-combined residents are preloader-handled, not solver-handled. All mappings already exist in `constants.py` and `canonical_rotation_code()`. Re-running the preloader (which now has all handlers) is the fix — not adding rotation_activity_requirements. Migration `20260224` created NF combo reqs, then `20260225` correctly removed them.

### 3. Hydrate Core Faculty Templates — `NOT DONE (PARTIAL)`
*   **Targets:** 4 core faculty without weekly templates.
*   **Issue:** These faculty lack `faculty_weekly_templates` rows. The solver defaults them to generic `GME` + `AT`.
*   **Action:** Insert default baseline templates.
*   **Status:** Model + API + coverage report exist. No seed data inserted yet.

---

## Phase 2: Logic Refinements (Preloader & Engine)

### 1. Explicitly Exclude Adjuncts from Solver — `DONE`
*   **Issue:** Adjuncts are getting solver-generated HDAs (GME/AT) instead of remaining completely blank for hand-jamming.
*   **Status:** Implemented at 3 filter points: `engine.py:949-951` (call eligibility), `engine.py:3306-3354` (HDA write-back skip), `activity_solver.py:1099,3442-3476` (template handling).

### 2. Update `constants.py` NF-Combined Mappings — `UNNECESSARY`
*   **Issue:** The preloader uses `NF_COMBINED_ACTIVITY_MAP` in `backend/app/services/preload/constants.py` to translate split rotations.
*   **Correction:** All mappings already exist: NF-LD→LDNF, NF-PEDS-PG→PEDNF, FMIT-PGY*→FMIT, PEDS-WARD*→PEDW. See `constants.py` and `canonical_rotation_code()`. The preloader has had all handlers since the rotation_codes.py updates.

### 3. Refine Preloader Primary Codes — `UNNECESSARY`
*   **Issue:** Some non-split inpatient rotations like `PEDS-WARD-` might also need explicit weekend handling.
*   **Correction:** PEDW handler exists at `rotation_codes.py:280-287`. All Block 12 rotation codes are handled.

---

## Phase 3: Execution & Regeneration — `NOT DONE`

**Status:** Pipeline infrastructure is complete (preloader, solver, export all verified working). Blocked on Phase 1.1 (NBN fix) and Phase 1.3 (faculty template seed).

Once remaining fixes are complete, execute a clean run:

1.  **Backup** (MANDATORY):
    ```python
    mcp__residency-scheduler__create_backup_tool(reason="Pre-Block 12 fresh solve")
    ```
2.  **Purge Bad Data:**
    ```sql
    DELETE FROM half_day_assignments
    WHERE date >= '2026-05-07' AND date <= '2026-06-03';
    ```
3.  **Run Preloader:**
    ```python
    svc.load_all_preloads(block_number=12, academic_year=2025)
    ```
4.  **Run Solver:**
    ```python
    engine.generate(block_number=12, academic_year=2025, algorithm="cp_sat")
    ```
5.  **Re-Export Workbook:**
    ```python
    export_svc.export_year_xlsx(academic_year=2025, output_path="/tmp/AY2025_Master_Schedule.xlsx")
    ```
6.  **Verify:** Confirm 56 HDAs for all 16 residents, proper schedules for 14 core faculty, and 0 HDAs for the 3 adjunct faculty.

**See:** `BLOCK_12_ANNUAL_WORKBOOK_ROADMAP.md` Steps 0-8 for the full detailed pipeline.

---

### Important Context Discovered During Exploration

*   **Preloader over Solver:** The `constants.py` mappings and `rotation_codes.py` handlers now cover ALL Block 12 rotations. The preloader is deterministic; the solver is easily broken by vacation overlap. NF-combined, FMIT, PEDW, LDNF, NF all have working handlers.
*   **Engine vs Faculty Templates:** The solver's engine dynamically falls back to generating generic HDAs if a faculty member has no `faculty_weekly_templates`. The engine uses `person.faculty_role` heavily (e.g. `'adjunct'`). Adjunct exclusion is now implemented (Phase 2.1 DONE).
*   **Alembic vs Raw SQL:** Since constraints like `min_halfdays=31` vs `max_halfdays=28` on `NBN` are data issues, an Alembic data migration is preferred over manual `psql` to ensure the fix propagates across all environments deterministically.
*   **Soft vs Hard Constraints:** In `rotation_activity_requirements`, `min_halfdays` acts as a HARD constraint. If a resident takes vacation, a high `min_halfdays` will result in `INFEASIBLE`. Keep `min_halfdays` at `0` and use `target_halfdays` with a high `priority`.
*   **32 of 48 constraints disabled:** All policy hard constraints are disabled in `ConstraintManager.create_default()` to prevent INFEASIBLE. See `BLOCK_12_ANNUAL_WORKBOOK_ROADMAP.md` section 11j for the P1-P5 re-enablement plan.
