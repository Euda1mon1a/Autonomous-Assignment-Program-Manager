# Faculty Scheduling Specification

> **Version:** 1.0
> **Created:** 2025-12-19
> **Status:** Approved specification for implementation

This document defines the complete scheduling parameters for faculty roles, FMIT coverage, call assignments, and coordination requirements.

---

## Table of Contents

1. [Faculty Roles and Clinic Requirements](#faculty-roles-and-clinic-requirements)
2. [Activity Types](#activity-types)
3. [FMIT (Inpatient Attending) Rules](#fmit-inpatient-attending-rules)
4. [Call Schedule Rules](#call-schedule-rules)
5. [Sports Medicine Coordination](#sports-medicine-coordination)
6. [Post-Call Rules](#post-call-rules)
7. [Supervision Ratios](#supervision-ratios)
8. [Current Faculty Roster](#current-faculty-roster)
9. [Implementation Requirements](#implementation-requirements)

---

## Faculty Roles and Clinic Requirements

### Role Definitions

| Role | Clinic Half-Days/Week | SM Clinic/Week | FMIT Eligible | Max FMIT/Year | Notes |
|------|----------------------|----------------|---------------|---------------|-------|
| **PD** (Program Director) | 0 | - | Yes | ~6 weeks | Leadership/admin focus |
| **APD** (Associate Program Director) | 2 (0.2 FTE) | - | Yes | ~6 weeks | Flexible within block |
| **OIC** (Officer in Charge) | 2 (0.2 FTE) | - | Yes | ~6 weeks | Flexible within block |
| **Department Chief** | 1 | - | Yes | ~6 weeks | Administrative duties |
| **Sports Medicine** | 0 | 4 | Yes | ~6 weeks | SM clinic only, no regular clinic |
| **Core Faculty** | Max 4 | - | Yes | ~6 weeks | Max 16 half-days per block |

### Clinic Flexibility Rules

- **APD/OIC**: 2 half-days/week target, can be distributed flexibly within a 4-week block (e.g., 0 one week, 4 another) as long as block total = 8 half-days
- **Core Faculty**: Hard maximum of 4 half-days per week, 16 per block
- **Sports Medicine**: Regular clinic blocked; SM clinic = 4 half-days/week

---

## Activity Types

### AT (Attending/Precepting)

- **Definition**: Dedicated resident precepting in clinic
- **Purpose**: Faculty supervision of resident patient encounters
- **Constraint**: This is the ONLY activity where supervision ratios apply
- **Exclusivity**: When scheduled for AT, faculty can only perform supervision duties

### PCAT (Post-Call Attending)

- **Definition**: Attending duty assigned morning after overnight call
- **Trigger**: Automatic assignment for AM block following Sun-Thurs overnight call
- **Purpose**: Ensures clinic coverage while acknowledging post-call status

### DO (Direct Observation)

- **Definition**: Direct observation of resident clinical encounters
- **Trigger**: Automatic assignment for PM block following overnight call
- **Purpose**: Educational assessment opportunity post-call

### SM Clinic (Sports Medicine Clinic)

- **Definition**: Specialized sports medicine clinic sessions
- **Staffing**: Sports Medicine faculty + SM rotation residents
- **Activities**: Procedures, ultrasound, specialized patient care
- **Constraint**: SM residents MUST be aligned with SM faculty (hard constraint)

---

## FMIT (Inpatient Attending) Rules

### Week Structure

```
FMIT Week: Friday (start) → Thursday (end)
           Independent of 4-week block boundaries
```

### Faculty FMIT Constraints

| Constraint | Rule |
|------------|------|
| **Duration** | Full week (Fri-Thurs) |
| **Activity** | FMIT is the half-day activity for ALL blocks during the week |
| **Clinic** | Blocked entirely (no clinic Mon-Thurs) |
| **Call (Sun-Thurs)** | NOT available |
| **Call (Fri-Sat)** | MANDATORY - FMIT attending covers Fri night and Sat night |
| **Post-FMIT Friday** | Blocked entirely (recovery day) |
| **Max per year** | ~6 weeks per faculty member |

### Resident FMIT Constraints

| Constraint | Rule |
|------------|------|
| **Duration** | Must respect 4-week block boundaries |
| **Ideal staffing** | 1 PGY-1 + 1 PGY-2 + 1 PGY-3 + Faculty |
| **Supervision** | Faculty oversight required |

### FMIT Timeline Example

```
Week 1 (FMIT Week):
  Fri:  FMIT (AM/PM) + Fri night call (mandatory)
  Sat:  FMIT (AM/PM) + Sat night call (mandatory)
  Sun:  FMIT (AM/PM) - NOT available for call
  Mon:  FMIT (AM/PM) - NOT available for call
  Tue:  FMIT (AM/PM) - NOT available for call
  Wed:  FMIT (AM/PM) - NOT available for call
  Thu:  FMIT (AM/PM) - NOT available for call

Week 2 (Post-FMIT):
  Fri:  BLOCKED (recovery) - no scheduling allowed
  Sat+: Normal availability resumes
```

---

## Call Schedule Rules

### Call Types

| Type | Days | Coverage |
|------|------|----------|
| **Overnight (Fri-Sat)** | Friday night, Saturday night | FMIT attending (mandatory) |
| **Overnight (Sun-Thurs)** | Sunday-Thursday nights | Non-FMIT faculty pool |
| **Weekend** | Saturday, Sunday daytime | As needed |

### Call Equity Tracking

| Category | Tracking Method | Notes |
|----------|-----------------|-------|
| **Sunday call** | Separate equity pool | Worst day - track independently |
| **Mon-Thurs call** | Combined equity pool | Track together for fairness |

### Call Preferences (Soft Constraints)

| Role | Preference | Reason |
|------|------------|--------|
| **PD** | Avoid Tuesday | Academic commitments |
| **APD** | Avoid Tuesday | Academic commitments |
| **Department Chief** | Prefer Wednesday | Personal preference |
| **OIC** | No preference | - |
| **Sports Medicine** | No preference | - |
| **Core Faculty** | No preference | - |

### Call Eligibility

- **Eligible for Sun-Thurs call**: All faculty NOT currently on FMIT
- **Fri-Sat call**: Exclusively FMIT attending
- **Post-FMIT Friday**: Not eligible for any call

---

## Sports Medicine Coordination

### Hard Constraint: SM Resident/Faculty Alignment

When a resident is on Sports Medicine rotation, they MUST be scheduled in SM clinic blocks at the same time as Sports Medicine faculty.

**Rationale**: Residents see the faculty's patients under direct supervision for specialized procedures and ultrasound examinations.

### SM Rotation Duration

| Rotation Type | Duration | SM Clinic Exposure |
|---------------|----------|-------------------|
| **Dedicated SM rotation** | 1 block (28 days) | 4 half-days/week aligned with SM faculty |
| **Other rotations with SM component** | Varies | Selected SM half-days as defined by rotation |

### SM Faculty Availability

- Sports Medicine faculty does NOT do regular clinic
- Available for FMIT (~6 weeks max per year)
- Available for call when not on FMIT
- Primary duty: SM clinic supervision

---

## Post-Call Rules

### Automatic Assignments After Overnight Call (Sun-Thurs)

```
Overnight Call (Sun-Thurs night)
         |
         v
    Next Day AM: PCAT (Post-Call Attending)
         |
         v
    Next Day PM: DO (Direct Observation)
```

### Post-Call Timeline Example

```
Tuesday night: Dr. Smith on overnight call
Wednesday AM:  Dr. Smith → PCAT (auto-assigned)
Wednesday PM:  Dr. Smith → DO (auto-assigned)
Thursday:      Dr. Smith → Normal schedule resumes
```

### Post-FMIT Rules

```
Thursday (last day of FMIT)
         |
         v
    Friday: BLOCKED (recovery day - no activities)
         |
         v
    Saturday: Normal availability resumes
```

---

## Supervision Ratios

### ACGME Requirements (AT Activity Only)

| PGY Level | Ratio | Meaning |
|-----------|-------|---------|
| **PGY-1** | 1:2 | 1 faculty per 2 PGY-1 residents |
| **PGY-2** | 1:4 | 1 faculty per 4 PGY-2 residents |
| **PGY-3** | 1:4 | 1 faculty per 4 PGY-3 residents |

### Application

- Ratios apply ONLY during AT (Attending/Precepting) activity
- Faculty scheduled for AT can only perform supervision duties
- Calculate required faculty based on resident mix in clinic

### Example Calculation

```
Clinic session with:
  - 3 PGY-1 residents → ceil(3/2) = 2 faculty needed
  - 2 PGY-2 residents → ceil(2/4) = 1 faculty needed
  - 2 PGY-3 residents → ceil(2/4) = 1 faculty needed

Total faculty required: max(1, 2+1+1) = 4 faculty for AT
```

---

## Current Faculty Roster

| Role | Count | Names (if applicable) |
|------|-------|----------------------|
| PD | 1 | - |
| APD | 1 | - |
| OIC | 1 | - |
| Department Chief | 1 | - |
| Sports Medicine | 1 | - |
| Core Faculty | 4 | - |
| **Total** | **9** | Excluding adjunct |

**Note**: Adjunct faculty are manually placed and not subject to automated scheduling constraints.

---

## Implementation Requirements

### Data Model Changes

1. **Add `faculty_role` field to Person model**
   - Enum values: `PD`, `APD`, `OIC`, `DEPT_CHIEF`, `SPORTS_MED`, `CORE`
   - Required for faculty type persons
   - Migration needed

2. **Add call tracking fields**
   - `sunday_call_count` for separate Sunday equity
   - `weekday_call_count` for Mon-Thurs equity

### New Constraints Required

| Constraint | Type | Priority |
|------------|------|----------|
| `FacultyRoleClinicConstraint` | Hard | High |
| `FMITWeekBlockingConstraint` | Hard | High |
| `FMITCallConstraint` | Hard | High |
| `PostFMITRecoveryConstraint` | Hard | High |
| `PostCallAutoAssignmentConstraint` | Hard | High |
| `SMResidentFacultyAlignmentConstraint` | Hard | High |
| `SundayCallEquityConstraint` | Soft | Medium |
| `TuesdayCallPreferenceConstraint` | Soft | Low |
| `DeptChiefWednesdayPreferenceConstraint` | Soft | Low |

### Validation Rules

1. FMIT attending must have Fri/Sat call assigned
2. FMIT attending cannot have Sun-Thurs call
3. Post-FMIT Friday must be empty
4. SM residents must align with SM faculty
5. Faculty clinic counts must respect role limits

---

## Appendix: Constraint Priority Levels

| Priority | Meaning | Violation Handling |
|----------|---------|-------------------|
| **CRITICAL** | ACGME compliance, patient safety | Schedule invalid if violated |
| **HIGH** | Core business rules | Warning + manual override required |
| **MEDIUM** | Equity and fairness | Warning, auto-balanced over time |
| **LOW** | Personal preferences | Best effort, no warning if unmet |
