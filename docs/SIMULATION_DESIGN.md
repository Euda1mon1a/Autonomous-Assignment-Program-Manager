***REMOVED*** Resilience Simulation Design

***REMOVED******REMOVED*** Purpose and Overview

The resilience simulation module provides **discrete-event simulation capabilities** to validate assumptions in the scheduling resilience framework through Monte Carlo analysis. Rather than relying on static calculations and theoretical metrics, simulation enables testing system behavior under dynamic conditions with random perturbations, cascading failures, and time-dependent effects.

***REMOVED******REMOVED******REMOVED*** Primary Goals

1. **Validate Tier 4 Research Concepts**: Test theoretical frameworks like minimum viable population and extinction vortex dynamics through simulation
2. **Stress-Test Zone Isolation**: Verify that blast radius containment actually prevents cascade failures under realistic conditions
3. **Quantify N-2 Contingency Resilience**: Measure system survival probability when losing any 2 faculty simultaneously (power grid standard)
4. **Model Burnout Cascades**: Simulate positive feedback loops where workload → burnout → departure → increased workload

***REMOVED******REMOVED******REMOVED*** Relationship to RESILIENCE_FRAMEWORK.md

This simulation module directly supports [RESILIENCE_FRAMEWORK.md](./RESILIENCE_FRAMEWORK.md) Tier 4: Research & Future Consideration:

| Framework Concept | Simulation Validation |
|-------------------|----------------------|
| **N-1/N-2 Contingency** (Tier 1) | N-2 scenario tests all pairwise faculty losses |
| **Blast Radius Isolation** (Tier 2) | Cascade scenario verifies zone containment |
| **Minimum Viable Population** (Tier 4) | Cascade scenario identifies critical faculty thresholds |
| **Extinction Vortex** (Tier 4) | Cascade scenario models self-reinforcing collapse |
| **Homeostasis Feedback** (Tier 2) | Both scenarios test feedback loop stability |

***REMOVED******REMOVED******REMOVED*** Technology Choice: SimPy

**SimPy** (Simulation for Python) is a process-based discrete-event simulation framework that enables modeling complex systems as interacting processes over time.

**Why SimPy:**
- **Discrete-Event Paradigm**: Natural fit for schedule-based events (shifts, failures, recoveries)
- **Process-Based Modeling**: Faculty, zones, and services as independent processes
- **Time-Efficient**: Can simulate months or years in seconds
- **Deterministic Randomness**: Seeded random number generation for reproducible results
- **Pure Python**: No compilation, easy integration with existing codebase

**Optional Dependency:**
SimPy is NOT included in core requirements.txt. Users must explicitly install:
```bash
pip install simpy
```

This keeps the core application lightweight while enabling advanced simulation for research and validation.

---

***REMOVED******REMOVED*** Architecture

***REMOVED******REMOVED******REMOVED*** Module Location

```
backend/app/resilience/simulation/
```

The simulation module lives within the resilience package, parallel to other resilience components like `blast_radius.py`, `contingency.py`, and `hub_analysis.py`.

***REMOVED******REMOVED******REMOVED*** Module Structure

```
simulation/
├── __init__.py              ***REMOVED*** Package exports, SimPy availability check
├── base.py                  ***REMOVED*** SimulationEnvironment, Config, Result base classes
├── events.py                ***REMOVED*** Event type definitions (Faculty, Zone, Cascade events)
├── metrics.py               ***REMOVED*** MetricsCollector, time-series tracking, statistics
├── n2_scenario.py           ***REMOVED*** N-2 contingency validation scenario
└── cascade_scenario.py      ***REMOVED*** Burnout cascade / extinction vortex scenario
```

***REMOVED******REMOVED******REMOVED*** Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     simulation/__init__.py                       │
│  - Checks SimPy availability (raises ImportError if missing)    │
│  - Exports all public API classes and functions                 │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
        ┌───────────────┐  ┌──────────┐  ┌──────────────┐
        │   base.py     │  │events.py │  │ metrics.py   │
        │               │  │          │  │              │
        │ - SimEnv      │  │ - Event  │  │ - Collector  │
        │ - Config      │  │   Types  │  │ - Summary    │
        │ - Result      │  │ - Enums  │  │ - Timeseries │
        └───────────────┘  └──────────┘  └──────────────┘
                    │             │             │
                    └─────────────┼─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
        ┌─────────────────────┐     ┌───────────────────────┐
        │  n2_scenario.py     │     │ cascade_scenario.py   │
        │                     │     │                       │
        │ - N2Config          │     │ - CascadeConfig       │
        │ - N2Result          │     │ - CascadeResult       │
        │ - N2Scenario        │     │ - BurnoutScenario     │
        │   .run()            │     │   .run()              │
        └─────────────────────┘     └───────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Dependency Flow

```
User Code
    │
    ├─> N2ContingencyScenario(...).run()
    │       │
    │       ├─> SimulationEnvironment (base.py)
    │       │       └─> simpy.Environment (with seed)
    │       │
    │       ├─> MetricsCollector (metrics.py)
    │       │       └─> Records events, time-series data
    │       │
    │       └─> Generates FacultyEvent, ZoneEvent (events.py)
    │
    └─> BurnoutCascadeScenario(...).run()
            │
            ├─> SimulationEnvironment (base.py)
            │
            ├─> MetricsCollector (metrics.py)
            │
            └─> Generates CascadeEvent (events.py)
```

---

***REMOVED******REMOVED*** Core Components

***REMOVED******REMOVED******REMOVED*** 1. SimulationEnvironment (`base.py`)

Wrapper around SimPy's `Environment` that provides:
- **Seeded Randomness**: Reproducible simulations via `random.seed()`
- **Clock Management**: Unified time tracking across scenarios
- **Process Registration**: Track all active simulation processes

```python
class SimulationEnvironment:
    """
    Wrapper around SimPy Environment with seeded randomness.

    Attributes:
        env: SimPy environment instance
        seed: Random seed for reproducibility
        clock: Current simulation time
        processes: List of registered simulation processes
    """

    def __init__(self, seed: int = None):
        self.seed = seed or random.randint(0, 2**32 - 1)
        random.seed(self.seed)
        np.random.seed(self.seed)
        self.env = simpy.Environment()
        self.processes = []

    def run(self, until: float):
        """Run simulation until specified time."""
        self.env.run(until=until)

    @property
    def now(self) -> float:
        """Current simulation time."""
        return self.env.now
```

***REMOVED******REMOVED******REMOVED*** 2. Configuration Classes (`base.py`)

Base configuration for all scenarios:

```python
class SimulationConfig(BaseModel):
    """Base configuration for all simulations."""

    seed: Optional[int] = None
    duration_hours: float = 720  ***REMOVED*** Default 1 month
    time_step_hours: float = 1.0

    ***REMOVED*** Logging and debugging
    verbose: bool = False
    collect_timeseries: bool = True
```

Scenarios inherit and extend with scenario-specific parameters.

***REMOVED******REMOVED******REMOVED*** 3. Result Classes (`base.py`)

```python
class SimulationResult(BaseModel):
    """Base result for all simulations."""

    seed: int
    start_time: datetime
    end_time: datetime
    duration_hours: float

    ***REMOVED*** Metrics
    metrics_summary: MetricsSummary
    timeseries: Optional[List[TimeSeriesPoint]] = None

    ***REMOVED*** Status
    completed: bool
    error: Optional[str] = None
```

