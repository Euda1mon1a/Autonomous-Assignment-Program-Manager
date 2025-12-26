# Institutional Rules Reference

Tripler Army Medical Center (TAMC) Family Medicine Residency Program-specific scheduling policies and requirements.

---

## Overview

These are **institutional policies** that supplement ACGME requirements. While not federal regulations, they are program requirements that require Program Director approval to override.

**Institution:** Tripler Army Medical Center (TAMC)
**Program:** Family Medicine Residency
**Context:** Military medical training environment
**Last Updated:** December 2025

---

## Military-Specific Requirements

### 1. Deployment and TDY (Temporary Duty) Scheduling

#### Deployment Status

**Absolute Blocking:**
When a resident is deployed, they are completely unavailable for scheduling.

**Types of Deployment:**
| Type | Duration | Scheduling Impact |
|------|----------|-------------------|
| **Combat Deployment** | 6-12 months | Complete block, no assignments |
| **Humanitarian Mission** | 2-6 months | Complete block, no assignments |
| **Training Deployment** | 2-4 weeks | Complete block, plan coverage |

**Requirements:**
- Mark as `DEPLOYMENT` absence type in system
- Update availability matrix immediately upon notification
- Pre-plan coverage for entire deployment period
- Maintain N-1 contingency for deployment scenarios

**Implementation:**
```python
# Deployment blocks ALL scheduling
if absence.type == 'DEPLOYMENT':
    availability_matrix[person.id][date_range] = 'BLOCKED'
    # Cannot override, even for emergencies
```

#### TDY (Temporary Duty) Assignments

**Partial Availability:**
TDY may reduce but not eliminate availability.

**Common TDY Types:**
- Medical education courses (2-4 weeks)
- Military training (1-2 weeks)
- Conference presentations (1 week)
- Staff augmentation (varies)

**Requirements:**
- Document TDY orders in system
- Determine clinical availability during TDY
- Some TDY allows remote clinic (telehealth)
- Most TDY blocks inpatient/call duties

**Implementation:**
```python
# TDY reduces capacity but may allow some duties
if absence.type == 'TDY':
    if tdy.allows_remote_work:
        availability_matrix[person.id][date_range] = 'REDUCED'
        # Can still do telehealth clinic
    else:
        availability_matrix[person.id][date_range] = 'BLOCKED'
```

### 2. Duty Restrictions

#### Security Clearance Requirements

**Some rotations require active security clearance:**

| Rotation | Clearance Level | Alternative if Unavailable |
|----------|----------------|---------------------------|
| Inpatient Psych | SECRET | Civilian hospital rotation |
| Flight Medicine | SECRET | Defer or substitute |
| Occupational Medicine | None | Open to all |

**Requirements:**
- Verify clearance status before assignment
- Track clearance expiration dates
- Plan alternative rotations for residents without clearance

#### Physical Fitness Standards

**Medical Deployment Readiness:**
- Current PHA (Periodic Health Assessment)
- Up-to-date immunizations
- Dental readiness (Class 1 or 2)
- Not on temporary profile restricting duty

**Requirements:**
- Monthly readiness check
- Non-deployable status affects rotation selection
- Cannot deploy if not medically ready (but can still do clinical work)

---

## Program Curriculum Requirements

### 1. FMIT (Family Medicine Inpatient Training) Sequencing

#### Requirement

**All PGY-1 residents must complete FMIT rotation in first 6 months** (Blocks 1-3).

**Rationale:**
- Foundational rotation for all family medicine training
- Builds core clinical skills early
- Required before progressing to advanced rotations

**Scheduling Rules:**

```python
def validate_fmit_sequencing(schedule):
    """Ensure all PGY-1s complete FMIT in first 6 months."""

    for resident in get_pgy1_residents():
        fmit_assignments = [
            a for a in resident.assignments
            if a.rotation.name == 'FMIT'
            and a.date <= academic_year_start + timedelta(days=180)  # 6 months
        ]

        if not fmit_assignments:
            raise SequencingViolation(
                f"{resident.name} has no FMIT assignment in first 6 months"
            )
```

**Common Conflicts:**
- Multiple PGY-1s on deployment first 6 months
- Conference attendance in Fall
- Maternity/paternity leave

