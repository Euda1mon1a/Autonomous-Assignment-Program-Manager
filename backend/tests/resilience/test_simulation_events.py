"""Tests for simulation events (pure logic, no DB)."""

from uuid import UUID, uuid4

from app.resilience.simulation.events import (
    BorrowingEvent,
    CascadeEvent,
    EventSeverity,
    EventType,
    FacultyEvent,
    SimulationEvent,
    ZoneEvent,
    _get_default_severity,
    create_event,
)


# -- EventSeverity enum -----------------------------------------------------


class TestEventSeverity:
    def test_values(self):
        assert EventSeverity.INFO == "INFO"
        assert EventSeverity.WARNING == "WARNING"
        assert EventSeverity.CRITICAL == "CRITICAL"
        assert EventSeverity.CATASTROPHIC == "CATASTROPHIC"

    def test_member_count(self):
        assert len(EventSeverity) == 4

    def test_is_string_enum(self):
        assert isinstance(EventSeverity.INFO, str)


# -- EventType enum ----------------------------------------------------------


class TestEventType:
    def test_faculty_events(self):
        assert EventType.FACULTY_SICK_CALL == "FACULTY_SICK_CALL"
        assert EventType.FACULTY_RETURN == "FACULTY_RETURN"
        assert EventType.FACULTY_RESIGNATION == "FACULTY_RESIGNATION"
        assert EventType.FACULTY_PCS == "FACULTY_PCS"

    def test_zone_events(self):
        assert EventType.ZONE_DEGRADED == "ZONE_DEGRADED"
        assert EventType.ZONE_FAILED == "ZONE_FAILED"
        assert EventType.ZONE_RECOVERED == "ZONE_RECOVERED"

    def test_cascade_events(self):
        assert EventType.CASCADE_STARTED == "CASCADE_STARTED"
        assert EventType.CASCADE_CONTAINED == "CASCADE_CONTAINED"
        assert EventType.CASCADE_SPREAD == "CASCADE_SPREAD"

    def test_borrowing_events(self):
        assert EventType.BORROWING_REQUESTED == "BORROWING_REQUESTED"
        assert EventType.BORROWING_APPROVED == "BORROWING_APPROVED"
        assert EventType.BORROWING_DENIED == "BORROWING_DENIED"
        assert EventType.BORROWING_COMPLETED == "BORROWING_COMPLETED"

    def test_simulation_control_events(self):
        assert EventType.SIMULATION_START == "SIMULATION_START"
        assert EventType.SIMULATION_END == "SIMULATION_END"
        assert EventType.CHECKPOINT == "CHECKPOINT"

    def test_member_count(self):
        assert len(EventType) == 17

    def test_is_string_enum(self):
        assert isinstance(EventType.FACULTY_SICK_CALL, str)


# -- SimulationEvent dataclass -----------------------------------------------


class TestSimulationEvent:
    def test_default_creation(self):
        event = SimulationEvent()
        assert isinstance(event.id, UUID)
        assert event.timestamp == 0.0
        assert event.event_type == EventType.SIMULATION_START
        assert event.severity == EventSeverity.INFO
        assert event.description == ""
        assert event.metadata == {}

    def test_custom_creation(self):
        uid = uuid4()
        event = SimulationEvent(
            id=uid,
            timestamp=10.0,
            event_type=EventType.CHECKPOINT,
            severity=EventSeverity.WARNING,
            description="Checkpoint reached",
            metadata={"step": 100},
        )
        assert event.id == uid
        assert event.timestamp == 10.0
        assert event.description == "Checkpoint reached"
        assert event.metadata["step"] == 100

    def test_unique_ids(self):
        e1 = SimulationEvent()
        e2 = SimulationEvent()
        assert e1.id != e2.id


# -- FacultyEvent dataclass --------------------------------------------------


