***REMOVED*** Advanced Scheduling Architecture

Cross-disciplinary algorithms for robust schedule optimization and anomaly detection.

---

***REMOVED******REMOVED*** Overview

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

***REMOVED******REMOVED*** Module Reference

***REMOVED******REMOVED******REMOVED*** 1. Karma Mechanism

**Location:** `backend/app/services/karma_mechanism.py`

A non-monetary, fair allocation system for repeated swap bidding.

***REMOVED******REMOVED******REMOVED******REMOVED*** Key Concepts

- **Self-contained economy**: Karma circulates among providers without external currency
- **Budget-balanced**: Total karma is conserved across all transactions
- **Fairness**: "If I give in now, I will be rewarded in the future"

***REMOVED******REMOVED******REMOVED******REMOVED*** Core Classes

```python
from app.services.karma_mechanism import KarmaMechanism, KarmaAccount

***REMOVED*** Initialize system
karma = KarmaMechanism(initial_balance=100.0)

***REMOVED*** Provider accounts
karma.create_account('dr_smith')
karma.create_account('dr_jones')

***REMOVED*** Bidding
karma.submit_bid('dr_smith', 'swap_123', bid_amount=30.0)
karma.submit_bid('dr_jones', 'swap_123', bid_amount=45.0)

***REMOVED*** Resolution
winner, amount = karma.resolve_swap('swap_123')
karma.settle('swap_123')  ***REMOVED*** Redistributes karma to losers
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Settlement Formula

```
Winner:  K_new = K_old - bid_amount
Losers:  K_new = K_old + (bid_amount / num_losers)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Fairness Monitoring

```python
gini = karma.get_gini_coefficient()
if karma.should_rebalance(threshold=0.3):
    karma.rebalance(target_gini=0.1)
```

---

***REMOVED******REMOVED******REMOVED*** 2. Artificial Immune System (AIS)

**Location:** `backend/app/resilience/immune_system.py`

Detects schedule anomalies using biological immune system principles.

***REMOVED******REMOVED******REMOVED******REMOVED*** Key Concepts

- **Negative Selection**: Generate detectors that recognize "non-self" (invalid states)
- **Clonal Selection**: Adaptive repair strategies that improve over time
- **No explicit rules**: Learns from examples, not hard-coded validation

***REMOVED******REMOVED******REMOVED******REMOVED*** Algorithm: Real-Valued Negative Selection (RNSA)

```
1. Extract features from valid schedules (Self)
2. Generate random detector candidates (hyperspheres)
3. Remove detectors that match any Self pattern
4. Remaining detectors recognize Non-Self (anomalies)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Usage

```python
from app.resilience.immune_system import ScheduleImmuneSystem

***REMOVED*** Train on valid schedules
immune = ScheduleImmuneSystem(feature_dims=12, detector_count=100)
immune.train(valid_schedules)

***REMOVED*** Monitor
if immune.is_anomaly(new_schedule):
    score = immune.get_anomaly_score(new_schedule)
    report = immune.detect_anomaly(new_schedule)

***REMOVED*** Repair
immune.register_antibody('coverage_fix', repair_fn, affinity_pattern)
result = immune.apply_repair(anomalous_schedule)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Feature Vector (12 dimensions)

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

***REMOVED******REMOVED******REMOVED*** 3. Tensegrity Solver

**Location:** `backend/app/scheduling/tensegrity_solver.py`

Finds globally stable schedule configurations using structural mechanics.

***REMOVED******REMOVED******REMOVED******REMOVED*** Key Concepts

- **Tensegrity**: Structures stabilized by continuous tension and isolated compression
- **Force Density Method**: Linear solve for equilibrium (no iteration)
- **Natural equilibrium = optimal schedule**

***REMOVED******REMOVED******REMOVED******REMOVED*** Model Mapping

| Structural Element | Schedule Equivalent |
|-------------------|---------------------|
| Node | Task/event with timestamp |
| Anchor | Fixed time constraint |
| Tension (cable) | Deadline/preference (pull together) |
| Compression (strut) | Resource limit/gap (push apart) |

