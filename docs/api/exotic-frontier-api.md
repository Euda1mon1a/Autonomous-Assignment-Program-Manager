# Exotic Frontier Concepts API Reference

> **Version**: 1.0
> **Created**: 2025-12-29
> **Module Count**: 10 modules, ~21,000 lines

---

## Overview

This document provides API reference for the 10 exotic frontier scheduling modules. These modules extend the resilience framework with concepts from statistical mechanics, quantum physics, topology, neuroscience, ecology, and catastrophe theory.

### Module Locations

| Module | File Path |
|--------|-----------|
| Metastability Detection | `/backend/app/resilience/metastability_detector.py` |
| Metastability Integration | `/backend/app/resilience/metastability_integration.py` |
| Spin Glass Model | `/backend/app/scheduling/spin_glass_model.py` |
| Circadian PRC | `/backend/app/resilience/circadian_model.py` |
| Penrose Process | `/backend/app/scheduling/penrose_efficiency.py` |
| Anderson Localization | `/backend/app/scheduling/anderson_localization.py` |
| Persistent Homology | `/backend/app/analytics/persistent_homology.py` |
| Free Energy Scheduler | `/backend/app/scheduling/free_energy_scheduler.py` |
| Keystone Species | `/backend/app/resilience/keystone_analysis.py` |
| Quantum Zeno Governor | `/backend/app/scheduling/zeno_governor.py` |
| Catastrophe Theory | `/backend/app/resilience/catastrophe_detector.py` |

---

## Quick Start

### Basic Import Pattern

```python
# Resilience modules
from app.resilience import (
    MetastabilityDetector,
    CircadianScheduleAnalyzer,
    KeystoneAnalyzer,
    CatastropheDetector,
)

# Scheduling modules
from app.scheduling import (
    SpinGlassScheduler,
    PenroseEfficiencyExtractor,
    AndersonLocalizer,
    FreeEnergyScheduler,
    ZenoGovernor,
)

# Analytics modules
from app.analytics import PersistentScheduleAnalyzer
```

### Alternative: Import from Specific Modules

```python
from app.resilience.metastability_detector import (
    MetastabilityDetector,
    MetastabilityAnalysis,
    EscapeStrategy,
)
from app.scheduling.spin_glass_model import (
    SpinGlassScheduler,
    SpinConfiguration,
    ReplicaSchedule,
)
from app.analytics.persistent_homology import (
    PersistentScheduleAnalyzer,
    PersistenceDiagram,
    TopologicalFeature,
)
```

---

## 1. Metastability Detection API

Detects when solvers become trapped in local optima and recommends escape strategies.

### Classes

#### `MetastabilityDetector`

```python
class MetastabilityDetector:
    def __init__(
        self,
        plateau_threshold: float = 0.01,     # CV threshold for plateau
        window_size: int = 10,                # Window for rolling stats
        temperature: float = 1.0,             # Boltzmann kT parameter
        min_samples: int = 20                 # Minimum samples for analysis
    )

    def detect_plateau(
        self,
        trajectory: list[float]
    ) -> bool:
        """Detect if solver is in plateau state."""

    def estimate_barrier_height(
        self,
        trajectory: list[float],
        constraint_violations: list[dict]
    ) -> float:
        """Estimate energy barrier from constraint violations."""

    def compute_escape_probability(
        self,
        barrier_height: float
    ) -> float:
        """Boltzmann escape probability: P = exp(-E/kT)."""

    def recommend_escape_strategy(
        self,
        analysis: MetastabilityAnalysis
    ) -> EscapeStrategy:
        """Recommend optimal escape strategy."""

    def analyze_solver_trajectory(
        self,
        trajectory: list[float],
        constraint_violations: list[dict] = None
    ) -> MetastabilityAnalysis:
        """Complete metastability analysis."""
```

#### `MetastabilityAnalysis`

```python
@dataclass
class MetastabilityAnalysis:
    is_metastable: bool                    # Is solver trapped?
    plateau_detected: bool                 # Plateau in objective?
    barrier_height: float                  # Estimated energy barrier
    escape_probability: float              # Boltzmann probability
    recommended_strategy: EscapeStrategy   # Best escape strategy
    trajectory_stats: dict                 # Rolling statistics
    confidence: float                      # Confidence in analysis
```