**Resolutions:**
- Front-load FMIT in Block 1 for residents at risk of deployment
- Use Blocks 2-3 for backup
- Extend to month 7 only with PD approval

### 2. Night Float (NF) Rotation Pattern

#### Requirement

**Night Float uses mirrored half-block pairing** - two residents alternate NF and day rotations within same block.

**Structure:**

```
Block 5 (4 weeks = 28 days):
┌────────────────────────┬────────────────────────┐
│ Half 1 (Days 1-14)     │ Half 2 (Days 15-28)    │
├────────────────────────┼────────────────────────┤
│ Resident A: NF         │ Resident A: NEURO      │
│ Resident B: NEURO      │ Resident B: NF         │
└────────────────────────┴────────────────────────┘
```

**Requirements:**
- Exactly 1 resident on NF per half-block
- Mirrored pair must be compatible (both PGY-2/3)
- Post-Call (PC) day required on Day 15 for Resident A
- Post-Call (PC) day required on Day 1 (next block) for Resident B
- Maximum 2-week NF stint (14 consecutive days)

**Implementation:**

```python
class NightFloatPostCallConstraint:
    """Enforce NF half-block mirroring and PC requirements."""

    def validate(self, assignments):
        for block in blocks:
            nf_assignments = get_nf_assignments(block)

            # Check exactly 1 resident on NF per half-block
            half1_nf = [a for a in nf_assignments if a.days <= 14]
            half2_nf = [a for a in nf_assignments if a.days > 14]

            if len(half1_nf) != 1 or len(half2_nf) != 1:
                raise NightFloatViolation("NF must have exactly 1 resident per half")

            # Check mirroring
            resident_a = half1_nf[0].person
            resident_b = half2_nf[0].person

            if resident_a == resident_b:
                raise NightFloatViolation("Same resident on both NF halves (no mirror)")

            # Check PC day after NF
            if not has_post_call_day(resident_a, block.day_15):
                raise NightFloatViolation(f"{resident_a} missing PC day after NF")

            if not has_post_call_day(resident_b, next_block.day_1):
                raise NightFloatViolation(f"{resident_b} missing PC day after NF")
```

**Common Violations:**
- Forgetting PC day on Day 15
- Same resident on both halves
- More than 2 weeks continuous NF

**See:** `backend/app/scheduling/constraints/night_float_post_call.py`

### 3. Post-Call (PC) Day Requirements

#### Requirement

**Mandatory Post-Call day after Night Float rotation** and certain other high-intensity rotations.

**Applies to:**
- Night Float (NF) - PC day after final night
- 24-hour inpatient call - PC day next day
- Long EM shifts (>12 hours) - PC day next day

**PC Day Definition:**
- No clinical duties
- No required educational activities
- Counts toward 1-in-7 rule
- Can be used for admin/study

**Scheduling Rules:**

```
If Night Float ends Day 14:
  → Day 15 must be Post-Call (no assignments)

If 24-hour call on Friday:
  → Saturday must be Post-Call

If working Night 1 through Night 6:
  → Day after Night 6 must be PC
```

**Implementation:**
```python
# After NF rotation, next day is PC
if previous_rotation == 'Night_Float' and previous_end_date == today - 1:
    # Today must be PC day
    if has_assignment(resident, today):
        raise PostCallViolation("PC day required after NF")
```

### 4. Continuity Clinic Requirements

#### Requirement

**Weekly continuity clinic attendance** throughout residency (except when on inpatient or NF rotations).

**Schedule:**
- PGY-1: 1 half-day per week
- PGY-2: 1 half-day per week
- PGY-3: 2 half-days per week (increased patient panel)

**Exceptions:**
- Inpatient rotations (FMIT, IM, EM) - no continuity clinic
- Night Float - no continuity clinic
- Deployment/TDY - continuity clinic paused
- Conference attendance - may miss one session

**Requirements:**
- Same clinic site throughout residency (continuity of care)
- Same preceptor when possible
- Dedicated patient panel
- Cannot be scheduled for conflicting duties during clinic time

