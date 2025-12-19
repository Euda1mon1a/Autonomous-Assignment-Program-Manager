***REMOVED*** Constraints Integration Guide

> **Purpose:** How to wire up and use the faculty scheduling constraints implemented in Phases 1-4.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Scheduling Engine                                │
│                  (backend/app/scheduling/engine.py)                  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Constraint Registry                               │
│           (backend/app/scheduling/constraints/__init__.py)           │
├─────────────────────────────────────────────────────────────────────┤
│  HARD CONSTRAINTS (must satisfy)                                     │
│  ├── FacultyRoleClinicConstraint      (role-based clinic limits)    │
│  ├── SMFacultyClinicConstraint        (SM blocked from regular)     │
│  ├── FMITWeekBlockingConstraint       (no clinic/call during FMIT)  │
│  ├── FMITMandatoryCallConstraint      (Fri/Sat call required)       │
│  ├── PostFMITRecoveryConstraint       (Friday blocked after FMIT)   │
│  ├── SMResidentFacultyAlignmentConstraint  (SM resident+faculty)    │
│  └── PostCallAutoAssignmentConstraint (PCAT AM, DO PM)              │
├─────────────────────────────────────────────────────────────────────┤
│  SOFT CONSTRAINTS (optimization weights)                             │
│  ├── SundayCallEquityConstraint       (weight: 10.0)                │
│  ├── WeekdayCallEquityConstraint      (weight: 5.0)                 │
│  ├── TuesdayCallPreferenceConstraint  (weight: 2.0, PD/APD avoid)   │
│  └── DeptChiefWednesdayPreferenceConstraint (weight: 1.0, bonus)    │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Data Model                                      │
│              (backend/app/models/person.py)                          │
├─────────────────────────────────────────────────────────────────────┤
│  Person                                                              │
│  ├── faculty_role: FacultyRole (pd, apd, oic, dept_chief, sm, core) │
│  ├── sunday_call_count: int                                         │
│  ├── weekday_call_count: int                                        │
│  └── fmit_weeks_count: int                                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites Checklist

Before the constraints will work correctly, ensure:

### 1. Database Migration Applied
```bash
cd backend
alembic upgrade head
```

This applies migration `018_add_faculty_role_and_call_equity.py`.

### 2. Faculty Roles Assigned

Each faculty member needs their `faculty_role` set:

```python
from app.models.person import FacultyRole

# Example: Assign roles to faculty
pd.faculty_role = FacultyRole.PD
apd.faculty_role = FacultyRole.APD
oic.faculty_role = FacultyRole.OIC
dept_chief.faculty_role = FacultyRole.DEPT_CHIEF
sm_faculty.faculty_role = FacultyRole.SPORTS_MED
core_faculty.faculty_role = FacultyRole.CORE
```

**Expected roster:**
| Role | Count | Weekly Clinic Limit |
|------|-------|---------------------|
| PD | 1 | 0 half-days |
| APD | 1 | 2 half-days |
| OIC | 1 | 2 half-days |
| Dept Chief | 1 | 1 half-day |
| Sports Med | 1 | 0 (4 SM clinic only) |
| Core Faculty | 4 | 4 half-days each |

### 3. Required Rotation Templates

These templates must exist in the database for constraints to reference:

| Template Name | Abbreviation | Purpose |
|---------------|--------------|---------|
| `PCAT` or `Post-Call Attending` | `PCAT` | Morning after overnight call |
| `DO` or `Direct Observation` | `DO` | Afternoon after overnight call |
| `Sports Medicine Clinic` | `SM` | SM-specific clinic (requires SM faculty) |
| `FMIT` | `FMIT` | Inpatient teaching week |

**How templates are detected:**
- By `name` containing the activity name
- By `abbreviation` field matching
- By `requires_specialty` = "Sports Medicine" (for SM clinic)

### 4. Block Structure

The system expects:
- Blocks with `date` and `time_of_day` ("AM" or "PM")
- 730 blocks per academic year (365 days × 2 sessions)

---

## Wiring Up Constraints

### Option A: Register All Constraints (Recommended)

In your scheduling engine initialization:

