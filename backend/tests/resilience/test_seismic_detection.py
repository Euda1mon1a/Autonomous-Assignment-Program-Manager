"""
Tests for STA/LTA seismic anomaly detection for burnout precursors.

Tests the burnout early warning system that uses seismology signal
processing algorithms to detect behavioral pattern changes.
"""

from datetime import datetime, timedelta
from uuid import uuid4

import numpy as np
import pytest

from app.resilience.seismic_detection import (
    BurnoutEarlyWarning,
    PrecursorSignal,
    SeismicAlert,
)


class TestPrecursorSignal:
    """Test PrecursorSignal enum."""

    def test_all_signal_types_defined(self):
        """Test that all expected precursor signal types exist."""
        expected_signals = {
            "swap_requests",
            "sick_calls",
            "preference_decline",
            "response_delays",
            "voluntary_coverage_decline",
        }

        actual_signals = {signal.value for signal in PrecursorSignal}
        assert actual_signals == expected_signals

    def test_signal_enum_values(self):
        """Test specific enum values."""
        assert PrecursorSignal.SWAP_REQUESTS == "swap_requests"
        assert PrecursorSignal.SICK_CALLS == "sick_calls"
        assert PrecursorSignal.PREFERENCE_DECLINE == "preference_decline"
        assert PrecursorSignal.RESPONSE_DELAYS == "response_delays"
        assert (
            PrecursorSignal.VOLUNTARY_COVERAGE_DECLINE == "voluntary_coverage_decline"
        )


class TestSeismicAlert:
    """Test SeismicAlert dataclass."""

    def test_alert_creation_minimal(self):
        """Test creating alert with minimal required fields."""
        alert = SeismicAlert(
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            sta_lta_ratio=3.5,
            trigger_time=datetime.now(),
            severity="medium",
            predicted_magnitude=5.0,
        )

        assert alert.signal_type == PrecursorSignal.SWAP_REQUESTS
        assert alert.sta_lta_ratio == 3.5
        assert alert.severity == "medium"
        assert alert.predicted_magnitude == 5.0
        assert alert.time_to_event is None
        assert alert.resident_id is None
        assert alert.context == {}

    def test_alert_creation_full(self):
        """Test creating alert with all fields."""
        resident_id = uuid4()
        trigger_time = datetime.now()
        time_to_event = timedelta(days=7)
        context = {"note": "test"}

        alert = SeismicAlert(
            signal_type=PrecursorSignal.SICK_CALLS,
            sta_lta_ratio=8.2,
            trigger_time=trigger_time,
            severity="high",
            predicted_magnitude=7.5,
            time_to_event=time_to_event,
            resident_id=resident_id,
            context=context,
        )

        assert alert.signal_type == PrecursorSignal.SICK_CALLS
        assert alert.sta_lta_ratio == 8.2
        assert alert.trigger_time == trigger_time
        assert alert.severity == "high"
        assert alert.predicted_magnitude == 7.5
        assert alert.time_to_event == time_to_event
        assert alert.resident_id == resident_id
        assert alert.context == context

    def test_alert_post_init_context(self):
        """Test that context is initialized to empty dict if None."""
        alert = SeismicAlert(
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            sta_lta_ratio=2.0,
            trigger_time=datetime.now(),
            severity="low",
            predicted_magnitude=2.0,
            context=None,
        )

        assert alert.context == {}


