# Conflict Resolution Workflow

Systematic approach to handling unavoidable scheduling conflicts and trade-offs in medical residency scheduling.

---

## Overview

Scheduling conflicts occur when constraints cannot all be simultaneously satisfied. This workflow provides a structured approach to:

1. **Rank conflicts by severity** - ACGME violations vs. preferences
2. **Generate resolution options** - Multiple trade-off proposals
3. **Document decisions** - Maintain audit trail for exceptions
4. **Escalate appropriately** - Know when to involve Program Director

**Core Principle:** ACGME compliance is non-negotiable. All other conflicts can be resolved through trade-offs and approvals.

---

## Conflict Classification

### Tier 1: Critical Conflicts (ACGME Violations)

**Impact:** Schedule cannot be deployed
**Resolution Authority:** Must be fixed, no exceptions
**Timeline:** Immediate resolution required

**Examples:**
- Resident scheduled for 85 hours in a week
- No 24-hour off period in 7 days
- PGY-1 supervision ratio violated (>2 residents per faculty)
- Post-call relief not provided (assigned shifts <8 hours after 24-hour call)

**Resolution Strategy:**
1. Identify the specific violation
2. Find alternative assignments that satisfy ACGME rule
3. Regenerate schedule if necessary
4. **Never deploy with Tier 1 conflicts**

### Tier 2: High Conflicts (Institutional Policy Violations)

**Impact:** Requires Program Director approval to override
**Resolution Authority:** Program Director or Curriculum Committee
**Timeline:** Must document and get approval before deployment

