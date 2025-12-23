***REMOVED*** Faculty Constraints Implementation Plan

> **Created:** 2025-12-19
> **Specification:** [FACULTY_SCHEDULING_SPECIFICATION.md](../architecture/FACULTY_SCHEDULING_SPECIFICATION.md)
> **Status:** Ready for implementation

This document outlines the implementation steps for adding faculty role-based scheduling constraints to the Residency Scheduler.

---

***REMOVED******REMOVED*** Implementation Phases

***REMOVED******REMOVED******REMOVED*** Phase 1: Data Model Updates (Foundation)
***REMOVED******REMOVED******REMOVED*** Phase 2: Core Constraints (FMIT, Clinic Limits)
***REMOVED******REMOVED******REMOVED*** Phase 3: Call System (Equity, Preferences)
***REMOVED******REMOVED******REMOVED*** Phase 4: Coordination (SM Alignment, Post-Call)

---

***REMOVED******REMOVED*** Phase 1: Data Model Updates

***REMOVED******REMOVED******REMOVED*** 1.1 Add Faculty Role Enum and Field

**Files to modify:**
- `backend/app/models/person.py`
- `backend/alembic/versions/` (new migration)

**Changes:**

```python
***REMOVED*** backend/app/models/person.py

class FacultyRole(str, Enum):
    """Faculty role types with specific scheduling constraints."""
    PD = "pd"                    ***REMOVED*** Program Director
    APD = "apd"                  ***REMOVED*** Associate Program Director
    OIC = "oic"                  ***REMOVED*** Officer in Charge
    DEPT_CHIEF = "dept_chief"   ***REMOVED*** Department Chief
    SPORTS_MED = "sports_med"   ***REMOVED*** Sports Medicine
    CORE = "core"               ***REMOVED*** Core Faculty

class Person(Base):
    ***REMOVED*** ... existing fields ...

    ***REMOVED*** New field
    faculty_role = Column(String(50))  ***REMOVED*** FacultyRole enum value
```

**Migration:**
```bash
alembic revision --autogenerate -m "Add faculty_role to Person model"
```

***REMOVED******REMOVED******REMOVED*** 1.2 Add Call Equity Tracking Fields

**Files to modify:**
- `backend/app/models/person.py`
- `backend/alembic/versions/` (new migration)

**Changes:**

```python
***REMOVED*** backend/app/models/person.py

class Person(Base):
    ***REMOVED*** ... existing fields ...

    ***REMOVED*** Call equity tracking (reset annually)
    sunday_call_count = Column(Integer, default=0)
    weekday_call_count = Column(Integer, default=0)  ***REMOVED*** Mon-Thurs
    fmit_weeks_count = Column(Integer, default=0)
```

***REMOVED******REMOVED******REMOVED*** 1.3 Update Schemas

**Files to modify:**
- `backend/app/schemas/person.py`

**Changes:**
- Add `faculty_role` to PersonCreate, PersonUpdate, PersonResponse
- Add call count fields to response schemas

---

***REMOVED******REMOVED*** Phase 2: Core Constraints

***REMOVED******REMOVED******REMOVED*** 2.1 Faculty Role Clinic Constraint

**File to create:**
- `backend/app/scheduling/constraints/faculty_role.py`

**Constraint: `FacultyRoleClinicConstraint`**

```python
"""
Faculty role-based clinic constraints.

Enforces clinic half-day limits by role:
- PD: 0/week
- Dept Chief: 1/week
- APD/OIC: 2/week (flexible within block, total 8/block)
- Sports Med: 0 regular clinic (SM clinic only)
- Core: Max 4/week (16/block)
"""

class FacultyRoleClinicConstraint(HardConstraint):

    ROLE_WEEKLY_LIMITS = {
        FacultyRole.PD: 0,
        FacultyRole.DEPT_CHIEF: 1,
        FacultyRole.APD: 2,
        FacultyRole.OIC: 2,
        FacultyRole.SPORTS_MED: 0,  ***REMOVED*** No regular clinic
        FacultyRole.CORE: 4,
    }

    ROLE_BLOCK_LIMITS = {
        FacultyRole.APD: 8,   ***REMOVED*** Flexible within block
        FacultyRole.OIC: 8,   ***REMOVED*** Flexible within block
        FacultyRole.CORE: 16, ***REMOVED*** Hard max
    }
```

