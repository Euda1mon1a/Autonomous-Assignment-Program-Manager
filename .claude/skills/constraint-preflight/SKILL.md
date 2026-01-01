---
name: constraint-preflight
description: Pre-flight verification for scheduling constraint development. Use when adding, modifying, or testing constraints to ensure they are properly implemented, exported, registered, and tested before commit.
model_tier: sonnet
parallel_hints:
  can_parallel_with: [test-writer, code-review]
  must_serialize_with: [SCHEDULING, schedule-optimization]
  preferred_batch_size: 1
context_hints:
  max_file_context: 50
  compression_level: 1
  requires_git_context: true
  requires_db_context: false
escalation_triggers:
  - pattern: "ACGME.*constraint"
    reason: "ACGME constraint changes require domain expert review"
  - pattern: "weight.*hierarchy"
    reason: "Weight hierarchy changes require clinical input"
  - keyword: ["compliance", "regulation"]
    reason: "Regulatory constraints require human verification"
---

# Constraint Pre-Flight Verification

Prevents the "implemented but not registered" bug where constraints are created, tested, and exported but never added to the ConstraintManager factory methods.

## When This Skill Activates

- When creating new scheduling constraints
- When modifying existing constraints
- Before committing constraint-related changes
- When the user asks to verify constraint registration
- After adding constraints to `__init__.py` exports

## The Constraint Gap Problem

### What Goes Wrong

A common failure mode in constraint development:

```
1. Create constraint class in backend/app/scheduling/constraints/*.py  ✓
2. Write tests for constraint logic                                     ✓
3. Export constraint in __init__.py                                     ✓
4. Tests pass locally                                                   ✓
5. ⚠️ FORGET to register in ConstraintManager.create_default()         ✗
6. Commit and push                                                      ✓
7. Schedule generation doesn't use the constraint!                      💥
```

### Why It Happens

- Tests verify constraint logic in isolation
- Tests don't verify the constraint is actually used by the scheduler
- Manual verification of "registered at line X" is error-prone
- No CI check catches unregistered constraints

## Pre-Flight Verification Script

Run this before committing any constraint changes:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend
python ../scripts/verify_constraints.py
```

### What It Checks

1. **Registration** - All exported constraints are in `ConstraintManager.create_default()`
2. **Weight Hierarchy** - Soft constraint weights follow documented order
3. **Manager Consistency** - Constraints in both `create_default()` and `create_resilience_aware()`

### Expected Output

```
============================================================
CONSTRAINT PRE-FLIGHT VERIFICATION
============================================================
This script verifies constraint implementation completeness.
Run this before committing constraint changes.

============================================================
CONSTRAINT REGISTRATION VERIFICATION
============================================================

Registered constraints (23 total):
  - 1in7Rule: ENABLED
  - 80HourRule: ENABLED
  - Availability: ENABLED
  - CallSpacing: ENABLED weight=8.0
  - ClinicCapacity: ENABLED
  ...

Block 10 Constraint Check:
  [OK] CallSpacingConstraint
  [OK] SundayCallEquityConstraint
  [OK] TuesdayCallPreferenceConstraint
  [OK] WeekdayCallEquityConstraint
  [OK] ResidentInpatientHeadcountConstraint
  [OK] PostFMITSundayBlockingConstraint

============================================================
WEIGHT HIERARCHY VERIFICATION
============================================================

Call equity weight hierarchy:
  [OK] SundayCallEquity: weight=10.0
  [OK] CallSpacing: weight=8.0
  [OK] WeekdayCallEquity: weight=5.0
  [OK] TuesdayCallPreference: weight=2.0

============================================================
MANAGER CONSISTENCY VERIFICATION
============================================================

Block 10 constraints in both managers:
  [OK] ResidentInpatientHeadcount
  [OK] PostFMITSundayBlocking
  [OK] SundayCallEquity
  [OK] CallSpacing
  [OK] WeekdayCallEquity
  [OK] TuesdayCallPreference

============================================================
SUMMARY
============================================================
  Registration: PASS
  Weight Hierarchy: PASS
  Manager Consistency: PASS

[SUCCESS] All verifications passed!
```

## Constraint Development Checklist

When creating a new constraint:

### Step 1: Implement Constraint Class

```python
# backend/app/scheduling/constraints/my_constraint.py

