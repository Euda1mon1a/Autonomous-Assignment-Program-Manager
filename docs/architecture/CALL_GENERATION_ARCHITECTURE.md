# Call Generation Architecture

> **Last Updated:** 2025-12-26
> **Module:** `backend/app/scheduling/`

---

## System Overview

The overnight call generation system is integrated into the constraint-based scheduling engine. It creates binary decision variables for each eligible faculty member and date, then uses hard constraints to ensure coverage and soft constraints to optimize equity.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SCHEDULING ENGINE                               │
│                                                                      │
│  ┌──────────────┐    ┌─────────────────┐    ┌───────────────────┐  │
│  │   Faculty    │───▶│  _get_call_     │───▶│ SchedulingContext │  │
│  │   (all)      │    │  eligible_      │    │ .call_eligible_   │  │
│  │              │    │  faculty()      │    │  faculty          │  │
│  └──────────────┘    └─────────────────┘    └─────────┬─────────┘  │
│                                                        │            │
│                                                        ▼            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                        SOLVER                                │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │  Call Variable Creation                              │    │   │
│  │  │  call[(f_i, b_i, "overnight")] = BoolVar            │    │   │
│  │  │  for each faculty × Sun-Thurs date                   │    │   │
│  │  └──────────────────────┬──────────────────────────────┘    │   │
│  │                         │                                    │   │
│  │                         ▼                                    │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │  Hard Constraints                                    │    │   │
│  │  │  • OvernightCallCoverage (exactly 1 per night)      │    │   │
│  │  │  • AdjunctCallExclusion (block adjuncts)            │    │   │
│  │  │  • CallAvailability (respect absences)              │    │   │
│  │  └──────────────────────┬──────────────────────────────┘    │   │
│  │                         │                                    │   │
│  │                         ▼                                    │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │  Soft Constraints (Optimization)                     │    │   │
│  │  │  • SundayCallEquity (weight=10)                      │    │   │
│  │  │  • WeekdayCallEquity (weight=5)                      │    │   │
│  │  │  • CallSpacing (weight=8)                            │    │   │
│  │  │  • TuesdayCallPreference (weight=2)                  │    │   │
│  │  └──────────────────────┬──────────────────────────────┘    │   │
│  │                         │                                    │   │
│  │                         ▼                                    │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │  Solution Extraction                                 │    │   │
│  │  │  SolverResult.call_assignments = [                  │    │   │
│  │  │    (person_id, block_id, "overnight"), ...          │    │   │
│  │  │  ]                                                   │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│                                      │                               │
│                                      ▼                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  _create_call_assignments_from_result()                      │   │
│  │  • Convert (person_id, block_id, call_type) to ORM          │   │
│  │  • Set is_weekend flag for Sunday                            │   │
│  │  • Add to database session                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                         ┌─────────────────────┐
                         │  call_assignments   │
                         │     (database)      │
                         └─────────────────────┘
                                      │
                                      ▼
                         ┌─────────────────────┐
                         │  API / Reports      │
                         └─────────────────────┘
```

## Component Details

### 1. SchedulingContext Extension

**File:** `backend/app/scheduling/constraints/base.py`

```python
@dataclass
class SchedulingContext:
    # ... existing fields ...

    # Call Assignment Data (for overnight call generation)
    call_eligible_faculty: list = field(default_factory=list)
    call_eligible_faculty_idx: dict[UUID, int] = field(default_factory=dict)
    existing_call_assignments: list = field(default_factory=list)
```

The context is populated in `__post_init__()` with indexed lookups for fast constraint evaluation.

### 2. Engine Integration

**File:** `backend/app/scheduling/engine.py`

```python
def _get_call_eligible_faculty(self, faculty: list[Person]) -> list[Person]:
    """Get faculty eligible for call (excludes adjuncts)."""
    return [
        f for f in faculty
        if f.faculty_role != FacultyRole.ADJUNCT.value
    ]

def _build_context(self, residents, faculty, blocks, templates, ...):
    call_eligible = self._get_call_eligible_faculty(faculty)
    context = SchedulingContext(
        ...,
        call_eligible_faculty=call_eligible,
    )
    return context

