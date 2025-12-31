# Resilience Framework for Medical Residency Scheduling

## Overview

Comprehensive cross-disciplinary resilience framework implementing concepts from power grid engineering, epidemiology, queuing theory, statistical process control, and advanced physics.

**Purpose**: Prevent burnout cascades, detect system instabilities, and maintain operational resilience in medical residency scheduling.

## Architecture

### Tier 1: Core Concepts (Foundation)

#### Defense in Depth (Cybersecurity/Power Grid)
- **Location**: `engine/defense_level_calculator.py`
- **Concept**: Five-tier safety system (GREEN → YELLOW → ORANGE → RED → BLACK)
- **Application**: Graduated response to system stress
- **Example**: System automatically escalates response as utilization crosses 80% → 90% → 95% thresholds

#### Utilization Monitoring (Queuing Theory)
- **Location**: `engine/utilization_monitor.py`, `queuing/erlang_c.py`
- **Concept**: 80% utilization threshold from M/M/c queue theory
- **Science**: Above 80%, queue length grows exponentially (Erlang C formula)
- **Application**: Prevent queue explosion by maintaining utilization < 80%

#### N-1/N-2 Contingency (Power Grid)
- **Location**: `contingency/n1_analyzer.py`, `contingency/n2_analyzer.py`
- **Concept**: System must survive any single (N-1) or dual (N-2) component failure
- **Standard**: NERC power grid reliability standards
- **Application**: Ensure schedule survives loss of any 1-2 residents

### Tier 2: Strategic Monitoring

#### Statistical Process Control (Manufacturing)
- **Location**: `spc/control_chart.py`, `spc/western_electric.py`
- **Concept**: 3-sigma control limits, Western Electric rules
- **Industry**: Semiconductor/Six Sigma quality control
- **Application**: Detect anomalies in burnout rates, work hours, coverage gaps

#### Burnout Epidemiology (Public Health)
- **Location**: `epidemiology/sir_model.py`, `epidemiology/rt_calculator.py`
- **Concept**: SIR compartmental model, R₀ reproduction number
- **Science**: Kermack-McKendrick epidemic modeling
- **Application**: Model burnout spread through schedule pressure cascades

### Tier 3: Exotic Frontier (Advanced Physics/Mathematics)

#### Metastability Detection (Statistical Mechanics)
- **Location**: `exotic/metastability.py`
- **Concept**: Detect systems trapped in local energy minima
- **Science**: Kramers escape rate theory
- **Application**: Identify when schedule is suboptimal but stable; predict reorganization

#### Spin Glass Model (Condensed Matter Physics)
- **Location**: `exotic/spin_glass.py`
- **Concept**: Frustrated constraint systems, replica symmetry breaking
- **Science**: Edwards-Anderson model, Parisi solution
- **Application**: Generate diverse schedule variants, explore conflicting preferences

#### Catastrophe Theory (Dynamical Systems)
- **Location**: `exotic/catastrophe.py`
- **Concept**: Predict sudden failures from smooth parameter changes
- **Science**: René Thom's catastrophe theory, cusp bifurcations
- **Application**: Identify tipping points in morale, predict sudden resignations

## Module Reference

### Engine (`engine/`)

| Module | Purpose | Key Metric |
|--------|---------|------------|
| `resilience_engine.py` | Main orchestrator | Overall resilience status |
| `defense_level_calculator.py` | Defense level assessment | GREEN/YELLOW/ORANGE/RED/BLACK |
| `utilization_monitor.py` | Utilization tracking | Utilization ratio, queue length |
| `threshold_manager.py` | Dynamic thresholds | SPC control limits |

### Contingency (`contingency/`)

| Module | Purpose | Standard |
|--------|---------|----------|
| `n1_analyzer.py` | Single-point failure detection | NERC N-1 |
| `n2_analyzer.py` | Dual-failure scenarios | NERC N-2 |

### Epidemiology (`epidemiology/`)

| Module | Purpose | Model |
|--------|---------|-------|
| `sir_model.py` | Burnout spread modeling | SIR compartmental |
| `rt_calculator.py` | Reproduction number | Cori method |

### Queuing (`queuing/`)

| Module | Purpose | Formula |
|--------|---------|---------|
| `erlang_c.py` | Queue calculations | Erlang C (M/M/c) |
| `utilization_optimizer.py` | Capacity optimization | Erlang optimization |

### SPC (`spc/`)

