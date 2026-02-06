# SWAP_REQUEST - Prompt Template

> **Purpose:** Process resident/faculty schedule swap requests with safety checks, impact assessment, and decision documentation
> **Complexity:** Low-Medium
> **Typical Duration:** 2-5 minutes
> **Prerequisites:** Access to current schedule, resident qualifications, swap policies
> **Version:** 1.0.0
> **Last Updated:** 2025-12-26

---

## Input Parameters

### Required

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `{{requester}}` | String | Person requesting swap | `"PGY2-01"` or `"FAC-APD"` |
| `{{target_date}}` | String | Date(s) of shift to swap | `"2024-01-15"` or `"2024-01-15 to 2024-01-17"` |
| `{{swap_type}}` | String | Type of swap | `"one_to_one"`, `"absorb"`, `"find_coverage"`, `"pool"` |

### Optional

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `{{swap_partner}}` | String | `null` | Other person in swap (if one-to-one) | `"PGY2-02"` |
| `{{reason}}` | String | `"personal"` | Why swap is needed | `"family emergency"`, `"conference"`, `"personal"` |
| `{{urgency}}` | String | `"standard"` | Priority level | `"routine"`, `"standard"`, `"urgent"`, `"emergency"` |
| `{{rotation}}` | String | Auto-detect | Rotation being swapped | `"inpatient"`, `"night_float"`, `"call"` |
| `{{auto_match}}` | Boolean | `false` | Find compatible swap partner automatically | `true`/`false` |
| `{{safety_level}}` | String | `"standard"` | Validation strictness | `"relaxed"`, `"standard"`, `"strict"` |
| `{{include_rationale}}` | Boolean | `true` | Include decision reasoning | `true`/`false` |
| `{{notification_method}}` | String | `"email"` | How to notify parties | `"email"`, `"sms"`, `"both"` |

---

## Template

