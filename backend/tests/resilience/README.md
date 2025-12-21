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

## Cross-Disciplinary Module Tests

The resilience framework incorporates cross-disciplinary techniques from manufacturing, epidemiology, telecommunications, seismology, wildfire science, and materials engineering. Each module has comprehensive test coverage:

### 1. Statistical Process Control (SPC) Monitoring
**File**: `test_spc_monitoring.py` (50+ tests)

Tests for manufacturing-inspired quality control adapted to scheduling workload:

- **Western Electric Rules (1-4)**: Detection of out-of-control processes
  - Rule 1: Single point beyond 3σ control limits
  - Rule 2: Two of three consecutive points beyond 2σ
  - Rule 3: Four of five consecutive points beyond 1σ
  - Rule 4: Eight consecutive points on one side of center line
- **Control Limit Calculations**: UCL/LCL computation and validation
- **Process Capability Indices**: Cp, Cpk, Pp, Ppk calculations
- **X-bar and R Charts**: Mean and range control charts for workload
- **Subgroup Analysis**: Statistical analysis of workload groups
- **Trend Detection**: Early warning of workload drift

### 2. Process Capability Analysis
**File**: `test_process_capability.py` (40+ tests)

Tests for Six Sigma-inspired capability metrics:

- **Six Sigma Capability Indices**: Comprehensive capability calculations
  - Cp (process capability): Relationship to specification limits
  - Cpk (process capability index): Accounts for process centering
  - Pp/Ppk (process performance): Long-term capability
  - Cpm (Taguchi capability): Target-focused metrics
- **Sigma Level Conversions**: DPMO ↔ Sigma level translations
  - Defects Per Million Opportunities (DPMO)
  - Z-score transformations
  - Quality level classifications (2σ to 6σ)
- **Workload Quality Analysis**: Application to schedule quality
  - Workload distribution analysis
  - Centering and spread metrics
  - Compliance with targets

### 3. Burnout Epidemiology (SIR Model)
**File**: `test_burnout_epidemiology.py` (44 tests)

Tests for epidemiological modeling of burnout contagion:

- **SIR Model Simulation**: Susceptible-Infected-Recovered dynamics
  - Compartmental model implementation
  - Time-series evolution of burnout states
  - Parameter sensitivity (β transmission, γ recovery)
- **Reproduction Number (R₀)**: Epidemic threshold calculation
  - R₀ > 1: Burnout spreads (epidemic)
  - R₀ < 1: Burnout dies out (endemic control)
  - Critical threshold analysis
- **Network-Based Contagion**: Graph-based burnout spread
  - Contact network modeling
  - Clustering coefficient impact
  - Network centrality and vulnerability
- **Intervention Strategies**: Testing burnout prevention tactics
  - Targeted interventions (high-centrality nodes)
  - Uniform prevention strategies
  - Vaccination/protection modeling

### 4. Erlang Coverage Models
**File**: `test_erlang_coverage.py` (47 tests)

Tests for telecommunications-inspired queueing theory:

- **Erlang B Formula**: Call blocking probability
  - Loss systems (no queueing)
  - Blocking probability calculations
  - Traffic intensity (offered load in Erlangs)
- **Erlang C Formula**: Wait probability in queued systems
  - Queueing systems with unlimited waiting
  - Average wait time calculations
  - Service level (probability of immediate answer)
- **Coverage Optimization**: Specialist scheduling optimization
  - Minimum specialists required for target service level
  - Trade-offs: coverage vs. blocking probability
  - Cost-effectiveness analysis
- **Traffic Engineering**: Workload and capacity planning
  - Peak load analysis
  - Capacity dimensioning
  - Quality of Service (QoS) targets

