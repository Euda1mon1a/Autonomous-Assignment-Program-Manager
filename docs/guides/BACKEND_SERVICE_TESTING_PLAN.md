# Backend Service Testing Plan
## SESSION 8 BURN: Service Layer Testing Prioritization

**Generated:** 2025-12-31
**Status:** ACTIONABLE IMPLEMENTATION GUIDE
**Risk Level:** HIGH (91.7% services untested per SESSION_1_BACKEND findings)

---

## Executive Summary

Based on SESSION_1_BACKEND analysis of 47 service classes across `backend/app/services/`:
- **44 services require comprehensive testing**
- **267 error handling blocks** need test coverage
- **87 eager loading operations** need N+1 validation tests
- **Test-driven refactoring required** for 3 services with over-engineering

---

## SECTION 1: SERVICE INVENTORY & PRIORITY TIERS

### Tier 1 - CRITICAL (Test Immediately)

**Core Domain Services** - Foundation for entire application

| Service | Lines | Dependencies | Risk | Priority |
|---------|-------|--------------|------|----------|
| `AssignmentService` | 472 | PersonRepo, BlockRepo | HIGH | **P0** |
| `PersonService` | 211 | None | HIGH | **P0** |
| `BlockService` | 126+ | AssignmentRepo | HIGH | **P0** |
| `SwapExecutor` | 337 | Multiple repos | CRITICAL | **P0** |
| `ACGMEValidator` | 80+ | None | CRITICAL | **P0** |
| `ConflictAutoResolver` | 180+ | PersonRepo, ConflictRepo | HIGH | **P0** |

**Testing Effort:** 40 hours
**Estimated Coverage:** 85% of schedule-related bugs

### Tier 2 - HIGH (Test Next Sprint)

**Feature Services** - Complex domain logic

| Service | Lines | Dependencies | Test Cases Needed |
|---------|-------|--------------|-------------------|
| `SwapValidationService` | 180+ | AssignmentRepo, ACGMEValidator | Validate all swap types |
| `SwapRequestService` | - | SwapRepo, NotificationService | CRUD + state transitions |
| `SwapAutoMatcher` | - | AssignmentRepo | Matching algorithm verification |
| `ConflictAutoDetector` | - | AssignmentRepo | Edge case conflict scenarios |
| `EmergencyCoverageService` | - | PersonRepo, BlockRepo | TDY/deployment scenarios |
| `FreezeHorizonService` | - | BlockRepo | Freeze date boundary testing |

**Testing Effort:** 30 hours
**Estimated Coverage:** 75% of swap-related bugs

### Tier 3 - MEDIUM (Test After Core)

**Utility/Framework Services**

| Service | Category | Purpose | Test Priority |
|---------|----------|---------|----------------|
| `AuthService` | Framework | Authentication | P1 |
| `EmailService` | Framework | Notifications | P2 |
| `IdempotencyService` | Resilience | Request deduplication | P2 |
| `AuditService` | Framework | Audit logging | P2 |
| `WorkflowService` | Framework | Workflow management | P3 |

**Testing Effort:** 20 hours

### Tier 4 - ANALYTICAL (Test For Performance)

**Specialized Services**

| Service | Purpose | Test Focus |
|---------|---------|------------|
| `ParetoOptimizationService` | Schedule optimization | Algorithm correctness |
| `ShapleyValuesService` | Attribution analysis | Mathematical accuracy |
| `GameTheoryService` | Strategic analysis | Game rules compliance |
| `HeatmapService` | Visualization | Data aggregation |
| `ResilienceService` | N-1/N-2 analysis | Contingency scenarios |
| `HomeostasisService` | Feedback loops | State equilibrium |

**Testing Effort:** 25 hours

---

## SECTION 2: TEST FIXTURE PATTERNS

### Pattern 1: Mock Database Fixtures

```python
# conftest.py
import pytest
from unittest.mock import MagicMock, Mock
from sqlalchemy.orm import Session

@pytest.fixture
def mock_db():
    """Mock SQLAlchemy session for unit tests."""
    db = MagicMock(spec=Session)

    # Mock query operations
    db.query.return_value.filter.return_value.first.return_value = None
    db.add = Mock()
    db.commit = Mock()
    db.flush = Mock()
    db.rollback = Mock()

    return db

@pytest.fixture
def mock_assignment_repo(mock_db):
    """Fixture: AssignmentRepository with pre-loaded test data."""
    from app.repositories.assignment import AssignmentRepository

    repo = AssignmentRepository(mock_db)

    # Mock common methods
    repo.get_by_id = Mock(return_value=SAMPLE_ASSIGNMENT)
    repo.list_with_filters = Mock(return_value=([SAMPLE_ASSIGNMENT], 1))
    repo.create = Mock(return_value=SAMPLE_ASSIGNMENT)
    repo.update = Mock(return_value=SAMPLE_ASSIGNMENT)
    repo.delete = Mock()

    return repo
```