def _create_call_assignments_from_result(
    self, result: SolverResult, context: SchedulingContext
) -> list[CallAssignment]:
    """Convert solver results to database records."""
    block_by_id = {b.id: b for b in context.blocks}
    for person_id, block_id, call_type in result.call_assignments:
        block = block_by_id[block_id]
        call = CallAssignment(
            date=block.date,
            person_id=person_id,
            call_type=call_type,
            is_weekend=(block.date.weekday() == 6),
        )
        self.db.add(call)
```

### 3. Solver Variable Creation

**File:** `backend/app/scheduling/solvers.py`

Both CP-SAT and PuLP solvers create call variables:

```python
# CP-SAT Solver
call = {}
call_eligible = getattr(context, "call_eligible_faculty", [])
call_idx = getattr(context, "call_eligible_faculty_idx", {})

if call_eligible:
    call_dates_processed = set()
    for block in workday_blocks:
        if block.date.weekday() not in (0, 1, 2, 3, 6):  # Skip Fri-Sat
            continue
        if block.date in call_dates_processed:
            continue
        call_dates_processed.add(block.date)

        b_i = context.block_idx[block.id]
        for faculty in call_eligible:
            f_i = call_idx.get(faculty.id)
            if f_i is not None:
                call[f_i, b_i, "overnight"] = model.NewBoolVar(f"call_{f_i}_{b_i}")

variables["call_assignments"] = call
```

### 4. Solution Extraction

```python
# Extract call assignments from solution
call_assignments_result = []
for (f_i, b_i, call_type), var in call.items():
    if solver.Value(var) == 1:
        faculty_id = # lookup from call_eligible
        block_id = # lookup from blocks
        call_assignments_result.append((faculty_id, block_id, call_type))

return SolverResult(
    ...,
    call_assignments=call_assignments_result,
)
```

## Database Model

**File:** `backend/app/models/call_assignment.py`

```python
class CallAssignment(Base):
    __tablename__ = "call_assignments"

    id = Column(GUID(), primary_key=True, default=uuid4)
    date = Column(Date, nullable=False)
    person_id = Column(GUID(), ForeignKey("people.id", ondelete="CASCADE"))
    call_type = Column(String(50), nullable=False)  # 'overnight', 'weekend', 'backup'
    is_weekend = Column(Boolean, default=False)
    is_holiday = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    person = relationship("Person", back_populates="call_assignments")

    # Constraints
    UniqueConstraint("date", "person_id", "call_type")
    CheckConstraint("call_type IN ('overnight', 'weekend', 'backup')")
```

## Variable Naming Convention

Call variables use a tuple key for efficient constraint access:

```python
call[(faculty_idx, block_idx, call_type)]
```

- **faculty_idx**: Index in `call_eligible_faculty` list (NOT all faculty)
- **block_idx**: Index in `context.blocks` list
- **call_type**: String literal, typically `"overnight"`

## Constraint Registration

**File:** `backend/app/scheduling/constraints/manager.py`

```python
# In create_default():
manager.add(OvernightCallCoverageConstraint())
manager.add(AdjunctCallExclusionConstraint())
manager.add(CallAvailabilityConstraint())

# Call equity constraints (already existed):
manager.add(SundayCallEquityConstraint(weight=10.0))
manager.add(CallSpacingConstraint(weight=8.0))
manager.add(WeekdayCallEquityConstraint(weight=5.0))
manager.add(TuesdayCallPreferenceConstraint(weight=2.0))
```

## Data Flow Summary

1. **Input**: Faculty list, blocks, availability matrix
2. **Filter**: Remove adjuncts → `call_eligible_faculty`
3. **Index**: Build `call_eligible_faculty_idx` for O(1) lookups
4. **Variables**: Create binary `call[f_i, b_i, type]` for each eligible combo
5. **Constraints**: Apply hard (coverage, exclusion, availability) and soft (equity)
6. **Solve**: Optimizer finds assignment minimizing penalties
7. **Extract**: Read solution values where `call[...] == 1`
8. **Persist**: Create `CallAssignment` ORM objects
9. **API**: Expose via `/api/v1/call-assignments` endpoints
