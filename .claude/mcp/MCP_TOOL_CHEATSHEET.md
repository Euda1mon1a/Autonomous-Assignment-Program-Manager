# MCP Tool Cheatsheet

**Purpose**: Quick reference for MCP tools and workflows (fits on screen)
**Audience**: Operators, coordinators, AI agents
**Version**: 1.0
**Last Updated**: 2025-12-31

---

## The 34+ Tools at a Glance

### Core Scheduling (5 tools)

| Tool | Input | Output | Time | Use |
|------|-------|--------|------|-----|
| **validate_schedule** | Date range | Compliance report | 50ms | ✓ First, always |
| **detect_conflicts** | Schedule ID | 6 conflict types | 50ms | ✓ Parallel with validate |
| **run_contingency** | Date range | N-1/N-2 gaps | 2-3s | ✓ Schedule generation |
| **analyze_swaps** | Person ID, assignment | Candidate scores | 100ms | ✓ Swap matching |
| **validate_by_id** | Schedule ID | Constraint check | 100ms | ✓ ConstraintService |

### Early Warning (7 tools)

| Tool | Input | Output | SLA | Use |
|------|-------|--------|-----|-----|
| **detect_precursors** | Person ID, signals | STA/LTA alerts | 100ms | Daily scan |
| **run_spc_analysis** | Weekly hours | Western E. rules | 50ms | Trend detection |
| **fire_danger** | Recent/monthly/yearly | FWI score | 50ms | ⚠️ Multi-temporal |
| **process_capability** | Hours data | Cp/Cpk indices | 20ms | Quality metric |
| **burnout_magnitude** | Multiple signals | Risk estimate | 100ms | Synthesis |
| **batch_fire_danger** | All residents | Summary stats | 500ms | Program screening |
| **workload_anomalies** | History | Deviation points | 100ms | Trend analysis |

### Resilience (12 tools)

| Tool | Input | Output | Use |
|------|-------|--------|-----|
| **utilization_check** | Capacity numbers | GREEN/YELLOW/RED | First check |
| **contingency_deep** | Schedule + dates | Detailed N-1/N-2 | Generation |
| **blast_radius** | Schedule, people | Impact scope | Identify critical |
| **sacrifice_hierarchy** | System state | Load shedding plan | Emergency preview |
| **homeostasis** | Schedule | Feedback loops | Stability check |
| **hub_centrality** | Network | Central people | Dependency map |
| **le_chatelier** | System state | Equilibrium shift | Theory check |
| **behavioral_patterns** | Historical | Trends | Input to unified |
| **get_defense_level** | Thresholds | 1-5 defense | System status |
| **get_fallbacks** | Schedule | Backup plans | Contingency |
| **check_mtf_compliance** | Schedule | Military readiness | DRRS category |
| **analyze_stigmergy** | Behavior | Swarm patterns | Emergent behavior |

### Epidemiology (3 tools)

| Tool | Input | Output | Use |
|------|-------|--------|-----|
| **calculate_rt** | Burned-out IDs | Rt value | Transmission rate |
| **simulate_spread** | Initial infected | Trajectory | 52-week projection |
| **simulate_contagion** | Network | Superspreaders | Network targets |

### Optimization (6 tools)

| Tool | Input | Output | Use |
|------|-------|--------|-----|
| **erlang_coverage** | Arrival rate, time | Staffing needed | Specialist coverage |
| **equity_metrics** | Hours/person | Gini coefficient | Fairness check |
| **process_capability** | Data + limits | Cpk indices | Quality score |
| **supply_demand** | History | Cycles detected | Capacity planning |
| **capacity_crunch** | Trends | Crunch timing | Alert early |
| **workload_trend** | History | Kalman filter line | Forecast |

### Composite (4 tools)

| Tool | Input | Output | Confidence |
|------|-------|--------|------------|
| **unified_critical** | All signals | Risk index (0-100) | 0.60-0.75 |
| **recovery_distance** | Schedule | RD metrics | 0.70 |
| **assess_creep** | Stress history | LMP score | 0.70 |
| **transcription** | Constraints | TF activity | 0.65 |

### Fatigue (7 tools)

| Tool | Input | Output | Notes |
|------|-------|--------|-------|
| **run_frms** | Schedule | FRMS score | Fatigue Risk Management |
| **scan_team_fatigue** | Team | Risk distribution | Batch operation |
| **assess_creep_fatigue** | Stress history | Larson-Miller param | Pre-failure detection |
| **burnout_rt** | Burned-out IDs | Transmission rate | Epidemiology |
| **simulate_spread** | Initial | 52-week trajectory | SIR model |
| **simulate_contagion** | Network | Superspreaders | SIS model |
| **assess_immune** | Violations | Pattern response | Adaptive response |

### Specialized (8 tools)

