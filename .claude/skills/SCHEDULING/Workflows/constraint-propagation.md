# Constraint Propagation Workflow

Systematic approach to applying scheduling constraints to reduce search space and identify infeasibility early.

---

## Overview

Constraint propagation is the process of applying scheduling rules systematically to:
1. **Reduce search space** - Eliminate invalid assignments before optimization
2. **Detect infeasibility early** - Identify impossible configurations before solver runs
3. **Improve solver performance** - Smaller search space = faster solutions
4. **Provide diagnostics** - Explain why certain schedules are impossible

**Key Principle:** Apply strongest constraints first (ACGME → Availability → Qualifications → Preferences)

---

## Constraint Hierarchy

### Tier 1: Absolute Constraints (ACGME Regulatory)
**Priority:** P0 - Must be satisfied, non-negotiable
**Failure Impact:** Schedule is invalid, cannot be deployed

| Constraint | Rule | Validation Method |
|------------|------|-------------------|
| 80-Hour Rule | Max 80 hours/week averaged over 4 weeks | `validate_work_hours()` |
| 1-in-7 Rule | One 24-hour off period every 7 days | `validate_days_off()` |
| Supervision PGY-1 | Max 2 PGY-1 per 1 faculty | `validate_supervision_ratios()` |
| Supervision PGY-2/3 | Max 4 PGY-2/3 per 1 faculty | `validate_supervision_ratios()` |
| Duty Period Limit | Max 24 hours standard shift | `validate_duty_periods()` |
| Night Float Limit | Max 6 consecutive nights | `validate_night_float()` |

**See:** `Reference/acgme-rules.md` for complete ACGME constraints

### Tier 2: Institutional Constraints (Policy-Based)
**Priority:** P1 - Should be satisfied, requires approval to override
**Failure Impact:** Policy exception needed, documented rationale required

| Constraint | Rule | Override Authority |
|------------|------|-------------------|
| Deployment Blocking | Military deployment = unavailable | None (absolute) |
| FMIT Sequencing | PGY-1 must do FMIT in first 6 months | Program Director |
| Night Float Pattern | Mirrored half-block pairing | Curriculum Committee |
| Post-Call Relief | PC day after NF rotation | Chief Resident |
| Continuity Clinic | Weekly continuity requirement | Program Director |
| Holiday Rotation | Fair holiday coverage distribution | Program Coordinator |

**See:** `Reference/institutional-rules.md` for complete institutional constraints

### Tier 3: Optimization Constraints (Preferences)
**Priority:** P2 - Best-effort satisfaction, can be relaxed
**Failure Impact:** Lower satisfaction score, no approval needed

| Constraint | Goal | Relaxation Method |
|------------|------|-------------------|
| Fairness | Gini coefficient <0.15 | Increase threshold to 0.20 |
| Shift Preference | Honor AM/PM preferences | Reduce weight in objective |
| Rotation Preference | Assign preferred rotations | Reduce weight in objective |
| Team Continuity | Minimize handoffs | Allow more transitions |
| Efficiency | Minimize schedule gaps | Accept some fragmentation |

---

## Propagation Algorithm

### Step 1: Gather All Constraints

**From ACGME rules:**
```python
acgme_constraints = [
    WorkHourConstraint(max_hours=80, rolling_weeks=4),
    DaysOffConstraint(min_per_week=1),
    SupervisionConstraint(pgy1_ratio=2, pgy23_ratio=4),
    DutyPeriodConstraint(max_hours=24),
    NightFloatConstraint(max_consecutive=6)
]
```

**From absences database:**
```python
# Query absences in scheduling horizon
absences = db.query(Absence).filter(
    Absence.start_date >= schedule_start,
    Absence.end_date <= schedule_end
).all()

# Create blocking constraints
for absence in absences:
    if absence.type in ['DEPLOYMENT', 'EXTENDED_LEAVE']:
        # Complete block - person cannot be assigned
        blocking_constraints.append(
            BlockingConstraint(person=absence.person, dates=absence.date_range)
        )
    elif absence.type in ['CONFERENCE', 'VACATION']:
        # Partial block - reduces capacity but may allow some assignments
        capacity_constraints.append(
            CapacityReductionConstraint(person=absence.person, dates=absence.date_range)
        )
```

**From rotation templates:**
```python
# Each template defines required qualifications
for template in rotation_templates:
    qualification_constraints.append(
        QualificationConstraint(
            rotation=template.name,
            required_pgy=template.pgy_levels,
            required_certs=template.certifications,
            min_coverage=template.min_coverage,
            max_coverage=template.max_coverage
        )
    )
```

