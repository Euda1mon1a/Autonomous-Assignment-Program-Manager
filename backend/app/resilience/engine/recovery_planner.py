"""
Recovery Planner.

Plans recovery actions from degraded resilience states.
Implements priority-based recovery and resource allocation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.resilience.engine.defense_level_calculator import DefenseLevel


class RecoveryAction(str, Enum):
    """Recovery action types."""

    REDUCE_LOAD = "reduce_load"
    ADD_CAPACITY = "add_capacity"
    ACTIVATE_BACKUP = "activate_backup"
    REDISTRIBUTE_WORK = "redistribute_work"
    IMPLEMENT_RESTRICTIONS = "implement_restrictions"
    EMERGENCY_PROTOCOL = "emergency_protocol"


@dataclass
class RecoveryStep:
    """Single recovery step."""

    action: RecoveryAction
    priority: int  # 1 (highest) to 5 (lowest)
    description: str
    estimated_time_hours: float
    expected_impact: str
    prerequisites: list[str]
    success_criteria: str


@dataclass
class RecoveryPlan:
    """Complete recovery plan."""

    current_defense_level: DefenseLevel
    target_defense_level: DefenseLevel
    steps: list[RecoveryStep]
    estimated_total_time: float
    success_probability: float
    contingency_actions: list[str]


class RecoveryPlanner:
    """
    Plan recovery from degraded resilience states.

    Uses defense-in-depth principles:
    - Multiple recovery paths
    - Layered defenses
    - Graceful degradation
    """

    def plan_recovery(
        self,
        current_level: DefenseLevel,
        current_utilization: float,
        n1_failures: int,
        n2_failures: int,
        coverage_gaps: int,
        burnout_cases: int,
    ) -> RecoveryPlan:
        """
        Generate recovery plan based on current state.

        Args:
            current_level: Current defense level
            current_utilization: Current utilization ratio
            n1_failures: Number of N-1 failures
            n2_failures: Number of N-2 failures
            coverage_gaps: Number of coverage gaps
            burnout_cases: Number of burnout cases

        Returns:
            RecoveryPlan with prioritized steps
        """
        steps = []

        # Determine target level (always aim for GREEN)
        target_level = DefenseLevel.GREEN

        # Generate recovery steps based on current problems
        if current_level == DefenseLevel.BLACK:
            steps.extend(self._black_recovery_steps())
        elif current_level == DefenseLevel.RED:
            steps.extend(self._red_recovery_steps())
        elif current_level == DefenseLevel.ORANGE:
            steps.extend(self._orange_recovery_steps())
        elif current_level == DefenseLevel.YELLOW:
            steps.extend(self._yellow_recovery_steps())

        # Add specific steps for each problem
        if current_utilization > 0.90:
            steps.extend(self._utilization_recovery_steps(current_utilization))

        if coverage_gaps > 0:
            steps.extend(self._coverage_recovery_steps(coverage_gaps))

        if burnout_cases > 0:
            steps.extend(self._burnout_recovery_steps(burnout_cases))

        if n2_failures > 0:
            steps.extend(self._n2_recovery_steps(n2_failures))

        # Sort by priority
        steps.sort(key=lambda s: s.priority)

        # Calculate total time
        total_time = sum(s.estimated_time_hours for s in steps)

        # Estimate success probability
        success_prob = self._estimate_success_probability(current_level, len(steps))

        # Generate contingency actions
        contingencies = self._generate_contingencies(current_level)

        return RecoveryPlan(
            current_defense_level=current_level,
            target_defense_level=target_level,
            steps=steps,
            estimated_total_time=total_time,
            success_probability=success_prob,
            contingency_actions=contingencies,
        )

    def _black_recovery_steps(self) -> list[RecoveryStep]:
        """Recovery steps for BLACK (emergency) level."""
        return [
            RecoveryStep(
                action=RecoveryAction.EMERGENCY_PROTOCOL,
                priority=1,
                description="Activate emergency response plan immediately",
                estimated_time_hours=0.5,
                expected_impact="Prevent complete system failure",
                prerequisites=[],
                success_criteria="Emergency protocols active",
            ),
            RecoveryStep(
                action=RecoveryAction.ACTIVATE_BACKUP,
                priority=1,
                description="Activate ALL backup coverage immediately",
                estimated_time_hours=1.0,
                expected_impact="Immediate capacity increase",
                prerequisites=["Emergency protocol active"],
                success_criteria="All backup personnel deployed",
            ),
            RecoveryStep(
                action=RecoveryAction.IMPLEMENT_RESTRICTIONS,
                priority=1,
                description="Suspend non-critical operations",
                estimated_time_hours=0.5,
                expected_impact="Reduce immediate load",
                prerequisites=[],
                success_criteria="Non-critical services suspended",
            ),
        ]

    def _red_recovery_steps(self) -> list[RecoveryStep]:
        """Recovery steps for RED (critical) level."""
        return [
            RecoveryStep(
                action=RecoveryAction.ACTIVATE_BACKUP,
                priority=1,
                description="Activate backup coverage",
                estimated_time_hours=2.0,
                expected_impact="Increase capacity by 20-30%",
                prerequisites=[],
                success_criteria="Backup coverage operational",
            ),
            RecoveryStep(
                action=RecoveryAction.REDUCE_LOAD,
                priority=2,
                description="Defer elective procedures and non-urgent appointments",
                estimated_time_hours=1.0,
                expected_impact="Reduce utilization by 10-15%",
                prerequisites=[],
                success_criteria="Load reduced below 90%",
            ),
        ]

    def _orange_recovery_steps(self) -> list[RecoveryStep]:
        """Recovery steps for ORANGE (degraded) level."""
        return [
            RecoveryStep(
                action=RecoveryAction.REDISTRIBUTE_WORK,
                priority=2,
                description="Redistribute workload to balance utilization",
                estimated_time_hours=4.0,
                expected_impact="Even out hotspots",
                prerequisites=[],
                success_criteria="Utilization balanced across all residents",
            ),
            RecoveryStep(
                action=RecoveryAction.REDUCE_LOAD,
                priority=3,
                description="Gradually reduce non-essential assignments",
                estimated_time_hours=8.0,
                expected_impact="Reduce utilization by 5-10%",
                prerequisites=[],
                success_criteria="Utilization below 85%",
            ),
        ]

    def _yellow_recovery_steps(self) -> list[RecoveryStep]:
        """Recovery steps for YELLOW (warning) level."""
        return [
            RecoveryStep(
                action=RecoveryAction.REDISTRIBUTE_WORK,
                priority=3,
                description="Optimize schedule to reduce peaks",
                estimated_time_hours=12.0,
                expected_impact="Smooth utilization curve",
                prerequisites=[],
                success_criteria="Peak utilization below 85%",
            ),
        ]

    def _utilization_recovery_steps(self, utilization: float) -> list[RecoveryStep]:
        """Generate utilization-specific recovery steps."""
        if utilization > 0.95:
            return [
                RecoveryStep(
                    action=RecoveryAction.ADD_CAPACITY,
                    priority=1,
                    description=f"URGENT: Add capacity immediately (current: {utilization:.1%})",
                    estimated_time_hours=2.0,
                    expected_impact="Prevent queue explosion",
                    prerequisites=[],
                    success_criteria="Utilization < 90%",
                )
            ]
        return []

    def _coverage_recovery_steps(self, gaps: int) -> list[RecoveryStep]:
        """Generate coverage gap recovery steps."""
        return [
            RecoveryStep(
                action=RecoveryAction.ACTIVATE_BACKUP,
                priority=1,
                description=f"Fill {gaps} coverage gaps with backup personnel",
                estimated_time_hours=gaps * 0.5,
                expected_impact="Restore full coverage",
                prerequisites=[],
                success_criteria="Zero coverage gaps",
            )
        ]

    def _burnout_recovery_steps(self, cases: int) -> list[RecoveryStep]:
        """Generate burnout recovery steps."""
        return [
            RecoveryStep(
                action=RecoveryAction.REDUCE_LOAD,
                priority=2,
                description=f"Reduce workload for {cases} affected residents",
                estimated_time_hours=24.0,
                expected_impact="Allow recovery, reduce Rt",
                prerequisites=[],
                success_criteria="Burnout Rt < 1.0",
            )
        ]

    def _n2_recovery_steps(self, n2_count: int) -> list[RecoveryStep]:
        """Generate N-2 contingency recovery steps."""
        return [
            RecoveryStep(
                action=RecoveryAction.ADD_CAPACITY,
                priority=3,
                description=f"Add redundancy to address {n2_count} N-2 vulnerabilities",
                estimated_time_hours=48.0,
                expected_impact="Improve system resilience",
                prerequisites=[],
                success_criteria="N-2 failures < 5",
            )
        ]

    def _estimate_success_probability(
        self,
        current_level: DefenseLevel,
        num_steps: int,
    ) -> float:
        """Estimate probability of successful recovery."""
        # Base probability by level
        base_prob = {
            DefenseLevel.GREEN: 1.0,
            DefenseLevel.YELLOW: 0.9,
            DefenseLevel.ORANGE: 0.7,
            DefenseLevel.RED: 0.5,
            DefenseLevel.BLACK: 0.3,
        }[current_level]

        # Reduce probability for complex recoveries (many steps)
        complexity_penalty = 0.05 * (num_steps - 1)

        return max(0.1, base_prob - complexity_penalty)

    def _generate_contingencies(self, current_level: DefenseLevel) -> list[str]:
        """Generate contingency actions if recovery plan fails."""
        if current_level == DefenseLevel.BLACK:
            return [
                "Request mutual aid from other residency programs",
                "Activate GME emergency protocols",
                "Notify ACGME of emergency situation",
                "Consider temporary service reductions",
            ]
        elif current_level == DefenseLevel.RED:
            return [
                "Escalate to program leadership",
                "Request external assistance",
                "Prepare for emergency staffing",
            ]
        else:
            return [
                "Monitor closely and escalate if deteriorating",
                "Prepare backup plans",
            ]
