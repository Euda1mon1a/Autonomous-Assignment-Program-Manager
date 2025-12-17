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
├── integration/
│   └── test_swap_workflow.py
└── conftest.py
```

***REMOVED******REMOVED******REMOVED*** Frontend

```
__tests__/
├── features/
│   ├── analytics/
│   └── swap-marketplace/
├── components/
└── setup.ts
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
