# Advanced Scheduling Architecture

Cross-disciplinary algorithms for robust schedule optimization and anomaly detection.

---

## Overview

The Residency Scheduler incorporates advanced algorithms from multiple disciplines:

| Layer | Domain | Purpose |
|-------|--------|---------|
| **Economic** | Game Theory | Fair resource allocation via Karma mechanism |
| **Immunological** | AIS | Anomaly detection without explicit rules |
| **Physics** | Structural Mechanics | Schedule stability via tensegrity equilibrium |
| **Graph Theory** | Rigidity Analysis | Constraint system health via pebble game |
| **Epidemiology** | Network Diffusion | Burnout contagion modeling |
| **Statistics** | Inequality Metrics | Workload fairness via Gini coefficient |

---

## Module Reference

### 1. Karma Mechanism

**Location:** `backend/app/services/karma_mechanism.py`

A non-monetary, fair allocation system for repeated swap bidding.

#### Key Concepts

- **Self-contained economy**: Karma circulates among providers without external currency
- **Budget-balanced**: Total karma is conserved across all transactions
- **Fairness**: "If I give in now, I will be rewarded in the future"

#### Core Classes

```python
from app.services.karma_mechanism import KarmaMechanism, KarmaAccount

# Initialize system
karma = KarmaMechanism(initial_balance=100.0)

# Provider accounts
karma.create_account('dr_smith')
karma.create_account('dr_jones')

# Bidding
karma.submit_bid('dr_smith', 'swap_123', bid_amount=30.0)
karma.submit_bid('dr_jones', 'swap_123', bid_amount=45.0)

# Resolution
winner, amount = karma.resolve_swap('swap_123')
karma.settle('swap_123')  # Redistributes karma to losers
```

#### Settlement Formula

```
Winner:  K_new = K_old - bid_amount
Losers:  K_new = K_old + (bid_amount / num_losers)
```

#### Fairness Monitoring

```python
gini = karma.get_gini_coefficient()
if karma.should_rebalance(threshold=0.3):
    karma.rebalance(target_gini=0.1)
```

---

### 2. Artificial Immune System (AIS)

**Location:** `backend/app/resilience/immune_system.py`

Detects schedule anomalies using biological immune system principles.

#### Key Concepts

- **Negative Selection**: Generate detectors that recognize "non-self" (invalid states)
- **Clonal Selection**: Adaptive repair strategies that improve over time
- **No explicit rules**: Learns from examples, not hard-coded validation

#### Algorithm: Real-Valued Negative Selection (RNSA)

```
1. Extract features from valid schedules (Self)
2. Generate random detector candidates (hyperspheres)
3. Remove detectors that match any Self pattern
4. Remaining detectors recognize Non-Self (anomalies)
```

#### Usage

```python
from app.resilience.immune_system import ScheduleImmuneSystem

# Train on valid schedules
immune = ScheduleImmuneSystem(feature_dims=12, detector_count=100)
immune.train(valid_schedules)

# Monitor
if immune.is_anomaly(new_schedule):
    score = immune.get_anomaly_score(new_schedule)
    report = immune.detect_anomaly(new_schedule)

# Repair
immune.register_antibody('coverage_fix', repair_fn, affinity_pattern)
result = immune.apply_repair(anomalous_schedule)
```

#### Feature Vector (12 dimensions)

| Index | Feature | Description |
|-------|---------|-------------|
| 0 | coverage_ratio | Overall slot coverage |
| 1-3 | type_coverage | Clinic, inpatient, procedure |
| 4-5 | acgme_compliance | Violation rate, hours compliance |
| 6-7 | supervision | Ratio, faculty availability |
| 8 | workload_balance | Standard deviation of hours |
| 9 | schedule_stability | Change rate |
| 10-11 | reserved | Future use |

---

### 3. Tensegrity Solver

**Location:** `backend/app/scheduling/tensegrity_solver.py`

Finds globally stable schedule configurations using structural mechanics.

#### Key Concepts

- **Tensegrity**: Structures stabilized by continuous tension and isolated compression
- **Force Density Method**: Linear solve for equilibrium (no iteration)
- **Natural equilibrium = optimal schedule**

#### Model Mapping

