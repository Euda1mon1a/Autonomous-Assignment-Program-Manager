"""Tests for heatmap group_by parameter validation and daily/weekly grouping.

Tests the new 'daily' and 'weekly' group_by options for heatmap generation.
"""

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


class TestHeatmapGroupBy:
    """Test suite for heatmap group_by parameter validation."""

    # ========================================================================
    # Valid group_by Values Tests
    # ========================================================================

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_group_by_person(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap with group_by='person'."""
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=MagicMock(
                x_labels=["2025-01-01", "2025-01-02"],
                y_labels=["Person1", "Person2"],
                z_values=[[1, 2], [3, 4]],
                color_scale="Viridis",
            ),
            title="Person Schedule Heatmap",
            metadata={"grouping_type": "person"},
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/visualization/heatmap?start_date=2025-01-01&end_date=2025-01-02&group_by=person",
            headers=auth_headers,
        )
        assert response.status_code == 200
        mock_service.generate_unified_heatmap.assert_called_once()
        call_kwargs = mock_service.generate_unified_heatmap.call_args[1]
        assert call_kwargs["group_by"] == "person"

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_group_by_rotation(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap with group_by='rotation'."""
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=MagicMock(
                x_labels=["2025-01-01", "2025-01-02"],
                y_labels=["Clinic", "Inpatient"],
                z_values=[[2, 1], [1, 3]],
                color_scale="Viridis",
            ),
            title="Rotation Schedule Heatmap",
            metadata={"grouping_type": "rotation"},
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/visualization/heatmap?start_date=2025-01-01&end_date=2025-01-02&group_by=rotation",
            headers=auth_headers,
        )
        assert response.status_code == 200
        mock_service.generate_unified_heatmap.assert_called_once()
        call_kwargs = mock_service.generate_unified_heatmap.call_args[1]
        assert call_kwargs["group_by"] == "rotation"

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_group_by_daily(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap with group_by='daily' (new feature)."""
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=MagicMock(
                x_labels=["2025-01-01", "2025-01-02", "2025-01-03"],
                y_labels=["Total Assignments"],
                z_values=[[5, 6, 4]],
                color_scale="Viridis",
            ),
            title="Daily Assignment Heatmap",
            metadata={"grouping_type": "daily", "date_range_days": 3},
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/visualization/heatmap?start_date=2025-01-01&end_date=2025-01-03&group_by=daily",
            headers=auth_headers,
        )
        assert response.status_code == 200
        mock_service.generate_unified_heatmap.assert_called_once()
        call_kwargs = mock_service.generate_unified_heatmap.call_args[1]
        assert call_kwargs["group_by"] == "daily"

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_group_by_weekly(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap with group_by='weekly' (new feature)."""
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=MagicMock(
                x_labels=["2025-01-01", "2025-01-08"],
                y_labels=["Total Assignments"],
                z_values=[[15, 12]],
                color_scale="Viridis",
            ),
            title="Weekly Assignment Heatmap",
            metadata={"grouping_type": "weekly", "weeks_count": 2},
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/visualization/heatmap?start_date=2025-01-01&end_date=2025-01-14&group_by=weekly",
            headers=auth_headers,
        )
        assert response.status_code == 200
        mock_service.generate_unified_heatmap.assert_called_once()
        call_kwargs = mock_service.generate_unified_heatmap.call_args[1]
        assert call_kwargs["group_by"] == "weekly"

    # ========================================================================
    # Case Insensitivity Tests
    # ========================================================================

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_group_by_daily_uppercase(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap with group_by='Daily' (uppercase) is normalized."""
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=MagicMock(
                x_labels=["2025-01-01"],
                y_labels=["Total Assignments"],
                z_values=[[5]],
                color_scale="Viridis",
            ),
            title="Daily Assignment Heatmap",
            metadata={"grouping_type": "daily"},
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/visualization/heatmap?start_date=2025-01-01&end_date=2025-01-01&group_by=Daily",
            headers=auth_headers,
        )
        assert response.status_code == 200
        # Verify it was normalized to lowercase
        call_kwargs = mock_service.generate_unified_heatmap.call_args[1]
        assert call_kwargs["group_by"] == "daily"

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_group_by_weekly_uppercase(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap with group_by='Weekly' (uppercase) is normalized."""
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=MagicMock(
                x_labels=["2025-01-01"],
                y_labels=["Total Assignments"],
                z_values=[[15]],
                color_scale="Viridis",
            ),
            title="Weekly Assignment Heatmap",
            metadata={"grouping_type": "weekly"},
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/visualization/heatmap?start_date=2025-01-01&end_date=2025-01-07&group_by=Weekly",
            headers=auth_headers,
        )
        assert response.status_code == 200
        # Verify it was normalized to lowercase
        call_kwargs = mock_service.generate_unified_heatmap.call_args[1]
        assert call_kwargs["group_by"] == "weekly"

    # ========================================================================
    # Invalid group_by Values Tests
    # ========================================================================

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
        detail = response.json()["detail"]
        assert "group_by" in detail
        assert "person" in detail
        assert "rotation" in detail
        assert "daily" in detail
        assert "weekly" in detail

    def test_heatmap_empty_group_by(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap with empty group_by parameter."""
        response = client.get(
            "/api/visualization/heatmap?start_date=2025-01-01&end_date=2025-01-31&group_by=",
            headers=auth_headers,
        )
        assert response.status_code == 400

    # ========================================================================
    # POST Endpoint Tests
    # ========================================================================

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_unified_heatmap_post_group_by_daily(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test POST unified heatmap with group_by='daily'."""
        mock_service = MagicMock()
        mock_service.calculate_date_range.return_value = (
            date(2025, 1, 1),
            date(2025, 1, 7),
        )
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=MagicMock(
                x_labels=["2025-01-01", "2025-01-02"],
                y_labels=["Total Assignments"],
                z_values=[[5, 6]],
                color_scale="Viridis",
            ),
            title="Daily Assignment Heatmap",
            metadata={"grouping_type": "daily"},
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/visualization/heatmap/unified",
            headers=auth_headers,
            json={
                "time_range": {"range_type": "week", "reference_date": "2025-01-01"},
                "group_by": "daily",
            },
        )
        assert response.status_code == 200
        call_kwargs = mock_service.generate_unified_heatmap.call_args[1]
        assert call_kwargs["group_by"] == "daily"

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_unified_heatmap_post_group_by_weekly(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test POST unified heatmap with group_by='weekly'."""
        mock_service = MagicMock()
        mock_service.calculate_date_range.return_value = (
            date(2025, 1, 1),
            date(2025, 3, 31),
        )
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=MagicMock(
                x_labels=["2025-01-01", "2025-01-08"],
                y_labels=["Total Assignments"],
                z_values=[[15, 14]],
                color_scale="Viridis",
            ),
            title="Weekly Assignment Heatmap",
            metadata={"grouping_type": "weekly"},
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/visualization/heatmap/unified",
            headers=auth_headers,
            json={
                "time_range": {"range_type": "quarter", "reference_date": "2025-01-15"},
                "group_by": "weekly",
            },
        )
        assert response.status_code == 200
        call_kwargs = mock_service.generate_unified_heatmap.call_args[1]
        assert call_kwargs["group_by"] == "weekly"

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_unified_heatmap_post_invalid_group_by(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test POST unified heatmap with invalid group_by."""
        response = client.post(
            "/api/visualization/heatmap/unified",
            headers=auth_headers,
            json={
                "time_range": {"range_type": "month", "reference_date": "2025-01-01"},
                "group_by": "invalid_value",
            },
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "group_by" in detail

    # ========================================================================
    # Image Export Tests
    # ========================================================================

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_image_group_by_daily(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap image export with group_by='daily'."""
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=MagicMock(
                x_labels=["2025-01-01"],
                y_labels=["Total Assignments"],
                z_values=[[5]],
                color_scale="Viridis",
            ),
            title="Daily Assignment Heatmap",
        )
        mock_service.export_heatmap_image.return_value = b"PNG_DATA"
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/visualization/heatmap/image?start_date=2025-01-01&end_date=2025-01-01&group_by=daily",
            headers=auth_headers,
        )
        assert response.status_code == 200
        call_kwargs = mock_service.generate_unified_heatmap.call_args[1]
        assert call_kwargs["group_by"] == "daily"

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_image_group_by_weekly(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap image export with group_by='weekly'."""
        mock_service = MagicMock()
        mock_service.generate_unified_heatmap.return_value = MagicMock(
            data=MagicMock(
                x_labels=["2025-01-01"],
                y_labels=["Total Assignments"],
                z_values=[[15]],
                color_scale="Viridis",
            ),
            title="Weekly Assignment Heatmap",
        )
        mock_service.export_heatmap_image.return_value = b"PNG_DATA"
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/visualization/heatmap/image?start_date=2025-01-01&end_date=2025-01-07&group_by=weekly&format=png",
            headers=auth_headers,
        )
        assert response.status_code == 200
        call_kwargs = mock_service.generate_unified_heatmap.call_args[1]
        assert call_kwargs["group_by"] == "weekly"

    @patch("app.api.routes.visualization.CachedHeatmapService")
    def test_heatmap_image_invalid_group_by(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap image with invalid group_by."""
        response = client.get(
            "/api/visualization/heatmap/image?start_date=2025-01-01&end_date=2025-01-07&group_by=bad_value",
            headers=auth_headers,
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "group_by" in detail
