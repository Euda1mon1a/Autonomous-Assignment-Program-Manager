# Success Criteria Reference

Comprehensive definitions of pass/fail criteria for test scenarios. Defines thresholds, quality metrics, and validation rules.

## Criteria Categories

1. **Coverage Criteria** - Schedule completeness
2. **ACGME Compliance Criteria** - Regulatory requirements
3. **Performance Criteria** - Speed and efficiency
4. **Quality Metrics** - Schedule quality
5. **Operational Criteria** - Practical requirements
6. **Data Integrity Criteria** - Consistency checks

---

## Coverage Criteria

### Coverage Completeness

**Definition:** Percentage of required blocks that have assigned personnel.

```yaml
coverage_completeness:
  metric: (assigned_blocks / total_blocks) * 100
  thresholds:
    excellent: ≥ 99%
    good: ≥ 95%
    acceptable: ≥ 90%
    poor: < 90%
    failure: < 85%
  critical: true
  rationale: "Incomplete coverage creates patient safety risk"
```

**Pass Criteria:**
- Coverage completeness ≥ 95% for normal scenarios
- Coverage completeness = 100% for critical rotations (ER, inpatient call)
- Coverage gaps documented and justified if < 100%

**Measurement:**
```python
total_blocks = len(schedule.blocks)
assigned_blocks = len([b for b in schedule.blocks if b.assigned_person])
coverage_completeness = (assigned_blocks / total_blocks) * 100
```

### Coverage Gap Duration

**Definition:** Total hours of uncovered blocks.

```yaml
coverage_gap_hours:
  metric: sum(hours for uncovered blocks)
  thresholds:
    excellent: 0 hours
    acceptable: ≤ 4 hours
    warning: ≤ 12 hours
    critical: > 12 hours
  critical: true
```

**Pass Criteria:**
- Zero coverage gaps for critical scenarios (N-1 failures, holiday coverage)
- ≤ 4 hours total gaps for complex scenarios
- Gaps only in non-critical rotations (admin, education)

### Backup Coverage Depth

**Definition:** Percentage of assignments with designated backup personnel.

```yaml
backup_coverage_depth:
  metric: (assignments_with_backup / total_assignments) * 100
  thresholds:
    excellent: ≥ 95%
    good: ≥ 85%
    acceptable: ≥ 75%
    poor: < 75%
  critical: false
```

**Pass Criteria:**
- ≥ 85% of critical assignments have backup
- All call assignments have backup
- All night float assignments have backup

---

## ACGME Compliance Criteria

### 80-Hour Rule Compliance

**Definition:** No resident exceeds 80 hours per week, averaged over rolling 4 weeks.

```yaml
acgme_80_hour_rule:
  metric: max(resident.rolling_4week_average for all residents)
  thresholds:
    compliant: ≤ 80.0 hours
    violation: > 80.0 hours
  critical: true
  calculation: (week1 + week2 + week3 + week4) / 4
```

**Pass Criteria:**
- ALL residents ≤ 80 hours/week (4-week average)
- Zero violations
- Warning issued if any resident ≥ 78 hours (approaching limit)

**Measurement:**
```python
def check_80_hour_compliance(resident, date):
    weeks = get_past_4_weeks(resident, date)
    hours_per_week = [sum(w.assignment_hours) for w in weeks]
    average = sum(hours_per_week) / 4
    return average <= 80.0
```

### 1-in-7 Day Off Compliance

**Definition:** Each resident has at least one 24-hour period off every 7 days.

```yaml
acgme_one_in_seven:
  metric: max_consecutive_duty_days for all residents
  thresholds:
    compliant: ≤ 6 days
    violation: ≥ 7 days
  critical: true
  averaging: "May be averaged over 4 weeks for some programs"
```

**Pass Criteria:**
- No resident works 7+ consecutive days
- Each resident has ≥ 24 continuous hours off per 7-day period
- If averaged: Average ≥ 1 day off per week over 4 weeks

