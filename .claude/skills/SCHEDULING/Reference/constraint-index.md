# Constraint Index

Complete catalog of all scheduling constraints with priorities, relaxation rules, and implementation references.

---

## Overview

This index organizes all scheduling constraints by tier (absolute, institutional, optimization) and provides quick reference for constraint properties, relaxation strategies, and code locations.

**Tier System:**
- **Tier 1 (Absolute)**: ACGME regulatory requirements - cannot be violated
- **Tier 2 (Institutional)**: Program policies - require approval to override
- **Tier 3 (Optimization)**: Preferences and fairness - can be relaxed

---

## Tier 1: Absolute Constraints (ACGME)

Cannot be violated under any circumstances. Schedule is invalid if any Tier 1 constraint fails.

### 1.1 Work Hour Constraint (80-Hour Rule)

**Constraint ID:** `ACGME_80_HOUR`
**Priority:** P0 (Absolute)
**Type:** Hard constraint

**Rule:**
Maximum 80 hours per week, averaged over any rolling 4-week period.

**Parameters:**
```python
max_hours_per_week = 80
rolling_window_weeks = 4
```

**Validation:**
```python
for week_start in all_weeks:
    four_week_window = [week_start, week_start+1, week_start+2, week_start+3]
    total_hours = sum(weekly_hours[w] for w in four_week_window)
    avg_hours = total_hours / 4.0

    if avg_hours > 80:
        raise ACGMEViolation("80-hour rule violated")
```

**Relaxation:** None allowed

**Implementation:**
- File: `backend/app/scheduling/constraints/acgme.py`
- Class: `WorkHourConstraint`
- MCP Tool: `validate_acgme_compliance`

**See Also:** `Reference/acgme-rules.md` - 80-Hour Rule section

---

### 1.2 Days Off Constraint (1-in-7 Rule)

**Constraint ID:** `ACGME_1_IN_7`
**Priority:** P0 (Absolute)
**Type:** Hard constraint

**Rule:**
One 24-hour period free from duty every 7 days, averaged over 4 weeks.

**Parameters:**
```python
min_days_off_per_week = 1
rolling_window_weeks = 4
day_off_hours = 24  # Consecutive hours
```

**Validation:**
```python
for four_week_period in all_periods:
    days_off = count_full_days_off(person, four_week_period)

    if days_off < 4:  # Less than 1 per week
        raise ACGMEViolation("1-in-7 rule violated")
```

**Relaxation:** None allowed (rare documented exceptions for patient continuity)

**Implementation:**
- File: `backend/app/scheduling/constraints/acgme.py`
- Class: `DaysOffConstraint`

---

### 1.3 Supervision Ratio Constraint (PGY-1)

**Constraint ID:** `ACGME_SUPERVISION_PGY1`
**Priority:** P0 (Absolute)
**Type:** Hard constraint

**Rule:**
Maximum 2 PGY-1 residents per 1 faculty member.

**Parameters:**
```python
max_pgy1_per_faculty = 2
supervision_type = 'direct'  # Direct supervision required
```

**Validation:**
```python
for block, rotation in all_assignments:
    pgy1_count = count_residents(block, rotation, pgy_level=1)
    faculty_count = count_faculty(block, rotation)

    if pgy1_count > 2 * faculty_count:
        raise ACGMEViolation("PGY-1 supervision ratio violated")
```

**Relaxation:** None allowed

**Implementation:**
- File: `backend/app/scheduling/constraints/acgme.py`
- Class: `SupervisionRatioConstraint`

---

### 1.4 Supervision Ratio Constraint (PGY-2/3)

**Constraint ID:** `ACGME_SUPERVISION_PGY23`
**Priority:** P0 (Absolute)
**Type:** Hard constraint

**Rule:**
Maximum 4 PGY-2/3 residents per 1 faculty member.

**Parameters:**
```python
max_pgy23_per_faculty = 4
supervision_type = 'indirect_with_direct_available'
```

**Validation:**
```python
for block, rotation in all_assignments:
    pgy23_count = count_residents(block, rotation, pgy_level__in=[2,3])
    faculty_count = count_faculty(block, rotation)

    if pgy23_count > 4 * faculty_count:
        raise ACGMEViolation("PGY-2/3 supervision ratio violated")
```

**Relaxation:** None allowed

