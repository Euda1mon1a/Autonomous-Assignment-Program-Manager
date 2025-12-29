# VaR (Value-at-Risk) Analysis for Schedule Vulnerability

## Overview

The VaR Risk Analysis tools apply **financial risk management concepts** to medical residency scheduling. They quantify worst-case schedule disruption scenarios using probabilistic bounds, complementing existing N-1/N-2 contingency analysis.

## What is Value-at-Risk (VaR)?

**VaR** answers the question: *"What is the maximum loss we can expect with X% confidence?"*

For example:
- **95% VaR for coverage = 12%** means: "With 95% confidence, coverage won't drop more than 12%"
- Only 5% of scenarios will have coverage drops exceeding 12%

### VaR vs CVaR (Conditional VaR)

- **VaR**: Maximum loss at a given confidence level (threshold)
- **CVaR (Expected Shortfall)**: Average loss in worst-case scenarios beyond VaR
  - More informative about **tail risk**
  - Captures severity of extreme events

Example:
```
VaR (95%) = 15% coverage drop
CVaR (95%) = 22% coverage drop

Interpretation: "In the worst 5% of scenarios, average coverage drop is 22%"
```

If CVaR >> VaR, you have significant tail risk (heavy-tailed distribution).

## Available Tools

### 1. `calculate_coverage_var_tool`

Quantifies risk of coverage degradation.

**Use case**: "How bad can coverage get with 95% confidence?"

```python
result = await calculate_coverage_var_tool(
    start_date="2025-01-01",
    end_date="2025-01-31",
    confidence_levels=[0.90, 0.95, 0.99],
    rotation_types=None,  # All rotations
    historical_days=90
)

# Output
for metric in result.var_metrics:
    print(metric.interpretation)
# "With 90% confidence, coverage won't drop more than 8.2%"
# "With 95% confidence, coverage won't drop more than 12.1%"
# "With 99% confidence, coverage won't drop more than 18.7%"
```

**Parameters**:
- `confidence_levels`: List of confidence levels (e.g., [0.90, 0.95, 0.99])
- `rotation_types`: Filter by rotation type (optional)
- `historical_days`: Days of historical data to analyze (30-365)

**Returns**:
- VaR at each confidence level
- Risk severity classification (low, moderate, high, critical, extreme)
- Recommendations for risk mitigation

### 2. `calculate_workload_var_tool`

Quantifies risk of unfair workload distribution.

**Use case**: "How unbalanced can workload get?"

```python
result = await calculate_workload_var_tool(
    start_date="2025-01-01",
    end_date="2025-03-31",
    metric="gini_coefficient"
)

if result.severity == "critical":
    print("Workload inequality at critical levels!")
    for rec in result.recommendations:
        print(f"- {rec}")
```

**Metrics available**:
- `gini_coefficient`: Inequality measure (0=perfect equality, 1=max inequality)
- `max_hours`: Maximum individual work hours
- `variance`: Workload variance across team

**Interpretation**:
- Gini < 0.20: Balanced workload
- Gini 0.20-0.30: Moderate inequality
- Gini > 0.30: High inequality (action needed)

### 3. `simulate_disruption_scenarios_tool`

Run Monte Carlo simulation of random disruptions.

**Use case**: "What happens if multiple people are absent?"

```python
result = await simulate_disruption_scenarios_tool(
    start_date="2025-01-01",
    end_date="2025-01-31",
    num_simulations=1000,
    disruption_types=["random_absence"],
    disruption_probability=0.05,  # 5% chance per person per day
    seed=42  # For reproducibility
)

print(f"95% VaR: {result.var_95_coverage_drop*100:.1f}% coverage drop")
print(f"99% VaR: {result.var_99_coverage_drop*100:.1f}% coverage drop")
print(f"Worst case: {result.worst_case_scenario.coverage_impact*100:.1f}% drop")
```

**Disruption types**:
- `random_absence`: Unplanned individual absences
- `mass_casualty`: Multiple simultaneous disruptions
- `deployment`: Military deployment scenario
- `illness_cluster`: Illness outbreak (e.g., flu, COVID)
- `equipment_failure`: Equipment/facility failure
- `weather_event`: Natural disaster

**Returns**:
- VaR at 95% and 99% confidence
- Sample scenarios (up to 10)
- Worst-case scenario with full details
- Mean coverage drop across all scenarios

