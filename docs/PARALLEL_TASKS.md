# Parallel Implementation Tasks

**Purpose:** 10 independent tasks for parallel execution across terminals.
**Guarantee:** Each task creates/modifies a UNIQUE file - zero interference possible.

---

## Task Overview

| # | File | Description | Est. Lines |
|---|------|-------------|------------|
| 1 | `simulation/__init__.py` | Package exports | ~50 |
| 2 | `simulation/base.py` | Base simulation environment | ~200 |
| 3 | `simulation/events.py` | Event type definitions | ~150 |
| 4 | `simulation/metrics.py` | Metrics collection & stats | ~200 |
| 5 | `simulation/n2_scenario.py` | N-2 contingency scenario | ~250 |
| 6 | `simulation/cascade_scenario.py` | Burnout cascade scenario | ~250 |
| 7 | `tests/test_resilience_blast_radius.py` | Blast radius unit tests | ~300 |
| 8 | `tests/test_resilience_hub_analysis.py` | Hub analysis unit tests | ~300 |
| 9 | `docs/SIMULATION_DESIGN.md` | Simulation architecture doc | ~200 |
| 10 | `docs/SKILL_ZONES_DESIGN.md` | Skill-based zones design | ~150 |

---

## Task 1: Simulation Package Init

**File:** `backend/app/resilience/simulation/__init__.py`

**Requirements:**
- Create package initialization
- Export all public classes from submodules (use forward references/comments for now)
- Include package docstring explaining SimPy-based simulation purpose
- Define `__all__` list

**Acceptance Criteria:**
```python
# Must contain:
- Package docstring
- __all__ = [...] with expected exports
- Placeholder imports (commented) for integration later
```

**No dependencies on other parallel tasks.**

---

## Task 2: Base Simulation Environment

**File:** `backend/app/resilience/simulation/base.py`

**Requirements:**
- Create `SimulationEnvironment` class wrapping SimPy env
- Create `SimulationConfig` dataclass for parameters
- Create `SimulationResult` dataclass for outputs
- Include abstract base for scenarios
- Handle case where simpy not installed (optional dependency)

**Skeleton:**
```python
"""Base simulation environment for resilience testing."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID
import logging

# SimPy is optional
try:
    import simpy
    HAS_SIMPY = True
except ImportError:
    HAS_SIMPY = False

logger = logging.getLogger(__name__)

@dataclass
class SimulationConfig:
    """Configuration for a simulation run."""
    seed: int = 42
    duration_days: int = 365
    time_step_hours: float = 1.0
    ***REMOVED*** parameters
    initial_faculty_count: int = 10
    minimum_viable_count: int = 3
    # Event probabilities (per day)
    sick_call_probability: float = 0.02
    resignation_base_probability: float = 0.001
    # ... more config

@dataclass
class SimulationResult:
    """Results from a simulation run."""
    config: SimulationConfig
    started_at: datetime
    completed_at: datetime
    # Outcomes
    final_faculty_count: int
    coverage_maintained: bool
    days_until_failure: int | None
    cascade_events: int
    # Statistics
    metrics: dict = field(default_factory=dict)

class SimulationScenario(Protocol):
    """Protocol for simulation scenarios."""
    def setup(self, env: "SimulationEnvironment") -> None: ...
    def run(self) -> SimulationResult: ...

class SimulationEnvironment:
    """SimPy-based simulation environment."""

    def __init__(self, config: SimulationConfig):
        if not HAS_SIMPY:
            raise ImportError("simpy required: pip install simpy")
        self.config = config
        self.env = simpy.Environment()
        # ... implementation
```

**No dependencies on other parallel tasks.**

---

## Task 3: Simulation Event Types

**File:** `backend/app/resilience/simulation/events.py`

**Requirements:**
- Define event dataclasses for simulation
- Event types: FacultyLoss, FacultySickCall, FacultyReturn, ZoneFailure, CascadeTrigger, BorrowingRequest, RecoveryComplete
- Include severity levels and timestamps
- Pure data definitions - no simulation logic

