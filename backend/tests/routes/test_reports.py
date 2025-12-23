"""Tests for report generation API routes.

Tests the PDF report generation functionality including:
- Schedule reports
- Compliance reports
- Analytics reports
- Faculty summary reports
"""

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


class TestReportRoutes:
    """Test suite for report generation API endpoints."""

    # ========================================================================
    # Authentication Tests
    # ========================================================================

    def test_schedule_report_requires_auth(self, client: TestClient):
        """Test that schedule report requires authentication."""
        response = client.post(
            "/api/reports/schedule",
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 401

    def test_compliance_report_requires_auth(self, client: TestClient):
        """Test that compliance report requires authentication."""
        response = client.post(
            "/api/reports/compliance",
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 401

    def test_analytics_report_requires_auth(self, client: TestClient):
        """Test that analytics report requires authentication."""
        response = client.post(
            "/api/reports/analytics",
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 401

    def test_faculty_summary_report_requires_auth(self, client: TestClient):
        """Test that faculty summary report requires authentication."""
        response = client.post(
            "/api/reports/faculty-summary",
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 401

    # ========================================================================
    # Schedule Report Tests
    # ========================================================================

    @patch("app.api.routes.reports.ScheduleReportTemplate")
    def test_schedule_report_success(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful schedule report generation."""
        mock_template = MagicMock()
        mock_template.generate.return_value = b"%PDF-1.4 fake pdf content"
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/schedule",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "include_details": True,
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers.get("content-disposition", "")

    @patch("app.api.routes.reports.ScheduleReportTemplate")
    def test_schedule_report_with_options(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test schedule report with all options."""
        mock_template = MagicMock()
        mock_template.generate.return_value = b"%PDF-1.4 fake pdf"
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/schedule",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "include_details": True,
                "include_logo": True,
                "include_page_numbers": True,
            },
        )
        assert response.status_code == 200

    @patch("app.api.routes.reports.ScheduleReportTemplate")
    def test_schedule_report_error(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test schedule report handles generation errors."""
        mock_template = MagicMock()
        mock_template.generate.side_effect = Exception("PDF generation failed")
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/schedule",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 500
        assert "Failed to generate" in response.json()["detail"]

    # ========================================================================
    # Compliance Report Tests
    # ========================================================================

    @patch("app.api.routes.reports.ComplianceReportTemplate")
    def test_compliance_report_success(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful compliance report generation."""
        mock_template = MagicMock()
        mock_template.generate.return_value = b"%PDF-1.4 compliance report"
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/compliance",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @patch("app.api.routes.reports.ComplianceReportTemplate")
    def test_compliance_report_with_pgy_filter(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test compliance report with PGY level filter."""
        mock_template = MagicMock()
        mock_template.generate.return_value = b"%PDF-1.4 compliance report"
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/compliance",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "pgy_levels": [1, 2, 3],
                "include_violations_only": True,
            },
        )
        assert response.status_code == 200

    @patch("app.api.routes.reports.ComplianceReportTemplate")
    def test_compliance_report_error(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test compliance report handles generation errors."""
        mock_template = MagicMock()
        mock_template.generate.side_effect = Exception("Data fetch failed")
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/compliance",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 500

    # ========================================================================
    # Analytics Report Tests
    # ========================================================================

    @patch("app.api.routes.reports.AnalyticsReportTemplate")
    def test_analytics_report_success(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful analytics report generation."""
        mock_template = MagicMock()
        mock_template.generate.return_value = b"%PDF-1.4 analytics report"
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/analytics",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @patch("app.api.routes.reports.AnalyticsReportTemplate")
    def test_analytics_report_with_options(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test analytics report with chart and metric options."""
        mock_template = MagicMock()
        mock_template.generate.return_value = b"%PDF-1.4 analytics report"
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/analytics",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "include_charts": True,
                "include_fairness_metrics": True,
                "include_trends": True,
                "include_logo": True,
                "include_page_numbers": True,
            },
        )
        assert response.status_code == 200

    @patch("app.api.routes.reports.AnalyticsReportTemplate")
    def test_analytics_report_error(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test analytics report handles generation errors."""
        mock_template = MagicMock()
        mock_template.generate.side_effect = Exception("Chart generation failed")
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/analytics",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 500

    # ========================================================================
    # Faculty Summary Report Tests
    # ========================================================================

    @patch("app.api.routes.reports.FacultySummaryReportTemplate")
    def test_faculty_summary_report_success(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful faculty summary report generation."""
        mock_template = MagicMock()
        mock_template.generate.return_value = b"%PDF-1.4 faculty summary"
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/faculty-summary",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @patch("app.api.routes.reports.FacultySummaryReportTemplate")
    def test_faculty_summary_report_with_faculty_ids(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test faculty summary report for specific faculty members."""
        mock_template = MagicMock()
        mock_template.generate.return_value = b"%PDF-1.4 faculty summary"
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/faculty-summary",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "faculty_ids": [str(uuid4()), str(uuid4())],
                "include_workload": True,
                "include_supervision": True,
            },
        )
        assert response.status_code == 200

    @patch("app.api.routes.reports.FacultySummaryReportTemplate")
    def test_faculty_summary_report_error(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test faculty summary report handles generation errors."""
        mock_template = MagicMock()
        mock_template.generate.side_effect = Exception("Faculty data not found")
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/faculty-summary",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 500

    # ========================================================================
    # Content Verification Tests
    # ========================================================================

    @patch("app.api.routes.reports.ScheduleReportTemplate")
    def test_report_returns_pdf_content(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that report returns actual PDF content."""
        pdf_content = b"%PDF-1.4 test content with more bytes"
        mock_template = MagicMock()
        mock_template.generate.return_value = pdf_content
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/schedule",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 200
        assert response.content == pdf_content

    @patch("app.api.routes.reports.ScheduleReportTemplate")
    def test_report_content_length_header(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that report includes correct content-length header."""
        pdf_content = b"%PDF-1.4 " + (b"x" * 1000)  # ~1KB PDF
        mock_template = MagicMock()
        mock_template.generate.return_value = pdf_content
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/schedule",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 200
        # Content-Length should be present
        assert "content-length" in response.headers

    @patch("app.api.routes.reports.ScheduleReportTemplate")
    def test_report_filename_in_disposition(
        self,
        mock_template_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that filename is included in content-disposition."""
        mock_template = MagicMock()
        mock_template.generate.return_value = b"%PDF-1.4 test"
        mock_template_class.return_value = mock_template

        response = client.post(
            "/api/reports/schedule",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 200
        disposition = response.headers.get("content-disposition", "")
        assert "schedule_report" in disposition
        assert "2025-01-01" in disposition
        assert "2025-01-31" in disposition
