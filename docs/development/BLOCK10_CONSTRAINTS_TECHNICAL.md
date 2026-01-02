# Block 10 Constraints: Technical Implementation Guide

> **Created:** 2025-12-25
> **Status:** Implemented, Tested, Verified
> **Block 10 Dates:** 2026-03-12 to 2026-04-08

---

## Overview

Block 10 introduced 6 new scheduling constraints focused on call equity and inpatient workload distribution. All constraints are registered in `ConstraintManager` and verified by CI tests.

---

## Constraint Inventory

| Constraint | Type | Weight | File |
|------------|------|--------|------|
| `PostFMITSundayBlockingConstraint` | Hard | N/A | `fmit.py` |
| `ResidentInpatientHeadcountConstraint` | Hard | N/A | `inpatient.py` |
| `CallSpacingConstraint` | Soft | 8.0 | `call_equity.py` |
| `SundayCallEquityConstraint` | Soft | 10.0 | `call_equity.py` |
| `WeekdayCallEquityConstraint` | Soft | 5.0 | `call_equity.py` |
| `TuesdayCallPreferenceConstraint` | Soft | 2.0 | `call_equity.py` |

### Weight Hierarchy

```
Sunday (10.0) > CallSpacing (8.0) > Weekday (5.0) > Tuesday (2.0)
```

Sunday call equity has highest priority because:
- Sunday assignments are most impactful to quality of life
- Residents strongly prefer fair distribution of weekend work
- Historical data shows Sunday imbalance causes most complaints

---

## Hard Constraints

### PostFMITSundayBlockingConstraint

**Location:** `backend/app/scheduling/constraints/fmit.py`

**Purpose:** Prevents scheduling a resident for Sunday call immediately after completing an FMIT (Family Medicine Inpatient Teaching) rotation.

**Rationale:** FMIT rotations are intensive inpatient weeks. Scheduling Sunday call immediately after creates excessive fatigue and violates the spirit of ACGME rest requirements.

```python
class PostFMITSundayBlockingConstraint(BaseConstraint):
    """Block Sunday call for residents completing FMIT the prior week."""

    constraint_type = ConstraintType.HARD
    category = ConstraintCategory.WORKLOAD

    def check(self, assignment: Assignment, context: ScheduleContext) -> ConstraintResult:
        # If this is a Sunday call assignment
        if not self._is_sunday_call(assignment):
            return ConstraintResult(satisfied=True)

        # Check if resident completed FMIT in the prior week
        if self._completed_fmit_prior_week(assignment.person_id, assignment.date):
            return ConstraintResult(
                satisfied=False,
                message=f"Cannot assign Sunday call after FMIT week",
                violation_type=ViolationType.HARD_CONSTRAINT
            )

        return ConstraintResult(satisfied=True)
```

### ResidentInpatientHeadcountConstraint

**Location:** `backend/app/scheduling/constraints/inpatient.py`

**Purpose:** Ensures minimum and maximum resident counts on inpatient services.

**Configuration:**
- Minimum: 2 residents (safety floor)
- Maximum: 4 residents (supervision capacity)

```python
class ResidentInpatientHeadcountConstraint(BaseConstraint):
    """Enforce min/max resident counts on inpatient services."""

    constraint_type = ConstraintType.HARD
    category = ConstraintCategory.COVERAGE

    def __init__(self, min_residents: int = 2, max_residents: int = 4):
        self.min_residents = min_residents
        self.max_residents = max_residents

    def check_daily(self, date: date, assignments: List[Assignment]) -> ConstraintResult:
        inpatient_count = sum(
            1 for a in assignments
            if a.rotation.activity_type == "inpatient"
        )

        if inpatient_count < self.min_residents:
            return ConstraintResult(
                satisfied=False,
                message=f"Only {inpatient_count} residents on inpatient (min: {self.min_residents})"
            )

        if inpatient_count > self.max_residents:
            return ConstraintResult(
                satisfied=False,
                message=f"{inpatient_count} residents on inpatient exceeds max ({self.max_residents})"
            )

        return ConstraintResult(satisfied=True)
```

---

## Soft Constraints (Call Equity)

### SundayCallEquityConstraint

**Location:** `backend/app/scheduling/constraints/call_equity.py`

**Purpose:** Distribute Sunday call assignments equitably across all residents.

**Weight:** 10.0 (highest among soft constraints)

```python
class SundayCallEquityConstraint(BaseConstraint):
    """Ensure fair distribution of Sunday call assignments."""

    constraint_type = ConstraintType.SOFT
    weight = 10.0
    category = ConstraintCategory.EQUITY

    def evaluate(self, schedule: Schedule) -> float:
        sunday_counts = self._count_sunday_calls_per_resident(schedule)
        variance = self._calculate_variance(sunday_counts)

        # Lower variance = better equity = higher score
        return 1.0 / (1.0 + variance)
```

### CallSpacingConstraint

**Location:** `backend/app/scheduling/constraints/call_equity.py`

**Purpose:** Ensure adequate spacing between call assignments for the same resident.

**Weight:** 8.0

**Configuration:**
- Minimum days between calls: 5
- Preferred days between calls: 7