***REMOVED******REMOVED******REMOVED*** 4. Event System (`events.py`)

Strongly-typed event dataclasses for tracking simulation events:

```python
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

class EventType(str, Enum):
    """Simulation event types."""
    FACULTY_UNAVAILABLE = "faculty_unavailable"
    FACULTY_AVAILABLE = "faculty_available"
    FACULTY_BURNOUT = "faculty_burnout"
    FACULTY_DEPARTURE = "faculty_departure"

    ZONE_DEGRADED = "zone_degraded"
    ZONE_FAILED = "zone_failed"
    ZONE_RECOVERED = "zone_recovered"

    WORKLOAD_SPIKE = "workload_spike"
    CASCADE_STARTED = "cascade_started"
    CASCADE_ACCELERATED = "cascade_accelerated"
    SYSTEM_COLLAPSE = "system_collapse"


class EventSeverity(str, Enum):
    """Event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SimulationEvent:
    """Base event class."""
    timestamp: float  ***REMOVED*** Simulation time
    event_type: EventType
    severity: EventSeverity
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FacultyEvent(SimulationEvent):
    """Faculty-related events."""
    faculty_id: str
    zone_id: Optional[str] = None
    workload_before: Optional[float] = None
    workload_after: Optional[float] = None


@dataclass
class ZoneEvent(SimulationEvent):
    """Zone-related events."""
    zone_id: str
    capacity_before: float
    capacity_after: float
    demand: float
    utilization: float


@dataclass
class CascadeEvent(SimulationEvent):
    """Cascade-specific events."""
    total_faculty: int
    available_faculty: int
    departure_rate: float  ***REMOVED*** Departures per month
    hiring_rate: float  ***REMOVED*** Hires per month
    in_vortex: bool  ***REMOVED*** Whether departure_rate > hiring_rate
```

***REMOVED******REMOVED******REMOVED*** 5. Metrics Collection (`metrics.py`)

```python
class MetricsCollector:
    """
    Collects time-series and aggregate metrics during simulation.

    Records:
    - Events as they occur
    - Time-series snapshots at regular intervals
    - Statistical summaries (min, max, mean, std)
    """

    def __init__(self, time_step: float = 1.0):
        self.time_step = time_step
        self.events: List[SimulationEvent] = []
        self.timeseries: List[TimeSeriesPoint] = []

    def record_event(self, event: SimulationEvent):
        """Add event to log."""
        self.events.append(event)

    def snapshot(self, time: float, state: Dict[str, float]):
        """Record system state at specific time."""
        point = TimeSeriesPoint(
            time=time,
            **state
        )
        self.timeseries.append(point)

    def summarize(self) -> MetricsSummary:
        """Generate statistical summary."""
        ***REMOVED*** Aggregate statistics from timeseries
        ***REMOVED*** Count events by type and severity
        ***REMOVED*** Calculate pass/fail rates
        ...


@dataclass
class TimeSeriesPoint:
    """Single point in time series."""
    time: float
    faculty_available: int
    total_workload: float
    max_zone_utilization: float
    cognitive_load: float


class MetricsSummary(BaseModel):
    """Aggregate statistics from simulation."""

    total_events: int
    critical_events: int

    ***REMOVED*** Faculty metrics
    avg_faculty_available: float
    min_faculty_available: int
    faculty_departures: int

    ***REMOVED*** Workload metrics
    avg_workload: float
    max_workload: float

    ***REMOVED*** Zone metrics
    zone_failures: int
    max_zone_utilization: float
```

---

***REMOVED******REMOVED*** Scenario 1: N-2 Contingency Validation

***REMOVED******REMOVED******REMOVED*** Purpose

Validate that the scheduling system can **survive the simultaneous loss of any 2 faculty members** without critical service failures. This standard comes from power grid reliability (NERC standards) where the grid must withstand N-1 (any single component failure) or N-2 (any two simultaneous failures).

***REMOVED******REMOVED******REMOVED*** Methodology

1. **Enumerate All Pairs**: For a faculty of size N, test all C(N,2) = N×(N-1)/2 combinations
2. **Sampling Option**: For large N, randomly sample K pairs to reduce computational cost
3. **Zone Sufficiency Check**: For each pair removal, verify all zones maintain minimum coverage
4. **Failure Mode Analysis**: When failures occur, classify by zone, time period, and service type

***REMOVED******REMOVED******REMOVED*** Implementation Outline (`n2_scenario.py`)

```python
from itertools import combinations
from typing import List, Optional, Set
from pydantic import BaseModel

class N2ScenarioConfig(BaseModel):
    """Configuration for N-2 contingency validation."""

    ***REMOVED*** Faculty to test
    faculty_ids: List[str]

    ***REMOVED*** Zone and service definitions
    zones: List[Dict[str, Any]]  ***REMOVED*** Zone configs with min_coverage

    ***REMOVED*** Sampling
    iterations: Optional[int] = None  ***REMOVED*** If set, sample this many pairs
    exhaustive: bool = True  ***REMOVED*** Test all pairs if True

    ***REMOVED*** Simulation parameters
    seed: Optional[int] = None
    duration_hours: float = 168  ***REMOVED*** 1 week

    ***REMOVED*** Pass criteria
    min_zone_coverage_pct: float = 0.95  ***REMOVED*** Zone must meet 95% of demand


class N2ScenarioResult(BaseModel):
    """Results from N-2 contingency validation."""

    ***REMOVED*** Overall
    total_pairs_tested: int
    pairs_passed: int
    pairs_failed: int
    pass_rate: float  ***REMOVED*** 0.0 to 1.0

    ***REMOVED*** Failure analysis
    vulnerable_pairs: List[Dict[str, Any]]  ***REMOVED*** Pairs that caused failures
    failure_modes: Dict[str, int]  ***REMOVED*** Zone failures by type

    ***REMOVED*** Most critical faculty
    critical_faculty_ids: List[str]  ***REMOVED*** Faculty whose loss causes most failures

    ***REMOVED*** Detailed results
    pair_results: List[Dict[str, Any]]  ***REMOVED*** Per-pair outcomes


class N2ContingencyScenario:
    """
    Simulate N-2 contingency scenarios to validate resilience.

    For each pair of faculty, simulate their simultaneous unavailability
    and check if the system maintains required zone coverage.
    """

    def __init__(self, config: N2ScenarioConfig):
        self.config = config
        self.env = SimulationEnvironment(seed=config.seed)
        self.metrics = MetricsCollector()

    def run(self) -> N2ScenarioResult:
        """Execute N-2 validation."""

        ***REMOVED*** Generate pairs to test
        pairs = self._generate_pairs()

        results = []
        for pair in pairs:
            result = self._test_pair(pair)
            results.append(result)

        ***REMOVED*** Analyze results
        return self._analyze_results(results)

    def _generate_pairs(self) -> List[Tuple[str, str]]:
        """Generate faculty pairs to test."""
        all_pairs = list(combinations(self.config.faculty_ids, 2))

        if self.config.exhaustive or self.config.iterations is None:
            return all_pairs

        ***REMOVED*** Random sampling
        return random.sample(all_pairs, min(self.config.iterations, len(all_pairs)))

    def _test_pair(self, pair: Tuple[str, str]) -> Dict:
        """Test a single pair removal."""
        faculty_a, faculty_b = pair

        ***REMOVED*** Create simulation with these faculty unavailable
        available_faculty = [
            f for f in self.config.faculty_ids
            if f not in pair
        ]

        ***REMOVED*** Simulate scheduling with reduced faculty
        zone_failures = []
        for zone in self.config.zones:
            coverage = self._calculate_coverage(zone, available_faculty)

            if coverage < self.config.min_zone_coverage_pct:
                zone_failures.append({
                    'zone_id': zone['id'],
                    'coverage': coverage,
                    'required': self.config.min_zone_coverage_pct,
                })

        return {
            'pair': pair,
            'passed': len(zone_failures) == 0,
            'zone_failures': zone_failures,
        }

    def _calculate_coverage(self, zone: Dict, faculty: List[str]) -> float:
        """Calculate zone coverage percentage with given faculty."""
        ***REMOVED*** Integration point with BlastRadiusManager
        ***REMOVED*** Check if faculty can meet zone minimum requirements
        ...

    def _analyze_results(self, results: List[Dict]) -> N2ScenarioResult:
        """Aggregate results and identify patterns."""
        passed = [r for r in results if r['passed']]
        failed = [r for r in results if not r['passed']]

        ***REMOVED*** Find which faculty appear most often in failures
        critical_faculty = self._identify_critical_faculty(failed)

        ***REMOVED*** Classify failure modes by zone
        failure_modes = self._classify_failure_modes(failed)

        return N2ScenarioResult(
            total_pairs_tested=len(results),
            pairs_passed=len(passed),
            pairs_failed=len(failed),
            pass_rate=len(passed) / len(results) if results else 0.0,
            vulnerable_pairs=failed,
            failure_modes=failure_modes,
            critical_faculty_ids=critical_faculty,
            pair_results=results,
        )
```

