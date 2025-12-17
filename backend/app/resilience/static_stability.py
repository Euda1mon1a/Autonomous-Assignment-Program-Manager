"""
Static Stability (AWS Architecture Pattern).

A system is "statically stable" if it continues operating correctly even when
components it depends on become unavailable. The system doesn't need to detect
the failure or make decisions—it just keeps working.

Key principle: "Cells should be able to operate completely independently if needed."

For scheduling, this means:
- Pre-computed fallback schedules for common failure scenarios
- No computation needed during crisis
- Instant switch to degraded mode
- Guaranteed response even if systems are down
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class FallbackScenario(Enum):
    """Pre-defined fallback scenarios."""
    SINGLE_FACULTY_LOSS = "1_faculty_loss"
    DOUBLE_FACULTY_LOSS = "2_faculty_loss"
    PCS_SEASON_50_PERCENT = "pcs_season_50_percent"
    HOLIDAY_SKELETON = "holiday_skeleton"
    PANDEMIC_ESSENTIAL = "pandemic_essential_only"
    MASS_CASUALTY = "mass_casualty_event"
    WEATHER_EMERGENCY = "weather_emergency"


@dataclass
class FallbackSchedule:
    """A pre-computed fallback schedule for a specific scenario."""
    id: UUID
    scenario: FallbackScenario
    name: str
    description: str
    created_at: datetime
    valid_from: date
    valid_until: date

    # The actual schedule data
    assignments: list[dict] = field(default_factory=list)

    # Metadata
    assumptions: list[str] = field(default_factory=list)
    services_reduced: list[str] = field(default_factory=list)
    coverage_rate: float = 0.0

    # Status
    is_active: bool = False
    last_activated: datetime | None = None
    activation_count: int = 0


@dataclass
class SchedulingZone:
    """
    An isolated scheduling unit that can operate independently.

    Implements AWS availability zone pattern for blast radius isolation.
    """
    id: UUID
    name: str
    services: list[str]
    dedicated_faculty: list[UUID]
    backup_faculty: list[UUID] = field(default_factory=list)
    minimum_coverage: int = 1

    def is_self_sufficient(self, available_faculty: set[UUID]) -> bool:
        """Check if zone can operate without borrowing."""
        available_dedicated = len(
            set(self.dedicated_faculty) & available_faculty
        )
        return available_dedicated >= self.minimum_coverage


class FallbackScheduler:
    """
    Manages pre-computed fallback schedules for instant crisis response.

    Design principles:
    1. Compute fallbacks during calm periods
    2. Store multiple scenarios ready to activate
    3. Zero decision-making delay during crisis
    4. Graceful degradation built-in
    """

    def __init__(self):
        self.fallback_schedules: dict[FallbackScenario, FallbackSchedule] = {}
        self.zones: dict[UUID, SchedulingZone] = {}
        self._schedule_generator: Callable | None = None

    def register_schedule_generator(
        self,
        generator: Callable[[FallbackScenario, date, date], list[dict]],
    ):
        """
        Register a function that can generate schedules for scenarios.

        The generator should accept:
        - scenario: FallbackScenario
        - start_date: date
        - end_date: date

        And return a list of assignment dictionaries.
        """
        self._schedule_generator = generator
        logger.info("Schedule generator registered")

    def create_zone(
        self,
        name: str,
        services: list[str],
        dedicated_faculty: list[UUID],
        minimum_coverage: int = 1,
    ) -> SchedulingZone:
        """
        Create an isolated scheduling zone.

        Zones provide blast radius isolation—failures in one zone
        cannot propagate to affect others.
        """
        zone = SchedulingZone(
            id=uuid4(),
            name=name,
            services=services,
            dedicated_faculty=dedicated_faculty,
            minimum_coverage=minimum_coverage,
        )
        self.zones[zone.id] = zone
        logger.info(f"Created scheduling zone: {name}")
        return zone

    def precompute_fallback(
        self,
        scenario: FallbackScenario,
        start_date: date,
        end_date: date,
        assumptions: list[str] = None,
        custom_assignments: list[dict] = None,
    ) -> FallbackSchedule:
        """
        Pre-compute and store a fallback schedule for a scenario.

        Args:
            scenario: The scenario this fallback addresses
            start_date: Start of the fallback period
            end_date: End of the fallback period
            assumptions: List of assumptions made in this schedule
            custom_assignments: Pre-built assignments (if not using generator)

        Returns:
            The created FallbackSchedule
        """
        if custom_assignments:
            assignments = custom_assignments
        elif self._schedule_generator:
            assignments = self._schedule_generator(scenario, start_date, end_date)
        else:
            assignments = []
            logger.warning(f"No schedule generator - fallback {scenario.value} has no assignments")

        # Calculate coverage rate
        coverage_rate = self._calculate_coverage_rate(assignments, start_date, end_date)

        # Determine services reduced based on scenario
        services_reduced = self._get_reduced_services(scenario)

        fallback = FallbackSchedule(
            id=uuid4(),
            scenario=scenario,
            name=self._get_scenario_name(scenario),
            description=self._get_scenario_description(scenario),
            created_at=datetime.now(),
            valid_from=start_date,
            valid_until=end_date,
            assignments=assignments,
            assumptions=assumptions or [],
            services_reduced=services_reduced,
            coverage_rate=coverage_rate,
        )

        self.fallback_schedules[scenario] = fallback
        logger.info(
            f"Pre-computed fallback: {scenario.value} "
            f"({len(assignments)} assignments, {coverage_rate:.0%} coverage)"
        )

        return fallback

    def precompute_all_fallbacks(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[FallbackScenario, FallbackSchedule]:
        """
        Pre-compute fallback schedules for all standard scenarios.

        Should be run during periods of normal operation to prepare
        for potential crises.
        """
        results = {}

        for scenario in FallbackScenario:
            try:
                fallback = self.precompute_fallback(scenario, start_date, end_date)
                results[scenario] = fallback
            except Exception as e:
                logger.error(f"Failed to precompute {scenario.value}: {e}")

        logger.info(f"Pre-computed {len(results)} fallback schedules")
        return results

    def activate_fallback(
        self,
        scenario: FallbackScenario,
    ) -> FallbackSchedule | None:
        """
        Activate a pre-computed fallback schedule.

        This is designed to be instant—no computation, just switch.

        Returns the fallback schedule if available, None if not found.
        """
        fallback = self.fallback_schedules.get(scenario)

        if not fallback:
            logger.error(f"No fallback available for scenario: {scenario.value}")
            return None

        # Check validity
        today = date.today()
        if not (fallback.valid_from <= today <= fallback.valid_until):
            logger.warning(
                f"Fallback {scenario.value} may be stale "
                f"(valid {fallback.valid_from} to {fallback.valid_until})"
            )

        # Activate
        fallback.is_active = True
        fallback.last_activated = datetime.now()
        fallback.activation_count += 1

        logger.warning(
            f"FALLBACK ACTIVATED: {scenario.value} - "
            f"{len(fallback.assignments)} assignments, "
            f"{fallback.coverage_rate:.0%} coverage. "
            f"Services reduced: {', '.join(fallback.services_reduced) or 'none'}"
        )

        return fallback

    def deactivate_fallback(self, scenario: FallbackScenario):
        """Deactivate a fallback and return to normal operations."""
        fallback = self.fallback_schedules.get(scenario)
        if fallback:
            fallback.is_active = False
            logger.info(f"Fallback deactivated: {scenario.value}")

    def get_active_fallbacks(self) -> list[FallbackSchedule]:
        """Get all currently active fallback schedules."""
        return [f for f in self.fallback_schedules.values() if f.is_active]

    def check_zone_health(
        self,
        available_faculty: set[UUID],
    ) -> dict[str, dict]:
        """
        Check health of all scheduling zones.

        Returns status for each zone indicating if it can operate
        independently with current faculty availability.
        """
        results = {}

        for _zone_id, zone in self.zones.items():
            is_healthy = zone.is_self_sufficient(available_faculty)
            dedicated_available = len(set(zone.dedicated_faculty) & available_faculty)
            backup_available = len(set(zone.backup_faculty) & available_faculty)

            results[zone.name] = {
                "healthy": is_healthy,
                "dedicated_available": dedicated_available,
                "dedicated_total": len(zone.dedicated_faculty),
                "backup_available": backup_available,
                "minimum_required": zone.minimum_coverage,
                "services": zone.services,
                "status": (
                    "GREEN" if is_healthy else
                    "YELLOW" if dedicated_available + backup_available >= zone.minimum_coverage else
                    "RED"
                ),
            }

        return results

    def get_best_fallback_for_situation(
        self,
        faculty_loss_count: int,
        is_pcs_season: bool = False,
        is_holiday: bool = False,
        is_emergency: bool = False,
    ) -> FallbackScenario | None:
        """
        Recommend the best fallback scenario for current situation.

        Args:
            faculty_loss_count: Number of faculty unavailable
            is_pcs_season: Whether in PCS/transition season
            is_holiday: Whether holiday period
            is_emergency: Whether external emergency

        Returns:
            Recommended FallbackScenario
        """
        if is_emergency:
            return FallbackScenario.MASS_CASUALTY

        if is_pcs_season and faculty_loss_count >= 5:
            return FallbackScenario.PCS_SEASON_50_PERCENT

        if is_holiday:
            return FallbackScenario.HOLIDAY_SKELETON

        if faculty_loss_count >= 2:
            return FallbackScenario.DOUBLE_FACULTY_LOSS

        if faculty_loss_count >= 1:
            return FallbackScenario.SINGLE_FACULTY_LOSS

        return None

    def get_status_report(self) -> dict:
        """Generate status report for all fallbacks and zones."""
        return {
            "fallbacks": {
                scenario.value: {
                    "available": scenario in self.fallback_schedules,
                    "active": (
                        self.fallback_schedules[scenario].is_active
                        if scenario in self.fallback_schedules else False
                    ),
                    "coverage_rate": (
                        f"{self.fallback_schedules[scenario].coverage_rate:.0%}"
                        if scenario in self.fallback_schedules else "N/A"
                    ),
                    "valid_until": (
                        self.fallback_schedules[scenario].valid_until.isoformat()
                        if scenario in self.fallback_schedules else None
                    ),
                    "activation_count": (
                        self.fallback_schedules[scenario].activation_count
                        if scenario in self.fallback_schedules else 0
                    ),
                }
                for scenario in FallbackScenario
            },
            "zones": {
                zone.name: {
                    "services": zone.services,
                    "dedicated_faculty_count": len(zone.dedicated_faculty),
                    "minimum_coverage": zone.minimum_coverage,
                }
                for zone in self.zones.values()
            },
            "summary": {
                "total_fallbacks_available": len(self.fallback_schedules),
                "active_fallbacks": len(self.get_active_fallbacks()),
                "total_zones": len(self.zones),
            },
        }

    def _calculate_coverage_rate(
        self,
        assignments: list[dict],
        start_date: date,
        end_date: date,
    ) -> float:
        """Calculate coverage rate for assignments."""
        if not assignments:
            return 0.0

        # Estimate number of blocks (2 per weekday)
        days = (end_date - start_date).days + 1
        weekdays = sum(
            1 for d in range(days)
            if (start_date + timedelta(days=d)).weekday() < 5
        )
        expected_blocks = weekdays * 2

        if expected_blocks == 0:
            return 1.0 if assignments else 0.0

        return min(1.0, len(assignments) / expected_blocks)

    def _get_scenario_name(self, scenario: FallbackScenario) -> str:
        """Get human-readable name for scenario."""
        names = {
            FallbackScenario.SINGLE_FACULTY_LOSS: "Single Faculty Loss",
            FallbackScenario.DOUBLE_FACULTY_LOSS: "Double Faculty Loss",
            FallbackScenario.PCS_SEASON_50_PERCENT: "PCS Season (50% Capacity)",
            FallbackScenario.HOLIDAY_SKELETON: "Holiday Skeleton Crew",
            FallbackScenario.PANDEMIC_ESSENTIAL: "Pandemic Essential Only",
            FallbackScenario.MASS_CASUALTY: "Mass Casualty Event",
            FallbackScenario.WEATHER_EMERGENCY: "Weather Emergency",
        }
        return names.get(scenario, scenario.value)

    def _get_scenario_description(self, scenario: FallbackScenario) -> str:
        """Get description for scenario."""
        descriptions = {
            FallbackScenario.SINGLE_FACULTY_LOSS: (
                "Schedule adjusted for loss of any single faculty member"
            ),
            FallbackScenario.DOUBLE_FACULTY_LOSS: (
                "Schedule adjusted for simultaneous loss of two faculty"
            ),
            FallbackScenario.PCS_SEASON_50_PERCENT: (
                "Summer PCS season with ~50% faculty unavailable"
            ),
            FallbackScenario.HOLIDAY_SKELETON: (
                "Minimal coverage for holiday periods"
            ),
            FallbackScenario.PANDEMIC_ESSENTIAL: (
                "Essential services only during pandemic"
            ),
            FallbackScenario.MASS_CASUALTY: (
                "All hands for mass casualty response"
            ),
            FallbackScenario.WEATHER_EMERGENCY: (
                "Reduced operations during weather emergency"
            ),
        }
        return descriptions.get(scenario, "")

    def _get_reduced_services(self, scenario: FallbackScenario) -> list[str]:
        """Get list of services reduced/suspended for scenario."""
        reductions = {
            FallbackScenario.SINGLE_FACULTY_LOSS: [],
            FallbackScenario.DOUBLE_FACULTY_LOSS: ["elective_procedures"],
            FallbackScenario.PCS_SEASON_50_PERCENT: [
                "research_time",
                "optional_education",
                "non_urgent_clinics",
            ],
            FallbackScenario.HOLIDAY_SKELETON: [
                "all_non_essential",
                "education",
                "research",
                "admin",
            ],
            FallbackScenario.PANDEMIC_ESSENTIAL: [
                "all_non_essential",
                "elective_procedures",
                "routine_clinics",
            ],
            FallbackScenario.MASS_CASUALTY: [
                "all_non_emergency",
            ],
            FallbackScenario.WEATHER_EMERGENCY: [
                "non_essential",
                "elective_procedures",
            ],
        }
        return reductions.get(scenario, [])
