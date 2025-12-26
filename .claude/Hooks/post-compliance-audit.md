# Post-Compliance Audit Hook

**Trigger:** After ACGME compliance audit completes

## Purpose

Record compliance audit results for:
- Regulatory documentation
- Trend analysis
- Proactive violation prevention
- Performance monitoring
- Accreditation preparation

---

## What to Capture

### 1. Audit Metadata

**File:** `History/compliance/audit_YYYY-MM-DD_HHMMSS.json`

```json
{
  "audit_id": "AUD-20251226-001",
  "timestamp": "2025-12-26T15:00:00Z",
  "auditor": "system|manual",
  "user": "admin",
  "schedule_id": "current",
  "audit_period": {
    "start_date": "2026-03-12",
    "end_date": "2026-04-08",
    "duration_days": 28,
    "duration_weeks": 4
  },
  "duration_seconds": 2.4
}
```

### 2. Overall Compliance Score

```json
{
  "compliance_summary": {
    "overall_status": "COMPLIANT|WARNING|VIOLATION",
    "compliance_score": 94.2,
    "score_breakdown": {
      "80_hour_rule": 98.0,
      "1_in_7_rule": 100.0,
      "supervision_ratio": 85.7,
      "duty_period_limits": 92.3
    },
    "total_people_audited": 27,
    "total_violations": 3,
    "critical_violations": 1,
    "warnings": 7,
    "compliant_areas": 87
  }
}
```

### 3. 80-Hour Rule Violations

```json
{
  "80_hour_violations": [
    {
      "person_id": "PGY2-03",
      "person_name": "Resident Name",
      "week_start": "2026-03-20",
      "week_end": "2026-03-26",
      "hours_worked": 82.5,
      "limit": 80.0,
      "overage": 2.5,
      "four_week_average": 78.3,
      "severity": "critical",
      "assignments": [
        {"date": "2026-03-20", "session": "AM", "rotation": "inpatient", "hours": 8},
        {"date": "2026-03-20", "session": "PM", "rotation": "call", "hours": 16}
      ]
    }
  ],
  "80_hour_warnings": [
    {
      "person_id": "PGY1-05",
      "week_start": "2026-03-27",
      "hours_worked": 78.5,
      "limit": 80.0,
      "margin": 1.5,
      "severity": "warning",
      "trend": "increasing"
    }
  ]
}
```

### 4. 1-in-7 Rule Violations

```json
{
  "1_in_7_violations": [
    {
      "person_id": "PGY3-01",
      "person_name": "Resident Name",
      "violation_period": {
        "start": "2026-03-12",
        "end": "2026-03-19",
        "consecutive_duty_days": 8
      },
      "last_day_off": "2026-03-11",
      "next_day_off": "2026-03-20",
      "severity": "critical",
      "reason": "Holiday coverage stacking"
    }
  ],
  "1_in_7_warnings": [
    {
      "person_id": "PGY2-04",
      "current_consecutive_days": 6,
      "next_scheduled_off": "2026-03-21",
      "compliant_if_off": true,
      "severity": "warning"
    }
  ]
}
```

### 5. Supervision Ratio Violations

```json
{
  "supervision_violations": [
    {
      "date": "2026-03-15",
      "session": "PM",
      "rotation": "inpatient",
      "required_ratio": "2:1",
      "actual_ratio": "3:1",
      "residents": ["PGY1-01", "PGY1-03", "PGY1-05"],
      "faculty": ["FAC-001"],
      "severity": "critical",
      "pgy_level": "PGY-1"
    }
  ],
  "supervision_warnings": [
    {
      "date": "2026-03-22",
      "session": "AM",
      "rotation": "procedures_half_day",
      "residents": ["PGY2-01", "PGY2-02", "PGY2-03", "PGY2-04"],
      "faculty": ["FAC-002"],
      "actual_ratio": "4:1",
      "required_ratio": "4:1",
      "at_capacity": true,
      "severity": "warning"
    }
  ]
}
```

### 6. Duty Period Violations

```json
{
  "duty_period_violations": [
    {
      "person_id": "PGY2-05",
      "date": "2026-03-18",
      "shift_start": "2026-03-18T07:00:00Z",
      "shift_end": "2026-03-19T09:00:00Z",
      "duration_hours": 26,
      "limit_hours": 24,
      "overage_hours": 2,
      "type": "extended_shift",
      "severity": "critical"
    }
  ],
  "time_off_violations": [
    {
      "person_id": "PGY1-02",
      "shift1_end": "2026-03-17T17:00:00Z",
      "shift2_start": "2026-03-18T00:00:00Z",
      "time_off_hours": 7,
      "required_hours": 8,
      "shortage_hours": 1,
      "severity": "critical"
    }
  ]
}
```

