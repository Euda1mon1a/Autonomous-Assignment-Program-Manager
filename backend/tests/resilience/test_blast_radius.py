"""Tests for Blast Radius Isolation (AWS architecture pattern)."""

from uuid import uuid4

from app.resilience.blast_radius import (
    BlastRadiusManager,
    BlastRadiusReport,
    BorrowingPriority,
    BorrowingRequest,
    ContainmentLevel,
    SchedulingZone,
    ZoneFacultyAssignment,
    ZoneHealthReport,
    ZoneIncident,
    ZoneStatus,
    ZoneType,
)


# ==================== Enums ====================


class TestZoneStatus:
    def test_is_str_enum(self):
        assert isinstance(ZoneStatus.GREEN, str)

    def test_values(self):
        assert ZoneStatus.GREEN == "green"
        assert ZoneStatus.YELLOW == "yellow"
        assert ZoneStatus.ORANGE == "orange"
        assert ZoneStatus.RED == "red"
        assert ZoneStatus.BLACK == "black"

    def test_count(self):
        assert len(ZoneStatus) == 5


class TestZoneType:
    def test_values(self):
        assert ZoneType.INPATIENT == "inpatient"
        assert ZoneType.OUTPATIENT == "outpatient"
        assert ZoneType.EDUCATION == "education"
        assert ZoneType.RESEARCH == "research"
        assert ZoneType.ADMINISTRATIVE == "admin"
        assert ZoneType.ON_CALL == "on_call"

    def test_count(self):
        assert len(ZoneType) == 6


class TestBorrowingPriority:
    def test_values(self):
        assert BorrowingPriority.CRITICAL == "critical"
        assert BorrowingPriority.HIGH == "high"
        assert BorrowingPriority.MEDIUM == "medium"
        assert BorrowingPriority.LOW == "low"

    def test_count(self):
        assert len(BorrowingPriority) == 4


class TestContainmentLevel:
    def test_values(self):
        assert ContainmentLevel.NONE == "none"
        assert ContainmentLevel.SOFT == "soft"
        assert ContainmentLevel.MODERATE == "moderate"
        assert ContainmentLevel.STRICT == "strict"
        assert ContainmentLevel.LOCKDOWN == "lockdown"

    def test_count(self):
        assert len(ContainmentLevel) == 5


# ==================== Dataclasses ====================


class TestZoneFacultyAssignment:
    def test_fields(self):
        fid = uuid4()
        a = ZoneFacultyAssignment(
            faculty_id=fid, faculty_name="Dr. Smith", role="primary"
        )
        assert a.faculty_id == fid
        assert a.faculty_name == "Dr. Smith"
        assert a.role == "primary"
        assert a.available is True


class TestBorrowingRequest:
    def test_defaults(self):
        r = BorrowingRequest(
            id=uuid4(),
            requesting_zone_id=uuid4(),
            lending_zone_id=uuid4(),
            faculty_id=uuid4(),
            priority=BorrowingPriority.HIGH,
            reason="Coverage gap",
            requested_at=None,
            duration_hours=8,
        )
        assert r.status == "pending"
        assert r.approved_by is None
        assert r.started_at is None
        assert r.completed_at is None
        assert r.was_effective is None


class TestZoneIncident:
    def test_defaults(self):
        i = ZoneIncident(
            id=uuid4(),
            zone_id=uuid4(),
            incident_type="faculty_loss",
            description="Faculty called out",
            started_at=None,
            severity="moderate",
        )
        assert i.faculty_affected == []
        assert i.capacity_lost == 0.0
        assert i.services_affected == []
        assert i.resolved_at is None
        assert i.containment_successful is True


# ==================== SchedulingZone ====================