**Implementation tasks:**
1. Create constraint class with `add_to_cpsat`, `add_to_pulp`, `validate` methods
2. Add unit tests in `backend/tests/test_faculty_role_constraint.py`
3. Register constraint in constraint registry

***REMOVED******REMOVED******REMOVED*** 2.2 FMIT Week Blocking Constraint

**File to create:**
- `backend/app/scheduling/constraints/fmit.py`

**Constraint: `FMITWeekBlockingConstraint`**

```python
"""
FMIT week constraints (Fri-Thurs).

Enforces:
- FMIT is half-day activity for ALL blocks during week
- Faculty blocked from clinic during FMIT
- Faculty blocked from Sun-Thurs call during FMIT
- Fri/Sat call mandatory for FMIT attending
- Post-FMIT Friday blocked (recovery)
"""

class FMITWeekBlockingConstraint(HardConstraint):

    def _get_fmit_week_dates(self, any_date: date) -> tuple[date, date]:
        """Get Fri-Thurs week containing the date."""
        ***REMOVED*** Friday = weekday 4
        days_since_friday = (any_date.weekday() - 4) % 7
        friday = any_date - timedelta(days=days_since_friday)
        thursday = friday + timedelta(days=6)
        return friday, thursday
```

**Implementation tasks:**
1. Create constraint class
2. Handle week boundary detection (Fri-Thurs)
3. Integrate with FMIT scheduler service
4. Add validation for mandatory Fri/Sat call
5. Add unit tests

***REMOVED******REMOVED******REMOVED*** 2.3 Post-FMIT Recovery Constraint

**File:** Add to `backend/app/scheduling/constraints/fmit.py`

**Constraint: `PostFMITRecoveryConstraint`**

```python
"""
Post-FMIT Friday is blocked for recovery.
No activities can be scheduled.
"""

class PostFMITRecoveryConstraint(HardConstraint):
    pass
```

---

***REMOVED******REMOVED*** Phase 3: Call System

***REMOVED******REMOVED******REMOVED*** 3.1 FMIT Call Constraint

**File:** Add to `backend/app/scheduling/constraints/fmit.py`

**Constraint: `FMITCallConstraint`**

```python
"""
FMIT attending call rules:
- MANDATORY: Fri night, Sat night call
- BLOCKED: Sun-Thurs call
"""

class FMITCallConstraint(HardConstraint):
    pass
```

***REMOVED******REMOVED******REMOVED*** 3.2 Sunday Call Equity Constraint

**File to create:**
- `backend/app/scheduling/constraints/call_equity.py`

**Constraint: `SundayCallEquityConstraint`**

```python
"""
Track Sunday call separately for equity.
Sunday is the worst call day - distribute fairly.
"""

class SundayCallEquityConstraint(SoftConstraint):
    pass
```

***REMOVED******REMOVED******REMOVED*** 3.3 Tuesday Call Preference Constraint

**File:** Add to `backend/app/scheduling/constraints/call_equity.py`

**Constraint: `TuesdayCallPreferenceConstraint`**

```python
"""
Soft preference: Avoid PD and APD on Tuesday call.
Reason: Academic commitments (teaching, conferences).
"""

class TuesdayCallPreferenceConstraint(SoftConstraint):

    AVOID_TUESDAY_ROLES = [FacultyRole.PD, FacultyRole.APD]
```

***REMOVED******REMOVED******REMOVED*** 3.4 Department Chief Wednesday Preference

**File:** Add to `backend/app/scheduling/constraints/call_equity.py`

