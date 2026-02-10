"""Tests for retry backoff strategies (pure logic, no DB)."""

import pytest

from app.resilience.retry.strategies import (
    BackoffStrategy,
    ExponentialBackoffStrategy,
    ExponentialBackoffWithCeiling,
    FixedDelayStrategy,
    LinearBackoffStrategy,
    RetryStrategy,
    get_retry_strategy,
)


# ── BackoffStrategy enum ─────────────────────────────────────────────────


class TestBackoffStrategy:
    def test_fixed_value(self):
        assert BackoffStrategy.FIXED.value == "fixed"

    def test_linear_value(self):
        assert BackoffStrategy.LINEAR.value == "linear"

    def test_exponential_value(self):
        assert BackoffStrategy.EXPONENTIAL.value == "exponential"

    def test_member_count(self):
        assert len(BackoffStrategy) == 3


# ── FixedDelayStrategy ────────────────────────────────────────────────────


class TestFixedDelayStrategy:
    def test_default_delay(self):
        s = FixedDelayStrategy()
        assert s.delay == 1.0

    def test_custom_delay(self):
        s = FixedDelayStrategy(delay=5.0)
        assert s.delay == 5.0

    def test_calculate_delay_ignores_attempt(self):
        s = FixedDelayStrategy(delay=3.0)
        for attempt in range(10):
            assert s.calculate_delay(attempt) == 3.0

    def test_get_delay_returns_same(self):
        s = FixedDelayStrategy(delay=3.0)
        assert s.get_delay(0) == 3.0
        assert s.get_delay(5) == 3.0

    def test_zero_delay(self):
        s = FixedDelayStrategy(delay=0.0)
        assert s.calculate_delay(0) == 0.0

    def test_is_retry_strategy(self):
        assert isinstance(FixedDelayStrategy(), RetryStrategy)

    def test_max_delay_none_by_default(self):
        s = FixedDelayStrategy()
        assert s.max_delay is None


# ── LinearBackoffStrategy ─────────────────────────────────────────────────


class TestLinearBackoffStrategy:
    def test_default_params(self):
        s = LinearBackoffStrategy()
        assert s.base_delay == 1.0
        assert s.increment == 1.0

    def test_attempt_zero(self):
        s = LinearBackoffStrategy(base_delay=2.0, increment=3.0)
        assert s.calculate_delay(0) == 2.0

    def test_attempt_one(self):
        s = LinearBackoffStrategy(base_delay=2.0, increment=3.0)
        assert s.calculate_delay(1) == 5.0

    def test_linear_growth(self):
        s = LinearBackoffStrategy(base_delay=1.0, increment=2.0)
        expected = [1.0, 3.0, 5.0, 7.0, 9.0]
        for attempt, exp in enumerate(expected):
            assert s.calculate_delay(attempt) == exp

    def test_zero_increment(self):
        """Zero increment behaves like fixed delay."""
        s = LinearBackoffStrategy(base_delay=5.0, increment=0.0)
        for attempt in range(5):
            assert s.calculate_delay(attempt) == 5.0

    def test_is_retry_strategy(self):
        assert isinstance(LinearBackoffStrategy(), RetryStrategy)


# ── ExponentialBackoffStrategy ────────────────────────────────────────────


class TestExponentialBackoffStrategy:
    def test_default_params(self):
        s = ExponentialBackoffStrategy()
        assert s.base_delay == 1.0
        assert s.multiplier == 2.0

    def test_attempt_zero(self):
        s = ExponentialBackoffStrategy(base_delay=1.0, multiplier=2.0)
        assert s.calculate_delay(0) == 1.0  # 1 * 2^0 = 1

    def test_attempt_sequence(self):
        s = ExponentialBackoffStrategy(base_delay=1.0, multiplier=2.0)
        expected = [1.0, 2.0, 4.0, 8.0, 16.0]
        for attempt, exp in enumerate(expected):
            assert s.calculate_delay(attempt) == exp

    def test_custom_multiplier(self):
        s = ExponentialBackoffStrategy(base_delay=1.0, multiplier=3.0)
        assert s.calculate_delay(0) == 1.0
        assert s.calculate_delay(1) == 3.0
        assert s.calculate_delay(2) == 9.0
        assert s.calculate_delay(3) == 27.0

    def test_custom_base_delay(self):
        s = ExponentialBackoffStrategy(base_delay=0.5, multiplier=2.0)
        assert s.calculate_delay(0) == 0.5
        assert s.calculate_delay(1) == 1.0
        assert s.calculate_delay(2) == 2.0

    def test_is_retry_strategy(self):
        assert isinstance(ExponentialBackoffStrategy(), RetryStrategy)

    def test_no_max_delay_by_default(self):
        s = ExponentialBackoffStrategy()
        assert s.max_delay is None

    def test_grows_without_bound(self):
        """Without max_delay, delay grows exponentially."""
        s = ExponentialBackoffStrategy(base_delay=1.0, multiplier=2.0)
        assert s.get_delay(20) == 1048576.0  # 2^20


# ── ExponentialBackoffWithCeiling ─────────────────────────────────────────