***REMOVED******REMOVED******REMOVED*** Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **N-2 Pass Rate** | % of faculty pairs whose simultaneous loss is survivable | > 95% |
| **Critical Faculty Count** | Number of faculty whose loss causes >50% of failures | < 20% of total |
| **Worst-Case Coverage** | Minimum zone coverage across all pair removals | > 80% |
| **Failure Mode Distribution** | Which zones/services fail most often | Balanced across zones |

***REMOVED******REMOVED******REMOVED*** Expected Output

```json
{
  "total_pairs_tested": 45,
  "pairs_passed": 42,
  "pairs_failed": 3,
  "pass_rate": 0.933,
  "vulnerable_pairs": [
    {
      "pair": ["faculty_001", "faculty_003"],
      "zone_failures": [
        {"zone_id": "zone_icu", "coverage": 0.75, "required": 0.95}
      ]
    }
  ],
  "failure_modes": {
    "zone_icu": 2,
    "zone_clinic": 1
  },
  "critical_faculty_ids": ["faculty_001", "faculty_003"]
}
```

***REMOVED******REMOVED******REMOVED*** Interpretation

- **Pass Rate 93%**: System survives most N-2 scenarios but has vulnerabilities
- **Critical Faculty**: Identified faculty_001 and faculty_003 as high-centrality nodes (hub vulnerability from Tier 3)
- **Action Items**:
  - Cross-train additional faculty for ICU coverage
  - Consider increasing ICU minimum staffing buffer
  - Monitor faculty_001 and faculty_003 for retention risk

---

***REMOVED******REMOVED*** Scenario 2: Burnout Cascade / Extinction Vortex

***REMOVED******REMOVED******REMOVED*** Purpose

Model the **positive feedback loop** where faculty loss → increased workload → burnout → more departures → system collapse. This implements concepts from:
- **Tier 4**: Minimum Viable Population and Extinction Vortex (ecology)
- **Tier 2**: Homeostasis and Positive Feedback Loops (biology)

***REMOVED******REMOVED******REMOVED*** Key Dynamics

The cascade is driven by a positive feedback loop:

```
Faculty Departure
      ↓
Workload Redistributed to Remaining Faculty
      ↓
Increased Individual Workload
      ↓
Higher Burnout Probability
      ↓
More Departures (Accelerating Rate)
      ↓
... (Loop Continues Until Stabilization or Collapse)
```

***REMOVED******REMOVED******REMOVED*** Mathematical Model

**Departure Probability** increases exponentially with workload:

```
P(departure) = base_rate × e^(k × (workload - threshold))

Where:
- base_rate: Baseline departure probability (e.g., 0.05/month)
- k: Sensitivity parameter (e.g., 2.0)
- workload: Current normalized workload (e.g., 1.2 = 120% capacity)
- threshold: Sustainable workload level (e.g., 0.8 = 80% utilization)
```

**Vortex Detection**: The system enters an "extinction vortex" when:

```
departure_rate > hiring_rate + natural_recovery_rate
```

At this point, faculty loss accelerates faster than replacement, leading to inevitable collapse unless external intervention occurs.

***REMOVED******REMOVED******REMOVED*** Implementation Outline (`cascade_scenario.py`)