**Skeleton:**
```python
"""Event types for resilience simulations."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

class EventSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    CATASTROPHIC = "catastrophic"

class EventType(str, Enum):
    FACULTY_SICK_CALL = "faculty_sick_call"
    FACULTY_RETURN = "faculty_return"
    FACULTY_RESIGNATION = "faculty_resignation"
    FACULTY_PCS = "faculty_pcs"
    ZONE_DEGRADED = "zone_degraded"
    ZONE_FAILED = "zone_failed"
    ZONE_RECOVERED = "zone_recovered"
    CASCADE_STARTED = "cascade_started"
    CASCADE_CONTAINED = "cascade_contained"
    BORROWING_REQUESTED = "borrowing_requested"
    BORROWING_COMPLETED = "borrowing_completed"

@dataclass
class SimulationEvent:
    """Base event in simulation."""
    id: UUID
    timestamp: float  # Simulation time
    event_type: EventType
    severity: EventSeverity
    description: str

@dataclass
class FacultyEvent(SimulationEvent):
    """Event affecting a faculty member."""
    faculty_id: UUID
    zone_id: UUID | None = None
    duration_days: float | None = None

@dataclass
class ZoneEvent(SimulationEvent):
    """Event affecting a scheduling zone."""
    zone_id: UUID
    previous_status: str
    new_status: str
    faculty_affected: list[UUID] = None

@dataclass
class CascadeEvent(SimulationEvent):
    """Cascade failure event."""
    trigger_zone_id: UUID
    affected_zones: list[UUID]
    was_contained: bool
    containment_time: float | None = None
```

**No dependencies on other parallel tasks.**

---

## Task 4: Simulation Metrics Collection

**File:** `backend/app/resilience/simulation/metrics.py`

**Requirements:**
- `MetricsCollector` class to gather simulation statistics
- Track: coverage rates, zone health, faculty counts, cascade events
- Statistical summaries: mean, std, percentiles
- Time-series data collection
- Export to dict for reporting

**Skeleton:**
```python
"""Metrics collection for simulations."""
import statistics
from dataclasses import dataclass, field
from typing import Any

@dataclass
class TimeSeriesPoint:
    """Single point in time series."""
    time: float
    value: float

@dataclass
class MetricsSummary:
    """Statistical summary of a metric."""
    name: str
    count: int
    mean: float
    std: float
    min: float
    max: float
    p50: float
    p95: float
    p99: float

class MetricsCollector:
    """Collects and analyzes simulation metrics."""

    def __init__(self):
        self._time_series: dict[str, list[TimeSeriesPoint]] = {}
        self._counters: dict[str, int] = {}
        self._events: list[dict] = []

    def record_value(self, metric: str, time: float, value: float):
        """Record a time-series value."""
        if metric not in self._time_series:
            self._time_series[metric] = []
        self._time_series[metric].append(TimeSeriesPoint(time, value))

    def increment(self, counter: str, amount: int = 1):
        """Increment a counter."""
        self._counters[counter] = self._counters.get(counter, 0) + amount

    def record_event(self, event: dict):
        """Record a discrete event."""
        self._events.append(event)

    def get_summary(self, metric: str) -> MetricsSummary | None:
        """Get statistical summary for a metric."""
        points = self._time_series.get(metric, [])
        if not points:
            return None
        values = [p.value for p in points]
        sorted_values = sorted(values)
        n = len(values)
        return MetricsSummary(
            name=metric,
            count=n,
            mean=statistics.mean(values),
            std=statistics.stdev(values) if n > 1 else 0.0,
            min=min(values),
            max=max(values),
            p50=sorted_values[n // 2],
            p95=sorted_values[int(n * 0.95)],
            p99=sorted_values[int(n * 0.99)],
        )

    def to_dict(self) -> dict[str, Any]:
        """Export all metrics as dictionary."""
        return {
            "counters": self._counters.copy(),
            "summaries": {
                name: self.get_summary(name).__dict__
                for name in self._time_series
            },
            "event_count": len(self._events),
        }
```

**No dependencies on other parallel tasks.**