#### `EscapeStrategy`

```python
class EscapeStrategy(Enum):
    CONTINUE_SEARCH = "continue"          # Low barrier, keep going
    INCREASE_TEMPERATURE = "heat"         # Add randomness
    BASIN_HOPPING = "hop"                 # Jump to new region
    RESTART_NEW_SEED = "restart"          # Fresh start
    ACCEPT_LOCAL_OPTIMUM = "accept"       # Stop optimization
```

### Usage Example

```python
from app.resilience.metastability_detector import MetastabilityDetector

detector = MetastabilityDetector(plateau_threshold=0.01, temperature=1.0)

# Solver objective history
trajectory = [1000, 950, 920, 918, 917, 917, 916, 916, 916, 916, 916]
violations = [{"type": "coverage", "penalty": 50}, {"type": "hours", "penalty": 30}]

analysis = detector.analyze_solver_trajectory(trajectory, violations)

if analysis.is_metastable:
    print(f"Solver trapped! Barrier: {analysis.barrier_height:.2f}")
    print(f"Escape probability: {analysis.escape_probability:.4f}")
    print(f"Recommended: {analysis.recommended_strategy.value}")
```

---

## 2. Spin Glass Model API

Generates diverse near-optimal schedules using frustrated constraint systems.

### Classes

#### `SpinGlassScheduler`

```python
class SpinGlassScheduler:
    def __init__(
        self,
        coupling_matrix: np.ndarray = None,  # J_ij interaction matrix
        temperature: float = 1.0,              # Boltzmann temperature
        num_replicas: int = 10                 # Number of schedule replicas
    )

    def build_coupling_matrix(
        self,
        constraints: list[Constraint],
        num_variables: int
    ) -> np.ndarray:
        """Build J_ij from constraint interactions."""

    def compute_frustration_index(
        self,
        configuration: np.ndarray
    ) -> float:
        """Measure constraint frustration (0=satisfied, 1=frustrated)."""

    def generate_replica_schedules(
        self,
        base_schedule: Schedule,
        num_replicas: int = None
    ) -> list[ReplicaSchedule]:
        """Generate diverse schedules via replica method."""

    def compute_parisi_overlap(
        self,
        schedule_a: Schedule,
        schedule_b: Schedule
    ) -> float:
        """Parisi overlap q = (1/N) Σ s_i^a s_i^b."""

    def sample_ground_states(
        self,
        num_samples: int,
        anneal_steps: int = 1000
    ) -> list[SpinConfiguration]:
        """Simulated annealing for ground state sampling."""
```

#### `ReplicaSchedule`

```python
@dataclass
class ReplicaSchedule:
    schedule: Schedule                     # Generated schedule
    energy: float                          # Hamiltonian energy
    frustration: float                     # Frustration index
    overlap_with_base: float               # Parisi overlap with base
    generation_method: str                 # "annealing", "metropolis", etc.
```

### Usage Example

```python
from app.scheduling.spin_glass_model import SpinGlassScheduler

scheduler = SpinGlassScheduler(temperature=1.0, num_replicas=5)

# Build from constraints
scheduler.build_coupling_matrix(constraints, num_variables=100)

# Generate diverse replicas
replicas = scheduler.generate_replica_schedules(base_schedule)

for replica in replicas:
    print(f"Energy: {replica.energy:.2f}, Overlap: {replica.overlap_with_base:.3f}")

# Check diversity
diversity = 1.0 - np.mean([r.overlap_with_base for r in replicas])
print(f"Schedule diversity: {diversity:.2%}")
```

---

## 3. Circadian Phase Response API

Models resident circadian rhythms and predicts burnout from phase shifts.

### Classes

#### `CircadianScheduleAnalyzer`

