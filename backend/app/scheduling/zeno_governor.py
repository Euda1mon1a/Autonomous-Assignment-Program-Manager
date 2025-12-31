"""
Quantum Zeno Effect Optimization Governor.

Prevents over-monitoring from freezing schedule optimization.

Physics basis: Frequent measurements collapse quantum wavefunction,
preventing transitions away from initial state. Evolution rate
decreases with measurement frequency.

Application: Manual schedule reviews "freeze" solver exploration,
trapping it in local optima. Limit interventions for better results.

Theoretical Foundation:
--------------------
In quantum mechanics, the Zeno effect states that a quantum system
that is continuously observed cannot evolve to a new state. The
measurement itself prevents transitions.

In scheduling optimization:
- Solver exploration = quantum state evolution
- Human review/intervention = measurement
- Assignment locks = wavefunction collapse
- Local optimum trapping = frozen initial state

Key Metrics:
-----------
1. Measurement Frequency: How often humans check/modify schedule
2. Frozen Ratio: % of assignments locked by human review
3. Evolution Prevention: Solver improvements blocked by locks
4. Local Optima Risk: Probability of being trapped in suboptimal solution
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


# Quantum Zeno Governor Constants
DEFAULT_MAX_CHECKS_PER_DAY = 3  # Default maximum schedule reviews per day
DEFAULT_MIN_INTERVAL_HOURS = 8  # Default minimum hours between interventions
DEFAULT_AUTO_LOCK_THRESHOLD = 0.95  # Default confidence threshold for auto-locking (95%)

# Zeno Risk Level Thresholds
LOW_RISK_MAX_INTERVENTIONS = 3  # Low risk: < 3 interventions/day
MODERATE_RISK_MAX_INTERVENTIONS = 6  # Moderate risk: 3-6 interventions/day
HIGH_RISK_MAX_INTERVENTIONS = 12  # High risk: 6-12 interventions/day

# Intervention Policy Configurations by Risk Level
LOW_RISK_MAX_CHECKS = 1
LOW_RISK_MIN_HOURS = 24
LOW_RISK_THRESHOLD = 0.99

MODERATE_RISK_MAX_CHECKS = 2
MODERATE_RISK_MIN_HOURS = 12
MODERATE_RISK_THRESHOLD = 0.97

HIGH_RISK_MAX_CHECKS = 3
HIGH_RISK_MIN_HOURS = 8
HIGH_RISK_THRESHOLD = 0.95

CRITICAL_RISK_MAX_CHECKS = 6
CRITICAL_RISK_MIN_HOURS = 4
CRITICAL_RISK_THRESHOLD = 0.90

# Monitoring Window Constants
DEFAULT_DURATION_HOURS = 8  # Default duration for optimization freedom window
DEFAULT_AVG_INTERVAL_HOURS = 24.0  # Default average interval between interventions


class ZenoRisk(str, Enum):
    """Risk level of Quantum Zeno effect freezing optimization."""

    LOW = "low"  # < 3 interventions/day, <10% frozen
    MODERATE = "moderate"  # 3-6 interventions/day, 10-25% frozen
    HIGH = "high"  # 6-12 interventions/day, 25-50% frozen
    CRITICAL = "critical"  # >12 interventions/day, >50% frozen


@dataclass
class InterventionPolicy:
    """Recommended intervention policy to prevent Zeno freezing."""

    max_checks_per_day: int = field(
        default=DEFAULT_MAX_CHECKS_PER_DAY, metadata={"description": "Maximum schedule reviews per day"}
    )
    min_interval_hours: int = field(
        default=DEFAULT_MIN_INTERVAL_HOURS, metadata={"description": "Minimum hours between interventions"}
    )
    recommended_windows: list[str] = field(
        default_factory=lambda: ["08:00-09:00", "14:00-15:00", "17:00-18:00"],
        metadata={"description": "Recommended time windows for reviews"},
    )
    hands_off_periods: list[dict[str, Any]] = field(
        default_factory=list,
        metadata={"description": "Periods when solver should run uninterrupted"},
    )
    auto_lock_threshold: float = field(
        default=DEFAULT_AUTO_LOCK_THRESHOLD,
        metadata={
            "description": "Confidence threshold for auto-locking assignments (0-1)"
        },
    )
    explanation: str = field(
        default="", metadata={"description": "Rationale for this policy"}
    )


@dataclass
class OptimizationFreedomWindow:
    """A period when solver should run without human intervention."""

    window_id: UUID = field(default_factory=uuid4)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(
        default_factory=lambda: datetime.now() + timedelta(hours=4)
    )
    reason: str = field(default="Allow solver exploration")
    is_active: bool = field(default=True)
    interventions_blocked: int = field(default=0)
    solver_improvements: int = field(default=0)
    final_score_improvement: float = field(default=0.0)


@dataclass
class ZenoMetrics:
    """Metrics for dashboard display of Zeno effect monitoring."""

    timestamp: datetime = field(default_factory=datetime.now)
    risk_level: ZenoRisk = field(default=ZenoRisk.LOW)

    # Measurement frequency metrics
    interventions_24h: int = field(default=0)
    interventions_7d: int = field(default=0)
    avg_interval_hours: float = field(default=24.0)
    measurement_frequency: float = field(
        default=0.0, metadata={"description": "Interventions per hour"}
    )

    # Frozen assignment metrics
    total_assignments: int = field(default=0)
    frozen_assignments: int = field(default=0)
    frozen_ratio: float = field(default=0.0)
    frozen_by_user: dict[str, int] = field(default_factory=dict)

    # Evolution prevention metrics
    evolution_prevented: int = field(
        default=0, metadata={"description": "Solver improvements blocked"}
    )
    local_optima_risk: float = field(
        default=0.0, metadata={"description": "Risk score 0.0-1.0"}
    )
    solver_attempts_blocked: int = field(default=0)
    last_successful_evolution: datetime | None = field(default=None)

    # Recommendations
    recommended_policy: InterventionPolicy = field(default_factory=InterventionPolicy)
    immediate_actions: list[str] = field(default_factory=list)
    watch_items: list[str] = field(default_factory=list)


@dataclass
class HumanIntervention:
    """Record of a human intervention in the schedule."""

    intervention_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: str = field(default="")
    assignments_reviewed: set[UUID] = field(default_factory=set)
    assignments_locked: set[UUID] = field(default_factory=set)
    assignments_modified: set[UUID] = field(default_factory=set)
    intervention_type: str = field(default="review")  # review, lock, modify, unlock
    reason: str = field(default="")


class ZenoGovernor:
    """
    Governor to prevent Quantum Zeno effect from freezing optimization.

    Tracks human interventions and provides recommendations to balance
    oversight with solver freedom.

    Usage:
        governor = ZenoGovernor()
        risk = await governor.log_human_intervention(
            checkpoint_time=datetime.now(),
            assignments_reviewed={uuid1, uuid2, uuid3}
        )
        if risk == ZenoRisk.CRITICAL:
            policy = governor.recommend_intervention_policy()
            # Apply policy restrictions
    """

    def __init__(self) -> None:
        """Initialize the Zeno Governor."""
        self.interventions: list[HumanIntervention] = []
        self.frozen_assignments: set[UUID] = set()
        self.total_assignments: int = 0
        self.freedom_windows: list[OptimizationFreedomWindow] = []
        self.solver_attempts: list[dict[str, Any]] = []
        self.locked_by_user: dict[str, set[UUID]] = defaultdict(set)

    async def log_human_intervention(
        self,
        checkpoint_time: datetime,
        assignments_reviewed: set[UUID],
        user_id: str = "unknown",
        assignments_locked: set[UUID] | None = None,
        assignments_modified: set[UUID] | None = None,
        intervention_type: str = "review",
        reason: str = "",
    ) -> ZenoRisk:
        """
        Log a human intervention and assess Zeno risk.

        Args:
            checkpoint_time: When the intervention occurred
            assignments_reviewed: Set of assignment IDs reviewed
            user_id: ID of user performing intervention
            assignments_locked: Set of assignment IDs locked (frozen)
            assignments_modified: Set of assignment IDs modified
            intervention_type: Type of intervention (review/lock/modify/unlock)
            reason: Reason for intervention

        Returns:
            ZenoRisk level after this intervention

        Example:
            risk = await governor.log_human_intervention(
                checkpoint_time=datetime.now(),
                assignments_reviewed={uuid1, uuid2},
                assignments_locked={uuid1},
                user_id="coordinator_123",
                intervention_type="lock",
                reason="ACGME compliance check"
            )
        """
        intervention = HumanIntervention(
            timestamp=checkpoint_time,
            user_id=user_id,
            assignments_reviewed=assignments_reviewed,
            assignments_locked=assignments_locked or set(),
            assignments_modified=assignments_modified or set(),
            intervention_type=intervention_type,
            reason=reason,
        )

        self.interventions.append(intervention)

        # Update frozen assignments tracking
        if assignments_locked:
            self.frozen_assignments.update(assignments_locked)
            self.locked_by_user[user_id].update(assignments_locked)

        # Calculate current risk level
        measurement_freq = self.compute_measurement_frequency()
        frozen_ratio = self.compute_frozen_assignments_ratio()

        # Risk thresholds
        if measurement_freq > 0.5 or frozen_ratio > 0.5:  # >12/day or >50% frozen
            return ZenoRisk.CRITICAL
        elif measurement_freq > 0.25 or frozen_ratio > 0.25:  # 6-12/day or 25-50%
            return ZenoRisk.HIGH
        elif measurement_freq > 0.125 or frozen_ratio > 0.10:  # 3-6/day or 10-25%
            return ZenoRisk.MODERATE
        else:
            return ZenoRisk.LOW

    def compute_measurement_frequency(
        self, time_window: timedelta = timedelta(hours=24)
    ) -> float:
        """
        Compute intervention frequency (measurements per hour).

        Args:
            time_window: Time window to analyze (default: 24 hours)

        Returns:
            Float representing interventions per hour

        Example:
            freq = governor.compute_measurement_frequency()
            # freq = 0.5 means 12 interventions per day (0.5 * 24)
        """
        if not self.interventions:
            return 0.0

        cutoff = datetime.now() - time_window
        recent_interventions = [i for i in self.interventions if i.timestamp >= cutoff]

        if not recent_interventions:
            return 0.0

        hours = time_window.total_seconds() / 3600
        return len(recent_interventions) / hours

    def compute_frozen_assignments_ratio(self) -> float:
        """
        Compute ratio of frozen (locked) assignments.

        Returns:
            Float 0.0-1.0 representing percentage of assignments frozen

        Example:
            ratio = governor.compute_frozen_assignments_ratio()
            # ratio = 0.35 means 35% of assignments are locked
        """
        if self.total_assignments == 0:
            return 0.0

        return len(self.frozen_assignments) / self.total_assignments

    def compute_local_optima_risk(self) -> float:
        """
        Compute risk of being trapped in local optimum.

        Risk factors:
        1. High frozen ratio (assignments can't be changed)
        2. High measurement frequency (solver can't explore)
        3. Time since last solver improvement
        4. Number of blocked solver attempts

        Returns:
            Float 0.0-1.0 risk score

        Example:
            risk = governor.compute_local_optima_risk()
            # risk = 0.8 means high probability of being trapped
        """
        frozen_ratio = self.compute_frozen_assignments_ratio()
        measurement_freq = self.compute_measurement_frequency()

        # Base risk from frozen ratio (0-0.5 range)
        risk = frozen_ratio * 0.5

        # Add risk from measurement frequency (0-0.3 range)
        # Normalize to 0-1, then scale
        freq_risk = min(measurement_freq / 1.0, 1.0) * 0.3
        risk += freq_risk

        # Add risk from blocked solver attempts (0-0.2 range)
        if self.solver_attempts:
            recent_attempts = [
                a
                for a in self.solver_attempts
                if datetime.now() - a.get("timestamp", datetime.now())
                < timedelta(days=1)
            ]
            blocked = sum(1 for a in recent_attempts if a.get("blocked", False))
            total = len(recent_attempts)
            if total > 0:
                block_ratio = blocked / total
                risk += block_ratio * 0.2

        return min(risk, 1.0)

    def recommend_intervention_policy(self) -> InterventionPolicy:
        """
        Recommend intervention policy based on current state.

        Returns:
            InterventionPolicy with recommended limits

        Example:
            policy = governor.recommend_intervention_policy()
            print(f"Max checks per day: {policy.max_checks_per_day}")
            print(f"Explanation: {policy.explanation}")
        """
        risk = self._assess_current_risk()
        frozen_ratio = self.compute_frozen_assignments_ratio()
        measurement_freq = self.compute_measurement_frequency()

        if risk == ZenoRisk.CRITICAL:
            return InterventionPolicy(
                max_checks_per_day=LOW_RISK_MAX_CHECKS,
                min_interval_hours=LOW_RISK_MIN_HOURS,
                recommended_windows=["09:00-10:00"],
                hands_off_periods=[
                    {
                        "start": "10:00",
                        "end": "09:00",
                        "duration_hours": 23,
                        "reason": "CRITICAL: Allow solver extended exploration time",
                    }
                ],
                auto_lock_threshold=LOW_RISK_THRESHOLD,
                explanation=(
                    f"CRITICAL Zeno risk detected. Frozen ratio: {frozen_ratio:.1%}, "
                    f"Intervention frequency: {measurement_freq:.2f}/hour. "
                    "Severely limit interventions to allow solver to escape local optimum."
                ),
            )

        elif risk == ZenoRisk.HIGH:
            return InterventionPolicy(
                max_checks_per_day=MODERATE_RISK_MAX_CHECKS,
                min_interval_hours=MODERATE_RISK_MIN_HOURS,
                recommended_windows=["09:00-10:00", "17:00-18:00"],
                hands_off_periods=[
                    {
                        "start": "10:00",
                        "end": "17:00",
                        "duration_hours": 7,
                        "reason": "HIGH risk: Morning solver exploration window",
                    }
                ],
                auto_lock_threshold=MODERATE_RISK_THRESHOLD,
                explanation=(
                    f"HIGH Zeno risk. Frozen ratio: {frozen_ratio:.1%}, "
                    f"Intervention frequency: {measurement_freq:.2f}/hour. "
                    "Reduce interventions to twice daily at fixed times."
                ),
            )

        elif risk == ZenoRisk.MODERATE:
            return InterventionPolicy(
                max_checks_per_day=HIGH_RISK_MAX_CHECKS,
                min_interval_hours=HIGH_RISK_MIN_HOURS,
                recommended_windows=["08:00-09:00", "14:00-15:00", "17:00-18:00"],
                hands_off_periods=[
                    {
                        "start": "09:00",
                        "end": "14:00",
                        "duration_hours": 5,
                        "reason": "MODERATE risk: Allow mid-day solver exploration",
                    }
                ],
                auto_lock_threshold=HIGH_RISK_THRESHOLD,
                explanation=(
                    f"MODERATE Zeno risk. Frozen ratio: {frozen_ratio:.1%}, "
                    f"Intervention frequency: {measurement_freq:.2f}/hour. "
                    "Limit interventions to 3x daily with 8+ hour spacing."
                ),
            )

        else:  # LOW risk
            return InterventionPolicy(
                max_checks_per_day=CRITICAL_RISK_MAX_CHECKS,
                min_interval_hours=CRITICAL_RISK_MIN_HOURS,
                recommended_windows=[
                    "08:00-09:00",
                    "10:00-11:00",
                    "13:00-14:00",
                    "15:00-16:00",
                    "17:00-18:00",
                    "20:00-21:00",
                ],
                hands_off_periods=[],
                auto_lock_threshold=CRITICAL_RISK_THRESHOLD,
                explanation=(
                    f"LOW Zeno risk. Frozen ratio: {frozen_ratio:.1%}, "
                    f"Intervention frequency: {measurement_freq:.2f}/hour. "
                    "Normal monitoring cadence is safe."
                ),
            )

    def compute_evolution_prevented(self) -> int:
        """
        Count solver improvements blocked by frozen assignments.

        Returns:
            Number of solver improvements that were blocked

        Example:
            blocked = governor.compute_evolution_prevented()
            print(f"{blocked} improvements blocked by human locks")
        """
        if not self.solver_attempts:
            return 0

        # Count attempts where solver wanted to modify frozen assignments
        blocked_count = 0
        for attempt in self.solver_attempts:
            if attempt.get("blocked", False):
                proposed_changes = attempt.get("proposed_changes", set())
                # Check if any proposed changes were to frozen assignments
                if proposed_changes & self.frozen_assignments:
                    blocked_count += 1

        return blocked_count

    async def create_freedom_window(
        self, duration_hours: int = 4, reason: str = "Allow solver exploration"
    ) -> OptimizationFreedomWindow:
        """
        Create a hands-off period for solver exploration.

        Args:
            duration_hours: Length of freedom window
            reason: Explanation for this window

        Returns:
            OptimizationFreedomWindow instance

        Example:
            window = await governor.create_freedom_window(
                duration_hours=DEFAULT_DURATION_HOURS,
                reason="Overnight optimization run"
            )
        """
        window = OptimizationFreedomWindow(
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=duration_hours),
            reason=reason,
            is_active=True,
        )

        self.freedom_windows.append(window)
        return window

    def is_in_freedom_window(self, check_time: datetime | None = None) -> bool:
        """
        Check if current time is within a freedom window.

        Args:
            check_time: Time to check (default: now)

        Returns:
            True if in freedom window, False otherwise
        """
        check_time = check_time or datetime.now()

        for window in self.freedom_windows:
            if window.is_active and window.start_time <= check_time <= window.end_time:
                return True

        return False

    def get_current_metrics(self) -> ZenoMetrics:
        """
        Get current Zeno effect metrics for dashboard.

        Returns:
            ZenoMetrics instance with current state

        Example:
            metrics = governor.get_current_metrics()
            print(f"Risk: {metrics.risk_level}")
            print(f"Frozen: {metrics.frozen_ratio:.1%}")
        """
        risk = self._assess_current_risk()
        measurement_freq = self.compute_measurement_frequency()
        frozen_ratio = self.compute_frozen_assignments_ratio()

        # Count interventions
        now = datetime.now()
        interventions_24h = len(
            [i for i in self.interventions if now - i.timestamp <= timedelta(days=1)]
        )
        interventions_7d = len(
            [i for i in self.interventions if now - i.timestamp <= timedelta(days=7)]
        )

        # Calculate average interval
        if len(self.interventions) >= 2:
            sorted_interventions = sorted(self.interventions, key=lambda x: x.timestamp)
            intervals = [
                (
                    sorted_interventions[i + 1].timestamp
                    - sorted_interventions[i].timestamp
                ).total_seconds()
                / 3600
                for i in range(len(sorted_interventions) - 1)
            ]
            avg_interval = sum(intervals) / len(intervals) if intervals else 24.0
        else:
            avg_interval = DEFAULT_AVG_INTERVAL_HOURS

        # Get frozen breakdown by user
        frozen_by_user = {
            user_id: len(assignments)
            for user_id, assignments in self.locked_by_user.items()
        }

        # Generate recommendations
        policy = self.recommend_intervention_policy()
        immediate_actions = self._generate_immediate_actions(risk)
        watch_items = self._generate_watch_items(risk)

        # Find last successful evolution
        last_success = None
        for attempt in reversed(self.solver_attempts):
            if attempt.get("successful", False) and not attempt.get("blocked", False):
                last_success = attempt.get("timestamp")
                break

        return ZenoMetrics(
            timestamp=now,
            risk_level=risk,
            interventions_24h=interventions_24h,
            interventions_7d=interventions_7d,
            avg_interval_hours=avg_interval,
            measurement_frequency=measurement_freq,
            total_assignments=self.total_assignments,
            frozen_assignments=len(self.frozen_assignments),
            frozen_ratio=frozen_ratio,
            frozen_by_user=frozen_by_user,
            evolution_prevented=self.compute_evolution_prevented(),
            local_optima_risk=self.compute_local_optima_risk(),
            solver_attempts_blocked=sum(
                1 for a in self.solver_attempts if a.get("blocked", False)
            ),
            last_successful_evolution=last_success,
            recommended_policy=policy,
            immediate_actions=immediate_actions,
            watch_items=watch_items,
        )

    def log_solver_attempt(
        self,
        proposed_changes: set[UUID],
        successful: bool,
        blocked: bool = False,
        reason: str = "",
    ) -> None:
        """
        Log a solver optimization attempt.

        Args:
            proposed_changes: Set of assignment IDs solver wanted to change
            successful: Whether solver improved the solution
            blocked: Whether attempt was blocked by frozen assignments
            reason: Explanation for outcome
        """
        attempt = {
            "timestamp": datetime.now(),
            "proposed_changes": proposed_changes,
            "successful": successful,
            "blocked": blocked,
            "reason": reason,
            "frozen_conflicts": proposed_changes & self.frozen_assignments,
        }

        self.solver_attempts.append(attempt)

    def unlock_assignment(self, assignment_id: UUID, user_id: str = "") -> bool:
        """
        Unlock (unfreeze) an assignment.

        Args:
            assignment_id: ID of assignment to unlock
            user_id: ID of user unlocking (for audit)

        Returns:
            True if unlocked, False if wasn't locked
        """
        if assignment_id in self.frozen_assignments:
            self.frozen_assignments.remove(assignment_id)

            # Remove from user's locked set
            if user_id and user_id in self.locked_by_user:
                self.locked_by_user[user_id].discard(assignment_id)

            # Log as intervention
            self.interventions.append(
                HumanIntervention(
                    user_id=user_id,
                    assignments_reviewed={assignment_id},
                    intervention_type="unlock",
                    reason="Manual unlock",
                )
            )

            return True

        return False

    def _assess_current_risk(self) -> ZenoRisk:
        """Internal method to assess current Zeno risk level."""
        measurement_freq = self.compute_measurement_frequency()
        frozen_ratio = self.compute_frozen_assignments_ratio()

        if measurement_freq > 0.5 or frozen_ratio > 0.5:
            return ZenoRisk.CRITICAL
        elif measurement_freq > 0.25 or frozen_ratio > 0.25:
            return ZenoRisk.HIGH
        elif measurement_freq > 0.125 or frozen_ratio > 0.10:
            return ZenoRisk.MODERATE
        else:
            return ZenoRisk.LOW

    def _generate_immediate_actions(self, risk: ZenoRisk) -> list[str]:
        """Generate immediate action recommendations."""
        actions = []

        if risk == ZenoRisk.CRITICAL:
            actions.append("🚨 CRITICAL: Stop all manual interventions immediately")
            actions.append("Unlock all non-essential frozen assignments")
            actions.append("Schedule 24-hour solver exploration window")
            actions.append("Review only for ACGME compliance violations")

        elif risk == ZenoRisk.HIGH:
            actions.append("⚠️ HIGH risk: Reduce intervention frequency")
            actions.append("Review and unlock assignments that can safely change")
            actions.append("Defer non-critical reviews to tomorrow")
            actions.append("Allow solver 12+ hours of uninterrupted runtime")

        elif risk == ZenoRisk.MODERATE:
            actions.append("📊 MODERATE risk: Space out reviews")
            actions.append("Wait 8+ hours between manual checks")
            actions.append("Consider unlocking low-priority locks")

        return actions

    def _generate_watch_items(self, risk: ZenoRisk) -> list[str]:
        """Generate items to monitor."""
        items = []

        frozen_ratio = self.compute_frozen_assignments_ratio()
        if frozen_ratio > 0.3:
            items.append(f"Frozen assignment ratio high: {frozen_ratio:.1%}")

        measurement_freq = self.compute_measurement_frequency()
        if measurement_freq > 0.2:
            items.append(
                f"Intervention frequency elevated: {measurement_freq * 24:.1f}/day"
            )

        local_optima_risk = self.compute_local_optima_risk()
        if local_optima_risk > 0.6:
            items.append(f"Local optima trap risk: {local_optima_risk:.1%}")

        blocked = self.compute_evolution_prevented()
        if blocked > 5:
            items.append(f"{blocked} solver improvements blocked by locks")

        return items
