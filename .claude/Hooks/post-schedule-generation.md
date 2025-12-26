# Post-Schedule Generation Hook

**Trigger:** After any schedule generation operation completes

## Purpose

Capture comprehensive data about schedule generation for:
- Historical analysis and trending
- Debugging failed generations
- Optimization tuning
- Compliance auditing
- Knowledge transfer

---

## What to Capture

### 1. Generation Metadata

**File:** `History/scheduling/generation_YYYY-MM-DD_HHMMSS.json`

```json
{
  "timestamp": "2025-12-26T14:30:00Z",
  "operation": "schedule_generation",
  "user": "admin",
  "branch": "main",
  "git_commit": "1020de3a",
  "duration_seconds": 45.2,
  "status": "success|failed|partial"
}
```

### 2. Input Parameters

```json
{
  "input": {
    "start_date": "2026-03-12",
    "end_date": "2026-04-08",
    "algorithm": "cp_sat",
    "timeout_seconds": 120,
    "num_residents": 15,
    "num_faculty": 12,
    "num_blocks": 56,
    "constraints_enabled": [
      "acgme_80_hour",
      "acgme_1_in_7",
      "supervision_ratio",
      "rotation_coverage",
      "fmit_requirements"
    ]
  }
}
```

### 3. Constraint Check Results

**Critical:** Log ALL constraint evaluations, not just violations

```json
{
  "constraints": {
    "hard_constraints": [
      {
        "name": "acgme_80_hour_rule",
        "checked": 15,
        "passed": 14,
        "failed": 1,
        "failures": [
          {
            "person": "PGY2-03",
            "week_start": "2026-03-20",
            "hours": 82.5,
            "limit": 80.0
          }
        ]
      },
      {
        "name": "supervision_ratio",
        "checked": 56,
        "passed": 56,
        "failed": 0
      }
    ],
    "soft_constraints": [
      {
        "name": "preference_satisfaction",
        "weight": 5,
        "score": 87.3,
        "penalty": 63.5
      },
      {
        "name": "fairness_gini",
        "weight": 3,
        "score": 0.12,
        "penalty": 36.0
      }
    ]
  }
}
```

### 4. Solver Statistics

**For CP-SAT solver:**

```json
{
  "solver": {
    "algorithm": "cp_sat",
    "status": "OPTIMAL|FEASIBLE|INFEASIBLE|TIMEOUT",
    "objective_value": 1234.5,
    "best_bound": 1200.0,
    "gap": 2.9,
    "num_branches": 45678,
    "num_conflicts": 1234,
    "wall_time": 45.2,
    "search_depth": 128,
    "memory_used_mb": 256
  }
}
```

### 5. Violations and Trade-offs

```json
{
  "validation": {
    "total_violations": 3,
    "critical_violations": 1,
    "warnings": 7,
    "violations_by_category": {
      "acgme_80_hour": 1,
      "acgme_1_in_7": 0,
      "supervision_ratio": 0,
      "coverage_gaps": 2
    },
    "trade_offs_made": [
      {
        "constraint": "weekend_preference",
        "relaxed_for": "coverage_requirement",
        "impact": "3 residents assigned non-preferred weekends"
      }
    ]
  }
}
```

### 6. Coverage Analysis

```json
{
  "coverage": {
    "total_blocks": 56,
    "assigned_blocks": 54,
    "coverage_rate": 96.4,
    "gaps": [
      {
        "date": "2026-03-15",
        "session": "PM",
        "rotation": "peds_clinic",
        "reason": "No available PGY-3 with peds certification"
      }
    ],
    "over_staffed": [
      {
        "date": "2026-03-20",
        "session": "AM",
        "rotation": "inpatient",
        "assigned": 4,
        "required": 3
      }
    ]
  }
}
```

### 7. Resilience Metrics

```json
{
  "resilience": {
    "n1_compliant": true,
    "n2_compliant": false,
    "critical_personnel": [
      {
        "person": "FAC-PD",
        "criticality_score": 8.5,
        "single_point_of_failure": true,
        "rotations": ["procedures_full_day"]
      }
    ],
    "utilization_threshold_violations": [
      {
        "person": "PGY2-05",
        "utilization": 0.87,
        "threshold": 0.80
      }
    ],
    "defense_level": "YELLOW",
    "homeostasis_score": 7.2
  }
}
```

