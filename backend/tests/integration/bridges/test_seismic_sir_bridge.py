"""
Tests for Seismic-SIR Bridge.

Tests the integration between seismic precursor detection (STA/LTA)
and SIR epidemic modeling (burnout transmission dynamics).

Mathematical formulas tested are from:
/docs/architecture/bridges/SEISMIC_SIR_BRIDGE.md
"""

from datetime import datetime, timedelta
from uuid import uuid4

import networkx as nx
import numpy as np
import pytest

from app.resilience.burnout_epidemiology import BurnoutEpidemiology
from app.resilience.seismic_detection import (
    BurnoutEarlyWarning,
    PrecursorSignal,
    SeismicAlert,
)


# Mock SeismicSIRBridge class for testing (will be implemented)
class SeismicSIRBridge:
    """
    Bridge between seismic precursor detection and SIR epidemic modeling.

    This is a test implementation based on the specification.
    """

    def __init__(
        self,
        seismic_detector: BurnoutEarlyWarning,
        epidemiology_model: BurnoutEpidemiology,
        sensitivity: float = 0.3,
        smoothing_factor: float = 0.2,
        beta_base: float = 0.05,
    ):
        """Initialize the seismic-SIR bridge."""
        if not 0 <= sensitivity <= 1:
            raise ValueError(f"sensitivity must be in [0, 1], got {sensitivity}")
        if not 0 <= smoothing_factor <= 1:
            raise ValueError(
                f"smoothing_factor must be in [0, 1], got {smoothing_factor}"
            )
        if not 0.01 <= beta_base <= 0.95:
            raise ValueError(f"beta_base must be in [0.01, 0.95], got {beta_base}")

        self.seismic_detector = seismic_detector
        self.epidemiology_model = epidemiology_model
        self.sensitivity = sensitivity
        self.smoothing_factor = smoothing_factor
        self.beta_base = beta_base

        # State tracking
        self._beta_smoothed = beta_base
        self._active_alerts = {}

    @staticmethod
    def _transform_sta_lta(ratio: float) -> float:
        """
        Transform STA/LTA ratio to beta delta using f(r) function.

        Formula from spec:
        f(r) = {
            0                           if r < 2.5    (no trigger)
            log₂(r / 2.5)              if 2.5 ≤ r < 10.0  (moderate)
            log₂(4) + 0.5×(r - 10)     if r ≥ 10.0   (critical)
        }

        Args:
            ratio: STA/LTA ratio from seismic detection

        Returns:
            Normalized beta adjustment value
        """
        if ratio < 2.5:
            # Below trigger threshold - no adjustment
            return 0.0
        elif ratio < 10.0:
            # Moderate range - logarithmic scaling
            return np.log2(ratio / 2.5)
        else:
            # Critical range - linear continuation
            return np.log2(4.0) + 0.5 * (ratio - 10.0)

    def _calculate_beta_delta(self) -> float:
        """
        Calculate aggregate beta delta from all active alerts.

        Formula from spec:
        β_total = β_base × (1 + α × Σᵢ wᵢ × f(rᵢ))

        Where:
        - wᵢ = degree(resident_i) / Σⱼ degree(resident_j)
        - f(rᵢ) = _transform_sta_lta(rᵢ)

        Returns:
            Aggregate f(r) value across all residents
        """
        if not self._active_alerts:
            return 0.0

        # Get network degrees for weighting
        network = self.epidemiology_model.network
        total_delta = 0.0
        total_weight = 0.0

        for resident_id, alert in self._active_alerts.items():
            # Transform STA/LTA to beta delta
            f_r = self._transform_sta_lta(alert.sta_lta_ratio)

            # Weight by network connectivity (super-spreaders matter more)
            if resident_id in network:
                weight = network.degree(resident_id)
            else:
                weight = 1.0

            total_delta += weight * f_r
            total_weight += weight

        # Weighted average
        if total_weight > 0:
            return total_delta / total_weight
        return 0.0

    def update_from_alerts(self, alerts: list[SeismicAlert]) -> dict:
        """
        Update SIR transmission rate based on new seismic alerts.

        Formula from spec:
        1. β_current = β_base × (1 + α × beta_delta)
        2. β_smoothed = γ × β_current + (1 - γ) × β_smoothed(t-1)
        3. β_final = clamp(β_smoothed, 0.01, 0.95)

        Args:
            alerts: List of newly detected seismic alerts

        Returns:
            Dict with beta adjustment details
        """
        # Update active alerts
        for alert in alerts:
            if alert.resident_id:
                self._active_alerts[alert.resident_id] = alert

        # Calculate beta adjustment
        beta_delta = self._calculate_beta_delta()
        beta_current = self.beta_base * (1 + self.sensitivity * beta_delta)

        # Apply smoothing (exponential moving average)
        self._beta_smoothed = (
            self.smoothing_factor * beta_current
            + (1 - self.smoothing_factor) * self._beta_smoothed
        )

        # Clamp to valid range
        beta_final = np.clip(self._beta_smoothed, 0.01, 0.95)

        # Record the adjustment
        adjustment_magnitude = (beta_final - self.beta_base) / self.beta_base * 100

        return {
            "beta_base": self.beta_base,
            "beta_adjusted": beta_final,
            "beta_current": beta_current,
            "beta_smoothed": self._beta_smoothed,
            "beta_delta": beta_delta,
            "num_active_alerts": len(self._active_alerts),
            "adjustment_magnitude": adjustment_magnitude,
        }

    def get_current_beta(self) -> float:
        """Get current smoothed beta value."""
        return self._beta_smoothed


