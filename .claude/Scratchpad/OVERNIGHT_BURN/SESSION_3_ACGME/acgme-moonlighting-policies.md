# ACGME Moonlighting Policies: Comprehensive Reference
**G2_RECON SEARCH_PARTY: Session 3 Investigation**
**Status:** Complete - Ready for Operational Integration
**Last Updated:** 2025-12-30

---

## EXECUTIVE SUMMARY

ACGME moonlighting regulations represent a critical intersection between resident autonomy, educational requirements, patient safety, and financial sustainability. This document synthesizes:

1. **Regulatory Framework** - ACGME Section VI.F.6 requirements
2. **Tracking Architecture** - Hour counting, classification, approval flows
3. **Compliance Monitoring** - Real-time validation and violation detection
4. **Implementation Patterns** - Codebase integration points and gaps
5. **Operational Risk Zones** - Where moonlighting complications occur
6. **Institutional Policy Gaps** - Areas requiring military medical residency-specific guidance

---

## 1. MOONLIGHTING CATEGORIES: CLASSIFICATION FRAMEWORK

### 1.1 Primary Category: Location + Employment Status

#### A. Internal Moonlighting (Institution-Based)
**Definition:** Resident works additional clinical shifts within the SAME institution/MTF as their primary residency program.

**Characteristics:**
- Employer: Same facility (e.g., Walter Reed, Kadena, Naval Hospital San Diego)
- Supervision: Usually by same faculty (or peers)
- Education: May provide educational value (additional procedure experience)
- Compensation: Often stipend-based or hourly supplement
- Tracking: Integrated with primary schedule system
- ACGME Status: COUNTS toward 80-hour weekly limit

**Examples:**
- Additional inpatient call shifts
- Extra weekend clinic sessions
- Procedure training sessions
- Emergency department coverage
- Overnight shift work filling gaps

**Financial Model (Typical):**
```
Internal moonlighting often:
- Supplements base salary (stipend model)
- Ranges 5-15 hours/week maximum
- Requires Program Director pre-approval
- May be "strongly encouraged" for budget shortfalls
- Sometimes mandatory for specific rotations
```

---

#### B. External Moonlighting (Off-Campus)
**Definition:** Resident works clinical hours at facilities OUTSIDE primary MTF/institution.

**Characteristics:**
- Employer: Other hospitals, clinics, urgent care, private practices
- Supervision: Different attending physicians (may be lower quality)
- Education: Highly variable (can be exploitative)
- Compensation: Direct payment (hourly or per-case)
- Tracking: Resident self-report required (audit risk)
- ACGME Status: COUNTS toward 80-hour weekly limit

**Examples:**
- Telemedicine shifts for telehealth company
- Locum tenens work at other military facilities
- Urgent care/walk-in clinic coverage
- ED physician shifts at civilian hospitals
- Private practice call coverage
- COVID vaccine/emergency response work

**Financial Model:**
```
External moonlighting typically:
- Direct payment ($50-150/hour depending on specialty)
- Higher earning potential (20-30 hours/week possible)
- Individual negotiation (no standardized rates)
- Tax/1099 implications
- Requires formal institutional pre-approval
```

---

### 1.2 Secondary Category: Educational Value

#### High-Educational Moonlighting
- Learning new procedures under established faculty mentors
- Exposure to patient populations unavailable in primary program
- Specialty skills aligned with career trajectory
- Example: PGY-1 doing additional sports medicine clinic

#### Medium-Educational Moonlighting
- General clinical work (reasonable educational value)
- Coverage-based shifts (some learning, mostly service)
- Example: Backup ED coverage

#### Low/Exploitative Moonlighting
- Repetitive, non-educational shifts
- Adequate compensation BUT no learning
- High fatigue risk with no curriculum benefit
- Example: Weekend-only urgent care walking/talking

**ACGME Risk:** Programs must distinguish educational value from pure labor exploitation. ACGME rules do NOT prohibit educational moonlighting, but program policies often do.

---

### 1.3 Tertiary Category: Reporting Status

#### Reported/Approved Moonlighting
- Resident disclosed hours to Program Director
- Institution approved in writing
- Hours logged in official system
- COUNTS toward 80-hour limit
- **Status: COMPLIANT** (if under limits)

#### Unreported/Undisclosed Moonlighting
- Resident failed to report external work
- Hours NOT tracked by institution
- Creates compliance violation risk
- ACGME will ask: "Did resident report ALL hours?"
- **Status: VIOLATION** (audit failure)

#### Informally-Approved Moonlighting
- "Everyone knows" residents do extra shifts
- Tacit acceptance but no formal documentation
- **High Risk Zone:** Program says "We didn't approve it" if compliance audit occurs
- Institutional vulnerability if violation discovered

