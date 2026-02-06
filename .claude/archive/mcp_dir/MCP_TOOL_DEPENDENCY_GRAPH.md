# MCP Tool Dependency Graph

**Status**: Comprehensive tool orchestration framework
**Version**: 1.0
**Last Updated**: 2025-12-31
**Purpose**: Document all 34+ MCP tool dependencies for proper sequencing in workflows

---

## Executive Summary

The Residency Scheduler MCP server exposes 34+ specialized tools organized into 10 functional categories. Understanding tool dependencies is critical for:
- **Workflow Design**: Proper sequencing prevents orphaned dependencies
- **Error Recovery**: Fallback strategies when dependencies fail
- **Performance**: Parallel execution of independent tools
- **Safety**: Validation before destructive operations

---

## Tool Categories and Dependencies

### Category 1: Core Scheduling Tools (5 tools)

**Functions**: Basic schedule operations and validation

```
validate_schedule
├─ Depends on: None (read-only)
├─ Used by: detect_conflicts, run_contingency_analysis
├─ Safety: TIER 1 (read-only)
└─ Parallelizable: Yes

detect_conflicts
├─ Depends on: validate_schedule (optional)
├─ Used by: run_contingency_analysis
├─ Safety: TIER 1 (read-only)
└─ Parallelizable: Yes

run_contingency_analysis
├─ Depends on: validate_schedule, detect_conflicts
├─ Used by: get_defense_level
├─ Safety: TIER 2 (scenario analysis, no apply)
└─ Parallelizable: Yes

analyze_swap_candidates
├─ Depends on: validate_schedule, detect_conflicts
├─ Used by: swap execution workflow
├─ Safety: TIER 1 (read-only analysis)
└─ Parallelizable: Yes

validate_schedule_by_id (ConstraintService)
├─ Depends on: None (read-only, constraint engine)
├─ Used by: All validation workflows
├─ Safety: TIER 1 (read-only)
└─ Parallelizable: Yes
```

**Dependency Order for Schedule Generation**:
```
1. validate_schedule (baseline)
   ├─ 2. detect_conflicts (parallel)
   ├─ 3. validate_schedule_by_id (parallel)
   └─ 4. run_contingency_analysis (sequential, needs steps 1-3)
       └─ 5. analyze_swap_candidates (optional, after validation)
```

---

### Category 2: Resilience Framework Tools (12 tools)

**Functions**: Core resilience monitoring and contingency analysis

```
check_utilization_threshold
├─ Depends on: None (direct calculation)
├─ Used by: get_defense_level, circuit_breaker_tools
├─ Safety: TIER 1 (read-only)
└─ Feedback: Input to defense level assessment

run_contingency_analysis_deep
├─ Depends on: validate_schedule, check_utilization_threshold
├─ Used by: calculate_blast_radius, get_defense_level
├─ Safety: TIER 2 (scenario analysis)
└─ Complexity: O(n²) - expensive operation

calculate_blast_radius
├─ Depends on: run_contingency_analysis_deep
├─ Used by: get_unified_critical_index, sacrifice_hierarchy
├─ Safety: TIER 1 (read-only analysis)
└─ Criticality: High

execute_sacrifice_hierarchy
├─ Depends on: calculate_blast_radius, check_utilization_threshold
├─ Used by: Emergency response workflows
├─ Safety: TIER 2 (preview only, no apply)
└─ Warning: Destructive simulation

analyze_homeostasis
├─ Depends on: validate_schedule, get_schedule_status
├─ Used by: get_unified_critical_index
├─ Safety: TIER 1 (read-only)
└─ Output: Feedback loop health

get_behavioral_patterns
├─ Depends on: None (historical analysis)
├─ Used by: get_unified_critical_index, SPC analysis
├─ Safety: TIER 1 (read-only)
└─ Insight: Trend identification

analyze_le_chatelier
├─ Depends on: analyze_homeostasis, get_behavioral_patterns
├─ Used by: get_unified_critical_index
├─ Safety: TIER 1 (read-only)
└─ Theory: Equilibrium analysis

analyze_hub_centrality
├─ Depends on: get_behavioral_patterns
├─ Used by: get_unified_critical_index
├─ Safety: TIER 1 (read-only)
└─ Pattern: Network analysis

get_defense_level
├─ Depends on: check_utilization_threshold, run_contingency_analysis_deep
├─ Used by: All resilience workflows, circuit breaker
├─ Safety: TIER 1 (read-only status)
└─ Critical: System health metric

get_static_fallbacks
├─ Depends on: validate_schedule
├─ Used by: Emergency response, blast radius
├─ Safety: TIER 1 (read-only)
└─ Purpose: Pre-computed backups

check_mtf_compliance
├─ Depends on: validate_schedule, get_defense_level
├─ Used by: Military readiness workflows
├─ Safety: TIER 1 (read-only, military-specific)
└─ Domain: Military medical facility compliance

analyze_stigmergy
├─ Depends on: get_behavioral_patterns, analyze_homeostasis
├─ Used by: Self-organizing system analysis
├─ Safety: TIER 1 (read-only)
└─ Theory: Swarm intelligence
```