@pytest.fixture
def network():
    """Create test social network with varying degrees."""
    G = nx.Graph()
    residents = [uuid4() for _ in range(10)]
    G.add_nodes_from(residents)

    # Create network with varying connectivity
    # Resident 0: hub (degree 5)
    for i in range(1, 6):
        G.add_edge(residents[0], residents[i])

    # Resident 1: medium connectivity (degree 3)
    G.add_edge(residents[1], residents[6])
    G.add_edge(residents[1], residents[7])

    # Remaining: low connectivity (degree 1-2)
    for i in range(2, 9):
        G.add_edge(residents[i], residents[i + 1])

    return G


@pytest.fixture
def seismic_detector():
    """Create seismic detector."""
    return BurnoutEarlyWarning(short_window=5, long_window=30)


@pytest.fixture
def epi_model(network):
    """Create epidemiology model."""
    return BurnoutEpidemiology(social_network=network)


@pytest.fixture
def bridge(seismic_detector, epi_model):
    """Create seismic-SIR bridge."""
    return SeismicSIRBridge(
        seismic_detector=seismic_detector,
        epidemiology_model=epi_model,
        sensitivity=0.3,
        smoothing_factor=0.2,
        beta_base=0.05,
    )


class TestSTALTATransformation:
    """Test STA/LTA to beta transformation function."""

    def test_transform_below_threshold(self, bridge):
        """Test f(r) returns 0 for ratios below 2.5 threshold."""
        # Test values below threshold
        assert bridge._transform_sta_lta(0.0) == 0.0
        assert bridge._transform_sta_lta(1.0) == 0.0
        assert bridge._transform_sta_lta(2.0) == 0.0
        assert bridge._transform_sta_lta(2.49) == 0.0

        # Boundary: exactly at threshold should still trigger
        assert bridge._transform_sta_lta(2.5) == 0.0

    def test_transform_moderate_range(self, bridge):
        """Test f(r) logarithmic scaling in moderate range (2.5-10.0)."""
        # f(r) = log₂(r / 2.5)

        # At r=5.0: log₂(5.0 / 2.5) = log₂(2) = 1.0
        assert bridge._transform_sta_lta(5.0) == pytest.approx(1.0, rel=0.01)

        # At r=10.0: log₂(10.0 / 2.5) = log₂(4) = 2.0
        assert bridge._transform_sta_lta(10.0) == pytest.approx(2.0, rel=0.01)

        # At r=7.5: log₂(7.5 / 2.5) = log₂(3) ≈ 1.585
        result = bridge._transform_sta_lta(7.5)
        expected = np.log2(7.5 / 2.5)
        assert result == pytest.approx(expected, rel=0.01)

    def test_transform_critical_range(self, bridge):
        """Test f(r) linear continuation in critical range (≥10.0)."""
        # f(r) = log₂(4) + 0.5 × (r - 10)

        # At r=10.0: log₂(4) + 0.5 × 0 = 2.0
        assert bridge._transform_sta_lta(10.0) == pytest.approx(2.0, rel=0.01)

        # At r=15.0: log₂(4) + 0.5 × 5 = 2.0 + 2.5 = 4.5
        assert bridge._transform_sta_lta(15.0) == pytest.approx(4.5, rel=0.01)

        # At r=20.0: log₂(4) + 0.5 × 10 = 2.0 + 5.0 = 7.0
        assert bridge._transform_sta_lta(20.0) == pytest.approx(7.0, rel=0.01)

        # Linear increment: should increase by 0.5 per unit
        f_15 = bridge._transform_sta_lta(15.0)
        f_16 = bridge._transform_sta_lta(16.0)
        assert (f_16 - f_15) == pytest.approx(0.5, rel=0.01)

    def test_transform_normal_elevation(self, bridge):
        """Test transformation for normal STA/LTA elevation."""
        # Typical moderate alert: ratio=3.5
        # f(3.5) = log₂(3.5 / 2.5) = log₂(1.4) ≈ 0.485
        result = bridge._transform_sta_lta(3.5)
        expected = np.log2(3.5 / 2.5)
        assert result == pytest.approx(expected, abs=0.01)
        assert 0.4 < result < 0.6  # Sanity check

    def test_transform_elevated_precursor(self, bridge):
        """Test transformation for elevated STA/LTA ratio."""
        # Strong precursor signal: ratio=8.0
        # f(8.0) = log₂(8.0 / 2.5) = log₂(3.2) ≈ 1.678
        result = bridge._transform_sta_lta(8.0)
        expected = np.log2(8.0 / 2.5)
        assert result == pytest.approx(expected, rel=0.01)
        assert 1.6 < result < 1.8

    def test_transform_critical_precursor(self, bridge):
        """Test transformation for critical STA/LTA ratio."""
        # Critical signal: ratio=18.0
        # f(18.0) = log₂(4) + 0.5 × (18 - 10) = 2.0 + 4.0 = 6.0
        result = bridge._transform_sta_lta(18.0)
        assert result == pytest.approx(6.0, rel=0.01)


