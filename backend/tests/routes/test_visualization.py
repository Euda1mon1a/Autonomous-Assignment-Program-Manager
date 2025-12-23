"""Tests for visualization API routes.

Tests the heatmap visualization functionality including:
- Unified schedule heatmaps
- Coverage analysis heatmaps
- Workload distribution heatmaps
- Image export functionality
"""

import io
from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


class TestVisualizationRoutes:
    """Test suite for visualization API endpoints."""

    # ========================================================================
    # Authentication Tests
    # ========================================================================

    def test_heatmap_requires_auth(self, client: TestClient):
        """Test that heatmap requires authentication."""
        response = client.get(
            "/api/visualization/heatmap?start_date=2025-01-01&end_date=2025-01-31"
        )
        assert response.status_code == 401

    def test_unified_heatmap_requires_auth(self, client: TestClient):
        """Test that unified heatmap POST requires authentication."""
        response = client.post(
            "/api/visualization/heatmap/unified",
            json={
                "time_range": {"range_type": "month", "value": "2025-01"},
                "group_by": "person",
            },
        )
        assert response.status_code == 401

    def test_heatmap_image_requires_auth(self, client: TestClient):
        """Test that heatmap image requires authentication."""
        response = client.get(
            "/api/visualization/heatmap/image?start_date=2025-01-01&end_date=2025-01-31"
        )
        assert response.status_code == 401

    def test_coverage_requires_auth(self, client: TestClient):
        """Test that coverage heatmap requires authentication."""
        response = client.get(
            "/api/visualization/coverage?start_date=2025-01-01&end_date=2025-01-31"
        )
        assert response.status_code == 401

    def test_workload_requires_auth(self, client: TestClient):
        """Test that workload heatmap requires authentication."""
        response = client.get(
            f"/api/visualization/workload?person_ids={uuid4()}&start_date=2025-01-01&end_date=2025-01-31"
        )
        assert response.status_code == 401

    def test_export_requires_auth(self, client: TestClient):
        """Test that export requires authentication."""
        response = client.post(
            "/api/visualization/export",
            json={
                "heatmap_type": "unified",
                "format": "png",
                "request_params": {
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-31",
                },
            },
        )
        assert response.status_code == 401

    # ========================================================================
    # Unified Heatmap Tests (GET)
    # ========================================================================

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful heatmap generation."""
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=[[1, 2, 3], [4, 5, 6]],
            x_labels=["2025-01-01", "2025-01-02", "2025-01-03"],
            y_labels=["Person 1", "Person 2"],
            title="Schedule Heatmap",
            color_scale="RdYlGn",
            metadata={"total_assignments": 100},
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/visualization/heatmap?start_date=2025-01-01&end_date=2025-01-31",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "x_labels" in data
        assert "y_labels" in data

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_with_filters(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap with person and rotation filters."""
        person_id = uuid4()
        rotation_id = uuid4()
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=[[1, 2]], x_labels=["2025-01-01"], y_labels=["Person"], title="Filtered"
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            f"/api/visualization/heatmap?start_date=2025-01-01&end_date=2025-01-31"
            f"&person_ids={person_id}&rotation_ids={rotation_id}&include_fmit=false&group_by=rotation",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_heatmap_invalid_group_by(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap with invalid group_by parameter."""
        response = client.get(
            "/api/visualization/heatmap?start_date=2025-01-01&end_date=2025-01-31&group_by=invalid",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "group_by" in response.json()["detail"]

    def test_heatmap_invalid_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap with start_date after end_date."""
        response = client.get(
            "/api/visualization/heatmap?start_date=2025-01-31&end_date=2025-01-01",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "start_date" in response.json()["detail"]

    # ========================================================================
    # Unified Heatmap Tests (POST with time range)
    # ========================================================================

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_unified_heatmap_with_time_range(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test unified heatmap with time range specification."""
        mock_service = MagicMock()
        mock_service.calculate_date_range.return_value = (
            date(2025, 1, 1),
            date(2025, 1, 31),
        )
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=[[1, 2, 3]],
            x_labels=["2025-01-01"],
            y_labels=["Person"],
            title="Monthly Heatmap",
            metadata=None,
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/visualization/heatmap/unified",
            headers=auth_headers,
            json={
                "time_range": {"range_type": "month", "value": "2025-01"},
                "group_by": "person",
                "include_fmit": True,
            },
        )
        assert response.status_code == 200

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_unified_heatmap_invalid_time_range(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test unified heatmap with invalid time range."""
        mock_service = MagicMock()
        mock_service.calculate_date_range.side_effect = ValueError("Invalid range")
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/visualization/heatmap/unified",
            headers=auth_headers,
            json={
                "time_range": {"range_type": "invalid", "value": "bad"},
                "group_by": "person",
            },
        )
        assert response.status_code == 400

    # ========================================================================
    # Heatmap Image Export Tests
    # ========================================================================

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_image_png(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap PNG image export."""
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=[[1, 2]], title="Test Heatmap"
        )
        mock_service.export_heatmap_image.return_value = b"\x89PNG fake image data"
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/visualization/heatmap/image?start_date=2025-01-01&end_date=2025-01-31&format=png",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_image_pdf(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap PDF image export."""
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=[[1, 2]], title="Test Heatmap"
        )
        mock_service.export_heatmap_image.return_value = b"%PDF-1.4 fake pdf"
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/visualization/heatmap/image?start_date=2025-01-01&end_date=2025-01-31&format=pdf",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_image_svg(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap SVG image export."""
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=[[1, 2]], title="Test Heatmap"
        )
        mock_service.export_heatmap_image.return_value = b"<svg>fake svg</svg>"
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/visualization/heatmap/image?start_date=2025-01-01&end_date=2025-01-31&format=svg",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"

    def test_heatmap_image_invalid_format(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap image with invalid format."""
        response = client.get(
            "/api/visualization/heatmap/image?start_date=2025-01-01&end_date=2025-01-31&format=gif",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "format" in response.json()["detail"]

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_image_export_error(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap image handles export errors."""
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(data=[[1, 2]], title="Test")
        mock_service.export_heatmap_image.side_effect = Exception("Export failed")
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/visualization/heatmap/image?start_date=2025-01-01&end_date=2025-01-31",
            headers=auth_headers,
        )
        assert response.status_code == 500

    # ========================================================================
    # Coverage Heatmap Tests
    # ========================================================================

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_coverage_heatmap_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful coverage heatmap generation."""
        mock_service = MagicMock()
        mock_service.generate_coverage_heatmap.return_value = MagicMock(
            data=[[3, 2, 4]],
            x_labels=["2025-01-01", "2025-01-02", "2025-01-03"],
            y_labels=["Cardiology", "Pulmonology"],
            title="Coverage Heatmap",
            gaps=[{"date": "2025-01-02", "rotation": "Pulmonology", "count": 1}],
            summary={"total_gaps": 1, "coverage_rate": 0.95},
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/visualization/coverage?start_date=2025-01-01&end_date=2025-01-31",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_coverage_heatmap_invalid_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test coverage heatmap with invalid date range."""
        response = client.get(
            "/api/visualization/coverage?start_date=2025-01-31&end_date=2025-01-01",
            headers=auth_headers,
        )
        assert response.status_code == 400

    # ========================================================================
    # Workload Heatmap Tests
    # ========================================================================

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_workload_heatmap_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful workload heatmap generation."""
        person_id = uuid4()
        mock_service = MagicMock()
        mock_service.generate_person_workload_heatmap.return_value = MagicMock(
            data=[[8, 10, 6]],
            x_labels=["2025-01-01", "2025-01-02", "2025-01-03"],
            y_labels=["Dr. Smith"],
            title="Workload Heatmap",
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            f"/api/visualization/workload?person_ids={person_id}&start_date=2025-01-01&end_date=2025-01-31",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_workload_heatmap_multiple_persons(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test workload heatmap for multiple persons."""
        person_id1 = uuid4()
        person_id2 = uuid4()
        mock_service = MagicMock()
        mock_service.generate_person_workload_heatmap.return_value = MagicMock(
            data=[[8, 10], [6, 9]],
            x_labels=["2025-01-01", "2025-01-02"],
            y_labels=["Dr. Smith", "Dr. Jones"],
            title="Workload Heatmap",
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            f"/api/visualization/workload?person_ids={person_id1}&person_ids={person_id2}"
            f"&start_date=2025-01-01&end_date=2025-01-31&include_weekends=true",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_workload_heatmap_invalid_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test workload heatmap with invalid date range."""
        person_id = uuid4()
        response = client.get(
            f"/api/visualization/workload?person_ids={person_id}&start_date=2025-01-31&end_date=2025-01-01",
            headers=auth_headers,
        )
        assert response.status_code == 400

    # ========================================================================
    # Export Endpoint Tests
    # ========================================================================

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_export_unified_heatmap(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test exporting unified heatmap."""
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=[[1, 2]], title="Unified Heatmap"
        )
        mock_service.export_heatmap_image.return_value = b"\x89PNG image data"
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/visualization/export",
            headers=auth_headers,
            json={
                "heatmap_type": "unified",
                "format": "png",
                "width": 1200,
                "height": 800,
                "request_params": {
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-31",
                    "group_by": "person",
                },
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_export_coverage_heatmap(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test exporting coverage heatmap."""
        mock_service = MagicMock()
        mock_service.generate_coverage_heatmap.return_value = MagicMock(
            data=[[3, 2]], title="Coverage Heatmap"
        )
        mock_service.export_heatmap_image.return_value = b"%PDF-1.4 pdf data"
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/visualization/export",
            headers=auth_headers,
            json={
                "heatmap_type": "coverage",
                "format": "pdf",
                "request_params": {
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-31",
                },
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_export_workload_heatmap(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test exporting workload heatmap."""
        mock_service = MagicMock()
        mock_service.generate_person_workload_heatmap.return_value = MagicMock(
            data=[[8, 10]], title="Workload Heatmap"
        )
        mock_service.export_heatmap_image.return_value = b"<svg>svg data</svg>"
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/visualization/export",
            headers=auth_headers,
            json={
                "heatmap_type": "workload",
                "format": "svg",
                "request_params": {
                    "person_ids": [str(uuid4())],
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-31",
                },
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"

    def test_export_invalid_format(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test export with invalid format."""
        response = client.post(
            "/api/visualization/export",
            headers=auth_headers,
            json={
                "heatmap_type": "unified",
                "format": "jpg",
                "request_params": {
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-31",
                },
            },
        )
        assert response.status_code == 400
        assert "format" in response.json()["detail"]

    def test_export_invalid_heatmap_type(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test export with invalid heatmap type."""
        response = client.post(
            "/api/visualization/export",
            headers=auth_headers,
            json={
                "heatmap_type": "custom",
                "format": "png",
                "request_params": {},
            },
        )
        assert response.status_code == 400
        assert "heatmap_type" in response.json()["detail"]