---

## Task 5: N-2 Contingency Scenario

**File:** `backend/app/resilience/simulation/n2_scenario.py`

**Requirements:**
- Simulate random loss of 2 faculty members
- Model zone response and borrowing attempts
- Track whether coverage is maintained
- Run multiple iterations for statistical validity
- Output pass/fail rate and failure modes

**Skeleton:**
```python
"""N-2 Contingency validation scenario.

Tests whether the system can survive loss of any 2 faculty members
without cascading failure, as required by power grid N-2 standards.
"""
import random
from dataclasses import dataclass
from uuid import UUID, uuid4

@dataclass
class N2ScenarioConfig:
    """Configuration for N-2 scenario."""
    iterations: int = 1000
    faculty_count: int = 10
    zone_count: int = 6
    recovery_time_hours: float = 4.0
    borrowing_enabled: bool = True

@dataclass
class N2ScenarioResult:
    """Results from N-2 scenario run."""
    config: N2ScenarioConfig
    iterations_run: int
    passes: int
    failures: int
    pass_rate: float
    # Failure analysis
    failure_modes: dict[str, int]  # mode -> count
    most_vulnerable_pairs: list[tuple[UUID, UUID]]
    average_recovery_time: float
    cascade_rate: float

class N2ContingencyScenario:
    """
    Validates N-2 contingency compliance.

    For each iteration:
    1. Select 2 random faculty to remove
    2. Check if all zones remain self-sufficient
    3. If not, attempt borrowing
    4. Track if coverage maintained or cascade occurs
    """

    def __init__(self, config: N2ScenarioConfig):
        self.config = config
        self._faculty: list[UUID] = []
        self._zones: list[dict] = []
        self._results: list[dict] = []

    def setup(self):
        """Initialize faculty and zone structures."""
        self._faculty = [uuid4() for _ in range(self.config.faculty_count)]
        # Create zones with faculty assignments
        # ... implementation

    def run_iteration(self, seed: int) -> dict:
        """Run single iteration of N-2 test."""
        random.seed(seed)
        # Select 2 faculty to lose
        lost = random.sample(self._faculty, 2)
        # Check zone self-sufficiency
        # Attempt borrowing if needed
        # Return results
        # ... implementation

    def run(self) -> N2ScenarioResult:
        """Run all iterations and aggregate results."""
        self.setup()
        for i in range(self.config.iterations):
            result = self.run_iteration(seed=i)
            self._results.append(result)
        return self._aggregate_results()

    def _aggregate_results(self) -> N2ScenarioResult:
        """Aggregate individual results into summary."""
        passes = sum(1 for r in self._results if r.get("passed", False))
        # ... implementation
```

**No dependencies on other parallel tasks.**

---

## Task 6: Burnout Cascade Scenario

**File:** `backend/app/resilience/simulation/cascade_scenario.py`

**Requirements:**
- Model positive feedback loop: overwork → burnout → departure → more overwork
- Implement "extinction vortex" from ecology
- Track time-to-collapse and minimum viable population
- Identify cascade trigger thresholds

