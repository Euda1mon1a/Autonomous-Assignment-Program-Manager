***REMOVED*** ADR-010: Pytest + Jest Testing Strategy

**Date:** 2024-12
**Status:** Adopted

***REMOVED******REMOVED*** Context

The Residency Scheduler handles critical medical data and scheduling decisions requiring:
- **High reliability**: Bugs in scheduling can impact patient care
- **Regulatory compliance**: ACGME violations must be prevented
- **Regression prevention**: Changes should not break existing functionality
- **Confidence in deployments**: Tests must validate system behavior
- **Documentation**: Tests serve as executable specifications

Medical safety-critical software requires comprehensive test coverage, but different components need different testing approaches.

***REMOVED******REMOVED*** Decision

Adopt a **multi-tiered testing strategy** with specialized tools:

***REMOVED******REMOVED******REMOVED*** Backend Testing: Pytest
- **Framework**: pytest with async support
- **Fixtures**: Comprehensive async fixtures for database, API clients
- **Coverage target**: 80% minimum, 90%+ for critical paths
- **Test types**: Unit, integration, performance, ACGME compliance

***REMOVED******REMOVED******REMOVED*** Frontend Testing: Jest + React Testing Library
- **Framework**: Jest for test runner
- **Component testing**: React Testing Library (not Enzyme)
- **E2E testing**: Playwright for end-to-end scenarios
- **Coverage target**: 80% minimum for components

***REMOVED******REMOVED******REMOVED*** Load Testing: k6 + pytest-benchmark
- **Tool**: k6 for HTTP load testing
- **Scenarios**: Baseline, concurrent users, schedule generation
- **Metrics**: p95 latency, throughput, error rate

***REMOVED******REMOVED*** Consequences

***REMOVED******REMOVED******REMOVED*** Positive
- **High confidence in deployments**: Comprehensive test coverage catches regressions
- **Regression detection**: Breaking changes caught by CI
- **Documentation via tests**: Tests demonstrate expected behavior
- **ACGME compliance validation**: Specialized tests ensure regulatory compliance
- **Performance baselines**: Load tests detect performance regressions
- **Faster debugging**: Tests isolate failing components

***REMOVED******REMOVED******REMOVED*** Negative
- **Test maintenance burden**: Tests require updates when features change
- **Slow CI**: Full test suite takes 5+ minutes
- **Async complexity**: Async fixtures and tests have learning curve
- **Flaky tests**: Timing issues in async tests require careful management
- **Coverage gaps**: High coverage doesn't guarantee correctness

***REMOVED******REMOVED*** Implementation

***REMOVED******REMOVED******REMOVED*** Backend Test Organization
```
backend/tests/
├── conftest.py              ***REMOVED*** Shared fixtures
├── unit/                    ***REMOVED*** Unit tests (if isolated)
├── integration/             ***REMOVED*** API integration tests
├── services/                ***REMOVED*** Service layer tests
├── scheduling/              ***REMOVED*** Scheduling engine tests
├── resilience/              ***REMOVED*** Resilience framework tests
├── performance/             ***REMOVED*** pytest-benchmark tests
└── test_acgme_compliance.py ***REMOVED*** ACGME validation tests
```

***REMOVED******REMOVED******REMOVED*** Pytest Fixtures
```python
***REMOVED*** conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.db.base import Base

@pytest.fixture(scope="session")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test_db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db(db_engine) -> AsyncSession:
    """Provide clean database session for each test."""
    async with AsyncSession(db_engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db):
    """Provide async HTTP client for API testing."""
    from httpx import AsyncClient
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

***REMOVED******REMOVED******REMOVED*** Backend Test Example
```python
***REMOVED*** tests/services/test_swap_executor.py
import pytest
from datetime import date
from app.services.swap_executor import SwapExecutor
from app.models.swap import SwapRequest, SwapType, SwapStatus

class TestSwapExecutor:
    """Test suite for swap execution logic."""

    @pytest.mark.asyncio
    async def test_execute_one_to_one_swap(self, db, swap_request):
        """Test successful execution of one-to-one swap."""
        executor = SwapExecutor()
        result = await executor.execute_swap(db, swap_request)

        assert result.status == "completed"
        assert result.executed_at is not None

        ***REMOVED*** Verify database state
        await db.refresh(swap_request)
        assert swap_request.status == SwapStatus.EXECUTED

    @pytest.mark.asyncio
    async def test_execute_swap_validation_failure(self, db, invalid_swap):
        """Test swap execution fails with ACGME violation."""
        executor = SwapExecutor()

        with pytest.raises(ValueError, match="ACGME violation"):
            await executor.execute_swap(db, invalid_swap)

    @pytest.mark.acgme
    async def test_swap_maintains_80_hour_rule(self, db, swap_request):
        """Test swap does not violate 80-hour work week rule."""
        executor = SwapExecutor()
        result = await executor.execute_swap(db, swap_request)

        ***REMOVED*** Verify both residents still under 80 hours
        for person_id in [swap_request.requester_id, swap_request.target_id]:
            hours = await self._calculate_weekly_hours(db, person_id)
            assert hours <= 80, f"Person {person_id} exceeds 80 hours"