```python
from typing import List, Optional
from pydantic import BaseModel
import math

class CascadeConfig(BaseModel):
    """Configuration for burnout cascade simulation."""

    ***REMOVED*** Initial conditions
    initial_faculty_count: int
    initial_demand_hours: float

    ***REMOVED*** Workload parameters
    sustainable_workload: float = 0.8  ***REMOVED*** 80% utilization threshold
    max_workload: float = 1.5  ***REMOVED*** Beyond this, immediate departure

    ***REMOVED*** Departure dynamics
    base_departure_rate: float = 0.05  ***REMOVED*** 5% per month baseline
    departure_sensitivity: float = 2.0  ***REMOVED*** Exponential scaling factor

    ***REMOVED*** Recovery dynamics
    hiring_rate: float = 0.10  ***REMOVED*** Can hire 10% per month (if trying)
    hiring_enabled: bool = True
    recovery_delay_months: float = 3.0  ***REMOVED*** Time to onboard new hire

    ***REMOVED*** Simulation parameters
    seed: Optional[int] = None
    max_simulation_days: int = 365
    time_step_hours: float = 24.0  ***REMOVED*** Daily steps

    ***REMOVED*** Stopping conditions
    collapse_threshold: int = 3  ***REMOVED*** If faculty drops below this, system collapses
    stability_threshold_days: int = 90  ***REMOVED*** If stable for this long, stop


class CascadeResult(BaseModel):
    """Results from burnout cascade simulation."""

    ***REMOVED*** Outcome
    collapsed: bool
    days_to_collapse: Optional[float] = None
    stabilized: bool
    days_to_stabilization: Optional[float] = None

    ***REMOVED*** Faculty dynamics
    final_faculty_count: int
    total_departures: int
    total_hires: int

    ***REMOVED*** Vortex analysis
    entered_vortex: bool
    vortex_entry_day: Optional[float] = None
    max_departure_rate: float  ***REMOVED*** Peak departures per month

    ***REMOVED*** Workload analysis
    max_workload: float
    days_over_threshold: int

    ***REMOVED*** Time series
    faculty_trajectory: List[TimeSeriesPoint]


class BurnoutCascadeScenario:
    """
    Simulate burnout cascade and extinction vortex dynamics.

    Models positive feedback loop where workload increases lead to
    accelerating departures, potentially causing system collapse.
    """

    def __init__(self, config: CascadeConfig):
        self.config = config
        self.env = SimulationEnvironment(seed=config.seed)
        self.metrics = MetricsCollector(time_step=config.time_step_hours)

        ***REMOVED*** State variables
        self.faculty_count = config.initial_faculty_count
        self.departures = []
        self.hires = []
        self.in_vortex = False

    def run(self) -> CascadeResult:
        """Execute cascade simulation."""

        ***REMOVED*** Register processes
        self.env.env.process(self._faculty_dynamics())
        self.env.env.process(self._metrics_collection())

        ***REMOVED*** Run simulation
        max_time = self.config.max_simulation_days * 24  ***REMOVED*** Convert to hours
        self.env.run(until=max_time)

        ***REMOVED*** Analyze results
        return self._analyze_cascade()

    def _faculty_dynamics(self):
        """SimPy process modeling faculty arrivals and departures."""

        while True:
            ***REMOVED*** Calculate current workload
            workload = self._calculate_workload()

            ***REMOVED*** Determine departure probability
            p_departure = self._departure_probability(workload)

            ***REMOVED*** Simulate departures
            for _ in range(self.faculty_count):
                if random.random() < p_departure * self.config.time_step_hours / 720:
                    ***REMOVED*** Faculty member departs
                    self._handle_departure()

            ***REMOVED*** Simulate hiring (if enabled)
            if self.config.hiring_enabled:
                p_hire = self.config.hiring_rate * self.config.time_step_hours / 720
                if random.random() < p_hire:
                    self._schedule_hire()

            ***REMOVED*** Check vortex condition
            self._check_vortex()

            ***REMOVED*** Check collapse
            if self.faculty_count <= self.config.collapse_threshold:
                self._trigger_collapse()
                break

            ***REMOVED*** Wait for next time step
            yield self.env.env.timeout(self.config.time_step_hours)

    def _calculate_workload(self) -> float:
        """Calculate normalized workload per faculty member."""
        capacity = self.faculty_count * self.config.sustainable_workload
        return self.config.initial_demand_hours / capacity if capacity > 0 else float('inf')

    def _departure_probability(self, workload: float) -> float:
        """
        Calculate monthly departure probability based on workload.

        Uses exponential model: P = base × e^(k × (w - threshold))
        """
        if workload >= self.config.max_workload:
            return 1.0  ***REMOVED*** Immediate departure

        excess_workload = max(0, workload - self.config.sustainable_workload)

        probability = (
            self.config.base_departure_rate *
            math.exp(self.config.departure_sensitivity * excess_workload)
        )

        return min(probability, 1.0)

    def _handle_departure(self):
        """Process a faculty departure."""
        self.faculty_count -= 1
        self.departures.append({
            'day': self.env.now / 24,
            'faculty_count_after': self.faculty_count,
            'workload': self._calculate_workload(),
        })

        ***REMOVED*** Record event
        event = FacultyEvent(
            timestamp=self.env.now,
            event_type=EventType.FACULTY_DEPARTURE,
            severity=EventSeverity.ERROR if self.faculty_count < 5 else EventSeverity.WARNING,
            message=f"Faculty departed. Remaining: {self.faculty_count}",
            faculty_id=f"faculty_{len(self.departures)}",
            workload_after=self._calculate_workload(),
        )
        self.metrics.record_event(event)

    def _schedule_hire(self):
        """Schedule a new hire (with delay)."""
        ***REMOVED*** Add future hire after onboarding delay
        arrival_time = self.env.now + (self.config.recovery_delay_months * 30 * 24)
        self.env.env.process(self._process_hire(arrival_time))

    def _process_hire(self, arrival_time: float):
        """SimPy process for delayed hire arrival."""
        yield self.env.env.timeout(arrival_time - self.env.now)

        self.faculty_count += 1
        self.hires.append({
            'day': self.env.now / 24,
            'faculty_count_after': self.faculty_count,
        })

        event = FacultyEvent(
            timestamp=self.env.now,
            event_type=EventType.FACULTY_AVAILABLE,
            severity=EventSeverity.INFO,
            message=f"New hire onboarded. Total: {self.faculty_count}",
            faculty_id=f"hire_{len(self.hires)}",
        )
        self.metrics.record_event(event)

    def _check_vortex(self):
        """Check if system has entered extinction vortex."""
        ***REMOVED*** Calculate recent departure rate (last 30 days)
        recent_days = 30
        recent_departures = [
            d for d in self.departures
            if d['day'] >= (self.env.now / 24 - recent_days)
        ]
        departure_rate = len(recent_departures) / (recent_days / 30)  ***REMOVED*** Per month

        ***REMOVED*** Compare to hiring rate
        if departure_rate > self.config.hiring_rate and not self.in_vortex:
            self.in_vortex = True

            event = CascadeEvent(
                timestamp=self.env.now,
                event_type=EventType.CASCADE_STARTED,
                severity=EventSeverity.CRITICAL,
                message="EXTINCTION VORTEX: Departure rate exceeds hiring rate",
                total_faculty=self.config.initial_faculty_count,
                available_faculty=self.faculty_count,
                departure_rate=departure_rate,
                hiring_rate=self.config.hiring_rate,
                in_vortex=True,
            )
            self.metrics.record_event(event)

    def _trigger_collapse(self):
        """Handle system collapse."""
        event = CascadeEvent(
            timestamp=self.env.now,
            event_type=EventType.SYSTEM_COLLAPSE,
            severity=EventSeverity.CRITICAL,
            message=f"SYSTEM COLLAPSE: Faculty count fell to {self.faculty_count}",
            total_faculty=self.config.initial_faculty_count,
            available_faculty=self.faculty_count,
            departure_rate=0.0,
            hiring_rate=0.0,
            in_vortex=True,
        )
        self.metrics.record_event(event)

    def _metrics_collection(self):
        """SimPy process for periodic metrics snapshots."""
        while True:
            self.metrics.snapshot(
                time=self.env.now,
                state={
                    'faculty_available': self.faculty_count,
                    'total_workload': self._calculate_workload(),
                    'departure_rate': self._recent_departure_rate(),
                }
            )

            yield self.env.env.timeout(self.config.time_step_hours)

    def _recent_departure_rate(self) -> float:
        """Calculate recent departure rate (per month)."""
        recent_days = 30
        recent = [
            d for d in self.departures
            if d['day'] >= (self.env.now / 24 - recent_days)
        ]
        return len(recent) / (recent_days / 30)

    def _analyze_cascade(self) -> CascadeResult:
        """Analyze simulation results."""

        ***REMOVED*** Determine outcome
        collapsed = self.faculty_count <= self.config.collapse_threshold
        collapse_events = [
            e for e in self.metrics.events
            if e.event_type == EventType.SYSTEM_COLLAPSE
        ]
        days_to_collapse = collapse_events[0].timestamp / 24 if collapse_events else None

        ***REMOVED*** Vortex analysis
        vortex_events = [
            e for e in self.metrics.events
            if e.event_type == EventType.CASCADE_STARTED
        ]
        entered_vortex = len(vortex_events) > 0
        vortex_entry_day = vortex_events[0].timestamp / 24 if vortex_events else None

        ***REMOVED*** Calculate max departure rate
        all_rates = [d['workload'] for d in self.departures]
        max_departure_rate = max(all_rates) if all_rates else 0.0

        return CascadeResult(
            collapsed=collapsed,
            days_to_collapse=days_to_collapse,
            stabilized=not collapsed and self.faculty_count > self.config.collapse_threshold,
            days_to_stabilization=None,  ***REMOVED*** TODO: Detect stability
            final_faculty_count=self.faculty_count,
            total_departures=len(self.departures),
            total_hires=len(self.hires),
            entered_vortex=entered_vortex,
            vortex_entry_day=vortex_entry_day,
            max_departure_rate=max_departure_rate,
            max_workload=max([self._calculate_workload()] + [d['workload'] for d in self.departures]),
            days_over_threshold=0,  ***REMOVED*** TODO: Calculate from time series
            faculty_trajectory=self.metrics.timeseries,
        )
```

