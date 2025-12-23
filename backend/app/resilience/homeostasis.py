"""
Homeostasis and Feedback Loops (Biology/Physiology Pattern).

Living systems maintain stability through continuous negative feedback loops
that detect deviation and trigger correction. When feedback fails or becomes
positive, systems destabilize.

Negative Feedback (Stabilizing):
- Deviation from setpoint -> Corrective action -> Return to setpoint
- Example: Thermostat detects cold -> Heater activates -> Temperature rises

Positive Feedback (Destabilizing):
- Deviation from setpoint -> Amplifying action -> Greater deviation
- Example: Bank run - fear of insolvency -> Withdrawals -> Actual insolvency

Bifurcation/Phase Transition Detection:
- High volatility often precedes sudden system state changes
- Jitter (oscillation frequency) indicates approaching instability
- Distance to criticality measures margin before threshold breach
- Early warning enables proactive intervention before collapse

This module implements:
1. Negative feedback loops for coverage, workload, and quality metrics
2. Detection of positive feedback (burnout spirals, attrition cascades)
3. Allostatic load tracking (cumulative stress cost)
4. Setpoint management and deviation monitoring
5. Volatility tracking for early warning of phase transitions
6. Distance-to-criticality metrics for bifurcation detection
"""

import logging
import statistics
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Type of feedback loop."""

    NEGATIVE = "negative"  # Stabilizing
    POSITIVE = "positive"  # Destabilizing


class DeviationSeverity(str, Enum):
    """Severity of deviation from setpoint."""

    NONE = "none"  # Within tolerance
    MINOR = "minor"  # Slight deviation
    MODERATE = "moderate"  # Noticeable deviation
    MAJOR = "major"  # Significant deviation
    CRITICAL = "critical"  # System stability threatened


class VolatilityLevel(str, Enum):
    """Level of volatility in a metric's values."""

    STABLE = "stable"  # Low variance, predictable
    NORMAL = "normal"  # Expected fluctuation
    ELEVATED = "elevated"  # Higher than normal variance
    HIGH = "high"  # Concerning instability
    CRITICAL = "critical"  # Approaching phase transition


class CorrectiveActionType(str, Enum):
    """Types of corrective actions."""

    REDISTRIBUTE = "redistribute"  # Redistribute workload
    RECRUIT_BACKUP = "recruit_backup"  # Bring in backup coverage
    DEFER_ACTIVITY = "defer_activity"  # Postpone non-critical work
    PROTECT_RESOURCE = "protect_resource"  # Shield overloaded faculty
    REDUCE_SCOPE = "reduce_scope"  # Reduce service scope
    ALERT_ONLY = "alert_only"  # Just notify, no automatic action


class AllostasisState(str, Enum):
    """Allostatic state of the system."""

    HOMEOSTASIS = "homeostasis"  # Stable, within normal operating range
    ALLOSTASIS = "allostasis"  # Actively compensating for stress
    ALLOSTATIC_LOAD = "allostatic_load"  # Chronic compensation, accumulating wear
    ALLOSTATIC_OVERLOAD = "allostatic_overload"  # System failing to compensate


@dataclass
class Setpoint:
    """
    A target value that the system tries to maintain.

    The system monitors current values and triggers corrections
    when deviation exceeds tolerance.
    """

    id: UUID
    name: str
    description: str
    target_value: float
    tolerance: float  # Acceptable deviation (0.05 = 5%)
    unit: str = ""
    minimum: float = 0.0
    maximum: float = 1.0
    is_critical: bool = False

    def check_deviation(self, current_value: float) -> tuple[float, DeviationSeverity]:
        """
        Check deviation from setpoint.

        Returns:
            Tuple of (deviation_amount, severity)
        """
        deviation = abs(current_value - self.target_value)
        relative_deviation = (
            deviation / self.target_value if self.target_value > 0 else deviation
        )

        if relative_deviation <= self.tolerance:
            return deviation, DeviationSeverity.NONE
        elif relative_deviation <= self.tolerance * 2:
            return deviation, DeviationSeverity.MINOR
        elif relative_deviation <= self.tolerance * 3:
            return deviation, DeviationSeverity.MODERATE
        elif relative_deviation <= self.tolerance * 5:
            return deviation, DeviationSeverity.MAJOR
        else:
            return deviation, DeviationSeverity.CRITICAL