**Resilience Workflow Dependency Chain**:
```
┌─ check_utilization_threshold ────┐
│                                   ├─ get_defense_level
├─ run_contingency_analysis_deep ──┤
│                                   ├─ execute_sacrifice_hierarchy
└─ analyze_homeostasis ────────────┤
                                    └─ get_unified_critical_index
                                        └─ System-wide alerts
```

---

### Category 3: Early Warning Detection Tools (7 tools)

**Functions**: Burnout precursor detection using cross-disciplinary science

```
detect_burnout_precursors (STA/LTA)
├─ Depends on: None (time series analysis)
├─ Used by: get_unified_critical_index
├─ Safety: TIER 1 (read-only)
├─ Input: Behavioral signal time series
└─ Output: Severity level with alerts

run_spc_analysis (Western Electric Rules)
├─ Depends on: None (statistical analysis)
├─ Used by: get_unified_critical_index, predict_burnout_magnitude
├─ Safety: TIER 1 (read-only)
├─ Input: Weekly work hours
└─ Output: Process control violations

calculate_fire_danger_index (CFFDRS)
├─ Depends on: None (multi-temporal analysis)
├─ Used by: get_unified_critical_index
├─ Safety: TIER 1 (read-only)
├─ Input: Recent/monthly/yearly workload + satisfaction
└─ Output: FWI score + danger class

calculate_process_capability_tool (Six Sigma)
├─ Depends on: run_spc_analysis (optional)
├─ Used by: Quality assessment workflows
├─ Safety: TIER 1 (read-only)
├─ Input: Weekly hours with spec limits
└─ Output: Cp/Cpk indices

predict_burnout_magnitude
├─ Depends on: run_spc_analysis, calculate_fire_danger_index
├─ Used by: Risk assessment workflows
├─ Safety: TIER 1 (read-only)
├─ Input: Multiple signal types
└─ Output: Risk magnitude + interventions

calculate_batch_fire_danger
├─ Depends on: calculate_fire_danger_index
├─ Used by: Program-wide screening
├─ Safety: TIER 1 (read-only, bulk operation)
├─ Input: Multiple residents (batch)
└─ Output: Summary statistics + outliers

detect_workload_anomalies (Kalman filter)
├─ Depends on: None (anomaly detection)
├─ Used by: Trend analysis workflows
├─ Safety: TIER 1 (read-only)
├─ Input: Historical workload data
└─ Output: Deviation points + confidence
```

**Early Warning Workflow**:
```
Input: Time series data for all residents
   ├─ detect_burnout_precursors (seismic) ──────┐
   ├─ run_spc_analysis (control chart) ─────────┤
   ├─ calculate_fire_danger_index (CFFDRS) ─────┤
   ├─ detect_workload_anomalies (Kalman) ───────┤
   └─ calculate_process_capability_tool ────────┤
       └─ predict_burnout_magnitude (aggregation)
           └─ get_unified_critical_index (final synthesis)
               └─ Alert generation + interventions
```

