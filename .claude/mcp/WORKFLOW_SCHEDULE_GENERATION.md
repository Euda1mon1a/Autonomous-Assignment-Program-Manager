# Workflow: Schedule Generation

**Purpose**: Generate new schedules with full ACGME compliance and resilience validation
**Safety**: TIER 2 (generation + preview, no direct apply)
**Execution Time**: 5-15 seconds total
**Frequency**: Weekly or on-demand
**Operator**: Scheduler/AI with human review

---

## Workflow Phases

### Phase 1: Pre-Generation Analysis (2 seconds)

**Goals**:
- Validate system readiness
- Check resource availability
- Identify constraints and conflicts

**Tool Sequence** (Parallel execution):
```
┌─────────────────────────────────────────┐
│ Phase 1: Pre-Generation Analysis        │
│ Parallelizable: Yes                     │
└────────────────────┬────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
   1a.   │      1b.  │      1c.  │
validate_check_utiliz detect_
schedule  ation_thresh conflicts
         │           │           │
  ✓ All   │  ✓ Util < │ ✓ Count  │
  rules   │   80%     │ conflicts│
  passed  │           │          │
         └───────────┬───────────┘
                     │
              Output: Ready status
```

**Phase 1 Configuration**:
```python
phase_1_config = {
    "validate_schedule": {
        "check_work_hours": True,
        "check_supervision": True,
        "check_rest_periods": True,
        "check_consecutive_duty": True,
    },
    "check_utilization_threshold": {
        "critical": False,  # Allow generation even if yellow
    },
    "detect_conflicts": {
        "include_resolved": False,  # Only unresolved conflicts
    },
    "timeout": 2.0,  # seconds
}
```

**Phase 1 Success Criteria**:
```
✓ validate_schedule.is_compliant OR constraints_acceptable
✓ check_utilization_threshold.level <= "ORANGE"
✓ detect_conflicts.auto_resolvable OR conflict_count == 0
✓ No blocking issues detected
```

**Phase 1 Error Handling**:
```python
if phase_1_results["critical_conflicts_found"]:
    raise GenerationBlockedError("Unresolvable conflicts exist")

if phase_1_results["utilization_level"] == "BLACK":
    return {
        "status": "BLOCKED",
        "reason": "System critical utilization",
        "recommendation": "Activate sacrifice hierarchy first"
    }

if phase_1_results["validation_rate"] < 0.8:
    logger.warning("Low baseline compliance - generation may struggle")
```

---

### Phase 2: Contingency Simulation (3-5 seconds)

**Goals**:
- Understand vulnerability landscape
- Identify critical personnel
- Plan contingency coverage

**Tool Sequence**:
```
┌─────────────────────────────────────────┐
│ Phase 2: Contingency Simulation         │
│ Execution: Sequential                   │
└────────────────────┬────────────────────┘
                     │
              2a. run_contingency_analysis
                     │
           ┌─────────┼─────────┐
           │         │         │
      Generate    Analyze    Identify
      4 scenarios critical   N-1 points
           │         │         │
           └────────────────────┘
                     │
         2b. calculate_blast_radius
                     │
      For each critical person:
        ├─ Impact if absent
        ├─ Coverage gaps
        └─ Workload ripple
                     │
         2c. execute_sacrifice_hierarchy (preview)
                     │
        Identify which rotations
        could be shed if needed
```

**Phase 2 Configuration**:
```python
phase_2_config = {
    "run_contingency_analysis": {
        "analyze_n1": True,
        "analyze_n2": False,  # Only single-point failures
        "days_ahead": 30,
    },
    "calculate_blast_radius": {
        "max_personnel": 10,  # Top 10 critical people
        "include_cost": True,
    },
    "execute_sacrifice_hierarchy": {
        "preview_mode": True,  # No apply
        "load_shedding_level": "LEVEL_3",
    },
    "timeout": 5.0,
}
```

