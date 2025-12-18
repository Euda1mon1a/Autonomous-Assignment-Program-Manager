# Idempotency Load Testing

## Overview

Comprehensive pytest tests for idempotency under concurrent load in `test_idempotency_load.py`.

**Created:** 2025-12-18
**Purpose:** Verify idempotency framework prevents duplicate record creation under high concurrency

## Test Coverage

### Test Classes (4)

1. **TestScheduleGenerationIdempotencyLoad** - Schedule generation with 100+ concurrent requests
2. **TestIdempotencyExpiry** - Expiration and cleanup behavior
3. **TestIdempotencyServiceConcurrency** - Service-level race conditions
4. **TestIdempotencyHeaderPropagation** - Response header verification

### Test Methods (9)

#### Schedule Generation Tests
- `test_schedule_generation_100_concurrent()` - 100 concurrent identical requests → 1 schedule run
- `test_schedule_generation_network_retry_simulation()` - Network retry patterns
- `test_schedule_generation_idempotency_key_isolation()` - Different keys create different runs
- `test_schedule_generation_idempotency_conflict_detection()` - Same key + different body = 422 error

#### Expiry Tests
- `test_schedule_generation_idempotency_expiry_allows_new_creation()` - Expired keys allow new creation
- `test_idempotency_cleanup_expired_records()` - Cleanup function removes expired records

#### Service Concurrency Tests
- `test_create_request_race_condition()` - Concurrent create_request with same key+hash
- `test_concurrent_mark_completed()` - Concurrent completion marking

#### Header Tests
- `test_replayed_response_includes_header()` - X-Idempotency-Replayed header verification

## Running Tests

```bash
# Run all idempotency load tests
cd backend
pytest tests/performance/test_idempotency_load.py -v

# Run specific test class
pytest tests/performance/test_idempotency_load.py::TestScheduleGenerationIdempotencyLoad -v

# Run specific test
pytest tests/performance/test_idempotency_load.py::TestScheduleGenerationIdempotencyLoad::test_schedule_generation_100_concurrent -v

# Run with performance marker
pytest -m performance tests/performance/test_idempotency_load.py
```

## Key Features

### Concurrency Testing
- Uses `ThreadPoolExecutor` for concurrent request simulation
- Tests with 20-100 concurrent workers
- Simulates network retry storms and race conditions

### Realistic Scenarios
- Network timeouts and retries
- Multiple connections with same idempotency key
- Key reuse after expiration
- Conflict detection (same key, different body)

### Comprehensive Verification
- Database state assertions
- Response consistency checks
- Idempotency record validation
- Header propagation verification

## Technical Details

### Idempotency Implementation (PR #240)
- Model: `IdempotencyRequest` with composite unique index on (key, body_hash)
- Service: `IdempotencyService` for hash computation and record management
- Endpoint: `/api/schedule/generate` with `Idempotency-Key` header support
- Expiry: 24-hour default expiration with cleanup function

### Test Fixtures Used
- `client` - FastAPI TestClient
- `db` - SQLAlchemy test database session
- `sample_residents` - Multiple test residents
- `sample_faculty_members` - Multiple test faculty
- `sample_rotation_template` - Rotation template for scheduling

## Critical Assertions

1. **Deduplication**: 100 concurrent requests → exactly 1 database record
2. **Response Consistency**: All concurrent requests return same ID
3. **Header Propagation**: Replayed responses include `X-Idempotency-Replayed: true`
4. **Conflict Detection**: Same key + different body → HTTP 422
5. **Expiry Behavior**: Expired keys allow new record creation
6. **Cleanup Efficiency**: Cleanup function removes only expired records

## Healthcare Context

Idempotency is **critical** for HIPAA-compliant healthcare applications:

- **Data Integrity**: Prevents duplicate schedule generations
- **ACGME Compliance**: Avoids double-booking violations
- **Audit Trail**: Maintains clean idempotency records
- **Network Resilience**: Handles retries without creating duplicates

## Future Enhancements

To extend idempotency to other endpoints:

1. **Absence Creation** - Add idempotency to `/api/absences`
2. **Military Deployments** - Critical for deployment tracking
3. **Assignment Creation** - Prevent double-booking
4. **Swap Requests** - Ensure single swap per request

See commented-out test examples in the original task description for patterns.

## Notes

- Tests use in-memory SQLite database (via conftest.py)
- Marked with `@pytest.mark.performance` for selective execution
- Thread-safe using `ThreadPoolExecutor` (TestClient is synchronous)
- All tests follow CLAUDE.md guidelines for healthcare applications
