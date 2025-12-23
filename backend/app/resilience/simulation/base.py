"""
Base simulation environment for resilience testing.

This module provides the foundational components for discrete-event simulation
of faculty scheduling resilience scenarios. It handles optional SimPy dependency
and defines core configuration and result structures.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from random import Random
from typing import Any

# Handle optional SimPy dependency
try:
    import simpy

    HAS_SIMPY = True
except ImportError:
    simpy = None  # type: ignore
    HAS_SIMPY = False


logger = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    """
    Configuration parameters for resilience simulation.

    Attributes:
        seed: Random seed for reproducibility
        duration_days: Total simulation duration in days
        time_step_hours: Time step granularity in hours
        initial_faculty_count: Starting number of faculty members
        minimum_viable_count: Minimum faculty needed to maintain coverage
        zone_count: Number of zones requiring coverage
        sick_call_probability: Daily probability of sick call per faculty
        resignation_base_probability: Daily base probability of resignation per faculty
        pcs_probability: Annual probability of PCS (Permanent Change of Station)
        recovery_time_hours: Average hours until faculty returns from sick call
        borrowing_enabled: Whether cross-zone faculty borrowing is allowed
    """

    seed: int = 42
    duration_days: int = 365
    time_step_hours: float = 1.0
    initial_faculty_count: int = 10
    minimum_viable_count: int = 3
    zone_count: int = 6
    sick_call_probability: float = 0.02  # per day
    resignation_base_probability: float = 0.001  # per day
    pcs_probability: float = 0.0027  # annual ~1% chance
    recovery_time_hours: float = 4.0
    borrowing_enabled: bool = True

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.duration_days <= 0:
            raise ValueError("duration_days must be positive")
        if self.time_step_hours <= 0:
            raise ValueError("time_step_hours must be positive")
        if self.initial_faculty_count < 0:
            raise ValueError("initial_faculty_count cannot be negative")
        if self.minimum_viable_count < 0:
            raise ValueError("minimum_viable_count cannot be negative")
        if self.zone_count < 1:
            raise ValueError("zone_count must be at least 1")
        if not (0 <= self.sick_call_probability <= 1):
            raise ValueError("sick_call_probability must be between 0 and 1")
        if not (0 <= self.resignation_base_probability <= 1):
            raise ValueError("resignation_base_probability must be between 0 and 1")
        if not (0 <= self.pcs_probability <= 1):
            raise ValueError("pcs_probability must be between 0 and 1")
        if self.recovery_time_hours < 0:
            raise ValueError("recovery_time_hours cannot be negative")


@dataclass
class SimulationResult:
    """
    Results and metrics from a completed simulation run.

    Attributes:
        config: The configuration used for this simulation
        started_at: Timestamp when simulation began
        completed_at: Timestamp when simulation completed
        final_faculty_count: Number of faculty at simulation end
        coverage_maintained: Whether minimum coverage was maintained
        days_until_failure: Days until coverage failure (None if no failure)
        cascade_events: Number of cascade failure events detected
        total_sick_calls: Total number of sick calls during simulation
        total_departures: Total number of faculty departures (resignations + PCS)
        metrics: Additional metrics and statistics collected during simulation
    """

    config: SimulationConfig
    started_at: datetime
    completed_at: datetime
    final_faculty_count: int
    coverage_maintained: bool
    days_until_failure: int | None
    cascade_events: int
    total_sick_calls: int
    total_departures: int
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        """Total wall-clock time for simulation execution."""
        return (self.completed_at - self.started_at).total_seconds()

    @property
    def success(self) -> bool:
        """Whether the simulation completed successfully without failure."""
        return self.coverage_maintained and self.days_until_failure is None

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "config": {
                "seed": self.config.seed,
                "duration_days": self.config.duration_days,
                "time_step_hours": self.config.time_step_hours,
                "initial_faculty_count": self.config.initial_faculty_count,
                "minimum_viable_count": self.config.minimum_viable_count,
                "zone_count": self.config.zone_count,
                "sick_call_probability": self.config.sick_call_probability,
                "resignation_base_probability": self.config.resignation_base_probability,
                "pcs_probability": self.config.pcs_probability,
                "recovery_time_hours": self.config.recovery_time_hours,
                "borrowing_enabled": self.config.borrowing_enabled,
            },
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "final_faculty_count": self.final_faculty_count,
            "coverage_maintained": self.coverage_maintained,
            "days_until_failure": self.days_until_failure,
            "cascade_events": self.cascade_events,
            "total_sick_calls": self.total_sick_calls,
            "total_departures": self.total_departures,
            "success": self.success,
            "metrics": self.metrics,
        }


class SimulationEnvironment:
    """
    Discrete-event simulation environment for resilience testing.

    This class wraps SimPy's simulation environment and provides helper methods
    for scheduling events, managing time, and maintaining random state.

    Raises:
        ImportError: If SimPy is not installed
    """

    def __init__(self, config: SimulationConfig) -> None:
        """
        Initialize simulation environment.

        Args:
            config: Configuration parameters for the simulation

        Raises:
            ImportError: If SimPy is not available
        """
        if not HAS_SIMPY:
            raise ImportError(
                "SimPy is required for simulation but not installed. "
                "Install with: pip install simpy"
            )

        self._config = config
        self._env = simpy.Environment()  # type: ignore
        self._random = Random(config.seed)

        logger.info(
            f"Initialized simulation environment with seed={config.seed}, "
            f"duration={config.duration_days} days"
        )

    @property
    def env(self) -> Any:
        """Access to underlying SimPy environment."""
        return self._env

    @property
    def config(self) -> SimulationConfig:
        """Simulation configuration."""
        return self._config

    @property
    def random(self) -> Random:
        """Seeded random number generator for reproducibility."""
        return self._random

    def run(self, until: float) -> None:
        """
        Run the simulation until the specified time.

        Args:
            until: Simulation time to run until (in time units)
        """
        logger.debug(f"Running simulation until time={until}")
        self._env.run(until=until)
        logger.debug(f"Simulation completed at time={self._env.now}")

    def now(self) -> float:
        """
        Get current simulation time.

        Returns:
            Current simulation time in hours
        """
        return float(self._env.now)

    def schedule_event(self, delay: float, callback: Callable[[], None]) -> None:
        """
        Schedule an event to occur after a delay.

        Args:
            delay: Time delay in hours before event occurs
            callback: Function to call when event triggers
        """

        def _event_wrapper() -> Any:
            """Wrapper to execute callback after timeout."""
            yield self._env.timeout(delay)
            callback()

        self._env.process(_event_wrapper())

    def to_days(self, time_units: float) -> float:
        """
        Convert simulation time units (hours) to days.

        Args:
            time_units: Time in simulation units (hours)

        Returns:
            Equivalent time in days
        """
        return time_units / 24.0

    def to_hours(self, time_units: float) -> float:
        """
        Convert simulation time units to hours (identity function for clarity).

        Args:
            time_units: Time in simulation units (hours)

        Returns:
            Equivalent time in hours
        """
        return time_units

    def __repr__(self) -> str:
        """String representation of simulation environment."""
        return (
            f"SimulationEnvironment(now={self.now():.2f}h, "
            f"config.duration={self.config.duration_days}d)"
        )
