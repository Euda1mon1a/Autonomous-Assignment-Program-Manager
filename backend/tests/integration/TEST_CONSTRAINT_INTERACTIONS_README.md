# Constraint Interaction Tests

## Overview

This test suite (`test_constraint_interactions.py`) implements comprehensive integration tests for complex constraint interaction scenarios based on the test frames defined in `docs/testing/TEST_SCENARIO_FRAMES.md`.

## Test Coverage

### 1. `test_conflicting_hard_constraints`
**Frame**: 3.1 from TEST_SCENARIO_FRAMES.md

**Scenario**: Resident must attend mandatory conference (hard constraint) AND cover call (hard constraint) simultaneously.

**Setup**:
- Creates a PGY-2 resident
- Creates a conference block on Wednesday AM
- Creates a call assignment for the same time slot
- Implements `ConferenceConstraint` as a hard constraint

**Validation**:
- Detects conflicting hard constraints
- Returns `satisfied=False`
- Generates CRITICAL severity violations
- Includes detailed violation information (person_id, block_id, conflict type)

**Expected Behavior**:
- Conflict should be detected before assignment creation in production
- Test verifies the constraint validation logic works correctly

---

### 2. `test_soft_constraint_zero_weight`
**Frame**: 3.2 from TEST_SCENARIO_FRAMES.md

**Scenario**: Preference constraint with `weight=0` should be effectively disabled.

**Setup**:
- Creates a PGY-1 resident who prefers AM shifts
- Assigns resident to PM shift (violates preference)
- Creates two `PreferenceConstraint` instances:
  - One with `weight=0.0` (disabled)
  - One with `weight=5.0` (active) for comparison

**Validation**:
- Zero-weight constraint produces `penalty=0.0`
- Zero-weight constraint returns `satisfied=True`
- Non-zero weight constraint produces `penalty > 0.0`
- Violations are recorded but have no impact when weight is zero

**Expected Behavior**:
- Allows runtime disabling of soft constraints
- Useful for A/B testing different optimization strategies

---

### 3. `test_credential_expiring_mid_block`
**Frame**: 3.3 from TEST_SCENARIO_FRAMES.md

**Scenario**: Faculty assigned to 4-week block, BLS credential expires in week 2.

**Setup**:
- Creates faculty member with procedure credentials
- Creates 4-week inpatient assignment (Jan 1-28)
- Mock credential data: BLS expires Jan 15 (mid-assignment)
- Implements `CredentialExpiringConstraint` to detect mid-block expirations

**Validation**:
- Assignment is `satisfied=True` (valid at start)
- Generates HIGH severity warning about expiration
- Calculates days until expiration
- Applies penalty for proactive flagging
- Includes detailed credential information

**Expected Behavior**:
- Proactive warning for administrators
- Allows assignment but flags for review
- Supports renewal workflow integration

**Note**: This test uses mock credential data since the credential model is not yet fully implemented in the system. When the credential model is added, this test should be updated to use real credential objects.

---

### 4. `test_leave_overlapping_call_assignment`
**Frame**: 3.4 from TEST_SCENARIO_FRAMES.md

**Scenario**: Faculty requests vacation leave for dates they're assigned to call.

**Setup**:
- Creates faculty member
- Creates 24-hour call assignment (Jan 15-16)
- Creates vacation absence overlapping call dates (Jan 15-17)
- Implements `LeaveConflictConstraint` to detect blocking absence conflicts

**Validation**:
- Returns `satisfied=False` (hard conflict)
- Generates CRITICAL severity violations
- Detects conflicts for all overlapping dates
- Includes absence details (type, start, end dates)

**Expected Behavior**:
- Prevents scheduling during blocking absences
- Flags need for coverage replacement
- Supports swap auto-matcher workflow integration

---

### 5. `test_multiple_constraints_validation`
**Bonus Test**: Ensures `ConstraintManager` correctly aggregates results

**Setup**:
- Creates resident with shift preferences
- Creates both AM and PM assignments
- Adds multiple constraints to ConstraintManager

**Validation**:
- Manager correctly aggregates violations
- Penalties are summed across constraints
- Result structure is correct
- Individual constraint violations are preserved

