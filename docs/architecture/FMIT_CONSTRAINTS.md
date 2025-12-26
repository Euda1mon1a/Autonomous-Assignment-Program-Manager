# FMIT Constraints Reference

This document describes all constraints related to Family Medicine Inpatient Teaching (FMIT) rotations.

---

## FMIT Week Structure

FMIT weeks run **Friday to Thursday**, independent of calendar weeks or academic blocks.

```
Fri  Sat  Sun  Mon  Tue  Wed  Thu
 |    |    |    |    |    |    |
 +------------ FMIT Week -----------+
 |                                  |
 v                                  v
Start                            End
```

### Faculty FMIT Week

When faculty is assigned FMIT for a week:
- **All blocks** during that week are FMIT activity
- **Blocked from** regular clinic assignments
- **Blocked from** overnight call Sunday-Thursday
- **Must take** Friday night and Saturday night call (mandatory)
- **Post-FMIT Friday** is blocked for recovery

### Resident FMIT Week

Residents on FMIT work **6 days per week**:
- No post-call recovery day
- Use templates: "Family Medicine Inpatient Team Intern" (FMI), "Family Medicine Inpatient Team Resident" (FMIT-R)

---

## Faculty vs Resident: Template Matching

The constraint system distinguishes faculty from residents based on template name:

```python
is_fmit = (
    hasattr(template, "activity_type")
    and template.activity_type == "inpatient"
    and hasattr(template, "name")
    and "FMIT" in template.name.upper()
)
```

| Template Name | Contains "FMIT"? | Who Uses It |
|---------------|------------------|-------------|
| FMIT AM | Yes | **Faculty** |
| FMIT PM | Yes | **Faculty** |
| Family Medicine Inpatient Team Intern | No | Residents (PGY-1) |
| Family Medicine Inpatient Team Resident | No | Residents (PGY-2/3) |

This means **post-FMIT constraints only apply to faculty**.

---

## Constraints

### 1. FMITWeekBlockingConstraint

**Type:** Hard Constraint
**Priority:** Critical
**Location:** `backend/app/scheduling/constraints/fmit.py:75`

Blocks clinic and Sun-Thurs call during FMIT week.

**Rules:**
- Block all clinic (outpatient) templates for FMIT faculty
- Block overnight call assignments Sunday through Thursday
- Friday and Saturday call are handled by FMITMandatoryCallConstraint

**Validation:** Fails if faculty assigned to clinic or Sun-Thurs call during FMIT week.

---

### 2. FMITMandatoryCallConstraint

**Type:** Hard Constraint
**Priority:** Critical
**Location:** `backend/app/scheduling/constraints/fmit.py:312`

Ensures FMIT attending covers Friday and Saturday night call.

**Rules:**
- FMIT faculty MUST take Friday night call
- FMIT faculty MUST take Saturday night call
- Prevents need for additional call coverage when FMIT attending is on-site

**Validation:** Fails if FMIT faculty not assigned Fri/Sat call.

---

### 3. PostFMITRecoveryConstraint

**Type:** Hard Constraint
**Priority:** High
**Location:** `backend/app/scheduling/constraints/fmit.py:468`

Blocks the Friday after FMIT week for recovery.

**Timeline:**
```
Thu (FMIT ends) → Fri (BLOCKED) → Sat → Sun
                      ^
                      |
              Recovery Day (PC)
```

**Rules:**
- Friday after FMIT Thursday is completely blocked
- No outpatient assignments
- No call assignments

**Why Faculty Only:**
- Template name matching only catches "FMIT AM/PM"
- Resident templates don't match the pattern
- Residents work 6 days/week on FMIT with no PC

**Note:** This constraint was missing from the default constraint manager until 2025-12-26.

---

### 4. PostFMITSundayBlockingConstraint

**Type:** Hard Constraint
**Priority:** High
**Location:** `backend/app/scheduling/constraints/fmit.py:671`

Blocks Sunday call immediately after FMIT week.

**Timeline:**
```
Thu (FMIT ends) → Fri (PC) → Sat (OK) → Sun (NO CALL)
                                              ^
                                              |
                                        Blocked for call
```

**Rules:**
- Faculty gets Friday recovery (PostFMITRecoveryConstraint)
- Saturday is normal availability
- Sunday call is blocked (this constraint)

**Rationale:** Even after Friday recovery, Sunday call is too soon after demanding FMIT week.

---

### 5. FMITContinuityTurfConstraint

**Type:** Hard Constraint (informational)
**Priority:** High
**Location:** `backend/app/scheduling/constraints/fmit.py:854`

FMIT continuity delivery turf rules based on system load.

**Load Shedding Levels:**

| Level | Name | Continuity Policy |
|-------|------|-------------------|
| 0 | NORMAL | FM attends all continuity deliveries |
| 1 | YELLOW | FM attends all (yellow alert) |
| 2 | ORANGE | FM preferred, OB acceptable |
| 3 | RED | OB covers most, FM if available |
| 4 | BLACK | All continuity to OB - FM essential services only |

**Note:** This is primarily a reporting/validation constraint. Turf decisions are made dynamically at runtime.

---

### 6. FMITStaffingFloorConstraint

**Type:** Hard Constraint
**Priority:** Critical
**Location:** `backend/app/scheduling/constraints/fmit.py:965`

Ensures minimum faculty available before FMIT assignments.

**Thresholds:**
- `MINIMUM_FACULTY_FOR_FMIT = 5` - Below this, NO FMIT assignments
- `FMIT_UTILIZATION_CAP = 0.20` - Max 20% of faculty on FMIT simultaneously

**Examples:**
- 4 faculty total: NO FMIT allowed (below minimum)
- 5 faculty total: Max 1 FMIT (5 × 0.20 = 1)
- 10 faculty total: Max 2 FMIT (10 × 0.20 = 2)
- 15 faculty total: Max 3 FMIT (15 × 0.20 = 3)

**Rationale:** Prevents "PCS season" scenario where FMIT assignment would overload remaining faculty during staffing shortages.

---

## Constraint Registration

All FMIT constraints must be registered in the constraint manager:

```python
# backend/app/scheduling/constraints/manager.py

from .fmit import (
    PostFMITRecoveryConstraint,
    PostFMITSundayBlockingConstraint,
)

# In create_default():
manager.add(PostFMITRecoveryConstraint())
manager.add(PostFMITSundayBlockingConstraint())
```

**Warning:** If a constraint class exists but isn't added to the manager, it will NOT be enforced during scheduling.

---

## Helper Functions

### `get_fmit_week_dates(any_date: date) -> tuple[date, date]`

Returns the Friday-Thursday FMIT week containing the given date.

```python
friday_start, thursday_end = get_fmit_week_dates(some_date)
```

### `is_sun_thurs(any_date: date) -> bool`

Returns True if date is Sunday through Thursday (call blocking days during FMIT).

---

## Related Documentation

- [Activity Types](ACTIVITY_TYPES.md) - How FMIT templates are classified
- [Engine Assignment Flow](ENGINE_ASSIGNMENT_FLOW.md) - How FMIT assignments are preserved
- [Faculty Scheduling Specification](FACULTY_SCHEDULING_SPECIFICATION.md) - Full faculty rules
