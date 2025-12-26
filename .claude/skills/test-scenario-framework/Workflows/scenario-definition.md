***REMOVED*** Scenario Definition Workflow

Complete guide to writing test scenario specifications for medical residency scheduling.

***REMOVED******REMOVED*** Scenario Structure

***REMOVED******REMOVED******REMOVED*** Complete Scenario Template

```yaml
scenario:
  ***REMOVED*** === Metadata ===
  name: "Descriptive scenario name"
  id: "category-operation-case-***REMOVED******REMOVED******REMOVED***"
  version: "1.0.0"
  author: "author-name"
  created: "2024-01-15"
  updated: "2024-01-20"

  ***REMOVED*** === Classification ===
  category: "n1_failure | swap | acgme_edge | integration | performance"
  priority: "critical | high | medium | low"
  tags: ["n1", "holiday", "acgme", "stress"]

  ***REMOVED*** === Documentation ===
  description: |
    Detailed description of what this scenario tests.
    Include context about why this edge case matters.

  rationale: |
    Why this scenario is important.
    What bugs or issues it prevents.

  related_bugs: ["***REMOVED***123", "***REMOVED***456"]
  related_scenarios: ["n1-001", "swap-005"]

  ***REMOVED*** === Configuration ===
  timeout_seconds: 300
  retry_on_failure: false
  capture_artifacts: true
  require_backup: true  ***REMOVED*** For destructive operations

  ***REMOVED*** === Setup Phase ===
  setup:
    ***REMOVED*** Database state
    database:
      clean_state: true  ***REMOVED*** Start with empty DB
      load_fixtures:
        - "base_persons.json"
        - "base_rotations.json"

    ***REMOVED*** Persons
    persons:
      - id: "resident-1"
        first_name: "Test"
        last_name: "Resident1"
        role: "RESIDENT"
        pgy_level: 2
        status: "active"
        max_hours_per_week: 80
        backup_for: []

      - id: "resident-2"
        first_name: "Test"
        last_name: "Resident2"
        role: "RESIDENT"
        pgy_level: 2
        status: "active"
        max_hours_per_week: 80
        backup_for: ["resident-1"]

      - id: "faculty-1"
        first_name: "Test"
        last_name: "Faculty1"
        role: "FACULTY"
        status: "active"
        can_supervise: true

    ***REMOVED*** Rotations
    rotations:
      - id: "inpatient-am"
        name: "Inpatient Morning"
        rotation_type: "inpatient"
        hours_per_block: 6
        min_persons: 1
        max_persons: 3
        requires_supervision: true

      - id: "clinic-am"
        name: "Clinic Morning"
        rotation_type: "clinic"
        hours_per_block: 4
        min_persons: 1
        max_persons: 2

    ***REMOVED*** Initial assignments
    assignments:
      - person_id: "resident-1"
        block_date: "2024-12-25"
        block_period: "AM"
        rotation_id: "inpatient-am"
        hours: 6

      - person_id: "resident-2"
        block_date: "2024-12-25"
        block_period: "AM"
        rotation_id: "clinic-am"
        hours: 4

      - person_id: "faculty-1"
        block_date: "2024-12-25"
        block_period: "AM"
        rotation_id: "inpatient-am"
        hours: 6

    ***REMOVED*** Constraints
    constraints:
      acgme_enabled: true
      n1_contingency_enabled: true
      auto_coverage: true

    ***REMOVED*** Preconditions (verified before test)
    preconditions:
      - check: "all_persons_exist"
        expected: true
      - check: "coverage_complete"
        expected: true
      - check: "acgme_compliant"
        expected: true

  ***REMOVED*** === Test Case Phase ===
  test_case:
    ***REMOVED*** Primary operation
    operation: "simulate_unavailability"

    ***REMOVED*** Operation parameters
    parameters:
      person_id: "resident-1"
      start_date: "2024-12-25"
      end_date: "2024-12-27"
      reason: "illness"
      trigger_contingency: true

    ***REMOVED*** Sequential operations (if multi-step)
    operations:
      - step: 1
        operation: "mark_unavailable"
        parameters:
          person_id: "resident-1"
          dates: ["2024-12-25", "2024-12-26"]

      - step: 2
        operation: "run_contingency_analysis"
        parameters:
          trigger: "n1_failure"

      - step: 3
        operation: "activate_backup_assignments"
        parameters:
          auto_assign: true

    ***REMOVED*** Concurrent operations (if testing race conditions)
    concurrent_operations:
      - operation: "request_swap"
        parameters:
          requestor_id: "resident-2"
          target_date: "2024-12-25"
      - operation: "mark_unavailable"
        parameters:
          person_id: "resident-3"
          dates: ["2024-12-25"]

  ***REMOVED*** === Expected Outcome Phase ===
  expected_outcome:
    ***REMOVED*** Overall success
    success: true

    ***REMOVED*** Specific assertions
    assertions:
      coverage_maintained:
        type: "boolean"
        expected: true
        critical: true

      acgme_compliant:
        type: "boolean"
        expected: true
        critical: true

      backup_activated:
        type: "boolean"
        expected: true
        critical: false

      assignments_modified:
        type: "numeric"
        expected: 3
        tolerance: 2  ***REMOVED*** Allow 1-5 assignments
        critical: false

      persons_affected:
        type: "numeric"
        expected: 2
        max: 5
        critical: false

      execution_time_seconds:
        type: "numeric"
        max: 10.0
        critical: false

    ***REMOVED*** State checks
    final_state:
      persons:
        - id: "resident-1"
          status: "unavailable"

        - id: "resident-2"
          status: "active"
          weekly_hours:
            min: 0
            max: 80

      assignments:
        - block_date: "2024-12-25"
          rotation_id: "inpatient-am"
          coverage_count:
            min: 1
            critical: true

      compliance:
        - rule: "80_hour_rule"
          status: "compliant"
          critical: true

        - rule: "one_in_seven"
          status: "compliant"
          critical: true

    ***REMOVED*** Expected errors (if testing failure scenarios)
    expected_errors:
      - type: "ACGMEViolation"
        count: 0
      - type: "CoverageGap"
        count: 0

    ***REMOVED*** Metrics
    performance_metrics:
      max_execution_time: 5.0
      max_db_queries: 50
      max_memory_mb: 256

  ***REMOVED*** === Validation Phase ===
  validation:
    ***REMOVED*** Comparison strategy
    comparison_strategy: "strict"  ***REMOVED*** strict | lenient | custom

    ***REMOVED*** Tolerance thresholds
    tolerances:
      numeric_percentage: 0.05  ***REMOVED*** 5% tolerance
      numeric_absolute: 2       ***REMOVED*** ±2 for counts
      timestamp_seconds: 1      ***REMOVED*** 1 second tolerance

    ***REMOVED*** Partial match rules
    partial_match:
      allow_extra_assignments: false
      allow_missing_assignments: false
      require_exact_order: false

    ***REMOVED*** Custom validators
    custom_validators:
      - name: "validate_backup_chain"
        function: "app.testing.validators.backup_chain_validator"

      - name: "validate_coverage_gaps"
        function: "app.testing.validators.coverage_gap_validator"

  ***REMOVED*** === Artifacts ===
  artifacts:
    capture:
      - "initial_database_state"
      - "final_database_state"
      - "execution_logs"
      - "sql_queries"
      - "performance_metrics"

    retention_days: 30

    export_formats:
      - "json"
      - "yaml"
      - "html_report"
```