class TestBurnoutEarlyWarning:
    """Test BurnoutEarlyWarning class."""

    def test_initialization_default(self):
        """Test initialization with default parameters."""
        detector = BurnoutEarlyWarning()

        assert detector.short_window == 5
        assert detector.long_window == 30

    def test_initialization_custom(self):
        """Test initialization with custom parameters."""
        detector = BurnoutEarlyWarning(short_window=10, long_window=60)

        assert detector.short_window == 10
        assert detector.long_window == 60

    def test_initialization_invalid_windows(self):
        """Test that initialization fails if short >= long window."""
        with pytest.raises(ValueError, match="short_window must be < long_window"):
            BurnoutEarlyWarning(short_window=30, long_window=10)

        with pytest.raises(ValueError, match="short_window must be < long_window"):
            BurnoutEarlyWarning(short_window=20, long_window=20)

    def test_classic_sta_lta_basic(self):
        """Test classic STA/LTA computation on simple signal."""
        # Create signal with sudden increase
        data = np.concatenate(
            [
                np.ones(30),  # Baseline
                np.ones(10) * 5,  # Sudden increase
            ]
        )

        sta_lta = BurnoutEarlyWarning.classic_sta_lta(data, nsta=5, nlta=30)

        # Should be close to 1.0 during baseline
        assert sta_lta[29] < 1.5

        # Should increase significantly after spike
        assert sta_lta[35] > 2.0

    def test_classic_sta_lta_short_data(self):
        """Test classic STA/LTA with data shorter than LTA window."""
        data = np.array([1, 2, 3, 4, 5])
        sta_lta = BurnoutEarlyWarning.classic_sta_lta(data, nsta=5, nlta=30)

        # Should return zeros for too-short data
        assert np.allclose(sta_lta, 0.0)

    def test_classic_sta_lta_zero_data(self):
        """Test classic STA/LTA with all-zero data."""
        data = np.zeros(50)
        sta_lta = BurnoutEarlyWarning.classic_sta_lta(data, nsta=5, nlta=30)

        # Should return zeros when LTA is zero
        assert np.allclose(sta_lta, 0.0)

    def test_recursive_sta_lta_basic(self):
        """Test recursive STA/LTA computation."""
        # Create signal with sudden increase
        data = np.concatenate(
            [
                np.ones(30),  # Baseline
                np.ones(10) * 5,  # Sudden increase
            ]
        )

        sta_lta = BurnoutEarlyWarning.recursive_sta_lta(data, nsta=5, nlta=30)

        # Should increase after spike
        assert sta_lta[-1] > sta_lta[29]

    def test_recursive_sta_lta_empty_data(self):
        """Test recursive STA/LTA with empty array."""
        data = np.array([])
        sta_lta = BurnoutEarlyWarning.recursive_sta_lta(data, nsta=5, nlta=30)

        assert len(sta_lta) == 0

    def test_recursive_vs_classic_sta_lta(self):
        """Test that recursive and classic methods give similar results."""
        # Create realistic signal
        np.random.seed(42)
        baseline = np.random.normal(1.0, 0.2, 30)
        spike = np.random.normal(5.0, 0.5, 10)
        data = np.concatenate([baseline, spike])

        classic = BurnoutEarlyWarning.classic_sta_lta(data, nsta=5, nlta=30)
        recursive = BurnoutEarlyWarning.recursive_sta_lta(data, nsta=5, nlta=30)

        # Both should detect the spike (ratio > 1.5 after spike)
        assert classic[35] > 1.5
        assert recursive[35] > 1.5

    def test_trigger_onset_basic(self):
        """Test trigger onset detection."""
        # Create STA/LTA with clear trigger
        sta_lta = np.array(
            [
                1.0,
                1.0,
                1.0,  # Below threshold
                3.0,
                4.0,
                3.5,  # Above threshold
                0.8,
                0.8,
                0.8,  # Back below
            ]
        )

        triggers = BurnoutEarlyWarning.trigger_onset(
            sta_lta, on_threshold=2.5, off_threshold=1.0
        )

        assert len(triggers) == 1
        assert triggers[0][0] == 3  # Start at index 3
        assert triggers[0][1] == 6  # End at index 6

    def test_trigger_onset_multiple_triggers(self):
        """Test detection of multiple trigger periods."""
        sta_lta = np.array(
            [
                1.0,
                1.0,
                3.0,
                3.0,
                0.5,  # First trigger
                1.0,
                1.0,
                4.0,
                4.0,
                0.5,  # Second trigger
            ]
        )

        triggers = BurnoutEarlyWarning.trigger_onset(
            sta_lta, on_threshold=2.5, off_threshold=1.0
        )

        assert len(triggers) == 2
        assert triggers[0] == (2, 4)
        assert triggers[1] == (7, 9)

    def test_trigger_onset_still_active(self):
        """Test trigger still active at end of data."""
        sta_lta = np.array([1.0, 1.0, 3.0, 3.5, 4.0])

        triggers = BurnoutEarlyWarning.trigger_onset(
            sta_lta, on_threshold=2.5, off_threshold=1.0
        )

        assert len(triggers) == 1
        assert triggers[0][0] == 2
        assert triggers[0][1] == 4  # End at last index

    def test_trigger_onset_no_triggers(self):
        """Test when no triggers occur."""
        sta_lta = np.array([1.0, 1.1, 1.2, 1.0, 0.9])

        triggers = BurnoutEarlyWarning.trigger_onset(
            sta_lta, on_threshold=2.5, off_threshold=1.0
        )

        assert len(triggers) == 0

    def test_trigger_onset_empty_data(self):
        """Test trigger onset with empty array."""
        sta_lta = np.array([])
        triggers = BurnoutEarlyWarning.trigger_onset(sta_lta)

        assert len(triggers) == 0

    def test_detect_precursors_basic(self):
        """Test precursor detection on realistic burnout signal."""
        detector = BurnoutEarlyWarning(short_window=5, long_window=30)
        resident_id = uuid4()

        # Create realistic swap request pattern
        # Baseline: 0-1 per week, then increasing stress
        time_series = (
            [0, 1, 0, 1, 0, 0, 1, 0, 1, 0] * 3  # 30 days baseline
            + [1, 2, 2, 3, 3, 4, 5, 6, 7, 8]  # 10 days increasing
        )

        alerts = detector.detect_precursors(
            resident_id=resident_id,
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            time_series=time_series,
        )

        # Should detect at least one alert
        assert len(alerts) > 0

        # Check alert properties
        alert = alerts[0]
        assert alert.signal_type == PrecursorSignal.SWAP_REQUESTS
        assert alert.resident_id == resident_id
        assert alert.sta_lta_ratio > 2.0
        assert alert.severity in ["low", "medium", "high", "critical"]
        assert 1.0 <= alert.predicted_magnitude <= 10.0

    def test_detect_precursors_short_time_series(self):
        """Test detection with time series too short."""
        detector = BurnoutEarlyWarning(short_window=5, long_window=30)
        resident_id = uuid4()

        # Only 20 data points (less than long_window)
        time_series = [1, 2, 1, 2, 1] * 4

        alerts = detector.detect_precursors(
            resident_id=resident_id,
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            time_series=time_series,
        )

        # Should return empty list
        assert len(alerts) == 0

    def test_detect_precursors_no_anomaly(self):
        """Test detection when no anomaly exists."""
        detector = BurnoutEarlyWarning(short_window=5, long_window=30)
        resident_id = uuid4()

        # Stable baseline, no spikes
        time_series = [1.0] * 50

        alerts = detector.detect_precursors(
            resident_id=resident_id,
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            time_series=time_series,
        )

        # Should not detect any alerts
        assert len(alerts) == 0

    def test_detect_precursors_severity_levels(self):
        """Test that severity levels are correctly assigned."""
        detector = BurnoutEarlyWarning(short_window=3, long_window=20)
        resident_id = uuid4()

        # Create extreme spike
        time_series = [1.0] * 20 + [20.0] * 10

        alerts = detector.detect_precursors(
            resident_id=resident_id,
            signal_type=PrecursorSignal.SICK_CALLS,
            time_series=time_series,
        )

        assert len(alerts) > 0

        # Should be high or critical severity due to extreme spike
        alert = alerts[0]
        assert alert.severity in ["high", "critical"]
        assert alert.sta_lta_ratio >= 3.5

    def test_detect_precursors_context_data(self):
        """Test that alert context contains useful debugging data."""
        detector = BurnoutEarlyWarning(short_window=5, long_window=30)
        resident_id = uuid4()

        time_series = [1.0] * 30 + [5.0] * 10

        alerts = detector.detect_precursors(
            resident_id=resident_id,
            signal_type=PrecursorSignal.RESPONSE_DELAYS,
            time_series=time_series,
        )

        assert len(alerts) > 0

        # Check context data
        context = alerts[0].context
        assert "trigger_start_idx" in context
        assert "trigger_end_idx" in context
        assert "growth_rate" in context
        assert "window_data" in context

    def test_predict_burnout_magnitude_single_signal(self):
        """Test magnitude prediction from single signal."""
        detector = BurnoutEarlyWarning(short_window=5, long_window=30)

        signals = {PrecursorSignal.SWAP_REQUESTS: [1.0] * 30 + [5.0] * 10}

        magnitude = detector.predict_burnout_magnitude(signals)

        assert 1.0 <= magnitude <= 10.0

    def test_predict_burnout_magnitude_multiple_signals(self):
        """Test magnitude prediction from multiple signals."""
        detector = BurnoutEarlyWarning(short_window=5, long_window=30)

        signals = {
            PrecursorSignal.SWAP_REQUESTS: [1.0] * 30 + [8.0] * 10,
            PrecursorSignal.SICK_CALLS: [0.5] * 30 + [3.0] * 10,
            PrecursorSignal.RESPONSE_DELAYS: [2.0] * 30 + [10.0] * 10,
        }

        magnitude = detector.predict_burnout_magnitude(signals)

        # Multiple signals should give higher confidence
        assert magnitude > 3.0
        assert magnitude <= 10.0

    def test_predict_burnout_magnitude_empty_signals(self):
        """Test magnitude prediction with no signals."""
        detector = BurnoutEarlyWarning(short_window=5, long_window=30)

        magnitude = detector.predict_burnout_magnitude({})

        assert magnitude == 0.0

    def test_predict_burnout_magnitude_short_signals(self):
        """Test magnitude prediction when all signals too short."""
        detector = BurnoutEarlyWarning(short_window=5, long_window=30)

        signals = {
            PrecursorSignal.SWAP_REQUESTS: [1, 2, 3],  # Too short
            PrecursorSignal.SICK_CALLS: [1, 2],  # Too short
        }

        magnitude = detector.predict_burnout_magnitude(signals)

        assert magnitude == 0.0

    def test_predict_burnout_magnitude_bonus_for_multiple(self):
        """Test that multiple signals increase magnitude estimate."""
        detector = BurnoutEarlyWarning(short_window=5, long_window=30)

        # Same spike in all signals
        spike_data = [1.0] * 30 + [5.0] * 10

        single_signal = {PrecursorSignal.SWAP_REQUESTS: spike_data.copy()}

        multiple_signals = {
            PrecursorSignal.SWAP_REQUESTS: spike_data.copy(),
            PrecursorSignal.SICK_CALLS: spike_data.copy(),
            PrecursorSignal.RESPONSE_DELAYS: spike_data.copy(),
        }

        mag_single = detector.predict_burnout_magnitude(single_signal)
        mag_multiple = detector.predict_burnout_magnitude(multiple_signals)

        # Multiple signals should give higher magnitude
        assert mag_multiple > mag_single

    def test_estimate_time_to_event_basic(self):
        """Test time to event estimation."""
        detector = BurnoutEarlyWarning()

        # Current ratio of 5.0, growing at 1.0 per day
        # Critical threshold is 10.0
        # Should take ~5 days
        time_to_event = detector.estimate_time_to_event(
            sta_lta_ratio=5.0, signal_growth_rate=1.0
        )

        assert time_to_event.days == 5

    def test_estimate_time_to_event_already_critical(self):
        """Test time estimation when already at critical level."""
        detector = BurnoutEarlyWarning()

        time_to_event = detector.estimate_time_to_event(
            sta_lta_ratio=12.0,  # Already above critical
            signal_growth_rate=1.0,
        )

        # Should return minimum (1 day)
        assert time_to_event.days == 1

    def test_estimate_time_to_event_negative_growth(self):
        """Test time estimation with negative growth rate."""
        detector = BurnoutEarlyWarning()

        time_to_event = detector.estimate_time_to_event(
            sta_lta_ratio=5.0,
            signal_growth_rate=-0.5,  # Improving
        )

        # Should return large value (1 year)
        assert time_to_event.days == 365

    def test_estimate_time_to_event_zero_growth(self):
        """Test time estimation with zero growth."""
        detector = BurnoutEarlyWarning()

        time_to_event = detector.estimate_time_to_event(
            sta_lta_ratio=5.0, signal_growth_rate=0.0
        )

        assert time_to_event.days == 365

    def test_estimate_time_to_event_slow_growth(self):
        """Test time estimation with very slow growth."""
        detector = BurnoutEarlyWarning()

        # Growth of 0.01 per day would take 500 days
        # Should be clamped to 365 days
        time_to_event = detector.estimate_time_to_event(
            sta_lta_ratio=5.0, signal_growth_rate=0.01
        )

        assert time_to_event.days == 365

    def test_estimate_magnitude_signal_weights(self):
        """Test that different signals have different magnitude weights."""
        # SICK_CALLS has higher weight (1.3) than RESPONSE_DELAYS (0.9)
        mag_sick = BurnoutEarlyWarning._estimate_magnitude(
            4.0, PrecursorSignal.SICK_CALLS
        )
        mag_delays = BurnoutEarlyWarning._estimate_magnitude(
            4.0, PrecursorSignal.RESPONSE_DELAYS
        )

        # Sick calls should yield higher magnitude for same ratio
        assert mag_sick > mag_delays

    def test_estimate_magnitude_logarithmic_scale(self):
        """Test that magnitude increases logarithmically with ratio."""
        # Doubling ratio should add ~1 to magnitude (log2 scale)
        mag_2 = BurnoutEarlyWarning._estimate_magnitude(
            2.0, PrecursorSignal.SWAP_REQUESTS
        )
        mag_4 = BurnoutEarlyWarning._estimate_magnitude(
            4.0, PrecursorSignal.SWAP_REQUESTS
        )
        mag_8 = BurnoutEarlyWarning._estimate_magnitude(
            8.0, PrecursorSignal.SWAP_REQUESTS
        )

        # Should increase roughly linearly on log scale
        assert abs((mag_4 - mag_2) - (mag_8 - mag_4)) < 0.5

    def test_estimate_magnitude_bounds(self):
        """Test that magnitude is always in valid range."""
        # Very small ratio
        mag_low = BurnoutEarlyWarning._estimate_magnitude(
            0.5, PrecursorSignal.SWAP_REQUESTS
        )
        assert 1.0 <= mag_low <= 10.0

        # Very large ratio
        mag_high = BurnoutEarlyWarning._estimate_magnitude(
            100.0, PrecursorSignal.SWAP_REQUESTS
        )
        assert 1.0 <= mag_high <= 10.0


