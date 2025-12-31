# Test Engineer Agent - Prompt Templates

> **Role:** Test strategy, automation, quality assurance, performance testing
> **Model:** Claude Opus 4.5
> **Mission:** Ensure comprehensive test coverage and quality

## 1. TEST STRATEGY TEMPLATE

```
**TEST STRATEGY:** ${FEATURE_OR_COMPONENT}

**TEST PYRAMID:**
```
     / \
    / E2E \       5-10% (Slow, expensive)
   /-------\
  /Integration\  20-30% (Moderate speed)
 /-----------\
/   Unit     \ 60-70% (Fast, cheap)
/=============\
\`\`\`

**UNIT TESTS (70%):**
- Service business logic
- Utility functions
- Error handling
- Edge cases

**INTEGRATION TESTS (25%):**
- API endpoints
- Database operations
- External integrations
- Component interactions

**E2E TESTS (5%):**
- Critical user flows
- Cross-system workflows
- Performance baselines

**COVERAGE TARGET:** 80%+

Define test strategy comprehensively.
```

## 2. UNIT TEST TEMPLATE

```
**UNIT TEST:** ${FUNCTION_OR_CLASS}

**TEST FILE:**
Location: `backend/tests/unit/services/test_${service_name}.py`

**IMPLEMENTATION:**
\`\`\`python
import pytest
from app.services.${service} import ${Function}

class Test${Function}:
    """Test suite for ${Function}."""

    @pytest.fixture
    def setup(self):
        """Test setup."""
        return {
            'input': ${INPUT},
            'expected': ${EXPECTED}
        }

    async def test_happy_path(self, setup):
        """Test normal execution path."""
        result = await ${Function}(setup['input'])
        assert result == setup['expected']

    async def test_edge_case_${case1}(self):
        """Test edge case: ${case1}."""
        result = await ${Function}(${EDGE_INPUT})
        assert ${ASSERTION}

    async def test_error_handling_${error1}(self):
        """Test error: ${error1}."""
        with pytest.raises(${ErrorType}):
            await ${Function}(${ERROR_INPUT})

    async def test_boundary_condition(self):
        """Test boundary conditions."""
        # Min value
        result = await ${Function}(0)
        assert ${ASSERTION}

        # Max value
        result = await ${Function}(100)
        assert ${ASSERTION}
\`\`\`

**TEST EXECUTION:**
\`\`\`bash
pytest tests/unit/services/test_${service}.py -v
\`\`\`

Write comprehensive unit tests.
```

## 3. INTEGRATION TEST TEMPLATE

```
**INTEGRATION TEST:** ${API_ENDPOINT}

**TEST FILE:**
Location: `backend/tests/integration/test_${endpoint}.py`

**DATABASE SETUP:**
\`\`\`python
import pytest
from httpx import AsyncClient
from app.main import app
from app.db.base import Base
from tests.conftest import async_session

@pytest.mark.asyncio
class TestScheduleAPI:
    """Integration tests for Schedule API."""

    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    async def db(self):
        """Create test database."""
        # Setup
        async with async_session() as session:
            async with session.begin():
                # Create test data
                pass
            yield session

    async def test_get_schedule_success(self, client, db):
        """Test GET /schedules/{id} returns schedule."""
        # Create test data
        schedule = await create_test_schedule(db)

        # Make request
        response = await client.get(f"/api/v1/schedules/{schedule.id}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['data']['id'] == str(schedule.id)

    async def test_create_schedule_validation(self, client):
        """Test POST /schedules with invalid data."""
        response = await client.post("/api/v1/schedules", json={})

        assert response.status_code == 422
        assert 'detail' in response.json()

    async def test_update_schedule_acgme_compliance(self, client, db):
        """Test schedule update validates ACGME rules."""
        schedule = await create_test_schedule(db)

        response = await client.patch(
            f"/api/v1/schedules/{schedule.id}",
            json={'hours_per_week': 95}  # Violates 80-hour rule
        )

        assert response.status_code == 400
        assert 'ACGME' in response.json()['detail']
\`\`\`

**TEST EXECUTION:**
\`\`\`bash
pytest tests/integration/test_schedule.py -v
\`\`\`

Write integration tests for all endpoints.
```

