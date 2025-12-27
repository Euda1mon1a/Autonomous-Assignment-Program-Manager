# Overnight Call Generation - Implementation Changelog

> **Date:** 2025-12-26
> **Feature:** Solver-integrated overnight faculty call generation
> **Branch:** claude/overnight-faculty-call

---

## Summary

Implemented solver-integrated overnight faculty call generation for Sunday through Thursday nights. The feature generates call assignments as part of the constraint-based scheduling optimization, ensuring complete coverage while balancing equity across eligible faculty.

---

## Files Created

### 1. Pydantic Schemas
**File:** `backend/app/schemas/call_assignment.py`

Defines API request/response contracts:

| Class | Purpose |
|-------|---------|
| `CallAssignmentBase` | Base model with date, person_id, call_type |
| `CallAssignmentCreate` | Request model for creating assignments |
| `CallAssignmentUpdate` | Request model for updates |
| `CallAssignmentResponse` | API response with enriched fields |
| `CallAssignmentWithPerson` | Extended response with faculty details |
| `CallCoverageReport` | Coverage analysis report model |
| `CallEquityReport` | Equity distribution report model |
| `BulkCallAssignmentCreate` | Bulk import request model |

### 2. Service Layer
**File:** `backend/app/services/call_assignment_service.py`

Business logic for call assignment management:

| Method | Purpose |
|--------|---------|
| `get_call_assignment(id)` | Retrieve single assignment |
| `list_call_assignments(...)` | List with filters |
| `create_call_assignment(data)` | Manual creation (adjuncts) |
| `bulk_create_call_assignments(...)` | Solver output import |
| `delete_call_assignment(id)` | Remove assignment |
| `delete_call_assignments_in_range(...)` | Range deletion |
| `get_coverage_report(...)` | Coverage analysis |
| `get_equity_report(year)` | Equity statistics |
| `get_faculty_call_counts(...)` | Per-faculty counts |

### 3. Hard Constraints
**File:** `backend/app/scheduling/constraints/call_coverage.py`

Three new hard constraints:

| Constraint | Priority | Purpose |
|------------|----------|---------|
| `OvernightCallCoverageConstraint` | CRITICAL | Exactly one faculty per night |
| `AdjunctCallExclusionConstraint` | HIGH | Block adjuncts from solver |
| `CallAvailabilityConstraint` | CRITICAL | Respect unavailability |

Helper functions:
- `is_overnight_call_day(date)` - Check if date is Sun-Thu
- `get_overnight_call_dates(start, end)` - Get eligible dates in range

Constants:
- `OVERNIGHT_CALL_DAYS = {0, 1, 2, 3, 6}` - Mon-Thu, Sun

### 4. API Routes
**File:** `backend/app/api/routes/call_assignments.py`

REST API endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/call-assignments` | GET | List with filters |
| `/call-assignments/{id}` | GET | Get single |
| `/call-assignments` | POST | Create (manual) |
| `/call-assignments/bulk` | POST | Bulk create |
| `/call-assignments/{id}` | DELETE | Remove |
| `/call-assignments/reports/coverage` | GET | Coverage report |
| `/call-assignments/reports/equity` | GET | Equity report |

### 5. Unit Tests
**File:** `backend/tests/test_call_generation.py`

Test coverage:
- `TestOvernightCallDays` - Day detection tests
- `TestOvernightCallCoverageConstraint` - Coverage constraint tests
- `TestAdjunctCallExclusionConstraint` - Adjunct filtering tests
- `TestCallAvailabilityConstraint` - Availability tests
- `TestCallAssignmentModel` - Database model tests
- `TestCallAssignmentService` - Service layer tests

---

## Files Modified

### 1. SolverResult Class
**File:** `backend/app/scheduling/solvers.py`

Added `call_assignments` field to capture solver output:

```python
class SolverResult:
    def __init__(
        self,
        ...,
        call_assignments: list[tuple[UUID, UUID, str]] = None,
    ):
        self.call_assignments = call_assignments or []
```

### 2. CPSATSolver
**File:** `backend/app/scheduling/solvers.py`

Added call variable creation (lines ~825-856):
```python
call = {}
call_eligible = getattr(context, "call_eligible_faculty", [])
call_idx = getattr(context, "call_eligible_faculty_idx", {})

if call_eligible:
    call_dates_processed = set()
    for block in workday_blocks:
        if block.date.weekday() not in (0, 1, 2, 3, 6):
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

Added call extraction (lines ~1010-1039):
```python
call_assignments_result = []
for (f_i, b_i, call_type), var in call.items():
    if solver.Value(var) == 1:
        # Find faculty and block
        call_assignments_result.append((faculty_id, block_id, call_type))
```

### 3. PuLPSolver
**File:** `backend/app/scheduling/solvers.py`

