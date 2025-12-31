# ACGME Validator Agent - Prompt Templates

> **Role:** ACGME compliance validation, rule enforcement, violation detection
> **Model:** Claude Opus 4.5
> **Mission:** Ensure 100% ACGME compliance

## 1. COMPLIANCE VALIDATION TEMPLATE

```
**ACGME COMPLIANCE VALIDATION**

**VALIDATION DATE:** ${TODAY}
**VALIDATION SCOPE:** ${SCOPE}

**ACGME RULES ENFORCED:**

### Rule 1: 80-Hour Rule
- Maximum 80 hours per week (averaged over 4-week periods)
- Measurement: Actual hours worked
- Threshold: Violation if avg > 80 hours/week

### Rule 2: 1-in-7 Rule
- Minimum 1 full day off every 7 days
- Measurement: 24-hour continuous period off
- Threshold: Violation if < 1 day off per 7 days

### Rule 3: Supervision Ratios
- PGY-1: 1 faculty per 2 residents
- PGY-2/3: 1 faculty per 4 residents
- Measurement: Concurrent assignments
- Threshold: Cannot exceed ratio

### Rule 4: Clinical Supervision
- Appropriate supervision of all clinical work
- Measurement: Qualifications of supervisor
- Threshold: Must be credentialed for activity

**VALIDATION ALGORITHM:**
1. Extract schedule data for person + date range
2. Calculate hours for each week
3. Calculate days off for each 7-day window
4. Check supervision ratios
5. Compare against thresholds
6. Generate compliance report

Validate ACGME compliance.
```

## 2. 80-HOUR RULE VALIDATION TEMPLATE

```
**80-HOUR RULE VALIDATION**

**RULE:** Max 80 hours per week (4-week rolling average)

**VALIDATION PARAMETERS:**
- Person ID: ${PERSON_ID}
- Start date: ${START_DATE}
- End date: ${END_DATE}
- Measurement unit: Hours worked

**CALCULATION METHOD:**
1. Get all assignments for person in date range
2. Group by week (Sunday-Saturday)
3. Calculate hours per week
4. Calculate 4-week rolling average
5. Compare to 80-hour threshold

**EXAMPLE CALCULATION:**
\`\`\`
Week 1: 78 hours
Week 2: 82 hours  (VIOLATION: > 80)
Week 3: 75 hours
Week 4: 76 hours
Week 5: 80 hours

4-week average (W1-W4): 77.75 hours (COMPLIANT)
4-week average (W2-W5): 78.25 hours (COMPLIANT)
Single week violation: Week 2 = 82 hours
\`\`\`

**VIOLATION DETECTION:**
- Hard violation: Single week > 85 hours
- Soft violation: 4-week avg > 80 hours
- Trending violation: Moving average increasing

**OUTPUT FORMAT:**
\`\`\`json
{
  "person_id": "${ID}",
  "rule": "80_hour",
  "compliant": false,
  "max_hours_observed": 82,
  "avg_hours_4_week": 78.25,
  "violations": [
    {
      "week": "2025-01-13",
      "hours": 82,
      "margin": 2
    }
  ]
}
\`\`\`

Validate 80-hour rule.
```

## 3. 1-IN-7 RULE VALIDATION TEMPLATE

```
**1-IN-7 RULE VALIDATION**

**RULE:** Minimum 1 full day off every 7 days

**VALIDATION PARAMETERS:**
- Person ID: ${PERSON_ID}
- Start date: ${START_DATE}
- End date: ${END_DATE}
- Full day off: 24-hour continuous, no assignments

**CALCULATION METHOD:**
1. Create list of all assigned dates
2. For each 7-day window (rolling), check for unassigned day
3. Count consecutive assigned days
4. Flag if > 6 consecutive days assigned

**VIOLATION DETECTION:**
- Maximum consecutive assigned days: 6
- Violation: 7+ consecutive assigned days
- Edge case: Assignment ending at 11:59 PM counts as next day off

**OUTPUT FORMAT:**
\`\`\`json
{
  "person_id": "${ID}",
  "rule": "1_in_7",
  "compliant": true,
  "max_consecutive_assigned": 5,
  "violations": [],
  "windows_analyzed": 52,
  "windows_compliant": 52
}
\`\`\`

Validate 1-in-7 rule.
```

## 4. SUPERVISION RATIO VALIDATION TEMPLATE

```
**SUPERVISION RATIO VALIDATION**

**RULE:** Faculty-to-resident ratios

**RATIOS:**
- PGY-1: 1 faculty per 2 residents (max 2:1)
- PGY-2/3: 1 faculty per 4 residents (max 4:1)

**VALIDATION PARAMETERS:**
- Rotation type: ${ROTATION_TYPE}
- Date: ${DATE}
- Rotation block: ${BLOCK}

**CALCULATION METHOD:**
1. Get all concurrent assignments for rotation
2. Count residents by PGY level
3. Count supervising faculty
4. Calculate actual ratio
5. Compare to required ratio

**VIOLATION DETECTION:**
- PGY-1 violations: More than 2 residents per faculty member
- PGY-2/3 violations: More than 4 residents per faculty member
- Missing supervisor: No qualified faculty assigned

**OUTPUT FORMAT:**
\`\`\`json
{
  "rotation": "${ROTATION}",
  "date": "${DATE}",
  "pgy1": {
    "residents": 4,
    "faculty": 2,
    "ratio": "2:1",
    "required": "2:1",
    "compliant": true
  },
  "pgy2_3": {
    "residents": 8,
    "faculty": 2,
    "ratio": "4:1",
    "required": "4:1",
    "compliant": true
  }
}
\`\`\`

Validate supervision ratios.
```

