# SCALING VALIDATION TESTS - Multi-Agent Coordination

> **Purpose:** Validate SEARCH_PARTY scales safely with increasing agent count
> **Created:** 2025-12-31
> **Focus:** Baseline performance, stress conditions, and failure points

---

## Overview

Scaling tests validate system behavior as agent count increases from baseline (10) to stress (15) to limit (20).

### Test Matrix

| Test | Agent Count | Target LOC | Expected Duration | Goal |
|------|-------------|-----------|------------------|------|
| **Baseline** | 10 agents | 20K | 3-5 min | Establish baseline metrics |
| **Stress** | 15 agents | 30K | 5-8 min | Identify bottlenecks |
| **Limit** | 20 agents | 40K | 10-15 min | Find breaking points |

---

## Test 1: 10-Agent Baseline

### Objective
Establish baseline performance metrics for standard SEARCH_PARTY deployment.

### Test Parameters

```yaml
Agent Configuration:
  Count: 10 agents (G2_RECON probes)
  Concurrency Model: Independent parallel execution
  Target: 20K LOC Python application
  Coordination: ORCHESTRATOR synthesis
  Duration: Target 3-5 minutes

Resource Allocation:
  CPU: 4 cores (per agent: 0.4 cores)
  Memory: 8GB total (per agent: 800MB)
  API Calls: 150-200 total
  Network: Unbounded
```

### Execution Steps

1. **Pre-flight Checks**
   ```bash
   # Verify resources available
   free -h  # Check memory
   nproc    # Check CPU count
   df -h    # Check disk space
   ```

2. **Deploy Baseline Test**
   ```bash
   ./test_runners/scale_test.sh \
     --mode=baseline \
     --agents=10 \
     --target-loc=20000 \
     --duration-target=4 \
     --metrics=all \
     --log-level=INFO
   ```

3. **Monitor Execution**
   - Agent startup: Should complete in <30 seconds
   - First results: Should arrive within 15 seconds
   - Synthesis time: Should be <5 seconds
   - Total duration: Should be 3-5 minutes

4. **Record Baseline Metrics**
   ```
   BASELINE_METRICS = {
       total_duration: 4m 23s,
       agent_count: 10,
       cpu_usage_peak: 68%,
       memory_usage_peak: 6.2 GB,
       api_calls: 175,
       probe_success_rate: 98.2%,
       result_accuracy: 97.1%,
       synthesis_time: 2.8s,
       network_throughput_mb: 12.4
   }
   ```

### Success Criteria

- [ ] All 10 agents start within 30 seconds
- [ ] First probe result arrives within 15 seconds
- [ ] Total execution time: 3-5 minutes
- [ ] CPU usage peaks <80%
- [ ] Memory usage peaks <7GB
- [ ] Probe success rate: >97%
- [ ] Result accuracy: >95%
- [ ] No agent crashes
- [ ] Synthesis completes without errors

### Metrics Collection

```python
baseline_metrics = {
    "agent_count": 10,
    "target_loc": 20000,
    "startup_time_sec": 28,
    "first_result_sec": 12,
    "total_duration_sec": 263,
    "cpu_peak_percent": 68,
    "memory_peak_mb": 6144,
    "api_calls_total": 175,
    "probe_success_count": 98,
    "probe_success_rate": 0.982,
    "result_accuracy": 0.971,
    "synthesis_time_sec": 2.8,
    "network_throughput_mbs": 12.4,
    "errors": 0,
    "timeouts": 0
}
```

### Expected Output

```
=== SCALING TEST 1: 10-AGENT BASELINE ===
Target: 20K LOC Python
Agents Deployed: 10
Startup Time: 28s

Execution Timeline:
  T+0s: Orchestrator initialized
  T+28s: All agents deployed
  T+40s: First probe result (probe_4)
  T+2m 15s: All probes returned
  T+2m 18s: Synthesis complete

Peak Metrics:
  CPU: 68% (4 cores available)
  Memory: 6.2 GB (8GB limit)
  API Calls: 175
  Network: 12.4 MB/s

Quality Metrics:
  Probe Success: 98/100 (98%)
  Accuracy: 97.1%
  Confidence: 0.94

Timing Breakdown:
  Probe Execution: 2m 15s
  Synthesis: 2.8s
  Overhead: 5.2s
  Total: 4m 23s

BASELINE_PASS: Yes
Metrics Recorded: baseline_20k_10agents.json
```

### Baseline Thresholds (For Comparison)

These values will be used as reference for stress and limit tests:

```
BASELINE_THRESHOLDS = {
    duration_sec: 263,
    memory_mb: 6144,
    cpu_percent: 68,
    api_calls: 175,
    accuracy: 0.971
}
```

---

## Test 2: 15-Agent Stress Test

