---
name: python-testing-patterns
description: Advanced pytest patterns for Python backend testing. Use when dealing with async tests, complex fixtures, mocking strategies, database testing, or debugging flaky tests. Complements test-writer with deeper patterns.
model_tier: sonnet
parallel_hints:
  can_parallel_with: [test-writer, coverage-reporter, code-review]
  must_serialize_with: []
  preferred_batch_size: 5
context_hints:
  max_file_context: 80
  compression_level: 1
  requires_git_context: true
  requires_db_context: false
escalation_triggers:
  - pattern: "production.*database"
    reason: "Production database access in tests requires human approval"
  - pattern: "flaky.*persist"
    reason: "Persistent flaky tests may need infrastructure changes"
  - keyword: ["external service", "infrastructure"]
    reason: "Test infrastructure changes need human review"
---

***REMOVED*** Python Testing Patterns Skill

Advanced pytest patterns and strategies for testing FastAPI applications with async SQLAlchemy, focusing on patterns beyond basic test generation.

***REMOVED******REMOVED*** When This Skill Activates

- Debugging flaky or failing tests
- Complex async testing scenarios
- Database transaction isolation issues
- Mocking external services
- Test performance optimization
- Fixture dependency management
- Parametrized test patterns

***REMOVED******REMOVED*** Project Test Structure

```
backend/tests/
├── conftest.py              ***REMOVED*** Shared fixtures
├── unit/                    ***REMOVED*** Pure unit tests
├── integration/             ***REMOVED*** Database integration tests
├── services/                ***REMOVED*** Service layer tests
├── api/                     ***REMOVED*** API endpoint tests
├── scheduling/              ***REMOVED*** Scheduling-specific tests
├── resilience/              ***REMOVED*** Resilience framework tests
└── performance/             ***REMOVED*** Performance benchmarks
```

***REMOVED******REMOVED*** Async Testing Patterns

***REMOVED******REMOVED******REMOVED*** Proper Async Test Setup

```python
***REMOVED*** conftest.py
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

***REMOVED*** Use pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create isolated database session per test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()
```

***REMOVED******REMOVED******REMOVED*** Async Context Managers in Tests

```python
@pytest.mark.asyncio
async def test_with_async_context():
    """Test async context manager behavior."""
    async with SomeAsyncResource() as resource:
        result = await resource.do_something()
        assert result is not None

***REMOVED*** Testing async generators
@pytest.mark.asyncio
async def test_async_generator():
    results = []
    async for item in async_data_stream():
        results.append(item)
    assert len(results) == expected_count
```

***REMOVED******REMOVED******REMOVED*** Concurrent Test Execution

```python
@pytest.mark.asyncio
async def test_concurrent_operations(db_session):
    """Test concurrent database operations."""
    import asyncio

    async def create_assignment(person_id: str):
        return await service.create_assignment(db_session, person_id=person_id)

    ***REMOVED*** Run concurrently
    results = await asyncio.gather(
        create_assignment("person-1"),
        create_assignment("person-2"),
        create_assignment("person-3"),
    )

    assert len(results) == 3
    assert all(r.id for r in results)
```

***REMOVED******REMOVED*** Fixture Patterns

***REMOVED******REMOVED******REMOVED*** Factory Fixtures

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
        person = Person(
            id=str(uuid4()),
            name=name,
            role=role,
            **kwargs
        )
        db_session.add(person)
        await db_session.flush()
        created.append(person)
        return person

    yield _create

    ***REMOVED*** Cleanup
    for person in created:
        await db_session.delete(person)

***REMOVED*** Usage
@pytest.mark.asyncio
async def test_with_factory(person_factory):
    resident = await person_factory(role="RESIDENT", pgy_level=1)
    faculty = await person_factory(role="FACULTY", name="Dr. Smith")

    assert resident.role == "RESIDENT"
    assert faculty.name == "Dr. Smith"
