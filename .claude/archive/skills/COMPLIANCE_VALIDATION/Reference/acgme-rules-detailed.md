# ACGME Rules - Detailed Reference

Complete ACGME (Accreditation Council for Graduate Medical Education) Common Program Requirements for resident duty hours, supervision, and educational standards.

**Source:** ACGME Common Program Requirements (Residency)
**Version:** 2022 (Effective July 1, 2022)
**URL:** https://www.acgme.org/globalassets/pfassets/programrequirements/cprresidency_2022v3.pdf

---

## Section VI: The Learning and Working Environment

### VI.A. Principles

The learning and working environment is essential to graduate medical education. Programs must:
- Ensure patient safety
- Maintain resident well-being
- Provide adequate supervision
- Establish a culture of professionalism

### VI.B. Professionalism

**VI.B.1.** Programs and their supervising institutions must educate residents and faculty regarding:
- Professional responsibilities
- Patient safety
- Quality improvement
- Supervision of residents
- Resident well-being

---

## VI.F. Duty Hours, On-Call Activities, and Working Environment

### VI.F.1. Maximum Hours of Work per Week

**ACGME Citation:** Section VI.F.1

**Requirement:**
> "Duty hours must be limited to **80 hours per week**, averaged over a **four-week period**, inclusive of all in-house clinical and educational activities, clinical work done from home, and all moonlighting."

**Implementation Details:**

#### Calculation Method
- **Rolling 4-Week Average:** Must check EVERY possible 28-day consecutive period
- **Includes:**
  - All in-house clinical duties
  - All educational activities (grand rounds, didactics, simulation)
  - Clinical work from home (telemedicine, chart reviews)
  - Internal moonlighting (within the institution)
  - External moonlighting (at other facilities)
- **Excludes:**
  - Reading/studying at home
  - Professional development activities outside duty hours
  - Voluntary educational activities

#### Warning Thresholds (Institutional)
| Status | Weekly Hours | Action Required |
|--------|-------------|-----------------|
| **SAFE** | < 75 hours | Continue monitoring |
| **WARNING** | 75-78 hours | Review schedule, plan mitigation |
| **AT RISK** | 78-80 hours | Immediate intervention |
| **VIOLATION** | > 80 hours | Schedule invalid, must fix |

#### Common Violations
1. **Holiday Coverage Clustering:** Multiple residents covering holidays leading to spike weeks
2. **Post-Deployment Overload:** Returning from TDY/deployment and immediately scheduled full-time
3. **Moonlighting Not Tracked:** External moonlighting hours not reported
4. **Home Call Miscalculated:** Home call hours not properly attributed

#### Validation Formula
```python
# For each resident, for each 28-day window
window_hours = sum(hours for day in 28_day_window)
average_weekly = window_hours / 4

if average_weekly > 80:
    # VIOLATION
```

---

### VI.F.2. Duty Periods

**VI.F.2.a. Maximum Duty Period Length**

**ACGME Citation:** Section VI.F.2.a

**Requirement:**
> "Duty periods of PGY-1 residents must be limited to a maximum of **16 hours** of continuous duty in the hospital.
> Duty periods of PGY-2 residents and above may be scheduled to a maximum of **24 hours** of continuous duty in the hospital."

**VI.F.2.a.(1) Additional Time for Transitions**

> "Programs must encourage residents to use alertness management strategies in the context of patient care responsibilities. Strategic napping, especially after 16 hours of continuous duty and between the hours of 10:00 p.m. and 8:00 a.m., is strongly suggested.
> It is essential for patient safety and resident education that effective transitions in care occur. Residents may be allowed to remain on-site in order to accomplish these goals, but this period of time must be no longer than an additional **four hours**."

**Implementation Details:**

#### PGY-1 Limits (Interns)
- **Maximum continuous duty:** 16 hours
- **With transition time:** 16 + 4 = 20 hours maximum
- **No exceptions**

#### PGY-2+ Limits (Senior Residents)
- **Maximum continuous duty:** 24 hours
- **With transition time:** 24 + 4 = 28 hours maximum
- **Transition time:** Must be for handoff/patient safety only

#### 24+4 Rule Details
- **First 24 hours:** Active patient care
- **Additional 4 hours:** Handoff, sign-out, education ONLY
- **No new patients** during the additional 4-hour period
- **Strategic napping encouraged** during night hours