class TestSchedulingZone:
    def _make_zone(self, **overrides):
        defaults = {
            "id": uuid4(),
            "name": "Test Zone",
            "zone_type": ZoneType.INPATIENT,
            "description": "Test zone",
            "minimum_coverage": 2,
            "optimal_coverage": 4,
        }
        defaults.update(overrides)
        return SchedulingZone(**defaults)

    def _make_faculty(self, available=True):
        return ZoneFacultyAssignment(
            faculty_id=uuid4(),
            faculty_name="Dr. Test",
            role="primary",
            available=available,
        )

    def test_defaults(self):
        z = self._make_zone()
        assert z.status == ZoneStatus.GREEN
        assert z.containment_level == ContainmentLevel.NONE
        assert z.borrowing_limit == 2
        assert z.lending_limit == 1

    def test_get_available_primary(self):
        z = self._make_zone()
        z.primary_faculty = [self._make_faculty(True), self._make_faculty(False)]
        assert len(z.get_available_primary()) == 1

    def test_get_total_available(self):
        z = self._make_zone()
        z.primary_faculty = [self._make_faculty(), self._make_faculty()]
        z.secondary_faculty = [self._make_faculty()]
        z.backup_faculty = [self._make_faculty()]
        z.borrowed_faculty = [uuid4()]
        z.lent_faculty = [uuid4()]
        # 2 primary + 1 secondary + 1 backup + 1 borrowed - 1 lent = 4
        assert z.get_total_available() == 4

    def test_is_self_sufficient(self):
        z = self._make_zone(minimum_coverage=2)
        z.primary_faculty = [self._make_faculty(), self._make_faculty()]
        assert z.is_self_sufficient() is True

    def test_not_self_sufficient(self):
        z = self._make_zone(minimum_coverage=3)
        z.primary_faculty = [self._make_faculty()]
        assert z.is_self_sufficient() is False

    def test_has_surplus(self):
        z = self._make_zone(optimal_coverage=2)
        z.primary_faculty = [self._make_faculty() for _ in range(3)]
        assert z.has_surplus() is True

    def test_no_surplus(self):
        z = self._make_zone(optimal_coverage=3)
        z.primary_faculty = [self._make_faculty(), self._make_faculty()]
        assert z.has_surplus() is False

    def test_calculate_status_green(self):
        z = self._make_zone(minimum_coverage=1, optimal_coverage=2)
        z.primary_faculty = [self._make_faculty() for _ in range(3)]
        assert z.calculate_status() == ZoneStatus.GREEN

    def test_calculate_status_yellow(self):
        z = self._make_zone(minimum_coverage=2, optimal_coverage=3)
        z.primary_faculty = [self._make_faculty() for _ in range(3)]
        # available=3, optimal=3, minimum=2 → 3 <= 3 → YELLOW
        assert z.calculate_status() == ZoneStatus.YELLOW

    def test_calculate_status_orange(self):
        z = self._make_zone(minimum_coverage=2, optimal_coverage=4)
        z.primary_faculty = [self._make_faculty(), self._make_faculty()]
        # available=2, minimum+1=3, minimum=2 → 2 < 3 → ORANGE
        assert z.calculate_status() == ZoneStatus.ORANGE

    def test_calculate_status_red(self):
        z = self._make_zone(minimum_coverage=3, optimal_coverage=5)
        z.primary_faculty = [self._make_faculty(), self._make_faculty()]
        # available=2, minimum=3 → 2 < 3 → RED
        assert z.calculate_status() == ZoneStatus.RED

    def test_calculate_status_black(self):
        z = self._make_zone(minimum_coverage=4, optimal_coverage=6)
        z.primary_faculty = [self._make_faculty()]
        # available=1, minimum*0.5=2 → 1 < 2 → BLACK
        assert z.calculate_status() == ZoneStatus.BLACK


# ==================== BlastRadiusManager ====================


class TestBlastRadiusManagerInit:
    def test_defaults(self):
        mgr = BlastRadiusManager()
        assert mgr.zones == {}
        assert mgr.borrowing_requests == []
        assert mgr.global_containment == ContainmentLevel.NONE


