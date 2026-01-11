"""Tests for block quality report tasks."""

import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.tasks.block_quality_report_tasks import (
    generate_block_quality_report,
    generate_multi_block_report,
    check_block_schedule_quality,
)


# =============================================================================
# Generate Block Quality Report Tests
# =============================================================================


class TestGenerateBlockQualityReport:
    """Tests for generate_block_quality_report task."""

    @patch("app.tasks.block_quality_report_tasks.SessionLocal")
    @patch("app.tasks.block_quality_report_tasks.BlockQualityReportService")
    def test_generate_block_quality_report_success(
        self, mock_service_class, mock_session
    ):
        """Test successful block quality report generation."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock report data
        mock_report = MagicMock()
        mock_report.executive_summary.total_assignments = 1008
        mock_report.executive_summary.resident_assignments = 744
        mock_report.executive_summary.faculty_assignments = 264
        mock_report.executive_summary.overall_status = "PASS"
        mock_report.executive_summary.acgme_compliance_rate = 100.0
        mock_report.executive_summary.nf_one_in_seven = "PASS (4/4)"
        mock_report.executive_summary.post_call_pcat_do = "GAP"
        mock_service.generate_report.return_value = mock_report

        # Execute the underlying function directly (bypass Celery binding)
        # Access the run method and use positional args
        mock_task = MagicMock()
        result = generate_block_quality_report.run(
            10,  # block_number
            2025,  # academic_year
            "summary",  # output_format
            False,  # save_to_file
        )

        # Verify results
        assert result["success"] is True
        assert result["block_number"] == 10
        assert result["total_assignments"] == 1008
        assert result["resident_assignments"] == 744
        assert result["faculty_assignments"] == 264

        # Verify database session was closed
        mock_db.close.assert_called_once()

    @patch("app.tasks.block_quality_report_tasks.SessionLocal")
    @patch("app.tasks.block_quality_report_tasks.BlockQualityReportService")
    @patch("app.tasks.block_quality_report_tasks.get_reports_directory")
    def test_generate_block_quality_report_saves_markdown(
        self, mock_get_dir, mock_service_class, mock_session, tmp_path
    ):
        """Test report saves to file in markdown format."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock reports directory
        mock_get_dir.return_value = tmp_path

        # Mock report service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock report data
        mock_report = MagicMock()
        mock_report.executive_summary.total_assignments = 1008
        mock_report.executive_summary.resident_assignments = 744
        mock_report.executive_summary.faculty_assignments = 264
        mock_report.executive_summary.overall_status = "PASS"
        mock_report.executive_summary.acgme_compliance_rate = 100.0
        mock_report.executive_summary.nf_one_in_seven = "PASS (4/4)"
        mock_report.executive_summary.post_call_pcat_do = "GAP"
        mock_service.generate_report.return_value = mock_report
        mock_service.to_markdown.return_value = "# Block 10 Report\n\nTest content"

        # Execute the underlying function directly
        result = generate_block_quality_report.run(
            10,  # block_number
            2025,  # academic_year
            "markdown",  # output_format
            True,  # save_to_file
        )

        # Verify file was created
        assert result["success"] is True
        assert result["file_path"] is not None
        assert "BLOCK_10" in result["file_path"]
        assert ".md" in result["file_path"]

    @patch("app.tasks.block_quality_report_tasks.SessionLocal")
    @patch("app.tasks.block_quality_report_tasks.BlockQualityReportService")
    @patch("app.tasks.block_quality_report_tasks.get_reports_directory")
    def test_generate_block_quality_report_saves_json(
        self, mock_get_dir, mock_service_class, mock_session, tmp_path
    ):
        """Test report saves to file in JSON format."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock reports directory
        mock_get_dir.return_value = tmp_path

        # Mock report service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock report data
        mock_report = MagicMock()
        mock_report.executive_summary.total_assignments = 1008
        mock_report.executive_summary.resident_assignments = 744
        mock_report.executive_summary.faculty_assignments = 264
        mock_report.executive_summary.overall_status = "PASS"
        mock_report.executive_summary.acgme_compliance_rate = 100.0
        mock_report.executive_summary.nf_one_in_seven = "PASS (4/4)"
        mock_report.executive_summary.post_call_pcat_do = "GAP"
        mock_report.model_dump_json.return_value = '{"test": "data"}'
        mock_service.generate_report.return_value = mock_report

        # Execute the underlying function directly
        result = generate_block_quality_report.run(
            10,  # block_number
            2025,  # academic_year
            "json",  # output_format
            True,  # save_to_file
        )

        # Verify file was created
        assert result["success"] is True
        assert ".json" in result["file_path"]


# =============================================================================
# Generate Multi-Block Report Tests
# =============================================================================


class TestGenerateMultiBlockReport:
    """Tests for generate_multi_block_report task."""

    @patch("app.tasks.block_quality_report_tasks.SessionLocal")
    @patch("app.tasks.block_quality_report_tasks.BlockQualityReportService")
    @patch("app.tasks.block_quality_report_tasks.get_reports_directory")
    def test_generate_multi_block_report_success(
        self, mock_get_dir, mock_service_class, mock_session, tmp_path
    ):
        """Test successful multi-block report generation."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock reports directory
        mock_get_dir.return_value = tmp_path

        # Mock report service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock individual reports
        def create_mock_report(total):
            report = MagicMock()
            report.executive_summary.total_assignments = total
            report.executive_summary.overall_status = "PASS"
            return report

        mock_service.generate_report.side_effect = [
            create_mock_report(1008),
            create_mock_report(1040),
        ]
        mock_service.to_markdown.return_value = "# Report"
        mock_service.generate_summary.return_value = MagicMock(
            overall_status="PASS",
            gaps_identified=[],
            model_dump_json=MagicMock(return_value="{}"),
        )
        mock_service.summary_to_markdown.return_value = "# Summary"

        # Execute the underlying function directly
        result = generate_multi_block_report.run(
            [10, 11],  # block_numbers
            2025,  # academic_year
            True,  # include_summary
            "markdown",  # output_format
            True,  # save_to_file
        )

        # Verify results
        assert result["success"] is True
        assert result["blocks_processed"] == 2
        assert result["blocks_failed"] == 0
        assert result["total_assignments"] == 2048
        assert "summary_file_path" in result

    @patch("app.tasks.block_quality_report_tasks.SessionLocal")
    @patch("app.tasks.block_quality_report_tasks.BlockQualityReportService")
    @patch("app.tasks.block_quality_report_tasks.get_reports_directory")
    def test_generate_multi_block_report_partial_failure(
        self, mock_get_dir, mock_service_class, mock_session, tmp_path
    ):
        """Test multi-block report with one block failing."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock reports directory
        mock_get_dir.return_value = tmp_path

        # Mock report service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # First report succeeds, second fails
        def generate_side_effect(block_num, year):
            if block_num == 10:
                report = MagicMock()
                report.executive_summary.total_assignments = 1008
                report.executive_summary.overall_status = "PASS"
                return report
            else:
                raise ValueError(f"Block {block_num} not found")

        mock_service.generate_report.side_effect = generate_side_effect
        mock_service.to_markdown.return_value = "# Report"
        mock_service.generate_summary.return_value = MagicMock(
            overall_status="PASS",
            gaps_identified=[],
        )
        mock_service.summary_to_markdown.return_value = "# Summary"

        # Execute the underlying function directly
        result = generate_multi_block_report.run(
            [10, 99],  # block_numbers
            2025,  # academic_year
            True,  # include_summary
            "markdown",  # output_format
            True,  # save_to_file
        )

        # Verify results
        assert result["success"] is True
        assert result["blocks_processed"] == 1
        assert result["blocks_failed"] == 1

    @patch("app.tasks.block_quality_report_tasks.SessionLocal")
    @patch("app.tasks.block_quality_report_tasks.BlockQualityReportService")
    def test_generate_multi_block_report_without_summary(
        self, mock_service_class, mock_session
    ):
        """Test multi-block report without summary."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock individual reports
        report = MagicMock()
        report.executive_summary.total_assignments = 1008
        report.executive_summary.overall_status = "PASS"
        mock_service.generate_report.return_value = report

        # Execute the underlying function directly
        result = generate_multi_block_report.run(
            [10],  # block_numbers
            2025,  # academic_year
            False,  # include_summary
            "markdown",  # output_format
            False,  # save_to_file
        )

        # Verify summary was not generated
        mock_service.generate_summary.assert_not_called()
        assert "summary_file_path" not in result