## 5. VIOLATION REPORTING TEMPLATE

```
**ACGME VIOLATION REPORT**

**REPORT DATE:** ${TODAY}
**REPORT PERIOD:** ${PERIOD}

**VIOLATION SUMMARY:**
- Total violations: ${TOTAL_VIOLATIONS}
- Affected personnel: ${AFFECTED_PERSONNEL}
- Critical violations: ${CRITICAL_COUNT}
- High violations: ${HIGH_COUNT}

**VIOLATIONS BY RULE:**

### 80-Hour Rule
- Violations: ${VIOLATIONS_80H}
- Affected residents: ${RESIDENTS_80H}
- Avg violation amount: ${AVG_EXCESS}hours

### 1-in-7 Rule
- Violations: ${VIOLATIONS_1IN7}
- Affected residents: ${RESIDENTS_1IN7}
- Consecutive days: Max ${MAX_CONSECUTIVE}

### Supervision Ratios
- Violations: ${VIOLATIONS_RATIO}
- Affected rotations: ${ROTATIONS}
- Ratios violated: ${RATIOS}

**AFFECTED PERSONNEL:**
\`\`\`json
[
  {
    "person_id": "${ID}",
    "name": "${NAME}",
    "pgy_level": "${LEVEL}",
    "violations": [
      {
        "rule": "80_hour",
        "date": "${DATE}",
        "severity": "HIGH"
      }
    ],
    "remediation": "${ACTION}"
  }
]
\`\`\`

**REMEDIATION ACTIONS:**
1. ${ACTION_1}
2. ${ACTION_2}
3. ${ACTION_3}

Report violations and remediation.
```

## 6. SCHEDULE COMPLIANCE CHECK TEMPLATE

```
**PRE-EXECUTION COMPLIANCE CHECK**

**SCHEDULE:** ${SCHEDULE_ID}
**CHECK DATE:** ${TODAY}

**COMPLIANCE CHECKPOINTS:**

### Before Schedule Execution
- [ ] All assignments have proper supervision
- [ ] No 80-hour violations projected
- [ ] All residents have adequate time off
- [ ] Credentials verified for all assignments

### Safety Checks
- [ ] Rotation coverage adequate
- [ ] Backup coverage planned
- [ ] Emergency contacts available
- [ ] Escalation paths clear

**CHECK RESULTS:**
- Overall compliance: ${COMPLIANCE_STATUS}
- Warnings: ${WARNING_COUNT}
- Blockers: ${BLOCKER_COUNT}

**APPROVAL DECISION:**
- Schedule approved for execution: ${APPROVED}
- Conditions: ${CONDITIONS}
- Remediation required: ${REMEDIATION}

Approve or block schedule for execution.
```

## 7. AUDIT TRAIL TEMPLATE

```
**AUDIT TRAIL: ACGME Compliance**

**AUDIT SCOPE:**
- Date range: ${START_DATE} to ${END_DATE}
- Personnel: All active residents/faculty
- Compliance rules: All (80-hour, 1-in-7, ratios)

**AUDIT EVENTS:**
\`\`\`json
[
  {
    "timestamp": "2025-12-31T10:30:00Z",
    "event": "violation_detected",
    "person_id": "${ID}",
    "rule": "80_hour",
    "value": 85,
    "threshold": 80,
    "action_taken": "escalated"
  },
  {
    "timestamp": "2025-12-31T11:00:00Z",
    "event": "violation_resolved",
    "person_id": "${ID}",
    "resolution": "schedule_modified",
    "modified_by": "${COORDINATOR}",
    "new_value": 78
  }
]
\`\`\`

**COMPLIANCE TIMELINE:**
- Violations detected: ${DETECTED_COUNT}
- Violations resolved: ${RESOLVED_COUNT}
- Escalations required: ${ESCALATIONS}
- Unresolved: ${UNRESOLVED_COUNT}

Generate audit trail.
```

## 8. STATUS REPORT TEMPLATE

```
**ACGME VALIDATOR STATUS REPORT**

**REPORT DATE:** ${TODAY}
**REPORTING PERIOD:** ${PERIOD}

**COMPLIANCE METRICS:**
- Overall compliance: ${OVERALL_PERCENT}%
- Personnel compliant: ${COMPLIANT_COUNT}/${TOTAL_COUNT}
- 80-hour rule: ${RULE_80H_PERCENT}%
- 1-in-7 rule: ${RULE_1IN7_PERCENT}%
- Supervision: ${SUPERVISION_PERCENT}%

**VIOLATIONS:**
- New violations: ${NEW_VIOLATIONS}
- Resolved violations: ${RESOLVED_VIOLATIONS}
- Unresolved: ${UNRESOLVED}
- Escalations: ${ESCALATIONS}

**TRENDS:**
- Compliance trend: ${TREND_DIRECTION}
- Most common violation: ${COMMON_VIOLATION}
- At-risk residents: ${AT_RISK_COUNT}

**CORRECTIVE ACTIONS:**
${CORRECTIVE_ACTIONS}

**NEXT AUDIT:** ${NEXT_AUDIT_DATE}
```

---

*Last Updated: 2025-12-31*
*Agent: ACGME Validator*
*Version: 1.0*
