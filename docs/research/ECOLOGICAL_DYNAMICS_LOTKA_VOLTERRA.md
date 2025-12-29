# Ecological Dynamics: Lotka-Volterra Predator-Prey Modeling for Schedule Supply/Demand

**Created:** 2025-12-29
**MCP Tools:** 4 tools (`analyze_supply_demand_cycles_tool`, `predict_capacity_crunch_tool`, `find_equilibrium_point_tool`, `simulate_intervention_tool`)
**Location:** `/mcp-server/src/scheduler_mcp/tools/ecological_dynamics_tools.py`

---

## Overview

This module applies **Lotka-Volterra predator-prey dynamics** from ecology to model oscillations between resource supply (available residents) and demand (workload). It predicts boom/bust cycles in coverage and complements homeostasis feedback loops.

### Key Concepts

| Concept | Scheduling Interpretation |
|---------|--------------------------|
| **Prey (x)** | Available capacity/slack (idle resident-hours, unfilled slots) |
| **Predator (y)** | Workload demand (procedures, clinic visits, patient census) |
| **α (alpha)** | Capacity growth rate (hiring, training, rotation expansion) |
| **β (beta)** | Consumption rate (how demand consumes capacity) |
| **δ (delta)** | Demand amplification (demand breeding from available capacity) |
| **γ (gamma)** | Demand decay rate (procedures completed, patients discharged) |

---

## Mathematical Foundation

### Lotka-Volterra Equations

```
dx/dt = αx - βxy    (capacity grows naturally, consumed by demand)
dy/dt = δxy - γy    (demand grows when capacity exists, decays naturally)
```

### Equilibrium Point

The system has a stable equilibrium at:

```
x* = γ/δ  (equilibrium capacity)
y* = α/β  (equilibrium demand)
```

At equilibrium, growth balances decay, but the equilibrium is neutrally stable (center point), meaning disturbances cause persistent oscillations.

### Oscillation Period

For systems near equilibrium, the period of oscillation is approximately:

```
T ≈ 2π/√(αγ)
```

This predicts how long boom/bust cycles take in days.

---

## MCP Tools

### 1. `analyze_supply_demand_cycles_tool`

**Purpose:** Fit Lotka-Volterra model to historical data and identify oscillation patterns.

**Input:**
```python
{
  "historical_data": [
    {"date": "2025-01-01", "capacity": 50.0, "demand": 40.0},
    {"date": "2025-01-08", "capacity": 45.0, "demand": 45.0},
    # ... minimum 10 data points
  ],
  "prediction_days": 90
}
```

**Output:**
```python
{
  "fitted_parameters": {"alpha": 0.12, "beta": 0.015, "delta": 0.008, "gamma": 0.10},
  "r_squared": 0.87,  # Goodness of fit
  "equilibrium_capacity": 12.5,
  "equilibrium_demand": 8.0,
  "oscillation_period_days": 57.3,
  "system_stability": "marginally_stable",
  "predicted_trajectory": [...],
  "ecological_interpretation": "System exhibits persistent oscillations..."
}
```

**Use Cases:**
- Identify natural boom/bust cycles in coverage
- Fit parameters from historical workload data
- Predict future oscillation patterns
- Assess system stability

---

### 2. `predict_capacity_crunch_tool`

**Purpose:** Forecast when demand will exceed supply (capacity crunch).

**Input:**
```python
{
  "current_capacity": 45.0,
  "current_demand": 48.0,
  "alpha": 0.12,  # From fitted model
  "beta": 0.015,
  "delta": 0.008,
  "gamma": 0.10,
  "crunch_threshold": 10.0,  # Minimum acceptable capacity
  "prediction_days": 180
}
```

**Output:**
```python
{
  "risk_level": "HIGH",  # IMMINENT, CRITICAL, HIGH, ELEVATED, MODERATE, LOW
  "days_until_crunch": 42,
  "crunch_date": "2025-03-15",
  "minimum_capacity": 8.3,
  "minimum_capacity_date": "2025-03-15",
  "will_recover": true,
  "recovery_date": "2025-05-10",
  "mitigation_urgency": "High priority. Begin mitigation planning this week."
}
```

**Risk Levels:**
| Level | Days Until Crunch | Action Required |
|-------|-------------------|-----------------|
| **IMMINENT** | <7 days | Activate contingency NOW |
| **CRITICAL** | <14 days | Urgent intervention required |
| **HIGH** | <30 days | Begin mitigation this week |
| **ELEVATED** | <60 days | Prepare intervention strategies |
| **MODERATE** | <90 days | Monitor and plan proactively |
| **LOW** | >90 days | Routine monitoring |

**Use Cases:**
- Early warning of coverage crises
- Trigger contingency plans
- Timeline for intervention deployment
- Risk-based resource allocation

