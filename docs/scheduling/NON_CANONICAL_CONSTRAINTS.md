# Non-Canonical / Future Constraints (Do Not Assume Enforced)

Purpose:
This document lists constraints and solver paths that exist in the codebase but are NOT part of the canonical CP-SAT schedule generation pipeline. These items may be experimental, incomplete, analytics-only, or require data/variables that are not currently wired into the solver.

Status: Informational only. No operational guarantees.

---

## 1) Non-Canonical Solver Paths

These solvers exist but are NOT used by the canonical pipeline:

- GreedySolver
- PuLPSolver
- HybridSolver
- Quantum / QUBO stack (backend/app/scheduling/quantum/*)

Why non-canonical?
The engine now forces CP-SAT. These solvers are retained for future experimentation or fallback, but are not authoritative.

---

## 2) Constraints That Exist but Are NOT Registered

### ResidentWeeklyClinicConstraint (backend/app/scheduling/constraints/resident_weekly_clinic.py)
- Status: Not registered.
- Reason: Depends on weekly_requirements data that is not loaded into SchedulingContext. Also rotation-level, not PGY-specific.
- Impact: Weekly clinic caps by PGY (as described in skill docs) are NOT enforced by this constraint.

### IntegratedWorkloadConstraint (backend/app/scheduling/constraints/integrated_workload.py)
- Status: Not registered.
- Reason: Uses incorrect variable set for faculty workload in CP-SAT (uses resident variables). Appears intended for reporting/analytics rather than optimization.
- Impact: Unified workload fairness (call + clinic + FMIT + admin + academic) is NOT enforced.

### FacultyWeeklyTemplateConstraint (backend/app/scheduling/constraints/faculty_weekly_template.py)
- Status: Not registered.
- Reason: Requires faculty activity variables (faculty_activities / faculty_slots) that are not part of the CP-SAT solver model.
- Impact: Faculty weekly template preferences are NOT enforced in solver.

---

## 3) Constraints Registered but Disabled by Default

### FMITMandatoryCallConstraint (backend/app/scheduling/constraints/fmit.py)
- Status: Registered but disabled.
- Reason: CP-SAT call variables are only created for Sun-Thu; Fri/Sat call is handled via preloads.
- Impact: FMIT Fri/Sat call coverage enforced only through preload rules.

### FMITWeekBlockingConstraint (backend/app/scheduling/constraints/fmit.py)
- Status: Registered but disabled.
- Reason: Requires FMIT week data (from preloads/assignments); disabled to avoid false blocking when data is incomplete.
- Impact: FMIT week blocking is not solver-enforced unless explicitly enabled with required data.

### FMITResidentClinicDayConstraint (backend/app/scheduling/constraints/inpatient.py)
- Status: Registered but disabled.
- Reason: Requires FMIT configuration data; disabled to avoid over-constraint.
- Impact: PGY-specific FMIT clinic day rules are not solver-enforced by default.

---

## 4) Preference-Only Constraints Not Included

### Department-chief Wednesday preference (backend/app/scheduling/constraints/call_equity.py)
- Constraint: `DeptChiefWednesdayPreferenceConstraint` (role-based preference)
- Status: Exists but not registered.
- Reason: Pure preference; not core policy.
- Impact: department-chief Wednesday preference not applied in solver.

---

## 5) Why These Are Not in the Canonical Doc

The canonical document is a source of truth for what the system enforces today. Including non-wired, disabled, or experimental constraints would:

- Mislead operators about enforcement
- Hide data-dependency gaps
- Create false expectations in schedule review

---

## 6) activation steps (non-canonical)

ResidentWeeklyClinicConstraint
- Load ResidentWeeklyRequirement into context
- Resolve PGY-specific caps separately (this constraint is rotation-agnostic)

IntegratedWorkloadConstraint
- Re-implement using correct faculty variables and half-day assignment data

FacultyWeeklyTemplateConstraint
- Integrate into faculty CP-SAT assignment model (not rotation solver)

FMITMandatoryCallConstraint
- Add Fri/Sat call variables to CP-SAT (or keep preload-based enforcement)