```python
class CallSpacingConstraint(BaseConstraint):
    """Enforce minimum spacing between call assignments."""

    constraint_type = ConstraintType.SOFT
    weight = 8.0
    category = ConstraintCategory.WORKLOAD

    def __init__(self, min_days: int = 5, preferred_days: int = 7):
        self.min_days = min_days
        self.preferred_days = preferred_days

    def check(self, assignment: Assignment, context: ScheduleContext) -> ConstraintResult:
        last_call = self._find_last_call(assignment.person_id, context)

        if last_call:
            days_since = (assignment.date - last_call.date).days

            if days_since < self.min_days:
                return ConstraintResult(
                    satisfied=False,
                    penalty=self.weight * 2,  # Double penalty for < minimum
                    message=f"Only {days_since} days since last call (min: {self.min_days})"
                )

            if days_since < self.preferred_days:
                return ConstraintResult(
                    satisfied=True,
                    penalty=self.weight * (self.preferred_days - days_since) / self.preferred_days,
                    message=f"{days_since} days since last call (preferred: {self.preferred_days})"
                )

        return ConstraintResult(satisfied=True, penalty=0)
```

### WeekdayCallEquityConstraint

**Location:** `backend/app/scheduling/constraints/call_equity.py`

**Purpose:** Distribute weekday (Monday-Friday) call assignments fairly.

**Weight:** 5.0

Similar structure to `SundayCallEquityConstraint` but for weekday assignments.

### TuesdayCallPreferenceConstraint

**Location:** `backend/app/scheduling/constraints/call_equity.py`

**Purpose:** Handle Tuesday call preferences (some residents prefer/avoid Tuesday due to recurring commitments).

**Weight:** 2.0 (lowest - preference, not requirement)

```python
class TuesdayCallPreferenceConstraint(BaseConstraint):
    """Honor Tuesday call preferences when possible."""

    constraint_type = ConstraintType.SOFT
    weight = 2.0
    category = ConstraintCategory.PREFERENCE

    def check(self, assignment: Assignment, context: ScheduleContext) -> ConstraintResult:
        if assignment.date.weekday() != 1:  # Tuesday
            return ConstraintResult(satisfied=True)

        preference = self._get_tuesday_preference(assignment.person_id)

        if preference == "avoid" and self._is_call_assignment(assignment):
            return ConstraintResult(
                satisfied=True,
                penalty=self.weight,
                message="Assigned Tuesday call despite 'avoid' preference"
            )

        return ConstraintResult(satisfied=True, penalty=0)
```

---

## Registration in ConstraintManager

All constraints are registered in both factory methods:

```python
# backend/app/scheduling/constraints/manager.py

class ConstraintManager:
    @classmethod
    def create_default(cls) -> "ConstraintManager":
        manager = cls()

        # ... existing constraints ...

        # Block 10: Call equity constraints
        manager.register(CallSpacingConstraint())
        manager.register(SundayCallEquityConstraint())
        manager.register(WeekdayCallEquityConstraint())
        manager.register(TuesdayCallPreferenceConstraint())

        # Block 10: Workload constraints
        manager.register(PostFMITSundayBlockingConstraint())
        manager.register(ResidentInpatientHeadcountConstraint())

        return manager

    @classmethod
    def create_resilience_aware(cls) -> "ConstraintManager":
        # Same constraints, plus resilience-specific ones
        manager = cls.create_default()
        # ... additional resilience constraints ...
        return manager
```

---

## Verification

### Pre-flight Script

```bash
python scripts/verify_constraints.py
```

Expected output:
```
Verifying constraint registration...
  - CallSpacingConstraint
  - SundayCallEquityConstraint
  - WeekdayCallEquityConstraint
  - TuesdayCallPreferenceConstraint
  - PostFMITSundayBlockingConstraint
  - ResidentInpatientHeadcountConstraint
All 25 constraints registered successfully
```

### CI Tests

```bash
pytest tests/test_constraint_registration.py -v
```

Tests verify:
1. All exported constraints from `__init__.py` are registered
2. Block 10 constraints specifically present
3. Weight hierarchy maintained
4. Both factory methods include all constraints

---

## Testing Block 10 Schedule Generation

```bash
# Get auth token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login/json" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "SecureP@ss1234"}' | jq -r '.access_token')

# Generate Block 10 schedule
curl -s -X POST "http://localhost:8000/api/v1/schedule/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2026-03-12",
    "end_date": "2026-04-08",
    "algorithm": "cp_sat",
    "timeout_seconds": 120
  }'
```

### Expected Results (from 2025-12-25 verification)

```json
{
  "status": "success",
  "total_assignments": 87,
  "validation": {
    "valid": true,
    "violations_count": 0
  },
  "metrics": {
    "coverage_percentage": 112.5,
    "conflicts_count": 0,
    "acgme_overrides": 0
  }
}
```

---

## Troubleshooting

### Constraints Not Registered

**Symptom:** `verify_constraints.py` shows fewer than 25 constraints

**Cause:** Code in container is stale (Docker image not rebuilt)

**Fix:** Use docker cp workaround:
```bash
docker cp backend/app/scheduling/constraints/manager.py \
  residency-scheduler-backend:/app/app/scheduling/constraints/manager.py
docker-compose restart backend
```

### ModuleNotFoundError

**Symptom:** `ModuleNotFoundError: No module named 'night_float_post_call'`

**Cause:** Missing file in container

**Fix:** Copy the missing module:
```bash
docker cp backend/app/scheduling/constraints/night_float_post_call.py \
  residency-scheduler-backend:/app/app/scheduling/constraints/night_float_post_call.py
```

---

## Related Documentation

- [DOCKER_WORKAROUNDS.md](DOCKER_WORKAROUNDS.md) - When Docker builds fail
- [SESSION_HANDOFF_20251225.md](SESSION_HANDOFF_20251225.md) - Session context
- [AGENT_SKILLS.md](AGENT_SKILLS.md) - constraint-preflight skill