**Measurement:**
```python
def check_one_in_seven(resident, date):
    consecutive_days = count_consecutive_duty_days(resident, date)
    return consecutive_days <= 6
```

### Duty Period Limit Compliance

**Definition:** No single duty period exceeds 24 hours (28 with exception).

```yaml
acgme_duty_period_limit:
  metric: max(duty_period.hours for all assignments)
  thresholds:
    compliant: ≤ 24 hours
    exception_allowed: ≤ 28 hours (with strategic napping + supervision)
    violation: > 28 hours
  critical: true
```

**Pass Criteria:**
- No duty period > 24 hours without exception
- Exception only granted with: strategic napping facilities + attending supervision
- Zero violations of 28-hour absolute maximum

### Post-Call Rest Compliance

**Definition:** Minimum 8 hours rest after 24-hour duty period.

```yaml
acgme_post_call_rest:
  metric: min(rest_hours after 24h call)
  thresholds:
    compliant: ≥ 8 hours
    violation: < 8 hours
  critical: true
```

**Pass Criteria:**
- ALL post-call rest periods ≥ 8 hours
- No assignments scheduled within 8 hours of call end time
- Exception: 14-hour rest for at-home call

### Supervision Ratio Compliance

**Definition:** Adequate faculty supervision based on PGY level.

```yaml
acgme_supervision_ratios:
  pgy1_ratio:
    metric: residents_pgy1 / faculty_count
    max_ratio: 2.0  # 2 PGY-1s per 1 faculty
    critical: true

  pgy2_pgy3_ratio:
    metric: residents_pgy2_pgy3 / faculty_count
    max_ratio: 4.0  # 4 PGY-2/3s per 1 faculty
    critical: true
```

**Pass Criteria:**
- PGY-1 ratio ≤ 2:1 at all times
- PGY-2/3 ratio ≤ 4:1 at all times
- All rotations have designated attending supervisor

### Night Float Limit Compliance

**Definition:** Maximum 6 consecutive night shifts.

```yaml
acgme_night_float_limit:
  metric: max(consecutive_nights for all residents)
  thresholds:
    compliant: ≤ 6 nights
    violation: ≥ 7 nights
  critical: true
```

**Pass Criteria:**
- No resident works 7+ consecutive nights
- Adequate handoff between night float rotations
- Minimum 24 hours off between night float blocks

### Overall ACGME Compliance

**Definition:** Composite compliance across all ACGME rules.

```yaml
acgme_overall_compliance:
  metric: (compliant_checks / total_checks) * 100
  thresholds:
    compliant: 100%
    violation: < 100%
  critical: true
  components:
    - 80_hour_rule
    - one_in_seven
    - duty_period_limit
    - post_call_rest
    - supervision_ratios
    - night_float_limit
```

**Pass Criteria:**
- 100% compliance required
- Zero violations across all rules
- Scenario fails if ANY ACGME rule violated

---

## Performance Criteria

### Execution Time

**Definition:** Time to complete scenario execution.

```yaml
execution_time_seconds:
  metric: end_time - start_time
  thresholds:
    excellent: < 5 seconds
    good: < 10 seconds
    acceptable: < 30 seconds
    slow: < 60 seconds
    timeout: ≥ timeout_limit
  critical: false  # Performance issue, not correctness
```

**Pass Criteria:**
- Simple scenarios: < 5s
- Complex scenarios: < 30s
- Integration scenarios: < 60s
- Timeout: Scenario fails if exceeds configured timeout

**Tolerance:**
- ±20% for execution time (system load variance)

### Database Query Count

**Definition:** Total number of database queries during execution.

```yaml
database_query_count:
  metric: count(all_sql_queries)
  thresholds:
    excellent: < 20 queries
    good: < 50 queries
    acceptable: < 100 queries
    poor: ≥ 100 queries
  critical: false
```

**Pass Criteria:**
- Use query optimization (joins, batching)
- Avoid N+1 query problems
- Warning if > 100 queries for simple scenarios

