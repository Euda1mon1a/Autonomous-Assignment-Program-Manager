"""Tests for ML API routes."""

from fastapi.testclient import TestClient


class TestMLRoutes:
    """Test suite for ML API endpoints."""

    def test_get_model_health(self, client: TestClient, auth_headers: dict):
        """Test checking ML model health."""
        response = client.get(
            "/api/ml/health",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "ml_enabled" in data
        assert "models_available" in data
        assert "models" in data
        assert "recommendations" in data

    def test_score_schedule_ml_disabled(self, client: TestClient, auth_headers: dict):
        """Test schedule scoring when ML is disabled."""
        request_data = {
            "schedule_data": {
                "assignments": [],
                "blocks": [],
            },
            "include_suggestions": True,
        }

        response = client.post(
            "/api/ml/score",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert "grade" in data
        assert "components" in data

    def test_predict_conflict_ml_disabled(self, client: TestClient, auth_headers: dict):
        """Test conflict prediction when ML is disabled."""
        request_data = {
            "person_id": "test-person-id",
            "block_id": "test-block-id",
            "rotation_id": "test-rotation-id",
            "existing_assignments": [],
        }

        response = client.post(
            "/api/ml/predict/conflict",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "conflict_probability" in data
        assert "risk_level" in data
        assert "recommendation" in data

    def test_predict_preference_ml_disabled(
        self, client: TestClient, auth_headers: dict
    ):
        """Test preference prediction when ML is disabled."""
        request_data = {
            "person_id": "test-person-id",
            "rotation_id": "test-rotation-id",
            "block_id": "test-block-id",
        }

        response = client.post(
            "/api/ml/predict/preference",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "preference_score" in data
        assert "interpretation" in data

    def test_analyze_workload_ml_disabled(self, client: TestClient, auth_headers: dict):
        """Test workload analysis when ML is disabled."""
        request_data = {
            "person_ids": None,
        }

        response = client.post(
            "/api/ml/analyze/workload",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_people" in data
        assert "fairness_score" in data

    def test_train_models_ml_disabled(self, client: TestClient, auth_headers: dict):
        """Test model training when ML is disabled."""
        request_data = {
            "model_types": ["preference"],
            "force_retrain": False,
        }

        response = client.post(
            "/api/ml/train",
            json=request_data,
            headers=auth_headers,
        )

        # Should fail because ML is disabled and force_retrain is False
        assert response.status_code == 400

    def test_train_models_async(self, client: TestClient, auth_headers: dict):
        """Test async model training endpoint."""
        request_data = {
            "model_types": ["preference"],
            "force_retrain": True,
        }

        response = client.post(
            "/api/ml/train/async",
            json=request_data,
            headers=auth_headers,
        )

        # Should succeed and return task info
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "task_id" in data or "message" in data

    def test_unauthorized_access(self, client: TestClient):
        """Test that unauthenticated requests are rejected."""
        response = client.get("/api/ml/health")

        assert response.status_code == 401


class TestMLSchemas:
    """Test suite for ML schemas."""

    def test_score_schedule_request_validation(self):
        """Test ScoreScheduleRequest validation."""
        from app.schemas.ml import ScoreScheduleRequest

        request = ScoreScheduleRequest(
            schedule_data={"assignments": []},
            include_suggestions=True,
        )

        assert request.schedule_data == {"assignments": []}
        assert request.include_suggestions is True

    def test_train_models_request_validation(self):
        """Test TrainModelsRequest validation."""
        from app.schemas.ml import TrainModelsRequest

        request = TrainModelsRequest(
            model_types=["preference", "conflict"],
            lookback_days=180,
            force_retrain=True,
        )

        assert len(request.model_types) == 2
        assert request.lookback_days == 180
        assert request.force_retrain is True

    def test_conflict_prediction_response(self):
        """Test ConflictPredictionResponse model."""
        from app.schemas.ml import ConflictPredictionResponse

        response = ConflictPredictionResponse(
            conflict_probability=0.75,
            risk_level="HIGH",
            risk_factors=["ACGME hours exceeded"],
            recommendation="Review before proceeding",
        )

        assert response.conflict_probability == 0.75
        assert response.risk_level == "HIGH"