```markdown
# Swap Request Processing

[IF urgency == "emergency"]
🚨 **EMERGENCY SWAP REQUEST**
Priority: IMMEDIATE - Process within 1 hour
[ENDIF]

[IF urgency == "urgent"]
⚠️ **URGENT SWAP REQUEST**
Priority: HIGH - Process within 4 hours
[ENDIF]

---

## Request Details

**Requester:** {{requester}}
**Target Date(s):** {{target_date}}
**Swap Type:** {{swap_type}}
[IF swap_partner]
**Swap Partner:** {{swap_partner}}
[ENDIF]
**Reason:** {{reason}}
**Urgency:** {{urgency|STANDARD}}
**Submitted:** [Timestamp]

---

## Swap Type Definition

[IF swap_type == "one_to_one"]
### One-to-One Swap

**Definition:** Two residents exchange shifts on different dates.

**Participants:**
- **Giver:** {{requester}} (gives up {{target_date}})
- **Receiver:** {{swap_partner}} (receives {{target_date}})
- **Exchange:** {{swap_partner}} gives up [date] to {{requester}}

**Example:**
- PGY2-01 swaps their Jan 15 inpatient shift with PGY2-02's Jan 22 inpatient shift
- Result: PGY2-01 works Jan 22, PGY2-02 works Jan 15

[ELIF swap_type == "absorb"]
### Absorb Swap (Give Away)

**Definition:** One resident gives away a shift to another, without receiving a shift in return.

**Participants:**
- **Giver:** {{requester}} (gives up {{target_date}})
- **Receiver:** {{swap_partner}} (receives {{target_date}})

**Example:**
- PGY2-01 gives their Jan 15 call shift to PGY2-02
- Result: PGY2-01 has day off Jan 15, PGY2-02 works Jan 15 (extra shift)

⚠️ **Note:** Receiver must not exceed duty hour limits.

[ELIF swap_type == "find_coverage"]
### Find Coverage

**Definition:** Requester needs coverage but hasn't identified a replacement yet.

**Participants:**
- **Requester:** {{requester}} (needs coverage for {{target_date}})
- **Potential Covers:** [To be determined]

**Process:**
[IF auto_match]
1. System will search for compatible residents
2. Notify best matches
3. First to accept gets the shift
[ELSE]
1. Manual notification to eligible residents
2. Chief resident coordinates responses
3. Assignment once volunteer found
[ENDIF]

[ELIF swap_type == "pool"]
### Pool Swap (Float Pool Coverage)

**Definition:** Shift covered by designated float pool resident (not a specific swap partner).

**Participants:**
- **Requester:** {{requester}} (needs coverage for {{target_date}})
- **Float Pool:** [System assigns from pool]

**Note:** Float pool exists for emergency coverage. May not be available for routine requests.

[ENDIF]

---

## Current Schedule Context

### Requester Current State

**{{requester}} Schedule:**
- **Current rotation:** {{requester_current_rotation}}
- **Hours this week:** {{requester_hours_this_week}} / 80
- **Hours this 4-week period:** {{requester_hours_4week}} / 80 avg
- **Rest days (last 7 days):** {{requester_rest_days}}
- **Assignments this month:** {{requester_assignments_count}}

**Shift Details ({{target_date}}):**
- **Rotation:** {{rotation}}
- **Type:** {{shift_type}} (e.g., call, day, night)
- **Duration:** {{shift_duration}} hours
- **Coverage required:** {{coverage_required}} (yes/no)

[IF swap_partner]
### Swap Partner Current State

**{{swap_partner}} Schedule:**
- **Current rotation:** {{partner_current_rotation}}
- **Hours this week:** {{partner_hours_this_week}} / 80
- **Hours this 4-week period:** {{partner_hours_4week}} / 80 avg
- **Rest days (last 7 days):** {{partner_rest_days}}
- **Assignments this month:** {{partner_assignments_count}}

[IF swap_type == "one_to_one"]
**Exchange Shift Details:**
- **Date:** {{exchange_date}}
- **Rotation:** {{exchange_rotation}}
- **Type:** {{exchange_shift_type}}
- **Duration:** {{exchange_shift_duration}} hours
[ENDIF]

[ENDIF]

---

## Safety Checks

[IF safety_level == "strict"]
### Strict Validation (All must pass)
[ELIF safety_level == "relaxed"]
### Relaxed Validation (Warnings allowed)
[ELSE]
### Standard Validation
[ENDIF]

#### ACGME Compliance Checks

1. **80-Hour Rule (Requester)**
   - Current 4-week avg: {{requester_hours_4week}}
   - After swap: {{requester_hours_4week_after}}
   - Status: [✅ Pass / ⚠️ Warning / ❌ Fail]
   - Details: {{compliance_details}}

[IF swap_partner]
2. **80-Hour Rule (Swap Partner)**
   - Current 4-week avg: {{partner_hours_4week}}
   - After swap: {{partner_hours_4week_after}}
   - Status: [✅ Pass / ⚠️ Warning / ❌ Fail]
   - Details: {{compliance_details}}
[ENDIF]

3. **1-in-7 Rest (Requester)**
   - Rest days last 7 days: {{requester_rest_days}}
   - After swap: {{requester_rest_days_after}}
   - Status: [✅ Pass / ⚠️ Warning / ❌ Fail]

[IF swap_partner]
4. **1-in-7 Rest (Swap Partner)**
   - Rest days last 7 days: {{partner_rest_days}}
   - After swap: {{partner_rest_days_after}}
   - Status: [✅ Pass / ⚠️ Warning / ❌ Fail]
[ENDIF]

5. **Continuous Duty Limits**
   - Shift duration: {{shift_duration}} hours
   - Allowed for level: {{max_duty_hours}} hours
   - Status: [✅ Pass / ❌ Fail]

6. **Rest Between Shifts**
   - Time between shifts: {{time_between_shifts}} hours
   - Required minimum: {{minimum_rest_between}} hours
   - Status: [✅ Pass / ❌ Fail]

#### Operational Checks

7. **Credential Requirements**
   [IF swap_partner]
   - **Requester qualified for exchange shift?** [✅ Yes / ❌ No]
     - Required: {{exchange_rotation_requirements}}
     - Requester has: {{requester_qualifications}}
   - **Partner qualified for requested shift?** [✅ Yes / ❌ No]
     - Required: {{rotation_requirements}}
     - Partner has: {{partner_qualifications}}
   [ELSE]
   - **Coverage assignment will check qualifications**
   [ENDIF]

8. **Coverage Adequacy**
   - **Minimum coverage met after swap?** [✅ Yes / ❌ No]
   - Required: {{minimum_coverage}}
   - After swap: {{coverage_after_swap}}

9. **Supervision Ratios**
   - **PGY-1 supervision maintained?** [✅ Yes / ❌ No / N/A]
   - Required ratio: {{required_ratio}}
   - After swap: {{actual_ratio}}

#### Policy Checks

10. **Swap Limit**
    - **Swaps this month (requester):** {{requester_swap_count}} / {{max_swaps_per_month}}
    - Status: [✅ Within limit / ⚠️ At limit / ❌ Exceeds limit]

[IF swap_partner]
11. **Swap Limit (Partner)**
    - **Swaps this month (partner):** {{partner_swap_count}} / {{max_swaps_per_month}}
    - Status: [✅ Within limit / ⚠️ At limit / ❌ Exceeds limit]
[ENDIF]

12. **Notice Period**
    - **Days before shift:** {{days_before_shift}}
    - **Required notice:** {{required_notice_days}} days
    - Status: [✅ Adequate / ⚠️ Short notice / ❌ Too late]

13. **Blackout Dates**
    - **Is {{target_date}} a blackout date?** [✅ No / ❌ Yes]
    - Blackout reason: {{blackout_reason}}

---

## Safety Check Summary

[IF all_checks_pass]
✅ **ALL SAFETY CHECKS PASSED**

Swap is safe to proceed.

[ELIF warnings_only]
⚠️ **WARNINGS DETECTED** (but no hard failures)

Swap can proceed with caution. Review warnings below:
[FOR warning IN warnings]
- {{warning.check_name}}: {{warning.message}}
[ENDFOR]

[ELSE]
❌ **SAFETY CHECK FAILURES**

Swap cannot proceed as requested. Failures:
[FOR failure IN failures]
- **{{failure.check_name}}**: {{failure.message}}
  - **Why this matters:** {{failure.impact}}
  - **Possible solutions:** {{failure.suggestions}}
[ENDFOR]

[ENDIF]

---

## Impact Assessment

### Workload Impact

**{{requester}}:**
- **Before swap:**
  - Shifts this month: {{requester_shifts_before}}
  - Total hours: {{requester_hours_before}}
  - Weekend shifts: {{requester_weekends_before}}
- **After swap:**
  - Shifts this month: {{requester_shifts_after}} (Δ: {{delta_shifts}})
  - Total hours: {{requester_hours_after}} (Δ: {{delta_hours}})
  - Weekend shifts: {{requester_weekends_after}} (Δ: {{delta_weekends}})

[IF swap_partner]
**{{swap_partner}}:**
- **Before swap:**
  - Shifts this month: {{partner_shifts_before}}
  - Total hours: {{partner_hours_before}}
  - Weekend shifts: {{partner_weekends_before}}
- **After swap:**
  - Shifts this month: {{partner_shifts_after}} (Δ: {{delta_shifts}})
  - Total hours: {{partner_hours_after}} (Δ: {{delta_hours}})
  - Weekend shifts: {{partner_weekends_after}} (Δ: {{delta_weekends}})
[ENDIF]

### Coverage Impact

**{{rotation}} Rotation:**
- **Coverage before swap:** {{coverage_before}} residents
- **Coverage after swap:** {{coverage_after}} residents
- **Minimum required:** {{minimum_coverage}}
- **Impact:** [No change / Improved / Reduced but adequate / ⚠️ Below minimum]

### Equity Impact

[IF swap_type == "one_to_one"]
**Workload Distribution:**
- Swap creates roughly equal exchange (fair trade)
- Equity score change: {{equity_delta}} (near zero is ideal)

[ELIF swap_type == "absorb"]
**Workload Distribution:**
- {{requester}} reduces workload by {{hours_reduced}} hours
- {{swap_partner}} increases workload by {{hours_increased}} hours
- Equity score change: {{equity_delta}}
  [IF equity_delta > 0]
  ✅ Improves overall equity (overworked resident reducing load)
  [ELIF equity_delta < -5]
  ⚠️ Worsens equity (creates imbalance)
  [ENDIF]
[ENDIF]

---

## Decision

[IF all_checks_pass OR (warnings_only AND safety_level != "strict")]

### ✅ APPROVED

**Swap request is APPROVED.**

[IF include_rationale]
**Rationale:**
{{approval_rationale}}

**Key factors in approval:**
1. {{approval_factor_1}}
2. {{approval_factor_2}}
3. {{approval_factor_3}}
[ENDIF]

**Conditions (if any):**
[IF approval_conditions]
[FOR condition IN approval_conditions]
- {{condition}}
[ENDFOR]
[ELSE]
None - unconditional approval
[ENDIF]

**Next Steps:**
1. Update schedule system with swap
2. Notify {{requester}} and {{swap_partner}} of approval
3. Confirm assignments with affected rotations
4. Document swap in audit trail
5. [IF urgency == "emergency"] Expedite notifications (within 1 hour)

**Rollback Window:**
- Swap can be reversed within {{rollback_hours}} hours
- Contact: {{contact_for_rollback}}

[ELSE]

### ❌ DENIED

**Swap request is DENIED.**

[IF include_rationale]
**Rationale:**
{{denial_rationale}}

**Primary reason(s) for denial:**
1. {{denial_reason_1}}
2. {{denial_reason_2}}
[ENDIF]

**Specific issues:**
[FOR issue IN denial_issues]
- **{{issue.name}}**: {{issue.explanation}}
[ENDFOR]

**Alternative Options:**

[IF auto_match AND swap_type == "find_coverage"]
#### Option 1: Auto-Match Alternative Partners

System has identified these compatible residents:
[FOR candidate IN match_candidates]
{{loop.index}}. **{{candidate.id}}** ({{candidate.level}})
   - Current hours: {{candidate.hours_4week}}
   - Compatibility score: {{candidate.score}} / 10
   - Availability: {{candidate.availability}}
   - Would you like to request swap with this person?
[ENDFOR]
[ENDIF]

#### Option 2: Modify Request

Consider these modifications:
- **Different date:** Try swapping {{alternative_date_1}} or {{alternative_date_2}}
- **Different partner:** {{alternative_partner_suggestion}}
- **Split shift:** Instead of full day, swap AM or PM block only

#### Option 3: Request Exception

If this is truly urgent:
- **Escalate to:** {{escalation_contact|"Chief Resident or Program Director"}}
- **Exception process:** {{exception_process}}
- **Justification needed:** {{justification_requirements}}

#### Option 4: Use Leave/Time Off

- Check if you have accrued leave time
- Submit leave request instead of swap request
- Contact: {{leave_coordinator}}

[ENDIF]

---

## Audit Trail

**Record:**
```
Swap Request ID: {{swap_id}}
Requester: {{requester}}
Partner: {{swap_partner|"TBD"}}
Target Date: {{target_date}}
Type: {{swap_type}}
Reason: {{reason}}
Submitted: [Timestamp]
Processed: [Timestamp]
Decision: [Approved/Denied]
Processed By: [System/Human]
Safety Checks: [Pass/Fail - see details above]
```

**Notifications Sent:**
- [ ] {{requester}} ({{notification_method}})
[IF swap_partner]
- [ ] {{swap_partner}} ({{notification_method}})
[ENDIF]
- [ ] Chief Resident
- [ ] Rotation coordinator for {{rotation}}
[IF urgency == "emergency" OR urgency == "urgent"]
- [ ] Program Director (urgent flag)
[ENDIF]

**Documentation:**
- [ ] Schedule updated in database
- [ ] Swap logged in audit trail
- [ ] Coverage confirmation sent to rotation
- [ ] Compliance metrics recalculated

---

```

