# Operations Research Domain

> **Queuing Theory, Game Theory, Signal Processing, and Six Sigma Tools**

This domain applies operations research and statistical methods to scheduling optimization.

---

## Tool Inventory (10 tools)

### Queuing Theory (3 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `optimize_erlang_coverage_tool` | Optimal specialist staffing | M/M/c queuing (Erlang-C formula) |
| `calculate_erlang_metrics_tool` | Detailed queuing metrics | Wait probability, service level |
| `check_utilization_threshold_tool` | 80% utilization warning | Queuing theory critical threshold |

**When to use:** Determining optimal on-call coverage; predicting wait times; capacity planning for specialist services.

### Game Theory (2 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `calculate_shapley_workload_tool` | Fair workload distribution | Shapley value (cooperative game theory) |
| (reserved) | Coalition formation analysis | Matching theory for swaps |

**When to use:** Ensuring equitable workload distribution; calculating fair shares based on marginal contribution; resolving allocation disputes.

### Signal Processing (3 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `detect_schedule_changepoints_tool` | Identify regime shifts | CUSUM and PELT algorithms |
| `detect_critical_slowing_down_tool` | Early warning of cascade failures | Variance, autocorrelation, relaxation time |
| (reserved) | Spectral analysis of patterns | FFT for periodicity detection |

**When to use:** Understanding when policies changed; detecting approaching phase transitions; analyzing schedule pattern evolution.

### Six Sigma / Quality Control (2 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `calculate_process_capability_tool` | Schedule quality metrics | Cp/Cpk indices (Six Sigma) |
| `calculate_equity_metrics_tool` | Workload inequality | Gini coefficient |
| `generate_lorenz_curve_tool` | Visualize distribution | Cumulative share plotting |

**When to use:** Measuring scheduling process consistency; identifying capability gaps; tracking equity over time.

---

## Integration with Core Tools

| Core Tool | OR Complement |
|-----------|--------------|
| `validate_schedule_tool` | `calculate_process_capability_tool` (quality metrics) |
| `analyze_swap_candidates_tool` | `calculate_shapley_workload_tool` (fair allocation) |
| `get_defense_level_tool` | `detect_critical_slowing_down_tool` (early warning) |

---

## Key Formulas

### Erlang-C (Wait Probability)

```
P(wait) = [A^c / (c! * (1 - rho))] / [sum(A^k/k!) + A^c/(c!*(1-rho))]
```

Where:
- A = arrival_rate * service_time (offered load)
- c = number of servers
- rho = A/c (utilization)

### Shapley Value

```
phi_i = sum over S not containing i: [|S|! * (n-|S|-1)!] / n! * [v(S union {i}) - v(S)]
```

### Gini Coefficient

```
G = sum_i sum_j |x_i - x_j| / (2 * n * sum_i x_i)
```

---

## Capability Interpretation

| Cpk Value | Sigma Level | DPMO | Status |
|-----------|-------------|------|--------|
| >= 2.0 | 6-sigma | 3.4 | World Class |
| >= 1.67 | 5-sigma | 233 | Excellent |
| >= 1.33 | 4-sigma | 6,210 | Capable |
| >= 1.0 | 3-sigma | 66,807 | Marginal |
| < 1.0 | < 3-sigma | > 66,807 | Incapable |

---

## Scientific References

- Erlang, A.K. (1917). "Solution of some problems in the theory of probabilities"
- Shapley, L.S. (1953). "A value for n-person games"
- Page, E.S. (1954). "Continuous inspection schemes"
- Killick, R. et al. (2012). "Optimal detection of changepoints"

---

## Activation

```bash
export ARMORY_DOMAINS="operations_research"
# or
/armory operations_research
```