```

***REMOVED******REMOVED******REMOVED*** Frontend Test Organization
```
frontend/
├── __tests__/
│   ├── components/          ***REMOVED*** Component tests
│   ├── pages/              ***REMOVED*** Page tests
│   └── integration/        ***REMOVED*** Integration tests
├── e2e/                    ***REMOVED*** Playwright E2E tests
└── jest.config.js
```

***REMOVED******REMOVED******REMOVED*** Frontend Component Test
```typescript
// __tests__/components/ScheduleList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ScheduleList } from '@/components/ScheduleList';

describe('ScheduleList', () => {
  it('renders schedules', async () => {
    const queryClient = new QueryClient();
    const mockSchedules = [
      { id: '1', name: 'Block 10', start_date: '2025-01-01' }
    ];

    render(
      <QueryClientProvider client={queryClient}>
        <ScheduleList initialData={mockSchedules} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Block 10')).toBeInTheDocument();
    });
  });

  it('handles loading state', () => {
    const queryClient = new QueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <ScheduleList initialData={[]} />
      </QueryClientProvider>
    );

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });
});
```

***REMOVED******REMOVED******REMOVED*** ACGME Compliance Tests
```python
***REMOVED*** tests/test_acgme_compliance.py
import pytest
from app.scheduling.acgme_validator import ACGMEValidator

@pytest.mark.acgme
class TestACGMECompliance:
    """Test suite for ACGME regulatory compliance."""

    async def test_80_hour_rule_validation(self, db, schedule):
        """Test 80-hour weekly limit enforcement."""
        validator = ACGMEValidator()
        result = await validator.validate_80_hour_rule(db, schedule)

        assert result.compliant, f"80-hour violations: {result.violations}"

    async def test_one_in_seven_rule(self, db, schedule):
        """Test 1-in-7 day off requirement."""
        validator = ACGMEValidator()
        result = await validator.validate_one_in_seven(db, schedule)

        assert result.compliant, f"1-in-7 violations: {result.violations}"

    async def test_supervision_ratios(self, db, schedule):
        """Test supervision ratio requirements."""
        validator = ACGMEValidator()
        result = await validator.validate_supervision_ratios(db, schedule)

        ***REMOVED*** PGY-1: 1 faculty per 2 residents
        ***REMOVED*** PGY-2/3: 1 faculty per 4 residents
        assert result.compliant, f"Ratio violations: {result.violations}"
```

***REMOVED******REMOVED******REMOVED*** Load Testing with k6
```javascript
// load-tests/scenarios/concurrent-users.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Ramp up to 10 users
    { duration: '3m', target: 50 },   // Ramp up to 50 users
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% under 500ms
    http_req_failed: ['rate<0.01'],   // Error rate < 1%
  },
};

export default function () {
  // Test schedule list endpoint
  const res = http.get('http://localhost:8000/api/schedules');

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);
}
```

***REMOVED******REMOVED******REMOVED*** Coverage Requirements

| Component | Coverage Target | Critical Paths |
|-----------|----------------|----------------|
| Backend Services | 80% minimum | 95%+ |
| API Routes | 80% minimum | 90%+ |
| ACGME Validation | 100% | 100% |
| Frontend Components | 80% minimum | N/A |
| Scheduling Engine | 90%+ | 100% |

***REMOVED******REMOVED******REMOVED*** Running Tests

```bash
***REMOVED*** Backend tests
cd backend
pytest                              ***REMOVED*** All tests
pytest --cov=app --cov-report=html  ***REMOVED*** With coverage
pytest -m acgme                     ***REMOVED*** ACGME tests only
pytest -v tests/services/           ***REMOVED*** Service layer only

***REMOVED*** Frontend tests
cd frontend
npm test                            ***REMOVED*** All tests
npm run test:coverage               ***REMOVED*** With coverage
npm run test:e2e                    ***REMOVED*** Playwright E2E

***REMOVED*** Load tests
cd load-tests
npm run test:smoke                  ***REMOVED*** Quick validation
npm run test:load                   ***REMOVED*** Full load test
k6 run scenarios/concurrent-users.js
```

***REMOVED******REMOVED*** References

- [pytest Documentation](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/react)
- [k6 Load Testing](https://k6.io/docs/)
- `backend/tests/conftest.py` - Shared pytest fixtures
- `frontend/jest.config.js` - Jest configuration
- `load-tests/` - k6 load testing scenarios
- `docs/development/TESTING_GUIDE.md` - Comprehensive testing guide
