"""
Burnout Cascade / Extinction Vortex Scenario.

This module models the positive feedback loop in organizational systems where
overwork leads to burnout, causing departures that increase workload on survivors,
creating a self-reinforcing death spiral.

The key dynamics modeled:
    - Workload = Total Demand / Faculty Count (increases as people leave)
    - Departure probability increases exponentially above sustainable threshold
    - Hiring has delay and is probabilistic (may not keep pace with losses)
    - "Extinction vortex" = when departure rate structurally exceeds replacement rate

This simulation demonstrates how systems can collapse even when they start in
seemingly stable configurations, highlighting the importance of maintaining
workload below critical thresholds.

Example:
    >>> config = CascadeConfig(initial_faculty=10, burnout_threshold=1.5)
    >>> scenario = BurnoutCascadeScenario(config)
    >>> result = scenario.run()
    >>> if result.collapsed:
    ...     print(f"System collapsed after {result.days_to_collapse} days")
    >>> for rec in result.recommendations:
    ...     print(rec)
"""

import math
import random
from dataclasses import dataclass
from typing import Optional


@dataclass
class CascadeConfig:
    """
    Configuration for burnout cascade simulation.

    Attributes:
        initial_faculty: Starting number of faculty members
        minimum_viable: Minimum faculty count needed to maintain operations
        max_simulation_days: Maximum days to simulate (2 years default)
        total_workload_units: Constant total demand on the system
        sustainable_workload: Workload per person that can be sustained long-term
        burnout_threshold: Workload level where burnout effects begin
        critical_threshold: Workload level indicating critical danger
        base_departure_rate: Daily probability of departure under normal conditions (~3%/year)
        burnout_multiplier: Factor by which burnout increases departure rate
        hiring_delay_days: Days between initiating hire and person starting
        hiring_rate: Daily probability of initiating a hire (for each open slot)
        max_hiring_queue: Maximum concurrent hiring processes
        seed: Random seed for reproducibility
    """

    initial_faculty: int = 10
    minimum_viable: int = 3
    max_simulation_days: int = 730  # 2 years
    total_workload_units: float = 10.0  # constant demand
    sustainable_workload: float = 1.2  # per person
    burnout_threshold: float = 1.5
    critical_threshold: float = 2.0
    base_departure_rate: float = 0.001  # per day, ~3%/year
    burnout_multiplier: float = 5.0  # how much burnout increases departure rate
    hiring_delay_days: int = 90
    hiring_rate: float = 0.02  # probability per day after delay
    max_hiring_queue: int = 3
    seed: int = 42


@dataclass
class DailySnapshot:
    """
    Snapshot of system state on a single day.

    Attributes:
        day: Current simulation day
        faculty_count: Number of active faculty
        workload_per_person: Current workload per faculty member
        departures: Number of departures that occurred this day
        hires: Number of new hires that started this day
        in_burnout_zone: Whether workload exceeds burnout threshold
        in_critical_zone: Whether workload exceeds critical threshold
    """

    day: int
    faculty_count: int
    workload_per_person: float
    departures: int
    hires: int
    in_burnout_zone: bool  # workload > burnout_threshold
    in_critical_zone: bool  # workload > critical_threshold


@dataclass
class CascadeResult:
    """
    Results from a cascade simulation run.

    Attributes:
        config: Configuration used for this simulation
        final_faculty_count: Number of faculty at simulation end
        collapsed: Whether system fell below minimum viable threshold
        days_to_collapse: Days until collapse (None if no collapse)
        peak_workload: Maximum workload experienced during simulation
        total_departures: Total number of faculty who departed
        departures_from_burnout: Departures that occurred during burnout conditions
        total_hires: Total number of successful hires
        entered_vortex: Whether system entered extinction vortex
        vortex_entry_day: Day when vortex was entered (None if never)
        vortex_faculty_count: Faculty count when vortex entered (None if never)
        time_in_burnout_zone: Number of days spent above burnout threshold
        time_in_critical_zone: Number of days spent above critical threshold
        snapshots: Complete daily history of simulation
        recommendations: Actionable recommendations based on results
    """

    config: CascadeConfig
    final_faculty_count: int
    collapsed: bool  # fell below minimum_viable
    days_to_collapse: Optional[int]
    peak_workload: float
    total_departures: int
    departures_from_burnout: int  # when workload > burnout_threshold
    total_hires: int
    entered_vortex: bool  # point of no return
    vortex_entry_day: Optional[int]
    vortex_faculty_count: Optional[int]
    time_in_burnout_zone: int  # days
    time_in_critical_zone: int  # days
    snapshots: list[DailySnapshot]
    recommendations: list[str]


