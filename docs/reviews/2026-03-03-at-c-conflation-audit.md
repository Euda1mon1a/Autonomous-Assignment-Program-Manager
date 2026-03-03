# Audit Finding: Conflation of `AT` and `C` in Post-Processing

**Date:** March 3, 2026
**Auditor:** Gemini CLI

## Summary of Findings

I have found the remaining trace of code that directly equivocates and conflates the `AT` (Attending / Supervision) and `C` (Clinic / Patient Capacity) activity codes.

This conflation occurs **after** the CP-SAT solver has finished its work, inside the translation layer that maps coarse solver assignments back to specific database activity codes.

## The Offending Code

### 1. The Engine Resolver (`backend/app/scheduling/engine.py`)

In `backend/app/scheduling/engine.py` (lines ~3840-3860), the internal function `_resolve_template_activity()` is responsible for refining the coarse solver outputs (`C`, `AT`, `PCAT`, `DO`, `OFF`) against the faculty's `WeeklyPattern` templates.

```python
        def _resolve_template_activity(
            faculty_id: UUID,
            slot_date: date,
            time_of_day: str,
            solver_type: str,
        ) -> str:
            """Resolve solver coarse type to specific template activity code."""

            # Only override C and AT — PCAT, DO, OFF have specific semantics
            if solver_type not in ("C", "AT"):
                return solver_type

            # Template day_of_week uses Python weekday convention (0=Mon, 6=Sun)
            py_wd = slot_date.weekday()

            tpl_code = template_lookup.get((faculty_id, py_wd, time_of_day))
            if tpl_code and tpl_code.lower() not in _POSTCALL_CODES:
                return tpl_code  # Template is authoritative

            return solver_type
```

### 2. The Enforcing Tests (`backend/tests/scheduling/test_resolve_template_activity.py`)

This conflation is currently codified as expected behavior in the test suite. The test file explicitly mocks this behavior:

```python
        # Only override C and AT — PCAT, DO, OFF have specific semantics
        if solver_type not in ("C", "AT"):
            return solver_type
```

## Why This is Harmful (The "Conflation" Problem)

The CP-SAT solver works incredibly hard to distinguish between `fac_clinic` (which counts toward maximum physical capacity and generates patient load) and `fac_supervise` (which satisfies the ACGME `SupervisionRatioConstraint` requirements).

By treating `C` and `AT` as identical, pliable "buckets" that can unconditionally be overwritten by whatever `tpl_code` the weekly pattern dictates, the post-processor destroys the solver's math.

**Failure Mode A (Losing Supervision):**
1. Solver realizes there are 5 residents in clinic on Tuesday AM. It assigns Dr. Smith the `AT` (Supervise) variable to satisfy the ACGME ratio constraint.
2. The `_resolve_template_activity` function sees the solver output `AT`.
3. Dr. Smith's weekly template for Tuesday AM happens to be `fm_clinic` (`C`).
4. The resolver blindly overwrites `AT` with `fm_clinic` because `solver_type` is in `("C", "AT")`.
5. The final schedule now lacks an attending for Tuesday AM, creating a silent ACGME violation.

**Failure Mode B (Losing Capacity):**
1. Solver realizes it needs to hit Dr. Jones' minimum clinic requirement, so it assigns `C`.
2. Dr. Jones' template for that slot happens to be `dfm` (Admin).
3. The resolver overwrites `C` with `dfm`.
4. The final schedule silently drops below Dr. Jones' required clinic capacity.

## Conclusion & Next Steps

The comment in `engine.py` notes:
> *NOTE: FacultyWeeklyTemplateConstraint is not yet registered, so the solver doesn't respect templates during optimization. Once registered, cross-category conflicts (solver=C, template=admin) will decrease.*

While adding the `FacultyWeeklyTemplateConstraint` will help the solver naturally align with the templates, this `_resolve_template_activity` function is fundamentally unsafe. It acts as a rogue post-processor that can silently invalidate hard solver constraints by conflating `C` and `AT` as interchangeable defaults.

**Recommendation:**
The resolver should be refactored to verify that the `tpl_code` actually belongs to the same semantic category as the `solver_type`. If the solver demanded `AT`, it should only be overridden by templates that have `is_supervision == True`. If the solver demanded `C`, it should only be overridden by templates that have `is_solver_clinic == True`.

---

## Action Taken

**Date:** 2026-03-03

Gemini's finding is validated. The `_SOLVER_CLINIC_CODES` and `_SOLVER_ADMIN_CODES` classification sets already exist at `engine.py:3900-3917` but are documented as "no longer gate the write-back." They must be reinstated as category gates.

**Tracked as:** Faculty Fix Roadmap Phase 4 — `docs/architecture/FACULTY_FIX_ROADMAP.md`

**Scope:**
- 4A: Category-gate `_resolve_template_activity()` — solver=C only overridden by clinic codes, solver=AT only by admin codes
- 4B: Mirror fix in `_apply_faculty_template_correction()` — same category gate for post-solve sweep
- 4C: Register `FacultyWeeklyTemplateConstraint` so solver natively respects templates during optimization
- 4D: Invert cross-category test expectations in `test_resolve_template_activity.py`

No schema changes required — the classification sets already exist in code.
