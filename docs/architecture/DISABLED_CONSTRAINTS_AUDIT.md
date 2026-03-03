# Disabled Constraints Audit

> **Date:** 2026-03-02 (updated 2026-03-03)
> **Scope:** All constraints in `ConstraintManager.create_default(profile="faculty")` (production default)
> **Source:** `backend/app/scheduling/constraints/manager.py`

## Summary

The constraint manager registers **51 constraints** in `create_default()`. With the `profile="faculty"` flag (used by `engine.py`), **4 additional constraints are re-enabled** (FMITWeekBlocking, FMITMandatoryCall, OvernightCallGeneration, DeptChiefWednesdayPreference), giving **47 enabled** at the manager level.

Only **4 remain disabled** in the manager — all conditionally enabled by `engine.py` at runtime when their data dependencies exist: ResidentWeeklyClinic, ZoneBoundary, PreferenceTrail, N1Vulnerability.

### Change Log

| Date | PR | Change |
|------|-----|--------|
| Mar 2 | #1224 | Initial audit: 9 disabled constraints documented |
| Mar 3 | #1225 | Removed FMITResidentClinicDay stub, fixed `_get_template_ids_by_activity` → `_get_template_ids_by_rotation_type` |
| Mar 3 | #1226 | Re-enabled 4 constraints after combined stress test (all OPTIMAL, 16.7s, Block 12) |

## Constraint Inventory

| # | Constraint Name | File | Type | Status | Notes |
|---|----------------|------|------|--------|-------|
| 1 | `WednesdayPMSingleFaculty` | `temporal.py` | Hard | **ENABLED** (PR #1226) | Passes OPTIMAL but **no-ops at runtime** — looks for `faculty_template_assignments` which solver creates. Originally INFEASIBLE Feb 28; now OPTIMAL (likely due to Wed PM LEC preloader fix in PR #1215). Needs variable mapping refactor to become functional. |
| 2 | `SMResidentFacultyAlignment` | `sports_medicine.py` | Hard | **ENABLED** (PR #1226) | SM data exists: SM faculty member (`faculty_role='sports_med'`), SM-AM/SM-PM/ACS-AM templates. `requires_specialty` column unpopulated so constraint no-ops gracefully. Fully functional when `requires_specialty` is populated. |
| 3 | `SMFacultyNoRegularClinic` | `faculty_role.py` | Hard | **ENABLED** (PR #1226) | Blocks SM faculty from regular clinic templates. SM faculty member matches via `faculty_role='sports_med'`. Active — prevents SM faculty member assignment to non-SM clinic slots. |
| 4 | ~~`FMITResidentClinicDay`~~ | ~~`inpatient.py`~~ | Hard | **REMOVED** (PR #1225) | Stub deleted. Pre-loader handles PGY-specific FMIT clinic days. |
| 5 | `HalfDayRequirement` | `halfday_requirement.py` | Soft | **ENABLED** (PR #1226) | Method bug fixed (PR #1225). CP-SAT deviation penalty still **incomplete** — creates `fm_vars`/`specialty_vars` but never adds penalty to objective. Runs OPTIMAL but effectively passive. |
| 6 | `ResidentWeeklyClinic` | `resident_weekly_clinic.py` | Soft | **DISABLED** (engine conditional) | Conditionally enabled by `engine.py` (line 1146) when `weekly_reqs` data exists. Implementation complete. Correct pattern. |
| 7 | `ZoneBoundary` | `resilience.py` | Soft | **DISABLED** (engine conditional) | Conditionally enabled by `engine.py` (line 1254) when zone data exists from `ResilienceService`. Implementation complete. Correct pattern. |
| 8 | `PreferenceTrail` | `resilience.py` | Soft | **DISABLED** (engine conditional) | Conditionally enabled by `engine.py` (line 1240) when preference trail data exists. Implementation complete. Correct pattern. |
| 9 | `N1Vulnerability` | `resilience.py` | Soft | **DISABLED** (engine conditional) | Conditionally enabled by `engine.py` (line 1228) during resilience loading. Implementation complete. Correct pattern. |

## Category Summary

| Category | Count | Constraints |
|----------|-------|-------------|
| **ENABLED** (active in manager, functional) | 1 | SMFacultyNoRegularClinic |
| **ENABLED** (active in manager, passive/no-op) | 3 | WednesdayPMSingleFaculty, SMResidentFacultyAlignment, HalfDayRequirement |
| **DISABLED** (engine enables when data exists) | 4 | ResidentWeeklyClinic, ZoneBoundary, PreferenceTrail, N1Vulnerability |
| **REMOVED** | 1 | FMITResidentClinicDay |

## Remaining Technical Debt

### 1. WednesdayPMSingleFaculty — Variable Mapping Refactor (HIGH)

**File:** `backend/app/scheduling/constraints/temporal.py:212`

**Status:** Enabled but passive. The constraint accesses `variables.get("faculty_template_assignments")` which the solver does create (`solvers.py:341`, `:1061`). It solves OPTIMAL but the variable key may not be populated for the constraint's specific use case (per-Wednesday-PM faculty assignment tracking). Needs investigation of whether the constraint actually adds any CP-SAT terms at runtime.

**Correction (PR #1225, Codex P2):** Original diagnosis was wrong — `faculty_template_assignments` does exist. The Feb 28 INFEASIBLE was likely caused by hard `== 1` conflicting with preloaded assignments on certain Wednesday PMs. The Wed PM LEC preloader (PR #1215) may have resolved the underlying conflict.

### 2. SMResidentFacultyAlignment — Data Population (LOW)

**File:** `backend/app/scheduling/constraints/sports_medicine.py`

**Status:** Enabled but no-ops because `requires_specialty` column on `rotation_templates` is not populated. SM faculty member is correctly identified as `sports_med` faculty. SM-AM/SM-PM/ACS-AM templates exist. When `requires_specialty = "Sports Medicine"` is set on relevant templates, this constraint will automatically activate resident-faculty alignment for SM rotations.

### 3. HalfDayRequirement — CP-SAT Deviation Formulation (MEDIUM)

**File:** `backend/app/scheduling/constraints/halfday_requirement.py:345-352`

**Status:** Enabled but passive. The `add_to_cpsat()` method creates `fm_vars` and `specialty_vars` correctly but the deviation penalty section (lines 345-352) has a "simplification" comment and does not actually create deviation IntVars or add penalty terms to the objective. The constraint runs without error but has zero effect on the optimization.

**Fix needed (~30 lines):** Create `under`/`over` IntVars for each target, add `AddAbsEquality` or similar deviation tracking, and append weighted penalty terms to the objective.

## Action Items

| Priority | Action | Constraint | Effort | Status |
|----------|--------|-----------|--------|--------|
| ~~LOW~~ | ~~Remove stub~~ | ~~FMITResidentClinicDay~~ | — | Done (PR #1225) |
| ~~MEDIUM~~ | ~~Fix method name bug~~ | ~~HalfDayRequirement~~ | — | Done (PR #1225) |
| ~~MEDIUM~~ | ~~Re-enable 4 stress-tested constraints~~ | ~~All 4~~ | — | Done (PR #1226) |
| HIGH | Verify WednesdayPMSingleFaculty adds terms at runtime | WednesdayPMSingleFaculty | Investigation |
| MEDIUM | Complete CP-SAT deviation formulation | HalfDayRequirement | ~30 lines |
| LOW | Populate `requires_specialty` on SM templates | SMResidentFacultyAlignment | Data entry |
