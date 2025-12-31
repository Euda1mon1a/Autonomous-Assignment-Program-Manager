# Workflow: Compliance Check

**Purpose**: Analyze existing schedule for ACGME violations and regulatory compliance
**Safety**: TIER 1 (read-only analysis)
**Execution Time**: 2-3 seconds
**Frequency**: Daily or on-demand
**Operator**: Coordinator, AI (autonomous)

---

## Workflow Overview

This workflow validates a schedule against all ACGME regulations and operational constraints without any schedule modifications. It's safe for autonomous execution and provides detailed violation diagnostics.

```
Input: Schedule Date Range
  │
  ├─→ Phase 1: Core Compliance Check (2 tools, parallel)
  │     ├─ 80-Hour Rule validation
  │     ├─ 1-in-7 Rest Rule validation
  │     └─ Supervision Ratio validation
  │
  ├─→ Phase 2: Detailed Constraint Analysis (3 tools, parallel)
  │     ├─ Conflict Detection (6 conflict types)
  │     ├─ Advanced Constraint Validation
  │     └─ Work Hour Trend Analysis
  │
  ├─→ Phase 3: Advanced Compliance (4 tools, parallel)
  │     ├─ SPC Control Chart Analysis
  │     ├─ Process Capability Assessment
  │     ├─ Equity Metrics (Gini coefficient)
  │     └─ Utilization Threshold Check
  │
  └─→ Phase 4: Synthesis & Reporting
        ├─ Aggregate all violations
        ├─ Rank by severity
        └─ Generate recommendations
```

---

## Phase 1: Core ACGME Compliance (0.5 seconds)

**Tools**:
- `validate_schedule` - Standard compliance checking
- `validate_schedule_by_id` - Advanced constraint validation

**Execution** (Parallel):
```python
phase_1_tasks = [
    validate_schedule(
        start_date=date_range.start,
        end_date=date_range.end,
        check_work_hours=True,
        check_supervision=True,
        check_rest_periods=True,
        check_consecutive_duty=True,
    ),
    validate_schedule_by_id(
        schedule_id=schedule_id,
        constraint_config="default",
        include_suggestions=True,
    ),
]
results_1 = await asyncio.gather(*phase_1_tasks)
```

**Output Structure**:
```json
{
  "80_hour_rule": {
    "compliant": true,
    "violations": 0,
    "worst_week": {
      "week": "2025-12-15:2025-12-22",
      "max_hours": 79.5,
      "person_id": "RES-001"
    }
  },
  "1_in_7_rest": {
    "compliant": true,
    "violations": 0,
    "violations_list": []
  },
  "supervision_ratio": {
    "compliant": true,
    "violations": 0,
    "avg_ratio": "1:2.5",
    "blocks_below_ratio": []
  },
  "constraint_issues": {
    "total": 2,
    "critical": 0,
    "warning": 2,
    "issues": [
      {
        "severity": "warning",
        "rule": "supervision",
        "message": "Block 2025-12-20-AM has 3 PGY-1 with 1.5 faculty"
      }
    ]
  }
}
```

**Phase 1 Interpretation**:

| Result | Interpretation | Action |
|--------|----------------|--------|
| All compliant | Schedule safe | Continue to Phase 2 |
| 1-2 warnings | Minor issues | Escalate to Phase 4 |
| 3+ warnings | Moderate issues | Request adjustment |
| Any critical | Major violation | Block deployment |

---

## Phase 2: Detailed Constraint Analysis (1 second)

**Tools** (Parallel execution):
- `detect_conflicts` - 6 conflict types
- `analyze_workload_trend` - Kalman filter smoothing
- `analyze_supply_demand_cycles` - Lotka-Volterra dynamics

**Execution**:
```python
phase_2_tasks = [
    detect_conflicts(
        schedule_id=schedule_id,
        conflict_types=None,  # All types
        include_resolved=False,
    ),
    analyze_workload_trend(
        schedule_id=schedule_id,
        method="kalman",
    ),
    analyze_supply_demand_cycles(
        date_range=[date_range.start, date_range.end],
    ),
]
results_2 = await asyncio.gather(*phase_2_tasks)
```