| Tool | Domain | Input | Output |
|------|--------|-------|--------|
| **detect_cycles** | FFT/Fourier | Time series | Periodicity |
| **harmonic_resonance** | Feedback loops | Signals | Resonance patterns |
| **schedule_entropy** | Thermodynamics | Assignments | Shannon entropy |
| **phase_transitions** | Phase changes | State progression | Criticality risk |
| **entropy_monitor** | Monitoring | Current entropy | Status vs threshold |
| **nash_stability** | Game theory | Strategies | Equilibrium points |
| **coordination_failures** | Game theory | Game matrix | Communication gaps |
| **schedule_energy** | Hopfield networks | Configuration | Energy value |

### Time Crystal (5 tools)

| Tool | Input | Output | Purpose |
|------|-------|--------|---------|
| **time_crystal_health** | Schedule | Health score | Anti-churn monitoring |
| **time_crystal_objective** | Schedule | Anti-churn score | Optimization target |
| **schedule_periodicity** | Time series | Periods found | Pattern-based scheduling |
| **schedule_rigidity** | Schedule | Rigidity 0-1 | Flexibility measure |
| **checkpoint_status** | Schedule | Boundary states | Discrete progress |

### Risk Analysis (5 tools)

| Tool | Input | Output | Use |
|------|-------|--------|-----|
| **workload_var** | Schedule | VaR metrics | Stress testing |
| **coverage_var** | Schedule | Coverage loss VaR | Contingency planning |
| **conditional_var** | VaR data | Tail risk | Worst case |
| **disruption_scenarios** | Schedule + types | Impact matrix | Scenario analysis |

### Auxiliary (4 tools)

| Tool | Purpose | Use |
|------|---------|-----|
| **check_circuit_breakers** | Tool health | System protection |
| **get_breaker_health** | Detailed status | Health dashboard |
| **test_half_open** | Recovery test | Testing recovery |
| **override_breaker** | Manual control | Emergency only |

---

## 4 Essential Workflows

### 1. Schedule Generation (12-25s)

```
Phase 1 (0.5s): Baseline Validation
  ├─ validate_schedule ✓ Required >= 0.85
  ├─ detect_conflicts
  └─ check_utilization
  → If FAIL: Request manual fix

Phase 2 (2-3s): Contingency
  ├─ run_contingency_deep
  ├─ calculate_blast_radius
  └─ execute_sacrifice (preview)
  → If >50% gaps: WARN

Phase 3 (1-2s): Early Warning (parallel)
  ├─ detect_precursors
  ├─ run_spc_analysis
  ├─ fire_danger_index
  └─ predict_magnitude

Phase 4 (0.5s): Risk Index
  └─ get_unified_critical_index
  → If risk > 70: Request review

Phase 5 (5-10s): Generate
  └─ Backend /schedules/generate

Phase 6 (1-2s): Post-validate
  ├─ validate_schedule (new)
  ├─ detect_conflicts
  └─ run_contingency
  → If NOT compliant: Show violations

Phase 7: Human Review & Approve

Phase 8: Deploy
```

**Confidence Thresholds**:
- Phase 1: >= 0.85
- Phase 2: >= 0.70
- Phase 6: >= 0.90 (required)

---

### 2. Compliance Check (2-3s)

```
Phase 1: ACGME Rules (parallel)
  ├─ validate_schedule
  ├─ validate_by_id
  → Report violations

Phase 2: Detailed (parallel)
  ├─ detect_conflicts
  ├─ workload_trend
  └─ supply_demand_cycles

Phase 3: Advanced (parallel)
  ├─ run_spc_analysis
  ├─ process_capability
  ├─ equity_metrics
  └─ utilization_check

Phase 4: Synthesis
  ├─ Aggregate violations
  ├─ Rank by severity
  └─ Recommendations

OUTPUT: Score 0-100
├─ >= 85 → Deploy OK
├─ 70-85 → Coordinator review
└─ < 70 → Fix required
```

---

### 3. Swap Execution (2-5s + review)

```
Phase 1: Validate (0.5s)
  └─ Check requester, assignment, compliance

Phase 2: Candidates (0.5s)
  └─ analyze_swap_candidates
  → Rank top 3-5

Phase 3: Impact (1s, parallel)
  ├─ detect_conflicts
  ├─ validate_schedule (simulated)
  └─ run_contingency
  → Check ACGME compliance maintained

Phase 4: Human Review
  ├─ Requester selects candidate
  └─ Mutual consent required

Phase 5: Execute (< 1s)
  ├─ Apply swap
  ├─ Log audit
  └─ Notify parties

Rollback: 24-hour window available
```

---

### 4. Resilience Assessment (5-8s)

```
Phase 1 (0.5s): Quick Status
  ├─ check_utilization_threshold
  ├─ check_circuit_breakers
  └─ get_defense_level
  → Quick health snapshot

Phase 2 (2-3s): Contingency
  ├─ run_contingency_deep
  ├─ calculate_blast_radius
  └─ execute_sacrifice (preview)
  → Identify critical personnel

Phase 3 (1-2s): Epidemiology
  ├─ calculate_rt
  └─ simulate_contagion
  → Network intervention plan

Phase 4 (1-2s): Analytics (parallel)
  ├─ detect_precursors
  ├─ run_spc_analysis
  ├─ fire_danger_index
  ├─ assess_creep_fatigue
  └─ 4 more specialized tools

Phase 5 (0.5s): Synthesis
  └─ get_unified_critical_index
  → Risk level, recommendations

OUTPUT: Dashboard + Alerts
```