***REMOVED******REMOVED******REMOVED*** Key Metrics

| Metric | Description | Interpretation |
|--------|-------------|----------------|
| **Collapsed** | Whether system fell below collapse threshold | System failure |
| **Days to Collapse** | Time until failure (if collapsed) | System fragility |
| **Entered Vortex** | Whether departure rate > hiring rate | Point of no return |
| **Vortex Entry Day** | When vortex began | Early warning indicator |
| **Max Departure Rate** | Peak monthly departures | Cascade severity |
| **Final Faculty Count** | Steady-state faculty level | New equilibrium |

***REMOVED******REMOVED******REMOVED*** Expected Output

**Scenario 1: Stable System**
```json
{
  "collapsed": false,
  "stabilized": true,
  "days_to_stabilization": 180,
  "final_faculty_count": 8,
  "total_departures": 2,
  "total_hires": 0,
  "entered_vortex": false,
  "max_departure_rate": 0.08,
  "max_workload": 1.1
}
```

**Scenario 2: Extinction Vortex**
```json
{
  "collapsed": true,
  "days_to_collapse": 120,
  "stabilized": false,
  "final_faculty_count": 2,
  "total_departures": 8,
  "total_hires": 2,
  "entered_vortex": true,
  "vortex_entry_day": 45,
  "max_departure_rate": 0.35,
  "max_workload": 2.3
}
```

***REMOVED******REMOVED******REMOVED*** Interpretation

**Stable System:**
- Initial stress caused 2 departures
- Workload remained below 110% of sustainable
- System stabilized at 8 faculty (80% of original)
- Never entered extinction vortex

**Extinction Vortex:**
- Initial stress triggered first departures on day 10
- Workload exceeded 200% by day 30
- Entered vortex on day 45 (departures > hiring)
- System collapsed on day 120 with only 2 faculty remaining
- **Conclusion**: With initial_faculty=10, minimum viable population is ~8. Below 8, cascade becomes inevitable.

---

***REMOVED******REMOVED*** Integration Points

***REMOVED******REMOVED******REMOVED*** 1. BlastRadiusManager Integration

The simulation module calls `BlastRadiusManager` to validate zone isolation:

```python
from app.resilience.blast_radius import BlastRadiusManager

class N2ContingencyScenario:

    def _calculate_coverage(self, zone: Dict, faculty: List[str]) -> float:
        """Calculate zone coverage using BlastRadiusManager."""

        ***REMOVED*** Create manager with simulated faculty availability
        manager = BlastRadiusManager(zones=[zone], faculty=faculty)

        ***REMOVED*** Check if zone can meet minimum requirements
        analysis = manager.analyze_zone(zone['id'])

        return analysis.coverage_ratio  ***REMOVED*** 0.0 to 1.0
```

***REMOVED******REMOVED******REMOVED*** 2. HubAnalyzer Integration

Use hub centrality scores to identify critical faculty:

```python
from app.resilience.hub_analysis import HubAnalyzer

class N2ContingencyScenario:

    def _identify_critical_faculty(self, failures: List[Dict]) -> List[str]:
        """Use hub analysis to rank faculty criticality."""

        ***REMOVED*** Extract faculty from failure cases
        faculty_in_failures = [f for pair in failures for f in pair['pair']]

        ***REMOVED*** Get hub centrality scores
        analyzer = HubAnalyzer(faculty=self.config.faculty_ids)
        hub_scores = analyzer.calculate_centrality()

        ***REMOVED*** Return faculty sorted by centrality (descending)
        return sorted(
            set(faculty_in_failures),
            key=lambda f: hub_scores.get(f, 0),
            reverse=True
        )
```

***REMOVED******REMOVED******REMOVED*** 3. ResilienceService Reporting

Simulation results integrate into the main resilience service:

```python
from app.resilience.service import ResilienceService

class ResilienceService:

    async def run_n2_validation(self, config: N2ScenarioConfig) -> N2ScenarioResult:
        """Run N-2 validation and store results."""

        scenario = N2ContingencyScenario(config)
        result = scenario.run()

        ***REMOVED*** Store in database
        await self._persist_simulation_result('n2_contingency', result)

        ***REMOVED*** Generate alerts if pass rate < threshold
        if result.pass_rate < 0.95:
            await self._alert_low_n2_resilience(result)

        return result

    async def run_cascade_simulation(self, config: CascadeConfig) -> CascadeResult:
        """Run cascade simulation and identify thresholds."""

        scenario = BurnoutCascadeScenario(config)
        result = scenario.run()

        ***REMOVED*** Store results
        await self._persist_simulation_result('burnout_cascade', result)

        ***REMOVED*** If system collapsed, identify minimum viable population
        if result.collapsed:
            mvp = self._binary_search_mvp(config)
            await self._alert_mvp_threshold(mvp)

        return result

    def _binary_search_mvp(self, config: CascadeConfig) -> int:
        """Find minimum viable population via binary search."""

        low, high = config.collapse_threshold, config.initial_faculty_count

        while low < high:
            mid = (low + high) // 2

            test_config = config.copy(update={'initial_faculty_count': mid})
            scenario = BurnoutCascadeScenario(test_config)
            result = scenario.run()

            if result.collapsed:
                low = mid + 1  ***REMOVED*** Need more faculty
            else:
                high = mid  ***REMOVED*** Can sustain with this level

        return low
```

---

***REMOVED******REMOVED*** Usage Examples

***REMOVED******REMOVED******REMOVED*** Example 1: N-2 Contingency Validation

```python
from app.resilience.simulation import N2ContingencyScenario, N2ScenarioConfig

***REMOVED*** Define faculty and zones
faculty_ids = [f"faculty_{i:03d}" for i in range(1, 11)]  ***REMOVED*** 10 faculty

zones = [
    {
        'id': 'zone_icu',
        'name': 'ICU Coverage',
        'min_coverage': 2,  ***REMOVED*** Need at least 2 faculty
        'services': ['critical_care', 'procedures'],
    },
    {
        'id': 'zone_clinic',
        'name': 'Outpatient Clinic',
        'min_coverage': 3,  ***REMOVED*** Need at least 3 faculty
        'services': ['primary_care', 'consultations'],
    },
]

***REMOVED*** Configure scenario
config = N2ScenarioConfig(
    faculty_ids=faculty_ids,
    zones=zones,
    exhaustive=True,  ***REMOVED*** Test all 45 pairs
    duration_hours=168,  ***REMOVED*** 1 week
    min_zone_coverage_pct=0.95,
    seed=42,  ***REMOVED*** Reproducible results
)

***REMOVED*** Run simulation
scenario = N2ContingencyScenario(config)
result = scenario.run()

***REMOVED*** Analyze results
print(f"N-2 Pass Rate: {result.pass_rate:.1%}")
print(f"Vulnerable Pairs: {len(result.vulnerable_pairs)}")

if result.pass_rate < 0.95:
    print("\nCritical Faculty (hub nodes):")
    for faculty_id in result.critical_faculty_ids:
        print(f"  - {faculty_id}")

    print("\nMost Common Failure Modes:")
    for zone, count in sorted(result.failure_modes.items(), key=lambda x: -x[1]):
        print(f"  - {zone}: {count} failures")
```

