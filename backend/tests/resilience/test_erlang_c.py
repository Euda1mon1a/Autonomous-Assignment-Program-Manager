"""
Tests for Erlang C queuing calculator.

Tests M/M/c queue calculations from telecommunications theory.
"""

import pytest

from app.resilience.queuing.erlang_c import ErlangC


class TestErlangC:
    """Test suite for Erlang C calculator."""

    def test_stable_system_low_utilization(self):
        """Test stable system with low utilization."""
        erlang = ErlangC()

        result = erlang.calculate(
            arrival_rate=2.0,  # 2 requests/hour
            service_rate=1.0,  # 1 per hour per server
            num_servers=5,  # 5 servers
        )

        # Utilization = λ/(c*μ) = 2/(5*1) = 0.4
        assert result.utilization == pytest.approx(0.4, abs=0.01)
        assert result.utilization < 1.0  # Stable
        assert result.prob_wait < 1.0
        assert result.avg_queue_length < 10  # Reasonable queue

    def test_high_utilization_increases_wait(self):
        """Test that high utilization increases wait time."""
        erlang = ErlangC()

        # Low utilization
        result_low = erlang.calculate(
            arrival_rate=4.0,
            service_rate=1.0,
            num_servers=10,  # ρ = 0.4
        )

        # High utilization
        result_high = erlang.calculate(
            arrival_rate=9.0,
            service_rate=1.0,
            num_servers=10,  # ρ = 0.9
        )

        assert result_high.utilization > result_low.utilization
        assert result_high.avg_wait_time > result_low.avg_wait_time
        assert result_high.avg_queue_length > result_low.avg_queue_length

    def test_unstable_system(self):
        """Test unstable system (ρ >= 1)."""
        erlang = ErlangC()

        result = erlang.calculate(
            arrival_rate=10.0,
            service_rate=1.0,
            num_servers=10,  # ρ = 1.0 (exactly unstable)
        )

        assert result.utilization >= 1.0
        assert result.prob_wait == 1.0
        assert result.avg_queue_length == float("inf")

    def test_adding_servers_reduces_wait(self):
        """Test that adding servers reduces wait time."""
        erlang = ErlangC()

        # 5 servers
        result_5 = erlang.calculate(
            arrival_rate=8.0,
            service_rate=1.0,
            num_servers=5,
        )

        # 10 servers
        result_10 = erlang.calculate(
            arrival_rate=8.0,
            service_rate=1.0,
            num_servers=10,
        )

        assert result_10.utilization < result_5.utilization
        assert result_10.avg_wait_time < result_5.avg_wait_time

    def test_calculate_required_servers(self):
        """Test calculating required servers for targets."""
        erlang = ErlangC()

        required = erlang.calculate_required_servers(
            arrival_rate=8.0,
            service_rate=1.0,
            target_utilization=0.80,
            target_service_level=0.80,
        )

        # Should need at least 10 servers (8/(1*0.8) = 10)
        assert required >= 10

        # Verify the result actually meets targets
        result = erlang.calculate(8.0, 1.0, required)
        assert result.utilization <= 0.80
        assert result.service_level >= 0.80

    def test_service_level_calculation(self):
        """Test service level (probability served within target time)."""
        erlang = ErlangC()

        result = erlang.calculate(
            arrival_rate=5.0,
            service_rate=1.0,
            num_servers=10,
            target_wait_time=0.5,  # 30 minutes
        )

        assert 0.0 <= result.service_level <= 1.0

    def test_compare_scenarios(self):
        """Test comparing multiple staffing scenarios."""
        erlang = ErlangC()

        results = erlang.compare_scenarios(
            arrival_rate=10.0,
            service_rate=1.0,
            server_counts=[8, 10, 12, 15],
        )

        assert len(results) == 4

        # Check that more servers = lower utilization
        for i in range(len(results) - 1):
            assert results[i].utilization >= results[i + 1].utilization

    def test_scale_effect(self):
        """Test effect of adding servers."""
        erlang = ErlangC()

        effect = erlang.calculate_scale_effect(
            arrival_rate=10.0,
            service_rate=1.0,
            current_servers=12,
            additional_servers=3,
        )

        # Adding servers should improve metrics
        assert effect["after_utilization"] < effect["before_utilization"]
        assert effect["after_wait_time"] < effect["before_wait_time"]
        assert effect["wait_time_reduction"] > 0

    def test_find_optimal_servers(self):
        """Test finding optimal servers minimizing cost."""
        erlang = ErlangC()

        optimal, cost = erlang.find_optimal_servers(
            arrival_rate=10.0,
            service_rate=1.0,
            cost_per_server=100.0,  # $100/hour per server
            cost_per_wait_hour=50.0,  # $50/hour customer wait cost
            max_servers=25,
        )

        assert optimal >= 11  # At least enough for stability
        assert cost > 0

    def test_littles_law(self):
        """Test Little's Law: L = λW."""
        erlang = ErlangC()

        result = erlang.calculate(
            arrival_rate=5.0,
            service_rate=1.0,
            num_servers=10,
        )

        # L_q = λ * W_q (Little's Law)
        if result.avg_wait_time < float("inf"):
            expected_queue = result.arrival_rate * result.avg_wait_time
            assert result.avg_queue_length == pytest.approx(expected_queue, abs=0.1)

    def test_zero_arrival_rate(self):
        """Test edge case with zero arrivals."""
        erlang = ErlangC()

        result = erlang.calculate(
            arrival_rate=0.0,
            service_rate=1.0,
            num_servers=5,
        )

        assert result.utilization == 0.0
        assert result.avg_queue_length == 0.0
        assert result.avg_wait_time == 0.0

    def test_80_percent_utilization_threshold(self):
        """Test that 80% utilization is near knee of curve."""
        erlang = ErlangC()

        # Calculate queue length at different utilizations
        util_70 = erlang.calculate(7.0, 1.0, 10)  # 70%
        util_80 = erlang.calculate(8.0, 1.0, 10)  # 80%
        util_90 = erlang.calculate(9.0, 1.0, 10)  # 90%

        # Queue growth accelerates after 80%
        growth_70_to_80 = util_80.avg_queue_length - util_70.avg_queue_length
        growth_80_to_90 = util_90.avg_queue_length - util_80.avg_queue_length

        # Growth from 80-90% should be much larger than 70-80%
        assert growth_80_to_90 > growth_70_to_80
