# Block 12 Remediation Plan (Solver & Preloader Data Starvation)

**Context:** The Block 12 export is rendering correctly, but the data is incomplete. The CP-SAT solver and preloader are failing to generate complete schedules for 12 of the 16 residents and 4 core faculty due to missing database constraints and preloader logic gaps.

**Goal:** Fix the upstream data requirements so the solver can successfully generate a complete 56-slot schedule for every active resident and core faculty member, while explicitly excluding adjuncts.

---

## Phase 1: Database Corrections (The Data Layer)

The solver is mathematically skipping residents because their `rotation_templates` have zero or broken `rotation_activity_requirements`.

### 1. Fix the NBN Broken Constraint
*   **Target:** PGY-1 resident on NBN rotation
*   **Issue:** NBN has a broken constraint where `min=31` is greater than `max=28` (or similar paradoxes). The solver ignores the rotation or fails as INFEASIBLE.
*   **Action:** Create a SQL update (or Alembic migration) to update the `rotation_activity_requirements` table for the NBN template.
    *   *Fix:* Set `min_halfdays` to a valid number (e.g., `20`) that is less than or equal to `max_halfdays`.

### 2. Hydrate Rotation Requirements
*   **Targets:** `Mayell` (FMIT-PGY3), NF-combined rotations (`Cataquiz`, `Sawyer`, `Thomas`, `Maher`, `Wilhelm`), and PEDS (`Sloss`).
*   **Issue:** These templates have 0, 1, or 2 requirements in the database. The solver requires explicit targets (e.g., "Schedule 20 L&D shifts") to fill non-NF gaps.
*   **Action:** Insert rows into `rotation_activity_requirements`.
    *   *Crucial Warning:* When inserting new constraints, **keep `min_halfdays` very conservative (e.g. 0 or 10) and rely on `target_halfdays` and `priority` (e.g., 80) to guide the solver.** Setting a hard `min_halfdays=20` will instantly break the solver (INFEASIBLE) if a resident has a week of vacation.

### 3. Hydrate Core Faculty Templates
*   **Targets:** `Van Brunt`, `Thiel`, `Napierala`, `Samblanet`.
*   **Issue:** These 4 core faculty lack `faculty_weekly_templates` rows. The solver defaults them to generic `GME` + `AT`.
*   **Action:** Insert default baseline templates (e.g., matching a standard core faculty profile) into the `faculty_weekly_templates` table for these 4 IDs.

---

## Phase 2: Logic Refinements (Preloader & Engine)

### 1. Explicitly Exclude Adjuncts from Solver
*   **Targets:** `Lamoureux`, `Gomes`.
*   **Issue:** Adjuncts are getting solver-generated HDAs (GME/AT) instead of remaining completely blank for hand-jamming.
*   **Action:** Modify `backend/app/scheduling/engine.py`.
    *   *Fix:* Add a filter: `if person.faculty_role == 'adjunct': continue` early in the `_build_context` phase so that variables are never initialized for them.

### 2. Update `constants.py` NF-Combined Mappings (The Preloader Blindspot)
*   **Issue:** The preloader uses `NF_COMBINED_ACTIVITY_MAP` in `backend/app/services/preload/constants.py` to translate split rotations. *If a new rotation like `NF-LD` or `NF-PEDS-PG` isn't in this dictionary, the preloader literally cannot map the daytime half and skips it.* This is why several residents lost their daytime clinics.
*   **Action:** Add the missing Block 12 mappings directly to `constants.py`:
    *   `"NF-LD": "LDNF"` (or whatever the primary L&D daytime code is, likely just `"LD"` or `"L&D"`)
    *   `"NF-PEDS-PG": "PEDW"`
    *   *Check `docs/analysis/BLOCK_12_ANALYSIS.md` to confirm the exact specialty codes meant for the day half.*

### 3. Refine Preloader Primary Codes (If needed)
*   **Issue:** Some non-split inpatient rotations like `PEDS-WARD-` might also need explicit weekend handling in `backend/app/services/preload/rotation_codes.py` so the preloader can lock them in without needing the solver.

---

## Phase 3: Execution & Regeneration

Once Phases 1 and 2 are complete, execute a clean run:

1.  **Purge Bad Data:**
    ```sql
    DELETE FROM half_day_assignments
    WHERE date >= '2026-05-07' AND date <= '2026-06-03';
    ```
2.  **Run Preloader:**
    ```python
    svc.load_all_preloads(block_number=12, academic_year=2025)
    ```
3.  **Run Solver:**
    ```python
    engine.generate(block_number=12, academic_year=2025, algorithm="cp_sat")
    ```
4.  **Re-Export Workbook:**
    ```bash
    curl -o AY2025_Master_Schedule.xlsx "http://localhost:8000/api/v1/export/schedule/year/xlsx?academic_year=2025"
    ```
5.  **Verify:** Confirm 56 HDAs for all 16 residents, proper schedules for 14 core faculty, and 0 HDAs for the 3 adjunct faculty.

---

### Important Context Discovered During Exploration

*   **Preloader over Solver:** Expanding the `constants.py` mappings and the `rotation_codes.py` logic to fully lock in `NF-LD`, `NF-PEDS-PG`, and `PEDS-WARD-` via the preloader is often much safer and faster than relying on the CP-SAT solver to fill in inpatient gaps. The preloader is deterministic; the solver is easily broken by vacation overlap.
*   **Engine vs Faculty Templates:** The solver's engine dynamically falls back to generating generic HDAs if a faculty member has no `faculty_weekly_templates`. The engine uses `person.faculty_role` heavily (e.g. `'adjunct'`).
*   **Alembic vs Raw SQL:** Since constraints like `min_halfdays=31` vs `max_halfdays=28` on `NBN` are data issues, an Alembic data migration (e.g., `alembic revision -m "fix_nbn_constraints"`) is preferred over manual `psql` to ensure the fix propagates across all environments deterministically.
*   **Soft vs Hard Constraints:** In `rotation_activity_requirements`, `min_halfdays` acts as a HARD constraint. If a resident takes vacation, a high `min_halfdays` will result in `INFEASIBLE`. Keep `min_halfdays` at `0` and use `target_halfdays` with a high `priority` when writing migrations for `FMIT-PGY3` and others.
