# Integration Testing Guide

## Overview

This guide covers integration testing for the Residency Scheduler application. Integration tests verify that different components work together correctly, testing the interactions between API routes, services, database, and external systems.

## Test Structure

### Organization

Integration tests are organized into several categories:

```
backend/tests/integration/
├── api/                    # API endpoint integration tests
│   ├── test_schedule_workflow.py
│   ├── test_swap_workflow.py
│   ├── test_compliance_workflow.py
│   ├── test_auth_workflow.py
│   ├── test_user_management.py
│   ├── test_assignment_workflow.py
│   ├── test_reporting_workflow.py
│   ├── test_notification_workflow.py
│   ├── test_bulk_operations.py
│   └── test_export_import.py
├── services/              # Service layer integration tests
│   ├── test_scheduler_integration.py
│   ├── test_compliance_integration.py
│   ├── test_swap_integration.py
│   ├── test_notification_integration.py
│   ├── test_celery_integration.py
│   ├── test_cache_integration.py
│   └── test_resilience_integration.py
├── scenarios/             # Complex scenario tests
│   ├── test_emergency_coverage.py
│   ├── test_cascade_failures.py
│   ├── test_concurrent_modifications.py
│   ├── test_acgme_enforcement.py
│   ├── test_academic_year.py
│   ├── test_multi_user.py
│   ├── test_high_load.py
│   ├── test_recovery.py
│   └── test_data_integrity.py
└── utils/                 # Test utilities
    ├── api_client.py
    ├── assertions.py
    ├── setup_helpers.py
    └── cleanup_helpers.py
```

## Running Integration Tests

### Run All Integration Tests

```bash
cd backend
pytest tests/integration/
```

### Run Specific Test Category

```bash
# API integration tests
pytest tests/integration/api/

# Service integration tests
pytest tests/integration/services/

# Scenario tests
pytest tests/integration/scenarios/
```

### Run Specific Test File

```bash
pytest tests/integration/api/test_schedule_workflow.py
```

### Run Specific Test

```bash
pytest tests/integration/api/test_schedule_workflow.py::TestScheduleWorkflow::test_create_schedule_workflow
```

### Run with Coverage

```bash
pytest tests/integration/ --cov=app --cov-report=html
```

## Writing Integration Tests

### Basic Test Structure

```python
"""
Integration tests for [feature] workflow.

Tests the end-to-end [feature] lifecycle.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.person import Person


class Test[Feature]Workflow:
    """Test [feature] workflow."""

    def test_[operation]_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
    ):
        """Test [operation] workflow."""
        # Step 1: Setup
        # Create necessary test data

        # Step 2: Execute
        # Perform the operation

        # Step 3: Verify
        # Assert expected outcomes

        # Step 4: Cleanup (if needed)
        # Clean up test data
```

### Using Test Utilities

#### API Client

```python
from tests.integration.utils import TestAPIClient

def test_with_api_client(client, auth_headers, db):
    api = TestAPIClient(client, auth_headers)

    # Create person
    response = api.create_person({
        "name": "Dr. Test",
        "type": "resident",
        "email": "test@hospital.org",
        "pgy_level": 1,
    })

    assert response.status_code == 201
```

#### Custom Assertions

```python
from tests.integration.utils import (
    assert_assignment_valid,
    assert_acgme_compliant,
    assert_no_conflicts,
)

def test_with_assertions(client, auth_headers):
    response = client.get("/api/assignments/123", headers=auth_headers)
    assignment = response.json()

    # Validate assignment structure
    assert_assignment_valid(assignment)

    # Check ACGME compliance
    compliance = client.get("/api/analytics/acgme/compliance").json()
    assert_acgme_compliant(compliance)
```

#### Setup Helpers

```python
from tests.integration.utils import (
    create_test_residents,
    create_test_schedule,
    setup_minimal_schedule_scenario,
)

def test_with_setup_helpers(db):
    # Create test residents
    residents = create_test_residents(db, count=5)

    # Create full schedule
    scenario = setup_minimal_schedule_scenario(db)

    # Use created data
    assert len(scenario["residents"]) == 3
    assert len(scenario["assignments"]) > 0
```

#### Cleanup Helpers

```python
from tests.integration.utils import TestDataCleanup

def test_with_cleanup(db):
    with TestDataCleanup(db) as cleanup:
        # Create test data
        person = create_test_person(db)
        cleanup.add_person(str(person.id))

        # Run tests
        # ...

        # Cleanup happens automatically on exit
```

## Test Categories

### API Integration Tests

Test complete API workflows from request to response.

**Focus:**
- HTTP request/response handling
- Request validation
- Response formatting
- Status codes
- Error handling

**Example:**
```python
def test_create_assignment_workflow(
    self,
    client: TestClient,
    auth_headers: dict,
):
    # Create assignment via API
    response = client.post(
        "/api/assignments/",
        json={
            "block_id": str(block_id),
            "person_id": str(person_id),
            "rotation_template_id": str(template_id),
            "role": "primary",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert "id" in response.json()
```

### Service Integration Tests

Test service layer operations with database.

