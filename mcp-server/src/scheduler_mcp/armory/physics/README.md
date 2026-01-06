# Physics Domain

> **Thermodynamics, Hopfield Networks, and Time Crystal Tools**

This domain applies physics concepts to schedule analysis and optimization.

---

## Tool Inventory (12 tools)

### Thermodynamics (4 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `calculate_schedule_entropy_tool` | Measure disorder in assignment distribution | Shannon entropy across dimensions |
| `get_entropy_monitor_state_tool` | Track entropy dynamics over time | Critical slowing detection |
| `analyze_phase_transitions_tool` | Detect approaching system failures | Universal early warning signals |
| `optimize_free_energy_tool` | Balance constraints vs flexibility | Helmholtz free energy: F = U - TS |

**When to use:** System appears to be approaching instability; need to quantify "disorder" in schedule; investigating why schedules keep failing.

### Hopfield Networks (5 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `calculate_hopfield_energy_tool` | Assess schedule stability | Energy function E = -0.5 * sum(w_ij * s_i * s_j) |
| `find_nearby_attractors_tool` | Discover alternative stable schedules | Basin of attraction mapping |
| `measure_basin_depth_tool` | Quantify robustness to perturbations | Energy barrier to escape |
| `detect_spurious_attractors_tool` | Find scheduling anti-patterns | Unintended stable states |
| `analyze_energy_landscape_tool` | Map schedule optimization surface | Local minima identification |

**When to use:** Schedule keeps converging to suboptimal patterns; need to understand why certain configurations are "sticky"; evaluating schedule robustness.

### Time Crystals (3 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `analyze_schedule_periodicity_tool` | Detect natural schedule cycles | Subharmonic responses (7, 14, 28 days) |
| `calculate_time_crystal_objective_tool` | Balance compliance vs stability | Anti-churn optimization |
| `get_checkpoint_status_tool` | Track stroboscopic state transitions | Discrete checkpoint management |

**When to use:** Preserving rotation patterns during regeneration; minimizing schedule churn; ensuring stable week-to-week transitions.

---

## Integration with Core Tools

These physics tools complement core resilience tools:

| Core Tool | Physics Complement |
|-----------|-------------------|
| `get_defense_level_tool` | `analyze_phase_transitions_tool` (early warning) |
| `run_contingency_analysis_tool` | `measure_basin_depth_tool` (robustness quantification) |
| `detect_conflicts_tool` | `detect_spurious_attractors_tool` (pattern analysis) |

---

## Scientific References

- Shannon, C.E. (1948). "A Mathematical Theory of Communication"
- Hopfield, J.J. (1982). "Neural networks and physical systems"
- Wilczek, F. (2012). "Quantum Time Crystals"
- Scheffer, M. et al. (2009). "Early-warning signals for critical transitions"

---

## Activation

```bash
export ARMORY_DOMAINS="physics"
# or
/armory physics
```
