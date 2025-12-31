# CHAOS ENGINEERING SUITE - SEARCH_PARTY Testing

> **Purpose:** Simulate failure scenarios and edge cases to validate SEARCH_PARTY resilience
> **Created:** 2025-12-31
> **Status:** Active

---

## Overview

The Chaos Engineering Suite comprises 6 destructive tests that push SEARCH_PARTY to failure points and validate recovery mechanisms.

### Test Categories

| Category | Tests | Duration | Risk Level |
|----------|-------|----------|-----------|
| **Timeout Cascades** | Test 1 | 15-20 min | HIGH |
| **Rate Limiting** | Test 2 | 20-30 min | HIGH |
| **Context Pollution** | Test 3 | 10-15 min | MEDIUM |
| **Target Complexity** | Test 4 | 30-45 min | HIGH |
| **Orchestrator Resilience** | Test 5 | 25-35 min | CRITICAL |
| **Memory Exhaustion** | Test 6 | 15-20 min | HIGH |

---

## Test 1: Timeout Cascade (All 10 Probes Timeout Simultaneously)

### Objective
Validate that SEARCH_PARTY gracefully handles complete probe failure without cascading system failure.

### Scenario
- Deploy all 10 probes with artificially low timeout (100ms)
- Target: Medium complexity codebase (15K LOC)
- Expected: Each probe timeout independently, no cross-probe failure propagation

### Setup

```bash
# Configuration for timeout cascade
PROBE_TIMEOUT_MS=100
PROBE_COUNT=10
TARGET_LOC=15000
EXPECTED_TIMEOUTS=10
CASCADE_THRESHOLD=8  # If >8 fail, orchestrator should abort gracefully
```

### Execution Steps

1. **Initialize Test Environment**
   ```bash
   ./test_runners/chaos_runner.sh \
     --test=timeout_cascade \
     --timeout=100 \
     --probes=10 \
     --log-dir=chaos_logs/test1
   ```

2. **Monitor Probe States** (every 1 second)
   ```
   Probe 1: RUNNING → TIMEOUT
   Probe 2: RUNNING → TIMEOUT
   ... (all 10 timeout within 2-3 seconds)
   ```

3. **Track Orchestrator Behavior**
   - Should log timeouts per probe
   - Should NOT cascade timeouts to other probes
   - Should trigger fallback synthesis (if >8 fail)
   - Should NOT crash or hang

### Success Criteria

- [ ] All 10 probes timeout within expected window (5 seconds)
- [ ] No cross-probe timeout propagation
- [ ] Orchestrator remains responsive (health check passes)
- [ ] Graceful degradation: uses whatever partial results exist
- [ ] Error log shows `TIMEOUT_CASCADE` event with count=10
- [ ] System recovers within 30 seconds

### Failure Conditions

| Condition | Severity | Recovery |
|-----------|----------|----------|
| Probe timeout causes orchestrator hang | CRITICAL | Kill orchestrator, restart |
| Timeout cascades to other probes | HIGH | Review probe isolation |
| Orchestrator crashes | CRITICAL | Review error handling |
| Synthesis fails without data | HIGH | Implement fallback (empty results) |
| Memory leak during timeouts | MEDIUM | Profile heap after test |

### Expected Output

```
=== CHAOS TEST 1: TIMEOUT CASCADE ===
Duration: 18 seconds
Probes Deployed: 10
Probes Timeout: 10 (100%)
Orchestrator Status: HEALTHY
Fallback Triggered: true
Result Quality: DEGRADED (0/10 probes)
```

---

## Test 2: API Rate Limit Stress (Start at 85% Usage)

### Objective
Validate rate limit handling and graceful backoff when API limits approached.

### Scenario
- Start with API usage at 85% of hourly limit
- Deploy 10 probes, each making ~15 API calls (150 total)
- Expected: Probes queue calls, some fail gracefully, system doesn't exceed limit

### Setup

```bash
# Rate limit configuration
HOURLY_LIMIT=60000           # Anthropic API limit
INITIAL_USAGE_PERCENT=85     # Start at 51000/60000
PROBES=10
CALLS_PER_PROBE=15
BACKOFF_STRATEGY=exponential
MAX_RETRIES=3
```

### Execution Steps

1. **Pre-populate API Usage**
   ```python
   # Simulate prior usage
   rate_limiter.consume(51000)  # 85% of limit
   ```

