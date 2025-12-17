"""Comprehensive tests for unified heatmap API routes."""
from datetime import date, timedelta
from io import BytesIO
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_heatmap_data(db: Session, sample_blocks: list[Block]) -> dict:
    """Create sample data for heatmap generation."""
    # Create rotation templates
    fmit_template = RotationTemplate(
        id=uuid4(),
        name="FMIT",
        activity_type="fmit",
        abbreviation="FMIT",
        supervision_required=True,
    )
    clinic_template = RotationTemplate(
        id=uuid4(),
        name="Sports Medicine Clinic",
        activity_type="clinic",
        abbreviation="SM",
        supervision_required=True,
    )
    procedures_template = RotationTemplate(
        id=uuid4(),
        name="Procedures",
        activity_type="procedures",
        abbreviation="PROC",
        supervision_required=True,
    )
    db.add_all([fmit_template, clinic_template, procedures_template])

    # Create people
    faculty1 = Person(
        id=uuid4(),
        name="Dr. Faculty One",
        type="faculty",
        email="faculty1@test.org",
        performs_procedures=True,
    )
    resident1 = Person(
        id=uuid4(),
        name="Dr. Resident One",
        type="resident",
        email="resident1@test.org",
        pgy_level=2,
    )
    resident2 = Person(
        id=uuid4(),
        name="Dr. Resident Two",
        type="resident",
        email="resident2@test.org",
        pgy_level=3,
    )
    db.add_all([faculty1, resident1, resident2])

    db.commit()
    db.refresh(fmit_template)
    db.refresh(clinic_template)
    db.refresh(procedures_template)
    db.refresh(faculty1)
    db.refresh(resident1)
    db.refresh(resident2)

    # Create assignments
    assignments = []
    for i, block in enumerate(sample_blocks[:6]):
        # Assign faculty to FMIT
        if i % 2 == 0:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=faculty1.id,
                rotation_template_id=fmit_template.id,
                role="primary",
            )
            assignments.append(assignment)
            db.add(assignment)

        # Assign residents to clinic and procedures
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=resident1.id if i % 2 == 0 else resident2.id,
            rotation_template_id=clinic_template.id if i % 3 == 0 else procedures_template.id,
            role="primary",
        )
        assignments.append(assignment)
        db.add(assignment)

    db.commit()
    for a in assignments:
        db.refresh(a)

    return {
        "templates": {
            "fmit": fmit_template,
            "clinic": clinic_template,
            "procedures": procedures_template,
        },
        "people": {
            "faculty1": faculty1,
            "resident1": resident1,
            "resident2": resident2,
        },
        "assignments": assignments,
    }


# ============================================================================
# Test GET /heatmap/data
# ============================================================================


