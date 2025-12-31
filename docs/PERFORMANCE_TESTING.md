***REMOVED*** Performance Testing Guide

Comprehensive guide to performance testing, benchmarking, profiling, and monitoring for the Residency Scheduler application.

***REMOVED******REMOVED*** Table of Contents

- [Overview](***REMOVED***overview)
- [Quick Start](***REMOVED***quick-start)
- [Benchmark Scripts](***REMOVED***benchmark-scripts)
- [Profiling Tools](***REMOVED***profiling-tools)
- [Monitoring Scripts](***REMOVED***monitoring-scripts)
- [Load Testing](***REMOVED***load-testing)
- [Configuration](***REMOVED***configuration)
- [CI/CD Integration](***REMOVED***cicd-integration)
- [Interpreting Results](***REMOVED***interpreting-results)
- [Troubleshooting](***REMOVED***troubleshooting)

---

***REMOVED******REMOVED*** Overview

The performance testing infrastructure consists of four main components:

1. **Benchmarks** (`backend/benchmarks/`) - Measure specific operation performance
2. **Profiling** (`backend/profiling/`) - Identify bottlenecks and optimization opportunities
3. **Monitoring** (`scripts/monitoring/`) - Track metrics over time and detect regressions
4. **Load Tests** (`load-tests/scenarios/`) - Test system behavior under realistic load

---

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** Run Quick Benchmark Suite

```bash
***REMOVED*** From project root
cd backend
python -m benchmarks --quick --verbose

***REMOVED*** Results saved to: benchmark_results/
```

***REMOVED******REMOVED******REMOVED*** Run Single Benchmark

```bash
***REMOVED*** Schedule generation benchmark
python -m benchmarks.schedule_generation_bench --residents 50 --weeks 4

***REMOVED*** ACGME validation benchmark
python -m benchmarks.acgme_validation_bench --residents 100 --weeks 4
```

***REMOVED******REMOVED******REMOVED*** Profile an Operation

```bash
***REMOVED*** Profile schedule generation
cd backend
python -m profiling.profile_scheduler --residents 50 --weeks 4

***REMOVED*** Results saved to: profiling_results/
```

***REMOVED******REMOVED******REMOVED*** Run Load Test

```bash
***REMOVED*** From load-tests directory
cd load-tests
npm install

***REMOVED*** Run peak load scenario
npm run test:load

***REMOVED*** Or run specific scenario
k6 run scenarios/peak_load_scenario.js
```

---

***REMOVED******REMOVED*** Benchmark Scripts

Location: `backend/benchmarks/`

***REMOVED******REMOVED******REMOVED*** Available Benchmarks

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

***REMOVED******REMOVED******REMOVED*** Usage Examples

***REMOVED******REMOVED******REMOVED******REMOVED*** Schedule Generation Benchmark

```bash
***REMOVED*** Single configuration
python -m benchmarks.schedule_generation_bench \
  --residents 50 \
  --weeks 4 \
  --iterations 5 \
  --verbose

***REMOVED*** Full suite (multiple program sizes)
python -m benchmarks.schedule_generation_bench --suite
```

***REMOVED******REMOVED******REMOVED******REMOVED*** ACGME Validation Benchmark

```bash
***REMOVED*** Test specific validation type
python -m benchmarks.acgme_validation_bench \
  --residents 100 \
  --weeks 4 \
  --rule full \
  --iterations 10

***REMOVED*** Full suite
python -m benchmarks.acgme_validation_bench --suite --verbose
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Database Query Benchmark

```bash
***REMOVED*** Simple queries
python -m benchmarks.database_query_bench \
  --query-type simple \
  --iterations 100

***REMOVED*** Join queries
python -m benchmarks.database_query_bench \
  --query-type joins \
  --iterations 50

***REMOVED*** Bulk operations
python -m benchmarks.database_query_bench \
  --query-type bulk \
  --batch-size 500 \
  --iterations 10

