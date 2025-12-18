***REMOVED*** ACGME Performance Tests

Performance and load tests for ACGME compliance validation in the Residency Scheduler.

***REMOVED******REMOVED*** Overview

These tests validate that ACGME compliance validation can handle large datasets efficiently, ensuring the system performs well even with 100+ residents and thousands of assignments.

***REMOVED******REMOVED*** Test Files

- **`__init__.py`** - Package initialization
- **`conftest.py`** - Shared fixtures for creating large datasets and measuring performance
- **`test_acgme_load.py`** - ACGME validation performance tests

***REMOVED******REMOVED*** Performance Thresholds

| Test Scenario | Max Time | Dataset |
|--------------|----------|---------|
| 100 residents, 4 weeks | 5.0s | ~5,600 assignments |
| 50 residents, 4 weeks | 2.0s | ~2,800 assignments |
| 25 residents, 2 weeks | 1.0s | ~700 assignments |
| 10 concurrent validations | 10.0s | 100 residents each |
| 12-week validation | 15.0s | ~16,800 assignments |

***REMOVED******REMOVED*** Running Tests

***REMOVED******REMOVED******REMOVED*** Run All Performance Tests

```bash
cd backend
pytest tests/performance/ -v
```

***REMOVED******REMOVED******REMOVED*** Run with Timing Output

```bash
pytest tests/performance/ -v -s
```

The `-s` flag shows print statements including detailed timing information.

***REMOVED******REMOVED******REMOVED*** Run Only Fast Performance Tests

```bash
pytest tests/performance/ -v -m "performance and not slow"
```

***REMOVED******REMOVED******REMOVED*** Run Only Slow/Load Tests

```bash
pytest tests/performance/ -v -m "performance and slow"
```

***REMOVED******REMOVED******REMOVED*** Run Specific Test Class

```bash
***REMOVED*** ACGME performance tests
pytest tests/performance/test_acgme_load.py::TestACGMEPerformance -v

***REMOVED*** Concurrent validation tests
pytest tests/performance/test_acgme_load.py::TestConcurrentValidation -v

***REMOVED*** Memory efficiency tests
pytest tests/performance/test_acgme_load.py::TestValidationMemoryEfficiency -v

***REMOVED*** Edge case tests
pytest tests/performance/test_acgme_load.py::TestValidationEdgeCases -v
```

***REMOVED******REMOVED******REMOVED*** Run Specific Test

```bash
pytest tests/performance/test_acgme_load.py::TestACGMEPerformance::test_80_hour_rule_large_dataset -v
```

***REMOVED******REMOVED*** Test Coverage

***REMOVED******REMOVED******REMOVED*** Test Classes

1. **TestACGMEPerformance** - Core validation performance
   - 80-hour rule with 100 residents
   - 1-in-7 rule with large datasets
   - Supervision ratio validation under load
   - Medium dataset (50 residents) validation
   - Small dataset (25 residents) baseline

2. **TestConcurrentValidation** - Concurrent operation handling
   - 10 simultaneous validations
   - Rapid sequential validation (caching)
   - Database locking behavior

3. **TestValidationMemoryEfficiency** - Memory and scaling
   - Huge dataset validation (12 weeks)
   - Incremental vs. full validation comparison

4. **TestValidationEdgeCases** - Edge cases and stress
   - Empty schedule validation
   - Sparse assignment validation

***REMOVED******REMOVED*** Fixtures

***REMOVED******REMOVED******REMOVED*** Dataset Fixtures

- **`large_resident_dataset`** - 100 residents (40 PGY-1, 35 PGY-2, 25 PGY-3)
- **`large_faculty_dataset`** - 30 faculty members
- **`four_week_blocks`** - 28 days of blocks (56 blocks total)
- **`large_assignment_dataset`** - ~5,600 assignments
- **`huge_dataset`** - 12 weeks of data (~16,800 assignments)
- **`large_rotation_template`** - Standard rotation template

***REMOVED******REMOVED******REMOVED*** Utility Fixtures

- **`perf_timer`** - Performance timer context manager
- **`measure_time`** - Function for timing operations
- **`assert_performance`** - Assert operation meets threshold

***REMOVED******REMOVED*** Example Output

