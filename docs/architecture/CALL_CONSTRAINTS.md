***REMOVED*** Call Coverage Constraints Reference

> **Module:** `backend/app/scheduling/constraints/call_coverage.py`
> **Last Updated:** 2025-12-26

---

***REMOVED******REMOVED*** Overview

The call coverage constraint system ensures complete overnight call coverage for Sunday through Thursday nights. It consists of three hard constraints that work together to guarantee valid call assignments.

***REMOVED******REMOVED*** Constants

```python
***REMOVED*** Days eligible for overnight call (Python weekday numbers)
OVERNIGHT_CALL_DAYS = {0, 1, 2, 3, 6}
***REMOVED*** 0 = Monday, 1 = Tuesday, 2 = Wednesday, 3 = Thursday, 6 = Sunday
```

***REMOVED******REMOVED*** Helper Functions

***REMOVED******REMOVED******REMOVED*** `is_overnight_call_day(date: date) -> bool`

Check if a date is an overnight call day (Sun-Thu).

```python
from app.scheduling.constraints.call_coverage import is_overnight_call_day
from datetime import date

is_overnight_call_day(date(2025, 1, 13))  ***REMOVED*** Monday -> True
is_overnight_call_day(date(2025, 1, 17))  ***REMOVED*** Friday -> False
```

***REMOVED******REMOVED******REMOVED*** `get_overnight_call_dates(start: date, end: date) -> list[date]`

Get all overnight call dates in a range.

```python
from app.scheduling.constraints.call_coverage import get_overnight_call_dates
from datetime import date

dates = get_overnight_call_dates(date(2025, 1, 1), date(2025, 1, 31))
***REMOVED*** Returns all Sun-Thu dates in January 2025
```

---

***REMOVED******REMOVED*** Hard Constraints

***REMOVED******REMOVED******REMOVED*** 1. OvernightCallCoverageConstraint

**Purpose:** Ensures exactly one faculty member is assigned to overnight call for each eligible night.

**Name:** `OvernightCallCoverage`
**Priority:** `CRITICAL`
**Type:** `CALL`

***REMOVED******REMOVED******REMOVED******REMOVED*** Constraint Logic

For each Sun-Thu night:
```python
sum(call[f, b, "overnight"] for f in eligible_faculty) == 1
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Implementation

```python
class OvernightCallCoverageConstraint(HardConstraint):
    def add_to_cpsat(self, model, variables, context):
        call_vars = variables.get("call_assignments", {})
        call_eligible = getattr(context, "call_eligible_faculty", [])

        if not call_vars or not call_eligible:
            return

        dates_processed = set()
        for block in context.blocks:
            if not is_overnight_call_day(block.date):
                continue
            if block.date in dates_processed:
                continue
            dates_processed.add(block.date)

            b_i = context.block_idx[block.id]
            date_vars = [
                call_vars[f_i, b_i, "overnight"]
                for f_i in range(len(call_eligible))
                if (f_i, b_i, "overnight") in call_vars
            ]

            if date_vars:
                model.Add(sum(date_vars) == 1)  ***REMOVED*** Exactly one
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Validation

Returns violations if any Sun-Thu night has zero or multiple assignments.

---

***REMOVED******REMOVED******REMOVED*** 2. AdjunctCallExclusionConstraint

**Purpose:** Prevents adjunct faculty from being assigned call by the solver. Adjuncts can be manually added via API after schedule generation.

**Name:** `AdjunctCallExclusion`
**Priority:** `HIGH`
**Type:** `CALL`

***REMOVED******REMOVED******REMOVED******REMOVED*** Constraint Logic

For each adjunct faculty member:
```python
call[adjunct_idx, b, "overnight"] == 0  ***REMOVED*** For all blocks
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Implementation

```python
class AdjunctCallExclusionConstraint(HardConstraint):
    def add_to_cpsat(self, model, variables, context):
        call_vars = variables.get("call_assignments", {})
        call_eligible = getattr(context, "call_eligible_faculty", [])
        call_idx = getattr(context, "call_eligible_faculty_idx", {})

        for faculty in call_eligible:
            if faculty.faculty_role == FacultyRole.ADJUNCT.value:
                f_i = call_idx.get(faculty.id)
                if f_i is not None:
                    for (fac_i, b_i, call_type), var in call_vars.items():
                        if fac_i == f_i:
                            model.Add(var == 0)