### 8. Backup Verification

```json
{
  "backup": {
    "created": true,
    "timestamp": "2025-12-26T14:25:00Z",
    "file": "backups/postgres/residency_scheduler_20251226_142500.sql.gz",
    "size_mb": 12.4,
    "verified": true,
    "tables_backed_up": ["assignments", "people", "rotations", "absences"]
  }
}
```

---

## Where to Store

### Primary Log File

**Location:** `.claude/History/scheduling/generation_YYYY-MM-DD_HHMMSS.json`

**Naming:**
- Use ISO 8601 timestamp
- Include operation type in filename
- Keep all generations for trending

### Summary File

**Location:** `.claude/History/scheduling/LATEST.json`

**Purpose:** Symlink or copy of most recent generation for quick reference

### Session Documentation

**Location:** `docs/sessions/SESSION_YYYY-MM-DD_SCHEDULE_GENERATION.md`

**Purpose:** Human-readable summary with:
- Problem statement (why generation was needed)
- Configuration choices made
- Results interpretation
- Lessons learned

---

## Format Specification

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["timestamp", "operation", "status", "input", "solver", "validation"],
  "properties": {
    "timestamp": {"type": "string", "format": "date-time"},
    "operation": {"type": "string", "enum": ["schedule_generation", "bulk_assign", "regeneration"]},
    "status": {"type": "string", "enum": ["success", "failed", "partial", "timeout"]},
    "duration_seconds": {"type": "number", "minimum": 0},
    "input": {"type": "object"},
    "solver": {"type": "object"},
    "constraints": {"type": "object"},
    "validation": {"type": "object"},
    "coverage": {"type": "object"},
    "resilience": {"type": "object"},
    "backup": {"type": "object"}
  }
}
```

### Retention Policy

| Age | Action |
|-----|--------|
| < 30 days | Keep all |
| 30-90 days | Keep if significant (>5 violations or failed) |
| 90-365 days | Monthly samples only |
| > 365 days | Aggregate statistics only |

---

## Trigger Conditions

Execute this hook when:

1. **Schedule generation completes** (success or failure)
2. **Bulk assignment operation finishes**
3. **Schedule regeneration requested**
4. **Manual constraint override applied**

**DO NOT trigger for:**
- Read-only validation checks
- Swap executions (use post-swap-execution hook)
- Individual assignment changes

---

## Integration with Skills

### Safe Schedule Generation Skill

After generation:
1. Extract solver statistics from response
2. Run validation via `validate_acgme_compliance`
3. Calculate resilience metrics
4. Write JSON log file
5. Create human-readable summary
6. Update LATEST.json symlink

### Schedule Verification Skill

Load latest generation log to populate checklist:
- Pre-fill known violations
- Highlight critical personnel
- Show coverage gaps
- Display trade-offs made

---

## Example Usage in Claude Session

```markdown
After successful schedule generation:

1. Extract data from API response
2. Calculate additional metrics (Gini, utilization)
3. Write JSON log:
   ```
   Write(.claude/History/scheduling/generation_2025-12-26_143000.json, data)
   ```
4. Create session summary:
   ```
   Write(docs/sessions/SESSION_2025-12-26_BLOCK_10_GENERATION.md, summary)
   ```
5. Notify user of violations requiring attention
```

---

## Checklist

After schedule generation:

- [ ] JSON log created with all sections
- [ ] Backup verification logged
- [ ] Constraints evaluation captured
- [ ] Solver statistics recorded
- [ ] Violations documented
- [ ] Resilience metrics calculated
- [ ] Coverage analysis completed
- [ ] LATEST.json updated
- [ ] Session summary created (if significant)
- [ ] User notified of critical issues

---

## Related Documentation

- `.claude/Hooks/post-compliance-audit.md` - For audit-specific logging
- `.claude/Methodologies/constraint-propagation.md` - Understanding constraint flow
- `docs/architecture/SOLVER_ALGORITHM.md` - Solver internals
- `.claude/skills/safe-schedule-generation/SKILL.md` - Generation procedures