**Implementation:**
```python
def assign_continuity_clinic(resident, week):
    """Assign weekly continuity clinic if not on blocking rotation."""

    # Check if on blocking rotation
    blocking_rotations = ['FMIT', 'IM', 'EM', 'NF', 'L&D']
    current_rotation = get_rotation(resident, week)

    if current_rotation.name not in blocking_rotations:
        # Assign continuity clinic
        clinic_day = resident.continuity_clinic_day  # e.g., Wednesday
        assign(resident, f"{week}-{clinic_day}", "Continuity_Clinic")
```

**Common Conflicts:**
- Rotation schedules clinic duties on continuity day
- Conference conflicts
- Call schedule overlaps

**Resolution:**
- Protected time: Continuity clinic has priority
- Reschedule conflicting duties
- If unavoidable conflict, notify preceptor and reschedule patients

### 5. Procedure Rotation Requirements

#### Requirement

**Minimum procedure numbers** must be met for graduation and board eligibility.

**Key Procedures:**
| Procedure Category | Minimum Required | When Logged |
|-------------------|------------------|-------------|
| Joint Injections | 15 | Throughout residency |
| Skin Procedures | 20 | Throughout residency |
| IUD Insertions | 5 | OB/GYN rotation |
| Colposcopy | 5 | OB/GYN rotation |
| Endometrial Biopsy | 3 | OB/GYN rotation |
| Vasectomy | 3 | Procedures rotation |
| Neonatal Circ | 3 | OB/GYN or Peds |

**Scheduling Implications:**
- Procedures rotation must be scheduled PGY-2 or PGY-3
- OB/GYN rotation must include adequate procedure volume clinics
- Track procedure numbers to ensure on-target for graduation

---

## Coverage Requirements

### 1. Minimum Staffing Levels

#### Rotation-Specific Minimums

| Rotation | Minimum Coverage | Target Coverage | Maximum Coverage |
|----------|------------------|-----------------|------------------|
| **FMIT Inpatient** | 3 residents | 4 residents | 5 residents |
| **Emergency Medicine** | 3 residents | 4 residents | 5 residents |
| **Clinic (AM/PM)** | 1 resident | 2 residents | 3 residents |
| **Night Float** | 1 resident | 1 resident | 1 resident |
| **Procedures** | 1 resident | 2 residents | 2 residents |
| **OB (L&D)** | 2 residents | 3 residents | 4 residents |

**Enforcement:**
```python
def validate_coverage(schedule):
    """Ensure all rotations meet minimum coverage."""

    for block in blocks:
        for rotation in rotations:
            coverage = count_assigned(rotation, block)

            if coverage < rotation.min_coverage:
                raise CoverageViolation(
                    f"{rotation.name} Block {block.id}: "
                    f"{coverage} assigned, {rotation.min_coverage} required"
                )
```

### 2. Holiday Coverage

#### Requirement

**Fair distribution of holiday coverage** across all residents.

**Major Holidays:**
- Thanksgiving (4-day weekend)
- Christmas (Dec 24-26)
- New Year's (Dec 31 - Jan 1)
- Independence Day (July 4)

**Fairness Rules:**
- No resident covers >2 major holidays per year
- Rotate holiday assignments year-to-year
- PGY-1 priority for family holidays (with consent)
- Track cumulative holiday burden

**Implementation:**
```python
def assign_holiday_coverage(holiday, year):
    """Assign holiday coverage fairly."""

    # Get residents who worked this holiday last year
    worked_last_year = get_holiday_workers(holiday, year - 1)

    # Deprioritize them this year
    candidates = [
        r for r in residents
        if r not in worked_last_year
        and get_holiday_count(r, year) < 2  # Haven't worked 2 holidays yet
    ]

    # Select from candidates
    selected = select_by_fairness(candidates)
    assign(selected, holiday, 'Holiday_Coverage')

    # Log for next year
    log_holiday_assignment(selected, holiday, year)
```

### 3. Weekend Coverage

#### Requirement

**Equitable weekend distribution** with maximum frequency limits.

**Weekend Coverage:**
- Saturday/Sunday clinic or inpatient coverage
- Rotates among residents not on blocking rotations

**Fairness Rules:**
- No more than 1 weekend per month (on average)
- No back-to-back weekends unless emergency
- Golden weekend (both days off) at least once per month

