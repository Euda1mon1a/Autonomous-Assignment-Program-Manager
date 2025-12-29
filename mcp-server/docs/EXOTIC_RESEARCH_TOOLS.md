# Exotic Cross-Disciplinary Research MCP Tools

> **Version**: 1.0
> **Added**: 2025-12-29
> **Tools Added**: 20 new MCP tools from 6 research domains

---

## Overview

This document covers the **20 new MCP tools** implementing exotic cross-disciplinary research concepts. These tools extend the existing resilience framework with advanced analytics from control theory, signal processing, game theory, financial risk analysis, ecology, and neuroscience.

### Tool Categories Summary

| Domain | Source Field | Tools | Purpose |
|--------|-------------|-------|---------|
| **Kalman Filter** | Control Theory | 2 | Noise filtering, trend extraction |
| **Fourier/FFT** | Signal Processing | 3 | Cycle detection, harmonic resonance |
| **Game Theory** | Economics | 3 | Nash stability, swap prediction |
| **Value-at-Risk** | Financial Engineering | 4 | Probabilistic risk bounds |
| **Lotka-Volterra** | Ecology | 4 | Supply/demand oscillations |
| **Hopfield Attractor** | Neuroscience | 4 | Energy landscape, stable patterns |

---

## 1. Kalman Filter Tools (Control Theory)

**Source Domain**: Control Theory & Estimation Theory

**Purpose**: Filter noisy workload measurements to extract true underlying trends.

### Core Concept

The Kalman filter is an optimal recursive estimator that combines:
- **Predictions** from a system model
- **Observations** (noisy measurements)

It produces filtered estimates with minimum variance, widely used in GPS, robotics, and signal processing.

**Key Equations**:
```
# Predict
x_pred = x_est
p_pred = p_est + Q

# Update
K = p_pred / (p_pred + R)
x_est = x_pred + K * (z - x_pred)
p_est = (1 - K) * p_pred
```

### Tools

#### `analyze_workload_trend`

Applies Kalman filter to workload history, returning filtered trend and predictions.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workload_history` | array | Yes | Time series of workload observations |
| `process_noise` | float | No | Q parameter (default: 1.0) |
| `measurement_noise` | float | No | R parameter (default: 2.0) |
| `prediction_steps` | int | No | Future steps to predict (default: 5) |

**Response**:
```json
{
  "filtered_values": [60.2, 61.5, 62.1, ...],
  "predictions": [63.0, 63.5, 64.0, ...],
  "confidence_intervals": [...],
  "trend_direction": "INCREASING",
  "trend_strength": 0.73,
  "smoothness_score": 0.85
}
```

**Integration**: Complements SPC monitoring by providing cleaner signals before Western Electric rule analysis.

---

#### `detect_workload_anomalies`

Compares raw vs filtered values to identify anomalies.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workload_history` | array | Yes | Time series of workload observations |
| `threshold_sigma` | float | No | Standard deviations for anomaly (default: 2.0) |

**Response**:
```json
{
  "anomalies": [
    {
      "index": 7,
      "raw_value": 85.0,
      "filtered_value": 62.3,
      "residual": 22.7,
      "severity": "HIGH",
      "sigma_deviation": 3.2
    }
  ],
  "anomaly_count": 3,
  "recommendations": ["Investigate week 7 spike"]
}
```

**Severity Classification**:
- MODERATE: 2-3σ deviation
- HIGH: 3-4σ deviation
- CRITICAL: 4+σ deviation

---

## 2. Fourier/FFT Analysis Tools (Signal Processing)

**Source Domain**: Signal Processing & Harmonic Analysis

**Purpose**: Detect natural cycles in scheduling patterns (7-day, 14-day, 28-day ACGME windows).

### Core Concept

Fourier Transform decomposes time-domain signals into frequency components:
- **Dominant frequencies** reveal periodic patterns
- **Power spectrum** shows strength of each cycle
- **Spectral entropy** measures pattern regularity

**FFT Application**:
```python
fft_result = np.fft.rfft(signal)
power_spectrum = np.abs(fft_result)**2
freqs = np.fft.rfftfreq(len(signal), d=1)
periods = 1 / freqs[1:]  # Convert to periods (days)
```

### Tools

#### `detect_schedule_cycles`

FFT-based detection of dominant periodic patterns.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `signal` | array | Yes | Daily schedule metric (hours, swaps, etc.) |
| `sampling_period_days` | float | No | Sampling interval (default: 1.0) |
| `top_n_periods` | int | No | Number of periods to return (default: 5) |