**Conflict Types Analysis**:

| Conflict Type | Severity | Interpretation |
|---------------|----------|----------------|
| `double_booking` | CRITICAL | Same person two places |
| `work_hour_violation` | CRITICAL | Exceeds 80-hour limit |
| `rest_period_violation` | CRITICAL | No day off in 7 days |
| `supervision_gap` | HIGH | Ratio not met |
| `leave_overlap` | MEDIUM | Assignment during leave |
| `credential_mismatch` | MEDIUM | Missing certifications |

**Conflict Detection Output**:
```json
{
  "conflicts_found": 3,
  "by_severity": {
    "critical": 0,
    "high": 1,
    "medium": 2
  },
  "conflicts": [
    {
      "id": "conflict-1",
      "type": "supervision_gap",
      "severity": "high",
      "blocks_affected": ["block-2025-12-18-AM"],
      "auto_resolution": {
        "available": true,
        "action": "Add faculty"
      }
    }
  ]
}
```

**Workload Trend Analysis**:
```json
{
  "trend": "stable",
  "drift_detected": false,
  "weekly_avg": 61.5,
  "trend_line": "flat",
  "forecast_30d": 62.0,
  "anomalies": 2,
  "anomaly_dates": ["2025-12-10", "2025-12-17"]
}
```

**Supply/Demand Cycles**:
```json
{
  "cycles_detected": 1,
  "primary_cycle": {
    "period": 14,  // days
    "amplitude": 5.2,
    "phase": 3.1
  },
  "equilibrium": {
    "supply": 8.5,
    "demand": 8.2,
    "ratio": 1.04,
    "status": "balanced"
  },
  "forecast": "stable"
}
```

---

## Phase 3: Advanced Compliance Analysis (0.5-1 second)

**Tools** (Parallel execution):
- `run_spc_analysis` - Western Electric Rules
- `calculate_process_capability` - Six Sigma metrics
- `calculate_equity_metrics` - Gini coefficient
- `check_utilization_threshold` - Queuing theory

**Execution**:
```python
phase_3_tasks = [
    run_spc_analysis(
        resident_ids="all",
        target_hours=60.0,
        sigma=5.0,
    ),
    calculate_process_capability(
        data=weekly_hours_all,
        lower_spec_limit=40.0,
        upper_spec_limit=80.0,
    ),
    calculate_equity_metrics(
        hours_per_provider=schedule_hours,
        target_gini=0.15,
    ),
    check_utilization_threshold(
        available_faculty=faculty_count,
        required_blocks=required_blocks,
    ),
]
results_3 = await asyncio.gather(*phase_3_tasks)
```

**SPC Analysis Results**:
```json
{
  "violations_detected": 1,
  "alerts": [
    {
      "rule": 4,
      "message": "8 consecutive points above centerline",
      "week_start": "2025-12-08",
      "severity": "warning"
    }
  ],
  "process_capability": {
    "cp": 1.45,
    "cpk": 1.32,
    "sigma_level": 4.0
  }
}
```

**Process Capability**:
```json
{
  "cp": 1.52,  // Potential (if centered)
  "cpk": 1.38,  // Actual (current centering)
  "interpretation": "CAPABLE",
  "sigma_level": 4.1,
  "estimated_defect_rate_ppm": 2600
}
```

**Equity Metrics**:
```json
{
  "gini_coefficient": 0.12,
  "is_equitable": true,
  "mean_hours": 62.3,
  "std_hours": 7.5,
  "coefficient_of_variation": 0.12,
  "most_overloaded": {
    "provider_id": "FAC-005",
    "hours": 72.5,
    "delta": 10.2
  },
  "most_underloaded": {
    "provider_id": "FAC-001",
    "hours": 48.0,
    "delta": -14.3
  }
}
```