### Memory Usage

**Definition:** Peak memory consumption during execution.

```yaml
memory_usage_mb:
  metric: max(memory_usage during execution)
  thresholds:
    excellent: < 128 MB
    good: < 256 MB
    acceptable: < 512 MB
    warning: ≥ 512 MB
  critical: false
```

**Pass Criteria:**
- No memory leaks
- Peak memory < 512 MB for normal scenarios
- Memory released after scenario completion

---

## Quality Metrics

### Workload Balance

**Definition:** Standard deviation of weekly hours across all residents.

```yaml
workload_balance:
  metric: std_dev(weekly_hours for all residents)
  thresholds:
    excellent: < 5 hours
    good: < 10 hours
    acceptable: < 15 hours
    poor: ≥ 15 hours
  critical: false
  rationale: "Fair distribution prevents burnout"
```

**Pass Criteria:**
- Standard deviation < 10 hours for balanced schedules
- No outliers (residents significantly over/under average)
- Equitable distribution of undesirable shifts (nights, weekends)

**Measurement:**
```python
import numpy as np

hours_per_resident = [resident.total_weekly_hours for resident in residents]
std_dev = np.std(hours_per_resident)
mean = np.mean(hours_per_resident)

# Check for outliers (> 2 std dev from mean)
outliers = [h for h in hours_per_resident if abs(h - mean) > 2 * std_dev]
```

### Utilization Rate

**Definition:** Average percentage of maximum hours used across residents.

```yaml
utilization_rate:
  metric: avg(resident_hours / max_hours) * 100
  thresholds:
    optimal: 65-75%
    acceptable: 60-80%
    over_utilized: > 80%
    under_utilized: < 60%
  critical: false
  warning_threshold: 80%
```

**Pass Criteria:**
- Utilization rate 60-80% (sustainable range)
- Warning if > 80% (system stress, burnout risk)
- Avoid under-utilization < 60% (inefficient)

### Schedule Stability

**Definition:** Percentage of assignments unchanged from previous schedule.

```yaml
schedule_stability:
  metric: (unchanged_assignments / total_assignments) * 100
  thresholds:
    stable: ≥ 90%
    moderate_change: 70-90%
    significant_change: < 70%
  critical: false
  applies_to: "Schedule modifications, swaps"
```

**Pass Criteria:**
- Minimize disruption: ≥ 80% stability for modifications
- N-1 scenarios: Expect lower stability (50-70%)
- Track "churn rate" (frequent reassignments)

### Preference Satisfaction

**Definition:** Percentage of resident preferences honored.

```yaml
preference_satisfaction:
  metric: (honored_preferences / total_preferences) * 100
  thresholds:
    excellent: ≥ 80%
    good: ≥ 60%
    acceptable: ≥ 40%
    poor: < 40%
  critical: false
```

**Pass Criteria:**
- Honor ≥ 60% of resident preferences when possible
- Critical rotations take precedence over preferences
- Balance individual preferences with system needs

---

## Operational Criteria

### Assignment Modification Count

**Definition:** Number of assignments changed during scenario.

```yaml
assignments_modified:
  metric: count(changed assignments)
  thresholds:
    minimal: ≤ 3 assignments
    moderate: ≤ 10 assignments
    significant: ≤ 20 assignments
    excessive: > 20 assignments
  critical: false
  tolerance: ± 2 assignments
```

**Pass Criteria:**
- N-1 scenarios: ≤ 10 assignments modified
- Swap scenarios: Exactly 2 assignments modified (one-to-one)
- Multi-swap: ≤ assignments_count * 2

### Persons Affected

**Definition:** Number of unique persons affected by scenario.

```yaml
persons_affected:
  metric: count(unique persons with changed assignments)
  thresholds:
    minimal: ≤ 2 persons
    moderate: ≤ 5 persons
    significant: ≤ 10 persons
    excessive: > 10 persons
  critical: false
```

