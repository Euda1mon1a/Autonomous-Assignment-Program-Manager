"""Tests for BlockQualityReportService."""

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.schemas.block_quality_report import (
    BlockDates,
    BlockAssignmentEntry,
    AbsenceEntry,
    CallCoverageSummary,
    FacultyPreloadedEntry,
    RotationSummary,
    ResidentDistribution,
    NFOneInSevenEntry,
    PostCallEntry,
    BlockQualityReport,
    CrossBlockSummary,
)
from app.services.block_quality_report_service import BlockQualityReportService


# =============================================================================
# Block Dates Tests
# =============================================================================


class TestGetBlockDates:
    """Tests for get_block_dates method."""

    def test_get_block_dates_valid_block(self):
        """Test getting dates for a valid block."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (
            date(2024, 12, 23),  # start_date
            date(2025, 1, 19),  # end_date
            28,  # days
        )
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_block_dates(10)

        assert isinstance(result, BlockDates)
        assert result.block_number == 10
        assert result.start_date == date(2024, 12, 23)
        assert result.end_date == date(2025, 1, 19)
        assert result.days == 28
        assert result.slots == 56

    def test_get_block_dates_invalid_block_raises(self):
        """Test that invalid block number raises ValueError."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (None, None, None)
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)

        with pytest.raises(ValueError, match="Block 99 not found"):
            service.get_block_dates(99)

    def test_get_block_dates_short_block(self):
        """Test getting dates for a shorter block (e.g., Block 13)."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (
            date(2025, 6, 2),
            date(2025, 6, 28),
            27,
        )
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_block_dates(13)

        assert result.days == 27
        assert result.slots == 54


# =============================================================================
# Block Assignments Tests
# =============================================================================


class TestGetBlockAssignments:
    """Tests for get_block_assignments method."""

    def test_get_block_assignments_returns_entries(self):
        """Test getting block assignments returns correct entries."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("John Doe", 2, "PCAT PM"),
            ("Jane Smith", 3, "Night Float"),
        ]
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_block_assignments(10, 2025)

        assert len(result) == 2
        assert isinstance(result[0], BlockAssignmentEntry)
        assert result[0].name == "John Doe"
        assert result[0].pgy_level == 2
        assert result[0].rotation == "PCAT PM"

    def test_get_block_assignments_empty(self):
        """Test getting block assignments when none exist."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_block_assignments(10, 2025)

        assert len(result) == 0


# =============================================================================
# Absences Tests
# =============================================================================


class TestGetAbsences:
    """Tests for get_absences method."""

    def test_get_absences_overlapping(self):
        """Test getting absences that overlap with date range."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("John Doe", "Vacation", date(2024, 12, 25), date(2025, 1, 1)),
            ("Jane Smith", "Conference", date(2025, 1, 5), date(2025, 1, 7)),
        ]
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_absences(date(2024, 12, 23), date(2025, 1, 19))

        assert len(result) == 2
        assert isinstance(result[0], AbsenceEntry)
        assert result[0].name == "John Doe"
        assert result[0].absence_type == "Vacation"

    def test_get_absences_none(self):
        """Test getting absences when none exist."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_absences(date(2024, 12, 23), date(2025, 1, 19))

        assert len(result) == 0


# =============================================================================
# Call Coverage Tests
# =============================================================================


class TestGetCallCoverage:
    """Tests for get_call_coverage method."""

    def test_get_call_coverage_full_block(self):
        """Test call coverage for a full 28-day block."""
        mock_db = MagicMock()

        # Mock two separate queries
        mock_result1 = MagicMock()
        mock_result1.fetchone.return_value = (20,)  # Sun-Thu count

        mock_result2 = MagicMock()
        mock_result2.fetchone.return_value = (8,)  # Fri-Sat count

        mock_db.execute.side_effect = [mock_result1, mock_result2]

        service = BlockQualityReportService(mock_db)
        result = service.get_call_coverage(date(2024, 12, 23), date(2025, 1, 19))

        assert isinstance(result, CallCoverageSummary)
        assert result.sun_thu_count == 20
        assert result.fri_sat_count == 8
        assert result.total_nights == 28


# =============================================================================
# Faculty Preloaded Tests
# =============================================================================


class TestGetFacultyPreloaded:
    """Tests for get_faculty_preloaded method."""

    def test_get_faculty_preloaded_returns_entries(self):
        """Test getting faculty preloaded assignments."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("Dr. Smith", "attending", 24),
            ("Dr. Jones", "chief", 20),
        ]
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_faculty_preloaded(date(2024, 12, 23), date(2025, 1, 19))

        assert len(result) == 2
        assert isinstance(result[0], FacultyPreloadedEntry)
        assert result[0].name == "Dr. Smith"
        assert result[0].slots == 24


