# Claude Code Skills Testing Patterns

**Document Purpose:** Comprehensive reference for testing Claude Code skills in the Residency Scheduler project.

**Last Updated:** 2025-12-30
**Author:** G2_RECON (SEARCH_PARTY Operation)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Testing Landscape](#current-testing-landscape)
3. [Skill Categories & Testing Approaches](#skill-categories--testing-approaches)
4. [Testing Framework Overview](#testing-framework-overview)
5. [Backend Testing Patterns (Python/pytest)](#backend-testing-patterns-pythonpytest)
6. [Frontend Testing Patterns (TypeScript/Jest)](#frontend-testing-patterns-typescriptjest)
7. [Integration & E2E Testing](#integration--e2e-testing)
8. [CI/CD Integration](#cicd-integration)
9. [Coverage Recommendations](#coverage-recommendations)
10. [Skill-Specific Testing Guidance](#skill-specific-testing-guidance)
11. [Common Pitfalls & Fixes](#common-pitfalls--fixes)
12. [Quality Gates & Validation](#quality-gates--validation)
13. [Testing Skills Themselves](#testing-skills-themselves)

---

## Executive Summary

### Key Findings (PERCEPTION + INVESTIGATION)

**Project Testing Maturity:** HIGH
- 175+ test files across `backend/tests/`
- Comprehensive pytest infrastructure with fixtures and parametrization
- CI/CD integration with GitHub Actions (13 workflows)
- Coverage reporting via Codecov
- Segregated test organization (unit, integration, performance, resilience, scenarios)

**Skills Testing Coverage:** PARTIAL
- 15 skills with dedicated testing frameworks (test-writer, python-testing-patterns, etc.)
- Pre-flight validation for constraints (constraint-preflight skill)
- Scenario-based testing for complex operations (test-scenario-framework)
- NO dedicated skill execution tests (skills themselves are not being tested)
- Missing: Skill composition validation, MCP tool integration tests

**Critical Gaps Identified:**
1. **Skill Execution Tests** - Skills are documented but not tested for correctness
2. **MCP Tool Integration** - No tests verifying MCP tools work correctly with skills
3. **Skill Composition** - No tests for parallel/serialized skill execution
4. **Error Handling** - Missing tests for skill failure scenarios
5. **CI Integration** - Skills not validated in CI/CD pipeline

---

## Current Testing Landscape

### (PERCEPTION Lens)

#### Test Directory Structure

```
backend/tests/
├── conftest.py                      # Shared pytest fixtures (100+ lines)
├── __init__.py
├── TEST_SUMMARY.md
├── TEST_EXPANSION_SUMMARY.md
├── api/                            # API endpoint tests
├── auth/                           # Authentication tests
├── autonomous/                     # Autonomous operation tests (NEW)
├── constraints/                    # Constraint validation tests
├── factories/                      # Test data factories
├── health/                         # Health check tests
├── integration/                    # Integration tests (27 modules)
├── performance/                    # Performance & load tests
├── resilience/                     # Resilience framework tests
├── routes/                         # API route tests
├── scenarios/                      # Scenario-based tests
├── e2e/                           # End-to-end tests
└── [140+ individual test files]

```

#### Test Markers (pytest.ini)

```ini
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    acgme: marks tests related to ACGME compliance
    performance: marks tests as performance/load tests
```

#### Available Fixtures (conftest.py)

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `db` | function | Fresh in-memory SQLite for each test |
| `client` | function | TestClient with DB override |
| `admin_user` | function | Pre-authenticated admin user |
| `auth_headers` | function | Bearer token headers |
| `sample_resident` | function | Test resident person |
| `sample_faculty` | function | Test faculty person |

#### CI/CD Workflow Integration

```yaml
# .github/workflows/ci.yml - Primary testing pipeline
Backend Tests:
  - Python 3.11
  - PostgreSQL 15 service
  - Coverage reporting to Codecov
  - Artifact upload (HTML reports)

Frontend Tests:
  - Node 20
  - Jest with coverage
  - Jest XML reports

Triggers:
  - Pull requests to main/master/develop
  - Pushes to main/master/claude/** branches
```

---

## Skill Categories & Testing Approaches

### (INVESTIGATION + ARCANA Lenses)

#### Skill Type Matrix

| Skill Category | Count | Testing Approach | Examples |
|---|---|---|---|
| **Knowledge Skills** | 12 | Documentation, reference validation | acgme-compliance, code-review, docker-containerization |
| **Workflow Skills** | 8 | Scenario + integration tests | COMPLIANCE_VALIDATION, SCHEDULING, SWAP_EXECUTION |
| **Framework Skills** | 5 | Pattern validation + examples | test-scenario-framework, python-testing-patterns, test-writer |
| **Development Skills** | 10 | Pre-flight checks + code analysis | constraint-preflight, automated-code-fixer, lint-monorepo |
| **Meta Skills** | 4 | Context management + orchestration | MCP_ORCHESTRATION, CORE, context-aware-delegation, startup |

#### Knowledge Skills (Reference-Based)

**Examples:** `acgme-compliance`, `code-review`, `docker-containerization`, `security-audit`

**How They're Currently Tested:**
1. By human review of documentation correctness
2. By application of recommendations in actual code review
3. By CI validation when rules are enforced

**Testing Gaps:**
- No automated validation that knowledge is current
- No test that recommendations are correct
- No verification that examples compile/execute

**Testing Strategy:**
```python
# Example: Test that ACGME compliance knowledge is current
@pytest.mark.skill
def test_acgme_compliance_skill_knowledge():
    """Verify ACGME compliance skill references are current."""
    from .claude.skills.acgme_compliance import SKILL

    # Load skill documentation
    skill_doc = read_skill_doc("acgme-compliance")

    # Validate: 80-hour rule cited correctly
    assert "80 hours" in skill_doc
    assert "4-week rolling average" in skill_doc

    # Validate: 1-in-7 rule present
    assert "one 24-hour period" in skill_doc or "1-in-7" in skill_doc

    # Validate: supervision ratios documented
    assert "PGY-1" in skill_doc and ("1:2" in skill_doc or "2:1" in skill_doc)
```

#### Workflow Skills (Execution-Based)

**Examples:** `COMPLIANCE_VALIDATION`, `SCHEDULING`, `SWAP_EXECUTION`

**How They're Currently Tested:**
1. By running actual backend operations they orchestrate
2. By scenario-based testing (test-scenario-framework)
3. By integration tests validating API operations

**Testing Gaps:**
- No tests that skills are invoked correctly
- No validation of skill error handling
- Missing rollback/recovery tests

**Testing Strategy:**
```python
# Example: Test workflow skill execution
@pytest.mark.skill
async def test_swap_execution_workflow(db_session):
    """Verify SWAP_EXECUTION skill orchestrates swap correctly."""
    from app.skills.swap_execution import SwapExecutionWorkflow

    # Setup: Create valid swap request
    swap = create_test_swap(db_session, ...)

    # Execute: Run the skill workflow
    workflow = SwapExecutionWorkflow(db_session)
    result = await workflow.execute(swap)

    # Validate: Verify workflow outputs
    assert result.status == "completed"
    assert result.audit_trail is not None
    assert result.rollback_capability is not None
```

#### Framework Skills (Pattern + Template Validation)

**Examples:** `test-scenario-framework`, `python-testing-patterns`, `test-writer`

**How They're Currently Tested:**
1. Through examples in skill documentation
2. By observing if generated tests pass
3. Manual verification of generated code patterns

**Testing Gaps:**
- No tests that generated tests are syntactically correct
- No validation of test coverage targets
- Missing scenario composition validation

**Testing Strategy:**
```python
# Example: Test framework skill generates valid tests
@pytest.mark.skill
def test_test_writer_generates_valid_pytest():
    """Verify test-writer skill generates correct pytest code."""
    from .claude.skills.test_writer import TestWriter

    # Define source code to test
    source = """
    def calculate_hours(assignments: list[Assignment]) -> float:
        return sum(a.hours for a in assignments)
    """

    # Generate tests using skill
    writer = TestWriter()
    tests = writer.generate_tests(source)

    # Validate: Tests are syntactically correct
    compile(tests, '<string>', 'exec')

    # Validate: Tests include happy path
    assert "def test_" in tests
    assert "calculate_hours" in tests
```

#### Development Skills (Pre-Flight / Analysis)

**Examples:** `constraint-preflight`, `automated-code-fixer`, `lint-monorepo`

**How They're Currently Tested:**
1. By running verification scripts
2. By checking CI/CD output
3. By manual inspection of fixes

**Testing Gaps:**
- No automated validation of pre-flight checks
- Missing test for all error detection scenarios
- No regression tests for fixes

**Testing Strategy:**
```python
# Example: Test constraint-preflight detects unregistered constraints
@pytest.mark.skill
def test_constraint_preflight_detects_unregistered():
    """Verify constraint-preflight skill detects missing registrations."""
    from .claude.skills.constraint_preflight import ConstraintPreflight

    # Create unregistered constraint scenario
    create_unregistered_constraint()

    # Run pre-flight check
    preflight = ConstraintPreflight()
    results = preflight.verify_all_constraints()

    # Validate: Error detected
    assert any("not registered" in r.message for r in results if r.severity == "error")
```

---

## Testing Framework Overview

### Testing Infrastructure

#### Backend (Python/pytest)

**Configuration File:** `backend/pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
minversion = 7.0

addopts =
    -v
    --tb=short
    --strict-markers
    -ra

markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    acgme: marks tests related to ACGME compliance
    performance: marks tests as performance/load tests

asyncio_mode = auto
```

**Key Dependencies:**
- `pytest` 7.0+ - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-xdist` - Parallel execution

**Database Setup:**
```python
# Using in-memory SQLite for speed
TEST_DATABASE_URL = "sqlite:///:memory:"

# With StaticPool to prevent threading issues
poolclass=StaticPool
```

#### Frontend (TypeScript/Jest)

**Configuration:** Inferred from `frontend/jest.config.js`

```javascript
// Expected configuration
{
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.ts?(x)', '**/?(*.)+(spec|test).ts?(x)'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1'
  },
  collectCoverageFrom: ['src/**/*.ts(x)', '!src/**/*.d.ts']
}
```

**Key Dependencies:**
- `jest` - Test framework
- `@testing-library/react` - React component testing
- `@testing-library/jest-dom` - DOM matchers
- `jest-junit` - JUnit XML reports
- `ts-jest` - TypeScript support

#### Test Database Strategy

**In-Memory SQLite (Fast)**
```python
@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create isolated DB per test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
```

**PostgreSQL Service (CI/CD)**
```yaml
services:
  postgres:
    image: postgres:15-alpine
    env:
      POSTGRES_DB: test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
```

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

## CI/CD Integration

### (PERCEPTION + MEDICINE Lenses)

#### GitHub Actions Workflow

**Primary CI Pipeline:** `.github/workflows/ci.yml`

```yaml
name: CI - Tests
on:
  pull_request:
    branches: [main, master, develop]
  push:
    branches:
      - main
      - 'claude/**'

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "20"

jobs:
  # Step 1: Detect changes
  changes:
    runs-on: ubuntu-latest
    outputs:
      backend: ${{ steps.filter.outputs.backend }}
      frontend: ${{ steps.filter.outputs.frontend }}
    steps:
      - uses: actions/checkout@v6
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            backend:
              - 'backend/**'
            frontend:
              - 'frontend/**'

  # Step 2: Run backend tests
  backend-tests:
    needs: changes
    if: ${{ needs.changes.outputs.backend == 'true' }}
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r backend/requirements.txt

      - name: Run tests with coverage
        run: pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v5
        with:
          files: backend/coverage.xml

  # Step 3: Run frontend tests
  frontend-tests:
    needs: changes
    if: ${{ needs.changes.outputs.frontend == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v6
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci --prefix frontend

      - name: Run tests
        run: npm run test:coverage --prefix frontend
```

#### Quality Gates

```yaml
# Before PR can merge, these checks must pass:

✅ CI - Tests (ci.yml)
  - backend-tests: pytest passes
  - frontend-tests: npm test passes
  - coverage-report: Codecov comment added

✅ Code Quality (code-quality.yml)
  - lint: ruff check pass
  - types: mypy pass
  - format: prettier/black pass

✅ Security (security.yml)
  - bandit: Security scan pass
  - dependabot: Dependency checks pass

✅ Docs (docs.yml)
  - Links verified
  - API docs generated
```

#### Coverage Thresholds (Suggested)

```python
# backend/pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-fail-under=70"

# By layer:
# - Services: 80%+ coverage required
# - Controllers: 75%+ coverage required
# - Models: 70%+ coverage required
# - Utils: 85%+ coverage required
```

---

## Coverage Recommendations

### (INVESTIGATION + INSIGHT Lenses)

#### Target Coverage by Component

| Component | Target | Minimum | Rationale |
|-----------|--------|---------|-----------|
| **Services** | 85% | 80% | Core business logic |
| **Controllers** | 80% | 75% | Request handling |
| **Models** | 75% | 70% | Data layer |
| **Utilities** | 90% | 85% | Reusable functions |
| **Routes** | 75% | 65% | Endpoint mappings |
| **Overall** | 80% | 70% | Project threshold |

#### Coverage Calculation Example

```bash
# Generate coverage report with missing lines
pytest --cov=app --cov-report=html --cov-report=term-missing

# Output shows:
# Name                    Stmts   Miss  Cover   Missing
# ─────────────────────────────────────────────────────
# app/services/swap.py      150     15   90%    45-50, 120-125
# app/models/person.py      120     30   75%    40-70, 100-115
#                          ─────  ─────  ──────
# TOTAL                    2450    350   85%

# Calculate: (2450 - 350) / 2450 = 85% coverage
```

#### Gap Analysis

**Coverage Gap Report:**

```python
# Script: scripts/coverage_analysis.py

import coverage
import json

cov = coverage.Coverage()
cov.load()

# Get coverage by type
gaps = {
    "services": analyze_layer("app/services"),
    "controllers": analyze_layer("app/controllers"),
    "models": analyze_layer("app/models"),
}

# Identify high-impact gaps
high_priority = [
    (module, lines)
    for module, lines in gaps.items()
    if len(lines) > 5 and module_is_critical(module)
]

print(f"High-priority coverage gaps: {len(high_priority)}")
for module, lines in high_priority:
    print(f"  {module}: {len(lines)} uncovered lines")
```

#### Coverage Improvement Plan

1. **Identify Gaps:** `pytest --cov=app --cov-report=term-missing`
2. **Prioritize:** Focus on high-traffic code paths (services, controllers)
3. **Generate Tests:** Use test-writer skill for uncovered functions
4. **Verify:** Re-run coverage after adding tests
5. **Document:** Add to PR description what's newly covered

---

## Skill-Specific Testing Guidance

### (ARCANA + RELIGION Lenses)

#### By Skill Type

##### Knowledge Skills Testing

**Skills:** `acgme-compliance`, `code-review`, `docker-containerization`, `security-audit`

**Testing Approach:**
1. Validate documentation references are correct
2. Test that examples compile/execute
3. Verify recommendations are actionable

```python
# Example: Test knowledge skill examples execute
@pytest.mark.skill
def test_code_review_skill_examples_are_valid():
    """Verify code-review skill examples compile."""
    skill_doc = read_skill("code-review")

    # Extract code examples from documentation
    examples = extract_code_blocks(skill_doc, language="python")

    # Test each example compiles
    for example in examples:
        try:
            compile(example, '<example>', 'exec')
        except SyntaxError as e:
            pytest.fail(f"Example failed to compile: {e}")
```

##### Workflow Skills Testing

**Skills:** `COMPLIANCE_VALIDATION`, `SCHEDULING`, `SWAP_EXECUTION`

**Testing Approach:**
1. Test each workflow phase in isolation
2. Test complete workflow end-to-end
3. Test error handling and rollback

```python
# Example: Test workflow skill phases
@pytest.mark.skill
async def test_compliance_validation_workflow_phases(db_session):
    """Test COMPLIANCE_VALIDATION skill workflow phases."""
    from app.skills.compliance_validation import ComplianceValidation

    skill = ComplianceValidation(db_session)
    schedule = create_test_schedule(db_session)

    # Phase 1: Audit
    audit_result = await skill.audit_schedule(schedule)
    assert audit_result.phase == "audit"
    assert audit_result.violations is not None

    # Phase 2: Analyze
    analysis = await skill.analyze_violations(audit_result.violations)
    assert analysis.phase == "analyze"
    assert analysis.patterns is not None

    # Phase 3: Remediate
    remediation = await skill.remediate(analysis)
    assert remediation.phase == "remediate"
    assert remediation.fixed_violations > 0
```

##### Framework Skills Testing

**Skills:** `test-scenario-framework`, `python-testing-patterns`, `test-writer`

**Testing Approach:**
1. Verify generated artifacts are valid
2. Test that patterns match documentation
3. Validate output quality

```python
# Example: Test test-writer skill generates valid tests
@pytest.mark.skill
def test_test_writer_generates_valid_tests():
    """Verify test-writer generates syntactically correct pytest."""
    from app.skills.test_writer import TestWriter

    source = """
    async def swap_assignments(db, swap_id):
        swap = await db.get(Swap, swap_id)
        if not swap:
            raise ValueError("Swap not found")
        return await execute_swap(db, swap)
    """

    writer = TestWriter()
    generated_tests = writer.generate_tests(source)

    # Validate syntax
    compile(generated_tests, '<generated>', 'exec')

    # Validate it tests the function
    assert "def test_" in generated_tests
    assert "swap_assignments" in generated_tests
    assert "ValueError" in generated_tests  # Should test error case
```

##### Development Skills Testing

**Skills:** `constraint-preflight`, `automated-code-fixer`, `lint-monorepo`

**Testing Approach:**
1. Test detection of all error types
2. Test fix correctness
3. Test no false positives

```python
# Example: Test automated-code-fixer detects and fixes
@pytest.mark.skill
async def test_automated_code_fixer_detects_and_fixes(tmp_path):
    """Verify automated-code-fixer detects and fixes issues."""
    from app.skills.automated_code_fixer import AutomatedCodeFixer

    # Create file with multiple issues
    test_file = tmp_path / "broken.py"
    test_file.write_text("""
import os
import sys
import json  # Unused

def test():
    x = 1
    y = 2
    z = x + y  # Unused variable
    return True
""")

    fixer = AutomatedCodeFixer()
    results = await fixer.fix_file(str(test_file))

    # Should detect unused imports and variables
    assert any("unused" in r.message for r in results)

    # Fixed file should be valid Python
    fixed_content = test_file.read_text()
    compile(fixed_content, str(test_file), 'exec')
```

#### MCP Tool Integration Testing

**Critical Gap:** No tests verify MCP tools work correctly

**Proposed Test Structure:**

```python
# backend/tests/skills/test_mcp_tool_integration.py

@pytest.mark.skill
@pytest.mark.mcp
class TestMCPToolIntegration:
    """Test that skills correctly invoke MCP tools."""

    async def test_mcp_tool_exists(self):
        """Verify MCP tools are registered."""
        from app.mcp_client import MCPClient

        client = MCPClient()
        tools = await client.list_tools()

        # Should have 29+ tools registered
        assert len(tools) > 25
        assert any(t.name == "validate_acgme_compliance" for t in tools)

    async def test_mcp_tool_executes(self):
        """Verify MCP tools can be executed."""
        from app.mcp_client import MCPClient

        client = MCPClient()
        result = await client.call_tool(
            name="validate_acgme_compliance",
            arguments={"schedule_id": "test-123"}
        )

        # Should return valid response
        assert result is not None
        assert hasattr(result, "violations") or hasattr(result, "is_valid")

    async def test_skill_uses_mcp_correctly(self):
        """Verify COMPLIANCE_VALIDATION skill uses MCP tools."""
        from app.skills.compliance_validation import ComplianceValidation
        from unittest.mock import AsyncMock, patch

        # Mock MCP client
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = {
            "is_valid": True,
            "violations": []
        }

        with patch("app.skills.compliance_validation.MCPClient", return_value=mock_client):
            skill = ComplianceValidation()
            result = await skill.audit_schedule("test-schedule")

        # Should have called MCP tool
        mock_client.call_tool.assert_called_once()
        assert "validate_acgme_compliance" in str(mock_client.call_tool.call_args)
```

#### Skill Composition Testing

**Critical Gap:** No tests verify skill composition (parallel/serialized execution)

**Proposed Test Structure:**

```python
# backend/tests/skills/test_skill_composition.py

@pytest.mark.skill
@pytest.mark.composition
class TestSkillComposition:
    """Test composition of multiple skills."""

    async def test_serialized_skills_execute_in_order(self):
        """Verify serialized skills execute in correct order."""
        from app.skills.orchestration import SkillOrchestrator

        execution_order = []

        # Mock skills that track execution
        skill1 = AsyncMock(name="skill1")
        skill1.side_effect = lambda: (execution_order.append("skill1"), "result1")[1]

        skill2 = AsyncMock(name="skill2")
        skill2.side_effect = lambda: (execution_order.append("skill2"), "result2")[1]

        # Execute with serialization requirement
        orchestrator = SkillOrchestrator()
        await orchestrator.execute_serialized([skill1, skill2])

        # Verify order
        assert execution_order == ["skill1", "skill2"]

    async def test_parallel_skills_execute_concurrently(self):
        """Verify parallel-safe skills execute concurrently."""
        from app.skills.orchestration import SkillOrchestrator

        import time

        # Mock skills with delays
        skill1 = AsyncMock()
        skill1.side_effect = lambda: asyncio.sleep(0.1)

        skill2 = AsyncMock()
        skill2.side_effect = lambda: asyncio.sleep(0.1)

        # Execute with parallelization
        orchestrator = SkillOrchestrator()
        start = time.time()
        await orchestrator.execute_parallel([skill1, skill2])
        elapsed = time.time() - start

        # Should take ~0.1s (parallel) not ~0.2s (serial)
        assert elapsed < 0.15
```

---

## Common Pitfalls & Fixes

### (MEDICINE + STEALTH Lenses)

#### Pitfall 1: Unregistered Constraints (STEALTH)

**Problem:** Constraint implemented, tested, but not registered in ConstraintManager.

```python
# BAD: Constraint exists but isn't used
class MyConstraint(SoftConstraint):
    pass

# In tests:
def test_my_constraint():
    constraint = MyConstraint()
    # Tests pass!

# In solver:
# ❌ MyConstraint never actually used because not in manager
```

**Fix:** Use constraint-preflight skill

```bash
# Before committing:
cd backend && python ../scripts/verify_constraints.py

# Should output:
# [OK] MyConstraint registered in ConstraintManager.create_default()
# [OK] MyConstraint registered in ConstraintManager.create_resilience_aware()
```

#### Pitfall 2: Race Conditions in Async Tests (SURVIVAL)

**Problem:** Async test doesn't wait for all operations to complete

```python
# BAD: Race condition
@pytest.mark.asyncio
async def test_create_and_list(db_session):
    await create_person(db_session, "Test")
    # ❌ Might not be flushed yet!
    people = await list_people(db_session)
    assert len(people) == 1  # Flaky!
```

**Fix:** Ensure commits before reading

```python
# GOOD: Explicit flush/commit
@pytest.mark.asyncio
async def test_create_and_list(db_session):
    await create_person(db_session, "Test")
    await db_session.commit()  # Or flush + refresh

    people = await list_people(db_session)
    assert len(people) == 1  # Reliable
```

#### Pitfall 3: Fixture Scope Mismatches (MEDICINE)

**Problem:** Fixture scope causes unexpected state sharing

```python
# BAD: Session-scope fixture modified by tests
@pytest.fixture(scope="session")
def shared_schedule(db):
    schedule = create_schedule(db)
    return schedule

def test_1_modifies_schedule(shared_schedule):
    shared_schedule.name = "Modified"
    db.commit()

def test_2_sees_modification(shared_schedule):
    # ❌ Gets modified version from test_1!
    assert shared_schedule.name == "Original"  # Fails
```

**Fix:** Use function scope for mutable objects

```python
# GOOD: Function scope ensures fresh data
@pytest.fixture(scope="function")
def fresh_schedule(db):
    schedule = create_schedule(db)
    yield schedule
    # Automatic cleanup after test

def test_1_modifies_schedule(fresh_schedule):
    fresh_schedule.name = "Modified"

def test_2_has_fresh_copy(fresh_schedule):
    assert fresh_schedule.name == "Original"  # Passes
```

#### Pitfall 4: Missing Type Hints (PERCEPTION)

**Problem:** Untyped code makes tests harder to write correctly

```python
# BAD: No types, unclear what's expected
def create_assignment(person, block):  # What types?
    return Assignment(person, block)

# Test is ambiguous:
def test_create_assignment():
    result = create_assignment("person-1", "2024-01-01")
    # ✓ String IDs? ✓ String dates?
    # ❌ Unclear, test is brittle
```

**Fix:** Add type hints everywhere

```python
# GOOD: Types make intent clear
def create_assignment(
    person: Person,
    block: Block
) -> Assignment:
    return Assignment(person_id=person.id, block_id=block.id)

# Test is explicit:
@pytest.mark.asyncio
async def test_create_assignment(
    db_session,
    person_factory,
    block_factory
):
    person = await person_factory()
    block = await block_factory()
    result = await create_assignment(person, block)
    assert isinstance(result, Assignment)
```

#### Pitfall 5: Hardcoded Test Data (INVESTIGATION)

**Problem:** Test data hardcoded makes tests fail when context changes

```python
# BAD: Hardcoded dates and IDs
def test_schedule_generation():
    schedule = generate_schedule(
        start_date="2024-01-01",  # Hardcoded!
        end_date="2024-12-31",
        program_id="abc-123"  # What if this doesn't exist?
    )
    assert schedule is not None
```

**Fix:** Use factories and date utilities

```python
# GOOD: Dynamic test data
from datetime import date, timedelta

@pytest.mark.asyncio
async def test_schedule_generation(
    db_session,
    program_factory,
):
    program = await program_factory()
    today = date.today()

    schedule = await generate_schedule(
        program_id=program.id,
        start_date=today,
        end_date=today + timedelta(days=365)
    )

    assert schedule.program_id == program.id
```

#### Pitfall 6: Incomplete Mock Setup (MEDICINE)

**Problem:** Mock missing required methods, causing AttributeError

```python
# BAD: Incomplete mock
mock_db = AsyncMock()
# Missing: execute, commit, rollback, flush...

@pytest.mark.asyncio
async def test_with_mock(mock_db):
    result = await service.get_all(mock_db)
    # ❌ AttributeError: 'AsyncMock' has no attribute 'execute'
```

**Fix:** Use spec or MagicMock chainability

```python
# GOOD: Mock with spec
from sqlalchemy.orm import AsyncSession

mock_db = AsyncMock(spec=AsyncSession)
mock_db.execute.return_value.scalars.return_value.all.return_value = []

# Or use MagicMock for chainable calls
mock_result = MagicMock()
mock_result.scalars.return_value.all.return_value = []
mock_db.execute.return_value = mock_result
```

#### Pitfall 7: Neglecting Error Cases (SURVIVAL)

**Problem:** Tests only check happy path, miss error scenarios

```python
# BAD: Only happy path tested
def test_validate_hours():
    result = validate_hours(40)
    assert result.is_valid  # ✓

def test_validate_hours_over_limit():
    # ❌ Never written! What if someone passes -1?
```

**Fix:** Test error cases explicitly

```python
# GOOD: Happy + sad paths
@pytest.mark.parametrize("hours,should_fail", [
    (80, False),   # Max allowed
    (81, True),    # Over limit
    (0, False),    # Min allowed
    (-1, True),    # Invalid
    (1000, True),  # Way over
])
def test_validate_hours(hours, should_fail):
    result = validate_hours(hours)
    assert result.is_valid != should_fail
```

---

## Quality Gates & Validation

### (INSIGHT + NATURE Lenses)

#### Pre-Commit Testing

**Before Every Commit:**

```bash
#!/bin/bash
# .git/hooks/pre-commit

set -e

echo "Running pre-commit checks..."

# 1. Backend tests
cd backend
pytest --tb=short -q
python ../scripts/verify_constraints.py

# 2. Frontend tests
cd ../frontend
npm run test:ci --silent

# 3. Linting
cd ../backend
ruff check app/
ruff format app/ --check

# 4. Type checking
mypy app/ --ignore-missing-imports 2>/dev/null || true

echo "✓ All checks passed"
```

#### Pre-PR Validation

**CI Workflow Completion Checklist:**

```yaml
# Must pass before PR merge
✅ ci.yml:backend-tests
   └─ pytest passes
   └─ coverage >= 70%

✅ ci.yml:frontend-tests
   └─ npm test passes
   └─ coverage >= 60%

✅ code-quality.yml
   └─ ruff lint: PASS
   └─ mypy type-check: PASS
   └─ prettier format: PASS

✅ security.yml
   └─ bandit: PASS
   └─ dependabot: PASS

✅ docs.yml
   └─ Link validation: PASS
   └─ API docs generated: PASS
```

#### Test Report Interpretation

**Coverage Report Example:**

```
Name                     Stmts   Miss  Cover   Missing
─────────────────────────────────────────────────────
app/services/swap.py       150     15    90%    45-50, 120-125
app/models/person.py       120     30    75%    40-70, 100-115
app/api/routes.py          200     50    75%    80-120
─────────────────────────────────────────────────────
TOTAL                     2450    350    85%

Lines not covered by tests:
- app/services/swap.py:45-50 - Rare edge case
- app/services/swap.py:120-125 - Error recovery path
- app/models/person.py:40-70 - Validation logic
```

**Action Items:**
1. Target missing lines in high-traffic code (services, models)
2. Use test-writer skill to generate tests for gaps
3. Review if missing lines are truly testable
4. Re-run coverage after adding tests

#### Flaky Test Detection

**Identifying Flaky Tests:**

```bash
# Run specific test multiple times
pytest --count=10 tests/test_swap_executor.py::test_execute_swap_success

# If fails on some runs:
# - Likely race condition
# - Likely insufficient mocking
# - Likely timing-dependent code
```

**Fix Flaky Tests:**

```python
# Pattern 1: Race condition
# BAD
@pytest.mark.asyncio
async def test_concurrent_swaps(db_session):
    await execute_swap_1()
    await execute_swap_2()  # Might execute first!
    results = await get_swaps()
    assert len(results) == 2  # ❌ Flaky

# GOOD
@pytest.mark.asyncio
async def test_concurrent_swaps(db_session):
    results = await asyncio.gather(
        execute_swap_1(),
        execute_swap_2()
    )
    assert len(results) == 2  # ✓ Deterministic

# Pattern 2: Missing flush
# BAD
def test_with_db(db_session):
    create_person(db_session, "Test")
    people = list_people(db_session)  # ❌ Not flushed

# GOOD
def test_with_db(db_session):
    create_person(db_session, "Test")
    db_session.flush()  # ✓ Explicit flush
    people = list_people(db_session)
```

---

## Testing Skills Themselves

### (RELIGION + STEALTH Lenses)

#### The Meta-Testing Problem

**Question:** How do we test that skills work correctly?

**Current State:**
- Skills are not unit tested
- Skills are validated by humans reviewing documentation
- Skills are indirectly tested through project operations
- No automated CI checks for skill correctness

**Proposed Solution:** Create skill test framework

#### Skill Testing Infrastructure

**Proposed Directory Structure:**

```
backend/tests/skills/
├── __init__.py
├── conftest.py                          # Shared skill test fixtures
├── test_acgme_compliance_skill.py       # Knowledge skill tests
├── test_code_review_skill.py
├── test_swap_execution_skill.py         # Workflow skill tests
├── test_compliance_validation_skill.py
├── test_test_writer_skill.py            # Framework skill tests
├── test_test_scenario_framework_skill.py
├── test_constraint_preflight_skill.py   # Development skill tests
├── test_automated_code_fixer_skill.py
├── test_mcp_integration.py              # MCP integration tests
├── test_skill_composition.py            # Multi-skill tests
└── fixtures/
    ├── skill_examples.py
    ├── test_data.py
    └── mock_services.py
```

#### Skill Test Fixture Pattern

```python
# backend/tests/skills/conftest.py

@pytest.fixture
def skill_context():
    """Provide context for skill testing."""
    return {
        "database": create_test_db(),
        "mcp_client": MockMCPClient(),
        "logger": logging.getLogger("test"),
        "config": SkillTestConfig(),
    }

@pytest.fixture
async def skill_with_context(skill_context):
    """Provide skill instance with full context."""
    class SkillEnvironment:
        def __init__(self, skill_class, context):
            self.skill = skill_class(**context)
            self.context = context

        async def execute(self, *args, **kwargs):
            return await self.skill.execute(*args, **kwargs)

    yield SkillEnvironment
```

#### Example: Testing a Knowledge Skill

```python
# backend/tests/skills/test_acgme_compliance_skill.py

@pytest.mark.skill
class TestACGMEComplianceSkill:
    """Tests for acgme-compliance knowledge skill."""

    def test_skill_documentation_exists(self):
        """Skill must have documentation."""
        skill_doc = read_skill_doc("acgme-compliance")
        assert skill_doc is not None
        assert len(skill_doc) > 100

    def test_acgme_80_hour_rule_documented(self):
        """80-hour rule must be documented accurately."""
        skill_doc = read_skill_doc("acgme-compliance")
        assert "80 hours" in skill_doc
        assert "4-week rolling average" in skill_doc or "rolling" in skill_doc

    def test_acgme_1_in_7_rule_documented(self):
        """1-in-7 rule must be documented."""
        skill_doc = read_skill_doc("acgme-compliance")
        assert "1-in-7" in skill_doc or "one 24-hour period off" in skill_doc

    def test_supervision_ratio_documented(self):
        """Supervision ratios must be documented."""
        skill_doc = read_skill_doc("acgme-compliance")
        # Should mention PGY-specific ratios
        assert "PGY" in skill_doc
        assert any(ratio in skill_doc for ratio in ["1:2", "1:4", "1:1"])

    def test_skill_examples_are_valid(self):
        """Examples in skill doc must be valid Python."""
        skill_doc = read_skill_doc("acgme-compliance")
        examples = extract_code_blocks(skill_doc)

        for example in examples:
            try:
                compile(example, '<skill_example>', 'exec')
            except SyntaxError as e:
                pytest.fail(f"Example has syntax error: {e}")

    def test_skill_provides_actionable_guidance(self):
        """Skill should provide specific, actionable advice."""
        skill_doc = read_skill_doc("acgme-compliance")

        # Should have practical examples
        assert "example" in skill_doc.lower()
        assert "how to" in skill_doc.lower() or "steps" in skill_doc.lower()
```

#### Example: Testing a Workflow Skill

```python
# backend/tests/skills/test_swap_execution_skill.py

@pytest.mark.skill
@pytest.mark.integration
class TestSwapExecutionSkill:
    """Tests for SWAP_EXECUTION workflow skill."""

    async def test_skill_orchestrates_swap_workflow(self, skill_context):
        """Skill should orchestrate complete swap workflow."""
        from app.skills.swap_execution import SwapExecutionWorkflow

        # Create test data
        swap = create_test_swap()

        # Execute skill workflow
        workflow = SwapExecutionWorkflow(skill_context)
        result = await workflow.execute_swap(swap)

        # Verify all phases executed
        assert result.safety_checks_passed
        assert result.audit_trail is not None
        assert result.rollback_capability is not None

    async def test_skill_safety_checks_work(self, skill_context):
        """Skill must validate swap safety."""
        from app.skills.swap_execution import SwapExecutionWorkflow

        # Create invalid swap
        invalid_swap = create_invalid_swap()

        workflow = SwapExecutionWorkflow(skill_context)
        result = await workflow.execute_swap(invalid_swap)

        # Should reject invalid swap
        assert not result.safety_checks_passed
        assert "ACGME" in str(result.error) or "violation" in str(result.error)

    async def test_skill_maintains_audit_trail(self, skill_context):
        """Skill must maintain complete audit trail."""
        from app.skills.swap_execution import SwapExecutionWorkflow

        swap = create_test_swap()
        workflow = SwapExecutionWorkflow(skill_context)
        result = await workflow.execute_swap(swap)

        # Audit trail should be complete
        assert "initiator" in result.audit_trail
        assert "timestamp" in result.audit_trail
        assert "before_state" in result.audit_trail
        assert "after_state" in result.audit_trail
```

#### Example: Testing a Framework Skill

```python
# backend/tests/skills/test_test_writer_skill.py

@pytest.mark.skill
class TestTestWriterSkill:
    """Tests for test-writer framework skill."""

    def test_generates_valid_pytest_syntax(self):
        """Generated tests must be valid Python."""
        from app.skills.test_writer import TestWriter

        source = """
        async def create_assignment(db, person_id, block_id):
            assignment = Assignment(person_id=person_id, block_id=block_id)
            db.add(assignment)
            await db.flush()
            return assignment
        """

        writer = TestWriter()
        tests = writer.generate_tests(source)

        # Must compile
        compile(tests, '<generated>', 'exec')

    def test_includes_happy_path(self):
        """Should include happy path test."""
        from app.skills.test_writer import TestWriter

        source = "def simple_function(x): return x * 2"

        writer = TestWriter()
        tests = writer.generate_tests(source)

        assert "def test_" in tests
        assert "simple_function" in tests
        assert "assert" in tests

    def test_includes_error_cases(self):
        """Should include error case tests."""
        from app.skills.test_writer import TestWriter

        source = """
        def divide(a, b):
            if b == 0:
                raise ValueError("Division by zero")
            return a / b
        """

        writer = TestWriter()
        tests = writer.generate_tests(source)

        # Should test error case
        assert "ValueError" in tests or "zero" in tests
        assert "pytest.raises" in tests or "with pytest" in tests
```

#### CI Integration for Skill Testing

**Proposed GitHub Actions Workflow:**

```yaml
# .github/workflows/skill-tests.yml
name: Skill Tests

on: [push, pull_request]

jobs:
  skill-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install backend dependencies
        run: pip install -r backend/requirements.txt

      - name: Run skill tests
        run: |
          cd backend
          pytest tests/skills/ -v --tb=short -m skill

      - name: Check skill documentation
        run: |
          python scripts/validate_skill_docs.py

      - name: Test MCP tool integration
        run: |
          cd backend
          pytest tests/skills/test_mcp_integration.py -v

      - name: Test skill composition
        run: |
          cd backend
          pytest tests/skills/test_skill_composition.py -v
```

---

## Final Recommendations

### (INSIGHT + INVESTIGATION Lenses)

#### Immediate Actions (Next 1 week)

1. **Create skill test framework**
   - [ ] Add `backend/tests/skills/` directory
   - [ ] Create skill test fixtures in `conftest.py`
   - [ ] Write example tests for 3 skills (code-review, test-writer, constraint-preflight)

2. **Document testing patterns**
   - [ ] Create `docs/testing/SKILL_TESTING.md`
   - [ ] Add examples for each skill type
   - [ ] Document MCP integration testing approach

3. **Add CI integration**
   - [ ] Create `.github/workflows/skill-tests.yml`
   - [ ] Add skill test job to main CI pipeline
   - [ ] Configure Codecov for skill tests

#### Short-term Improvements (2-4 weeks)

1. **Comprehensive skill coverage**
   - [ ] Write tests for all 15+ skills
   - [ ] Target 70%+ coverage on skill code
   - [ ] Add pre-flight validation in CI

2. **MCP tool validation**
   - [ ] Create tests for all 29+ MCP tools
   - [ ] Verify tool integration with skills
   - [ ] Test error handling paths

3. **Skill composition validation**
   - [ ] Test parallel skill execution
   - [ ] Test serialized skill execution
   - [ ] Test error handling in composition

#### Long-term Vision (1-3 months)

1. **Skill test automation**
   - [ ] Auto-generate test stubs from skill YAML
   - [ ] Generate test reports per skill
   - [ ] Track skill reliability over time

2. **Continuous quality monitoring**
   - [ ] Dashboard showing skill test results
   - [ ] Alerts for skill test failures
   - [ ] Historical trend analysis

3. **Skill certification program**
   - [ ] Define skill quality gates
   - [ ] Require tests before skill deployment
   - [ ] Track skill versioning and compatibility

---

## Appendix A: Testing Terminology

| Term | Definition |
|------|-----------|
| **Unit Test** | Tests single function/method in isolation |
| **Integration Test** | Tests multiple components working together |
| **E2E Test** | Tests complete user workflow end-to-end |
| **Scenario Test** | Tests complex business scenario with setup/validation |
| **Fixture** | Reusable test data/setup |
| **Mock** | Simulated object replacing real dependency |
| **Parametrize** | Run same test with multiple inputs |
| **Coverage** | % of code executed by tests |
| **Marker** | Tag for grouping/filtering tests |
| **Flaky Test** | Test that passes/fails inconsistently |

## Appendix B: Testing Tools Reference

| Tool | Purpose | Status |
|------|---------|--------|
| `pytest` | Python test framework | In use |
| `pytest-asyncio` | Async test support | In use |
| `pytest-cov` | Coverage reporting | In use |
| `pytest-xdist` | Parallel execution | Installed, not in CI |
| `jest` | JavaScript/TypeScript testing | In use |
| `@testing-library/react` | React testing | In use |
| `sqlalchemy` | ORM with test helpers | In use |
| `freezegun` | Mock time in tests | Available |
| `faker` | Generate test data | Available |
| `hypothesis` | Property-based testing | Not installed |

## Appendix C: Quick Command Reference

```bash
# Backend Testing
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific marker
pytest -m acgme
pytest -m integration
pytest -m "not slow"

# Run specific file
pytest tests/test_swap_executor.py

# Run matching pattern
pytest -k "test_execute_swap"

# Debug mode (drop to pdb on failure)
pytest --pdb

# Show print statements
pytest -s

# Parallel execution
pytest -n auto

# Frontend Testing
cd ../frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Watch mode
npm test -- --watch

# Single run (CI mode)
npm run test:ci
```

---

**Document Status:** COMPLETE
**Confidence Level:** HIGH (Based on comprehensive codebase analysis)
**Ready for:** Implementation, CI/CD integration, team documentation