**From preferences:**
```python
# Preferences become soft constraints with penalties
for pref in preferences:
    if pref.type == 'HARD_BLOCK':
        # Treat as Tier 2 constraint
        hard_constraints.append(
            PreferenceBlockConstraint(person=pref.person, dates=pref.dates)
        )
    else:
        # Soft constraint with penalty
        soft_constraints.append(
            PreferenceSoftConstraint(person=pref.person, details=pref.details, weight=pref.priority)
        )
```

### Step 2: Build Availability Matrix

**Create person × block availability table:**

```python
from collections import defaultdict
from datetime import timedelta

def build_availability_matrix(people, blocks, absences):
    """
    Create matrix of {person_id: {block_id: availability_status}}

    Availability status:
    - AVAILABLE: Can be assigned
    - BLOCKED: Cannot be assigned (deployment, extended leave)
    - REDUCED: Partially available (conference, vacation)
    """
    matrix = defaultdict(dict)

    for person in people:
        for block in blocks:
            # Default to available
            matrix[person.id][block.id] = "AVAILABLE"

            # Check for blocking absences
            for absence in absences:
                if absence.person_id != person.id:
                    continue

                # Check if absence overlaps block
                if overlaps(absence.date_range, block.date_range):
                    if absence.type in ['DEPLOYMENT', 'EXTENDED_LEAVE']:
                        matrix[person.id][block.id] = "BLOCKED"
                        break  # Blocked is strongest status
                    elif absence.type in ['CONFERENCE', 'VACATION']:
                        # Only reduce if not already blocked
                        if matrix[person.id][block.id] != "BLOCKED":
                            matrix[person.id][block.id] = "REDUCED"

    return matrix


def overlaps(range1, range2):
    """Check if two date ranges overlap."""
    return not (range1['end'] < range2['start'] or range2['end'] < range1['start'])
```

**Identify coverage risks:**

```python
def check_coverage_risks(availability_matrix, rotation_templates):
    """Find blocks where coverage requirements may not be met."""
    risks = []

    for rotation in rotation_templates:
        for block in blocks:
            # Count available people for this rotation
            available_count = sum(
                1 for person in people
                if availability_matrix[person.id][block.id] == "AVAILABLE"
                and person.pgy_level in rotation.required_pgy_levels
            )

            if available_count < rotation.min_coverage:
                risks.append({
                    'rotation': rotation.name,
                    'block': block.id,
                    'required': rotation.min_coverage,
                    'available': available_count,
                    'severity': 'HIGH' if available_count == 0 else 'MEDIUM'
                })

    return risks
```

### Step 3: Apply Domain Reduction

**Eliminate impossible assignments:**

```python
def reduce_domains(people, blocks, rotation_templates, availability_matrix):
    """
    For each (person, block, rotation) triple, determine if assignment is possible.
    Returns: {(person_id, block_id): [valid_rotation_ids]}
    """
    valid_assignments = defaultdict(list)

    for person in people:
        for block in blocks:
            # Skip if person unavailable
            if availability_matrix[person.id][block.id] == "BLOCKED":
                continue

            for rotation in rotation_templates:
                # Check PGY level qualification
                if person.pgy_level not in rotation.required_pgy_levels:
                    continue

                # Check certifications
                if not has_required_certs(person, rotation):
                    continue

                # Check activity type restrictions
                if not can_do_activity_type(person, rotation.activity_type):
                    continue

                # Valid assignment
                valid_assignments[(person.id, block.id)].append(rotation.id)

    return valid_assignments


def has_required_certs(person, rotation):
    """Check if person has all required certifications."""
    required = set(rotation.required_certifications or [])
    person_certs = set(c.type for c in person.certifications if c.is_valid())
    return required.issubset(person_certs)


def can_do_activity_type(person, activity_type):
    """Check if person can do this type of rotation."""
    # Example restrictions
    if activity_type == 'night_float' and person.pgy_level == 1:
        # Policy: PGY-1 cannot do solo night float
        return False
    return True
```

### Step 4: Constraint Propagation Iterations

**Iteratively narrow domains until fixpoint:**

