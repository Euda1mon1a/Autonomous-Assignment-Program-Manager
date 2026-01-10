# Post-Test Coverage Hook

**Trigger:** Before committing code changes to backend or frontend

---

## Purpose

Ensure test coverage is maintained by:
- Verifying test files exist for changed code
- Reminding developers to run coverage checks
- Providing clear thresholds and commands
- Optionally running full coverage validation

---

## Quick Reference

### Coverage Thresholds

| Component | Local Minimum | CI Minimum | Notes |
|-----------|---------------|------------|-------|
| **Backend (Python)** | 70% | 80% | CI is stricter |
| **Frontend (TypeScript)** | 60% | 70% | CI is stricter |

### Run Coverage Locally

**Backend (pytest + coverage):**
```bash
cd backend
pytest --cov=app --cov-report=term-missing --cov-report=html
# Open htmlcov/index.html for detailed report
```

**Frontend (Jest):**
```bash
cd frontend
npm run test:coverage
# Open coverage/lcov-report/index.html for detailed report
```

### Run Full Coverage Check at Commit Time

```bash
# Set environment variable to enable full check
COVERAGE_FULL=1 git commit -m "your message"
```

---

## What the Hook Checks

### Check 1: Backend Test File Existence (WARNING)

For each changed Python file in `backend/app/`:
- Looks for corresponding `test_*.py` in `backend/tests/`
- Warns if no obvious test file exists

**Example:**
```
Changed: backend/app/services/scheduling.py
Looking for: backend/tests/test_scheduling.py
            backend/tests/services/test_scheduling.py
```

### Check 2: Frontend Test File Existence (WARNING)

For each changed TypeScript file in `frontend/src/`:
- Looks for corresponding `*.test.ts(x)` file
- Checks `__tests__/` subdirectory pattern

**Example:**
```
Changed: frontend/src/components/Calendar.tsx
Looking for: frontend/src/components/__tests__/Calendar.test.tsx
            frontend/src/components/Calendar.test.tsx
```

### Check 3: Test Command Reminder (INFO)

When code files are staged, displays:
```
Remember to run tests before push:
  cd backend && pytest --cov=app --cov-report=term-missing
  cd frontend && npm test:coverage
```

### Check 4: Optional Full Coverage Run

With `COVERAGE_FULL=1`:
- Runs full test suite with coverage
- Fails if below threshold (70% backend, 60% frontend)
- Blocks commit on failure

---

## How to Improve Coverage

### 1. Identify Uncovered Lines

```bash
# Backend: terminal report shows missing lines
cd backend
pytest --cov=app --cov-report=term-missing

# Output shows:
# Name                                 Stmts   Miss  Cover   Missing
# -----------------------------------------------------------------
# app/services/scheduling.py             100     15    85%   45-52, 78-84
```

```bash
# Frontend: generate HTML report
cd frontend
npm run test:coverage
# Open coverage/lcov-report/index.html
```

### 2. Write Targeted Tests

Focus on:
1. **Uncovered functions** - Functions with 0% coverage
2. **Edge cases** - Error paths, boundary conditions
3. **Critical paths** - Business logic, validation

### 3. Use Test Markers

**Backend (pytest markers):**
```python
@pytest.mark.unit
def test_quick_validation():
    ...

@pytest.mark.integration
def test_database_operation():
    ...

@pytest.mark.slow
def test_large_schedule_generation():
    ...
```

**Frontend (Jest describe blocks):**
```typescript
describe('Unit: Calendar component', () => {
    it('renders correctly', () => { ... });
});

describe('Integration: Calendar with API', () => {
    it('fetches and displays events', () => { ... });
});
```

---

## CI/CD Coverage Enforcement

### GitHub Actions Workflow

**File:** `.github/workflows/quality-gates.yml`

**Backend validation (lines 298-317):**
```yaml
- name: Check Backend Coverage
  run: |
    COVERAGE=$(python -c "import xml.etree.ElementTree as ET; ...")
    if (( $(echo "$COVERAGE < $COVERAGE_THRESHOLD_BACKEND" | bc -l) )); then
      echo "Coverage $COVERAGE% below threshold $COVERAGE_THRESHOLD_BACKEND%"
      exit 1
    fi
```

