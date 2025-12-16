"""
Resilience Service - Orchestrates all resilience components.

This service provides a unified interface to:

Tier 1 (Critical):
1. Monitor system health (utilization, coverage, redundancy)
2. Detect and respond to degraded conditions
3. Activate appropriate defense levels
4. Execute load shedding when needed
5. Switch to fallback schedules during crisis

Tier 2 (Strategic):
6. Homeostasis - Feedback loops and allostatic load tracking
7. Blast Radius Isolation - Zone-based failure containment
8. Le Chatelier - Equilibrium shift analysis and stress compensation

The service integrates:
Tier 1:
- UtilizationMonitor (queuing theory 80% threshold)
- DefenseInDepth (5-level nuclear safety paradigm)
- ContingencyAnalyzer (N-1/N-2 power grid analysis)
- FallbackScheduler (AWS static stability)
- SacrificeHierarchy (triage load shedding)

Tier 2:
- HomeostasisMonitor (feedback loops, allostatic load)
- BlastRadiusManager (zone isolation, borrowing)
- LeChatelierAnalyzer (equilibrium, stress compensation)
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional, Callable, Any
from uuid import UUID
import logging

from sqlalchemy.orm import Session

# Tier 1 imports
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

# Tier 2 imports
from app.resilience.homeostasis import (
    HomeostasisMonitor,
    AllostasisMetrics,
    AllostasisState,
    HomeostasisStatus,
    FeedbackLoop,
    PositiveFeedbackRisk,
    CorrectiveAction,
    DeviationSeverity,
)
from app.resilience.blast_radius import (
    BlastRadiusManager,
    SchedulingZone,
    ZoneStatus,
    ZoneType,
    ContainmentLevel,
    BorrowingRequest as ZoneBorrowingRequest,
    ZoneIncident,
    ZoneHealthReport,
    BlastRadiusReport,
)
from app.resilience.le_chatelier import (
    LeChatelierAnalyzer,
    SystemStress,
    StressType,
    CompensationResponse,
    CompensationType,
    EquilibriumShift,
    EquilibriumState,
    EquilibriumReport,
    StressResponsePrediction,
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
    # Tier 1: Utilization thresholds
    max_utilization: float = 0.80
    warning_threshold: float = 0.70

    # Tier 1: Auto-activation settings
    auto_activate_defense: bool = True
    auto_activate_fallback: bool = False  # Require manual confirmation
    auto_shed_load: bool = True

    # Tier 1: Monitoring intervals
    health_check_interval_minutes: int = 15
    contingency_analysis_interval_hours: int = 24

    # Tier 1: Notification settings
    alert_recipients: list[str] = field(default_factory=list)
    escalation_threshold: DefenseLevel = DefenseLevel.CONTAINMENT

    # Tier 2: Homeostasis settings
    homeostasis_check_interval_minutes: int = 30
    allostatic_warning_threshold: float = 50.0
    allostatic_critical_threshold: float = 80.0
    auto_correct_feedback_loops: bool = True

    # Tier 2: Blast radius settings
    enable_zone_isolation: bool = True
    default_containment_level: ContainmentLevel = ContainmentLevel.NONE
    auto_escalate_containment: bool = True

    # Tier 2: Le Chatelier settings
    base_compensation_rate: float = 0.5  # 50% natural compensation
    compensation_cost_multiplier: float = 1.5
    sustainability_threshold: float = 0.7


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

        # Initialize Tier 1 components
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

        # Initialize Tier 2 components
        self.homeostasis = HomeostasisMonitor()
        self.blast_radius = BlastRadiusManager()
        self.equilibrium = LeChatelierAnalyzer(
            base_compensation_rate=self.config.base_compensation_rate,
            compensation_cost_multiplier=self.config.compensation_cost_multiplier,
            sustainability_threshold=self.config.sustainability_threshold,
        )

        # State tracking
        self._last_health_check: Optional[datetime] = None
        self._last_contingency_analysis: Optional[datetime] = None
        self._last_homeostasis_check: Optional[datetime] = None
        self._crisis_mode: bool = False
        self._event_handlers: dict[str, list[Callable]] = {}

        # Initialize default zones if zone isolation is enabled
        if self.config.enable_zone_isolation:
            self._initialize_default_zones()

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

    def _initialize_default_zones(self):
        """Initialize default scheduling zones for blast radius isolation."""
        self.blast_radius.create_default_zones()
        logger.info("Initialized default scheduling zones for blast radius isolation")

    # =========================================================================
    # Tier 2: Homeostasis Methods
    # =========================================================================

    def check_homeostasis(
        self,
        current_values: dict[str, float],
    ) -> HomeostasisStatus:
        """
        Check homeostasis feedback loops and trigger corrections.

        Args:
            current_values: Dict of setpoint_name -> current_value
                Example: {"coverage_rate": 0.92, "faculty_utilization": 0.78}

        Returns:
            HomeostasisStatus with feedback loop states and recommendations
        """
        self._last_homeostasis_check = datetime.now()

        # Check all feedback loops
        corrections = self.homeostasis.check_all_loops(current_values)

        # Get allostasis metrics if available
        faculty_metrics = list(self.homeostasis.allostasis_metrics.values())

        # Detect positive feedback risks
        system_metrics = {"coverage_rate": current_values.get("coverage_rate", 1.0)}
        risks = self.homeostasis.detect_positive_feedback_risks(faculty_metrics, system_metrics)

        # Get overall status
        status = self.homeostasis.get_status(faculty_metrics)

        # Emit event if corrections triggered
        if corrections:
            self._emit_event("homeostasis_correction", {
                "corrections_count": len(corrections),
                "corrections": [
                    {"type": c.action_type.value, "severity": c.deviation_severity.value}
                    for c in corrections
                ],
            })

        # Emit event if positive feedback risks detected
        if risks:
            self._emit_event("positive_feedback_detected", {
                "risks_count": len(risks),
                "urgent_count": sum(1 for r in risks if r.urgency == "immediate"),
            })

        return status

    def calculate_allostatic_load(
        self,
        entity_id: UUID,
        entity_type: str,
        stress_factors: dict,
    ) -> AllostasisMetrics:
        """
        Calculate allostatic load for a faculty member or the system.

        Args:
            entity_id: Faculty ID or system UUID
            entity_type: "faculty" or "system"
            stress_factors: Dict of stress factor values

        Returns:
            AllostasisMetrics with calculated load and risk level
        """
        metrics = self.homeostasis.calculate_allostatic_load(
            entity_id, entity_type, stress_factors
        )

        # Check thresholds and emit events
        if metrics.total_allostatic_load >= self.config.allostatic_critical_threshold:
            self._emit_event("allostatic_critical", {
                "entity_id": str(entity_id),
                "entity_type": entity_type,
                "load": metrics.total_allostatic_load,
            })
        elif metrics.total_allostatic_load >= self.config.allostatic_warning_threshold:
            self._emit_event("allostatic_warning", {
                "entity_id": str(entity_id),
                "entity_type": entity_type,
                "load": metrics.total_allostatic_load,
            })

        return metrics

    def get_feedback_loop_status(self, setpoint_name: str) -> Optional[FeedbackLoop]:
        """Get status of a specific feedback loop."""
        return self.homeostasis.get_feedback_loop(setpoint_name)

    # =========================================================================
    # Tier 2: Blast Radius Methods
    # =========================================================================

    def check_zone_health(self, zone_id: UUID) -> Optional[ZoneHealthReport]:
        """
        Check health of a specific scheduling zone.

        Args:
            zone_id: Zone to check

        Returns:
            ZoneHealthReport with zone status and recommendations
        """
        return self.blast_radius.check_zone_health(zone_id)

    def check_all_zones(self) -> BlastRadiusReport:
        """
        Check health of all scheduling zones.

        Returns:
            BlastRadiusReport with all zone statuses and overall containment status
        """
        report = self.blast_radius.check_all_zones()

        # Auto-escalate containment if configured
        if (
            self.config.auto_escalate_containment and
            report.zones_critical > 0 and
            self.blast_radius.global_containment == ContainmentLevel.NONE
        ):
            self.set_containment_level(
                ContainmentLevel.MODERATE,
                f"Auto-escalated due to {report.zones_critical} critical zones"
            )

        return report

    def create_zone(
        self,
        name: str,
        zone_type: ZoneType,
        description: str,
        services: list[str],
        minimum_coverage: int = 1,
        optimal_coverage: int = 2,
        priority: int = 5,
    ) -> SchedulingZone:
        """Create a new scheduling zone."""
        zone = self.blast_radius.create_zone(
            name=name,
            zone_type=zone_type,
            description=description,
            services=services,
            minimum_coverage=minimum_coverage,
            optimal_coverage=optimal_coverage,
            priority=priority,
        )

        self._emit_event("zone_created", {
            "zone_id": str(zone.id),
            "zone_name": name,
            "zone_type": zone_type.value,
        })

        return zone

    def assign_faculty_to_zone(
        self,
        zone_id: UUID,
        faculty_id: UUID,
        faculty_name: str,
        role: str = "primary",
    ) -> bool:
        """Assign a faculty member to a zone."""
        return self.blast_radius.assign_faculty_to_zone(
            zone_id, faculty_id, faculty_name, role
        )

    def request_zone_borrowing(
        self,
        requesting_zone_id: UUID,
        lending_zone_id: UUID,
        faculty_id: UUID,
        priority: str,
        reason: str,
        duration_hours: int = 8,
    ) -> Optional[ZoneBorrowingRequest]:
        """Request to borrow faculty from another zone."""
        from app.resilience.blast_radius import BorrowingPriority

        priority_map = {
            "critical": BorrowingPriority.CRITICAL,
            "high": BorrowingPriority.HIGH,
            "medium": BorrowingPriority.MEDIUM,
            "low": BorrowingPriority.LOW,
        }

        request = self.blast_radius.request_borrowing(
            requesting_zone_id=requesting_zone_id,
            lending_zone_id=lending_zone_id,
            faculty_id=faculty_id,
            priority=priority_map.get(priority, BorrowingPriority.MEDIUM),
            reason=reason,
            duration_hours=duration_hours,
        )

        if request:
            self._emit_event("zone_borrowing_requested", {
                "request_id": str(request.id),
                "priority": priority,
                "status": request.status,
            })

        return request

    def record_zone_incident(
        self,
        zone_id: UUID,
        incident_type: str,
        description: str,
        severity: str,
        faculty_affected: list[UUID] = None,
        services_affected: list[str] = None,
    ) -> Optional[ZoneIncident]:
        """Record an incident affecting a zone."""
        incident = self.blast_radius.record_incident(
            zone_id=zone_id,
            incident_type=incident_type,
            description=description,
            severity=severity,
            faculty_affected=faculty_affected,
            services_affected=services_affected,
        )

        if incident:
            self._emit_event("zone_incident_recorded", {
                "incident_id": str(incident.id),
                "zone_id": str(zone_id),
                "severity": severity,
            })

        return incident

    def set_containment_level(
        self,
        level: ContainmentLevel,
        reason: str,
    ):
        """Set system-wide containment level."""
        previous = self.blast_radius.global_containment
        self.blast_radius.set_global_containment(level, reason)

        self._emit_event("containment_changed", {
            "previous_level": previous.value,
            "new_level": level.value,
            "reason": reason,
        })

    # =========================================================================
    # Tier 2: Le Chatelier / Equilibrium Methods
    # =========================================================================

    def apply_system_stress(
        self,
        stress_type: StressType,
        description: str,
        magnitude: float,
        duration_days: int,
        capacity_impact: float,
        demand_impact: float = 0.0,
        is_acute: bool = True,
        is_reversible: bool = True,
    ) -> SystemStress:
        """
        Apply a stress to the system and track its impact.

        Args:
            stress_type: Type of stress (faculty_loss, demand_surge, etc.)
            description: Description of the stress
            magnitude: 0.0 - 1.0 (fraction of system affected)
            duration_days: Expected duration
            capacity_impact: Negative value for capacity reduction
            demand_impact: Positive value for demand increase
            is_acute: True for sudden stress
            is_reversible: True if stress can be removed

        Returns:
            SystemStress record
        """
        stress = self.equilibrium.apply_stress(
            stress_type=stress_type,
            description=description,
            magnitude=magnitude,
            duration_days=duration_days,
            capacity_impact=capacity_impact,
            demand_impact=demand_impact,
            is_acute=is_acute,
            is_reversible=is_reversible,
        )

        self._emit_event("stress_applied", {
            "stress_id": str(stress.id),
            "stress_type": stress_type.value,
            "magnitude": magnitude,
            "capacity_impact": capacity_impact,
        })

        return stress

    def initiate_compensation(
        self,
        stress_id: UUID,
        compensation_type: CompensationType,
        description: str,
        magnitude: float,
        effectiveness: float = 0.8,
        sustainability_days: int = 30,
        immediate_cost: float = 0.0,
        hidden_cost: float = 0.0,
    ) -> Optional[CompensationResponse]:
        """
        Initiate a compensation response to a stress.

        Args:
            stress_id: ID of the stress being compensated
            compensation_type: Type of compensation
            description: What's being done
            magnitude: How much compensation (0.0 - 1.0)
            effectiveness: Expected effectiveness
            sustainability_days: How long can this be maintained
            immediate_cost: Direct costs
            hidden_cost: Indirect costs (burnout, etc.)

        Returns:
            CompensationResponse if successful
        """
        compensation = self.equilibrium.initiate_compensation(
            stress_id=stress_id,
            compensation_type=compensation_type,
            description=description,
            magnitude=magnitude,
            effectiveness=effectiveness,
            sustainability_days=sustainability_days,
            immediate_cost=immediate_cost,
            hidden_cost=hidden_cost,
        )

        if compensation:
            self._emit_event("compensation_initiated", {
                "compensation_id": str(compensation.id),
                "stress_id": str(stress_id),
                "compensation_type": compensation_type.value,
                "magnitude": magnitude,
            })

        return compensation

    def calculate_equilibrium_shift(
        self,
        original_capacity: float,
        original_demand: float,
    ) -> EquilibriumShift:
        """
        Calculate the equilibrium shift from original state to current.

        Per Le Chatelier's principle, compensation is always partial
        and the new equilibrium will be different from the old one.

        Args:
            original_capacity: Capacity before stress
            original_demand: Demand before stress

        Returns:
            EquilibriumShift analysis
        """
        shift = self.equilibrium.calculate_equilibrium_shift(
            original_capacity, original_demand
        )

        self._emit_event("equilibrium_shift_calculated", {
            "shift_id": str(shift.id),
            "original_coverage": shift.original_coverage_rate,
            "new_coverage": shift.new_coverage_rate,
            "equilibrium_state": shift.equilibrium_state.value,
            "is_sustainable": shift.is_sustainable,
        })

        return shift

    def predict_stress_response(
        self,
        stress_type: StressType,
        magnitude: float,
        duration_days: int,
        capacity_impact: float,
        demand_impact: float = 0.0,
    ) -> StressResponsePrediction:
        """
        Predict how the system will respond to a potential stress.

        Use this for planning before actually applying stress.

        Args:
            stress_type: Type of stress
            magnitude: Fraction of system affected
            duration_days: Expected duration
            capacity_impact: Capacity reduction
            demand_impact: Demand increase

        Returns:
            StressResponsePrediction with recommendations
        """
        return self.equilibrium.predict_stress_response(
            stress_type=stress_type,
            magnitude=magnitude,
            duration_days=duration_days,
            capacity_impact=capacity_impact,
            demand_impact=demand_impact,
        )

    def get_equilibrium_report(self) -> EquilibriumReport:
        """Get comprehensive equilibrium analysis report."""
        return self.equilibrium.get_report()

    def resolve_stress(self, stress_id: UUID, resolution_notes: str = ""):
        """Mark a stress as resolved."""
        self.equilibrium.resolve_stress(stress_id, resolution_notes)
        self._emit_event("stress_resolved", {
            "stress_id": str(stress_id),
            "resolution_notes": resolution_notes,
        })

    # =========================================================================
    # Tier 2: Combined Status
    # =========================================================================

    def get_tier2_status(self, current_metrics: dict[str, float] = None) -> dict:
        """
        Get combined status of all Tier 2 resilience components.

        Args:
            current_metrics: Optional current values for homeostasis check

        Returns:
            Dict with combined Tier 2 status
        """
        # Homeostasis status
        if current_metrics:
            homeostasis_status = self.check_homeostasis(current_metrics)
        else:
            homeostasis_status = self.homeostasis.get_status()

        # Blast radius status
        blast_radius_report = self.check_all_zones()

        # Equilibrium status
        equilibrium_report = self.get_equilibrium_report()

        # Determine overall Tier 2 status
        if (
            homeostasis_status.overall_state == AllostasisState.ALLOSTATIC_OVERLOAD or
            equilibrium_report.current_equilibrium_state == EquilibriumState.CRITICAL or
            blast_radius_report.zones_critical > len(self.blast_radius.zones) * 0.3
        ):
            tier2_status = "critical"
        elif (
            homeostasis_status.overall_state in (AllostasisState.ALLOSTASIS, AllostasisState.ALLOSTATIC_LOAD) or
            equilibrium_report.current_equilibrium_state in (EquilibriumState.STRESSED, EquilibriumState.UNSUSTAINABLE) or
            blast_radius_report.zones_degraded > len(self.blast_radius.zones) * 0.3
        ):
            tier2_status = "degraded"
        else:
            tier2_status = "healthy"

        # Build recommendations
        recommendations = []
        recommendations.extend(homeostasis_status.recommendations)
        recommendations.extend(blast_radius_report.recommendations)
        recommendations.extend(equilibrium_report.recommendations)

        return {
            "generated_at": datetime.now().isoformat(),
            "homeostasis": {
                "state": homeostasis_status.overall_state.value,
                "feedback_loops_healthy": homeostasis_status.feedback_loops_healthy,
                "feedback_loops_deviating": homeostasis_status.feedback_loops_deviating,
                "average_allostatic_load": homeostasis_status.average_allostatic_load,
                "positive_feedback_risks": homeostasis_status.positive_feedback_risks,
            },
            "blast_radius": {
                "total_zones": blast_radius_report.total_zones,
                "zones_healthy": blast_radius_report.zones_healthy,
                "zones_degraded": blast_radius_report.zones_degraded,
                "zones_critical": blast_radius_report.zones_critical,
                "containment_active": blast_radius_report.containment_active,
                "containment_level": blast_radius_report.containment_level.value,
            },
            "equilibrium": {
                "state": equilibrium_report.current_equilibrium_state.value,
                "current_coverage_rate": equilibrium_report.current_coverage_rate,
                "compensation_debt": equilibrium_report.compensation_debt,
                "sustainability_score": equilibrium_report.sustainability_score,
                "days_until_exhaustion": equilibrium_report.days_until_exhaustion,
            },
            "tier2_status": tier2_status,
            "recommendations": recommendations[:10],  # Top 10 recommendations
        }
