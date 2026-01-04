# MCP Tools & Utilities Reconnaissance
## Session 8 SEARCH_PARTY Operation: G2_RECON

**Conducted:** 2025-12-30
**Scope:** FastMCP server with 81+ tools for AI-assisted scheduling
**Documentation Status:** Complete inventory with utility analysis

---

## Executive Summary

The Residency Scheduler MCP Server is a **comprehensive AI integration platform** with **81 registered MCP tools** organized across 8 functional domains. This document provides complete tool inventory, utility classification, and integration patterns for AI assistants working with the scheduler.

**Key Statistics:**
- **Total Tools:** 81
- **Functional Domains:** 8 (Core Scheduling, Resilience, Early Warning, Empirical, Deployment, Advanced Analytics, Thermodynamics, Immune System)
- **Framework:** FastMCP (decorator-based, type-validated)
- **Transport:** HTTP (containerized)
- **Async Support:** Full Celery integration for long-running operations

---

## SEARCH_PARTY LENSES: Reconnaissance Findings

### PERCEPTION: Current Utility Tools

The MCP server exposes operational capabilities through two primary interfaces:

#### Resources (Read-Only)
- `schedule_status` - Real-time schedule state, assignments, coverage metrics
- `compliance_summary` - ACGME compliance status, violations, warnings

#### Tools (Active Operations)
81 tools implementing validation, analysis, simulation, and optimization across 8 domains.

### INVESTIGATION: Utility Coverage Map

**Full Coverage Domains:**
1. **Core Scheduling** (5 tools) - Validation, contingency, conflict detection
2. **Async Task Management** (4 tools) - Celery integration, task lifecycle
3. **Resilience Framework** (15+ tools) - Tiers 1-4, defense monitoring
4. **Early Warning Integration** (8 tools) - STA/LTA, SPC, fire index
5. **Deployment Tools** (9 tools) - CI/CD, validation, promotion
6. **Empirical Testing** (5 tools) - Benchmarking, ablation, module analysis
7. **Thermodynamics & Energy** (8 tools) - Free energy, entropy, phase transitions
8. **Immune System & Advanced** (18+ tools) - Circuit breakers, game theory, Hopfield networks

**Undocumented Utilities:**
- Tool dependencies and chaining patterns not fully explicit
- Helper function philosophy scattered across modules
- No centralized tool dependency graph

### ARCANA: Integration Patterns

#### Pattern 1: Standard Tool Registration
```python
@mcp.tool()
async def tool_name(param1: Type1, param2: Type2) -> ResponseType:
    """Tool description."""
    # Implementation
```

#### Pattern 2: Error Handling
All tools include `try-except` blocks with `MCPError` responses:
```python
try:
    # Tool logic
except Exception as e:
    logger.error(f"Error: {e}")
    return MCPError(f"Operation failed: {str(e)}")
```

#### Pattern 3: API Client Abstraction
All tools use shared `api_client.get_api_client()` for backend communication:
- Decouples MCP server from direct database access
- Enables PII protection through API layer
- Consistent credential handling

#### Pattern 4: Anonymization for OPSEC/PERSEC
```python
def _anonymize_id(identifier: str, prefix: str) -> str:
    """Hash-based deterministic anonymization."""
    hash_suffix = hashlib.sha256(identifier.encode()).hexdigest()[:6]
    return f"{prefix}-{hash_suffix}"
```

#### Pattern 5: Async/Await for Concurrency
All tools use `async def` with proper `await` for:
- API calls via httpx async client
- Celery task operations
- Database queries (when direct)

### HISTORY: Tool Evolution Timeline

**Phase 1: Core Scheduling (Baseline)**
- Basic validation, contingency analysis, conflict detection
- Swap candidate analysis
- Compliance checking

**Phase 2: Resilience Framework (Tiers 1-2)**
- Utilization threshold monitoring (queuing theory)
- Defense-in-depth levels (5-level system)
- Contingency analysis for power grid model
- Static fallback schedules
- Sacrifice hierarchy execution

**Phase 3: Cross-Disciplinary Analytics (Tier 3+)**
- SPC (Western Electric Rules) for drift detection
- Erlang coverage optimization (telecom queuing)
- Fire danger index (forestry CFFDRS model)
- Burnout epidemiology (SIR models)

**Phase 4: Exotic Frontier Concepts (Tier 5)**
- Kalman filters (control theory)
- Fourier/FFT analysis (signal processing)
- Game theory (Nash equilibrium, Pareto improvements)
- Value-at-Risk (financial engineering)
- Lotka-Volterra (ecology)
- Hopfield networks (neuroscience)

