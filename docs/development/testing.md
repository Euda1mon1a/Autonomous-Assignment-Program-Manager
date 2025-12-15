# Testing Guidelines

This document provides comprehensive testing guidelines for the Residency Scheduler project, covering backend, frontend, and end-to-end testing.

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Backend Testing](#backend-testing)
3. [Frontend Testing](#frontend-testing)
4. [End-to-End Testing](#end-to-end-testing)
5. [Test Coverage](#test-coverage)
6. [Best Practices](#best-practices)
7. [Continuous Integration](#continuous-integration)

---

## Testing Overview

### Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  ← Fewer, slower, more integrated
                    │  Tests  │
                    └────┬────┘
                         │
                   ┌─────┴─────┐
                   │Integration│  ← Medium count
                   │   Tests   │
                   └─────┬─────┘
                         │
              ┌──────────┴──────────┐
              │     Unit Tests      │  ← Many, fast, isolated
              │                     │
              └─────────────────────┘
```

### Testing Stack

| Layer | Backend | Frontend |
|-------|---------|----------|
| Unit | pytest | Jest |
| Integration | pytest + TestClient | Jest + MSW |
| E2E | - | Playwright |
| Mocking | unittest.mock | MSW |

### Test Categories

| Category | Marker/Location | Purpose |
|----------|-----------------|---------|
| Unit | `@pytest.mark.unit` | Test individual functions |
| Integration | `@pytest.mark.integration` | Test component interactions |
| ACGME | `@pytest.mark.acgme` | ACGME compliance tests |
| API | `test_*_api.py` | REST endpoint tests |
| Hooks | `__tests__/hooks/` | React Query hook tests |
| Components | `__tests__/components/` | React component tests |

---

## Backend Testing

### Setup

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Install test dependencies
pip install pytest pytest-cov pytest-asyncio
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_people_api.py

# Run specific test class
pytest tests/test_people_api.py::TestCreatePerson

# Run specific test method
pytest tests/test_people_api.py::TestCreatePerson::test_create_resident_success

# Run tests by marker
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests
pytest -m acgme          # ACGME compliance tests
pytest -m "not slow"     # Skip slow tests

# Run with coverage
pytest --cov=app --cov-report=html

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

### Test Configuration

The `pyproject.toml` contains pytest configuration:

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_functions = ["test_*"]
asyncio_mode = "auto"
addopts = ["-v", "--strict-markers", "-ra"]
markers = [
    "acgme: marks tests for ACGME compliance validation",
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
```

### Test Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def sample_resident(db):
    """Create a sample resident for testing."""
    from app.models import Person
    person = Person(
        name="Dr. Test Resident",
        email="test.resident@hospital.org",
        type="resident",
        pgy_level=2,
        is_active=True
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person

@pytest.fixture
def sample_faculty(db):
    """Create a sample faculty member for testing."""
    from app.models import Person
    person = Person(
        name="Dr. Test Faculty",
        email="test.faculty@hospital.org",
        type="faculty",
        is_active=True
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person
```

### Writing Backend Tests

#### API Tests

```python
# tests/test_people_api.py
import pytest
from fastapi.testclient import TestClient

class TestCreatePerson:
    """Tests for POST /api/people endpoint."""

    def test_create_resident_success(self, client: TestClient):
        """Should create a new resident with valid data."""
        payload = {
            "name": "Dr. New Resident",
            "email": "new.resident@hospital.org",
            "type": "resident",
            "pgy_level": 1,
        }

        response = client.post("/api/people", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["type"] == "resident"
        assert data["pgy_level"] == 1
        assert "id" in data

    def test_create_resident_missing_pgy_level(self, client: TestClient):
        """Should return 422 when creating resident without PGY level."""
        payload = {
            "name": "Dr. No PGY",
            "email": "no.pgy@hospital.org",
            "type": "resident",
            # pgy_level is missing
        }

        response = client.post("/api/people", json=payload)

        assert response.status_code == 422

    def test_create_faculty_success(self, client: TestClient):
        """Should create faculty member without PGY level."""
        payload = {
            "name": "Dr. Faculty Member",
            "email": "faculty@hospital.org",
            "type": "faculty",
        }

        response = client.post("/api/people", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "faculty"
        assert data["pgy_level"] is None

    def test_create_duplicate_email(self, client: TestClient, sample_resident):
        """Should return 400 when email already exists."""
        payload = {
            "name": "Duplicate Person",
            "email": sample_resident.email,  # Already exists
            "type": "resident",
            "pgy_level": 1,
        }

        response = client.post("/api/people", json=payload)

        assert response.status_code == 400
```

#### ACGME Compliance Tests

```python
# tests/test_constraints.py
import pytest
from datetime import date, timedelta
from app.scheduling.validator import ACGMEValidator
from app.models import Assignment, Block, Person

class TestACGMECompliance:
    """Tests for ACGME rule validation."""

    @pytest.fixture
    def validator(self):
        return ACGMEValidator()

    @pytest.mark.acgme
    def test_80_hour_rule_compliance(self, validator, db):
        """Should pass when resident works <= 80 hours/week average."""
        # Create test data with 70 hours/week
        assignments = self._create_assignments(hours_per_week=70)

        result = validator.validate_80_hour_rule(assignments)

        assert result.is_valid
        assert len(result.violations) == 0

    @pytest.mark.acgme
    def test_80_hour_rule_violation(self, validator, db):
        """Should fail when resident exceeds 80 hours/week average."""
        # Create test data with 90 hours/week
        assignments = self._create_assignments(hours_per_week=90)

        result = validator.validate_80_hour_rule(assignments)

        assert not result.is_valid
        assert len(result.violations) > 0
        assert result.violations[0].rule == "80_HOUR_RULE"

    @pytest.mark.acgme
    def test_one_in_seven_rule(self, validator, db):
        """Should validate one day off every 7 days."""
        # Create 7 consecutive working days
        assignments = self._create_consecutive_days(7)

        result = validator.validate_one_in_seven(assignments)

        assert not result.is_valid

    def _create_assignments(self, hours_per_week):
        """Helper to create test assignments."""
        # Implementation...
        pass

    def _create_consecutive_days(self, days):
        """Helper to create consecutive day assignments."""
        # Implementation...
        pass
```

#### Scheduling Engine Tests

```python
# tests/test_scheduling_engine.py
import pytest
from datetime import date, timedelta
from app.scheduling.engine import SchedulingEngine

class TestSchedulingEngine:
    """Tests for the scheduling engine."""

    @pytest.fixture
    def engine(self, db):
        return SchedulingEngine(db)

    def test_generate_schedule_basic(self, engine, sample_residents, sample_blocks):
        """Should generate a valid schedule."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)

        result = engine.generate_schedule(start_date, end_date)

        assert result is not None
        assert len(result.assignments) > 0
        assert all(a.person_id is not None for a in result.assignments)

    def test_respects_absences(self, engine, sample_resident, sample_absence):
        """Should not assign people during their absences."""
        start_date = sample_absence.start_date
        end_date = sample_absence.end_date

        result = engine.generate_schedule(start_date, end_date)

        # Verify no assignments for the absent person
        absent_assignments = [
            a for a in result.assignments
            if a.person_id == sample_resident.id
        ]
        assert len(absent_assignments) == 0

    def test_acgme_compliance(self, engine, sample_residents, sample_blocks):
        """Generated schedule should be ACGME compliant."""
        result = engine.generate_schedule(
            date(2024, 1, 1),
            date(2024, 1, 31)
        )

        # Should have no critical violations
        critical_violations = [
            v for v in result.violations
            if v.severity == "critical"
        ]
        assert len(critical_violations) == 0
```

---

## Frontend Testing

### Setup

```bash
cd frontend

# Install dependencies (includes test dependencies)
npm install
```

### Running Tests

```bash
# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- usePeople.test.ts

# Run tests matching pattern
npm test -- --testPathPattern="hooks"

# Update snapshots
npm test -- -u
```

### Test Configuration

Jest configuration in `jest.config.js` or `package.json`:

```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
};
```

### Mocking API Calls

Tests mock the API module:

```typescript
// __tests__/hooks/usePeople.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { usePeople, useCreatePerson } from '@/lib/hooks';
import { get, post } from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  del: jest.fn(),
}));

const mockGet = get as jest.MockedFunction<typeof get>;
const mockPost = post as jest.MockedFunction<typeof post>;

// Test data
const mockPeople = {
  items: [
    { id: 1, name: 'Dr. Smith', type: 'resident', pgy_level: 2 },
    { id: 2, name: 'Dr. Jones', type: 'faculty', pgy_level: null },
  ],
  total: 2,
  page: 1,
  size: 10,
};

// Create wrapper with fresh QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('usePeople', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch people data successfully', async () => {
    mockGet.mockResolvedValueOnce(mockPeople);

    const { result } = renderHook(() => usePeople(), {
      wrapper: createWrapper(),
    });

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    // Wait for success
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(2);
    expect(mockGet).toHaveBeenCalledWith('/api/people', expect.any(Object));
  });

  it('should handle fetch error', async () => {
    const error = new Error('Network error');
    mockGet.mockRejectedValueOnce(error);

    const { result } = renderHook(() => usePeople(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeDefined();
  });
});

describe('useCreatePerson', () => {
  it('should create a person successfully', async () => {
    const newPerson = { name: 'Dr. New', type: 'resident', pgy_level: 1 };
    const createdPerson = { id: 3, ...newPerson };

    mockPost.mockResolvedValueOnce(createdPerson);

    const { result } = renderHook(() => useCreatePerson(), {
      wrapper: createWrapper(),
    });

    // Execute mutation
    result.current.mutate(newPerson);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/api/people', newPerson);
    expect(result.current.data).toEqual(createdPerson);
  });
});
```

### Component Tests

```typescript
// __tests__/components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/ui/Button';

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>);

    expect(screen.getByRole('button')).toHaveTextContent('Click me');
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies variant classes', () => {
    render(<Button variant="danger">Delete</Button>);

    expect(screen.getByRole('button')).toHaveClass('bg-red-500');
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>);

    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

---

## End-to-End Testing

### Setup

```bash
cd frontend

# Install Playwright browsers
npx playwright install
```

### Running E2E Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run with browser UI
npm run test:e2e:ui

# Run specific test file
npx playwright test e2e/login.spec.ts

# Run in headed mode (see browser)
npx playwright test --headed

# Run with specific browser
npx playwright test --project=chromium
```

### E2E Test Example

```typescript
// e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Login', () => {
  test('should login successfully with valid credentials', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    // Fill in credentials
    await page.fill('[name="email"]', 'admin@hospital.org');
    await page.fill('[name="password"]', 'password123');

    // Submit form
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[name="email"]', 'wrong@email.com');
    await page.fill('[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('.error-message')).toBeVisible();
  });
});

test.describe('Schedule', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[name="email"]', 'admin@hospital.org');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
  });

  test('should generate a new schedule', async ({ page }) => {
    await page.goto('/schedule');

    // Click generate button
    await page.click('button:has-text("Generate Schedule")');

    // Fill in date range
    await page.fill('[name="startDate"]', '2024-01-01');
    await page.fill('[name="endDate"]', '2024-01-31');

    // Submit
    await page.click('button:has-text("Generate")');

    // Wait for success
    await expect(page.locator('.schedule-grid')).toBeVisible();
  });
});
```

---

## Test Coverage

### Coverage Requirements

| Component | Minimum Coverage |
|-----------|------------------|
| Backend API Routes | 80% |
| Backend Scheduling | 90% |
| Backend Models | 70% |
| Frontend Hooks | 80% |
| Frontend Components | 60% |

### Generating Coverage Reports

**Backend:**
```bash
cd backend
pytest --cov=app --cov-report=html --cov-report=xml

# View HTML report
open htmlcov/index.html
```

**Frontend:**
```bash
cd frontend
npm run test:coverage

# View HTML report
open coverage/lcov-report/index.html
```

### Coverage Configuration

**Backend (`pyproject.toml`):**
```toml
[tool.coverage.run]
source = ["app"]
branch = true
omit = ["*/tests/*", "*/__pycache__/*", "*/alembic/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
fail_under = 70
```

**Frontend (`jest.config.js`):**
```javascript
coverageThreshold: {
  global: {
    branches: 70,
    functions: 70,
    lines: 70,
    statements: 70,
  },
},
```

---

## Best Practices

### Test Structure

Use the **Arrange-Act-Assert** pattern:

```python
def test_create_person():
    # Arrange
    payload = {"name": "Dr. Test", "email": "test@hospital.org", "type": "resident", "pgy_level": 1}

    # Act
    response = client.post("/api/people", json=payload)

    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == "Dr. Test"
```

### Naming Conventions

Use descriptive test names:

```python
# Good
def test_create_resident_missing_pgy_level_returns_422():
    ...

def test_schedule_generation_respects_absence_dates():
    ...

# Bad
def test_create_1():
    ...

def test_it_works():
    ...
```

### Test Independence

Each test should:
- Run independently
- Not depend on test order
- Clean up after itself
- Not share mutable state

### What to Test

**DO test:**
- Business logic
- API endpoints
- Edge cases
- Error handling
- ACGME compliance rules

**DON'T test:**
- Framework code
- External libraries
- Database queries directly
- Implementation details

### Mocking Guidelines

- Mock external services
- Mock at the boundary (API calls, database)
- Don't mock internal implementation
- Use fixtures for common test data

---

## Continuous Integration

### CI Pipeline

Tests run automatically on:
- Pull requests to `main`
- Pushes to `main`

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3
        with:
          files: backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage --watchAll=false
      - uses: codecov/codecov-action@v3
        with:
          files: frontend/coverage/lcov.info

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
          npx playwright install --with-deps
      - name: Start services
        run: docker-compose up -d
      - name: Run E2E tests
        run: |
          cd frontend
          npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

---

## Troubleshooting

### Common Issues

**Backend: Import errors**
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
```

**Frontend: Module not found**
```bash
npm test -- --clearCache
```

**E2E: Timeout errors**
```typescript
test.setTimeout(60000); // 60 seconds
```

**Flaky tests**
- Check for race conditions
- Use proper `waitFor` assertions
- Avoid hardcoded delays

---

*Last Updated: December 2024*