### 7. Trend Data

```json
{
  "trends": {
    "30_day_comparison": {
      "previous_audit": {
        "date": "2025-11-26",
        "violations": 5,
        "warnings": 12,
        "score": 89.5
      },
      "current_audit": {
        "date": "2025-12-26",
        "violations": 3,
        "warnings": 7,
        "score": 94.2
      },
      "improvement": true,
      "delta_violations": -2,
      "delta_warnings": -5,
      "delta_score": 4.7
    },
    "violation_frequency": {
      "80_hour": [
        {"date": "2025-10-26", "count": 2},
        {"date": "2025-11-26", "count": 3},
        {"date": "2025-12-26", "count": 1}
      ],
      "1_in_7": [
        {"date": "2025-10-26", "count": 1},
        {"date": "2025-11-26", "count": 0},
        {"date": "2025-12-26", "count": 1}
      ]
    },
    "high_risk_residents": [
      {
        "person_id": "PGY2-03",
        "violation_count_30d": 2,
        "warning_count_30d": 5,
        "trend": "worsening"
      }
    ]
  }
}
```

### 8. Recommendations

```json
{
  "recommendations": {
    "immediate_actions": [
      {
        "priority": "P0",
        "action": "Remove PGY2-03 from call on 2026-03-27 to prevent 80-hour violation",
        "affected_people": ["PGY2-03"],
        "deadline": "2026-03-27T00:00:00Z",
        "estimated_effort": "15 minutes",
        "swap_candidates": ["PGY2-01", "PGY2-04"]
      }
    ],
    "preventive_actions": [
      {
        "priority": "P1",
        "action": "Redistribute holiday coverage to avoid consecutive duty days",
        "affected_people": ["PGY3-01"],
        "timeframe": "Before next holiday",
        "estimated_effort": "30 minutes"
      }
    ],
    "policy_reviews": [
      {
        "priority": "P2",
        "issue": "Inpatient rotation consistently violates supervision ratio",
        "recommendation": "Add 1 additional faculty to inpatient pool or reduce resident assignments",
        "requires_approval": true
      }
    ]
  }
}
```

### 9. People-Level Summary

```json
{
  "people_summary": [
    {
      "person_id": "PGY2-03",
      "person_name": "Resident Name",
      "role": "RESIDENT",
      "pgy_level": "PGY-2",
      "compliance_status": "VIOLATION",
      "violations": [
        {"rule": "80_hour", "count": 1, "severity": "critical"}
      ],
      "warnings": [
        {"rule": "fairness", "count": 2, "severity": "warning"}
      ],
      "average_hours_per_week": 76.3,
      "max_hours_per_week": 82.5,
      "consecutive_duty_days": 6,
      "days_off_in_period": 4,
      "utilization": 0.87,
      "at_risk": true
    }
  ]
}
```

### 10. Rotation-Level Analysis

```json
{
  "rotation_analysis": [
    {
      "rotation": "inpatient",
      "total_assignments": 56,
      "violations": 3,
      "violation_rate": 5.4,
      "common_issues": [
        "supervision_ratio",
        "extended_shifts"
      ],
      "requires_review": true
    },
    {
      "rotation": "peds_clinic",
      "total_assignments": 28,
      "violations": 0,
      "violation_rate": 0.0,
      "compliant": true
    }
  ]
}
```

---

## Where to Store

### Audit Logs

**Location:** `.claude/History/compliance/audit_YYYY-MM-DD_HHMMSS.json`

**Naming:**
- ISO 8601 timestamp
- One file per audit
- Keep all audits indefinitely (regulatory requirement)

### Latest Audit

**Location:** `.claude/History/compliance/LATEST.json`

**Purpose:** Symlink to most recent audit

### Monthly Compliance Report

**Location:** `.claude/History/compliance/report_YYYY-MM.md`

**Purpose:** Human-readable summary for stakeholders

```markdown
# ACGME Compliance Report - December 2025

## Executive Summary
- **Overall Status:** COMPLIANT with minor violations
- **Compliance Score:** 94.2%
- **Total Audits:** 4
- **Trend:** Improving (+4.7 points from previous month)

## Violations Summary
- Critical: 1 (80-hour rule)
- Warnings: 7 (capacity warnings)

## Actions Taken
1. Redistributed call assignments for PGY2-03
2. Added faculty coverage for high-risk periods

## Recommendations
- Review inpatient rotation staffing model
- Implement predictive monitoring for 80-hour rule
```

### Compliance Dashboard Data

**Location:** `.claude/History/compliance/dashboard.json`

**Purpose:** Real-time dashboard metrics