```python
def propagate_constraints(valid_assignments, constraints, max_iterations=10):
    """
    Apply constraints iteratively until no more reductions possible.

    Algorithm:
    1. For each constraint, eliminate assignments that violate it
    2. If any domain becomes empty, problem is infeasible
    3. Repeat until no changes (fixpoint) or max iterations
    """
    iteration = 0
    changed = True

    while changed and iteration < max_iterations:
        changed = False
        iteration += 1

        for constraint in constraints:
            # Apply constraint and get eliminated assignments
            eliminations = constraint.propagate(valid_assignments)

            if eliminations:
                changed = True
                for (person_id, block_id, rotation_id) in eliminations:
                    if rotation_id in valid_assignments[(person_id, block_id)]:
                        valid_assignments[(person_id, block_id)].remove(rotation_id)

                        # Check if domain became empty
                        if not valid_assignments[(person_id, block_id)]:
                            raise InfeasibleScheduleError(
                                f"No valid rotations for person {person_id} in block {block_id}"
                            )

        print(f"Iteration {iteration}: {'Changes made' if changed else 'Fixpoint reached'}")

    return valid_assignments
```

**Example constraint propagation:**

```python
class WorkHourConstraint:
    """80-hour work hour limit constraint."""

    def propagate(self, valid_assignments):
        """Eliminate assignments that would violate work hour limits."""
        eliminations = []

        for person_id in people:
            # Calculate current work hours by week
            weekly_hours = calculate_weekly_hours(person_id, current_assignments)

            for week in weeks:
                if weekly_hours[week] > 60:  # Getting close to limit
                    # Eliminate high-hour rotations in this week
                    for block in blocks_in_week(week):
                        for rotation_id in valid_assignments[(person_id, block.id)]:
                            rotation = get_rotation(rotation_id)
                            if rotation.weekly_hours > 10:  # Would push over limit
                                eliminations.append((person_id, block.id, rotation_id))

        return eliminations
```

### Step 5: Detect Conflicts

**Identify constraint conflicts:**

```python
def detect_conflicts(constraints):
    """Find pairs of constraints that cannot both be satisfied."""
    conflicts = []

    for i, c1 in enumerate(constraints):
        for c2 in constraints[i+1:]:
            if are_conflicting(c1, c2):
                conflicts.append({
                    'constraint1': c1,
                    'constraint2': c2,
                    'explanation': explain_conflict(c1, c2),
                    'severity': classify_severity(c1, c2)
                })

    return conflicts


def are_conflicting(c1, c2):
    """Check if two constraints conflict."""
    # Example: Hard block preference conflicts with coverage requirement
    if isinstance(c1, PreferenceBlockConstraint) and isinstance(c2, CoverageConstraint):
        if c1.person_id in c2.required_people and overlaps(c1.dates, c2.dates):
            return True
    return False


def classify_severity(c1, c2):
    """Determine conflict severity based on constraint tiers."""
    tier_map = {
        'ACGMEConstraint': 1,
        'InstitutionalConstraint': 2,
        'PreferenceConstraint': 3
    }

    tier1 = tier_map.get(type(c1).__name__, 3)
    tier2 = tier_map.get(type(c2).__name__, 3)

    if tier1 == 1 or tier2 == 1:
        return 'CRITICAL'  # ACGME conflict
    elif tier1 == 2 or tier2 == 2:
        return 'HIGH'      # Institutional conflict
    else:
        return 'MEDIUM'    # Preference conflict
```

---

## Backtracking Strategies

### When to Backtrack

**Backtracking is needed when:**
1. Domain becomes empty (no valid assignments for some person/block)
2. Constraint conflict detected
3. Coverage requirement cannot be met
4. Solver times out or fails

### Backtracking Approaches

#### 1. Constraint Relaxation

**Relax weakest constraints first (Tier 3, then Tier 2):**

```python
def backtrack_with_relaxation(constraints, valid_assignments):
    """Progressively relax constraints until feasible."""

    # Try with all constraints
    try:
        result = propagate_constraints(valid_assignments, constraints)
        return result
    except InfeasibleScheduleError as e:
        print(f"Infeasible with all constraints: {e}")

    # Remove Tier 3 constraints and retry
    tier12_constraints = [c for c in constraints if c.tier <= 2]
    try:
        result = propagate_constraints(valid_assignments, tier12_constraints)
        print("SUCCESS: Feasible after relaxing Tier 3 (preferences)")
        return result
    except InfeasibleScheduleError as e:
        print(f"Still infeasible: {e}")

    # Remove some Tier 2 constraints (requires approval)
    critical_constraints = [c for c in constraints if c.tier == 1]
    try:
        result = propagate_constraints(valid_assignments, critical_constraints)
        print("WARNING: Only feasible with Tier 1 (ACGME) constraints. Requires PD approval.")
        return result
    except InfeasibleScheduleError as e:
        print(f"CRITICAL: Infeasible even with only ACGME constraints: {e}")
        raise
```

#### 2. Coverage Adjustment

