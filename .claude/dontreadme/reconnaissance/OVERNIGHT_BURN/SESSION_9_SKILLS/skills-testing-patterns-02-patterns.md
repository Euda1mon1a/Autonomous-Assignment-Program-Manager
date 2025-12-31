# Claude Code Skills Testing Patterns - Part 2 of 3: Testing Patterns

**Document Purpose:** Backend, Frontend, and Integration/E2E testing patterns for Claude Code skills.

**Last Updated:** 2025-12-30
**Author:** G2_RECON (SEARCH_PARTY Operation)

**Part 2 of 3:** Backend Testing, Frontend Testing, and Integration & E2E Testing
**See Also:** [Part 1 - Foundations](skills-testing-patterns-01-foundations.md) | [Part 3 - Implementation](skills-testing-patterns-03-implementation.md)

---

## Table of Contents

5. [Backend Testing Patterns (Python/pytest)](#backend-testing-patterns-pythonpytest)
6. [Frontend Testing Patterns (TypeScript/Jest)](#frontend-testing-patterns-typescriptjest)
7. [Integration & E2E Testing](#integration--e2e-testing)

---

## Backend Testing Patterns (Python/pytest)

### (HISTORY + NATURE Lenses)

#### Test File Organization

**Standard Structure:**

```python
"""Tests for swap executor service."""
import pytest
from datetime import date
from unittest.mock import AsyncMock, patch

from app.services.swap_executor import SwapExecutor
from app.models.swap import SwapRequest

class TestSwapExecutor:
    """Test suite for SwapExecutor service."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        return SwapExecutor()

    async def test_execute_swap_success(self, executor, db_session):
        """Test successful swap execution."""
        # Setup
        swap = create_test_swap(...)

        # Execute
        result = await executor.execute_swap(db_session, swap)

        # Validate
        assert result.status == "completed"

    async def test_execute_swap_failure(self, executor):
        """Test swap execution with error."""
        with pytest.raises(ValueError):
            await executor.execute_swap(None, None)
```

#### Test Naming Conventions

| Pattern | Format | Example |
|---------|--------|---------|
| **Happy Path** | `test_{function}_{scenario}` | `test_execute_swap_success` |
| **Edge Case** | `test_{function}_{edge_case}` | `test_execute_swap_past_date` |
| **Error Case** | `test_{function}_{error}_error` | `test_execute_swap_db_error` |
| **Integration** | `test_{function}_integration` | `test_execute_swap_integration` |

#### Fixture Patterns

**Factory Fixture Pattern:**

```python
@pytest.fixture
def person_factory(db_session):
    """Factory for creating test persons."""
    created = []

    async def _create(
        name: str = "Test Person",
        role: str = "RESIDENT",
        **kwargs
    ) -> Person:
        person = Person(id=str(uuid4()), name=name, role=role, **kwargs)
        db_session.add(person)
        await db_session.flush()
        created.append(person)
        return person

    yield _create

    # Cleanup
    for person in created:
        await db_session.delete(person)
```

**Composition Fixture Pattern:**

```python
@pytest.fixture
async def schedule_with_assignments(db_session, person_factory, block_factory):
    """Composite fixture with related entities."""
    residents = [
        await person_factory(name=f"Resident {i}", role="RESIDENT")
        for i in range(3)
    ]
    faculty = await person_factory(role="FACULTY")
    blocks = [await block_factory(date=date.today() + timedelta(days=i)) for i in range(7)]

    # Create assignments
    for i, block in enumerate(blocks):
        assignment = Assignment(
            person_id=residents[i % len(residents)].id,
            block_id=block.id,
        )
        db_session.add(assignment)

    await db_session.flush()
    return {"residents": residents, "faculty": faculty, "blocks": blocks}
```

#### Async Testing Pattern

**Proper Async Setup:**

```python
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create isolated async database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()

@pytest.mark.asyncio
async def test_async_operation(db_session):
    """Test async database operation."""
    result = await service.get_all(db_session)
    assert len(result) >= 0
```

#### Mocking Patterns

**AsyncMock for Async Functions:**

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_async_mock():
    mock_fetch = AsyncMock(return_value={"data": "value"})

    with patch("app.services.external.fetch_data", mock_fetch):
        result = await service.process_data()

    mock_fetch.assert_called_once()
    assert result["data"] == "value"
```

**Mocking Database Queries:**

```python
@pytest.mark.asyncio
async def test_service_with_mocked_db():
    """Test service without real database."""
    mock_db = AsyncMock(spec=AsyncSession)

    # Mock query result chain
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Person(id="1", name="Test"),
    ]
    mock_db.execute.return_value = mock_result

    result = await person_service.get_all(mock_db)
    assert len(result) == 1
```

#### Parametrized Testing

**Basic Parametrization:**

```python
@pytest.mark.parametrize("hours,expected_valid", [
    (40, True),   # Normal week
    (80, True),   # Maximum allowed
    (81, False),  # Over limit
    (0, True),    # No hours
    (-1, False),  # Invalid negative
])
def test_weekly_hours_validation(hours, expected_valid):
    result = validate_weekly_hours(hours)
    assert result.is_valid == expected_valid
```

**Parametrize with Fixtures:**

```python
@pytest.fixture(params=["RESIDENT", "FACULTY", "ADMIN"])
def role(request):
    return request.param

@pytest.mark.asyncio
async def test_permission_by_role(db_session, role, person_factory):
    """Test runs once per role."""
    person = await person_factory(role=role)
    permissions = await get_permissions(person)

    if role == "ADMIN":
        assert "delete_schedule" in permissions
```

#### Markers and Selection

**Running Tests by Marker:**

```bash
# Run only ACGME compliance tests
pytest -m acgme

# Run integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run specific test file
pytest tests/services/test_swap_executor.py

# Run tests matching pattern
pytest -k "test_swap"
```

#### Coverage Commands

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html --cov-report=term-missing

# Fail if coverage drops below 70%
pytest --cov=app --cov-fail-under=70

# Show only lines not covered
pytest --cov=app --cov-report=term-missing:skip-covered
```

---

## Frontend Testing Patterns (TypeScript/Jest)

### (NATURE + PERCEPTION Lenses)

#### Jest Test Structure

**Standard Component Test:**

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ScheduleView } from '@/components/ScheduleView';

describe('ScheduleView', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  beforeEach(() => {
    queryClient.clear();
  });

  it('renders schedule data when loaded', async () => {
    render(<ScheduleView scheduleId="123" />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Schedule 123')).toBeInTheDocument();
    });
  });

  it('handles error state', async () => {
    render(<ScheduleView scheduleId="invalid" />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});
```

#### Hook Testing

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useSchedule } from '@/hooks/useSchedule';

describe('useSchedule', () => {
  it('fetches schedule data', async () => {
    const { result } = renderHook(() => useSchedule('123'), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.id).toBe('123');
  });

  it('handles error state', async () => {
    const { result } = renderHook(() => useSchedule('invalid'), { wrapper });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});
```

#### TypeScript Test Typing

**Proper Type Safety:**

```typescript
interface TestComponentProps {
  scheduleId: string;
  onUpdate: (schedule: Schedule) => void;
}

describe('TestComponent', () => {
  const defaultProps: TestComponentProps = {
    scheduleId: '123',
    onUpdate: jest.fn(),
  };

  it('calls onUpdate with correct type', () => {
    const onUpdate = jest.fn();
    render(<TestComponent {...defaultProps} onUpdate={onUpdate} />);

    fireEvent.click(screen.getByRole('button'));

    expect(onUpdate).toHaveBeenCalledWith(expect.objectContaining({
      id: '123'
    }));
  });
});
```

#### Testing TanStack Query

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { server } from './mocks/server';
import { rest } from 'msw';

describe('API Data Fetching', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  it('refetches on error', async () => {
    const { result } = renderHook(
      () => useSchedules(),
      { wrapper: ({ children }) =>
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      }
    );

    await waitFor(() => expect(result.current.isFetching).toBe(false));

    expect(result.current.isError).toBe(false);
  });
});
```

#### Jest Configuration (Inferred)

```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  testMatch: [
    '**/__tests__/**/*.ts?(x)',
    '**/?(*.)+(spec|test).ts?(x)'
  ],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  collectCoverageFrom: [
    'src/**/*.ts(x)',
    '!src/**/*.d.ts',
    '!src/index.tsx'
  ],
};
```

---

## Integration & E2E Testing

### (HISTORY + SURVIVAL Lenses)

#### Scenario-Based Testing Framework

**Scenario Definition Structure:**

```yaml
scenario:
  name: "N-1 Failure During Holiday Coverage"
  id: "n1-holiday-coverage-001"
  category: "resilience"
  tags: ["n-1", "holiday", "acgme"]

  setup:
    persons:
      - id: "resident-1"
        role: "RESIDENT"
        pgy_level: 2
        max_hours_per_week: 80

    assignments:
      - person_id: "resident-1"
        block_date: "2024-12-25"
        rotation: "inpatient"
        hours: 12

  test_case:
    operation: "simulate_unavailability"
    parameters:
      person_id: "resident-1"
      start_date: "2024-12-25"
      end_date: "2024-12-27"
      reason: "illness"

  expected_outcome:
    success: true
    coverage_maintained: true
    acgme_compliant: true
    backup_activated: true
    max_reassignments: 5
