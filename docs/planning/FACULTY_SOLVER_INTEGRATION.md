<<<<<<< HEAD
***REMOVED*** Faculty Solver Integration (REQUIRED)
=======
***REMOVED*** Solver Integration (REQUIRED)
>>>>>>> origin/docs/session-14-summary

> **Last Updated:** 2025-12-22
> **Status:** Phase 1 Complete (Core Infrastructure)

***REMOVED******REMOVED*** Scope Clarification

This scheduling system co-schedules **BOTH**:
- 🧑‍⚕️ Residents: 730 half-days/year
- 👨‍🔬 Faculty: 730 half-days/year

Faculty are NOT post-processed. They must be modeled in the solver.

---

***REMOVED******REMOVED*** Implementation Status

| Component | Residents | Faculty | Status |
|-----------|-----------|---------|--------|
| Decision variables | ✅ Yes | ✅ Yes | **Done** |
| `context.*_idx` | ✅ `resident_idx` | ✅ `faculty_idx` | **Done** |
| Constraints applied | ✅ Yes | ✅ Wednesday constraints | **Partial** |
| Solution extraction | ✅ Yes | ✅ Yes | **Done** |

---

***REMOVED******REMOVED*** Implementation Checklist

***REMOVED******REMOVED******REMOVED*** ✅ 1. Add `faculty_idx` to `SchedulingContext`
**File:** `backend/app/scheduling/constraints/base.py`
**Status:** ✅ **COMPLETED** (2025-12-22)

```python
***REMOVED*** Added to SchedulingContext dataclass
faculty_idx: dict[UUID, int] = field(default_factory=dict)

***REMOVED*** Populated in __post_init__
self.faculty_idx = {f.id: i for i, f in enumerate(self.faculty)}
```

***REMOVED******REMOVED******REMOVED*** ✅ 2. Create Faculty Decision Variables (all templates)
**File:** `backend/app/scheduling/solvers.py`
**Status:** ✅ **COMPLETED** (2025-12-22)

Added to both **PuLP** and **CP-SAT** solvers:
- 3D faculty variables: `f[f_i, b_i, t_i]` for each faculty/block/template
- 2D aggregated view: `f_2d[f_i, b_i]` for constraints needing block-level info
- Variables dict entries:
  - `faculty_assignments` → 2D view
  - `faculty_template_assignments` → 3D view
- "At most one rotation per faculty per block" constraint

***REMOVED******REMOVED******REMOVED*** ✅ 3. Update Faculty-Referencing Constraints (Partial)
**Status:** ✅ **COMPLETED for temporal.py** (2025-12-22)

Changed `context.resident_idx.get(f.id)` → `context.faculty_idx.get(f.id)` and
switched to `faculty_template_assignments` in:

| File | Status | Notes |
|------|--------|-------|
| `temporal.py` | ✅ Done | `WednesdayPMSingleFacultyConstraint`, `InvertedWednesdayConstraint` |
| `capacity.py` | ⏳ TODO | `MaxPhysiciansInClinicConstraint` |
| `faculty_role.py` | ⏳ TODO | If using faculty variables |
| `sports_medicine.py` | ⏳ TODO | If using faculty variables |
| `post_call.py` | ⏳ TODO | If using faculty variables |
| `resilience.py` | ⏳ TODO | Hub/Zone/PreferenceTrail/N1 constraints |
| `acgme.py` | ⏳ TODO | `SupervisionRatioConstraint` |

***REMOVED******REMOVED******REMOVED*** ⏳ 4. Bind Faculty to Resident Assignments
**Status:** ⏳ **TODO**

- If residents are assigned to clinic templates, require ≥1 faculty in the same
  block/template (or block, if you choose to aggregate).
- Enforce Wednesday rules against faculty variables (exact counts).

***REMOVED******REMOVED******REMOVED*** ⏳ 5. Add Faculty-Specific Constraints
**Status:** ⏳ **TODO**

**Faculty are NOT residents.** Different rules apply:

| Constraint | Details | Status |
|------------|---------|--------|
| One block per half-day | Can't be in 2 places | ✅ Done (via at-most-one constraint) |
| Availability | Per-faculty calendar | ⏳ TODO |
| **Weekend Call** | Friday AM → Sunday noon | ⏳ TODO (see 5a) |
| No 80-hour rule | N/A | ✅ N/A |
| No one-in-seven | N/A | ✅ N/A |

***REMOVED******REMOVED******REMOVED*** ⏳ 5a. Add Call Decision Variables
**Status:** ⏳ **TODO**