**Response**:
```json
{
  "dominant_period_days": 7.1,
  "periodicity_detected": true,
  "all_periods": [
    {"period_days": 7.1, "power": 145.3, "interpretation": "Weekly cycle"},
    {"period_days": 14.0, "power": 42.1, "interpretation": "Bi-weekly pattern"},
    {"period_days": 28.2, "power": 38.7, "interpretation": "ACGME 4-week window"}
  ],
  "signal_to_noise": 4.2
}
```

---

#### `analyze_harmonic_resonance`

Check alignment with ACGME regulatory windows.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `signal` | array | Yes | Daily schedule metric |
| `target_periods` | array | No | ACGME periods [7, 14, 28] |

**Response**:
```json
{
  "acgme_7d_alignment": 0.92,
  "acgme_14d_alignment": 0.85,
  "acgme_28d_alignment": 0.78,
  "overall_resonance": 0.85,
  "health_status": "healthy",
  "resonant_harmonics": ["7-day"],
  "dissonant_frequencies": [],
  "recommendations": ["Schedule aligns well with ACGME cycles"]
}
```

---

#### `calculate_spectral_entropy`

Measure schedule complexity via Shannon entropy of power spectrum.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `signal` | array | Yes | Daily schedule metric |

**Response**:
```json
{
  "spectral_entropy": 0.28,
  "signal_complexity": "simple",
  "predictability": "high",
  "frequency_concentration": 0.72,
  "interpretation": "Highly regular schedule with dominant periodic pattern"
}
```

**Complexity Classification**:
- Simple: entropy < 0.3 (highly regular)
- Moderate: entropy 0.3-0.6
- Complex: entropy 0.6-0.8
- Chaotic: entropy > 0.8 (unpredictable)

---

## 3. Game Theory Tools (Economics)

**Source Domain**: Game Theory & Mechanism Design

**Purpose**: Detect stable schedule states where no individual has incentive to deviate (Nash equilibrium).

### Core Concept

In game-theoretic terms:
- **Players**: Residents/faculty
- **Strategies**: Accept current assignment vs request swap
- **Payoffs**: Preference satisfaction, workload balance, convenience

A schedule is **Nash stable** if no player can improve by unilaterally changing their assignment.

### Tools

#### `analyze_nash_stability`

Check if current schedule is a Nash equilibrium.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | Yes | Analysis period start |
| `end_date` | string | Yes | Analysis period end |
| `utility_weights` | object | No | Custom weights for utility components |

**Response**:
```json
{
  "is_nash_equilibrium": false,
  "stability_score": 0.72,
  "players_with_deviations": 12,
  "deviation_rate": 0.30,
  "deviations": [
    {
      "person_id": "FAC-001",
      "current_utility": 0.65,
      "best_alternative_utility": 0.82,
      "utility_gain": 0.17,
      "deviation_type": "SWAP",
      "description": "Prefers to swap clinic days with FAC-002"
    }
  ],
  "interpretation": "Schedule is unstable; expect 30% swap request rate"
}
```

---

#### `find_deviation_incentives`

Analyze specific person's incentive to deviate.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | string | Yes | Person to analyze |
| `start_date` | string | Yes | Analysis period start |
| `end_date` | string | Yes | Analysis period end |

**Response**:
```json
{
  "person_id": "FAC-001",
  "current_utility": 0.65,
  "utility_breakdown": {
    "workload_fairness": 0.55,
    "preference_match": 0.70,
    "convenience": 0.80,
    "continuity": 0.60
  },
  "best_alternatives": [
    {
      "action": "swap_with_FAC-002",
      "new_utility": 0.82,
      "improvement": 0.17
    }
  ],
  "has_deviation_incentive": true,
  "swap_likelihood": "high"
}
```

---

#### `detect_coordination_failures`

Find Pareto improvements blocked by coordination barriers.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | Yes | Analysis period start |
| `end_date` | string | Yes | Analysis period end |
| `max_parties` | int | No | Max players in multi-way swap (default: 3) |

**Response**:
```json
{
  "coordination_failures": [
    {
      "failure_type": "MULTI_WAY_SWAP_NEEDED",
      "parties": ["FAC-001", "FAC-002", "FAC-003"],
      "current_total_utility": 1.95,
      "potential_total_utility": 2.40,
      "welfare_gain": 0.45,
      "blocked_by": "No multi-way swap mechanism available"
    }
  ],
  "total_welfare_left_on_table": 1.23,
  "recommendations": [
    "Enable 3-way swap matching in swap system",
    "Create swap marketplace for complex trades"
  ]
}
```

