"""Tests for experiments/A/B testing API routes."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.experiments import (
    Experiment,
    ExperimentConfig,
    ExperimentStatus,
    ExperimentTargeting,
    Variant,
)


class TestExperimentsRoutes:
    """Test suite for experiments API endpoints."""

    def test_create_experiment(self, client: TestClient, auth_headers: dict):
        """Test creating a new experiment."""
        experiment_data = {
            "key": "test_experiment_1",
            "name": "Test Experiment",
            "description": "A test experiment",
            "variants": [
                {"key": "control", "name": "Control", "allocation": 50, "is_control": True},
                {"key": "treatment", "name": "Treatment", "allocation": 50},
            ],
        }

        response = client.post(
            "/api/experiments/",
            json=experiment_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["key"] == "test_experiment_1"
        assert data["name"] == "Test Experiment"
        assert data["status"] == "draft"
        assert len(data["variants"]) == 2

    def test_create_experiment_invalid_allocation(self, client: TestClient, auth_headers: dict):
        """Test that experiment creation fails with invalid allocation."""
        experiment_data = {
            "key": "invalid_experiment",
            "name": "Invalid Experiment",
            "variants": [
                {"key": "control", "allocation": 60},
                {"key": "treatment", "allocation": 60},  # Sum = 120, invalid
            ],
        }

        response = client.post(
            "/api/experiments/",
            json=experiment_data,
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_list_experiments(self, client: TestClient, auth_headers: dict):
        """Test listing experiments."""
        response = client.get(
            "/api/experiments/",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "experiments" in data
        assert "total" in data
        assert "page" in data

    def test_get_experiment_stats(self, client: TestClient, auth_headers: dict):
        """Test getting experiment statistics."""
        response = client.get(
            "/api/experiments/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_experiments" in data
        assert "running_experiments" in data

    def test_get_experiment_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent experiment."""
        response = client.get(
            "/api/experiments/nonexistent_key",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_unauthorized_access(self, client: TestClient):
        """Test that unauthenticated requests are rejected."""
        response = client.get("/api/experiments/")

        assert response.status_code == 401


class TestExperimentModels:
    """Test suite for experiment models."""

    def test_variant_validation(self):
        """Test variant model validation."""
        variant = Variant(
            key="control",
            name="Control",
            allocation=50,
            is_control=True,
        )

        assert variant.key == "control"
        assert variant.allocation == 50

    def test_variant_invalid_key(self):
        """Test that invalid variant key raises error."""
        with pytest.raises(ValueError):
            Variant(
                key="invalid key with spaces",
                allocation=50,
            )

    def test_experiment_targeting(self):
        """Test experiment targeting model."""
        targeting = ExperimentTargeting(
            roles=["admin", "coordinator"],
            percentage=50,
        )

        assert len(targeting.roles) == 2
        assert targeting.percentage == 50

    def test_experiment_config(self):
        """Test experiment configuration model."""
        config = ExperimentConfig(
            sticky_bucketing=True,
            min_sample_size=200,
            confidence_level=0.99,
        )

        assert config.sticky_bucketing is True
        assert config.min_sample_size == 200
        assert config.confidence_level == 0.99