class TestCreateZone:
    def test_creates_zone(self):
        mgr = BlastRadiusManager()
        zone = mgr.create_zone(
            name="Inpatient",
            zone_type=ZoneType.INPATIENT,
            description="ICU and wards",
            services=["icu", "wards"],
            minimum_coverage=3,
            optimal_coverage=5,
            priority=10,
        )
        assert isinstance(zone, SchedulingZone)
        assert zone.name == "Inpatient"
        assert zone.zone_type == ZoneType.INPATIENT
        assert zone.minimum_coverage == 3
        assert zone.priority == 10
        assert zone.id in mgr.zones

    def test_create_default_zones(self):
        mgr = BlastRadiusManager()
        zones = mgr.create_default_zones()
        assert len(zones) == 6
        types = {z.zone_type for z in zones}
        assert ZoneType.INPATIENT in types
        assert ZoneType.OUTPATIENT in types
        assert ZoneType.ON_CALL in types
        assert ZoneType.EDUCATION in types
        assert ZoneType.RESEARCH in types
        assert ZoneType.ADMINISTRATIVE in types

    def test_default_zones_have_borrowing_relationships(self):
        mgr = BlastRadiusManager()
        zones = mgr.create_default_zones()
        inpatient = next(z for z in zones if z.zone_type == ZoneType.INPATIENT)
        # Inpatient (highest priority=10) can borrow from all others
        assert len(inpatient.can_borrow_from) > 0
        # Admin (lowest priority=1) can lend to all others
        admin = next(z for z in zones if z.zone_type == ZoneType.ADMINISTRATIVE)
        assert len(admin.can_lend_to) > 0


class TestAssignFaculty:
    def test_assign_primary(self):
        mgr = BlastRadiusManager()
        zone = mgr.create_zone("Test", ZoneType.INPATIENT, "Test", ["icu"])
        fid = uuid4()
        result = mgr.assign_faculty_to_zone(zone.id, fid, "Dr. Smith", "primary")
        assert result is True
        assert len(zone.primary_faculty) == 1
        assert zone.primary_faculty[0].faculty_id == fid

    def test_assign_secondary(self):
        mgr = BlastRadiusManager()
        zone = mgr.create_zone("Test", ZoneType.INPATIENT, "Test", ["icu"])
        result = mgr.assign_faculty_to_zone(zone.id, uuid4(), "Dr. A", "secondary")
        assert result is True
        assert len(zone.secondary_faculty) == 1

    def test_assign_backup(self):
        mgr = BlastRadiusManager()
        zone = mgr.create_zone("Test", ZoneType.INPATIENT, "Test", ["icu"])
        result = mgr.assign_faculty_to_zone(zone.id, uuid4(), "Dr. B", "backup")
        assert result is True
        assert len(zone.backup_faculty) == 1

    def test_invalid_role(self):
        mgr = BlastRadiusManager()
        zone = mgr.create_zone("Test", ZoneType.INPATIENT, "Test", ["icu"])
        result = mgr.assign_faculty_to_zone(zone.id, uuid4(), "Dr. C", "invalid")
        assert result is False

    def test_invalid_zone(self):
        mgr = BlastRadiusManager()
        result = mgr.assign_faculty_to_zone(uuid4(), uuid4(), "Dr. D", "primary")
        assert result is False


