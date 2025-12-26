# Cross-Disciplinary Bridge Specifications

**Purpose:** Integration specifications connecting resilience framework components across disciplinary boundaries.

---

## Overview

The Resilience Framework adapts concepts from multiple industries (nuclear engineering, forestry, seismology, epidemiology, materials science, finance, telecommunications, game theory). **Bridge specifications** define how these heterogeneous systems communicate and trigger each other.

### What is a Bridge?

A **bridge** is a formal integration specification that:

1. **Maps** outputs from one system to inputs of another
2. **Defines** trigger conditions and thresholds
3. **Specifies** data flow and transformation logic
4. **Implements** hysteresis/filtering to prevent oscillation
5. **Provides** override mechanisms for manual control
6. **Includes** test cases and monitoring instrumentation

Bridges are **implementation-ready**: they contain complete class specifications, method signatures, test cases, and metrics.

---

## Bridge Index

| Bridge | Systems Connected | Purpose | Status |
|--------|-------------------|---------|--------|
| **[FWI_DEFENSE_LEVEL_BRIDGE](FWI_DEFENSE_LEVEL_BRIDGE.md)** | Burnout Fire Index → Defense in Depth | Map multi-temporal danger rating to 5-level safety system | ✅ Complete |
| **[ERLANG_N1_BRIDGE](ERLANG_N1_BRIDGE.md)** | Erlang C Coverage → N-1 Contingency | Convert queuing metrics to redundancy analysis | ✅ Complete |
| **[SEISMIC_SIR_BRIDGE](SEISMIC_SIR_BRIDGE.md)** | STA/LTA Detection → SIR Epidemiology | Link burnout precursor detection to spread modeling | ✅ Complete |
| **[HUB_EPIDEMIOLOGY_BRIDGE](HUB_EPIDEMIOLOGY_BRIDGE.md)** | Network Centrality → SIR Transmission | Hub faculty as burnout super-spreaders | ✅ Complete |
| **[KALMAN_WORKLOAD_BRIDGE](KALMAN_WORKLOAD_BRIDGE.md)** | Kalman Filtering → Workload Prediction | Fuse noisy workload signals for forecasting | ✅ Complete |
| **[CREEP_SPC_BRIDGE](CREEP_SPC_BRIDGE.md)** | Creep/Fatigue → SPC Control Charts | Long-term stress accumulation to process control | ✅ Complete |
| **[NASH_STABILITY_BRIDGE](NASH_STABILITY_BRIDGE.md)** | Nash Equilibrium → Static Stability | Game theory stability to fallback schedules | ✅ Complete |
| **[VOLATILITY_CIRCUIT_BREAKER_BRIDGE](VOLATILITY_CIRCUIT_BREAKER_BRIDGE.md)** | Schedule Volatility → Trading Halts | Financial circuit breakers for schedule chaos | ✅ Complete |

---

## Bridge Architecture

### Design Pattern

All bridges follow a common architecture:

```
┌─────────────────┐
│  Source System  │  (e.g., Burnout Fire Index)
│                 │
│  Outputs:       │
│  - danger_class │
│  - fwi_score    │
│  - components   │
└────────┬────────┘
         │
         v
┌─────────────────────────────────────────┐
│         BRIDGE SPECIFICATION             │
│                                          │
│  1. Mapping Table                       │
│     Source → Target                     │
│                                          │
│  2. Transformation Logic                │
│     - Thresholds                        │
│     - Scaling                           │
│     - Hysteresis                        │
│                                          │
│  3. Override Mechanism                  │
│     - Manual control                    │
│     - Audit trail                       │
│                                          │
│  4. Monitoring                          │
│     - Metrics                           │
│     - Alerts                            │
└────────┬────────────────────────────────┘
         │
         v
┌─────────────────┐
│  Target System  │  (e.g., Defense in Depth)
│                 │
│  Inputs:        │
│  - defense_level│
│  - context      │
└─────────────────┘
```

### Required Sections

Every bridge specification must include:

1. **Mapping Table**: Source values → Target values
2. **Hysteresis Logic**: Prevent oscillation (if applicable)
3. **Data Flow Diagram**: Visual representation of information flow
4. **Multi-Component Integration**: How sub-components interact (if applicable)
5. **Override Logic**: Manual control and exceptions
6. **Implementation Specification**: Ready-to-code classes and methods
7. **Test Cases**: Unit and integration tests
8. **Monitoring & Alerts**: Prometheus metrics and Grafana dashboards

