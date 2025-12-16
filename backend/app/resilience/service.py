"""
Resilience Service - Orchestrates all resilience components.

This service provides a unified interface to:
1. Monitor system health (utilization, coverage, redundancy)
2. Detect and respond to degraded conditions
3. Activate appropriate defense levels
4. Execute load shedding when needed
5. Switch to fallback schedules during crisis

The service integrates:
- UtilizationMonitor (queuing theory 80% threshold)
- DefenseInDepth (5-level nuclear safety paradigm)
- ContingencyAnalyzer (N-1/N-2 power grid analysis)
- FallbackScheduler (AWS static stability)
- SacrificeHierarchy (triage load shedding)
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional, Callable, Any
from uuid import UUID
import logging

from sqlalchemy.orm import Session

from app.resilience.utilization import (
    UtilizationMonitor,
    UtilizationThreshold,
    UtilizationLevel,
    UtilizationMetrics,
)
from app.resilience.defense_in_depth import (
    DefenseInDepth,
    DefenseLevel,
    RedundancyStatus,
)
from app.resilience.contingency import (
    ContingencyAnalyzer,
    VulnerabilityReport,
    CentralityScore,
)
from app.resilience.static_stability import (
    FallbackScheduler,
    FallbackScenario,
    FallbackSchedule,
)
from app.resilience.sacrifice_hierarchy import (
    SacrificeHierarchy,
    LoadSheddingLevel,
    ActivityCategory,
    Activity,
)

logger = logging.getLogger(__name__)


@dataclass
class SystemHealthReport:
    """Comprehensive system health report."""
    timestamp: datetime
    overall_status: str  # "healthy", "degraded", "critical", "emergency"

    # Component statuses
    utilization: UtilizationMetrics
    defense_level: DefenseLevel
    redundancy_status: list[RedundancyStatus]
    load_shedding_level: LoadSheddingLevel
    active_fallbacks: list[str]

    # Risk indicators
    n1_pass: bool
    n2_pass: bool
    phase_transition_risk: str

    # Recommendations
    immediate_actions: list[str] = field(default_factory=list)
    watch_items: list[str] = field(default_factory=list)


@dataclass
class ResilienceConfig:
    """Configuration for resilience service."""
    # Utilization thresholds
    max_utilization: float = 0.80
    warning_threshold: float = 0.70

    # Auto-activation settings
    auto_activate_defense: bool = True
    auto_activate_fallback: bool = False  # Require manual confirmation
    auto_shed_load: bool = True

    # Monitoring intervals
    health_check_interval_minutes: int = 15
    contingency_analysis_interval_hours: int = 24

    # Notification settings
    alert_recipients: list[str] = field(default_factory=list)
    escalation_threshold: DefenseLevel = DefenseLevel.CONTAINMENT


class ResilienceService:
    """
    Main service for scheduling system resilience.

    Provides unified interface for:
    - Health monitoring
    - Crisis detection and response
    - Load management
    - Fallback activation

    Usage:
        service = ResilienceService(db)
        health = service.check_health(faculty, blocks, assignments)

        if health.overall_status == "critical":
            service.activate_crisis_response()
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        config: Optional[ResilienceConfig] = None,
    ):
        self.db = db
        self.config = config or ResilienceConfig()

        # Initialize components
        self.utilization = UtilizationMonitor(
            UtilizationThreshold(
                max_utilization=self.config.max_utilization,
                warning_threshold=self.config.warning_threshold,
            )
        )
        self.defense = DefenseInDepth()
        self.contingency = ContingencyAnalyzer()
        self.fallback = FallbackScheduler()
        self.sacrifice = SacrificeHierarchy()

        # State tracking
        self._last_health_check: Optional[datetime] = None
        self._last_contingency_analysis: Optional[datetime] = None
        self._crisis_mode: bool = False
        self._event_handlers: dict[str, list[Callable]] = {}

    def check_health(
        self,
        faculty: list,
        blocks: list,
        assignments: list,
        coverage_requirements: Optional[dict[UUID, int]] = None,
    ) -> SystemHealthReport:
        """
        Perform comprehensive system health check.

        Args:
            faculty: List of faculty members
            blocks: List of blocks in period
            assignments: List of current assignments
            coverage_requirements: Dict of block_id -> required coverage

        Returns:
            Complete SystemHealthReport
        """
        self._last_health_check = datetime.now()

        # Default coverage requirements (1 per block)
        if coverage_requirements is None:
            coverage_requirements = {b.id: 1 for b in blocks}

        # 1. Check utilization
        required_blocks = sum(coverage_requirements.values())
        utilization_metrics = self.utilization.calculate_utilization(
            available_faculty=faculty,
            required_blocks=required_blocks,
            blocks_per_faculty_per_day=2.0,
            days_in_period=max(1, len(set(b.date for b in blocks))),
        )

        # 2. Check redundancy for critical services
        redundancy_status = self.defense.check_all_redundancy({
            "clinical_coverage": {
                "available_providers": faculty,
                "minimum_required": max(1, len(blocks) // 10),  # Rough estimate
            },
        })

        # 3. Run contingency analysis (if due)
        vulnerability_report = self._maybe_run_contingency(
            faculty, blocks, assignments, coverage_requirements,
            utilization_metrics.utilization_rate,
        )

        # 4. Determine defense level
        current_defense = self.defense.get_recommended_level(
            1.0 - utilization_metrics.utilization_rate  # coverage rate
        )

        # 5. Determine overall status
        overall_status = self._determine_overall_status(
            utilization_metrics.level,
            current_defense,
            vulnerability_report,
        )

        # 6. Build recommendations
        immediate_actions, watch_items = self._build_recommendations(
            overall_status,
            utilization_metrics,
            vulnerability_report,
        )

        # 7. Auto-activate defenses if configured
        if self.config.auto_activate_defense:
            self._auto_activate_defense(current_defense)

        report = SystemHealthReport(
            timestamp=datetime.now(),
            overall_status=overall_status,
            utilization=utilization_metrics,
            defense_level=current_defense,
            redundancy_status=redundancy_status,
            load_shedding_level=self.sacrifice.current_level,
            active_fallbacks=[f.scenario.value for f in self.fallback.get_active_fallbacks()],
            n1_pass=vulnerability_report.n1_pass if vulnerability_report else True,
            n2_pass=vulnerability_report.n2_pass if vulnerability_report else True,
            phase_transition_risk=(
                vulnerability_report.phase_transition_risk if vulnerability_report else "low"
            ),
            immediate_actions=immediate_actions,
            watch_items=watch_items,
        )

        # Emit health event
        self._emit_event("health_check", report)

        return report

    def activate_crisis_response(
        self,
        severity: str = "moderate",
        reason: str = "",
    ) -> dict:
        """
        Activate crisis response mode.

        Args:
            severity: "minor", "moderate", "severe", "critical"
            reason: Description of crisis

        Returns:
            Dict with actions taken
        """
        self._crisis_mode = True
        actions_taken = []

        # Determine appropriate responses
        if severity == "minor":
            # Yellow level
            self.defense.activate_action(DefenseLevel.CONTROL, "early_warning")
            self.sacrifice.activate_level(LoadSheddingLevel.YELLOW, reason)
            actions_taken.append("Activated early warning monitoring")
            actions_taken.append("Suspended optional education activities")

        elif severity == "moderate":
            # Orange level
            self.defense.activate_action(DefenseLevel.SAFETY_SYSTEMS, "auto_reassignment")
            self.sacrifice.activate_level(LoadSheddingLevel.ORANGE, reason)
            actions_taken.append("Activated automatic reassignment")
            actions_taken.append("Suspended admin, research, and optional education")

        elif severity == "severe":
            # Red level
            self.defense.activate_action(DefenseLevel.CONTAINMENT, "service_reduction")
            self.sacrifice.activate_level(LoadSheddingLevel.RED, reason)
            actions_taken.append("Activated service reduction protocol")
            actions_taken.append("Suspended all non-clinical education")

        elif severity == "critical":
            # Black level
            self.defense.activate_action(DefenseLevel.EMERGENCY, "crisis_communication")
            self.sacrifice.activate_level(LoadSheddingLevel.BLACK, reason)
            actions_taken.append("Activated emergency response")
            actions_taken.append("Essential services only")

        logger.warning(
            f"Crisis response activated: {severity}. "
            f"Reason: {reason}. "
            f"Actions: {actions_taken}"
        )

        self._emit_event("crisis_activated", {
            "severity": severity,
            "reason": reason,
            "actions": actions_taken,
        })

        return {
            "crisis_mode": True,
            "severity": severity,
            "actions_taken": actions_taken,
            "load_shedding_level": self.sacrifice.current_level.name,
        }

    def deactivate_crisis_response(self, reason: str = "") -> dict:
        """
        Deactivate crisis response and begin recovery.

        Recovery is gradual - services restored in reverse sacrifice order.
        """
        self._crisis_mode = False

        # Reduce load shedding
        self.sacrifice.deactivate_level(LoadSheddingLevel.NORMAL)

        # Deactivate fallbacks
        for fallback in self.fallback.get_active_fallbacks():
            self.fallback.deactivate_fallback(fallback.scenario)

        logger.info(f"Crisis response deactivated. Reason: {reason}")

        self._emit_event("crisis_deactivated", {"reason": reason})

        return {
            "crisis_mode": False,
            "recovery_plan": self.sacrifice.get_recovery_plan(),
        }

    def recommend_fallback(
        self,
        faculty_available: int,
        faculty_total: int,
        is_pcs_season: bool = False,
        is_holiday: bool = False,
    ) -> Optional[FallbackScenario]:
        """
        Get recommended fallback scenario based on current conditions.

        Args:
            faculty_available: Number of faculty currently available
            faculty_total: Total number of faculty normally
            is_pcs_season: Whether in PCS transition period
            is_holiday: Whether holiday period

        Returns:
            Recommended FallbackScenario, or None if normal operations OK
        """
        loss_count = faculty_total - faculty_available

        return self.fallback.get_best_fallback_for_situation(
            faculty_loss_count=loss_count,
            is_pcs_season=is_pcs_season,
            is_holiday=is_holiday,
        )

    def activate_fallback(
        self,
        scenario: FallbackScenario,
        approved_by: Optional[str] = None,
    ) -> Optional[FallbackSchedule]:
        """
        Activate a pre-computed fallback schedule.

        Args:
            scenario: The fallback scenario to activate
            approved_by: Who approved the activation

        Returns:
            The activated FallbackSchedule, or None if not available
        """
        fallback = self.fallback.activate_fallback(scenario)

        if fallback:
            self._emit_event("fallback_activated", {
                "scenario": scenario.value,
                "approved_by": approved_by,
                "assignments_count": len(fallback.assignments),
            })

        return fallback

    def get_centrality_report(
        self,
        faculty: list,
        assignments: list,
        services: dict[UUID, list[UUID]],
    ) -> list[CentralityScore]:
        """
        Get faculty centrality scores (hub vulnerability analysis).

        Higher centrality = more critical = bigger impact if removed.
        """
        return self.contingency.calculate_centrality(faculty, assignments, services)

    def precompute_fallbacks(
        self,
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        Pre-compute all fallback schedules for a period.

        Should be run during calm periods to prepare for crisis.
        """
        return self.fallback.precompute_all_fallbacks(start_date, end_date)

    def get_comprehensive_report(
        self,
        faculty: list,
        blocks: list,
        assignments: list,
    ) -> dict:
        """
        Generate comprehensive resilience report.

        Combines all component reports into single document.
        """
        # Health check
        health = self.check_health(faculty, blocks, assignments)

        # Utilization report
        utilization_report = self.utilization.get_status_report(health.utilization)

        # Defense status
        defense_status = self.defense.get_status_report()

        # Fallback status
        fallback_status = self.fallback.get_status_report()

        # Load shedding status
        sacrifice_status = self.sacrifice.get_status()

        return {
            "generated_at": datetime.now().isoformat(),
            "overall_status": health.overall_status,
            "summary": {
                "utilization_level": health.utilization.level.value,
                "defense_level": health.defense_level.name,
                "load_shedding_level": health.load_shedding_level.name,
                "n1_compliant": health.n1_pass,
                "n2_compliant": health.n2_pass,
                "phase_transition_risk": health.phase_transition_risk,
            },
            "immediate_actions": health.immediate_actions,
            "watch_items": health.watch_items,
            "components": {
                "utilization": utilization_report,
                "defense": defense_status,
                "fallback": fallback_status,
                "sacrifice": {
                    "level": sacrifice_status.level.name,
                    "activities_suspended": sacrifice_status.activities_suspended,
                    "activities_protected": sacrifice_status.activities_protected,
                },
            },
        }

    def register_event_handler(
        self,
        event_type: str,
        handler: Callable[[dict], Any],
    ):
        """
        Register handler for resilience events.

        Event types:
        - health_check: Periodic health check completed
        - crisis_activated: Crisis response activated
        - crisis_deactivated: Crisis response ended
        - fallback_activated: Fallback schedule activated
        - threshold_exceeded: Utilization threshold exceeded
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def _emit_event(self, event_type: str, data: Any):
        """Emit event to registered handlers."""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Event handler error ({event_type}): {e}")

    def _maybe_run_contingency(
        self,
        faculty: list,
        blocks: list,
        assignments: list,
        coverage_requirements: dict,
        current_utilization: float,
    ) -> Optional[VulnerabilityReport]:
        """Run contingency analysis if due or if utilization is high."""
        should_run = (
            self._last_contingency_analysis is None or
            (datetime.now() - self._last_contingency_analysis).total_seconds() >
            self.config.contingency_analysis_interval_hours * 3600 or
            current_utilization > 0.80  # Always run when stressed
        )

        if not should_run:
            return None

        self._last_contingency_analysis = datetime.now()

        return self.contingency.generate_report(
            faculty=faculty,
            blocks=blocks,
            assignments=assignments,
            coverage_requirements=coverage_requirements,
            current_utilization=current_utilization,
        )

    def _determine_overall_status(
        self,
        utilization_level: UtilizationLevel,
        defense_level: DefenseLevel,
        vulnerability: Optional[VulnerabilityReport],
    ) -> str:
        """Determine overall system status from components."""
        # Check for emergency conditions
        if utilization_level == UtilizationLevel.BLACK:
            return "emergency"
        if defense_level == DefenseLevel.EMERGENCY:
            return "emergency"

        # Check for critical conditions
        if utilization_level == UtilizationLevel.RED:
            return "critical"
        if defense_level == DefenseLevel.CONTAINMENT:
            return "critical"
        if vulnerability and vulnerability.phase_transition_risk == "critical":
            return "critical"

        # Check for degraded conditions
        if utilization_level == UtilizationLevel.ORANGE:
            return "degraded"
        if defense_level in (DefenseLevel.CONTROL, DefenseLevel.SAFETY_SYSTEMS):
            return "degraded"
        if vulnerability and not vulnerability.n1_pass:
            return "degraded"

        # Check for warning conditions
        if utilization_level == UtilizationLevel.YELLOW:
            return "warning"
        if vulnerability and not vulnerability.n2_pass:
            return "warning"

        return "healthy"

    def _build_recommendations(
        self,
        overall_status: str,
        utilization: UtilizationMetrics,
        vulnerability: Optional[VulnerabilityReport],
    ) -> tuple[list[str], list[str]]:
        """Build immediate actions and watch items from analysis."""
        immediate = []
        watch = []

        # Based on overall status
        if overall_status == "emergency":
            immediate.append("EMERGENCY: Activate crisis response immediately")
            immediate.append("Notify leadership and stakeholders")
            immediate.append("Prepare for service closure if needed")

        elif overall_status == "critical":
            immediate.append("Activate load shedding to ORANGE or RED level")
            immediate.append("Cancel all non-essential activities")
            immediate.append("Notify leadership")

        elif overall_status == "degraded":
            immediate.append("Review and defer non-urgent commitments")
            immediate.append("Confirm backup coverage is in place")

        # Based on utilization
        if utilization.level == UtilizationLevel.YELLOW:
            watch.append(f"Utilization at {utilization.utilization_rate:.0%} - approaching threshold")

        if utilization.buffer_remaining < 0.10:
            immediate.append(f"Buffer critically low ({utilization.buffer_remaining:.0%})")

        # Based on vulnerability
        if vulnerability:
            for action in vulnerability.recommended_actions:
                if "URGENT" in action.upper():
                    immediate.append(action)
                else:
                    watch.append(action)

            if vulnerability.phase_transition_risk in ("high", "critical"):
                immediate.append("System approaching phase transition - reduce load")

        return immediate, watch

    def _auto_activate_defense(self, recommended_level: DefenseLevel):
        """Auto-activate defense level if configured."""
        # Only auto-activate up to SAFETY_SYSTEMS level
        # Higher levels require manual confirmation
        if recommended_level.value <= DefenseLevel.SAFETY_SYSTEMS.value:
            current_actions = self.defense.get_level_status(recommended_level)
            for action in current_actions.actions:
                if action.is_automated and action.activation_count == 0:
                    self.defense.activate_action(recommended_level, action.name)