### Pattern 2: Data Factories

```python
# tests/factories.py
from factory import Factory, Faker
from app.models import Assignment, Person, Block

class PersonFactory(Factory):
    """Generate test Person objects."""
    class Meta:
        model = Person

    id = Faker('uuid4')
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    email = Faker('email')
    type = 'resident'
    pgy_level = 1

class BlockFactory(Factory):
    """Generate test Block objects."""
    class Meta:
        model = Block

    id = Faker('uuid4')
    date = Faker('date_object')
    period = 'AM'

class AssignmentFactory(Factory):
    """Generate test Assignment objects."""
    class Meta:
        model = Assignment

    id = Faker('uuid4')
    person = SubFactory(PersonFactory)
    block = SubFactory(BlockFactory)
    rotation_template_id = Faker('uuid4')
```

### Pattern 3: Service Integration Fixtures

```python
# tests/services/conftest.py
import pytest
from app.services.assignment_service import AssignmentService

@pytest.fixture
def assignment_service(mock_db, mock_assignment_repo):
    """Fixture: AssignmentService with mocked repositories."""
    service = AssignmentService(mock_db)
    service.assignment_repo = mock_assignment_repo
    return service

@pytest.fixture
def assignment_service_with_acgme(assignment_service, mock_db):
    """Fixture: AssignmentService with ACGME validator."""
    from app.scheduling.acgme_validator import ACGMEValidator

    assignment_service.acgme_validator = Mock(spec=ACGMEValidator)
    assignment_service.acgme_validator.validate = Mock(
        return_value={"is_compliant": True, "warnings": []}
    )

    return assignment_service
```

---

## SECTION 3: PRIORITIZED TESTING TASKS (TOP 10 SERVICES)

### Task 1: AssignmentService Unit Tests

**File:** `backend/tests/services/test_assignment_service.py`

**Test Cases Required:**
```
✅ test_create_assignment_success
✅ test_create_assignment_duplicate_conflict
✅ test_create_assignment_acgme_violation
✅ test_create_assignment_with_freeze_horizon
✅ test_list_assignments_pagination
✅ test_list_assignments_with_filters
✅ test_update_assignment_success
✅ test_update_assignment_frozen
✅ test_delete_assignment_cascade
✅ test_list_assignments_n_plus_one_prevention
```

**Estimated Time:** 8 hours
**Coverage Target:** 85%

---

### Task 2: SwapExecutor Unit & Integration Tests

**File:** `backend/tests/services/test_swap_executor.py`

**Test Cases Required:**
```
✅ test_execute_one_to_one_swap_success
✅ test_execute_one_to_one_swap_acgme_violation
✅ test_execute_one_to_one_swap_cascade_updates
✅ test_execute_swap_with_call_cascade
✅ test_execute_swap_transaction_rollback_on_error
✅ test_execute_swap_idempotency
✅ test_execute_swap_24hr_rollback_window
✅ test_execute_swap_with_absence_conflicts
```

**Estimated Time:** 10 hours
**Coverage Target:** 90%

---

### Task 3: ACGMEValidator Unit Tests

**File:** `backend/tests/services/test_acgme_validator.py`

**Test Cases Required:**
```
✅ test_validate_80_hour_rule_compliant
✅ test_validate_80_hour_rule_violation
✅ test_validate_1_in_7_rule_compliant
✅ test_validate_1_in_7_rule_violation
✅ test_validate_supervision_ratio_compliant
✅ test_validate_supervision_ratio_violation
✅ test_validate_multiple_violations_returns_all
✅ test_validate_with_4_week_rolling_average
✅ test_validate_pgy1_vs_pgy2_different_ratios
```

**Estimated Time:** 6 hours
**Coverage Target:** 95%

---

### Task 4: PersonService Unit Tests

**File:** `backend/tests/services/test_person_service.py`

**Test Cases Required:**
```
✅ test_get_person_by_id
✅ test_get_person_with_relationships
✅ test_list_residents_pagination
✅ test_list_faculty_by_department
✅ test_create_person_success
✅ test_create_person_duplicate_email
✅ test_update_person_success
✅ test_update_person_role_change
✅ test_delete_person_cascade_check
```

**Estimated Time:** 6 hours
**Coverage Target:** 80%

---

### Task 5: ConflictAutoResolver Unit Tests

**File:** `backend/tests/services/test_conflict_auto_resolver.py`

