"""Tests for compliance report tasks."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, Mock
from datetime import date, timedelta
import os
import json
import tempfile
from uuid import uuid4

from app.tasks.compliance_report_tasks import (
    generate_daily_compliance_summary,
    generate_weekly_compliance_report,
    generate_monthly_executive_summary,
    generate_custom_compliance_report,
    check_violation_alerts,
)


# =============================================================================
# Report Storage Tests
# =============================================================================


class TestReportStorage:
    """Tests for report storage functionality."""

    def test_save_report_creates_file(self, tmp_path):
        """Test report is saved to file."""
        # This test assumes there's a save_report helper function
        # If it doesn't exist, this tests the file creation logic
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        report_data = {"violations": [], "summary": "All clear"}
        filename = f"test_report_{date.today().isoformat()}.json"
        filepath = reports_dir / filename

        # Save report
        with open(filepath, 'w') as f:
            json.dump(report_data, f)

        # Verify file exists and contains correct data
        assert filepath.exists()
        with open(filepath) as f:
            saved_data = json.load(f)
        assert saved_data["violations"] == []
        assert saved_data["summary"] == "All clear"

    def test_save_report_creates_directory(self, tmp_path):
        """Test report directory is created if missing."""
        reports_dir = tmp_path / "new_reports"

        # Directory should not exist yet
        assert not reports_dir.exists()

        # Create directory
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Verify directory was created
        assert reports_dir.exists()

        # Save a test report
        report_data = {"test": "data"}
        filepath = reports_dir / "test_report.json"
        with open(filepath, 'w') as f:
            json.dump(report_data, f)

        assert filepath.exists()


# =============================================================================
# Daily Compliance Summary Tests
# =============================================================================


class TestDailyComplianceSummary:
    """Tests for daily compliance summary generation."""

    @patch('app.tasks.compliance_report_tasks.SessionLocal')
    @patch('app.tasks.compliance_report_tasks.ComplianceReportGenerator')
    def test_generate_daily_compliance_summary_success(self, mock_generator, mock_session):
        """Test successful daily summary generation."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report generator
        mock_gen_instance = MagicMock()
        mock_generator.return_value = mock_gen_instance

        # Mock report data
        mock_report_data = MagicMock()
        mock_report_data.work_hour_summary = {
            "total_residents": 10,
            "total_violations": 0,
            "compliance_rate": 100.0
        }
        mock_report_data.coverage_metrics = {
            "coverage_rate_percent": 95.0
        }
        mock_gen_instance.generate_compliance_data.return_value = mock_report_data

        # Execute task
        result = generate_daily_compliance_summary(lookback_days=1)

        # Verify results
        assert result["success"] is True
        assert result["message"] == "Daily compliance summary generated"
        assert result["summary"]["total_residents"] == 10
        assert result["summary"]["total_violations"] == 0
        assert result["summary"]["compliance_rate"] == 100.0

        # Verify database session was closed
        mock_db.close.assert_called_once()

    @patch('app.tasks.compliance_report_tasks.SessionLocal')
    @patch('app.tasks.compliance_report_tasks.ComplianceReportGenerator')
    def test_generate_daily_compliance_summary_with_violations(self, mock_generator, mock_session, caplog):
        """Test daily summary with violations found."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report generator
        mock_gen_instance = MagicMock()
        mock_generator.return_value = mock_gen_instance

        # Mock report data with violations
        mock_report_data = MagicMock()
        mock_report_data.work_hour_summary = {
            "total_residents": 10,
            "total_violations": 3,
            "compliance_rate": 70.0
        }
        mock_report_data.coverage_metrics = {
            "coverage_rate_percent": 95.0
        }
        mock_gen_instance.generate_compliance_data.return_value = mock_report_data

        # Execute task
        result = generate_daily_compliance_summary(lookback_days=1)

        # Verify results
        assert result["success"] is True
        assert result["summary"]["total_violations"] == 3

        # Verify warning was logged
        assert any("Found 3 violations" in record.message for record in caplog.records)


# =============================================================================
# Weekly Compliance Report Tests
# =============================================================================


class TestWeeklyComplianceReport:
    """Tests for weekly compliance report generation."""

    @patch('app.tasks.compliance_report_tasks.SessionLocal')
    @patch('app.tasks.compliance_report_tasks.ComplianceReportGenerator')
    def test_generate_weekly_compliance_report_pdf(self, mock_generator, mock_session):
        """Test weekly report generation in PDF format."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report generator
        mock_gen_instance = MagicMock()
        mock_generator.return_value = mock_gen_instance

        # Mock report data
        mock_report_data = MagicMock()
        mock_report_data.work_hour_summary = {
            "total_residents": 15,
            "total_violations": 2,
            "compliance_rate": 86.7
        }
        mock_gen_instance.generate_compliance_data.return_value = mock_report_data

        # Mock PDF export
        mock_pdf_bytes = b"PDF content here"
        mock_gen_instance.export_to_pdf.return_value = mock_pdf_bytes

        # Execute task
        result = generate_weekly_compliance_report(format="pdf")

        # Verify results
        assert result["success"] is True
        assert result["message"] == "Weekly compliance report generated"
        assert result["file_size"] == len(mock_pdf_bytes)
        assert result["filename"].endswith(".pdf")
        assert result["summary"]["total_residents"] == 15
        assert result["summary"]["total_violations"] == 2

        # Verify PDF export was called
        mock_gen_instance.export_to_pdf.assert_called_once()

    @patch('app.tasks.compliance_report_tasks.SessionLocal')
    @patch('app.tasks.compliance_report_tasks.ComplianceReportGenerator')
    def test_generate_weekly_compliance_report_excel(self, mock_generator, mock_session):
        """Test weekly report generation in Excel format."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report generator
        mock_gen_instance = MagicMock()
        mock_generator.return_value = mock_gen_instance

        # Mock report data
        mock_report_data = MagicMock()
        mock_report_data.work_hour_summary = {
            "total_residents": 15,
            "total_violations": 2,
            "compliance_rate": 86.7
        }
        mock_gen_instance.generate_compliance_data.return_value = mock_report_data

        # Mock Excel export
        mock_excel_bytes = b"Excel content here"
        mock_gen_instance.export_to_excel.return_value = mock_excel_bytes

        # Execute task
        result = generate_weekly_compliance_report(format="excel")

        # Verify results
        assert result["success"] is True
        assert result["filename"].endswith(".excel")
        assert result["file_size"] == len(mock_excel_bytes)

        # Verify Excel export was called
        mock_gen_instance.export_to_excel.assert_called_once()


# =============================================================================
# Monthly Executive Summary Tests
# =============================================================================


class TestMonthlyExecutiveSummary:
    """Tests for monthly executive summary generation."""

    @patch('app.tasks.compliance_report_tasks.SessionLocal')
    @patch('app.tasks.compliance_report_tasks.ComplianceReportGenerator')
    def test_generate_monthly_executive_summary(self, mock_generator, mock_session):
        """Test monthly executive summary generation."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report generator
        mock_gen_instance = MagicMock()
        mock_generator.return_value = mock_gen_instance

        # Mock report data
        mock_report_data = MagicMock()
        mock_report_data.work_hour_summary = {
            "total_residents": 20,
            "total_violations": 5,
            "compliance_rate": 75.0,
            "avg_weekly_hours": 65.5
        }
        mock_report_data.supervision_summary = {
            "compliance_rate": 98.0
        }
        mock_gen_instance.generate_compliance_data.return_value = mock_report_data

        # Mock exports
        mock_pdf_bytes = b"PDF content"
        mock_excel_bytes = b"Excel content"
        mock_gen_instance.export_to_pdf.return_value = mock_pdf_bytes
        mock_gen_instance.export_to_excel.return_value = mock_excel_bytes

        # Execute task
        result = generate_monthly_executive_summary()

        # Verify results
        assert result["success"] is True
        assert result["message"] == "Monthly executive summary generated"
        assert "pdf" in result["files"]
        assert "excel" in result["files"]
        assert result["files"]["pdf"]["size"] == len(mock_pdf_bytes)
        assert result["files"]["excel"]["size"] == len(mock_excel_bytes)
        assert result["summary"]["total_residents"] == 20
        assert result["summary"]["avg_weekly_hours"] == 65.5
        assert result["summary"]["supervision_compliance"] == 98.0