**Utilization Check**:
```json
{
  "utilization_pct": 78.5,
  "level": "YELLOW",
  "status": "approaching_critical",
  "safe_threshold": 80.0,
  "margin": 1.5,
  "recommendations": [
    "Monitor daily for capacity",
    "Prepare contingency plans"
  ]
}
```

---

## Phase 4: Synthesis & Reporting (0.5 seconds)

**Goals**:
- Aggregate all violations
- Rank by severity and impact
- Generate actionable recommendations

**Aggregation Logic**:
```python
def synthesize_compliance_report(phase_results):
    """Aggregate phases 1-3 into unified report."""

    violations = []

    # Phase 1 ACGME rules
    violations.extend(phase_results[1]["acgme_violations"])

    # Phase 2 conflicts
    violations.extend(phase_results[2]["conflicts"])

    # Phase 3 advanced
    violations.extend(phase_results[3]["spc_violations"])
    violations.extend(phase_results[3]["equity_concerns"])
    violations.extend(phase_results[3]["utilization_warnings"])

    # Rank by severity
    violations.sort(key=lambda x: severity_score(x))

    return {
        "schedule_id": schedule_id,
        "date_range": date_range,
        "total_violations": len(violations),
        "by_severity": categorize_by_severity(violations),
        "violations": violations,
        "summary": generate_summary(violations),
        "recommendations": generate_recommendations(violations),
        "compliance_score": calculate_score(violations),
        "timestamp": datetime.now().isoformat(),
    }
```

**Comprehensive Report Format**:
```json
{
  "schedule_id": "schedule-2025-12",
  "date_range": {
    "start": "2025-12-01",
    "end": "2025-12-31"
  },
  "compliance_summary": {
    "overall_score": 92,  // 0-100
    "status": "COMPLIANT",
    "total_violations": 3,
    "critical": 0,
    "warning": 2,
    "info": 1
  },
  "acgme_rules": {
    "80_hour_rule": {
      "compliant": true,
      "violations": 0,
      "max_hours": 79.5,
      "avg_hours": 61.2
    },
    "1_in_7_rest": {
      "compliant": true,
      "violations": 0
    },
    "supervision_ratio": {
      "compliant": true,
      "violations": 0,
      "avg_ratio": "1:2.5"
    }
  },
  "quality_metrics": {
    "spc": {
      "violations": 1,
      "control_limit_breaches": 0,
      "rules_triggered": ["rule_4"],
      "severity": "warning"
    },
    "process_capability": {
      "cpk": 1.38,
      "interpretation": "CAPABLE",
      "sigma_level": 4.1
    },
    "equity": {
      "gini": 0.12,
      "is_equitable": true,
      "max_delta": 14.3,
      "concern": "one_provider_underloaded"
    }
  },
  "resource_utilization": {
    "utilization_pct": 78.5,
    "level": "YELLOW",
    "margin_to_critical": 1.5,
    "concern": "approaching_threshold"
  },
  "detailed_violations": [
    {
      "id": "v001",
      "severity": "warning",
      "category": "spc",
      "rule": "western_electric_4",
      "message": "8 consecutive points above centerline (2025-12-08 to 2025-12-15)",
      "affected_people": ["RES-001", "RES-002"],
      "affected_blocks": 8,
      "suggested_action": "Review rotation assignments for trend"
    }
  ],
  "recommendations": [
    {
      "priority": 1,
      "category": "immediate",
      "action": "None - schedule compliant",
      "rationale": "All ACGME rules satisfied"
    },
    {
      "priority": 2,
      "category": "monitoring",
      "action": "Watch SPC trend",
      "rationale": "8-point rule triggered; monitor next week"
    },
    {
      "priority": 3,
      "category": "long_term",
      "action": "Rebalance equity",
      "rationale": "FAC-001 underloaded by 14.3 hours"
    }
  ],
  "deployment_readiness": {
    "can_deploy": true,
    "blocking_issues": [],
    "warnings": ["spc_trend", "utilization_yellow"],
    "approval_level": "coordinator"
  }
}
```

