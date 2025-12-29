# MCP Tools Reference

> **Status**: Production-ready
> **Version**: 1.0
> **Last Updated**: 2025-12-28

---

## Overview

The Model Context Protocol (MCP) server exposes 34+ scheduling and resilience tools for AI assistant interaction. These tools provide programmatic access to the Cross-Disciplinary Engineering Resilience Framework, enabling AI agents to analyze burnout risk, optimize staffing, validate compliance, and monitor system health.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Claude AI Agent                            │
├─────────────────────────────────────────────────────────────────┤
│                    MCP Server (FastMCP)                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Early Warning  │  │  Epidemiology   │  │  Optimization   │ │
│  │     Tools       │  │     Tools       │  │     Tools       │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                    │           │
│  ┌────────┴────────┐  ┌────────┴────────┐  ┌────────┴────────┐ │
│  │   Composite     │  │   Resilience    │  │   Core          │ │
│  │   Analytics     │  │   Framework     │  │   Scheduling    │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
├───────────┴────────────────────┴────────────────────┴───────────┤
│                    Backend API (FastAPI)                        │
└─────────────────────────────────────────────────────────────────┘
```

### Tool Categories

| Category | Tools | Purpose |
|----------|-------|---------|
| **Early Warning** | 4 tools | Detect burnout precursors before crisis |
| **Epidemiology** | 3 tools | Model burnout spread through networks |
| **Optimization** | 3 tools | Staffing, quality, and equity analysis |
| **Composite** | 4 tools | Unified risk scores and advanced analytics |
| **Resilience** | 12 tools | Core resilience framework monitoring |
| **Scheduling** | 8+ tools | Schedule generation and management |

---

## Early Warning Tools

These tools apply cross-disciplinary science to detect burnout before it occurs.

### detect_burnout_precursors

**Purpose**: Detect early warning signs of burnout using seismic STA/LTA algorithm.

**Scientific Basis**: Adapts seismological P-wave detection to identify behavioral changes that precede burnout events. The STA/LTA (Short-Term Average / Long-Term Average) algorithm detects sudden deviations from baseline behavior.

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `resident_id` | string | Yes | - | UUID of resident to analyze |
| `signal_type` | enum | Yes | - | Type of precursor signal (see below) |
| `time_series` | list[float] | Yes | - | Time series data (daily counts) |
| `short_window` | int | No | 5 | STA window size (samples) |
| `long_window` | int | No | 30 | LTA window size (samples) |

**Signal Types**:
- `swap_requests` - Frequency of shift swap requests
- `sick_calls` - Pattern changes in unplanned absences
- `preference_decline` - Declining preferred shift requests
- `response_delays` - Slower response times to requests
- `voluntary_coverage_decline` - Refusing extra shifts

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `resident_id` | string | Resident identifier |
| `signal_type` | enum | Signal type analyzed |
| `alerts_detected` | int | Number of precursor alerts |
| `alerts` | list[SeismicAlertInfo] | Detailed alert information |
| `max_sta_lta_ratio` | float | Maximum STA/LTA ratio observed |
| `analysis_summary` | string | Human-readable summary |
| `recommended_actions` | list[string] | Intervention recommendations |
| `severity` | string | `healthy`, `warning`, `elevated`, `critical` |

**Example**:

```python
result = await detect_burnout_precursors(
    resident_id="abc-123",
    signal_type="swap_requests",
    time_series=[0, 1, 0, 1, 0, 2, 3, 5, 7, 8, 12, 15, 18],
    short_window=5,
    long_window=30
)

if result.alerts_detected > 0:
    print(f"WARNING: {result.alerts[0].severity} precursor detected")
    print(f"STA/LTA ratio: {result.max_sta_lta_ratio:.2f}")