**Frontend validation (lines 375-396):**
```yaml
- name: Check Frontend Coverage
  run: |
    COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
    if (( $(echo "$COVERAGE < $COVERAGE_THRESHOLD_FRONTEND" | bc -l) )); then
      echo "Coverage $COVERAGE% below threshold $COVERAGE_THRESHOLD_FRONTEND%"
      exit 1
    fi
```

### Codecov Integration

Coverage reports are uploaded to Codecov for:
- Historical tracking
- PR comments showing coverage delta
- Coverage badges

---

## Test File Conventions

### Backend (pytest)

```
backend/
├── app/
│   ├── services/
│   │   └── scheduling.py        # Source file
│   ├── models/
│   │   └── person.py            # Source file
│   └── api/
│       └── routes/
│           └── schedule.py      # Source file
└── tests/
    ├── test_scheduling.py       # Option 1: Flat
    ├── services/
    │   └── test_scheduling.py   # Option 2: Mirrored structure
    └── integration/
        └── test_schedule_api.py # Integration tests
```

### Frontend (Jest)

```
frontend/
└── src/
    ├── components/
    │   ├── Calendar.tsx              # Source file
    │   └── __tests__/
    │       └── Calendar.test.tsx     # Option 1: __tests__ subdir
    ├── features/
    │   ├── schedule/
    │   │   ├── ScheduleView.tsx
    │   │   └── ScheduleView.test.tsx # Option 2: Adjacent
    └── lib/
        ├── api.ts
        └── api.test.ts
```

---

## Exemptions

### Files That Don't Need Tests

Some files are intentionally excluded from coverage requirements:

**Backend:**
- `backend/app/core/config.py` - Configuration (tested via integration)
- `backend/app/models/__init__.py` - Re-exports only
- `backend/alembic/**` - Migrations

**Frontend:**
- `frontend/src/types/**` - Type definitions only
- `frontend/src/mocks/**` - Test mocks
- `frontend/src/**/*.d.ts` - TypeScript declarations

### Documenting Exemptions

If a file legitimately doesn't need tests, add to coverage config:

**Backend (`pyproject.toml`):**
```toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/alembic/*",
    "app/core/config.py",  # Configuration - tested via integration
]
```

**Frontend (`jest.config.js`):**
```javascript
collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/types/**',      // Type definitions
    '!src/mocks/**',      // Test infrastructure
]
```

---

## Troubleshooting

### "Coverage below threshold" in CI but passes locally

**Likely causes:**
1. CI uses stricter thresholds (80% backend, 70% frontend)
2. CI runs all tests, local run might skip some
3. Generated files differ between environments

**Fix:** Run with CI thresholds:
```bash
cd backend
pytest --cov=app --cov-fail-under=80

cd frontend
npm test -- --coverage --coverageThreshold='{"global":{"lines":70}}'
```

### Test file not found warning but test exists

**Likely causes:**
1. Test file uses non-standard naming
2. Test is in integration test directory

**Fix:** Either:
- Rename to match convention (`test_<module>.py`)
- Add explicit test import in existing test file

### Hook too slow

The hook is designed to be fast (<5 seconds) by default. If slow:
1. Check for `COVERAGE_FULL=1` (runs full suite)
2. Ensure you're not running from within `backend/` or `frontend/`

---

## Related Documentation

- `.github/workflows/quality-gates.yml` - CI enforcement
- `backend/pyproject.toml` - pytest/coverage config
- `frontend/jest.config.js` - Jest coverage config
- `.claude/Governance/QA_GUIDELINES.md` - Testing standards

---

## Checklist

Before committing code changes:

- [ ] Changed files have corresponding test files
- [ ] Tests pass locally (`pytest` / `npm test`)
- [ ] Coverage is above local threshold (70% backend, 60% frontend)
- [ ] New code has test coverage for critical paths
- [ ] Edge cases and error paths are tested
- [ ] Integration tests updated if API changed
