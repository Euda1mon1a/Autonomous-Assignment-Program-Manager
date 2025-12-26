# Resilience Scenario Tests

## Overview

This test suite implements integration tests for the resilience framework based on the test frames defined in `docs/testing/TEST_SCENARIO_FRAMES.md` Section 4.

## Test Coverage

### 1. N-1 Single Point of Failure (`test_n1_single_point_of_failure`)

**Based on:** Frame 4.1 - N-1 Analysis with Single Point of Failure

**Scenario:**
- Only 1 faculty member has PALS (Pediatric Advanced Life Support) certification
- 4 pediatric clinic shifts require PALS
- Loss of this faculty member would leave all peds clinics uncovered

**What it tests:**
- N-1 contingency analysis correctly identifies critical dependencies
- Single points of failure are flagged with "critical" severity
- Unique provider status is detected
- Mitigation recommendations include cross-training or backup

**Expected Results:**
- ✓ Vulnerability detected with `severity="critical"`
- ✓ `is_unique_provider=True`
- ✓ Affected blocks count matches PALS-required shifts
- ✓ Recommendations include "cross-train" or "backup"

---

### 2. N-2 Cascading Failure (`test_n2_cascading_failure`)

**Based on:** Frame 4.2 - N-2 Cascading Failure Simulation

**Scenario:**
- 8 faculty members working at 87.5% utilization (70 hours/week each)
- Simulate loss of 2 faculty members (25% capacity loss)
- Remaining 6 faculty must absorb workload → 116.7% utilization
- This exceeds the 80% safe threshold, potentially triggering cascade

**What it tests:**
- N-2 analysis identifies fatal pairs whose joint loss causes system failure
- Cascade simulation models workload redistribution
- Phase transition risk is detected when system approaches critical thresholds
- Mitigation strategies are recommended

**Expected Results:**
- ✓ Fatal pairs detected in high-utilization scenarios
- ✓ Cascade simulation shows reduced final coverage
- ✓ Phase transition risk elevated to "medium", "high", or "critical"
- ✓ Mitigation recommendations provided

---

### 3. Utilization Threshold Transitions (`test_utilization_threshold_transitions`)

**Based on:** Frame 4.3 - Utilization Threshold Transitions

**Scenario:**
- Incrementally increase faculty workload from 75% → 80% → 85% → 90% → 95%
- Monitor defense level transitions at each threshold
- Verify boundary conditions (79.9% vs 80.1%)

**What it tests:**
- Utilization calculations are accurate
- Defense levels transition at correct thresholds:
  - < 80%: GREEN (healthy)
  - 80-85%: YELLOW (warning)
  - 85-90%: ORANGE (above threshold)
  - 90-95%: RED (critical)
  - > 95%: BLACK (emergency)
- 80% threshold is the critical transition point

**Expected Results:**
- ✓ Utilization percentages match expected values (±2%)
- ✓ Defense levels escalate at correct thresholds
- ✓ 80% boundary triggers YELLOW or higher
- ✓ Transitions are monotonic (no level skipping)

---

### 4. Defense Level Escalation (`test_defense_level_escalation`)

**Based on:** Frame 4.4 - Defense Level Escalation and De-escalation

**Scenario:**
- Test escalation: Coverage drops from 98% → 92% → 85% → 75% → 65%
- Test de-escalation: Coverage recovers from 75% → 85% → 92% → 98%
- Verify actions activate correctly at each level

**What it tests:**
- Defense-in-depth framework recommends correct levels based on coverage
- Escalation sequence: PREVENTION → CONTROL → SAFETY_SYSTEMS → CONTAINMENT → EMERGENCY
- De-escalation reverses smoothly as conditions improve
- Action activation tracking works (activation count, timestamps)

**Expected Results:**
- ✓ Defense levels match coverage thresholds
- ✓ Escalation is monotonic (levels increase)
- ✓ De-escalation is monotonic (levels decrease)
- ✓ Action activation increments counters and sets timestamps
- ✓ Status report includes all 5 defense levels

---

## Additional Tests

### 5. Boundary Conditions (`test_utilization_exactly_at_threshold`)

Tests exact threshold behavior (80.0% utilization).

### 6. N+2 Redundancy Rule (`test_redundancy_check_n_plus_2_rule`)

