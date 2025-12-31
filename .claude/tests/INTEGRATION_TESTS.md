# INTEGRATION TESTS - Multi-Protocol Coordination

> **Purpose:** Validate SEARCH_PARTY end-to-end workflows and multi-protocol coordination
> **Created:** 2025-12-31
> **Focus:** Agent handoff, protocol coordination, and synthesis

---

## Overview

Integration tests validate the complete SEARCH_PARTY workflow from probe deployment through synthesis, including multi-protocol coordination and cross-session handling.

### Test Categories

| Test | Protocols | Duration | Complexity |
|------|-----------|----------|-----------|
| **G2_RECON → ORCHESTRATOR** | 2 | 5-8 min | Medium |
| **Multi-Protocol Coordination** | 4+ | 10-15 min | High |
| **Cross-Session Synthesis** | 2 | 8-12 min | High |

---

## Test 1: G2_RECON → ORCHESTRATOR Handoff

### Objective
Validate seamless transition from reconnaissance probe deployment through orchestrator synthesis.

### Test Workflow

```
Phase 1: G2_RECON Deployment
  ├─ Deploy 10 G2_RECON probes
  ├─ Probes analyze target independently
  ├─ Each probe generates findings report
  └─ Results queue for handoff

Phase 2: Probe Handoff
  ├─ G2_RECON → ORCHESTRATOR message passing
  ├─ Validate result format conversion
  ├─ Verify no data loss in handoff
  └─ Track timing and throughput

Phase 3: ORCHESTRATOR Synthesis
  ├─ Orchestrator aggregates 10 probe results
  ├─ Applies quality gates (validation, discrepancy, confidence)
  ├─ Performs cross-probe analysis
  └─ Generates final synthesis report

Phase 4: Output Delivery
  ├─ Format final report
  ├─ Verify all probe findings included
  ├─ Calculate coverage and accuracy
  └─ Return to user
```

### Setup

```yaml
Configuration:
  Probes: 10 G2_RECON
  Target: Medium complexity (20K LOC)
  Result Size: ~1-5MB per probe
  Handoff Protocol: Message queue (async)
  Synthesis Method: Aggregation + De-duplication

Instrumentation:
  - Probe-level: Execution time, findings count
  - Queue-level: Message throughput, latency
  - Synthesis-level: Aggregation time, deduplication efficiency
```

### Execution Steps

1. **Initialize Test Environment**
   ```bash
   ./test_runners/integration_test.sh \
     --test=g2_orchestrator_handoff \
     --probes=10 \
     --target=medium \
     --instrument=all \
     --log-level=DEBUG
   ```

2. **Phase 1: Deploy G2_RECON Probes**
   ```
   T+0s: Probes 1-10 initialized
   T+5s: All probes running
   T+10-180s: Probes analyze target
   T+180s: All probes complete, results queued
   ```

3. **Phase 2: Monitor Handoff**
   ```
   T+180s: ORCHESTRATOR receives probe_1 results
   T+185s: ORCHESTRATOR receives probe_2 results
   ...
   T+250s: ORCHESTRATOR has all 10 probe results
   Handoff Duration: 70 seconds (for 10 probes)
   Throughput: ~140KB/s
   ```

4. **Phase 3: Synthesis**
   ```
   T+250s: Begin aggregation
   T+250-260s: Quality gates check
   T+260-265s: De-duplicate findings
   T+265-270s: Generate final report
   T+270s: Complete
   Total Synthesis Time: 20 seconds
   ```

5. **Phase 4: Validate Output**
   ```bash
   # Verify all probe findings in final report
   grep -c "probe_" final_report.json  # Should show 10 probes mentioned

   # Verify coverage
   jq '.coverage' final_report.json    # Should match max of probe coverages

   # Verify confidence
   jq '.confidence' final_report.json  # Should be aggregated score
   ```

### Success Criteria

- [ ] All 10 probes deploy within 5 seconds
- [ ] All probes complete analysis
- [ ] Handoff completes within 60-90 seconds
- [ ] No data loss in handoff (all findings present)
- [ ] Quality gates pass all results
- [ ] Synthesis completes within 20 seconds
- [ ] Final report includes all probe findings
- [ ] No timeout or hanging

### Expected Output