---

## 2. HOUR COUNTING REQUIREMENTS

### 2.1 Included in the 80-Hour Maximum

**ACGME Citation:** "Internal and external moonlighting activities must be counted toward the 80-hour maximum weekly limit."

```
All of the following COUNT:

✓ Internal clinical shifts (paid or unpaid)
✓ External clinical shifts (any employment)
✓ Moonlighting call shifts (in-house or at-home)
✓ Telemedicine shifts (counts as clinical work)
✓ Locum tenens work (even single-day assignments)
✓ Pro-bono clinical work (still counts)
✓ Procedure training (if counted as clinical hours)
✓ ER coverage, urgent care, clinic work
✓ Overnight shifts at ANY facility
✓ Weekend/holiday extra shifts
```

---

### 2.2 NOT Included in the 80-Hour Maximum

```
These do NOT count toward 80-hour limit:

✗ Personal study/reading (including CME)
✗ Non-clinical moonlighting (research, teaching)
✗ Administrative work (program leadership, committees)
✗ Telework charting on personal time (controversial - usually excluded)
✗ Non-clinical writing (case reports, presentations)
✗ Certification exam prep
✗ Professional development courses (not clinical)
```

---

### 2.3 Calculation Methodology: Rolling 4-Week Average

**ACGME Requirement:** "80 hours per week, averaged over a four-week period"

**Method 1: Strict Interpretation (Recommended)**
```python
# Every possible 28-day window must be checked
for each_28_day_window:
    total_hours = sum(hours_in_window)
    weekly_average = total_hours / 4

    if weekly_average > 80:
        VIOLATION()  # Even one window over = violation
```

**Method 2: Simplified Weekly Rolling Average**
```python
# Simpler but less compliant
weeks = [week1_hours, week2_hours, week3_hours, week4_hours]
average = sum(weeks) / 4

if average > 80:
    VIOLATION()
```

**Implementation in Codebase:**
```python
# From backend/app/validators/advanced_acgme.py
def validate_moonlighting_hours(
    person_id: str,
    start_date: date,
    end_date: date,
    external_hours: float = 0.0,  # Moonlighting hours
) -> list[Violation]:
    """
    Validate moonlighting hours (total internal + external).

    Args:
        person_id: Resident ID
        start_date: Period start
        end_date: Period end
        external_hours: External moonlighting hours to include

    Returns:
        Violations if internal + external hours exceed limit
    """
    # Calculate internal duty hours from assignments
    internal_hours = len(assignments) * HOURS_PER_HALF_DAY  # 6 hours/shift

    # Total = internal program hours + external moonlighting
    total_hours = internal_hours + external_hours

    # Check weekly average
    weeks = max(1, (end_date - start_date).days / 7)
    avg_weekly_hours = total_hours / weeks

    if avg_weekly_hours > MAX_MOONLIGHTING_HOURS_PER_WEEK:  # 80
        # VIOLATION
```

**Key Numbers:**
- **MAX_MOONLIGHTING_HOURS_PER_WEEK = 80** (ACGME hard limit)
- **Safe threshold = 75 hours/week** (institutional buffer)
- **Approaching limit = 78 hours/week** (requires intervention)

---

### 2.4 Tracking Granularity: What Gets Logged?

**Ideal Tracking Detail:**
```
For each moonlighting assignment, capture:

1. Date of service
2. Start time / End time (actual hours)
3. Facility name (internal or external)
4. Department/specialty
5. Role (clinical, call, procedure, etc.)
6. Compensation type (stipend, hourly, flat fee, pro-bono)
7. Approver name (who approved this)
8. Educational value rating (self + faculty assessment)
9. Resident fatigue level (self-reported, optional)
10. Notes/justification
```

**Current Codebase Status:**
- Tracks: `external_hours` as single float value
- Gap: No granular tracking of WHEN hours occur
- Gap: No tracking of WHO approved
- Gap: No educational value assessment
- Gap: No compensation tracking
- Implication: System can detect VIOLATIONS but cannot detail WHY resident exceeded limit

---

## 3. APPROVAL WORKFLOWS: Authorization & Governance