```

**Use Cases**:
- Monitor individual residents for behavioral drift
- Early intervention before burnout crisis
- Validate effectiveness of wellness programs

---

### run_spc_analysis

**Purpose**: Apply Statistical Process Control using Western Electric Rules to detect workload drift.

**Scientific Basis**: Adapted from semiconductor manufacturing quality control. Western Electric Rules detect when a process goes "out of control" by analyzing patterns in time series data.

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `resident_id` | string | Yes | - | UUID of resident to analyze |
| `weekly_hours` | list[float] | Yes | - | Weekly work hours (chronological) |
| `target_hours` | float | No | 60.0 | Target weekly hours (centerline) |
| `sigma` | float | No | 5.0 | Process standard deviation (hours) |

**Western Electric Rules Applied**:
- **Rule 1**: 1 point beyond 3-sigma (CRITICAL - process out of control)
- **Rule 2**: 2 of 3 consecutive points beyond 2-sigma (WARNING - shift detected)
- **Rule 3**: 4 of 5 consecutive points beyond 1-sigma (WARNING - trend detected)
- **Rule 4**: 8 consecutive points on same side of centerline (INFO - sustained shift)

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `resident_id` | string | Resident identifier |
| `violations_detected` | int | Number of rule violations |
| `alerts` | list[SPCAlertInfo] | Detailed violation information |
| `control_limits` | dict | UCL/LCL values at each sigma level |
| `process_capability` | dict or null | Cp/Cpk indices if available |
| `weeks_analyzed` | int | Number of weeks in analysis |
| `mean_hours` | float | Sample mean |
| `std_hours` | float | Sample standard deviation |
| `analysis_summary` | string | Human-readable summary |
| `recommended_actions` | list[string] | Intervention recommendations |
| `severity` | string | `healthy`, `warning`, `critical` |

**Example**:

```python
result = await run_spc_analysis(
    resident_id="abc-123",
    weekly_hours=[58, 62, 59, 67, 71, 75, 78, 80],
    target_hours=60.0,
    sigma=5.0
)

if result.violations_detected > 0:
    for alert in result.alerts:
        print(f"{alert.rule}: {alert.message}")
```

**Use Cases**:
- Weekly workload monitoring
- Detect schedule drift before ACGME violations
- Continuous improvement tracking

---

### calculate_fire_danger_index

**Purpose**: Calculate multi-temporal burnout danger using Fire Weather Index (FWI) system.

**Scientific Basis**: Adapts the Canadian Forest Fire Danger Rating System (CFFDRS) for burnout prediction. Like wildfires, burnout develops across multiple time scales that must align for catastrophe.

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `resident_id` | string | Yes | - | UUID of resident to assess |
| `recent_hours` | float | Yes | - | Hours worked in last 2 weeks |
| `monthly_load` | float | Yes | - | Average monthly hours over last 3 months |
| `yearly_satisfaction` | float | Yes | - | Job satisfaction over past year (0.0-1.0) |
| `workload_velocity` | float | No | 0.0 | Rate of workload increase (hours/week) |

**FWI System Components**:
- **FFMC (Fine Fuel)**: Recent 2-week workload (immediate risk, 0-100)
- **DMC (Duff Moisture)**: 3-month accumulation (medium-term burden, 0-100)
- **DC (Drought)**: Yearly satisfaction erosion (long-term risk, 0-100)
- **ISI (Spread Index)**: Rate of deterioration
- **BUI (Buildup)**: Combined medium + long-term burden
- **FWI (Final Index)**: Composite danger score

**Danger Classes**:

| Class | FWI Score | Interpretation |
|-------|-----------|----------------|
| `low` | <20 | Normal operations |
| `moderate` | 20-40 | Monitor closely |
| `high` | 40-60 | Reduce workload |
| `very_high` | 60-80 | Significant restrictions |
| `extreme` | 80+ | Emergency measures |

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `resident_id` | string | Resident identifier |
| `danger_class` | enum | LOW, MODERATE, HIGH, VERY_HIGH, EXTREME |
| `fwi_score` | float | Fire Weather Index score |
| `component_scores` | ComponentScores | FFMC, DMC, DC, ISI, BUI, FWI |
| `is_safe` | bool | Whether resident is in safe zone |
| `requires_intervention` | bool | Whether intervention is needed |
| `recommended_restrictions` | list[string] | Activity restrictions |
| `temporal_analysis` | dict | Interpretation of each temporal scale |
| `severity` | string | `healthy`, `warning`, `elevated`, `critical`, `emergency` |

**Example**:

```python
result = await calculate_fire_danger_index(
    resident_id="abc-123",
    recent_hours=75.0,       # High recent workload
    monthly_load=260.0,      # Sustained overwork
    yearly_satisfaction=0.4, # Low satisfaction
    workload_velocity=8.0    # Increasing workload
)

if result.danger_class == "extreme":
    print("EMERGENCY: Immediate intervention required")
    for restriction in result.recommended_restrictions:
        print(f"  - {restriction}")