**Skeleton:**
```python
"""Burnout cascade / extinction vortex scenario.

Models the positive feedback loop where faculty loss increases
workload on remaining faculty, causing burnout and further departures.
"""
import math
import random
from dataclasses import dataclass
from uuid import UUID, uuid4

@dataclass
class CascadeConfig:
    """Configuration for cascade scenario."""
    initial_faculty: int = 10
    minimum_viable: int = 3
    max_simulation_days: int = 730  # 2 years
    # Workload parameters
    base_workload_per_person: float = 1.0
    sustainable_workload: float = 1.2
    burnout_threshold: float = 1.5
    # Probability parameters
    base_departure_rate: float = 0.001  # Per day
    burnout_departure_multiplier: float = 5.0
    # Recovery parameters
    hiring_delay_days: int = 90
    hiring_probability: float = 0.1  # Per day after delay

@dataclass
class CascadeResult:
    """Results from cascade simulation."""
    config: CascadeConfig
    final_faculty_count: int
    collapsed: bool
    days_until_collapse: int | None
    peak_workload: float
    total_departures: int
    departures_from_burnout: int
    # Vortex analysis
    entered_vortex: bool
    vortex_entry_day: int | None
    vortex_faculty_count: int | None

class BurnoutCascadeScenario:
    """
    Simulates burnout-driven faculty departure cascade.

    Models the "extinction vortex" from ecology where a population
    becomes too small to be viable, leading to accelerating collapse.

    Key dynamics:
    - Workload per person = Total demand / Faculty count
    - Burnout probability increases exponentially with overwork
    - Departures increase workload for survivors
    - Hiring may not keep pace with departures
    """

    def __init__(self, config: CascadeConfig):
        self.config = config
        self._faculty: list[UUID] = []
        self._day = 0
        self._events: list[dict] = []

    def calculate_workload(self) -> float:
        """Calculate current workload per faculty member."""
        if len(self._faculty) == 0:
            return float('inf')
        total_demand = self.config.initial_faculty * self.config.base_workload_per_person
        return total_demand / len(self._faculty)

    def calculate_burnout_probability(self, workload: float) -> float:
        """
        Calculate daily probability of burnout departure.

        Uses exponential increase above sustainable threshold.
        """
        if workload <= self.config.sustainable_workload:
            return self.config.base_departure_rate

        # Exponential increase above sustainable
        overwork_ratio = workload / self.config.sustainable_workload
        multiplier = math.exp(overwork_ratio - 1)
        return min(0.5, self.config.base_departure_rate * multiplier *
                   self.config.burnout_departure_multiplier)

    def is_in_vortex(self, workload: float) -> bool:
        """Check if system has entered extinction vortex."""
        # Vortex = workload so high that departure rate exceeds recovery
        return workload > self.config.burnout_threshold

    def simulate_day(self) -> dict:
        """Simulate one day."""
        workload = self.calculate_workload()
        burnout_prob = self.calculate_burnout_probability(workload)

        events = {"day": self._day, "departures": 0, "hires": 0}

        # Check each faculty for departure
        for fac_id in self._faculty[:]:
            if random.random() < burnout_prob:
                self._faculty.remove(fac_id)
                events["departures"] += 1

        # Check for hiring
        # ... implementation

        self._day += 1
        return events

    def run(self) -> CascadeResult:
        """Run full simulation."""
        self._faculty = [uuid4() for _ in range(self.config.initial_faculty)]
        self._day = 0

        while self._day < self.config.max_simulation_days:
            if len(self._faculty) < self.config.minimum_viable:
                # Collapsed
                return self._build_result(collapsed=True)
            self.simulate_day()

        return self._build_result(collapsed=False)
```

**No dependencies on other parallel tasks.**

---

## Task 7: Blast Radius Unit Tests

**File:** `backend/tests/test_resilience_blast_radius.py`

**Requirements:**
- Test `SchedulingZone` status calculations
- Test `BlastRadiusManager` zone creation and management
- Test borrowing request flow
- Test incident recording and containment
- Test zone health reports