***REMOVED******REMOVED*** Variable Parameterization

***REMOVED******REMOVED******REMOVED*** Using Variables

```yaml
scenario:
  name: "Parameterized N-1 Failure"

  ***REMOVED*** Define variables
  variables:
    unavailable_person: "resident-1"
    backup_person: "resident-2"
    test_date: "2024-12-25"
    max_hours: 80

  ***REMOVED*** Use variables with ${var} syntax
  test_case:
    operation: "mark_unavailable"
    parameters:
      person_id: "${unavailable_person}"
      date: "${test_date}"

  expected_outcome:
    assertions:
      backup_person_assigned:
        type: "assignment_exists"
        person_id: "${backup_person}"
        date: "${test_date}"
```

***REMOVED******REMOVED******REMOVED*** Scenario Templates with Parameter Injection

```python
***REMOVED*** Define template
template = load_scenario_template("n1_failure_template.yaml")

***REMOVED*** Generate scenarios with different parameters
scenarios = []
for resident_id in ["resident-1", "resident-2", "resident-3"]:
    for test_date in date_range("2024-12-01", "2024-12-31"):
        scenario = template.render(
            unavailable_person=resident_id,
            test_date=test_date
        )
        scenarios.append(scenario)
```

***REMOVED******REMOVED******REMOVED*** Dynamic Value Generation

