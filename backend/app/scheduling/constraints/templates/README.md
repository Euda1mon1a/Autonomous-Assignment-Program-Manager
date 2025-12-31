# Constraint Templates

This directory contains templates for creating new constraints in the scheduler.

## Available Templates

### Hard Constraints (Must Be Satisfied)

1. **hard_constraint_template.py** - Base template for hard constraints
   - Enforces business rules that cannot be violated
   - Violations make schedule infeasible
   - Use for ACGME rules, capacity limits, availability
   - Example: Availability, Capacity, Supervision

2. **temporal_constraint_template.py** - Time-based constraints
   - Day-of-week restrictions (Wednesday-only rotations)
   - Time-of-block constraints (AM/PM specificity)
   - Date range enforcement
   - Recovery period requirements
   - Example: Wednesday constraints, Post-call recovery

3. **resource_constraint_template.py** - Resource allocation constraints
   - Clinic capacity limits
   - Faculty workload caps
   - Equipment/facility availability
   - Room booking constraints
   - Example: Clinic capacity, Max physicians in clinic

4. **sequence_constraint_template.py** - Ordered relationships
   - Prerequisite rotation requirements
   - Post-duty sequence enforcement
   - Recovery rotation requirements
   - Example: Post-call auto-assignment, FMIT recovery

5. **exclusion_constraint_template.py** - Prohibition constraints
   - Person type exclusions (adjuncts from call)
   - Role-based restrictions
   - Eligibility requirements
   - Example: Adjunct call exclusion, Ineligible clinics

### Soft Constraints (Optimization Objectives)

6. **soft_constraint_template.py** - Base template for soft constraints
   - Optimization objectives with weights
   - Violations add penalties to objective
   - Can be relaxed if needed
   - Example: Equity, Continuity, Preferences

7. **preference_constraint_template.py** - Individual preferences
   - Scheduling wish lists
   - Time-of-day preferences
   - Rotation type preferences
   - Example: Faculty preferences, Time-slot preferences

8. **fairness_constraint_template.py** - Equitable distribution
   - Call distribution fairness
   - Weekend duty balance
   - Specialty rotation equality
   - Example: Call equity, Weekend balance

9. **coverage_constraint_template.py** - Coverage requirements
   - All required slots filled
   - Minimum staffing levels
   - Service availability
   - Example: Clinic coverage, Call coverage

### Composite Constraints

10. **composite_constraint_template.py** - Multi-constraint groups
    - Combines related constraints
    - Simplifies constraint management
    - Example: FMIT constraint group, Call management group

## How to Use Templates

### Creating a New Hard Constraint

1. Copy `hard_constraint_template.py`
2. Rename class to your constraint name (e.g., `MyRotationConstraint`)
3. Update docstring with constraint description
4. Implement `_violates_constraint()` method
5. Update `add_to_cpsat()` and `add_to_pulp()` methods
6. Implement `validate()` method
7. Add unit tests to `backend/tests/scheduling/constraints/`
8. Register in `backend/app/scheduling/constraints/manager.py`

```python
# Example: Custom rotation constraint
class CustomRotationConstraint(HardConstraint):
    """Ensures residents complete required rotation sequence."""

    def __init__(self):
        super().__init__(
            name="CustomRotation",
            constraint_type=ConstraintType.ROTATION,
            priority=ConstraintPriority.HIGH,
        )

    def _violates_constraint(self, assignment, context):
        # Check if resident can take this rotation
        resident = self._get_resident(assignment.person_id, context)
        rotation = self._get_rotation(assignment.rotation_id, context)
        return not resident.can_take(rotation)
```

### Creating a New Soft Constraint

1. Copy `soft_constraint_template.py`
2. Rename class to your constraint name
3. Update docstring and weight guidelines
4. Implement `_violates_constraint()` method
5. Update penalty calculation in `validate()`
6. Implement `add_to_cpsat()` and `add_to_pulp()` if needed
7. Add unit tests
8. Register in manager

```python
# Example: Specialty preference constraint
class SpecialtyPreferenceConstraint(SoftConstraint):
    """Prefers resident assignments to their specialty rotation."""

    def __init__(self, weight: float = 1.0):
        super().__init__(
            name="SpecialtyPreference",
            constraint_type=ConstraintType.PREFERENCE,
            weight=weight,
        )

    def _violates_preference(self, assignment, context):
        resident = self._get_resident(assignment.person_id, context)
        rotation = self._get_rotation(assignment.rotation_id, context)
        return resident.specialty != rotation.specialty
```

### Creating a Composite Constraint

