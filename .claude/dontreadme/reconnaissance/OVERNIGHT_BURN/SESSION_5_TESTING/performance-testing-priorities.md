# Performance Testing Priorities & Implementation Guide
**SEARCH_PARTY Final Recommendations**

---

## Executive Summary

**Current State:**
- 53 pytest performance tests ✓
- 8 k6 load test scenarios ✓
- Clear SLA definitions ✓
- **3 CRITICAL gaps** blocking production

**Recommended Action:**
Implement 3 critical performance test suites before deployment. Estimated 40-50 hours of work spread across 3-5 days.

---

## Priority Matrix

```
IMPACT
  HIGH │
       │  ┌─────────────┬──────────────┐
       │  │ Swap Tests  │ Resilience   │
       │  │ (CRITICAL)  │ (CRITICAL)   │
       │  │ ~15h        │ ~20h         │
       │  ├─────────────┼──────────────┤
       │  │ MCP Tests   │ Failure      │
       │  │ (CRITICAL)  │ Scenarios    │
       │  │ ~15h        │ (MODERATE)   │
       │  │             │ ~12h         │
       │  └─────────────┴──────────────┘
       │
       └──────────────────────────────────
         LOW    EFFORT    HIGH
```

---

## 🔴 CRITICAL PRIORITY 1: Swap Operation Load Tests

### Business Context
- **User Impact:** High (faculty/residents use daily)
- **Data Integrity Risk:** High (schedule consistency critical)
- **Current Testing:** Unit tests only, zero load testing
- **Effort Estimate:** 15-20 hours
- **Timeline:** 2-3 days

### Why Critical
Swap operations are business-critical but completely untested under load:
- No concurrent swap testing
- No race condition scenarios
- No performance baseline
- No rollback consistency verification

### Implementation Plan

#### File: `backend/tests/performance/test_swap_execution_load.py`

```python
@pytest.mark.performance
@pytest.mark.slow
class TestSwapExecutionLoad:
    """Load tests for swap execution and matching."""

    @pytest.fixture(autouse=True)
    def setup_swap_test_data(self, db: Session, large_resident_dataset):
        """Create 4 weeks of assignments for swaps."""
        # Reuse large_assignment_dataset fixture
        # Create 100+ swappable blocks across 100 residents

    async def test_100_concurrent_one_to_one_swaps(self):
        """
        100 concurrent swap requests should complete within SLA.

        Requirement: < 500ms per swap (p95), 100% success consistency
        """
        # Test 100 simultaneous one-to-one swap requests
        # Verify: No race conditions, all succeed, no duplicates
        # Measure: Duration, consistency, data integrity

    async def test_swap_matching_performance_1000_candidates(self):
        """
        Finding swap match among 1000 candidates should be fast.

        Requirement: < 10 seconds for search + validation
        """
        # Create schedule with 1000+ potential matches
        # Measure: Search algorithm performance, ranking quality
        # Verify: Correct matches identified

    async def test_race_condition_same_shift_multiple_swaps(self):
        """
        Multiple swaps targeting same shift should handle gracefully.

        Requirement: First wins, others get clear error
        """
        # 10 concurrent swaps for same shift
        # Only 1 should succeed, others should fail cleanly
        # Verify: No data corruption, consistency

    async def test_swap_rollback_consistency_under_load(self):
        """
        Rollback after 100 swaps should restore all state consistently.

        Requirement: 100% consistency in 24-hour window
        """
        # Execute 100 swaps
        # Rollback 50 of them concurrently
        # Verify: State completely restored, no orphaned records

    async def test_swap_validation_performance_complex_schedule(self):
        """
        Swap validation with complex ACGME rules should be fast.

        Requirement: < 5 seconds for validation of complex swap
        """
        # Validate swap that would affect 80-hour rule calculations
        # Verify: Correct compliance check, performance acceptable
```

#### Test Data Requirements
```python
# Need 100+ distinct assignments per resident
# At least 4 weeks of schedule
# Mix of different rotation types
# Faculty with different supervision constraints
```

#### Expected Metrics
- Swap execution p50/p95/p99
- Match finding performance (candidate count vs. time)
- Rollback consistency percentage
- Race condition handling success rate

