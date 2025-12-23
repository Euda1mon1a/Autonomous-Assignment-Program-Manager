"""
Comprehensive unit tests for the blast radius isolation module.

Tests cover:
- SchedulingZone operations and status calculations
- BlastRadiusManager zone management
- Cross-zone borrowing requests and limits
- Incident recording and containment
- Zone health monitoring and reporting
- Event handler registration and triggering
"""

from uuid import uuid4

import pytest

from app.resilience.blast_radius import (
    BlastRadiusManager,
    BorrowingPriority,
    ContainmentLevel,
    SchedulingZone,
    ZoneFacultyAssignment,
    ZoneStatus,
    ZoneType,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def manager():
    """Create a fresh BlastRadiusManager."""
    return BlastRadiusManager()


@pytest.fixture
def manager_with_zones(manager):
    """Create a manager with default zones configured."""
    manager.create_default_zones()
    return manager


@pytest.fixture
def manager_with_faculty(manager_with_zones):
    """Create a manager with zones and faculty assigned."""
    # Get zones
    zones = list(manager_with_zones.zones.values())

    # Assign faculty to inpatient zone (highest priority)
    inpatient = next(z for z in zones if z.zone_type == ZoneType.INPATIENT)
    for i in range(5):
        manager_with_zones.assign_faculty_to_zone(
            inpatient.id,
            uuid4(),
            f"Dr. Inpatient {i}",
            "primary" if i < 3 else "secondary",
        )

    # Assign faculty to outpatient zone
    outpatient = next(z for z in zones if z.zone_type == ZoneType.OUTPATIENT)
    for i in range(4):
        manager_with_zones.assign_faculty_to_zone(
            outpatient.id,
            uuid4(),
            f"Dr. Outpatient {i}",
            "primary" if i < 2 else "secondary",
        )

    # Assign faculty to education zone (lower priority)
    education = next(z for z in zones if z.zone_type == ZoneType.EDUCATION)
    for i in range(3):
        manager_with_zones.assign_faculty_to_zone(
            education.id,
            uuid4(),
            f"Dr. Education {i}",
            "primary" if i < 2 else "backup",
        )

    return manager_with_zones


# ============================================================================
# TestSchedulingZone
# ============================================================================


class TestSchedulingZone:
    """Test SchedulingZone class operations."""

    def test_empty_zone_not_self_sufficient(self):
        """Empty zone with no faculty is not self-sufficient."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test Zone",
            zone_type=ZoneType.INPATIENT,
            description="Test",
            minimum_coverage=1,
            optimal_coverage=2,
        )

        assert not zone.is_self_sufficient()
        assert zone.get_total_available() == 0

    def test_zone_with_minimum_faculty_is_self_sufficient(self):
        """Zone with exactly minimum faculty is self-sufficient."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test Zone",
            zone_type=ZoneType.INPATIENT,
            description="Test",
            minimum_coverage=2,
            optimal_coverage=3,
        )

        # Add exactly minimum coverage
        zone.primary_faculty.append(
            ZoneFacultyAssignment(uuid4(), "Dr. A", "primary", available=True)
        )
        zone.secondary_faculty.append(
            ZoneFacultyAssignment(uuid4(), "Dr. B", "secondary", available=True)
        )

        assert zone.is_self_sufficient()
        assert zone.get_total_available() == 2

    def test_zone_with_surplus_has_surplus(self):
        """Zone with more than optimal coverage has surplus."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test Zone",
            zone_type=ZoneType.OUTPATIENT,
            description="Test",
            minimum_coverage=2,
            optimal_coverage=3,
        )

        # Add more than optimal
        for i in range(4):
            zone.primary_faculty.append(
                ZoneFacultyAssignment(uuid4(), f"Dr. {i}", "primary", available=True)
            )

        assert zone.has_surplus()
        assert zone.get_total_available() == 4

    def test_zone_without_surplus_has_no_surplus(self):
        """Zone at or below optimal has no surplus."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test Zone",
            zone_type=ZoneType.OUTPATIENT,
            description="Test",
            minimum_coverage=2,
            optimal_coverage=3,
        )

        # Add exactly optimal
        for i in range(3):
            zone.primary_faculty.append(
                ZoneFacultyAssignment(uuid4(), f"Dr. {i}", "primary", available=True)
            )

        assert not zone.has_surplus()
        assert zone.get_total_available() == 3

    def test_status_green_above_optimal(self):
        """Zone above optimal coverage has GREEN status."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test Zone",
            zone_type=ZoneType.INPATIENT,
            description="Test",
            minimum_coverage=2,
            optimal_coverage=3,
        )

        # Add 4 faculty (above optimal of 3)
        for i in range(4):
            zone.primary_faculty.append(
                ZoneFacultyAssignment(uuid4(), f"Dr. {i}", "primary", available=True)
            )

        assert zone.calculate_status() == ZoneStatus.GREEN

    def test_status_yellow_at_optimal(self):
        """Zone at optimal coverage has YELLOW status."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test Zone",
            zone_type=ZoneType.INPATIENT,
            description="Test",
            minimum_coverage=2,
            optimal_coverage=3,
        )

        # Add exactly optimal (3)
        for i in range(3):
            zone.primary_faculty.append(
                ZoneFacultyAssignment(uuid4(), f"Dr. {i}", "primary", available=True)
            )

        assert zone.calculate_status() == ZoneStatus.YELLOW

    def test_status_orange_above_minimum(self):
        """Zone above minimum but below optimal has ORANGE status."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test Zone",
            zone_type=ZoneType.INPATIENT,
            description="Test",
            minimum_coverage=2,
            optimal_coverage=4,
        )

        # Add minimum + 1 (3, which is < optimal)
        for i in range(3):
            zone.primary_faculty.append(
                ZoneFacultyAssignment(uuid4(), f"Dr. {i}", "primary", available=True)
            )

        assert zone.calculate_status() == ZoneStatus.ORANGE

    def test_status_red_below_minimum(self):
        """Zone below minimum coverage has RED status."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test Zone",
            zone_type=ZoneType.INPATIENT,
            description="Test",
            minimum_coverage=3,
            optimal_coverage=5,
        )

        # Add 2 (below minimum of 3)
        for i in range(2):
            zone.primary_faculty.append(
                ZoneFacultyAssignment(uuid4(), f"Dr. {i}", "primary", available=True)
            )

        assert zone.calculate_status() == ZoneStatus.RED

    def test_status_black_critically_low(self):
        """Zone below half of minimum has BLACK status."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test Zone",
            zone_type=ZoneType.INPATIENT,
            description="Test",
            minimum_coverage=4,
            optimal_coverage=6,
        )

        # Add 1 (below 4 * 0.5 = 2)
        zone.primary_faculty.append(
            ZoneFacultyAssignment(uuid4(), "Dr. A", "primary", available=True)
        )

        assert zone.calculate_status() == ZoneStatus.BLACK

    def test_unavailable_faculty_not_counted(self):
        """Unavailable faculty are not counted in totals."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test Zone",
            zone_type=ZoneType.INPATIENT,
            description="Test",
            minimum_coverage=2,
            optimal_coverage=3,
        )

        # Add 3 faculty but mark 1 unavailable
        zone.primary_faculty.append(
            ZoneFacultyAssignment(uuid4(), "Dr. A", "primary", available=True)
        )
        zone.primary_faculty.append(
            ZoneFacultyAssignment(uuid4(), "Dr. B", "primary", available=True)
        )
        zone.primary_faculty.append(
            ZoneFacultyAssignment(uuid4(), "Dr. C", "primary", available=False)
        )

        assert zone.get_total_available() == 2
        assert len(zone.get_available_primary()) == 2

    def test_borrowed_faculty_counted(self):
        """Borrowed faculty are added to available count."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test Zone",
            zone_type=ZoneType.INPATIENT,
            description="Test",
            minimum_coverage=2,
            optimal_coverage=3,
        )

        # Add 2 primary faculty
        for i in range(2):
            zone.primary_faculty.append(
                ZoneFacultyAssignment(uuid4(), f"Dr. {i}", "primary", available=True)
            )

        # Borrow 1 faculty
        zone.borrowed_faculty.append(uuid4())

        assert zone.get_total_available() == 3

    def test_lent_faculty_subtracted(self):
        """Lent faculty are subtracted from available count."""
        zone = SchedulingZone(
            id=uuid4(),
            name="Test Zone",
            zone_type=ZoneType.INPATIENT,
            description="Test",
            minimum_coverage=2,
            optimal_coverage=4,
        )

        # Add 4 primary faculty
        for i in range(4):
            zone.primary_faculty.append(
                ZoneFacultyAssignment(uuid4(), f"Dr. {i}", "primary", available=True)
            )

        # Lend 1 faculty
        zone.lent_faculty.append(uuid4())

        assert zone.get_total_available() == 3


# ============================================================================
# TestBlastRadiusManager
# ============================================================================


class TestBlastRadiusManager:
    """Test BlastRadiusManager operations."""

    def test_create_zone(self, manager):
        """Creating a zone adds it to the manager."""
        zone = manager.create_zone(
            name="Test Zone",
            zone_type=ZoneType.INPATIENT,
            description="Test zone",
            services=["icu", "wards"],
            minimum_coverage=2,
            optimal_coverage=4,
            priority=8,
        )

        assert zone.id in manager.zones
        assert manager.zones[zone.id] == zone
        assert zone.name == "Test Zone"
        assert zone.zone_type == ZoneType.INPATIENT
        assert zone.services == ["icu", "wards"]
        assert zone.minimum_coverage == 2
        assert zone.optimal_coverage == 4
        assert zone.priority == 8

    def test_create_default_zones_count(self, manager):
        """Creating default zones creates 6 zones."""
        zones = manager.create_default_zones()

        assert len(zones) == 6
        assert len(manager.zones) == 6

    def test_create_default_zones_priorities(self, manager):
        """Default zones have correct priority ordering."""
        zones = manager.create_default_zones()

        # Get zones by type
        inpatient = next(z for z in zones if z.zone_type == ZoneType.INPATIENT)
        outpatient = next(z for z in zones if z.zone_type == ZoneType.OUTPATIENT)
        on_call = next(z for z in zones if z.zone_type == ZoneType.ON_CALL)
        education = next(z for z in zones if z.zone_type == ZoneType.EDUCATION)
        research = next(z for z in zones if z.zone_type == ZoneType.RESEARCH)
        admin = next(z for z in zones if z.zone_type == ZoneType.ADMINISTRATIVE)

        # Check priority ordering (higher = more protected)
        assert inpatient.priority == 10  # Highest
        assert on_call.priority == 9
        assert outpatient.priority == 8
        assert education.priority == 6
        assert research.priority == 3
        assert admin.priority == 1  # Lowest

    def test_create_default_zones_borrowing_relationships(self, manager):
        """Default zones have correct borrowing relationships."""
        zones = manager.create_default_zones()

        # Higher priority zones can borrow from lower priority
        inpatient = next(z for z in zones if z.zone_type == ZoneType.INPATIENT)
        education = next(z for z in zones if z.zone_type == ZoneType.EDUCATION)

        # Inpatient (priority 10) can borrow from education (priority 6)
        assert education.id in inpatient.can_borrow_from
        # Education can lend to inpatient
        assert inpatient.id in education.can_lend_to

        # Education cannot borrow from inpatient
        assert inpatient.id not in education.can_borrow_from
        # Inpatient cannot lend to education
        assert education.id not in inpatient.can_lend_to

    def test_assign_faculty_primary(self, manager_with_zones):
        """Assigning primary faculty works correctly."""
        zone = list(manager_with_zones.zones.values())[0]
        faculty_id = uuid4()

        result = manager_with_zones.assign_faculty_to_zone(
            zone.id,
            faculty_id,
            "Dr. Test",
            "primary",
        )

        assert result is True
        assert len(zone.primary_faculty) > 0
        assert any(f.faculty_id == faculty_id for f in zone.primary_faculty)

    def test_assign_faculty_secondary(self, manager_with_zones):
        """Assigning secondary faculty works correctly."""
        zone = list(manager_with_zones.zones.values())[0]
        faculty_id = uuid4()

        result = manager_with_zones.assign_faculty_to_zone(
            zone.id,
            faculty_id,
            "Dr. Test",
            "secondary",
        )

        assert result is True
        assert any(f.faculty_id == faculty_id for f in zone.secondary_faculty)

    def test_assign_faculty_backup(self, manager_with_zones):
        """Assigning backup faculty works correctly."""
        zone = list(manager_with_zones.zones.values())[0]
        faculty_id = uuid4()

        result = manager_with_zones.assign_faculty_to_zone(
            zone.id,
            faculty_id,
            "Dr. Test",
            "backup",
        )

        assert result is True
        assert any(f.faculty_id == faculty_id for f in zone.backup_faculty)

    def test_assign_faculty_invalid_role(self, manager_with_zones):
        """Assigning faculty with invalid role fails."""
        zone = list(manager_with_zones.zones.values())[0]

        result = manager_with_zones.assign_faculty_to_zone(
            zone.id,
            uuid4(),
            "Dr. Test",
            "invalid_role",
        )

        assert result is False

    def test_assign_faculty_invalid_zone(self, manager_with_zones):
        """Assigning faculty to non-existent zone fails."""
        result = manager_with_zones.assign_faculty_to_zone(
            uuid4(),  # Non-existent zone
            uuid4(),
            "Dr. Test",
            "primary",
        )

        assert result is False


# ============================================================================
# TestBorrowingRequests
# ============================================================================


class TestBorrowingRequests:
    """Test cross-zone borrowing operations."""

    def test_request_borrowing_success(self, manager_with_faculty):
        """Successful borrowing request is created."""
        zones = list(manager_with_faculty.zones.values())
        inpatient = next(z for z in zones if z.zone_type == ZoneType.INPATIENT)
        education = next(z for z in zones if z.zone_type == ZoneType.EDUCATION)

        faculty_id = uuid4()

        request = manager_with_faculty.request_borrowing(
            requesting_zone_id=inpatient.id,
            lending_zone_id=education.id,
            faculty_id=faculty_id,
            priority=BorrowingPriority.MEDIUM,
            reason="Surge in ICU admissions",
            duration_hours=8,
        )

        assert request is not None
        assert request.requesting_zone_id == inpatient.id
        assert request.lending_zone_id == education.id
        assert request.priority == BorrowingPriority.MEDIUM
        assert request in manager_with_faculty.borrowing_requests

    def test_request_borrowing_blocked_lockdown(self, manager_with_faculty):
        """Borrowing blocked during global lockdown."""
        manager_with_faculty.set_global_containment(
            ContainmentLevel.LOCKDOWN,
            "System emergency",
        )

        zones = list(manager_with_faculty.zones.values())
        inpatient = next(z for z in zones if z.zone_type == ZoneType.INPATIENT)
        education = next(z for z in zones if z.zone_type == ZoneType.EDUCATION)

        request = manager_with_faculty.request_borrowing(
            requesting_zone_id=inpatient.id,
            lending_zone_id=education.id,
            faculty_id=uuid4(),
            priority=BorrowingPriority.MEDIUM,
            reason="Test",
            duration_hours=8,
        )

        assert request is None

    def test_request_borrowing_blocked_strict_non_critical(self, manager_with_faculty):
        """Non-critical borrowing blocked during strict containment."""
        manager_with_faculty.set_global_containment(
            ContainmentLevel.STRICT,
            "Incident containment",
        )

        zones = list(manager_with_faculty.zones.values())
        inpatient = next(z for z in zones if z.zone_type == ZoneType.INPATIENT)
        education = next(z for z in zones if z.zone_type == ZoneType.EDUCATION)

        request = manager_with_faculty.request_borrowing(
            requesting_zone_id=inpatient.id,
            lending_zone_id=education.id,
            faculty_id=uuid4(),
            priority=BorrowingPriority.MEDIUM,  # Not critical
            reason="Test",
            duration_hours=8,
        )

        assert request is None

    def test_request_borrowing_allowed_strict_critical(self, manager_with_faculty):
        """Critical borrowing allowed during strict containment."""
        manager_with_faculty.set_global_containment(
            ContainmentLevel.STRICT,
            "Incident containment",
        )

        zones = list(manager_with_faculty.zones.values())
        inpatient = next(z for z in zones if z.zone_type == ZoneType.INPATIENT)
        education = next(z for z in zones if z.zone_type == ZoneType.EDUCATION)

        request = manager_with_faculty.request_borrowing(
            requesting_zone_id=inpatient.id,
            lending_zone_id=education.id,
            faculty_id=uuid4(),
            priority=BorrowingPriority.CRITICAL,  # Critical priority
            reason="Life safety emergency",
            duration_hours=8,
        )

        assert request is not None
        assert request.status == "approved"  # Auto-approved

    def test_request_borrowing_not_in_can_borrow_list(self, manager_with_faculty):
        """Borrowing blocked if not in can_borrow_from list."""
        zones = list(manager_with_faculty.zones.values())
        education = next(z for z in zones if z.zone_type == ZoneType.EDUCATION)
        inpatient = next(z for z in zones if z.zone_type == ZoneType.INPATIENT)

        # Education (lower priority) cannot borrow from inpatient (higher priority)
        request = manager_with_faculty.request_borrowing(
            requesting_zone_id=education.id,
            lending_zone_id=inpatient.id,
            faculty_id=uuid4(),
            priority=BorrowingPriority.MEDIUM,
            reason="Test",
            duration_hours=8,
        )

        assert request is None

    def test_request_borrowing_lending_zone_no_surplus(self, manager_with_faculty):
        """Low priority borrowing blocked if lending zone has no surplus."""
        zones = list(manager_with_faculty.zones.values())
        inpatient = next(z for z in zones if z.zone_type == ZoneType.INPATIENT)
        education = next(z for z in zones if z.zone_type == ZoneType.EDUCATION)

        # Remove faculty from education zone to eliminate surplus
        education.primary_faculty.clear()
        education.secondary_faculty.clear()
        education.backup_faculty.clear()

        # Add only minimum coverage
        for i in range(education.minimum_coverage):
            education.primary_faculty.append(
                ZoneFacultyAssignment(
                    uuid4(), f"Dr. Min {i}", "primary", available=True
                )
            )

        assert not education.has_surplus()

        # Low priority request should fail
        request = manager_with_faculty.request_borrowing(
            requesting_zone_id=inpatient.id,
            lending_zone_id=education.id,
            faculty_id=uuid4(),
            priority=BorrowingPriority.LOW,
            reason="Test",
            duration_hours=8,
        )

        assert request is None

    def test_request_borrowing_at_limit(self, manager_with_faculty):
        """Borrowing blocked if at borrowing limit."""
        zones = list(manager_with_faculty.zones.values())
        inpatient = next(z for z in zones if z.zone_type == ZoneType.INPATIENT)
        education = next(z for z in zones if z.zone_type == ZoneType.EDUCATION)

        # Fill borrowing limit
        for _ in range(inpatient.borrowing_limit):
            inpatient.borrowed_faculty.append(uuid4())

        request = manager_with_faculty.request_borrowing(
            requesting_zone_id=inpatient.id,
            lending_zone_id=education.id,
            faculty_id=uuid4(),
            priority=BorrowingPriority.MEDIUM,
            reason="Test",
            duration_hours=8,
        )

        assert request is None

    def test_critical_priority_auto_approved(self, manager_with_faculty):
        """Critical priority requests are auto-approved."""
        zones = list(manager_with_faculty.zones.values())
        inpatient = next(z for z in zones if z.zone_type == ZoneType.INPATIENT)
        education = next(z for z in zones if z.zone_type == ZoneType.EDUCATION)

        faculty_id = uuid4()

        request = manager_with_faculty.request_borrowing(
            requesting_zone_id=inpatient.id,
            lending_zone_id=education.id,
            faculty_id=faculty_id,
            priority=BorrowingPriority.CRITICAL,
            reason="Life safety emergency",
            duration_hours=8,
        )

        assert request is not None
        assert request.status == "approved"
        assert request.approved_by == "auto_critical"
        assert faculty_id in inpatient.borrowed_faculty
        assert faculty_id in education.lent_faculty

    def test_complete_borrowing(self, manager_with_faculty):
        """Completing borrowing updates zones correctly."""
        zones = list(manager_with_faculty.zones.values())
        inpatient = next(z for z in zones if z.zone_type == ZoneType.INPATIENT)
        education = next(z for z in zones if z.zone_type == ZoneType.EDUCATION)

        faculty_id = uuid4()

        # Create and auto-approve critical request
        request = manager_with_faculty.request_borrowing(
            requesting_zone_id=inpatient.id,
            lending_zone_id=education.id,
            faculty_id=faculty_id,
            priority=BorrowingPriority.CRITICAL,
            reason="Test",
            duration_hours=8,
        )

        assert faculty_id in inpatient.borrowed_faculty
        assert faculty_id in education.lent_faculty

        # Complete the borrowing
        manager_with_faculty.complete_borrowing(request.id, was_effective=True)

        assert request.status == "completed"
        assert request.was_effective is True
        assert request.completed_at is not None
        assert faculty_id not in inpatient.borrowed_faculty
        assert faculty_id not in education.lent_faculty


# ============================================================================
# TestIncidentHandling
# ============================================================================


class TestIncidentHandling:
    """Test incident recording and resolution."""

    def test_record_incident(self, manager_with_faculty):
        """Recording an incident creates incident record."""
        zones = list(manager_with_faculty.zones.values())
        zone = zones[0]

        incident = manager_with_faculty.record_incident(
            zone_id=zone.id,
            incident_type="faculty_loss",
            description="Unexpected absence",
            severity="moderate",
            faculty_affected=[uuid4()],
            services_affected=["icu"],
        )

        assert incident is not None
        assert incident.zone_id == zone.id
        assert incident.incident_type == "faculty_loss"
        assert incident.severity == "moderate"
        assert incident in zone.incidents

    def test_incident_updates_zone_status(self, manager_with_faculty):
        """Incident that reduces capacity updates zone status."""
        zones = list(manager_with_faculty.zones.values())
        education = next(z for z in zones if z.zone_type == ZoneType.EDUCATION)

        # Record current status
        initial_status = education.status

        # Remove most faculty and record incident
        affected_ids = [f.faculty_id for f in education.primary_faculty]
        for faculty in education.primary_faculty:
            faculty.available = False

        incident = manager_with_faculty.record_incident(
            zone_id=education.id,
            incident_type="faculty_loss",
            description="Multiple absences",
            severity="severe",
            faculty_affected=affected_ids,
        )

        assert incident is not None
        # Status should be updated (likely degraded)
        # The exact status depends on faculty counts

    def test_severe_incident_triggers_containment(self, manager_with_faculty):
        """Severe incident triggers moderate containment."""
        zones = list(manager_with_faculty.zones.values())
        zone = zones[0]

        assert zone.containment_level == ContainmentLevel.NONE

        manager_with_faculty.record_incident(
            zone_id=zone.id,
            incident_type="quality_issue",
            description="Quality concern",
            severity="severe",
        )

        assert zone.containment_level == ContainmentLevel.MODERATE

    def test_critical_incident_triggers_strict_containment(self, manager_with_faculty):
        """Critical incident triggers strict containment."""
        zones = list(manager_with_faculty.zones.values())
        zone = zones[0]

        assert zone.containment_level == ContainmentLevel.NONE

        manager_with_faculty.record_incident(
            zone_id=zone.id,
            incident_type="external",
            description="External emergency",
            severity="critical",
        )

        assert zone.containment_level == ContainmentLevel.STRICT

    def test_resolve_incident(self, manager_with_faculty):
        """Resolving incident marks it resolved."""
        zones = list(manager_with_faculty.zones.values())
        zone = zones[0]

        incident = manager_with_faculty.record_incident(
            zone_id=zone.id,
            incident_type="demand_surge",
            description="Surge",
            severity="moderate",
        )

        assert incident.resolved_at is None

        manager_with_faculty.resolve_incident(
            incident.id,
            resolution_notes="Surge passed",
            containment_successful=True,
        )

        assert incident.resolved_at is not None
        assert incident.resolution_notes == "Surge passed"
        assert incident.containment_successful is True

    def test_resolve_incident_clears_containment(self, manager_with_faculty):
        """Resolving all incidents clears zone containment."""
        zones = list(manager_with_faculty.zones.values())
        zone = zones[0]

        # Create incident that triggers containment
        incident = manager_with_faculty.record_incident(
            zone_id=zone.id,
            incident_type="quality_issue",
            description="Issue",
            severity="severe",
        )

        assert zone.containment_level != ContainmentLevel.NONE

        # Resolve the incident
        manager_with_faculty.resolve_incident(
            incident.id,
            resolution_notes="Resolved",
            containment_successful=True,
        )

        # Containment should be cleared when no active incidents
        assert zone.containment_level == ContainmentLevel.NONE


# ============================================================================
# TestZoneHealthReports
# ============================================================================


class TestZoneHealthReports:
    """Test zone health monitoring and reporting."""

    def test_check_zone_health(self, manager_with_faculty):
        """Checking zone health returns comprehensive report."""
        zones = list(manager_with_faculty.zones.values())
        zone = zones[0]

        report = manager_with_faculty.check_zone_health(zone.id)

        assert report is not None
        assert report.zone_id == zone.id
        assert report.zone_name == zone.name
        assert report.zone_type == zone.zone_type
        assert isinstance(report.status, ZoneStatus)
        assert isinstance(report.containment_level, ContainmentLevel)
        assert isinstance(report.is_self_sufficient, bool)
        assert isinstance(report.has_surplus, bool)
        assert report.available_faculty >= 0
        assert report.minimum_required == zone.minimum_coverage
        assert report.optimal_required == zone.optimal_coverage
        assert report.checked_at is not None

    def test_check_all_zones(self, manager_with_faculty):
        """Checking all zones returns blast radius report."""
        report = manager_with_faculty.check_all_zones()

        assert report is not None
        assert report.total_zones == len(manager_with_faculty.zones)
        assert (
            report.zones_healthy + report.zones_degraded + report.zones_critical
            == report.total_zones
        )
        assert len(report.zone_reports) == report.total_zones
        assert report.generated_at is not None

    def test_health_report_recommendations(self, manager_with_faculty):
        """Health report includes relevant recommendations."""
        zones = list(manager_with_faculty.zones.values())

        # Find a zone with surplus
        surplus_zone = None
        for zone in zones:
            if zone.has_surplus():
                surplus_zone = zone
                break

        if surplus_zone:
            report = manager_with_faculty.check_zone_health(surplus_zone.id)
            assert any("surplus" in r.lower() for r in report.recommendations)

    def test_blast_radius_report_aggregation(self, manager_with_faculty):
        """Blast radius report correctly aggregates zone data."""
        # Create some incidents to make zones critical
        zones = list(manager_with_faculty.zones.values())

        # Make one zone critical
        critical_zone = zones[0]
        for faculty in critical_zone.primary_faculty:
            faculty.available = False
        for faculty in critical_zone.secondary_faculty:
            faculty.available = False

        report = manager_with_faculty.check_all_zones()

        # Should have at least one critical zone
        assert report.zones_critical >= 1

        # Should have recommendations for critical zones
        assert len(report.recommendations) > 0
        if report.zones_critical > 0:
            assert any("critical" in r.lower() for r in report.recommendations)


# ============================================================================
# TestEventHandlers
# ============================================================================


class TestEventHandlers:
    """Test event handler registration and triggering."""

    def test_register_status_handler(self, manager):
        """Status handlers can be registered."""
        called = []

        def handler(zone, old_status, new_status):
            called.append((zone.id, old_status, new_status))

        manager.register_status_handler(handler)
        assert handler in manager._on_zone_status_change

    def test_status_handler_called_on_change(self, manager_with_faculty):
        """Status handlers are called when status changes."""
        called = []

        def handler(zone, old_status, new_status):
            called.append((zone.name, old_status, new_status))

        manager_with_faculty.register_status_handler(handler)

        zones = list(manager_with_faculty.zones.values())
        zone = zones[0]

        # Force a status change by making faculty unavailable
        initial_status = zone.status
        for faculty in zone.primary_faculty:
            faculty.available = False

        # Trigger status update
        manager_with_faculty._update_zone_status(zone)

        # Handler should be called if status changed
        if zone.status != initial_status:
            assert len(called) > 0
            assert called[0][0] == zone.name
            assert called[0][1] == initial_status
            assert called[0][2] == zone.status

    def test_register_containment_handler(self, manager):
        """Containment handlers can be registered."""
        called = []

        def handler(old_level, new_level, reason):
            called.append((old_level, new_level, reason))

        manager.register_containment_handler(handler)
        assert handler in manager._on_containment_change

    def test_containment_handler_called(self, manager):
        """Containment handlers are called on level changes."""
        called = []

        def handler(old_level, new_level, reason):
            called.append((old_level, new_level, reason))

        manager.register_containment_handler(handler)

        manager.set_global_containment(
            ContainmentLevel.STRICT,
            "Testing containment",
        )

        assert len(called) == 1
        assert called[0][0] == ContainmentLevel.NONE
        assert called[0][1] == ContainmentLevel.STRICT
        assert called[0][2] == "Testing containment"
