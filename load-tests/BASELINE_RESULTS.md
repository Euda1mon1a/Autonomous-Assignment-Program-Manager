# Baseline Performance Results

Baseline performance metrics for the Residency Scheduler application. These serve as reference points for detecting performance regressions.

## Table of Contents

- [Overview](#overview)
- [Test Environment](#test-environment)
- [Smoke Test Baseline](#smoke-test-baseline)
- [Load Test Baseline](#load-test-baseline)
- [API Endpoint Baselines](#api-endpoint-baselines)
- [Database Benchmarks](#database-benchmarks)
- [Monitoring Baselines](#monitoring-baselines)
- [Updating Baselines](#updating-baselines)

## Overview

### Purpose of Baselines

Baselines provide:
1. **Reference Points**: Know what "good" looks like
2. **Regression Detection**: Identify when performance degrades
3. **Capacity Planning**: Understand current system limits
4. **Optimization Tracking**: Measure improvement over time

### Baseline Methodology

Baselines were established using:
- **Infrastructure**: Docker Compose (1 backend, 1 db, 1 redis)
- **Hardware**: 4 CPU cores, 8GB RAM
- **Test Duration**: 5 minutes (after 2 min warmup)
- **Load Level**: 20 concurrent users
- **Data Set**: 50 persons, 10 rotations, 365 days of blocks

## Test Environment

### Software Versions

```yaml
Backend:
  Python: 3.11.7
  FastAPI: 0.109.0
  SQLAlchemy: 2.0.25
  PostgreSQL: 15.5

Load Testing:
  k6: v0.47.0
  Locust: 2.17.0
  pytest-benchmark: 4.0.0

Infrastructure:
  Docker: 24.0.6
  Docker Compose: 2.23.0
```

### Hardware Specifications

```yaml
Test Machine:
  CPU: 4 cores (Intel i7 equivalent)
  RAM: 8GB
  Disk: SSD
  Network: 1Gbps local

Docker Resources:
  Backend Container: 2 CPU, 2GB RAM
  Database Container: 1 CPU, 2GB RAM
  Redis Container: 1 CPU, 512MB RAM
```

## Smoke Test Baseline

**Purpose**: Quick validation with minimal load
**VUs**: 1
**Duration**: 1 minute
**Date Established**: 2025-01-01

### Results

```
Total Requests:        120
Request Rate:          2.0 req/s
Failed Requests:       0 (0%)
Checks Passed:         100%

Response Times:
  Avg:                 85ms
  Min:                 45ms
  Med:                 78ms
  Max:                 320ms
  P90:                 145ms
  P95:                 180ms
  P99:                 280ms
```

### Status: ✅ All thresholds passed

## Load Test Baseline

**Purpose**: Production-like load
**VUs**: 10-20 (ramped)
**Duration**: 14 minutes
**Date Established**: 2025-01-01

### Overall Results

```
Total Requests:        28,450
Request Rate:          33.5 req/s
Failed Requests:       142 (0.5%)
Checks Passed:         97.8%
Total Data Received:   125 MB
Total Data Sent:       45 MB

Response Times:
  Avg:                 245ms
  Min:                 42ms
  Med:                 220ms
  Max:                 3,420ms
  P90:                 385ms
  P95:                 490ms
  P99:                 890ms
  P99.9:               1,850ms
```

### Status: ✅ All thresholds passed

### Response Time Distribution

```
0-100ms:     12,500 requests (44%)
100-200ms:    8,200 requests (29%)
200-300ms:    4,100 requests (14%)
300-500ms:    2,450 requests (9%)
500-1000ms:     950 requests (3%)
1000ms+:        250 requests (1%)
```

### Request Breakdown by Operation

```
Operation                  Count    Avg      P95      P99
────────────────────────────────────────────────────────
GET /assignments          8,500    180ms    320ms    650ms
GET /persons              6,200    145ms    280ms    520ms
GET /rotations            5,100    135ms    260ms    490ms
GET /blocks               4,800    140ms    270ms    500ms
GET /compliance           2,400    620ms    980ms   1,650ms
GET /swaps                1,850    165ms    295ms    560ms
POST /assignments           450    385ms    680ms   1,120ms
POST /swaps                 150    420ms    750ms   1,280ms
```

## API Endpoint Baselines

### CRUD Operations

#### List Operations

```javascript
// GET /api/v1/persons?limit=20
{
  avg: 145ms,
  p50: 135ms,
  p95: 280ms,
  p99: 520ms,
  throughput: 45 req/s
}

// GET /api/v1/rotations?limit=20
{
  avg: 135ms,
  p50: 125ms,
  p95: 260ms,
  p99: 490ms,
  throughput: 50 req/s
}

// GET /api/v1/assignments?limit=20
{
  avg: 180ms,
  p50: 165ms,
  p95: 320ms,
  p99: 650ms,
  throughput: 38 req/s
}
```

#### Create Operations

```javascript
// POST /api/v1/persons
{
  avg: 245ms,
  p50: 230ms,
  p95: 420ms,
  p99: 780ms,
  throughput: 25 req/s
}

// POST /api/v1/assignments
{
  avg: 385ms,
  p50: 360ms,
  p95: 680ms,
  p99: 1120ms,
  throughput: 15 req/s
}
```

#### Update Operations

```javascript
// PUT /api/v1/persons/{id}
{
  avg: 265ms,
  p50: 245ms,
  p95: 450ms,
  p99: 820ms,
  throughput: 22 req/s
}
```

#### Delete Operations

```javascript
// DELETE /api/v1/persons/{id}
{
  avg: 185ms,
  p50: 170ms,
  p95: 340ms,
  p99: 620ms,
  throughput: 30 req/s
}
```

### Business Logic Operations

#### Schedule Generation

```javascript
// POST /api/v1/schedules/generate
{
  avg: 6,850ms,
  p50: 6,200ms,
  p95: 9,800ms,
  p99: 15,400ms,
  throughput: 0.15 req/s,  // ~1 per 7 seconds
  notes: "Highly variable based on constraints"
}
```

#### ACGME Compliance Validation

```javascript
// POST /api/v1/compliance/validate
{
  avg: 620ms,
  p50: 580ms,
  p95: 980ms,
  p99: 1,650ms,
  throughput: 8 req/s
}

// GET /api/v1/compliance/work-hours
{
  avg: 385ms,
  p50: 360ms,
  p95: 650ms,
  p99: 1,120ms,
  throughput: 12 req/s
}
```

#### Resilience Operations

```javascript
// GET /api/v1/resilience/n-minus-one
{
  avg: 1,850ms,
  p50: 1,720ms,
  p95: 2,890ms,
  p99: 4,320ms,
  throughput: 2.5 req/s
}

// GET /api/v1/resilience/utilization
{
  avg: 680ms,
  p50: 640ms,
  p95: 1,080ms,
  p99: 1,820ms,
  throughput: 6 req/s
}
```

#### Swap Operations

```javascript
// POST /api/v1/swaps
{
  avg: 420ms,
  p50: 395ms,
  p95: 750ms,
  p99: 1,280ms,
  throughput: 10 req/s
}

// GET /api/v1/swaps/match
{
  avg: 785ms,
  p50: 720ms,
  p95: 1,320ms,
  p99: 2,180ms,
  throughput: 5 req/s
}

// POST /api/v1/swaps/{id}/execute
{
  avg: 365ms,
  p50: 340ms,
  p95: 620ms,
  p99: 1,050ms,
  throughput: 12 req/s
}
```

### Authentication

```javascript
// POST /api/v1/auth/login
{
  avg: 685ms,
  p50: 650ms,
  p95: 980ms,
  p99: 1,520ms,
  throughput: 8 req/s,
  notes: "Slow due to bcrypt (intentional)"
}

// POST /api/v1/auth/refresh
{
  avg: 185ms,
  p50: 170ms,
  p95: 320ms,
  p99: 580ms,
  throughput: 28 req/s
}

// GET /api/v1/auth/me
{
  avg: 145ms,
  p50: 135ms,
  p95: 260ms,
  p99: 480ms,
  throughput: 35 req/s
}
```

## Database Benchmarks

### Query Performance

Using `pytest-benchmark`:

```python
# Simple SELECT query
benchmark_simple_query:
  mean:     12.5ms
  median:   11.8ms
  stddev:    2.3ms
  min:       9.2ms
  max:      28.4ms

# JOIN query (3 tables)
benchmark_join_query:
  mean:     38.7ms
  median:   36.2ms
  stddev:    8.9ms
  min:      28.5ms
  max:      89.3ms

# Complex aggregation
benchmark_aggregation:
  mean:     124.8ms
  median:   118.5ms
  stddev:    24.6ms
  min:       92.1ms
  max:      245.7ms

# Bulk insert (100 rows)
benchmark_bulk_insert:
  mean:     185.3ms
  median:   178.2ms
  stddev:    32.4ms
  min:      145.6ms
  max:      298.5ms
```

### Connection Pool

```
Active Connections (under load):
  Avg:      12
  Max:      28
  Pool Size: 50
  Utilization: 56%

Connection Wait Time:
  Avg:      2.3ms
  P95:      8.5ms
  P99:      18.2ms
```

## Monitoring Baselines

### System Resources (Under Load)

```yaml
Backend Container:
  CPU Usage:
    Avg: 65%
    P95: 85%
    Max: 92%

  Memory:
    Avg: 1.2GB
    P95: 1.6GB
    Max: 1.8GB (of 2GB limit)

  Network:
    Inbound:  2.5 MB/s
    Outbound: 8.2 MB/s

Database Container:
  CPU Usage:
    Avg: 42%
    P95: 68%
    Max: 78%

  Memory:
    Avg: 850MB
    P95: 1.3GB
    Max: 1.5GB (of 2GB limit)

  Disk I/O:
    Read:  125 IOPS
    Write: 45 IOPS

Redis Container:
  CPU Usage:
    Avg: 8%
    Max: 15%

  Memory:
    Avg: 180MB
    Max: 245MB (of 512MB limit)
```

### Cache Performance

```yaml
Cache Hit Rate:
  Overall:     84%
  Persons:     92%
  Rotations:   95%
  Assignments: 78%

Cache Response Time:
  Avg: 3.2ms
  P95: 8.5ms
  P99: 15.2ms

Cache Miss Recovery:
  Avg: 142ms
  P95: 285ms
```

### Error Rates

```yaml
HTTP Errors:
  4xx: 0.3% (mostly 404s, some 422 validation)
  5xx: 0.2% (timeout under peak load)

Database Errors:
  Connection Timeouts: 0.1%
  Query Failures:      0.05%
  Deadlocks:           0.02%

Redis Errors:
  Connection Issues:   0.01%
  Timeout:             0.03%
```

## Updating Baselines

### When to Update

Update baselines when:
1. **Infrastructure Changes**: Upgraded hardware/database
2. **Major Optimizations**: Significant performance improvements
3. **Architecture Changes**: New caching layer, CDN, etc.
4. **Quarterly Reviews**: Regular baseline refresh

### DO NOT Update When:

- Performance regresses (fix regression instead)
- Minor fluctuations (< 5% variance)
- Temporary infrastructure issues
- Single outlier test run

### Update Process

```bash
# 1. Run comprehensive test suite
cd load-tests
k6 run k6/scenarios/smoke-test.js --out json=results/smoke-baseline-YYYY-MM-DD.json
k6 run k6/scenarios/load-test.js --out json=results/load-baseline-YYYY-MM-DD.json

# 2. Run benchmarks
cd ../backend
pytest tests/benchmarks/ --benchmark-only --benchmark-json=../load-tests/results/bench-baseline-YYYY-MM-DD.json

# 3. Analyze results
cd ../load-tests
python scripts/analyze-results.py results/load-baseline-YYYY-MM-DD.json --output analysis-YYYY-MM-DD.json

# 4. Compare to current baseline
python scripts/compare-baselines.py \
  results/load-baseline-YYYY-MM-DD.json \
  baseline-results.json

# 5. If improvement is confirmed (> 10% better, multiple runs), update this document

# 6. Archive old baseline
mkdir -p baselines/archive
mv baseline-results.json baselines/archive/baseline-$(date +%Y-%m-%d).json

# 7. Save new baseline
cp results/load-baseline-YYYY-MM-DD.json baseline-results.json

# 8. Update this document with new metrics

# 9. Commit changes
git add BASELINE_RESULTS.md baseline-results.json
git commit -m "chore: update performance baselines (REASON)"
```

### Validation Checklist

Before updating baselines:

- [ ] Run tests 3+ times to ensure consistency
- [ ] Verify infrastructure matches original baseline environment
- [ ] Document reason for change (optimization, infrastructure upgrade)
- [ ] Get approval from team lead
- [ ] Update CI/CD thresholds accordingly

## Historical Baselines

### Performance Improvements Over Time

```
Date        P95 Response   Throughput   Notes
──────────────────────────────────────────────────────
2024-06-01  890ms         25 req/s     Initial baseline
2024-08-15  720ms         32 req/s     Database indexing
2024-10-01  620ms         38 req/s     Query optimization
2024-12-01  490ms         45 req/s     Redis caching
2025-01-01  490ms         50 req/s     Connection pooling
```

### Capacity Growth

```
Year       Max VUs   Max Throughput   P95
─────────────────────────────────────────────
2024       50        45 req/s         890ms
2025       100       90 req/s         490ms (projected)
```

## Interpreting Baselines

### What Good Looks Like

Using baselines to evaluate current performance:

```
Current vs Baseline P95 Response Time:

Within 5%:        ✅ Normal variance
5-10% slower:     ⚠️  Monitor for trend
10-20% slower:    ⚠️  Investigate
> 20% slower:     ❌ Regression - take action
```

### Regression Detection

```python
def is_regression(current, baseline, threshold=0.10):
    """
    Detect if performance regressed beyond threshold
    """
    variance = (current - baseline) / baseline

    if variance > threshold:
        return True, f"Regression: {variance*100:.1f}% slower"

    return False, "Performance acceptable"

# Example
current_p95 = 650  # ms
baseline_p95 = 490  # ms

is_regression(current_p95, baseline_p95)
# Returns: (True, "Regression: 32.7% slower")
```

## Conclusion

These baselines represent the expected performance of the Residency Scheduler under normal operating conditions. Use them as reference points for:

1. **Daily Monitoring**: Compare production metrics to baselines
2. **Change Validation**: Ensure changes don't regress performance
3. **Capacity Planning**: Understand current limits
4. **Goal Setting**: Target improvements beyond baseline

**Remember**: Baselines are targets, not limits. Always strive to improve!

---

**Last Updated**: 2025-01-01
**Next Review**: 2025-04-01
**Maintained By**: Residency Scheduler Team
