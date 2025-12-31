# Performance Test Coverage - Quick Reference
**SEARCH_PARTY Recon Results**

---

## Test Inventory at a Glance

### Backend pytest: 53 Performance Tests

**Location:** `/backend/tests/performance/`

**File Breakdown:**
```
conftest.py (fixtures + utilities)
  - PerformanceTimer class
  - Large dataset fixtures (100 residents, 30 faculty, 56 blocks, 5.6K assignments)
  - Huge dataset fixture (12 weeks, 16.8K assignments)
  - Performance assertion helpers

test_acgme_load.py (34 tests across 4 classes)
  ✓ TestACGMEPerformance (5)
  ✓ TestConcurrentValidation (2)
  ✓ TestValidationMemoryEfficiency (2)
  ✓ TestValidationEdgeCases (2)

test_connection_pool.py (22 tests across 5 classes)
  ✓ TestConnectionPoolStress (4)
  ✓ TestConnectionLeakDetection (3)
  ✓ TestPoolRecovery (3)
  ✓ TestConcurrentTransactionIsolation (3)
  ✓ TestTaskSessionScope (3)
  ✓ TestConnectionPoolMetrics (1)

test_idempotency_load.py (9 tests across 4 classes)
  ✓ TestScheduleGenerationIdempotencyLoad (4)
  ✓ TestIdempotencyExpiry (2)
  ✓ TestIdempotencyServiceConcurrency (2)
  ✓ TestIdempotencyHeaderPropagation (1)
```

---

### k6 Load Tests: 8 Scenarios

**Location:** `/load-tests/scenarios/`

| Scenario | File | Load Pattern | Duration | Purpose |
|----------|------|--------------|----------|---------|
| Baseline | `api-baseline.js` | 1 VU, 100 iter | ~1m | Endpoint baselines (p50/p95/p99) |
| Concurrent | `concurrent-users.js` | 10→50 VUs | 5m | Multi-user load pattern |
| Auth Security | `auth-security.js` | Variable | 10m | Rate limit + auth attacks |
| Schedule Gen | `schedule-generation.js` | 1→10 admins | 15m | Schedule generation stress |
| Rate Limit | `rate-limit-attack.js` | Spike | 5m | DDoS simulation |
| Peak Load | `peak_load_scenario.js` | 200 VUs | 10m | Capacity ceiling |
| Soak Test | `soak_test_scenario.js` | 20 VUs | 60m | Memory leak detection |
| Spike Test | `spike_test_scenario.js` | 10→100 VU burst | 5m | Graceful degradation |

---

## SLA Thresholds

### ACGME Validation (pytest)

| Dataset | Threshold | Notes |
|---------|-----------|-------|
| 100 residents, 4 weeks (5.6K assignments) | < 5.0s | Must complete in single request |
| 50 residents, 4 weeks (2.8K assignments) | < 2.0s | Medium program baseline |
| 25 residents, 2 weeks (700 assignments) | < 1.0s | Small program fast path |
| 10 concurrent validations | < 10s | No queue buildup |
| 100 residents, 12 weeks (16.8K assignments) | < 15.0s | 3x scaling factor |

### k6 Load Test Thresholds

| Metric | Default | Strict | Relaxed |
|--------|---------|--------|---------|
| p95 response | < 500ms | < 300ms | < 2000ms |
| p99 response | < 1000ms | < 600ms | < 5000ms |
| Error rate | < 1% | < 0.5% | < 2% |

**Strict Applied To:** Auth, compliance checks
**Relaxed Applied To:** Schedule generation, complex ops

---

## Coverage Matrix

| Component | Unit Tests | Load Tests | Status |
|-----------|-----------|-----------|--------|
| ACGME Validator | ✓ 5 tests | ✗ Indirect | Well covered |
| Connection Pool | ✓ 11 tests | ✗ Indirect | Well covered |
| Idempotency | ✓ 9 tests | ✓ Indirect | Good coverage |
| Auth Security | ✓ Partial | ✓ 1 scenario | Covered |
| Schedule Gen | ✓ Partial | ✓ 1 scenario | Needs algo profiling |
| **Swap Operations** | ✗ NONE | ✗ NONE | **CRITICAL GAP** |
| **Resilience** | ✗ NONE | ✗ NONE | **CRITICAL GAP** |
| **MCP Server** | ✗ NONE | ✗ NONE | **CRITICAL GAP** |
| API Endpoints | ✓ 10 profiled | ✓ 10 profiled | Needs expansion |

---

## Critical Gaps (Action Items)

### 🔴 CRITICAL - Must Fix Before Production

**1. Swap Operation Load Testing**
```
Missing: test_swap_execution_load.py
Expected: 4-5 tests
- 100 concurrent swaps
- Swap matching performance (1000 candidates)
- Race condition testing
- Rollback consistency
Target SLA: < 5s per swap, 100% consistency
```

**2. Resilience Framework Benchmarks**
```
Missing: test_resilience_load.py
Expected: 4-5 tests
- N-1/N-2 contingency analysis (< 5s)
- Defense level scoring (< 1s)
- Circuit breaker timing (< 500ms)
- Burnout Rt calculation (< 10s)
```

**3. MCP Server Performance**
```
Missing: test_mcp_integration_performance.py
Expected: 4-5 tests
- Single tool execution (< 500ms p95)
- Tool chaining (< 2s for 3-level chains)
- Parallel tool execution (10 concurrent)
- Callback latency (< 200ms)
```

### 🟡 MODERATE - Should Complete Soon