---

### Category 4: Fatigue & Burnout Analysis Tools (7 tools)

**Functions**: FRMS, creep-fatigue, contagion modeling, and advanced analytics

```
run_frms_assessment (Fatigue Risk Management)
├─ Depends on: validate_schedule, run_spc_analysis
├─ Used by: get_unified_critical_index
├─ Safety: TIER 1 (read-only)
├─ Input: Schedule with fatigue metrics
└─ Output: Risk assessment + recommendations

scan_team_fatigue
├─ Depends on: run_frms_assessment
├─ Used by: Program-wide fatigue screening
├─ Safety: TIER 1 (read-only, batch)
├─ Input: Team roster
└─ Output: Risk distribution + priorities

assess_creep_fatigue (Larson-Miller)
├─ Depends on: run_frms_assessment, calculate_fire_danger_index
├─ Used by: get_unified_critical_index
├─ Safety: TIER 1 (read-only)
├─ Input: Long-term stress history
└─ Output: Creep stage + time-to-failure prediction

calculate_burnout_rt (Epidemiology - SIR)
├─ Depends on: None (network analysis)
├─ Used by: simulate_burnout_contagion, get_unified_critical_index
├─ Safety: TIER 1 (read-only)
├─ Input: Burned-out provider IDs
└─ Output: Rt value + intervention level

simulate_burnout_spread (SIR simulation)
├─ Depends on: calculate_burnout_rt
├─ Used by: Trajectory prediction
├─ Safety: TIER 1 (read-only, simulation)
├─ Input: Initial infected + parameters
└─ Output: Weekly trajectory + peak timing

simulate_burnout_contagion (SIS network diffusion)
├─ Depends on: calculate_burnout_rt, get_behavioral_patterns
├─ Used by: Network-based intervention planning
├─ Safety: TIER 1 (read-only, network simulation)
├─ Input: Network structure + parameters
└─ Output: Superspreaders + intervention targets

assess_immune_response (Artificial Immune System)
├─ Depends on: None (pattern recognition)
├─ Used by: Adaptive response workflows
├─ Safety: TIER 1 (read-only)
├─ Input: Constraint violations
└─ Output: Immune response patterns
```

**Burnout Analysis Dependency Chain**:
```
┌─────────────────────────────────────────┐
│  Input: Schedule + Historical Data      │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   FRMS Track          Epidemiology Track
        │                     │
     run_frms           calculate_burnout_rt
        │                     │
    scan_team           simulate_burnout_contagion
        │                     │
  assess_creep         Network intervention plan
        │                     │
        └──────────────┬──────┘
                       │
            get_unified_critical_index
```

---

### Category 5: Optimization & Analytics Tools (6 tools)

**Functions**: Staffing, quality metrics, equity analysis, and capacity planning

```
optimize_erlang_coverage
├─ Depends on: None (queuing theory calculation)
├─ Used by: Staffing optimization workflows
├─ Safety: TIER 1 (read-only)
├─ Input: Arrival rate + service time
└─ Output: Recommended staff + service levels

calculate_equity_metrics
├─ Depends on: validate_schedule
├─ Used by: Fairness assessment
├─ Safety: TIER 1 (read-only)
├─ Input: Hours per provider
└─ Output: Gini coefficient + recommendations

calculate_process_capability
├─ Depends on: run_spc_analysis (optional)
├─ Used by: Quality assessment
├─ Safety: TIER 1 (read-only)
├─ Input: Data with spec limits
└─ Output: Cp/Cpk + sigma level

analyze_supply_demand_cycles (Lotka-Volterra)
├─ Depends on: get_behavioral_patterns, validate_schedule
├─ Used by: Capacity planning
├─ Safety: TIER 1 (read-only)
├─ Input: Supply/demand history
└─ Output: Cycle analysis + equilibrium

predict_capacity_crunch (Predator-prey dynamics)
├─ Depends on: analyze_supply_demand_cycles
├─ Used by: Resource planning
├─ Safety: TIER 1 (read-only)
├─ Input: Historical trends
└─ Output: Crunch timing + severity

analyze_workload_trend (Kalman filter)
├─ Depends on: None (time series smoothing)
├─ Used by: Trend-based planning
├─ Safety: TIER 1 (read-only)
├─ Input: Workload history
└─ Output: Trend line + forecast
```

