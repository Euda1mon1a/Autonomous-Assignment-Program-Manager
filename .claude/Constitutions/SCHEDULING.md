# SCHEDULING CONSTITUTION - Domain-Specific Rules

> **Version:** 1.0.0
> **Last Updated:** 2025-12-26
> **Purpose:** Rules specific to medical residency scheduling operations
> **Parent Document:** `.claude/CONSTITUTION.md`
> **Related:** `CORE.md`, `SAFETY_CRITICAL.md`

---

## I. SCOPE

This Scheduling Constitution defines rules specific to medical residency schedule generation, validation, and management. These rules supplement the Core Constitution and are enforced for all scheduling-related operations.

**Domain Mission:** Generate compliant, resilient, and equitable schedules that protect resident welfare and ensure patient safety.

---

## II. ACGME COMPLIANCE (Tier 0 - Absolute)

**Principle:** ACGME compliance is the highest priority and cannot be violated under any circumstance.

### A. 80-Hour Rule

**Requirement:** Maximum 80 hours per week, averaged over rolling 4-week periods.

**Validation:**
- Pre-generation: Check projected hours before assigning blocks
- Post-generation: Validate entire schedule for compliance
- Runtime: Monitor actual hours and alert on threshold approach

**Calculation:**
```python
def validate_80_hour_rule(person_id: str, start_date: date) -> bool:
    """
    Validate 80-hour rule for 4-week rolling period.

    Returns:
        True if compliant, False if violation detected
    """
    end_date = start_date + timedelta(weeks=4)
    total_hours = sum_hours(person_id, start_date, end_date)
    avg_weekly_hours = total_hours / 4

    if avg_weekly_hours > 80:
        logger.error(
            "80_hour_violation",
            person_id=person_id,
            start_date=start_date,
            total_hours=total_hours,
            avg_weekly=avg_weekly_hours
        )
        return False

    return True
```

**Consequences of Violation:**
- Schedule generation MUST fail
- No override mechanism permitted
- Alert program director immediately
- Document in compliance audit log

### B. 1-in-7 Rule

**Requirement:** One 24-hour period free of clinical duties every 7 days.

**Validation:**
- Clock starts at midnight local time (HST for this deployment)
- 24-hour period must be completely free (no calls, no clinic)
- Window slides day-by-day (not fixed weekly)

**Calculation:**
```python
def validate_1_in_7_rule(person_id: str, current_date: date) -> bool:
    """
    Validate 1-in-7 rule for rolling 7-day window.

    Returns:
        True if compliant (at least one 24-hour free period in last 7 days)
    """
    start_date = current_date - timedelta(days=6)

    # Check each day in window
    for day_offset in range(7):
        check_date = start_date + timedelta(days=day_offset)

        # Check if this 24-hour period is completely free
        if is_day_completely_free(person_id, check_date):
            return True

    # No free 24-hour period found in 7-day window
    logger.error(
        "1_in_7_violation",
        person_id=person_id,
        window_start=start_date,
        window_end=current_date
    )
    return False
```

**Special Cases:**
- Holiday calls may extend duty periods, but 1-in-7 still applies
- Post-call days count as free if no scheduled duties
- Mandatory training/conferences do NOT count as free time

### C. Supervision Ratios

**Requirement:** Maintain adequate faculty supervision for all clinical activities.

**Ratios:**
- PGY-1 (Intern): Maximum 2 residents per 1 faculty
- PGY-2/3 (Senior): Maximum 4 residents per 1 faculty
- Procedures: 1:1 ratio for first 10 independent procedures

**Validation:**
```python
def validate_supervision_ratio(
    block_id: int,
    rotation_type: str
) -> tuple[bool, str]:
    """
    Validate faculty supervision ratios for a block.

    Returns:
        (is_compliant, violation_message)
    """
    assignments = get_block_assignments(block_id)

    # Count residents by PGY level
    pgy1_count = count_residents_by_level(assignments, "PGY-1")
    pgy2_3_count = count_residents_by_level(assignments, "PGY-2/3")

    # Count faculty
    faculty_count = count_faculty(assignments)

    # Check PGY-1 ratio
    if pgy1_count > 0:
        ratio_pgy1 = pgy1_count / faculty_count
        if ratio_pgy1 > 2:
            return False, f"PGY-1 ratio violation: {ratio_pgy1:.1f}:1 exceeds 2:1"

    # Check PGY-2/3 ratio
    if pgy2_3_count > 0:
        ratio_pgy23 = pgy2_3_count / faculty_count
        if ratio_pgy23 > 4:
            return False, f"PGY-2/3 ratio violation: {ratio_pgy23:.1f}:1 exceeds 4:1"

    return True, "Supervision ratios compliant"
```