```
=== INTEGRATION TEST 1: G2_RECON → ORCHESTRATOR HANDOFF ===

Workflow Timeline:
  Phase 1 (G2_RECON Deployment): 5s
    ├─ Probe 1-10: Started
    ├─ Probe startup: Successful
    └─ Status: ✓ READY

  Phase 2 (Probe Execution): 175s
    ├─ Probe 1-10: Running
    ├─ Avg execution: 175s
    ├─ Results queued: 10/10
    └─ Status: ✓ COMPLETE

  Phase 3 (Handoff): 70s
    ├─ Results received: 10/10
    ├─ Handoff throughput: 140KB/s
    ├─ Message queue depth: 0
    └─ Status: ✓ COMPLETE

  Phase 4 (Synthesis): 20s
    ├─ Quality validation: 10/10 pass
    ├─ Aggregation: 8s
    ├─ De-duplication: 4s
    ├─ Report generation: 8s
    └─ Status: ✓ COMPLETE

Total Duration: 270 seconds (4m 30s)

Result Statistics:
  Probes Completed: 10/10 (100%)
  Findings Total: 287 (aggregated from 10 probes)
  Findings Unique: 164 (after de-duplication)
  Data Integrity: 100% (no loss)
  Coverage: 92.3% (from probe results)
  Confidence: 0.88 (aggregated)

Quality Gates:
  Output Validation: 10/10 pass ✓
  Discrepancy Detection: No high variance ✓
  Confidence Aggregation: 0.88 ✓

Integration Status:
  G2_RECON → ORCHESTRATOR: ✓ PASS
  Message Passing: ✓ PASS
  Data Integrity: ✓ PASS
  Timing Performance: ✓ PASS
  Result Synthesis: ✓ PASS

TEST_PASS: Handoff workflow successful
```

---

## Test 2: Multi-Protocol Coordination

### Objective
Validate that SEARCH_PARTY coordinates multiple probe protocols simultaneously without interference.

### Protocols Under Test

```yaml
Protocol 1: G2_RECON (10 probes)
  - General reconnaissance
  - Fast, broad analysis
  - ~30KB results per probe

Protocol 2: DEEP_ANALYSIS (3 probes)
  - Focused deep dives
  - Slower, but more detailed
  - ~500KB results per probe

Protocol 3: SECURITY_FOCUSED (5 probes)
  - Security-specific analysis
  - Specialized detectors
  - ~80KB results per probe

Protocol 4: PERFORMANCE_METRICS (4 probes)
  - Performance analysis
  - Metrics and optimization
  - ~100KB results per probe

Total: 22 concurrent probes, 4 distinct protocols
```

### Setup

```yaml
Deployment:
  G2_RECON: 10 probes
  DEEP_ANALYSIS: 3 probes
  SECURITY_FOCUSED: 5 probes
  PERFORMANCE_METRICS: 4 probes
  Total: 22 probes

Coordination Requirements:
  1. No resource contention (probes share CPU/memory)
  2. Protocol-specific logic preserved
  3. Results aggregated per protocol
  4. Cross-protocol findings merged
  5. Final synthesis integrates all protocols

Synchronization Points:
  - All probes start within 10 seconds
  - All probes complete before synthesis starts
  - Each protocol validates independently
  - Synthesis merges results in protocol order
```

### Execution Steps

1. **Deploy Multi-Protocol Team**
   ```bash
   ./test_runners/integration_test.sh \
     --test=multi_protocol_coordination \
     --protocols=G2_RECON,DEEP_ANALYSIS,SECURITY_FOCUSED,PERFORMANCE_METRICS \
     --probe-counts=10,3,5,4 \
     --coordination=strict \
     --detect-interference
   ```

2. **Monitor Protocol Isolation**
   ```
   T+0s: Start all 22 probes

   G2_RECON: [==============] 10 probes
   DEEP_ANALYSIS: [============================] 3 probes
   SECURITY: [===============] 5 probes
   PERF: [==================] 4 probes

   Monitor for:
   - CPU contention (should be smooth, not spiky)
   - Memory sharing (should be coordinated, not competing)
   - I/O patterns (should be sequential, not parallel conflicts)
   - Network usage (should be fair share)
   ```

