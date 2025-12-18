# Testing

Testing strategies and commands.

---

## Backend Testing

```bash
cd backend

# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific file
pytest tests/test_schedule_service.py

# By marker
pytest -m acgme        # ACGME compliance
pytest -m unit         # Unit tests
pytest -m integration  # Integration tests
```

---

## Frontend Testing

```bash
cd frontend

# Unit tests
npm test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage

# E2E tests
npm run test:e2e

# E2E with UI
npm run test:e2e:ui
```

---

## Test Structure

### Backend

```
tests/
├── test_schedule_service.py
├── test_swap_service.py
├── test_notification_service.py  # 38 tests: send, bulk, schedule, preferences
├── test_health_routes.py         # 37 tests: health endpoints, error scenarios
├── test_absence_service.py       # 23 tests: CRUD, date filtering
├── test_assignment_service.py    # 22 tests: CRUD, ACGME validation
├── test_person_service.py        # 37 tests: CRUD, filtering
├── test_block_service.py         # 31 tests: CRUD, block generation
├── integration/
│   └── test_swap_workflow.py
└── conftest.py
```

### Frontend

```
__tests__/
├── features/
│   ├── analytics/           # 165 tests: MetricsCard, FairnessTrend, etc.
│   ├── audit/               # 264 tests: AuditLogTable, Timeline, etc.
│   └── swap-marketplace/    # 186 tests: SwapRequestCard, Filters, etc.
├── pages/
│   └── settings.test.tsx    # 53 tests: rendering, validation, accessibility
├── components/
└── setup.ts
```

---

## Test Categories

### Backend Test Files

| Test File | Tests | Coverage Area |
|-----------|-------|---------------|
| `test_notification_service.py` | 38 | Notification send, bulk, schedule, preferences |
| `test_health_routes.py` | 37 | Health endpoints, error handling, performance |
| `test_person_service.py` | 37 | Person CRUD, filtering by type/PGY/specialty |
| `test_block_service.py` | 31 | Block CRUD, generation, date filtering |
| `test_absence_service.py` | 23 | Absence CRUD, date range validation |
| `test_assignment_service.py` | 22 | Assignment CRUD, ACGME validation |

### Frontend Test Files

| Feature | Tests | Coverage Area |
|---------|-------|---------------|
| Analytics | 165 | MetricsCard, FairnessTrend, VersionComparison, WhatIfAnalysis |
| Audit | 264 | AuditLogTable, Filters, Export, Timeline, ChangeComparison |
| Swap Marketplace | 186 | SwapRequestCard, Filters, Form, MySwapRequests |
| Settings | 53 | Rendering, validation, save/update, error states |

---

## Running Specific Test Suites

### Backend

```bash
# Health check tests
pytest tests/test_health_routes.py -v

# Notification service tests
pytest tests/test_notification_service.py -v

# Service layer tests only
pytest tests/test_*_service.py -v

# With specific marker
pytest -m unit -v
pytest -m integration -v
```

### Frontend

```bash
# Analytics feature tests
npm test -- --testPathPattern="features/analytics"

# Settings page tests
npm test -- --testPathPattern="pages/settings"

# Swap marketplace tests
npm test -- --testPathPattern="swap-marketplace"

# All feature tests
npm test -- --testPathPattern="features"
```

---

## Coverage Requirements

- **Backend**: 70% minimum
- **Frontend**: 70% minimum

```bash
# Check coverage
pytest --cov=app --cov-fail-under=70
npm run test:coverage
```

---

## Load Testing

Comprehensive load testing infrastructure using k6 and pytest for performance validation.

### k6 Load Tests

```bash
cd load-tests

# Install dependencies
npm install

# Run smoke test (quick validation)
npm run test:smoke

# Run load test (50 VUs, 5 min)
npm run test:load

# Run stress test (200 VUs, 10 min)
npm run test:stress

# Run specific scenario
k6 run scenarios/schedule-generation.js
k6 run scenarios/concurrent-users.js
k6 run scenarios/api-baseline.js

# With custom options
k6 run --vus 50 --duration 5m scenarios/concurrent-users.js

# Docker execution
npm run test:docker:load
```

### pytest Performance Tests

```bash
cd backend

# Run all performance tests
pytest -m performance -v

# Run specific performance test suites
pytest tests/performance/test_acgme_load.py -v      # ACGME validation
pytest tests/performance/test_connection_pool.py -v  # DB connection pool
pytest tests/performance/test_idempotency_load.py -v # Idempotency

# Run resilience load tests
pytest tests/resilience/test_resilience_load.py -v

# Exclude slow tests
pytest -m "performance and not slow" -v
```

### Load Test Scenarios

| Scenario | Tool | Purpose | Target |
|----------|------|---------|--------|
| API Baseline | k6 | Establish latency baselines | p95 < 500ms |
| Concurrent Users | k6 | Multi-user simulation | 100 VUs |
| Schedule Generation | k6 | Stress test generation | p95 < 30s |
| Rate Limit Attack | k6 | Security validation | 429 in < 10 req |
| ACGME Performance | pytest | Compliance validation | 100 residents < 5s |
| Connection Pool | pytest | Pool saturation | No crashes |
| Idempotency | pytest | Duplicate prevention | 100 req → 1 record |

### Performance Test Markers

| Marker | Description |
|--------|-------------|
| `@pytest.mark.performance` | Performance-focused tests |
| `@pytest.mark.slow` | Long-running tests (> 30s) |
| `@pytest.mark.resilience` | Resilience framework tests |

### SLO Targets

| Metric | Normal | Under Load |
|--------|--------|------------|
| API P95 Latency | < 500ms | < 2s |
| Schedule Generation | < 180s | < 300s |
| ACGME Validation | < 2s | < 5s |
| Error Rate | < 0.1% | < 1% |

### Documentation

- **[Load Testing Guide](/docs/operations/LOAD_TESTING.md)** - Comprehensive guide
- **[Nginx Setup](/nginx/LOAD_TESTING_SETUP.md)** - Nginx configuration
- **[k6 README](/load-tests/README.md)** - k6 scenarios documentation

---

## Test Markers

Backend tests use pytest markers for categorization:

| Marker | Description |
|--------|-------------|
| `@pytest.mark.unit` | Isolated unit tests |
| `@pytest.mark.integration` | Tests with database interactions |
| `@pytest.mark.acgme` | ACGME compliance validation tests |
| `@pytest.mark.asyncio` | Async test methods |

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```