**Phase 5: Advanced Systems (Current)**
- Circuit breaker patterns (infrastructure)
- Time crystal scheduling (quantum-inspired)
- Thermodynamic optimization
- Immune system simulation (AIS)
- FRMS (fatigue risk management)
- Deployment automation

### INSIGHT: Helper Function Philosophy

**Core Pattern:** Modularity through Separation of Concerns

```
server.py (Main orchestrator, 81 tools)
    ├── async_tools.py (4 tools) - Celery lifecycle
    ├── resilience_integration.py (15+ tools) - Tier 1-4
    ├── early_warning_integration.py (8 tools) - STA/LTA, SPC
    ├── composite_resilience_tools.py (4 tools) - Advanced metrics
    ├── deployment_tools.py (9 tools) - CI/CD
    ├── empirical_tools.py (5 tools) - Benchmarking
    ├── circuit_breaker_tools.py (4 tools) - Pattern monitoring
    ├── thermodynamics_tools.py (8 tools) - Energy optimization
    ├── hopfield_attractor_tools.py (4 tools) - Network dynamics
    ├── immune_system_tools.py (3 tools) - AIS simulation
    ├── frms_integration.py (4 tools) - Fatigue management
    ├── time_crystal_tools.py (4 tools) - Anti-churn scheduling
    ├── tools/
    │   ├── game_theory_tools.py - Equilibrium analysis
    │   ├── fourier_analysis_tools.py - Signal processing
    │   ├── kalman_filter_tools.py - Trend extraction
    │   ├── ecological_dynamics_tools.py - Population models
    │   └── var_risk_tools.py - Financial risk metrics
    ├── api_client.py - Backend HTTP abstraction
    ├── domain_context.py - Business logic support
    └── error_handling.py - Consistent error patterns
```

**Helper Functions (Non-Tool):**
- `get_api_client()` - Lazy-loaded httpx AsyncClient
- `_anonymize_id()` - OPSEC/PERSEC ID masking
- `parse_date_range()` - Date string parsing
- Serialization helpers for complex types (date, datetime, UUID)

### RELIGION: Documentation Completeness Audit

**Well-Documented:**
- Core scheduling tools (README.md has examples)
- Async tools (ASYNC_TOOLS.md, ASYNC_TOOLS_QUICK_REFERENCE.md)
- Resilience framework (RESILIENCE_MCP_INTEGRATION.md)
- Deployment tools (docs/deployment-tools.md)

**Partially Documented:**
- Game theory tools (GAME_THEORY_QUICKSTART.md, limited depth)
- Fourier analysis (FOURIER_ANALYSIS_TOOLS.md, technical but sparse)
- VAR risk analysis (VAR_IMPLEMENTATION_SUMMARY.md, brief overview)

**Undocumented Utilities:**
- Kalman filter tools (no standalone guide)
- Ecological dynamics tools (no guide)
- Thermodynamics tools (no guide)
- Hopfield attractor tools (HOPFIELD_TOOLS.md exists but minimal)
- Immune system tools (no guide)
- FRMS integration (no standalone guide)
- Time crystal tools (no guide)
- Circuit breaker tools (error-handling.md mentions but no tool guide)

**Gap:** No centralized MCP tool reference with:
- Complete tool signature listing
- Parameter validation rules
- Error handling patterns by tool
- Cross-tool dependency documentation
- Chaining examples

### NATURE: Tool Redundancy Analysis

**Complementary vs. Redundant:**

| Category | Tools | Redundancy | Reason |
|----------|-------|-----------|--------|
| Schedule Validation | 2 | Complementary | One by date range, one by schedule ID |
| Contingency Analysis | 2 | Complementary | One for scheduling, one for resilience |
| Burnout Detection | 3 | Overlapping | STA/LTA, Fire Index, SIR model - different methods |
| Process Capability | 3 | Complementary | SPC, Erlang, FRMS - different domains |
| Workload Analysis | 4 | Complementary | Shapley value, entropy, VAR, Hopfield - different aspects |
| Risk Assessment | 5 | Overlapping | Fire Index, VAR, Process Capability, FRMS, Thermal |

**No Critical Redundancy** - All tools provide distinct analytical perspectives.

### MEDICINE: Convenience Context

**Context Management:**
- **No Persistent State** - Tools are stateless; context passed via parameters
- **Request/Response Models** - All tools use typed Pydantic models for clarity
- **Error Standardization** - Consistent MCPError format across tools
- **Logging** - All tools use `logging.getLogger(__name__)` for audit trails

**Developer Convenience:**
- **Decorator Pattern** - No boilerplate tool registration
- **Type Validation** - FastMCP auto-validates parameters
- **Docstring Generation** - Tools auto-documented for MCP clients