class TestFacultyEvent:
    def test_default_creation(self):
        event = FacultyEvent()
        assert isinstance(event.faculty_id, UUID)
        assert event.faculty_name == ""
        assert event.zone_id is None
        assert event.duration_days is None
        assert event.is_permanent is False

    def test_custom_creation(self):
        fid = uuid4()
        zid = uuid4()
        event = FacultyEvent(
            timestamp=5.0,
            event_type=EventType.FACULTY_SICK_CALL,
            faculty_id=fid,
            faculty_name="Dr. Smith",
            zone_id=zid,
            duration_days=3.0,
        )
        assert event.faculty_id == fid
        assert event.faculty_name == "Dr. Smith"
        assert event.zone_id == zid
        assert event.duration_days == 3.0

    def test_is_simulation_event(self):
        assert issubclass(FacultyEvent, SimulationEvent)

    def test_permanent_event(self):
        event = FacultyEvent(
            event_type=EventType.FACULTY_RESIGNATION,
            is_permanent=True,
        )
        assert event.is_permanent is True


# -- ZoneEvent dataclass -----------------------------------------------------


class TestZoneEvent:
    def test_default_creation(self):
        event = ZoneEvent()
        assert isinstance(event.zone_id, UUID)
        assert event.zone_name == ""
        assert event.previous_status == ""
        assert event.new_status == ""
        assert event.faculty_affected == []
        assert event.services_affected == []

    def test_custom_creation(self):
        event = ZoneEvent(
            event_type=EventType.ZONE_FAILED,
            zone_name="Zone A",
            previous_status="active",
            new_status="failed",
            services_affected=["cardiology", "surgery"],
        )
        assert event.zone_name == "Zone A"
        assert event.new_status == "failed"
        assert len(event.services_affected) == 2

    def test_is_simulation_event(self):
        assert issubclass(ZoneEvent, SimulationEvent)


# -- CascadeEvent dataclass --------------------------------------------------


class TestCascadeEvent:
    def test_default_creation(self):
        event = CascadeEvent()
        assert isinstance(event.trigger_zone_id, UUID)
        assert isinstance(event.trigger_event_id, UUID)
        assert event.affected_zones == []
        assert event.depth == 1
        assert event.was_contained is False
        assert event.containment_time is None

    def test_custom_creation(self):
        zones = [uuid4(), uuid4()]
        event = CascadeEvent(
            event_type=EventType.CASCADE_SPREAD,
            affected_zones=zones,
            depth=3,
            was_contained=True,
            containment_time=15.0,
        )
        assert len(event.affected_zones) == 2
        assert event.depth == 3
        assert event.was_contained is True
        assert event.containment_time == 15.0

    def test_is_simulation_event(self):
        assert issubclass(CascadeEvent, SimulationEvent)


# -- BorrowingEvent dataclass ------------------------------------------------


class TestBorrowingEvent:
    def test_default_creation(self):
        event = BorrowingEvent()
        assert isinstance(event.requesting_zone_id, UUID)
        assert isinstance(event.lending_zone_id, UUID)
        assert isinstance(event.faculty_id, UUID)
        assert event.was_approved is False
        assert event.denial_reason is None

    def test_approved_event(self):
        event = BorrowingEvent(
            event_type=EventType.BORROWING_APPROVED,
            was_approved=True,
        )
        assert event.was_approved is True

    def test_denied_event(self):
        event = BorrowingEvent(
            event_type=EventType.BORROWING_DENIED,
            was_approved=False,
            denial_reason="Insufficient staff in lending zone",
        )
        assert event.was_approved is False
        assert event.denial_reason == "Insufficient staff in lending zone"

    def test_is_simulation_event(self):
        assert issubclass(BorrowingEvent, SimulationEvent)


# -- _get_default_severity ---------------------------------------------------


