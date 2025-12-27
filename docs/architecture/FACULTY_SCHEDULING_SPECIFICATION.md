<<<<<<< HEAD
***REMOVED*** Faculty Scheduling Specification
=======
***REMOVED*** Scheduling Specification
>>>>>>> origin/docs/session-14-summary

> **Version:** 1.1
> **Created:** 2025-12-19
> **Updated:** 2025-12-19
> **Status:** Approved specification for implementation

This document defines the complete scheduling parameters for faculty roles, FMIT coverage, call assignments, and coordination requirements.

---

***REMOVED******REMOVED*** Table of Contents

1. [Faculty Roles and Clinic Requirements](***REMOVED***faculty-roles-and-clinic-requirements)
2. [Activity Types](***REMOVED***activity-types)
3. [FMIT (Inpatient Attending) Rules](***REMOVED***fmit-inpatient-attending-rules)
4. [Call Schedule Rules](***REMOVED***call-schedule-rules)
5. [Sports Medicine Coordination](***REMOVED***sports-medicine-coordination)
6. [Post-Call Rules](***REMOVED***post-call-rules)
7. [Supervision Ratios](***REMOVED***supervision-ratios)
8. [Procedure Credentialing](***REMOVED***procedure-credentialing)
9. [Wednesday Didactics](***REMOVED***wednesday-didactics)
10. [Leave Request Windows](***REMOVED***leave-request-windows)
11. [Night Float](***REMOVED***night-float)
12. [Emergency Coverage (Scramble)](***REMOVED***emergency-coverage-scramble)
13. [Military Program Constraints](***REMOVED***military-program-constraints)
14. [Rotation Templates](***REMOVED***rotation-templates)
15. [Current Faculty Roster](***REMOVED***current-faculty-roster)
16. [Implementation Requirements](***REMOVED***implementation-requirements)
17. [Future Exploration](***REMOVED***future-exploration)

---

<<<<<<< HEAD
***REMOVED******REMOVED*** Faculty Roles and Clinic Requirements
=======
***REMOVED******REMOVED*** Roles and Clinic Requirements
>>>>>>> origin/docs/session-14-summary

***REMOVED******REMOVED******REMOVED*** Role Definitions

| Role | Clinic Half-Days/Week | SM Clinic/Week | FMIT Eligible | Max FMIT/Year | Notes |
|------|----------------------|----------------|---------------|---------------|-------|
| **PD** (Program Director) | 0 | - | Yes | ~6 weeks | Leadership/admin focus |
| **APD** (Associate Program Director) | 2 (0.2 FTE) | - | Yes | ~6 weeks | Flexible within block |
| **OIC** (Officer in Charge) | 2 (0.2 FTE) | - | Yes | ~6 weeks | Flexible within block |
| **Department Chief** | 1 | - | Yes | ~6 weeks | Administrative duties |
| **Sports Medicine** | 0 | 4 | Yes | ~6 weeks | SM clinic only, no regular clinic |
| **Core Faculty** | Max 4 | - | Yes | ~6 weeks | Max 16 half-days per block |

***REMOVED******REMOVED******REMOVED*** Clinic Flexibility Rules

- **APD/OIC**: 2 half-days/week target, can be distributed flexibly within a 4-week block (e.g., 0 one week, 4 another) as long as block total = 8 half-days
- **Core Faculty**: Hard maximum of 4 half-days per week, 16 per block
- **Sports Medicine**: Regular clinic blocked; SM clinic = 4 half-days/week

---

***REMOVED******REMOVED*** Activity Types

***REMOVED******REMOVED******REMOVED*** AT (Attending/Precepting)

- **Definition**: Dedicated resident precepting in clinic
- **Purpose**: Faculty supervision of resident patient encounters
- **Constraint**: This is the ONLY activity where supervision ratios apply
- **Exclusivity**: When scheduled for AT, faculty can only perform supervision duties

***REMOVED******REMOVED******REMOVED*** PCAT (Post-Call Attending)

