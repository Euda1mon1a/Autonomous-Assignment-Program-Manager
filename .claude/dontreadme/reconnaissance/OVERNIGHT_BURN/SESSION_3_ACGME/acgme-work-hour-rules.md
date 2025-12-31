# ACGME Work Hour Rules - Complete Implementation Inventory

**Search Party Operation:** G2_RECON
**Target:** ACGME Work Hour Compliance
**Generated:** 2025-12-30
**Scope:** Complete rule mapping, code location registry, edge case documentation

---

## EXECUTIVE SUMMARY

This document provides a **complete inventory of ACGME work hour rules** implemented in the Residency Scheduler system. It includes:

1. **Core ACGME Rules** - The 4 regulatory pillars
2. **Code Location Mapping** - Where each rule is implemented
3. **Implementation Details** - Constants, formulas, validation logic
4. **Edge Cases** - Special scenarios and handling
5. **Compliance Verification Checklist** - Pre-deployment validation

---

## PART 1: CORE ACGME RULES INVENTORY

### Rule 1: 80-Hour Maximum Work Week

**ACGME Standard:**
> "Duty hours are limited to 80 hours per week, averaged over a four-week period, inclusive of all in-house clinical and educational activities." — Common Program Requirements, Section VI.F.1

**Mathematical Definition:**
```
4-week rolling average ≤ 80 hours/week
Equivalently: 28-consecutive-day window total ≤ 320 hours
```

**Implementation Constants:**

| Constant | Value | Definition |
|----------|-------|-----------|
| `MAX_WEEKLY_HOURS` | 80 | Hard limit per week |
| `ROLLING_WEEKS` | 4 | Averaging period in weeks |
| `ROLLING_DAYS` | 28 | Exact days in averaging window (strict) |
| `HOURS_PER_BLOCK` | 6 | Hours assigned per half-day block (AM/PM) |
| `MAX_BLOCKS_PER_WINDOW` | 53 | Maximum blocks in 28-day window: (80×4)/6 = 53.33 → 53 |

**What Counts Toward 80 Hours:**
- Direct patient care activities
- Educational conferences and didactics
- Administrative duties related to patient care
- In-house call time (including sleep during call)
- Moonlighting (internal or external)
- Handoff/transition time (up to 4 hours)

**What Does NOT Count:**
- Personal study and preparation
- Reading medical literature outside work hours
- Voluntary research conducted outside scheduled time

**Calculation Formula:**
```
For any 28-day window starting on date D:
  window_end = D + 27 days
  total_hours = sum(hours_by_date[d] for d in range(D, D+28))
  average_weekly = total_hours / 4

  IF average_weekly > 80:
    VIOLATION detected
```

**Rolling Window Semantics:**
- **Strict rolling:** Check EVERY possible 28-day window
- **Not calendar-based:** Window can start any day, not just Monday
- **Example violation window:** Jan 5 to Feb 1, Jan 6 to Feb 2, etc.
- **Resident assignment implications:** Cannot assign shifts that cause avg > 80 in ANY 28-day window

---

### Rule 2: 1-in-7 Day Off Rule

**ACGME Standard:**
> "Residents must have one day in seven free from all educational and clinical responsibilities, averaged over four weeks." — Common Program Requirements, Section VI.F.3

**Mathematical Definition:**
```
In any 7-day window: At least 1 full 24-hour period off
Averaged over 4 weeks: Minimum 4 complete days off per 28-day period
Simplified approximation: Cannot work more than 6 consecutive calendar days
```

**Implementation Constants:**

| Constant | Value | Definition |
|----------|-------|-----------|
| `MAX_CONSECUTIVE_DAYS` | 6 | Maximum consecutive work days |
| `DAYS_PER_WEEK` | 7 | Standard week length |
| `AVERAGING_WEEKS` | 4 | 4-week averaging period |

**Simplified Implementation Note:**
The code implements the **conservative approximation**: "Cannot work more than 6 consecutive calendar days."

This is simpler than strict interpretation (4 days off in 28 days) but ensures compliance with stricter windowing.

