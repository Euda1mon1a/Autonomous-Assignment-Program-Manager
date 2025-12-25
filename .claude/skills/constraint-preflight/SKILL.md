---
name: constraint-preflight
description: Pre-flight verification for scheduling constraint development. Use when adding, modifying, or testing constraints to ensure they are properly implemented, exported, registered, and tested before commit.
---

***REMOVED*** Constraint Pre-Flight Verification

Prevents the "implemented but not registered" bug where constraints are created, tested, and exported but never added to the ConstraintManager factory methods.

***REMOVED******REMOVED*** When This Skill Activates

- When creating new scheduling constraints
- When modifying existing constraints
- Before committing constraint-related changes
- When the user asks to verify constraint registration
- After adding constraints to `__init__.py` exports

***REMOVED******REMOVED*** The Constraint Gap Problem

***REMOVED******REMOVED******REMOVED*** What Goes Wrong

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

***REMOVED******REMOVED******REMOVED*** Why It Happens

- Tests verify constraint logic in isolation
- Tests don't verify the constraint is actually used by the scheduler
- Manual verification of "registered at line X" is error-prone
- No CI check catches unregistered constraints

***REMOVED******REMOVED*** Pre-Flight Verification Script

Run this before committing any constraint changes:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend
python ../scripts/verify_constraints.py
```

***REMOVED******REMOVED******REMOVED*** What It Checks

1. **Registration** - All exported constraints are in `ConstraintManager.create_default()`
2. **Weight Hierarchy** - Soft constraint weights follow documented order
3. **Manager Consistency** - Constraints in both `create_default()` and `create_resilience_aware()`

***REMOVED******REMOVED******REMOVED*** Expected Output

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

***REMOVED******REMOVED*** Constraint Development Checklist

When creating a new constraint:

***REMOVED******REMOVED******REMOVED*** Step 1: Implement Constraint Class

```python
***REMOVED*** backend/app/scheduling/constraints/my_constraint.py

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
        ***REMOVED*** CP-SAT implementation
        pass

    def add_to_pulp(self, model, variables, context) -> None:
        ***REMOVED*** PuLP implementation
        pass

    def validate(self, assignments, context) -> ConstraintResult:
        ***REMOVED*** Validation implementation
        pass
```

***REMOVED******REMOVED******REMOVED*** Step 2: Export in `__init__.py`

```python
***REMOVED*** backend/app/scheduling/constraints/__init__.py

from .my_constraint import MyNewConstraint

__all__ = [
    ***REMOVED*** ... existing exports ...
    "MyNewConstraint",
]
```

***REMOVED******REMOVED******REMOVED*** Step 3: Register in Manager (CRITICAL!)

```python
***REMOVED*** backend/app/scheduling/constraints/manager.py

from .my_constraint import MyNewConstraint

class ConstraintManager:
    @classmethod
    def create_default(cls) -> "ConstraintManager":
        manager = cls()
        ***REMOVED*** ... existing constraints ...
        manager.add(MyNewConstraint(weight=5.0))  ***REMOVED*** ADD THIS!
        return manager

    @classmethod
    def create_resilience_aware(cls, ...) -> "ConstraintManager":
        manager = cls()
        ***REMOVED*** ... existing constraints ...
        manager.add(MyNewConstraint(weight=5.0))  ***REMOVED*** ADD THIS TOO!
        return manager
```

***REMOVED******REMOVED******REMOVED*** Step 4: Write Tests

```python
***REMOVED*** backend/tests/test_my_constraint.py

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

***REMOVED******REMOVED******REMOVED*** Step 5: Run Pre-Flight Verification

```bash
cd backend
python ../scripts/verify_constraints.py
```

***REMOVED******REMOVED******REMOVED*** Step 6: Commit Only If All Pass

```bash
git add .
git commit -m "feat: add MyNewConstraint for [purpose]"
```

***REMOVED******REMOVED*** Test Coverage

The `test_constraint_registration.py` file provides automated CI coverage:

```python
***REMOVED*** Key tests that prevent the registration gap:

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

***REMOVED******REMOVED*** Quick Commands

```bash
***REMOVED*** Run pre-flight verification
cd backend && python ../scripts/verify_constraints.py

***REMOVED*** Run constraint registration tests only
cd backend && pytest tests/test_constraint_registration.py -v

***REMOVED*** Run all constraint tests
cd backend && pytest tests/test_*constraint*.py -v

***REMOVED*** Check manager.py for registrations
grep -n "manager.add" backend/app/scheduling/constraints/manager.py
```

***REMOVED******REMOVED*** Key Files

| File | Purpose |
|------|---------|
| `scripts/verify_constraints.py` | Pre-flight verification script |
| `backend/tests/test_constraint_registration.py` | CI tests for registration |
| `backend/app/scheduling/constraints/manager.py` | Where constraints are registered |
| `backend/app/scheduling/constraints/__init__.py` | Where constraints are exported |

***REMOVED******REMOVED*** Weight Hierarchy Reference

For call equity constraints, follow this hierarchy (highest impact first):

| Constraint | Weight | Rationale |
|------------|--------|-----------|
| SundayCallEquity | 10.0 | Worst call day, highest priority |
| CallSpacing | 8.0 | Burnout prevention |
| WeekdayCallEquity | 5.0 | Balance Mon-Thu calls |
| TuesdayCallPreference | 2.0 | Academic scheduling preference |
| DeptChiefWednesdayPreference | 1.0 | Personal preference (lowest) |

***REMOVED******REMOVED*** Escalation Rules

Escalate to human when:
1. Pre-flight verification fails with unclear errors
2. Weight hierarchy decisions need clinical input
3. New constraint category needs architectural review
4. Constraint affects ACGME compliance rules