# =============================================================================
# Check Block Schedule Quality Tests
# =============================================================================


class TestCheckBlockScheduleQuality:
    """Tests for check_block_schedule_quality task."""

    @patch("app.tasks.block_quality_report_tasks.SessionLocal")
    @patch("app.tasks.block_quality_report_tasks.BlockQualityReportService")
    def test_check_block_schedule_quality_pass(self, mock_service_class, mock_session):
        """Test quality check that passes."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock report with no issues
        mock_report = MagicMock()
        mock_report.executive_summary.total_assignments = 1008
        mock_report.executive_summary.acgme_compliance_rate = 100.0
        mock_report.executive_summary.overall_status = "PASS"
        mock_report.executive_summary.post_call_pcat_do = "PASS"
        mock_report.executive_summary.nf_one_in_seven = "PASS (4/4)"
        mock_report.executive_summary.double_bookings = 0
        mock_service.generate_report.return_value = mock_report

        # Execute task
        result = check_block_schedule_quality(block_number=10, academic_year=2025)

        # Verify results
        assert result["passed"] is True
        assert result["block_number"] == 10
        assert len(result["issues"]) == 0

    @patch("app.tasks.block_quality_report_tasks.SessionLocal")
    @patch("app.tasks.block_quality_report_tasks.BlockQualityReportService")
    def test_check_block_schedule_quality_with_issues(
        self, mock_service_class, mock_session
    ):
        """Test quality check that fails with issues."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock report with issues
        mock_report = MagicMock()
        mock_report.executive_summary.total_assignments = 1008
        mock_report.executive_summary.acgme_compliance_rate = 100.0
        mock_report.executive_summary.overall_status = "PASS (1 GAP)"
        mock_report.executive_summary.post_call_pcat_do = "GAP"
        mock_report.executive_summary.nf_one_in_seven = "FAIL (2/4)"
        mock_report.executive_summary.double_bookings = 2
        mock_service.generate_report.return_value = mock_report

        # Execute task
        result = check_block_schedule_quality(block_number=10, academic_year=2025)

        # Verify results
        assert result["passed"] is False
        assert result["block_number"] == 10
        assert len(result["issues"]) == 3
        assert "Post-call PCAT/DO gap" in result["issues"]
        assert "NF 1-in-7 failure" in result["issues"]
        assert "2 double-bookings" in result["issues"]

    @patch("app.tasks.block_quality_report_tasks.SessionLocal")
    @patch("app.tasks.block_quality_report_tasks.BlockQualityReportService")
    def test_check_block_schedule_quality_error(self, mock_service_class, mock_session):
        """Test quality check handles errors gracefully."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report service to raise exception
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.generate_report.side_effect = ValueError("Block not found")

        # Execute task
        result = check_block_schedule_quality(block_number=99, academic_year=2025)

        # Verify results
        assert result["passed"] is False
        assert result["block_number"] == 99
        assert "error" in result
        assert "Block not found" in result["error"]


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestTaskErrorHandling:
    """Tests for task error handling and retries."""

    @patch("app.tasks.block_quality_report_tasks.SessionLocal")
    def test_database_session_always_closes(self, mock_session):
        """Test database session is closed even on error."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Execute task that will fail (no service mock)
        try:
            check_block_schedule_quality(block_number=10, academic_year=2025)
        except Exception:
            pass

        # Verify database session was still closed
        mock_db.close.assert_called_once()


# =============================================================================
# Reports Directory Tests
# =============================================================================


class TestGetReportsDirectory:
    """Tests for get_reports_directory helper."""

    @patch("app.tasks.block_quality_report_tasks.os.getenv")
    def test_get_reports_directory_uses_env_var(self, mock_getenv, tmp_path):
        """Test reports directory uses environment variable."""
        from app.tasks.block_quality_report_tasks import get_reports_directory

        mock_getenv.return_value = str(tmp_path / "custom_reports")

        result = get_reports_directory()

        assert "custom_reports" in str(result)
        assert result.exists()

    @patch("app.tasks.block_quality_report_tasks.os.getenv")
    def test_get_reports_directory_creates_if_missing(self, mock_getenv, tmp_path):
        """Test reports directory is created if it doesn't exist."""
        from app.tasks.block_quality_report_tasks import get_reports_directory

        new_dir = tmp_path / "new_reports"
        mock_getenv.return_value = str(new_dir)

        # Directory shouldn't exist yet
        assert not new_dir.exists()

        result = get_reports_directory()

        # Directory should be created
        assert result.exists()