```

***REMOVED******REMOVED******REMOVED*** Fixture Composition

```python
@pytest.fixture
async def schedule_with_assignments(db_session, person_factory, block_factory):
    """Composite fixture with related entities."""
    ***REMOVED*** Create people
    residents = [
        await person_factory(name=f"Resident {i}", role="RESIDENT")
        for i in range(3)
    ]

    faculty = await person_factory(name="Faculty", role="FACULTY")

    ***REMOVED*** Create blocks
    blocks = [
        await block_factory(date=date.today() + timedelta(days=i))
        for i in range(7)
    ]

    ***REMOVED*** Create schedule
    schedule = Schedule(id=str(uuid4()), name="Test Schedule")
    db_session.add(schedule)

    ***REMOVED*** Create assignments
    for i, block in enumerate(blocks):
        assignment = Assignment(
            person_id=residents[i % len(residents)].id,
            block_id=block.id,
            schedule_id=schedule.id,
        )
        db_session.add(assignment)

    await db_session.flush()

    return {
        "schedule": schedule,
        "residents": residents,
        "faculty": faculty,
        "blocks": blocks,
    }
```

***REMOVED******REMOVED******REMOVED*** Scoped Fixtures for Performance

```python
***REMOVED*** Session-scoped for expensive setup
@pytest.fixture(scope="session")
async def db_engine():
    """Shared engine across all tests."""
    engine = create_async_engine(TEST_DATABASE_URL)
    yield engine
    await engine.dispose()

***REMOVED*** Module-scoped for related test groups
@pytest.fixture(scope="module")
async def seeded_database(db_engine):
    """Seed data once per module."""
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        ***REMOVED*** Seed common data
    yield
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

***REMOVED******REMOVED*** Mocking Patterns

***REMOVED******REMOVED******REMOVED*** AsyncMock for Async Functions

```python
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_with_async_mock():
    ***REMOVED*** Mock async function
    mock_fetch = AsyncMock(return_value={"data": "value"})

    with patch("app.services.external.fetch_data", mock_fetch):
        result = await service.process_data()

    mock_fetch.assert_called_once()
    assert result["data"] == "value"

***REMOVED*** Mock async context manager
@pytest.mark.asyncio
async def test_mock_async_context_manager():
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    async with mock_session as session:
        session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=expected_result)
        ))
```

***REMOVED******REMOVED******REMOVED*** Mocking Database Queries

```python
@pytest.mark.asyncio
async def test_service_with_mocked_db():
    """Test service without real database."""
    mock_db = AsyncMock(spec=AsyncSession)

    ***REMOVED*** Mock the query result chain
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Person(id="1", name="Test"),
    ]
    mock_db.execute.return_value = mock_result

    result = await person_service.get_all(mock_db)

    assert len(result) == 1
    mock_db.execute.assert_called_once()
```

***REMOVED******REMOVED******REMOVED*** Mocking External APIs

```python
import httpx
from unittest.mock import patch

@pytest.fixture
def mock_external_api():
    """Mock external API responses."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_response
        yield mock_get

@pytest.mark.asyncio
async def test_external_integration(mock_external_api):
    result = await integration_service.check_external_status()
    assert result["status"] == "ok"
```

***REMOVED******REMOVED******REMOVED*** Mocking datetime

```python
from freezegun import freeze_time
from datetime import datetime, date

@freeze_time("2024-06-15 10:00:00")
def test_date_dependent_logic():
    """Test logic that depends on current date."""
    result = get_current_block()
    assert result.date == date(2024, 6, 15)

***REMOVED*** Or with pytest-freezegun
@pytest.mark.freeze_time("2024-01-01")
async def test_new_year_logic():
    result = await calculate_yearly_stats()
    assert result.year == 2024
```

***REMOVED******REMOVED*** Database Testing Patterns

***REMOVED******REMOVED******REMOVED*** Transaction Isolation

```python
@pytest.fixture
async def isolated_transaction(db_session):
    """Ensure complete isolation with savepoints."""
    ***REMOVED*** Start a savepoint
    async with db_session.begin_nested():
        yield db_session
    ***REMOVED*** Automatically rolls back after test
```

***REMOVED******REMOVED******REMOVED*** Testing Constraints