**Constraint: `DeptChiefWednesdayPreferenceConstraint`**

```python
"""
Soft preference: Dept Chief prefers Wednesday call.
Personal preference - lowest priority.
"""

class DeptChiefWednesdayPreferenceConstraint(SoftConstraint):
    pass
```

---

***REMOVED******REMOVED*** Phase 4: Coordination Constraints

***REMOVED******REMOVED******REMOVED*** 4.1 Sports Medicine Alignment Constraint

**File to create:**
- `backend/app/scheduling/constraints/sports_medicine.py`

**Constraint: `SMResidentFacultyAlignmentConstraint`**

```python
"""
HARD CONSTRAINT: SM residents must be scheduled in SM clinic
at the same time as Sports Medicine faculty.

Rationale: Residents see faculty's patients under supervision
for specialized procedures and ultrasound.
"""

class SMResidentFacultyAlignmentConstraint(HardConstraint):

    def add_to_cpsat(self, model, variables, context):
        """
        For each SM clinic block:
        - If SM resident assigned → SM faculty must be assigned
        - If SM faculty assigned → SM resident should be assigned (soft?)
        """
        pass
```

**Implementation considerations:**
- Need to identify SM rotation vs rotations with SM components
- Cross-reference `rotation_template.requires_specialty` with `person.specialties`
- May need to track SM faculty availability separately

***REMOVED******REMOVED******REMOVED*** 4.2 Post-Call Auto-Assignment Constraint

**File to create:**
- `backend/app/scheduling/constraints/post_call.py`

**Constraint: `PostCallAutoAssignmentConstraint`**

```python
"""
Auto-assign activities after overnight call (Sun-Thurs):
- AM block: PCAT (Post-Call Attending)
- PM block: DO (Direct Observation)
"""

class PostCallAutoAssignmentConstraint(HardConstraint):

    def add_to_cpsat(self, model, variables, context):
        """
        For each Sun-Thurs overnight call assignment:
        1. Next day AM → force PCAT activity
        2. Next day PM → force DO activity
        """
        pass
```

**New activity types needed:**
- Add `PCAT` and `DO` to activity type enum or rotation templates

---

***REMOVED******REMOVED*** File Structure Summary

***REMOVED******REMOVED******REMOVED*** New Files to Create

```
backend/app/scheduling/constraints/
├── faculty_role.py          ***REMOVED*** Phase 2.1 - Role-based clinic limits
├── fmit.py                   ***REMOVED*** Phase 2.2, 2.3, 3.1 - FMIT blocking/call
├── call_equity.py            ***REMOVED*** Phase 3.2, 3.3, 3.4 - Call preferences
├── sports_medicine.py        ***REMOVED*** Phase 4.1 - SM alignment
└── post_call.py              ***REMOVED*** Phase 4.2 - PCAT/DO auto-assignment

backend/tests/
├── test_faculty_role_constraint.py
├── test_fmit_constraints.py
├── test_call_equity_constraints.py
├── test_sports_medicine_constraint.py
└── test_post_call_constraint.py
```

***REMOVED******REMOVED******REMOVED*** Files to Modify

```
backend/app/models/person.py           ***REMOVED*** Add faculty_role, call counts
backend/app/schemas/person.py          ***REMOVED*** Update schemas
backend/alembic/versions/              ***REMOVED*** New migrations
backend/app/scheduling/constraints/__init__.py  ***REMOVED*** Register new constraints
backend/app/models/rotation_template.py  ***REMOVED*** May need PCAT/DO activity types
```

---

