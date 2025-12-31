# Workflow: Resilience Assessment

**Purpose**: Comprehensive system-wide resilience evaluation with multi-domain analysis
**Safety**: TIER 1 (read-only analysis and monitoring)
**Execution Time**: 5-8 seconds
**Frequency**: Weekly (automated) or on-demand
**Operator**: System (automated), leadership (review)

---

## Workflow Overview

This workflow performs comprehensive resilience assessment across multiple domains: contingency analysis, burnout epidemiology, network analysis, and advanced metrics.

```
System Health Check Request
  │
  ├─→ Phase 1: Quick System Status (0.5 seconds)
  │     ├─ Check utilization threshold
  │     ├─ Check circuit breaker status
  │     └─ Get defense level
  │
  ├─→ Phase 2: Contingency Vulnerability (2-3 seconds)
  │     ├─ Run N-1/N-2 contingency analysis
  │     ├─ Calculate blast radius
  │     ├─ Identify critical personnel
  │     └─ Plan mitigation strategies
  │
  ├─→ Phase 3: Burnout Epidemiology (1-2 seconds)
  │     ├─ Calculate burnout Rt
  │     ├─ Identify superspreaders
  │     ├─ Simulate contagion spread
  │     └─ Network intervention planning
  │
  ├─→ Phase 4: Advanced Analytics (1-2 seconds)
  │     ├─ Early warning signals (precursors, SPC, fire index)
  │     ├─ Fatigue assessment (FRMS, creep-fatigue)
  │     ├─ Specialized analysis (entropy, harmonics, equilibrium)
  │     └─ Quality metrics (equity, capability)
  │
  ├─→ Phase 5: Unified Risk Synthesis (0.5 seconds)
  │     ├─ Aggregate all signals
  │     ├─ Calculate unified critical index
  │     ├─ Identify risk patterns
  │     └─ Generate recommendations
  │
  └─→ Phase 6: Reporting & Alerting
        ├─ Generate executive dashboard
        ├─ Escalate critical alerts
        └─ Log metrics for trend analysis
```

---

## Phase 1: Quick System Status (0.5 seconds)

**Goals**:
- Get snapshot of system health
- Identify critical alerts
- Determine if deeper analysis needed

**Tools** (Parallel):
- `check_utilization_threshold`
- `check_circuit_breakers`
- `get_defense_level`

**Execution**:
```python
async def phase_1_quick_status() -> Phase1Result:
    """Get system health snapshot."""

    results = await asyncio.gather(
        check_utilization_threshold(
            available_faculty=count_active_faculty(),
            required_blocks=get_required_blocks(),
        ),
        check_circuit_breakers(),
        get_defense_level(),
    )

    utilization, breakers, defense = results

    return Phase1Result(
        timestamp=datetime.now(),
        utilization={
            "pct": utilization.utilization_pct,
            "level": utilization.level,  # GREEN/YELLOW/ORANGE/RED/BLACK
            "threshold_margin": 80.0 - utilization.utilization_pct,
        },
        circuit_breakers={
            "closed": len([b for b in breakers if b.state == "CLOSED"]),
            "open": len([b for b in breakers if b.state == "OPEN"]),
            "half_open": len([b for b in breakers if b.state == "HALF_OPEN"]),
            "total": len(breakers),
        },
        defense_level=defense.level,  # 1-5 (prevention to emergency)
        system_status=calculate_status([utilization, breakers, defense]),
    )
```

**Phase 1 Output**:
```json
{
  "timestamp": "2025-12-31T15:00:00Z",
  "system_status": "YELLOW",
  "utilization": {
    "current_pct": 78.5,
    "level": "YELLOW",
    "threshold": 80.0,
    "margin": 1.5,
    "safe": false
  },
  "circuit_breakers": {
    "closed": 12,
    "open": 0,
    "half_open": 1,
    "total": 13,
    "health": "mostly_healthy"
  },
  "defense_level": 2,
  "interpretation": "System operating near capacity. Recommend monitoring."
}
```