### D. ACGME Validation Points

**When to Validate:**

1. **Pre-Generation**
   - Before schedule generation starts
   - Check constraint feasibility
   - Verify no impossible requirements

2. **During Generation**
   - Real-time constraint checking during solver execution
   - Abort if violation detected
   - Prevents wasted computation

3. **Post-Generation**
   - Full compliance audit of generated schedule
   - Generate compliance report
   - Required before schedule deployment

4. **Runtime Monitoring**
   - Continuous monitoring during schedule execution
   - Alert on threshold approach (e.g., 75 hours/week)
   - Daily compliance checks

5. **After Schedule Changes**
   - Validate after every swap request
   - Validate after emergency reassignments
   - Validate after leave approval

6. **Monthly Audits**
   - Comprehensive compliance report
   - Statistical analysis of violations
   - Trend analysis for proactive intervention

---

## III. CONSTRAINT HIERARCHY

**Principle:** Constraints are prioritized in strict tiers. Lower tiers CANNOT override higher tiers.

### Tier 1: Regulatory (Absolute)

**Hard Constraints - Violations MUST fail operation:**

- ACGME 80-hour rule
- ACGME 1-in-7 rule
- ACGME supervision ratios
- Licensing requirements (valid medical license)
- Credentialing requirements (slot-type specific)
- Legal restrictions (duty hour caps mandated by law)

**Enforcement:** Schedule generation MUST fail if Tier 1 violated.

**Agent Directive:** REFUSE to generate schedule violating Tier 1 constraints.

### Tier 2: Institutional Policy

**Hard Constraints - Violations require documented waiver:**

- Local work hour limits (e.g., 70 hours if stricter than ACGME)
- Clinical coverage requirements (minimum staffing levels)
- Specialty-specific rules (e.g., pediatrics continuity clinic)
- Call schedule patterns (e.g., max 3 nights in a row)
- Training requirements (e.g., all PGY-1s must attend weekly conference)

**Enforcement:** Hard constraints unless explicit waiver documented and approved.

**Waiver Process:**
1. Document reason for waiver
2. Program director approval required
3. Limited duration (max 30 days)
4. Logged in audit trail
5. Regular review of active waivers

### Tier 3: Optimization Preferences

**Soft Constraints - Optimize but can be violated if necessary:**

- Fairness (equal distribution of undesirable shifts)
- Continuity (minimize resident rotations, prefer same faculty)
- Learning opportunities (procedure exposure, case variety)
- Personal preferences (preferred clinic days, call nights)
- Travel minimization (reduce commute, co-locate teams)

**Enforcement:** Penalty-based optimization. Violations penalized in objective function.

**Penalty Weights:**
```python
TIER_3_PENALTIES = {
    "unfair_distribution": 10,  # Penalty per unfair shift assignment
    "rotation_change": 5,       # Penalty per unnecessary rotation change
    "missed_learning": 3,       # Penalty per missed learning opportunity
    "preference_violation": 1   # Penalty per preference violation
}
```

### Tier 4: Nice-to-Have

**Lowest Priority - Ignored if conflicts arise:**

