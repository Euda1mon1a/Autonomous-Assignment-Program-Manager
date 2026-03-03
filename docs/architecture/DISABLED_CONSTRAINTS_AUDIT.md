# Disabled Constraints Audit

> **Date:** 2026-03-02 (updated 2026-03-03)
> **Scope:** All constraints disabled in `ConstraintManager.create_default(profile="faculty")` (production default)
> **Source:** `backend/app/scheduling/constraints/manager.py`

## Summary

The constraint manager registers **51 constraints** in `create_default()`. With the `profile="faculty"` flag (used by `engine.py`), **4 additional constraints are re-enabled** (FMITWeekBlocking, FMITMandatoryCall, OvernightCallGeneration, DeptChiefWednesdayPreference), giving **47 enabled** at the manager level.

**Update (Mar 3, PR #1226):** 4 previously-disabled constraints re-enabled after combined stress test (all OPTIMAL, 16.7s, Block 12). Only **4 remain disabled** — all conditionally enabled by `engine.py` at runtime when data exists (ResidentWeeklyClinic, ZoneBoundary, PreferenceTrail, N1Vulnerability).

Of these 9, **3 are conditionally enabled** by `engine.py` at runtime when their data dependencies exist (HalfDayRequirement, ResidentWeeklyClinic, and the 3 Tier-2 resilience constraints).

## Constraint Inventory

| # | Constraint Name | File | Type | Category | Reason Disabled | Recommendation |
|---|----------------|------|------|----------|----------------|----------------|
| 1 | `WednesdayPMSingleFaculty` | `temporal.py` | Hard | DEFER | `faculty_template_assignments` exists in both solver paths (`solvers.py:341`, `:1061`). Root cause of INFEASIBLE (Feb 28 stress test): hard `== 1` exactly-one-faculty-in-clinic conflicts with preloaded assignments on certain Wednesday PMs. | Investigate preload conflicts. Convert to soft constraint or relax to `>= 1`. |
| 2 | `SMResidentFacultyAlignment` | `sports_medicine.py` | Hard | DEFER | Requires Sports Medicine program data (`is_sports_medicine`, `requires_specialty` on templates, SM faculty identification). No SM program currently configured in the database. Implementation is complete and well-tested. | Enable when SM program is configured. Safe to enable -- will no-op gracefully (early returns) when no SM data exists. |
| 3 | `SMFacultyNoRegularClinic` | `faculty_role.py` | Hard | DEFER | Same dependency as #2. Blocks SM faculty (`faculty_role == "sports_med"`) from regular clinic templates. No SM faculty currently in database. | Enable when SM program is configured. Safe to enable -- no-ops when no SM faculty exist. |
| 4 | ~~`FMITResidentClinicDay`~~ | ~~`inpatient.py`~~ | Hard | REMOVED | Was a stub: `add_to_cpsat()` logged "Added 0 constraints" and returned. Removed in PR #1225. Pre-loader handles PGY-specific FMIT clinic days. | Done. |
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
| **REMOVED** (stub deleted PR #1225) | 1 | FMITResidentClinicDay |

## Detailed Findings

### 1. WednesdayPMSingleFaculty (DEFER)

**File:** `backend/app/scheduling/constraints/temporal.py:212`

**Correction (PR #1225, Codex P2):** The original diagnosis was wrong — `faculty_template_assignments` **does** exist in both solver paths (`solvers.py:341` and `:1061`). The constraint accesses the correct variable key.

The actual root cause of INFEASIBLE (Feb 28 stress test) is the hard `model.Add(sum(...) == 1)` requirement: on certain Wednesday PMs, preloaded assignments and other hard constraints leave zero or multiple faculty available for outpatient clinic, making exactly-one unsatisfiable.

**Tests:** `backend/tests/constraints/test_temporal_constraint.py:496` (helper tests only, no solver integration)

**Fix required:** Either:
- Investigate which Wednesday PM blocks conflict with preloads/other constraints
- Convert from hard to soft constraint (penalize deviation from 1)
- Relax to `>= 1` if the concern is only about having at least one

### 2-3. SM Constraints (DEFER -- data dependency)

**Files:** `sports_medicine.py`, `faculty_role.py:329`

Both constraints are well-implemented with proper CP-SAT, PuLP, and validation methods. They gracefully no-op when SM data is absent (early return when no SM templates/faculty found). The only reason they are disabled is that the Sports Medicine program is not yet configured in the database.

**Tests:** `backend/tests/scheduling/test_sports_medicine_constraint.py`, `backend/tests/scheduling/test_faculty_role_constraint.py`

**Note:** These are actually safe to enable now -- they will do nothing without SM data and activate automatically when SM faculty/templates are added. However, keeping them disabled makes the constraint count cleaner and avoids any edge-case surprises.

### 4. FMITResidentClinicDay (REMOVED — PR #1225)

Stub constraint deleted. Pre-loader handles all PGY-specific FMIT clinic day assignments. Removed from `inpatient.py`, `manager.py`, `__init__.py`, `config.py`.

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
| ~~LOW~~ | ~~Remove stub from registration~~ | ~~FMITResidentClinicDay~~ | Done (PR #1225) |
| ~~MEDIUM~~ | ~~Fix `_get_template_ids_by_activity` bug~~ | ~~HalfDayRequirement~~ | Done (PR #1225) |
| MEDIUM | Complete CP-SAT deviation formulation | HalfDayRequirement | ~30 lines |
| HIGH | Refactor to use existing solver variables | WednesdayPMSingleFaculty | Variable mapping refactor |
| LOW | Enable when SM program configured | SM constraints (2) | 0 code change (data dependency) |