**Test Cases Required:**
```
✅ test_analyze_conflict_double_booking
✅ test_analyze_conflict_hour_violation
✅ test_analyze_conflict_multiple_issues
✅ test_analyze_conflicts_batch_operation
✅ test_resolve_conflict_with_swap
✅ test_resolve_conflict_with_reassignment
✅ test_detect_cascading_conflicts
✅ test_batch_analysis_n_queries_optimized
```

**Estimated Time:** 8 hours
**Coverage Target:** 85%

---

### Task 6: SwapValidationService Unit Tests

**File:** `backend/tests/services/test_swap_validation.py`

**Test Cases Required:**
```
✅ test_validate_swap_basic_compatibility
✅ test_validate_swap_acgme_post_swap
✅ test_validate_swap_absence_conflicts
✅ test_validate_swap_frozen_periods
✅ test_validate_swap_by_request_type
✅ test_validate_swap_supervisor_approval_required
```

**Estimated Time:** 6 hours
**Coverage Target:** 85%

---

### Task 7: FreezeHorizonService Unit Tests

**File:** `backend/tests/services/test_freeze_horizon_service.py`

**Test Cases Required:**
```
✅ test_is_block_frozen_returns_correct_status
✅ test_freeze_horizon_advance_configuration
✅ test_get_frozen_blocks_range
✅ test_can_modify_block_checks_freeze
✅ test_partial_modification_within_threshold
```

**Estimated Time:** 5 hours
**Coverage Target:** 90%

---

### Task 8: AuthService Unit Tests

**File:** `backend/tests/services/test_auth_service.py`

**Test Cases Required:**
```
✅ test_authenticate_user_success
✅ test_authenticate_user_wrong_password
✅ test_authenticate_user_disabled_account
✅ test_generate_jwt_token
✅ test_verify_jwt_token_valid
✅ test_verify_jwt_token_expired
✅ test_verify_jwt_token_invalid
✅ test_hash_password_security
✅ test_verify_password_correctness
```

**Estimated Time:** 5 hours
**Coverage Target:** 95%

---

### Task 9: IdempotencyService Unit Tests

**File:** `backend/tests/services/test_idempotency_service.py`

**Test Cases Required:**
```
✅ test_process_with_idempotency_first_request
✅ test_process_with_idempotency_duplicate_request
✅ test_cache_expiration_allows_reprocessing
✅ test_error_handling_does_not_cache
✅ test_different_keys_processed_separately
```

**Estimated Time:** 4 hours
**Coverage Target:** 90%

---

### Task 10: BatchService Unit Tests

**File:** `backend/tests/services/test_batch_service.py`

**Test Cases Required:**
```
✅ test_create_batch_success
✅ test_process_batch_validation_errors
✅ test_process_batch_acgme_violations
✅ test_batch_partial_success_handling
✅ test_batch_operation_idempotency
```

**Estimated Time:** 6 hours
**Coverage Target:** 80%

---

## SECTION 4: MOCK STRATEGY DOCUMENTATION

### Strategy A: Repository Mocking

**Use When:** Testing service business logic in isolation

```python
@pytest.fixture
def mock_assignment_repo():
    """Mock repository to avoid database calls."""
    from unittest.mock import Mock
    repo = Mock()

    # Setup return values
    repo.get_by_id.return_value = SAMPLE_ASSIGNMENT
    repo.list_with_filters.return_value = ([SAMPLE_ASSIGNMENT], 1)
    repo.create.return_value = SAMPLE_ASSIGNMENT

    return repo

def test_create_assignment_calls_repo(assignment_service, mock_assignment_repo):
    """Verify service calls repository correctly."""
    assignment_service.assignment_repo = mock_assignment_repo

    result = assignment_service.create_assignment(block_id=..., person_id=...)

    # Verify repo method was called
    mock_assignment_repo.create.assert_called_once()
```

### Strategy B: Integration Testing

**Use When:** Testing repository + service interaction with real database

```python
@pytest.fixture
def test_db():
    """Real database session for integration tests."""
    # Create test database
    test_db_url = "sqlite:///:memory:"
    engine = create_engine(test_db_url)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(engine)

def test_create_assignment_integration(test_db):
    """Integration test with real database."""
    repo = AssignmentRepository(test_db)
    service = AssignmentService(test_db)

    # Create real objects
    result = service.create_assignment(...)

    # Verify in database
    db_obj = repo.get_by_id(result.id)
    assert db_obj is not None
```

### Strategy C: External Service Mocking

**Use When:** Services call external APIs (email, SMS, webhooks)

```python
@pytest.fixture
def mock_email_service(monkeypatch):
    """Mock EmailService to prevent actual email sending."""
    mock_send = Mock(return_value=True)
    monkeypatch.setattr("app.services.email.EmailService.send_email", mock_send)
    return mock_send

def test_notify_assignment_sends_email(mock_email_service):
    """Verify email notification is triggered."""
    service = AssignmentService(db)
    service.create_assignment(...)

    # Verify email was queued
    mock_email_service.assert_called()
```