**Examples:**
- Hard preference block violated (scheduled during approved vacation)
- FMIT sequencing violated (PGY-1 doesn't get FMIT in first 6 months)
- Coverage falls below institutional minimum (not ACGME minimum)
- Military deployment scheduling conflict

**Resolution Strategy:**
1. Document the policy violation
2. Propose exception with rationale
3. Get written approval from authority
4. Record exception in audit log

### Tier 3: Medium Conflicts (Optimization Trade-offs)

**Impact:** Lower satisfaction scores
**Resolution Authority:** Program Coordinator or Chief Resident
**Timeline:** Document and inform affected parties

**Examples:**
- Shift preference not honored (wanted AM, got PM)
- Workload slightly imbalanced (Gini = 0.17 vs. target 0.15)
- Rotation preference not met (wanted Neurology, assigned ID)
- Continuity team change mid-year

**Resolution Strategy:**
1. Quantify the impact
2. Offer compensatory adjustments if possible
3. Communicate with affected person
4. Track for future consideration

### Tier 4: Low Conflicts (Minor Suboptimality)

**Impact:** Minimal, acceptable as-is
**Resolution Authority:** Informational only
**Timeline:** Log for future improvement

**Examples:**
- Schedule has small gaps (efficiency score 0.88 vs. target 0.90)
- Slightly more fragmentation than ideal
- Backup capacity at 81% (vs. target 80%)
- Preference satisfaction at 79% (vs. target 80%)

**Resolution Strategy:**
1. Document for future reference
2. No action required unless pattern emerges
3. Consider for next generation cycle

---

## Conflict Identification

### Automated Detection

**Run conflict detection:**

```bash
# Via MCP tool
mcp call detect_conflicts --schedule_id="2026-2027-academic-year"

# Via API
curl -X POST http://localhost:8000/api/v1/schedule/detect-conflicts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"schedule_id": "2026-2027-academic-year", "strict": true}'
```

**Expected output:**

```json
{
  "schedule_id": "2026-2027-academic-year",
  "total_conflicts": 7,
  "conflicts_by_tier": {
    "tier1_critical": 0,
    "tier2_high": 2,
    "tier3_medium": 4,
    "tier4_low": 1
  },
  "conflicts": [
    {
      "id": "conflict-001",
      "tier": 2,
      "type": "HARD_PREFERENCE_VIOLATION",
      "severity": "HIGH",
      "description": "PGY1-03 scheduled during approved vacation",
      "affected_people": ["PGY1-03"],
      "affected_dates": ["2026-12-25"],
      "constraint_violated": "Hard block preference",
      "suggested_resolutions": [
        "Find substitute for Dec 25",
        "Swap with PGY1-04 who is available"
      ]
    },
    {
      "id": "conflict-002",
      "tier": 3,
      "type": "FAIRNESS_IMBALANCE",
      "severity": "MEDIUM",
      "description": "Workload imbalance (Gini=0.17)",
      "affected_people": ["PGY2-01", "PGY2-05"],
      "metric": {
        "current": 0.17,
        "target": 0.15,
        "pgy2_01_hours": 76,
        "pgy2_05_hours": 68
      },
      "suggested_resolutions": [
        "Swap one shift from PGY2-01 to PGY2-05",
        "Adjust future assignments to rebalance"
      ]
    }
  ]
}
```

### Manual Review

**Check for common conflict patterns:**

1. **Post-holiday stacking:**
   ```sql
   -- People with back-to-back holiday coverage
   SELECT person_id, COUNT(*) as holiday_count
   FROM assignments
   WHERE rotation_type = 'HOLIDAY_COVERAGE'
   GROUP BY person_id
   HAVING COUNT(*) > 2;
   ```

2. **Consecutive high-intensity rotations:**
   ```sql
   -- People with 3+ consecutive weeks of high-intensity rotations
   SELECT person_id, start_date, rotation
   FROM assignments
   WHERE rotation_intensity = 'HIGH'
   ORDER BY person_id, start_date;
   ```

3. **Insufficient post-call relief:**
   ```sql
   -- Assignments within 8 hours of previous 24-hour shift
   SELECT a1.person_id, a1.end_datetime, a2.start_datetime
   FROM assignments a1
   JOIN assignments a2 ON a1.person_id = a2.person_id
   WHERE a1.rotation_type = 'CALL_24HR'
     AND a2.start_datetime < (a1.end_datetime + INTERVAL '8 hours');
   ```

---

## Resolution Process

### Step 1: Rank Conflicts by Priority

**Create conflict priority list:**

```python
def rank_conflicts(conflicts):
    """Sort conflicts by resolution priority."""

    def priority_score(conflict):
        # Tier 1 (ACGME) = highest priority
        tier_score = (4 - conflict['tier']) * 1000

        # Within tier, sort by number of affected people
        people_score = len(conflict['affected_people']) * 10

        # Then by date proximity (earlier dates = higher priority)
        date_score = get_days_until(conflict['affected_dates'][0])

        return tier_score + people_score + date_score

    return sorted(conflicts, key=priority_score, reverse=True)
```

**Example ranked list:**

```
Priority  | ID           | Tier | Type                      | Affected
----------|--------------|------|---------------------------|------------------
1         | conflict-003 | 1    | ACGME_80_HOUR             | PGY2-04
2         | conflict-001 | 2    | HARD_PREFERENCE_VIOLATION | PGY1-03
3         | conflict-005 | 2    | COVERAGE_BELOW_MIN        | Block 7, EM
4         | conflict-002 | 3    | FAIRNESS_IMBALANCE        | PGY2-01, PGY2-05
5         | conflict-004 | 3    | SHIFT_PREFERENCE          | PGY1-07
6         | conflict-006 | 3    | CONTINUITY_BREAK          | PGY3-02
7         | conflict-007 | 4    | EFFICIENCY_SUBOPTIMAL     | All
```

### Step 2: Generate Resolution Proposals

**For each conflict, generate 2-3 resolution options:**

#### Example: ACGME Work Hour Violation

**Conflict:**
```
PGY2-04 scheduled for 82 hours in week of 2026-03-15
- Current: 82 hours
- ACGME limit: 80 hours
- Violation: 2 hours over
```

**Resolution Options:**

```json
{
  "conflict_id": "conflict-003",
  "resolution_options": [
    {
      "id": "option-A",
      "description": "Remove one 4-hour clinic shift",
      "actions": [
        {
          "action": "remove_assignment",
          "person": "PGY2-04",
          "date": "2026-03-18",
          "rotation": "Continuity Clinic"
        },
        {
          "action": "find_substitute",
          "rotation": "Continuity Clinic",
          "date": "2026-03-18",
          "candidates": ["PGY2-01", "PGY2-03"]
        }
      ],
      "impact": {
        "work_hours_pgy2_04": 78,
        "coverage_maintained": true,
        "acgme_compliant": true
      },
      "trade_offs": "Continuity with patient panel interrupted"
    },
    {
      "id": "option-B",
      "description": "Shorten two 6-hour shifts to 5 hours each",
      "actions": [
        {
          "action": "modify_assignment",
          "person": "PGY2-04",
          "date": "2026-03-16",
          "rotation": "Inpatient",
          "old_hours": 6,
          "new_hours": 5
        },
        {
          "action": "modify_assignment",
          "person": "PGY2-04",
          "date": "2026-03-17",
          "rotation": "Inpatient",
          "old_hours": 6,
          "new_hours": 5
        }
      ],
      "impact": {
        "work_hours_pgy2_04": 80,
        "coverage_maintained": true,
        "acgme_compliant": true
      },
      "trade_offs": "Reduced inpatient coverage by 2 hours"
    },
    {
      "id": "option-C",
      "description": "Move weekend call to following week",
      "actions": [
        {
          "action": "move_assignment",
          "person": "PGY2-04",
          "rotation": "Weekend Call",
          "from_date": "2026-03-20",
          "to_date": "2026-03-27"
        },
        {
          "action": "find_substitute",
          "rotation": "Weekend Call",
          "date": "2026-03-20",
          "candidates": ["PGY2-02", "PGY2-06"]
        }
      ],
      "impact": {
        "work_hours_pgy2_04_week1": 74,
        "work_hours_pgy2_04_week2": 82,
        "acgme_compliant": false
      },
      "trade_offs": "Shifts violation to next week - NOT VIABLE"
    }
  ],
  "recommendation": "option-A"
}
```

#### Example: Hard Preference Violation

**Conflict:**
```
PGY1-03 scheduled during approved vacation (Dec 25)
- Preference type: Hard block
- Dates: 2026-12-24 to 2026-12-26
- Current assignment: Emergency coverage Dec 25
```

**Resolution Options:**

```json
{
  "conflict_id": "conflict-001",
  "resolution_options": [
    {
      "id": "option-A",
      "description": "Swap with PGY1-04 who is available",
      "actions": [
        {
          "action": "execute_swap",
          "person1": "PGY1-03",
          "person2": "PGY1-04",
          "date": "2026-12-25",
          "rotation": "Emergency Coverage"
        }
      ],
      "impact": {
        "preference_honored": true,
        "coverage_maintained": true,
        "pgy1_04_consent_required": true
      },
      "trade_offs": "Requires PGY1-04 to work holiday"
    },
    {
      "id": "option-B",
      "description": "Use backup faculty coverage",
      "actions": [
        {
          "action": "remove_assignment",
          "person": "PGY1-03",
          "date": "2026-12-25",
          "rotation": "Emergency Coverage"
        },
        {
          "action": "assign_faculty",
          "person": "FAC-BACKUP-01",
          "date": "2026-12-25",
          "rotation": "Emergency Coverage"
        }
      ],
      "impact": {
        "preference_honored": true,
        "coverage_maintained": true,
        "faculty_overtime_cost": 800
      },
      "trade_offs": "Budget impact ($800 overtime)"
    },
    {
      "id": "option-C",
      "description": "Revoke vacation approval (requires PD approval)",
      "actions": [
        {
          "action": "override_preference",
          "person": "PGY1-03",
          "preference_id": "pref-125",
          "authority": "Program Director",
          "rationale": "Critical coverage shortage"
        }
      ],
      "impact": {
        "preference_honored": false,
        "coverage_maintained": true,
        "morale_impact": "HIGH"
      },
      "trade_offs": "Policy violation, requires exceptional circumstances"
    }
  ],
  "recommendation": "option-A (if PGY1-04 consents, else option-B)"
}
```

### Step 3: Evaluate Trade-offs

**Trade-off analysis framework:**

| Dimension | Weight | Evaluation Criteria |
|-----------|--------|---------------------|
| **ACGME Compliance** | 1.0 | Must be 100% compliant |
| **Coverage Adequacy** | 0.9 | Minimum levels must be met |
| **Policy Adherence** | 0.7 | Institutional rules followed |
| **Fairness** | 0.6 | Equitable distribution |
| **Preference Satisfaction** | 0.5 | Honor stated preferences |
| **Cost** | 0.4 | Budget impact |
| **Morale** | 0.3 | Resident/faculty satisfaction |

**Scoring resolution options:**

```python
def score_resolution(option, weights):
    """Score a resolution option across multiple dimensions."""

    scores = {
        'acgme_compliance': 1.0 if option['impact']['acgme_compliant'] else 0.0,
        'coverage_adequacy': 1.0 if option['impact']['coverage_maintained'] else 0.0,
        'policy_adherence': calculate_policy_score(option),
        'fairness': calculate_fairness_score(option),
        'preference_satisfaction': calculate_preference_score(option),
        'cost': calculate_cost_score(option),
        'morale': calculate_morale_score(option)
    }

    weighted_score = sum(
        scores[dimension] * weights[dimension]
        for dimension in scores
    )

    return {
        'total_score': weighted_score,
        'dimension_scores': scores,
        'is_viable': scores['acgme_compliance'] == 1.0 and scores['coverage_adequacy'] == 1.0
    }
```

### Step 4: Document Decisions

**All conflict resolutions must be documented:**

#### Resolution Documentation Template

```markdown
## Conflict Resolution Report

**Conflict ID:** conflict-001
**Date Resolved:** 2026-11-15
**Resolved By:** Program Coordinator

### Conflict Description
- **Type:** Hard Preference Violation
- **Severity:** Tier 2 (High)
- **Affected People:** PGY1-03
- **Affected Dates:** 2026-12-25
- **Description:** Resident scheduled during approved vacation

### Resolution Selected
**Option:** option-A (Swap with PGY1-04)

**Actions Taken:**
1. Contacted PGY1-04, received consent for holiday swap
2. Executed swap via swap management system (swap_id: swap-456)
3. Notified both residents via email
4. Updated holiday coverage roster

**Impact:**
- Preference honored: ✓
- Coverage maintained: ✓
- Consent obtained: ✓
- Budget impact: $0

### Trade-offs Accepted
- PGY1-04 works holiday instead of PGY1-03
- PGY1-04 receives compensatory time off in January

### Approvals
- **Resident Consent (PGY1-04):** Obtained 2026-11-15
- **Chief Resident:** Approved 2026-11-15
- **Program Coordinator:** Executed 2026-11-15

### Audit Trail
- Original assignment: assignment-8472
- Swap request: swap-456
- Final assignment: assignment-8473
```

#### Store in Database

```python
conflict_resolution = ConflictResolution(
    conflict_id="conflict-001",
    conflict_type="HARD_PREFERENCE_VIOLATION",
    tier=2,
    resolved_date=datetime.now(),
    resolved_by="coordinator-01",
    resolution_option="option-A",
    actions_taken=[
        {"action": "execute_swap", "swap_id": "swap-456"},
        {"action": "notify", "recipients": ["PGY1-03", "PGY1-04"]}
    ],
    approvals=[
        {"role": "resident", "person": "PGY1-04", "date": "2026-11-15"},
        {"role": "chief_resident", "date": "2026-11-15"},
        {"role": "coordinator", "date": "2026-11-15"}
    ],
    trade_offs="PGY1-04 works holiday, receives compensatory time",
    notes="Resolution successful, both residents satisfied"
)
db.add(conflict_resolution)
db.commit()
```

---

## Escalation Procedures

### When to Escalate

#### Escalate to Chief Resident
- Tier 3 conflicts requiring peer mediation
- Swap negotiations between residents
- Minor policy clarifications

#### Escalate to Program Coordinator
- Tier 2 conflicts requiring administrative action
- Coverage gaps requiring backup scheduling
- Budget-impacting resolutions (faculty overtime)

#### Escalate to Program Director
- Tier 1 conflicts that cannot be auto-resolved
- Tier 2 conflicts requiring policy exceptions
- Multiple simultaneous high-severity conflicts
- Systemic issues (recurring pattern)

#### Escalate to Curriculum Committee
- Rotation structure conflicts
- Curriculum requirement conflicts
- Major policy change proposals

### Escalation Template

```markdown
## Escalation Request

**To:** Program Director
**From:** Program Coordinator
**Date:** 2026-11-20
**Priority:** HIGH

### Issue Summary
Multiple conflicts detected in Block 7 schedule due to simultaneous absences.

### Conflicts Requiring Resolution
1. **conflict-005** (Tier 2): Emergency Medicine coverage below minimum
   - Required: 3 residents
   - Available: 2 residents
   - Dates: 2026-03-12 to 2026-03-18

2. **conflict-008** (Tier 2): FMIT sequencing violation for PGY1-02
   - Required: FMIT by end of December
   - Current: Scheduled for January
   - Reason: Three PGY-1s on approved leave in November

### Root Cause
- Deployment: PGY2-03 (2 weeks)
- Conference: PGY2-05 (1 week)
- Sick leave: PGY1-04 (1 week)
- Pre-approved vacation: PGY1-03 (1 week)

Total: 4 residents unavailable, overlapping for 3 days

### Attempted Resolutions
1. ✗ Reduce coverage to 2 residents - Violates institutional policy
2. ✗ Cancel approved vacation - Ethically problematic
3. ✗ Move rotation to different block - FMIT sequencing further violated

### Proposed Solutions Requiring PD Approval

**Option A: Temporary coverage reduction with enhanced supervision**
- Reduce EM to 2 residents for 3 days
- Add senior faculty for direct supervision
- Document as exceptional circumstance
- Estimated cost: $1,200

**Option B: Adjust FMIT timeline for PGY1-02**
- Extend FMIT deadline to end of January
- Requires Curriculum Committee approval
- Maintains EM coverage at 3 residents

**Option C: Recall resident from conference**
- Ask PGY2-05 to return early from conference
- Maintains coverage and FMIT timeline
- Significant morale and educational impact

### Recommendation
Option A with Option B as backup

Option A addresses immediate coverage need with enhanced safety (senior faculty).
Option B is acceptable if conference is essential for PGY2-05's research.
Option C should be last resort due to educational impact.

### Required Decision
Please approve Option A or select alternative by 2026-11-22.

### Supporting Documents
- Block 7 coverage analysis
- Faculty availability matrix
- FMIT rotation schedule
- Absence approval records
```

---

## Automated Conflict Resolution

### Swap Auto-Matcher

**For preference conflicts, automatically suggest swaps:**

```python
def auto_match_swaps(conflict):
    """Find potential swap candidates to resolve conflict."""

    if conflict['type'] != 'PREFERENCE_VIOLATION':
        return []

    person = conflict['affected_people'][0]
    dates = conflict['affected_dates']
    unwanted_assignment = get_assignment(person, dates)

    # Find people who:
    # 1. Are available on those dates
    # 2. Are qualified for the rotation
    # 3. Might want this shift (preference match)
    candidates = []

    for other_person in get_all_residents():
        if other_person.id == person:
            continue

        # Check availability
        if not is_available(other_person, dates):
            continue

        # Check qualification
        if not is_qualified(other_person, unwanted_assignment.rotation):
            continue

        # Check if this matches their preference
        preference_score = calculate_preference_match(
            other_person,
            unwanted_assignment.rotation,
            dates
        )

        # Check what they could offer in return
        their_assignments = get_assignments(other_person, date_range=dates)

        for their_assignment in their_assignments:
            # Would original person want this?
            reverse_score = calculate_preference_match(
                person,
                their_assignment.rotation,
                their_assignment.dates
            )

            if preference_score > 0.5 and reverse_score > 0.5:
                candidates.append({
                    'candidate': other_person.id,
                    'offer_rotation': their_assignment.rotation,
                    'swap_type': 'one-to-one',
                    'match_score': (preference_score + reverse_score) / 2,
                    'estimated_satisfaction_gain': preference_score - 0.3  # Current dissatisfaction
                })

    return sorted(candidates, key=lambda c: c['match_score'], reverse=True)
```

### Fairness Auto-Balancer

**For workload imbalance, automatically rebalance:**

```python
def auto_balance_workload(conflict):
    """Propose shift transfers to improve fairness."""

    if conflict['type'] != 'FAIRNESS_IMBALANCE':
        return []

    overloaded = [p for p in conflict['affected_people'] if get_workload(p) > average_workload]
    underloaded = [p for p in conflict['affected_people'] if get_workload(p) < average_workload]

    proposals = []

    for overloaded_person in overloaded:
        # Find their lowest-priority assignments
        assignments = get_assignments(overloaded_person, order_by='priority')

        for assignment in assignments:
            # Find underloaded person who can take it
            for underloaded_person in underloaded:
                if can_transfer(assignment, from_person=overloaded_person, to_person=underloaded_person):
                    new_gini = calculate_gini_after_transfer(assignment, overloaded_person, underloaded_person)

                    proposals.append({
                        'from_person': overloaded_person,
                        'to_person': underloaded_person,
                        'assignment': assignment,
                        'gini_improvement': conflict['metric']['current'] - new_gini,
                        'estimated_effort': 'LOW'  # Single shift transfer
                    })

    return sorted(proposals, key=lambda p: p['gini_improvement'], reverse=True)
```

---

## Conflict Prevention

### Proactive Strategies

#### 1. Front-load Constraint Checking

**Check for conflicts BEFORE generating schedule:**

```bash
# Pre-generation conflict detection
curl -X POST http://localhost:8000/api/v1/schedule/pre-check \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "ctx-2026-2027",
    "check_types": ["absences", "coverage", "qualifications"]
  }'
```

#### 2. Stagger Absences

**Guidance for coordinators:**
- Limit concurrent absences to 10% of residents
- Spread conference attendance across months
- Blackout periods for critical rotations

#### 3. Maintain Buffer Capacity

**Resilience-based planning:**
- Never schedule above 80% utilization
- Maintain backup pool (faculty, moonlighters)
- Pre-approve substitute arrangements

#### 4. Regular Schedule Health Checks

**Weekly monitoring:**

```bash
# Automated health check (run via cron)
curl -X GET http://localhost:8000/api/v1/schedule/health \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.warnings, .violations'
```

---

## See Also

- `Workflows/generate-schedule.md` - Complete workflow including conflict resolution
- `Workflows/constraint-propagation.md` - Early conflict detection
- `Reference/constraint-index.md` - All constraints with override authorities
- `swap-management` skill - Swap-based conflict resolution
- `acgme-compliance` skill - ACGME violation handling
