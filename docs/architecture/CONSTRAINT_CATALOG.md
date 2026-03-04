# Constraint Catalog - Residency Scheduler

**Version:** 2.0
**Last Updated:** 2025-12-31
**Purpose:** Complete reference guide for all scheduling constraints

## Table of Contents

1. [Overview](#overview)
2. [Quick Reference](#quick-reference)
3. [Hard Constraints](#hard-constraints)
4. [Soft Constraints](#soft-constraints)
5. [Constraint Priorities](#constraint-priorities)
6. [Constraint Types](#constraint-types)
7. [Constraint Conflicts Matrix](#constraint-conflicts-matrix)
8. [Parameter Reference](#parameter-reference)
9. [Examples](#examples)
10. [Testing Guide](#testing-guide)
11. [Debugging Guide](#debugging-guide)
12. [Relaxation Rules](#relaxation-rules)
13. [Performance Tuning](#performance-tuning)

---

## Overview

The constraint system in the Residency Scheduler consists of:

- **47 Constraint Classes** organized into 18 modules
- **Hard Constraints (27)**: Must be satisfied; violations make schedule infeasible
- **Soft Constraints (20)**: Optimization objectives; violations add penalty to objective
- **Base Classes**: `Constraint`, `HardConstraint`, `SoftConstraint`, `SchedulingContext`
- **Manager**: `ConstraintManager` for orchestrating constraint application

### Core Architecture

```
Constraint (Abstract)
├── HardConstraint
│   ├── ACGME Constraints (4)
│   ├── Capacity Constraints (4)
│   ├── Call Constraints (3)
│   ├── FMIT Constraints (5)
│   ├── Temporal Constraints (3)
│   ├── Availability Constraints (2)
│   └── Other (2)
├── SoftConstraint
│   ├── Equity Constraints (5)
│   ├── Resilience Constraints (4)
│   ├── Preference Constraints (3)
│   ├── Coverage Constraints (2)
│   ├── Call Equity Constraints (4)
│   └── Faculty Constraints (2)
```

---

## Quick Reference

| Name | Type | Category | Priority | Weight | File |
|------|------|----------|----------|--------|------|
| **Availability** | Hard | ACGME | CRITICAL | - | acgme.py |
| **EightyHourRule** | Hard | ACGME | CRITICAL | - | acgme.py |
| **OneInSevenRule** | Hard | ACGME | CRITICAL | - | acgme.py |
| **SupervisionRatio** | Hard | ACGME | CRITICAL | - | acgme.py |
| **OnePersonPerBlock** | Hard | Capacity | HIGH | - | capacity.py |
| **ClinicCapacity** | Hard | Capacity | HIGH | - | capacity.py |
| **MaxPhysiciansInClinic** | Hard | Capacity | HIGH | - | capacity.py |
| **CoverageConstraint** | Soft | Coverage | HIGH | 1.0 | capacity.py |
| **PostCallAutoAssignment** | Hard | Call | CRITICAL | - | post_call.py |
| **NightFloatPostCall** | Hard | Call | HIGH | - | night_float_post_call.py |
| **OvernightCallCoverage** | Hard | Call | HIGH | - | call_coverage.py |
| **OvernightCallGeneration** | Hard | Call | HIGH | - | overnight_call.py |
| **CallAvailability** | Hard | Call | HIGH | - | call_coverage.py |
| **AdjunctCallExclusion** | Hard | Call | CRITICAL | - | call_coverage.py |
| **FacultyDayAvailability** | Hard | Faculty | HIGH | - | primary_duty.py |
| **FacultyPrimaryDutyClinic** | Hard | Faculty | HIGH | - | primary_duty.py |
| **FacultyRoleClinic** | Hard | Faculty | HIGH | - | faculty_role.py |
| **SMFacultyClinic** | Hard | Faculty | HIGH | - | faculty_role.py |
| **EquityConstraint** | Soft | Equity | MEDIUM | 2.0 | equity.py |
| **ContinuityConstraint** | Soft | Equity | MEDIUM | 1.5 | equity.py |
| **PreferenceConstraint** | Soft | Preference | MEDIUM | 1.0 | faculty.py |
| **HubProtection** | Soft | Resilience | MEDIUM | 1.5 | resilience.py |
| **UtilizationBuffer** | Soft | Resilience | HIGH | 2.0 | resilience.py |
| **N1Vulnerability** | Soft | Resilience | HIGH | 2.5 | resilience.py |
| **PreferenceTrail** | Soft | Resilience | LOW | 0.5 | resilience.py |
| **ZoneBoundary** | Soft | Resilience | MEDIUM | 1.0 | resilience.py |
| **FMIT Constraints** | Hard | FMIT | HIGH | - | fmit.py |
| **Call Equity Constraints** | Soft | Call Equity | MEDIUM | 1.0-2.0 | call_equity.py |
| **Temporal Constraints** | Hard | Temporal | HIGH | - | temporal.py |
| **Inpatient Constraints** | Hard | Inpatient | HIGH | - | inpatient.py |
| **Sports Medicine Constraints** | Hard | Sports Med | HIGH | - | sports_medicine.py |

---

## Hard Constraints

### ACGME Compliance (acgme.py)

#### 1. Availability Constraint
**Type:** `AVAILABILITY` | **Priority:** `CRITICAL` | **Module:** `acgme.py`

Ensures residents and faculty are only assigned during periods when available.

**Validation Logic:**
```python
for assignment in assignments:
    if assignment.person_id in context.availability:
        if not context.availability[person_id][block_id]["available"]:
            violation()  # Mark unavailable assignment as violation
```

**Parameters:**
- `context.availability`: Dict[UUID, Dict[UUID, Dict]] - availability matrix
- Format: `{person_id: {block_id: {'available': bool, 'replacement': str}}}`

**Typical Violations:**
- Assignment during vacation
- Assignment during deployment (TDY)
- Assignment during medical leave
- Assignment during requested absence

**Test Coverage:**
- Resident vacation blocking
- Faculty TDY blocking
- Deployment period blocking

---

#### 2. Eighty Hour Rule Constraint
**Type:** `DUTY_HOURS` | **Priority:** `CRITICAL` | **Module:** `acgme.py`

Enforces maximum 80 hours per week, strictly calculated over 4-week rolling average.

**Validation Logic:**
```python
for resident in residents:
    for each 4-week rolling window:
        total_hours = sum(assignments.hours in window)
        if total_hours > 80:
            violations += 1
```

**Parameters:**
- Window: 28 consecutive days (4 weeks)
- Max hours: 80 per week (320 per 4-week average)
- Calculation: Rolling average across all possible 28-day windows

**Typical Violations:**
- Cumulative hours exceed 80/week over 4-week period
- Night float + inpatient assignments exceed limit
- Moonlighting not properly deducted

**Test Coverage:**
- Rolling window boundary cases
- Resident with high baseline assignments + extra duty
- Night float rotation stacking

---

#### 3. One In Seven Rule Constraint
**Type:** `CONSECUTIVE_DAYS` | **Priority:** `CRITICAL` | **Module:** `acgme.py`

Ensures at least one 24-hour period off every 7 consecutive days.

**Validation Logic:**
```python
for resident in residents:
    for each 7-day window:
        days_worked = count_days_with_assignments(resident, window)
        if days_worked >= 7:
            violation()  # No 24-hour break in 7 days
```

**Parameters:**
- Window size: 7 consecutive days
- Min break: 24 consecutive hours off
- Calculation: Any calendar window

**Typical Violations:**
- 7 consecutive days of assignments
- Call duty + daytime assignments spanning 7 days without break
- Post-call + regular assignment same/next day

**Test Coverage:**
- Week boundary cases
- Post-call recovery requirements
- Multiple call weeks

---

#### 4. Supervision Ratio Constraint
**Type:** `SUPERVISION` | **Priority:** `CRITICAL` | **Module:** `acgme.py`

Ensures adequate faculty-to-resident supervision ratios by PGY level.

**Validation Logic:**
```python
for rotation in rotations:
    faculty_count = count_eligible_faculty(rotation)
    resident_count = count_residents(rotation)

    # PGY-1: 1 faculty per 2 residents
    if pgy_level == 1:
        if resident_count > faculty_count * 2:
            violation()

    # PGY-2/3: 1 faculty per 4 residents
    elif pgy_level >= 2:
        if resident_count > faculty_count * 4:
            violation()
```

**Parameters:**
- PGY-1: 1 faculty : 2 residents max
- PGY-2/3: 1 faculty : 4 residents max
- Eligible faculty: Full-time, not adjunct, not new to service

**Typical Violations:**
- Too many PGY-1s with limited faculty
- Missing faculty assignment for rotation
- Adjunct faculty counted as full-time

**Test Coverage:**
- PGY-1 supervision at boundary
- Mixed PGY levels in rotation
- Faculty availability during rotation

---

### Capacity Constraints (capacity.py)

#### 5. One Person Per Block Constraint
**Type:** `CAPACITY` | **Priority:** `HIGH` | **Module:** `capacity.py`

Ensures exactly one person is assigned to each block-rotation pair.

**Validation Logic:**
```python
for block in blocks:
    for rotation_template in templates:
        count = assignments.filter(
            block_id=block.id,
            template_id=template.id
        ).count()
        if count != 1:
            violation()
```

**Parameters:**
- One assignment per (block, rotation_template) pair
- Null assignments allowed only for unscheduled rotations

**Typical Violations:**
- Double-booking (2 people assigned to same block-rotation)
- No one assigned to required rotation
- Adjunct assigned to permanent slot

**Test Coverage:**
- Duplicate assignments
- Missing required rotation assignments
- Oversubscribed block

---

#### 6. Clinic Capacity Constraint
**Type:** `CAPACITY` | **Priority:** `HIGH` | **Module:** `capacity.py`

Enforces clinic maximum occupancy limits.

**Validation Logic:**
```python
for clinic in clinics:
    for block in blocks:
        count = assignments.filter(
            block_id=block.id,
            rotation_type='clinic',
            clinic_id=clinic.id
        ).count()
        if count > clinic.max_capacity:
            violation()
```

**Parameters:**
- `clinic.max_capacity`: Maximum residents per clinic per block
- Typical range: 2-4 residents per clinic per AM/PM block

**Typical Violations:**
- Too many residents assigned to limited clinic slots
- Clinic specialty mismatch

**Test Coverage:**
- Clinic at capacity
- Multiple clinics with different capacities
- Specialty clinic capacity constraints

---

#### 7. Max Physicians In Clinic Constraint
**Type:** `CAPACITY` | **Priority:** `HIGH` | **Module:** `capacity.py`

Limits faculty supervising same clinic block.

**Validation Logic:**
```python
for clinic in clinics:
    for block in blocks:
        count = faculty_assignments.filter(
            block_id=block.id,
            clinic_id=clinic.id
        ).count()
        if count > clinic.max_faculty:
            violation()
```

**Parameters:**
- `clinic.max_faculty`: Maximum faculty per clinic block
- Typical: 1-2 attending physicians per clinic

**Typical Violations:**
- Multiple faculty assigned to same clinic block
- Supervision redundancy

---

### Call Constraints (call_coverage.py, post_call.py, overnight_call.py, night_float_post_call.py)

#### 8. Post Call Auto Assignment Constraint
**Type:** `CALL` | **Priority:** `CRITICAL` | **Module:** `post_call.py`

Automatically assigns "post-call" rotation after call duty.

**Validation Logic:**
```python
for assignment in call_assignments:
    if is_call_duty(assignment):
        next_day_assignment = find_assignment(
            person_id=assignment.person_id,
            date=assignment.date + 1
        )
        if not next_day_assignment or not is_post_call(next_day_assignment):
            violation()
```

**Parameters:**
- Trigger: Any call duty assignment
- Action: Automatically assign post-call rotation next block
- Duration: 1 block (AM or PM)

**Typical Violations:**
- Call duty not followed by post-call recovery
- Post-call work hour reduction not applied

**Test Coverage:**
- Overnight call → morning post-call
- Night float post-call handling
- Week boundary post-call (end of week call)

---

#### 9. Night Float Post Call Constraint
**Type:** `CALL` | **Priority:** `HIGH` | **Module:** `night_float_post_call.py`

Special handling for night float post-call recovery requirements.

**Validation Logic:**
```python
for assignment in night_float_assignments:
    if is_night_float(assignment):
        # Night float typically Friday-Monday
        # Post-call recovery: Mon/Tue light duty
        next_assignments = find_next_2_blocks(assignment.person_id)
        if not (is_light_duty(next_assignments[0]) or
                is_light_duty(next_assignments[1])):
            violation()
```

**Parameters:**
- Trigger: Night float rotation
- Recovery: 2 blocks of light duty (clinic preferred)
- Duration: Following week

**Typical Violations:**
- Night float not followed by adequate light duty
- Heavy assignment (inpatient) post-night float

---

#### 10. Overnight Call Coverage Constraint
**Type:** `CALL` | **Priority:** `HIGH` | **Module:** `call_coverage.py`

Ensures overnight call is properly covered by assigned faculty.

**Validation Logic:**
```python
for date in date_range:
    for overnight_shift in overnights:
        assigned_faculty = assignments.filter(
            date=date,
            shift_type='overnight_call'
        ).count()
        if assigned_faculty < overnight_shift.required_count:
            violation()
```

**Parameters:**
- Required faculty per overnight: 1-2 depending on service
- Coverage validation: Faculty available, credentialed, not over-assigned

**Typical Violations:**
- No faculty assigned to overnight call
- Faculty with TDY/absence assigned to call

---

#### 11. Overnight Call Generation Constraint
**Type:** `CALL` | **Priority:** `HIGH` | **Module:** `overnight_call.py`

Generates overnight call assignments for residents when applicable.

**Validation Logic:**
```python
for resident in residents:
    expected_calls = resident.expected_call_nights_per_year
    actual_calls = count_call_assignments(resident)
    if actual_calls < expected_calls * (current_week / 52):
        warning()  # Under-scheduled on calls (soft constraint)
```

**Parameters:**
- Frequency: Based on specialty (typically 2-4 calls per month)
- Eligible residents: PGY-2 and above, not new
- Spacing: Minimum 5 days between calls

**Typical Violations:**
- Resident not reaching expected call frequency
- Call assignments bunched together

---

#### 12. Call Availability Constraint
**Type:** `CALL` | **Priority:** `HIGH` | **Module:** `call_coverage.py`

Ensures personnel assigned to call duty are actually available.

**Validation Logic:**
```python
for assignment in call_assignments:
    if is_call_duty(assignment):
        if not context.availability[person_id][block_id]["available"]:
            violation()
```

**Parameters:**
- Prerequisite: Availability constraint
- Special handling: Call duty blocking dates
- Exception: Call-covered absences (TDY call coverage)

**Typical Violations:**
- Faculty with TDY assigned to call
- Vacation call assignments

---

#### 13. Adjunct Call Exclusion Constraint
**Type:** `CALL` | **Priority:** `CRITICAL` | **Module:** `call_coverage.py`

Prevents adjunct faculty from taking call duty assignments.

**Validation Logic:**
```python
for assignment in call_assignments:
    faculty = get_person(assignment.person_id)
    if faculty.is_adjunct:
        violation()  # Adjuncts cannot take call
```

**Parameters:**
- Adjunct identification: `person.faculty_type == 'ADJUNCT'`
- Enforcement: Hard constraint at solver level

**Typical Violations:**
- Adjunct assigned to overnight call
- Adjunct assigned to weekend call

---

### Faculty Assignment Constraints (primary_duty.py, faculty_role.py)

#### 14. Faculty Day Availability Constraint
**Type:** `AVAILABILITY` | **Priority:** `HIGH` | **Module:** `primary_duty.py`

Restricts faculty to specific days based on role constraints.

**Validation Logic:**
```python
for faculty in faculty_list:
    for assignment in faculty.assignments:
        if not is_allowed_day(faculty.role, assignment.date):
            violation()
```

**Parameters:**
- Faculty role determines allowed days
- Typical: Department chair M/W/F only, others flexible
- Exception handling: Department needs can override

**Typical Violations:**
- APD assigned to evening shifts
- Clinic director assigned to non-clinic rotation

---

#### 15. Faculty Primary Duty Clinic Constraint
**Type:** `AVAILABILITY` | **Priority:** `HIGH` | **Module:** `primary_duty.py`

Ensures faculty with primary clinic duties meet minimum clinic assignments.

**Validation Logic:**
```python
for faculty in faculty_with_clinic_duty:
    clinic_weeks = count_weeks_with_clinic(faculty)
    if clinic_weeks < faculty.min_clinic_weeks:
        violation()
```

**Parameters:**
- `faculty.primary_clinic`: Primary assigned clinic
- `faculty.min_clinic_weeks`: Minimum weeks per year in clinic
- Typical: 8-12 weeks per year for clinic faculty

**Typical Violations:**
- Clinic faculty not meeting clinic assignment quota
- Primary clinic rotation under-scheduled

---

#### 16. Faculty Role Clinic Constraint
**Type:** `AVAILABILITY` | **Priority:** `HIGH` | **Module:** `faculty_role.py`

Maps faculty roles to eligible clinics.

**Validation Logic:**
```python
for assignment in assignments:
    faculty = get_person(assignment.person_id)
    clinic = get_clinic(assignment)
    if not clinic in faculty.eligible_clinics:
        violation()
```

**Parameters:**
- Clinic eligibility by role
- Typical: Faculty specialized in certain clinics only
- Example: Ortho faculty only in ortho clinic

**Typical Violations:**
- Faculty assigned to clinic outside specialty
- Role-clinic mismatch

---

#### 17. Sports Medicine Faculty Clinic Constraint
**Type:** `AVAILABILITY` | **Priority:** `HIGH` | **Module:** `faculty_role.py`

Specialty constraint for sports medicine faculty clinic assignments.

**Validation Logic:**
```python
for assignment in sports_med_assignments:
    if not is_sports_medicine_faculty(assignment.person_id):
        violation()
```

**Parameters:**
- Sports medicine clinic: Requires certified sports med faculty
- Certification: Board certified or fellowship trained

---

### Temporal Constraints (temporal.py, inpatient.py, fmit.py)

#### 18. Wednesday AM Intern Only Constraint
**Type:** `ROTATION` | **Priority:** `HIGH` | **Module:** `temporal.py`

Wednesday AM clinic restricted to PGY-1 residents only.

**Validation Logic:**
```python
for assignment in wednesday_am_clinic_assignments:
    resident = get_person(assignment.person_id)
    if resident.pgy_level != 1:
        violation()
```

**Parameters:**
- Day: Wednesday
- Time: AM block
- Rotation: Specific clinic (typically family medicine core)
- Restriction: PGY-1 only

---

#### 19. Wednesday PM Single Faculty Constraint
**Type:** `ROTATION` | **Priority:** `HIGH` | **Module:** `temporal.py`

Wednesday PM clinic limited to single faculty supervisor.

**Validation Logic:**
```python
wednesday_pm_clinics = assignments.filter(
    day_of_week=2,  # Wednesday
    block='PM',
    is_clinic=True
)
for clinic in unique_clinics(wednesday_pm_clinics):
    faculty_count = count_unique_faculty(wednesday_pm_clinics)
    if faculty_count > 1:
        violation()
```

**Parameters:**
- Day: Wednesday
- Time: PM block
- Max faculty: 1 per clinic

---

#### 20. Inverted Wednesday Constraint
**Type:** `ROTATION` | **Priority:** `HIGH` | **Module:** `temporal.py`

Alternate weeks: Some weeks with Wednesday clinic, some without (staggered).

**Validation Logic:**
```python
for resident in residents:
    for each 2-week period:
        week1_wed = has_wednesday_clinic(resident, period[0])
        week2_wed = has_wednesday_clinic(resident, period[1])
        if week1_wed == week2_wed:  # Both or neither
            warning()  # Soft constraint - log for review
```

**Parameters:**
- Pattern: Alternating weeks with clinic duty
- Goal: Balance clinic exposure across year

---

#### 21. FMIT Mandatory Call Constraint
**Type:** `CALL` | **Priority:** `HIGH` | **Module:** `fmit.py`

FMIT (Family Medicine Internal Training) residents must take assigned call.

**Validation Logic:**
```python
for resident in fmit_residents:
    call_count = count_call_assignments(resident)
    if call_count < resident.required_calls:
        violation()
```

**Parameters:**
- FMIT requirement: Minimum call frequency
- Typical: 2-3 calls per month minimum

---

#### 22. FMIT Staffing Floor Constraint
**Type:** `CAPACITY` | **Priority:** `HIGH` | **Module:** `fmit.py`

Maintains minimum FMIT resident staffing in clinic rotations.

**Validation Logic:**
```python
for fmit_clinic in fmit_clinics:
    for block in blocks:
        count = assignments.filter(
            clinic_id=fmit_clinic.id,
            block_id=block.id,
            is_fmit=True
        ).count()
        if count < fmit_clinic.min_residents:
            violation()
```

**Parameters:**
- Clinic: FMIT-specific clinics
- Minimum staffing: 1-2 residents per block

---

#### 23. FMIT Week Blocking Constraint
**Type:** `ROTATION` | **Priority:** `HIGH` | **Module:** `fmit.py`

Blocks continuous rotation coverage for FMIT continuity of care.

**Validation Logic:**
```python
for fmit_resident in fmit_residents:
    for month in year:
        for week in month:
            assignments = get_assignments(resident, week)
            clinic_days = count_clinic_assignments(assignments)
            if clinic_days != expected_clinic_days:
                violation()
```

**Parameters:**
- FMIT block pattern: Specific week structure
- Continuity: Consistent clinic provider per patient

---

#### 24. FMIT Continuity Turf Constraint
**Type:** `ROTATION` | **Priority:** `HIGH` | **Module:** `fmit.py`

Prevents frequent rotation changes for FMIT continuity ("turffing").

**Validation Logic:**
```python
for fmit_resident in fmit_residents:
    for patient_cohort in continuity_patients:
        provider_count = count_unique_providers(patient_cohort)
        if provider_count > max_providers:
            violation()  # Too many turfs
```

**Parameters:**
- Max turf count: Limit number of provider changes
- Continuity goal: Same provider for > 80% of patient visits

---

#### 25. Post FMIT Recovery Constraint
**Type:** `RECOVERY` | **Priority:** `HIGH` | **Module:** `fmit.py`

Requires light duty period after intensive FMIT rotations.

**Validation Logic:**
```python
for resident in fmit_residents:
    if ends_intensive_rotation(resident):
        next_rotation = get_next_rotation(resident)
        if not is_light_duty(next_rotation):
            violation()
```

**Parameters:**
- Trigger: End of intensive block (e.g., 4-week in-house)
- Recovery: 1 week light duty (clinic preferred)

---

#### 26. Post FMIT Sunday Blocking Constraint
**Type:** `ROTATION` | **Priority:** `HIGH` | **Module:** `fmit.py`

Blocks Sunday work immediately after FMIT intensive rotations.

**Validation Logic:**
```python
for resident in fmit_residents:
    if ends_intensive_rotation(resident):
        next_sunday = get_next_sunday(resident)
        if has_assignment(resident, next_sunday):
            violation()  # No work assigned Sunday post-intensive
```

**Parameters:**
- Trigger: Post-FMIT intensive rotation
- Duration: 1 Sunday off
- Recovery purpose: Physical recovery

---

#### 27. Resident Inpatient Headcount Constraint
**Type:** `CAPACITY` | **Priority:** `HIGH` | **Module:** `inpatient.py`

Maintains minimum resident coverage on inpatient rotations.

**Validation Logic:**
```python
for inpatient_unit in units:
    for block in blocks:
        count = assignments.filter(
            unit_id=inpatient_unit.id,
            block_id=block.id,
            is_resident=True
        ).count()
        if count < inpatient_unit.min_residents:
            violation()
```

**Parameters:**
- Inpatient units: ICU, telemetry, etc.
- Min staffing: 2-4 residents per unit per block

---

## Soft Constraints

Soft constraints are optimization objectives with configurable weights. Violations incur penalties in the objective function.

### Equity Constraints (equity.py)

#### 28. Equity Constraint
**Type:** `EQUITY` | **Priority:** `MEDIUM` | **Weight:** `2.0` | **Module:** `equity.py`

Balances assignment distribution across all residents.

**Penalty Calculation:**
```python
deviation = abs(resident_assignment_count - mean_assignment_count)
penalty = weight * priority.value * deviation
```

**Parameters:**
- Weight: 2.0 (high importance)
- Target: All residents have similar number of assignments
- Metric: Standard deviation of assignment counts

**Optimization Goal:**
- Minimize assignment variance across residents
- Typical: Within ±2 assignments of mean

**Typical Optimizations:**
- Distribute high-demand rotations equally
- Balance weekend assignments
- Equalize on-call frequency

---

#### 29. Continuity Constraint
**Type:** `CONTINUITY` | **Priority:** `MEDIUM` | **Weight:** `1.5` | **Module:** `equity.py`

Promotes continuity of care through repeated assignments.

**Penalty Calculation:**
```python
continuity_score = count_resident_assigned_same_rotation()
penalty = weight * priority.value * (1 - continuity_score)
```

**Parameters:**
- Weight: 1.5
- Target: Residents see familiar patients/settings
- Metric: Repeat clinic assignments to same location

**Optimization Goal:**
- Maximize number of repeated assignments
- Typical: 3-4 month continuity blocks

---

### Resilience Constraints (resilience.py)

#### 30. Hub Protection Constraint
**Type:** `RESILIENCE` | **Priority:** `MEDIUM` | **Weight:** `1.5` | **Module:** `resilience.py`

Protects critical "hub" faculty from over-assignment.

**Penalty Calculation:**
```python
hub_score = context.get_hub_score(faculty_id)
assignment_count = len(assignments[faculty_id])
if hub_score > 0.6:  # Critical hub
    penalty = weight * priority.value * (assignment_count - target)
```

**Parameters:**
- Hub threshold: Score > 0.6 (from network analysis)
- Max assignments: Based on role and availability
- Network metrics: Betweenness centrality, degree centrality

**Optimization Goal:**
- Reduce assignments to critical faculty
- Maintain operational redundancy

**Integration:**
- Uses `SchedulingContext.hub_scores` from ResilienceService
- Requires resilience data population

---

#### 31. Utilization Buffer Constraint
**Type:** `UTILIZATION_BUFFER` | **Priority:** `HIGH` | **Weight:** `2.0` | **Module:** `resilience.py`

Maintains 20% utilization buffer to prevent cascade failures (queuing theory).

**Penalty Calculation:**
```python
current_util = context.current_utilization
target_util = context.target_utilization  # Default 0.80
if current_util > target_util:
    excess = current_util - target_util
    penalty = weight * priority.value * excess^2
```

**Parameters:**
- Target utilization: 0.80 (80%)
- Buffer: 20% idle capacity
- Theory: Reduces queueing delay and cascade risk
- Metric: Slot fill rate vs. total available slots

**Optimization Goal:**
- Keep system utilization below 80%
- Maintain emergency reserve capacity

---

#### 32. N1 Vulnerability Constraint
**Type:** `N1_VULNERABILITY` | **Priority:** `HIGH` | **Weight:** `2.5` | **Module:** `resilience.py`

Reduces risk of single-point-of-failure faculty (N-1 vulnerability).

**Penalty Calculation:**
```python
if faculty_id in context.n1_vulnerable_faculty:
    # This faculty is critical - distribute assignments to backups
    backup_faculty = find_backup_faculty(faculty_id)
    if not backup_faculty:
        penalty = weight * priority.value * CRITICAL_PENALTY
```

**Parameters:**
- Vulnerable faculty: Identified by contingency analysis
- Mitigation: Cross-training, backup assignments
- Metric: Schedule survives loss of faculty member

**Optimization Goal:**
- Eliminate single points of failure
- Build redundant coverage

---

#### 33. Preference Trail Constraint
**Type:** `PREFERENCE_TRAIL` | **Priority:** `LOW` | **Weight:** `0.5` | **Module:** `resilience.py`

Incorporates learned faculty preferences from stigmergy.

**Penalty Calculation:**
```python
for assignment in assignments:
    strength = context.get_preference_strength(faculty_id, slot_type)
    if strength < 0.3:  # Strong avoidance
        penalty += weight * priority.value * (0.3 - strength)
    elif strength > 0.7:  # Strong preference
        bonus = weight * priority.value * (strength - 0.7)  # Negative penalty
```

**Parameters:**
- Strength range: 0.0-1.0 (0=avoid, 1=prefer)
- Threshold: 0.3 (avoidance), 0.7 (preference)
- Learning: From historical schedules

---

#### 34. Zone Boundary Constraint
**Type:** `ZONE_BOUNDARY` | **Priority:** `MEDIUM` | **Weight:** `1.0` | **Module:** `resilience.py`

Keeps faculty assignments within assigned operational zones (blast radius isolation).

**Penalty Calculation:**
```python
for assignment in assignments:
    faculty_zone = context.zone_assignments.get(faculty_id)
    block_zone = context.block_zones.get(block_id)
    if faculty_zone != block_zone:
        penalty += weight * priority.value * CROSS_ZONE_PENALTY
```

**Parameters:**
- Zone assignment: Geographical or operational zones
- Cross-zone assignments: Allowed but penalized
- Purpose: Isolate failures to single zone

---

### Preference Constraints (faculty.py)

#### 35. Faculty Preference Constraint
**Type:** `PREFERENCE` | **Priority:** `MEDIUM` | **Weight:** `1.0` | **Module:** `faculty.py`

Respects individual faculty scheduling preferences.

**Penalty Calculation:**
```python
for faculty in faculty_list:
    for preference in faculty.preferences:
        if assignment conflicts with preference:
            penalty += weight * priority.value * preference.severity
```

**Parameters:**
- Preference types: Avoid rotation, prefer rotation, unavailable
- Severity: 0.5 (nice-to-have) to 2.0 (important)
- Soft constraint: Can be overridden

**Typical Preferences:**
- Prefer morning shifts
- Avoid back-to-back clinics
- Unavailable on specific dates
- Prefer specific clinics

---

#### 36. Faculty Clinic Equity Soft Constraint
**Type:** `EQUITY` | **Priority:** `MEDIUM` | **Weight:** `1.5` | **Module:** `primary_duty.py`

Balances clinic assignments across faculty with clinic duties.

**Penalty Calculation:**
```python
for faculty_group in clinic_faculty:
    mean_clinics = mean(clinic_assignment_count)
    for faculty in clinic_faculty:
        deviation = abs(faculty.clinic_count - mean_clinics)
        penalty += weight * priority.value * deviation
```

**Parameters:**
- Clinic faculty: Those with clinic duties
- Target: Balanced clinic assignments
- Metric: Clinic weeks per faculty per year

---

### Coverage Constraints (capacity.py)

#### 37. Coverage Constraint
**Type:** `COVERAGE` | **Priority:** `HIGH` | **Weight:** `1.0` | **Module:** `capacity.py`

Ensures all required rotations have assigned personnel.

**Penalty Calculation:**
```python
for rotation_slot in required_slots:
    if no_assignment(rotation_slot):
        penalty += weight * priority.value * SLOT_PENALTY
```

**Parameters:**
- Required slots: All block-rotation pairs
- Assignment requirement: Exactly one person
- Soft constraint: Can leave gaps in low-priority slots

**Typical Coverage:**
- All clinic sessions covered
- All in-house rotations covered
- Call nights covered

---

### Call Equity Constraints (call_equity.py)

#### 38. Weekday Call Equity Constraint
**Type:** `EQUITY` | **Priority:** `MEDIUM` | **Weight:** `1.5` | **Module:** `call_equity.py`

Balances weekday (Monday-Thursday) overnight call assignments.

**Penalty Calculation:**
```python
for faculty in call_eligible:
    weekday_call_count = count_calls(faculty, days=['Mon','Tue','Wed','Thu'])
    deviation = abs(weekday_call_count - mean_weekday_calls)
    penalty += weight * priority.value * deviation
```

**Parameters:**
- Weekday call: Monday-Thursday nights
- Goal: Distribute evenly across faculty
- Frequency: Typically 1-2 per month per faculty

---

#### 39. Sunday Call Equity Constraint
**Type:** `EQUITY` | **Priority:** `MEDIUM` | **Weight:** `2.0` | **Module:** `call_equity.py`

Balances Sunday call assignments (less desirable).

**Penalty Calculation:**
```python
for faculty in call_eligible:
    sunday_count = count_calls(faculty, day='Sunday')
    deviation = abs(sunday_count - mean_sunday_calls)
    penalty += weight * priority.value * deviation * 2.0  # Extra weight
```

**Parameters:**
- Sunday calls: Less desirable, higher compensation
- Weight: 2.0 (higher priority than weekday)
- Goal: Maximize fairness of weekend duty

---

#### 40. Call Spacing Constraint
**Type:** `EQUITY` | **Priority:** `MEDIUM` | **Weight:** `1.5` | **Module:** `call_equity.py`

Encourages spacing between consecutive call assignments.

**Penalty Calculation:**
```python
for faculty in call_eligible:
    for call1, call2 in consecutive_calls(faculty):
        days_between = (call2.date - call1.date).days
        if days_between < MIN_DAYS:
            penalty += weight * priority.value * (MIN_DAYS - days_between)
```

**Parameters:**
- Min spacing: 5-7 days between calls
- Burnout reduction: Adequate recovery time
- Exception: Consecutive weeks allowed if scheduled

---

#### 41. Tuesday Call Preference Constraint
**Type:** `PREFERENCE` | **Priority:** `MEDIUM` | **Weight:** `1.0` | **Module:** `call_equity.py`

Soft preference for Tuesday calls (mid-week recovery).

**Penalty Calculation:**
```python
for faculty in call_eligible:
    if preferred_call_day == 'Tuesday':
        if assignment in ['Mon','Wed','Thu']:
            penalty += weight * priority.value * PREFERENCE_PENALTY
```

**Parameters:**
- Preferred day: Tuesday (mid-week, good recovery window)
- Soft constraint: Can assign other days if needed

---

#### 42. Department Chief Wednesday Preference Constraint
**Type:** `PREFERENCE` | **Priority:** `MEDIUM` | **Weight:** `1.0` | **Module:** `call_equity.py`

Soft preference for Department Chief to have light duty on Wednesdays.

**Penalty Calculation:**
```python
if role == 'DEPARTMENT_CHIEF':
    for wednesday_assignment in wednesday_assignments:
        if is_heavy_duty(wednesday_assignment):
            penalty += weight * priority.value * HEAVY_DUTY_PENALTY
```

**Parameters:**
- Role: Department Chief / Program Director
- Preferred duty: Light (clinic preferred)
- Day: Wednesday

---

### FMIT Resident Constraints (inpatient.py, sports_medicine.py)

#### 43. FMIT Resident Clinic Day Constraint
**Type:** `ROTATION` | **Priority:** `HIGH` | **Weight:** `1.5` | **Module:** `inpatient.py`

Ensures FMIT residents have minimum clinic days during inpatient rotations.

**Penalty Calculation:**
```python
for fmit_resident in fmit_residents:
    during_inpatient_rotation:
        clinic_days = count_clinic_days(resident)
        if clinic_days < min_clinic_days:
            penalty += weight * priority.value * (min_clinic_days - clinic_days)
```

**Parameters:**
- FMIT inpatient rotation: 4-week periods
- Min clinic days: 1-2 days per week
- Goal: Maintain clinic continuity during in-house

---

#### 44. Sports Medicine Resident-Faculty Alignment Constraint
**Type:** `ALIGNMENT` | **Priority:** `HIGH` | **Weight:** `1.5` | **Module:** `sports_medicine.py`

Aligns sports medicine resident assignments with faculty expertise.

**Penalty Calculation:**
```python
for resident in sports_med_residents:
    for assignment in assignments:
        if assignment.faculty_id:
            if faculty.specialty != 'sports_medicine':
                penalty += weight * priority.value * MISMATCH_PENALTY
```

**Parameters:**
- Sports medicine residents: PGY-2/3 in SM track
- Faculty requirement: Sports medicine certified
- Specialty match: Important for learning outcomes

---

## Constraint Priorities

Constraints are prioritized by importance for solver ordering and soft constraint weighting:

### Priority Levels

| Priority | Value | Description | Examples |
|----------|-------|-------------|----------|
| **CRITICAL** | 100 | ACGME compliance, system integrity | 80-Hour Rule, Availability, Call Exclusion |
| **HIGH** | 75 | Essential operational constraints | Capacity, Supervision, Faculty roles |
| **MEDIUM** | 50 | Optimization objectives, preferences | Equity, Coverage, Preferences |
| **LOW** | 25 | Nice-to-have optimizations | Preference Trails, Light optimizations |

### Solver Impact

- **Hard constraints** (all priorities): Enforced during solving, violations make schedule infeasible
- **Soft constraints**: Ordered by priority when applying penalties
  - CRITICAL priority = weight multiplied by 100
  - HIGH priority = weight multiplied by 75
  - MEDIUM priority = weight multiplied by 50
  - LOW priority = weight multiplied by 25

---

## Constraint Types

All constraints fall into these categories:

| Type | Description | Examples |
|------|-------------|----------|
| `AVAILABILITY` | Person availability on dates | Availability, Faculty Day Availability |
| `DUTY_HOURS` | Work hour limits | 80-Hour Rule, Shift Limits |
| `CONSECUTIVE_DAYS` | Daily working patterns | 1-in-7 Rule, Recovery Requirements |
| `SUPERVISION` | Faculty-resident ratios | Supervision Ratio |
| `CAPACITY` | Resource limits | Clinic Capacity, Headcount |
| `ROTATION` | Rotation-specific rules | Wednesday constraints, FMIT rules |
| `PREFERENCE` | Soft preferences | Faculty preferences, Timeslot preferences |
| `EQUITY` | Fair distribution | Equity, Continuity, Call Equity |
| `CONTINUITY` | Continuity of care | Continuity, FMIT Continuity Turf |
| `CALL` | Call duty specific | Call Coverage, Spacing, Exclusions |
| `SPECIALTY` | Specialty requirements | Faculty Role Clinic, SM Alignment |
| `RESILIENCE` | System resilience | Hub Protection, N-1 Vulnerability, Zones |
| `FATIGUE_LIMIT` | Fatigue-related limits | Circadian Protection, Recovery |
| `RECOVERY_REQUIREMENT` | Post-duty recovery | Post-Call, Post-FMIT Recovery |
| `SHIFT_DURATION_LIMIT` | Maximum shift length | Night Float limits |

---

## Constraint Conflicts Matrix

### Potential Conflicts

| Constraint A | Constraint B | Conflict Type | Resolution |
|--------------|--------------|---------------|-----------|
| Equity | Continuity | Distribution vs. Continuity | Continuity usually takes precedence |
| Hub Protection | Fairness | Protection vs. Equal distribution | Accept some inequity for resilience |
| Capacity | Equity | Limited slots vs. Fair distribution | Prioritize capacity hard constraint |
| FMIT Continuity Turf | Equity | Limited providers vs. Fair rotation | Turf constraint takes precedence |
| Call Spacing | Call Equity | Spacing vs. Fair distribution | Try to satisfy both, spacing primary |
| Preference Trail | Explicit Preferences | Learned vs. Stated | Explicit preferences take precedence |

### Conflict Resolution Strategy

1. **Hard constraints always satisfied** (no conflicts at solver level)
2. **Soft constraints adjusted by weights** (higher weight = more important)
3. **Priority ordering** when conflicts arise
4. **Relaxation** (disable lower-priority soft constraints if needed)

---

## Parameter Reference

### Common Parameters

| Parameter | Type | Range | Typical Values | Purpose |
|-----------|------|-------|-----------------|---------|
| `weight` | float | 0.0-10.0 | 0.5-2.5 | Soft constraint importance multiplier |
| `priority` | enum | CRITICAL-LOW | - | Constraint priority for ordering |
| `enabled` | bool | true/false | true | Enable/disable constraint |
| `person_id` | UUID | - | - | Person (resident or faculty) |
| `block_id` | UUID | - | - | Time block (AM or PM) |
| `rotation_id` | UUID | - | - | Rotation template |
| `clinic_id` | UUID | - | - | Clinic location |
| `availability` | dict | - | - | Availability matrix (person × block) |
| `max_capacity` | int | 1-10 | 2-4 | Resource limit |
| `min_count` | int | 1-5 | 1-3 | Minimum required |
| `hub_score` | float | 0.0-1.0 | - | Hub vulnerability (0=not hub, 1=critical) |

### Context Data

| Field | Type | Populated By | Purpose |
|-------|------|--------------|---------|
| `residents` | list[Person] | Scheduler | All PGY residents |
| `faculty` | list[Person] | Scheduler | All faculty |
| `blocks` | list[Block] | Scheduler | All AM/PM blocks |
| `templates` | list[RotationTemplate] | Scheduler | All rotation types |
| `availability` | dict | Absence service | Absence blocking |
| `hub_scores` | dict[UUID, float] | ResilienceService | Hub centrality scores |
| `n1_vulnerable_faculty` | set[UUID] | ResilienceService | Critical faculty |
| `preference_trails` | dict[UUID, dict] | ResilienceService | Stigmergy preferences |
| `zone_assignments` | dict[UUID, UUID] | ResilienceService | Zone mapping |

---

## Examples

### Example 1: Building a Constraint Manager

```python
from app.scheduling.constraints import ConstraintManager
from app.scheduling.constraints.acgme import (
    AvailabilityConstraint,
    EightyHourRuleConstraint,
    OneInSevenRuleConstraint,
)

# Create manager
manager = ConstraintManager()

# Add constraints with chaining
manager.add(AvailabilityConstraint()) \
        .add(EightyHourRuleConstraint()) \
        .add(OneInSevenRuleConstraint())

# Enable resilience constraints when data available
if context.has_resilience_data():
    from app.scheduling.constraints.resilience import HubProtectionConstraint
    manager.add(HubProtectionConstraint())
    manager.enable("HubProtection")

# Apply to solver
manager.apply_to_cpsat(model, variables, context)
```

### Example 2: Validating Against Constraints

```python
# Validate all constraints
result = manager.validate_all(assignments, context)

# Check results
if not result.satisfied:
    print(f"Found {len(result.violations)} violations:")
    for violation in result.violations:
        print(f"- {violation.constraint_name}: {violation.message}")
        print(f"  Severity: {violation.severity}")
else:
    print("All constraints satisfied!")

# Soft constraint penalties
print(f"Total penalty: {result.penalty}")
```

### Example 3: Selectively Disabling Constraints

```python
# Disable soft constraints for faster solving
manager.disable("Equity") \
        .disable("Continuity") \
        .disable("PreferenceTrail")

# Keep hard constraints enabled
enabled = manager.get_enabled()
hard = manager.get_hard_constraints()
```

---

## Testing Guide

### Unit Testing Constraints

```python
import pytest
from app.scheduling.constraints.acgme import EightyHourRuleConstraint
from app.scheduling.constraints.base import SchedulingContext

@pytest.fixture
def constraint():
    return EightyHourRuleConstraint()

@pytest.fixture
def context():
    return SchedulingContext(residents=[], faculty=[], blocks=[], templates=[])

def test_eighty_hour_rule_satisfied(constraint, context):
    """Test that schedules under 80 hours satisfy constraint."""
    assignments = create_assignments(70)  # 70 hours
    result = constraint.validate(assignments, context)
    assert result.satisfied

def test_eighty_hour_rule_violated(constraint, context):
    """Test that schedules over 80 hours violate constraint."""
    assignments = create_assignments(100)  # 100 hours
    result = constraint.validate(assignments, context)
    assert not result.satisfied
    assert len(result.violations) > 0
```

### Integration Testing

```python
def test_constraint_manager_with_multiple_violations():
    """Test manager aggregates violations from multiple constraints."""
    manager = ConstraintManager()
    manager.add(AvailabilityConstraint())
    manager.add(EightyHourRuleConstraint())

    # Create schedule with multiple violations
    assignments = create_invalid_schedule()

    result = manager.validate_all(assignments, context)
    assert not result.satisfied
    assert len(result.violations) >= 2  # At least 2 violation types
```

---

## Debugging Guide

### Identifying Constraint Violations

```python
# Get detailed violation info
for violation in result.violations:
    print(f"Constraint: {violation.constraint_name}")
    print(f"Type: {violation.constraint_type}")
    print(f"Severity: {violation.severity}")
    print(f"Person: {violation.person_id}")
    print(f"Block: {violation.block_id}")
    print(f"Details: {violation.details}")
```

### Checking Constraint Status

```python
# List all constraints
all_constraints = manager.constraints
print(f"Total constraints: {len(all_constraints)}")

# List enabled constraints
enabled = manager.get_enabled()
print(f"Enabled: {[c.name for c in enabled]}")

# List hard vs soft
hard = manager.get_hard_constraints()
soft = manager.get_soft_constraints()
print(f"Hard: {len(hard)}, Soft: {len(soft)}")
```

### Solver Debugging

```python
# Enable verbose logging
import logging
logging.getLogger('app.scheduling.constraints').setLevel(logging.DEBUG)

# Apply constraints with debug output
manager.apply_to_cpsat(model, variables, context)
# Look for error messages in logs
```

---

## Relaxation Rules

When solving fails due to constraint conflicts, use relaxation in this order:

### Tier 1: Disable Low-Priority Soft Constraints
```python
manager.disable("PreferenceTrail")  # Weight 0.5
manager.disable("FacultyPreference")  # Low priority preferences
manager.disable("CallSpacing")  # Can tolerate tighter spacing
```

### Tier 2: Reduce Medium-Priority Soft Constraints
```python
manager.disable("Continuity")  # Reduce continuity requirement
manager.disable("Equity")  # Allow some inequity
# Reduce weights on resilience constraints
```

### Tier 3: Relax High-Priority Soft Constraints
```python
manager.disable("UtilizationBuffer")  # Allow > 80% util
manager.disable("CallEquity")  # Allow unequal call distribution
```

### Tier 4: Hard Constraint Relaxation (Last Resort)
```python
# Only if absolutely necessary - discuss with human
manager.disable("PostCallAutoAssignment")  # Risk: burnout
manager.disable("SupervisionRatio")  # Risk: compliance violation
# NEVER disable: Availability, 80-Hour Rule, 1-in-7 Rule
```

---

## Performance Tuning

### Constraint Application Ordering

The `ConstraintManager` automatically orders constraints by priority:

```python
# Constraints applied in order: CRITICAL → HIGH → MEDIUM → LOW
for constraint in sorted(self.get_enabled(), key=lambda c: -c.priority.value):
    constraint.add_to_cpsat(model, variables, context)
```

### Optimization Hints

1. **Disable soft constraints during exploration**: Keep only hard constraints during initial solve
2. **Add soft constraints progressively**: Add lower-weight constraints after hard constraints
3. **Use constraint weights wisely**: Higher weight = more enforcement
   - CRITICAL conflicts: weight = 3.0-5.0
   - Important preferences: weight = 1.0-2.0
   - Nice-to-have: weight = 0.5-1.0

### Scalability Considerations

| Constraint Type | Scaling | Notes |
|-----------------|---------|-------|
| **Hard constraints** | O(n) | Must check all during validation |
| **Soft constraints** | O(n) | Added to objective function |
| **Availability** | O(n²) | n residents × n blocks |
| **Equity** | O(n) | Single pass across assignments |
| **Call spacing** | O(n log n) | Sort by date then check gaps |

---

## Constraint Registration

See `constraint_registry.py` for registering new constraints:

```python
from app.scheduling.constraint_registry import ConstraintRegistry

# Auto-register constraint
@ConstraintRegistry.register(
    name="MyConstraint",
    version="1.0",
    category="CUSTOM"
)
class MyConstraint(HardConstraint):
    ...

# Retrieve registered constraints
constraints = ConstraintRegistry.get_all()
constraint = ConstraintRegistry.get("MyConstraint", "1.0")
```

---

## Migration Guide

### From Version 1.0 → 2.0

**Changes:**
- Constraint base classes simplified
- `ConstraintManager` improved with disable/enable
- Resilience constraints added to core
- Registry system introduced

**Migration:**
```python
# Old: Manual constraint creation
constraints = [
    AvailabilityConstraint(),
    EightyHourRuleConstraint(),
]

# New: Using manager with chaining
manager = ConstraintManager()
manager.add(AvailabilityConstraint()).add(EightyHourRuleConstraint())
```

---

## See Also

- [Constraint Builder](CONSTRAINT_BUILDER.md) - Fluent API for creating constraints
- [Constraint Validator](CONSTRAINT_VALIDATOR.md) - Pre-solver validation
- [Constraint Registry](CONSTRAINT_REGISTRY.md) - Constraint registration and discovery
- [Solver Algorithm](../architecture/SOLVER_ALGORITHM.md) - How constraints are applied
- [Resilience Framework](../architecture/cross-disciplinary-resilience.md) - Resilience constraints

---

**Last Updated:** 2025-12-31
**Maintained By:** Residency Scheduler Team