# =============================================================================
# Solved By Rotation Tests
# =============================================================================


class TestGetSolvedByRotation:
    """Tests for get_solved_by_rotation method."""

    def test_get_solved_by_rotation_returns_summaries(self):
        """Test getting solved assignments grouped by rotation."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("PCAT PM", "clinic", 200),
            ("Night Float", "inpatient", 150),
            ("DO AM", "clinic", 100),
        ]
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_solved_by_rotation(date(2024, 12, 23), date(2025, 1, 19))

        assert len(result) == 3
        assert isinstance(result[0], RotationSummary)
        assert result[0].rotation == "PCAT PM"
        assert result[0].rotation_type == "clinic"
        assert result[0].count == 200

    def test_get_solved_by_rotation_handles_null_rotation(self):
        """Test handling null rotation names."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (None, None, 50),  # No rotation assigned
        ]
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_solved_by_rotation(date(2024, 12, 23), date(2025, 1, 19))

        assert len(result) == 1
        assert result[0].rotation == "Unknown"
        assert result[0].rotation_type == "unknown"


# =============================================================================
# Resident Distribution Tests
# =============================================================================


class TestGetResidentDistribution:
    """Tests for get_resident_distribution method."""

    def test_get_resident_distribution_returns_entries(self):
        """Test getting resident slot distribution."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("John Doe", 2, 48),
            ("Jane Smith", 3, 44),
        ]
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_resident_distribution(
            date(2024, 12, 23), date(2025, 1, 19), 56
        )

        assert len(result) == 2
        assert isinstance(result[0], ResidentDistribution)
        assert result[0].name == "John Doe"
        assert result[0].count == 48
        assert result[0].utilization_pct == 86.0  # 48/56 * 100


# =============================================================================
# NF One-in-Seven Tests
# =============================================================================


class TestGetNfOneInSeven:
    """Tests for get_nf_one_in_seven method."""

    def test_get_nf_one_in_seven_pass(self):
        """Test NF 1-in-7 check that passes."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("John Doe", "Night Float", 24),  # 28 - 24 = 4 off days >= 4 min
        ]
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_nf_one_in_seven(date(2024, 12, 23), date(2025, 1, 19), 28)

        assert len(result) == 1
        assert isinstance(result[0], NFOneInSevenEntry)
        assert result[0].status == "PASS"
        assert result[0].work_days == 24
        assert result[0].off_days == 4

    def test_get_nf_one_in_seven_fail(self):
        """Test NF 1-in-7 check that fails."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("John Doe", "Night Float", 26),  # 28 - 26 = 2 off days < 4 min
        ]
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_nf_one_in_seven(date(2024, 12, 23), date(2025, 1, 19), 28)

        assert len(result) == 1
        assert result[0].status == "FAIL"
        assert result[0].off_days == 2


# =============================================================================
# Post-Call Check Tests
# =============================================================================


class TestGetPostCallCheck:
    """Tests for get_post_call_check method."""

    def test_get_post_call_check_pass(self):
        """Test post-call check that passes (PCAT AM + DO PM)."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("John Doe", date(2024, 12, 24), "PCAT AM", "DO PM"),
        ]
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_post_call_check(date(2024, 12, 23), date(2025, 1, 19))

        assert len(result) == 1
        assert isinstance(result[0], PostCallEntry)
        assert result[0].status == "PASS"

    def test_get_post_call_check_gap(self):
        """Test post-call check that shows gap (no PCAT/DO)."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("John Doe", date(2024, 12, 24), None, None),
        ]
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_post_call_check(date(2024, 12, 23), date(2025, 1, 19))

        assert len(result) == 1
        assert result[0].status == "NO PCAT/DO"

    def test_get_post_call_check_partial(self):
        """Test post-call check that is partial (only PCAT or DO)."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("John Doe", date(2024, 12, 24), "PCAT AM", "Clinic"),  # PCAT but no DO
        ]
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_post_call_check(date(2024, 12, 23), date(2025, 1, 19))

        assert len(result) == 1
        assert result[0].status == "PARTIAL"