**Implementation:**
- File: `backend/app/scheduling/constraints/acgme.py`
- Class: `SupervisionRatioConstraint`

---

### 1.5 Duty Period Limit Constraint

**Constraint ID:** `ACGME_DUTY_PERIOD`
**Priority:** P0 (Absolute)
**Type:** Hard constraint

**Rule:**
Maximum 24-hour duty period (plus 4 hours transition).

**Parameters:**
```python
max_continuous_hours = 24
transition_hours = 4  # For handoff/education
min_rest_after_24h = 14  # Hours
min_rest_standard = 8   # Hours
```

**Validation:**
```python
for shift in all_shifts:
    if shift.duration > 24:
        raise ACGMEViolation("Duty period exceeds 24 hours")

    next_shift = get_next_shift(shift.person)
    rest_hours = (next_shift.start - shift.end).total_seconds() / 3600

    required_rest = 14 if shift.duration == 24 else 8

    if rest_hours < required_rest:
        raise ACGMEViolation(f"Insufficient rest: {rest_hours}h < {required_rest}h")
```

**Relaxation:** None allowed

**Implementation:**
- File: `backend/app/scheduling/constraints/acgme.py`
- Class: `DutyPeriodConstraint`

---

### 1.6 Night Float Limit Constraint

**Constraint ID:** `ACGME_NIGHT_FLOAT`
**Priority:** P0 (Absolute)
**Type:** Hard constraint

**Rule:**
Maximum 6 consecutive nights on night float.

**Parameters:**
```python
max_consecutive_nights = 6
min_rest_after_nf = 24  # Hours
```

**Validation:**
```python
for nf_block in get_night_float_blocks(person):
    consecutive_nights = count_consecutive_nights(nf_block)

    if consecutive_nights > 6:
        raise ACGMEViolation("Night float exceeds 6 consecutive nights")
```

**Relaxation:** None allowed

**Implementation:**
- File: `backend/app/scheduling/constraints/acgme.py`
- Class: `NightFloatLimitConstraint`

---

### 1.7 On-Call Frequency Constraint

**Constraint ID:** `ACGME_CALL_FREQUENCY`
**Priority:** P0 (Absolute)
**Type:** Hard constraint

**Rule:**
In-house call no more frequently than every 3rd night.

**Parameters:**
```python
min_days_between_call = 2  # Every 3rd night = 2 days between
rolling_window_weeks = 4
```

**Validation:**
```python
for four_week_period in all_periods:
    call_nights = get_call_nights(person, four_week_period)

    if len(call_nights) > 9:  # 28 days / 3 ≈ 9
        raise ACGMEViolation("Call frequency exceeds every 3rd night")
```

**Relaxation:** None allowed

**Implementation:**
- File: `backend/app/scheduling/constraints/acgme.py`
- Class: `CallFrequencyConstraint`

---

## Tier 2: Institutional Constraints (Policy)

Require Program Director approval to override. Violations documented as exceptions.

### 2.1 Deployment Blocking Constraint

**Constraint ID:** `MILITARY_DEPLOYMENT`
**Priority:** P1 (Institutional - Absolute)
**Type:** Hard constraint

**Rule:**
Deployed personnel cannot be scheduled for any duties.

**Parameters:**
```python
absence_type = 'DEPLOYMENT'
blocking_type = 'absolute'  # No exceptions
```

**Validation:**
```python
for assignment in all_assignments:
    if has_deployment(assignment.person, assignment.date):
        raise DeploymentViolation("Cannot schedule deployed personnel")
```

**Relaxation:** None (deployment is absolute block)

**Override Authority:** None

**Implementation:**
- File: `backend/app/scheduling/constraints/temporal.py`
- Class: `AbsenceConstraint`

---

### 2.2 FMIT Sequencing Constraint

**Constraint ID:** `FMIT_SEQUENCING`
**Priority:** P1 (Institutional)
**Type:** Hard constraint with override

**Rule:**
All PGY-1 residents must complete FMIT rotation in first 6 months.

**Parameters:**
```python
rotation_name = 'FMIT'
pgy_level = 1
deadline = academic_year_start + timedelta(days=180)  # 6 months
```