```python
class CircadianScheduleAnalyzer:
    def __init__(
        self,
        natural_period: float = 24.1,      # Natural circadian period (hours)
        phase_tolerance: float = 2.0,       # Acceptable phase shift (hours)
        entrainment_strength: float = 0.5   # Coupling to external zeitgebers
    )

    def analyze_shift_schedule(
        self,
        shift_times: list[datetime],
        resident_id: str
    ) -> CircadianAnalysis:
        """Analyze phase response to shift schedule."""

    def predict_phase_shift(
        self,
        light_exposure: list[tuple[datetime, float]],
        current_phase: float
    ) -> float:
        """Predict phase shift from PRC."""

    def compute_burnout_risk(
        self,
        accumulated_phase_debt: float,
        recovery_time: float
    ) -> float:
        """Burnout risk from circadian disruption."""

    def recommend_schedule_adjustment(
        self,
        analysis: CircadianAnalysis
    ) -> list[ScheduleRecommendation]:
        """Recommendations to minimize phase disruption."""
```

#### `CircadianAnalysis`

```python
@dataclass
class CircadianAnalysis:
    current_phase: float                   # Phase relative to midnight
    phase_debt: float                      # Accumulated phase shift
    entrainment_stability: float           # How stable is entrainment?
    burnout_risk: float                    # Risk score (0-1)
    recovery_estimate: timedelta           # Time to recover rhythm
    critical_shifts: list[datetime]        # Most disruptive shifts
```

### Usage Example

```python
from app.resilience.circadian_model import CircadianScheduleAnalyzer
from datetime import datetime

analyzer = CircadianScheduleAnalyzer(phase_tolerance=2.0)

# Night shift schedule
shifts = [
    datetime(2025, 1, 1, 19, 0),   # 7 PM start
    datetime(2025, 1, 2, 19, 0),
    datetime(2025, 1, 3, 19, 0),
]

analysis = analyzer.analyze_shift_schedule(shifts, resident_id="R-001")

print(f"Phase debt: {analysis.phase_debt:.1f} hours")
print(f"Burnout risk: {analysis.burnout_risk:.2%}")
print(f"Recovery time: {analysis.recovery_estimate}")
```

---

## 4. Penrose Process Efficiency API

Extracts efficiency from rotation boundary periods (ergospheres).

### Classes

#### `PenroseEfficiencyExtractor`

```python
class PenroseEfficiencyExtractor:
    def __init__(
        self,
        rotation_boundary_hours: int = 4,   # Ergosphere size
        min_efficiency_gain: float = 0.05   # Minimum gain to report
    )

    def identify_ergosphere_periods(
        self,
        schedule: Schedule,
        rotation_transitions: list[RotationTransition]
    ) -> list[ErgospherePeriod]:
        """Find transition periods with extractable efficiency."""

    def find_negative_energy_swaps(
        self,
        ergosphere: ErgospherePeriod,
        candidates: list[Person]
    ) -> list[NegativeEnergySwap]:
        """Find swaps that benefit both parties (negative energy)."""

    def extract_efficiency(
        self,
        schedule: Schedule,
        swap: NegativeEnergySwap
    ) -> tuple[Schedule, float]:
        """Execute swap and return efficiency gain."""

    def compute_kerr_metric(
        self,
        schedule: Schedule
    ) -> float:
        """Kerr-like metric for schedule rotation."""
```

#### `NegativeEnergySwap`

```python
@dataclass
class NegativeEnergySwap:
    person_a: Person
    person_b: Person
    period: ErgospherePeriod
    gain_a: float                          # Benefit to person A
    gain_b: float                          # Benefit to person B
    net_efficiency: float                  # Total extracted efficiency
```

### Usage Example

```python
from app.scheduling.penrose_efficiency import PenroseEfficiencyExtractor

extractor = PenroseEfficiencyExtractor(rotation_boundary_hours=4)

# Find ergospheres at rotation transitions
ergospheres = extractor.identify_ergosphere_periods(schedule, transitions)

for ergo in ergospheres:
    swaps = extractor.find_negative_energy_swaps(ergo, candidates)
    for swap in swaps:
        if swap.net_efficiency > 0.1:
            print(f"Beneficial swap: {swap.person_a} <-> {swap.person_b}")
            print(f"  Net efficiency gain: {swap.net_efficiency:.2%}")
```

---

## 5. Anderson Localization API

Minimizes update cascade scope through constraint disorder.

### Classes

#### `AndersonLocalizer`

