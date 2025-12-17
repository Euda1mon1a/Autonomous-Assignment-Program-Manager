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

This module implements:
1. Negative feedback loops for coverage, workload, and quality metrics
2. Detection of positive feedback (burnout spirals, attrition cascades)
3. Allostatic load tracking (cumulative stress cost)
4. Setpoint management and deviation monitoring
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
    NONE = "none"          # Within tolerance
    MINOR = "minor"        # Slight deviation
    MODERATE = "moderate"  # Noticeable deviation
    MAJOR = "major"        # Significant deviation
    CRITICAL = "critical"  # System stability threatened


class CorrectiveActionType(str, Enum):
    """Types of corrective actions."""
    REDISTRIBUTE = "redistribute"      # Redistribute workload
    RECRUIT_BACKUP = "recruit_backup"  # Bring in backup coverage
    DEFER_ACTIVITY = "defer_activity"  # Postpone non-critical work
    PROTECT_RESOURCE = "protect_resource"  # Shield overloaded faculty
    REDUCE_SCOPE = "reduce_scope"      # Reduce service scope
    ALERT_ONLY = "alert_only"          # Just notify, no automatic action


class AllostasisState(str, Enum):
    """Allostatic state of the system."""
    HOMEOSTASIS = "homeostasis"  # Stable, within normal operating range
    ALLOSTASIS = "allostasis"    # Actively compensating for stress
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
        relative_deviation = deviation / self.target_value if self.target_value > 0 else deviation

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
            self.value_history = self.value_history[-self.max_history_size:]

        self.last_checked = ts

    def get_trend(self) -> str:
        """Analyze recent trend in values."""
        if len(self.value_history) < 3:
            return "insufficient_data"

        recent = [v for _, v in self.value_history[-10:]]

        if len(recent) < 3:
            return "insufficient_data"

        # Check trend direction
        first_half = statistics.mean(recent[:len(recent)//2])
        second_half = statistics.mean(recent[len(recent)//2:])

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
    acute_stress_score: float = 0.0    # Recent/immediate stress
    chronic_stress_score: float = 0.0  # Accumulated over time
    total_allostatic_load: float = 0.0

    # Thresholds
    warning_threshold: float = 50.0
    critical_threshold: float = 80.0

    def calculate(self):
        """Calculate allostatic load from component factors."""
        # Acute stress (recent, higher weight)
        self.acute_stress_score = (
            self.consecutive_weekend_calls * 4.0 +
            self.nights_past_month * 2.0 +
            self.schedule_changes_absorbed * 1.5 +
            self.coverage_gap_responses * 2.0
        )

        # Chronic stress (accumulated)
        self.chronic_stress_score = (
            self.holidays_worked_this_year * 5.0 +
            self.overtime_hours_month * 0.5 +
            self.cross_coverage_events * 1.0
        )

        # Total with chronic stress having more weight long-term
        self.total_allostatic_load = self.acute_stress_score + (self.chronic_stress_score * 1.2)

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
    trigger: str           # What starts the loop
    amplification: str     # How it gets worse
    consequence: str       # End result if unchecked

    # Detection metrics
    evidence: list[str]
    confidence: float  # 0.0 - 1.0
    severity: DeviationSeverity

    # Recommended intervention
    intervention: str
    urgency: str  # "immediate", "soon", "monitor"


@dataclass
class HomeostasisStatus:
    """Overall homeostasis status for the system."""
    timestamp: datetime
    overall_state: AllostasisState
    feedback_loops_healthy: int
    feedback_loops_deviating: int
    active_corrections: int
    positive_feedback_risks: int
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

        Args:
            loop_id: ID of the feedback loop to check
            current_value: Current value of the monitored metric

        Returns:
            CorrectiveAction if correction triggered, None otherwise
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
                action.execution_result = "success" if action.effective else "ineffective"
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
            consecutive_weekend_calls=stress_factors.get("consecutive_weekend_calls", 0),
            nights_past_month=stress_factors.get("nights_past_month", 0),
            schedule_changes_absorbed=stress_factors.get("schedule_changes_absorbed", 0),
            holidays_worked_this_year=stress_factors.get("holidays_worked_this_year", 0),
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

        Positive feedback loops amplify problems:
        - Burnout -> Sick calls -> More work -> More burnout
        - Short-staffing -> Errors -> Investigations -> More short-staffing
        - Senior faculty leave -> Juniors overloaded -> Juniors leave

        Args:
            faculty_metrics: List of faculty allostatic metrics
            system_metrics: System-level metrics dict

        Returns:
            List of detected positive feedback risks
        """
        risks = []

        # Check for burnout cascade
        high_load_count = sum(
            1 for m in faculty_metrics
            if m.state in (AllostasisState.ALLOSTATIC_LOAD, AllostasisState.ALLOSTATIC_OVERLOAD)
        )
        if high_load_count > 0:
            high_load_ratio = high_load_count / len(faculty_metrics) if faculty_metrics else 0
            if high_load_ratio > 0.3:  # >30% faculty with high allostatic load
                risks.append(PositiveFeedbackRisk(
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
                    severity=DeviationSeverity.CRITICAL if high_load_ratio > 0.5 else DeviationSeverity.MAJOR,
                    intervention="Immediately reduce workload for highest-load faculty, consider temporary service reduction",
                    urgency="immediate" if high_load_ratio > 0.5 else "soon",
                ))

        # Check for coverage gap spiral
        coverage_rate = system_metrics.get("coverage_rate", 1.0)
        if coverage_rate < 0.85:
            risks.append(PositiveFeedbackRisk(
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
            ))

        # Check for attrition cascade
        avg_load = statistics.mean(
            [m.total_allostatic_load for m in faculty_metrics]
        ) if faculty_metrics else 0

        if avg_load > 60:  # High system-wide stress
            risks.append(PositiveFeedbackRisk(
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
            ))

        self.positive_feedback_risks = risks
        return risks

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
        for loop in self.feedback_loops.values():
            if loop.consecutive_deviations > 0:
                deviating += 1
            else:
                healthy += 1

        # Calculate average allostatic load
        if faculty_metrics:
            avg_load = statistics.mean(
                [m.total_allostatic_load for m in faculty_metrics]
            )
        else:
            avg_load = statistics.mean(
                [m.total_allostatic_load for m in self.allostasis_metrics.values()]
            ) if self.allostasis_metrics else 0.0

        # Determine overall state
        if avg_load > 80:
            overall_state = AllostasisState.ALLOSTATIC_OVERLOAD
        elif avg_load > 50:
            overall_state = AllostasisState.ALLOSTATIC_LOAD
        elif deviating > healthy:
            overall_state = AllostasisState.ALLOSTASIS
        else:
            overall_state = AllostasisState.HOMEOSTASIS

        # Build recommendations
        recommendations = []
        if overall_state == AllostasisState.ALLOSTATIC_OVERLOAD:
            recommendations.append("CRITICAL: System in allostatic overload - immediate intervention required")
            recommendations.append("Activate load shedding to RED or BLACK level")
        elif overall_state == AllostasisState.ALLOSTATIC_LOAD:
            recommendations.append("System accumulating stress - review workload distribution")
            recommendations.append("Protect high-load faculty from additional assignments")
        elif overall_state == AllostasisState.ALLOSTASIS:
            recommendations.append("System actively compensating - monitor for sustained deviation")

        for risk in self.positive_feedback_risks:
            if risk.urgency == "immediate":
                recommendations.append(f"URGENT: {risk.intervention}")

        return HomeostasisStatus(
            timestamp=datetime.now(),
            overall_state=overall_state,
            feedback_loops_healthy=healthy,
            feedback_loops_deviating=deviating,
            active_corrections=len([a for a in self.corrective_actions if a.executed]),
            positive_feedback_risks=len(self.positive_feedback_risks),
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