```yaml
scenario:
  setup:
    persons:
      ***REMOVED*** Generate 10 residents dynamically
      - generator: "create_residents"
        count: 10
        template:
          role: "RESIDENT"
          pgy_level: "{{ loop.index % 3 + 1 }}"
          id: "resident-{{ loop.index }}"

      ***REMOVED*** Generate date range
      - generator: "create_date_range"
        start: "2024-12-01"
        end: "2024-12-31"
        variable_name: "test_dates"
```

***REMOVED******REMOVED*** Data Fixtures

***REMOVED******REMOVED******REMOVED*** Fixture Files

```json
// fixtures/base_persons.json
{
  "persons": [
    {
      "id": "resident-1",
      "first_name": "Test",
      "last_name": "Resident1",
      "role": "RESIDENT",
      "pgy_level": 1,
      "status": "active"
    }
    // ... more persons
  ]
}
```

***REMOVED******REMOVED******REMOVED*** Fixture Loading

```yaml
scenario:
  setup:
    database:
      load_fixtures:
        ***REMOVED*** Load base fixtures
        - "fixtures/base_persons.json"
        - "fixtures/base_rotations.json"

        ***REMOVED*** Load scenario-specific fixtures
        - "fixtures/scenarios/n1_holiday_setup.json"

        ***REMOVED*** Merge strategy
        merge_strategy: "deep_merge"  ***REMOVED*** or "replace", "append"
```

***REMOVED******REMOVED******REMOVED*** Fixture Factories

```python
***REMOVED*** Define fixture factory
class PersonFixtureFactory:
    @staticmethod
    def create_resident(
        id: str,
        pgy_level: int,
        max_hours: int = 80
    ) -> dict:
        return {
            "id": id,
            "role": "RESIDENT",
            "pgy_level": pgy_level,
            "max_hours_per_week": max_hours,
            "status": "active"
        }

***REMOVED*** Use in scenario
scenario:
  setup:
    persons:
      - "{{ PersonFixtureFactory.create_resident('resident-1', 1) }}"
      - "{{ PersonFixtureFactory.create_resident('resident-2', 2) }}"
```

***REMOVED******REMOVED*** Success Criteria Definition

***REMOVED******REMOVED******REMOVED*** Binary Criteria

```yaml
expected_outcome:
  assertions:
    coverage_maintained:
      type: "boolean"
      expected: true
      critical: true  ***REMOVED*** Scenario fails if this fails
      message: "Coverage must be maintained after N-1 failure"
```

***REMOVED******REMOVED******REMOVED*** Numeric Criteria with Ranges

