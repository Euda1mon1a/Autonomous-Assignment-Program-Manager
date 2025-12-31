# Scheduler Test Coverage Gaps - Cheatsheet
**Quick reference for test writing priorities**

## By The Numbers

| Metric | Value | Status |
|--------|-------|--------|
| Total constraints | 46 | Analyzed ✓ |
| **Untested constraints** | **31 (67%)** | **CRITICAL GAP** |
| Constraint tests today | 180 | Low |
| Constraint tests needed | 350+ | High priority |
| Parametrized solver tests | 4 | Near zero |
| Infeasibility tests | 0 | Missing entirely |
| Objective function tests | 0 | Missing entirely |

---

## The 5 Critical Gaps

### GAP 1: ACGME Constraints Untested
```
Missing: AvailabilityConstraint, EightyHourRule, OneInSeven, Supervision
Action: Create tests/constraints/test_acgme_constraints.py
Tests needed: 25-30
Effort: 2-3 weeks
Impact: CRITICAL - Core regulatory compliance
```

### GAP 2: No Solver Algorithm Comparison
```
Current: Algorithms tested in isolation
Problem: Quality differences unknown
Action: Create tests/scheduling/test_solver_comparison.py
Pattern:
  @pytest.mark.parametrize("solver_type", ["greedy", "cp_sat", "pulp", "hybrid"])
  def test_all_solvers_handle_scenario(solver_type):
      pass
Tests needed: 15-20
Effort: 1 week
Impact: CRITICAL - Algorithm selection validation
```

### GAP 3: Infeasibility Handling Not Tested
```
Missing: Impossible scenario detection and recovery
Tests needed: 20-25
Effort: 2-3 weeks
Impact: CRITICAL - Production system resilience
Scenarios:
  - All residents on leave
  - Insufficient faculty for supervision
  - Conflicting hard constraints
  - Resource exhaustion
```

### GAP 4: Optimization Objectives Untested
```
Missing: Objective value correctness, penalty calculation
Tests needed: 12-15
Effort: 1-2 weeks
Impact: HIGH - Solution quality validation
```

### GAP 5: Limited Edge Cases
```
Current: 13 edge case tests
Missing: 30+ additional edge cases
Tests needed: 15-20
Effort: 1-2 weeks
Impact: MEDIUM - System robustness
```

---

## Constraint Test Writing Priority Matrix

### Priority 1 - MUST HAVE (Regulatory/Critical)

**Availability & Work Hours**
- [ ] AvailabilityConstraint (residents only work when available)
- [ ] EightyHourRuleConstraint (max 80 hrs/week, 4-week average)
- [ ] OneInSevenRuleConstraint (one 24-hour period off per 7 days)
- [ ] SupervisionRatioConstraint (PGY-1: 1:2, PGY-2/3: 1:4)

**Files to create:**
```
tests/constraints/test_acgme_constraints.py  (25-30 tests)
```

**Effort:** 2-3 weeks

---

### Priority 2 - HIGH VALUE (Block/Call Management)

**FMIT Constraints**
- [ ] FMITWeekBlockingConstraint
- [ ] FMITMandatoryCallConstraint
- [ ] FMITStaffingFloorConstraint
- [ ] FMITContinuityTurfConstraint

**Call Equity (Soft)**
- [ ] SundayCallEquityConstraint
- [ ] WeekdayCallEquityConstraint
- [ ] CallSpacingConstraint
- [ ] TuesdayCallPreferenceConstraint

**Files to expand:**
```
tests/constraints/test_fmit_constraints.py           (12-15 tests)
tests/constraints/test_call_equity_soft_constraints.py (10-12 tests)
```

**Effort:** 1-2 weeks each

---

### Priority 3 - MEDIUM VALUE (Faculty & Resilience)

**Faculty Management**
- [ ] FacultyDayAvailabilityConstraint
- [ ] FacultyPrimaryDutyClinicConstraint
- [ ] FacultyRoleClinicConstraint
- [ ] SMFacultyClinicConstraint