**Phase 1 Alerts**:

```
RED ALERT: Utilization >= 90% → Activate contingency protocols
YELLOW ALERT: Utilization 80-90% → Increase monitoring frequency
ORANGE: Circuit breaker OPEN → Check protected resource
HALF_OPEN: Testing recovery → Monitor 5 minutes
```

---

## Phase 2: Contingency Vulnerability (2-3 seconds)

**Goals**:
- Identify which personnel are critical
- Calculate impact if they're absent (N-1)
- Plan coverage gaps and workarounds

**Tools** (Sequential):
- `run_contingency_analysis_deep` (N-1/N-2 analysis)
- `calculate_blast_radius` (impact scope)
- `execute_sacrifice_hierarchy` (preview load shedding)

**Execution**:
```python
async def phase_2_contingency_analysis() -> Phase2Result:
    """Analyze system vulnerability to N-1/N-2 failures."""

    # Step 1: Deep contingency analysis
    contingency = await run_contingency_analysis_deep(
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        analyze_n1=True,
        analyze_n2=False,  # Focus on single failures
    )

    # Step 2: Calculate impact radius
    blast_radius = await calculate_blast_radius(
        schedule_id=get_current_schedule().id,
        max_personnel=15,  # Top 15 critical people
        include_cost=True,
    )

    # Step 3: Analyze load shedding options
    sacrifice = await execute_sacrifice_hierarchy(
        preview_mode=True,
        load_shedding_level="LEVEL_3",
    )

    # Synthesize findings
    return Phase2Result(
        contingency_analysis=contingency,
        critical_personnel=identify_critical_people(blast_radius),
        coverage_gaps=summarize_gaps(contingency),
        mitigation_strategies=plan_mitigations(contingency, sacrifice),
        vulnerability_score=calculate_vulnerability(contingency, blast_radius),
    )
```

**Critical Personnel Identification**:
```json
{
  "critical_personnel": [
    {
      "person_id": "FAC-PD",
      "rank": 1,
      "critical_rotations": ["Inpatient-call", "Procedures"],
      "if_absent_coverage_gaps": 5,
      "workarounds_available": 3,
      "backup_coverage": "Inadequate",
      "risk_level": "HIGH"
    },
    {
      "person_id": "FAC-001",
      "rank": 2,
      "critical_rotations": ["Clinic"],
      "if_absent_coverage_gaps": 2,
      "workarounds_available": 1,
      "backup_coverage": "Partial",
      "risk_level": "MEDIUM"
    }
  ],
  "total_critical_count": 5,
  "total_vulnerable_gaps": 12,
  "percentage_of_schedule": 1.6  // 12 out of 730 blocks
}
```

**Blast Radius Metrics**:
```json
{
  "blast_radius_analysis": {
    "max_blast_radius": 8,
    "avg_blast_radius": 3.5,
    "personnel_analysis": [
      {
        "person_id": "FAC-PD",
        "direct_impact": 5,
        "cascading_impact": 3,
        "total_affected_people": 8,
        "total_affected_blocks": 15
      }
    ],
    "critical_cascade_count": 2
  }
}
```

**Mitigation Strategies**:
```json
{
  "mitigation_strategies": [
    {
      "priority": 1,
      "person_id": "FAC-PD",
      "strategy": "Cross-train 2 faculty for call coverage",
      "timeline": "2-4 weeks",
      "gap_reduction": "80%"
    },
    {
      "priority": 2,
      "person_id": "FAC-001",
      "strategy": "Develop clinic rotation backup plan",
      "timeline": "1 week",
      "gap_reduction": "50%"
    }
  ]
}
```

---

## Phase 3: Burnout Epidemiology (1-2 seconds)

**Goals**:
- Monitor burnout spread through network
- Identify superspreaders
- Plan network-based interventions

**Tools** (Parallel then Sequential):
- `calculate_burnout_rt` (transmission rate)
- `simulate_burnout_contagion` (network spread)
- Plus: Historical burnout data analysis