---

## 4. Value-at-Risk Tools (Financial Engineering)

**Source Domain**: Financial Risk Management

**Purpose**: Quantify worst-case schedule disruption using probabilistic bounds.

### Core Concept

**VaR (Value-at-Risk)**: "With X% confidence, losses won't exceed Y"
**CVaR (Conditional VaR)**: "Average loss in worst (1-X)% scenarios"

Applied to scheduling:
- VaR for coverage: "With 95% confidence, coverage won't drop below 85%"
- CVaR: "In the worst 5% of disruption scenarios, average coverage is 72%"

### Tools

#### `calculate_coverage_var`

VaR for coverage metrics at multiple confidence levels.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | Yes | Analysis period start |
| `end_date` | string | Yes | Analysis period end |
| `confidence_levels` | array | No | e.g., [0.90, 0.95, 0.99] |

**Response**:
```json
{
  "var_metrics": [
    {
      "confidence": 0.95,
      "var_coverage_drop": 12.1,
      "interpretation": "With 95% confidence, coverage won't drop more than 12.1%"
    },
    {
      "confidence": 0.99,
      "var_coverage_drop": 18.5,
      "interpretation": "With 99% confidence, coverage won't drop more than 18.5%"
    }
  ],
  "current_coverage": 94.2,
  "severity": "moderate",
  "recommendations": ["Maintain current backup pool size"]
}
```

---

#### `calculate_workload_var`

VaR for workload distribution metrics.

**Response**:
```json
{
  "var_metrics": [
    {
      "confidence": 0.95,
      "var_max_hours": 78.5,
      "var_gini_increase": 0.08
    }
  ],
  "current_gini": 0.12,
  "severity": "low",
  "interpretation": "Workload distribution stable under most scenarios"
}
```

---

#### `simulate_disruption_scenarios`

Monte Carlo simulation of random disruptions.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `num_simulations` | int | No | Number of Monte Carlo runs (default: 1000) |
| `disruption_types` | array | No | Types to simulate (absence, deployment, etc.) |
| `seed` | int | No | Random seed for reproducibility |

**Response**:
```json
{
  "simulations_run": 1000,
  "var_95": 15.2,
  "var_99": 22.8,
  "worst_case_coverage_drop": 35.1,
  "disruption_breakdown": {
    "absence": {"frequency": 0.65, "avg_impact": 8.2},
    "deployment": {"frequency": 0.15, "avg_impact": 18.5},
    "illness": {"frequency": 0.20, "avg_impact": 12.1}
  },
  "recommendations": ["Build TDY-specific contingency pool"]
}
```

---

#### `calculate_conditional_var`

Expected Shortfall (CVaR) for tail risk.

**Response**:
```json
{
  "cvar_95": 18.7,
  "cvar_99": 27.3,
  "interpretation": "In worst 5% of scenarios, average coverage drop is 18.7%",
  "tail_scenarios": [
    {"scenario": "Multiple TDY + flu outbreak", "coverage_drop": 32.5}
  ]
}
```

---

## 5. Lotka-Volterra Tools (Ecology)

**Source Domain**: Population Ecology & Dynamical Systems

**Purpose**: Model oscillations between resource supply (available residents) and demand (workload).

### Core Concept

The Lotka-Volterra equations model predator-prey dynamics:
```
dx/dt = αx - βxy    (prey/capacity: grows, consumed by demand)
dy/dt = δxy - γy    (predator/demand: grows from capacity, decays)
```

Applied to scheduling:
- **x** = Available capacity/slack
- **y** = Workload demand
- Predicts boom/bust cycles in coverage

**Equilibrium**: x* = γ/δ, y* = α/β

### Tools

#### `analyze_supply_demand_cycles`

Fit Lotka-Volterra model to historical data.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `historical_data` | array | Yes | List of {date, capacity, demand} |
| `prediction_days` | int | No | Days to forecast (default: 90) |

**Response**:
```json
{
  "fitted_parameters": {
    "alpha": 0.12,
    "beta": 0.015,
    "delta": 0.008,
    "gamma": 0.10
  },
  "equilibrium_capacity": 12.5,
  "equilibrium_demand": 8.0,
  "oscillation_period_days": 57.3,
  "system_stability": "marginally_stable",
  "r_squared": 0.82,
  "interpretation": "System oscillates with ~8-week cycles"
}
```