***REMOVED******REMOVED******REMOVED******REMOVED*** Core Equation

```
F · x = p

Where:
- F = Force Density Matrix (topology + force magnitudes)
- x = Node positions (timestamps)
- p = External forces (anchor constraints)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Usage

```python
from app.scheduling.tensegrity_solver import TensegritySolver

solver = TensegritySolver()

***REMOVED*** Add nodes (tasks)
solver.add_node('shift_start', position=8.0, is_anchor=True)
solver.add_node('task_a', position=9.0)
solver.add_node('task_b', position=10.0)
solver.add_node('shift_end', position=17.0, is_anchor=True)

***REMOVED*** Add constraints
solver.add_tension_element('shift_start', 'task_a', force_density=1.0)
solver.add_compression_element('task_a', 'task_b', force_density=0.5)
solver.add_tension_element('task_b', 'shift_end', force_density=1.0)

***REMOVED*** Solve
solution = solver.solve()  ***REMOVED*** Returns equilibrium positions
schedule = solver.to_schedule(solution)
```

---

***REMOVED******REMOVED******REMOVED*** 4. Pebble Game (Rigidity Analysis)

**Location:** `backend/app/scheduling/rigidity_analysis.py`

Identifies over-constrained and under-constrained schedule regions.

***REMOVED******REMOVED******REMOVED******REMOVED*** Key Concepts

- **(2,3)-Sparsity**: A graph is rigid if |E| ≤ 2|V| - 3
- **Pebbles**: Represent degrees of freedom (2 per node)
- **Stressed**: Too many constraints (redundant)
- **Flexible**: Too few constraints (under-determined)

***REMOVED******REMOVED******REMOVED******REMOVED*** Algorithm

```
1. Assign 2 pebbles to each node
2. For each edge (constraint):
   - Try to find a pebble from either endpoint
   - If found: edge is "independent"
   - If not found: edge is "redundant" (over-constrained)
3. Count remaining pebbles = degrees of freedom
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Usage

```python
from app.scheduling.rigidity_analysis import ConstraintRigidityAnalyzer

analyzer = ConstraintRigidityAnalyzer()
graph = analyzer.build_constraint_graph(tasks, constraints)
result = analyzer.run_pebble_game(graph)

***REMOVED*** Analysis
rigid_regions = analyzer.identify_rigid_regions()
flexible_regions = analyzer.identify_flexible_regions()
stressed_regions = analyzer.identify_stressed_regions()

***REMOVED*** Recommendations
changes = analyzer.recommend_constraint_changes()
***REMOVED*** Returns: [{'action': 'remove', 'constraint': ...}, ...]
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Interpretation

| Region Type | Meaning | Action |
|-------------|---------|--------|
| Rigid | Fully constrained, stable | No change needed |
| Flexible | Under-constrained | Add constraints |
| Stressed | Over-constrained, conflicting | Remove constraints |

---

***REMOVED******REMOVED******REMOVED*** 5. Burnout Contagion Model

**Location:** `backend/app/resilience/contagion_model.py`

Models burnout spread through provider social networks using epidemiology.

***REMOVED******REMOVED******REMOVED******REMOVED*** Key Concepts

- **SIS Model**: Susceptible → Infected → Susceptible (burnout can recur)
- **Superspreaders**: High-centrality nodes with high burnout
- **Network interventions**: Edge removal, quarantine, buffer pairing

***REMOVED******REMOVED******REMOVED******REMOVED*** Usage

```python
from app.resilience.contagion_model import BurnoutContagionModel

***REMOVED*** Initialize with social network
model = BurnoutContagionModel(provider_network)
model.configure(infection_rate=0.05, recovery_rate=0.01)

***REMOVED*** Set initial burnout states
model.set_initial_burnout(provider_ids, burnout_scores)

***REMOVED*** Simulate
results = model.simulate(iterations=50)

***REMOVED*** Analysis
superspreaders = model.identify_superspreaders()
interventions = model.recommend_interventions()
report = model.generate_report()
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Intervention Types