**Calculation Formula:**
```
For resident:
  work_dates = sorted list of dates with assignments

  consecutive_count = 1
  max_consecutive = 1

  FOR each adjacent pair of dates:
    IF date[i+1] - date[i] == 1 day:
      consecutive_count += 1
      max_consecutive = max(max_consecutive, consecutive_count)
    ELSE:
      consecutive_count = 1  # Reset streak

  IF max_consecutive > 6:
    VIOLATION detected
```

**Strict Interpretation (Not Implemented):**
```
28-day periods must contain ≥ 4 complete 24-hour days off
This is more complex to track and would require shift start/end times
Current implementation uses 6-day approximation (conservative)
```

---

### Rule 3: Supervision Ratios

**ACGME Standard:**
> "The program must demonstrate that the appropriate level of supervision is in place for all residents who care for patients." — Common Program Requirements, Section VI.B

**Supervision Requirements by PGY Level:**

| PGY Level | Ratio | Definition | Supervision Type |
|-----------|-------|-----------|-----------------|
| PGY-1 | 1:2 | 1 faculty per 2 residents | Direct/immediate |
| PGY-2 | 1:4 | 1 faculty per 4 residents | Available/remote |
| PGY-3 | 1:4 | 1 faculty per 4 residents | Available/remote |

**Implementation Constants:**

| Constant | Value | Definition |
|----------|-------|-----------|
| `PGY1_RATIO` | 2 | Max residents per faculty (PGY-1) |
| `OTHER_RATIO` | 4 | Max residents per faculty (PGY-2/3) |

**Calculation Formula (Fractional Supervision Load):**
```
supervision_units = (pgy1_count × 2) + (other_count × 1)
required_faculty = ceil(supervision_units / 4)

Alternative ceiling formula:
required_pgy1_faculty = ceil(pgy1_count / 2)
required_other_faculty = ceil(other_count / 4)
required_total = max(required_pgy1_faculty, required_other_faculty)
```

**Example Calculations:**

| Scenario | PGY-1 | PGY-2/3 | Calculation | Required |
|----------|-------|---------|-------------|----------|
| 2 PGY-1 only | 2 | 0 | (2×2 + 0×1)/4 = 1 | 1 faculty |
| 4 PGY-2 only | 0 | 4 | (0×2 + 4×1)/4 = 1 | 1 faculty |
| 1 PGY-1 + 2 PGY-2 | 1 | 2 | (1×2 + 2×1)/4 = 1 | 1 faculty |
| 3 PGY-1 only | 3 | 0 | (3×2 + 0×1)/4 = 1.5 → 2 | 2 faculty |
| 6 residents mixed | 3 | 3 | (3×2 + 3×1)/4 = 2.25 → 3 | 3 faculty |

**Validation Per Block:**
```
FOR each block in schedule:
  residents_assigned = count of resident assignments on block
  pgy1_residents = count of PGY-1 residents on block
  other_residents = residents_assigned - pgy1_residents

  faculty_assigned = count of faculty assignments on block

  required = calculate_required_faculty(pgy1_residents, other_residents)

  IF faculty_assigned < required:
    VIOLATION: Insufficient supervision
```

---

### Rule 4: Availability/Absence Enforcement

**ACGME Standard:**
> Implicit requirement: Residents must only be scheduled during periods when available for duty.

**Types of Absences:**
- Medical leave (illness, disability)
- Vacation/personal time
- Conference attendance
- Deployment/TDY (military context)
- Maternity/family leave
- Other approved absences

**Implementation:**

| Absence Type | Blocks Resident | Penalty | Category |
|--------------|----------------|---------|----------|
| Vacation | Yes (hard) | Violation if assigned | Blocking |
| Medical leave | Yes (hard) | Violation if assigned | Blocking |
| Conference | Contextual | May allow if educational | Soft |
| TDY/Deployment | Yes (hard) | Violation if assigned | Blocking |

**Validation Formula:**
```
FOR each assignment (resident, block):
  IF resident.id in availability_matrix:
    IF availability_matrix[resident.id][block.id]["available"] == False:
      VIOLATION: Assigned during absence
```

