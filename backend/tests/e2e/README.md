# End-to-End Tests for Residency Scheduler

## Overview

This directory contains end-to-end (E2E) tests that validate complete workflows across the entire application stack, from schedule generation through validation and export.

## Test Files

### `test_celery_jobs_e2e.py`

Comprehensive E2E tests for Celery background job execution and monitoring.

#### Test Classes

##### `TestCeleryJobWorkflowE2E` (3 tests)

Tests the complete Celery job lifecycle from submission to completion.

**Tests:**

1. **`test_submit_and_monitor_health_check_job`**
   - Submit periodic_health_check task
   - Monitor task status transitions
   - Verify queuing mechanism works

2. **`test_submit_contingency_analysis_job`**
   - Submit task with custom parameters
   - Verify task queued with correct configuration
   - Check task ID generation

3. **`test_job_status_transitions`**
   - Test notification alert task
   - Verify task lifecycle states
   - Validate task result object

##### `TestCeleryJobResultsE2E` (3 tests)

Tests result storage, retrieval, and error handling.

**Tests:**

1. **`test_retrieve_health_check_results`**
   - Execute health check synchronously
   - Retrieve result from backend
   - Validate result structure (timestamp, status, utilization, defense_level)

2. **`test_retrieve_contingency_analysis_results`**
   - Execute contingency analysis task
   - Validate complex result structure (period, n1_pass, n2_pass, recommendations)
   - Test nested data handling

3. **`test_failed_task_result_handling`**
   - Submit task that fails
   - Verify failure recorded in result
   - Check error message captured

##### `TestCeleryQueueManagementE2E` (3 tests)

Tests queue management, routing, and concurrent job execution.

**Tests:**

1. **`test_concurrent_job_submission`**
   - Submit 5 jobs simultaneously
   - Verify all queued successfully
   - Check unique task IDs generated

2. **`test_queue_routing`**
   - Verify resilience tasks → resilience queue
   - Verify notification tasks → notifications queue
   - Test queue isolation

3. **`test_inspect_active_jobs`**
   - Use Celery inspect API
   - Check active, scheduled, reserved tasks
   - Validate worker status

##### `TestCeleryErrorHandlingE2E` (3 tests)

Tests error handling, retries, and failure recovery.

**Tests:**

1. **`test_task_retry_on_failure`**
   - Simulate database connection failure
   - Verify task retries automatically
   - Check retry count increments

2. **`test_max_retries_exhausted`**
   - Test persistent failure scenario
   - Verify task fails after max_retries
   - Check final state is FAILURE

3. **`test_error_message_in_result`**
   - Submit task with invalid parameters
   - Verify error message captured
   - Test traceback availability

##### `TestCeleryTaskTypesE2E` (3 tests)

Tests different Celery task types across modules.

**Tests:**

1. **`test_resilience_health_check_task`**
   - Execute periodic_health_check
   - Validate metrics updated
   - Check result contains health status

2. **`test_utilization_forecast_task`**
   - Execute generate_utilization_forecast
   - Verify forecast generation
   - Check high-risk period identification

3. **`test_notification_alert_task`**
   - Execute send_resilience_alert
   - Validate multi-channel delivery
   - Test priority handling

##### `TestCeleryMonitoringE2E` (2 tests)

Tests monitoring, metrics collection, and observability.

**Tests:**

1. **`test_task_metrics_collection`**
   - Collect active task count
   - Calculate completed/failed task counts
   - Verify success rate calculation

2. **`test_recent_task_history`**
   - Retrieve task execution history
   - Verify proper ordering (most recent first)
   - Validate task metadata

### `test_schedule_generation_e2e.py`

Comprehensive E2E tests for the complete schedule generation workflow.

#### Test Classes

##### `TestScheduleGenerationWorkflow` (8 tests)

Tests the complete integration of schedule generation, ACGME validation, and export functionality.

**Tests:**

1. **`test_full_schedule_generation_greedy_algorithm`**
   - Complete workflow: Generate (greedy) → Validate → Export
   - Verifies schedule creation, ACGME validation, and CSV/JSON export
   - Primary E2E test for the most common use case

2. **`test_schedule_generation_with_validation`**
   - Direct engine testing (bypasses API)
   - Tests core generation and validation logic
   - Verifies proper linking of assignments to blocks and people

3. **`test_schedule_generation_multiple_algorithms`**
   - Compares results from different solver algorithms
   - Tests greedy and other available algorithms
   - Ensures no crashes and proper result structure

4. **`test_export_formats_consistency`**
   - Validates data consistency across export formats
   - Tests CSV and JSON exports
   - Verifies no data loss during export