---

## Mock Constraint Implementations

The test file includes three mock constraint classes for testing purposes:

### `ConferenceConstraint` (HardConstraint)
- Marks specific blocks as mandatory conference attendance
- Detects conflicting assignments during conference times
- Returns CRITICAL violations for conflicts

### `PreferenceConstraint` (SoftConstraint)
- Models resident shift time preferences (AM/PM)
- Configurable weight (including zero for disabling)
- Calculates penalty based on preference violations

### `CredentialExpiringConstraint` (SoftConstraint)
- Detects credentials expiring during assignment periods
- Groups assignments by person and checks date ranges
- Returns HIGH severity warnings with detailed expiration info

### `LeaveConflictConstraint` (HardConstraint)
- Detects assignments during blocking absences
- Queries database for absence records
- Returns CRITICAL violations for any conflicts

---

## Running the Tests

```bash
# Run all constraint interaction tests
cd backend
pytest tests/integration/test_constraint_interactions.py -v

# Run specific test
pytest tests/integration/test_constraint_interactions.py::TestConstraintInteractions::test_conflicting_hard_constraints -v

# Run with coverage
pytest tests/integration/test_constraint_interactions.py --cov=app.scheduling.constraints --cov-report=html
```

---

## Dependencies

The tests require:
- `pytest` - Testing framework
- `sqlalchemy` - ORM and database models
- `app.models.*` - Person, Block, Assignment, Absence, RotationTemplate models
- `app.scheduling.constraints.*` - Constraint system (base classes, manager)

---

## Test Data Patterns

### Realistic Scenarios
All tests use realistic medical residency scenarios:
- PGY-level residents
- Faculty with procedure credentials
- Call assignments, clinic shifts, conferences
- Vacation and emergency leave types
- 24-hour call coverage periods

### Fixture-Free Design
Tests create their own data to ensure:
- Each test is self-contained
- Clear setup-action-assert flow
- Easy to understand without external context
- Follows patterns from existing integration tests

### Database Transaction Handling
- Uses `db` fixture from `conftest.py`
- Each test gets fresh database
- All data is committed before validation
- Clean teardown after each test

---

## Future Enhancements

### When Credential Model is Implemented:
1. Replace mock `CredentialExpiringConstraint` with real credential queries
2. Add tests for:
   - Grace periods after expiration
   - Credential renewal during assignment
   - Multiple credentials expiring at different times
   - Hard vs soft credential requirements

### Additional Constraint Interaction Tests:
3. **Cascading Constraint Failures** (Frame 4.2)
   - N-2 analysis triggering multiple violations
   - Defense level escalations

4. **Concurrent Operation Conflicts** (Frame 5.1)
   - Optimistic locking during swap execution
   - Race conditions in constraint validation

5. **Schedule Generation Edge Cases** (Frame 6.1)
   - Infeasible solutions due to conflicting constraints
   - Pareto optimization with competing objectives

---

## Integration with Constraint Service

These tests validate the constraint system used by:
- `app.services.constraint_service.py` - Schedule validation API
- `app.scheduling.engine.py` - Schedule generation
- `app.services.swap_executor.py` - Swap validation
- `app.api.routes/schedules.py` - Schedule validation endpoints

The mock constraints follow the same interface as production constraints, ensuring test scenarios accurately reflect real-world behavior.

---

## Test Maintenance

### When to Update:
- Adding new constraint types to the system
- Changing constraint validation logic
- Modifying database schema (Person, Block, Assignment, Absence)
- Implementing credential model
- Adding new test frames to TEST_SCENARIO_FRAMES.md

### Review Checklist:
- [ ] All imports resolve to actual files
- [ ] Database session handling is correct
- [ ] Context objects include all required data
- [ ] Assertions match expected constraint behavior
- [ ] Error messages are clear and actionable
- [ ] Mock constraints follow production patterns

---

**Last Updated**: 2025-12-26
**Based on**: docs/testing/TEST_SCENARIO_FRAMES.md (Frames 3.1-3.4)
**Maintainer**: Development Team
