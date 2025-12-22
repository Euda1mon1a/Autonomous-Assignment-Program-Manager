***REMOVED*** Solver Integration Gap

## Problem Summary
Wednesday constraints (`WednesdayPMSingleFacultyConstraint`, `InvertedWednesdayConstraint`) cannot enforce faculty assignments because **the solver only models resident decision variables**.

## Current State

### Solver Architecture (`backend/app/scheduling/solvers.py`)
```python
# Line ~176-223: Only resident variables are created
for r_i, resident in enumerate(context.residents):
    for b_i, block in enumerate(context.blocks):
        for t_i, template in enumerate(context.templates):
            template_vars[r_i, b_i, t_i] = model.NewBoolVar(...)
```

- `template_assignments` dict: **residents only**
- `context.resident_idx`: maps resident IDs to indices
- Faculty are NOT in `resident_idx` → `f_i = context.resident_idx.get(f.id)` returns `None`

### Wednesday Constraints Impact
```python
# temporal.py add_to_cpsat - this does nothing because:
for f in context.faculty:
    f_i = context.resident_idx.get(f.id)  # Always None!
    if f_i is not None and (f_i, b_i, t_i) in template_vars:
        faculty_clinic_vars.append(...)  # Never executed
```

**Result:** `faculty_clinic_vars` is always empty → no constraints added.

---

## Required Changes

### Option 1: Model Faculty in Solver (Recommended)

**Files to modify:**
1. `backend/app/scheduling/solvers.py` - Add faculty decision variables
2. `backend/app/scheduling/constraints/base.py` - Add `faculty_idx` to `SchedulingContext`
3. `backend/app/scheduling/constraints/temporal.py` - Use `faculty_idx` instead of `resident_idx`

**Implementation Steps:**

1. **Add faculty variables to solver:**
```python
# In solvers.py, after resident variables
faculty_vars = {}
for f_i, faculty in enumerate(context.faculty):
    for b_i, block in enumerate(context.blocks):
        for t_i, template in enumerate(context.templates):
            faculty_vars[f_i, b_i, t_i] = model.NewBoolVar(
                f"faculty_{f_i}_block_{b_i}_template_{t_i}"
            )
variables["faculty_assignments"] = faculty_vars
```

2. **Add faculty_idx to SchedulingContext:**
```python
# In base.py SchedulingContext
faculty_idx: dict[uuid.UUID, int] = field(default_factory=dict)

# Populate during context creation
faculty_idx = {f.id: i for i, f in enumerate(context.faculty)}
```

3. **Update temporal.py constraints:**
```python
# Replace:
f_i = context.resident_idx.get(f.id)
# With:
f_i = context.faculty_idx.get(f.id)

# Use faculty_vars instead of template_vars:
faculty_vars = variables.get("faculty_assignments", {})
```

4. **Add faculty-specific constraints:**
- Faculty can only be at one place per block (OnePersonPerBlockConstraint equivalent)
- Faculty supervision requirements still apply

---

## Scope Assessment

| Task | Complexity | Risk |
|------|------------|------|
| Add `faculty_idx` to context | Low | Low |
| Add faculty decision variables | Medium | Medium |
| Update Wednesday constraints | Low | Low |
| Test integration | Medium | Medium |
| Faculty-specific constraints | Medium | Low |

**Estimated effort:** 2-3 hours

---

## Validation After Fix
1. Run solver and verify faculty variables are created
2. Check that Wednesday constraints add clauses to model
3. Validate generated schedules have exactly 1 faculty on Wed PM
4. Validate 4th Wednesday has different AM/PM faculty

---

## Current Workaround
Constraints are currently **validation-only** — they check assignments after solving but don't prevent violations during optimization. This is acceptable for initial deployment since violations will be flagged in the schedule report.
