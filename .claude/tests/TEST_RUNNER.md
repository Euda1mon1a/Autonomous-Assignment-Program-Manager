# TEST RUNNER FRAMEWORK - Execution & Reporting

> **Purpose:** Execute all SEARCH_PARTY tests with consistent methodology and reporting
> **Created:** 2025-12-31
> **Status:** Active

---

## Overview

The Test Runner Framework provides unified execution, monitoring, and reporting for all SEARCH_PARTY tests:
- Chaos Engineering Suite (6 tests)
- Scaling Validation Tests (3 tests)
- Quality Gate Tests (3 tests)
- Integration Tests (3 tests)

**Total:** 15 comprehensive tests covering resilience, scaling, quality, and workflow integration.

---

## Quick Start

### Run Everything

```bash
cd /home/user/Autonomous-Assignment-Program-Manager

# Run all tests with defaults
./test_runners/test_all.sh

# Run specific test suite
./test_runners/test_chaos.sh
./test_runners/test_scaling.sh
./test_runners/test_quality.sh
./test_runners/test_integration.sh

# Run single test
./test_runners/run_test.sh --test=timeout_cascade
./test_runners/run_test.sh --test=scaling_baseline
./test_runners/run_test.sh --test=output_validation
./test_runners/run_test.sh --test=g2_orchestrator_handoff
```

### Monitor Progress

```bash
# Watch test execution in real-time
tail -f test_logs/current.log

# View test dashboard
open http://localhost:8888/test-dashboard
```

### Get Results

```bash
# Generate HTML report
./test_runners/report.sh --format=html --output=results.html

# Generate JSON results
./test_runners/report.sh --format=json --output=results.json

# Print summary to console
./test_runners/report.sh --format=console
```

---

## Test Execution Model

### Phase 1: Preparation (5 minutes)

```
1. Load test configuration
2. Create test environment
3. Initialize baseline metrics
4. Verify resources available
5. Start monitoring agents
```

### Phase 2: Execution (varies by test)

```
1. Deploy test infrastructure
2. Execute test scenarios
3. Monitor metrics in real-time
4. Collect telemetry
5. Track events and errors
```

### Phase 3: Validation (2-5 minutes)

```
1. Verify success criteria
2. Check thresholds
3. Flag anomalies
4. Collect final metrics
5. Generate test report
```

### Phase 4: Cleanup (1-2 minutes)

```
1. Terminate test infrastructure
2. Archive logs
3. Clean temporary files
4. Update test database
5. Report completion
```

---

## Test Configuration

### Environment Variables

```bash
# Test runner configuration
TEST_LOG_DIR=test_logs          # Where to store logs
TEST_DB_PATH=test_results.db    # SQLite results database
TEST_TIMEOUT_MULTIPLIER=1.5     # Extend timeouts in slow environments
TEST_PARALLEL=true              # Run compatible tests in parallel

# Test-specific settings
CHAOS_PROBE_COUNT=10            # Probes per chaos test
SCALING_BASELINE_AGENTS=10      # Agents for baseline test
QUALITY_TEST_CASES=10           # Test cases per quality test
INTEGRATION_PROTOCOLS=4         # Protocols for integration test

# Resource limits
MAX_CPU_PERCENT=90              # Max CPU usage
MAX_MEMORY_MB=8192              # Max memory (8GB)
MAX_API_CALLS=400               # Max API calls per test
DISK_SPACE_MIN_GB=10            # Minimum free disk space required

# Logging
LOG_LEVEL=INFO                  # INFO, DEBUG, TRACE
LOG_FORMAT=json                 # json, text, compact
```

### Configuration File

```yaml
# .claude/tests/test_config.yaml

test_runner:
  mode: standard              # standard, parallel, serial
  timeout_multiplier: 1.5
  retry_failed: true
  max_retries: 2

test_suites:
  chaos:
    enabled: true
    timeout_minutes: 120
    tests:
      - timeout_cascade
      - rate_limit_stress
      - context_pollution
      - target_size_explosion
      - orchestrator_crash
      - memory_exhaustion

  scaling:
    enabled: true
    timeout_minutes: 90
    tests:
      - baseline_10_agents
      - stress_15_agents
      - limit_20_agents

  quality:
    enabled: true
    timeout_minutes: 45
    tests:
      - output_validation
      - discrepancy_detection
      - confidence_aggregation

  integration:
    enabled: true
    timeout_minutes: 60
    tests:
      - g2_orchestrator_handoff
      - multi_protocol_coordination
      - cross_session_synthesis

monitoring:
  metrics: [cpu, memory, disk, network, api_calls]
  sample_interval_sec: 5
  dashboard_port: 8888

reporting:
  formats: [html, json, console]
  archive_logs: true
  upload_results: false
```

