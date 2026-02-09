"""Tests for experiments/A-B testing schemas (Pydantic validation and Field constraints)."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.experiments.ab_testing import (
    ExperimentStatus,
    ExperimentTargeting,
    MetricType,
    Variant,
)
from app.schemas.experiments import (
    ExperimentCreateRequest,
    ExperimentUpdateRequest,
    UserAssignmentRequest,
    MetricTrackRequest,
    ConcludeExperimentRequest,
    VariantResponse,
    ExperimentResponse,
    ExperimentListResponse,
    VariantAssignmentResponse,
    MetricDataResponse,
    VariantMetricsResponse,
    ExperimentResultsResponse,
    ExperimentLifecycleResponse,
    ExperimentLifecycleListResponse,
    ExperimentStatsResponse,
)


# ===========================================================================
# ExperimentCreateRequest Tests
# ===========================================================================


def _make_variants(n=2):
    variants = []
    for i in range(n):
        variants.append(
            Variant(
                key=f"variant_{i}",
                name=f"Variant {i}",
                allocation=50 if n == 2 else 100 // n,
                is_control=(i == 0),
            )
        )
    return variants


class TestExperimentCreateRequest:
    def test_valid_minimal(self):
        r = ExperimentCreateRequest(
            key="exp-001",
            name="Test Experiment",
            variants=_make_variants(),
        )
        assert r.description == ""
        assert r.hypothesis == ""
        assert r.start_date is None
        assert r.end_date is None

    # --- key min_length=1, max_length=100 ---

    def test_key_empty(self):
        with pytest.raises(ValidationError):
            ExperimentCreateRequest(key="", name="Test", variants=_make_variants())

    def test_key_too_long(self):
        with pytest.raises(ValidationError):
            ExperimentCreateRequest(
                key="x" * 101, name="Test", variants=_make_variants()
            )

    # --- name min_length=1, max_length=255 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            ExperimentCreateRequest(key="exp-001", name="", variants=_make_variants())

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            ExperimentCreateRequest(
                key="exp-001", name="x" * 256, variants=_make_variants()
            )

    # --- variants min_length=2 ---

    def test_variants_one(self):
        with pytest.raises(ValidationError):
            ExperimentCreateRequest(
                key="exp-001", name="Test", variants=_make_variants(1)
            )

    def test_variants_three(self):
        r = ExperimentCreateRequest(
            key="exp-001", name="Test", variants=_make_variants(3)
        )
        assert len(r.variants) == 3


# ===========================================================================
# ExperimentUpdateRequest Tests
# ===========================================================================


class TestExperimentUpdateRequest:
    def test_all_none(self):
        r = ExperimentUpdateRequest()
        assert r.name is None
        assert r.description is None
        assert r.hypothesis is None
        assert r.targeting is None
        assert r.config is None
        assert r.end_date is None

    # --- name min_length=1, max_length=255 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            ExperimentUpdateRequest(name="")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            ExperimentUpdateRequest(name="x" * 256)

    # --- description max_length=2000 ---

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            ExperimentUpdateRequest(description="x" * 2001)

    def test_description_max_length(self):
        r = ExperimentUpdateRequest(description="x" * 2000)
        assert len(r.description) == 2000

    # --- hypothesis max_length=1000 ---

    def test_hypothesis_too_long(self):
        with pytest.raises(ValidationError):
            ExperimentUpdateRequest(hypothesis="x" * 1001)


# ===========================================================================
# UserAssignmentRequest Tests
# ===========================================================================


class TestUserAssignmentRequest:
    def test_valid_minimal(self):
        r = UserAssignmentRequest(user_id="user-001")
        assert r.user_attributes == {}
        assert r.force_variant is None

    # --- user_id min_length=1, max_length=100 ---

    def test_user_id_empty(self):
        with pytest.raises(ValidationError):
            UserAssignmentRequest(user_id="")

    def test_user_id_too_long(self):
        with pytest.raises(ValidationError):
            UserAssignmentRequest(user_id="x" * 101)

    # --- force_variant max_length=100 ---

    def test_force_variant_too_long(self):
        with pytest.raises(ValidationError):
            UserAssignmentRequest(user_id="user-001", force_variant="x" * 101)


# ===========================================================================
# MetricTrackRequest Tests
# ===========================================================================


class TestMetricTrackRequest:
    def test_valid(self):
        r = MetricTrackRequest(
            user_id="user-001",
            variant_key="control",
            metric_name="response_time",
            value=1.5,
        )
        assert r.metric_type == MetricType.NUMERIC
        assert r.metadata == {}

    # --- metric_name min_length=1, max_length=100 ---

    def test_metric_name_empty(self):
        with pytest.raises(ValidationError):
            MetricTrackRequest(
                user_id="user-001",
                variant_key="control",
                metric_name="",
                value=1.0,
            )

    def test_metric_name_too_long(self):
        with pytest.raises(ValidationError):
            MetricTrackRequest(
                user_id="user-001",
                variant_key="control",
                metric_name="x" * 101,
                value=1.0,
            )


# ===========================================================================
# ConcludeExperimentRequest Tests
# ===========================================================================


class TestConcludeExperimentRequest:
    def test_valid(self):
        r = ConcludeExperimentRequest(winning_variant="variant_0")
        assert r.notes == ""

    # --- winning_variant min_length=1, max_length=100 ---

    def test_winning_variant_empty(self):
        with pytest.raises(ValidationError):
            ConcludeExperimentRequest(winning_variant="")

    def test_winning_variant_too_long(self):
        with pytest.raises(ValidationError):
            ConcludeExperimentRequest(winning_variant="x" * 101)

    # --- notes max_length=2000 ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            ConcludeExperimentRequest(winning_variant="v0", notes="x" * 2001)

    def test_notes_max_length(self):
        r = ConcludeExperimentRequest(winning_variant="v0", notes="x" * 2000)
        assert len(r.notes) == 2000


# ===========================================================================
# Response Schema Tests
# ===========================================================================


class TestVariantResponse:
    def test_valid(self):
        r = VariantResponse(
            key="control",
            name="Control",
            description="Baseline",
            allocation=50,
            is_control=True,
            config={},
        )
        assert r.is_control is True


class TestExperimentListResponse:
    def test_valid(self):
        r = ExperimentListResponse(
            experiments=[], total=0, page=1, page_size=10, total_pages=0
        )
        assert r.experiments == []


class TestVariantAssignmentResponse:
    def test_valid(self):
        r = VariantAssignmentResponse(
            experiment_key="exp-001",
            user_id="user-001",
            variant_key="control",
            assigned_at=datetime.now(),
            is_override=False,
        )
        assert r.is_override is False


class TestVariantMetricsResponse:
    def test_valid(self):
        r = VariantMetricsResponse(
            variant_key="control",
            user_count=100,
            metrics={"response_time": {"mean": 1.5, "std": 0.3}},
        )
        assert r.user_count == 100


class TestExperimentResultsResponse:
    def test_valid(self):
        r = ExperimentResultsResponse(
            experiment_key="exp-001",
            status=ExperimentStatus.COMPLETED,
            start_date=None,
            end_date=None,
            duration_days=30.0,
            total_users=200,
            variant_metrics=[],
            is_significant=True,
            confidence_level=0.95,
            p_value=0.03,
            winning_variant="variant_1",
            recommendation="Deploy variant_1",
            statistical_power=0.8,
        )
        assert r.is_significant is True


class TestExperimentLifecycleListResponse:
    def test_valid(self):
        r = ExperimentLifecycleListResponse(events=[], total=0)
        assert r.events == []


class TestExperimentStatsResponse:
    def test_valid(self):
        r = ExperimentStatsResponse(
            total_experiments=10,
            running_experiments=3,
            completed_experiments=5,
            draft_experiments=1,
            paused_experiments=0,
            cancelled_experiments=1,
            total_users_assigned=500,
            total_metrics_tracked=2000,
        )
        assert r.total_experiments == 10