**Resilience**
- [ ] HubProtectionConstraint
- [ ] N1VulnerabilityConstraint
- [ ] UtilizationBufferConstraint
- [ ] ZoneBoundaryConstraint

**Files to create:**
```
tests/constraints/test_faculty_constraints.py     (10-12 tests)
tests/constraints/test_resilience_constraints.py  (12-15 tests)
```

**Effort:** 1-2 weeks each

---

## Solver Testing Priority Matrix

### Priority 1 - CRITICAL

**Parametrized Solver Comparison**
```python
# File: tests/scheduling/test_solver_comparison.py

@pytest.mark.parametrize("solver_type", ["greedy", "cp_sat", "pulp", "hybrid"])
class TestSolverAlgorithms:
    def test_solver_finds_feasible_solution(self, solver_type):
        """Every solver should find feasible solution if one exists."""

    def test_solver_respects_hard_constraints(self, solver_type):
        """All solvers must satisfy hard constraints."""

    def test_solver_timeout_respected(self, solver_type):
        """Solver should respect time limit."""

    def test_solver_determinism(self, solver_type):
        """Given same seed, solver is deterministic."""
```

**Tests needed:** 15-20
**Effort:** 1 week

---

### Priority 2 - HIGH VALUE

**Solver Quality Metrics**
```python
# File: tests/scheduling/test_solver_quality.py

class TestObjectiveValue:
    def test_objective_is_deterministic(self):
        """Same solution always has same objective."""

    def test_objective_reflects_violations(self):
        """Each violation increases objective."""

    def test_objective_improves_with_iterations(self):
        """Solution quality improves over time."""

class TestAlgorithmSelection:
    def test_select_greedy_for_simple_problems(self):
        """Small problems use fast greedy."""

    def test_select_cp_sat_for_complex_problems(self):
        """Large problems use optimal CP-SAT."""
```

**Tests needed:** 12-15
**Effort:** 1-2 weeks

---

## Infeasibility Testing Priority

### Must Have

```python
# File: tests/scheduling/test_infeasibility_detection.py

class TestInfeasibilityDetection:
    def test_detect_all_residents_unavailable(self):
        """All residents on leave -> infeasible."""

    def test_detect_insufficient_faculty(self):
        """Can't meet supervision ratios -> infeasible."""

    def test_detect_conflicting_hard_constraints(self):
        """Conflicting requirements -> infeasible."""

    def test_infeasibility_message_helpful(self):
        """Error explains why infeasible."""

class TestGracefulDegradation:
    def test_relax_soft_constraints_first(self):
        """Soft relaxed before hard."""

    def test_relaxation_priority_order(self):
        """Higher priority soft relaxed last."""

    def test_minimum_hard_violations(self):
        """If must violate hard, minimize violations."""
```

**Tests needed:** 20-25
**Effort:** 2-3 weeks

---

## Edge Case Testing Checklist

### Must Have

- [ ] Single day schedule (minimal)
- [ ] Full year schedule (maximum)
- [ ] Leap year handling
- [ ] Daylight saving time transitions
- [ ] Single faculty coverage (resource exhaustion)
- [ ] Single resident schedule
- [ ] Single rotation template
- [ ] More residents than blocks
- [ ] More blocks than residents
- [ ] Exact capacity match
- [ ] Holiday handling
- [ ] Weekend boundaries
- [ ] Timezone boundaries
- [ ] Block boundaries
- [ ] Rotation capacity limits

**File:** `tests/scheduling/test_generation_edge_cases.py` (expand from 13 to 30+ tests)
**Effort:** 1-2 weeks

---

## Implementation Roadmap

### Week 1-2: Foundation (P1 Part 1)
```
[ ] Create test_solver_comparison.py (parametrized algorithms)
[ ] Create test_acgme_constraints.py (start with availability, 80-hour)
```

### Week 2-4: Compliance (P1 Part 2)
```
[ ] Complete test_acgme_constraints.py (all 4 ACGME rules)
[ ] Create test_infeasibility_detection.py (detection logic)
```