**Skeleton:**
```python
"""Unit tests for blast radius isolation module."""
import pytest
from uuid import uuid4
from datetime import datetime

from app.resilience.blast_radius import (
    BlastRadiusManager,
    SchedulingZone,
    ZoneFacultyAssignment,
    ZoneStatus,
    ZoneType,
    ContainmentLevel,
    BorrowingPriority,
)


class TestSchedulingZone:
    """Tests for SchedulingZone dataclass."""

    def test_empty_zone_is_not_self_sufficient(self):
        """Zone with no faculty cannot be self-sufficient."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test",
            zone_type=ZoneType.INPATIENT,
            description="Test zone",
            minimum_coverage=2,
        )
        assert not zone.is_self_sufficient()

    def test_zone_with_enough_faculty_is_self_sufficient(self):
        """Zone with adequate faculty is self-sufficient."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test",
            zone_type=ZoneType.INPATIENT,
            description="Test zone",
            minimum_coverage=2,
        )
        zone.primary_faculty = [
            ZoneFacultyAssignment(uuid4(), "Dr. A", "primary"),
            ZoneFacultyAssignment(uuid4(), "Dr. B", "primary"),
        ]
        assert zone.is_self_sufficient()

    def test_status_calculation_green(self):
        """Zone above optimal coverage is GREEN."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test",
            zone_type=ZoneType.INPATIENT,
            description="Test zone",
            minimum_coverage=2,
            optimal_coverage=3,
        )
        zone.primary_faculty = [
            ZoneFacultyAssignment(uuid4(), f"Dr. {i}", "primary")
            for i in range(4)
        ]
        assert zone.calculate_status() == ZoneStatus.GREEN

    def test_status_calculation_red(self):
        """Zone below minimum is RED."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test",
            zone_type=ZoneType.INPATIENT,
            description="Test zone",
            minimum_coverage=3,
        )
        zone.primary_faculty = [
            ZoneFacultyAssignment(uuid4(), "Dr. A", "primary"),
            ZoneFacultyAssignment(uuid4(), "Dr. B", "primary"),
        ]
        assert zone.calculate_status() == ZoneStatus.RED


class TestBlastRadiusManager:
    """Tests for BlastRadiusManager."""

    @pytest.fixture
    def manager(self):
        return BlastRadiusManager()

    def test_create_zone(self, manager):
        """Can create a scheduling zone."""
        zone = manager.create_zone(
            name="Inpatient",
            zone_type=ZoneType.INPATIENT,
            description="Test",
            services=["icu", "wards"],
            minimum_coverage=2,
        )
        assert zone.id in manager.zones
        assert zone.name == "Inpatient"

    def test_create_default_zones(self, manager):
        """Default zones are created correctly."""
        zones = manager.create_default_zones()
        assert len(zones) == 6
        # Check priority ordering
        types = [z.zone_type for z in zones]
        assert ZoneType.INPATIENT in types
        assert ZoneType.ADMINISTRATIVE in types

    def test_assign_faculty_to_zone(self, manager):
        """Can assign faculty to zones."""
        zone = manager.create_zone(
            name="Test",
            zone_type=ZoneType.OUTPATIENT,
            description="Test",
            services=["clinics"],
        )
        result = manager.assign_faculty_to_zone(
            zone.id, uuid4(), "Dr. Test", "primary"
        )
        assert result is True
        assert len(zone.primary_faculty) == 1

    def test_borrowing_blocked_in_lockdown(self, manager):
        """Borrowing is blocked during lockdown."""
        manager.create_default_zones()
        manager.set_global_containment(ContainmentLevel.LOCKDOWN, "Test")

        zones = list(manager.zones.values())
        request = manager.request_borrowing(
            requesting_zone_id=zones[0].id,
            lending_zone_id=zones[1].id,
            faculty_id=uuid4(),
            priority=BorrowingPriority.HIGH,
            reason="Need coverage",
        )
        assert request is None


class TestIncidentHandling:
    """Tests for incident recording and containment."""

    @pytest.fixture
    def manager_with_zones(self):
        manager = BlastRadiusManager()
        manager.create_default_zones()
        return manager

    def test_record_incident(self, manager_with_zones):
        """Can record incidents affecting zones."""
        zone = list(manager_with_zones.zones.values())[0]
        incident = manager_with_zones.record_incident(
            zone_id=zone.id,
            incident_type="faculty_loss",
            description="Dr. X resigned",
            severity="moderate",
        )
        assert incident is not None
        assert incident.zone_id == zone.id

    def test_severe_incident_triggers_containment(self, manager_with_zones):
        """Severe incidents activate zone containment."""
        zone = list(manager_with_zones.zones.values())[0]
        manager_with_zones.record_incident(
            zone_id=zone.id,
            incident_type="faculty_loss",
            description="Multiple losses",
            severity="severe",
        )
        assert zone.containment_level != ContainmentLevel.NONE
```

**No dependencies on other parallel tasks.**

---

## Task 8: Hub Analysis Unit Tests