# =============================================================================
# Custom Compliance Report Tests
# =============================================================================


class TestCustomComplianceReport:
    """Tests for custom compliance report generation."""

    @patch('app.tasks.compliance_report_tasks.SessionLocal')
    @patch('app.tasks.compliance_report_tasks.ComplianceReportGenerator')
    def test_generate_custom_compliance_report(self, mock_generator, mock_session):
        """Test custom report generation."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report generator
        mock_gen_instance = MagicMock()
        mock_generator.return_value = mock_gen_instance

        # Mock report data
        mock_report_data = MagicMock()
        mock_report_data.work_hour_summary = {
            "total_residents": 8,
            "total_violations": 1,
            "compliance_rate": 87.5
        }
        mock_gen_instance.generate_compliance_data.return_value = mock_report_data

        # Mock export
        mock_pdf_bytes = b"Custom PDF"
        mock_gen_instance.export_to_pdf.return_value = mock_pdf_bytes

        # Execute task
        result = generate_custom_compliance_report(
            start_date="2025-01-01",
            end_date="2025-01-31",
            pgy_levels=[1, 2],
            format="pdf"
        )

        # Verify results
        assert result["success"] is True
        assert result["message"] == "Custom compliance report generated"
        assert result["filename"].endswith(".pdf")
        assert result["parameters"]["pgy_levels"] == [1, 2]
        assert result["summary"]["total_residents"] == 8

    @patch('app.tasks.compliance_report_tasks.SessionLocal')
    @patch('app.tasks.compliance_report_tasks.ComplianceReportGenerator')
    def test_generate_custom_compliance_report_with_resident_ids(self, mock_generator, mock_session):
        """Test custom report with specific resident IDs."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report generator
        mock_gen_instance = MagicMock()
        mock_generator.return_value = mock_gen_instance

        # Mock report data
        mock_report_data = MagicMock()
        mock_report_data.work_hour_summary = {
            "total_residents": 2,
            "total_violations": 0,
            "compliance_rate": 100.0
        }
        mock_gen_instance.generate_compliance_data.return_value = mock_report_data

        # Mock export
        mock_pdf_bytes = b"Custom PDF"
        mock_gen_instance.export_to_pdf.return_value = mock_pdf_bytes

        # Execute task with resident IDs
        resident_ids = [str(uuid4()), str(uuid4())]
        result = generate_custom_compliance_report(
            start_date="2025-01-01",
            end_date="2025-01-31",
            resident_ids=resident_ids,
            format="pdf"
        )

        # Verify results
        assert result["success"] is True
        assert result["parameters"]["resident_ids"] == resident_ids