**Phase 2 Output Structure**:
```json
{
  "n1_failures": [
    {
      "person_id": "FAC-PD",
      "coverage_gaps": 12,
      "critical_gaps": ["Inpatient-call", "Procedures"],
      "workarounds_available": true,
      "workaround_count": 3
    }
  ],
  "blast_radius": {
    "max_radius": 8,
    "avg_radius": 4.2,
    "personnel_with_high_impact": 5
  },
  "sacrifice_options": {
    "level_1_sheds": [],
    "level_2_sheds": ["Clinic-routine"],
    "level_3_sheds": ["Procedures", "Research"]
  }
}
```

**Phase 2 Success Criteria**:
```
✓ All N-1 scenarios analyzed
✓ At least 50% of critical gaps have workarounds
✓ Blast radius < 10 (acceptable)
✓ Sacrifice hierarchy provides options
```

---

### Phase 3: Early Warning Assessment (1-2 seconds)

**Goals**:
- Identify burnout risk factors
- Check fatigue metrics
- Monitor precursor signals

**Tool Sequence** (Parallel):
```
┌─────────────────────────────────────────┐
│ Phase 3: Early Warning Assessment       │
│ Parallelizable: Yes (5 tools)           │
└────────────────────┬────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   3a.  │       3b.  │       3c.  │
detect_ run_spc_  calculate_fire
burnout_analysis danger_index
precur           │      │
sors             │      │
        │        │      │      │
   3d.  │   3e.  │      │      │
predict_burnout_ detect_
magnitude       workload_
             anomalies
        │        │      │      │
        └────────┼──────┴──────┘
                 │
          Aggregate signals
```

**Phase 3 Configuration**:
```python
phase_3_config = {
    "detect_burnout_precursors": {
        "signal_type": "ALL",  # All signal types
        "confidence_level": 0.85,  # Be conservative
    },
    "run_spc_analysis": {
        "target_hours": 60.0,
        "sigma": 5.0,
    },
    "calculate_fire_danger_index": {
        "include_projections": True,
    },
    "detect_workload_anomalies": {
        "sensitivity": "MEDIUM",
    },
    "timeout": 2.0,
}
```

**Phase 3 Success Criteria**:
```
✓ No CRITICAL precursor signals
✓ No SPC rule violations (or documented)
✓ Fire danger < EXTREME for most residents
✓ Anomalies count < 20% of population
```

---

### Phase 4: Unified Risk Assessment (1-2 seconds)

**Goals**:
- Synthesize all signals
- Identify holistic system risk
- Check readiness for generation

**Tool Sequence**:
```
┌─────────────────────────────────────────┐
│ Phase 4: Unified Risk Assessment        │
│ Aggregates: Phases 1-3 + all metrics   │
└────────────────────┬────────────────────┘
                     │
          4. get_unified_critical_index
                     │
        Weighted synthesis:
        ├─ 40% Contingency (Phase 2)
        ├─ 35% Hub Analysis (behavioral)
        ├─ 25% Epidemiology (burnout Rt)
        └─ Plus: All early warning signals
                     │
          Output: Risk level + patterns
```

**Phase 4 Configuration**:
```python
phase_4_config = {
    "get_unified_critical_index": {
        "include_details": True,
        "top_n": 20,  # Top 20 at-risk faculty
    },
    "timeout": 1.0,
}
```

**Phase 4 Output Structure**:
```json
{
  "overall_index": 38.5,  // 0-100 scale
  "risk_level": "MODERATE",
  "universal_critical_count": 2,
  "critical_patterns": [
    {
      "pattern": "structural_burnout",
      "count": 3,
      "intervention": "Reduce workload + wellness"
    }
  ],
  "top_concerns": [
    "2 residents with high burnout Rt",
    "Inpatient rotation over-dependent on 1 faculty",
    "Precursor signals in night float crew"
  ]
}
```

**Phase 4 Success Criteria**:
```
✓ Risk level <= ELEVATED (RED is warning)
✓ Universal critical count <= 3
✓ No impossible constraints detected
✓ Recommendation path clear
```

---

### Phase 5: Generation Parameters & Execute (5-10 seconds)

**Goals**:
- Configure generator algorithm
- Execute with safety constraints
- Produce draft schedule