#### Violation Examples
```
❌ PGY-1 assigned 8am-2am (18 hours) - EXCEEDS 16-hour limit
❌ PGY-2 assigned 7am-1pm next day (30 hours) - EXCEEDS 28-hour limit
✅ PGY-1 assigned 7am-11pm (16 hours) - COMPLIANT
✅ PGY-2 assigned 6am-10am next day (28 hours with handoff) - COMPLIANT
```

---

### VI.F.3. Minimum Time Off between Scheduled Duty Periods

**VI.F.3.a. One Day in Seven Free**

**ACGME Citation:** Section VI.F.3.a

**Requirement:**
> "Residents must be scheduled for a minimum of **one day in seven free from all educational and clinical responsibilities**, averaged over a four-week period, inclusive of call. One day is defined as one continuous 24-hour period free from all clinical, educational, and administrative activities."

**Implementation Details:**

#### Calculation Method
- **Continuous 24-hour period:** Must be a full calendar day or equivalent
- **Free from ALL activities:** No clinic, no rounds, no conferences, no call
- **Averaged over 4 weeks:** Must have at least 4 days off in any 28-day period
- **Minimum compliance:** At least 1 day every 7 days on average

#### Acceptable Patterns (28-day examples)
- **Strict:** 1 day off per week (4 days off in 28 days) ✅
- **Flexible:** 0-2-1-1 pattern (totaling 4 days) ✅
- **Borderline:** 0-0-0-4 pattern (all 4 days at end) ⚠️ Technically compliant but poor practice
- **Violation:** 3 days off in 28 days ❌

#### Simplified Implementation
**Conservative approach (recommended):**
> "Residents cannot work more than **6 consecutive calendar days**"

This ensures compliance while being easier to enforce than tracking rolling 28-day averages.

#### Common Violations
1. **Weekend Call Coverage:** Resident covers Saturday call, works through week, covers next Saturday
2. **Rotation Transitions:** No day off between ending one rotation and starting another
3. **Holiday Coverage:** Working through holiday weekends without relief

---

### VI.F.3.b. Minimum Time Off Between Duty Periods

**ACGME Citation:** Section VI.F.3.b

**Requirement:**
> "PGY-1 residents should have **10 hours** free of clinical work and education between daily duty periods.
> PGY-2 residents and above must have a minimum of **eight hours** between scheduled clinical work and education periods."

**Implementation Details:**

#### PGY-1 Requirements
- **Minimum:** 10 hours (strongly recommended)
- **Example:** End at 6pm → Cannot start before 4am next day

#### PGY-2+ Requirements
- **Minimum:** 8 hours (required)
- **Example:** End at 10pm → Cannot start before 6am next day

#### Post-Call Policies
**VI.F.3.b.(1) Post-Call:**
> "Residents must be prepared to enter the next duty period well-rested and fit to provide safe, effective patient care. This must occur within the context of the 80-hour weekly limit, averaged over four weeks."

**Recommended Practice:**
- Post-call residents should not return to duty until after 8-10 hours of rest
- Consider post-call day as half-day or day off
- No clinic assignments immediately post-call

---

### VI.F.4. Maximum Frequency of In-House Night Float

**ACGME Citation:** Section VI.F.4

**Requirement:**
> "Residents must not be scheduled for more than **six consecutive nights** of night float."

**Implementation Details:**

#### Night Float Definition
- **Night shift:** Typically 7pm-7am or similar overnight coverage
- **Night float rotation:** Block of consecutive night shifts
- **Does NOT include:** Occasional overnight call

#### Maximum Limits
- **Consecutive nights:** 6 maximum
- **Required break:** At least 1 night off before resuming night float
- **Monthly limit:** No specific ACGME limit, but institutional limits recommended

#### Common Violations
```
❌ Resident scheduled Mon-Sun night shifts (7 nights) - EXCEEDS LIMIT
✅ Resident scheduled Mon-Sat nights, Sun off, Mon resumes (6 consecutive) - COMPLIANT
⚠️  Resident does 6 nights, 1 off, 6 more nights - Technically compliant but fatigue risk
```

#### Institutional Best Practices
- **2-week blocks maximum** (e.g., 5 nights/week for 2 weeks = 10 total with days off)
- **Adequate recovery time** after night float (48+ hours before daytime duties)
- **Post-night-float clinic day** as recovery/transition