class TestMultiResidentAggregation:
    """Test degree-weighted aggregation across multiple residents."""

    def test_single_alert_aggregation(self, bridge, network):
        """Test aggregation with single alert."""
        residents = list(network.nodes())

        alert = SeismicAlert(
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            sta_lta_ratio=5.0,  # f(5.0) = 1.0
            trigger_time=datetime.now(),
            severity="medium",
            predicted_magnitude=4.0,
            resident_id=residents[0],
        )

        bridge._active_alerts[alert.resident_id] = alert
        delta = bridge._calculate_beta_delta()

        # With single alert, weight doesn't matter (normalized to 1)
        # delta = f(5.0) = 1.0
        assert delta == pytest.approx(1.0, rel=0.01)

    def test_degree_weighted_averaging(self, bridge, network):
        """Test that higher-degree residents get higher weights."""
        residents = list(network.nodes())

        # Resident 0: hub with degree=5, ratio=8.0 → f(8.0) ≈ 1.678
        # Resident 9: low degree=1, ratio=4.0 → f(4.0) ≈ 0.678
        alert_hub = SeismicAlert(
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            sta_lta_ratio=8.0,
            trigger_time=datetime.now(),
            severity="high",
            predicted_magnitude=5.0,
            resident_id=residents[0],  # High degree node
        )

        alert_low = SeismicAlert(
            signal_type=PrecursorSignal.SICK_CALLS,
            sta_lta_ratio=4.0,
            trigger_time=datetime.now(),
            severity="medium",
            predicted_magnitude=3.5,
            resident_id=residents[9],  # Low degree node
        )

        bridge._active_alerts[alert_hub.resident_id] = alert_hub
        bridge._active_alerts[alert_low.resident_id] = alert_low

        delta = bridge._calculate_beta_delta()

        # Weighted average: (w_hub × f_hub + w_low × f_low) / (w_hub + w_low)
        # w_hub = degree(0) = 5, w_low = degree(9) = 1
        f_hub = bridge._transform_sta_lta(8.0)
        f_low = bridge._transform_sta_lta(4.0)
        expected = (5 * f_hub + 1 * f_low) / (5 + 1)

        assert delta == pytest.approx(expected, rel=0.01)

        # Hub's signal should dominate (higher weight)
        assert delta > f_low
        assert delta < f_hub  # But not as high as hub alone

    def test_three_residents_different_degrees(self, bridge, network):
        """Test aggregation with three residents of different connectivity."""
        residents = list(network.nodes())

        # Create alerts for residents with different degrees
        alerts = [
            SeismicAlert(
                signal_type=PrecursorSignal.SWAP_REQUESTS,
                sta_lta_ratio=6.0,  # f(6.0) = log₂(2.4) ≈ 1.263
                trigger_time=datetime.now(),
                severity="medium",
                predicted_magnitude=4.5,
                resident_id=residents[0],  # degree=5
            ),
            SeismicAlert(
                signal_type=PrecursorSignal.SICK_CALLS,
                sta_lta_ratio=5.0,  # f(5.0) = 1.0
                trigger_time=datetime.now(),
                severity="medium",
                predicted_magnitude=4.0,
                resident_id=residents[1],  # degree=3
            ),
            SeismicAlert(
                signal_type=PrecursorSignal.RESPONSE_DELAYS,
                sta_lta_ratio=4.0,  # f(4.0) ≈ 0.678
                trigger_time=datetime.now(),
                severity="low",
                predicted_magnitude=3.0,
                resident_id=residents[5],  # degree=1
            ),
        ]

        for alert in alerts:
            bridge._active_alerts[alert.resident_id] = alert

        delta = bridge._calculate_beta_delta()

        # Calculate expected weighted average
        degrees = [network.degree(residents[i]) for i in [0, 1, 5]]
        f_values = [bridge._transform_sta_lta(r) for r in [6.0, 5.0, 4.0]]
        expected = sum(d * f for d, f in zip(degrees, f_values)) / sum(degrees)

        assert delta == pytest.approx(expected, rel=0.01)