**Issue:** No context/session management for related operations. Example:
```python
# Currently, AI must track scenario IDs across calls
task_id = start_background_task(resilience_health_check)
# Later, AI must remember task_id to poll
status = get_task_status(task_id)
```

Potential improvement: Session-scoped context caching (not implemented).

### SURVIVAL: Diagnostic Tools

**Core Diagnostics:**
- `get_deployment_status_tool()` - Check deployment health
- `check_circuit_breakers_tool()` - Breaker status monitoring
- `get_breaker_health_tool()` - Detailed breaker diagnostics
- `get_checkpoint_status_tool()` - Time crystal checkpoints
- `get_time_crystal_health_tool()` - Schedule stability metrics
- `get_entropy_monitor_state_tool()` - Entropy/disorder monitoring

**Indirect Diagnostics (via resilience analysis):**
- `get_unified_critical_index_tool()` - Holistic health metric
- `run_spc_analysis_tool()` - Drift detection (indicates problems)
- `detect_burnout_precursors_tool()` - Early warning system

**Coverage Gaps:**
- No tool-level health check (API connectivity test)
- No MCP server performance metrics
- No Celery task queue monitoring (upstream concern)

### STEALTH: Undocumented Utilities

**Deliberate Obfuscation:** None detected.

**Implicit Utilities (Not Exported as Tools):**
1. **Domain Context Module** (`domain_context.py`)
   - Business rule engine for eligibility
   - Credential validation
   - Not exposed as MCP tool

2. **Error Handling Module** (`error_handling.py`)
   - Custom exception types (MCPError, ValidationError, etc.)
   - Logging configuration
   - Not exposed as tool

3. **API Client Module** (`api_client.py`)
   - httpx AsyncClient wrapper
   - Retry logic (exponential backoff)
   - Bearer token injection
   - Connection pooling

4. **Database Utilities** (in resilience_integration.py)
   - Direct DB session management (for performance)
   - Query optimization helpers
   - Not exposed as separate tools

---

## Complete Tool Inventory

### 1. Core Scheduling Tools (5 tools)

| Tool | Function | Parameters | Returns | Purpose |
|------|----------|-----------|---------|---------|
| `validate_schedule_tool` | Validate by date range | `start_date`, `end_date`, check flags | `ScheduleValidationResult` | ACGME compliance |
| `validate_schedule_by_id_tool` | Validate by ID | `schedule_id`, check flags | `ScheduleValidationResult` | Specific schedule audit |
| `run_contingency_analysis_tool` | Impact analysis | `scenario`, `person_ids`, date range | `ContingencyAnalysisResult` | Emergency response |
| `detect_conflicts_tool` | Find conflicts | `date_range`, `conflict_type` | `ConflictDetectionResult` | Proactive conflict prevention |
| `analyze_swap_candidates_tool` | Find swap options | `person_id`, `date_range` | `SwapCandidatesResult` | Schedule flexibility |

**Usage Pattern:**
```python
# Validate schedule for compliance
result = validate_schedule_tool(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 3, 31),
    check_work_hours=True,
    check_supervision=True
)
if not result.is_valid:
    print(f"Found {result.critical_issues} critical issues")
```

---

### 2. Async Task Management Tools (4 tools)

| Tool | Function | Parameters | Returns | Purpose |
|------|----------|-----------|---------|---------|
| `start_background_task_tool` | Start async job | `task_type`, `params` | `BackgroundTaskResult` | Long-running ops |
| `get_task_status_tool` | Poll task | `task_id` | `TaskStatusResult` | Progress monitoring |
| `cancel_task_tool` | Stop task | `task_id` | `CancelTaskResult` | Task lifecycle |
| `list_active_tasks_tool` | View active jobs | None | `ActiveTasksResult` | Queue monitoring |

**Task Types Supported:**
- `resilience_health_check` - System health (1-2 min)
- `resilience_contingency` - N-1/N-2 analysis (2-5 min)
- `resilience_fallback_precompute` - Backup schedules (5-10 min)
- `resilience_utilization_forecast` - Utilization trends (1-3 min)
- `metrics_computation` - Schedule metrics (2-5 min)
- `metrics_snapshot` - Metrics snapshot (30 sec)
- `metrics_cleanup` - Stale metrics cleanup (1 min)
- `metrics_fairness_report` - Equity analysis (2-3 min)

**Usage Pattern:**
```python
# Start long-running analysis
result = start_background_task_tool(
    task_type=TaskType.RESILIENCE_CONTINGENCY,
    params={"days_ahead": 90}
)
task_id = result.task_id

# Poll until complete
import time
while True:
    status = get_task_status_tool(task_id)
    if status.status == TaskStatus.SUCCESS:
        print(f"Result: {status.result}")
        break
    elif status.status == TaskStatus.FAILURE:
        print(f"Error: {status.error}")
        break
    time.sleep(5)
```