**Reduce coverage requirements:**

```python
def backtrack_with_coverage_reduction(rotation_templates):
    """Try reducing coverage requirements to find feasible solution."""

    for rotation in rotation_templates:
        original_min = rotation.min_coverage

        # Try reducing by 1
        rotation.min_coverage = original_min - 1
        try:
            result = propagate_constraints(valid_assignments, constraints)
            print(f"Feasible with {rotation.name} coverage reduced from {original_min} to {rotation.min_coverage}")
            return result
        except InfeasibleScheduleError:
            # Restore and try next rotation
            rotation.min_coverage = original_min
            continue

    raise InfeasibleScheduleError("Cannot find feasible solution even with reduced coverage")
```

#### 3. Temporal Decomposition

**Break problem into smaller time windows:**

```python
def backtrack_with_decomposition(blocks, constraints):
    """Generate schedule in smaller chunks instead of all at once."""

    # Divide into quarters (13 weeks / 4 = ~3-4 blocks each)
    quarters = divide_into_quarters(blocks)

    all_assignments = []

    for quarter_num, quarter_blocks in enumerate(quarters):
        print(f"Generating Q{quarter_num + 1} schedule...")

        # Use previous quarter's end state as starting point
        context = build_context_from_previous(all_assignments[-1] if all_assignments else None)

        try:
            quarter_assignments = propagate_and_solve(quarter_blocks, constraints, context)
            all_assignments.extend(quarter_assignments)
        except InfeasibleScheduleError as e:
            print(f"Q{quarter_num + 1} failed: {e}")
            # Try relaxing constraints for this quarter only
            quarter_assignments = propagate_and_solve(
                quarter_blocks,
                relax_constraints(constraints),
                context
            )
            all_assignments.extend(quarter_assignments)

    return all_assignments
```

---

## Conflict Detection

### Types of Conflicts

#### 1. Hard Conflicts (Cannot Both Be True)

**Example: Deployment vs. Coverage Requirement**

```python
# Person A is deployed (unavailable)
deployment_constraint = BlockingConstraint(
    person='PGY2-01',
    dates='2026-03-01 to 2026-03-28'
)

# But coverage requires Person A for critical rotation
coverage_constraint = RequiredPersonConstraint(
    rotation='Emergency Medicine',
    required_person='PGY2-01',
    dates='2026-03-01 to 2026-03-28'
)

# CONFLICT: Person cannot be both unavailable and required
```

**Resolution:**
- Find substitute for Person A
- Reduce coverage requirement
- Reschedule rotation to different block

#### 2. Soft Conflicts (Can Coexist But Suboptimal)

**Example: Preference vs. Fairness**

```python
# Resident prefers AM shifts
preference_constraint = ShiftPreferenceConstraint(
    person='PGY1-05',
    preferred_session='AM'
)

# But fairness requires PM shift to balance workload
fairness_constraint = EquityConstraint(
    person='PGY1-05',
    recommended_session='PM',
    reason='Already has 8 AM shifts, cohort average is 5'
)

# SOFT CONFLICT: Can assign PM but violates preference
```

**Resolution:**
- Accept lower preference satisfaction
- Find another resident to take PM shift
- Adjust fairness threshold

#### 3. Cascading Conflicts (One Violation Causes Others)

**Example: Post-Call Violation Chain**

```python
# Resident does 24-hour call on Friday
call_assignment = Assignment(
    person='PGY3-02',
    rotation='Inpatient Call',
    date='2026-03-15',  # Friday
    session='24-hour'
)

# Post-call constraint requires Saturday off
post_call_constraint = PostCallReliefConstraint(
    person='PGY3-02',
    required_off_date='2026-03-16'  # Saturday
)

# But coverage requires this person Saturday
weekend_coverage = CoverageConstraint(
    rotation='Weekend Clinic',
    required_people=['PGY3-02'],
    date='2026-03-16'
)

# And they're scheduled for clinic Sunday
sunday_assignment = Assignment(
    person='PGY3-02',
    rotation='Continuity Clinic',
    date='2026-03-17',  # Sunday
    session='AM'
)

# CASCADING: Post-call violation + 1-in-7 violation (no day off in 7 days)
```

**Resolution:**
- Move call to Thursday (gives Friday/Saturday off)
- Find substitute for Saturday coverage
- Reschedule Sunday clinic

### Conflict Detection Algorithm