### Objective
Identify bottlenecks and degradation when scaling to 15 agents (50% above baseline).

### Test Parameters

```yaml
Agent Configuration:
  Count: 15 agents (1.5x baseline)
  Target: 30K LOC (1.5x baseline)
  Expected Duration: 5-8 minutes
  Stress Model: Fixed parallelism + contention

Resource Limits:
  CPU: Same 4 cores (agents share more)
  Memory: Same 8GB (higher contention)
  API Calls: ~260 total (1.5x)
  Network: Same limits

Expected Degradation:
  Duration: +50% (not +100%, due to parallelism)
  Memory: +40% (some sharing, but more overhead)
  CPU: Increased contention, possible throttling
```

### Execution Steps

1. **Pre-Test Analysis**
   ```bash
   # Check resource availability
   ./test_runners/resource_check.sh

   # Retrieve baseline thresholds
   baseline_thresholds=$(cat baseline_20k_10agents.json)
   ```

2. **Deploy Stress Test**
   ```bash
   ./test_runners/scale_test.sh \
     --mode=stress \
     --agents=15 \
     --target-loc=30000 \
     --baseline-metrics=baseline_20k_10agents.json \
     --detect-bottlenecks \
     --log-level=DEBUG
   ```

3. **Monitor for Degradation**
   - Measure at 5min, 10min, 15min marks
   - Track CPU throttling events
   - Monitor memory pressure
   - Log any API rate limit hits

4. **Identify Bottlenecks**
   - Is duration degrading linearly or exponentially?
   - Where do agents spend most time?
   - Are there lock contentions?
   - Is memory becoming constraint?

5. **Record Stress Metrics**
   ```
   STRESS_METRICS = {
       agent_count: 15,
       target_loc: 30000,
       total_duration: 6m 42s,  # +52% vs baseline
       memory_peak: 7.8GB,      # +26% vs baseline
       cpu_peak: 85%,           # Higher contention
       api_calls: 261,          # +49%
       probe_success_rate: 96.4%, # -1.8%
       result_accuracy: 94.8%, # -2.3%
       synthesis_time: 4.1s    # +46%
   }
   ```

### Success Criteria

- [ ] All 15 agents start within 45 seconds
- [ ] Total execution time: 5-8 minutes (acceptable degradation)
- [ ] CPU usage peaks <95% (some throttling OK)
- [ ] Memory stays <8GB (critical limit)
- [ ] Probe success rate: >95% (acceptable drop)
- [ ] Result accuracy: >93% (acceptable drop)
- [ ] No deadlocks or hangs
- [ ] No agent crashes from resource contention

### Bottleneck Detection

```python
bottleneck_check = {
    "cpu_constrained": cpu_peak_percent > 90,
    "memory_constrained": memory_peak_mb > 7500,
    "api_rate_limited": rate_limit_hits > 0,
    "synthesis_bottleneck": synthesis_time_sec > 5,
    "lock_contention": probe_execution_std_dev > 15,  # High variance = contention
    "network_bottleneck": api_calls_incomplete > 5
}

# If cpu_constrained or memory_constrained, note limitation
# These indicate hardware scaling limits
```

### Expected Output

```
=== SCALING TEST 2: 15-AGENT STRESS ===
Target: 30K LOC Python
Agents Deployed: 15
Startup Time: 42s

Execution Timeline:
  T+0s: Orchestrator initialized
  T+42s: All agents deployed
  T+50s: First probe result (probe_8)
  T+3m 30s: All probes returned
  T+3m 34s: Synthesis complete

Peak Metrics:
  CPU: 85% (4 cores, higher contention)
  Memory: 7.8 GB (97.5% utilization)
  API Calls: 261
  Network: 18.2 MB/s

Quality Metrics:
  Probe Success: 144/150 (96%)
  Accuracy: 94.8%
  Confidence: 0.91

Degradation Analysis:
  Duration: +52% vs baseline (263s → 402s)
  Memory: +26% vs baseline (6.2GB → 7.8GB)
  CPU: +25% vs baseline (68% → 85%)
  Accuracy: -2.3% vs baseline (97.1% → 94.8%)

Bottleneck Analysis:
  CPU Constrained: YES (85% peak, 4 cores shared)
  Memory Constrained: NO (7.8GB / 8GB = 97%)
  API Rate Limited: NO
  Synthesis Bottleneck: NO
  Lock Contention: MODERATE (agent std dev = 12s)

Timing Breakdown:
  Probe Execution: 3m 30s
  Synthesis: 4.1s
  Overhead: 8.3s
  Total: 6m 42s

STRESS_PASS: Yes (within expected degradation)
Metrics Recorded: stress_30k_15agents.json

RECOMMENDATION:
  CPU is the primary scaling bottleneck.
  Memory utilization acceptable but near limit.
  Consider agent pooling or async optimization.
```

