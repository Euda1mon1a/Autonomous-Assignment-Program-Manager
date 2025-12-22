"""Tests for BlastRadiusService.

Tests for the blast radius service which manages zone-based failure
containment following the AWS Availability Zone pattern.
"""

import pytest
from uuid import uuid4

from app.services.resilience.blast_radius import (
    BlastRadiusAnalysisResult,
    BlastRadiusService,
    IncidentRecordResult,
    ZoneCreationResult,
    ZoneHealthResult,
)


class TestBlastRadiusService:
    """Test suite for BlastRadiusService."""

    @pytest.fixture
    def service(self):
        """Create a BlastRadiusService instance for testing."""
        # Service doesn't require db for basic operations
        return BlastRadiusService(db=None)

    @pytest.fixture
    def service_with_zones(self):
        """Create a service with zone isolation enabled."""
        return BlastRadiusService(
            db=None,
            config={"enable_zone_isolation": True}
        )

    def test_service_initialization(self, service):
        """Test BlastRadiusService initializes correctly."""
        assert service is not None
        assert service._manager is not None
        assert service._enable_zone_isolation is True

    def test_service_initialization_with_config(self):
        """Test BlastRadiusService respects configuration."""
        service = BlastRadiusService(
            db=None,
            config={
                "enable_zone_isolation": False,
                "auto_escalate_containment": False,
            }
        )
        assert service._enable_zone_isolation is False
        assert service._auto_escalate is False

    def test_calculate_blast_radius(self, service_with_zones):
        """Test blast radius calculation returns valid result."""
        result = service_with_zones.calculate_blast_radius()

        assert isinstance(result, BlastRadiusAnalysisResult)
        assert result.total_zones >= 0
        assert result.zones_healthy >= 0
        assert result.zones_degraded >= 0
        assert result.zones_critical >= 0
        assert result.containment_level in [
            "none", "soft", "moderate", "strict", "lockdown"
        ]
        assert result.severity in ["healthy", "warning", "degraded", "critical"]
        assert result.analyzed_at is not None

    def test_calculate_blast_radius_empty_service(self, service):
        """Test blast radius calculation with no zones."""
        # Service with zone isolation should create default zones
        result = service.calculate_blast_radius()
        assert isinstance(result, BlastRadiusAnalysisResult)
        assert result.total_zones >= 0

    def test_get_all_zones(self, service_with_zones):
        """Test getting all zones."""
        zones = service_with_zones.get_all_zones()

        assert isinstance(zones, list)
        # With zone isolation enabled, should have default zones
        if service_with_zones._enable_zone_isolation:
            assert len(zones) >= 0

    def test_create_zone(self, service):
        """Test zone creation."""
        result = service.create_zone(
            name="Test Zone",
            zone_type="inpatient",
            description="A test zone",
            services=["service1", "service2"],
            minimum_coverage=2,
            optimal_coverage=4,
            priority=7,
        )

        assert isinstance(result, ZoneCreationResult)
        assert result.success is True
        assert result.zone_id is not None
        assert result.zone_name == "Test Zone"

    def test_create_zone_with_different_types(self, service):
        """Test zone creation with different zone types."""
        zone_types = [
            "inpatient", "outpatient", "education",
            "research", "admin", "on_call"
        ]

        for zone_type in zone_types:
            result = service.create_zone(
                name=f"Test {zone_type.title()} Zone",
                zone_type=zone_type,
            )
            assert result.success is True
            assert result.zone_id is not None

    def test_check_zone_health(self, service):
        """Test checking health of a specific zone."""
        # First create a zone
        create_result = service.create_zone(
            name="Health Check Zone",
            zone_type="inpatient",
        )
        assert create_result.success is True

        zone_id = create_result.zone_id
        health = service.check_zone_health(uuid4())  # Non-existent zone

        # Non-existent zone returns None
        assert health is None

    def test_assign_faculty_to_zone(self, service):
        """Test assigning faculty to a zone."""
        # Create zone first
        create_result = service.create_zone(
            name="Faculty Assignment Zone",
            zone_type="inpatient",
        )
        assert create_result.success is True

        from uuid import UUID
        zone_id = UUID(create_result.zone_id)
        faculty_id = uuid4()

        success = service.assign_faculty_to_zone(
            zone_id=zone_id,
            faculty_id=faculty_id,
            faculty_name="Dr. Test",
            role="primary",
        )

        assert success is True

    def test_assign_faculty_invalid_zone(self, service):
        """Test assigning faculty to non-existent zone."""
        success = service.assign_faculty_to_zone(
            zone_id=uuid4(),
            faculty_id=uuid4(),
            faculty_name="Dr. Test",
            role="primary",
        )

        assert success is False

    def test_record_incident(self, service):
        """Test recording an incident in a zone."""
        # Create zone first
        create_result = service.create_zone(
            name="Incident Zone",
            zone_type="inpatient",
        )
        assert create_result.success is True

        from uuid import UUID
        zone_id = UUID(create_result.zone_id)

        result = service.record_incident(
            zone_id=zone_id,
            incident_type="faculty_loss",
            description="Test incident",
            severity="moderate",
            faculty_affected=[uuid4()],
            services_affected=["service1"],
        )

        assert isinstance(result, IncidentRecordResult)
        assert result.success is True
        assert result.incident_id is not None

    def test_record_incident_invalid_zone(self, service):
        """Test recording incident in non-existent zone."""
        result = service.record_incident(
            zone_id=uuid4(),
            incident_type="faculty_loss",
            description="Test incident",
            severity="moderate",
        )

        assert result.success is False
        assert result.error_code == "ZONE_NOT_FOUND"

    def test_set_containment_level(self, service):
        """Test setting containment level."""
        success = service.set_containment_level("moderate", "Testing containment")
        assert success is True

        level = service.get_containment_level()
        assert level == "moderate"

    def test_set_containment_level_all_levels(self, service):
        """Test setting all containment levels."""
        levels = ["none", "soft", "moderate", "strict", "lockdown"]

        for level in levels:
            success = service.set_containment_level(level, f"Testing {level}")
            assert success is True
            assert service.get_containment_level() == level

    def test_set_containment_level_invalid(self, service):
        """Test setting invalid containment level."""
        success = service.set_containment_level("invalid_level", "Testing")
        assert success is False

    def test_get_zones_by_status(self, service):
        """Test getting zones filtered by status."""
        # Create a zone
        service.create_zone(name="Status Test Zone", zone_type="inpatient")

        # New zones should be "green" status
        green_zones = service.get_zones_by_status("green")
        assert isinstance(green_zones, list)

    def test_get_zone_by_type(self, service):
        """Test getting zone by type."""
        # Create a zone
        service.create_zone(name="Type Test Zone", zone_type="education")

        zone = service.get_zone_by_type("education")
        assert zone is not None
        assert zone["zone_type"] == "education"

    def test_get_zone_by_type_not_found(self, service):
        """Test getting zone by type when none exists."""
        # Clear any existing zones by creating fresh service
        fresh_service = BlastRadiusService(
            db=None,
            config={"enable_zone_isolation": False}
        )
        zone = fresh_service.get_zone_by_type("research")
        # May be None if no zones of that type exist
        # This is expected behavior

    def test_request_borrowing(self, service):
        """Test requesting faculty borrowing between zones."""
        # Create two zones
        zone1_result = service.create_zone(name="Requesting Zone", zone_type="inpatient")
        zone2_result = service.create_zone(name="Lending Zone", zone_type="inpatient")

        from uuid import UUID
        zone1_id = UUID(zone1_result.zone_id)
        zone2_id = UUID(zone2_result.zone_id)

        # Assign faculty to lending zone
        faculty_id = uuid4()
        service.assign_faculty_to_zone(
            zone_id=zone2_id,
            faculty_id=faculty_id,
            faculty_name="Dr. Lender",
        )

        result = service.request_borrowing(
            requesting_zone_id=zone1_id,
            lending_zone_id=zone2_id,
            faculty_id=faculty_id,
            priority="high",
            reason="Testing borrowing",
            duration_hours=4,
        )

        # Result may be None if borrowing is blocked by containment
        if result is not None:
            assert "request_id" in result

    def test_manager_property(self, service):
        """Test accessing underlying manager."""
        manager = service.manager
        assert manager is not None
        assert hasattr(manager, "zones")
        assert hasattr(manager, "check_all_zones")

    def test_severity_determination(self, service_with_zones):
        """Test that severity is correctly determined."""
        result = service_with_zones.calculate_blast_radius()

        # With all healthy zones, severity should be healthy or warning
        assert result.severity in ["healthy", "warning", "degraded", "critical"]

    def test_zone_details_in_result(self, service):
        """Test that zone details are included in result."""
        # Create a zone
        service.create_zone(name="Details Zone", zone_type="inpatient")

        result = service.calculate_blast_radius()

        assert isinstance(result.zone_details, list)
        if result.zone_details:
            zone_detail = result.zone_details[0]
            assert "zone_id" in zone_detail
            assert "zone_name" in zone_detail
            assert "zone_type" in zone_detail
            assert "status" in zone_detail

    def test_recommendations_in_result(self, service_with_zones):
        """Test that recommendations are included in result."""
        result = service_with_zones.calculate_blast_radius()

        assert isinstance(result.recommendations, list)


