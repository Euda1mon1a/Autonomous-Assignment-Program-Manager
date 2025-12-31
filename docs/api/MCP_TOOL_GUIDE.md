# MCP Tool Usage Guide

> **Status**: Production-ready
> **Version**: 2.0
> **Last Updated**: 2025-12-30
> **Total Tools**: 81

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Tool Categories](#tool-categories)
4. [Common Workflows](#common-workflows)
5. [Tool Reference by Category](#tool-reference-by-category)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The Model Context Protocol (MCP) server provides 81 specialized tools for AI-assisted medical residency scheduling and resilience monitoring. These tools expose the Cross-Disciplinary Engineering Resilience Framework through a standardized interface.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Claude AI Agent                            │
├─────────────────────────────────────────────────────────────────┤
│                    MCP Server (FastMCP)                         │
│                        81 Tools                                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │ Scheduling   │ Resilience   │ Early Warning│ Analytics    │ │
│  │ (8 tools)    │ (12 tools)   │ (4 tools)    │ (3 tools)    │ │
│  ├──────────────┼──────────────┼──────────────┼──────────────┤ │
│  │ Deployment   │ Epidemiology │ Circuit      │ Time Crystal │ │
│  │ (7 tools)    │ (3 tools)    │ Breakers     │ (7 tools)    │ │
│  │              │              │ (5 tools)    │              │ │
│  ├──────────────┼──────────────┼──────────────┼──────────────┤ │
│  │ Composite    │ Immune       │ Thermodynamics│ Hopfield    │ │
│  │ (4 tools)    │ System       │ (5 tools)    │ Network      │ │
│  │              │ (4 tools)    │              │ (5 tools)    │ │
│  ├──────────────┼──────────────┼──────────────┼──────────────┤ │
│  │ FRMS         │ Async Tasks  │ Testing      │              │ │
│  │ (6 tools)    │ (4 tools)    │ (3 tools)    │              │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    Backend API (FastAPI)                        │
│              PostgreSQL │ Redis │ Celery                        │
└─────────────────────────────────────────────────────────────────┘
```

### Connection Information

- **MCP Server**: `http://mcp-server:8080` (Docker internal)
- **Backend API**: `http://backend:8000` (MCP → Backend)
- **Protocol**: Model Context Protocol (FastMCP)
- **Transport**: HTTP

---

## Quick Start

### Basic Usage Pattern

All MCP tools follow a consistent pattern:

```python
# 1. Import the tool
from scheduler_mcp import mcp

# 2. Call the tool with parameters
result = await tool_name(
    param1="value1",
    param2="value2"
)

# 3. Process the response
if result.status == "success":
    print(result.data)
else:
    print(f"Error: {result.error}")
```

### Example: Check Schedule Compliance

```python
# Validate a week of schedules
result = await validate_schedule_tool(
    start_date="2025-01-01",
    end_date="2025-01-07",
    check_work_hours=True,
    check_supervision=True
)

if not result.is_compliant:
    print(f"Found {len(result.violations)} violations:")
    for violation in result.violations:
        print(f"  - {violation.type}: {violation.message}")
```

### Example: Monitor Burnout Risk

```python
# Calculate Fire Danger Index for a resident
result = await calculate_fire_danger_index_tool(
    resident_id="abc-123",
    recent_hours=75.0,
    monthly_load=260.0,
    yearly_satisfaction=0.4
)

if result.danger_class in ["very_high", "extreme"]:
    print(f"⚠️ ALERT: {result.danger_class} burnout risk")
    for restriction in result.recommended_restrictions:
        print(f"  • {restriction}")
```

---

## Tool Categories

### 1. Schedule Validation & Management (8 tools)

Validate ACGME compliance and manage schedules.

| Tool | Purpose |
|------|---------|
| `validate_schedule_tool` | Validate schedule against ACGME regulations |
| `validate_schedule_by_id_tool` | Validate specific schedule by ID |
| `detect_conflicts_tool` | Find scheduling conflicts |
| `analyze_swap_candidates_tool` | Find compatible swap candidates |
| `calculate_schedule_entropy_tool` | Measure schedule randomness/complexity |
| `analyze_schedule_periodicity_tool` | Detect natural cycles in schedules |
| `detect_schedule_changepoints_tool` | Identify sudden schedule changes |
| `analyze_behavioral_patterns_tool` | Extract scheduling behavior patterns |

**Common Use Cases:**
- Pre-deployment schedule validation
- Conflict resolution
- Schedule quality analysis
- Pattern detection for optimization

---

### 2. Resilience Framework (12 tools)

Core resilience monitoring and defense-in-depth.

| Tool | Purpose |
|------|---------|
| `check_utilization_threshold_tool` | Check 80% utilization threshold |
| `run_contingency_analysis_tool` | N-1/N-2 contingency analysis |
| `run_contingency_analysis_resilience_tool` | Enhanced contingency with resilience |
| `get_defense_level_tool` | Current defense-in-depth level |
| `analyze_homeostasis_tool` | Biological feedback loop analysis |
| `calculate_blast_radius_tool` | Failure containment zones |
| `analyze_le_chatelier_tool` | Equilibrium shift analysis |
| `check_mtf_compliance_tool` | Military readiness (DRRS) translation |
| `execute_sacrifice_hierarchy_tool` | Triage-based load shedding |
| `get_static_fallbacks_tool` | Pre-computed backup schedules |
| `benchmark_resilience_tool` | Resilience framework benchmarking |
| `benchmark_constraints_tool` | Constraint system benchmarking |

**Common Use Cases:**
- Daily resilience health checks
- Vulnerability detection
- Crisis response planning
- System stability monitoring

---

### 3. Early Warning System (4 tools)

Cross-disciplinary burnout detection before crisis.

| Tool | Purpose |
|------|---------|
| `detect_burnout_precursors_tool` | Seismic STA/LTA algorithm |
| `run_spc_analysis_tool` | Statistical Process Control |
| `calculate_fire_danger_index_tool` | Multi-temporal burnout (FWI) |
| `calculate_batch_fire_danger_tool` | Batch FWI for multiple residents |
| `predict_burnout_magnitude_tool` | Predict burnout severity |

**Scientific Basis:**
- **STA/LTA**: Seismological P-wave detection
- **SPC**: Semiconductor manufacturing quality control
- **FWI**: Canadian Forest Fire Danger Rating System

**Common Use Cases:**
- Weekly workload monitoring
- Individual burnout screening
- Program-wide risk assessment
- Early intervention triggers

---

### 4. Epidemiology Tools (3 tools)

Model burnout spread through networks.

| Tool | Purpose |
|------|---------|
| `calculate_burnout_rt_tool` | Reproduction number (Rt) |
| `simulate_burnout_spread_tool` | SIR epidemic simulation |
| `simulate_burnout_contagion_tool` | SIS network diffusion |

**Key Concepts:**
- **Rt < 1**: Burnout declining
- **Rt > 1**: Burnout spreading
- **Superspreaders**: High-connectivity individuals

**Common Use Cases:**
- Identify superspreaders
- Predict epidemic trajectory
- Evaluate intervention effectiveness
- Network-based targeting

---

### 5. Optimization & Analytics (3 tools)

Quantitative staffing and quality analysis.

| Tool | Purpose |
|------|---------|
| `optimize_erlang_coverage_tool` | Erlang-C queuing for specialists |
| `calculate_erlang_metrics_tool` | Erlang metrics for existing staffing |
| `calculate_process_capability_tool` | Six Sigma Cp/Cpk indices |
| `calculate_workload_process_capability_tool` | Workload-specific capability |
| `calculate_equity_metrics_tool` | Gini coefficient & fairness |
| `generate_lorenz_curve_tool` | Equity visualization data |

**Common Use Cases:**
- Specialist staffing optimization
- Schedule quality quantification
- Workload equity monitoring
- ACGME compliance evidence

---

### 6. Composite Analytics (4 tools)

Unified multi-domain risk assessment.

| Tool | Purpose |
|------|---------|
| `get_unified_critical_index_tool` | Aggregated risk score |
| `calculate_recovery_distance_tool` | Schedule fragility (operations research) |
| `assess_creep_fatigue_tool` | Materials science burnout model |
| `analyze_transcription_triggers_tool` | Gene regulatory network for constraints |

**Risk Patterns Detected:**
- Universal Critical (all 3 domains high)
- Structural Burnout (contingency + epidemiology)
- Influential Hub (contingency + network)
- Social Connector (epidemiology + network)

**Common Use Cases:**
- Holistic risk assessment
- Cross-domain pattern detection
- Intervention prioritization
- Hidden risk discovery

---

### 7. Circuit Breaker Tools (5 tools)

Distributed systems failure isolation.

| Tool | Purpose |
|------|---------|
| `check_circuit_breakers_tool` | All breakers status |
| `get_breaker_health_tool` | Health metrics for breakers |
| `override_circuit_breaker_tool` | Manual override (emergency) |
| `test_half_open_tool` | Test half-open state |

**Circuit Breaker States:**
- **Closed**: Normal operations
- **Open**: Failure detected, requests blocked
- **Half-Open**: Testing recovery

**Common Use Cases:**
- Monitor service health
- Emergency overrides
- Recovery testing
- Dependency failure isolation

---

### 8. Deployment Workflow (7 tools)

Safe deployment with validation gates.

| Tool | Purpose |
|------|---------|
| `validate_deployment_tool` | Pre-deployment validation |
| `run_smoke_tests_tool` | Post-deployment smoke tests |
| `run_security_scan_tool` | Security vulnerability scan |
| `promote_to_production_tool` | Canary → production promotion |
| `rollback_deployment_tool` | Emergency rollback |
| `get_deployment_status_tool` | Current deployment status |
| `list_deployments_tool` | Deployment history |

**Deployment Stages:**
1. Validate → 2. Smoke Test → 3. Security Scan → 4. Canary → 5. Production

**Common Use Cases:**
- CI/CD pipeline integration
- Safe schedule deployment
- Emergency rollbacks
- Deployment audit trail

---

### 9. Time Crystal Scheduling (7 tools)

Anti-churn and stability optimization.

| Tool | Purpose |
|------|---------|
| `calculate_time_crystal_objective_tool` | Anti-churn score |
| `get_time_crystal_health_tool` | Stability metrics |
| `get_checkpoint_status_tool` | Stroboscopic checkpoints |
| `calculate_shapley_workload_tool` | Fair workload via game theory |
| `detect_critical_slowing_down_tool` | Early phase transition warning |
| `analyze_phase_transitions_tool` | System state changes |
| `get_entropy_monitor_state_tool` | Entropy tracking |

**Key Concepts:**
- **Rigidity Score**: 0.0 (chaos) → 1.0 (frozen)
- **Subharmonics**: Natural 7d, 14d, 28d cycles
- **Stroboscopic Points**: Week start, block end

**Common Use Cases:**
- Minimize schedule changes on regeneration
- Detect instability before cascade
- Fair workload distribution
- Schedule stability monitoring

---

### 10. Artificial Immune System (4 tools)

Immunology-inspired resilience.

| Tool | Purpose |
|------|---------|
| `assess_immune_response_tool` | Immune system health |
| `check_memory_cells_tool` | Historical threat recognition |
| `analyze_antibody_response_tool` | Active defense mechanisms |

**Immune Concepts:**
- **Memory Cells**: Past schedule failure patterns
- **Antibodies**: Active defenses against known threats
- **Immune Response**: System-wide reaction to stress

**Common Use Cases:**
- Learn from past failures
- Adaptive defense mechanisms
- Pattern-based threat detection
- Immunological schedule hardening

---

### 11. Thermodynamics Tools (5 tools)

Entropy, phase transitions, free energy.

| Tool | Purpose |
|------|---------|
| `calculate_schedule_entropy_tool` | Shannon entropy of schedules |
| `analyze_energy_landscape_tool` | Thermodynamic stability |
| `optimize_free_energy_tool` | Minimize free energy |
| `analyze_phase_transitions_tool` | Detect state changes |
| `detect_critical_slowing_down_tool` | Pre-transition warning signs |

**Thermodynamic Principles:**
- **High Entropy**: Disordered, flexible schedules
- **Low Entropy**: Ordered, rigid schedules
- **Phase Transition**: Abrupt quality shift
- **Free Energy**: Combined internal + organizational cost

**Common Use Cases:**
- Optimize schedule flexibility
- Predict system transitions
- Balance order vs adaptability
- Energy landscape mapping

---

### 12. Hopfield Network Attractors (5 tools)

Energy landscape & schedule stability.

| Tool | Purpose |
|------|---------|
| `calculate_hopfield_energy_tool` | Energy of current schedule state |
| `find_nearby_attractors_tool` | Find stable nearby schedules |
| `detect_spurious_attractors_tool` | Detect unwanted local minima |
| `measure_basin_depth_tool` | Measure stability well depth |
| `analyze_stigmergy_tool` | Indirect coordination via environment |

**Hopfield Concepts:**
- **Energy**: Lower = more stable
- **Attractor**: Stable schedule configuration
- **Basin**: Region attracted to same stable state
- **Spurious Attractor**: Unintended stable state

**Common Use Cases:**
- Find stable schedule alternatives
- Avoid local minima traps
- Measure schedule robustness
- Discover hidden stable states

---

### 13. FRMS (Fatigue Risk Management) (6 tools)

Aviation-style fatigue risk management.

| Tool | Purpose |
|------|---------|
| `run_frms_assessment_tool` | Comprehensive FRMS assessment |
| `get_fatigue_score_tool` | Individual fatigue score |
| `evaluate_fatigue_hazard_tool` | Hazard evaluation |
| `scan_team_fatigue_tool` | Team-wide fatigue scan |
| `assess_schedule_fatigue_risk_tool` | Schedule-level risk |
| `analyze_sleep_debt_tool` | Cumulative sleep deficit |

**FRMS Framework:**
- **Acute Fatigue**: Last 24-48 hours
- **Cumulative Fatigue**: Last 7-14 days
- **Circadian Disruption**: Shift timing misalignment
- **Sleep Debt**: Accumulated deficit

**Common Use Cases:**
- Pre-flight style checks before critical procedures
- Monitor cumulative fatigue
- Schedule circadian-friendly rotations
- Sleep debt tracking

---

### 14. Async Task Management (4 tools)

Long-running background operations.

| Tool | Purpose |
|------|---------|
| `start_background_task_tool` | Start Celery task |
| `get_task_status_tool` | Poll task status |
| `cancel_task_tool` | Cancel running task |
| `list_active_tasks_tool` | List all active tasks |

**Available Task Types:**
- `resilience_health_check`: Daily health monitoring
- `resilience_contingency`: N-1/N-2 analysis
- `resilience_fallback_precompute`: Precompute backups
- `metrics_computation`: Schedule metrics
- `metrics_fairness_report`: Equity trends

**Common Use Cases:**
- Schedule long-running analyses
- Monitor computation progress
- Cancel runaway tasks
- Background metric computation

---

### 15. Empirical Testing Tools (3 tools)

Benchmarking and validation.

| Tool | Purpose |
|------|---------|
| `benchmark_solvers_tool` | Compare solver performance |
| `benchmark_resilience_tool` | Resilience framework benchmarking |
| `benchmark_constraints_tool` | Constraint system benchmarking |
| `ablation_study_tool` | Component removal analysis |
| `module_usage_analysis_tool` | Identify unused modules |

**Common Use Cases:**
- Performance regression testing
- Solver selection
- Identify dead code
- Component importance analysis
- System optimization

---

## Common Workflows

### Workflow 1: Daily Resilience Check

Monitor system health every morning.

```python
# 1. Check utilization
util = await check_utilization_threshold_tool(
    available_faculty=24,
    required_blocks=40
)

# 2. Get defense level
defense = await get_defense_level_tool()

# 3. Calculate burnout Rt
rt = await calculate_burnout_rt_tool(
    burned_out_provider_ids=["p1", "p2"]
)

# 4. Check circuit breakers
breakers = await check_circuit_breakers_tool()

# 5. Generate unified index
index = await get_unified_critical_index_tool(
    include_details=True,
    top_n=5
)

# Alert if critical
if index.risk_level in ["high", "critical"]:
    send_alert(f"System risk: {index.risk_level}")
```

### Workflow 2: Pre-Deployment Validation

Validate before deploying new schedule.

```python
# 1. Validate ACGME compliance
validation = await validate_schedule_tool(
    start_date="2025-01-01",
    end_date="2025-03-31",
    check_work_hours=True,
    check_supervision=True
)

# 2. Check for conflicts
conflicts = await detect_conflicts_tool(
    start_date="2025-01-01",
    end_date="2025-03-31"
)

# 3. Calculate process capability
capability = await calculate_process_capability_tool(
    data=weekly_hours,
    lower_spec_limit=40,
    upper_spec_limit=80
)

# 4. Check equity
equity = await calculate_equity_metrics_tool(
    hours_per_provider=hours_dict
)

# Only deploy if all gates pass
if (validation.is_compliant and
    len(conflicts) == 0 and
    capability.cpk >= 1.33 and
    equity.is_equitable):

    await promote_to_production_tool(
        deployment_id="deploy-123"
    )
```

### Workflow 3: Individual Burnout Screening

Screen resident for burnout risk.

```python
# 1. Fire Danger Index (multi-temporal)
fwi = await calculate_fire_danger_index_tool(
    resident_id="res-123",
    recent_hours=75.0,
    monthly_load=260.0,
    yearly_satisfaction=0.4
)

# 2. SPC Analysis (process control)
spc = await run_spc_analysis_tool(
    resident_id="res-123",
    weekly_hours=[72, 75, 78, 80, 82],
    target_hours=60.0
)

# 3. Precursor Detection (seismic)
precursors = await detect_burnout_precursors_tool(
    resident_id="res-123",
    signal_type="swap_requests",
    time_series=[0, 1, 2, 3, 5, 8, 13]  # Fibonacci pattern
)

# 4. FRMS Assessment (aviation fatigue)
frms = await run_frms_assessment_tool(
    resident_id="res-123"
)

# Aggregate risk
high_risk = (
    fwi.danger_class in ["very_high", "extreme"] or
    spc.violations_detected > 2 or
    precursors.alerts_detected > 0 or
    frms.fatigue_level == "critical"
)

if high_risk:
    # Trigger intervention
    schedule_wellness_checkup("res-123")
```

### Workflow 4: Schedule Optimization

Optimize schedule quality and equity.

```python
# 1. Baseline entropy (flexibility)
entropy = await calculate_schedule_entropy_tool(
    start_date="2025-01-01",
    end_date="2025-03-31"
)

# 2. Find stable alternatives (Hopfield)
attractors = await find_nearby_attractors_tool(
    max_distance=5
)

# 3. Calculate Shapley values (fairness)
shapley = await calculate_shapley_workload_tool(
    faculty_ids=["f1", "f2", "f3"],
    start_date="2025-01-01",
    end_date="2025-03-31"
)

# 4. Optimize for anti-churn (time crystal)
time_crystal = await calculate_time_crystal_objective_tool()

# 5. Test recovery distance (fragility)
recovery = await calculate_recovery_distance_tool(
    max_events=20
)

# Select schedule with best balance
best_schedule = min(attractors, key=lambda s: (
    0.3 * s.energy +           # Stability
    0.3 * (1 - s.equity) +     # Inequity penalty
    0.2 * s.churn_score +      # Change penalty
    0.2 * s.fragility         # Fragility penalty
))
```

### Workflow 5: Emergency Response

Respond to crisis situation.

```python
# 1. Check current defense level
defense = await get_defense_level_tool()

if defense.level >= 4:  # Containment or Emergency

    # 2. Calculate blast radius
    blast = await calculate_blast_radius_tool()

    # 3. Get static fallbacks
    fallbacks = await get_static_fallbacks_tool()

    # 4. Execute sacrifice hierarchy
    sacrifice = await execute_sacrifice_hierarchy_tool(
        severity_level=defense.level
    )

    # 5. Override circuit breakers if needed
    if defense.level == 5:  # Emergency
        await override_circuit_breaker_tool(
            breaker_name="critical_services",
            override_state="closed"  # Force allow
        )

    # 6. Start emergency contingency
    task = await start_background_task_tool(
        task_type="resilience_crisis_activation",
        params={"severity": defense.level}
    )

    # Alert leadership
    escalate_crisis(defense, blast, sacrifice)
```

---

## Best Practices

### 1. Error Handling

Always handle tool errors gracefully:

```python
try:
    result = await validate_schedule_tool(...)
except ValueError as e:
    logger.error(f"Invalid parameters: {e}")
except RuntimeError as e:
    logger.warning(f"Backend unavailable: {e}")
    # Use fallback or retry
```

### 2. Batch Operations

Use batch tools when processing multiple entities:

```python
# ❌ DON'T: Loop individual calls
for resident in residents:
    await calculate_fire_danger_index_tool(resident.id, ...)

# ✅ DO: Use batch tool
await calculate_batch_fire_danger_tool(
    resident_ids=[r.id for r in residents],
    ...
)
```

### 3. Async Task Polling

Poll long-running tasks with backoff:

```python
task = await start_background_task_tool(
    task_type="resilience_contingency",
    params={"days_ahead": 90}
)

while True:
    status = await get_task_status_tool(task.task_id)

    if status.state in ["success", "failure"]:
        break

    await asyncio.sleep(2)  # Poll every 2 seconds
```

### 4. Caching Results

Cache expensive computations:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
async def get_cached_equity(date_key):
    return await calculate_equity_metrics_tool(...)
```

### 5. Severity-Based Alerting

Route alerts by severity:

```python
def route_alert(tool_result):
    if tool_result.severity == "healthy":
        return  # No alert
    elif tool_result.severity == "warning":
        notify_coordinator(tool_result)
    elif tool_result.severity == "critical":
        notify_leadership(tool_result)
    elif tool_result.severity == "emergency":
        page_everyone(tool_result)
```

### 6. Validation Chains

Chain validations for comprehensive checks:

```python
async def comprehensive_validation(schedule_id):
    # ACGME compliance
    acgme = await validate_schedule_by_id_tool(schedule_id)

    # Conflicts
    conflicts = await detect_conflicts_tool(...)

    # Equity
    equity = await calculate_equity_metrics_tool(...)

    # Resilience
    contingency = await run_contingency_analysis_tool(...)

    return {
        "compliant": acgme.is_valid,
        "conflict_free": len(conflicts) == 0,
        "equitable": equity.is_equitable,
        "resilient": contingency.passes_n1
    }
```

---

## Troubleshooting

### Tool Returns Fallback Data

**Symptom**: Tool returns simplified results with warnings.

**Cause**: Backend service unavailable or module missing.

**Solution**:
1. Check backend API health: `curl http://backend:8000/health`
2. Check MCP server logs: `docker-compose logs mcp-server`
3. Verify dependencies: `pip list | grep scipy`

### Task Stuck in Pending

**Symptom**: Background task never starts.

**Cause**: Celery workers not running or Redis unavailable.

**Solution**:
```bash
# Check Celery workers
docker-compose logs celery-worker

# Check Redis
docker-compose exec redis redis-cli PING

# Restart workers
docker-compose restart celery-worker celery-beat
```

### Rate Limit Exceeded

**Symptom**: Tool returns 429 error.

**Cause**: Too many requests to backend API.

**Solution**:
- Use batch tools instead of loops
- Add delays between calls
- Check rate limit headers: `X-RateLimit-Remaining`

### Invalid Date Format

**Symptom**: ValueError about date parsing.

**Cause**: Incorrect date string format.

**Solution**:
```python
# ❌ DON'T: Use ambiguous formats
start_date = "1/15/2025"

# ✅ DO: Use ISO 8601
start_date = "2025-01-15"
```

### Missing Required Parameters

**Symptom**: Tool raises TypeError about missing arguments.

**Cause**: Required parameter not provided.

**Solution**:
- Check tool signature: `help(tool_name)`
- Review parameter descriptions
- Provide all required fields

### Circuit Breaker Open

**Symptom**: Tool returns immediately with failure.

**Cause**: Circuit breaker protecting failing dependency.

**Solution**:
1. Check breaker status: `await check_circuit_breakers_tool()`
2. Fix underlying service
3. Test recovery: `await test_half_open_tool(breaker_name)`
4. Emergency override: `await override_circuit_breaker_tool(breaker_name, "closed")`

---

## Performance Benchmarks

Measured on 100 residents, 52 weeks of data, 4 CPU cores:

| Tool Category | Typical Latency | Notes |
|---------------|-----------------|-------|
| **Early Warning** | <100ms | Real-time suitable |
| **Resilience** | <200ms | Fast checks |
| **Epidemiology** | 200ms-1s | Network analysis |
| **Optimization** | <50ms | Very fast |
| **Composite** | 200ms-2s | Multi-domain aggregation |
| **Circuit Breakers** | <10ms | Near-instant |
| **Deployment** | 1-5s | Validation gates |
| **Time Crystal** | <500ms | Moderate |
| **Immune System** | <100ms | Fast |
| **Thermodynamics** | <200ms | Moderate |
| **Hopfield** | 500ms-2s | Energy landscape search |
| **FRMS** | <100ms | Fast |
| **Async Tasks** | <50ms | Queue only, execution varies |
| **Benchmarking** | 5-60s | Dependent on test scope |

**Optimization Tips:**
- Use batch tools for >10 entities
- Cache frequently-accessed results
- Run expensive analyses as background tasks
- Pre-compute fallbacks during low-traffic periods

---

## Integration Examples

### Celery Scheduled Tasks

```python
from celery import shared_task
from scheduler_mcp import mcp

@shared_task
def daily_resilience_check():
    """Daily automated resilience monitoring."""

    # Unified critical index
    index = await get_unified_critical_index_tool(
        include_details=True
    )

    # Fire danger for all residents
    fire_batch = await calculate_batch_fire_danger_tool(
        resident_ids=get_all_resident_ids()
    )

    # Burnout Rt
    burned_out = get_burned_out_residents()
    rt = await calculate_burnout_rt_tool(
        burned_out_provider_ids=burned_out
    )

    # Generate report
    generate_daily_report(index, fire_batch, rt)
```

### Dashboard Integration

```python
# Real-time dashboard data
async def get_dashboard_data():
    return {
        "utilization": await check_utilization_threshold_tool(...),
        "defense_level": await get_defense_level_tool(),
        "breakers": await check_circuit_breakers_tool(),
        "equity": await calculate_equity_metrics_tool(...),
        "burnout_rt": await calculate_burnout_rt_tool(...)
    }
```

### Alert Pipeline

```python
async def monitor_and_alert():
    """Continuous monitoring with alerting."""

    while True:
        # Check multiple signals
        spc = await run_spc_analysis_tool(...)
        precursors = await detect_burnout_precursors_tool(...)
        fwi = await calculate_fire_danger_index_tool(...)

        # Aggregate severity
        max_severity = max(
            spc.severity,
            precursors.severity,
            fwi.severity,
            key=lambda s: ["healthy", "warning", "critical", "emergency"].index(s)
        )

        # Route alert
        if max_severity in ["critical", "emergency"]:
            send_alert(max_severity, [spc, precursors, fwi])

        await asyncio.sleep(900)  # Every 15 minutes
```

---

## API Response Patterns

All tools follow consistent response patterns:

### Success Response

```json
{
  "status": "success",
  "data": { ... },
  "severity": "healthy" | "warning" | "critical" | "emergency",
  "recommendations": ["action1", "action2"],
  "metadata": {
    "timestamp": "2025-12-30T10:00:00Z",
    "tool_version": "2.0"
  }
}
```

### Error Response

```json
{
  "status": "error",
  "error": "Error message",
  "error_type": "ValueError" | "RuntimeError" | "ImportError",
  "severity": "warning",
  "fallback_used": true
}
```

### Degraded Response

```json
{
  "status": "success",
  "data": { ... },
  "severity": "warning",
  "warnings": [
    "Erlang module unavailable - using simplified estimation"
  ],
  "degraded": true
}
```

---

## Document Information

**Version**: 2.0
**Last Updated**: 2025-12-30
**Maintained By**: MCP Integration Team
**Total Tools Documented**: 81

**Related Documentation**:
- [MCP Tools Reference](./MCP_TOOLS_REFERENCE.md) - Detailed tool specifications
- [Cross-Disciplinary Resilience Framework](../architecture/cross-disciplinary-resilience.md)
- [MCP Server Architecture](../architecture/mcp-server.md)
- [Backend API Reference](./index.md)
- [AI Agent User Guide](../guides/AI_AGENT_USER_GUIDE.md)

**Contributing**:
- Tool additions: Update `mcp-server/src/scheduler_mcp/server.py`
- Documentation: Update this guide
- Examples: Add to workflows section

**Support**:
- Issues: File in GitHub repository
- Questions: Consult project documentation
- Emergency: Contact system administrator