- Preferred clinic days (e.g., prefer Mondays over Fridays)
- Social events (e.g., prefer off on friend's birthday)
- Commute optimization (prefer assignments closer to home)
- Preferred colleagues (prefer working with specific faculty)

**Enforcement:** Best-effort. No penalty if ignored.

**Agent Directive:** Communicate to users that Tier 4 requests are best-effort only.

---

## IV. RESILIENCE FRAMEWORK

**Principle:** Schedules must be resilient to disruptions and maintain safe staffing levels.

### A. Defense-in-Depth Levels

**Utilization Thresholds:**

| Level | Color | Utilization | Required Actions |
|-------|-------|-------------|------------------|
| **Safe** | GREEN | ≤ 80% | Normal operations |
| **Caution** | YELLOW | 80-85% | Log warning, alert coordinators, monitor closely |
| **Warning** | ORANGE | 85-90% | Block new non-essential assignments, escalate to PD |
| **Critical** | RED | 90-95% | Activate N-1 contingency, emergency protocols |
| **Emergency** | BLACK | > 95% | Activate N-2 contingency, load shedding, external help |

**Utilization Calculation:**
```python
def calculate_utilization(
    date_range: tuple[date, date]
) -> dict[str, float]:
    """
    Calculate staffing utilization across all roles.

    Returns:
        Dictionary of {role: utilization_percentage}
    """
    start_date, end_date = date_range
    utilization = {}

    for role in ["Faculty", "PGY-1", "PGY-2", "PGY-3"]:
        total_capacity = get_total_capacity(role, start_date, end_date)
        assigned_hours = get_assigned_hours(role, start_date, end_date)

        utilization[role] = (assigned_hours / total_capacity) * 100

    return utilization
```

**Agent Actions by Level:**

- **GREEN**: Normal operations, proactive scheduling
- **YELLOW**: Alert coordinators, increase monitoring frequency to daily
- **ORANGE**: Block new assignments, require PD approval for exceptions
- **RED**: Activate backup faculty, cancel electives, defer non-urgent procedures
- **BLACK**: Request external coverage, activate mutual aid agreements

### B. N-1/N-2 Contingency

**Principle:** System must function gracefully when key personnel unavailable.

**N-1 Contingency:** System operates normally with 1 key person unavailable
- Must maintain ACGME compliance
- Coverage gaps filled by backup personnel
- No reduction in patient safety

**N-2 Contingency:** System degrades gracefully with 2 key people unavailable
- May violate Tier 3/4 constraints
- MUST maintain Tier 1/2 constraints (ACGME, safety)
- Activate mutual aid agreements if needed

**Validation:**
```python
async def validate_n1_contingency(schedule: Schedule) -> bool:
    """
    Validate schedule can handle loss of 1 key person.

    Tests each key person individually.
    """
    key_persons = identify_key_persons(schedule)

    for person in key_persons:
        # Simulate person unavailability
        test_schedule = schedule.without(person)

        # Validate remaining schedule
        if not await validate_acgme_compliance(test_schedule):
            logger.error(
                "n1_contingency_failure",
                person_id=person.id,
                role=person.role
            )
            return False

        # Check coverage gaps
        gaps = find_coverage_gaps(test_schedule)
        if gaps and not can_fill_gaps(gaps):
            logger.error(
                "n1_coverage_gap",
                person_id=person.id,
                gaps=len(gaps)
            )
            return False

    return True
```

**Key Person Identification:**
- Unique specialists (only ortho surgeon, only pediatrician)
- High-utilization faculty (>80% scheduled)
- Single coverage roles (solo night coverage)

### C. Health Check Requirements

**Schedule Health Threshold:** `health >= 0.7`

**Health Calculation:**
```python
def calculate_schedule_health(schedule: Schedule) -> float:
    """
    Calculate overall schedule health score (0.0 to 1.0).

    Combines multiple resilience metrics.
    """
    metrics = {
        "acgme_compliance": 1.0 if validate_acgme(schedule) else 0.0,
        "coverage_completeness": calculate_coverage_ratio(schedule),
        "utilization_safety": 1.0 - (max_utilization(schedule) / 100),
        "n1_contingency": 1.0 if validate_n1(schedule) else 0.5,
        "fairness": calculate_fairness_score(schedule)
    }

    # Weighted average
    weights = {
        "acgme_compliance": 0.40,  # 40% weight
        "coverage_completeness": 0.25,
        "utilization_safety": 0.20,
        "n1_contingency": 0.10,
        "fairness": 0.05
    }

    health = sum(metrics[k] * weights[k] for k in metrics)
    return health
```

**Minimum Health Requirements:**
- Production schedules: health >= 0.85
- Emergency schedules: health >= 0.70
- Test schedules: health >= 0.50

**Agent Directive:** If schedule health < 0.7, REJECT and require remediation before deployment.

---

## V. SCHEDULE VALIDATION REQUIREMENTS

**Principle:** All schedules must pass comprehensive validation before deployment.

### A. Validation Checklist

**Pre-Deployment Validation:**

- [ ] ACGME 80-hour rule validated for all residents
- [ ] ACGME 1-in-7 rule validated for all residents
- [ ] Supervision ratios validated for all blocks
- [ ] Coverage gaps identified and resolved
- [ ] N-1 contingency validated
- [ ] Utilization thresholds checked (all roles ≤ 80%)
- [ ] Credential requirements validated (slot-type invariants)
- [ ] Conflict detection completed (no double-booking)
- [ ] Fairness metrics computed (Gini coefficient ≤ 0.3)
- [ ] Schedule health >= 0.7
- [ ] Backup schedule generated and tested

### B. Validation Enforcement

**Agent Actions:**

1. **Run Full Validation**
   ```python
   validation_result = await run_full_validation(schedule)
   ```

2. **Check for Failures**
   ```python
   if validation_result.has_critical_failures():
       logger.error("schedule_validation_failed", failures=validation_result.failures)
       raise ValidationError("Schedule has critical validation failures")
   ```

3. **Generate Compliance Report**
   ```python
   report = generate_compliance_report(schedule, validation_result)
   save_report(report, f"compliance_report_{schedule.id}.pdf")
   ```

4. **Require Approval for Warnings**
   ```python
   if validation_result.has_warnings():
       logger.warning("schedule_has_warnings", warnings=validation_result.warnings)
       # Require explicit PD approval before deployment
       await request_approval(schedule, validation_result.warnings)
   ```

---

## VI. BACKUP REQUIREMENTS

**Principle:** Never generate schedules without backup capability.

### A. Backup Before Generation

**Mandatory Pre-Generation Backup:**

```python
async def generate_schedule_with_backup(
    db: AsyncSession,
    params: ScheduleParams
) -> Schedule:
    """
    Generate schedule with mandatory backup of current state.

    This ensures rollback capability if generation fails or produces
    non-compliant schedule.
    """
    # REQUIRED: Backup current schedule
    logger.info("Creating pre-generation backup...")
    backup = await create_schedule_backup(db)

    try:
        # Generate new schedule
        logger.info("Generating schedule...", params=params)
        schedule = await generate_schedule(db, params)

        # Validate
        validation = await validate_schedule(schedule)
        if not validation.is_compliant:
            raise ValidationError(f"Generated schedule non-compliant: {validation.failures}")

        # Commit
        await db.commit()
        logger.info("Schedule generation successful", schedule_id=schedule.id)
        return schedule

    except Exception as e:
        logger.error("Schedule generation failed, rolling back...", error=str(e))

        # Restore from backup
        await restore_schedule_backup(db, backup)
        await db.commit()

        raise
```

**Backup Contents:**
- All current assignments
- Metadata (generation timestamp, parameters)
- Validation results
- Correlation ID for audit trail

### B. Backup Retention

**Retention Policy:**
- Keep last 5 schedule versions
- Keep monthly snapshots for 1 year
- Keep annual snapshots indefinitely
- Compressed storage after 90 days

**Backup Location:**
- Primary: Database (schedule_backups table)
- Secondary: Encrypted file storage (S3 or local)
- Tertiary: Offsite backup (for disaster recovery)

---

## VII. SWAP VALIDATION

**Principle:** All schedule swaps must maintain ACGME compliance and system integrity.

### A. Swap Validation Sequence

**Required Checks (in order):**

1. **Pre-Swap Compliance Check**
   ```python
   # Verify both parties currently compliant
   assert validate_acgme_compliance(person_a)
   assert validate_acgme_compliance(person_b)
   ```

2. **Post-Swap Simulation**
   ```python
   # Calculate projected work hours after swap
   simulated_schedule = simulate_swap(person_a, person_b, shifts)
   projected_hours_a = calculate_hours(simulated_schedule, person_a)
   projected_hours_b = calculate_hours(simulated_schedule, person_b)
   ```

3. **Conflict Detection**
   ```python
   # Check for double-booking or rotation conflicts
   conflicts = detect_conflicts(simulated_schedule)
   if conflicts:
       raise ConflictError(f"Swap creates conflicts: {conflicts}")
   ```

4. **Credential Verification**
   ```python
   # Ensure both parties qualified for swapped slots
   assert has_credentials(person_a, shift_b.slot_type)
   assert has_credentials(person_b, shift_a.slot_type)
   ```

5. **Approval Chain**
   ```python
   # Track requestor, approver, execution timestamp
   swap_request.requestor = person_a
   swap_request.approver = faculty_or_coordinator
   swap_request.approved_at = datetime.utcnow()
   ```

### B. Forbidden Swaps

**Never Permit:**
- Swaps that create ACGME violations
- Swaps without proper approval (faculty or coordinator)
- Swaps that bypass credential requirements
- Swaps lacking audit trail
- Swaps during critical coverage periods (without PD override)
- Swaps that create N-1 contingency failures

### C. Rollback Window

**Requirement:** All swaps must be reversible within 24 hours.

```python
async def execute_swap_with_rollback(
    db: AsyncSession,
    swap_request: SwapRequest
) -> SwapExecution:
    """
    Execute swap with 24-hour rollback window.
    """
    # Store original assignments
    original_assignments = {
        "person_a": await get_assignments(swap_request.person_a_id),
        "person_b": await get_assignments(swap_request.person_b_id)
    }

    # Store in audit table
    audit_record = await store_swap_audit(swap_request, original_assignments)

    # Execute swap
    execution = await perform_swap(db, swap_request)

    # Set rollback deadline
    execution.rollback_deadline = datetime.utcnow() + timedelta(hours=24)

    await db.commit()
    return execution
```

---

## VIII. COVERAGE REQUIREMENTS

**Principle:** All clinical services must maintain minimum staffing levels.

### A. Minimum Staffing Levels

**By Service:**

| Service | Minimum Staff | Time Period |
|---------|---------------|-------------|
| Emergency Department | 2 residents + 1 faculty | 24/7 |
| Inpatient Ward | 1 resident per 8 patients + 1 faculty | Daytime |
| Night Float | 1 resident + 1 attending (phone) | Nights |
| Clinic | 1 faculty per 4 residents | Business hours |
| Procedures | 1 faculty per 2 residents | When scheduled |

**Validation:**
```python
def validate_coverage(block_id: int) -> tuple[bool, list[str]]:
    """
    Validate minimum staffing levels for a block.

    Returns:
        (is_compliant, list_of_violations)
    """
    violations = []

    for service in REQUIRED_SERVICES:
        min_required = MINIMUM_STAFFING[service]
        actual_count = count_assignments(block_id, service)

        if actual_count < min_required:
            violations.append(
                f"{service} understaffed: {actual_count} < {min_required}"
            )

    return len(violations) == 0, violations
```

### B. Coverage Gap Detection

**Algorithm:**
1. Identify all required coverage periods
2. Count assigned staff for each period
3. Compare to minimum requirements
4. Flag periods below threshold
5. Prioritize gaps by severity (critical services first)

**Gap Severity:**
- **CRITICAL**: Zero coverage for required service
- **HIGH**: Below minimum but partial coverage
- **MEDIUM**: At minimum but no backup
- **LOW**: Adequate coverage but tight

---

## IX. FAIRNESS & EQUITY

**Principle:** Distribute workload and undesirable shifts equitably.

### A. Fairness Metrics

**Gini Coefficient:** Measure inequality in shift distribution
- Target: ≤ 0.3 (moderate inequality)
- Alert: > 0.4 (high inequality)
- Reject: > 0.5 (severe inequality)

**Calculation:**
```python
def calculate_gini_coefficient(assignments: list[Assignment]) -> float:
    """
    Calculate Gini coefficient for shift distribution.

    Returns:
        Value between 0 (perfect equality) and 1 (perfect inequality)
    """
    # Count shifts per person
    shift_counts = Counter(a.person_id for a in assignments)
    counts = sorted(shift_counts.values())

    n = len(counts)
    if n == 0:
        return 0.0

    # Gini formula
    index = sum((i + 1) * count for i, count in enumerate(counts))
    gini = (2 * index) / (n * sum(counts)) - (n + 1) / n

    return gini
```

### B. Undesirable Shift Distribution

**Rotation Equitably:**
- Weekend calls
- Holiday coverage
- Night float blocks
- High-acuity rotations

**Tracking:**
```python
async def track_undesirable_shifts(person_id: str, year: int) -> dict:
    """
    Track distribution of undesirable shifts for fairness analysis.
    """
    return {
        "weekend_calls": count_shifts(person_id, year, "weekend_call"),
        "holiday_coverage": count_shifts(person_id, year, "holiday"),
        "night_float_weeks": count_shifts(person_id, year, "night_float"),
        "trauma_rotations": count_shifts(person_id, year, "trauma")
    }
```

---

## X. CROSS-REFERENCES

**Related Constitutions:**
- **CORE.md**: Universal rules (logging, security, error handling)
- **SAFETY_CRITICAL.md**: Non-negotiable safety principles and forbidden operations

**Related Documentation:**
- `docs/architecture/SOLVER_ALGORITHM.md`: Technical details of constraint solver
- `docs/architecture/cross-disciplinary-resilience.md`: Resilience framework concepts
- `backend/app/scheduling/acgme_validator.py`: Implementation of ACGME validation

---

## XI. ENFORCEMENT

**Agent Responsibilities:**

1. **Validate Before Action**
   - Run all applicable validations before schedule operations
   - Document validation results in audit log

2. **Refuse Non-Compliant Operations**
   - Politely refuse operations violating Tier 1 constraints
   - Explain rationale and suggest alternatives

3. **Escalate Violations**
   - Alert program director for ACGME violations
   - Log all violations in compliance audit system

4. **Continuous Monitoring**
   - Monitor schedule health metrics
   - Alert on threshold crossings (utilization, fairness)

---

## XII. AMENDMENT HISTORY

| Version | Date | Changes | Approved By |
|---------|------|---------|-------------|
| 1.0.0 | 2025-12-26 | Initial Scheduling Constitution | System Architect |

---

**END OF SCHEDULING CONSTITUTION**

*These scheduling rules ensure ACGME compliance, resilience, and fairness in all schedule operations.*
