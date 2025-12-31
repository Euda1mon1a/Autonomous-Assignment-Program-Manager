# MCP Tools Quick Reference
## Fast lookup for 81 MCP scheduling tools

---

## Tool Categories

### Core Scheduling (5)
```
validate_schedule_tool             - ACGME compliance validation (date range)
validate_schedule_by_id_tool       - ACGME compliance validation (by ID)
run_contingency_analysis_tool      - Emergency impact analysis
detect_conflicts_tool              - Find scheduling conflicts
analyze_swap_candidates_tool       - Find swap options
```

### Async Task Management (4)
```
start_background_task_tool         - Start long-running background job
get_task_status_tool               - Poll task status & results
cancel_task_tool                   - Stop running/queued task
list_active_tasks_tool             - View active background tasks
```

### Resilience - Tier 1 (3)
```
check_utilization_threshold_tool   - 80% queuing theory buffer
get_defense_level_tool             - 5-level defense readiness
run_contingency_analysis_resilience_tool - N-1/N-2 power grid analysis
```

### Resilience - Tier 2 (4)
```
get_static_fallbacks_tool          - Precomputed backup schedules
execute_sacrifice_hierarchy_tool    - Load shedding triage
analyze_homeostasis_tool           - Feedback loop equilibrium
calculate_blast_radius_tool        - Failure zone isolation
```

### Resilience - Tier 3 (8)
```
analyze_le_chatelier_tool          - Chemistry equilibrium shifts
analyze_hub_centrality_tool        - Network criticality
assess_cognitive_load_tool         - Burnout risk (psychology)
get_behavioral_patterns_tool       - Schedule behavior analysis
analyze_stigmergy_tool             - Swarm intelligence patterns
run_spc_analysis_tool              - Western Electric drift detection
calculate_process_capability_tool  - Six Sigma Cp/Cpk indices
optimize_erlang_coverage_tool      - Telecom queuing optimization
```

### Burnout Epidemiology (4)
```
calculate_burnout_rt_tool          - SIR reproduction number
simulate_burnout_spread_tool       - Network contagion dynamics
simulate_burnout_contagion_tool    - Multi-agent intervention
detect_burnout_precursors_tool     - STA/LTA seismic early warning
```

### Early Warning Tools (4)
```
detect_burnout_precursors_tool     - STA/LTA acceleration threshold
predict_burnout_magnitude_tool     - Magnitude estimation
run_spc_analysis_tool              - Western Electric rules (8)
calculate_fire_danger_index_tool   - CFFDRS multi-temporal model
calculate_batch_fire_danger_tool   - Batch fire danger assessment
```

### Deployment (9)
```
validate_deployment_tool           - Pre-deployment validation
run_security_scan_tool             - Security vulnerability scan
run_smoke_tests_tool               - Quick sanity tests
promote_to_production_tool         - Production promotion
rollback_deployment_tool           - Emergency rollback
get_deployment_status_tool         - Deployment health
list_deployments_tool              - View deployment history
benchmark_solvers_tool             - Solver performance
benchmark_constraints_tool         - Constraint overhead
```

### Empirical Testing (5)
```
benchmark_solvers_tool             - Constraint solver performance
benchmark_constraints_tool         - Individual constraint cost
ablation_study_tool                - Feature importance analysis
benchmark_resilience_tool          - Resilience subsystem perf
module_usage_analysis_tool         - Function call dependency graph
```

### Thermodynamics & Energy (8)
```
optimize_free_energy_tool          - Free energy minimization
calculate_time_crystal_objective_tool - Anti-churn metric
analyze_energy_landscape_tool      - Potential well mapping
get_entropy_monitor_state_tool     - Schedule disorder level
analyze_phase_transitions_tool     - Behavioral state changes
calculate_schedule_entropy_tool    - Information theory entropy
analyze_schedule_periodicity_tool  - Fourier cycle detection
analyze_schedule_rigidity_tool     - Schedule flexibility
```

### Circuit Breakers (4)
```
check_circuit_breakers_tool        - All breaker status
get_breaker_health_tool            - Detailed breaker metrics
test_half_open_tool                - Recovery testing
override_circuit_breaker_tool      - Manual breaker control
```

