# Transport Dynamics Roadmap (Dissolution Layer Concept)

> **Created:** 2025-12-23
> **Status:** Planning (Not Yet Implemented)
> **Priority:** Future Iteration - Exotic Resilience Enhancement
> **Origin:** Fleeting insight to capture before losing

---

## Executive Summary

This document captures a concept for extending the resilience framework with **advection-diffusion transport modeling** inspired by dissolution layer dynamics in physical chemistry. The core insight: scheduling systems have an analogous "saturation interface" between well-mixed capacity pools and locally-stressed units.

**Key innovation:** Rate-based analysis (how fast work flows) vs current state-based analysis (utilization levels).

---

## Concept Overview

### The Physical Analogy

| Dissolution Concept | Scheduling Analogy |
|---------------------|-------------------|
| Hydration shell around solute | Saturation layer around overloaded units |
| Saturation layer prevents fresh solvent reaching interior | "Stuck" supervisors at 80%+ block availability signals |
| Diffusion-limited dissolution | Work diffuses OUT of overstressed units slower than it arrives IN |
| Mixing speed determines dissolution rate | Inter-unit load transfer speed determines scheduling velocity |
| Péclet Number (advection/diffusion ratio) | Task arrival rate / rebalancing capacity ratio |

### Why This Matters

Current resilience modules detect **states** (utilization at 85%). Transport dynamics would detect **trajectories** (Pe approaching 1.0 = instability imminent). This enables earlier intervention.

---

## Proposed Metrics

### 1. Saturation Gradient (dC/dz)
- Measures workload density differential between stressed units and system average
- High gradient = thick "boundary layer" of stuck assignments
- Low gradient = good mixing (load evenly distributed)

### 2. Péclet Number (Pe)
```
Pe = (task_arrival_rate × characteristic_length) / effective_diffusion_coefficient
```
- Pe < 0.8: System stable, can keep up with arrivals
- 0.8 ≤ Pe < 1.2: Approaching critical, monitor closely
- Pe ≥ 1.2: Unstable, boundary layer thickening

### 3. Effective Diffusion Coefficient (D_eff)
- How fast assignments "diffuse" OUT of overloaded units
- Track velocity of task reassignment/rebalancing
- Compare to velocity of new task arrival

### 4. Boundary Layer Thickness
- Fraction of units in saturation zone (top quartile by utilization)
- >0.4 = risky concentration of stress

### 5. Time-to-Saturation
- Estimated time until next unit saturates completely
- Uses: dU/dt = (arrivals - rebalancing)

---

## Integration with Existing Modules

### Coordination Points

| Existing Module | Integration Strategy |
|-----------------|---------------------|
| `utilization.py` | Derive Pe threshold from queuing theory (80% = Pe 0.8) |
| `stigmergy.py` | Coordinate diffusion coefficient with trail evaporation rate |
| `metrics.py` | Add 4 new Prometheus gauges |
| `tasks.py` | Add transport check to `periodic_health_check` |
| `service.py` | Wire transport alerts into `ResilienceService` |
| `blast_radius.py` | Boundary layer as continuous alternative to discrete zones |

### Potential Conflicts to Resolve

1. **Stigmergy evaporation vs diffusion coefficient**: Both model "flow" of preferences/work
   - Option A: Transport module wraps stigmergy, computes diffusion from trail data
   - Option B: Replace stigmergy's decay with transport-based evaporation
   - **Decision needed**: Avoid two independent flow models

2. **Utilization thresholds**: Static 80% vs dynamic Pe threshold
   - Recommendation: Pe threshold derived from existing queuing theory for consistency

---

## Phased Implementation Plan

### Phase 0: Documentation (Current)
- [x] Capture concept in roadmap document
- [x] Identify integration points
- [ ] Review with team before implementation

### Phase 1: Proof of Concept (Estimated: 1-2 days when ready)
**Goal:** Validate concept with minimal dependencies

**New File:** `backend/app/resilience/transport_models.py`

```python
"""
Transport dynamics and saturation boundary layer metrics.

Applies advection-diffusion concepts to scheduling:
- Saturation Gradient: measure uneven workload distribution
- Péclet Number: ratio of task arrival to rebalancing speed
- Effective Diffusion: how fast work actually flows between units
"""
```

**Core Functions:**
- `saturation_gradient(units_data: list[dict]) -> float`
- `peclet_number(task_arrival_rate, rebalancing_capacity) -> float`
- `critical_saturation_alert(units_data, ...) -> dict`
- `time_to_saturation(current_util, arrival_rate, rebalancing_rate) -> float`

**Dependencies:** NumPy/SciPy only (no new packages)

**Tests:** `backend/tests/resilience/test_transport_models.py`

### Phase 2: Service Integration (Estimated: 2-3 days)
**Goal:** Wire into existing resilience infrastructure

**Changes:**
- `ResilienceService.check_transport_dynamics()` method
- Add to `periodic_health_check` Celery task
- Integration tests with mock data

**Prometheus Metrics:**
```python
saturation_gradient_metric = Gauge("resilience_saturation_gradient", ...)
peclet_number_metric = Gauge("resilience_peclet_number", ...)
boundary_layer_thickness = Gauge("resilience_boundary_layer_thickness", ...)
time_to_saturation_minutes = Gauge("resilience_time_to_saturation_minutes", ...)
```