2. **Deploy Probes with Monitoring**
   ```bash
   ./test_runners/rate_limit_stress.sh \
     --usage-level=85 \
     --probes=10 \
     --calls-per-probe=15 \
     --backoff=exponential
   ```

3. **Track Rate Limit Events**
   - Log successful API calls
   - Log rate limit rejections
   - Log backoff delays
   - Log retry attempts

### Success Criteria

- [ ] Initial API usage at 85% ±2%
- [ ] System detects approaching limit (threshold: 90%)
- [ ] Probes implement exponential backoff (1s, 2s, 4s, 8s)
- [ ] No API call exceeds limit (100% of hourly quota)
- [ ] At least 8 out of 10 probes complete (>80% success)
- [ ] System remains responsive during rate limit period

### Failure Conditions

| Condition | Severity | Action |
|-----------|----------|--------|
| Exceeds hourly API limit | CRITICAL | Review rate limit middleware |
| No backoff implemented | HIGH | Implement exponential backoff |
| Orchestrator becomes unresponsive | CRITICAL | Add timeout to API calls |
| 429 errors not handled | HIGH | Add retry handler |
| Memory grows during backoff | MEDIUM | Profile memory allocation |

### Expected Output

```
=== CHAOS TEST 2: RATE LIMIT STRESS ===
Initial Usage: 51000/60000 (85%)
Probes Deployed: 10
API Calls Attempted: 150
API Calls Successful: 137 (91%)
API Calls Rate-Limited: 13 (9%)
Max Backoff Wait: 8.4s
Final Usage: 59800/60000 (99.7%)
Probes Completed: 9/10 (90%)
```

---

## Test 3: Context Pollution (Back-to-Back Runs)

### Objective
Validate that sequential SEARCH_PARTY runs don't leak state, credentials, or context from prior runs.

### Scenario
- Run SEARCH_PARTY 5 times sequentially on different targets
- Each run has unique credentials, target code, and expected results
- Verify isolation between runs

### Setup

```bash
# Context isolation test
RUNS=5
TARGETS=["app1", "app2", "app3", "app4", "app5"]
UNIQUE_CREDENTIALS=true
VERIFY_ISOLATION=true
```

### Execution Steps

1. **Run 1: Target A**
   - Credential: `token_A`
   - Target: `app1` (private repo)
   - Store baseline results

2. **Run 2: Target B**
   - Credential: `token_B`
   - Target: `app2` (different private repo)
   - Verify Run 1 credentials not leaked
   - Verify Run 1 target code not visible

3. **Run 3: Target C** (same target as Run 1)
   - Credential: `token_C` (different from Run 1)
   - Target: `app1` (same as Run 1, different creds)
   - Verify different results due to different credentials
   - Verify not using cached results from Run 1

4. **Run 4-5: Similar pattern**
   - Alternate targets and credentials
   - Check for cross-contamination

### Success Criteria

- [ ] Each run uses only its own credentials
- [ ] No credential bleed between runs
- [ ] Target-specific context isolated per run
- [ ] Cache properly keyed (includes target + credentials)
- [ ] Session state cleared between runs
- [ ] Probe memory cleaned up after each run
- [ ] No residual files in temp directories

### Failure Conditions

| Condition | Severity | Fix |
|-----------|----------|-----|
| Old credentials used in new run | CRITICAL | Review credential storage |
| Cache hit with wrong creds | CRITICAL | Add credential to cache key |
| Temp files not cleaned | MEDIUM | Implement cleanup hook |
| Probe state leaked to next run | HIGH | Review probe initialization |
| Session data persisted | HIGH | Clear session on start |

### Expected Output

```
=== CHAOS TEST 3: CONTEXT POLLUTION ===
Sequential Runs: 5
Runs Completed: 5/5 (100%)
Credential Contamination: 0 (PASS)
Context Leakage: 0 (PASS)
Cache Misses (expected): 5/5 (100%)
Temp Cleanup: PASS
Session Isolation: PASS
Overall: ISOLATED (no pollution detected)
```

---

## Test 4: Target Size Explosion (100K+ LOC)

### Objective
Validate SEARCH_PARTY handles massive codebases without performance degradation or memory exhaustion.

### Scenario
- Generate synthetic 100K-500K LOC codebase
- Deploy standard 10-probe team
- Measure memory, latency, accuracy under load

### Setup

```bash
# Large target configuration
TARGET_SIZES=[100000, 250000, 500000]  # LOC
PROBES=10
MEMORY_LIMIT_GB=8
TIMEOUT_BUFFER=2x  # Double normal timeouts
METRICS=[memory, latency, accuracy]
```