---

#### `predict_capacity_crunch`

Forecast when demand will exceed supply.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `current_capacity` | float | Yes | Current available capacity |
| `current_demand` | float | Yes | Current workload demand |
| `alpha`, `beta`, `delta`, `gamma` | float | Yes | Model parameters |
| `crunch_threshold` | float | No | Critical capacity level |

**Response**:
```json
{
  "crunch_predicted": true,
  "days_until_crunch": 42,
  "risk_level": "HIGH",
  "minimum_capacity_reached": 6.2,
  "recovery_time_days": 28,
  "recommendations": ["Add capacity before day 30 to prevent crunch"]
}
```

---

#### `find_equilibrium_point`

Calculate stable equilibrium and sensitivity.

**Response**:
```json
{
  "equilibrium_capacity": 12.5,
  "equilibrium_demand": 8.0,
  "oscillation_period_days": 57.3,
  "sensitivity_analysis": {
    "alpha_elasticity": 0.8,
    "gamma_elasticity": -0.6
  },
  "recommendations": ["Increase α (capacity growth) for higher equilibrium"]
}
```

---

#### `simulate_intervention`

Model effect of adding capacity or reducing demand.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `intervention_type` | enum | Yes | "add_capacity", "reduce_demand", etc. |
| `intervention_magnitude` | float | Yes | Fractional change (e.g., 0.25 = 25%) |

**Response**:
```json
{
  "intervention_type": "add_capacity",
  "magnitude": 0.25,
  "effectiveness_score": 0.73,
  "capacity_improvement": 18.5,
  "new_equilibrium_capacity": 15.6,
  "recommendation": "HIGHLY EFFECTIVE: Adding 25% capacity prevents crunch"
}
```

---

## 6. Hopfield Attractor Tools (Neuroscience)

**Source Domain**: Neural Networks & Computational Neuroscience

**Purpose**: Model schedule states as attractors in an energy landscape.

### Core Concept

Hopfield networks model associative memory:
- **State**: Schedule encoded as binary pattern
- **Energy**: E = -0.5 × Σ(w_ij × s_i × s_j)
- **Attractors**: Stable patterns (energy minima)
- **Basin of Attraction**: Region converging to same attractor

Lower energy = more stable schedule. Basin depth = robustness to perturbation.

### Tools

#### `calculate_hopfield_energy`

Compute Hopfield energy of current schedule state.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | Yes | Schedule period start |
| `end_date` | string | Yes | Schedule period end |

**Response**:
```json
{
  "energy": -42.5,
  "normalized_energy": 0.35,
  "stability_classification": "stable",
  "distance_to_nearest_minimum": 3,
  "interpretation": "Schedule is in a stable configuration"
}
```

**Stability Classification**:
- very_stable: normalized energy < 0.2
- stable: 0.2-0.4
- marginally_stable: 0.4-0.6
- unstable: 0.6-0.8
- highly_unstable: > 0.8

---

#### `find_nearby_attractors`

Identify stable patterns near current state.

**Response**:
```json
{
  "current_attractor": {
    "type": "local_minimum",
    "energy": -42.5
  },
  "nearby_attractors": [
    {
      "type": "global_minimum",
      "energy": -48.2,
      "hamming_distance": 5,
      "description": "More balanced workload distribution"
    },
    {
      "type": "local_minimum",
      "energy": -40.1,
      "hamming_distance": 3,
      "description": "Slightly worse but accessible via simple swaps"
    }
  ],
  "improvement_possible": true,
  "recommendations": ["5 swaps could reach global minimum"]
}
```

---

#### `measure_basin_depth`

How stable is current attractor (energy barrier to escape).

**Response**:
```json
{
  "basin_depth": 8.5,
  "escape_barrier": {
    "min_barrier": 3.2,
    "avg_barrier": 6.1,
    "max_barrier": 12.8
  },
  "basin_stability_index": 0.78,
  "robustness_threshold": 3,
  "interpretation": "Schedule can absorb 3+ random perturbations without destabilizing"
}
```

---

#### `detect_spurious_attractors`

Find unintended stable patterns (scheduling anti-patterns).