**Execution**:
```python
async def phase_3_burnout_epidemiology() -> Phase3Result:
    """Analyze burnout spread and contagion risk."""

    # Identify currently burned out residents
    burned_out = await get_burned_out_residents()

    # Calculate transmission rate
    rt_result = await calculate_burnout_rt(
        burned_out_provider_ids=[p.id for p in burned_out],
        time_window_days=28,
    )

    # Simulate network spread
    contagion_result = await simulate_burnout_contagion(
        initial_infected_ids=[p.id for p in burned_out],
        transmission_probability=0.1,
        recovery_probability=0.05,
        iterations=100,
    )

    # Identify high-risk contacts
    high_risk = contagion_result.superspreaders

    return Phase3Result(
        rt_value=rt_result.rt,
        intervention_level=rt_result.intervention_level,
        epidemic_trajectory=contagion_result,
        superspreaders=high_risk,
        intervention_targets=select_intervention_targets(high_risk),
    )
```

**Burnout Rt Assessment**:
```json
{
  "burnout_epidemiology": {
    "rt": 1.2,
    "status": "spreading",
    "interpretation": "Burnout spreading at 20% per 28-day cycle",
    "intervention_level": "moderate",
    "interventions": [
      "Workload reduction for 3 at-risk individuals",
      "Peer support pairing with resilient staff",
      "Wellness program outreach"
    ],
    "herd_immunity_threshold": 0.17,
    "current_affected": {
      "burned_out": 2,
      "at_risk": 4,
      "high_risk": 1
    }
  }
}
```

**Superspreader Analysis**:
```json
{
  "superspreaders": [
    {
      "person_id": "RES-001",
      "superspreader_score": 0.78,
      "network_connections": 12,
      "estimated_influence": "5+ residents",
      "intervention": "High-priority wellness support + monitoring"
    }
  ],
  "high_risk_contacts": [
    "RES-002", "RES-004", "RES-007"
  ],
  "recommended_interventions": [
    {
      "type": "isolation",
      "person": "RES-001",
      "duration": "2 weeks",
      "reason": "Intensive burnout recovery"
    },
    {
      "type": "peer_support",
      "target": ["RES-002", "RES-004"],
      "duration": "4 weeks",
      "reason": "High-risk contacts prevention"
    }
  ]
}
```

---

## Phase 4: Advanced Analytics (1-2 seconds)

**Goals**:
- Detect early warning signals
- Assess fatigue accumulation
- Monitor specialized metrics

**Tools** (Parallel execution - 8 tools):

```
Early Warning Batch:
├─ detect_burnout_precursors (STA/LTA seismic)
├─ run_spc_analysis (Western Electric rules)
├─ calculate_fire_danger_index (CFFDRS)
├─ predict_burnout_magnitude (multi-signal)
├─ detect_workload_anomalies (Kalman filter)
└─ run_frms_assessment (Fatigue Risk Management)

Specialized Analysis Batch:
├─ assess_creep_fatigue (Larson-Miller)
└─ calculate_schedule_entropy (Disorder metric)
```

**Execution**:
```python
async def phase_4_advanced_analytics() -> Phase4Result:
    """Run all advanced analytics in parallel."""

    early_warning_tasks = [
        detect_burnout_precursors(
            resident_id="all",
            signal_type=["swap_requests", "sick_calls"],
        ),
        run_spc_analysis(resident_id="all"),
        calculate_fire_danger_index(resident_id="all"),
        predict_burnout_magnitude(resident_id="all"),
        detect_workload_anomalies(resident_id="all"),
        run_frms_assessment(),
    ]

    specialized_tasks = [
        assess_creep_fatigue(include_assessments=True, top_n=20),
        calculate_schedule_entropy(),
    ]

    results = await asyncio.gather(*early_warning_tasks, *specialized_tasks)

    return Phase4Result(
        early_warning=aggregate_early_warning(results[:6]),
        fatigue_assessment=results[6],
        entropy=results[7],
        critical_residents=identify_critical_residents(results),
    )
```