- **Definition**: Attending duty assigned morning after overnight call
- **Trigger**: Automatic assignment for AM block following Sun-Thurs overnight call
- **Purpose**: Ensures clinic coverage while acknowledging post-call status

***REMOVED******REMOVED******REMOVED*** DO (Direct Observation)

- **Definition**: Direct observation of resident clinical encounters
- **Trigger**: Automatic assignment for PM block following overnight call
- **Purpose**: Educational assessment opportunity post-call

***REMOVED******REMOVED******REMOVED*** SM Clinic (Sports Medicine Clinic)

- **Definition**: Specialized sports medicine clinic sessions
- **Staffing**: Sports Medicine faculty + SM rotation residents
- **Activities**: Procedures, ultrasound, specialized patient care
- **Constraint**: SM residents MUST be aligned with SM faculty (hard constraint)

---

***REMOVED******REMOVED*** FMIT (Inpatient Attending) Rules

***REMOVED******REMOVED******REMOVED*** Week Structure

```
FMIT Week: Friday (start) → Thursday (end)
           Independent of 4-week block boundaries
```

<<<<<<< HEAD
***REMOVED******REMOVED******REMOVED*** Faculty FMIT Constraints
=======
***REMOVED******REMOVED******REMOVED*** FMIT Constraints
>>>>>>> origin/docs/session-14-summary

| Constraint | Rule |
|------------|------|
| **Duration** | Full week (Fri-Thurs) |
| **Activity** | FMIT is the half-day activity for ALL blocks during the week |
| **Clinic** | Blocked entirely (no clinic Mon-Thurs) |
| **Call (Sun-Thurs)** | NOT available |
| **Call (Fri-Sat)** | MANDATORY - FMIT attending covers Fri night and Sat night |
| **Post-FMIT Friday** | Blocked entirely (recovery day) |
| **Max per year** | ~6 weeks per faculty member |

***REMOVED******REMOVED******REMOVED*** Resident FMIT Constraints

| Constraint | Rule |
|------------|------|
| **Duration** | Must respect 4-week block boundaries |
| **Ideal staffing** | 1 PGY-1 + 1 PGY-2 + 1 PGY-3 + Faculty |
| **Supervision** | Faculty oversight required |

***REMOVED******REMOVED******REMOVED*** FMIT Timeline Example

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

***REMOVED******REMOVED*** Call Schedule Rules

***REMOVED******REMOVED******REMOVED*** Call Types

| Type | Days | Coverage |
|------|------|----------|
| **Overnight (Fri-Sat)** | Friday night, Saturday night | FMIT attending (mandatory) |
| **Overnight (Sun-Thurs)** | Sunday-Thursday nights | Non-FMIT faculty pool |
| **Weekend** | Saturday, Sunday daytime | As needed |

***REMOVED******REMOVED******REMOVED*** Call Equity Tracking

| Category | Tracking Method | Notes |
|----------|-----------------|-------|
| **Sunday call** | Separate equity pool | Worst day - track independently |
| **Mon-Thurs call** | Combined equity pool | Track together for fairness |

***REMOVED******REMOVED******REMOVED*** Call Preferences (Soft Constraints)

| Role | Preference | Reason |
|------|------------|--------|
| **PD** | Avoid Tuesday | Academic commitments |
| **APD** | Avoid Tuesday | Academic commitments |
| **Department Chief** | Prefer Wednesday | Personal preference |
| **OIC** | No preference | - |
| **Sports Medicine** | No preference | - |
| **Core Faculty** | No preference | - |

***REMOVED******REMOVED******REMOVED*** Call Eligibility

- **Eligible for Sun-Thurs call**: All faculty NOT currently on FMIT
- **Fri-Sat call**: Exclusively FMIT attending
- **Post-FMIT Friday**: Not eligible for any call

---

***REMOVED******REMOVED*** Sports Medicine Coordination

***REMOVED******REMOVED******REMOVED*** Hard Constraint: SM Resident/Faculty Alignment

When a resident is on Sports Medicine rotation, they MUST be scheduled in SM clinic blocks at the same time as Sports Medicine faculty.