#### Pass/Fail Criteria
```
✓ 100 concurrent swaps: < 500ms per swap (p95)
✓ Matching 1000 candidates: < 10s
✓ Race condition handling: 0% data corruption
✓ Rollback: 100% consistency
```

---

## 🔴 CRITICAL PRIORITY 2: Resilience Framework Load Tests

### Business Context
- **User Impact:** High (system stability dependent)
- **Data Integrity Risk:** Medium (affects decision-making)
- **Current Testing:** Zero (brand new framework)
- **Effort Estimate:** 20-25 hours
- **Timeline:** 3-4 days

### Why Critical
Resilience framework is new and untested at any scale:
- N-1/N-2 contingency calculations not profiled
- Defense level scoring not benchmarked
- Circuit breaker implementation not validated
- Exotic frontier concepts (SIR models, etc.) not load-tested

### Implementation Plan

#### File: `backend/tests/performance/test_resilience_load.py`

```python
@pytest.mark.performance
@pytest.mark.slow
class TestResiliencePerformance:
    """Load tests for resilience framework operations."""

    async def test_n1_contingency_analysis_100_residents(self):
        """
        N-1 contingency analysis for 100 residents should be fast.

        Requirement: < 5 seconds (can run on every schedule change)
        """
        # Execute contingency analysis
        # Measure: Analysis time, memory, correctness
        # Verify: All residents/faculty covered, failure detection works

    async def test_defense_level_scoring_real_time(self):
        """
        Defense level scoring should provide real-time feedback.

        Requirement: < 1 second per scoring operation
        """
        # Score defense levels (GREEN/YELLOW/ORANGE/RED/BLACK)
        # Make 100 incremental schedule changes
        # Measure: Level transition time, consistency

    async def test_circuit_breaker_state_transitions(self):
        """
        Circuit breaker should trip/reset correctly under load.

        Requirement: < 500ms per state transition
        """
        # Trigger circuit breaker conditions
        # Verify: Correct state transitions, timing
        # Test recovery from failure conditions

    async def test_burnout_rt_calculation_sir_model(self):
        """
        Burnout Rt calculation (SIR model) should scale to 200 residents.

        Requirement: < 10 seconds for 200-resident population
        """
        # Execute SIR model for burnout prediction
        # Measure: Model calculation time, parameter accuracy
        # Verify: Results make clinical sense

    async def test_concurrent_resilience_evaluations(self):
        """
        Multiple concurrent resilience evaluations should not degrade.

        Requirement: 10 concurrent evaluations < 20 seconds total
        """
        # Run 10 concurrent resilience analyses
        # Verify: No database lock contention, results consistent

    async def test_resilience_metrics_under_heavy_load(self):
        """
        Resilience metrics collection should not impact API performance.

        Requirement: < 100ms overhead per request
        """
        # Generate load while collecting resilience metrics
        # Measure: API latency impact, metric accuracy
```

#### Dependencies to Test
```
- N-1/N-2 contingency solver (OR-Tools based?)
- SIR model implementation (NDlib)
- Circuit breaker state machine
- Metrics collection (OpenTelemetry)
- Defense level scoring algorithm
```

#### Expected Metrics
- Contingency analysis time vs. program size
- Defense level consistency across schedule changes
- Circuit breaker response time
- Burnout Rt accuracy vs. input parameters
- Metrics collection overhead

#### Pass/Fail Criteria
```
✓ N-1 analysis (100 res): < 5s
✓ Defense level scoring: < 1s per operation
✓ Circuit breaker transitions: < 500ms
✓ Burnout Rt (200 res): < 10s
✓ 10 concurrent analyses: < 20s total
✓ Metrics overhead: < 100ms per request
```

---

## 🔴 CRITICAL PRIORITY 3: MCP Server Performance Tests

### Business Context
- **User Impact:** High (core AI integration feature)
- **Data Integrity Risk:** Low (read-heavy operations mostly)
- **Current Testing:** Zero (MCP container only)
- **Effort Estimate:** 15-20 hours
- **Timeline:** 2-3 days