| Structural Element | Schedule Equivalent |
|-------------------|---------------------|
| Node | Task/event with timestamp |
| Anchor | Fixed time constraint |
| Tension (cable) | Deadline/preference (pull together) |
| Compression (strut) | Resource limit/gap (push apart) |

#### Core Equation

```
F · x = p

Where:
- F = Force Density Matrix (topology + force magnitudes)
- x = Node positions (timestamps)
- p = External forces (anchor constraints)
```

#### Usage

```python
from app.scheduling.tensegrity_solver import TensegritySolver

solver = TensegritySolver()

# Add nodes (tasks)
solver.add_node('shift_start', position=8.0, is_anchor=True)
solver.add_node('task_a', position=9.0)
solver.add_node('task_b', position=10.0)
solver.add_node('shift_end', position=17.0, is_anchor=True)

# Add constraints
solver.add_tension_element('shift_start', 'task_a', force_density=1.0)
solver.add_compression_element('task_a', 'task_b', force_density=0.5)
solver.add_tension_element('task_b', 'shift_end', force_density=1.0)

# Solve
solution = solver.solve()  # Returns equilibrium positions
schedule = solver.to_schedule(solution)
```

---

### 4. Pebble Game (Rigidity Analysis)

**Location:** `backend/app/scheduling/rigidity_analysis.py`

Identifies over-constrained and under-constrained schedule regions.

#### Key Concepts

- **(2,3)-Sparsity**: A graph is rigid if |E| ≤ 2|V| - 3
- **Pebbles**: Represent degrees of freedom (2 per node)
- **Stressed**: Too many constraints (redundant)
- **Flexible**: Too few constraints (under-determined)

#### Algorithm

```
1. Assign 2 pebbles to each node
2. For each edge (constraint):
   - Try to find a pebble from either endpoint
   - If found: edge is "independent"
   - If not found: edge is "redundant" (over-constrained)
3. Count remaining pebbles = degrees of freedom
```

#### Usage

```python
from app.scheduling.rigidity_analysis import ConstraintRigidityAnalyzer

analyzer = ConstraintRigidityAnalyzer()
graph = analyzer.build_constraint_graph(tasks, constraints)
result = analyzer.run_pebble_game(graph)

# Analysis
rigid_regions = analyzer.identify_rigid_regions()
flexible_regions = analyzer.identify_flexible_regions()
stressed_regions = analyzer.identify_stressed_regions()

# Recommendations
changes = analyzer.recommend_constraint_changes()
# Returns: [{'action': 'remove', 'constraint': ...}, ...]
```

#### Interpretation

| Region Type | Meaning | Action |
|-------------|---------|--------|
| Rigid | Fully constrained, stable | No change needed |
| Flexible | Under-constrained | Add constraints |
| Stressed | Over-constrained, conflicting | Remove constraints |

---

### 5. Burnout Contagion Model

**Location:** `backend/app/resilience/contagion_model.py`

Models burnout spread through provider social networks using epidemiology.

#### Key Concepts

- **SIS Model**: Susceptible → Infected → Susceptible (burnout can recur)
- **Superspreaders**: High-centrality nodes with high burnout
- **Network interventions**: Edge removal, quarantine, buffer pairing

#### Usage

```python
from app.resilience.contagion_model import BurnoutContagionModel

# Initialize with social network
model = BurnoutContagionModel(provider_network)
model.configure(infection_rate=0.05, recovery_rate=0.01)

# Set initial burnout states
model.set_initial_burnout(provider_ids, burnout_scores)

# Simulate
results = model.simulate(iterations=50)

# Analysis
superspreaders = model.identify_superspreaders()
interventions = model.recommend_interventions()
report = model.generate_report()
```

#### Intervention Types

| Intervention | Description | Cost |
|--------------|-------------|------|
| Workload reduction | Decrease hours for superspreader | Medium |
| Edge removal | Separate high-burnout collaborators | Low |
| Quarantine | Isolate extreme cases (>85% burnout) | High |
| Buffer pairing | Pair with high-resilience provider | Low |

---

### 6. Equity Metrics (Gini Coefficient)

**Location:** `backend/app/resilience/equity_metrics.py`

Measures workload fairness using inequality statistics.

#### Key Concepts