class TestSmoothingPreventsOscillation:
    """Test that exponential moving average smoothing prevents rapid changes."""

    def test_smoothing_gradual_increase(self, bridge, network):
        """Test that beta increases gradually, not instantly."""
        residents = list(network.nodes())

        # First update: moderate alert
        alert1 = SeismicAlert(
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            sta_lta_ratio=5.0,  # f(5.0) = 1.0
            trigger_time=datetime.now(),
            severity="medium",
            predicted_magnitude=4.0,
            resident_id=residents[0],
        )

        result1 = bridge.update_from_alerts([alert1])
        beta_after_first = result1["beta_adjusted"]

        # Beta should increase from baseline
        assert beta_after_first > bridge.beta_base

        # Second update: higher alert (should increase further but gradually)
        alert2 = SeismicAlert(
            signal_type=PrecursorSignal.SICK_CALLS,
            sta_lta_ratio=10.0,  # f(10.0) = 2.0
            trigger_time=datetime.now(),
            severity="high",
            predicted_magnitude=6.0,
            resident_id=residents[1],
        )

        result2 = bridge.update_from_alerts([alert2])
        beta_after_second = result2["beta_adjusted"]

        # Beta should increase but not jump to maximum
        assert beta_after_second > beta_after_first

        # With smoothing_factor=0.2, change should be gradual
        # The increase should be less than if no smoothing applied
        beta_change = beta_after_second - beta_after_first
        assert beta_change < 0.05  # Not a huge jump

    def test_smoothing_factor_effect(self, seismic_detector, epi_model):
        """Test that smoothing_factor controls response speed."""
        # Create two bridges with different smoothing factors
        bridge_fast = SeismicSIRBridge(
            seismic_detector=seismic_detector,
            epidemiology_model=epi_model,
            sensitivity=0.3,
            smoothing_factor=0.8,  # Fast response (80% weight on new)
            beta_base=0.05,
        )

        bridge_slow = SeismicSIRBridge(
            seismic_detector=seismic_detector,
            epidemiology_model=epi_model,
            sensitivity=0.3,
            smoothing_factor=0.1,  # Slow response (10% weight on new)
            beta_base=0.05,
        )

        # Same alert to both
        alert = SeismicAlert(
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            sta_lta_ratio=8.0,
            trigger_time=datetime.now(),
            severity="high",
            predicted_magnitude=5.0,
            resident_id=uuid4(),
        )

        result_fast = bridge_fast.update_from_alerts([alert])
        result_slow = bridge_slow.update_from_alerts([alert])

        # Fast bridge should respond more strongly
        assert result_fast["beta_adjusted"] > result_slow["beta_adjusted"]

        # Both should be above baseline
        assert result_fast["beta_adjusted"] > 0.05
        assert result_slow["beta_adjusted"] > 0.05