| Module | Purpose | Standard |
|--------|---------|----------|
| `control_chart.py` | Control charts | Shewhart, CUSUM, EWMA |
| `western_electric.py` | Rule-based detection | Western Electric 8 rules |

### Exotic (`exotic/`)

| Module | Purpose | Theory |
|--------|---------|--------|
| `metastability.py` | Trapped state detection | Kramers theory |
| `spin_glass.py` | Diverse schedules | Edwards-Anderson |
| `catastrophe.py` | Tipping point prediction | Thom catastrophe theory |

## Usage Examples

### 1. Assess Overall Resilience

```python
from app.resilience import ResilienceEngine
from datetime import date

engine = ResilienceEngine()

status = engine.assess_resilience(
    period_start=date(2024, 1, 1),
    period_end=date(2024, 1, 7),
    total_capacity=1000.0,  # Total available hours
    utilized_capacity=850.0,  # Scheduled hours
    num_servers=10,  # Number of residents
    n1_failures=5,
    n2_failures=2,
    coverage_gaps=1,
    burnout_cases=2,
)

print(f"Defense Level: {status.defense_level.level}")
print(f"Utilization: {status.utilization.utilization_ratio:.1%}")
print(f"Risk Score: {status.risk_score:.2%}")
print(f"Healthy: {status.is_healthy}")

for alert in status.alerts:
    print(f"  - {alert}")
```

### 2. N-1 Contingency Analysis

```python
from app.resilience.contingency import N1Analyzer

analyzer = N1Analyzer()

# Analyze single resident failure
scenario = analyzer.analyze_person_failure(
    person_id="resident_001",
    assigned_slots=[(date(2024, 1, 1), "clinic"), (date(2024, 1, 2), "inpatient")],
    available_backups=["backup_001", "backup_002"],
    backup_capacity={"backup_001": 10, "backup_002": 5},
)

print(f"Criticality: {scenario.criticality_score:.2f}")
print(f"Backup Available: {scenario.backup_available}")
print(f"Mitigation: {scenario.mitigation_strategy}")
```

### 3. Burnout Epidemic Modeling

```python
from app.resilience.epidemiology import SIRModel

model = SIRModel(transmission_rate=0.3, recovery_rate=0.1)

print(f"R0: {model.basic_reproduction_number}")  # R0 = 3.0

forecast = model.simulate(
    initial_susceptible=95,
    initial_infected=5,
    initial_recovered=0,
    days=90,
)

print(f"Peak burnout: {forecast.peak_infected} residents")
print(f"Time to peak: {forecast.time_to_peak} days")
print(f"Total cases: {forecast.total_cases}")
```

### 4. Erlang C Capacity Planning

```python
from app.resilience.queuing import ErlangC

erlang = ErlangC()

result = erlang.calculate(
    arrival_rate=8.0,  # 8 consults/hour
    service_rate=1.0,  # 1 consult/hour/resident
    num_servers=10,  # 10 residents on duty
)

print(f"Utilization: {result.utilization:.1%}")
print(f"Probability of waiting: {result.prob_wait:.1%}")
print(f"Average queue length: {result.avg_queue_length:.1f}")
print(f"Average wait time: {result.avg_wait_time:.2f} hours")
```

### 5. SPC Monitoring

```python
from app.resilience.spc import ControlChart, WesternElectricRules

# Create control chart
chart = ControlChart()

# Calculate limits from baseline
baseline_burnout = [2.0, 3.0, 2.5, 2.0, 3.5, 2.8, 2.2, 3.0, 2.5, 2.7]
limits = chart.calculate_limits(baseline_burnout)

# Monitor new data
point = chart.add_point(5.0)  # Sudden spike

print(f"In control: {point.is_in_control}")
print(f"Zone: {point.zone}")

# Check Western Electric rules
rules = WesternElectricRules(limits.center_line, limits.sigma)
violations = rules.check_all_rules(chart.data_points)

for v in violations:
    print(f"Rule {v.rule_number}: {v.description}")
```

## Key Thresholds

### Utilization (Queuing Theory)
- **< 60%**: Under-utilized (consider capacity reduction)
- **60-80%**: Optimal range (GREEN)
- **80-90%**: Warning zone (YELLOW) - queue growth accelerating
- **90-95%**: Danger zone (ORANGE) - queue unstable
- **> 95%**: Critical (RED/BLACK) - queue explosion imminent

### Defense Levels
- **GREEN**: Normal operations, all metrics healthy
- **YELLOW**: Early warning, proactive measures needed
- **ORANGE**: Degraded operations, activate contingencies
- **RED**: Critical state, emergency protocols
- **BLACK**: System failure, activate mutual aid