```python
class AndersonLocalizer:
    def __init__(
        self,
        disorder_strength: float = 0.3,    # W parameter
        localization_threshold: float = 0.1 # When to consider localized
    )

    def add_disorder(
        self,
        constraint_matrix: np.ndarray
    ) -> np.ndarray:
        """Add diagonal disorder to constraint coupling."""

    def compute_localization_length(
        self,
        energy: float
    ) -> float:
        """Compute characteristic localization length."""

    def compute_localization_region(
        self,
        change_point: int,
        constraint_graph: nx.Graph
    ) -> set[int]:
        """Find region affected by localized change."""

    def create_microsolver(
        self,
        region: set[int],
        full_constraints: list[Constraint]
    ) -> MicroSolver:
        """Create solver for localized region only."""

    def validate_localization(
        self,
        before: Schedule,
        after: Schedule
    ) -> LocalizationReport:
        """Verify that changes stayed localized."""
```

#### `LocalizationReport`

```python
@dataclass
class LocalizationReport:
    is_localized: bool                     # Did changes stay contained?
    affected_region: set[int]              # What changed
    expected_region: set[int]              # What should have changed
    leakage: float                         # Fraction outside region
    localization_length: float             # Characteristic length
```

### Usage Example

```python
from app.scheduling.anderson_localization import AndersonLocalizer

localizer = AndersonLocalizer(disorder_strength=0.3)

# Add disorder to constraint matrix
disordered_matrix = localizer.add_disorder(constraint_matrix)

# Find localized region for a change
region = localizer.compute_localization_region(change_point=50, constraint_graph=graph)
print(f"Localized region size: {len(region)} (vs full: {len(graph)})")

# Create micro-solver for just this region
micro = localizer.create_microsolver(region, constraints)
partial_solution = micro.solve()

# Verify localization
report = localizer.validate_localization(before_schedule, after_schedule)
print(f"Localized: {report.is_localized}, Leakage: {report.leakage:.2%}")
```

---

## 6. Persistent Homology (TDA) API

Computes topological features of schedules across multiple scales.

### Classes

#### `PersistentScheduleAnalyzer`

```python
class PersistentScheduleAnalyzer:
    def __init__(
        self,
        max_dimension: int = 2,            # Max Betti number dimension
        max_scale: float = 10.0            # Max filtration parameter
    )

    def schedule_to_point_cloud(
        self,
        schedule: Schedule
    ) -> np.ndarray:
        """Convert schedule to point cloud for TDA."""

    def compute_persistence_diagram(
        self,
        point_cloud: np.ndarray
    ) -> PersistenceDiagram:
        """Compute birth-death pairs via Vietoris-Rips."""

    def extract_betti_numbers(
        self,
        diagram: PersistenceDiagram,
        scale: float
    ) -> dict[int, int]:
        """Extract Betti numbers at given scale."""

    def extract_schedule_voids(
        self,
        diagram: PersistenceDiagram
    ) -> list[CoverageVoid]:
        """Identify coverage voids from β₂ features."""

    def extract_schedule_cycles(
        self,
        diagram: PersistenceDiagram
    ) -> list[ScheduleCycle]:
        """Identify scheduling loops from β₁ features."""

    def compute_bottleneck_distance(
        self,
        diagram_a: PersistenceDiagram,
        diagram_b: PersistenceDiagram
    ) -> float:
        """Distance between two schedule topologies."""
```

#### `PersistenceDiagram`

```python
@dataclass
class PersistenceDiagram:
    dimension: int                         # Homology dimension
    birth_death_pairs: list[tuple[float, float]]  # (birth, death) pairs
    betti_curve: np.ndarray               # Betti numbers vs scale
    total_persistence: float              # Sum of lifetimes
```

### Usage Example

```python
from app.analytics.persistent_homology import PersistentScheduleAnalyzer

analyzer = PersistentScheduleAnalyzer(max_dimension=2)

# Convert schedule to point cloud
cloud = analyzer.schedule_to_point_cloud(schedule)

# Compute persistence
diagram = analyzer.compute_persistence_diagram(cloud)

# Extract topological features
betti = analyzer.extract_betti_numbers(diagram, scale=5.0)
print(f"β₀={betti[0]} (clusters), β₁={betti[1]} (loops), β₂={betti[2]} (voids)")

# Find coverage voids
voids = analyzer.extract_schedule_voids(diagram)
for void in voids:
    print(f"Coverage void: {void.location}, persistence: {void.persistence:.2f}")
```