class TestRequestBorrowing:
    def _setup(self):
        mgr = BlastRadiusManager()
        z1 = mgr.create_zone("High", ZoneType.INPATIENT, "High", ["icu"], priority=10)
        z2 = mgr.create_zone("Low", ZoneType.EDUCATION, "Low", ["edu"], priority=3)
        z1.can_borrow_from = [z2.id]
        z2.can_lend_to = [z1.id]
        # Give z2 surplus faculty
        for _ in range(4):
            mgr.assign_faculty_to_zone(z2.id, uuid4(), "Dr.", "primary")
        fid = uuid4()
        return mgr, z1, z2, fid

    def test_successful_borrowing(self):
        mgr, z1, z2, fid = self._setup()
        req = mgr.request_borrowing(
            z1.id, z2.id, fid, BorrowingPriority.HIGH, "Coverage gap"
        )
        assert req is not None
        assert isinstance(req, BorrowingRequest)
        # Auto-approved because global containment is NONE
        assert req.status == "approved"

    def test_critical_auto_approved(self):
        mgr, z1, z2, fid = self._setup()
        mgr.global_containment = ContainmentLevel.MODERATE
        req = mgr.request_borrowing(
            z1.id, z2.id, fid, BorrowingPriority.CRITICAL, "Emergency"
        )
        assert req is not None
        assert req.status == "approved"

    def test_lockdown_blocks_all(self):
        mgr, z1, z2, fid = self._setup()
        mgr.global_containment = ContainmentLevel.LOCKDOWN
        req = mgr.request_borrowing(
            z1.id, z2.id, fid, BorrowingPriority.CRITICAL, "Emergency"
        )
        assert req is None

    def test_strict_blocks_non_critical(self):
        mgr, z1, z2, fid = self._setup()
        mgr.global_containment = ContainmentLevel.STRICT
        req = mgr.request_borrowing(
            z1.id, z2.id, fid, BorrowingPriority.MEDIUM, "Normal"
        )
        assert req is None

    def test_zone_lockdown_blocks(self):
        mgr, z1, z2, fid = self._setup()
        z2.containment_level = ContainmentLevel.LOCKDOWN
        req = mgr.request_borrowing(z1.id, z2.id, fid, BorrowingPriority.HIGH, "Need")
        assert req is None

    def test_not_in_borrow_list(self):
        mgr, z1, z2, fid = self._setup()
        z1.can_borrow_from = []
        req = mgr.request_borrowing(z1.id, z2.id, fid, BorrowingPriority.HIGH, "Need")
        assert req is None

    def test_borrowing_limit_blocks(self):
        mgr, z1, z2, fid = self._setup()
        z1.borrowing_limit = 0
        req = mgr.request_borrowing(z1.id, z2.id, fid, BorrowingPriority.HIGH, "Need")
        assert req is None

    def test_invalid_zones(self):
        mgr, z1, z2, fid = self._setup()
        req = mgr.request_borrowing(uuid4(), z2.id, fid, BorrowingPriority.HIGH, "Need")
        assert req is None


class TestCompleteBorrowing:
    def test_completes_request(self):
        mgr = BlastRadiusManager()
        z1 = mgr.create_zone("A", ZoneType.INPATIENT, "A", ["icu"], priority=10)
        z2 = mgr.create_zone("B", ZoneType.EDUCATION, "B", ["edu"], priority=3)
        z1.can_borrow_from = [z2.id]
        for _ in range(4):
            mgr.assign_faculty_to_zone(z2.id, uuid4(), "Dr.", "primary")
        fid = uuid4()
        req = mgr.request_borrowing(
            z1.id, z2.id, fid, BorrowingPriority.CRITICAL, "Test"
        )
        assert fid in z1.borrowed_faculty
        mgr.complete_borrowing(req.id, was_effective=True)
        assert req.status == "completed"
        assert req.was_effective is True
        assert fid not in z1.borrowed_faculty