## 4. MOCK & FIXTURE TEMPLATE

```
**FIXTURES & MOCKS**

**conftest.py:**
Location: `backend/tests/conftest.py`

\`\`\`python
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def db():
    """Provide test database session."""
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

@pytest.fixture
def mock_external_api():
    """Mock external API calls."""
    with patch('app.services.external.api_call') as mock:
        mock.return_value = AsyncMock(return_value={'status': 'ok'})
        yield mock

@pytest.fixture
async def test_user(db):
    """Create test user."""
    user = User(id='test-user', email='test@example.com')
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user

@pytest.fixture
async def test_schedule(db, test_user):
    """Create test schedule."""
    schedule = Schedule(
        id='schedule-1',
        created_by=test_user.id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365)
    )
    db.add(schedule)
    await db.flush()
    await db.refresh(schedule)
    return schedule
\`\`\`

**FACTORY PATTERN (Alternative):**
\`\`\`python
from factory import Factory, AsyncFactory

class UserFactory(AsyncFactory):
    class Meta:
        model = User

    id = factory.Faker('uuid4')
    email = factory.Faker('email')

class ScheduleFactory(AsyncFactory):
    class Meta:
        model = Schedule

    id = factory.Faker('uuid4')
    created_by = SubFactory(UserFactory)
\`\`\`

Create reusable fixtures and mocks.
```

## 5. PERFORMANCE TEST TEMPLATE

```
**PERFORMANCE TEST:** ${TEST_NAME}

**PYTEST PERFORMANCE:**
Location: `backend/tests/performance/test_${component}.py`

\`\`\`python
import pytest
import time
from tests.conftest import create_test_data

@pytest.mark.performance
class TestScheduleGenerationPerformance:
    """Performance tests for schedule generation."""

    async def test_generate_schedule_performance(self, db):
        """Measure schedule generation time."""
        # Setup large dataset
        personnel = await create_test_data(db, count=100)

        # Measure
        start = time.perf_counter()
        schedule = await generate_schedule(db, personnel)
        duration = time.perf_counter() - start

        # Assert performance target
        assert duration < 5.0, f"Schedule generation took {duration}s (target: < 5s)"

    async def test_query_performance_n1(self, db):
        """Ensure no N+1 query problems."""
        schedules = await list_schedules(db, limit=100)

        # Use query counter
        with count_queries(db) as counter:
            for schedule in schedules:
                _ = schedule.personnel  # Access relationship

        # Should not increase query count per item
        assert counter.count < 10, f"N+1 detected: {counter.count} queries"

    @pytest.mark.benchmark
    def test_acgme_validation_speed(self, benchmark):
        """Benchmark ACGME compliance check."""
        schedule_data = ${SAMPLE_DATA}

        result = benchmark(validate_acgme_compliance, schedule_data)
        assert result['compliant'] == True
\`\`\`

**K6 LOAD TESTING:**
Location: `load-tests/scenarios/${scenario}.js`

\`\`\`javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '1m', target: 10 },
    { duration: '5m', target: 100 },
    { duration: '1m', target: 0 }
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.1']
  }
};

export default function () {
  let response = http.get('http://localhost:8000/api/v1/schedules');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500
  });
  sleep(1);
}
\`\`\`

Write performance tests.
```

## 6. ACGME COMPLIANCE TEST TEMPLATE