```python
from app.scheduling.constraints import (
    # Phase 2: Core constraints
    FacultyRoleClinicConstraint,
    SMFacultyClinicConstraint,
    FMITWeekBlockingConstraint,
    FMITMandatoryCallConstraint,
    PostFMITRecoveryConstraint,
    # Phase 3: Call equity
    SundayCallEquityConstraint,
    WeekdayCallEquityConstraint,
    TuesdayCallPreferenceConstraint,
    DeptChiefWednesdayPreferenceConstraint,
    # Phase 4: SM alignment and post-call
    SMResidentFacultyAlignmentConstraint,
    PostCallAutoAssignmentConstraint,
)

class SchedulingEngine:
    def __init__(self):
        self.constraints = [
            # Hard constraints (order doesn't matter for CP-SAT)
            FacultyRoleClinicConstraint(),
            SMFacultyClinicConstraint(),
            FMITWeekBlockingConstraint(),
            FMITMandatoryCallConstraint(),
            PostFMITRecoveryConstraint(),
            SMResidentFacultyAlignmentConstraint(),
            PostCallAutoAssignmentConstraint(),
            # Soft constraints (weights determine priority)
            SundayCallEquityConstraint(),
            WeekdayCallEquityConstraint(),
            TuesdayCallPreferenceConstraint(),
            DeptChiefWednesdayPreferenceConstraint(),
        ]
```

### Option B: Selective Constraint Loading

For testing or gradual rollout:

```python
def get_active_constraints(config: dict) -> list:
    """Load constraints based on configuration."""
    constraints = []

    if config.get("enable_faculty_role_limits", True):
        constraints.append(FacultyRoleClinicConstraint())
        constraints.append(SMFacultyClinicConstraint())

    if config.get("enable_fmit_constraints", True):
        constraints.extend([
            FMITWeekBlockingConstraint(),
            FMITMandatoryCallConstraint(),
            PostFMITRecoveryConstraint(),
        ])

    if config.get("enable_call_equity", True):
        constraints.extend([
            SundayCallEquityConstraint(),
            WeekdayCallEquityConstraint(),
        ])

    # ... etc
    return constraints
```

---

## Constraint Interactions

### FMIT Week Flow

```
Friday (FMIT starts)
├── FMIT faculty: Mandatory Friday night call
├── SM clinic: CANCELLED (SM faculty on FMIT)
└── Other faculty: Normal schedule

Saturday
├── FMIT faculty: Mandatory Saturday night call
└── Other faculty: Normal schedule

Sunday - Thursday
├── FMIT faculty: BLOCKED from clinic and call
├── Overnight call: Covered by non-FMIT faculty
└── Post-call next day: PCAT (AM) + DO (PM)

Following Friday
└── FMIT faculty: BLOCKED entirely (recovery)
```

### Post-Call Assignment Flow

```
Sun/Mon/Tue/Wed/Thu night call
         │
         ▼
    Next day AM ──────► PCAT assignment
         │
         ▼
    Next day PM ──────► DO assignment
```

### SM Clinic Flow

```
SM Clinic Block
      │
      ├── SM Resident assigned?
      │         │
      │         ▼
      │    SM Faculty MUST be assigned
      │
      └── Regular resident assigned?
                │
                ▼
           No SM constraint
```

---

## Call Equity Tracking

### Updating Counters After Scheduling

After a schedule is generated and accepted, update equity counters:

```python
async def update_call_equity_counters(
    db: AsyncSession,
    assignments: list[Assignment]
) -> None:
    """Update faculty call counts after schedule generation."""
    for assignment in assignments:
        if not assignment.is_call:
            continue

        faculty = await db.get(Person, assignment.person_id)
        if not faculty or faculty.role != "FACULTY":
            continue

        call_date = assignment.block.date
        if call_date.weekday() == 6:  # Sunday
            faculty.sunday_call_count += 1
        else:
            faculty.weekday_call_count += 1

    await db.commit()
```

### Querying Current Equity State

```python
async def get_call_equity_report(db: AsyncSession) -> dict:
    """Get call distribution across faculty."""
    result = await db.execute(
        select(Person)
        .where(Person.role == "FACULTY")
        .where(Person.faculty_role.isnot(None))
    )
    faculty = result.scalars().all()

    return {
        f.name: {
            "role": f.faculty_role,
            "sunday_calls": f.sunday_call_count,
            "weekday_calls": f.weekday_call_count,
            "fmit_weeks": f.fmit_weeks_count,
        }
        for f in faculty
    }
```

---

## Testing Recommendations

### Unit Testing Individual Constraints

```bash
# Run all constraint tests
cd backend
pytest tests/test_faculty_role.py -v
pytest tests/test_fmit_constraints.py -v
pytest tests/test_call_equity_constraints.py -v
pytest tests/test_phase4_constraints.py -v
```

### Integration Testing

Create test scenarios covering:

1. **FMIT week with SM faculty**
   - Verify SM clinic cancelled
   - Verify Fri/Sat call assigned to FMIT attending
   - Verify Sun-Thurs call assigned to others
   - Verify Friday recovery blocked