```

**Note:** In practice, adjuncts are already filtered out of `call_eligible_faculty` in `engine._get_call_eligible_faculty()`. This constraint serves as a double-check.

---

***REMOVED******REMOVED******REMOVED*** 3. CallAvailabilityConstraint

**Purpose:** Prevents call assignment when a faculty member is marked unavailable (vacation, leave, FMIT, etc.).

**Name:** `CallAvailability`
**Priority:** `CRITICAL`
**Type:** `CALL`

***REMOVED******REMOVED******REMOVED******REMOVED*** Constraint Logic

For each unavailable faculty-block pair:
```python
call[f, b, "overnight"] == 0
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Implementation

```python
class CallAvailabilityConstraint(HardConstraint):
    def add_to_cpsat(self, model, variables, context):
        call_vars = variables.get("call_assignments", {})
        call_eligible = getattr(context, "call_eligible_faculty", [])
        call_idx = getattr(context, "call_eligible_faculty_idx", {})

        for faculty in call_eligible:
            f_i = call_idx.get(faculty.id)
            if f_i is None:
                continue

            faculty_availability = context.availability.get(faculty.id, {})

            for block in context.blocks:
                if not is_overnight_call_day(block.date):
                    continue

                b_i = context.block_idx[block.id]
                block_avail = faculty_availability.get(block.id, {})

                if not block_avail.get("available", True):
                    key = (f_i, b_i, "overnight")
                    if key in call_vars:
                        model.Add(call_vars[key] == 0)
```

---

***REMOVED******REMOVED*** Soft Constraints (Equity)

These constraints are defined in `call_equity.py` and work with the call variables:

***REMOVED******REMOVED******REMOVED*** SundayCallEquityConstraint

**Weight:** 10.0

Balances Sunday call assignments across faculty. Sunday is tracked separately because it's more burdensome (weekend night).

***REMOVED******REMOVED******REMOVED*** WeekdayCallEquityConstraint

**Weight:** 5.0

Balances Mon-Thu call assignments across faculty.

***REMOVED******REMOVED******REMOVED*** CallSpacingConstraint

**Weight:** 8.0

Prevents back-to-back call assignments. Penalizes when the same faculty has call on consecutive eligible nights.

***REMOVED******REMOVED******REMOVED*** TuesdayCallPreferenceConstraint

**Weight:** 2.0

Honors faculty preferences for or against Tuesday call.

---

***REMOVED******REMOVED*** Variable Structure

All call constraints expect variables in this format:

```python
variables["call_assignments"] = {
    (faculty_idx, block_idx, "overnight"): BoolVar,
    ...
}
```

- **faculty_idx**: Index in `context.call_eligible_faculty`
- **block_idx**: Index in `context.blocks`
- **call_type**: String literal `"overnight"`

---

***REMOVED******REMOVED*** Constraint Priority Hierarchy

| Priority | Value | Constraints |
|----------|-------|-------------|
| CRITICAL | 100 | OvernightCallCoverage, CallAvailability |
| HIGH | 75 | AdjunctCallExclusion |

Hard constraints with higher priority are applied first, ensuring the most critical requirements are satisfied before optimization begins.

---

***REMOVED******REMOVED*** Integration with Existing Constraints

***REMOVED******REMOVED******REMOVED*** FMIT Week Blocking

The `PostFMITRecoveryConstraint` and `PostFMITSundayBlockingConstraint` in `fmit.py` mark faculty as unavailable during and after their FMIT week. `CallAvailabilityConstraint` then prevents call assignment for these periods.

***REMOVED******REMOVED******REMOVED*** Night Float Coordination

Faculty on Night Float rotations are marked unavailable in the availability matrix, preventing double-duty via `CallAvailabilityConstraint`.

---

***REMOVED******REMOVED*** Testing

Test file: `backend/tests/test_call_generation.py`

Key test scenarios:
1. `TestOvernightCallDays` - Verify day detection
2. `TestOvernightCallCoverageConstraint` - Verify coverage enforcement
3. `TestAdjunctCallExclusionConstraint` - Verify adjunct filtering
4. `TestCallAvailabilityConstraint` - Verify availability respect