---

## Common Bridge Patterns

### Pattern 1: Threshold-Based Activation

**Example:** FWI → Defense Level

```python
def map_to_target(source_value: float) -> TargetEnum:
    if source_value < 20:
        return TargetEnum.LEVEL_1
    elif source_value < 40:
        return TargetEnum.LEVEL_2
    # ... etc
```

**Use when:** Source system outputs continuous values, target system uses discrete levels.

### Pattern 2: Hysteresis (Schmitt Trigger)

**Example:** All alert systems

```python
class HysteresisState:
    def apply(self, recommended, current):
        if recommended > current:
            # Escalation: Need N consecutive
            if self.consecutive_count >= ESCALATE_THRESHOLD:
                return recommended
        elif recommended < current:
            # De-escalation: Need M consecutive below (threshold - buffer)
            if value < (threshold - buffer) and self.consecutive_count >= DEESCALATE_THRESHOLD:
                return recommended
        return current
```

**Use when:** Preventing rapid oscillation at thresholds is critical.

### Pattern 3: Multi-Component Voting

**Example:** FWI components (ISI + BUI)

```python
def recommend(fwi_result):
    base_level = map_fwi_score(fwi_result.fwi)

    # Component adjustments
    if fwi_result.isi > HIGH_THRESHOLD:
        base_level += 1  # Escalate for rapid change
    if fwi_result.bui > HIGH_THRESHOLD:
        base_level += 1  # Escalate for sustained burden

    return min(base_level, MAX_LEVEL)
```

**Use when:** Source system has multiple indicators with different meanings.

### Pattern 4: Rate Limiting

**Example:** Alert fatigue prevention

```python
class RateLimitedBridge:
    def __init__(self, min_interval: timedelta):
        self.last_transition = None
        self.min_interval = min_interval

    def can_transition(self) -> bool:
        if self.last_transition is None:
            return True
        elapsed = datetime.now() - self.last_transition
        return elapsed >= self.min_interval
```

**Use when:** Target system can be overwhelmed by rapid updates.

---

## Bridge Development Workflow

### 1. Identify Integration Need

**Question:** Do two systems need to communicate?

Example: "When FWI detects EXTREME danger, should Defense in Depth activate EMERGENCY level?"

### 2. Define Source and Target

**Source System:**
- What outputs are available?
- What are their data types, ranges, meanings?

**Target System:**
- What inputs are required?
- What are valid values/states?

### 3. Design Mapping

Create a table:

| Source Value | Target Value | Rationale |
|--------------|--------------|-----------|
| X < 20 | Level 1 | Normal operations |
| 20 ≤ X < 40 | Level 2 | Elevated monitoring |
| ... | ... | ... |

### 4. Address Edge Cases

- **Oscillation:** Add hysteresis
- **Missing data:** Define fallback behavior
- **Manual override:** Provide escape hatch
- **Rate limiting:** Prevent spam

### 5. Write Specification

Use template from existing bridges:
1. Executive summary
2. Mapping table
3. Hysteresis logic (if needed)
4. Data flow diagram
5. Implementation spec
6. Test cases
7. Monitoring

### 6. Implement

Create bridge class in `backend/app/resilience/bridges/`

### 7. Test

Write comprehensive unit tests in `backend/tests/resilience/bridges/`

### 8. Monitor

Add Prometheus metrics and Grafana dashboard

---

## Bridge Governance

### When to Create a Bridge

✅ **Create a bridge when:**
- Two resilience systems need bidirectional or unidirectional data flow
- Mapping logic is non-trivial (not just `target = source`)
- Multiple teams/disciplines need shared understanding
- Integration will be reused in multiple places

❌ **Don't create a bridge when:**
- Simple pass-through (just use direct function call)
- One-time integration (inline the logic)
- Mapping is obvious (no need for formal spec)

### Versioning

Bridges are versioned separately from source/target systems:

```
FWI_DEFENSE_LEVEL_BRIDGE v1.0
├─ Compatible with: BurnoutFireIndex v2.x
├─ Compatible with: DefenseInDepth v1.x
└─ Breaking change requires: v2.0
```

### Deprecation

To deprecate a bridge:
1. Mark as `[DEPRECATED]` in this README
2. Update source/target systems to use new integration
3. Maintain for 1 release cycle
4. Archive to `docs/architecture/bridges/deprecated/`

---

## Testing Bridges