***REMOVED*** Full suite
python -m benchmarks.database_query_bench --suite
```

***REMOVED******REMOVED******REMOVED*** Benchmark Output

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

***REMOVED******REMOVED*** Profiling Tools

Location: `backend/profiling/`

***REMOVED******REMOVED******REMOVED*** Available Profilers

| Profiler | File | Purpose |
|----------|------|---------|
| **Scheduler Profiler** | `profile_scheduler.py` | Profile schedule generation |
| **Query Profiler** | `profile_queries.py` | Profile database operations |
| **API Profiler** | `profile_api_endpoints.py` | Profile request handling |
| **Background Tasks** | `profile_background_tasks.py` | Profile Celery tasks |
| **Flame Graphs** | `flame_graph_generator.py` | Generate visual profiling |

***REMOVED******REMOVED******REMOVED*** Usage Examples

***REMOVED******REMOVED******REMOVED******REMOVED*** Profile Schedule Generation

```bash
python -m profiling.profile_scheduler \
  --residents 100 \
  --weeks 4 \
  --sort cumulative

***REMOVED*** Results include:
***REMOVED*** - Function-level timing
***REMOVED*** - Call counts
***REMOVED*** - Cumulative time spent
***REMOVED*** - Bottleneck identification
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Profile Database Queries

```bash
***REMOVED*** Profile simple queries
python -m profiling.profile_queries --query-type simple

***REMOVED*** Profile joins
python -m profiling.profile_queries --query-type joins

***REMOVED*** Profile all query types
python -m profiling.profile_queries --query-type all
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Generate Flame Graph

```bash
***REMOVED*** Using py-spy (recommended)
sudo python -m profiling.flame_graph_generator \
  --target schedule \
  --method pyspy \
  --duration 30

***REMOVED*** Convert existing pstats file
python -m profiling.flame_graph_generator \
  --pstats profiling_results/schedule_generation.pstats
```

**Note:** Flame graph generation with py-spy requires `sudo` on Linux. Install py-spy:

```bash
pip install py-spy
```

***REMOVED******REMOVED******REMOVED*** Interpreting Profiling Results

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

***REMOVED******REMOVED*** Monitoring Scripts

Location: `scripts/monitoring/`

***REMOVED******REMOVED******REMOVED*** Available Scripts

| Script | Purpose |
|--------|---------|
| `collect_metrics.py` | Gather performance metrics |
| `generate_report.py` | Create performance reports |
| `compare_benchmarks.py` | Compare benchmark runs |
| `alert_on_regression.py` | Detect performance regressions |

***REMOVED******REMOVED******REMOVED*** Collect Metrics

```bash
***REMOVED*** Collect once
python scripts/monitoring/collect_metrics.py \
  --output metrics/performance_metrics.json

***REMOVED*** Continuous collection (every 5 minutes)
python scripts/monitoring/collect_metrics.py \
  --continuous \
  --interval 300

***REMOVED*** Print to stdout instead of saving
python scripts/monitoring/collect_metrics.py --print
```

Collected metrics include:
- System resources (CPU, memory, disk)
- Database statistics (size, connections, table sizes)
- Latest benchmark results

***REMOVED******REMOVED******REMOVED*** Generate Reports

```bash
***REMOVED*** Generate text report
python scripts/monitoring/generate_report.py \
  --metrics metrics/performance_metrics.json \
  --format text

***REMOVED*** Generate HTML report
python scripts/monitoring/generate_report.py \
  --format html \
  --output reports/performance.html

***REMOVED*** Generate Markdown report
python scripts/monitoring/generate_report.py \
  --format markdown \
  --output reports/PERFORMANCE.md
```

***REMOVED******REMOVED******REMOVED*** Compare Benchmarks

```bash
***REMOVED*** Compare two specific runs
python scripts/monitoring/compare_benchmarks.py \
  --baseline benchmark_results/baseline.json \
  --current benchmark_results/current.json

***REMOVED*** Compare last 7 runs in directory
python scripts/monitoring/compare_benchmarks.py \
  --dir benchmark_results/ \
  --last 7
```

***REMOVED******REMOVED******REMOVED*** Detect Regressions

```bash
***REMOVED*** Check for regressions (15% threshold)
python scripts/monitoring/alert_on_regression.py \
  --dir benchmark_results/ \
  --threshold 15

***REMOVED*** CI mode (exit code 1 on regression)
python scripts/monitoring/alert_on_regression.py \
  --dir benchmark_results/ \
  --threshold 10 \
  --ci

***REMOVED*** Send Slack alert on regression
python scripts/monitoring/alert_on_regression.py \
  --dir benchmark_results/ \
  --slack-webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

***REMOVED******REMOVED*** Load Testing

Location: `load-tests/scenarios/`

***REMOVED******REMOVED******REMOVED*** Available Scenarios

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

***REMOVED******REMOVED******REMOVED*** Setup

```bash
cd load-tests
npm install
```