```python
import pytest
from sqlalchemy.exc import IntegrityError

@pytest.mark.asyncio
async def test_unique_constraint(db_session):
    """Test database unique constraint."""
    person1 = Person(email="test@example.com")
    person2 = Person(email="test@example.com")  ***REMOVED*** Duplicate

    db_session.add(person1)
    await db_session.flush()

    db_session.add(person2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
```

***REMOVED******REMOVED******REMOVED*** Testing Cascade Deletes

```python
@pytest.mark.asyncio
async def test_cascade_delete(db_session, schedule_with_assignments):
    """Test that deleting schedule cascades to assignments."""
    schedule = schedule_with_assignments["schedule"]
    schedule_id = schedule.id

    ***REMOVED*** Count assignments before
    result = await db_session.execute(
        select(func.count()).where(Assignment.schedule_id == schedule_id)
    )
    before_count = result.scalar()
    assert before_count > 0

    ***REMOVED*** Delete schedule
    await db_session.delete(schedule)
    await db_session.flush()

    ***REMOVED*** Verify cascade
    result = await db_session.execute(
        select(func.count()).where(Assignment.schedule_id == schedule_id)
    )
    after_count = result.scalar()
    assert after_count == 0
```

***REMOVED******REMOVED*** Parametrized Testing

***REMOVED******REMOVED******REMOVED*** Basic Parametrization

```python
@pytest.mark.parametrize("hours,expected_valid", [
    (40, True),   ***REMOVED*** Normal week
    (80, True),   ***REMOVED*** Maximum allowed
    (81, False),  ***REMOVED*** Over limit
    (0, True),    ***REMOVED*** No hours
    (-1, False),  ***REMOVED*** Invalid negative
])
def test_weekly_hours_validation(hours, expected_valid):
    result = validate_weekly_hours(hours)
    assert result.is_valid == expected_valid
```

***REMOVED******REMOVED******REMOVED*** Parametrize with Fixtures

```python
@pytest.fixture(params=["RESIDENT", "FACULTY", "ADMIN"])
def role(request):
    """Parametrized fixture for user roles."""
    return request.param

@pytest.mark.asyncio
async def test_permission_by_role(db_session, role, person_factory):
    """Test runs once per role."""
    person = await person_factory(role=role)
    permissions = await get_permissions(person)

    if role == "ADMIN":
        assert "delete_schedule" in permissions
    else:
        assert "delete_schedule" not in permissions
```

***REMOVED******REMOVED******REMOVED*** Complex Parametrization

```python
@pytest.mark.parametrize("pgy_level,specialty,expected_ratio", [
    (1, "Internal Medicine", 2),  ***REMOVED*** PGY-1: 1:2 supervision
    (2, "Internal Medicine", 4),  ***REMOVED*** PGY-2: 1:4 supervision
    (3, "Surgery", 4),            ***REMOVED*** PGY-3: 1:4 supervision
    (1, "Critical Care", 1),      ***REMOVED*** ICU: 1:1 regardless of PGY
])
async def test_supervision_ratios(pgy_level, specialty, expected_ratio):
    """Test ACGME supervision ratio requirements."""
    ratio = calculate_supervision_ratio(pgy_level, specialty)
    assert ratio == expected_ratio
```

***REMOVED******REMOVED*** Debugging Flaky Tests

***REMOVED******REMOVED******REMOVED*** Identify Flakiness

```python
***REMOVED*** Run test multiple times
***REMOVED*** pytest --count=10 tests/test_flaky.py

***REMOVED*** Add timing information
@pytest.mark.asyncio
async def test_potentially_flaky(caplog):
    import time
    start = time.time()

    result = await some_async_operation()

    elapsed = time.time() - start
    caplog.info(f"Operation took {elapsed:.2f}s")

    assert result is not None
```

***REMOVED******REMOVED******REMOVED*** Fix Race Conditions

