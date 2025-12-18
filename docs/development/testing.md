***REMOVED*** Testing

Testing strategies and commands.

---

***REMOVED******REMOVED*** Backend Testing

```bash
cd backend

***REMOVED*** Run all tests
pytest

***REMOVED*** With coverage
pytest --cov=app --cov-report=html

***REMOVED*** Specific file
pytest tests/test_schedule_service.py

***REMOVED*** By marker
pytest -m acgme        ***REMOVED*** ACGME compliance
pytest -m unit         ***REMOVED*** Unit tests
pytest -m integration  ***REMOVED*** Integration tests
```

---

***REMOVED******REMOVED*** Frontend Testing

```bash
cd frontend

***REMOVED*** Unit tests
npm test

***REMOVED*** Watch mode
npm run test:watch

***REMOVED*** Coverage
npm run test:coverage

***REMOVED*** E2E tests
npm run test:e2e

***REMOVED*** E2E with UI
npm run test:e2e:ui
```

---

***REMOVED******REMOVED*** Test Structure

***REMOVED******REMOVED******REMOVED*** Backend

```
tests/
├── test_schedule_service.py
├── test_swap_service.py
├── test_notification_service.py  ***REMOVED*** 38 tests: send, bulk, schedule, preferences
├── test_health_routes.py         ***REMOVED*** 37 tests: health endpoints, error scenarios
├── test_absence_service.py       ***REMOVED*** 23 tests: CRUD, date filtering
├── test_assignment_service.py    ***REMOVED*** 22 tests: CRUD, ACGME validation
├── test_person_service.py        ***REMOVED*** 37 tests: CRUD, filtering
├── test_block_service.py         ***REMOVED*** 31 tests: CRUD, block generation
├── integration/
│   └── test_swap_workflow.py
└── conftest.py
```

***REMOVED******REMOVED******REMOVED*** Frontend

```
__tests__/
├── features/
│   ├── analytics/           ***REMOVED*** 165 tests: MetricsCard, FairnessTrend, etc.
│   ├── audit/               ***REMOVED*** 264 tests: AuditLogTable, Timeline, etc.
│   └── swap-marketplace/    ***REMOVED*** 186 tests: SwapRequestCard, Filters, etc.
├── pages/
│   └── settings.test.tsx    ***REMOVED*** 53 tests: rendering, validation, accessibility
├── components/
└── setup.ts
```

---

***REMOVED******REMOVED*** Test Categories

***REMOVED******REMOVED******REMOVED*** Backend Test Files

| Test File | Tests | Coverage Area |
|-----------|-------|---------------|
| `test_notification_service.py` | 38 | Notification send, bulk, schedule, preferences |
| `test_health_routes.py` | 37 | Health endpoints, error handling, performance |
| `test_person_service.py` | 37 | Person CRUD, filtering by type/PGY/specialty |
| `test_block_service.py` | 31 | Block CRUD, generation, date filtering |
| `test_absence_service.py` | 23 | Absence CRUD, date range validation |
| `test_assignment_service.py` | 22 | Assignment CRUD, ACGME validation |

***REMOVED******REMOVED******REMOVED*** Frontend Test Files

| Feature | Tests | Coverage Area |
|---------|-------|---------------|
| Analytics | 165 | MetricsCard, FairnessTrend, VersionComparison, WhatIfAnalysis |
| Audit | 264 | AuditLogTable, Filters, Export, Timeline, ChangeComparison |
| Swap Marketplace | 186 | SwapRequestCard, Filters, Form, MySwapRequests |
| Settings | 53 | Rendering, validation, save/update, error states |

---

***REMOVED******REMOVED*** Running Specific Test Suites

***REMOVED******REMOVED******REMOVED*** Backend

```bash
***REMOVED*** Health check tests
pytest tests/test_health_routes.py -v

***REMOVED*** Notification service tests
pytest tests/test_notification_service.py -v

***REMOVED*** Service layer tests only
pytest tests/test_*_service.py -v

***REMOVED*** With specific marker
pytest -m unit -v
pytest -m integration -v
```

***REMOVED******REMOVED******REMOVED*** Frontend

```bash
***REMOVED*** Analytics feature tests
npm test -- --testPathPattern="features/analytics"

***REMOVED*** Settings page tests
npm test -- --testPathPattern="pages/settings"

***REMOVED*** Swap marketplace tests
npm test -- --testPathPattern="swap-marketplace"

***REMOVED*** All feature tests
npm test -- --testPathPattern="features"
```

---

***REMOVED******REMOVED*** Coverage Requirements

- **Backend**: 70% minimum
- **Frontend**: 70% minimum

```bash
***REMOVED*** Check coverage
pytest --cov=app --cov-fail-under=70
npm run test:coverage
```

---

***REMOVED******REMOVED*** Test Markers

Backend tests use pytest markers for categorization:

| Marker | Description |
|--------|-------------|
| `@pytest.mark.unit` | Isolated unit tests |
| `@pytest.mark.integration` | Tests with database interactions |
| `@pytest.mark.acgme` | ACGME compliance validation tests |
| `@pytest.mark.asyncio` | Async test methods |

```bash
***REMOVED*** Run only unit tests
pytest -m unit

***REMOVED*** Run only integration tests
pytest -m integration

***REMOVED*** Exclude slow tests
pytest -m "not slow"
```