class TestBetaClamping:
    """Test that beta is clamped to valid range [0.01, 0.95]."""

    def test_beta_clamped_to_maximum(self, bridge, network):
        """Test that beta never exceeds 0.95."""
        residents = list(network.nodes())

        # Create extreme alerts that would push beta > 0.95
        extreme_alerts = [
            SeismicAlert(
                signal_type=PrecursorSignal.SICK_CALLS,
                sta_lta_ratio=50.0,  # Extremely high
                trigger_time=datetime.now(),
                severity="critical",
                predicted_magnitude=10.0,
                resident_id=residents[i],
            )
            for i in range(5)
        ]

        result = bridge.update_from_alerts(extreme_alerts)

        # Beta should be clamped to max
        assert result["beta_adjusted"] <= 0.95
        assert result["beta_adjusted"] >= 0.01

    def test_beta_clamped_to_minimum(self, seismic_detector, epi_model):
        """Test that beta never goes below 0.01."""
        # Create bridge with very low baseline
        bridge = SeismicSIRBridge(
            seismic_detector=seismic_detector,
            epidemiology_model=epi_model,
            sensitivity=0.0,  # No sensitivity to alerts
            smoothing_factor=0.2,
            beta_base=0.01,  # At minimum
        )

        # Even with no alerts, beta should stay at minimum
        result = bridge.update_from_alerts([])

        assert result["beta_adjusted"] >= 0.01
        assert result["beta_adjusted"] <= 0.95

    def test_multiple_updates_stay_in_bounds(self, bridge, network):
        """Test that beta stays in bounds over multiple updates."""
        residents = list(network.nodes())

        # Simulate multiple update cycles with varying intensities
        for i in range(10):
            ratio = 3.0 + i * 2.0  # Increasing from 3 to 21
            alert = SeismicAlert(
                signal_type=PrecursorSignal.SWAP_REQUESTS,
                sta_lta_ratio=ratio,
                trigger_time=datetime.now(),
                severity="high",
                predicted_magnitude=5.0,
                resident_id=residents[i % len(residents)],
            )

            result = bridge.update_from_alerts([alert])

            # Always in bounds
            assert 0.01 <= result["beta_adjusted"] <= 0.95

    def test_beta_calculation_components(self, bridge, network):
        """Test that beta calculation follows the formula correctly."""
        residents = list(network.nodes())

        alert = SeismicAlert(
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            sta_lta_ratio=5.0,  # f(5.0) = 1.0
            trigger_time=datetime.now(),
            severity="medium",
            predicted_magnitude=4.0,
            resident_id=residents[0],
        )

        result = bridge.update_from_alerts([alert])

        # Verify formula: β_current = β_base × (1 + α × beta_delta)
        # beta_delta = f(5.0) = 1.0 (with single alert, no weighting needed)
        # β_current = 0.05 × (1 + 0.3 × 1.0) = 0.05 × 1.3 = 0.065

        # With smoothing (first update): β_smoothed = γ × β_current + (1-γ) × β_base
        # β_smoothed = 0.2 × 0.065 + 0.8 × 0.05 = 0.013 + 0.040 = 0.053

        expected_current = 0.05 * (1 + 0.3 * 1.0)
        expected_smoothed = 0.2 * expected_current + 0.8 * 0.05

        assert result["beta_current"] == pytest.approx(expected_current, rel=0.01)
        assert result["beta_smoothed"] == pytest.approx(expected_smoothed, rel=0.01)
        assert result["beta_adjusted"] == pytest.approx(expected_smoothed, rel=0.01)


