"""Tests for block quality report schemas (nested models, composites, defaults)."""

from datetime import date

from app.schemas.block_quality_report import (
    BlockDates,
    BlockAssignmentEntry,
    AbsenceEntry,
    CallCoverageSummary,
    FacultyPreloadedEntry,
    RotationSummary,
    ResidentDistribution,
    PersonAssignmentSummary,
    NFOneInSevenEntry,
    PostCallEntry,
    CallBeforeLeaveEntry,
    AccountabilityEntry,
    ExecutiveSummary,
    SectionA,
    SectionB,
    SectionC,
    SectionD,
    SectionE,
    BlockQualityReport,
    BlockSummaryEntry,
    CrossBlockSummary,
)


class TestBlockDates:
    def test_valid(self):
        r = BlockDates(
            block_number=10,
            academic_year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            days=31,
            slots=62,
        )
        assert r.block_number == 10
        assert r.slots == 62


class TestBlockAssignmentEntry:
    def test_valid(self):
        r = BlockAssignmentEntry(name="Dr. Smith", pgy_level=2, rotation="FM Clinic")
        assert r.pgy_level == 2


class TestAbsenceEntry:
    def test_valid(self):
        r = AbsenceEntry(
            name="Dr. Jones",
            absence_type="vacation",
            start_date=date(2026, 1, 5),
            end_date=date(2026, 1, 10),
        )
        assert r.absence_type == "vacation"


class TestCallCoverageSummary:
    def test_valid(self):
        r = CallCoverageSummary(sun_thu_count=20, fri_sat_count=8, total_nights=28)
        assert r.total_nights == 28


class TestFacultyPreloadedEntry:
    def test_defaults(self):
        r = FacultyPreloadedEntry(name="Dr. Smith", slots=10)
        assert r.role is None

    def test_with_role(self):
        r = FacultyPreloadedEntry(name="Dr. Smith", slots=10, role="attending")
        assert r.role == "attending"


class TestRotationSummary:
    def test_valid(self):
        r = RotationSummary(rotation="FM Clinic", rotation_type="outpatient", count=8)
        assert r.count == 8


class TestResidentDistribution:
    def test_valid(self):
        r = ResidentDistribution(
            name="Dr. Jones", pgy_level=1, count=40, utilization_pct=85.0
        )
        assert r.utilization_pct == 85.0


class TestPersonAssignmentSummary:
    def test_resident(self):
        r = PersonAssignmentSummary(
            name="Dr. Jones",
            person_type="resident",
            pgy_level=2,
            preloaded=5,
            solved=35,
            total=40,
            utilization_pct=80.0,
        )
        assert r.person_type == "resident"

    def test_faculty(self):
        r = PersonAssignmentSummary(
            name="Dr. Smith",
            person_type="faculty",
            preloaded=10,
            solved=12,
            total=22,
            utilization_pct=90.0,
        )
        assert r.pgy_level is None


class TestNFOneInSevenEntry:
    def test_valid(self):
        r = NFOneInSevenEntry(
            name="Dr. Jones",
            rotation="Night Float",
            work_days=6,
            off_days=1,
            status="PASS",
        )
        assert r.status == "PASS"


class TestPostCallEntry:
    def test_defaults(self):
        r = PostCallEntry(name="Dr. Jones", call_date=date(2026, 1, 5), status="PASS")
        assert r.am_next_day is None
        assert r.pm_next_day is None


class TestCallBeforeLeaveEntry:
    def test_defaults(self):
        r = CallBeforeLeaveEntry(
            name="Dr. Jones",
            call_date=date(2026, 1, 5),
            next_day=date(2026, 1, 6),
            status="PASS",
        )
        assert r.absence_type is None

    def test_with_absence_type(self):
        r = CallBeforeLeaveEntry(
            name="Dr. Jones",
            call_date=date(2026, 1, 5),
            next_day=date(2026, 1, 6),
            absence_type="vacation",
            status="SOFT",
        )
        assert r.absence_type == "vacation"


class TestAccountabilityEntry:
    def test_defaults(self):
        r = AccountabilityEntry(
            name="Dr. Jones", assigned=40, unaccounted=0, notes="All accounted"
        )
        assert r.pgy_level is None
        assert r.role is None


class TestExecutiveSummary:
    def test_valid(self):
        r = ExecutiveSummary(
            block_number=10,
            date_range="Jan 1 - Jan 31",
            total_assignments=200,
            resident_assignments=160,
            faculty_assignments=40,
            acgme_compliance_rate=100.0,
            double_bookings=0,
            call_coverage="28/28",
            nf_one_in_seven="PASS (4/4)",
            post_call_pcat_do="PASS",
            call_before_leave="PASS",
            overall_status="PASS",
        )
        assert r.overall_status == "PASS"
        assert r.acgme_compliance_rate == 100.0