**Output:**
```
N-2 Pass Rate: 93.3%
Vulnerable Pairs: 3

Critical Faculty (hub nodes):
  - faculty_001
  - faculty_003

Most Common Failure Modes:
  - zone_icu: 2 failures
  - zone_clinic: 1 failure
```

***REMOVED******REMOVED******REMOVED*** Example 2: Burnout Cascade Simulation

```python
from app.resilience.simulation import BurnoutCascadeScenario, CascadeConfig

***REMOVED*** Configure cascade scenario
config = CascadeConfig(
    initial_faculty_count=10,
    initial_demand_hours=320,  ***REMOVED*** 320 hours of weekly demand

    ***REMOVED*** Workload thresholds
    sustainable_workload=0.8,  ***REMOVED*** 80% utilization is sustainable
    max_workload=1.5,  ***REMOVED*** Above 150%, immediate departure

    ***REMOVED*** Dynamics
    base_departure_rate=0.05,  ***REMOVED*** 5% monthly baseline
    departure_sensitivity=2.0,  ***REMOVED*** Exponential sensitivity
    hiring_rate=0.10,  ***REMOVED*** Can hire 10% per month
    hiring_enabled=True,
    recovery_delay_months=3.0,

    ***REMOVED*** Simulation
    max_simulation_days=365,
    time_step_hours=24.0,  ***REMOVED*** Daily steps
    collapse_threshold=3,
    seed=42,
)

***REMOVED*** Run simulation
scenario = BurnoutCascadeScenario(config)
result = scenario.run()

***REMOVED*** Analyze outcome
if result.collapsed:
    print(f"SYSTEM COLLAPSED on day {result.days_to_collapse:.0f}")
    print(f"Final faculty count: {result.final_faculty_count}")

    if result.entered_vortex:
        print(f"Entered extinction vortex on day {result.vortex_entry_day:.0f}")
        print(f"  → Departures accelerated beyond hiring capacity")
else:
    print(f"System stabilized with {result.final_faculty_count} faculty")
    print(f"Total departures: {result.total_departures}")
    print(f"Total hires: {result.total_hires}")

print(f"\nMax workload: {result.max_workload:.1%}")
print(f"Max departure rate: {result.max_departure_rate:.2f}/month")
```

**Output (Collapse Scenario):**
```
SYSTEM COLLAPSED on day 120
Final faculty count: 2
Entered extinction vortex on day 45
  → Departures accelerated beyond hiring capacity

Max workload: 230.5%
Max departure rate: 0.35/month
```

**Output (Stable Scenario):**
```
System stabilized with 8 faculty
Total departures: 2
Total hires: 0

Max workload: 110.2%
Max departure rate: 0.08/month
```

***REMOVED******REMOVED******REMOVED*** Example 3: Finding Minimum Viable Population

```python
from app.resilience.simulation import BurnoutCascadeScenario, CascadeConfig

def find_minimum_viable_population(base_config: CascadeConfig) -> int:
    """Binary search to find minimum faculty count that avoids collapse."""

    low, high = base_config.collapse_threshold, base_config.initial_faculty_count

    print(f"Searching for MVP between {low} and {high} faculty...")

    while low < high:
        mid = (low + high) // 2

        ***REMOVED*** Test with this faculty count
        config = base_config.copy(update={'initial_faculty_count': mid})
        scenario = BurnoutCascadeScenario(config)
        result = scenario.run()

        print(f"  Testing {mid} faculty: {'COLLAPSED' if result.collapsed else 'STABLE'}")

        if result.collapsed:
            low = mid + 1  ***REMOVED*** Need more faculty
        else:
            high = mid  ***REMOVED*** Can sustain with this level

    return low


***REMOVED*** Find MVP for current demand
config = CascadeConfig(
    initial_faculty_count=10,
    initial_demand_hours=320,
    sustainable_workload=0.8,
    max_simulation_days=180,
    seed=42,
)

mvp = find_minimum_viable_population(config)
print(f"\nMinimum Viable Population: {mvp} faculty")
print(f"Below {mvp} faculty, extinction vortex becomes inevitable")
```

**Output:**
```
Searching for MVP between 3 and 10 faculty...
  Testing 6 faculty: COLLAPSED
  Testing 8 faculty: STABLE
  Testing 7 faculty: COLLAPSED

Minimum Viable Population: 8 faculty
Below 8 faculty, extinction vortex becomes inevitable
```

---

***REMOVED******REMOVED*** Future Scenarios

***REMOVED******REMOVED******REMOVED*** 1. PCS Season Surge Simulation

**Purpose**: Model the annual PCS (Permanent Change of Station) season where multiple faculty depart and arrive simultaneously.

**Key Features:**
- Stochastic departure times (concentrated in summer months)
- Onboarding delay for new arrivals (3-6 months)
- Credential transfer delays (privileges, credentialing)
- Training requirements for new faculty

**Metrics:**
- Coverage gaps during transition period
- Maximum concurrent vacancies
- Time to restore full operational capacity

***REMOVED******REMOVED******REMOVED*** 2. Holiday Skeleton Crew Validation

**Purpose**: Verify system can operate with minimal staffing during holidays when most faculty take leave.

**Key Features:**
- Define "skeleton crew" minimum per service
- Model leave preferences and conflicts
- Test coverage for emergency scenarios during holidays

**Metrics:**
- Minimum viable holiday staffing
- Risk level for various skeleton crew sizes
- Fairness of holiday distribution over time

***REMOVED******REMOVED******REMOVED*** 3. Pandemic Response Modeling

**Purpose**: Simulate response to infectious disease outbreak affecting faculty availability.

**Key Features:**
- Exponential infection spread model (SIR dynamics)
- Quarantine requirements reducing available faculty
- PPE and safety protocol time overhead
- Surge in patient demand

**Metrics:**
- Peak simultaneous faculty unavailability
- Days until operational capacity restored
- Service reduction requirements

***REMOVED******REMOVED******REMOVED*** 4. Hub Removal Impact Analysis

**Purpose**: Simulate targeted removal of high-centrality "hub" faculty to test vulnerability.

**Key Features:**
- Integrate with HubAnalyzer to identify critical nodes
- Simulate sudden vs. planned departures
- Model backfill strategies (internal promotion vs. external hire)

**Metrics:**
- Time to restore capability after hub loss
- Number of services impacted
- Cost of different backfill strategies

---

***REMOVED******REMOVED*** Implementation Roadmap

***REMOVED******REMOVED******REMOVED*** Phase 1: Foundation (Week 1-2)
- [ ] Implement `base.py` with SimulationEnvironment, Config, Result classes
- [ ] Implement `events.py` with all event types and severity levels
- [ ] Implement `metrics.py` with MetricsCollector and time-series tracking
- [ ] Unit tests for core infrastructure

***REMOVED******REMOVED******REMOVED*** Phase 2: N-2 Scenario (Week 3-4)
- [ ] Implement `n2_scenario.py` with exhaustive and sampling modes
- [ ] Integration with BlastRadiusManager for zone coverage calculations
- [ ] Integration with HubAnalyzer for critical faculty identification
- [ ] Comprehensive tests with various faculty/zone configurations

