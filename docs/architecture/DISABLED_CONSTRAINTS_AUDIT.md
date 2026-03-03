# Disabled Constraints Audit

> **Date:** 2026-03-02
> **Scope:** All constraints disabled in `ConstraintManager.create_default(profile="faculty")` (production default)
> **Source:** `backend/app/scheduling/constraints/manager.py`

## Summary

The constraint manager registers **52 constraints** in `create_default()`. With the `profile="faculty"` flag (used by `engine.py`), **4 additional constraints are re-enabled** (FMITWeekBlocking, FMITMandatoryCall, OvernightCallGeneration, DeptChiefWednesdayPreference), leaving **9 constraints disabled** at the manager level.

Of these 9, **3 are conditionally enabled** by `engine.py` at runtime when their data dependencies exist (HalfDayRequirement, ResidentWeeklyClinic, and the 3 Tier-2 resilience constraints).

## Constraint Inventory

| # | Constraint Name | File | Type | Category | Reason Disabled | Recommendation |
|---|----------------|------|------|----------|----------------|----------------|
| 1 | `WednesdayPMSingleFaculty` | `temporal.py` | Hard | DEFER | Uses `faculty_template_assignments` variable dict key that does not exist in the current solver model. The solver creates `template_assignments` but not `faculty_template_assignments`. Stress test (Feb 28) confirmed INFEASIBLE when enabled. | Needs solver variable refactor to map faculty through `template_assignments` or create the missing variable dict. |
| 2 | `SMResidentFacultyAlignment` | `sports_medicine.py` | Hard | DEFER | Requires Sports Medicine program data (`is_sports_medicine`, `requires_specialty` on templates, SM faculty identification). No SM program currently configured in the database. Implementation is complete and well-tested. | Enable when SM program is configured. Safe to enable -- will no-op gracefully (early returns) when no SM data exists. |
| 3 | `SMFacultyNoRegularClinic` | `faculty_role.py` | Hard | DEFER | Same dependency as #2. Blocks SM faculty (`faculty_role == "sports_med"`) from regular clinic templates. No SM faculty currently in database. | Enable when SM program is configured. Safe to enable -- no-ops when no SM faculty exist. |
| 4 | `FMITResidentClinicDay` | `inpatient.py` | Hard | DEAD | Implementation is a **stub**: `add_to_cpsat()` logs "Added 0 constraints (pre-loaded)" and returns. `validate()` returns satisfied unconditionally. The pre-loading mechanism handles FMIT resident clinic day assignments, making this constraint redundant. | Remove from registration. The pre-loader (`sync_preload_service.py`) already handles PGY-specific FMIT clinic days. This constraint adds nothing. |
| 5 | `HalfDayRequirement` | `halfday_requirement.py` | Soft | DEFER | Disabled at manager level but **conditionally enabled by engine.py** (line 1157) when `halfday_reqs` data exists. CP-SAT implementation is **incomplete** -- the deviation variable section has a "simplification" comment and does not actually add penalty terms to the objective. PuLP `add_to_pulp()` and `validate()` call `_get_template_ids_by_activity()` which **does not exist** (will raise `AttributeError`). | Fix the missing method (`_get_template_ids_by_activity` -> `_get_template_ids_by_rotation_type`) and complete the CP-SAT deviation penalty. Keep disabled at manager level; engine enables when data exists. |
| 6 | `ResidentWeeklyClinic` | `resident_weekly_clinic.py` | Soft | OK | Disabled at manager level but **conditionally enabled by engine.py** (line 1146) when `weekly_reqs` data exists. Implementation is complete with proper CP-SAT soft penalty formulation (under_min/over_max IntVars). Tests exist. | No action needed. The current pattern (disabled in manager, enabled by engine when data exists) is correct and intentional. |
| 7 | `ZoneBoundary` | `resilience.py` | Soft | OK | Tier-2 resilience constraint. Disabled at manager level but **conditionally enabled by engine.py** (line 1254) when zone assignment data exists from `ResilienceService`. Implementation is complete. Requires `context.zone_assignments` and `context.block_zones` to be populated. | No action needed. Correct pattern -- engine enables when resilience data is available. |
| 8 | `PreferenceTrail` | `resilience.py` | Soft | OK | Tier-2 resilience constraint. Disabled at manager level but **conditionally enabled by engine.py** (line 1240) when preference trail data exists from stigmergy analysis. Implementation is complete. Requires `context.preference_trails` to be populated. | No action needed. Correct pattern -- engine enables when preference data is available. |
| 9 | `N1Vulnerability` | `resilience.py` | Soft | OK | Tier-2 resilience constraint. Disabled at manager level but **conditionally enabled by engine.py** (line 1228) unconditionally during resilience loading. Implementation is complete. Uses `context.availability` and `context.n1_vulnerable_faculty` data. | No action needed. Correct pattern -- engine enables during resilience data loading. |

