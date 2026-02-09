"""Tests for VaR analytics schemas (enums, Field bounds, defaults)."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.schemas.var_analytics import (
    RiskSeverity,
    VaRMetric,
    CoverageVaRRequest,
    CoverageVaRResponse,
    WorkloadVaRRequest,
    WorkloadVaRResponse,
    ConditionalVaRRequest,
    ConditionalVaRResponse,
)


class TestRiskSeverity:
    def test_values(self):
        assert RiskSeverity.LOW.value == "low"
        assert RiskSeverity.MODERATE.value == "moderate"
        assert RiskSeverity.HIGH.value == "high"
        assert RiskSeverity.CRITICAL.value == "critical"
        assert RiskSeverity.EXTREME.value == "extreme"

    def test_count(self):
        assert len(RiskSeverity) == 5

    def test_is_str(self):
        assert isinstance(RiskSeverity.LOW, str)


class TestVaRMetric:
    def test_valid(self):
        r = VaRMetric(
            confidence_level=0.95,
            var_value=3.5,
            interpretation="With 95% confidence, loss <= 3.5",
            percentile=95.0,
        )
        assert r.confidence_level == 0.95

    # --- confidence_level ge=0.0, le=1.0 ---

    def test_confidence_level_negative(self):
        with pytest.raises(ValidationError):
            VaRMetric(
                confidence_level=-0.1,
                var_value=0,
                interpretation="t",
                percentile=0,
            )

    def test_confidence_level_above_max(self):
        with pytest.raises(ValidationError):
            VaRMetric(
                confidence_level=1.1,
                var_value=0,
                interpretation="t",
                percentile=0,
            )

    # --- percentile ge=0.0, le=100.0 ---

    def test_percentile_negative(self):
        with pytest.raises(ValidationError):
            VaRMetric(
                confidence_level=0.5,
                var_value=0,
                interpretation="t",
                percentile=-1.0,
            )

    def test_percentile_above_max(self):
        with pytest.raises(ValidationError):
            VaRMetric(
                confidence_level=0.5,
                var_value=0,
                interpretation="t",
                percentile=101.0,
            )


class TestCoverageVaRRequest:
    def test_defaults(self):
        r = CoverageVaRRequest(start_date=date(2026, 3, 1), end_date=date(2026, 6, 30))
        assert r.confidence_levels == [0.90, 0.95, 0.99]
        assert r.rotation_types is None
        assert r.historical_days == 90

    # --- historical_days ge=30, le=365 ---

    def test_historical_days_below_min(self):
        with pytest.raises(ValidationError):
            CoverageVaRRequest(
                start_date=date(2026, 3, 1),
                end_date=date(2026, 6, 30),
                historical_days=29,
            )

    def test_historical_days_above_max(self):
        with pytest.raises(ValidationError):
            CoverageVaRRequest(
                start_date=date(2026, 3, 1),
                end_date=date(2026, 6, 30),
                historical_days=366,
            )

    def test_historical_days_boundaries(self):
        r = CoverageVaRRequest(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 6, 30),
            historical_days=30,
        )
        assert r.historical_days == 30
        r = CoverageVaRRequest(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 6, 30),
            historical_days=365,
        )
        assert r.historical_days == 365


class TestCoverageVaRResponse:
    def _make_metric(self):
        return VaRMetric(
            confidence_level=0.95,
            var_value=0.85,
            interpretation="test",
            percentile=95.0,
        )

    def test_valid(self):
        r = CoverageVaRResponse(
            analyzed_at=datetime(2026, 3, 1),
            period_start=date(2026, 3, 1),
            period_end=date(2026, 6, 30),
            historical_days=90,
            scenarios_analyzed=1000,
            var_metrics=[self._make_metric()],
            baseline_coverage=0.95,
            worst_case_coverage=0.80,
            severity=RiskSeverity.LOW,
        )
        assert r.recommendations == []
        assert r.metadata == {}

    # --- baseline_coverage ge=0.0, le=1.0 ---

    def test_baseline_coverage_negative(self):
        with pytest.raises(ValidationError):
            CoverageVaRResponse(
                analyzed_at=datetime(2026, 3, 1),
                period_start=date(2026, 3, 1),
                period_end=date(2026, 6, 30),
                historical_days=90,
                scenarios_analyzed=1000,
                var_metrics=[],
                baseline_coverage=-0.1,
                worst_case_coverage=0.5,
                severity=RiskSeverity.LOW,
            )

    def test_baseline_coverage_above_max(self):
        with pytest.raises(ValidationError):
            CoverageVaRResponse(
                analyzed_at=datetime(2026, 3, 1),
                period_start=date(2026, 3, 1),
                period_end=date(2026, 6, 30),
                historical_days=90,
                scenarios_analyzed=1000,
                var_metrics=[],
                baseline_coverage=1.1,
                worst_case_coverage=0.5,
                severity=RiskSeverity.LOW,
            )


class TestWorkloadVaRRequest:
    def test_defaults(self):
        r = WorkloadVaRRequest(start_date=date(2026, 3, 1), end_date=date(2026, 6, 30))
        assert r.confidence_levels == [0.90, 0.95, 0.99]
        assert r.metric == "gini_coefficient"


class TestWorkloadVaRResponse:
    def test_valid(self):
        r = WorkloadVaRResponse(
            analyzed_at=datetime(2026, 3, 1),
            period_start=date(2026, 3, 1),
            period_end=date(2026, 6, 30),
            metric="gini_coefficient",
            var_metrics=[],
            baseline_value=0.15,
            worst_case_value=0.45,
            severity=RiskSeverity.MODERATE,
        )
        assert r.recommendations == []
        assert r.metadata == {}


class TestConditionalVaRRequest:
    def test_defaults(self):
        r = ConditionalVaRRequest(
            start_date=date(2026, 3, 1), end_date=date(2026, 6, 30)
        )
        assert r.confidence_level == 0.95
        assert r.loss_metric == "coverage_drop"

    # --- confidence_level ge=0.5, le=0.999 ---

    def test_confidence_level_below_min(self):
        with pytest.raises(ValidationError):
            ConditionalVaRRequest(
                start_date=date(2026, 3, 1),
                end_date=date(2026, 6, 30),
                confidence_level=0.49,
            )

    def test_confidence_level_above_max(self):
        with pytest.raises(ValidationError):
            ConditionalVaRRequest(
                start_date=date(2026, 3, 1),
                end_date=date(2026, 6, 30),
                confidence_level=1.0,
            )

    def test_confidence_level_boundaries(self):
        r = ConditionalVaRRequest(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 6, 30),
            confidence_level=0.5,
        )
        assert r.confidence_level == 0.5
        r = ConditionalVaRRequest(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 6, 30),
            confidence_level=0.999,
        )
        assert r.confidence_level == 0.999


class TestConditionalVaRResponse:
    def test_valid(self):
        r = ConditionalVaRResponse(
            analyzed_at=datetime(2026, 3, 1),
            period_start=date(2026, 3, 1),
            period_end=date(2026, 6, 30),
            confidence_level=0.95,
            loss_metric="coverage_drop",
            var_value=0.10,
            cvar_value=0.15,
            interpretation="Expected coverage drop in worst 5% of scenarios: 15%",
            tail_scenarios_count=50,
            tail_mean=0.14,
            tail_std=0.03,
            severity=RiskSeverity.HIGH,
        )
        assert r.recommendations == []
        assert r.metadata == {}
        assert r.cvar_value == 0.15
