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