---

## PART 2: CODE LOCATION MAPPING

### Primary Implementation Files

#### File 1: Core Constraint Classes
**Path:** `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/services/constraints/acgme.py`

**Contains:**
- `ACGMEConstraintValidator` - High-level validator interface
- `EightyHourRuleConstraint` - 80-hour rule implementation
- `OneInSevenRuleConstraint` - 1-in-7 rule implementation
- `SupervisionRatioConstraint` - Supervision ratio validation
- `AvailabilityConstraint` - Absence/blocking validation
- `SchedulingContext` - Data container for constraints
- `ConstraintResult` - Validation result wrapper

**Key Methods:**
- `validate()` - Post-schedule validation
- `add_to_cpsat()` - OR-Tools solver integration
- `add_to_pulp()` - PuLP linear solver integration

**Lines of Code:** ~993 lines

---

#### File 2: Backward Compatibility Layer
**Path:** `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/scheduling/constraints/acgme.py`

**Purpose:** Re-exports from services layer for backward compatibility

**Contains:**
- All 4 constraint classes (re-exported)
- `ACGMEConstraintValidator` placeholder

**Status:** Legacy import path, new code should use services layer directly

---

#### File 3: Database Validators
**Path:** `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/validators/acgme_validators.py`

**Purpose:** Async validators for database operations

**Contains:**
- `validate_80_hour_rule()` - Database-driven 80-hour checking
- `validate_one_in_seven_rule()` - Database-driven 1-in-7 checking
- `validate_24_plus_4_rule()` - 24+4 shift limit (detailed below)
- `validate_supervision_ratio()` - Database-driven supervision checking
- `validate_post_call_restrictions()` - Post-call rest requirements
- `validate_acgme_compliance()` - Comprehensive validation
- `validate_assignment_acgme_compliance()` - Pre-assignment validation

**Lines of Code:** ~499 lines

---

### Solver Integration Points

#### OR-Tools CP-SAT Integration
**Files Using `add_to_cpsat()`:**
- `backend/app/scheduling/solvers.py` - Solver orchestration
- `backend/app/scheduling/engine.py` - Schedule generation engine
- `backend/app/scheduling/optimizer.py` - Optimization wrapper

**Constraint Addition Pattern:**
```python
constraint = EightyHourRuleConstraint()
constraint.add_to_cpsat(model, variables, context)
```

#### PuLP Linear Programming Integration
**Files Using `add_to_pulp()`:**
- `backend/app/scheduling/pyomo_solver.py` - Pyomo solver integration
- Alternative solver paths for smaller instances

---

### Test Coverage Files

#### Primary Test File
**Path:** `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/tests/validators/test_acgme_comprehensive.py`

**Test Categories:**
- 80-hour rule validation tests
- 1-in-7 rule validation tests
- Supervision ratio validation tests
- Integration tests with multiple constraints
- Edge case tests

#### Scenario Tests
**Path:** `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/tests/scenarios/acgme_violation_scenarios.py`

**Predefined Violation Scenarios:**
- `create_80_hour_violation()` - Resident exceeds 80 hours in week
- `create_1_in_7_violation()` - 14+ consecutive days without rest
- `create_pgy1_supervision_violation()` - 3+ PGY-1 per faculty
- `create_pgy2_supervision_violation()` - 5+ PGY-2/3 per faculty
- `create_unsupervised_pgy1_violation()` - No faculty with PGY-1
- `create_double_booking_violation()` - Same resident in 2 rotations

#### Integration Tests
**Path:** `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/tests/integration/scenarios/test_acgme_enforcement.py`

**Test Scenarios:**
- `test_prevent_80_hour_violation_scenario()` - Prevents 80-hour violations
- `test_enforce_mandatory_day_off_scenario()` - Enforces 1-in-7 rule
- `test_supervision_ratio_enforcement_scenario()` - Supervises correctly

---

## PART 3: IMPLEMENTATION DETAILS

### 80-Hour Rule Implementation Details

