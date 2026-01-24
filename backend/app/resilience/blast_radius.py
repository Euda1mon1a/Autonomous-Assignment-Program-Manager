"""
Blast Radius Isolation (AWS Architecture Pattern).

Design systems so failures are contained within defined boundaries ("cells" or
"availability zones"). A problem in one area cannot propagate to affect others.

Key Principle: "Cells should be able to operate completely independently if needed."

This module implements:
1. Scheduling Zones - Isolated units with dedicated faculty
2. Zone Health Monitoring - Track zone-level capacity and status
3. Cross-Zone Borrowing - Controlled resource sharing with limits
4. Failure Containment - Prevent cascade across zone boundaries
5. Zone Recovery - Restore zones after incidents

Zone Design Principles:
- Each zone has dedicated faculty as primary coverage
- Cross-zone borrowing requires explicit approval
- Zones cannot be depleted below minimum for other zones
- Failures in one zone trigger local degradation, not system-wide

Example Zones:
- Zone A: Inpatient (ICU, Wards, Procedures)
- Zone B: Outpatient (Clinics, Consults)
- Zone C: Education (Didactics, Simulation)

When Zone C loses capacity, Zones A and B continue unaffected.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class ZoneStatus(str, Enum):
    """Health status of a scheduling zone."""

    GREEN = "green"  # Fully operational, can support others
    YELLOW = "yellow"  # Operational but at minimum capacity
    ORANGE = "orange"  # Degraded, using backup faculty
    RED = "red"  # Critical, needs support
    BLACK = "black"  # Failed, services suspended


class ZoneType(str, Enum):
    """Types of scheduling zones."""

    INPATIENT = "inpatient"  # ICU, wards, procedures
    OUTPATIENT = "outpatient"  # Clinics, consults
    EDUCATION = "education"  # Didactics, simulation
    RESEARCH = "research"  # Research activities
    ADMINISTRATIVE = "admin"  # Meetings, committees
    ON_CALL = "on_call"  # Call coverage


class BorrowingPriority(str, Enum):
    """Priority levels for cross-zone borrowing."""

    CRITICAL = "critical"  # Life safety, must fulfill
    HIGH = "high"  # Important, should fulfill if possible
    MEDIUM = "medium"  # Normal priority
    LOW = "low"  # Optional, decline if any strain


class ContainmentLevel(str, Enum):
    """Level of failure containment."""

    NONE = "none"  # No containment active
    SOFT = "soft"  # Advisory, log borrowing
    MODERATE = "moderate"  # Require approval for borrowing
    STRICT = "strict"  # No cross-zone borrowing
    LOCKDOWN = "lockdown"  # Zone completely isolated


@dataclass
class ZoneFacultyAssignment:
    """Faculty assignment to a zone."""

    faculty_id: UUID
    faculty_name: str
    role: str  # "primary", "secondary", "backup"
    available: bool = True
    assigned_at: datetime = field(default_factory=datetime.now)


@dataclass
class BorrowingRequest:
    """Request to borrow faculty from another zone."""

    id: UUID
    requesting_zone_id: UUID
    lending_zone_id: UUID
    faculty_id: UUID
    priority: BorrowingPriority
    reason: str
    requested_at: datetime
    duration_hours: int

    # Approval tracking
    status: str = "pending"  # pending, approved, denied, completed
    approved_by: str | None = None
    approved_at: datetime | None = None
    denial_reason: str | None = None

    # Execution tracking
    started_at: datetime | None = None
    completed_at: datetime | None = None
    was_effective: bool | None = None


@dataclass
class ZoneIncident:
    """An incident affecting a zone."""

    id: UUID
    zone_id: UUID
    incident_type: str  # "faculty_loss", "demand_surge", "quality_issue", "external"
    description: str
    started_at: datetime
    severity: str  # "minor", "moderate", "severe", "critical"

    # Impact
    faculty_affected: list[UUID] = field(default_factory=list)
    capacity_lost: float = 0.0
    services_affected: list[str] = field(default_factory=list)

    # Resolution
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    containment_successful: bool = True


@dataclass
class SchedulingZone:
    """
    An isolated scheduling unit that can operate independently.

    Implements AWS availability zone pattern for blast radius isolation.
    Each zone has dedicated resources and can operate without other zones.
    """

    id: UUID
    name: str
    zone_type: ZoneType
    description: str

    # Services in this zone
    services: list[str] = field(default_factory=list)

    # Faculty assignments
    primary_faculty: list[ZoneFacultyAssignment] = field(default_factory=list)
    secondary_faculty: list[ZoneFacultyAssignment] = field(default_factory=list)
    backup_faculty: list[ZoneFacultyAssignment] = field(default_factory=list)

    # Capacity requirements
    minimum_coverage: int = 1
    optimal_coverage: int = 2
    maximum_coverage: int = 5

    # Status
    status: ZoneStatus = ZoneStatus.GREEN
    containment_level: ContainmentLevel = ContainmentLevel.NONE
    last_status_change: datetime | None = None

    # Borrowing rules
    can_borrow_from: list[UUID] = field(default_factory=list)
    can_lend_to: list[UUID] = field(default_factory=list)
    borrowing_limit: int = 2  # Max faculty can borrow at once
    lending_limit: int = 1  # Max faculty can lend at once
    borrowed_faculty: list[UUID] = field(default_factory=list)
    lent_faculty: list[UUID] = field(default_factory=list)

    # Priority (higher = more protected)
    priority: int = 5

    # Metrics
    created_at: datetime = field(default_factory=datetime.now)
    incidents: list[ZoneIncident] = field(default_factory=list)
    total_borrowing_requests: int = 0
    total_lending_events: int = 0

    def get_available_primary(self) -> list[ZoneFacultyAssignment]:
        """Get available primary faculty."""
        return [f for f in self.primary_faculty if f.available]

    def get_available_secondary(self) -> list[ZoneFacultyAssignment]:
        """Get available secondary faculty."""
        return [f for f in self.secondary_faculty if f.available]

    def get_available_backup(self) -> list[ZoneFacultyAssignment]:
        """Get available backup faculty."""
        return [f for f in self.backup_faculty if f.available]

    def get_total_available(self) -> int:
        """Get total available faculty count."""
        return (
            len(self.get_available_primary())
            + len(self.get_available_secondary())
            + len(self.get_available_backup())
            + len(self.borrowed_faculty)
            - len(self.lent_faculty)
        )

    def is_self_sufficient(self) -> bool:
        """Check if zone can operate without borrowing."""
        return self.get_total_available() >= self.minimum_coverage

    def has_surplus(self) -> bool:
        """Check if zone can lend faculty."""
        return self.get_total_available() > self.optimal_coverage

    def calculate_status(self) -> ZoneStatus:
        """Calculate current zone status."""
        available = self.get_total_available()

        if available < self.minimum_coverage * 0.5:
            return ZoneStatus.BLACK
        elif available < self.minimum_coverage:
            return ZoneStatus.RED
        elif available < self.minimum_coverage + 1:
            return ZoneStatus.ORANGE
        elif available <= self.optimal_coverage:
            return ZoneStatus.YELLOW
        else:
            return ZoneStatus.GREEN


@dataclass
class ZoneHealthReport:
    """Health report for a scheduling zone."""

    zone_id: UUID
    zone_name: str
    zone_type: ZoneType
    checked_at: datetime

    # Status
    status: ZoneStatus
    containment_level: ContainmentLevel
    is_self_sufficient: bool
    has_surplus: bool

    # Capacity
    available_faculty: int
    minimum_required: int
    optimal_required: int
    capacity_ratio: float  # available / minimum

    # Borrowing
    faculty_borrowed: int
    faculty_lent: int
    net_borrowing: int

    # Active issues
    active_incidents: int
    services_affected: list[str]

    # Recommendations
    recommendations: list[str]


@dataclass
class BlastRadiusReport:
    """Overall blast radius containment report."""

    generated_at: datetime
    total_zones: int
    zones_healthy: int
    zones_degraded: int
    zones_critical: int

    # Containment status
    containment_active: bool
    containment_level: ContainmentLevel
    zones_isolated: int

    # Borrowing summary
    active_borrowing_requests: int
    pending_borrowing_requests: int

    # Zone reports
    zone_reports: list[ZoneHealthReport]

    # Overall recommendations
    recommendations: list[str]


class BlastRadiusManager:
    """
    Manages blast radius isolation through scheduling zones.

    Ensures failures are contained within zone boundaries and
    controls cross-zone resource sharing.
    """

    def __init__(self) -> None:
        self.zones: dict[UUID, SchedulingZone] = {}
        self.borrowing_requests: list[BorrowingRequest] = []
        self.global_containment: ContainmentLevel = ContainmentLevel.NONE
        self.approval_handlers: dict[BorrowingPriority, Callable] = {}

        # Event handlers
        self._on_zone_status_change: list[Callable] = []
        self._on_containment_change: list[Callable] = []

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
        """
        Create a new scheduling zone.

        Args:
            name: Zone name
            zone_type: Type of zone
            description: Zone description
            services: Services provided by this zone
            minimum_coverage: Minimum faculty needed
            optimal_coverage: Optimal faculty count
            priority: Zone priority (higher = more protected)

        Returns:
            Created SchedulingZone
        """
        zone = SchedulingZone(
            id=uuid4(),
            name=name,
            zone_type=zone_type,
            description=description,
            services=services,
            minimum_coverage=minimum_coverage,
            optimal_coverage=optimal_coverage,
            priority=priority,
        )

        self.zones[zone.id] = zone
        logger.info(f"Created scheduling zone: {name} ({zone_type.value})")

        return zone

    def create_default_zones(self) -> list[SchedulingZone]:
        """Create default zone configuration."""
        zones = [
            self.create_zone(
                name="Inpatient Clinical",
                zone_type=ZoneType.INPATIENT,
                description="ICU, hospital wards, and inpatient procedures",
                services=["icu", "wards", "procedures", "consults"],
                minimum_coverage=3,
                optimal_coverage=5,
                priority=10,  # Highest priority
            ),
            self.create_zone(
                name="Outpatient Clinical",
                zone_type=ZoneType.OUTPATIENT,
                description="Outpatient clinics and ambulatory care",
                services=["clinics", "ambulatory", "follow_ups"],
                minimum_coverage=2,
                optimal_coverage=4,
                priority=8,
            ),
            self.create_zone(
                name="Call Coverage",
                zone_type=ZoneType.ON_CALL,
                description="Night, weekend, and holiday call coverage",
                services=["night_call", "weekend_call", "holiday_call"],
                minimum_coverage=2,
                optimal_coverage=3,
                priority=9,
            ),
            self.create_zone(
                name="Education",
                zone_type=ZoneType.EDUCATION,
                description="Resident education and didactics",
                services=["didactics", "simulation", "supervision"],
                minimum_coverage=1,
                optimal_coverage=2,
                priority=6,
            ),
            self.create_zone(
                name="Research",
                zone_type=ZoneType.RESEARCH,
                description="Research activities and protected time",
                services=["research", "publications", "grants"],
                minimum_coverage=0,
                optimal_coverage=2,
                priority=3,
            ),
            self.create_zone(
                name="Administrative",
                zone_type=ZoneType.ADMINISTRATIVE,
                description="Meetings, committees, and admin tasks",
                services=["meetings", "committees", "admin"],
                minimum_coverage=0,
                optimal_coverage=1,
                priority=1,  # Lowest priority
            ),
        ]

        # Set up borrowing relationships (higher can borrow from lower)
        for _i, zone in enumerate(zones):
            # Can borrow from lower priority zones
            zone.can_borrow_from = [z.id for z in zones if z.priority < zone.priority]
            # Can lend to higher priority zones
            zone.can_lend_to = [z.id for z in zones if z.priority > zone.priority]

        return zones

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
        zone = self.zones.get(zone_id)
        if not zone:
            return False

        assignment = ZoneFacultyAssignment(
            faculty_id=faculty_id,
            faculty_name=faculty_name,
            role=role,
        )

        if role == "primary":
            zone.primary_faculty.append(assignment)
        elif role == "secondary":
            zone.secondary_faculty.append(assignment)
        elif role == "backup":
            zone.backup_faculty.append(assignment)
        else:
            return False

        logger.info(f"Assigned {faculty_name} to zone {zone.name} as {role}")
        return True

    def request_borrowing(
        self,
        requesting_zone_id: UUID,
        lending_zone_id: UUID,
        faculty_id: UUID,
        priority: BorrowingPriority,
        reason: str,
        duration_hours: int = 8,
    ) -> BorrowingRequest | None:
        """
        Request to borrow faculty from another zone.

        Cross-zone borrowing is the controlled mechanism for sharing resources
        while maintaining blast radius isolation. Requests are validated
        against containment levels, zone relationships, and capacity limits.

        Args:
            requesting_zone_id: UUID of the zone needing faculty.
            lending_zone_id: UUID of the zone to borrow from.
            faculty_id: UUID of the specific faculty member to borrow.
            priority: BorrowingPriority level (CRITICAL, HIGH, MEDIUM, LOW).
            reason: Description of why borrowing is needed.
            duration_hours: How long the faculty is needed. Default 8 hours.

        Returns:
            BorrowingRequest: If request is created (may be pending or auto-approved).
            None: If request is blocked by containment or capacity limits.

        Example:
            >>> manager = BlastRadiusManager()
            >>> # Request emergency borrowing from outpatient to cover inpatient
            >>> request = manager.request_borrowing(
            ...     requesting_zone_id=inpatient_zone.id,
            ...     lending_zone_id=outpatient_zone.id,
            ...     faculty_id=dr_smith.id,
            ...     priority=BorrowingPriority.CRITICAL,
            ...     reason="ICU attending called out sick"
            ... )
        """
        requesting_zone = self.zones.get(requesting_zone_id)
        lending_zone = self.zones.get(lending_zone_id)

        if not requesting_zone or not lending_zone:
            return None

        # Check containment level
        if self.global_containment == ContainmentLevel.LOCKDOWN:
            logger.warning("Borrowing blocked: System in lockdown")
            return None

        if self.global_containment == ContainmentLevel.STRICT and priority not in (
            BorrowingPriority.CRITICAL,
        ):
            logger.warning(
                "Borrowing blocked: Strict containment, only critical allowed"
            )
            return None

        # Check zone-level containment
        if lending_zone.containment_level == ContainmentLevel.LOCKDOWN:
            logger.warning(
                f"Borrowing blocked: Zone {lending_zone.name} is locked down"
            )
            return None

        # Check if lending zone is in can_borrow_from list
        if lending_zone_id not in requesting_zone.can_borrow_from:
            logger.warning(
                f"Borrowing not allowed: {requesting_zone.name} cannot borrow from {lending_zone.name}"
            )
            return None

        # Check lending zone capacity
        if not lending_zone.has_surplus():
            logger.warning(f"Lending zone {lending_zone.name} has no surplus capacity")
            if priority not in (BorrowingPriority.CRITICAL, BorrowingPriority.HIGH):
                return None

        # Check limits
        if len(requesting_zone.borrowed_faculty) >= requesting_zone.borrowing_limit:
            logger.warning(f"Zone {requesting_zone.name} at borrowing limit")
            return None

        if len(lending_zone.lent_faculty) >= lending_zone.lending_limit:
            logger.warning(f"Zone {lending_zone.name} at lending limit")
            if priority != BorrowingPriority.CRITICAL:
                return None

        # Create request
        request = BorrowingRequest(
            id=uuid4(),
            requesting_zone_id=requesting_zone_id,
            lending_zone_id=lending_zone_id,
            faculty_id=faculty_id,
            priority=priority,
            reason=reason,
            requested_at=datetime.now(),
            duration_hours=duration_hours,
        )

        # Auto-approve for critical priority
        if priority == BorrowingPriority.CRITICAL:
            self._approve_borrowing(request, "auto_critical")
        elif self.global_containment == ContainmentLevel.NONE:
            # Auto-approve when no containment
            self._approve_borrowing(request, "auto_no_containment")

        self.borrowing_requests.append(request)
        requesting_zone.total_borrowing_requests += 1

        logger.info(
            f"Borrowing request created: {requesting_zone.name} <- {lending_zone.name} "
            f"({priority.value} priority, status: {request.status})"
        )

        return request

    def _approve_borrowing(self, request: BorrowingRequest, approved_by: str) -> None:
        """Approve and execute a borrowing request."""
        request.status = "approved"
        request.approved_by = approved_by
        request.approved_at = datetime.now()
        request.started_at = datetime.now()

        # Update zones
        requesting_zone = self.zones.get(request.requesting_zone_id)
        lending_zone = self.zones.get(request.lending_zone_id)

        if requesting_zone:
            requesting_zone.borrowed_faculty.append(request.faculty_id)

        if lending_zone:
            lending_zone.lent_faculty.append(request.faculty_id)
            lending_zone.total_lending_events += 1

    def complete_borrowing(
        self,
        request_id: UUID,
        was_effective: bool = True,
    ) -> None:
        """Mark a borrowing request as completed."""
        for request in self.borrowing_requests:
            if request.id == request_id:
                request.status = "completed"
                request.completed_at = datetime.now()
                request.was_effective = was_effective

                # Update zones
                requesting_zone = self.zones.get(request.requesting_zone_id)
                lending_zone = self.zones.get(request.lending_zone_id)

                if (
                    requesting_zone
                    and request.faculty_id in requesting_zone.borrowed_faculty
                ):
                    requesting_zone.borrowed_faculty.remove(request.faculty_id)

                if lending_zone and request.faculty_id in lending_zone.lent_faculty:
                    lending_zone.lent_faculty.remove(request.faculty_id)

                return

    def record_incident(
        self,
        zone_id: UUID,
        incident_type: str,
        description: str,
        severity: str,
        faculty_affected: list[UUID] | None = None,
        services_affected: list[str] | None = None,
    ) -> ZoneIncident | None:
        """
        Record an incident affecting a zone.

        Args:
            zone_id: Affected zone
            incident_type: Type of incident
            description: What happened
            severity: "minor", "moderate", "severe", "critical"
            faculty_affected: List of affected faculty
            services_affected: List of affected services

        Returns:
            ZoneIncident if recorded
        """
        zone = self.zones.get(zone_id)
        if not zone:
            return None

        incident = ZoneIncident(
            id=uuid4(),
            zone_id=zone_id,
            incident_type=incident_type,
            description=description,
            started_at=datetime.now(),
            severity=severity,
            faculty_affected=faculty_affected or [],
            services_affected=services_affected or zone.services.copy(),
        )

        # Calculate capacity lost
        if faculty_affected:
            total_faculty = (
                len(zone.primary_faculty)
                + len(zone.secondary_faculty)
                + len(zone.backup_faculty)
            )
            if total_faculty > 0:
                incident.capacity_lost = len(faculty_affected) / total_faculty

        zone.incidents.append(incident)

        # Update zone status
        self._update_zone_status(zone)

        # Trigger containment if severe
        if severity in ("severe", "critical"):
            self._activate_containment(zone, incident)

        logger.warning(
            f"Incident recorded in zone {zone.name}: {incident_type} ({severity})"
        )

        return incident

    def _update_zone_status(self, zone: SchedulingZone) -> None:
        """Update zone status based on current capacity."""
        previous_status = zone.status
        zone.status = zone.calculate_status()

        if zone.status != previous_status:
            zone.last_status_change = datetime.now()
            logger.info(
                f"Zone {zone.name} status changed: {previous_status.value} -> {zone.status.value}"
            )

            # Notify handlers
            for handler in self._on_zone_status_change:
                try:
                    handler(zone, previous_status, zone.status)
                except Exception as e:
                    logger.error(f"Zone status handler error: {e}")

    def _activate_containment(
        self, zone: SchedulingZone, incident: ZoneIncident
    ) -> None:
        """Activate containment for a zone based on incident."""
        if incident.severity == "critical":
            zone.containment_level = ContainmentLevel.STRICT
        elif incident.severity == "severe":
            zone.containment_level = ContainmentLevel.MODERATE
        else:
            zone.containment_level = ContainmentLevel.SOFT

        logger.warning(
            f"Containment activated for zone {zone.name}: {zone.containment_level.value}"
        )

    def set_global_containment(
        self,
        level: ContainmentLevel,
        reason: str,
    ) -> None:
        """Set system-wide containment level."""
        previous = self.global_containment
        self.global_containment = level

        logger.warning(
            f"Global containment changed: {previous.value} -> {level.value}. Reason: {reason}"
        )

        # Notify handlers
        for handler in self._on_containment_change:
            try:
                handler(previous, level, reason)
            except Exception as e:
                logger.error(f"Containment handler error: {e}")

    def check_zone_health(self, zone_id: UUID) -> ZoneHealthReport | None:
        """
        Check health of a specific zone.

        Args:
            zone_id: Zone to check

        Returns:
            ZoneHealthReport if zone exists
        """
        zone = self.zones.get(zone_id)
        if not zone:
            return None

        # Update status first
        self._update_zone_status(zone)

        available = zone.get_total_available()
        capacity_ratio = (
            available / zone.minimum_coverage
            if zone.minimum_coverage > 0
            else float("inf")
        )

        # Build recommendations
        recommendations = []

        if zone.status == ZoneStatus.BLACK:
            recommendations.append(
                f"CRITICAL: Zone {zone.name} has failed - activate fallback immediately"
            )
        elif zone.status == ZoneStatus.RED:
            recommendations.append(
                f"Zone {zone.name} critical - request emergency support"
            )
            if zone.can_borrow_from:
                recommendations.append("Consider borrowing from available zones")
        elif zone.status == ZoneStatus.ORANGE:
            recommendations.append(f"Zone {zone.name} degraded - monitor closely")
        elif zone.has_surplus():
            recommendations.append(
                f"Zone {zone.name} has surplus - can support other zones"
            )

        # Check active incidents
        active_incidents = [i for i in zone.incidents if not i.resolved_at]

        return ZoneHealthReport(
            zone_id=zone.id,
            zone_name=zone.name,
            zone_type=zone.zone_type,
            checked_at=datetime.now(),
            status=zone.status,
            containment_level=zone.containment_level,
            is_self_sufficient=zone.is_self_sufficient(),
            has_surplus=zone.has_surplus(),
            available_faculty=available,
            minimum_required=zone.minimum_coverage,
            optimal_required=zone.optimal_coverage,
            capacity_ratio=capacity_ratio,
            faculty_borrowed=len(zone.borrowed_faculty),
            faculty_lent=len(zone.lent_faculty),
            net_borrowing=len(zone.borrowed_faculty) - len(zone.lent_faculty),
            active_incidents=len(active_incidents),
            services_affected=[
                s for i in active_incidents for s in i.services_affected
            ],
            recommendations=recommendations,
        )

    def check_all_zones(self) -> BlastRadiusReport:
        """
        Check health of all zones and generate blast radius report.

        Returns:
            Comprehensive BlastRadiusReport
        """
        zone_reports = []
        healthy = 0
        degraded = 0
        critical = 0
        isolated = 0

        for zone in self.zones.values():
            report = self.check_zone_health(zone.id)
            if report:
                zone_reports.append(report)

                if report.status == ZoneStatus.GREEN:
                    healthy += 1
                elif report.status in (ZoneStatus.YELLOW, ZoneStatus.ORANGE):
                    degraded += 1
                else:
                    critical += 1

                if zone.containment_level != ContainmentLevel.NONE:
                    isolated += 1

        # Count borrowing requests
        pending = len([r for r in self.borrowing_requests if r.status == "pending"])
        active = len(
            [
                r
                for r in self.borrowing_requests
                if r.status == "approved" and not r.completed_at
            ]
        )

        # Build recommendations
        recommendations = []

        if critical > 0:
            recommendations.append(f"ALERT: {critical} zone(s) in critical status")

        if degraded > len(self.zones) * 0.5:
            recommendations.append(
                "Over 50% of zones degraded - consider global load shedding"
            )

        if self.global_containment == ContainmentLevel.NONE and critical > 0:
            recommendations.append("Consider activating containment to prevent cascade")

        if pending > 3:
            recommendations.append(
                f"{pending} pending borrowing requests - review and process"
            )

        return BlastRadiusReport(
            generated_at=datetime.now(),
            total_zones=len(self.zones),
            zones_healthy=healthy,
            zones_degraded=degraded,
            zones_critical=critical,
            containment_active=self.global_containment != ContainmentLevel.NONE,
            containment_level=self.global_containment,
            zones_isolated=isolated,
            active_borrowing_requests=active,
            pending_borrowing_requests=pending,
            zone_reports=zone_reports,
            recommendations=recommendations,
        )

    def get_zone_by_type(self, zone_type: ZoneType) -> SchedulingZone | None:
        """Get first zone of a specific type."""
        for zone in self.zones.values():
            if zone.zone_type == zone_type:
                return zone
        return None

    def get_zones_by_status(self, status: ZoneStatus) -> list[SchedulingZone]:
        """Get all zones with a specific status."""
        return [z for z in self.zones.values() if z.status == status]

    def register_status_handler(
        self,
        handler: Callable[[SchedulingZone, ZoneStatus, ZoneStatus], None],
    ) -> None:
        """Register handler for zone status changes."""
        self._on_zone_status_change.append(handler)

    def register_containment_handler(
        self,
        handler: Callable[[ContainmentLevel, ContainmentLevel, str], None],
    ) -> None:
        """Register handler for containment level changes."""
        self._on_containment_change.append(handler)

    def resolve_incident(
        self,
        incident_id: UUID,
        resolution_notes: str,
        containment_successful: bool = True,
    ) -> None:
        """Resolve an incident."""
        for zone in self.zones.values():
            for incident in zone.incidents:
                if incident.id == incident_id:
                    incident.resolved_at = datetime.now()
                    incident.resolution_notes = resolution_notes
                    incident.containment_successful = containment_successful

                    # Check if containment can be relaxed
                    active_incidents = [i for i in zone.incidents if not i.resolved_at]
                    if not active_incidents:
                        zone.containment_level = ContainmentLevel.NONE

                    self._update_zone_status(zone)
                    logger.info(f"Incident {incident_id} resolved in zone {zone.name}")
                    return