**Implementation:**
```python
def assign_weekend_coverage(month):
    """Assign weekend coverage for the month."""

    weekends = get_weekends(month)

    for weekend in weekends:
        # Find residents with fewest weekends this month
        candidates = sorted(residents, key=lambda r: get_weekend_count(r, month))

        # Exclude those who worked last weekend
        candidates = [c for c in candidates if not worked_last_weekend(c)]

        # Assign from candidates
        selected = candidates[0]
        assign(selected, weekend, 'Weekend_Coverage')
```

---

## Leave and Absence Policies

### 1. Vacation Leave

#### Allowance

**3 weeks (15 working days) per academic year** for all residents.

**Scheduling Rules:**
- Must be requested 8 weeks in advance (12 weeks preferred)
- Maximum 2 weeks consecutive
- Cannot be taken during FMIT (PGY-1) or other critical rotations
- Must not create coverage gaps
- Subject to approval based on service needs

**Blackout Periods:**
- First month of academic year (orientation/FMIT)
- Board exam period (if applicable)
- High-demand service periods (holiday coverage)

**Implementation:**
```python
def request_vacation(resident, start_date, end_date):
    """Process vacation request."""

    # Calculate days
    days_requested = count_working_days(start_date, end_date)
    days_used = get_vacation_used(resident, academic_year)
    days_remaining = 15 - days_used

    if days_requested > days_remaining:
        raise InsufficientVacationError(
            f"Only {days_remaining} days remaining"
        )

    # Check blackout periods
    if is_blackout_period(resident, start_date, end_date):
        raise BlackoutPeriodError("Vacation not allowed during this period")

    # Check coverage impact
    if creates_coverage_gap(resident, start_date, end_date):
        raise CoverageGapError("Would create critical coverage gap")

    # Create preference with high priority
    create_hard_preference(resident, start_date, end_date, type='VACATION')
```

### 2. Conference Leave

#### Allowance

**Educational conferences encouraged** with time and budget limits.

**Limits:**
- 1 national conference per year (up to 5 days)
- 1 regional conference per year (up to 3 days)
- Research presentation conferences (if applicable)

**Requirements:**
- Submit abstract or educational purpose
- Get Program Director approval
- Arrange coverage for clinical duties
- Submit conference report upon return

**Scheduling:**
- Counts as educational time (NOT vacation)
- Preferred during elective rotations
- Avoid during inpatient/critical rotations

### 3. Sick Leave

#### Policy

**Unlimited sick leave** for legitimate illness (federal policy).

**Requirements:**
- Notify Chief Resident ASAP (ideally night before)
- Notify Program Coordinator for records
- Medical note required if >3 consecutive days
- Cannot be used for non-medical purposes

**Scheduling Impact:**
- Immediate coverage replacement needed
- May affect rotation completion requirements
- Extended sick leave may require rotation extension

### 4. Parental Leave

#### Allowance

**6 weeks parental leave** for primary caregiver (federal military policy).

**Scheduling:**
- Must be taken within 1 year of birth/adoption
- Can be split (e.g., 3 weeks + 3 weeks)
- Requires 30-day notice (or ASAP after unexpected birth)
- Rotation pause - may extend graduation date

**Implementation:**
```python
def schedule_parental_leave(resident, estimated_date, duration_weeks):
    """Block parental leave and adjust rotations."""

    # Block scheduling around due date (±2 weeks)
    buffer_start = estimated_date - timedelta(weeks=2)
    buffer_end = estimated_date + timedelta(weeks=duration_weeks + 2)

    create_blocking_absence(
        resident,
        buffer_start,
        buffer_end,
        type='PARENTAL_LEAVE'
    )

    # Adjust rotation schedule
    pause_rotations(resident, buffer_start, buffer_end)

    # May extend graduation date
    if total_leave_days(resident) > 30:
        flag_for_graduation_extension(resident)
```

---

## Call Schedule Requirements

### 1. Call Equity

#### Requirement

**Fair distribution of call shifts** among residents at same PGY level.

**Metrics:**
- Total call days per block
- Weekend vs. weekday call ratio
- Holiday call distribution
- Night vs. day call ratio