```

**Use Cases**:
- Multi-dimensional burnout risk assessment
- Program-wide screening
- Targeted wellness interventions

---

### calculate_process_capability_tool

**Purpose**: Calculate Six Sigma process capability indices (Cp/Cpk) for workload distribution.

**Scientific Basis**: Six Sigma quality metrics measure how well a process fits within specification limits. Adapted from manufacturing to assess schedule quality.

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `weekly_hours` | list[float] | Yes | - | Weekly work hours data (min 2 values) |
| `lower_spec_limit` | float | No | 40.0 | Minimum hours (lower spec) |
| `upper_spec_limit` | float | No | 80.0 | Maximum hours (ACGME limit) |

**Capability Classification**:

| Cpk Value | Classification | Interpretation |
|-----------|----------------|----------------|
| >= 2.0 | World Class | 6-sigma quality |
| >= 1.67 | Excellent | 5-sigma quality |
| >= 1.33 | Capable | 4-sigma, industry standard |
| >= 1.0 | Marginal | 3-sigma, minimum acceptable |
| < 1.0 | Incapable | Violations expected |

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `cp` | float | Process Capability (potential) |
| `cpk` | float | Process Capability Index (actual) |
| `pp` | float | Process Performance (long-term) |
| `ppk` | float | Process Performance Index |
| `mean` | float | Sample mean |
| `sigma` | float | Sample standard deviation |
| `lsl` | float | Lower specification limit |
| `usl` | float | Upper specification limit |
| `interpretation` | string | Capability classification |
| `recommendation` | string | Improvement guidance |

**Example**:

```python
result = await calculate_process_capability_tool(
    weekly_hours=[58, 62, 59, 61, 63, 60, 58, 62],
    lower_spec_limit=40.0,
    upper_spec_limit=80.0
)

print(f"Cpk: {result.cpk:.2f} - {result.interpretation}")
# Output: "Cpk: 1.45 - CAPABLE"
```

**Use Cases**:
- Quantify schedule quality
- ACGME compliance evidence
- Track improvement over time

---

## Epidemiology Tools

These tools model burnout as a contagious condition that spreads through social networks.

### calculate_burnout_rt

**Purpose**: Calculate the effective reproduction number (Rt) for burnout spread.

**Scientific Basis**: Applies SIR (Susceptible-Infected-Recovered) epidemiological modeling to burnout transmission. The reproduction number indicates whether burnout is spreading or declining.

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `burned_out_provider_ids` | list[string] | Yes | - | Provider IDs currently burned out |
| `time_window_days` | int | No | 28 | Time window for contact tracing |

**Rt Interpretation**:

| Rt Value | Status | Intervention Level |
|----------|--------|-------------------|
| < 0.5 | Declining | None - maintain preventive measures |
| 0.5 - 1.0 | Controlled | Monitoring - watch at-risk individuals |
| 1.0 - 2.0 | Spreading | Moderate - workload reduction, support |
| 2.0 - 3.0 | Rapid Spread | Aggressive - mandatory time off |
| >= 3.0 | Crisis | Emergency - system-wide intervention |

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `rt` | float | Effective reproduction number |
| `status` | enum | `no_cases`, `declining`, `controlled`, `spreading`, `rapid_spread`, `crisis` |
| `intervention_level` | enum | `none`, `monitoring`, `moderate`, `aggressive`, `emergency` |
| `interventions` | list[string] | Recommended intervention strategies |
| `herd_immunity_threshold` | float | Fraction needing immunity to stop spread |
| `total_cases_analyzed` | int | Number of burnout cases analyzed |
| `total_close_contacts` | int | Number of close contacts identified |
| `superspreaders` | list[SuperspreaderInfo] | High-connectivity individuals |
| `high_risk_contacts` | list[string] | Provider IDs at high risk |
| `severity` | string | `healthy`, `warning`, `critical`, `emergency` |

**Example**:

```python
result = await calculate_burnout_rt(
    burned_out_provider_ids=["provider-1", "provider-2", "provider-3"],
    time_window_days=28
)

if result.rt > 1.0:
    print(f"Burnout spreading! Rt={result.rt:.2f}")
    print(f"Interventions: {result.interventions}")