```yaml
expected_outcome:
  assertions:
    assignments_modified:
      type: "numeric"
      min: 1          ***REMOVED*** At least 1 assignment
      max: 10         ***REMOVED*** No more than 10 assignments
      expected: 5     ***REMOVED*** Ideally 5 assignments
      tolerance: 2    ***REMOVED*** ±2 is acceptable (3-7 range)
      critical: false
```

***REMOVED******REMOVED******REMOVED*** String Matching Criteria

```yaml
expected_outcome:
  assertions:
    person_status:
      type: "string"
      expected: "unavailable"
      match_type: "exact"  ***REMOVED*** or "contains", "regex", "case_insensitive"

    error_message:
      type: "string"
      expected: "ACGME violation.*80 hour"
      match_type: "regex"
```

***REMOVED******REMOVED******REMOVED*** Collection Criteria

```yaml
expected_outcome:
  assertions:
    affected_persons:
      type: "collection"
      expected_items: ["resident-1", "resident-2"]
      match_type: "exact"  ***REMOVED*** or "subset", "superset", "contains_all"
      order_matters: false

    compliance_violations:
      type: "collection"
      expected_count: 0
      max_count: 0
      critical: true
```

***REMOVED******REMOVED******REMOVED*** State Comparison Criteria

```yaml
expected_outcome:
  state_comparison:
    ***REMOVED*** Compare final state to initial state
    - field: "persons.resident-1.status"
      initial: "active"
      final: "unavailable"

    - field: "assignments.count"
      change_type: "increased"
      min_change: 1
      max_change: 5
```

***REMOVED******REMOVED******REMOVED*** Custom Validation Functions

```yaml
expected_outcome:
  custom_validations:
    - name: "validate_acgme_compliance_full"
      function: "app.testing.validators.full_acgme_check"
      parameters:
        strict_mode: true
        include_warnings: false
      expected_result: true
      critical: true

    - name: "validate_backup_chain_intact"
      function: "app.testing.validators.backup_chain_validator"
      parameters:
        require_full_coverage: true
      expected_result: true
      critical: true
```

***REMOVED******REMOVED*** Scenario Categories

***REMOVED******REMOVED******REMOVED*** 1. N-1 Failure Scenarios
```yaml
category: "n1_failure"
tags: ["resilience", "contingency", "backup"]

***REMOVED*** Test system resilience when one person unavailable
***REMOVED*** Validate backup activation and coverage maintenance
```

***REMOVED******REMOVED******REMOVED*** 2. Swap Operation Scenarios
```yaml
category: "swap"
tags: ["swap", "reassignment", "acgme"]

***REMOVED*** Test swap request processing
***REMOVED*** Validate ACGME compliance after swaps
***REMOVED*** Test multi-swap chains
```

***REMOVED******REMOVED******REMOVED*** 3. ACGME Edge Case Scenarios
```yaml
category: "acgme_edge"
tags: ["acgme", "compliance", "boundary"]

***REMOVED*** Test exact boundary conditions (80 hours, etc.)
***REMOVED*** Validate rule enforcement
***REMOVED*** Test edge cases in compliance logic
```

***REMOVED******REMOVED******REMOVED*** 4. Integration Scenarios
```yaml
category: "integration"
tags: ["integration", "multi_operation", "end_to_end"]

***REMOVED*** Test multiple operations in sequence
***REMOVED*** Validate system consistency
***REMOVED*** Test real-world workflows
```

***REMOVED******REMOVED******REMOVED*** 5. Performance Scenarios
```yaml
category: "performance"
tags: ["performance", "load", "stress"]

***REMOVED*** Test system under load
***REMOVED*** Validate response times
***REMOVED*** Test scalability limits
```

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** 1. Scenario Naming Convention

```
Format: {category}_{operation}_{edge_case}_{number}

Examples:
✅ n1_failure_holiday_coverage_001
✅ swap_multi_chain_acgme_boundary_002
✅ acgme_80hour_exact_limit_003

❌ test1
❌ scenario_about_swaps
❌ n1_test
```