3. **Validate Protocol Boundaries**
   ```python
   # Each protocol should return results in its own format
   g2_results = filter_by_protocol(all_results, "G2_RECON")
   assert len(g2_results) == 10
   assert all(r.schema == "g2_recon_schema" for r in g2_results)

   deep_results = filter_by_protocol(all_results, "DEEP_ANALYSIS")
   assert len(deep_results) == 3
   assert all(r.schema == "deep_analysis_schema" for r in deep_results)
   ```

4. **Synthesis Across Protocols**
   ```
   Phase A: G2_RECON aggregation (10 results)
   Phase B: DEEP_ANALYSIS aggregation (3 results)
   Phase C: SECURITY aggregation (5 results)
   Phase D: PERFORMANCE aggregation (4 results)
   Phase E: Cross-protocol merge
   Phase F: Final report generation
   ```

### Success Criteria

- [ ] All 22 probes deploy within 15 seconds
- [ ] All probes complete without interference
- [ ] No protocol crosstalk (results stay in correct protocol)
- [ ] CPU utilization even (not spiky from contention)
- [ ] Memory pressure acceptable (<8GB)
- [ ] Per-protocol aggregation succeeds
- [ ] Cross-protocol synthesis succeeds
- [ ] Final report includes all 4 protocols

### Expected Output

```
=== INTEGRATION TEST 2: MULTI-PROTOCOL COORDINATION ===

Protocols: 4 (G2_RECON, DEEP_ANALYSIS, SECURITY, PERFORMANCE)
Total Probes: 22

Deployment Phase:
  G2_RECON (10): Started at T+0s, completed at T+2s ✓
  DEEP_ANALYSIS (3): Started at T+1s, completed at T+3s ✓
  SECURITY (5): Started at T+0s, completed at T+4s ✓
  PERFORMANCE (4): Started at T+1s, completed at T+2s ✓
  Status: ALL STARTED ✓

Execution Phase:
  Timeline (sample):
    0-100s: All probes running
    100-300s: G2 and SECURITY completing
    300-400s: DEEP_ANALYSIS completing (slower)
    400s: All probes done

  Resource Utilization:
    CPU: 75% (smooth, no spikes) ✓
    Memory: 6.8GB (no pressure) ✓
    Network: Balanced across protocols ✓

Completion Phase:
  G2_RECON: 10/10 complete (300 findings)
  DEEP_ANALYSIS: 3/3 complete (450 deep findings)
  SECURITY: 5/5 complete (180 security issues)
  PERFORMANCE: 4/4 complete (120 metrics)

Result Integrity:
  G2_RECON results: 300KB aggregated
  DEEP_ANALYSIS results: 1.5MB aggregated
  SECURITY results: 400KB aggregated
  PERFORMANCE results: 400KB aggregated
  Total: 2.6MB

Protocol Isolation:
  G2_RECON schema: ✓ Preserved
  DEEP_ANALYSIS schema: ✓ Preserved
  SECURITY schema: ✓ Preserved
  PERFORMANCE schema: ✓ Preserved
  Cross-protocol contamination: None ✓

Synthesis Phase:
  Per-protocol aggregation: 4/4 success ✓
  Cross-protocol merge: Success ✓
  Confidence calculation: 0.91 ✓
  Final report generation: 4.2s ✓

Quality Metrics:
  Total Findings: 1050 (aggregated)
  Unique Findings: 847 (after de-duplication)
  Deduplication Ratio: 80.7%
  Coverage (all protocols): 94.2%
  Confidence: 0.91

Protocol Distribution in Report:
  G2_RECON: 28% (301 findings)
  DEEP_ANALYSIS: 43% (365 findings)
  SECURITY: 17% (145 findings)
  PERFORMANCE: 12% (102 findings)

Timing Summary:
  Deployment: 4s
  Execution: 400s
  Synthesis: 12s
  Total: 416s (6m 56s)

Coordination Status:
  No protocol interference: ✓ PASS
  All boundaries preserved: ✓ PASS
  Cross-protocol synthesis: ✓ PASS
  Resource contention: None ✓

TEST_PASS: Multi-protocol coordination working
```

---

## Test 3: Cross-Session Synthesis

### Objective
Validate that SEARCH_PARTY can handle results from multiple independent sessions and synthesize coherent findings.

### Test Scenario

