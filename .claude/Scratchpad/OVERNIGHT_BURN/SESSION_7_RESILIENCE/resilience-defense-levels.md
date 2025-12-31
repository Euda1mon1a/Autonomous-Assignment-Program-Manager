# RESILIENCE DEFENSE LEVELS: Comprehensive Reference

**Status:** Operational Reference Document
**Last Updated:** 2025-12-30
**Session:** G2_RECON SEARCH_PARTY - SESSION_7_RESILIENCE

---

## Executive Summary

The Residency Scheduler implements a **5-level Defense-in-Depth system** derived from nuclear reactor safety paradigms, adapted for medical residency workforce resilience. This system provides graduated response postures from prevention through emergency crisis management.

**Defense-in-Depth Philosophy:** Each level operates independently, assuming all previous levels have failed. The system escalates protection as burnout risk increases.

---

## Table of Contents

1. [Defense Level Definitions](#1-defense-level-definitions)
2. [Level Characteristics Matrix](#2-level-characteristics-matrix)
3. [Transition Rules & Thresholds](#3-transition-rules--thresholds)
4. [Escalation Procedures](#4-escalation-procedures)
5. [De-escalation Procedures](#5-de-escalation-procedures)
6. [Response Playbooks by Level](#6-response-playbooks-by-level)
7. [Hysteresis Logic](#7-hysteresis-logic)
8. [Manual Override Procedures](#8-manual-override-procedures)
9. [Trigger Conditions](#9-trigger-conditions)
10. [Audit & Monitoring](#10-audit--monitoring)

---

## 1. Defense Level Definitions

### Level 1: PREVENTION (GREEN)

**Color Code:** GREEN
**Numeric Value:** 1
**Burnout Fire Index (FWI) Range:** 0-20 (LOW danger)
**System State:** Fully operational, proactive measures active

**Definition:**
Level 1 represents optimal operational conditions where the system is healthy, has adequate staffing margins, and sufficient redundancy. Focus is on maintaining buffers and preventing degradation.

**Key Characteristics:**
- All capacity buffers in place (20% minimum reserve)
- No stress signals detected
- Faculty satisfaction and morale stable
- Work hours within safe ranges
- Full redundancy for critical functions (N+2 or better)
- Cross-training programs active
- Absence forecasting active

**Clinical Context:**
Normal residency operations with adequate scheduling flexibility, faculty availability, and no burnout indicators.

**Implementation:**
`DefenseLevel.PREVENTION` (enum value 1)

---

### Level 2: CONTROL (YELLOW)

**Color Code:** YELLOW
**Numeric Value:** 2
**Burnout Fire Index (FWI) Range:** 20-40 (MODERATE danger)
**System State:** Operational with elevated monitoring

**Definition:**
Level 2 is activated when early warning signals appear. One or more temporal indicators are elevated but not yet critical. The system transitions from prevention to active monitoring and early intervention.

**Key Characteristics:**
- Capacity buffer reduced but adequate (15-20%)
- One or more burnout indicators elevated:
  - Work hours trending upward
  - Monthly/recent workload increased
  - Faculty satisfaction slightly declining
- Early warning alerts activated
- Trend analysis in progress
- Coverage monitoring intensified
- Contingency planning begins

**Clinical Context:**
Busy season (e.g., July (July new residents, holiday season) with slightly elevated call frequency, some faculty absences, but no critical gaps yet.

**Implementation:**
`DefenseLevel.CONTROL` (enum value 2)

---

### Level 3: SAFETY_SYSTEMS (ORANGE)

**Color Code:** ORANGE
**Numeric Value:** 3
**Burnout Fire Index (FWI) Range:** 40-60 (HIGH danger)
**System State:** Automated protective measures engage

**Definition:**
Level 3 represents a shift from monitoring to active intervention. Multiple burnout indicators are elevated or conditions are deteriorating rapidly. Automated protective systems are activated.

**Key Characteristics:**
- Capacity buffer depleted to minimum (10-15%)
- Multiple temporal indicators elevated:
  - Significant work hour accumulation
  - Monthly burnout scores elevated
  - Velocity indicator shows rapid deterioration
- Automated reassignment algorithms activated
- Pre-approved backup pools called
- Overtime authorization begins
- Load balancing algorithms engaged
- Zone isolation considerations begin

**Clinical Context:**
Crisis period (major surge in admissions, multiple faculty sick calls, unexpected departures) but core services still staffed.

**Implementation:**
`DefenseLevel.SAFETY_SYSTEMS` (enum value 3)

---

### Level 4: CONTAINMENT (RED)

**Color Code:** RED
**Numeric Value:** 4
**Burnout Fire Index (FWI) Range:** 60-80 (VERY_HIGH danger)
**System State:** Damage limitation mode

**Definition:**
Level 4 is a severe response posture. The system is experiencing critical stress across multiple dimensions. Manual intervention required to limit damage and protect core services.

**Key Characteristics:**
- Capacity buffer below minimum (< 10%)
- Severe conditions detected:
  - Critical work hour overages
  - Sustained high burden across months
  - Low satisfaction scores
- Service reduction protocols activated
- Non-essential services suspended
- Faculty reassignment enforced
- Zone isolation implemented
- Minimum service guarantee protection
- Clinical leadership deep involvement
- Possible external resource requests

**Clinical Context:**
Major emergency (pandemic surge, mass departure of faculty, natural disaster impact) requiring service curtailment and external help.

**Implementation:**
`DefenseLevel.CONTAINMENT` (enum value 4)

---

### Level 5: EMERGENCY (BLACK)

**Color Code:** BLACK
**Numeric Value:** 5
**Burnout Fire Index (FWI) Range:** 80+ (EXTREME danger)
**System State:** Crisis response

**Definition:**
Level 5 represents catastrophic system failure or imminent failure. All protective measures are in effect. External escalation and crisis management protocols are invoked.

**Key Characteristics:**
- Capacity critically depleted (< 5%)
- Extreme conditions:
  - Critically severe work hours
  - Multi-temporal severe burden
  - Severe satisfaction collapse
  - Multiple simultaneous failures
- Crisis communication activated
- External escalation to hospital leadership
- Possible regulatory notification
- All contingencies exhausted
- Post-incident review planned
- Media/stakeholder communication
- Recovery planning initiated

**Clinical Context:**
Catastrophic failure (mass simultaneous faculty absences, system-wide failure, workforce collapse) with potential patient safety implications.

**Implementation:**
`DefenseLevel.EMERGENCY` (enum value 5)

---

## 2. Level Characteristics Matrix

| Characteristic | GREEN (1) | YELLOW (2) | ORANGE (3) | RED (4) | BLACK (5) |
|---|---|---|---|---|---|
| **FWI Range** | 0-20 | 20-40 | 40-60 | 60-80 | 80+ |
| **Danger Class** | LOW | MODERATE | HIGH | VERY_HIGH | EXTREME |
| **Utilization** | < 60% | 60-75% | 75-85% | 85-95% | > 95% |
| **Capacity Buffer** | 20%+ | 15-20% | 10-15% | < 10% | < 5% |
| **Redundancy** | N+2/N+3 | N+1/N+2 | N+0/N+1 | Below N | Critical |
| **Mode** | Prevention | Monitoring | Intervention | Containment | Crisis |
| **Automated Actions** | Forecasting | Monitoring | Reassignment | Reduction | External |
| **Manual Intervention** | Minimal | Occasional | Regular | Constant | Continuous |
| **Faculty Mood** | Stable | Alert | Stressed | High Stress | Extreme Stress |
| **Response Time** | Hours/Days | Hours | Minutes | Real-time | Immediate |

---

## 3. Transition Rules & Thresholds

### Escalation Thresholds (GREEN → BLACK)

| Transition | FWI Score | Utilization | Coverage | ISI Trigger | BUI Trigger |
|---|---|---|---|---|---|
| GREEN → YELLOW | ≥ 20 | ≥ 60% | < 95% | — | — |
| YELLOW → ORANGE | ≥ 40 | ≥ 75% | < 90% | > 60 | — |
| ORANGE → RED | ≥ 60 | ≥ 85% | < 85% | — | > 70 |
| RED → BLACK | ≥ 80 | ≥ 95% | < 70% | Multiple | Multiple |

### De-escalation Thresholds (BLACK → GREEN)

| Transition | FWI Score | Utilization | Coverage | Duration Required |
|---|---|---|---|---|
| BLACK → RED | < 75 | < 93% | > 72% | 3 consecutive checks |
| RED → ORANGE | < 56 | < 83% | > 80% | 3 consecutive checks |
| ORANGE → YELLOW | < 37 | < 73% | > 88% | 3 consecutive checks |
| YELLOW → GREEN | < 18 | < 58% | > 93% | 3 consecutive checks |

**Buffer Rule:** De-escalation threshold = escalation threshold × (1 - 0.10) where 0.10 is the 10% hysteresis buffer.

---

## 4. Escalation Procedures

### Automatic Escalation Flow

```
Monitor FWI Score & Components
        ↓
Compare to Current Level Threshold
        ↓
IF FWI_SCORE >= THRESHOLD:
        ↓
Check ISI (Rapid Deterioration)  ← If ISI > 60, escalate +1 level
        ↓
Check BUI (Sustained Burden)      ← If BUI > 70, escalate +1 level
        ↓
Recommended Level = Base + Adjustments
        ↓
Apply Hysteresis Logic
(Requires 2 consecutive checks above threshold)
        ↓
IF Threshold Met:
  - Log transition with audit trail
  - Activate level-specific actions
  - Send escalation alert
  - Update dashboards
ELSE:
  - Maintain current level
  - Track consecutive count
```

### Escalation Consecutive Check Requirements

**Escalation requires 2 consecutive FWI checks above the threshold:**

```
Time    FWI Score   Recommended   Consecutive   Current Level   Action
────────────────────────────────────────────────────────────────────
0:00    38          CONTROL       0             PREVENTION      (baseline)
0:15    42          ORANGE        1             PREVENTION      (count=1)
0:30    41          ORANGE        2             ORANGE          ✓ ESCALATE
0:45    38          CONTROL       0             ORANGE          (reset)
1:00    40          ORANGE        1             ORANGE          (count=1)
1:15    42          ORANGE        2             ORANGE          ✓ ESCALATE
```

**Rationale:** Prevents false positives from transient FWI spikes. System must see sustained elevation.

### Escalation Alert Template

When escalating from level N to N+1:

```
EVENT: Defense Level Escalation
FROM_LEVEL: {current_level_name}
TO_LEVEL: {new_level_name}
FWI_SCORE: {fwi_score}
DANGER_CLASS: {danger_class}
TRIGGER_TYPE: {fwi_mapping | isi_escalation | bui_escalation}
ISI_VALUE: {isi_score}
BUI_VALUE: {bui_score}
CONSECUTIVE_CHECKS: {count}
TIMESTAMP: {iso8601}
AUDIT_ID: {uuid}

ALERT_MESSAGE:
"Defense level escalated {FROM} → {TO} (FWI={score:.1f}, {danger}).
Trigger: {trigger_description}.
Recommended actions for {TO_LEVEL} activated immediately."
```

---

## 5. De-escalation Procedures

### Automatic De-escalation Flow

```
Monitor FWI Score
        ↓
Compare to De-escalation Threshold
(threshold - 10% buffer)
        ↓
IF FWI_SCORE < DE_ESCALATION_THRESHOLD:
        ↓
Recommended Level = Lower level
        ↓
Apply Hysteresis Logic
(Requires 3 consecutive checks BELOW threshold)
        ↓
IF Threshold Met:
  - Log transition with audit trail
  - Deactivate old level actions
  - Activate new level actions (may be more relaxed)
  - Send de-escalation alert
  - Update dashboards
ELSE:
  - Maintain current level
  - Track consecutive count
```

### De-escalation Consecutive Check Requirements

**De-escalation requires 3 consecutive FWI checks BELOW (threshold - buffer):**

```
Time    FWI Score   De-esc Thresh   Consecutive   Current Level   Action
──────────────────────────────────────────────────────────────────────
0:00    80          75              0             BLACK           (baseline)
0:15    74          75              1             BLACK           (count=1)
0:30    73          75              2             BLACK           (count=2)
0:45    72          75              3             RED             ✓ DE-ESCALATE
1:00    80          56              0             RED             (reset)
1:15    55          56              1             RED             (count=1)
1:30    54          56              2             RED             (count=2)
1:45    50          56              3             ORANGE          ✓ DE-ESCALATE
```

**Rationale:** Requires sustained improvement before relaxing protections. Prevents premature de-escalation and allows time for system stabilization.

### De-escalation Alert Template

When de-escalating from level N to N-1:

```
EVENT: Defense Level De-escalation
FROM_LEVEL: {current_level_name}
TO_LEVEL: {new_level_name}
FWI_SCORE: {fwi_score}
DANGER_CLASS: {danger_class}
SUSTAINABILITY: {3_consecutive_checks_below_threshold}
TIMESTAMP: {iso8601}
AUDIT_ID: {uuid}

ALERT_MESSAGE:
"Defense level de-escalated {FROM} → {TO} (FWI={score:.1f}).
System sustained improved conditions for 45+ minutes.
Relaxing protective measures for {TO_LEVEL} level."
```

---

## 6. Response Playbooks by Level

### Level 1: PREVENTION (GREEN) - Playbook

**Objective:** Maintain proactive buffers and prevent degradation

**Actions:**
- Maintain 20% capacity buffer minimum
- Run cross-training programs (quarterly)
- Track absence forecasts 90 days ahead
- Monitor burnout indicators weekly
- Plan rotation adjustments for next quarter
- Maintain pre-approved backup pools
- Conduct monthly trend analysis

**Stakeholders:**
- Program Director (quarterly review)
- Faculty (receive satisfaction surveys)
- Residents (normal scheduling)

**Communication:**
- Monthly resilience dashboard review
- Quarterly faculty meetings
- Annual program evaluation

**Success Metrics:**
- FWI < 20 sustained
- Coverage rate > 95%
- Faculty satisfaction > 0.8
- No burnout signals

**Exit Condition:** Any indicator reaching 0.7 scale moves to YELLOW

---

### Level 2: CONTROL (YELLOW) - Playbook

**Objective:** Early detection and rapid intervention

**Actions:**
1. **Monitoring Intensification**
   - Increase FWI updates to weekly (from monthly)
   - Daily coverage monitoring
   - Trend analysis every 3 days
   - Watch ISI and BUI components

2. **Early Intervention**
   - Schedule meetings with at-risk faculty
   - Identify potential leave timing issues
   - Prepare contingency rotations
   - Begin backup notification process

3. **Preventive Measures**
   - Defer non-essential activities
   - Pre-approve overtime budget
   - Alert staffing office to potential needs
   - Review next month's schedule for flexibility

**Stakeholders:**
- Program Director (weekly briefing)
- Associate Program Director
- Faculty with elevated scores
- Residents (may see schedule adjustments)

**Communication:**
- Weekly dashboard updates
- Ad-hoc faculty alerts
- Monthly program director report

**Success Metrics:**
- FWI stabilizes < 40
- Coverage rate > 90%
- Faculty engagement maintained

**Exit Condition:** FWI crosses 40 or utilization > 75%

---

### Level 3: SAFETY_SYSTEMS (ORANGE) - Playbook

**Objective:** Automated protective actions engage

**Actions:**
1. **Automated Interventions** (System-driven)
   - Auto-reassignment algorithms activated
   - Pre-approved backup faculty called
   - Overtime authorization triggered
   - Load balancing on all zones

2. **Manual Oversight** (Human-driven)
   - Daily Director stand-ups
   - Real-time coverage gap identification
   - Ad-hoc staffing decisions
   - Faculty wellness checks

3. **Service Adjustments**
   - Reduce elective procedures by 10-20%
   - Extend consult turnaround times
   - Defer non-urgent education activities
   - Compress meeting schedules

4. **External Coordination**
   - Brief Hospital VP (Medicine/Surgery)
   - Alert neighboring departments to potential requests
   - Activate retired faculty on-call list
   - Prepare locum requisitions

**Stakeholders:**
- Program Director (daily)
- Clinical Department Chairs
- Hospital VP Medical Affairs
- HR/Staffing Office
- All Faculty (briefing required)
- Residents (expect schedule changes)

**Communication:**
- Daily briefings at 8:00 AM
- Daily dashboard updates
- Twice-weekly faculty calls
- Hospital leadership update

**Success Metrics:**
- Maintain > 85% coverage
- FWI trending downward
- Faculty reports stable morale

**Exit Condition:** FWI crosses 60 or coverage drops < 85%

---

### Level 4: CONTAINMENT (RED) - Playbook

**Objective:** Damage limitation and core service protection

**Actions:**
1. **Service Reduction Protocols**
   - Suspend elective procedures
   - Close non-essential clinics
   - Defer education/conferences
   - Restrict new admissions (if possible)
   - Reduce ancillary services

2. **Faculty Deployment**
   - Enforce reassignments
   - Activate zone isolation
   - Implement cross-zone borrowing strictly
   - Lock essential faculty assignments

3. **Leadership Escalation**
   - Hospital VP becomes primary contact
   - C-Suite briefing required
   - Patient safety committee notification
   - Quality/Compliance review

4. **External Resources**
   - Activate locum requisitions
   - Contact neighboring programs
   - Prepare for external clinical support
   - Notify accreditation bodies if needed

5. **Resident Protection**
   - Monitor resident work hours strictly
   - Enforce off-service days
   - Provide mental health support
   - May require schedule simplification

**Stakeholders:**
- Hospital Chief Medical Officer
- Department Chairs
- Program Director (primary)
- Clinical Operations
- HR/Staffing
- All Faculty (daily involvement)
- Residents (significant schedule changes)

**Communication:**
- Twice-daily leadership briefings
- Real-time dashboard updates
- Hourly coverage checks
- Daily faculty/resident all-hands
- Hospital administration daily update

**Success Metrics:**
- Maintain > 80% core coverage
- No critical safety gaps
- FWI trajectory controlled
- All staff briefed daily

**Exit Condition:** FWI sustained < 56 OR coverage returns > 85% for 3 consecutive days

---

### Level 5: EMERGENCY (BLACK) - Playbook

**Objective:** Crisis management and system preservation

**Actions:**
1. **Crisis Communication** (IMMEDIATE)
   - Hospital CEO notification
   - Board briefing initiated
   - Media communication prepared
   - Stakeholder alerts sent

2. **All Resources Activated**
   - Locum request emergency level
   - All retired faculty called
   - Neighboring programs contacted
   - External agency engaged
   - Possible patient transfer/diversion

3. **Regulatory Notification**
   - Accreditation body notification (may be required)
   - State medical board notification (if applicable)
   - Patient safety incident review
   - Compliance documentation

4. **Recovery Planning**
   - Incident command structure established
   - Recovery timeline defined
   - Root cause analysis initiated
   - Prevention measures designed

5. **Resident/Faculty Protection**
   - Resident schedules may be dramatically simplified
   - Mental health support mandatory
   - Leave authorizations expedited
   - Possible rotation reassignments

**Stakeholders:**
- Hospital CEO/President
- Board of Directors
- Program Director (intensive involvement)
- Clinical Department Chairs (all affected specialties)
- Patient Safety Officer
- Compliance Officer
- Legal Counsel
- All Residents (may require redeployment)

**Communication:**
- Real-time command center updates
- Hourly leadership briefings
- Daily public health statements
- Ongoing stakeholder updates
- Continuous resident/faculty briefings

**Success Metrics:**
- Patient safety maintained
- No license/accreditation jeopardy
- All staff accounted for
- Recovery timeline established

**Exit Condition:** System stabilization and transition to RED/ORANGE level planning

---

## 7. Hysteresis Logic

### Purpose

Hysteresis prevents **oscillation** at threshold boundaries. Without it:
- System might oscillate GREEN ↔ YELLOW multiple times per day
- Alert fatigue would disable response
- Protective measures wouldn't have time to take effect

### Implementation

**State Machine:**
```
State: {
  current_level: DefenseLevel,
  candidate_level: Optional[DefenseLevel],
  consecutive_count: int,
  last_update: datetime
}

On each FWI update:
  recommended = map_fwi_to_level(fwi_score)

  IF recommended > current_level:
    # Escalation path
    IF recommended == candidate_level:
      consecutive_count += 1
      IF consecutive_count >= 2:
        current_level = recommended
        candidate_level = None
        consecutive_count = 0
        ACTIVATE(recommended)
    ELSE:
      candidate_level = recommended
      consecutive_count = 1

  ELIF recommended < current_level:
    # De-escalation path
    de_escalate_threshold = threshold - (threshold * 0.10)
    IF fwi_score < de_escalate_threshold:
      IF recommended == candidate_level:
        consecutive_count += 1
        IF consecutive_count >= 3:
          current_level = recommended
          candidate_level = None
          consecutive_count = 0
          ACTIVATE(recommended)
      ELSE:
        candidate_level = recommended
        consecutive_count = 1
    ELSE:
      # Within hysteresis band
      candidate_level = None
      consecutive_count = 0

  ELSE:
    # Same level, reset
    candidate_level = None
    consecutive_count = 0
```

### Example: Threshold Oscillation Prevention

**Without Hysteresis (PROBLEM):**
```
Time  FWI  Recommended  Current  Action
────────────────────────────────────────
0:00  39   CONTROL      CONTROL  (steady)
0:15  41   ORANGE       ORANGE   ✗ ESCALATE (false positive)
0:30  39   CONTROL      CONTROL  ✗ DE-ESCALATE (premature)
0:45  41   ORANGE       ORANGE   ✗ ESCALATE (again)
1:00  39   CONTROL      CONTROL  ✗ DE-ESCALATE (oscillating)
```

**With Hysteresis (SOLUTION):**
```
Time  FWI  Recommended  Candidate  Count  Current  Action
──────────────────────────────────────────────────────────
0:00  39   CONTROL      —          0      CONTROL  (steady)
0:15  41   ORANGE       ORANGE     1      CONTROL  (candidate set)
0:30  42   ORANGE       ORANGE     2      ORANGE   ✓ ESCALATE
0:45  39   CONTROL      CONTROL    1      ORANGE   (within buffer)
1:00  40   ORANGE       —          0      ORANGE   (back to steady)
1:15  36   CONTROL      CONTROL    1      ORANGE   (below buffer)
1:30  35   CONTROL      CONTROL    2      ORANGE   (2nd consecutive)
1:45  34   CONTROL      CONTROL    3      CONTROL  ✓ DE-ESCALATE
```

**Result:** System required sustained conditions (3 consecutive checks below 37) to de-escalate.

---

## 8. Manual Override Procedures

### Override Types

| Type | Purpose | Approval | Duration | Use Case |
|------|---------|----------|----------|----------|
| **Emergency Escalate** | Jump directly to BLACK | Admin | Until cancelled | Sudden critical event |
| **Level Lock** | Fix at specific level | Admin | Max 24 hours | Testing or false positive |
| **Hysteresis Bypass** | Skip consecutive checks | Admin | Single use | Urgent need to escalate |
| **System Test** | Trigger without actual activation | System | During test | Drills/validation |

### Emergency Escalation Procedure

**When to use:** Sudden catastrophic event (mass faculty sick calls, critical infrastructure failure)

**Procedure:**
1. Administrator initiates override request
2. Logs reason (audit trail required)
3. Targets DefenseLevel.EMERGENCY
4. System:
   - Skips hysteresis logic
   - Immediately activates BLACK level
   - Sends critical alerts
   - Logs override event with timestamp
5. Override tracked until manual cancellation or expiration

**Example:**
```python
override = DefenseOverride(
    override_type="emergency_escalate",
    target_level=DefenseLevel.EMERGENCY,
    applied_by="admin-user-5678",
    reason="Multiple faculty ICU call-out due to COVID",
    expires_at=datetime.now() + timedelta(hours=24)
)

bridge.apply_override(override)
# → Immediately activates BLACK level
# → Logs: "Override applied: emergency_escalate to EMERGENCY by admin-5678"
```

### Level Lock Procedure

**When to use:** Testing, false positive from data quality issue, maintenance window

**Procedure:**
1. Administrator initiates lock
2. Specifies target level (e.g., YELLOW)
3. Set expiration time (max 24 hours)
4. System:
   - Ignores FWI recommendations
   - Maintains locked level for duration
   - Logs lock event
   - Sends informational alert
5. On expiration:
   - Auto-restores to automatic control
   - Processes current FWI (doesn't apply hysteresis)

**Example:**
```python
override = DefenseOverride(
    override_type="level_lock",
    target_level=DefenseLevel.CONTROL,
    applied_by="admin-user-5678",
    reason="Data quality validation - suspecting false spike",
    expires_at=datetime.now() + timedelta(hours=1)
)

bridge.apply_override(override)
# → Locks level at CONTROL
# → Logs: "Level lock applied: CONTROL until 2025-12-30T15:30:00Z"
```

### Hysteresis Bypass Procedure

**When to use:** Urgent need to escalate without waiting for consecutive checks

**Procedure:**
1. Administrator initiates bypass
2. Specifies target level (higher than current)
3. System:
   - Processes current FWI recommendation
   - Applies it immediately without hysteresis
   - Clears override (single-use)
   - Logs bypass event

**Example:**
```python
override = DefenseOverride(
    override_type="hysteresis_bypass",
    target_level=DefenseLevel.SAFETY_SYSTEMS,  # Not used in bypass
    applied_by="admin-user-5678",
    reason="Urgent coverage gap - unexpected faculty departure"
)

bridge.apply_override(override)
# → Processes current FWI
# → Immediately applies recommended level (no 2-check wait)
# → Clears override after use
```

### System Test Procedure

**When to use:** Drills, testing response procedures, validation testing

**Procedure:**
1. System initiates test override
2. Specifies test level to trigger
3. System:
   - Logs test event
   - Returns test level in responses
   - Does NOT actually activate level
   - Does NOT send operational alerts
4. Test code validates responses as if level was active
5. On completion:
   - Clears test override
   - Restores normal operation

---

## 9. Trigger Conditions

### Automatic Escalation Triggers

#### PRIMARY: FWI Score Mapping
```
FWI Score   →   Recommended Level
0-20        →   PREVENTION (1)
20-40       →   CONTROL (2)
40-60       →   SAFETY_SYSTEMS (3)
60-80       →   CONTAINMENT (4)
80+         →   EMERGENCY (5)
```

#### SECONDARY: ISI Component (Rapid Deterioration)

**Trigger:** `ISI > 60 AND FWI >= 20`

**Effect:** Escalate base level +1 (capped at EMERGENCY)

**Rationale:** High ISI indicates rapid deterioration in recent hours/days. Even if overall FWI is moderate, fast-spreading burnout warrants faster response.

**Example:**
```
Resident A:
  FWI = 35 (MODERATE → CONTROL)
  ISI = 70 (high velocity)

Base mapping: CONTROL
ISI adjustment: +1 level
Final: SAFETY_SYSTEMS

Reasoning: Overall danger moderate, but spreading rapidly.
Escalate to automated protective actions now.
```

#### SECONDARY: BUI Component (Sustained Burden)

**Trigger:** `BUI > 70 AND FWI >= 40`

**Effect:** Escalate base level +1 (capped at EMERGENCY)

**Rationale:** High BUI indicates deep, accumulated burden across multiple timescales. Chronic conditions require more aggressive intervention than acute stress.

**Example:**
```
Resident B:
  FWI = 55 (HIGH → SAFETY_SYSTEMS)
  BUI = 75 (severe accumulation)

Base mapping: SAFETY_SYSTEMS
BUI adjustment: +1 level
Final: CONTAINMENT

Reasoning: Deep multi-temporal burden requires not just automation
but actual service reduction and damage limitation.
```

### Escalation Alert Messages

**By Trigger Type:**

**FWI-Based:**
```
"Overall burnout danger escalated to ORANGE (FWI=52).
Multiple temporal indicators elevated. Automated protective
measures activated."
```

**ISI-Based:**
```
"RAPID DETERIORATION DETECTED (ISI=68). Escalating to ORANGE
for automated protective actions. Workload velocity is at
dangerous rate - immediate action required."
```

**BUI-Based:**
```
"SEVERE ACCUMULATED BURDEN DETECTED (BUI=76). Escalating to RED
for service reduction. Deep multi-temporal burnout risk requires
damage limitation."
```

---

## 10. Audit & Monitoring

### Audit Trail Requirements

All defense level transitions must be logged with:

```json
{
  "timestamp": "2025-12-30T14:30:00Z",
  "event_type": "defense_level_transition",
  "audit_id": "uuid-1234-5678",
  "from_level": "CONTROL",
  "to_level": "SAFETY_SYSTEMS",
  "fwi_score": 42.5,
  "danger_class": "HIGH",
  "trigger_type": "fwi_mapping | isi_escalation | bui_escalation | manual_override",
  "isi_value": 70.2,
  "bui_value": 35.1,
  "consecutive_count": 2,
  "hysteresis_active": true,
  "override_id": null,
  "initiated_by": "system | admin-user-id",
  "approval_status": "auto | admin-approved"
}
```

### Prometheus Metrics

```python
# Defense level tracking
defense_level_gauge = Gauge(
    "defense_level_current",
    "Current active defense level (1-5)"
)

# Transition tracking
defense_transitions_counter = Counter(
    "defense_transitions_total",
    "Total defense level transitions",
    ["from_level", "to_level", "trigger_type"]
)

# Component metrics
fwi_score_gauge = Gauge("fwi_score_current", "Current FWI")
fwi_isi_gauge = Gauge("fwi_isi_current", "Current ISI")
fwi_bui_gauge = Gauge("fwi_bui_current", "Current BUI")

# Hysteresis tracking
hysteresis_consecutive_gauge = Gauge(
    "defense_hysteresis_consecutive_count",
    "Current consecutive count for hysteresis"
)

# Override tracking
override_active_gauge = Gauge(
    "defense_override_active",
    "Whether manual override is active (0 or 1)"
)
```

### Dashboard Panels

**Key Visualizations:**

1. **Defense Level Gauge**
   - Current level with threshold colors (GREEN → YELLOW → ORANGE → RED → BLACK)
   - Updates every 5 minutes

2. **FWI Score Trend**
   - Time series of FWI, ISI, BUI
   - Threshold lines overlaid
   - Shows historical 30-day trend

3. **Defense Level Transitions**
   - Timeline of all transitions
   - Trigger type annotation
   - Who initiated (system vs. admin)

4. **Hysteresis State**
   - Current level vs. recommended level
   - Consecutive count progress
   - Time-to-threshold indicator

5. **Override Status**
   - Active overrides (if any)
   - Expiration countdown
   - Applied by information

### Alert Rules

**Critical (Fire Immediately):**
- `defense_level_current == 5` (EMERGENCY activated)
- Rapid escalation: 2+ level jumps in 30 minutes
- Override expiration without auto-restore

**High (Within 5 minutes):**
- `defense_level_current == 4` (CONTAINMENT for 5+ minutes)
- Frequent ISI escalations (> 3 per hour)

**Warning (Within 15 minutes):**
- `defense_level_current == 3` (ORANGE for 15+ minutes)
- Hysteresis preventing de-escalation (> 5 consecutive checks)
- BUI elevated sustained (> 70 for 2+ hours)

---

## Operational Reference Tables

### Quick Escalation Decision Tree

```
Is system under stress?
  ├─ No → GREEN (1)
  ├─ Yes: Are early warning signals appearing?
  │   ├─ No → GREEN (1)
  │   ├─ Yes: Are multiple indicators elevated?
  │   │   ├─ No → YELLOW (2)
  │   │   ├─ Yes: Is deterioration rapid (ISI > 60)?
  │   │   │   ├─ Yes → ORANGE (3) [ISI escalation]
  │   │   │   ├─ No: Is burden sustained deep (BUI > 70)?
  │   │   │   │   ├─ Yes → RED (4) [BUI escalation]
  │   │   │   │   ├─ No: Coverage sufficient (> 85%)?
  │   │   │   │   │   ├─ Yes → ORANGE (3)
  │   │   │   │   │   ├─ No → RED (4)
  │   │   │   │   │   ├─ Coverage critical (< 70%)?
  │   │   │   │   │   │   ├─ Yes → BLACK (5)
```

### Response Activation Checklist by Level

**YELLOW Activation Checklist:**
- [ ] Weekly FWI monitoring enabled
- [ ] Trend analysis initiated
- [ ] Director briefed
- [ ] Contingency rotations prepared
- [ ] Overtime budget pre-approved
- [ ] Dashboard alerts enabled

**ORANGE Activation Checklist:**
- [ ] Daily FWI updates active
- [ ] Auto-reassignment algorithms enabled
- [ ] Backup faculty pools notified
- [ ] Daily director stand-ups begun
- [ ] Service reduction plan reviewed
- [ ] Hospital leadership briefed

**RED Activation Checklist:**
- [ ] Service reduction protocols activated
- [ ] Faculty reassignments enforced
- [ ] Zone isolation implemented
- [ ] Hospital VP engaged
- [ ] Clinical leadership daily involvement
- [ ] Locum requisitions initiated
- [ ] Patient safety committee briefed

**BLACK Activation Checklist:**
- [ ] Hospital CEO notification
- [ ] Board briefing initiated
- [ ] All resources activated (locums, retired faculty)
- [ ] Regulatory notification (if required)
- [ ] Media communication prepared
- [ ] Incident command structure established
- [ ] Recovery timeline defined

---

## Appendix: Military DEFCON Analogy

The Defense-in-Depth system draws inspiration from military DEFCON (Defense Readiness Condition) levels, adapted for medical workforce resilience:

| DEFCON | Military Context | Defense Level | Medical Context |
|--------|------------------|---------------|-----------------|
| DEFCON 5 | Peacetime readiness | GREEN (1) | Normal scheduling, adequate staffing |
| DEFCON 4 | Increased readiness | YELLOW (2) | Elevated workload, monitoring increased |
| DEFCON 3 | Increase in force readiness | ORANGE (3) | Partial mobilization, protective measures |
| DEFCON 2 | Further increase in readiness | RED (4) | Full mobilization, service curtailment |
| DEFCON 1 | Maximum readiness | BLACK (5) | Full crisis mode, external escalation |

**Key Difference:** Unlike military escalation which may involve external threats, medical escalation is based on internal workforce capacity and burnout indicators.

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-30 | Initial comprehensive reference document |

---

**Document Classification:** Operational Reference - Share with Program Directors, Hospital Leadership, and Scheduling Administrators
**Last Reviewed:** 2025-12-30
**Next Review:** Q1 2026