1. Copy `composite_constraint_template.py`
2. Define group name and component constraints
3. Register in manager as a single unit

```python
# Example: Surgical call constraint group
class CompositeSurgicalCallConstraint(CompositeConstraint):
    """All surgical call-related constraints."""
    def __init__(self):
        super().__init__(
            name="SurgicalCall",
            constraints=[
                SurgicalCallMandatoryConstraint(),
                SurgicalCallSpacingConstraint(),
                SurgicalPostCallRecoveryConstraint(),
            ]
        )
```

## Template Selection Guide

| Need | Template | Type |
|------|----------|------|
| ACGME rule enforcement | hard_constraint | Hard |
| Availability/absence blocking | hard_constraint | Hard |
| Capacity limit (clinics, faculty) | resource_constraint | Hard |
| Day-of-week restriction | temporal_constraint | Hard |
| Prevent invalid combinations | exclusion_constraint | Hard |
| Required sequence (call→post-call) | sequence_constraint | Hard |
| Fair distribution | fairness_constraint | Soft |
| Personal scheduling preference | preference_constraint | Soft |
| Coverage gap filling | coverage_constraint | Soft |
| Multiple related rules | composite_constraint | Either |

## Common Parameters

### Hard Constraint __init__()
```python
def __init__(self):
    super().__init__(
        name="ConstraintName",
        constraint_type=ConstraintType.XXX,  # Choose appropriate type
        priority=ConstraintPriority.HIGH,     # CRITICAL, HIGH, MEDIUM, LOW
    )
```

### Soft Constraint __init__()
```python
def __init__(self, weight: float = 1.0):
    super().__init__(
        name="ConstraintName",
        constraint_type=ConstraintType.XXX,
        weight=weight,  # Higher = more important
        priority=ConstraintPriority.MEDIUM,
    )
```

## Weight Guidelines for Soft Constraints

- **0.1-0.5**: Nice-to-have optimizations (low priority)
- **0.5-1.0**: Preferences (moderate priority)
- **1.0-1.5**: Important objectives (high priority)
- **1.5-2.5**: Critical soft requirements (very high)
- **2.5+**: Nearly hard constraints (enforce strongly)

Multiply weight by priority.value:
- CRITICAL (100) × 1.0 weight = penalty 100
- HIGH (75) × 1.5 weight = penalty 112.5
- MEDIUM (50) × 1.0 weight = penalty 50
- LOW (25) × 0.5 weight = penalty 12.5

## Testing Constraints

Each constraint should have unit tests:

```python
# tests/scheduling/constraints/test_my_constraint.py

import pytest
from app.scheduling.constraints.my_module import MyConstraint
from app.scheduling.constraints.base import SchedulingContext

@pytest.fixture
def constraint():
    return MyConstraint()

@pytest.fixture
def context():
    return SchedulingContext(residents=[], faculty=[], blocks=[], templates=[])

def test_constraint_satisfied(constraint, context):
    """Test valid schedule satisfies constraint."""
    assignments = create_valid_assignments()
    result = constraint.validate(assignments, context)
    assert result.satisfied

def test_constraint_violated(constraint, context):
    """Test invalid schedule violates constraint."""
    assignments = create_invalid_assignments()
    result = constraint.validate(assignments, context)
    assert not result.satisfied
    assert len(result.violations) > 0
```

## Registering a New Constraint

1. Import in `backend/app/scheduling/constraints/manager.py`:
   ```python
   from .my_module import MyConstraint
   ```

2. Add to manager imports at top

3. Use in constraint manager:
   ```python
   manager = ConstraintManager()
   manager.add(MyConstraint())
   ```

4. Enable/disable as needed:
   ```python
   manager.enable("MyConstraint")
   manager.disable("MyConstraint")
   ```

## See Also

- [Constraint Catalog](../CONSTRAINT_CATALOG.md) - Complete constraint reference
- [Constraint Builder](../constraint_builder.py) - Fluent API for creating constraints
- [Constraint Validator](../constraint_validator.py) - Pre-solver validation
- [Constraint Registry](../constraint_registry.py) - Constraint registration system

## Example Implementation Files

- `backend/app/scheduling/constraints/acgme.py` - ACGME constraints (hard)
- `backend/app/scheduling/constraints/capacity.py` - Resource constraints (hard)
- `backend/app/scheduling/constraints/equity.py` - Fairness constraints (soft)
- `backend/app/scheduling/constraints/resilience.py` - Resilience constraints (soft)

---

**Last Updated:** 2025-12-31
**Maintained By:** Residency Scheduler Team