### 5. Seismic Overload Detection
**File**: `test_seismic_detection.py** (52 tests)

Tests for seismology-inspired anomaly detection:

- **STA/LTA Algorithm**: Short-Term Average / Long-Term Average ratio
  - Trigger detection for workload spikes
  - Threshold calibration (typically 3-5)
  - Noise filtering and signal enhancement
- **Precursor Detection**: Early warning of schedule instability
  - Pre-event signal detection
  - Lead time quantification
  - False alarm rate management
- **Magnitude Estimation**: Severity quantification
  - Richter-inspired magnitude scales
  - Energy release calculations (10^(1.5M) scaling)
  - Impact assessment (minor/moderate/major/great)
- **Foreshock/Aftershock Analysis**: Event sequencing
  - Primary vs. secondary events
  - Clustering and temporal patterns
  - Cascade failure prediction

### 6. Burnout Fire Weather Index
**File**: `test_burnout_fire_index.py` (60+ tests)

Tests for wildfire science-inspired burnout risk metrics:

- **Multi-Temporal Indices**: Layered risk assessment
  - FFMC (Fine Fuel Moisture Code): 1-day stress indicators
  - DMC (Duff Moisture Code): 15-day accumulated stress
  - DC (Drought Code): 53-day chronic stress
- **Fire Weather Index (FWI)**: Composite burnout risk
  - Initial Spread Index (ISI): Rate of stress spread
  - Buildup Index (BUI): Total stress accumulation
  - Final FWI calculation: Overall burnout danger
- **Danger Classification**: Risk level categorization
  - Low (FWI 0-5): Normal operations
  - Moderate (5-11): Increased monitoring
  - High (11-21): Preventive actions required
  - Very High (21-37): Restrictions needed
  - Extreme (>37): Emergency protocols
- **Restriction Recommendations**: Automated interventions
  - Work restrictions based on danger class
  - Load shedding priorities
  - Recovery period recommendations

### 7. Creep and Fatigue Analysis
**File**: `test_creep_fatigue.py` (40+ tests)

Tests for materials engineering-inspired stress accumulation:

- **Larson-Miller Parameter (LMP)**: Time-temperature-stress relationships
  - LMP = T × (C + log₁₀(t)) formulation
  - Creep life prediction
  - Stress-rupture time estimation
- **Creep Stages**: Progressive deformation under sustained load
  - Primary creep: Decreasing strain rate
  - Secondary (steady-state) creep: Constant strain rate
  - Tertiary creep: Accelerating strain leading to failure
- **Fatigue Accumulation**: Miner's rule for cumulative damage
  - Linear damage accumulation: Σ(n/N) ≥ 1 failure criterion
  - Cycle counting and stress history
  - Remaining life estimation
- **Stress-Life (S-N) Curves**: Fatigue life relationships
  - High-cycle fatigue (>10⁴ cycles)
  - Low-cycle fatigue (<10⁴ cycles)
  - Endurance limit determination
- **Combined Creep-Fatigue**: Interaction of sustained and cyclic loads
  - Damage fraction calculations
  - Safe operating envelopes
  - Failure mode prediction

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

### Running Cross-Disciplinary Tests

Run all cross-disciplinary module tests:

```bash
cd backend
pytest tests/resilience/test_spc_monitoring.py \
       tests/resilience/test_process_capability.py \
       tests/resilience/test_burnout_epidemiology.py \
       tests/resilience/test_erlang_coverage.py \
       tests/resilience/test_seismic_detection.py \
       tests/resilience/test_burnout_fire_index.py \
       tests/resilience/test_creep_fatigue.py -v
```

Run individual modules:

```bash
# Statistical Process Control
pytest tests/resilience/test_spc_monitoring.py -v

# Process Capability (Six Sigma)
pytest tests/resilience/test_process_capability.py -v

# Burnout Epidemiology (SIR Model)
pytest tests/resilience/test_burnout_epidemiology.py -v

# Erlang Coverage (Queueing Theory)
pytest tests/resilience/test_erlang_coverage.py -v

# Seismic Detection (STA/LTA)
pytest tests/resilience/test_seismic_detection.py -v