---

## 7. Free Energy Scheduler API

Implements Friston's free energy principle for prediction-driven scheduling.

### Classes

#### `FreeEnergyScheduler`

```python
class FreeEnergyScheduler:
    def __init__(
        self,
        complexity_weight: float = 0.5,    # λ in F = λ·C + A
        learning_rate: float = 0.1,        # For belief updates
        forecast_horizon: int = 14         # Days ahead to predict
    )

    def compute_free_energy(
        self,
        schedule: Schedule,
        forecast: Forecast,
        observations: list[Observation]
    ) -> float:
        """F = complexity + inaccuracy."""

    def compute_complexity(
        self,
        schedule: Schedule,
        prior: Distribution
    ) -> float:
        """KL divergence from prior beliefs."""

    def compute_inaccuracy(
        self,
        schedule: Schedule,
        observations: list[Observation]
    ) -> float:
        """Prediction error vs. observations."""

    def active_inference_step(
        self,
        current_schedule: Schedule,
        observations: list[Observation]
    ) -> tuple[Schedule, Forecast]:
        """One step of active inference."""

    def update_beliefs(
        self,
        prior: Distribution,
        observations: list[Observation]
    ) -> Distribution:
        """Bayesian belief update."""

    def generate_actions(
        self,
        beliefs: Distribution,
        goals: list[Goal]
    ) -> list[ScheduleAction]:
        """Generate actions to minimize expected free energy."""
```

#### `FreeEnergyAnalysis`

```python
@dataclass
class FreeEnergyAnalysis:
    free_energy: float                     # Total F
    complexity: float                      # Divergence from prior
    inaccuracy: float                      # Prediction error
    expected_free_energy: float            # Future F under current policy
    recommended_actions: list[ScheduleAction]  # To minimize F
```

### Usage Example

```python
from app.scheduling.free_energy_scheduler import FreeEnergyScheduler

scheduler = FreeEnergyScheduler(complexity_weight=0.5, forecast_horizon=14)

# Compute current free energy
F = scheduler.compute_free_energy(schedule, forecast, observations)
print(f"Free energy: {F:.2f}")

# Run active inference step
new_schedule, new_forecast = scheduler.active_inference_step(schedule, observations)

# Generate recommended actions
actions = scheduler.generate_actions(beliefs, goals)
for action in actions[:3]:
    print(f"Recommended: {action.type} - reduces F by {action.f_reduction:.2f}")
```

---

## 8. Keystone Species Analysis API

Identifies critical resources with cascade collapse potential.

### Classes

#### `KeystoneAnalyzer`

```python
class KeystoneAnalyzer:
    def __init__(
        self,
        cascade_threshold: float = 0.3,    # Coverage drop to trigger cascade
        uniqueness_weight: float = 0.4     # Weight for skill uniqueness
    )

    def build_dependency_graph(
        self,
        schedule: Schedule,
        resources: list[Resource]
    ) -> nx.DiGraph:
        """Build resource dependency network."""

    def compute_keystoneness_score(
        self,
        resource: Resource,
        graph: nx.DiGraph
    ) -> float:
        """Score combining centrality, uniqueness, cascade depth."""

    def simulate_removal_cascade(
        self,
        resource: Resource,
        schedule: Schedule
    ) -> CascadeSimulation:
        """Simulate what happens if resource is removed."""

    def identify_keystones(
        self,
        resources: list[Resource],
        threshold: float = 0.7
    ) -> list[KeystoneResource]:
        """Find all keystone resources above threshold."""

    def recommend_redundancy(
        self,
        keystones: list[KeystoneResource]
    ) -> list[RedundancyRecommendation]:
        """Recommend backup resources for keystones."""
```

#### `KeystoneResource`

```python
@dataclass
class KeystoneResource:
    resource: Resource
    keystoneness: float                    # 0-1 score
    centrality: float                      # Network centrality
    uniqueness: float                      # Skill uniqueness
    cascade_depth: int                     # How far cascade spreads
    dependent_coverage: float              # Coverage depending on this
```

### Usage Example