### Execution Steps

1. **Generate 100K LOC Target**
   ```bash
   ./test_generators/generate_codebase.py \
     --lines=100000 \
     --language=python \
     --complexity=high \
     --output=targets/100k
   ```

2. **Deploy SEARCH_PARTY**
   ```bash
   ./test_runners/scale_test.sh \
     --target=targets/100k \
     --probes=10 \
     --memory-limit=8GB \
     --monitor-metrics
   ```

3. **Monitor During Execution**
   - Memory: Should stay <8GB
   - Latency: Should scale O(log n), not O(n²)
   - Accuracy: Should maintain >95% precision

4. **Repeat for 250K and 500K**

### Success Criteria

- [ ] 100K LOC: Completes within 5 minutes
- [ ] 250K LOC: Completes within 10 minutes
- [ ] 500K LOC: Completes within 20 minutes
- [ ] Memory stays within 8GB limit
- [ ] Latency scales sub-linearly
- [ ] Probe accuracy stays >95%
- [ ] No out-of-memory errors
- [ ] No probe crashes from size

### Failure Conditions

| Condition | Severity | Optimization |
|-----------|----------|--------------|
| Memory exceeds 8GB | CRITICAL | Implement streaming analysis |
| Latency scales O(n²) | HIGH | Profile hot paths, add caching |
| Accuracy drops <90% | MEDIUM | Increase sampling rate |
| Probes crash on large targets | CRITICAL | Add size guards, streaming |
| Disk I/O becomes bottleneck | MEDIUM | Implement async I/O |

### Expected Output

```
=== CHAOS TEST 4: TARGET SIZE EXPLOSION ===

100K LOC Target:
  Duration: 4m 32s
  Memory Peak: 2.1 GB
  Probe Accuracy: 98.2%
  Status: PASS

250K LOC Target:
  Duration: 9m 18s
  Memory Peak: 4.6 GB
  Probe Accuracy: 97.8%
  Status: PASS

500K LOC Target:
  Duration: 19m 45s
  Memory Peak: 7.8 GB
  Probe Accuracy: 96.9%
  Status: PASS

Overall Scaling: O(log n) [OPTIMAL]
```

---

## Test 5: Orchestrator Crash (Kill Mid-Deployment)

### Objective
Validate that killing orchestrator mid-deployment doesn't corrupt data or leave orphaned probes.

### Scenario
- Deploy SEARCH_PARTY with 10 probes
- After probes are 50% complete, kill orchestrator process
- Verify graceful shutdown, cleanup, and safe rollback

### Setup

```bash
# Orchestrator crash test
PROBES=10
KILL_AT_PERCENT=50
SIGNAL=SIGKILL    # Force kill, not graceful
VERIFY_CLEANUP=true
```

### Execution Steps

1. **Deploy Probes**
   ```bash
   ./test_runners/crash_test.sh \
     --probes=10 \
     --kill-at=50% \
     --signal=SIGKILL \
     --monitor=process_list
   ```

2. **Monitor Probe Status**
   - Count running probes before kill
   - Kill orchestrator at 50%
   - Count lingering probes after kill

3. **Verify Cleanup**
   - No orphaned processes
   - No locked files
   - No corrupted state
   - Database consistent

4. **Restart Orchestrator**
   - Should start cleanly
   - Should not retry already-completed work
   - Should use crash recovery log

### Success Criteria

- [ ] All orphaned probes terminated within 5 seconds
- [ ] No locked files after crash
- [ ] Database transactions rolled back cleanly
- [ ] No data corruption detected
- [ ] Restart completes without errors
- [ ] Crash log recorded for debugging
- [ ] No duplicate work on restart

### Failure Conditions

| Condition | Severity | Recovery |
|-----------|----------|----------|
| Orphaned probes linger | HIGH | Implement timeout kill, process group cleanup |
| Database locked after crash | CRITICAL | Review transaction handling |
| Data corruption detected | CRITICAL | Implement checkpoints/WAL |
| Restart hangs | CRITICAL | Add startup timeouts |
| Duplicate work on restart | HIGH | Implement idempotency keys |

### Expected Output

```
=== CHAOS TEST 5: ORCHESTRATOR CRASH ===
Target: Medium complexity (20K LOC)
Probes Deployed: 10
Progress at Kill: 50%
Probes Still Running: 5
Kill Signal: SIGKILL
Time to Full Cleanup: 3.2s
Orphaned Processes: 0
Database Integrity: OK
Restart Time: 0.8s
Duplicate Work: 0
Overall: SAFE_SHUTDOWN (no corruption)
```