***REMOVED******REMOVED*** Implementation Order

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Data Model (MUST BE FIRST)                         │
│  1.1 Add faculty_role field + migration                     │
│  1.2 Add call equity fields + migration                     │
│  1.3 Update schemas                                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Core Constraints (FOUNDATION)                      │
│  2.1 FacultyRoleClinicConstraint                           │
│  2.2 FMITWeekBlockingConstraint                            │
│  2.3 PostFMITRecoveryConstraint                            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Call System (DEPENDS ON PHASE 2)                   │
│  3.1 FMITCallConstraint                                     │
│  3.2 SundayCallEquityConstraint                            │
│  3.3 TuesdayCallPreferenceConstraint                       │
│  3.4 DeptChiefWednesdayPreferenceConstraint                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 4: Coordination (CAN PARALLELIZE WITH PHASE 3)        │
│  4.1 SMResidentFacultyAlignmentConstraint                  │
│  4.2 PostCallAutoAssignmentConstraint                      │
└─────────────────────────────────────────────────────────────┘
```

---

***REMOVED******REMOVED*** Testing Strategy

***REMOVED******REMOVED******REMOVED*** Unit Tests (per constraint)

Each constraint needs tests for:
1. `add_to_cpsat` - Constraint added correctly to OR-Tools model
2. `add_to_pulp` - Constraint added correctly to PuLP model
3. `validate` - Correct violations detected

***REMOVED******REMOVED******REMOVED*** Integration Tests

1. **Full schedule generation** with all new constraints active
2. **Constraint interaction** - Verify constraints don't conflict
3. **Edge cases**:
   - FMIT week spanning block boundary
   - SM faculty on FMIT (who covers SM clinic?)
   - Multiple faculty with same role

***REMOVED******REMOVED******REMOVED*** Validation Tests

1. Role clinic limits enforced
2. FMIT blocking works correctly
3. Post-call assignments generated
4. SM alignment maintained
5. Call equity tracked

---

***REMOVED******REMOVED*** Migration Strategy

***REMOVED******REMOVED******REMOVED*** Step 1: Schema Migration
```bash
cd backend
alembic revision --autogenerate -m "Add faculty_role and call_equity fields"
alembic upgrade head
```

***REMOVED******REMOVED******REMOVED*** Step 2: Data Population
- Create script to set `faculty_role` for existing faculty
- Initialize call counts to 0

***REMOVED******REMOVED******REMOVED*** Step 3: Constraint Registration
- Add new constraints to registry
- Enable incrementally (one at a time) for testing

***REMOVED******REMOVED******REMOVED*** Step 4: Validation
- Run scheduler with new constraints on test data
- Verify no regressions in existing functionality

---

***REMOVED******REMOVED*** Estimated Effort

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 1 | 2-3 hours | None |
| Phase 2 | 4-6 hours | Phase 1 |
| Phase 3 | 3-4 hours | Phase 2 |
| Phase 4 | 4-5 hours | Phase 1, 2 |
| Testing | 4-6 hours | All phases |
| **Total** | **17-24 hours** | |

---

***REMOVED******REMOVED*** Open Questions for Implementation

1. **SM faculty on FMIT**: When SM faculty is on FMIT, who covers SM clinic?
   - Option A: SM clinic cancelled that week
   - Option B: Another faculty with SM specialty covers
   - **Recommendation**: Flag as conflict, require manual resolution

2. **PCAT/DO activity types**: Create as new rotation templates or special activity flags?
   - **Recommendation**: Create dedicated rotation templates for clarity

3. **Call assignment model**: Current `CallAssignment` model sufficient?
   - May need to add `is_fmit_mandatory` flag
   - May need separate Sunday tracking field

4. **Constraint priority tuning**: What weights for soft constraints?
   - Tuesday avoidance vs Wednesday preference vs equity
   - **Recommendation**: Make configurable in settings

---

***REMOVED******REMOVED*** References

- [Faculty Scheduling Specification](../architecture/FACULTY_SCHEDULING_SPECIFICATION.md)
- [ACGME Constraints](../../backend/app/scheduling/constraints/acgme.py)
- [Existing Temporal Constraints](../../backend/app/scheduling/constraints/temporal.py)
- [FMIT Scheduler Service](../../backend/app/services/fmit_scheduler_service.py)