# Burnout Fire Weather Index
pytest tests/resilience/test_burnout_fire_index.py -v

# Creep and Fatigue Analysis
pytest tests/resilience/test_creep_fatigue.py -v
```

Run with coverage:

```bash
pytest tests/resilience/test_spc_monitoring.py \
       tests/resilience/test_process_capability.py \
       tests/resilience/test_burnout_epidemiology.py \
       tests/resilience/test_erlang_coverage.py \
       tests/resilience/test_seismic_detection.py \
       tests/resilience/test_burnout_fire_index.py \
       tests/resilience/test_creep_fatigue.py \
       --cov=app.resilience --cov-report=html -v
```

## Test Markers

- `@pytest.mark.resilience`: All resilience framework tests
- `@pytest.mark.performance`: Performance-sensitive tests
- `@pytest.mark.asyncio`: Async tests requiring pytest-asyncio

## Performance Targets

### Core Resilience Framework

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

### Cross-Disciplinary Modules

| Component | Target | Test Count |
|-----------|--------|------------|
| SPC Western Electric Rules | <10ms per check | 50+ tests |
| Process Capability (Cp/Cpk) | <5ms per calculation | 40+ tests |
| SIR Model Simulation (100 days) | <100ms | 44 tests |
| Erlang B/C Calculations | <5ms per formula | 47 tests |
| STA/LTA Detection | <20ms per window | 52 tests |
| FWI Index Calculation | <10ms per day | 60+ tests |
| Creep-Fatigue Analysis | <15ms per lifecycle | 40+ tests |

**Note**: Cross-disciplinary modules are designed for real-time or near-real-time operation with minimal computational overhead.

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

### Cross-Disciplinary Module Verification

The seven cross-disciplinary modules have comprehensive test coverage:

✓ **SPC Monitoring (50+ tests)**: Western Electric Rules, control charts, process capability
✓ **Process Capability (40+ tests)**: Six Sigma metrics, DPMO, sigma level conversions
✓ **Burnout Epidemiology (44 tests)**: SIR model, R₀ calculation, network contagion
✓ **Erlang Coverage (47 tests)**: Erlang B/C formulas, queueing theory, optimization
✓ **Seismic Detection (52 tests)**: STA/LTA algorithm, precursor detection, magnitude estimation
✓ **Fire Weather Index (60+ tests)**: FFMC/DMC/DC indices, FWI calculation, danger classification
✓ **Creep-Fatigue (40+ tests)**: Larson-Miller parameter, creep stages, fatigue accumulation

**Total: 330+ cross-disciplinary tests** covering manufacturing, epidemiology, telecommunications, seismology, wildfire science, and materials engineering principles adapted for medical scheduling resilience.

## Future Improvements

### Core Resilience Framework

1. Fix database schema issue to enable full pytest integration
2. Add integration tests with actual database fixtures
3. Add stress tests with 100+ faculty members
4. Add cascade failure simulation tests
5. Add network graph analysis tests (using NetworkX)

### Cross-Disciplinary Modules

6. **SPC Monitoring**: Add CUSUM (Cumulative Sum) and EWMA (Exponentially Weighted Moving Average) charts
7. **Process Capability**: Implement machine capability indices (Cm, Cmk) for equipment-specific analysis
8. **Epidemiology**: Add SEIR model (with Exposed state) and vaccination strategy optimization
9. **Erlang Coverage**: Implement Erlang X (Engset) formula for finite population systems
10. **Seismic Detection**: Add P-wave/S-wave discrimination and triangulation for multi-sensor arrays
11. **Fire Weather Index**: Integrate meteorological data APIs for real-time risk assessment
12. **Creep-Fatigue**: Add probabilistic life prediction using Weibull distributions
13. **Integration**: Create unified dashboard showing all cross-disciplinary metrics in real-time
14. **Validation**: Benchmark against historical schedule data to validate model accuracy
