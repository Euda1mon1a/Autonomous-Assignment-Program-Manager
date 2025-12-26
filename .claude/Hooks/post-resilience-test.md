# Post-Resilience Test Hook

**Trigger:** After resilience health checks or contingency analysis completes

## Purpose

Record resilience test results for:
- System health monitoring
- Vulnerability identification
- Capacity planning
- Recovery time estimation
- Defense-in-depth validation

---

## What to Capture

### 1. Test Metadata

**File:** `History/resilience/test_YYYY-MM-DD_HHMMSS.json`

```json
{
  "test_id": "RES-20251226-001",
  "timestamp": "2025-12-26T16:00:00Z",
  "test_type": "health_check|n1_analysis|n2_analysis|hub_centrality|utilization",
  "user": "admin",
  "schedule_id": "current",
  "duration_seconds": 3.2
}
```

### 2. Overall Resilience Health Score

```json
{
  "health_summary": {
    "overall_score": 7.2,
    "max_score": 10.0,
    "status": "GREEN|YELLOW|ORANGE|RED|BLACK",
    "defense_level": "GREEN",
    "timestamp": "2025-12-26T16:00:00Z",
    "trend": "stable|improving|degrading",
    "previous_score": 6.8,
    "delta": 0.4
  }
}
```

### 3. Defense-in-Depth Levels

```json
{
  "defense_levels": {
    "current_level": "GREEN",
    "level_details": {
      "GREEN": {
        "active": true,
        "criteria": [
          "utilization < 80%",
          "n1_compliant = true",
          "coverage_rate > 90%"
        ],
        "all_met": true
      },
      "YELLOW": {
        "active": false,
        "criteria": [
          "utilization 80-85%",
          "n1_compliant = false",
          "coverage_rate 85-90%"
        ],
        "triggers": []
      },
      "ORANGE": {
        "active": false,
        "criteria": [
          "utilization 85-90%",
          "n2_compliant = false"
        ],
        "triggers": []
      },
      "RED": {
        "active": false,
        "criteria": ["utilization > 90%"],
        "triggers": []
      },
      "BLACK": {
        "active": false,
        "criteria": ["system_failure"],
        "triggers": []
      }
    },
    "escalation_triggers": [],
    "time_at_current_level": "48 hours"
  }
}
```

### 4. N-1 Contingency Results

```json
{
  "n1_analysis": {
    "compliant": true,
    "total_scenarios_tested": 27,
    "failures": [
      {
        "person_id": "FAC-PD",
        "person_name": "Program Director",
        "role": "Faculty",
        "impact": "critical",
        "affected_rotations": ["procedures_full_day"],
        "affected_dates": ["2026-03-15", "2026-03-22"],
        "coverage_loss": 2,
        "no_backup": true,
        "reason": "Only faculty with advanced procedures certification"
      }
    ],
    "warnings": [
      {
        "person_id": "PGY3-02",
        "impact": "moderate",
        "affected_rotations": ["peds_clinic"],
        "backup_available": true,
        "backup_person": "PGY3-04",
        "backup_utilization_increase": 0.15,
        "marginal": true
      }
    ],
    "robust_areas": [
      {
        "rotation": "inpatient",
        "redundancy_level": 4,
        "can_handle_2_absences": true
      }
    ]
  }
}
```

### 5. N-2 Contingency Results

```json
{
  "n2_analysis": {
    "compliant": false,
    "total_scenarios_tested": 351,
    "critical_pairs": [
      {
        "person_1": "FAC-001",
        "person_2": "FAC-003",
        "impact": "catastrophic",
        "affected_rotations": ["procedures_half_day", "peds_clinic"],
        "coverage_loss": 8,
        "recovery_impossible": true,
        "reason": "Only two faculty with dual certification"
      }
    ],
    "degraded_pairs": [
      {
        "person_1": "PGY2-01",
        "person_2": "PGY2-03",
        "impact": "moderate",
        "affected_rotations": ["inpatient"],
        "coverage_loss": 4,
        "recovery_possible": true,
        "recovery_time_hours": 24,
        "requires_overtime": true
      }
    ],
    "mitigation_recommendations": [
      {
        "issue": "Dual absence of procedures-certified faculty",
        "recommendation": "Cross-train FAC-005 in advanced procedures",
        "estimated_time": "6 months",
        "priority": "P0"
      }
    ]
  }
}
```

