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
├── integration/
│   └── test_swap_workflow.py
└── conftest.py
```

### Frontend

```
__tests__/
├── features/
│   ├── analytics/
│   └── swap-marketplace/
├── components/
└── setup.ts
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
