"""
Tests for Fourier analysis tools.

These tests verify the FFT-based periodicity detection, harmonic resonance
analysis, and spectral entropy calculations.
"""

import numpy as np
import pytest


# Mock test - actual tests will run once numpy is available in test environment
class TestFourierAnalysisTools:
    """Test suite for Fourier analysis MCP tools."""

    @pytest.mark.asyncio
    async def test_detect_schedule_cycles_weekly_pattern(self):
        """Test detection of 7-day weekly pattern."""
        # Import here to avoid module-level import errors if numpy not installed
        try:
            from scheduler_mcp.tools.fourier_analysis_tools import detect_schedule_cycles
        except ImportError:
            pytest.skip("Numpy not available")

        # Create synthetic 7-day periodic signal (4 weeks)
        days = 28
        signal = [40 + 10 * np.sin(2 * np.pi * i / 7) for i in range(days)]

        result = await detect_schedule_cycles(signal)

        assert result.periodicity_detected is True
        assert result.dominant_period_days is not None
        # Should detect ~7-day period (allow some tolerance)
        assert 6.0 <= result.dominant_period_days <= 8.0
        assert result.signal_length_days == days

    @pytest.mark.asyncio
    async def test_detect_schedule_cycles_too_short(self):
        """Test handling of signal that's too short."""
        try:
            from scheduler_mcp.tools.fourier_analysis_tools import detect_schedule_cycles
        except ImportError:
            pytest.skip("Numpy not available")

        # Signal too short (< 7 samples)
        signal = [1.0, 2.0, 3.0]

        result = await detect_schedule_cycles(signal)

        assert result.periodicity_detected is False
        assert result.dominant_period_days is None
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_detect_schedule_cycles_all_zeros(self):
        """Test handling of all-zero signal."""
        try:
            from scheduler_mcp.tools.fourier_analysis_tools import detect_schedule_cycles
        except ImportError:
            pytest.skip("Numpy not available")

        # All zeros
        signal = [0.0] * 14

        result = await detect_schedule_cycles(signal)

        assert result.periodicity_detected is False
        assert result.dominant_period_days is None

    @pytest.mark.asyncio
    async def test_analyze_harmonic_resonance_weekly_aligned(self):
        """Test resonance analysis with ACGME-aligned signal."""
        try:
            from scheduler_mcp.tools.fourier_analysis_tools import (
                analyze_harmonic_resonance,
            )
        except ImportError:
            pytest.skip("Numpy not available")

        # Perfect 7-day cycle (aligned with ACGME weekly)
        days = 28
        signal = [40 + 10 * np.sin(2 * np.pi * i / 7) for i in range(days)]

        result = await analyze_harmonic_resonance(signal)

        # Should have strong 7-day alignment
        assert result.acgme_7d_alignment > 0.5
        assert result.overall_resonance > 0.3
        assert result.health_status in ["healthy", "degraded", "critical"]

    @pytest.mark.asyncio
    async def test_analyze_harmonic_resonance_dissonant(self):
        """Test resonance analysis with non-ACGME period."""
        try:
            from scheduler_mcp.tools.fourier_analysis_tools import (
                analyze_harmonic_resonance,
            )
        except ImportError:
            pytest.skip("Numpy not available")

        # 5-day cycle (not aligned with ACGME 7/14/28)
        days = 30
        signal = [40 + 10 * np.sin(2 * np.pi * i / 5) for i in range(days)]

        result = await analyze_harmonic_resonance(signal)

        # Should have weak ACGME alignment
        assert result.overall_resonance < 0.7
        # Should detect dissonant frequencies
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_calculate_spectral_entropy_simple_signal(self):
        """Test entropy calculation for simple periodic signal."""
        try:
            from scheduler_mcp.tools.fourier_analysis_tools import (
                calculate_spectral_entropy,
            )
        except ImportError:
            pytest.skip("Numpy not available")

        # Pure sinusoid - should have low entropy
        days = 28
        signal = [40 + 10 * np.sin(2 * np.pi * i / 7) for i in range(days)]

        result = await calculate_spectral_entropy(signal)

        # Pure sinusoid should have low entropy
        assert result.spectral_entropy < 0.5
        assert result.signal_complexity in ["simple", "moderate"]
        assert result.predictability in ["high", "moderate"]

    @pytest.mark.asyncio
    async def test_calculate_spectral_entropy_complex_signal(self):
        """Test entropy calculation for complex multi-frequency signal."""
        try:
            from scheduler_mcp.tools.fourier_analysis_tools import (
                calculate_spectral_entropy,
            )
        except ImportError:
            pytest.skip("Numpy not available")

        # Multi-frequency signal - should have higher entropy
        days = 56
        signal = [
            40
            + 10 * np.sin(2 * np.pi * i / 7)
            + 5 * np.sin(2 * np.pi * i / 3)
            + 3 * np.sin(2 * np.pi * i / 11)
            for i in range(days)
        ]

        result = await calculate_spectral_entropy(signal)

        # Multi-frequency should have higher entropy than pure sinusoid
        assert result.spectral_entropy > 0.3
        assert result.dominant_frequencies_count >= 3

    @pytest.mark.asyncio
    async def test_calculate_spectral_entropy_white_noise(self):
        """Test entropy calculation for noisy signal."""
        try:
            from scheduler_mcp.tools.fourier_analysis_tools import (
                calculate_spectral_entropy,
            )
        except ImportError:
            pytest.skip("Numpy not available")

        # Random white noise - should have high entropy
        np.random.seed(42)
        days = 56
        signal = list(np.random.randn(days) * 10 + 40)

        result = await calculate_spectral_entropy(signal)

        # White noise should have high entropy
        assert result.spectral_entropy > 0.6
        assert result.signal_complexity in ["complex", "chaotic"]
        assert result.predictability in ["low", "very low"]

    @pytest.mark.asyncio
    async def test_calculate_spectral_entropy_flat_signal(self):
        """Test entropy calculation for flat (constant) signal."""
        try:
            from scheduler_mcp.tools.fourier_analysis_tools import (
                calculate_spectral_entropy,
            )
        except ImportError:
            pytest.skip("Numpy not available")

        # Constant signal (no variation)
        signal = [40.0] * 28

        result = await calculate_spectral_entropy(signal)

        # Flat signal should have very low/zero entropy
        assert result.spectral_entropy < 0.2
        assert result.frequency_concentration > 0.8
