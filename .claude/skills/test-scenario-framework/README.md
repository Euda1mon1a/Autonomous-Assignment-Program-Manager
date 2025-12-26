# TEST_SCENARIO_FRAMEWORK Skill

Comprehensive framework for defining, executing, and validating test scenarios for medical residency scheduling.

## Quick Start

```bash
# Activate the skill
Use the Skill tool with: test-scenario-framework

# Run a single scenario
pytest -m scenario -k "n1-simple-unavailable-001"

# Run all N-1 scenarios
pytest -m scenario -k "n1-"

# Run full regression suite
pytest -m scenario
```

## What's Included

### Main Skill File
- **SKILL.md** (471 lines) - Complete skill definition, phases, and integration points

### Workflows (3 comprehensive guides)
- **scenario-definition.md** (720 lines) - How to write scenario specifications
- **scenario-execution.md** (875 lines) - End-to-end execution pipeline
- **scenario-validation.md** (848 lines) - Result validation and comparison

### Reference Library (2 comprehensive references)
- **scenario-library.md** (984 lines) - 31 pre-built test scenarios
- **success-criteria.md** (775 lines) - Pass/fail criteria definitions

**Total:** 4,673 lines of comprehensive documentation

## Scenario Library Overview

### 31 Pre-Built Scenarios

1. **N-1 Failure Scenarios (10)**
   - Simple single resident unavailable
   - Holiday coverage failure
   - Multiple simultaneous absences
   - Backup chain cascade (3+ levels)
   - Weekend coverage gap
   - Night float replacement
   - TDY/deployment coverage
   - Post-call relief failure
   - Supervision ratio violation risk
   - Cascade failure prevention

2. **Swap Operation Scenarios (5)**
   - Simple one-to-one swap
   - Multi-swap chain (3-way)
   - Swap rejected (ACGME violation)
   - Absorb shift (give away)
   - Auto-match swap candidate

3. **ACGME Edge Case Scenarios (7)**
   - Exact 80-hour boundary
   - 1-in-7 strict boundary
   - Post-call 8-hour minimum
   - Duty period 24-hour limit
   - Night float 6-night maximum
   - Supervision ratio PGY-1 (2:1)
   - 4-week rolling average

4. **Holiday & Vacation Conflict Scenarios (4)**
   - Christmas coverage overlap
   - Thanksgiving week shortage
   - New Year's vacation conflict
   - Last-minute leave cancellation

5. **Moonlighting Scenarios (3)**
   - External moonlighting hours
   - Internal moonlighting
   - Moonlighting schedule conflict

6. **Integration Scenarios (2)**
   - Full month schedule generation
   - Concurrent multi-swap with N-1 failure

## Key Features

### Comprehensive Coverage
- ✅ All ACGME rules tested (80-hour, 1-in-7, duty limits, supervision, etc.)
- ✅ All scheduling operations (assignments, swaps, N-1, generation)
- ✅ Edge cases and boundary conditions
- ✅ Holiday/vacation conflicts
- ✅ Moonlighting integration
- ✅ Concurrent operations and race conditions

### Structured Testing Phases
1. **Scenario Selection** - Choose from library or define custom
2. **Scenario Definition** - Structured YAML specification
3. **Scenario Execution** - Automated execution with timeout protection
4. **Result Validation** - Compare against expected outcomes
5. **Reporting** - Comprehensive test reports

### Validation Strategies
- **Strict Comparison** - Exact match required
- **Lenient Comparison** - Tolerance-based matching
- **Custom Validators** - User-defined validation functions
- **Partial Match** - Allow extra/missing items with rules
- **State Comparison** - Pre/post execution delta analysis

### Success Criteria
- **Coverage Criteria** - Completeness, gap duration, backup depth
- **ACGME Compliance** - 100% compliance required for all rules
- **Performance Criteria** - Execution time, query count, memory
- **Quality Metrics** - Workload balance, utilization, stability
- **Operational Criteria** - Notification delivery, audit trails
- **Data Integrity** - No double-booking, orphaned assignments, consistency

## File Organization

