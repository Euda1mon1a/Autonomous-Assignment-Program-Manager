# Post-Swap Execution Hook

**Trigger:** After any swap request is executed or rolled back

## Purpose

Capture swap transaction data for:
- Audit trail compliance
- Swap pattern analysis
- Fairness monitoring
- Constraint validation history
- Rollback capability

---

## What to Capture

### 1. Swap Transaction Record

**File:** `History/swaps/swap_YYYY-MM-DD_HHMMSS_<swap-id>.json`

```json
{
  "swap_id": "SWP-20251226-001",
  "timestamp": "2025-12-26T14:45:00Z",
  "operation": "execute|rollback",
  "user": "FAC-001",
  "status": "success|failed|partial",
  "duration_ms": 234
}
```

### 2. Swap Details

```json
{
  "swap_type": "one_to_one|absorb|chain",
  "initiator": {
    "person_id": "FAC-001",
    "name": "Dr. Smith",
    "role": "Faculty"
  },
  "participants": [
    {
      "person_id": "FAC-002",
      "name": "Dr. Jones",
      "role": "Faculty",
      "action": "giving|receiving"
    }
  ],
  "assignments": {
    "before": [
      {
        "assignment_id": "ASG-12345",
        "person_id": "FAC-001",
        "date": "2026-03-15",
        "session": "AM",
        "rotation": "peds_clinic"
      }
    ],
    "after": [
      {
        "assignment_id": "ASG-12345",
        "person_id": "FAC-002",
        "date": "2026-03-15",
        "session": "AM",
        "rotation": "peds_clinic"
      }
    ]
  }
}
```

### 3. Validation Results

```json
{
  "validation": {
    "pre_swap_validation": {
      "timestamp": "2025-12-26T14:44:58Z",
      "passed": true,
      "checks": [
        {
          "check": "credential_match",
          "passed": true,
          "details": "Both faculty have peds clinic credentials"
        },
        {
          "check": "acgme_80_hour",
          "passed": true,
          "fac_001_hours": 62.5,
          "fac_002_hours": 58.0,
          "post_swap_fac_001": 60.0,
          "post_swap_fac_002": 61.5
        },
        {
          "check": "supervision_ratio",
          "passed": true,
          "ratio_maintained": "3:1"
        }
      ]
    },
    "post_swap_validation": {
      "timestamp": "2025-12-26T14:45:00Z",
      "passed": true,
      "new_violations": 0,
      "resolved_violations": 1,
      "details": "Swap resolved workload imbalance for FAC-001"
    }
  }
}
```

### 4. Constraint Impact

```json
{
  "constraint_impact": {
    "affected_constraints": [
      {
        "constraint": "fairness_gini",
        "before": 0.15,
        "after": 0.12,
        "improvement": true,
        "delta": -0.03
      },
      {
        "constraint": "weekend_distribution",
        "before": {
          "fac_001": 4,
          "fac_002": 3
        },
        "after": {
          "fac_001": 3,
          "fac_002": 4
        },
        "balanced": true
      }
    ],
    "ripple_effects": [
      {
        "affected_person": "PGY2-03",
        "reason": "Supervision ratio recalculated",
        "impact": "none",
        "action_required": false
      }
    ]
  }
}
```

### 5. Resilience Impact

```json
{
  "resilience_impact": {
    "utilization_change": {
      "fac_001": {
        "before": 0.85,
        "after": 0.78,
        "within_threshold": true
      },
      "fac_002": {
        "before": 0.72,
        "after": 0.79,
        "within_threshold": true
      }
    },
    "n1_compliance": {
      "before": true,
      "after": true,
      "change": "none"
    },
    "critical_personnel_change": {
      "fac_001": {
        "before_criticality": 7.5,
        "after_criticality": 6.8,
        "still_critical": true
      }
    },
    "defense_level": {
      "before": "YELLOW",
      "after": "GREEN",
      "improved": true
    }
  }
}
```

### 6. Audit Trail

```json
{
  "audit": {
    "request_date": "2025-12-20T10:00:00Z",
    "approval_date": "2025-12-21T15:30:00Z",
    "approved_by": "admin",
    "execution_date": "2025-12-26T14:45:00Z",
    "executed_by": "system",
    "reason": "Personal conflict - family event",
    "auto_matched": false,
    "rollback_deadline": "2025-12-27T14:45:00Z",
    "rollback_available": true,
    "notification_sent": true,
    "notification_recipients": [
      "FAC-001",
      "FAC-002",
      "admin@example.com"
    ]
  }
}
```

### 7. Database Changes

```json
{
  "database": {
    "backup_created": true,
    "backup_file": "backups/postgres/pre_swap_SWP-20251226-001.sql.gz",
    "tables_modified": ["assignments", "swap_requests"],
    "rows_updated": 2,
    "rows_inserted": 1,
    "rows_deleted": 0,
    "transaction_id": "txn_1234567890",
    "committed": true
  }
}
```

### 8. Rollback Data (If Applicable)

For rollback operations:

```json
{
  "rollback": {
    "original_swap_id": "SWP-20251226-001",
    "rollback_reason": "Requester changed mind",
    "rollback_user": "FAC-001",
    "within_window": true,
    "hours_elapsed": 18.5,
    "deadline_hours": 24,
    "restoration_successful": true,
    "assignments_restored": 2,
    "notifications_sent": true
  }
}
```