```

**Scenario Execution:**

```python
from app.testing.scenario_executor import ScenarioExecutor

async def test_n1_holiday_coverage():
    """Run N-1 failure scenario."""
    executor = ScenarioExecutor()

    result = await executor.run_scenario(
        scenario_id="n1-holiday-coverage-001",
        timeout=300,  # 5 minutes
        capture_metrics=True
    )

    # Validate results
    assert result.status == "passed"
    assert result.validations["acgme_compliant"]["passed"]
    assert result.execution_time_seconds < 5
```

#### E2E Testing Organization

```
backend/tests/e2e/
├── test_schedule_generation_e2e.py
├── test_swap_operations_e2e.py
├── test_compliance_audit_e2e.py
├── test_resilience_e2e.py
├── test_multi_operation_chain_e2e.py
└── test_performance_e2e.py
```

**E2E Test Pattern:**

```python
@pytest.mark.integration
class TestScheduleGenerationE2E:
    """End-to-end schedule generation workflow."""

    async def test_full_generation_workflow(self, db_session, seed_data):
        """Test complete schedule generation from request to publication."""
        # Setup: Create program with people and rotations
        program = seed_data["program"]
        persons = seed_data["persons"]
        rotations = seed_data["rotations"]

        # Generate schedule
        scheduler = ScheduleGenerator(db_session)
        schedule = await scheduler.generate(
            program_id=program.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )

        # Validate ACGME compliance
        validator = ACGMEValidator(db_session)
        compliance = await validator.validate(schedule)

        assert compliance.is_valid
        assert len(schedule.assignments) > 0
        assert all(a.person_id in [p.id for p in persons] for a in schedule.assignments)
```

#### Performance Testing

```python
@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmarks for critical operations."""

    async def test_schedule_generation_performance(self, benchmark_data):
        """Ensure schedule generation completes within SLA."""
        import time

        start = time.time()
        result = await generate_schedule(
            db_session=benchmark_data["db"],
            **benchmark_data["params"]
        )
        elapsed = time.time() - start

        assert result.is_valid
        assert elapsed < 5.0, f"Generation took {elapsed:.2f}s, expected < 5s"

    @pytest.mark.slow
    async def test_validation_load(self, db_session, large_schedule):
        """Test validation doesn't degrade with large datasets."""
        validator = ACGMEValidator(db_session)

        import time
        start = time.time()
        result = await validator.validate(large_schedule)
        elapsed = time.time() - start

        # Should complete in < 10s even with 1000+ assignments
        assert elapsed < 10.0
        assert result.is_valid
```

---


---

**Next Section:** [Part 3 - CI/CD Integration & Implementation](skills-testing-patterns-03-implementation.md)

**Updated:** 2025-12-31 | **Part 2 of 3**
