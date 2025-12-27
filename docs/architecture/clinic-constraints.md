# Clinic Scheduling Constraints

This document captures all clinic-specific scheduling constraints, including implemented, planned, and deferred features.

## Overview

The clinic has unique operational requirements beyond standard ACGME rules:
- Physical space limitations
- Continuity clinic protection (Wednesday mornings)
- Faculty coverage requirements
- Special "inverted" schedule days

---

## Implemented Constraints

### 1. MaxPhysiciansInClinicConstraint (Hard Constraint)

**Status:** Implemented

**Rule:** Maximum 6 physicians (faculty + residents combined) in clinic at any one time.

**Rationale:** Physical space limitation - the clinic can only accommodate 6 providers simultaneously.

**Implementation:**
- Counts ALL persons assigned to clinic templates per block (regardless of role)
- Applies to both AM and PM sessions independently
- Hard constraint: violations make schedule infeasible

```python
# Pseudocode
for each block:
    clinic_count = count(assignments where template.activity_type == 'clinic')
    assert clinic_count <= 6
```

### 2. WednesdayAMInternOnlyConstraint (Hard Constraint)

**Status:** Implemented

**Rule:** Wednesday morning clinic sessions should be staffed by interns (PGY-1) only, with rare exceptions.

### 3. FacultyPrimaryDutyClinicConstraint (Hard Constraint)

**Status:** Implemented (2025-12-27)

**Rule:** Faculty clinic assignments must respect per-faculty min/max half-days per week defined in Airtable primary duty configuration.

**Rationale:** Different faculty members have different clinical responsibilities based on their primary duty (role + individual adjustments). The Airtable configuration provides more granular control than role-based defaults.

**Implementation:**
- Loads configuration from `docs/schedules/sanitized_primary_duties.json`
- Enforces `Clinic Minimum Half-Days Per Week` (coverage requirement)
- Enforces `Clinic Maximum Half-Days Per Week` (capacity limit)
- Evaluated per calendar week (Monday-Sunday)

See [primary-duty-constraints.md](primary-duty-constraints.md) for full documentation.

### 4. FacultyDayAvailabilityConstraint (Hard Constraint)

**Status:** Implemented (2025-12-27)

**Rule:** Faculty can only be assigned to clinic on their available days, as defined in Airtable primary duty configuration.

**Rationale:** Faculty have administrative duties, teaching commitments, or other obligations that make them unavailable on certain days of the week.

**Implementation:**
- Reads `availableMonday` through `availableFriday` flags from primary duty config
- Blocks clinic assignments on unavailable days
- Priority: CRITICAL (violations make schedule infeasible)

See [primary-duty-constraints.md](primary-duty-constraints.md) for full documentation.

### 5. FacultyClinicEquitySoftConstraint (Soft Constraint)

**Status:** Implemented (2025-12-27)

**Rule:** Optimize toward target clinic coverage (midpoint of min/max from primary duty config).

**Implementation:**
- Calculates target as `(min + max) // 2`
- Penalizes deviation from target (soft constraint with weight 15.0)
- Does not make schedule infeasible

See [primary-duty-constraints.md](primary-duty-constraints.md) for full documentation.

---

## Planned Constraints (Phase 2)

### 6. ClinicContinuityConstraint (Hard Constraint)

**Status:** Planned

**Rule:** Clinic must remain "open" every day. At least one faculty member must be present during each clinic session.

**Rationale:** Patient care continuity requires the clinic to be staffed at all times.

**Specific Requirements:**
- At least 1 faculty with `role="supervising"` per clinic session
- Applies to all weekday AM and PM blocks

### 4. WednesdayPMFacultyCoverageConstraint (Hard + Soft)

**Status:** Planned

**Rule:** One faculty member must cover Wednesday PM clinic while all others attend academics/lecture.

**Components:**
- **Hard:** Exactly 1 faculty assigned to Wednesday PM clinic
- **Soft (Equity):** Wednesday PM clinic duty should be evenly distributed among faculty over the academic year

**Rationale:** Wednesday PM is protected academic time (lectures, conferences). Clinic must remain open, so one faculty rotates through coverage duty.

### 5. FourthWednesdayInvertedScheduleConstraint (Hard Constraint)

**Status:** Planned