#### Calculation Precision
```python
# From EightyHourRuleConstraint.__init__()
max_blocks_per_window = (MAX_WEEKLY_HOURS * ROLLING_WEEKS) // HOURS_PER_BLOCK
# = (80 * 4) // 6
# = 320 // 6
# = 53 blocks (integer division, not ceil)

# Critical: This uses floor division
# 53 blocks × 6 hours = 318 hours (leaves 2-hour margin)
# 54 blocks × 6 hours = 324 hours (exceeds limit by 4 hours)
```

#### Rolling Window Implementation
```python
def _calculate_rolling_average(
    self, hours_by_date: dict, window_start: date
) -> float:
    window_end = window_start + timedelta(days=self.ROLLING_DAYS - 1)

    total_hours = sum(
        hours
        for d, hours in hours_by_date.items()
        if window_start <= d <= window_end  # INCLUSIVE endpoints
    )

    return total_hours / self.ROLLING_WEEKS  # Always divide by 4
```

**Key Implementation Notes:**
1. Window is EXACTLY 28 days (ROLLING_DAYS - 1 = 27 day offset)
2. Endpoints are INCLUSIVE (window_start to window_end, both inclusive)
3. Division always by 4 weeks, regardless of actual day count
4. Hours accumulated per date (not per shift)

#### Constraint Generation Strategy
```python
# From add_to_cpsat():
FOR each possible 28-day window starting date:
  window_blocks = [b for b in blocks if start_date <= b.date <= end_date]

  FOR each resident:
    sum(assignment_vars for resident in window_blocks) <= 53

# This generates O(N_dates × N_residents) constraints
# For 365-day schedule + 10 residents = ~3,650 constraints
```

---

### 1-in-7 Rule Implementation Details

#### Simplified vs. Strict Interpretation

**Current Implementation (Simplified):**
```
Cannot work more than 6 consecutive calendar days
```

**Strict ACGME Interpretation:**
```
In any 4-week period: Must have exactly 4 complete 24-hour days off
More complex tracking of shift start/end times required
```

**Why Simplified?**
- Conservative: Guarantees compliance with strict rule
- Simpler to implement and understand
- Works well with block-based scheduling (not hour-granular)
- Less computational overhead

#### Consecutive Day Tracking
```python
# From validate():
consecutive = 1
max_consecutive = 1

FOR i in range(1, len(sorted_dates)):
    IF (sorted_dates[i] - sorted_dates[i-1]).days == 1:
        consecutive += 1
        max_consecutive = max(max_consecutive, consecutive)
    ELSE:
        consecutive = 1  # Reset on gap

IF max_consecutive > 6:
    VIOLATION
```

**Important:** This checks only ASSIGNED dates, not all calendar dates.

Example:
- Assigned: Mon, Tue, Wed, Thu (4 consecutive days)
- Not assigned: Friday-Sunday
- Assigned: Mon, Tue, Wed (3 more consecutive = 7 total consecutive calendar days!)
- **Violation:** 7 consecutive days with assignment detected

---

### Supervision Ratio Implementation Details

#### Fractional Load Calculation
```python
def calculate_required_faculty(self, pgy1_count: int, other_count: int) -> int:
    # Integer math: PGY-1 = 2 units, PGY-2/3 = 1 unit
    # (4 units = 1 faculty member)
    supervision_units = (pgy1_count * 2) + other_count
    return (supervision_units + 3) // 4 if supervision_units > 0 else 0

# Equivalent to: ceil(supervision_units / 4)
# (supervision_units + 3) // 4 rounds up correctly
```

**Worked Examples:**

| Input | Calculation | Result | Interpretation |
|-------|-------------|--------|-----------------|
| (1, 0) | (1×2 + 0 + 3)//4 = 5//4 | 1 faculty | 1 PGY-1 alone |
| (2, 0) | (2×2 + 0 + 3)//4 = 7//4 | 1 faculty | 2 PGY-1 together |
| (3, 0) | (3×2 + 0 + 3)//4 = 9//4 | 2 faculty | 3 PGY-1 need 2 faculty |
| (0, 4) | (0 + 4 + 3)//4 = 7//4 | 1 faculty | 4 PGY-2/3 together |
| (0, 5) | (0 + 5 + 3)//4 = 8//4 | 2 faculty | 5 PGY-2/3 need 2 faculty |
| (1, 2) | (1×2 + 2 + 3)//4 = 7//4 | 1 faculty | Mixed: 1 PGY-1 + 2 PGY-2/3 |
| (2, 2) | (2×2 + 2 + 3)//4 = 9//4 | 2 faculty | Mixed: 2 PGY-1 + 2 PGY-2/3 |