**Pass Criteria:**
- Minimize blast radius of changes
- N-1 scenarios: Affect only necessary persons
- Avoid cascade effects (unless testing cascade scenarios)

### Notification Delivery

**Definition:** All required notifications sent successfully.

```yaml
notification_delivery:
  metric: (successful_notifications / required_notifications) * 100
  thresholds:
    compliant: 100%
    partial: ≥ 90%
    failure: < 90%
  critical: true  # Communication is critical
```

**Pass Criteria:**
- 100% of required notifications delivered
- Residents notified of assignment changes
- Program director notified of violations/emergencies
- Faculty notified of supervision requirement changes

### Audit Trail Completeness

**Definition:** All changes logged with timestamps and user attribution.

```yaml
audit_trail_completeness:
  metric: (logged_changes / total_changes) * 100
  thresholds:
    compliant: 100%
    violation: < 100%
  critical: true
  required_fields:
    - timestamp
    - user_id
    - action
    - before_state
    - after_state
    - reason
```

**Pass Criteria:**
- 100% of changes logged
- Audit log immutable (append-only)
- All required fields populated
- Audit trail survives rollback

---

## Data Integrity Criteria

### No Double Booking

**Definition:** No person assigned to overlapping time blocks.

```yaml
no_double_booking:
  metric: count(persons with overlapping assignments)
  thresholds:
    compliant: 0
    violation: > 0
  critical: true
```

**Pass Criteria:**
- Zero double-bookings
- All assignments non-overlapping for same person
- Time conflict detection working correctly

**Measurement:**
```python
def check_double_booking(person, date):
    assignments = get_assignments(person, date)
    for i, a1 in enumerate(assignments):
        for a2 in assignments[i+1:]:
            if a1.overlaps(a2):
                return False  # Double booking detected
    return True  # No conflicts
```

### No Orphaned Assignments

**Definition:** No assignments without valid person or rotation.

```yaml
no_orphaned_assignments:
  metric: count(assignments with null person_id or rotation_id)
  thresholds:
    compliant: 0
    violation: > 0
  critical: true
```

**Pass Criteria:**
- All assignments have valid person_id
- All assignments have valid rotation_id
- All assignments have valid date
- Foreign key constraints enforced

### State Consistency

**Definition:** Database state is consistent after all operations.

```yaml
state_consistency:
  checks:
    - referential_integrity: "All foreign keys valid"
    - constraint_satisfaction: "All DB constraints met"
    - no_partial_transactions: "No uncommitted changes"
    - backup_chain_integrity: "All backup references valid"
  critical: true
```

**Pass Criteria:**
- All database constraints satisfied
- No orphaned records
- Backup chains intact (no circular references)
- Aggregate counts match detail records

### Idempotency

**Definition:** Running scenario multiple times produces same result.

```yaml
idempotency:
  metric: final_state(run1) == final_state(run2)
  critical: true  # For deterministic scenarios
  applies_to: "Non-random scenarios only"
```

**Pass Criteria:**
- Same input → same output (deterministic scenarios)
- State snapshots identical across runs
- No side effects from previous runs

---

## Composite Success Criteria

### Scenario Pass Definition

A scenario PASSES if ALL of the following are true:

```yaml
scenario_pass_criteria:
  required_conditions:
    - acgme_compliance: 100%
    - coverage_completeness: ≥ 95%
    - no_double_booking: true
    - no_orphaned_assignments: true
    - state_consistency: true
    - all_critical_assertions: passed
```

**Critical Assertions:**
- ACGME compliance = 100%
- Coverage completeness ≥ threshold
- No data integrity violations
- All scenario-specific critical assertions passed

**Non-Critical Failures:**
- Performance below target (slow but correct)
- Workload imbalance (functional but not optimal)
- Low preference satisfaction (compliant but less ideal)

### Scenario Fail Definition

A scenario FAILS if ANY of the following are true:

```yaml
scenario_fail_criteria:
  failure_conditions:
    - any_acgme_violation: true
    - critical_assertion_failed: true
    - double_booking_detected: true
    - data_corruption: true
    - timeout_exceeded: true
    - execution_error: true
```