### 6. Critical Personnel Identification

```json
{
  "critical_personnel": [
    {
      "person_id": "FAC-PD",
      "person_name": "Program Director",
      "role": "Faculty",
      "criticality_score": 8.5,
      "max_score": 10.0,
      "single_point_of_failure": true,
      "reasons": [
        "Only provider for procedures_full_day",
        "Highest number of unique certifications",
        "No backup with equivalent credentials"
      ],
      "unique_rotations": ["procedures_full_day"],
      "assignments_count": 12,
      "absence_impact": "Cannot cover 12 blocks without overtime",
      "mitigation": {
        "cross_train": "FAC-002",
        "estimated_time": "3 months",
        "cost": "High"
      }
    },
    {
      "person_id": "PGY3-02",
      "criticality_score": 6.2,
      "single_point_of_failure": false,
      "backup_available": true,
      "backup_person": "PGY3-04",
      "backup_capacity_margin": "tight"
    }
  ],
  "total_spof": 1,
  "total_critical": 5,
  "total_marginal": 8
}
```

### 7. Utilization Threshold Analysis

```json
{
  "utilization_analysis": {
    "threshold": 0.80,
    "system_average": 0.73,
    "within_threshold": true,
    "violations": [
      {
        "person_id": "PGY2-05",
        "utilization": 0.87,
        "threshold": 0.80,
        "overage": 0.07,
        "severity": "warning",
        "burnout_risk": "elevated",
        "assignments_count": 26,
        "recommended_assignments": 24
      }
    ],
    "at_capacity": [
      {
        "person_id": "FAC-002",
        "utilization": 0.79,
        "threshold": 0.80,
        "margin": 0.01,
        "status": "marginal",
        "can_absorb_swap": false
      }
    ],
    "under_utilized": [
      {
        "person_id": "PGY1-04",
        "utilization": 0.52,
        "threshold": 0.80,
        "margin": 0.28,
        "status": "available",
        "can_absorb": 8
      }
    ]
  }
}
```

### 8. Homeostasis Metrics

```json
{
  "homeostasis": {
    "score": 7.2,
    "max_score": 10.0,
    "status": "stable",
    "feedback_loops": [
      {
        "loop": "workload_balance",
        "status": "active",
        "stabilizing": true,
        "gini_coefficient": 0.12,
        "target": 0.15,
        "within_tolerance": true
      },
      {
        "loop": "coverage_adjustment",
        "status": "active",
        "stabilizing": true,
        "coverage_rate": 96.4,
        "target": 95.0,
        "within_tolerance": true
      }
    ],
    "perturbations": [
      {
        "event": "Holiday coverage 2025-12-25",
        "impact": "moderate",
        "recovery_time_hours": 18,
        "system_restored": true
      }
    ],
    "resilience_factors": {
      "diversity": 0.82,
      "redundancy": 0.75,
      "modularity": 0.68,
      "feedback_strength": 0.91
    }
  }
}
```

### 9. Hub Centrality Analysis

```json
{
  "hub_centrality": {
    "network_stats": {
      "total_nodes": 27,
      "total_edges": 156,
      "average_degree": 5.78,
      "clustering_coefficient": 0.42,
      "diameter": 4
    },
    "hub_rankings": [
      {
        "person_id": "FAC-PD",
        "centrality_score": 0.85,
        "degree": 12,
        "betweenness": 0.32,
        "closeness": 0.78,
        "eigenvector": 0.91,
        "hub_type": "super_hub",
        "removal_impact": "catastrophic"
      },
      {
        "person_id": "FAC-002",
        "centrality_score": 0.62,
        "hub_type": "major_hub",
        "removal_impact": "severe"
      }
    ],
    "network_vulnerability": {
      "robustness_coefficient": 0.68,
      "attack_tolerance": "moderate",
      "failure_tolerance": "high",
      "critical_threshold": 3
    }
  }
}
```

