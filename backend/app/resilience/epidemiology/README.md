***REMOVED*** Burnout Epidemiology Module

> **Location**: `backend/app/resilience/epidemiology/`
> **Purpose**: Apply infectious disease epidemiology models to burnout spread prediction
> **Scientific Basis**: Kermack-McKendrick SIR model, Cori method for Rt estimation

---

***REMOVED******REMOVED*** Overview

This module applies epidemiological modeling techniques to understand and predict burnout spread through medical residency programs. Burnout is modeled as a "contagious" condition that spreads through social and work networks via:

- **Schedule pressure cascades**: Covering for burned-out colleagues increases load on others
- **Social contagion**: Negativity and emotional exhaustion spread through teams (Christakis & Fowler, 2008)
- **Workload redistribution**: Each absence creates additional burden on remaining staff

By treating burnout as an epidemic, we can apply proven public health tools (R0, contact tracing, herd immunity) to organizational health.

---

***REMOVED******REMOVED*** Module Components

***REMOVED******REMOVED******REMOVED*** 1. SIR Model (`sir_model.py`)

Implements the classic **Susceptible-Infected-Recovered (SIR)** compartmental model.

***REMOVED******REMOVED******REMOVED******REMOVED*** State Definitions

| State | Symbol | Description | Burnout Analogy |
|-------|--------|-------------|-----------------|
| **Susceptible** | S | Healthy, at risk of infection | Healthy residents who could burn out |
| **Infected** | I | Currently infectious | Actively burned out (can spread stress) |
| **Recovered** | R | Recovered or removed | Recovered from burnout or left system |

***REMOVED******REMOVED******REMOVED******REMOVED*** Core Equations

The SIR model is governed by these ordinary differential equations:

```
dS/dt = -beta * S * I / N    (Susceptibles become infected)
dI/dt = beta * S * I / N - gamma * I    (Infections minus recoveries)
dR/dt = gamma * I    (Infected recover)
```

Where:
- **beta**: Transmission rate - probability of burnout transmission per contact
- **gamma**: Recovery rate - 1/gamma = average duration of burnout
- **N**: Total population (S + I + R, conserved over time)

***REMOVED******REMOVED******REMOVED******REMOVED*** Basic Reproduction Number (R0)

```
R0 = beta / gamma
```

| R0 Value | Interpretation | Action |
|----------|----------------|--------|
| R0 < 1 | Burnout declining | Current measures working |
| R0 = 1 | Endemic equilibrium | Stable but watch closely |
| R0 > 1 | Epidemic growth | Intervention needed |

***REMOVED******REMOVED******REMOVED******REMOVED*** Herd Immunity Threshold

```
HIT = 1 - 1/R0
```

The fraction of population that must be "immune" (recovered or protected) to stop spread.

| R0 | HIT | Interpretation |
|----|-----|----------------|
| 2 | 50% | Half must be immune |
| 3 | 67% | Two-thirds must be immune |
| 4 | 75% | Three-quarters must be immune |

***REMOVED******REMOVED******REMOVED******REMOVED*** Usage Example

```python
from app.resilience.epidemiology import SIRModel

***REMOVED*** Initialize model with transmission and recovery rates
model = SIRModel(
    transmission_rate=0.3,  ***REMOVED*** beta = 30% transmission per contact
    recovery_rate=0.1       ***REMOVED*** gamma = 10% recovery rate (10-day avg duration)
)

print(f"R0 = {model.basic_reproduction_number}")  ***REMOVED*** R0 = 3.0

***REMOVED*** Simulate epidemic trajectory
forecast = model.simulate(
    initial_susceptible=95,
    initial_infected=5,
    initial_recovered=0,
    days=90
)

print(f"Peak burnout: {forecast.peak_infected} residents on day {forecast.peak_day}")
print(f"Total cases: {forecast.total_cases}")
print(f"Herd immunity threshold: {model.calculate_herd_immunity_threshold():.1%}")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Intervention Effect Analysis

```python
***REMOVED*** Compare baseline vs. intervention scenarios
impact = model.calculate_intervention_effect(
    current_beta=0.4,           ***REMOVED*** Current transmission rate
    intervention_beta=0.2,      ***REMOVED*** Reduced rate after intervention
    current_infected=10,
    total_population=100,
    days=60
)

print(f"Cases prevented: {impact['cases_prevented']} ({impact['cases_prevented_pct']:.1f}%)")
print(f"Peak reduction: {impact['peak_reduction']} residents")
print(f"Peak delay: {impact['peak_delay_days']} days")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Phase Classification