**Optimization Workflow**:
```
Staffing Optimization:
  Erlang Coverage → Service Level Recommendations

Quality Assurance:
  Process Capability → Sigma Level Assessment

Equity Analysis:
  Schedule → Equity Metrics → Rebalancing Plan

Capacity Planning:
  Supply/Demand → Cycle Analysis → Crunch Prediction
```

---

### Category 6: Composite Resilience Tools (4 tools)

**Functions**: Aggregate multiple signals into unified risk scores

```
get_unified_critical_index
├─ Depends on: (Aggregates all below)
│   ├─ run_contingency_analysis_deep (40% weight)
│   ├─ analyze_hub_centrality (35% weight)
│   ├─ calculate_burnout_rt (25% weight)
│   ├─ detect_burnout_precursors
│   ├─ run_spc_analysis
│   ├─ calculate_fire_danger_index
│   ├─ assess_creep_fatigue
│   └─ Plus: All early warning tools
├─ Used by: System-level decision making
├─ Safety: TIER 1 (read-only aggregation)
├─ Frequency: Compute daily/on-demand
└─ Output: Overall index + risk patterns + recommendations

calculate_recovery_distance
├─ Depends on: validate_schedule, run_contingency_analysis_deep
├─ Used by: Schedule fragility assessment
├─ Safety: TIER 1 (read-only, graph search)
├─ Complexity: O(n³) - expensive
└─ Output: RD metrics + fragility score

assess_creep_fatigue (See Category 4)

analyze_transcription_triggers
├─ Depends on: get_behavioral_patterns, validate_schedule
├─ Used by: Adaptive constraint management
├─ Safety: TIER 1 (read-only)
├─ Input: Constraint violations + environmental signals
└─ Output: TF activity + constraint modifications
```

**Unified Risk Index Assembly**:
```
Contingency (40%)
├─ N-1/N-2 Analysis
├─ Blast Radius
└─ Recovery Distance

Hub Analysis (35%)
├─ Network Centrality
├─ Superspreader Identification
└─ Cascade Risk

Epidemiology (25%)
├─ Burnout Rt
├─ Contagion Risk
└─ Spread Trajectory

Final Assembly:
  Weighted Sum → Risk Patterns → Intervention Ranking
```

---

### Category 7: Specialized Analytics Tools (8 tools)

**Functions**: Cross-disciplinary scientific analysis

```
detect_schedule_cycles (FFT Fourier analysis)
├─ Depends on: validate_schedule
├─ Used by: Periodicity assessment
├─ Safety: TIER 1 (read-only)
├─ Input: Schedule time series
└─ Output: Dominant periods + harmonics

analyze_harmonic_resonance
├─ Depends on: detect_schedule_cycles
├─ Used by: Feedback loop detection
├─ Safety: TIER 1 (read-only)
├─ Input: Signal interactions
└─ Output: Resonance patterns

calculate_schedule_entropy (Thermodynamics)
├─ Depends on: validate_schedule
├─ Used by: Disorder assessment
├─ Safety: TIER 1 (read-only)
├─ Input: Assignment distribution
└─ Output: Shannon entropy + disorder level

analyze_phase_transitions
├─ Depends on: validate_schedule, check_utilization_threshold
├─ Used by: Criticality assessment
├─ Safety: TIER 1 (read-only)
├─ Input: System state progression
└─ Output: Phase transition risk

get_entropy_monitor_state
├─ Depends on: calculate_schedule_entropy
├─ Used by: Ongoing monitoring
├─ Safety: TIER 1 (read-only)
└─ Output: Current entropy vs. threshold

analyze_nash_stability (Game theory)
├─ Depends on: get_behavioral_patterns, validate_schedule
├─ Used by: Incentive alignment analysis
├─ Safety: TIER 1 (read-only)
├─ Input: Strategy space
└─ Output: Equilibrium points + deviations

detect_coordination_failures (Game theory)
├─ Depends on: analyze_nash_stability
├─ Used by: Communication gap analysis
├─ Safety: TIER 1 (read-only)
├─ Input: Coordination game matrix
└─ Output: Failure points + interventions

calculate_schedule_energy (Hopfield networks)
├─ Depends on: validate_schedule
├─ Used by: Attractor landscape analysis
├─ Safety: TIER 1 (read-only)
├─ Input: Schedule configuration
└─ Output: Energy value + stability
```

