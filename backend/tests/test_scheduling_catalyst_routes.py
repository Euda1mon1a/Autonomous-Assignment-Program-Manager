"""Tests for scheduling catalyst API routes."""

from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient


class TestSchedulingCatalystRoutes:
    """Test suite for scheduling catalyst API endpoints."""

    def test_detect_barriers(self, client: TestClient, auth_headers: dict):
        """Test barrier detection endpoint."""
        request_data = {
            "assignment_id": str(uuid4()),
            "proposed_change": {
                "target_date": date.today().isoformat(),
                "reaction_type": "swap",
            },
        }

        response = client.post(
            "/api/scheduling-catalyst/barriers/detect",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_barriers" in data
        assert "barriers" in data
        assert "activation_energy" in data
        assert "summary" in data

    def test_optimize_pathway(self, client: TestClient, auth_headers: dict):
        """Test pathway optimization endpoint."""
        request_data = {
            "assignment_id": str(uuid4()),
            "proposed_change": {
                "target_date": date.today().isoformat(),
            },
            "energy_threshold": 0.8,
        }

        response = client.post(
            "/api/scheduling-catalyst/pathways/optimize",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "blocking_barriers" in data
        assert "recommendations" in data

    def test_analyze_swap_barriers(self, client: TestClient, auth_headers: dict):
        """Test swap barrier analysis endpoint."""
        request_data = {
            "source_faculty_id": str(uuid4()),
            "source_week": date.today().isoformat(),
            "target_faculty_id": str(uuid4()),
            "swap_type": "one_to_one",
        }

        response = client.post(
            "/api/scheduling-catalyst/swaps/analyze",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "swap_feasible" in data
        assert "barriers" in data
        assert "activation_energy" in data
        assert "recommendations" in data

    def test_get_catalyst_capacity(self, client: TestClient, auth_headers: dict):
        """Test catalyst capacity endpoint."""
        response = client.get(
            "/api/scheduling-catalyst/capacity",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "person_catalysts_available" in data
        assert "mechanism_catalysts_available" in data
        assert "total_capacity" in data

    def test_batch_optimize(self, client: TestClient, auth_headers: dict):
        """Test batch optimization endpoint."""
        request_data = {
            "changes": [
                {
                    "assignment_id": str(uuid4()),
                    "proposed_change": {"target_date": date.today().isoformat()},
                    "energy_threshold": 0.8,
                    "prefer_mechanisms": True,
                    "allow_multi_step": True,
                },
            ],
            "find_optimal_order": True,
        }

        response = client.post(
            "/api/scheduling-catalyst/batch/optimize",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_changes" in data
        assert "successful_pathways" in data
        assert "results" in data

    def test_unauthorized_access(self, client: TestClient):
        """Test that unauthenticated requests are rejected."""
        response = client.get("/api/scheduling-catalyst/capacity")

        assert response.status_code == 401


class TestSchedulingCatalystSchemas:
    """Test suite for scheduling catalyst schemas."""

    def test_barrier_detection_request(self):
        """Test BarrierDetectionRequest validation."""
        from app.schemas.scheduling_catalyst import BarrierDetectionRequest

        request = BarrierDetectionRequest(
            assignment_id=uuid4(),
            proposed_change={"target_date": "2024-01-15"},
        )

        assert request.proposed_change["target_date"] == "2024-01-15"

    def test_swap_barrier_analysis_request(self):
        """Test SwapBarrierAnalysisRequest validation."""
        from app.schemas.scheduling_catalyst import SwapBarrierAnalysisRequest

        request = SwapBarrierAnalysisRequest(
            source_faculty_id=uuid4(),
            source_week=date.today(),
            target_faculty_id=uuid4(),
            swap_type="one_to_one",
        )

        assert request.swap_type == "one_to_one"

    def test_energy_barrier_response(self):
        """Test EnergyBarrierResponse model."""
        from app.schemas.scheduling_catalyst import (
            BarrierTypeEnum,
            EnergyBarrierResponse,
        )

        response = EnergyBarrierResponse(
            barrier_type=BarrierTypeEnum.KINETIC,
            name="Freeze Horizon",
            description="Within freeze period",
            energy_contribution=0.5,
            is_absolute=False,
            source="freeze_horizon",
        )

        assert response.barrier_type == BarrierTypeEnum.KINETIC
        assert response.energy_contribution == 0.5