| Intervention | Description | Cost |
|--------------|-------------|------|
| Workload reduction | Decrease hours for superspreader | Medium |
| Edge removal | Separate high-burnout collaborators | Low |
| Quarantine | Isolate extreme cases (>85% burnout) | High |
| Buffer pairing | Pair with high-resilience provider | Low |

---

***REMOVED******REMOVED******REMOVED*** 6. Equity Metrics (Gini Coefficient)

**Location:** `backend/app/resilience/equity_metrics.py`

Measures workload fairness using inequality statistics.

***REMOVED******REMOVED******REMOVED******REMOVED*** Key Concepts

- **Gini coefficient**: 0 = perfect equality, 1 = perfect inequality
- **Lorenz curve**: Visual representation of distribution
- **Target for medical scheduling**: G < 0.15

***REMOVED******REMOVED******REMOVED******REMOVED*** Formula

```
G = (Σᵢ Σⱼ |xᵢ - xⱼ|) / (2n² × μ)

Where:
- xᵢ, xⱼ = individual values (hours)
- n = number of providers
- μ = mean value
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Usage

```python
from app.resilience.equity_metrics import (
    gini_coefficient,
    lorenz_curve,
    equity_report
)

***REMOVED*** Basic calculation
gini = gini_coefficient(provider_hours)

***REMOVED*** With intensity weighting
weighted_gini = gini_coefficient(hours, weights=intensity_factors)

***REMOVED*** Comprehensive report
report = equity_report(
    provider_hours={'dr_a': 45, 'dr_b': 38, 'dr_c': 52},
    intensity_weights={'dr_a': 1.2, 'dr_b': 1.0, 'dr_c': 1.5}
)

print(report['gini'])           ***REMOVED*** 0.12
print(report['is_equitable'])   ***REMOVED*** True (< 0.15 threshold)
print(report['recommendations']) ***REMOVED*** ['Reduce dr_c hours by 5']
```

---

***REMOVED******REMOVED*** Integration Points

***REMOVED******REMOVED******REMOVED*** With Existing Scheduling Engine

```python
***REMOVED*** backend/app/scheduling/engine.py integration

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

***REMOVED******REMOVED******REMOVED*** With Resilience Service

```python
***REMOVED*** backend/app/resilience/service.py integration

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

        ***REMOVED*** AIS anomaly detection
        if self.immune_system.is_anomaly(schedule):
            results['anomaly'] = self.immune_system.detect_anomaly(schedule)

        ***REMOVED*** Equity check
        results['equity'] = equity_report(schedule.provider_hours)

        return results
```

***REMOVED******REMOVED******REMOVED*** With Swap Management

```python
***REMOVED*** backend/app/services/swap_executor.py integration

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

***REMOVED******REMOVED*** Dependencies

Added to `requirements.txt`:

```txt
scipy>=1.11.0      ***REMOVED*** Sparse matrix operations for tensegrity solver
ndlib>=5.1.0       ***REMOVED*** Network diffusion for burnout contagion
```

---

***REMOVED******REMOVED*** References

***REMOVED******REMOVED******REMOVED*** Academic Papers

1. **Karma Mechanism**: Elokda et al., "A Self-Contained Karma Economy for Dynamic Allocation" (2023)
2. **Negative Selection**: Forrest et al., "Self-Nonself Discrimination in a Computer" (1994)
3. **Pebble Game**: Jacobs & Hendrickson, "An Algorithm for Two-Dimensional Rigidity Percolation" (1997)
4. **Force Density**: Schek, "The Force Density Method for Form Finding" (1974)
5. **Network Diffusion**: Rossetti et al., "NDlib: A Python Library for Network Diffusion" (2018)

***REMOVED******REMOVED******REMOVED*** Related Documentation

- [Resilience Framework](resilience.md) - Core resilience concepts
- [Scheduling Workflow](../guides/scheduling-workflow.md) - Basic scheduling guide
- [Swap Management](../guides/swap-management.md) - Swap system guide
- [Libraries Research](../research/scheduling-libs-research.md) - Full library evaluation