---

### 3. Resilience Framework Tools (15+ tools)

#### Tier 1: Core Monitoring (3 tools)

| Tool | Domain | Metric | Thresholds |
|------|--------|--------|-----------|
| `check_utilization_threshold_tool` | Queuing Theory | 80% utilization buffer | GREEN/YELLOW/ORANGE/RED/BLACK |
| `get_defense_level_tool` | Defense-in-Depth | 5-level readiness | PREVENTION → EMERGENCY |
| `run_contingency_analysis_resilience_tool` | Power Grid Model | N-1/N-2 failure impact | Feasibility score |

#### Tier 2: Strategic Analysis (4 tools)

| Tool | Domain | Purpose |
|------|--------|---------|
| `get_static_fallbacks_tool` | Disaster Recovery | Precomputed backup schedules |
| `execute_sacrifice_hierarchy_tool` | Triage System | Load shedding decisions |
| `analyze_homeostasis_tool` | Feedback Loops | Schedule equilibrium |
| `calculate_blast_radius_tool` | Failure Containment | Zone isolation analysis |

#### Tier 3: Advanced Analytics (8 tools)

| Tool | Framework | Source Domain |
|------|-----------|--------------|
| `analyze_le_chatelier_tool` | Equilibrium Shifts | Chemistry |
| `analyze_hub_centrality_tool` | Network Analysis | Graph Theory |
| `assess_cognitive_load_tool` | Burnout Prevention | Psychology |
| `get_behavioral_patterns_tool` | Pattern Recognition | Data Science |
| `analyze_stigmergy_tool` | Swarm Behavior | Ethology |
| `run_spc_analysis_tool` | Statistical Process Control | Manufacturing |
| `calculate_process_capability_tool` | Six Sigma | Manufacturing |
| `optimize_erlang_coverage_tool` | Queuing Theory | Telecommunications |

#### Tier 4: Burnout Epidemiology (4+ tools)

| Tool | Method | Metric |
|------|--------|--------|
| `calculate_burnout_rt_tool` | SIR Model | Reproduction number |
| `simulate_burnout_spread_tool` | Network Contagion | Spread dynamics |
| `simulate_burnout_contagion_tool` | Multi-agent | Intervention outcomes |
| `detect_burnout_precursors_tool` | STA/LTA | Early warning |

**Usage Pattern:**
```python
# Check system health across multiple dimensions
util = check_utilization_threshold_tool()
if util.level in ["RED", "BLACK"]:
    # Escalate to crisis management
    defense = get_defense_level_tool(util.utilization_rate)
    if defense.escalation_needed:
        hierarchy = execute_sacrifice_hierarchy_tool(
            criteria="minimize_burnout"
        )
        print(f"Sacrifice plan: {hierarchy.recommendations}")
```

---

### 4. Early Warning Integration Tools (8 tools)

| Category | Tools | Purpose |
|----------|-------|---------|
| **STA/LTA** | `detect_burnout_precursors_tool`, `predict_burnout_magnitude_tool` | Seismic-inspired burnout detection |
| **SPC** | `run_spc_analysis_tool`, `calculate_workload_process_capability_tool` | Western Electric drift rules |
| **Fire Danger** | `calculate_fire_danger_index_tool`, `calculate_batch_fire_danger_tool` | CFFDRS multi-temporal danger |

**Key Metrics:**
- **STA/LTA Ratio:** Acceleration threshold for burnout signal
- **SPC Rules:** 8 Western Electric rules for out-of-control detection
- **Fire Danger:** Combined temporal factors (drying, wind, temperature)

---

### 5. Deployment Tools (9 tools)

| Phase | Tools | Purpose |
|-------|-------|---------|
| **Validation** | `validate_deployment_tool`, `run_security_scan_tool` | Pre-deployment checks |
| **Testing** | `run_smoke_tests_tool`, `benchmark_solvers_tool` | Sanity validation |
| **Promotion** | `promote_to_production_tool`, `list_deployments_tool` | Release management |
| **Rollback** | `rollback_deployment_tool` | Emergency recovery |
| **Monitoring** | `get_deployment_status_tool` | Health tracking |

---

### 6. Empirical Testing Tools (5 tools)

| Tool | Methodology | Output |
|------|-----------|--------|
| `benchmark_solvers_tool` | Constraint solver performance | Latency, throughput, memory |
| `benchmark_constraints_tool` | Individual constraint cost | Per-constraint overhead |
| `ablation_study_tool` | Feature importance | Tool impact analysis |
| `benchmark_resilience_tool` | Resilience subsystem performance | Recovery metrics |
| `module_usage_analysis_tool` | Function call graph | Dependency analysis |

