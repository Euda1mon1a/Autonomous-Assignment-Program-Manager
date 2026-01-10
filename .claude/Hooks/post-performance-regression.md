# Post-Performance Regression Hook

**Trigger:** Before committing changes to backend code or tests

---

## Purpose

Catch performance regressions early by:
- Detecting slow test patterns in staged code
- Reminding developers to check test timing
- Optionally running full performance validation
- Providing actionable feedback before CI

---

## Quick Reference

### Thresholds

| Metric | Default | Configurable |
|--------|---------|--------------|
| **Slow test warning** | 2.0s | `SLOW_THRESHOLD=3.0` |
| **Full check trigger** | Manual | `PERF_FULL=1` |

### Run Performance Checks Manually

**Quick timing check:**
```bash
cd backend
pytest --durations=10 -q
pytest -m "not slow" --durations=5
```

**Full performance suite:**
```bash
cd backend
pytest tests/performance/ -v --durations=0
```

**Benchmarks:**
```bash
cd backend
python -m benchmarks --quick
python -m benchmarks --all
```

### Trigger Full Check at Commit

```bash
PERF_FULL=1 git commit -m "your message"
```

---

## What the Hook Checks

### Check 1: Staged File Detection (INFO)

Counts backend files staged for commit:
- `backend/app/**/*.py` - Application code
- `backend/tests/**/*.py` - Test files

Skips hook entirely if no backend files staged.

### Check 2: Slow Test Markers (INFO)

Looks for `@pytest.mark.slow` decorators in staged test files.
Properly marked slow tests are expected and healthy.

### Check 3: Performance Test Changes (INFO)

Detects changes to `backend/tests/performance/**/*.py`.
Performance test modifications warrant extra attention.

### Check 4: Slow Patterns (WARNING)

Scans staged code for patterns that typically indicate slow operations:
- `time.sleep(N)` - Intentional delays
- `range(10000+)` - Large iterations
- `for ... in range(100+)` - Bulk operations

**Example warning:**
```
Potentially slow patterns detected in 2 file(s):
  - backend/tests/test_bulk.py
  - backend/app/services/batch.py

Consider marking with @pytest.mark.slow if intentional.
```

### Check 5: Timing Reminder (INFO)

When test files are staged, displays helpful commands:
```
Test files modified. Before push, verify timing:
  cd backend && pytest --durations=10 -q
  pytest -m 'not slow' --durations=5
```

### Check 6: Full Performance Run (PERF_FULL=1)

With `PERF_FULL=1`:
1. Runs fast tests with timing analysis
2. Warns if any test exceeds threshold (default 2s)
3. Runs performance test suite
4. Fails commit if tests fail

---

## Performance Test Infrastructure

### Test Markers

The codebase uses pytest markers to categorize tests:

```python
@pytest.mark.slow
def test_large_schedule_generation():
    """Takes >10s, skip in quick runs."""
    ...

@pytest.mark.performance
def test_validation_throughput():
    """Performance benchmark."""
    ...

@pytest.mark.integration
def test_database_operations():
    """Requires database."""
    ...
```

**Running by marker:**
```bash
pytest -m "not slow"           # Skip slow tests
pytest -m performance          # Only performance tests
pytest -m "unit and not slow"  # Fast unit tests
```

### Performance Thresholds

Defined in `backend/tests/performance/`:

| Scenario | Threshold | Notes |
|----------|-----------|-------|
| 100 residents, 4 weeks | < 5.0s | ACGME validation |
| 50 residents, 4 weeks | < 2.0s | Standard load |
| 25 residents, 4 weeks | < 1.0s | Light load |
| 10 concurrent validations | < 10.0s | Concurrency test |
| Memory per operation | < 500MB | Resource limit |

### Benchmark Suite

Location: `backend/benchmarks/`

```bash
# Run all benchmarks
python -m benchmarks --all

# Quick benchmarks only
python -m benchmarks --quick

# Specific category
python -m benchmarks --category scheduling
python -m benchmarks --category database
```

---

## CI Integration

### Quality Gates Workflow

Performance is checked in CI via `.github/workflows/quality-gates.yml`:
- Runs on PR, push to main, and scheduled
- Stricter thresholds than local hooks
- Artifact collection for trend analysis

### Load Testing Workflow

Weekly load tests via `.github/workflows/load-tests.yml`:
- Uses k6 for load testing
- Configurable test type, duration, virtual users
- Manual trigger available for pre-release validation

---

## Troubleshooting

### "Slow patterns detected" but code is fine

**Likely causes:**
1. Pattern matched in comments or strings
2. Intentional bulk operation (e.g., data migration)

**Fix:**
- If intentional, mark test with `@pytest.mark.slow`
- If false positive, the pattern is informational only

### Tests pass locally but fail in CI

**Likely causes:**
1. CI has less resources (slower)
2. CI runs full suite including slow tests
3. Flaky tests under load

**Fix:**
```bash
# Run exactly what CI runs
pytest -m "not slow" --durations=20
pytest tests/performance/ -v
```

### Hook too slow

The hook is fast by default (~1-2 seconds). If slow:
1. Check if `PERF_FULL=1` is set
2. Full mode runs actual tests which takes time

---

## Best Practices

### 1. Mark Slow Tests

Always mark tests that take >2s:
```python
@pytest.mark.slow
def test_comprehensive_validation():
    ...
```

### 2. Separate Performance Tests

Keep performance tests in `tests/performance/`:
```
backend/tests/
├── unit/              # Fast unit tests
├── integration/       # Integration tests
└── performance/       # Performance benchmarks
    ├── test_scheduling_perf.py
    └── test_validation_perf.py
```

### 3. Use Timing Utilities

The codebase provides timing helpers:
```python
from tests.performance.fixtures import measure_time, assert_performance

with measure_time() as timer:
    result = expensive_operation()

assert_performance(timer.elapsed, max_seconds=2.0)
```

### 4. Review Before Push

Before pushing changes to test files:
```bash
cd backend
pytest --durations=10 -q
```

---

## Related Documentation

- `backend/tests/performance/` - Performance test suite
- `backend/benchmarks/` - Benchmark suite
- `backend/pytest.ini` - Test markers configuration
- `.github/workflows/load-tests.yml` - CI load testing
- `.github/workflows/quality-gates.yml` - CI quality gates

---

## Checklist

Before committing backend/test changes:

- [ ] Test files have appropriate markers (`@pytest.mark.slow`)
- [ ] No unintentional slow patterns introduced
- [ ] Quick tests pass: `pytest -m "not slow" -q`
- [ ] Timing is reasonable: `pytest --durations=10`
- [ ] Performance tests pass (if modified): `pytest tests/performance/`