**4. API Endpoint Baseline Expansion**
```
Current: 10 endpoints profiled
Missing: 10+ endpoints (swaps, resilience, credentials, conflicts)
Effort: Add to api-baseline.js
```

**5. Schedule Generation Algorithm Profiling**
```
Current: k6 stress test only
Missing: Algorithm-level profiling
- Solver iteration tracking
- Constraint propagation overhead
- Memory allocations
- Solution quality vs. time tradeoff
```

**6. Failure Scenario Testing**
```
Missing: test_resilience_failures.py
Scenarios:
- Slow database (query latency spike)
- Redis unavailable
- Celery worker failure
- Rate limiter malfunction
```

---

## Test Execution Commands

### Run All Performance Tests

```bash
# Backend pytest
cd backend
pytest -m performance -v                    # All performance tests
pytest -m performance --co                 # List only (no run)
pytest tests/performance/ -v               # All performance test files

# k6 Load Tests
cd load-tests
npm run test:smoke                         # Quick validation (1 min)
npm run test:load                          # Standard load test (5 min, 50 VUs)
npm run test:stress                        # Stress test (10 min, 200 VUs)
```

### Run Individual Test Classes

```bash
# ACGME Performance
pytest tests/performance/test_acgme_load.py::TestACGMEPerformance -v

# Connection Pool
pytest tests/performance/test_connection_pool.py::TestConnectionPoolStress -v

# Idempotency
pytest tests/performance/test_idempotency_load.py::TestScheduleGenerationIdempotencyLoad -v
```

### Run Specific k6 Scenarios

```bash
k6 run scenarios/api-baseline.js                    # 1 min baseline
k6 run scenarios/schedule-generation.js             # 15 min stress
k6 run scenarios/soak_test_scenario.js              # 60 min soak
```

---

## Performance Fixtures

### Available in conftest.py

```python
# Large datasets
large_resident_dataset       # 100 residents (40 PGY1, 35 PGY2, 25 PGY3)
large_faculty_dataset        # 30 faculty
large_rotation_template      # Standard rotation
four_week_blocks            # 28 days = 56 blocks (AM/PM)
large_assignment_dataset    # ~5,600 assignments
huge_dataset                # 12 weeks, 16.8K assignments

# Utilities
perf_timer                  # Performance measurement context
measure_time()              # Context manager for timing
assert_performance()        # Assert operation within threshold
PerformanceTimer class      # Manual timing with elapsed property
```

### Usage Example

```python
def test_my_performance(large_resident_dataset, large_assignment_dataset, perf_timer):
    with measure_time("My operation") as metrics:
        result = my_expensive_operation()

    assert_performance(
        metrics["duration"],
        MAX_THRESHOLD,
        "My operation"
    )
```

---

## Key Thresholds Reference

### ACGME Validation Thresholds
```python
MAX_VALIDATION_TIME_100_RESIDENTS = 5.0      # seconds
MAX_VALIDATION_TIME_50_RESIDENTS = 2.0       # seconds
MAX_VALIDATION_TIME_25_RESIDENTS = 1.0       # seconds
MAX_CONCURRENT_VALIDATION_TIME = 10.0        # seconds (10 concurrent)
MAX_MEMORY_MB = 500                          # MB per operation
```

### Connection Pool Thresholds
```python
pool_size = 5
max_overflow = 5
pool_timeout = 2  # seconds
pool_pre_ping = True  # Health checks enabled
```

### k6 Threshold Examples
```javascript
'http_req_duration': ['p(95)<500', 'p(99)<1000']
'http_req_failed': ['rate<0.01']
'checks': ['rate>0.98']
```

---

## What's Tested Well ✓

- ACGME compliance validation (all 3 rules)
- Connection pool lifecycle (creation, reuse, cleanup)
- Database transaction isolation
- Idempotency under concurrent load (100 requests)
- API endpoint baseline performance
- Auth endpoint security and rate limiting
- Schedule generation stress (up to 10 concurrent admins)
- Memory efficiency with extreme datasets (16.8K assignments)

---

## What's NOT Tested ✗

- Swap operations (any load level)
- Resilience framework calculations
- MCP server tool execution
- Schedule generation algorithm profiling
- Complex API operations (20+ endpoints untested)
- Failure scenarios (slow DB, service degradation)
- WebSocket endpoints (if implemented)
- Bulk operations (batch assignment, mass swaps)

---

## Metrics Collected

### pytest Performance Tests
- Response time (start → end)
- Violations detected
- Coverage rate
- Memory usage
- Connection checkout/checkin counts
- Transaction isolation levels
- Error counts and types

### k6 Load Tests
- HTTP request duration (p50, p95, p99)
- Requests per second (throughput)
- Error rate
- Failed requests
- Custom business metrics (schedules created, ACGME violations)
- Response status code distribution

---

## Next Steps

**Immediate (This Week):**
1. Review gap assessment with team
2. Prioritize critical vs. moderate gaps
3. Assign 1-2 engineers to critical gaps
4. Plan Phase 1 implementation

**Short Term (Next 2 Weeks):**
1. Implement swap operation load tests
2. Add resilience framework benchmarks
3. Create MCP server performance tests
4. Expand API endpoint baseline

**Medium Term (Month):**
1. Set up continuous performance monitoring
2. Integrate k6 with Prometheus/Grafana
3. Create performance regression detection
4. Add CI/CD performance checks

---

**Last Updated:** 2025-12-30
**Document Type:** Performance Test Inventory & Gap Analysis
**Confidence Level:** High (based on source code review)
**Status:** Ready for team review and prioritization