**Example: Ablation Study**
```
Tool | Impact on Compliance | Impact on Equity | Removal Cost
-----|-------------------|-----------------|-------------
ACGME Validator | -95% compliance | 0% | Highest
Hub Centrality | -5% equity | -20% equity | Medium
Shapley Value | -2% fairness | -15% fairness | Low
```

---

### 7. Thermodynamics & Energy Optimization (8 tools)

| Tool | Concept | Application |
|------|---------|-------------|
| `optimize_free_energy_tool` | Free Energy Principle | Schedule efficiency |
| `calculate_time_crystal_objective_tool` | Anti-churn | Stability metric |
| `analyze_energy_landscape_tool` | Potential wells | Optimal schedule regions |
| `get_entropy_monitor_state_tool` | Disorder measurement | Schedule complexity |
| `analyze_phase_transitions_tool` | State changes | Behavior changes |
| `calculate_schedule_entropy_tool` | Information theory | Diversity metric |
| `analyze_schedule_periodicity_tool` | Fourier analysis | Cycle detection |
| `analyze_schedule_rigidity_tool` | Changeability | Flexibility metric |

**Unified Metric:** `get_unified_critical_index_tool()`
- Combines: Utilization, entropy, rigidity, criticality, burnout Rt
- Output: Single 0-1 health score

---

### 8. Immune System & Advanced Neuroscience (10+ tools)

#### Immune System (AIS)
| Tool | Method | Purpose |
|------|--------|---------|
| `assess_immune_response_tool` | Antigen-antibody | Threat response |
| `check_memory_cells_tool` | Immunological memory | Pattern learning |
| `analyze_antibody_response_tool` | Adaptive immunity | Personalized response |

#### Hopfield Networks
| Tool | Purpose |
|------|---------|
| `calculate_hopfield_energy_tool` | Schedule energy state |
| `find_nearby_attractors_tool` | Stable patterns nearby |
| `measure_basin_depth_tool` | Robustness to perturbations |
| `detect_spurious_attractors_tool` | Anti-patterns |

#### Game Theory
| Tool | Analysis |
|------|----------|
| `analyze_nash_stability_tool` | Equilibrium detection |
| `find_deviation_incentives_tool` | Swap prediction |
| `detect_coordination_failures_tool` | Pareto gaps |

#### Financial Risk
| Tool | Metric |
|------|--------|
| `calculate_coverage_var_tool` | Probabilistic bounds |
| `calculate_workload_var_tool` | Distribution risk |
| `calculate_conditional_var_tool` | Tail risk |
| `simulate_disruption_scenarios_tool` | Monte Carlo stress |

#### Ecological Dynamics
| Tool | Model |
|------|-------|
| `analyze_supply_demand_cycles_tool` | Lotka-Volterra |
| `predict_capacity_crunch_tool` | Crisis forecasting |
| `find_equilibrium_point_tool` | Stable staffing |
| `simulate_intervention_tool` | What-if capacity |

#### Signal Processing
| Tool | Analysis |
|------|----------|
| `detect_schedule_cycles_tool` | FFT periodicity |
| `analyze_harmonic_resonance_tool` | ACGME alignment |
| `calculate_spectral_entropy_tool` | Complexity |

#### Control Theory
| Tool | Purpose |
|------|---------|
| `analyze_workload_trend_tool` | Kalman filtering |
| `detect_workload_anomalies_tool` | Outlier detection |

---

### 9. Fatigue Risk Management (FRMS) Tools (4 tools)

| Tool | Assessment | Output |
|------|-----------|--------|
| `run_frms_assessment_tool` | Full fatigue risk | Comprehensive report |
| `get_fatigue_score_tool` | Single score | 0-100 fatigue index |
| `analyze_sleep_debt_tool` | Cumulative fatigue | Recovery hours needed |
| `evaluate_fatigue_hazard_tool` | Hazard assessment | Risk zones |
| `scan_team_fatigue_tool` | Group fatigue | Team-wide assessment |
| `assess_schedule_fatigue_risk_tool` | Schedule impact | Fatigue from schedule |

---

### 10. Circuit Breaker & Time Crystal Tools

#### Circuit Breaker (Infrastructure Pattern)
| Tool | Function |
|------|----------|
| `check_circuit_breakers_tool` | All breaker status |
| `get_breaker_health_tool` | Detailed metrics |
| `test_half_open_tool` | Recovery testing |
| `override_circuit_breaker_tool` | Manual control |