5. **`test_acgme_validation_after_generation`**
   - Creates schedule with known violations
   - Verifies validator detects 80-hour and 1-in-7 rule violations
   - Tests violation reporting

6. **`test_schedule_generation_error_handling`**
   - Tests invalid date ranges
   - Tests invalid algorithm names
   - Tests missing required fields
   - Verifies appropriate error codes and messages

7. **`test_schedule_persistence_across_sessions`**
   - Verifies assignments persist to database
   - Tests data integrity across sessions
   - Validates relationship maintenance

8. **`test_concurrent_validation_and_export`**
   - Simulates concurrent operations
   - Tests for database locks/deadlocks
   - Ensures result consistency

##### `TestScheduleGenerationEdgeCases` (3 tests)

Tests edge cases and complex integration scenarios.

**Tests:**

1. **`test_empty_schedule_generation`**
   - Tests with no residents or templates
   - Verifies graceful handling of empty data

2. **`test_single_day_schedule_generation`**
   - Tests minimal date range (single day)
   - Verifies validation and export work for small datasets

3. **`test_long_schedule_generation`**
   - Tests extended period (4 weeks)
   - Validates ACGME rolling window checks
   - Tests performance with larger datasets

## Fixtures

### `complete_program_setup`

Creates a comprehensive test environment:
- **6 residents** (2 per PGY level: 1, 2, 3)
- **4 faculty members** with various specialties
- **4 rotation templates** (clinic, inpatient, procedures, conference)
- **14 days of blocks** (28 half-day blocks for 2 weeks)

## Test Coverage

### ✅ Covered Scenarios

- Complete schedule generation workflow
- ACGME compliance validation (80-hour rule, 1-in-7 rule)
- Export to multiple formats (CSV, JSON)
- Multiple solver algorithms
- Database persistence
- Error handling
- Edge cases (empty, single day, extended periods)
- Concurrent operations

### ⏳ TODOs (Not Fully Tested)

1. **Real API integration** with export endpoints (requires route implementation)
2. **CP-SAT solver** testing (if available)
3. **Excel (XLSX) export** (requires additional dependencies)
4. **Real resilience framework** integration (mocked for performance)
5. **Multi-user concurrent** schedule generation (requires advanced setup)
6. **Faculty supervision assignment** validation (complex relationships)

### Known Limitations

- Some tests use simplified mock data
- Export endpoint tests limited by available routes
- ACGME validation tests are basic (full validation requires more setup)
- Some advanced constraint tests require additional fixtures

## Running the Tests

### Run all E2E tests:
```bash
cd backend
pytest tests/e2e/ -v
```

### Run specific test class:
```bash
pytest tests/e2e/test_schedule_generation_e2e.py::TestScheduleGenerationWorkflow -v
```

### Run single test:
```bash
pytest tests/e2e/test_schedule_generation_e2e.py::TestScheduleGenerationWorkflow::test_full_schedule_generation_greedy_algorithm -v
```

### Run with coverage:
```bash
pytest tests/e2e/ --cov=app.scheduling --cov-report=html
```

### Run only E2E tests (skip unit/integration):
```bash
pytest -m e2e -v
```

## Test Markers

Tests in this module use the `@pytest.mark.e2e` marker to distinguish them from unit and integration tests.

## Dependencies

These tests require:
- SQLAlchemy and database models
- FastAPI TestClient
- SchedulingEngine and ACGMEValidator
- Export services

## Architecture Validation

These E2E tests validate the complete architecture:

```
API Route (FastAPI endpoint)
    ↓
Controller (request/response handling)
    ↓
Service (business logic)
    ↓
SchedulingEngine
    ↓
Solver (greedy/CP-SAT/PuLP)
    ↓
ACGMEValidator
    ↓
Export (CSV/JSON/XML)
    ↓
Database (persistence)
```

## Best Practices

1. **Use fixtures** for complex test data setup
2. **Test complete workflows** end-to-end
3. **Verify database state** after operations
4. **Test error scenarios** in addition to happy path
5. **Mock external dependencies** but test integration points
6. **Keep tests isolated** - each test should be independent

## Contributing

When adding new E2E tests:

1. Follow the existing test structure
2. Use descriptive test names
3. Include comprehensive docstrings
4. Test both success and failure scenarios
5. Verify database state changes
6. Update this README with new test descriptions

## Related Documentation

- [CLAUDE.md](../../../CLAUDE.md) - Testing requirements
- [Test Scenarios](../integration/test_scheduling_flow.py) - Integration tests
- [Solver Documentation](../../../docs/architecture/SOLVER_ALGORITHM.md) - Scheduling algorithms