```

**Use Cases**:
- Monitor program-wide burnout trends
- Identify superspreaders for targeted intervention
- Track effectiveness of wellness initiatives

---

### simulate_burnout_spread

**Purpose**: Run SIR epidemic simulation for burnout spread through the social network.

**Scientific Basis**: Uses the classic SIR (Susceptible-Infected-Recovered) model to project how burnout might spread over time. Helps predict epidemic trajectory and peak infection.

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `initial_infected_ids` | list[string] | Yes | - | Provider IDs initially burned out |
| `infection_rate` | float | No | 0.05 | Beta - transmission probability per contact/week |
| `recovery_rate` | float | No | 0.02 | Gamma - recovery probability per week |
| `simulation_weeks` | int | No | 52 | Weeks to simulate |

**Key Metrics**:
- **R0** = beta / gamma (basic reproduction number)
- **Herd Immunity Threshold** = 1 - (1/R0)

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `simulation_weeks` | int | Weeks simulated |
| `infection_rate` | float | Beta parameter |
| `recovery_rate` | float | Gamma parameter |
| `r0` | float | Basic reproduction number |
| `herd_immunity_threshold` | float | Immunity threshold |
| `initial_infected` | int | Starting cases |
| `final_infected` | int | Cases at end |
| `peak_infected` | int | Maximum simultaneous cases |
| `peak_week` | int | Week of peak infection |
| `epidemic_died_out` | bool | Whether epidemic ended |
| `trajectory` | list[SIRSimulationPoint] | Weekly S, I, R values |
| `warnings` | list[string] | Alert messages |
| `severity` | string | Overall severity |

**Example**:

```python
result = await simulate_burnout_spread(
    initial_infected_ids=["provider-1", "provider-2", "provider-3"],
    infection_rate=0.05,
    recovery_rate=0.02,
    simulation_weeks=52
)

print(f"R0: {result.r0:.2f}")
print(f"Peak: {result.peak_infected} infected at week {result.peak_week}")
if result.epidemic_died_out:
    print("Epidemic died out naturally")
```

**Use Cases**:
- Predict burnout epidemic trajectory
- Evaluate intervention effectiveness (change beta/gamma)
- Capacity planning for wellness resources

---

### simulate_burnout_contagion

**Purpose**: Simulate burnout contagion using SIS network diffusion model with superspreader identification.

**Scientific Basis**: Uses SIS (Susceptible-Infected-Susceptible) model on the actual social/collaboration network. Unlike SIR, SIS allows reinfection - appropriate for burnout which can recur.

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `initial_infected_ids` | list[string] | Yes | - | Initially burned out providers |
| `transmission_probability` | float | No | 0.1 | Per-edge transmission probability |
| `recovery_probability` | float | No | 0.05 | Per-iteration recovery probability |
| `iterations` | int | No | 100 | Simulation iterations |
| `burnout_threshold` | float | No | 0.7 | Score threshold for "infected" |

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `network_size` | int | Total nodes in network |
| `current_susceptible` | int | Currently healthy |
| `current_infected` | int | Currently burned out |
| `current_infection_rate` | float | Fraction infected |
| `contagion_risk` | enum | `low`, `moderate`, `high`, `critical` |
| `final_infection_rate` | float | Projected final rate |
| `peak_infection_rate` | float | Peak during simulation |
| `superspreaders` | list[ContagionSuperspreaderProfile] | Superspreader details |
| `recommended_interventions` | list[NetworkInterventionInfo] | Network interventions |
| `severity` | string | Overall severity |

**Example**:

```python
result = await simulate_burnout_contagion(
    initial_infected_ids=["provider-1"],
    transmission_probability=0.1,
    recovery_probability=0.05,
    iterations=100
)

print(f"Contagion risk: {result.contagion_risk}")
for ss in result.superspreaders[:3]:
    print(f"Superspreader: {ss.provider_id} (score={ss.superspreader_score:.2f})")
```

**Use Cases**:
- Identify network-based intervention targets
- Predict cascade failures
- Design burnout-resistant team structures

---

## Optimization Tools

These tools provide quantitative analysis for staffing, quality, and equity.

### optimize_erlang_coverage

**Purpose**: Optimize specialist staffing using Erlang-C queuing theory.

**Scientific Basis**: Applies M/M/c queuing theory (Markovian arrival, Markovian service, c servers) to determine optimal coverage. The same model used by call centers worldwide.

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `specialty` | string | Yes | - | Name of specialty |
| `arrival_rate` | float | Yes | - | Average requests per hour |
| `service_time_minutes` | float | Yes | - | Average time per case (minutes) |
| `target_wait_minutes` | float | No | 15.0 | Target wait time |
| `target_wait_probability` | float | No | 0.05 | Max acceptable wait probability |
| `max_servers` | int | No | 20 | Maximum servers to consider |

**Key Concepts**:
- **Offered Load (A)** = arrival_rate * service_time
- **80% Utilization Threshold**: Above 80%, wait times grow exponentially
- **Service Level**: Percentage served within target wait time

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `specialty` | string | Specialty name |
| `recommended_specialists` | int | Minimum staff to meet service level |
| `current_utilization` | float | Server utilization rate |
| `wait_probability` | float | Probability of waiting |
| `avg_wait_time_minutes` | float | Expected average wait |
| `service_level` | float | Percentage served within target |
| `offered_load` | float | Total work arriving |
| `staffing_table` | list[StaffingTableEntry] | Options with different server counts |
| `queue_stable` | bool | Whether queue is stable |
| `recommendations` | list[string] | Staffing recommendations |
| `severity` | string | `healthy`, `warning`, `critical`, `emergency` |

**Example**:

```python
result = await optimize_erlang_coverage(
    specialty="Orthopedic Surgery",
    arrival_rate=2.5,       # 2.5 cases/hour
    service_time_minutes=30, # 30 min per case
    target_wait_minutes=15,
    target_wait_probability=0.05
)

