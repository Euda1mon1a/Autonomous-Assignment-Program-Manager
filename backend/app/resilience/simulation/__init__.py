"""
SimPy-based Discrete-Event Simulation Module for Resilience Framework Validation.

This package provides discrete-event simulation capabilities using SimPy to validate
and test assumptions in the resilience framework. It enables modeling of complex
scenarios including faculty availability, zone capacity, and cascade effects through
time-based simulation.

The simulation module supports:
- N-2 contingency scenarios (simultaneous faculty unavailability)
- Burnout cascade scenarios (spreading workload effects)
- Custom event sequences and perturbations
- Time-series metrics collection and analysis
- Validation of theoretical resilience metrics against dynamic behavior

Key Components:
    - base: Core simulation infrastructure (config, environment, results)
    - events: Event types and severity levels for simulation
    - metrics: Metrics collection and time-series analysis
    - n2_scenario: N-2 contingency scenario implementation
    - cascade_scenario: Burnout cascade scenario implementation

Example:
    >>> from backend.app.resilience.simulation import N2ContingencyScenario
    >>> scenario = N2ContingencyScenario(faculty_ids=[1, 2], duration_hours=24)
    >>> result = scenario.run()
    >>> print(result.summary.max_cognitive_load)

Dependencies:
    - SimPy: Discrete-event simulation library
    - NumPy: Numerical computations
    - Pydantic: Configuration and result validation
"""

__version__ = "0.1.0"

# Check for SimPy availability (optional, handled gracefully in modules)
try:
    import simpy

    HAS_SIMPY = True
except ImportError:
    simpy = None  # type: ignore
    HAS_SIMPY = False


# Define public API exports
__all__ = [
    # SimPy availability flag
    "HAS_SIMPY",
    # Base simulation infrastructure
    "SimulationConfig",
    "SimulationResult",
    "SimulationEnvironment",
    # Event types and definitions
    "EventType",
    "EventSeverity",
    "SimulationEvent",
    "FacultyEvent",
    "ZoneEvent",
    "CascadeEvent",
    # Metrics collection and analysis
    "MetricsCollector",
    "MetricsSummary",
    "TimeSeriesPoint",
    # N-2 contingency scenario
    "N2ScenarioConfig",
    "N2ScenarioResult",
    "N2ContingencyScenario",
    # Burnout cascade scenario
    "CascadeConfig",
    "CascadeResult",
    "BurnoutCascadeScenario",
]


# Base simulation infrastructure
from app.resilience.simulation.base import (
    SimulationConfig,
    SimulationEnvironment,
    SimulationResult,
)

# Burnout cascade scenario
from app.resilience.simulation.cascade_scenario import (
    BurnoutCascadeScenario,
    CascadeConfig,
    CascadeResult,
)

# Event types and definitions
from app.resilience.simulation.events import (
    CascadeEvent,
    EventSeverity,
    EventType,
    FacultyEvent,
    SimulationEvent,
    ZoneEvent,
)

# Metrics collection and analysis
from app.resilience.simulation.metrics import (
    MetricsCollector,
    MetricsSummary,
    TimeSeriesPoint,
)

# N-2 contingency scenario
from app.resilience.simulation.n2_scenario import (
    N2ContingencyScenario,
    N2ScenarioConfig,
    N2ScenarioResult,
)