#### Per-Block Validation
```python
# From validate():
by_block = group assignments by block_id

FOR each block:
  residents = [a.person_id for a in assignments if a.type == "resident"]
  faculty = [a.person_id for a in assignments if a.type == "faculty"]

  pgy1_count = count residents with pgy_level == 1
  other_count = len(residents) - pgy1_count

  required = calculate_required_faculty(pgy1_count, other_count)

  IF len(faculty) < required:
    VIOLATION
```

---

## PART 4: EDGE CASES & SPECIAL SCENARIOS

### Edge Case 1: Midnight Window Crossing

**Scenario:**
Resident works 24-hour shift from 6pm to 6pm next day. How many "duty days" does this count?

**Implementation:**
```
Block-based system counts calendar dates
6pm Mon to 6pm Tue shift occupies:
  - Monday block (date = Mon)
  - Tuesday block (date = Tue)
  = 2 calendar days

This is CORRECT per ACGME standards:
"At least one day in seven free" counts calendar days
```

**Implications:**
- Night shifts that span midnight are counted as 2 calendar days
- This is conservative and ensures compliance

---

### Edge Case 2: Exactly 80 Hours

**Scenario:**
Resident averages exactly 80.0 hours per week. Is this compliant?

**Implementation:**
```python
IF average_weekly_hours > MAX_WEEKLY_HOURS:  # > 80, NOT >=
    VIOLATION

# Therefore: 80.0 hours exactly = COMPLIANT ✓
# 80.1 hours = VIOLATION ✗
```

**Floating Point Precision:**
```python
# Example calculation:
total_hours = 320  # 80 hours/week * 4 weeks
average_weekly = 320 / 4  # = 80.0
IF 80.0 > 80:  # False, no violation
```

---

### Edge Case 3: Partial Windows at Schedule Boundaries

**Scenario:**
Schedule ends on day 25 of a 28-day window. Should we allow this?

**Current Implementation:**
```python
# Checks EVERY possible 28-day window within data
# If no complete 28-day window exists at end, no constraint added
# Result: Last few days may appear to exceed 80-hour limit temporarily

# This is ACCEPTABLE because:
# 1. Next schedule block will re-validate
# 2. Typically generates 365-day schedules (covers multiple 28-day windows)
```

---

### Edge Case 4: Leap Year & 365/366 Day Schedules

**Scenario:**
Does the system handle Feb 29 (leap year) correctly?

**Current Implementation:**
```python
# Uses Python's timedelta(days=28) which is calendar-aware
# Feb 29 is treated like any other date
# Leap year February = 29 days (correctly included)

# Validation: For leap year:
# Schedule period = Jan 1 to Dec 31 next year = 366 days
# Includes extra day in Feb naturally
# No special handling needed
```

---

### Edge Case 5: Moonlighting Hours

**Current Status:** DOCUMENTED but NOT ENFORCED

**From ACGME Requirements:**
> "All moonlighting (internal or external) must be counted toward the 80-hour weekly limit."

**System Implementation:**
```python
# Database field exists: Person.moonlighting_hours
# NOT currently included in 80-hour calculation
# TODO: Integrate moonlighting hours into rolling average

# Current limitation:
# HOURS_PER_BLOCK = 6 (fixed for in-house duty)
# Moonlighting must be added separately if tracked
```

**Compliance Gap:**
- If resident works 70 hours scheduled + 15 hours moonlighting = 85 hours
- System would show 70 hours (70 < 80) ✗ COMPLIANT per system
- But actual = 85 hours ✗ ACGME VIOLATION