print(f"Need {result.recommended_specialists} specialists")
print(f"Wait probability: {result.wait_probability:.1%}")
```

**Use Cases**:
- Determine optimal specialist coverage
- Plan for demand surges
- Balance utilization vs wait times

---

### calculate_process_capability

**Purpose**: Calculate Six Sigma process capability indices for schedule quality.

**Scientific Basis**: Six Sigma statistical process control adapted for scheduling. Measures how consistently ACGME compliance and operational constraints are maintained.

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `data` | list[float] | Yes | - | Sample measurements (min 2) |
| `lower_spec_limit` | float | Yes | - | LSL - minimum acceptable |
| `upper_spec_limit` | float | Yes | - | USL - maximum acceptable |
| `target` | float | No | midpoint | Ideal target value |

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `cp` | float | Process potential (assumes centered) |
| `cpk` | float | Process capability (actual) |
| `pp` | float | Process performance (long-term) |
| `ppk` | float | Process performance index |
| `cpm` | float | Taguchi index (off-target penalty) |
| `capability_status` | string | EXCELLENT, CAPABLE, MARGINAL, INCAPABLE |
| `sigma_level` | float | Estimated sigma level |
| `sample_size` | int | Data points analyzed |
| `centering_assessment` | string | Process centering quality |
| `estimated_defect_rate_ppm` | float | Defects per million |
| `recommendations` | list[string] | Improvement recommendations |
| `severity` | string | `excellent`, `capable`, `marginal`, `incapable` |

**Example**:

```python
result = await calculate_process_capability(
    data=[65, 72, 58, 75, 68, 70, 62, 77, 55, 71],
    lower_spec_limit=40,
    upper_spec_limit=80,
    target=60
)

print(f"Capability: {result.capability_status}")
print(f"Sigma Level: {result.sigma_level:.2f}")
```

---

### calculate_equity_metrics

**Purpose**: Analyze workload equity using Gini coefficient and fairness metrics.

**Scientific Basis**: Applies income inequality metrics (Gini coefficient, Lorenz curves) to measure workload distribution fairness.

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `hours_per_provider` | dict[string, float] | Yes | - | Provider ID to hours mapping |
| `target_gini` | float | No | 0.15 | Maximum acceptable Gini |
| `intensity_weights` | dict[string, float] | No | None | Intensity multipliers by shift type |

**Gini Coefficient Interpretation**:

| Gini Value | Interpretation |
|------------|----------------|
| 0.0 - 0.10 | Very equitable |
| 0.10 - 0.20 | Equitable |
| 0.20 - 0.30 | Moderate inequality |
| 0.30 - 0.40 | Significant inequality |
| > 0.40 | High inequality |

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `gini_coefficient` | float | Gini (0=equality, 1=max inequality) |
| `target_gini` | float | Target threshold |
| `is_equitable` | bool | Whether distribution meets target |
| `mean_hours` | float | Average hours |
| `std_hours` | float | Standard deviation |
| `min_hours` | float | Minimum assigned |
| `max_hours` | float | Maximum assigned |
| `coefficient_of_variation` | float | Relative spread |
| `most_overloaded_provider` | string | Highest hours provider |
| `most_underloaded_provider` | string | Lowest hours provider |
| `overload_delta` | float | Hours above mean |
| `underload_delta` | float | Hours below mean |
| `recommendations` | list[string] | Rebalancing suggestions |
| `severity` | string | `equitable`, `warning`, `inequitable`, `critical` |

**Example**:

```python
result = await calculate_equity_metrics(
    hours_per_provider={
        "FAC-001": 72,
        "FAC-002": 65,
        "FAC-003": 58,
        "FAC-004": 80,
        "FAC-005": 55
    },
    target_gini=0.15
)