Tests nuclear engineering N+2 rule (system survives loss of 2 components).

### 7. Stable Cascade Simulation (`test_cascade_simulation_with_no_failures`)

Tests that low-utilization scenarios don't trigger false cascades.

### 8. Comprehensive Report (`test_comprehensive_vulnerability_report`)

Tests full vulnerability report generation combining N-1, N-2, and phase transition analysis.

---

## Running the Tests

### Prerequisites

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run All Resilience Scenario Tests

```bash
pytest tests/integration/test_resilience_scenarios.py -v
```

### Run Specific Test

```bash
pytest tests/integration/test_resilience_scenarios.py::test_n1_single_point_of_failure -v
```

### Run with Coverage

```bash
pytest tests/integration/test_resilience_scenarios.py --cov=app.resilience --cov-report=html
```

### Run Only Resilience Integration Tests

```bash
pytest -m "resilience and integration" -v
```

---

## Test Data and Fixtures

### Faculty Fixtures

- `pals_certified_faculty`: Single faculty with PALS certification (single point of failure)
- `faculty_without_pals`: 5 faculty members without PALS
- `balanced_faculty_pool`: 8 faculty for balanced schedule scenarios

### Block Fixtures

- `peds_clinic_blocks`: 4 blocks requiring PALS certification
- `balanced_blocks`: 14 blocks (1 week, AM/PM)

### Assignment Fixtures

- `balanced_assignments`: 8 faculty covering 14 blocks at 87.5% utilization

### Component Fixtures

- `utilization_monitor`: UtilizationMonitor with 80% threshold
- `contingency_analyzer`: ContingencyAnalyzer for N-1/N-2 analysis
- `defense_in_depth`: DefenseInDepth manager

---

## Relationship to Resilience Framework

These tests exercise the following resilience components:

### From `app.resilience.contingency`:
- `ContingencyAnalyzer.analyze_n1()` - Single point of failure detection
- `ContingencyAnalyzer.analyze_n2()` - Fatal pair detection
- `ContingencyAnalyzer.simulate_cascade_failure()` - Cascade modeling
- `ContingencyAnalyzer.generate_report()` - Comprehensive vulnerability reports

### From `app.resilience.defense_in_depth`:
- `DefenseInDepth.get_recommended_level()` - Defense level selection
- `DefenseInDepth.activate_action()` - Action activation
- `DefenseInDepth.check_redundancy()` - N+2 redundancy verification
- `DefenseInDepth.get_status_report()` - Status reporting

### From `app.resilience.utilization`:
- `UtilizationMonitor.calculate_utilization()` - Utilization calculation
- Utilization threshold detection (GREEN/YELLOW/ORANGE/RED/BLACK)

---

## Cross-References

- **Test Frames**: `docs/testing/TEST_SCENARIO_FRAMES.md` Section 4
- **Resilience Architecture**: `docs/architecture/cross-disciplinary-resilience.md`
- **Contingency Analysis**: `backend/app/resilience/contingency.py`
- **Defense in Depth**: `backend/app/resilience/defense_in_depth.py`
- **Load Testing**: `backend/tests/resilience/test_resilience_load.py`

---

## Expected Test Duration

- Individual tests: < 1 second each
- Full suite: < 10 seconds
- Tests use in-memory SQLite, no external dependencies

---

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`, ensure you're in the backend directory and have activated the virtual environment:

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Database Errors

Tests use in-memory SQLite and create fresh databases for each test. If you see database errors, verify:
- SQLAlchemy models are imported correctly
- `conftest.py` is in the tests directory
- Base.metadata is configured

### NetworkX Warnings

Some centrality calculations use NetworkX. If not installed:

```bash
pip install networkx
```

Tests will fall back to basic centrality if NetworkX is unavailable.

---

## Future Enhancements

Potential additions to test coverage:

1. **N-3 Analysis**: Test system response to loss of 3+ faculty
2. **Temporal Cascades**: Test failures that spread over time
3. **Multi-Zone Failures**: Test blast radius isolation across zones
4. **Recovery Simulation**: Test system recovery after adding staff
5. **Real-Time Monitoring**: Test continuous monitoring and alerting

---

**Last Updated:** 2025-12-26
**Maintained by:** Development Team
**Review Cycle:** After resilience framework changes