### Burnout Epidemiology
- **R₀ < 1**: Burnout declining (interventions working)
- **R₀ = 1**: Endemic equilibrium
- **R₀ > 1**: Epidemic growth (urgent intervention needed)

## Scientific Foundations

### 1. Erlang C Formula (1917)

$$
C(c, a) = \frac{\frac{a^c}{c!} \cdot \frac{c}{c-a}}{\sum_{k=0}^{c-1} \frac{a^k}{k!} + \frac{a^c}{c!} \cdot \frac{c}{c-a}}
$$

Where:
- `a = λ/μ` (offered load)
- `c` = number of servers
- `C` = probability of queuing

### 2. SIR Differential Equations

$$
\frac{dS}{dt} = -\beta \frac{SI}{N}
$$

$$
\frac{dI}{dt} = \beta \frac{SI}{N} - \gamma I
$$

$$
\frac{dR}{dt} = \gamma I
$$

Basic reproduction number: $R_0 = \frac{\beta}{\gamma}$

### 3. Cusp Catastrophe Potential

$$
V(x; a, b) = \frac{x^4}{4} + \frac{ax^2}{2} + bx
$$

Bifurcation set: $a^3 + 27b^2 = 0$

### 4. Western Electric Rules (1956)

1. One point beyond ±3σ
2. Two of three consecutive beyond ±2σ
3. Four of five consecutive beyond ±1σ
4. Eight consecutive same side of center
5. Six consecutive trending
6. Fifteen consecutive within ±1σ
7. Fourteen consecutive alternating
8. Eight consecutive beyond ±1σ (both sides)

## Testing

Comprehensive test suite in `backend/tests/resilience/`:

```bash
# Run all resilience tests
pytest backend/tests/resilience/

# Run specific module tests
pytest backend/tests/resilience/test_defense_levels.py
pytest backend/tests/resilience/test_n1_analysis.py
pytest backend/tests/resilience/test_sir_model.py
pytest backend/tests/resilience/test_erlang_c.py
pytest backend/tests/resilience/test_spc.py
```

## Performance Considerations

- **N-2 Analysis**: Combinatorially expensive (C(n,2) scenarios). Limit to max_combinations.
- **SIR Simulation**: ODE solving is O(days × iterations). Cache results.
- **Spin Glass**: Simulated annealing is O(iterations × num_spins). Use parallel replicas.
- **SPC**: Real-time monitoring is O(1) per point. Batch processing recommended.

## Integration Points

### Celery Tasks
- Schedule periodic resilience health checks (every 15 min)
- Run N-1/N-2 analysis nightly
- Update SPC control charts daily
- Calculate Rt weekly

### API Endpoints
```python
# Suggested endpoints (implementation in app/api/routes/)
GET  /api/resilience/status          # Current resilience status
GET  /api/resilience/defense-level   # Current defense level
GET  /api/resilience/n1-analysis     # N-1 failure scenarios
GET  /api/resilience/burnout-forecast # SIR forecast
POST /api/resilience/simulate        # Simulate interventions
```

### Dashboard Widgets
- Defense level indicator (traffic light)
- Utilization gauge with 80% threshold
- Burnout Rt trend chart
- SPC control chart with violations
- N-1 SPOF count
- Top 5 critical scenarios

## References

### Power Grid
- NERC Reliability Standards (N-1/N-2 contingency)
- IEEE Power & Energy Society (utilization thresholds)

### Epidemiology
- Kermack & McKendrick (1927) - SIR model foundations
- Cori et al. (2013) - EpiEstim R_t estimation

### Queuing Theory
- Erlang, A.K. (1917) - Erlang C formula
- Kleinrock (1975) - Queueing Systems Vol. 1

### SPC
- Shewhart (1931) - Control chart theory
- Western Electric (1956) - Eight rules
- Montgomery (2012) - Statistical Quality Control

### Exotic Concepts
- Kramers (1940) - Escape rate theory
- Edwards & Anderson (1975) - Spin glass model
- Thom (1972) - Catastrophe theory
- Parisi (1979) - Replica symmetry breaking

## License

Internal use only. Part of Residency Scheduler application.

## Maintenance

- **Author**: Claude (AI Assistant) + Human supervision
- **Created**: 2024-12-31 (Session 26 burn)
- **Last Updated**: 2024-12-31
- **Status**: Production-ready
- **Dependencies**: numpy, scipy, networkx (see requirements.txt)