### Scaling Curve Analysis

```
SCALING CURVE:
  10 agents, 20K LOC: 4m 23s (baseline)
  15 agents, 30K LOC: 6m 42s (1.5x agents, 1.5x target)

Expected vs Actual:
  Naive expectation: Same time (perfect parallelism)
  Linear expectation: +50% time (due to resource sharing)
  Actual: +52% (very close to linear)

Conclusion: SUBLINEAR SCALING (good)
Scaling factor: 1.02x per agent added
```

---

## Test 3: 20-Agent Limit Test (Breaking Point Analysis)

### Objective
Find the maximum viable agent count and characterize system behavior at breaking point.

### Test Parameters

```yaml
Agent Configuration:
  Count: 20 agents (2x baseline)
  Target: 40K LOC (2x baseline)
  Expected Duration: 10-15 minutes (acceptable)
  Failure Model: Expect >5% agent failures

Expected Outcomes:
  1. Graceful degradation at 20 agents
  2. OR: Exceeding limits → need architectural changes
  3. New maximum stable count discovered

Resource Constraints:
  CPU: 4 cores (0.2 cores per agent - very tight)
  Memory: 8GB (400MB per agent average)
  API: ~400 calls (2x baseline)
```

### Execution Steps

1. **Pre-Limit Analysis**
   ```bash
   # Extrapolate from baseline/stress curves
   ./test_runners/predict_scaling.sh \
     --baseline=baseline_20k_10agents.json \
     --stress=stress_30k_15agents.json \
     --project-to=20
   ```

   Expected prediction:
   ```
   Projected Duration: 8-10 min
   Projected Memory: 7.9GB
   Projected CPU: 95%+
   Risk: HIGH (at limits)
   ```

2. **Deploy Limit Test with Safety Guards**
   ```bash
   ./test_runners/scale_test.sh \
     --mode=limit \
     --agents=20 \
     --target-loc=40000 \
     --safety-guards=enabled \
     --detect-breaking-point \
     --graceful-degradation=enabled \
     --log-level=TRACE
   ```

3. **Monitor for Breaking Points**
   - Watch for first agent timeout (usual breaking indicator)
   - Watch for probe crashes
   - Watch for synthesis failures
   - Watch for API rate limit hits
   - Watch for memory swaps (very bad)

4. **Characterize Failure Mode**
   ```python
   # If system breaks, identify mode:
   breaking_point_analysis = {
       "broke_at_agent_count": 18,  # Example
       "first_failure_time": "5m 42s",
       "failure_mode": "api_rate_limit",  # or timeout, memory, cpu
       "graceful_fallback": True,  # Did system recover?
       "max_viable_agents": 19,    # Highest count that works
       "headroom": 1,  # Agents before breaking point
   }
   ```

5. **Record Limit Metrics**

### Success Criteria (Flexible)

**Best Case (Passes Limit Test):**
- [ ] All 20 agents start and complete
- [ ] Total time: <15 minutes
- [ ] Memory stays <8GB
- [ ] CPU peak <100% (or acceptable throttling)
- [ ] Result accuracy: >90%
- [ ] System remains responsive

**Good Case (Graceful Degradation):**
- [ ] 18-19 agents succeed
- [ ] System detects overload
- [ ] Implements graceful fallback (partial results)
- [ ] No crashes or corruption
- [ ] Clear error messages
- [ ] Recovery time <10 seconds

**Acceptable Case (System Breaks Cleanly):**
- [ ] System detects overload before crash
- [ ] Clean error handling
- [ ] State consistent (no corruption)
- [ ] Documented maximum (e.g., "19 agents max on 4-core system")

### Expected Output (Success Path)

```
=== SCALING TEST 3: 20-AGENT LIMIT ===
Target: 40K LOC Python
Agents Deployed: 20
Startup Time: 52s

Execution Timeline:
  T+0s: Orchestrator initialized
  T+52s: All agents deployed
  T+58s: First probe result (probe_3)
  T+4m 45s: All probes returned
  T+4m 48s: Synthesis complete

Peak Metrics:
  CPU: 98% (4 cores, maxed out)
  Memory: 7.95 GB (99.4% utilization)
  API Calls: 398
  Network: 24.1 MB/s

Quality Metrics:
  Probe Success: 195/200 (97.5%)
  Accuracy: 93.2%
  Confidence: 0.89

Scaling Analysis:
  10 agents: 4m 23s (baseline)
  15 agents: 6m 42s (1.5x agents)
  20 agents: 8m 48s (2.0x agents)

  Scaling curve: O(log n) to O(sqrt n)
  Superlinear growth but subquadratic

Resource Saturation:
  CPU: 98% (SATURATED)
  Memory: 99.4% (SATURATED)
  API: 398/400 (99.5% allocation)

Headroom Analysis:
  CPU headroom: 2% (very tight)
  Memory headroom: 0.6% (critical)
  API headroom: 0.5% (critical)

Behavior Under Saturation:
  No crashes: ✓ YES
  No deadlocks: ✓ YES
  Graceful degradation: ✓ YES
  Result quality acceptable: ✓ YES (93.2% > 90% threshold)
  Recovery from transient spike: ✓ YES

Timing Breakdown:
  Probe Execution: 4m 45s
  Synthesis: 3.2s
  Overhead: 0.8s
  Total: 8m 48s

LIMIT_PASS: Yes (system stable at 20 agents)
Max Viable Agents: 20+ (on 4-core system with 8GB RAM)
Metrics Recorded: limit_40k_20agents.json

RECOMMENDATION:
  System can handle 20 concurrent agents on tested hardware.
  Both CPU and memory at saturation.
  Consider:
  - Async optimization to reduce per-agent overhead
  - Memory optimization (streaming processing)
  - Probe pooling/batching
  - Hardware upgrade if >20 agents needed
```