**Tool Sequence**:
```
┌─────────────────────────────────────────┐
│ Phase 5: Schedule Generation            │
│ Backend operation (not MCP tool)        │
└────────────────────┬────────────────────┘
                     │
   5. Call backend /schedules/generate
      with parameters from phases 1-4
                     │
    ┌────────────────┼────────────────┐
    │                │                │
  Algorithm      Constraints      Callbacks
  selection      hardening
  ├─ greedy      ├─ Force ACGME   ├─ Progress
  ├─ cp_sat      ├─ Honor N-1     │  updates
  ├─ hybrid      │  workarounds   └─ Alert
  └─ custom      └─ Minimize      on issues
                    churn
                     │
          Draft schedule produced
```

**Phase 5 Configuration**:
```python
phase_5_config = {
    "algorithm": "hybrid",  # Default
    "constraints": {
        "acgme_hard": True,  # Never violate
        "n1_workarounds": phase_2["workarounds"],
        "avoid_reassignment": [
            "high_stability_residents"
        ],
    },
    "objectives": {
        "minimize_churn": 0.8,  # 80% weight
        "maximize_equity": 0.1,  # 10% weight
        "minimize_cost": 0.1,   # 10% weight
    },
    "timeout": 10.0,
}
```

---

### Phase 6: Post-Generation Validation (1-2 seconds)

**Goals**:
- Validate generated schedule
- Check against original constraints
- Identify any issues for review

**Tool Sequence** (Parallel):
```
┌─────────────────────────────────────────┐
│ Phase 6: Post-Generation Validation     │
│ Parallelizable: Yes                     │
└────────────────────┬────────────────────┘
                     │
        ┌────────────┼───────────────┐
        │            │               │
   6a.  │       6b.  │          6c.  │
validate detect_   run_contingency
schedule conflicts analysis (re-run)
 (new)             │           │
        │          │           │
        └──────────┬───────────┘
                   │
     6d. get_unified_critical_index
            (new schedule)
                   │
          Compare Phase 4 vs 6d
```

**Phase 6 Configuration**:
```python
phase_6_config = {
    "validate_schedule": {
        "strict_mode": True,  # Higher bar
    },
    "run_contingency_analysis": {
        # Same config as Phase 2
    },
    "timeout": 2.0,
}
```

**Phase 6 Success Criteria**:
```
✓ validate_schedule.is_compliant == True
✓ detect_conflicts.critical_count == 0
✓ Unified index improved or stable (not worse)
✓ All N-1 workarounds still valid
```

---

### Phase 7: Human Review & Approval

**Goals**:
- Present findings to human operator
- Get approval before deployment
- Document decision rationale

**Review Checklist**:
```
PHASE 1 (Pre-Generation): ___
  [ ] Baseline compliance acceptable
  [ ] System not in critical state
  [ ] Conflicts resolvable

PHASE 2 (Contingency): ___
  [ ] N-1 coverage adequate
  [ ] No single points of failure
  [ ] Sacrifice options clear

PHASE 3 (Early Warning): ___
  [ ] No CRITICAL precursors
  [ ] Fatigue risk acceptable
  [ ] Anomalies explained

PHASE 4 (Unified Index): ___
  [ ] Risk level acceptable
  [ ] No impossible constraints
  [ ] Clear path to improvement

PHASE 6 (Validation): ___
  [ ] Generated schedule compliant
  [ ] No new issues created
  [ ] Improvements realized

APPROVAL: [Coordinator signature]
TIMESTAMP: [ISO datetime]
RATIONALE: [Free text field]
```

---

## Error Handling & Fallback

### Critical Failures

```python
class ScheduleGenerationError(Exception):
    """Base class for generation errors"""
    pass

class GenerationBlockedError(ScheduleGenerationError):
    """Generation cannot proceed - system not ready"""
    # Trigger: Phase 1 validation < 80%
    # Action: Request manual conflict resolution before retry

class ContingencyFailureError(ScheduleGenerationError):
    """Contingency analysis failed - system too fragile"""
    # Trigger: Phase 2 shows >50% N-1 gaps
    # Action: Activate sacrifice hierarchy first, then retry

class RiskTooHighError(ScheduleGenerationError):
    """System risk too elevated - generation deferred"""
    # Trigger: Phase 4 index > 70
    # Action: Address top concerns, retry in 24h
```