### Why Critical
MCP server is production-ready but unvalidated for performance:
- Tool discovery overhead unknown
- Tool chaining latency not measured
- API callback performance not tested
- Concurrent tool execution not validated

### Implementation Plan

#### File: `backend/tests/performance/test_mcp_integration_performance.py`

```python
@pytest.mark.performance
@pytest.mark.slow
class TestMCPToolPerformance:
    """Performance tests for MCP server tool execution."""

    async def test_single_tool_execution_latency(self):
        """
        Single tool execution should be fast.

        Requirement: < 500ms (p95) for typical tool
        """
        # Execute individual MCP tools
        # Measure: Tool execution time, p50/p95/p99
        # Expected: Read-heavy tools < 200ms, write tools < 500ms

    async def test_tool_discovery_performance(self):
        """
        Tool discovery should be instant (cached).

        Requirement: < 100ms for discovery request
        """
        # Call tool discovery endpoint
        # Measure: Discovery time, caching effectiveness
        # Verify: All 29+ tools discovered

    async def test_tool_chaining_latency(self):
        """
        Tool chaining (sequential tool calls) should scale linearly.

        Requirement: < 2 seconds for 3-level chain
        """
        # Execute tool chains: 1-level, 2-level, 3-level
        # Measure: Chaining overhead, scaling factor
        # Verify: Linear scaling (no exponential overhead)

    async def test_parallel_tool_execution(self):
        """
        Parallel tool execution should achieve good concurrency.

        Requirement: 10 concurrent tools < 1 second total
        """
        # Execute 10 tools in parallel
        # Measure: Parallelization efficiency, bottlenecks
        # Verify: No database connection exhaustion

    async def test_api_callback_roundtrip_latency(self):
        """
        MCP → API callback roundtrip should be low-latency.

        Requirement: < 200ms roundtrip
        """
        # Tool calls back to API endpoint
        # Measure: Callback latency (both directions)
        # Verify: No authentication/authorization bottlenecks

    async def test_concurrent_mcp_clients(self):
        """
        Multiple concurrent MCP clients should not degrade.

        Requirement: 10 concurrent clients with individual tool calls
        """
        # Spawn 10 simulated MCP clients
        # Each executes sequence of tool calls
        # Measure: Per-client latency, total throughput

    async def test_tool_error_handling_performance(self):
        """
        Error handling should not significantly impact latency.

        Requirement: Error paths < 1s even with failures
        """
        # Trigger various tool error conditions
        # Measure: Error handling latency
        # Verify: Graceful failure, no cascading failures
```

#### Test Setup
```python
@pytest.fixture
async def mcp_client():
    """Fixture for MCP server connection."""
    # Connect to MCP server (via docker-compose or local)
    # Setup authentication if needed

@pytest.fixture
async def api_callback_server():
    """Fixture for testing API callbacks from MCP."""
    # Lightweight mock API for callback testing
```

#### Expected Metrics
- Individual tool execution time (p50/p95/p99)
- Tool discovery response time
- Chaining overhead per level
- Parallel execution efficiency (scaling factor)
- Callback latency (both directions)
- Error handling cost

#### Pass/Fail Criteria
```
✓ Single tool execution: < 500ms (p95)
✓ Tool discovery: < 100ms
✓ 3-level chain: < 2s
✓ 10 concurrent tools: < 1s
✓ Callback roundtrip: < 200ms
✓ Error paths: < 1s
```

---

## 🟡 MODERATE PRIORITY 1: API Endpoint Baseline Expansion

### Why Moderate
Current baseline covers 10/20+ endpoints. Missing critical endpoints:
- `/api/swap/*` (4-5 endpoints)
- `/api/resilience/*` (2 endpoints)
- `/api/schedule/validate` (ACGME check)
- `/api/person/*/credentials` (bulk checks)
- `/api/assignments/conflicts` (conflict detection)

### Effort Estimate: 8-10 hours
### Timeline: 1-2 days

### Implementation
```javascript
// Expand load-tests/scenarios/api-baseline-extended.js
// Add 10+ new endpoints to measurement suite
// Establish individual baselines for each
// Generate comparison report vs. fast endpoints
```

---

## 🟡 MODERATE PRIORITY 2: Schedule Generation Algorithm Profiling

