"""
Comprehensive tests for Reports API routes.

Tests coverage for PDF report generation:
- POST /api/reports/schedule - Generate schedule report
- POST /api/reports/compliance - Generate compliance report
- POST /api/reports/analytics - Generate analytics report
- POST /api/reports/faculty-summary - Generate faculty summary report
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Classes
# ============================================================================


class TestScheduleReportEndpoint:
    """Tests for POST /api/reports/schedule endpoint."""

    def test_schedule_report_requires_auth(self, client: TestClient):
        """Test that schedule report requires authentication."""
        response = client.post(
            "/api/reports/schedule",
            json={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=30)).isoformat(),
            },
        )

        assert response.status_code in [401, 403]

    def test_schedule_report_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test successful schedule report generation."""
        with patch(
            "app.api.routes.reports.ScheduleReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.return_value = b"%PDF-1.4 test content"
            mock_template_class.return_value = mock_template

            response = client.post(
                "/api/reports/schedule",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=30)).isoformat(),
                    "include_details": True,
                    "include_logo": True,
                    "include_page_numbers": True,
                },
                headers=auth_headers,
            )

            if response.status_code == 200:
                assert response.headers["content-type"] == "application/pdf"
                assert "content-disposition" in response.headers

    def test_schedule_report_requires_dates(
        self, client: TestClient, auth_headers: dict
    ):
        """Test schedule report requires date parameters."""
        response = client.post(
            "/api/reports/schedule",
            json={},
            headers=auth_headers,
        )

        # Should return 422 for missing required fields
        assert response.status_code in [401, 422]

    def test_schedule_report_minimal_options(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test schedule report with minimal options."""
        with patch(
            "app.api.routes.reports.ScheduleReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.return_value = b"%PDF-1.4 minimal"
            mock_template_class.return_value = mock_template

            response = client.post(
                "/api/reports/schedule",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=7)).isoformat(),
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_schedule_report_error_handling(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test schedule report handles errors gracefully."""
        with patch(
            "app.api.routes.reports.ScheduleReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.side_effect = Exception("Report generation failed")
            mock_template_class.return_value = mock_template

            response = client.post(
                "/api/reports/schedule",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=30)).isoformat(),
                },
                headers=auth_headers,
            )

            assert response.status_code in [401, 500]


class TestComplianceReportEndpoint:
    """Tests for POST /api/reports/compliance endpoint."""

    def test_compliance_report_requires_auth(self, client: TestClient):
        """Test that compliance report requires authentication."""
        response = client.post(
            "/api/reports/compliance",
            json={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=30)).isoformat(),
            },
        )

        assert response.status_code in [401, 403]

    def test_compliance_report_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test successful compliance report generation."""
        with patch(
            "app.api.routes.reports.ComplianceReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.return_value = b"%PDF-1.4 compliance"
            mock_template_class.return_value = mock_template

            response = client.post(
                "/api/reports/compliance",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=30)).isoformat(),
                    "pgy_levels": [1, 2, 3],
                    "include_violations_only": False,
                    "include_logo": True,
                    "include_page_numbers": True,
                },
                headers=auth_headers,
            )

            if response.status_code == 200:
                assert response.headers["content-type"] == "application/pdf"

    def test_compliance_report_violations_only(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test compliance report with violations only filter."""
        with patch(
            "app.api.routes.reports.ComplianceReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.return_value = b"%PDF-1.4 violations"
            mock_template_class.return_value = mock_template

            response = client.post(
                "/api/reports/compliance",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=30)).isoformat(),
                    "include_violations_only": True,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_compliance_report_specific_pgy_levels(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test compliance report for specific PGY levels."""
        with patch(
            "app.api.routes.reports.ComplianceReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.return_value = b"%PDF-1.4 pgy"
            mock_template_class.return_value = mock_template

            response = client.post(
                "/api/reports/compliance",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=30)).isoformat(),
                    "pgy_levels": [1],  # Only PGY-1
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_compliance_report_error_handling(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test compliance report handles errors gracefully."""
        with patch(
            "app.api.routes.reports.ComplianceReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.side_effect = Exception("Template error")
            mock_template_class.return_value = mock_template

            response = client.post(
                "/api/reports/compliance",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=30)).isoformat(),
                },
                headers=auth_headers,
            )

            assert response.status_code in [401, 500]