```python
phase = model.classify_epidemic_phase(infected_count=10, total_population=100)
***REMOVED*** Returns: "epidemic" (10% prevalence)

***REMOVED*** Phase thresholds:
***REMOVED*** - "no_cases": 0 infected
***REMOVED*** - "sporadic": < 1% prevalence
***REMOVED*** - "outbreak": 1-5% prevalence
***REMOVED*** - "epidemic": 5-15% prevalence
***REMOVED*** - "crisis": > 15% prevalence
```

---

***REMOVED******REMOVED******REMOVED*** 2. Rt Calculator (`rt_calculator.py`)

Estimates the **effective reproduction number (Rt)** in real-time using the Cori method (EpiEstim).

Unlike R0 (basic reproduction number), Rt accounts for:
- Current immunity levels (recovered individuals)
- Interventions already in place
- Changing transmission dynamics over time

***REMOVED******REMOVED******REMOVED******REMOVED*** Rt Interpretation

| Rt Value | Status | Interpretation |
|----------|--------|----------------|
| Rt < 0.9 | Declining | Burnout outbreak shrinking |
| 0.9-1.1 | Stable | Endemic equilibrium |
| Rt > 1.1 | Growing | Burnout spreading actively |

***REMOVED******REMOVED******REMOVED******REMOVED*** Serial Interval

The **serial interval** is the time between successive cases in a transmission chain. For burnout:
- **Default mean**: 7 days (time for stress to propagate)
- **Default std**: 3 days (variation in transmission timing)

***REMOVED******REMOVED******REMOVED******REMOVED*** Cori Method Implementation

The Cori method estimates Rt using:

1. **Infectiousness calculation**: Weight past cases by serial interval distribution
2. **Bayesian posterior**: Use Gamma distribution for uncertainty quantification
3. **Sliding window**: Smooth estimates over configurable window (default 7 days)

```
Rt(t) = I(t) / Lambda(t)

Where:
- I(t) = New cases at time t
- Lambda(t) = sum of w_s * I(t-s)  (infectiousness from past cases)
- w_s = Serial interval distribution weights
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Usage Example

```python
from app.resilience.epidemiology import RtCalculator

calculator = RtCalculator(
    serial_interval_mean=7.0,  ***REMOVED*** 7-day average serial interval
    serial_interval_std=3.0
)

***REMOVED*** Daily new burnout cases over past 30 days
incidence = [1, 0, 2, 1, 3, 2, 4, 3, 5, 4,
             6, 5, 7, 6, 5, 4, 3, 3, 2, 2,
             1, 1, 1, 0, 1, 0, 1, 0, 0, 1]

***REMOVED*** Calculate Rt for each day (after initial window)
estimates = calculator.calculate_rt(incidence, window_size=7)

for est in estimates[-5:]:  ***REMOVED*** Last 5 days
    print(f"{est.date}: Rt={est.rt_mean:.2f} "
          f"[{est.rt_lower:.2f}-{est.rt_upper:.2f}] "
          f"({est.interpretation})")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Calculate Rt from R0

When SIR state is known, derive Rt directly:

```python
***REMOVED*** Rt = R0 * (susceptible fraction)
rt = calculator.calculate_rt_from_r0(
    r0=3.0,                    ***REMOVED*** Basic reproduction number
    susceptible=70,            ***REMOVED*** Current susceptible count
    total_population=100       ***REMOVED*** Total population
)
***REMOVED*** rt = 3.0 * (70/100) = 2.1
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Outbreak Control Assessment

```python
assessment = calculator.assess_outbreak_control(
    current_rt=0.85,
    rt_history=[1.2, 1.1, 0.95, 0.9, 0.88, 0.85, 0.83],
    days_below_one=7  ***REMOVED*** Require 7 consecutive days Rt < 1
)

print(f"Controlled: {assessment['is_controlled']}")
print(f"Trend: {assessment['trend_direction']}")
print(f"Assessment: {assessment['assessment']}")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Intervention Forecast

```python
***REMOVED*** Forecast Rt trend with intervention
future_rt = calculator.forecast_rt_trend(
    current_rt=1.5,
    intervention_effect=0.7,  ***REMOVED*** 30% reduction in transmission
    days_ahead=14
)

***REMOVED*** Shows gradual decline as intervention takes effect
```

---

***REMOVED******REMOVED*** Network-Based Epidemiology

The `burnout_epidemiology.py` module (in parent directory) extends these models with **network analysis** using NetworkX:

***REMOVED******REMOVED******REMOVED*** BurnoutEpidemiology Class

Combines SIR dynamics with social network structure:

```python
from app.resilience.burnout_epidemiology import BurnoutEpidemiology
import networkx as nx
from uuid import uuid4

***REMOVED*** Create social network (nodes=residents, edges=connections)
G = nx.Graph()
residents = [uuid4() for _ in range(20)]
G.add_nodes_from(residents)

***REMOVED*** Add connections (shared shifts, mentorship, teams)
G.add_edge(residents[0], residents[1])  ***REMOVED*** Mentor-mentee
G.add_edge(residents[1], residents[2])  ***REMOVED*** Teammates
***REMOVED*** ... more edges

analyzer = BurnoutEpidemiology(G)
```

***REMOVED******REMOVED******REMOVED*** Key Features

| Feature | Method | Description |
|---------|--------|-------------|
| **State Tracking** | `record_burnout_state()` | Track burnout progression over time |
| **Contact Tracing** | `get_close_contacts()` | Find high-risk contacts of burned-out individuals |
| **Rt Calculation** | `calculate_reproduction_number()` | Network-aware Rt with secondary case counting |
| **SIR Simulation** | `simulate_sir_spread()` | Discrete-time network epidemic simulation |
| **Super-Spreaders** | `identify_super_spreaders()` | Find high-connectivity nodes |
| **Interventions** | `get_interventions()` | Evidence-based recommendations by Rt level |

***REMOVED******REMOVED******REMOVED*** Intervention Levels

Based on Rt value, the module recommends graduated interventions:

| Rt Range | Level | Example Actions |
|----------|-------|-----------------|
| < 0.5 | None | Continue preventive measures |
| 0.5-1.0 | Monitoring | Increase monitoring, voluntary support groups |
| 1.0-2.0 | Moderate | Workload reduction, mandatory check-ins |
| 2.0-3.0 | Aggressive | Mandatory time off, emergency staffing |
| >= 3.0 | Emergency | Crisis management, operational pause |

---

***REMOVED******REMOVED*** Integration with Other Modules

***REMOVED******REMOVED******REMOVED*** Seismic-SIR Bridge

The epidemiology module integrates with seismic precursor detection:

```
Seismic Detection (STA/LTA) --> beta Adjustment --> SIR Forecast
```

When stress precursors are detected (swap requests, sick calls), the transmission rate beta is dynamically adjusted:

```python
***REMOVED*** Formula: beta_adjusted = beta_base * (1 + alpha * sum(w_i * f(r_i)))
***REMOVED*** Where:
***REMOVED*** - alpha = sensitivity parameter
***REMOVED*** - w_i = network degree weight (super-spreaders matter more)
***REMOVED*** - f(r_i) = STA/LTA ratio transformation
```

***REMOVED******REMOVED******REMOVED*** Resilience Engine

Epidemiology metrics feed into the overall resilience assessment:

- **Burnout Rt** -> Risk score component
- **Epidemic phase** -> Defense level adjustment
- **Super-spreaders** -> Targeted intervention priority

---

***REMOVED******REMOVED*** Data Classes

***REMOVED******REMOVED******REMOVED*** SIRSnapshot

Point-in-time SIR model state:

```python
@dataclass
class SIRSnapshot:
    timestamp: datetime
    susceptible: int
    infected: int
    recovered: int
    total_population: int
    beta: float      ***REMOVED*** Transmission rate
    gamma: float     ***REMOVED*** Recovery rate
    r0: float        ***REMOVED*** Basic reproduction number
```

***REMOVED******REMOVED******REMOVED*** SIRForecast

Epidemic trajectory forecast:

```python
@dataclass
class SIRForecast:
    days_ahead: int
    forecasted_infected: list[int]
    forecasted_susceptible: list[int]
    forecasted_recovered: list[int]
    peak_infected: int      ***REMOVED*** Maximum infected count
    peak_day: int           ***REMOVED*** Day of peak
    time_to_peak: int       ***REMOVED*** Days until peak
    total_cases: int        ***REMOVED*** Cumulative infections
```

***REMOVED******REMOVED******REMOVED*** RtEstimate

Reproduction number estimate with uncertainty:

```python
@dataclass
class RtEstimate:
    date: date
    rt_mean: float      ***REMOVED*** Mean Rt estimate
    rt_lower: float     ***REMOVED*** Lower 95% CI
    rt_upper: float     ***REMOVED*** Upper 95% CI
    confidence: float   ***REMOVED*** Confidence (0-1)
    interpretation: str ***REMOVED*** "growing", "stable", "declining"
```