---

## Confidence Levels Quick Guide

```
0.0-0.25  RED    ✗ Don't trust - escalate to human
0.25-0.50 ORANGE ⚠️ Low confidence - validate with 2nd tool
0.50-0.75 YELLOW ≈ Moderate - OK for routine decisions
0.75-0.90 GREEN  ✓ High - suitable for autonomous use
0.90-1.0  BLUE   ✓✓ Very High - full confidence

Thresholds by Workflow:
├─ Schedule generation: Phase 1 >= 0.85, Phase 6 >= 0.90
├─ Compliance check: >= 0.85 for deployment
├─ Swap execution: >= 0.75 for all phases
└─ Resilience: >= 0.65 for overall index
```

---

## Error Handling Quick Reference

| Error | Tool | Recovery |
|-------|------|----------|
| **Timeout** | Any | Retry 2x, use cache, fallback |
| **Compliance fail** | validate_schedule | Show violations, request fix |
| **No candidates** | analyze_swaps | Escalate to coordinator |
| **High risk** | unified_critical | Request human review |
| **Circuit open** | Any | Use fallback, alert coord |
| **Data missing** | Any | Use defaults, mark degraded |

---

## Health Monitoring

```
Tool Status Display:
├─ GREEN:   Healthy (< SLA latency)
├─ YELLOW:  Degraded (near SLA, using cache)
├─ RED:     Critical (timeout, failures)
└─ GRAY:    Unavailable (circuit open)

Circuit Breaker States:
├─ CLOSED:     Normal operation
├─ OPEN:       Too many failures, fast-fail
└─ HALF_OPEN:  Testing recovery

Alert Conditions:
├─ CRITICAL:   Tool < 0.40 health → Page on-call
├─ HIGH:       Tool < 0.65 health → Email coordinator
├─ MEDIUM:     Tool < 0.80 health → Dashboard alert
└─ LOW:        Log for review
```

---

## Common Commands

### Check Schedule Compliance
```
1. Run: compliance_check workflow
   └─ Outputs: score, violations, recommendations
2. If score >= 85: OK to deploy
3. If score 70-85: Coordinator review
4. If score < 70: Request fixes
```

### Generate New Schedule
```
1. Run: schedule_generation workflow
   └─ 6 phases, ~20 seconds
2. Review: Phase 1-4 results for risks
3. Approve: Coordinator signs off
4. Deploy: Update schedule
5. Monitor: Watch for issues
```

### Execute Swap Request
```
1. Run: swap_execution Phase 1-3
2. Show: Top 3 candidates
3. Get: Mutual consent
4. Approve: Coordinator signature
5. Execute: Apply swap + log audit
6. Optional: Rollback within 24h
```

### Assess System Health
```
1. Run: resilience_assessment
2. Output: 5 risk domains
3. If index > 70: Alert coordinator
4. Top priorities: [list]
5. Recommendations: [list]
```

---

## Tool Dependency Basics

```
Can run in parallel (independent):
├─ All Phase 1 validation tools
├─ All Phase 3 early warning tools
└─ Most Phase 4 analytics tools

Must run serial (dependent):
├─ generate_schedule → validate_schedule
├─ contingency → blast_radius → sacrifice
└─ Rt → simulate_contagion

Critical path (parallelized):
├─ Contingency (2-3s, serial)
├─ Early warning (1-2s, parallel = 1-2s vs 5s)
└─ Saves ~3-4 seconds per workflow
```

---

## Decision Matrix

**Should I run this tool?**

```
Is it in the workflow? YES → Run it
  └─ Is tool healthy? YES → Execute
      └─ Confidence >= threshold? YES → Use result
          └─ Take action based on result
    └─ NO → Use fallback (cache/simplified)
  └─ NO → Skip tool

  └─ NO (not in workflow) → Don't run (wastes time)
```

---

## SLA Targets

| Tool Category | Target Latency | Timeout | Alert if > |
|---------------|----------------|---------|-----------|
| Core Scheduling | < 100ms | 5s | 150ms |
| Early Warning | < 100ms | 5s | 200ms |
| Resilience | < 1-2s | 10s | 3-4s |
| Optimization | < 500ms | 5s | 1s |
| Analytics | < 100ms | 2s | 150ms |

---

## Resources

- **MCP_TOOL_DEPENDENCY_GRAPH.md**: Full dependency detail
- **MCP_CONFIDENCE_FRAMEWORK.md**: Confidence calculation rules
- **MCP_TOOL_HEALTH_MONITOR.md**: Health check details
- **WORKFLOW_*.md**: 4 detailed workflow guides
- **MCP_ORCHESTRATION_GUIDE.md**: Advanced patterns

---

**Quick Start**: Read this page (5 min), then pick a workflow

**Print This**: Format optimized for single page printing

**Version**: 1.0
**Last Updated**: 2025-12-31