#### Time Crystal (Anti-Churn)
| Tool | Metric |
|------|--------|
| `get_checkpoint_status_tool` | Discrete state tracking |
| `get_time_crystal_health_tool` | Schedule stability |
| `calculate_recovery_distance_tool` | N-1 recovery edits |

---

### 11. Advanced Metrics & Shapley Value Analysis

| Tool | Analysis |
|------|----------|
| `calculate_shapley_workload_tool` | Fair workload attribution |
| `calculate_equity_metrics_tool` | Fairness indices |
| `generate_lorenz_curve_tool` | Inequality visualization |
| `detect_critical_slowing_down_tool` | Tipping point detection |
| `detect_schedule_changepoints_tool` | Behavioral changes |

---

## Utility Classification Matrix

### By Use Case

| Use Case | Primary Tools | Secondary Tools |
|----------|--------------|-----------------|
| **Compliance Validation** | `validate_schedule_*`, `check_mtf_compliance_tool` | SPC, Erlang, Process Capability |
| **Emergency Response** | `run_contingency_analysis_*`, `execute_sacrifice_hierarchy_tool` | Burnout analysis, Entropy monitoring |
| **Fairness & Equity** | Shapley value, Lorenz curve, Equity metrics | Hub centrality, Stigmergy |
| **Workload Optimization** | Erlang coverage, Free energy, Time crystal | Kalman filtering, Hopfield energy |
| **Burnout Prevention** | STA/LTA precursors, Fire index, FRMS, SIR | Cognitive load, Behavioral patterns |
| **Schedule Stability** | Rigidity, Entropy, Periodicity, Time crystal | Hopfield basin depth, Changepoint detection |
| **Risk Assessment** | VAR metrics, Burnout Rt, Fire danger | Process capability, Contingency analysis |

### By Domain

| Domain | Tools | Maturity | Typical Use |
|--------|-------|----------|------------|
| **Core Scheduling** | 5 | Mature | Daily operations |
| **Resilience** | 15+ | Mature | Scenario planning |
| **Epidemiology** | 4 | Mature | Burnout forecasting |
| **Game Theory** | 3 | Experimental | Behavioral prediction |
| **Signal Processing** | 3 | Experimental | Pattern discovery |
| **Thermodynamics** | 8 | Experimental | Energy optimization |
| **Immune System** | 3 | Research | Novel threat response |
| **FRMS** | 5 | Emerging | Fatigue management |

---

## Integration Patterns & Best Practices

### Pattern 1: Sequential Validation Workflow

```python
# 1. Initial validation
validation = validate_schedule_tool(start, end)
if not validation.is_valid:
    # 2. Identify specific issues
    conflicts = detect_conflicts_tool(date_range)
    # 3. Propose resolutions via swaps
    swaps = analyze_swap_candidates_tool(person_id, date_range)
    # 4. Recommend sacrifices if needed
    sacrifices = execute_sacrifice_hierarchy_tool(criteria)
```

### Pattern 2: Long-Running Analysis with Polling

```python
# Start background task
task = start_background_task_tool(
    TaskType.RESILIENCE_CONTINGENCY,
    {"days_ahead": 90}
)

# Poll in loop until complete
while True:
    status = get_task_status_tool(task.task_id)
    if status.status in [TaskStatus.SUCCESS, TaskStatus.FAILURE]:
        break
    time.sleep(5)

# Retrieve result
result = status.result  # Contains contingency analysis data
```

### Pattern 3: Holistic Health Assessment

```python
# Gather metrics from multiple perspectives
metrics = {
    "utilization": check_utilization_threshold_tool(),
    "defense": get_defense_level_tool(),
    "unified_index": get_unified_critical_index_tool(),
    "burnout": calculate_burnout_rt_tool(),
    "fatigue": get_fatigue_score_tool(),
    "entropy": get_entropy_monitor_state_tool(),
    "rigidity": analyze_schedule_rigidity_tool(),
}

# Synthesize decision
overall_health = metrics["unified_index"].score
if overall_health < 0.3:
    # CRITICAL - activate crisis mode
```

### Pattern 4: Deployment Safety Gate

```python
# Pre-deployment validation
validation = validate_deployment_tool(environment="staging")
security = run_security_scan_tool(environment="staging")
tests = run_smoke_tests_tool(environment="staging")

if all([validation.passed, security.vulnerabilities == 0, tests.passed]):
    # Promote to production
    result = promote_to_production_tool(
        source="staging",
        target="production"
    )
else:
    print("Deployment blocked by safety gates")
```

### Pattern 5: Fair Workload Distribution

