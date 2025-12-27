"""
Tests for Three-Process Model of Alertness.

Tests cover:
- State management (create, update wakefulness, update sleep)
- Effectiveness calculation (homeostatic, circadian, sleep inertia)
- WOCL detection and risk multipliers
- Shift prediction functionality
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.frms.three_process_model import (
    ThreeProcessModel,
    AlertnessState,
    EffectivenessScore,
    CircadianPhase,
    SleepInertiaState,
)


class TestThreeProcessModel:
    """Test suite for ThreeProcessModel."""

    @pytest.fixture
    def model(self):
        """Create a fresh model instance."""
        return ThreeProcessModel()

    @pytest.fixture
    def person_id(self):
        """Create a test person ID."""
        return uuid4()

    def test_create_state_fully_rested(self, model, person_id):
        """Test creating a fully rested alertness state."""
        state = model.create_state(person_id, initial_reservoir=100.0)

        assert state.person_id == person_id
        assert state.sleep_reservoir == 100.0
        assert state.hours_awake == 0.0
        assert state.cumulative_debt == 0.0
        assert state.effectiveness is not None
        assert state.effectiveness.overall >= 90.0

    def test_create_state_with_custom_reservoir(self, model, person_id):
        """Test creating state with depleted reservoir."""
        state = model.create_state(person_id, initial_reservoir=60.0)

        assert state.sleep_reservoir == 60.0
        assert state.effectiveness.overall < 90.0

    def test_update_wakefulness_depletes_reservoir(self, model, person_id):
        """Test that wakefulness depletes sleep reservoir."""
        state = model.create_state(person_id)
        initial_reservoir = state.sleep_reservoir

        # Update for 4 hours of wakefulness
        new_state = model.update_wakefulness(state, hours=4.0)

        assert new_state.sleep_reservoir < initial_reservoir
        assert new_state.hours_awake == 4.0
        assert new_state.timestamp > state.timestamp

    def test_update_wakefulness_extended_depletes_more(self, model, person_id):
        """Test that extended wakefulness causes more depletion."""
        state = model.create_state(person_id)

        # 4 hours of wakefulness
        state_4h = model.update_wakefulness(state, hours=4.0)

        # 16 hours of wakefulness from original
        state_16h = model.update_wakefulness(state, hours=16.0)

        assert state_16h.sleep_reservoir < state_4h.sleep_reservoir
        assert state_16h.effectiveness.overall < state_4h.effectiveness.overall

    def test_update_sleep_restores_reservoir(self, model, person_id):
        """Test that sleep restores the reservoir."""
        state = model.create_state(person_id)

        # Deplete with wakefulness
        depleted_state = model.update_wakefulness(state, hours=16.0)
        depleted_reservoir = depleted_state.sleep_reservoir

        # Restore with sleep
        restored_state = model.update_sleep(depleted_state, hours=8.0)

        assert restored_state.sleep_reservoir > depleted_reservoir
        assert restored_state.hours_awake == 0.0
        assert restored_state.last_sleep_end is not None

    def test_update_sleep_quality_affects_recovery(self, model, person_id):
        """Test that sleep quality affects recovery rate."""
        state = model.create_state(person_id)
        depleted = model.update_wakefulness(state, hours=16.0)

        # Good quality sleep
        good_sleep = model.update_sleep(depleted, hours=8.0, quality=1.0)

        # Poor quality sleep
        poor_sleep = model.update_sleep(depleted, hours=8.0, quality=0.5)

        assert good_sleep.sleep_reservoir > poor_sleep.sleep_reservoir

    def test_circadian_phase_wocl(self, model, person_id):
        """Test WOCL detection at 4:00 AM."""
        timestamp = datetime(2025, 1, 15, 4, 0, 0)  # 4:00 AM
        state = model.create_state(person_id, timestamp=timestamp)

        assert state.circadian_phase == CircadianPhase.WOCL
        assert model.is_in_wocl(4.0)

    def test_circadian_phase_morning_peak(self, model, person_id):
        """Test morning peak at 10:00 AM."""
        timestamp = datetime(2025, 1, 15, 10, 0, 0)  # 10:00 AM
        state = model.create_state(person_id, timestamp=timestamp)

        assert state.circadian_phase == CircadianPhase.MORNING_PEAK
        assert not model.is_in_wocl(10.0)

    def test_wocl_risk_multiplier(self, model):
        """Test WOCL risk multiplier is highest at 4 AM."""
        # At WOCL center (4 AM)
        multiplier_4am = model.get_wocl_risk_multiplier(4.0)

        # At WOCL edge (2 AM)
        multiplier_2am = model.get_wocl_risk_multiplier(2.0)

        # Outside WOCL (10 AM)
        multiplier_10am = model.get_wocl_risk_multiplier(10.0)

        assert multiplier_4am > multiplier_2am
        assert multiplier_2am > multiplier_10am
        assert multiplier_10am == 1.0

    def test_effectiveness_includes_all_components(self, model, person_id):
        """Test that effectiveness score includes all components."""
        state = model.create_state(person_id)
        score = model.calculate_effectiveness(state)

        assert hasattr(score, "overall")
        assert hasattr(score, "homeostatic")
        assert hasattr(score, "circadian")
        assert hasattr(score, "sleep_inertia")
        assert hasattr(score, "risk_level")
        assert hasattr(score, "factors")

    def test_effectiveness_risk_levels(self, model, person_id):
        """Test that risk levels are correctly assigned."""
        # Fully rested = optimal
        state = model.create_state(person_id, initial_reservoir=100.0)
        score = model.calculate_effectiveness(state)
        # Risk level depends on time of day and all factors
        assert score.risk_level in ["optimal", "acceptable"]

        # Severely depleted = high risk
        state = model.create_state(person_id, initial_reservoir=40.0)
        score = model.calculate_effectiveness(state)
        assert score.risk_level in ["high_risk", "unacceptable", "critical", "caution"]

    def test_sleep_inertia_immediately_after_wake(self, model, person_id):
        """Test sleep inertia penalty immediately after waking."""
        state = model.create_state(person_id)

        # Simulate sleep ending just now
        state = model.update_sleep(state, hours=8.0)

        # Check effectiveness right after waking
        score = model.calculate_effectiveness(state)

        # Sleep inertia should be present
        assert score.sleep_inertia > 0

    def test_sleep_inertia_resolves_after_30_minutes(self, model, person_id):
        """Test sleep inertia resolves after 30 minutes."""
        state = model.create_state(person_id)
        state = model.update_sleep(state, hours=8.0)

        # After 30 minutes awake
        state = model.update_wakefulness(state, hours=0.5)
        score = model.calculate_effectiveness(state)

        # Sleep inertia should be minimal
        assert score.sleep_inertia < 5.0

    def test_max_shift_duration_by_start_time(self, model):
        """Test that max shift duration varies by start time."""
        # Favorable (morning)
        morning = model.calculate_max_shift_duration(8.0, base_duration=12.0)

        # Unfavorable (evening)
        evening = model.calculate_max_shift_duration(20.0, base_duration=12.0)

        # Highly unfavorable (night)
        night = model.calculate_max_shift_duration(2.0, base_duration=12.0)

        assert morning == 12.0
        assert evening == 10.0  # 12 - 2
        assert night == 8.0  # 12 - 4

    def test_predict_shift_effectiveness(self, model, person_id):
        """Test shift effectiveness prediction."""
        state = model.create_state(person_id)
        shift_start = datetime.now()

        predictions = model.predict_shift_effectiveness(
            state=state,
            shift_start=shift_start,
            shift_duration_hours=12.0,
            sample_interval_minutes=60,  # Hourly samples
        )

        # Should have 13 samples (0, 1, 2, ..., 12 hours)
        assert len(predictions) >= 12

        # Each prediction should have timestamp and score
        for timestamp, score in predictions:
            assert isinstance(timestamp, datetime)
            assert isinstance(score, EffectivenessScore)
            assert 0 <= score.overall <= 100

        # Effectiveness should generally decrease over shift
        start_effectiveness = predictions[0][1].overall
        end_effectiveness = predictions[-1][1].overall
        assert end_effectiveness < start_effectiveness

    def test_shift_summary(self, model, person_id):
        """Test shift summary generation."""
        state = model.create_state(person_id)
        predictions = model.predict_shift_effectiveness(
            state=state,
            shift_start=datetime.now(),
            shift_duration_hours=12.0,
        )

        summary = model.get_shift_summary(predictions)

        assert "effectiveness" in summary
        assert "risk_distribution" in summary
        assert "wocl_exposure" in summary
        assert "recommendations" in summary

        assert "minimum" in summary["effectiveness"]
        assert "maximum" in summary["effectiveness"]
        assert "mean" in summary["effectiveness"]

    def test_cumulative_debt_accumulates(self, model, person_id):
        """Test that cumulative debt accumulates over days."""
        state = model.create_state(person_id)

        # Simulate multiple days with insufficient sleep
        for _ in range(5):
            # 16 hours awake
            state = model.update_wakefulness(state, hours=16.0)
            # Only 5 hours sleep (deficit)
            state = model.update_sleep(state, hours=5.0)

        # Should have accumulated debt
        assert state.cumulative_debt > 0

    def test_effectiveness_score_serialization(self, model, person_id):
        """Test that effectiveness score can be serialized."""
        state = model.create_state(person_id)
        score = model.calculate_effectiveness(state)

        score_dict = score.to_dict()

        assert "overall" in score_dict
        assert "components" in score_dict
        assert "timestamp" in score_dict
        assert "risk_level" in score_dict
        assert "factors" in score_dict

    def test_alertness_state_serialization(self, model, person_id):
        """Test that alertness state can be serialized."""
        state = model.create_state(person_id)
        state = model.update_wakefulness(state, hours=4.0)

        state_dict = state.to_dict()

        assert "person_id" in state_dict
        assert "sleep_reservoir" in state_dict
        assert "hours_awake" in state_dict
        assert "circadian_phase" in state_dict
        assert "effectiveness" in state_dict


class TestCircadianComponent:
    """Tests for circadian rhythm component."""

    @pytest.fixture
    def model(self):
        return ThreeProcessModel()

    def test_circadian_minimum_at_4am(self, model):
        """Test that circadian alertness is minimum around 4 AM."""
        values = [model._circadian_component(h) for h in range(24)]

        # Minimum should be around hour 4
        min_hour = values.index(min(values))
        assert 3 <= min_hour <= 5

    def test_circadian_maximum_in_afternoon(self, model):
        """Test that circadian alertness peaks in afternoon."""
        values = [model._circadian_component(h) for h in range(24)]

        # Maximum should be in afternoon (roughly 12 hours from minimum)
        max_hour = values.index(max(values))
        assert 14 <= max_hour <= 18

    def test_circadian_24_hour_cycle(self, model):
        """Test that circadian has 24-hour periodicity."""
        # Value at hour 0 should be close to value at hour 24
        val_0 = model._circadian_component(0.0)
        val_24 = model._circadian_component(24.0)

        # Allow for small numerical differences
        assert abs(val_0 - val_24) < 0.01


class TestModelCalibration:
    """Tests for model calibration functionality."""

    def test_custom_calibration(self):
        """Test that model accepts custom calibration parameters."""
        custom_params = {
            "tau_wake": 20.0,  # Custom time constant
            "threshold_faa_caution": 80.0,  # Stricter threshold
        }

        model = ThreeProcessModel(calibration=custom_params)

        assert model.TAU_WAKE == 20.0
        assert model.THRESHOLD_FAA_CAUTION == 80.0

    def test_default_parameters(self):
        """Test that default parameters match SAFTE-FAST literature."""
        model = ThreeProcessModel()

        # Based on SAFTE-FAST literature
        assert model.TAU_WAKE == 18.2
        assert model.TAU_SLEEP == 4.2
        assert model.CIRCADIAN_PERIOD == 24.0
        assert model.WOCL_START == 2.0
        assert model.WOCL_END == 6.0
        assert model.THRESHOLD_FAA_CAUTION == 77.0
        assert model.THRESHOLD_FRA_HIGH_RISK == 70.0