***REMOVED******REMOVED******REMOVED*** Phase 3: Cascade Scenario (Week 5-6)
- [ ] Implement `cascade_scenario.py` with departure dynamics
- [ ] Implement vortex detection logic
- [ ] Add hiring and recovery processes
- [ ] Validate against known collapse scenarios

***REMOVED******REMOVED******REMOVED*** Phase 4: Integration & Reporting (Week 7-8)
- [ ] Integrate scenarios into ResilienceService
- [ ] Database models for simulation results
- [ ] API endpoints for triggering simulations
- [ ] Dashboard visualization for results

***REMOVED******REMOVED******REMOVED*** Phase 5: Advanced Scenarios (Week 9+)
- [ ] PCS season surge simulation
- [ ] Holiday skeleton crew validation
- [ ] Pandemic response modeling
- [ ] Hub removal impact analysis

---

***REMOVED******REMOVED*** Testing Strategy

***REMOVED******REMOVED******REMOVED*** Unit Tests

```python
***REMOVED*** tests/resilience/simulation/test_base.py
def test_simulation_environment_reproducibility():
    """Verify same seed produces same results."""
    env1 = SimulationEnvironment(seed=42)
    env2 = SimulationEnvironment(seed=42)

    ***REMOVED*** Run identical processes
    result1 = run_test_simulation(env1)
    result2 = run_test_simulation(env2)

    assert result1 == result2


***REMOVED*** tests/resilience/simulation/test_n2_scenario.py
def test_n2_scenario_all_pass():
    """Test scenario where all pairs pass."""
    config = N2ScenarioConfig(
        faculty_ids=[f"f{i}" for i in range(10)],
        zones=[{'id': 'z1', 'min_coverage': 2}],
        exhaustive=True,
    )

    scenario = N2ContingencyScenario(config)
    result = scenario.run()

    assert result.pass_rate == 1.0
    assert result.pairs_failed == 0


***REMOVED*** tests/resilience/simulation/test_cascade_scenario.py
def test_cascade_stable_workload():
    """Test that low workload remains stable."""
    config = CascadeConfig(
        initial_faculty_count=10,
        initial_demand_hours=200,  ***REMOVED*** Low demand
        max_simulation_days=180,
    )

    scenario = BurnoutCascadeScenario(config)
    result = scenario.run()

    assert not result.collapsed
    assert not result.entered_vortex
    assert result.final_faculty_count >= 8


def test_cascade_high_workload_collapses():
    """Test that excessive workload causes collapse."""
    config = CascadeConfig(
        initial_faculty_count=5,  ***REMOVED*** Too few
        initial_demand_hours=400,  ***REMOVED*** High demand
        max_simulation_days=180,
    )

    scenario = BurnoutCascadeScenario(config)
    result = scenario.run()

    assert result.collapsed
    assert result.entered_vortex
```

***REMOVED******REMOVED******REMOVED*** Integration Tests

```python
***REMOVED*** tests/integration/test_simulation_integration.py
async def test_n2_with_real_zones(db_session):
    """Test N-2 scenario with actual zone configurations."""

    ***REMOVED*** Load real zone data
    zones = await ZoneRepository.get_all(db_session)
    faculty = await FacultyRepository.get_active(db_session)

    config = N2ScenarioConfig(
        faculty_ids=[f.id for f in faculty],
        zones=[z.to_dict() for z in zones],
        exhaustive=False,
        iterations=100,  ***REMOVED*** Sample 100 pairs
    )

    scenario = N2ContingencyScenario(config)
    result = scenario.run()

    ***REMOVED*** Verify results are meaningful
    assert result.total_pairs_tested == 100
    assert 0.0 <= result.pass_rate <= 1.0

    ***REMOVED*** Store results
    await SimulationResultRepository.create(db_session, result)
```

***REMOVED******REMOVED******REMOVED*** Performance Tests

```python
def test_n2_performance_large_faculty():
    """Verify N-2 simulation completes in reasonable time."""

    config = N2ScenarioConfig(
        faculty_ids=[f"f{i}" for i in range(50)],  ***REMOVED*** 50 faculty = 1225 pairs
        zones=[{'id': f"z{i}", 'min_coverage': 2} for i in range(5)],
        exhaustive=True,
    )

    start = time.time()
    scenario = N2ContingencyScenario(config)
    result = scenario.run()
    duration = time.time() - start

    assert duration < 60  ***REMOVED*** Should complete within 60 seconds
    assert result.total_pairs_tested == 1225


def test_cascade_performance_long_simulation():
    """Verify cascade simulation handles long time periods."""

    config = CascadeConfig(
        initial_faculty_count=10,
        max_simulation_days=1000,  ***REMOVED*** ~3 years
        time_step_hours=24.0,
    )

    start = time.time()
    scenario = BurnoutCascadeScenario(config)
    result = scenario.run()
    duration = time.time() - start

    assert duration < 30  ***REMOVED*** Should complete within 30 seconds
```

---

***REMOVED******REMOVED*** Performance Considerations

***REMOVED******REMOVED******REMOVED*** Simulation Speed

**Target Performance:**
- N-2 Scenario: 100 pairs/second for simple zone checks
- Cascade Scenario: 1 year simulated in < 5 seconds
- Memory: < 500MB for typical scenarios

**Optimization Strategies:**

1. **Vectorization**: Use NumPy for batch calculations
   ```python
   ***REMOVED*** Instead of:
   for faculty in faculty_list:
       workload[faculty] = calculate_workload(faculty)

   ***REMOVED*** Use:
   workloads = np.array([calculate_workload(f) for f in faculty_list])
   ```