---

## Examples

### Example 1: Simple One-to-One Swap (Approved)

**Instantiation:**
```
requester: "PGY2-01"
target_date: "2024-01-15"
swap_type: "one_to_one"
swap_partner: "PGY2-02"
reason: "family event"
urgency: "standard"
rotation: "inpatient"
safety_level: "standard"
include_rationale: true
notification_method: "email"
```

**Output:**

```markdown
# Swap Request Processing

---

## Request Details

**Requester:** PGY2-01
**Target Date(s):** 2024-01-15
**Swap Type:** one_to_one
**Swap Partner:** PGY2-02
**Reason:** family event
**Urgency:** STANDARD
**Submitted:** 2024-01-05 14:30

---

## Swap Type Definition

### One-to-One Swap

**Definition:** Two residents exchange shifts on different dates.

**Participants:**
- **Giver:** PGY2-01 (gives up 2024-01-15)
- **Receiver:** PGY2-02 (receives 2024-01-15)
- **Exchange:** PGY2-02 gives up 2024-01-22 to PGY2-01

**Example:**
- PGY2-01 swaps their Jan 15 inpatient shift with PGY2-02's Jan 22 inpatient shift
- Result: PGY2-01 works Jan 22, PGY2-02 works Jan 15

---

## Current Schedule Context

### Requester Current State

**PGY2-01 Schedule:**
- **Current rotation:** Inpatient
- **Hours this week:** 68 / 80
- **Hours this 4-week period:** 74 / 80 avg
- **Rest days (last 7 days):** 2
- **Assignments this month:** 12

**Shift Details (2024-01-15):**
- **Rotation:** Inpatient
- **Type:** Day shift
- **Duration:** 12 hours
- **Coverage required:** Yes (minimum 3 residents)

### Swap Partner Current State

**PGY2-02 Schedule:**
- **Current rotation:** Clinic
- **Hours this week:** 45 / 80
- **Hours this 4-week period:** 63 / 80 avg
- **Rest days (last 7 days):** 2
- **Assignments this month:** 10

**Exchange Shift Details:**
- **Date:** 2024-01-22
- **Rotation:** Inpatient
- **Type:** Day shift
- **Duration:** 12 hours

---

## Safety Checks

### Standard Validation

#### ACGME Compliance Checks

1. **80-Hour Rule (Requester)**
   - Current 4-week avg: 74 hours
   - After swap: 74 hours (no change - same rotation type)
   - Status: ✅ Pass

2. **80-Hour Rule (Swap Partner)**
   - Current 4-week avg: 63 hours
   - After swap: 63 hours (no change - same rotation type)
   - Status: ✅ Pass

3. **1-in-7 Rest (Requester)**
   - Rest days last 7 days: 2
   - After swap: 2 (swap doesn't affect rest days)
   - Status: ✅ Pass

4. **1-in-7 Rest (Swap Partner)**
   - Rest days last 7 days: 2
   - After swap: 2
   - Status: ✅ Pass

5. **Continuous Duty Limits**
   - Shift duration: 12 hours
   - Allowed for PGY-2: 28 hours
   - Status: ✅ Pass

6. **Rest Between Shifts**
   - Both residents have >14 hours between shifts
   - Status: ✅ Pass

#### Operational Checks

7. **Credential Requirements**
   - **Requester qualified for exchange shift?** ✅ Yes (PGY-2 qualified for inpatient)
   - **Partner qualified for requested shift?** ✅ Yes (PGY-2 qualified for inpatient)

8. **Coverage Adequacy**
   - **Minimum coverage met after swap?** ✅ Yes
   - Required: 3 residents on inpatient
   - After swap: 3 residents (same people, different dates)

9. **Supervision Ratios**
   - **PGY-1 supervision maintained?** ✅ Yes
   - No change to supervision structure

#### Policy Checks

10. **Swap Limit**
    - **Swaps this month (requester):** 1 / 3
    - Status: ✅ Within limit

11. **Swap Limit (Partner)**
    - **Swaps this month (partner):** 0 / 3
    - Status: ✅ Within limit

12. **Notice Period**
    - **Days before shift:** 10 days
    - **Required notice:** 7 days
    - Status: ✅ Adequate

13. **Blackout Dates**
    - **Is 2024-01-15 a blackout date?** ✅ No

---

## Safety Check Summary

✅ **ALL SAFETY CHECKS PASSED**

Swap is safe to proceed.

---

## Impact Assessment

### Workload Impact

**PGY2-01:**
- **Before swap:**
  - Shifts this month: 12
  - Total hours: 148
  - Weekend shifts: 2
- **After swap:**
  - Shifts this month: 12 (Δ: 0)
  - Total hours: 148 (Δ: 0)
  - Weekend shifts: 2 (Δ: 0)

**PGY2-02:**
- **Before swap:**
  - Shifts this month: 10
  - Total hours: 126
  - Weekend shifts: 1
- **After swap:**
  - Shifts this month: 10 (Δ: 0)
  - Total hours: 126 (Δ: 0)
  - Weekend shifts: 1 (Δ: 0)

### Coverage Impact

**Inpatient Rotation:**
- **Coverage before swap:** 3 residents
- **Coverage after swap:** 3 residents
- **Minimum required:** 3
- **Impact:** No change

### Equity Impact

**Workload Distribution:**
- Swap creates roughly equal exchange (fair trade)
- Equity score change: 0.02 (near zero is ideal)

---

## Decision

### ✅ APPROVED

**Swap request is APPROVED.**

**Rationale:**
PGY2-01 and PGY2-02 are swapping equivalent shifts (both inpatient day shifts, same duration). All ACGME compliance checks pass, coverage is maintained, and both residents are within their swap limits. This is a straightforward exchange with no negative impacts.

**Key factors in approval:**
1. Both residents qualified for swapped shifts
2. ACGME compliance maintained (duty hours, rest days)
3. Coverage adequacy preserved (3 residents on both dates)
4. Adequate notice provided (10 days)
5. Equal value exchange (equity neutral)

**Conditions:**
None - unconditional approval

**Next Steps:**
1. Update schedule system with swap
2. Notify PGY2-01 and PGY2-02 of approval
3. Confirm assignments with inpatient rotation coordinator
4. Document swap in audit trail

**Rollback Window:**
- Swap can be reversed within 24 hours
- Contact: Chief Resident

---

## Audit Trail

**Record:**
```
Swap Request ID: SWP-2024-0105-001
Requester: PGY2-01
Partner: PGY2-02
Target Date: 2024-01-15 (exchange: 2024-01-22)
Type: one_to_one
Reason: family event
Submitted: 2024-01-05 14:30
Processed: 2024-01-05 14:45
Decision: Approved
Processed By: System (automated approval)
Safety Checks: All Passed
```

**Notifications Sent:**
- [✅] PGY2-01 (email)
- [✅] PGY2-02 (email)
- [✅] Chief Resident
- [✅] Inpatient rotation coordinator

**Documentation:**
- [✅] Schedule updated in database
- [✅] Swap logged in audit trail
- [✅] Coverage confirmation sent to rotation
- [✅] Compliance metrics recalculated
```