### Expected Output (Graceful Degradation Path)

```
=== SCALING TEST 3: 20-AGENT LIMIT (GRACEFUL DEGRADATION) ===
...
Agents Deployed: 20
Agent Startup: 18/20 successful (90%)
Failed at startup: 2 agents (memory limit)

Peak Metrics:
  CPU: 99%+ (THROTTLING)
  Memory: 8.0GB (at hard limit)
  API Calls: 312/400 (incomplete)

Overload Detection:
  Triggered at: T+2m 15s
  Cause: Memory allocation failure
  Response: Pause 2 agents, continue with 18
  Recovery Time: 8 seconds

Quality Degradation:
  Probe Success: 162/180 (90%)
  Accuracy: 89.1%
  Confidence: 0.85

Result: GRACEFUL_DEGRADATION_PASS
Max Stable Agents: 18 (on this hardware)
Recommendation: Limit deployment to <18 agents or upgrade hardware
```

---

## Scaling Across All Tests

### Scaling Table

| Metric | Baseline (10) | Stress (15) | Limit (20) | Scaling Type |
|--------|---------------|------------|-----------|--------------|
| **Duration** | 4m 23s | 6m 42s | 8m 48s | Sub-linear |
| **Memory** | 6.2 GB | 7.8 GB | 7.95 GB | Sublinear |
| **CPU** | 68% | 85% | 98% | Linear |
| **Accuracy** | 97.1% | 94.8% | 93.2% | Acceptable decline |
| **Success Rate** | 98% | 96% | 97.5% | Stable |

### Key Findings

**Good Scaling Indicators:**
- Duration grows O(log n) or O(sqrt n), not O(n)
- Memory growth sublinear
- Success rate remains >90%
- System remains responsive

**Warning Signs:**
- Duration grows O(n²) or worse
- Memory linear with agent count
- Accuracy drops >10% from baseline
- Frequent timeouts or crashes
- System becomes unresponsive

---

## Scaling Recommendations

### If Baseline Test Passes

✓ System ready for 10-agent deployments
✓ Baseline metrics established for regression testing

### If Stress Test Passes

✓ System can handle 15 agents with minor degradation
✓ CPU is primary bottleneck
✓ Memory has some headroom
→ **Recommendation:** Deploy with 12-15 agent teams for 25-30K LOC targets

### If Limit Test Passes

✓ System can handle 20+ agents
✓ Hardware is fully utilized
✓ Graceful degradation working
→ **Recommendation:** 20 agents is maximum on 4-core system; upgrade hardware for more

### If Tests Fail

✗ **Identify bottleneck:** CPU, memory, API, or network?
✗ **Optimization priority:**
  1. Fix O(n²) algorithms
  2. Implement streaming processing
  3. Add agent pooling
  4. Increase hardware resources

---

## Running Scaling Tests

### Run All Three Tests

```bash
./test_runners/scale_suite.sh --all
```

### Run Individual Test

```bash
./test_runners/scale_test.sh --mode=baseline --agents=10
./test_runners/scale_test.sh --mode=stress --agents=15
./test_runners/scale_test.sh --mode=limit --agents=20
```

### Generate Scaling Report

```bash
./test_runners/scaling_report.sh \
  --baseline=baseline_20k_10agents.json \
  --stress=stress_30k_15agents.json \
  --limit=limit_40k_20agents.json \
  --output=scaling_analysis.html
```

---

## Regression Testing

After changes to scheduling, probe coordination, or orchestrator:

```bash
# Compare against baseline
./test_runners/scale_test.sh --mode=baseline --compare=baseline_20k_10agents.json

# Alert if degradation >5%
```

**Last Updated:** 2025-12-31
**Status:** ACTIVE