```json
{
  "last_updated": "2025-12-26T15:00:00Z",
  "current_status": "COMPLIANT",
  "score": 94.2,
  "trend_7d": +1.2,
  "trend_30d": +4.7,
  "active_violations": 3,
  "at_risk_people": 2,
  "next_audit": "2026-01-26T15:00:00Z"
}
```

---

## Format Specification

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["audit_id", "timestamp", "compliance_summary", "recommendations"],
  "properties": {
    "audit_id": {"type": "string", "pattern": "^AUD-\\d{8}-\\d{3}$"},
    "timestamp": {"type": "string", "format": "date-time"},
    "compliance_summary": {"type": "object"},
    "80_hour_violations": {"type": "array"},
    "1_in_7_violations": {"type": "array"},
    "supervision_violations": {"type": "array"},
    "duty_period_violations": {"type": "array"},
    "trends": {"type": "object"},
    "recommendations": {"type": "object"}
  }
}
```

### Retention Policy

| Age | Action |
|-----|--------|
| All audits | **KEEP INDEFINITELY** (regulatory requirement) |
| Monthly reports | Keep all (accreditation documentation) |
| Dashboard data | Keep latest + 90 days history |

**CRITICAL:** Compliance audits are legal/regulatory documentation. Never delete.

---

## Trigger Conditions

Execute this hook when:

1. **Scheduled compliance audit runs** (daily/weekly/monthly)
2. **Manual audit requested** (pre-accreditation, investigation)
3. **Post-schedule-generation validation** (verify new schedule)
4. **Incident investigation** (violation reported)

**DO NOT trigger for:**
- Individual person compliance checks (too granular)
- Real-time monitoring alerts (use separate alerting)
- Validation during schedule generation (use post-schedule-generation hook)

---

## Integration with Skills

### ACGME Compliance Skill

After audit:
1. Collect all violation data
2. Calculate compliance score
3. Generate recommendations
4. Write audit log
5. Update dashboard data
6. Create monthly report (if month-end)
7. Send alerts for critical violations

### Schedule Verification Skill

Load latest audit to inform verification:
- Pre-populate known violations
- Highlight high-risk areas
- Show trend context

---

## Example Usage in Claude Session

```markdown
After running compliance audit:

1. Execute audit via MCP tool validate_acgme_compliance
2. Extract all violation categories
3. Calculate trends from previous audits
4. Generate recommendations
5. Write audit log:
   ```
   Write(.claude/History/compliance/audit_2025-12-26_150000.json, data)
   ```
6. Update dashboard:
   ```
   Write(.claude/History/compliance/dashboard.json, metrics)
   ```
7. Alert on critical violations:
   ```
   If critical_violations > 0:
       Print high-priority recommendations
       Notify program director
   ```
```

---

## Checklist

After compliance audit:

- [ ] Audit log created with all sections
- [ ] All ACGME rules checked
- [ ] Violations categorized by severity
- [ ] Trend comparison with previous audits
- [ ] People-level summary generated
- [ ] Rotation-level analysis completed
- [ ] Recommendations prioritized
- [ ] LATEST.json updated
- [ ] Dashboard metrics updated
- [ ] Monthly report created (if applicable)
- [ ] Critical violations alerted

---

## Regulatory Compliance Notes

### ACGME Documentation Requirements

Per ACGME Common Program Requirements:
- Programs must maintain documentation of duty hours
- Programs must monitor and address violations
- Programs must have action plans for systemic issues

**This hook satisfies:**
- ✓ Documentation of compliance checks
- ✓ Violation monitoring and tracking
- ✓ Action plan generation (recommendations)

### Accreditation Preparation

During site visits, auditors may request:
- Historical violation trends → `compliance/audit_*.json`
- Action plans for violations → `recommendations` sections
- Proof of monitoring → Audit frequency and completeness

**All data in History/compliance/ directory is accreditation-ready.**

---

## Analytics Use Cases

This data enables:

1. **Predictive Compliance**
   - Which residents are at risk of future violations?
   - Which rotations need staffing adjustments?

2. **Program Evaluation**
   - Is compliance improving over time?
   - Are policy changes effective?

3. **Resource Planning**
   - Do we need more faculty for supervision?
   - Should we adjust rotation capacity?

4. **Benchmarking**
   - How do we compare to ACGME national averages?
   - Which areas are we excelling/struggling?

---

## Related Documentation

- `.claude/Hooks/post-schedule-generation.md` - Validation after generation
- `.claude/skills/acgme-compliance/SKILL.md` - Compliance checking procedures
- `docs/architecture/ACGME_RULES.md` - Detailed rule specifications
- `backend/app/scheduling/acgme_validator.py` - Validation implementation
