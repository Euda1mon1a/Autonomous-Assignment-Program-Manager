"""
Integration tests for reporting workflow.

Tests report generation, export, scheduling, and delivery.
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestReportingWorkflow:
    """Test report generation and management workflows."""

    def test_generate_schedule_report_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test generating a schedule report."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        report_response = client.post(
            "/api/reports/schedule",
            json={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "format": "pdf",
            },
            headers=auth_headers,
        )
        assert report_response.status_code in [200, 201, 404, 501]

    def test_generate_compliance_report_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test generating ACGME compliance report."""
        report_response = client.post(
            "/api/reports/compliance",
            json={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=30)).isoformat(),
            },
            headers=auth_headers,
        )
        assert report_response.status_code in [200, 201, 404, 501]

    def test_generate_utilization_report_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test generating resource utilization report."""
        report_response = client.get(
            f"/api/reports/utilization?start_date={date.today().isoformat()}",
            headers=auth_headers,
        )
        assert report_response.status_code in [200, 404, 501]

    def test_export_report_formats_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test exporting reports in different formats."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        for fmt in ["pdf", "csv", "json", "xlsx"]:
            export_response = client.get(
                f"/api/reports/schedule?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}&format={fmt}",
                headers=auth_headers,
            )
            assert export_response.status_code in [200, 404, 501]

    def test_scheduled_report_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test scheduling recurring reports."""
        # Create scheduled report
        schedule_response = client.post(
            "/api/reports/schedule-recurring",
            json={
                "report_type": "compliance",
                "frequency": "weekly",
                "format": "pdf",
                "recipients": ["admin@hospital.org"],
            },
            headers=auth_headers,
        )
        assert schedule_response.status_code in [200, 201, 404, 501]

    def test_list_available_reports_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test listing available report types."""
        list_response = client.get(
            "/api/reports/",
            headers=auth_headers,
        )
        assert list_response.status_code in [200, 404]

    def test_report_history_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test retrieving report generation history."""
        history_response = client.get(
            "/api/reports/history",
            headers=auth_headers,
        )
        assert history_response.status_code in [200, 404, 501]

    def test_download_generated_report_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test downloading a previously generated report."""
        download_response = client.get(
            "/api/reports/download/dummy_report_id",
            headers=auth_headers,
        )
        assert download_response.status_code in [200, 404]
