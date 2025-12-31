# Performance Thresholds Documentation

Comprehensive documentation of performance thresholds and SLAs for the Residency Scheduler application.

## Table of Contents

- [Overview](#overview)
- [Threshold Philosophy](#threshold-philosophy)
- [Global Thresholds](#global-thresholds)
- [API-Specific Thresholds](#api-specific-thresholds)
- [Test Type Thresholds](#test-type-thresholds)
- [Custom Metrics Thresholds](#custom-metrics-thresholds)
- [Setting Thresholds](#setting-thresholds)
- [Threshold Violations](#threshold-violations)

## Overview

Thresholds define acceptable performance criteria. Tests fail if thresholds are not met, making them critical for maintaining SLAs and detecting performance regressions.

### Threshold Format

k6 thresholds use this format:

```javascript
{
  'metric_name': ['condition1', 'condition2']
}
```

Examples:
- `'http_req_duration': ['p(95)<500']` - 95th percentile < 500ms
- `'http_req_failed': ['rate<0.01']` - Error rate < 1%
- `'checks': ['rate>0.95']` - 95% of checks must pass

## Threshold Philosophy

### Production SLA Targets

Our production SLAs are based on:
1. **User Experience**: Keep interfaces responsive
2. **ACGME Compliance**: Critical operations must complete reliably
3. **Industry Standards**: Healthcare application benchmarks
4. **Cost Optimization**: Balance performance vs. infrastructure cost

### Percentiles Explained

| Percentile | Meaning | When to Use |
|------------|---------|-------------|
| **P50 (Median)** | 50% of requests are faster | Typical user experience |
| **P90** | 90% of requests are faster | Common case threshold |
| **P95** | 95% of requests are faster | SLA threshold |
| **P99** | 99% of requests are faster | Outlier detection |
| **Max** | Slowest request | Absolute worst case |

**Rule of Thumb**: Set SLA thresholds at P95, monitor P99 for degradation.

## Global Thresholds

### Standard Load Test Thresholds

Applied to `load-test.js`:

```javascript
{
  // Response time
  http_req_duration: [
    'p(90)<500',   // 90% of requests < 500ms
    'p(95)<800',   // 95% of requests < 800ms
    'p(99)<1500'   // 99% of requests < 1.5s
  ],

  // Error rate
  http_req_failed: ['rate<0.01'],  // < 1% errors

  // Server processing time
  http_req_waiting: ['p(95)<600'],  // < 600ms

  // Connection time
  http_req_connecting: ['p(95)<100'],  // < 100ms

  // Checks (assertions)
  checks: ['rate>0.98'],  // > 98% pass

  // Throughput
  data_received: ['rate>1000000'],  // > 1MB/s
  data_sent: ['rate>100000']  // > 100KB/s
}
```

### Justification

- **Response Time**: Based on Nielsen's usability research (< 1s feels instant)
- **Error Rate**: Healthcare systems require high reliability
- **Checks**: Balance between strict validation and real-world conditions

## API-Specific Thresholds

Different endpoints have different performance characteristics.

### CRUD Operations

#### List Operations (Simple)
```javascript
{
  'http_req_duration{name:list_persons}': ['p(95)<300']  // 300ms
}
```

**Rationale**: Simple queries with pagination should be fast.

**Examples**:
- `GET /api/v1/persons?limit=20`
- `GET /api/v1/rotations?limit=20`
- `GET /api/v1/blocks?limit=30`

#### List Operations (Complex with Filters)
```javascript
{
  'http_req_duration{name:list_assignments}': ['p(95)<500']  // 500ms
}
```

**Rationale**: Complex joins and filters take longer.

**Examples**:
- `GET /api/v1/assignments?person_id=X&date_range=Y`
- `GET /api/v1/swaps?status=PENDING&sort=created_at`

#### Create Operations
```javascript
{
  'http_req_duration{name:create}': ['p(95)<500']  // 500ms
}
```

**Rationale**: Write operations + validation logic.

#### Update Operations
```javascript
{
  'http_req_duration{name:update}': ['p(95)<500']  // 500ms
}
```

#### Delete Operations
```javascript
{
  'http_req_duration{name:delete}': ['p(95)<300']  // 300ms
}
```

**Rationale**: Deletes are typically fast (single row + cascade).

### Business Logic Operations

#### Schedule Generation
```javascript
{
  'http_req_duration{name:generate_schedule}': [
    'p(95)<10000',  // 10 seconds
    'p(99)<20000'   // 20 seconds
  ]
}
```

**Rationale**:
- Computationally expensive (constraint solving)
- Users understand complex operations take time
- 10s threshold keeps UI responsive with progress indicators

**Acceptable**: 5-10 seconds
**Warning**: 10-15 seconds
**Critical**: > 15 seconds

#### Schedule Validation
```javascript
{
  'http_req_duration{name:validate_schedule}': ['p(95)<2000']  // 2s
}
```

**Rationale**: Validation checks multiple constraints but should be faster than generation.

#### ACGME Compliance Checks
```javascript
{
  'http_req_duration{name:compliance_check}': ['p(95)<1500']  // 1.5s
}
```

**Rationale**: Critical for regulatory compliance, must be thorough but reasonably fast.

#### Work Hours Calculation
```javascript
{
  'http_req_duration{name:work_hours}': ['p(95)<500']  // 500ms
}
```

**Rationale**: Simple aggregation query.

### Resilience Operations

#### N-1 Contingency Analysis
```javascript
{
  'http_req_duration{name:n_minus_one}': ['p(95)<3000']  // 3s
}
```

**Rationale**: Complex graph analysis, acceptable to take a few seconds.

#### Utilization Calculation
```javascript
{
  'http_req_duration{name:utilization}': ['p(95)<1000']  // 1s
}
```

#### Resilience Metrics Dashboard
```javascript
{
  'http_req_duration{name:resilience_metrics}': ['p(95)<2000']  // 2s
}
```

### Swap Operations

#### Swap Matching
```javascript
{
  'http_req_duration{name:match_swap}': ['p(95)<1000']  // 1s
}
```

**Rationale**: Finding compatible swaps requires searching, but should be interactive.

#### Swap Execution
```javascript
{
  'http_req_duration{name:execute_swap}': ['p(95)<500']  // 500ms
}
```

**Rationale**: Simple database transaction.

#### Swap Rollback
```javascript
{
  'http_req_duration{name:rollback_swap}': ['p(95)<500']  // 500ms
}
```

### Authentication

#### Login
```javascript
{
  'http_req_duration{name:login}': ['p(95)<1000']  // 1s
}
```

**Rationale**: Password hashing is computationally expensive (intentionally).

#### Token Refresh
```javascript
{
  'http_req_duration{name:refresh_token}': ['p(95)<300']  // 300ms
}
```

**Rationale**: No password hashing, just JWT validation.

## Test Type Thresholds

### Smoke Test Thresholds

**Purpose**: Quick validation, relaxed thresholds.

```javascript
{
  http_req_duration: [
    'p(95)<1000',  // 1 second
    'p(99)<2000'   // 2 seconds
  ],
  http_req_failed: ['rate<0.05'],  // < 5% errors
  checks: ['rate>0.95']  // > 95% checks pass
}
```

**Justification**: Smoke tests run with minimal load, so we accept higher latency but still validate functionality.

### Load Test Thresholds

**Purpose**: Production SLA validation.

```javascript
{
  http_req_duration: [
    'p(90)<500',   // 500ms
    'p(95)<800',   // 800ms
    'p(99)<1500'   // 1.5s
  ],
  http_req_failed: ['rate<0.01'],  // < 1% errors
  checks: ['rate>0.98']  // > 98% checks pass
}
```

**Justification**: Strict thresholds representing our production SLA.

### Stress Test Thresholds

**Purpose**: Find limits, expect degradation.

```javascript
{
  http_req_duration: [
    'p(90)<1000',   // 1s
    'p(95)<2000',   // 2s
    'p(99)<5000'    // 5s
  ],
  http_req_failed: ['rate<0.05'],  // < 5% errors (relaxed)
  checks: ['rate>0.90']  // > 90% checks pass
}
```

**Justification**: Under stress, we expect some degradation. The goal is to identify breaking points, not enforce strict SLAs.

### Spike Test Thresholds

**Purpose**: Test elasticity and recovery.

```javascript
{
  http_req_duration: [
    'p(90)<2000',   // 2s (during spike)
    'p(95)<3000',   // 3s
    'p(99)<8000'    // 8s
  ],
  http_req_failed: ['rate<0.10'],  // < 10% errors during spike
  checks: ['rate>0.85'],  // > 85% checks pass

  // Recovery phase
  'http_req_duration{scenario:recovery}': ['p(95)<500']  // Quick recovery
}
```

**Justification**: Allow degradation during spike, but verify quick recovery afterward.

### Soak Test Thresholds

**Purpose**: Long-term stability, detect memory leaks.

```javascript
{
  http_req_duration: [
    'p(95)<1000',   // Should not degrade over time
    'p(99)<2000'
  ],
  http_req_failed: ['rate<0.02'],  // < 2% errors
  checks: ['rate>0.95'],

  // Memory stability
  memory_usage: ['max<80'],  // < 80% memory
  connection_pool: ['value<100']  // < 100 connections
}
```

**Justification**: Performance should remain consistent over time. Increasing latency suggests memory leaks or resource exhaustion.

## Custom Metrics Thresholds

### Database Performance

```javascript
{
  db_query_duration: [
    'p(95)<100',  // Most queries < 100ms
    'p(99)<500'   // Complex queries < 500ms
  ],
  db_connections_active: ['max<80'],  // Max 80 active connections
  db_transactions_failed: ['rate<0.01']  // < 1% transaction failures
}
```

### Cache Performance

```javascript
{
  cache_hit_rate: ['rate>0.80'],  // > 80% cache hits
  cache_response_time: ['p(95)<10'],  // < 10ms
  cache_miss_recovery: ['p(95)<200']  // < 200ms to populate cache
}
```

### Rate Limiting

```javascript
{
  'http_req_duration{status:429}': ['count>0'],  // Expect some rate limiting
  rate_limit_triggered: ['rate>0.80'],  // In rate limit tests, should trigger
  rate_limit_recovery: ['p(95)<1000']  // < 1s to recover
}
```

## Setting Thresholds

### How to Choose Thresholds

1. **Baseline First**: Run tests without thresholds to establish baseline
2. **User Research**: Understand user tolerance (< 1s feels instant)
3. **Business Requirements**: Map to SLA contracts
4. **Iterative Refinement**: Tighten as you optimize

### Threshold Setting Process

```bash
# Step 1: Establish baseline (no thresholds)
k6 run k6/scenarios/load-test.js --out json=baseline.json

# Step 2: Analyze results
python scripts/analyze-results.py baseline.json

# Step 3: Set thresholds at P95 + 20% buffer
# If P95 was 400ms, set threshold at 480ms

# Step 4: Validate thresholds pass
k6 run k6/scenarios/load-test.js

# Step 5: Tighten gradually
# Reduce threshold by 10% each sprint as you optimize
```

### Progressive Threshold Tightening

| Phase | P95 Target | Error Rate | Notes |
|-------|------------|------------|-------|
| **MVP** | < 2000ms | < 5% | Initial launch |
| **Beta** | < 1000ms | < 2% | After initial optimizations |
| **Production** | < 800ms | < 1% | Current target |
| **Optimized** | < 500ms | < 0.5% | Future goal |

## Threshold Violations

### When Thresholds Fail

k6 exits with code 99 when thresholds fail:

```bash
✗ http_req_duration...........: p(95)=1200ms (threshold: p(95)<800ms)
```

### Troubleshooting Violations

#### 1. Response Time Violations

**Symptoms**: `http_req_duration` exceeds threshold

**Investigation**:
```bash
# Check which endpoints are slow
k6 run --http-debug k6/scenarios/load-test.js | grep "p(95)"

# Profile backend
docker-compose logs backend | grep -i "slow"

# Check database
docker-compose exec db psql -U scheduler -c "
  SELECT query, calls, mean_exec_time
  FROM pg_stat_statements
  ORDER BY mean_exec_time DESC
  LIMIT 10;
"
```

**Solutions**:
- Add database indexes
- Optimize N+1 queries
- Implement caching
- Add database connection pooling

#### 2. Error Rate Violations

**Symptoms**: `http_req_failed` exceeds threshold

**Investigation**:
```bash
# Count errors by status code
cat results.json | jq '.metrics.http_reqs.values | group_by(.tags.status) | map({status: .[0].tags.status, count: length})'

# Check backend errors
docker-compose logs backend | grep -i error
```

**Solutions**:
- Fix application bugs
- Handle edge cases
- Improve input validation
- Add retry logic

#### 3. Check Violations

**Symptoms**: `checks` threshold not met

**Investigation**:
```bash
# See which checks failed
k6 run --verbose k6/scenarios/load-test.js | grep "✗"

# Review check logic
# Failed checks usually indicate application bugs
```

**Solutions**:
- Fix assertion logic
- Handle null/undefined cases
- Improve error responses
- Update test expectations

### Temporary Threshold Adjustments

Sometimes you need to temporarily relax thresholds:

```javascript
// For new features (not yet optimized)
const isNewFeature = true;
const threshold = isNewFeature ? 'p(95)<2000' : 'p(95)<800';

export const options = {
  thresholds: {
    http_req_duration: [threshold]
  }
};
```

**When acceptable**:
- New features (first 2 sprints)
- Known infrastructure issues
- Test environment limitations

**Not acceptable**:
- Production regressions
- Avoiding optimization work
- Long-term workarounds

## Monitoring Threshold Trends

### Track Over Time

```bash
# Save baseline
k6 run k6/scenarios/load-test.js --out json=results/baseline-2024-01-01.json

# Compare weekly
python scripts/compare-baselines.py \
  results/baseline-2024-01-01.json \
  results/current.json
```

### Regression Detection

```python
# scripts/performance-regression-detector.py

def detect_regression(current_p95, baseline_p95, threshold_pct=10):
    """
    Detect if performance regressed by more than threshold_pct
    """
    regression_pct = ((current_p95 - baseline_p95) / baseline_p95) * 100

    if regression_pct > threshold_pct:
        print(f"REGRESSION: {regression_pct:.1f}% slower than baseline")
        return True

    return False
```

### CI/CD Threshold Enforcement

```yaml
# .github/workflows/load-tests.yml

- name: Run load test
  run: k6 run k6/scenarios/load-test.js

- name: Check thresholds
  run: |
    if [ $? -eq 99 ]; then
      echo "Threshold violations detected!"
      exit 1
    fi
```

## Best Practices

### 1. Always Set Thresholds

Never run tests without thresholds in CI/CD:

```javascript
// ❌ Bad: No thresholds
export const options = {
  vus: 50,
  duration: '5m'
};

// ✅ Good: Clear thresholds
export const options = {
  vus: 50,
  duration: '5m',
  thresholds: {
    http_req_duration: ['p(95)<800'],
    http_req_failed: ['rate<0.01']
  }
};
```

### 2. Use Tags for Granular Thresholds

```javascript
// Tag requests
session.get('/api/schedules/generate', {
  name: 'generate_schedule',
  endpoint: 'schedules'
});

// Specific threshold for expensive operation
export const options = {
  thresholds: {
    'http_req_duration{name:generate_schedule}': ['p(95)<10000'],
    'http_req_duration': ['p(95)<800']  // General threshold
  }
};
```

### 3. Document Threshold Changes

When changing thresholds, document why:

```javascript
export const options = {
  thresholds: {
    // Relaxed from 500ms to 800ms on 2024-01-15
    // Reason: Added ACGME compliance validation to endpoint
    // TODO: Optimize to get back under 500ms
    http_req_duration: ['p(95)<800']
  }
};
```

### 4. Review Quarterly

Schedule quarterly threshold reviews:
- Are we meeting SLAs?
- Can we tighten thresholds?
- Do thresholds reflect current infrastructure?
- Are new features impacting performance?

## Conclusion

Thresholds are not arbitrary numbers—they represent our commitment to user experience and system reliability. Set them based on data, enforce them rigorously, and adjust them as you optimize.

**Remember**:
- Start conservative
- Tighten progressively
- Never compromise user experience
- Document all changes