---

### VI.F.5. Maximum In-House On-Call Frequency

**ACGME Citation:** Section VI.F.5

**Requirement:**
> "Residents must be scheduled for in-house call no more frequently than every third night, when averaged over a four-week period."

**Implementation Details:**

#### Call Frequency Limits
- **Maximum:** Every 3rd night (q3 call)
- **Calculation:** Averaged over 4 weeks
- **Includes:** All in-house call (not home call)

#### Acceptable Patterns (per 28 days)
- **q3 call:** 9-10 calls per month ✅
- **q4 call:** 7-8 calls per month ✅ (better than minimum)
- **q2 call:** 14 calls per month ❌ VIOLATION

#### Home Call vs. In-House Call
**VI.F.5.a. Home Call:**
> "Time spent on patient care activities by residents on at-home call must count toward the 80-hour maximum weekly limit. The frequency of at-home call is not subject to the every-third-night limitation, but must satisfy the requirement for one-day-in-seven free of clinical work and education, when averaged over four weeks."

**Home call rules:**
- **No frequency limit** (can be every night if needed)
- **Hours count toward 80-hour limit** if called in
- **Must still meet 1-in-7 rule**

---

### VI.F.6. Moonlighting

**ACGME Citation:** Section VI.F.6

**Requirement:**
> "Moonlighting must not interfere with the ability of the resident to achieve the goals and objectives of the educational program, and must not interfere with the resident's fitness for work nor compromise patient safety."

**VI.F.6.a. Moonlighting Hours:**
> "Internal and external moonlighting activities must be counted toward the 80-hour maximum weekly limit."

**Implementation Details:**

#### Types of Moonlighting
1. **Internal moonlighting:** Extra shifts within the residency institution
2. **External moonlighting:** Work at other facilities

#### Tracking Requirements
- **All moonlighting hours** must be reported
- **Included in 80-hour limit**
- **Program director approval** required
- **Cannot compromise educational objectives**

#### Common Issues
```
❌ Resident works 70 program hours + 15 moonlighting hours = 85 total (VIOLATION)
❌ Resident moonlights but doesn't report hours (VIOLATION)
✅ Resident works 65 program hours + 10 moonlighting hours = 75 total (COMPLIANT)
```

---

### VI.F.7. In-House Call Rooms

**ACGME Citation:** Section VI.F.7

**Requirement:**
> "Residents must be provided with adequate, safe, and quiet on-call rooms, as required by the Clinical Learning Environment Review (CLER) Program."

---

### VI.F.8. Professionalism, Responsibility, and Patient Safety

**ACGME Citation:** Section VI.F.8

**Requirement:**
> "All residents and faculty members must demonstrate responsiveness to patient needs that supersedes self-interest. This includes the recognition that under certain circumstances, the best interests of the patient may be served by transitioning that patient's care to another qualified and rested provider."

---

## VI.C. Supervision

### VI.C.1. General Supervision Requirements

**ACGME Citation:** Section VI.C.1

**Requirement:**
> "All patient care must be supervised by qualified faculty. The privilege of progressive authority and responsibility, conditional independence, and a supervisory role in patient care delegated to each resident must be assigned by the program director and faculty members."

### VI.C.1.a. PGY-1 Supervision

**ACGME Citation:** Section VI.C.1.a

**Requirement:**
> "PGY-1 residents must have direct supervision immediately available."

**Implementation:**
- **Direct supervision:** Physically present or immediately available
- **Faculty-to-PGY-1 ratio:** Typically 1:2 (one faculty per two interns)
- **High-risk procedures:** Direct supervision required

### VI.C.1.b. PGY-2+ Supervision

**ACGME Citation:** Section VI.C.1.b

**Requirement:**
> "PGY-2 residents and above should generally have indirect supervision with direct supervision immediately available."

**Implementation:**
- **Indirect supervision:** Faculty available by phone/pager
- **Faculty-to-PGY-2+ ratio:** Typically 1:4 (one faculty per four senior residents)
- **Complex cases:** May require direct supervision

---

## VI.D. Well-Being

### VI.D.1. Resident Well-Being

**ACGME Citation:** Section VI.D.1