### Week 4-6: Recovery (P1 Part 3)
```
[ ] Complete test_infeasibility_detection.py (recovery logic)
[ ] Create test_solver_quality.py (objective validation)
```

### Week 6-8: Blocks (P2 Part 1)
```
[ ] Expand test_fmit_constraints.py
[ ] Create test_call_equity_soft_constraints.py
```

### Week 8-10: Faculty (P3 Part 1)
```
[ ] Create test_faculty_constraints.py
[ ] Expand test_generation_edge_cases.py
```

### Week 10-12: Resilience (P3 Part 2)
```
[ ] Create test_resilience_constraints.py
[ ] Complete edge case expansion
```

### Week 12+: Advanced
```
[ ] Property-based testing with hypothesis
[ ] Bio-inspired solver tests
[ ] Mutation testing for quality validation
```

---

## Quick Copy-Paste Test Templates

### Constraint Test Template
```python
class TestNewConstraint:
    @pytest.fixture
    def constraint(self):
        return NewConstraint(name="test", priority=ConstraintPriority.HIGH)

    def test_validate_passes_valid(self, constraint, valid_assignment):
        result = constraint.validate(valid_assignment)
        assert result.satisfied

    def test_validate_fails_invalid(self, constraint, invalid_assignment):
        result = constraint.validate(invalid_assignment)
        assert not result.satisfied

    def test_add_to_cpsat(self, constraint, cpsat_model, variables):
        constraint.add_to_cpsat(cpsat_model, variables)
        assert len(cpsat_model.constraints) > 0

    def test_add_to_pulp(self, constraint, pulp_model, variables):
        constraint.add_to_pulp(pulp_model, variables)
        assert len(pulp_model.constraints) > 0
```

### Parametrized Solver Template
```python
@pytest.mark.parametrize("solver_type", ["greedy", "cp_sat", "pulp", "hybrid"])
def test_solver_feasibility(solver_type, scheduling_context):
    solver = SolverFactory.create(solver_type)
    result = solver.solve(scheduling_context)

    assert result.success
    assert len(result.assignments) > 0

    # Verify no hard constraint violations
    violations = ACGMEValidator().validate(result.assignments)
    assert len(violations) == 0
```

### Infeasibility Template
```python
def test_infeasibility_all_residents_unavailable(db):
    # Make all residents unavailable
    for resident in get_all_residents(db):
        create_absence(db, resident, full_date_range)

    # Try to schedule
    result = engine.generate_schedule(context)

    # Should detect infeasibility
    assert result.status == "infeasible"
    assert result.infeasibility_explanation is not None
```

---

## Effort Summary

| Category | Tests | Weeks | When |
|----------|-------|-------|------|
| ACGME Constraints | 25-30 | 2-3 | Week 1-4 |
| Solver Comparison | 15-20 | 1 | Week 1-2 |
| Infeasibility | 20-25 | 2-3 | Week 2-5 |
| FMIT Constraints | 12-15 | 1-2 | Week 5-7 |
| Call Equity | 10-12 | 1-2 | Week 5-7 |
| Solver Quality | 12-15 | 1-2 | Week 4-6 |
| Faculty | 10-12 | 1-2 | Week 8-10 |
| Edge Cases | 15-20 | 1-2 | Week 8-10 |
| Resilience | 12-15 | 1-2 | Week 10-12 |
| **TOTAL** | **139-174** | **12-18** | **Staged rollout** |

---

## Success Metrics

**Before (Today):**
- Untested constraints: 31
- Parametrized solver tests: 4
- Infeasibility tests: 0
- Total constraint tests: 180

**After (Post-Implementation):**
- Untested constraints: 0
- Parametrized solver tests: 50+
- Infeasibility tests: 50+
- Total constraint tests: 350-400

**Coverage Improvement:**
- Constraint coverage: 33% → 100%
- Algorithm validation: Isolated → Parametrized comparison
- Robustness testing: 13 → 50+ edge cases

---

Generated: 2025-12-30
Full analysis: test-scheduler-coverage-analysis.md