**Faculty call requires separate variables:**
```python
***REMOVED*** In solvers.py
call_vars = {}
for f_i, faculty in enumerate(context.faculty):
    for w_i, weekend in enumerate(weekend_dates):  ***REMOVED*** ~52 weekends
        call_vars[f_i, w_i] = model.NewBoolVar(f"faculty_call_{f_i}_{w_i}")
variables["faculty_call"] = call_vars
```
**Constraints:**
- **FMIT attending auto-assigned** Fri AM → Sun noon for their week
- Other faculty rotate remaining weekends (eligible if not on leave)
- Equitable: each non-FMIT faculty ~same count/year
- If on call, blocked from clinic Friday PM and Monday AM

**Mapping to Assignments:**
```python
***REMOVED*** Extract faculty_call → CallAssignment rows (NOT Assignment)
for f_i, w_i in call_vars:
    if solver.Value(call_vars[f_i, w_i]):
        call_assignments.append(CallAssignment(
            person_id=context.faculty[f_i].id,
            call_type="FACULTY_WEEKEND",  ***REMOVED*** Distinct from resident overnight
            start_date=weekend_dates[w_i].friday,
            end_date=weekend_dates[w_i].sunday_noon,
        ))
```
**Coexistence:** Faculty call is separate from resident overnight call.
- Resident call: `PostCallAutoAssignmentConstraint` (Sun-Thu overnight)
- Faculty call: New constraint (Fri AM - Sun noon, ~52/year)

***REMOVED******REMOVED******REMOVED*** ✅ 6. Extract Faculty Assignments
**File:** `backend/app/scheduling/solvers.py`
**Status:** ✅ **COMPLETED** (2025-12-22)

Added faculty assignment extraction to both PuLP and CP-SAT solvers:
```python
***REMOVED*** After resident extraction
faculty_assignment_count = 0
for faculty in context.faculty:
    f_i = context.faculty_idx[faculty.id]
    for block in workday_blocks:
        b_i = context.block_idx[block.id]
        for template in context.templates:
            t_i = template_idx[template.id]
            if (f_i, b_i, t_i) in f and solver.Value(f[f_i, b_i, t_i]) == 1:
                assignments.append((faculty.id, block.id, template.id))
                faculty_assignment_count += 1
```

Updated statistics to include:
- `total_faculty`: Count of faculty in context
- `resident_assignments`: Count of resident assignments
- `faculty_assignments`: Count of faculty assignments

***REMOVED******REMOVED******REMOVED*** ⏳ 7. Update Tests
**Status:** ⏳ **TODO**

- [ ] Test faculty variables exist
- [ ] Test Wednesday constraints fire with faculty_idx
- [ ] Integration test with mixed resident/faculty
- [ ] Validate faculty assignments appear in outputs/DB

---

***REMOVED******REMOVED*** Completed Work Summary (2025-12-22)

***REMOVED******REMOVED******REMOVED*** Files Modified
| File | Changes |
|------|---------|
| `backend/app/scheduling/constraints/base.py` | Added `faculty_idx` field and population in `__post_init__` |
| `backend/app/scheduling/solvers.py` | Added faculty decision variables (3D+2D) to PuLP and CP-SAT, faculty extraction |
| `backend/app/scheduling/constraints/temporal.py` | Fixed `WednesdayPMSingleFacultyConstraint` and `InvertedWednesdayConstraint` to use `faculty_idx` |

***REMOVED******REMOVED******REMOVED*** Alembic Migration Fixes
Fixed migration chain issues preventing database upgrades:
- `20251221_add_screener_clinic_session_intern_stagger_models.py`: Fixed `down_revision`
- `20251221_add_rotation_halfday_requirements.py`: Fixed `down_revision`
- `20251220_add_gateway_auth_tables.py`: Fixed mismatched revision ID reference

---

***REMOVED******REMOVED*** Remaining Work

***REMOVED******REMOVED******REMOVED*** Phase 2: Additional Constraint Updates
Update remaining constraint files to use `faculty_idx`:
- `capacity.py`
- `faculty_role.py`
- `sports_medicine.py`
- `post_call.py`
- `resilience.py`
- `acgme.py`

***REMOVED******REMOVED******REMOVED*** Phase 3: Faculty Call Implementation
- Add `faculty_call` decision variables for weekend call rotation
- Implement FMIT auto-assignment logic
- Add equity constraints for call distribution
- Create `CallAssignment` extraction

***REMOVED******REMOVED******REMOVED*** Phase 4: Testing
- Unit tests for faculty variables
- Integration tests for Wednesday constraints
- End-to-end solver tests with faculty+residents

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

---

***REMOVED******REMOVED*** Files Impacted

| File | Status | Scope |
|------|--------|-------|
| `solvers.py` | ✅ Done | Major - faculty variables + extraction |
| `base.py` | ✅ Done | Context - faculty_idx |
| `temporal.py` | ✅ Done | Wednesday constraints |
| `capacity.py` | ⏳ TODO | Index fixes |
| `faculty_role.py` | ⏳ TODO | Index fixes |
| `acgme.py` | ⏳ TODO | Index fixes |
| Test files | ⏳ TODO | New tests |