2. **Post-call assignments**
   - Verify PCAT assigned morning after call
   - Verify DO assigned afternoon after call
   - Verify both skip Friday/Saturday call (handled by FMIT)

3. **SM resident alignment**
   - Verify SM resident cannot be in SM clinic without SM faculty
   - Verify regular residents can be in SM clinic

4. **Call equity over time**
   - Run multiple scheduling cycles
   - Verify Sunday/weekday counts balance
   - Verify PD/APD avoid Tuesday
   - Verify Dept Chief gets Wednesday when possible

### Smoke Test Script

```python
"""Quick validation that constraints load correctly."""
from app.scheduling.constraints import (
    FacultyRoleClinicConstraint,
    SMFacultyClinicConstraint,
    FMITWeekBlockingConstraint,
    FMITMandatoryCallConstraint,
    PostFMITRecoveryConstraint,
    SundayCallEquityConstraint,
    WeekdayCallEquityConstraint,
    TuesdayCallPreferenceConstraint,
    DeptChiefWednesdayPreferenceConstraint,
    SMResidentFacultyAlignmentConstraint,
    PostCallAutoAssignmentConstraint,
)

def test_constraints_instantiate():
    """Verify all constraints can be instantiated."""
    constraints = [
        FacultyRoleClinicConstraint(),
        SMFacultyClinicConstraint(),
        FMITWeekBlockingConstraint(),
        FMITMandatoryCallConstraint(),
        PostFMITRecoveryConstraint(),
        SundayCallEquityConstraint(),
        WeekdayCallEquityConstraint(),
        TuesdayCallPreferenceConstraint(),
        DeptChiefWednesdayPreferenceConstraint(),
        SMResidentFacultyAlignmentConstraint(),
        PostCallAutoAssignmentConstraint(),
    ]

    for c in constraints:
        print(f"✓ {c.name}: {c.__class__.__bases__[0].__name__}")

    print(f"\nTotal: {len(constraints)} constraints loaded")

if __name__ == "__main__":
    test_constraints_instantiate()
```

---

## Remaining Considerations

### 1. Template Creation
PCAT and DO templates may need to be created in the database if they don't exist. The constraint will skip validation if templates aren't found (logs a warning).

### 2. Solver Configuration
For large schedules, consider CP-SAT solver time limits:
```python
solver.parameters.max_time_in_seconds = 300  # 5 minutes
```

### 3. Constraint Weights Tuning
Soft constraint weights may need adjustment based on real-world results:
- Sunday equity (10.0) > Weekday equity (5.0) > Tuesday avoidance (2.0) > Wednesday bonus (1.0)

### 4. FMIT Week Assignment
The system assumes FMIT weeks are pre-assigned to faculty. You'll need:
- A way to designate which faculty has FMIT each week
- Possibly a separate FMIT assignment model or flag on assignments

### 5. Resident Specialty Tracking
For SM resident detection, ensure residents have:
- A `specialty` or `track` field indicating "Sports Medicine"
- Or use rotation history to identify SM-track residents

### 6. Audit Trail
Consider logging constraint violations for review:
```python
# In scheduling service
for constraint in constraints:
    result = constraint.validate(assignments, context)
    if not result.satisfied:
        logger.warning(f"Constraint {constraint.name} violated: {result.violations}")
```

---

## Quick Reference: Constraint Priority

| Priority | Value | Constraints |
|----------|-------|-------------|
| CRITICAL | 100 | (ACGME compliance) |
| HIGH | 75 | FacultyRoleClinic, FMIT*, SM Alignment, PostCall |
| MEDIUM | 50 | SundayCallEquity, WeekdayCallEquity |
| LOW | 25 | TuesdayPreference, WednesdayPreference |

---

## File Locations

| Purpose | File |
|---------|------|
| Data model | `backend/app/models/person.py` |
| Migration | `backend/alembic/versions/018_add_faculty_role_and_call_equity.py` |
| Role constraints | `backend/app/scheduling/constraints/faculty_role.py` |
| FMIT constraints | `backend/app/scheduling/constraints/fmit.py` |
| Call equity | `backend/app/scheduling/constraints/call_equity.py` |
| SM alignment | `backend/app/scheduling/constraints/sports_medicine.py` |
| Post-call | `backend/app/scheduling/constraints/post_call.py` |
| Constraint registry | `backend/app/scheduling/constraints/__init__.py` |
| Specification | `docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md` |
| Implementation plan | `docs/planning/FACULTY_CONSTRAINTS_IMPLEMENTATION_PLAN.md` |

---

*Last updated: 2025-12-19*