**Rationale**: Residents see the faculty's patients under direct supervision for specialized procedures and ultrasound examinations.

***REMOVED******REMOVED******REMOVED*** SM Rotation Duration

| Rotation Type | Duration | SM Clinic Exposure |
|---------------|----------|-------------------|
| **Dedicated SM rotation** | 1 block (28 days) | 4 half-days/week aligned with SM faculty |
| **Other rotations with SM component** | Varies | Selected SM half-days as defined by rotation |

***REMOVED******REMOVED******REMOVED*** SM Faculty Availability

- Sports Medicine faculty does NOT do regular clinic
- Available for FMIT (~6 weeks max per year)
- Available for call when not on FMIT
- Primary duty: SM clinic supervision
- **When SM faculty is on FMIT**: SM clinic is cancelled for that week (no backup coverage)

---

***REMOVED******REMOVED*** Post-Call Rules

***REMOVED******REMOVED******REMOVED*** Automatic Assignments After Overnight Call (Sun-Thurs)

```
Overnight Call (Sun-Thurs night)
         |
         v
    Next Day AM: PCAT (Post-Call Attending)
         |
         v
    Next Day PM: DO (Direct Observation)
```

***REMOVED******REMOVED******REMOVED*** Post-Call Timeline Example

```
Tuesday night: Dr. Smith on overnight call
Wednesday AM:  Dr. Smith → PCAT (auto-assigned)
Wednesday PM:  Dr. Smith → DO (auto-assigned)
Thursday:      Dr. Smith → Normal schedule resumes
```

***REMOVED******REMOVED******REMOVED*** Post-FMIT Rules

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

***REMOVED******REMOVED*** Supervision Ratios

***REMOVED******REMOVED******REMOVED*** ACGME Requirements (AT Activity Only)

| PGY Level | Ratio | Meaning |
|-----------|-------|---------|
| **PGY-1** | 1:2 | 1 faculty per 2 PGY-1 residents |
| **PGY-2** | 1:4 | 1 faculty per 4 PGY-2 residents |
| **PGY-3** | 1:4 | 1 faculty per 4 PGY-3 residents |

***REMOVED******REMOVED******REMOVED*** Application

- Ratios apply ONLY during AT (Attending/Precepting) activity
- Faculty scheduled for AT can only perform supervision duties
- Calculate required faculty based on resident mix in clinic

***REMOVED******REMOVED******REMOVED*** Example Calculation

```
Clinic session with:
  - 3 PGY-1 residents → 3 × 0.5 = 1.5 supervision load (1:2 ratio)
  - 2 PGY-2 residents → 2 × 0.25 = 0.5 supervision load (1:4 ratio)
  - 2 PGY-3 residents → 2 × 0.25 = 0.5 supervision load (1:4 ratio)

Total supervision load: 1.5 + 0.5 + 0.5 = 2.5
Faculty required: ceil(2.5) = 3 faculty for AT

Note: Summing fractional loads BEFORE ceiling avoids overcounting
in mixed PGY scenarios.
```

---

***REMOVED******REMOVED*** Procedure Credentialing

***REMOVED******REMOVED******REMOVED*** Overview

Certain procedures require specific faculty credentialing. Only credentialed faculty may supervise or perform these procedures. This is a **faculty-specific constraint** - resident procedure tracking is handled externally via MyEvaluations.

***REMOVED******REMOVED******REMOVED*** Credentialed Procedures

| Procedure | Description | Credentialed Faculty |
|-----------|-------------|---------------------|
| **Vasectomy** | Office-based surgical procedure | Limited (2-3 faculty) |
| **Botox** | Therapeutic botulinum toxin injection | Limited subset |
| **Colposcopy** | Cervical examination with magnification | Limited subset |
| **IUD Insertion** | Intrauterine device placement | Most faculty (note exceptions) |
| **Joint Injection** | Musculoskeletal injections | Sports Med + credentialed others |
| **Skin Biopsy** | Punch/shave biopsy procedures | Most faculty |