class TestIntegration:
    """Integration tests for full burnout detection workflow."""

    def test_full_detection_workflow(self):
        """Test complete workflow from data to alerts."""
        detector = BurnoutEarlyWarning(short_window=5, long_window=30)
        resident_id = uuid4()

        # Simulate 60 days of data
        # Weeks 1-4: Normal (0-2 swap requests per week)
        baseline = [0, 1, 0, 1, 0, 2, 1] * 4

        # Weeks 5-6: Increasing stress (3-5 per week)
        increasing = [2, 3, 3, 4, 4, 5, 5] * 2

        # Weeks 7-8: High stress (6-8 per week)
        high_stress = [6, 7, 7, 8, 8, 7, 6] * 2

        time_series = baseline + increasing + high_stress

        # Detect precursors
        alerts = detector.detect_precursors(
            resident_id=resident_id,
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            time_series=time_series,
        )

        # Should detect anomaly
        assert len(alerts) > 0

        # Check that severity increases with ratio
        for alert in alerts:
            if alert.sta_lta_ratio >= 10.0:
                assert alert.severity == "critical"
            elif alert.sta_lta_ratio >= 5.0:
                assert alert.severity in ["high", "critical"]

    def test_multi_signal_magnitude_prediction(self):
        """Test magnitude prediction with realistic multi-signal data."""
        detector = BurnoutEarlyWarning(short_window=5, long_window=30)

        # Create correlated burnout signals
        baseline = [1.0] * 30
        stress = [5.0] * 15

        signals = {
            PrecursorSignal.SWAP_REQUESTS: baseline + stress,
            PrecursorSignal.SICK_CALLS: baseline + [3.0] * 15,
            PrecursorSignal.RESPONSE_DELAYS: baseline + [8.0] * 15,
        }

        magnitude = detector.predict_burnout_magnitude(signals)

        # Should predict significant burnout risk
        assert magnitude >= 4.0
        assert magnitude <= 10.0

    def test_early_vs_late_detection(self):
        """Test that detector provides earlier warning as stress builds."""
        detector = BurnoutEarlyWarning(short_window=3, long_window=20)
        resident_id = uuid4()

        # Gradual increase pattern
        gradual = [1.0] * 20 + [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]

        alerts = detector.detect_precursors(
            resident_id=resident_id,
            signal_type=PrecursorSignal.PREFERENCE_DECLINE,
            time_series=gradual,
        )

        if alerts:
            # First alert should trigger before end of series
            first_alert_context = alerts[0].context
            trigger_start = first_alert_context["trigger_start_idx"]

            # Should detect before peak stress
            assert trigger_start < len(gradual) - 1
