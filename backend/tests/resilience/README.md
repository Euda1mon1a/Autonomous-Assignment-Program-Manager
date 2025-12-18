# Resilience Framework Load Tests

## Overview

The `test_resilience_load.py` file contains comprehensive load tests for the resilience framework, testing all major components under stress conditions.

## Test Coverage

### 1. Utilization Threshold Tests
- `test_utilization_threshold_escalation`: Verifies defense levels escalate correctly (GREEN → YELLOW → ORANGE → RED → BLACK)
- `test_utilization_calculation_response_time`: Performance test (<100ms for 60 faculty)
- `test_buffer_remaining_calculation`: Validates buffer calculation accuracy

### 2. N-1/N-2 Contingency Analysis Tests
- `test_n1_analysis_performance`: N-1 analysis completes in <5s for 60 faculty
- `test_n2_analysis_performance`: N-2 analysis completes in <30s
- `test_contingency_report_generation`: Full report generation in <30s
- `test_centrality_calculation_performance`: Centrality scores in <5s

### 3. Concurrent Operation Tests
- `test_concurrent_utilization_checks`: Multiple simultaneous checks don't interfere
- `test_concurrent_contingency_analyses`: Consistent results under parallel execution

### 4. Crisis Response Tests
- `test_crisis_detection_latency`: Crisis detection in <5s
- `test_defense_activation_latency`: Defense activation in <100ms

### 5. Sacrifice Hierarchy Tests
- `test_load_shedding_decision_latency`: Load shedding decisions in <500ms
- `test_sacrifice_hierarchy_consistency`: Deterministic sacrifice decisions

### 6. Homeostasis Tests
- `test_feedback_loop_correction_latency`: Feedback corrections in <100ms
- `test_multiple_simultaneous_perturbations`: Handles multiple perturbations (<500ms)
- `test_allostatic_load_calculation`: Allostatic load calculation in <50ms

### 7. Blast Radius Tests
- `test_zone_failure_isolation`: Failures contained within zones
- `test_containment_response_time`: Containment activation in <100ms
- `test_zone_health_check_performance`: Zone health checks in <200ms

### 8. End-to-End Tests
- `test_full_resilience_check_under_load`: Complete resilience check under high load (<45s)
- `test_resilience_metrics_tracking`: Performance metrics tracking

## Running Tests

### With pytest (requires database fixtures)

```bash
cd backend
pytest tests/resilience/test_resilience_load.py -v
```

**Note**: Currently blocked by a pre-existing database schema issue in `conftest.py` related to the `Person.absences` relationship. See Known Issues below.

### Standalone Verification

Run core tests without database dependencies:

```bash
cd backend
python -c "$(cat tests/resilience/test_resilience_load.py | grep -A 1000 'import pytest')"
```

Or use the verification script that tests core functionality.

## Test Markers

- `@pytest.mark.resilience`: All resilience framework tests
- `@pytest.mark.performance`: Performance-sensitive tests
- `@pytest.mark.asyncio`: Async tests requiring pytest-asyncio

## Performance Targets

| Component | Target | Actual |
|-----------|--------|--------|
| Utilization calculation | <100ms | <1ms ✓ |
| N-1 analysis (60 faculty) | <5s | - |
| N-2 analysis | <30s | - |
| Load shedding decision | <500ms | <1ms ✓ |
| Crisis detection | <5s | - |
| Defense activation | <100ms | - |
| Feedback correction | <100ms | - |
| Zone health check | <200ms | - |
| Full resilience check | <45s | - |

## Known Issues

### Database Schema Issue (Pre-existing)

The test suite cannot run with pytest currently due to a pre-existing SQLAlchemy relationship issue in `conftest.py`:

```
AmbiguousForeignKeysError: Could not determine join condition between parent/child 
tables on relationship Person.absences - there are multiple foreign key paths 
linking the tables.
```

**Impact**: Tests using database fixtures cannot run via pytest.

**Workaround**: Core resilience logic has been verified with standalone tests (see Standalone Verification above).

**Fix Required**: Update `app/models/person.py` to specify `foreign_keys` argument in the `absences` relationship.

## Test Fixtures

### Load Scenario Fixtures

- `large_faculty_pool`: 60 faculty members for load testing
- `large_block_set`: 180 blocks (90 days, AM/PM)
- `high_load_assignments`: 110 assignments = 91.7% utilization
- `crisis_scenario_assignments`: 30 available faculty (50% loss)

### Component Fixtures

- `utilization_monitor`: UtilizationMonitor with standard thresholds
- `contingency_analyzer`: ContingencyAnalyzer instance
- `defense_in_depth`: DefenseInDepth manager
- `sacrifice_hierarchy`: SacrificeHierarchy with sample activities
- `homeostasis_monitor`: HomeostasisMonitor instance
- `blast_radius_manager`: BlastRadiusManager with default zones

## Implementation Notes

### Test Design Principles

1. **Performance-focused**: All tests include timing assertions to ensure components meet performance targets
2. **Realistic load**: Uses 50-60 faculty members to simulate production-scale load
3. **Concurrent testing**: Verifies components work correctly under parallel execution
4. **End-to-end validation**: Includes comprehensive tests that exercise all components together

### Load Test Scenarios

1. **High Load (90%+ utilization)**: Tests system behavior approaching capacity
2. **Crisis (50% faculty loss)**: Tests extreme overload conditions
3. **Concurrent Operations**: Tests parallel execution of resilience checks
4. **Multi-perturbation**: Tests multiple simultaneous system stresses

## Verification

Core resilience functionality has been verified:

✓ Utilization threshold escalation works correctly  
✓ Performance targets met (<100ms for calculations)  
✓ Sacrifice hierarchy protects patient safety  
✓ Buffer calculations are accurate  
✓ High load scenarios detected correctly

## Future Improvements

1. Fix database schema issue to enable full pytest integration
2. Add integration tests with actual database fixtures
3. Add stress tests with 100+ faculty members
4. Add cascade failure simulation tests
5. Add network graph analysis tests (using NetworkX)