class MyNewConstraint(SoftConstraint):
    """
    Docstring explaining the constraint's purpose.
    """
    def __init__(self, weight: float = 5.0) -> None:
        super().__init__(
            name="MyNewConstraint",
            constraint_type=ConstraintType.EQUITY,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )

    def add_to_cpsat(self, model, variables, context) -> None:
        # CP-SAT implementation
        pass

    def add_to_pulp(self, model, variables, context) -> None:
        # PuLP implementation
        pass

    def validate(self, assignments, context) -> ConstraintResult:
        # Validation implementation
        pass
```

### Step 2: Export in `__init__.py`

```python
# backend/app/scheduling/constraints/__init__.py

from .my_constraint import MyNewConstraint

__all__ = [
    # ... existing exports ...
    "MyNewConstraint",
]
```

### Step 3: Register in Manager (CRITICAL!)

```python
# backend/app/scheduling/constraints/manager.py

from .my_constraint import MyNewConstraint

class ConstraintManager:
    @classmethod
    def create_default(cls) -> "ConstraintManager":
        manager = cls()
        # ... existing constraints ...
        manager.add(MyNewConstraint(weight=5.0))  # ADD THIS!
        return manager

    @classmethod
    def create_resilience_aware(cls, ...) -> "ConstraintManager":
        manager = cls()
        # ... existing constraints ...
        manager.add(MyNewConstraint(weight=5.0))  # ADD THIS TOO!
        return manager
```

### Step 4: Write Tests

```python
# backend/tests/test_my_constraint.py

from app.scheduling.constraints import MyNewConstraint, ConstraintManager


class TestMyNewConstraint:
    def test_constraint_initialization(self):
        constraint = MyNewConstraint()
        assert constraint.name == "MyNewConstraint"
        assert constraint.weight == 5.0

    def test_constraint_registered_in_manager(self):
        """CRITICAL: Verify constraint is actually used!"""
        manager = ConstraintManager.create_default()
        registered_types = {type(c) for c in manager.constraints}
        assert MyNewConstraint in registered_types
```

### Step 5: Run Pre-Flight Verification

```bash
cd backend
python ../scripts/verify_constraints.py
```

### Step 6: Commit Only If All Pass

```bash
git add .
git commit -m "feat: add MyNewConstraint for [purpose]"
```

## Test Coverage

The `test_constraint_registration.py` file provides automated CI coverage:

```python
# Key tests that prevent the registration gap:

class TestConstraintRegistration:
    def test_block10_hard_constraints_in_default_manager(self):
        """Verify hard constraints are registered."""

    def test_block10_soft_constraints_in_default_manager(self):
        """Verify soft constraints are registered."""

    def test_call_equity_weight_hierarchy(self):
        """Verify weights follow: Sunday > Spacing > Weekday > Tuesday."""


class TestConstraintExportIntegrity:
    def test_all_call_equity_exports_registered(self):
        """All exported classes must be in manager."""

    def test_inpatient_constraint_registered(self):
        """ResidentInpatientHeadcountConstraint is registered."""
```

## Quick Commands

```bash
# Run pre-flight verification
cd backend && python ../scripts/verify_constraints.py

# Run constraint registration tests only
cd backend && pytest tests/test_constraint_registration.py -v

# Run all constraint tests
cd backend && pytest tests/test_*constraint*.py -v

# Check manager.py for registrations
grep -n "manager.add" backend/app/scheduling/constraints/manager.py
```

## Key Files

| File | Purpose |
|------|---------|
| `scripts/verify_constraints.py` | Pre-flight verification script |
| `backend/tests/test_constraint_registration.py` | CI tests for registration |
| `backend/app/scheduling/constraints/manager.py` | Where constraints are registered |
| `backend/app/scheduling/constraints/__init__.py` | Where constraints are exported |

## Weight Hierarchy Reference

For call equity constraints, follow this hierarchy (highest impact first):

| Constraint | Weight | Rationale |
|------------|--------|-----------|
| SundayCallEquity | 10.0 | Worst call day, highest priority |
| CallSpacing | 8.0 | Burnout prevention |
| WeekdayCallEquity | 5.0 | Balance Mon-Thu calls |
| TuesdayCallPreference | 2.0 | Academic scheduling preference |
| DeptChiefWednesdayPreference | 1.0 | Personal preference (lowest) |

## Concrete Usage Example

### End-to-End: Adding a New Constraint

**Scenario:** You need to add a constraint that prevents residents from being scheduled for more than 2 consecutive weekend calls.

**Step 1: Create the Constraint Class**
```bash
# Create new file
touch backend/app/scheduling/constraints/weekend_call_limit.py
```

```python
# backend/app/scheduling/constraints/weekend_call_limit.py
from typing import Any, Dict
from app.scheduling.constraints.base import SoftConstraint, ConstraintType, ConstraintPriority, ConstraintResult