---

### Example 2: Emergency Swap with Auto-Match (Initially Denied, Then Alternative)

**Instantiation:**
```
requester: "PGY1-03"
target_date: "2024-01-08"
swap_type: "find_coverage"
reason: "family emergency"
urgency: "emergency"
rotation: "night_float"
auto_match: true
safety_level: "standard"
include_rationale: true
notification_method: "both"
```

**Output:**

```markdown
🚨 **EMERGENCY SWAP REQUEST**
Priority: IMMEDIATE - Process within 1 hour

# Swap Request Processing

---

## Request Details

**Requester:** PGY1-03
**Target Date(s):** 2024-01-08
**Swap Type:** find_coverage
**Reason:** family emergency
**Urgency:** EMERGENCY
**Submitted:** 2024-01-07 18:45

---

## Swap Type Definition

### Find Coverage

**Definition:** Requester needs coverage but hasn't identified a replacement yet.

**Participants:**
- **Requester:** PGY1-03 (needs coverage for 2024-01-08)
- **Potential Covers:** [To be determined]

**Process:**
1. System will search for compatible residents
2. Notify best matches
3. First to accept gets the shift

---

[... current schedule context, safety checks ...]

## Safety Check Summary

❌ **SAFETY CHECK FAILURES**

Swap cannot proceed as originally requested. Failures:
- **80-Hour Rule (First Match - PGY1-04)**: Would push PGY1-04 to 84 hours in current 4-week period
  - **Why this matters:** ACGME violation, accreditation risk
  - **Possible solutions:** Find different coverage or reduce hours elsewhere

- **Continuous Duty Limit (PGY1-03)**: Has already worked 14 hours today, night shift would exceed 16-hour limit for PGY-1
  - **Why this matters:** PGY-1 cannot work >16 continuous hours
  - **Possible solutions:** Must end current shift before starting night shift (requires 8-hour break)

---

## Decision

### ❌ DENIED

**Swap request is DENIED as originally submitted.**

**Rationale:**
PGY1-03 cannot work the scheduled night shift (19:00-07:00) because they are currently on a day shift that started at 07:00. Working both shifts would exceed the 16-hour continuous duty limit for PGY-1 residents. Additionally, the first auto-match candidate (PGY1-04) would exceed 80-hour limit if assigned this shift.

**Primary reasons for denial:**
1. Continuous duty limit violation for PGY1-03
2. No compatible residents found within duty hour limits

**Alternative Options:**

#### Option 1: Auto-Match Alternative Partners

System has identified these compatible residents who CAN cover the shift:

1. **PGY2-05** (PGY-2)
   - Current hours: 68 hours (4-week avg)
   - Compatibility score: 9 / 10
   - Availability: Available (not scheduled)
   - Qualified: Yes (PGY-2 can cover night float)
   - ✅ **RECOMMENDED:** Best match with no compliance issues

2. **Float Pool (Moonlighter-02)**
   - Current hours: 42 hours (part-time)
   - Compatibility score: 7 / 10
   - Availability: On-call for emergencies
   - Cost: $$$ (moonlighter rate)

#### Option 2: Modify Request

- **Emergency coverage protocol:** Given family emergency status, recommend invoking emergency float pool (Moonlighter-02) for tonight
- **PGY1-03 schedule:** Must end current shift immediately (18:00 latest) to get 8-hour rest before any future shifts

#### Option 3: Request Exception

**RECOMMEND THIS PATH:**
Given emergency status:
1. **Immediate:** Assign Moonlighter-02 to cover tonight's shift (2024-01-08 19:00-07:00)
2. **Tomorrow:** Assign PGY2-05 to cover 2024-01-09 night shift if needed
3. **PGY1-03:** Grant emergency leave for 2024-01-08 to 2024-01-10
4. **Escalate to:** Program Director (emergency leave approval needed)

**Next Steps (Recommended):**
1. Chief Resident calls Moonlighter-02 immediately
2. Notify PGY2-05 as backup for tomorrow
3. Submit emergency leave request for PGY1-03
4. PGY1-03 should end current shift ASAP (not exceed 16 hours)

---

## Audit Trail

**Record:**
```
Swap Request ID: SWP-2024-0107-999 (EMERGENCY)
Requester: PGY1-03
Partner: TBD
Target Date: 2024-01-08
Type: find_coverage
Reason: family emergency
Urgency: EMERGENCY
Submitted: 2024-01-07 18:45
Processed: 2024-01-07 18:50
Decision: Denied as submitted, alternative recommended
Processed By: System + Chief Resident notified
Safety Checks: Failed (duty hour limits)
Recommended Action: Use moonlighter + emergency leave
```

**Notifications Sent:**
- [✅] PGY1-03 (SMS + email) - "Swap denied, but emergency coverage arranged. Call Chief Resident."
- [✅] Chief Resident (SMS - URGENT) - "Emergency swap needed, recommend moonlighter"
- [✅] Program Director (SMS) - "Emergency leave request pending approval"
- [✅] Moonlighter-02 (SMS) - "Emergency coverage request for tonight 19:00-07:00"
- [ ] PGY2-05 (SMS) - "Standby for tomorrow night coverage"

---

**URGENT ACTION REQUIRED:**
Chief Resident must confirm coverage within 30 minutes (before 19:00 shift start).
```