**Validation:**
```python
for resident in get_pgy1_residents():
    fmit_assignments = [
        a for a in resident.assignments
        if a.rotation.name == 'FMIT' and a.date <= deadline
    ]

    if not fmit_assignments:
        raise SequencingViolation(f"{resident.name} missing FMIT in first 6 months")
```

**Relaxation:** Extend to month 7 with PD approval

**Override Authority:** Program Director

**Implementation:**
- File: `backend/app/scheduling/constraints/fmit.py`
- Class: `FMITSequencingConstraint`

---

### 2.3 Night Float Post-Call Constraint

**Constraint ID:** `NIGHT_FLOAT_POST_CALL`
**Priority:** P1 (Institutional)
**Type:** Hard constraint

**Rule:**
Post-Call (PC) day required after Night Float rotation.

**Parameters:**
```python
rotation_name = 'Night_Float'
post_call_required = True
pc_day_offset = 1  # Day after NF ends
```

**Validation:**
```python
for nf_assignment in get_nf_assignments(person):
    pc_day = nf_assignment.end_date + timedelta(days=1)

    if has_assignment(person, pc_day):
        raise PostCallViolation(f"PC day required on {pc_day}")
```

**Relaxation:** None (safety requirement)

**Override Authority:** Program Director (rare emergency only)

**Implementation:**
- File: `backend/app/scheduling/constraints/night_float_post_call.py`
- Class: `NightFloatPostCallConstraint`

---

### 2.4 Hard Preference Block Constraint

**Constraint ID:** `HARD_PREFERENCE_BLOCK`
**Priority:** P1 (Institutional)
**Type:** Hard constraint with override

**Rule:**
Approved hard preferences (vacation, family commitments) must be honored.

**Parameters:**
```python
preference_type = 'HARD_BLOCK'
requires_approval = True
override_requires_pd_approval = True
```

**Validation:**
```python
for preference in get_hard_preferences(person):
    if has_assignment(person, preference.date_range):
        raise PreferenceViolation(
            f"Assignment conflicts with approved preference: {preference.reason}"
        )
```

**Relaxation:** Override with PD approval and resident consent

**Override Authority:** Program Director

**Implementation:**
- File: `backend/app/scheduling/constraints/temporal.py`
- Class: `PreferenceConstraint`

---

### 2.5 Minimum Coverage Constraint

**Constraint ID:** `MINIMUM_COVERAGE`
**Priority:** P1 (Institutional)
**Type:** Hard constraint with override

**Rule:**
Each rotation must meet minimum staffing levels.

**Parameters:**
```python
# Varies by rotation
rotation_minimums = {
    'FMIT': 3,
    'Emergency': 3,
    'Clinic': 1,
    'Night_Float': 1,
    'OB': 2
}
```

**Validation:**
```python
for block, rotation in all_assignments:
    coverage = count_assigned(rotation, block)
    minimum = rotation.min_coverage

    if coverage < minimum:
        raise CoverageViolation(
            f"{rotation.name} Block {block}: {coverage} < {minimum} required"
        )
```

**Relaxation:** Reduce minimum with enhanced supervision plan

**Override Authority:** Program Director

**Implementation:**
- File: `backend/app/scheduling/constraints/capacity.py`
- Class: `MinimumCoverageConstraint`

---

### 2.6 Continuity Clinic Constraint

**Constraint ID:** `CONTINUITY_CLINIC`
**Priority:** P1 (Institutional)
**Type:** Hard constraint

**Rule:**
Weekly continuity clinic required (except during inpatient rotations).

**Parameters:**
```python
frequency = 'weekly'
blocking_rotations = ['FMIT', 'IM', 'EM', 'NF', 'L&D']
pgy1_half_days = 1
pgy2_half_days = 1
pgy3_half_days = 2
```

**Validation:**
```python
for week, resident in all_weeks_residents:
    current_rotation = get_rotation(resident, week)

    if current_rotation.name not in blocking_rotations:
        clinic_assignments = count_continuity_clinic(resident, week)
        required = {1: 1, 2: 1, 3: 2}[resident.pgy_level]

        if clinic_assignments < required:
            raise ContinuityViolation(
                f"{resident.name} missing continuity clinic in week {week}"
            )
```

**Relaxation:** Skip week with PD approval (e.g., conference)

**Override Authority:** Program Director

**Implementation:**
- File: `backend/app/scheduling/constraints/temporal.py`
- Class: `ContinuityClinicConstraint`