---

## Execution Workflows

### Workflow 1: Full Suite (All Tests)

```bash
./test_runners/test_all.sh \
  --config=test_config.yaml \
  --duration-limit=480 \
  --report=full
```

**Timeline:**
- Chaos Engineering: 120 minutes (6 tests × 20 min avg)
- Scaling Validation: 90 minutes (3 tests × 30 min avg)
- Quality Gates: 45 minutes (3 tests × 15 min avg)
- Integration: 60 minutes (3 tests × 20 min avg)
- **Total: ~315 minutes (5.25 hours)**

### Workflow 2: Quick Validation (Smoke Tests)

```bash
./test_runners/test_all.sh \
  --mode=smoke \
  --duration-limit=60 \
  --tests=timeout_cascade,scaling_baseline,output_validation,g2_orchestrator_handoff
```

**Timeline:**
- One test from each suite: ~60 minutes
- Validates basic functionality without full suite
- Good for CI/CD pipelines

### Workflow 3: Continuous Integration (Daily)

```bash
# Run on schedule (e.g., nightly)
0 2 * * * /path/to/test_runners/test_all.sh \
  --config=test_config.yaml \
  --archive=true \
  --alert-on-failure=true
```

**Tests Run:** All 15 tests
**When:** 2:00 AM daily
**Duration:** ~5.5 hours
**Reporting:** Email results, upload to dashboard

### Workflow 4: Targeted Testing (Single Suite)

```bash
# Run just chaos tests
./test_runners/test_chaos.sh --all

# Run just scaling tests
./test_runners/test_scaling.sh --all

# Run just quality tests
./test_runners/test_quality.sh --all

# Run just integration tests
./test_runners/test_integration.sh --all
```

---

## Execution Examples

### Example 1: Run Baseline Scaling Test

```bash
./test_runners/run_test.sh \
  --test=scaling_baseline \
  --agents=10 \
  --target-loc=20000 \
  --duration-target=4 \
  --verbose
```

**Output:**
```
=== TEST RUNNER: scaling_baseline ===
Configuration:
  Agents: 10
  Target LOC: 20000
  Expected Duration: 4 minutes
  Verbose: true

[PREP] Creating test environment... OK (0.3s)
[PREP] Initializing baseline metrics... OK (0.1s)
[EXEC] Deploying 10 agents... OK (3.2s)
[EXEC] Monitoring execution... (4m 23s elapsed)
  CPU: 68% | Memory: 6.2GB | API: 175 calls
[VALID] Checking success criteria...
  ✓ Startup time: 28s (<30s)
  ✓ First result: 12s (<15s)
  ✓ Total duration: 4m23s (3-5m range)
  ✓ CPU peak: 68% (<80%)
  ✓ Memory peak: 6.2GB (<7GB)
  ✓ Probe success: 98% (>97%)

[RESULT] TEST PASS
  Duration: 4m 23s (within expectations)
  Metrics: baseline_20k_10agents.json
  Confidence: High
```

### Example 2: Run Chaos Timeout Test

```bash
./test_runners/run_test.sh \
  --test=timeout_cascade \
  --timeout-ms=100 \
  --probes=10 \
  --detect-cascade
```

**Output:**
```
=== TEST RUNNER: timeout_cascade ===
Configuration:
  Probe Timeout: 100ms
  Probes: 10
  Cascade Detection: enabled

[PREP] Creating test environment... OK
[PREP] Deploying 10 probes with 100ms timeout... OK (2.1s)
[EXEC] Monitoring timeout behavior...
  T+1.2s: Probe 1 timeout
  T+1.4s: Probe 2 timeout
  T+1.5s: Probe 3 timeout
  T+1.6s: Probe 4 timeout
  T+1.7s: Probe 5 timeout
  T+1.8s: Probe 6 timeout
  T+1.9s: Probe 7 timeout
  T+2.0s: Probe 8 timeout
  T+2.1s: Probe 9 timeout
  T+2.2s: Probe 10 timeout
  Total Timeouts: 10
  Cascade Detected: NO (independent timeouts)

[VALID] Checking success criteria...
  ✓ All probes timeout: 10/10
  ✓ No cascade propagation: confirmed
  ✓ Orchestrator responsive: yes
  ✓ Recovery time: 2.8s (<30s)

[RESULT] TEST PASS
  Timeout Pattern: Independent (good)
  Recovery: Graceful
  Orchestrator Health: OK
```