**Response**:
```json
{
  "spurious_attractors_detected": 2,
  "attractors": [
    {
      "type": "OVERLOAD_CONCENTRATION",
      "description": "3 residents consistently overloaded while others underutilized",
      "risk_level": "high",
      "basin_coverage": 0.15,
      "mitigation": "Enforce workload caps in constraint engine"
    },
    {
      "type": "SHIFT_CLUSTERING",
      "description": "Night shifts cluster on same residents",
      "risk_level": "medium",
      "mitigation": "Add night shift rotation constraint"
    }
  ],
  "total_basin_coverage": 0.25,
  "recommendations": ["25% of state space leads to anti-patterns"]
}
```

---

## Integration with Existing Framework

### Complement Matrix

| New Tool | Complements | Synergy |
|----------|-------------|---------|
| Kalman Filter | SPC Monitoring | Cleaner signals for Western Electric rules |
| Fourier/FFT | Time Crystal Periodicity | Precise cycle detection for anti-churn |
| Game Theory | Shapley Fairness | Stability + fairness together |
| VaR | N-1/N-2 Contingency | Probabilistic bounds on disruption |
| Lotka-Volterra | Homeostasis | Models dynamics homeostasis responds to |
| Hopfield | Thermodynamics | Energy landscape complements free energy |

### Usage Patterns

**Proactive Risk Assessment**:
```python
# 1. Filter noise from workload data
trend = await analyze_workload_trend(workload_history=data)

# 2. Detect natural cycles
cycles = await detect_schedule_cycles(signal=trend.filtered_values)

# 3. Check Nash stability
nash = await analyze_nash_stability(start_date="2025-01-01", end_date="2025-01-31")

# 4. Calculate VaR bounds
var = await calculate_coverage_var(confidence_levels=[0.95, 0.99])

# 5. Check energy landscape
energy = await calculate_hopfield_energy(start_date="2025-01-01", end_date="2025-01-31")
```

### Recommended Execution Frequency

| Tool Category | Frequency | Rationale |
|---------------|-----------|-----------|
| Kalman Filter | On new data | Real-time filtering |
| Fourier/FFT | Weekly | Detect cycle changes |
| Game Theory | Daily | Predict swap requests |
| VaR | Weekly | Risk assessment |
| Lotka-Volterra | Monthly | Long-term dynamics |
| Hopfield | On schedule change | Stability check |

---

## Dependencies

All tools use existing project dependencies:
- `numpy>=2.0` (all tools)
- `scipy>=1.11` (Lotka-Volterra ODE integration)
- `pydantic>=2.0` (validation)

No new dependencies required.

---

## File Locations

| Component | Location |
|-----------|----------|
| Kalman Filter | `mcp-server/src/scheduler_mcp/tools/kalman_filter_tools.py` |
| Fourier/FFT | `mcp-server/src/scheduler_mcp/tools/fourier_analysis_tools.py` |
| Game Theory | `mcp-server/src/scheduler_mcp/tools/game_theory_tools.py` |
| VaR Risk | `mcp-server/src/scheduler_mcp/var_risk_tools.py` |
| Lotka-Volterra | `mcp-server/src/scheduler_mcp/tools/ecological_dynamics_tools.py` |
| Hopfield | `mcp-server/src/scheduler_mcp/hopfield_attractor_tools.py` |
| Tests | `mcp-server/tests/test_*.py` |

---

## References

### Control Theory
- Kalman, R.E. (1960). "A New Approach to Linear Filtering and Prediction Problems." *ASME Journal of Basic Engineering*.

### Signal Processing
- Cooley, J.W. & Tukey, J.W. (1965). "An Algorithm for the Machine Calculation of Complex Fourier Series." *Mathematics of Computation*.

### Game Theory
- Nash, J. (1950). "Equilibrium Points in N-Person Games." *Proceedings of the National Academy of Sciences*.
- Shapley, L.S. (1953). "A Value for N-Person Games." *Contributions to the Theory of Games*.

### Financial Risk
- Jorion, P. (2006). *Value at Risk: The New Benchmark for Managing Financial Risk*. McGraw-Hill.

### Ecology
- Lotka, A.J. (1925). *Elements of Physical Biology*. Williams & Wilkins.
- Volterra, V. (1926). "Fluctuations in the Abundance of a Species Considered Mathematically." *Nature*.

### Neuroscience
- Hopfield, J.J. (1982). "Neural Networks and Physical Systems with Emergent Collective Computational Abilities." *Proceedings of the National Academy of Sciences*.

---

**Document Version**: 1.0
**Last Updated**: 2025-12-29
**Total New Tools**: 20