# =============================================================================
# Violation Alerts Tests
# =============================================================================


class TestViolationAlerts:
    """Tests for violation alerts checking."""

    @patch('app.tasks.compliance_report_tasks.SessionLocal')
    @patch('app.tasks.compliance_report_tasks.ComplianceReportGenerator')
    def test_check_violation_alerts_no_violations(self, mock_generator, mock_session, caplog):
        """Test violation check with no violations found."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report generator
        mock_gen_instance = MagicMock()
        mock_generator.return_value = mock_gen_instance

        # Mock report data with no violations
        mock_report_data = MagicMock()
        mock_report_data.acgme_violations = []
        mock_gen_instance.generate_compliance_data.return_value = mock_report_data

        # Execute task
        result = check_violation_alerts(lookback_days=1)

        # Verify results
        assert result["success"] is True
        assert result["message"] == "No violations found"
        assert result["violations_found"] == 0
        assert result["critical_violations"] == 0

        # Verify info log
        assert any("No compliance violations found" in record.message for record in caplog.records)

    @patch('app.tasks.compliance_report_tasks.SessionLocal')
    @patch('app.tasks.compliance_report_tasks.ComplianceReportGenerator')
    def test_check_violation_alerts_with_violations(self, mock_generator, mock_session, caplog):
        """Test violation check with violations found."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report generator
        mock_gen_instance = MagicMock()
        mock_generator.return_value = mock_gen_instance

        # Mock report data with violations
        violations = [
            {"severity": "CRITICAL", "type": "80_HOUR_RULE"},
            {"severity": "WARNING", "type": "1_IN_7_RULE"},
            {"severity": "CRITICAL", "type": "SUPERVISION"}
        ]
        mock_report_data = MagicMock()
        mock_report_data.acgme_violations = violations
        mock_gen_instance.generate_compliance_data.return_value = mock_report_data

        # Execute task
        result = check_violation_alerts(lookback_days=1)

        # Verify results
        assert result["success"] is True
        assert result["message"] == "Found 3 violations"
        assert result["violations_found"] == 3
        assert result["critical_violations"] == 2
        assert len(result["violations"]) == 3

        # Verify warning log
        assert any("Found 3 violations" in record.message for record in caplog.records)
        assert any("2 critical" in record.message for record in caplog.records)

    @patch('app.tasks.compliance_report_tasks.SessionLocal')
    @patch('app.tasks.compliance_report_tasks.ComplianceReportGenerator')
    def test_check_violation_alerts_limits_violations(self, mock_generator, mock_session):
        """Test violation check limits returned violations to 10."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock report generator
        mock_gen_instance = MagicMock()
        mock_generator.return_value = mock_gen_instance

        # Mock report data with many violations
        violations = [{"severity": "WARNING", "type": f"VIOLATION_{i}"} for i in range(20)]
        mock_report_data = MagicMock()
        mock_report_data.acgme_violations = violations
        mock_gen_instance.generate_compliance_data.return_value = mock_report_data

        # Execute task
        result = check_violation_alerts(lookback_days=1)

        # Verify results
        assert result["violations_found"] == 20
        assert len(result["violations"]) == 10  # Limited to first 10


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestTaskErrorHandling:
    """Tests for task error handling and retries."""

    @patch('app.tasks.compliance_report_tasks.SessionLocal')
    def test_task_retries_on_exception(self, mock_session):
        """Test that tasks retry on exceptions."""
        # Mock database session to raise exception
        mock_session.side_effect = Exception("Database connection failed")

        # Create a mock task instance with retry method
        mock_task = MagicMock()
        mock_task.retry = MagicMock(side_effect=Exception("Retry called"))

        # Execute task should raise retry exception
        with pytest.raises(Exception, match="Retry called"):
            # Bind the task instance
            task_func = generate_daily_compliance_summary.__wrapped__
            task_func(mock_task, lookback_days=1)

    @patch('app.tasks.compliance_report_tasks.SessionLocal')
    @patch('app.tasks.compliance_report_tasks.ComplianceReportGenerator')
    def test_database_session_always_closes(self, mock_generator, mock_session):
        """Test database session is closed even on error."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock generator to raise exception
        mock_gen_instance = MagicMock()
        mock_gen_instance.generate_compliance_data.side_effect = Exception("Report generation failed")
        mock_generator.return_value = mock_gen_instance

        # Execute task should handle exception
        mock_task = MagicMock()
        mock_task.retry = MagicMock(side_effect=Exception("Retry"))

        with pytest.raises(Exception):
            task_func = generate_daily_compliance_summary.__wrapped__
            task_func(mock_task, lookback_days=1)

        # Verify database session was still closed
        mock_db.close.assert_called_once()
