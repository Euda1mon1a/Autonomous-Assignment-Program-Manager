# Overnight Call Processing Architecture

> **Last Updated:** 2025-12-27
> **Status:** Implemented
> **Related PRs:** #470, #472 (unified)

---

## Overview

Overnight faculty call is managed through a solver-integrated constraint system that optimizes call assignments as part of the scheduling process. This approach ensures call assignments respect all other scheduling constraints (availability, ACGME compliance, workload equity) while maintaining required coverage.

---

## Coverage Pattern

### Weeknight Call (Solver-Generated)

| Night | Weekday | Coverage |
|-------|---------|----------|
| Sunday | 6 | Faculty overnight call |
| Monday | 0 | Faculty overnight call |
| Tuesday | 1 | Faculty overnight call |
| Wednesday | 2 | Faculty overnight call |
| Thursday | 3 | Faculty overnight call |

### Weekend Call (FMIT-Managed)

| Night | Coverage |
|-------|----------|
| Friday | FMIT faculty (pre-assigned) |
| Saturday | FMIT faculty (pre-assigned) |

Friday-Saturday call is **not solver-generated** - it's covered by the FMIT faculty as part of their inpatient week.

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer                                 │
│  /call-assignments endpoints with RBAC                          │
│  • Read: Any authenticated user                                 │
│  • Write: ADMIN, COORDINATOR, FACULTY                          │
│  • Reports: ADMIN, COORDINATOR                                  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                     Controller Layer                             │
│  CallAssignmentController                                        │
│  • Request/response handling                                     │
│  • Error translation to HTTP                                     │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                      Service Layer                               │
│  CallAssignmentService (async SQLAlchemy 2.0)                   │
│  • CRUD operations                                               │
│  • Coverage/equity reporting                                     │
│  • N+1 optimization with selectinload                           │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                    Constraint Layer                              │
│  OvernightCallCoverageConstraint (Hard)                         │
│  • Exactly one faculty per Sun-Thu night                        │
│  AdjunctCallExclusionConstraint (Hard)                          │
│  • Adjuncts excluded from solver optimization                   │
│  CallAvailabilityConstraint (Hard)                              │
│  • Respects faculty availability/absences                       │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                      Solver Layer                                │
│  PuLPSolver / CPSATSolver                                        │
│  • call[f_i, b_i, "overnight"] decision variables               │
│  • Integrated with other constraints                             │
│  • Returns SolverResult.call_assignments                        │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                      Engine Layer                                │
│  SchedulingEngine._create_call_assignments_from_result()        │
│  • Converts solver output to CallAssignment records             │
│  • Persists to database                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Constraint System

### Modular Constraint Trio

The overnight call system uses three modular hard constraints:

#### 1. OvernightCallCoverageConstraint

**Purpose:** Ensures exactly one faculty member is assigned overnight call for each Sun-Thu night.

```python
# Constraint: sum of all faculty call vars for this date == 1
for date in overnight_call_dates:
    model.Add(sum(call[f_i, b_i, "overnight"] for f_i in eligible) == 1)
```

**Validation:** Reports violations for uncovered nights or double-bookings.

#### 2. AdjunctCallExclusionConstraint

**Purpose:** Prevents adjunct faculty from being auto-assigned call.

```python
# Constraint: adjunct call vars forced to 0
if faculty.faculty_role == "ADJUNCT":
    model.Add(call[f_i, b_i, "overnight"] == 0)
```

**Rationale:** Adjuncts can be manually added to call after solver runs, but the solver should not depend on their availability for coverage.

#### 3. CallAvailabilityConstraint

**Purpose:** Blocks call assignment when faculty is unavailable.

```python
# Constraint: call blocked when unavailable
if not availability[faculty_id][block_id]["available"]:
    model.Add(call[f_i, b_i, "overnight"] == 0)
```

**Sources of unavailability:**
- Approved leave/absences
- FMIT week assignments
- Other blocking commitments

---

## Solver Integration

### Variable Creation

Call assignment variables are created in both PuLP and CP-SAT solvers:

```python
# In solver.solve()
call = {}
call_eligible = context.call_eligible_faculty
call_idx = context.call_eligible_faculty_idx

for block in workday_blocks:
    if block.date.weekday() not in OVERNIGHT_CALL_DAYS:
        continue
    b_i = context.block_idx[block.id]
    for faculty in call_eligible:
        f_i = call_idx[faculty.id]
        call[f_i, b_i, "overnight"] = model.NewBoolVar(f"call_{f_i}_{b_i}")

variables["call_assignments"] = call
```

