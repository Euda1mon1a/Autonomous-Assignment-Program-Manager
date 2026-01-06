# Biology Domain

> **Epidemiology, Immune Systems, Gene Regulation, and Materials Science Tools**

This domain applies biological and materials science concepts to workforce health and constraint management.

---

## Tool Inventory (14 tools)

### Epidemiology (4 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `calculate_burnout_rt_tool` | Calculate burnout reproduction number | Rt < 1 = declining, Rt > 1 = spreading |
| `simulate_burnout_spread_tool` | Project burnout trajectory | SIR model (Susceptible-Infected-Recovered) |
| `simulate_burnout_contagion_tool` | Network-based contagion analysis | SIS model with superspreader detection |
| (reserved) | Herd immunity threshold calculation | 1 - 1/R0 |

**When to use:** Burnout appears to be spreading through team; need to identify superspreaders; planning interventions to break transmission chains.

### Immune System / AIS (4 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `assess_immune_response_tool` | Overall AIS health status | Detector coverage and repair readiness |
| `check_memory_cells_tool` | Review learned anomaly patterns | Faster response to known issues |
| `analyze_antibody_response_tool` | Find best repair strategy | Clonal selection by affinity |
| (reserved) | Detector training status | Negative selection algorithm |

**When to use:** Investigating why similar issues keep recurring; evaluating system's self-healing capability; understanding which repair strategies work best.

### Gene Regulation (2 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `analyze_transcription_triggers_tool` | Constraint activation network | Transcription factors control constraint weights |
| (reserved) | Chromatin state analysis | Constraint accessibility (open/silenced) |

**When to use:** Understanding how constraints interact; debugging why certain rules activate/deactivate; analyzing constraint hierarchy.

### Materials Science (4 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `assess_creep_fatigue_tool` | Predict burnout from workload | Larson-Miller Parameter (LMP) |
| `calculate_recovery_distance_tool` | Measure edit distance to feasibility | Recovery after N-1 shocks |
| (reserved) | Stress-strain analysis | Workload vs performance curve |
| (reserved) | Fatigue cycle counting | Miner's rule cumulative damage |

**When to use:** Predicting which residents are approaching burnout; quantifying schedule fragility; understanding recovery costs.

---

## Integration with Core Tools

| Core Tool | Biology Complement |
|-----------|-------------------|
| `get_unified_critical_index_tool` | `simulate_burnout_contagion_tool` (superspreader analysis) |
| `run_contingency_analysis_tool` | `calculate_recovery_distance_tool` (edit distance) |
| `validate_schedule_tool` | `analyze_transcription_triggers_tool` (constraint activation) |

---

## Epidemiological Thresholds

| Rt Value | Status | Action |
|----------|--------|--------|
| < 0.5 | Declining rapidly | Maintain current practices |
| 0.5 - 1.0 | Declining slowly | Monitor closely |
| 1.0 - 1.5 | Growing slowly | Targeted interventions |
| 1.5 - 2.0 | Growing | Aggressive intervention |
| > 2.0 | Rapid spread | Emergency measures |

---

## Scientific References

- Kermack, W.O. & McKendrick, A.G. (1927). "Contributions to the mathematical theory of epidemics"
- Forrest, S. et al. (1994). "Self-nonself discrimination in a computer"
- Larson, F.R. & Miller, J. (1952). "Time-temperature relationship for rupture and creep stresses"
- Bakker, A.B. et al. (2009). "Burnout contagion among intensive care nurses"

---

## Activation

```bash
export ARMORY_DOMAINS="biology"
# or
/armory biology
```
