"""
Tests for SIR burnout epidemiology model.

Tests compartmental epidemic modeling applied to burnout spread.
"""

import pytest

from app.resilience.epidemiology.sir_model import SIRModel, SIRState


class TestSIRModel:
    """Test suite for SIR burnout model."""

    def test_basic_reproduction_number(self):
        """Test R0 calculation."""
        model = SIRModel(transmission_rate=0.3, recovery_rate=0.1)

        assert model.basic_reproduction_number == 3.0  # β/γ = 0.3/0.1
        assert model.r0 == 3.0

    def test_r0_interpretation(self):
        """Test R0 > 1 means epidemic."""
        # Epidemic (R0 > 1)
        epidemic_model = SIRModel(transmission_rate=0.5, recovery_rate=0.2)
        assert epidemic_model.r0 > 1.0

        # Endemic (R0 = 1)
        endemic_model = SIRModel(transmission_rate=0.1, recovery_rate=0.1)
        assert endemic_model.r0 == 1.0

        # Die out (R0 < 1)
        dying_model = SIRModel(transmission_rate=0.05, recovery_rate=0.1)
        assert dying_model.r0 < 1.0

    def test_simulate_epidemic_growth(self):
        """Test epidemic simulation with R0 > 1."""
        model = SIRModel(transmission_rate=0.4, recovery_rate=0.1)  # R0 = 4

        forecast = model.simulate(
            initial_susceptible=95,
            initial_infected=5,
            initial_recovered=0,
            days=90,
        )

        assert forecast.days_ahead == 90
        assert len(forecast.forecasted_infected) == 90

        # Should have epidemic peak
        assert forecast.peak_infected > 5
        assert forecast.time_to_peak > 0
        assert forecast.total_cases > 5

    def test_simulate_die_out(self):
        """Test simulation with R0 < 1 (burnout dies out)."""
        model = SIRModel(transmission_rate=0.05, recovery_rate=0.1)  # R0 = 0.5

        forecast = model.simulate(
            initial_susceptible=95,
            initial_infected=5,
            initial_recovered=0,
            days=90,
        )

        # Epidemic should die out
        final_infected = forecast.forecasted_infected[-1]
        assert final_infected < 5  # Fewer infected at end than start

    def test_herd_immunity_threshold(self):
        """Test herd immunity threshold calculation."""
        # R0 = 4 => HIT = 1 - 1/4 = 0.75 (75% immune needed)
        model = SIRModel(transmission_rate=0.4, recovery_rate=0.1)
        hit = model.calculate_herd_immunity_threshold()

        assert hit == pytest.approx(0.75, abs=0.01)

        # R0 < 1 => no herd immunity needed
        model_low = SIRModel(transmission_rate=0.05, recovery_rate=0.1)
        hit_low = model_low.calculate_herd_immunity_threshold()

        assert hit_low == 0.0

    def test_predict_final_size(self):
        """Test final epidemic size prediction."""
        model = SIRModel(transmission_rate=0.3, recovery_rate=0.1)

        final_size = model.predict_final_size(
            initial_infected=10,
            total_population=100,
        )

        # Should be > 10 (epidemic spreads)
        assert final_size >= 10

    def test_intervention_effect(self):
        """Test calculating intervention impact."""
        model = SIRModel(transmission_rate=0.4, recovery_rate=0.1)

        impact = model.calculate_intervention_effect(
            current_beta=0.4,
            intervention_beta=0.2,  # 50% reduction in transmission
            current_infected=10,
            total_population=100,
            days=60,
        )

        # Intervention should reduce cases
        assert impact["cases_prevented"] > 0
        assert impact["intervention_total_cases"] < impact["baseline_total_cases"]
        assert impact["intervention_r0"] < impact["baseline_r0"]

    def test_classify_epidemic_phase(self):
        """Test epidemic phase classification."""
        model = SIRModel(transmission_rate=0.3, recovery_rate=0.1)

        # No cases
        assert model.classify_epidemic_phase(0, 100) == "no_cases"

        # Sporadic (<1%)
        assert model.classify_epidemic_phase(1, 200) == "sporadic"

        # Outbreak (1-5%)
        assert model.classify_epidemic_phase(3, 100) == "outbreak"

        # Epidemic (5-15%)
        assert model.classify_epidemic_phase(10, 100) == "epidemic"

        # Crisis (>15%)
        assert model.classify_epidemic_phase(20, 100) == "crisis"

    def test_empty_population_edge_case(self):
        """Test edge case with empty population."""
        model = SIRModel(transmission_rate=0.3, recovery_rate=0.1)

        forecast = model.simulate(
            initial_susceptible=0,
            initial_infected=0,
            initial_recovered=0,
            days=30,
        )

        assert forecast.peak_infected == 0
        assert forecast.total_cases == 0

    def test_conservation_of_population(self):
        """Test that S + I + R = N is conserved."""
        model = SIRModel(transmission_rate=0.3, recovery_rate=0.1)

        forecast = model.simulate(
            initial_susceptible=90,
            initial_infected=10,
            initial_recovered=0,
            days=90,
        )

        # Check conservation at random time points
        for i in [0, 30, 60, 89]:
            total = (
                forecast.forecasted_susceptible[i]
                + forecast.forecasted_infected[i]
                + forecast.forecasted_recovered[i]
            )
            assert total == pytest.approx(100, abs=2)  # Allow small numerical error

    def test_peak_timing_reasonable(self):
        """Test that epidemic peak occurs at reasonable time."""
        model = SIRModel(transmission_rate=0.5, recovery_rate=0.1)

        forecast = model.simulate(
            initial_susceptible=95,
            initial_infected=5,
            initial_recovered=0,
            days=100,
        )

        # Peak should occur between day 0 and day 100
        assert 0 <= forecast.time_to_peak < 100
        assert forecast.peak_day == forecast.time_to_peak