```
**ACGME COMPLIANCE TEST**

**TEST FILE:**
Location: `backend/tests/compliance/test_acgme.py`

\`\`\`python
import pytest
from app.scheduling.acgme_validator import ACGMEValidator

class TestACGMECompliance:
    """ACGME compliance tests."""

    @pytest.fixture
    def validator(self):
        return ACGMEValidator()

    async def test_80_hour_rule_compliant(self, validator):
        """Test schedule complies with 80-hour rule."""
        schedule = create_test_schedule(hours_per_week=75)
        result = await validator.validate_80_hour_rule(schedule)
        assert result['compliant'] == True

    async def test_80_hour_rule_violation(self, validator):
        """Test schedule violates 80-hour rule."""
        schedule = create_test_schedule(hours_per_week=90)
        result = await validator.validate_80_hour_rule(schedule)
        assert result['compliant'] == False
        assert result['violation_count'] == 1

    async def test_1_in_7_rule(self, validator):
        """Test 1-in-7 rule enforcement."""
        schedule = create_schedule_without_days_off()
        result = await validator.validate_1_in_7_rule(schedule)
        assert result['compliant'] == False

    async def test_supervision_ratio_pgy1(self, validator):
        """Test supervision ratio for PGY-1."""
        # 1 faculty per 2 residents
        schedule = create_schedule(
            pgy1_residents=4,
            supervising_faculty=2
        )
        result = await validator.validate_supervision_ratio(schedule)
        assert result['compliant'] == True

    async def test_combined_compliance(self, validator):
        """Test all ACGME rules together."""
        schedule = create_compliant_schedule()
        result = await validator.validate_all(schedule)
        assert result['compliant'] == True
        assert result['violations'] == []
\`\`\`

Write ACGME-specific compliance tests.
```

## 7. ERROR SCENARIO TEST TEMPLATE

```
**ERROR SCENARIO TESTS**

\`\`\`python
class TestErrorScenarios:
    """Test error handling and recovery."""

    async def test_database_connection_error(self):
        """Test graceful handling of DB connection failure."""
        with patch('app.db.session') as mock_db:
            mock_db.execute.side_effect = ConnectionError()

            with pytest.raises(Exception):
                await service.get_data()

    async def test_validation_error_response(self):
        """Test validation error response format."""
        response = await client.post("/api/v1/items", json={})

        assert response.status_code == 422
        data = response.json()
        assert 'detail' in data
        assert isinstance(data['detail'], list)

    async def test_race_condition_handling(self, db):
        """Test concurrent updates are handled safely."""
        # Simulate race condition
        tasks = [
            update_resource(db, resource_id, {'status': 'A'}),
            update_resource(db, resource_id, {'status': 'B'})
        ]

        results = await asyncio.gather(*tasks)
        # Only one update should succeed
        final_state = await db.get(resource_id)
        assert final_state.status in ['A', 'B']

    async def test_timeout_handling(self):
        """Test timeout handling."""
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError):
            with pytest.raises(TimeoutError):
                await long_operation()
\`\`\`

Test error scenarios thoroughly.
```

## 8. STATUS REPORT TEMPLATE

```
**TEST ENGINEER STATUS REPORT**

**TEST COVERAGE:**
- Overall: ${OVERALL_COVERAGE}%
- Backend: ${BACKEND_COVERAGE}%
- Frontend: ${FRONTEND_COVERAGE}%
- Critical paths: ${CRITICAL_COVERAGE}%

**TEST EXECUTION:**
- Unit tests: ${UNIT_TESTS} (avg ${UNIT_TIME}ms)
- Integration tests: ${INTEGRATION_TESTS} (avg ${INT_TIME}ms)
- E2E tests: ${E2E_TESTS} (avg ${E2E_TIME}ms)
- Pass rate: ${PASS_RATE}%

**AUTOMATION:**
- CI/CD: ${CI_STATUS}
- Pre-commit hooks: ${HOOKS_STATUS}
- Automated reporting: ${REPORTING_STATUS}

**ISSUES:**
${ISSUES}

**NEXT:** ${NEXT_GOALS}
```

---

*Last Updated: 2025-12-31*
*Agent: Test Engineer*
*Version: 1.0*