class TestSectionA:
    def test_valid(self):
        r = SectionA(
            block_assignments=[
                BlockAssignmentEntry(name="Dr. Jones", pgy_level=1, rotation="FM")
            ],
            absences=[],
            call_coverage=CallCoverageSummary(
                sun_thu_count=20, fri_sat_count=8, total_nights=28
            ),
            faculty_preloaded=[],
        )
        assert len(r.block_assignments) == 1


class TestSectionB:
    def test_valid(self):
        r = SectionB(
            by_rotation=[
                RotationSummary(rotation="FM", rotation_type="outpatient", count=5)
            ],
            resident_distribution=[],
            total_solved=50,
        )
        assert r.total_solved == 50


class TestSectionC:
    def test_valid(self):
        r = SectionC(
            all_assignments=[],
            preloaded_total=20,
            solved_total=80,
            grand_total=100,
            resident_range="40-48",
            faculty_range="22-24",
            gaps_detected=["Gap 1"],
        )
        assert len(r.gaps_detected) == 1


class TestSectionD:
    def test_valid(self):
        r = SectionD(
            faculty_fmit_friday="N/A",
            nf_one_in_seven=[],
            post_call_pcat_do=[],
            post_call_gap_count=0,
            call_before_leave=[],
            call_before_leave_gap_count=0,
        )
        assert r.post_call_gap_count == 0


class TestSectionE:
    def test_valid(self):
        r = SectionE(
            resident_accountability=[],
            faculty_accountability=[],
            all_accounted=True,
        )
        assert r.all_accounted is True


class TestBlockQualityReport:
    def _make_report(self):
        block_dates = BlockDates(
            block_number=10,
            academic_year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            days=31,
            slots=62,
        )
        executive_summary = ExecutiveSummary(
            block_number=10,
            date_range="Jan 1 - Jan 31",
            total_assignments=200,
            resident_assignments=160,
            faculty_assignments=40,
            acgme_compliance_rate=100.0,
            double_bookings=0,
            call_coverage="28/28",
            nf_one_in_seven="PASS",
            post_call_pcat_do="PASS",
            call_before_leave="PASS",
            overall_status="PASS",
        )
        section_a = SectionA(
            block_assignments=[],
            absences=[],
            call_coverage=CallCoverageSummary(
                sun_thu_count=20, fri_sat_count=8, total_nights=28
            ),
            faculty_preloaded=[],
        )
        section_b = SectionB(by_rotation=[], resident_distribution=[], total_solved=0)
        section_c = SectionC(
            all_assignments=[],
            preloaded_total=0,
            solved_total=0,
            grand_total=0,
            resident_range="0",
            faculty_range="0",
            gaps_detected=[],
        )
        section_d = SectionD(
            faculty_fmit_friday="N/A",
            nf_one_in_seven=[],
            post_call_pcat_do=[],
            post_call_gap_count=0,
            call_before_leave=[],
            call_before_leave_gap_count=0,
        )
        section_e = SectionE(
            resident_accountability=[],
            faculty_accountability=[],
            all_accounted=True,
        )
        return BlockQualityReport(
            block_dates=block_dates,
            executive_summary=executive_summary,
            section_a=section_a,
            section_b=section_b,
            section_c=section_c,
            section_d=section_d,
            section_e=section_e,
            generated_at="2026-01-31T12:00:00",
        )

    def test_valid(self):
        r = self._make_report()
        assert r.block_dates.block_number == 10
        assert r.executive_summary.overall_status == "PASS"


class TestBlockSummaryEntry:
    def test_valid(self):
        r = BlockSummaryEntry(
            block_number=10,
            dates="Jan 1 - Jan 31",
            days=31,
            resident_count=8,
            faculty_count=4,
            total=200,
            acgme_compliance="100%",
            nf_one_in_seven="PASS",
            post_call="PASS",
            call_before_leave="PASS",
            status="PASS",
        )
        assert r.block_number == 10


class TestCrossBlockSummary:
    def test_valid(self):
        r = CrossBlockSummary(
            academic_year=2026,
            blocks=[],
            total_assignments=0,
            total_resident=0,
            total_faculty=0,
            overall_status="PASS",
            gaps_identified=[],
            generated_at="2026-01-31T12:00:00",
        )
        assert r.academic_year == 2026
        assert r.blocks == []