class TestBridgeIntegration:
    """Integration tests for full seismic-SIR pipeline."""

    def test_end_to_end_beta_adjustment(self, bridge, network):
        """Test complete workflow from alerts to beta adjustment."""
        residents = list(network.nodes())

        # Scenario: Multiple residents showing stress signals
        alerts = [
            SeismicAlert(
                signal_type=PrecursorSignal.SWAP_REQUESTS,
                sta_lta_ratio=6.0,
                trigger_time=datetime.now(),
                severity="medium",
                predicted_magnitude=4.5,
                resident_id=residents[0],
            ),
            SeismicAlert(
                signal_type=PrecursorSignal.SICK_CALLS,
                sta_lta_ratio=8.0,
                trigger_time=datetime.now(),
                severity="high",
                predicted_magnitude=5.5,
                resident_id=residents[1],
            ),
        ]

        result = bridge.update_from_alerts(alerts)

        # Verify all expected fields present
        assert "beta_base" in result
        assert "beta_adjusted" in result
        assert "beta_current" in result
        assert "num_active_alerts" in result
        assert "adjustment_magnitude" in result

        # Verify beta increased from baseline
        assert result["beta_adjusted"] > result["beta_base"]

        # Verify alerts are tracked
        assert result["num_active_alerts"] == 2

        # Verify current beta matches
        assert bridge.get_current_beta() == result["beta_adjusted"]

    def test_no_alerts_no_adjustment(self, bridge):
        """Test that no alerts means no beta adjustment."""
        result = bridge.update_from_alerts([])

        # Beta should remain at baseline
        assert result["beta_adjusted"] == pytest.approx(bridge.beta_base, rel=0.01)
        assert result["num_active_alerts"] == 0
        assert abs(result["adjustment_magnitude"]) < 1.0  # Minimal change

    def test_parameter_validation(self, seismic_detector, epi_model):
        """Test that invalid parameters raise errors."""
        # Invalid sensitivity
        with pytest.raises(ValueError, match="sensitivity"):
            SeismicSIRBridge(
                seismic_detector,
                epi_model,
                sensitivity=1.5,  # > 1.0
            )

        # Invalid smoothing_factor
        with pytest.raises(ValueError, match="smoothing_factor"):
            SeismicSIRBridge(
                seismic_detector,
                epi_model,
                smoothing_factor=-0.1,  # < 0.0
            )

        # Invalid beta_base
        with pytest.raises(ValueError, match="beta_base"):
            SeismicSIRBridge(
                seismic_detector,
                epi_model,
                beta_base=1.0,  # > 0.95
            )