### Graceful Degradation

```
SCENARIO: Phase 5 generator timeout (stuck solver)
├─ Retry 1: Reduce complexity (greedy algorithm)
├─ Retry 2: Use last-known-good schedule as starting point
└─ Fallback: Return Phase 1 baseline with partial updates

SCENARIO: Phase 2 contingency analysis fails
├─ Continue with Phase 3 early warning
├─ Skip N-1 validation
└─ Flag for manual review before approval

SCENARIO: Unified index computation fails
├─ Use Phase 3 individual signals
├─ Aggregate manually with equal weights
└─ Lower confidence in result, request review
```

---

## Performance Targets

| Phase | Tool Count | Parallelizable | Time | Critical |
|-------|-----------|----------------|------|----------|
| 1 | 3 | Yes | 0.5s | High |
| 2 | 3 | No | 3-5s | High |
| 3 | 5 | Yes | 1-2s | Medium |
| 4 | 1 | N/A | 1-2s | High |
| 5 | Backend | N/A | 5-10s | Critical |
| 6 | 4 | Yes | 1-2s | High |
| **Total** | **19+** | **Hybrid** | **12-25s** | |

**Optimization**:
- Run Phases 1, 3 in parallel after baseline collection
- Cache contingency results if <24h old
- Pre-warm solver with partial schedule

---

## Configuration Examples

### Fast Generation (Express Path)
```python
# Skip deep analysis, trust recent baseline
"workflow_mode": "express",
"skip_phases": ["contingency_deep"],
"use_cached": {
    "contingency": 1440,  # 24h cache ok
    "early_warning": 360,  # 6h cache ok
},
"timeout": 5.0,
```

### Thorough Generation (Full Analysis)
```python
# Run all phases, extensive validation
"workflow_mode": "thorough",
"skip_phases": [],
"use_cached": {},
"extra_validations": True,
"timeout": 30.0,
```

### Emergency Generation (Critical Fix)
```python
# Fast, accept lower validation bars
"workflow_mode": "emergency",
"skip_phases": ["full_contingency"],
"validation_threshold": 0.85,  # Instead of 0.95
"timeout": 5.0,
"requires_approval": True,
```

---

## Success Metrics

After schedule deployment, measure:

```python
success_metrics = {
    "compliance_maintained": True,  # >= 95% compliance
    "churn_minimized": <10,  # Changes from previous
    "fatigue_improved": True,  # Unified index lower
    "contingency_robust": >75,  # % N-1 gaps covered
    "staff_satisfaction": >=4.0,  # Survey score
    "deployment_time": "<2 weeks",
}
```

---

## Workflow Diagram

```
START
  │
  ├─→ [1] Validation & Readiness Check
  │     └─→ FAIL? → Request Manual Review → END
  │
  ├─→ [2] Contingency Simulation (N-1/N-2)
  │     └─→ FAIL? → Activate Sacrifice Hierarchy → RETRY [1]
  │
  ├─→ [3] Early Warning Assessment (parallel)
  │     └─→ CRITICAL? → Alert + Request Review → END
  │
  ├─→ [4] Unified Risk Synthesis
  │     └─→ TOO_HIGH? → Defer 24h → END
  │
  ├─→ [5] Schedule Generation (Backend)
  │     └─→ TIMEOUT? → Fallback to Greedy → [6]
  │
  ├─→ [6] Post-Generation Validation
  │     └─→ FAIL? → Review Issues → Approve/Reject
  │
  ├─→ [7] Human Review & Approval
  │     └─→ REJECT? → Adjustment Loop → [1]
  │         APPROVE? ↓
  │
  ├─→ [8] Deploy Schedule
  │     └─→ Monitor Metrics
  │
  └─→ END (Success)
```

---

## Related Workflows

- **WORKFLOW_SWAP_EXECUTION.md**: Handle schedule modifications
- **WORKFLOW_COMPLIANCE_CHECK.md**: Validate existing schedule
- **WORKFLOW_RESILIENCE_ASSESSMENT.md**: Monitor system health

---

**Last Updated**: 2025-12-31
**Version**: 1.0
**Tested**: Yes, with 100+ schedules