class TestGetDefaultSeverity:
    def test_faculty_sick_call_is_warning(self):
        assert (
            _get_default_severity(EventType.FACULTY_SICK_CALL) == EventSeverity.WARNING
        )

    def test_faculty_return_is_info(self):
        assert _get_default_severity(EventType.FACULTY_RETURN) == EventSeverity.INFO

    def test_faculty_resignation_is_critical(self):
        assert (
            _get_default_severity(EventType.FACULTY_RESIGNATION)
            == EventSeverity.CRITICAL
        )

    def test_cascade_spread_is_catastrophic(self):
        assert (
            _get_default_severity(EventType.CASCADE_SPREAD)
            == EventSeverity.CATASTROPHIC
        )

    def test_zone_failed_is_critical(self):
        assert _get_default_severity(EventType.ZONE_FAILED) == EventSeverity.CRITICAL

    def test_zone_recovered_is_info(self):
        assert _get_default_severity(EventType.ZONE_RECOVERED) == EventSeverity.INFO

    def test_borrowing_denied_is_warning(self):
        assert (
            _get_default_severity(EventType.BORROWING_DENIED) == EventSeverity.WARNING
        )

    def test_simulation_start_is_info(self):
        assert _get_default_severity(EventType.SIMULATION_START) == EventSeverity.INFO


# -- create_event factory ----------------------------------------------------


class TestCreateEvent:
    def test_faculty_event_type(self):
        event = create_event(EventType.FACULTY_SICK_CALL, timestamp=5.0)
        assert isinstance(event, FacultyEvent)
        assert event.event_type == EventType.FACULTY_SICK_CALL

    def test_zone_event_type(self):
        event = create_event(EventType.ZONE_DEGRADED, timestamp=3.0)
        assert isinstance(event, ZoneEvent)
        assert event.event_type == EventType.ZONE_DEGRADED

    def test_cascade_event_type(self):
        event = create_event(EventType.CASCADE_STARTED, timestamp=7.0)
        assert isinstance(event, CascadeEvent)

    def test_borrowing_event_type(self):
        event = create_event(EventType.BORROWING_REQUESTED, timestamp=2.0)
        assert isinstance(event, BorrowingEvent)

    def test_simulation_control_event(self):
        event = create_event(EventType.SIMULATION_START, timestamp=0.0)
        assert isinstance(event, SimulationEvent)
        # SIMULATION_START is not in the class map, so it's base SimulationEvent
        assert event.event_type == EventType.SIMULATION_START

    def test_default_severity_applied(self):
        event = create_event(EventType.FACULTY_RESIGNATION)
        assert event.severity == EventSeverity.CRITICAL

    def test_custom_severity_overrides(self):
        event = create_event(
            EventType.FACULTY_SICK_CALL, severity=EventSeverity.CRITICAL
        )
        assert event.severity == EventSeverity.CRITICAL

    def test_kwargs_passed_through(self):
        event = create_event(
            EventType.FACULTY_SICK_CALL,
            faculty_name="Dr. Jones",
            duration_days=5.0,
        )
        assert event.faculty_name == "Dr. Jones"
        assert event.duration_days == 5.0

    def test_all_faculty_events_produce_faculty_event(self):
        for et in [
            EventType.FACULTY_SICK_CALL,
            EventType.FACULTY_RETURN,
            EventType.FACULTY_RESIGNATION,
            EventType.FACULTY_PCS,
        ]:
            event = create_event(et)
            assert isinstance(event, FacultyEvent)

    def test_all_zone_events_produce_zone_event(self):
        for et in [
            EventType.ZONE_DEGRADED,
            EventType.ZONE_FAILED,
            EventType.ZONE_RECOVERED,
        ]:
            event = create_event(et)
            assert isinstance(event, ZoneEvent)

    def test_all_cascade_events_produce_cascade_event(self):
        for et in [
            EventType.CASCADE_STARTED,
            EventType.CASCADE_CONTAINED,
            EventType.CASCADE_SPREAD,
        ]:
            event = create_event(et)
            assert isinstance(event, CascadeEvent)

    def test_all_borrowing_events_produce_borrowing_event(self):
        for et in [
            EventType.BORROWING_REQUESTED,
            EventType.BORROWING_APPROVED,
            EventType.BORROWING_DENIED,
            EventType.BORROWING_COMPLETED,
        ]:
            event = create_event(et)
            assert isinstance(event, BorrowingEvent)