### Example 3: Run Quality Output Validation

```bash
./test_runners/run_test.sh \
  --test=output_validation \
  --test-cases=10 \
  --schema=probe_output_schema.json
```

**Output:**
```
=== TEST RUNNER: output_validation ===
Configuration:
  Test Cases: 10
  Schema: probe_output_schema.json

[PREP] Loading schema... OK
[PREP] Generating test cases...
  Case 1/10: Valid output [OK]
  Case 2/10: Missing field [OK]
  Case 3/10: Wrong type [OK]
  Case 4/10: Out of range [OK]
  Case 5/10: Corrupted JSON [OK]
  Case 6/10: Semantic error [OK]
  Case 7/10: Edge case 1 [OK]
  Case 8/10: Edge case 2 [OK]
  Case 9/10: Edge case 3 [OK]
  Case 10/10: Edge case 4 [OK]

[EXEC] Running validation...
  Case 1: PASS (valid passes)
  Case 2: PASS (missing field rejected)
  Case 3: PASS (wrong type rejected)
  Case 4: PASS (out of range rejected)
  Case 5: PASS (corrupted rejected)
  Case 6: PASS (semantic flagged)
  Case 7-10: PASS (edge cases handled)

[VALID] Verification...
  ✓ All expected outcomes correct: 10/10
  ✓ False positives: 0
  ✓ False negatives: 0

[RESULT] TEST PASS
  Pass Rate: 100%
  Coverage: Complete
```

---

## Real-Time Monitoring

### Dashboard View

```
╔════════════════════════════════════════════════════════════╗
║                    TEST RUNNER DASHBOARD                   ║
╠════════════════════════════════════════════════════════════╣
║ Current Test: timeout_cascade                              ║
║ Status: RUNNING (2m 15s elapsed)                            ║
║                                                             ║
║ Progress:                                                   ║
║ [████████████████░░░░] 65% (Phase 2: Execution)            ║
║                                                             ║
║ Metrics:                                                    ║
║  CPU: 68% ━━━━━━━━━━━━━━━━━━━━━━ 100%                     ║
║  Memory: 6.2GB ━━━━━━━━━━━ 8GB                             ║
║  API Calls: 175/400 ━━━━━━━━━━━━━━━━━━                    ║
║  Network: 12.4 MB/s ━━━━━━━━━━━━━━━━━━━━                  ║
║                                                             ║
║ Test Queue:                                                 ║
║  ✓ timeout_cascade (running)                               ║
║  ⏳ rate_limit_stress (queued)                             ║
║  ⏳ context_pollution (queued)                             ║
║  ⏳ ... (12 more tests)                                    ║
║                                                             ║
║ Recent Events:                                              ║
║  2025-12-31 10:23:15 - Probe 1 timeout detected            ║
║  2025-12-31 10:23:16 - Probe 2 timeout detected            ║
║  2025-12-31 10:23:17 - Orchestrator health check OK         ║
║                                                             ║
╚════════════════════════════════════════════════════════════╝
```

### CLI Monitoring

```bash
# Watch logs in real-time
tail -f test_logs/current.log | grep -E "PASS|FAIL|ERROR"

# Monitor resource usage
watch -n 1 'ps aux | grep test_runner | awk "{print \$3, \$4, \$6}"'

# Check test database
sqlite3 test_results.db "SELECT test_name, status, duration FROM test_results ORDER BY start_time DESC LIMIT 5;"
```

---

## Test Results & Reporting

### Result Storage

Results are stored in SQLite database:

```sql
CREATE TABLE test_results (
  id INTEGER PRIMARY KEY,
  test_name TEXT,
  suite TEXT,
  status TEXT,  -- PASS, FAIL, ERROR
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  duration_sec INTEGER,
  configuration JSON,
  metrics JSON,
  error_message TEXT,
  log_file TEXT
);

CREATE TABLE test_metrics (
  id INTEGER PRIMARY KEY,
  test_id INTEGER,
  metric_name TEXT,
  metric_value FLOAT,
  threshold FLOAT,
  unit TEXT,
  FOREIGN KEY(test_id) REFERENCES test_results(id)
);
```

### Queries