***REMOVED******REMOVED******REMOVED*** Implementation Notes

- Each faculty member needs a `credentialed_procedures` field (list/array)
- When scheduling procedure clinics, validate faculty has required credential
- Some faculty may have **negative credentials** (explicitly NOT credentialed for common procedures like IUD insertion)

***REMOVED******REMOVED******REMOVED*** Data Model

```
Person (Faculty)
├── credentialed_procedures: List[str]  ***REMOVED*** ["vasectomy", "botox", "colposcopy"]
└── excluded_procedures: List[str]      ***REMOVED*** ["iud_insertion"] (optional inverse)
```

---

***REMOVED******REMOVED*** Wednesday Didactics

***REMOVED******REMOVED******REMOVED*** Protected Educational Time

Wednesday afternoon is protected for resident didactics (educational conferences).

| Constraint | Rule |
|------------|------|
| **Time** | Wednesday PM (half-day block) |
| **Residents** | Should not be scheduled for clinic |
| **Faculty** | Reduced clinic staffing; some faculty attend/teach |
| **Type** | Soft constraint with high weight |

***REMOVED******REMOVED******REMOVED*** Exceptions

- FMIT residents/faculty: May have modified participation
- Night float: Excused from didactics
- On-call residents: Excused if post-call

***REMOVED******REMOVED******REMOVED*** Implementation

- Block Wednesday PM from routine resident clinic scheduling
- Flag Wednesday PM faculty assignments as "reduced coverage acceptable"
- Track didactics attendance separately if required

---

***REMOVED******REMOVED*** Leave Request Windows

***REMOVED******REMOVED******REMOVED*** Request Timing Requirements

| Leave Type | Advance Notice | Approval Authority |
|------------|----------------|-------------------|
| **Vacation/PTO** | TBD - needs specification | Program Coordinator |
| **Conference** | TBD - needs specification | PD/APD |
| **Military (TDY)** | As soon as orders received | Automatic (orders-based) |
| **Medical** | As soon as known | Program Coordinator |
| **Parental** | 30+ days preferred | PD |

***REMOVED******REMOVED******REMOVED*** Blackout Periods

> **TODO**: Define blackout periods for leave requests (e.g., orientation week, graduation, peak census periods)

***REMOVED******REMOVED******REMOVED*** Concurrent Leave Limits

> **TODO**: Define maximum number of residents/faculty on leave simultaneously

***REMOVED******REMOVED******REMOVED*** Implementation Notes

- Leave requests need `request_date` and `requested_for_date` tracking
- Calculate days in advance at request time
- Enforce minimum notice periods (soft constraint with override)
- Track blackout periods in configuration

---

***REMOVED******REMOVED*** Night Float

***REMOVED******REMOVED******REMOVED*** Overview

Night float is a **rotation template** with hard scheduling rules. Residents on night float cover overnight duties for a defined period.

***REMOVED******REMOVED******REMOVED*** Hard Constraints

| Constraint | Rule |
|------------|------|
| **Duration** | Defined per rotation (typically 1-2 weeks) |
| **Schedule** | Night shifts only (no daytime activities) |
| **Consecutive Nights** | Maximum per ACGME (typically 6 consecutive) |
| **Recovery** | Required day off after night float block ends |
| **Didactics** | Excused from Wednesday didactics |
| **Clinic** | No continuity clinic during night float |

***REMOVED******REMOVED******REMOVED*** Night Float vs. Overnight Call

| Aspect | Night Float | Overnight Call |
|--------|-------------|----------------|
| **Duration** | Multi-day rotation | Single night |
| **Next Day** | Off (sleeping) | PCAT AM + DO PM |
| **Frequency** | Rotation-based | Distributed across faculty |
| **Coverage** | Resident + backup | Faculty primary |

***REMOVED******REMOVED******REMOVED*** Implementation

- Night float is a rotation template type, not an ad-hoc assignment
- Template defines all half-day blocks as "night float" activity
- System must prevent conflicting daytime assignments
- Post-night-float recovery day is hard constraint

---