---

### 3. `find_equilibrium_point_tool`

**Purpose:** Calculate stable equilibrium and understand parameter sensitivity.

**Input:**
```python
{
  "alpha": 0.12,
  "beta": 0.015,
  "delta": 0.008,
  "gamma": 0.10
}
```

**Output:**
```python
{
  "equilibrium_capacity": 12.5,  # x* = γ/δ
  "equilibrium_demand": 8.0,     # y* = α/β
  "oscillation_period_days": 57.3,
  "is_stable": true,
  "ecological_interpretation": "Equilibrium capacity: 12.5...",
  "parameter_sensitivity": {
    "alpha": "Increasing α (capacity growth) raises equilibrium demand (y*=α/β)",
    "beta": "Increasing β (consumption) lowers equilibrium demand (y*=α/β)",
    "delta": "Increasing δ (demand amplification) lowers equilibrium capacity (x*=γ/δ)",
    "gamma": "Increasing γ (demand decay) raises equilibrium capacity (x*=γ/δ)"
  }
}
```

**Use Cases:**
- Target capacity planning (x*)
- Target workload planning (y*)
- Understand parameter trade-offs
- Design staffing policies

---

### 4. `simulate_intervention_tool`

**Purpose:** Model effects of interventions (add capacity, reduce demand, etc.).

**Input:**
```python
{
  "current_capacity": 40.0,
  "current_demand": 48.0,
  "alpha": 0.12,
  "beta": 0.015,
  "delta": 0.008,
  "gamma": 0.10,
  "intervention_type": "add_capacity",  # See table below
  "intervention_magnitude": 0.25,  # 25% increase
  "intervention_start_day": 0,
  "intervention_duration_days": 90,
  "simulation_days": 180
}
```

**Intervention Types:**

| Type | Effect | Parameter Changes |
|------|--------|-------------------|
| `add_capacity` | Hire residents, expand rotations | α ↑ (growth rate) |
| `reduce_demand` | Cancel elective procedures | γ ↑ (decay rate) |
| `increase_efficiency` | Streamline workflows | β ↓ (consumption rate) |
| `moonlighting` | Temporary capacity injection | One-time capacity boost |
| `locums` | External capacity | One-time capacity boost |
| `schedule_compression` | Increase utilization | β ↑, γ ↑ (faster processing) |
| `demand_smoothing` | Spread workload over time | δ ↓, γ ↑ (dampen oscillations) |

**Output:**
```python
{
  "baseline_min_capacity": 35.2,
  "intervention_min_capacity": 42.8,
  "capacity_improvement": 7.6,
  "baseline_oscillation_amplitude": 18.4,
  "intervention_oscillation_amplitude": 12.1,
  "amplitude_reduction": 6.3,
  "intervention_effectiveness": 0.73,  # 73% effective
  "recommendation": "HIGHLY EFFECTIVE: add_capacity shows strong positive impact..."
}
```

**Effectiveness Scoring:**
| Score | Interpretation | Recommendation |
|-------|----------------|----------------|
| >0.7 | Highly effective | Strongly recommended |
| 0.4-0.7 | Moderately effective | Recommended |
| 0.1-0.4 | Limited effectiveness | Consider alternatives |
| <0.1 | Ineffective | Not recommended |

**Use Cases:**
- Test "what-if" scenarios
- Compare intervention strategies
- Optimize resource allocation
- Justify staffing requests

---

## Ecological Interpretation

### Predator-Prey Analogy

| Ecological System | Scheduling System |
|-------------------|-------------------|
| **Prey population grows** | Capacity expands (hiring, training) |
| **Predators consume prey** | Workload consumes capacity (procedures, clinics) |
| **Overhunting depletes prey** | Overwork burns out residents (capacity crash) |
| **Prey scarcity starves predators** | Low capacity limits workload (demand declines) |
| **Predators die, prey rebounds** | Burnout forces demand reduction, capacity recovers |
| **Cycle repeats** | Boom/bust pattern in coverage |

### System Dynamics

```
PHASE 1: Abundance (High Capacity, Low Demand)
├─ Residents well-rested, low workload
├─ Demand begins to grow (procedures scheduled)
└─ Capacity slowly consumed

PHASE 2: Equilibrium Approach
├─ Capacity ≈ Demand
├─ System near equilibrium point (x*, y*)
└─ Small perturbations cause oscillations

PHASE 3: Overload (Low Capacity, High Demand)
├─ Workload exceeds capacity
├─ Residents overworked, burnout risk
└─ Unsustainable state triggers corrections

PHASE 4: Recovery (Demand Declines)
├─ Procedures deferred, workload drops
├─ Capacity recovers (rest, hiring)
└─ Cycle returns to PHASE 1
```