2. **Caching**: Cache expensive zone calculations
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=1000)
   def calculate_zone_coverage(zone_id, faculty_tuple):
       ***REMOVED*** Expensive calculation
       ...
   ```

3. **Sampling**: For large N-2 scenarios, use stratified sampling
   ```python
   ***REMOVED*** Sample pairs weighted by faculty centrality
   hub_scores = get_hub_scores(faculty)
   sample_weights = [hub_scores[f1] * hub_scores[f2] for f1, f2 in all_pairs]
   sampled_pairs = random.choices(all_pairs, weights=sample_weights, k=100)
   ```

4. **Parallel Execution**: Run independent simulations in parallel
   ```python
   from concurrent.futures import ProcessPoolExecutor

   with ProcessPoolExecutor(max_workers=4) as executor:
       futures = [executor.submit(run_simulation, config) for config in configs]
       results = [f.result() for f in futures]
   ```

---

***REMOVED******REMOVED*** References

***REMOVED******REMOVED******REMOVED*** Documentation

- [RESILIENCE_FRAMEWORK.md](./RESILIENCE_FRAMEWORK.md) - Overall resilience framework and concept prioritization
- [RESILIENCE_SCHEDULING_INTEGRATION.md](./RESILIENCE_SCHEDULING_INTEGRATION.md) - How resilience integrates with scheduling
- [RESILIENCE_SUGGESTIONS_REVIEW.md](./RESILIENCE_SUGGESTIONS_REVIEW.md) - Gemini's simulation suggestions and review

***REMOVED******REMOVED******REMOVED*** External Resources

- **SimPy Documentation**: [https://simpy.readthedocs.io/](https://simpy.readthedocs.io/)
  - Getting Started: [https://simpy.readthedocs.io/en/latest/simpy_intro/](https://simpy.readthedocs.io/en/latest/simpy_intro/)
  - Process Interaction: [https://simpy.readthedocs.io/en/latest/topical_guides/process_interaction.html](https://simpy.readthedocs.io/en/latest/topical_guides/process_interaction.html)

- **N-2 Contingency Standards**:
  - NERC Reliability Standards: [https://www.nerc.com/pa/Stand/Pages/default.aspx](https://www.nerc.com/pa/Stand/Pages/default.aspx)
  - TPL-001-4: Transmission System Planning Performance Requirements

- **Extinction Vortex / Minimum Viable Population**:
  - Gilpin, M. E., & Soulé, M. E. (1986). "Minimum viable populations: processes of species extinction"
  - Fagan, W. F., & Holmes, E. E. (2006). "Quantifying the extinction vortex"
  - Application to organizations: [https://hbr.org/2011/07/adaptability-the-new-competitive-advantage](https://hbr.org/2011/07/adaptability-the-new-competitive-advantage)

- **Discrete-Event Simulation Best Practices**:
  - Banks, J., et al. (2010). "Discrete-Event System Simulation" (5th Edition)
  - Law, A. M. (2015). "Simulation Modeling and Analysis" (5th Edition)

***REMOVED******REMOVED******REMOVED*** Related Code Modules

- `backend/app/resilience/blast_radius.py` - Zone isolation and blast radius management
- `backend/app/resilience/hub_analysis.py` - Hub vulnerability and centrality analysis
- `backend/app/resilience/contingency.py` - N-1/N-2 contingency planning (static analysis)
- `backend/app/resilience/homeostasis.py` - Feedback loops and homeostasis
- `backend/app/resilience/service.py` - Main resilience service coordinating all modules

---

***REMOVED******REMOVED*** Appendix A: Mathematical Models

***REMOVED******REMOVED******REMOVED*** Departure Probability Function

The exponential departure probability model is based on empirical burnout research:

```
P(departure | workload) = β × exp(κ × max(0, w - w_threshold))

Where:
  β = base_departure_rate (baseline monthly departure probability)
  κ = departure_sensitivity (how quickly probability increases)
  w = current workload (normalized, e.g., 1.0 = 100% of sustainable)
  w_threshold = sustainable_workload (typically 0.8 = 80% utilization)
```

**Interpretation:**
- When `w ≤ w_threshold`: P(departure) = β (baseline)
- When `w = 1.0`: P(departure) = β × exp(κ × 0.2)
- When `w = 1.5`: P(departure) = β × exp(κ × 0.7)

**Example Values:**
- β = 0.05 (5% monthly baseline, ~40% annual turnover)
- κ = 2.0 (exponential sensitivity)
- w_threshold = 0.8

**Resulting Probabilities:**
- 80% workload → 5% monthly departure (baseline)
- 100% workload → 7.5% monthly departure
- 120% workload → 13.5% monthly departure
- 150% workload → 40% monthly departure

***REMOVED******REMOVED******REMOVED*** Vortex Condition

System enters extinction vortex when:

```
d(faculty)/dt < 0  AND  |d(faculty)/dt| > hiring_rate
```

Or equivalently:

```
departure_rate(t) > hiring_rate + natural_recovery_rate
```

This creates a **positive feedback loop** because:
1. Departures reduce faculty count
2. Reduced faculty increases workload for remaining staff
3. Increased workload increases departure probability
4. Higher departure probability accelerates further departures
5. Cycle repeats, accelerating until collapse or external intervention

***REMOVED******REMOVED******REMOVED*** Minimum Viable Population

MVP is the smallest faculty size that avoids extinction vortex under normal conditions:

```
MVP = ceil(demand / (sustainable_workload × (1 - base_departure_rate)))
```

**Example:**
- Demand = 320 hours/week
- Sustainable workload = 0.8 (32 hours/week per faculty)
- Base departure rate = 0.05 (5% monthly)

```
MVP = ceil(320 / (32 × 0.95)) = ceil(10.53) = 11 faculty
```

Below 11 faculty, even baseline departures trigger workload increases that accelerate further departures.

---

***REMOVED******REMOVED*** Appendix B: Visualization Examples

***REMOVED******REMOVED******REMOVED*** N-2 Heatmap

Visualize which faculty pairs are vulnerable:

```python
import matplotlib.pyplot as plt
import seaborn as sns

def plot_n2_heatmap(result: N2ScenarioResult):
    """Create heatmap showing vulnerable faculty pairs."""

    ***REMOVED*** Build matrix
    faculty = result.config.faculty_ids
    n = len(faculty)
    matrix = np.zeros((n, n))

    for failure in result.vulnerable_pairs:
        f1, f2 = failure['pair']
        i1, i2 = faculty.index(f1), faculty.index(f2)
        matrix[i1, i2] = 1
        matrix[i2, i1] = 1

    ***REMOVED*** Plot
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        matrix,
        xticklabels=faculty,
        yticklabels=faculty,
        cmap='Reds',
        cbar_kws={'label': 'Vulnerable Pair'},
    )
    plt.title(f'N-2 Vulnerability Matrix (Pass Rate: {result.pass_rate:.1%})')
    plt.tight_layout()
    plt.savefig('n2_heatmap.png', dpi=150)
```

***REMOVED******REMOVED******REMOVED*** Cascade Trajectory

Plot faculty count over time during cascade:

```python
import matplotlib.pyplot as plt

def plot_cascade_trajectory(result: CascadeResult):
    """Plot faculty count over time with vortex indicator."""

    days = [p.time / 24 for p in result.faculty_trajectory]
    faculty_counts = [p.faculty_available for p in result.faculty_trajectory]

    plt.figure(figsize=(14, 6))
    plt.plot(days, faculty_counts, linewidth=2)

    ***REMOVED*** Mark vortex entry
    if result.entered_vortex:
        plt.axvline(
            result.vortex_entry_day,
            color='red',
            linestyle='--',
            label=f'Vortex Entry (Day {result.vortex_entry_day:.0f})'
        )

    ***REMOVED*** Mark collapse
    if result.collapsed:
        plt.axvline(
            result.days_to_collapse,
            color='black',
            linestyle='--',
            label=f'Collapse (Day {result.days_to_collapse:.0f})'
        )

    plt.axhline(
        result.config.collapse_threshold,
        color='orange',
        linestyle=':',
        label=f'Collapse Threshold ({result.config.collapse_threshold})'
    )

    plt.xlabel('Days')
    plt.ylabel('Faculty Count')
    plt.title('Burnout Cascade Trajectory')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('cascade_trajectory.png', dpi=150)
```

---

***REMOVED******REMOVED*** Conclusion

The simulation module provides a rigorous, quantitative foundation for validating resilience assumptions through discrete-event modeling. By testing system behavior under stress conditions—from N-2 contingencies to extinction vortex dynamics—we can:

1. **Identify Hidden Vulnerabilities**: Static analysis misses time-dependent cascades
2. **Quantify Risk**: Replace qualitative assessments with measurable probabilities
3. **Test Interventions**: Simulate the impact of cross-training, buffer policies, and hiring strategies
4. **Set Evidence-Based Thresholds**: Determine minimum viable population through simulation, not guesswork

The simulation module transforms resilience from theory into testable, falsifiable predictions, enabling data-driven decision-making for critical workforce planning.

---

**Document Version**: 1.0
**Last Updated**: 2025-12-17
**Author**: Claude Code
**Status**: Design Complete, Implementation Pending
