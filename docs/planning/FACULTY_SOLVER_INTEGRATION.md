# Faculty Solver Integration (REQUIRED)

## Scope Clarification

This scheduling system co-schedules **BOTH**:
- 🧑‍⚕️ Residents: 730 half-days/year
- 👨‍🔬 Faculty: 730 half-days/year

Faculty are NOT post-processed. They must be modeled in the solver.

---

## Current Gap

| Component | Residents | Faculty |
|-----------|-----------|---------|
| Decision variables | ✅ Yes | ❌ No |
| `context.*_idx` | ✅ `resident_idx` | ❌ No `faculty_idx` |
| Constraints applied | ✅ Yes | ❌ Broken |
| Solution extraction | ✅ Yes | ❌ Missing |

---

## Implementation Checklist

### 1. Add `faculty_idx` to `SchedulingContext`
**File:** `backend/app/scheduling/constraints/base.py`
```python
faculty_idx: dict[uuid.UUID, int] = field(default_factory=dict)
```

### 2. Create Faculty Decision Variables
**File:** `backend/app/scheduling/solvers.py`
```python
# After resident variables (~line 223)
faculty_vars = {}
for f_i, faculty in enumerate(context.faculty):
    for b_i, block in enumerate(workday_blocks):
        for t_i, template_id in enumerate(template_ids):
            faculty_vars[f_i, b_i, t_i] = model.NewBoolVar(...)
variables["faculty_assignments"] = faculty_vars
```
**Also add PuLP equivalent.**

### 3. Update All Faculty-Referencing Constraints
Change `context.resident_idx.get(f.id)` → `context.faculty_idx.get(f.id)`

**Files:**
- `temporal.py` (Wed constraints)
- `capacity.py` (MaxPhysiciansInClinicConstraint)
- `faculty_role.py`
- `sports_medicine.py`
- `acgme.py` (SupervisionRatioConstraint)

### 4. Add Faculty-Specific Constraints
- One faculty per block (can't be in 2 places)
- Faculty availability
- **Wednesday rules** (already written, need faculty_idx)

### 5. Extract Faculty Assignments
**File:** `backend/app/scheduling/solvers.py`
```python
# After resident extraction
for f_i, b_i, t_i in faculty_vars:
    if solver.Value(faculty_vars[f_i, b_i, t_i]):
        assignments.append(Assignment(
            person_id=context.faculty[f_i].id,
            ...
        ))
```

### 6. Update Tests
- Test faculty variables exist
- Test Wednesday constraints fire
- Integration test with mixed resident/faculty

---

## Effort Estimate
**8-10 hours** across 2-3 sessions

## Files Impacted
- `solvers.py` (major)
- `base.py` (context)
- `temporal.py` (minor - index fix)
- `capacity.py`, `faculty_role.py`, `acgme.py` (index fixes)
- Test files