---

### Category 8: Time Crystal & Anti-Churn Tools (5 tools)

**Functions**: Minimize schedule churn while maintaining compliance

```
get_time_crystal_health
├─ Depends on: validate_schedule, detect_schedule_cycles
├─ Used by: Anti-churn monitoring
├─ Safety: TIER 1 (read-only)
├─ Output: Health score + rigidity metrics

calculate_time_crystal_objective
├─ Depends on: validate_schedule
├─ Used by: Optimization guidance
├─ Safety: TIER 1 (read-only)
├─ Output: Anti-churn score + target

analyze_schedule_periodicity
├─ Depends on: detect_schedule_cycles
├─ Used by: Pattern-based optimization
├─ Safety: TIER 1 (read-only)
├─ Output: Periodic patterns + stability

analyze_schedule_rigidity
├─ Depends on: validate_schedule, get_time_crystal_health
├─ Used by: Flexibility assessment
├─ Safety: TIER 1 (read-only)
├─ Output: Rigidity score (0-1)

get_checkpoint_status
├─ Depends on: validate_schedule
├─ Used by: Boundary monitoring
├─ Safety: TIER 1 (read-only)
├─ Output: Checkpoint states + validity
```

---

### Category 9: Risk Analysis Tools (5 tools)

**Functions**: Value-at-Risk and disruption scenario analysis

```
calculate_workload_var
├─ Depends on: validate_schedule, detect_workload_anomalies
├─ Used by: Stress testing
├─ Safety: TIER 1 (read-only)
├─ Output: VaR metrics at confidence levels

calculate_coverage_var
├─ Depends on: validate_schedule, run_contingency_analysis_deep
├─ Used by: Contingency planning
├─ Safety: TIER 1 (read-only)
├─ Output: Coverage loss VaR

calculate_conditional_var
├─ Depends on: calculate_workload_var
├─ Used by: Worst-case analysis
├─ Safety: TIER 1 (read-only)
├─ Output: Tail risk assessment

simulate_disruption_scenarios
├─ Depends on: validate_schedule, run_contingency_analysis_deep
├─ Used by: Scenario planning
├─ Safety: TIER 2 (scenario, no apply)
├─ Output: Impact matrices + RD metrics

get_behavioral_patterns (See Category 2)
```

---

### Category 10: Auxiliary Systems (4 tools)

**Functions**: Circuit breaker, deployment, and background tasks

```
check_circuit_breakers
├─ Depends on: get_defense_level, check_utilization_threshold
├─ Used by: System protection
├─ Safety: TIER 1 (read-only status)
├─ Output: Breaker states + health

get_breaker_health
├─ Depends on: check_circuit_breakers
├─ Used by: Health dashboard
├─ Safety: TIER 1 (read-only)
└─ Output: Detailed health metrics

test_half_open_breaker (HALF_OPEN → CLOSED recovery test)
├─ Depends on: check_circuit_breakers
├─ Used by: Recovery testing
├─ Safety: TIER 2 (test, monitoring)
└─ Output: Test results + recommendations

override_circuit_breaker (MANUAL mode)
├─ Depends on: check_circuit_breakers
├─ Used by: Emergency override
├─ Safety: TIER 3 (requires approval)
├─ Warning: Disables automatic protection
└─ Output: Confirmation + audit trail
```

---

## Dependency Tiers & Safety Levels