### Scenario Warning Definition

A scenario issues WARNING if:

```yaml
scenario_warning_criteria:
  warning_conditions:
    - utilization_rate: > 80%
    - workload_std_dev: > 10 hours
    - coverage_completeness: < 100% but ≥ 95%
    - execution_time: > expected but < timeout
```

Warnings don't fail scenario but indicate areas for improvement.

---

## Tolerance Configuration

### Default Tolerances

```yaml
default_tolerances:
  numeric_percentage: 0.05  # 5%
  numeric_absolute: 2       # ±2 for counts
  timestamp_seconds: 1      # 1 second
  boolean_exact: true       # No tolerance for boolean
```

### Field-Specific Tolerances

```yaml
field_tolerances:
  execution_time_seconds:
    percentage: 0.20  # ±20%
    rationale: "System load variance"

  assignments_modified:
    absolute: 3  # ±3 assignments
    rationale: "Optimization may vary"

  persons_affected:
    absolute: 2  # ±2 persons
    rationale: "Backup chain alternatives"

  weekly_hours:
    absolute: 1.0  # ±1 hour
    rationale: "Rounding and partial shifts"
```

### Scenario-Specific Overrides

```yaml
scenario_type_tolerances:
  n1_failure:
    assignments_modified:
      absolute: 5  # Higher tolerance for N-1 scenarios

  integration:
    execution_time_seconds:
      percentage: 0.50  # ±50% for complex integration tests
```

---

## Validation Checklist

### Pre-Execution Validation

- [ ] Scenario structure valid (YAML syntax)
- [ ] All required fields present
- [ ] Variable references resolvable
- [ ] Fixtures exist and loadable
- [ ] Preconditions defined and checkable

### Post-Execution Validation

- [ ] All assertions evaluated
- [ ] ACGME compliance checked
- [ ] Coverage completeness verified
- [ ] Data integrity validated
- [ ] Performance metrics captured
- [ ] Audit trail complete

### Failure Analysis Checklist

If scenario fails:

1. **Identify failure type:**
   - [ ] Critical assertion failed
   - [ ] ACGME violation
   - [ ] Data integrity issue
   - [ ] Timeout exceeded
   - [ ] Execution error

2. **Categorize failures:**
   - [ ] Critical (must fix)
   - [ ] Non-critical (optimization)
   - [ ] Environmental (test infrastructure)

3. **Root cause analysis:**
   - [ ] Review execution logs
   - [ ] Compare pre/post state snapshots
   - [ ] Check for timing issues
   - [ ] Verify test data correctness

4. **Resolution:**
   - [ ] Fix code if bug
   - [ ] Update scenario if expectation wrong
   - [ ] Add test case if coverage gap

---

## References

- See `Workflows/scenario-definition.md` for defining success criteria in scenarios
- See `Workflows/scenario-validation.md` for validation implementation
- See `Reference/scenario-library.md` for scenario-specific criteria
- ACGME Common Program Requirements: https://www.acgme.org/

---

## Summary Table

| Criteria Category | Critical | Pass Threshold | Tolerance |
|-------------------|----------|----------------|-----------|
| Coverage Completeness | ✅ | ≥ 95% | ±2% |
| ACGME 80-Hour Rule | ✅ | 100% compliant | 0 |
| ACGME 1-in-7 Rule | ✅ | 100% compliant | 0 |
| No Double Booking | ✅ | 0 conflicts | 0 |
| State Consistency | ✅ | 100% consistent | 0 |
| Execution Time | ❌ | < 30s | ±20% |
| Workload Balance | ❌ | Std dev < 10h | ±2h |
| Utilization Rate | ❌ | 60-80% | ±5% |
| Assignments Modified | ❌ | Scenario-specific | ±2-5 |

**Critical (✅):** Scenario fails if not met
**Non-Critical (❌):** Warning issued, scenario can still pass
