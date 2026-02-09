"""Tests for ML schemas (Field bounds, defaults, nested models)."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.ml import (
    TrainModelsRequest,
    ScoreScheduleRequest,
    PredictConflictRequest,
    PredictPreferenceRequest,
    WorkloadAnalysisRequest,
    ModelStatusResponse,
    ModelHealthResponse,
    TrainingResultResponse,
    TrainModelsResponse,
    ScoreComponentResponse,
    SuggestionResponse,
    ScheduleScoreResponse,
    ConflictPredictionResponse,
    PreferencePredictionResponse,
    PersonWorkloadResponse,
    WorkloadAnalysisResponse,
)


class TestTrainModelsRequest:
    def test_defaults(self):
        r = TrainModelsRequest()
        assert r.model_types is None
        assert r.lookback_days is None
        assert r.force_retrain is False

    # --- lookback_days ge=30, le=730 ---

    def test_lookback_days_below_min(self):
        with pytest.raises(ValidationError):
            TrainModelsRequest(lookback_days=29)

    def test_lookback_days_above_max(self):
        with pytest.raises(ValidationError):
            TrainModelsRequest(lookback_days=731)

    def test_lookback_days_boundaries(self):
        r = TrainModelsRequest(lookback_days=30)
        assert r.lookback_days == 30
        r = TrainModelsRequest(lookback_days=730)
        assert r.lookback_days == 730


class TestScoreScheduleRequest:
    def test_defaults(self):
        r = ScoreScheduleRequest()
        assert r.schedule_id is None
        assert r.schedule_data is None
        assert r.include_suggestions is True


class TestPredictConflictRequest:
    def test_valid_minimal(self):
        r = PredictConflictRequest(person_id="p1", block_id="b1")
        assert r.rotation_id is None
        assert r.existing_assignments == []

    def test_full(self):
        r = PredictConflictRequest(
            person_id="p1",
            block_id="b1",
            rotation_id="r1",
            existing_assignments=[{"id": "a1"}],
        )
        assert len(r.existing_assignments) == 1


class TestPredictPreferenceRequest:
    def test_valid(self):
        r = PredictPreferenceRequest(person_id="p1", rotation_id="r1", block_id="b1")
        assert r.person_id == "p1"


class TestWorkloadAnalysisRequest:
    def test_defaults(self):
        r = WorkloadAnalysisRequest()
        assert r.person_ids is None
        assert r.start_date is None
        assert r.end_date is None


class TestModelStatusResponse:
    def test_valid(self):
        r = ModelStatusResponse(
            name="preference", available=True, last_trained=None, age_days=None
        )
        assert r.metrics is None

    def test_trained(self):
        r = ModelStatusResponse(
            name="conflict",
            available=True,
            last_trained=datetime(2026, 3, 1),
            age_days=5,
            metrics={"accuracy": 0.85},
        )
        assert r.metrics["accuracy"] == 0.85


class TestModelHealthResponse:
    def test_valid(self):
        model = ModelStatusResponse(
            name="preference", available=False, last_trained=None, age_days=None
        )
        r = ModelHealthResponse(
            ml_enabled=True,
            models_available="1/3",
            models=[model],
            recommendations=["Train preference model"],
        )
        assert len(r.recommendations) == 1


class TestTrainingResultResponse:
    def test_valid_minimal(self):
        r = TrainingResultResponse(model_name="preference", status="success")
        assert r.samples is None
        assert r.metrics is None
        assert r.error is None
        assert r.path is None

    def test_failed(self):
        r = TrainingResultResponse(
            model_name="conflict", status="error", error="Not enough data"
        )
        assert r.error == "Not enough data"


class TestTrainModelsResponse:
    def test_valid(self):
        result = TrainingResultResponse(model_name="preference", status="success")
        r = TrainModelsResponse(
            timestamp=datetime(2026, 3, 1),
            lookback_days=90,
            models_trained=1,
            results={"preference": result},
        )
        assert r.task_id is None


class TestScoreComponentResponse:
    def test_valid(self):
        r = ScoreComponentResponse(name="coverage", score=0.9, weight=0.4)
        assert r.details == {}

    # --- score ge=0.0, le=1.0 ---

    def test_score_negative(self):
        with pytest.raises(ValidationError):
            ScoreComponentResponse(name="x", score=-0.1, weight=0.5)

    def test_score_above_max(self):
        with pytest.raises(ValidationError):
            ScoreComponentResponse(name="x", score=1.1, weight=0.5)

    # --- weight ge=0.0, le=1.0 ---

    def test_weight_negative(self):
        with pytest.raises(ValidationError):
            ScoreComponentResponse(name="x", score=0.5, weight=-0.1)

    def test_weight_above_max(self):
        with pytest.raises(ValidationError):
            ScoreComponentResponse(name="x", score=0.5, weight=1.1)


class TestSuggestionResponse:
    def test_valid(self):
        r = SuggestionResponse(
            type="rebalance",
            priority="high",
            description="Move assignment from Dr. A to Dr. B",
            impact=0.15,
        )
        assert r.affected_items == []

    # --- impact ge=0.0, le=1.0 ---

    def test_impact_negative(self):
        with pytest.raises(ValidationError):
            SuggestionResponse(type="x", priority="low", description="t", impact=-0.1)

    def test_impact_above_max(self):
        with pytest.raises(ValidationError):
            SuggestionResponse(type="x", priority="low", description="t", impact=1.1)


class TestScheduleScoreResponse:
    def test_valid(self):
        comp = ScoreComponentResponse(name="coverage", score=0.9, weight=0.4)
        r = ScheduleScoreResponse(overall_score=0.85, grade="B+", components=[comp])
        assert r.suggestions == []
        assert r.metadata == {}

    # --- overall_score ge=0.0, le=1.0 ---

    def test_overall_score_negative(self):
        with pytest.raises(ValidationError):
            ScheduleScoreResponse(overall_score=-0.1, grade="F", components=[])

    def test_overall_score_above_max(self):
        with pytest.raises(ValidationError):
            ScheduleScoreResponse(overall_score=1.1, grade="A+", components=[])


class TestConflictPredictionResponse:
    def test_valid(self):
        r = ConflictPredictionResponse(
            conflict_probability=0.15,
            risk_level="LOW",
            risk_factors=["No recent conflicts"],
            recommendation="Proceed with assignment",
        )
        assert r.conflict_probability == 0.15

    # --- conflict_probability ge=0.0, le=1.0 ---

    def test_probability_negative(self):
        with pytest.raises(ValidationError):
            ConflictPredictionResponse(
                conflict_probability=-0.1,
                risk_level="LOW",
                risk_factors=[],
                recommendation="t",
            )


class TestPreferencePredictionResponse:
    def test_valid(self):
        r = PreferencePredictionResponse(
            preference_score=0.8,
            interpretation="Highly preferred",
            contributing_factors=[{"factor": "history", "weight": 0.6}],
        )
        assert r.preference_score == 0.8

    # --- preference_score ge=0.0, le=1.0 ---

    def test_score_negative(self):
        with pytest.raises(ValidationError):
            PreferencePredictionResponse(
                preference_score=-0.1,
                interpretation="t",
                contributing_factors=[],
            )


class TestPersonWorkloadResponse:
    def test_valid(self):
        r = PersonWorkloadResponse(
            person_id="p1",
            person_name="Dr. Smith",
            current_utilization=0.8,
            optimal_utilization=0.75,
            is_overloaded=True,
        )
        assert r.workload_cluster is None


class TestWorkloadAnalysisResponse:
    def test_valid(self):
        r = WorkloadAnalysisResponse(
            total_people=20,
            overloaded_count=3,
            underutilized_count=2,
            fairness_score=0.85,
            gini_coefficient=0.12,
            people=[],
            rebalancing_suggestions=[],
        )
        assert r.fairness_score == 0.85

    # --- fairness_score ge=0.0, le=1.0 ---

    def test_fairness_score_negative(self):
        with pytest.raises(ValidationError):
            WorkloadAnalysisResponse(
                total_people=0,
                overloaded_count=0,
                underutilized_count=0,
                fairness_score=-0.1,
                gini_coefficient=0.0,
                people=[],
                rebalancing_suggestions=[],
            )

    # --- gini_coefficient ge=0.0, le=1.0 ---

    def test_gini_above_max(self):
        with pytest.raises(ValidationError):
            WorkloadAnalysisResponse(
                total_people=0,
                overloaded_count=0,
                underutilized_count=0,
                fairness_score=0.5,
                gini_coefficient=1.1,
                people=[],
                rebalancing_suggestions=[],
            )