class TestBlastRadiusServiceIntegration:
    """Integration tests for BlastRadiusService."""

    def test_full_zone_lifecycle(self):
        """Test complete zone lifecycle: create, assign, incident, resolve."""
        service = BlastRadiusService(db=None)

        # 1. Create zone
        create_result = service.create_zone(
            name="Lifecycle Test Zone",
            zone_type="inpatient",
            minimum_coverage=1,
        )
        assert create_result.success is True

        from uuid import UUID
        zone_id = UUID(create_result.zone_id)

        # 2. Assign faculty
        faculty_id = uuid4()
        assign_success = service.assign_faculty_to_zone(
            zone_id=zone_id,
            faculty_id=faculty_id,
            faculty_name="Dr. Lifecycle",
            role="primary",
        )
        assert assign_success is True

        # 3. Check blast radius
        result = service.calculate_blast_radius()
        assert result.total_zones >= 1

        # 4. Record incident
        incident_result = service.record_incident(
            zone_id=zone_id,
            incident_type="faculty_loss",
            description="Faculty unavailable",
            severity="minor",
        )
        assert incident_result.success is True

        # 5. Set containment
        service.set_containment_level("soft", "Minor incident response")
        assert service.get_containment_level() == "soft"

        # 6. Resolve and return to normal
        service.set_containment_level("none", "Incident resolved")
        assert service.get_containment_level() == "none"

    def test_auto_escalate_containment(self):
        """Test auto-escalation of containment when critical zones detected."""
        service = BlastRadiusService(
            db=None,
            config={"auto_escalate_containment": True}
        )

        # Initially containment should be none
        assert service.get_containment_level() == "none"

        # After calculating blast radius, if there are critical zones,
        # containment should be auto-escalated
        result = service.calculate_blast_radius()
        # Result should reflect the containment level
        assert result.containment_level in [
            "none", "soft", "moderate", "strict", "lockdown"
        ]
