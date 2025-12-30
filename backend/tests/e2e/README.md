# End-to-End Tests for Schedule Generation Workflow

This directory contains comprehensive end-to-end tests for the schedule generation workflow.

## Test Coverage

### `test_schedule_workflow.py`

**Full Schedule Generation Flow:**
- `test_full_schedule_generation_greedy_algorithm` - Complete workflow using greedy algorithm
- `test_schedule_generation_with_multiple_algorithms` - Testing all solver algorithms (greedy, cp_sat, pulp)
- `test_schedule_generation_respects_absences` - Verifies blocking absences are respected
- `test_schedule_generation_with_pgy_level_filter` - Tests PGY level filtering
- `test_schedule_generation_creates_faculty_supervision` - Verifies faculty supervision assignment

**ACGME Compliance Validation:**
- `test_acgme_validation_after_generation` - Validates ACGME checks after generation
- `test_acgme_validator_standalone` - Tests validator as independent component
- `test_validation_detects_supervision_violations` - Stress test for supervision ratios

**Schedule Export:**
- `test_export_schedule_to_json` - JSON export functionality
- `test_export_schedule_to_csv` - CSV export functionality
- `test_export_includes_all_schedule_components` - Verifies export completeness

**Error Handling:**
- `test_invalid_date_range_error` - Invalid date range handling
- `test_no_residents_error_handling` - No residents scenario
- `test_no_templates_error_handling` - No templates scenario
- `test_invalid_algorithm_fallback` - Invalid algorithm fallback to greedy
- `test_timeout_handling` - Solver timeout handling

## Running the Tests

### Run all E2E tests:
```bash
cd backend
pytest tests/e2e/ -v
```

### Run specific test class:
```bash
pytest tests/e2e/test_schedule_workflow.py::TestScheduleGenerationE2E -v
```

### Run specific test:
```bash
pytest tests/e2e/test_schedule_workflow.py::TestScheduleGenerationE2E::test_full_schedule_generation_greedy_algorithm -v
```

### Run with coverage:
```bash
pytest tests/e2e/ --cov=app.scheduling --cov=app.services.export --cov-report=html
```

### Run E2E tests only (skip unit tests):
```bash
pytest tests/e2e/ -v --tb=short
```

## Test Data Setup

Each test uses fixtures defined in `conftest.py` and local fixtures:

- `academic_year_setup` - Complete setup with residents, faculty, and rotation templates
- `schedule_with_absence` - Setup with blocking absence for absence testing

## Dependencies

These tests require:
- SQLAlchemy ORM models
- Scheduling engine (`app.scheduling.engine`)
- ACGME validator (`app.scheduling.validator`)
- Export services (`app.services.export`)

## Test Environment

Tests use in-memory SQLite database configured in `tests/conftest.py`.
Each test gets a fresh database to ensure isolation.

## Debugging

### View detailed output:
```bash
pytest tests/e2e/test_schedule_workflow.py -v -s
```

### Run with debugger on failure:
```bash
pytest tests/e2e/test_schedule_workflow.py --pdb
```

### See full traceback:
```bash
pytest tests/e2e/test_schedule_workflow.py -v --tb=long
```

## CI/CD Integration

These tests are designed to run in CI pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run E2E Tests
  run: |
    cd backend
    pytest tests/e2e/ -v --tb=short
```

## Notes

- Tests are marked with `@pytest.mark.asyncio` where async operations are used
- Export tests verify data structure and completeness
- Error handling tests ensure graceful failures without exceptions
- All tests use the greedy algorithm by default for speed (30s timeout)