### Hopfield Networks (4)
```
calculate_hopfield_energy_tool     - Schedule state energy
find_nearby_attractors_tool        - Nearby stable patterns
measure_basin_depth_tool           - Perturbation robustness
detect_spurious_attractors_tool    - Anti-pattern detection
```

### Game Theory (3)
```
analyze_nash_stability_tool        - Nash equilibrium detection
find_deviation_incentives_tool     - Swap request prediction
detect_coordination_failures_tool  - Pareto improvement gaps
```

### Value-at-Risk / Financial (4)
```
calculate_coverage_var_tool        - Probabilistic coverage bounds
calculate_workload_var_tool        - Workload distribution risk
calculate_conditional_var_tool     - Expected shortfall (tail risk)
simulate_disruption_scenarios_tool - Monte Carlo stress testing
```

### Ecological Dynamics (4)
```
analyze_supply_demand_cycles_tool  - Lotka-Volterra predator-prey
predict_capacity_crunch_tool       - Capacity crisis forecasting
find_equilibrium_point_tool        - Stable staffing targets
simulate_intervention_tool         - What-if capacity changes
```

### Signal Processing (3)
```
detect_schedule_cycles_tool        - FFT periodicity (7d, 28d)
analyze_harmonic_resonance_tool    - ACGME window alignment
calculate_spectral_entropy_tool    - Schedule complexity
```

### Control Theory / Kalman (2)
```
analyze_workload_trend_tool        - Kalman filtering trends
detect_workload_anomalies_tool     - Outlier via residuals
```

### Fatigue Risk Management (5)
```
run_frms_assessment_tool           - Full FRMS assessment
get_fatigue_score_tool             - Single fatigue index (0-100)
analyze_sleep_debt_tool            - Cumulative fatigue
evaluate_fatigue_hazard_tool       - Hazard assessment
scan_team_fatigue_tool             - Group fatigue scan
assess_schedule_fatigue_risk_tool  - Schedule impact on fatigue
```

### Immune System (AIS) (3)
```
assess_immune_response_tool        - Antigen-antibody response
check_memory_cells_tool            - Immunological memory
analyze_antibody_response_tool     - Adaptive immunity
```

### Advanced Metrics (5)
```
calculate_shapley_workload_tool    - Fair workload attribution
calculate_equity_metrics_tool      - Fairness indices (Gini, etc)
generate_lorenz_curve_tool         - Inequality visualization
detect_critical_slowing_down_tool  - Tipping point warning
detect_schedule_changepoints_tool  - Behavioral change detection
```

### Compliance & Time Crystal (4)
```
check_mtf_compliance_tool          - MTF schedule compliance
get_checkpoint_status_tool         - Time crystal checkpoints
get_time_crystal_health_tool       - Schedule stability metric
calculate_recovery_distance_tool   - N-1 recovery edit count
```

### Advanced Resilience (4)
```
get_unified_critical_index_tool    - Holistic health score (0-1)
assess_creep_fatigue_tool          - Materials science fatigue
analyze_transcription_triggers_tool - Gene expression analogy
```

---

## Quick Usage Patterns

### Emergency Response
```python
util = check_utilization_threshold_tool()
if util.level in ["RED", "BLACK"]:
    defense = get_defense_level_tool(util.utilization_rate)
    if defense.escalation_needed:
        plan = execute_sacrifice_hierarchy_tool(criteria="minimize_burnout")
```

### Compliance Check
```python
result = validate_schedule_tool(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 3, 31),
    check_work_hours=True,
    check_supervision=True
)
if not result.is_valid:
    print(f"Issues: {result.total_issues} (Critical: {result.critical_issues})")
```

### Long-Running Analysis
```python
task = start_background_task_tool(
    task_type=TaskType.RESILIENCE_CONTINGENCY,
    params={"days_ahead": 90}
)
status = get_task_status_tool(task.task_id)
# Poll until status.status in [SUCCESS, FAILURE]
```