```
Session A: Run 1 on Monday (10 probes, 20K LOC)
  └─ Results: 150 findings, confidence 0.88

Session B: Run 2 on Wednesday (8 probes, 25K LOC)
  └─ Results: 180 findings, confidence 0.82

Cross-Session Task:
  Merge Session A + Session B results
  Identify:
    - Consistent findings (in both)
    - New findings in Session B
    - Resolved findings (not in Session B)
    - Regression findings (worse in Session B)
```

### Setup

```yaml
Session A:
  Date: 2025-12-27
  Probes: 10
  Target Version: 1.0
  Target LOC: 20K
  Findings: 150
  Confidence: 0.88

Session B:
  Date: 2025-12-31 (4 days later)
  Probes: 8 (2 probes offline)
  Target Version: 1.1 (code changed)
  Target LOC: 25K (5K new code)
  Findings: 180
  Confidence: 0.82 (different probes)

Cross-Session Analysis:
  1. De-normalize findings to location+type
  2. Find overlaps (same location, same issue)
  3. Identify new issues (in B, not in A)
  4. Identify resolved issues (in A, not in B)
  5. Track severity changes
  6. Generate delta report
```

### Execution Steps

1. **Load Session A Results**
   ```bash
   session_a=$(load_results("session_a_2025-12-27.json"))
   # 150 findings from 10 probes
   ```

2. **Load Session B Results**
   ```bash
   session_b=$(load_results("session_b_2025-12-31.json"))
   # 180 findings from 8 probes
   ```

3. **Normalize Finding Identifiers**
   ```python
   # Convert to canonical form: {file}:{line}:{type}:{severity}

   def normalize_finding(finding):
       return {
           "location": f"{finding['file']}:{finding['line']}",
           "type": finding['issue_type'],
           "severity": finding['severity'],
           "description": finding['description'],
       }

   session_a_normalized = [normalize_finding(f) for f in session_a.findings]
   session_b_normalized = [normalize_finding(f) for f in session_b.findings]
   ```

4. **Perform Cross-Session Analysis**
   ```python
   consistent = find_intersection(session_a_normalized, session_b_normalized)
   new_in_b = find_difference(session_b_normalized, session_a_normalized)
   resolved_in_b = find_difference(session_a_normalized, session_b_normalized)

   # Track severity changes
   for finding_a in session_a_normalized:
       matching_b = find_in_session(session_b_normalized, finding_a)
       if matching_b and finding_a.severity != matching_b.severity:
           severity_changes.append((finding_a, matching_b))
   ```

5. **Generate Delta Report**
   ```
   Cross-Session Synthesis Report

   Consistent (both sessions): 120 findings
   New in Session B: 60 findings
   Resolved in Session B: 30 findings

   Severity Changes:
     Critical → High: 3 findings
     High → Medium: 5 findings
     Low → Critical: 1 finding

   Overall Trend: DEGRADATION (+30 net new findings)
   ```

### Success Criteria

- [ ] Session A results load correctly (150 findings)
- [ ] Session B results load correctly (180 findings)
- [ ] Normalization preserves finding identity
- [ ] Consistent findings identified correctly
- [ ] New findings identified correctly
- [ ] Resolved findings identified correctly
- [ ] Severity changes tracked
- [ ] Delta report generated accurately

### Expected Output