```python
from app.resilience.keystone_analysis import KeystoneAnalyzer

analyzer = KeystoneAnalyzer(cascade_threshold=0.3)

# Build dependency graph
graph = analyzer.build_dependency_graph(schedule, resources)

# Find keystones
keystones = analyzer.identify_keystones(resources, threshold=0.7)

for k in keystones[:5]:
    print(f"Keystone: {k.resource.name}")
    print(f"  Score: {k.keystoneness:.2f}")
    print(f"  Cascade depth: {k.cascade_depth}")

# Simulate removal
sim = analyzer.simulate_removal_cascade(keystones[0].resource, schedule)
print(f"Removal impact: {sim.coverage_drop:.2%} coverage loss")

# Get redundancy recommendations
recs = analyzer.recommend_redundancy(keystones)
for rec in recs:
    print(f"Add backup for {rec.keystone.name}: {rec.suggested_backup}")
```

---

## 9. Quantum Zeno Governor API

Prevents over-monitoring from freezing schedule optimization.

### Classes

#### `ZenoGovernor`

```python
class ZenoGovernor:
    def __init__(
        self,
        zeno_threshold: float = 0.8,       # Intervention rate threshold
        decay_rate: float = 0.1,           # How fast interventions decay
        observation_window: int = 24       # Hours to track
    )

    def log_human_intervention(
        self,
        intervention_type: str,
        timestamp: datetime = None
    ) -> None:
        """Log a human intervention event."""

    def compute_intervention_rate(
        self,
        window_hours: int = None
    ) -> float:
        """Compute intervention frequency."""

    def compute_zeno_effect_strength(
        self
    ) -> float:
        """Measure how much Zeno effect is freezing evolution."""

    def is_zeno_frozen(
        self
    ) -> bool:
        """Is schedule evolution frozen by observation?"""

    def compute_local_optima_risk(
        self
    ) -> float:
        """Risk that over-monitoring trapped in local optimum."""

    def recommend_intervention_reduction(
        self
    ) -> ZenoRecommendation:
        """Recommend how to reduce interventions."""
```

#### `ZenoRecommendation`

```python
@dataclass
class ZenoRecommendation:
    current_rate: float                    # Current intervention rate
    target_rate: float                     # Recommended rate
    is_frozen: bool                        # Is evolution frozen?
    recommended_actions: list[str]         # What to do
    cooling_period: timedelta              # How long to wait
```

### Usage Example

```python
from app.scheduling.zeno_governor import ZenoGovernor
from datetime import datetime

governor = ZenoGovernor(zeno_threshold=0.8)

# Log interventions
governor.log_human_intervention("manual_swap", datetime.now())
governor.log_human_intervention("constraint_override", datetime.now())
governor.log_human_intervention("manual_swap", datetime.now())

# Check Zeno effect
if governor.is_zeno_frozen():
    print("WARNING: Schedule evolution is frozen by over-monitoring!")
    rec = governor.recommend_intervention_reduction()
    print(f"Recommendation: {rec.recommended_actions}")
    print(f"Cooling period: {rec.cooling_period}")
```

---

## 10. Catastrophe Theory Detector API

Predicts sudden failures from smooth parameter changes.

### Classes

#### `CatastropheDetector`

```python
class CatastropheDetector:
    def __init__(
        self,
        control_params: list[str] = None,  # Parameters to track
        cusp_threshold: float = 0.2        # Distance to warn
    )

    def map_constraint_space(
        self,
        schedule: Schedule,
        constraints: list[Constraint]
    ) -> ConstraintManifold:
        """Map schedule to catastrophe manifold."""

    def detect_catastrophe_cusp(
        self,
        manifold: ConstraintManifold
    ) -> list[CatastropheCusp]:
        """Find cusp singularities in parameter space."""

    def compute_distance_to_catastrophe(
        self,
        current_state: np.ndarray,
        cusp: CatastropheCusp
    ) -> float:
        """Distance to nearest cusp point."""

    def predict_failure_trajectory(
        self,
        current_state: np.ndarray,
        velocity: np.ndarray
    ) -> FailurePrediction:
        """Predict if current trajectory leads to catastrophe."""

    def identify_bifurcation_points(
        self,
        manifold: ConstraintManifold
    ) -> list[BifurcationPoint]:
        """Find fold, cusp, swallowtail bifurcations."""

    def recommend_safe_trajectory(
        self,
        current_state: np.ndarray,
        goal_state: np.ndarray,
        cusps: list[CatastropheCusp]
    ) -> Trajectory:
        """Path that avoids catastrophe cusps."""
```

