"""
Defense in Depth (Nuclear Engineering Safety Paradigm).

Implements the 5-level defense in depth strategy from nuclear reactor safety:

Level 1: Prevention - Design to prevent abnormal operation
Level 2: Control - Detect and respond to abnormal operation
Level 3: Safety Systems - Engineered systems to control accidents
Level 4: Containment - Limit consequences of severe accidents
Level 5: Emergency Response - Mitigate radiological consequences

Each level operates independently, assuming all previous levels have failed.
The N+2 redundancy rule ensures critical functions survive 2 simultaneous failures.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any

logger = logging.getLogger(__name__)


class DefenseLevel(IntEnum):
    """The five levels of defense in depth."""
    PREVENTION = 1      # Design to prevent problems
    CONTROL = 2         # Detect and respond to problems
    SAFETY_SYSTEMS = 3  # Automated safety systems
    CONTAINMENT = 4     # Limit damage spread
    EMERGENCY = 5       # Crisis response


@dataclass
class DefenseAction:
    """A specific action within a defense level."""
    name: str
    description: str
    level: DefenseLevel
    is_automated: bool = False
    trigger_condition: str | None = None
    action_handler: Callable | None = None
    last_activated: datetime | None = None
    activation_count: int = 0


@dataclass
class DefenseStatus:
    """Status of a defense level."""
    level: DefenseLevel
    name: str
    status: str  # "ready", "active", "degraded", "failed"
    actions: list[DefenseAction] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)


@dataclass
class RedundancyStatus:
    """Status of redundancy for a critical function."""
    function_name: str
    required_minimum: int
    current_available: int
    redundancy_level: int  # How many can fail before minimum
    status: str  # "N+2" (healthy), "N+1" (warning), "N+0" (minimum), "BELOW" (critical)


class DefenseInDepth:
    """
    Implements defense in depth for scheduling resilience.

    Maps nuclear safety concepts to scheduling:

    Level 1 (Prevention):
    - Maintain 20% capacity buffer
    - Cross-train faculty on multiple services
    - Proactive absence management

    Level 2 (Control):
    - Real-time coverage monitoring
    - Early warning alerts for gaps
    - Trend analysis for burnout

    Level 3 (Safety Systems):
    - Automated reassignment algorithms
    - Pre-approved backup pools
    - Overtime authorization triggers

    Level 4 (Containment):
    - Service reduction protocols
    - Protected minimum services
    - Isolation of affected areas

    Level 5 (Emergency):
    - Crisis communication
    - External escalation
    - Post-incident review
    """

    def __init__(self):
        self.levels: dict[DefenseLevel, DefenseStatus] = {}
        self.redundancy_requirements: dict[str, int] = {}
        self._initialize_levels()

    def _initialize_levels(self):
        """Initialize all defense levels with default actions."""
        self.levels = {
            DefenseLevel.PREVENTION: DefenseStatus(
                level=DefenseLevel.PREVENTION,
                name="Prevention",
                status="ready",
                actions=[
                    DefenseAction(
                        name="capacity_buffer",
                        description="Maintain 20% capacity buffer in scheduling",
                        level=DefenseLevel.PREVENTION,
                        is_automated=True,
                    ),
                    DefenseAction(
                        name="cross_training",
                        description="Ensure faculty cross-trained on multiple services",
                        level=DefenseLevel.PREVENTION,
                        is_automated=False,
                    ),
                    DefenseAction(
                        name="absence_forecasting",
                        description="Proactive monitoring of upcoming absences",
                        level=DefenseLevel.PREVENTION,
                        is_automated=True,
                    ),
                ],
            ),
            DefenseLevel.CONTROL: DefenseStatus(
                level=DefenseLevel.CONTROL,
                name="Control",
                status="ready",
                actions=[
                    DefenseAction(
                        name="coverage_monitoring",
                        description="Real-time monitoring of coverage gaps",
                        level=DefenseLevel.CONTROL,
                        is_automated=True,
                        trigger_condition="coverage < 95%",
                    ),
                    DefenseAction(
                        name="early_warning",
                        description="Alert when coverage dropping",
                        level=DefenseLevel.CONTROL,
                        is_automated=True,
                        trigger_condition="coverage < 90%",
                    ),
                    DefenseAction(
                        name="burnout_tracking",
                        description="Monitor faculty workload and fatigue indicators",
                        level=DefenseLevel.CONTROL,
                        is_automated=True,
                    ),
                ],
            ),
            DefenseLevel.SAFETY_SYSTEMS: DefenseStatus(
                level=DefenseLevel.SAFETY_SYSTEMS,
                name="Safety Systems",
                status="ready",
                actions=[
                    DefenseAction(
                        name="auto_reassignment",
                        description="Automated reassignment when gaps detected",
                        level=DefenseLevel.SAFETY_SYSTEMS,
                        is_automated=True,
                        trigger_condition="gap_detected",
                    ),
                    DefenseAction(
                        name="backup_activation",
                        description="Activate pre-approved backup coverage",
                        level=DefenseLevel.SAFETY_SYSTEMS,
                        is_automated=True,
                        trigger_condition="primary_unavailable",
                    ),
                    DefenseAction(
                        name="overtime_authorization",
                        description="Automatic overtime authorization for critical gaps",
                        level=DefenseLevel.SAFETY_SYSTEMS,
                        is_automated=False,
                        trigger_condition="coverage < 85%",
                    ),
                ],
            ),
            DefenseLevel.CONTAINMENT: DefenseStatus(
                level=DefenseLevel.CONTAINMENT,
                name="Containment",
                status="ready",
                actions=[
                    DefenseAction(
                        name="service_reduction",
                        description="Reduce non-essential services",
                        level=DefenseLevel.CONTAINMENT,
                        is_automated=False,
                        trigger_condition="coverage < 80%",
                    ),
                    DefenseAction(
                        name="minimum_service_protection",
                        description="Protect patient safety coverage at all costs",
                        level=DefenseLevel.CONTAINMENT,
                        is_automated=True,
                    ),
                    DefenseAction(
                        name="zone_isolation",
                        description="Isolate affected scheduling zones",
                        level=DefenseLevel.CONTAINMENT,
                        is_automated=False,
                    ),
                ],
            ),
            DefenseLevel.EMERGENCY: DefenseStatus(
                level=DefenseLevel.EMERGENCY,
                name="Emergency Response",
                status="ready",
                actions=[
                    DefenseAction(
                        name="crisis_communication",
                        description="Notify all stakeholders of emergency",
                        level=DefenseLevel.EMERGENCY,
                        is_automated=False,
                        trigger_condition="coverage < 70%",
                    ),
                    DefenseAction(
                        name="external_escalation",
                        description="Escalate to hospital leadership / external authorities",
                        level=DefenseLevel.EMERGENCY,
                        is_automated=False,
                        trigger_condition="coverage < 60%",
                    ),
                    DefenseAction(
                        name="incident_documentation",
                        description="Document all decisions for review",
                        level=DefenseLevel.EMERGENCY,
                        is_automated=True,
                    ),
                ],
            ),
        }

    def get_level_status(self, level: DefenseLevel) -> DefenseStatus:
        """Get status of a specific defense level."""
        return self.levels[level]

    def get_all_status(self) -> list[DefenseStatus]:
        """Get status of all defense levels."""
        return list(self.levels.values())

    def activate_action(
        self,
        level: DefenseLevel,
        action_name: str,
        context: dict | None = None,
    ) -> bool:
        """
        Activate a specific defense action.

        Returns True if action was activated successfully.
        """
        level_status = self.levels.get(level)
        if not level_status:
            logger.error(f"Unknown defense level: {level}")
            return False

        for action in level_status.actions:
            if action.name == action_name:
                action.last_activated = datetime.now()
                action.activation_count += 1

                logger.info(
                    f"Defense action activated: Level {level.value} ({level.name}) - "
                    f"{action.name}: {action.description}"
                )

                if action.action_handler and context:
                    try:
                        action.action_handler(context)
                    except Exception as e:
                        logger.error(f"Action handler failed: {e}")
                        return False

                return True

        logger.warning(f"Action not found: {action_name} in level {level}")
        return False

    def check_redundancy(
        self,
        function_name: str,
        available_providers: list,
        minimum_required: int,
    ) -> RedundancyStatus:
        """
        Check redundancy status for a critical function.

        Uses the N+2 rule: should be able to lose 2 providers and still operate.
        """
        available = len(available_providers)
        redundancy = available - minimum_required

        if redundancy >= 2:
            status = "N+2"  # Healthy - can lose 2
        elif redundancy == 1:
            status = "N+1"  # Warning - can only lose 1
        elif redundancy == 0:
            status = "N+0"  # At minimum - no redundancy
        else:
            status = "BELOW"  # Below minimum - critical

        return RedundancyStatus(
            function_name=function_name,
            required_minimum=minimum_required,
            current_available=available,
            redundancy_level=max(0, redundancy),
            status=status,
        )

    def check_all_redundancy(
        self,
        services: dict[str, dict],
    ) -> list[RedundancyStatus]:
        """
        Check redundancy for all critical services.

        Args:
            services: Dict of service_name -> {
                'available_providers': list,
                'minimum_required': int
            }

        Returns:
            List of RedundancyStatus for each service
        """
        results = []
        for name, config in services.items():
            status = self.check_redundancy(
                function_name=name,
                available_providers=config.get('available_providers', []),
                minimum_required=config.get('minimum_required', 1),
            )
            results.append(status)

            # Log warnings for degraded redundancy
            if status.status == "N+1":
                logger.warning(f"Reduced redundancy for {name}: only 1 backup available")
            elif status.status == "N+0":
                logger.warning(f"No redundancy for {name}: at minimum staffing")
            elif status.status == "BELOW":
                logger.error(f"CRITICAL: {name} below minimum staffing!")

        return results

    def get_recommended_level(self, coverage_rate: float) -> DefenseLevel:
        """
        Get the recommended active defense level based on coverage.

        Higher levels should be activated as coverage drops.
        """
        if coverage_rate >= 0.95:
            return DefenseLevel.PREVENTION
        elif coverage_rate >= 0.90:
            return DefenseLevel.CONTROL
        elif coverage_rate >= 0.80:
            return DefenseLevel.SAFETY_SYSTEMS
        elif coverage_rate >= 0.70:
            return DefenseLevel.CONTAINMENT
        else:
            return DefenseLevel.EMERGENCY

    def get_status_report(self) -> dict:
        """Generate comprehensive defense status report."""
        return {
            "levels": [
                {
                    "level": status.level.value,
                    "name": status.name,
                    "status": status.status,
                    "actions": [
                        {
                            "name": a.name,
                            "description": a.description,
                            "automated": a.is_automated,
                            "activations": a.activation_count,
                            "last_activated": (
                                a.last_activated.isoformat() if a.last_activated else None
                            ),
                        }
                        for a in status.actions
                    ],
                    "alerts": status.alerts,
                }
                for status in self.levels.values()
            ],
            "summary": {
                "all_levels_ready": all(
                    s.status == "ready" for s in self.levels.values()
                ),
                "active_alerts": sum(
                    len(s.alerts) for s in self.levels.values()
                ),
            },
        }

    def register_action_handler(
        self,
        level: DefenseLevel,
        action_name: str,
        handler: Callable[[dict], Any],
    ):
        """Register a handler function for a defense action."""
        level_status = self.levels.get(level)
        if level_status:
            for action in level_status.actions:
                if action.name == action_name:
                    action.action_handler = handler
                    logger.info(f"Handler registered for {level.name}/{action_name}")
                    return

        logger.warning(f"Could not register handler: {level.name}/{action_name} not found")
