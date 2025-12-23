"""
Tests for Erlang C queuing theory specialist coverage optimization.

Tests include:
- Erlang B formula accuracy
- Erlang C formula accuracy
- Wait probability calculations
- Average wait time calculations
- Service level calculations
- Occupancy calculations
- Specialist coverage optimization
- Edge cases and error handling
"""

import pytest

from app.resilience.erlang_coverage import (
    ErlangCCalculator,
    ErlangMetrics,
    SpecialistCoverage,
)


class TestErlangBFormula:
    """Test Erlang B blocking probability calculations."""

    def test_erlang_b_zero_load(self):
        """Test Erlang B with zero offered load."""
        calc = ErlangCCalculator()
        result = calc.erlang_b(offered_load=0.0, servers=5)
        assert result == 0.0

    def test_erlang_b_zero_servers(self):
        """Test Erlang B with zero servers."""
        calc = ErlangCCalculator()
        result = calc.erlang_b(offered_load=5.0, servers=0)
        assert result == 1.0

    def test_erlang_b_known_values(self):
        """Test Erlang B against known values from standard tables."""
        calc = ErlangCCalculator()

        # Known value: A=1.0, c=2 -> B ≈ 0.200
        result = calc.erlang_b(offered_load=1.0, servers=2)
        assert abs(result - 0.200) < 0.05

        # Known value: A=5.0, c=8 -> B ≈ 0.070 (using recursive formula)
        result = calc.erlang_b(offered_load=5.0, servers=8)
        assert abs(result - 0.070) < 0.02

        # Test that result is reasonable (low blocking with excess capacity)
        result = calc.erlang_b(offered_load=10.0, servers=15)
        assert result < 0.15  # Should be relatively low

    def test_erlang_b_increasing_servers(self):
        """Test that more servers reduces blocking probability."""
        calc = ErlangCCalculator()
        offered_load = 5.0

        prob_3 = calc.erlang_b(offered_load, servers=3)
        prob_5 = calc.erlang_b(offered_load, servers=5)
        prob_8 = calc.erlang_b(offered_load, servers=8)

        assert prob_3 > prob_5 > prob_8
        assert prob_8 < 0.1  # Should be quite low with 8 servers

    def test_erlang_b_caching(self):
        """Test that results are cached correctly."""
        calc = ErlangCCalculator()

        # First call
        result1 = calc.erlang_b(offered_load=5.0, servers=8)

        # Second call should use cache
        result2 = calc.erlang_b(offered_load=5.0, servers=8)

        assert result1 == result2
        assert (5.0, 8) in calc._erlang_b_cache


class TestErlangCFormula:
    """Test Erlang C wait probability calculations."""

    def test_erlang_c_zero_load(self):
        """Test Erlang C with zero offered load."""
        calc = ErlangCCalculator()
        result = calc.erlang_c(offered_load=0.0, servers=5)
        assert result == 0.0

    def test_erlang_c_zero_servers(self):
        """Test Erlang C with zero servers."""
        calc = ErlangCCalculator()
        result = calc.erlang_c(offered_load=0.0, servers=0)
        assert result == 1.0

    def test_erlang_c_unstable_queue(self):
        """Test that unstable queue raises ValueError."""
        calc = ErlangCCalculator()

        with pytest.raises(ValueError, match="Unstable queue"):
            calc.erlang_c(offered_load=10.0, servers=8)

        with pytest.raises(ValueError, match="Unstable queue"):
            calc.erlang_c(offered_load=5.0, servers=5)

    def test_erlang_c_known_values(self):
        """Test Erlang C against known values from standard tables."""
        calc = ErlangCCalculator()

        # Known value: A=5.0, c=8 -> C ≈ 0.075
        result = calc.erlang_c(offered_load=5.0, servers=8)
        assert abs(result - 0.075) < 0.02

        # Known value: A=3.0, c=5 -> C ≈ 0.127
        result = calc.erlang_c(offered_load=3.0, servers=5)
        assert abs(result - 0.127) < 0.02

        # Known value: A=10.0, c=15 -> C ≈ 0.117
        result = calc.erlang_c(offered_load=10.0, servers=15)
        assert abs(result - 0.117) < 0.02

    def test_erlang_c_increasing_servers(self):
        """Test that more servers reduces wait probability."""
        calc = ErlangCCalculator()
        offered_load = 5.0

        prob_6 = calc.erlang_c(offered_load, servers=6)
        prob_8 = calc.erlang_c(offered_load, servers=8)
        prob_10 = calc.erlang_c(offered_load, servers=10)

        assert prob_6 > prob_8 > prob_10
        assert prob_10 < 0.05  # Should be very low with 10 servers

    def test_erlang_c_caching(self):
        """Test that results are cached correctly."""
        calc = ErlangCCalculator()

        # First call
        result1 = calc.erlang_c(offered_load=5.0, servers=8)

        # Second call should use cache
        result2 = calc.erlang_c(offered_load=5.0, servers=8)

        assert result1 == result2
        assert (5.0, 8) in calc._erlang_c_cache