**File:** `backend/tests/test_resilience_hub_analysis.py`

**Requirements:**
- Test `FacultyCentrality` calculations
- Test hub identification with various thresholds
- Test cross-training recommendation generation
- Test hub protection plan creation
- Test distribution report generation

**Skeleton:**
```python
"""Unit tests for hub vulnerability analysis module."""
import pytest
from uuid import uuid4
from datetime import date

from app.resilience.hub_analysis import (
    HubAnalyzer,
    FacultyCentrality,
    HubRiskLevel,
    HubProtectionStatus,
    CrossTrainingPriority,
)


class TestFacultyCentrality:
    """Tests for FacultyCentrality dataclass."""

    def test_composite_score_calculation(self):
        """Composite score is calculated correctly."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Dr. Test",
            calculated_at=datetime.now(),
            degree_centrality=0.5,
            betweenness_centrality=0.3,
            eigenvector_centrality=0.4,
            pagerank=0.2,
            replacement_difficulty=0.6,
        )
        centrality.calculate_composite()
        assert 0.0 <= centrality.composite_score <= 1.0

    def test_risk_level_low(self):
        """Low composite score yields LOW risk."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Dr. Test",
            calculated_at=datetime.now(),
        )
        centrality.composite_score = 0.1
        assert centrality.risk_level == HubRiskLevel.LOW

    def test_risk_level_catastrophic_unique_services(self):
        """Many unique services yields CATASTROPHIC risk."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Dr. Critical",
            calculated_at=datetime.now(),
            unique_services=3,
        )
        assert centrality.risk_level == HubRiskLevel.CATASTROPHIC

    def test_is_hub_detection(self):
        """Hub detection based on thresholds."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Dr. Hub",
            calculated_at=datetime.now(),
            composite_score=0.5,
        )
        assert centrality.is_hub is True


class TestHubAnalyzer:
    """Tests for HubAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        return HubAnalyzer(hub_threshold=0.4, use_networkx=False)

    @pytest.fixture
    def sample_data(self):
        """Sample faculty and service data."""
        faculty = [
            type('Faculty', (), {'id': uuid4(), 'name': f'Dr. {i}'})()
            for i in range(5)
        ]
        services = {
            uuid4(): [faculty[0].id],  # Single provider
            uuid4(): [faculty[0].id, faculty[1].id],  # Dual
            uuid4(): [f.id for f in faculty],  # All can cover
        }
        return faculty, [], services

    def test_calculate_centrality_basic(self, analyzer, sample_data):
        """Basic centrality calculation works."""
        faculty, assignments, services = sample_data
        results = analyzer.calculate_centrality(faculty, assignments, services)
        assert len(results) == 5
        # First faculty has unique service, should rank highest
        assert results[0].faculty_id == faculty[0].id

    def test_identify_hubs(self, analyzer, sample_data):
        """Hub identification from centrality scores."""
        faculty, assignments, services = sample_data
        analyzer.calculate_centrality(faculty, assignments, services)
        hubs = analyzer.identify_hubs()
        assert len(hubs) > 0

    def test_cross_training_single_provider(self, analyzer, sample_data):
        """Single-provider services generate HIGH priority recommendations."""
        faculty, _, services = sample_data
        recs = analyzer.generate_cross_training_recommendations(
            services=services,
            all_faculty=[f.id for f in faculty],
        )
        high_priority = [r for r in recs if r.priority == CrossTrainingPriority.HIGH]
        assert len(high_priority) >= 1


class TestHubProtection:
    """Tests for hub protection planning."""

    @pytest.fixture
    def analyzer_with_hubs(self):
        analyzer = HubAnalyzer(use_networkx=False)
        # Manually create a hub
        hub_id = uuid4()
        analyzer.centrality_cache[hub_id] = FacultyCentrality(
            faculty_id=hub_id,
            faculty_name="Dr. Critical",
            calculated_at=datetime.now(),
            composite_score=0.7,
        )
        return analyzer, hub_id

    def test_create_protection_plan(self, analyzer_with_hubs):
        """Can create protection plan for a hub."""
        analyzer, hub_id = analyzer_with_hubs
        plan = analyzer.create_protection_plan(
            hub_faculty_id=hub_id,
            period_start=date(2024, 7, 1),
            period_end=date(2024, 8, 31),
            reason="PCS season protection",
        )
        assert plan is not None
        assert plan.hub_faculty_id == hub_id


class TestDistributionReport:
    """Tests for hub distribution reporting."""

    def test_report_generation(self):
        """Distribution report generates without errors."""
        analyzer = HubAnalyzer(use_networkx=False)
        # Add some test data
        for i in range(3):
            analyzer.centrality_cache[uuid4()] = FacultyCentrality(
                faculty_id=uuid4(),
                faculty_name=f"Dr. {i}",
                calculated_at=datetime.now(),
                composite_score=0.3 * i,
            )

        services = {uuid4(): [uuid4()]}  # Single provider
        report = analyzer.get_distribution_report(services)

        assert report.total_faculty == 3
        assert len(report.services_with_single_provider) >= 1
```