```python
***REMOVED*** BAD - Race condition
@pytest.mark.asyncio
async def test_race_condition():
    await service.create_item()
    items = await service.list_items()  ***REMOVED*** Might not see new item yet
    assert len(items) == 1

***REMOVED*** GOOD - Wait for consistency
@pytest.mark.asyncio
async def test_no_race_condition(db_session):
    await service.create_item(db_session)
    await db_session.commit()  ***REMOVED*** Ensure committed

    items = await service.list_items(db_session)
    assert len(items) == 1
```

***REMOVED******REMOVED******REMOVED*** Test Isolation Issues

```python
***REMOVED*** BAD - Shared state between tests
class TestWithSharedState:
    items = []  ***REMOVED*** Class-level state

    def test_add_item(self):
        self.items.append(1)
        assert len(self.items) == 1  ***REMOVED*** Fails if run after another test

***REMOVED*** GOOD - Fresh state per test
class TestWithIsolation:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.items = []

    def test_add_item(self):
        self.items.append(1)
        assert len(self.items) == 1  ***REMOVED*** Always works
```

***REMOVED******REMOVED*** Performance Testing

***REMOVED******REMOVED******REMOVED*** Benchmark Tests

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_schedule_generation_performance(db_session, benchmark_data):
    """Ensure schedule generation completes in reasonable time."""
    import time

    start = time.time()
    result = await generate_schedule(db_session, **benchmark_data)
    elapsed = time.time() - start

    assert result.is_valid
    assert elapsed < 5.0, f"Generation took {elapsed:.2f}s, expected < 5s"
```

***REMOVED******REMOVED******REMOVED*** Memory Profiling

```python
@pytest.mark.performance
def test_memory_usage():
    """Test that operation doesn't leak memory."""
    import tracemalloc

    tracemalloc.start()

    for _ in range(100):
        process_large_dataset()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    ***REMOVED*** Peak should be reasonable
    assert peak < 100 * 1024 * 1024, f"Peak memory: {peak / 1024 / 1024:.1f}MB"
```

***REMOVED******REMOVED*** Running Tests

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

***REMOVED*** Basic runs
pytest                                  ***REMOVED*** All tests
pytest -v                               ***REMOVED*** Verbose
pytest -x                               ***REMOVED*** Stop on first failure
pytest --tb=short                       ***REMOVED*** Short traceback

***REMOVED*** Filtering
pytest -k "test_swap"                   ***REMOVED*** Name matching
pytest -m "not slow"                    ***REMOVED*** Skip slow tests
pytest -m acgme                         ***REMOVED*** Only ACGME tests
pytest tests/services/                  ***REMOVED*** Specific directory

***REMOVED*** Debugging
pytest --pdb                            ***REMOVED*** Drop to debugger on failure
pytest --pdb-first                      ***REMOVED*** Debugger on first failure
pytest -s                               ***REMOVED*** Show print statements
pytest --capture=no                     ***REMOVED*** No output capture

***REMOVED*** Coverage
pytest --cov=app --cov-report=html      ***REMOVED*** HTML report
pytest --cov=app --cov-fail-under=70    ***REMOVED*** Fail if under 70%

***REMOVED*** Performance
pytest --durations=10                   ***REMOVED*** Show 10 slowest tests
pytest -n auto                          ***REMOVED*** Parallel execution (pytest-xdist)
```

***REMOVED******REMOVED*** Integration with Other Skills

***REMOVED******REMOVED******REMOVED*** With test-writer
- test-writer: generates basic test structure
- python-testing-patterns: handles complex scenarios, fixtures, debugging

***REMOVED******REMOVED******REMOVED*** With automated-code-fixer
When tests fail:
1. Analyze failure type (flaky, isolation, async)
2. Apply appropriate pattern fix
3. Verify with multiple runs

***REMOVED******REMOVED******REMOVED*** With systematic-debugger
For test debugging:
1. Use exploration phase to understand test state
2. Add strategic logging
3. Apply fix patterns from this skill

***REMOVED******REMOVED*** Escalation Rules

**Escalate to human when:**

1. Test requires production database access
2. Flaky test persists after isolation fixes
3. Performance benchmark thresholds unclear
4. Test infrastructure changes needed
5. External service mocking too complex