```bash
# View all test results
sqlite3 test_results.db "SELECT test_name, status, duration_sec FROM test_results;"

# View failed tests
sqlite3 test_results.db "SELECT test_name, error_message FROM test_results WHERE status='FAIL';"

# Calculate average duration by suite
sqlite3 test_results.db "SELECT suite, AVG(duration_sec) as avg_duration FROM test_results GROUP BY suite;"

# Export to CSV
sqlite3 -header -csv test_results.db "SELECT * FROM test_results;" > results.csv
```

### Report Generation

#### HTML Report

```bash
./test_runners/report.sh \
  --format=html \
  --output=results.html \
  --include-graphs \
  --theme=dark
```

**Generates:** Full HTML report with:
- Test summary
- Pass/fail breakdown
- Performance graphs
- Resource usage charts
- Metrics comparison
- Failure analysis
- Recommendations

#### JSON Report

```bash
./test_runners/report.sh \
  --format=json \
  --output=results.json \
  --include-metrics \
  --include-logs
```

**Generates:** Machine-readable JSON with all test data.

#### Console Report

```bash
./test_runners/report.sh --format=console
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║                   TEST EXECUTION SUMMARY                   ║
╠════════════════════════════════════════════════════════════╣
║                                                             ║
║ Total Tests: 15                                             ║
║ Passed: 14 (93%)  ✓                                         ║
║ Failed: 1 (7%)   ✗                                          ║
║ Errors: 0                                                   ║
║                                                             ║
║ By Suite:                                                   ║
║  ✓ Chaos Engineering (6/6 pass)                            ║
║  ✓ Scaling Validation (3/3 pass)                           ║
║  ✓ Quality Gates (3/3 pass)                                ║
║  ⚠ Integration (2/3 pass) - 1 failure                      ║
║                                                             ║
║ Failed Tests:                                               ║
║  ✗ multi_protocol_coordination                             ║
║    Error: Protocol interference detected in G2_RECON       ║
║    Recommendation: Review probe resource allocation        ║
║                                                             ║
║ Total Duration: 5h 23m                                      ║
║ Start Time: 2025-12-31 02:00:00                            ║
║ End Time: 2025-12-31 07:23:00                              ║
║                                                             ║
╚════════════════════════════════════════════════════════════╝
```

---

## Debugging & Troubleshooting

### Test Fails

```bash
# Check test logs
cat test_logs/{test_name}.log | tail -100

# Enable debug mode
./test_runners/run_test.sh --test={test_name} --debug

# Extract metrics from failure
jq '.metrics' test_logs/{test_name}_metrics.json

# Replay test with same seed (reproducible failure)
./test_runners/run_test.sh --test={test_name} --seed=12345
```

### Test Hangs

```bash
# Check orchestrator status
curl http://localhost:8000/health

# Kill hung test
pkill -f test_runner

# Check for resource exhaustion
free -h  # Memory
df -h    # Disk
top -b -n 1 | head -15  # Processes
```

### Test Timeout

```bash
# Increase timeout
./test_runners/run_test.sh --test={test_name} --timeout=600

# Check slow systems
./test_runners/run_test.sh --test={test_name} --timeout-multiplier=2.0
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: SEARCH_PARTY Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 360
    steps:
      - uses: actions/checkout@v2
      - name: Run smoke tests
        run: ./test_runners/test_all.sh --mode=smoke
      - name: Upload results
        uses: actions/upload-artifact@v2
        if: always()
        with:
          name: test-results
          path: test_logs/
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Prepare') {
            steps {
                sh './test_runners/prepare_environment.sh'
            }
        }
        stage('Test') {
            parallel {
                stage('Chaos') {
                    steps {
                        sh './test_runners/test_chaos.sh --all'
                    }
                }
                stage('Scaling') {
                    steps {
                        sh './test_runners/test_scaling.sh --all'
                    }
                }
                stage('Quality') {
                    steps {
                        sh './test_runners/test_quality.sh --all'
                    }
                }
                stage('Integration') {
                    steps {
                        sh './test_runners/test_integration.sh --all'
                    }
                }
            }
        }
        stage('Report') {
            steps {
                sh './test_runners/report.sh --format=html'
                publishHTML([reportDir: 'test_logs', reportFiles: 'report.html'])
            }
        }
    }
}
```

---

## Summary Template

### Test Completion Report