```python
def detect_all_conflicts(assignments, constraints):
    """Comprehensive conflict detection."""

    conflicts = {
        'hard': [],      # Must be resolved
        'soft': [],      # Should be resolved
        'cascading': []  # Chain reactions
    }

    # Check each constraint against current assignments
    for constraint in constraints:
        violations = constraint.find_violations(assignments)

        for violation in violations:
            conflict = {
                'constraint': constraint,
                'violation': violation,
                'affected_people': violation.people,
                'affected_dates': violation.dates,
                'severity': constraint.tier
            }

            # Classify conflict type
            if constraint.tier == 1:  # ACGME
                conflicts['hard'].append(conflict)
            elif constraint.tier == 2:  # Institutional
                # Check if it triggers cascade
                if triggers_cascade(conflict, constraints):
                    conflicts['cascading'].append(conflict)
                else:
                    conflicts['hard'].append(conflict)
            else:  # Preference
                conflicts['soft'].append(conflict)

    # Identify conflict chains
    conflicts['cascading'].extend(find_conflict_chains(conflicts['hard']))

    return conflicts


def triggers_cascade(conflict, all_constraints):
    """Check if resolving this conflict violates other constraints."""
    # Simulate removing the conflicting assignment
    test_assignments = remove_assignment(conflict.violation.assignment)

    # Check if this creates new violations
    new_violations = []
    for constraint in all_constraints:
        if constraint != conflict.constraint:
            new_violations.extend(constraint.find_violations(test_assignments))

    return len(new_violations) > 0
```

---

## Propagation Performance

### Complexity Analysis

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Build Availability Matrix | O(P × B × A) | P=people, B=blocks, A=absences |
| Domain Reduction | O(P × B × R × C) | R=rotations, C=certifications |
| Constraint Propagation | O(I × C × A) | I=iterations, C=constraints, A=assignments |
| Conflict Detection | O(C × A) | Check each constraint against assignments |

**For typical academic year:**
- People: 24 residents + 12 faculty = 36
- Blocks: 13 (4-week blocks)
- Rotations: 18 templates
- Absences: ~50
- Constraints: ~20 active

**Expected Runtime:** <1 second for propagation phase

### Optimization Tips

**1. Cache constraint checks:**
```python
from functools import lru_cache

@lru_cache(maxsize=10000)
def check_qualification(person_id, rotation_id):
    """Cached qualification check."""
    # Expensive database lookup cached
    pass
```

**2. Index data structures:**
```python
# Index absences by person for O(1) lookup
absences_by_person = defaultdict(list)
for absence in absences:
    absences_by_person[absence.person_id].append(absence)
```

**3. Early termination:**
```python
def propagate_constraints(valid_assignments, constraints):
    for constraint in sorted(constraints, key=lambda c: c.selectivity, reverse=True):
        # Apply most selective constraints first
        # Stop if domain becomes empty
        if not valid_assignments:
            break
```

---

## Diagnostic Output

### Propagation Report Format

```
=== CONSTRAINT PROPAGATION REPORT ===

Input:
  - People: 36 (24 residents, 12 faculty)
  - Blocks: 13
  - Rotations: 18
  - Initial assignments possible: 8,424

Phase 1: Availability Matrix
  - Blocking absences: 12 (deployments, extended leave)
  - Reduced availability: 38 (conferences, vacation)
  - Assignments eliminated: 1,248
  - Remaining possible: 7,176

Phase 2: Domain Reduction
  - PGY level mismatches eliminated: 2,340
  - Certification mismatches eliminated: 624
  - Activity type restrictions: 156
  - Remaining possible: 4,056

Phase 3: Constraint Propagation (3 iterations)
  - Iteration 1: 412 assignments eliminated (ACGME constraints)
  - Iteration 2: 89 assignments eliminated (supervision ratios)
  - Iteration 3: 0 assignments eliminated (fixpoint reached)
  - Remaining possible: 3,555

Coverage Risk Assessment:
  ⚠ Block 5: Night Float (2 available, 1 required) - LOW RISK
  ⚠ Block 9: Emergency (3 available, 3 required) - MEDIUM RISK
  ✓ All other rotations: Adequate coverage

Conflicts Detected: 2
  - SOFT: Resident PGY1-03 preference for AM conflicts with fairness
  - SOFT: Resident PGY2-05 vacation overlaps continuity clinic

Feasibility: YES (with 2 soft conflicts)
Recommendation: Proceed to optimization phase
```

---

## See Also

- `Workflows/generate-schedule.md` - Complete workflow including propagation
- `Workflows/conflict-resolution.md` - How to resolve detected conflicts
- `Reference/constraint-index.md` - All constraints with priorities
- `Reference/acgme-rules.md` - ACGME constraint details