### Why Moderate
Current k6 test only measures HTTP response time. Missing:
- Solver iteration count
- Constraint propagation overhead
- Backtracking frequency
- Solution quality vs. time tradeoff
- Memory allocations during solving

### Effort Estimate: 12-15 hours
### Timeline: 1-2 days

### Implementation
```python
# Create: backend/tests/performance/test_schedule_generation_profiling.py
class TestScheduleGenerationProfiling:
    async def test_solver_iteration_count_scaling():
        """Track iterations needed vs. schedule complexity."""

    async def test_constraint_propagation_overhead():
        """Measure constraint propagation vs. total solving time."""

    async def test_solution_quality_vs_time_pareto():
        """Profile quality improvements over solving time."""

    async def test_memory_efficiency_large_schedules():
        """Track memory usage during solving."""
```

---

## 🟡 MODERATE PRIORITY 3: Failure Scenario Testing

### Why Moderate
System untested under degraded conditions:
- Database latency spike
- Redis unavailability
- Celery worker failure
- Rate limiter malfunction
- API timeout scenarios

### Effort Estimate: 10-12 hours
### Timeline: 1-2 days

### Implementation
```python
# Create: backend/tests/performance/test_resilience_failures.py
class TestFailureScenarios:
    async def test_performance_with_slow_database():
        """Measure API response with slow queries."""

    async def test_graceful_degradation_redis_down():
        """Verify system works without caching."""

    async def test_circuit_breaker_fallback_path():
        """Measure fallback performance."""
```

---

## Implementation Roadmap

### Phase 1: Critical Gaps (Week 1)
**Goal:** Close blocking gaps before production

```
Monday-Tuesday:    Swap operation tests (Priority 1)
  - test_swap_execution_load.py (15h)
  - Fixtures, concurrent testing, race conditions

Wednesday-Thursday: Resilience tests (Priority 2)
  - test_resilience_load.py (20h)
  - N-1/N-2, defense levels, circuit breaker

Thursday-Friday:   MCP server tests (Priority 3)
  - test_mcp_integration_performance.py (15h)
  - Tool discovery, chaining, callbacks

Weekend:           Testing, documentation, team review
```

### Phase 2: Moderate Gaps (Week 2)
**Goal:** Complete coverage expansion

```
Monday-Tuesday:    API baseline expansion (10h)
Tuesday-Wednesday: Algorithm profiling (12h)
Wednesday-Thursday: Failure scenarios (10h)
Thursday-Friday:   Integration testing, CI/CD setup
```

### Phase 3: Observability (Week 3)
**Goal:** Continuous monitoring infrastructure

```
Monday-Wednesday:  Prometheus/Grafana integration (15h)
Wednesday-Thursday: Performance regression detection (10h)
Thursday-Friday:   CI/CD performance checks, dashboards
```

---

## Resource Requirements

### Per Test Suite (15-25 hours)

#### Development
- 1 engineer, 3-5 days
- Access to: codebase, MCP server, staging environment

#### Infrastructure
- PostgreSQL (for realistic performance testing)
- Redis (for caching tests)
- MCP server container (for MCP tests)
- Load testing hardware (k6 agent or cloud)

#### Validation
- Code review (2-4 hours)
- Performance testing (2-4 hours)
- Documentation (2-3 hours)

### Total Effort
```
Critical Path: 50-60 hours
Parallel Work: Can reduce to 3-5 days with 2-3 engineers
Sequential Work: 1-2 weeks for single engineer
```

---

## Success Criteria

### Critical Tests
- [x] All critical tests pass with SLAs met
- [x] Tests integrated into pytest -m performance suite
- [x] k6 scenarios use consistent thresholds
- [x] Documentation complete with examples
- [x] Team trained on running tests
- [x] CI/CD integrated (if applicable)

### SLA Verification
```
✓ All operations within defined thresholds
✓ Error rates acceptable (< 1% for normal, < 5% for complex)
✓ No memory leaks detected (soak test)
✓ Concurrency tested at 10x expected load
✓ Failure scenarios handled gracefully
```

### Coverage Validation
```
✓ 70%+ of codebase touched by performance tests
✓ All user-facing operations benchmarked
✓ Business-critical features stress-tested
✓ Edge cases covered (empty data, extreme load)
```

