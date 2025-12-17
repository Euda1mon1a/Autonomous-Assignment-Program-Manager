"""
Utilization Threshold Management (Queuing Theory).

Implements the 80% utilization threshold from queuing theory to prevent
cascade failures. Wait times increase exponentially as utilization
approaches capacity:

    Wait Time ~ rho / (1 - rho)

    At 50% utilization: 1x wait
    At 80% utilization: 4x wait
    At 90% utilization: 9x wait
    At 95% utilization: 19x wait

The 20% buffer absorbs variance, sick days, and emergencies.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from uuid import UUID

logger = logging.getLogger(__name__)


class UtilizationLevel(Enum):
    """Utilization status levels."""
    GREEN = "green"      # < 70% - Healthy buffer
    YELLOW = "yellow"    # 70-80% - Approaching threshold
    ORANGE = "orange"    # 80-90% - Above threshold, degraded operations
    RED = "red"          # 90-95% - Critical, cascade risk
    BLACK = "black"      # > 95% - Imminent failure


@dataclass
class UtilizationThreshold:
    """Configuration for utilization thresholds."""
    max_utilization: float = 0.80  # Target maximum
    warning_threshold: float = 0.70  # Yellow alert
    critical_threshold: float = 0.90  # Red alert
    emergency_threshold: float = 0.95  # Black alert

    def get_level(self, utilization: float) -> UtilizationLevel:
        """Determine utilization level from value."""
        if utilization >= self.emergency_threshold:
            return UtilizationLevel.BLACK
        elif utilization >= self.critical_threshold:
            return UtilizationLevel.RED
        elif utilization >= self.max_utilization:
            return UtilizationLevel.ORANGE
        elif utilization >= self.warning_threshold:
            return UtilizationLevel.YELLOW
        return UtilizationLevel.GREEN


@dataclass
class UtilizationMetrics:
    """Metrics for a utilization calculation."""
    total_capacity: int  # Total available faculty-blocks
    required_coverage: int  # Required coverage blocks
    current_assignments: int  # Currently assigned blocks
    utilization_rate: float  # current / capacity
    effective_utilization: float  # required / capacity
    level: UtilizationLevel
    buffer_remaining: float  # How much buffer before threshold

    # Breakdown by category
    by_service: dict = field(default_factory=dict)
    by_faculty: dict = field(default_factory=dict)


@dataclass
class UtilizationForecast:
    """Forecast of utilization over time."""
    date: date
    predicted_utilization: float
    predicted_level: UtilizationLevel
    contributing_factors: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)


class UtilizationMonitor:
    """
    Monitors and enforces utilization thresholds.

    Core principle: Never schedule above 80% of theoretical capacity.
    When at 50% faculty (e.g., PCS season), effective capacity is
    50% * 80% = 40% of original.
    """

    def __init__(
        self,
        threshold: UtilizationThreshold | None = None,
    ):
        self.threshold = threshold or UtilizationThreshold()
        self._capacity_cache = {}

    def calculate_utilization(
        self,
        available_faculty: list,
        required_blocks: int,
        blocks_per_faculty_per_day: float = 2.0,
        days_in_period: int = 1,
    ) -> UtilizationMetrics:
        """
        Calculate current utilization metrics.

        Args:
            available_faculty: List of available faculty members
            required_blocks: Number of blocks that need coverage
            blocks_per_faculty_per_day: Max blocks per faculty per day (default 2 = AM+PM)
            days_in_period: Number of days in the period

        Returns:
            UtilizationMetrics with current status
        """
        # Calculate theoretical capacity
        total_capacity = int(
            len(available_faculty) * blocks_per_faculty_per_day * days_in_period
        )

        if total_capacity == 0:
            return UtilizationMetrics(
                total_capacity=0,
                required_coverage=required_blocks,
                current_assignments=0,
                utilization_rate=1.0 if required_blocks > 0 else 0.0,
                effective_utilization=1.0 if required_blocks > 0 else 0.0,
                level=UtilizationLevel.BLACK if required_blocks > 0 else UtilizationLevel.GREEN,
                buffer_remaining=0.0,
            )

        # Calculate utilization
        utilization_rate = required_blocks / total_capacity
        level = self.threshold.get_level(utilization_rate)

        # Calculate buffer remaining before threshold
        max_safe_blocks = int(total_capacity * self.threshold.max_utilization)
        buffer_remaining = max(0, max_safe_blocks - required_blocks) / total_capacity

        return UtilizationMetrics(
            total_capacity=total_capacity,
            required_coverage=required_blocks,
            current_assignments=required_blocks,
            utilization_rate=utilization_rate,
            effective_utilization=utilization_rate,
            level=level,
            buffer_remaining=buffer_remaining,
        )

    def get_safe_capacity(
        self,
        available_faculty: list,
        blocks_per_faculty_per_day: float = 2.0,
        days_in_period: int = 1,
    ) -> int:
        """
        Get safe capacity (80% of theoretical) for scheduling.

        This is the maximum number of blocks that should be scheduled
        to maintain operational buffer.
        """
        theoretical = int(
            len(available_faculty) * blocks_per_faculty_per_day * days_in_period
        )
        return int(theoretical * self.threshold.max_utilization)

    def check_assignment_safe(
        self,
        current_utilization: float,
        additional_blocks: int,
        total_capacity: int,
    ) -> tuple[bool, str]:
        """
        Check if adding blocks would exceed safe threshold.

        Returns:
            Tuple of (is_safe, message)
        """
        if total_capacity == 0:
            return False, "No capacity available"

        new_utilization = (
            current_utilization * total_capacity + additional_blocks
        ) / total_capacity

        if new_utilization > self.threshold.max_utilization:
            return False, (
                f"Would exceed 80% threshold: {new_utilization:.1%} utilization. "
                f"Consider load shedding or service reduction."
            )

        if new_utilization > self.threshold.warning_threshold:
            return True, (
                f"Warning: Approaching threshold at {new_utilization:.1%}. "
                f"Buffer reducing."
            )

        return True, f"Safe: {new_utilization:.1%} utilization"

    def forecast_utilization(
        self,
        base_faculty: list,
        known_absences: dict[date, list[UUID]],
        required_coverage_by_date: dict[date, int],
        forecast_days: int = 90,
    ) -> list[UtilizationForecast]:
        """
        Forecast utilization over a period, accounting for known absences.

        Args:
            base_faculty: List of all faculty
            known_absences: Dict of date -> list of absent faculty IDs
            required_coverage_by_date: Dict of date -> required blocks
            forecast_days: Number of days to forecast

        Returns:
            List of daily utilization forecasts
        """
        forecasts = []
        today = date.today()
        base_count = len(base_faculty)

        for day_offset in range(forecast_days):
            forecast_date = today + timedelta(days=day_offset)

            # Get absences for this date
            absent_ids = known_absences.get(forecast_date, [])
            available_count = base_count - len(absent_ids)

            # Get required coverage
            required = required_coverage_by_date.get(forecast_date, 0)

            # Calculate utilization
            if available_count > 0:
                capacity = available_count * 2  # 2 blocks per day
                utilization = required / capacity if capacity > 0 else 1.0
            else:
                utilization = 1.0 if required > 0 else 0.0

            level = self.threshold.get_level(utilization)

            # Build contributing factors
            factors = []
            if len(absent_ids) > 0:
                factors.append(f"{len(absent_ids)} faculty absent")
            if level in (UtilizationLevel.RED, UtilizationLevel.BLACK):
                factors.append("Critical staffing shortage")

            # Build recommendations
            recommendations = []
            if level == UtilizationLevel.YELLOW:
                recommendations.append("Monitor closely")
            elif level == UtilizationLevel.ORANGE:
                recommendations.append("Consider deferring non-essential activities")
            elif level == UtilizationLevel.RED:
                recommendations.append("Activate load shedding protocol")
            elif level == UtilizationLevel.BLACK:
                recommendations.append("Emergency staffing measures required")

            forecasts.append(UtilizationForecast(
                date=forecast_date,
                predicted_utilization=utilization,
                predicted_level=level,
                contributing_factors=factors,
                recommendations=recommendations,
            ))

        return forecasts

    def calculate_wait_time_multiplier(self, utilization: float) -> float:
        """
        Calculate expected wait time multiplier based on queuing theory.

        Uses M/M/1 queue formula: W = rho / (1 - rho)

        This represents how much longer things take compared to baseline.
        """
        if utilization >= 1.0:
            return float('inf')
        if utilization <= 0:
            return 0.0

        return utilization / (1 - utilization)

    def get_status_report(
        self,
        metrics: UtilizationMetrics,
    ) -> dict:
        """Generate human-readable status report."""
        wait_multiplier = self.calculate_wait_time_multiplier(metrics.utilization_rate)

        status_messages = {
            UtilizationLevel.GREEN: "System healthy with adequate buffer",
            UtilizationLevel.YELLOW: "Approaching utilization threshold",
            UtilizationLevel.ORANGE: "Above optimal threshold - degraded operations",
            UtilizationLevel.RED: "Critical utilization - cascade failure risk",
            UtilizationLevel.BLACK: "Emergency - immediate intervention required",
        }

        return {
            "level": metrics.level.value,
            "utilization": f"{metrics.utilization_rate:.1%}",
            "message": status_messages[metrics.level],
            "buffer_remaining": f"{metrics.buffer_remaining:.1%}",
            "wait_time_multiplier": (
                f"{wait_multiplier:.1f}x" if wait_multiplier < 100 else "Critical"
            ),
            "capacity": {
                "total": metrics.total_capacity,
                "safe_maximum": int(metrics.total_capacity * self.threshold.max_utilization),
                "current_used": metrics.current_assignments,
            },
            "recommendations": self._get_recommendations(metrics.level),
        }

    def _get_recommendations(self, level: UtilizationLevel) -> list[str]:
        """Get recommendations based on utilization level."""
        recommendations = {
            UtilizationLevel.GREEN: [
                "Continue normal operations",
                "Good time for training or improvement initiatives",
            ],
            UtilizationLevel.YELLOW: [
                "Review upcoming commitments",
                "Ensure backup coverage is confirmed",
                "Consider deferring new initiatives",
            ],
            UtilizationLevel.ORANGE: [
                "Cancel optional meetings and education",
                "Defer non-urgent research activities",
                "Prepare for possible escalation",
            ],
            UtilizationLevel.RED: [
                "Activate load shedding protocol",
                "Cancel all non-clinical activities",
                "Consolidate services where possible",
                "Notify leadership",
            ],
            UtilizationLevel.BLACK: [
                "Emergency staffing measures",
                "Consider service closure",
                "Escalate to external authority",
                "Document all decisions",
            ],
        }
        return recommendations.get(level, [])