### 10. Recovery Time Estimates

```json
{
  "recovery_estimates": {
    "scenarios": [
      {
        "scenario": "Single faculty absence (non-critical)",
        "estimated_recovery_time_hours": 4,
        "recovery_method": "Automatic swap matching",
        "manual_intervention_required": false
      },
      {
        "scenario": "Single faculty absence (critical - FAC-PD)",
        "estimated_recovery_time_hours": 48,
        "recovery_method": "Manual reassignment + overtime",
        "manual_intervention_required": true,
        "requires_approval": true
      },
      {
        "scenario": "Dual faculty absence (critical pair)",
        "estimated_recovery_time_hours": 120,
        "recovery_method": "Schedule regeneration + policy exception",
        "manual_intervention_required": true,
        "requires_approval": true,
        "success_probability": 0.6
      },
      {
        "scenario": "Mass absence (pandemic, deployment)",
        "estimated_recovery_time_hours": 336,
        "recovery_method": "Activate static fallback schedule",
        "manual_intervention_required": true,
        "requires_policy_change": true,
        "success_probability": 0.4
      }
    ],
    "rto_compliance": {
      "target_rto_hours": 24,
      "scenarios_meeting_rto": 2,
      "scenarios_exceeding_rto": 2,
      "rto_compliance_rate": 50.0
    }
  }
}
```

### 11. Mitigation Recommendations

```json
{
  "recommendations": {
    "immediate": [
      {
        "priority": "P0",
        "issue": "FAC-PD is single point of failure for procedures",
        "action": "Restrict FAC-PD procedures assignments to 75% capacity",
        "rationale": "Build buffer for absence coverage",
        "impact": "Reduced single-day failure risk",
        "deadline": "Next schedule generation"
      }
    ],
    "short_term": [
      {
        "priority": "P1",
        "issue": "PGY2-05 exceeds 80% utilization threshold",
        "action": "Reduce assignments by 2 blocks",
        "rationale": "Prevent burnout, maintain surge capacity",
        "impact": "Improved N-1 resilience",
        "deadline": "Within 7 days"
      }
    ],
    "long_term": [
      {
        "priority": "P2",
        "issue": "Lack of backup for advanced procedures",
        "action": "Cross-train FAC-002 or FAC-005 in procedures",
        "rationale": "Eliminate single point of failure",
        "impact": "N-1 compliance for procedures rotation",
        "estimated_time": "3-6 months",
        "cost": "Training + certification fees"
      }
    ],
    "policy_changes": [
      {
        "priority": "P3",
        "issue": "No static fallback schedules defined",
        "action": "Create and maintain pre-computed fallback schedules",
        "rationale": "Enable fast recovery from mass absence events",
        "impact": "Reduced RTO for catastrophic scenarios",
        "effort": "High - ongoing maintenance"
      }
    ]
  }
}
```

---

## Where to Store

### Resilience Test Logs

**Location:** `.claude/History/resilience/test_YYYY-MM-DD_HHMMSS.json`

**Naming:**
- ISO 8601 timestamp
- One file per test run
- Keep all tests for trending

### Latest Test

**Location:** `.claude/History/resilience/LATEST.json`

**Purpose:** Quick access to current resilience state

### Resilience Dashboard

**Location:** `.claude/History/resilience/dashboard.json`

**Purpose:** Real-time monitoring metrics

```json
{
  "last_updated": "2025-12-26T16:00:00Z",
  "health_score": 7.2,
  "defense_level": "GREEN",
  "n1_compliant": true,
  "n2_compliant": false,
  "critical_personnel_count": 1,
  "utilization_violations": 1,
  "trend_7d": "stable",
  "trend_30d": "improving"
}
```