class TestExponentialBackoffWithCeiling:
    def test_default_max_delay(self):
        s = ExponentialBackoffWithCeiling()
        assert s.max_delay == 60.0

    def test_exponential_until_ceiling(self):
        s = ExponentialBackoffWithCeiling(
            base_delay=1.0, multiplier=2.0, max_delay=10.0
        )
        assert s.get_delay(0) == 1.0
        assert s.get_delay(1) == 2.0
        assert s.get_delay(2) == 4.0
        assert s.get_delay(3) == 8.0
        assert s.get_delay(4) == 10.0  # Capped at max_delay
        assert s.get_delay(5) == 10.0  # Still capped

    def test_calculate_delay_uncapped(self):
        """calculate_delay itself doesn't cap; get_delay does."""
        s = ExponentialBackoffWithCeiling(
            base_delay=1.0, multiplier=2.0, max_delay=10.0
        )
        assert s.calculate_delay(4) == 16.0  # 1 * 2^4 = 16, uncapped
        assert s.get_delay(4) == 10.0  # Capped by get_delay

    def test_is_retry_strategy(self):
        assert isinstance(ExponentialBackoffWithCeiling(), RetryStrategy)

    def test_custom_params(self):
        s = ExponentialBackoffWithCeiling(
            base_delay=0.5, multiplier=3.0, max_delay=30.0
        )
        assert s.base_delay == 0.5
        assert s.multiplier == 3.0
        assert s.max_delay == 30.0


# ── RetryStrategy.get_delay (max_delay capping) ──────────────────────────


class TestGetDelayCapping:
    def test_no_cap_when_max_delay_none(self):
        s = FixedDelayStrategy(delay=100.0, max_delay=None)
        assert s.get_delay(0) == 100.0

    def test_capped_when_exceeds_max(self):
        s = FixedDelayStrategy(delay=100.0, max_delay=50.0)
        assert s.get_delay(0) == 50.0

    def test_not_capped_when_under_max(self):
        s = FixedDelayStrategy(delay=10.0, max_delay=50.0)
        assert s.get_delay(0) == 10.0

    def test_equal_to_max_returns_max(self):
        s = FixedDelayStrategy(delay=50.0, max_delay=50.0)
        assert s.get_delay(0) == 50.0

    def test_linear_capping(self):
        s = LinearBackoffStrategy(base_delay=1.0, increment=10.0, max_delay=25.0)
        assert s.get_delay(0) == 1.0
        assert s.get_delay(1) == 11.0
        assert s.get_delay(2) == 21.0
        assert s.get_delay(3) == 25.0  # Capped: 31 > 25
        assert s.get_delay(4) == 25.0  # Capped: 41 > 25

    def test_exponential_capping(self):
        s = ExponentialBackoffStrategy(base_delay=1.0, multiplier=2.0, max_delay=10.0)
        assert s.get_delay(0) == 1.0
        assert s.get_delay(3) == 8.0
        assert s.get_delay(4) == 10.0  # Capped: 16 > 10


# ── get_retry_strategy factory ────────────────────────────────────────────


class TestGetRetryStrategy:
    def test_fixed_returns_fixed(self):
        s = get_retry_strategy(BackoffStrategy.FIXED)
        assert isinstance(s, FixedDelayStrategy)

    def test_linear_returns_linear(self):
        s = get_retry_strategy(BackoffStrategy.LINEAR)
        assert isinstance(s, LinearBackoffStrategy)

    def test_exponential_without_max_returns_exponential(self):
        s = get_retry_strategy(BackoffStrategy.EXPONENTIAL)
        assert isinstance(s, ExponentialBackoffStrategy)

    def test_exponential_with_max_returns_ceiling(self):
        s = get_retry_strategy(BackoffStrategy.EXPONENTIAL, max_delay=60.0)
        assert isinstance(s, ExponentialBackoffWithCeiling)

    def test_custom_base_delay(self):
        s = get_retry_strategy(BackoffStrategy.FIXED, base_delay=5.0)
        assert isinstance(s, FixedDelayStrategy)
        assert s.delay == 5.0

    def test_linear_custom_increment(self):
        s = get_retry_strategy(BackoffStrategy.LINEAR, increment=3.0)
        assert isinstance(s, LinearBackoffStrategy)
        assert s.increment == 3.0

    def test_exponential_custom_multiplier(self):
        s = get_retry_strategy(BackoffStrategy.EXPONENTIAL, multiplier=3.0)
        assert isinstance(s, ExponentialBackoffStrategy)
        assert s.multiplier == 3.0

    def test_unknown_strategy_raises(self):
        with pytest.raises(ValueError, match="Unknown backoff strategy"):
            get_retry_strategy("invalid_strategy")

    def test_all_strategies_are_retry_strategy(self):
        for bs in BackoffStrategy:
            strategy = get_retry_strategy(bs)
            assert isinstance(strategy, RetryStrategy)

    def test_fixed_max_delay_passthrough(self):
        s = get_retry_strategy(BackoffStrategy.FIXED, max_delay=10.0)
        assert s.max_delay == 10.0

    def test_linear_max_delay_passthrough(self):
        s = get_retry_strategy(BackoffStrategy.LINEAR, max_delay=20.0)
        assert s.max_delay == 20.0