```
=== INTEGRATION TEST 3: CROSS-SESSION SYNTHESIS ===

Session A:
  Date: 2025-12-27
  Probes: 10/10 (100% success)
  Target LOC: 20K
  Findings: 150
  Confidence: 0.88

Session B:
  Date: 2025-12-31
  Probes: 8/10 (80% success, 2 probes offline)
  Target LOC: 25K (+5K new code)
  Findings: 180
  Confidence: 0.82

Cross-Session Delta Analysis:
  ┌─ Consistent Findings (present in both):
  │  └─ Count: 120
  │     Examples:
  │       - SQL injection in auth.py:42 (HIGH)
  │       - Missing input validation in forms.py:156 (MEDIUM)
  │       - Hard-coded credentials in config.py:8 (CRITICAL)
  │     Status: Unresolved issues
  │
  ├─ New Findings (Session B only):
  │  └─ Count: 60
  │     Examples:
  │       - Race condition in cache.py:34 (HIGH) [NEW]
  │       - Deprecated library usage in utils.py:12 (MEDIUM) [NEW]
  │       - Missing CSRF token in forms.py:201 (MEDIUM) [NEW]
  │     Status: Issues introduced in new code
  │
  └─ Resolved Findings (Session A only):
     └─ Count: 30
        Examples:
          - Memory leak in parser.py:89 [FIXED]
          - Buffer overflow risk in crypto.py:45 [FIXED]
          - Missing bounds check in array.py:67 [FIXED]
        Status: Successfully resolved

Severity Changes:
  CRITICAL (0): Critical → High (0)
  HIGH (8):
    - Security issue in api.py:78: HIGH → CRITICAL ⚠️
    - Buffer overflow in utils.py:234: HIGH → MEDIUM ✓
  MEDIUM (5):
    - Performance issue in loop.py:45: MEDIUM → LOW ✓
  LOW (3):
    - Code style in formatter.py:89: LOW → MEDIUM ⚠️

Overall Trend Analysis:
  Consistent Issues: 120 (unresolved, ongoing)
  New Issues: 60 (introduced since last session)
  Resolved Issues: 30 (fixed since last session)

  Net Change: +30 issues (60 new - 30 resolved)
  Trend: DEGRADATION (more issues than improvements)

Code Changes Analysis:
  Lines Changed: 5000 (25% of codebase)
  Issues per 1000 LOC (Session A): 7.5
  Issues per 1000 LOC (Session B): 7.2
  Trend: Slight improvement in issue density

Quality Metrics:
  Session A Confidence: 0.88
  Session B Confidence: 0.82 (-6% due to fewer probes)
  Delta Confidence: 0.80 (from cross-session aggregation)

Recommendations:
  1. Address new high/critical issues in cache.py and api.py
  2. Maintain fixes in resolved areas (don't regress)
  3. Investigate why parser.py and crypto.py fixes haven't regressed
  4. Code changes improved issue density but added new issues

Synthesis Status:
  Session A load: ✓ PASS
  Session B load: ✓ PASS
  Normalization: ✓ PASS
  Delta analysis: ✓ PASS
  Report generation: ✓ PASS

TEST_PASS: Cross-session synthesis working
```

---

## Integration Test Execution

### Run All Integration Tests

```bash
./test_runners/integration_suite.sh --all
```

### Run Individual Test

```bash
./test_runners/integration_test.sh --test=g2_orchestrator_handoff
./test_runners/integration_test.sh --test=multi_protocol_coordination
./test_runners/integration_test.sh --test=cross_session_synthesis
```

### Full End-to-End Test

```bash
# Run realistic workflow: Deploy → Execute → Synthesize → Report
./test_runners/e2e_test.sh \
  --target=real_codebase \
  --probes=10 \
  --protocols=all \
  --sessions=1 \
  --full-report
```

---

## Debugging Integration Issues

### Test 1 Fails (G2_RECON → ORCHESTRATOR)

**Common Issue:** Probe timeout during handoff
**Debug Steps:**
```bash
# Check message queue
docker-compose exec mcp-server redis-cli LLEN probe_results_queue

# Monitor orchestrator logs
docker-compose logs -f orchestrator | grep handoff
```

**Common Issue:** Data loss in handoff
**Debug Steps:**
```bash
# Compare probe results before/after handoff
probe_count_before=$(jq '.probes | length' session.json)
probe_count_after=$(jq '.results | length' orchestrator_input.json)
```

### Test 2 Fails (Multi-Protocol)

**Common Issue:** Protocol interference
**Debug Steps:**
```bash
# Check CPU/memory per protocol
ps aux | grep probe | awk '{print $3, $4, $12}' | sort

# Verify protocol boundaries
for proto in G2_RECON DEEP_ANALYSIS SECURITY PERFORMANCE; do
  jq ".results[] | select(.protocol == \"$proto\") | .id" | wc -l
done
```

### Test 3 Fails (Cross-Session)

**Common Issue:** Normalization inconsistency
**Debug Steps:**
```bash
# Check normalized finding format
jq '.findings[0] | keys' session_a.json
jq '.findings[0] | keys' session_b.json

# Verify matching logic
jq '.delta.consistent | length' cross_session_report.json
```

---

**Last Updated:** 2025-12-31
**Status:** ACTIVE