class TestWaitProbability:
    """Test wait probability calculations."""

    def test_calculate_wait_probability_basic(self):
        """Test basic wait probability calculation."""
        calc = ErlangCCalculator()

        # 2.5 calls/hour, 30 min (0.5 hr) per call, 3 servers
        # Offered load = 2.5 * 0.5 = 1.25
        result = calc.calculate_wait_probability(
            arrival_rate=2.5,
            service_time=0.5,
            servers=3,
        )

        assert 0.0 <= result <= 1.0
        assert result < 0.2  # Should be relatively low with this config

    def test_calculate_wait_probability_high_load(self):
        """Test wait probability with high load."""
        calc = ErlangCCalculator()

        # High load scenario: 8 calls/hour, 0.5 hr per call, 5 servers
        # Offered load = 8 * 0.5 = 4.0
        result = calc.calculate_wait_probability(
            arrival_rate=8.0,
            service_time=0.5,
            servers=5,
        )

        assert result > 0.3  # Should be high with tight capacity

    def test_calculate_wait_probability_excess_capacity(self):
        """Test wait probability with excess capacity."""
        calc = ErlangCCalculator()

        # Low load: 2 calls/hour, 0.5 hr per call, 10 servers
        # Offered load = 2 * 0.5 = 1.0
        result = calc.calculate_wait_probability(
            arrival_rate=2.0,
            service_time=0.5,
            servers=10,
        )

        assert result < 0.01  # Should be very low with excess capacity


class TestAverageWaitTime:
    """Test average wait time calculations."""

    def test_calculate_avg_wait_time_basic(self):
        """Test basic average wait time calculation."""
        calc = ErlangCCalculator()

        result = calc.calculate_avg_wait_time(
            arrival_rate=2.5,
            service_time=0.5,
            servers=3,
        )

        assert result >= 0.0
        assert result < 0.5  # Should be less than service time

    def test_calculate_avg_wait_time_unstable(self):
        """Test that unstable queue raises ValueError."""
        calc = ErlangCCalculator()

        with pytest.raises(ValueError, match="Unstable queue"):
            calc.calculate_avg_wait_time(
                arrival_rate=10.0,
                service_time=0.5,
                servers=5,
            )

    def test_calculate_avg_wait_time_increases_with_load(self):
        """Test that wait time increases with load."""
        calc = ErlangCCalculator()
        servers = 5

        # Low load
        wait_low = calc.calculate_avg_wait_time(
            arrival_rate=2.0,
            service_time=0.5,
            servers=servers,
        )

        # Medium load
        wait_med = calc.calculate_avg_wait_time(
            arrival_rate=4.0,
            service_time=0.5,
            servers=servers,
        )

        # High load (still stable)
        wait_high = calc.calculate_avg_wait_time(
            arrival_rate=4.8,
            service_time=0.5,
            servers=servers,
        )

        assert wait_low < wait_med < wait_high


class TestServiceLevel:
    """Test service level calculations."""

    def test_calculate_service_level_basic(self):
        """Test basic service level calculation."""
        calc = ErlangCCalculator()

        # 2.5 calls/hour, 0.5 hr service, 3 servers, 0.25 hr (15 min) target
        result = calc.calculate_service_level(
            arrival_rate=2.5,
            service_time=0.5,
            servers=3,
            target_wait=0.25,
        )

        assert 0.0 <= result <= 1.0
        assert result > 0.8  # Should achieve good service level

    def test_calculate_service_level_zero_target(self):
        """Test service level with zero target wait."""
        calc = ErlangCCalculator()

        # Zero target means immediate answer
        result = calc.calculate_service_level(
            arrival_rate=2.5,
            service_time=0.5,
            servers=3,
            target_wait=0.0,
        )

        # Service level with zero wait = 1 - P(wait)
        wait_prob = calc.calculate_wait_probability(2.5, 0.5, 3)
        expected = 1.0 - wait_prob

        assert abs(result - expected) < 0.01

    def test_calculate_service_level_long_target(self):
        """Test service level with very long target wait."""
        calc = ErlangCCalculator()

        # Very long target should approach 100%
        result = calc.calculate_service_level(
            arrival_rate=2.5,
            service_time=0.5,
            servers=3,
            target_wait=10.0,  # 10 hours!
        )

        assert result > 0.99  # Nearly 100%

    def test_calculate_service_level_increases_with_servers(self):
        """Test that service level increases with more servers."""
        calc = ErlangCCalculator()
        arrival_rate = 5.0
        service_time = 0.5
        target_wait = 0.25

        sl_6 = calc.calculate_service_level(arrival_rate, service_time, 6, target_wait)
        sl_8 = calc.calculate_service_level(arrival_rate, service_time, 8, target_wait)
        sl_10 = calc.calculate_service_level(
            arrival_rate, service_time, 10, target_wait
        )

        assert sl_6 < sl_8 < sl_10