---

## Integration with Other Resilience Tools

### Complementary Frameworks

| Tool | Focus | Relationship to LV |
|------|-------|-------------------|
| **Homeostasis (PID Control)** | Active stabilization | LV models natural dynamics; PID actively counteracts |
| **N-1/N-2 Contingency** | Shock vulnerability | LV predicts recovery trajectory after shocks |
| **Burnout Rt (SIR Model)** | Contagion spread | LV models resource depletion; SIR models burnout transmission |
| **Erlang C (Queuing)** | Optimal staffing | LV identifies oscillation period; Erlang optimizes within cycle |
| **Defense in Depth** | Layered protection | LV forecasts when defense levels will be breached |

### Workflow Integration

```
1. Historical Analysis
   ├─ Use analyze_supply_demand_cycles_tool
   ├─ Fit parameters (α, β, δ, γ)
   └─ Identify oscillation period

2. Risk Assessment
   ├─ Use predict_capacity_crunch_tool
   ├─ Classify risk level
   └─ Set intervention timeline

3. Strategic Planning
   ├─ Use find_equilibrium_point_tool
   ├─ Determine target capacity (x*)
   └─ Design staffing policies

4. Intervention Testing
   ├─ Use simulate_intervention_tool
   ├─ Compare strategies (add capacity vs reduce demand)
   ├─ Select most effective intervention
   └─ Deploy and monitor

5. Continuous Monitoring
   ├─ Re-fit model monthly with new data
   ├─ Update predictions
   └─ Adjust interventions as needed
```

---

## Implementation Details

### Parameter Fitting Algorithm

Uses **scipy.optimize.least_squares** with:
- **Bounds:** All parameters >0 (physical constraint)
- **Cost function:** Combined residuals for capacity and demand
- **Goodness of fit:** R² for model validation

```python
def fit_lotka_volterra_parameters(
    time_series: list[float],
    capacity_series: list[float],
    demand_series: list[float],
    initial_guess: tuple[float, float, float, float] | None = None,
) -> tuple[float, float, float, float, float]:
    # ... (see implementation in ecological_dynamics_tools.py)
```

### ODE Integration

Uses **scipy.integrate.odeint** for trajectory simulation:

```python
def lotka_volterra(y, t, alpha, beta, delta, gamma):
    x, y_val = y
    dxdt = alpha * x - beta * x * y_val
    dydt = delta * x * y_val - gamma * y_val
    return [dxdt, dydt]

solution = odeint(lotka_volterra, y0, t, args=(alpha, beta, delta, gamma))
```

### Stability Classification

| Criterion | Classification |
|-----------|---------------|
| Recent variance < Early variance × 0.5 | **Stable** (damped oscillations) |
| Max(recent) > Max(early) × 2 | **Unstable** (diverging) |
| CV > 1.5 | **Chaotic** (irregular) |
| Otherwise | **Marginally Stable** (persistent oscillations) |

---

## Example Scenarios

### Scenario 1: Flu Season Surge

**Context:** Winter flu season increases clinic demand.

**Data:**
```python
# Historical data shows demand spikes in winter
data = [
  {"date": "2024-12-01", "capacity": 50, "demand": 35},
  {"date": "2024-12-15", "capacity": 48, "demand": 42},
  {"date": "2025-01-01", "capacity": 42, "demand": 55},  # Peak flu
  {"date": "2025-01-15", "capacity": 38, "demand": 60},  # Overloaded
  {"date": "2025-02-01", "capacity": 45, "demand": 48},  # Recovery
  # ...
]
```

**Analysis:**
1. Fit LV model → α=0.08, β=0.02, δ=0.015, γ=0.12
2. Predict crunch → CRITICAL (12 days until crunch)
3. Simulate interventions:
   - **Moonlighting:** Effectiveness 0.65 (moderate)
   - **Demand smoothing:** Effectiveness 0.82 (highly effective)
4. **Decision:** Implement demand smoothing (defer non-urgent visits)

### Scenario 2: Deployment Impact

**Context:** 3 residents deployed for 6 months.

**Data:**
```python
# Sudden capacity drop
before_deployment = {"capacity": 55, "demand": 48}
after_deployment = {"capacity": 35, "demand": 48}  # -20 capacity
```

**Analysis:**
1. Predict crunch → IMMINENT (4 days)
2. Simulate interventions:
   - **Add capacity (locums):** Effectiveness 0.91
   - **Reduce demand:** Effectiveness 0.73
3. **Decision:** Hire locums + defer elective procedures

### Scenario 3: Long-Term Staffing Policy

**Context:** Design sustainable staffing levels.

**Goal:** Prevent oscillations, maintain equilibrium.