**Rule:** Every 4th (final) Wednesday of each academic BLOCK has an "inverted" schedule:
- Morning: Academics/lecture (instead of clinic)
- Afternoon: Advising time (instead of academics)
- Clinic must remain open with faculty coverage

**Requirements:**
- One faculty in clinic AM
- A **different** faculty in clinic PM
- The AM and PM faculty must be different people

**Implementation Approach:**
1. Identify 4th Wednesday of each 4-week block (not calendar month)
2. Create `DifferentPersonConstraint` for AM vs PM slots
3. Ensure minimum coverage (1 faculty each session)

```python
# Identifying 4th Wednesday of a block
def get_fourth_wednesday(block_start_date: date) -> date:
    """
    Find the 4th Wednesday within a 4-week academic block.
    Block structure: 28 days starting from block_start_date.
    """
    current = block_start_date
    wednesday_count = 0

    while (current - block_start_date).days < 28:
        if current.weekday() == 2:  # Wednesday
            wednesday_count += 1
            if wednesday_count == 4:
                return current
        current += timedelta(days=1)
    return None  # Should not happen in a 4-week block
```

---

## Deferred Constraints (Phase 3)

### 6. TimeVaryingSupervisionRatioConstraint

**Status:** Deferred - Document only

**Rule:** Supervision ratios vary by academic year half:

| Period | Intern (PGY-1) Ratio | PGY-2/3 Ratio | Notes |
|--------|---------------------|---------------|-------|
| H1 (Blocks 1-6, July-Dec) | 1:2 | 1:4 | Faculty must physically see patients |
| H2 (Blocks 7-13, Jan-June) | 1:3 | 1:4 | Interns more independent |

**Current Approach:** Use 1:2 for all PGY-1 year-round. This is conservative (over-staffed in H2) but safe.

**Why Deferred:**
- Adds significant complexity to supervision calculations
- Every block needs to know "which half of the year am I in?"
- Testing becomes more complex (need to test both halves)
- Current 1:2 ratio is safe failure mode

**Future Implementation Notes:**
- Add `academic_half` computed property to Block model
- Modify `SupervisionRatioConstraint.calculate_required_faculty()` to accept block context
- Consider making ratios configurable in ApplicationSettings

---

## Constraint Interaction Matrix

| Constraint | Interacts With | Notes |
|------------|----------------|-------|
| MaxPhysiciansInClinic | ClinicCapacity | Both limit clinic occupancy, different scopes |
| WednesdayAMInternOnly | SupervisionRatio | Interns still need faculty supervision |
| ClinicContinuity | WednesdayPMCoverage | Both ensure clinic stays open |
| FourthWednesdayInverted | ClinicContinuity, Equity | Complex interaction, different faculty AM/PM |
| TimeVaryingSupervision | All supervision constraints | Would change ratio calculations |

---

## Configuration

### Current Settings (ApplicationSettings)

```python
pgy1_supervision_ratio = "1:2"  # Static, does not vary by half
pgy2_supervision_ratio = "1:4"
pgy3_supervision_ratio = "1:4"
```

### Proposed Future Settings

```python
# Phase 2
clinic_max_physicians = 6
wednesday_am_intern_only = True
wednesday_am_exceptions = []  # List of exception dates

# Phase 3 (deferred)
h1_pgy1_ratio = "1:2"
h2_pgy1_ratio = "1:3"
```

---

## Testing Strategy

### Unit Tests Required

1. **MaxPhysiciansInClinicConstraint**
   - Test with 5 physicians (pass)
   - Test with 6 physicians (pass at limit)
   - Test with 7 physicians (fail)
   - Test faculty + residents combined counting

2. **WednesdayAMInternOnlyConstraint**
   - Test PGY-1 on Wednesday AM (pass)
   - Test PGY-2 on Wednesday AM (fail)
   - Test PGY-1 on Wednesday PM (pass - no restriction)
   - Test PGY-2 on Monday AM (pass - no restriction)

3. **Integration Tests**
   - Full schedule generation with all constraints enabled
   - Verify constraint interactions don't cause infeasibility

---

## References

- ACGME Common Program Requirements, Section VI.B (Supervision)
- `backend/app/scheduling/constraints.py` - Main constraint implementations
- `backend/app/models/block.py` - Block model with date/time fields
- `backend/app/services/academic_block_service.py` - Academic block organization