**Focus:**
- Business logic execution
- Database transactions
- Data persistence
- Service interactions

**Example:**
```python
def test_scheduler_service_integration(db: Session):
    scheduler = SchedulerService(db)

    result = scheduler.generate_schedule(
        start_date=date.today(),
        end_date=date.today() + timedelta(days=7),
        person_ids=[...],
    )

    assert result.success
    assert len(result.assignments) > 0
```

### Scenario Tests

Test complex real-world scenarios.

**Focus:**
- Multi-step workflows
- Edge cases
- Error recovery
- System behavior under stress

**Example:**
```python
def test_emergency_coverage_scenario(
    client: TestClient,
    auth_headers: dict,
    db: Session,
):
    # Create assignments
    # ...

    # Simulate emergency absence
    absence = create_absence(db, person_id, date.today())

    # System should automatically find coverage
    coverage_response = client.post(
        "/api/emergency/find-coverage",
        json={...},
        headers=auth_headers,
    )

    assert coverage_response.status_code == 200
```

## Best Practices

### 1. Test Isolation

Each test should be independent and not rely on other tests.

```python
# Good
def test_create_assignment(db):
    person = create_test_person(db)
    block = create_test_block(db)
    # Use test-specific data

# Bad
def test_create_assignment(db):
    # Assumes person with ID 123 exists
    person_id = "123"
```

### 2. Use Fixtures

Leverage pytest fixtures for common setup.

```python
@pytest.fixture
def schedule_scenario(db):
    return setup_minimal_schedule_scenario(db)

def test_with_scenario(schedule_scenario):
    residents = schedule_scenario["residents"]
    # Use scenario data
```

### 3. Clear Test Names

Use descriptive test names that explain what is being tested.

```python
# Good
def test_swap_request_rejected_when_violates_80_hour_rule(...)

# Bad
def test_swap_1(...)
```

### 4. Arrange-Act-Assert

Structure tests clearly:

```python
def test_example():
    # Arrange - Setup test data
    person = create_test_person()

    # Act - Execute operation
    result = perform_operation(person)

    # Assert - Verify outcome
    assert result.success
```

### 5. Test Both Success and Failure

```python
def test_create_assignment_success(...):
    # Test successful creation
    ...

def test_create_assignment_fails_on_conflict(...):
    # Test failure when conflict exists
    ...
```

### 6. Clean Up After Tests

```python
def test_with_cleanup(db):
    with TestDataCleanup(db) as cleanup:
        person = create_person(db)
        cleanup.add_person(person.id)
        # Test code
        # Cleanup automatic
```

## Common Patterns

### Testing Authentication

```python
def test_requires_authentication(client):
    response = client.get("/api/protected/")
    assert response.status_code == 401

def test_with_authentication(client, auth_headers):
    response = client.get("/api/protected/", headers=auth_headers)
    assert response.status_code == 200
```

### Testing Pagination

```python
def test_pagination(client, auth_headers):
    response = client.get(
        "/api/people/?limit=10&offset=0",
        headers=auth_headers,
    )

    data = response.json()
    assert_pagination_valid(data)
    assert len(data["items"]) <= 10
```

### Testing Validation

```python
def test_validation_error(client, auth_headers):
    response = client.post(
        "/api/people/",
        json={"name": ""},  # Invalid: empty name
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert "validation" in response.json()["detail"].lower()
```

### Testing Async Operations

```python
def test_async_operation(client, auth_headers):
    # Start async operation
    response = client.post(
        "/api/scheduler/generate",
        json={...},
        headers=auth_headers,
    )

    # Should return job ID
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    # Poll for completion
    # (or use background task testing)
```

## Troubleshooting

### Tests Failing Due to Data Conflicts

**Problem:** Tests fail because of existing data in database.

**Solution:** Use test database isolation:
```python
@pytest.fixture(scope="function")
def db():
    # Create fresh database for each test
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
```

### Tests Running Slowly

**Problem:** Integration tests take too long.

**Solution:**
- Use `pytest-xdist` for parallel execution
- Mark slow tests with `@pytest.mark.slow`
- Run quick tests in CI, slow tests nightly

```bash
# Run fast tests only
pytest -m "not slow"

# Run with parallelization
pytest -n auto
```

### Flaky Tests

**Problem:** Tests fail intermittently.

**Solution:**
- Avoid time-dependent assertions
- Use explicit waits instead of sleeps
- Ensure proper test isolation
- Check for race conditions

## Coverage Goals

- **API Routes:** 90%+ coverage
- **Services:** 85%+ coverage
- **Critical Paths:** 100% coverage (scheduling, ACGME compliance, swaps)

Check coverage:
```bash
pytest tests/integration/ --cov=app --cov-report=term-missing
```

## CI/CD Integration

Integration tests run automatically in CI:

```yaml
# .github/workflows/test.yml
- name: Run Integration Tests
  run: |
    cd backend
    pytest tests/integration/ --cov=app --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

## Next Steps

- [E2E Testing Guide](./e2e-testing-guide.md)
- [Test Scenarios Catalog](./test-scenarios.md)
- [Performance Testing](../development/PERFORMANCE_TESTING.md)