### Monthly Resilience Report

**Location:** `.claude/History/resilience/report_YYYY-MM.md`

**Purpose:** Executive summary for stakeholders

---

## Format Specification

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["test_id", "timestamp", "test_type", "health_summary"],
  "properties": {
    "test_id": {"type": "string", "pattern": "^RES-\\d{8}-\\d{3}$"},
    "timestamp": {"type": "string", "format": "date-time"},
    "test_type": {"type": "string"},
    "health_summary": {"type": "object"},
    "defense_levels": {"type": "object"},
    "n1_analysis": {"type": "object"},
    "n2_analysis": {"type": "object"},
    "critical_personnel": {"type": "array"},
    "recommendations": {"type": "object"}
  }
}
```

### Retention Policy

| Age | Action |
|-----|--------|
| < 90 days | Keep all |
| 90-365 days | Keep all (trend analysis) |
| 1-3 years | Keep monthly samples |
| > 3 years | Aggregate statistics only |

---

## Trigger Conditions

Execute this hook when:

1. **Scheduled resilience health check** (daily/weekly)
2. **After schedule generation** (verify new schedule resilience)
3. **After major changes** (personnel changes, rotation updates)
4. **Manual resilience test requested**
5. **Defense level escalation** (automatic on threshold crossing)

**DO NOT trigger for:**
- Individual utilization checks (too frequent)
- Swap candidate analysis (separate concern)

---

## Integration with Skills

### Resilience Framework

After test:
1. Run all resilience checks (health, N-1, N-2, centrality, utilization)
2. Calculate defense level
3. Identify critical personnel
4. Generate recommendations
5. Write test log
6. Update dashboard
7. Alert on escalations

### Production Incident Responder

Load latest resilience test during incidents:
- Identify available backup personnel
- Estimate recovery time for scenario
- Suggest mitigation actions

---

## Example Usage in Claude Session

```markdown
After running resilience test:

1. Execute resilience checks via MCP tools
2. Aggregate results from all tools
3. Calculate overall health score
4. Identify critical issues
5. Write test log:
   ```
   Write(.claude/History/resilience/test_2025-12-26_160000.json, data)
   ```
6. Update dashboard:
   ```
   Write(.claude/History/resilience/dashboard.json, metrics)
   ```
7. Alert on critical findings:
   ```
   If defense_level in [RED, BLACK]:
       Trigger incident response
   If single_points_of_failure > 0:
       Alert program director
   ```
```

---

## Checklist

After resilience test:

- [ ] Test log created with all sections
- [ ] Health score calculated
- [ ] Defense level determined
- [ ] N-1 analysis completed
- [ ] N-2 analysis completed (if applicable)
- [ ] Critical personnel identified
- [ ] Utilization thresholds checked
- [ ] Hub centrality calculated
- [ ] Recovery time estimated
- [ ] Recommendations prioritized
- [ ] LATEST.json updated
- [ ] Dashboard metrics updated
- [ ] Critical issues alerted

---

## Analytics Use Cases

This data enables:

1. **Predictive Resilience**
   - Is system resilience improving or degrading?
   - Are mitigations effective?

2. **Capacity Planning**
   - Do we need additional faculty?
   - Which certifications are bottlenecks?

3. **Risk Management**
   - What are our top vulnerabilities?
   - How fast can we recover from incidents?

4. **Policy Optimization**
   - Is 80% utilization threshold appropriate?
   - Should we maintain static fallbacks?

---

## Related Documentation

- `.claude/Methodologies/resilience-thinking.md` - Resilience design patterns
- `docs/architecture/cross-disciplinary-resilience.md` - Framework concepts
- `backend/app/resilience/` - Resilience implementation
- `.claude/skills/production-incident-responder/SKILL.md` - Incident response