### Solution Extraction

```python
call_assignments_result = []
for (f_i, b_i, call_type), var in call.items():
    if solver.Value(var) == 1:
        call_assignments_result.append((faculty_id, block_id, call_type))

return SolverResult(..., call_assignments=call_assignments_result)
```

---

## Integration with Existing Constraints

The call system integrates with existing constraints from `call_equity.py`:

| Constraint | Type | Weight | Purpose |
|------------|------|--------|---------|
| `SundayCallEquityConstraint` | Soft | 10.0 | Balance Sunday call distribution |
| `WeekdayCallEquityConstraint` | Soft | 5.0 | Balance Mon-Thu call distribution |
| `TuesdayCallPreferenceConstraint` | Soft | 3.0 | PD/APD avoid Tuesday |
| `CallSpacingConstraint` | Soft | 4.0 | Prevent back-to-back call weeks |
| `DeptChiefWednesdayPreferenceConstraint` | Soft | 2.0 | Dept chief Wednesday preference |

---

## SchedulingContext Fields

The `SchedulingContext` dataclass includes call-related fields:

```python
@dataclass
class SchedulingContext:
    # ... other fields ...

    # Call-eligible faculty (excludes adjuncts)
    call_eligible_faculty: list = field(default_factory=list)
    call_eligible_faculty_idx: dict[UUID, int] = field(default_factory=dict)
```

Built in `__post_init__`:
```python
self.call_eligible_faculty_idx = {
    f.id: i for i, f in enumerate(self.call_eligible_faculty)
}
```

---

## Database Model

```python
class CallAssignment(Base):
    __tablename__ = "call_assignments"

    id = Column(GUID(), primary_key=True)
    date = Column(Date, nullable=False)
    person_id = Column(GUID(), ForeignKey("people.id"))
    call_type = Column(String(50))  # 'overnight', 'weekend', 'backup'
    is_weekend = Column(Boolean, default=False)
    is_holiday = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("date", "person_id", "call_type"),
    )
```

---

## Reporting

### Coverage Report

Identifies gaps where no overnight call is assigned:

```json
{
  "total_expected_nights": 22,
  "covered_nights": 20,
  "coverage_percentage": 90.91,
  "gaps": ["2025-01-15", "2025-01-22"]
}
```

### Equity Report

Tracks distribution with Sunday calls separated (Sunday is considered the "worst" call day):

```json
{
  "sunday_call_stats": {"min": 0, "max": 2, "mean": 0.75, "stdev": 0.5},
  "weekday_call_stats": {"min": 2, "max": 4, "mean": 2.75, "stdev": 0.71},
  "distribution": [
    {"name": "Dr. Smith", "sunday_calls": 2, "weekday_calls": 3, "total_calls": 5}
  ]
}
```

---

## FMIT Coordination

The overnight call system respects FMIT constraints:

1. **FMITWeekBlockingConstraint**: Faculty on FMIT week cannot take overnight call
2. **PostFMITSundayBlockingConstraint**: No Sunday call immediately after FMIT week
3. **FMITMandatoryCallConstraint**: FMIT faculty cover Fri-Sat (not solver-generated)

---

## File Reference

| File | Purpose |
|------|---------|
| `constraints/call_coverage.py` | Modular constraint trio |
| `constraints/call_equity.py` | Soft equity constraints |
| `solvers.py` | Call variable creation/extraction |
| `engine.py` | Call-eligible faculty, persistence |
| `services/call_assignment_service.py` | Async service layer |
| `controllers/call_assignment_controller.py` | Request handling |
| `api/routes/call_assignments.py` | REST endpoints |
| `schemas/call_assignment.py` | Pydantic schemas |
| `models/call_assignment.py` | SQLAlchemy model |

---

## Related Documentation

- [SOLVER_ALGORITHM.md](SOLVER_ALGORITHM.md) - Core solver architecture
- [FMIT_CONSTRAINTS.md](FMIT_CONSTRAINTS.md) - FMIT week handling
- [cross-disciplinary-resilience.md](cross-disciplinary-resilience.md) - Resilience framework