---

## Team Assignments

### Recommended Task Breakdown

**Engineer 1: Swap Tests (Priority 1)**
- Fixtures and test data setup
- Concurrent swap testing
- Race condition scenarios
- Rollback validation
- Estimated: 15-20 hours, 2-3 days

**Engineer 2: Resilience Tests (Priority 2)**
- N-1/N-2 contingency integration
- Defense level scoring tests
- Circuit breaker validation
- SIR model performance
- Estimated: 20-25 hours, 3-4 days

**Engineer 3: MCP Tests (Priority 3)**
- MCP client setup
- Tool discovery testing
- Chaining and parallelization
- Callback testing
- Estimated: 15-20 hours, 2-3 days

**Engineering Lead: Integration & Documentation**
- Code review and approval
- SLA validation
- Documentation and examples
- Team training
- Estimated: 10-15 hours, ongoing

---

## Monitoring & Metrics Post-Implementation

### Dashboard Metrics
```
Real-time Performance:
  - Swap operation p95 latency
  - Resilience analysis completion time
  - MCP tool execution latency
  - API endpoint response times

Trend Analysis:
  - Performance degradation over time
  - Error rate trends
  - Throughput changes
  - Resource utilization patterns
```

### Alert Thresholds
```
🔴 CRITICAL (page on-call):
  - Any operation exceeds SLA by > 50%
  - Error rate > 5%
  - Memory leak detected in soak test

🟡 WARNING (create ticket):
  - Operation within SLA but trending toward threshold
  - Error rate > 2%
  - Throughput decline > 10%
```

---

## Risk Mitigation

### Testing Risks
```
Risk: Tests themselves are slow and block CI/CD
Mitigation:
  - Mark slow tests with @pytest.mark.slow
  - Run in separate CI job (nightly or manual)
  - Parallel execution where possible

Risk: Tests flaky due to timing sensitivity
Mitigation:
  - Use generous thresholds (p95 not p50)
  - Retry failed tests once
  - Investigate before dismissing as "flaky"

Risk: Performance regressions slip through
Mitigation:
  - Baseline current performance
  - Require < 5% degradation for approvals
  - Historical trend analysis
```

### Deployment Risks
```
Risk: Performance requirements too strict, can't deploy
Mitigation:
  - Set realistic thresholds (allow 20% buffer)
  - Prioritize critical path over edge cases
  - Allow variance in load test thresholds

Risk: Load tests aren't representative
Mitigation:
  - Use real-world data patterns
  - Simulate peak load correctly
  - Validate against production metrics
```

---

## Definition of Done

### For Each Test Suite
- [ ] All test methods implemented and passing
- [ ] SLAs documented with business justification
- [ ] Fixtures created and working correctly
- [ ] Edge cases covered
- [ ] Performance assertions in place
- [ ] Code reviewed and approved
- [ ] Documentation complete with examples
- [ ] CI/CD integration (if applicable)
- [ ] Team trained on execution
- [ ] Historical baseline established

### For Overall Initiative
- [ ] All 3 critical test suites complete
- [ ] 53 + N tests passing consistently
- [ ] No performance regressions from baseline
- [ ] Team confident in performance story
- [ ] Ready for production deployment

---

## Document Control

**Created:** 2025-12-30
**Updated:** N/A
**Status:** Ready for implementation
**Owner:** Engineering Lead
**Review Frequency:** Weekly during implementation

---

## Next Action Items

**This Week:**
1. [ ] Share analysis with engineering team
2. [ ] Schedule prioritization meeting
3. [ ] Assign engineers to critical tasks
4. [ ] Create detailed implementation tickets
5. [ ] Establish baseline for swap operations

**Next Week:**
1. [ ] Complete swap operation tests (critical)
2. [ ] Begin resilience framework tests
3. [ ] Start MCP server integration tests

**Following Week:**
1. [ ] All critical tests passing
2. [ ] Begin moderate priority work
3. [ ] Plan observability infrastructure

---

**Contact:** [Engineering Lead]
**Questions:** Refer to test-performance-coverage-analysis.md for detailed inventory