---

## SECTION 5: ERROR HANDLING TEST PATTERNS

### Pattern: Exception Testing

```python
def test_create_assignment_acgme_violation():
    """Test service raises correct exception on ACGME violation."""
    from app.exceptions.compliance import ACGMEComplianceError

    with pytest.raises(ACGMEComplianceError):
        service.create_assignment(
            block_id=BLOCK_EXCEEDING_80_HOURS,
            person_id=RESIDENT_ID,
        )

def test_create_assignment_returns_error_dict():
    """Test service returns error in dict format."""
    result = service.create_assignment(
        block_id=block_id,
        person_id=duplicate_person_id,
    )

    assert result["error"] is not None
    assert result["assignment"] is None
    assert "already assigned" in result["error"]
```

---

## SECTION 6: FIXTURE PATTERNS GUIDE

### Global Fixtures (conftest.py)

```python
# Place in: backend/tests/conftest.py

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4

@pytest.fixture
def sample_person():
    """Standard test person (resident)."""
    return {
        "id": uuid4(),
        "first_name": "Test",
        "last_name": "Resident",
        "email": "resident@test.com",
        "type": "resident",
        "pgy_level": 1,
    }

@pytest.fixture
def sample_block():
    """Standard test block."""
    return {
        "id": uuid4(),
        "date": date.today(),
        "period": "AM",
    }

@pytest.fixture
def sample_assignment(sample_person, sample_block):
    """Standard test assignment."""
    return {
        "id": uuid4(),
        "person_id": sample_person["id"],
        "block_id": sample_block["id"],
        "rotation_template_id": uuid4(),
        "created_at": datetime.now(),
    }
```

---

## SECTION 7: TESTING TIMELINE & EXECUTION

### Phase 1: Foundation (Week 1)
- [ ] Create test infrastructure (fixtures, factories, conftest)
- [ ] Write Tier 1 tests (AssignmentService, ACGMEValidator, PersonService)
- [ ] Achieve 80%+ coverage on critical services

**Effort:** 40 hours
**Owner:** Senior Test Engineer

### Phase 2: Feature Services (Week 2)
- [ ] Write SwapExecutor tests
- [ ] Write ConflictAutoResolver tests
- [ ] Write SwapValidationService tests

**Effort:** 30 hours
**Owner:** Mid-level Test Engineer

### Phase 3: Framework Services (Week 3)
- [ ] Write AuthService tests
- [ ] Write IdempotencyService tests
- [ ] Write BatchService tests

**Effort:** 20 hours
**Owner:** Mid-level Test Engineer

### Phase 4: Analytical Services (Week 4)
- [ ] Write tests for ParetoOptimization, Shapley, GameTheory
- [ ] Performance verification for algorithms

**Effort:** 25 hours
**Owner:** Data Scientist / Engineer

---

## SECTION 8: TESTING QUALITY GATES

### Coverage Requirements
- **Critical Services:** 85%+ line coverage, 90%+ branch coverage
- **Feature Services:** 80%+ coverage
- **Utility Services:** 75%+ coverage

### Test Execution Requirements
```bash
# Run all tests
pytest backend/tests/services/ -v --cov=app.services --cov-report=html

# Run only critical services
pytest backend/tests/services/test_assignment_service.py \
        backend/tests/services/test_acgme_validator.py \
        backend/tests/services/test_swap_executor.py \
        -v --cov=app.services

# Generate coverage report
pytest --cov=app.services --cov-report=term-missing
```

### Performance Gate
- Unit tests should execute in < 2 seconds
- Integration tests should execute in < 10 seconds per test
- Batch test suite should complete in < 60 seconds

---

## SECTION 9: CI/CD INTEGRATION

### GitHub Actions Workflow
```yaml
name: Service Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r backend/requirements.txt pytest pytest-cov

      - name: Run service tests
        run: |
          cd backend
          pytest tests/services/ -v --cov=app.services

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## SECTION 10: SUMMARY & NEXT STEPS

**Total Estimated Testing Effort:** 125 hours
**Recommended Timeline:** 4 weeks (2-3 engineers)

**Immediate Action Items:**
1. [ ] Set up test infrastructure (conftest.py, factories)
2. [ ] Write Tier 1 service tests
3. [ ] Configure CI/CD testing gates
4. [ ] Establish coverage baselines
5. [ ] Document service mocking patterns

**Long-term Goals:**
- Achieve 85%+ coverage across all services
- Implement mutation testing for critical paths
- Add performance regression tests
- Document service contract tests

---

*Generated by SESSION 8 BURN - Backend Improvements*
*Reference: SESSION_1_BACKEND/backend-service-patterns.md*