***REMOVED******REMOVED******REMOVED*** 2. Documentation Requirements

**Every scenario MUST have:**
- Clear name describing what it tests
- Description explaining the test purpose
- Rationale for why this edge case matters
- Related bugs/issues if applicable
- Expected behavior clearly defined

***REMOVED******REMOVED******REMOVED*** 3. Isolation Requirements

**Scenarios must be:**
- Completely independent (no shared state)
- Idempotent (can run multiple times with same result)
- Deterministic (same input → same output)
- Self-contained (all setup in scenario file)

***REMOVED******REMOVED******REMOVED*** 4. Fixture Guidelines

**Use fixtures for:**
- Common setup data (base persons, rotations)
- Reusable test data patterns
- Large data sets

**Don't use fixtures for:**
- Scenario-specific data (inline in scenario)
- Temporal data (use variables)
- Data that varies per scenario

***REMOVED******REMOVED******REMOVED*** 5. Assertion Guidelines

**Write assertions that:**
- Are specific and measurable
- Have clear pass/fail criteria
- Include critical flag for must-pass checks
- Provide helpful failure messages

**Avoid:**
- Vague assertions ("system works")
- Impossible assertions (conflicting requirements)
- Too many non-critical assertions (focus on what matters)

***REMOVED******REMOVED*** Example Scenarios

***REMOVED******REMOVED******REMOVED*** Simple N-1 Failure
```yaml
scenario:
  name: "Simple N-1 Failure - Single Resident Unavailable"
  id: "n1-simple-001"
  category: "n1_failure"

  setup:
    persons:
      - {id: "r1", role: "RESIDENT", pgy_level: 2}
      - {id: "r2", role: "RESIDENT", pgy_level: 2, backup_for: ["r1"]}

    assignments:
      - {person_id: "r1", date: "2024-12-25", rotation: "inpatient", hours: 12}

  test_case:
    operation: "mark_unavailable"
    parameters: {person_id: "r1", date: "2024-12-25"}

  expected_outcome:
    assertions:
      coverage_maintained: {type: "boolean", expected: true, critical: true}
      backup_assigned: {type: "boolean", expected: true, critical: true}
```

***REMOVED******REMOVED******REMOVED*** Complex Multi-Operation
```yaml
scenario:
  name: "Multi-Swap Chain with ACGME Validation"
  id: "swap-chain-001"
  category: "swap"

  test_case:
    operations:
      - {step: 1, operation: "request_swap", params: {...}}
      - {step: 2, operation: "validate_acgme", params: {...}}
      - {step: 3, operation: "execute_swap", params: {...}}
      - {step: 4, operation: "request_swap", params: {...}}
      - {step: 5, operation: "execute_swap", params: {...}}
      - {step: 6, operation: "validate_final_state", params: {...}}

  expected_outcome:
    assertions:
      all_swaps_completed: {type: "boolean", expected: true, critical: true}
      acgme_compliant_final: {type: "boolean", expected: true, critical: true}
      swap_chain_length: {type: "numeric", expected: 2, critical: false}
```

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Common Issues

**Issue: Scenario times out**
```
Solution: Increase timeout or optimize operations
- Check for infinite loops
- Reduce test data size
- Profile slow operations
```

**Issue: Fixtures not loading**
```
Solution: Verify fixture file paths and format
- Check file exists at specified path
- Validate JSON/YAML syntax
- Ensure fixture structure matches expected schema
```

**Issue: Assertions failing unexpectedly**
```
Solution: Check tolerance settings and expected values
- Review tolerance thresholds
- Verify expected values are realistic
- Check for timing issues (use appropriate tolerances)
```

***REMOVED******REMOVED*** References

- See `Workflows/scenario-execution.md` for execution details
- See `Workflows/scenario-validation.md` for validation details
- See `Reference/scenario-library.md` for pre-built scenarios
- See `Reference/success-criteria.md` for criteria definitions