***REMOVED******REMOVED*** Emergency Coverage (Scramble)

***REMOVED******REMOVED******REMOVED*** Overview

This program does **not** use a formal jeopardy/backup system. When coverage gaps occur, the program "scrambles" to find coverage.

***REMOVED******REMOVED******REMOVED*** Current Process

1. Coverage gap identified (illness, emergency, etc.)
2. Program coordinator contacts available faculty/residents
3. Manual reassignment based on who responds
4. Schedule updated after coverage secured

***REMOVED******REMOVED******REMOVED*** Scramble Decision Support (Future Enhancement)

The system could provide decision support for scramble situations:

| Feature | Description |
|---------|-------------|
| **Availability Query** | Who is available for this block? |
| **Constraint Check** | Would assigning person X violate any constraints? |
| **Equity Impact** | How would this affect call/clinic equity? |
| **Quick Swap** | One-click reassignment with validation |
| **Notification** | Automated outreach to available pool |

***REMOVED******REMOVED******REMOVED*** Who Can Cover

> **TODO**: Define coverage eligibility rules
> - Can PGY-1 cover PGY-3 clinic?
> - Can faculty cover resident duties?
> - Cross-rotation coverage rules?

---

***REMOVED******REMOVED*** Military Program Constraints

***REMOVED******REMOVED******REMOVED*** Moonlighting

**Moonlighting is NOT ALLOWED** at military residency programs.

| Rule | Enforcement |
|------|-------------|
| **Internal moonlighting** | Prohibited |
| **External moonlighting** | Prohibited |
| **Exception process** | None - absolute prohibition |

***REMOVED******REMOVED******REMOVED*** Military-Specific Duties

| Duty Type | Scheduling Impact |
|-----------|-------------------|
| **TDY (Temporary Duty)** | Automatic leave - schedule around orders |
| **Deployment** | Extended absence - backfill required |
| **PT (Physical Training)** | Early morning - may affect AM blocks |
| **Military Training Days** | Periodic - treat as leave |
| **Drill (Reserves)** | If applicable - weekend impact |

***REMOVED******REMOVED******REMOVED*** Implementation

- No moonlighting fields/workflow needed
- TDY/deployment leave types with orders-based approval
- Consider PT time in early AM scheduling if applicable

---

***REMOVED******REMOVED*** Rotation Templates

***REMOVED******REMOVED******REMOVED*** Overview

Rotation templates define the expected half-day activities for residents during specific rotations. This is a **complex domain** requiring dedicated exploration.

***REMOVED******REMOVED******REMOVED*** Template Categories

| Category | Constraint Type | Examples |
|----------|-----------------|----------|
| **Hard-constrained** | Must follow exactly | FMIT, Night Float |
| **Soft-constrained** | Minimum activities/week | Outpatient, Procedures |
| **Flexible** | General guidelines | Electives |

***REMOVED******REMOVED******REMOVED*** Known Hard Templates

| Template | Hard Rules |
|----------|------------|
| **FMIT** | All blocks = FMIT activity, Fri/Sat call mandatory, no Sun-Thurs call |
| **Night Float** | Night shifts only, no daytime activities, recovery day required |

***REMOVED******REMOVED******REMOVED*** Known Soft Templates

| Template | Soft Rules |
|----------|------------|
| **Outpatient** | Minimum X clinic half-days per week |
| **Procedures** | Minimum Y procedure half-days per week |
| **Sports Medicine** | Must align with SM faculty availability |

***REMOVED******REMOVED******REMOVED*** Template Data Model Considerations

```
RotationTemplate
├── name: str
├── duration_blocks: int (typically 28 days = 1 block)
├── constraint_type: "hard" | "soft" | "flexible"
├── required_activities: List[ActivityRequirement]
│   ├── activity_type: str
│   ├── min_per_week: int (soft)
│   ├── max_per_week: int (soft)
│   └── exact_per_week: int (hard)
├── blocked_activities: List[str]  ***REMOVED*** Cannot do these during rotation
├── special_rules: Dict  ***REMOVED*** FMIT call rules, etc.
└── didactics_policy: "required" | "excused" | "modified"
```