@dataclass
class VolatilityMetrics:
    """
    Volatility metrics for detecting system instability.

    High volatility often precedes phase transitions (bifurcations) where
    small parameter changes produce dramatic shifts. Monitoring volatility
    provides early warning of approaching instability.
    """

    volatility: float  # Coefficient of variation (std_dev / mean)
    jitter: float  # Oscillation frequency (direction changes / observations)
    momentum: float  # Rate of change (slope of recent values)
    distance_to_critical: float  # Distance to critical threshold (0-1 normalized)
    level: VolatilityLevel  # Categorical classification

    @property
    def is_warning(self) -> bool:
        """Whether volatility warrants attention."""
        return self.level in (
            VolatilityLevel.ELEVATED,
            VolatilityLevel.HIGH,
            VolatilityLevel.CRITICAL,
        )

    @property
    def is_critical(self) -> bool:
        """Whether volatility indicates imminent instability."""
        return self.level == VolatilityLevel.CRITICAL


@dataclass
class FeedbackLoop:
    """
    A feedback loop that monitors a metric and triggers corrections.

    Negative feedback loops stabilize the system by counteracting deviation.
    Positive feedback loops (detected, not created) destabilize.
    """

    id: UUID
    name: str
    description: str
    setpoint: Setpoint
    feedback_type: FeedbackType
    check_interval_minutes: int = 15

    # Current state
    is_active: bool = True
    last_checked: datetime | None = None
    last_correction: datetime | None = None
    consecutive_deviations: int = 0
    total_corrections: int = 0

    # History for trend analysis
    value_history: list[tuple[datetime, float]] = field(default_factory=list)
    max_history_size: int = 100

    def record_value(self, value: float, timestamp: datetime | None = None):
        """Record a metric value for trend analysis."""
        ts = timestamp or datetime.now()
        self.value_history.append((ts, value))

        # Trim history if needed
        if len(self.value_history) > self.max_history_size:
            self.value_history = self.value_history[-self.max_history_size :]

        self.last_checked = ts

    def get_trend(self) -> str:
        """Analyze recent trend in values."""
        if len(self.value_history) < 3:
            return "insufficient_data"

        recent = [v for _, v in self.value_history[-10:]]

        if len(recent) < 3:
            return "insufficient_data"

        # Check trend direction
        first_half = statistics.mean(recent[: len(recent) // 2])
        second_half = statistics.mean(recent[len(recent) // 2 :])

        diff = second_half - first_half
        threshold = self.setpoint.tolerance * self.setpoint.target_value

        if abs(diff) < threshold:
            return "stable"
        elif diff > 0:
            return "increasing"
        else:
            return "decreasing"

    def is_improving(self) -> bool:
        """Check if values are trending toward setpoint."""
        if len(self.value_history) < 2:
            return True

        recent = [v for _, v in self.value_history[-5:]]
        target = self.setpoint.target_value

        # Calculate average distance from target
        first_distance = abs(recent[0] - target)
        last_distance = abs(recent[-1] - target)

        return last_distance < first_distance

    def get_volatility(self, window_size: int = 20) -> float:
        """
        Calculate coefficient of variation (volatility) of recent values.

        Higher values indicate more instability. A stable system typically
        has volatility < 0.1 (10% coefficient of variation).

        Args:
            window_size: Number of recent values to analyze

        Returns:
            Coefficient of variation (std_dev / mean), or 0 if insufficient data
        """
        if len(self.value_history) < 3:
            return 0.0

        recent_values = [v for _, v in self.value_history[-window_size:]]
        if len(recent_values) < 3:
            return 0.0

        mean_val = statistics.mean(recent_values)
        if mean_val == 0:
            return 0.0

        std_dev = statistics.stdev(recent_values)
        return std_dev / abs(mean_val)

    def get_jitter(self, window_size: int = 20) -> float:
        """
        Calculate jitter (oscillation frequency) of recent values.

        Jitter measures how often values change direction. High jitter
        indicates unstable oscillation around a value, even if the mean
        appears stable.

        Args:
            window_size: Number of recent values to analyze

        Returns:
            Jitter as ratio of direction changes to observations (0-1)
        """
        if len(self.value_history) < 3:
            return 0.0

        recent_values = [v for _, v in self.value_history[-window_size:]]
        if len(recent_values) < 3:
            return 0.0

        # Count direction changes
        direction_changes = 0
        for i in range(2, len(recent_values)):
            prev_delta = recent_values[i - 1] - recent_values[i - 2]
            curr_delta = recent_values[i] - recent_values[i - 1]
            # Direction change if sign flips
            if prev_delta * curr_delta < 0:
                direction_changes += 1

        return direction_changes / (len(recent_values) - 2)

    def get_momentum(self, window_size: int = 10) -> float:
        """
        Calculate momentum (rate of change) of recent values.

        Positive momentum means values are increasing, negative means decreasing.
        Normalized by the setpoint tolerance for comparability.

        Args:
            window_size: Number of recent values to analyze

        Returns:
            Normalized rate of change (positive = increasing, negative = decreasing)
        """
        if len(self.value_history) < 2:
            return 0.0

        recent = self.value_history[-window_size:]
        if len(recent) < 2:
            return 0.0

        # Simple linear regression slope
        n = len(recent)
        x_vals = list(range(n))
        y_vals = [v for _, v in recent]

        x_mean = sum(x_vals) / n
        y_mean = sum(y_vals) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)

        if denominator == 0:
            return 0.0

        slope = numerator / denominator

        # Normalize by tolerance threshold
        tolerance_value = self.setpoint.tolerance * self.setpoint.target_value
        if tolerance_value > 0:
            return slope / tolerance_value
        return slope

    def get_distance_to_criticality(self) -> float:
        """
        Calculate normalized distance to critical threshold.

        Returns a value between 0 (at critical) and 1 (at setpoint).
        Values near 0 indicate approaching a phase transition.

        Returns:
            Distance to criticality (0 = critical, 1 = at target)
        """
        if len(self.value_history) < 1:
            return 1.0

        current_value = self.value_history[-1][1]
        target = self.setpoint.target_value
        critical_threshold = (
            self.setpoint.tolerance * 5 * target
        )  # 5x tolerance = CRITICAL

        deviation = abs(current_value - target)
        if critical_threshold == 0:
            return 1.0

        # Normalize: 0 = at critical threshold, 1 = at target
        distance = max(0.0, 1.0 - (deviation / critical_threshold))
        return distance

    def get_volatility_metrics(self) -> VolatilityMetrics:
        """
        Get comprehensive volatility analysis.

        Combines volatility, jitter, momentum, and distance to criticality
        into a single assessment of system stability.

        Returns:
            VolatilityMetrics with all volatility indicators
        """
        volatility = self.get_volatility()
        jitter = self.get_jitter()
        momentum = self.get_momentum()
        distance = self.get_distance_to_criticality()

        # Determine volatility level based on multiple factors
        # Higher volatility + high jitter + low distance = more critical
        risk_score = (
            volatility * 2.0  # Variance is primary indicator
            + jitter * 1.5  # Oscillation amplifies risk
            + (1.0 - distance) * 1.0  # Proximity to threshold
        )

        if risk_score < 0.2:
            level = VolatilityLevel.STABLE
        elif risk_score < 0.5:
            level = VolatilityLevel.NORMAL
        elif risk_score < 1.0:
            level = VolatilityLevel.ELEVATED
        elif risk_score < 1.5:
            level = VolatilityLevel.HIGH
        else:
            level = VolatilityLevel.CRITICAL

        return VolatilityMetrics(
            volatility=volatility,
            jitter=jitter,
            momentum=momentum,
            distance_to_critical=distance,
            level=level,
        )


@dataclass
class CorrectiveAction:
    """A corrective action triggered by feedback loop deviation."""

    id: UUID
    feedback_loop_id: UUID
    action_type: CorrectiveActionType
    description: str
    triggered_at: datetime
    deviation_severity: DeviationSeverity
    deviation_amount: float
    target_value: float
    actual_value: float

    # Outcome tracking
    executed: bool = False
    execution_result: str | None = None
    effective: bool | None = None


@dataclass
class AllostasisMetrics:
    """
    Allostatic load metrics for a faculty member or the system.

    Allostatic load is the cumulative cost of chronic stress adaptation.
    Even if the system "handles" each crisis, the biological/organizational
    cost accumulates until sudden failure.
    """

    id: UUID
    entity_id: UUID  # Faculty ID or system UUID
    entity_type: str  # "faculty" or "system"
    calculated_at: datetime

    # Stress factors (weighted)
    consecutive_weekend_calls: int = 0
    nights_past_month: int = 0
    schedule_changes_absorbed: int = 0
    holidays_worked_this_year: int = 0
    overtime_hours_month: float = 0.0
    coverage_gap_responses: int = 0
    cross_coverage_events: int = 0

    # Calculated scores
    acute_stress_score: float = 0.0  # Recent/immediate stress
    chronic_stress_score: float = 0.0  # Accumulated over time
    total_allostatic_load: float = 0.0

    # Thresholds
    warning_threshold: float = 50.0
    critical_threshold: float = 80.0

    def calculate(self):
        """Calculate allostatic load from component factors."""
        # Acute stress (recent, higher weight)
        self.acute_stress_score = (
            self.consecutive_weekend_calls * 4.0
            + self.nights_past_month * 2.0
            + self.schedule_changes_absorbed * 1.5
            + self.coverage_gap_responses * 2.0
        )

        # Chronic stress (accumulated)
        self.chronic_stress_score = (
            self.holidays_worked_this_year * 5.0
            + self.overtime_hours_month * 0.5
            + self.cross_coverage_events * 1.0
        )

        # Total with chronic stress having more weight long-term
        self.total_allostatic_load = self.acute_stress_score + (
            self.chronic_stress_score * 1.2
        )

    @property
    def state(self) -> AllostasisState:
        """Determine current allostatic state."""
        if self.total_allostatic_load < self.warning_threshold * 0.5:
            return AllostasisState.HOMEOSTASIS
        elif self.total_allostatic_load < self.warning_threshold:
            return AllostasisState.ALLOSTASIS
        elif self.total_allostatic_load < self.critical_threshold:
            return AllostasisState.ALLOSTATIC_LOAD
        else:
            return AllostasisState.ALLOSTATIC_OVERLOAD

    @property
    def risk_level(self) -> str:
        """Get human-readable risk level."""
        state = self.state
        if state == AllostasisState.HOMEOSTASIS:
            return "low"
        elif state == AllostasisState.ALLOSTASIS:
            return "moderate"
        elif state == AllostasisState.ALLOSTATIC_LOAD:
            return "high"
        else:
            return "critical"


@dataclass
class PositiveFeedbackRisk:
    """
    A detected positive feedback loop risk.

    Positive feedback loops amplify deviation and destabilize systems.
    We detect these patterns and recommend interventions.
    """

    id: UUID
    name: str
    description: str
    detected_at: datetime

    # The loop pattern
    trigger: str  # What starts the loop
    amplification: str  # How it gets worse
    consequence: str  # End result if unchecked

    # Detection metrics
    evidence: list[str]
    confidence: float  # 0.0 - 1.0
    severity: DeviationSeverity

    # Recommended intervention
    intervention: str
    urgency: str  # "immediate", "soon", "monitor"


@dataclass
class VolatilityAlert:
    """
    Alert for high volatility in a feedback loop.

    High volatility often precedes system instability (bifurcation).
    These alerts trigger before threshold crossings to enable proactive response.
    """

    id: UUID
    feedback_loop_name: str
    detected_at: datetime
    volatility_metrics: VolatilityMetrics

    # Alert details
    description: str
    evidence: list[str]
    severity: DeviationSeverity

    # Recommended action
    intervention: str
    urgency: str  # "immediate", "soon", "monitor"


@dataclass
class HomeostasisStatus:
    """Overall homeostasis status for the system."""

    timestamp: datetime
    overall_state: AllostasisState
    feedback_loops_healthy: int
    feedback_loops_deviating: int
    feedback_loops_volatile: int  # NEW: loops with high volatility
    active_corrections: int
    positive_feedback_risks: int
    volatility_alerts: int  # NEW: count of volatility alerts
    average_allostatic_load: float
    recommendations: list[str]


class HomeostasisMonitor:
    """
    Monitors system homeostasis through feedback loops.

    Implements the biological concept of homeostasis:
    - Maintains setpoints through negative feedback
    - Detects positive feedback risks
    - Tracks allostatic load
    - Triggers corrective actions
    """

    def __init__(self):
        self.feedback_loops: dict[UUID, FeedbackLoop] = {}
        self.setpoints: dict[UUID, Setpoint] = {}
        self.allostasis_metrics: dict[UUID, AllostasisMetrics] = {}
        self.positive_feedback_risks: list[PositiveFeedbackRisk] = []
        self.volatility_alerts: list[VolatilityAlert] = []  # NEW
        self.corrective_actions: list[CorrectiveAction] = []
        self.correction_handlers: dict[CorrectiveActionType, Callable] = {}

        # Initialize default setpoints
        self._initialize_default_setpoints()

    def _initialize_default_setpoints(self):
        """Initialize default setpoints for scheduling metrics."""
        default_setpoints = [
            Setpoint(
                id=uuid4(),
                name="coverage_rate",
                description="Target coverage rate for scheduled blocks",
                target_value=0.95,
                tolerance=0.05,
                unit="ratio",
                minimum=0.0,
                maximum=1.0,
                is_critical=True,
            ),
            Setpoint(
                id=uuid4(),
                name="faculty_utilization",
                description="Target faculty utilization rate",
                target_value=0.75,  # Below 80% threshold
                tolerance=0.10,
                unit="ratio",
                minimum=0.0,
                maximum=1.0,
                is_critical=True,
            ),
            Setpoint(
                id=uuid4(),
                name="workload_balance",
                description="Standard deviation of workload across faculty",
                target_value=0.15,  # Low variance is good
                tolerance=0.05,
                unit="std_dev",
                minimum=0.0,
                maximum=1.0,
                is_critical=False,
            ),
            Setpoint(
                id=uuid4(),
                name="schedule_stability",
                description="Rate of schedule changes vs planned",
                target_value=0.95,  # 95% of schedule unchanged
                tolerance=0.05,
                unit="ratio",
                minimum=0.0,
                maximum=1.0,
                is_critical=False,
            ),
            Setpoint(
                id=uuid4(),
                name="acgme_compliance",
                description="ACGME duty hour compliance rate",
                target_value=1.0,
                tolerance=0.02,
                unit="ratio",
                minimum=0.0,
                maximum=1.0,
                is_critical=True,
            ),
        ]

        for sp in default_setpoints:
            self.setpoints[sp.id] = sp

            # Create feedback loop for each setpoint
            loop = FeedbackLoop(
                id=uuid4(),
                name=f"{sp.name}_feedback",
                description=f"Negative feedback loop for {sp.description}",
                setpoint=sp,
                feedback_type=FeedbackType.NEGATIVE,
            )
            self.feedback_loops[loop.id] = loop

    def register_correction_handler(
        self,
        action_type: CorrectiveActionType,
        handler: Callable[[CorrectiveAction], bool],
    ):
        """Register a handler for a type of corrective action."""
        self.correction_handlers[action_type] = handler
        logger.info(f"Registered correction handler for {action_type.value}")

    def check_feedback_loop(
        self,
        loop_id: UUID,
        current_value: float,
    ) -> CorrectiveAction | None:
        """
        Check a feedback loop and trigger correction if needed.

        This is the core homeostasis mechanism: detect deviation from
        setpoint and trigger corrective action to restore equilibrium.
        Like a thermostat, it continuously monitors and adjusts.

        Args:
            loop_id: UUID of the feedback loop to check.
            current_value: Current value of the monitored metric.

        Returns:
            CorrectiveAction: If deviation requires correction, returns the
                action taken (or to be taken).
            None: If metric is within tolerance and no action needed.

        Example:
            >>> monitor = HomeostasisMonitor()
            >>> loop = monitor.get_feedback_loop("coverage_rate")
            >>> action = monitor.check_feedback_loop(loop.id, 0.82)
            >>> if action:
            ...     print(f"Correction needed: {action.action_type.value}")
        """
        loop = self.feedback_loops.get(loop_id)
        if not loop or not loop.is_active:
            return None

        # Record value
        loop.record_value(current_value)

        # Check deviation
        deviation, severity = loop.setpoint.check_deviation(current_value)

        if severity == DeviationSeverity.NONE:
            loop.consecutive_deviations = 0
            return None

        loop.consecutive_deviations += 1

        # Determine if correction needed
        if severity in (DeviationSeverity.MAJOR, DeviationSeverity.CRITICAL):
            return self._trigger_correction(loop, current_value, deviation, severity)

        # For minor/moderate, check for persistent deviation
        if loop.consecutive_deviations >= 3:
            return self._trigger_correction(loop, current_value, deviation, severity)

        return None

    def _trigger_correction(
        self,
        loop: FeedbackLoop,
        current_value: float,
        deviation: float,
        severity: DeviationSeverity,
    ) -> CorrectiveAction:
        """Trigger a corrective action for a feedback loop."""
        # Determine action type based on setpoint and severity
        action_type = self._determine_action_type(loop.setpoint, severity)

        action = CorrectiveAction(
            id=uuid4(),
            feedback_loop_id=loop.id,
            action_type=action_type,
            description=self._get_correction_description(loop, action_type, severity),
            triggered_at=datetime.now(),
            deviation_severity=severity,
            deviation_amount=deviation,
            target_value=loop.setpoint.target_value,
            actual_value=current_value,
        )

        # Execute if handler registered
        handler = self.correction_handlers.get(action_type)
        if handler:
            try:
                action.executed = True
                action.effective = handler(action)
                action.execution_result = (
                    "success" if action.effective else "ineffective"
                )
            except Exception as e:
                action.execution_result = f"error: {e}"
                logger.error(f"Correction handler failed: {e}")
        else:
            action.execution_result = "no_handler"

        self.corrective_actions.append(action)
        loop.last_correction = datetime.now()
        loop.total_corrections += 1

        logger.warning(
            f"Corrective action triggered: {action_type.value} for {loop.name} "
            f"(deviation: {severity.value}, value: {current_value:.2f})"
        )

        return action

    def _determine_action_type(
        self,
        setpoint: Setpoint,
        severity: DeviationSeverity,
    ) -> CorrectiveActionType:
        """Determine appropriate corrective action type."""
        if severity == DeviationSeverity.CRITICAL:
            if setpoint.name in ("coverage_rate", "acgme_compliance"):
                return CorrectiveActionType.RECRUIT_BACKUP
            return CorrectiveActionType.REDUCE_SCOPE

        if severity == DeviationSeverity.MAJOR:
            if setpoint.name == "workload_balance":
                return CorrectiveActionType.REDISTRIBUTE
            if setpoint.name == "faculty_utilization":
                return CorrectiveActionType.DEFER_ACTIVITY
            return CorrectiveActionType.PROTECT_RESOURCE

        return CorrectiveActionType.ALERT_ONLY

    def _get_correction_description(
        self,
        loop: FeedbackLoop,
        action_type: CorrectiveActionType,
        severity: DeviationSeverity,
    ) -> str:
        """Generate description for corrective action."""
        descriptions = {
            CorrectiveActionType.REDISTRIBUTE: f"Redistributing workload to correct {loop.name} deviation",
            CorrectiveActionType.RECRUIT_BACKUP: f"Recruiting backup coverage for {loop.name}",
            CorrectiveActionType.DEFER_ACTIVITY: f"Deferring non-critical activities due to {loop.name}",
            CorrectiveActionType.PROTECT_RESOURCE: f"Protecting overloaded resources ({loop.name})",
            CorrectiveActionType.REDUCE_SCOPE: f"Reducing service scope due to critical {loop.name} deviation",
            CorrectiveActionType.ALERT_ONLY: f"Alert: {loop.name} showing {severity.value} deviation",
        }
        return descriptions.get(action_type, f"Correcting {loop.name}")

    def calculate_allostatic_load(
        self,
        entity_id: UUID,
        entity_type: str,
        stress_factors: dict,
    ) -> AllostasisMetrics:
        """
        Calculate allostatic load for an entity.

        Args:
            entity_id: Faculty or system ID
            entity_type: "faculty" or "system"
            stress_factors: Dict of stress factor values

        Returns:
            Calculated AllostasisMetrics
        """
        metrics = AllostasisMetrics(
            id=uuid4(),
            entity_id=entity_id,
            entity_type=entity_type,
            calculated_at=datetime.now(),
            consecutive_weekend_calls=stress_factors.get(
                "consecutive_weekend_calls", 0
            ),
            nights_past_month=stress_factors.get("nights_past_month", 0),
            schedule_changes_absorbed=stress_factors.get(
                "schedule_changes_absorbed", 0
            ),
            holidays_worked_this_year=stress_factors.get(
                "holidays_worked_this_year", 0
            ),
            overtime_hours_month=stress_factors.get("overtime_hours_month", 0.0),
            coverage_gap_responses=stress_factors.get("coverage_gap_responses", 0),
            cross_coverage_events=stress_factors.get("cross_coverage_events", 0),
        )

        metrics.calculate()
        self.allostasis_metrics[entity_id] = metrics

        return metrics

    def detect_positive_feedback_risks(
        self,
        faculty_metrics: list[AllostasisMetrics],
        system_metrics: dict,
    ) -> list[PositiveFeedbackRisk]:
        """
        Detect potential positive feedback loops.

        Positive feedback loops amplify deviation instead of correcting it,
        leading to runaway destabilization. Key patterns detected:
        - Burnout cascade: Burnout → Sick calls → More work → More burnout
        - Coverage spiral: Low coverage → Errors → Investigations → Less coverage
        - Attrition cascade: Departures → Overload → More departures

        Args:
            faculty_metrics: List of AllostasisMetrics for each faculty member.
            system_metrics: Dict of system-level metrics including:
                - coverage_rate: Current coverage rate (0.0 to 1.0)

        Returns:
            list[PositiveFeedbackRisk]: Detected risks with interventions.
                Each risk includes trigger, amplification mechanism,
                consequence, and recommended intervention.

        Example:
            >>> monitor = HomeostasisMonitor()
            >>> faculty_load = [monitor.calculate_allostatic_load(f.id, "faculty", {...}) for f in faculty]
            >>> risks = monitor.detect_positive_feedback_risks(faculty_load, {"coverage_rate": 0.80})
            >>> urgent = [r for r in risks if r.urgency == "immediate"]
            >>> if urgent:
            ...     print(f"URGENT: {urgent[0].name} - {urgent[0].intervention}")
        """
        risks = []

        # Check for burnout cascade
        high_load_count = sum(
            1
            for m in faculty_metrics
            if m.state
            in (AllostasisState.ALLOSTATIC_LOAD, AllostasisState.ALLOSTATIC_OVERLOAD)
        )
        if high_load_count > 0:
            high_load_ratio = (
                high_load_count / len(faculty_metrics) if faculty_metrics else 0
            )
            if high_load_ratio > 0.3:  # >30% faculty with high allostatic load
                risks.append(
                    PositiveFeedbackRisk(
                        id=uuid4(),
                        name="burnout_cascade",
                        description="High allostatic load may trigger burnout cascade",
                        detected_at=datetime.now(),
                        trigger="Multiple faculty with high stress load",
                        amplification="Burnout leads to sick calls, increasing load on others",
                        consequence="Accelerating departures and system collapse",
                        evidence=[
                            f"{high_load_count}/{len(faculty_metrics)} faculty with high allostatic load",
                            f"High load ratio: {high_load_ratio:.0%}",
                        ],
                        confidence=min(0.95, high_load_ratio + 0.4),
                        severity=(
                            DeviationSeverity.CRITICAL
                            if high_load_ratio > 0.5
                            else DeviationSeverity.MAJOR
                        ),
                        intervention="Immediately reduce workload for highest-load faculty, consider temporary service reduction",
                        urgency="immediate" if high_load_ratio > 0.5 else "soon",
                    )
                )

        # Check for coverage gap spiral
        coverage_rate = system_metrics.get("coverage_rate", 1.0)
        if coverage_rate < 0.85:
            risks.append(
                PositiveFeedbackRisk(
                    id=uuid4(),
                    name="coverage_spiral",
                    description="Low coverage may trigger quality/error spiral",
                    detected_at=datetime.now(),
                    trigger=f"Coverage at {coverage_rate:.0%}",
                    amplification="Low coverage leads to errors, investigations take time away",
                    consequence="Further coverage degradation, potential accreditation issues",
                    evidence=[
                        f"Coverage rate: {coverage_rate:.0%}",
                        "Below safe threshold of 85%",
                    ],
                    confidence=0.7,
                    severity=DeviationSeverity.MAJOR,
                    intervention="Activate backup coverage immediately, consider fallback schedule",
                    urgency="immediate",
                )
            )

        # Check for attrition cascade
        avg_load = (
            statistics.mean([m.total_allostatic_load for m in faculty_metrics])
            if faculty_metrics
            else 0
        )

        if avg_load > 60:  # High system-wide stress
            risks.append(
                PositiveFeedbackRisk(
                    id=uuid4(),
                    name="attrition_cascade",
                    description="High system stress may trigger departure cascade",
                    detected_at=datetime.now(),
                    trigger=f"Average allostatic load: {avg_load:.1f}",
                    amplification="High stress causes departures, remaining faculty take on more",
                    consequence="Self-reinforcing departure cycle, program viability at risk",
                    evidence=[
                        f"Average faculty stress: {avg_load:.1f}",
                        "Above warning threshold of 60",
                    ],
                    confidence=0.6,
                    severity=DeviationSeverity.MAJOR,
                    intervention="Review workload distribution, consider service reduction, protect high-risk faculty",
                    urgency="soon",
                )
            )

        self.positive_feedback_risks = risks
        return risks

    def detect_volatility_risks(self) -> list[VolatilityAlert]:
        """
        Detect high volatility in feedback loops.

        High volatility often precedes phase transitions (bifurcations) where
        the system suddenly shifts to a new state. This provides early warning
        before threshold crossings occur.

        Returns:
            List of volatility alerts for unstable loops
        """
        alerts = []

        for loop in self.feedback_loops.values():
            if not loop.is_active or len(loop.value_history) < 5:
                continue

            metrics = loop.get_volatility_metrics()

            # Generate alert if volatility is concerning
            if metrics.is_warning:
                evidence = []

                if metrics.volatility > 0.15:
                    evidence.append(
                        f"High variance: {metrics.volatility:.1%} coefficient of variation"
                    )
                if metrics.jitter > 0.5:
                    evidence.append(
                        f"High oscillation: {metrics.jitter:.1%} direction changes"
                    )
                if metrics.distance_to_critical < 0.3:
                    evidence.append(
                        f"Near critical threshold: {metrics.distance_to_critical:.1%} margin"
                    )
                if abs(metrics.momentum) > 1.0:
                    direction = "increasing" if metrics.momentum > 0 else "decreasing"
                    evidence.append(
                        f"Rapid {direction}: {abs(metrics.momentum):.1f}x tolerance/interval"
                    )

                # Determine severity and urgency
                if metrics.level == VolatilityLevel.CRITICAL:
                    severity = DeviationSeverity.CRITICAL
                    urgency = "immediate"
                    intervention = (
                        f"CRITICAL: {loop.setpoint.name} showing phase transition indicators. "
                        "Freeze non-essential changes, activate contingency protocols."
                    )
                elif metrics.level == VolatilityLevel.HIGH:
                    severity = DeviationSeverity.MAJOR
                    urgency = "soon"
                    intervention = (
                        f"{loop.setpoint.name} unstable. Review recent changes, "
                        "consider reverting to last stable configuration."
                    )
                else:  # ELEVATED
                    severity = DeviationSeverity.MODERATE
                    urgency = "monitor"
                    intervention = (
                        f"{loop.setpoint.name} showing elevated volatility. "
                        "Increase monitoring frequency, prepare contingencies."
                    )

                alert = VolatilityAlert(
                    id=uuid4(),
                    feedback_loop_name=loop.name,
                    detected_at=datetime.now(),
                    volatility_metrics=metrics,
                    description=f"High volatility detected in {loop.setpoint.name}",
                    evidence=evidence,
                    severity=severity,
                    intervention=intervention,
                    urgency=urgency,
                )
                alerts.append(alert)

                logger.warning(
                    f"Volatility alert: {loop.setpoint.name} at {metrics.level.value} "
                    f"(volatility={metrics.volatility:.2f}, jitter={metrics.jitter:.2f})"
                )

        self.volatility_alerts = alerts
        return alerts

    def check_all_loops(
        self,
        current_values: dict[str, float],
    ) -> list[CorrectiveAction]:
        """
        Check all feedback loops with current values.

        Args:
            current_values: Dict of setpoint_name -> current_value

        Returns:
            List of corrective actions triggered
        """
        actions = []

        for loop in self.feedback_loops.values():
            if loop.setpoint.name in current_values:
                value = current_values[loop.setpoint.name]
                action = self.check_feedback_loop(loop.id, value)
                if action:
                    actions.append(action)

        return actions

    def get_status(
        self,
        faculty_metrics: list[AllostasisMetrics] | None = None,
    ) -> HomeostasisStatus:
        """
        Get overall homeostasis status.

        Args:
            faculty_metrics: Optional list of faculty metrics for load calculation

        Returns:
            HomeostasisStatus summary
        """
        # Count loop states
        healthy = 0
        deviating = 0
        volatile = 0
        for loop in self.feedback_loops.values():
            if loop.consecutive_deviations > 0:
                deviating += 1
            else:
                healthy += 1
            # Check volatility
            if len(loop.value_history) >= 5:
                vol_metrics = loop.get_volatility_metrics()
                if vol_metrics.is_warning:
                    volatile += 1

        # Calculate average allostatic load
        if faculty_metrics:
            avg_load = statistics.mean(
                [m.total_allostatic_load for m in faculty_metrics]
            )
        else:
            avg_load = (
                statistics.mean(
                    [m.total_allostatic_load for m in self.allostasis_metrics.values()]
                )
                if self.allostasis_metrics
                else 0.0
            )

        # Determine overall state (volatility can escalate state)
        if avg_load > 80:
            overall_state = AllostasisState.ALLOSTATIC_OVERLOAD
        elif avg_load > 50 or volatile > len(self.feedback_loops) // 2:
            overall_state = AllostasisState.ALLOSTATIC_LOAD
        elif deviating > healthy or volatile > 0:
            overall_state = AllostasisState.ALLOSTASIS
        else:
            overall_state = AllostasisState.HOMEOSTASIS

        # Build recommendations
        recommendations = []
        if overall_state == AllostasisState.ALLOSTATIC_OVERLOAD:
            recommendations.append(
                "CRITICAL: System in allostatic overload - immediate intervention required"
            )
            recommendations.append("Activate load shedding to RED or BLACK level")
        elif overall_state == AllostasisState.ALLOSTATIC_LOAD:
            recommendations.append(
                "System accumulating stress - review workload distribution"
            )
            recommendations.append(
                "Protect high-load faculty from additional assignments"
            )
        elif overall_state == AllostasisState.ALLOSTASIS:
            recommendations.append(
                "System actively compensating - monitor for sustained deviation"
            )

        for risk in self.positive_feedback_risks:
            if risk.urgency == "immediate":
                recommendations.append(f"URGENT: {risk.intervention}")

        # Add volatility-based recommendations
        for alert in self.volatility_alerts:
            if alert.urgency == "immediate":
                recommendations.append(f"VOLATILITY ALERT: {alert.intervention}")
            elif alert.urgency == "soon" and len(recommendations) < 5:
                recommendations.append(
                    f"Volatility warning: {alert.feedback_loop_name} unstable"
                )

        return HomeostasisStatus(
            timestamp=datetime.now(),
            overall_state=overall_state,
            feedback_loops_healthy=healthy,
            feedback_loops_deviating=deviating,
            feedback_loops_volatile=volatile,
            active_corrections=len([a for a in self.corrective_actions if a.executed]),
            positive_feedback_risks=len(self.positive_feedback_risks),
            volatility_alerts=len(self.volatility_alerts),
            average_allostatic_load=avg_load,
            recommendations=recommendations,
        )

    def get_setpoint(self, name: str) -> Setpoint | None:
        """Get a setpoint by name."""
        for sp in self.setpoints.values():
            if sp.name == name:
                return sp
        return None

    def get_feedback_loop(self, setpoint_name: str) -> FeedbackLoop | None:
        """Get feedback loop for a setpoint."""
        for loop in self.feedback_loops.values():
            if loop.setpoint.name == setpoint_name:
                return loop
        return None