### 4. `calculate_conditional_var_tool`

Calculate CVaR (Expected Shortfall) for tail risk analysis.

**Use case**: "How bad are the worst-case scenarios?"

```python
result = await calculate_conditional_var_tool(
    start_date="2025-01-01",
    end_date="2025-03-31",
    confidence_level=0.95,
    loss_metric="coverage_drop"
)

print(f"VaR (95%): {result.var_value:.2%}")
print(f"CVaR (Expected Shortfall): {result.cvar_value:.2%}")

# Check tail risk premium
tail_premium = result.cvar_value - result.var_value
if tail_premium > 0.05:
    print("WARNING: Significant tail risk detected!")
    print("Worst scenarios are much worse than VaR threshold")
```

**Loss metrics**:
- `coverage_drop`: Coverage degradation (0-1 scale)
- `workload_spike`: Workload increase multiplier
- `acgme_violations`: Count of ACGME violations

## Use Cases

### 1. Strategic Planning

**Question**: "Should we hire an additional faculty member?"

```python
# Baseline risk
baseline = await calculate_coverage_var_tool(
    start_date="2025-01-01",
    end_date="2025-12-31",
    confidence_levels=[0.95]
)

# Simulate with +1 faculty (adjust disruption probability)
with_buffer = await simulate_disruption_scenarios_tool(
    start_date="2025-01-01",
    end_date="2025-12-31",
    num_simulations=1000,
    disruption_probability=0.04  # Lower due to buffer
)

# Compare VaR
if baseline.var_metrics[0].var_value > 0.15:
    print("HIGH RISK: Recommend hiring additional faculty")
```

### 2. Deployment Preparation

**Question**: "Can we handle a 2-person deployment?"

```python
result = await simulate_disruption_scenarios_tool(
    start_date="2025-02-01",
    end_date="2025-05-31",  # 4-month deployment
    disruption_types=["deployment"],
    disruption_probability=0.10,  # 10% (2 out of 20)
    num_simulations=500
)

if result.var_95_coverage_drop > 0.20:
    print("ALERT: Deployment will severely impact coverage")
    print("Recommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")
```

### 3. Flu Season Preparedness

**Question**: "How vulnerable are we to illness outbreak?"

```python
result = await simulate_disruption_scenarios_tool(
    start_date="2025-12-01",  # Flu season
    end_date="2026-02-28",
    disruption_types=["illness_cluster"],
    disruption_probability=0.08,  # 8% (cluster effect)
    num_simulations=1000
)

# Check CVaR for tail risk
cvar_result = await calculate_conditional_var_tool(
    start_date="2025-12-01",
    end_date="2026-02-28",
    confidence_level=0.95,
    loss_metric="coverage_drop"
)

if cvar_result.cvar_value > 0.25:
    print("CRITICAL: Flu outbreak could cause 25%+ coverage loss")
    print("Implement defense in depth:")
    print("  1. Cross-train faculty")
    print("  2. Establish backup call pool")
    print("  3. Pre-negotiate coverage MOUs with nearby programs")
```

### 4. Workload Equity Monitoring

**Question**: "Is workload becoming dangerously unequal?"

```python
result = await calculate_workload_var_tool(
    start_date="2025-01-01",
    end_date="2025-03-31",
    metric="gini_coefficient"
)

if result.severity in ["critical", "extreme"]:
    print(f"Gini coefficient VaR (95%): {result.var_metrics[0].var_value:.3f}")
    print("Workload inequality exceeds acceptable bounds")
    print("Action required:")
    for rec in result.recommendations:
        print(f"  - {rec}")
```

## Integration with Existing Tools

VaR tools complement other resilience framework components:

| Tool | Purpose | Complements |
|------|---------|-------------|
| **VaR Analysis** | Probabilistic risk bounds | N-1/N-2 contingency (deterministic) |
| **Monte Carlo Simulation** | Stochastic scenario testing | Pre-solver validation |
| **CVaR (Expected Shortfall)** | Tail risk quantification | Unified Critical Index |
| **Workload VaR** | Inequality risk | Equity metrics (Gini, Lorenz) |

### Workflow Example