**Early Warning Summary**:
```json
{
  "early_warning_signals": {
    "burnout_precursors": {
      "alerts_detected": 2,
      "severity": ["warning", "warning"],
      "residents": ["RES-001", "RES-003"]
    },
    "spc_violations": {
      "violations": 1,
      "rule": "rule_4",
      "severity": "warning"
    },
    "fire_danger": {
      "extreme": 0,
      "very_high": 1,
      "high": 3,
      "moderate": 4
    },
    "workload_anomalies": {
      "detected": 2,
      "residents": ["RES-002", "RES-005"]
    }
  }
}
```

**Fatigue Assessment**:
```json
{
  "fatigue_assessment": {
    "residents_analyzed": 10,
    "high_risk": 2,
    "moderate_risk": 3,
    "low_risk": 5,
    "frms_score_avg": 4.2,
    "critical_concerns": [
      "RES-001: Tertiary creep stage (pre-failure)",
      "RES-003: Elevated fatigue hazard"
    ]
  }
}
```

---

## Phase 5: Unified Risk Synthesis (0.5 seconds)

**Goals**:
- Synthesize all signals into unified score
- Identify risk patterns
- Generate actionable recommendations

**Tool**:
- `get_unified_critical_index`

**Execution**:
```python
async def phase_5_unified_synthesis() -> Phase5Result:
    """Synthesize all resilience signals."""

    unified = await get_unified_critical_index(
        include_details=True,
        top_n=20,
    )

    # Enhance with context from earlier phases
    enhanced = add_phase_context(
        unified,
        phase_1_status,
        phase_2_vulnerability,
        phase_3_epidemiology,
        phase_4_analytics,
    )

    return Phase5Result(
        unified_index=enhanced,
        overall_risk_level=enhanced.risk_level,
        critical_faculty_count=enhanced.critical_count,
        risk_patterns=identify_patterns(enhanced),
        top_priorities=rank_priorities(enhanced),
    )
```

**Unified Risk Index Output**:
```json
{
  "overall_resilience_index": 42.5,
  "scale": "0-100 (higher = more risk)",
  "risk_level": "MODERATE",
  "interpretation": "System functioning but requires monitoring",
  "contributing_factors": {
    "contingency_vulnerability": 48,  // 40% weight
    "network_centrality": 38,  // 35% weight
    "burnout_epidemiology": 32  // 25% weight
  },
  "critical_faculty": [
    {
      "person_id": "FAC-PD",
      "risk_score": 68,
      "risk_pattern": "structural_burnout",
      "concerns": ["High contingency impact", "Elevated fire danger"],
      "interventions": [
        "Cross-training backup",
        "Workload reduction",
        "Wellness program"
      ]
    }
  ],
  "system_risk_patterns": [
    {
      "pattern": "structural_burnout",
      "count": 3,
      "intervention_focus": "Workload + wellness"
    },
    {
      "pattern": "isolated_workhorse",
      "count": 2,
      "intervention_focus": "Backup development"
    }
  ]
}
```

---

## Phase 6: Reporting & Alerting (0.5 seconds)

**Goals**:
- Generate executive reports
- Trigger alerts if critical
- Log metrics for trend analysis

**Output Formats**:

### Executive Dashboard
```json
{
  "timestamp": "2025-12-31T15:00:00Z",
  "system_health": "YELLOW",
  "key_metrics": {
    "resilience_index": 42.5,
    "utilization": "78.5% (YELLOW)",
    "burnout_rt": 1.2,
    "critical_faculty": 5,
    "defense_level": 2
  },
  "alerts": [
    {
      "severity": "HIGH",
      "message": "Utilization approaching critical (78.5%)",
      "action": "Review contingency plans"
    },
    {
      "severity": "MEDIUM",
      "message": "Burnout spreading (Rt=1.2)",
      "action": "Increase wellness program availability"
    }
  ],
  "recommendations": [
    "Cross-train 2 faculty for call coverage (FAC-PD backup)",
    "Implement targeted burnout interventions (3 residents)",
    "Monitor SPC trend (rule 4 violation this week)"
  ]
}
```