---

## Test 6: Memory Exhaustion Recovery

### Objective
Validate that SEARCH_PARTY detects memory pressure and implements graceful degradation.

### Scenario
- Constrain process to 512MB memory limit
- Deploy probes that would exceed limit
- Verify system doesn't crash, implements fallback

### Setup

```bash
# Memory exhaustion test
MEMORY_LIMIT_MB=512
PROBES=10
TARGET_LOC=50000
EXPECTED_BEHAVIOR=graceful_degradation
```

### Execution Steps

1. **Set Memory Limit**
   ```bash
   ulimit -v 524288  # 512MB virtual memory
   ```

2. **Deploy SEARCH_PARTY**
   ```bash
   ./test_runners/memory_test.sh \
     --memory-limit=512MB \
     --probes=10 \
     --target-size=50K
   ```

3. **Monitor Memory Allocation**
   - Track memory usage
   - Trigger at 80%, 90%, 95%, 100%
   - Test fallback at each threshold

4. **Verify Graceful Degradation**
   - Probes pause, don't crash
   - Partial results returned
   - System remains responsive

### Success Criteria

- [ ] Memory usage stays under 512MB
- [ ] System detects memory pressure (at 80%)
- [ ] Implements backoff/pause (at 90%)
- [ ] Returns partial results (at 100%)
- [ ] No crashes from OOM
- [ ] Recovery after memory freed

### Expected Output

```
=== CHAOS TEST 6: MEMORY EXHAUSTION ===
Memory Limit: 512 MB
Target Size: 50K LOC
Probes Deployed: 10

Memory Thresholds:
  80% (410 MB): Throttling enabled
  90% (460 MB): Backoff started
  95% (488 MB): 2 probes paused
  99% (507 MB): 4 probes paused

Final State:
  Probes Running: 6/10
  Memory Used: 508 MB (99%)
  Partial Results: 180/300 (60%)
  Graceful Degradation: YES
  Recovery: PASS
```

---

## Running All Chaos Tests

### Quick Run (All Tests, Defaults)

```bash
cd /home/user/Autonomous-Assignment-Program-Manager
./test_runners/chaos_suite.sh --all
```

### Individual Test Run

```bash
# Run specific test
./test_runners/chaos_suite.sh --test=timeout_cascade
./test_runners/chaos_suite.sh --test=rate_limit_stress
```

### Generate Report

```bash
./test_runners/chaos_report.sh --output=chaos_results.html
```

---

## Metrics & Thresholds

### Performance Targets

| Metric | Test 1 | Test 2 | Test 3 | Test 4 | Test 5 | Test 6 |
|--------|--------|--------|--------|--------|--------|--------|
| Success Rate | N/A | >80% | 100% | 100% | 100% | >90% |
| Crash Rate | 0% | 0% | 0% | 0% | 0% | 0% |
| Memory Peak | — | — | — | <8GB | — | <512MB |
| Recovery Time | <30s | <15s | <5s | — | <5s | <10s |
| Data Loss | 0 | 0 | 0 | 0 | 0 | 0 |

---

## Debugging Failed Tests

### Test 1 Fails (Timeout Cascade)
- Check probe timeout implementation
- Verify no timeout synchronization
- Review orchestrator timeout handler

### Test 2 Fails (Rate Limit)
- Check rate limit middleware
- Verify backoff algorithm
- Review API call logging

### Test 3 Fails (Context Pollution)
- Check credential storage
- Verify cache key format
- Review session cleanup

### Test 4 Fails (Target Size)
- Profile memory allocation
- Check for O(n²) algorithms
- Implement streaming analysis

### Test 5 Fails (Orchestrator Crash)
- Review process cleanup
- Check database transaction handling
- Add startup recovery log

### Test 6 Fails (Memory Exhaustion)
- Implement memory monitoring
- Add throttling logic
- Test graceful degradation

---

## Next Steps

- [ ] Implement test runner scripts in `test_runners/`
- [ ] Create baseline metrics
- [ ] Set up continuous chaos testing (daily)
- [ ] Create dashboards for trend analysis
- [ ] Document probe-specific chaos tests
- [ ] Add synthetic failure injection points

**Last Updated:** 2025-12-31
**Status:** ACTIVE