**Recommendation:**
- Integrate `Person.moonlighting_hours` field into 80-hour calculation
- Track as separate variable in constraint equations
- Add validator to sum scheduled + moonlighting hours

---

### Edge Case 6: Post-Call Day Restrictions (24+4 Rule)

**ACGME Standard:**
> "Residents may work a maximum of 24 consecutive hours of clinical duty. An additional 4 hours is permitted for continuity of care and educational activities (total 28 hours maximum). After 24 hours on duty, residents must have at least 10 hours free of duty."

**Current Implementation Status:** PARTIAL/DOCUMENTED ONLY

```python
# From validate_24_plus_4_rule():
# Simplified check: If more than 2 blocks on same day -> violation flag
# NOT a true 24+4 implementation (would need shift start/end times)

# Database structure supports it:
# Shift.start_time, Shift.end_time fields exist
# But scheduler uses block-based (AM/PM) not hour-granular
```

**Gap:** Block model (6-hour AM/PM) doesn't track minute-level precision needed for 24+4 enforcement

**Workaround:** Post-call day (DO = Direct Observation, PCAT = Post-Call Attending) auto-assignment ensures rest after overnight call

---

### Edge Case 7: Absence During Peak Period

**Scenario:**
Resident approved for vacation during busiest rotation. How is this handled?

**Implementation:**
```python
# Availability enforcement = HARD CONSTRAINT
# If resident.availability[block.id]["available"] == False
#   => assignment_var == 0 (forced)

# No override or exception mechanism
# Vacation blocking is absolute

# Consequence:
# Vacation period = unscheduled capacity gap
# May cause other residents to exceed limits
```

**Mitigation Strategies:**
1. Plan vacations during lower-acuity rotations
2. Hire temporary locum coverage
3. Adjust other residents' schedules with solver
4. Request ACGME exception for continuity (documented)

---

### Edge Case 8: Multiple Overlapping Constraints

**Scenario:**
How does system resolve conflicts between:
- 80-hour rule (max block count per window)
- 1-in-7 rule (max 6 consecutive days)
- Supervision ratio (minimum faculty per block)

**Implementation:**
```python
# All constraints are HARD (high priority)
# Solver uses constraint hierarchy:
# 1. Availability (blocking absences) - CRITICAL
# 2. Supervision (patient safety) - CRITICAL
# 3. 80-Hour rule (ACGME) - CRITICAL
# 4. 1-in-7 rule (ACGME) - CRITICAL
# 5. Other operational constraints - HIGH/MEDIUM

# If constraints are mutually infeasible:
# Solver fails (no valid schedule exists)
# Administrator must:
# - Hire more faculty
# - Adjust rotation template hours
# - Extend schedule period
# - Request ACGME exception
```

**Example Infeasibility:**
```
4 residents, 1 faculty (violates 1:2 supervision ratio)
Resident schedule: 80 hours/week already
Cannot add any shifts due to 80-hour limit
Cannot remove supervision due to hard constraint
=> INFEASIBLE PROBLEM
```

---

## PART 5: COMPLIANCE VERIFICATION CHECKLIST

### Pre-Deployment Validation

#### ✅ Static Code Analysis

- [ ] All 4 constraint classes implemented
  - [ ] `EightyHourRuleConstraint` with rolling window logic
  - [ ] `OneInSevenRuleConstraint` with consecutive day tracking
  - [ ] `SupervisionRatioConstraint` with PGY-level ratios
  - [ ] `AvailabilityConstraint` with absence blocking

- [ ] Constants correctly defined
  - [ ] `MAX_WEEKLY_HOURS = 80`
  - [ ] `ROLLING_DAYS = 28` (strict, not 28.5 or 4 weeks)
  - [ ] `MAX_CONSECUTIVE_DAYS = 6`
  - [ ] `PGY1_RATIO = 2, OTHER_RATIO = 4`
  - [ ] `HOURS_PER_BLOCK = 6`

- [ ] Math verified for max blocks
  - [ ] `(80 * 4) // 6 = 53` (not 54)
  - [ ] Formula correctly floors to prevent overflow