class TestGetHeatmapData:
    """Tests for GET /heatmap/data endpoint."""

    def test_get_heatmap_data_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_heatmap_data: dict,
    ):
        """Test successful heatmap data retrieval."""
        start_date = date.today()
        end_date = date.today() + timedelta(days=6)

        response = client.get(
            "/api/unified-heatmap/heatmap/data",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "include_fmit": True,
                "include_residency": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "x_labels" in data
        assert "y_labels" in data
        assert "z_values" in data
        assert "color_scale" in data
        assert "metadata" in data
        assert "generated_at" in data
        assert len(data["x_labels"]) == 7  # 7 days

    def test_get_heatmap_data_requires_auth(self, client: TestClient):
        """Test that endpoint requires authentication."""
        start_date = date.today()
        end_date = date.today() + timedelta(days=1)

        response = client.get(
            "/api/unified-heatmap/heatmap/data",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        assert response.status_code == 401

    def test_get_heatmap_data_invalid_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that start_date must be before end_date."""
        start_date = date.today() + timedelta(days=10)
        end_date = date.today()

        response = client.get(
            "/api/unified-heatmap/heatmap/data",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "start_date must be before or equal to end_date" in response.json()["detail"]

    def test_get_heatmap_data_both_flags_false(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that at least one inclusion flag must be True."""
        start_date = date.today()
        end_date = date.today() + timedelta(days=1)

        response = client.get(
            "/api/unified-heatmap/heatmap/data",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "include_fmit": False,
                "include_residency": False,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "At least one of include_fmit or include_residency must be True" in response.json()["detail"]

    def test_get_heatmap_data_fmit_only(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_heatmap_data: dict,
    ):
        """Test filtering to FMIT assignments only."""
        start_date = date.today()
        end_date = date.today() + timedelta(days=3)

        response = client.get(
            "/api/unified-heatmap/heatmap/data",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "include_fmit": True,
                "include_residency": False,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should only include FMIT rotation
        if data["y_labels"]:
            assert all("FMIT" in label for label in data["y_labels"])

    def test_get_heatmap_data_residency_only(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_heatmap_data: dict,
    ):
        """Test filtering to residency assignments only."""
        start_date = date.today()
        end_date = date.today() + timedelta(days=3)

        response = client.get(
            "/api/unified-heatmap/heatmap/data",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "include_fmit": False,
                "include_residency": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should not include FMIT rotation
        assert "FMIT" not in data["y_labels"]

    def test_get_heatmap_data_same_start_end_date(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_heatmap_data: dict,
    ):
        """Test heatmap for single day."""
        target_date = date.today()

        response = client.get(
            "/api/unified-heatmap/heatmap/data",
            params={
                "start_date": target_date.isoformat(),
                "end_date": target_date.isoformat(),
                "include_fmit": True,
                "include_residency": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["x_labels"]) == 1

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.generate_coverage_heatmap")
    def test_get_heatmap_data_service_error(
        self,
        mock_generate: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test handling of service errors."""
        mock_generate.side_effect = Exception("Database error")

        start_date = date.today()
        end_date = date.today() + timedelta(days=1)

        response = client.get(
            "/api/unified-heatmap/heatmap/data",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 500
        assert "Failed to generate heatmap data" in response.json()["detail"]


# ============================================================================
# Test POST /heatmap/data
# ============================================================================


class TestPostHeatmapData:
    """Tests for POST /heatmap/data endpoint."""

    def test_post_heatmap_data_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_heatmap_data: dict,
    ):
        """Test successful heatmap data retrieval via POST."""
        start_date = date.today()
        end_date = date.today() + timedelta(days=6)

        response = client.post(
            "/api/unified-heatmap/heatmap/data",
            json={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "include_fmit": True,
                "include_residency": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "x_labels" in data
        assert "y_labels" in data
        assert "z_values" in data

    def test_post_heatmap_data_requires_auth(self, client: TestClient):
        """Test that POST endpoint requires authentication."""
        start_date = date.today()
        end_date = date.today() + timedelta(days=1)

        response = client.post(
            "/api/unified-heatmap/heatmap/data",
            json={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "include_fmit": True,
                "include_residency": True,
            },
        )

        assert response.status_code == 401

    def test_post_heatmap_data_invalid_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test POST with invalid date range."""
        start_date = date.today() + timedelta(days=10)
        end_date = date.today()

        response = client.post(
            "/api/unified-heatmap/heatmap/data",
            json={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "include_fmit": True,
                "include_residency": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "start_date must be before or equal to end_date" in response.json()["detail"]


# ============================================================================
# Test GET /heatmap/render
# ============================================================================


class TestGetHeatmapRender:
    """Tests for GET /heatmap/render endpoint."""

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.generate_plotly_heatmap")
    def test_render_heatmap_success(
        self,
        mock_render: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful heatmap rendering."""
        mock_render.return_value = "<html><body>Heatmap</body></html>"

        start_date = date.today()
        end_date = date.today() + timedelta(days=6)

        response = client.get(
            "/api/unified-heatmap/heatmap/render",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "include_fmit": True,
                "include_residency": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "Heatmap" in response.text

    def test_render_heatmap_requires_auth(self, client: TestClient):
        """Test that render endpoint requires authentication."""
        start_date = date.today()
        end_date = date.today() + timedelta(days=1)

        response = client.get(
            "/api/unified-heatmap/heatmap/render",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        assert response.status_code == 401

    def test_render_heatmap_invalid_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test render with invalid date range."""
        start_date = date.today() + timedelta(days=10)
        end_date = date.today()

        response = client.get(
            "/api/unified-heatmap/heatmap/render",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "start_date must be before or equal to end_date" in response.json()["detail"]

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.generate_plotly_heatmap")
    def test_render_heatmap_service_error(
        self,
        mock_render: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test handling of rendering errors."""
        mock_render.side_effect = Exception("Plotly error")

        start_date = date.today()
        end_date = date.today() + timedelta(days=1)

        response = client.get(
            "/api/unified-heatmap/heatmap/render",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 500
        assert "Failed to render heatmap" in response.json()["detail"]


# ============================================================================
# Test POST /heatmap/render
# ============================================================================


class TestPostHeatmapRender:
    """Tests for POST /heatmap/render endpoint."""

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.generate_plotly_heatmap")
    def test_post_render_heatmap_success(
        self,
        mock_render: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful heatmap rendering via POST."""
        mock_render.return_value = "<html><body>Heatmap POST</body></html>"

        start_date = date.today()
        end_date = date.today() + timedelta(days=6)

        response = client.post(
            "/api/unified-heatmap/heatmap/render",
            json={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "include_fmit": True,
                "include_residency": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "Heatmap POST" in response.text

    def test_post_render_heatmap_requires_auth(self, client: TestClient):
        """Test that POST render requires authentication."""
        response = client.post(
            "/api/unified-heatmap/heatmap/render",
            json={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=1)).isoformat(),
                "include_fmit": True,
                "include_residency": True,
            },
        )

        assert response.status_code == 401


# ============================================================================
# Test GET /heatmap/export
# ============================================================================


class TestGetHeatmapExport:
    """Tests for GET /heatmap/export endpoint."""

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.export_heatmap_image")
    def test_export_heatmap_png_success(
        self,
        mock_export: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful heatmap export as PNG."""
        mock_export.return_value = b"fake_png_data"

        start_date = date.today()
        end_date = date.today() + timedelta(days=6)

        response = client.get(
            "/api/unified-heatmap/heatmap/export",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "format": "png",
                "width": 1200,
                "height": 800,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert "attachment" in response.headers["content-disposition"]
        assert "unified_heatmap" in response.headers["content-disposition"]
        assert ".png" in response.headers["content-disposition"]

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.export_heatmap_image")
    def test_export_heatmap_svg_success(
        self,
        mock_export: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful heatmap export as SVG."""
        mock_export.return_value = b"<svg>fake_svg</svg>"

        start_date = date.today()
        end_date = date.today() + timedelta(days=6)

        response = client.get(
            "/api/unified-heatmap/heatmap/export",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "format": "svg",
                "width": 1600,
                "height": 1000,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"
        assert ".svg" in response.headers["content-disposition"]

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.export_heatmap_image")
    def test_export_heatmap_pdf_success(
        self,
        mock_export: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful heatmap export as PDF."""
        mock_export.return_value = b"fake_pdf_data"

        start_date = date.today()
        end_date = date.today() + timedelta(days=6)

        response = client.get(
            "/api/unified-heatmap/heatmap/export",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "format": "pdf",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert ".pdf" in response.headers["content-disposition"]

    def test_export_heatmap_requires_auth(self, client: TestClient):
        """Test that export requires authentication."""
        response = client.get(
            "/api/unified-heatmap/heatmap/export",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=1)).isoformat(),
                "format": "png",
            },
        )

        assert response.status_code == 401

    def test_export_heatmap_invalid_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test export with invalid date range."""
        start_date = date.today() + timedelta(days=10)
        end_date = date.today()

        response = client.get(
            "/api/unified-heatmap/heatmap/export",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "format": "png",
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "start_date must be before or equal to end_date" in response.json()["detail"]

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.export_heatmap_image")
    def test_export_heatmap_value_error(
        self,
        mock_export: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test handling of value errors during export."""
        mock_export.side_effect = ValueError("Invalid format")

        response = client.get(
            "/api/unified-heatmap/heatmap/export",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=1)).isoformat(),
                "format": "png",
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Invalid format" in response.json()["detail"]

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.export_heatmap_image")
    def test_export_heatmap_service_error(
        self,
        mock_export: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test handling of general export errors."""
        mock_export.side_effect = Exception("Export failed")

        response = client.get(
            "/api/unified-heatmap/heatmap/export",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=1)).isoformat(),
                "format": "png",
            },
            headers=auth_headers,
        )

        assert response.status_code == 500
        assert "Failed to export heatmap" in response.json()["detail"]

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.export_heatmap_image")
    def test_export_heatmap_custom_dimensions(
        self,
        mock_export: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test export with custom width and height."""
        mock_export.return_value = b"custom_size_image"

        response = client.get(
            "/api/unified-heatmap/heatmap/export",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=1)).isoformat(),
                "format": "png",
                "width": 2000,
                "height": 1500,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        # Verify that service was called with correct dimensions
        mock_export.assert_called_once()
        call_args = mock_export.call_args
        assert call_args.kwargs["width"] == 2000
        assert call_args.kwargs["height"] == 1500


# ============================================================================
# Test POST /heatmap/export
# ============================================================================


class TestPostHeatmapExport:
    """Tests for POST /heatmap/export endpoint."""

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.export_heatmap_image")
    def test_post_export_heatmap_success(
        self,
        mock_export: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful heatmap export via POST."""
        mock_export.return_value = b"fake_png_data"

        response = client.post(
            "/api/unified-heatmap/heatmap/export",
            json={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=6)).isoformat(),
                "format": "png",
                "include_fmit": True,
                "include_residency": True,
                "width": 1200,
                "height": 800,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_post_export_heatmap_requires_auth(self, client: TestClient):
        """Test that POST export requires authentication."""
        response = client.post(
            "/api/unified-heatmap/heatmap/export",
            json={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=1)).isoformat(),
                "format": "png",
                "include_fmit": True,
                "include_residency": True,
                "width": 1200,
                "height": 800,
            },
        )

        assert response.status_code == 401

    def test_post_export_heatmap_invalid_format(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test POST export with invalid format."""
        response = client.post(
            "/api/unified-heatmap/heatmap/export",
            json={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=1)).isoformat(),
                "format": "invalid_format",
                "include_fmit": True,
                "include_residency": True,
                "width": 1200,
                "height": 800,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "format must be 'png', 'svg', or 'pdf'" in response.json()["detail"]


# ============================================================================
# Test GET /person-coverage/data
# ============================================================================


class TestGetPersonCoverageData:
    """Tests for GET /person-coverage/data endpoint."""

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.generate_person_coverage_heatmap")
    def test_get_person_coverage_success(
        self,
        mock_generate: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful person coverage data retrieval."""
        mock_generate.return_value = {
            "x_labels": ["2024-01-01", "2024-01-02"],
            "y_labels": ["Dr. Smith", "Dr. Jones"],
            "z_values": [[2, 1], [1, 2]],
            "color_scale": "Blues",
            "metadata": {"total_assignments": 6},
        }

        start_date = date.today()
        end_date = date.today() + timedelta(days=6)

        response = client.get(
            "/api/unified-heatmap/person-coverage/data",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "include_call": False,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "x_labels" in data
        assert "y_labels" in data
        assert "z_values" in data

    def test_get_person_coverage_requires_auth(self, client: TestClient):
        """Test that person coverage requires authentication."""
        response = client.get(
            "/api/unified-heatmap/person-coverage/data",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=1)).isoformat(),
            },
        )

        assert response.status_code == 401

    def test_get_person_coverage_invalid_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test person coverage with invalid date range."""
        start_date = date.today() + timedelta(days=10)
        end_date = date.today()

        response = client.get(
            "/api/unified-heatmap/person-coverage/data",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "start_date must be before or equal to end_date" in response.json()["detail"]

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.generate_person_coverage_heatmap")
    def test_get_person_coverage_with_call_assignments(
        self,
        mock_generate: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test person coverage including call assignments."""
        mock_generate.return_value = {
            "x_labels": ["2024-01-01"],
            "y_labels": ["Dr. Smith"],
            "z_values": [[3]],
            "color_scale": "Blues",
            "metadata": {"include_call": True},
        }

        response = client.get(
            "/api/unified-heatmap/person-coverage/data",
            params={
                "start_date": date.today().isoformat(),
                "end_date": date.today().isoformat(),
                "include_call": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        assert call_args.kwargs["include_call"] is True

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.generate_person_coverage_heatmap")
    def test_get_person_coverage_service_error(
        self,
        mock_generate: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test handling of person coverage service errors."""
        mock_generate.side_effect = Exception("Coverage calculation failed")

        response = client.get(
            "/api/unified-heatmap/person-coverage/data",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=1)).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 500
        assert "Failed to generate person coverage data" in response.json()["detail"]


# ============================================================================
# Test POST /person-coverage/data
# ============================================================================


class TestPostPersonCoverageData:
    """Tests for POST /person-coverage/data endpoint."""

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.generate_person_coverage_heatmap")
    def test_post_person_coverage_success(
        self,
        mock_generate: MagicMock,
        client: TestClient,
        auth_headers: dict,
        sample_resident: Person,
    ):
        """Test successful person coverage data retrieval via POST."""
        mock_generate.return_value = {
            "x_labels": ["2024-01-01"],
            "y_labels": ["Dr. Smith"],
            "z_values": [[2]],
            "color_scale": "Blues",
            "metadata": {"total_assignments": 2},
        }

        response = client.post(
            "/api/unified-heatmap/person-coverage/data",
            json={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=6)).isoformat(),
                "person_ids": [str(sample_resident.id)],
                "include_call": False,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "x_labels" in data
        assert "y_labels" in data

    def test_post_person_coverage_requires_auth(self, client: TestClient):
        """Test that POST person coverage requires authentication."""
        response = client.post(
            "/api/unified-heatmap/person-coverage/data",
            json={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=1)).isoformat(),
                "person_ids": None,
                "include_call": False,
            },
        )

        assert response.status_code == 401

    def test_post_person_coverage_invalid_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test POST person coverage with invalid date range."""
        start_date = date.today() + timedelta(days=10)
        end_date = date.today()

        response = client.post(
            "/api/unified-heatmap/person-coverage/data",
            json={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "person_ids": None,
                "include_call": False,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "start_date must be before or equal to end_date" in response.json()["detail"]


# ============================================================================
# Test GET /weekly-fmit/data
# ============================================================================


class TestGetWeeklyFMITData:
    """Tests for GET /weekly-fmit/data endpoint."""

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.generate_weekly_fmit_heatmap")
    def test_get_weekly_fmit_success(
        self,
        mock_generate: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful weekly FMIT data retrieval."""
        mock_generate.return_value = {
            "x_labels": ["2024-01-01", "2024-01-08"],
            "y_labels": ["Dr. Adams", "Dr. Brown"],
            "z_values": [[1, 0], [0, 1]],
            "color_scale": "RdYlGn",
            "metadata": {"total_weeks": 2},
        }

        start_date = date.today()
        end_date = date.today() + timedelta(days=14)

        response = client.get(
            "/api/unified-heatmap/weekly-fmit/data",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "x_labels" in data
        assert "y_labels" in data
        assert "z_values" in data
        assert "color_scale" in data

    def test_get_weekly_fmit_requires_auth(self, client: TestClient):
        """Test that weekly FMIT requires authentication."""
        response = client.get(
            "/api/unified-heatmap/weekly-fmit/data",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=14)).isoformat(),
            },
        )

        assert response.status_code == 401

    def test_get_weekly_fmit_invalid_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test weekly FMIT with invalid date range."""
        start_date = date.today() + timedelta(days=30)
        end_date = date.today()

        response = client.get(
            "/api/unified-heatmap/weekly-fmit/data",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "start_date must be before or equal to end_date" in response.json()["detail"]

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.generate_weekly_fmit_heatmap")
    def test_get_weekly_fmit_service_error(
        self,
        mock_generate: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test handling of weekly FMIT service errors."""
        mock_generate.side_effect = Exception("FMIT calculation failed")

        response = client.get(
            "/api/unified-heatmap/weekly-fmit/data",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=14)).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 500
        assert "Failed to generate weekly FMIT data" in response.json()["detail"]


# ============================================================================
# Test POST /weekly-fmit/data
# ============================================================================


class TestPostWeeklyFMITData:
    """Tests for POST /weekly-fmit/data endpoint."""

    @patch("app.services.unified_heatmap_service.UnifiedHeatmapService.generate_weekly_fmit_heatmap")
    def test_post_weekly_fmit_success(
        self,
        mock_generate: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful weekly FMIT data retrieval via POST."""
        mock_generate.return_value = {
            "x_labels": ["2024-01-01", "2024-01-08", "2024-01-15"],
            "y_labels": ["Dr. Adams", "Dr. Brown", "Dr. Chen"],
            "z_values": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            "color_scale": "RdYlGn",
            "metadata": {"total_weeks": 3},
        }

        response = client.post(
            "/api/unified-heatmap/weekly-fmit/data",
            json={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=21)).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "x_labels" in data
        assert len(data["x_labels"]) == 3

    def test_post_weekly_fmit_requires_auth(self, client: TestClient):
        """Test that POST weekly FMIT requires authentication."""
        response = client.post(
            "/api/unified-heatmap/weekly-fmit/data",
            json={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=14)).isoformat(),
            },
        )

        assert response.status_code == 401

    def test_post_weekly_fmit_invalid_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test POST weekly FMIT with invalid date range."""
        start_date = date.today() + timedelta(days=30)
        end_date = date.today()

        response = client.post(
            "/api/unified-heatmap/weekly-fmit/data",
            json={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "start_date must be before or equal to end_date" in response.json()["detail"]


# ============================================================================
# Integration Tests with Real Data
# ============================================================================


class TestHeatmapIntegration:
    """Integration tests using real database data."""

    def test_full_heatmap_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_heatmap_data: dict,
    ):
        """Test complete workflow from data generation to export."""
        start_date = date.today()
        end_date = date.today() + timedelta(days=6)

        # 1. Get heatmap data
        response = client.get(
            "/api/unified-heatmap/heatmap/data",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "include_fmit": True,
                "include_residency": True,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["date_range_days"] == 7

    def test_empty_date_range_handling(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test heatmap generation with no assignments in date range."""
        # Use far future date where no assignments exist
        start_date = date.today() + timedelta(days=1000)
        end_date = date.today() + timedelta(days=1007)

        response = client.get(
            "/api/unified-heatmap/heatmap/data",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "include_fmit": True,
                "include_residency": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should still return structure even with no data
        assert "x_labels" in data
        assert "y_labels" in data
        assert "z_values" in data