```
╔════════════════════════════════════════════════════════════╗
║         SEARCH_PARTY TEST SUITE COMPLETION REPORT          ║
╠════════════════════════════════════════════════════════════╣
║                                                             ║
║ EXECUTION SUMMARY                                           ║
║ ─────────────────                                           ║
║ Total Tests: 15                                             ║
║ Passed: XX (XX%)                                            ║
║ Failed: X (X%)                                              ║
║ Errors: X                                                   ║
║ Duration: X hours Y minutes                                 ║
║ Start Time: YYYY-MM-DD HH:MM:SS                            ║
║ End Time: YYYY-MM-DD HH:MM:SS                              ║
║                                                             ║
║ TEST SUITE BREAKDOWN                                        ║
║ ────────────────────                                        ║
║ Chaos Engineering (6 tests): ✓ PASS                        ║
║   ✓ timeout_cascade                                         ║
║   ✓ rate_limit_stress                                       ║
║   ✓ context_pollution                                       ║
║   ✓ target_size_explosion                                   ║
║   ✓ orchestrator_crash                                      ║
║   ✓ memory_exhaustion                                       ║
║                                                             ║
║ Scaling Validation (3 tests): ✓ PASS                       ║
║   ✓ baseline_10_agents                                      ║
║   ✓ stress_15_agents                                        ║
║   ✓ limit_20_agents                                         ║
║                                                             ║
║ Quality Gates (3 tests): ✓ PASS                            ║
║   ✓ output_validation                                       ║
║   ✓ discrepancy_detection                                   ║
║   ✓ confidence_aggregation                                  ║
║                                                             ║
║ Integration Tests (3 tests): ⚠ PARTIAL PASS                ║
║   ✓ g2_orchestrator_handoff                                 ║
║   ✗ multi_protocol_coordination (FAILED)                   ║
║   ✓ cross_session_synthesis                                 ║
║                                                             ║
║ KEY FINDINGS                                                ║
║ ─────────────                                               ║
║ • SEARCH_PARTY resilience: EXCELLENT                       ║
║   - Handles timeouts gracefully                            ║
║   - Rate limits properly enforced                          ║
║   - Context properly isolated                              ║
║                                                             ║
║ • Scaling performance: GOOD                                 ║
║   - 10 agents: baseline established                        ║
║   - 15 agents: acceptable degradation (+52%)               ║
║   - 20 agents: at resource saturation                      ║
║                                                             ║
║ • Quality gates: ROBUST                                     ║
║   - Output validation: 100% accuracy                       ║
║   - Discrepancy detection: 100% recall                     ║
║   - Confidence aggregation: suitable for synthesis         ║
║                                                             ║
║ • Integration workflows: MOSTLY FUNCTIONAL                 ║
║   - Probe handoff: working perfectly                       ║
║   - Multi-protocol coordination: needs optimization        ║
║   - Cross-session synthesis: working perfectly             ║
║                                                             ║
║ RECOMMENDATIONS                                             ║
║ ────────────────                                            ║
║ 1. Address multi-protocol CPU contention:                  ║
║    - Implement probe pooling or async optimization         ║
║    - Reduce per-probe overhead                             ║
║    - Consider agent batching                               ║
║                                                             ║
║ 2. Monitor resource utilization in production:             ║
║    - Set alerts at 75% CPU, 80% memory                     ║
║    - Implement automatic scaling                           ║
║    - Consider hardware upgrade for >15 agents              ║
║                                                             ║
║ 3. Establish baseline metrics for regression testing:      ║
║    - Archive baseline_20k_10agents.json                    ║
║    - Compare future runs against baseline                  ║
║    - Alert on >5% performance degradation                  ║
║                                                             ║
║ DEPLOYMENT READINESS                                        ║
║ ─────────────────────                                       ║
║ ✓ Core functionality: READY                                ║
║ ✓ Resilience: VERIFIED                                     ║
║ ⚠ Scaling limits: IDENTIFIED (20 agents max)               ║
║ ✓ Quality gates: FUNCTIONAL                                ║
║ ✓ Workflows: READY (with noted optimization)               ║
║                                                             ║
║ NEXT STEPS                                                  ║
║ ──────────                                                  ║
║ □ Fix multi_protocol_coordination test                     ║
║ □ Document scaling limitations in production guidelines    ║
║ □ Set up continuous testing (daily runs)                   ║
║ □ Create performance regression dashboards                 ║
║ □ Implement automated alerts for test failures             ║
║                                                             ║
║ Results: test_logs/report.html                             ║
║ Database: test_results.db                                  ║
║                                                             ║
╚════════════════════════════════════════════════════════════╝
```

---

**Last Updated:** 2025-12-31
**Status:** ACTIVE
**Maintained By:** AI Testing Framework