**Fairness Targets:**
| Metric | Target |
|--------|--------|
| Gini coefficient | <0.15 |
| Max/Min ratio | <1.3 |
| Std deviation | <2 days per block |

**Implementation:**
```python
def validate_call_equity(schedule):
    """Check call distribution fairness."""

    for pgy_level in [1, 2, 3]:
        residents = get_residents_by_pgy(pgy_level)
        call_counts = [count_call_days(r) for r in residents]

        gini = calculate_gini(call_counts)
        if gini > 0.15:
            raise CallEquityViolation(
                f"PGY-{pgy_level} call distribution unfair (Gini={gini:.2f})"
            )
```

**See:** `backend/app/scheduling/constraints/call_equity.py`

### 2. Call Frequency

#### Limits

**Maximum call frequency** to prevent burnout.

| Call Type | Maximum Frequency |
|-----------|-------------------|
| 24-hour in-house call | Every 3rd day (ACGME) |
| Weekend call | 2 per month |
| Holiday call | 2 per year (major holidays) |
| Night shift | 6 consecutive max (ACGME) |

---

## Block Structure

### Academic Year Structure

**Annual Schedule:**
- Start: July 1
- End: June 30 (following year)
- Total: 365 days

**Block System:**
- 13 blocks per year
- Each block: 4 weeks (28 days)
- Final block: 29 days (to complete 365)

**Block Calendar Example:**
```
Block 1: Jul 1 - Jul 28 (4 weeks)
Block 2: Jul 29 - Aug 25 (4 weeks)
Block 3: Aug 26 - Sep 22 (4 weeks)
...
Block 13: Jun 3 - Jun 30 (28 days - last block may vary)
```

**Session Structure:**
- Each day has 2 sessions: AM (0800-1200), PM (1300-1700)
- Some rotations use full-day blocks
- Clinic rotations use half-day (AM/PM) scheduling

---

## Special Rotation Rules

### 1. Sports Medicine Rotation

**Unique Requirements:**
- Requires sports medicine fellowship interest
- Not required for all residents
- Variable schedule based on team schedules
- Includes game coverage (evenings/weekends)

**Scheduling:**
- Elective rotation (PGY-2/3 only)
- Variable hours (includes game attendance)
- Weekend coverage for events
- Coordinate with sports medicine faculty

**See:** `backend/app/scheduling/constraints/sports_medicine.py`

### 2. International Health Rotation

**Unique Requirements:**
- Requires advance planning (6-12 months)
- Subject to travel approval
- May require security clearance
- Often 4 weeks (full block)

**Scheduling:**
- Typically PGY-3 year
- Cannot be during critical service months
- Requires backup coverage plan
- Subject to deployment status

---

## Monitoring and Compliance

### Weekly Checks

**Program Coordinator reviews:**
- [ ] Upcoming week coverage complete
- [ ] No ACGME violations forecasted
- [ ] Leave requests approved/denied
- [ ] Call schedule balanced

### Monthly Reviews

**Program Director reviews:**
- [ ] Rotation completion on track
- [ ] Procedure numbers adequate
- [ ] Fairness metrics (Gini, call equity)
- [ ] Resident concerns addressed

### Quarterly Reviews

**Curriculum Committee reviews:**
- [ ] Rotation requirements met
- [ ] Educational goals on track
- [ ] Policy compliance
- [ ] Schedule optimization opportunities

---

## Policy Override Authority

| Policy | Override Authority | Documentation Required |
|--------|-------------------|------------------------|
| ACGME Rules | None | N/A (cannot override) |
| FMIT Sequencing | Program Director | Educational justification |
| Coverage Minimums | Program Director | Safety plan |
| Vacation Limits | Program Coordinator | Special circumstances memo |
| Call Equity | Chief Resident | Fairness analysis |
| Holiday Coverage | Program Coordinator | Resident consent |

---

## References

- TAMC Family Medicine Residency Policy Manual
- ACGME Common Program Requirements (see `acgme-rules.md`)
- Military Personnel Policies (MILPER messages)
- System implementation: `backend/app/scheduling/constraints/`

---

**Document Version:** 1.0
**Last Updated:** December 2025
**Maintained By:** Program Coordinator
**Review Frequency:** Annually