```python
# 1. Check deterministic contingency
n1_result = await check_n1_contingency()

# 2. If contingency passes, quantify probabilistic risk
var_result = await calculate_coverage_var_tool(
    start_date="2025-01-01",
    end_date="2025-12-31",
    confidence_levels=[0.95, 0.99]
)

# 3. If VaR is acceptable, check tail risk
cvar_result = await calculate_conditional_var_tool(
    start_date="2025-01-01",
    end_date="2025-12-31",
    confidence_level=0.95
)

# 4. If tail risk is high, run detailed simulation
if cvar_result.cvar_value > 0.20:
    sim_result = await simulate_disruption_scenarios_tool(
        start_date="2025-01-01",
        end_date="2025-12-31",
        num_simulations=1000
    )

    print("Detailed scenario analysis:")
    for scenario in sim_result.sample_scenarios[:5]:
        print(f"  {scenario.disruptions_count} disruptions -> "
              f"{scenario.coverage_impact*100:.1f}% coverage loss")
```

## Interpreting Results

### Risk Severity Levels

| Severity | VaR Range | Action |
|----------|-----------|--------|
| **Low** | < 10% | Monitor only |
| **Moderate** | 10-15% | Increase monitoring |
| **High** | 15-20% | Implement mitigation |
| **Critical** | 20-30% | Urgent action required |
| **Extreme** | > 30% | Emergency intervention |

### VaR Confidence Levels

| Confidence | Use Case |
|------------|----------|
| **90%** | Routine planning, moderate risk tolerance |
| **95%** | Standard operations, balanced risk |
| **99%** | High-stakes scenarios, low risk tolerance |
| **99.9%** | Military deployments, extreme risk aversion |

### CVaR Interpretation

```python
var = result.var_value
cvar = result.cvar_value
tail_premium = cvar - var

if tail_premium < 0.02:
    print("Tail risk is minimal (thin-tailed distribution)")
elif tail_premium < 0.05:
    print("Moderate tail risk (normal-ish distribution)")
else:
    print("HIGH TAIL RISK (heavy-tailed distribution)")
    print("Worst scenarios are significantly worse than VaR")
```

## Best Practices

1. **Use multiple confidence levels**: Compare 90%, 95%, 99% to understand risk distribution
2. **Combine VaR and CVaR**: VaR gives threshold, CVaR gives tail severity
3. **Run simulations seasonally**: Flu season vs summer vacation patterns differ
4. **Set reproducible seeds**: For scenario testing, use `seed` parameter
5. **Monitor trends**: Track VaR over time to detect deteriorating resilience
6. **Validate assumptions**: Review disruption probabilities quarterly

## Limitations

1. **Historical data quality**: VaR accuracy depends on representative historical data
2. **Distribution assumptions**: Placeholder uses exponential/beta distributions
3. **Independence assumption**: Monte Carlo assumes disruptions are independent
4. **Non-stationary risk**: VaR from past data may not predict future (regime shifts)
5. **Correlation effects**: Real disruptions may cluster (not captured in simple model)

## Future Enhancements

Planned improvements (see MCP Placeholder Implementation Plan):

1. **Copula-based simulation**: Capture disruption correlation structure
2. **Regime-switching models**: Different VaR for normal vs crisis periods
3. **Bayesian VaR**: Update VaR as new data arrives
4. **Extreme Value Theory**: Better tail risk modeling (GPD, GEV)
5. **Stress testing**: Scenario-based VaR for specific threats

## References

### Financial Risk Management

- Jorion, P. (2006). *Value at Risk: The New Benchmark for Managing Financial Risk*
- McNeil, A.J., Frey, R., & Embrechts, P. (2015). *Quantitative Risk Management*

### Healthcare Applications

- Dumas, M.B., Brizendine, E.J. (2014). "Emergency department resource planning using stochastic simulation"
- Green, L.V. (2006). "Queueing analysis in healthcare"

### Statistical Methods

- Embrechts, P., Klüppelberg, C., & Mikosch, T. (1997). *Modelling Extremal Events*
- Acerbi, C., Tasche, D. (2002). "Expected Shortfall: A natural coherent alternative to Value at Risk"

## See Also

- [Resilience Framework Overview](../../docs/architecture/cross-disciplinary-resilience.md)
- [N-1/N-2 Contingency Analysis](../../docs/architecture/N_CONTINGENCY.md)
- [Monte Carlo Simulation Guide](../../docs/guides/MONTE_CARLO_SIMULATION.md)
- [Process Capability Analysis](../../docs/resilience/PROCESS_CAPABILITY.md)