#### ✅ Unit Test Validation

- [ ] 80-Hour Rule Tests
  - [ ] Single resident working exactly 80 hours: COMPLIANT
  - [ ] Single resident working 80.1 hours: VIOLATION ✗
  - [ ] 28-day window total of 320 hours: COMPLIANT
  - [ ] 28-day window total of 321 hours: VIOLATION ✗
  - [ ] Multiple overlapping 28-day windows: All checked
  - [ ] Partial window at schedule boundary: Graceful handling

- [ ] 1-in-7 Rule Tests
  - [ ] 6 consecutive days: COMPLIANT
  - [ ] 7 consecutive days: VIOLATION ✗
  - [ ] 6 + 1 day off + 6: COMPLIANT (reset after gap)
  - [ ] Averaging over 4 weeks: Correctly tracks

- [ ] Supervision Tests
  - [ ] 1 PGY-1 + 1 faculty: COMPLIANT
  - [ ] 3 PGY-1 + 1 faculty: VIOLATION ✗
  - [ ] 4 PGY-2/3 + 1 faculty: COMPLIANT
  - [ ] 5 PGY-2/3 + 1 faculty: VIOLATION ✗
  - [ ] Mixed (1 PGY-1 + 2 PGY-2/3) + 1 faculty: COMPLIANT

- [ ] Availability Tests
  - [ ] Assignment during vacation: VIOLATION ✗
  - [ ] Assignment during approved absence: VIOLATION ✗
  - [ ] Assignment during available period: COMPLIANT

#### ✅ Integration Tests

- [ ] End-to-end schedule generation with all 4 constraints
- [ ] Solver feasibility when constraints are compatible
- [ ] Solver infeasibility detection when constraints conflict
- [ ] Validation after solver completion matches constraint rules

#### ✅ Edge Case Coverage

- [ ] Leap year handling (366-day schedules)
- [ ] Midnight-crossing shifts (2 calendar days)
- [ ] Exactly 80.0 hours boundary
- [ ] Partial windows at schedule boundaries
- [ ] Floating-point precision in hour calculations
- [ ] Empty schedule (0 blocks): No errors
- [ ] Single resident: Correct calculation
- [ ] 100+ residents: Solver performance acceptable

#### ✅ Database Validation

- [ ] All assignments have person_id, block_id, rotation_template_id
- [ ] Block dates are valid (no nulls, no future dates outside schedule)
- [ ] Person records have pgy_level field for supervision
- [ ] Availability matrix properly populated
- [ ] No duplicate assignments for same (person, block, template)

#### ✅ Performance Validation

- [ ] 365-day schedule + 50 residents: Generate < 5 minutes
- [ ] Constraint evaluation < 100ms for validation
- [ ] Rolling window loop doesn't O(n³) explode
- [ ] Memory usage < 2GB for large problems

#### ✅ Compliance Documentation

- [ ] ACGME reference citations correct
- [ ] Constants linked to ACGME standards
- [ ] Calculation formulas documented
- [ ] Limitations and gaps identified
- [ ] Simplified vs. strict interpretation documented

---

## PART 6: KNOWN LIMITATIONS & GAPS

### Gap 1: Moonlighting Hours Not Integrated

**Status:** Partially implemented
**Severity:** HIGH (ACGME requirement not enforced)
**Required Fix:**
```python
# In EightyHourRuleConstraint:
# Add moonlighting_hours to total_hours calculation
total_hours = sum(hours_by_date[d]) + resident.moonlighting_hours
```

---

### Gap 2: 24+4 Rule Not Enforced

**Status:** Documented, not enforced
**Severity:** MEDIUM (simplified block model is conservative approximation)
**Required Fix:**
```python
# Need shift start/end time tracking
# Current 6-hour blocks insufficient for minute-level precision
# Alternative: Enforce via post-call day auto-assignment (implemented)
```

---

### Gap 3: No Backup Call Counting

**Status:** Not implemented
**Severity:** MEDIUM (rare scenario)
**ACGME Requirement:**
> "When residents are on backup call (second call), time spent counts only if activated."

