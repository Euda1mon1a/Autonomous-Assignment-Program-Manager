# Advanced Resilience Domain

> **Homeostasis, Cognitive Load, Stigmergy, and Blast Radius Tools**

This domain contains specialized resilience analysis tools that go beyond the core N-1/N-2 framework.

---

## Tool Inventory (8 tools)

### Homeostasis & Feedback (2 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `analyze_homeostasis_tool` | Monitor system equilibrium | Feedback loops and allostatic load |
| `analyze_le_chatelier_tool` | Predict stress response | Equilibrium shift under perturbation |

**When to use:** Understanding how system compensates for disruptions; predicting rebound effects after changes; measuring cumulative stress.

### Cognitive Load (2 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `assess_cognitive_load_tool` | Monitor decision complexity | Miller's Law (7 plus/minus 2) |
| (reserved) | Decision queue analysis | Coordinator workload tracking |

**When to use:** Scheduling coordinator is overwhelmed; decision backlog building up; need to simplify interfaces.

### Stigmergy / Swarm Intelligence (2 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `get_behavioral_patterns_tool` | Emergent preference patterns | Ant pheromone trail analogy |
| `analyze_stigmergy_tool` | Slot-specific optimization signals | Collective intelligence for assignments |

**When to use:** Understanding unwritten scheduling preferences; finding optimal patterns from historical behavior; improving assignment suggestions.

### Blast Radius / Containment (2 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `calculate_blast_radius_tool` | Zone isolation health | Failure containment analysis |
| `analyze_hub_centrality_tool` | Single point of failure detection | Network betweenness and PageRank |

**When to use:** Investigating cascade failure potential; identifying critical dependencies; designing isolation boundaries.

---

## Integration with Core Tools

| Core Tool | Advanced Complement |
|-----------|-------------------|
| `get_defense_level_tool` | `analyze_homeostasis_tool` (equilibrium tracking) |
| `run_contingency_analysis_tool` | `calculate_blast_radius_tool` (containment) |
| `get_unified_critical_index_tool` | `analyze_hub_centrality_tool` (network analysis) |

---

## Homeostasis Feedback Loops

The system monitors several regulatory loops:

| Loop | Set Point | Too Low | Too High |
|------|-----------|---------|----------|
| Coverage | 100% | Gap alerts | Overstaffing waste |
| Utilization | 65-75% | Underuse | Burnout risk |
| Workload variance | < 15% | - | Equity issues |
| Decision queue | < 7 items | - | Cognitive overload |

---

## Le Chatelier Predictions

When stress is applied, the system shifts to compensate:

| Stressor | Short-term Response | Long-term Risk |
|----------|-------------------|----------------|
| Faculty absence | Redistribute load | Burnout spread |
| Coverage gap | Overtime requests | Hour violations |
| High turnover | Senior overload | Knowledge loss |
| Policy change | Workarounds | Compliance drift |

**Key insight:** Compensation is always partial and temporary. The system cannot fully absorb stress without external intervention.

---

## Cognitive Load Thresholds

Based on Miller's Law and decision fatigue research:

| Queue Size | Status | Action |
|------------|--------|--------|
| 1-5 | Healthy | Normal operation |
| 6-7 | Caution | Prioritize decisions |
| 8-9 | Warning | Defer non-critical |
| 10+ | Critical | Emergency triage |

---

## Scientific References

- Cannon, W.B. (1932). "The Wisdom of the Body" (homeostasis)
- Miller, G.A. (1956). "The magical number seven, plus or minus two"
- Grasse, P.P. (1959). "La reconstruction du nid" (stigmergy)
- Le Chatelier, H. (1884). "Sur un enonce general des lois des equilibres chimiques"

---

## Activation

```bash
export ARMORY_DOMAINS="resilience_advanced"
# or
/armory resilience_advanced
```