**Analysis:**
1. Historical fit → α=0.10, β=0.018, δ=0.012, γ=0.11
2. Find equilibrium → x*=9.2, y*=5.6
3. **Policy:** Maintain minimum 9.2 idle capacity hours/week
4. **Staffing:** Hire to ensure x* even during absences

---

## Testing

See `/mcp-server/test_ecological_dynamics.py` for comprehensive test suite.

**Run tests:**
```bash
cd /mcp-server
python test_ecological_dynamics.py
```

**Expected output:**
```
╔══════════════════════════════════════════════════════════════════════╗
║      Lotka-Volterra Ecological Dynamics Tools - Test Suite          ║
╚══════════════════════════════════════════════════════════════════════╝

TEST 1: Analyze Supply/Demand Cycles
...
R² goodness of fit: 0.8723
System stability: marginally_stable

TEST 2: Predict Capacity Crunch
...
Risk level: HIGH
Days until crunch: 42

TEST 3: Find Equilibrium Point
...
Equilibrium capacity (x*): 12.50
Oscillation period: 57.3 days

TEST 4: Simulate Intervention
...
Effectiveness score: 73.42%
HIGHLY EFFECTIVE: add_capacity shows strong positive impact.

✓ All tests completed successfully!
```

---

## References

### Academic Literature

1. **Lotka, A. J. (1925)** - "Elements of Physical Biology"
   Original predator-prey model formulation

2. **Volterra, V. (1926)** - "Fluctuations in the Abundance of a Species"
   Independent derivation of the same equations

3. **Murray, J. D. (2002)** - "Mathematical Biology"
   Chapter 3: Models for Interacting Populations

### Application to Workforce Dynamics

4. **Sterman, J. D. (2000)** - "Business Dynamics: Systems Thinking and Modeling"
   System dynamics in organizational contexts

5. **Forrester, J. W. (1961)** - "Industrial Dynamics"
   Oscillations in production-inventory systems

### Resilience Engineering

6. **Hollnagel, E. (2011)** - "RAG - Resilience Analysis Grid"
   Capacity vs demand analysis in safety-critical systems

---

## Future Enhancements

### Planned Features

1. **Multi-Species Extensions**
   - Multiple specialties (peds, IM, surg) as separate species
   - Competitive dynamics (shared resources)

2. **Stochastic Models**
   - Add noise terms to account for random shocks
   - Monte Carlo simulation for uncertainty quantification

3. **Spatial Models**
   - Diffusion terms for inter-site capacity sharing
   - Network topology effects

4. **Parameter Adaptation**
   - Online learning of parameters
   - Adaptive forecasting as new data arrives

5. **Control Theory Integration**
   - Optimal control for intervention timing
   - PID + LV hybrid (active + passive dynamics)

---

## Limitations and Caveats

### Model Assumptions

1. **Continuous Population:** LV assumes continuous values, but residents are discrete
   - **Mitigation:** Valid for large programs (>10 residents)

2. **No Spatial Structure:** Assumes well-mixed population
   - **Mitigation:** Use for single-site programs; extend for multi-site

3. **No Time Delays:** Instantaneous response
   - **Mitigation:** Training delays not modeled; consider lag effects separately

4. **No Stochasticity:** Deterministic equations
   - **Mitigation:** Use for expected behavior; add Monte Carlo for uncertainty

5. **No Seasonal Forcing:** Assumes constant parameters
   - **Mitigation:** Re-fit seasonally or add time-varying parameters

### When to Use vs Avoid

**Use LV When:**
- ✅ Analyzing boom/bust cycles in historical data
- ✅ Predicting medium-term capacity trends (weeks to months)
- ✅ Comparing intervention strategies
- ✅ Understanding equilibrium targets

**Avoid LV When:**
- ❌ Immediate crisis (use N-1/N-2 contingency instead)
- ❌ Discrete events (use discrete event simulation)
- ❌ Highly stochastic systems (use Monte Carlo)
- ❌ Short-term forecasting (<1 week, use time series methods)

---

## Conclusion

Lotka-Volterra predator-prey modeling provides a **complementary lens** to traditional scheduling approaches. While homeostasis (PID control) actively stabilizes the system, LV models the **natural dynamics** when controls are absent or delayed. Together, they form a comprehensive resilience framework:

- **LV:** Describes natural oscillations and equilibrium
- **PID:** Actively counteracts deviations from equilibrium
- **N-1/N-2:** Tests resilience to sudden shocks
- **SIR:** Models burnout contagion
- **Erlang C:** Optimizes staffing within constraints

By combining cross-disciplinary tools, the scheduler achieves **defense in depth** against workforce instability.

---

**Document Version:** 1.0
**Last Updated:** 2025-12-29
**Maintainer:** Resilience Framework Team
