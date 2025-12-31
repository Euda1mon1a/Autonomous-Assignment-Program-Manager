# QA_TESTER Agent - Enhanced Specification

> **Document Version:** 2.0 (Enhanced)
> **Date:** 2025-12-30
> **Author:** G2_RECON (SEARCH_PARTY Operation)
> **Status:** Comprehensive Reconnaissance Complete
> **Base Document:** `.claude/Agents/QA_TESTER.md` (v1.1)

---

## Executive Summary

This enhanced specification provides comprehensive QA_TESTER agent guidance including:
- Advanced testing patterns (pytest, Jest, integration, performance)
- Complete testing infrastructure mapping
- Coverage strategies and quality gates
- Edge case discovery methodologies
- Fixture and factory patterns
- Test execution workflows
- Performance testing frameworks
- Integration testing approaches

---

## Table of Contents

1. [Testing Infrastructure Overview](#testing-infrastructure-overview)
2. [Backend Testing (pytest)](#backend-testing-pytest)
3. [Frontend Testing (Jest)](#frontend-testing-jest)
4. [Integration Testing](#integration-testing)
5. [Performance Testing](#performance-testing)
6. [Edge Case Discovery Framework](#edge-case-discovery-framework)
7. [Test Patterns & Best Practices](#test-patterns--best-practices)
8. [Coverage Targets & Metrics](#coverage-targets--metrics)
9. [Fixture & Factory Strategies](#fixture--factory-strategies)
10. [Quality Gates & Escalation](#quality-gates--escalation)
11. [Advanced Workflows](#advanced-workflows)

---

## Testing Infrastructure Overview

### Architecture

```
Residency Scheduler Testing Pyramid
=====================================

                     /\
                    /  \              E2E Tests (Playwright)
                   /    \             - Full user workflows
                  /      \            - Cross-browser validation
                 /________\

                   /\                 Integration Tests
                  /  \                - API + Database
                 /    \               - Multi-service flows
                /______\              - Swap workflows

              /\                      Unit Tests
             /  \                     - Services (pytest)
            /    \                    - Components (Jest)
           /______\                   - Isolated logic

Repository
==========

backend/
├── tests/
│   ├── conftest.py               # Global fixtures & configuration
│   ├── factories.py              # FactoryBoy test data generators
│   ├── pytest.ini                # pytest configuration
│   ├── unit/                     # Unit tests by domain
│   │   └── services/
│   │       └── test_constraint_service.py
│   ├── integration/              # Multi-component workflows
│   │   ├── conftest.py          # Integration-specific fixtures
│   │   ├── test_scheduling_flow.py
│   │   ├── test_swap_workflow.py
│   │   └── test_resilience_integration.py
│   ├── performance/              # Load & stress testing
│   │   ├── conftest.py          # Performance fixtures
│   │   ├── test_acgme_load.py
│   │   └── test_idempotency_load.py
│   ├── services/                 # Service-layer tests
│   │   ├── test_swap_executor.py
│   │   ├── test_swap_executor_edge_cases.py
│   │   └── test_credential_service.py
│   ├── scheduling/               # Scheduling engine tests
│   │   └── test_spin_glass.py
│   ├── validators/               # ACGME validator tests
│   │   └── test_acgme_comprehensive.py
│   ├── resilience/               # Resilience framework tests
│   │   └── test_resilience_integration.py
│   └── [80+ other test files]    # Routes, auth, notifications, etc.

frontend/
├── jest.config.js                # Jest configuration
├── tsconfig.jest.json            # TypeScript Jest config
├── __tests__/
│   ├── setup.ts                  # Test environment setup
│   ├── features/
│   │   ├── analytics/            # Analytics component tests
│   │   ├── audit/                # Audit log tests
│   │   └── swap-marketplace/     # Swap feature tests
│   └── pages/
│       └── settings.test.tsx

load-tests/
├── scenarios/                     # k6 load test scenarios
│   ├── api-baseline.js
│   ├── concurrent-users.js
│   ├── schedule-generation.js
│   └── rate-limit-attack.js
└── jest.config.js                # k6 test configuration
```

### Test Statistics

- **Total Backend Test Files:** 80+
- **Total Backend Test Functions:** 1,000+
- **Largest Test File:** `test_conflict_alert_service.py` (2,257 lines)
- **Coverage Goals:** 80% overall, 95% critical paths
- **Frontend Test Files:** 6+
- **Frontend Test Functions:** 600+
- **Frontend Coverage Goal:** 70% overall

---

## Backend Testing (pytest)

### Configuration

**File:** `/backend/pytest.ini`

```ini
[pytest]
# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Markers available
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    acgme: marks tests related to ACGME compliance
    performance: marks tests as performance/load tests

# Asyncio mode for async tests
asyncio_mode = auto
```

### Global Fixtures (`conftest.py`)

The main test configuration provides 13+ pytest fixtures:

#### Database Fixtures

```python
@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create fresh database for each test."""
    # Creates all tables, yields session, drops all tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create test client with database override."""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

#### Authentication Fixtures

```python
@pytest.fixture
def admin_user(db: Session) -> User:
    """Create admin user for authenticated tests."""
    user = User(
        id=uuid4(),
        username="testadmin",
        email="testadmin@test.org",
        hashed_password=get_password_hash("testpass123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def auth_headers(client: TestClient, admin_user: User) -> dict:
    """Get authentication headers for API requests."""
    response = client.post(
        "/api/auth/login/json",
        json={"username": "testadmin", "password": "testpass123"}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
```

#### Data Fixtures

```python
@pytest.fixture
def sample_resident(db: Session) -> Person:
    """Create sample resident for tests."""
    resident = Person(
        id=uuid4(),
        name="PGY1-01",
        type="resident",
        email="pgy1@hospital.org",
        pgy_level=1,
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)
    return resident

@pytest.fixture
def sample_faculty(db: Session) -> Person:
    """Create sample faculty for tests."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Faculty",
        type="faculty",
        email="faculty@hospital.org",
        performs_procedures=True,
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty

@pytest.fixture
def sample_block(db: Session) -> Block:
    """Create sample block for tests."""
    block = Block(
        id=uuid4(),
        date=date.today(),
        time_of_day="AM",
        block_number=1,
        is_weekend=False,
        is_holiday=False,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block
```

### Running pytest

#### Common Commands

```bash
# Run all tests
cd backend
pytest

# Run with verbose output
pytest -v

# Run specific file
pytest tests/test_swap_executor.py

# Run specific test class
pytest tests/test_swap_executor.py::TestSwapExecutor

# Run specific test function
pytest tests/test_swap_executor.py::TestSwapExecutor::test_execute_one_to_one_swap

# Run by marker
pytest -m acgme                    # Only ACGME compliance tests
pytest -m unit                     # Only unit tests
pytest -m integration              # Only integration tests
pytest -m "not slow"               # Exclude slow tests

# Run with coverage
pytest --cov=app --cov-report=html

# Run with detailed output
pytest -v -s                       # Verbose + show print statements

# Run with timing
pytest --durations=10              # Show 10 slowest tests

# Run in parallel (install pytest-xdist)
pytest -n auto                     # Use all CPU cores
```

#### Coverage Reports

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View coverage by module
pytest --cov=app --cov-report=term-missing

# Check specific module coverage
pytest --cov=app.services --cov-report=html tests/services/
```

### Test Pattern Examples

#### Pattern 1: Unit Test with Fixtures

```python
"""Tests for swap validator service."""
import pytest
from datetime import date, timedelta
from uuid import uuid4

from app.services.swap_validator import SwapValidator
from app.models.person import Person


class TestSwapValidator:
    """Test swap validation logic."""

    @pytest.fixture
    def validator(self, db):
        """Create validator instance."""
        return SwapValidator(db)

    def test_validate_one_to_one_swap_success(
        self, validator, sample_resident, sample_faculty, db
    ):
        """Test successful one-to-one swap validation."""
        # Setup: Create assignments
        assignment_a = create_assignment(
            db, person=sample_resident, date=date.today()
        )
        assignment_b = create_assignment(
            db, person=sample_faculty, date=date.today()
        )

        # Execute: Validate swap
        result = validator.validate_swap(
            initiator_id=sample_resident.id,
            partner_id=sample_faculty.id,
            initiator_date=date.today(),
            partner_date=date.today(),
        )

        # Assert: Swap is valid
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_swap_fails_with_acgme_violation(
        self, validator, sample_resident, db
    ):
        """Test swap validation fails when ACGME rules would be violated."""
        # Setup: Create assignments that would exceed 80-hour rule
        for _ in range(20):  # Create many assignments
            create_assignment(
                db, person=sample_resident, date=date.today()
            )

        # Execute: Try to validate additional swap
        result = validator.validate_swap(
            initiator_id=sample_resident.id,
            partner_id=uuid4(),
            initiator_date=date.today(),
            partner_date=date.today(),
        )

        # Assert: Swap is invalid due to ACGME violation
        assert not result.is_valid
        assert any("80-hour" in error for error in result.errors)

    @pytest.mark.parametrize("pgy_level", [1, 2, 3])
    def test_validate_swap_for_all_pgy_levels(
        self, validator, db, pgy_level
    ):
        """Test swap validation works for all PGY levels."""
        resident = create_resident(db, pgy_level=pgy_level)
        faculty = create_faculty(db)

        result = validator.validate_swap(
            initiator_id=resident.id,
            partner_id=faculty.id,
            initiator_date=date.today(),
            partner_date=date.today(),
        )

        assert result.is_valid
```

#### Pattern 2: Integration Test with API Client

```python
"""Integration tests for swap workflow."""
import pytest
from fastapi.testclient import TestClient


class TestSwapWorkflow:
    """Test end-to-end swap workflow."""

    def test_swap_request_creation_and_execution(
        self, client: TestClient, auth_headers: dict, db
    ):
        """Test complete swap workflow: request -> validate -> execute."""
        # Step 1: Create test data
        resident_a = create_resident(db, name="PGY1-01")
        resident_b = create_resident(db, name="PGY1-02")
        assignment_a = create_assignment(db, person=resident_a)
        assignment_b = create_assignment(db, person=resident_b)

        # Step 2: Create swap request via API
        swap_request = {
            "initiator_id": str(resident_a.id),
            "partner_id": str(resident_b.id),
            "initiator_date": assignment_a.block.date.isoformat(),
            "partner_date": assignment_b.block.date.isoformat(),
        }
        response = client.post(
            "/api/swaps",
            json=swap_request,
            headers=auth_headers
        )

        # Step 3: Verify swap request created
        assert response.status_code == 201
        swap_id = response.json()["id"]

        # Step 4: Approve swap
        response = client.post(
            f"/api/swaps/{swap_id}/approve",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Step 5: Verify swap executed
        response = client.get(f"/api/swaps/{swap_id}", headers=auth_headers)
        assert response.json()["status"] == "completed"

        # Step 6: Verify assignments swapped
        response = client.get(
            f"/api/assignments/{assignment_a.id}",
            headers=auth_headers
        )
        assert response.json()["person_id"] == str(resident_b.id)
```

#### Pattern 3: Parametrized Test

```python
"""Test ACGME validation with multiple scenarios."""
import pytest
from datetime import date, timedelta

# Test data: (hours, expected_valid, description)
ACGME_80_HOUR_TEST_CASES = [
    (79.5, True, "Below limit"),
    (80.0, True, "Exactly at limit"),
    (80.01, False, "Just over limit"),
    (100.0, False, "Well over limit"),
    (0.0, True, "Zero hours"),
    (-5.0, False, "Negative hours (invalid)"),
]


class TestACGME80HourRule:
    """Test 80-hour rule validation."""

    @pytest.mark.parametrize(
        "hours,expected_valid,description",
        ACGME_80_HOUR_TEST_CASES
    )
    def test_80_hour_rule_validation(
        self, validator, db, hours, expected_valid, description
    ):
        """Test 80-hour rule with various hour counts."""
        resident = create_resident(db)

        # Create assignments totaling 'hours' hours
        for i in range(int(hours)):
            create_assignment(
                db, person=resident, duration_hours=1.0
            )

        result = validator.validate_80_hour_rule(resident.id)
        assert result.is_valid == expected_valid, description
```

#### Pattern 4: Async Test

```python
"""Test async database operations."""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession


class TestAsyncOperations:
    """Test async database operations."""

    @pytest.mark.asyncio
    async def test_async_resident_creation(self, async_db: AsyncSession):
        """Test creating resident with async."""
        resident = Person(
            name="Async Resident",
            type="resident",
            pgy_level=1,
        )
        async_db.add(resident)
        await async_db.commit()

        result = await async_db.execute(
            select(Person).where(Person.name == "Async Resident")
        )
        created = result.scalar_one_or_none()

        assert created is not None
        assert created.name == "Async Resident"
```

---

## Frontend Testing (Jest)

### Configuration

**File:** `/frontend/jest.config.js`

```javascript
const config = {
  testEnvironment: 'jsdom',
  testTimeout: 15000,
  setupFilesAfterEnv: ['<rootDir>/__tests__/setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@/types/(.*)$': '<rootDir>/types/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.test.{ts,tsx}',
    '!src/**/__mocks__/**',
  ],
  coverageThreshold: {
    global: {
      branches: 60,
      functions: 60,
      lines: 60,
      statements: 60,
    },
  },
}
```

### Running Jest

```bash
# Run all tests
cd frontend
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- SwapRequestCard.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="swap"

# Run with different environment
npm test -- --env=jsdom

# Generate coverage report
npm run test:coverage
```

### Test Pattern Examples

#### Pattern 1: Component Unit Test

```typescript
/**
 * Test for SwapRequestCard component.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { SwapRequestCard } from '@/features/swap-marketplace/SwapRequestCard'
import { SwapRequest } from '@/types/swap'

describe('SwapRequestCard', () => {
  const mockSwapRequest: SwapRequest = {
    id: '123',
    initiator: { id: 'res1', name: 'PGY1-01' },
    partner: { id: 'res2', name: 'PGY1-02' },
    status: 'pending',
    createdAt: new Date().toISOString(),
  }

  it('renders swap request details', () => {
    render(<SwapRequestCard request={mockSwapRequest} />)

    expect(screen.getByText('PGY1-01')).toBeInTheDocument()
    expect(screen.getByText('PGY1-02')).toBeInTheDocument()
  })

  it('shows approve button when pending', () => {
    render(<SwapRequestCard request={mockSwapRequest} />)

    const approveBtn = screen.getByRole('button', { name: /approve/i })
    expect(approveBtn).toBeInTheDocument()
  })

  it('calls onApprove callback when approve clicked', async () => {
    const onApprove = jest.fn()
    render(
      <SwapRequestCard
        request={mockSwapRequest}
        onApprove={onApprove}
      />
    )

    const approveBtn = screen.getByRole('button', { name: /approve/i })
    fireEvent.click(approveBtn)

    await waitFor(() => {
      expect(onApprove).toHaveBeenCalledWith('123')
    })
  })
})
```

#### Pattern 2: Hook Test

```typescript
/**
 * Test for useSwapRequests hook.
 */
import { renderHook, waitFor } from '@testing-library/react'
import { useSwapRequests } from '@/hooks/useSwapRequests'
import * as api from '@/services/api'

jest.mock('@/services/api')

describe('useSwapRequests', () => {
  it('fetches swap requests on mount', async () => {
    const mockRequests = [
      { id: '1', status: 'pending' },
      { id: '2', status: 'approved' },
    ]

    ;(api.getSwapRequests as jest.Mock).mockResolvedValue(mockRequests)

    const { result } = renderHook(() => useSwapRequests())

    await waitFor(() => {
      expect(result.current.requests).toEqual(mockRequests)
    })
  })

  it('handles error when fetch fails', async () => {
    ;(api.getSwapRequests as jest.Mock).mockRejectedValue(
      new Error('API Error')
    )

    const { result } = renderHook(() => useSwapRequests())

    await waitFor(() => {
      expect(result.current.error).toBeTruthy()
    })
  })
})
```

---

## Integration Testing

### Structure

Integration tests verify components working together across service boundaries.

**Location:** `/backend/tests/integration/`

```
integration/
├── conftest.py                    # Integration-specific fixtures
├── test_scheduling_flow.py        # Schedule generation workflow
├── test_swap_workflow.py          # Swap request workflow
├── test_leave_workflow.py         # Leave request workflow
├── test_fmit_swap_workflow.py     # FMIT rotation swaps
└── test_resilience_integration.py # Resilience features
```

### Integration Test Example

```python
"""Integration test for complete swap workflow."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date


class TestSwapWorkflowIntegration:
    """Test end-to-end swap workflow."""

    def test_swap_workflow_complete(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
    ):
        """
        Test complete swap workflow:
        1. Create two residents with assignments
        2. Create swap request
        3. Validate swap doesn't violate ACGME
        4. Approve swap
        5. Execute swap
        6. Verify assignments swapped
        7. Verify ACGME still compliant
        """
        # Setup: Create residents
        resident_a = create_resident(db, name="PGY1-01", pgy_level=1)
        resident_b = create_resident(db, name="PGY1-02", pgy_level=1)

        # Create assignments
        block_a = create_block(db, date=date(2025, 8, 1))
        block_b = create_block(db, date=date(2025, 8, 2))

        assign_a = create_assignment(
            db, person=resident_a, block=block_a, rotation="Clinic"
        )
        assign_b = create_assignment(
            db, person=resident_b, block=block_b, rotation="Inpatient"
        )

        # Create swap request
        response = client.post(
            "/api/swaps",
            json={
                "initiator_id": str(resident_a.id),
                "partner_id": str(resident_b.id),
                "initiator_assignment_id": str(assign_a.id),
                "partner_assignment_id": str(assign_b.id),
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        swap = response.json()
        swap_id = swap["id"]
        assert swap["status"] == "pending"

        # Approve swap
        response = client.post(
            f"/api/swaps/{swap_id}/approve",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Execute swap
        response = client.post(
            f"/api/swaps/{swap_id}/execute",
            headers=auth_headers,
        )
        assert response.status_code == 200
        executed = response.json()
        assert executed["status"] == "completed"

        # Verify assignments swapped
        response = client.get(
            f"/api/assignments/{assign_a.id}",
            headers=auth_headers,
        )
        assert response.json()["person_id"] == str(resident_b.id)

        response = client.get(
            f"/api/assignments/{assign_b.id}",
            headers=auth_headers,
        )
        assert response.json()["person_id"] == str(resident_a.id)

        # Verify ACGME still compliant
        response = client.get(
            f"/api/compliance/residents/{resident_a.id}",
            headers=auth_headers,
        )
        assert response.json()["compliant"] is True
```

---

## Performance Testing

### Configuration & Fixtures

**Location:** `/backend/tests/performance/`

**File:** `conftest.py`

```python
import pytest
from contextlib import contextmanager
import time


@contextmanager
def measure_time(operation_name: str):
    """Context manager for timing operations."""
    metrics = {"operation": operation_name}
    start = time.time()
    yield metrics
    duration = time.time() - start
    metrics["duration"] = duration
    print(f"{operation_name}: {duration:.3f}s")


@pytest.fixture
def perf_timer():
    """Fixture providing performance timer."""
    return measure_time


# Performance thresholds
MAX_VALIDATION_TIME_100_RESIDENTS = 5.0   # seconds
MAX_VALIDATION_TIME_50_RESIDENTS = 2.0    # seconds
MAX_VALIDATION_TIME_25_RESIDENTS = 1.0    # seconds
```

### Performance Test Example

```python
"""Performance tests for ACGME validation."""
import pytest
from app.scheduling.acgme_validator import ACGMEValidator


class TestACGMEPerformance:
    """Test ACGME validation performance."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_80_hour_rule_large_dataset(
        self, db, large_resident_dataset, large_assignment_dataset, perf_timer
    ):
        """
        Test 80-hour rule validation performance with 100 residents.

        Requirements:
        - Should complete in < 5 seconds
        - Should handle ~5,600 assignments
        """
        validator = ACGMEValidator(db)

        with perf_timer("80-hour rule validation (100 residents)") as metrics:
            violations = validator.validate_80_hour_rule()

        duration = metrics["duration"]
        assert duration < MAX_VALIDATION_TIME_100_RESIDENTS, \
            f"Validation took {duration:.2f}s, expected < {MAX_VALIDATION_TIME_100_RESIDENTS}s"

        # Print metrics
        print(f"Total violations: {len(violations)}")
        print(f"Validation rate: {len(large_resident_dataset) / duration:.1f} residents/sec")

    @pytest.mark.performance
    def test_concurrent_validation(self, db, large_resident_dataset):
        """Test 10 concurrent ACGME validations."""
        import concurrent.futures
        from app.scheduling.acgme_validator import ACGMEValidator

        validator = ACGMEValidator(db)

        def run_validation():
            return validator.validate_80_hour_rule()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            start = time.time()
            futures = [executor.submit(run_validation) for _ in range(10)]
            results = [f.result() for f in futures]
            duration = time.time() - start

        # All results should be identical (consistent validation)
        assert all(r == results[0] for r in results)

        # Should complete in reasonable time
        assert duration < 10.0, f"Concurrent validation took {duration:.2f}s"
```

### Load Testing with k6

**Location:** `/load-tests/scenarios/`

```bash
# Run smoke test (quick validation)
npm run test:smoke

# Run standard load test (50 VUs, 5 minutes)
npm run test:load

# Run stress test (200 VUs, 10 minutes)
npm run test:stress

# Run custom scenario
k6 run --vus 100 --duration 5m scenarios/schedule-generation.js
```

---

## Edge Case Discovery Framework

### Comprehensive Edge Case Catalog

#### 1. Temporal Edge Cases

```python
"""Test temporal edge cases."""
from datetime import date, datetime, timedelta

class TestTemporalEdgeCases:
    """Test temporal boundaries and transitions."""

    @pytest.mark.parametrize("date_offset,description", [
        (0, "Same day as deadline"),
        (-1, "Day before deadline"),
        (1, "Day after deadline"),
        (-7, "Exactly one week before"),
        (7, "Exactly one week after"),
    ])
    def test_acgme_window_boundaries(
        self, db, date_offset, description
    ):
        """Test ACGME validation at rolling 4-week boundaries."""
        start_date = date(2025, 8, 1)
        target_date = start_date + timedelta(days=date_offset)

        # Create assignments up to target date
        for i in range(4 * 7):  # 4 weeks
            create_assignment(
                db,
                person=resident,
                date=start_date + timedelta(days=i),
                hours=10.0
            )

        # Verify validation at boundary
        result = validate_80_hour_rule(resident, target_date)
        assert result is not None, f"Failed at {description}"

    def test_leap_year_assignment(self, db):
        """Test assignment on Feb 29 (leap year)."""
        leap_date = date(2024, 2, 29)
        resident = create_resident(db)

        assignment = create_assignment(
            db, person=resident, date=leap_date
        )

        assert assignment.date == leap_date
        assert validate_assignment(assignment)

    def test_daylight_saving_time_transition(self, db):
        """Test assignments crossing DST transition."""
        # Fall back: 2:00 AM -> 1:00 AM (gain 1 hour)
        # Spring forward: 2:00 AM -> 3:00 AM (lose 1 hour)

        dst_transition = datetime(2025, 3, 9, 2, 0)  # Spring forward

        assignment = create_assignment(
            db,
            start_time=dst_transition,
            end_time=dst_transition + timedelta(hours=12),
        )

        # Duration calculation should handle DST correctly
        expected_hours = 11.0  # Not 12 (lose 1 hour)
        assert assignment.duration_hours == expected_hours
```

#### 2. Concurrency Edge Cases

```python
class TestConcurrencyEdgeCases:
    """Test concurrent operations."""

    def test_simultaneous_swap_same_resident(self, db):
        """Test two swap requests for same resident simultaneously."""
        import threading

        resident_a = create_resident(db, name="A")
        resident_b = create_resident(db, name="B")
        resident_c = create_resident(db, name="C")

        assign_a1 = create_assignment(db, person=resident_a)
        assign_b = create_assignment(db, person=resident_b)
        assign_c = create_assignment(db, person=resident_c)

        results = []

        def swap_a_with_b():
            result = execute_swap(resident_a, resident_b, assign_a1, assign_b)
            results.append(("a_b", result))

        def swap_a_with_c():
            assign_a2 = create_assignment(db, person=resident_a)
            result = execute_swap(resident_a, resident_c, assign_a2, assign_c)
            results.append(("a_c", result))

        t1 = threading.Thread(target=swap_a_with_b)
        t2 = threading.Thread(target=swap_a_with_c)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Both swaps should succeed (different assignments)
        assert all(success for _, success in results)

    def test_race_condition_schedule_generation(self, db):
        """Test schedule generation doesn't corrupt data under concurrent load."""
        import concurrent.futures

        def generate_schedule():
            return schedule_generator.generate_schedule(
                residents=large_resident_dataset,
                blocks=large_block_dataset,
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(generate_schedule) for _ in range(5)]
            schedules = [f.result() for f in futures]

        # All schedules should be valid
        for schedule in schedules:
            assert validate_schedule(schedule)

        # Database should be consistent
        assert verify_database_integrity(db)
```

#### 3. Data Edge Cases

```python
class TestDataEdgeCases:
    """Test edge cases with data values."""

    @pytest.mark.parametrize("value", [
        None,
        "",
        "   ",
        "a" * 1000,  # Very long string
        "\n\t\r",    # Whitespace only
        "'; DROP TABLE--",  # SQL injection attempt
        "<script>alert('xss')</script>",  # XSS attempt
    ])
    def test_resident_name_edge_cases(self, db, value):
        """Test resident creation with edge case names."""
        try:
            resident = create_resident(db, name=value)

            # If created, verify it's sanitized correctly
            retrieved = db.query(Person).filter(
                Person.id == resident.id
            ).first()

            assert retrieved is not None
            assert retrieved.name == (value if value else "Unknown")
        except ValueError:
            # Some values might be rejected, which is acceptable
            pass

    def test_zero_and_negative_hours(self, db):
        """Test assignment with zero and negative hours."""
        resident = create_resident(db)

        # Zero hours should be valid (resident off)
        assignment = create_assignment(db, person=resident, hours=0.0)
        assert validate_assignment(assignment)

        # Negative hours should fail validation
        with pytest.raises(ValueError):
            create_assignment(db, person=resident, hours=-5.0)

    def test_empty_schedule(self, db):
        """Test validation of completely empty schedule."""
        # No residents, no assignments
        assert len(db.query(Person).all()) == 0

        result = validate_schedule()
        assert result.is_valid
        assert result.warnings  # Should warn about empty schedule
```

#### 4. Business Logic Edge Cases

```python
class TestBusinessLogicEdgeCases:
    """Test business logic boundaries."""

    def test_exactly_80_hours_in_rolling_window(self, db):
        """Test resident with exactly 80 hours in rolling 4-week window."""
        resident = create_resident(db)

        # Create assignments totaling exactly 80 hours
        for i in range(8):  # 8 * 10 = 80
            create_assignment(
                db,
                person=resident,
                date=date(2025, 8, 1) + timedelta(days=i),
                hours=10.0
            )

        # Should be valid (exactly at limit)
        result = validator.validate_80_hour_rule(resident.id)
        assert result.is_valid

    def test_swap_into_own_shift(self, db):
        """Test resident trying to swap into their own shift."""
        resident = create_resident(db)
        assignment = create_assignment(db, person=resident)

        # Try to swap with themselves (no-op)
        result = validate_swap(
            initiator_id=resident.id,
            partner_id=resident.id,  # Same person
            initiator_assignment_id=assignment.id,
            partner_assignment_id=assignment.id,  # Same assignment
        )

        # Should be rejected
        assert not result.is_valid
        assert "cannot swap with self" in result.errors[0]

    def test_credential_expires_during_assignment(self, db):
        """Test credential that expires during an assignment."""
        resident = create_resident(db)
        assignment = create_assignment(
            db,
            person=resident,
            date=date(2025, 12, 15),
            rotation="Procedures"
        )

        # Credential expires on assignment date
        credential = create_credential(
            db,
            person=resident,
            type="BLS",
            expires_at=date(2025, 12, 15)  # Same day
        )

        # Should be invalid (credential expired on that date)
        result = validate_assignment_credentials(assignment)
        assert not result.is_valid
```

---

## Test Patterns & Best Practices

### Pattern Library

#### Pattern A: Fixture Composition

```python
"""Build complex fixtures from simpler ones."""

@pytest.fixture
def minimal_resident(db: Session) -> Person:
    """Minimal resident."""
    return create_resident(db, name="R1")

@pytest.fixture
def resident_with_assignments(db: Session, minimal_resident: Person) -> Person:
    """Resident with weekly assignments."""
    for day in range(7):
        create_assignment(
            db,
            person=minimal_resident,
            date=date(2025, 8, 1) + timedelta(days=day)
        )
    return minimal_resident

@pytest.fixture
def resident_with_leave(db: Session, resident_with_assignments: Person) -> Person:
    """Resident with both assignments and leave."""
    create_absence(
        db,
        person=resident_with_assignments,
        start_date=date(2025, 8, 8),
        end_date=date(2025, 8, 15),
        type="vacation"
    )
    return resident_with_assignments
```

#### Pattern B: Factory Pattern

```python
"""Use factories for flexible test data generation."""

from factory_boy import Factory

class ResidentFactory(Factory):
    class Meta:
        model = Person

    id = factory.LazyFunction(uuid4)
    name = factory.Faker("name")
    type = "resident"
    pgy_level = factory.Iterator([1, 2, 3])
    email = factory.LazyAttribute(
        lambda o: f"{o.name.lower()}@hospital.org"
    )

# Usage
resident = ResidentFactory(pgy_level=2)
residents = ResidentFactory.create_batch(10)
```

#### Pattern C: Mocking External Services

```python
"""Mock external service calls."""
from unittest.mock import patch, MagicMock

def test_with_mocked_email_service(db):
    """Test without actually sending emails."""
    with patch('app.notifications.email.send') as mock_send:
        mock_send.return_value = {"status": "sent"}

        result = notify_resident(db, resident_id)

        assert mock_send.called
        assert result["status"] == "sent"
```

#### Pattern D: Parametrized Tests

```python
"""Test multiple scenarios with single test."""

@pytest.mark.parametrize("pgy,expected_ratio", [
    (1, 2),    # PGY-1 needs 1:2 supervision
    (2, 4),    # PGY-2 needs 1:4 supervision
    (3, 4),    # PGY-3 needs 1:4 supervision
])
def test_supervision_ratio_by_pgy(db, pgy, expected_ratio):
    """Test supervision ratio requirements."""
    resident = create_resident(db, pgy_level=pgy)
    faculty = [create_faculty(db) for _ in range(expected_ratio)]

    result = validate_supervision_ratio(resident, faculty)
    assert result.is_valid
```

#### Pattern E: Context Manager Testing

```python
"""Test code using context managers."""

def test_transaction_rollback(db):
    """Test that failed transaction rolls back."""
    resident = create_resident(db)

    try:
        with db.begin_nested():
            create_assignment(db, person=resident)
            # Force an error
            raise ValueError("Test error")
    except ValueError:
        pass

    # Assignment should be rolled back
    assignments = db.query(Assignment).filter(
        Assignment.person_id == resident.id
    ).all()
    assert len(assignments) == 0
```

### Anti-Patterns to Avoid

```python
# ANTI-PATTERN 1: Hidden test dependencies
def test_resident_creation():
    """Tests depend on order of execution - BAD."""
    global CREATED_RESIDENT
    CREATED_RESIDENT = create_resident()
    assert CREATED_RESIDENT is not None

# BETTER: Use fixtures
def test_resident_creation(db):
    """Clear dependency on fixture."""
    resident = create_resident(db)
    assert resident is not None

# ANTI-PATTERN 2: Test too large/unfocused
def test_everything():
    """Tests multiple unrelated things."""
    resident = create_resident(db)
    assignment = create_assignment(db, person=resident)
    faculty = create_faculty(db)
    # Test 10 different things...

# BETTER: Focus on one thing
def test_resident_creation(db):
    """Test only resident creation."""
    resident = create_resident(db)
    assert resident.id is not None

# ANTI-PATTERN 3: Test assertions on strings
def test_error_message():
    """Brittle assertion on error message."""
    try:
        invalid_operation()
    except ValueError as e:
        assert str(e) == "Very specific error message"

# BETTER: Assert on error type and pattern
def test_error_type():
    """Check error type and pattern."""
    with pytest.raises(ValueError, match="specific.*error"):
        invalid_operation()
```

---

## Coverage Targets & Metrics

### Target Coverage

| Module | Target | Priority |
|--------|--------|----------|
| `app/scheduling/acgme_validator.py` | 95% | P0 - Critical |
| `app/services/swap_executor.py` | 95% | P0 - Critical |
| `app/scheduling/engine.py` | 90% | P0 - Critical |
| `app/api/routes/` | 80% | P1 - Important |
| `app/services/` | 90% | P1 - Important |
| `app/models/` | 70% | P2 - Nice to have |
| Overall Backend | 80% | Minimum |
| Frontend | 70% | Minimum |

### Measuring Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View coverage by file
pytest --cov=app --cov-report=term-missing | head -30

# Check specific module
pytest --cov=app.scheduling --cov-report=html tests/scheduling/

# Generate badge
coverage-badge -o coverage.svg -f
```

### Coverage Gaps

When coverage drops:

1. **Identify untested paths:**
   ```bash
   pytest --cov=app --cov-report=html
   # Open htmlcov/index.html and look for red lines
   ```

2. **Write targeted tests:**
   ```python
   def test_error_handling_in_xyz():
       """Cover the uncovered error path in xyz."""
       # Test the specific scenario
   ```

3. **Use coverage reports to prioritize:**
   - Critical paths: Require 95%+ coverage
   - Important paths: Require 80%+ coverage
   - Less critical: Require 60%+ coverage

---

## Fixture & Factory Strategies

### Fixture Scope

```python
# Function scope (default) - Fresh for each test
@pytest.fixture(scope="function")
def resident(db):
    return create_resident(db)

# Module scope - Reused across all tests in module
@pytest.fixture(scope="module")
def large_dataset():
    return create_1000_residents()

# Session scope - Reused across all tests
@pytest.fixture(scope="session")
def db_url():
    return "postgresql://localhost/test_db"
```

### Fixture Best Practices

```python
# GOOD: Fixture names describe what they create
@pytest.fixture
def resident_with_high_call_burden(db):
    """Create resident with many call assignments."""
    resident = create_resident(db)
    for _ in range(20):
        create_call_assignment(db, person=resident)
    return resident

# GOOD: Fixtures are composable
@pytest.fixture
def facility_with_residents(db):
    """Complete facility setup."""
    residents = [create_resident(db) for _ in range(10)]
    faculty = [create_faculty(db) for _ in range(3)]
    return {"residents": residents, "faculty": faculty}

# GOOD: Use cleanup for side effects
@pytest.fixture
def temporary_file():
    """Fixture that cleans up after itself."""
    path = "/tmp/test_schedule.json"
    yield path
    os.remove(path)  # Cleanup after test

# BAD: Unclear fixture names
@pytest.fixture
def data(db):  # What data?
    return create_something(db)

# BAD: Fixtures with side effects
@pytest.fixture
def send_email(db):  # Fixtures shouldn't send things
    send_notification()  # This runs for every test
    return
```

### FactoryBoy Patterns

```python
"""Advanced FactoryBoy usage."""

class ResidentFactory(factory.Factory):
    class Meta:
        model = Person

    # Basic attributes
    id = factory.LazyFunction(uuid4)
    name = factory.Faker("name")

    # Traits for variants
    class Params:
        high_call_burden = factory.Trait(
            # ... create with many call assignments
        )
        on_leave = factory.Trait(
            # ... create with active absence
        )

    # Post-generation hooks
    @factory.post_generation
    def add_assignments(obj, create, extracted, **kwargs):
        if not create:
            return

        for _ in range(4 * 7):  # Create 4 weeks of assignments
            AssignmentFactory(person=obj)

# Usage
resident = ResidentFactory()  # Basic
resident = ResidentFactory(high_call_burden=True)  # With trait
residents = ResidentFactory.create_batch(100)  # Many residents
```

---

## Quality Gates & Escalation

### Pre-Commit Gates

Before any commit, verify:

```bash
# 1. All tests pass
pytest --tb=short

# 2. Coverage acceptable
pytest --cov=app --cov-report=term-missing | grep "TOTAL"
# Should show >= 80%

# 3. No lint errors
ruff check app/
ruff format --check app/

# 4. Type checking passes
mypy app/

# 5. ACGME tests pass
pytest -m acgme
```

### Escalation Decision Tree

```
Test Failure Detected
├── Is it a known flaky test?
│   ├── YES → Rerun, document as flaky
│   └── NO → Continue
├── Is it in critical path? (ACGME, swap, auth)
│   ├── YES → P0 - Blocks merge
│   └── NO → Continue
├── Is it affecting multiple tests?
│   ├── YES → P1 - Investigate root cause
│   └── NO → P2 - Fix individually
└── Escalate: Create bug report with reproduction steps
```

### Bug Report Template (from QA_TESTER.md)

```markdown
## QA Escalation: [Bug Title]

**Agent:** QA_TESTER
**Severity:** [P0 | P1 | P2 | P3]
**Type:** [Bug | Test Failure | Flaky Test]

### Issue
[Clear description of problem]

### Reproduction
```python
@pytest.mark.skip(reason="Reproduce bug")
def test_bug_reproduction(db):
    # Minimal reproducible example
    pass
```

### Stack Trace
[Full error message if applicable]

### Impact
[Who is affected? How does it break functionality?]

### Recommended Fix
[Suggestion if known, or analysis]
```

---

## Advanced Workflows

### Workflow 1: Adding New Feature with TDD

```
1. Write failing test
   pytest tests/test_new_feature.py -v  # RED

2. Write minimal implementation
   # Just enough to make test pass

3. Run test
   pytest tests/test_new_feature.py -v  # GREEN

4. Refactor and improve
   # Clean up code while tests still pass

5. Add edge case tests
   # Test boundary conditions, error cases

6. Verify coverage
   pytest --cov=app.new_feature --cov-report=html

7. Run full suite
   pytest --tb=short
   pytest -m acgme
```

### Workflow 2: Debugging a Flaky Test

```
1. Identify the test
   pytest tests/test_xyz.py::TestClass::test_flaky -v -s

2. Run multiple times
   for i in {1..10}; do pytest tests/test_xyz.py::test_flaky -v; done

3. Collect failures
   # Note which runs failed, which succeeded

4. Add logging
   # Add print statements or logging to understand state

5. Identify timing issues
   # Look for sleep/timeout issues

6. Check for isolation problems
   # Verify fixtures clean up properly

7. Add delay if needed
   # Sometimes small sleep prevents race conditions

8. Document as flaky
   @pytest.mark.flaky(reruns=3, reruns_delay=1)
   def test_flaky():
```

### Workflow 3: Regression Testing After Fix

```
1. Write failing test that reproduces bug
   def test_bug_issue_247():
       # Setup for bug reproduction
       # Should fail before fix

2. Verify test fails
   pytest tests/test_regression.py::test_bug_issue_247 -v
   # Should show red failure

3. Apply fix
   # Fix the code in source

4. Verify test passes
   pytest tests/test_regression.py::test_bug_issue_247 -v
   # Should show green

5. Run related tests
   pytest tests/test_related.py -v

6. Run full suite
   pytest --tb=short

7. Tag test with issue number
   @pytest.mark.issue_247
   def test_bug_issue_247():

8. Document in test docstring
   def test_bug_issue_247():
       """
       Regression test for issue #247.

       Bug: Swap was not validating...
       Fix: Added validation check in swap_service.py
       """
```

---

## Reference: Complete Test Infrastructure Map

### Pytest Plugins & Tools

Installed pytest extensions:

- **pytest-cov** - Coverage measurement
- **pytest-asyncio** - Async test support
- **pytest-xdist** - Parallel test execution
- **pytest-mock** - Mocking utilities
- **factory-boy** - Test data generation
- **faker** - Fake data generation

### Test Database

```python
# In-memory SQLite for tests (conftest.py)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Key advantages:
# - No setup/teardown overhead
# - Parallel test execution safe
# - Fast test execution
# - Isolated from production
```

### Performance Benchmarks

Current performance thresholds (measured on CI):

| Operation | Time | Count |
|-----------|------|-------|
| 100 residents, 4-week validation | 5.0s | ~5,600 assignments |
| 50 residents, 4-week validation | 2.0s | ~2,800 assignments |
| 25 residents, 2-week validation | 1.0s | ~700 assignments |
| 10 concurrent validations | 10.0s | 100 residents each |
| 12-week validation | 15.0s | ~16,800 assignments |

### Key Test Files & Responsibilities

| File | Tests | Maintainer Notes |
|------|-------|------------------|
| `test_acgme_comprehensive.py` | ACGME validator | Critical - regulatory |
| `test_swap_executor.py` | Swap logic | Critical - user-facing |
| `test_swap_executor_edge_cases.py` | Edge cases | Important - catch bugs early |
| `test_conflict_alert_service.py` | Conflict detection | Important - prevents oversched |
| `test_auth_routes.py` | Authentication | Critical - security |
| Integration tests | End-to-end flows | Important - catch integration bugs |
| Performance tests | Load scenarios | Important - catch scaling issues |

---

## Conclusion & Next Steps

### For QA_TESTER Implementation

The enhanced specification provides:

✓ **Complete testing infrastructure mapping** - Know where to find and add tests
✓ **Concrete code patterns** - Copy-paste examples for common test scenarios
✓ **Coverage strategies** - Know what to test and what thresholds to enforce
✓ **Edge case framework** - Systematic approach to finding corner cases
✓ **Performance benchmarks** - Know acceptable performance thresholds
✓ **Advanced workflows** - TDD, debugging, regression testing, flaky test handling

### For Effective Agent Delegation

When delegating to QA_TESTER:

1. **Provide context** - Specific test area, recent changes, known concerns
2. **Specify scope** - "Test ACGME compliance" vs. "Test everything"
3. **Request output** - Test names, coverage report, bug report format
4. **Allow autonomy** - QA_TESTER knows when to escalate

### Document History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2025-12-30 | Enhanced spec with infrastructure mapping, patterns, workflows |
| 1.1 | 2025-12-29 | Added context isolation section |
| 1.0 | 2025-12-26 | Initial QA_TESTER agent specification |

---

**Document prepared by:** G2_RECON (SEARCH_PARTY Operation)
**Reconnaissance Status:** COMPLETE - All testing infrastructure mapped and documented
**Next Review:** 2026-01-30 (Monthly)