***REMOVED******REMOVED******REMOVED*** ⚠️ Future Work Required

Rotation templates require dedicated analysis:
- Inventory all current rotations
- Document each template's half-day activity expectations
- Classify constraints as hard vs. soft
- Define minimum/maximum thresholds
- Handle template exceptions and overrides

---

***REMOVED******REMOVED*** Current Faculty Roster

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

***REMOVED******REMOVED*** Implementation Requirements

***REMOVED******REMOVED******REMOVED*** Data Model Changes

1. **Add `faculty_role` field to Person model**
   - Enum values: `PD`, `APD`, `OIC`, `DEPT_CHIEF`, `SPORTS_MED`, `CORE`
   - Required for faculty type persons
   - Migration needed

2. **Add call tracking fields**
   - `sunday_call_count` for separate Sunday equity
   - `weekday_call_count` for Mon-Thurs equity

***REMOVED******REMOVED******REMOVED*** New Constraints Required

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

***REMOVED******REMOVED******REMOVED*** Validation Rules

1. FMIT attending must have Fri/Sat call assigned
2. FMIT attending cannot have Sun-Thurs call
3. Post-FMIT Friday must be empty
4. SM residents must align with SM faculty
5. Faculty clinic counts must respect role limits

---

***REMOVED******REMOVED*** Appendix: Constraint Priority Levels

| Priority | Meaning | Violation Handling |
|----------|---------|-------------------|
| **CRITICAL** | ACGME compliance, patient safety | Schedule invalid if violated |
| **HIGH** | Core business rules | Warning + manual override required |
| **MEDIUM** | Equity and fairness | Warning, auto-balanced over time |
| **LOW** | Personal preferences | Best effort, no warning if unmet |

---

***REMOVED******REMOVED*** Future Exploration

***REMOVED******REMOVED******REMOVED*** Areas Requiring Dedicated Analysis

The following topics are identified but require deeper exploration before implementation:

| Area | Status | Priority | Notes |
|------|--------|----------|-------|
| **Rotation Templates** | 🔴 Not started | High | Inventory all rotations, define hard/soft constraints per template |
| **Leave Request Windows** | 🟡 Partial | Medium | Define advance notice requirements, blackout periods |
| **Procedure Credentialing** | 🟡 Partial | Medium | Complete faculty credentialing inventory |
| **Scramble Decision Support** | 🔴 Not started | Low | Nice-to-have tooling for coverage gaps |
| **Cross-Coverage Rules** | 🔴 Not started | Low | Currently none, but may need in future |

***REMOVED******REMOVED******REMOVED*** Questions to Answer

1. **Rotation Templates**
   - What are all the rotation types?
   - What are the minimum half-day activity requirements for each?
   - Which templates have hard vs. soft constraints?
   - How do templates handle holiday weeks?

2. **Leave Management**
   - How many days advance notice for vacation?
   - What are the blackout periods?
   - Maximum concurrent residents on leave?
   - Maximum concurrent faculty on leave?

3. **Procedure Scheduling**
   - Complete list of credentialed procedures
   - Which faculty are credentialed for each?
   - How often are procedure clinics scheduled?
   - Do residents need to be paired with credentialed faculty?

4. **Wednesday Didactics**
   - Exact time block (1300-1700? All PM?)
   - Which faculty roles are expected to attend?
   - How is attendance tracked?

***REMOVED******REMOVED******REMOVED*** Implementation Phases (Proposed)

| Phase | Focus | Estimated Complexity |
|-------|-------|---------------------|
| ✅ Phase 1-4 | Faculty roles, FMIT, call equity, SM alignment, post-call | Complete |
| Phase 5 | Procedure credentialing | Medium |
| Phase 6 | Wednesday didactics blocking | Low |
| Phase 7 | Leave request windows | Medium |
| Phase 8 | Rotation template constraints | High |
| Phase 9 | Scramble decision support | Medium |

---

*This document is a living specification. Update as requirements are clarified.*