class WeekendCallLimitConstraint(SoftConstraint):
    """
    Prevents residents from working more than 2 consecutive weekend calls.
    Soft constraint - penalizes violations rather than blocking them.
    """
    def __init__(self, weight: float = 6.0, max_consecutive: int = 2) -> None:
        super().__init__(
            name="WeekendCallLimit",
            constraint_type=ConstraintType.WORKLOAD,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )
        self.max_consecutive = max_consecutive

    def add_to_cpsat(self, model, variables, context) -> None:
        # Implementation for CP-SAT solver
        pass

    def validate(self, assignments, context) -> ConstraintResult:
        # Validation implementation
        pass
```

**Step 2: Export in `__init__.py`**
```bash
# Edit backend/app/scheduling/constraints/__init__.py
```

Add to exports:
```python
from .weekend_call_limit import WeekendCallLimitConstraint

__all__ = [
    # ... existing exports ...
    "WeekendCallLimitConstraint",
]
```

**Step 3: Register in Manager (CRITICAL!)**
```bash
# Edit backend/app/scheduling/constraints/manager.py
```

Add to both factory methods:
```python
from .weekend_call_limit import WeekendCallLimitConstraint

class ConstraintManager:
    @classmethod
    def create_default(cls) -> "ConstraintManager":
        manager = cls()
        # ... existing constraints ...
        manager.add(WeekendCallLimitConstraint(weight=6.0))  # ADD THIS!
        return manager

    @classmethod
    def create_resilience_aware(cls, ...) -> "ConstraintManager":
        manager = cls()
        # ... existing constraints ...
        manager.add(WeekendCallLimitConstraint(weight=6.0))  # AND THIS!
        return manager
```

**Step 4: Write Tests**
```python
# backend/tests/test_weekend_call_limit.py
import pytest
from app.scheduling.constraints import WeekendCallLimitConstraint, ConstraintManager

class TestWeekendCallLimitConstraint:
    def test_constraint_initialization(self):
        """Test basic initialization."""
        constraint = WeekendCallLimitConstraint()
        assert constraint.name == "WeekendCallLimit"
        assert constraint.weight == 6.0
        assert constraint.max_consecutive == 2

    def test_constraint_registered_in_manager(self):
        """CRITICAL: Verify constraint is actually used!"""
        manager = ConstraintManager.create_default()
        registered_types = {type(c) for c in manager.constraints}
        assert WeekendCallLimitConstraint in registered_types
```

**Step 5: Run Pre-Flight Verification**
```bash
cd backend
python ../scripts/verify_constraints.py
```

Expected output should show:
```
Registered constraints (24 total):  # One more than before
  ...
  - WeekendCallLimit: ENABLED weight=6.0
  ...

[SUCCESS] All verifications passed!
```

**Step 6: Run Tests**
```bash
cd backend
pytest tests/test_weekend_call_limit.py -v
pytest tests/test_constraint_registration.py -v  # Ensure it passes
```

**Step 7: Commit**
```bash
git add .
git commit -m "feat(constraints): add WeekendCallLimitConstraint

Prevents residents from working >2 consecutive weekend calls.
Weight: 6.0 (between CallSpacing and WeekdayCallEquity)

- Implemented constraint class with CP-SAT support
- Exported in __init__.py
- Registered in both ConstraintManager factory methods
- Added tests including registration verification
- Verified with pre-flight script"
```

**Total Time:** ~20 minutes for a simple constraint

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ CONSTRAINT DEVELOPMENT WORKFLOW                             │
└─────────────────────────────────────────────────────────────┘

1. CREATE CLASS
   ├─ Write constraint logic in constraints/*.py
   ├─ Inherit from SoftConstraint or HardConstraint
   └─ Implement add_to_cpsat() and validate()
              ↓
2. EXPORT
   ├─ Add import to __init__.py
   └─ Add class name to __all__ list
              ↓
3. REGISTER (CRITICAL - Don't Skip!)
   ├─ Add to ConstraintManager.create_default()
   └─ Add to ConstraintManager.create_resilience_aware()
              ↓
4. TEST
   ├─ Write unit tests for constraint logic
   ├─ Write registration test (verifies in manager)
   └─ Run all tests: pytest
              ↓
5. PRE-FLIGHT VERIFICATION
   ├─ Run: python ../scripts/verify_constraints.py
   ├─ Check: Registration, weights, consistency
   └─ Must pass before commit
              ↓
6. COMMIT
   └─ Only if all checks pass
```