Added identical call variable creation (lines ~277-304) and extraction (lines ~497-522) patterns using PuLP syntax:

```python
call[f_i, b_i, "overnight"] = pulp.LpVariable(f"call_{f_i}_{b_i}", cat=pulp.LpBinary)
```

### 4. SchedulingContext
**File:** `backend/app/scheduling/constraints/base.py`

Extended dataclass with call-eligible faculty fields (lines ~237-245):

```python
@dataclass
class SchedulingContext:
    # ... existing fields ...

    # Call Assignment Data
    call_eligible_faculty: list = field(default_factory=list)
    call_eligible_faculty_idx: dict[UUID, int] = field(default_factory=dict)
    existing_call_assignments: list = field(default_factory=list)
```

Updated `__post_init__` to build call index (lines ~271-275):
```python
if self.call_eligible_faculty:
    self.call_eligible_faculty_idx = {
        f.id: i for i, f in enumerate(self.call_eligible_faculty)
    }
```

### 5. SchedulingEngine
**File:** `backend/app/scheduling/engine.py`

Added imports:
```python
from app.models.call_assignment import CallAssignment
from app.models.person import Person, FacultyRole
```

Added `_get_call_eligible_faculty()` method (lines ~945-961):
```python
def _get_call_eligible_faculty(self, faculty: list[Person]) -> list[Person]:
    return [
        f for f in faculty
        if f.faculty_role != FacultyRole.ADJUNCT.value
    ]
```

Updated `_build_context()` to populate call data (lines ~467-481):
```python
call_eligible = self._get_call_eligible_faculty(faculty)
context = SchedulingContext(
    ...,
    call_eligible_faculty=call_eligible,
)
```

Added `_create_call_assignments_from_result()` method (lines ~795-842):
```python
def _create_call_assignments_from_result(
    self, result: SolverResult, context: SchedulingContext
) -> list[CallAssignment]:
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

Integrated into `generate()` flow (lines ~277-281):
```python
# Step 6.5: Create call assignments from solver results
call_assignments = self._create_call_assignments_from_result(
    solver_result, context
)
```

### 6. ConstraintManager
**File:** `backend/app/scheduling/constraints/manager.py`

Added imports (lines ~62-66):
```python
from .call_coverage import (
    AdjunctCallExclusionConstraint,
    CallAvailabilityConstraint,
    OvernightCallCoverageConstraint,
)
```

Registered in `create_default()` (lines ~313-316):
```python
manager.add(OvernightCallCoverageConstraint())
manager.add(AdjunctCallExclusionConstraint())
manager.add(CallAvailabilityConstraint())
```

Registered in `create_resilience_aware()` (lines ~393-396).

### 7. Constraints __init__
**File:** `backend/app/scheduling/constraints/__init__.py`

Added exports (lines ~49-53):
```python
from .call_coverage import (
    AdjunctCallExclusionConstraint,
    CallAvailabilityConstraint,
    OvernightCallCoverageConstraint,
)
```

Added to `__all__` list.

### 8. API Routes __init__
**File:** `backend/app/api/routes/__init__.py`

Registered router (line ~81):
```python
api_router.include_router(call_assignments.router)
```

---

## Database Schema

No new migrations required. Uses existing `CallAssignment` model from `backend/app/models/call_assignment.py`:

```sql
CREATE TABLE call_assignments (
    id UUID PRIMARY KEY,
    date DATE NOT NULL,
    person_id UUID REFERENCES people(id) ON DELETE CASCADE,
    call_type VARCHAR(50) NOT NULL,
    is_weekend BOOLEAN DEFAULT FALSE,
    is_holiday BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_call_per_day UNIQUE (date, person_id, call_type),
    CONSTRAINT check_call_type CHECK (call_type IN ('overnight', 'weekend', 'backup'))
);
```

---

## Key Design Decisions

1. **Solver Integration**: Call assignments generated as part of constraint optimization, not post-processing
2. **Adjunct Exclusion**: Adjuncts filtered at engine level (`_get_call_eligible_faculty`) with constraint double-check
3. **One Variable Per Date**: Call variables use date deduplication, not one per AM/PM block
4. **FMIT Coordination**: Fri-Sat excluded (weekday 4, 5); FMIT handles weekend coverage
5. **Equity Separation**: Sunday call tracked separately from weekday for equity balancing

---

## Verification

```bash
# Lint check
./venv/bin/ruff check app/scheduling/ app/api/routes/call_assignments.py --fix
# Result: All checks passed!

# Format check
./venv/bin/ruff format app/services/call_assignment_service.py \
  app/schemas/call_assignment.py \
  app/scheduling/constraints/call_coverage.py \
  app/api/routes/call_assignments.py
# Result: 4 files reformatted
```