# =============================================================================
# Report Generation Tests
# =============================================================================


class TestGenerateReport:
    """Tests for generate_report method."""

    @patch.object(BlockQualityReportService, "get_block_dates")
    @patch.object(BlockQualityReportService, "get_block_assignments")
    @patch.object(BlockQualityReportService, "get_absences")
    @patch.object(BlockQualityReportService, "get_call_coverage")
    @patch.object(BlockQualityReportService, "get_faculty_preloaded")
    @patch.object(BlockQualityReportService, "get_solved_by_rotation")
    @patch.object(BlockQualityReportService, "get_resident_distribution")
    @patch.object(BlockQualityReportService, "get_totals")
    @patch.object(BlockQualityReportService, "get_nf_one_in_seven")
    @patch.object(BlockQualityReportService, "get_post_call_check")
    @patch.object(BlockQualityReportService, "get_accountability")
    def test_generate_report_success(
        self,
        mock_accountability,
        mock_post_call,
        mock_nf,
        mock_totals,
        mock_resident_dist,
        mock_rotation,
        mock_faculty,
        mock_call,
        mock_absences,
        mock_assignments,
        mock_dates,
    ):
        """Test successful report generation."""
        mock_db = MagicMock()

        # Set up mocks
        mock_dates.return_value = BlockDates(
            block_number=10,
            academic_year=2025,
            start_date=date(2024, 12, 23),
            end_date=date(2025, 1, 19),
            days=28,
            slots=56,
        )
        mock_assignments.return_value = [
            BlockAssignmentEntry(name="John Doe", pgy_level=2, rotation="PCAT PM")
        ]
        mock_absences.return_value = []
        mock_call.return_value = CallCoverageSummary(
            sun_thu_count=20, fri_sat_count=8, total_nights=28
        )
        mock_faculty.return_value = [
            FacultyPreloadedEntry(name="Dr. Smith", slots=24, role="attending")
        ]
        mock_rotation.return_value = [
            RotationSummary(rotation="PCAT PM", rotation_type="clinic", count=100)
        ]
        mock_resident_dist.return_value = [
            ResidentDistribution(
                name="John Doe", pgy_level=2, count=48, utilization_pct=86.0
            )
        ]
        mock_totals.return_value = {"resident": 744, "faculty": 264}
        mock_nf.return_value = []
        mock_post_call.return_value = []
        mock_accountability.return_value = ([], [])

        service = BlockQualityReportService(mock_db)
        result = service.generate_report(10, 2025)

        assert isinstance(result, BlockQualityReport)
        assert result.block_dates.block_number == 10
        assert result.executive_summary.block_number == 10
        assert "generated_at" in result.model_dump()

    def test_generate_report_invalid_block(self):
        """Test report generation with invalid block."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (None, None, None)
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)

        with pytest.raises(ValueError, match="Block 99 not found"):
            service.generate_report(99, 2025)


# =============================================================================
# Summary Generation Tests
# =============================================================================


class TestGenerateSummary:
    """Tests for generate_summary method."""

    @patch.object(BlockQualityReportService, "generate_report")
    def test_generate_summary_multiple_blocks(self, mock_generate_report):
        """Test generating summary for multiple blocks."""
        mock_db = MagicMock()

        # Create mock reports
        mock_report1 = MagicMock()
        mock_report1.executive_summary.date_range = "2024-12-23 to 2025-01-19"
        mock_report1.executive_summary.resident_assignments = 744
        mock_report1.executive_summary.faculty_assignments = 264
        mock_report1.executive_summary.total_assignments = 1008
        mock_report1.executive_summary.acgme_compliance_rate = 100.0
        mock_report1.executive_summary.nf_one_in_seven = "PASS (4/4)"
        mock_report1.executive_summary.post_call_pcat_do = "GAP"
        mock_report1.executive_summary.overall_status = "PASS (1 GAP)"
        mock_report1.block_dates.days = 28

        mock_report2 = MagicMock()
        mock_report2.executive_summary.date_range = "2025-01-20 to 2025-02-16"
        mock_report2.executive_summary.resident_assignments = 768
        mock_report2.executive_summary.faculty_assignments = 272
        mock_report2.executive_summary.total_assignments = 1040
        mock_report2.executive_summary.acgme_compliance_rate = 100.0
        mock_report2.executive_summary.nf_one_in_seven = "PASS (4/4)"
        mock_report2.executive_summary.post_call_pcat_do = "GAP"
        mock_report2.executive_summary.overall_status = "PASS (1 GAP)"
        mock_report2.block_dates.days = 28

        mock_generate_report.side_effect = [mock_report1, mock_report2]

        service = BlockQualityReportService(mock_db)
        result = service.generate_summary([10, 11], 2025)

        assert isinstance(result, CrossBlockSummary)
        assert len(result.blocks) == 2
        assert result.total_resident == 744 + 768
        assert result.total_faculty == 264 + 272
        assert result.academic_year == 2025
        assert len(result.gaps_identified) == 2  # Both blocks have GAP


# =============================================================================
# Markdown Output Tests
# =============================================================================


class TestMarkdownOutput:
    """Tests for markdown conversion methods."""

    def test_to_markdown_format(self):
        """Test converting report to markdown format."""
        from app.schemas.block_quality_report import (
            ExecutiveSummary,
            SectionA,
            SectionB,
            SectionC,
            SectionD,
            SectionE,
        )

        mock_db = MagicMock()
        service = BlockQualityReportService(mock_db)

        # Create a minimal report with actual Pydantic models
        report = BlockQualityReport(
            block_dates=BlockDates(
                block_number=10,
                academic_year=2025,
                start_date=date(2024, 12, 23),
                end_date=date(2025, 1, 19),
                days=28,
                slots=56,
            ),
            executive_summary=ExecutiveSummary(
                block_number=10,
                date_range="2024-12-23 to 2025-01-19",
                total_assignments=1008,
                resident_assignments=744,
                faculty_assignments=264,
                acgme_compliance_rate=100.0,
                double_bookings=0,
                call_coverage="28/28",
                nf_one_in_seven="PASS (4/4)",
                post_call_pcat_do="GAP",
                overall_status="PASS",
            ),
            section_a=SectionA(
                block_assignments=[],
                absences=[],
                call_coverage=CallCoverageSummary(
                    sun_thu_count=20, fri_sat_count=8, total_nights=28
                ),
                faculty_preloaded=[],
            ),
            section_b=SectionB(
                by_rotation=[], resident_distribution=[], total_solved=744
            ),
            section_c=SectionC(
                all_assignments=[],
                preloaded_total=264,
                solved_total=744,
                grand_total=1008,
                resident_range="40-48",
                faculty_range="20-24",
                gaps_detected=[],
            ),
            section_d=SectionD(
                faculty_fmit_friday="N/A",
                nf_one_in_seven=[],
                post_call_pcat_do=[],
                post_call_gap_count=0,
            ),
            section_e=SectionE(
                resident_accountability=[],
                faculty_accountability=[],
                all_accounted=True,
            ),
            generated_at="2025-01-11T12:00:00",
        )

        result = service.to_markdown(report)

        assert "# Block 10" in result
        assert "Executive Summary" in result
        assert "Section A" in result
        assert "Section B" in result
        assert "Section D" in result

    def test_summary_to_markdown_format(self):
        """Test converting cross-block summary to markdown."""
        mock_db = MagicMock()
        service = BlockQualityReportService(mock_db)

        summary = CrossBlockSummary(
            academic_year=2025,
            blocks=[],
            total_assignments=4112,
            total_resident=3020,
            total_faculty=1092,
            overall_status="PASS with gaps",
            gaps_identified=["Block 10: Post-Call PCAT/DO gap"],
            generated_at="2025-01-11T12:00:00",
        )

        result = service.summary_to_markdown(summary)

        assert "Cross-Block Summary" in result
        assert "Academic Year" in result
        assert "4112" in result
        assert "PASS with gaps" in result


# =============================================================================
# Totals Tests
# =============================================================================


class TestGetTotals:
    """Tests for get_totals method."""

    def test_get_totals_returns_counts(self):
        """Test getting total assignments by type."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("resident", 744),
            ("faculty", 264),
        ]
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_totals(date(2024, 12, 23), date(2025, 1, 19))

        assert result["resident"] == 744
        assert result["faculty"] == 264

    def test_get_totals_empty(self):
        """Test getting totals when no assignments exist."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        service = BlockQualityReportService(mock_db)
        result = service.get_totals(date(2024, 12, 23), date(2025, 1, 19))

        assert result["resident"] == 0
        assert result["faculty"] == 0