```
tests/performance/test_acgme_load.py::TestACGMEPerformance::test_80_hour_rule_large_dataset

Validating 80-hour rule for 100 residents
Date range: 2025-12-18 to 2026-01-14
Total assignments: 5600

80-hour rule validation (100 residents): 2.456s
✓ 80-hour rule validation (100 residents) completed in 2.456s (threshold: 5.000s)
Total violations: 3
Coverage rate: 95.2%
Validation rate: 40.7 residents/sec
PASSED
```

***REMOVED******REMOVED*** Interpreting Results

***REMOVED******REMOVED******REMOVED*** Success Criteria

- **Duration < Threshold**: Test passes if validation completes within threshold
- **Consistent Results**: Concurrent validations should produce identical results
- **Scaling Behavior**: Performance should scale roughly linearly with dataset size

***REMOVED******REMOVED******REMOVED*** Common Failures

1. **Timeout/Slow Performance**
   - Database query optimization needed
   - Too many N+1 queries
   - Missing indexes on key columns
   - Need caching or query batching

2. **Inconsistent Concurrent Results**
   - Database transaction isolation issues
   - Race conditions in validation logic
   - Caching stale data

3. **Memory Issues**
   - Loading too much data into memory at once
   - Not releasing database connections
   - Memory leaks in validation logic

***REMOVED******REMOVED*** Integration with CI/CD

These tests can be integrated into CI/CD pipelines:

```yaml
***REMOVED*** Example GitHub Actions
- name: Run performance tests
  run: |
    cd backend
    pytest tests/performance/ -v -m "performance and not slow"
```

Run slow tests on a schedule (nightly):

```yaml
***REMOVED*** Nightly performance regression tests
- name: Run slow performance tests
  run: |
    cd backend
    pytest tests/performance/ -v -m "performance and slow"
```

***REMOVED******REMOVED*** Extending Tests

***REMOVED******REMOVED******REMOVED*** Adding New Performance Tests

1. Add test to appropriate class in `test_acgme_load.py`
2. Use `@pytest.mark.performance` and optionally `@pytest.mark.slow`
3. Use `measure_time()` context manager for timing
4. Use `assert_performance()` to validate threshold
5. Document test requirements in docstring

***REMOVED******REMOVED******REMOVED*** Example

```python
@pytest.mark.performance
def test_my_new_validation(self, db, large_dataset):
    """
    Test description here.

    Requirements:
        - Should complete in < 3 seconds
        - Should handle edge case X
    """
    validator = ACGMEValidator(db)

    with measure_time("My validation") as metrics:
        result = validator.my_validation()

    assert_performance(metrics["duration"], 3.0, "My validation")
    assert result is not None
```

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Tests Running Slowly

1. **Check database**: Ensure using in-memory SQLite for tests
2. **Check fixtures**: Verify fixtures aren't creating more data than needed
3. **Profile**: Use `pytest --profile` to identify bottlenecks
4. **Database queries**: Check for N+1 queries with SQL logging

***REMOVED******REMOVED******REMOVED*** Flaky Tests

1. **Timing sensitivity**: Add small buffer to thresholds if tests occasionally fail
2. **Concurrency**: Ensure database properly handles concurrent access
3. **Fixture cleanup**: Verify fixtures clean up properly between tests

***REMOVED******REMOVED******REMOVED*** Import Errors

Ensure all dependencies installed:

```bash
cd backend
pip install -r requirements.txt
```

***REMOVED******REMOVED*** References

- [ACGME Duty Hour Requirements](https://www.acgme.org/what-we-do/accreditation/common-program-requirements/)
- [pytest Performance Testing](https://docs.pytest.org/en/stable/how-to/mark.html)
- [SQLAlchemy Performance](https://docs.sqlalchemy.org/en/20/faq/performance.html)

***REMOVED******REMOVED*** Maintenance

Review and update performance thresholds:
- After infrastructure upgrades
- When optimizations are implemented
- If dataset sizes change significantly
- Based on production monitoring data

Update thresholds in `conftest.py`:

```python
MAX_VALIDATION_TIME_100_RESIDENTS = 5.0  ***REMOVED*** seconds
MAX_VALIDATION_TIME_50_RESIDENTS = 2.0   ***REMOVED*** seconds
MAX_VALIDATION_TIME_25_RESIDENTS = 1.0   ***REMOVED*** seconds
```