## Common Failure Modes

### Failure Mode 1: Forgot to Register
**Symptom:** Tests pass, but schedule generation doesn't use the constraint

**Cause:** Constraint created and exported, but not added to `ConstraintManager`

**Detection:**
```bash
python ../scripts/verify_constraints.py
# Shows: "Not registered: WeekendCallLimitConstraint"
```

**Fix:** Add to both `create_default()` and `create_resilience_aware()`

### Failure Mode 2: Wrong Weight Hierarchy
**Symptom:** Pre-flight fails with weight hierarchy error

**Cause:** Weight doesn't follow documented precedence

**Example:**
```
CallSpacing: weight=8.0
WeekendCallLimit: weight=10.0  # WRONG - higher than CallSpacing
WeekdayCallEquity: weight=5.0
```

**Fix:** Adjust weight to fit hierarchy (e.g., 6.0 for between CallSpacing and WeekdayCallEquity)

### Failure Mode 3: Only Registered in One Manager
**Symptom:** Works in normal mode, fails in resilience-aware mode (or vice versa)

**Cause:** Added to `create_default()` but forgot `create_resilience_aware()`

**Detection:**
```bash
python ../scripts/verify_constraints.py
# Shows: "Manager consistency: FAIL"
```

**Fix:** Add to both factory methods

### Failure Mode 4: Import but No Export
**Symptom:** ImportError when trying to use constraint

**Cause:** Imported in manager.py but not exported from __init__.py

**Detection:**
```python
from app.scheduling.constraints import WeekendCallLimitConstraint
# ImportError: cannot import name 'WeekendCallLimitConstraint'
```

**Fix:** Add to __all__ list in constraints/__init__.py

### Failure Mode 5: Tests Pass Locally, CI Fails
**Symptom:** Local tests pass, but CI reports "constraint not found"

**Cause:** Forgot to commit the constraint file or __init__.py update

**Prevention:** Double-check `git status` before pushing

## Integration with Other Skills

### With `code-review`
**When:** After implementing constraint, before committing
**Purpose:** Review constraint logic, type hints, docstrings
**Workflow:**
1. Complete constraint implementation
2. Invoke code-review skill to check quality
3. Address any issues found
4. Run pre-flight verification
5. Commit

### With `test-writer`
**When:** Need comprehensive test coverage for complex constraint
**Purpose:** Generate edge case tests
**Workflow:**
1. Implement basic constraint
2. Invoke test-writer with constraint logic
3. Review generated tests
4. Add to test suite
5. Run pre-flight verification

### With `systematic-debugger`
**When:** Constraint not behaving as expected in solver
**Purpose:** Debug why constraint isn't being enforced
**Workflow:**
1. Notice constraint violation in generated schedule
2. Invoke systematic-debugger
3. Check if constraint is registered (often the issue!)
4. Debug constraint logic if registered
5. Fix and re-verify

### With `schedule-optimization`
**When:** Understanding how constraint affects schedule quality
**Purpose:** Tune constraint weights for optimal results
**Workflow:**
1. Implement and register constraint
2. Invoke schedule-optimization to test impact
3. Adjust weight based on results
4. Re-run verification
5. Document weight rationale

### With `database-migration`
**When:** Constraint needs new database fields (e.g., max_consecutive preference per person)
**Purpose:** Coordinate schema changes with constraint implementation
**Workflow:**
1. Invoke database-migration to add fields
2. Implement constraint using new fields
3. Register constraint
4. Test with migration applied
5. Commit both migration and constraint

## Escalation Rules

Escalate to human when:
1. Pre-flight verification fails with unclear errors
2. Weight hierarchy decisions need clinical input
3. New constraint category needs architectural review
4. Constraint affects ACGME compliance rules
5. Constraint requires database schema changes
6. Multiple constraints conflict with each other