---

### 2.7 Qualification Constraint

**Constraint ID:** `QUALIFICATION_MATCH`
**Priority:** P1 (Institutional)
**Type:** Hard constraint

**Rule:**
Only assign residents to rotations they are qualified for.

**Parameters:**
```python
# Varies by rotation
required_qualifications = {
    'pgy_level': [1, 2, 3],
    'certifications': ['BLS', 'ACLS'],
    'security_clearance': None
}
```

**Validation:**
```python
for assignment in all_assignments:
    rotation = assignment.rotation
    person = assignment.person

    # Check PGY level
    if person.pgy_level not in rotation.required_pgy_levels:
        raise QualificationViolation("PGY level mismatch")

    # Check certifications
    if not has_certs(person, rotation.required_certs):
        raise QualificationViolation("Missing required certifications")
```

**Relaxation:** None (safety requirement)

**Override Authority:** None

**Implementation:**
- File: `backend/app/scheduling/constraints/base.py`
- Class: `QualificationConstraint`

---

## Tier 3: Optimization Constraints (Preferences)

Best-effort satisfaction. Can be relaxed without approval. Tracked for quality metrics.

### 3.1 Fairness (Workload Equity) Constraint

**Constraint ID:** `WORKLOAD_EQUITY`
**Priority:** P2 (Optimization)
**Type:** Soft constraint with penalty

**Rule:**
Distribute workload evenly (Gini coefficient <0.15).

**Parameters:**
```python
target_gini = 0.15
max_acceptable_gini = 0.20
penalty_per_0.01_over = 10
```

**Validation:**
```python
workloads = [count_hours(r) for r in residents]
gini = calculate_gini(workloads)

if gini > 0.15:
    penalty = (gini - 0.15) * 1000  # Soft penalty
    warnings.append(f"Fairness suboptimal: Gini={gini:.2f}")
```

**Relaxation:** Accept up to Gini=0.20

**Override Authority:** None (optimization goal)

**Implementation:**
- File: `backend/app/scheduling/constraints/equity.py`
- Class: `WorkloadEquityConstraint`

---

### 3.2 Call Equity Constraint

**Constraint ID:** `CALL_EQUITY`
**Priority:** P2 (Optimization)
**Type:** Soft constraint with penalty

**Rule:**
Distribute call shifts fairly among residents.

**Parameters:**
```python
target_gini = 0.10
include_weekend_call = True
include_holiday_call = True
weight_holiday = 1.5  # Holidays count more
```

**Validation:**
```python
call_counts = {}
for resident in residents:
    call_counts[resident] = (
        count_weekday_call(resident) +
        count_weekend_call(resident) +
        1.5 * count_holiday_call(resident)
    )

gini = calculate_gini(list(call_counts.values()))

if gini > 0.10:
    penalty = (gini - 0.10) * 500
```

**Relaxation:** Accept up to Gini=0.15

**Override Authority:** Chief Resident

**Implementation:**
- File: `backend/app/scheduling/constraints/call_equity.py`
- Class: `CallEquityConstraint`

---

### 3.3 Shift Preference Constraint

**Constraint ID:** `SHIFT_PREFERENCE`
**Priority:** P2 (Optimization)
**Type:** Soft constraint with penalty

**Rule:**
Honor resident preferences for shift times (AM/PM).

**Parameters:**
```python
preference_types = ['AM_PREFERRED', 'PM_PREFERRED', 'NO_PREFERENCE']
satisfaction_weight = 0.20  # In objective function
penalty_per_violation = 5
```

**Validation:**
```python
for assignment in all_assignments:
    pref = get_preference(assignment.person, 'shift_time')

    if pref == 'AM_PREFERRED' and assignment.session == 'PM':
        penalty += 5
    elif pref == 'PM_PREFERRED' and assignment.session == 'AM':
        penalty += 5
```

**Relaxation:** Reduce weight in objective function

**Override Authority:** None (optimization goal)

**Implementation:**
- File: `backend/app/scheduling/constraints/temporal.py`
- Class: `ShiftPreferenceConstraint`

---

### 3.4 Rotation Preference Constraint

**Constraint ID:** `ROTATION_PREFERENCE`
**Priority:** P2 (Optimization)
**Type:** Soft constraint with penalty