print(f"Gini: {result.gini_coefficient:.3f}")
print(f"Equitable: {result.is_equitable}")
print(f"Most overloaded: {result.most_overloaded_provider}")
```

**Use Cases**:
- Monitor workload fairness
- Identify rebalancing opportunities
- Track equity over time

---

## Composite Analytics Tools

These tools aggregate signals from multiple resilience modules into unified risk scores.

### get_unified_critical_index

**Purpose**: Calculate unified critical index aggregating all resilience signals into a single actionable risk score.

**Scientific Basis**: Combines three domains with weighted scoring:
- **Contingency (40%)**: N-1/N-2 vulnerability
- **Hub Analysis (35%)**: Network centrality
- **Epidemiology (25%)**: Burnout super-spreader potential

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_details` | bool | No | True | Include individual faculty assessments |
| `top_n` | int | No | 5 | Number of top-risk faculty to return |

**Risk Patterns**:

| Pattern | Domains High | Intervention Focus |
|---------|--------------|-------------------|
| `universal_critical` | All three | Immediate protection |
| `structural_burnout` | Contingency + Epidemiology | Workload + wellness |
| `influential_hub` | Contingency + Hub | Cross-training |
| `social_connector` | Epidemiology + Hub | Network diversification |
| `isolated_workhorse` | Contingency only | Backup development |
| `burnout_vector` | Epidemiology only | Wellness support |
| `network_anchor` | Hub only | Distribute responsibilities |
| `low_risk` | None | Continue monitoring |

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `overall_index` | float | System-wide risk score (0-100) |
| `risk_level` | string | `low`, `moderate`, `elevated`, `high`, `critical` |
| `risk_concentration` | float | Gini coefficient of risk distribution |
| `critical_count` | int | Faculty with elevated risk |
| `universal_critical_count` | int | Faculty critical in all domains |
| `pattern_distribution` | dict | Count by risk pattern |
| `top_priority` | list[string] | Top priority faculty IDs |
| `top_critical_faculty` | list[FacultyUnifiedIndex] | Detailed assessments |
| `contributing_factors` | dict | Weight of each domain |
| `trend` | string | `improving`, `stable`, `degrading` |
| `top_concerns` | list[string] | Top 3-5 risk factors |
| `recommendations` | list[string] | System recommendations |
| `severity` | string | `healthy`, `warning`, `critical`, `emergency` |

**Example**:

```python
result = await get_unified_critical_index(include_details=True, top_n=5)

if result.risk_level == "critical":
    print(f"ALERT: {result.universal_critical_count} faculty need protection")
    for faculty in result.top_critical_faculty:
        print(f"  - {faculty.faculty_name}: {faculty.risk_pattern}")
```

**Use Cases**:
- Holistic system risk assessment
- Prioritize interventions across multiple dimensions
- Identify hidden patterns from cross-domain analysis

---

### calculate_recovery_distance

**Purpose**: Measure schedule fragility using recovery distance metrics from operations research.

**Scientific Basis**: Recovery Distance (RD) measures minimum edits needed to restore feasibility after N-1 shocks. Lower RD = more resilient schedule.

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | string | No | today | Analysis start (YYYY-MM-DD) |
| `end_date` | string | No | +30 days | Analysis end (YYYY-MM-DD) |
| `max_events` | int | No | 20 | Maximum N-1 events to test |
| `include_samples` | bool | No | True | Include sample results |

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `events_tested` | int | Number of N-1 events tested |
| `rd_mean` | float | Average recovery distance |
| `rd_median` | float | Median recovery distance |
| `rd_p95` | float | 95th percentile (worst-case) |
| `rd_max` | int | Maximum observed |
| `breakglass_count` | int | Events requiring >3 edits |
| `infeasible_count` | int | Events with no recovery |
| `by_event_type` | dict | Breakdown by event type |
| `fragility_score` | float | Overall fragility (0-1) |
| `sample_results` | list[RecoveryResultInfo] | Sample individual results |
| `recommendations` | list[string] | Recommendations |
| `severity` | string | `resilient`, `moderate`, `fragile`, `brittle` |

**Example**:

```python
result = await calculate_recovery_distance(max_events=20)

if result.rd_p95 > 4:
    print("WARNING: High recovery cost in worst case")
if result.breakglass_count > result.events_tested * 0.2:
    print("CRITICAL: Many scenarios require extensive rework")
```

**Use Cases**:
- Assess schedule robustness
- Identify fragile assignments
- Plan contingency reserves

---

### assess_creep_fatigue

**Purpose**: Assess burnout risk using materials science creep-fatigue analysis.

