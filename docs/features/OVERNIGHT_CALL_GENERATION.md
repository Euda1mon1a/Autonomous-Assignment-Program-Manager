# Overnight Faculty Call Generation

> **Last Updated:** 2025-12-26
> **Status:** Implemented
> **Module:** `backend/app/scheduling/`

---

## Overview

The Overnight Faculty Call Generation feature automates the assignment of overnight call duties to faculty members during schedule generation. This ensures complete coverage for Sunday through Thursday nights while respecting ACGME compliance requirements and faculty availability.

## Key Features

- **Solver-Integrated**: Call assignments are generated as part of the constraint-based scheduling optimization
- **Sun-Thurs Coverage**: Automated coverage for Sunday through Thursday nights only
- **FMIT Integration**: Friday and Saturday nights are handled by FMIT (Faculty Managing Inpatient Teaching) assignments
- **Adjunct Exclusion**: Adjunct faculty are excluded from solver-generated call; they can be manually added via API
- **Equity Optimization**: Call is distributed fairly across eligible faculty using soft constraints

## Coverage Pattern

| Day | Night Coverage | Handler |
|-----|----------------|---------|
| Sunday | Overnight Call | **Solver-generated** |
| Monday | Overnight Call | **Solver-generated** |
| Tuesday | Overnight Call | **Solver-generated** |
| Wednesday | Overnight Call | **Solver-generated** |
| Thursday | Overnight Call | **Solver-generated** |
| Friday | FMIT | Block schedule (not solver) |
| Saturday | FMIT | Block schedule (not solver) |

## Faculty Eligibility

### Automatically Assigned (Solver-Generated)
- Program Director (PD)
- Associate Program Director (APD)
- Core Faculty
- Officer in Charge (OIC)
- Department Chiefs
- Sports Medicine Faculty

### Manually Assigned (API)
- **Adjunct Faculty** - Excluded from solver optimization, can be added via `POST /api/v1/call-assignments`

## How It Works

### 1. Context Building
When the scheduling engine runs, it builds a `SchedulingContext` that includes:
- `call_eligible_faculty`: List of faculty eligible for overnight call (excludes adjuncts)
- `call_eligible_faculty_idx`: Lookup dictionary for fast constraint evaluation

### 2. Variable Creation
The CP-SAT and PuLP solvers create binary decision variables:
```
call[(faculty_idx, block_idx, "overnight")] = 0 or 1
```

### 3. Constraint Enforcement
Three hard constraints ensure valid call assignments:
1. **OvernightCallCoverage**: Exactly one faculty per Sun-Thurs night
2. **AdjunctCallExclusion**: Forces adjunct variables to 0
3. **CallAvailability**: Blocks call when faculty is unavailable

### 4. Equity Optimization
Soft constraints optimize for fair distribution:
- **SundayCallEquity**: Balances Sunday call across faculty
- **WeekdayCallEquity**: Balances Mon-Thu call across faculty
- **CallSpacing**: Prevents back-to-back call assignments
- **TuesdayCallPreference**: Honors faculty Tuesday preferences

### 5. Persistence
After solving, `CallAssignment` records are created in the database with:
- Date of the call night
- Assigned faculty ID
- Call type ("overnight")
- Weekend/holiday flags

## API Endpoints

### List Call Assignments
```http
GET /api/v1/call-assignments?start_date=2025-01-01&end_date=2025-01-31
```

### Create Manual Assignment (Adjuncts)
```http
POST /api/v1/call-assignments
Content-Type: application/json

{
  "date": "2025-01-15",
  "person_id": "uuid-here",
  "call_type": "overnight"
}
```

### Coverage Report
```http
GET /api/v1/call-assignments/reports/coverage?start_date=2025-01-01&end_date=2025-01-31
```

### Equity Report
```http
GET /api/v1/call-assignments/reports/equity?year=2025
```

## Configuration

The call generation system uses the following constants:

```python
# Days eligible for overnight call (Python weekday numbers)
OVERNIGHT_CALL_DAYS = {0, 1, 2, 3, 6}  # Mon, Tue, Wed, Thu, Sun
```

## Integration with FMIT

The overnight call system is designed to complement FMIT (Faculty Managing Inpatient Teaching):

- **FMIT Week**: Faculty on FMIT are blocked from overnight call during their week
- **Friday-Saturday**: Handled entirely by FMIT faculty, not the call solver
- **Post-FMIT Recovery**: Faculty get recovery time after FMIT before returning to call pool

## Troubleshooting

### No Call Assignments Generated
1. Check that `call_eligible_faculty` is populated in context
2. Verify solver is running (CP-SAT or PuLP, not Greedy)
3. Confirm faculty have `faculty_role` set (not adjunct)

### Incomplete Coverage
1. Check for availability conflicts blocking faculty
2. Review hard constraint violations in solver output
3. Verify sufficient eligible faculty for the date range

### Equity Imbalance
1. Review soft constraint weights in ConstraintManager
2. Check for faculty with many absence records
3. Consider adjusting `SundayCallEquity` weight

## Related Documentation

- [Call Constraints Reference](../architecture/CALL_CONSTRAINTS.md)
- [Call Generation Architecture](../architecture/CALL_GENERATION_ARCHITECTURE.md)
- [Call Assignments API Reference](../api/CALL_ASSIGNMENTS_API.md)
- [Solver Algorithm](../architecture/SOLVER_ALGORITHM.md)