```python
# Analyze fairness
shapley = calculate_shapley_workload_tool(
    date_range=(start, end),
    method="shapley"
)

# Visualize inequality
lorenz = generate_lorenz_curve_tool()

# Suggest improvements
equity = calculate_equity_metrics_tool()

# Implement fairness-preserving swaps
for person_id in inequity_list:
    swaps = analyze_swap_candidates_tool(person_id, date_range)
```

---

## Error Handling & Edge Cases

### Standard Error Response Format

```python
class MCPError(BaseModel):
    error: str  # Brief error message
    details: dict[str, Any]  # Additional context
    suggested_action: str | None  # Remediation
```

### Common Error Scenarios

| Scenario | Tool | Handling |
|----------|------|----------|
| **Invalid Date Range** | Validation tools | `ValueError`: "end_date must be >= start_date" |
| **Person Not Found** | Contingency tools | `ValidationError`: "person_id {id} does not exist" |
| **Task Already Complete** | Cancel task | `StateError`: "cannot cancel completed task" |
| **Insufficient Data** | Analytics tools | `DataError`: "minimum 14 days data required" |
| **API Unreachable** | All tools | `ConnectionError`: "backend API unavailable" |
| **Solver Timeout** | Schedule generation | `TimeoutError`: "solver exceeded 300s limit" |

### Retry Strategy

All tools implement exponential backoff (1s, 2s, 4s, 8s, 16s max):

```python
async with get_api_client() as client:
    response = await client.post(url, json=data)
    # Built-in retry on 429, 503, 504
```

---

## Performance Characteristics

### Tool Execution Time Estimates

| Tool Category | Median Duration | P99 | Bottleneck |
|---------------|-----------------|-----|-----------|
| Validation | 200ms | 500ms | API call |
| Contingency analysis | 2s | 5s | Solver optimization |
| Fairness metrics | 500ms | 1.5s | Graph traversal |
| Burnout analysis | 300ms | 1s | DB query |
| Deployment checks | 1s | 3s | External service calls |
| Background tasks | 1-10min | Variable | Task-dependent |

### Concurrency Model

- **Max concurrent calls:** 50 (httpx connection pool)
- **Connection timeout:** 30s
- **Read timeout:** 60s
- **Queue depth (Celery):** 10,000 tasks

---

## Security Considerations

### Input Validation

All tools validate via Pydantic:
```python
class ScheduleValidationRequest(BaseModel):
    start_date: date
    end_date: date
    check_work_hours: bool = True
    # ... additional fields
```

### Output Sanitization

Sensitive fields anonymized:
```python
person_id: str | None = None  # Never exposed raw
role: str | None = None  # Role-based, no PII
anonymized_ref: str = _anonymize_id(person_id)  # Safe for logging
```

### Audit Trail

All tool invocations logged with:
- Timestamp
- Tool name
- Parameters (sanitized)
- Result summary
- Execution time

---

## Undocumented Utilities & Helper Functions

### In `api_client.py`

```python
async def get_api_client() -> AsyncClient:
    """Lazy-loaded httpx client with retry logic."""
    # Singleton pattern
    # Auto-injects Bearer token from env
    # Configures exponential backoff
```

### In `domain_context.py`

```python
def check_credential_eligibility(person_id, slot_type, date):
    """Eligibility engine for slot credential requirements."""
    # Hard constraints (must-have credentials)
    # Soft constraints (nice-to-have, penalties)
    # Window-based expiration logic
```

### In `resilience_integration.py`

```python
def _anonymize_id(identifier, prefix="Provider"):
    """Deterministic hash-based anonymization."""
    # OPSEC/PERSEC compliant
    # Reversible only with original ID
```

### In `error_handling.py`

```python
class MCPError(BaseModel):
    """Standard error response."""

class ValidationError(MCPError):
    """Input validation failed."""

class StateError(MCPError):
    """Invalid state transition."""
```

---

## Tool Chaining Recommendations

### Recommended Call Sequences

**Scenario 1: Emergency Response**
```
1. check_utilization_threshold_tool()
2. get_defense_level_tool()
3. run_contingency_analysis_resilience_tool()
4. execute_sacrifice_hierarchy_tool()
5. list_active_tasks_tool() (optional monitoring)
```

**Scenario 2: Schedule Optimization**
```
1. validate_schedule_tool()
2. analyze_swap_candidates_tool()
3. calculate_shapley_workload_tool()
4. generate_lorenz_curve_tool()
5. analyze_schedule_rigidity_tool()
```

**Scenario 3: Deployment**
```
1. validate_deployment_tool()
2. run_security_scan_tool()
3. run_smoke_tests_tool()
4. benchmark_resilience_tool()
5. promote_to_production_tool()
6. get_deployment_status_tool() (verify)
```