### Execution Safety Tiers

```
TIER 1 (Analysis/Read-Only) - Autonomous Execution
├─ All validation tools
├─ All detection/analysis tools
├─ All monitoring tools
├─ All read-only queries
└─ Safe to execute without approval (34 tools)

TIER 2 (Generation/Simulation) - Review Required
├─ Contingency analysis
├─ Sacrifice hierarchy (preview)
├─ Disruption simulation
├─ Circuit breaker testing
└─ Execute with caution, review results before applying

TIER 3 (Destructive/Override) - Human Only
├─ Override circuit breaker (MANUAL mode)
├─ Any tool that would modify schedules
├─ Direct database operations (blocked from MCP)
└─ Never execute autonomously
```

### Parallelization Matrix

Tools that can run in parallel (no dependencies):

```
Group A (Core Analysis) - All parallel:
├─ validate_schedule
├─ detect_conflicts
├─ analyze_swap_candidates
├─ get_schedule_status
└─ get_compliance_summary

Group B (Early Warning) - All parallel:
├─ detect_burnout_precursors
├─ run_spc_analysis
├─ calculate_fire_danger_index
├─ calculate_workload_var
└─ detect_workload_anomalies

Group C (Specialized) - All parallel:
├─ detect_schedule_cycles
├─ calculate_schedule_entropy
├─ optimize_erlang_coverage
├─ calculate_equity_metrics
└─ analyze_nash_stability

Sequential Dependencies (cannot parallelize):
├─ detect_conflicts → run_contingency_analysis
├─ calculate_fire_danger_index → get_unified_critical_index
└─ simulate_burnout_spread → Rt-based planning
```

---

## Circular Dependency Detection

The following patterns must be avoided:

```
ANTI-PATTERN 1: Validation Loop
X: validate_schedule → detect_conflicts → run_contingency_analysis → (circular back to validate_schedule)
✓ Solution: Use separate analysis branches, no feedback to validator

ANTI-PATTERN 2: Feedback Loop
X: get_defense_level → circuit_breaker → execute_sacrifice → (modifies utilization)
✓ Solution: One-directional signal flow, circuit breaker is idempotent

ANTI-PATTERN 3: Aggregation Cycle
X: get_unified_critical_index → (reads all early warning) → early warning tools → (reads from unified index)
✓ Solution: Unidirectional aggregation, early warning tools independent
```

**Validation Function**:
```python
def detect_circular_dependencies(tool_graph: Dict[str, List[str]]) -> List[List[str]]:
    """
    Detect circular dependencies in tool dependency graph.

    Args:
        tool_graph: Dict mapping tool_name -> list of dependencies

    Returns:
        List of circular paths found, or [] if none

    Algorithm: DFS cycle detection (O(V + E))
    """
    cycles = []
    visited = set()
    rec_stack = set()

    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in tool_graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, path)
            elif neighbor in rec_stack:
                cycles.append(path + [neighbor])

        rec_stack.remove(node)
        path.pop()

    for tool in tool_graph:
        if tool not in visited:
            dfs(tool, [])

    return cycles
```

---

## Dependency Validation Checklist

Before deploying a new tool or workflow:

- [ ] All declared dependencies exist in tool registry
- [ ] No circular dependencies detected
- [ ] All dependent tools are initialized before use
- [ ] Fallback behavior defined if dependency fails
- [ ] Error handling for missing dependencies
- [ ] Safety tier appropriate for use case
- [ ] Performance implications documented (execution time, resources)
- [ ] Integration tests passing for dependency chain
- [ ] Documentation updated with new dependencies

---

## Common Workflow Patterns

### Pattern 1: Validation → Analysis (Serial)
```
Recommended for: Schedule review
Time: ~500ms total
validate_schedule → detect_conflicts → run_contingency_analysis
├─ All data validated before next stage
├─ No assumptions made
└─ Safe for autonomous execution
```