**No dependencies on other parallel tasks.**

---

## Task 9: Simulation Design Document

**File:** `docs/SIMULATION_DESIGN.md`

**Requirements:**
- Architecture overview for SimPy-based simulation module
- Describe the two main scenarios (N-2, Cascade)
- Explain metrics collection approach
- Document integration with existing resilience components
- Include usage examples

**Structure:**
```markdown
# Resilience Simulation Module Design

## Overview
- Purpose: Validate resilience framework assumptions via discrete-event simulation
- Technology: SimPy (optional dependency)
- Location: backend/app/resilience/simulation/

## Architecture
[Diagram showing module structure]

## Scenarios
### N-2 Contingency Validation
- Purpose
- Methodology
- Expected outputs

### Burnout Cascade / Extinction Vortex
- Purpose
- Key dynamics modeled
- Expected outputs

## Metrics Collection
- Time-series data
- Statistical summaries
- Event logs

## Integration Points
- Connection to BlastRadiusManager
- Connection to HubAnalyzer
- Output for reporting

## Usage Examples
[Code examples]

## Future Scenarios
- Ideas for additional validation scenarios
```

**No dependencies on other parallel tasks.**

---

## Task 10: Skill-Based Zones Design Document

**File:** `docs/SKILL_ZONES_DESIGN.md`

**Requirements:**
- Document the "warm body fallacy" problem
- Propose data model changes for skill tracking
- Describe enhanced self-sufficiency algorithm
- Integration with hub analysis
- Migration considerations

**Structure:**
```markdown
# Skill-Based Zone Self-Sufficiency Design

## Problem Statement
Current `is_self_sufficient()` only checks headcount, not skills.

## The "Warm Body Fallacy"
- Example scenario
- Risk implications

## Proposed Solution

### Data Model Changes
```python
# SchedulingZone additions
critical_skills: dict[str, int]  # skill -> minimum_required

# ZoneFacultyAssignment additions
skills: list[str]
```

### Algorithm Enhancement
```python
def is_self_sufficient(self) -> bool:
    # Check count
    # Check each critical skill
```

### Integration with Hub Analysis
- Use hub analysis to identify critical skills
- Feed cross-training recommendations into zone planning

## Migration Plan
1. Add fields (nullable)
2. Populate existing zones
3. Enable skill checks

## Testing Strategy
- Unit tests for skill checking
- Integration tests with hub analyzer
```

**No dependencies on other parallel tasks.**

---

## Execution Notes

### Before Starting
1. Each terminal should `git pull` to ensure latest code
2. Each terminal works on EXACTLY ONE file from this list
3. No cross-file imports during parallel work

### After Parallel Work
1. Each terminal commits its single file
2. Integration task merges all changes
3. Add imports to `__init__.py` files
4. Run full test suite

### File Creation Commands
```bash
# Create simulation package directory
mkdir -p backend/app/resilience/simulation

# Create empty __init__ for tests (if needed)
mkdir -p backend/tests/resilience
touch backend/tests/resilience/__init__.py
```
