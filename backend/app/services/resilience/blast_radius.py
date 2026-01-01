"""Blast Radius Service - Zone containment and failure isolation.

This service implements the AWS Availability Zone pattern for scheduling,
ensuring failures are contained within defined boundaries ("zones").

Key Principle: "Zones should operate completely independently if needed."

Features:
1. Zone Health Monitoring - Track zone-level capacity and status
2. Blast Radius Calculation - Analyze failure containment effectiveness
3. Cross-Zone Borrowing - Controlled resource sharing with limits
4. Containment Level Management - Prevent cascade across zone boundaries
5. Zone Incident Recording - Track and respond to zone-level issues

Usage:
    service = BlastRadiusService(db)
    report = service.calculate_blast_radius()

    if report.zones_critical > 0:
        service.set_containment_level("moderate", "Critical zones detected")
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.resilience.blast_radius import (
    BlastRadiusManager,
    BlastRadiusReport,
    BorrowingPriority,
    ContainmentLevel,
    SchedulingZone,
    ZoneHealthReport,
    ZoneIncident,
    ZoneStatus,
    ZoneType,
)

logger = logging.getLogger(__name__)


@dataclass
class BlastRadiusAnalysisResult:
    """Result of blast radius analysis."""

    # Zone counts
    total_zones: int
    zones_healthy: int
    zones_degraded: int
    zones_critical: int

    # Containment status
    containment_active: bool
    containment_level: str
    zones_isolated: int

    # Borrowing status
    active_borrowing_requests: int
    pending_borrowing_requests: int

    # Zone details
    zone_details: list[dict] = field(default_factory=list)

    # Recommendations
    recommendations: list[str] = field(default_factory=list)

    # Severity assessment
    severity: str = "healthy"  # healthy, warning, degraded, critical

    # Timestamp
    analyzed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ZoneHealthResult:
    """Result of single zone health check."""

    zone_id: str
    zone_name: str
    zone_type: str
    status: str
    containment_level: str
    is_self_sufficient: bool
    has_surplus: bool
    available_faculty: int
    minimum_required: int
    optimal_required: int
    capacity_ratio: float
    faculty_borrowed: int
    faculty_lent: int
    net_borrowing: int
    active_incidents: int
    services_affected: list[str]
    recommendations: list[str]
    checked_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ZoneCreationResult:
    """Result of zone creation."""

    success: bool
    zone_id: str | None = None
    zone_name: str | None = None
    message: str = ""
    error_code: str | None = None


@dataclass
class IncidentRecordResult:
    """Result of incident recording."""

    success: bool
    incident_id: str | None = None
    zone_id: str | None = None
    containment_activated: bool = False
    message: str = ""
    error_code: str | None = None
    # FIX: Added started_at field to provide timestamp to API response
    started_at: datetime | None = None
    capacity_lost: float = 0.0


class BlastRadiusService:
    """
    Service for managing blast radius isolation through scheduling zones.

    Implements AWS availability zone pattern to ensure failures are contained
    within zone boundaries and don't cascade across the entire system.

    Args:
        db: SQLAlchemy database session
        config: Optional configuration dict with settings:
            - enable_zone_isolation: bool (default True)
            - auto_escalate_containment: bool (default True)
            - default_containment_level: str (default "none")
    """

    def __init__(
        self,
        db: Session,
        config: dict[str, Any] | None = None,
    ):
        self.db = db
        self.config = config or {}

        # Initialize the blast radius manager
        self._manager = BlastRadiusManager()

        # Apply configuration
        self._enable_zone_isolation = self.config.get("enable_zone_isolation", True)
        self._auto_escalate = self.config.get("auto_escalate_containment", True)

        # Initialize default zones if zone isolation is enabled
        if self._enable_zone_isolation and not self._manager.zones:
            self._initialize_default_zones()

    def _initialize_default_zones(self) -> None:
        """Initialize default scheduling zones."""
        self._manager.create_default_zones()
        logger.info("Initialized default scheduling zones for blast radius isolation")

    def calculate_blast_radius(
        self,
        check_all_zones: bool = True,
    ) -> BlastRadiusAnalysisResult:
        """
        Calculate blast radius and analyze zone containment status.

        This is the main analysis method that evaluates how well failures
        are being contained within scheduling zones.

        Args:
            check_all_zones: If True, check all zones. If False, use cached status.

        Returns:
            BlastRadiusAnalysisResult with comprehensive analysis
        """
        logger.info(f"Calculating blast radius (check_all={check_all_zones})")

        try:
            # Get the full report from the manager
            report = self._manager.check_all_zones()

            # Convert zone reports to detail dicts
            zone_details = []
            for zr in report.zone_reports:
                zone_details.append(
                    {
                        "zone_id": str(zr.zone_id),
                        "zone_name": zr.zone_name,
                        "zone_type": zr.zone_type.value,
                        "status": zr.status.value,
                        "containment_level": zr.containment_level.value,
                        "is_self_sufficient": zr.is_self_sufficient,
                        "has_surplus": zr.has_surplus,
                        "available_faculty": zr.available_faculty,
                        "minimum_required": zr.minimum_required,
                        "capacity_ratio": zr.capacity_ratio,
                        "active_incidents": zr.active_incidents,
                        "recommendations": zr.recommendations,
                    }
                )

            # Determine severity
            severity = self._determine_severity(report)

            # Auto-escalate containment if configured
            if self._auto_escalate and report.zones_critical > 0:
                if self._manager.global_containment == ContainmentLevel.NONE:
                    self._manager.set_global_containment(
                        ContainmentLevel.MODERATE,
                        f"Auto-escalated due to {report.zones_critical} critical zones",
                    )
                    logger.warning("Auto-escalated containment to MODERATE")

            return BlastRadiusAnalysisResult(
                total_zones=report.total_zones,
                zones_healthy=report.zones_healthy,
                zones_degraded=report.zones_degraded,
                zones_critical=report.zones_critical,
                containment_active=report.containment_active,
                containment_level=report.containment_level.value,
                zones_isolated=report.zones_isolated,
                active_borrowing_requests=report.active_borrowing_requests,
                pending_borrowing_requests=report.pending_borrowing_requests,
                zone_details=zone_details,
                recommendations=report.recommendations,
                severity=severity,
                analyzed_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Blast radius calculation failed: {e}")
            raise

    def _determine_severity(self, report: BlastRadiusReport) -> str:
        """Determine overall severity from blast radius report."""
        if report.zones_critical > 0:
            return "critical"
        elif report.zones_degraded > report.total_zones * 0.3:
            return "degraded"
        elif report.zones_degraded > 0:
            return "warning"
        return "healthy"

    def check_zone_health(self, zone_id: UUID) -> ZoneHealthResult | None:
        """
        Check health of a specific scheduling zone.

        Args:
            zone_id: UUID of the zone to check

        Returns:
            ZoneHealthResult or None if zone not found
        """
        report = self._manager.check_zone_health(zone_id)

        if not report:
            return None

        return ZoneHealthResult(
            zone_id=str(report.zone_id),
            zone_name=report.zone_name,
            zone_type=report.zone_type.value,
            status=report.status.value,
            containment_level=report.containment_level.value,
            is_self_sufficient=report.is_self_sufficient,
            has_surplus=report.has_surplus,
            available_faculty=report.available_faculty,
            minimum_required=report.minimum_required,
            optimal_required=report.optimal_required,
            capacity_ratio=report.capacity_ratio,
            faculty_borrowed=report.faculty_borrowed,
            faculty_lent=report.faculty_lent,
            net_borrowing=report.net_borrowing,
            active_incidents=report.active_incidents,
            services_affected=report.services_affected,
            recommendations=report.recommendations,
            checked_at=datetime.utcnow(),
        )

    def get_all_zones(self) -> list[dict]:
        """
        Get all scheduling zones and their current status.

        Returns:
            List of zone information dicts
        """
        zones = []
        for zone in self._manager.zones.values():
            zones.append(
                {
                    "id": str(zone.id),
                    "name": zone.name,
                    "zone_type": zone.zone_type.value,
                    "description": zone.description,
                    "services": zone.services,
                    "minimum_coverage": zone.minimum_coverage,
                    "optimal_coverage": zone.optimal_coverage,
                    "priority": zone.priority,
                    "status": zone.status.value,
                    "containment_level": zone.containment_level.value,
                    "borrowing_limit": zone.borrowing_limit,
                    "lending_limit": zone.lending_limit,
                    "is_active": True,
                }
            )
        return zones

    def create_zone(
        self,
        name: str,
        zone_type: str,
        description: str = "",
        services: list[str] | None = None,
        minimum_coverage: int = 1,
        optimal_coverage: int = 2,
        priority: int = 5,
    ) -> ZoneCreationResult:
        """
        Create a new scheduling zone.

        Args:
            name: Zone name
            zone_type: Type of zone (inpatient, outpatient, education, etc.)
            description: Zone description
            services: Services provided by this zone
            minimum_coverage: Minimum faculty needed
            optimal_coverage: Optimal faculty count
            priority: Zone priority (higher = more protected)

        Returns:
            ZoneCreationResult with creation status
        """
        try:
            # Map string zone type to enum
            type_map = {
                "inpatient": ZoneType.INPATIENT,
                "outpatient": ZoneType.OUTPATIENT,
                "education": ZoneType.EDUCATION,
                "research": ZoneType.RESEARCH,
                "admin": ZoneType.ADMINISTRATIVE,
                "administrative": ZoneType.ADMINISTRATIVE,
                "on_call": ZoneType.ON_CALL,
            }

            zone_type_enum = type_map.get(zone_type.lower(), ZoneType.INPATIENT)

            zone = self._manager.create_zone(
                name=name,
                zone_type=zone_type_enum,
                description=description,
                services=services or [],
                minimum_coverage=minimum_coverage,
                optimal_coverage=optimal_coverage,
                priority=priority,
            )

            logger.info(f"Created zone: {name} ({zone_type})")

            return ZoneCreationResult(
                success=True,
                zone_id=str(zone.id),
                zone_name=zone.name,
                message=f"Zone '{name}' created successfully",
            )

        except Exception as e:
            logger.error(f"Failed to create zone: {e}")
            return ZoneCreationResult(
                success=False,
                message=f"Failed to create zone: {str(e)}",
                error_code="ZONE_CREATION_FAILED",
            )

    def assign_faculty_to_zone(
        self,
        zone_id: UUID,
        faculty_id: UUID,
        faculty_name: str,
        role: str = "primary",
    ) -> bool:
        """
        Assign a faculty member to a zone.

        Args:
            zone_id: Zone to assign to
            faculty_id: Faculty member ID
            faculty_name: Faculty member name
            role: "primary", "secondary", or "backup"

        Returns:
            True if successful
        """
        success = self._manager.assign_faculty_to_zone(
            zone_id=zone_id,
            faculty_id=faculty_id,
            faculty_name=faculty_name,
            role=role,
        )

        if success:
            logger.info(f"Assigned {faculty_name} to zone {zone_id} as {role}")
        else:
            logger.warning(f"Failed to assign {faculty_name} to zone {zone_id}")

        return success

    def record_incident(
        self,
        zone_id: UUID,
        incident_type: str,
        description: str,
        severity: str,
        faculty_affected: list[UUID] | None = None,
        services_affected: list[str] | None = None,
    ) -> IncidentRecordResult:
        """
        Record an incident affecting a zone.

        This may trigger containment activation based on severity.

        Args:
            zone_id: Affected zone
            incident_type: Type of incident (faculty_loss, demand_surge, etc.)
            description: What happened
            severity: "minor", "moderate", "severe", "critical"
            faculty_affected: List of affected faculty IDs
            services_affected: List of affected services

        Returns:
            IncidentRecordResult with recording status and timestamp
        """
        try:
            incident = self._manager.record_incident(
                zone_id=zone_id,
                incident_type=incident_type,
                description=description,
                severity=severity,
                faculty_affected=faculty_affected,
                services_affected=services_affected,
            )

            if not incident:
                return IncidentRecordResult(
                    success=False,
                    message="Zone not found",
                    error_code="ZONE_NOT_FOUND",
                )

            # Check if containment was activated
            zone = self._manager.zones.get(zone_id)
            containment_activated = (
                zone and zone.containment_level != ContainmentLevel.NONE
            )

            logger.warning(
                f"Incident recorded in zone {zone_id}: {incident_type} ({severity})"
            )

            # FIX: Return started_at and capacity_lost from the incident
            return IncidentRecordResult(
                success=True,
                incident_id=str(incident.id),
                zone_id=str(zone_id),
                containment_activated=containment_activated,
                message=f"Incident recorded: {incident_type}",
                started_at=incident.started_at,
                capacity_lost=incident.capacity_lost,
            )

        except Exception as e:
            logger.error(f"Failed to record incident: {e}")
            return IncidentRecordResult(
                success=False,
                message=f"Failed to record incident: {str(e)}",
                error_code="INCIDENT_RECORD_FAILED",
            )

    def set_containment_level(
        self,
        level: str,
        reason: str,
    ) -> bool:
        """
        Set system-wide containment level.

        Args:
            level: Containment level (none, soft, moderate, strict, lockdown)
            reason: Why containment is being set

        Returns:
            True if successful
        """
        level_map = {
            "none": ContainmentLevel.NONE,
            "soft": ContainmentLevel.SOFT,
            "moderate": ContainmentLevel.MODERATE,
            "strict": ContainmentLevel.STRICT,
            "lockdown": ContainmentLevel.LOCKDOWN,
        }

        containment_level = level_map.get(level.lower())
        if not containment_level:
            logger.error(f"Invalid containment level: {level}")
            return False

        self._manager.set_global_containment(containment_level, reason)
        logger.warning(f"Containment set to {level}: {reason}")

        return True

    def get_containment_level(self) -> str:
        """Get current global containment level."""
        return self._manager.global_containment.value

    def request_borrowing(
        self,
        requesting_zone_id: UUID,
        lending_zone_id: UUID,
        faculty_id: UUID,
        priority: str,
        reason: str,
        duration_hours: int = 8,
    ) -> dict | None:
        """
        Request to borrow faculty from another zone.

        Args:
            requesting_zone_id: Zone needing faculty
            lending_zone_id: Zone to borrow from
            faculty_id: Specific faculty to borrow
            priority: Priority level (critical, high, medium, low)
            reason: Why borrowing is needed
            duration_hours: How long needed

        Returns:
            Dict with request details or None if blocked
        """
        priority_map = {
            "critical": BorrowingPriority.CRITICAL,
            "high": BorrowingPriority.HIGH,
            "medium": BorrowingPriority.MEDIUM,
            "low": BorrowingPriority.LOW,
        }

        request = self._manager.request_borrowing(
            requesting_zone_id=requesting_zone_id,
            lending_zone_id=lending_zone_id,
            faculty_id=faculty_id,
            priority=priority_map.get(priority.lower(), BorrowingPriority.MEDIUM),
            reason=reason,
            duration_hours=duration_hours,
        )

        if not request:
            return None

        return {
            "request_id": str(request.id),
            "status": request.status,
            "priority": request.priority.value,
            "duration_hours": request.duration_hours,
            "approved": request.status == "approved",
        }

    def complete_borrowing(self, request_id: UUID, was_effective: bool = True) -> None:
        """Mark a borrowing request as completed."""
        self._manager.complete_borrowing(request_id, was_effective)
        logger.info(f"Borrowing request {request_id} completed")

    def resolve_incident(
        self,
        incident_id: UUID,
        resolution_notes: str,
        containment_successful: bool = True,
    ) -> None:
        """Resolve an incident."""
        self._manager.resolve_incident(
            incident_id=incident_id,
            resolution_notes=resolution_notes,
            containment_successful=containment_successful,
        )
        logger.info(f"Incident {incident_id} resolved")

    def get_zones_by_status(self, status: str) -> list[dict]:
        """Get all zones with a specific status."""
        status_map = {
            "green": ZoneStatus.GREEN,
            "yellow": ZoneStatus.YELLOW,
            "orange": ZoneStatus.ORANGE,
            "red": ZoneStatus.RED,
            "black": ZoneStatus.BLACK,
        }

        zone_status = status_map.get(status.lower())
        if not zone_status:
            return []

        zones = self._manager.get_zones_by_status(zone_status)
        return [
            {
                "id": str(z.id),
                "name": z.name,
                "zone_type": z.zone_type.value,
                "status": z.status.value,
            }
            for z in zones
        ]

    def get_zone_by_type(self, zone_type: str) -> dict | None:
        """Get first zone of a specific type."""
        type_map = {
            "inpatient": ZoneType.INPATIENT,
            "outpatient": ZoneType.OUTPATIENT,
            "education": ZoneType.EDUCATION,
            "research": ZoneType.RESEARCH,
            "admin": ZoneType.ADMINISTRATIVE,
            "on_call": ZoneType.ON_CALL,
        }

        zone_type_enum = type_map.get(zone_type.lower())
        if not zone_type_enum:
            return None

        zone = self._manager.get_zone_by_type(zone_type_enum)
        if not zone:
            return None

        return {
            "id": str(zone.id),
            "name": zone.name,
            "zone_type": zone.zone_type.value,
            "status": zone.status.value,
            "priority": zone.priority,
        }

    @property
    def manager(self) -> BlastRadiusManager:
        """Access the underlying BlastRadiusManager for advanced operations."""
        return self._manager