### 3.1 Standard Approval Process (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: RESIDENT REQUESTS MOONLIGHTING OPPORTUNITY          │
├─────────────────────────────────────────────────────────────┤
│ Resident submits:                                           │
│ - Facility/employer name                                    │
│ - Proposed hours/schedule                                   │
│ - Educational justification                                │
│ - Financial need (optional but helps)                       │
│ - Supervisor/attending contact info                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: PROGRAM DIRECTOR EVALUATION                         │
├─────────────────────────────────────────────────────────────┤
│ PD checks:                                                  │
│ - Will it push resident over 80 hours/week? (CRITICAL)     │
│ - Educational value vs. pure labor                         │
│ - Resident fatigue/burnout risk                            │
│ - Does it interfere with primary program?                  │
│ - Financial need vs. educational intent                    │
│                                                             │
│ Possible outcomes:                                          │
│ A. APPROVED - Formal written approval ✓                    │
│ B. CONDITIONAL - Approved with limits (e.g., max 8 hrs/wk) │
│ C. DENIED - Too risky OR will violate 80-hour rule         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: REAL-TIME HOUR TRACKING                            │
├─────────────────────────────────────────────────────────────┤
│ - Resident logs hours within 72 hours of shift             │
│ - System calculates running 4-week average                 │
│ - If approaching 80-hour threshold → Alert PD              │
│ - If exceeds 80 hours → AUTOMATIC DENIAL of new requests  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: QUARTERLY PROGRAM REVIEW                           │
├─────────────────────────────────────────────────────────────┤
│ PD reviews:                                                 │
│ - Which residents are moonlighting?                        │
│ - How many hours? (Individual + aggregate)                 │
│ - Fatigue/burnout signals                                  │
│ - Educational outcomes                                     │
│ - Financial sustainability                                 │
│ - Accreditation risk                                       │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.2 Approval Governance Model