**Gap:** No distinction between primary and backup call in current model

---

### Gap 4: Strategic Patient Care Exception

**Status:** Not implemented
**Severity:** LOW (rare, requires documentation)
**ACGME Requirement:**
> "In rare circumstances, residents may exceed duty hour limits for continuity of care. Must be reviewed and documented."

**Gap:** System prevents all violations; no exception mechanism

---

### Gap 5: Handoff Time Precision

**Status:** Approximate (4-hour block included in 6-hour HOURS_PER_BLOCK)
**Severity:** LOW (conservative)
**Current Logic:**
```
- Standard duty: 12 hours/block (not 6)  <- CONTRADICTION IN DOCS
- Post-call handoff: +4 hours (approximate)
- Total: Can reach 28 hours
```

**Note:** Actual hours/block definition should be clarified in code vs. documentation.

---

## PART 7: REGULATORY EVOLUTION & CONTEXT

### ACGME Rule History

| Year | Major Change | Impact |
|------|-------------|--------|
| 2003 | 80-hour rule introduced | Foundation of modern duty hour limits |
| 2011 | Strengthened 1-in-7, added 16-hour PGY-1 limit | Enhanced resident protections |
| 2017 | Adjusted call frequency (every 3rd night), clarified handoff time | Operational clarification |
| 2023 | Reinforced supervision ratios, added telehealth considerations | Current requirements |

### PGY-1 Specific Restrictions (Not Fully Implemented)

**Requirement:**
> "PGY-1 residents limited to 16 consecutive hours (with exceptions)"

**System Status:** NOT ENFORCED
- Applies to PGY-1 only, not other levels
- More restrictive than 24-hour rule for first-year residents
- Would require separate constraint class

---

## SUMMARY TABLE: RULES VS. IMPLEMENTATION STATUS

| Rule | Constraint Class | Status | Strictness | Notes |
|------|------------------|--------|-----------|-------|
| 80-Hour Limit | `EightyHourRuleConstraint` | ✅ IMPLEMENTED | Strict rolling window | All 28-day windows checked |
| 1-in-7 Day Off | `OneInSevenRuleConstraint` | ✅ IMPLEMENTED | Conservative | Approximates with 6-day max |
| Supervision | `SupervisionRatioConstraint` | ✅ IMPLEMENTED | Strict by PGY level | Fractional load calculation |
| Availability | `AvailabilityConstraint` | ✅ IMPLEMENTED | Absolute blocking | Absence = no assignment |
| 24+4 Rule | Partial (`post_call.py`) | ⚠️ PARTIAL | Approximate | Block-based, not hour-granular |
| Moonlighting | `validate_80_hour_rule()` | ⚠️ DOCUMENTED | Not enforced | Gap in calculation |
| PGY-1 16-hour limit | NONE | ❌ NOT IMPLEMENTED | N/A | Separate rule for first-year |
| Backup call | NONE | ❌ NOT IMPLEMENTED | N/A | Rare scenario |
| Strategic exception | NONE | ❌ NOT IMPLEMENTED | N/A | Requires override mechanism |

---

## REFERENCES

### Code Files (Absolute Paths)

1. **Primary Constraint Implementation:**
   `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/services/constraints/acgme.py`

2. **Legacy Re-Export:**
   `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/scheduling/constraints/acgme.py`

3. **Database Validators:**
   `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/validators/acgme_validators.py`

4. **Documentation:**
   `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docs/rag-knowledge/acgme-rules.md`

### Official ACGME References

- **Common Program Requirements:**
  https://www.acgme.org/globalassets/pfassets/programrequirements/cprresidency_2022v3.pdf

  Section VI (Fatigue Mitigation and Duty Hours):
  - VI.F.1 - 80-hour rule
  - VI.F.3 - 1-in-7 rule
  - VI.B - Supervision ratios

---

**Document Status:** Complete reconnaissance operation
**Confidence Level:** HIGH (based on direct code analysis)
**Last Updated:** 2025-12-30
**Author:** G2_RECON Signal Amplification Team
