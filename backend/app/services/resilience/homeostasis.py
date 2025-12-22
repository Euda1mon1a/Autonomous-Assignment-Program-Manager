"""Homeostasis service for resilience monitoring.

This service encapsulates the logic for checking system homeostasis,
including feedback loop monitoring, allostatic load calculation,
and positive feedback risk detection.

The service follows the biological homeostasis paradigm:
- Negative feedback loops stabilize the system
- Positive feedback loops are detected as risks
- Allostatic load tracks cumulative stress costs
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import get_resilience_config
from app.resilience.homeostasis import (
    AllostasisMetrics,
    AllostasisState,
    HomeostasisMonitor,
    HomeostasisStatus,
)
from app.resilience.service import ResilienceConfig, ResilienceService
from app.schemas.resilience import (
    AllostasisState as SchemaAllostasisState,
    HomeostasisReport,
)

logger = logging.getLogger(__name__)


class HomeostasisService:
    """
    Service for monitoring and managing system homeostasis.

    This service provides a clean interface for checking homeostasis
    feedback loops and calculating system health metrics. It wraps
    the underlying ResilienceService with a focused API for homeostasis
    operations.

    Usage:
        service = HomeostasisService(db)
        report = service.check_homeostasis({
            "coverage_rate": 0.92,
            "faculty_utilization": 0.78,
        })

        if report.overall_state == AllostasisState.ALLOSTATIC_OVERLOAD:
            # Take corrective action
            pass
    """

    def __init__(
        self,
        db: Session,
        config: ResilienceConfig | None = None,
    ):
        """
        Initialize the homeostasis service.

        Args:
            db: Database session for persistence operations
            config: Optional resilience configuration
        """
        self.db = db
        self._config = config
        self._resilience_service: ResilienceService | None = None

    @property
    def resilience_service(self) -> ResilienceService:
        """
        Lazily initialize and return the resilience service.

        This ensures the service is only created when needed and
        uses the provided configuration.
        """
        if self._resilience_service is None:
            if self._config is None:
                self._config = get_resilience_config()
            self._resilience_service = ResilienceService(
                db=self.db,
                config=self._config,
            )
        return self._resilience_service

    @property
    def homeostasis_monitor(self) -> HomeostasisMonitor:
        """Direct access to the homeostasis monitor component."""
        return self.resilience_service.homeostasis

    def check_homeostasis(
        self,
        metrics: dict[str, float],
    ) -> HomeostasisReport:
        """
        Check homeostasis with provided metrics.

        This method evaluates the current system state against defined
        setpoints and returns a comprehensive report of feedback loop
        health, active corrections, and recommendations.

        The metrics dict should contain setpoint names mapped to their
        current values. Available setpoints include:
        - coverage_rate: Target 0.95, tolerance 0.05
        - faculty_utilization: Target 0.75, tolerance 0.10
        - workload_balance: Target 0.15 std_dev, tolerance 0.05
        - schedule_stability: Target 0.95, tolerance 0.05
        - acgme_compliance: Target 1.0, tolerance 0.02

        Args:
            metrics: Dict of setpoint_name -> current_value
                Example: {"coverage_rate": 0.92, "faculty_utilization": 0.78}

        Returns:
            HomeostasisReport with feedback loop states and recommendations

        Example:
            >>> service = HomeostasisService(db)
            >>> report = service.check_homeostasis({
            ...     "coverage_rate": 0.92,
            ...     "faculty_utilization": 0.78,
            ... })
            >>> print(report.overall_state)
            AllostasisState.HOMEOSTASIS
        """
        # Validate metrics input
        if not metrics:
            logger.warning("check_homeostasis called with empty metrics dict")

        # Use the resilience service's check_homeostasis method
        # which handles all the feedback loop checking, corrections,
        # and positive feedback risk detection
        status: HomeostasisStatus = self.resilience_service.check_homeostasis(
            current_values=metrics,
        )

        # Convert the internal HomeostasisStatus to the public HomeostasisReport
        report = self._convert_status_to_report(status)

        logger.info(
            "Homeostasis check completed: state=%s, healthy=%d, deviating=%d, "
            "risks=%d, avg_load=%.2f",
            report.overall_state.value,
            report.feedback_loops_healthy,
            report.feedback_loops_deviating,
            report.positive_feedback_risks,
            report.average_allostatic_load,
        )

        return report

    def get_current_status(self) -> HomeostasisReport:
        """
        Get current homeostasis status without providing new metrics.

        This returns the cached status from the homeostasis monitor
        without triggering new feedback loop checks.

        Returns:
            HomeostasisReport with current state
        """
        status = self.homeostasis_monitor.get_status()
        return self._convert_status_to_report(status)

    def calculate_allostatic_load(
        self,
        entity_id: str,
        entity_type: str,
        stress_factors: dict,
    ) -> AllostasisMetrics:
        """
        Calculate allostatic load for a faculty member or system.

        Allostatic load represents the cumulative cost of chronic stress
        adaptation. Even if the system handles each crisis, the cost
        accumulates until potential failure.

        Args:
            entity_id: Faculty ID or system UUID as string
            entity_type: "faculty" or "system"
            stress_factors: Dict of stress factor values:
                - consecutive_weekend_calls: int
                - nights_past_month: int
                - schedule_changes_absorbed: int
                - holidays_worked_this_year: int
                - overtime_hours_month: float
                - coverage_gap_responses: int
                - cross_coverage_events: int

        Returns:
            AllostasisMetrics with calculated load and risk level
        """
        from uuid import UUID

        entity_uuid = UUID(entity_id) if isinstance(entity_id, str) else entity_id

        return self.resilience_service.calculate_allostatic_load(
            entity_id=entity_uuid,
            entity_type=entity_type,
            stress_factors=stress_factors,
        )

    def get_feedback_loop_status(self, setpoint_name: str) -> dict | None:
        """
        Get status of a specific feedback loop.

        Args:
            setpoint_name: Name of the setpoint (e.g., "coverage_rate")

        Returns:
            Dict with feedback loop details, or None if not found
        """
        loop = self.homeostasis_monitor.get_feedback_loop(setpoint_name)
        if not loop:
            return None

        current_value = None
        deviation = None
        if loop.value_history:
            current_value = loop.value_history[-1][1]
            deviation, _ = loop.setpoint.check_deviation(current_value)

        return {
            "name": loop.name,
            "setpoint_name": loop.setpoint.name,
            "target_value": loop.setpoint.target_value,
            "tolerance": loop.setpoint.tolerance,
            "current_value": current_value,
            "deviation": deviation,
            "consecutive_deviations": loop.consecutive_deviations,
            "trend": loop.get_trend(),
            "is_improving": loop.is_improving(),
            "total_corrections": loop.total_corrections,
            "last_checked": loop.last_checked.isoformat() if loop.last_checked else None,
        }

    def get_all_feedback_loops(self) -> list[dict]:
        """
        Get status of all feedback loops.

        Returns:
            List of feedback loop status dicts
        """
        loops = []
        for loop in self.homeostasis_monitor.feedback_loops.values():
            status = self.get_feedback_loop_status(loop.setpoint.name)
            if status:
                loops.append(status)
        return loops

    def get_positive_feedback_risks(self) -> list[dict]:
        """
        Get all detected positive feedback loop risks.

        Returns:
            List of risk dicts with details and interventions
        """
        return [
            {
                "id": str(risk.id),
                "name": risk.name,
                "description": risk.description,
                "detected_at": risk.detected_at.isoformat(),
                "trigger": risk.trigger,
                "amplification": risk.amplification,
                "consequence": risk.consequence,
                "evidence": risk.evidence,
                "confidence": risk.confidence,
                "severity": risk.severity.value,
                "intervention": risk.intervention,
                "urgency": risk.urgency,
            }
            for risk in self.homeostasis_monitor.positive_feedback_risks
        ]

    def _convert_status_to_report(
        self,
        status: HomeostasisStatus,
    ) -> HomeostasisReport:
        """
        Convert internal HomeostasisStatus to public HomeostasisReport.

        Args:
            status: Internal status from HomeostasisMonitor

        Returns:
            HomeostasisReport Pydantic model for API response
        """
        return HomeostasisReport(
            timestamp=status.timestamp,
            overall_state=SchemaAllostasisState(status.overall_state.value),
            feedback_loops_healthy=status.feedback_loops_healthy,
            feedback_loops_deviating=status.feedback_loops_deviating,
            active_corrections=status.active_corrections,
            positive_feedback_risks=status.positive_feedback_risks,
            average_allostatic_load=status.average_allostatic_load,
            recommendations=status.recommendations,
        )


def get_homeostasis_service(db: Session) -> HomeostasisService:
    """
    Factory function to create HomeostasisService instance.

    This is the recommended way to obtain a HomeostasisService instance
    in route handlers using FastAPI's dependency injection.

    Args:
        db: Database session

    Returns:
        HomeostasisService instance

    Example:
        @router.post("/tier2/homeostasis/check")
        async def check_homeostasis(
            request: HomeostasisCheckRequest,
            service: HomeostasisService = Depends(get_homeostasis_service),
        ):
            return service.check_homeostasis(request.metrics)
    """
    return HomeostasisService(db=db)