### Unit Test Requirements

Every bridge must have tests for:

1. **Nominal mapping**: Each source value → correct target value
2. **Boundary conditions**: Thresholds, min/max values
3. **Hysteresis behavior**: Escalation, de-escalation, oscillation prevention
4. **Override logic**: Emergency escalation, level lock, bypass
5. **Edge cases**: Missing data, invalid inputs, expired overrides

### Integration Test Requirements

Test full data flow:

```python
def test_fwi_to_defense_full_flow():
    # 1. Calculate FWI
    fwi_report = burnout_rating.calculate_burnout_danger(...)

    # 2. Bridge processes report
    defense_level = bridge.process_fwi_report(fwi_report)

    # 3. Defense system activates
    assert defense_service.current_level == defense_level
    assert defense_service.active_actions == expected_actions
```

### Load Testing

For high-frequency bridges (updated every 15s):

```python
def test_bridge_performance():
    # Process 1000 FWI reports
    start = time.time()
    for _ in range(1000):
        bridge.process_fwi_report(generate_random_fwi_report())
    elapsed = time.time() - start

    assert elapsed < 1.0  # 1ms per report
```

---

## Monitoring Bridges

### Standard Metrics

All bridges should expose:

```python
# Current state
bridge_source_value = Gauge("bridge_{name}_source_value")
bridge_target_value = Gauge("bridge_{name}_target_value")
bridge_hysteresis_active = Gauge("bridge_{name}_hysteresis_active")

# Transitions
bridge_transitions_total = Counter(
    "bridge_{name}_transitions_total",
    ["from_value", "to_value"]
)

# Overrides
bridge_override_active = Gauge("bridge_{name}_override_active")
bridge_override_applications = Counter(
    "bridge_{name}_override_applications_total",
    ["override_type"]
)
```

### Standard Alerts

```yaml
# Critical: Override active for extended period
- alert: BridgeOverrideStuck
  expr: bridge_{name}_override_active == 1
  for: 24h
  severity: warning

# Warning: Rapid oscillation
- alert: BridgeOscillating
  expr: rate(bridge_{name}_transitions_total[5m]) > 5
  for: 15m
  severity: warning
```

---

## Bridge Catalog

### Tier 1 Bridges (Core Integration)

**FWI → Defense Level**
- Connects: Multi-temporal danger rating to safety system activation
- Update frequency: 15 minutes
- Critical path: Yes

**Erlang C → N-1 Contingency**
- Connects: Queuing coverage to redundancy analysis
- Update frequency: 1 hour
- Critical path: No

### Tier 2 Bridges (Advanced Analytics)

**STA/LTA → SIR Epidemiology**
- Connects: Burnout precursor detection to spread modeling
- Update frequency: Daily
- Critical path: No

**Network Centrality → SIR Transmission**
- Connects: Hub faculty identification to super-spreader analysis
- Update frequency: Weekly
- Critical path: No

### Tier 3 Bridges (Specialized)

**Kalman Filter → Workload Prediction**
**Creep/Fatigue → SPC Charts**
**Nash Equilibrium → Static Stability**
**Volatility → Circuit Breakers**

---

## Future Bridges

### Planned

1. **SPC → Defense Level**: Western Electric rules trigger safety systems
2. **BFI → Sacrifice Hierarchy**: FWI danger class determines load shedding priority
3. **Rt → Containment Zones**: Burnout reproduction number triggers zone isolation
4. **Erlang C → Auto-Scaling**: Queuing delays trigger capacity expansion

### Research

1. **Multi-Bridge Orchestration**: How do bridges interact when multiple activate simultaneously?
2. **Bridge Health Monitoring**: Meta-analysis of bridge performance
3. **Adaptive Thresholds**: Machine learning to tune bridge parameters

---

## References

1. **Cross-Disciplinary Resilience Framework**
   - `docs/architecture/cross-disciplinary-resilience.md`

2. **Individual System Documentation**
   - `backend/app/resilience/burnout_fire_index.py`
   - `backend/app/resilience/defense_in_depth.py`
   - `backend/app/resilience/erlang_coverage.py`
   - `backend/app/resilience/seismic_detection.py`
   - `backend/app/resilience/burnout_epidemiology.py`

3. **Testing Patterns**
   - `backend/tests/resilience/test_fwi_defense_bridge.py`

---

**Maintainers:** Architecture Team
**Last Updated:** 2025-12-26
**Next Review:** 2026-01-26