class BurnoutCascadeScenario:
    """
    Simulates burnout cascade / extinction vortex dynamics.

    This class models the death spiral that can occur in organizational systems
    when workload exceeds sustainable levels. As faculty leave due to burnout,
    remaining faculty face even higher workload, leading to more departures.

    The simulation uses exponential departure probability curves to model the
    accelerating effect of excessive workload on turnover. It also models
    realistic hiring constraints including delays and capacity limits.

    The "extinction vortex" is detected when the system reaches a point where
    the departure rate structurally exceeds the replacement rate, making
    recovery impossible without external intervention.
    """

    def __init__(self, config: CascadeConfig):
        """
        Initialize cascade scenario with configuration.

        Args:
            config: Configuration parameters for the simulation
        """
        self.config = config
        self._faculty_count = config.initial_faculty
        self._day = 0
        self._hiring_queue: list[int] = []  # days when hires arrive
        self._snapshots: list[DailySnapshot] = []
        self._rng = random.Random(config.seed)
        self._departures_in_burnout = 0

    def calculate_workload(self) -> float:
        """
        Calculate current workload per person.

        Returns:
            Workload units per faculty member (infinity if no faculty)
        """
        if self._faculty_count == 0:
            return float('inf')
        return self.config.total_workload_units / self._faculty_count

    def calculate_departure_probability(self, workload: float) -> float:
        """
        Calculate probability of departure based on workload.

        Uses exponential increase above sustainable threshold to model the
        accelerating effect of burnout on turnover decisions.

        Formula:
            - workload <= sustainable: base_rate
            - workload > sustainable: base_rate * exp(k * (ratio - 1)) * multiplier

        where ratio = workload / sustainable and k controls steepness.

        Args:
            workload: Current workload per person

        Returns:
            Daily probability of departure (capped at 1.0)
        """
        if workload <= self.config.sustainable_workload:
            return self.config.base_departure_rate

        # Exponential increase based on how far above sustainable
        ratio = workload / self.config.sustainable_workload
        k = 1.0  # steepness factor
        exponential_factor = math.exp(k * (ratio - 1))

        return min(
            1.0,
            self.config.base_departure_rate * exponential_factor * self.config.burnout_multiplier
        )

    def is_in_vortex(self) -> bool:
        """
        Check if system is in extinction vortex.

        The vortex occurs when expected departures exceed expected hires,
        creating a self-reinforcing downward spiral. This is a structural
        condition that typically requires external intervention to escape.

        Returns:
            True if departure rate exceeds replacement rate
        """
        workload = self.calculate_workload()
        departure_prob = self.calculate_departure_probability(workload)

        # Expected departures per day
        expected_departures = departure_prob * self._faculty_count

        # Expected hires per day (considering queue limit)
        active_hiring_slots = min(
            self.config.max_hiring_queue,
            len(self._hiring_queue)
        )
        expected_hires = self.config.hiring_rate * active_hiring_slots

        # In vortex if losing more than gaining
        return expected_departures > expected_hires

    def _process_departures(self) -> int:
        """
        Process faculty departures for the current day.

        Each faculty member has an independent probability of departing based
        on current workload. Departures during burnout conditions are tracked
        separately for analysis.

        Returns:
            Number of faculty who departed this day
        """
        workload = self.calculate_workload()
        departure_prob = self.calculate_departure_probability(workload)

        departed = 0
        for _ in range(self._faculty_count):
            if self._rng.random() < departure_prob:
                departed += 1

        # Track if departures happened during burnout
        if workload > self.config.burnout_threshold:
            self._departures_in_burnout += departed

        self._faculty_count -= departed
        return departed

    def _process_hiring(self) -> int:
        """
        Process hiring for the current day.

        Hiring has two phases:
        1. Check if anyone in the queue arrives today (after delay period)
        2. Attempt to add new candidates to queue (if under capacity)

        Returns:
            Number of new hires who started today
        """
        hired = 0

        # Process existing queue - check if anyone arrives today
        new_queue = []
        for arrival_day in self._hiring_queue:
            if arrival_day == self._day:
                hired += 1
            elif arrival_day > self._day:
                new_queue.append(arrival_day)
        self._hiring_queue = new_queue

        # Add new hiring attempts if under capacity
        while len(self._hiring_queue) < self.config.max_hiring_queue:
            if self._rng.random() < self.config.hiring_rate:
                arrival_day = self._day + self.config.hiring_delay_days
                self._hiring_queue.append(arrival_day)

        self._faculty_count += hired
        return hired

    def _simulate_day(self) -> DailySnapshot:
        """
        Simulate a single day and return snapshot.

        Order of operations:
        1. Process departures
        2. Process hiring
        3. Calculate metrics
        4. Record snapshot

        Returns:
            Snapshot of system state after this day's events
        """
        # Process in order: departures, then hiring
        departures = self._process_departures()
        hires = self._process_hiring()

        workload = self.calculate_workload()

        snapshot = DailySnapshot(
            day=self._day,
            faculty_count=self._faculty_count,
            workload_per_person=workload,
            departures=departures,
            hires=hires,
            in_burnout_zone=workload > self.config.burnout_threshold,
            in_critical_zone=workload > self.config.critical_threshold
        )

        self._snapshots.append(snapshot)
        self._day += 1

        return snapshot

    def _detect_vortex_entry(self) -> Optional[tuple[int, int]]:
        """
        Detect when system entered extinction vortex.

        The vortex is identified by a sustained period where workload is in
        the critical zone AND faculty count shows a declining trend. This
        indicates the system has entered a self-reinforcing death spiral.

        Returns:
            Tuple of (day, faculty_count) at vortex entry, or None if never entered
        """
        if len(self._snapshots) < 30:  # Need some history
            return None

        for i in range(30, len(self._snapshots)):
            snapshot = self._snapshots[i]

            # Check if in critical zone
            if not snapshot.in_critical_zone:
                continue

            # Look at trend over last 30 days
            recent_snapshots = self._snapshots[i-30:i]
            faculty_counts = [s.faculty_count for s in recent_snapshots]

            # Check if declining trend
            if len(faculty_counts) >= 2:
                start_avg = sum(faculty_counts[:10]) / 10
                end_avg = sum(faculty_counts[-10:]) / 10

                # If declining by >20% and in critical zone, consider it vortex entry
                if end_avg < start_avg * 0.8:
                    return (snapshot.day, snapshot.faculty_count)

        return None

    def _generate_recommendations(self) -> list[str]:
        """
        Generate recommendations based on simulation results.

        Analyzes the simulation outcome and current system state to provide
        actionable recommendations for preventing or recovering from cascade
        scenarios.

        Returns:
            List of recommendation strings ordered by priority
        """
        recommendations = []

        workload = self.calculate_workload()

        if self._faculty_count < self.config.minimum_viable:
            recommendations.append(
                "CRITICAL: System has collapsed. Immediate emergency hiring and workload reduction required."
            )

        if workload > self.config.critical_threshold:
            recommendations.append(
                f"URGENT: Workload ({workload:.2f}) exceeds critical threshold ({self.config.critical_threshold}). "
                "Immediate intervention required to prevent cascade."
            )
        elif workload > self.config.burnout_threshold:
            recommendations.append(
                f"WARNING: Workload ({workload:.2f}) in burnout zone (>{self.config.burnout_threshold}). "
                "Increased departure risk. Consider workload reduction or accelerated hiring."
            )

        if self.is_in_vortex():
            recommendations.append(
                "System is in extinction vortex: departure rate exceeds replacement rate. "
                "Multiple interventions needed: reduce workload, accelerate hiring, improve retention."
            )

        # Hiring queue recommendations
        if len(self._hiring_queue) == 0:
            recommendations.append(
                "No active hiring pipeline. Start recruitment immediately to prevent future shortfalls."
            )
        elif len(self._hiring_queue) < self.config.max_hiring_queue:
            recommendations.append(
                f"Hiring pipeline at {len(self._hiring_queue)}/{self.config.max_hiring_queue} capacity. "
                "Consider expanding recruitment efforts."
            )

        # Time-based recommendations
        time_in_burnout = sum(1 for s in self._snapshots if s.in_burnout_zone)
        burnout_pct = (time_in_burnout / len(self._snapshots) * 100) if self._snapshots else 0

        if burnout_pct > 50:
            recommendations.append(
                f"System spent {burnout_pct:.1f}% of time in burnout zone. "
                "Structural workload reduction needed to achieve sustainability."
            )

        # Departure analysis
        total_departures = sum(s.departures for s in self._snapshots)
        if self._departures_in_burnout > 0 and total_departures > 0:
            burnout_departure_pct = (self._departures_in_burnout / total_departures * 100)
            recommendations.append(
                f"{burnout_departure_pct:.1f}% of departures occurred during burnout conditions. "
                "Focus on workload management to improve retention."
            )

        return recommendations

    def run(self) -> CascadeResult:
        """
        Run the cascade simulation.

        Executes the day-by-day simulation until either:
        1. System collapses (falls below minimum viable threshold)
        2. Maximum simulation duration is reached

        Returns:
            Complete simulation results including snapshots and analysis
        """
        # Reset state
        self._day = 0
        self._snapshots = []
        self._faculty_count = self.config.initial_faculty
        self._hiring_queue = []
        self._departures_in_burnout = 0

        collapsed = False
        days_to_collapse = None

        while self._day < self.config.max_simulation_days:
            self._simulate_day()

            # Check for collapse
            if self._faculty_count < self.config.minimum_viable:
                collapsed = True
                days_to_collapse = self._day
                break

        # Calculate statistics
        peak_workload = max(
            (s.workload_per_person for s in self._snapshots),
            default=0.0
        )
        total_departures = sum(s.departures for s in self._snapshots)
        total_hires = sum(s.hires for s in self._snapshots)
        time_in_burnout = sum(1 for s in self._snapshots if s.in_burnout_zone)
        time_in_critical = sum(1 for s in self._snapshots if s.in_critical_zone)

        # Detect vortex
        vortex_info = self._detect_vortex_entry()
        entered_vortex = vortex_info is not None
        vortex_entry_day = vortex_info[0] if vortex_info else None
        vortex_faculty_count = vortex_info[1] if vortex_info else None

        recommendations = self._generate_recommendations()

        return CascadeResult(
            config=self.config,
            final_faculty_count=self._faculty_count,
            collapsed=collapsed,
            days_to_collapse=days_to_collapse,
            peak_workload=peak_workload,
            total_departures=total_departures,
            departures_from_burnout=self._departures_in_burnout,
            total_hires=total_hires,
            entered_vortex=entered_vortex,
            vortex_entry_day=vortex_entry_day,
            vortex_faculty_count=vortex_faculty_count,
            time_in_burnout_zone=time_in_burnout,
            time_in_critical_zone=time_in_critical,
            snapshots=self._snapshots,
            recommendations=recommendations
        )