***REMOVED******REMOVED******REMOVED*** Running Load Tests

```bash
***REMOVED*** Quick smoke test
npm run test:smoke

***REMOVED*** Standard load test
npm run test:load

***REMOVED*** Stress test
npm run test:stress

***REMOVED*** Run specific scenario
k6 run scenarios/peak_load_scenario.js

***REMOVED*** Run with custom options
k6 run --vus 100 --duration 10m scenarios/sustained_load_scenario.js
```

***REMOVED******REMOVED******REMOVED*** Load Test Scenarios Explained

***REMOVED******REMOVED******REMOVED******REMOVED*** Peak Load Scenario

**Purpose:** Test behavior at maximum expected load
**Configuration:** 0 → 50 → 100 → 150 → 200 VUs over 22 minutes
**Success Criteria:**
- p95 < 5s even at peak
- Error rate < 10% at 200 VUs
- No system crashes

```bash
k6 run scenarios/peak_load_scenario.js
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Sustained Load Scenario

**Purpose:** Identify memory leaks and gradual degradation
**Configuration:** 50 VUs for 30 minutes
**Success Criteria:**
- Response times remain stable
- No memory growth
- Error rate < 2%

```bash
k6 run scenarios/sustained_load_scenario.js
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Spike Test Scenario

**Purpose:** Test recovery from sudden traffic spikes
**Configuration:** 10 → 200 → 10 VUs (spike in 10 seconds)
**Success Criteria:**
- System doesn't crash
- Error rate < 30% during spike
- Recovery success > 95%

```bash
k6 run scenarios/spike_test_scenario.js
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Soak Test Scenario

**Purpose:** Long-duration test for memory leaks
**Configuration:** 30 VUs for 2+ hours
**Success Criteria:**
- No performance degradation over time
- Memory usage stays flat
- Error rate < 1%

```bash
***REMOVED*** 2-hour soak test
k6 run scenarios/soak_test_scenario.js

***REMOVED*** Extended 4-hour soak test
k6 run --duration 4h scenarios/soak_test_scenario.js
```

***REMOVED******REMOVED******REMOVED*** k6 Cloud Integration

For larger-scale tests, use k6 Cloud:

```bash
***REMOVED*** Run on k6 Cloud
k6 cloud scenarios/peak_load_scenario.js

***REMOVED*** With custom options
k6 cloud --vus 500 --duration 20m scenarios/sustained_load_scenario.js
```

---

***REMOVED******REMOVED*** Configuration

***REMOVED******REMOVED******REMOVED*** Benchmark Configuration

File: `benchmark_config.yaml`

```yaml
***REMOVED*** Example configuration
schedule_generation:
  enabled: true
  configurations:
    - name: "medium_program"
      residents: 25
      weeks: 4
      iterations: 3
      threshold_seconds: 10.0
```

***REMOVED******REMOVED******REMOVED*** Baseline Metrics

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
***REMOVED*** Run benchmarks and save as new baseline
python -m benchmarks --suite
mv benchmark_results/latest.json baseline_metrics.json
```

---

***REMOVED******REMOVED*** CI/CD Integration

***REMOVED******REMOVED******REMOVED*** GitHub Actions Example

```yaml
***REMOVED*** .github/workflows/performance-tests.yml
name: Performance Tests

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  ***REMOVED*** Daily at 2 AM

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

***REMOVED******REMOVED******REMOVED*** Pre-commit Hook

```bash
***REMOVED*** .git/hooks/pre-commit
***REMOVED***!/bin/bash

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

***REMOVED******REMOVED*** Interpreting Results

***REMOVED******REMOVED******REMOVED*** Performance Metrics

***REMOVED******REMOVED******REMOVED******REMOVED*** Duration Metrics

- **avg_duration**: Average time across all iterations
- **min_duration**: Fastest iteration
- **max_duration**: Slowest iteration
- **p95_duration**: 95th percentile (95% of requests faster than this)
- **p99_duration**: 99th percentile

**Good:** Low standard deviation (consistent performance)
**Bad:** High standard deviation (unpredictable performance)

***REMOVED******REMOVED******REMOVED******REMOVED*** Throughput Metrics

- **operations per second**: How many operations can be performed per second
- **requests per second**: HTTP request rate

**Good:** Linear scaling with resources
**Bad:** Throughput decrease as load increases (indicates bottleneck)

***REMOVED******REMOVED******REMOVED******REMOVED*** Memory Metrics

