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

***REMOVED******REMOVED*** Workflow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│            CONSTRAINT PRE-FLIGHT WORKFLOW                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STEP 1: Implement Constraint Class                             │
│  ┌────────────────────────────────────────────────┐             │
│  │ Create class in constraints/*.py               │             │
│  │ Implement: __init__, add_to_cpsat,             │             │
│  │            add_to_pulp, validate                │             │
│  └────────────────────────────────────────────────┘             │
│                         ↓                                        │
│  STEP 2: Export in __init__.py                                  │
│  ┌────────────────────────────────────────────────┐             │
│  │ Add import statement                           │             │
│  │ Add to __all__ list                            │             │
│  └────────────────────────────────────────────────┘             │
│                         ↓                                        │
│  STEP 3: Register in ConstraintManager (CRITICAL!)              │
│  ┌────────────────────────────────────────────────┐             │
│  │ Import in manager.py                           │             │
│  │ Add to create_default()                        │             │
│  │ Add to create_resilience_aware()               │             │
│  │ ⚠️ MUST BE IN BOTH FACTORY METHODS             │             │
│  └────────────────────────────────────────────────┘             │
│                         ↓                                        │
│  STEP 4: Write Tests                                            │
│  ┌────────────────────────────────────────────────┐             │
│  │ Unit tests for constraint logic                │             │
│  │ Registration test in manager                   │             │
│  │ Integration test with scheduler                │             │
│  └────────────────────────────────────────────────┘             │
│                         ↓                                        │
│  STEP 5: Run Pre-Flight Verification (MANDATORY)                │
│  ┌────────────────────────────────────────────────┐             │
│  │ python ../scripts/verify_constraints.py        │             │
│  │ ✓ Registration check                           │             │
│  │ ✓ Weight hierarchy check                       │             │
│  │ ✓ Manager consistency check                    │             │
│  └────────────────────────────────────────────────┘             │
│                         ↓                                        │
│  STEP 6: Commit Only If All Pass                                │
│  ┌────────────────────────────────────────────────┐             │
│  │ All verifications PASS                         │             │
│  │ Tests PASS                                     │             │
│  │ → Safe to commit                               │             │
│  └────────────────────────────────────────────────┘             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED*** Concrete Usage Example: Adding FridayCallAvoidanceConstraint

**Scenario:** Program director wants to minimize Friday call assignments to improve weekend coverage.

***REMOVED******REMOVED******REMOVED*** Complete Implementation Walkthrough

**Step 1: Implement the Constraint Class**

```python
***REMOVED*** backend/app/scheduling/constraints/friday_call_avoidance.py

"""Soft constraint to minimize Friday call assignments."""

from typing import Any, Dict, List
from app.scheduling.constraints.base import SoftConstraint, ConstraintResult
from app.scheduling.constraints.types import ConstraintType, ConstraintPriority


class FridayCallAvoidanceConstraint(SoftConstraint):
    """
    Minimize Friday inpatient call assignments to improve weekend coverage.

    Clinical rationale: Friday call often extends into Saturday coverage,
    reducing resident availability for weekend shifts.

    Weight: 3.0 (medium-low priority, below call equity constraints)
    """

    def __init__(self, weight: float = 3.0) -> None:
        super().__init__(
            name="FridayCallAvoidance",
            constraint_type=ConstraintType.PREFERENCE,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )

    def add_to_cpsat(
        self, model: Any, variables: Dict[str, Any], context: Dict[str, Any]
    ) -> None:
        """Add penalty for Friday call assignments in CP-SAT solver."""
        ***REMOVED*** Implementation details...
        pass

    def add_to_pulp(
        self, model: Any, variables: Dict[str, Any], context: Dict[str, Any]
    ) -> None:
        """Add penalty for Friday call assignments in PuLP solver."""
        ***REMOVED*** Implementation details...
        pass

    def validate(
        self, assignments: List[Any], context: Dict[str, Any]
    ) -> ConstraintResult:
        """Validate Friday call distribution."""
        ***REMOVED*** Implementation details...
        pass
```

**Step 2: Export in __init__.py**

```python
***REMOVED*** backend/app/scheduling/constraints/__init__.py

from .friday_call_avoidance import FridayCallAvoidanceConstraint

__all__ = [
    ***REMOVED*** ... existing exports ...
    "CallSpacingConstraint",
    "SundayCallEquityConstraint",
    "TuesdayCallPreferenceConstraint",
    "WeekdayCallEquityConstraint",
    ***REMOVED*** NEW:
    "FridayCallAvoidanceConstraint",  ***REMOVED*** ← Add this!
]
```

**Step 3: Register in ConstraintManager (CRITICAL!)**

```python
***REMOVED*** backend/app/scheduling/constraints/manager.py

from .friday_call_avoidance import FridayCallAvoidanceConstraint

class ConstraintManager:
    @classmethod
    def create_default(cls) -> "ConstraintManager":
        """Create manager with standard constraint set."""
        manager = cls()

        ***REMOVED*** ... existing constraints ...

        ***REMOVED*** Call equity constraints (weight hierarchy matters!)
        manager.add(SundayCallEquityConstraint(weight=10.0))
        manager.add(CallSpacingConstraint(weight=8.0))
        manager.add(WeekdayCallEquityConstraint(weight=5.0))
        manager.add(TuesdayCallPreferenceConstraint(weight=2.0))

        ***REMOVED*** NEW: Add Friday avoidance (weight=3.0, below call equity)
        manager.add(FridayCallAvoidanceConstraint(weight=3.0))  ***REMOVED*** ← Add this!

        return manager

    @classmethod
    def create_resilience_aware(
        cls,
        n1_compliant: bool = True,
        utilization_cap: float = 0.8,
        defense_level: int = 2,
    ) -> "ConstraintManager":
        """Create manager with resilience-aware constraints."""
        manager = cls()

        ***REMOVED*** ... existing constraints ...

        ***REMOVED*** Call preferences
        manager.add(SundayCallEquityConstraint(weight=10.0))
        manager.add(CallSpacingConstraint(weight=8.0))
        manager.add(WeekdayCallEquityConstraint(weight=5.0))
        manager.add(TuesdayCallPreferenceConstraint(weight=2.0))

        ***REMOVED*** NEW: Add here too!
        manager.add(FridayCallAvoidanceConstraint(weight=3.0))  ***REMOVED*** ← And this!

        return manager
```

**Step 4: Write Tests**

```python
***REMOVED*** backend/tests/test_friday_call_avoidance.py

import pytest
from app.scheduling.constraints import (
    FridayCallAvoidanceConstraint,
    ConstraintManager,
)


class TestFridayCallAvoidanceConstraint:
    def test_constraint_initialization(self):
        """Verify constraint initializes with correct values."""
        constraint = FridayCallAvoidanceConstraint()
        assert constraint.name == "FridayCallAvoidance"
        assert constraint.weight == 3.0
        assert constraint.constraint_type == ConstraintType.PREFERENCE

    def test_custom_weight(self):
        """Test constraint with custom weight."""
        constraint = FridayCallAvoidanceConstraint(weight=5.0)
        assert constraint.weight == 5.0

    def test_constraint_registered_in_default_manager(self):
        """CRITICAL: Verify constraint is in create_default()."""
        manager = ConstraintManager.create_default()
        registered_types = {type(c) for c in manager.constraints}
        assert FridayCallAvoidanceConstraint in registered_types

    def test_constraint_registered_in_resilience_manager(self):
        """CRITICAL: Verify constraint is in create_resilience_aware()."""
        manager = ConstraintManager.create_resilience_aware()
        registered_types = {type(c) for c in manager.constraints}
        assert FridayCallAvoidanceConstraint in registered_types

    def test_validate_friday_distribution(self):
        """Test validation logic for Friday call assignments."""
        ***REMOVED*** Implementation...
        pass
```

**Step 5: Run Pre-Flight Verification**

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

***REMOVED*** Run verification script
python ../scripts/verify_constraints.py
```

**Expected Output:**
```
============================================================
CONSTRAINT PRE-FLIGHT VERIFICATION
============================================================

============================================================
CONSTRAINT REGISTRATION VERIFICATION
============================================================

Registered constraints (24 total):  ***REMOVED*** ← Was 23, now 24
  - 1in7Rule: ENABLED
  - 80HourRule: ENABLED
  - Availability: ENABLED
  - CallSpacing: ENABLED weight=8.0
  ...
  - FridayCallAvoidance: ENABLED weight=3.0  ***REMOVED*** ← NEW!

Block 10 Constraint Check:
  [OK] CallSpacingConstraint
  [OK] SundayCallEquityConstraint
  [OK] TuesdayCallPreferenceConstraint
  [OK] WeekdayCallEquityConstraint
  [OK] FridayCallAvoidanceConstraint  ***REMOVED*** ← NEW!

============================================================
WEIGHT HIERARCHY VERIFICATION
============================================================

Call preference weight hierarchy:
  [OK] SundayCallEquity: weight=10.0
  [OK] CallSpacing: weight=8.0
  [OK] WeekdayCallEquity: weight=5.0
  [OK] FridayCallAvoidance: weight=3.0  ***REMOVED*** ← NEW! Correctly positioned
  [OK] TuesdayCallPreference: weight=2.0

============================================================
MANAGER CONSISTENCY VERIFICATION
============================================================

Block 10 constraints in both managers:
  [OK] FridayCallAvoidance  ***REMOVED*** ← In both create_default() and create_resilience_aware()

============================================================
SUMMARY
============================================================
  Registration: PASS ✓
  Weight Hierarchy: PASS ✓
  Manager Consistency: PASS ✓

[SUCCESS] All verifications passed!
```

**Step 6: Run Tests and Commit**

```bash
***REMOVED*** Run tests
pytest tests/test_friday_call_avoidance.py -v
pytest tests/test_constraint_registration.py -v

***REMOVED*** All pass? Commit!
git add backend/app/scheduling/constraints/friday_call_avoidance.py
git add backend/app/scheduling/constraints/__init__.py
git add backend/app/scheduling/constraints/manager.py
git add backend/tests/test_friday_call_avoidance.py

git commit -m "$(cat <<'EOF'
feat: add FridayCallAvoidanceConstraint to minimize Friday calls

Implements soft constraint (weight=3.0) to reduce Friday inpatient
call assignments, improving weekend coverage availability.

- Constraint registered in both default and resilience-aware managers
- Weight positioned below call equity (5.0) but above Tuesday preference (2.0)
- Verified with pre-flight check and registration tests
EOF
)"
```

***REMOVED******REMOVED*** Failure Mode Handling

***REMOVED******REMOVED******REMOVED*** Failure Mode 1: Constraint Not Registered

**Symptom:**
```bash
$ python ../scripts/verify_constraints.py

[ERROR] FridayCallAvoidanceConstraint exported but NOT registered in ConstraintManager!
```

**Root cause:** Forgot Step 3 (registering in manager.py)

**Recovery:**
```python
***REMOVED*** 1. Add to manager.py
from .friday_call_avoidance import FridayCallAvoidanceConstraint

***REMOVED*** 2. Add to BOTH factory methods
def create_default(cls):
    manager.add(FridayCallAvoidanceConstraint(weight=3.0))  ***REMOVED*** Add this!

def create_resilience_aware(cls, ...):
    manager.add(FridayCallAvoidanceConstraint(weight=3.0))  ***REMOVED*** And this!

***REMOVED*** 3. Re-run verification
python ../scripts/verify_constraints.py
***REMOVED*** Should now PASS
```

***REMOVED******REMOVED******REMOVED*** Failure Mode 2: Weight Hierarchy Violation

**Symptom:**
```bash
$ python ../scripts/verify_constraints.py

[WARNING] Weight hierarchy violated:
  SundayCallEquity: 10.0
  CallSpacing: 8.0
  FridayCallAvoidance: 9.0  ← TOO HIGH! Should be < 8.0
  WeekdayCallEquity: 5.0
```

**Root cause:** Weight set too high, violating call equity hierarchy

**Recovery:**
```python
***REMOVED*** 1. Adjust weight in manager.py
***REMOVED*** OLD:
manager.add(FridayCallAvoidanceConstraint(weight=9.0))  ***REMOVED*** Wrong!

***REMOVED*** NEW:
manager.add(FridayCallAvoidanceConstraint(weight=3.0))  ***REMOVED*** Correct

***REMOVED*** 2. Document rationale
***REMOVED*** Weight must be < 5.0 (below WeekdayCallEquity)
***REMOVED*** but > 2.0 (above TuesdayCallPreference)
***REMOVED*** because Friday avoidance is more important than day preference

***REMOVED*** 3. Re-run verification
python ../scripts/verify_constraints.py
```

***REMOVED******REMOVED******REMOVED*** Failure Mode 3: Missing from One Manager

**Symptom:**
```bash
$ python ../scripts/verify_constraints.py

[ERROR] Manager consistency check FAILED:
  FridayCallAvoidance in create_default() ✓
  FridayCallAvoidance in create_resilience_aware() ✗ MISSING!
```

**Root cause:** Added to `create_default()` but forgot `create_resilience_aware()`

**Recovery:**
```python
***REMOVED*** Add to BOTH methods:
@classmethod
def create_resilience_aware(cls, ...):
    manager = cls()
    ***REMOVED*** ... other constraints ...
    manager.add(FridayCallAvoidanceConstraint(weight=3.0))  ***REMOVED*** ← Add this!
    return manager
```

***REMOVED******REMOVED******REMOVED*** Failure Mode 4: Tests Fail Despite Correct Code

**Symptom:**
```bash
$ pytest tests/test_constraint_registration.py -v

FAILED test_constraint_registered_in_default_manager
AssertionError: FridayCallAvoidanceConstraint not in registered types
```

**Root cause:** Test ran before constraint was imported in manager

**Recovery:**
```bash
***REMOVED*** 1. Verify import exists in manager.py
grep "FridayCallAvoidanceConstraint" backend/app/scheduling/constraints/manager.py

***REMOVED*** 2. If missing, add import:
from .friday_call_avoidance import FridayCallAvoidanceConstraint

***REMOVED*** 3. Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

***REMOVED*** 4. Re-run tests
pytest tests/test_constraint_registration.py -v
```

***REMOVED******REMOVED*** Integration with Other Skills

***REMOVED******REMOVED******REMOVED*** With automated-code-fixer

**Scenario:** Pre-flight fails, automated-code-fixer can add registration

```
[constraint-preflight detects missing registration]
→ "FridayCallAvoidanceConstraint exported but not registered"

[Invoke automated-code-fixer]
→ automated-code-fixer adds manager.add() lines to both methods
→ Re-runs verification
→ All checks PASS
→ Commits fix
```

***REMOVED******REMOVED******REMOVED*** With test-writer

**Workflow:**
```
[User creates new constraint class]
[constraint-preflight activated]

Step 1-3: Implement, export, register
Step 4: Invoke test-writer skill

"Generate comprehensive tests for FridayCallAvoidanceConstraint:
- Initialization tests
- Registration tests
- Validation logic tests
- Weight hierarchy tests"

[test-writer generates test suite]
[constraint-preflight verifies tests cover registration]
```

***REMOVED******REMOVED******REMOVED*** With code-review

**Pre-commit integration:**
```
[About to commit constraint changes]
[constraint-preflight runs verification]
→ All checks PASS

[Invoke code-review skill]
→ Reviews constraint implementation
→ Checks weight rationale is documented
→ Verifies clinical justification in docstring
→ Approves or requests changes

[Commit only after both skills approve]
```

***REMOVED******REMOVED******REMOVED*** With pr-reviewer

**PR workflow:**
```
[PR created with new constraint]
[pr-reviewer activated]

→ Detects constraint-related changes
→ Invokes constraint-preflight automatically
→ Runs verification in CI
→ Includes verification output in PR review:

"Constraint Pre-Flight Check: PASS ✓
- Registration verified
- Weight hierarchy correct
- Manager consistency confirmed"
```

***REMOVED******REMOVED*** Validation Checklist

***REMOVED******REMOVED******REMOVED*** Pre-Implementation Checklist
- [ ] Constraint purpose is clear and documented
- [ ] Clinical/operational rationale defined
- [ ] Weight determined relative to existing constraints
- [ ] Decided if hard or soft constraint
- [ ] Identified which managers need registration

***REMOVED******REMOVED******REMOVED*** Implementation Checklist
- [ ] Constraint class created with all required methods
- [ ] Docstring explains purpose and rationale
- [ ] Exported in `__init__.py`
- [ ] Imported in `manager.py`
- [ ] Added to `create_default()`
- [ ] Added to `create_resilience_aware()` (if applicable)
- [ ] Weight documented with justification

***REMOVED******REMOVED******REMOVED*** Testing Checklist
- [ ] Unit tests for constraint logic
- [ ] Registration test in default manager
- [ ] Registration test in resilience manager (if applicable)
- [ ] Weight hierarchy test (for soft constraints)
- [ ] Integration test with scheduler
- [ ] All tests PASS

***REMOVED******REMOVED******REMOVED*** Verification Checklist
- [ ] Run `python ../scripts/verify_constraints.py`
- [ ] Registration check: PASS
- [ ] Weight hierarchy check: PASS
- [ ] Manager consistency check: PASS
- [ ] Run `pytest tests/test_constraint_registration.py -v`: ALL PASS
- [ ] Run full test suite: ALL PASS

***REMOVED******REMOVED******REMOVED*** Pre-Commit Checklist
- [ ] All verification checks PASS
- [ ] All tests PASS
- [ ] No linting errors
- [ ] Weight rationale documented in code
- [ ] Clinical justification in docstring
- [ ] Ready to commit

***REMOVED******REMOVED******REMOVED*** Escalation Checklist

**Escalate to human if ANY of these are true:**
- [ ] New constraint category (not equity/preference/workload)
- [ ] Weight hierarchy decision needs clinical input
- [ ] Affects ACGME compliance rules
- [ ] Conflicts with existing constraints
- [ ] Requires new solver techniques
- [ ] Pre-flight verification fails with unclear errors

***REMOVED******REMOVED*** Escalation Rules

Escalate to human when:
1. Pre-flight verification fails with unclear errors
2. Weight hierarchy decisions need clinical input
3. New constraint category needs architectural review
4. Constraint affects ACGME compliance rules