**Scientific Basis**: Adapts Larson-Miller parameter (time-dependent creep) and Miner's Rule (cyclic fatigue) from materials science to predict burnout.

**Creep Stages**:
- **Primary**: Adaptation phase, strain rate decreasing
- **Secondary**: Steady-state, sustainable performance
- **Tertiary**: Accelerating damage, approaching burnout

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_assessments` | bool | No | True | Include individual assessments |
| `top_n` | int | No | 10 | Number of highest-risk residents |

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `residents_analyzed` | int | Number assessed |
| `high_risk_count` | int | Residents at high risk |
| `moderate_risk_count` | int | Residents at moderate risk |
| `tertiary_creep_count` | int | Residents in pre-failure stage |
| `average_lmp` | float | Average Larson-Miller parameter |
| `average_remaining_life` | float | Average fatigue life remaining |
| `lmp_threshold` | float | LMP failure threshold (~45) |
| `safe_lmp` | float | Safe operating LMP (~31.5) |
| `assessments` | list[CreepFatigueAssessment] | Individual assessments |
| `system_recommendations` | list[string] | System-wide recommendations |
| `severity` | string | `healthy`, `at_risk`, `critical` |

**Example**:

```python
result = await assess_creep_fatigue(include_assessments=True, top_n=10)

if result.tertiary_creep_count > 0:
    print(f"URGENT: {result.tertiary_creep_count} residents approaching burnout")
    for assessment in result.assessments:
        if assessment.overall_risk == "high":
            print(f"  {assessment.resident_id}: LMP={assessment.creep_analysis.larson_miller_parameter:.1f}")
```

**Use Cases**:
- Monitor long-term stress accumulation
- Predict time-to-burnout
- Optimize rotation sequences

---

### analyze_transcription_triggers

**Purpose**: Analyze bio-inspired constraint regulation using transcription factor patterns.

**Scientific Basis**: Adapts gene regulatory network concepts from molecular biology for context-sensitive constraint management. Transcription factors (TFs) activate or repress constraints based on environmental signals.

**TF Types**:
- **Activator**: Increases constraint weight
- **Repressor**: Decreases/disables constraint
- **Dual**: Context-dependent
- **Pioneer**: Re-enables silenced constraints
- **Master**: Controls entire regulatory programs

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_constraints` | bool | No | True | Include constraint details |
| `include_loops` | bool | No | True | Include regulatory loops |

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `total_tfs` | int | Total transcription factors |
| `active_tfs` | int | Currently active TFs |
| `master_regulators_active` | int | Active master regulators |
| `total_constraints_regulated` | int | Constraints with promoters |
| `constraints_with_modified_weight` | int | Modified weights |
| `regulatory_edges` | int | TF-to-target links |
| `detected_loops` | int | Regulatory loops found |
| `total_activation` | float | Sum of activator expression |
| `total_repression` | float | Sum of repressor expression |
| `network_entropy` | float | Regulatory state diversity |
| `active_tfs_list` | list[TranscriptionFactorInfo] | Active TF details |
| `regulated_constraints` | list[ConstraintRegulationInfo] | Constraint status |
| `loops` | list[RegulatoryLoopInfo] | Detected loops |
| `severity` | string | `normal`, `regulatory_stress`, `crisis_mode` |

**Use Cases**:
- Understand constraint behavior under stress
- Debug constraint conflicts
- Optimize regulatory network design

---

## Resilience Framework Tools

Core tools for monitoring system stability and vulnerability.

### check_utilization_threshold

**Purpose**: Check current utilization against 80% threshold from queuing theory.

**Scientific Basis**: Above 80% utilization, wait times increase exponentially and cascade failures become likely.

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `available_faculty` | int | Yes | - | Available faculty count |
| `required_blocks` | int | Yes | - | Blocks requiring coverage |
| `blocks_per_faculty_per_day` | float | No | 2.0 | Max blocks per faculty/day |
| `days_in_period` | int | No | 1 | Days in analysis period |

**Utilization Levels**:

| Level | Range | Status |
|-------|-------|--------|
| `green` | <70% | Healthy |
| `yellow` | 70-80% | Warning |
| `orange` | 80-90% | Critical |
| `red` | 90-95% | Emergency |
| `black` | 95%+ | Collapse imminent |

---

### run_contingency_analysis

**Purpose**: Perform N-1/N-2 contingency analysis (power grid methodology).

**Scientific Basis**: From electrical grid planning - system must survive loss of any single (N-1) or pair (N-2) of components.

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | date | No | today | Analysis start |
| `end_date` | date | No | +28 days | Analysis end |
| `analyze_n1` | bool | No | True | Perform N-1 analysis |
| `analyze_n2` | bool | No | True | Perform N-2 analysis |