**Rule:**
Assign residents to preferred rotations when possible.

**Parameters:**
```python
preference_levels = {
    'HIGHLY_DESIRED': +10,
    'PREFERRED': +5,
    'NEUTRAL': 0,
    'NOT_PREFERRED': -5,
    'AVOID': -10
}
satisfaction_weight = 0.20
```

**Validation:**
```python
satisfaction_score = 0

for assignment in all_assignments:
    pref_level = get_rotation_preference(assignment.person, assignment.rotation)
    satisfaction_score += preference_levels[pref_level]

preference_satisfaction = satisfaction_score / max_possible_score
```

**Relaxation:** Reduce weight or ignore for specific rotations

**Override Authority:** None (optimization goal)

**Implementation:**
- File: `backend/app/scheduling/constraints/temporal.py`
- Class: `RotationPreferenceConstraint`

---

### 3.5 Continuity (Minimize Handoffs) Constraint

**Constraint ID:** `CONTINUITY`
**Priority:** P2 (Optimization)
**Type:** Soft constraint with penalty

**Rule:**
Minimize transitions and handoffs.

**Parameters:**
```python
penalty_per_handoff = 3
prefer_consecutive_weeks = True
prefer_same_team = True
```

**Validation:**
```python
handoff_count = 0

for resident in residents:
    rotations = get_rotations_chronological(resident)

    for i in range(len(rotations) - 1):
        if rotations[i] != rotations[i+1]:
            handoff_count += 1

penalty = handoff_count * 3
```

**Relaxation:** Accept more handoffs (reduce penalty weight)

**Override Authority:** None (optimization goal)

**Implementation:**
- File: `backend/app/scheduling/constraints/temporal.py`
- Class: `ContinuityConstraint`

---

### 3.6 Efficiency (Minimize Gaps) Constraint

**Constraint ID:** `EFFICIENCY`
**Priority:** P2 (Optimization)
**Type:** Soft constraint with penalty

**Rule:**
Minimize gaps and fragmentation in schedules.

**Parameters:**
```python
penalty_per_gap_day = 2
prefer_contiguous_blocks = True
```

**Validation:**
```python
gap_count = 0

for resident in residents:
    assignments = get_assignments_chronological(resident)

    for i in range(len(assignments) - 1):
        gap_days = (assignments[i+1].start_date - assignments[i].end_date).days - 1

        if gap_days > 0:
            gap_count += gap_days

penalty = gap_count * 2
```

**Relaxation:** Accept some fragmentation (reduce penalty)

**Override Authority:** None (optimization goal)

**Implementation:**
- File: `backend/app/scheduling/constraints/temporal.py`
- Class: `EfficiencyConstraint`

---

### 3.7 Resilience (80% Utilization) Constraint

**Constraint ID:** `RESILIENCE_UTILIZATION`
**Priority:** P2 (Optimization)
**Type:** Soft constraint with penalty

**Rule:**
Maintain slack capacity (max 80% utilization).

**Parameters:**
```python
max_utilization = 0.80
penalty_per_percent_over = 20
```

**Validation:**
```python
for person in all_people:
    capacity = calculate_max_capacity(person)  # e.g., 80 hours/week
    scheduled = calculate_scheduled_hours(person)
    utilization = scheduled / capacity

    if utilization > 0.80:
        penalty += (utilization - 0.80) * 100 * 20  # 20 per percent over
        warnings.append(f"{person.name} at {utilization:.0%} utilization")
```

**Relaxation:** Accept up to 85% utilization

**Override Authority:** None (optimization goal)

**Implementation:**
- File: `backend/app/scheduling/constraints/resilience.py`
- Class: `UtilizationConstraint`

---

## Constraint Interaction Matrix

Some constraints interact or conflict. This matrix shows compatibility:

| Constraint | Conflicts With | Notes |
|------------|----------------|-------|
| 80-Hour Rule | Minimum Coverage | May need to reduce coverage if hours approaching limit |
| 1-in-7 Rule | Call Equity | Ensure fair call doesn't violate days off |
| Hard Preference | Coverage | Vacation may conflict with coverage needs |
| Continuity Clinic | FMIT Rotation | Clinic paused during inpatient rotations |
| Fairness | Preferences | Fair distribution may conflict with individual preferences |
| Night Float Limit | Coverage | Maximum 6 nights may limit NF coverage options |

