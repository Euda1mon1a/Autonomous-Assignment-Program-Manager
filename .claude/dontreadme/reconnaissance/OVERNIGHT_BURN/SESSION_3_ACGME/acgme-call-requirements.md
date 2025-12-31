# ACGME Call Scheduling Requirements - Comprehensive Guide

> **SEARCH_PARTY Investigation:** G2_RECON PERCEPTION → INVESTIGATION → ARCANA → HISTORY → INSIGHT → RELIGION → NATURE → MEDICINE → SURVIVAL → STEALTH
>
> **Document Purpose:** Consolidate all ACGME call scheduling rules, rest period requirements, night float documentation, and post-call recovery protocols from the Residency Scheduler codebase.

---

## Table of Contents

1. [In-House Call Frequency Limits](#in-house-call-frequency-limits)
2. [Rest Period Requirements](#rest-period-requirements)
3. [Call Structure in System](#call-structure-in-system)
4. [Night Float Implementation](#night-float-implementation)
5. [Post-Call Recovery Rules](#post-call-recovery-rules)
6. [Call Equity Constraints](#call-equity-constraints)
7. [Call Eligibility Rules](#call-eligibility-rules)
8. [Integrated System Constraints](#integrated-system-constraints)

---

## In-House Call Frequency Limits

### ACGME "Every Third Night" Rule

**Regulatory Requirement:**
```
Residents must not be scheduled for in-house call more frequently than
every third night, averaged over a 4-week period.
```

**Quantitative Limits:**
- **28-day period:** Maximum ~9-10 in-house call shifts
- **Calculation basis:** 28 days ÷ 3 = 9.33 nights
- **Averaging method:** Rolling 4-week window (strict compliance required)

**Practical Implementation:**
- A resident can work call on Monday, then cannot be scheduled again until Thursday minimum
- Example compliant pattern: Mon call → Thu call → Sun call → Wed call
- Example non-compliant: Mon call → Tue call (violates every-3rd-night rule)

### Call Type Coverage in System

| Call Type | Nights | Coverage Model | Frequency Limit |
|-----------|--------|-----------------|-----------------|
| **Overnight (Fri-Sat)** | Friday, Saturday | FMIT attending (mandatory) | Varies by FMIT assignment |
| **Overnight (Sun-Thurs)** | Sunday-Thursday | Non-FMIT faculty pool | Every 3rd night average |
| **Weekend** | Saturday, Sunday daytime | As needed | Not specifically regulated |

---

## Rest Period Requirements

### Post-Call Mandatory Rest

**ACGME Standard:**
```
After 24 hours of in-house call, residents must have at least 10 hours
free of duty before returning to clinical work.
```

**Key Details:**
- **Continuous period:** 10 consecutive hours minimum
- **Timing:** Must begin immediately after the call period ends
- **No exceptions:** 10-hour minimum is non-negotiable
- **New patient rule:** No new patients accepted after 24 hours on duty

### Extended Shift Rules

**24-Hour Maximum Plus Handoff Time:**
- **Clinical duty:** Maximum 24 consecutive hours
- **Handoff period:** Additional 4 hours permitted (total 28 hours maximum)
- **Handoff activities:** Patient transitions, educational debriefing, continuity care only
- **New patient restriction:** Cannot accept new patients during the final 4 hours (except continuity)

**Post-Shift Requirements:**
- After 28-hour shift: 10-hour rest minimum before next duty period
- No clinical responsibilities during mandatory rest period
- Rest period is counted in duty hour limits

### PGY-1 Specific Restrictions

**Protective Limitation:**
- PGY-1 residents: Maximum **16 consecutive hours** (hard cap, no exceptions)
- No additional handoff time beyond 16 hours for PGY-1
- No gradual increase in first months of PGY-1

**Supervision During Extended Shifts:**
- Senior resident or attending must be immediately available
- Cannot take independent call during PGY-1 year

---

## Call Structure in System

### Call Assignment Model

The system tracks call assignments separately from regular clinical assignments:

```python
class CallAssignment:
    date: Date                           # Date of call
    person_id: UUID                      # Faculty member
    call_type: str                       # 'overnight', 'weekend', 'backup'
    is_weekend: bool                     # Weekend indicator
    is_holiday: bool                     # Holiday indicator
```

### Call Types Tracked

| Call Type | Definition | Duty Hours | Frequency Limit |
|-----------|-----------|-----------|-----------------|
| **overnight** | In-house call 24+ hours | Full duty hours counted | Every 3rd night |
| **weekend** | Weekend call | Varies by role | No specific limit |
| **backup** | Second-call status | Hours counted if activated | Varies |

---

## Night Float Implementation

### Night Float Definition and Usage

**Purpose:**
- Alternative scheduling model for extended block-based night work
- Residents rotate through dedicated night shift assignment (typically 2-week period)
- Differs from traditional "on-call" model

**Block-Half Structure:**
- Academic year divided into 4-week blocks
- Each 4-week block divided into two 2-week halves (block-halves)
- Night Float assignment typically spans one complete block-half (14 days)

### Night Float Rest Requirements

**Post-Night Float Recovery:**

When a resident completes Night Float assignment:
- **Transition timing:** Recovery day occurs at block-half boundary
- **AM transition:** First AM of next block-half = **Post-Call (PC) recovery**
- **PM transition:** First PM of next block-half = **Post-Call (PC) recovery**
- **Full day off:** Both AM and PM blocked for recovery (entire day unavailable for other work)

**Implementation Logic:**

```python
# Night Float to Post-Call transition
If NF assignment on Block_half_1_day_14:
    Then PC assignment on Block_half_2_day_1 (AM + PM)

If NF assignment on Block_half_2_day_28:
    Then PC assignment on Block_1_day_1 (AM + PM) of next block
```

**Purpose of PC Days:**
- Mandatory recovery from extended night shift pattern
- Prevents immediate return to day shift duties
- Educational activities only (no clinical assignments)

### Night Float Validation

The system validates Night Float post-call compliance:

```
NightFloatPostCallConstraint:
- Detects NF assignments ending at block-half boundaries
- Forces PC (Post-Call) for both AM and PM of following day
- Blocks any other rotation assignment during PC day
- Severity: CRITICAL (hard constraint)
```

---

## Post-Call Recovery Rules

### Automatic Post-Call Activity Assignment

When faculty takes **overnight call on Sun-Thurs:**

| Time | Activity | Code | Definition |
|------|----------|------|-----------|
| **Next day AM** | Post-Call Attending | PCAT | Supervise residents in clinic (lighter duty) |
| **Next day PM** | Direct Observation | DO | Observe resident encounters (assessment/education) |

**System Implementation:**

```python
class PostCallAutoAssignmentConstraint:
    """
    When faculty takes Sun-Thurs overnight call:
    - Next day AM block: PCAT (Post-Call Attending)
    - Next day PM block: DO (Direct Observation)
    """
```

**Rationale:**
1. **PCAT (AM):** Acknowledges post-call fatigue while maintaining clinic coverage
2. **DO (PM):** Lighter educational duty rather than full clinical responsibilities
3. **Coverage:** Clinic continues with post-call attending supervision
4. **Safety:** Reduced independent decision-making post-call

### FMIT Weekend Call Post-Call Treatment

**Friday-Saturday Call (FMIT attending):**
- FMIT faculty take mandatory Fri/Sat night call
- **Post-FMIT Friday:** Entire day BLOCKED (recovery day)
- **Next week:** Normal availability resumes
- **No automatic PCAT/DO:** Weekend call handled differently than Sun-Thurs

### Friday Post-FMIT Blocking

**FMIT Week Structure:**
```
FMIT Week: Friday (start) → Thursday (end)
- Friday-Thursday: All blocks = FMIT activity
- Friday night: MANDATORY call
- Saturday night: MANDATORY call
```

**Post-FMIT Friday (following week):**
- **Status:** Completely blocked (not available for scheduling)
- **Purpose:** Recovery from FMIT week + weekend call
- **Duration:** One full calendar day (AM + PM)
- **Next availability:** Saturday following post-FMIT Friday

---

## Call Equity Constraints

### Sunday Call Equity (Soft Constraint)

**Why Sunday is Special:**
- Disrupts weekend rest
- Monday morning typically busy
- Higher patient volume from weekend
- Considered the "worst" call day

**Equity Tracking:**
- Sunday calls tracked separately from weekday calls
- Penalty increases quadratically with deviation from mean
- Weight: 10.0 (high priority among soft constraints)

**Implementation:**
```python
SundayCallEquityConstraint:
    - Separate equity pool for Sundays
    - Minimizes maximum Sunday call count across faculty
    - Encourages even 1-2 call distribution
    - Imbalance tolerance: >2 difference flagged as concerning
```

### Weekday Call Equity (Mon-Thurs)

**Tracking Method:**
- Monday through Thursday calls grouped together
- Combined equity pool (separate from Sunday)
- Fairness metric: minimize variance in per-faculty counts

**Implementation:**
```python
WeekdayCallEquityConstraint:
    - Mon-Thurs calls tracked as single pool
    - Weight: 5.0 (moderate priority)
    - Imbalance tolerance: >3 difference flagged as concerning
```

### Call Spacing Constraint

**Back-to-Back Call Prevention:**
- Penalizes consecutive week call assignments for same faculty
- Example: Call on Week 1 Sunday + Week 2 Monday = penalty
- Weight: 8.0 (high-moderate priority)

**Purpose:**
- Burnout prevention
- Schedule equity
- Work-life balance with recovery time

### Call Preferences (Soft)

| Role | Preference | Weight | Reason |
|------|-----------|--------|--------|
| **PD** | Avoid Tuesday | 2.0 | Academic commitments |
| **APD** | Avoid Tuesday | 2.0 | Teaching/conferences |
| **Dept Chief** | Prefer Wednesday | 1.0 (bonus) | Personal preference |
| **OIC** | No preference | - | Flexible |
| **Core Faculty** | No preference | - | Flexible |

---

## Call Eligibility Rules

### Faculty Eligible for Auto-Generated Overnight Call (Sun-Thurs)

**Inclusion Criteria:**
- NOT on FMIT during their FMIT week
- NOT adjunct faculty
- NOT with blocking absences
- NOT in post-FMIT Sunday blocking period

**Exclusion Rules:**
| Scenario | Eligible? | Reason |
|----------|-----------|--------|
| FMIT week (Fri-Thurs) | NO | Blocked by FMIT activity |
| Post-FMIT Friday | NO | Recovery day blocked |
| Post-FMIT Sunday | NO | Specific Sunday blocking |
| ADJUNCT faculty | NO | Manual assignment only |
| Approved leave/vacation | NO | Absence blocking |
| Deployment/TDY | NO | Military absence blocking |

### ADJUNCT Faculty Call Assignment

**Rules:**
- NOT auto-scheduled for call in solver
- CAN be manually assigned to specific call dates
- Treated as special assignment outside of equity tracking
- Useful for guest lecturers, temporary faculty

### FMIT Faculty Call Assignment

**Friday-Saturday Call (Mandatory):**
- FMIT attending covers Fri night + Sat night
- Mandatory coverage (non-negotiable)
- Separate from Sun-Thurs call pool
- Not subject to equity constraints (hardcoded requirement)

**Sunday-Thursday Availability:**
- NOT available during FMIT week (Sun-Thurs)
- Return to pool after FMIT week ends
- Post-FMIT Sunday blocking enforced

---

## Integrated System Constraints

### Constraint Priority Hierarchy

**CRITICAL (Hard Constraints):**
1. Availability (no assignments during absences)
2. 80-hour rule (rolling 4-week average)
3. 1-in-7 rule (one day off per 7 days)
4. Supervision ratios (faculty-to-resident)
5. Overnight call generation (exactly one per night Sun-Thurs)
6. Night Float post-call (mandatory PC day)
7. Post-call auto-assignment (PCAT/DO after call)

**MEDIUM (Soft Constraints - Scored):**
1. Call equity constraints (Sunday, weekday, spacing)
2. Call preferences (Tuesday avoidance, Wednesday preference)

### Solver Constraint Integration

**Call Assignment Variables:**
```python
call_assignments[(faculty_idx, block_idx, "overnight")] = BoolVar
```

**Coverage Constraints:**
```
For each night (Sun-Thurs):
  sum(call_vars for eligible faculty) == 1  # Exactly one per night
```

**Equity Optimization:**
```
Minimize: sum of variance penalties
- SundayCallEquity (weight 10)
- WeekdayCallEquity (weight 5)
- CallSpacing (weight 8)
- TuesdayPreference (weight 2)
- WednesdayPreference (weight -1 for bonus)
```

### Known Implementation Constraints

**Limitations in Current System:**

1. **Every-3rd-Night Rule:** Not explicitly enforced in solver
   - System relies on post-hoc equity penalties
   - Recommend: Add hard constraint in future releases

2. **10-Hour Rest Period:** Not explicitly tracked
   - Requires integration with duty hour logging system
   - Depends on accurate call duration data

3. **Call Type vs Clinical Duty Distinction:** Partially implemented
   - Call assignments tracked separately
   - Duty hour calculation depends on accurate data entry

4. **PGY-1 Special Restrictions:** Not explicitly enforced
   - Relies on program policy and manual oversight
   - 16-hour maximum not in automated constraints

---

## Key ACGME Callout

> **Critical:** The ACGME "every third night" rule is a regulatory requirement that ALL programs must enforce. While the Residency Scheduler includes equity constraints that encourage fair distribution, this specific frequency limit should be explicitly modeled as a hard constraint to ensure systematic compliance.

### Recommended System Enhancements

1. **Add explicit every-3rd-night hard constraint** to scheduler
2. **Track actual rest periods** (10-hour minimum after call)
3. **Monitor PGY-1 shift limits** (16-hour maximum)
4. **Integrate with duty hour logging** for real-time compliance
5. **Weekly compliance reports** to program leadership

---

## Summary Reference

| Requirement | ACGME Rule | System Implementation | Enforcement |
|-------------|-----------|----------------------|------------|
| Call frequency | Every 3rd night | Equity penalties (soft) | Post-hoc |
| Rest period | 10 hours minimum | Not enforced | Manual |
| Shift length | 24 hours max | Not enforced | Manual |
| Post-call duty | PCAT/DO required | AutoAssignment (hard) | Solver |
| Night Float recovery | PC day mandatory | NightFloatPostCall (hard) | Solver |
| Sunday equity | Separate tracking | SundayCallEquity (soft) | Penalty |
| Weekday equity | Combined tracking | WeekdayCallEquity (soft) | Penalty |
| Call spacing | Prevent back-to-back | CallSpacing (soft) | Penalty |

---

**Last Updated:** 2025-12-30
**Source:** Residency Scheduler codebase analysis
**Investigation Status:** Complete - G2_RECON SEARCH_PARTY