class TestOccupancy:
    """Test occupancy calculations."""

    def test_calculate_occupancy_basic(self):
        """Test basic occupancy calculation."""
        calc = ErlangCCalculator()

        # Offered load = 2.5 * 0.5 = 1.25, 3 servers
        # Occupancy = 1.25 / 3 = 0.417
        result = calc.calculate_occupancy(
            arrival_rate=2.5,
            service_time=0.5,
            servers=3,
        )

        assert abs(result - 0.417) < 0.01

    def test_calculate_occupancy_zero_servers(self):
        """Test occupancy with zero servers."""
        calc = ErlangCCalculator()

        result = calc.calculate_occupancy(
            arrival_rate=2.5,
            service_time=0.5,
            servers=0,
        )

        assert result == 1.0  # Capped at 100%

    def test_calculate_occupancy_high_load(self):
        """Test occupancy with high load."""
        calc = ErlangCCalculator()

        # Offered load = 5.0 * 0.5 = 2.5, 3 servers
        # Occupancy = 2.5 / 3 = 0.833
        result = calc.calculate_occupancy(
            arrival_rate=5.0,
            service_time=0.5,
            servers=3,
        )

        assert abs(result - 0.833) < 0.01

    def test_calculate_occupancy_capped(self):
        """Test that occupancy is capped at 1.0."""
        calc = ErlangCCalculator()

        # Over-capacity (would be > 1.0)
        result = calc.calculate_occupancy(
            arrival_rate=10.0,
            service_time=0.5,
            servers=3,
        )

        assert result == 1.0


class TestOptimizeSpecialistCoverage:
    """Test specialist coverage optimization."""

    def test_optimize_basic(self):
        """Test basic coverage optimization."""
        calc = ErlangCCalculator()

        coverage = calc.optimize_specialist_coverage(
            specialty="Orthopedic Surgery",
            arrival_rate=2.5,
            service_time=0.5,
            target_wait_prob=0.05,
        )

        assert isinstance(coverage, SpecialistCoverage)
        assert coverage.specialty == "Orthopedic Surgery"
        assert coverage.required_specialists >= 2  # At minimum
        assert coverage.predicted_wait_probability <= 0.05
        assert 0.0 <= coverage.service_level <= 1.0
        assert coverage.offered_load == 2.5 * 0.5

    def test_optimize_high_load(self):
        """Test optimization with high load."""
        calc = ErlangCCalculator()

        coverage = calc.optimize_specialist_coverage(
            specialty="Cardiology",
            arrival_rate=10.0,
            service_time=1.0,
            target_wait_prob=0.05,
        )

        # High load (10 Erlangs) should require many specialists
        assert coverage.required_specialists > 10
        assert coverage.predicted_wait_probability <= 0.05

    def test_optimize_low_load(self):
        """Test optimization with low load."""
        calc = ErlangCCalculator()

        coverage = calc.optimize_specialist_coverage(
            specialty="Rare Specialty",
            arrival_rate=0.5,
            service_time=0.5,
            target_wait_prob=0.05,
        )

        # Low load should require few specialists
        assert coverage.required_specialists <= 3
        assert coverage.predicted_wait_probability <= 0.05

    def test_optimize_strict_target(self):
        """Test optimization with strict target."""
        calc = ErlangCCalculator()

        coverage = calc.optimize_specialist_coverage(
            specialty="Emergency Medicine",
            arrival_rate=5.0,
            service_time=0.5,
            target_wait_prob=0.01,  # Very strict: 1% wait probability
        )

        assert coverage.predicted_wait_probability <= 0.01
        # Stricter target should require more specialists
        assert coverage.required_specialists >= 4

    def test_optimize_impossible_target(self):
        """Test that impossible target raises ValueError."""
        calc = ErlangCCalculator()

        with pytest.raises(ValueError, match="Cannot meet target"):
            calc.optimize_specialist_coverage(
                specialty="Test",
                arrival_rate=50.0,  # Very high load
                service_time=1.0,
                target_wait_prob=0.001,  # Very strict
                max_servers=10,  # Low limit
            )

    def test_optimize_different_targets(self):
        """Test that stricter targets require more specialists."""
        calc = ErlangCCalculator()

        coverage_5pct = calc.optimize_specialist_coverage(
            specialty="Test",
            arrival_rate=5.0,
            service_time=0.5,
            target_wait_prob=0.05,
        )

        coverage_1pct = calc.optimize_specialist_coverage(
            specialty="Test",
            arrival_rate=5.0,
            service_time=0.5,
            target_wait_prob=0.01,
        )

        assert coverage_1pct.required_specialists >= coverage_5pct.required_specialists


