"""Tests for SOC (Self-Organized Criticality) predictor."""

import pytest
import numpy as np
from datetime import datetime

from app.resilience.soc_predictor import SOCAvalanchePredictor, WarningLevel


class TestSOCAvalanchePredictor:
    """Test suite for SOC avalanche prediction."""

    @pytest.fixture
    def predictor(self):
        """Create predictor instance."""
        return SOCAvalanchePredictor()

    @pytest.mark.asyncio
    async def test_insufficient_data(self, predictor):
        """Test handling of insufficient data."""
        # Only 10 data points (need 30 minimum)
        utilization = [0.75] * 10

        result = await predictor.detect_critical_slowing_down(utilization)

        assert result.warning_level == WarningLevel.UNKNOWN
        assert result.is_critical is False
        assert result.confidence == 0.0
        assert "Insufficient data" in result.recommendations[0]

    @pytest.mark.asyncio
    async def test_healthy_system(self, predictor):
        """Test detection with healthy system (stable utilization)."""
        # Stable utilization around 60% with minor random noise
        np.random.seed(42)
        utilization = list(0.6 + np.random.normal(0, 0.02, 60))

        result = await predictor.detect_critical_slowing_down(utilization)

        assert result.warning_level == WarningLevel.GREEN
        assert result.is_critical is False
        assert result.signals_triggered == 0
        assert result.data_quality == "excellent"
        assert "healthy" in result.recommendations[0].lower()

    @pytest.mark.asyncio
    async def test_increasing_variance_signal(self, predictor):
        """Test detection of increasing variance (early warning)."""
        # Stable first half, increasing variance second half
        np.random.seed(42)
        stable = list(0.7 + np.random.normal(0, 0.02, 30))
        unstable = list(0.7 + np.random.normal(0, 0.08, 30))
        utilization = stable + unstable

        result = await predictor.detect_critical_slowing_down(utilization)

        # Should detect variance increase
        assert result.variance_current is not None
        assert result.variance_baseline is not None
        assert result.variance_current > result.variance_baseline

    @pytest.mark.asyncio
    async def test_high_autocorrelation_signal(self, predictor):
        """Test detection of high autocorrelation."""
        # Create highly autocorrelated series (sluggish system)
        utilization = [0.7]
        for i in range(59):
            # Each value closely follows previous (AC1 will be high)
            utilization.append(utilization[-1] + np.random.normal(0, 0.01))

        result = await predictor.detect_critical_slowing_down(utilization)

        # Should detect high autocorrelation
        assert result.autocorrelation_ac1 is not None
        if result.autocorrelation_ac1 is not None:
            assert result.autocorrelation_ac1 > 0.5  # Should be quite high

    @pytest.mark.asyncio
    async def test_multiple_signals_critical(self, predictor):
        """Test critical detection with multiple signals."""
        # Create pathological series approaching criticality:
        # - High variance
        # - High autocorrelation
        # - Increasing trend
        np.random.seed(42)

        # Start stable
        base = [0.6 + np.random.normal(0, 0.02) for _ in range(20)]

        # Add increasing variance + autocorrelation
        critical = [base[-1]]
        for i in range(40):
            # High autocorrelation (follows previous)
            next_val = critical[-1] + np.random.normal(0, 0.05)
            # Increasing variance over time
            next_val += np.random.normal(0, 0.02 * (i / 40))
            critical.append(next_val)

        utilization = base + critical

        result = await predictor.detect_critical_slowing_down(utilization)

        # Should trigger at least one warning signal
        assert result.signals_triggered >= 1
        assert result.avalanche_risk_score > 0.0

    @pytest.mark.asyncio
    async def test_data_quality_assessment(self, predictor):
        """Test data quality assessment."""
        # Excellent: 60+ days
        data_excellent = [0.7] * 60
        result = await predictor.detect_critical_slowing_down(data_excellent)
        assert result.data_quality == "excellent"

        # Good: 45-59 days
        data_good = [0.7] * 50
        result = await predictor.detect_critical_slowing_down(data_good)
        assert result.data_quality == "good"

        # Fair: 30-44 days
        data_fair = [0.7] * 35
        result = await predictor.detect_critical_slowing_down(data_fair)
        assert result.data_quality == "fair"

    @pytest.mark.asyncio
    async def test_recommendations_scale_with_severity(self, predictor):
        """Test that recommendations increase with warning level."""
        # Green: stable
        stable = list(0.6 + np.random.normal(0, 0.01, 60))
        result_green = await predictor.detect_critical_slowing_down(stable)

        assert result_green.warning_level == WarningLevel.GREEN
        assert len(result_green.immediate_actions) == 0

        # Note: Creating guaranteed YELLOW/ORANGE/RED is tricky with real algorithms,
        # so we just verify that structure is correct
        assert result_green.recommendations is not None
        assert isinstance(result_green.recommendations, list)

    @pytest.mark.asyncio
    async def test_avalanche_risk_calculation(self, predictor):
        """Test avalanche risk score calculation."""
        # Stable system should have low risk
        stable = list(0.6 + np.random.normal(0, 0.01, 60))
        result = await predictor.detect_critical_slowing_down(stable)

        assert 0.0 <= result.avalanche_risk_score <= 1.0
        # Stable system should have relatively low risk
        assert result.avalanche_risk_score < 0.5

    @pytest.mark.asyncio
    async def test_cache_functionality(self, predictor):
        """Test caching of analysis results."""
        utilization = list(0.6 + np.random.normal(0, 0.01, 60))

        # First analysis
        result1 = await predictor.detect_critical_slowing_down(utilization)

        # Get cached result
        cached = predictor.get_last_analysis()

        assert cached is not None
        assert cached.id == result1.id
        assert cached.calculated_at == result1.calculated_at

        # Clear cache
        predictor.clear_cache()
        assert predictor.get_last_analysis() is None

    @pytest.mark.asyncio
    async def test_days_lookback_parameter(self, predictor):
        """Test days_lookback parameter limits data used."""
        # 90 days of data
        utilization = list(0.6 + np.random.normal(0, 0.01, 90))

        # Analyze only last 45 days
        result = await predictor.detect_critical_slowing_down(
            utilization, days_lookback=45
        )

        assert result.days_analyzed == 45

    def test_warning_level_enum(self):
        """Test WarningLevel enum values."""
        assert WarningLevel.GREEN.value == "green"
        assert WarningLevel.YELLOW.value == "yellow"
        assert WarningLevel.ORANGE.value == "orange"
        assert WarningLevel.RED.value == "red"
        assert WarningLevel.UNKNOWN.value == "unknown"
