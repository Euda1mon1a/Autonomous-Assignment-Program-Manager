***REMOVED*** Faculty Solver Integration (REQUIRED)

***REMOVED******REMOVED*** Scope Clarification

This scheduling system co-schedules **BOTH**:
- 🧑‍⚕️ Residents: 730 half-days/year
- 👨‍🔬 Faculty: 730 half-days/year

Faculty are NOT post-processed. They must be modeled in the solver.

---

***REMOVED******REMOVED*** Current Gap

| Component | Residents | Faculty |
|-----------|-----------|---------|
| Decision variables | ✅ Yes | ❌ No |
| `context.*_idx` | ✅ `resident_idx` | ❌ No `faculty_idx` |
| Constraints applied | ✅ Yes | ❌ Broken |
| Solution extraction | ✅ Yes | ❌ Missing |

---

***REMOVED******REMOVED*** Implementation Checklist

***REMOVED******REMOVED******REMOVED*** 1. Add `faculty_idx` to `SchedulingContext`
**File:** `backend/app/scheduling/constraints/base.py`
```python
faculty_idx: dict[uuid.UUID, int] = field(default_factory=dict)
```
Populate `faculty_idx` in `__post_init__` alongside `resident_idx`.

***REMOVED******REMOVED******REMOVED*** 2. Create Faculty Decision Variables (all templates)
**File:** `backend/app/scheduling/solvers.py`
```python
***REMOVED*** After resident variables (~line 223)
faculty_vars = {}
for f_i, faculty in enumerate(context.faculty):
    for b_i, block in enumerate(workday_blocks):
        for t_i, template_id in enumerate(template_ids):
            faculty_vars[f_i, b_i, t_i] = model.NewBoolVar(...)
variables["faculty_assignments"] = faculty_vars
```
**Also add PuLP equivalent** and keep the same 3D shape `(f_i, b_i, t_i)` everywhere.
If any constraints expect 2D `(f_i, b_i)`, update them to aggregate over templates.

***REMOVED******REMOVED******REMOVED*** 3. Update All Faculty-Referencing Constraints
Change `context.resident_idx.get(f.id)` → `context.faculty_idx.get(f.id)` and
switch to `faculty_assignments` where appropriate.

**Files:**
- `temporal.py` (Wed constraints)
- `capacity.py` (MaxPhysiciansInClinicConstraint)
- `faculty_role.py`
- `sports_medicine.py`
- `post_call.py`
- `resilience.py` (Hub/Zone/PreferenceTrail/N1 constraints)
- `acgme.py` (SupervisionRatioConstraint - if enforcing in solver)

***REMOVED******REMOVED******REMOVED*** 4. Bind Faculty to Resident Assignments
- If residents are assigned to clinic templates, require ≥1 faculty in the same
  block/template (or block, if you choose to aggregate).
- Enforce Wednesday rules against faculty variables (exact counts).

***REMOVED******REMOVED******REMOVED*** 5. Add Faculty-Specific Constraints
- One faculty per block (can't be in 2 places)
- Faculty availability
- Supervision ratio constraints (in-solver or keep post-hoc, but be consistent)

***REMOVED******REMOVED******REMOVED*** 6. Extract Faculty Assignments
**File:** `backend/app/scheduling/solvers.py`
```python
***REMOVED*** After resident extraction
for f_i, b_i, t_i in faculty_vars:
    if solver.Value(faculty_vars[f_i, b_i, t_i]):
        assignments.append(Assignment(
            person_id=context.faculty[f_i].id,
            ...
        ))
```
Also update `_create_assignments_from_result` (or equivalent) to persist faculty
rows and avoid double-assigning during the post-hoc supervision step.

***REMOVED******REMOVED******REMOVED*** 7. Update Tests
- Test faculty variables exist
- Test Wednesday constraints fire
- Integration test with mixed resident/faculty
- Validate faculty assignments appear in outputs/DB

---

***REMOVED******REMOVED*** Effort Estimate
**8-10 hours** across 2-3 sessions

---

***REMOVED******REMOVED*** Risks / Assumptions

**Assumptions**
- Faculty should be modeled for all templates (not clinic-only).
- Faculty assignments can be represented with the same block/template grid as residents.
- The post-hoc supervision step will be removed or adjusted to avoid double-assignment.

**Risks**
- Adding faculty variables multiplies solver size and may increase solve time or
  cause infeasibility without additional constraints (availability, coverage).
- Existing constraints that implicitly assume residents-only may over-constrain
  once faculty variables are introduced; careful auditing is required.
- If objective functions include faculty variables unintentionally, the solver
  may over-assign faculty unless bounded by explicit constraints.

***REMOVED******REMOVED*** Files Impacted
- `solvers.py` (major)
- `base.py` (context)
- `temporal.py` (minor - index fix)
- `capacity.py`, `faculty_role.py`, `acgme.py` (index fixes)
- Test files