### Pattern 2: Early Warning Batch (Parallel)
```
Recommended for: Daily resilience scanning
Time: ~150ms (parallel) vs 500ms (serial)
detect_burnout_precursors
run_spc_analysis
calculate_fire_danger_index
detect_workload_anomalies
predict_burnout_magnitude
└─ All execute simultaneously, aggregate at end
```

### Pattern 3: Resilience Assessment (Tiered)
```
Recommended for: Critical decision making
Tier 1: Fast checks (50ms)
  ├─ check_utilization_threshold
  └─ get_defense_level
Tier 2: Medium analysis (500ms)
  └─ run_contingency_analysis_deep
Tier 3: Full synthesis (200ms)
  └─ get_unified_critical_index
```

### Pattern 4: Risk Aggregation (Star topology)
```
Recommended for: System-wide monitoring
Central tool: get_unified_critical_index
Inputs from (all parallel):
├─ detect_burnout_precursors
├─ run_spc_analysis
├─ calculate_fire_danger_index
├─ assess_creep_fatigue
├─ calculate_burnout_rt
├─ analyze_hub_centrality
├─ run_contingency_analysis_deep
└─ analyze_le_chatelier
```

---

## Implementation Notes

### Error Propagation

```
Tool Execution Flow:

A → B → C (Sequential)
     ↓
   Error at B
     ↓
   Fallback to cached C data (if available)
   OR return degraded response with severity flag

A → {B, C, D} (Parallel)
        ↓
   Error at C
     ↓
   Continue with A, B, D; mark C as failed
   Aggregate results with warnings
```

### Performance Characteristics

| Tool | Latency | Complexity | Notes |
|------|---------|-----------|-------|
| validate_schedule | <50ms | O(n) | Linear in assignments |
| detect_conflicts | <50ms | O(n) | Linear in assignments |
| run_contingency_analysis | 100-500ms | O(n²) | Quadratic in scope |
| get_unified_critical_index | 200-300ms | O(n) | Aggregation only |
| simulate_burnout_spread | 1-2s | O(n×weeks) | Simulation heavy |
| calculate_recovery_distance | 2-5s | O(n³) | Graph search expensive |

### Timeout Recommendations

```python
TOOL_TIMEOUTS = {
    # Fast tools (no timeout needed)
    "validate_schedule": 0.1,
    "detect_conflicts": 0.1,
    "run_spc_analysis": 0.05,

    # Medium tools
    "run_contingency_analysis": 1.0,
    "get_unified_critical_index": 0.5,
    "calculate_fire_danger_index": 0.1,

    # Slow tools
    "run_contingency_analysis_deep": 5.0,
    "simulate_burnout_spread": 10.0,
    "calculate_recovery_distance": 30.0,
}
```

---

## Graph Visualization

**ASCII Graph of Top 10 Critical Dependencies**:

```
                    ┌─────────────────────────┐
                    │  get_unified_critical_  │
                    │       index             │
                    └──────────────┬──────────┘
                                   │
                 ┌─────────────────┼─────────────────┐
                 │                 │                 │
        ┌────────▼────────┐ ┌──────▼──────┐ ┌──────▼──────┐
        │    Contingency  │ │    Hub      │ │  Burnout    │
        │    Analysis (40)│ │ Centrality  │ │    Rt (25)  │
        │                │ │   (35)      │ │             │
        └────────┬────────┘ └──────┬──────┘ └──────┬──────┘
                 │                 │                │
        ┌────────▼─────┐  ┌────────▼────┐  ┌─────▼──────┐
        │  Validation  │  │ Behavioral  │  │  Network   │
        │  + Detection │  │  Patterns   │  │ Analysis   │
        └──────────────┘  └─────────────┘  └────────────┘
```

---

## References

- SESSION_8_MCP: Complete tool inventory (34+ tools)
- Cross-Disciplinary Resilience Framework: Theory backing
- MCP_TOOLS_REFERENCE.md: Individual tool documentation
- ACGME_COMPLIANCE.md: Regulatory context

---

**Last Reviewed**: 2025-12-31
**Next Update**: Quarterly or after tool additions
**Maintainer**: MCP Integration Team