---

***REMOVED******REMOVED*** Mathematical Foundations

***REMOVED******REMOVED******REMOVED*** SIR Model Derivation

The SIR model assumes:
1. **Homogeneous mixing**: Any susceptible can contact any infected
2. **Closed population**: N = S + I + R is constant
3. **Permanent immunity**: Recovered individuals don't become susceptible again

The force of infection is proportional to the infected fraction:

```
Force of infection lambda = beta * I / N
```

***REMOVED******REMOVED******REMOVED*** Cori Method (EpiEstim)

The Cori method uses Bayesian inference with:

1. **Prior**: Uninformative Gamma distribution
2. **Likelihood**: Poisson process for new infections
3. **Posterior**: Gamma distribution for Rt

```
Rt posterior ~ Gamma(shape=I(t)+1, scale=1/Lambda(t))

95% CI = [Gamma.ppf(0.025), Gamma.ppf(0.975)]
```

***REMOVED******REMOVED******REMOVED*** Serial Interval Distribution

Modeled as Gamma distribution:

```python
shape = mean**2 / variance
scale = variance / mean

***REMOVED*** Default: mean=7, std=3
***REMOVED*** shape = 49/9 = 5.44
***REMOVED*** scale = 9/7 = 1.29
```

---

***REMOVED******REMOVED*** Testing

***REMOVED******REMOVED******REMOVED*** Unit Tests

```bash
***REMOVED*** Run SIR model tests
pytest backend/tests/resilience/test_sir_model.py -v

***REMOVED*** Run network epidemiology tests
pytest backend/tests/resilience/test_burnout_epidemiology.py -v
```

***REMOVED******REMOVED******REMOVED*** Integration Tests

```bash
***REMOVED*** Test seismic-SIR bridge
pytest backend/tests/integration/bridges/test_seismic_sir_bridge.py -v
```

***REMOVED******REMOVED******REMOVED*** Test Coverage

The test suite covers:
- R0 calculation and interpretation
- Epidemic simulation (growth, die-out, conservation)
- Herd immunity threshold calculation
- Intervention effect analysis
- Phase classification
- Rt estimation with Cori method
- Network-based contact tracing
- Super-spreader identification
- Intervention escalation

---

***REMOVED******REMOVED*** Configuration

***REMOVED******REMOVED******REMOVED*** Default Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `transmission_rate` (beta) | 0.3 | Probability of transmission per contact |
| `recovery_rate` (gamma) | 0.1 | Recovery rate (1/10 = 10-day duration) |
| `serial_interval_mean` | 7.0 days | Time between successive cases |
| `serial_interval_std` | 3.0 days | Variation in serial interval |
| `window_size` (Rt) | 7 days | Sliding window for Rt estimation |

***REMOVED******REMOVED******REMOVED*** Thresholds

```python
***REMOVED*** Rt interpretation thresholds
RT_DECLINING_THRESHOLD = 0.9
RT_GROWING_THRESHOLD = 1.1

***REMOVED*** Minimum cases for confident Rt estimate
MIN_CASES_FOR_CONFIDENCE = 10.0
```

---

***REMOVED******REMOVED*** References

***REMOVED******REMOVED******REMOVED*** Epidemiology

1. **Kermack, W.O. & McKendrick, A.G.** (1927). "A contribution to the mathematical theory of epidemics." *Proceedings of the Royal Society A*.

2. **Cori, A. et al.** (2013). "A new framework and software to estimate time-varying reproduction numbers during epidemics." *American Journal of Epidemiology*.

***REMOVED******REMOVED******REMOVED*** Social Contagion

3. **Christakis, N.A. & Fowler, J.H.** (2008). "Dynamic spread of happiness in a large social network." *BMJ*.

4. **Bakker, A.B. et al.** (2009). "Burnout contagion among intensive care nurses." *Journal of Advanced Nursing*.

***REMOVED******REMOVED******REMOVED*** Implementation

5. **EpiEstim R Package**: Real-time Rt estimation methodology
6. **SciPy ODE Solvers**: `scipy.integrate.odeint` for SIR differential equations
7. **NetworkX**: Graph analysis for social network epidemiology

---

***REMOVED******REMOVED*** See Also

- [Resilience Framework README](../README.md) - Overall resilience architecture
- [Cross-Disciplinary Resilience](../../../../docs/architecture/cross-disciplinary-resilience.md) - Full concept documentation