---

## Output Formats

### 1. Executive Summary (For Leadership)
```
COMPLIANCE CHECK REPORT
Schedule: December 2025
Date: 2025-12-31

Status: COMPLIANT ✓
Overall Score: 92/100

Key Metrics:
├─ ACGME Violations: 0
├─ Quality Issues: 2 (minor)
├─ Utilization: 78.5% (yellow)
└─ Equity (Gini): 0.12 (good)

Recommendation: APPROVE FOR DEPLOYMENT
```

### 2. Detailed Report (For Coordinators)
```
DETAILED COMPLIANCE ANALYSIS
[10+ page PDF with all violations, trends, recommendations]
```

### 3. JSON API Response (For Integrations)
```json
{
  "compliance_score": 92,
  "violations": [...],
  "recommendations": [...],
  "raw_metrics": {...}
}
```

### 4. Monitoring Dashboard Data
```
Real-time metrics feed for live dashboards:
- Compliance trend (last 30 days)
- SPC control charts (weekly)
- Equity distribution (current)
- Utilization gauge (current)
```

---

## Common Scenarios & Responses

### Scenario 1: Compliant Schedule
```
Status: COMPLIANT ✓
Score: 95+
Action: APPROVE - Deploy to production
Reason: All rules satisfied, quality metrics good
Monitor: Routine monitoring only
```

### Scenario 2: Minor Violations
```
Status: MINOR ISSUES ⚠
Score: 80-94
Action: CONDITIONAL APPROVE
Condition: Coordinator review violations
Reason: Non-critical issues, easily addressable
Follow-up: Implement recommendations within 2 weeks
```

### Scenario 3: Critical Violations
```
Status: NON-COMPLIANT ✗
Score: <80
Action: DO NOT DEPLOY
Reason: ACGME violation(s) detected
Fix Required: Address critical issues before deployment
Estimated Fix Time: 2-7 days (schedule regeneration)
```

---

## Performance Characteristics

| Phase | Tools | Parallelizable | Time | Result |
|-------|-------|----------------|------|--------|
| 1 | 2 | Yes | 0.5s | Core compliance |
| 2 | 3 | Yes | 1.0s | Detailed issues |
| 3 | 4 | Yes | 0.5s | Advanced metrics |
| 4 | 1 | N/A | 0.5s | Report synthesis |
| **Total** | **10** | **Mostly** | **2-3s** | Complete report |

**Optimization**:
- All phases parallelizable except 4
- Cache results valid for 24h if no schedule changes
- Streaming results for large schedules

---

## Configuration Variants

### Quick Check (30 seconds)
```python
"mode": "quick",
"phases": [1],  # ACGME rules only
"caching": True,
"detail_level": "summary",
```

### Standard Check (2-3 seconds)
```python
"mode": "standard",
"phases": [1, 2, 3, 4],  # All phases
"caching": True,
"detail_level": "detailed",
```

### Audit Check (5-10 seconds)
```python
"mode": "audit",
"phases": [1, 2, 3, 4],  # All phases
"caching": False,  # Fresh data
"detail_level": "exhaustive",
"include_historical": True,  # Trend analysis
```

---

## Success Criteria

Compliance check is successful when:

```
✓ All phases complete within 3 seconds
✓ No tool timeout/failure (fallback if needed)
✓ Report generated in required format
✓ Compliance score <= 100
✓ Violations clearly categorized
✓ Recommendations actionable
✓ No PII leaked in output
```

---

## Related Documentation

- **ACGME Rules**: See docs/user-guide/compliance.md
- **Workflow_Swap_Execution**: Handle schedule modifications
- **Workflow_Schedule_Generation**: Generate new schedule
- **MCP_TOOL_DEPENDENCY_GRAPH**: Tool sequencing details

---

**Last Updated**: 2025-12-31
**Version**: 1.0
**Tested**: Daily in production
**Safety**: TIER 1 (read-only, autonomous execution approved)
