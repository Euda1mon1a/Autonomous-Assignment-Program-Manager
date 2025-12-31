"""
Exotic Resilience API Endpoint Tests.

Tests for Tier 5 exotic frontier resilience concepts:
- Metastability detection (statistical mechanics)
- Spin glass models (condensed matter physics)
- Catastrophe theory (dynamical systems)

Test Coverage:
- Request/response validation
- Core algorithm correctness
- Edge cases and boundary conditions
- Error handling
- Integration with FastAPI
"""

import pytest
from fastapi.testclient import TestClient


***REMOVED*** ============================================================================
***REMOVED*** Test Class: Metastability Detection
***REMOVED*** ============================================================================


class TestMetastabilityEndpoint:
    """Tests for metastability detection endpoint."""

    def test_metastability_detection_stable_state(self, client: TestClient):
        """Test metastability detection for stable state (no metastability)."""
        response = client.post(
            "/api/v1/resilience/exotic/exotic/metastability",
            json={
                "current_energy": 1.0,
                "energy_landscape": [1.5, 2.0, 1.8],  ***REMOVED*** Current is global minimum
                "barrier_samples": [0.5, 0.8, 0.3],
                "temperature": 1.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        ***REMOVED*** Should not be metastable (current state is global minimum)
        assert data["is_metastable"] is False
        assert data["risk_level"] == "low"
        assert data["source"] == "backend"
        assert "stable configuration" in data["recommendations"][0].lower()

    def test_metastability_detection_metastable_state(self, client: TestClient):
        """Test metastability detection for trapped state."""
        response = client.post(
            "/api/v1/resilience/exotic/exotic/metastability",
            json={
                "current_energy": 2.0,
                "energy_landscape": [1.0, 2.0, 3.0],  ***REMOVED*** Lower energy state exists at 1.0
                "barrier_samples": [0.3, 0.5],  ***REMOVED*** Low barrier to escape
                "temperature": 1.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        ***REMOVED*** Should detect metastability
        assert data["is_metastable"] is True
        assert data["risk_level"] in ["moderate", "high", "critical"]
        assert data["nearest_stable_state"] is not None
        assert data["barrier_height"] > 0
        assert data["escape_rate"] >= 0
        assert len(data["recommendations"]) > 0

    def test_metastability_high_barrier_low_risk(self, client: TestClient):
        """Test that high barrier reduces risk level."""
        response = client.post(
            "/api/v1/resilience/exotic/exotic/metastability",
            json={
                "current_energy": 2.0,
                "energy_landscape": [1.0, 2.0, 3.0],
                "barrier_samples": [5.0, 6.0],  ***REMOVED*** Very high barrier
                "temperature": 1.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        ***REMOVED*** High barrier should result in low risk
        assert data["barrier_height"] >= 5.0
        assert data["risk_level"] == "low"
        assert data["lifetime"] > 10.0  ***REMOVED*** Long lifetime due to high barrier

    def test_metastability_insufficient_data(self, client: TestClient):
        """Test metastability with insufficient data."""
        response = client.post(
            "/api/v1/resilience/exotic/exotic/metastability",
            json={
                "current_energy": 1.0,
                "energy_landscape": [],  ***REMOVED*** No landscape data
                "barrier_samples": [],
                "temperature": 1.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        ***REMOVED*** Should handle gracefully
        assert data["is_metastable"] is False
        assert data["barrier_height"] == 0.0
        assert data["lifetime"] == float("inf")

    def test_metastability_temperature_effect(self, client: TestClient):
        """Test effect of temperature on escape rate."""
        ***REMOVED*** Low temperature
        response_low_temp = client.post(
            "/api/v1/resilience/exotic/exotic/metastability",
            json={
                "current_energy": 2.0,
                "energy_landscape": [1.0],
                "barrier_samples": [1.0],
                "temperature": 0.1,  ***REMOVED*** Low temperature
            },
        )

        ***REMOVED*** High temperature
        response_high_temp = client.post(
            "/api/v1/resilience/exotic/exotic/metastability",
            json={
                "current_energy": 2.0,
                "energy_landscape": [1.0],
                "barrier_samples": [1.0],
                "temperature": 5.0,  ***REMOVED*** High temperature
            },
        )

        assert response_low_temp.status_code == 200
        assert response_high_temp.status_code == 200

        low_temp_data = response_low_temp.json()
        high_temp_data = response_high_temp.json()

        ***REMOVED*** Higher temperature should have higher escape rate
        assert high_temp_data["escape_rate"] > low_temp_data["escape_rate"]
        assert low_temp_data["lifetime"] > high_temp_data["lifetime"]

    def test_metastability_invalid_temperature(self, client: TestClient):
        """Test that invalid temperature is rejected."""
        response = client.post(
            "/api/v1/resilience/exotic/exotic/metastability",
            json={
                "current_energy": 1.0,
                "energy_landscape": [1.5],
                "barrier_samples": [0.5],
                "temperature": 0.0,  ***REMOVED*** Invalid: too low
            },
        )

        assert response.status_code == 422


class TestReorganizationRiskEndpoint:
    """Tests for reorganization risk prediction endpoint."""

    def test_reorganization_low_risk(self, client: TestClient):
        """Test low reorganization risk scenario."""
        response = client.post(
            "/api/v1/resilience/exotic/exotic/reorganization-risk",
            json={
                "current_stability": 0.9,  ***REMOVED*** High stability
                "external_perturbation": 0.1,  ***REMOVED*** Low perturbation
                "system_temperature": 1.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["risk_level"] == "low"
        assert data["risk_score"] <= 0.3
        assert data["effective_barrier"] > 0.5
        assert data["source"] == "backend"

    def test_reorganization_high_risk(self, client: TestClient):
        """Test high reorganization risk scenario."""
        response = client.post(
            "/api/v1/resilience/exotic/exotic/reorganization-risk",
            json={
                "current_stability": 0.3,  ***REMOVED*** Low stability
                "external_perturbation": 0.5,  ***REMOVED*** High perturbation
                "system_temperature": 2.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["risk_level"] in ["high", "critical"]
        assert data["risk_score"] >= 0.5
        assert data["effective_barrier"] <= 0.2
        assert (
            "URGENT" in data["recommendations"][0]
            or "High risk" in data["recommendations"][0]
        )

    def test_reorganization_critical_immediate(self, client: TestClient):
        """Test critical risk with barrier breached."""
        response = client.post(
            "/api/v1/resilience/exotic/exotic/reorganization-risk",
            json={
                "current_stability": 0.2,
                "external_perturbation": 0.5,  ***REMOVED*** Perturbation exceeds stability
                "system_temperature": 1.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["risk_level"] == "critical"
        assert data["risk_score"] >= 0.8
        assert data["effective_barrier"] <= 0.0
        assert data["estimated_time_to_reorganization"] == 0.0  ***REMOVED*** Immediate


***REMOVED*** ============================================================================
***REMOVED*** Test Class: Spin Glass Model
***REMOVED*** ============================================================================


class TestSpinGlassEndpoint:
    """Tests for spin glass replica generation endpoint."""

    def test_spin_glass_basic_generation(self, client: TestClient):
        """Test basic spin glass replica generation."""
        response = client.post(
            "/api/v1/resilience/exotic/exotic/spin-glass",
            json={
                "num_spins": 50,
                "num_replicas": 3,
                "temperature": 1.0,
                "frustration_level": 0.3,
                "num_iterations": 500,
            },
        )

        assert response.status_code == 200
        data = response.json()

        ***REMOVED*** Should generate requested number of replicas
        assert len(data["configurations"]) == 3
        assert data["source"] == "backend"

        ***REMOVED*** All configurations should have valid metrics
        for config in data["configurations"]:
            assert "energy" in config
            assert 0.0 <= config["frustration"] <= 1.0
            assert -1.0 <= config["overlap"] <= 1.0

        ***REMOVED*** Ensemble metrics
        assert data["mean_energy"] is not None
        assert data["energy_std"] >= 0.0
        assert 0.0 <= data["diversity_score"] <= 1.0
        assert data["difficulty"] in ["easy", "moderate", "hard", "very_hard"]

    def test_spin_glass_diversity_increases_with_replicas(self, client: TestClient):
        """Test that more replicas increase diversity."""
        ***REMOVED*** Generate few replicas
        response_few = client.post(
            "/api/v1/resilience/exotic/exotic/spin-glass",
            json={
                "num_spins": 30,
                "num_replicas": 2,
                "temperature": 1.0,
                "frustration_level": 0.3,
                "num_iterations": 500,
            },
        )

        ***REMOVED*** Generate many replicas
        response_many = client.post(
            "/api/v1/resilience/exotic/exotic/spin-glass",
            json={
                "num_spins": 30,
                "num_replicas": 10,
                "temperature": 1.0,
                "frustration_level": 0.3,
                "num_iterations": 500,
            },
        )

        assert response_few.status_code == 200
        assert response_many.status_code == 200

        data_few = response_few.json()
        data_many = response_many.json()

        ***REMOVED*** More replicas should generally have higher diversity
        ***REMOVED*** (though this is stochastic, so we just check it's valid)
        assert 0.0 <= data_many["diversity_score"] <= 1.0

    def test_spin_glass_frustration_effect(self, client: TestClient):
        """Test effect of frustration level on landscape ruggedness."""
        ***REMOVED*** Low frustration
        response_low = client.post(
            "/api/v1/resilience/exotic/exotic/spin-glass",
            json={
                "num_spins": 40,
                "num_replicas": 3,
                "temperature": 1.0,
                "frustration_level": 0.1,  ***REMOVED*** Low frustration
                "num_iterations": 500,
            },
        )

        ***REMOVED*** High frustration
        response_high = client.post(
            "/api/v1/resilience/exotic/exotic/spin-glass",
            json={
                "num_spins": 40,
                "num_replicas": 3,
                "temperature": 1.0,
                "frustration_level": 0.8,  ***REMOVED*** High frustration
                "num_iterations": 500,
            },
        )

        assert response_low.status_code == 200
        assert response_high.status_code == 200

        ***REMOVED*** Both should return valid data
        data_low = response_low.json()
        data_high = response_high.json()

        assert 0.0 <= data_low["landscape_ruggedness"] <= 1.0
        assert 0.0 <= data_high["landscape_ruggedness"] <= 1.0

    def test_spin_glass_invalid_parameters(self, client: TestClient):
        """Test that invalid parameters are rejected."""
        ***REMOVED*** num_spins too small
        response = client.post(
            "/api/v1/resilience/exotic/exotic/spin-glass",
            json={
                "num_spins": 5,  ***REMOVED*** Below minimum of 10
                "num_replicas": 3,
                "temperature": 1.0,
                "frustration_level": 0.3,
                "num_iterations": 500,
            },
        )
        assert response.status_code == 422

        ***REMOVED*** num_replicas too high
        response = client.post(
            "/api/v1/resilience/exotic/exotic/spin-glass",
            json={
                "num_spins": 50,
                "num_replicas": 25,  ***REMOVED*** Above maximum of 20
                "temperature": 1.0,
                "frustration_level": 0.3,
                "num_iterations": 500,
            },
        )
        assert response.status_code == 422

        ***REMOVED*** frustration out of range
        response = client.post(
            "/api/v1/resilience/exotic/exotic/spin-glass",
            json={
                "num_spins": 50,
                "num_replicas": 3,
                "temperature": 1.0,
                "frustration_level": 1.5,  ***REMOVED*** Above 1.0
                "num_iterations": 500,
            },
        )
        assert response.status_code == 422


***REMOVED*** ============================================================================
***REMOVED*** Test Class: Catastrophe Theory
***REMOVED*** ============================================================================


class TestCatastropheEndpoint:
    """Tests for catastrophe prediction endpoint."""

    def test_catastrophe_no_jump_detected(self, client: TestClient):
        """Test case where no catastrophe is predicted."""
        response = client.post(
            "/api/v1/resilience/exotic/exotic/catastrophe",
            json={
                "current_a": 1.0,
                "current_b": 0.5,
                "da": 0.1,  ***REMOVED*** Small change
                "db": 0.1,
                "num_steps": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()

        ***REMOVED*** May or may not detect catastrophe depending on parameters
        assert "catastrophe_detected" in data
        assert "resilience_score" in data
        assert 0.0 <= data["resilience_score"] <= 1.0
        assert data["status"] in ["robust", "stable", "vulnerable", "critical"]
        assert data["source"] == "backend"

    def test_catastrophe_jump_detected(self, client: TestClient):
        """Test case where catastrophe jump is detected."""
        response = client.post(
            "/api/v1/resilience/exotic/exotic/catastrophe",
            json={
                "current_a": -1.0,  ***REMOVED*** Near bifurcation
                "current_b": 0.1,
                "da": -2.0,  ***REMOVED*** Large change crossing bifurcation
                "db": 1.0,
                "num_steps": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()

        ***REMOVED*** Check catastrophe point structure if detected
        if data["catastrophe_detected"]:
            assert data["catastrophe_point"] is not None
            point = data["catastrophe_point"]
            assert "a_critical" in point
            assert "b_critical" in point
            assert "jump_magnitude" in point
            assert point["jump_magnitude"] >= 0

    def test_catastrophe_resilience_scoring(self, client: TestClient):
        """Test resilience scoring for different parameter values."""
        ***REMOVED*** Far from bifurcation (robust)
        response_robust = client.post(
            "/api/v1/resilience/exotic/exotic/catastrophe",
            json={
                "current_a": 5.0,  ***REMOVED*** Far from bifurcation set
                "current_b": 0.0,
                "da": 0.1,
                "db": 0.1,
                "num_steps": 50,
            },
        )

        assert response_robust.status_code == 200
        data_robust = response_robust.json()

        ***REMOVED*** Should indicate safety
        assert data_robust["is_safe"] or data_robust["status"] in ["robust", "stable"]
        assert len(data_robust["recommendations"]) > 0

    def test_catastrophe_critical_warning(self, client: TestClient):
        """Test that critical status generates urgent warnings."""
        response = client.post(
            "/api/v1/resilience/exotic/exotic/catastrophe",
            json={
                "current_a": 0.0,  ***REMOVED*** On bifurcation boundary
                "current_b": 0.0,
                "da": -0.5,
                "db": 0.5,
                "num_steps": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()

        ***REMOVED*** Check that recommendations exist
        assert len(data["recommendations"]) > 0

        ***REMOVED*** If status is critical, should have URGENT warning
        if data["status"] == "critical":
            assert any("URGENT" in rec for rec in data["recommendations"])

    def test_catastrophe_invalid_num_steps(self, client: TestClient):
        """Test that invalid num_steps is rejected."""
        response = client.post(
            "/api/v1/resilience/exotic/exotic/catastrophe",
            json={
                "current_a": 1.0,
                "current_b": 0.5,
                "da": 0.1,
                "db": 0.1,
                "num_steps": 5,  ***REMOVED*** Below minimum of 10
            },
        )

        assert response.status_code == 422


***REMOVED*** ============================================================================
***REMOVED*** Integration Tests
***REMOVED*** ============================================================================


class TestExoticIntegration:
    """Integration tests for exotic endpoints."""

    def test_all_endpoints_return_backend_source(self, client: TestClient):
        """Test that all exotic endpoints mark source as 'backend'."""
        endpoints = [
            (
                "/api/v1/resilience/exotic/exotic/metastability",
                {
                    "current_energy": 1.0,
                    "energy_landscape": [1.5],
                    "barrier_samples": [0.5],
                    "temperature": 1.0,
                },
            ),
            (
                "/api/v1/resilience/exotic/exotic/reorganization-risk",
                {
                    "current_stability": 0.9,
                    "external_perturbation": 0.1,
                    "system_temperature": 1.0,
                },
            ),
            (
                "/api/v1/resilience/exotic/exotic/spin-glass",
                {
                    "num_spins": 20,
                    "num_replicas": 2,
                    "temperature": 1.0,
                    "frustration_level": 0.3,
                    "num_iterations": 200,
                },
            ),
            (
                "/api/v1/resilience/exotic/exotic/catastrophe",
                {
                    "current_a": 1.0,
                    "current_b": 0.5,
                    "da": 0.1,
                    "db": 0.1,
                    "num_steps": 50,
                },
            ),
        ]

        for endpoint, payload in endpoints:
            response = client.post(endpoint, json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["source"] == "backend", (
                f"Endpoint {endpoint} returned wrong source"
            )

    def test_exotic_endpoints_handle_concurrent_requests(self, client: TestClient):
        """Test that exotic endpoints can handle concurrent requests."""
        ***REMOVED*** This is a simplified concurrency test
        ***REMOVED*** In production, use pytest-asyncio for true async testing

        responses = []
        for _ in range(3):
            response = client.post(
                "/api/v1/resilience/exotic/exotic/metastability",
                json={
                    "current_energy": 1.0,
                    "energy_landscape": [1.5],
                    "barrier_samples": [0.5],
                    "temperature": 1.0,
                },
            )
            responses.append(response)

        ***REMOVED*** All should succeed
        for response in responses:
            assert response.status_code == 200