**Scenario 4: Burnout Prevention**
```
1. detect_burnout_precursors_tool()
2. calculate_burnout_rt_tool()
3. run_spc_analysis_tool()
4. calculate_fire_danger_index_tool()
5. get_fatigue_score_tool()
6. assess_cognitive_load_tool()
```

---

## Missing & Potential Utilities

### High-Priority Gaps

1. **Tool Dependency Graph** - No explicit documentation of which tools depend on which
2. **Context Caching** - No session-scoped state management across related calls
3. **Batch Operations** - No bulk validation/analysis endpoint
4. **Tool Composition** - No higher-order tools that chain calls
5. **Metrics Aggregation** - No single "health dashboard" endpoint (though `get_unified_critical_index_tool()` is close)

### Potential New Utilities

1. **Scenario Replay** - Load historical scenarios and replay with different parameters
2. **Tool Profiling** - Performance analysis of individual constraints
3. **Sensitivity Analysis** - What-if parameter sweeps
4. **Diff Generation** - Compare two schedule versions
5. **Plan Execution** - Multi-step plans with checkpoints

---

## FastMCP Framework Integration

### Tool Registration Process

```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP(name="residency-scheduler")

@mcp.tool()
async def validate_schedule_tool(...) -> ScheduleValidationResult:
    """Tool implementation."""
```

### Key Framework Features Used

1. **Type Validation** - Automatic via Pydantic
2. **Documentation Generation** - From docstrings
3. **Error Handling** - Via exception handlers
4. **Transport Abstraction** - SSE, HTTP

### Framework Limitations

- No built-in tool chaining
- No context persistence
- No rate limiting (application-level)
- No authentication hook (relies on API layer)

---

## Resource Availability

### Read-Only Resources

**1. schedule_status**
- Real-time schedule state
- Current assignments
- Coverage metrics
- Refresh: On-demand

**2. compliance_summary**
- ACGME violation list
- Warning thresholds
- Compliance rate
- Refresh: On-demand

---

## Deployment Topologies

### Docker Compose (Recommended)

```yaml
mcp-server:
  image: residency-scheduler-mcp:latest
  environment:
    DATABASE_URL: postgresql://...
    API_BASE_URL: http://backend:8000
  networks:
    - app-network
  ports:
    - "8080:8080"  # HTTP
```

### HTTP Transport (Production)

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "type": "http",
      "url": "http://localhost:8088/mcp"
    }
  }
}
```

---

## Tool Usage Statistics

### Tier 1 (High Utility)

**Most Used Tools:**
1. `validate_schedule_tool` - Pre-deployment safety
2. `check_utilization_threshold_tool` - Continuous monitoring
3. `detect_conflicts_tool` - Proactive conflict prevention
4. `get_task_status_tool` - Async operation tracking
5. `get_unified_critical_index_tool` - Health synthesis

### Tier 2 (Medium Utility)

**Conditional Use:**
- Contingency analysis (emergency-driven)
- Burnout forecasting (periodic monitoring)
- Fairness metrics (compliance audits)
- Deployment validation (CI/CD gates)

### Tier 3 (Research/Experimental)

**Exploratory Use:**
- Game theory equilibrium
- Exotic frontier concepts
- Signal processing analysis
- Thermodynamic optimization

---

## Conclusion: SEARCH_PARTY Findings Summary

### Strengths
1. **Comprehensive Coverage** - 81 tools across 8 domains, no critical gaps
2. **Well-Integrated** - Standard patterns, consistent error handling, async-first
3. **Modular Architecture** - Tools organized by domain, easy to discover and extend
4. **Security-Aware** - OPSEC/PERSEC compliance, PII protection, audit trails
5. **Production-Ready** - Exponential backoff, connection pooling, comprehensive validation

### Weaknesses
1. **Documentation Fragmentation** - 10+ docs, no single comprehensive reference
2. **No Tool Dependency Graph** - Implicit relationships, hard to chain optimally
3. **Limited Context Management** - Tools are stateless, complex multi-step workflows need external orchestration
4. **Missing Batch Operations** - Single-item processing, no bulk operations
5. **Experimental Tools Underdocumented** - Exotic frontier concepts lack usage examples

### Recommendations
1. **Create Unified Tool Reference** - Single source of truth for all 81 tools
2. **Implement Tool Composition Framework** - Higher-order tools that chain calls
3. **Add Context Manager** - Session-scoped state for related operations
4. **Develop Scenario Playbooks** - Pre-built multi-step workflows
5. **Add Batch Operations** - Bulk validation, metrics computation

---

**Document Version:** 1.0
**Last Updated:** 2025-12-30
**Status:** Complete