### Health Dashboard
```python
metrics = {
    "util": check_utilization_threshold_tool(),
    "defense": get_defense_level_tool(),
    "index": get_unified_critical_index_tool(),
    "burnout": calculate_burnout_rt_tool(),
    "fatigue": get_fatigue_score_tool(),
}
```

### Fair Workload
```python
shapley = calculate_shapley_workload_tool(date_range=(start, end))
lorenz = generate_lorenz_curve_tool()
equity = calculate_equity_metrics_tool()
```

### Pre-Deployment Safety
```python
validation = validate_deployment_tool(environment="staging")
security = run_security_scan_tool(environment="staging")
tests = run_smoke_tests_tool(environment="staging")
# Only promote if all pass
```

---

## Tool Response Types

### Core Responses
- `ScheduleValidationResult` - validation tools
- `ContingencyAnalysisResult` - contingency analysis
- `ConflictDetectionResult` - conflict detection
- `SwapCandidatesResult` - swap analysis
- `BackgroundTaskResult` - task start confirmation
- `TaskStatusResult` - task status & result

### Resilience Responses
- `UtilizationResponse` - utilization status
- `DefenseLevelResponse` - defense readiness
- `ContingencyAnalysisResult` - impact assessment
- `StaticFallbacksResponse` - backup schedules

### Analytics Responses
- `BurnoutAnalysisResult` - epidemic analysis
- `SPCAnalysisResponse` - drift detection
- `ProcessCapabilityResponse` - Six Sigma metrics
- `UnifiedCriticalIndexResponse` - holistic health

### Metric Responses
- `ShapleyValueResult` - fair attribution
- `EquityMetricsResult` - fairness indices
- `LorenzCurveResult` - inequality visualization
- `FatigueScoreResult` - fatigue index

---

## Error Codes

| Code | Meaning | Recovery |
|------|---------|----------|
| 400 | Bad parameters | Validate inputs |
| 404 | Resource not found | Check IDs |
| 422 | Validation failed | Check Pydantic schema |
| 429 | Rate limited | Wait & retry |
| 503 | Backend unavailable | Check API health |
| 504 | Timeout | Retry with longer timeout |

---

## Performance Expectations

| Tool Category | Typical Duration | Notes |
|---------------|-----------------|-------|
| Validation | 200ms | API call bottleneck |
| Contingency | 2s | Solver optimization |
| Metrics | 500ms | Graph traversal |
| Burnout | 300ms | DB query |
| Deployment | 1s | External services |
| Background | 1-10min | Task-dependent |

---

## Recommended Workflows

### Morning Operations
1. `get_unified_critical_index_tool()` - Daily health check
2. `detect_burnout_precursors_tool()` - Early warning
3. `get_fatigue_score_tool()` - Team fatigue
4. `run_spc_analysis_tool()` - Drift detection

### Pre-Deployment
1. `validate_deployment_tool()` - Validation
2. `run_security_scan_tool()` - Security check
3. `run_smoke_tests_tool()` - Quick tests
4. `promote_to_production_tool()` - Promotion

### Emergency Response
1. `check_utilization_threshold_tool()` - Assess severity
2. `run_contingency_analysis_resilience_tool()` - Impact analysis
3. `execute_sacrifice_hierarchy_tool()` - Resolution plan
4. `list_active_tasks_tool()` - Monitor effects

### Fairness Audit
1. `calculate_shapley_workload_tool()` - Fair attribution
2. `generate_lorenz_curve_tool()` - Inequality view
3. `calculate_equity_metrics_tool()` - Metrics
4. `analyze_swap_candidates_tool()` - Fix options

---

## Resources Available

1. **schedule_status** - Current assignments, coverage
2. **compliance_summary** - ACGME violations, warnings

---

## Configuration

```bash
# Environment variables
DATABASE_URL=postgresql://...
API_BASE_URL=http://localhost:8000
REDIS_URL=redis://localhost:6379
```

---

## Tool Dependencies

Most tools are independent. Key dependencies:

- Async tools → Celery + Redis
- Deployment tools → External services
- Analytics → API backend
- Burnout tools → Epidemiology data

---

**Total Tools: 81**
**Functional Domains: 8**
**Last Updated: 2025-12-30**