- **baseline_mb**: Starting memory
- **peak_mb**: Maximum memory used
- **growth_mb**: Memory increase over iterations

**Good:** Growth < 50 MB, no leak detected
**Bad:** Linear growth over iterations (memory leak)

***REMOVED******REMOVED******REMOVED*** Regression Detection

Performance regression is detected when:

1. **Duration increases > 10%** from baseline
2. **Throughput decreases > 10%** from baseline
3. **Memory usage increases > 15%** from baseline

***REMOVED******REMOVED******REMOVED*** Load Test Thresholds

| Load Level | Concurrent Users | P95 Response Time | Error Rate |
|------------|------------------|-------------------|------------|
| Normal | 50 | < 2s | < 2% |
| Peak | 150 | < 5s | < 10% |
| Maximum | 200 | < 10s | < 20% |

---

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Benchmark Failures

***REMOVED******REMOVED******REMOVED******REMOVED*** "Database connection failed"

**Cause:** Database not running or wrong credentials

**Solution:**
```bash
***REMOVED*** Check database is running
docker-compose ps db

***REMOVED*** Start database
docker-compose up -d db

***REMOVED*** Verify connection
docker-compose exec db psql -U scheduler -d residency_scheduler
```

***REMOVED******REMOVED******REMOVED******REMOVED*** "Out of memory"

**Cause:** Benchmark dataset too large for available RAM

**Solution:**
```bash
***REMOVED*** Reduce benchmark size
python -m benchmarks.schedule_generation_bench \
  --residents 25 \
  --weeks 2  ***REMOVED*** Reduce from 4 weeks

***REMOVED*** Or increase Docker memory limit
***REMOVED*** Edit docker-compose.yml: mem_limit: 4g
```

***REMOVED******REMOVED******REMOVED******REMOVED*** "Import error: No module named 'app'"

**Cause:** Wrong working directory

**Solution:**
```bash
***REMOVED*** Run from backend directory
cd backend
python -m benchmarks
```

***REMOVED******REMOVED******REMOVED*** Profiling Failures

***REMOVED******REMOVED******REMOVED******REMOVED*** "py-spy: Operation not permitted"

**Cause:** py-spy requires root access on Linux

**Solution:**
```bash
***REMOVED*** Run with sudo
sudo env PATH=$PATH python -m profiling.flame_graph_generator \
  --target schedule \
  --method pyspy

***REMOVED*** Or use cprofile method (no sudo required)
python -m profiling.flame_graph_generator \
  --target schedule \
  --method cprofile
```

***REMOVED******REMOVED******REMOVED*** Load Test Failures

***REMOVED******REMOVED******REMOVED******REMOVED*** "Connection refused"

**Cause:** Backend not running or wrong URL

**Solution:**
```bash
***REMOVED*** Check backend is running
curl http://localhost:8000/health

***REMOVED*** Update BASE_URL in load-tests/utils/auth.js
export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
```

***REMOVED******REMOVED******REMOVED******REMOVED*** "k6 command not found"

**Cause:** k6 not installed

**Solution:**
```bash
***REMOVED*** Install k6 (macOS)
brew install k6

***REMOVED*** Install k6 (Linux)
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** Benchmarking

1. **Run multiple iterations** (at least 3-5) to account for variance
2. **Warm up** the system before measuring (first run is often slower)
3. **Use consistent hardware** for comparing results
4. **Test in isolation** - no other processes running
5. **Document conditions** - record system specs, database state, etc.

***REMOVED******REMOVED******REMOVED*** Profiling

1. **Profile production-like data** - use realistic dataset sizes
2. **Profile the slow path** - focus on operations taking > 1s
3. **Profile incrementally** - isolate specific subsystems
4. **Compare before/after** - profile after optimizations to verify improvement

***REMOVED******REMOVED******REMOVED*** Load Testing

1. **Start small** - begin with smoke tests, then scale up
2. **Monitor resources** - watch CPU, memory, database connections
3. **Test realistic scenarios** - mimic actual user behavior
4. **Test failure modes** - what happens at 2x expected load?
5. **Test recovery** - can system recover from spikes?

***REMOVED******REMOVED******REMOVED*** Monitoring

1. **Collect metrics continuously** - track trends over time
2. **Set alerts** - be notified of regressions automatically
3. **Compare regularly** - check new benchmarks against baseline
4. **Update baselines** - after major optimizations or infrastructure changes

---

***REMOVED******REMOVED*** Additional Resources

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