---

## Validation Checklist

Before finalizing swap decision:

- [ ] **All safety checks completed** (ACGME, operational, policy)
- [ ] **Impact assessed** (workload, coverage, equity)
- [ ] **Decision justified** (rationale documented)
- [ ] **Alternatives considered** (if denied)
- [ ] **Notifications prepared** (all affected parties identified)
- [ ] **Audit trail complete** (all fields filled)

[IF approved]
- [ ] **Schedule updated** (changes reflected in system)
- [ ] **Rollback window communicated** (parties know they can reverse)
[ENDIF]

[IF urgency == "emergency"]
- [ ] **Escalation completed** (PD or chief resident notified)
- [ ] **Timeline met** (processed within 1 hour)
[ENDIF]

---

## Notes

### Auto-Match Algorithm

When `auto_match: true`, system searches for compatible residents using:
1. **Qualification match:** Must be credentialed for the rotation
2. **Duty hour compliance:** Adding shift must not violate 80-hour rule
3. **Rest compliance:** Must maintain 1-in-7 rest
4. **Availability:** Not already scheduled during that time
5. **Swap limit:** Not exceeded monthly swap limit
6. **Compatibility score:** Weighted combination of factors

Candidates ranked by score, top matches notified first.

### Rollback Policy

- **Standard swaps:** 24-hour rollback window
- **Emergency swaps:** 4-hour rollback window (shorter due to urgency)
- **After rollback window:** Requires chief resident or PD approval

### Integration with Other Templates

Typical workflow:
1. **SWAP_REQUEST** → Process individual swap (this template)
2. **CONSTRAINT_ANALYSIS** → If complex multi-swap scenario
3. **INCIDENT_REVIEW** → If swap led to coverage gap or compliance issue
4. **SCHEDULE_GENERATION** → If many swaps require schedule rebuild

### Common Denial Reasons

- Duty hour limit exceeded
- Insufficient notice (<7 days for routine)
- Credential mismatch (requester/partner not qualified)
- Coverage would drop below minimum
- Swap limit exceeded
- Blackout date (e.g., major holiday, high-demand period)

### Version History

- **v1.0.0** (2025-12-26): Initial template creation
  - Based on swap management system requirements
  - Includes auto-match algorithm for coverage finding
  - Supports emergency swap processing
  - Integrated with ACGME compliance validation