---

## Where to Store

### Individual Swap Logs

**Location:** `.claude/History/swaps/swap_YYYY-MM-DD_HHMMSS_<swap-id>.json`

**Naming:**
- ISO 8601 timestamp
- Include swap ID for traceability
- Separate file per swap operation

### Swap Index

**Location:** `.claude/History/swaps/INDEX.json`

**Purpose:** Quick lookup of all swaps

```json
{
  "swaps": [
    {
      "swap_id": "SWP-20251226-001",
      "date": "2025-12-26",
      "type": "one_to_one",
      "status": "completed",
      "rolled_back": false,
      "file": "swap_2025-12-26_144500_SWP-20251226-001.json"
    }
  ],
  "total_swaps": 42,
  "successful_swaps": 40,
  "failed_swaps": 2,
  "rollbacks": 3
}
```

### Monthly Summary

**Location:** `.claude/History/swaps/summary_YYYY-MM.json`

**Purpose:** Aggregated statistics for reporting

```json
{
  "month": "2025-12",
  "total_swaps": 12,
  "swap_types": {
    "one_to_one": 10,
    "absorb": 2,
    "chain": 0
  },
  "success_rate": 91.7,
  "average_processing_time_ms": 245,
  "rollback_rate": 8.3,
  "top_requesters": [
    {"person_id": "FAC-001", "count": 3},
    {"person_id": "FAC-005", "count": 2}
  ],
  "fairness_improvement": 0.04,
  "constraint_violations_resolved": 5
}
```

---

## Format Specification

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["swap_id", "timestamp", "operation", "status", "swap_type", "validation"],
  "properties": {
    "swap_id": {"type": "string", "pattern": "^SWP-\\d{8}-\\d{3}$"},
    "timestamp": {"type": "string", "format": "date-time"},
    "operation": {"type": "string", "enum": ["execute", "rollback"]},
    "status": {"type": "string", "enum": ["success", "failed", "partial"]},
    "swap_type": {"type": "string", "enum": ["one_to_one", "absorb", "chain"]},
    "validation": {"type": "object"},
    "constraint_impact": {"type": "object"},
    "resilience_impact": {"type": "object"},
    "audit": {"type": "object"}
  }
}
```

### Retention Policy

| Age | Action |
|-----|--------|
| < 90 days | Keep all (rollback window + audit trail) |
| 90-365 days | Keep all (annual compliance reporting) |
| 1-3 years | Keep if significant (violations resolved) |
| > 3 years | Aggregate monthly summaries only |

---

## Trigger Conditions

Execute this hook when:

1. **Swap executed successfully**
2. **Swap execution failed** (capture failure reason)
3. **Swap rolled back**
4. **Chain swap completed** (log entire chain)

**DO NOT trigger for:**
- Swap request creation (not execution)
- Swap candidate analysis (read-only)
- Swap approval (separate audit)

---

## Integration with Skills

### Swap Management Skill

After swap execution:
1. Capture before/after state
2. Run constraint validation
3. Calculate resilience impact
4. Write swap log
5. Update INDEX.json
6. Send notifications

### Resilience Monitoring

After swap:
1. Recalculate utilization for affected people
2. Re-run N-1 analysis if critical personnel affected
3. Update defense level if thresholds crossed
4. Alert if new single point of failure created

---

## Example Usage in Claude Session

```markdown
After executing swap SWP-20251226-001:

1. Extract swap details from request and response
2. Run post-swap validation
3. Calculate fairness delta
4. Write swap log:
   ```
   Write(.claude/History/swaps/swap_2025-12-26_144500_SWP-20251226-001.json, data)
   ```
5. Update INDEX.json:
   ```
   Edit(.claude/History/swaps/INDEX.json, append_swap_entry)
   ```
6. Notify participants:
   ```
   Tool: send_notification
   Recipients: [FAC-001, FAC-002]
   ```
```

---

## Checklist

After swap execution:

- [ ] Swap log created with all sections
- [ ] Before/after state captured
- [ ] Validation results recorded
- [ ] Constraint impact assessed
- [ ] Resilience metrics recalculated
- [ ] Audit trail complete
- [ ] Database backup verified
- [ ] INDEX.json updated
- [ ] Monthly summary incremented
- [ ] Notifications sent
- [ ] Rollback deadline set (if applicable)

---

## Analytics Use Cases

This data enables:

1. **Swap Pattern Analysis**
   - Who swaps most frequently?
   - Which rotations have highest swap rate?
   - Time-of-year patterns?

2. **Fairness Monitoring**
   - Are swaps improving or degrading fairness?
   - Is swap access equitable?

3. **Constraint Impact**
   - Do swaps resolve or create violations?
   - Which constraints are most affected?

4. **System Health**
   - Swap success rate trending
   - Processing time trends
   - Rollback rate patterns

---

## Related Documentation

- `.claude/Hooks/post-schedule-generation.md` - For generation logging
- `.claude/Methodologies/surgical-swaps.md` - Minimal-impact swaps
- `.claude/skills/swap-management/SKILL.md` - Swap procedures
- `docs/architecture/SWAP_WORKFLOW.md` - Swap system design