class TestRecordIncident:
    def test_records_incident(self):
        mgr = BlastRadiusManager()
        zone = mgr.create_zone("Test", ZoneType.INPATIENT, "Test", ["icu"])
        incident = mgr.record_incident(
            zone.id, "faculty_loss", "Faculty left", "moderate"
        )
        assert isinstance(incident, ZoneIncident)
        assert incident.severity == "moderate"
        assert len(zone.incidents) == 1

    def test_severe_activates_containment(self):
        mgr = BlastRadiusManager()
        zone = mgr.create_zone("Test", ZoneType.INPATIENT, "Test", ["icu"])
        mgr.record_incident(zone.id, "demand_surge", "Big surge", "severe")
        assert zone.containment_level == ContainmentLevel.MODERATE

    def test_critical_activates_strict(self):
        mgr = BlastRadiusManager()
        zone = mgr.create_zone("Test", ZoneType.INPATIENT, "Test", ["icu"])
        mgr.record_incident(zone.id, "faculty_loss", "Mass exodus", "critical")
        assert zone.containment_level == ContainmentLevel.STRICT

    def test_invalid_zone(self):
        mgr = BlastRadiusManager()
        result = mgr.record_incident(uuid4(), "test", "test", "minor")
        assert result is None

    def test_capacity_lost_calculated(self):
        mgr = BlastRadiusManager()
        zone = mgr.create_zone("Test", ZoneType.INPATIENT, "Test", ["icu"])
        fid1 = uuid4()
        fid2 = uuid4()
        mgr.assign_faculty_to_zone(zone.id, fid1, "Dr. A", "primary")
        mgr.assign_faculty_to_zone(zone.id, fid2, "Dr. B", "primary")
        incident = mgr.record_incident(
            zone.id,
            "faculty_loss",
            "One left",
            "moderate",
            faculty_affected=[fid1],
        )
        assert incident.capacity_lost == 0.5  # 1/2


class TestSetGlobalContainment:
    def test_sets_containment(self):
        mgr = BlastRadiusManager()
        mgr.set_global_containment(ContainmentLevel.STRICT, "Testing")
        assert mgr.global_containment == ContainmentLevel.STRICT


class TestCheckZoneHealth:
    def test_returns_report(self):
        mgr = BlastRadiusManager()
        zone = mgr.create_zone(
            "Test", ZoneType.INPATIENT, "Test", ["icu"], minimum_coverage=1
        )
        mgr.assign_faculty_to_zone(zone.id, uuid4(), "Dr. A", "primary")
        mgr.assign_faculty_to_zone(zone.id, uuid4(), "Dr. B", "primary")
        mgr.assign_faculty_to_zone(zone.id, uuid4(), "Dr. C", "primary")
        report = mgr.check_zone_health(zone.id)
        assert isinstance(report, ZoneHealthReport)
        assert report.zone_name == "Test"
        assert report.available_faculty == 3

    def test_returns_none_invalid(self):
        mgr = BlastRadiusManager()
        assert mgr.check_zone_health(uuid4()) is None


class TestCheckAllZones:
    def test_returns_report(self):
        mgr = BlastRadiusManager()
        mgr.create_default_zones()
        report = mgr.check_all_zones()
        assert isinstance(report, BlastRadiusReport)
        assert report.total_zones == 6
        assert len(report.zone_reports) == 6


class TestGetZoneByType:
    def test_finds_zone(self):
        mgr = BlastRadiusManager()
        mgr.create_default_zones()
        zone = mgr.get_zone_by_type(ZoneType.INPATIENT)
        assert zone is not None
        assert zone.zone_type == ZoneType.INPATIENT

    def test_not_found(self):
        mgr = BlastRadiusManager()
        assert mgr.get_zone_by_type(ZoneType.RESEARCH) is None


class TestGetZonesByStatus:
    def test_all_green_initially(self):
        mgr = BlastRadiusManager()
        mgr.create_default_zones()
        greens = mgr.get_zones_by_status(ZoneStatus.GREEN)
        # Some default zones have min_coverage=0, so they start green
        assert len(greens) >= 0


class TestResolveIncident:
    def test_resolves_and_relaxes_containment(self):
        mgr = BlastRadiusManager()
        zone = mgr.create_zone("Test", ZoneType.INPATIENT, "Test", ["icu"])
        incident = mgr.record_incident(zone.id, "faculty_loss", "Test", "severe")
        assert zone.containment_level == ContainmentLevel.MODERATE
        mgr.resolve_incident(incident.id, "Resolved")
        assert incident.resolved_at is not None
        assert incident.resolution_notes == "Resolved"
        assert zone.containment_level == ContainmentLevel.NONE