- **Gini coefficient**: 0 = perfect equality, 1 = perfect inequality
- **Lorenz curve**: Visual representation of distribution
- **Target for medical scheduling**: G < 0.15

#### Formula

```
G = (Σᵢ Σⱼ |xᵢ - xⱼ|) / (2n² × μ)

Where:
- xᵢ, xⱼ = individual values (hours)
- n = number of providers
- μ = mean value
```

#### Usage

```python
from app.resilience.equity_metrics import (
    gini_coefficient,
    lorenz_curve,
    equity_report
)

# Basic calculation
gini = gini_coefficient(provider_hours)

# With intensity weighting
weighted_gini = gini_coefficient(hours, weights=intensity_factors)

# Comprehensive report
report = equity_report(
    provider_hours={'dr_a': 45, 'dr_b': 38, 'dr_c': 52},
    intensity_weights={'dr_a': 1.2, 'dr_b': 1.0, 'dr_c': 1.5}
)

print(report['gini'])           # 0.12
print(report['is_equitable'])   # True (< 0.15 threshold)
print(report['recommendations']) # ['Reduce dr_c hours by 5']
```

---

## Integration Points

### With Existing Scheduling Engine

```python
# backend/app/scheduling/engine.py integration

from app.scheduling.rigidity_analysis import ConstraintRigidityAnalyzer
from app.scheduling.tensegrity_solver import TensegritySolver

class SchedulingEngine:
    def validate_constraints(self):
        """Check constraint system health before solving."""
        analyzer = ConstraintRigidityAnalyzer()
        graph = analyzer.build_constraint_graph(self.tasks, self.constraints)

        stressed = analyzer.identify_stressed_regions()
        if stressed:
            logger.warning(f"Over-constrained regions: {stressed}")
            return analyzer.recommend_constraint_changes()
```

### With Resilience Service

```python
# backend/app/resilience/service.py integration

from app.resilience.immune_system import ScheduleImmuneSystem
from app.resilience.contagion_model import BurnoutContagionModel
from app.resilience.equity_metrics import equity_report

class ResilienceService:
    def __init__(self):
        self.immune_system = ScheduleImmuneSystem()
        self.contagion_model = None

    def check_schedule_health(self, schedule):
        """Multi-layer health check."""
        results = {}

        # AIS anomaly detection
        if self.immune_system.is_anomaly(schedule):
            results['anomaly'] = self.immune_system.detect_anomaly(schedule)

        # Equity check
        results['equity'] = equity_report(schedule.provider_hours)

        return results
```

### With Swap Management

```python
# backend/app/services/swap_executor.py integration

from app.services.karma_mechanism import KarmaMechanism

class SwapExecutor:
    def __init__(self):
        self.karma = KarmaMechanism()

    def process_competitive_swap(self, swap_request):
        """Handle swap with multiple interested parties."""
        for provider_id, bid in swap_request.bids.items():
            self.karma.submit_bid(provider_id, swap_request.id, bid)

        winner, amount = self.karma.resolve_swap(swap_request.id)
        self.karma.settle(swap_request.id)

        return winner
```

---

## Dependencies

Added to `requirements.txt`:

```txt
scipy>=1.11.0      # Sparse matrix operations for tensegrity solver
ndlib>=5.1.0       # Network diffusion for burnout contagion
```

---

## References

### Academic Papers

1. **Karma Mechanism**: Elokda et al., "A Self-Contained Karma Economy for Dynamic Allocation" (2023)
2. **Negative Selection**: Forrest et al., "Self-Nonself Discrimination in a Computer" (1994)
3. **Pebble Game**: Jacobs & Hendrickson, "An Algorithm for Two-Dimensional Rigidity Percolation" (1997)
4. **Force Density**: Schek, "The Force Density Method for Form Finding" (1974)
5. **Network Diffusion**: Rossetti et al., "NDlib: A Python Library for Network Diffusion" (2018)

### Related Documentation

- [Resilience Framework](resilience.md) - Core resilience concepts
- [Scheduling Workflow](../guides/scheduling-workflow.md) - Basic scheduling guide
- [Swap Management](../guides/swap-management.md) - Swap system guide
- [Libraries Research](../research/scheduling-libs-research.md) - Full library evaluation
