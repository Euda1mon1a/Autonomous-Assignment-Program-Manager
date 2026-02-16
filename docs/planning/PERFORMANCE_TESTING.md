# Performance Testing Guide

Comprehensive guide to performance testing, benchmarking, profiling, and monitoring for the Residency Scheduler application.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Benchmark Scripts](#benchmark-scripts)
- [Profiling Tools](#profiling-tools)
- [Monitoring Scripts](#monitoring-scripts)
- [Load Testing](#load-testing)
- [Configuration](#configuration)
- [CI/CD Integration](#cicd-integration)
- [Interpreting Results](#interpreting-results)
- [Troubleshooting](#troubleshooting)

---

## Overview

The performance testing infrastructure consists of four main components:

1. **Benchmarks** (`backend/benchmarks/`) - Measure specific operation performance
2. **Profiling** (`backend/profiling/`) - Identify bottlenecks and optimization opportunities
3. **Monitoring** (`scripts/monitoring/`) - Track metrics over time and detect regressions
4. **Load Tests** (`load-tests/scenarios/`) - Test system behavior under realistic load

---

## Quick Start

### Run Quick Benchmark Suite

```bash
# From project root
cd backend
python -m benchmarks --quick --verbose

# Results saved to: benchmark_results/
```

### Run Single Benchmark

```bash
# Schedule generation benchmark
python -m benchmarks.schedule_generation_bench --residents 50 --weeks 4

# ACGME validation benchmark
python -m benchmarks.acgme_validation_bench --residents 100 --weeks 4
```

### Profile an Operation

```bash
# Profile schedule generation
cd backend
python -m profiling.profile_scheduler --residents 50 --weeks 4

# Results saved to: profiling_results/
```

### Run Load Test

```bash
# From load-tests directory
cd load-tests
npm install

# Run peak load scenario
npm run test:load

# Or run specific scenario
k6 run scenarios/peak_load_scenario.js
```

---

## Benchmark Scripts

Location: `backend/benchmarks/`

### Available Benchmarks

| Benchmark | File | Purpose |
|-----------|------|---------|
| **Schedule Generation** | `schedule_generation_bench.py` | Measure schedule generation time |
| **ACGME Validation** | `acgme_validation_bench.py` | Measure compliance checking speed |
| **Database Queries** | `database_query_bench.py` | Measure query performance |
| **Resilience Calculations** | `resilience_calculation_bench.py` | Measure resilience metrics |
| **Swap Matching** | `swap_matching_bench.py` | Measure swap matching algorithm |
| **Concurrent Requests** | `concurrent_requests_bench.py` | Measure API throughput |
| **Memory Usage** | `memory_usage_bench.py` | Track memory consumption |
| **Startup Time** | `startup_time_bench.py` | Measure app initialization |

### Usage Examples

#### Schedule Generation Benchmark

```bash
# Single configuration
python -m benchmarks.schedule_generation_bench \
  --residents 50 \
  --weeks 4 \
  --iterations 5 \
  --verbose

# Full suite (multiple program sizes)
python -m benchmarks.schedule_generation_bench --suite
```

#### ACGME Validation Benchmark

```bash
# Test specific validation type
python -m benchmarks.acgme_validation_bench \
  --residents 100 \
  --weeks 4 \
  --rule full \
  --iterations 10

# Full suite
python -m benchmarks.acgme_validation_bench --suite --verbose
```

#### Database Query Benchmark

```bash
# Simple queries
python -m benchmarks.database_query_bench \
  --query-type simple \
  --iterations 100

# Join queries
python -m benchmarks.database_query_bench \
  --query-type joins \
  --iterations 50

# Bulk operations
python -m benchmarks.database_query_bench \
  --query-type bulk \
  --batch-size 500 \
  --iterations 10

# Full suite
python -m benchmarks.database_query_bench --suite
```

### Benchmark Output

All benchmarks generate JSON output with the following structure:

```json
{
  "benchmark_name": "schedule_generation_50res_4wk",
  "category": "schedule_generation",
  "timestamp": "2025-01-01 12:00:00",
  "duration_seconds": 45.2,
  "iterations": 3,
  "avg_duration": 15.1,
  "min_duration": 14.5,
  "max_duration": 15.8,
  "std_deviation": 0.6,
  "throughput": 3.3,
  "memory_mb": 420,
  "peak_memory_mb": 480,
  "metadata": {
    "num_residents": 50,
    "num_weeks": 4,
    "success_rate": "100%"
  }
}
```

Results are saved to `benchmark_results/` directory.

---

## Profiling Tools

Location: `backend/profiling/`

### Available Profilers

| Profiler | File | Purpose |
|----------|------|---------|
| **Scheduler Profiler** | `profile_scheduler.py` | Profile schedule generation |
| **Query Profiler** | `profile_queries.py` | Profile database operations |
| **API Profiler** | `profile_api_endpoints.py` | Profile request handling |
| **Background Tasks** | `profile_background_tasks.py` | Profile Celery tasks |
| **Flame Graphs** | `flame_graph_generator.py` | Generate visual profiling |

### Usage Examples

#### Profile Schedule Generation

```bash
python -m profiling.profile_scheduler \
  --residents 100 \
  --weeks 4 \
  --sort cumulative

# Results include:
# - Function-level timing
# - Call counts
# - Cumulative time spent
# - Bottleneck identification
```

#### Profile Database Queries

```bash
# Profile simple queries
python -m profiling.profile_queries --query-type simple

# Profile joins
python -m profiling.profile_queries --query-type joins

# Profile all query types
python -m profiling.profile_queries --query-type all
```

#### Generate Flame Graph

```bash
# Using py-spy (recommended)
sudo python -m profiling.flame_graph_generator \
  --target schedule \
  --method pyspy \
  --duration 30

# Convert existing pstats file
python -m profiling.flame_graph_generator \
  --pstats profiling_results/schedule_generation.pstats
```

**Note:** Flame graph generation with py-spy requires `sudo` on Linux. Install py-spy:

```bash
pip install py-spy
```

### Interpreting Profiling Results

Profiling output shows:

1. **Function name** - Which function was called
2. **ncalls** - Number of times called
3. **tottime** - Total time spent in function (excluding subfunctions)
4. **cumtime** - Cumulative time (including subfunctions)
5. **percall** - Average time per call

Look for:
- High `cumtime` functions (main bottlenecks)
- High `ncalls` with low `percall` (opportunities for caching)
- Unexpected function calls (inefficient code paths)

---

## Monitoring Scripts

Location: `scripts/monitoring/`

### Available Scripts

| Script | Purpose |
|--------|---------|
| `collect_metrics.py` | Gather performance metrics |
| `generate_report.py` | Create performance reports |
| `compare_benchmarks.py` | Compare benchmark runs |
| `alert_on_regression.py` | Detect performance regressions |

### Collect Metrics

```bash
# Collect once
python scripts/monitoring/collect_metrics.py \
  --output metrics/performance_metrics.json

# Continuous collection (every 5 minutes)
python scripts/monitoring/collect_metrics.py \
  --continuous \
  --interval 300

# Print to stdout instead of saving
python scripts/monitoring/collect_metrics.py --print
```

Collected metrics include:
- System resources (CPU, memory, disk)
- Database statistics (size, connections, table sizes)
- Latest benchmark results

### Generate Reports

```bash
# Generate text report
python scripts/monitoring/generate_report.py \
  --metrics metrics/performance_metrics.json \
  --format text

# Generate HTML report
python scripts/monitoring/generate_report.py \
  --format html \
  --output reports/performance.html

# Generate Markdown report
python scripts/monitoring/generate_report.py \
  --format markdown \
  --output reports/PERFORMANCE.md
```

### Compare Benchmarks

```bash
# Compare two specific runs
python scripts/monitoring/compare_benchmarks.py \
  --baseline benchmark_results/baseline.json \
  --current benchmark_results/current.json

# Compare last 7 runs in directory
python scripts/monitoring/compare_benchmarks.py \
  --dir benchmark_results/ \
  --last 7
```

### Detect Regressions

```bash
# Check for regressions (15% threshold)
python scripts/monitoring/alert_on_regression.py \
  --dir benchmark_results/ \
  --threshold 15

# CI mode (exit code 1 on regression)
python scripts/monitoring/alert_on_regression.py \
  --dir benchmark_results/ \
  --threshold 10 \
  --ci

# Send Slack alert on regression
python scripts/monitoring/alert_on_regression.py \
  --dir benchmark_results/ \
  --slack-webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## Load Testing

Location: `load-tests/scenarios/`

### Available Scenarios

| Scenario | File | Purpose |
|----------|------|---------|
| **API Baseline** | `api-baseline.js` | Establish baseline metrics |
| **Concurrent Users** | `concurrent-users.js` | Multi-user simulation |
| **Schedule Generation** | `schedule-generation.js` | Schedule generation load |
| **Peak Load** | `peak_load_scenario.js` | Maximum capacity test |
| **Sustained Load** | `sustained_load_scenario.js` | Long-duration stability |
| **Spike Test** | `spike_test_scenario.js` | Sudden traffic spikes |
| **Soak Test** | `soak_test_scenario.js` | 2+ hour endurance test |
| **Auth Security** | `auth-security.js` | Authentication load |
| **Rate Limit Attack** | `rate-limit-attack.js` | Rate limiting validation |

### Setup

```bash
cd load-tests
npm install
```

### Running Load Tests

```bash
# Quick smoke test
npm run test:smoke

# Standard load test
npm run test:load

# Stress test
npm run test:stress

# Run specific scenario
k6 run scenarios/peak_load_scenario.js

# Run with custom options
k6 run --vus 100 --duration 10m scenarios/sustained_load_scenario.js
```

### Load Test Scenarios Explained

#### Peak Load Scenario

**Purpose:** Test behavior at maximum expected load
**Configuration:** 0 → 50 → 100 → 150 → 200 VUs over 22 minutes
**Success Criteria:**
- p95 < 5s even at peak
- Error rate < 10% at 200 VUs
- No system crashes

```bash
k6 run scenarios/peak_load_scenario.js
```

#### Sustained Load Scenario

**Purpose:** Identify memory leaks and gradual degradation
**Configuration:** 50 VUs for 30 minutes
**Success Criteria:**
- Response times remain stable
- No memory growth
- Error rate < 2%

```bash
k6 run scenarios/sustained_load_scenario.js
```

#### Spike Test Scenario

**Purpose:** Test recovery from sudden traffic spikes
**Configuration:** 10 → 200 → 10 VUs (spike in 10 seconds)
**Success Criteria:**
- System doesn't crash
- Error rate < 30% during spike
- Recovery success > 95%

```bash
k6 run scenarios/spike_test_scenario.js
```

#### Soak Test Scenario

**Purpose:** Long-duration test for memory leaks
**Configuration:** 30 VUs for 2+ hours
**Success Criteria:**
- No performance degradation over time
- Memory usage stays flat
- Error rate < 1%

```bash
# 2-hour soak test
k6 run scenarios/soak_test_scenario.js

# Extended 4-hour soak test
k6 run --duration 4h scenarios/soak_test_scenario.js
```

### k6 Cloud Integration

For larger-scale tests, use k6 Cloud:

```bash
# Run on k6 Cloud
k6 cloud scenarios/peak_load_scenario.js

# With custom options
k6 cloud --vus 500 --duration 20m scenarios/sustained_load_scenario.js
```

---

## Configuration

### Benchmark Configuration

File: `benchmark_config.yaml`

```yaml
# Example configuration
schedule_generation:
  enabled: true
  configurations:
    - name: "medium_program"
      residents: 25
      weeks: 4
      iterations: 3
      threshold_seconds: 10.0
```

### Baseline Metrics

File: `baseline_metrics.json`

Contains expected performance baselines for all benchmarks. Used for regression detection.

```json
{
  "benchmarks": {
    "schedule_generation": {
      "medium_program": {
        "avg_duration_seconds": 8.0,
        "p95_duration_seconds": 10.0
      }
    }
  }
}
```

Update baselines after major optimizations:

```bash
# Run benchmarks and save as new baseline
python -m benchmarks --suite
mv benchmark_results/latest.json baseline_metrics.json
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/performance-tests.yml
name: Performance Tests

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  benchmark:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run quick benchmark suite
        run: |
          cd backend
          python -m benchmarks --quick

      - name: Check for regressions
        run: |
          python scripts/monitoring/alert_on_regression.py \
            --dir benchmark_results/ \
            --threshold 15 \
            --ci

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: benchmark_results/
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "Running quick performance benchmarks..."
cd backend
python -m benchmarks --quick

if [ $? -ne 0 ]; then
  echo "❌ Performance benchmarks failed"
  exit 1
fi

echo "✓ Performance benchmarks passed"
```

---

## Interpreting Results

### Performance Metrics

#### Duration Metrics

- **avg_duration**: Average time across all iterations
- **min_duration**: Fastest iteration
- **max_duration**: Slowest iteration
- **p95_duration**: 95th percentile (95% of requests faster than this)
- **p99_duration**: 99th percentile

**Good:** Low standard deviation (consistent performance)
**Bad:** High standard deviation (unpredictable performance)

#### Throughput Metrics

- **operations per second**: How many operations can be performed per second
- **requests per second**: HTTP request rate

**Good:** Linear scaling with resources
**Bad:** Throughput decrease as load increases (indicates bottleneck)

#### Memory Metrics

- **baseline_mb**: Starting memory
- **peak_mb**: Maximum memory used
- **growth_mb**: Memory increase over iterations

**Good:** Growth < 50 MB, no leak detected
**Bad:** Linear growth over iterations (memory leak)

### Regression Detection

Performance regression is detected when:

1. **Duration increases > 10%** from baseline
2. **Throughput decreases > 10%** from baseline
3. **Memory usage increases > 15%** from baseline

### Load Test Thresholds

| Load Level | Concurrent Users | P95 Response Time | Error Rate |
|------------|------------------|-------------------|------------|
| Normal | 50 | < 2s | < 2% |
| Peak | 150 | < 5s | < 10% |
| Maximum | 200 | < 10s | < 20% |

---

## Troubleshooting

### Benchmark Failures

#### "Database connection failed"

**Cause:** Database not running or wrong credentials

**Solution:**
```bash
# Check database is running
docker-compose ps db

# Start database
docker-compose up -d db

# Verify connection
docker-compose exec db psql -U scheduler -d residency_scheduler
```

#### "Out of memory"

**Cause:** Benchmark dataset too large for available RAM

**Solution:**
```bash
# Reduce benchmark size
python -m benchmarks.schedule_generation_bench \
  --residents 25 \
  --weeks 2  # Reduce from 4 weeks

# Or increase Docker memory limit
# Edit docker-compose.yml: mem_limit: 4g
```

#### "Import error: No module named 'app'"

**Cause:** Wrong working directory

**Solution:**
```bash
# Run from backend directory
cd backend
python -m benchmarks
```

### Profiling Failures

#### "py-spy: Operation not permitted"

**Cause:** py-spy requires root access on Linux

**Solution:**
```bash
# Run with sudo
sudo env PATH=$PATH python -m profiling.flame_graph_generator \
  --target schedule \
  --method pyspy

# Or use cprofile method (no sudo required)
python -m profiling.flame_graph_generator \
  --target schedule \
  --method cprofile
```

### Load Test Failures

#### "Connection refused"

**Cause:** Backend not running or wrong URL

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Update BASE_URL in load-tests/utils/auth.js
export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
```

#### "k6 command not found"

**Cause:** k6 not installed

**Solution:**
```bash
# Install k6 (macOS)
brew install k6

# Install k6 (Linux)
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

---

## Best Practices

### Benchmarking

1. **Run multiple iterations** (at least 3-5) to account for variance
2. **Warm up** the system before measuring (first run is often slower)
3. **Use consistent hardware** for comparing results
4. **Test in isolation** - no other processes running
5. **Document conditions** - record system specs, database state, etc.

### Profiling

1. **Profile production-like data** - use realistic dataset sizes
2. **Profile the slow path** - focus on operations taking > 1s
3. **Profile incrementally** - isolate specific subsystems
4. **Compare before/after** - profile after optimizations to verify improvement

### Load Testing

1. **Start small** - begin with smoke tests, then scale up
2. **Monitor resources** - watch CPU, memory, database connections
3. **Test realistic scenarios** - mimic actual user behavior
4. **Test failure modes** - what happens at 2x expected load?
5. **Test recovery** - can system recover from spikes?

### Monitoring

1. **Collect metrics continuously** - track trends over time
2. **Set alerts** - be notified of regressions automatically
3. **Compare regularly** - check new benchmarks against baseline
4. **Update baselines** - after major optimizations or infrastructure changes

---

## Additional Resources

- **Benchmark results directory:** `benchmark_results/`
- **Profiling results directory:** `profiling_results/`
- **Metrics directory:** `metrics/`
- **Load test reports:** Check k6 output and Grafana dashboard

For questions or issues, see:
- Project documentation: `docs/`
- CLAUDE.md: Development guidelines
- GitHub Issues: Report problems

---

**Last Updated:** 2025-01-01
**Maintained by:** Development Team