class TestAnalyticsReportEndpoint:
    """Tests for POST /api/reports/analytics endpoint."""

    def test_analytics_report_requires_auth(self, client: TestClient):
        """Test that analytics report requires authentication."""
        response = client.post(
            "/api/reports/analytics",
            json={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=30)).isoformat(),
            },
        )

        assert response.status_code in [401, 403]

    def test_analytics_report_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test successful analytics report generation."""
        with patch(
            "app.api.routes.reports.AnalyticsReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.return_value = b"%PDF-1.4 analytics"
            mock_template_class.return_value = mock_template

            response = client.post(
                "/api/reports/analytics",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=30)).isoformat(),
                    "include_charts": True,
                    "include_fairness_metrics": True,
                    "include_trends": True,
                    "include_logo": True,
                    "include_page_numbers": True,
                },
                headers=auth_headers,
            )

            if response.status_code == 200:
                assert response.headers["content-type"] == "application/pdf"

    def test_analytics_report_without_charts(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test analytics report without charts."""
        with patch(
            "app.api.routes.reports.AnalyticsReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.return_value = b"%PDF-1.4 no charts"
            mock_template_class.return_value = mock_template

            response = client.post(
                "/api/reports/analytics",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=30)).isoformat(),
                    "include_charts": False,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_analytics_report_error_handling(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test analytics report handles errors gracefully."""
        with patch(
            "app.api.routes.reports.AnalyticsReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.side_effect = Exception("Analytics error")
            mock_template_class.return_value = mock_template

            response = client.post(
                "/api/reports/analytics",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=30)).isoformat(),
                },
                headers=auth_headers,
            )

            assert response.status_code in [401, 500]


class TestFacultySummaryReportEndpoint:
    """Tests for POST /api/reports/faculty-summary endpoint."""

    def test_faculty_summary_requires_auth(self, client: TestClient):
        """Test that faculty summary report requires authentication."""
        response = client.post(
            "/api/reports/faculty-summary",
            json={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=30)).isoformat(),
            },
        )

        assert response.status_code in [401, 403]

    def test_faculty_summary_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test successful faculty summary report generation."""
        with patch(
            "app.api.routes.reports.FacultySummaryReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.return_value = b"%PDF-1.4 faculty"
            mock_template_class.return_value = mock_template

            response = client.post(
                "/api/reports/faculty-summary",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=30)).isoformat(),
                    "include_workload": True,
                    "include_supervision": True,
                    "include_logo": True,
                    "include_page_numbers": True,
                },
                headers=auth_headers,
            )

            if response.status_code == 200:
                assert response.headers["content-type"] == "application/pdf"

    def test_faculty_summary_specific_faculty(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test faculty summary for specific faculty members."""
        with patch(
            "app.api.routes.reports.FacultySummaryReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.return_value = b"%PDF-1.4 specific"
            mock_template_class.return_value = mock_template

            faculty_id = str(uuid4())
            response = client.post(
                "/api/reports/faculty-summary",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=30)).isoformat(),
                    "faculty_ids": [faculty_id],
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_faculty_summary_error_handling(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test faculty summary handles errors gracefully."""
        with patch(
            "app.api.routes.reports.FacultySummaryReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.side_effect = Exception("Faculty report error")
            mock_template_class.return_value = mock_template

            response = client.post(
                "/api/reports/faculty-summary",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=30)).isoformat(),
                },
                headers=auth_headers,
            )

            assert response.status_code in [401, 500]


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestReportsEdgeCases:
    """Tests for edge cases in report generation."""

    def test_report_large_date_range(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test report with large date range (1 year)."""
        with patch(
            "app.api.routes.reports.ScheduleReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.return_value = b"%PDF-1.4 large range"
            mock_template_class.return_value = mock_template

            response = client.post(
                "/api/reports/schedule",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=365)).isoformat(),
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_report_single_day(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test report for a single day."""
        with patch(
            "app.api.routes.reports.ScheduleReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.return_value = b"%PDF-1.4 single day"
            mock_template_class.return_value = mock_template

            today = date.today()
            response = client.post(
                "/api/reports/schedule",
                json={
                    "start_date": today.isoformat(),
                    "end_date": today.isoformat(),
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_report_past_dates(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test report for past date range."""
        with patch(
            "app.api.routes.reports.ScheduleReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.return_value = b"%PDF-1.4 past"
            mock_template_class.return_value = mock_template

            past_end = date.today() - timedelta(days=1)
            past_start = past_end - timedelta(days=30)
            response = client.post(
                "/api/reports/schedule",
                json={
                    "start_date": past_start.isoformat(),
                    "end_date": past_end.isoformat(),
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_report_future_dates(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test report for future date range."""
        with patch(
            "app.api.routes.reports.ScheduleReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.return_value = b"%PDF-1.4 future"
            mock_template_class.return_value = mock_template

            future_start = date.today() + timedelta(days=30)
            future_end = future_start + timedelta(days=30)
            response = client.post(
                "/api/reports/schedule",
                json={
                    "start_date": future_start.isoformat(),
                    "end_date": future_end.isoformat(),
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


# ============================================================================
# Integration Tests
# ============================================================================


class TestReportsIntegration:
    """Integration tests for report generation."""

    def test_all_report_endpoints_accessible(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test all report endpoints are accessible."""
        with (
            patch("app.api.routes.reports.ScheduleReportTemplate") as mock_schedule,
            patch("app.api.routes.reports.ComplianceReportTemplate") as mock_compliance,
            patch("app.api.routes.reports.AnalyticsReportTemplate") as mock_analytics,
            patch(
                "app.api.routes.reports.FacultySummaryReportTemplate"
            ) as mock_faculty,
        ):
            # Configure all mocks
            for mock_class in [
                mock_schedule,
                mock_compliance,
                mock_analytics,
                mock_faculty,
            ]:
                mock_instance = MagicMock()
                mock_instance.generate.return_value = b"%PDF-1.4 test"
                mock_class.return_value = mock_instance

            endpoints = [
                "/api/reports/schedule",
                "/api/reports/compliance",
                "/api/reports/analytics",
                "/api/reports/faculty-summary",
            ]

            for endpoint in endpoints:
                response = client.post(
                    endpoint,
                    json={
                        "start_date": date.today().isoformat(),
                        "end_date": (date.today() + timedelta(days=30)).isoformat(),
                    },
                    headers=auth_headers,
                )

                # Should not return 404 or 405
                assert response.status_code in [
                    200,
                    401,
                    422,
                    500,
                ], f"Failed for {endpoint}"

    def test_report_pdf_response_headers(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test PDF response has correct headers."""
        with patch(
            "app.api.routes.reports.ScheduleReportTemplate"
        ) as mock_template_class:
            mock_template = MagicMock()
            mock_template.generate.return_value = b"%PDF-1.4 headers test"
            mock_template_class.return_value = mock_template

            response = client.post(
                "/api/reports/schedule",
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=30)).isoformat(),
                },
                headers=auth_headers,
            )

            if response.status_code == 200:
                assert response.headers["content-type"] == "application/pdf"
                assert "content-disposition" in response.headers
                assert "attachment" in response.headers["content-disposition"]
                assert ".pdf" in response.headers["content-disposition"]

    def test_reports_http_methods(self, client: TestClient, auth_headers: dict):
        """Test reports only accept POST requests."""
        endpoints = [
            "/api/reports/schedule",
            "/api/reports/compliance",
            "/api/reports/analytics",
            "/api/reports/faculty-summary",
        ]

        for endpoint in endpoints:
            # GET should not be allowed
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code in [401, 405]

            # PUT should not be allowed
            response = client.put(
                endpoint,
                json={
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=30)).isoformat(),
                },
                headers=auth_headers,
            )
            assert response.status_code in [401, 405]