### Alert Escalation Logic
```python
if unified_index.risk_level == "CRITICAL":
    # Alert leadership immediately
    send_alert_to([
        "program_director",
        "associate_program_director",
        "hr_director"
    ], urgency="immediate")

elif unified_index.risk_level == "ELEVATED":
    # Alert coordinators
    send_alert_to(["coordinators"], urgency="high")

elif unified_index.risk_level == "MODERATE":
    # Log for review
    log_to_dashboard("resilience_metrics")
```

### Trend Analysis
```json
{
  "trend_analysis": {
    "period": "last_4_weeks",
    "resilience_index_trend": "improving",
    "utilization_trend": "increasing",
    "burnout_rt_trend": "stable",
    "critical_faculty_trend": "increasing",
    "forecast_30d": {
      "predicted_index": 45.0,
      "confidence": 0.75,
      "risk_level_forecast": "MODERATE"
    }
  }
}
```

---

## Configuration Variants

### Quick Assessment (2 seconds)
```python
"mode": "quick",
"phases": [1, 5],  # Skip detailed analysis
"detail_level": "summary",
```

### Standard Assessment (5 seconds)
```python
"mode": "standard",
"phases": [1, 2, 3, 4, 5],  # All phases
"detail_level": "comprehensive",
```

### Deep Audit (15+ seconds)
```python
"mode": "deep",
"phases": [1, 2, 3, 4, 5],
"detail_level": "exhaustive",
"include_historical": True,
"historical_periods": 12,  # 12 weeks of history
```

---

## Performance Targets

| Phase | Tools | Parallelizable | Time | Critical |
|-------|-------|----------------|------|----------|
| 1: Quick Status | 3 | Yes | 0.5s | High |
| 2: Contingency | 3 | No | 2-3s | High |
| 3: Epidemiology | 2 | Partial | 1-2s | Medium |
| 4: Advanced | 8 | Yes | 1-2s | Medium |
| 5: Synthesis | 1 | N/A | 0.5s | High |
| 6: Reporting | - | N/A | 0.5s | Medium |
| **Total** | **18+** | **High** | **5-8s** | |

**Optimization**:
- Cache contingency results (valid 6-12 hours)
- Cache epidemiology (valid 24 hours)
- Pre-compute early warning in background tasks

---

## Error Handling

```python
# Phase-specific error handling
if phase_2_contingency_fails():
    logger.warning("Contingency analysis failed - using cached data")
    contingency = get_cached_contingency()

if phase_4_early_warning_timeout():
    logger.warning("Early warning batch incomplete - partial results")
    return Phase4Result(
        early_warning=partial_results,
        fatigue_assessment=None,
        note="Incomplete analysis - timeout"
    )

# Overall synthesis
if overall_synthesis_incomplete():
    return Phase5Result(
        unified_index=degraded_index,
        confidence="low",
        recommendation="Retry full assessment"
    )
```

---

## Success Criteria

Resilience assessment is successful when:

```
✓ All phases complete within 8 seconds
✓ Unified index calculated
✓ Critical personnel identified
✓ Mitigation strategies available
✓ Alerts generated if needed
✓ Recommendations actionable
✓ Trend analysis complete
```

---

## Related Workflows

- **WORKFLOW_SCHEDULE_GENERATION.md**: Use resilience assessment to guide generation
- **WORKFLOW_COMPLIANCE_CHECK.md**: Validate schedule after generation
- **Circuit Breaker Integration**: Use defense level to auto-trigger protections

---

**Last Updated**: 2025-12-31
**Version**: 1.0
**Safety**: TIER 1 (read-only, autonomous execution approved)
**Frequency**: Weekly automated + on-demand