## Category Summary

| Category | Count | Constraints |
|----------|-------|-------------|
| **OK** (correctly disabled, engine enables when needed) | 4 | ResidentWeeklyClinic, ZoneBoundary, PreferenceTrail, N1Vulnerability |
| **DEFER** (needs work before enabling) | 4 | WednesdayPMSingleFaculty, SMResidentFacultyAlignment, SMFacultyNoRegularClinic, HalfDayRequirement |
| **DEAD** (stub, should be removed) | 1 | FMITResidentClinicDay |

## Detailed Findings

### 1. WednesdayPMSingleFaculty (DEFER)

**File:** `backend/app/scheduling/constraints/temporal.py:212`
**Disable reason (line 373-375):** "needs solver variable refactor (uses faculty_template_assignments vars that don't exist in current model)"

The constraint's `add_to_cpsat()` method accesses `variables.get("faculty_template_assignments", {})`. The current solver (`solvers.py`) only creates `template_assignments` -- there is no `faculty_template_assignments` key. This means the constraint silently no-ops (the dict is empty, so it returns early). However, if enabled as a **hard** constraint, the solver would not add any constraints but the **validation** step would still check for exactly 1 faculty in clinic on Wednesday PM, potentially raising false violations.

**Tests:** `backend/tests/constraints/test_temporal_constraint.py:496` (helper tests only, no solver integration)

**Fix required:** Either:
- Refactor to use `template_assignments` with faculty identification from context
- Create `faculty_template_assignments` in the solver
- Convert to soft constraint to avoid infeasibility risk

### 2-3. SM Constraints (DEFER -- data dependency)

**Files:** `sports_medicine.py`, `faculty_role.py:329`

Both constraints are well-implemented with proper CP-SAT, PuLP, and validation methods. They gracefully no-op when SM data is absent (early return when no SM templates/faculty found). The only reason they are disabled is that the Sports Medicine program is not yet configured in the database.

**Tests:** `backend/tests/scheduling/test_sports_medicine_constraint.py`, `backend/tests/scheduling/test_faculty_role_constraint.py`

**Note:** These are actually safe to enable now -- they will do nothing without SM data and activate automatically when SM faculty/templates are added. However, keeping them disabled makes the constraint count cleaner and avoids any edge-case surprises.

### 4. FMITResidentClinicDay (DEAD)

**File:** `backend/app/scheduling/constraints/inpatient.py:371`

This is a stub constraint:
- `add_to_cpsat()`: Logs "Added 0 constraints (pre-loaded)" and returns
- `add_to_pulp()`: `pass`
- `validate()`: Always returns `satisfied=True`

The pre-loading mechanism (`backend/app/services/preload/sync_preload_service.py`) handles FMIT resident clinic day assignments. This constraint was presumably created as a placeholder that was never needed.

**Tests:** `backend/tests/scheduling/test_inpatient_constraint.py` (tests exist but only for `ResidentInpatientHeadcountConstraint`, not for this stub)

### 5. HalfDayRequirement (DEFER -- buggy)

**File:** `backend/app/scheduling/constraints/halfday_requirement.py:216`

Two bugs identified:
1. **Missing method:** `add_to_pulp()` (line 370) and `validate()` (line 425) call `self._get_template_ids_by_activity(context)` which does not exist. Only `_get_template_ids_by_rotation_type()` is defined. These methods will raise `AttributeError` at runtime.
2. **Incomplete CP-SAT:** The `add_to_cpsat()` method creates `fm_vars` and `specialty_vars` but the deviation penalty section (lines 346-352) is commented as "simplification" and does not actually create deviation variables or add them to the objective.

**Tests:** `backend/tests/scheduling/test_halfday_requirement_constraint.py` (tests exist but may not exercise the buggy paths)

### 6-9. Conditionally-Enabled Constraints (OK)

ResidentWeeklyClinic, ZoneBoundary, PreferenceTrail, and N1Vulnerability follow a correct architectural pattern: disabled in the manager (safe default), enabled by `engine.py` when their data dependencies are satisfied. This is the intended behavior and should not be changed.

## Action Items

| Priority | Action | Constraint | Effort |
|----------|--------|-----------|--------|
| LOW | Remove stub from registration | FMITResidentClinicDay | 1 line change |
| MEDIUM | Fix `_get_template_ids_by_activity` bug | HalfDayRequirement | Method rename or add alias |
| MEDIUM | Complete CP-SAT deviation formulation | HalfDayRequirement | ~30 lines |
| HIGH | Refactor to use existing solver variables | WednesdayPMSingleFaculty | Variable mapping refactor |
| LOW | Enable when SM program configured | SM constraints (2) | 0 code change (data dependency) |