**Requirement:**
> "Programs must have a curriculum that includes resident well-being, including management of stress, fatigue, depression, substance use, and other behaviors that may put residents or patients at risk."

### VI.D.1.a. Fatigue Mitigation

**ACGME Citation:** Section VI.D.1.a

**Requirement:**
> "Programs must educate faculty members and residents to recognize signs of fatigue and sleep deprivation, and must adopt and apply policies to prevent and counteract potential negative effects."

**Strategies include:**
- Strategic napping during shifts
- Adequate time off between shifts
- Monitoring for burnout
- Access to mental health resources

---

## Violation Consequences

### Institutional Consequences

**Warning Status:**
- Initial citation for violations
- Corrective action plan required
- Follow-up review in 6-12 months

**Probation:**
- Continued violations after warning
- Increased oversight
- May affect program accreditation status

**Withdrawal of Accreditation:**
- Severe or repeated violations
- Failure to correct deficiencies
- Immediate impact on residents (must transfer)

### Reporting Requirements

**Programs must:**
- Self-report significant violations
- Document all duty hour violations
- Maintain audit trails
- Provide annual duty hour reports

---

## Documentation Requirements

### VI.F.9. Duty Hours Monitoring

**ACGME Citation:** Section VI.F.9

**Requirement:**
> "Programs must design an effective program-specific, ACGME-accredited, web-based system to monitor resident duty hours, and to prepare aggregate data for annual program evaluation and improvement."

**Implementation:**
- **Real-time tracking:** Duty hours logged regularly (at least weekly)
- **Validation:** Faculty review and attestation
- **Audit capability:** Historical data queryable
- **Exception reporting:** Violations flagged automatically

### Required Data Points

Programs must track:
- Daily duty hours (in-house and at-home call)
- Days off (24-hour periods)
- Moonlighting hours (internal and external)
- Duty period lengths
- Time off between shifts

---

## Program-Specific Variations

**NOTE:** Some specialties have program-specific requirements that modify these common requirements. Always check specialty-specific requirements for:

- Surgery programs (may have different duty hour structures)
- Obstetrics programs (labor/delivery coverage)
- Emergency medicine (shift-based structures)

**This document covers COMMON requirements applicable to all residency programs.**

---

## Quick Reference Table

| Rule | Limit | Averaged Over | Citation |
|------|-------|---------------|----------|
| Weekly Hours | 80 hours max | 4 weeks | VI.F.1 |
| PGY-1 Duty Period | 16 hours max (+ 4 handoff) | N/A | VI.F.2.a |
| PGY-2+ Duty Period | 24 hours max (+ 4 handoff) | N/A | VI.F.2.a |
| Days Off | 1 in 7 | 4 weeks | VI.F.3.a |
| PGY-1 Time Between Shifts | 10 hours | N/A | VI.F.3.b |
| PGY-2+ Time Between Shifts | 8 hours | N/A | VI.F.3.b |
| Night Float Max | 6 consecutive nights | N/A | VI.F.4 |
| In-House Call Frequency | Every 3rd night max | 4 weeks | VI.F.5 |
| Moonlighting | Counts toward 80h | 4 weeks | VI.F.6 |
| PGY-1 Supervision | Direct (immediately available) | N/A | VI.C.1.a |
| PGY-2+ Supervision | Indirect (available by phone) | N/A | VI.C.1.b |

---

## Institutional Policies (Example - Military MTF)

**These are program-specific and may vary:**

- **FMIT Coverage:** Weekly faculty rotation (not ACGME-mandated)
- **Night Float Headcount:** Exactly 1 resident (institutional)
- **NICU Friday Clinic:** Required for NICU residents (institutional)
- **Post-Call Blocking:** No clinic assignments post-call (institutional best practice)

**Always distinguish between ACGME regulatory requirements (Tier 1) and institutional policies (Tier 2).**

---

## Additional Resources

- **ACGME Website:** https://www.acgme.org
- **Common Program Requirements:** https://www.acgme.org/what-we-do/accreditation/common-program-requirements/
- **CLER Program:** https://www.acgme.org/what-we-do/clinical-learning-environment-review-cler/
- **Institutional Policies:** See program-specific guidelines

---

**Last Updated:** 2025-12-26
**Reviewed By:** COMPLIANCE_VALIDATION Skill
**Next Review:** 2026-07-01 (annual ACGME update cycle)