class TestCalculateMetrics:
    """Test complete metrics calculation."""

    def test_calculate_metrics_basic(self):
        """Test basic metrics calculation."""
        calc = ErlangCCalculator()

        metrics = calc.calculate_metrics(
            arrival_rate=2.5,
            service_time=0.5,
            servers=3,
            target_wait=0.25,
        )

        assert isinstance(metrics, ErlangMetrics)
        assert 0.0 <= metrics.wait_probability <= 1.0
        assert metrics.avg_wait_time >= 0.0
        assert 0.0 <= metrics.service_level <= 1.0
        assert 0.0 <= metrics.occupancy <= 1.0

    def test_calculate_metrics_default_target(self):
        """Test metrics with default target wait."""
        calc = ErlangCCalculator()

        metrics = calc.calculate_metrics(
            arrival_rate=2.5,
            service_time=0.5,
            servers=3,
        )

        # Default target should be half of service time
        assert isinstance(metrics, ErlangMetrics)
        assert metrics.service_level > 0.0

    def test_calculate_metrics_consistency(self):
        """Test that metrics are internally consistent."""
        calc = ErlangCCalculator()

        metrics = calc.calculate_metrics(
            arrival_rate=5.0,
            service_time=0.5,
            servers=8,
            target_wait=0.25,
        )

        # Occupancy should match offered_load / servers
        expected_occupancy = (5.0 * 0.5) / 8
        assert abs(metrics.occupancy - expected_occupancy) < 0.01

        # Service level should be >= (1 - wait_probability)
        assert metrics.service_level >= (1.0 - metrics.wait_probability) - 0.01


class TestGenerateStaffingTable:
    """Test staffing table generation."""

    def test_generate_staffing_table_basic(self):
        """Test basic staffing table generation."""
        calc = ErlangCCalculator()

        table = calc.generate_staffing_table(
            arrival_rate=2.5,
            service_time=0.5,
        )

        assert len(table) > 0
        assert all("servers" in row for row in table)
        assert all("wait_probability" in row for row in table)
        assert all("service_level" in row for row in table)
        assert all("occupancy" in row for row in table)

    def test_generate_staffing_table_range(self):
        """Test staffing table with custom range."""
        calc = ErlangCCalculator()

        table = calc.generate_staffing_table(
            arrival_rate=5.0,
            service_time=0.5,
            min_servers=5,
            max_servers=10,
        )

        assert len(table) <= 6  # Max 6 rows (5-10 inclusive)
        assert table[0]["servers"] >= 5
        assert table[-1]["servers"] <= 10

    def test_generate_staffing_table_decreasing_wait(self):
        """Test that wait probability decreases with more servers."""
        calc = ErlangCCalculator()

        table = calc.generate_staffing_table(
            arrival_rate=5.0,
            service_time=0.5,
            min_servers=6,
            max_servers=10,
        )

        # Each row should have lower or equal wait probability than previous
        for i in range(1, len(table)):
            assert table[i]["wait_probability"] <= table[i - 1]["wait_probability"]

    def test_generate_staffing_table_increasing_service_level(self):
        """Test that service level increases with more servers."""
        calc = ErlangCCalculator()

        table = calc.generate_staffing_table(
            arrival_rate=5.0,
            service_time=0.5,
            min_servers=6,
            max_servers=10,
        )

        # Each row should have higher or equal service level than previous
        for i in range(1, len(table)):
            assert table[i]["service_level"] >= table[i - 1]["service_level"]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_very_small_arrival_rate(self):
        """Test with very small arrival rate."""
        calc = ErlangCCalculator()

        metrics = calc.calculate_metrics(
            arrival_rate=0.01,
            service_time=0.1,
            servers=1,
        )

        assert metrics.wait_probability < 0.01
        assert metrics.occupancy < 0.01

    def test_very_large_server_count(self):
        """Test with very large server count."""
        calc = ErlangCCalculator()

        metrics = calc.calculate_metrics(
            arrival_rate=5.0,
            service_time=0.5,
            servers=100,  # Way more than needed
        )

        assert metrics.wait_probability < 0.0001  # Nearly zero
        assert metrics.service_level > 0.9999  # Nearly 100%

    def test_boundary_stable_queue(self):
        """Test queue at stability boundary."""
        calc = ErlangCCalculator()

        # Just under stability limit
        metrics = calc.calculate_metrics(
            arrival_rate=4.99,
            service_time=0.5,
            servers=3,  # Offered load = 2.495, just under 2.5
        )

        assert metrics.wait_probability > 0.0  # Should still calculate

    def test_negative_values_handling(self):
        """Test that negative values are handled appropriately."""
        calc = ErlangCCalculator()

        # Negative arrival rate should give zero load
        result = calc.erlang_b(offered_load=-1.0, servers=5)
        assert result == 0.0

        # Negative servers should give blocking
        result = calc.erlang_b(offered_load=5.0, servers=-1)
        assert result == 1.0