#### `CatastropheCusp`

```python
@dataclass
class CatastropheCusp:
    location: np.ndarray                   # Position in parameter space
    type: str                              # "fold", "cusp", "swallowtail"
    control_params: list[str]              # Which params are at cusp
    basin_of_attraction: float             # How far danger extends
    criticality: float                     # How severe is crossing
```

### Usage Example

```python
from app.resilience.catastrophe_detector import CatastropheDetector

detector = CatastropheDetector(control_params=["coverage", "utilization", "hours"])

# Map to manifold
manifold = detector.map_constraint_space(schedule, constraints)

# Find cusps
cusps = detector.detect_catastrophe_cusp(manifold)

for cusp in cusps:
    distance = detector.compute_distance_to_catastrophe(current_state, cusp)
    print(f"Cusp type: {cusp.type}")
    print(f"  Distance: {distance:.3f}")
    print(f"  Critical params: {cusp.control_params}")

# Predict trajectory
prediction = detector.predict_failure_trajectory(current_state, velocity)
if prediction.will_fail:
    print(f"WARNING: Catastrophe predicted in {prediction.time_to_failure}")
    safe_path = detector.recommend_safe_trajectory(current_state, goal, cusps)
```

---

## Integration Patterns

### Combining Modules

```python
# Use metastability with catastrophe theory
if detector.is_near_catastrophe():
    analysis = metastability.analyze_solver_trajectory(trajectory)
    if analysis.is_metastable:
        # Use basin hopping to escape before catastrophe
        strategy = EscapeStrategy.BASIN_HOPPING

# Use keystone analysis with localization
keystones = keystone_analyzer.identify_keystones(resources)
for k in keystones:
    # Ensure changes to keystones stay localized
    region = localizer.compute_localization_region(k.resource.id, graph)
    print(f"Changes to {k.resource} affect {len(region)} variables")

# Use TDA with free energy
topology = tda.compute_persistence_diagram(schedule)
if topology.total_persistence > threshold:
    # High topological complexity -> increase free energy weight
    scheduler.complexity_weight *= 1.2
```

### FastAPI Endpoint Example

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.resilience.catastrophe_detector import CatastropheDetector

router = APIRouter()

class CatastropheAnalysisResponse(BaseModel):
    is_near_catastrophe: bool
    distance: float
    cusp_type: str | None
    recommendation: str

@router.get("/catastrophe-risk/{schedule_id}")
async def analyze_catastrophe_risk(
    schedule_id: str,
    db: Session = Depends(get_db)
) -> CatastropheAnalysisResponse:
    """Analyze catastrophe risk for schedule."""
    schedule = await get_schedule(db, schedule_id)
    detector = CatastropheDetector()

    manifold = detector.map_constraint_space(schedule, constraints)
    cusps = detector.detect_catastrophe_cusp(manifold)

    if cusps:
        nearest = min(cusps, key=lambda c: c.distance_from_current)
        return CatastropheAnalysisResponse(
            is_near_catastrophe=nearest.distance_from_current < 0.2,
            distance=nearest.distance_from_current,
            cusp_type=nearest.type,
            recommendation="Reduce utilization" if nearest.type == "cusp" else "Monitor closely"
        )

    return CatastropheAnalysisResponse(
        is_near_catastrophe=False,
        distance=1.0,
        cusp_type=None,
        recommendation="Schedule is stable"
    )
```

---

## Related Documentation

- [Exotic Frontier Concepts](/docs/architecture/EXOTIC_FRONTIER_CONCEPTS.md) - Detailed concept explanations
- [Cross-Disciplinary Resilience](/docs/architecture/cross-disciplinary-resilience.md) - Framework overview
- [MCP Tools Reference](/docs/api/MCP_TOOLS_REFERENCE.md) - AI agent tools
- [Testing Strategy](/docs/development/testing.md) - Test patterns for exotic modules

---

**Document Version**: 1.0
**Last Updated**: 2025-12-29
