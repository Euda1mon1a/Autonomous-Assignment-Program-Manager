"""Tests for daily manifest schemas (nested models, defaults, V2 redesign)."""

from datetime import date
from uuid import uuid4

from app.schemas.daily_manifest import (
    PersonSummary,
    AssignmentSummary,
    StaffingSummary,
    LocationManifest,
    DailyManifestResponse,
    FMITSection,
    NightCallInfo,
    RemoteAssignment,
    AbsenceInfo,
    AttendingInfo,
    HalfDayStaff,
    LocationManifestV2,
    AssignmentInfo,
    PersonClinicCoverage,
    SituationalAwareness,
    DailyManifestResponseV2,
)


class TestPersonSummary:
    def test_valid(self):
        r = PersonSummary(id=uuid4(), name="Dr. Smith")
        assert r.pgy_level is None

    def test_with_pgy(self):
        r = PersonSummary(id=uuid4(), name="Dr. Jones", pgy_level=2)
        assert r.pgy_level == 2


class TestAssignmentSummary:
    def test_valid(self):
        person = PersonSummary(id=uuid4(), name="Dr. Smith")
        r = AssignmentSummary(person=person, role="primary", activity="FM Clinic")
        assert r.role == "primary"


class TestStaffingSummary:
    def test_valid(self):
        r = StaffingSummary(total=10, residents=7, faculty=3)
        assert r.total == 10


class TestLocationManifest:
    def test_valid(self):
        staffing = StaffingSummary(total=5, residents=3, faculty=2)
        r = LocationManifest(
            clinic_location="Main Clinic",
            time_slots={"AM": [], "PM": []},
            staffing_summary=staffing,
        )
        assert r.clinic_location == "Main Clinic"

    def test_no_location(self):
        staffing = StaffingSummary(total=0, residents=0, faculty=0)
        r = LocationManifest(
            time_slots={"AM": []},
            staffing_summary=staffing,
        )
        assert r.clinic_location is None


class TestDailyManifestResponse:
    def test_valid(self):
        r = DailyManifestResponse(date=date(2026, 3, 2), locations=[])
        assert r.time_of_day is None
        assert r.generated_at is not None

    def test_with_time_of_day(self):
        r = DailyManifestResponse(date=date(2026, 3, 2), time_of_day="AM", locations=[])
        assert r.time_of_day == "AM"


# --- V2 Schemas ---


class TestFMITSection:
    def test_defaults(self):
        r = FMITSection()
        assert r.attending is None
        assert r.residents == []

    def test_populated(self):
        att = PersonSummary(id=uuid4(), name="Dr. Smith")
        res = PersonSummary(id=uuid4(), name="Dr. Jones", pgy_level=2)
        r = FMITSection(attending=att, residents=[res])
        assert r.attending.name == "Dr. Smith"
        assert len(r.residents) == 1


class TestNightCallInfo:
    def test_defaults(self):
        person = PersonSummary(id=uuid4(), name="Dr. Smith")
        r = NightCallInfo(person=person)
        assert r.call_type == "night"

    def test_custom_call_type(self):
        person = PersonSummary(id=uuid4(), name="Dr. Smith")
        r = NightCallInfo(person=person, call_type="backup")
        assert r.call_type == "backup"


class TestRemoteAssignment:
    def test_valid(self):
        person = PersonSummary(id=uuid4(), name="Dr. Jones")
        r = RemoteAssignment(person=person, location="Hilo")
        assert r.surrogate is None

    def test_with_surrogate(self):
        person = PersonSummary(id=uuid4(), name="Dr. Jones")
        surrogate = PersonSummary(id=uuid4(), name="Dr. Smith")
        r = RemoteAssignment(person=person, location="Okinawa", surrogate=surrogate)
        assert r.surrogate.name == "Dr. Smith"


class TestAbsenceInfo:
    def test_valid(self):
        person = PersonSummary(id=uuid4(), name="Dr. Smith")
        r = AbsenceInfo(person=person, absence_type="vacation")
        assert r.absence_type == "vacation"


class TestAttendingInfo:
    def test_defaults(self):
        r = AttendingInfo()
        assert r.am is None
        assert r.pm is None

    def test_populated(self):
        am = PersonSummary(id=uuid4(), name="Dr. Smith")
        pm = PersonSummary(id=uuid4(), name="Dr. Jones")
        r = AttendingInfo(am=am, pm=pm)
        assert r.am.name == "Dr. Smith"
        assert r.pm.name == "Dr. Jones"


class TestHalfDayStaff:
    def test_defaults(self):
        r = HalfDayStaff()
        assert r.assignments == []
        assert r.count == 0


class TestLocationManifestV2:
    def test_defaults(self):
        r = LocationManifestV2(location="Main Clinic")
        assert r.am.count == 0
        assert r.pm.count == 0


class TestAssignmentInfo:
    def test_valid(self):
        r = AssignmentInfo(activity="clinical", abbreviation="CL", role="primary")
        assert r.abbreviation == "CL"


class TestPersonClinicCoverage:
    def test_defaults(self):
        person = PersonSummary(id=uuid4(), name="Dr. Smith")
        r = PersonClinicCoverage(person=person)
        assert r.am is None
        assert r.pm is None

    def test_with_assignments(self):
        person = PersonSummary(id=uuid4(), name="Dr. Smith")
        am = AssignmentInfo(activity="clinical", abbreviation="CL", role="primary")
        pm = AssignmentInfo(
            activity="procedures", abbreviation="PR", role="supervising"
        )
        r = PersonClinicCoverage(person=person, am=am, pm=pm)
        assert r.am.activity == "clinical"
        assert r.pm.role == "supervising"


class TestSituationalAwareness:
    def test_defaults(self):
        r = SituationalAwareness()
        assert r.fmit_team.attending is None
        assert r.night_rotation == []
        assert r.remote_assignments == []
        assert r.absences == []


class TestDailyManifestResponseV2:
    def test_defaults(self):
        r = DailyManifestResponseV2(date=date(2026, 3, 2))
        assert r.situational_awareness.night_rotation == []
        assert r.attending.am is None
        assert r.clinic_coverage == []
        assert r.generated_at is not None