class TestRealWorldScenarios:
    """Test realistic medical scheduling scenarios."""

    def test_er_orthopedic_coverage(self):
        """Test ER orthopedic surgeon coverage optimization."""
        calc = ErlangCCalculator()

        # Scenario: ER needs orthopedic consults
        # Average 1.5 consults/hour, 2 hours per consult
        coverage = calc.optimize_specialist_coverage(
            specialty="Orthopedic Surgery",
            arrival_rate=1.5,
            service_time=2.0,
            target_wait_prob=0.10,  # 10% acceptable wait
        )

        assert coverage.required_specialists >= 3
        assert coverage.offered_load == 3.0

    def test_cardiology_call_schedule(self):
        """Test cardiology call schedule optimization."""
        calc = ErlangCCalculator()

        # Scenario: Cardiology call coverage
        # Average 0.8 calls/hour, 1.5 hours per case
        coverage = calc.optimize_specialist_coverage(
            specialty="Cardiology",
            arrival_rate=0.8,
            service_time=1.5,
            target_wait_prob=0.05,  # 5% max wait
        )

        assert coverage.required_specialists >= 2
        assert coverage.predicted_wait_probability <= 0.05

    def test_procedure_specialist_coverage(self):
        """Test procedure specialist coverage optimization."""
        calc = ErlangCCalculator()

        # Scenario: Emergent procedure coverage
        # Average 2.0 cases/hour during peak, 0.75 hour per procedure
        coverage = calc.optimize_specialist_coverage(
            specialty="Interventional Radiology",
            arrival_rate=2.0,
            service_time=0.75,
            target_wait_prob=0.05,
        )

        assert coverage.required_specialists >= 2
        assert coverage.offered_load == 1.5

    def test_high_volume_clinic(self):
        """Test high-volume clinic staffing."""
        calc = ErlangCCalculator()

        # Scenario: High-volume urgent care
        # 12 patients/hour, 20 minutes (0.33 hr) per patient
        coverage = calc.optimize_specialist_coverage(
            specialty="Urgent Care Physician",
            arrival_rate=12.0,
            service_time=0.33,
            target_wait_prob=0.10,
            max_servers=15,
        )

        assert coverage.required_specialists >= 4
        assert coverage.offered_load == pytest.approx(3.96, rel=0.1)

    def test_rare_specialty_coverage(self):
        """Test rare specialty with low volume."""
        calc = ErlangCCalculator()

        # Scenario: Rare specialty consultation
        # Average 0.2 consults/hour, 3 hours per case
        coverage = calc.optimize_specialist_coverage(
            specialty="Pediatric Neurosurgery",
            arrival_rate=0.2,
            service_time=3.0,
            target_wait_prob=0.05,
        )

        # Low volume should still require at least 1-2 specialists
        assert coverage.required_specialists >= 1
        assert coverage.offered_load == 0.6
