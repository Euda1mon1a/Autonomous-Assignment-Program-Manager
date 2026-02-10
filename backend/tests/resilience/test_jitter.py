"""Tests for retry jitter strategies (pure logic, no DB)."""

import pytest

from app.resilience.retry.jitter import (
    DecorrelatedJitter,
    EqualJitter,
    FullJitter,
    JitterStrategy,
    JitterType,
    NoJitter,
    get_jitter_strategy,
)


# ── JitterType enum ─────────────────────────────────────────────────────


class TestJitterType:
    def test_none_value(self):
        assert JitterType.NONE.value == "none"

    def test_full_value(self):
        assert JitterType.FULL.value == "full"

    def test_equal_value(self):
        assert JitterType.EQUAL.value == "equal"

    def test_decorrelated_value(self):
        assert JitterType.DECORRELATED.value == "decorrelated"

    def test_member_count(self):
        assert len(JitterType) == 4


# ── NoJitter ─────────────────────────────────────────────────────────────


class TestNoJitter:
    def test_returns_exact_delay(self):
        jitter = NoJitter()
        assert jitter.apply(5.0, 0) == 5.0

    def test_returns_zero_delay(self):
        jitter = NoJitter()
        assert jitter.apply(0.0, 0) == 0.0

    def test_large_delay_unchanged(self):
        jitter = NoJitter()
        assert jitter.apply(1000.0, 10) == 1000.0

    def test_ignores_previous_delay(self):
        jitter = NoJitter()
        assert jitter.apply(5.0, 0, previous_delay=100.0) == 5.0

    def test_is_jitter_strategy(self):
        assert isinstance(NoJitter(), JitterStrategy)


# ── FullJitter ───────────────────────────────────────────────────────────


class TestFullJitter:
    def test_within_bounds(self):
        jitter = FullJitter()
        for _ in range(100):
            result = jitter.apply(10.0, 0)
            assert 0.0 <= result <= 10.0

    def test_zero_delay(self):
        jitter = FullJitter()
        assert jitter.apply(0.0, 0) == 0.0

    def test_not_always_same(self):
        """Statistical: with 100 samples, shouldn't all be identical."""
        jitter = FullJitter()
        results = {jitter.apply(10.0, 0) for _ in range(100)}
        assert len(results) > 1

    def test_is_jitter_strategy(self):
        assert isinstance(FullJitter(), JitterStrategy)


# ── EqualJitter ──────────────────────────────────────────────────────────


class TestEqualJitter:
    def test_within_bounds(self):
        jitter = EqualJitter()
        for _ in range(100):
            result = jitter.apply(10.0, 0)
            assert 5.0 <= result <= 10.0  # half + random(0, half)

    def test_minimum_is_half(self):
        """The minimum possible value should be half the delay."""
        jitter = EqualJitter()
        results = [jitter.apply(10.0, 0) for _ in range(1000)]
        assert min(results) >= 5.0

    def test_zero_delay(self):
        jitter = EqualJitter()
        assert jitter.apply(0.0, 0) == 0.0

    def test_not_always_same(self):
        jitter = EqualJitter()
        results = {jitter.apply(10.0, 0) for _ in range(100)}
        assert len(results) > 1

    def test_is_jitter_strategy(self):
        assert isinstance(EqualJitter(), JitterStrategy)


# ── DecorrelatedJitter ───────────────────────────────────────────────────


class TestDecorrelatedJitter:
    def test_first_attempt_bounds(self):
        jitter = DecorrelatedJitter(base_delay=1.0)
        for _ in range(100):
            result = jitter.apply(5.0, 0, previous_delay=0.0)
            assert 1.0 <= result <= 5.0

    def test_subsequent_attempt_bounds(self):
        jitter = DecorrelatedJitter(base_delay=1.0)
        prev = 2.0
        for _ in range(100):
            result = jitter.apply(5.0, 1, previous_delay=prev)
            assert 1.0 <= result <= prev * 3

    def test_custom_base_delay(self):
        jitter = DecorrelatedJitter(base_delay=0.5)
        assert jitter.base_delay == 0.5
        for _ in range(100):
            result = jitter.apply(5.0, 0, previous_delay=0.0)
            assert 0.5 <= result <= 5.0

    def test_default_base_delay(self):
        jitter = DecorrelatedJitter()
        assert jitter.base_delay == 1.0

    def test_is_jitter_strategy(self):
        assert isinstance(DecorrelatedJitter(), JitterStrategy)


# ── get_jitter_strategy factory ──────────────────────────────────────────


class TestGetJitterStrategy:
    def test_none_returns_no_jitter(self):
        strategy = get_jitter_strategy(JitterType.NONE)
        assert isinstance(strategy, NoJitter)

    def test_full_returns_full_jitter(self):
        strategy = get_jitter_strategy(JitterType.FULL)
        assert isinstance(strategy, FullJitter)

    def test_equal_returns_equal_jitter(self):
        strategy = get_jitter_strategy(JitterType.EQUAL)
        assert isinstance(strategy, EqualJitter)

    def test_decorrelated_returns_decorrelated_jitter(self):
        strategy = get_jitter_strategy(JitterType.DECORRELATED)
        assert isinstance(strategy, DecorrelatedJitter)

    def test_decorrelated_with_custom_base_delay(self):
        strategy = get_jitter_strategy(JitterType.DECORRELATED, base_delay=0.5)
        assert isinstance(strategy, DecorrelatedJitter)
        assert strategy.base_delay == 0.5

    def test_unknown_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown jitter type"):
            get_jitter_strategy("bad_type")

    def test_all_strategies_are_jitter_strategy(self):
        for jt in JitterType:
            strategy = get_jitter_strategy(jt)
            assert isinstance(strategy, JitterStrategy)