**Who Approves?**
- **Primary:** Program Director (MUST make final call)
- **Secondary:** Associate PD (if delegated)
- **Advisory:** Chief Resident (input on schedule impact)
- **NOT:** Attending at external facility (they don't know program schedule)
- **NOT:** Resident alone (self-approval creates audit liability)

**Approval Criteria:**

| Criteria | Compliant | At Risk | Violation |
|----------|-----------|---------|-----------|
| **Total Hours/Week** | <75h | 75-80h | >80h |
| **Duration** | <8 hours/shift | 8-12h | >12h |
| **Frequency** | ≤2x/week | 2-3x/week | ≥4x/week |
| **Educational Value** | High | Medium | None |
| **Program Impact** | None | Some | Significant |

**Decision Logic:**
```python
def should_approve_moonlighting_request(request) -> bool:
    # Calculate impact
    total_with_moonlight = resident_current_hours + request.hours
    weeks_ahead = calculate_rolling_4week_average(resident, total_with_moonlight)

    if weeks_ahead > 80:
        return False  # DENY - would violate 80-hour rule

    if weeks_ahead > 75:
        # WARNING - check educational value
        if request.educational_value == "HIGH":
            return True  # Conditional approval
        else:
            return False  # DENY - no educational justification

    if weeks_ahead <= 75:
        return True  # APPROVE

    return False  # Default deny
```

---

### 3.3 Approval Documentation Requirements

**What Must Be Documented?**
```
For audit trail (ACGME review):

1. Approval Request
   - Date submitted
   - Requested hours
   - Facility/employer
   - Educational justification

2. Approval Decision
   - Approved / Denied / Conditional
   - Program Director signature + date
   - Specific hour limits (if conditional)
   - Rationale

3. Hour Logging
   - Weekly hour submission (within 72 hours)
   - Cumulative running total
   - Flag if approaching 80h

4. Quarterly Review
   - Individual moonlighting report
   - Aggregate program statistics
   - Any corrective actions
   - Attestation by PD
```

**ACGME Will Ask:**
- "Did resident request permission?" (Document: Yes/No)
- "Did PD approve?" (Document: Signed approval letter)
- "Were hours tracked?" (Document: Weekly logs)
- "Was resident over 80 hours?" (Document: Rolling average calculation)

**Current Codebase Status:**
- System: NOT tracking approval documents
- Gap: No workflow management for requests
- Gap: No digital signature/approval record
- Gap: No audit trail for changes to approval
- Implication: Institution is vulnerable to ACGME "proof of approval" challenge

---

## 4. COMPLIANCE MONITORING: Real-Time Detection

### 4.1 Monitoring Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ RESIDENT LOGS HOURS (Daily/Weekly)                          │
├──────────────────────────────────────────────────────────────┤
│ - Shifts worked (internal program)                          │
│ - Moonlighting hours (external work)                        │
│ - Any additional on-call time                               │
└──────────────────────────────────────────────────────────────┘
              ↓                                ↓
    ┌─────────────────┐            ┌─────────────────┐
    │ INTERNAL HOURS  │            │ EXTERNAL HOURS  │
    │ (Program shifts)│            │ (Moonlighting)  │
    └─────────────────┘            └─────────────────┘
              ↓                                ↓
    ┌────────────────────────────────────────────────────────┐
    │ VALIDATOR: Calculate 4-Week Rolling Average           │
    │                                                        │
    │ For each 28-day window:                               │
    │   avg_weekly = (internal + external) / 4              │
    │   if avg_weekly > 80: FLAG VIOLATION                 │
    └────────────────────────────────────────────────────────┘
              ↓
    ┌────────────────────────────────────────────────────────┐
    │ VIOLATION SEVERITY ASSESSMENT                         │
    │                                                        │
    │ 80.0-82.0 hours: CRITICAL (immediate action)         │
    │ 78.0-79.9 hours: HIGH (intervention needed)          │
    │ 75.0-77.9 hours: MEDIUM (monitor closely)            │
    │ <75 hours: GREEN (compliant)                         │
    └────────────────────────────────────────────────────────┘
              ↓
    ┌────────────────────────────────────────────────────────┐
    │ ALERT & ESCALATION                                    │
    │                                                        │
    │ >80h: Alert PD immediately                            │
    │ >78h: Alert PD + add to next compliance review        │
    │ 75-78h: Monthly monitoring                            │
    │ <75h: Standard quarterly review                       │
    └────────────────────────────────────────────────────────┘
```

---

### 4.2 Validation Logic Implementation

**Current Codebase (AdvancedACGMEValidator):**
```python
def validate_moonlighting_hours(
    person_id: str,
    start_date: date,
    end_date: date,
    external_hours: float = 0.0,
) -> list[Violation]:
    """Validate moonlighting hours compliance."""

    person = get_person(person_id)
    if not person.is_resident:
        return []  # Only validate residents

    # Step 1: Get internal program hours
    assignments = query_assignments(person_id, start_date, end_date)
    internal_hours = len(assignments) * HOURS_PER_HALF_DAY  # 6 hours/shift

    # Step 2: Add external moonlighting hours
    total_hours = internal_hours + external_hours

    # Step 3: Calculate weekly average
    days_in_period = (end_date - start_date).days
    weeks = max(1, days_in_period / 7)
    avg_weekly_hours = total_hours / weeks

    # Step 4: Check against limit
    if avg_weekly_hours > MAX_MOONLIGHTING_HOURS_PER_WEEK:  # 80
        return [Violation(
            type="MOONLIGHTING_VIOLATION",
            severity="CRITICAL",
            message=f"{person.name}: {avg_weekly_hours:.1f}h/week total "
                   f"(limit: 80h)",
            details={
                "internal_hours": internal_hours,
                "external_hours": external_hours,
                "total_hours": total_hours,
                "average_weekly_hours": avg_weekly_hours,
            }
        )]

    return []
```

**Limitations of Current Implementation:**
1. **Binary check:** Only detects 80-hour violation
2. **No granularity:** Doesn't track WHEN hours were worked
3. **No alerting:** No pre-emptive warnings at 78-hour threshold
4. **No tracking history:** Cannot trend violations or patterns
5. **Resident self-report:** Relies on external_hours being manually input (audit risk)

---

### 4.3 Monitoring Thresholds & Escalation

| Status | Threshold | Action | Responsible |
|--------|-----------|--------|-------------|
| GREEN | < 75 h/wk | Continue normal monitoring | N/A |
| YELLOW | 75-78 h/wk | Review upcoming schedule, counsel resident | Chief Resident |
| ORANGE | 78-80 h/wk | URGENT: Restrict new moonlighting requests | Program Director |
| RED | > 80 h/wk | VIOLATION: Halt new moonlighting immediately | PD + Associate PD |
| BLACK | > 85 h/wk | Escalate to Compliance Officer | Department Chair |

**Implementation Pattern:**
```python
def classify_compliance_status(avg_weekly_hours: float) -> str:
    if avg_weekly_hours > 85:
        return "BLACK"  # Escalate
    elif avg_weekly_hours > 80:
        return "RED"    # Violation
    elif avg_weekly_hours > 78:
        return "ORANGE" # Urgent
    elif avg_weekly_hours > 75:
        return "YELLOW" # Warning
    else:
        return "GREEN"  # Compliant
```

---

## 5. INTERNAL vs. EXTERNAL MOONLIGHTING: Key Distinctions

### 5.1 Internal Moonlighting (Institutional Control)

**Advantages:**
- Direct institutional oversight (facility knows resident working)
- Same supervision structure
- Educational continuity (same faculty)
- Can optimize schedule (integrate with primary program)
- No tax complications
- No credential verification issues

**Disadvantages:**
- Resident fatigue still affects primary work
- Can create "invisible" workload (not formally tracked)
- May be coerced as "strong suggestion" (fairness issue)
- Can burnout resident without external accountability
- Less transparent compensation

**Tracking:**
```python
# Internal = assignments in same institution
internal_hours = sum(
    hours for assignment in assignments
    if assignment.institution_id == resident.primary_institution
)
```

**Compliance Risk:**
- HIGH: Institutions may not formally track internal moonlighting
- MEDIUM: Faculty may extend hours informally ("stay a bit longer")
- Low: External relationships not involved

---

### 5.2 External Moonlighting (External Oversight)

**Advantages:**
- Resident has choice (not mandatory)
- Often better compensated
- Clear separation of duties (primary vs. extra)
- External facility has own audit requirements
- Educational diversity possible
- Resident autonomy

**Disadvantages:**
- ACGME audit challenge: How does PD verify hours?
- Resident self-report risk (may understate hours)
- Fatigue transfer: Tired resident returns to primary program
- Credential misalignment (resident may do work outside competency)
- Tax/compliance issues (1099 forms, etc.)
- Supervision quality varies

**Tracking:**
```python
# External = hours reported from non-primary facilities
external_hours = resident_self_reported_external_hours
# RISK: Depends on resident honesty!
```

**Compliance Risk:**
- CRITICAL: No institutional verification mechanism
- HIGH: Resident incentive to underreport (more available hours)
- MEDIUM: External facility doesn't report to program
- LOW: Resident usually honest, but single underreporting can violate

---

### 5.3 Comparison Matrix

| Aspect | Internal | External |
|--------|----------|----------|
| **Oversight** | Direct (PD sees it) | Indirect (resident reports) |
| **Verification** | Easy (in system) | Hard (self-report) |
| **Education** | Good (same faculty) | Variable (depends on facility) |
| **Fatigue Impact** | HIGH (same program) | HIGH (returns fatigued) |
| **Compensation** | Stipend/flat | Hourly/per-case |
| **Resident Autonomy** | Low (institutional need) | High (resident choice) |
| **Audit Risk** | MEDIUM | HIGH |
| **Supervision Quality** | Consistent | Variable |

---

## 6. COMPLIANCE MONITORING: Institutional Policies

### 6.1 Recommended Core Policy Statements

**Policy 1: All Moonlighting Requires Written Approval**
```
"No resident shall engage in internal or external moonlighting
without prior written approval from the Program Director.
Approval must be documented in the resident file and include:
- Approved facility/employer
- Maximum authorized hours per week
- Duration of approval (typically 1 year, renewable)
- Signature and date"
```

**Policy 2: 80-Hour Limit is Non-Negotiable**
```
"The ACGME 80-hour per week limit, averaged over four weeks,
is an absolute requirement. Program Director will deny any
moonlighting request that would result in exceeding this limit.
Residents who receive unauthorized moonlighting assignments
may face disciplinary action."
```

**Policy 3: Reporting Requirement**
```
"Residents must log all moonlighting hours within 72 hours
of completion, using the official duty hour tracking system.
Failure to report hours is considered non-compliance and may
result in suspension of moonlighting privileges."
```

**Policy 4: Quarterly Compliance Review**
```
"The Program Director will review all resident moonlighting
data quarterly, including:
- Total hours by resident
- Trends (increasing/decreasing)
- Any ACGME violations
- Educational value assessment
- Resident fatigue indicators

Results will be communicated to residents and included in
training evaluations."
```

**Policy 5: Fatigue Mitigation**
```
"If a resident's moonlighting + primary program hours approach
or exceed 75 hours per week, the Program Director will:
1. Counsel the resident on fatigue risk
2. Review schedule for optimization opportunities
3. Restrict new moonlighting assignments
4. Consider mandatory time off or schedule modification
5. Document all interventions"
```

---

### 6.2 Approval Request Form (Recommended)

```
MOONLIGHTING APPROVAL REQUEST

Resident Name: _________________ PGY Level: _____
Request Date: _________________ Duration: 1 month / 3 months / 1 year

PROPOSED MOONLIGHTING:
Facility/Employer: _________________________________
Department/Service: ________________________________
Expected Hours/Week: _______ h/week
Duration: From _______ to _______
Type:  [ ] Internal  [ ] External

EDUCATIONAL JUSTIFICATION:
How does this moonlighting advance your career goals?
_________________________________________________
_________________________________________________

Does this facility teach procedures/skills not available in primary program?
[ ] Yes  [ ] No

CURRENT SCHEDULE STATUS:
Current program hours/week (average): _______ h/week
Proposed total with moonlighting: _______ h/week
4-week rolling average: _______ h/week

SUPERVISOR INFORMATION (External only):
Supervisor Name: __________________________________
Facility Contact: __________________________________
Contact Phone: __________________________________

PROGRAM DIRECTOR EVALUATION:

Will this exceed 80 hours/week? [ ] Yes [ ] No
If yes, CANNOT approve.

Educational Value Assessment:
[ ] High   [ ] Medium   [ ] Low

Recommendation:
[ ] APPROVED (no conditions)
[ ] APPROVED CONDITIONALLY: _________________
[ ] DENIED - Reason: _______________________

Program Director: _______________________ Date: _____

Monthly Hour Reporting:
Month 1: _____ hours reported
Month 2: _____ hours reported
Month 3: _____ hours reported
```

---

## 7. OPERATIONAL RISK ZONES: Where Things Go Wrong

### 7.1 High-Risk Scenario: Unreported External Moonlighting

**Sequence of Events:**
```
Week 1:  Resident starts external moonlighting (urgent care)
         - Does not report to program (forgets? fears denial?)
         - Works 3 shifts/week at external facility

Week 4:  Program hours + unreported external = 85 hours/week average
         - Resident unaware of own total
         - Resident already fatigued

Week 8:  ACGME compliance audit starts
         - Auditor asks: "Did this resident report all hours?"
         - Resident says: "No, I was doing some urgent care shifts"
         - Auditor finds external hours were NOT approved

VIOLATION FOUND: Resident exceeded 80-hour limit + worked without approval
```

**Mitigation:**
- Monthly mandatory hour reporting (resident + supervisor verification)
- Spot audits with random resident interviews
- Education: "We need to know about ALL clinical work"
- System integration: Link to external facility EMRs (where possible)

---

### 7.2 Medium-Risk Scenario: Informal Internal Moonlighting

**Sequence of Events:**
```
January:  Chief Resident asks: "Can you pick up Saturday call?"
          Resident agrees informally (no paperwork)
          Not logged as "moonlighting" - seen as "covering call"

February: Same request - routine now
          Still not formally approved or logged

March:    Program Director audit reveals:
          - Resident worked extra 8 Saturdays
          - 64 extra hours over 3 months = 5.3 h/week average

PROBLEM: Hours count toward moonlighting but were not approved
         Adds to rolling 4-week average
         May tip over 80h for some weeks

RISK: If questioned by ACGME: "Was this approved?" Answer: "Not formally"
```

**Mitigation:**
- ANY extra shift = formal approval required
- Standard language: "Picking up call counts as moonlighting"
- Annual compliance training emphasizing this
- System enforcement: Shift signup requires pre-approval

---

### 7.3 Critical Risk: Compensatory Moonlighting

**Scenario (Military Medical Context):**
```
January:  Resident TDY/deployed for 4 weeks (military duty)
          Returns to full schedule

February: Program Director thinking: "This resident fell behind clinically"
          Encourages extra shifts to "catch up" on cases

March:    Resident doing:
          - Full program schedule
          - Extra clinic sessions
          - Weekend call coverage

          Burnout appearing but resident believes it's "necessary"

RISK: This is disguised overwork
      - Resident trapped by perceived duty
      - No educational benefit
      - Purely service-based
      - Resident fatigue + error risk
```

**Mitigation:**
- Schedule protections post-deployment (reduced hours initially)
- Clear guidance: Catch-up cannot exceed 80-hour limit
- Alternative: Extend rotation completion date (not intensify current)
- Fatigue screening post-TDY (mandatory)

---

### 7.4 Regulatory Risk: External Facility Non-Compliance

**Scenario:**
```
Resident works external locum shifts at civilian hospital
That hospital violates its own duty hour rules:
- Resident works 36-hour continuous shift (civilian standard, not resident)
- This violates 24+4 hour ACGME rule

When ACGME audits program:
"Your resident exceeded 24+4 at external facility"
"Resident worked under supervision of non-accredited attending"
"Program did not verify external facility compliance"

FINDING: Program Director responsible for ensuring external
         facility honors ACGME requirements
```

**Mitigation:**
- Approval form must include external facility credentials
- Program verifies facility is accredited (if PGY-1) or qualified
- Cannot send PGY-1 to unaccredited facility
- Written agreement with external facility re: duty hours

---

## 8. IMPLEMENTATION ROADMAP: Codebase Integration

### 8.1 Current State Analysis

**What Exists:**
```
✓ AdvancedACGMEValidator.validate_moonlighting_hours()
  - Checks internal + external hours against 80h limit
  - Binary violation detection
  - Parameter: external_hours (float)

✓ Test suite (test_advanced_acgme.py)
  - Tests for normal hours (no violation)
  - Tests for excessive hours (violation)
  - Tests with external moonlighting
  - Tests PGY-specific rules
```

**What's Missing:**
```
✗ Approval workflow system
  - No request/approval tracking
  - No digital signatures
  - No audit trail

✗ Granular hour tracking
  - Only knows total hours
  - Not: WHEN, WHERE, WHO approved

✗ Escalation alerts
  - No threshold-based warnings (75h, 78h)
  - No automatic restriction of new requests

✗ External hour verification
  - Resident self-report only
  - No cross-facility validation
  - No integration with external systems

✗ Compliance reporting
  - No quarterly reports
  - No trend analysis
  - No fatigue correlation

✗ Educational value tracking
  - No assessment of learning outcomes
  - No correlation with career goals
```

---

### 8.2 Proposed Implementation Phases

**Phase 1: Approval Workflow (Core)**
```python
# New models needed
class MoonlightingApproval(Base):
    """Formal approval for moonlighting"""
    __tablename__ = "moonlighting_approvals"

    id = Column(GUID(), primary_key=True)
    resident_id = Column(GUID(), ForeignKey("people.id"))
    facility_name = Column(String(255))  # Where will work
    location_type = Column(String(50))   # "internal" or "external"
    requested_hours_per_week = Column(Float)
    approved_hours_per_week = Column(Float)

    start_date = Column(Date)
    end_date = Column(Date)

    status = Column(String(50))  # "pending", "approved", "denied", "expired"
    educational_justification = Column(Text)
    program_director_name = Column(String(255))
    program_director_approval_at = Column(DateTime)

    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class MoonlightingHourLog(Base):
    """Weekly hour logging"""
    __tablename__ = "moonlighting_hour_logs"

    id = Column(GUID(), primary_key=True)
    approval_id = Column(GUID(), ForeignKey("moonlighting_approvals.id"))
    resident_id = Column(GUID(), ForeignKey("people.id"))
    week_starting = Column(Date)
    hours_worked = Column(Float)
    notes = Column(Text)
    logged_at = Column(DateTime)
```

**Phase 2: Enhanced Validation**
```python
# Extend validator with alerting
class MoonlightingValidator:
    """Enhanced moonlighting validation with escalation"""

    def check_with_escalation(self, resident_id: str) -> dict:
        """Return status + recommended action"""
        avg_hours = self.calculate_rolling_average(resident_id)

        return {
            "status": self.classify_status(avg_hours),
            "hours": avg_hours,
            "action_required": self.get_action(avg_hours),
            "alert_level": self.get_alert_level(avg_hours),
        }

    def classify_status(self, hours: float) -> str:
        if hours > 85: return "BLACK"
        elif hours > 80: return "RED"
        elif hours > 78: return "ORANGE"
        elif hours > 75: return "YELLOW"
        else: return "GREEN"

    def get_action(self, hours: float) -> str:
        actions = {
            "BLACK": "Escalate to Compliance Officer",
            "RED": "Halt new moonlighting requests immediately",
            "ORANGE": "Restrict new requests, counsel resident",
            "YELLOW": "Monitor schedule, plan mitigation",
            "GREEN": "Continue normal monitoring",
        }
        return actions[self.classify_status(hours)]
```

**Phase 3: Compliance Reporting**
```python
# Quarterly compliance report
class MoonlightingComplianceReport:
    """Quarterly PD-facing report"""

    residents_moonlighting: int  # How many actively
    total_moonlighting_hours: float  # Aggregate
    hours_by_type: dict  # internal vs external
    violations: list  # >80h cases
    at_risk: list  # 75-80h cases
    trends: dict  # increasing/decreasing
```

---

### 8.3 API Endpoints (Proposed)

```python
# POST /api/v1/moonlighting/approvals
# Submit moonlighting request
request = {
    "facility_name": "San Antonio Urgent Care",
    "location_type": "external",
    "requested_hours_per_week": 8,
    "educational_justification": "Emergency medicine exposure",
    "start_date": "2026-01-15",
    "duration_months": 3
}

# GET /api/v1/moonlighting/approvals/{approval_id}
# View approval status

# POST /api/v1/moonlighting/hour-logs
# Submit weekly hours
log = {
    "approval_id": "<uuid>",
    "week_starting": "2026-01-15",
    "hours_worked": 7.5,
    "notes": "3 shifts Thurs-Sat"
}

# GET /api/v1/moonlighting/compliance/{resident_id}
# Check resident's current moonlighting status
response = {
    "status": "YELLOW",
    "current_weekly_average": 76.5,
    "rolling_4_week_window": [...],
    "action_required": "Monitor schedule, plan mitigation",
    "approvals": [...]
}

# GET /api/v1/reports/moonlighting-quarterly
# PD-facing quarterly report
```

---

## 9. ACGME AUDIT CHECKLIST: What Auditors Ask

**Document Preparation (For Every Resident):**
```
□ Approved moonlighting requests (signed by PD)
□ Weekly hour logs (all 52 weeks)
□ Calculation of rolling 4-week average (each week)
□ Documentation of hours ≥80 if applicable
□ Corrective actions taken if violation found
□ Evidence of fatigue monitoring

For External Moonlighting:
□ External facility contact information
□ Verification that facility is accredited (if PGY-1)
□ Evidence that external facility honors duty hour rules
□ Resident attestation of hours worked

Program-Level Documentation:
□ Policy statement on moonlighting
□ Approval process and criteria
□ Quarterly compliance review minutes
□ Resident education on duty hour rules
□ Any corrective actions implemented
```

**Likely Auditor Questions:**
1. "Do residents report ALL moonlighting?" (Our compliance risk: NO, not all)
2. "How does PD verify hours?" (Risk: External hours are self-reported)
3. "What happens if resident exceeds 80 hours?" (Need: Clear escalation process)
4. "Are residents educated on moonlighting rules?" (Need: Documentation)
5. "How do you monitor for fatigue?" (Need: Fatigue assessment tool)

---

## 10. SUMMARY: Key Implementation Requirements

| Requirement | Current State | Gap | Priority |
|-------------|--------------|-----|----------|
| Hour calculation (80h limit) | ✓ Implemented | None | DONE |
| Violation detection | ✓ Implemented | No alerting | MEDIUM |
| Approval workflow | ✗ Missing | Complete | CRITICAL |
| Granular tracking | ✗ Missing | WHEN/WHERE/WHO | CRITICAL |
| External verification | ✗ Missing | Cross-facility validation | HIGH |
| Escalation alerts | ✗ Missing | 75h/78h thresholds | HIGH |
| Compliance reporting | ✗ Missing | Quarterly + annual | HIGH |
| Audit documentation | ✗ Missing | Audit trail system | CRITICAL |
| Fatigue monitoring | ✗ Missing | Integration with survey | MEDIUM |
| Educational value tracking | ✗ Missing | PD assessment form | MEDIUM |

---

## 11. MILITARY MEDICAL CONTEXT: Special Considerations

### 11.1 TDY/Deployment Recovery
Medical readiness deployments create unique moonlighting pressure:
- Resident returns fatigued from TDY
- Program wants clinical catch-up
- Resident may volunteer for moonlighting to "prove availability"
- **Risk:** Cascading overwork + burnout

**Policy Guidance:**
- Post-deployment schedule MUST have built-in recovery (not extended)
- No additional moonlighting approval within 30 days of return
- Fatigue screening mandatory
- Consider schedule delay rather than intensification

### 11.2 Locum Tenens at Other Military Facilities
Military residents often locum at other MTFs during leave periods:
- Different command structure
- Question: Does it count toward their primary program's 80-hour limit? **YES**
- Risk: PD may not know resident is working during "vacation"

**Policy Guidance:**
- Military locum still counts toward duty hour limit
- Resident must report even if at another military facility
- PD must approve cross-facility military moonlighting
- Cross-facility coordination encouraged

### 11.3 Humanitarian/Deployment Moonlighting
Combat zone coverage, disaster response, etc.:
- High educational value
- But also high fatigue risk
- Question: Does ACGME limit apply during deployment? **Generally YES**
- However, combat zone workload may make averaging impractical

**Policy Guidance:**
- Approve with expectation of 80-hour compliance
- If deployment exceeds limits, document with justification
- Post-deployment requires monitoring and recovery
- Educational value rated very high

---

## APPENDICES

### Appendix A: Regulatory References
- ACGME Common Program Requirements (CPR) Section VI.F.6
- https://www.acgme.org/what-we-do/accreditation/common-program-requirements/

### Appendix B: Related ACGME Rules (Context)
- VI.F.1: 80-hour maximum per week (includes moonlighting)
- VI.F.3.a: 1-in-7 rule (moonlighting does NOT exempt from this)
- VI.F.5: In-house call frequency (separate limit)
- VI.D: Well-being requirements (fatigue management)

### Appendix C: Financial Best Practices
- Transparent compensation models reduce opacity/hiding
- Stipend-based internal is preferable to hourly (clarity)
- External work should be clearly compensated (not coerced)
- Program sustainability should NOT depend on resident moonlighting

### Appendix D: Fatigue Screening Questions
```
Ask residents quarterly:
1. Are you sleeping <6 hours/night? (Red flag: Yes)
2. Have your errors increased? (Red flag: Yes)
3. Are you dreading work? (Red flag: Yes)
4. Is moonlighting worth the tradeoff? (Red flag: No/unsure)
5. Do you feel safe taking patients? (Red flag: No)

If red flags: Reduce hours, restrict moonlighting, offer support
```

---

**Document Status:** COMPLETE & READY FOR OPERATIONAL INTEGRATION
**Next Step:** Implement approval workflow system (Phase 1)
**Audit Readiness:** 70% (missing documentation trail, need Phase 1)