---

## Constraint Relaxation Strategy

When constraints conflict, relax in this order:

1. **First:** Relax Tier 3 optimization constraints
   - Reduce fairness target (0.15 → 0.20 Gini)
   - Reduce preference satisfaction target (80% → 75%)
   - Accept more fragmentation

2. **Second:** Adjust Tier 2 institutional constraints with approval
   - Request coverage reduction (with safety plan)
   - Request FMIT deadline extension (1 month max)
   - Request preference override (with resident consent)

3. **Never:** Relax Tier 1 ACGME constraints
   - These are non-negotiable
   - If ACGME constraints cannot be met, problem is infeasible
   - Must add resources or reduce requirements

---

## Implementation Reference

### Constraint System Architecture

**Base Class:**
```python
# backend/app/scheduling/constraints/base.py
class BaseConstraint:
    tier: int  # 1=ACGME, 2=Institutional, 3=Optimization
    priority: int  # 0-2 (lower = higher priority)
    type: str  # 'hard' or 'soft'

    def validate(self, assignments) -> List[Violation]:
        """Check constraint, return violations."""
        pass

    def apply(self, model) -> None:
        """Apply constraint to solver model."""
        pass

    def penalty(self, assignments) -> float:
        """Calculate soft constraint penalty."""
        pass
```

**Constraint Manager:**
```python
# backend/app/scheduling/constraints/manager.py
class ConstraintManager:
    def __init__(self):
        self.constraints = []

    def register(self, constraint):
        """Register a constraint."""
        self.constraints.append(constraint)

    def validate_all(self, assignments):
        """Run all constraints, collect violations."""
        violations = []
        for constraint in sorted(self.constraints, key=lambda c: c.priority):
            violations.extend(constraint.validate(assignments))
        return violations

    def get_by_tier(self, tier):
        """Get constraints by tier."""
        return [c for c in self.constraints if c.tier == tier]
```

### Constraint Files

| Constraint Category | File | Classes |
|--------------------|----- |---------|
| ACGME Rules | `acgme.py` | `WorkHourConstraint`, `DaysOffConstraint`, `SupervisionRatioConstraint` |
| Availability | `temporal.py` | `AbsenceConstraint`, `PreferenceConstraint` |
| Coverage | `capacity.py` | `MinimumCoverageConstraint`, `MaximumCoverageConstraint` |
| Equity | `equity.py` | `WorkloadEquityConstraint` |
| Call Equity | `call_equity.py` | `CallEquityConstraint` |
| Resilience | `resilience.py` | `UtilizationConstraint`, `N1ContingencyConstraint` |
| FMIT Specific | `fmit.py` | `FMITSequencingConstraint` |
| NF Specific | `night_float_post_call.py` | `NightFloatPostCallConstraint` |
| Inpatient | `inpatient.py` | `InpatientConstraint` |
| Faculty | `faculty.py` | `FacultyAvailabilityConstraint` |

---

## Quick Reference: Constraint Priorities

**When constraints conflict, follow this priority order:**

1. ACGME 80-Hour (cannot violate)
2. ACGME 1-in-7 (cannot violate)
3. ACGME Supervision (cannot violate)
4. ACGME Duty Period (cannot violate)
5. Deployment Blocking (cannot violate)
6. Minimum Coverage (can reduce with PD approval)
7. FMIT Sequencing (can extend 1 month with PD approval)
8. Hard Preferences (can override with PD approval + resident consent)
9. Continuity Clinic (can skip with PD approval)
10. Fairness (can relax to Gini=0.20)
11. Call Equity (can relax to Gini=0.15)
12. Preferences (can ignore if necessary)
13. Continuity (can accept more handoffs)
14. Efficiency (can accept fragmentation)

---

## See Also

- `Reference/acgme-rules.md` - Detailed ACGME requirements
- `Reference/institutional-rules.md` - Detailed institutional policies
- `Workflows/constraint-propagation.md` - How constraints are applied
- `Workflows/conflict-resolution.md` - Handling constraint conflicts
- `backend/app/scheduling/constraints/` - Implementation code

---

**Document Version:** 1.0
**Last Updated:** December 2025
**Maintained By:** Technical Team + Program Coordinator
**Review Frequency:** When constraints change or new rules added