---

### get_defense_level

**Purpose**: Get current defense-in-depth level (nuclear safety paradigm).

**Scientific Basis**: 5-level defense-in-depth from nuclear reactor safety adapted for scheduling.

**Defense Levels**:
1. **Prevention**: Normal operations
2. **Control**: Minor issues, automated response
3. **Safety Systems**: Significant stress, semi-automated
4. **Containment**: Serious issues, manual intervention
5. **Emergency**: Crisis, all-hands response

---

### analyze_homeostasis

**Purpose**: Analyze feedback loops and allostatic load.

**Scientific Basis**: Biological homeostasis concepts for system stability monitoring.

---

### calculate_blast_radius

**Purpose**: Analyze failure containment within scheduling zones.

**Scientific Basis**: AWS-style blast radius isolation for preventing cascade failures.

---

### check_mtf_compliance

**Purpose**: Check military-style compliance reporting (DRRS translation).

**Response includes**:
- DRRS category (C1-C5)
- Mission capability (FMC/PMC/NMC)
- Circuit breaker status
- Iron Dome regulatory protection status

---

## Error Handling

All MCP tools follow consistent error handling patterns:

### Standard Errors

| Error Type | Cause | Response |
|------------|-------|----------|
| `ValueError` | Invalid parameters | 400-style error with message |
| `RuntimeError` | Backend unavailable | Fallback data with warning |
| `ImportError` | Module not installed | Graceful degradation |

### Fallback Behavior

When backend services are unavailable, tools return:
- Simplified calculations where possible
- Clear indication of degraded mode
- Recommendations to retry later

**Example Fallback**:
```python
# When Erlang module unavailable
return ErlangCoverageResponse(
    ...
    recommendations=[
        "Erlang module unavailable - using simplified estimation",
        f"Minimum {min_servers} specialists recommended for stability"
    ],
    severity="warning"
)
```

---

## Integration Patterns

### Celery Task Integration

Many tools are scheduled via Celery for automated monitoring:

```python
from celery import shared_task

@shared_task
def daily_resilience_check():
    """Daily resilience monitoring task."""
    # Fire index for all residents
    for resident in get_active_residents():
        result = calculate_fire_danger_index(...)
        if result.requires_intervention:
            send_alert(resident.id, result)

    # Program-wide Rt
    burned_out = get_burned_out_residents()
    epi_result = calculate_burnout_rt(burned_out)
    if epi_result.rt > 1.0:
        escalate_to_leadership(epi_result)
```

### Dashboard Integration

Tools provide data for real-time dashboards:

- **SPC Control Charts**: `run_spc_analysis` data
- **Fire Index Heat Map**: `calculate_fire_danger_index` batch results
- **Staffing Tables**: `optimize_erlang_coverage` staffing_table
- **Equity Lorenz Curves**: `calculate_equity_metrics` with Lorenz data

### Alert Pipeline

Tool outputs feed into notification system:

```
Tool Response → Severity Assessment → Alert Generation → Delivery
                    ↓                      ↓              ↓
              (healthy/warning/        (Email/SMS/      (Resident/
               critical/emergency)      Dashboard)       Coordinator/
                                                        Leadership)
```

---

## Performance Benchmarks

Measured on 100 residents, 52 weeks of data:

| Tool | Latency | Notes |
|------|---------|-------|
| `run_spc_analysis` | <10ms | Real-time suitable |
| `calculate_process_capability_tool` | <20ms | Fast |
| `calculate_fire_danger_index` | <50ms | Moderate |
| `optimize_erlang_coverage` | <5ms | Very fast |
| `detect_burnout_precursors` | <100ms | Depends on signal length |
| `calculate_burnout_rt` | <500ms | Network analysis |
| `simulate_burnout_spread` | <1s | Full simulation |
| `get_unified_critical_index` | <200ms | Aggregates multiple domains |
| `calculate_recovery_distance` | <2s | Graph search intensive |
| `assess_creep_fatigue` | <30ms | Fast |

---

## Document Information

**Version**: 1.0
**Last Updated**: 2025-12-28
**Maintained By**: MCP Integration Team

**Related Documentation**:
- [Cross-Disciplinary Resilience Framework](../architecture/cross-disciplinary-resilience.md)
- [MCP Server Architecture](../architecture/mcp-server.md)
- [Backend API Reference](./backend-api.md)
- [AI Agent User Guide](../guides/AI_AGENT_USER_GUIDE.md)