### Phase 3: Alert Generation (Estimated: 1 day)
**Goal:** Actionable alerts from transport metrics

**Alert Conditions:**
- Pe > 0.8: "WARNING: Pe trending toward unstable"
- Pe > 1.0: "CRITICAL: Task arrival outpacing rebalancing"
- Gradient > 0.2 + Pe > 0.8: "Increase inter-unit communication"
- Thickness > 0.4: "Risk of cascade failure"

### Phase 4: Optional Online Learning (Future)
**Goal:** Self-tuning diffusion parameters

**New Dependency:** `river>=0.11.0` (online ML)

**Feature:** `DynamicDiffusionTuner` class that learns:
- (saturation_gradient, peclet_number, arrival_rate) → optimal_capacity

**Only implement if:** Phase 1-3 prove value in empirical testing

---

## Empirical Testing Strategy

### Module Comparison Framework

This module will participate in the planned **empirical module comparison** framework:

```
┌─────────────────────────────────────────────────────────────┐
│           RESILIENCE MODULE COMPARISON MATRIX               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Existing Modules          │  New Transport Module          │
│  ─────────────────────────│──────────────────────────────  │
│  utilization.py (80%)     │  transport_models.py (Pe)      │
│  spc_monitoring.py        │                                │
│  seismic_detection.py     │                                │
│  burnout_fire_index.py    │                                │
│                                                             │
│  Test Scenarios:                                            │
│  1. Gradual load increase (Pe should warn before 80%)       │
│  2. Sudden spike (compare warning lead times)               │
│  3. Uneven distribution (gradient detection)                │
│  4. Recovery dynamics (how fast Pe returns to stable)       │
│                                                             │
│  Metrics to Compare:                                        │
│  - Warning lead time (hours before critical state)          │
│  - False positive rate                                      │
│  - Specificity (does it identify root cause?)               │
│  - Computational cost                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Test Scenarios

1. **Baseline Comparison**
   - Same historical data → compare alerts from transport vs utilization modules
   - Expected: Transport warns earlier for flow-rate problems

2. **Combination Testing**
   - Transport + SPC (statistical drift + flow rate)
   - Transport + Seismic (precursor signals + flow rate)
   - Transport + Burnout Fire Index (multi-temporal + flow rate)

3. **False Positive Analysis**
   - How often does Pe > 0.8 NOT lead to actual problems?
   - Tune thresholds based on empirical data

### Success Criteria

| Metric | Target |
|--------|--------|
| Warning lead time | ≥2 hours before utilization threshold breach |
| False positive rate | <15% |
| Unique detection | Identifies ≥1 scenario other modules miss |
| Computational overhead | <50ms per health check |

---

## Dependency Analysis

### Minimal (Phase 1)
```
numpy>=1.24.0     # Already installed
scipy>=1.11.0     # Already installed
```

### Optional (Phase 4)
```
river>=0.11.0     # Online ML - only if learning proves valuable
```

### Rejected
```
fipy             # Too heavy for scheduling use case (PDE solver)
pymc             # Bayesian overkill for this application
```

---

## Configuration

### New Config Variables

```python
# backend/app/core/config.py (future addition)

class ResilienceTransportConfig:
    """Transport dynamics configuration."""

    TRANSPORT_ENABLED: bool = True
    PE_WARNING_THRESHOLD: float = 0.8
    PE_CRITICAL_THRESHOLD: float = 1.2
    GRADIENT_WARNING_THRESHOLD: float = 0.15
    BOUNDARY_LAYER_WARNING_THRESHOLD: float = 0.4
    CHARACTERISTIC_LENGTH: float = 1.0  # Org unit distance
```

### Prometheus Dashboard

New Grafana panel: "Transport Dynamics"
- Péclet Number gauge (0-2 scale)
- Saturation Gradient time series
- Boundary Layer Thickness gauge
- Time-to-Saturation countdown

---

## Documentation Updates (When Implemented)

1. **`docs/architecture/cross-disciplinary-resilience.md`**
   - Add new section: "Transport Dynamics (Advection-Diffusion)"
   - Follow existing format (source domain, core concept, application, key classes)

2. **`CLAUDE.md`**
   - Add to "Tier 3+ Cross-Disciplinary Analytics" list
   - Brief description of Péclet number concept

3. **`docs/api/resilience.md`**
   - Document new metrics endpoints (if any)

---

## Open Questions

1. **Unit standardization**: What time unit for arrival/rebalancing rates? (Recommend: per day)
2. **Characteristic length**: How to define "organizational distance" between units?
3. **Stigmergy coordination**: Wrap or replace evaporation model?
4. **Threshold calibration**: Use synthetic data or wait for production data?

---

## References

- Advection-Diffusion Equation: https://en.wikipedia.org/wiki/Advection-diffusion_equation
- Péclet Number: https://en.wikipedia.org/wiki/Péclet_number
- FiPy Documentation: https://www.ctcms.nist.gov/fipy/ (reference only, not using)
- River Online ML: https://riverml.xyz/
- Queuing Theory (M/M/c): https://en.wikipedia.org/wiki/M/M/c_queue

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-23 | 0.1 | Initial roadmap created from review session |

---

*This document captures a conceptual enhancement for future implementation. Do not implement without team review and empirical testing framework in place.*