```
test-scenario-framework/
├── SKILL.md                           # Main skill definition
├── README.md                          # This file
├── Workflows/
│   ├── scenario-definition.md         # How to write scenarios
│   ├── scenario-execution.md          # Execution pipeline
│   └── scenario-validation.md         # Validation strategies
└── Reference/
    ├── scenario-library.md            # 31 pre-built scenarios
    └── success-criteria.md            # Pass/fail criteria
```

## Integration with Other Skills

### With acgme-compliance
- Automatic ACGME validation during scenario execution
- Pre/post compliance verification
- Continuous monitoring

### With safe-schedule-generation
- Database backup before destructive scenarios
- Transaction-based execution
- Rollback on validation failure

### With systematic-debugger
- Full execution trace capture on failure
- Hypothesis generation from failures
- Minimal reproduction scenario creation

### With test-writer
- Convert scenarios to automated pytest tests
- Generate regression test suite
- CI/CD integration

## Usage Examples

### Run Single Scenario
```bash
pytest -m scenario -k "n1-simple-unavailable-001" -v
```

### Run Category
```bash
pytest -m scenario -k "swap-"    # All swap scenarios
pytest -m scenario -k "acgme-"   # All ACGME edge cases
pytest -m scenario -k "holiday-" # All holiday scenarios
```

### Generate Report
```bash
pytest -m scenario --html=scenario-report.html --self-contained-html
```

### Parallel Execution
```bash
pytest -m scenario -n auto  # Run scenarios in parallel
```

## Scenario Development

### Create New Scenario

1. Copy template from `scenario-definition.md`
2. Define setup (persons, rotations, assignments)
3. Define test case (operations to execute)
4. Define expected outcome (assertions, state checks)
5. Save as `backend/tests/scenarios/{category}/{name}.yaml`
6. Create pytest test wrapper
7. Run and verify

### Scenario Naming Convention
```
Format: {category}_{operation}_{edge_case}_{number}

Examples:
- n1-simple-unavailable-001
- swap-multi-chain-002
- acgme-80hour-exact-003
- holiday-christmas-overlap-001
```

## Testing Standards

### Pass Criteria
- ✅ 100% ACGME compliance
- ✅ Coverage completeness ≥ 95%
- ✅ Zero data integrity violations
- ✅ All critical assertions passed

### Failure Triggers
- ❌ Any ACGME violation
- ❌ Double booking detected
- ❌ Data corruption
- ❌ Timeout exceeded
- ❌ Critical assertion failed

### Performance Targets
- Simple scenarios: < 5s
- Complex scenarios: < 30s
- Integration scenarios: < 60s

## Scenario Matrix

| Category | Total | Critical | High | Medium |
|----------|-------|----------|------|--------|
| N-1 Failures | 10 | 6 | 3 | 1 |
| Swap Operations | 5 | 1 | 2 | 2 |
| ACGME Edge Cases | 7 | 7 | 0 | 0 |
| Holiday/Vacation | 4 | 2 | 2 | 0 |
| Moonlighting | 3 | 1 | 2 | 0 |
| Integration | 2 | 2 | 0 | 0 |
| **TOTAL** | **31** | **19** | **9** | **3** |

## Next Steps

1. **Review scenario library** - Familiarize yourself with pre-built scenarios
2. **Run example scenarios** - Test execution pipeline
3. **Create custom scenarios** - Define scenarios for your use cases
4. **Integrate with CI/CD** - Add to automated testing pipeline
5. **Extend library** - Contribute new scenarios for edge cases

## References

- See `Workflows/scenario-definition.md` for complete scenario specification guide
- See `Workflows/scenario-execution.md` for execution pipeline details
- See `Workflows/scenario-validation.md` for validation strategies
- See `Reference/scenario-library.md` for all 31 pre-built scenarios
- See `Reference/success-criteria.md` for comprehensive pass/fail criteria

## Support

For questions or issues:
1. Check workflow documentation in `Workflows/`
2. Review example scenarios in `Reference/scenario-library.md`
3. Consult success criteria in `Reference/success-criteria.md`
4. Use systematic-debugger skill for complex failures
